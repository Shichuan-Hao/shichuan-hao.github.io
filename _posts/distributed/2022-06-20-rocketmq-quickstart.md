---
title: "RocketMQ 快速实战与核心概念详解"
date: 2022-06-20
categories: distributed
tags: [RocketMQ, 消息队列, NameServer, Broker, 集群部署, Dledger, 消息模型]
mermaid: true
---

> RocketMQ 是阿里巴巴开源的消息中间件，历经双十一万亿级消息考验，是少数适用于金融场景的 MQ 产品。本文从环境搭建到集群部署，从运行架构到消息模型，带你快速理解 RocketMQ 的核心设计。

## 一、MQ 的三大作用

| 作用 | 类比 | 意义 |
|------|------|------|
| **异步** | 快递放驿站→客户自取 | 提高系统响应速度和吞吐量 |
| **解耦** | 翻译社翻译多种语言书籍 | 减少服务间影响，支持数据分发 |
| **削峰** | 三峡大坝蓄水→下游缓慢排水 | 以稳定系统资源应对突发流量 |

## 二、四大 MQ 产品横向对比

| 产品 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **Kafka** | 吞吐量极大，高性能，集群高可用 | 可能丢数据，功能单一 | 日志分析、大数据采集 |
| **RabbitMQ** | 消息可靠性高，功能全面 | Erlang 难定制，吞吐量低 | 企业内部小规模调用 |
| **Pulsar** | 基于 BookKeeper，可靠性极高 | 周边生态不足，应用少 | 大规模企业服务 |
| **RocketMQ** | 高吞吐、高可用、功能全面，Java 易定制 | 服务加载慢 | **几乎全场景，特别适合金融** |

> RocketMQ 最大的优势：出身于阿里**金融互联网**，在吞吐量与可靠性之间找到了最优平衡——比 Kafka 更可靠，比 RabbitMQ 吞吐更高。

**RocketMQ 5.0 里程碑**（2022 下半年）：
- 重构代码量超过 **60%**
- 增加大量新特性
- 4.x 已于 2024 年 3 月停止维护

---

## 三、快速搭建与实战

### 3.1 内存配置

RocketMQ 默认需要 **12GB 内存**。学习环境修改：

```bash
# runserver.sh
JAVA_OPT="${JAVA_OPT} -server -Xms1g -Xmx1g -Xmn512m"

# runbroker.sh  
JAVA_OPT="${JAVA_OPT} -server -Xms2g -Xmx2g"
```

### 3.2 启动服务

```bash
# 1. 启动 NameServer
nohup bin/mqnamesrv &
# 日志出现 "The Name Server boot success. serializeType=JSON" 即成功

# 2. 启动 Broker
nohup bin/mqbroker -n localhost:9876 -c conf/broker.conf &
```

**NameServer 的作用**：负责**路由服务**和**服务注册**。Producer 和 Consumer 从 NameServer 获取 Broker 的网络地址。

### 3.3 Java 客户端收发消息

```xml
<dependency>
    <groupId>org.apache.rocketmq</groupId>
    <artifactId>rocketmq-client</artifactId>
    <version>5.3.0</version>
</dependency>
```

**发送消息**：

```java
DefaultMQProducer producer = new DefaultMQProducer("test-producer-group");
producer.setNamesrvAddr("localhost:9876");
producer.start();

Message msg = new Message("test-topic", "tagA", "Hello RocketMQ".getBytes());
SendResult result = producer.send(msg);
System.out.println(result.getSendStatus());

producer.shutdown();
```

**消费消息**：

```java
DefaultMQPushConsumer consumer = new DefaultMQPushConsumer("test-consumer-group");
consumer.setNamesrvAddr("localhost:9876");
consumer.subscribe("test-topic", "*");

consumer.registerMessageListener((MessageListenerConcurrently) (msgs, context) -> {
    for (MessageExt msg : msgs) {
        System.out.println("收到: " + new String(msg.getBody()));
    }
    return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
});

consumer.start();
```

---

## 四、RocketMQ 运行架构

```
┌───────────────────────────────────────────────────────┐
│                    RocketMQ 集群                        │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  NameServer  │  │  NameServer  │  │  NameServer  │   │
│  │  (路由中心)   │  │  (路由中心)   │  │  (路由中心)   │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │            │
│         └────────────────┼────────────────┘            │
│                          │                              │
│           ┌──────────────┼──────────────┐              │
│           ▼              ▼              ▼              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Broker-A    │  │  Broker-B    │  │  Broker-C    │    │
│  │ (Master)    │  │ (Master)    │  │ (Master)    │    │
│  └──────┬──────┘  └─────────────┘  └─────────────┘     │
│         │                                               │
│         ▼                                               │
│  ┌─────────────┐                                        │
│  │Broker-A-S   │                                        │
│  │ (Slave)     │                                        │
│  └─────────────┘                                        │
└───────────────────────────────────────────────────────┘
```

| 组件 | 职责 |
|------|------|
| **NameServer** | 路由中心，保存 Broker 网络地址和 Topic 路由信息。无状态，可集群部署，节点间**不通信** |
| **Broker** | 消息存储和转发核心。分为 Master 和 Slave |
| **Topic** | 消息主题，同一 Topic 的消息分布在多个 Broker 上 |
| **Queue** | 消息分区，同一 Broker 上一个 Topic 可对应多个 Queue |

> NameServer 之间**不通信**，这与其他分布式系统（如 ZK）完全不同。它通过 Broker 心跳上报来维护路由信息，设计极为简洁。

---

## 五、RocketMQ 消息模型

```
Producer → Broker → Consumer
   │         │         │
   ▼         ▼         ▼
 Topic    Message    Queue
   │         │
   ▼         ▼
 Queue    CommitLog
```

**消息流转**：

1. Producer 发送消息到 Broker 的指定 Topic
2. Broker 将消息写入 **CommitLog**（顺序写盘）
3. Broker 再异步写入 **ConsumeQueue**（按 Topic-Queue 建立索引）
4. Consumer 从 ConsumeQueue 中读取消息

**为何设计 CommitLog？**——所有 Topic 的消息都写入同一个 CommitLog，保证**顺序写盘**（随机写→零）。这是 RocketMQ 解决"多 Topic 下 IO 性能压力"的核心设计。

### 消息消费两种模式

| 模式 | 说明 |
|------|------|
| **集群消费** | 同一 Group 内，每条消息只被一个 Consumer 消费 |
| **广播消费** | 每个 Consumer 都会收到每条消息 |

---

## 六、集群升级路径

```
单机 → 多主集群 → 主从集群 → Dledger 高可用集群
```

**Dledger** 是 RocketMQ 自带的 Raft 实现，替代传统的主从切换机制，保证**自动故障转移**和**数据强一致**。

---

## 七、RocketMQ 可视化管理

```bash
# 下载 rocketmq-dashboard jar 包
java -jar rocketmq-dashboard-1.0.0.jar --rocketmq.config.namesrvAddr=localhost:9876
# 浏览器访问 http://localhost:8080
```

可以直观看到：集群状态、Topic 分布、消息堆积、消费进度、生产消费 TPS 等。

---

## 八、总结

| 要点 | 说明 |
|------|------|
| 定位 | 高吞吐+高可靠+功能全面，特别适合金融场景 |
| 核心组件 | NameServer(路由) + Broker(存储) + Producer/Consumer |
| NameServer | 无状态，节点间不通信，通过 Broker 心跳上报路由 |
| 存储 | CommitLog 顺序写 + ConsumeQueue 索引，解决多 Topic IO 瓶颈 |
| 5.0 大版本 | 重构 60% 代码，新增大量特性 |
| 高可用 | 主从同步 → Dledger（Raft）自动故障转移 |
