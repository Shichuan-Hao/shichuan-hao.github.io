---
layout: post
title: "ElasticSearch快速安装上手：Windows/Linux双平台部署"
date: 2022-06-15
categories: [distributed]
tags: [ElasticSearch, 安装部署, Windows, Linux, 配置详解]
comments: true
---

> 初学者建议直接安装 Windows 版本的 ElasticSearch。

---

## 一、Windows 安装 ES

### 1、下载并解压

下载地址：`https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.14.3-windows-x86_64.zip`

解压后 ES 目录结构：

| 目录 | 描述 |
|------|------|
| `bin` | 脚本文件（启动 elasticsearch、安装插件等） |
| `config` | 配置文件目录（elasticsearch.yml、jvm.options等） |
| `jdk` | 7.x 以后带有自带的 Java 环境 |
| `data` | 默认数据存放目录（生产需修改） |
| `lib` | ES 依赖的 Java 类库 |
| `logs` | 默认日志存储路径（生产需修改） |
| `modules` | ES 模块（Cluster、Discovery、Indices 等） |
| `plugins` | 已安装插件目录 |

### 2、配置 JDK 环境

ES 比较耗内存，建议 4G 以上内存。

JDK 环境变量优先级：
```
ES_JAVA_HOME > ES_HOME > 系统 JAVA_HOME
```

7.0 开始内置了 Java 环境。设置环境变量：
```
ES_JAVA_HOME → ES 使用的 Java 运行时路径
ES_HOME → ES 的安装路径
```

参照 `elasticsearch-env.bat` 了解环境变量配置。

### 3、配置 elasticsearch.yml

```yaml
# 关闭 security 安全认证（初学者建议关闭）
xpack.security.enabled: false
```

### 4、启动服务

1. 解决日志乱码：编辑 `config/jvm.options` 末尾添加：
   ```
   -Dfile.encoding=GBK
   ```

2. 进入 `bin` 目录，双击 `elasticsearch.bat` 启动

3. 浏览器访问：`http://localhost:9200`

**端口说明**：
- **9200**：浏览器访问的 HTTP RESTful 端口
- **9300**：集群间组件通信端口

---

## 二、Linux 安装 ES

### 1、环境准备

| 项目 | 配置 |
|------|------|
| Linux 系统 | CentOS 7 |
| IP | 192.168.65.47 |
| 操作用户 | fox |

> **关键**：ES 不允许使用 root 账号启动！

```bash
# 创建专有账户
adduser fox
passwd fox
```

### 2、下载解压

```bash
# 通过 fox 用户登录
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.14.3-linux-x86_64.tar.gz
tar -xzf elasticsearch-8.14.3-linux-x86_64.tar.gz
cd elasticsearch-8.14.3/

# 如果在 root 用户下解压，需要改所有权
chown -R fox:fox elasticsearch-8.14.3
```

### 3、JDK 环境配置（可选）

```bash
# 编辑用户级环境变量
vim .bash_profile

export ES_JAVA_HOME=/home/fox/elasticsearch-8.14.3/jdk/
export ES_HOME=/home/fox/elasticsearch-8.14.3

# 使配置生效
source .bash_profile
```

### 4、常用配置参数

```yaml
# elasticsearch.yml

# 集群名称（同集群必须一致）
cluster.name: my-application

# 节点名称（需唯一）
node.name: node-1

# 数据存储目录（生产环境强烈建议另设安全目录）
path.data: /data/es/data

# 日志存储目录
path.logs: /data/es/logs

# 内存锁定检查（生产建议 true，非生产可 false）
bootstrap.memory_lock: true

# 服务绑定地址（0.0.0.0 开启远程访问）
network.host: 0.0.0.0

# HTTP 端口
http.port: 9200

# 节点通信端口
transport.port: 9300

# 集群发现主机列表
discovery.seed_hosts: ["host1", "host2"]

# 初始 Master 选举节点（集群首次构建完成后应移除）
cluster.initial_master_nodes: ["node-1"]

# 单节点模式（绕过引导检查，初学者建议）
discovery.type: single-node

# 关闭安全认证（初学者建议）
xpack.security.enabled: false
```

### 5、开发模式 vs 生产模式

| | 开发模式 | 生产模式 |
|------|----------|----------|
| 触发条件 | 未配置集群发现设置 | 修改了集群相关配置 |
| 引导检查 | 不执行，仅警告 | **严格检查**，不合理配置拒绝启动 |
| JVM 检查 | 跳过 | 检查 JVM 大小、内存锁、虚拟内存等 |
| 建议 | 学习阶段 + `discovery.type=single-node` | 生产上线阶段 |

**生产模式检查项**：JVM 大小、内存锁、虚拟内存、最大线程数、集群发现配置等。

> ES 宁可拒绝服务也要阻止不合理的配置启动，防止后期出现难以解决的性能问题。

### 6、配置 JVM 参数

修改 `config/jvm.options`：

```
# 调整堆内存大小
-Xms1g
-Xmx1g

# 内存使用建议：
#   Xms 和 Xmx 值设置为一样大
#   Xmx 不超过物理内存的 50%，最大不超过 32GB
#   预留一半内存给 Lucene（利用系统文件缓存）
```

---

## 三、安装 IK 分词器

### 为什么需要 IK 分词器？

ES 自带的分词器对中文支持很差：

```
# 标准分词器
GET _analyze
{
  "text": "我爱北京天安门",
  "analyzer": "standard"
}
# → ["我","爱","北","京","天","安","门"]   # 单字拆分，无意义！
```

### 安装步骤

```bash
# 进入 ES 目录
cd elasticsearch-8.14.3

# Windows
bin\elasticsearch-plugin.bat install https://get.infini.cloud/elasticsearch/analysis-ik/8.14.3

# Linux
bin/elasticsearch-plugin install https://get.infini.cloud/elasticsearch/analysis-ik/8.14.3

# 重启 ES
```

### 验证分词效果

```bash
# ik_max_word（最细粒度）
GET _analyze
{
  "text": "我爱北京天安门",
  "analyzer": "ik_max_word"
}
# → ["我","爱","北京","天安门","京天","安门"]

# ik_smart（智能模式）
GET _analyze
{
  "text": "我爱北京天安门",
  "analyzer": "ik_smart"
}
# → ["我","爱","北京","天安门"]
```

**两种模式对比**：

| 模式 | 策略 | 索引推荐 | 搜索推荐 |
|------|------|----------|----------|
| `ik_max_word` | 最细粒度拆分 | ✅（覆盖更多词） | |
| `ik_smart` | 智能最简拆分 | | ✅（避免误召回） |

---

## 四、常用运维指令

```bash
# 查看集群健康
GET _cat/health?v

# 查看节点
GET _cat/nodes?v

# 查看所有索引
GET _cat/indices?v

# 查看分片
GET _cat/shards?v

# 查看插件列表
GET _cat/plugins?v
```

---

## 五、常见问题

### 1. 虚拟内存不足
```
max virtual memory areas vm.max_map_count [65530] is too low
```

解决：
```bash
# 临时修改
sysctl -w vm.max_map_count=262144
# 永久修改
echo "vm.max_map_count=262144" >> /etc/sysctl.conf
```

### 2. 文件描述符不足
```bash
# 修改 /etc/security/limits.conf
fox soft nofile 65536
fox hard nofile 65536
```

### 3. 内存锁定失败
```yaml
# 开发环境中关闭内存锁定
bootstrap.memory_lock: false
```

> 有道云笔记：[ES快速安装上手](https://note.youdao.com/s/17k3uiZJ)
