---
layout: post
title: "ElasticSearch基础数据管理详解：索引/映射/文档CRUD全操作"
date: 2022-06-16
categories: [distributed]
tags: [ElasticSearch, 索引管理, 映射, Mapping, 文档CRUD, 分词]
comments: true
---

> ES 功能的核心是搜索引擎，理解核心概念对加深 ES 理解大有裨益。

---

## 一、索引管理

### 创建索引

```json
PUT /employee
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "name": {
        "type": "keyword"
      },
      "sex": {
        "type": "integer"
      },
      "age": {
        "type": "integer"
      },
      "address": {
        "type": "text",
        "analyzer": "ik_max_word",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 50
          }
        }
      },
      "remark": {
        "type": "text",
        "analyzer": "ik_smart",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      }
    }
  }
}
```

**settings 参数说明**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `number_of_shards` | 1 | 主分片数（索引创建后不可修改） |
| `number_of_replicas` | 1 | 每个主分片的副本数（可动态修改） |

### 索引操作

```bash
# 查看所有索引
GET _cat/indices?v

# 查看索引详情
GET /employee

# 查看索引的Mapping
GET /employee/_mapping

# 查看索引的Settings
GET /employee/_settings

# 删除索引
DELETE /employee

# 判断索引是否存在
HEAD /employee
```

---

## 二、Mapping 映射详解

### 什么是 Mapping

映射类似关系型数据库中的 Schema，可以近似理解为"**表结构**"。

映射定义了：
- 字段名称、字段类型
- 是否需要分词
- 是否需要索引
- 是否需要存储
- 是否需要多字段类型

### Dynamic Mapping（动态映射）

ES 可以智能推断数据类型：

```bash
# 不预先创建 mapping，直接插入文档
POST /test_index/_doc/1
{
  "name": "张三",
  "age": 25,
  "birthday": "2022-01-01"
}

# 查看自动生成的 mapping
GET /test_index/_mapping
# age → long, name → text+keyword子字段, birthday → date
```

**Dynamic 动态识别规则**：

| JSON 类型 | ES 推断类型 |
|-----------|------------|
| `true` / `false` | `boolean` |
| `123` | `long` |
| `123.45` | `float` |
| `"2022-01-01"` | `date` |
| `"hello world"` | `text` + `keyword` 子字段 |
| `{"key":"value"}` | `object` |

**Dynamic 三种模式**：

```json
{
  "mappings": {
    "dynamic": "true|false|strict"
  }
}
```

| 值 | 行为 |
|------|------|
| `true`（默认） | 自动添加新字段到 mapping |
| `false` | 新字段不会被索引，但存 `_source` |
| `strict` | 遇到新字段直接报错 |

> **生产建议**：关键业务索引使用 `strict` 模式，避免字段类型被意外改变。

### type=text 自动生成的 keyword 子字段

```bash
GET /employee/_mapping
# address 字段自动包含:
#   address        → text 类型（分词，用于全文检索）
#   address.keyword → keyword 类型（精确匹配、排序、聚合）
```

**使用对比**：
```bash
# 精确匹配 → 用 .keyword
GET /employee/_search
{ "query": { "term": { "address.keyword": "广州天河公园" } } }

# 全文检索 → 用原字段（分词）
GET /employee/_search
{ "query": { "match": { "address": "广州公园" } } }
```

### keyword 类型的 ignore_above

```json
"address": {
  "type": "keyword",
  "ignore_above": 50    // 超过50字符的文本不索引，但保留在_source
}
```

---

## 三、文档管理

### 新增文档

```bash
# 指定 ID（推荐）
PUT /employee/_doc/1
{
  "name": "张三",
  "sex": 1,
  "age": 25,
  "address": "广州天河公园",
  "remark": "java developer"
}

# 自动生成 ID
POST /employee/_doc
{
  "name": "李四",
  ...
}
```

### 更新文档

```bash
# 全量替换（指定ID，覆盖整个文档）
PUT /employee/_doc/1
{
  "name": "张三改",
  ...
}

# 部分更新（只更新指定字段）
POST /employee/_update/1
{
  "doc": {
    "age": 26,
    "address": "广州天河新地址"
  }
}

# 脚本更新（对数值做运算）
POST /employee/_update/1
{
  "script": {
    "source": "ctx._source.age++"
  }
}
```

### 批量操作（_bulk）

```bash
POST /employee/_bulk
{"index":{"_id":"1"}}
{"name":"张三","sex":1,"age":25,"address":"广州天河公园","remark":"java developer"}
{"index":{"_id":"2"}}
{"name":"李四","sex":1,"age":28,"address":"广州荔湾大厦","remark":"java assistant"}
{"update":{"_id":"3"}}
{"doc":{"age":30}}
{"delete":{"_id":"4"}}
```

**注意**：
- 换行以 `\n` 分隔，JSON 不能格式化换行
- 批量中的每对操作是独立的，某条失败不影响其他操作

### 删除文档

```bash
DELETE /employee/_doc/1
```

### 查询文档

```bash
# 单条查询
GET /employee/_doc/1

# 查看文档是否存在
HEAD /employee/_doc/1

# _source 过滤
GET /employee/_doc/1?_source=name,age
GET /employee/_doc/1?_source_includes=name,age&_source_excludes=sex
```

---

## 四、版本控制和乐观锁

### 版本号机制

ES 使用 `_version` 实现乐观锁：

```bash
# 第一次创建 → _version: 1
PUT /employee/_doc/1
{ "name": "张三" }

# 更新 → _version: 2
POST /employee/_update/1
{ "doc": { "age": 26 } }

# 使用版本号做乐观锁（版本不匹配则失败）
PUT /employee/_doc/1?if_seq_no=3&if_primary_term=1
{ "name": "张三" }
```

**核心字段**：

| 字段 | 说明 |
|------|------|
| `_version` | 文档版本号（每次更新递增） |
| `_seq_no` | 序列号（每次更新递增，更精确） |
| `_primary_term` | 主分片任期（主分片发生变化时递增） |

---

## 五、索引别名

### 什么是别名

别名类似于 Linux 的软链接，指向一个或多个索引。

### 创建和使用

```bash
# 创建别名
POST _aliases
{
  "actions": [
    {"add": {"index": "employee", "alias": "emp"}}
  ]
}

# 通过别名操作
GET /emp/_doc/1
POST /emp/_search
{ "query": { "match_all": {} } }

# 原子性切换（零停机重新索引）
POST _aliases
{
  "actions": [
    {"remove": {"index": "employee_v1", "alias": "emp"}},
    {"add": {"index": "employee_v2", "alias": "emp"}}
  ]
}
```

---

## 六、中文分词器实战

### IK 分词器两种模式对比

```bash
# ik_max_word —— 最细粒度
GET _analyze
{
  "text": "中华人民共和国国歌",
  "analyzer": "ik_max_word"
}
# → ["中华人民共和国","中华人民","中华","华人","人民共和国","人民","共和国","国歌"]

# ik_smart —— 智能模式
GET _analyze
{
  "text": "中华人民共和国国歌",
  "analyzer": "ik_smart"
}
# → ["中华人民共和国","国歌"]
```

### 索引和搜索推荐

| 场景 | 分词器 | 原因 |
|------|--------|------|
| 索引（写入时） | `ik_max_word` | 最细粒度，最大范围覆盖搜索词 |
| 搜索（查询时） | `ik_smart` | 较少的分词，减少无效匹配 |

---

## 七、Object 类型和 Nested 类型

### Object 类型的陷阱

```bash
PUT /my_index/_doc/1
{
  "user": [
    {"name": "John", "age": 30},
    {"name": "Alice", "age": 25}
  ]
}
```

ES 内部存储时会将 Object 扁平化：
```
user.name: ["John", "Alice"]
user.age:  [30, 25]
```

搜索 `user.name=John AND user.age=25` 时，**可能会匹配到错误结果**（Alice 25 被平铺到同一层）。

### Nested 类型解决

```json
PUT /my_index
{
  "mappings": {
    "properties": {
      "user": {
        "type": "nested"  // 保持独立关联
      }
    }
  }
}
```

查询时用 nested query：
```json
GET /my_index/_search
{
  "query": {
    "nested": {
      "path": "user",
      "query": {
        "bool": {
          "must": [
            {"match": {"user.name": "John"}},
            {"match": {"user.age": 25}}
          ]
        }
      }
    }
  }
}
```

### 三种关联数据建模方式对比

| 方式 | 说明 | 适用场景 |
|------|------|----------|
| Object | 扁平化存储 | 简单嵌套，无需独立查询子对象 |
| Nested | 独立存储子对象 | 独立查询子对象的组合条件 |
| Join | 父子文档 | 一对多关系，子文档需频繁更新 |

---

## 八、总结

```
索引创建 → Mapping 设计（字段类型 + 分词策略）
    ↓
文档 CRUD（PUT/POST/DELETE/_bulk）
    ↓
别名管理（零停机重新索引）
    ↓
IK 分词器（ik_max_word 索引用 / ik_smart 搜索用）
    ↓
关联建模（Object / Nested / Join 选型）
```

> 有道云笔记：[ES基础数据管理详解](https://note.youdao.com/s/SKUMcuXv)
