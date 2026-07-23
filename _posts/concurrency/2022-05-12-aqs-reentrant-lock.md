---
title: 深入理解AQS之独占锁ReentrantLock源码分析
categories: [Java, 并发编程]
tags: [AQS, AbstractQueuedSynchronizer, ReentrantLock, 独占锁, CLH队列, 公平锁, 非公平锁, Condition]
author: hsc
date: 2022-05-12 00:00:00 +0800
description: 深入剖析AQS框架和ReentrantLock源码，涵盖CLH队列、独占锁获取/释放、公平锁vs非公平锁、Condition原理等核心内容。
source: 有道云笔记
---

# 深入理解AQS之独占锁ReentrantLock源码分析

> 主讲老师：Fox

---

## 一、AQS 概述

> AQS (AbstractQueuedSynchronizer) 是 Java 并发工具包中最重要的基石，学习 JUC 必须掌握 AQS。

### 1.1 基本概念

AQS 是一个**抽象队列同步器**，用来构建锁和其他同步组件的基础框架。

- **本质**：FIFO 双向队列 + 一个 `int` 状态变量 `state`
- **核心思想**：如果被请求的共享资源空闲，当前请求线程设置为工作线程，资源锁定；否则进入等待队列

```java
public abstract class AbstractQueuedSynchronizer
    extends AbstractOwnableSynchronizer
    implements java.io.Serializable {

    // 同步状态（volatile + CAS 保证线程安全）
    private volatile int state;

    // CLH 队列
    // head / tail：延迟初始化 + volatile
}
```

### 1.2 state 的含义

| 实现类 | state 含义 |
|--------|-----------|
| ReentrantLock | 锁重入次数 |
| ReentrantReadWriteLock | 高16位：读锁；低16位：写锁 |
| Semaphore | 剩余许可证数 |
| CountDownLatch | 剩余计数 |
| ThreadPoolExecutor | 线程池状态 + 工作线程数 |

### 1.3 AQS 的两种模式

| 模式 | 含义 | 实现类 |
|------|------|--------|
| **独占模式** | 只有一个线程能获取锁 | ReentrantLock |
| **共享模式** | 多个线程可同时获取 | Semaphore、CountDownLatch |

两种模式都有对应的 `acquire/release` 流程，子类只需实现 `tryAcquire/tryRelease`（独占）或 `tryAcquireShared/tryReleaseShared`（共享）。

### 1.4 CLH 队列

AQS 通过内置的 **CLH（Craig, Landin, and Hagersten）锁队列** 来管理线程竞争和同步。

```
Node 节点结构：
┌────────────────────────────────────┐
│ prev (前驱) ← 双向链表              │
│ next (后继)                        │
│ thread (线程引用)                   │
│ waitStatus (等待状态)               │
│ mode: SHARED / EXCLUSIVE           │
└────────────────────────────────────┘

head ← Node ← Node ← Node ← tail
(哨兵)  (T1)    (T2)    (T3)
```

**waitStatus 取值：**

| 值 | 常量 | 含义 |
|------|------|------|
| 0 | 默认 | 初始状态 |
| 1 | CANCELLED | 节点已取消 |
| -1 | SIGNAL | 后继节点需要被唤醒 |
| -2 | CONDITION | 节点在条件队列中 |
| -3 | PROPAGATE | 共享模式下传播（unpark后继） |

---

## 二、ReentrantLock 源码分析

### 2.1 类结构

```
ReentrantLock
  └── Sync extends AbstractQueuedSynchronizer
       ├── NonfairSync (非公平锁)
       └── FairSync (公平锁)
```

```java
public class ReentrantLock implements Lock, java.io.Serializable {
    private final Sync sync;

    abstract static class Sync extends AbstractQueuedSynchronizer {
        abstract void lock();
        // tryRelease 是通用的（公平和非公平都用同一个释放逻辑）
        protected final boolean tryRelease(int releases) { ... }
    }

    static final class NonfairSync extends Sync {
        void lock() { ... }
        protected final boolean tryAcquire(int acquires) { ... }
    }

    static final class FairSync extends Sync {
        void lock() { ... }
        protected final boolean tryAcquire(int acquires) { ... }
    }
}
```

### 2.2 lock() 方法流程

#### 非公平锁 lock()

```java
final void lock() {
    // 先CAS尝试获取锁（插队）
    if (compareAndSetState(0, 1))
        setExclusiveOwnerThread(Thread.currentThread());
    else
        acquire(1);  // 失败走标准流程
}
```

#### 公平锁 lock()

```java
final void lock() {
    acquire(1);  // 直接走标准流程（不插队）
}
```

### 2.3 acquire() 流程

```java
public final void acquire(int arg) {
    // 1. tryAcquire 尝试获取锁
    // 2. 失败 → addWaiter 创建节点入队
    // 3. acquireQueued 自旋/阻塞
    if (!tryAcquire(arg) &&
        acquireQueued(addWaiter(Node.EXCLUSIVE), arg))
        selfInterrupt();
}
```

**详细流程：**

```
acquire(1)
  ├─ tryAcquire(1) → 子类实现
  │   ├─ 成功 → 返回
  │   └─ 失败 → 继续
  ├─ addWaiter(EXCLUSIVE) → 创建Node入队
  │   ├─ 快速入队：tail != null → CAS设置tail
  │   └─ enq() 完整入队：自旋 + CAS
  └─ acquireQueued(node, 1)
      ├─ 死循环自旋
      ├─ node.predecessor() == head? → tryAcquire
      │   ├─ 成功 → 设自己为head → 返回
      │   └─ 失败 → shouldParkAfterFailedAcquire
      │       ├─ 前驱 SIGNAL → parkAndCheckInterrupt()
      │       │   └─ LockSupport.park(this) 阻塞
      │       └─ 前驱 CANCELLED → 跳过取消节点
      └─ 被唤醒 → 重新自旋
```

### 2.4 tryAcquire 实现

#### 非公平锁 tryAcquire

```java
protected final boolean tryAcquire(int acquires) {
    return nonfairTryAcquire(acquires);
}

final boolean nonfairTryAcquire(int acquires) {
    final Thread current = Thread.currentThread();
    int c = getState();
    if (c == 0) {
        // state=0 → 直接CAS抢锁（不等队列中的人）
        if (compareAndSetState(0, acquires)) {
            setExclusiveOwnerThread(current);
            return true;
        }
    }
    else if (current == getExclusiveOwnerThread()) {
        // 重入：state += acquires
        int nextc = c + acquires;
        if (nextc < 0) throw new Error("Maximum lock count exceeded");
        setState(nextc);
        return true;
    }
    return false;
}
```

#### 公平锁 tryAcquire

```java
protected final boolean tryAcquire(int acquires) {
    final Thread current = Thread.currentThread();
    int c = getState();
    if (c == 0) {
        // 关键区别：先检查队列是否有等待者
        if (!hasQueuedPredecessors() &&
            compareAndSetState(0, acquires)) {
            setExclusiveOwnerThread(current);
            return true;
        }
    }
    else if (current == getExclusiveOwnerThread()) {
        // 重入（与非公平一致）
        int nextc = c + acquires;
        if (nextc < 0) throw new Error("...");
        setState(nextc);
        return true;
    }
    return false;
}
```

**公平锁关键判断：`hasQueuedPredecessors()`**

```java
public final boolean hasQueuedPredecessors() {
    Node t = tail;
    Node h = head;
    Node s;
    return h != t &&                    // 队列不空
        ((s = h.next) == null ||        // head.next 为空
         s.thread != Thread.currentThread()); // 下一位不是自己
}
```

> 这样保证：队列中有等待者的时间点比当前线程早，就不让当前线程获取锁 → **公平**。

### 2.5 tryRelease 实现

```java
protected final boolean tryRelease(int releases) {
    int c = getState() - releases;
    if (Thread.currentThread() != getExclusiveOwnerThread())
        throw new IllegalMonitorStateException();
    boolean free = false;
    if (c == 0) {
        free = true;
        setExclusiveOwnerThread(null);
    }
    setState(c);  // state = c
    return free;  // c == 0 才完全释放
}
```

**release() 流程：**

```java
public final boolean release(int arg) {
    if (tryRelease(arg)) {     // state 减到 0
        Node h = head;
        if (h != null && h.waitStatus != 0)
            unparkSuccessor(h);  // 唤醒 head 的下一个节点
        return true;
    }
    return false;
}
```

---

## 三、公平锁 vs 非公平锁 总结

| 对比维度 | 公平锁 | 非公平锁 |
|---------|--------|---------|
| **获取策略** | 先到先得，严格排队 | 新线程可以先抢（插队） |
| **lock() 区别** | 直接调用 `acquire(1)` | 先 CAS 抢一次 |
| **tryAcquire 区别** | 先检查 `hasQueuedPredecessors()` | 直接 CAS |
| **性能** | 较低（更多上下文切换） | 较高 |
| **线程饥饿** | 不会 | 可能 |
| **默认** | | ✅ 默认 |

---

## 四、Condition 条件队列

### 4.1 原理

```java
ReentrantLock lock = new ReentrantLock();
Condition condition = lock.newCondition();

// await() 流程：
// 1. 线程进入 Condition 的等待队列
// 2. 完全释放锁（state=0）
// 3. LockSupport.park() 阻塞
// 4. 被 signal 唤醒后重新获取锁

// signal() 流程：
// 1. 将 Condition 队列的第一个节点转移到 AQS 同步队列
// 2. 转移后在 AQS 队列中等待获取锁
```

**条件队列 vs 同步队列：**

```
AQS同步队列（独占锁阻塞队列）：
head → T1 → T2 → tail

Condition条件队列（等待条件）：
firstWaiter → W1 → W2 → lastWaiter

signal()：W1 从条件队列转移到同步队列尾部
```

### 4.2 await 源码分析

```java
public final void await() throws InterruptedException {
    if (Thread.interrupted()) throw new InterruptedException();
    Node node = addConditionWaiter();   // 加入条件队列
    int savedState = fullyRelease(node); // 释放所有锁
    int interruptMode = 0;
    while (!isOnSyncQueue(node)) {      // 不在同步队列则阻塞
        LockSupport.park(this);
        if ((interruptMode = checkInterruptWhileWaiting(node)) != 0)
            break;
    }
    // 被signal后，在同步队列中重新获取锁
    if (acquireQueued(node, savedState) && interruptMode != THROW_IE)
        interruptMode = REINTERRUPT;
    if (node.nextWaiter != null)
        unlinkCancelledWaiters();       // 清理取消节点
    if (interruptMode != 0)
        reportInterruptAfterWait(interruptMode);
}
```

### 4.3 signal 源码分析

```java
public final void signal() {
    if (!isHeldExclusively())
        throw new IllegalMonitorStateException();
    Node first = firstWaiter;
    if (first != null)
        doSignal(first);  // 转移第一个节点到同步队列
}
```

---

## 五、可中断锁

```java
// lock() — 不可中断，阻塞到获取锁
lock.lock();

// lockInterruptibly() — 等待时可被中断
lock.lockInterruptibly();

// tryLock() — 非阻塞，立即返回
lock.tryLock();

// tryLock(time, unit) — 超时尝试
lock.tryLock(1, TimeUnit.SECONDS);
```

---

## 六、总结

| 主题 | 要点 |
|------|------|
| **AQS 结构** | `volatile int state` + CLH 双向队列 + CAS |
| **Node** | prev/next/thread/waitStatus，管理阻塞线程 |
| **独占获取** | tryAcquire → addWaiter → acquireQueued（自旋+park） |
| **独占释放** | tryRelease → unparkSuccessor 唤醒后继 |
| **公平 vs 非公平** | 非公平先 CAS 抢一次；公平检查 `hasQueuedPredecessors()` |
| **Condition** | 条件队列（单向）↔ 同步队列（双向），signal 转移节点 |
| **可重入** | `state` 记录重入次数，`exclusiveOwnerThread` 记录持有线程 |
