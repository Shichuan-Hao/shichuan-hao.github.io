---
layout: post
title: "Redis Stack扩展功能实战：JSON/Search/TimeSeries/Bloom"
date: 2022-06-12
categories: [distributed]
tags: [Redis, Redis Stack, JSON, RedisSearch, TimeSeries, 布隆过滤器]
comments: true
---

> Redis Stack 是基于 Redis OSS 的更完整技术栈，提供 JSON、Search、Bloom Filter、TimeSeries 等高级扩展功能，将 Redis 的定位从纯缓存扩展到多模型数据库。

---

## 一、Redis Stack 概述

### Redis OSS vs Redis Stack

```
Redis OSS (Open Source)：
  数据类型 → String/Hash/List/Set/ZSet/Bitmap 等

Redis Stack：
  Redis OSS + 多个扩展模块
  ├── RedisJSON      → JSON文档存储和操作
  ├── RediSearch     → 全文搜索和二级索引
  ├── RedisTimeSeries → 时序数据
  ├── RedisBloom     → 布隆过滤器和概率数据结构
  └── RedisGraph     → 图数据库（已停止维护）
```

### 安装方式

```bash
# 方式1：Docker
docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest

# 方式2：下载安装包（需科学上网）
# https://redis.io/downloads/

# 确认已安装的模块
127.0.0.1:6379> MODULE LIST
```

---

## 二、RedisJSON

### 基础操作

```bash
# 存入JSON
JSON.SET user:1 $ '{"name":"roy","age":18,"address":{"city":"深圳","lane":"南山大道"}}'

# 获取整个JSON
JSON.GET user:1
# → {"name":"roy","age":18,"address":{"city":"深圳","lane":"南山大道"}}

# 获取指定字段
JSON.GET user:1 $.name
# → ["roy"]

JSON.GET user:1 $.age $.address.city
# → {"$.age":[18],"$.address.city":["深圳"]}

# 格式美化
JSON.GET user:1 $.address.lane INDENT "\t" NEWLINE "\n" SPACE " "
```

**核心指令**：

| 指令 | 说明 |
|------|------|
| `JSON.SET` | 存入 JSON |
| `JSON.GET` | 获取 JSON |
| `JSON.DEL` | 删除路径 |
| `JSON.TYPE` | 获取类型 |
| `JSON.NUMINCRBY` | 数字增量 |
| `JSON.STRAPPEND` | 字符串追加 |
| `JSON.STRLEN` | 字符串长度 |
| `JSON.ARRAPPEND` | 数组追加 |
| `JSON.ARRPOP` | 数组弹出 |
| `JSON.ARRINDEX` | 查找索引 |
| `JSON.ARRINSERT` | 插入元素 |
| `JSON.ARRLEN` | 数组长度 |
| `JSON.ARRTRIM` | 截取数组 |
| `JSON.OBJKEYS` | 返回对象所有 key |
| `JSON.OBJLEN` | 对象 key 数量 |

### 高级操作

```bash
# 数字递增
JSON.NUMINCRBY user:1 $.age 1

# 新增字段（路径不存在则创建）
JSON.SET user:1 $.son '{"name":"lily","age":...}'
JSON.SET user:1 $.daughter '{"name":"lucy","age":...}'

# 通配符操作
JSON.GET user:1 $..age
# → [18, 5, 5]

# 条件操作
JSON.SET user:1 $.isHome true
JSON.GET user:1 $..[?(@.isHome != true)]
# → 返回条件匹配的子元素
```

### JSON 与 Hash 对比

| | JSON | Hash |
|---|---|---|
| 查询方式 | JSONPath 路径表达式 | HGET field |
| 嵌套支持 | ✅ 多层嵌套 | ❌ 仅一层 field-value |
| 部分更新 | ✅ 按路径局部更新 | ✅ HGETSET 等 |
| 数组操作 | ✅ 完整数组指令 | ❌ 无数组概念 |
| 使用场景 | 复杂嵌套文档 | 简单键值对 |

---

## 三、RediSearch

### 什么是 RediSearch

RediSearch 让 Redis 支持**全文搜索**和**二级索引**查询，但与传统搜索引擎不同：
- 索引与数据共同保存在 Hash/JSON 中
- RediSearch 类 Elasticsearch，但数据结构简单很多

### 创建索引

```bash
# 基于 Hash 创建索引
FT.CREATE idx:user ON HASH PREFIX 1 "user:" 
  SCHEMA name TEXT SORTABLE 
  age NUMERIC SORTABLE 
  email TAG SORTABLE

# 基于 JSON 创建索引
FT.CREATE idx:userjson ON JSON PREFIX 1 "user:" 
  SCHEMA $.name AS name TEXT SORTABLE 
  $.age AS age NUMERIC SORTABLE
```

**字段类型**：

| 类型 | 说明 | 排序 | 搜索 |
|------|------|------|------|
| TEXT | 文本，会分词 | ✅ | ✅ |
| NUMERIC | 数字 | ✅ | ✅ 范围搜索 |
| TAG | 逗号分隔的标签 | ✅ | ✅ 精确匹配 |
| GEO | 地理位置 | ❌ | ✅ 范围搜索 |

### 查询语法

```bash
# 全量查询
FT.SEARCH idx:user "*" LIMIT 0 2

# 模糊查询（模糊因子用%包围）
FT.SEARCH idx:user "%wang%" 

# 精确查询与组合
FT.SEARCH idx:user "@name:wang @age:[18 30]"

# 数字范围
FT.SEARCH idx:user "@age:[18,30]"

# 分页
FT.SEARCH idx:user "@age:[18,30]" LIMIT 0 10

# 多条件
FT.SEARCH idx:user "@address:{北京} @age:[20 30]"

# 聚合查询
FT.AGGREGATE idx:user "*" 
  GROUPBY 1 @address 
  REDUCE COUNT 0 AS user_count 
  SORTBY 2 @user_count DESC

# 删除索引
FT.DROPINDEX idx:user
```

### 搜索优化

```bash
# 查看索引信息
FT.INFO idx:user

# 后台索引
FT.CREATE ... ON HASH PREFIX 1 ... SCHEMA ... NOOFFSETS NOSTOPWORDS

# Tag字段优化
FT.CREATE idx:user ON HASH PREFIX 1 "user:"
  SCHEMA email TAG SORTABLE CASESENSITIVE SEPARATOR "|"
```

---

## 四、RedisTimeSeries

### 核心概念

RedisTimeSeries 用于高效存储和查询**时序数据**。

```bash
# 创建时间序列
TS.CREATE sensor:temperature:room RETENTION 86400000 LABELS sensor_id 1 room "bedroom"

# 添加数据点
TS.ADD sensor:temperature:room * 23.5   # * = 自动使用当前时间戳
TS.ADD sensor:temperature:room 1650000000000 22.8

# 范围查询
TS.RANGE sensor:temperature:room 1650000000000 1650001000000

# 使用聚合查询
TS.RANGE sensor:temperature:room 1650000000000 1650086400000 AGGREGATION avg 60000
```

### 降采样规则

```bash
# 创建时设置规则
TS.CREATE sensor:temperature:room:avg
TS.CREATERULE sensor:temperature:room sensor:temperature:room:avg 
  AGGREGATION avg 60000   # 1分钟avg聚合
```

**支持的聚合函数**：avg, sum, min, max, range, count, first, last, std.p, std.s, var.p, var.s, twa

---

## 五、RedisBloom

### 布隆过滤器

详见缓存优化篇，这里列举核心指令：

```bash
BF.RESERVE bloom1 0.01 10000         # 创建（误判率1%，容量1W）
BF.ADD bloom1 "item1"
BF.EXISTS bloom1 "item1"
BF.MADD bloom1 a b c
BF.MEXISTS bloom1 a b c d
```

### Cuckoo 过滤器

相比于 Bloom，**支持删除操作**：

```bash
CF.RESERVE cf1 10000
CF.ADD cf1 "item1"
CF.EXISTS cf1 "item1"
CF.DEL cf1 "item1"         # 删除（Bloom不支持！）
CF.COUNT cf1 "item1"
```

### Top-K

统计最常见元素：

```bash
TOPK.RESERVE topk1 3 2000 7 0.925
TOPK.ADD topk1 a b c d e
TOPK.LIST topk1
```

---

## 六、Redis Stack 适用场景总结

| 模块 | 适用场景 | 不适用场景 |
|------|----------|------------|
| JSON | 嵌套复杂文档存储 | 简单KV |
| Search | 商品搜索、全文搜索 | 替代ES（能力差距大） |
| TimeSeries | IoT数据、监控指标 | 常规缓存 |
| Bloom | 防止缓存穿透、去重 | 需要精确判断的场景 |

**总体定位**：Redis Stack 不是要替代 ES、MongoDB 等专用数据库，而是在缓存层提供**适度的扩展能力**，让简单的查询需求不需要再引入额外组件。

> 有道云笔记链接：[Redis Stack扩展功能](https://note.youdao.com/s/IEyQFc7H)
