---
layout: post
title: "融会贯通：ShardingSphere CosID主键生成框架深度分析"
date: 2022-07-27
categories: [distributed]
tags: [ShardingSphere, CosID, 分布式ID, 雪花算法, 号段模式]
comments: true

---

## 一、分布式 ID 核心要求

| 要求 | 说明 |
|------|------|
| **全局唯一** | 不能重复 |
| **趋势递增** | 利于数据库索引 |
| **高性能** | 高并发下不成为瓶颈 |
| **高可用** | 不依赖单点 |

---

## 二、CosID 两种方案

### 1、Snowflake（雪花算法）

```
64 位 ID 结构：
  [1bit 未使用] [41bit 时间戳] [10bit 机器ID] [12bit 序列号]
```

- 41bit 时间戳 → 可用 69 年
- 10bit 工作机器 → 支持 1024 台机器
- 12bit 序列号 → 每毫秒 4096 个 ID

```yaml
# CosID Snowflake 配置
cosid:
  snowflake:
    enabled: true
    machine:
      distributor:
        type: redis     # 通过 Redis 分配机器ID
    clock-backwards:
      spin-timeout: 1   # 时钟回拨容忍1ms
```

### 2、Segment（号段模式）

```
从数据库批量获取一段 ID，在内存中分配。

请求 → 本地号段 [1000-2000) → 用完 → 批量获取下一段 [2000-3000)
```

```yaml
cosid:
  segment:
    enabled: true
    distributor:
      type: redis       # Redis 存储号段
    share:
      offset: 0
      step: 1000        # 每次获取 1000 个
```

---

## 三、两种方案对比

| | Snowflake | Segment |
|------|-----------|---------|
| **递增性** | 趋势递增（近似有序） | 严格递增（本地段内） |
| **ID 长度** | 长（64bit） | 可自定义 |
| **性能** | 极高 | 高（号段用完需获取） |
| **依赖** | 机器ID分配（Redis/ZK） | 号段存储（Redis/DB） |
| **适用** | 通用 | 需要短 ID 或有严格递增要求 |

---

## 四、CosID 核心特性

### 1、机器 ID 安全分配

```
Redis/ZK 作为机器 ID 注册中心
→ 启动时获取机器 ID → 绑定 + 定期续约
→ 进程退出时释放 → 防止机器 ID 冲突
```

### 2、时钟回拨处理

```yaml
clock-backwards:
  spin-timeout: 1         # 回拨 < 1ms → 自旋等待
  broken-threshold: 2000  # 回拨 > 2s → 抛出异常
```

### 3、号段双 Buffer

```
当前号段 [1000-2000) → 用到 80% → 后台异步获取下一段 [2000-3000)
→ 号段用完 → 直接切换到新号段 → 不阻塞
```

---

## 五、总结

```
CosID 双模式：
  Snowflake → 64位趋势递增 → 高性能
  Segment  → 号段模式 → 严格递增 / 短ID

关键设计：
  机器ID(Redis分配+续约) + 时钟回拨处理 + 号段双Buffer
```
