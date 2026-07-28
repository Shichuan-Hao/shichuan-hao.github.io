---
layout: post
title: "Redis7核心数据结构实战"
date: 2022-06-08
categories: [distributed]
tags: [Redis, 数据结构, String, Hash, List, Set, ZSet, Stream]
comments: true
---

> 永远的神：`help @group` 指令

## String 结构

### 常用操作

| 指令 | 说明 |
|------|------|
| `SET key value` | 存入字符串键值对 |
| `MSET key value [key value ...]` | 批量存储 |
| `SETNX key value` | 不存在时存入 |
| `GET key` | 获取值 |
| `MGET key [key ...]` | 批量获取 |
| `DEL key [key ...]` | 删除键 |
| `EXPIRE key seconds` | 设置过期时间 |

### 原子加减

| 指令 | 说明 |
|------|------|
| `INCR key` | 加1 |
| `DECR key` | 减1 |
| `INCRBY key increment` | 加指定值 |
| `DECRBY key decrement` | 减指定值 |

### 常见应用场景

**1. 单值缓存**：
```
SET key value
APPEND key value
```

**2. 对象缓存**：
```
# JSON方式
set user:1 '{"name":"roy","balance":1888}'

# 多key方式
MSET user:1:name roy user:1:balance 1888
MGET user:1:name user:1:balance
```

**3. 分布式锁**：
```
SETNX product:10001 true    # 获取锁（返回1成功，0失败）
...执行业务操作...
DEL product:10001           # 释放锁

# 防止死锁的改进写法
SET product:10001 true ex 10 nx
```

---

## Hash 结构

### 常用操作

| 指令 | 说明 |
|------|------|
| `HSET key field value` | 存储哈希表键值 |
| `HSETNX key field value` | 不存在时才存储 |
| `HMSET key field value [field value ...]` | 批量存储 |
| `HGET key field` | 获取field值 |
| `HMGET key field [field ...]` | 批量获取 |
| `HDEL key field [field ...]` | 删除field |
| `HLEN key` | field数量 |
| `HGETALL key` | 获取所有键值 |
| `HINCRBY key field increment` | 原子加减 |

### 应用场景：电商购物车

```
用户id → key
商品id → field
商品数量 → value

hset cart:1001 10088 1        # 添加商品
hincrby cart:1001 10088 1     # 增加数量
hlen cart:1001                # 商品总数
hdel cart:1001 10088          # 删除商品
hgetall cart:1001             # 获取所有商品
```

### Hash 优缺点

| 优点 | 缺点 |
|------|------|
| 同类数据归类整合，方便管理 | 过期功能只能用在 key 上，不能用在 field 上 |
| 相比 String 操作消耗内存与 CPU 更小 | **集群架构下不适合大规模使用**（可能数据倾斜） |
| 相比 String 储存更节省空间 | |

---

## List 类型

### 常用操作

| 指令 | 说明 |
|------|------|
| `LPUSH key value [value ...]` | 表头（左）插入 |
| `RPUSH key value [value ...]` | 表尾（右）插入 |
| `LPOP key` | 移除并返回头元素 |
| `RPOP key` | 移除并返回尾元素 |
| `LRANGE key start stop` | 返回指定区间元素 |
| `BLPOP key [key ...] timeout` | 阻塞式头弹出 |
| `BRPOP key [key ...] timeout` | 阻塞式尾弹出 |

### 常用数据结构组合

```
Stack（栈）        = LPUSH + LPOP
Queue（队列）      = LPUSH + RPOP
Blocking MQ（阻塞队列） = LPUSH + BRPOP
```

### 应用场景

- 视频列表、签到列表
- 排队机
- 简化版消息队列（MQ）

### 注意点

1. List 容量上限是 2^32 - 1（约 40 多亿个元素），但要注意 **BigKey 问题**
2. List 底层是**双向链表**，双端操作性能高；通过索引操作中间节点性能低

---

## Set 类型

### 常用操作

| 指令 | 说明 |
|------|------|
| `SADD key member [member ...]` | 添加元素（存在则忽略） |
| `SREM key member [member ...]` | 删除元素 |
| `SMEMBERS key` | 获取所有元素 |
| `SCARD key` | 元素个数 |
| `SISMEMBER key member` | 判断是否存在 |
| `SRANDMEMBER key [count]` | 随机选 count 个（不删除） |
| `SPOP key [count]` | 随机弹出 count 个（删除） |

### 集合运算

| 运算 | 指令 | 存储结果 |
|------|------|----------|
| 交集 | `SINTER key [key ...]` | `SINTERSTORE dest key [key ...]` |
| 并集 | `SUNION key [key ...]` | `SUNIONSTORE dest key [key ...]` |
| 差集 | `SDIFF key [key ...]` | `SDIFFSTORE dest key [key ...]` |

### 应用场景

**1. 微信抽奖小程序**：
```
SADD key {userID}                        # 参与抽奖
SMEMBERS key                             # 查看所有参与用户
SRANDMEMBER key [count] / SPOP key [count]  # 抽取中奖者
```

**2. 微信微博点赞/收藏/标签**：
```
SADD like:{消息ID} {用户ID}     # 点赞
SREM like:{消息ID} {用户ID}     # 取消点赞
SISMEMBER like:{消息ID} {用户ID} # 检查是否点赞
SMEMBERS like:{消息ID}          # 获取点赞列表
SCARD like:{消息ID}             # 点赞数
```

**3. 社交关系**：
```
SINTER set1 set2 set3 → { c }      # 共同关注
SUNION set1 set2 set3 → { a,b,c,d,e }  # 朋友圈
SDIFF set1 set2 set3 → { a }       # 推荐好友
```

---

## ZSet 有序列表类型

### 常用操作

| 指令 | 说明 |
|------|------|
| `ZADD key score member [[score member]…]` | 添加带分值元素 |
| `ZREM key member [member …]` | 删除元素 |
| `ZSCORE key member` | 返回分值 |
| `ZINCRBY key increment member` | 增加分值 |
| `ZCARD key` | 元素个数 |
| `ZRANGE key start stop [WITHSCORES]` | 正序获取 |
| `ZREVRANGE key start stop [WITHSCORES]` | 倒序获取 |

### 集合运算

```
ZUNIONSTORE destkey numkeys key [key ...]  # 并集
ZINTERSTORE destkey numkeys key [key …]    # 交集
```

### 应用场景：排行榜

```
# 点击新闻加热度
ZINCRBY hotNews:20190819 1 守护香港

# 当日排行前十
ZREVRANGE hotNews:20190819 0 9 WITHSCORES

# 七日搜索榜单计算（合并7天数据）
ZUNIONSTORE hotNews:20190813-20190819 7 hotNews:20190813 ... hotNews:20190819

# 展示七日排行前十
ZREVRANGE hotNews:20190813-20190819 0 9 WITHSCORES
```

---

## Bitmap 类型

### 常用操作

| 指令 | 说明 |
|------|------|
| `SETBIT key offset value` | 将 offset 位置设为 0/1 |
| `GETBIT key offset` | 获取 offset 位置的值 |
| `BITCOUNT key [start end]` | 统计 1 的个数 |
| `BITPOS key bit [start [end]]` | 返回第一个值为 bit 的 offset |
| `BITOP AND\|OR\|XOR\|NOT destkey key [key ...]` | 二进制位运算 |

### 应用场景：每日签到

```
SETBIT dailycheck:1 100 1    # 1号用户第100天签到
BITCOUNT dailycheck:1        # 统计签到次数
BITPOS dailycheck:1 1        # 第一天签到的时间
```

**优点**：快速、高效、节省空间

---

## Hyperloglog 类型

**作用**：统计一个集合中**不重复元素个数**（典型场景：UV 统计）

```
PFADD visitlog 192.168.65.111 192.168.65.112 192.168.65.111
PFCOUNT visitlog                              # 统计独立访客
PFMERGE destkey [sourcekey [sourcekey ...]]   # 合并多条记录
```

---

## Geo 类型

### 常用操作

```
GEOADD key longitude latitude member [...]       # 添加地点
GEOPOS key [member ...]                          # 返回经纬度
GEODIST key member1 member2 [M|KM|FT|MI]         # 计算距离
GEORADIUS key lon lat radius unit [...]          # 按半径查询附近
GEOSEARCH key FROMMEMBER member BYRADIUS ...     # 查询附近地点
```

### 应用场景示例

```
GEOADD changsha 113.017489 28.200454 火车站 112.96903 28.201195 橘子洲
GEODIST changsha 火车站 橘子洲 M                    # 查询距离
GEORADIUSBYMEMBER changsha 火车站 2 KM withdist withcoord count 4  # 附近景点
```

---

## Stream 类型

**作用**：Redis 版 MQ = 阻塞队列 + pub/sub

**注意**：了解即可，企业应用中较少使用。

### 常用操作

```
XADD key * field value [field value ...]          # 发布消息（* 自动生成ID）
XDEL key id [id ...]                              # 删除消息
XLEN key                                          # 队列长度
XRANGE key start end [COUNT count]                # 查询消息

# 消费者组
XGROUP CREATE mystream groupA 0                   # 0从头部开始消费，$从尾部
XREADGROUP GROUP groupA consumer1 count 2 STREAMS mystream >
XPENDING mystream groupA                          # 查看消费进度
```

---

## 补充：SpringBoot 集成 Redis

**Maven 依赖**：
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
```

**核心配置**：
```yaml
spring:
  data:
    redis:
      host: 192.168.65.214
      port: 6379
      password: 123qweasd
```

**RedisTemplate 快速上手**：

```java
@Resource
private RedisTemplate<String,Object> redisTemplate;

// 按组操作
redisTemplate.opsForValue().xxx      // String类型
redisTemplate.opsForSet().xxx        // Set类型
redisTemplate.opsForHash().xxx       // Hash类型
redisTemplate.opsForList().xxx       // List类型
redisTemplate.opsForZSet().xxx       // ZSet类型
redisTemplate.opsForGeo().xxx        // Geo类型
redisTemplate.opsForHyperLogLog().xxx // HyperLogLog类型
redisTemplate.opsForStream().xxx     // Stream类型
redisTemplate.opsForValue().setBit() // Bitmap类型
```

**中文乱码问题**：
```java
@Bean
public RedisTemplate<String,Object> redisTemplate(RedisConnectionFactory factory){
    RedisTemplate<String, Object> redisTemplate = new RedisTemplate<>();
    redisTemplate.setConnectionFactory(factory);
    
    StringRedisSerializer stringRedisSerializer = new StringRedisSerializer();
    GenericToStringSerializer<String> genericToStringSerializer = 
        new GenericToStringSerializer<>(String.class);
    
    redisTemplate.setKeySerializer(stringRedisSerializer);
    redisTemplate.setValueSerializer(genericToStringSerializer);
    redisTemplate.setHashKeySerializer(stringRedisSerializer);
    redisTemplate.setHashValueSerializer(stringRedisSerializer);
    redisTemplate.afterPropertiesSet();
    return redisTemplate;
}
```

> 理解 → 熟练 → 记忆
