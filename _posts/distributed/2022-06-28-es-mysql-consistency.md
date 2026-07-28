---
layout: post
title: "MySQL到ES数据一致性方案：双写/MQ/定时/Canal四种方案全面对比"
date: 2022-06-28
categories: [distributed]
tags: [ElasticSearch, MySQL, 数据同步, Canal, binlog, 数据一致性]
comments: true
---

> 如何保证 MySQL 和 ES 之间的数据一致性？这是面试高频题，也是微服务架构中必须解的问题。

---

## 一、业务场景

**需求**：酒店搜索系统，用户可按目的地、酒店名、房型、价格等属性全模糊搜索。

**技术指标**：
- QPS: 1000+
- 响应时间: < 500ms
- 数据一致性要求高

**方案**：MySQL 存储酒店数据，ES 提供搜索引擎能力。关键在于如何同步两边的数据。

---

## 二、四种数据一致性方案对比

### 方案总览

```
方案一：同步双写
  业务代码 → MySQL (成功) → ES (成功) → 返回

方案二：MQ 异步双写
  业务代码 → MySQL + MQ → 消费者 → ES

方案三：扫表定时同步
  定时任务 → 扫描 MySQL 增量 → 批量写 ES

方案四：监听 Binlog
  MySQL binlog → Canal → Kafka → 消费者 → ES
```

---

### 方案一：同步双写

**实现**：业务代码中先写 MySQL，成功后同步写 ES。

```java
@Transactional
public void updateHotel(Hotel hotel) {
    // Step 1: 写 MySQL
    hotelMapper.update(hotel);
    // Step 2: 同步写 ES
    elasticsearchTemplate.save(hotel);
}
```

| 优点 | 缺点 |
|------|------|
| 数据一致性高 | 代码耦合度增加 |
| 实时性强 | 性能开销（两次写入） |
| 实现简单 | ES 写失败可能导致不一致 |

**ES 写失败的处理**：
- 方式一：事务回滚（但跨系统事务实现复杂）
- 方式二：记录失败日志 → 后续补偿重试

**适用场景**：旧系统、偏后台管理系统、用户量少、对实时性要求高、治理成本有限。

---

### 方案二：MQ 异步双写

**实现**：写 MySQL 后发 MQ 消息，消费者异步更新 ES。

```
Producer:
  @Transactional
  public void updateHotel(Hotel hotel) {
      hotelMapper.update(hotel);
      rocketMQTemplate.send("hotel-change", hotel);
  }

Consumer:
  @RocketMQMessageListener(topic = "hotel-change", ...)
  public void onMessage(Hotel hotel) {
      elasticsearchTemplate.save(hotel);
  }
```

| 优点 | 缺点 |
|------|------|
| 系统解耦 | 存在同步延迟（秒级） |
| 消息持久化不丢 | 需要补偿机制 |
| 高可用容错 | 系统复杂度增加 |

**顺序问题**：MQ 消息需保证同一 key 的顺序性。

**适用场景**：
- 已引入 MQ 中间件
- 用户体量大、高并发
- 可接受秒级延迟
- 业务变更少

---

### 方案三：扫表定时同步

**实现**：定时任务定期扫描 MySQL 变更数据，批量写入 ES。

```java
@Scheduled(cron = "0 */1 * * * ?")  // 每分钟执行
public void syncData() {
    // 查询上次同步以来的变更
    List<Hotel> hotels = hotelMapper.findByUpdateTime(lastSyncTime);
    // 批量写 ES
    hotels.forEach(esTemplate::save);
    lastSyncTime = new Date();
}
```

| 优点 | 缺点 |
|------|------|
| 实现最简单 | 实时性差 |
| 适合批量数据 | 对 MySQL 有查询压力 |
| 对在线业务影响小 | 数据一致性窗口大 |

**适用场景**：旧系统、用户体量小、偏报表统计类业务、对实时性要求不高。

---

### 方案四：监听 Binlog（推荐）

**实现**：Canal 伪装成 MySQL Slave，监听 binlog，将变更推送到 Kafka，消费者同步 ES。

```
架构：
  MySQL → binlog → Canal Server
                      │
                      ▼
                    Kafka
                      │
                      ▼
                 ES Consumer → Elasticsearch
```

**Canal 原理**：
- Canal 模拟 MySQL Slave 的交互协议
- 将自己伪装为 Slave → 向 Master 发送 dump 协议
- Master 收到 dump 请求 → 推送 binlog 给 Slave
- Canal 解析 binlog 对象 → 推送到 Kafka

| 优点 | 缺点 |
|------|------|
| 业务代码零侵入 | 构建 binlog 系统复杂 |
| 可靠，接近实时 | MQ 存在延时风险 |
| 完全解耦 | 需维护 Canal + Kafka |

**适用场景**：
- 用户可以开放 MySQL binlog
- 互联网公司、用户体量大
- 高并发、可接受秒级延迟

---

## 三、四种方案选型决策树

```
需要强一致性？
  │
  ├─ Yes → 同步双写（小体量）/ XA两阶段提交（大体量但复杂）
  │
  └─ No → 已引入 MQ？
            │
            ├─ Yes → MQ 异步方案
            │
            └─ No → 可开放 binlog？
                      │
                      ├─ Yes → Canal + Kafka
                      │
                      └─ No → 定时扫表
```

---

## 四、数据不一致的补偿机制

不管哪种方案，都需要补偿：

1. **定期对账**：定时任务比较 MySQL 和 ES 数据，发现不一致则补偿
2. **失败重试**：MQ 消费者失败重试 + 死信队列兜底
3. **人工干预入口**：后台管理系统提供手动数据同步按钮
4. **数据版本号**：每条数据带 version，消费者检查版本

---

## 五、总结

```
MySQL → ES 数据同步方案选择：

  实时性要求 + 简单   → 同步双写
  高并发 + 已有 MQ    → MQ 异步
  历史老系统 + 非实时 → 定时扫表
  标准互联网实践      → Canal + binlog（推荐）

补偿机制不可少：
  定期对账 + 失败重试 + 死信队列 + 手动修复
```

> 有道云笔记：[MySQL到ES数据一致性](https://note.youdao.com/s/7cCYHeaP)
