---
title: "Redis 缓存设计与性能优化实战手册"
date: 2022-06-11
categories: distributed
tags: [Redis, 缓存穿透, 缓存击穿, 缓存雪崩, BigKey, 布隆过滤器, 连接池, 性能调优]
mermaid: true
---

> 不仅要会用 Redis，更要把缓存设计好。本章从缓存三大经典问题出发，涵盖键值设计规范、命令使用、客户端调优、内核参数、内存淘汰策略等完整实践指南。

## 一、多级缓存架构

在大型互联网系统中，缓存不是单一的 Redis 层，而是多级架构：

```
客户端 → CDN → Nginx本地缓存 → Redis分布式缓存 → 数据库
```

每一层的命中率直接决定了系统的吞吐量。本章聚焦 **Redis 缓存层**的设计与优化。

---

## 二、缓存穿透

### 问题描述

查询一个**根本不存在**的数据，缓存层和存储层都不会命中。通常出于容错的考虑，如果从存储层查不到数据就不写入缓存层。结果：不存在的数据每次请求都要打到数据库，失去了缓存保护后端存储的意义。

**原因**：
1. 自身业务代码或数据出现问题（如用错 key 前缀）
2. 恶意攻击、爬虫等造成大量空命中

### 方案一：缓存空对象

```java
String get(String key) {
    // 从缓存中获取数据
    String cacheValue = cache.get(key);
    // 缓存为空
    if (StringUtils.isBlank(cacheValue)) {
        // 从存储中获取
        String storageValue = storage.get(key);
        cache.set(key, storageValue);
        // 如果存储数据为空，需要设置一个过期时间(300秒)
        if (storageValue == null) {
            cache.expire(key, 60 * 5);
        }
        return storageValue;
    } else {
        // 缓存非空
        return cacheValue;
    }
}
```

**关键点**：即使是 null 值也要缓存，但必须设**较短的过期时间**（如 300 秒），防止缓存层被大量 null 值占满。

### 方案二：布隆过滤器

> 当布隆过滤器说某个值存在时，这个值**可能**不存在；当它说**不存在**时，那就**肯定不存在**。

**原理**：布隆过滤器是一个大型的**位数组** + 多个**无偏 hash 函数**（无偏是指 hash 值算得比较均匀）。

**添加 key**：使用多个 hash 函数对 key 进行 hash，对位数组长度取模得到多个位置，将这些位置全部置为 1。

**查询 key**：同样算出多个位置，检查是否都为 1：
- 只要有一个位为 0 → key **肯定不存在**
- 所有位都为 1 → key **可能存在**（可能被其他 key 污染）

> 位数组越稀疏，误判概率越低；位数组越拥挤，误判概率越高。

**Redisson 实现**：

```java
// 引入依赖
// <dependency>
//     <groupId>org.redisson</groupId>
//     <artifactId>redisson</artifactId>
//     <version>3.6.5</version>
// </dependency>

public class RedissonBloomFilter {
    public static void main(String[] args) {
        Config config = new Config();
        config.useSingleServer().setAddress("redis://localhost:6379");
        RedissonClient redisson = Redisson.create(config);

        RBloomFilter<String> bloomFilter = redisson.getBloomFilter("nameList");
        // 初始化：预计元素1亿, 误差率3%
        // 根据这两个参数会自动计算底层 bit 数组大小
        bloomFilter.tryInit(100000000L, 0.03);

        bloomFilter.add("zhuge");

        System.out.println(bloomFilter.contains("guojia")); // false
        System.out.println(bloomFilter.contains("baiqi"));  // false
        System.out.println(bloomFilter.contains("zhuge"));  // true
    }
}
```

**布隆过滤器 + 缓存联合使用**：

```java
// 初始化：把所有已有数据放入布隆过滤器
RBloomFilter<String> bloomFilter = redisson.getBloomFilter("nameList");
bloomFilter.tryInit(100000000L, 0.03);

void init() {
    for (String key : keys) {
        bloomFilter.put(key);
    }
}

String get(String key) {
    // 第一层：布隆过滤器判断 key 是否存在
    Boolean exist = bloomFilter.contains(key);
    if (!exist) {
        return "";   // 直接拦截，不查缓存也不查数据库
    }
    // 第二层：查缓存
    String cacheValue = cache.get(key);
    if (StringUtils.isBlank(cacheValue)) {
        String storageValue = storage.get(key);
        cache.set(key, storageValue);
        if (storageValue == null) {
            cache.expire(key, 60 * 5);
        }
        return storageValue;
    } else {
        return cacheValue;
    }
}
```

**适用场景**：数据命中不高、数据相对固定、实时性低（通常是数据集较大）。代码维护较复杂，但缓存空间占用很少。

> ⚠️ 注意：布隆过滤器**不能删除数据**，要删除得重新初始化全部数据。

---

## 三、缓存失效（击穿）

### 问题描述

大批量缓存在**同一时间失效**，导致大量请求同时穿透缓存直达数据库，可能造成数据库瞬间压力过大甚至挂掉。

### 解决方案：过期时间随机化

```java
String get(String key) {
    String cacheValue = cache.get(key);
    if (StringUtils.isBlank(cacheValue)) {
        String storageValue = storage.get(key);
        cache.set(key, storageValue);
        // 过期时间：300~600 秒之间的随机数
        int expireTime = new Random().nextInt(300) + 300;
        if (storageValue == null) {
            cache.expire(key, expireTime);
        }
        return storageValue;
    } else {
        return cacheValue;
    }
}
```

核心思路：**批量增加缓存时，将过期时间打散**，避免集中过期形成"缓存风暴"。

---

## 四、缓存雪崩

### 问题描述

缓存层支撑不住或宕掉后，流量像奔逃的野牛一样打向后端存储层。缓存层由于某些原因不能提供服务（超大并发、bigkey、缓存设计不好），大量请求直接打到存储层，造成存储层级联宕机。

### 三层防护策略

**1. 保证缓存层服务高可用**

使用 Redis Sentinel 或 Redis Cluster 部署，确保缓存层本身不会单点故障。

**2. 依赖隔离 + 限流熔断降级**

使用 Sentinel（阿里）或 Hystrix 限流降级组件。服务降级策略：

| 数据类型 | 降级方式 |
|---------|---------|
| 非核心数据（商品属性、用户信息） | 直接返回预定义的默认值、空值或错误提示 |
| 核心数据（商品库存） | 允许查缓存，缓存缺失时可走数据库 |

**3. 提前演练**

项目上线前，模拟缓存层宕掉后的负载情况，制定预案。

---

## 五、热点缓存 Key 重建优化

### 致命场景

两个条件同时出现时：
1. 当前 key 是一个**热点 key**（热门娱乐新闻），并发量非常大
2. 重建缓存**不能短时间完成**（复杂 SQL、多次 IO、多个依赖）

结果：缓存失效瞬间，**大量线程同时重建缓存**，后端负载暴增，甚至应用崩溃。

### 解决方案：互斥锁（SET NX）

```java
String get(String key) {
    // 从 Redis 中获取数据
    String value = redis.get(key);
    // 如果 value 为空，则开始重构缓存
    if (value == null) {
        // 只允许一个线程重建缓存，使用 NX 并设置过期时间 EX
        String mutexKey = "mutext:key:" + key;
        if (redis.set(mutexKey, "1", "ex 180", "nx")) {
            // 获得锁 → 从数据源获取数据
            value = db.get(key);
            // 回写 Redis，并设置过期时间
            redis.setex(key, timeout, value);
            // 删除互斥锁
            redis.delete(mutexKey);
        } else {
            // 未获得锁 → 休息 50 毫秒后重试
            Thread.sleep(50);
            get(key);  // 递归重试
        }
    }
    return value;
}
```

**关键设计点**：
- `SET mutexKey 1 EX 180 NX`：三个特性合而为一（原子操作）
  - `NX`：只有 key 不存在时才设置成功（互斥）
  - `EX 180`：180 秒过期，防止死锁
- 未拿到锁的线程 `sleep(50)` 后重试，避免 CPU 空转
- 重建完成后**主动删除互斥锁**，让等待线程可以读到新缓存

---

## 六、缓存与数据库双写不一致

### 两种不一致场景

1. **双写不一致**：先更新数据库成功，再更新缓存时失败 → 读到旧缓存
2. **读写并发不一致**：线程 A 读缓存未命中 → 查数据库 → 线程 B 更新了数据库和缓存 → 线程 A 将旧值写入缓存

### 分级解决方案

| 级别 | 场景 | 方案 |
|------|------|------|
| 低并发 | 个人订单、用户数据 | 几乎不需要考虑，加过期时间即可 |
| 高并发但可容忍短暂不一致 | 商品名称、分类菜单 | 过期时间 + 主动更新 |
| 高并发且不能容忍不一致 | 库存、金额 | 分布式读写锁 + 队列化 |
| 最终一致性 | 非实时场景 | Canal 监听 binlog 异步更新缓存 |

### 重要认知

> 放入缓存的数据应该是对**实时性、一致性要求不是很高**的数据。**切记不要为了用缓存，同时又要保证绝对的一致性做大量的过度设计和控制，增加系统复杂性！**

如果写多读多又不能容忍缓存数据不一致，那就**没必要加缓存了**，直接操作数据库。如果数据库扛不住压力，可以把缓存作为数据读写的主存储，异步同步到数据库（数据库仅作备份）。

---

## 七、开发规范与性能优化

### 7.1 键值设计

#### Key 名设计

| 规则 | 说明 | 示例 |
|------|------|------|
| 【建议】可读性和可管理性 | 业务名(库名)为前缀，冒号分隔 | `trade:order:1` |
| 【建议】简洁性 | 控制 key 长度，内存占用不容忽视 | `u:{uid}:fr:m:{mid}` 代替 `user:{uid}:friends:messages:{mid}` |
| 【强制】不包含特殊字符 | 空格、换行、引号、转义字符 | ❌ |

#### Value 设计

**【强制】拒绝 BigKey**

BigKey 的定义：

| 类型 | BigKey 标准 |
|------|------------|
| String | 单个 value **超过 10KB** |
| Hash/List/Set/ZSet | 元素个数**超过 5000** |

> 反例：一个包含 200 万个元素的 List。

**BigKey 的三大危害**：

**1. Redis 阻塞**

删除 BigKey 时，Redis 是单线程的，一个 `DEL` 操作可能阻塞数秒。非字符串的 BigKey **不要用 del 删除**，使用 `HSCAN`、`SSCAN`、`ZSCAN` 渐进式删除。

特别注意：一个 200 万元素的 ZSet 设置 1 小时过期，过期时触发的自动 `DEL` 操作也会造成阻塞。Redis 4.0 引入 `lazyfree-lazy-expire yes` 可异步删除，避免此问题。

**2. 网络拥塞**

假设一个 BigKey 为 1MB，客户端每秒访问 1000 次：
```
1MB × 1000 = 1000MB/s = 8Gbps
```

普通千兆网卡（128MB/s）直接被击穿。服务器通常是**单机多实例**部署，一个 BigKey 可能影响同机其他实例。

**3. 过期删除阻塞**

**BigKey 产生场景**：

| 场景 | 示例 |
|------|------|
| 社交类 | 明星/大 V 的粉丝列表（不精心设计必是 BigKey） |
| 统计类 | 按天存储功能用户集合（用户量上来后必是 BigKey） |
| 缓存类 | 从数据库 load 所有字段序列化到一个 key；关联数据也存一起 |

**BigKey 优化策略**：

1. **拆**：
   - Big List → `list1`, `list2`, ... `listN`
   - Big Hash → 分段存储，如 100 万用户数据拆为 200 个 key，每个放 5000 条
2. **择优操作**：用 `HMGET` 而不是 `HGETALL`，用优雅方式删除

**【推荐】选择合适的数据类型**

```java
// ❌ 反例：多个 String key
set user:1:name tom
set user:1:age 19
set user:1:favor football

// ✅ 正例：一个 Hash
hmset user:1 name tom age 19 favor football
```

**【推荐】控制 key 的生命周期**

Redis 不是垃圾桶！建议使用 `expire` 设置过期时间，条件允许打散过期时间防止集中过期。

### 7.2 命令使用规范

**1. O(N) 命令关注 N 的数量**

`HGETALL`、`LRANGE`、`SMEMBERS`、`ZRANGE`、`SINTER` 并非不能用，但需要**明确 N 的值**。有遍历需求使用 `HSCAN`、`SSCAN`、`ZSCAN` 代替。

**2. 禁用危险命令**

```bash
rename-command KEYS ""
rename-command FLUSHDB ""
rename-command FLUSHALL ""
```

线上禁止使用 `KEYS`、`FLUSHALL`、`FLUSHDB`，通过 rename 机制禁用，或用 `SCAN` 渐进式处理。

**3. 合理使用 select**

Redis 多数据库较弱，用数字区分，很多客户端支持较差。多业务用多数据库实际还是**单线程处理**，会有干扰。建议**多个业务拆分到不同实例**。

**4. 批量操作提高效率**

| 方式 | 说明 |
|------|------|
| 原生命令 | `MGET`、`MSET`，**原子操作** |
| Pipeline | 打包多个不同命令，**非原子操作** |

控制一次批量操作的**元素个数在 500 以内**（实际也和元素字节数有关）。

| 对比 | 原生命令 | Pipeline |
|------|---------|----------|
| 原子性 | 原子 | 非原子 |
| 命令类型 | 必须相同命令 | 可以混合不同命令 |
| 支持 | 服务端支持 | 需要客户端+服务端同时支持 |

**5. Redis 事务**

Redis 事务功能较弱（不支持回滚），不建议过多使用，可以用 **Lua 脚本**替代。

### 7.3 客户端使用

**1. 避免多个应用使用一个 Redis 实例**

正例：不相干的业务拆分，公共数据做服务化。

**2. 使用连接池**

```java
JedisPoolConfig jedisPoolConfig = new JedisPoolConfig();
jedisPoolConfig.setMaxTotal(5);
jedisPoolConfig.setMaxIdle(2);
jedisPoolConfig.setTestOnBorrow(true);

JedisPool jedisPool = new JedisPool(jedisPoolConfig, "192.168.0.60", 6379, 3000, null);

Jedis jedis = null;
try {
    jedis = jedisPool.getResource();
    jedis.executeCommand();
} catch (Exception e) {
    logger.error("op key {} error: " + e.getMessage(), key, e);
} finally {
    if (jedis != null)
        jedis.close();  // 注意：不是关闭连接，而是归还到连接池
}
```

**连接池参数详解**：

| 参数 | 含义 | 默认值 | 建议 |
|------|------|--------|------|
| `maxTotal` | 最大连接数 | 8 | 按 QPS 计算 |
| `maxIdle` | 最大空闲连接数 | 8 | 按 QPS 计算 |
| `minIdle` | 最小空闲连接数 | 0 | 需预热 |
| `blockWhenExhausted` | 池耗尽时是否等待 | true | 保持默认 |
| `maxWaitMillis` | 最大等待时间(ms) | -1(永不超时) | **不建议默认** |
| `testOnBorrow` | 借用时检测有效性(ping) | false | 高并发设为 false |
| `testOnReturn` | 归还时检测有效性(ping) | false | 高并发设为 false |
| `jmxEnabled` | 是否开启 JMX 监控 | true | 建议开启 |

**连接池大小精确计算公式**：

```
假设：
  - 一次命令平均耗时 ≈ 1ms（borrow + 命令 + 网络 + return）
  - 一个连接的 QPS ≈ 1000/1 = 1000
  - 业务期望 QPS = 50000

理论连接数 = 50000 / 1000 = 50 个
实际 maxTotal = 50 × 1.5~2 = 75~100（预留余量）
```

> ⚠️ 注意：`nodes(应用个数) × maxTotal` 不能超过 Redis 的 `maxclients`。连接数太大不仅占用资源，而且对于 Redis 这种高 QPS 服务器，一个大命令的阻塞即使再大的连接池也无济于事。

**maxIdle 和 minIdle 的关系**：

- `maxIdle` 才是业务真正需要的最大连接数，`maxTotal` 是给余量。最佳性能是 `maxTotal = maxIdle`（避免连接池伸缩的性能干扰）
- `minIdle` 更准确说是"至少需要保持的空闲连接数"
- 如果系统启动完马上就有大量请求，需要做**连接池预热**

**连接池预热代码**：

```java
List<Jedis> minIdleJedisList = new ArrayList<Jedis>(jedisPoolConfig.getMinIdle());

for (int i = 0; i < jedisPoolConfig.getMinIdle(); i++) {
    Jedis jedis = null;
    try {
        jedis = pool.getResource();
        minIdleJedisList.add(jedis);
        jedis.ping();
    } catch (Exception e) {
        logger.error(e.getMessage(), e);
    } finally {
        // 注意：这里不能马上 close，否则连接池里始终只有 1 个连接
    }
}
// 统一将预热的连接归还回连接池
for (int i = 0; i < jedisPoolConfig.getMinIdle(); i++) {
    Jedis jedis = minIdleJedisList.get(i);
    jedis.close();
}
```

**3. 高并发下添加熔断功能**

建议客户端添加熔断功能（Sentinel、Hystrix），防止缓存故障拖垮整个服务。

**4. 设置合理的密码**

如有必要，使用 SSL 加密访问。

### 7.4 内存淘汰策略

Redis 对过期键的三种清除策略：

| 策略 | 描述 |
|------|------|
| **被动删除** | 读/写已过期 key 时触发惰性删除 |
| **主动删除** | 定期主动淘汰一批已过期 key（冷数据无法被惰性删除覆盖） |
| **内存超限淘汰** | 已用内存超过 `maxmemory` 时触发 |

**8 种淘汰策略**（Redis 4.0+）：

| # | 策略 | 说明 |
|---|------|------|
| 1 | `volatile-ttl` | 删除**最早过期**的 key |
| 2 | `volatile-random` | 随机删除**有 TTL** 的 key |
| 3 | `volatile-lru` | LRU 删除**有 TTL** 的 key |
| 4 | `volatile-lfu` | LFU 删除**有 TTL** 的 key |
| 5 | `allkeys-random` | 随机删除**所有** key |
| 6 | `allkeys-lru` | LRU 删除**所有** key |
| 7 | `allkeys-lfu` | LFU 删除**所有** key |
| 8 | `noeviction` | **不删除**，写操作报错 `OOM command not allowed` |

**LRU vs LFU**：

| 算法 | 参考维度 | 适用场景 |
|------|---------|---------|
| LRU（最近最少使用） | 最近一次访问**时间** | 热点数据明显 |
| LFU（最不经常使用） | 最近一段时间访问**次数** | 避免周期性批量操作污染 |

> 偶发性、周期性的批量操作会导致 LRU 命中率急剧下降（缓存污染），这时 LFU 可能更好。

**推荐配置**：
- `maxmemory-policy volatile-lru`（默认是 `noeviction`）
- 必须设置 `maxmemory`，否则内存超出物理限制时会触发 swap，Redis 性能急剧下降
- 主从模式：只有**主节点**执行过期删除策略，然后 `DEL key` 同步到从节点

---

## 八、系统内核参数优化

### 8.1 vm.swappiness

`swappiness` 决定操作系统使用 swap 的倾向程度（0~100）：
- 值越大，越倾向于使用 swap
- 值越小，越倾向于使用物理内存

```
# 查看内核版本
cat /proc/version

# 内核 < 3.5：设置为 0（宁愿 swap 也不会 OOM killer）
# 内核 >= 3.5：设置为 1（宁愿 swap 也不会 OOM killer）
echo 1 > /proc/sys/vm/swappiness
echo vm.swappiness=1 >> /etc/sysctl.conf
```

> OOM killer：Linux 发现可用内存不足时，强制杀死用户进程来保证系统有足够内存。

### 8.2 vm.overcommit_memory

| 值 | 含义 |
|---|------|
| 0 | 内核检查**是否有足够可用物理内存**；不足时申请失败 |
| 1 | 允许分配**所有物理内存**，不管当前内存状态 |

Redis 建议设为 **1**，让 fork 操作在低内存下也能成功执行：

```bash
echo "vm.overcommit_memory=1" >> /etc/sysctl.conf
sysctl vm.overcommit_memory=1
```

### 8.3 文件句柄数

```
# 查看当前限制
ulimit -a  # 查看 open files 项

# 设置上限（避免 "Too many open files" 错误）
ulimit -n 65535
```

---

## 九、慢查询日志（slowlog）

```bash
# 查询有关慢日志的配置
config get slow*

# 设置慢日志时间阈值（单位：微秒）
# 此处 20000 = 20ms，超过 20ms 的操作都会记录
# 生产环境建议 1000（1ms），若单机并发 > 1万 可设为 100
config set slowlog-log-slower-than 20000

# 设置慢日志保存数量，满时删除最早的记录
# 建议设置稍大些，防止丢失日志（长命令会被截断，不占太多内存）
config set slowlog-max-len 1024

# 持久化当前配置到 redis.conf
config rewrite

# 获取慢查询日志当前长度
slowlog len

# 获取最新 5 条慢查询（每条含：ID、时间戳、耗时、命令和参数）
slowlog get 5

# 重置慢查询日志
slowlog reset
```

---

## 十：总结

| 维度 | 核心要点 |
|------|---------|
| 缓存穿透 | 缓存空对象（短过期）+ 布隆过滤器（不存在的一定拦截） |
| 缓存击穿 | 过期时间加随机值，打散集中失效 |
| 缓存雪崩 | 缓存高可用 + 限流熔断降级 + 提前演练 |
| 热点 Key | 互斥锁（SET NX），只让一个线程重建 |
| BigKey | 拆分成小 key，渐进式删除，避免全量操作 |
| 连接池 | maxTotal = QPS / 单连接QPS × 1.5，minIdle 预热 |
| 内存淘汰 | 建议 volatile-lru，必须设 maxmemory |
| 内核参数 | swappiness=1, overcommit_memory=1, 文件句柄 65535 |
| 慢查询 | 生产建议阈值 1ms(1000微秒)，定期检查 slowlog |

> 缓存设计的核心原则：对实时性和一致性要求不高的数据才适合放入缓存。不要为了用缓存而做过度的设计！
