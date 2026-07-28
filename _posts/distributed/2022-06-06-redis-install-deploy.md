---
layout: post
title: "Redis7.X 四种模式完整部署教程（单机/主从/哨兵/集群）"
date: 2022-06-06 09:00:00 +0800
categories: [distributed]
tags: [Redis, 部署, 单机, 主从复制, 哨兵, 集群, 运维]
comments: true
---

## 一、环境准备：安装 gcc

Redis 由 C 语言编写，编译需要 gcc 环境。

```bash
# 关闭防火墙
systemctl stop firewalld.service

# 检查防火墙状态
firewall-cmd --state

# 卸载防火墙（生产环境按需操作）
yum remove firewalld

# 检查 gcc 版本
gcc --version

# 安装 gcc
yum install gcc
```

---

## 二、单机部署

### 2.1 下载编译安装

```bash
# 创建应用目录，养成文件归类习惯
mkdir -p /opt/software/redis
cd /opt/software/redis

# 下载 Redis 稳定版
wget https://download.redis.io/redis-stable.tar.gz

# 解压
tar -xzf redis-stable.tar.gz

# 编译安装
cd redis-stable
make install

# 检查安装结果，/usr/local/bin 下会生成以下可执行文件
ll /usr/local/bin
```

### 2.2 编译生成的文件说明

| 文件 | 作用 |
|------|------|
| `redis-benchmark` | 性能测试工具，模拟 N 个客户端同时发请求 |
| `redis-check-aof` | 修复有问题的 AOF 文件 |
| `redis-check-rdb` | 修复有问题的 RDB 文件 |
| `redis-sentinel` | Redis 哨兵，高可用集群使用 |
| `redis-server` | Redis 服务器启动命令 |
| `redis-cli` | 客户端命令行操作入口 |

### 2.3 启动 Redis（前台模式）

```bash
# 方式一：源码目录下启动
./src/redis-server

# 方式二：使用 /usr/local/bin 下启动
redis-server
```

> ⚠️ 前台启动会阻塞终端，退出终端即关闭服务。

### 2.4 配置 Redis 后台运行

编辑 `redis.conf`，修改以下关键配置：

```bash
vim redis.conf
```

| 行号 | 配置项 | 值 | 说明 |
|------|--------|-----|------|
| 87 | `bind` | `* -::*` | 支持 IPv4/IPv6 远程连接 |
| 111 | `protected-mode` | `no` | 允许远程连接（不设密码时必须关闭） |
| 309 | `daemonize` | `yes` | 开启守护进程，后台运行 |
| 355 | `logfile` | `/opt/software/redis/redis-stable/redis.log` | 指定日志文件 |
| 510 | `dir` | `/opt/software/redis` | 指定工作目录（存放 RDB、AOF） |
| 1044 | `requirepass` | `1qaz@WSX` | 设置密码（可选） |

配置完成后，使用配置文件启动：

```bash
redis-server redis.conf

# 带密码认证连接
redis-cli -a 1qaz@WSX

# 退出
quit

# 关闭 Redis
redis-cli shutdown
```

---

## 三、主从部署 (Master-Slave Replication)

### 3.1 架构原理

```
         ┌──────────┐
         │  Master  │ ── 写操作
         │  :6379   │
         └────┬─────┘
      ┌───────┼───────┐
      ▼       ▼       ▼
  ┌──────┐┌──────┐┌──────┐
  │Slave1││Slave2││Slave3│ ── 读操作
  │:6379 ││:6379 ││:6379 │
  └──────┘└──────┘└──────┘
```

- 数据复制**单向**：主 → 从
- 一个主可有多个从，一个从只能有一个主
- 默认每台 Redis 服务器都是主节点

### 3.2 主从复制的四大作用

| 作用 | 说明 |
|------|------|
| **数据冗余** | 热备份，持久化之外的冗余手段 |
| **故障恢复** | 主节点故障时，从节点可接管服务（需人工干预） |
| **负载均衡** | 读写分离：主写从读，分担服务器负载 |
| **高可用基石** | 哨兵和集群模式的基础 |

### 3.3 部署步骤

主节点配置不变，从节点在配置文件中添加一行：

```bash
# 从节点 redis.conf 添加
replicaof 192.168.75.129 6379
```

验证：

```bash
# 主节点查看从节点信息
redis-cli info Replication
```

### 3.4 主从复制的缺点

- **复制延迟**：异步复制，系统繁忙时延迟更严重，从节点越多越严重
- **Master 挂了需人工干预**：默认不会自动选举新主节点
- **不能保证高可用**：单纯主从架构是数据冗余 + 读分担，不是高可用方案

---

## 四、哨兵部署 (Sentinel)

### 4.1 哨兵模式原理

哨兵通过独立的哨兵进程监控主从节点状态，自动完成：

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Sentinel-1   │     │ Sentinel-2   │     │ Sentinel-3   │
│  :26379      │◄───►│  :26379      │◄───►│  :26379      │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │ 监控
              ┌─────────────┴─────────────┐
              │          Master           │
              │          :6379            │
              └─────────────┬─────────────┘
                     ┌──────┴──────┐
                     ▼             ▼
              ┌──────────┐ ┌──────────┐
              │  Slave-1 │ │  Slave-2 │
              │  :6379   │ │  :6379   │
              └──────────┘ └──────────┘
```

### 4.2 哨兵选举过程

1. 每个在线哨兵都可成为 Leader
2. 每个哨兵向其他哨兵发送 `sentinel is-master-down-by-addr` 命令，要求将自己设为 Leader
3. 其他哨兵可以同意或拒绝
4. 获得票数 >= `num(sentinels)/2+1` 即成为 Leader
5. 未过半则继续选举

### 4.3 主观下线 vs 客观下线

```
主观下线 (S_DOWN):
  Sentinel 向 Master 发送 PING
  → 超过 down-after-milliseconds 未收到 PONG 或收到错误
  → 该 Sentinel 单方面认为 Master 不可用

客观下线 (O_DOWN):
  当主观下线的节点是主节点时
  → 该 Sentinel 通过 sentinel is-master-down-by-addr 咨询其他 Sentinel
  → 超过 quorum 个 Sentinel 同意
  → 判定为客观下线，触发故障转移
```

### 4.4 故障转移流程

1. **确认主节点故障**：Sentinel 定期 PING Master，确认 Master 不可用（客观下线）
2. **选举新主节点**——从节点筛选规则：
   - 过滤掉不健康的（下线/断线，没回复过 PING 的）
   - 选择**从节点优先级**最高的（`replica-priority` 值最小的）
   - 选择**复制偏移量**最大的（数据最完整的）
3. **故障转移**：由 Leader Sentinel 执行
4. **客户端重定向**：Sentinel 通知客户端新主节点位置，无缝切换

### 4.5 哨兵部署配置

3 台机器都需要配置 `sentinel.conf`：

```bash
protected-mode no                                # 6行，关闭保护模式
daemonize yes                                    # 15行，后台启动
logfile /opt/software/redis/redis-stable/sentinel.log  # 34行
dir /opt/software/redis                          # 73行
sentinel monitor mymaster 192.168.75.129 6379 2  # 93行，监控主节点
#    ↑名称    ↑主IP    ↑端口  ↑quorum:至少2个哨兵同意才判定故障
sentinel down-after-milliseconds mymaster 30000  # 134行，30秒超时
sentinel failover-timeout mymaster 180000        # 234行，故障转移超时180秒
```

启动和观察：

```bash
# 启动哨兵
redis-sentinel sentinel.conf

# 检查哨兵状态
redis-cli -p 26379 info sentinel
```

### 4.6 故障模拟

```bash
# 杀掉主节点进程
ps aux | grep redis
redis-cli -p 6379 shutdown

# 观察哨兵日志（129 主节点下线，重新选举新主节点）
tail -f sentinel.log

# 重新启动旧主节点（自动加入作为从节点）
redis-server redis.conf
tail -f sentinel.log

# 切换后检查节点信息
redis-cli info replication

# 查看自动修改的配置文件
cat redis.conf
cat sentinel.conf
```

### 4.7 哨兵使用建议

- 哨兵节点数量应为**多个**（至少 3 个），保证自身高可用
- 哨兵节点数应是**奇数**（防止脑裂场景下平票）
- 各哨兵节点配置应**一致**
- Docker 部署要注意**端口映射**正确性

### 4.8 哨兵模式不能保证数据零丢失的原因

1. **复制延迟**：异步复制，从节点可能尚未完全同步最新写入
2. **故障检测和转移时间**：检测 + 转移期间，Master 可能已接收了未复制的写操作
3. **网络分区**：网络分裂时，孤立的主节点继续接受写操作，恢复前无法复制
4. **多个从节点同时故障**：无可用从节点提升为 Master

---

## 五、集群部署 (Cluster)

### 5.1 集群的作用

| 作用 | 说明 |
|------|------|
| **数据分区** | 突破单机内存限制，数据分散到多个节点 |
| **高并发** | 每个主节点都可提供读写服务，大幅提升响应能力 |
| **高可用** | 主从复制 + 主节点自动故障转移 |
| **解决单机瓶颈** | 单机内存过大时，bgsave/bgrewriteaof 的 fork 可能阻塞主进程；全量复制时缓冲区可能溢出 |

### 5.2 哈希槽 (Hash Slot) 机制

```
Redis 集群使用 16384 个哈希槽（编号 0~16383）

Key → CRC16(key) % 16384 → 确定属于哪个槽 → 路由到对应节点

┌─────────────────┬──────────────────┬──────────────────┐
│    Node A        │     Node B       │     Node C       │
│  Slots 0~5460   │ Slots 5461~10922 │ Slots 10923~16383│
└─────────────────┴──────────────────┴──────────────────┘
```

### 5.3 高可用架构：三主三从

```
┌────────┐  ┌────────┐  ┌────────┐
│Master A│  │Master B│  │Master C│
│ :6379  │  │ :6379  │  │ :6379  │
└───┬────┘  └───┬────┘  └───┬────┘
    │           │           │
    ▼           ▼           ▼
┌────────┐  ┌────────┐  ┌────────┐
│Slave A1│  │Slave B1│  │Slave C1│
│ :6380  │  │ :6380  │  │ :6380  │
└────────┘  └────────┘  └────────┘
```

- 任一主节点故障 → 其从节点自动提升为主
- 当某主节点和其所有从节点都失败 → 集群不可用

### 5.4 集群配置

每台机器两个 Redis 实例（6379 + 6380），配置如下：

**6379 端口配置** (`cluster/redis_6379.conf`)：

```bash
bind * -::*
daemonize yes
protected-mode no
cluster-enabled yes                # 开启集群模式
cluster-node-timeout 5000          # 节点超时时间
dir "/opt/software/redis/cluster"
appendonly yes                     # 开启 AOF
port 6379
logfile "/opt/software/redis/redis-stable/cluster/redis6379.log"
cluster-config-file nodes-6379.conf
appendfilename "appendonly6379.aof"
dbfilename "dump6379.rdb"
```

**6380 端口配置** (`cluster/redis_6380.conf`)：

```bash
bind * -::*
daemonize yes
protected-mode no
cluster-enabled yes
cluster-node-timeout 5000
dir "/opt/software/redis/cluster"
appendonly yes
port 6380
logfile "/opt/software/redis/redis-stable/cluster/redis6380.log"
cluster-config-file nodes-6380.conf
appendfilename "appendonly6380.aof"
dbfilename "dump6380.rdb"
```

### 5.5 创建集群

```bash
# 先启动所有 6 个 Redis 实例
redis-server ./cluster/redis_6379.conf
redis-server ./cluster/redis_6380.conf

# 检查服务
ps aux | grep redis

# 创建三主三从集群（--cluster-replicas 1 表示每个主节点带 1 个从节点）
redis-cli --cluster create --cluster-replicas 1 \
  192.168.75.129:6379 192.168.75.129:6380 \
  192.168.75.131:6379 192.168.75.131:6380 \
  192.168.75.132:6379 192.168.75.132:6380
```

### 5.6 验证和运维命令

```bash
# 集群信息
redis-cli cluster info

# 节点身份信息
redis-cli cluster nodes

# 节点复制信息
redis-cli info replication

# 带路由规则连接（关键！-c 参数自动重定向到正确节点）
redis-cli -c
set k1 v1          # 自动路由到对应槽位所在的节点

# 停止服务
redis-cli -p 6379 shutdown
redis-cli -p 6380 shutdown
```

### 5.7 故障转移模拟

```bash
# 将 129 机器的主节点(6379)停掉
redis-cli -p 6379 shutdown

# 观察其从节点(6380)的日志
cat redis6380.log
# → 6380 自动提升为主节点

# 在另一台机器查看集群节点信息
redis-cli cluster nodes
# → 确认 6380 已成为新主节点

# 重新启动旧主节点 6379
redis-server ./cluster/redis_6379.conf

# 查看其节点信息（自动变为从节点）
redis-cli -p 6379 info replication

# 观察日志确认重新加入集群
```

### 5.8 为什么是 16384 个槽？

- **CRC16 算法**输出 16 位，即 0~65535
- Redis 选择 16384 (2^14) 而非 65535 (2^16)，原因：
  - 心跳包中包含槽位信息，16384 个槽用位图表示仅需 2KB，65535 需 8KB
  - 集群节点数量通常不超过 1000 个，16384 已足够均匀分配
  - 更小的位图意味着更低的消息传输开销

---

## 六、完整目录结构

```
/opt/software/redis/                     # Redis 应用目录
├── redis-stable/                        # Redis 应用根目录
│   ├── cluster/                         # 集群配置文件存放路径（手动创建）
│   │   ├── redis_6379.conf
│   │   ├── redis_6380.conf
│   │   ├── redis6379.log
│   │   └── redis6380.log
│   ├── redis.conf                       # 单机/主从配置
│   ├── sentinel.conf                    # 哨兵配置
│   └── redis.log                        # 日志
└── cluster/                             # 集群数据存储目录
    ├── nodes-6379.conf                  # 集群节点配置文件（自动生成）
    ├── nodes-6380.conf
    ├── appendonly6379.aof
    ├── appendonly6380.aof
    ├── dump6379.rdb
    └── dump6380.rdb
```

---

## 七、四种模式选型总结

| 模式 | 高可用 | 数据分片 | 复杂度 | 适用场景 |
|------|--------|----------|--------|----------|
| **单机** | ❌ | ❌ | 低 | 开发测试、缓存量小 |
| **主从** | ❌ (需人工) | ❌ | 低 | 读写分离、数据备份 |
| **哨兵** | ✅ | ❌ | 中 | 中小规模、要求自动故障转移 |
| **集群** | ✅ | ✅ | 高 | 大规模、海量数据、高并发 |

---

## 八、面试要点

1. **Redis 哨兵模式的选举过程是怎样的？** — 票数 >= n/2+1 成为 Leader
2. **主观下线和客观下线的区别？** — 单个 Sentinel 判定 vs 多数 Sentinel 一致判定
3. **Redis 集群为什么是 16384 个槽？** — 心跳位图 2KB vs 8KB 的权衡
4. **哨兵模式为什么节点要是奇数？** — 防止脑裂场景下的平票
5. **四种部署模式各自解决了什么问题？** — 单机→主从(冗余) → 哨兵(自动故障转移) → 集群(分片扩容)
