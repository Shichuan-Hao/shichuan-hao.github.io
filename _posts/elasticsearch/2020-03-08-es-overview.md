---
title: ElasticSearch 概述
description: ElasticSearch 概述。
author: 郝世川
date: 2020-03-08 17:27:00 +0800
categories: [分布式, ElasticSearch]
tags: [排版]
# pin: true
# math: true
# mermaid: true
# image:
#   path: /assets/img/posts/devices-mockup.png
#   lqip: data:image/webp;base64,UklGRpoAAABXRUJQVlA4WAoAAAAQAAAADwAABwAAQUxQSDIAAAARL0AmbZurmr57yyIiqE8oiG0bejIYEQTgqiDA9vqnsUSI6H+oAERp2HZ65qP/VIAWAFZQOCBCAAAA8AEAnQEqEAAIAAVAfCWkAALp8sF8rgRgAP7o9FDvMCkMde9PK7euH5M1m6VWoDXf2FkP3BqV0ZYbO6NA/VFIAAAA
#   alt: Chirpy 主题在多种设备上的响应式渲染效果。
---

## 什么是 ElasticSearch

ElasticSearch (简称 ES) 是一个开源的分布式搜索和数据分析引擎，是用Java开发并且是当前最流行的开源的企业级搜索引擎。能够达到近实时搜索，它专门设计用于处理大规模的文本数据和实现高性能的全文检索。

## ElasticSearch 的优势
搜索引擎的排名参见：[搜索引擎排名](https://db-engines.com/en/ranking/search+engine)

作为排名第一的搜索引擎，其优势如下：
1. 分布式架构：ES 采用分布式架构，可以轻松处理大规模数据，并支持水平扩展，提供系统的可扩展性和容错性
2. 全文检索功能：ES 提供了强大的全文检索功能，可以对文本数据进行高效的搜索和分析，支持复杂的查询语法和自定义分析器。
3. 多语言支持：ES 支持多种语言的数据处理和检索，可以满足不同语言环境下的搜索需求。
4. 高性能：ES 采用倒排索引等优化技术，可以实现高效的搜索和数据处理性能，满足大规模数据实时查询需求
5. 实时性：ES 提供近乎实时的搜索和分析功能，确保用户能够及时获取最新的数据和信息
6. 易用性：ES 提供了丰富的 API 和插件，使得开发者可以轻松集成和使用，同时其查询语法简洁明了，容易上手。

> - [官方网站](https://www.elastic.co/) 
> - [官方文档](https://www.elastic.co/guide/index.html)
> - [官方社区](https://discuss.elastic.co/)
> - [官方博客](https://www.elastic.co/blog/)
> - [官方下载](https://www.elastic.co/cn/downloads/past-releases#elasticsearch)


## Elastic Stack 生态介绍
Elastic Stack 由 Logstash、Beats、Elasticsearch 和 Kibana 组成，是当前最流行的开源企业级搜索和分析平台，在数据采集、存储、分析、可视化等领域有着无可比拟的优势。

Elasticsearch
: 
  1. 作为Elastic Stack 的基石，ES 是一个高度可扩展的全文搜索与分析引擎。其
  2. 利用分布式架构提供近乎实时的数据搜索、分析和可视化能力。
  3. 通过强大的索引和查询功能，可以处理PB级的数据量，支持复杂的数据分析和挖掘需求，是构建现代数据驱动应用的理想选择。

Logstash
: 
  1. Logstash 是一个灵活的服务器端数据处理管道，能够同时从多个源采集数据，转换数据，然后将数据发送到自定的目的地。
  2. 支持丰富的插件生态系统，使得数据收集、解析和转换的过程变得高效且易于配置。
  3. 在 Elastic Stack 中扮演着数据预处理和传输的关键角色，确保数据以正确的格式和结构进入 Elasticsearch 中，未后续的分析和可视化提供坚实的基础。

Beats
: 
  1. Beats 是一个轻量级的数据采集器，转为发送数据到 Logstash、Elasticsearch 等目的地而设计。
  2. 每个 Beat 都是一个独立运行的守护进程，用来从系统或应用程序中收集数据，并将这些数据转发到指定的数据收集和处理系统中。
  3. Beats 家族包括 Filebeat（用于文件日志）、Metricbeat（用于系统和应用性能指标）、Heartbeat (用于监控服务可用性) 等多个成员，它们共同构成了强大的边缘数据采集网络，覆盖了广泛的监控和日志收集需求。

Kibana
: 
  1. Kibana 是Elastic Stack 的可视化和管理界面，为 Elasticsearch 数据提供了强大的可视化功能
  2. 通过 Kibana，用户可以轻松地创建仪表板、图表和地图，以直观的方式展示 Elasticsearch 中的数据。
  3. 提供了交互式查询和过滤功能，使用户能够深入挖掘数据，发现隐藏的趋势和模式。
  4. 作为 Elastic Stack 的用户界面，Kibana 使得数据分析变得更加简单和直观，是数据可视化的重要工具。

Elastic Stack 通过整合 Elasticserch、Logstash、Beats 和 Kibana 这四大核心组件，帮助我们实现数据收集、处理、存储到分析和可视化的一体化解决方案。这一方案不仅简化了数据处理的复杂性，还提高了数据处理的效率和准确性，是现代数据分析和监控领域不可或缺的强大工具。

## ElasticSearch 应用场景
<hl=red>只要用到搜索的场景，ElasticSearch几乎都可以是最好的选择。</hl> 结合Kibana、Logstash、Beats、ElasticSearch 可以用于全文检索、日志分析、商业智能等场景。

- 全文检索
: 
1. 支持各类应用、网站等全文搜索。包括淘宝、京东等电商平台的搜索，360手机助手、豌豆荚等应用市场平台的搜索，以及腾讯文档、石墨文档等平台的全文检索服务。
2. 支持用户通过自定义打分、自定义排序、高亮等机制召回期望的结果数据，通过跨机房/跨机架、异地容灾等策略，为用户提供高可用、高并发、低延时、用户体验好的搜索服务

- 日志分析
: 
  Elasticsearch 支持的日志包含但不限于如下类型：
    1. 用户行为日志、应用日志等业务日志。
    2. 慢查询、异常探测等状态日志
    3. Debug、Info、WARN、ERROR、FATAL 等不同等级的系统日志
  基于<color=red>倒排索引技术</color>，Elasticsearch 能够实现高效且灵活的搜索分析功能。从产生日志到生成相应的倒排索引并将其写入 Elasticsearch，再到最终用户可以访问这些信息，整个过程所需时间仅为秒级。这确保了Elasticsearch能够快速处理和检索大量数据，满足实时搜索和分析需求。因而，Elasticsearch 被广泛应用于快速分析和处理大量的日志数据，从而对业务运行状况进行实时的监控和故障排查。

- 商业智能场景
: 
  大型业务数据给电子商务、移动App开发、广告媒体等领域的企业的数据收集和数据分析带来巨大的挑战。而 Elasticsearch 具有结构化查询功能，能实现全文数据检索和聚合分析，所以能有效帮助客户对上诉大数据进行高效且个人性化的分析，进而发现问题、辅助业务决策，并从数据中挖掘真正的商业价值。比如睿思BI、百度数据可视化Suger BI...等，都借助Elasticsearch 的高效、实时的数据分析和可视化能力，帮助企业更好地理解市场趋势、优化决策过程。