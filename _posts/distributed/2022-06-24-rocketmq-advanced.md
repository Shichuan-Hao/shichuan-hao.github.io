---
title: "RocketMQ 进阶：源码解读、Dledger 集群与 MQ 常见问题"
date: 2022-06-24
categories: distributed
tags: [RocketMQ, 源码分析, Dledger, 事务消息, 消息可靠性, MQ面试]
mermaid: true
---

> 从客户端编程模型到 CommitLog 存储引擎，从 Dledger  自动故障转移到事务消息——这一章深入 RocketMQ 源码和设计方案，回答 MQ 三大经典面试题。

## 一、客户端编程模型

### 1.1 三种消息发送方式

| 方式 | 说明 | 可靠性 |
|------|------|--------|
| **同步发送** | 等待 Broker 确认后返回 | 高 |
| **异步发送** | 不等待确认，通过回调获取结果 | 中 |
| **单向发送** | 只发送不等待任何响应 | 低（可能丢失） |

```java
// 同步发送
SendResult result = producer.send(msg);

// 异步发送
producer.send(msg, new SendCallback() {
    @Override
    public void onSuccess(SendResult result) { ... }
    @Override
    public void onException(Throwable e) { ... }
});

// 单向发送
producer.sendOneway(msg);
```

### 1.2 消费模式再深化

| 模式 | 应用 |
|------|------|
| **集群消费**（默认） | 同一 Group 中每条消息只被消费一次 |
| **广播消费** | 每个 Consumer 都收到一样的消息 |
| **顺序消费** | 按发送顺序严格消费 |
| **延时消费** | 指定延迟时间后才投递 |

**顺序消费**的保障机制：
- Producer 端：将有序消息发往**同一个 Queue**
- Consumer 端：对 Queue 加**分布式锁**，保证同一 Queue 同一时间只被一个线程消费

---

## 二、RocketMQ 存储设计

### 2.1 CommitLog 核心设计

```
Producer 写消息
    ↓
CommitLog（所有 Topic 共享，顺序写盘）
    ↓
ConsumeQueue（按 Topic-Queue 维度建立索引）
    ↓
Consumer 拉取消息
```

**为什么 CommitLog 要设计成一个？**

> 传统 MQ（ActiveMQ/CQ）每个 Topic 单独建文件。Topic 一多，文件分散，**随机 IO 打满磁盘**。RocketMQ 把所有消息写入同一个 CommitLog，保证**顺序写盘**——这是解决"多 Topic IO 瓶颈"的核心设计。

### 2.2 文件存储结构

```
store/
  ├── commitlog/         # 核心消息存储
  │   └── 00000000000000000000
  │   └── 00000000001073741824      # 每个文件1GB
  ├── consumequeue/      # 消费队列索引
  │   └── topic-A/
  │       └── 0/         # Queue 0 的索引
  │       └── 1/         # Queue 1 的索引
  ├── index/             # 索引文件（按 key 查消息）
  └── config/            # 运行配置
```

**CommitLog 文件大小固定 1GB**。通过 MappedByteBuffer（内存映射文件）实现高效读写。

---

## 三、Dledger 高可用机制

### 3.1 为什么需要 Dledger？

传统主从复制：
- Master 写 → 异步同步到 Slave → 返回成功
- Master 宕机 → 手动或脚本切换 → 已经写入但未同步的数据**永久丢失**

Dledger 基于 **Raft 协议**实现：
- 消息写入需**超过半数**节点确认
- Leader 宕机后**自动选举**新 Leader
- 保证**已提交的数据不丢失**

### 3.2 Dledger 集群配置

```bash
# broker.conf
enableDLegerCommitLog=true
dLegerGroup=group-a
dLegerPeers=n0-192.168.1.1:40001;n1-192.168.1.2:40001;n2-192.168.1.3:40001
dLegerSelfId=n0
```

---

## 四、MQ 三大经典面试问题

### Q1：如何保证消息不丢失？

| 环节 | 丢失风险 | 解决方案 |
|------|---------|---------|
| **生产端** | 发送成功但 Broker 未刷盘就宕机 | 同步刷盘 / Dledger 集群 |
| **Broker 端** | 主从切换时未同步数据丢失 | 同步双写 / Dledger |
| **消费端** | 拉取后业务异常未 ACK | 业务幂等 + 重试机制 |

### Q2：如何保证消息不重复消费？

**根本原因**：MQ 保证的是"至少一次投递"（At Least Once），无法避免重复。

**解决方案**：
1. **消费端做好幂等**：基于业务唯一 ID 去重（数据库唯一索引、Redis 去重）
2. **消息携带唯一 ID**：生产者生成全局唯一消息 ID

### Q3：如何保证消息的顺序性？

**三个环节**：
1. **发送端**：有序消息发往**同一个 Queue**
2. **存储端**：RocketMQ CommitLog 内部保证顺序写入
3. **消费端**：同一 Queue 同一时间**只被一个线程消费**

> 顺序消息牺牲了一部分并发能力，仅在必要时使用。

---

## 五、事务消息

RocketMQ 的特色功能：解决**本地事务 + 消息发送**的原子性问题。

```
发送 Half 消息 → 执行本地事务 → 返回事务状态
                                  ↓
                      COMMIT → 消息可见
                      ROLLBACK → 消息丢弃
                      未知 → Broker 回查
```

**典型场景**：下单 → 扣减库存（本地事务）+ 发送订单消息（给下游系统）

---

## 六、总结

| 维度 | 要点 |
|------|------|
| 存储核心 | CommitLog 顺序写盘，所有 Topic 共享，ConsumeQueue 按队列建立索引 |
| 高可用 | 主从同步 → Dledger（Raft）→ 过半提交 + 自动选主 |
| 不丢消息 | 同步刷盘 + 同步双写 + Dledger |
| 不重复 | 消费端幂等（唯一ID + 去重） |
| 顺序性 | 同 Queue + 同线程，牺牲并发保证顺序 |
| 事务消息 | Half 消息 + 本地事务 + 回查机制 |
