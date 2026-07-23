---
title: CyclicBarrier源码分析
categories: [Java, 并发编程]
tags: [JUC, CyclicBarrier, 源码分析, ReentrantLock, Condition, 栅栏]
author: hsc
date: 2022-05-15 00:00:00 +0800
description: 深入剖析CyclicBarrier源码，基于ReentrantLock+Condition实现循环栅栏，可重用特性、Generation代机制、与CountDownLatch对比。
source: 有道云笔记
---

# CyclicBarrier源码分析

---

## 一、基本概念

CyclicBarrier（循环栅栏）让一组线程达到一个屏障（同步点）时被阻塞，直到**最后一个线程到达**屏障时，屏障才会打开，所有被拦截的线程才会继续运行。

**核心特点：可循环使用。**

### 1.1 类结构

```
CyclicBarrier
  ├── ReentrantLock lock     // 互斥锁
  ├── Condition trip         // 条件变量（基于 lock）
  ├── int parties            // 参与线程总数
  ├── int count              // 剩余等待线程数
  ├── Runnable barrierCommand // 屏障打开时执行的任务（可选）
  └── Generation generation  // 当前"代"
```

### 1.2 Generation

```java
private static class Generation {
    boolean broken;  // 是否损坏（线程中断 / 超时 / 异常）
}
```

> Generation 用于区分不同周期。`reset()` 会创建一个新的 Generation。

### 1.3 构造函数

```java
public CyclicBarrier(int parties) {
    this(parties, null);
}

public CyclicBarrier(int parties, Runnable barrierAction) {
    if (parties <= 0) throw new IllegalArgumentException();
    this.parties = parties;
    this.count = parties;
    this.barrierCommand = barrierAction;
}
```

---

## 二、核心方法

### 2.1 await() — 等待

```java
public int await() throws InterruptedException, BrokenBarrierException {
    try {
        return dowait(false, 0L);
    } catch (TimeoutException toe) {
        throw new Error(toe);  // 不加超时的 await 不会抛 TimeoutException
    }
}

public int await(long timeout, TimeUnit unit)
    throws InterruptedException, BrokenBarrierException, TimeoutException {
    return dowait(true, unit.toNanos(timeout));
}
```

### 2.2 dowait() — 核心实现

```java
private int dowait(boolean timed, long nanos)
    throws InterruptedException, BrokenBarrierException, TimeoutException {

    final ReentrantLock lock = this.lock;
    lock.lock();
    try {
        final Generation g = generation;

        // 1. 检查栅栏是否已损坏
        if (g.broken)
            throw new BrokenBarrierException();

        // 2. 检查当前线程是否被中断
        if (Thread.interrupted()) {
            breakBarrier();  // 损坏栅栏并唤醒所有等待线程
            throw new InterruptedException();
        }

        // 3. count--，index 是当前线程的到达索引
        int index = --count;

        // 4. 如果 count == 0，说明所有线程到达
        if (index == 0) {
            boolean ranAction = false;
            try {
                final Runnable command = barrierCommand;
                if (command != null)
                    command.run();  // 执行屏障动作
                ranAction = true;
                nextGeneration();   // 开启下一代
                return 0;
            } finally {
                if (!ranAction)
                    breakBarrier(); // 屏障动作失败 → 损坏栅栏
            }
        }

        // 5. count > 0，等待其他线程
        for (;;) {
            try {
                if (!timed)
                    trip.await();     // Condition.await() 阻塞
                else if (nanos > 0L)
                    nanos = trip.awaitNanos(nanos);  // 超时等待
            } catch (InterruptedException ie) {
                if (g == generation && !g.broken) {
                    breakBarrier();
                    throw ie;
                } else {
                    Thread.currentThread().interrupt();
                }
            }

            if (g.broken)
                throw new BrokenBarrierException();

            if (g != generation)  // 新一代 → 成功
                return index;

            if (timed && nanos <= 0L) {
                breakBarrier();
                throw new TimeoutException();
            }
        }
    } finally {
        lock.unlock();
    }
}
```

### 2.3 nextGeneration() — 开启下一代

```java
private void nextGeneration() {
    trip.signalAll();       // 唤醒所有等待线程
    count = parties;        // 重置 count
    generation = new Generation();  // 新的 Generation
}
```

### 2.4 breakBarrier() — 损坏栅栏

```java
private void breakBarrier() {
    generation.broken = true;  // 标记损坏
    count = parties;           // 重置 count
    trip.signalAll();          // 唤醒所有等待线程
}
```

### 2.5 reset() — 重置

```java
public void reset() {
    final ReentrantLock lock = this.lock;
    lock.lock();
    try {
        breakBarrier();       // 损坏当前代
        nextGeneration();     // 启动新一代
    } finally {
        lock.unlock();
    }
}
```

---

## 三、核心流程总结

```
┌─────────────────────────────────────────────┐
│ CyclicBarrier cb = new CyclicBarrier(N, task)│
│                                              │
│ 线程1: cb.await() → count-- → count>0 → 阻塞│
│ 线程2: cb.await() → count-- → count>0 → 阻塞│
│ ...                                          │
│ 线程N: cb.await() → count-- → count==0      │
│   → 执行 barrierCommand                     │
│   → nextGeneration()                        │
│     → trip.signalAll() 唤醒所有线程          │
│     → count = N, generation = new           │
│                                              │
│ 所有线程被唤醒，检查 g != generation，成功！ │
│ 可以继续下一轮 await() ...                   │
└─────────────────────────────────────────────┘
```

---

## 四、与 CountDownLatch 对比

| | CyclicBarrier | CountDownLatch |
|------|------|------|
| **可重用** | ✅ `reset()` 重置 | ❌ 一次性 |
| **计数器** | 减计数（count→0触发） | 减计数（count→0触发） |
| **角色** | 线程互相等待 | 一个/多个等待线程 + 多个执行线程 |
| **屏障动作** | 支持 `Runnable` | 不支持 |
| **异常处理** | Generation.broken 损坏机制 | 无 |
| **底层实现** | ReentrantLock + Condition | AQS 共享模式 |
| **获取等待数** | `getNumberWaiting()` | `getCount()` |

---

## 五、使用示例

```java
public class CyclicBarrierExample {
    static CyclicBarrier barrier = new CyclicBarrier(3, () -> {
        System.out.println("所有线程到达，执行屏障动作！");
    });

    public static void main(String[] args) {
        for (int i = 0; i < 3; i++) {
            new Thread(() -> {
                try {
                    System.out.println(Thread.currentThread().getName() + " 到达");
                    barrier.await();  // 等待其他线程
                    System.out.println(Thread.currentThread().getName() + " 继续");
                    
                    // 第二轮
                    barrier.await();  // 可以重复使用
                    System.out.println(Thread.currentThread().getName() + " 第二轮完成");
                } catch (Exception e) { e.printStackTrace(); }
            }).start();
        }
    }
}
```

---

## 六、总结

| 要点 | 说明 |
|------|------|
| **底层** | ReentrantLock + Condition |
| **核心变量** | `parties`（总数）、`count`（剩余）、`Generation`（代） |
| **dowait 流程** | count-- → count==0 触发 → nextGeneration → 否则 Condition.await |
| **可循环** | `reset()` 或 `nextGeneration()` 重置 count 和 generation |
| **异常处理** | `breakBarrier()` 标记 broken=true + 唤醒所有 |
