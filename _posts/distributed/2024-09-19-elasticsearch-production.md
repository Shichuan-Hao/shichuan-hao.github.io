---

title: "ElasticSearch集群架构生产最佳实践"
description: "节点角色配置方案节点角色介绍如果你的 Elasticsearch 集群是 7.9 之前的版本,在配置节点的时候,则只会涉及节点类型的知识。"
author: hsc
date: 2024-09-19 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Redis', 'ElasticSearch']
toc: true

---

### 1. 节点角色配置方案节点角色介绍如果你的 Elasticsearch 集群是 7.9 之前的版本,在配置节点的时候,则只会涉及节点类型的知识。
主节点:负责集群管理和元数据维护,确保集群正常运行。
数据节点:负责存储、检索和处理数据,提供搜索和聚合功能。
协调节点:处理客户端请求,协调数据节点工作,优化分布式搜索。
ingest 节点:即预处理节点,负责数据预处理,如过滤、转换等,准备好数据再将其索引到数据节点。
Elasticsearch 7.9 版本开始引入节点角色的概念。节点角色划分的目的是让不同角色的节点各司其职,共同确保集群功能的稳定和性能的高可用。
Elasticsearch 早期版本(以 7.1 版本为例)中,如果配置仅候选主节点类型,那么极端情况下需要的配置如下:
1 node.master: true2 node.data: false3 node.ingest: false 这是非常烦琐的配置,其逻辑类似于“若我要说明自己是主节点,则要先说明我不是数据节点、不是 ingest 节点、不是 XXX 节点......”。 而节点角色的出现“革命性”地解决了这个问题。利用节点角色,我们只需要说明“我是 XXX”即可,而不需要卖力解释“我不是 XXX”。
1 node.roles: [data,master]以 Elasticsearch 8.X 版本集群为例,如果我们不手动设置节点角色,则默认节点角色为 cdfhilmrstw。
对默认节点角色 cdfhilmrstw 的解释如下表所示:
当集群规模比较大之后(比如集群节点数大于 6 个) ,就需要手动设定、配置节点角色。

一个节点只承担一个角色的配置在开发环境中,一个节点可承担多种角色。
在生产环境中:
根据数据量,写入和查询的吞吐量,选择合适的部署方式建议设置单一角色的节点这种单一角色职责分离的好处:
单一 master eligible nodes: 负责集群状态(cluster state)的管理使用低配置的 CPU,RAM 和磁盘单一 data nodes: 负责数据存储及处理客户端请求使用高配置的 CPU,RAM 和磁盘单一 ingest nodes: 负责数据处理使用高配置 CPU; 中等配置的 RAM; 低配置的磁盘单一 Coordinating Only Nodes(Client Node)
使用高配置 CPU; 高配置的 RAM; 低配置的磁盘生产环境中,建议为一些大的集群配置 Coordinating Only Nodes 扮演 Load Balancers,降低 Master 和 Data Nodes 的负载负责搜索结果的 Gather/Reduce 有时候无法预知客户端会发送怎么样的请求。比如大量占用内存的操作,一个深度聚合可能会引发 OOM 增加节点的场景当磁盘容量无法满足需求时,可以增加数据节点;
磁盘读写压力大时,增加数据节点当系统中有大量的复杂查询及聚合时候,增加 Coordinating 节点,增加查询的性能
2. 高可用场景部署方案读写分离架构 Hot & Warm 架构热节点存放用户最关心的热数据;温节点存放用户关心优先级低的暖数据;冷节点存放用户不太关心的冷数据。

典型的应用场景在成本有限的前提下,让客户关注的实时数据和历史数据硬件隔离,最大化解决客户反应的响应时间慢的问题。
业务场景描述:每日增量 6TB 日志数据,高峰时段写入及查询频率都较高,集群压力较大,查询 ES 时,常出现查询缓慢问题。
ES 集群的索引写入及查询速度主要依赖于磁盘的 IO 速度,冷热数据分离的关键为使用 SSD 磁盘存储热数据,提升查询效率。
若全部使用 SSD,成本过高,且存放冷数据较为浪费,因而使用普通 SATA 磁盘与 SSD 磁盘混搭,可做到资源充分利用,性能大幅提升的目标。
ES 为什么要设计 Hot & Warm 架构?
ES 数据通常不会有 Update 操作;
适用于 Time based 索引数据,同时数据量比较大的场景。
引入 Warm 节点,低配置大容量的机器存放老数据,以降低部署成本两类数据节点,不同的硬件配置:
Hot 节点(通常使用 SSD)..索引不断有新文档写入。
Warm 节点(通常使用 HDD)..索引不存在新数据的写入,同时也不存在大量的数据查询 Hot Nodes 用于数据的写入:
lndexing 对 CPU 和 IO 都有很高的要求,所以需要使用高配置的机器存储的性能要好,建议使用 SSDWarm Nodes 用于保存只读的索引,比较旧的数据。通常使用大容量的磁盘配置 Hot & Warm 架构使用 Shard Filtering 实现 Hot&Warm node 间的数据迁移 node.attr 来指定 node 属性:hot 或是 warm。
在 index 的 settings 里通过 index.routing.allocation 来指定索引(index)到一个满足要求的 node 设置 分配索引到节点,节点的属性规则 index.routing.allocation.include.{attr} 至少包含一个值 index.routina.allocation.exclude.{attr} 不能包含任何一个值 index.routina.allocation.require. {attr} 所有值都需要包含

使用 Shard Filtering,步骤分为以下几步:
标记节点(Tagging)
配置索引到 Hot Node 配置索引到 Warm 节点
1) 标记节点需要通过“node.attr”来标记一个节点节点的 attribute 可以是任何的 key/value 可以通过 elasticsearch.yml1 # 标记一个 Hot 节点 2 node.attr.my_node_type: hot34 # 标记一个 warm 节点 5 node.attr.my_node_type: warm67 # 查看节点 8 GET /_cat/nodeattrs?v2)配置 Hot 数据创建索引时候,指定将其创建在 hot 节点上

1 # 配置到 Hot 节点 2 PUT /index-2022-053 {4 "settings":{5 "number_of_shards":2,6 "number_of_replicas":0,7 "index.routing.allocation.require.my_node_type":"hot"
8 }9 }1011 POST /index-2022-05/_doc12 {13 "create_time":"2022-05-27"
14 }1516 #查看索引文档的分布 17 GET _cat/shards/index-2022-05?v3)旧数据移动到 Warm 节点 Index.routing.allocation 是一个索引级的 dynamic setting,可以通过 API 在后期进行设定 1 # 配置到 warm 节点 2 PUT /index-2022-05/_settings3 {4 "index.routing.allocation.require.my_node_type":"warm"
5 }6 GET _cat/shards/index-2022-05?v
3. ES 跨集群搜索(CCS)
ES 水平扩展存在的问题单集群水平扩展时,节点数不能无限增加

当集群的 meta 信息(节点,索引,集群状态)过多会导致更新压力变大,单个 Active Master 会成为性能瓶颈,导致整个集群无法正常工作早期版本,通过 Tribe Node 可以实现多集群访问的需求,但是还存在一定的问题 Tribe Node 会以 Client Node 的方式加入每个集群,集群中 Master 节点的任务变更需要 Tribe Node 的回应才能继续。
Tribe Node 不保存 Cluster State 信息,一旦重启,初始化很慢当多个集群存在索引重名的情况时,只能设置一种 Prefer 规则跨集群搜索实战 Elasticsearch 5.3 引入了跨集群搜索的功能(Cross Cluster Search),推荐使用允许任何节点扮演联合节点,以轻量的方式,将搜索请求进行代理不需要以 Client Node 的形式加入其他集群 1)配置集群

1 //启动 3 个集群 2 elasticsearch.bat -E node.name=cluster0node -E cluster.name=cluster0 -Epath.data=cluster0_data -E discovery.type=single-node -E http.port=9200 -Etransport.port=93003 elasticsearch.bat -E node.name=cluster1node -E cluster.name=cluster1 -Epath.data=cluster1_data -E discovery.type=single-node -E http.port=9201 -Etransport.port=93014 elasticsearch.bat -E node.name=cluster2node -E cluster.name=cluster2 -Epath.data=cluster2_data -E discovery.type=single-node -E http.port=9202 -Etransport.port=930256 //在每个集群上设置动态的设置 7 PUT _cluster/settings8 {9 "persistent": {10 "cluster": {11 "remote": {12 "cluster0": {13 "seeds": [14 "127.0.0.1:9300"
15 ],16 "transport.ping_schedule": "30s"
17 },18 "cluster1": {19 "seeds": [20 "127.0.0.1:9301"
21 ],22 "transport.compress": true,23 "skip_unavailable": true24 },25 "cluster2": {26 "seeds": [27 "127.0.0.1:9302"
28 ]29 }30 }31 }32 }33 }CCS 的配置:
1)seeds 配置的远程集群的 remote cluster 的一个 node。
2)connected 如果至有少一个到远程集群的连接则为 true。
3)num_nodes_connected 远程集群中连接节点的数量。
4)max_connections_per_cluster 远程集群维护的最大连接数。
5)transport.ping_schedule 设置了 tcp 层面的活性监听 6)skip_unavailable 设置为 true 的话,当这个 remote cluster 不可用的时候,就会忽略,默认是 false,当对应的 remotecluster 不可用的话,则会报错。
7)cluster.remote.connections_per_clustergateway nodes 数量,默认是 38)cluster.remote.initial_connect_timeout 节点启动时等待远程节点的超时时间,默认是 30s9)cluster.remote.node.attr:
一个节点属性,用于过滤掉 remote cluster 中 符合 gateway nodes 的节点,比如设置 cluster.remote.node.attr=gateway,那么将匹配节点属性 node.attr.gateway: true 的 node 才会被该 node 连接用来做 CCS 查询。
10)cluster.remote.connect:
默认情况下,群集中的任意节点都可以充当 federated client 并连接到 remote cluster,cluster.remote.connect 可以设置为 false(默认为 true)以防止某些节点连接到 remote cluster11)在使用 api 进行动态设置的时候每次都要把 seeds 带上 2)创建测试数据

1 #在不同集群上执行 2 # cluster0 localhost:92003 POST /users/_doc4 {5 "name":"fox",6 "age":"30"
7 }89 #cluster1 localhost:920110 POST /users/_doc11 {12 "name":"monkey",13 "age":"33"
14 }1516 #cluster2 localhost:920217 POST /users/_doc18 {19 "name":"mark",20 "age":"35"
21 }223)查询 1 #查询结果获取到所有集群符合要求的数据 2 GET /users,cluster1:users,cluster2:users/_search3 {4 "query": {5 "range": {6 "age": {7 "gte": 30,8 "lte": 409 }10 }11 }12 }

### 4. 如何对集群的容量进行规划一个集群总共需要多少个节点?一个索引需要设置几个分片?规划上需要保持一定的余量,当负载出现波动,节点出现丢失时,还能正常运行。
做容量规划时,一些需要考虑的因素:
机器的软硬件配置单条文档的大小│文档的总数据量│索引的总数据量((Time base 数据保留的时间)|副本分片数文档是如何写入的(Bulk 的大小)
文档的复杂度,文档是如何进行读取的(怎么样的查询和聚合)
做容量规划之前应该先对业务的性能需求做一个评估。
评估业务的性能需求:
数据吞吐及性能需求数据写入的吞吐量,每秒要求写入多少数据?
查询的吞吐量?
单条查询可接受的最大返回时间?
了解你的数据数据的格式和数据的 Mapping 实际的查询和聚合长的是什么样的常见用例:
搜索: 固定大小的数据集搜索的数据集增长相对比较缓慢日志: 基于时间序列的数据使用 ES 存放日志与性能指标。数据每天不断写入,增长速度较快结合 Warm Node 做数据的老化处理硬件配置:
选择合理的硬件,数据节点尽可能使用 SSD 搜索等性能要求高的场景,建议 SSD 按照 1∶10-20 的比例配置内存和硬盘日志类和查询并发低的场景,可以考虑使用机械硬盘存储按照 1:50 的比例配置内存和硬盘单节点数据建议控制在 2TB 以内,最大不建议超过 5TBJVM 配置机器内存的一半,JVM 内存配置不建议超过 32G 不建议在一台服务器上运行多个节点

内存大小要根据 Node 需要存储的数据来进行估算搜索类的比例建议: 1:16 日志类: 1:48——1:96 之间假设总数据量 1T,设置一个副本就是 2T 总数据量如果搜索类的项目,每个节点 31*16 = 496 G,加上预留空间。所以每个节点最多 400G 数据,至少需要 5 个数据节点如果是日志类项目,每个节点 31*50= 1550 GB,2 个数据节点即可部署方式:
按需选择合理的部署方式如果需要考虑可靠性高可用,建议部署 3 台单一的 Master 节点如果有复杂的查询和聚合,建议设置 Coordinating 节点集群扩容:
增加 Coordinating / Ingest Node 解决 CPU 和内存开销的问题增加数据节点解决存储的容量的问题为避免分片分布不均的问题,要提前监控磁盘空间,提前清理数据或增加节点容量规划案例 1: 固定大小的数据集场景:产品信息库搜索特性:
被搜索的数据集很大,但是增长相对比较慢(不会有大量的写入)。更关心搜索和聚合的读取性能数据的重要性与时间范围无关。关注的是搜索的相关度估算索引的的数据量,然后确定分片的大小:
单个分片的数据不要超过 20 GB 可以通过增加副本分片,提高查询的吞吐量思考:如果单个索引数据量非常大,如何优化提升查询性能?
拆分索引如果业务上有大量的查询是基于一个字段进行 Filter,该字段又是一个数量有限的枚举值。
例如订单所在的地区。可以考虑以地区进行索引拆分如果在单个索引有大量的数据,可以考虑将索引拆分成多个索引:
查询性能可以得到提高如果要对多个索引进行查询,还是可以在查询中指定多个索引得以实现如果业务上有大量的查询是基于一个字段进行 Filter,该字段数值并不固定

可以启用 Routing 功能,按照 filter 字段的值分布到集群中不同的 shard,降低查询时相关的 shard 数提高 CPU 利用率 1 es 分片路由的规则:
2 shard_num = hash(_routing) % num_primary_shards3 _routing 字段的取值,默认是_id 字段,可以自定义。
45 PUT /users6 {7 "settings": {8 "number_of_shards":29 }10 }11 POST /users/_create/1?routing=fox12 {13 "name":"fox"
14 }容量规划案例 2: 基于时间序列的数据相关的场景:
日志/指标/安全相关的事件舆情分析特性:
每条数据都有时间戳,文档基本不会被更新(日志和指标数据)
用户更多的会查询近期的数据,对旧的数据查询相对较少对数据的写入性能要求比较高创建基于时间序列的索引创建 timed-base 索引在索引的名字中增加时间信息按照每天/每周/每月的方式进行划分这样做的好处:更加合理的组织索引,例如随着时间推移,便于对索引做的老化处理。
可以利用 Hot & Warm 架构备份和删除的效率高基于 Date Math 方式建立索引比如:假设当前日期 2022-05-27

<indexName-{now/d}> indexName-2022.05.27<indexName-{now{YYYY.MM}}> indexName-2022.051 # PUT /<logs-{now/d}>2 PUT /%3Clogs-%7Bnow%2Fd%7D%3E34 # POST /<logs-{now/d}>/_search5 POST /%3Clogs-%7Bnow%2Fd%7D%3E/_search 基于 Index Alias 索引最新的数据创建索引,每天/每周/每月在索引的名字中增加时间信息

1 PUT /logs_2022-05-272 PUT /logs_2022-05-2634 #可以每天晚上定时执行 5 POST /_aliases6 {7 "actions": [8 {9 "add": {10 "index": "logs_2022-05-27",11 "alias": "logs_write"
12 }13 },14 {15 "remove": {16 "index": "logs_2022-05-26",17 "alias": "logs_write"
18 }19 }20 ]21 }2223 GET /logs_write
5. 如何设计和管理分片单个分片
7.0 开始,新创建一个索引时,默认只有一个主分片。
单个分片,查询算分,聚合不准的问题都可以得以避免单个索引,单个分片时候,集群无法实现水平扩展。
即使增加新的节点,无法实现水平扩展两个分片

集群增加一个节点后,Elasticsearch 会自动进行分片的移动,也叫 Shard Rebalancing 如何设计分片数当分片数>节点数时一旦集群中有新的数据节点加入,分片就可以自动进行分配分片在重新分配时,系统不会有 downtime 多分片的好处: 一个索引如果分布在不同的节点,多个节点可以并行执行查询可以并行执行数据写入可以分散到多个机器案例 1 每天 1GB 的数据,一个索引一个主分片,一个副本分片需保留半年的数据,接近 360 GB 的数据量,360 个分片案例 25 个不同的日志,每天创建一个日志索引。每个日志索引创建 10 个主分片保留半年的数据 5*10* 30* 6 = 9000 个分片分片过多所带来的副作用 Shard 是 Elasticsearch 实现集群水平扩展的最小单位。过多设置分片数会带来一些潜在的问题:
每个分片是一个 Lucene 的索引,会使用机器的资源。过多的分片会导致额外的性能开销。
Lucene Indices / File descriptors / RAM/ CPU 每次搜索的请求,需要从每个分片上获取数据分片的 Meta 信息由 Master 节点维护。过多,会增加管理的负担。经验值,控制分片总数在 10W 以内如何确定主分片数从存储的物理角度看:
搜索类应用,单个分片不要超过 20 GB 日志类应用,单个分片不要大于 50 GB 为什么要控制分片存储大小:
提高 Update 的性能进行 Merge 时,减少所需的资源丢失节点后,具备更快的恢复速度

便于分片在集群内 Rebalancing 如何确定副本分片数副本是主分片的拷贝:
提高系统可用性..响应查询请求,防止数据丢失需要占用和主分片一样的资源对性能的影响:
副本会降低数据的索引速度: 有几份副本就会有几倍的 CPU 资源消耗在索引上会减缓对主分片的查询压力,但是会消耗同样的内存资源。如果机器资源充分,提高副本数,可以提高整体的查询 QPSES 的分片策略会尽量保证节点上的分片数大致相同,但是有些场景下会导致分配不均匀:
扩容的新节点没有数据,导致新索引集中在新的节点热点数据过于集中,可能会产生性能问题可以通过调整分片总数,避免分配不均衡"index.routing.allocation.total_shards_per_node",index 级别的,表示这个 index 每个 Node 总共允许存在多少个 shard,默认值是-1 表示无穷多个;
"cluster.routing.allocation.total_shards_per_node",cluster 级别,表示集群范围内每个 Node 允许存在有多少个 shard。默认值是-1 表示无穷多个。
如果目标 Node 的 Shard 数超过了配置的上限,则不允许分配 Shard 到该 Node 上。注意:index 级别的配置会覆盖 cluster 级别的配置。
思考:5 个节点的集群。索引有 5 个主分片,1 个副本,index.routing.allocation.total_shards_per_node 应该如何设置?
(5+5)/ 5= 2 生产环境中要适当调大这个数字,避免有节点下线时,分片无法正常迁移
