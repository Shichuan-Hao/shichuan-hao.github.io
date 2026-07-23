---
title: 深入理解并发原子性、可见性、有序性与JMM内存模型
categories: [Java, 并发编程]
tags: [JMM, 内存模型, 原子性, 可见性, 有序性, happens-before, volatile, 指令重排, 内存屏障, CPU缓存]
author: hsc
date: 2022-05-20 00:00:00 +0800
description: 深入剖析Java内存模型(JMM)的三大特性：原子性、可见性、有序性，理解happens-before规则、volatile原理与内存屏障机制。
mindmap:
---

# 深入理解并发原子性、可见性、有序性与JMM内存模型

## 一、并发编程的三个核心问题

### 1.1 问题的来源

并发编程下的Bug往往源于三个层面：

| 层面 | 问题 | 根本原因 |
|------|------|----------|
| 硬件 | CPU缓存 | 可见性问题 |
| 编译器/CPU | 指令重排 | 有序性问题 |
| 操作系统 | 线程切换 | 原子性问题 |

### 1.2 三大核心问题

```
并发编程三大特性
├── 原子性（Atomicity）
│   └── 一个或多个操作不可分割
├── 可见性（Visibility）
│   └── 线程修改共享变量后，其他线程立即可见
└── 有序性（Ordering）
    └── 程序执行顺序与代码顺序一致
```

---

## 二、CPU缓存架构与缓存一致性

### 2.1 CPU多级缓存架构

```
CPU核心0              CPU核心1
┌─────────┐          ┌─────────┐
│ 寄存器   │          │ 寄存器   │
├─────────┤          ├─────────┤
│ L1 Cache │          │ L1 Cache │  ← 最接近CPU，极快
├─────────┤          ├─────────┤
│ L2 Cache │          │ L2 Cache │
└────┬─────┘          └────┬─────┘
     └──────────────────────┘
               │
          L3 Cache (共享)
               │
            内存 (RAM)
```

| 层级 | 访问延迟 | 容量 | 位置 |
|------|---------|------|------|
| 寄存器 | ~1ns | ~1KB | 核心内 |
| L1 Cache | ~2ns | 32-64KB | 核心独占 |
| L2 Cache | ~7ns | 256KB-512KB | 核心独占 |
| L3 Cache | ~15ns | 8-32MB | CPU共享 |
| 内存 | ~100ns | 数GB | 外部 |

### 2.2 缓存带来的可见性问题

```
线程A                线程B
  │                    │
  ▼                    ▼
x=1 (L1 Cache A)   y=1 (L1 Cache B)
  │                    │
  不同步！             不同步！
  │                    │
  ▼                    ▼
 main memory: x=0, y=0   ← 主内存还是旧值

线程A修改了x=1，但线程B的缓存中x可能还是0 → 可见性问题！
```

### 2.3 缓存一致性协议（MESI）

为了解决多核缓存一致性问题，CPU实现了**MESI协议**：

| 状态 | 全称 | 含义 |
|------|------|------|
| **M**odified | 已修改 | 数据仅在该核心缓存中，已被修改，与内存不一致 |
| **E**xclusive | 独占 | 数据仅在该核心缓存中，与内存一致 |
| **S**hared | 共享 | 数据在多核心缓存中，与内存一致 |
| **I**nvalid | 失效 | 缓存行无效 |

状态转换机制：
```
I → E: 读取时其他缓存中没有
I → S: 读取时其他缓存中有
E → M: 写入修改
S → M: 写入时通知其他缓存失效
M → S: 其他核心读取时写回内存
```

---

## 三、原子性（Atomicity）

### 3.1 什么是原子性

一个或多个操作，要么全部执行且不被中断，要么全不执行。

### 3.2 原子性问题的产生

```java
// 看似简单的 count++ 实际是三个操作
public void increment() {
    count++;  // 1.读取count  2.count+1  3.写回count
}
```

线程切换可能发生在任何一步之间，导致丢失更新。

### 3.3 保证原子性的方式

| 方式 | 原理 | 适用场景 |
|------|------|---------|
| `synchronized` | JVM锁，互斥 | 任何需要原子性的场景 |
| `Lock` | JDK显式锁 | 更灵活的锁控制 |
| `AtomicXXX` | CAS 无锁 | 简单计数/标记等 |
| `LongAdder` | 分段累加 | 高并发计数 |

```java
// 示例：AtomicInteger 保证原子性
AtomicInteger atomicCount = new AtomicInteger(0);
atomicCount.incrementAndGet();  // 原子操作

// LongAdder 高并发场景
LongAdder adder = new LongAdder();
adder.increment();  // 更高性能
```

---

## 四、可见性（Visibility）

### 4.1 什么是可见性

一个线程修改了共享变量，其他线程能**立即**看到修改后的值。

### 4.2 可见性问题的产生

```java
public class VisibilityDemo {
    private static boolean flag = false;
    
    public static void main(String[] args) {
        new Thread(() -> {
            while (!flag) {}  // 线程B可能永远不会退出！
            System.out.println("退出");
        }).start();
        
        Thread.sleep(1000);
        flag = true;  // 线程A修改flag，但线程B可能看不到
    }
}
```

线程A修改了 `flag = true`，但这个修改可能仅在A的缓存中，B仍然看到 `flag = false`。

### 4.3 保证可见性的方式

| 方式 | 原理 |
|------|------|
| `volatile` | 写操作立即刷新到主内存，读操作从主内存读取 |
| `synchronized` | 锁释放前将变量刷新到主内存 |
| `Lock` | 与synchronized类似 |
| `final` | 构造完成后对所有线程可见 |

### 4.4 volatile 写-读的内存语义

```
volatile 写：
1. 将当前缓存行的数据写回主内存
2. 使其他CPU缓存中的该数据失效（MESI）

volatile 读：
1. 直接从主内存读取最新值
```

---

## 五、有序性（Ordering）

### 5.1 什么是有序性

程序执行顺序与代码顺序一致。

### 5.2 指令重排

为了性能优化，编译器和CPU可能对指令进行重排序：

```java
// 原始代码
int a = 1;    // 1
int b = 2;    // 2
int c = a + b;// 3

// 可能被重排为
int b = 2;    // 2
int a = 1;    // 1
int c = a + b;// 3  (有依赖关系的不会重排)
```

### 5.3 指令重排的三种类型

| 类型 | 重排者 | 说明 |
|------|--------|------|
| 编译器重排 | JIT编译器 | 不改变单线程语义的前提下调整顺序 |
| 指令级并行重排 | CPU | 流水线优化，乱序执行 |
| 内存系统重排 | 缓存/缓冲区 | Store Buffer造成写入顺序不一致 |

### 5.4 重排导致的问题 — 经典 Double Check Locking

```java
public class Singleton {
    private static volatile Singleton instance;  // volatile 必不可少！
    
    public static Singleton getInstance() {
        if (instance == null) {                    // 第一次检查
            synchronized (Singleton.class) {
                if (instance == null) {            // 第二次检查
                    instance = new Singleton();    // 问题行！
                }
            }
        }
        return instance;
    }
}
```

`new Singleton()` 实际上分三步：
1. 分配内存空间
2. 初始化对象（调用构造函数）
3. 将引用指向内存地址

步骤2和3可能被重排（2↔3），导致其他线程拿到一个未初始化完成的对象。**volatile 禁止了这种重排**。

### 5.5 内存屏障（Memory Barrier）

| 屏障类型 | 指令 | 效果 |
|----------|------|------|
| LoadLoad | Load1; LoadLoad; Load2 | Load1 在 Load2 之前完成 |
| StoreStore | Store1; StoreStore; Store2 | Store1 在 Store2 之前完成 |
| LoadStore | Load1; LoadStore; Store2 | Load1 在 Store2 之前完成 |
| StoreLoad | Store1; StoreLoad; Load2 | Store1 在 Load2 之前完成（全能屏障） |

---

## 六、Java 内存模型（JMM）

### 6.1 JMM 抽象模型

```
 线程A          线程B
 ┌─────┐      ┌─────┐
 │工作内存│    │工作内存│    ← 线程私有，存储变量的拷贝
 └──┬──┘      └──┬──┘
    │   JMM控制   │
    ▼            ▼
 ┌─────────────────┐
 │     主内存       │    ← 共享，存储所有变量
 └─────────────────┘
```

> JMM 屏蔽了不同硬件和操作系统的内存访问差异，保证Java程序在各种平台下对内存的访问效果一致。

### 6.2 JMM 的三大特性

| 特性 | JMM 如何保证 |
|------|-------------|
| **原子性** | 通过 `synchronized`、`Lock`、`Atomic` 类保证 |
| **可见性** | 通过 `volatile`、`synchronized`、`final` 保证 |
| **有序性** | 通过 `volatile`、`synchronized`、happens-before 规则保证 |

### 6.3 happens-before 规则

happens-before 是 JMM 中定义的两个操作之间的偏序关系。如果A happens-before B，则A的结果对B可见。

| 规则 | 说明 |
|------|------|
| **程序顺序规则** | 单线程中，前面的操作 happens-before 后面的操作 |
| **监视器锁规则** | 解锁 happens-before 后续的加锁 |
| **volatile规则** | volatile 写 happens-before 后续的 volatile 读 |
| **传递性** | A hb B, B hb C → A hb C |
| **start规则** | `thread.start()` hb 线程中所有操作 |
| **join规则** | 线程中所有操作 hb `thread.join()` 返回 |
| **线程中断规则** | `interrupt()` hb 被中断线程检测到中断 |

### 6.4 happens-before 实践示例

```java
// 示例1：volatile的happens-before
volatile int a = 0;
int b = 0;

// 线程A
b = 1;          // 1
a = 1;          // 2 (volatile写)

// 线程B
if (a == 1) {   // 3 (volatile读)
    // 根据happens-before：2 hb 3 → b=1 对线程B可见
    System.out.println(b);  // 一定输出 1
}
```

```java
// 示例2：锁的happens-before
int x = 0;
synchronized (lock) {
    x = 10;          // 1
}                    // 2 (解锁)

// 另一个线程
synchronized (lock) {// 3 (加锁)
    // 2 hb 3 → x=10 可见
    System.out.println(x);  // 一定输出 10
}
```

---

## 七、volatile 深度解析

### 7.1 volatile 的语义

| 语义 | 说明 |
|------|------|
| **可见性** | 写操作立即刷新到主内存，读操作从主内存读取 |
| **有序性** | 禁止指令重排序（通过内存屏障） |
| **不保证原子性** | 复合操作（如 count++）仍然不安全 |

### 7.2 volatile 的内存屏障插入策略

```
volatile 写操作：
    StoreStore 屏障
    volatile 写
    StoreLoad 屏障

volatile 读操作：
    volatile 读
    LoadLoad 屏障
    LoadStore 屏障
```

### 7.3 volatile 使用场景

```java
// 场景1：状态标志
volatile boolean running = true;

// 场景2：DCL单例（前面已展示）

// 场景3：独立观察（读多写少）
volatile int temperature;
```

### 7.4 volatile 不适用场景

```java
// 错误：复合操作
volatile int count = 0;
count++;  // 不安全！读-改-写不是原子的

// 正确做法
AtomicInteger count = new AtomicInteger(0);
count.incrementAndGet();  // 安全
```

---

## 八、同步关键字的对比

### 8.1 volatile vs synchronized

| 特性 | volatile | synchronized |
|------|----------|--------------|
| 原子性 | ❌ 不保证 | ✅ 保证 |
| 可见性 | ✅ 保证 | ✅ 保证 |
| 有序性 | ✅ 部分禁止重排 | ✅ 保证 |
| 性能 | 读写开销小 | 有锁竞争开销 |
| 适用场景 | 状态标记、DCL | 复合操作、临界区 |

### 8.2 final 的语义

```java
// final字段在构造函数完成后，对所有线程可见
class FinalDemo {
    final int x;
    int y;
    
    FinalDemo() {
        x = 10;
        y = 20;
    }
    // 构造完成后：x 一定可见（final），y 不一定可见
}
```

---

## 九、总结

```
并发编程三大问题：
├── 原子性 → synchronized / Lock / Atomic
├── 可见性 → volatile / synchronized / final
└── 有序性 → volatile / synchronized / happens-before

JMM 通过 happens-before 规则定义了：
- 什么时候一个线程的写对另一个线程可见
- 保证了正确的同步程序的执行结果

硬件层面：
├── CPU 缓存 → 可见性问题 → MESI 协议解决
├── 指令重排 → 有序性问题 → 内存屏障解决
└── 线程切换 → 原子性问题 → 锁/CAS 解决
```

核心要点：
1. JMM 是语言级别的抽象，屏蔽了底层硬件差异
2. volatile 保证可见性和有序性，**不保证原子性**
3. happens-before 是判断并发安全的核心规则
4. DCL 单例必须使用 volatile 防止指令重排
5. 理解 MESI 协议有助于理解可见性问题的硬件根因
