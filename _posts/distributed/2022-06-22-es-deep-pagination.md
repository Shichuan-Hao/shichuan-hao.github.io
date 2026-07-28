---
layout: post
title: "ES深度分页问题及解决方案详解：from+size/scroll/search_after/PIT"
date: 2022-06-22
categories: [distributed]
tags: [ElasticSearch, 深度分页, scroll, search_after, PIT, 性能优化]
comments: true
---

> 深度分页：用户尝试访问第 1000 页或更后面的数据时，数据库需要先跳过前面数十万条记录，大量数据扫描和排序导致性能瓶颈甚至 OOM。

---

## 一、ES 分页查询流程

```
Client
  │ GET /index/_search?from=10000&size=100
  ▼
Coordinating Node (协调节点)
  │ 转发请求给各分片
  ├──▶ Shard 1: 取前 10100 条，排序后返回给协调节点
  ├──▶ Shard 2: 取前 10100 条，排序后返回给协调节点
  └──▶ Shard 3: 取前 10100 条，排序后返回给协调节点
  │
  ▼
协调节点汇总 30300 条数据 → 二次排序 → 取 [10000, 10100] → 返回客户端
```

**核心问题**：每次有序查询在每个分片中单独执行，然后 heap 中汇总二次排序。查询越靠后，堆内存汇总数据越多，容易导致 **OOM 和频繁 Full GC**。

---

## 二、max_result_window 限制

```bash
# 默认值 10000
GET /employee/_search
{
  "query": { "match_all": {} },
  "from": 10000,
  "size": 5
}
# 报错：from + size 超过 10000
```

**为什么限制？**：ES 限制最大分页数是为了保护堆内存不被错误操作溢出。

**临时调大（不推荐）**：
```json
PUT /employee/_settings
{
  "index.max_result_window": 20000
}
```

---

## 三、from+size 的优缺点

| 优点 | 缺点 |
|------|------|
| 支持随机翻页 | 受 `max_result_window` 限制 |
| 使用简单 | 深度翻页性能指数级下降 |
| 适合小型数据集 | 越往后越慢 |

**适用场景**：
- 小型数据集 Top N（N ≤ 10000）
- 主流 PC 搜索引擎的随机跳页（如百度前 20 页）

> 谷歌、百度已经取消了跳页功能。淘宝仅展示前 100 页。手机端 APP 只能"下拉加载更多"。

---

## 四、Scroll Search 滚动查询

### 原理

scroll 类似**数据库游标**，首次查询时创建一个**快照**，后续滚动基于这个快照数据。

### 实现步骤

**Step 1**：第一次 scroll 查询
```bash
GET /kibana_sample_data_flights/_search?scroll=5m
{
  "query": { "term": { "OriginWeather": "Sunny" } },
  "size": 100
}

# 返回：
# {
#   "_scroll_id": "DXF1ZXJ5QW5kRmV0Y2gBAAAA...",
#   "hits": { ... }
# }
```

**Step 2**：使用 scroll_id 翻页
```bash
GET /_search/scroll
{
  "scroll": "5m",
  "scroll_id": "DXF1ZXJ5QW5kRmV0Y2gBAAAA..."
}
# 继续翻页，直到返回空 hits
```

**Step 3**：清除 scroll（超时自动清除，但建议手动清除）
```bash
DELETE /_search/scroll
{
  "scroll_id": "DXF1ZXJ5QW5kRmV0Y2gBAAAA..."
}

# 清除所有 scroll
DELETE /_search/scroll/_all
```

### scroll 特点

| 特点 | 说明 |
|------|------|
| 数据快照 | 基于首次查询时刻的快照，后续变更不影响 |
| 非实时 | 新写入数据不可见 |
| 资源消耗 | 保持 scroll 上下文需要资源 |
| **官方态度** | ES 7 后不推荐 scroll 做深度分页 |

---

## 五、search_after（推荐方案）

### 原理

search_after 使用**上一页最后一条记录的排序值**作为游标，避免遍历前面的记录。

### 使用步骤

```bash
# Step 1：首次查询
GET /employee/_search
{
  "size": 2,
  "query": { "match_all": {} },
  "sort": [
    { "age": "asc" },
    { "_id": "asc" }        // _id 作为 tiebreaker（排序值可能重复）
  ]
}

# 返回最后一条 sort 值：[25, "1"]

# Step 2：下一页
GET /employee/_search
{
  "size": 2,
  "query": { "match_all": {} },
  "sort": [
    { "age": "asc" },
    { "_id": "asc" }
  ],
  "search_after": [25, "1"]     // 上一页最后一条的 sort 值
}
```

### search_after 特点

| 特点 | 说明 |
|------|------|
| 实时性 | ✅ 实时数据 |
| 性能 | ✅ 性能稳定，不受翻页深度影响 |
| 缺点 | ❌ 不支持随机跳页（只能"下一页"） |
| 需要 | 排序字段唯一（用 _id 做 tiebreaker） |

---

## 六、PIT（Point In Time）— ES 7.10+

### 什么是 PIT

PIT 是轻量级的**数据视图**，在 search_after 基础上提供了更稳定的分页体验。

```bash
# Step 1：创建 PIT
POST /employee/_pit?keep_alive=5m
# 返回：{ "id": "46uA..." }

# Step 2：基于 PIT 的 search_after
GET /_search
{
  "size": 100,
  "query": { "match_all": {} },
  "pit": {
    "id": "46uA...",
    "keep_alive": "5m"
  },
  "sort": [
    { "@timestamp": "asc" },
    { "_shard_doc": "asc" }
  ],
  "search_after": [1620000000000, 123]
}

# Step 3：删除 PIT
DELETE /_pit
{
  "id": "46uA..."
}
```

**PIT vs scroll**：

| | scroll | PIT + search_after |
|------|--------|---------------------|
| 数据更新 | 创建后不可见 | ✅ 可见 |
| 状态保持 | 重服务端状态 | 轻量级 |
| 推荐版本 | 不推荐 | ✅ 推荐 |

---

## 七、四种方案对比总结

| 方案 | 实时性 | 跳页 | 深度分页性能 | 适用场景 |
|------|--------|------|-------------|----------|
| from+size | ✅ 实时 | ✅ | ❌ 差 | 前 10000 条，小型数据集 |
| scroll | ❌ 快照 | ❌ | ✅ 好 | 非 C 端大批量导出 |
| search_after | ✅ 实时 | ❌ | ✅ 好 | **C 端无限滚动** |
| PIT+search_after | ✅ 实时 | ❌ | ✅ 最好 | 生产环境推荐 |

---

## 八、实战建议

```
百度/谷歌：删除跳页，限制页数
淘宝/京东：仅展示前 100 页
移动端 APP：下拉加载更多（本质 search_after）

生产环境推荐：
  数据量 < 10000  → from + size
  数据量 > 10000  → search_after（或 PIT + search_after）
  数据导出       → scroll
```

> 有道云笔记：[ES深度分页问题详解](https://note.youdao.com/s/DMuehv8e)
