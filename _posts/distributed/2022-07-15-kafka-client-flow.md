---
layout: post
title: "Kafka客户端消息流转：Producer/Consumer参数调优与Coordinator机制"
date: 2022-07-15
categories: [distributed]
tags: [Kafka, Producer, Consumer, 参数优化, Group Coordinator, 消息分区]
comments: true
---

## 一、Producer 核心参数

```java
Properties props = new Properties();
props.put("bootstrap.servers", "localhost:9092");
props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
props.put("acks", "all");                    // 副本确认机制
props.put("batch.size", 16384);              // 批量大小
props.put("linger.ms", 10);                  // 延迟发送（攒批）
props.put("buffer.memory", 33554432);        // 发送缓冲区
props.put("retries", 3);                     // 重试次数
props.put("compression.type", "snappy");     // 压缩
```

### acks 三种模式

| 值 | 说明 | 可靠性 | 性能 |
|------|------|--------|------|
| `0` | 不等确认 | 最低 | 最高 |
| `1` | Leader 确认即可 | 中 | 中 |
| `all`/-1 | 所有 ISR 确认 | **最高** | 最低 |

### 消息分区策略

```java
// 默认：key → hash % partition数
producer.send(new ProducerRecord<>("topic", "key123", "message"));

// 自定义分区器
props.put("partitioner.class", "com.my.MyPartitioner");
```

---

## 二、Consumer 核心参数

```java
Properties props = new Properties();
props.put("bootstrap.servers", "localhost:9092");
props.put("group.id", "my-group");            // 消费者组
props.put("enable.auto.commit", "false");     // 关闭自动提交
props.put("auto.offset.reset", "earliest");   // 从头消费
props.put("max.poll.records", 500);           // 单次拉取最大条数
```

### offset 管理

```java
// 手动同步提交
consumer.commitSync();

// 手动异步提交
consumer.commitAsync((offsets, exception) -> {
    if (exception == null) { /* 成功 */ }
});

// 处理完再提交（推荐）
consumer.poll(Duration.ofMillis(1000)).forEach(record -> {
    processRecord(record);
    consumer.commitSync();
});
```

### Rebalance 机制

消费者组变动（加入/离开）→ 触发 Rebalance → 重新分配 Partition

```java
consumer.subscribe(Collections.singletonList("topic"), 
    new ConsumerRebalanceListener() {
        @Override
        public void onPartitionsRevoked(Collection<TopicPartition> partitions) {
            // Rebalance 前：提交当前offset
            consumer.commitSync();
        }
        @Override
        public void onPartitionsAssigned(Collection<TopicPartition> partitions) {
            // Rebalance 后：定位offset
        }
    });
```

---

## 三、Group Coordinator 协调机制

```
Consumer 加入 Group → Coordinator (某个Broker) 
  → 选举 Group Leader Consumer
  → Leader 制定分配方案
  → 方案发给 Coordinator
  → Coordinator 分发给所有 Consumer
```

**重要机制**：

| 机制 | 说明 |
|------|------|
| `session.timeout.ms` | Consumer 心跳超时 → 踢出组（默认45s） |
| `max.poll.interval.ms` | 两次 poll 最大间隔 → 超时踢出组 |
| `heartbeat.interval.ms` | 心跳间隔（session.timeout的1/3） |

---

## 四、总结

```
Producer 优化：
   acks=all + 批量 + 压缩 + linger.ms → 安全+高效

Consumer 核心：
   手动提交offset + 处理后再提交 + 防止Rebalance误踢

Rebalance：
   组内Consumer变化 → Coordinator协调重新分配
   onPartitionsRevoked → 提交offset → onPartitionsAssigned → 恢复消费
```
