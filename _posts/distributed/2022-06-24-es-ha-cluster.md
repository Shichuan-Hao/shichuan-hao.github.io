---
layout: post
title: "ElasticSearch高可用集群架构实战：三节点部署与监控运维"
date: 2022-06-24
categories: [distributed]
tags: [ElasticSearch, 集群, 高可用, 分片, 副本, 故障转移]
comments: true
---

> ES 集群架构的价值：高可用（节点停止服务不影响整体） + 可扩展（水平扩容存储和请求处理能力）。

---

## 一、核心概念

### 1、集群（Cluster）

- 一个集群可有一个或多个节点
- 不同集群通过不同名字区分，默认 `"elasticsearch"`
- 配置方式：`cluster.name: my-cluster` 或 `-E cluster.name=es-cluster`

### 2、节点（Node）

- 每个节点是一个 ES 实例（本质是一个 Java 进程）
- 生产环境建议一台机器只运行一个 ES 实例
- 节点名通过配置或启动参数指定：`node.name: node1`
- 启动后分配 UID，保存在 data 目录下

### 3、分片（Shard）

**主分片（Primary Shard）**：
- 解决数据水平扩展问题
- 分片是运行的 Lucene 实例
- **索引创建后不可修改**（除非 Reindex）

**副本分片（Replica Shard）**：
- 主分片的拷贝，解决数据高可用
- **副本数可动态调整**
- 增加副本提高服务可用性和读取吞吐

```json
PUT /blogs
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1
  }
}
```

**分片架构示意**：
```
  Cluster
  ├── Node 1: P0, P1, R2
  ├── Node 2: P2, R0, R1
  └── Node 3: (备份)
```

### 4、集群状态

| 状态 | 含义 | 触发场景 |
|------|------|----------|
| **Green** | 主分片与副本都正常分配 | 一切正常 |
| **Yellow** | 主分片全部正常，有副本未分配 | 单节点集群 / 副本分配不出 |
| **Red** | 有主分片未能分配 | 磁盘满 / 节点宕机 |

---

## 二、搭建三节点集群

### 1、环境准备

| IP | 节点名 |
|------|--------|
| 192.168.65.213 | node-1 |
| 192.168.65.207 | node-2 |
| 192.168.65.208 | node-3 |

**创建用户**：
```bash
# root 用户
adduser es
passwd es
```

**配置 hosts**：
```bash
vim /etc/hosts
192.168.65.213 es-node1
192.168.65.207 es-node2
192.168.65.208 es-node3
```

**关闭防火墙**：
```bash
systemctl stop firewalld
systemctl disable firewalld
```

### 2、系统级配置（生产模式引导检查）

```bash
# 1. 文件描述符
echo "es soft nofile 65536" >> /etc/security/limits.conf
echo "es hard nofile 65536" >> /etc/security/limits.conf

# 2. 最大线程数
echo "es soft nproc 4096" >> /etc/security/limits.conf
echo "es hard nproc 4096" >> /etc/security/limits.conf

# 3. 虚拟内存
echo "vm.max_map_count=262144" >> /etc/sysctl.conf
sysctl -p
```

### 3、集群配置（elasticsearch.yml）

**node-1**：
```yaml
cluster.name: es-cluster
node.name: node-1
path.data: /data/es/data
path.logs: /data/es/logs
network.host: 0.0.0.0
http.port: 9200
transport.port: 9300
discovery.seed_hosts: ["192.168.65.213", "192.168.65.207", "192.168.65.208"]
cluster.initial_master_nodes: ["node-1", "node-2", "node-3"]
```

**node-2 / node-3** 仅修改 `node.name`，其余相同。

### 4、CAT API 运维

```bash
GET _cluster/health           # 集群健康状况
GET /_cat/nodes?v             # 查看节点信息
GET /_cat/health?v            # 集群状态（红黄绿）
GET /_cat/shards?v            # 各 shard 详细情况
GET /_cat/shards/{index}?v    # 指定索引的分片情况
GET /_cat/master?v            # master 节点信息
GET /_cat/indices?v           # 所有索引详细信息
```

---

## 三、故障转移演示

```bash
# 查看当前 master 和分片分布
GET /_cat/nodes?v
GET /_cat/shards/blogs?v

# 停止某个节点
kill -9 {node_pid}

# 观察集群变化
GET /_cluster/health
# Yellow → Green（副本提升为主分片）
```

**故障转移流程**：
```
1. node-1 (master) 宕机
2. 集群检测到 master 丢失（3秒 ping timeout）
3. node-2 和 node-3 发起 master 选举
4. 新 master 将宕机节点的副本提升为主分片
5. 集群恢复 Green
```

---

## 四、水平扩容

```bash
# 动态调整副本数
PUT /blogs/_settings
{
  "number_of_replicas": 2
}

# 添加新节点自动分布分片
# 新节点加入 → 集群自动 Rebalance
```

**扩容效果**：
```
3节点 1副本 → 6节点 2副本:
  - 存储容量翻倍
  - 读取吞吐量翻倍
  - 集群容错能力提升
```

---

## 五、集群运维要点

### 健康检查脚本

```bash
# 定时检查
while true; do
  curl -s "localhost:9200/_cluster/health?pretty" | grep status
  sleep 30
done
```

### 常见问题

| 问题 | 检查 | 解决 |
|------|------|------|
| 集群状态 Red | 磁盘空间 / 节点存活 | 扩容磁盘 / 重启节点 |
| 集群状态 Yellow | 副本数 > 节点数-1 | 减少副本数或增加节点 |
| 脑裂 | 网络分区 | 配置 `discovery.seed_hosts` |

### 备份与恢复

```bash
# 快照仓库注册
PUT _snapshot/my_backup
{
  "type": "fs",
  "settings": { "location": "/mount/backups" }
}

# 创建快照
PUT _snapshot/my_backup/snapshot_1?wait_for_completion=true

# 恢复快照
POST _snapshot/my_backup/snapshot_1/_restore
```

---

## 六、总结

```
ES 集群核心价值：
  ✓ 高可用 → 节点宕机不影响服务
  ✓ 可扩展 → 水平扩容存储和查询能力
  ✓ 数据安全 → 副本保证数据不丢失

关键配置：
  discovery.seed_hosts → 集群发现
  cluster.initial_master_nodes → 初始 Master
  number_of_shards → 主分片数（创建后不可改）
  number_of_replicas → 副本数（可动态调整）

日常运维：
  _cat API → 健康监控
  _cluster/health → 状态检查
  快照仓库 → 灾难恢复
```

> 有道云笔记：[ES高可用集群架构实战](https://note.youdao.com/s/QjNg4jNb)
