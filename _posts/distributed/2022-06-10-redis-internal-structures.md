---
title: "Redis 7 底层数据结构深度解析：从 redisObject 到 SkipList"
date: 2022-06-10
categories: distributed
tags: [Redis, 底层结构, SDS, ListPack, QuickList, SkipList, IntSet, 源码分析]
mermaid: true
---

> 面试官："Redis 为什么这么快？" 这道题的正确答案不在应用层，而在底层源码里。从 redisObject 统一对象模型到 SDS/ListPack/QuickList/SkipList 的自适应编码，本文结合 Redis 7.2.5 源码带你彻底拆解。

## 一、整体理解 Redis 底层数据结构

### 1.1 Redis 数据在底层是什么样的？

我们知道 Redis 的应用层有 String、Hash、List、Set、ZSet 等数据类型。但它们在底层是什么样子的？Redis 提供了一个 `OBJECT` 指令可以查看：

```bash
127.0.0.1:6379> set k1 v1
OK
127.0.0.1:6379> OBJECT ENCODING k1
"embstr"

127.0.0.1:6379> set k2 1
OK
127.0.0.1:6379> OBJECT ENCODING k2
"int"

127.0.0.1:6379> set k3 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa  # 超过44字节
OK
127.0.0.1:6379> OBJECT ENCODING k3
"raw"
```

**关键发现**：同一种应用层类型（String），底层可能对应多种不同的数据结构。Redis 会根据 value 的特征，**自适应选择最优的内部编码**。

还可以用 `DEBUG OBJECT` 查看更详细的内部信息（需在配置中开启 `enable-debug-command local`）：

```bash
127.0.0.1:6379> DEBUG OBJECT k1
Value at:0x7f0e36264c80 refcount:1 encoding:embstr serializedlength:3 lru:7607589 lru_seconds_idle:23
```

### 1.2 redisObject：Redis 的统一对象模型

在 Redis 源码 `server.h` 第 900 行，定义了核心的 `redisObject` 结构体：

```c
typedef struct redisObject {
    unsigned type:4;        // 上层数据类型：string, hash, set, zset, list
    unsigned encoding:4;    // 底层编码方式：int, embstr, raw, listpack, skiplist...
    unsigned lru:LRU_BITS;  // LRU时间或LFU数据（8位频率 + 16位访问时间）
    int refcount;           // 引用计数（共享对象）
    void *ptr;              // 指向真正底层数据结构的指针
} robj;
```

> Redis 中 key 是 String，而 **value 统一被封装为 redisObject**。这个设计类似 Java 的面向对象思想：不关心底层是什么，统一用一个对象包装。

核心字段含义：
- **type**：上层类型，用 `TYPE key` 查看
- **encoding**：底层编码，用 `OBJECT ENCODING key` 查看
- **lru**：内存超限时用于 LRU/LFU 淘汰
- **refcount**：对象引用次数，`OBJECT REFCOUNT key` 查看；1000 以内的整数字符串会被共享
- **\*ptr**：指向真正的数据存储结构

在 `server.h` 第 880 行定义了所有底层编码类型：

```c
/* Objects encoding. */
#define OBJ_ENCODING_RAW          0     /* Raw representation */
#define OBJ_ENCODING_INT          1     /* Encoded as integer */
#define OBJ_ENCODING_HT           2     /* Encoded as hash table */
#define OBJ_ENCODING_ZIPMAP       3     /* No longer used */
#define OBJ_ENCODING_LINKEDLIST   4     /* No longer used */
#define OBJ_ENCODING_ZIPLIST      5     /* No longer used: replaced by listpack */
#define OBJ_ENCODING_INTSET       6     /* Encoded as intset */
#define OBJ_ENCODING_SKIPLIST     7     /* Encoded as skiplist */
#define OBJ_ENCODING_EMBSTR       8     /* Embedded sds string encoding */
#define OBJ_ENCODING_QUICKLIST    9     /* Encoded as linked list of listpacks */
#define OBJ_ENCODING_STREAM       10    /* Encoded as a radix tree of listpacks */
#define OBJ_ENCODING_LISTPACK     11    /* Encoded as a listpack */
```

> 注意：`OBJ_ENCODING_ZIPLIST`、`OBJ_ENCODING_LINKEDLIST`、`OBJ_ENCODING_ZIPMAP` 已标记为不再使用。Redis 7 用 **ListPack 全面替代了 ZipList**，这是 Redis 6 → 7 最大的底层变化。

### 1.3 全部类型的底层对应关系总表

| 应用层类型 | Redis 6 底层结构 | Redis 7 底层结构 |
|-----------|-----------------|-----------------|
| **String** | SDS (动态字符串) | SDS |
| **Set** | intset + hashtable | intset + **listpack** + hashtable |
| **ZSet** | skiplist + **ziplist** | skiplist + **listpack** |
| **List** | quicklist + **ziplist** | quicklist + **listpack** |
| **Hash** | hashtable + **ziplist** | hashtable + **listpack** |

> ⚠️ 这是高级职位的**高频面试题**。

---

## 二、String 数据结构详解：SDS

### 2.1 三种内部编码

String 类型底层根据 value 自动选择三种编码：

| 编码 | 触发条件 | 说明 |
|------|---------|------|
| **int** | value 可转为 long 整数 | ptr 指针直接存整数值，不额外分配内存 |
| **embstr** | 字符串且长度 < 44 字节 | SDS 嵌入在 redisObject 旁边，连续内存 |
| **raw** | 字符串且长度 ≥ 44 字节 | SDS 独立分配，ptr 指针指向它 |

> 浮点数会被 Redis 先转为字符串再处理，不会用 int 编码。1000 以内的整数会直接复用预先创建的共享缓存对象（`OBJ_SHARED_INTEGER = 1000`）。

源码验证路径：
1. `SET` 指令 → `t_string.c` 的 `setCommand()` → 调用 `tryObjectEncoding()`
2. `object.c` 的 `tryObjectEncodingEx()` 中判断类型：
   - 能转 long 且长度 ≤ 20 位 → int
   - 字符串 → 判断长度

### 2.2 SDS 是什么？

SDS（Simple Dynamic String）是 Redis 对 C 语言字符串的封装。定义在 `sds.h`：

```c
// 根据字符串长度不同，有多种 SDS 变体
struct __attribute__ ((__packed__)) sdshdr5  { unsigned char flags; char buf[]; };
struct __attribute__ ((__packed__)) sdshdr8  { uint8_t len; uint8_t alloc; unsigned char flags; char buf[]; };
struct __attribute__ ((__packed__)) sdshdr16 { uint16_t len; uint16_t alloc; unsigned char flags; char buf[]; };
struct __attribute__ ((__packed__)) sdshdr32 { uint32_t len; uint32_t alloc; unsigned char flags; char buf[]; };
struct __attribute__ ((__packed__)) sdshdr64 { uint64_t len; uint64_t alloc; unsigned char flags; char buf[]; };
```

**SDS 相比 C 原生字符串的优势**：

1. **O(1) 获取长度**：SDS 记录了 `len`，不用像 C 字符串那样 O(N) 遍历到 `\0`
2. **避免缓冲区溢出**：SDS 有 `alloc` 记录分配空间，拼接时先检查空间
3. **二进制安全**：C 字符串以 `\0` 结束，数据内容不能包含 `\0`。SDS 用 `len` 判断边界，可以存任意二进制数据
4. **空间预分配**：减少内存重分配次数

### 2.3 embstr vs raw 的区别

`embstr` 字面意思是"内嵌字符串"（embedded string）。源码在 `object.c` 92 行：

```c
// embstr 会创建一块连续内存：redisObject + SDS 紧挨着分配
robj *createEmbeddedStringObject(const char *ptr, size_t len) {
    robj *o = zmalloc(sizeof(robj) + sizeof(struct sdshdr8) + len + 1);
    // redisObject 和 SDS 在同一块内存上
    o->type = OBJ_STRING;
    o->encoding = OBJ_ENCODING_EMBSTR;
    // ptr 直接指向内存尾部
    ...
}
```

**区别总结**：

| 特性 | embstr | raw |
|------|--------|-----|
| 内存分配 | 1 次（连续内存） | 2 次（redisObject + SDS 分开） |
| 内存释放 | 1 次 | 2 次 |
| 缓存友好 | 高（连续内存利用 CPU 缓存） | 低 |
| 可否修改 | ❌ 不可变（修改后会转 raw） | ✅ |

> ⚠️ **embstr 是不可变的**。如果你对 embstr 的 key 执行 `APPEND` 等修改操作，即使修改后长度仍小于 44 字节，Redis 也会**重新创建一个 raw 类型**。

### 2.4 String 底层结构总结

```
                               set k1 v1
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │  value 能转 long 整数？    │
                    └──────┬──────────┬────────┘
                          YES         NO
                           │           │
                           ▼           ▼
                        int编码        字符串
                           │           │
               ┌───────────┤     ┌─────┴─────┐
               ▼                     │           │
        <1000: 复用预创建         <44字节      ≥44字节
        缓存对象，连内存              │           │
        都不需要分配                ▼           ▼
        ≥1000: ptr直接           embstr       raw
        指向整数值               （不可变）    （可变）
```

> **设计哲学**：Redis 根据用户的不同键值**自适应选择最优编码**，这些逻辑对用户完全透明。这种"多态"的设计模式是 Redis 高性能的重要保障。

---

## 三、Hash 类型数据结构详解：ListPack

### 3.1 两种底层编码

```bash
127.0.0.1:6379> hset user:1 id 1 name roy
(integer) 2
127.0.0.1:6379> OBJECT ENCODING user:1
"listpack"                            # ← 数据量小时用 listpack
```

```bash
127.0.0.1:6379> config set hash-max-listpack-entries 3
127.0.0.1:6379> config set hash-max-listpack-value 8
127.0.0.1:6379> hset user:1 name royaaaaaaaaaaaaaaaa  # value 长度超限
127.0.0.1:6379> OBJECT ENCODING user:1
"hashtable"                           # ← 升级为 hashtable
```

**转换规则**：由两个参数决定

| 参数 | 含义 | 默认值 |
|------|------|--------|
| `hash-max-listpack-entries` | 键值对个数上限 | 512 |
| `hash-max-listpack-value` | 单个 value 大小上限（字节） | 64 |

> 可以**升级**（listpack → hashtable），但**不能降级**（hashtable 不会自动变回 listpack）。

### 3.2 ZipList → ListPack 的演进历程（重要！）

要理解 ListPack，必须先理解 ZipList。在 Redis 6 中，Hash/List/ZSet 在元素较少时都用 ZipList 存储。

#### ZipList 的结构

ZipList 是一个**内存紧凑型**数据结构，占用一块连续的内存空间：

```
┌──────────┬──────────┬──────────┬───────┬───────┬───────┬───────┐
│ zlbytes  │ zltail   │ zllen    │entry1 │entry2 │ ...   │ zlend │
│ (总字节) │ (尾偏移) │ (节点数) │       │       │       │ (0xFF)│
└──────────┴──────────┴──────────┴───────┴───────┴───────┴───────┘
```

每个 entry 的结构：

```
┌──────────────────────┬──────────┬──────────┐
│ previous_entry_length│ encoding │ content  │
│ (1或5字节)            │ (编码)    │ (数据)   │
└──────────────────────┴──────────┴──────────┘
```

**previous_entry_length** 的设计是 ZipList 的精华，也是它的致命缺陷：

- 前一个 entry 长度 < 254 → 占 **1 字节**
- 前一个 entry 长度 ≥ 254 → 占 **5 字节**（第一个字节 `0xFE`，后 4 字节存储真实长度）
- 255 被 `zlend` 占用作为结束标记

> 这种设计让 ZipList 不需要保存前后指针（像双向链表那样），极大压缩了内存。要从头或尾找指定元素，通过长度字段即可计算偏移，时间复杂度 O(1)。但找中间元素只能**从前往后单向遍历**。

#### 连锁更新问题（Cascade Update）

这是 ZipList 被废弃的**核心原因**。考虑如下场景：

```
假设一个 ZipList，每个 entry 的长度都在 250~253 字节范围
此时所有 previous_entry_length 都只需要 1 个字节

现在在表头插入一个长度 ≥ 254 的新节点：

  [新节点254+] → [e1=252] → [e2=251] → [e3=253] → ...

Step 1: e1 的 previous_entry_length 只有 1 字节，装不下新节点的长度
         → 扩展 e1 的 previous_entry_length 到 5 字节
         → e1 长度变成 252 + 4 = 256 字节（≥ 254）
Step 2: e2 的 previous_entry_length 发现 e1 变成 256，装不下
         → 扩展 e2 的 previous_entry_length 到 5 字节
         → e2 长度变成 251 + 4 = 255 字节（≥ 254）
Step 3: e3 同理...
         → 继续蔓延到后续所有 entry
```

**连锁更新的危害**：
- 一次插入操作可能触发大量节点的内存重分配
- 每个节点重新分配都涉及内存拷贝
- 极端情况下性能退化严重，且不安全

Redis 作者 antirez 在他的 listpack 仓库中专门介绍了这个问题：[listpack/listpack.md](https://github.com/antirez/listpack/blob/master/listpack.md)

#### ListPack 的解决方案

ListPack 只做了一个关键修改：

```
┌──────────┬──────────┬──────────┐
│ encoding │ content  │ cur_len  │   ← 记录自己的长度，而非前一个的长度！
└──────────┴──────────┴──────────┘
```

**把 previous_entry_length 替换为 cur_len（自己的长度）**：
- 每个 entry 只记录自己的长度，不再依赖前一个 entry
- 前一个 entry 变化，不影响当前 entry 的长度记录
- **彻底消除了连锁更新问题**

源码定义在 `listpack.h` 49 行：

```c
/* Listpack element encoding */
#define LP_ENCODING_7BIT_UINT 0
#define LP_ENCODING_13BIT_INT 4
// ... 更多编码类型
```

### 3.3 Hash 底层结构总结

1. Hash 底层大多用 **listpack** 存储（元素少、value 小）
2. 超过阈值后升级为 **hashtable**（不会降级）
3. listpack 是 ziplist 的升级，**消除了连锁更新问题**
4. 判断阈值的两个参数：`hash-max-listpack-entries`（默认512）和 `hash-max-listpack-value`（默认64）

---

## 四、List 类型数据结构详解：QuickList

### 4.1 两种底层编码

```bash
127.0.0.1:6379> lpush l1 a1 a2
127.0.0.1:6379> OBJECT ENCODING l1
"listpack"

127.0.0.1:6379> config set list-max-listpack-size 2
127.0.0.1:6379> lpush l3 a1 a2 a3
127.0.0.1:6379> OBJECT ENCODING l3
"quicklist"
```

参数 `list-max-listpack-size` 控制升级阈值：

```
# -5: 64Kb   -4: 32Kb   -3: 16Kb   -2: 8Kb   -1: 4Kb
# 正数: 精确的元素个数
# 推荐: -2 (8Kb) 或 -1 (4Kb)
list-max-listpack-size -2
```

### 4.2 为什么需要 QuickList？

这是一个经典的**数据结构权衡**问题：

| 数据结构 | 查询/LRANGE | 增删/LPUSH/LPOP |
|---------|-----------|---------------|
| **数组 (Array / ListPack)** | ✅ O(1) 通过偏移量定位 | ❌ 需移动大量内存 |
| **链表 (LinkedList)** | ❌ O(N) 只能遍历 | ✅ 只需调整指针 |

> ListPack 对检索友好（LRANGE），但对增删不友好（LPUSH/LPOP）。
> 纯链表对增删友好，但对检索不友好，也不适合 List 场景。

Redis 需要一个**数组 + 链表结合体**──这就是 **QuickList**。

### 4.3 QuickList 的结构设计

```
┌─────────────────────────────────────────────────────┐
│                    QuickList                         │
│                     (表头)                            │
├─────────┬─────────┬─────────┬─────────┬─────────────┤
│  Node 0 │  Node 1 │  Node 2 │  Node 3 │     ...      │
│  ↓prev  │ ↓ prev  │ ↓ prev  │ ↓ prev  │              │
│  →next  │ → next  │ → next  │ → next  │              │
├────┬────┼────┬────┼────┬────┼────┬────┼─────────────┤
│ListPack│ListPack│ListPack│ListPack│   ...           │
│(紧凑数组)│(紧凑数组)│(紧凑数组)│(紧凑数组)│               │
└────┴────┴────┴────┴────┴────┴────┴────┴─────────────┘
```

源码定义（`quicklist.h`）：

```c
// 每个节点是一个 quicklistNode
typedef struct quicklistNode {
    struct quicklistNode *prev;     // 前一个节点（链表）
    struct quicklistNode *next;     // 后一个节点（链表）
    unsigned char *entry;           // 指向 listpack（数组）
    size_t sz;                      // entry 的总字节数
    unsigned int count : 16;        // listpack 中的元素数量
    unsigned int encoding : 2;      // RAW==1 or LZF==2
    unsigned int container : 2;     // PLAIN==1 or PACKED==2
    unsigned int recompress : 1;
    unsigned int attempted_compress : 1;
    unsigned int dont_compress : 1;
    unsigned int extra : 9;
} quicklistNode;
```

**设计精髓**：

| 层面 | 结构 | 优势 |
|------|------|------|
| **宏观**（Node 之间） | 双向链表 | LPUSH/LPOP 只需操作头节点，O(1) |
| **微观**（Node 内部） | ListPack（数组） | LRANGE 在少数节点内利用数组偏移快速定位 |

还有 `list-compress-depth` 参数控制中间节点是否压缩（LZF 算法）：

```
# 0 = 不压缩
# 1 = 不压缩首尾两端的1个节点
# 2 = 不压缩首尾两端的2个节点
```

两端不压缩是为了保证 LPUSH/LPOP/LRANGE 两端操作的性能。

### 4.4 List 底层结构总结

```
list 数据量小（list-max-listpack-size 以内）
         │
         ▼
     listpack 直接存储
         │
   【升级过程】
         │
         ▼
   quicklist（链表 + listpack）
         │
  ┌──────┴──────┐
  │ 宏观：链表   │ ← 方便增删节点
  │ 微观：数组   │ ← 方便检索数据
  └─────────────┘
```

> Redis 6 的 quicklist 内部是 ziplist，Redis 7 改为 listpack。本质上一样，只是内部容器升级了。

---

## 五、Set 类型数据结构详解

### 5.1 三种底层编码

```bash
127.0.0.1:6379> sadd s1 1 2 3 4 5
127.0.0.1:6379> OBJECT ENCODING s1
"intset"           # ← 全数字 → intset

127.0.0.1:6379> sadd s2 a b c d e
127.0.0.1:6379> OBJECT ENCODING s2
"listpack"         # ← 非数字但数据少 → listpack

127.0.0.1:6379> config set set-max-listpack-entries 2
127.0.0.1:6379> sadd s3 a b c d e
127.0.0.1:6379> OBJECT ENCODING s3
"hashtable"        # ← 数据量大 → hashtable
```

**三个控制参数**：

| 参数 | 含义 | 默认值 |
|------|------|--------|
| `set-max-intset-entries` | intset 最大元素数 | 512 |
| `set-max-listpack-entries` | listpack 最大元素数 | 128 |
| `set-max-listpack-value` | listpack 单元素最大字节 | 64 |

Set 底层的 intset 结构很简单（定义在 `intset.h`）：

```c
typedef struct intset {
    uint32_t encoding;    // 元素的编码方式（2/4/8字节）
    uint32_t length;      // 元素个数
    int8_t contents[];    // 保存元素的数组
} intset;
```

> intset 中的元素按**从小到大排序**且**不重复**，支持二分查找。

---

## 六、ZSet 类型数据结构详解：SkipList

### 6.1 两种底层编码

```bash
127.0.0.1:6379> zadd z1 80 a
127.0.0.1:6379> OBJECT ENCODING z1
"listpack"

127.0.0.1:6379> config set zset-max-listpack-entries 3
127.0.0.1:6379> zadd z2 80 a 90 b 91 c 95 d
127.0.0.1:6379> OBJECT ENCODING z2
"skiplist"
```

**控制参数**：

| 参数 | 含义 | 默认值 |
|------|------|--------|
| `zset-max-listpack-entries` | listpack 最大元素数 | 128 |
| `zset-max-listpack-value` | 单元素最大字节数 | 64 |

### 6.2 为什么需要 SkipList？

ZSet 的数据需要**按 score 排序**。排序过程涉及数据移动：

- 数据少 → listpack 移动内存的成本可接受
- 数据多 → 频繁移动内存开销太大，需要链表结构

但纯链表的检索是 O(N)，太慢。

**SkipList（跳表）的设计思路**：在有序链表的基础上**构建多层逐渐缩减的索引**：

```
Level 3:  1 ──────────────────────> 27 ──────────> (null)
Level 2:  1 ───────> 12 ──────────> 27 ──────────> (null)
Level 1:  1 ──> 5 ──> 12 ──> 17 ──> 27 ──> 33 ──> (null)
          ↓     ↓     ↓     ↓     ↓     ↓
          各层索引是同一个节点的不同层级视图
```

**查找过程**：从最高层开始，沿索引快速跳跃，到接近目标时降层，直到最底层找到。

| 特性 | SkipList | 平衡树（AVL/红黑树） |
|------|---------|-------------------|
| 时间复杂度（查找） | O(logN) | O(logN) |
| 实现复杂度 | 简单 | 复杂（需要旋转） |
| 范围查询 | ✅ 高效（链表天然有序） | 较复杂 |
| 并发友好 | ✅（局部调整） | ❌（需要全局旋转） |

> SkipList 是**用空间换时间**的典型。时间复杂度 O(logN)，空间复杂度 O(N)。适合**读多写少**的场景，这正是 Redis 的天生优势。

**为什么 Redis 用 SkipList 而不用红黑树？**
1. SkipList 实现简单，代码量少
2. SkipList 范围查询天然高效（有序链表直接遍历）
3. 高并发下 SkipList 只需局部调整，红黑树需要全局平衡旋转

### 6.3 源码验证路径

底层转换逻辑在 `t_zset.c`：

```c
// zaddGenericCommand → zsetAdd
// 会根据 zset-max-listpack-entries 和 zset-max-listpack-value 
// 决定是否从 listpack 升级到 skiplist
```

### 6.4 ZSet 底层结构总结

```
zset 数据量小
    ↓
  listpack（紧凑数组）
    ↓ 超过阈值（128 entries 或 64 bytes/value）
  skiplist（多层索引链表，读多写少最优）
```

---

## 七、课程总结与面试导向

### 7.1 四大高频面试题

**Q1：Redis 底层数据结构总览？**

| 版本 | String | Set | ZSet | List | Hash |
|------|--------|-----|------|------|------|
| Redis 6 | SDS | intset+hashtable | skiplist+ziplist | quicklist+ziplist | hashtable+ziplist |
| Redis 7 | SDS | intset+listpack+hashtable | skiplist+listpack | quicklist+listpack | hashtable+listpack |

**Q2：Redis 6 → Redis 7 底层结构最大的变化是什么？**

用 **ListPack 全面替代 ZipList**。核心原因是 ZipList 的 `previous_entry_length` 机制导致**连锁更新（Cascade Update）**问题，ListPack 改为记录自己的长度后彻底消除此问题。

**Q3：QuickList 为什么要设计成链表+数组的结合？**

数组（ListPack）对 LRANGE 检索友好但对 LPUSH 增删不友好；链表增删 O(1) 但检索 O(N)。QuickList 宏观用链表方便增删，微观用 ListPack 方便检索，取两者之长。

**Q4：为什么 ZSet 用 SkipList 而不用红黑树？**

SkipList 实现简单、范围查询天然高效、并发友好（局部调整）。Redis 追求简单高效，不需要红黑树那种复杂的旋转平衡。

### 7.2 "Redis 为什么这么快"的底层视角

> 无锁化的线程模型、层层递进的集群架构、灵活定制的底层数据结构、极致优化的算法实现——这些是 Redis 对性能极致要求的体现。

从底层数据结构角度看：
- **SDS**：O(1) 长度获取、空间预分配、二进制安全
- **ListPack**：紧凑内存、CPU 缓存友好、消除连锁更新
- **QuickList**：数组+链表混合，兼顾两端操作和随机访问
- **SkipList**：O(logN) 查找，空间换时间
- **自适应性**：数据量小时自动选择最紧凑的结构，大时切换到最高效的结构

> Redis 的价值不仅仅是快。集中式缓存、分布式锁、分布式主键生成、NoSQL 数据库、向量搜索——如何在复杂业务中最大化发挥 Redis 的性能优势，是每个 Java 程序员的基本功。
