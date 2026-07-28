---
layout: post
title: "RocketMQ集群高级特性：事务消息/定时消息/Dledger全解析"
date: 2022-07-13
categories: [distributed]
tags: [RocketMQ, 事务消息, 定时消息, Dledger, 集群, 高可用]
comments: true

---

## 一、事务消息

### 流程

```
生产者:
  sendMessageInTransaction → MQ
    发送 Half 消息（暂不可见）
    
MQ:
  存储 Half 消息 → 返回结果给生产者
  
生产者:
  收到结果 → 执行本地事务
  → commit / rollback → 告知 MQ
  → 未知 → MQ 主动回查（check）
  
MQ:
  commit → 消息对消费者可见
  rollback → 消息删除
```

### 回查机制

```java
TransactionListener listener = new TransactionListener() {
    @Override
    public LocalTransactionState executeLocalTransaction(Message msg, Object arg) {
        // 执行本地事务
        return LocalTransactionState.UNKNOW;
    }

    @Override
    public LocalTransactionState checkLocalTransaction(MessageExt msg) {
        // MQ 回查：检查本地事务是否已提交
        return LocalTransactionState.COMMIT_MESSAGE;
    }
};

TransactionMQProducer producer = new TransactionMQProducer("group");
producer.setTransactionListener(listener);
producer.sendMessageInTransaction(msg, null);
```

**应用场景**：订单创建 + 扣库存 + 通知下游 → 事务保证一致性。

---

## 二、定时/延迟消息

### 时间轮算法

```
TimerWheel(timeUnit, slots)
  slot 0 → [任务A, 任务B]  ← 当前指针
  slot 1 → [任务C]
  slot 2 → []
  ...
  
指针每秒前进一格 → 到期任务取出执行
```

**18 个预设等级**（不可自定义）：
- 1s, 5s, 10s, 30s
- 1m, 2m, 3m, 4m, 5m, 6m, 7m, 8m, 9m, 10m, 20m, 30m
- 1h, 2h

```java
msg.setDelayTimeLevel(3);  // 第3级=10秒
```

---

## 三、Dledger 高可用

### 问题：传统主从方案的不足

Master 宕机 → 需人工切换 → 服务中断窗口可能很长

### Dledger 方案（Raft 实现）

```
3个 Dledger 节点:
  Leader  → 写入 + 同步到 Follower
  Follower → 接收同步 + 参与投票
  
Leader 宕机 → 自动选举 → 秒级选出新 Leader → 恢复服务
```

**配置**：
```conf
# dLedgerSelfId=所属节点号
# dLedgerGroup=raft组
# dLedgerPeers=节点列表
enableDLegerCommitLog=true
dLegerSelfId=n0
dLegerGroup=group1
dLegerPeers=n0-192.168.1.1:40911;n1-192.168.1.2:40911;n2-192.168.1.3:40911
```

---

## 四、总结

```
事务消息 → Half消息 + 本地事务 + 回查 → 分布式事务
定时消息 → 时间轮 + 18预设等级
Dledger → Raft 共识算法 → 自动选举高可用
```
