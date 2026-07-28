---
layout: post
title: "ElasticSearch聚合操作详解：Metric/Bucket/Pipeline三类聚合实战"
date: 2022-06-19
categories: [distributed]
tags: [ElasticSearch, 聚合查询, Aggregation, Bucket, Metric, Pipeline, 数据分析]
comments: true
---

> ES 除搜索以外，提供了强大的数据统计分析功能——聚合（Aggregations），类似 MySQL 的 GROUP BY + 聚合函数。

---

## 一、聚合概述

### 什么是聚合（Aggregations）

```
聚合查询 = 查询条件 + 聚合函数 + 聚合嵌套

解决的问题：
  · 什么品牌最受欢迎？
  · 平均价格、最高价格、最低价格？
  · 每月的销售情况？
```

### 应用场景

| 场景 | 聚合用途 |
|------|----------|
| 电商平台 | 统计各地区销售额、用户消费总额、产品销售量 |
| 社交媒体 | 统计发布/转发/评论次数，按地区/时间/话题维度分析 |
| 物流企业 | 统计各区域运输量、车辆运输次数 |
| 金融企业 | 统计客户交易总额、产品销售、交易员业绩 |
| 智能家居 | 统计设备使用次数、能源消耗量 |

---

## 二、聚合基本语法

```json
GET <index_name>/_search
{
  "aggs": {
    "<aggs_name>": {          // 聚合名称（自定义）
      "<agg_type>": {         // 聚合类型
        "field": "<field_name>"
      }
    }
  }
}
```

**不使用 query 时聚合所有文档**。也可以组合使用 `query` + `aggs`：先筛选后聚合（类似 SQL 的 WHERE + GROUP BY）。

---

## 三、聚合三大分类

### 类比 MySQL

| MySQL | ES 聚合类型 |
|-------|-----------|
| `SELECT AVG(price)` | Metric 聚合 |
| `GROUP BY size` | Bucket 聚合 |
| 对子查询结果再聚合 | Pipeline 聚合 |

---

## 四、Metric 聚合（指标聚合）

对文档字段进行数学运算。

### 1、示例数据

```bash
DELETE /employees

PUT /employees
{
  "mappings": {
    "properties": {
      "age": { "type": "integer" },
      "gender": { "type": "keyword" },
      "job": {
        "type": "text",
        "fields": { "keyword": { "type": "keyword", "ignore_above": 50 } }
      },
      "name": { "type": "keyword" },
      "salary": { "type": "integer" }
    }
  }
}

PUT /employees/_bulk
{ "index" : { "_id" : "1" } }
{ "name":"Emma","age":32,"job":"Product Manager","gender":"female","salary":35000 }
{ "index" : { "_id" : "2" } }
{ "name":"Underwood","age":41,"job":"Dev Manager","gender":"male","salary":50000 }
{ "index" : { "_id" : "3" } }
{ "name":"Tran","age":25,"job":"Web Designer","gender":"male","salary":18000 }
{ "index" : { "_id" : "4" } }
{ "name":"Rivera","age":26,"job":"Web Designer","gender":"female","salary":22000 }
{ "index" : { "_id" : "5" } }
{ "name":"Rose","age":25,"job":"QA","gender":"female","salary":18000 }
{ "index" : { "_id" : "6" } }
{ "name":"Lucy","age":31,"job":"QA","gender":"female","salary":25000 }
{ "index" : { "_id" : "7" } }
{ "name":"Byrd","age":27,"job":"QA","gender":"male","salary":20000 }
```

### 2、常用 Metric 聚合

```json
# 统计 salary 的各种指标
GET /employees/_search
{
  "aggs": {
    "avg_salary": { "avg": { "field": "salary" } },
    "max_salary": { "max": { "field": "salary" } },
    "min_salary": { "min": { "field": "salary" } },
    "sum_salary": { "sum": { "field": "salary" } }
  }
}
```

```json
# 统计（count/value_count/cardinality/stats）
{
  "aggs": {
    "total_count": { "value_count": { "field": "name" } },
    "distinct_jobs": { "cardinality": { "field": "job.keyword" } },
    "salary_stats": { "stats": { "field": "salary" } },
    "percentiles": { "percentiles": { "field": "salary" } }
  }
}
```

**Metric 函数总结**：

| 函数 | SQL 类比 | 说明 |
|------|----------|------|
| `avg` | AVG() | 平均值 |
| `max` | MAX() | 最大值 |
| `min` | MIN() | 最小值 |
| `sum` | SUM() | 求和 |
| `value_count` | COUNT() | 非空计数 |
| `cardinality` | COUNT(DISTINCT) | 去重计数（近似） |
| `stats` | — | 一次性返回 min/max/avg/sum/count |
| `percentiles` | — | 百分位统计 |
| `top_hits` | — | 每个桶中的 top N 文档 |

---

## 五、Bucket 聚合（桶聚合）

将文档分组到不同的"桶"中。

### 1、Terms —— 按字段值分组

```json
GET /employees/_search
{
  "aggs": {
    "by_gender": {
      "terms": { "field": "gender" }
    }
  }
}
```

**size 参数**（返回 Top N 桶）：
```json
"terms": { "field": "gender", "size": 10 }
```

### 2、Range —— 数值范围分组

```json
GET /employees/_search
{
  "aggs": {
    "salary_ranges": {
      "range": {
        "field": "salary",
        "ranges": [
          { "to": 20000 },
          { "from": 20000, "to": 40000 },
          { "from": 40000 }
        ]
      }
    }
  }
}
```

### 3、Date Histogram —— 日期直方图

```json
{
  "aggs": {
    "by_month": {
      "date_histogram": {
        "field": "create_time",
        "calendar_interval": "month",
        "format": "yyyy-MM"
      }
    }
  }
}
```

`calendar_interval` 可选：`minute` / `hour` / `day` / `week` / `month` / `year`

### 4、Filter —— 按条件分组

```json
{
  "aggs": {
    "high_salary": {
      "filter": { "range": { "salary": { "gte": 30000 } } }
    }
  }
}
```

---

## 六、Metric + Bucket 嵌套

**SQL 对比**：

```sql
-- SQL: 按性别统计薪资
SELECT gender, AVG(salary), MAX(salary)
FROM employees
GROUP BY gender;
```

```json
// ES DSL 等价写法
GET /employees/_search
{
  "aggs": {
    "by_gender": {
      "terms": { "field": "gender" },
      "aggs": {
        "avg_salary": { "avg": { "field": "salary" } },
        "max_salary": { "max": { "field": "salary" } }
      }
    }
  }
}
```

**输出**：
```json
{
  "aggregations": {
    "by_gender": {
      "buckets": [
        {
          "key": "female",
          "doc_count": 4,
          "avg_salary": { "value": 25000.0 },
          "max_salary": { "value": 35000.0 }
        },
        {
          "key": "male",
          "doc_count": 3,
          "avg_salary": { "value": 29333.0 },
          "max_salary": { "value": 50000.0 }
        }
      ]
    }
  }
}
```

---

## 七、Pipeline 聚合

对聚合结果进行二次聚合。

### 常用的 Pipeline 聚合

```json
# average_bucket —— 求桶平均值
{
  "aggs": {
    "by_gender": {
      "terms": { "field": "gender" },
      "aggs": {
        "avg_salary_bucket": { "avg": { "field": "salary" } }
      }
    },
    "overall_avg": {
      "avg_bucket": {
        "buckets_path": "by_gender>avg_salary_bucket"
      }
    }
  }
}
```

**Pipeline 类型**：
- `avg_bucket` / `min_bucket` / `max_bucket` / `sum_bucket`
- `derivative`：计算相邻桶的差值
- `cumulative_sum`：桶累计和

---

## 八、聚合查询优化

### 1、控制聚合精度

```json
"terms": {
  "field": "gender",
  "size": 20,                   // 返回前20个桶
  "shard_size": 100             // 每个分片返回的候选桶数
}
```

### 2、使用 filter 缩小聚合范围

```json
{
  "query": { "range": { "age": { "gte": 25 } } },
  "aggs": {
    "by_gender": { "terms": { "field": "gender" } }
  }
}
```

### 3、聚合缓存

- `query` 阶段的 filter 可用于聚合过滤
- ES 会自动缓存 filter 结果
- 复杂聚合注意内存消耗

---

## 九、总结

```
聚合三层次：

  Metric 聚合     → avg/max/min/sum/stats/cardinality
  Bucket 聚合     → terms/range/date_histogram/filter
  Pipeline 聚合   → avg_bucket/derivative/cumulative_sum

组合使用：
  Query（过滤）→ Bucket（分组）→ Metric（统计）
  类似 SQL: WHERE → GROUP BY → AVG/MAX/MIN

嵌套：
  Bucket 内嵌 Metric（最常用）
  Bucket 内嵌 Bucket（多维度分析）
  Pipeline 聚合二次计算（跨桶运算）
```

> 有道云笔记：[ES聚合操作详解](https://note.youdao.com/s/ICVDmP4d)
