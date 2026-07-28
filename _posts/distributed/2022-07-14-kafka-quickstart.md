---
layout: post
title: "Kafka快速上手：Topic/Partition/Broker核心机制与集群实战"
date: 2022-07-14
categories: [distributed]
tags: [Kafka, MQ, 消息队列, Topic, Partition, Consumer Group, 集群]
comments: true
---

> Kafka 最早诞生于 LinkedIn，用于收集并处理庞大的应用日志。目前是最具影响力的开源 MQ 产品。

---

## 一、Kafka 产品特点

### 适用场景决定产品特点

Kafka 的核心场景是**日志收集**：

| 特点 | 原因 |
|------|------|
| 数据吞吐量极大 | 需要快速收集海量日志 |
| 集群容错性高 | 允许少量节点崩溃 |
| 功能不需太复杂 | 关注消息传递而非消息处理 |
| 允许少量数据丢失 | 海量日志中少量的丢失不影响结果 |

---

## 二、快速搭建

```bash
# 1. 启动 Zookeeper（如果是 Kafka 3.8+ 可不用 ZK）
nohup bin/zookeeper-server-start.sh config/zookeeper.properties &

# 2. 启动 Kafka
nohup bin/kafka-server-start.sh config/server.properties &

# 验证
jps  # 看到 Kafka 和 QuorumPeerMain 进程
```

---

## 三、简单收发消息

```bash
# 创建 Topic
bin/kafka-topics.sh --create --topic test --bootstrap-server localhost:9092

# 启动生产者（发送消息）
bin/kafka-console-producer.sh --broker-list localhost:9092 --topic test

# 启动消费者（消费消息）
bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic test --from-beginning
```

---

## 四、Consumer Group（消费者组）

**核心价值**：

```
Consumer Group A: [C1] [C2]        → 组内分摊消费
Consumer Group B: [C3]             → 独立消费同一 Topic

Producer → [P0] [P1] [P2] [P3]
              │    │    │    │
              ▼    ▼    ▼    ▼
           C1读取P0+P1    C2读取P2+P3    (Group A, 组内负载均衡)
           C3读取全部4个分区              (Group B, 独立消费)
```

**Consumer Group 规则**：
- Topic 下**一个 Partition 只能被组内一个 Consumer 消费**
- 组内 Consumer 数 > Partition 数 → 多余的 Consumer 空闲
- 不同 Consumer Group 互相独立，相当于广播

---

## 五、Topic / Partition / Broker

```
Topic: "order-topic"
  ├── Partition 0 (leader → Broker 1, replica → Broker 2)
  ├── Partition 1 (leader → Broker 2, replica → Broker 1)
  └── Partition 2 (leader → Broker 3, replica → Broker 1)

Broker 集群 (3个节点)
  Broker 1: [P0-leader] [P1-replica] [P2-replica]
  Broker 2: [P0-replica] [P1-leader]
  Broker 3: [P2-leader]
```

**关键理解**：

| 概念 | 说明 |
|------|------|
| **Topic** | 逻辑概念，消息类别 |
| **Partition** | 物理存储单元，append-only 日志文件 |
| **Broker** | Kafka 服务实例 |
| **Leader** | 负责读写，每个 Partition 只有一个 |
| **Replica** | 数据备份，只从 Leader 同步 |

---

## 六、Kafka 集群消息流转

```
Producer → 指定 Topic
              │ metadata 请求 → 获取 Partition Leader
              ▼
         发送到 Leader Broker
              │
         Leader 写入 Partition（append 日志）
              │
         Replica 同步数据（ISR 机制）
              │
         Consumer pull 拉取消息
              │ 记录 offset（消费位点）
              ▼
```

**Kafka 为什么快（五大性能机制）**：

| 机制 | 说明 |
|------|------|
| 顺序写入 | 分区日志 append-only，磁盘顺序写接近内存速度 |
| Page Cache | 利用 OS 缓存，数据先写内存 |
| 零拷贝 | sendfile 直接内核传输 |
| 批量处理 | Producer 批量发、Consumer 批量拉 |
| 数据压缩 | GZIP/Snappy/LZ4 压缩 |

---

## 七、总结

```
Kafka 核心三板斧：
  Topic → 消息分类
  Partition → 水平扩展+顺序写入
  Consumer Group → 负载均衡+广播

设计哲学：
  append-only 日志 + 顺序读写 + OS PageCache
  → 追求极致吞吐量，功能简洁
```
