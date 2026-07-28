---
layout: post
title: "ES性能调优最佳实践：写入/读取/底层原理全面优化"
date: 2022-06-26
categories: [distributed]
tags: [ElasticSearch, 性能调优, 写入优化, 读取优化, 底层原理, segment]
comments: true
---

> 从 ES 底层读写原理出发，系统化理解 ES 的性能瓶颈与优化方向。

---

## 一、ES 底层读写工作原理

### 1、分片路由规则

```java
shard_num = hash(_routing) % num_primary_shards
```

- `_routing` 默认取 `_id`，可自定义
- `num_primary_shards` 创建后不可修改 → **这就是为什么主分片数不能改**

### 2、写入数据过程

```
客户端 → [任意节点 = coordinating node]
           │
           │ 路由计算 → 确定目标 shard
           ▼
    [target node primary shard]
           │ 写入 Primary Shard
           ▼
    [同步到所有 Replica Shard]
           │
           ▼
    coordinating node ← 收到所有 replica 确认
           │
           ▼
        客户端 ← 写入成功
```

### 3、根据 ID 查询（单文档）

```
Client → coordinating node
           │ hash(_id) % shards_size
           ▼
    random choice: primary shard OR replica shard
           │
           ▼
    return document
```

读请求在 primary shard 和所有 replica 之间**随机轮询**，天然负载均衡。

### 4、全文搜索查询

```
query phase:
  coordinating node → 转发到所有 shard
                     → 各 shard 返回 (doc_id, score) 列表
                     → 合并排序

fetch phase:
  coordinating node → 根据 doc_id 去各节点拉取实际 document
                     → 返回给客户端
```

---

## 二、ES 底层存储结构

### 核心概念

| 概念 | 说明 |
|------|------|
| **Segment** | 倒排索引文件，每秒自动生成。文件过多时自动 merge |
| **Commit Point** | 记录当前所有可用 segment，维护 `.del` 删除标记文件 |
| **Translog** | 事务日志，防止宕机数据丢失。ES 6.0 起每次请求默认落盘 |
| **OS Cache** | 操作系统缓存，segment 先放 OS cache 再持久化到磁盘 |

### 数据写入底层原理

```
文档写入 → Index Buffer (内存)
              │
              │ refresh_interval (默认1秒)
              ▼
         Segment (OS Cache) → 可被搜索
              │
              │ translog 同步落盘
              ▼
         Flush: Segment 写入磁盘 → 更新 Commit Point → 删除旧 translog
```

**三个关键操作**：

| 操作 | 触发 | 作用 |
|------|------|------|
| **Refresh** | 每秒（`refresh_interval`） | 数据从 buffer 到 segment，变得可搜索 |
| **Translog Sync** | 每次请求 | 保证数据不丢失 |
| **Flush** | 30 分钟 / translog 512MB | segment 写入磁盘 |

**近实时搜索**：由于 refresh_interval 默认 1 秒，所以 ES 数据写入后最多 1 秒才能被搜索到。这就是"近实时"的含义。

---

## 三、提升写入性能

### 1、批量写入

```bash
POST _bulk
{ "index": { "_index": "test", "_id": "1" } }
{ "field1": "value1" }
{ "index": { "_index": "test", "_id": "2" } }
{ "field1": "value2" }
```

**bulk 线程池配置**：
```yaml
thread_pool.bulk.queue_size: 1000
```

### 2、调整 refresh_interval

```json
// 批量导入时可暂时关闭（导入完成后恢复）
PUT /test_index/_settings
{
  "refresh_interval": "-1"     // -1 = 关闭自动 refresh
}

// 导入完成恢复
PUT /test_index/_settings
{
  "refresh_interval": "30s"
}
```

### 3、副本数设为 0（导入阶段）

```json
PUT /test_index/_settings
{
  "number_of_replicas": 0
}
// 导入完成后设置回正常值
```

### 4、写入优化总结

```bash
# 批量导入的完整优化步骤：
# 1. 关闭 refresh
PUT /test/_settings { "refresh_interval": "-1" }

# 2. 副本数设为 0
PUT /test/_settings { "number_of_replicas": 0 }

# 3. 批量 bulk 导入
POST _bulk ...

# 4. 恢复副本数
PUT /test/_settings { "number_of_replicas": 1 }

# 5. 恢复 refresh
PUT /test/_settings { "refresh_interval": "1s" }

# 6. 手动 force_merge（合并 segment）
POST /test/_forcemerge?max_num_segments=1
```

---

## 四、提升读取性能

### 1、数据建模优化

```json
// ❌ 避免查询时 script 计算
GET blogs/_search
{
  "query": {
    "bool": {
      "filter": {
        "script": {
          "script": { "source": "doc['title.keyword'].value.length()>5" }
        }
      }
    }
  }
}

// ✅ 写入时预先计算好字段
POST blogs/_doc/1
{
  "title": "elasticsearch",
  "title_length": 13    // 预先计算保存
}
```

### 2、尽量用 Filter Context

```json
// ❌ must 参与评分计算
{ "query": { "bool": { "must": [{ "term": { "status": "active" } }] } } }

// ✅ filter 不参与评分，并且有缓存
{ "query": { "bool": { "filter": [{ "term": { "status": "active" } }] } } }
```

### 3、避免 `*` 开头通配符

```bash
# ❌ 性能杀手
GET /employee/_search
{
  "query": { "wildcard": { "address": { "value": "*白云*" } } }
}
```

### 4、使用 Profile & Explain API

```bash
# profile：查看各阶段耗时
GET /employee/_search
{
  "profile": true,
  "query": { "match_all": {} }
}

# explain：查看评分详情
GET /employee/_explain/1
{
  "query": { "match": { "address": "广州" } }
}
```

### 5、查询优化清单

| 优化点 | 做法 |
|--------|------|
| 数据建模 | 写入时预先计算，避免查询时 script |
| 查询方式 | filter 代替 must（精确匹配场景） |
| 通配符 | 避免 `*` 开头 |
| 字段设计 | keyword 做精确匹配，text 做全文搜索 |
| 慢查询 | Profile + Explain 分析定位 |
| force_merge | 只读索引定期合并 segment |
| 缓存 | 利用节点查询缓存与分片请求缓存 |

---

## 五、总结

```
写入优化：
  bulk 批量 → 关闭 refresh → 副本=0 → 导入完恢复

读取优化：
  filter 代替 must → 避免 script → 避免 *开头通配符

底层理解：
  shard = hash(_routing) % num_primary_shards
  写入: index buffer → segment(OS cache, 1s) → translog → flush(disk)
  读取: coordinating node → shard(随机轮询) → 合并结果
```

> 有道云笔记：[ES性能调优最佳实践](https://note.youdao.com/s/aOLNM6ud)
