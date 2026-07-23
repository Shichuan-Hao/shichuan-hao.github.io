---
title: "ElasticSearch 索引与文档操作完全指南"
date: 2022-06-13
categories: distributed
tags: [ElasticSearch, 索引, 文档, Mapping, 别名, Dynamic Mapping, 批量操作]
mermaid: true
---

> 索引和文档是 ES 的一体两面。从创建索引到了解 Dynamic Mapping，从文档 CRUD 到并发控制，从索引别名到数据建模——本文覆盖 ES 日常开发的全部基础操作。

## 一、索引操作详解

### 1.1 创建索引

最简方式（全部默认）：

```json
PUT /myindex
```

完整的创建索引语法：

```json
PUT /index_name
{
  "settings": {
    "number_of_shards": 1,          // 分片数量（创建后不可改）
    "number_of_replicas": 1          // 副本数量（可动态修改）
  },
  "mappings": {
    "properties": {
      "field1": { "type": "text" },
      "field2": { "type": "keyword" }
    }
  }
}
```

**实战：创建学生索引**：

```json
PUT /student_index
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "name":           { "type": "text" },
      "age":            { "type": "integer" },
      "enrolled_date":  { "type": "date" }
    }
  }
}
```

### 1.2 查询索引信息

```json
GET /myindex              # 获取指定索引信息
GET /student_index        # 获取学生索引
```

### 1.3 修改索引

**动态更新 settings**（副本数可在线调整）：

```json
PUT /student_index/_settings
{
  "index": {
    "number_of_replicas": 2
  }
}
```

**动态新增字段**（已有字段不可改）：

```json
PUT /student_index/_mapping
{
  "properties": {
    "grade": { "type": "integer" }
  }
}
```

> ⚠️ Mapping 中已有字段的类型不可修改（需要 Reindex 重建索引）。只能新增字段，不能删除字段。

### 1.4 删除索引

```json
DELETE /myindex
```

### 1.5 索引别名详解

**为什么需要别名？**

| 场景 | 问题 | 别名方案 |
|------|------|---------|
| 按日期切分的 n 个索引 | 每次搜索要指定数十个索引 | 别名指向所有按月切分的索引 |
| 线上索引 mappping 需要修改 | 直接改会停服？ | 创建新索引，切换别名指向 |

**创建索引时指定别名**：

```json
PUT myindex
{
  "aliases": { "myindex_alias": {} },
  "settings": { "refresh_interval": "30s", "number_of_shards": 1, "number_of_replicas": 0 }
}
```

**为已有索引添加别名**：

```json
POST /_aliases
{
  "actions": [
    { "add": { "index": "my_index", "alias": "my_index_alias" } }
  ]
}
```

**多索引别名实战**（日志检索场景）：

```json
# 1. 先创建 3 个按月的索引
PUT tlmall_logs_202401
PUT tlmall_logs_202402
PUT tlmall_logs_202403

# 2. 绑定别名为同一组
POST _aliases
{
  "actions": [
    { "add": { "index": "tlmall_logs_202401", "alias": "tlmall_logs_2024" } },
    { "add": { "index": "tlmall_logs_202402", "alias": "tlmall_logs_2024" } },
    { "add": { "index": "tlmall_logs_202403", "alias": "tlmall_logs_2024" } }
  ]
}

# 3. 跨所有 3 个月索引检索
POST tlmall_logs_2024/_search
```

> 使用别名和直接查索引的检索效率**完全一致**——别名只是物理索引的软链接。

---

## 二、文档操作详解

### 2.1 PUT vs POST 的区别

| 特性 | PUT | POST |
|------|-----|------|
| 指定 ID | **必须**指定 | **可选**（不指定则自动生成） |
| 幂等性 | ✅ 幂等（重复执行结果一致） | ❌ 非幂等 |
| 更新行为 | 全量替换（覆盖整个文档） | 可用 `_update` 部分更新 |

### 2.2 新增文档

**指定 ID 新增**（PUT，覆盖已有文档）：

```json
PUT /employee/_doc/1
{
  "name": "张三",
  "sex": 1,
  "age": 25,
  "address": "广州天河公园",
  "remark": "java developer"
}
```

**不指定 ID 新增**（POST，自动生成 ID）：

```json
POST /employee/_doc
{
  "name": "张三",
  "sex": 1,
  "age": 25,
  "address": "广州天河公园",
  "remark": "java developer"
}

# 响应
{
  "_id": "abc123xyz",   # ← ES 自动生成
  "_version": 1,
  "result": "created"
}
```

### 2.3 批量操作（_bulk API）

`_bulk` API 支持四种操作：**Index、Create、Update、Delete**。

```json
POST /_bulk

# Index：不存在则创建，存在则替换
{"index":  {"_index": "employee", "_id": "1"}}
{"name":"张三","sex":1,"age":25,"address":"广州天河公园","remark":"java developer"}

# Create：不存在则创建，存在则报错
{"create": {"_index": "employee", "_id": "2"}}
{"name":"李四","sex":1,"age":28,"address":"广州荔湾大厦","remark":"java assistant"}

# Update：部分更新
{"update": {"_index": "employee", "_id": "3"}}
{"doc": {"age": 29}}

# Delete：删除文档
{"delete": {"_index": "employee", "_id": "4"}}
```

> ⚠️ `_bulk` 请求体中每个操作用**换行符分隔**，不能有空行。请求 Content-Type 必须是 `application/x-ndjson`。

**完整 Bulk 插入示例**：

```json
POST /employee/_bulk
{"index":{"_index":"employee","_id":"1"}}
{"name":"张三","sex":1,"age":25,"address":"广州天河公园","remark":"java developer"}
{"index":{"_index":"employee","_id":"2"}}
{"name":"李四","sex":1,"age":28,"address":"广州荔湾大厦","remark":"java assistant"}
{"index":{"_index":"employee","_id":"3"}}
{"name":"王五","sex":0,"age":26,"address":"广州白云山公园","remark":"php developer"}
{"index":{"_index":"employee","_id":"4"}}
{"name":"赵六","sex":0,"age":22,"address":"长沙橘子洲","remark":"python assistant"}
{"index":{"_index":"employee","_id":"5"}}
{"name":"张龙","sex":0,"age":19,"address":"长沙麓谷企业广场","remark":"java architect assistant"}
{"index":{"_index":"employee","_id":"6"}}
{"name":"赵虎","sex":1,"age":32,"address":"长沙麓谷兴工国际产业园","remark":"java architect"}
```

### 2.4 查询文档

**按 ID 查询**：

```json
GET /employee/_doc/1
```

**按 ID 批量查询**（mget）：

```json
GET /employee/_mget
{
  "ids": ["1", "2", "3"]
}
```

**全量查询**：

```json
GET /employee/_search
{
  "query": { "match_all": {} }
}
```

**按字段匹配**：

```json
# 全文检索 address 包含"广州白云山"的文档
GET /employee/_search
{
  "query": {
    "match": { "address": "广州白云山" }
  }
}
```

**精确匹配（不分词）**：

```json
# 精确匹配 keyword 类型字段
GET /employee/_search
{
  "query": {
    "term": { "name": "张三" }
  }
}
```

**范围查询**：

```json
GET /employee/_search
{
  "query": {
    "range": {
      "age": { "gte": 20, "lte": 26 }
    }
  }
}
```

### 2.5 更新文档

**单个文档部分更新**：

```json
POST /employee/_update/1
{
  "doc": { "age": 28 }
}
```

**批量更新**：

```json
POST _bulk
{"update":{"_index":"employee","_id":3}}
{"doc":{"age":29}}
{"update":{"_index":"employee","_id":4}}
{"doc":{"age":27}}
```

**按条件批量更新**（`_update_by_query`）：

```json
POST /employee/_update_by_query
{
  "query": { "term": { "name": "张三" } },
  "script": {
    "source": "ctx._source.age = 30",
    "lang": "painless"
  }
}
```

### 2.6 删除文档

**按 ID 删除**：

```json
DELETE /employee/_doc/1
```

**批量删除**：

```json
POST _bulk
{"delete":{"_index":"employee","_id":3}}
{"delete":{"_index":"employee","_id":4}}
```

**按条件删除**（`_delete_by_query`）：

```json
POST /employee/_delete_by_query
{
  "query": { "match": { "address": "广州" } }
}
```

### 2.7 并发控制（乐观锁）

ES 7+ 使用 `_seq_no` + `_primary_term` 实现乐观锁：

```json
# 更新时带上当前 seq_no 和 primary_term
POST /employee/_doc/1?if_seq_no=13&if_primary_term=1
{
  "name": "张三xxxx",
  "sex": 1,
  "age": 25
}

# 如果版本不匹配 → HTTP 409 Conflict
{
  "error": {
    "type": "version_conflict_engine_exception",
    "reason": "[1]: version conflict, required seqNo [13], primary term [1]."
  }
}
```

---

## 三、文档建模最佳实践

### 3.1 如何处理关联关系

ES **不擅长**处理关联关系，一般有四种方案：

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **Object** | 文档在一起，读性能高 | 对象数组查询可能不准 | 简单嵌套 |
| **Nested** | 保持对象独立性 | 更新子文档需更新整个文档 | 少量子文档，偶尔更新 |
| **Join** | 父子独立更新 | 维护消耗内存，读性能差 | 子文档更新频繁 |
| **宽表冗余** | 速度最快 | 冗余浪费存储 | 一对多/多对多 |
| **业务端关联** | 简单直观 | 多次请求耗时 | 数据量少 |

> **核心原则**：不要在 ES 中做多表关联！突破关系型数据库的思维定式，尽量使用扁平的宽表文档模型。

### 3.2 Object 数组查询的陷阱

```json
POST /my_movies/_doc/1
{
  "title": "Speed",
  "actors": [
    { "first_name": "Keanu",  "last_name": "Reeves" },
    { "first_name": "Dennis", "last_name": "Hopper" }
  ]
}

# 查询 first_name=Keanu AND last_name=Hopper 的电影
# ❌ 会错误返回 Speed！
# Object 内部数据被扁平化：
#   actors.first_name: ["Keanu", "Dennis"]
#   actors.last_name:  ["Reeves", "Hopper"]
# Keanu 和 Hopper 虽然不在同一个对象中，但字段值都存在！
```

**Nested 类型解决**：

```json
PUT /my_movies
{
  "mappings": {
    "properties": {
      "actors": {
        "type": "nested",         # ← 关键：声明为 nested
        "properties": {
          "first_name": {"type": "keyword"},
          "last_name":  {"type": "keyword"}
        }
      }
    }
  }
}

# Nested 查询
POST /my_movies/_search
{
  "query": {
    "nested": {
      "path": "actors",
      "query": {
        "bool": {
          "must": [
            {"match": {"actors.first_name": "Keanu"}},
            {"match": {"actors.last_name": "Hopper"}}
          ]
        }
      }
    }
  }
}
```

### 3.3 Join 父子文档

```json
# 定义 join 关系
PUT /my_blogs
{
  "mappings": {
    "properties": {
      "blog_comments_relation": {
        "type": "join",
        "relations": { "blog": "comment" }
      }
    }
  }
}

# 索引父文档
PUT /my_blogs/_doc/blog1
{
  "title": "Learning Elasticsearch",
  "content": "learning ELK",
  "blog_comments_relation": { "name": "blog" }
}

# 索引子文档（必须带 routing = 父文档 ID）
PUT /my_blogs/_doc/comment1?routing=blog1
{
  "comment": "I am learning ELK",
  "username": "Jack",
  "blog_comments_relation": {
    "name": "comment",
    "parent": "blog1"
  }
}

# 查询：返回有 Jack 评论的博客（父文档）
POST /my_blogs/_search
{
  "query": {
    "has_child": {
      "type": "comment",
      "query": { "match": { "username": "Jack" } }
    }
  }
}

# 查询：返回 "Learning Hadoop" 博客的所有评论（子文档）
POST /my_blogs/_search
{
  "query": {
    "has_parent": {
      "parent_type": "blog",
      "query": { "match": { "title": "Learning Hadoop" } }
    }
  }
}
```

> `routing` 参数确保父子文档存在同一个分片上，是 Join 查询性能的关键。

### 3.4 避免过多字段

- 文档中最好避免大量字段（默认最大 1000）
- 过多字段不易维护，且 Mapping 保存在 Cluster State 中影响集群性能
- 删除或修改字段需要 Reindex

### 3.5 Dynamic Mapping 策略

| 值 | 说明 |
|------|------|
| `true`（默认） | 未知字段自动加入 Mapping |
| `false` | 新字段不被索引，但保留在 `_source` |
| `strict` | 新字段导致写入**失败** |

生产环境建议用 **`strict`**：

```json
PUT /user
{
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "name": { "type": "text" },
      "address": {
        "type": "object",
        "dynamic": "true"    # address 内部允许动态字段
      }
    }
  }
}

# 插入 age 字段 → 报错！
PUT /user/_doc/1
{
  "name": "fox",
  "age": 32        # ← 未在 mapping 中定义，拒绝写入
}
```

### 3.6 避免模糊查询

正则、通配符、前缀查询性能很差，特别是通配符开头会导致性能灾难。

**优化技巧：将字符串拆成结构化字段**：

```json
# ❌ 用通配符查版本号
GET softwares/_search?q=version:7.2.*

# ✅ 拆成结构化对象
PUT softwares/
{
  "mappings": {
    "properties": {
      "version": {
        "properties": {
          "display_name": {"type": "keyword"},
          "major": {"type": "byte"},
          "minor": {"type": "byte"},
          "hot_fix": {"type": "byte"}
        }
      }
    }
  }
}

# 精确查询版本为 7.2.x 的软件
POST softwares/_search
{
  "query": {
    "bool": {
      "filter": [
        {"term": {"version.major": 7}},
        {"term": {"version.minor": 2}}
      ]
    }
  }
}
```

### 3.7 避免空值引起聚合不准

```json
PUT /scores
{
  "mappings": {
    "properties": {
      "score": {
        "type": "float",
        "null_value": 0    # ← null 值统一替换为 0
      }
    }
  }
}
```

### 3.8 Mapping 元信息管理

```json
PUT /my_index
{
  "mappings": {
    "_meta": {
      "index_version_mapping": "1.1"
    }
  }
}
```

> 建议将 Mapping 文件上传 Git 进行版本管理。

---

## 四、实战案例：理财产品信息检索

```json
# 1) 创建索引
PUT /product_info
{
  "settings": { "number_of_shards": 1, "number_of_replicas": 1 },
  "mappings": {
    "properties": {
      "productName": { "type": "text", "analyzer": "ik_smart" },
      "annual_rate": { "type": "keyword" },
      "describe":    { "type": "text", "analyzer": "ik_smart" }
    }
  }
}

# 2) 批量导入数据
POST /product_info/_bulk
{"index":{}}
{"productName":"理财产品A","annual_rate":"3.2200%","describe":"180天定期理财，最低20000起投，收益稳定，可以自助选择消息推送"}
# ... 省略其他 5 条

# 3) 全文搜索描述包含"每天收益到账消息推送"的产品
GET /product_info/_search
{
  "query": { "match": { "describe": "每天收益到账消息推送" } }
}

# 4) 搜索年化率在 3.00%~3.13% 之间的产品
GET /product_info/_search
{
  "query": {
    "range": {
      "annual_rate": { "gte": "3.0000%", "lte": "3.1300%" }
    }
  }
}
```

---

## 五、总结

| 维度 | 要点 |
|------|------|
| 索引 | 按业务/时间维度创建，名称全小写，分片数创建后不可改 |
| 文档 | PUT 全量替换 + 幂等 / POST 支持部分更新 / Bulk 批量操作 |
| 并发 | `_seq_no` + `_primary_term` 乐观锁，冲突返回 409 |
| 别名 | 多索引逻辑分组，透明切换索引，与物理索引效率一致 |
| 建模 | 避免关联，优先宽表；Nested 保持对象独立性；strict 控制字段 |
| Mapping | 只能新增字段不能改/删；用 _meta 做版本管理 |
