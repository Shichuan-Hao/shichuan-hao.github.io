---
layout: post
title: "Redis缓存设计与性能优化（进阶篇）：多级缓存架构与生产级监控"
date: 2022-06-13
categories: [distributed]
tags: [Redis, 多级缓存, 一致性, 缓存监控, 缓存预热, 生产优化]
comments: true

---

## 一、多级缓存架构

### 为什么需要多级缓存？

单个 Redis 扛不住百万 QPS → 需要分层：

```
请求 → Nginx本地缓存(L1) → Redis集群(L2) → 数据库(L3)
        命中率~80%           命中率~15%        最终数据
```

### L1：Nginx 本地缓存

```nginx
# nginx.conf
proxy_cache_path /data/nginx/cache levels=1:2 keys_zone=my_cache:100m;

location /api/ {
    proxy_cache my_cache;
    proxy_cache_valid 200 10s;           # 200 响应缓存 10 秒
    proxy_cache_key $uri$is_args$args;   # 缓存键
    add_header X-Cache-Status $upstream_cache_status;
}
```

### L2：Redis 分布式缓存

标准模式，见基础篇。

### L3：数据库

- 读写分离（主库写、从库读）
- 连接池优化

---

## 二、缓存预热

### 为什么需要预热？

新系统上线 / 缓存清空后 → 大量请求直接打 DB → 可能击穿。

```java
@Component
public class CacheWarmUp implements ApplicationRunner {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    @Autowired
    private ProductService productService;
    
    @Override
    public void run(ApplicationArguments args) {
        // 批量加载热点数据
        List<Product> hotProducts = productService.findHotProducts(10000);
        hotProducts.forEach(p -> 
            redisTemplate.opsForValue().set(
                "product:" + p.getId(), p, 24, TimeUnit.HOURS
            )
        );
    }
}
```

**预热策略**：
- 系统启动时加载历史热点数据
- 定时任务刷新热点数据
- 大促前提前加载

---

## 三、缓存一致性方案

### Cache-Aside Pattern（最常用）

```java
// 读：先查缓存，miss 查 DB，写回缓存
public Product getProduct(Long id) {
    Product p = redis.get("product:" + id);
    if (p == null) {
        p = db.findById(id);
        if (p != null) {
            redis.set("product:" + id, p, 3600);
        }
    }
    return p;
}

// 写：先更新 DB，再删除缓存
@Transactional
public void updateProduct(Product p) {
    db.update(p);
    redis.del("product:" + p.getId());
}
```

**为什么是删除缓存而不是更新缓存？**
- 更新 → 可能存在并发写顺序问题
- 删除 → 下次读自动重建，更安全

### 延迟双删

```java
@Transactional
public void updateProduct(Product p) {
    redis.del("product:" + p.getId());    // (1) 先删缓存
    db.update(p);                           // (2) 更新DB
    try { Thread.sleep(500); } catch (Exception e) {}
    redis.del("product:" + p.getId());    // (3) 延迟再删
}
```

> 保证并发读请求不会把旧数据写回缓存。

---

## 四、Redis 性能监控指标

### 关键指标

```bash
# 命中率（最重要的指标！）
INFO stats
  keyspace_hits: 985000
  keyspace_misses: 15000
  # 命中率 = 985000 / (985000+15000) = 98.5%

# 内存
INFO memory
  used_memory_human: 2.5G
  mem_fragmentation_ratio: 1.05   # 碎片率，>1.5 需关注

# 连接数
INFO clients
  connected_clients: 150
  blocked_clients: 0              # >0 表示有阻塞操作

# 慢查询
SLOWLOG GET 10
```

### 监控告警规则

| 指标 | 阈值 | 告警级别 |
|------|------|----------|
| 命中率 < 90% | 持续 5 分钟 | 警告 |
| 内存使用率 > 80% | 任意时刻 | 严重 |
| 连接数 > 80% maxclients | 持续 1 分钟 | 严重 |
| 阻塞客户端 > 0 | 任意时刻 | 严重 |
| 慢查询 > 10ms | 持续累积 | 警告 |
| 主从延迟 > 1s | 持续 1 分钟 | 警告 |

---

## 五、生产运维 checklist

```
□ 关闭危险命令：rename-command FLUSHALL "" / KEYS "" / CONFIG ""
□ 设置 requirepass + protected-mode yes
□ 内存上限 maxmemory + 淘汰策略 allkeys-lru
□ 持久化 RDB + AOF 混合开启
□ 慢查询监控 slowlog-log-slower-than 10000
□ 连接池预热 + 合理大小
□ 磁盘预留 30% 空间
□ 内核参数：vm.overcommit_memory=1 + somaxconn
□ 定期备份 RDB
```

---

## 六、总结

```
多级缓存 → Nginx(L1) + Redis(L2) + DB(L3)
缓存预热 → 启动加载 + 定时刷新
一致性   → Cache-Aside + 延迟双删
监控     → 命中率/内存/连接/慢查询
运维     → 安全加固 + 参数优化 + 定期备份
```
