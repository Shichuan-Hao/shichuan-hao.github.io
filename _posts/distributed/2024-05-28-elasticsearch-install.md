---



title: "ElasticSearch快速安装上手"
description: "下载 ElasticSearch 并解压下载地址: 目录结构如下: 目录 描述脚本文件,包括启动 elasticsearch,安装插件"
author: hsc
date: 2024-05-28 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Redis', 'ElasticSearch']
toc: true



---

### 1. ElasticSearch 安装和简单配置温馨提示:初学者建议直接安装 windows 版本的 ElasticSearch 安装文档:https://www.elastic.co/guide/en/elasticsearch/reference/8.14/install-elasticsearch.htmlwindows 安装 ElasticSearch
1)下载 ElasticSearch 并解压下载地址: https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.14.3-windows-x86_64.zipElasticSearch 目录结构如下:
目录 描述脚本文件,包括启动 elasticsearch,安装插件,bin 运行统计数据等配置文件目录,如 elasticsearch 配置、角色配 config 置、 jvm 配置等。
jdk 7.x 以后特有,自带的 java 环境默认的数据存放目录,包含节点、分片、索引、 data 文档的所有数据,生产环境需要修改。
lib elasticsearch 依赖的 Java 类库 logs 默认的日志文件存储路径,生产环境需要修改。
包含所有的 Elasticsearch 模块,如 Cluster、modulesDiscovery、Indices 等。
plugins 已安装插件目录 2)配置 JDK 环境 ES 比较耗内存,建议虚拟机 4G 或以上内存,jvm1g 以上的内存分配运行 Elasticsearch,需安装并配置 JDK。各个版本对 Java 的依赖 https://www.elastic.co/support/matrix#matrix_jvm7.0 开始,内置了 Java 环境。 ES 的 JDK 环境变量生效的优先级配置顺序 ES_JAVA_HOME>ES_HOMEES_JAVA_HOME:这个环境变量用于指定 Elasticsearch 使用的 Java 运行时环境的路径。在启动 Elasticsearch 时,它会检查 ES_JAVA_HOME 环境变量并使用其中的 Java 路径。

ES_HOME:这个环境变量指定 Elasticsearch 的安装路径。它用于定位 Elasticsearch 的配置文件、插件和其他相关资源。设置 ES_HOME 环境变量可以让您在命令行中更方便地访问 Elasticsearch 的目录结构和文件。
可以参考 ES 的环境文件 elasticsearch-env.batwindows 下,设置 ES_JAVA_HOME 和 ES_HOME 的环境变量 3)配置 ElasticSearch 编辑 config/elasticsearch.yml 文件关闭 security 安全认证 ES 8 默认是开启 Security 的,初学者便于快速上手,可以关闭 Security。
编辑 config/elasticsearch.yml 文件 4)启动 ElasticSearch 服务 4.1)解决启动日志乱码问题 1 #打开 config/jvm.options 文件—>末尾添加 2 -Dfile.encoding=GBK4.2)进入 bin 目录,点击 elasticsearch.bat 文件启动 ES 服务注意:9300 端口为 Elasticsearch 集群间组件的通信端口,9200 端口为浏览器访问的 http 协议 RESTful 端口。
打开浏览器(推荐使用谷歌浏览器),输入地址:http://localhost:9200,测试结果 linux 安装 ElasticSearch1)环境准备准备 linux 安装环境:
linux 系统 IP 操作用户 centos7 192.168.65.47 fox 注意:ES 不允许使用 root 账号启动服务,如果你当前账号是 root,则需要创建一个专有账户

1 #为 elaticsearch 创建用户 2 adduser fox3 passwd fox2)通过 fox 用户登录,下载 ElasticSearch 并解压 1 #centos7 通过 fox 用户进入 2 wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.14.3-linuxx86_64.tar.gz3 tar -xzf elasticsearch-8.14.3-linux-x86_64.tar.gz4 cd elasticsearch-8.14.3/注意: 如果在 root 用户下解压了 ES 安装包,可以通过下面的命令将 ES 安装包的所有者和组更改为 fox 用户 1 # 在 root 用户下操作 2 chown -R fox:fox elasticsearch-8.14.33)配置 JDK 环境(可选)
1 # 进入 fox 用户主目录,比如/home/fox 目录下,设置用户级别的环境变量 2 vim .bash_profile3 #设置 ES_JAVA_HOME 和 ES_HOME 的路径 4 export ES_JAVA_HOME=/home/fox/elasticsearch-8.14.3/jdk/5 export ES_HOME=/home/fox/elasticsearch-8.14.36 #执行以下命令使配置生效 7 source .bash_profile4)配置 ElasticSearch 修改 config/elasticsearch.yml 配置文件

1 vim elasticsearch.yml23 #配置节点对外提供服务的地址以及集群内通信的 ip 地址,默认为回环地址 127.0.0.1 和[::1]4 #配置为 0.0.0.0 开启远程访问支持 5 network.host: 0.0.0.06 #指定节点为单节点,可以绕过引导检查 初学者建议设置为此开发模式 7 discovery.type: single-node89 #初学者建议关闭 security 安全认证 10 xpack.security.enabled: false 开发模式和生产模式开发模式:开发模式是默认配置(未配置集群发现设置),如果用户只是出于学习目的,而引导检查会把很多用户挡在门外,所以 ES 提供了一个设置项 discovery.type=single-node。此项配置为指定节点为单节点,可以绕过引导检查。
生产模式:当用户修改了有关集群的相关配置会触发生产模式,在生产模式下,服务启动会触发 ES 的引导检查或者叫启动检查(bootstrap checks),所谓引导检查就是在服务启动之前对一些重要的配置项进行检查,检查其配置值是否是合理的。引导检查包括对 JVM 大小、内存锁、虚拟内存、最大线程数、集群发现相关配置等相关的检查,如果某一项或者几项的配置不合理,ES 会拒绝启动服务,并且在开发模式下的某些警告信息会升级成错误信息输出。引导检查十分严格,之所以宁可拒绝服务也要阻止用户启动服务是为了防止用户在对 ES 的基本使用不了解的前提下启动服务而导致的后期性能问题无法解决或者解决起来很麻烦。因为一旦服务以某种不合理的配置启动,时间久了之后可能会产生较大的性能问题,但此时集群已经变得难以维护和扩展,ES 为了避免这种情况而做出了引导检查的设置,本来在开发模式下为警告的启动日志会升级为报错(Error)。这种设定虽然增加了用户的使用门槛,但是避免了日后产生更大的问题。
ElasticSearch 常用配置参数参考文档:https://www.elastic.co/guide/en/elasticsearch/reference/8.14/important-settings.htmlcluster.name 当前节点所属集群名称,多个节点如果要组成同一个集群,那么集群名称一定要配置成相同。默认值 elasticsearch,生产环境建议根据 ES 集群的使用目的修改成合适的名字。不要在不同的环境中重用相同的集群名称,否则,节点可能会加入错误的集群。
node.name 当前节点名称,默认值当前节点部署所在机器的主机名,所以如果一台机器上要起多个 ES 节点的话,需要通过配置该属性明确指定不同的节点名称。
path.data

配置数据存储目录,比如索引数据等,默认值 $ES_HOME/data,生产环境下强烈建议部署到另外的安全目录,防止 ES 升级导致数据被误删除。
path.logs 配置日志存储目录,比如运行日志和集群健康信息等,默认值 $ES_HOME/logs,生产环境下强烈建议部署到另外的安全目录,防止 ES 升级导致数据被误删除。
bootstrap.memory_lock 配置 ES 启动时是否进行内存锁定检查,默认值 true。
ES 对于内存的需求比较大,一般生产环境建议配置大内存,如果内存不足,容易导致内存交换到磁盘,严重影响 ES 的性能。所以默认启动时进行相应大小内存的锁定,如果无法锁定则会启动失败。
非生产环境可能机器内存本身就很小,能够供给 ES 使用的就更小,如果该参数配置为 true 的话很可能导致无法锁定内存以致 ES 无法成功启动,此时可以修改为 false。
network.host 节点对外提供服务的地址以及集群内通信的 ip 地址,默认值为当前节点所在机器的本机回环地址 127.0.0.1 和[::1],这就导致默认情况下只能通过当前节点所在主机访问当前节点。
http.port 配置当前 ES 节点对外提供服务的 http 端口,默认 9200transport.port:
节点通信端口号,默认 9300discovery.seed_hosts 配置参与集群节点发现过程的主机列表,说白一点就是集群中所有节点所在的主机列表,可以是具体的 IP 地址,也可以是可解析的域名。
cluster.initial_master_nodes 配置 ES 集群初始化时参与 master 选举的节点名称列表,必须与 node.name 配置的一致。 ES 集群首次构建完成后,应该将集群中所有节点的配置文件中的 cluster.initial_master_nodes 配置项移除,重启集群或者将新节点加入某个已存在的集群时切记不要设置该配置项。
5) 配置 JVM 参数(可选)
修改 config/jvm.options 配置文件,调整 jvm 堆内存大小 1 vim jvm.options2 -Xms4g3 -Xmx4g 配置的建议:
Xms(JVM 启动时分配的最小堆内存)和 Xms(JVM 在运行过程中能够分配的最大堆内存)设置成—样 Xmx 不要超过机器内存的 50%

不要超过 30GB - https://www.elastic.co/cn/blog/a-heap-of-trouble6)启动 ElasticSearch 服务 1 #注意:es 默认不能用 root 用户启动 2 #fox 用户下启动 ES3 bin/elasticsearch45 # -d 后台启动 6 bin/elasticsearch -d 打开本地浏览器(推荐使用谷歌浏览器),输入地址:http://192.168.65.47:9200 (换成 linux 环境对应的 ip),测试结果如下:
生产模式启动 ES 服务常见错误总结如果不配置 discovery.type: single-node 绕过引导检查,ES 服务启动可能会抛出异常,比如提示如下:
[1]: max file descriptors [4096] for elasticsearch process is too low, increase to at least [65536]ES 因为需要大量的创建索引文件,需要大量的打开系统的文件,所以我们需要解除 linux 系统当中打开文件最大数目的限制,不然 ES 启动就会抛错 1 #切换到 root 用户 2 vim /etc/security/limits.conf34 末尾添加如下配置:
5 * soft nofile 655366 * hard nofile 655367 * soft nproc 40968 * hard nproc 4096[2]: max number of threads [1024] for user [es] is too low, increase to at least [4096]无法创建本地线程问题,用户最大可创建线程数太小

1 vim /etc/security/limits.d/20-nproc.conf23 改为如下配置:
4 * soft nproc 4096[3]: max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144]最大虚拟内存太小,调大系统的虚拟内存 1 vim /etc/sysctl.conf2 追加以下内容:
3 vm.max_map_count=2621444 保存退出之后执行如下命令:
5 sysctl -p[4]: the default discovery settings are unsuitable for production use; at least one of[discovery.seed_hosts, discovery.seed_providers, cluster.initial_master_nodes] must be configured 缺少默认配置,至少需要配置 discovery.seed_hosts/discovery.seed_providers、discovery.seed_providers、cluster.initial_master_nodes 中的一个参数.discovery.seed_hosts: 集群主机列表 discovery.seed_providers: 基于配置文件配置集群主机列表 cluster.initial_master_nodes: 启动时初始化的参与选主的 node,生产环境必填 1 vim config/elasticsearch.yml2 #添加配置 3 discovery.seed_hosts: ["127.0.0.1"]4 cluster.initial_master_nodes: ["node-1"]56 #或者指定配置单节点(开发模式 会绕过引导检查)
7 discovery.type: single-node
2. 安装 ES 浏览器插件

插件名称 插件图标 功能介绍 下载地址 Elasticsearch Head image 方便查看集群节点数据 Chrome 下载方便管理和索引、分片支持同时连接多集群 Github 下载 Elasticsearch Tools image-1677761829554 方便查看节点资源占用 Chrome 下载可执行查询语句 Elasticvue image-1677761848792 功能强大对国人友好 Chrome 下载 Edge 下载 Elasticvue 界面如下:
3. 可视化客户端 Kibana 安装 Kibana 是一个开源分析和可视化平台,旨在与 Elasticsearch 协同工作。
参考文档:https://www.elastic.co/guide/en/kibana/8.14/get-started.html 下载地址:https://www.elastic.co/cn/downloads/past-releases#kibana1)下载并解压缩 Kibana1 #windows2 https://artifacts.elastic.co/downloads/kibana/kibana-8.14.3-windows-x86_64.zip3 #linux4 wget https://artifacts.elastic.co/downloads/kibana/kibana-8.14.3-linux-x86_64.tar.gz5 tar -zxvf kibana-8.14.3-linux-x86_64.tar.gz6 cd kibana-8.14.32)修改 Kibana.yml 配置文件

1 vim config/kibana.yml23 #指定 Kibana 服务器监听的端口号 4 server.port: 56015 #指定 Kibana 服务器绑定的主机地址 6 server.host: "0.0.0.0"
7 #指定 Kibana 连接到的 Elasticsearch 实例的访问地址 8 elasticsearch.hosts: ["http://localhost:9200"]9 #将 Kibana 的界面语言设置为简体中文 10 i18n.locale: "zh-CN"
3)运行 Kibanawindows 直接执行 kibana.batLinux 注意:kibana 也需要非 root 用户启动 1 #启动 kibana 服务 2 bin/kibana3 #后台启动,并将日志写入到 logs/kibana.log4 nohup bin/kibana > logs/kibana.log 2>&1 &56 #查询 kibana 进程 7 netstat -tunlp | grep 56014)访问 Kibana: http://localhost:5601cat API

1 /_cat/allocation #查看单节点的 shard 分配整体情况 2 /_cat/shards #查看各 shard 的详细情况 3 /_cat/shards/{index} #查看指定分片的详细情况 4 /_cat/master #查看 master 节点信息 5 /_cat/nodes #查看所有节点信息 6 /_cat/indices #查看集群中所有 index 的详细信息 7 /_cat/indices/{index} #查看集群中指定 index 的详细信息 8 /_cat/segments #查看各 index 的 segment 详细信息,包括 segment 名, 所属 shard, 内存(磁盘)占用大小, 是否刷盘 9 /_cat/segments/{index}#查看指定 index 的 segment 详细信息 10 /_cat/count #查看当前集群的 doc 数量 11 /_cat/count/{index} #查看指定索引的 doc 数量 12 /_cat/recovery #查看集群内每个 shard 的 recovery 过程.调整 replica。
13 /_cat/recovery/{index}#查看指定索引 shard 的 recovery 过程 14 /_cat/health #查看集群当前状态:红、黄、绿 15 /_cat/pending_tasks #查看当前集群的 pending task16 /_cat/aliases #查看集群中所有 alias 信息,路由配置等 17 /_cat/aliases/{alias} #查看指定索引的 alias 信息 18 /_cat/thread_pool #查看集群各节点内部不同类型的 threadpool 的统计信息,19 /_cat/plugins #查看集群各个节点上的 plugin 信息 20 /_cat/fielddata #查看当前集群各个节点的 fielddata 内存使用情况 21 /_cat/fielddata/{fields} #查看指定 field 的内存使用情况,里面传 field 属性对应的值 22 /_cat/nodeattrs #查看单节点的自定义属性 23 /_cat/repositories #输出集群中注册快照存储库 24 /_cat/templates #输出当前正在存在的模板信息
4. 安装中文分词插件 Elasticsearch 提供插件机制对系统进行扩展在线安装以安装 analysis-icu 这个分词插件为例 analysis-icu 功能:
基于 ICU(International Components for Unicode)库,提供高级的文本分析和处理功能。
支持多语言和复杂的 Unicode 文本处理。
包含 ICU 分词器(ICU Tokenizer)和 ICU 标准化过滤器(ICU Normalizer)。
analysis-icu 应用场景:

多语言文本分析,适用于处理各种语言的文本。
支持 Unicode 标准化和处理复杂字符。
提供高级的文本处理功能,如正则表达式替换、文本转换等。
1 #查看已安装插件 2 bin/elasticsearch-plugin list3 #安装插件 4 bin/elasticsearch-plugin install analysis-icu5 #删除插件 6 bin/elasticsearch-plugin remove analysis-icu 注意:安装和删除完插件后,需要重启 ES 服务才能生效。
测试分词效果 1 POST _analyze2 {3 "analyzer":"icu_analyzer",4 "text":"中华人民共和国"
5 }离线安装本地下载相应的插件,解压,然后手动上传到 elasticsearch 的 plugins 目录,然后重启 ES 实例就可以了。
比如 ik 中文分词插件:https://github.com/medcl/elasticsearch-analysis-ik 注意:ik 分词器插件和 ES 版本必须一一对应,否则会出现兼容性问题导致 ES 启动失败。
当前 ik 分词器插件最新版本还只支持到 ES8.4.1,而我们使用的 ES 版本是 8.14.3,安装后会出现兼容性问题。那如何解决?
可以从 https://release.infinilabs.com/analysis-ik/stable/ 下载 ES8.14.3 对应版本的分词器测试分词效果

1 #ES 的默认分词设置是 standard,会单字拆分 2 POST _analyze3 {4 "analyzer":"standard",5 "text":"中华人民共和国"
6 }78 #ik_smart:会做最粗粒度的拆 9 POST _analyze10 {11 "analyzer": "ik_smart",12 "text": "中华人民共和国"
13 }1415 #ik_max_word:会将文本做最细粒度的拆分 16 POST _analyze17 {18 "analyzer":"ik_max_word",19 "text":"中华人民共和国"
20 }21 创建索引时可以指定 IK 分词器作为默认分词器 1 # 创建索引,指定默认分词器 2 PUT /employee3 {4 "settings" : {5 "index" : {6 "analysis.analyzer.default.type": "ik_max_word"
7 }8 }9 }1011 #查看索引 setting 信息 12 GET /employee/_settings

也可以针对字段配置 IK 分词器

1 #创建索引 2 PUT /index3 # 指定 content 字段使用 ik 分词器 4 POST /index/_mapping5 {6 "properties": {7 "content": {8 "type": "text",9 "analyzer": "ik_max_word",10 "search_analyzer": "ik_smart"
11 }12 }13 }1415 #索引文档,也就是插入文档 16 POST /index/_create/117 {"content":"美国留给伊拉克的是个烂摊子吗"}1819 POST /index/_create/220 {"content":"公安部:各地校车将享最高路权"}2122 POST /index/_create/323 {"content":"中韩渔警冲突调查:韩警平均每天扣 1 艘中国渔船"}2425 POST /index/_create/426 {"content":"中国驻洛杉矶领事馆遭亚裔男子枪击 嫌犯已自首"}2728 #带高亮的查询 29 POST /index/_search30 {31 "query": {32 "match": {33 "content": "中国"
34 }35 },36 "highlight": {37 "pre_tags": [38 "<tag1>",39 "<tag2>"

40 ],41 "post_tags": [42 "</tag1>",43 "</tag2>"
44 ],45 "fields": {46 "content": {}47 }48 }49 }/index/_mapping 映射属性的解释:
"properties":这是一个包含字段定义的 JSON 对象。在这个例子中,它只包含了一个字段 content。
"content":这是索引中要定义的字段名。
"type": "text":指定 content 字段的数据类型为 text。在 Elasticsearch 中,text 类型用于全文搜索的文本字段,它可以被分词器(analyzer)处理成多个词条(tokens)用于索引和搜索。
"analyzer": "ik_max_word":指定在索引(写入)content 字段时使用的分词器为 ik_max_word。
ik_max_word 是 Elasticsearch 的 IK 分词器插件提供的一个分词器,它会对文本进行最细粒度的切分,以便尽可能多地捕获文本中的关键词,提高搜索的召回率。
"search_analyzer": "ik_smart":指定在搜索(查询)content 字段时使用的分词器为 ik_smart。
ik_smart 是 IK 分词器的另一种分词模式,它尝试对文本进行更智能的切分,以提高搜索的准确率。通过在索引和搜索时使用不同的分词器,可以在提高召回率的同时保持搜索的精度。
