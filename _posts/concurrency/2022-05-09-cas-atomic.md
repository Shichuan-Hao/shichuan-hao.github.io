---
title: 深入理解CAS&Atomic原子操作类详解
categories: [Java, 并发编程]
tags: [CAS, 原子操作, AtomicInteger, Unsafe, ABA问题, LongAdder, Striped64]
author: hsc
date: 2022-05-09 00:00:00 +0800
description: 深入讲解CAS原理、Unsafe类、Atomic原子操作类（AtomicInteger、LongAdder、AtomicStampedReference等）、ABA问题解决方案。
source: 有道云笔记 / https://note.youdao.com/s/2Z8aM6jL
---

## 一、什么是CAS

### 1.1 概念

**CAS（Compare And Swap，比较并交换）** 是一种无锁算法。在不使用锁（没有线程被阻塞）的情况下实现多线程之间的变量同步。

### 1.2 CAS算法过程

包含三个参数：
- **V** — 要更新的变量（内存值）
- **E** — 期望的值（旧值）
- **N** — 要写入的新值

执行逻辑：**仅当 V 的值等于 E 时，才将 V 的值设置为 N**

- 相等 → 更新 V = N，返回 true
- 不相等 → 说明其他线程已更新，不更新，返回 false

```
线程 ①                     线程 ②
if V == E:                 if V == E:
    V = N                      V = N
else:                      else:
    放弃重试                    放弃重试
```

### 1.3 为什么多线程对共享变量的操作不安全？

```java
// count++ 在 CPU 中分 3 步执行
// 1. 从内存中读 count 到寄存器
// 2. 寄存器中 count + 1
// 3. 写回内存
// 多个线程读到了相同的 count 值，分别 +1 → 少加了一次
```

CAS 可以保证 count++ 的原子性 —— 但需要自旋（循环重试）。

### 1.4 CAS 的特点

- **轻量级** — 不需要切换线程
- **CPU 层面支持** — 是 CPU 原子指令（cmpxchg），比用锁更高效
- **汇编指令** — `lock cmpxchg` 指令
- **短小精悍** — 适用于并发量不大、锁竞争不激烈的场景

### 1.5 CAS 底层实现

外部代码 → `Unsafe` 类 → `native` 方法 → CPU 的 `cmpxchg` 指令。

```java
// AtomicInteger#compareAndSet
public final boolean compareAndSet(int expect, int update) {
    return unsafe.compareAndSwapInt(this, valueOffset, expect, update);
}
```

Unsafe 是核心，它提供了三种 CAS 方法：`compareAndSwapObject`、`compareAndSwapInt`、`compareAndSwapLong`。

```java
// 基于 Unsafe 实现自旋
public class SpinLock {
    private AtomicReference<Thread> sign = new AtomicReference<>();

    public void lock() {
        Thread current = Thread.currentThread();
        while (!sign.compareAndSet(null, current)) {
            // 自旋等待
        }
    }

    public void unlock() {
        Thread current = Thread.currentThread();
        sign.compareAndSet(current, null);
    }
}
```

---

## 二、Unsafe 类

Unsafe 是 CAS 的核心类，存在 `sun.misc` 包中。由于 Java 方法无法直接访问底层系统，需要通过本地（native）方法访问。

| 能力 | 说明 |
|------|------|
| 内存操作 | 分配/释放/读写堆外内存 |
| 操作对象/属性 | 绕过构造器创建对象、操控对象属性 |
| 数组操作 | 获取数组元素偏移量 |
| **CAS 操作** | 提供 `compareAndSwapInt` 等原子操作 |
| 线程调度 | `park`、`unpark` |
| 内存屏障 | `loadFence`、`storeFence`、`fullFence` |

> 不推荐在应用程序中使用 Unsafe，推荐封装好后使用。

---

## 三、Atomic 原子操作类

共有 13 个原子操作类，可按分组记忆：

### 3.1 原子更新基本类型（3个）

| 类 | 说明 |
|------|------|
| `AtomicBoolean` | 原子更新布尔类型 |
| `AtomicInteger` | 原子更新整型 |
| `AtomicLong` | 原子更新长整型 |

**常用方法：**

| 方法 | 说明 |
|------|------|
| `int addAndGet(int delta)` | 以原子方式相加，返回新值 |
| `boolean compareAndSet(int expect, int update)` | CAS 操作 |
| `int getAndIncrement()` | i++ |
| `int incrementAndGet()` | ++i |
| `int getAndSet(int newValue)` | 返回旧值，设为新值 |
| `int getAndAdd(int delta)` | 返回旧值，累加后设新值 |
| `void lazySet(int newValue)` | 最终会设置成功（延迟写） |

```java
// AtomicInteger 使用示例
public class AtomicIntegerDemo {
    private static AtomicInteger sum = new AtomicInteger(0);

    public static void inCreate() {
        sum.getAndIncrement();
    }

    public static void main(String[] args) {
        for (int i = 0; i < 10; i++) {
            new Thread(() -> {
                for (int j = 0; j < 100; j++) {
                    inCreate();
                    try { Thread.sleep(200); } catch (InterruptedException e) {}
                }
            }).start();
        }
    }
}
```

#### AtomicInteger 源码分析

```java
// AtomicInteger 底层依赖 Unsafe#compareAndSwapInt
public class AtomicInteger extends Number implements Serializable {
    private static final Unsafe unsafe = Unsafe.getUnsafe();
    private static final long valueOffset;
    private volatile int value;

    static {
        try {
            // 拿到 value 在 AtomicInteger 对象中的偏移量
            valueOffset = unsafe.objectFieldOffset(
                AtomicInteger.class.getDeclaredField("value"));
        } catch (Exception ex) { throw new Error(ex); }
    }

    public final int getAndIncrement() {
        return unsafe.getAndAddInt(this, valueOffset, 1);
    }
}

// Unsafe#getAndAddInt
public final int getAndAddInt(Object o, long offset, int delta) {
    int v;
    do {
        v = getIntVolatile(o, offset);     // 获取当前值
        // compareAndSwapInt: (对象, 偏移量, 期望值v, 新值v+delta)
    } while (!compareAndSwapInt(o, offset, v, v + delta));
    return v;
}
```

### 3.2 原子更新数组（3个）

| 类 | 说明 |
|------|------|
| `AtomicIntegerArray` | 原子更新整型数组元素 |
| `AtomicLongArray` | 原子更新长整型数组元素 |
| `AtomicReferenceArray` | 原子更新引用类型数组元素 |

### 3.3 原子更新引用类型（3个）

```java
// AtomicReference 使用示例
class User {
    private String name;
    public volatile int age;
    // getters/setters...
}

AtomicReference<User> userRef = new AtomicReference<>();
userRef.set(new User("张三", 15));
userRef.compareAndSet(oldUser, newUser);
```

### 3.4 原子更新字段（3个）

| 类 | 说明 |
|------|------|
| `AtomicIntegerFieldUpdater` | 原子更新整型字段 |
| `AtomicLongFieldUpdater` | 原子更新长整型字段 |
| `AtomicReferenceFieldUpdater` | 原子更新引用类型字段 |

**约束条件：**
1. 字段必须是 `volatile` 类型
2. 字段的描述类型与调用者的操作对象关系一致
3. 只能是实例变量，不能是类变量（不能加 static）
4. 只能是可修改变量（不能加 final）

### 3.5 新一代原子类（JDK 1.8）

| 类 | 说明 |
|------|------|
| `LongAdder` | 比 AtomicLong 更高的并发性能，适合 count++ 统计场景 |
| `DoubleAdder` | 对 LongAdder 的 double 封装 |
| `LongAccumulator` | 自定义聚合逻辑 |
| `DoubleAccumulator` | 自定义聚合逻辑的 double 版 |

#### LongAdder 原理

高并发场景下 `AtomicLong` 的单一 `value` 成为热点 → 大量 CAS 竞争 → 性能下降。

`LongAdder` 采用**空间换时间**策略：将单一热点 value 拆分成 Cell 数组，不同线程 CAS 到不同的 Cell，最终求和：

```
LongAdder
├── base（无竞争时使用）
└── cells[] → Cell[0], Cell[1], Cell[2]...
    └── 有竞争时，不同线程命中不同 Cell
```

**原理：**
1. 无竞争 → 直接 CAS 到 `base`（如同 AtomicLong）
2. 有竞争 → 创建 Cell 数组，每个线程 CAS 不同 Cell
3. `sum()` → 遍历 base + 所有 Cell 求和
4. **Striped64** 是 LongAdder 的父类，定义了 base、cells 等核心逻辑

**横向对比：**

| | AtomicLong | LongAdder |
|------|------|------|
| 原理 | CAS + 自旋 | 分段锁（空间换时间） |
| 适合场景 | 低竞争 | 高并发统计 |
| 递增 | `increment()` | `add(1)` |
| 求和 | `get()` | `sum()`（弱一致性） |

---

## 四、ABA 问题

### 4.1 什么是 ABA 问题

CAS 判断值没有变过，但实际上可能：
```
A → B → A  （值回到原来的A，但中间变化过）
```

**举例：** 小明账户余额100元，小偷偷走50元，又退回50元 → 余额仍是100，CAS 无法发现。

### 4.2 ABA 问题的解决方案

#### AtomicStampedReference（版本号）

```java
// 使用版本戳（类似乐观锁）
AtomicStampedReference<Integer> ref = 
    new AtomicStampedReference<>(100, 0);

int stamp = ref.getStamp();
ref.compareAndSet(100, 50, stamp, stamp + 1);  // 100→50, 版本0→1
```

#### AtomicMarkableReference（布尔标记）

适合只需要"是否被改过"的场景，不支持多重更新。

```java
AtomicMarkableReference<Integer> ref =
    new AtomicMarkableReference<>(100, false);

ref.compareAndSet(100, 50, false, true);
```

---

## 五、总结

| 主题 | 要点 |
|------|------|
| **CAS 概念** | Compare And Swap，无锁同步，CPU 指令 `lock cmpxchg` |
| **Unsafe 类** | Java 底层操作核心，CAS 方法、内存操作、线程调度 |
| **基本原子类** | `AtomicInteger`/`AtomicLong`/`AtomicBoolean`，基于 Unsafe + volatile |
| **数组原子类** | `AtomicIntegerArray`/`AtomicLongArray`/`AtomicReferenceArray` |
| **引用原子类** | `AtomicReference`/`AtomicStampedReference`/`AtomicMarkableReference` |
| **字段更新器** | `AtomicIntegerFieldUpdater` 等，字段需 volatile |
| **LongAdder** | JDK8 新增，分段 Cell 减少竞争，适合高并发统计 |
| **ABA 问题** | 用 `AtomicStampedReference`（版本号）解决 |
