---
layout: post
title: "RocketMQ核心源码解读：CommitLog存储设计与消息流转全解析"
date: 2022-07-12
categories: [distributed]
tags: [RocketMQ, 源码分析, CommitLog, 存储设计, MappedFile, 零拷贝]
comments: true
---

## 一、RocketMQ 存储架构

### 为什么 RocketMQ 要用 CommitLog？

Kafka 缺点：Topic 过多 → Partition 文件多 → 文件索引耗时 → IO 性能下降

RocketMQ 的设计动机就是解决**多 Topic 场景下的 IO 压力问题**。

### CommitLog 存储模型

```
┌─────────────────────────────────────────────┐
│                  CommitLog                    │
│  (所有 Topic 的消息顺序写入同一个文件)          │
│                                               │
│  [TopicA Msg1][TopicB Msg1][TopicA Msg2]...  │
└─────────────────────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ConsumeQ │ │ConsumeQ │ │ConsumeQ │
    │ TopicA  │ │ TopicB  │ │ TopicC  │
    │ (索引)  │ │ (索引)  │ │ (索引)  │
    └─────────┘ └─────────┘ └─────────┘
```

**核心设计**：
- **CommitLog**：所有消息按顺序追加到一个日志文件（不管什么 Topic）
- **ConsumeQueue**：轻量级消费队列，只存 CommitLog 偏移量（20 字节/条）
- **IndexFile**：消息索引，用于根据 Key 查询

**优势**：
- 无论多少 Topic，IO 都是顺序写入 → **IO 性能不受 Topic 数量影响**
- 相比 Kafka（每个 Topic-Partition 独立文件），RocketMQ 更不会因为 Topic 多而降速

---

## 二、文件存储详细结构

```
$HOME/store/
  ├── commitlog/
  │   ├── 00000000000000000000
  │   └── 00000000001073741824   (每个文件1GB)
  ├── consumequeue/
  │   └── TopicA/0/
  │       ├── 00000000000000000000
  │       └── 00000000000006000000
  ├── index/
  │   └── 00000000000000000000
  ├── config/
  └── abort
```

### CommitLog 一条消息的结构

```
TotalSize | MagicCode | BodyCRC | QueueId | Flag | QueueOffset |
PhysicalOffset | SysFlag | BornTimestamp | BornHost | StoreTimestamp |
StoreHost | ReconsumeTimes | PreparedTransactionOffset | BodyLength | Body
```

---

## 三、MappedFile 与零拷贝

```java
// RocketMQ 的核心零拷贝实现
MappedFile mappedFile = new MappedFile(fileName, fileSize);
MappedByteBuffer byteBuffer = mappedFile.getMappedByteBuffer();

// 写入消息 → 直接写内存映射文件
byteBuffer.put(messageBytes);

// 读取消息 → 直接读内存映射文件
byteBuffer.position(pos);
byteBuffer.get(readBuffer, 0, size);
```

- **mmap**：文件映射到内存，减少内核→用户拷贝
- **sendfile**：投递消息时，数据从文件直接到网卡（零拷贝）
- **TransientStorePool**：堆外内存池预分配，加速写入

---

## 四、刷盘机制

```java
// 同步刷盘
GroupCommitService
  → 每条消息写入后调用 force()
  → 等 OS 返回刷盘成功才返回 → 安全但慢

// 异步刷盘  
FlushRealTimeService
  → 每隔固定时间（默认500ms）执行一次
  → 性能高，但可能丢最近500ms内的消息
```

---

## 五、消息复制（主从同步）

```java
// 同步复制 (SYNC_MASTER)
Master 等 Slave 确认后才返回成功 → 强一致

// 异步复制 (ASYNC_MASTER)
Master 不等 Slave → 高性能，可能丢失少量消息
```

---

## 六、总结

```
CommitLog 设计核心：
  所有 Topic → 同一个 CommitLog 顺序写入
  → IO 不受 Topic 数量影响

文件结构：
  CommitLog (全量) → ConsumeQueue (索引) → IndexFile (Key查询)

零拷贝：
  mmap(写入) + sendfile(投递) → 减少内核拷贝
```
