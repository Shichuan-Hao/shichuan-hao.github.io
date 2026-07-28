---
layout: post
title: "微服务日志采集与分析系统实战：ELK+消息队列+Filebeat+Nginx全景"
date: 2022-06-27
categories: [distributed]
tags: [ELK, ElasticSearch, Logstash, Kibana, Filebeat, Nginx, 日志采集]
comments: true
---

> 随着企业信息化进程加速，日志数据量急剧增加且来源多样、格式复杂，传统日志管理已难以满足需求。ELK 提供了高效、实时、可扩展的日志管理解决方案。

---

## 一、为什么要使用 ELK

| 目标 | ELK 提供的价值 |
|------|---------------|
| **集中化管理** | 统一收集、管理所有节点日志，提高问题定位效率 |
| **高效检索** | ElasticSearch 的倒排索引实现快速查询 |
| **日志分析与监控** | 系统日志、应用日志、安全日志多维度分析 |
| **数据可视化** | Kibana 生成维度表格和图形，使数据直观可控 |
| **安全性与负载监控** | 实时了解服务器负荷、性能和安全性 |

---

## 二、ELK 整体架构

### 经典 ELK 架构

```
┌──────────┐    ┌──────────┐    ┌────────────────┐    ┌─────────┐
│ Filebeat │───▶│ Logstash │───▶│ Elasticsearch  │───▶│ Kibana  │
│(日志收集) │    │(数据处理) │    │  (存储与搜索)    │    │(可视化) │
└──────────┘    └──────────┘    └────────────────┘    └─────────┘
```

**适用场景**：数据量较小的开发环境。

### 整合消息队列 + Nginx 的生产架构

```
┌──────────┐    ┌────────┐    ┌──────────┐    ┌────────────────┐    ┌──────────┐    ┌─────────┐
│ Filebeat │───▶│  Kafka │───▶│ Logstash │───▶│ Elasticsearch  │───▶│  Nginx   │───▶│ Kibana  │
│          │    │(缓冲层) │    │          │    │                │    │(反向代理) │    │         │
└──────────┘    └────────┘    └──────────┘    └────────────────┘    └──────────┘    └─────────┘
```

**消息队列的作用**：
- 缓冲：避免 Logstash 或 ES 故障时数据丢失
- 削峰填谷：均衡网络传输
- 解耦：Filebeat 和 Logstash 解耦

**适用场景**：生产环境，大数据量处理。确保数据安全性和完整性。

---

## 三、Logstash 详解

### Logstash 核心概念

| 概念 | 说明 |
|------|------|
| **Pipeline** | input → filter → output 三个阶段的处理流程 |
| **Event** | 数据在内部的流转表现形式（Java Object） |
| **Codec** | 编解码器，原始数据 → Event → 目标数据 |

### Logstash Pipeline 配置

```
input {
  beats { port => 5044 }       # 接收 Filebeat 数据
}

filter {
  grok {                        # 结构化解析
    match => { "message" => "%{COMBINEDAPACHELOG}" }
  }
  date {                        # 日期转换
    match => [ "timestamp", "dd/MMM/yyyy:HH:mm:ss Z" ]
  }
  mutate {                      # 字段处理
    remove_field => ["@version"]
  }
}

output {
  elasticsearch {
    hosts => ["http://localhost:9200"]
    index => "web-logs-%{+YYYY.MM.dd}"
  }
}
```

### Logstash 安装与测试

```bash
# 下载
wget https://artifacts.elastic.co/downloads/logstash/logstash-8.14.3-linux-x86_64.tar.gz

# 测试最基本的管道
bin/logstash -e 'input { stdin { } } output { stdout {} }'

# 输入 "hello logstash" → 输出结构化 JSON
```

### 常用 Input 插件

| 插件 | 说明 |
|------|------|
| `file` | 读取文件 |
| `beats` | 接收 Filebeat 数据 |
| `kafka` | 消费 Kafka 消息 |
| `stdin` | 标准输入（测试用） |
| `syslog` | 系统日志 |

### 常用 Filter 插件

| 插件 | 说明 |
|------|------|
| `grok` | 正则解析非结构化数据为结构化 |
| `date` | 日期字段解析和转换 |
| `mutate` | 字段增删改 |
| `geoip` | IP 地理位置查询 |
| `drop` | 丢弃事件 |

---

## 四、Filebeat 配置

```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/*.log
    - /var/log/app/*.log

  # 多行合并
  multiline.pattern: '^\['
  multiline.negate: true
  multiline.match: after

output.logstash:
  hosts: ["localhost:5044"]

# 或者直接输出到 ES
# output.elasticsearch:
#   hosts: ["localhost:9200"]
```

---

## 五、Kibana 可视化

- 连接到 ES 后，可通过 Kibana Discovery 搜索和过滤日志
- Kibana Visualize：创建柱状图、折线图、饼图等
- Kibana Dashboard：组合多个 Visualization 为仪表盘

---

## 六、架构选型建议

| 场景 | 架构 | 原因 |
|------|------|------|
| 开发/测试 | Filebeat → Logstash → ES → Kibana | 简单够用 |
| 小规模生产 | + Kafka | 加缓冲防丢 |
| 大规模生产 | + Kafka + Nginx | 全链路稳定 |

**组件版本对齐**：所有 Elastic Stack 组件必须用**相同版本**。

---

## 七、总结

```
ELK 日志系统的价值：
  集中收集 → 统一处理 → 高效搜索 → 直观可视化

核心组件：
  Filebeat  → 轻量级日志收集
  Logstash  → 数据过滤和转换 (input/filter/output)
  ES        → 分布式搜索和存储
  Kibana    → Web 可视化界面

生产增强：
  Kafka     → 消息缓冲（防丢/削峰）
  Nginx     → 反向代理（负载/安全）
```

> 有道云笔记：[ELK日志采集系统实战](https://note.youdao.com/s/RS7Q6QL7)
