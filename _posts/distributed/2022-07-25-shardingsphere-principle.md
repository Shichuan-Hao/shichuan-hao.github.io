---
layout: post
title: "随心所欲：ShardingSphere实现原理与内核解析"
date: 2022-07-25
categories: [distributed]
tags: [ShardingSphere, 内核解析, SQL解析, SQL路由, SQL改写, 结果归并]
comments: true

---

## 一、整体架构

```
SQL → 解析 → 路由 → 改写 → 执行 → 归并 → 结果
```

| 阶段 | 职责 |
|------|------|
| **解析** | SQL 词法/语法分析，生成 AST |
| **路由** | 根据分片策略计算目标数据源和表 |
| **改写** | 将逻辑 SQL 改写为物理 SQL |
| **执行** | 并发执行多路 SQL |
| **归并** | 合并多路结果集 |

---

## 二、SQL 解析

### 词法分析 → 语法分析

```
SELECT * FROM t_order WHERE order_id = 1
         ↓ 词法分析
[SELECT, *, FROM, t_order, WHERE, order_id, =, 1]
         ↓ 语法分析 → AST
         SELECT
          /    \
      columns  FROM
       [*]    t_order
                  │
               WHERE (= order_id 1)
```

### 分片条件提取

从 AST 中提取：
- 分片键的值
- WHERE 条件中与分片相关的表达式

---

## 三、SQL 路由

### 路由类型

| 类型 | 说明 | 路由数量 |
|------|------|----------|
| **单播** | 精确命中一片 | 1 |
| **广播** | 所有分片 | N |
| **全库表** | 所有库×所有表 |
| **全库** | 所有库 |
| **全实例** | 所有数据源 |

```
SELECT * FROM t_order WHERE order_id = 1  → order_id%2=1 → ds0.t_order_1 → 单播
SELECT * FROM t_order                      → 所有片 → 广播
```

---

## 四、SQL 改写

### 改写类型

| 改写 | 示例 |
|------|------|
| **表名改写** | `t_order` → `t_order_0` |
| **分页改写** | limit offset → 各片limit 0,offset+size 后归并 |
| **批量改写** | INSERT VALUES 拆分为多条 |
| **聚合改写** | AVG → SUM/COUNT |

---

## 五、结果归并

### 五种归并策略

| 类型 | 说明 |
|------|------|
| **遍历归并** | ORDER BY → 多路有序结果合并排序 |
| **分组归并** | GROUP BY → 多路预排序再分组聚合 |
| **分页归并** | LIMIT → 多路结果重新分页 |
| **聚合归并** | COUNT/SUM → 多路结果累加 |
| **装饰归并** | 单路结果直接透传 |

### 归并举例

```
SELECT * FROM t_order ORDER BY order_id LIMIT 0,10

各分片返回：
  ds0: [order_id=1,3,5,7,9,11,...]
  ds1: [order_id=2,4,6,8,10,12,...]

归并 → 各取前10条 → 合并 → 排序 → 取最终前10条
```

---

## 六、执行引擎

### 两种模式

| 模式 | 说明 | 内存占用 |
|------|------|----------|
| **内存归并** | 全部结果加载到内存 | 高 |
| **流式归并** | 逐条处理（每次只读取1条） | **低** |
| **连接限制** | 限制数据库连接数（默认） | 中 |

---

## 七、总结

```
ShardingSphere 内核流程：
  SQL → Parser(解析AST) 
      → Router(计算分片) 
      → Rewrite(改写表名等) 
      → Execute(并发执行) 
      → Merge(结果归并)

归并核心：
  遍历(排序) + 分组(聚合) + 分页 + 聚合
  流式归并 > 内存归并（低内存、高性能）
```
