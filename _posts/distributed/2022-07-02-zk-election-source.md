---
layout: post
title: "Zookeeper选举Leader源码剖析：从QuorumPeerMain到双层选举队列"
date: 2022-07-02
categories: [distributed]
tags: [Zookeeper, 源码分析, Leader选举, QuorumPeer, 选举算法, 分布式一致性]
comments: true
---

> 看源码的价值：提升技术功底、深度掌握框架、快速定位线上问题、面试加分、知其然知其所以然。

---

## 一、源码阅读方法论

1. **先使用**：快速掌握框架基本使用
2. **抓主线**：找 demo 入手，画主流程图，切勿陷入细枝末节
3. **画图做笔记**：核心功能点深入源码，画走向图，记录闪光点
4. **整合总结**：回到主流程图梳理一遍

---

## 二、从源码启动 Zookeeper

### 下载与编译

```bash
# 下载源码（分支 3.5.8）
git clone https://github.com/apache/zookeeper.git
cd zookeeper

# 创建 Version 辅助类（解决编译报错）
# 路径: org.apache.zookeeper.version.Info

# 编译
mvn clean install -DskipTests
```

### 找到入口类

从 `bin/zkServer.sh` 找到启动主类：
```
org.apache.zookeeper.server.quorum.QuorumPeerMain
```

### 启动配置

```
1. 将 conf/zoo_sample.cfg 复制为 zoo.cfg，配置启动参数
2. 注释掉 pom.xml 中 jline 以外的 provided scope 依赖
3. 复制 log4j.properties 到 target/classes 目录
```

### 集群启动

复制 3 个 zoo.cfg，修改端口和集群配置，data 目录分别建 myid 文件：
```
server.1=192.168.50.190:2888:3888
server.2=192.168.50.190:2889:3889
server.3=192.168.50.190:2890:3890
```

---

## 三、Leader 选举多层队列架构

整个选举底层分为两层：

```
┌─────────────────────────────────────────┐
│         选举应用层 (FastLeaderElection)   │
│  · 统一队列接收和发送选票                  │
│  · 选举逻辑判断                          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│         消息传输层 (QuorumCnxManager)      │
│  · 按机器分队列（避免互相影响）             │
│  · 独立线程发送                           │
│  · 某台机器失败不影响对其他机器的消息发送     │
└─────────────────────────────────────────┘
```

**为什么分两层队列**：按发送的机器分队列，避免某台机器出问题时影响对正常机器的消息发送。

---

## 四、选举流程详解

### 启动时选举

```
1. 每个节点启动 → QuorumPeer.start()
2. 进入 LOOKING 状态 → 开始 Leader 选举
3. 发起投票（投自己）
4. 接收其他节点的投票
5. 比较投票：
   - 先比较 epoch（选举的任期）
   - 再比较 zxid（事务ID，越大数据越新）
   - 最后比较 myid（机器ID，越大越优先）
6. 根据过半原则确定 Leader
7. 选举结束 → 进入 LEADING 或 FOLLOWING 状态
```

### 选举判断规则

```
选票比较优先级：
  epoch 大的 > epoch 小的
  zxid 大的 > zxid 小的
  myid 大的 > myid 小的
```

### Leader 宕机后重新选举

```
1. Follower 心跳超时 → 发现 Leader 丢失
2. 进入 LOOKING 状态
3. 增加 epoch 值（新一轮选举）
4. 重复选举流程 → 选出新 Leader
5. 新 Leader 数据同步 → 恢复服务
```

---

## 五、关键源码类

| 类 | 职责 |
|------|------|
| `QuorumPeerMain` | 启动入口，加载配置 |
| `QuorumPeer` | 每个 ZK 节点实例，状态机核心 |
| `FastLeaderElection` | 快速 Leader 选举算法实现 |
| `QuorumCnxManager` | 选举消息传输管理 |
| `WorkerSender / WorkerReceiver` | 消息发送/接收 Worker |

---

## 六、总结

```
Leader 选举核心流程：

  start() → LOOKING → 投自己 → 接收投票 → 比较选票
                                              │
                        epoch > zxid > myid   │
                                              ▼
                              过半同意 → LEADING / FOLLOWING

  选举双层架构：
    应用层(FastLeaderElection) → 统一队列
    传输层(QuorumCnxManager)  → 按机器分队列
```

> 有道云笔记：[Zookeeper选举Leader源码剖析](https://note.youdao.com/noteshare?id=dfa894cfaf0fde76405dd205dc1d1b47)
