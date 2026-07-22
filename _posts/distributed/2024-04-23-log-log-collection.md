---


title: "微服务日志采集与分析系统实战"
description: "为什么要使用 ELK 随着企业信息化进程的加速,日志数据量急剧增加且来源多样、格式复杂,传统的日志管理方式已难以满足需求。"
author: hsc
date: 2024-04-23 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Redis', 'Kafka', 'ElasticSearch', '分布式事务']
toc: true


---

### 1. 为什么要使用 ELK 随着企业信息化进程的加速,日志数据量急剧增加且来源多样、格式复杂,传统的日志管理方式已难以满足需求。
ELK(Elasticsearch、Logstash、Kibana)的引入,正是为了应对这些挑战。 ELK 通过其强大的分布式搜索能力(Elasticsearch)、灵活的数据采集与处理功能(Logstash)、以及直观的数据可视化界面(Kibana),提供了高效、实时、可扩展且易用的日志管理解决方案,帮助企业和开发人员更有效地管理和分析日志数据,从而提高工作效率和问题解决速度。
以下是使用 ELK 的主要原因:
1. 集中化管理与高效检索日志:
在大型分布式系统中,ELK 通过构建集中式日志系统,实现所有节点上日志的统一收集、管理和访问,提高定位问题的效率。
Elasticsearch 提供强大的检索特性,能够快速查询问题日志,显著提升运维人员的工作效率。
2. 全面的日志分析与系统监控:
ELK 能够管理和分析包括系统日志、应用程序日志和安全日志在内的多种日志,帮助系统运维和开发人员了解服务器软硬件信息、检查配置错误及其原因。

通过分析和监控日志,可以及时了解服务器的负荷、性能和安全性,从而及时采取措施纠正错误。
3. 直观的数据可视化与理解:
Kibana 为 Elasticsearch 提供 Web 可视化界面,可以生成各种维度表格、图形,使复杂的日志数据可视化。
可视化界面帮助用户更直观地理解和分析数据,进一步提升日志分析和系统监控的效果。
2. ELK 的整体架构分析 ELK 架构分为两种,一种是经典的 ELK,另外一种是加上消息队列(Redis 或 Kafka 或 RabbitMQ)和 Nginx 结构。
2.1 经典的 ELK 组成:经典的 ELK 架构主要由 Filebeat + Logstash + Elasticsearch + Kibana 组成。在早期,ELK 架构可能仅包含 Logstash + Elasticsearch + Kibana,但随着技术的发展,Filebeat 因其轻量级和高效性逐渐被引入作为日志收集工具。
特点:
日志收集:Filebeat 作为轻量级的日志收集代理,部署在客户端上,消耗资源少,能够高效地收集日志数据。
数据处理:Logstash 作为数据处理管道,负责将 Filebeat 收集的日志数据进行过滤、转换等操作,然后发送到 Elasticsearch 进行存储。
存储与搜索:Elasticsearch 是一个基于 Lucene 的分布式搜索和分析引擎,提供强大的数据存储和搜索能力。
可视化:Kibana 为 Elasticsearch 提供 Web 可视化界面,允许用户通过图表、仪表盘等方式直观地查看和分析日志数据。
适用场景:经典的 ELK 架构主要适用于数据量较小的开发环境。然而,由于缺少消息队列的缓冲机制,当 Logstash 或 Elasticsearch 出现故障时,可能存在数据丢失的风险。
2.2 整合消息队列+Nginx 的 ELK 架构组成:在经典的 ELK 架构基础上,整合消息队列(如 Redis、Kafka、RabbitMQ)和 Nginx,形成更为复杂的架构。
特点:
消息队列:引入消息队列作为缓冲机制,确保即使在 Logstash 或 Elasticsearch 出现故障时,日志数据也不会丢失。消息队列能够均衡网络传输,降低数据丢失的可能性。
Nginx:Nginx 作为高性能的 Web 和反向代理服务器,可以进一步优化整个系统的性能和可用性。它可以在负载均衡、缓存等方面发挥作用,提升用户访问体验。
扩展性:由于引入了消息队列和 Nginx 等组件,整个架构的扩展性得到增强。可以根据实际需求动态调整各组件的资源分配和部署规模。
适用场景:整合消息队列+Nginx 的架构主要适用于生产环境,特别是需要处理大数据量的场景。它能够确保数据的安全性和完整性,同时提供高性能的日志处理和可视化分析服务。

### 3. 数据处理管道 Logstash 详解 Logstash 的概述 Logstash 是免费且开放的服务器端数据处理管道,能够从多个来源采集数据,转换数据,然后将数据发送到您最喜欢的存储库中。
https://www.elastic.co/cn/logstash/应用场景:ETL 工具 / 数据采集处理引擎 Logstash 的工作原理分析 Logstash 核心概念 Pipeline 包含了 input—filter—output 三个阶段的处理流程插件生命周期管理队列管理 Logstash Event 数据在内部流转时的具体表现形式。数据在 input 阶段被转换为 Event,在 output 被转化成目标格式数据 Event 其实是一个 Java Object,在配置文件中,可以对 Event 的属性进行增删改查 Codec (Code / Decode)
将原始数据 decode 成 Event;将 Event encode 成目标数据 Logstash 数据传输原理
1. 数据采集与输入:Logstash 支持各种输入选择,能够以连续的流式传输方式,轻松地从日志、指标、 Web 应用以及数据存储中采集数据。
2. 实时解析和数据转换:通过 Logstash 过滤器解析各个事件,识别已命名的字段来构建结构,并将它们转换成通用格式,最终将数据从源端传输到存储库中。
3. 存储与数据导出:Logstash 提供多种输出选择,可以将数据发送到指定的地方。
Logstash 通过管道完成数据的采集与处理,管道配置中包含 input、output 和 filter(可选)插件,input 和 output 用来配置输入和输出数据源、 filter 用来对数据进行过滤或预处理。

Logstash 的安装与配置 Logstash 安装 logstash 官方文档: https://www.elastic.co/guide/en/logstash/8.14/installing-logstash.html1)下载并解压 logstash 下载地址: https://www.elastic.co/cn/downloads/past-releases#logstash 选择版本:8.14.31 #下载 Logstash2 #windows3 https://artifacts.elastic.co/downloads/logstash/logstash-8.14.3-windows-x86_64.zip4 #linux5 https://artifacts.elastic.co/downloads/logstash/logstash-8.14.3-linux-x86_64.tar.gz2)测试:运行最基本的 logstash 管道 1 cd logstash-8.14.32 #linux3 #-e 选项表示,直接把配置放在命令中,这样可以有效快速进行测试 4 bin/logstash -e 'input { stdin { } } output { stdout {} }'5 #windows6 .\bin\logstash.bat -e "input { stdin { } } output { stdout {} }"
测试结果:
Logstash 的配置参考:https://www.elastic.co/guide/en/logstash/8.14/configuration.htmlLogstash 的管道配置文件对每种类型的插件都提供了一个单独的配置部分,用于处理管道事件。

1 input {2 stdin { }3 }45 filter {6 grok {7 match => { "message" => "%{COMBINEDAPACHELOG}" }8 }9 date {10 match => [ "timestamp" , "dd/MMM/yyyy:HH:mm:ss Z" ]11 }12 }1314 output {15 elasticsearch {16 index => "logstash-demo"
17 hosts => ["localhost:9200"]18 }19 stdout { codec => rubydebug }20 }每个配置部分可以包含一个或多个插件。例如,指定多个 filter 插件,Logstash 会按照它们在配置文件中出现的顺序进行处理。
1 #运行 2 bin/logstash -f logstash-demo.conf 测试效果 Loginstash 插件 Input Pluginshttps://www.elastic.co/guide/en/logstash/8.14/input-plugins.html 一个 Pipeline 可以有多个 input 插件 Stdin / File

Beats / Log4J /Elasticsearch / JDBC / Kafka /Rabbitmq /RedisJMX/ HTTP / Websocket / UDP / TCPGoogle Cloud Storage / S3Github / TwitterFilter Pluginshttps://www.elastic.co/guide/en/logstash/8.14/filter-plugins.htmlFilter Plugin 可以对 Logstash Event 进行各种处理,例如解析,删除字段,类型转换 Date: 日期解析 Dissect: 分割符解析 Grok: 正则匹配解析 Mutate: 对字段做各种操作 Convert : 类型转换 Gsub : 字符串替换 Split / Join /Merge: 字符串切割,数组合并字符串,数组合并数组 Rename: 字段重命名 Update / Replace: 字段内容更新替换 Remove_field: 字段删除 Ruby: 利用 Ruby 代码来动态修改 EventOutput Pluginshttps://www.elastic.co/guide/en/logstash/8.14/output-plugins.html 将 Event 发送到特定的目的地,是 Pipeline 的最后一个阶段。
常见 Output Plugins:
ElasticsearchEmail / PagedutyInfluxdb / Kafka / Mongodb / Opentsdb / ZabbixHttp / TCP / WebsocketCodec Pluginshttps://www.elastic.co/guide/en/logstash/8.14/codec-plugins.html 将原始数据 decode 成 Event;将 Event encode 成目标数据内置的 Codec Plugins:
Line / MultilineJSON / Avro / Cef (ArcSight Common Event Format)
Dots / RubydebugCodec Plugin 测试

1 # single line2 bin/logstash -e "input{stdin{codec=>line}}output{stdout{codec=> rubydebug}}"
3Codec Plugin —— Multiline 设置参数:
pattern: 设置行匹配的正则表达式 what : 如果匹配成功,那么匹配行属于上一个事件还是下一个事件 previous / nextnegate : 是否对 pattern 结果取反 true / false

1 # 多行数据,异常 2 Exception in thread "main" java.lang.NullPointerException3 at com.example.myproject.Book.getTitle(Book.java:16)
4 at com.example.myproject.Author.getBookTitles(Author.java:25)
5 at com.example.myproject.Bootstrap.main(Bootstrap.java:14)
678 #vim multiline-exception.conf9 input {10 stdin {11 codec => multiline {12 pattern => "^\s"
13 what => "previous"
14 }15 }16 }1718 filter {}1920 output {21 stdout { codec => rubydebug }22 }2324 #执行管道 25 bin/logstash -f multiline-exception.confLogstash QueueIn Memory Queue 进程 Crash,机器宕机,都会引起数据的丢失 Persistent Queue 机器宕机,数据也不会丢失; 数据保证会被消费; 可以替代 Kafka 等消息队列缓冲区的作用 1 # pipelines.yml2 queue.type: persisted (默认是 memory)
3 queue.max_bytes: 4gb

实践练习:同步 mysql 数据到 Elasticsearch 需求分析将数据库中的数据同步到 ES,借助 ES 的全文搜索,提高搜索速度需要把新增用户信息同步到 Elasticsearch 中用户信息 Update 后,需要能被更新到 Elasticsearch 支持增量更新用户注销后,不能被 ES 所搜索到实现思路借助 JDBC Input Plugin 将数据从数据库读到 Logstash 需要自己提供所需的 JDBC Driver;
JDBC Input Plugin 支持定时任务 Scheduling,其语法来自 Rufus-scheduler,其扩展了 Cron,使用 Cron 的语法可以完成任务的触发;
JDBC Input Plugin 支持通过 Tracking_column / sql_last_value 的方式记录 State,最终实现增量的更新;
官方文档:Jdbc input plugin 拓展:如何保证 Mysql 数据库到 ES 的数据一致性 JDBC Input Plugin 实现步骤 1)拷贝 jdbc 依赖到 logstash-8.14.3/drivers(自定义的)目录下 2)准备 mysql-demo.conf 配置文件

1 input {2 jdbc {3 jdbc_driver_library => "/home/fox/logstash-8.14.3/driver/mysql-connector-java5.1.49.jar"
4 jdbc_driver_class => "com.mysql.jdbc.Driver"
5 jdbc_connection_string => "jdbc:mysql://localhost:3306/test?useSSL=false"
6 jdbc_user => "root"
7 jdbc_password => "123456"
8 #启用追踪,如果为 true,则需要指定 tracking_column9 use_column_value => true10 #指定追踪的字段,11 tracking_column => "last_updated"
12 #追踪字段的类型,目前只有数字(numeric)和时间类型(timestamp),默认是数字类型 13 tracking_column_type => "numeric"
14 #记录最后一次运行的结果 15 record_last_run => true16 #上面运行结果的保存位置 17 last_run_metadata_path => "jdbc-position.txt"
18 statement => "SELECT * FROM user where last_updated >:sql_last_value;"
19 schedule => " * * * * * *"
20 }21 }22 output {23 elasticsearch {24 document_id => "%{id}"
25 document_type => "_doc"
26 index => "users"
27 hosts => ["http://localhost:9200"]28 username: "elastic"
29 password: "123456"
30 }31 stdout{32 codec => rubydebug33 }34 }3)运行 logstash

1 bin/logstash -f mysql-demo.conf 测试 1 #user 表 2 CREATE TABLE `user` (3 `id` int NOT NULL AUTO_INCREMENT,4 `name` varchar(50) DEFAULT NULL,5 `address` varchar(50) DEFAULT NULL,6 `last_updated` bigint DEFAULT NULL,7 `is_deleted` int DEFAULT NULL,8 PRIMARY KEY (`id`)
9 ) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 ;
10 #插入数据 11 INSERT INTO user(name,address,last_updated,is_deleted) VALUES("张三","广州天河",unix_timestamp(NOW()),0);
1 # 更新 2 update user set address="广州白云山",last_updated=unix_timestamp(NOW()) where name="张三";
1 #删除 2 update user set is_deleted=1,last_updated=unix_timestamp(NOW()) where name="张三";

1 #ES 中查询 2 # 创建 alias,只显示没有被标记 deleted 的用户 3 POST /_aliases4 {5 "actions": [6 {7 "add": {8 "index": "users",9 "alias": "view_users",10 "filter" : { "term" : { "is_deleted" : 0} }11 }12 }13 ]14 }1516 # 通过 Alias 查询,查不到被标记成 deleted 的用户 17 POST view_users/_search1819 POST view_users/_search20 {21 "query": {22 "term": {23 "name.keyword": {24 "value": "张三"
25 }26 }27 }28 }
4. 轻量级采集器 FileBeat 详解 FileBeat 的概述 Beats 是一个免费且开放的平台,集合了多种单一用途的数据采集器。它们从成百上千或成千上万台机器和系统向 Logstash 或 Elasticsearch 发送数据。

FileBeat 专门用于转发和收集日志数据的轻量级采集工具。它可以作为代理安装在服务器上,FileBeat 监视指定路径的日志文件,收集日志数据,并将收集到的日志转发到 Elasticsearch 或者 Logstash。
FileBeat 的工作原理分析启动 FileBeat 时,会启动一个或者多个输入(Input),这些 Input 监控指定的日志数据位置。 FileBeat 会针对每一个文件启动一个 Harvester(收割机)。Harvester 读取每一个文件的日志,将新的日志发送到 libbeat,libbeat 将数据收集到一起,并将数据发送给输出(Output)。
logstash vs FileBeatLogstash 是在 jvm 上运行的,资源消耗比较大。而 FileBeat 是基于 golang 编写的,功能较少但资源消耗也比较小,更轻量级。
Logstash 和 Filebeat 都具有日志收集功能,Filebeat 更轻量,占用资源更少 Logstash 具有 Filter 功能,能过滤分析日志一般结构都是 Filebeat 采集日志,然后发送到消息队列、 Redis、MQ 中,然后 Logstash 去获取,利用 Filter 功能过滤分析,然后存储到 Elasticsearch 中 FileBeat 和 Logstash 配合,实现背压机制。当将数据发送到 Logstash 或 Elasticsearch 时,Filebeat 使用背压敏感协议,以应对更多的数据量。如果 Logstash 正在忙于处理数据,则会告诉 Filebeat 减慢读取速度。一旦拥堵得到解决,Filebeat 就会恢复到原来的步伐并继续传输数据。
Filebeat 的安装与配置 https://www.elastic.co/guide/en/beats/filebeat/8.14/filebeat-installation-configuration.html1)下载并解压 Filebeat 下载地址:https://www.elastic.co/cn/downloads/past-releases#filebeat 选择版本:8.14.31 #windows2 https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-8.14.3-windowsx86_64.zip3 # linux4 curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-8.14.3-linuxx86_64.tar.gz5 tar xzvf filebeat-8.14.3-linux-x86_64.tar.gz

2)编辑配置修改 filebeat.yml 以设置连接信息:
1 output.elasticsearch:
2 hosts: ["192.168.65.174:9200","192.168.65.192:9200","192.168.65.204:9200"]3 username: "elastic"
4 password: "123456"
5 setup.kibana:
6 host: "192.168.65.174:5601"
3) 启用和配置数据收集模块从安装目录中,运行:
1 # 查看可以模块列表 2 ./filebeat modules list34 #启用 nginx 模块 5 ./filebeat modules enable nginx6 #如果需要更改 nginx 日志路径,修改 modules.d/nginx.yml7 - module: nginx8 access:
9 enabled: true10 var.paths: ["/var/log/nginx/access.log*"]1112 #启用 Logstash 模块 13 ./filebeat modules enable logstash14 #在 modules.d/logstash.yml 文件中修改设置 15 - module: logstash16 log:
17 enabled: true18 var.paths: ["/home/fox/logstash-8.14.3/logs/*.log"]194)启动 Filebeat

1 # setup 命令加载 Kibana 仪表板。 如果仪表板已经设置,则忽略此命令。
2 ./filebeat setup3 # 启动 Filebeat4 ./filebeat -e 启动成功后,在 kibana 中可以查看到 logstash 的日志实践练习 1:FileBeat 采集 tomcat 服务器日志并发送到 LogstashTomcat 服务器运行过程中产生很多日志信息,通过 filebeat 采集 tomcat 日志并发送到 Logstash1)配置 FileBeats 采集 tomcat 日志并将日志发送到 Logstash 创建配置文件 filebeat-tomcat.yml,配置 FileBeats 将数据发送到 Logstash1 #因为 Tomcat 的 web log 日志都是以 IP 地址开头的,所以我们需要修改下匹配字段。
2 # 不以 ip 地址开头的行追加到上一行 3 filebeat.inputs:
4 - type: log5 enabled: true6 paths:
7 - /home/fox/apache-tomcat-9.0.93/logs/*access*.*8 multiline.pattern: '^\\d+\\.\\d+\\.\\d+\\.\\d+ '9 multiline.negate: true10 multiline.match: after1112 output.logstash:
13 enabled: true14 hosts: ["localhost:5044"]15pattern:正则表达式 negate:true 或 false;默认是 false,匹配 pattern 的行合并到上一行;true,不匹配 pattern 的行合并到上一行 match:after 或 before,合并到上一行的末尾或开头 2)启动 FileBeat,并指定使用指定的配置文件

1 ./filebeat -e -c filebeat-tomcat.yml 可能出现的异常:
异常 1:Exiting: error loading config file: config file ("filebeat-tomcat.yml") can only be writable by theowner but the permissions are "-rw-rw-r--" (to fix the permissions use: 'chmod go-w/home/fox/filebeat-8.14.3-linux-x86_64/filebeat-tomcat.yml')
因为安全原因不要其他用户写的权限,去掉写的权限就可以了 1 chmod 644 filebeat-tomcat.yml 异常 2:Failed to connect to backoff(async(tcp://192.168.65.204:5044)): dial tcp192.168.65.204:5044: connect: connection refusedFileBeat 将尝试建立与 Logstash 监听的 IP 和端口号进行连接。但此时,我们并没有开启并配置 Logstash,所以 FileBeat 是无法连接到 Logstash 的。
2) 配置 Logstash 接收 FileBeat 收集的数据并打印 1 vim config/logstsh-tomcat.conf2 # 配置从 FileBeat 接收数据 3 input {4 beats {5 port => 50446 }7 }89 output {10 stdout {11 codec => rubydebug12 }13 }测试 logstash 配置是否正确

1 bin/logstash -f config/logstsh-tomcat.conf --config.test_and_exit 启动 logstash1 # reload.automatic:修改配置文件时自动重新加载 2 bin/logstash -f config/logstsh-tomcat.conf --config.reload.automatic 测试:访问 tomcat,logstash 是否接收到了 Filebeat 传过来的 tomcat 日志实践练习 2: 整合 ELK 采集与分析 tomcat 日志 1)Logstash 输出数据到 Elasticsearch 如果我们需要将数据输出值 ES 而不是控制台的话,我们修改 Logstash 的 output 配置。
1 vim config/logstsh-tomcat.conf2 input {3 beats {4 port => 50445 }6 }78 output {9 elasticsearch {10 hosts => ["http://localhost:9200"]11 index => "tomcat-logs"
12 user => "elastic"
13 password => "123456"
14 }15 stdout{16 codec => rubydebug17 }18 }启动 logstash

1 bin/logstash -f config/logstsh-tomcat.conf --config.reload.automatic 测试日志是否保存到了 ES 思考:日志信息都保证在 message 字段中,是否可以把日志进行解析一个个的字段?例如:IP 字段、时间、请求方式、请求 URL、响应结果。
2) 利用 Logstash 过滤器解析日志从日志文件中收集到的数据包含了很多有效信息,比如 IP、时间等,在 Logstash 中可以配置过滤器 Filter 对采集到的数据进行过滤处理,Logstash 中有大量的插件可以供我们使用。
1 查看 Logstash 已经安装的插件 2 bin/logstash-plugin listGrok 插件 Grok 是一种将非结构化日志解析为结构化的插件。这个工具非常适合用来解析系统日志、 Web 服务器日志、 MySQL 或者是任意其他的日志格式。
https://www.elastic.co/guide/en/logstash/8.14/plugins-filters-grok.htmlGrok 语法 Grok 是通过模式匹配的方式来识别日志中的数据,可以把 Grok 插件简单理解为升级版本的正则表达式。
它拥有更多的模式,默认 Logstash 拥有 120 个模式。如果这些模式不满足我们解析日志的需求,我们可以直接使用正则表达式来进行匹配。
grok 模式的语法是:
1 %{SYNTAX:SEMANTIC}SYNTAX(语法)指的是 Grok 模式名称,SEMANTIC(语义)是给模式匹配到的文本字段名。例如:
1 %{NUMBER:duration} %{IP:client}2 duration 表示:匹配一个数字,client 表示匹配一个 IP 地址。

默认在 Grok 中,所有匹配到的的数据类型都是字符串,如果要转换成 int 类型(目前只支持 int 和 float),可以这样:%{NUMBER:duration:int} %{IP:client}常用的 Grok 模式 https://help.aliyun.com/document_detail/129387.html?scm=20140722.184.2.173 用法 1 filter {2 grok {3 match => { "message" => "%{IP:client} %{WORD:method} %{URIPATHPARAM:request} %{NUMBER:bytes} %{NUMBER:duration}" }4 }5 }比如,tomacat 日志 1 192.168.65.103 - - [23/Jun/2022:22:37:23 +0800] "GET /docs/images/docs-stylesheet.cssHTTP/1.1" 200 5780 解析后的字段字段名 说明 client IP 浏览器端 IPtimestamp 请求的时间戳 method 请求方式(GET/POST)
uri 请求的链接地址 status 服务器端响应状态 length 响应的数据长度 grok 模式

1 %{IP:ip} - - \[%{HTTPDATE:date}\] \"%{WORD:method} %{PATH:uri} %{DATA:protocol}\" %{INT:status} %{INT:length}为了方便测试,我们可以使用 Kibana 来进行 Grok 开发:
修改 Logstash 配置文件 1 vim config/logstash-console.conf23 input {4 beats {5 port => 50446 }7 }89 filter {10 grok {11 match => {12 "message" => "%{IP:ip} - - \[%{HTTPDATE:date}\] \"%{WORD:method} %{PATH:uri} %{DATA:protocol}\" %{INT:status:int} %{INT:length:int}"
13 }14 }15 }1617 output {18 stdout {19 codec => rubydebug20 }21 }启动 logstash 测试 1 bin/logstash -f config/logstash-console.conf --config.reload.automaticmutate 插件使用 mutate 插件过滤掉不需要的字段

1 mutate {2 enable_metric => "false"
3 remove_field => ["message", "log", "tags", "input", "agent", "host", "ecs","@version"]4 }Date 插件要将日期格式进行转换,我们可以使用 Date 插件来实现。该插件专门用来解析字段中的日期,官方说明文档:
https://www.elastic.co/guide/en/logstash/8.14/plugins-filters-date.html 用法如下:
将 date 字段转换为「年月日 时分秒」格式。默认字段经过 date 插件处理后,会输出到@timestamp 字段,所以,我们可以通过修改 target 属性来重新定义输出字段。
1 date {2 match => ["date","dd/MMM/yyyy:HH:mm:ss Z","yyyy-MM-dd HH:mm:ss"]3 target => "date"
4 }filter 完整的配置测试效果
3) 输出到 Elasticsearch 指定索引 index 来指定索引名称,默认输出的 index 名称为:logstash-%{+yyyy.MM.dd}。但注意,要在 index 中使用时间格式化,filter 的输出必须包含 @timestamp 字段,否则将无法解析日期。

1 output {2 elasticsearch {3 index => "tomcat_web_log_%{+YYYY-MM}"
4 hosts => ["http://localhost:9200"]5 user => "elastic"
6 password => "123456"
7 }8 stdout{9 codec => rubydebug10 }11 }注意:index 名称中,不能出现大写字符完整的 Logstash 配置文件

1 vim config/logstash-tomcat-es.conf23 input {4 beats {5 port => 50446 }7 }89 filter {10 grok {11 match => {12 "message" => "%{IP:ip} - - \[%{HTTPDATE:date}\] \"%{WORD:method} %{PATH:uri} %{DATA:protocol}\" %{INT:status:int} %{INT:length:int}"
13 }14 }15 mutate {16 enable_metric => "false"
17 remove_field => ["message", "log", "tags", "input", "agent", "host", "ecs","@version"]18 }19 date {20 match => ["date","dd/MMM/yyyy:HH:mm:ss Z","yyyy-MM-dd HH:mm:ss"]21 target => "date"
22 }23 }2425 output {26 stdout {27 codec => rubydebug28 }29 elasticsearch {30 index => "tomcat_web_log_%{+YYYY-MM}"
31 hosts => ["http://localhost:9200"]32 user => "elastic"
33 password => "123456"
34 }35 }启动 logstash

1 bin/logstash -f config/logstash-tomcat-es.conf --config.reload.automatic 查询 es 中是否有数据 4)通过 Kibana 分析微服务日志在 kibana 中,创建一个数据视图,创建完成后可以看到索引的相关详细信息点击 Discover,选择刚刚创建的数据视图筛选出 status 为 403 的日志
5. 微服务整合 ELK 实现日志采集与分析实战实现思路分析 Spring Boot 应用输出日志到 ELK 的流程如下图所示:
实现步骤:
1. Spring Boot 应用产生日志数据,使用 Logback 日志框架记录日志。
2. Logstash 作为日志收集器,接收 Spring Boot 应用发送的日志数据。
3. Logstash 解析和过滤日志数据,可能会对其进行格式化和处理。
4. 处理后的日志数据被发送到 Elasticsearch,Elasticsearch 将日志数据存储在分布式索引中。
5. Kibana 连接到 Elasticsearch,可以查看存储在 Elasticsearch 中的日志数据。
微服务整合 Logstash 实现日志采集 1)使用 logstash 日志插件引入依赖 1 <dependency>2 <groupId>net.logstash.logback</groupId>3 <spanrtifactId>logstash-logback-encoder</artifactId>4 <version>6.3</version>5 </dependency>

2)logback-spring.xml 中添加 logstash 配置 1 <?xml version="1.0" encoding="UTF-8"?>2 <configuration debug="false">3 <property name="LOG_HOME" value="logs/elk-demo.log" />4 <spanppender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">5 <encoder class="ch.qos.logback.classic.encoder.PatternLayoutEncoder">6 <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{50} %msg%n</pattern>7 </encoder>8 </appender>910 <spanppender name="logstash"
class="net.logstash.logback.appender.LogstashTcpSocketAppender">11 <destination>192.168.65.211:4560</destination>12 <encoder class="net.logstash.logback.encoder.LogstashEncoder" >13 <customFields>{"appname": "elk-demo"}</customFields>14 </encoder>15 </appender>16 <!-- 日志输出级别 -->17 <root level="INFO">18 <spanppender-ref ref="STDOUT" />19 <spanppender-ref ref="logstash" />20 </root>21 </configuration>3)添加 elk-demo.conf 配置,启动 logstash

1 vim config/elk-demo.conf23 input {4 tcp {5 host => "0.0.0.0"
6 port => "4560"
7 mode => "server"
8 codec => json_lines9 }10 stdin {}11 }12 filter {1314 }15 output {16 stdout {17 codec => rubydebug18 }19 elasticsearch {20 hosts => ["127.0.0.1:9200"]21 index => "%{[appname]}-%{+YYYY.MM.dd}"
22 }23 }24 启动 logstash1 # 后台启动 2 bin/logstash -f config/elk-demo.conf4)测试调用 springboot 应用提供的接口,logstash 控制台是否正常打印日志在 kibana 中查看 elk-demo 开头的索引是否存在通过 Kibana 分析微服务日志创建 demo-elk-*的数据视图

在 Discover 中查看日志数据
