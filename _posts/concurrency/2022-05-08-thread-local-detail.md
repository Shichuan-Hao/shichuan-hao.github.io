---
title: 导致JVM内存泄露的ThreadLocal详解
categories: [Java, 并发编程]
tags: [ThreadLocal, 内存泄漏, ThreadLocalMap, 弱引用, 源码分析]
author: hsc
date: 2022-05-08 00:00:00 +0800
description: 深入拆解ThreadLocal原理、源码、内存泄漏问题及解决方案，涵盖ThreadLocalMap结构、弱引用、哈希冲突等内容。
---

## 一、ThreadLocal 介绍

### 1.1 什么是 ThreadLocal

Java官方文档中的描述：**ThreadLocal 类用来提供线程内部的局部变量。**这种变量在多线程环境下访问（通过 `get` 和 `set` 方法访问）时能保证各个线程的变量相对独立于其他线程内的变量。ThreadLocal 实例通常来说都是 `private static` 类型的，用于关联线程和线程上下文。

**三大特性：**

| 特性 | 说明 |
|------|------|
| 线程安全 | 在多线程并发的场景下保证线程安全 |
| 传递数据 | 在同一线程、不同组件中传递公共变量 |
| 线程隔离 | 每个线程的变量都是独立的，不会互相影响 |

### 1.2 基本使用

#### 常用方法

| 方法 | 描述 |
|------|------|
| `ThreadLocal()` | 创建 ThreadLocal 对象 |
| `public void set(T value)` | 设置当前线程绑定的局部变量 |
| `public T get()` | 获取当前线程绑定的局部变量 |
| `public void remove()` | 移除当前线程绑定的局部变量 |

#### 使用案例

**问题场景（不使用 ThreadLocal）：**

```java
public class ThreadLocalDemo {
    private String content;

    private String getContent() {
        return content;
    }

    private void setContent(String content) {
        this.content = content;
    }

    public static void main(String[] args) {
        ThreadLocalDemo demo = new ThreadLocalDemo();
        for (int i = 0; i < 5; i++) {
            Thread thread = new Thread(new Runnable() {
                @Override
                public void run() {
                    demo.setContent(Thread.currentThread().getName() + "的数据");
                    System.out.println(Thread.currentThread().getName() + "--->" 
                        + demo.getContent());
                }
            });
            thread.setName("线程" + i);
            thread.start();
        }
    }
}
```

输出（数据混乱）：

```
线程0--->线程1的数据
线程2--->线程2的数据
线程1--->线程1的数据
线程4--->线程4的数据
线程3--->线程3的数据
```

多个线程访问同一个变量时，线程间的数据没有隔离，出现异常。

**使用 ThreadLocal 解决：**

```java
public class ThreadLocalDemo2 {
    private static ThreadLocal<String> threadLocal = new ThreadLocal<>();

    private String getContent() {
        return threadLocal.get();
    }

    private void setContent(String content) {
        threadLocal.set(content);
    }

    public static void main(String[] args) {
        ThreadLocalDemo2 demo = new ThreadLocalDemo2();
        for (int i = 0; i < 5; i++) {
            Thread thread = new Thread(new Runnable() {
                @Override
                public void run() {
                    demo.setContent(Thread.currentThread().getName() + "的数据");
                    System.out.println(Thread.currentThread().getName() + "--->" 
                        + demo.getContent());
                }
            });
            thread.setName("线程" + i);
            thread.start();
        }
    }
}
```

输出（数据隔离）：

```
线程0--->线程0的数据
线程4--->线程4的数据
线程1--->线程1的数据
线程3--->线程3的数据
线程2--->线程2的数据
```

### 1.3 ThreadLocal 与 synchronized 的区别

| 对比维度 | synchronized | ThreadLocal |
|---------|-------------|-------------|
| **原理** | "以时间换空间"，只提供一份变量，不同线程排队访问 | "以空间换时间"，为每个线程提供一份变量的副本 |
| **侧重点** | 多线程之间访问资源的同步 | 多线程中让每个线程之间的数据相互隔离 |

> 虽然 ThreadLocal 和 synchronized 都能解决问题，但在某些场景下使用 ThreadLocal 更为合适，因为这样可以使程序拥有更高的并发性。

### 1.4 ThreadLocal 的优势

1. **传递数据** — 保存每个线程绑定的数据，在需要的地方可以直接获取，避免参数直接传递带来的代码耦合问题
2. **线程隔离** — 各线程之间的数据相互隔离却又具备并发性，避免同步方式带来的性能损失

### 1.5 ThreadLocal 在 Spring 事务中的应用

Spring 的事务就借助了 ThreadLocal 类。Spring 会从数据库连接池中获得一个 connection，然后把 connection 放进 ThreadLocal 中，也就和线程绑定了。事务需要提交或者回滚，只要从 ThreadLocal 中拿到 connection 进行操作。

**为何 Spring 的事务要借助 ThreadLocal 类？**

以 JDBC 为例，正常的事务代码：

```java
dbc = new DataBaseConnection();     // 第1行
Connection con = dbc.getConnection(); // 第2行
con.setAutoCommit(false);            // 第3行
con.executeUpdate(...);              // 第4行
con.executeUpdate(...);              // 第5行
con.executeUpdate(...);              // 第6行
con.commit();                        // 第7行
```

可以分成三个部分：
- **事务准备阶段：** 第1～3行
- **业务处理阶段：** 第4～6行
- **事务提交阶段：** 第7行

不管开启事务还是执行具体的 SQL，都需要一个具体的**数据库连接**。

问题：Service 调用多个 DAO，如何让三个 DAO 使用**同一个**数据库连接？如果不使用 ThreadLocal，就必须为每个 DAO 显式传递数据库连接——这显然不合适。

Web 容器中，每个完整的请求周期会由一个线程来处理。因此，将数据库连接放入 ThreadLocal 中，当前线程执行时直接从 ThreadLocal 获取即可，实现了**跨层次的隐式参数共享**。结合 Spring 的 IOC 和 AOP，完美解决了这个问题。

---

## 二、ThreadLocal 的内部结构

### 2.1 常见的误解

如果不看源码，可能会猜测 ThreadLocal 是这样设计的：

> 每个 ThreadLocal 都创建一个 Map，用**线程作为 key**，局部变量作为 value。

这是最简单的设计，JDK 早期确实是这样做的，但**现在已经不是了**。

### 2.2 现在的设计（JDK 8）

JDK 优化后的设计：**每个 Thread 维护一个 `ThreadLocalMap`，Map 的 key 是 `ThreadLocal` 实例本身，value 才是要存储的值。**

```
Thread → ThreadLocalMap → Entry(ThreadLocal, value)
```

具体过程：

1. 每个 Thread 线程内部都有一个 Map（ThreadLocalMap）
2. Map 里面存储 ThreadLocal 对象（key）和线程的变量副本（value）
3. Thread 内部的 Map 由 ThreadLocal 维护，由 ThreadLocal 负责向 map 获取和设置线程的变量值
4. 不同线程每次获取副本值时，别的线程不能获取到当前线程的副本值，形成副本隔离

### 2.3 这样设计的好处

| 优势 | 说明 |
|------|------|
| **Entry 数量减少** | 存储数量由 ThreadLocal 数量决定（而非 Thread 数量），实际中 ThreadLocal 数量通常少于 Thread 数量 |
| **内存自动回收** | 当 Thread 销毁之后，对应的 ThreadLocalMap 也随之销毁，减少内存使用 |

---

## 三、ThreadLocal 的核心方法源码

除构造方法外，ThreadLocal 对外暴露以下 4 个方法：

| 方法 | 描述 |
|------|------|
| `protected T initialValue()` | 返回当前线程局部变量的初始值 |
| `public void set(T value)` | 设置当前线程绑定的局部变量 |
| `public T get()` | 获取当前线程绑定的局部变量 |
| `public void remove()` | 移除当前线程绑定的局部变量 |

### 3.1 set 方法

#### 源码（含中文注释）

```java
/**
 * 设置当前线程对应的ThreadLocal的值
 * @param value 将要保存在当前线程对应的ThreadLocal的值
 */
public void set(T value) {
    // 获取当前线程对象
    Thread t = Thread.currentThread();
    // 获取此线程对象中维护的ThreadLocalMap对象
    ThreadLocalMap map = getMap(t);
    // 判断map是否存在
    if (map != null)
        // 存在则调用map.set设置此实体entry
        map.set(this, value);
    else
        // 1）当前线程Thread 不存在ThreadLocalMap对象
        // 2）则调用createMap进行ThreadLocalMap对象的初始化
        // 3）并将 t(当前线程)和value(t对应的值)作为第一个entry存放至ThreadLocalMap中
        createMap(t, value);
}

/**
 * 获取当前线程Thread对应维护的ThreadLocalMap
 * @param t the current thread 当前线程
 * @return the map 对应维护的ThreadLocalMap
 */
ThreadLocalMap getMap(Thread t) {
    return t.threadLocals;
}

/**
 * 创建当前线程Thread对应维护的ThreadLocalMap
 * @param t 当前线程
 * @param firstValue 存放到map中第一个entry的值
 */
void createMap(Thread t, T firstValue) {
    // 这里的this是调用此方法的threadLocal
    t.threadLocals = new ThreadLocalMap(this, firstValue);
}
```

#### 执行流程

1. 首先获取当前线程，并根据当前线程获取一个 Map
2. 如果 Map 不为空 → 将参数设置到 Map 中（当前 ThreadLocal 的引用作为 key）
3. 如果 Map 为空 → 给该线程创建 Map，并设置初始值

### 3.2 get 方法

#### 源码（含中文注释）

```java
/**
 * 返回当前线程中保存ThreadLocal的值
 * 如果当前线程没有此ThreadLocal变量，
 * 则它会通过调用initialValue方法进行初始化值
 * @return 返回当前线程对应此ThreadLocal的值
 */
public T get() {
    // 获取当前线程对象
    Thread t = Thread.currentThread();
    // 获取此线程对象中维护的ThreadLocalMap对象
    ThreadLocalMap map = getMap(t);
    // 如果此map存在
    if (map != null) {
        // 以当前的ThreadLocal为key，调用getEntry获取对应的存储实体e
        ThreadLocalMap.Entry e = map.getEntry(this);
        // 对e进行判空
        if (e != null) {
            @SuppressWarnings("unchecked")
            // 获取存储实体e对应的value值
            T result = (T) e.value;
            return result;
        }
    }
    /*
     * 初始化：有两种情况有执行当前代码
     * 第一种情况: map不存在，表示此线程没有维护的ThreadLocalMap对象
     * 第二种情况: map存在, 但是没有与当前ThreadLocal关联的entry
     */
    return setInitialValue();
}

/**
 * 初始化
 * @return the initial value 初始化后的值
 */
private T setInitialValue() {
    // 调用initialValue获取初始化的值（此方法可以被子类重写, 默认返回null）
    T value = initialValue();
    // 获取当前线程对象
    Thread t = Thread.currentThread();
    // 获取此线程对象中维护的ThreadLocalMap对象
    ThreadLocalMap map = getMap(t);
    if (map != null)
        map.set(this, value);
    else
        createMap(t, value);
    return value;
}
```

#### 执行流程

1. 获取当前线程 → 获取 Map
2. Map 不为空 → 以 ThreadLocal 引用为 key 获取 Entry
3. Entry 不为 null → 返回 `e.value`
4. Map 为空 或 Entry 为空 → 通过 `initialValue()` 获取初始值，创建新 Map

> **总结：** 先获取当前线程的 ThreadLocalMap 变量，如果存在则返回值，不存在则创建并返回初始值。

### 3.3 remove 方法

```java
/**
 * 删除当前线程中保存的ThreadLocal对应的实体entry
 */
public void remove() {
    // 获取当前线程对象中维护的ThreadLocalMap对象
    ThreadLocalMap m = getMap(Thread.currentThread());
    // 如果此map存在
    if (m != null)
        // 存在则调用map.remove，以当前ThreadLocal为key删除对应的实体entry
        m.remove(this);
}
```

**执行流程：**
1. 获取当前线程，根据当前线程获取 Map
2. Map 不为空 → 移除当前 ThreadLocal 对象对应的 entry

### 3.4 initialValue 方法

```java
/**
 * 返回当前线程对应的ThreadLocal的初始值
 *
 * 此方法的第一次调用发生在，当线程通过get方法访问此线程的ThreadLocal值时
 * 除非线程先调用了set方法，在这种情况下，initialValue才不会被这个线程调用。
 * 通常情况下，每个线程最多调用一次这个方法。
 *
 * 这个方法仅仅简单的返回null;
 * 如果程序员想ThreadLocal线程局部变量有一个除null以外的初始值，
 * 必须通过子类继承ThreadLocal的方式去重写此方法
 * 通常, 可以通过匿名内部类的方式实现
 *
 * @return 当前ThreadLocal的初始值
 */
protected T initialValue() {
    return null;
}
```

**三个要点：**
1. **延迟调用** — `set` 未调用而先调用了 `get` 时才执行，且仅执行1次
2. **默认返回 null**
3. **可通过子类继承重写**来设置除 null 之外的初始值

```java
// 为ThreadLocal设置初始值的写法
private static ThreadLocal<String> threadLocal = new ThreadLocal<String>() {
    @Override
    protected String initialValue() {
        return "默认值";
    }
};
```

---

## 四、ThreadLocalMap 源码分析

ThreadLocal 的操作实际上是围绕 `ThreadLocalMap` 展开的。它是 `ThreadLocal` 的内部类，没有实现 Map 接口，以独立方式实现 Map 功能。

### 4.1 基本结构

#### 成员变量

```java
/**
 * 初始容量 —— 必须是2的整次幂
 */
private static final int INITIAL_CAPACITY = 16;

/**
 * 存放数据的table，数组长度必须是2的整次幂
 */
private Entry[] table;

/**
 * 数组里面entrys的个数，用于判断table当前使用量是否超过阈值
 */
private int size = 0;

/**
 * 进行扩容的阈值，表使用量大于它的时候进行扩容
 */
private int threshold; // Default to 0
```

与 HashMap 类似：
- `INITIAL_CAPACITY` = 初始容量（16）
- `table` = Entry 数组，存储数据
- `size` = 表中的存储数目
- `threshold` = 扩容阈值

#### 存储结构 — Entry

```java
/*
 * Entry继承WeakReference，并且用ThreadLocal作为key.
 * 如果key为null(entry.get() == null)，意味着key不再被引用，
 * 因此这时候entry也可以从table中清除。
 */
static class Entry extends WeakReference<ThreadLocal<?>> {
    /** The value associated with this ThreadLocal. */
    Object value;

    Entry(ThreadLocal<?> k, Object v) {
        super(k);
        value = v;
    }
}
```

**关键点：**
- Entry 继承 `WeakReference`，key（ThreadLocal）是**弱引用**
- 目的是将 ThreadLocal 对象的生命周期和线程生命周期**解绑**

### 4.2 弱引用和内存泄漏

#### 概念回顾

| 概念 | 说明 |
|------|------|
| **Memory Overflow**（内存溢出） | 没有足够的内存提供给申请者使用 |
| **Memory Leak**（内存泄漏） | 动态分配的堆内存未释放/无法释放，堆积最终导致内存溢出 |
| **强引用** | 只要强引用指向一个对象，GC 就不会回收 |
| **弱引用**（WeakReference） | GC 一旦发现只具有弱引用的对象，无论内存是否充足，都会回收 |

#### 如果 key 使用强引用

```
threadLocal Ref → ThreadLocal (强引用)
                          ↑ (强引用)
Thread → ThreadLocalMap → Entry(key=ThreadLocal, value=obj)
```

- 业务代码中 `threadLocal Ref` 被回收后
- ThreadLocalMap 的 Entry **强引用**了 ThreadLocal → **ThreadLocal 无法被 GC 回收**
- 只要 CurrentThread 还在运行，`Thread → ThreadLocalMap → Entry` 强引用链存在 → Entry 不会被回收 → **Entry 内存泄漏**

#### 如果 key 使用弱引用（实际设计）

```
threadLocal Ref → ThreadLocal (强引用)
                          ↑ (弱引用)
Thread → ThreadLocalMap → Entry(key=ThreadLocal, value=obj)
```

- `threadLocal Ref` 被回收后 → ThreadLocal 只有弱引用 → **ThreadLocal 会被 GC 回收**，Entry.key = null
- 但仍有强引用链：`Thread → ThreadLocalMap → Entry → value`
- 这块 value 永远不会被访问到 → **value 内存泄漏**

#### 内存泄漏的真正原因

> ⚠️ **核心结论：ThreadLocal 内存泄漏的根源是** ThreadLocalMap 的生命周期跟 Thread 一样长，如果没有手动删除对应 key 就会导致内存泄漏。

**内存泄漏发生的两个前提：**
1. 没有手动删除这个 Entry
2. CurrentThread 依然运行

**避免内存泄漏的两种方式：**

| 方式 | 难度 |
|------|------|
| 使用完 ThreadLocal，调用 `remove()` 删除对应的 Entry | 简单可控 |
| 使用完 ThreadLocal，当前 Thread 也随之运行结束 | 线程池场景不可行 |

#### 为什么 key 使用弱引用？

虽然无论 key 用强引用还是弱引用都无法完全避免内存泄漏，**弱引用比强引用可以多一层保障：**

> 弱引用的 ThreadLocal 会被 GC 回收，对应的 value 在下一次调用 `set`/`get`/`remove` 时会被清除。

ThreadLocalMap 的 `set`/`getEntry` 方法中会对 `key == null`（即 ThreadLocal 已被回收）的情况进行判断，将 value 置为 null。

> 也就是说，**即使忘记调用 `remove()`，弱引用也比强引用多一次自动清理的机会。**

```java
// 线程池中使用ThreadLocal的正确姿势
ExecutorService es;
ThreadLocal tl;
es.execute(() -> {
    tl.set(obj);
    try {
        // 业务逻辑
    } finally {
        tl.remove();  // 必须手动清理！
    }
});
```

### 4.3 Hash 冲突的解决

ThreadLocalMap 使用**线性探测法**解决哈希冲突。

#### 构造方法

```java
/*
 * firstKey : 本ThreadLocal实例(this)
 * firstValue ： 要保存的线程本地变量
 */
ThreadLocalMap(ThreadLocal<?> firstKey, Object firstValue) {
    // 初始化table
    table = new ThreadLocal.ThreadLocalMap.Entry[INITIAL_CAPACITY];
    // 计算索引（重点！）
    int i = firstKey.threadLocalHashCode & (INITIAL_CAPACITY - 1);
    // 设置值
    table[i] = new ThreadLocal.ThreadLocalMap.Entry(firstKey, firstValue);
    size = 1;
    // 设置阈值
    setThreshold(INITIAL_CAPACITY);
}
```

**关于 `firstKey.threadLocalHashCode`：**

```java
private final int threadLocalHashCode = nextHashCode();

private static int nextHashCode() {
    return nextHashCode.getAndAdd(HASH_INCREMENT);
}

private static AtomicInteger nextHashCode = new AtomicInteger();

// 特殊的hash值 — 与斐波那契数列（黄金分割数）有关
private static final int HASH_INCREMENT = 0x61c88647;
```

`HASH_INCREMENT = 0x61c88647` 与黄金分割数有关，**目的是让哈希码均匀分布在 2^n 的数组里**，尽量避免 hash 冲突。

**关于 `& (INITIAL_CAPACITY - 1)`：** 等价于取模运算 `hashCode % size` 的高效实现。这也是数组长度必须是 2 的整次幂的原因。

#### set 方法源码

```java
private void set(ThreadLocal<?> key, Object value) {
    ThreadLocal.ThreadLocalMap.Entry[] tab = table;
    int len = tab.length;
    // 计算索引
    int i = key.threadLocalHashCode & (len - 1);
    /**
     * 使用线性探测法查找元素
     */
    for (ThreadLocal.ThreadLocalMap.Entry e = tab[i];
         e != null;
         e = tab[i = nextIndex(i, len)]) {
        ThreadLocal<?> k = e.get();
        // ThreadLocal对应的key存在，直接覆盖
        if (k == key) {
            e.value = value;
            return;
        }
        // key为null但value不为null → ThreadLocal已被回收 → 陈旧元素
        if (k == null) {
            replaceStaleEntry(key, value, i);  // 替换陈旧元素 + 垃圾清理
            return;
        }
    }

    // key不存在且没有陈旧元素 → 在空位置创建新Entry
    tab[i] = new Entry(key, value);
    int sz = ++size;
    /*
     * cleanSomeSlots清除e.get()==null的元素
     * 如果没清除任何entry, 且当前使用量达到阈值 → rehash
     */
    if (!cleanSomeSlots(i, sz) && sz >= threshold)
        rehash();
}

/**
 * 获取环形数组的下一个索引
 */
private static int nextIndex(int i, int len) {
    return ((i + 1 < len) ? i + 1 : 0);
}
```

#### 执行流程

1. 根据 key 计算索引 i，查找 i 位置的 Entry
2. Entry 存在且 key 相等 → 直接覆盖 value
3. Entry 存在但 key 为 null → 调用 `replaceStaleEntry` 更换陈旧 Entry
4. 循环探测直到遇到 null 位置 → 新建 Entry 插入，size + 1
5. 调用 `cleanSomeSlots` 清理 key 为 null 的 Entry
6. 如果 `size >= threshold` → 执行 `rehash()` 全表扫描清理

#### 线性探测法详解

```
table 看成一个环形数组：
table[0], table[1], ..., table[14], table[15], table[0], ...
```

- 当前 key 的 hash 值为 14
- `table[14]` 有值且 key 不同 → hash 冲突
- 探测 `14 + 1 = 15` → 如果 `table[15]` 还冲突
- 回到 `0`，取 `table[0]` → 以此类推，直到找到空位或匹配的 key

---

## 五、总结

| 主题 | 要点 |
|------|------|
| **ThreadLocal 作用** | 线程隔离 + 隐式参数传递，高并发场景下替代 synchronized |
| **内部结构** | 每个 Thread 持有 ThreadLocalMap，key 为 ThreadLocal 实例（弱引用），value 为变量 |
| **核心方法** | `set`/`get`/`remove`/`initialValue`，操作底层 ThreadLocalMap |
| **内存泄漏根源** | ThreadLocalMap 生命周期 = Thread 生命周期，**未手动 remove 导致** |
| **弱引用的意义** | 无法完全避免泄漏，但多一层自动清理的保障 |
| **正确使用姿势** | 线程池中务必在 `finally` 中调用 `remove()` |
| **Hash 冲突** | 线性探测法（环形数组），`HASH_INCREMENT = 0x61c88647` 基于黄金分割数均匀分散 |
| **Spring 应用** | Spring 事务通过 ThreadLocal 绑定 Connection，实现跨层隐式传递 |
