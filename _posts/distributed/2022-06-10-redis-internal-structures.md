---
layout: post
title: "Redis7底层数据结构深度解析：从redisObject到SkipList"
date: 2022-06-10
categories: [distributed]
tags: [Redis, 底层数据结构, SDS, SkipList, QuickList, ListPack, redisObject, 源码分析]
comments: true
---

> 作为 Java 程序员，研究 Redis 底层结构的目的只有一个：**面试**！体现你对 Redis 的理解深度。  
> 基于 Redis 7.2.5 源码。

---

## 一、整体理解Redis底层数据结构

### 1、Redis 数据在底层是什么样？

用 `OBJECT ENCODING` 指令查看底层编码：

```
127.0.0.1:6379> set k1 v1
OK
127.0.0.1:6379> OBJECT ENCODING k1
"embstr"
```

**底层编码类型**（`server.h` line 880）：

```c
/* Objects encoding. */
#define OBJ_ENCODING_RAW 0         /* Raw representation */
#define OBJ_ENCODING_INT 1         /* Encoded as integer */
#define OBJ_ENCODING_HT 2          /* Encoded as hash table */
#define OBJ_ENCODING_ZIPMAP 3      /* No longer used */
#define OBJ_ENCODING_LINKEDLIST 4  /* No longer used */
#define OBJ_ENCODING_ZIPLIST 5     /* No longer used: Redis7改用listpack */
#define OBJ_ENCODING_INTSET 6      /* Encoded as intset */
#define OBJ_ENCODING_SKIPLIST 7    /* Encoded as skiplist */
#define OBJ_ENCODING_EMBSTR 8      /* Embedded sds string encoding */
#define OBJ_ENCODING_QUICKLIST 9   /* Encoded as linked list of listpacks */
#define OBJ_ENCODING_STREAM 10     /* Encoded as a radix tree of listpacks */
#define OBJ_ENCODING_LISTPACK 11   /* Encoded as a listpack */
```

> Redis7 用 **listpack 替代了 ziplist**。旧文章中的 ziplist 相关讨论现已过时。

### 2、redisObject 结构（`server.h` line 900）

```c
struct redisObject {
    unsigned type:4;       // 上层数据类型: string, hash, set 等
    unsigned encoding:4;   // 底层编码类型: int, embstr, raw 等
    unsigned lru:LRU_BITS; // LRU时间 或 LFU数据
    int refcount;          // 引用计数
    void *ptr;             // 指向真正底层数据结构的指针
};
```

```
用户视角: type = string          KEY: k1
Redis底层: encoding = embstr     VALUE: redisObject -> SDS
```

`DEBUG OBJECT` 可查看 key 内部结构（需开启 `enable-debug-command`）：
```
127.0.0.1:6379> DEBUG OBJECT k1
Value at:0x7f0e36264c80 refcount:1 encoding:embstr serializedlength:3 lru:7607589 lru_seconds_idle:23
```

### 3、上层类型 vs 底层结构对照表

| 上层类型 | Redis6 底层 | **Redis7 底层** |
|----------|------------|----------------|
| **string** | SDS | SDS (int/embstr/raw) |
| **set** | intset + hashtable | intset + **listpack** + hashtable |
| **zset** | skiplist + ziplist | skiplist + **listpack** |
| **list** | quicklist + ziplist | quicklist + **listpack** |
| **hash** | hashtable + ziplist | hashtable + **listpack** |

> **核心变化**：Redis7 全面用 listpack 替代 ziplist。但保留 ziplist 代码以兼容。

---

## 二、String 数据结构详解

### 1、String 的三种编码

```
int    : value 可转为 long 整数 → ptr 直接存整数（不分配额外内存）
embstr : 字符串长度 < 44 字节 → redisObject + SDS 连续分配
raw    : 字符串长度 ≥ 44 字节 → redisObject 的 ptr 指向独立 SDS
```

**浮点数处理**：Redis 内部先把浮点数转成字符串再保存。

**源码验证**（`t_string.c` → `object.c:tryObjectEncodingEx`）：
- 数字长度超过 20 位 → 不用 int 保存
- `OBJ_SHARED_INTEGER = 1000`：1000 以内的数字直接指向共享内存

### 2、int 类型

robj 中的 ptr 直接指向缓存数据对象，小数字共享预创建对象。

### 3、embstr 类型（内嵌字符串）

embstr 核心：**将 SDS 对象直接分配在 redisObject 自己的内存后面**。连续内存提高读取速度、避免内存碎片。

> SDS 是不可修改的字符串。如果用 APPEND 修改，即使长度仍小于 44，Redis 也会改用 raw 类型。

### 4、SDS（Simple Dynamic String，`sds.h` line 45）

```c
struct __attribute__ ((__packed__)) sdshdr8 {
    uint8_t len;         // 已使用长度
    uint8_t alloc;       // 总分配长度（不含header和\0）
    unsigned char flags; // 类型标记
    char buf[];          // 实际数据
};
```

**为什么用 SDS 封装而不是 C 原生数组？**

| 问题 | C 原生 char[] | SDS |
|------|---------------|-----|
| 获取字符串长度 | O(N) 遍历 | O(1) 直接读 len |
| 二进制安全 | \0 作为结束符，内容包含\0则歧义 | 通过 len 确定长度 |
| 缓冲区溢出 | 手动管理，容易溢出 | 自动扩容 |

### 5、raw 类型

兜底方案。redisObject 和 SDS 分开申请内存，ptr 指向独立 SDS。

**总结**：

```
value能转数字?  ──Yes→ int类型（小数字用缓存对象）
     │
     No ↓
长度 < 44字节?  ──Yes→ embstr类型（连续内存，SDS内嵌）
     │
     No ↓
长度 ≥ 44字节   ──→    raw类型（redisObject + 独立SDS）
```

---

## 三、Hash 数据结构详解

### 1、Hash 的两种编码

```
数据量小 → listpack
数据量大 → hashtable
```

**判断标准**（两个配置参数）：
```conf
hash-max-listpack-entries 512   # 键值对个数阈值（默认512）
hash-max-listpack-value 64      # 单个value大小阈值（默认64字节）
```

```bash
127.0.0.1:6379> hset user:1 id 1 name roy
127.0.0.1:6379> OBJECT ENCODING user:1
"listpack"                                 # 数据少 → listpack

127.0.0.1:6379> config set hash-max-listpack-entries 3
127.0.0.1:6379> config set hash-max-listpack-value 8
127.0.0.1:6379> hset user:1 name royaaaaaaaaaaaaaaaa
127.0.0.1:6379> OBJECT ENCODING user:1
"hashtable"                                # 超阈值 → hashtable
```

**重要结论**：大部分正常情况 hash 都使用 listpack。listpack 可以升级为 hashtable，但**hashtable 不会降级**。

### 2、Hash 底层存储结构

```
hash value = dict → dictEntry[] (多个<k,v>对)
```

`dictEntry` 结构（`dict.c` line 63）：封装了 hash 的每个 field-value 键值对。

### 3、ListPack 详解（ziplist 的升级版）

**为什么要淘汰 ziplist？—— 连锁更新问题**

ziplist 的 entry 结构：
```
[previous_entry_length] [encoding] [content]
```

`previous_entry_length` 记录前一个节点的长度：
- 前节点 < 254 字节 → 占 1 字节
- 前节点 ≥ 254 字节 → 占 **5 字节**（首字节 0xfe + 4字节真实长度）

**连锁更新场景**：

```
初始状态: 每个 entry 长度在 250~253 字节之间
         previous_entry_length 都是 1 字节

插入一个 ≥254 字节的新节点到 E1 头部：
  → E1 的 previous_entry_length 需要从 1 字节扩展到 5 字节
  → E1 总长度超过 254 字节
  → E2 的 previous_entry_length 也需要扩展到 5 字节
  → E3 的 previous_entry_length 也需要扩展到 5 字节
  → ... 连锁反应！
```

**ListPack 的解决方案**：

listpack 的 entry 改为**记录自己的长度**而不是前一个 entry 的长度：
```
[encoding] [data] [backlen]
```

这样前一个 entry 变化不影响当前 entry，彻底解决连锁更新。

**ListPack 结构**（`listpack.h` line 49）：
```
|<-- total_bytes -->|<-- num_elements -->|<-- entry1 -->|<-- entry2 -->|...|<-- end -->|
```

---

## 四、List 数据结构详解

### 1、List 的两种编码

```bash
# 数据少 → listpack
127.0.0.1:6379> lpush l1 a1
127.0.0.1:6379> rpush l1 a2
127.0.0.1:6379> OBJECT ENCODING l1
"listpack"

# 数据多 → quicklist
127.0.0.1:6379> config set list-max-listpack-size 2
127.0.0.1:6379> lpush l3 a1 a2 a3
127.0.0.1:6379> OBJECT ENCODING l3
"quicklist"
```

**核心参数** `list-max-listpack-size`：
```
正数: 每个list节点存储的元素个数
负数 -1 ~ -5: 每个list节点的大小
  -5: 64Kb  (不推荐)
  -4: 32Kb  (不推荐)
  -3: 16Kb  (不推荐)
  -2: 8Kb   (推荐！)
  -1: 4Kb   (推荐！)
```

另一个参数 `list-compress-depth`：quicklist 节点压缩级别。0=不压缩，数字越大中间节点压缩越多。

### 2、QuickList 详解

**为什么需要 QuickList？**

| 数据结构 | 优点 | 缺点 |
|----------|------|------|
| Array（listpack） | 检索快（偏移量定位） | 增删慢（需移动大量节点） |
| LinkedList | 增删快（只调整指针） | 检索慢（只能遍历） |
| **QuickList** | **兼顾两者优点** | |

**QuickList 结构**：

```
quickList (链表)
  ├── quicklistNode (链表节点)
  │     ├── *prev (指向前一个节点)
  │     ├── *next (指向后一个节点)
  │     └── *entry → listpack (实际数据)
  ├── quicklistNode
  │     └── *entry → listpack
  └── quicklistNode
        └── *entry → listpack
```

- `quicklist` 整体是一个**链表**（`quick.h` line 98）
- 每个 `quicklistNode` 保存前后节点指针（`quick.h` line 36）
- `quicklistNode` 的 `*entry` 指向具体保存数据的 **listpack**

> Redis6 中 quicklistNode 存的是 ziplist，Redis7 改为 listpack。

---

## 五、Set 数据结构详解

### Set 三种编码

```bash
127.0.0.1:6379> sadd s1 1 2 3 4 5
127.0.0.1:6379> OBJECT ENCODING s1
"intset"           # 全数字 → intset

127.0.0.1:6379> sadd s2 a b c d e
127.0.0.1:6379> OBJECT ENCODING s2
"listpack"         # 非数字、数据少 → listpack

127.0.0.1:6379> config set set-max-listpack-entries 2
127.0.0.1:6379> sadd s3 a b c d e
127.0.0.1:6379> OBJECT ENCODING s3
"hashtable"        # 超阈值 → hashtable
```

**相关参数**：
```conf
set-max-intset-entries 512        # intset 最多保存元素数
set-max-listpack-entries 128      # listpack 最多保存元素数
set-max-listpack-value 64         # listpack 单个元素最大字节
```

**intset 结构**（`intset.h` line 35）：
```c
typedef struct intset {
    uint32_t encoding;   // 编码方式
    uint32_t length;     // 元素数量
    int8_t contents[];   // 实际元素数组
} intset;
```

Set 数据的子元素也是 `<k,v>` 形式的 entry，其中 key=元素值，value=null。

---

## 六、ZSet 数据结构详解

### ZSet 两种编码

```bash
127.0.0.1:6379> zadd z1 80 a
127.0.0.1:6379> OBJECT ENCODING z1
"listpack"    # 数据少 → listpack

127.0.0.1:6379> config set zset-max-listpack-entries 3
127.0.0.1:6379> zadd z2 80 a 90 b 91 c 95 d
127.0.0.1:6379> OBJECT ENCODING z2
"skiplist"    # 数据多 → skiplist
```

**参数**：
```conf
zset-max-listpack-entries 128     # 元素个数阈值
zset-max-listpack-value 64        # 单个元素值大小阈值
```

### SkipList（跳表）详解

**为什么需要 SkipList？**

ZSet 需要按 score 排序，sort 需要移动内存：
- 数据少 → 移动后重排成 listpack 可以接受
- 数据多 → 频繁移动内存开销大 → 链表结构更合适

但单链表检索只能从头到尾 O(N) → **SkipList 优化思路**：构建多层逐级缩减的子索引。

```
Level 3:  1 ──────────────→ 7 ──────────────→ ...
Level 2:  1 ────→ 3 ──────→ 7 ────→ 9 ──────→ ...
Level 1:  1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → ...
```

```
时间复杂度: O(log N)  查找
空间复杂度: O(N)      存储索引
```

**SkipList 特点**：
- ✅ 检索性能高，O(logN)
- ✅ Redis 读多写少的场景非常适合
- ❌ 更新时维护索引成本更高

---

## 七、总体总结

### 各类型底层结构总表

| Type | 编码方式 | 转换条件 |
|------|----------|----------|
| String | int → embstr → raw | 自动根据 value 类型和长度 |
| Hash | listpack → hashtable | 元素数>512 或 值>64字节 |
| List | listpack → quicklist | list-max-listpack-size 控制 |
| Set | intset → listpack → hashtable | 元素数超阈值即升级 |
| ZSet | listpack → skiplist | 元素数>128 或 值>64字节 |

### 经典面试题：Redis为什么这么快？

**没有标准答案**，Redis 在各层面都做了极致优化：
1. **无锁化的线程模型**：单线程串行，避免锁竞争和上下文切换
2. **层次分明的集群架构**：主从 → 哨兵 → Cluster，逐级升级
3. **灵活定制的底层数据结构**：根据数据特征自动选择最优编码
4. **极致优化的算法实现**：SkipList 空间换时间，QuickList 兼顾增删和检索

> 有道云笔记链接：[Redis底层数据结构解析](https://note.youdao.com/s/7u6OAnRJ)
