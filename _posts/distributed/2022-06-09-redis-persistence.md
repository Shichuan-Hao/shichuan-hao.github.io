---
title: "Redis 数据持久化与高可用架构深入剖析"
date: 2022-06-09
categories: distributed
tags: [Redis, 持久化, RDB, AOF, 主从复制, Sentinel, Cluster, gossip, 数据安全]
mermaid: true
---

> 从数据安全性的角度，重新理解 Redis 的集群架构。不是教你怎么用 Redis，而是教你怎么把 Redis 用得比别人深一点。

## 一、Redis 性能压测：建立性能基准线

Redis 所有数据保存在内存中，性能非常强悍。但内存断电即丢失。真实项目中需要针对应用场景估算 Redis 性能，在**数据安全性**与**读写性能**之间找到平衡点。

Redis 提供了压测脚本 `redis-benchmark`：

```bash
# 20个并发线程，100万请求，测试 set 指令
redis-benchmark -a 123qweasd -t set -n 1000000 -c 20
```

输出示例：

```
Summary:
  throughput summary: 116536.53 requests per second
  latency summary (msec):
          avg       min       p50       p95       p99       max
        0.111     0.032     0.111     0.167     0.215     3.199
```

**平均每秒 11 万次写操作，p99 延迟仅 0.215ms**——这就是 Redis 纯内存运作的恐怖性能。后续每调整一次部署架构，都应该跑一次 benchmark 做对比。

---

## 二、Redis 持久化机制全景

官网：[Redis Persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)

Redis 提供了三种持久化策略：

| 策略 | 说明 |
|------|------|
| **无持久化** | 完全关闭持久化，Redis 仅作缓存使用 |
| **RDB** (Redis Database) | 按时间间隔保存全量数据快照 |
| **AOF** (Append Only File) | 记录每次写操作，通过操作重演恢复数据 |
| **RDB + AOF** | 混合使用，兼顾恢复速度和数据安全性 |

### 2.1 RDB 深度解析

#### RDB 做什么
RDB 在指定时间间隔，备份当前时间点**内存中的全部数据集**，保存到磁盘文件（通常是 `dump.rdb`）。恢复时直接将快照文件读回内存。

由于 RDB 存的是全量数据，你甚至可以直接用它来传递数据——例如从一个 Redis 实例将数据同步到另一个同版本实例，只需复制最近的 RDB 文件。

#### 核心配置参数

**1. save 策略**（最核心配置）：

```
save <seconds> <changes> [<seconds> <changes> ...]
```

默认配置（注释掉但生效）：
```
save 3600 1     # 1小时内至少有1次修改
save 300 100    # 5分钟内至少有100次修改
save 60 10000   # 1分钟内至少有10000次修改
```

配置 `save ""` 可完全禁用 RDB 快照。

**2. 其他重要参数**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `dbfilename` | RDB 文件名 | `dump.rdb` |
| `dir` | 文件目录 | `./` |
| `rdbcompression` | 是否启用 LZF 压缩 | `yes` |
| `stop-writes-on-bgsave-error` | bgsave 失败时是否停止写入 | `yes` |
| `rdbchecksum` | 是否用 CRC64 校验（+10% CPU 开销） | `yes` |

#### RDB 触发时机

1. **自动触发**：达到 `save` 配置条件
2. **手动触发**：
   - `save`：主线程执行，**阻塞**所有客户端请求，直到备份完成
   - `bgsave`：fork 子进程执行，**不阻塞**主线程，但需要复制一份内存，占更多 CPU/内存
3. **主从复制时**：master 触发 RDB 全量同步给 slave

使用 `LASTSAVE` 指令查看最后一次成功快照的时间（Unix 时间戳），Linux 上 `date -d @{timestamp}` 可格式化。

#### RDB 优缺点分析

| 优点 | 缺点 |
|------|------|
| 文件紧凑，适合定期备份 | 不能实时备份，总会有数据丢失 |
| 适合灾难恢复 | fork 子进程时复制内存，大数据量下可能造成短暂服务停用 |
| 对主线程性能几乎无影响（子进程完成） | 与 AOF 相比，重启大数据量时 AOF 可通过 base RDB 快速恢复 |
| 重启恢复速度快 | — |

---

### 2.3 AOF 深度解析

#### AOF 做什么

以日志形式记录**每一个写操作**（读操作不记录），只允许追加不允许改写。Redis 重启时，通过**重演 AOF 中的指令**恢复数据。

#### Redis 7 的 AOF 文件结构变化

这是 Redis 7 最重要的改进之一。**之前是一个文件，现在变成了三个文件**：

```
appendonly.aof.1.base.rdb     # 二进制 RDB 快照（基础数据）
appendonly.aof.1.incr.aof     # 增量操作日志（文本格式）
appendonly.aof.manifest       # 元信息文件（记录文件顺序和类型）
```

> Redis 7 之前，AOF 文件中也包含 RDB 二进制部分和 AOF 文本部分。Redis 7 将它们分成独立文件，既可以分别恢复，也便于控制 AOF 文件大小。
>
> 拆分增量文件的方式，还能进一步控制单个文件大小。

这意味着 **Redis 7 的 AOF 已经内置了 RDB + AOF 混合能力**。

#### 核心配置参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `appendonly` | 是否开启 AOF | `no` |
| `appendfilename` | AOF 文件基础名 | `appendonly.aof` |
| `appenddirname` | AOF 文件目录（Redis 7 新增） | `appendonlydir` |
| `appendfsync` | 同步策略 | `everysec` |
| `auto-aof-rewrite-percentage` | 重写触发百分比 | `100` |
| `auto-aof-rewrite-min-size` | 重写触发最小大小 | `64mb` |
| `no-appendfsync-on-rewrite` | 重写期间是否同步 | `no` |

**`appendfsync` 三种策略**：

| 值 | 说明 |
|------|------|
| `always` | 每次写操作都 fsync，数据最安全，性能最低 |
| `everysec` | 每秒 fsync 一次，最多丢失 1 秒数据（**推荐**） |
| `no` | 交由操作系统决定何时刷盘，性能最高，安全性最低 |

**AOF 重写机制**：

Redis 会定期对 AOF 操作进行优化重写，让操作更精简。例如将多次 `INCR` 合并为一个 `SET`。在 Redis 7 中，重写时会生成新的 `base.rdb` 和 `incr.aof` 文件。

- 手动触发：`BGREWRITEAOF`
- 自动触发：AOF 文件增长到上次重写后大小的 100%（`auto-aof-rewrite-percentage`），且文件大小超过 64MB（`auto-aof-rewrite-min-size`）

#### AOF 文件内容解析：手写一个 Redis 客户端

AOF 中的增量文件记录的是 Redis **序列化协议（RESP）** 格式的指令。例如执行 `set k1 v1`，AOF 文件中记录：

```
*3          # 三个部分
$3          # 第一部分长度 3
SET         # 第一部分值
$2          # 第二部分长度 2
k1          # 第二部分值
$2          # 第三部分长度 2
v1          # 第三部分值
```

理解这个协议后，你可以**手写一个 Redis 客户端**：

```java
public class MyRedisClient {
    OutputStream write;
    InputStream reader;

    public MyRedisClient(String host, int port) throws IOException {
        Socket socket = new Socket(host, port);
        write = socket.getOutputStream();
        reader = socket.getInputStream();
    }

    // auth 123qweasd
    public String auth(String password) {
        StringBuffer command = new StringBuffer();
        command.append("*2").append("\r\n");           // 参数数量
        command.append("$4").append("\r\n");           // 第一个参数长度
        command.append("AUTH").append("\r\n");         // 第一个参数值
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

    // set k4 v4
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

    public static void main(String[] args) throws IOException {
        MyRedisClient client = new MyRedisClient("192.168.65.214", 6379);
        System.out.println(client.auth("123qweasd"));
        System.out.println(client.set("test", "test"));
    }
}
```

这就是 RESP 协议的实现——Redis 的通信底层其实并不神秘，就是 TCP + 文本协议。

#### AOF 日志修复

如果 Redis 意外宕机，AOF 文件可能出现指令记录不完整的情况。此时 Redis 启动会失败：

```
# Bad file format reading the append only file
# make a backup of your AOF file, then use ./redis-check-aof --fix <filename.manifest>
```

修复方式：

```bash
redis-check-aof --fix appendonly.aof.1.incr.aof
```

修复过程会将最后一条不完整的指令删除。对于 RDB 文件也有 `redis-check-rdb` 修复工具，但 RDB 是二进制压缩格式，一般不太可能被篡改。

---

### 2.4 混合持久化策略：RDB + AOF

两种策略各有优劣，Redis 支持同时开启：

```
aof-use-rdb-preamble yes
```

**数据恢复优先级**：Redis 重启时**优先选择 AOF 文件恢复**。因为 AOF 数据集通常比 RDB 更完整。同时 AOF 现在已包含 RDB 格式（base.rdb），恢复效率也很高。

**但依然建议保留 RDB 定期备份**：AOF 数据不断变化，不太利于定期做冷备份。保留 RDB 文件作为数据安全的最后保障。

> ⚠️ 持久化只能保证**单机**的数据安全。如果服务器磁盘坏了，再好的持久化策略也没用。要保证数据安全，就必须引入集群化方案。

---

## 三、主从复制（Replica）机制

> 主从复制 → 哨兵集群 → Redis Cluster，这三者是层层递进的。

### 3.1 基本概念

官网：[Redis Replication](https://redis.io/docs/latest/operate/oss_and_stack/management/replication/)

```
  +------------------+      +---------------+
  |      Master      | ---> |    Replica    |
  | (receive writes) |      |  (exact copy) |
  +------------------+      +---------------+
```

核心要点：
- Redis 复制是**异步**的
- 可以配置当 slave 数量不足时 master 拒绝写入
- slave 支持**部分重同步**（断线重连后增量同步）
- 复制是自动的，网络分区后 slave 会自动重连

**最典型的作用**：
1. **读写分离**：master 以写为主，slave 以读为主
2. **数据备份 + 容灾恢复**

### 3.2 核心配置

一个原则：**配从不配主**。可以在几乎不影响运行中的 Redis 服务的情况下，为其配置从节点。

```bash
# 配置文件中
REPLICAOF host port

# 运行时动态修改
SLAVEOF host port       # 成为指定节点的 slave
SLAVEOF NO ONE          # 取消主从关系，自己成为 master
```

### 3.3 确认主从状态

**在 master 上**：

```
127.0.0.1:6379> info replication
# Replication
role:master
connected_slaves:1
slave0:ip=192.168.65.214,port=6380,state=online,offset=56,lag=1
master_replid:56a1835bdb1f02d2398fac3c34a321e665b07d36
```

重点关注 slave 的 `state` 状态和 `offset` 偏移量。刚建立 Replica 时，offset 是逐步推进的。

**在 slave 上**：

```
127.0.0.1:6380> info replication
# Replication
role:slave
master_host:192.168.65.214
master_port:6379
master_link_status:up           # 重点关注连接状态
slave_read_only:1               # 从库默认只读
```

### 3.4 从库禁止写数据

```bash
127.0.0.1:6380> set k4 v4
(error) READONLY You can't write against a read only replica.
```

配置 `replica-read-only yes` 保证从库只读。但注意：**从库虽然禁止数据写操作，但没有禁止 CONFIG、DEBUG 等管理指令**。如果这些指令与主节点不一致，容易造成数据不一致。

**企业级安全实践**：通过 `rename-command` 屏蔽危险指令：

```
rename-command CONFIG ""
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
```

### 3.5 主从复制完整工作流程

```
┌─────────┐                    ┌─────────┐
│  Slave  │                    │  Master │
└────┬────┘                    └────┬────┘
     │         1. sync 请求          │
     │─────────────────────────────>│
     │                              │ 2. 触发 RDB 全量备份
     │                              │    同时收集写指令缓存
     │    3. RDB + 操作指令全量同步    │
     │<─────────────────────────────│
     │ 4. slave 删除旧数据，加载新数据  │
     │                              │
     │    5. 心跳包（默认10秒间隔）     │
     │<────────────────────────────>│
     │                              │
     │    6. 增量同步（offset 跟踪）   │
     │<─────────────────────────────│
```

**详细步骤**：

1. Slave 启动后，向 master 发送 `sync` 请求，等待连接建立。建立成功后，slave **删除自己的数据日志文件**，等待主节点同步
2. Master 收到 sync 请求后，触发一次 **RDB 全量备份**，同时收集此期间所有新收到的写指令
3. Master 将 RDB 快照 + 缓存的写指令全量同步给 slave，完成第一次全量同步
4. 主从关系建立后，master 定期向 slave 发送心跳（`repl-ping-replica-period` 参数，默认 10 秒）
5. Slave 持续回复心跳，master 持续将写指令增量同步给 slave，通过 `master_repl_offset` 记录已同步的偏移量
6. 如果 slave 短暂不回复心跳，master 停止同步。slave 重新上线后，master 从上次的 offset 继续增量同步

### 3.6 主从复制的缺点

1. **复制延时、信号衰减**：所有写操作先在 master 操作再同步到 slave，一定有延迟。系统繁忙或 slave 数量增加时更加严重
2. **Mater 高可用问题**：master 挂了，slave **不会自动切换**。只能人工干预——重启 master，或手动将某个 slave 切换为 master，再调整其他 slave 的主节点
3. **从数据安全性角度**：主从复制牺牲了服务高可用，但增加了数据安全（多副本）

> 这就是 Sentinel 要解决的问题——当检测到 master 宕机后，自动从 slave 中选择一个节点提升为 master。

---

## 四、Redis 哨兵集群（Sentinel）

> Sentinel 不负责数据读写，它负责给 Replica 主从复制提供**高可用**能力。

### 4.1 Sentinel 四大职责

| 职责 | 说明 |
|------|------|
| **主从监控** | 监控主从 Redis 运行是否正常 |
| **消息通知** | 将故障转移结果发送给客户端 |
| **故障转移** | Master 异常时自动进行主从切换 |
| **配置中心** | 客户端通过连接哨兵获取当前 master 地址 |

### 4.2 核心配置

```bash
# sentinel.conf
sentinel monitor <master-name> <ip> <redis-port> <quorum>
```

最关键的参数是这个 **`quorum`**——这直接关系到 Sentinel 如何判定 master 真正宕机。

### 4.3 工作原理：S_DOWN 与 O_DOWN

#### 第一步：如何发现 master 宕机？

```
  每个 Sentinel 持续向 master 发送心跳
          │
          ▼
  超过 down-after-milliseconds 没收到响应（默认30秒）
          │
          ▼
  S_DOWN（主观下线）：这一个 Sentinel 认为 master 挂了
          │
          ▼
  Sentinel 之间互相沟通，交换对 master 状态的判断
          │
          ▼
  超过 quorum 个 Sentinel 都认为 master S_DOWN
          │
          ▼
  O_DOWN（客观下线）：集群确认 master 真正宕机，开始故障转移
```

> **S_DOWN（主观下线）**：单个 Sentinel 的主观判断。可能是网络抖动造成的误判。
>
> **O_DOWN（客观下线）**：多个 Sentinel 达成共识后的结论，排除误判可能。

**quorum 的建议值**：Sentinel 集群搭建**奇数个节点**，quorum 配置为**超半数**，最大化保证可用性。

#### 第二步：如何切换新的 master？

从 Sentinel 日志可以看到完整过程：

```
1. Master 变成 O_DOWN
2. Sentinel 集群选举一个 Sentinel 作为 Leader
   ↓ 采用 Raft 算法，超半数节点投票同意
3. Leader 在健康的 Slave 中选举新的 Master
   ↓ 选举规则见下
4. Leader 对新 Master 执行 SLAVEOF NO ONE，提升为 Master
5. Leader 对其他 Slave 执行 SLAVEOF 新Master
6. 旧 Master 恢复后 → 降级为 Slave，从新 Master 同步数据
7. 最终配置覆盖到各 Redis 的 redis.conf
```

**新 Master 的选举规则**（优先级递减）：

```
1. replica-priority 最低的从节点（默认值100）
           ↓ 如果相同
2. 复制偏移量 offset 最大的从节点（数据最新最全）
           ↓ 如果相同
3. RunID 字典顺序最小的节点
```

### 4.4 Sentinel 的缺点

1. **对客户端不友好**：master 切换后，客户端需要将写请求重新指向新 master
2. **数据不安全**：主从复制集群中，所有数据以 master 为准。master 宕机时，已经完成但还没同步给 slave 的操作会彻底丢失。因为只要 master 一切换，所有数据就以新 master 为准了

> 因此，企业实际运用中，更多的是用 Redis Cluster。

---

## 五、Redis 集群（Cluster）

> 将多组 Redis Replica 主从集群整合到一起，像一个 Redis 服务一样对外提供服务。**Redis Cluster 的核心依然是 Replica 复制集。**

### 5.1 Cluster 要解决的三个核心问题

| 问题 | Cluster 的解决方案 |
|------|-------------------|
| 客户端需频繁切换 master | Redis Cluster 自动重定向 |
| 单复制集数据量太大 | 数据分片到多个 master 节点 |
| master 挂了自动切换 | 每个 master 有 slave，自动 failover |

### 5.2 核心配置与搭建

```bash
# redis.conf
cluster-enabled yes
cluster-config-file nodes-6379.conf
cluster-node-timeout 5000
```

完整的集群节点配置示例：

```bash
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

依次创建 6 个节点（6381-6386）：

```bash
redis-server redis6381.conf
redis-server redis6382.conf
# ... 以此类推到 6386

# 创建集群：3主3从
redis-cli -a 123qweasd --cluster create --cluster-replicas 1 \
  192.168.65.214:6381 192.168.65.214:6382 192.168.65.214:6383 \
  192.168.65.214:6384 192.168.65.214:6385 192.168.65.214:6386

# 验证集群
redis-cli -p 6381 -a 123qweasd -c
> cluster nodes
> cluster info
```

### 5.3 Cluster 自动重定向验证

```bash
127.0.0.1:6381> set k1 v1
-> Redirected to slot [12706] located at 192.168.65.214:6383
OK

192.168.65.214:6383> set k2 v2
-> Redirected to slot [449] located at 192.168.65.214:6381
OK
```

数据根据 key 自动路由到对应的 master 节点，客户端**自动跟随重定向**，解决了"客户端频繁切换 master"的问题。

### 5.4 故障转移验证

```bash
# 关闭 6383（一个 master）
redis-cli -a 123qweasd -p 6383 -c shutdown

# 重新查看集群状态
redis-cli -a 123qweasd -p 6381 -c cluster nodes
```

可以看到 6384 从 `slave` 变成了 `master`，6383 标记为 `master,fail`。重新启动 6383 后，它变成了 6384 的 slave。整个过程**自动完成**，不需要人工干预。

> 也可以手动触发：在 slave 节点上执行 `CLUSTER FAILOVER` 即可触发故障转移。

### 5.5 Slot 槽位机制详解

Redis 集群设置 **16384 个哈希槽**（0-16383）。每个 key 通过 `CRC16(key) mod 16384` 决定放到哪个槽。集群中每个 master 负责一部分 hash 槽。

#### 如何分配 Slot？

```bash
# 增加新节点 6387、6388
redis-cli -a 123qweasd -p 6381 --cluster add-node \
  192.168.65.214:6387 192.168.65.214:6388

# 手动触发 reshard，重新分配槽位
redis-cli -a 123qweasd -p 6381 --cluster reshard 192.168.65.214:6381
```

reshard 只会**移动那部分槽位对应的数据**，不需要全量迁移。

> 注：如果负责某部分槽位的**所有**节点（master + 所有 slave）都挂了，Cluster 默认停止服务。可通过 `cluster-require-full-coverage no` 强制继续服务，但通常不建议这样做。

#### key 与 Slot 的对应关系

```bash
127.0.0.1:6381> CLUSTER KEYSLOT k1
(integer) 12706
```

**批量操作的问题**：

```bash
127.0.0.1:6381> mset k1 v1 k2 v2 k3 v3
(error) CROSSSLOT Keys in request don't hash to the same slot
```

跨槽的批量操作无法保证原子性——这本质上是一个**分布式事务问题**。分布式事务非常复杂（不要以为用 Seata 就能轻松解决），大部分业务场景下**直接拒绝分布式事务**是一种很好的策略。

**Hash Tag 解决方案**：

```bash
127.0.0.1:6381> CLUSTER KEYSLOT roy{k1}
(integer) 12706
127.0.0.1:6381> CLUSTER KEYSLOT k1
(integer) 12706
127.0.0.1:6381> CLUSTER KEYSLOT roy:k1
(integer) 12349    # 不同的 slot！
```

大括号 `{}` 中的内容决定 key 的 hash slot。使用相同的 hash tag：

```bash
127.0.0.1:6381> mset user_{1}_name roy user_{1}_id 1 user_{1}_password 123
-> Redirected to slot [9842] located at 192.168.65.214:6382
OK
```

#### 数据倾斜问题及解决

大量数据集中存储在集群中某一个热点节点上，造成该节点负载明显大于其他节点。

**解决思路**：
1. 调整 key 结构，将热点 key 尽量平均分配到各个 slot
2. 调整 slot 分布，将数据量大、访问频繁的热点 slot 重新分配到不同节点

### 5.6 Gossip 协议

Redis 集群**去中心化**，各个节点之间通过 **Gossip 协议**频繁通信，交换节点状态和集群元数据。

**四种消息类型**：

| 消息 | 作用 |
|------|------|
| `meet` | 通知新节点加入集群 |
| `ping` | 节点间发送心跳，携带自身状态和集群元数据 |
| `pong` | 对 ping/meet 的响应，也用于信息广播 |
| `fail` | 通知其他节点：某个节点已宕机 |

**Gossip 协议的特点**：

- 节点间**陆陆续续**同步元数据，不是瞬间全网同步——有一定延迟
- **好处**：节点数量增加时，每个节点的负载几乎恒定（O(1) 复杂度），因此可以构建大量节点
- **坏处**：数据同步有延迟，节点太多时延迟增加——对 Redis 不适用。所以**不建议构建太大的 Redis 集群**
- 每个节点都有专门的 Gossip 通信端口：**服务端口 + 10000**（防火墙不要屏蔽）

### 5.7 Cluster 选举流程

当 slave 发现自己的 master 变为 `FAIL` 状态时：

```
1.  slave 将 currentEpoch 加 1（通过 cluster info 查看）
2.  slave 广播 FAILOVER_AUTH_REQUEST 信息
3.  只有其他 master 节点响应，返回 FAILOVER_AUTH_ACK
    每个 epoch 每个 master 只投一次票
4.  slave 收集 master 的 ACK 投票
5.  收到 > 半数 master 的 ACK 后，成为新 master
    （这解释了为什么 Cluster 至少需要 3 个主节点——
     2 个主节点时，挂 1 个只剩 1 个，无法超过半数）
6.  slave 广播 Pong 消息通知所有节点
```

**延迟选举机制**：slave 并不立即发起选举，而是有一定延迟：

```
DELAY = 500ms + random(0 ~ 500ms) + SLAVE_RANK × 1000ms
```

- `SLAVE_RANK` 越小表示已复制的数据越新（offset 越大）
- 持有**最新数据**的 slave 将**最先发起选举**——这是非常聪明的优先级设计

### 5.8 Cluster 数据安全到底如何？

**稳定状态下，Cluster 是能保证数据安全的**：

每个 master 都有 slave 即时备份。master 宕机，slave 自动切换。

还有两个参数进一步保证数据安全：

```
min-replicas-to-write 3    # 至少 3 个 slave 在线才接受写入
min-replicas-max-lag 10    # slave 延迟超过 10 秒不计数
```

**但要注意**：Gossip 协议在同步元数据时不保证强一致性。在特定条件下（如网络抖动造成的脑裂），Cluster 可能丢失一些已被接收的写入。这些条件通常比较苛刻，出现概率小。

> **结论**：在有良好运维支持的情况下，Redis Cluster 的数据是安全的。甚至有 Redis Cloud 云服务可以直接作为数据库使用。

---

## 六、总结：数据安全性视角看 Redis 架构演进

```
单机无持久化          → 纯缓存模式，无数据安全
    ↓
单机 + RDB/AOF       → 裸盘持久化，单机故障可恢复
    ↓
主从复制（Replica）    → 数据多副本，读写分离，但无自动故障转移
    ↓
哨兵集群（Sentinel）   → 自动故障转移，但客户端需感知切换，数据可能丢失
    ↓
Redis Cluster         → 数据分片 + 自动故障转移 + 客户端自动重定向
```

> Redis 基于内存和硬盘的成本对比，通常不建议作为独立数据库使用。大部分情况下，发挥其高性能优势作为缓存使用是最佳实践。但如果有非常靠谱的运维支撑，Redis 作为数据库也完全可行。
