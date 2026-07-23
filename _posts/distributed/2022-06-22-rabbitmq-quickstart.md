---
title: "RabbitMQ 快速上手：AMQP 协议、死信队列与 Quorum 高可用"
date: 2022-06-22
categories: distributed
tags: [RabbitMQ, AMQP, 死信队列, 延迟队列, Quorum队列, 消息可靠性]
mermaid: true
---

> RabbitMQ 是 AMQP 协议的标杆实现。相比 Kafka 的大吞吐，RabbitMQ 更专注于消息可靠性和丰富的消息路由能力。本文从 AMQP 核心模型到死信/延迟队列再到 Quorum 高可用，覆盖 RabbitMQ 的完整知识体系。

## 一、AMQP 协议与核心架构

RabbitMQ 基于 **AMQP（Advanced Message Queuing Protocol）**，核心架构：

```
Producer ──→ Exchange ──→ Queue ──→ Consumer
                │
            Binding Key
```

| 组件 | 说明 |
|------|------|
| **Producer** | 消息生产者 |
| **Exchange** | 交换机，接收消息并根据路由规则转发 |
| **Queue** | 消息缓冲队列 |
| **Binding** | 绑定关系，Exchange 和 Queue 之间的路由规则 |
| **Consumer** | 消息消费者 |

### Exchange 四种类型

| 类型 | 路由规则 |
|------|---------|
| **Direct** | 按 Routing Key **精确匹配** |
| **Fanout** | **广播**到所有绑定的 Queue |
| **Topic** | 按 Routing Key **模式匹配**（`*` 单词, `#` 多词） |
| **Headers** | 按消息 Header 属性匹配 |

---

## 二、消息可靠性保障

### 2.1 三种确认机制

| 机制 | 说明 |
|------|------|
| **Publisher Confirm** | 生产者确认：消息是否到达 Broker |
| **Consumer Ack** | 消费者确认：消息是否成功处理 |
| **Persistence** | 消息持久化：Broker 重启后不丢失 |

### 2.2 持久化配置

```java
// 声明持久化队列
channel.queueDeclare("queue", true, false, false, null);

// 发送持久化消息
channel.basicPublish("exchange", "routingKey",
    MessageProperties.PERSISTENT_TEXT_PLAIN, body);
```

---

## 三、死信队列（DLX）与延迟队列

### 3.1 死信的三种来源

1. 消息被 **拒绝（Reject/Nack）**且不重新入队
2. 消息 **TTL 过期**
3. 队列达到最大长度，**溢出**

### 3.2 死信队列架构

```
业务队列（设置 TTL / 长度限制）
    │ 消息"死亡"
    ▼
死信交换机（DLX）
    │
    ▼
死信队列 ──→ 死信消费者（告警、日志、补偿）
```

### 3.3 延迟队列实现

利用 TTL + DLX 的组合实现延迟投递：

```
延迟队列（设置 TTL，无消费者）
    │ TTL 过期
    ▼
死信交换机
    │
    ▼
实际消费队列 ──→ 消费者
```

---

## 四、Quorum 队列（高可用架构）

| 类型 | 特点 |
|------|------|
| Classic 镜像队列 | 主节点+镜像节点，数据全量复制，每个节点都有全量数据 |
| **Quorum 队列**（3.8+ 推荐） | 基于 Raft 协议，过半写入即确认，性能更好 |

**Quorum 队列优势**：
- 基于 **Raft 协议**保证数据一致性
- 自动选举 Leader
- 数据安全性更高
- 性能比 Mirror 队列更好

---

## 五、总结

| 维度 | 要点 |
|------|------|
| 核心协议 | AMQP：Exchange → Binding → Queue |
| Exchange | Direct(精确)/Fanout(广播)/Topic(模式)/Headers |
| 可靠性 | Publisher Confirm + Consumer Ack + 持久化 |
| 死信队列 | TTL过期/拒绝/溢出 → DLX → 死信消费者 |
| 延迟队列 | TTL队列(无消费者) + DLX + 实际队列 |
| 高可用 | Classic Mirror → Quorum队列(Raft) |
| 选型对比 | 可靠性最高，吞吐量不如 Kafka/RocketMQ |
