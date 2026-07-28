---
layout: post
title: "Kafka日志索引详解：LogSegment/稀疏索引/时间戳索引/零拷贝读取"
date: 2022-07-17
categories: [distributed]
tags: [Kafka, 日志索引, LogSegment, 稀疏索引, 零拷贝, 数据存储]
comments: true

---

## 一、Kafka 日志存储结构

```
/data/kafka-logs/
  └── order-0/                   (Topic-Partition)
      ├── 00000000000000000000.log       (日志文件)
      ├── 00000000000000000000.index     (偏移索引)
      ├── 00000000000000000000.timeindex (时间索引)
      ├── 00000000000000000800.log
      ├── 00000000000000000800.index
      └── 00000000000000000800.timeindex
```

---

## 二、LogSegment（日志段）

**LogSegment 三文件**：

| 文件 | 用途 | 特点 |
|------|------|------|
| `.log` | 消息数据 | append-only，达1G自动滚动 |
| `.index` | 偏移量索引 | 稀疏索引（非每条都记录） |
| `.timeindex` | 时间戳索引 | 按时间查找消息 |

---

## 三、稀疏索引原理

### 为什么用稀疏索引？

全量索引 → 索引文件太大 → 影响性能

**稀疏索引**：每 `log.index.interval.bytes`（默认4KB）记录一条

```
.log 文件:
  offset 0: msg(1KB)
  offset 1024: msg(1KB)
  offset 2048: msg(1KB)
  offset 3072: msg(1KB)
  offset 4096: msg(1KB) → 写入 .index 记录

.index 文件:
  relativeOffset: 0 → position: 0
  relativeOffset: 4 → position: 4096
  ...
```

**查找消息**：
```
offset = 3500
→ 定位 LogSegment（文件名范围）
→ 查 .index 找到最近的低位索引（offset 3072 → position 3072）
→ 从 position 3072 开始顺序扫描 .log 找到 offset 3500
```

---

## 四、时间戳索引

```
查找 2小时前的消息：
→ 查 .timeindex（timestamp → offset）
→ 找到 offset → 走 .index 定位 position → 读 .log
```

---

## 五、日志清理策略

| 策略 | 参数 | 说明 |
|------|------|------|
| **时间** | `log.retention.hours=168` | 7天后删除 |
| **大小** | `log.retention.bytes` | 超过大小删除旧段 |
| **压缩** | `cleanup.policy=compact` | 保留每个 key 最新值 |

---

## 六、总结

```
LogSegment 三段式：
  .log + .index(稀疏) + .timeindex

查找 = 文件名定位 Segment 
     → 二分查 .index → 顺序扫描 .log
     
零拷贝 = sendfile → 数据从文件直接到Socket

清理 = 时间(7天) + 大小 + key压缩(compact)
```
