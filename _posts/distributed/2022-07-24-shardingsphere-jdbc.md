---
layout: post
title: "见招拆招：ShardingJDBC分库分表实战指南"
date: 2022-07-24
categories: [distributed]
tags: [ShardingSphere, ShardingJDBC, 分库分表, 数据分片, 读写分离]
comments: true

---

## 一、ShardingJDBC 定位

ShardingSphere-JDBC 定位为轻量级 Java 框架，在 JDBC 层提供分库分表、读写分离等增强功能，属于**客户端分片**方案。

```
Application → ShardingJDBC(JDBC增强) → DB1, DB2, DB3...
```

### Maven 依赖

```xml
<dependency>
    <groupId>org.apache.shardingsphere</groupId>
    <artifactId>shardingsphere-jdbc-core</artifactId>
    <version>5.5.0</version>
</dependency>
```

---

## 二、分库分表 YAML 配置

```yaml
dataSources:
  ds0:
    dataSourceClassName: com.zaxxer.hikari.HikariDataSource
    driverClassName: com.mysql.cj.jdbc.Driver
    jdbcUrl: jdbc:mysql://localhost:3306/db0
    username: root
    password: root
  ds1:
    dataSourceClassName: com.zaxxer.hikari.HikariDataSource
    driverClassName: com.mysql.cj.jdbc.Driver
    jdbcUrl: jdbc:mysql://localhost:3306/db1
    username: root
    password: root

rules:
  - !SHARDING
    tables:
      t_order:
        actualDataNodes: ds$->{0..1}.t_order_$->{0..1}
        tableStrategy:
          standard:
            shardingColumn: order_id
            shardingAlgorithmName: t_order_inline
        databaseStrategy:
          standard:
            shardingColumn: user_id
            shardingAlgorithmName: ds_inline
    shardingAlgorithms:
      t_order_inline:
        type: INLINE
        props:
          algorithm-expression: t_order_$->{order_id % 2}
      ds_inline:
        type: INLINE
        props:
          algorithm-expression: ds_$->{user_id % 2}

props:
  sql-show: true
```

**解读**：
- 2 个库（ds0、ds1）× 每库 2 张表（t_order_0, t_order_1）= 4 张表
- `user_id % 2` → 决定库
- `order_id % 2` → 决定表

---

## 三、四种分片策略

### 1、Standard（标准分片）

```java
public class CustomShardingAlgorithm implements StandardShardingAlgorithm<Long> {
    @Override
    public String doSharding(Collection<String> availableTargetNames, 
            PreciseShardingValue<Long> shardingValue) {
        Long orderId = shardingValue.getValue();
        String target = "t_order_" + (orderId % availableTargetNames.size());
        for (String name : availableTargetNames) {
            if (name.endsWith(target)) return name;
        }
        throw new RuntimeException("No match");
    }
}
```

### 2、Hint（强制路由）

```java
HintManager hintManager = HintManager.getInstance();
hintManager.addTableShardingValue("t_order", 0);  // 强制路由到 table_0
// ...执行SQL...
hintManager.close();
```

### 3、Complex（复合分片）

多分片键场景，例如 `user_id` 和 `order_id` 同时参与分片决策。

### 4、Broadcast（广播表）

每个库都有全量数据的表（如字典表），不分片。

---

## 四、读写分离

```yaml
- !READWRITE_SPLITTING
  dataSources:
    readwrite_ds:
      writeDataSourceName: ds0_master
      readDataSourceNames:
        - ds0_slave1
        - ds0_slave2
      loadBalancerName: round_robin
  loadBalancers:
    round_robin:
      type: ROUND_ROBIN
```

---

## 五、分布式主键

```yaml
# 雪花算法 keyGenerator
keyGenerators:
  snowflake:
    type: SNOWFLAKE
```

```java
@TableId(type = IdType.ASSIGN_ID)
private Long orderId;
```

---

## 六、实战技巧

### 1、避免跨表查询

```sql
-- ❌ 错误：跨分片关联
SELECT * FROM t_order o LEFT JOIN t_order_item i ON o.order_id = i.order_id;

-- ✅ 正确：订单号做关联键，保证同一库
```

### 2、分页处理

ShardingJDBC 会自动对分页查询做归并，但深度分页性能较差。

### 3、绑定表

```yaml
bindingTables:
  - t_order, t_order_item   # 同分片规则，避免笛卡尔积
```

---

## 七、总结

```
ShardingJDBC 核心：
  数据源 × 分片策略 = 分库分表
  Standard(单键) + Hint(强制) + Complex(多键)

配置三要素：
  actualDataNodes → 分片键 → 分片算法

补充能力：
  读写分离 + 分布式主键 + 绑定表 + 广播表
```
