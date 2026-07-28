---
layout: post
title: "MQ常见问题梳理：不丢消息/不重复消费/有序性三座大山"
date: 2022-07-28
categories: [distributed]
tags: [MQ, 消息可靠性, 消息丢失, 重复消费, 顺序消息, 面试题]
comments: true
---

> 学完 RocketMQ、Kafka、RabbitMQ 三大 MQ 后，用统一的视角回顾 MQ 共有的三大核心问题。

---

## 一、MQ 如何保证消息不丢失

### 消息链路分析

```
Producer ─┬─(1)网络发送─▶ Broker ─┬─(3)存储落盘─▶ Broker 磁盘
          │                       │
          └── 可能丢              └── (4)网络投递 ─▶ Consumer
                                                     │
                                                (可能丢)
```

**三个可能丢消息的环节**：①生产者到 Broker、②Broker 存储、③Broker 到消费者。

### 1、生产者发送不丢：生产者确认机制

| MQ | 机制 |
|------|------|
| **RocketMQ** | `sendOneway`(不确认)、`send`(同步确认)、`send(callback)`(异步确认) |
| **Kafka** | `send()` 返回 Future → `.get()` 同步确认或回调异步确认 |
| **RabbitMQ** | Publisher Confirm → `addConfirmListener` 处理 ack/nack |

**统一思路**：Broker 给 Producer 返回响应，确认消息已写入。

**RocketMQ 事务消息（高级）**：
```
Half 消息（Broker 暂存）→ 执行本地事务 → 
  成功 → 提交（消费者可见）
  失败 → 回滚（消费者不可见）
未知状态 → Broker 主动回查 → 最终决定提交/回滚
```

### 2、Broker 存储不丢：刷盘机制

```
应用程序 write() → PageCache（操作系统缓存） → fsync() → 磁盘
                              ↑ 断电丢失         ↑ 持久化
```

| MQ | 配置 |
|------|------|
| **RocketMQ** | `flushDiskType = SYNC_FLUSH / ASYNC_FLUSH` |
| **Kafka** | `flush.messages` / `flush.ms` 控制刷盘间隔 |
| **RabbitMQ** | Queue 持久化 + Message `deliveryMode=2` |

> 核心：同步刷盘安全但慢，异步刷盘快但可能丢。

### 3、消费者不丢：手动确认

| MQ | 方式 |
|------|------|
| **RocketMQ** | CLUSTERING 模式下返回 CONSUME_SUCCESS / RECONSUME_LATER |
| **Kafka** | `enable.auto.commit=false` 手动提交 offset |
| **RabbitMQ** | `acknowledge-mode: manual` 手动 ack |

**原则**：消费成功才确认，失败则重试。

---

## 二、MQ 如何保证消息不重复消费

### 原因分析

```
正常：Producer → MQ → Consumer → 确认

异常之一：Consumer 消费成功 → 确认包丢失 → 超时重试
         → MQ 再次投递 → 同一消息被消费两次！
```

### 解决方案：幂等性

**核心思路**：让消费端对同一消息消费多次的结果一样。

| 方案 | 实现 |
|------|------|
| **数据库唯一约束** | 消息ID入库，唯一键防重 |
| **Redis 防重** | `setnx messageId` 判断是否已处理 |
| **状态机** | 业务状态只有特定流转方向（如已支付→不能再次支付） |

```java
// Redis 防重示例
public void consume(Message msg) {
    String msgId = msg.getMsgId();
    Boolean success = redis.setnx("msg:dedup:" + msgId, "1");
    if (!success) return;  // 已处理过
    
    // 处理业务逻辑...
    
    redis.expire("msg:dedup:" + msgId, 3600);  // 1小时过期清理
}
```

---

## 三、MQ 如何保证消息有序性

### 问题：Partition/Queue 的有序性

```
Topic 下有 4 个队列，消息分散：
  P0: [m1, m5, m9]
  P1: [m2, m6, m10]
  P2: [m3, m7, m11]
  P3: [m4, m8, m12]

消费者可能乱序消费 → 需要保证局部有序
```

### 解决方案

| MQ | 方案 |
|------|------|
| **RocketMQ** | 同一业务ID消息 → 同一 MessageQueue（`MessageQueueSelector`） |
| **Kafka** | 同一 Key 的消息 → 同一 Partition |
| **RabbitMQ** | 单一 Queue + 单一 Consumer 保证严格有序 |

```java
// RocketMQ 有序发送
producer.send(msg, new MessageQueueSelector() {
    @Override
    public MessageQueue select(List<MessageQueue> mqs, Message msg, Object arg) {
        Long orderId = (Long) arg;
        int index = (int) (orderId % mqs.size());
        return mqs.get(index);
    }
}, orderId);

// Kafka 有序发送
ProducerRecord<String, String> record = new ProducerRecord<>(
    "topic", orderId.toString(), message);  // orderId 作为 key → 同一 Partition
```

---

## 四、三座大山总结

```
不丢消息 = 生产者确认 + Broker 持久化 + 消费者手动确认

不重复消费 = 幂等性设计（数据库唯一键 / Redis去重 / 状态机）

消息有序 = 同一业务ID → 同一队列 → 单一消费者
```
