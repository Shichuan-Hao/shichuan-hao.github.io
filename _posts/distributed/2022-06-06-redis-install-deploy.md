---
title: "Redis 7.X 多模式安装部署完整指南"
date: 2022-06-06
categories: distributed
tags: [Redis, 安装部署, 主从复制, 哨兵, Cluster, 运维]
mermaid: true
---

> Redis 的部署远不止 `apt-get install redis` 一行命令。从单机到主从到哨兵到集群，每一层架构演进都有对应的部署细节和踩坑经验。本文覆盖 Redis 7.X 的完整安装与四种模式部署。

## 一、Redis 安装

### 1.1 单机安装

Redis 官网：[redis.io](https://redis.io/)

Redis 主要维护最新版本。Redis 7 目前支持到 **v7.2.5**，于 2024 年 5 月发布。如果想体验最新特性，可以安装不稳定版本（如 7.2.5）。但生产环境强烈建议使用最新的稳定版本（7.2.4）。

#### 安装步骤（CentOS/Ubuntu 通用）

```bash
# 1. 更新系统 & 安装基础依赖
yum update -y && yum install -y gcc make

# 2. 下载源码
wget -c https://download.redis.io/releases/redis-7.2.5.tar.gz
tar xzvf redis-7.2.5.tar.gz

# 3. 编译安装
cd redis-7.2.5
make && make install
```

**make 常见问题**：

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| `gcc: command not found` | 未安装 gcc | `yum install -y gcc` |
| `fatal error: jemalloc/jemalloc.h` | 分配器问题 | `make MALLOC=libc` |
| `cc: error: unrecognized command line option '-std=c11'` | gcc 版本太低 | 升级 gcc |
| server.c 等编译错误 | gcc 7 以下与 Redis 7 不兼容 | `yum install -y centos-release-scl` → `yum install -y devtoolset-7` |

Redis 7 需要 gcc 7 或以上版本。如果报编译错误，优先检查 gcc 版本：

```bash
gcc -v
```

#### 编译后文件说明

| 文件 | 说明 |
|------|------|
| `redis-server` | 服务端程序 |
| `redis-cli` | 客户端 |
| `redis-benchmark` | 性能压测工具 |
| `redis-check-aof` | AOF 文件修复 |
| `redis-check-rdb` | RDB 文件检查 |
| `redis-sentinel` | 哨兵（指向 redis-server 的软链接） |

### 1.2 基础配置

Redis 的默认配置文件位于源码目录的 `redis.conf`。**任何时候都不要使用默认配置，必须手动创建修改**。

```bash
# 创建工作目录
mkdir /myredis
cp redis.conf /myredis/redis.conf

# 基础设置（编辑 myredis/redis.conf）
bind 0.0.0.0           # 旧版绑定地址（留 "" 让新版 -::\* 生效）
protected-mode no      # 非保护模式（学习环境）
daemonize yes          # 守护进程模式（后台运行）
port 6379
logfile "/myredis/redis.log"
dir /myredis

# 加上密码（极其重要！防止挖矿病毒）
requirepass yourpassword
```

> ⚠️ **安全警告**：生产环境**必须设置密码**。网络上大量扫描程序时刻尝试连接无密码的 Redis 实例，注入挖矿脚本。密码强度应按照"防暴力破解"标准设置。

#### 启动服务

```bash
redis-server /myredis/redis.conf
redis-cli -a yourpassword
# 或连接后再认证
redis-cli
> AUTH yourpassword
```

#### 验证安装

```bash
127.0.0.1:6379> ping
PONG
127.0.0.1:6379> info server
# ... Redis 版本信息
```

---

## 二、主从复制模式部署

### 2.1 为什么需要主从

单机 Redis 能做到"数据安全"吗？通过 RDB/AOF 持久化，单机 Redis 的数据在节点重启后可恢复。但硬盘故障（SSD 也有寿命）、服务器断电等硬件问题，数据就彻底没了。

所以需要**主从复制**来构建多副本数据安全。

### 2.2 部署步骤

一个原则：**配从不配主**。主节点照常启动，不需要特殊配置。

```bash
# 主节点 (6379) — 配置同上单机版

# 从节点 (6380) — 配置文件增加一行
port 6380
replicaof 192.168.65.214 6379
masterauth 123qweasd      # 如果 master 有密码，必须配置
```

> `replicaof` 是 Redis 5.0 后的新指令名（旧版 `slaveof` 仍可用但官方推荐 replacement）。

全量配置文件对比：

| 配置项 | Master (6379) | Slave (6380) |
|--------|--------------|--------------|
| `port` | 6379 | 6380 |
| `replicaof` | 无 | `192.168.65.214 6379` |
| `masterauth` | 无 | `123qweasd` |
| `replica-read-only` | — | `yes`（默认） |

### 2.3 验证主从状态

```bash
# Master 端
127.0.0.1:6379> info replication
# Replication
role:master
connected_slaves:1
slave0:ip=192.168.65.214,port=6380,state=online,offset=56,lag=1

# Slave 端
127.0.0.1:6380> info replication
# Replication
role:slave
master_host:192.168.65.214
master_port:6379
master_link_status:up
slave_read_only:1
```

关键检查项：
- `connected_slaves` 数量是否正确
- `master_link_status: up`（slave 端必须为 up）
- `state: online`（master 端必须为 online）

### 2.4 主从复制的数据一致性

**Redis 复制是异步的**。默认情况下，master 写完数据立即返回客户端，无需等待 slave 确认。这在高并发下是合理的设计，但意味着存在**数据丢失窗口**。

可以通过 `min-replicas-to-write` 和 `min-replicas-max-lag` 限制：

```
min-replicas-to-write 1          # 至少 1 个 slave 在线
min-replicas-max-lag 10          # slave 延迟不超过 10 秒
```

> 人总是有两个选择：要么接受可能丢失；要么不接受，但忍受性能的可能回退。Redis 的设计哲学倾向前者——接受小概率的数据丢失，换取极致性能。

---

## 三、哨兵（Sentinel）模式部署

### 3.1 Sentinel 的核心价值

主从复制解决了数据多副本问题，但 master 挂掉后**不会自动切换**。Sentinel 就是来解决这个问题的。

### 3.2 部署步骤

按照**至少 3 个 Sentinel 节点**的原则配置（为什么是 3 个？为了在选举 Leader 时满足"超半数"的 Raft 要求）。

```bash
# sentinel-26379.conf
daemonize yes
port 26379
protected-mode no
logfile "/root/myredis/sentinel/sentinel-26379.log"
pidfile /var/run/redis-sentinel-26379.pid
dir /root/myredis/sentinel

# 核心配置：监控 master
# sentinel monitor <master-name> <ip> <port> <quorum>
sentinel monitor mymaster 192.168.65.214 6379 2

# master 密码
sentinel auth-pass mymaster 123qweasd

# 主观下线判定时间（默认30秒，生产建议适当调大）
sentinel down-after-milliseconds mymaster 30000

# 故障转移超时时间
sentinel failover-timeout mymaster 180000
```

> **quorum 参数**是整个 Sentinel 架构的核心。3 个 Sentinel 设置 quorum=2，意味着需要 2 个 Sentinel 达成共识才判定 master 客观下线。这是避免误判的关键。

```bash
# 依次启动 3 个 Sentinel
redis-server sentinel-26379.conf --sentinel &
redis-server sentinel-26380.conf --sentinel &
redis-server sentinel-26381.conf --sentinel &

# 或者直接
redis-sentinel sentinel-26379.conf &
```

### 3.3 验证 Sentinel

```bash
# 连接任意 Sentinel
redis-cli -p 26379

127.0.0.1:26379> info sentinel
# Sentinel
sentinel_masters:1
sentinel_tilt:0
sentinel_running_scripts:0
sentinel_scripts_queue_length:0
master0:name=mymaster,status=ok,address=192.168.65.214:6379,slaves=1,sentinels=3
```

关键信息：
- `sentinels:3`：所有 Sentinel 互相发现了
- `status=ok`：master 状态正常

### 3.4 故障转移验证

```bash
# 模拟 master 宕机
redis-cli -p 6379 -a 123qweasd SHUTDOWN

# 在 Sentinel 上查看
redis-cli -p 26379 sentinel get-master-addr-by-name mymaster
1) "192.168.65.214"
2) "6380"        # ← 6380 已成为新 master
```

### 3.5 Sentinel 连接方式

Java 客户端连接 Sentinel：

```java
Set<String> sentinels = new HashSet<>();
sentinels.add("192.168.65.214:26379");
sentinels.add("192.168.65.214:26380");
sentinels.add("192.168.65.214:26381");

JedisSentinelPool pool = new JedisSentinelPool("mymaster", sentinels, config, "123qweasd");
// 当 master 切换时，客户端自动感知新 master 地址
```

---

## 四、Redis Cluster 模式部署

### 4.1 Cluster 的前置认知

Cluster 是三合一的方案：
- **数据分片**：16384 个 slot 分配到多个主节点
- **自动故障转移**：每个主节点有对应从节点
- **自动重定向**：客户端请求自动路由到正确节点

### 4.2 完整的 6 节点配置文件（3主3从）

以 6381 节点为例：

```bash
# redis6381.conf
bind * -::*
daemonize yes
protected-mode no
port 6381
requirepass 123qweasd
masterauth 123qweasd

# ===== Cluster 配置 =====
cluster-enabled yes
cluster-config-file nodes-6381.conf
cluster-node-timeout 5000          # 节点超时（毫秒）

# ===== 持久化（Cluster 环境必须开启） =====
appendonly yes
appenddirname "aof"
appendfilename "appendonly6381.aof"
dbfilename "dump6381.rdb"

logfile "/root/myredis/cluster/redis6381.log"
pidfile /var/run/redis_6381.pid
dir "/root/myredis/cluster"
```

依次为 6381-6386 创建配置并启动：

```bash
redis-server redis6381.conf
redis-server redis6382.conf
# ... 到 6386
```

### 4.3 创建集群

```bash
redis-cli -a 123qweasd --cluster create --cluster-replicas 1 \
  192.168.65.214:6381 \
  192.168.65.214:6382 \
  192.168.65.214:6383 \
  192.168.65.214:6384 \
  192.168.65.214:6385 \
  192.168.65.214:6386
```

`--cluster-replicas 1` 表示每个主节点配 1 个从节点。Redis 会**自动**：
- 前 3 个节点（6381/6382/6383）设为 master
- 后 3 个节点（6384/6385/6386）分别作为它们的 slave
- 自动分配 16384 个 slot 到 3 个 master（约 5461 个/节点）

### 4.4 验证集群

```bash
# 连接集群（加 -c 参数启用集群模式）
redis-cli -a 123qweasd -p 6381 -c

127.0.0.1:6381> CLUSTER NODES
b5d7fa0bef... 192.168.65.214:6381@16381 myself,master - 0 0 1 connected 0-5460
e8cd1c6a3c... 192.168.65.214:6382@16382 master - 0 0 2 connected 5461-10922
c1d5f8e479... 192.168.65.214:6383@16383 master - 0 0 3 connected 10923-16383
a1b2c3d4e5... 192.168.65.214:6384@16384 slave b5d7fa0bef 0 0 1 connected
f6g7h8i9j0... 192.168.65.214:6385@16385 slave e8cd1c6a3c 0 0 2 connected
k1l2m3n4o5... 192.168.65.214:6386@16386 slave c1d5f8e479 0 0 3 connected

127.0.0.1:6381> CLUSTER INFO
cluster_state:ok
cluster_slots_assigned:16384
cluster_slots_ok:16384
cluster_slots_fail:0
cluster_known_nodes:6
cluster_size:3
```

### 4.5 动态扩容

```bash
# 添加新 master（6387）
redis-cli -a 123qweasd --cluster add-node 192.168.65.214:6387 192.168.65.214:6381

# 迁移 slot 给新节点
redis-cli -a 123qweasd --cluster reshard 192.168.65.214:6381
# 交互式引导：要移多少slot？哪个节点接收？从哪些节点移出？

# 添加 slave（6388 作为 6387 的从节点）
redis-cli -a 123qweasd --cluster add-node \
  192.168.65.214:6388 192.168.65.214:6381 \
  --cluster-slave --cluster-master-id <master-node-id>
```

### 4.6 故障转移验证

```bash
# 关闭 6381（一个 master）
redis-cli -a 123qweasd -p 6381 shutdown

# 查看集群状态变化
redis-cli -a 123qweasd -p 6382 -c cluster nodes
# 6384 应自动升级为 master，slot 范围变为 0-5460
```

> **注意**：`CLUSTER FAILOVER` 可手动触发故障转移。`CLUSTER FAILOVER FORCE` 不等待主节点响应，强制切换（可能导致数据丢失）。

### 4.7 集群相关故障排查

| 问题 | 现象 | 解决 |
|------|------|------|
| `(error) CLUSTERDOWN` | 所有 slot 未全部分配 | 检查节点是否全部启动，执行 `cluster info` |
| `(error) MOVED 12706 192.168.65.214:6383` | 客户端未加 `-c` 参数 | 加 `-c` 参数重连 |
| 连接不上某个节点 | 防火墙阻挡 | 开放服务端口 + 服务端口+10000（Gossip 端口） |
| 集群分裂（脑裂） | 网络分区导致两个 master | 调整 `cluster-node-timeout`，优化网络 |

---

## 五、部署架构选型指南

| 场景 | 推荐架构 | 理由 |
|------|---------|------|
| 本地开发 | 单机 | 简单够用 |
| 小型项目（QPS < 1万） | 主从复制 | 读写分离，数据备份 |
| 中型项目（需要高可用） | Sentinel (3节点) | 自动故障转移 |
| 大型项目（数据量大/QPS > 5万） | Cluster (6节点起) | 数据分片 + 自动故障转移 |
| 云环境 | Redis Cloud / 云厂商托管 | 免运维，弹性扩容 |

> 生产环境切换建议路径：单机 → 主从复制 → Sentinel → Cluster。不要一步到位跳到 Cluster，在理解每一层的基础上逐步演进。
