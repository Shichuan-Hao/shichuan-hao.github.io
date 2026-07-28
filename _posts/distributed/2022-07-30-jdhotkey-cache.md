---
layout: post
title: "京东热点缓存探测系统JDhotkey架构剖析：从热点发现到集群广播"
date: 2022-07-30
categories: [distributed]
tags: [JDhotkey, 热点缓存, 热点探测, 高并发, 缓存系统, 京东]
comments: true

---

## 一、背景：电商热点问题

### 什么是热点Key？

双十一/618期间，某些爆款商品的缓存 key 被**瞬间百万级并发**请求。

```
普通商品：QPS 100 → 缓存扛得住
热门商品：QPS 1000000 → 单机 Redis 崩 → 缓存击穿 → DB 崩 → 服务雪崩
```

### 传统方案的不足

| 方案 | 问题 |
|------|------|
| 人工识别 | 滞后，发现时已产生故障 |
| 定时统计 | 实时性不够 |
| Redis 多副本 | 副本同步也有延迟 |

---

## 二、JDhotkey 系统架构

```
┌────────────────────────────────────────────────────────┐
│                     Worker 集群（每台App实例）            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  Worker  │  │  Worker  │  │  Worker  │              │
│  │ (滑动窗口 │  │ (滑动窗口 │  │ (滑动窗口 │              │
│  │  统计)   │  │  统计)   │  │  统计)   │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │              │              │                   │
│       └──────────────┼──────────────┘                   │
│                      │ 上报热点key                       │
│                      ▼                                  │
│              ┌──────────────┐                           │
│              │  Dashboard   │  热点数据收集/维护           │
│              └──────┬───────┘                           │
│                      │                                  │
│                      │ 推送热点key列表                    │
│                      ▼                                  │
│              ┌──────────────┐                           │
│              │  etcd 集群   │  配置中心/通知              │
│              └──────┬───────┘                           │
│                      │ etcd watch                      │
│                      ▼                                  │
│              ┌──────────────┐                           │
│              │  全量 Worker │  接收热点key -> 本地缓存     │
│              └──────────────┘                           │
└────────────────────────────────────────────────────────┘
```

---

## 三、热点探测五步流程

```
Step 1: Worker 内滑动窗口统计
  → 每个 key 维护一个时间窗口内的访问计数
  → 计数超过阈值 → 标记为"疑似热点"

Step 2: 上报 Dashboard
  → Worker 将疑似热点 key 上报给 Dashboard
  → Dashboard 汇总所有 Worker 的上报

Step 3: Dashboard 判断（集群维度）
  → 汇总计数 > 集群阈值 → 确认热点
  → 否则 → 是局部热点（不需要全集群广播）

Step 4: 写入 etcd
  → Dashboard 将热点 key 写入 etcd

Step 5: Worker 监听 etcd 变化
  → 通过 etcd watch 实时接收热点通知
  → 将热点 key 放入本地缓存（如 Caffeine）
  → 对该 key 的请求走本地缓存，不再打 Redis
```

---

## 四、核心设计要点

### 1、滑动窗口统计

```
时间窗口: 最近 10 秒
精度: 1 秒/bucket

[1s] [1s] [1s] [1s] [1s] [1s] [1s] [1s] [1s] [1s]
 ← 当前时间指针移动 →

每 1 秒：
  → 丢弃最旧的 bucket → 创建新的 bucket → 重新统计
```

### 2、规则设置

```yaml
规则配置：
  - key 匹配模式: sku_*
    窗口大小: 10s
    阈值: 100 次/秒 → 标记热点
```

### 3、Worker 本地缓存

```
热点 key → Caffeine Cache (本地JVM缓存)
  → 容量有限 → 只缓存真正的热点
  → TTL 短（热点持续判断中）

非热点 key → Redis 远程缓存
```

### 4、etcd 通知机制

```
Dashboard → etcd put /hotkeys/current ["sku_123","sku_456"]
         → Worker watch → 触发回调 → 更新本地热点缓存
```

---

## 五、容灾设计

| 场景 | 应对 |
|------|------|
| Dashboard 宕机 | etcd 数据仍在，Worker 继续用当前热点列表 |
| etcd 集群宕机 | Worker 降级 → 不再区分热点，兜底用本地缓存策略 |
| Worker 宕机 | 无影响，其他 Worker 继续工作 |
| 热点误判 | 按周期重新计算，热点降级很快 |

---

## 六、总结

```
JDhotkey 核心思路：
  滑动窗口统计(Worker) 
  → Dashboard汇总判断 
  → etcd持久化+通知 
  → Worker本地缓存(Caffeine)

关键设计：
  不要全量key缓存 → 只缓存真正的热点
  滑动窗口实时统计 → 秒级发现
  etcd watch → 毫秒级广播
  容灾降级 → Dashboard/etcd 宕机不影响核心业务
```

> JDhotkey 已开源：[https://github.com/jd-opensource/hotkey](https://github.com/jd-opensource/hotkey)
