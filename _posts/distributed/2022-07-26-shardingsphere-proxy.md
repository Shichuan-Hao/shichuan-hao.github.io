---
layout: post
title: "登堂入室：深入理解ShardingProxy服务端分库分表"
date: 2022-07-26
categories: [distributed]
tags: [ShardingSphere, ShardingProxy, 分库分表, 服务端代理, MySQL协议]
comments: true

---

## 一、ShardingProxy 定位

### JDBC vs Proxy

| | ShardingJDBC | ShardingProxy |
|------|-------------|---------------|
| **方案** | 客户端分片 | 服务端代理 |
| **部署** | jar 包引入 | 独立服务 |
| **语言** | Java only | MySQL 协议，**多语言通用** |
| **维护** | 嵌入式 | 运维独立 |
| **性能** | 高（无网络跳转） | 中（多一跳） |

```
ShardingJDBC:
  App(Java) → [ShardingJDBC] → DB

ShardingProxy:
  App(Java/Python/Go/...) → ShardingProxy → DB
```

---

## 二、安装配置

### 下载与启动

```bash
wget https://dlcdn.apache.org/shardingsphere/5.5.0/apache-shardingsphere-5.5.0-shardingsphere-proxy-bin.tar.gz
tar -xzf apache-shardingsphere-5.5.0-shardingsphere-proxy-bin.tar.gz
cd apache-shardingsphere-5.5.0-shardingsphere-proxy-bin
```

### Server YAML 配置

```yaml
# conf/server.yaml
authority:
  users:
    - user: root@%
      password: root
  privilege:
    type: ALL_PERMITTED

props:
  proxy-frontend-database-protocol-type: MySQL
```

### 分片规则配置

```yaml
# conf/config-sharding.yaml
databaseName: sharding_db

dataSources:
  ds0:
    url: jdbc:mysql://192.168.1.1:3306/db0
    username: root
    password: root
  ds1:
    url: jdbc:mysql://192.168.1.2:3306/db1
    username: root
    password: root

rules:
  - !SHARDING
    tables:
      t_order:
        actualDataNodes: ds$->{0..1}.t_order_$->{0..1}
        databaseStrategy:
          standard:
            shardingColumn: user_id
            shardingAlgorithmName: ds_inline
        tableStrategy:
          standard:
            shardingColumn: order_id
            shardingAlgorithmName: t_order_inline
    shardingAlgorithms:
      ds_inline:
        type: INLINE
        props:
          algorithm-expression: ds_$->{user_id % 2}
      t_order_inline:
        type: INLINE
        props:
          algorithm-expression: t_order_$->{order_id % 2}
```

### 启动

```bash
bin/start.sh          # 启动 (端口 3307)
tail -f logs/stdout.log

# 连接
mysql -h 127.0.0.1 -P 3307 -u root -p
USE sharding_db;
INSERT INTO t_order ...  -- 自动分片
```

---

## 三、Proxy 核心优势

| 优势 | 说明 |
|------|------|
| **多语言支持** | 支持 MySQL/PostgreSQL 协议，Java/Python/Go 通用 |
| **透明接入** | 应用无需改代码，换连接地址即可 |
| **治理集中** | 分片规则在 Proxy 配置，不用到处维护 |
| **监控方便** | 中间件层统一监控 SQL 执行情况 |

---

## 四、JDBC vs Proxy 选型

| 场景 | 推荐 |
|------|------|
| Java 单一应用 | ShardingJDBC（性能高） |
| 多语言混合 | ShardingProxy |
| 已有系统改造 | ShardingProxy（零代码侵入） |
| 性能要求极高 | ShardingJDBC（无网络跳转） |
| 规则频繁调整 | ShardingProxy（集中管理） |

---

## 五、总结

```
ShardingProxy = MySQL 协议代理 + 分库分表
  优势：多语言通用 + 零代码侵入 + 集中治理
  劣势：多一跳网络延迟

选型：
  单语言Java → JDBC
  多语言/零侵入 → Proxy
```
