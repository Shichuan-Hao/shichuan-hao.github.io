---
layout: post
title: "RabbitMQ应用开发篇：消息确认/死信队列/延迟队列/优先级队列实战"
date: 2022-07-20
categories: [distributed]
tags: [RabbitMQ, 消息确认, 死信队列, 延迟队列, TTL, 应用开发]
comments: true

---

## 一、消息确认机制

### 生产者确认（Publisher Confirm）

```java
// 开启 Confirm 模式
channel.confirmSelect();

// 单条确认
channel.basicPublish("ex", "rk", null, "msg".getBytes());
if (channel.waitForConfirms()) {
    // 发送成功
}

// 批量确认
channel.basicPublish("ex1", "rk1", null, "msg1".getBytes());
channel.basicPublish("ex2", "rk2", null, "msg2".getBytes());
channel.waitForConfirms();  // 等所有都确认

// 异步确认
channel.addConfirmListener(
    (seqNo, multiple) -> System.out.println("确认: " + seqNo),
    (seqNo, multiple) -> System.out.println("未确认: " + seqNo)
);
```

### 消费者确认（Consumer Ack）

```java
// 自动确认（默认，不推荐）
channel.basicConsume("queue", true, callback, cancel -> {});

// 手动确认（推荐）
channel.basicConsume("queue", false, (tag, delivery) -> {
    try {
        processMessage(delivery);
        channel.basicAck(delivery.getEnvelope().getDeliveryTag(), false);
    } catch (Exception e) {
        // basicNack: 重回队列重试
        channel.basicNack(delivery.getEnvelope().getDeliveryTag(), false, true);
    }
}, cancel -> {});
```

---

## 二、TTL 和死信队列

### 消息 TTL

```java
// 队列级别 TTL
Map<String, Object> args = new HashMap<>();
args.put("x-message-ttl", 10000);  // 10秒
channel.queueDeclare("queue", true, false, false, args);

// 消息级别 TTL
AMQP.BasicProperties props = new AMQP.BasicProperties.Builder()
    .expiration("10000")
    .build();
channel.basicPublish("ex", "rk", props, "msg".getBytes());
```

### 死信队列（DLX）三种来源

| 来源 | 说明 |
|------|------|
| 消息过期 | TTL 到期未被消费 |
| 队列满 | 队列到达长度限制 |
| 消息被拒绝 | `basicReject`/`basicNack` 且 `requeue=false` |

```java
// 声明死信交换机和队列
channel.exchangeDeclare("dlx_exchange", BuiltinExchangeType.TOPIC);
channel.queueDeclare("dlx_queue", true, false, false, null);
channel.queueBind("dlx_queue", "dlx_exchange", "dead.#");

// 业务队列绑定死信
Map<String, Object> args = new HashMap<>();
args.put("x-dead-letter-exchange", "dlx_exchange");
args.put("x-dead-letter-routing-key", "dead.order");
channel.queueDeclare("order_queue", true, false, false, args);
```

---

## 三、延迟队列

> RabbitMQ 本身没有延迟队列功能，通过 TTL + 死信队列组合实现。

```
Producer → Normal Exchange → Queue(TTL=5s, 无Consumer)
                                │ 过期
                                ▼
                            DLX Exchange → DLX Queue → Consumer(延迟5s消费)
```

```java
// 流程
// 1. 创建 DLX Exchange + DLX Queue
// 2. 创建普通 Queue 绑定：(x-message-ttl: 5000) + (x-dead-letter-exchange: dlx)
// 3. Producer 发送到普通 Exchange → 5s 后进入 DLX → Consumer 从 DLX 消费
```

---

## 四、优先级队列

```java
Map<String, Object> args = new HashMap<>();
args.put("x-max-priority", 10);  // 0最低 10最高
channel.queueDeclare("priority_queue", true, false, false, args);

// 发送高优先级消息
AMQP.BasicProperties props = new AMQP.BasicProperties.Builder()
    .priority(9)
    .build();
channel.basicPublish("ex", "rk", props, "urgent".getBytes());
```

---

## 五、总结

```
消息确认: Publisher Confirm + Consumer Ack(手动)
死信队列: TTL过期 + 队列满 + 拒绝(不重回) → DLX
延迟队列: TTL + DLX 组合实现
优先级: x-max-priority + basicProperties.priority
```
