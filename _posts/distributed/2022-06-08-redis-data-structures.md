---
title: "Redis 7 核心数据结构实战手册"
date: 2022-06-08
categories: distributed
tags: [Redis, String, Hash, List, Set, ZSet, Stream, HyperLogLog, BitMap, GEO]
mermaid: true
---

> "纸上得来终觉浅"。Redis 的数据结构远不止简单的 string/list/hash/set/zset。从 Stream 消息队列到 HyperLogLog 亿级统计，从 BitMap 签到到 GEO 附近的人——每种类型都对应一个真实的业务场景。本文带你从最常用的 10 种类型入手，了解底层结构，熟练基础操作。

## 一、Redis Key 的命名与管理

### 1.1 Key 命名规范

官方没有强制要求，但建议：

```
业务名:表名:id
```

```bash
127.0.0.1:6379> set user:1:name roy
OK
127.0.0.1:6379> set user:1:age 19
OK

127.0.0.1:6379> keys user:1*
1) "user:1:name"
2) "user:1:age"
```

### 1.2 Key 查询

```bash
# 获取所有 key
127.0.0.1:6379> keys *

# 模糊匹配
127.0.0.1:6379> keys pattern
    ?   # 单字符匹配（占位）
    *   # 任意多字符
    []  # 匹配括号内任一字符
    [^] # 匹配不在括号内的字符
    [a-b] # 匹配 a 到 ab 之间的字符

# 生产环境用 SCAN 替代 KEYS
127.0.0.1:6379> SCAN cursor [MATCH pattern] [COUNT count]
    参数：
      cursor: 遍历游标
      pattern: 匹配模式
      count: 每次近似返回数量（默认10）

    MSET/MGET 也支持类似操作
```

### 1.3 Key 操作指令

| 指令 | 说明 | 时间复杂度 |
|------|------|-----------|
| `EXISTS key...` | 检查是否存在，返回存在个数 | O(N) |
| `RENAME key newkey` | 重命名，newkey 存在则**覆盖** | O(1) |
| `RENAMENX key newkey` | 原名存在 & 目标名**不存在**时才改 | O(1) |
| `DEL key...` | 删除，O(N) | |
| `UNLINK key...` | **异步删除**，处理后返回，不阻塞主线程 | O(N) |
| `MOVE key db` | 移动到指定库 | O(1) |
| `TYPE key` | 查看类型 | O(1) |
| `EXPIRE key seconds` | 设置过期时间(秒) | O(1) |
| `EXPIREAT key timestamp` | 设置过期Unix时间戳 | O(1) |
| `PEXPIRE key milliseconds` | 毫秒级过期 | O(1) |
| `TTL key` | 查看剩余秒数（-1永不过期，-2不存在） | O(1) |
| `PTTL key` | 查看剩余毫秒数 | O(1) |
| `PERSIST key` | 移除过期时间 | O(1) |

> `UNLINK` 是 `DEL` 的异步版本：从 keyspace 中移除 key 后，**在后台线程异步释放内存**。处理 BigKey 时用 `UNLINK` 可避免阻塞主线程。

TTL 不会自动延长：`set` 一个已有过期时间的 key 会**清除过期时间**（key 变回永不过期）。

---

## 二、String 类型：不止是字符串

String 是 Redis 最简单也最核心的类型。最大支持 512MB。

> 所有数据都存在 **RedisObject** 中。所有的 key 和 value 本质都是 String。其他类型（Hash、List、Set、ZSet）是基于 String 的**有序编排**。

### 2.1 基础操作

使用数字时，实际在内存中以 int 类型存储，但指令上统一以 "string" 处理：

```bash
127.0.0.1:6379> set user:1:name roy
127.0.0.1:6379> set user:1:age 19
127.0.0.1:6379> mset user:1:email roy@123.com user:1:mobile 13800000000
127.0.0.1:6379> mget user:1:id user:1:name user:1:age
1) (nil)
2) "roy"
3) "19"
```

### 2.2 完整指令速查

| 分类 | 指令 | 说明 |
|------|------|------|
| 设置 | `SET key value` | K-V 关联，key 存在则覆盖 |
| | `SETNX key value` | 不存在时才设置（分布式锁基础） |
| | `SETEX key seconds value` | 原子设置 + 过期 |
| | `SETRANGE key offset value` | 指定位置替换值 |
| | `MSET key value...` | 批量设置 |
| | `MSETNX key value...` | 批量设置（全部不存在） |
| | `GETSET key value` | 先 GET 旧值再 SET 新值 |
| | `APPEND key value` | 末尾追加 |
| 获取 | `GET key` | 获取值 |
| | `MGET key...` | 批量获取 |
| | `GETRANGE key start end` | 获取子串（含 end，0/-1 含全部） |
| | `STRLEN key` | 获取长度 |
| 自增 | `INCR key` | 原子加1（不存在时由0开始） |
| | `INCRBY key increment` | 指定步长 |
| | `DECR key` | 原子减1 |
| | `DECRBY key decrement` | 指定步长 |
| | `INCRBYFLOAT key increment` | 浮点增减 |
| 删除 | `DEL key...` | 原子删除 |

> 注意 `SETRANGE`：当 offset=3 替换 3 个字符 "BCD" 时，第 6 位若原来有值则不变，若原来没有则补 `\x00`。它是**替换**而非插入。

### 2.3 典型应用场景

| 场景 | 实现 | 示例 |
|------|------|------|
| 分布式锁 | SETNX + EXPIRE / SET NX EX | `SET lock:order:1 1 EX 30 NX` |
| 计数器 | INCR | 文章阅读量、点赞数 |
| 分布式 ID 生成 | INCR | `INCR global:user:id` |
| 对象缓存 | SET/GET | 用户 Session、配置信息 |
| 限流 | INCR + EXPIRE | 单位时间内访问次数 |
| 二进制存储 | SET/GET | 小文件（缩略图等） |

---

## 三、Hash 类型：结构化对象存储

Hash 适合存储对象。早期 Redis 设计非常节俭：能用一个 key 存储的尽量不用过多 key。但现在有了 Cluster、HashTag 等功能，对 key 的容忍度提高了很多。

### 3.1 完整指令速查

| 分类 | 指令 | 说明 |
|------|------|------|
| 设置 | `HSET key field value...` | 设字段值，可批量 |
| | `HSETNX key field value` | 字段不存在才设置 |
| 获取 | `HGET key field` | 获取字段值 |
| | `HMGET key field...` | 批量获取 |
| | `HGETALL key` | 获取所有字段值 |
| | `HKEYS key` | 所有字段名 |
| | `HVALS key` | 所有字段值 |
| | `HLEN key` | 字段数量 |
| | `HEXISTS key field` | 字段是否存在 |
| 计数 | `HINCRBY key field increment` | 整数增减 |
| | `HINCRBYFLOAT key field increment` | 浮点增减 |
| 删除 | `HDEL key field...` | 删除字段 |
| 遍历 | `HSCAN key cursor` | 迭代器遍历（替代 HGETALL 大 Hash） |

> 注意：HINCRBY、HINCRBYFLOAT 相当于 String 的 INCRBY、INCRBYFLOAT 放在 Hash 的 field 上，数据安全性和性能一样。

### 3.2 应用场景对比

| 存储方式 | 操作 | 特点 |
|---------|------|------|
| `HSET user:1 name roy age 19` | 一个 key 存整个用户对象 | 内存省，原子性好 |
| `SET user:1:name roy` + `SET user:1:age 19` | 每个属性单独一个 key | 过期时间独立，更灵活 |

现在的推荐：**根据数据特征选择**——需要独立过期时间的用多个 String Key，追求紧凑存储的用 Hash。

---

## 四、List 类型：有序可重复队列

### 4.1 数据结构特性

- **有序**可重复
- 按插入顺序排序
- 底层基于链表（双端操作 O(1)）
- 可根据索引获取元素（`LINDEX`）
- 可实现**栈**（`LPUSH` + `LPOP`）或**队列**（`LPUSH` + `RPOP`）

### 4.2 完整指令速查

| 分类 | 指令 | 说明 |
|------|------|------|
| 添加 | `LPUSH key element...` | 头部插入 |
| | `RPUSH key element...` | 尾部插入 |
| 弹出 | `LPOP key [count]` | 头部弹出 |
| | `RPOP key [count]` | 尾部弹出 |
| | `BLPOP key... timeout` | **阻塞式**头部弹出（timeout=0 无限等待） |
| | `BRPOP key... timeout` | **阻塞式**尾部弹出 |
| 移动 | `LMOVE source dest <LEFT|RIGHT> <LEFT|RIGHT>` | 原子移动（多步合一） |
| | `BLMOVE source dest <LEFT|RIGHT> <LEFT|RIGHT> timeout` | 阻塞式移动 |
| 检索 | `LLEN key` | 元素个数 |
| | `LINDEX key index` | 按索引获取 |
| | `LRANGE key start stop` | 区间获取 |
| | `LPOS key element [RANK] [COUNT] [MAXLEN]` | 元素位置 |
| 修改 | `LSET key index element` | 替换指定位置元素 |
| | `LINSERT key BEFORE\|AFTER pivot element` | 指定位置插入 |
| 删除 | `LREM key count element` | count>0 从左删，<0 从右删，=0 全删 |
| | `LTRIM key start stop` | 修剪列表（保留区间） |

> **LMOVE** 是 Redis 6.2 引入的原子操作（替代了旧的 RPOPLPUSH），用于实现可靠队列。
>
> **BLMOVE/BRPOP/BLPOP** 需要多个客户端配合测试。

### 4.3 应用场景

| 场景 | 实现 |
|------|------|
| 消息队列 | LPUSH + RPOP（或 BRPOP 阻塞消费） |
| 最新 N 条 | LPUSH + LTRIM（保留最新 100 条） |
| 栈 | LPUSH + LPOP |
| 社交 Feed 流 | LPUSH 新动态 + LRANGE 分页查看 |

---

## 五、Set 类型：无序去重集合

> 交、并、差集是 Set 特有的高价值能力。

### 5.1 完整指令速查

| 分类 | 指令 | 说明 |
|------|------|------|
| 添加 | `SADD key member...` | 添加成员 |
| 查找 | `SMEMBERS key` | 查看所有成员 |
| | `SISMEMBER key member` | 是否在集合中 |
| | `SCARD key` | 成员数量 |
| | `SRANDMEMBER key [count]` | 随机返回 |
| 移除 | `SREM key member...` | 删除成员 |
| | `SPOP key [count]` | 随机弹出 |
| 移动 | `SMOVE source dest member` | 原子移动到另一个集合 |
| 交集 | `SINTER key...` | 多集合交集 |
| | `SINTERCARD numkeys key... [LIMIT limit]` | 交集大小（不返回内容，Redis 7 新） |
| | `SINTERSTORE dest key...` | 交集 + 保存 |
| 并集 | `SUNION key...` | 多集合并集 |
| | `SUNIONSTORE dest key...` | 并集 + 保存 |
| 差集 | `SDIFF key...` | 差集（第一个集合有，后面集合无） |
| | `SDIFFSTORE dest key...` | 差集 + 保存 |

> **SINTERCARD** 是 Redis 7 新增，特别适用于**只关心交集数量、不关心内容**的场景（如共同好友数、共同关注数）——直接返回数字，**避免传输大量数据**。

### 5.2 应用场景

| 场景 | 实现 |
|------|------|
| 抽奖系统 | `SPOP` / `SRANDMEMBER` |
| 点赞/收藏 | `SADD` 用户ID → 去重 |
| 标签系统 | `SADD` 标签 + `SINTER` 按标签查找 |
| 共同好友 | `SINTER` 两个好友集合 |
| 推荐关注 | `SDIFF`：关注了A但没关注B的人 |

### 5.3 Set 运算业务案例

```bash
# 用户标签
SADD news:1:tags tech ai
SADD news:2:tags travel food
SADD news:3:tags tech travel

# 按标签找新闻
SINTER news:1:tags news:2:tags     # 同时有 tech 和 travel

# 推荐：用户A看过的标签中，用户B没看过哪些
SDIFF user:A:tags user:B:tags
```

---

## 六、ZSet（Sorted Set）类型：带权重的集合

### 6.1 与 Set 和 List 的区别

| 类型 | 特点 |
|------|------|
| List | 除序值，通过链表低层双向遍历，操作两端 O(1) |
| Set | 无序不重复，通过哈希表 O(1) 快速检索 |
| ZSet | 加权排序不重复，底层 listpack / skiplist |

**应用原则**：能用 Set 实现的功能优先用 Set，需要排序时才用 ZSet。

### 6.2 完整指令速查

| 分类 | 指令 | 说明 |
|------|------|------|
| 添加 | `ZADD key score member...` | 添加成员（可批量） |
| 查找 | `ZRANGE key min max [BYSCORE\|BYLEX] [REV] [LIMIT]` | 按索引范围（Redis 7: 支持 BYSCORE/BYLEX 直接查询） |
| | `ZSCORE key member` | 成员分数 |
| | `ZRANK key member` | 排名（从低到高） |
| | `ZREVRANK key member` | 排名（从高到低） |
| | `ZCARD key` | 元素总数 |
| | `ZCOUNT key min max` | 分数区间内元素数 |
| 删除 | `ZREM key member...` | 删除成员 |
| | `ZREMRANGEBYRANK key start end` | 按排名范围删 |
| | `ZREMRANGEBYSCORE key min max` | 按分数范围删 |
| 运算 | `ZUNION numkeys key... [WEIGHTS w...] [AGGREGATE SUM\|MIN\|MAX]` | 并集运算 |
| | `ZINTER numkeys key... [WEIGHTS w...] [AGGREGATE SUM\|MIN\|MAX]` | 交集运算 |
| | `ZUNIONSTORE dest numkeys key...` | 并集 + 保存 |
| | `ZINTERSTORE dest numkeys key...` | 交集 + 保存 |
| | `ZINTERCARD numkeys key... [LIMIT limit]` | 交集数量（Redis 7 新） |

**ZADD 参数详解**（Redis 7 新增了多个选项）：

```
ZADD key [NX|XX] [GT|LT] [CH] [INCR] score member [score member ...]
  NX: 不更新已存在成员
  XX: 只更新已存在成员
  GT: 新分>旧分才更新
  LT: 新分<旧分才更新
  CH: 返回被修改的元素个数
  INCR: 分数增减，不能批量
```

**排行榜实现**：

```bash
# 分数从低到高
ZRANGE leaderboard 0 -1

# 分数从高到低（反向）
ZREVRANGE leaderboard 0 -1 WITHSCORES

# Top 10 分数
ZREVRANGEBYSCORE leaderboard +inf -inf WITHSCORES LIMIT 0 10

# 分页倒序：每页20条，第N页
ZREVRANGE leaderboard 0 +inf BYSCORE REV LIMIT (N-1)*20 20

# 包含分数范围
ZREVRANGEBYSCORE leaderboard 100 50  # 分数 50~100 倒序
ZRANGEBYSCORE leaderboard 50 100     # 分数 50~100 正序
```

### 6.3 应用场景

| 场景 | 实现 |
|------|------|
| 排行榜（游戏、直播） | ZADD + ZREVRANGE |
| 延迟队列 | score=执行时间戳，轮询 0~当前时间 |
| 带权重的标签 | tag + weight 排序推荐 |
| 时间线 | score=时间戳，按时间排序 |

---

## 七、BitMap：位运算的极致

用 String 实现，每个 bit 占一位。setbit key 操作的是 redisObject 的动态字符串。

| 指令 | 说明 |
|------|------|
| `SETBIT key offset value` | 设置位（offset注意大小端问题） |
| `GETBIT key offset` | 获取位 |
| `BITPOS key bit [start] [end] [BYTE\|BIT]` | 查找首个 0/1 位 |
| `BITCOUNT key [start end [BYTE\|BIT]]` | 统计 1 的个数 |
| `BITFIELD key [GET type offset] [SET type offset value] [INCRBY type offset increment]` | 多类型操作 |
| `BITOP operation destkey key...` | 位运算（AND/OR/XOR/NOT） |

**签到系统**：

```bash
# userId=100，2020年1月15日签到
SETBIT user:sign:100:202001 14 1

# 检查1月15日是否签到
GETBIT user:sign:100:202001 14

# 统计这个月签到天数
BITCOUNT user:sign:100:202001 0 -1
```

> ⚠️ **大端小端问题**：bitmap 内部在每个字节中**高位在前低位在后**（大端序）。所以 `SETBIT key 0 1` 在最左边位置，`SETBIT key 7 1` 在最右边位置。

**连续签到优化**：

```bash
# BITFIELD 可以一次 SET 多个连续位
BITFIELD user:sign:100:2020:1 SET u31 0 7   # 第0天开始 7 天连续设置
```

---

## 八、HyperLogLog：亿级数据量的统计利器

> 统计网站 UV（Unique Visitor）的传统做法是用 Set 存储用户 ID。一个网站日活如果上亿，Set 里存一亿个 UUID（36字节/个）≈ 3.6GB——内存扛不住。

HyperLogLog 底层基于**伯努利试验**和**极大似然估计**：完成 n 次实验需要的轮次，最大值记录了"运气最差"时的实验量级，通过这个值反推 n。

### 8.1 指令速查

| 指令 | 说明 |
|------|------|
| `PFADD key element...` | 添加（内存占用极低） |
| `PFCOUNT key...` | 基数统计 |

```bash
127.0.0.1:6379> PFADD 2020_03_09:unique:ids "uuid-1" "uuid-2" "uuid-3" "uuid-4"
(integer) 1

127.0.0.1:6379> PFCOUNT 2020_03_09:unique:ids
(integer) 4
```

### 8.2 性能特点

- 不管数据量多大，**固定占用 12KB 内存**
- 标准误差率 **0.81%**（可接受范围内）
- 不支持删除单个元素、不支持查看具体元素

> 12KB 存 10 亿 UV！误差不到 1%，对于大多数统计场景完全可以接受。

---

## 九、GEO：地理位置计算

GEO 底层是 ZSet。

### 9.1 指令速查

| 指令 | 说明 |
|------|------|
| `GEOADD key longitude latitude member...` | 添加坐标 |
| `GEOPOS key member...` | 获取坐标 |
| `GEODIST key member1 member2 [m\|km\|ft\|mi]` | 两点距离 |
| `GEOSEARCH key [FROMMEMBER member\|FROMLONLAT lon lat] [BYRADIUS\|BYBOX]` | 搜索附近 |
| `GEOSEARCHSTORE dest src...` | 搜索+保存 |

**添加城市**：

```bash
GEOADD city 116.408 39.904 beijing
GEOADD city 121.445 31.213 shanghai
GEOADD city 113.26 23.13 guangzhou
GEOADD city 114.06 22.54 shenzhen
GEOADD city 104.07 30.66 chengdu
GEOADD city 119.3 26.07 fuzhou
GEOADD city 118.78 32.06 nanjing
```

**搜索附近**：

```bash
# 距离上海半径200km内的城市（上海到南京距离 √）
GEOSEARCH city FROMMEMBER shanghai BYRADIUS 200 km

# 指定经纬度，5km范围内
GEOSEARCH city FROMLONLAT 121.445 31.213 BYRADIUS 5 km
```

---

## 十、Stream：Redis 的消息队列

> Redis 5 之前可以用 List 的 BLPOP 做"消息队列"，但那只是**简单实现**。真正的消息队列需要支持消费组、消息确认、消息回溯——这就是 Stream。

### 10.1 核心概念

| 概念 | 说明 | 类比 Kafka |
|------|------|-----------|
| Stream | 消息流（Key 的名称） | Topic |
| Message | 消息（field-value 对） | Record |
| Consumer Group | 消费组 | Consumer Group |
| Consumer | 消费者 | Consumer |
| `>` | 未投递的新消息 | — |
| `$` | 当前最新消息 | — |
| `$>` | 排除新的未送达消息 | — |
| PEL | 已送达但未确认的消息列表 | — |

### 10.2 指令速查

| 分类 | 指令 | 说明 |
|------|------|------|
| 生产 | `XADD key [NOMKSTREAM] [MAXLEN] id field value...` | 添加消息 |
| | `XADD key * field value...` | 自动生成ID |
| | `XTRIM key MAXLEN [~] count` | 按长度裁剪 |
| 消费 | `XREAD [COUNT c] [BLOCK ms] STREAMS key... id...` | 读消息 |
| | `XREADGROUP GROUP group consumer [COUNT c] [BLOCK ms] STREAMS key... id...` | 组消费 |
| 确认 | `XACK key group id...` | 消息确认 |
| | `XAUTOCLAIM key group consumer min-idle-time start-id [COUNT c]` | 自动认领超时消息 |
| 管理 | `XGROUP CREATE key group id\|$ [MKSTREAM]` | 创建消费组 |
| | `XGROUP DESTROY key group` | 删除消费组 |
| | `XGROUP SETID key group id\|$` | 设置消费位置 |
| | `XINFO STREAM key [FULL]` | 流信息 |
| | `XINFO GROUPS key` | 消费组信息 |
| | `XPENDING key group [[IDLE ms] start end count [consumer]]` | 待处理消息 |
| | `XDEL key id...` | 删除消息 |
| | `XRANGE key start end [COUNT count]` | 范围查询 |
| | `XREVRANGE key end start [COUNT count]` | 反向范围查询 |

**生产者示例**：

```bash
# * 号表示自动生成ID（毫秒时间戳-序号）
XADD mystream * field1 value1 field2 value2

# 限制最大长度（~ 近似删除，性能更好）
XADD mystream MAXLEN ~ 1000 * field1 value1
```

**消费者示例**：

```bash
# 独立消费（不需要消费组）
XREAD COUNT 2 STREAMS mystream 0   # 从最早开始
>XREAD COUNT 2 STREAMS mystream $   # 只等新消息

# 消费组模式
XGROUP CREATE mystream mygroup $ MKSTREAM

# 消费者A消费
XREADGROUP GROUP mygroup consumerA COUNT 1 STREAMS mystream >
XREADGROUP GROUP mygroup consumerB COUNT 1 STREAMS mystream >
XREADGROUP GROUP mygroup consumerC COUNT 1 STREAMS mystream >

# 查看确认情况
XPENDING mystream mygroup

# 确认消费
XACK mystream mygroup 1650000000000-0
```

### 10.3 应用场景

| 场景 | 推荐 |
|------|------|
| 轻量级消息队列 | Redis Stream（比 List 更可靠） |
| 重消息、高可靠 | RocketMQ / Kafka |
| 有 ACK 需求 | Stream（必须） |
| 有重试需求 | Stream + XAUTOCLAIM |

> Kafka 数据也存在硬盘上（日志文件），支持从任意位置消费；Redis Stream 数据主要在内存中，少量存盘备份。两者不矛盾，看场景选择。

---

## 十一、数据结构总结

| 类型 | 特性 | 典型场景 |
|------|------|---------|
| String | K-V，二进制安全 | 缓存、计数器、分布式锁 |
| Hash | 字段-值映射 | 对象存储、用户信息 |
| List | 有序可重复，双端操作 | 消息队列、最新列表 |
| Set | 无序去重，交并差集 | 标签、共同好友、抽奖 |
| ZSet | 带权排序 | 排行榜、延迟队列 |
| BitMap | 位操作 | 签到、布隆过滤器 |
| HyperLogLog | 基数估算(0.81%误差) | UV统计、大数据去重计数 |
| GEO | 地理位置 | 附近的人、LBS |
| Stream | 持久化消息流 | 可靠消息队列 |

> 理解每种数据结构的底层编码（intset/listpack/skiplist/quicklist/raw/embstr...）是面试中区分初中高级的分水岭。详见底层数据结构篇的完整分析。
