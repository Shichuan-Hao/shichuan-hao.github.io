---
layout: post
title: "Zookeeper应用场景实战（二）：分布式锁与服务注册发现"
date: 2022-07-01
categories: [distributed]
tags: [Zookeeper, 分布式锁, 服务注册, Spring Cloud, Curator, 羊群效应]
comments: true
---

> 在分布式集群中，需要跨机器的进程间同步机制。ZK 以其高可靠性和一致性保证，在分布式锁和服务注册领域有广泛应用。

---

## 一、什么是分布式锁

单机开发 → `synchronized` / `Lock` 解决并发。

分布式集群 → 需要**跨JVM**的锁机制，即**分布式锁**。

### 三种主流方案对比

| 方案 | 原理 | 性能 | 可靠性 | 适用场景 |
|------|------|------|--------|----------|
| **数据库** | 唯一索引排他性 | 低 | 中 | 非首选 |
| **Redis** | SET NX + Lua 原子操作 | **高** | 中 | 高并发、性能优先 |
| **Zookeeper** | 临时有序节点 + Watch | 中 | **高** | 高可靠、一致性优先 |

> Redis 锁：常见且成熟的方案，适合高并发。ZooKeeper 锁：高可靠和强一致性场景，但频繁创建删除节点导致性能不如 Redis。

---

## 二、ZK 分布式锁设计思路

### 方案一：简单互斥锁（有羊群效应）

```
锁路径: /lock

客户端 A: create /lock (成功) → 拿到锁
客户端 B: create /lock (失败) → watch /lock
客户端 C: create /lock (失败) → watch /lock

A释放锁 → 删除 /lock → B和C同时被唤醒
→ 只有一个能拿到锁 → 另一个白醒 → 羊群效应！
```

**羊群效应（Herd Effect）**：一个锁释放后，所有等待者同时被唤醒，只有一个能拿到锁，其余全部白竞争。

### 方案二：公平锁（有序临时节点）

这是 **Curator InterProcessMutex** 的核心实现：

```
锁路径: /lock

客户端 A: create /lock/_c_0000000001 → 序号最小 → 拿到锁
客户端 B: create /lock/_c_0000000002 → watch /lock/_c_0000000001
客户端 C: create /lock/_c_0000000003 → watch /lock/_c_0000000002

A释放: 删除 /lock/_c_0000000001 → B被唤醒 → 拿到锁
B释放: 删除 /lock/_c_0000000002 → C被唤醒 → 拿到锁
```

**每个客户端只 watch 前一个节点**，避免了羊群效应。

### Curator 可重入分布式锁

```java
InterProcessMutex lock = new InterProcessMutex(client, "/lockPath");

try {
    if (lock.acquire(10, TimeUnit.SECONDS)) {
        // 执行业务逻辑
    }
} finally {
    lock.release();
}
```

**InterProcessMutex 特性**：
- 可重入（同一线程可多次获取）
- 阻塞锁
- 自动释放（session超时后临时节点自动删除，不会死锁）
- 公平锁（按创建顺序）

---

## 三、三种分布式锁方案代码对比

### 基于数据库

```sql
-- 利用唯一索引实现
INSERT INTO distributed_lock (lock_name, holder, expire_time) 
VALUES ('order_lock', 'server1', NOW() + INTERVAL 30 SECOND);
```

问题：性能低、单点故障、没有自动失效机制。

### 基于 Redis

```java
// SET NX + EX 原子操作
String result = jedis.set("lock:order", "server1", 
    SetParams.setParams().nx().ex(30));
if ("OK".equals(result)) {
    try { /* 业务逻辑 */ } 
    finally { jedis.del("lock:order"); }
}
```

### 基于 Zookeeper（Curator）

```java
InterProcessMutex lock = new InterProcessMutex(client, "/locks/order");
lock.acquire();
try {
    // 业务逻辑
} finally {
    lock.release();
}
```

---

## 四、ZK 服务注册与发现

### 设计思路

```
服务提供者启动 → 在 /services/order-service 下创建临时节点
服务消费者 → watch /services/order-service → 获取可用服务列表
提供者宕机 → 临时节点自动删除 → 消费者收到通知 → 更新列表
```

### ZK 注册中心优缺点

| 优点 | 缺点 |
|------|------|
| 高可用（多节点容错） | 性能不如 Nacos/Consul |
| 强一致性（所有节点数据一致） | 大量读写时可能遇到性能瓶颈 |
| 实时性（Watch 通知机制） | 不适合超大规模服务注册 |

### Spring Cloud Zookeeper 整合

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-zookeeper-discovery</artifactId>
</dependency>
```

```yaml
spring:
  application:
    name: order-service
  cloud:
    zookeeper:
      connect-string: 192.168.65.156:2181,192.168.65.190:2181
      discovery:
        enabled: true
```

---

## 五、总结

```
ZK 分布式锁：
  方案一（简单互斥）→ 羊群效应
  方案二（有序临时节点）→ Curator InterProcessMutex → 推荐！

ZK vs Redis 锁选型：
  高并发 + 可接受少量不一致 → Redis
  高可靠 + 强一致性 → Zookeeper

ZK 服务注册：
  Spring Cloud Zookeeper → 临时节点注册 → Watch 动态发现
```

> 有道云笔记：[Zookeeper经典应用场景实战二](https://note.youdao.com/s/F6cC7lvp)
