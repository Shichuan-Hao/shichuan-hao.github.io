---
layout: post
title: "ES集群架构生产最佳实践：节点角色分离与Hot-Warm冷热架构"
date: 2022-06-25
categories: [distributed]
tags: [ElasticSearch, 生产实践, 节点角色, Hot-Warm, 冷热分离, 读写分离]
comments: true
---

> ES 7.9 引入节点角色概念，让不同角色的节点各司其职。Hot-Warm 冷热数据分离架构则在成本有限的前提下最大化性能。

---

## 一、ES 节点角色详解

### 从旧配置到节点角色

**ES 7.1 旧配置方式**：
```yaml
# "我要说明我是主节点" → "我要说明我不是数据节点、不是ingest节点......"
node.master: true
node.data: false
node.ingest: false
```

**ES 8.x 节点角色**（直接说明"我是XXX"）：
```yaml
node.roles: [data, master]
```

### 默认节点角色

不手动设置时，ES 8.x 默认角色为 `cdfhilmrstw`：

| 角色字母 | 角色名称 | 职责 |
|----------|----------|------|
| `m` | Master | 集群管理和元数据维护 |
| `d` | Data | 存储、检索和处理数据 |
| `i` | Ingest | 数据预处理（过滤、转换） |
| `h` | Hot | 热数据节点 |
| `w` | Warm | 暖数据节点 |
| `c` | Cold | 冷数据节点 |
| `f` | Frozen | 冻结数据节点 |
| `l` | ML | 机器学习 |
| `r` | Remote Cluster Client | 跨集群搜索 |
| `s` | Content | 通用内容节点 |
| `t` | Transform | 数据转换 |

### 单一角色职责分离

| 节点类型 | 配置 | 硬件建议 |
|----------|------|----------|
| **Master Only** | `node.roles: [master]` | 低配置 CPU/RAM/磁盘 |
| **Data Only** | `node.roles: [data]` | 高配置 CPU/RAM/磁盘 |
| **Ingest Only** | `node.roles: [ingest]` | 高配置 CPU / 中RAM / 低磁盘 |
| **Coordinating Only** | `node.roles: []` | 高配置 CPU/RAM / 低磁盘 |

**生产环境建议**：集群规模 > 6 个节点时，手动设定单一角色。

**什么时候加节点**：
- 磁盘容量不足 → 增加数据节点
- 磁盘读写压力大 → 增加数据节点
- 大量复杂查询/聚合 → 增加 Coordinating 节点

---

## 二、Coordinating Only Nodes（协调节点）

### 职责

- 扮演 **Load Balancer**，降低 Master 和 Data 节点负载
- 负责搜索结果的 **Gather / Reduce**
- 防止深度聚合等操作引发 OOM

### 配置

```yaml
# 不分配任何数据相关角色
node.roles: []
```

---

## 三、Hot & Warm 冷热架构

### 为什么需要 Hot & Warm？

| 问题 | 说明 |
|------|------|
| ES 数据特点 | 通常无 Update 操作 |
| 适用场景 | 基于时间的索引数据，数据量大 |
| 成本平衡 | Hot 用 SSD、Warm 用大容量 HDD |
| 性能目标 | 热点数据高性能，历史数据成本低 |

### 典型场景

> 每日增量 6TB 日志数据，高峰时段查询频繁，集群压力大。

**两种节点的不同硬件配置**：

| 节点 | 存储 | 用途 |
|------|------|------|
| **Hot Nodes** | SSD | 数据写入（新索引），高 IO 性能 |
| **Warm Nodes** | HDD（大容量） | 只读的旧数据，低频率查询 |

### 配置步骤

**Step 1**：标记节点
```yaml
# hot node (elasticsearch.yml)
node.attr.my_node_type: hot

# warm node (elasticsearch.yml)
node.attr.my_node_type: warm
```

**Step 2**：查看节点标记
```bash
GET /_cat/nodeattrs?v
```

**Step 3**：新建索引到 Hot 节点
```json
PUT /index-2022-05
{
  "settings": {
    "number_of_shards": 2,
    "number_of_replicas": 0,
    "index.routing.allocation.require.my_node_type": "hot"
  }
}
```

**Step 4**：迁移老数据到 Warm 节点
```json
PUT /index-2022-04/_settings
{
  "index.routing.allocation.require.my_node_type": "warm"
}
```

### Shard Filtering 规则

```yaml
# 分配规则（索引级 dynamic setting）
index.routing.allocation.include.{attr}     # 至少包含一个值
index.routing.allocation.exclude.{attr}     # 不能包含任何一个值
index.routing.allocation.require.{attr}     # 所有值都需要包含
```

---

## 四、读写分离架构

```
        Client
          │
          ▼
   [Coordinating Nodes]
     /          \
    ▼            ▼
[Master Nodes] [Data Nodes]
  (管理)      (搜索/聚合)
     \           /
      ▼         ▼
[Replica Nodes] (数据副本)

写入: Client → Coordinating → Master → Data Node
读取: Client → Coordinating → Data Node (可读副本)
```

**读写分离价值**：
- 写请求走 Master 管理的主分片
- 读请求可走任意副本分片
- 提升读取吞吐量

---

## 五、ILM（索引生命周期管理）+ Hot-Warm

```json
PUT _ilm/policy/hot_warm_policy
{
  "phases": {
    "hot": {
      "min_age": "0ms",
      "actions": {
        "rollover": { "max_size": "50gb", "max_age": "1d" },
        "set_priority": { "priority": 100 }
      }
    },
    "warm": {
      "min_age": "7d",
      "actions": {
        "allocate": {
          "require": { "my_node_type": "warm" }
        },
        "shrink": { "number_of_shards": 1 },
        "forcemerge": { "max_num_segments": 1 },
        "set_priority": { "priority": 50 }
      }
    },
    "cold": {
      "min_age": "30d",
      "actions": {
        "allocate": { "require": { "my_node_type": "cold" } }
      }
    },
    "delete": {
      "min_age": "90d",
      "actions": { "delete": {} }
    }
  }
}
```

---

## 六、总结

```
生产级 ES 部署建议：

  节点角色:
    集群 < 6节点       → 混合角色
    集群 ≥ 6节点       → 单一角色分离

  冷热分离:
    数据量大 + 时序数据 → Hot(Warm) 架构
    Hot: SSD 高配置
    Warm: HDD 大容量低配置

  扩展策略:
    存储不足 → 加 Data 节点
    查询慢  → 加 Data 节点或 Coordinating 节点
    写入慢  → 加 Data 节点（SSD）
```

> 有道云笔记：[ES集群生产最佳实践](https://note.youdao.com/s/UostSRP4)
