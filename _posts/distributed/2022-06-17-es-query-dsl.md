---
layout: post
title: "ElasticSearch高级查询Query DSL实战：全文/精确/组合/自定义四大查询"
date: 2022-06-17
categories: [distributed]
tags: [ElasticSearch, Query DSL, 查询语法, match, term, bool, range]
comments: true
---

> Query DSL（Domain Specified Language 领域专用语言）利用 REST API 传递 JSON 格式的请求体与 ES 交互，让检索变得更强大、更简洁。

---

## 一、基本语法与示例数据

```bash
# 基本语法
GET /<index_name>/_search
{ json请求体数据 }
```

**示例数据**：

```bash
DELETE /employee

PUT /employee
{
  "settings": { "number_of_shards": 1, "number_of_replicas": 1 },
  "mappings": {
    "properties": {
      "name": { "type": "keyword" },
      "sex": { "type": "integer" },
      "age": { "type": "integer" },
      "address": {
        "type": "text", "analyzer": "ik_max_word",
        "fields": { "keyword": { "type": "keyword" } }
      },
      "remark": {
        "type": "text", "analyzer": "ik_smart",
        "fields": { "keyword": { "type": "keyword" } }
      }
    }
  }
}

POST /employee/_bulk
{"index":{"_id":"1"}}
{"name":"张三","sex":1,"age":25,"address":"广州天河公园","remark":"java developer"}
{"index":{"_id":"2"}}
{"name":"李四","sex":1,"age":28,"address":"广州荔湾大厦","remark":"java assistant"}
{"index":{"_id":"3"}}
{"name":"王五","sex":0,"age":26,"address":"广州白云山公园","remark":"php developer"}
{"index":{"_id":"4"}}
{"name":"赵六","sex":0,"age":22,"address":"长沙橘子洲","remark":"python assistant"}
{"index":{"_id":"5"}}
{"name":"张龙","sex":0,"age":19,"address":"长沙麓谷企业广场","remark":"java architect assistant"}
{"index":{"_id":"6"}}
{"name":"赵虎","sex":1,"age":32,"address":"长沙麓谷兴工国际产业园","remark":"java architect"}
```

---

## 二、match_all —— 匹配所有文档

```json
GET /employee/_search
{
  "query": { "match_all": {} }
}
```

**高级用法**：

```json
GET /employee/_search
{
  "query": { "match_all": {} },
  "size": 10,
  "sort": [{ "_score": { "order": "desc" } }]
}

# _source 过滤
GET /employee/_search
{
  "query": { "match_all": {} },
  "_source": false         // 不返回源数据，仅返回元字段
}
```

---

## 三、全文检索查询

### 1、match —— 分词匹配

```json
GET /employee/_search
{
  "query": {
    "match": {
      "address": "广州白云山"
    }
  }
}
```

**逻辑**：对"广州白云山"分词 → `["广州","白云山"]` → 两个词任一个匹配即返回（OR 逻辑）。

**多字段 match**：
```json
GET /employee/_search
{
  "query": {
    "multi_match": {
      "query": "java",
      "fields": ["remark", "address"]
    }
  }
}
```

### 2、match_phrase —— 短语匹配

```json
GET /employee/_search
{
  "query": {
    "match_phrase": {
      "address": "白云山"
    }
  }
}
```

- 分词后所有词必须**依次出现**
- 词间距离 `slop` 参数控制允许的间隔词数

### 3、match_phrase_prefix —— 前缀匹配

```json
GET /employee/_search
{
  "query": {
    "match_phrase_prefix": {
      "remark": "java dev"
    }
  }
}
```

---

## 四、精确匹配查询

### 1、term —— 精确值匹配（不分词）

```json
# 错误用法：keyword 类型才生效
GET /employee/_search
{
  "query": { "term": { "address": "广州" } }
}

# 正确：需要 .keyword 子字段
GET /employee/_search
{
  "query": {
    "term": { "address.keyword": "广州天河公园" }
  }
}
```

**term vs match**：

| | term | match |
|------|------|-------|
| 是否分词 | ❌ 不分词，精确匹配 | ✅ 先分词再匹配 |
| 适用字段 | keyword、数值、日期 | text |
| 常见场景 | 状态/标签/ID过滤 | 全文搜索 |

### 2、terms —— 多值匹配

```json
GET /employee/_search
{
  "query": {
    "terms": { "name": ["张三", "李四"] }
  }
}
```

### 3、range —— 范围查询

```json
GET /employee/_search
{
  "query": {
    "range": {
      "age": { "gte": 25, "lte": 30 }
    }
  }
}
```

| 参数 | 含义 |
|------|------|
| `gte` | >= |
| `gt` | > |
| `lte` | <= |
| `lt` | < |

---

## 五、组合查询（bool）

### bool 四种条件

```json
GET /employee/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "remark": "java" } }
      ],
      "must_not": [
        { "term": { "sex": 0 } }
      ],
      "should": [
        { "term": { "age": 25 } },
        { "term": { "age": 28 } }
      ],
      "filter": [
        { "range": { "age": { "gte": 20, "lte": 35 } } }
      ]
    }
  }
}
```

| 条件 | 逻辑 | 对评分的影响 |
|------|------|-------------|
| `must` | AND，必须满足 | ✅ 参与评分 |
| `must_not` | NOT，必须不满足 | ❌ 不参与评分 |
| `should` | OR，满足越多越好 | ✅ 参与评分 |
| `filter` | 过滤，必须满足 | ❌ 不参与评分（高效） |

> **最佳实践**：能用 filter 就不用 must，filter 不参与评分计算 + 有缓存，性能更高。

**filter vs must 对比**：

| | filter | must |
|------|--------|------|
| 评分 | ❌ 不计算 | ✅ 计算 |
| 缓存 | ✅ 缓存结果 | ❌ 不缓存 |
| 用途 | 精确过滤、范围过滤 | 全文匹配 |

---

## 六、自定义查询

### 1、boosting 权重提升

```json
GET /employee/_search
{
  "query": {
    "bool": {
      "should": [
        { "match": { "remark": { "query": "java", "boost": 3 } } },
        { "match": { "address": { "query": "长沙", "boost": 2 } } }
      ]
    }
  }
}
```

### 2、constant_score

```json
# 过滤结果评分统一为 1.0
GET /employee/_search
{
  "query": {
    "constant_score": {
      "filter": { "range": { "age": { "gte": 25 } } },
      "boost": 1.5
    }
  }
}
```

### 3、exists —— 查询有某字段的文档

```json
GET /employee/_search
{
  "query": { "exists": { "field": "remark" } }
}
```

### 4、prefix / wildcard / regex

```json
# 前缀查询
{ "prefix": { "name": "张" } }

# 通配符查询
{ "wildcard": { "name": "张*" } }

# 正则查询
{ "regexp": { "name": "张.*" } }
```

### 5、fuzzy —— 模糊查询（容错匹配）

```json
GET /employee/_search
{
  "query": {
    "fuzzy": {
      "address": { "value": "白云", "fuzziness": "AUTO" }
    }
  }
}
```

---

## 七、分页查询

### from + size

```json
GET /employee/_search
{
  "from": 0,
  "size": 2,
  "query": { "match_all": {} }
}
```

**from + size 分页限制**：
- `from + size` 不能超过 `index.max_result_window`（默认 10000）
- 深度分页性能开销大（协调节点需从所有分片收集 `from+size` 条数据再排序）

### search_after

```json
GET /employee/_search
{
  "size": 2,
  "query": { "match_all": {} },
  "sort": [{ "age": "asc" }, { "_id": "asc" }],
  "search_after": [25, "1"]    // 上一页最后一条的 sort 值
}
```

---

## 八、高亮显示

```json
GET /employee/_search
{
  "query": { "match": { "address": "广州" } },
  "highlight": {
    "fields": {
      "address": {}
    }
  }
}
```

**返回结果**：
```json
{
  "_source": { "address": "广州天河公园" },
  "highlight": {
    "address": ["<em>广州</em>天河公园"]
  }
}
```

**自定义高亮标签**：
```json
"highlight": {
  "pre_tags": ["<span style='color:red'>"],
  "post_tags": ["</span>"],
  "fields": { "address": {} }
}
```

---

## 九、查询总结

```
全文查询     → match, match_phrase, multi_match
精确查询     → term, terms, range, exists
组合查询     → bool(must/must_not/should/filter)
自定义查询   → boosting, fuzzy, wildcard, regexp, prefix
分页         → from+size / search_after
高亮         → highlight
```

> 官方文档：[Query DSL](https://www.elastic.co/guide/en/elasticsearch/reference/8.14/query-dsl.html)

> 有道云笔记：[ES高级查询Query DSL实战](https://note.youdao.com/s/8WkK3m2H)
