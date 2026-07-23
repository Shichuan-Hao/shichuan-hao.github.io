---
title: "ElasticSearch Query DSL 深度解析与聚合分析实战"
date: 2022-06-14
categories: distributed
tags: [ElasticSearch, Query DSL, 聚合分析, BM25, 相关性打分, 全文检索]
mermaid: true
---

> ES 的查询能力远不止 MySQL 的 `WHERE`。从全文匹配到高亮展示，从精确过滤到聚合分析，Query DSL 是一套完整的搜索语言。理解 Query Context vs Filter Context、相关性打分原理（TF-IDF → BM25），是用好 ES 的关键。

## 一、Query DSL 全貌

> ES 把 Lucene 语法包装成 JSON 格式查询语法。Query DSL 包含两大块：叶子查询（match/term/range）和组合查询（bool）。

### 1.1 查询所有（match_all）

最简单也最常用的查询：

```json
GET /employee/_search
{
  "query": {
    "match_all": {
      "boost": 1.2    # 相关性分数加权
    }
  }
}
```

### 1.2 分页查询

```json
GET /employee/_search
{
  "from": 0,
  "size": 10,
  "query": {
    "match_all": {}
  },
  "sort": [
    { "age": { "order": "desc" } },
    { "name": { "order": "asc" } }
  ]
}
```

> 还可以用 `sort` 对 `_score` 进行排序。

### 1.3 返回指定字段（_source）

```json
GET /employee/_search
{
  "_source": ["name", "age"],
  "query": { "match_all": {} }
}
```

### 1.4 Query Context vs Filter Context

| 上下文 | 回答的问题 | 是否打分 | 是否缓存 | 适用场景 |
|--------|----------|---------|---------|---------|
| **Query** | 这个文档**有多匹配**？ | ✅ 相关度评分 | ❌ 不缓存 | 全文搜索，需排序 |
| **Filter** | 这个文档**是否匹配**？ | ❌ 不分 | ✅ 自动缓存 | 精确匹配，范围过滤 |

**关键认知**：搜索中先用 **Filter 缩小范围**，再用 **Query 打分排序**，是性能最佳实践。

---

## 二、全文查询（Full Text Query）

### 2.1 match：智能全文检索

```json
# 搜索 address 包含"广州白云山公园"的文档
GET /employee/_search
{
  "query": {
    "match": {
      "address": {
        "query": "广州白云山公园",
        "operator": "or"       # or(默认)/and
      }
    }
  }
}
```

**operator='or' vs 'and' 的区别**：

- **or**：目标文档字段中**任意**查询条件分词匹配即可。查询例句中每个分词匹配越多越靠前。
- **and**：目标文档字段必须包含查询条件**所有**分词。可搭配 `minimum_should_match`。

### 2.2 match_phrase：短语匹配

```json
GET /employee/_search
{
  "query": {
    "match_phrase": {
      "address": "广州白云山"    # 分词顺序+位置必须一致
    }
  }
}
```

| 参数 | 说明 |
|------|------|
| `query` | 查询条件 |
| `analyzer` | 分词器 |
| `slop` | 两个分词之间允许的最大间隔距离（默认0） |

**slop 实战**：

```json
# slop=1：允许"广州 白云山"之间隔一个词
GET /employee/_search
{
  "query": {
    "match_phrase": {
      "address": {
        "query": "广州白云山",
        "slop": 1
      }
    }
  }
}
```

### 2.3 multi_match：多字段搜索

**best_fields**（默认）：匹配评分最高的字段作为最终评分：

```json
GET /employee/_search
{
  "query": {
    "multi_match": {
      "query": "java",
      "type": "best_fields",
      "fields": ["remark", "address"]
    }
  }
}
```

**most_fields**：多个字段的综合评分：

```json
GET /employee/_search
{
  "query": {
    "multi_match": {
      "query": "java elasticStack",
      "type": "most_fields",
      "fields": ["remark^3", "address^2"]
    }
  }
}
```

**cross_fields**：跨字段搜索（所有字段视为一个整体）：

```json
GET /employee/_search
{
  "query": {
    "multi_match": {
      "query": "Jack 湖南",
      "type": "cross_fields",
      "fields": ["name", "address"]
    }
  }
}
```

### 2.4 query_string

支持使用逻辑运算符构建复杂查询：

```json
GET /employee/_search
{
  "query": {
    "query_string": {
      "default_field": "address",
      "query": "白云山 AND 公园"      # 必须同时包含"白云山"和"公园"
    }
  }
}
```

> `query_string` 使用时注意：查询条件中的 `AND | OR` 运算符**必须全大写**。

### 2.5 simple_query_string

类似 `query_string` 但更健壮，不会因为用户的语法错误而抛出异常。

### 2.6 Intervals 查询

让用户对查询术语的顺序和临近度进行细粒度的**完全控制**：

```json
GET /employee/_search
{
  "query": {
    "intervals": {
      "address": {
        "all_of": {
          "ordered": true,
          "intervals": [
            { "match": { "query": "广州" } },
            { "match": { "query": "白云山" } }
          ],
          "max_gaps": 3
        }
      }
    }
  }
}
```

---

## 三、精确值查询（Term-Level Query）

### 3.1 term：精确匹配（不分词）

```json
GET /employee/_search
{
  "query": {
    "term": { "name.keyword": "张三" }
  }
}
```

> ⚠️ `term` 查询**不会对输入分词**。全文检索字段应使用 `match`，精确值字段（keyword/数字/日期/boolean）使用 `term`。

### 3.2 terms：多值匹配

```json
GET /employee/_search
{
  "query": {
    "terms": { "name.keyword": ["张三", "李四"] }
  }
}
```

### 3.3 range：范围查询

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

| 参数 | 含义 |
|------|------|
| `gte` | greater than or equal |
| `gt` | greater than |
| `lte` | less than or equal |
| `lt` | less than |

### 3.4 exists / prefix / wildcard / regexp / fuzzy / ids

```json
# exists：字段存在
GET /employee/_search
{ "query": { "exists": { "field": "address" } } }

# prefix：前缀匹配
GET /employee/_search
{ "query": { "prefix": { "name.keyword": "张" } } }

# wildcard：通配符（? 单字符, * 多字符）
GET /employee/_search
{ "query": { "wildcard": { "name.keyword": "张*" } } }

# regexp：正则匹配
GET /employee/_search
{ "query": { "regexp": { "name.keyword": "张.*" } } }

# fuzzy：模糊匹配（支持错别字纠正）
GET /employee/_search
{ "query": { "fuzzy": { "name.keyword": "张山" } } }  # 可能匹配到"张三"

# ids：按 ID 列表查询
GET /employee/_search
{ "query": { "ids": { "values": ["1", "2", "5"] } } }
```

> `prefix`/`wildcard`/`fuzzy` 查询性能较差，特别是**通配符开头**会导致全量扫描，生产环境慎用。

---

## 四、组合查询（Compound Query）

### 4.1 bool：布尔查询

```json
GET /employee/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "address": "广州" } }
      ],
      "should": [
        { "match_phrase": { "remark": "java" } },
        { "match_phrase": { "remark": "python" } },
        { "match_phrase": { "remark": "php" } }
      ],
      "must_not": [
        { "match": { "address": "长沙" } }
      ],
      "minimum_should_match": 1,
      "filter": {
        "range": { "age": { "gte": 20, "lte": 28 } }
      }
    }
  }
}
```

| 子句 | 逻辑 | 是否影响评分 |
|------|------|------------|
| `must` | **必须匹配**（AND） | ✅ 影响 |
| `should` | **或匹配**（OR） | ✅ 影响 |
| `must_not` | **必须不匹配**（NOT） | ❌ Filter Context |
| `filter` | **必须匹配**（不评分） | ❌ Filter Context |

> `filter` 和 `must_not` 同为 Filter Context，不计算评分、可被缓存，性能优于 `must`。

**同一个 bool 中多 filter/must/must_not**：

```json
{
  "bool": {
    "must": [
      {"match": {"title": "Search"}},
      {"match": {"content": "Elasticsearch"}}
    ],
    "filter": [
      {"term": {"status": "published"}},
      {"range": {"publish_date": {"gte": "2015-01-01"}}}
    ]
  }
}
```

### 4.2 boosting

`positive` 中匹配会提高评分，`negative` 中匹配会**降低评分**：

```json
GET /employee/_search
{
  "query": {
    "boosting": {
      "positive": { "term": { "address": "广州" } },
      "negative": { "term": { "address": "白云山" } },
      "negative_boost": 0.5
    }
  }
}
```

### 4.3 constant_score / dis_max / function_score

```json
# constant_score：包装 filter，统一评分
GET /employee/_search
{
  "query": {
    "constant_score": {
      "filter": { "term": { "name.keyword": "张三" } },
      "boost": 1.2
    }
  }
}

# dis_max：取最佳匹配 fields 的最高评分
GET /employee/_search
{
  "query": {
    "dis_max": {
      "queries": [
        { "match": { "remark": "java" } },
        { "match": { "address": "java" } }
      ],
      "tie_breaker": 0.7
    }
  }
}

# function_score：自定义打分函数
GET /employee/_search
{
  "query": {
    "function_score": {
      "query": { "match": { "remark": "java" } },
      "boost": "5",
      "functions": [
        {
          "filter": { "match": { "address": "广州" } },
          "random_score": {},
          "weight": 50
        }
      ],
      "max_boost": 80,
      "boost_mode": "multiply"
    }
  }
}
```

function_score 支持多种打分函数：**weight**、**random_score**、**script_score**、**field_value_factor**、衰减函数（gauss/linear/exp）。

---

## 五、聚合分析（Aggregation）

### 5.1 聚合的分类

| 分类 | 说明 | 示例 |
|------|------|------|
| **Bucket** | 将文档归纳到不同的 bucket | terms, range, date_histogram |
| **Metric** | 从文档中计算指标 | avg, sum, min, max, stats |
| **Pipeline** | 对其他聚合结果再聚合 | moving_avg, derivative |

### 5.2 Bucket 聚合实战

**terms：按字段值分桶**：

```json
GET /employee/_search
{
  "size": 0,                  # 不需要文档内容
  "aggs": {
    "age_aggs": {
      "terms": { "field": "age", "size": 10 }
    }
  }
}
```

**range：按范围分桶**：

```json
GET /employee/_search
{
  "size": 0,
  "aggs": {
    "age_range": {
      "range": {
        "field": "age",
        "ranges": [
          { "to": 20 },
          { "from": 20, "to": 30 },
          { "from": 30 }
        ]
      }
    }
  }
}
```

**date_histogram：按时间分桶**（销售数据分析场景）：

```json
GET /employee/_search
{
  "size": 0,
  "aggs": {
    "enrolled_over_time": {
      "date_histogram": {
        "field": "enrolled_date",
        "calendar_interval": "month",    # year/quarter/month/week/day/hour
        "format": "yyyy-MM-dd"
      }
    }
  }
}
```

### 5.3 Metric 聚合实战

```json
GET /employee/_search
{
  "size": 0,
  "aggs": {
    "age_stats": {
      "stats": { "field": "age" }    # min/max/avg/sum/count 一次算出
    }
  }
}
```

**嵌套聚合**（分桶 + 指标）：

```json
# 按性别分组 → 组内计算平均年龄
GET /employee/_search
{
  "size": 0,
  "aggs": {
    "sex_aggs": {
      "terms": { "field": "sex" },
      "aggs": {
        "avg_age": { "avg": { "field": "age" } },
        "age_stats": { "stats": { "field": "age" } }
      }
    }
  }
}
```

### 5.4 Pipeline 聚合实战

**min_bucket**：

```json
GET /employee/_search
{
  "size": 0,
  "aggs": {
    "sales_per_month": {
      "date_histogram": {
        "field": "enrolled_date",
        "calendar_interval": "month"
      },
      "aggs": {
        "sales": { "sum": { "field": "age" } }
      }
    },
    "min_monthly_sales": {
      "min_bucket": { "buckets_path": "sales_per_month>sales" }
    }
  }
}
```

**avg_bucket / max_bucket / stats_bucket**：

```json
"aggs": {
  "avg_monthly_sales": {
    "avg_bucket": { "buckets_path": "sales_per_month>sales" }
  },
  "stats_monthly_sales": {
    "stats_bucket": { "buckets_path": "sales_per_month>sales" }
  }
}
```

---

## 六、高亮显示（Highlighting）

```json
GET /employee/_search
{
  "query": { "match": { "address": "广州" } },
  "highlight": {
    "pre_tags": ["<font color='red'>"],
    "post_tags": ["</font>"],
    "fields": {
      "address": {
        "number_of_fragments": 1
      },
      "remark": {
        "number_of_fragments": 0,  # 返回整个字段
        "fragment_size": 200
      }
    }
  }
}
```

| 模式 | 说明 |
|------|------|
| `unified`（默认） | 句子 / 整个字段 |
| `plain` | 根据单词定位两者结合 |
| `fast-vector-highlighter`（fvh） | 更快更大，使用 term_vectors |

---

## 七、相关性评分原理

### 7.1 Lucene TF-IDF 模型

```
TF-IDF = 词频（TF） × 逆文档频率（IDF） × 字段长度归一化（Field Norm）
```

| 因子 | 含义 | 说明 |
|------|------|------|
| **TF（词频）** | 搜索词在文档中出现的次数 | 越多越相关，ES 5.0 前用 `√次数`，之后 BM25 改用非线性饱和 |
| **IDF（逆文档频率）** | `log(文档总数 / 包含该词的文档数)` | 搜索词越少见，权重越高 |
| **Field-length Norm** | 字段越短，权重越高 | 短文本中的搜索词更有代表性 |

### 7.2 BM25（ES 5.0+ 默认算法）

BM25 在 TF-IDF 基础上的改进：

1. **TF 的非线性饱和处理**：出现第 1 次权重显著增加，出现第 5 次及之后权重增长趋缓
2. **更好的 Field-length Norm**：参数 `b` 的默认值 0.75，值越大对字段长度的惩罚越明显
3. **通用性**：目前被广泛认为是最好的全文检索算法之一

### 7.3 explain：查看评分详情

```json
GET /employee/_search
{
  "explain": true,
  "query": { "match": { "address": "广州" } }
}
```

### 7.4 自定义打分

```json
GET /employee/_search
{
  "query": {
    "script_score": {
      "query": { "match": { "address": "广州" } },
      "script": {
        "source": "_score * doc['age'].value < 25 ? 1.5 : 1"
      }
    }
  }
}
```

> ⚠️ 尽量不要使用 script_score，复杂脚本会严重影响性能。优先考虑 `boost` 和 `function_score`。

---

## 八、全文搜索实战案例

**场景：电商商品搜索**：

```json
GET /product_info/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "理财 稳定 收益",
            "fields": ["productName^3", "describe"]
          }
        }
      ],
      "filter": [
        { "term": { "status": "on_sale" } },
        { "range": { "price": { "gte": 100, "lte": 10000 } } }
      ]
    }
  },
  "sort": [
    { "_score": { "order": "desc" } },
    { "sales_volume": { "order": "desc" } }
  ],
  "highlight": {
    "fields": {
      "productName": {},
      "describe": {}
    }
  },
  "from": 0,
  "size": 20
}
```

---

## 九、总结

| 分类 | 核心 API | 说明 |
|------|---------|------|
| 全文查询 | `match`/`match_phrase`/`multi_match` | 会分词，计算评分 |
| 精确查询 | `term`/`terms`/`range` | 不分词，用于 Filter |
| 组合查询 | `bool`(must/should/must_not/filter) | filter 不评分可缓存 |
| 自定义分 | `boosting`/`function_score`/`dis_max` | 调整排序 |
| 聚合 | Bucket/Metric/Pipeline | 分组统计 |
| 高亮 | highlight | 搜索结果标注 |
| 评分 | BM25（TF+IDF饱和+字段长度） | explain 查看细节 |

> Query Context 回答"有多匹配"，Filter Context 回答"是否匹配"。搜索中先用 Filter 缩小范围，再用 Query 打分排序，是最佳实践。
