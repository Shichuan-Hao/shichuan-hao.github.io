---
layout: post
title: "Kafka功能扩展：幂等/事务/流处理/跨集群同步全景"
date: 2022-07-18
categories: [distributed]
tags: [Kafka, 幂等性, 事务, Kafka Streams, MirrorMaker, 跨集群]
comments: true

---

## 一、生产者幂等

```java
props.put("enable.idempotence", "true");
```

**原理**：
```
Producer → Broker: 每条消息带 ProducerID + Sequence Number
Broker: 记录每个 TopicPartition 最近5条消息的序列号
→ 重复的 Sequence Number → 拒绝写入 → 保证幂等
```

**局限**：单分区单会话内幂等。重启 → 新 ProducerID → 无法跨会话去重。

---

## 二、事务

### Kafka 事务解决什么问题？

幂等只能保证单分区内不重复。事务可以保证**跨分区原子写入**。

```java
// 开启事务
props.put("transactional.id", "my-tx-id");
producer.initTransactions();

// 写事务
producer.beginTransaction();
producer.send(msg1);  // → topicA-partition0
producer.send(msg2);  // → topicA-partition1
producer.commitTransaction();  // 原子提交

// 消费-处理-生产（Exactly-Once）
consumer.subscribe(Collections.singletonList("source-topic"));
while (true) {
    ConsumerRecords<...> records = consumer.poll(...);
    producer.beginTransaction();
    for (ConsumerRecord<...> record : records) {
        producer.send(process(record));  // 处理后发送
        // 提交消费位移到事务中
        producer.sendOffsetsToTransaction(offsets, consumer.groupMetadata());
    }
    producer.commitTransaction();
}
```

---

## 三、Kafka Connect

**无需编码的数据管道**：
```
Source Connector: DB → Kafka Topic
Sink Connector:   Kafka Topic → DB/ES/S3
```

常用 Connector：JDBC、Debezium(CDC)、Elasticsearch、S3

---

## 四、Kafka Streams

**流处理**：在 Kafka 内部实时聚合/过滤/转换数据，无需外部集群。

```java
StreamsBuilder builder = new StreamsBuilder();
KStream<String, String> stream = builder.stream("input-topic");

stream.filter((k, v) -> v != null)
    .mapValues(v -> v.toUpperCase())
    .groupByKey()
    .count()
    .toStream()
    .to("output-topic");
```

---

## 五、MirrorMaker 2.0（跨集群同步）

```
数据中心 A             数据中心 B
Kafka Cluster  → MM2 → Kafka Cluster
               (同步)
```

用于：灾备、数据迁移、多区域部署

---

## 六、总结

```
幂等 → enable.idempotence → 单分区不重复
事务 → transactional.id → 跨分区原子写入+ Exactly-Once
Connect → CDC/Mirror → 数据管道
Streams → 流处理 → Kafka 内实时计算
MM2 → 跨集群 → 灾备/迁移
```
