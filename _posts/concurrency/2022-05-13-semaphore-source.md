---
title: Semaphore源码分析
categories: [Java, 并发编程]
tags: [JUC, Semaphore, AQS, 共享锁, 源码分析]
author: hsc
date: 2022-05-13 00:00:00 +0800
description: 深入剖析Semaphore源码，基于AQS共享模式实现信号量，涵盖acquire/release逻辑、公平与非公平实现、限流应用场景。
source: 有道云笔记
---

# Semaphore源码分析

---

## 一、基本概念

Semaphore（信号量）控制同时访问特定资源的线程数量。通过对**许可证（permits）**的获取和释放来协调各线程。

### 1.1 类结构

```
Semaphore
  └── Sync extends AbstractQueuedSynchronizer (AQS)
       ├── NonfairSync (非公平，默认)
       └── FairSync (公平)
```

### 1.2 构造函数

```java
// permits：许可证总数
public Semaphore(int permits) {
    sync = new NonfairSync(permits);  // 默认非公平
}

// fair=true：公平模式
public Semaphore(int permits, boolean fair) {
    sync = fair ? new FairSync(permits) : new NonfairSync(permits);
}
```

构造函数最终调用 `AQS.setState(permits)` 设置许可证总数。

---

## 二、核心方法

### 2.1 acquire() — 获取许可证

```java
// Semaphore
public void acquire() throws InterruptedException {
    sync.acquireSharedInterruptibly(1);  // 共享模式获取
}

// AQS
public final void acquireSharedInterruptibly(int arg) throws InterruptedException {
    if (Thread.interrupted()) throw new InterruptedException();
    if (tryAcquireShared(arg) < 0)     // 返回负数 → 需要入队
        doAcquireSharedInterruptibly(arg);  // 入队、阻塞、等待唤醒
}
```

#### tryAcquireShared — 非公平

```java
final int nonfairTryAcquireShared(int acquires) {
    for (;;) {
        int available = getState();  // 当前可用许可证
        int remaining = available - acquires;
        // CAS 减许可证，减到 >= 0 才算成功
        if (remaining < 0 || compareAndSetState(available, remaining))
            return remaining;
    }
}
```

#### tryAcquireShared — 公平

```java
protected int tryAcquireShared(int acquires) {
    for (;;) {
        // 关键区别：先检查 AQS 队列是否有等待者
        if (hasQueuedPredecessors())
            return -1;  // 前面有人排队 → 不抢
        int available = getState();
        int remaining = available - acquires;
        if (remaining < 0 || compareAndSetState(available, remaining))
            return remaining;
    }
}
```

#### doAcquireSharedInterruptibly — 入队阻塞

```java
private void doAcquireSharedInterruptibly(int arg) {
    final Node node = addWaiter(Node.SHARED);  // 共享模式入队
    boolean failed = true;
    try {
        for (;;) {
            final Node p = node.predecessor();
            if (p == head) {
                int r = tryAcquireShared(arg);  // 前驱是head，再尝试获取
                if (r >= 0) {
                    setHeadAndPropagate(node, r);  // 获取成功，设置head并传播
                    p.next = null;
                    failed = false;
                    return;
                }
            }
            if (shouldParkAfterFailedAcquire(p, node) &&
                parkAndCheckInterrupt())
                throw new InterruptedException();
        }
    } finally {
        if (failed) cancelAcquire(node);
    }
}
```

### 2.2 release() — 释放许可证

```java
// Semaphore
public void release() {
    sync.releaseShared(1);
}

// AQS
public final boolean releaseShared(int arg) {
    if (tryReleaseShared(arg)) {      // CAS +1
        doReleaseShared();            // 唤醒后继节点
        return true;
    }
    return false;
}

// Sync 中 tryReleaseShared
protected final boolean tryReleaseShared(int releases) {
    for (;;) {
        int current = getState();
        int next = current + releases;
        if (next < current) throw new Error("Maximum permit count exceeded");
        if (compareAndSetState(current, next))
            return true;  // CAS 成功返回 true，由 AQS 负责唤醒后继
    }
}
```

---

## 三、核心流程总结

```
acquire() 流程：
  1. tryAcquireShared(1) → 返回值 >= 0? 直接成功
  2. 小于 0 → doAcquireSharedInterruptibly
     a. addWaiter(SHARED) 入同步队列
     b. 自旋：前驱是 head? → tryAcquireShared
     c. 成功 → setHeadAndPropagate (设置head并传播)
     d. 失败 → park 阻塞等待

release() 流程：
  1. tryReleaseShared(1) → CAS state + 1
  2. doReleaseShared → unparkSuccessor 唤醒后继
  3. 被唤醒的线程重新自旋获取
```

---

## 四、公平 vs 非公平

| | 非公平 Semaphore | 公平 Semaphore |
|------|------|------|
| `tryAcquireShared` | 直接 CAS 减 state | 先检查 `hasQueuedPredecessors()` |
| 新线程 | 可以插队 | 必须排队 |
| 性能 | 较高 | 较低 |
| 默认 | ✅ | |

---

## 五、应用场景

1. **线程池限制并发数** — 连接池、HTTP 并发限制
2. **接口限流** — `tryAcquire` 失败直接拒绝
3. **停车场模型** — 有空位才能进入

```java
// 限流示例
class RateLimiter {
    Semaphore semaphore = new Semaphore(100);
    
    boolean tryAquire() {
        return semaphore.tryAcquire();
    }
    void release() { semaphore.release(); }
}
```

---

## 六、总结

| 要点 | 说明 |
|------|------|
| **模式** | AQS 共享模式 |
| **state 含义** | 可用许可证数 |
| **acquire** | `state--`，不够则入 AQS 队列阻塞 |
| **release** | `state++`，CAS 成功后唤醒后继 |
| **公平/非公平** | 区别在 `tryAcquireShared` 是否检查队列 |
