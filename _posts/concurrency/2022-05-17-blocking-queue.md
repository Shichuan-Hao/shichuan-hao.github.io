---
title: 阻塞队列BlockingQueue实战及其原理分析
categories: [Java, 并发编程]
tags: [BlockingQueue, 阻塞队列, ArrayBlockingQueue, LinkedBlockingQueue, SynchronousQueue, DelayQueue, PriorityBlockingQueue, 生产者消费者]
author: hsc
date: 2022-05-17 00:00:00 +0800
description: 深入讲解BlockingQueue实战与原理，涵盖7种阻塞队列特点、源码分析、线程池选型、生产者消费者模式及DelayQueue延迟订单实战。
---


## 一、BlockingQueue 概述

### 1.1 什么是阻塞队列

BlockingQueue 是 `java.util.concurrent` 包下的接口，继承了 `Queue` 接口。

- **队列为空时**：获取元素的操作会被阻塞
- **队列满时**：添加元素的操作会被阻塞
- 天然适合**生产者-消费者**模式

### 1.2 核心方法

| 方法类型 | 抛出异常 | 返回特殊值 | 一直阻塞 | 超时退出 |
|---------|---------|-----------|---------|---------|
| **插入** | `add(e)` | `offer(e)` | `put(e)` | `offer(e, time, unit)` |
| **移除** | `remove()` | `poll()` | `take()` | `poll(time, unit)` |
| **检查** | `element()` | `peek()` | 不支持 | 不支持 |

### 1.3 阻塞队列全家福

| 队列 | 数据结构 | 有界 | 特点 |
|------|---------|------|------|
| **ArrayBlockingQueue** | 数组 | ✅ 有界 | 一把 ReentrantLock |
| **LinkedBlockingQueue** | 链表 | 默认 Integer.MAX_VALUE | 两把锁（putLock/takeLock） |
| **SynchronousQueue** | 无存储 | ✅ 容量0 | 直接传递，不存储 |
| **PriorityBlockingQueue** | 数组（堆） | 无界 | 优先级排序 |
| **DelayQueue** | 优先级队列 | 无界 | 延迟取出 |
| **LinkedTransferQueue** | 链表 | 无界 | 融合 transfer + Synchronous |
| **LinkedBlockingDeque** | 双向链表 | 可设容量 | 双端操作 |

---

## 二、ArrayBlockingQueue 源码分析

### 2.1 数据结构

```java
public class ArrayBlockingQueue<E> extends AbstractQueue<E> {
    final Object[] items;        // 底层数组
    int takeIndex;               // 队头
    int putIndex;                // 队尾
    int count;                   // 元素个数
    final ReentrantLock lock;    // 全局唯一锁
    private final Condition notEmpty;   // take 等待条件
    private final Condition notFull;    // put 等待条件
}
```

### 2.2 put 方法

```java
public void put(E e) throws InterruptedException {
    checkNotNull(e);
    final ReentrantLock lock = this.lock;
    lock.lockInterruptibly();
    try {
        while (count == items.length)   // 队列满 → 阻塞
            notFull.await();
        enqueue(e);                     // 入队
    } finally {
        lock.unlock();
    }
}

private void enqueue(E x) {
    final Object[] items = this.items;
    items[putIndex] = x;
    if (++putIndex == items.length) putIndex = 0;  // 循环
    count++;
    notEmpty.signal();  // 唤醒等待 take 的线程
}
```

### 2.3 take 方法

```java
public E take() throws InterruptedException {
    final ReentrantLock lock = this.lock;
    lock.lockInterruptibly();
    try {
        while (count == 0)   // 队列空 → 阻塞
            notEmpty.await();
        return dequeue();
    } finally {
        lock.unlock();
    }
}

private E dequeue() {
    final Object[] items = this.items;
    E x = (E) items[takeIndex];
    items[takeIndex] = null;
    if (++takeIndex == items.length) takeIndex = 0;  // 循环
    count--;
    if (itrs != null) itrs.elementDequeued();  // 通知迭代器
    notFull.signal();  // 唤醒等待 put 的线程
    return x;
}
```

**特点总结：**
- 一把 ReentrantLock，put 和 take 互斥
- 循环数组，takeIndex/putIndex 循环使用
- notEmpty（读等待）+ notFull（写等待）

---

## 三、LinkedBlockingQueue 源码分析

### 3.1 数据结构

```java
public class LinkedBlockingQueue<E> extends AbstractQueue<E> {
    static class Node<E> {
        E item;
        Node<E> next;
    }
    private final int capacity;          // 容量（默认 Integer.MAX_VALUE）
    private final AtomicInteger count;   // 原子计数器
    transient Node<E> head;
    private transient Node<E> last;
    private final ReentrantLock takeLock;    // 出队锁
    private final Condition notEmpty = takeLock.newCondition();
    private final ReentrantLock putLock;     // 入队锁
    private final Condition notFull = putLock.newCondition();
}
```

### 3.2 两把锁设计

**put 锁和 take 锁分离** → 生产者和消费者可以并行操作，吞吐量更高。

```java
// put 使用 putLock
public void put(E e) throws InterruptedException {
    int c = -1;
    Node<E> node = new Node<E>(e);
    final ReentrantLock putLock = this.putLock;
    final AtomicInteger count = this.count;
    putLock.lockInterruptibly();
    try {
        while (count.get() == capacity)
            notFull.await();      // 满则阻塞于 putLock 的条件
        enqueue(node);
        c = count.getAndIncrement();
        if (c + 1 < capacity)
            notFull.signal();     // 还有空位，唤醒下一个生产者
    } finally {
        putLock.unlock();
    }
    if (c == 0)
        signalNotEmpty();  // 原来是空的 → 可能有消费者在等 → 唤醒
}

// take 使用 takeLock
public E take() throws InterruptedException {
    E x;
    int c = -1;
    final AtomicInteger count = this.count;
    final ReentrantLock takeLock = this.takeLock;
    takeLock.lockInterruptibly();
    try {
        while (count.get() == 0)
            notEmpty.await();     // 空则阻塞于 takeLock 的条件
        x = dequeue();
        c = count.getAndDecrement();
        if (c > 1)
            notEmpty.signal();    // 还有元素 → 唤醒下一个消费者
    } finally {
        takeLock.unlock();
    }
    if (c == capacity)
        signalNotFull(); // 原来是满的 → 可能有生产者在等 → 唤醒
    return x;
}
```

---

## 四、ArrayBlockingQueue vs LinkedBlockingQueue

| 对比 | ArrayBlockingQueue | LinkedBlockingQueue |
|------|------|------|
| **数据结构** | 数组（循环） | 单向链表 |
| **锁机制** | 1 把 ReentrantLock | 2 把（putLock + takeLock） |
| **并发度** | put/take 互斥 | put/take 可并行 |
| **内存** | 预分配，不产生额外对象 | 每次插入创建 Node |
| **必须指定容量** | ✅ | 可选（默认超大） |
| **适用场景** | 容量固定，高并发压力不大 | 高并发生产消费 |

---

## 五、PriorityBlockingQueue

基于**堆（数组实现）**的优先级无界阻塞队列。`take` 时取最小元素。

```java
PriorityBlockingQueue<Task> queue = new PriorityBlockingQueue<>(10,
    (a, b) -> a.priority - b.priority);
```

- 无界（`tryGrow` 自动扩容）
- 一把 `ReentrantLock`
- `notEmpty` Condition（只有取等待，写不阻塞）

---

## 六、DelayQueue

### 6.1 概念

无界延迟阻塞队列，元素必须实现 `Delayed` 接口。**只有到期元素才能被取出。**

```java
public interface Delayed extends Comparable<Delayed> {
    long getDelay(TimeUnit unit);  // 剩余延迟时间
}
```

### 6.2 数据结构

```java
public class DelayQueue<E extends Delayed> extends AbstractQueue<E> {
    private final transient ReentrantLock lock = new ReentrantLock();
    private final PriorityQueue<E> q = new PriorityQueue<>(); // 堆
    private Thread leader = null;  // 等待到期的线程
    private final Condition available = lock.newCondition();
}
```

### 6.3 延迟订单实战

```java
public class DelayQueueExample {
    public static void main(String[] args) throws InterruptedException {
        DelayQueue<Order> delayQueue = new DelayQueue<>();
        delayQueue.put(new Order("order1", System.currentTimeMillis(), 5000));
        delayQueue.put(new Order("order2", System.currentTimeMillis(), 2000));
        delayQueue.put(new Order("order3", System.currentTimeMillis(), 3000));

        while (!delayQueue.isEmpty()) {
            Order order = delayQueue.take();
            System.out.println("处理订单：" + order.getOrderId());
        }
    }

    static class Order implements Delayed {
        private String orderId;
        private long createTime;
        private long delayTime;

        public Order(String orderId, long createTime, long delayTime) {
            this.orderId = orderId;
            this.createTime = createTime;
            this.delayTime = delayTime;
        }

        @Override
        public long getDelay(TimeUnit unit) {
            long diff = createTime + delayTime - System.currentTimeMillis();
            return unit.convert(diff, TimeUnit.MILLISECONDS);
        }

        @Override
        public int compareTo(Delayed o) {
            return Long.compare(this.getDelay(TimeUnit.MILLISECONDS),
                                o.getDelay(TimeUnit.MILLISECONDS));
        }
    }
}
```

### 6.4 take 方法关键逻辑

```java
public E take() throws InterruptedException {
    lock.lockInterruptibly();
    try {
        for (;;) {
            E first = q.peek();   // 堆顶（最早到期）
            if (first == null) {
                available.await();  // 队列空 → 无限等待
            } else {
                long delay = first.getDelay(NANOSECONDS);
                if (delay <= 0)
                    return q.poll();  // 到期 → 取出
                first = null;
                if (leader != null)
                    available.await();    // 有人已在等 → 无限等待
                else {
                    Thread thisThread = Thread.currentThread();
                    leader = thisThread;
                    try {
                        available.awaitNanos(delay);  // 按延迟等待
                    } finally {
                        if (leader == thisThread)
                            leader = null;
                    }
                }
            }
        }
    } finally {
        if (leader == null && q.peek() != null)
            available.signal();
        lock.unlock();
    }
}
```

**Leader-Follower 模式：** 只让一个线程等待到期时间，其他线程无限等待，减少不必要的定时唤醒。

---

## 七、SynchronousQueue

**无容量**的阻塞队列，每个 put 必须等待一个 take（反之亦然）。

```java
// 纯"传递"队列
SynchronousQueue<String> queue = new SynchronousQueue<>();

// 线程A
queue.put("data");  // 阻塞直到有人 take

// 线程B
String data = queue.take();  // 阻塞直到有人 put
```

- 适合**直接传递**场景，不经中间存储
- CachedThreadPool 使用 SynchronousQueue

---

## 八、线程池中的阻塞队列选择

| 线程池 | 使用队列 | 说明 |
|--------|---------|------|
| `FixedThreadPool` | LinkedBlockingQueue | 无界队列，队列无限堆积 |
| `SingleThreadExecutor` | LinkedBlockingQueue | 同上 |
| `CachedThreadPool` | SynchronousQueue | 直接传递，不存储 |
| `ScheduledThreadPool` | DelayedWorkQueue | 基于堆的延迟队列 |

---

## 九、选择阻塞队列的策略

| 维度 | 推荐 |
|------|------|
| **需要排序** | PriorityBlockingQueue |
| **需要延迟** | DelayQueue |
| **直接传递** | SynchronousQueue |
| **固定容量** | ArrayBlockingQueue |
| **高并发吞吐** | LinkedBlockingQueue（两把锁） |
| **无界队列** | LinkedBlockingQueue（不设容量） |
| **双端操作** | LinkedBlockingDeque |

> ⚠️ 生产环境建议**设置队列容量**，防止无界队列导致 OOM。

---

## 十、总结

| 队列 | 结构 | 锁 | 适用 |
|------|------|------|------|
| ArrayBlockingQueue | 数组 | 1锁 | 容量固定 |
| LinkedBlockingQueue | 链表 | 2锁分离 | 高并发 |
| PriorityBlockingQueue | 堆 | 1锁 | 优先级 |
| DelayQueue | 堆+优先 | 1锁 | 延迟任务 |
| SynchronousQueue | 无 | CAS | 直接传递 |
