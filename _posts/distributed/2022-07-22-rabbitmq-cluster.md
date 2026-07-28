---
layout: post
title: "RabbitMQ集群实战：多节点部署/联邦/Shovel/监控运维全指南"
date: 2022-07-22
categories: [distributed]
tags: [RabbitMQ, 集群部署, 联邦, Shovel, 监控, 运维]
comments: true

---

## 一、集群架构模式

### 普通集群

```
Node1: Queue-A (实际数据在 Node1)
Node2: Queue-A 的元数据(实际数据在 Node1, 路由到 Node1)
Node3: Queue-A 的元数据

访问任意节点都可路由到 Node1 读数据
但 Node1 宕机 → Queue-A 不可用 → 需镜像队列
```

### 镜像集群

```
Node1: Queue-A Master + 数据
Node2: Queue-A Mirror + 数据副本
Node3: Queue-A Mirror + 数据副本

Node1 宕机 → Node2 成为新 Master → 继续服务
```

---

## 二、集群搭建

```bash
# 1. 统一 Erlang Cookie（集群认证）
scp /var/lib/rabbitmq/.erlang.cookie node2:/var/lib/rabbitmq/.erlang.cookie
scp /var/lib/rabbitmq/.erlang.cookie node3:/var/lib/rabbitmq/.erlang.cookie

# 2. 各节点启动 RabbitMQ
systemctl start rabbitmq-server

# 3. 加入集群（在 node2/node3）
rabbitmqctl stop_app
rabbitmqctl reset
rabbitmqctl join_cluster rabbit@node1
rabbitmqctl start_app

# 4. 查看集群状态
rabbitmqctl cluster_status
```

### 配置镜像策略

```bash
rabbitmqctl set_policy ha-all "^" '{"ha-mode":"all","ha-sync-mode":"automatic"}'
```

---

## 三、跨集群方案

### Federation Plugin（联邦）

```
数据中心 A                   数据中心 B
RabbitMQ Cluster  →联邦→  RabbitMQ Cluster
  (Exchange)                 (Exchange)
```

- 上游：定义被谁消费
- 下游：定义从哪里拉

### Shovel Plugin

```
源端 Queue → (Shovel) → 目标端 Queue/Exchange
```

更轻量，配置更灵活。

---

## 四、监控运维

### 命令行

```bash
rabbitmqctl list_queues name messages consumers
rabbitmqctl list_exchanges
rabbitmqctl list_bindings
rabbitmqctl list_connections
```

### HTTP API

```bash
curl -u guest:guest http://localhost:15672/api/queues
```

### 关键监控项

| 指标 | 说明 |
|------|------|
| `queue_messages_ready` | 待消费消息数 |
| `queue_messages_unacknowledged` | 已投递未确认 |
| `message_rates` | 消息速率 |
| `consumer_count` | 消费者数量 |

---

## 五、内存/磁盘告警

```bash
# 内存水位控制
rabbitmqctl set_vm_memory_high_watermark 0.4  # 40% 触发告警

# 磁盘水位控制
rabbitmqctl set_disk_free_limit "4GB"  # 少于4GB触发告警
```

---

## 六、总结

```
集群 = 多节点 + .erlang.cookie 统一
镜像队列 → ha-mode:all → 高可用（3节点推荐）
跨集群 → Federation(Exchange级) / Shovel(Queue级)
监控 → HTTP API + rabbitmqctl
告警 → 内存40% + 磁盘4GB 水位
```
