---
layout: post
title: "Kafka集群工作机制详解：Controller选举/ISR/副本同步/Leader切换"
date: 2022-07-16
categories: [distributed]
tags: [Kafka, 集群, Controller, ISR, 副本同步, Leader选举, Zookeeper]
comments: true
---

## 一、Kafka 集群角色

| 角色 | 职责 |
|------|------|
| **Broker** | 消息存储和转发 |
| **Controller** | 集群管理（Partition Leader 选举） |
| **Zookeeper** | Broker 注册、Controller 选举、元数据存储 |

### Controller 选举

```
Kafka 依赖 ZK 实现 Controller 选举：
  Broker 启动 → 尝试在 ZK 创建 /controller 临时节点
  → 创建成功 → 自己是 Controller
  → 已存在 → 成为普通 Broker，watch /controller
  → Controller 宕机 → 临时节点消失 → 其他 Broker 抢创建 → 新 Controller
```

### Controller 职责

- Broker 上下线 → 更新集群元数据
- Topic 创建/删除
- Partition Leader 选举
- 分区副本分配

---

## 二、Partition 副本机制

```
Topic: "order", 3 Partitions, 副本因子=3

  P0: Leader(Broker1)  Follower(Broker2)  Follower(Broker3)
  P1: Leader(Broker2)  Follower(Broker1)  Follower(Broker3)  
  P2: Leader(Broker3)  Follower(Broker1)  Follower(Broker2)
```

### ISR（In-Sync Replicas）

**ISR = Leader + 保持同步的 Follower 集合**

```
判断标准：
  Follower 落后 Leader 时间 ≤ replica.lag.time.max.ms(10s)
  → 在 ISR 中
  → 超过 10s 未同步 → 踢出 ISR
  → 同步恢复 → 重新加入 ISR
```

**ISR 的作用**：
- `acks=all` 时，消息必须被所有 ISR 确认才返回成功
- Leader 宕机时，优先从 ISR 中选新 Leader

---

## 三、Leader 选举

### 优先副本选举

- 每个 Partition 有一个 `preferredReplica`
- 集群初始分配时第 1 个 Replica 就是 preferredReplica
- 自动 Leader 再平衡：周期性检查 → Leader 不在 preferred → 迁移

### Unclean Leader 选举

```conf
unclean.leader.election.enable = false  (默认)
# true: ISR 全挂了，允许 OSR 中选（可能丢数据）
# false: ISR 全挂了，Partition 不可用（等 ISR 恢复）
```

---

## 四、Leader 切换流程

```
Controller 监控 → Broker 宕机 → ZK 临时节点消失
  → Controller 感知 → 遍历所有受影响 Partition
  → 从 ISR 选择新 Leader（第一个活的）
  → 更新 Partition 状态 → 通知其他 Broker
  → 通知 Producer/Consumer 新 Leader 地址
```

---

## 五、总结

```
Controller → ZK 临时节点选举 → 集群管理核心

Partition 副本：
  Leader(读写) + Follower(同步)
  ISR = 保持同步的 Follower 集合

Leader 选举：
  ISR 中选 → 安全
  Unclean 选举 → 可能丢数据（默认关闭）
```
