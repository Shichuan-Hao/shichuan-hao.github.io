---
title: "分布式技术栈全景速查手册"
date: 2022-06-26
categories: distributed
tags: [分布式, Redis, ES, ZK, MQ, Netty, 全景总结]
mermaid: true
---

> 分布式系列完整笔记的索引和速查手册。将 20 篇笔记的核心内容浓缩成对比表格，方便快速回顾和面试准备。

## 一、缓存技术栈

| 维度 | 要点 |
|------|------|
| **核心价值** | 高性能 KV 存储、内存数据库、缓存 |
| **线程模型** | 核心线程单线程 + IO 多线程（Redis 6+） + 异步删除/持久化子线程 |
| **数据持久化** | RDB（全量快照）+ AOF（操作日志）+ Redis 7 三文件结构 |
| **高可用演进** | 单机 → 主从复制 → Sentinel 哨兵 → Cluster 集群 |
| **底层结构** | SDS / ListPack / QuickList / SkipList / IntSet（ZipList → ListPack） |
| **缓存三问题** | 穿透（空值缓存+布隆）/ 击穿（随机过期）/ 雪崩（高可用+限流） |
| **性能调优** | BigKey 检测、连接池、慢查询、内存淘汰、内核参数 |

## 二、搜索引擎

| 维度 | 要点 |
|------|------|
| **核心原理** | 倒排索引（关键词 → 文档列表） |
| **核心概念** | Index(库) / Mapping(表结构) / Document(行) |
| **查询能力** | Query Context(打分) vs Filter Context(不分词不评分可缓存) |
| **全文检索** | match / match_phrase / multi_match |
| **精确查询** | term / terms / range（不分词） |
| **聚合分析** | Bucket(分桶) / Metric(统计) / Pipeline(二次聚合) |
| **深度分页** | from+size → search_after(推荐) → PIT → Scroll(全量导出) |
| **相关性打分** | BM25（TF 非线性饱和 + IDF + 字段长度归一化） |

## 三、消息队列

| 维度 | Kafka | RocketMQ | RabbitMQ |
|------|-------|----------|----------|
| **定位** | 海量日志采集 | 金融级全场景 | 企业级可靠消息 |
| **吞吐量** | 极高 | 高 | 中等 |
| **可靠性** | 中（允许少量丢失） | 高 | 高 |
| **高级功能** | 少 | 事务消息/延迟/死信 | 死信/延迟/优先级 |
| **存储设计** | Partition 分段日志 | CommitLog 顺序写 | 队列内存/磁盘 |
| **协议** | 自定义 TCP | 自定义 TCP | AMQP 0-9-1 |
| **语言** | Scala/Java | Java | Erlang |
| **MQ 三问** | 不丢→同步刷盘/确认 | 重复→幂等 | 有序→同Queue同线程 |

## 四、分布式协调（ZooKeeper）

| 维度 | 要点 |
|------|------|
| **核心公式** | ZK = 文件系统(DataTree) + 监听机制(Watcher) |
| **节点类型** | 持久/临时/持久顺序/临时顺序/容器/TTL |
| **选举算法** | 启动期选主(epoch>zxid>myid) + 运行期选主(FastLeaderElection) |
| **一致性** | ZAB 协议：选举→发现→同步→广播 |
| **半数原则** | 选举和提交都需超过半数节点确认 |
| **应用场景** | 分布式锁/配置中心/注册中心/Master-Worker/命名服务 |

## 五、网络通信

| 维度 | 要点 |
|------|------|
| **BIO** | 1连接1线程，阻塞io，accept + read 两步阻塞 |
| **NIO** | Selector 多路复用，Channel + Buffer，非阻塞 |
| **epoll** | 红黑树 + 就绪链表 + 事件回调，O(1) 获取就绪 fd |
| **零拷贝** | sendfile() 绕过用户态，DMA 直接磁盘→网卡 |
| **Netty** | EventLoop(N:1 Channel) + Pipeline(入站/出站双向链表) |
| **TCP 疑难** | 粘包拆包（定长/分隔符/长度域）+ 心跳检测 + 断线重连 |

## 六、分库分表

| 维度 | 要点 |
|------|------|
| **核心产品** | ShardingSphere-JDBC（推荐）/ ShardingSphere-Proxy |
| **分片类型** | 垂直分库/分表 + 水平分库/分表 |
| **分片策略** | Standard/Complex/Hint/Inline |
| **分布式ID** | CosID = 号段模式 + 雪花算法（解决时钟回拨） |

## 七、架构演进路径

```
单机应用
  → 读写分离（MySQL主从）
    → 引入缓存（Redis）
      → 数据分片（ShardingSphere + 分布式ID）
        → 异步解耦（MQ）
          → 全文检索（ES）
            → 分布式协调（ZK/Nacos）
              → 微服务体系
```

> 分布式技术栈的每一个组件都不是孤立存在的。Redis 的持久化依赖磁盘 IO（mmap），Netty 的高性能依赖 epoll 和零拷贝，RocketMQ 的 CommitLog 依赖顺序写盘——底层原理是相通的。

## 八、高频面试交叉问题

**1. Redis Cluster 和 ZK 的选举机制有何不同？**

| 维度 | Redis Cluster | ZooKeeper |
|------|--------------|-----------|
| 协议 | Gossip | ZAB |
| 投票者 | 只有 Master 节点 | 所有 Follower 节点 |
| 中心化 | 去中心化 | Leader-Follower |
| 一致性 | 最终一致 | 强一致 |

**2. RocketMQ commitlog 为什么这么设计？**

借鉴了 Kafka 的日志设计。所有 Topic 消息写入同一个 CommitLog，保证**顺序写盘**，避免多 Topic 时的随机 IO。通过 ConsumeQueue 索引实现高效消费。

**3. epoll 为什么比 select/poll 快？**

select/poll 每次调用需要把全部 fd 集合从用户态拷贝到内核态，且需要遍历所有 fd 找就绪的。epoll 通过**红黑树 + 就绪链表 + 事件回调**，epoll_wait 直接从就绪链表取出，O(1) 复杂度。

**4. Redis 为什么用 SkipList 而不用红黑树？**

SkipList 实现简单、范围查询天然高效（有序链表遍历）、并发友好（局部调整，不需要全局旋转平衡）。
