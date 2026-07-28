---
layout: post
title: "Redis数据安全性分析：持久化/主从/哨兵/集群全景解析"
date: 2022-06-09
categories: [distributed]
tags: [Redis, RDB, AOF, 持久化, 主从复制, Sentinel, Cluster, 数据安全]
comments: true
---

> 不是教你怎么用 Redis，而是教你怎么把 Redis 用得比别人深一点。

---

## 一、Redis性能压测

Redis 所有数据保存在内存，性能强悍，但内存断电即失。真实项目中需要**在数据安全性与读写性能之间找到平衡点**。

**压测脚本**：

```bash
# 20个线程，100W个请求，测试set指令
redis-benchmark -a 123qweasd -t set -n 1000000 -c 20

Summary:
  throughput summary: 116536.53 requests per second
  latency summary (msec):
          avg       min       p50       p95       p99       max
        0.111     0.032     0.111     0.167     0.215     3.199
```

**平均每秒 11W 次写操作**。后续调整部署架构后建议多进行对比测试。

---

## 二、Redis数据持久化机制详解

### 1、整体策略

Redis 提供四种持久化策略：

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| 无持久化 | 完全关闭，不保证数据安全 | 纯缓存 |
| RDB | 按时间间隔保存全量数据快照 | 数据备份、灾难恢复 |
| AOF | 记录每次写操作，可操作重演恢复 | 数据安全要求高 |
| RDB+AOF | 同时开启 | **生产推荐** |

### RDB 优缺点

| 优点 | 缺点 |
|------|------|
| 文件紧凑，适合定期备份 | 不能实时备份，有数据丢失可能 |
| 非常适合灾难恢复 | fork 时需克隆内存，大数据量/弱 CPU 可能造成短暂停服 |
| 备份性能快，主线程几乎无影响 | |
| 大数据量重启比 AOF 快很多 | |

### AOF 优缺点

| 优点 | 缺点 |
|------|------|
| 更安全，默认每秒 fsync，最多损失 1 秒 | 同样数据集，AOF 文件通常比 RDB 大 |
| 追加写入，不会出现记录不完整 | 写操作频繁时，备份性能比 RDB 慢 |
| 文件太大自动切换新日志文件 | |
| 误删数据后可简单修复（删 FLUSHALL） | |

**使用建议**：
1. 纯缓存 → 关闭持久化
2. 关注数据安全，接受少量损失 → 只用 RDB
3. **不建议单独用 AOF**，RDB+AOF 数据恢复更快

---

### 2、RDB 详解

**RDB 能干什么**：在指定时间间隔，备份当前内存中的全量数据集到 `dump.rdb`。恢复时直接将快照文件读回内存。

**核心配置**：

```
# save策略：核心！seconds changes
save 3600 1     # 1小时内至少1次变更
save 300 100    # 5分钟内至少100次变更
save 60 10000   # 1分钟内至少10000次变更

dir /root/myredis/cluster           # 文件目录
dbfilename dump.rdb                 # 文件名
rdbcompression yes                  # 是否压缩（消耗CPU）
stop-writes-on-bgsave-error yes     # 备份失败时是否停止写入
rdbchecksum yes                     # CRC64校验（约10%性能消耗）
```

**何时触发 RDB 备份**：
1. 到达配置文件中的快照配置 → 自动触发
2. 手动 `save`（阻塞主线程）或 `bgsave`（fork 子线程，不阻塞）
3. 主从复制时触发

`LASTSAVE` 指令查看最后一次成功快照的时间戳。

---

### 3、AOF 详解

**核心配置**：

```
appendonly yes                              # 开启AOF
appendfilename "appendonly.aof"             # 文件名
appenddirname "aof"                         # AOF目录（Redis7新增）
appendfsync everysec                        # 同步方式

# 重写触发策略
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# 重写期间是否同步
no-appendfsync-on-rewrite no
```

**Redis7 AOF 三文件结构**（重大变化！）：

```
appendonly.aof.1.base.rdb     ← 二进制数据快照（RDB格式）
appendonly.aof.1.incr.aof     ← 增量操作日志（文本格式）
appendonly.aof.manifest       ← 元文件，记录文件信息和顺序
```

> Redis7 将原本一个 AOF 文件拆成三个文件，既保留 RDB+AOF 功能，又控制 AOF 文件大小。

**AOF 文件内容解析 — RESP 协议**：

`set k1 v1` 在 AOF 中记录为：
```
*3          # 三个部分
$3          # 第一个参数长度3
SET         # 第一个参数
$2          # 第二个参数长度2
k1          # 第二个参数
$2          # 第三个参数长度2
v1          # 第三个参数
```

**手写 Redis 客户端（基于 RESP 协议）**：

```java
public class MyRedisClient {
    OutputStream write;
    InputStream reader;
    
    public MyRedisClient(String host, int port) throws IOException {
        Socket socket = new Socket(host, port);
        write = socket.getOutputStream();
        reader = socket.getInputStream();
    }
    
    public String auth(String password) {
        StringBuffer command = new StringBuffer();
        command.append("*2").append("\r\n");         // 参数数量
        command.append("$4").append("\r\n");         // 第一个参数长度
        command.append("AUTH").append("\r\n");       // 第一个参数值
        command.append("$").append(password.getBytes().length).append("\r\n");
        command.append(password).append("\r\n");
        
        try {
            write.write(command.toString().getBytes());
            byte[] response = new byte[1024];
            reader.read(response);
            return new String(response);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
    
    public String set(String key, String value) {
        StringBuffer command = new StringBuffer();
        command.append("*3").append("\r\n");
        command.append("$3").append("\r\n");
        command.append("SET").append("\r\n");
        command.append("$").append(key.getBytes().length).append("\r\n");
        command.append(key).append("\r\n");
        command.append("$").append(value.getBytes().length).append("\r\n");
        command.append(value).append("\r\n");
        
        try {
            write.write(command.toString().getBytes());
            byte[] response = new byte[1024];
            reader.read(response);
            return new String(response);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
}
```

**AOF 日志恢复**：

如果 AOF 文件因意外情况指令记录不完整（模拟：手动编辑 incr.aof 文件末尾加随机文字），Redis 启动失败，日志：
```
Bad file format reading the append only file appendonly.aof.1.incr.aof:
make a backup of your AOF file, then use ./redis-check-aof --fix <filename.manifest>
```

修复命令：
```bash
redis-check-aof --fix appendonly.aof.1.incr.aof
# 修复过程本质：将最后那条不完整指令删除掉
```

---

### 4、混合持久化策略

```conf
aof-use-rdb-preamble yes   # AOF中使用RDB格式的base文件
```

**恢复优先级**：Redis 重启时**优先从 AOF 文件恢复**。因为 AOF 数据集通常比 RDB 更完整。

**最佳实践**：同时开启 RDB+AOF，但保留 RDB 文件做定期备份（AOF 不断变化不利于做定期全量备份）。

> 持久化策略只能保证**单机**数据安全。磁盘坏了，再好的持久化也没用。需要集群化方案。

---

## 三、Redis主从复制（Replication）

三种分布式方案（主从复制、哨兵集群、Redis集群）是**层层递进**的。

### 1、Replica 是什么？

```
+------------------+      +---------------+
|      Master      | ---> |    Replica    |
| (receive writes) |      |  (exact copy) |
+------------------+      +---------------+
```

核心特性：
1. **异步复制**：Master 可以配置在不够 N 个 Replica 时停止接受写入
2. **部分重同步**：连接短暂断开后可增量同步
3. **自动重连**：网络分区恢复后自动重连重同步

**典型作用**：读写分离（Master 写、Slave 读）、数据备份 + 容灾恢复

### 2、配置原则

**配从不配主**：在从节点配置 `REPLICAOF host port`

```
REPLICAOF host port|NO ONE     # 配置文件中指定
SLAVEOF host port|NO ONE       # 运行时动态修改
```

### 3、主从状态查看

**Master 节点** (`info replication`)：
```
role:master
connected_slaves:1
slave0:ip=192.168.65.214,port=6380,state=online,offset=56,lag=1
master_repl_offset:56
```

**Slave 节点** (`info replication`)：
```
role:slave
master_host:192.168.65.214
master_port:6379
master_link_status:up        # ← 重点观察
slave_read_only:1            # 从库默认只读
```

**从库安全加固**：从库虽然只读数据，但 CONFIG、DEBUG 等管理指令仍然可用。通过 `rename-command` 禁用危险指令：
```conf
replica-read-only yes
rename-command CONFIG ""
rename-command FLUSHALL ""
rename-command FLUSHDB ""
rename-command KEYS ""
```

### 4、主从复制工作流程

```
1. Slave 启动 → 向 Master 发送 sync 请求
2. Slave 删除自己原有数据日志文件
3. Master 触发 RDB 全量备份 + 收集期间修改指令
4. Master 将 RDB + 操作指令全量同步给 Slave（第一次全量同步）
5. 建立关系后，Master 定期向 Slave 发送心跳（repl-ping-replica-period，默认10秒）
6. Master 持续将后续修改指令传递给 Slave，记录offset偏移量
7. Slave 短暂不回复心跳 → Master 停止同步
8. Slave 重新上线 → Master 从 offset 开始继续同步
```

### 5、主从复制的缺点

1. **复制延时**：所有写先 Master 再同步 Slave，一定有延迟；系统繁忙时更严重
2. **Master 的高可用问题**：Master 挂了，Slave 不会自动切换，只能人工干预
3. **数据安全**：牺牲了高可用，但增加了数据安全

---

## 四、Redis哨兵集群（Sentinel）

### 1、Sentinel 四大作用

| 作用 | 说明 |
|------|------|
| **主从监控** | 监控主从 Redis 运行是否正常 |
| **消息通知** | 将故障转移结果发送给客户端 |
| **故障转移** | Master 异常时，自动主从切换 |
| **配置中心** | 客户端连接哨兵获取当前 Master 地址 |

### 2、核心配置

```
sentinel monitor <master-name> <ip> <redis-port> <quorum>
```

`quorum` 是最关键的参数。

### 3、工作原理详解

#### S_DOWN（主观下线） vs O_DOWN（客观下线）

```
Sentinel 持续向 Master 发送心跳
         ↓
超过 down-after-milliseconds（默认30秒）没响应
         ↓
S_DOWN（主观下线）：单个 Sentinel 认为 Master 挂了
         ↓
超过 quorum 个 Sentinel 都认为 S_DOWN
         ↓
O_DOWN（客观下线）：集群确认 Master 确实挂了
         ↓
开始故障切换
```

**为什么需要 S_DOWN → O_DOWN**：防止网络抖动造成的误判！

**最佳实践**：Sentinel 搭建奇数个节点，quorum 设为过半。

#### 故障切换四步骤

```
1. Master 变 O_DOWN → Sentinel 集群选举一个 Leader（Raft 算法）
2. Leader 在健康 Slave 中选择新的 Master：
   ① replica-priority 最低的（默认100）
   ② 复制偏移量 offset 最大的（数据最全）
   ③ RunID 字典顺序最小的
3. 新 Master 执行 slave of no one → 提升为 Master
   其他 Slave 执行 slave of → 指向新 Master
4. 旧 Master 恢复 → 降级为 Slave，从新 Master 同步数据
```

选举采用 **Raft 算法**（多数派一致）：超过半数节点投票同意 → 成为最终决议。这也是 quorum 建议设为过半的原因。

### 4、Sentinel 的缺点

1. **对客户端不友好**：Master 切换后客户端要频繁切换写请求地址
2. **数据不安全**：Master 宕机时，已完成但未同步的操作会彻底丢失（新 Master 以自己数据为准）

---

## 五、Redis集群（Cluster）

### 1、Cluster 要解决的三个问题

1. 客户端需要频繁切换 Master 的问题
2. 服务端数据量太大后，单个复制集难以承担
3. Master 挂了之后，自动将 Slave 切换成 Master

### 2、核心配置

```conf
cluster-enabled yes
cluster-config-file nodes-6379.conf
cluster-node-timeout 5000
```

**完整集群配置文件示例**：
```conf
bind * -::*
daemonize yes
protected-mode no
requirepass 123qweasd
masterauth 123qweasd
port 6381
cluster-enabled yes
cluster-config-file nodes-6381.conf
cluster-node-timeout 5000
logfile "/root/myredis/cluster/redis6381.log"
pidfile /var/run/redis_6381.pid
appendonly yes
dir "/root/myredis/cluster"
appenddirname "aof"
appendfilename "appendonly6381.aof"
dbfilename "dump6381.rdb"
```

**创建集群**：
```bash
redis-cli -a 123qweasd --cluster create \
  --cluster-replicas 1 \
  192.168.65.214:6381 192.168.65.214:6382 192.168.65.214:6383 \
  192.168.65.214:6384 192.168.65.214:6385 192.168.65.214:6386
```

**连接集群**：
```bash
redis-cli -p 6381 -a 123qweasd -c   # -c 表示集群模式
```

**集群演示**：
```
127.0.0.1:6381> set k1 v1
-> Redirected to slot [12706] located at 192.168.65.214:6383   # 自动重定向！
OK

192.168.65.214:6383> set k2 v2
-> Redirected to slot [449] located at 192.168.65.214:6381     # 自动重定向！
OK
```

**验证高可用**：
```bash
# 关闭6383服务（Master）
redis-cli -a 123qweasd -p 6383 -c shutdown

# 查看集群状态 → 6384从slave切换成了master！
redis-cli -a 123qweasd -p 6381 -c cluster nodes

# 重新启动6383 → 6383变为6384的slave
redis-server redis6383.conf
```

### 3、详解 Slot 槽位

Redis 集群设置 **16384 个哈希槽**。每个 key 通过**CRC16校验后对16384取模**决定放哪个槽。

```
slot = CRC16(key) mod 16384
```

#### Slot 分配与 Reshard

```bash
# 增加节点
redis-cli -a 123qweasd -p 6381 --cluster add-node 192.168.65.214:6387 192.168.65.214:6388

# 检查集群状态 → 新节点没有 slot
redis-cli -a 123qweasd -p 6381 --cluster check 192.168.65.214:6381

# 手动触发 reshard
redis-cli -a 123qweasd -p 6381 reshard 192.168.65.214:6381
```

**Reshard 原理**：从旧节点分配部分槽位给新节点，只移动对应槽位的数据，不需要全量迁移。

#### 集群一致性保障

```conf
cluster-require-full-coverage yes  # 有槽位没被覆盖 → 集群停止服务
```

通常不建议改为 `no`，因为意味着数据服务不完整。

#### HashTag 机制

```
127.0.0.1:6381> CLUSTER KEYSLOT k1        → 12706
127.0.0.1:6381> CLUSTER KEYSLOT roy{k1}   → 12706  # 只计算{}内的
127.0.0.1:6381> CLUSTER KEYSLOT roy:k1    → 12349  # 不同的slot
```

**应用**：将有关系的 key 通过 HashTag 分到同一个 slot，解决跨槽批量操作问题：
```
mset user_{1}_name roy user_{1}_id 1 user_{1}_password 123
→ Redirected to slot [9842] located at 192.168.65.214:6382
```

#### 数据倾斜问题

常见解决两步：调整 key 结构（热点 key 打散）→ 调整 slot 分布（热点 slot 重新分配）

### 4、Gossip 协议与集群选举

**Gossip 协议消息类型**：

| 消息 | 作用 |
|------|------|
| `meet` | 通知新节点加入集群 |
| `ping` | 节点间心跳，交换元数据 |
| `pong` | 对 ping/meet 的回复，也可用于信息广播 |
| `fail` | 通知其他节点某节点宕机 |

**特点**：
- 去中心化，各节点通过 gossip 互相通信达成统一
- 数据同步有延迟，但每个节点负载不随节点数增长
- 不建议构建太大的 Redis 集群（节点太多 → 同步延迟增加）
- **每个节点有一个专门的 gossip 端口 = 服务端口 + 10000**（部署时注意防火墙）

**集群选举流程**：

```
1. Slave 发现自己的 Master 变为 FAIL
2. 将 currentEpoch +1，广播 FAILOVER_AUTH_REQUEST
3. 只有 Master 响应，判断合法性，每个 epoch 只发一次 ACK
4. Slave 收集 FAILOVER_AUTH_ACK
5. 收到超过半数 Master 的 ACK → 成为新 Master
   （为什么至少3个主节点？2个的话，挂1个只剩1个，无法过半）
6. Slave 广播 Pong 通知其他节点
```

**选举延迟**：
```
DELAY = 500ms + random(0~500ms) + SLAVE_RANK * 1000ms
```

SLAVE_RANK 越小 = 已复制数据越新 → 持有最新数据的 slave 最先发起选举（理论上）。

### 5、Cluster 数据安全

```
min-replicas-to-write 3    # 至少3个Replica在线才允许写
min-replicas-max-lag 10    # Replica延迟不超过10秒
```

> Gossip 协议不保证强一致性，在特定条件下（如脑裂）可能丢失部分写入。有良好运维支撑，通常可以认为 Redis 集群数据是安全的。

---

## 六、数据安全性方案总结

```
单机持久化 → 主从复制 → 哨兵集群 → Redis Cluster
   (数据不丢)  (数据备份)  (自动切换)  (分布式+高可用)
```

**整体建议**：
- Redis 通常不建议作为独立数据库，更多发挥**高性能缓存**优势
- 有靠谱运维支撑，Redis 做数据库**完全可行**（如 Redis Cloud 提供数据库实例）
- Redis 企业版核心就在高可用和数据安全上提供了更全面支持

> 有道云笔记链接：[Redis数据安全性分析](https://note.youdao.com/s/Bwu9bklN)
