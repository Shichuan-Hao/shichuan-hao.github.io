---
layout: post
title: "Zookeeper ZAB协议源码剖析：原子广播与崩溃恢复全解析"
date: 2022-07-03
categories: [distributed]
tags: [Zookeeper, ZAB协议, 源码分析, 原子广播, 崩溃恢复, Paxos, 分布式一致性]
comments: true
---

> ZAB 协议全称 Zookeeper Atomic Broadcast（Zookeeper原子广播协议），是 Paxos 算法的一种简化实现，专门为 ZK 设计。

---

## 一、ZAB 协议概述

整个 Zookeeper 是一个多节点分布式一致性算法的实现，底层采用 **ZAB 协议**。

ZAB 协议定义：为分布式协调服务 Zookeeper 专门设计，支持 **崩溃恢复** 和 **原子广播** 的协议。

### ZK 主备模式架构

```
Client ──► Leader（写请求）
              │
              │ 复制数据
              ▼
         Follower 1, Follower 2, Follower 3
              │
         ┌────┴────┐
         过半 ACK →
              │
         Leader 提交 → 同步到所有 Follower
```

**复制过程**类似两阶段提交（2PC），但只需**过半 Follower（含 Leader 自己）**返回 ACK 即可提交，大大减小同步阻塞，提高可用性。

---

## 二、ZAB 协议两种模式

```
┌───────────────────────────────────────┐
│              ZAB 协议                  │
│                                       │
│  ┌──────────────┐  Leader挂掉  ┌───────┐  │
│  │  消息广播    │ ◄──────────► │ 崩溃  │  │
│  │   (normal)   │  新Leader    │ 恢复  │  │
│  └──────────────┘   ──────────►└───────┘  │
│                                       │
└───────────────────────────────────────┘
```

简而言之：**Leader 正常 → 消息广播模式；Leader 不可用 → 崩溃恢复模式**。

---

## 三、消息广播（原子广播）

### 流程

```
1. 客户端发送写请求 → Leader
2. Leader 将请求封装为事务 Proposal，分配全局递增唯一 ID（ZXID）
3. Leader 将 Proposal 广播给所有 Follower
4. Follower 收到后返回 ACK
5. Leader 收到过半 ACK → 发送 Commit 消息
6. Follower 收到 Commit → 应用到内存数据
```

### ZXID 设计

```
ZXID（64位）：
  ┌──────── 高32位 ────────┐  ┌──────── 低32位 ────────┐
  │        epoch           │  │       counter           │
  │   Leader 选举周期编号   │  │   事务递增计数器         │
  └────────────────────────┘  └────────────────────────┘
```

- **高 32 位（epoch）**：代表了每代 Leader 的唯一性。新 Leader 当选后 epoch +1
- **低 32 位（counter）**：每代 Leader 中事务的唯一性，从 0 开始递增

**好处**：
- 保证事务全局顺序
- Follower 通过高 32 位识别不同代 Leader
- 简化数据恢复流程

### 关键细节

1. **Leader 与 Follower 间有消息队列**，解耦同步阻塞
2. **只有 Leader 接受写请求**，Follower 收到写请求也会转发到 Leader
3. **ZAB 规定**：一个事务在一台机器被 commit 成功 → 必须在所有机器都被处理成功（哪怕机器崩溃）

---

## 四、崩溃恢复

### 两个核心问题

**假设 1**：Leader 复制 Proposal 给所有 Follower 后，**还没来得及收到 ACK 就崩溃**，怎么办？

**假设 2**：Leader 收到 ACK 并自己提交后，**发送了部分 Commit 后就崩溃**，怎么办？

### ZAB 两条核心原则

1. **丢弃**那些只在 Leader 提出/复制、但**没有提交**的事务
2. **确保**那些已经在 Leader **提交**的事务最终被所有服务器提交

### 选举算法设计

**核心目标**：新 Leader 拥有集群中所有机器中 **ZXID 最大**的事务。

> 这样做的好处：保证新 Leader 一定具有所有已提交的提案，省去检查事务提交/丢弃的步骤。

### 数据同步

```
崩溃恢复后 → 正式工作前：
  Leader 确认事务是否已被过半 Follower 提交
     ↓
  Follower 提交的 ZXID 对比 Leader 的 ZXID
     ↓
  落后 → 同步 Leader 数据
  超前 → 回滚未提交事务（截断到 Leader 的 ZXID）
     ↓
  同步完成 → Follower 加入可用服务器列表 → 进入消息广播模式
```

---

## 五、ZAB vs Paxos vs Raft

| | ZAB | Paxos | Raft |
|------|-----|-------|------|
| 提出者 | Yahoo! | Lamport | Stanford |
| 角色 | Leader/Follower | Proposer/Acceptor/Learner | Leader/Follower/Candidate |
| 实现复杂度 | 中等 | 高 | 低 |
| 使用项目 | Zookeeper | Chubby | etcd, Consul |
| 核心特点 | Paxos 简化版 | 理论完备 | 易于理解 |

---

## 六、总结

```
ZAB 协议核心：

  消息广播（Leader 正常）：
    Client → Leader → Proposal（ZXID）→ 广播
    → 过半 ACK → Commit → 数据落盘

  崩溃恢复（Leader 挂）：
    选举 ZXID 最大的为新 Leader
    → 数据对齐（回滚或同步）
    → 重新进入消息广播

  ZXID = epoch(32bit) + counter(32bit)
    保证：全局有序 + 跨 Leader 可追踪 + 简化恢复
```

> 有道云笔记：[ZAB协议源码剖析](https://note.youdao.com/noteshare?id=0284e85bc556d16fefc05e7a0b30da93)
