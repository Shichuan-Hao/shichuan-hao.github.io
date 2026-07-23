---
title: JUC并发同步工具类在大厂中应用实战
categories: [Java, 并发编程]
tags: [JUC, CountDownLatch, CyclicBarrier, Semaphore, Exchanger, Phaser, ReentrantLock, Condition]
author: hsc
date: 2022-05-11 00:00:00 +0800
description: 深入讲解JUC并发同步工具类在大厂中的实际应用，涵盖CountDownLatch、CyclicBarrier、Semaphore、Exchanger、Phaser、ReentrantLock与Condition等核心类。
source: 有道云笔记 / 公众号:CunWorkNotes
---

# JUC并发同步工具类在大厂中应用实战

> 主讲老师：Fox

---

## 一、JUC 概述

### 1.1 JUC 包分类

Java 并发工具包 `java.util.concurrent` 可分为以下分类：

| 分类 | 包含内容 |
|------|---------|
| **locks 包** | ReentrantLock、ReentrantReadWriteLock、StampedLock、AbstractQueuedSynchronizer |
| **atomic 包** | AtomicInteger、AtomicLong、LongAdder、AtomicReference 等 |
| **tools 工具类** | CountDownLatch、CyclicBarrier、Semaphore、Exchanger、Phaser |
| **collections 并发容器** | ConcurrentHashMap、CopyOnWriteArrayList、BlockingQueue 等 |
| **executor 线程池** | ThreadPoolExecutor、ForkJoinPool、FutureTask 等 |

---

## 二、CountDownLatch（倒计时门闩）

### 2.1 场景

某年级 4 个班班主任统计成绩，要等**所有班级统计完**后年级主任才汇总。

### 2.2 核心 API

| 方法 | 说明 |
|------|------|
| `CountDownLatch(int count)` | 构造器，计数器初始值 |
| `countDown()` | 计数器减 1 |
| `await()` | 当前线程等待，直到计数器为 0 |
| `await(long timeout, TimeUnit unit)` | 带超时等待 |

### 2.3 应用案例

```java
// 线程池 + CountDownLatch 优化
public class CountDownLatchPoolDemo {
    private static ExecutorService executorService = Executors.newFixedThreadPool(2);
    private static CountDownLatch latch = new CountDownLatch(5);

    public static void main(String[] args) throws InterruptedException {
        for (int i = 0; i < 5; i++) {
            executorService.submit(() -> {
                System.out.println(Thread.currentThread().getName() + " 开始计算");
                try { Thread.sleep(1000); } catch (InterruptedException e) {}
                latch.countDown();
                System.out.println(Thread.currentThread().getName() + " 计算完成");
            });
        }
        latch.await();  // 主线程等待所有任务完成
        System.out.println("所有计算任务完成，汇总结果");
        executorService.shutdown();
    }
}
```

### 2.4 核心源码

```java
// CountDownLatch 基于 AQS 共享模式实现
public class CountDownLatch {
    private final Sync sync;

    private static final class Sync extends AbstractQueuedSynchronizer {
        Sync(int count) { setState(count); }
        int getCount() { return getState(); }
        // 共享模式：state == 0 时获取成功
        protected int tryAcquireShared(int acquires) {
            return (getState() == 0) ? 1 : -1;
        }
        protected boolean tryReleaseShared(int releases) {
            for (;;) {
                int c = getState();
                if (c == 0) return false;
                int nextc = c - 1;
                if (compareAndSetState(c, nextc))
                    return nextc == 0;
            }
        }
    }
}
```

**原理：** 构造函数设置 AQS `state = count`。`countDown()` → `releaseShared(1)` 对 state 减 1，`state = 0` 时唤醒所有等待线程。`await()` → `acquireSharedInterruptibly(1)` 检查 state 是否为 0。

### 2.5 大厂应用场景

- **电商压测** — 模拟高并发：`CountDownLatch(1)` 控制所有线程同时开始
- **对账系统** — 查询未对账订单、派送单、订单商品 → 等所有完成再汇总
- **单测/集成测试** — 等待异步结果后 assertion

---

## 三、CyclicBarrier（循环栅栏）

### 3.1 场景

公司团建，所有人必须在楼下集合后统一出发，人到齐了才能走。

### 3.2 核心 API

| 方法 | 说明 |
|------|------|
| `CyclicBarrier(int parties)` | 设置参与线程数 |
| `CyclicBarrier(int parties, Runnable barrierAction)` | 人到齐后执行的动作 |
| `await()` | 等待，当前线程被拦截 |
| `await(long timeout, TimeUnit unit)` | 带超时 |
| `getNumberWaiting()` | 当前等待的线程数 |
| `isBroken()` | 栅栏是否损坏 |
| `reset()` | 重置栅栏为初始状态 |

### 3.3 应用案例

```java
public class CyclicBarrierDemo {
    private static final int THREAD_NUM = 5;

    public static void main(String[] args) {
        CyclicBarrier cyclicBarrier = new CyclicBarrier(THREAD_NUM, () -> {
            System.out.println("------当线程数达到" + THREAD_NUM + "之后，执行------");
        });

        for (int i = 0; i < THREAD_NUM + 2; i++) {
            int index = i;
            new Thread(() -> {
                try {
                    System.out.println(Thread.currentThread().getName() + " 集合");
                    cyclicBarrier.await();  // 阻塞直到 5 个线程都到达
                    System.out.println(Thread.currentThread().getName() + " 出发");
                } catch (Exception e) { e.printStackTrace(); }
            }, "Thread-" + index).start();
        }
    }
}
```

### 3.4 核心源码

CyclicBarrier 基于 ReentrantLock + Condition 实现，通过 `Generation` 区分不同代：

```
核心结构：
- parties：参与线程数
- count：剩余等待线程数（每次 await 减 1）
- Generation：当前代，broken 时断开
- ReentrantLock + Condition：阻塞/唤醒
```

### 3.5 CountDownLatch vs CyclicBarrier

| 对比维度 | CountDownLatch | CyclicBarrier |
|---------|---------------|---------------|
| **可重用** | 不可重用 | `reset()` 可重置复用 |
| **角色** | 一个/多个等待线程 + 多个工作线程 | 线程之间互相等待 |
| **计数方向** | 递减（count down） | 递增（等待线程越来越多） |
| **场景** | 等待 N 个任务完成 | N 个线程相互等待，然后一起出发 |

---

## 四、Semaphore（信号量）

### 4.1 概念

信号量是一种**共享锁**，用来控制同时访问特定资源的线程数量。通过对令牌（permits）的获取和释放来协调各线程。

### 4.2 使用场景

- 停车场有空位才能停车
- 连接池（最多 10 个连接，来一个减一，用完加一）
- 限流

### 4.3 核心 API

| 方法 | 说明 |
|------|------|
| `Semaphore(int permits)` | 构造函数，指定许可证数（非公平） |
| `Semaphore(int permits, boolean fair)` | 指定是否公平 |
| `acquire()` | 获取许可，阻塞 |
| `acquire(int permits)` | 获取 permits 个许可 |
| `release()` | 释放一个许可 |
| `release(int permits)` | 释放 permits 个许可 |
| `availablePermits()` | 当前可用许可数 |
| `tryAcquire()` | 尝试获取，无许可返回 false |
| `tryAcquire(long timeout, TimeUnit unit)` | 带超时尝试 |

```java
public class SemaphoreDemo {
    public static void main(String[] args) {
        Semaphore semaphore = new Semaphore(3);  // 3个车位
        for (int i = 0; i < 6; i++) {
            new Thread(() -> {
                try {
                    semaphore.acquire();
                    System.out.println(Thread.currentThread().getName() + " 抢到了车位");
                    Thread.sleep(2000);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                } finally {
                    System.out.println(Thread.currentThread().getName() + " 离开了车位");
                    semaphore.release();
                }
            }, "车辆" + i).start();
        }
    }
}
```

### 4.4 核心源码（基于 AQS 共享模式）

```java
// 获取许可
semaphore.acquire() → sync.acquireSharedInterruptibly(1)
  → tryAcquireShared(1)
    → 检查 state - 1 >= 0 ? CAS减1 : 返回负数入队阻塞

// 释放许可  
semaphore.release() → sync.releaseShared(1)
  → tryReleaseShared(1) 
    → CAS state + 1，唤醒后续等待线程
```

### 4.5 限流案例

```java
// 简单限流器（最多同时 10 个请求）
public class RateLimiter {
    private final Semaphore semaphore;
    
    public RateLimiter(int maxPermits) {
        this.semaphore = new Semaphore(maxPermits);
    }
    
    public boolean tryAcquire() {
        return semaphore.tryAcquire();
    }
    
    public void release() {
        semaphore.release();
    }
}
```

---

## 五、Exchanger（交换器）

### 5.1 概念

两个线程之间交换数据的同步点。线程 A 和线程 B 互相交换数据，**成对出现**。

### 5.2 核心 API

| 方法 | 说明 |
|------|------|
| `exchange(V x)` | 交换数据，阻塞直到另一个线程到达 |
| `exchange(V x, long timeout, TimeUnit unit)` | 带超时 |

### 5.3 使用案例

```java
public class ExchangerDemo {
    private static Exchanger<String> exchanger = new Exchanger<>();

    public static void main(String[] args) {
        new Thread(() -> {
            String A = "银行流水A";
            try {
                String B = exchanger.exchange(A);
                System.out.println("A收到：" + B);
            } catch (InterruptedException e) { e.printStackTrace(); }
        }, "A").start();

        new Thread(() -> {
            String B = "银行流水B";
            try {
                String A = exchanger.exchange(B);
                System.out.println("B收到：" + A);
            } catch (InterruptedException e) { e.printStackTrace(); }
        }, "B").start();
    }
}
```

### 5.4 应用场景

- **遗传算法** — 两批染色体交换
- **校对工作** — 两人交换数据相互校验
- **数据交换** — 银行流水对账

---

## 六、Phaser（阶段器）

### 6.1 概念

JDK 1.7 引入，**增强版 CyclicBarrier + CountDownLatch**。支持分阶段同步，动态调整参与线程数。

### 6.2 核心 API

| 方法 | 说明 |
|------|------|
| `Phaser()` / `Phaser(int parties)` | 构造，初始参与方 0 或指定 |
| `register()` | 新增一个参与方 |
| `bulkRegister(int parties)` | 批量注册 |
| `arriveAndAwaitAdvance()` | 到达并等待其他方（类似 await） |
| `arriveAndDeregister()` | 到达并注销（不参与下一阶段） |
| `arrive()` | 到达（不等待） |
| `getPhase()` | 获取当前阶段号 |
| `getRegisteredParties()` | 获取已注册参与方数 |
| `getArrivedParties()` | 已到达参与方数 |

### 6.3 示例

```java
public class PhaserDemo {
    public static void main(String[] args) {
        Phaser phaser = new Phaser(3) {
            @Override
            protected boolean onAdvance(int phase, int registeredParties) {
                System.out.println("=====第" + phase + "阶段完成=====");
                return phase >= 2;  // 3 阶段后终止
            }
        };

        for (int i = 0; i < 3; i++) {
            new Thread(() -> {
                while (!phaser.isTerminated()) {
                    int phase = phaser.arriveAndAwaitAdvance();
                    System.out.println(Thread.currentThread().getName() + " 完成阶段" + phase);
                }
            }, "T" + i).start();
        }
    }
}
```

---

## 七、ReentrantLock

### 7.1 概念

可重入互斥锁，与 synchronized 类似但更灵活。基于 AQS 实现。

### 7.2 API

| 方法 | 说明 |
|------|------|
| `lock()` | 获取锁，阻塞 |
| `lockInterruptibly()` | 可中断获取 |
| `tryLock()` | 尝试获取，非阻塞 |
| `tryLock(long time, TimeUnit unit)` | 带超时尝试 |
| `unlock()` | 释放锁（必须 finally 中调用） |
| `newCondition()` | 创建条件变量 |
| `getHoldCount()` | 当前线程持有锁次数 |
| `isHeldByCurrentThread()` | 是否被当前线程持有 |
| `isFair()` | 是否公平锁 |

### 7.3 基本使用

```java
ReentrantLock lock = new ReentrantLock();

lock.lock();
try {
    // 业务代码
} finally {
    lock.unlock();  // 必须在 finally 中释放
}
```

### 7.4 公平锁 vs 非公平锁

```java
ReentrantLock fairLock = new ReentrantLock(true);     // 公平锁
ReentrantLock unfairLock = new ReentrantLock(false);  // 非公平锁（默认）
```

| | 公平锁 | 非公平锁 |
|------|------|------|
| 获取策略 | 先到先得（队列） | 插队抢占 |
| 吞吐量 | 较低 | 较高 |
| 饥饿 | 不会 | 可能 |

### 7.5 可重入性

```java
// 同一个线程多次获取同一把锁
lock.lock();
lock.lock();  // 重入成功，state = 2
lock.unlock();
lock.unlock();  // state = 0 才真正释放
```

### 7.6 条件变量 Condition

```java
ReentrantLock lock = new ReentrantLock();
Condition condition = lock.newCondition();

// 等待方
lock.lock();
try {
    while (条件不满足) {
        condition.await();
    }
    // 业务逻辑
} finally {
    lock.unlock();
}

// 通知方
lock.lock();
try {
    // 改变条件
    condition.signalAll();  // 或 signal()
} finally {
    lock.unlock();
}
```

---

## 八、ReentrantReadWriteLock（读写锁）

### 8.1 概念

读写锁允许：**读读共享、读写互斥、写写互斥**。

```java
ReentrantReadWriteLock rwLock = new ReentrantReadWriteLock();
rwLock.readLock().lock();   // 读锁（共享）
rwLock.writeLock().lock();  // 写锁（独占）
```

### 8.2 适用场景

**读多写少**的场景。缓存系统是最典型应用。

### 8.3 锁降级

写锁可以降级为读锁（获取写锁 → 获取读锁 → 释放写锁），但**不支持锁升级**。

```java
rwLock.writeLock().lock();
try {
    // 写操作
    rwLock.readLock().lock();  // 获取读锁
} finally {
    rwLock.writeLock().unlock();  // 释放写锁 → 降级为读锁
}
try {
    // 在读锁保护下做后续处理
} finally {
    rwLock.readLock().unlock();
}
```

---

## 九、StampedLock（JDK8+）

### 9.1 概念

ReentrantReadWriteLock 的升级版，支持三种模式：

| 模式 | 说明 |
|------|------|
| **写锁**（Write Lock） | 排他写锁，`writeLock()` |
| **悲观读锁**（Pessimistic Read） | 与写锁互斥，`readLock()` |
| **乐观读**（Optimistic Read） | 无锁，通过戳验证，`tryOptimisticRead()` |

```java
StampedLock sl = new StampedLock();

// 乐观读
long stamp = sl.tryOptimisticRead();
// 读数据...
if (!sl.validate(stamp)) {   // 验证戳是否被修改
    stamp = sl.readLock();   // 升级为悲观读
    try {
        // 重读数据...
    } finally {
        sl.unlockRead(stamp);
    }
}
```

### 9.2 注意事项

- **不可重入**（与 ReentrantReadWriteLock 不同）
- 写锁支持条件变量，读锁不支持
- 需要显式传递 stamp

---

## 十、大厂实战案例

### 10.1 电商对账系统

```java
// 并发查3个数据源 → CountDownLatch 聚合
CountDownLatch latch = new CountDownLatch(3);
executor.submit(() -> { queryUncheckOrders(); latch.countDown(); });
executor.submit(() -> { queryDeliverOrders(); latch.countDown(); });
executor.submit(() -> { queryProductInfo(); latch.countDown(); });
latch.await();
merge();
```

### 10.2 接口限流

```java
// Semaphore 限流
Semaphore limiter = new Semaphore(50);  // 最多 50 并发
if (limiter.tryAcquire(100, TimeUnit.MILLISECONDS)) {
    try { process(); } finally { limiter.release(); }
} else {
    throw new RuntimeException("系统繁忙，请稍后再试");
}
```

### 10.3 缓存更新

```java
// ReadWriteLock 读多写少
class Cache {
    Map<String, Object> map = new HashMap<>();
    ReentrantReadWriteLock lock = new ReentrantReadWriteLock();
    
    Object get(String key) {
        lock.readLock().lock();
        try { return map.get(key); } finally { lock.readLock().unlock(); }
    }
    
    void put(String key, Object val) {
        lock.writeLock().lock();
        try { map.put(key, val); } finally { lock.writeLock().unlock(); }
    }
}
```

---

## 十一、总结

| 工具类 | 用途 | 一句话 |
|--------|------|--------|
| CountDownLatch | 等待 N 个任务完成 | "等大家都做完" |
| CyclicBarrier | N 个线程互相等待 | "人到齐了一起出发" |
| Semaphore | 控制并发数（令牌） | "有空位才能进" |
| Exchanger | 两线程交换数据 | "交换银行流水" |
| Phaser | 分阶段同步 | "多阶段赛跑" |
| ReentrantLock | 显式独占锁 | "synchronized 的升级版" |
| ReentrantReadWriteLock | 读写锁 | "读读共享，读写互斥" |
| StampedLock | 乐观读 + 读写锁 | "更高性能的读写锁" |
