---
title: "ZooKeeper Leader 选举源码剖析与 ZAB 一致性协议"
date: 2022-06-17
categories: distributed
tags: [ZooKeeper, Leader选举, ZAB协议, 源码分析, 分布式一致性, QuorumPeer]
mermaid: true
---

> "为什么 ZK 选举需要奇数节点？"、"ZAB 和 Raft 有什么区别？"——这些面试题的本质是对 ZK Leader 选举流程和 ZAB 协议的深入理解。本文从源码启动 ZK 开始，走进 QuorumPeer 选举引擎的核心，拆解 ZAB 协议的四个阶段。

## 一、从源码启动 ZooKeeper

### 1.1 获取源码

```bash
git clone https://github.com/apache/zookeeper.git
# 选择分支 3.5.8
```

`org.apache.zookeeper.Version` 类会报错，需手动创建辅助类：

```java
package org.apache.zookeeper.version;
public interface Info {
    int MAJOR = 1;
    int MINOR = 0;
    int MICRO = 0;
    String QUALIFIER = null;
    int REVISION = -1;
    String REVISION_HASH = "1";
    String BUILD_DATE = "2020-10-15";
}
```

编译：

```bash
mvn clean install -DskipTests
```

### 1.2 找到入口类

从 `bin/zkServer.sh` 中找到主类：

```
org.apache.zookeeper.server.quorum.QuorumPeerMain
```

这就是 ZK 集群模式的启动入口。

**注意事项**：
1. 将 `conf/zoo_sample.cfg` 复制为 `zoo.cfg`，配置到启动参数
2. `pom.xml` 中除 jline 外的 scope=provided 依赖要注释掉
3. `log4j.properties` 复制到 `target/classes` 目录

### 1.3 从源码启动集群

复制 3 个不同端口的 `zoo.cfg`，在每个 data 目录中创建 `myid` 文件，配置三个不同的启动节点。

---

## 二、Leader 选举架构

### 2.1 选举双层队列架构

```
┌─────────────────────────────────────────────┐
│              选举应用层                       │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ 统一接收队列  │  │   统一发送队列         │  │
│  │ (所有机器)   │  │ (所有机器共享)        │  │
│  └─────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────┤
│              消息传输层                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ 机器1队列 │ │ 机器2队列 │ │ 机器3队列 │     │
│  │ (独立)   │ │ (独立)   │ │ (独立)   │     │
│  └──────────┘ └──────────┘ └──────────┘     │
└─────────────────────────────────────────────┘
```

> **设计思想**：传输层按目标机器拆分队列，某台机器出问题发送失败时**不影响对正常机器的消息发送**。这是典型的高可用架构设计。

### 2.2 投票对比规则

```java
protected boolean totalOrderPredicate(
    long newId, long newZxid, long newEpoch,
    long curId, long curZxid, long curEpoch) {

    return ((newEpoch > curEpoch)
            || ((newEpoch == curEpoch)
                && ((newZxid > curZxid)
                    || ((newZxid == curZxid)
                        && (newId > curId)))));
}
```

**优先级顺序**：epoch > zxid > myid

### 2.3 zxid 的内部结构

```java
public class ZxidUtils {
    public static long getEpochFromZxid(long zxid) {
        return zxid >> 32L;          // 高 32 位 = epoch
    }
    public static long getCounterFromZxid(long zxid) {
        return zxid & 0xffffffffL;   // 低 32 位 = counter
    }
    public static long makeZxid(long epoch, long counter) {
        return (epoch << 32L) | (counter & 0xffffffffL);
    }
}
```

```
zxid (64位):
├───────── 高 32 位 ─────────┤├───────── 低 32 位 ─────────┤
│         epoch              │         counter            │
│    (选举周期)               │    (事务递增计数器)         │
└───────────────────────────┘└───────────────────────────┘
```

- **epoch**：每轮选举自增，用来区分不同的 Leader 周期
- **counter**：同一 epoch 内，每个事务递增，保证事务顺序

---

## 三、Leader 选举详细流程

### 3.1 启动期选举

场景：三节点集群依次启动

```
节点1(myid=1) 启动:
  → 投票给自己 (epoch=0, zxid=0, id=1)
  → 等待其他节点连接（半数次投票 = 2票才可当选）
  → 阻塞等待...

节点2(myid=2) 启动:
  → 投票给自己 (epoch=0, zxid=0, id=2)
  → 收到节点1的投票
  → 比较：epoch相同=0, zxid相同=0, id: 2>1 → 赢
  → 改投票给节点2
  → 等待...

节点3(myid=3) 启动:
  → 投票给自己 (epoch=0, zxid=0, id=3)
  → 收到节点1和节点2的投票（都投节点2）
  → 比较：epoch相同, zxid相同, id: 3>2 → 赢
  → 改投票给节点3
  → 节点2收到节点3的投票，比较后也改投节点3
  → 节点3获得超过半数投票 → 成为 Leader
```

**关键点**：
1. 每个节点初始投票给自己
2. 收到更大 epoch/zxid/id 的投票后，更新自己的投票
3. 获得**超过半数**投票的节点成为 Leader
4. 这就是为什么 ZK 集群需要**奇数个节点**——2N+1 个节点可容忍 N 个故障

### 3.2 运行期选举（Leader 宕机）

```
Leader(节点3) 宕机:
  → 节点1 和 节点2 感知 Leader 心跳超时 → 进入 LOOKING 状态
  → epoch + 1 (新选举轮次)
  → 节点1: epoch=1, zxid=100, myid=1 → 投票给自己
  → 节点2: epoch=1, zxid=100, myid=2 → 投票给自己
  → 比较：epoch相同=1, zxid相同=100, id: 2>1 → 节点2胜
  → 节点1 改投节点2，节点2 获得超过半数 → 成为新 Leader
```

---

## 四、ZAB 协议详解

> **ZAB（ZooKeeper Atomic Broadcast）** 是为 ZK 专门设计的崩溃恢复原子广播协议。它确保集群中所有节点接收和处理事务请求的顺序一致。

### 4.1 ZAB 协议的四个阶段

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Leader选举  │ →  │  发现阶段     │ →  │  同步阶段     │ →  │  广播阶段     │
│ (Election)  │    │ (Discovery)  │    │ (Synchronization)│  │  (Broadcast) │
└─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

#### 阶段 1：Leader 选举

此时集群**没有 Leader**。所有节点状态为 **LOOKING**。通过选举算法选出 epoch 最大的节点作为准 Leader。

#### 阶段 2：发现阶段

Leader 收集所有 Follower 的最新 epoch（即上一轮接受提议的最后 epoch）。从中选出最大的 epoch，并在此基础上加 1 作为**新 epoch**。

#### 阶段 3：同步阶段

Leader 将最新的数据同步到所有 Follower。过半 Follower 同步完成并 ACK 后，进入广播阶段。

#### 阶段 4：广播阶段

Leader 接收客户端请求，将提案广播给所有 Follower。过半 Follower 写入日志并 ACK 后，Leader 提交该提案并回复客户端。

### 4.2 广播阶段的详细流程

```
Client  →  Leader  发送写请求
              │
              ▼
         Leader 生成 Proposal（zxid递增）
              │
              ▼
         Leader 广播 Proposal 给所有 Follower
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
  Follower 1  Follower 2  Follower 3
    写入日志    写入日志    写入日志
    返回ACK     返回ACK     返回ACK
    │         │         │
    └─────────┼─────────┘
              ▼
    超过半数 Follower 返回 ACK？
         │         │
        YES        NO
         │         │
         ▼         ▼
  Leader 提交   不提交,等待
  回复Client
         │
         ▼
  Leader 发送 COMMIT 给 Follower
         │
         ▼
  Follower 提交并应用到内存
```

**简化版两阶段提交（2PC）**：
- 阶段一：广播 Proposal + 收集 ACK
- 阶段二：广播 COMMIT

但与传统 2PC 不同的是，ZAB 只需要**超过半数 ACK** 即可提交（不需要全部 ACK），这是分布式一致性的经典权衡。

### 4.3 ZAB 与 Raft 的对比

| 维度 | ZAB | Raft |
|------|-----|------|
| Leader 选举 | 先比较 epoch，再比较 zxid（事务ID） | 先比较 term，再比较 log index |
| 日志复制 | Proposal → ACK → Commit（两阶段） | AppendEntries RPC（类两阶段） |
| 成员变更 | 较复杂的**重配置**机制 | 联合共识（Joint Consensus），更清晰 |
| 实现复杂度 | 相对复杂 | 设计更清晰，便于理解 |
| 恢复机制 | 发现+同步阶段 | 日志匹配+快照 |

> ZAB 在 ZooKeeper 3.5+ 也引入了类似 Raft 的改进。实际面试中，掌握两者的核心设计理念和区别即可。

### 4.4 ZK 的数据一致性保证

| 保证 | 说明 |
|------|------|
| **全局可线性化写入** | 先到达 Leader 的写请求先被处理，Leader 决定顺序 |
| **客户端 FIFO 顺序** | 同一客户端发起的请求按发送顺序执行 |
| **过半 ACK** | 提案需超过半数 Follower 确认后才提交 |

---

## 五、源码阅读方法

看 ZK 源码的最佳路径：

1. **先使用**：通过 CLI 命令和 Java API 掌握基本使用
2. **抓主线**：从 `QuorumPeerMain` 入手，画源码主流程图
3. **画图做笔记**：找到选举、同步、广播等核心功能点，深入源码细节
4. **整合总结**：把所有图在脑中进行串联，形成完整画面

> 源码中 `QuorumPeer` 类是选举的核心引擎，`FastLeaderElection` 是默认的选举算法实现。

---

## 六、总结

| 要点 | 说明 |
|------|------|
| 入口类 | `QuorumPeerMain`，从 `zkServer.sh` 找到 |
| 选举优先级 | **epoch > zxid > myid** |
| zxid 结构 | 高 32 位 epoch + 低 32 位 counter |
| ZAB 四阶段 | 选举 → 发现 → 同步 → 广播 |
| 过半原则 | 选举和提交都需要超过半数节点确认 |
| 奇数节点 | 2N+1 个节点可容忍 N 个故障，且投票不出现平局 |
