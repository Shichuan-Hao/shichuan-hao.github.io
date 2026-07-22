---


title: "ElasticSearch高可用集群架构实战"
description: "ES 集群架构的优势: 提高系统的可用性: 在 ES 集群中,即使部分节点停止服务,整个集群的服务也不会受到影响,因为数据和索引操作可以在剩余的节点上继续进行。"
author: hsc
date: 2024-09-07 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Redis', 'ElasticSearch']
toc: true


---

### 1. 为什么要使用 ES 集群架构分布式系统的可用性与扩展性高可用性服务可用性——允许有节点停止服务数据可用性——部分节点丢失,不会丢失数据可扩展性请求量提升/数据的不断增长(将数据分布到所有节点上)
ES 集群架构的优势:
提高系统的可用性: 在 ES 集群中,即使部分节点停止服务,整个集群的服务也不会受到影响,因为数据和索引操作可以在剩余的节点上继续进行。
存储的水平扩容: ES 集群支持通过增加新的节点来扩展存储容量,实现数据的水平扩展,这样可以有效应对数据量的增长。
2. 核心概念集群一个集群可以有一个或者多个节点不同的集群通过不同的名字来区分,默认名字“elasticsearch“通过配置文件修改,或者在命令行中 -E cluster.name=es-cluster 进行设定

节点节点是一个 Elasticsearch 的实例本质上就是一个 JAVA 进程一台机器上可以运行多个 Elasticsearch 进程,但是生产环境一般建议一台机器上只运行一个 Elasticsearch 实例每一个节点都有名字,通过配置文件配置,或者启动时候 -E node.name=node1 指定每一个节点在启动之后,会分配一个 UID,保存在 data 目录下分片(Primary Shard & Replica Shard)
主分片(Primary Shard)
用以解决数据水平扩展的问题。通过主分片,可以将数据分布到集群内的所有节点之上一个分片是一个运行的 Lucene 的实例主分片数在索引创建时指定,后续不允许修改,除非 Reindex 副本分片(Replica Shard)
用以解决数据高可用的问题。 副本分片是主分片的拷贝副本分片数,可以动态调整增加副本数,还可以在一定程度上提高服务的可用性(读取的吞吐)
1 # 指定索引的主分片和副本分片数 2 PUT /blogs3 {4 "settings": {5 "number_of_shards": 3,6 "number_of_replicas": 17 }8 }分片架构集群 statusGreen: 主分片与副本都正常分配 Yellow: 主分片全部正常分配,有副本分片未能正常分配 Red: 有主分片未能分配。例如,当服务器的磁盘容量超过 85%时,去创建了一个新的索引

1 #查看集群的健康状况 2 GET _cluster/healthCAT API 查看集群信息 12 GET /_cat/nodes?v #查看节点信息 3 GET /_cat/health?v #查看集群当前状态:红、黄、绿 4 GET /_cat/shards?v #查看各 shard 的详细情况 5 GET /_cat/shards/{index}?v #查看指定分片的详细情况 6 GET /_cat/master?v #查看 master 节点信息 7 GET /_cat/indices?v #查看集群中所有 index 的详细信息 8 GET /_cat/indices/{index}?v #查看集群中指定 index 的详细信息
3. 搭建三节点 ES 集群建议:每台机器先安装好单节点 ES 进程,并能正常运行,再修改配置,搭建集群参考课程:ElasticSearch 快速安装上手 IP ES 节点名
192.168.65.213node-1192.168.65.207node-2192.168.65.208 node-3ES 集群搭建步骤 1)系统环境准备安装版本:elasticsearch8.14.3 操作系统: CentOS7 切换到 root 用户,创建用户 es

1 adduser es2 passwd es 修改/etc/hosts1 vim /etc/hosts2 192.168.65.213 es-node13 192.168.65.207 es-node24 192.168.65.208 es-node3 关闭防火墙 1 #查看防火墙状态 2 systemctl status firewalld3 #关闭防火墙 4 systemctl stop firewalld5 systemctl disable firewalld 在生产模式下,服务启动会触发 ES 的引导检查或者叫启动检查(bootstrap checks),所谓引导检查就是在服务启动之前对一些重要的配置项进行检查,检查其配置值是否是合理的。引导检查包括对 JVM 大小、内存锁、虚拟内存、最大线程数、集群发现相关配置等相关的检查,如果某一项或者几项的配置不合理,ES 会拒绝启动服务。
[1]: max file descriptors [4096] for elasticsearch process is too low, increase to at least [65536]ES 因为需要大量的创建索引文件,需要大量的打开系统的文件,所以我们需要解除 linux 系统当中打开文件最大数目的限制,不然 ES 启动就会抛错

1 #切换到 root 用户 2 vim /etc/security/limits.conf34 末尾添加如下配置:
5 * soft nofile 655366 * hard nofile 655367 * soft nproc 40968 * hard nproc 4096[2]: max number of threads [1024] for user [es] is too low, increase to at least [4096]无法创建本地线程问题,用户最大可创建线程数太小 1 vim /etc/security/limits.d/20-nproc.conf23 改为如下配置:
4 * soft nproc 4096[3]: max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144]最大虚拟内存太小,调大系统的虚拟内存 1 vim /etc/sysctl.conf2 追加以下内容:
3 vm.max_map_count=2621444 保存退出之后执行如下命令:
5 sysctl -p2)切换到 es 用户,修改 elasticsearch.yml

1 # 指定集群名称 3 个节点必须一致 2 cluster.name: es-cluster3 #指定节点名称,每个节点名字唯一 4 node.name: node-15 # 绑定 ip,开启远程访问,可以配置 0.0.0.06 network.host: 0.0.0.07 #指定 web 端口 8 #http.port: 92009 #指定 tcp 端口 10 #transport.tcp.port: 930011 #用于节点发现,一般配置集群的候选主节点 12 discovery.seed_hosts: ["es-node1", "es-node2", "es-node3"]13 #7.0 新引入的配置项,集群引导节点。指定集群初次选举中用到的具有主节点资格的节 14 #点称为集群引导节点,只在第一次形成集群时需要 15 #该选项配置为 node.name 的值,指定可以初始化集群节点的名称 16 cluster.initial_master_nodes: ["node-1","node-2","node-3"]17 #解决跨域问题 18 http.cors.enabled: true19 http.cors.allow-origin: "*"
20 #初学者建议关闭 security 安全认证 21 xpack.security.enabled: false 三个节点配置如下:

1 #192.168.65.213 的配置 2 cluster.name: es-cluster3 node.name: node-14 network.host: 0.0.0.05 discovery.seed_hosts: ["es-node1", "es-node2", "es-node3"]6 cluster.initial_master_nodes: ["node-1","node-2","node-3"]7 http.cors.enabled: true8 http.cors.allow-origin: "*"
9 xpack.security.enabled: false1011 #192.168.65.207 的配置 12 cluster.name: es-cluster13 node.name: node-314 network.host: 0.0.0.015 discovery.seed_hosts: ["es-node1", "es-node2", "es-node3"]16 cluster.initial_master_nodes: ["node-1","node-2","node-3"]17 http.cors.enabled: true18 http.cors.allow-origin: "*"
19 xpack.security.enabled: false2021 #192.168.65.208 的配置 22 cluster.name: es-cluster23 node.name: node-224 network.host: 0.0.0.025 discovery.seed_hosts: ["es-node1", "es-node2", "es-node3"]26 cluster.initial_master_nodes: ["node-1","node-2","node-3"]27 http.cors.enabled: true28 http.cors.allow-origin: "*"
29 xpack.security.enabled: false
3) 启动每个节点的 ES 服务

1 # 注意:如果运行过单节点模式,需要删除 data 目录, 否则会导致无法加入集群 2 rm -rf data3 #安装 ik 分词器 4 bin/elasticsearch-plugin install https://release.infinilabs.com/analysisik/stable/elasticsearch-analysis-ik-8.14.3.zip5 # 启动 ES 服务 6 bin/elasticsearch -d4)验证集群 http://192.168.65.213:9200/_cat/nodes?pretty 安装 Cerebro 客户端 Cerebro 介绍 Cerebro 可以查看分片分配和通过图形界面执行常见的索引操作。 完全开源,并且它允许添加用户,密码或 LDAP 身份验证问网络界面。
Cerebro 基于 Scala 的 Play 框架编写,用于后端 REST 和 Elasticsearch 通信。 它使用通过 AngularJS 编写的单页应用程序(SPA)前端。
项目网址:https://github.com/lmenezes/cerebro 安装 Cerebro 下载地址:https://github.com/lmenezes/cerebro/releases/download/v0.9.4/cerebro-0.9.4.zip 运行 cerebro1 cerebro-0.9.4/bin/cerebro23 #后台启动 4 nohup bin/cerebro &访问:http://192.168.65.207:9000/输入 ES 集群节点:http://192.168.65.207:9200,建立连接:
安装 kibana1)修改 kibana 配置

1 vim config/kibana.yml23 server.host: "192.168.65.213"
4 i18n.locale: "zh-CN"
2)运行 Kibana 提示:Kibana 对外的 tcp 端口是 5601,使用 netstat -tunlp|grep 5601 即可查看进程 1 #后台启动 2 nohup bin/kibana &34 #查询 kibana 进程 5 netstat -tunlp | grep 5601 访问 Kibana: http://192.168.65.213:5601/
4. ES 集群安全认证参考文档:https://www.elastic.co/guide/en/elasticsearch/reference/8.14/configuring-stack-security.html 近几年来,ES 数据泄露事件频发给国内各行业用户敲响了数据安全的警钟。比如:
2019 年发生的 ES 数据泄露事件,泄露包括 27 亿个电子邮件地址,其中 10 亿个密码是以简单的明文存储,涉及国内多家互联网公司。
2021 年 Group-IB 报告显示,网络上暴露的 ES 实例超过 10 万个,约占 2021 年暴露数据库总数的 30% 。
2022 年漫画阅读平台 Mangatoon 遭遇数据泄露,黑客从不安全的 ES 数据库中窃取了属于 2300 万用户帐户的信息。
2022 年阿里巴巴遭受了一次重大数据泄露,涉及客户数据包括:姓名、电话号、身份证号、居住地址等信息共计 23TB。
ES 敏感信息泄露的原因 Elasticsearch 在安装后,不提供任何形式的安全防护不合理的配置导致公网可以访问 ES 集群。比如在 elasticsearch.yml 文件中,server.host 配置为 0.0.0.0

基于 Security 的安全认证 ES 8 默认启动了 Security。ES 8.x 第一次启动之后会输出以下信息,此时服务已经启动成功了。
比如 windows 下第一次启动 ES,会输出如下信息:
1 2 -> Elasticsearch security features have been automatically configured!
3 -> Authentication is enabled and cluster connections are encrypted.45 -> Password for the elastic user (reset with `bin/elasticsearch-reset-password -uelastic`):
6 GFDGvf9kEuSaZrr=3eLt78 -> HTTP CA certificate SHA-256 fingerprint:
9 f76d093b63225ea0866b4fcc1766293caf05c6ae152a9e95e3149afd74be5fa81011 -> Configure Kibana to use this cluster:
12 * Run Kibana and click the configuration link in the terminal when Kibana starts.13 * Copy the following enrollment token and paste it into Kibana in your browser (validfor the next 30 minutes):
14eyJ2ZXIiOiI4LjE0LjAiLCJhZHIiOlsiMTcyLjE5LjE3Ni4xOjkyMDAiXSwiZmdyIjoiZjc2ZDA5M2I2MzIyNWVhMDg2NmI0ZmNjMTc2NjI5M2NhZjA1YzZhZTE1MmE5ZTk1ZTMxNDlhZmQ3NGJlNWZhOCIsImtleSI6IjI1VW1jSkVCaXNrRWNrdjRYMXVzOlRWQjlMS2RwUkRTT2hjUmhWVGF2cUEifQ==1516 -> Configure other nodes to join this cluster:
17 * On this node:
18 - Create an enrollment token with `bin/elasticsearch-create-enrollment-token -snode`.19 - Uncomment the transport.host setting at the end of config/elasticsearch.yml.20 - Restart Elasticsearch.21 * On other nodes:
22 - Start Elasticsearch with `bin/elasticsearch --enrollment-token <token>`, using theenrollment token that you generated.23 首次启动 Elasticsearch 时,会自动进行以下安全配置:
为传输层和 HTTP 层生成 TLS 证书和密钥。
TLS 配置设置被写入 elasticsearch.yml。

为 elastic 用户生成密码。
为 Kibana 生成一个注册令牌。
修改账号密码在 ES 8.x 版本以后,elasticsearch-setup-passwords 设置密码的工具已经被弃用删除,此命令为 7.x 之前第一次生成密码时使用,8.x 在第一次启动的时候会自动生密码。
如果需要修改账户密码,需进行以下操作:
1 #为 elastic 账号自动生成新密码,输出至控制台 2 bin/elasticsearch-reset-password -u elastic3 #手工指定用户的新密码 4 bin/elasticsearch-reset-password -u elastic -i5 #指定服务地址和账户名 6 bin/elasticsearch-reset-password --url "https://ip:9200" -u elastic -i 验证服务状态访问服务在 7.x 的版本是通过如下地址访问 ES 服务:http://localhost:9200/但是在 8.x 的版本访问会看到如下页面:
原因解释这是正常现象,因为 Elastic 8 默认开启了 SSL,将默认配置项由 true 改为 false 即可推荐做法关闭 SSL 虽然可以访问服务了,但这本质上是在规避问题而非解决问题,更推荐的做法是使用 https 协议进行访问:
https://localhost:9200/,此时如果你的浏览器版本是比较新的版本会出现以下弹窗提示,即:

输入账号密码验证:
三节点 ES 集群增加安全认证 node-1 增加安全认证 1)停止集群所有节点,并删除 data 目录 2)以 node-1 为例,修改 config/elasticsearch.yml 配置文件
3) 删除 data 目录(不删除会报错),然后启动 node-1 节点 1 bin/elasticsearch -d 查看 elasticsearch.yml 配置文件,多出很多 security 相关配置
4) 修改用户 elastic 的密码 1 bin/elasticsearch-reset-password -u elastic -i5)测试,访问 https://192.168.65.213:9200/输入用户名密码 node-2 和 node-3 加入集群 1)修改 node-2 和 node-3 的 elasticsearch.yml 配置文件 2)向集群中加入新节点默认情况下,要向集群中添加新节点,需要通过令牌来完成节点之间的通信 2.1)在 node-1 中执行下面的命令为新节点生成注册令牌 1 bin/elasticsearch-create-enrollment-token -s node2.2)以 node-2 为例,启动 node-2 节点,并带上注册令牌

1 bin/elasticsearch --enrollment-token <enrollment-token> -d 同上,启动 node-3 节点,并带上注册令牌注意:只有第一次加入集群需要带上注册令牌,后续启动不需要 2.3)通过 head 插件查看集群部署 Kibana1)进入 ES 目录,生成 kibana 的注册令牌 1 bin/elasticsearch-create-enrollment-token -s kibana
2) 进入 kibana 目录,通过下面的命令注册 Kibana1 bin/kibana-setup --enrollment-token <enrollment-token>3)直接启动 Kibana 服务 1 nohup bin/kibana &然后我们访问 Kibana:http://192.168.65.213:5601/输入用户名 elastic 和密码,进入 kibana 主界面部署 cerebro1)修改配置文件

1 vim conf/application.conf23 hosts = [4 {5 host = "https://192.168.65.207:9200"
6 name = "es-cluster"
7 auth = {8 username = "elastic"
9 password = "123456"
10 }11 }12 ]13
2) 启动 cerebro 服务 1 nohup bin/cerebro -Dplay.ws.ssl.loose.acceptAnyCertificate=true &访问:http://192.168.65.207:9000/
