---
layout: post
title: "Redis缓存设计与性能优化：从理论到生产实践"
date: 2022-06-11
categories: [distributed]
tags: [Redis, 缓存设计, 缓存穿透, 缓存击穿, 缓存雪崩, 布隆过滤器, 性能优化, 连接池]
comments: true
---

> 缓存设计是 Redis 最核心的应用场景。本节从三大缓存问题出发，逐步深入到生产级别的优化策略。

---

## 一、缓存穿透

### 什么是缓存穿透

查询一个**根本不存在**的数据，缓存层和存储层都不会命中。通常出于**容错考虑**，如果从存储层查不到数据则不写入缓存层。

**危害**：这会导致不存在的数据每次请求都要到存储层查询，失去了缓存保护后端存储的意义。如果大量查询不存在的数据，缓存自身将失去价值。

### 解决方案一：缓存空对象

```java
// 伪代码
public String get(String key) {
    String value = redis.get(key);
    if (value == null) {
        value = db.get(key);       // 查DB
        if (value == null) {
            redis.set(key, "null", 300);  // 缓存空值，短期TTL
        } else {
            redis.set(key, value, 3600);
        }
    }
    return value;
}
```

**问题**：
- 空值做了缓存：缓存层存了更多键，需要更多内存（可以设较短过期时间）
- 数据不一致：缓存层和存储层会有一段时间窗口不一致（过期时间到期后重新加载）

### 解决方案二：布隆过滤器

**布隆过滤器本质**：一个**很长的二进制向量**和**一系列随机映射函数**。

```
添加元素步骤：
  1. 用 k 个 hash 函数分别计算
  2. 将结果对应的 k 个位置都设为 1

查询元素步骤：
  1. 用同样 k 个 hash 函数计算
  2. 检查所有位置是否都为 1
  3. 都为1 → 可能存在（有误判）
  4. 有0   → 一定不存在
```

**特点**：
- ✅ 查询高效
- ✅ 占用空间少
- ❌ **有误判率**（假阳性）
- ❌ **不能删除**（删除一个位置会误伤其他元素）

**两种实现**：

| | Google BloomFilter | Redis Bloom Filter |
|---|---|---|
| 基于 | JVM内存 | Redis |
| 特点 | 只能在本机 | 分布式可用 |
| 淘汰 | 重启即失 | 随Redis持久化 |

Redis Bloom Filter 指令：
```bash
BF.ADD bloomfilter1 "item1"
BF.EXISTS bloomfilter1 "item1"    # 返回 1 存在 / 0 不存在
BF.MADD bloomfilter1 "item2" "item3"
BF.MEXISTS bloomfilter1 "item1" "item2"
```

**最佳实践**：将**所有可能存在的数据哈希**放到足够大的 BitMap 中，一定不存在的数据直接被 BitMap 拦截。数据量给够大可有效降低误判率。

---

## 二、缓存击穿

### 什么是缓存击穿

数据库有但缓存没有（一般缓存到期），**高并发**时，同一个 key 被大量请求同时查询，这些请求全部打到 DB 上，DB 瞬时压力过大。

### 解决方案：互斥锁

核心思路：让**只有一个线程**去查DB并重建缓存，其他线程等待。

```java
// 互斥锁核心代码
public String get(String key) {
    String value = redis.get(key);
    
    // 缓存值过期（逻辑过期时间）
    if (value != null && isExpired(value)) {
        // 获取互斥锁（SET NX）
        if (redis.setnx(key + ":mutex", "1")) {
            redis.expire(key + ":mutex", 3 * 60);
            // 开新线程查DB并重建缓存
            executor.submit(() -> {
                String dbValue = db.get(key);
                redis.set(key, dbValue, 3600);
                redis.del(key + ":mutex");  // 释放锁
            });
        }
    }
    
    if (value == null) {
        // 缓存真的没有
        if (redis.setnx(key + ":mutex", "1")) {
            redis.expire(key + ":mutex", 3 * 60);
            value = db.get(key);
            redis.set(key, value, 3600);
            redis.del(key + ":mutex");
        } else {
            Thread.sleep(50);
            return get(key);  // 重试
        }
    }
    return value;
}
```

**SET NX 互斥锁注意点**：
- **一定要设过期时间**：否则持锁线程挂了 → 死锁
- 获取不到锁的线程→ 休眠重试 → 保证只有一个线程查 DB

**逻辑过期 vs 物理过期**：
- **物理过期**：TTL 到了就过期 → 击穿时查 DB（压力大）
- **逻辑过期**：TTL 到了不真正删除，标记过期 → 抢锁重建

---

## 三、缓存雪崩

### 什么是缓存雪崩

缓存层**大面积失效**，流量如雪崩打到 DB 层，存储层大量请求直接打爆。

**危害**：后端并发压力骤增，可能直接导致数据库宕机。

### 解决方案：缓存层高可用 + 限流降级

```
1. 保证缓存层高可用   → Redis Cluster / Sentinel
2. 后端限流降级       → Hystrix / Sentinel
3. 提前演练           → 压力测试了解承载能力
4. 分散过期时间       → 在基础过期时间上加随机偏移量
```

### 过期时间打散

```java
// 给过期时间加随机偏移，避免大批量key同时过期
int expireTime = baseTime + new Random().nextInt(300);  // 加 ±300s 随机偏移
redis.set(key, value, expireTime);
```

### 多级缓存策略

```
Nginx本地缓存 → Redis分布式缓存 → DB
      ↓              ↓            ↓
   热点key       常规数据      最终数据
```

| 方案 | 说明 |
|------|------|
| 事前 | 保证 Redis 高可用 + 数据预热 |
| 事中 | 本地 ehcache + hystrix 限流 |
| 事后 | Redis 持久化快速恢复 |

---

## 四、热点Key重建策略

当一个 key 是**热点**（数百万并发），在缓存失效瞬间，海量请求直接到 DB：

**核心思路**：
1. 互斥锁保证只有一个线程重建
2. **不等**：不等重建线程完成，超时返回
3. **逻辑过期**：物理 TTL 长，逻辑过期快

```java
public String queryWithLogicalExpire(String keyPrefix, Long id, 
        Class<R> type, Function<Long, R> dbFallback,
        Long time, TimeUnit unit) {
    
    String key = keyPrefix + id;
    String json = stringRedisTemplate.opsForValue().get(key);
    
    if (StrUtil.isBlank(json)) {
        return null;
    }
    
    // 反序列化
    RedisData redisData = JSONUtil.toBean(json, RedisData.class);
    R r = JSONUtil.toBean((JSONObject) redisData.getData(), type);
    LocalDateTime expireTime = redisData.getExpireTime();
    
    // 逻辑过期判断
    if (expireTime.isAfter(LocalDateTime.now())) {
        return r;  // 未过期直接返回
    }
    
    // 逻辑过期 → 尝试获取互斥锁
    String lockKey = LOCK_SHOP_KEY + id;
    boolean isLock = tryLock(lockKey);
    
    if (isLock) {
        // 获取锁成功 → 开新线程异步重建缓存
        CACHE_REBUILD_EXECUTOR.submit(() -> {
            try {
                R newR = dbFallback.apply(id);
                this.saveShop2Redis(id, 20L);  // 重建缓存
            } catch (Exception e) {
                throw new RuntimeException(e);
            } finally {
                unlock(lockKey);
            }
        });
    }
    
    // 返回旧的缓存数据（不等新数据）
    return r;
}
```

---

## 五、BigKey分析

### 多大数据算大？

基于《阿里开发者手册》：

| 维度 | 标准 |
|------|------|
| String | value > 10 KB |
| Hash/List/Set/ZSet | 元素 > 5000 个 |

### 危害

1. 超时阻塞：主线程单线程串行，操作大 key 让后面指令一直排队
2. 网络阻塞：单次网络传输流量大
3. **迁移困难**：大 key 迁移会**直接阻塞 Redis 主线程**！数据量大 + 频次高 = 雪上加霜

### 如何发现

```bash
redis-cli --bigkeys -i 0.1
# -i 0.1: 每隔100条scan指令休息0.1秒（减少ops）
# 本质：scan + strlen/llen/scard/hlen/zcard
```

注意事项：
- `--bigkeys` 扫描的是**元素数**，不是内存占用
- `--memkeys`: 扫描**内存占用**
- **建议在从节点执行**，避免增加主节点压力

### 如何删除

```bash
# 同步删除（阻塞）
DEL key

# 异步删除（Redis4.0+，不阻塞主线程）
UNLINK key
```

注意：`UNLINK` 不阻塞主线程，但后台线程仍需逐元素删除（释放内存），会带来额外的内存/CPU 资源消耗。

---

## 六、连接池数精确计算

### 经验公式

对于一个日均活跃连接数 Q 的服务：

```
最佳最大连接数 = ((core_count * 2) + effective_spindle_count)
```

其中：
- `core_count`: CPU 内核数
- `effective_spindle_count`: 磁盘有效轴数（SSD 有效轴数通常为 1）

**核心原则**：连接池不是越大越好。

- 连接数太小 → 连接不够用，频繁建立/关闭连接，获取连接超时
- 连接数太大 → CPU/Lua时间/带宽竞争，指令等待+网络阻塞，反而拖慢性能

### JedisPool 配置

需注意**预热操作**：在服务启动时定期发送 PING 命令，避免流量突变时连接数不够：

```java
@Component
public class PoolWarmup {
    @PostConstruct
    public void init() {
        // 启动时预热连接池
        for (int i = 0; i < 10; i++) {
            try (Jedis jedis = jedisPool.getResource()) {
                jedis.ping();
            }
        }
    }
}
```

---

## 七、淘汰策略详解

```conf
maxmemory 4gb                      # 最大内存
maxmemory-policy allkeys-lru       # 淘汰策略
```

### 八种淘汰策略

| 策略 | 行为 | 适用场景 |
|------|------|----------|
| `noeviction` | 不淘汰，超出报错 | 不允许数据丢失 |
| `allkeys-lru` | 所有 key 用 LRU | **通用推荐** |
| `volatile-lru` | 有过期时间的 key 用 LRU | |
| `allkeys-random` | 所有 key 随机淘汰 | |
| `volatile-random` | 有过期时间的 key 随机淘汰 | |
| `volatile-ttl` | 有过期时间且 TTL 最短优先 | |
| `allkeys-lfu` | 所有 key 用 LFU | 某时段热点 |
| `volatile-lfu` | 有过期时间用 LFU | 某时段热点 |

### LRU 优化版本 — 近似 LRU

Redis 不会对所有数据做精确 LRU（遍历所有 key 代价太高）。用**近似 LRU**：随机挑选 5 个 key（`maxmemory-samples` 控制），淘汰其中最久未使用的。

---

## 八、运维经验参数配置

### 慢查询监控

```bash
# 动态修改
CONFIG SET slowlog-log-slower-than 10000   # 10ms（微秒）
CONFIG SET slowlog-max-len 128

# 查看慢查询
SLOWLOG GET 5
SLOWLOG LEN
SLOWLOG RESET
```

**注意**：
- `slowlog-log-slower-than`：设置阈值时考虑并发情况，单个指令 1ms 很快，但 OPS 100000 时都排队就慢
- 多检查慢查询日志排查 BigKey、复杂度高的指令

### 客户端优化

```java
// Pipeline：减少 RTT
Pipeline pipeline = jedis.pipelined();
for (int i = 0; i < 100; i++) {
    pipeline.set("key" + i, "value" + i);
}
pipeline.sync();

// 避免使用 KEYS
// 错误：keys *
// 正确：SCAN 0 MATCH * COUNT 100
```

### 内核参数

```bash
# 内存分配策略优化
echo 'vm.overcommit_memory = 1' >> /etc/sysctl.conf

# TCP backlog
echo 511 > /proc/sys/net/core/somaxconn
```

---

## 九、总结

```
缓存穿透 → 缓存空值 / 布隆过滤器
缓存击穿 → 互斥锁（SET NX）
缓存雪崩 → 高可用 + 过期打散 + 多级缓存
热点Key → 逻辑过期 + 互斥锁 + 不等策略
BigKey  → --bigkeys 扫描 + UNLINK 删除
连接池  → 公式计算 + 预热
淘汰策略 → allkeys-lru 推荐
```

> 这些策略不是互斥的，生产环境通常**组合使用**。核心原则：**绝不让大量请求直接打到数据库**。
