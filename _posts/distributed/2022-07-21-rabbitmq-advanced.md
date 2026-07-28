---
layout: post
title: "RabbitMQ高级功能篇：消息补偿/幂等/限流/镜像队列/仲裁队列全解析"
date: 2022-07-21
categories: [distributed]
tags: [RabbitMQ, 消息补偿, 限流, 镜像队列, Quorum队列, 高级功能]
comments: true

---

## 一、消息补偿与重试

```java
// 消费端限流（每次只取1条，确认后再取下一条）
channel.basicQos(1);

// 消费重试逻辑
channel.basicConsume("queue", false, (tag, delivery) -> {
    try {
        processMessage(delivery);
        channel.basicAck(tag, false);
    } catch (Exception e) {
        // 获取重试次数
        int retryCount = delivery.getProperties().getHeaders()
            .getOrDefault("retry-count", 0);
        if (retryCount < 3) {
            // 重试：重新入队（带重试计数）
            Map<String, Object> headers = delivery.getProperties().getHeaders();
            headers.put("retry-count", retryCount + 1);
            // 重新发送到延迟队列
            channel.basicPublish("delay_ex", "delay", 
                new AMQP.BasicProperties.Builder().headers(headers).build(),
                delivery.getBody());
            channel.basicAck(tag, false);
        } else {
            // 超过3次 → 进入死信
            channel.basicNack(tag, false, false);
        }
    }
});
```

---

## 二、消费端限流

```java
// prefetchCount: 一次最多取多少条未确认消息
channel.basicQos(100);       // 单消费者
channel.basicQos(0, 100, true);  // 全局 channel 级别
```

---

## 三、镜像队列（Mirror Queue）

### 传统高可用方案

```
普通队列只存在于一个节点。节点宕机 → 队列不可用。

镜像队列 → 数据同步到多个节点：
  Master (node1) + Mirror (node2) + Mirror (node3)
  Master 故障 → 最老的 Mirror 自动升级为 Master
```

**声明**：
```bash
rabbitmqctl set_policy ha-all "^" '{"ha-mode":"all"}'
```

**ha-mode** 三种模式：
- `all`：全部节点镜像
- `exactly`：指定数量节点
- `nodes`：指定具体节点

### 镜像队列的局限

- 性能低（需要同步到多个节点）
- 网络分区风险

---

## 四、Quorum 队列（Raft）

> RabbitMQ 3.8+ 引入的新一代高可用队列，基于 Raft 协议。

```java
Map<String, Object> args = new HashMap<>();
args.put("x-queue-type", "quorum");
channel.queueDeclare("quorum_queue", true, false, false, args);
```

### 镜像队列 vs Quorum 队列

| | 镜像队列 | Quorum 队列 |
|------|----------|------------|
| 一致性 | 最终一致 | **强一致（Raft）** |
| 性能 | 较低 | 较高 |
| 故障恢复 | 存在数据丢失风险 | 不丢数据 |
| RabbitMQ版本 | 早期版本 | **3.8+ 推荐** |

---

## 五、流式插件（Stream）

> RabbitMQ 3.9+ 引入，类似 Kafka 的日志流模型。

```java
// 创建 Stream
Map<String, Object> args = new HashMap<>();
args.put("x-queue-type", "stream");
args.put("x-max-length-bytes", 20_000_000_000L);  // 20GB
channel.queueDeclare("my_stream", true, false, false, args);

// 从指定 offset 消费
channel.basicQos(100);
channel.basicConsume("my_stream", false, 
    Map.of("x-stream-offset", 0),  // 从头开始
    callback, cancel -> {});
```

---

## 六、总结

```
补偿重试：basicNack + 计数 + 次数超限进死信
消费限流：basicQos(prefetchCount)
高可用演进：镜像队列 → Quorum队列(Raft, 推荐)
新特性：Stream队列(日志流模型)
```
