---
layout: post
title: "RocketMQ快速实战：从搭建到消息模型全景解析"
date: 2022-07-10
categories: [distributed]
tags: [RocketMQ, MQ, 消息队列, 消息模型, 集群部署, Dledger]
comments: true
---

> RocketMQ 是阿里巴巴开源的消息中间件，历经双十一高并发场景考验，能处理亿万级别消息。2016年开源后捐赠给 Apache。

---

## 一、MQ 简介

**MQ = Message + Queue**：
- **Message**：跨进程传递的数据（进程可在同机器或不同机器）
- **Queue**：具有 FIFO 特性的缓存结构

**MQ 三大作用**：

| 作用 | 说明 | 类比 |
|------|------|------|
| **异步** | 发送方不等待，继续自己的任务 | 快递放驿站，不等客户亲自取 |
| **解耦** | 服务间只跟 MQ 交互，互相不感知 | 翻译社帮英文输出多语言版本 |
| **削峰** | 以稳定的系统资源应对突发流量 | 三峡大坝蓄洪然后慢慢放水 |

---

## 二、四大 MQ 横向对比

| 产品 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **Kafka** | 吞吐量大、性能好、生态完整 | 可能丢数据、功能单一 | 日志分析、大数据采集 |
| **RabbitMQ** | 可靠性高、功能全面 | 吞吐低、Erlang 小众 | 企业内小规模服务调用 |
| **Pulsar** | 基于 BookKeeper，可靠性极高 | 生态差距、使用公司少 | 企业内部大规模调用 |
| **RocketMQ** | 高吞吐/高性能/高可用、功能全面、Java 开发 | 服务加载慢 | **几乎全场景，特别金融** |

> RocketMQ 在阿里内部每天处理超 5 万亿次请求，支撑超 3000 个核心应用。

---

## 三、RocketMQ 快速搭建

```bash
# 下载运行版本
wget https://dist.apache.org/repos/dist/release/rocketmq/5.3.0/rocketmq-all-5.3.0-bin-release.zip

# 解压后启动 NameServer
nohup sh bin/mqnamesrv &

# 启动 Broker
nohup sh bin/mqbroker -n localhost:9876 &

# 验证
jps   # 看到 NamesrvStartup + BrokerStartup
```

---

## 四、快速收发消息

```bash
# 创建 Topic
sh bin/mqadmin updateTopic -n localhost:9876 -t TestTopic -c DefaultCluster

# 启动消费者
sh bin/tools.sh org.apache.rocketmq.example.quickstart.Consumer

# 启动生产者
sh bin/tools.sh org.apache.rocketmq.example.quickstart.Producer
```

---

## 五、分布式集群部署

```
集群架构：

  NameServer (无状态，独立部署)
  ├── Broker Master (192.168.1.1)
  │   └── Broker Slave (192.168.1.2)
  ├── Broker Master (192.168.1.3)
  │   └── Broker Slave (192.168.1.4)
  └── ...

  Client → NameServer (获取路由) → Broker (收发消息)
```

**Dledger 高可用集群**：

传统方案中，Master 挂了需要人工或 NameServer 切换。Dledger 使用 Raft 协议实现自动选举，秒级切换。

---

## 六、RocketMQ 运行架构

```
Producer (消息发送者)
    │
    ▼
NameServer (路由注册中心)
    │ 获取 Broker 信息
    ▼
Broker (消息存储和转发)
    │
    ▼
Consumer (消息消费者)
```

**NameServer 职责**：
- Broker 注册
- 路由信息管理（告知 Producer/Consumer 应该连哪个 Broker）
- **无状态**，节点间不通信

**Broker 职责**：
- 消息存储
- 消息投递
- 与 NameServer 保持心跳（30秒注册一次）

---

## 七、RocketMQ 消息模型

```
Topic = 消息的逻辑分类
  ├── MessageQueue 0 (队列0)
  ├── MessageQueue 1 (队列1)
  ├── MessageQueue 2 (队列2)
  └── MessageQueue 3 (队列3)

Producer → 消息 → Topic → MessageQueue → Consumer

Consumer Group：
  - 组内消费者分摊消费所有 MessageQueue
  - 组间消费互不影响（广播模式的实现基础）
```

**关键概念**：

| 概念 | 说明 |
|------|------|
| **Topic** | 消息主题，逻辑分类 |
| **MessageQueue** | 消息队列，物理存储 |
| **Tag** | 消息标签，二次分类过滤 |
| **Consumer Group** | 消费组，组内负载均衡 |
| **Offset** | 消费位点，记录消费到哪里 |

### 为什么不用直接给 Consumer 发消息？

RocketMQ 为什么设计了 Topic → MessageQueue 两层结构？**原因**：Kafka 用 Topic 来区分一个大的业务模块但 Partition 多了影响 IO → RocketMQ 用 Topic+Tag 方式解决，引出了 CommitLog 的设计。

---

## 八、总结

```
RocketMQ 核心架构：
  NameServer(路由) → Broker(存储) → Consumer(消费)

消息模型：
  Topic → MessageQueue → Consumer Group
  Tag 做二级分类过滤

集群方案：
  多 Master 多 Slave → 高性能 + 高可用
  Dledger(Raft) → 自动选举、秒级切换
```
