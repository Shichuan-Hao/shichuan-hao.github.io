---
title: "ElasticSearch 8 核心概念、安装部署与分词实战"
date: 2022-06-12
categories: distributed
tags: [ElasticSearch, 倒排索引, IK分词器, 全文检索, Kibana, 安装部署]
mermaid: true
---

> ES 不是又一个 MySQL。它是分布式搜索引擎，核心是倒排索引和相关性排序。本文从搜索引擎基础知识讲起，覆盖 ES 8 安装、核心概念（索引/映射/文档）、IK 分词、Kibana 可视化和索引别名实战。

## 一、搜索引擎基础

### 1.1 全文检索 vs 数据库查询

**查询（Query）**：有明确的搜索条件边界。年龄 15~25 岁，颜色=红色，价格<3000——这里有明确的范围界定。

**检索（Search / Full-Text Search）**：无搜索条件边界，召回结果取决于相关性。同义词、谐音、别名、错别字、网络热梗均可成为相关性判断依据。

举个例子：在电商平台搜索"Java设计模式"：

用 MySQL 的做法：
```sql
SELECT * FROM t_blog WHERE content LIKE "%Java设计模式%";
```

这种遍历所有记录进行匹配的方式，不但**效率低**（全表扫描），且搜索结果**不符合搜索期望**（无法按相关性排序）。

### 1.2 倒排索引的原理

全文检索的核心是**倒排索引**（Inverted Index）。

**正排索引**（MySQL 的索引方式）：根据文档 ID 查找内容。
```
文档1 → "Java中的23种设计模式..."
文档2 → "Java多线程设计模式..."
文档3 → "设计模式之美..."
```

**倒排索引**：根据关键词查找文档。
```
关键词       →  文档ID列表
Java         →  doc1, doc2
设计模式      →  doc1, doc2, doc3, doc4
多线程       →  doc2
JavaScript   →  doc4
```

倒排索引的构建过程：

1. **文档预处理**：分词处理，移除停用词，词干提取
2. **构建词典**：将处理后的词汇添加到词典，分配唯一 ID
3. **创建倒排列表**：记录每个词汇出现在哪些文档、哪个位置
4. **存储索引文件**：词典 + 倒排列表压缩后存盘
5. **查询处理**：从词典查找关键词的倒排列表，快速定位文档

> 倒排索引将"单词→文档"的映射提前算好存起来，查询时直接 O(1) 定位，再也不用遍历所有文档。

---

## 二、Elastic Stack 生态

Elastic Stack 由四大核心产品组成：

```
┌──────────────────────────────────────────────────────┐
│                    Elastic Stack                      │
├──────────┬──────────┬───────────────┬────────────────┤
│  Beats   │ Logstash │ Elasticsearch │    Kibana      │
│ (采集)    │ (处理)    │  (存储+搜索)   │  (可视化)       │
└──────────┴──────────┴───────────────┴────────────────┘
```

| 组件 | 职责 |
|------|------|
| **Beats** | 轻量级数据采集器（Filebeat 日志/Metricbeat 指标/Heartbeat 服务可用性） |
| **Logstash** | 服务端数据处理管道，采集+转换+发送 |
| **Elasticsearch** | 分布式全文搜索与分析引擎，PB 级数据量 |
| **Kibana** | 可视化和管理界面，仪表板、图表、地图 |

三大应用场景：
- **全文检索**：电商搜索、应用市场搜索、文档搜索（淘宝、360 手机助手、腾讯文档）
- **日志分析**：业务日志、慢查询、异常探测、系统日志（58 集团、唯品会）
- **商业智能（BI）**：数据可视化、趋势分析（永洪 BI、Sugar BI）

---

## 三、ES 核心概念（对比 MySQL 理解）

| MySQL | Elasticsearch | 说明 |
|-------|--------------|------|
| 数据库 | 索引（Index） | 逻辑容器，存储相关数据 |
| 表 | Type（7.x 已废弃） | 从 ES 7 开始 **一个索引只能包含一个文档类型** |
| 行 | 文档（Document） | JSON 对象，基本存储单元 |
| 列 | 字段（Field） | JSON 键值对 |
| Schema | 映射（Mapping） | 字段名、字段类型、分词语义、是否索引 |
| SQL | DSL | 基于 JSON 的领域特定查询语言 |

### 3.1 索引（Index）

索引是存储和管理相关数据的逻辑容器。**索引名称必须全部小写**，不可重复。

常见索引实践：
- `weibo_index` — 微博业务
- `news_index` — 新闻业务
- `logs_202407` — 2024 年 7 月日志（按时间切分）

### 3.2 映射（Mapping）

类似于数据库的"表结构"。定义了字段名称、字段类型、是否需要分词、是否需要索引等。

```json
PUT /employee
{
  "mappings": {
    "properties": {
      "name":       { "type": "keyword" },
      "sex":        { "type": "integer" },
      "age":        { "type": "integer" },
      "address":    { "type": "text", "analyzer": "ik_max_word" },
      "remark":     { "type": "text", "analyzer": "ik_smart" }
    }
  }
}
```

### 3.3 文档元数据

```json
{
  "_index": "employee",
  "_id": "2",
  "_version": 1,
  "_seq_no": 1,
  "_primary_term": 1,
  "found": true,
  "_source": {
    "name": "李四",
    "sex": 1,
    "age": 28,
    "address": "广州荔湾大厦"
  }
}
```

| 元数据 | 说明 |
|--------|------|
| `_index` | 所属索引名 |
| `_id` | 文档唯一 ID |
| `_version` | 版本号，修改/删除时自增 |
| `_seq_no` | Shard 级别严格递增，后写入的更大 |
| `_primary_term` | Primary Shard 重分配时递增 |

**`_seq_no` 和 `_primary_term` 的重要性**：ES 7+ 用这两个字段替代了旧版的 `_version`。用于**乐观锁并发控制**：

```json
POST /employee/_doc/1?if_seq_no=13&if_primary_term=1
{
  "name": "张三xxxx",
  "sex": 1,
  "age": 25
}
```

如果 seq_no 不匹配，抛出 `version_conflict_engine_exception`（HTTP 409）。

---

## 四、ES 8 安装部署

### 4.1 Windows 安装

```bash
# 下载
# https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.14.3-windows-x86_64.zip

# 解压后目录结构
bin/       # 脚本：elasticsearch.bat, elasticsearch-plugin.bat
config/    # elasticsearch.yml, jvm.options, role_mapping.yml
jdk/       # 7.x 后内置 Java 环境
data/      # 数据目录（生产环境需修改）
logs/      # 日志目录（生产环境需修改）
modules/   # 各功能模块
plugins/   # 插件目录
```

**修改配置 `config/elasticsearch.yml`**：

```yaml
# 关闭安全认证（学习环境）
xpack.security.enabled: false

# 开发模式（单节点，绕过引导检查）
discovery.type: single-node

# 解决日志乱码
# config/jvm.options 末尾添加
-Dfile.encoding=GBK
```

### 4.2 Linux 安装

```bash
# 1. 创建非 root 账户（ES 不允许 root 启动）
adduser fox && passwd fox

# 2. 下载解压
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.14.3-linux-x86_64.tar.gz
tar -xzf elasticsearch-8.14.3-linux-x86_64.tar.gz
chown -R fox:fox elasticsearch-8.14.3  # 改所有权

# 3. 配置 JDK 环境
vim .bash_profile
export ES_JAVA_HOME=/home/fox/elasticsearch-8.14.3/jdk/
export ES_HOME=/home/fox/elasticsearch-8.14.3
source .bash_profile
```

**核心配置参数**：

| 参数 | 说明 | 建议 |
|------|------|------|
| `cluster.name` | 集群名称 | 不同集群须不同 |
| `node.name` | 节点名称 | 一台机器多节点须区分 |
| `network.host` | 绑定地址 | `0.0.0.0` 开启远程访问 |
| `http.port` | HTTP 端口 | 默认 9200 |
| `transport.port` | 集群通信端口 | 默认 9300 |
| `path.data` | 数据目录 | 生产环境脱离 ES 目录 |
| `path.logs` | 日志目录 | 生产环境脱离 ES 目录 |
| `bootstrap.memory_lock` | 内存锁定 | 生产环境建议 true |
| `discovery.seed_hosts` | 集群节点列表 | 集群模式必配 |
| `cluster.initial_master_nodes` | 初始 Master 候选 | 首次构建后移除 |

### 4.3 生产模式启动错误解决

不配置 `discovery.type: single-node` 时会触发引导检查，常见错误：

```bash
# 错误1：文件句柄数不足
max file descriptors [4096] is too low, increase to at least [65536]

# 解决：/etc/security/limits.conf 添加
*  soft  nofile  65536
*  hard  nofile  65536
*  soft  nproc   4096
*  hard  nproc   4096

# 错误2：最大虚拟内存太小
max virtual memory areas vm.max_map_count [65530] is too low

# 解决：/etc/sysctl.conf 添加
vm.max_map_count=262144
sysctl -p

# 错误3：缺少集群发现配置
the default discovery settings are unsuitable for production use

# 解决：
discovery.seed_hosts: ["192.168.65.47"]
cluster.initial_master_nodes: ["node-1"]
```

### 4.4 开发模式 vs 生产模式

| 模式 | 触发条件 | 特点 |
|------|---------|------|
| **开发模式** | `discovery.type: single-node`，未配置集群发现 | 绕过引导检查，日志为 WARNING |
| **生产模式** | 配置了集群相关设置 | 严格引导检查，不满足则**拒绝启动** |

> ES 这种 "宁可拒绝启动也不让你在不合理配置下运行" 的设计哲学，是为了防止日后出现难以修复的性能问题。

### 4.5 JVM 配置

```bash
# config/jvm.options
-Xms4g
-Xmx4g
```

要点：
- **Xms 和 Xmx 设成一样**（避免运行时动态调整）
- **Xmx 不要超过机器内存的 50%**
- **不要超过 30GB**（超过后指针压缩失效，浪费内存）

---

## 五、Kibana 安装

```bash
# 下载
wget https://artifacts.elastic.co/downloads/kibana/kibana-8.14.3-linux-x86_64.tar.gz
tar -zxvf kibana-8.14.3-linux-x86_64.tar.gz
cd kibana-8.14.3

# config/kibana.yml
server.port: 5601
server.host: "0.0.0.0"
elasticsearch.hosts: ["http://localhost:9200"]
i18n.locale: "zh-CN"

# 启动
nohup bin/kibana > logs/kibana.log 2>&1 &
```

---

## 六、ES 插件与 IK 分词器

### 6.1 插件安装

```bash
# 查看已安装插件
bin/elasticsearch-plugin list

# 安装 ICU 分词插件
bin/elasticsearch-plugin install analysis-icu

# 删除插件
bin/elasticsearch-plugin remove analysis-icu

# 重启生效
```

### 6.2 IK 中文分词器

ES 默认 `standard` 分词器按**单字拆分**中文：

```json
POST _analyze
{
  "analyzer": "standard",
  "text": "中华人民共和国"
}
// 输出：["中","华","人","民","共","和","国"]  ← 没意义
```

**IK 分词器提供两种模式**：

```json
// ik_smart：最粗粒度拆分
POST _analyze
{ "analyzer": "ik_smart", "text": "中华人民共和国" }
// 输出：["中华人民共和国"]

// ik_max_word：最细粒度拆分
POST _analyze
{ "analyzer": "ik_max_word", "text": "中华人民共和国" }
// 输出：["中华人民共和国","中华人民","中华","华人","人民","共和","共和国","国"]
//       尽可能多地切出关键词，提高搜索召回率
```

**安装 IK 分词器**：

```bash
# 离线安装（推荐，版本必须严格对应）
# https://release.infinilabs.com/analysis-ik/stable/
# 下载对应 ES 版本的 zip，解压到 plugins/ik 目录

# 验证
POST _analyze
{ "analyzer": "ik_max_word", "text": "我是中国人" }
```

### 6.3 索引级别配置分词器

```json
# 创建索引时指定默认分词器
PUT /employee
{
  "settings": {
    "index": {
      "analysis.analyzer.default.type": "ik_max_word"
    }
  }
}

# 字段级别：写入用 ik_max_word（最细粒度），搜索用 ik_smart（更精准）
POST /index/_mapping
{
  "properties": {
    "content": {
      "type": "text",
      "analyzer": "ik_max_word",
      "search_analyzer": "ik_smart"
    }
  }
}
```

> **设计思想**：写入时用最细粒度分词（`ik_max_word`）最大化召回，搜索时用智能分词（`ik_smart`）提高精度。

---

## 七、CAT API 快速运维

```bash
GET /_cat/allocation         # 各节点 shard 分配情况
GET /_cat/shards             # 所有 shard 详情
GET /_cat/shards/{index}     # 指定 index shard
GET /_cat/master             # master 节点信息
GET /_cat/nodes              # 所有节点信息
GET /_cat/indices            # 所有索引详情
GET /_cat/indices/{index}    # 指定索引
GET /_cat/segments           # 所有 segment 详情
GET /_cat/count              # 当前集群 doc 数量
GET /_cat/health             # 集群健康状态（红/黄/绿）
GET /_cat/pending_tasks      # 当前 pending task
GET /_cat/aliases            # 所有别名信息
GET /_cat/thread_pool        # 线程池统计
GET /_cat/plugins            # 各节点插件信息
GET /_cat/fielddata          # fielddata 内存使用
GET /_cat/repositories       # 快照存储库
GET /_cat/templates          # 模板信息
```

---

## 八、总结

| 要点 | 说明 |
|------|------|
| ES 核心 | 基于倒排索引的分布式搜索引擎，非关系型数据库 |
| 核心概念 | Index→Database, Mapping→Schema, Document→Row |
| ES 8 安装 | 内置 JDK，禁止 root 启动，开发模式绕过引导检查 |
| 生产环境 | 文件句柄 65536+，vm.max_map_count 262144，JVM 不超 50% 内存 |
| IK 分词 | ik_smart(智能精度) + ik_max_word(最大化召回) |
| 分词策略 | 写入用 ik_max_word，搜索用 ik_smart |
| Kibana | 可视化界面，支持中文，端口 5601 |
