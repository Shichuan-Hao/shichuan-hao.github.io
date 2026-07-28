---
layout: post
title: "ElasticSearch搜索相关性详解：TF-IDF/BM25算法与自定义评分策略"
date: 2022-06-18
categories: [distributed]
tags: [ElasticSearch, 相关性评分, TF-IDF, BM25, 自定义评分, Explain API]
comments: true
---

> 搜索引擎本质是一个匹配过程——从海量数据中找到匹配用户需求的内容。

---

## 一、什么决定了搜索结果的排序？

**相关性**（Relevance）：描述一个文档与查询语句匹配程度的度量标准。通过为每个匹配文档计算**相关性评分（_score）**来实现。

**评判四个维度**：
1. 是否可以找到所有相关的内容
2. 有多少不相关的内容被返回了
3. 文档的打分是否合理
4. 结合业务需求，平衡结果排名

```json
{
  "_score": 1.234,              // ← 这就是相关性评分
  "_source": { ... }
}
```

---

## 二、TF-IDF 评分算法

### 三个核心因子

**1. 词频（TF — Term Frequency）**
```
TF = 某个词在文档中出现的次数 / 文档的总词数
```
- 检索词在文档中出现频率越高，相关性越高

**2. 逆向文本频率（IDF — Inverse Document Frequency）**
```
IDF = log(语料库的文档总数 / (包含该词的文档数 + 1))
```
- 每个词在索引中出现的频率越高，相关性越低
- "是"、"的"、"在" 在所有文档中出现频繁 → 不重要，降低权重

**3. 字段长度归一值（Field-Length Norm）**
- 短 title 中的词比长 content 中的同样词权重大

```
评分 = TF × IDF × field-length norm
```

### 通过 Explain API 查看评分过程

```bash
# 查看评分详情
GET /test_score/_search
{
  "explain": true,
  "query": {
    "match": { "content": "elasticsearch" }
  }
}

# 查看指定文档的评分
GET /test_score/_explain/2
{
  "query": {
    "match": { "content": "elasticsearch" }
  }
}
```

---

## 三、BM25 评分算法

### 从 TF-IDF 到 BM25

- ES 5.x 之前：默认 TF-IDF
- ES 5.x 之后：默认 **Okapi BM25**
- BM = Best Match，25 = 经过 25 次迭代调整

### BM25 对 TF-IDF 的改进

| 问题 | TF-IDF | BM25 |
|------|--------|------|
| TF 无限增长 | 词出现次数越多得分越高 | 随 TF 增长，得分逐渐趋于一个上界 |
| 文档长度影响 | 无节制 | 可调节参数控制 |
| 应用灵活性 | 固定公式 | 多个可调参数 |

**BM25 公式趋势**：
```
Score ↑
  |    ┌────────────────
  |   /
  |  /
  | /
  |/
  └─────────────────→ TF (词频)
  随着词频增加，得分趋于饱和（不会无限增长）
```

---

## 四、自定义评分策略

### 为什么需要自定义评分？

1. **排序偏好**：通过自定义评分满足用户的排序偏好
2. **特殊字段权重**：给特定字段更高权重
3. **业务逻辑需求**：定义复杂的评分逻辑
4. **用户行为数据**：使用点击率等作为评分因素

### 六大自定义评分策略

#### 1、Index Boost（索引级权重）

场景：不同标签的数据存不同索引，需按类别排序展示。

```json
POST my_index_100*/_search
{
  "query": {
    "indices_boost": [
      { "my_index_100a": 3.0 },
      { "my_index_100b": 2.0 },
      { "my_index_100c": 1.0 }
    ],
    "term": { "subject.keyword": { "value": "subject 1" } }
  }
}
```

#### 2、Boosting —— 修改文档相关性

```json
GET /employee/_search
{
  "query": {
    "boosting": {
      "positive": { "match": { "remark": "java" } },
      "negative": { "match": { "remark": "assistant" } },
      "negative_boost": 0.5    // 命中negative的文档降权
    }
  }
}
```

#### 3、function_score —— 最灵活的自定义评分

```json
GET /employee/_search
{
  "query": {
    "function_score": {
      "query": { "match": { "remark": "java" } },
      "functions": [
        {
          "filter": { "term": { "address.keyword": "广州天河公园" } },
          "weight": 3
        },
        {
          "field_value_factor": {
            "field": "age",
            "factor": 0.1,
            "modifier": "log1p"
          }
        }
      ],
      "boost_mode": "multiply"       // multiply/sum/avg/replace
    }
  }
}
```

**function_score 常用函数**：

| 函数 | 说明 |
|------|------|
| `weight` | 权重相乘 |
| `field_value_factor` | 利用文档字段值影响评分 |
| `random_score` | 随机评分 |
| `script_score` | 用 Painless 脚本自定义计算 |

#### 4、rescore —— 查询后二次打分

```json
GET /employee/_search
{
  "query": { "match": { "remark": "java" } },
  "rescore": {
    "window_size": 50,       // 对前50个结果重新打分
    "query": {
      "rescore_query": {
        "match": { "address": { "query": "长沙", "boost": 2 } }
      }
    }
  }
}
```

**执行流程**：
```
初始查询(query) → 结果集(top N)
         ↓
二次打分(rescore) → 对 window_size 条结果重新评分
         ↓
最终排序
```

---

## 五、相关性优化实践

### 1、多字段搜索权重设计

```json
{
  "query": {
    "multi_match": {
      "query": "小米手机",
      "fields": ["name^3", "keywords^2", "subTitle"]
    }
  }
}
```

`^3` 表示 `name` 字段权重是默认的 3 倍。

### 2、搜索建议优化

```json
# match_phrase_prefix 实现输入提示
GET /employee/_search
{
  "query": {
    "match_phrase_prefix": {
      "address": { "query": "广州" }
    }
  }
}
```

### 3、搜索结果预期调整

```
搜索引擎核心目标：
  
  用户期望的结果          用户实际得到的结果
  ┌──────────┐           ┌──────────┐
  │   交集   │           │          │
  │  → 越大越好           │          │
  └──────────┘           └──────────┘
```

---

## 六、总结

```
默认评分  → BM25（ES 5+）
          → TF-IDF + 多个可调参数改进版

查看评分  → Explain API / _explain

自定义评分:
  索引级   → indices_boost
  文档级   → boosting / negative_boost
  字段级   → function_score（最强灵活性）
  后处理   → rescore_query（二次打分）
```

> 有道云笔记：[搜索相关性详解](https://note.youdao.com/s/PJRhfowf)
