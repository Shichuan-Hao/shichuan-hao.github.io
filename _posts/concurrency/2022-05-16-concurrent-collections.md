---
title: 并发容器（Map、List、Set）实战及其原理分析
categories: [Java, 并发编程]
tags: [并发容器, ConcurrentHashMap, CopyOnWriteArrayList, CopyOnWriteArraySet, ConcurrentLinkedQueue, ConcurrentSkipListMap, 源码分析]
author: hsc
date: 2022-05-16 00:00:00 +0800
description: 深入讲解并发容器实战与原理，涵盖ConcurrentHashMap（JDK7 vs JDK8）、CopyOnWriteArrayList/Set、ConcurrentLinkedQueue、ConcurrentSkipListMap等核心内容。
source: 有道云笔记 / cunlove.cn
---

# 并发容器（Map、List、Set）实战及其原理分析

---

## 一、同步容器 vs 并发容器

### 1.1 古老同步容器

`Vector`、`Hashtable`、`Collections.synchronizedXxx()` — 通过 `synchronized` 实现，并发度低。

```java
Map<String, Object> map = Collections.synchronizedMap(new HashMap<>());
List<String> list = Collections.synchronizedList(new ArrayList<>());
```

**问题：** 多线程下对容器迭代操作仍需要**客户端加锁**。

```java
// 不安全的迭代
for (String s : list) { ... }  // 并发修改可能抛 ConcurrentModificationException

// 需要手动加锁
synchronized (list) {
    for (String s : list) { ... }
}
```

### 1.2 并发容器概述

| 容器 | 对应单线程版 | 并发原理 |
|------|------------|---------|
| ConcurrentHashMap | HashMap | JDK7:分段锁 / JDK8:CAS+synchronized |
| CopyOnWriteArrayList | ArrayList | 写时复制 |
| CopyOnWriteArraySet | HashSet | 基于 CopyOnWriteArrayList |
| ConcurrentLinkedQueue | LinkedList | CAS 无锁算法 |
| ConcurrentSkipListMap | TreeMap | 跳表 + CAS |
| ConcurrentSkipListSet | TreeSet | 基于 ConcurrentSkipListMap |

---

## 二、ConcurrentHashMap

> 面试高频：JDK7 和 JDK8 的 ConcurrentHashMap 差异。

### 2.1 JDK 7 — 分段锁（Segment）

```
ConcurrentHashMap
├── Segment[0] → HashEntry[] → HashEntry → HashEntry → ...
├── Segment[1] → HashEntry[] → HashEntry → ...
├── ...
└── Segment[N] → HashEntry[] → ...
```

- 默认 **16 个 Segment**（并发度 16）
- Segment 继承 ReentrantLock，锁粒度更细
- put/get 时先 hash 定位到 Segment，再在 Segment 内操作

**缺点：** Segment 数量固定，无法动态扩容。

### 2.2 JDK 8 — CAS + synchronized

```
ConcurrentHashMap
├── Node<K,V>[] table
├── 链表（拉链法）
├── 红黑树（链表 ≥ 8 且 数组长度 ≥ 64 时树化）
└── 没有 Segment 层，直接对 Node 操作
```

**put 流程：**

```java
final V putVal(K key, V value, boolean onlyIfAbsent) {
    for (Node<K,V>[] tab = table;;) {  // 自旋
        // 1. table 为空 → 初始化（CAS 保证只有一个线程初始化）
        if (tab == null) {
            initTable();  // sizeCtl CAS
            continue;
        }
        // 2. 桶位置为空 → CAS 直接插入，无锁
        if ((f = tabAt(tab, i = (n-1) & hash)) == null) {
            if (casTabAt(tab, i, null, new Node<K,V>(...)))
                break;
        }
        // 3. 正在扩容 → 协助扩容
        else if (hash == MOVED) {
            helpTransfer(tab, f);
        }
        // 4. 桶位置不空 → synchronized 锁住头节点，插入链表或树
        else {
            synchronized (f) {
                // 遍历链表/树，插入或更新
            }
        }
    }
}
```

### 2.3 关键设计点

| 设计 | 说明 |
|------|------|
| **CAS 插入** | 桶为空时 CAS 无锁插入 |
| **synchronized 缩小粒度** | 仅锁 table[i] 的头节点 |
| **红黑树** | 链表 ≥ 8 且数组 ≥ 64 时树化，提高查询效率 |
| **多线程扩容** | `transfer()` 支持多个线程并发迁移数据 |
| **sizeCtl** | 多用途变量：初始化(-1)、阈值(threshold)、扩容中(负数) |

### 2.4 JDK7 vs JDK8 总结

| 对比 | JDK 7 | JDK 8 |
|------|------|------|
| **实现** | Segment 分段锁（ReentrantLock） | CAS + synchronized + 红黑树 |
| **并发度** | 固定 16 Segment | 数组长度（更细粒度） |
| **hash冲突** | 链表 | 链表 → 红黑树 |
| **查询复杂度** | O(n) 链表 | O(log n) 红黑树 |
| **size()** | 计算 3 次取一致值 | `baseCount` + `CounterCell` 数组 |

### 2.5 为什么不用 HashTable？

HashTable 所有方法加 `synchronized`，同一时刻只能一个线程访问 → 并发度极低。

---

## 三、CopyOnWriteArrayList

### 3.1 读写分离

- **读**：无锁，直接读原数组
- **写**：`ReentrantLock` 加锁，复制新数组 + 修改 + 替换引用

```java
// add 源码
public boolean add(E e) {
    final ReentrantLock lock = this.lock;
    lock.lock();
    try {
        Object[] elements = getArray();
        int len = elements.length;
        Object[] newElements = Arrays.copyOf(elements, len + 1);
        newElements[len] = e;
        setArray(newElements);  // 原子替换引用
        return true;
    } finally {
        lock.unlock();
    }
}

// get 源码（无锁）
public E get(int index) {
    return get(getArray(), index);
}
```

### 3.2 特点

| 优点 | 缺点 |
|------|------|
| 读操作无锁，性能极高 | 写操作复制整个数组，内存开销大 |
| 迭代安全，不抛 ConcurrentModificationException | 读的是"快照"，弱一致性 |
| 实现简单 | 写多时不适合 |

> ⚠️ **适用场景：读多写少**。

### 3.3 CopyOnWriteArraySet

底层基于 `CopyOnWriteArrayList`，通过 `addIfAbsent` 去重：

```java
public boolean add(E e) {
    return al.addIfAbsent(e);
}
```

---

## 四、ConcurrentLinkedQueue

**无界非阻塞队列**，基于 CAS + 链表实现。使用 Michael-Scott 算法。

```java
// offer 入队
public boolean offer(E e) {
    final Node<E> newNode = new Node<>(e);
    for (Node<E> t = tail, p = t;;) {
        Node<E> q = p.next;
        if (q == null) {
            // CAS 设置新节点为尾节点的 next
            if (p.casNext(null, newNode)) {
                // 更新 tail（失败也无妨，由其他线程代劳）
                if (p != t) casTail(t, newNode);
                return true;
            }
        }
        // 自旋...
    }
}
```

**特点：** 完全无锁，CAS 驱动，高并发场景性能优异。

---

## 五、ConcurrentSkipListMap

基于**跳表（SkipList）**实现的并发有序 Map，Key 有序。

```
Level 2: 1 ─────────→ 7 ─────────→ 9
Level 1: 1 ──→ 5 ──→ 7 ──→ 8 ──→ 9
Level 0: 1 → 3 → 5 → 7 → 8 → 9 → 10
```

- 查找、插入、删除均为 **O(log n)**
- 比红黑树更简单，天然支持并发
- 通过 CAS 和标记节点实现无锁/轻量级同步

```java
ConcurrentSkipListMap<Integer, String> map = new ConcurrentSkipListMap<>();
map.put(1, "A");
map.put(3, "C");
map.put(2, "B");
```

---

## 六、并发容器选择指南

| 场景 | 推荐容器 | 原因 |
|------|---------|------|
| 高并发 KV 存储 | ConcurrentHashMap | CAS+synchronized，细粒度锁 |
| 读多写少的 List | CopyOnWriteArrayList | 读无锁，写复制 |
| 读多写少的 Set | CopyOnWriteArraySet | 基于 COWArrayList |
| 并发队列 | ConcurrentLinkedQueue | CAS 无锁 |
| 有序并发 Map | ConcurrentSkipListMap | 跳表，有序 |
| 阻塞队列 | LinkedBlockingQueue 等 | 见阻塞队列章节 |

---

## 七、总结

| 容器 | 实现原理 | 适用场景 |
|------|---------|---------|
| ConcurrentHashMap | CAS + synchronized + 红黑树 (JDK8) | 高并发 KV |
| CopyOnWriteArrayList | 写时复制 + ReentrantLock | 读多写少 |
| CopyOnWriteArraySet | 基于 COWArrayList | 读多写少的 Set |
| ConcurrentLinkedQueue | CAS 无锁 | 高并发队列 |
| ConcurrentSkipListMap | 跳表 + CAS | 有序并发 Map |
