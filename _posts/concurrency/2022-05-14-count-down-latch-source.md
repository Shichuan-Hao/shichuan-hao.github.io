---
title: CountDownLatch源码分析
categories: [Java, 并发编程]
tags: [JUC, CountDownLatch, AQS, 共享锁, 源码分析, 并发工具]
author: hsc
date: 2022-05-14 00:00:00 +0800
description: 深入剖析CountDownLatch源码，基于AQS共享模式实现，涵盖countDown、await原理、与CyclicBarrier对比。
source: 有道云笔记
---

# CountDownLatch源码分析

---

## 一、基本概念

CountDownLatch 是一个**倒计时门闩**，让一个/一组线程等待其他线程完成操作。计数器为 0 时释放所有等待线程。**一次性使用，不可重置。**

### 1.1 类结构

```
CountDownLatch
  └── Sync extends AbstractQueuedSynchronizer (AQS)
```

CountDownLatch 只有一个内部类 Sync，基于 AQS 共享模式。

### 1.2 构造函数

```java
public CountDownLatch(int count) {
    if (count < 0) throw new IllegalArgumentException("count < 0");
    this.sync = new Sync(count);
}

Sync(int count) {
    setState(count);  // AQS state = count
}
```

---

## 二、核心方法源码

### 2.1 countDown() — 计数器减1

```java
public void countDown() {
    sync.releaseShared(1);  // 共享模式释放
}

// AQS
public final boolean releaseShared(int arg) {
    if (tryReleaseShared(arg)) {   // state 减到 0 返回 true
        doReleaseShared();         // 唤醒所有等待线程
        return true;
    }
    return false;
}
```

#### Sync#tryReleaseShared

```java
protected boolean tryReleaseShared(int releases) {
    for (;;) {
        int c = getState();
        if (c == 0) return false;  // 已经是0，不操作
        int nextc = c - 1;
        if (compareAndSetState(c, nextc))
            return nextc == 0;  // 减到0时返回true，触发doReleaseShared
    }
}
```

### 2.2 await() — 等待

```java
public void await() throws InterruptedException {
    sync.acquireSharedInterruptibly(1);
}

// AQS
public final void acquireSharedInterruptibly(int arg) throws InterruptedException {
    if (Thread.interrupted()) throw new InterruptedException();
    if (tryAcquireShared(arg) < 0)         // state != 0 → 返回-1
        doAcquireSharedInterruptibly(arg); // 入队阻塞
}
```

#### Sync#tryAcquireShared

```java
protected int tryAcquireShared(int acquires) {
    return (getState() == 0) ? 1 : -1;  // 极简：state=0则成功
}
```

#### doAcquireSharedInterruptibly — 入队阻塞

```java
private void doAcquireSharedInterruptibly(int arg) {
    final Node node = addWaiter(Node.SHARED);  // 共享节点入队
    boolean failed = true;
    try {
        for (;;) {
            final Node p = node.predecessor();
            if (p == head) {
                int r = tryAcquireShared(arg);
                if (r >= 0) {                        // state == 0
                    setHeadAndPropagate(node, r);    // 设置head并传播唤醒
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

---

## 三、核心流程总结

```
┌─────────────────────────────────────────────┐
│ CountDownLatch latch = new CountDownLatch(N);│  state = N
│                                              │
│ 工作线程1: latch.countDown()  → state -= 1  │
│ 工作线程2: latch.countDown()  → state -= 1  │
│ ...                                          │
│ 工作线程N: latch.countDown()  → state = 0   │
│                           ├─ tryReleaseShared返回true│
│                           └─ doReleaseShared 唤醒所有await线程│
│                                              │
│ 主线程:  latch.await()                       │
│   ├─ tryAcquireShared: state==0?返回1:返回-1 │
│   ├─ state≠0 → 入队 → park 阻塞             │
│   └─ state==0 → 被唤醒 → 继续执行            │
└─────────────────────────────────────────────┘
```

---

## 四、执行流程图

```
主线程: await()
  → acquireSharedInterruptibly(1)
    → tryAcquireShared(1)
      → state == 0 ? return 1 : return -1
        → -1: doAcquireSharedInterruptibly
          → addWaiter(SHARED)
          → for(;;)自旋
            → predecessor==head? tryAcquireShared
              → 成功: setHeadAndPropagate(传播)
              → 失败: park()阻塞

工作线程: countDown()
  → releaseShared(1)
    → tryReleaseShared(1)
      → CAS: state--
      → state==0 ? return true : false
        → true: doReleaseShared()
          → unparkSuccessor(head) 唤醒所有等待线程
```

---

## 五、应用场景

| 场景 | 描述 |
|------|------|
| **并发测试模拟** | 多个线程同时启动压测 |
| **对账系统** | 多个数据源查询完成后汇总 |
| **任务依赖** | A、B、C 三个任务完成后再执行 D |
| **启动前检查** | 所有组件初始化完成后启动服务 |

```java
// 压测：让 100 个线程同时开始
CountDownLatch startGate = new CountDownLatch(1);
CountDownLatch endGate = new CountDownLatch(100);

for (int i = 0; i < 100; i++) {
    new Thread(() -> {
        try {
            startGate.await();  // 都等待发令枪
            doWork();
        } finally {
            endGate.countDown();
        }
    }).start();
}
startGate.countDown();  // 发令！
endGate.await();        // 等全部完成
System.out.println("全部完成！");
```

---

## 六、CountDownLatch vs CyclicBarrier

| 对比维度 | CountDownLatch | CyclicBarrier |
|---------|---------------|---------------|
| **计数方向** | 递减 | 递增 |
| **可重用** | 不可重用 | `reset()` 重置 |
| **角色分工** | 主线程等待多个工作线程 | 多个线程互相等待 |
| **使用次数** | 一次性 | 可循环使用 |

---

## 七、总结

| 要点 | 说明 |
|------|------|
| **模式** | AQS 共享模式 |
| **state 含义** | 剩余计数 |
| **countDown** | CAS `state--`，减到 0 唤醒所有 |
| **await** | `state != 0` 入队阻塞，`state == 0` 直接通过 |
| **不可重用** | state 到 0 后无法重置 |
