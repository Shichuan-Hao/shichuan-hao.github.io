---
title: "Kafka 快速上手：从单机到集群，理解核心流转模型"
date: 2022-06-21
categories: distributed
tags: [Kafka, 消息队列, 消费者组, Partition, Broker, 集群]
mermaid: true
---

> Kafka 是全球最具影响力的开源 MQ，诞生于 LinkedIn 的海量日志采集场景。它的设计哲学"简单、快速、可扩展"贯穿始终。本文从单机搭建到集群工作机制，建立 Kafka 的完整认知框架。

## 一、Kafka 的定位与特点

Kafka 最初是 LinkedIn 用来收集海量应用日志的。业务场景决定了产品特点：

| 特点 | 说明 |
|------|------|
| **数据吞吐量极大** | 能快速收集海量日志 |
| **集群容错性高** | 允许少量节点崩溃 |
| **功能简单** | 没有死信队列、顺序消息等高级功能 |
| **允许少量数据丢失** | 海量日志中少量丢失不影响结果 |

> Kafka 的设计初衷就是**允许少量数据丢失**的。虽然社区在不断优化数据安全性，但对比 RocketMQ，这部分仍是选型要点。

**版本说明**：如 `kafka_2.13-3.8.0`，`2.13` 是 Scala 版本，`3.8.0` 是 Kafka 版本。

---

## 二、单机快速上手

### 2.1 启动

```bash
# 1. 启动 Zookeeper
nohup bin/zookeeper-server-start.sh config/zookeeper.properties &

# 2. 启动 Kafka
nohup bin/kafka-server-start.sh config/server.properties &
# Kafka 默认监听 9092 端口
```

### 2.2 收发消息

```bash
# 创建 Topic
bin/kafka-topics.sh --create --topic test --bootstrap-server localhost:9092

# 生产者
bin/kafka-console-producer.sh --broker-list localhost:9092 --topic test
> Hello Kafka

# 消费者
bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic test
# 输出: Hello Kafka
```

---

## 三、核心概念

### 3.1 消费者组（Consumer Group）

| 特性 | 说明 |
|------|------|
| 组内消费 | 同一 Group 的多个 Consumer **不会**重复消费同一条消息 |
| 跨组消费 | 不同 Group 可以各自消费同一条消息（实现**广播**效果） |
| 动态扩缩 | 增加 Consumer 自动触发 **Rebalance** |

> 消费者组的核心价值：让 Kafka 同时具备**队列**（组内排他消费）和**发布/订阅**（跨组广播消费）的特性。

### 3.2 Topic、Partition、Broker 关系

```
Topic: order-topic
  ├── Partition 0 → Broker 1 (Leader)
  │                    └── Broker 2 (Follower)
  ├── Partition 1 → Broker 2 (Leader)
  │                    └── Broker 3 (Follower)
  └── Partition 2 → Broker 3 (Leader)
                       └── Broker 1 (Follower)
```

| 组件 | 说明 |
|------|------|
| **Topic** | 消息的逻辑分类 |
| **Partition** | Topic 的物理分片，每个 Partition 是**有序、不可变**的消息序列 |
| **Broker** | Kafka 服务器节点 |
| **Leader** | 负责该 Partition 的读写 |
| **Follower** | 被动同步，不对外服务 |

**重要规则**：一个 Partition 只能被同一 Group 内的 **一个** Consumer 消费。如果 Group 内 Consumer 数量超过 Partition 数量，多出的 Consumer 处于空闲状态。

### 3.3 消息传递机制

| 策略 | 说明 |
|------|------|
| **At Most Once**（最多一次） | 发完不管，可能丢消息 |
| **At Least Once**（至少一次） | 确保送达，可能重复 |
| **Exactly Once**（精确一次） | Kafka 0.11+ 支持幂等 + 事务 |

---

## 四、Kafka 集群消息流转模型

```
Producer → Broker集群 → Consumer Group
              │
              ├── Partition 0 (Leader on Broker 1)
              │                  │
              │          Replica on Broker 2
              ├── Partition 1 (Leader on Broker 2)
              └── ...
```

**完整流程**：

1. Producer 将消息写入 Leader Partition
2. Follower 从 Leader 同步数据（ISR: In-Sync Replicas）
3. Consumer 从 Leader 拉取（Pull）消息
4. **Offset**：每条消息有唯一 offset，Consumer 通过管理 offset 实现消费进度控制

---

## 五、Kafka 为什么快？

| 机制 | 说明 |
|------|------|
| **顺序写盘** | 追加写，无随机 IO |
| **零拷贝** | sendfile() 直接从内核发送到网卡 |
| **Page Cache** | 利用 OS 页缓存，减少物理 IO |
| **批量压缩** | 多条消息打包压缩传输 |
| **分区并行** | 多个 Partition 并行读写 |

---

## 六、总结

| 要点 | 说明 |
|------|------|
| 定位 | 高吞吐日志采集，允许少量丢数据 |
| 核心概念 | Topic → Partition → offset，Consumer Group |
| 启动依赖 | 需要先启动 ZooKeeper |
| 分区消费 | 1 Partition 只能被 1 个 Consumer（同 Group）消费 |
| 高性能 | 顺序IO + 零拷贝 + 页缓存 + 分区并行 |
| 与 RocketMQ 差异 | Kafka 吞吐更高但功能更简单，RocketMQ 兼顾金融级可靠性 |
