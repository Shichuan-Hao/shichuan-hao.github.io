---
title: 并发锁机制之深入理解synchronized
categories: [Java, 并发编程]
tags: [synchronized, 锁升级, 偏向锁, 轻量级锁, 重量级锁, 对象头, Mark Word, Monitor, 锁消除, 锁粗化]
author: hsc
date: 2022-05-10 00:00:00 +0800
description: 深入剖析synchronized底层原理，涵盖对象头、Mark Word、Monitor机制、锁升级过程、锁消除与锁粗化等核心知识点。
source: 有道云笔记
---

# 并发锁机制之深入理解synchronized

> 主讲老师：Fox

---

## 一、synchronized 基础回顾

### 1.1 三种使用方式

| 方式 | 锁对象 |
|------|--------|
| 修饰实例方法 | 当前实例对象 `this` |
| 修饰静态方法 | 当前类的 Class 对象 |
| 修饰代码块 | `synchronized(obj)` 中的 obj 对象 |

### 1.2 字节码层面

```java
// 同步代码块 → monitorenter / monitorexit 指令
synchronized (obj) {
    // 业务逻辑
}

// 同步方法 → ACC_SYNCHRONIZED 标志
public synchronized void method() {
    // 方法上的同步由 JVM 方法常量池中 ACC_SYNCHRONIZED 标志控制
}
```

JDK 1.6 之前 synchronized 是重量级锁（直接使用 OS 的 Mutex Lock），效率低。

**JDK 1.6 之后**进行了大量优化：偏向锁、轻量级锁、适应性自旋、锁消除、锁粗化等，让 synchronized 性能与 ReentrantLock 相当。

---

## 二、synchronized 的底层原理

### 2.1 对象头布局

**HotSpot 虚拟机对象头（32位为例）：**

```
普通对象：
|----------------------------------------------|
| Mark Word (32bit)                            |
|----------------------------------------------|
| Klass Pointer (32bit, 压缩后)                 |
|----------------------------------------------|
| 实例数据                                      |
|----------------------------------------------|
| 对齐填充                                      |
|----------------------------------------------|

数组对象：
|----------------------------------------------|
| Mark Word (32bit)                            |
|----------------------------------------------|
| Klass Pointer (32bit, 压缩后)                 |
|----------------------------------------------|
| 数组长度                                      |
|----------------------------------------------|
| 数组数据                                      |
|----------------------------------------------|
```

### 2.2 Mark Word

Mark Word 存储对象自身的运行时数据，如哈希码、GC分代年龄、锁状态标志等。

**32位 Mark Word 结构：**

| 锁状态 | 25bit | 4bit | 1bit | 2bit |
|--------|-------|------|------|------|
| 无锁 | 对象 hashCode | 分代年龄 | 0 | 01 |
| 偏向锁 | 线程ID(23bit)+epoch(2bit) | 分代年龄 | 1 | 01 |
| 轻量级锁 | 指向栈中锁记录的指针(30bit) | | | 00 |
| 重量级锁 | 指向monitor的指针(30bit) | | | 10 |
| GC标记 | 空 | | | 11 |

**64位 Mark Word：**

| 锁状态 | 62bit | 2bit |
|--------|-------|------|
| 无锁 | unused:25 \| hashCode:31 \| cms_free:1 \| age:4 \| biased:1 | 01 |
| 偏向锁 | thread:54 \| epoch:2 \| cms_free:1 \| age:4 \| biased:1 | 01 |
| 轻量级锁 | ptr_to_lock_record:62 | 00 |
| 重量级锁 | ptr_to_heavyweight_monitor:62 | 10 |
| GC标记 | | 11 |

### 2.3 Monitor（管程/监视器）

每个 Java 对象都可以关联一个 Monitor。在 HotSpot 中，Monitor 由 `ObjectMonitor` 实现：

```cpp
ObjectMonitor() {
    _header       = NULL;
    _count        = 0;        // 重入次数
    _waiters      = 0;        // 等待线程数
    _recursions   = 0;        // 递归次数
    _object       = NULL;     // 关联的对象
    _owner        = NULL;     // 持有锁的线程
    _WaitSet      = NULL;     // wait() 的线程集合
    _EntryList    = NULL;     // 锁竞争线程队列（阻塞队列）
    _cxq          = NULL;     // 竞争队列（ContentionList）
}
```

**synchronized 加锁过程：**
1. 线程进入 `_cxq` 或 `_EntryList` 竞争
2. 通过 CAS 尝试获取 `_owner`
3. 获取成功 → `_count = 1`，执行业务
4. 获取失败 → 阻塞等待
5. 持有线程调用 `wait()` → 进入 `_WaitSet`，释放锁
6. `notify()` / `notifyAll()` → 从 `_WaitSet` 移到 `_EntryList`

---

## 三、锁升级过程（JDK 1.6+）

锁升级方向：**无锁 → 偏向锁 → 轻量级锁 → 重量级锁**（不可逆降级）。

```
无锁 (01) 
  ↓ 线程A第一次获取
偏向锁 (01) — 记录线程ID
  ↓ 另一个线程竞争但CAS成功
轻量级锁 (00) — 自旋
  ↓ 自旋超过阈值 / 竞争激烈
重量级锁 (10) — 操作系统互斥量
```

> **注意：** HotSpot 中锁只能升级不能降级（除了特殊STW时的批量撤销）。

### 3.1 偏向锁（Biased Locking）

**核心思想：** 锁总是由同一线程多次获取，让锁记录这个偏好线程的 ID。

**加锁流程：**
1. 检查 Mark Word 是否标记为偏向锁（biased_lock=1, lock=01）
2. 是 → 检查 ThreadID
   - 是当前线程 → 直接执行同步代码
   - 不是当前线程 → CAS 竞争偏向锁
3. 竞争成功 → ThreadID 改为自己
4. 竞争失败 → **偏向锁撤销** → 升级为轻量级锁

#### 偏向锁的撤销

- 到达安全点（Safepoint），暂停持有偏向锁的线程
- 检查偏向线程状态：
  - 已退出 → 撤销偏向锁，恢复到无锁
  - 仍在执行 → 升级为轻量级锁

**JDK 15+ 默认关闭偏向锁**（现代应用锁竞争普遍，偏向锁反而带来额外开销）。

#### JVM 偏向锁参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `-XX:+UseBiasedLocking` | JDK 15后废弃 | 启用偏向锁 |
| `-XX:BiasedLockingStartupDelay=0` | 4秒 | 偏向锁启动延迟，0为立即 |
| `-XX:-UseBiasedLocking` | | 禁用偏向锁 |

```java
// 查看 Java 对象头
// 引入 jol-core 依赖
import org.openjdk.jol.info.ClassLayout;

Object o = new Object();
System.out.println(ClassLayout.parseInstance(o).toPrintable());
```

### 3.2 轻量级锁（Lightweight Locking）

**核心思想：** 多线程错开竞争时，用 CAS 自旋代替 OS 互斥。

**加锁流程：**
1. 线程在栈帧中创建 **Lock Record**（锁记录）
2. 将对象的 Mark Word 复制到 Lock Record 中（Displaced Mark Word）
3. CAS 尝试将对象头的 Mark Word 替换为指向 Lock Record 的指针
4. 成功 → 获取轻量级锁
5. 失败 → 自旋重试

**解锁流程：**
1. 将 Displaced Mark Word 用 CAS 替换回对象头
2. 成功 → 解锁完成
3. 失败 → 说明有竞争，升级为重量级锁

### 3.3 重量级锁（Heavyweight Lock）

轻量级锁膨胀后 → 对象头的 Mark Word 指向 Monitor 对象。

- 未获取锁的线程 → 进入 Monitor 的 EntryList
- 持有锁的线程调用 `wait()` → 进入 WaitSet
- Monitor 由操作系统 Mutex Lock 实现
- 涉及**用户态 ↔ 内核态切换**，成本高

### 3.4 自适应自旋（Adaptive Spinning）

- 上次同一锁自旋成功 → 允许更长时间自旋
- 上次自旋失败 → 减少自旋甚至不旋
- 由 JVM 动态智能决策

---

## 四、锁消除与锁粗化

### 4.1 锁消除（Lock Elimination）

JIT 编译器分析发现**不会发生共享数据竞争** → 移除不必要的锁操作。

```java
// 锁消除示例
public String concat(String s1, String s2) {
    StringBuffer sb = new StringBuffer();  // 局部变量，无逃逸
    sb.append(s1);
    sb.append(s2);
    return sb.toString();  // 内部同步可被消除
}
```

**逃逸分析** 是锁消除的数据支撑：`-XX:+DoEscapeAnalysis`。

### 4.2 锁粗化（Lock Coarsening）

如果连续对同一对象反复加锁解锁 → JIT 将锁范围扩大（粗化）。

```java
// 锁粗化前
for (int i = 0; i < 100; i++) {
    synchronized (lock) {
        doSomething();  // 每次循环加锁解锁
    }
}

// JIT 优化后等价于
synchronized (lock) {
    for (int i = 0; i < 100; i++) {
        doSomething();  // 只加锁一次
    }
}
```

---

## 五、常见问题

### 5.1 锁升级能否降级？

HotSpot 中，锁升级后**不能降级**。但 STW 时的批量撤销（bulk revocation）可恢复无锁状态。

### 5.2 synchronized 与 Lock 对比

| 对比维度 | synchronized | Lock（ReentrantLock） |
|---------|-------------|----------------------|
| 本质 | Java 关键字，JVM 层面 | JDK 提供的接口 |
| 锁释放 | 自动释放 | 必须 `unlock()`，推荐 finally |
| 锁状态 | 无法判断 | `isLocked()` / `isHeldByCurrentThread()` |
| 锁类型 | 非公平（不可选） | 公平/非公平可选 |
| 中断 | 不可中断 | `lockInterruptibly()` 可中断 |
| 条件变量 | `wait/notify` | `Condition`（可多条件） |
| 性能 | JDK 6+ 优化后差异不大 | 特定场景更优 |
| 适用 | 大部分场景直接用 | 需要更多灵活性时 |

---

## 六、synchronized 工作流程总结

```
synchronized(obj) {
    // 业务逻辑
}
```

1. **线程检查** Monitor 的 `_owner`
2. 无 owner → CAS 设为当前线程 → 获取锁
3. 有 owner → 检查 `_recursions`（可重入）
   - 同一线程 → `_recursions++`，可重入
   - 不同线程 → 进入 EntryList 竞争队列，阻塞
4. 退出 synchronized → `_recursions--`
   - `_recursions == 0` → 释放锁，唤醒 EntryList 中的线程

---

## 七、总结

| 主题 | 要点 |
|------|------|
| **对象头** | Mark Word 存储锁状态、GC信息、hashCode |
| **Monitor** | `_owner`/`_EntryList`/`_WaitSet`，OS Mutex Lock |
| **偏向锁** | 记录线程ID，单线程重复获取，JDK15+默认关闭 |
| **轻量级锁** | CAS自旋 + Lock Record，错开竞争场景 |
| **重量级锁** | Monitor，OS 互斥量，阻塞队列 |
| **自适应自旋** | 根据历史动态调整自旋次数 |
| **锁消除** | 逃逸分析 + 消除无竞争锁 |
| **锁粗化** | 连续加锁解锁合并为一次 |
| **不可降级** | 锁只能升级不能降级（除了批量撤销） |
