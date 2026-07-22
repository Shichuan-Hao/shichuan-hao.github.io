---


title: "Mysql8.0高可用集群架构实战"
description: "Mysql8.0 高可用集群架构实战..."
author: hsc
date: 2020-12-08 00:00:00 +0800
categories: ['Java 后端', '性能调优']
tags: ['性能调优', 'MySQL', 'MySQL优化']
toc: true


---

Mysql8.0 高可用集群架构实战

MySQL InnoDB Cluster 官方文档:https://dev.mysql.com/doc/mysql-shell/8.0/en/mysql-innodb-cluster.html 基本概述 InnoDB Cluster 是 MySQL 官方实现高可用+读写分离的架构方案,其中包含以下组件 MySQL Group Replication,简称 MGR,是 MySQL 的主从同步高可用方案,包括数据同步及角色选举 Mysql Shell 是 InnoDB Cluster 的管理工具,用来创建和管理集群 Mysql Router 是业务流量入口,支持对 MGR 的主从角色判断,可以配置不同的端口分别对外提供读写服务,实现读写分离 MySQL Router 与组复制和 MySQL Shell 高度整合,只有将其与组复制和 MySQL Shell 共同使用,才能够称为 InnoDB Cluster。
集群架构

InnoDB Cluster 将三个 MySQL 数据库实例构成一个高可用集群。其中一个实例是具有读/写能力的主要成员,其他两个实例是具有只读能力的次要成员。组复制将数据从主要成员复制到次要成员。 MySQLRouter 将客户端应用程序连接到集群的主要成员。
搭建一主两从 InnoDB 集群
1. 安装 3 个数据库实例参考:Docker 安装 MySQL8.0 可以利用 docker 快速部署 3 个 MySQL 实例主机名(角色) server_id 宿主机 IP 容器固定 IP DB Portmgr-
1 192.168.65.223 172.19.0.10 3321>3306node1(primary)
mgrnode2(Secondary 2 192.168.65.223 172.19.0.11 3322>3306)
mgr- 3 192.168.65.223 172.19.0.12 3323>3306

node3(Secondary)
1 # 创建组复制的网络 保证三个 mysql 容器之间可以通过容器名访问 2 docker network create --driver bridge --subnet 172.19.0.0/24 --gateway 172.19.0.1 mgrnetwork34 mkdir -p /mysql/mgr/node1/data /mysql/mgr/node1/conf /mysql/mgr/node1/log5 mkdir -p /mysql/mgr/node2/data /mysql/mgr/node2/conf /mysql/mgr/node2/log6 mkdir -p /mysql/mgr/node3/data /mysql/mgr/node3/conf /mysql/mgr/node3/log78 #以 mgr-node1 配置为例,创建/mysql/mgr/node1/conf/custom.cnf,添加以下配置:
9 vim /mysql/mgr/node1/conf/custom.cnf10 [mysql]11 # 设置 mysql 客户端默认编码 12 default-character-set=utf813 [mysqld]14 #指定 sever_id,三个 Mysql 实例需要分别改为对应的 sever_id15 server_id=116 # 必须开启 GTID 支持 17 gtid_mode=ON18 enforce_gtid_consistency=ON19 # 启用二进制日志 20 log-bin=mysql-bin21 #启用并行复制 22 binlog_transaction_dependency_tracking=WRITESET23 replica_preserve_commit_order=ON24 replica_parallel_type=LOGICAL_CLOCK25 transaction_write_set_extraction=XXHASH6426 #对于 Group Replication,数据必须存储在 InnoDB 事务存储引擎中 27 disabled_storage_engines="MyISAM,BLACKHOLE,FEDERATED,ARCHIVE,MEMORY"
2829 # mgr-node2 和 mgr-node3 同上,注意配置文件路径和修改 server_id30 vim /mysql/mgr/node2/conf/custom.cnf31 [mysql]32 # 设置 mysql 客户端默认编码 33 default-character-set=utf834 [mysqld]

35 #指定 sever_id,三个 Mysql 实例需要分别改为对应的 sever_id36 server_id=237 # 必须开启 GTID 支持 38 gtid_mode=ON39 enforce_gtid_consistency=ON40 # 启用二进制日志 41 log-bin=mysql-bin42 #启用并行复制 43 binlog_transaction_dependency_tracking=WRITESET44 replica_preserve_commit_order=ON45 replica_parallel_type=LOGICAL_CLOCK46 transaction_write_set_extraction=XXHASH6447 #对于 Group Replication,数据必须存储在 InnoDB 事务存储引擎中 48 disabled_storage_engines="MyISAM,BLACKHOLE,FEDERATED,ARCHIVE,MEMORY"
4950 vim /mysql/mgr/node3/conf/custom.cnf51 [mysql]52 # 设置 mysql 客户端默认编码 53 default-character-set=utf854 [mysqld]55 #指定 sever_id,三个 Mysql 实例需要分别改为对应的 sever_id56 server_id=357 # 必须开启 GTID 支持 58 gtid_mode=ON59 enforce_gtid_consistency=ON60 # 启用二进制日志 61 log-bin=mysql-bin62 #启用并行复制 63 binlog_transaction_dependency_tracking=WRITESET64 replica_preserve_commit_order=ON65 replica_parallel_type=LOGICAL_CLOCK66 transaction_write_set_extraction=XXHASH6467 #对于 Group Replication,数据必须存储在 InnoDB 事务存储引擎中 68 disabled_storage_engines="MyISAM,BLACKHOLE,FEDERATED,ARCHIVE,MEMORY"
6970 #运行 mysql 容器 71 # 为了便于测试,启动容器时指定好 IP、hostname72 docker run -d \73 --name mgr-node1 \74 --privileged=true \

75 --restart=always \76 --ip 172.19.0.10 \77 --hostname mgr-node1 \78 --add-host mgr-node2:172.19.0.11 \79 --add-host mgr-node3:172.19.0.12 \80 --network mgr-network \81 -p 3321:3306 \82 -v /mysql/mgr/node1/data:/var/lib/mysql \83 -v /mysql/mgr/node1/conf:/etc/mysql/conf.d \84 -v /mysql/mgr/node1/log:/logs \85 -e MYSQL_ROOT_PASSWORD=123456 \86 -e TZ=Asia/Shanghai mysql:8.0.27 \87 --lower_case_table_names=1888990 docker run -d \91 --name mgr-node2 \92 --privileged=true \93 --restart=always \94 --ip 172.19.0.11 \95 --hostname mgr-node2 \96 --add-host mgr-node1:172.19.0.10 \97 --add-host mgr-node3:172.19.0.12 \98 --network mgr-network \99 -p 3322:3306 \100 -v /mysql/mgr/node2/data:/var/lib/mysql \101 -v /mysql/mgr/node2/conf:/etc/mysql/conf.d \102 -v /mysql/mgr/node2/log:/logs \103 -e MYSQL_ROOT_PASSWORD=123456 \104 -e TZ=Asia/Shanghai mysql:8.0.27 \105 --lower_case_table_names=1106107 docker run -d \108 --name mgr-node3 \109 --privileged=true \110 --restart=always \111 --ip 172.19.0.12 \112 --hostname mgr-node3 \113 --add-host mgr-node1:172.19.0.10 \

114 --add-host mgr-node2:172.19.0.11 \115 --network mgr-network \116 -p 3323:3306 \117 -v /mysql/mgr/node3/data:/var/lib/mysql \118 -v /mysql/mgr/node3/conf:/etc/mysql/conf.d \119 -v /mysql/mgr/node3/log:/logs \120 -e MYSQL_ROOT_PASSWORD=123456 \121 -e TZ=Asia/Shanghai mysql:8.0.27 \122 --lower_case_table_names=1123124125 # 在宿主机上配置 mysql 容器的 ip 和 host 映射 126 vim /etc/hosts127 172.19.0.10 mgr-node1128 172.19.0.11 mgr-node2129 172.19.0.12 mgr-node3 所有实例分别配置远程访问 1 # 以 node1 为例 2 docker exec -it mgr-node1 /bin/bash3 mysql -u root -p1234564 #进入 mysql 执行 5 ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '123456';
6 flush privileges;
2. 安装 mysqlrouter 和安装 mysqlshellMySQL Router 是 MySQL Proxy 的后继产品,它提供了 MySQL 协议的路由器功能,可以用来实现读写分离、负载均衡和高可用性解决方案。
安装 mysql-router 下载地址:https://downloads.mysql.com/archives/router/1 # 以 centos7 为例

2 wget https://downloads.mysql.com/archives/get/p/41/file/mysql-router-community-8.0.271.el7.x86_64.rpm3 rpm -ivh mysql-router-community-8.0.27-1.el7.x86_64.rpm 安装 mysql-shell 下载地址:https://downloads.mysql.com/archives/shell/1 # 以 centos7 为例 2 wget https://downloads.mysql.com/archives/get/p/43/file/mysql-shell-8.0.27-
3. InnoDB Cluster 初始化
3.1 参数及权限配置预需求检测在添加实例到集群中前,使用该方法检查实例配置是否满足 InnoDB 集群要求。
1 mysqlsh root@192.168.65.223:3321 --js2 // 检查实例是否符合 InnoDB Cluster 的参数及权限配置要求 3 dba.checkInstanceConfiguration('root@mgr-node1:3306')

4 dba.checkInstanceConfiguration('root@mgr-node2:3306')
5 dba.checkInstanceConfiguration('root@mgr-node3:3306')
如果验证通过返回 ok。
如果验证没通过,比如出现下面的日志提示,需要 mysql 实例开启 gtid 和指定 server_id 搭建 InnoDB Cluster 需要满足的要求如下:
InnoDB 集群使用了 Group Replication,因此必须满足使用组复制的要求。具体可以参考 https://dev.mysql.com/doc/refman/8.0/en/group-replication-requirements.html。其中比较重要的几点有:
必须开启二进制日志,并且日志格式为 ROW,即--log-bin 和 binlog_format=row(默认);
必须开启副本更新日志,即 log_replica_updates=ON(默认) ;
必须开启 GTID,即 gtid_mode=ON 和 enforce_gtid_consistency=ON。
存储引擎只 能使用 InnoDB。最好禁用其他存储引擎:
1 disabled_storage_engines="MyISAM,BLACKHOLE,FEDERATED,ARCHIVE,MEMORY"
从 8.0.23 开始,集群中的实例要启用并行复制。需要配置以下系统变量:
1 binlog_transaction_dependency_tracking=WRITESET2 slave_preserve_commit_order=ON3 slave_parallel_type=LOGICAL_CLOCK4 transaction_write_set_extraction=XXHASH643.2 初始化 InnoDB Cluster 相关配置

1// 对实例配置 InnoDB Cluster 相关参数 2 dba.configureInstance('root@mgr-node1:3306')
3 dba.configureInstance('root@mgr-node2:3306')
4 dba.configureInstance('root@mgr-node3:3306')
4.创建一主两从 InnoDB 集群集群常用命令 1 #会列出 dba 相关指令 2 dba.help();
3 #列出详细指令的用法 4 dba.help('deploySandboxInstance');
5 #检查节点配置实例,用于加入 cluster 之前 6 dba.checkInstanceConfiguration("root@hostname:3306");
7 #节点初始化 8 dba.configureInstance('root@hostname:3306');
9 #重启集群 10 dba.rebootClusterFromCompleteOutage('myCluster');
11 #会列出集群相关指令 12 cluster.help();
13 #创建集群 14 var cluster = dba.createCluster('myCluster');
15 #获取当前集群实例 16 var cluster = dba.getCluster('myCluster');
17 查看集群状态 18 cluster.status();
19 #检查 cluster 节点状态

20 cluster.checkInstanceState("root@hostname:3306") ;
21 #增加节点 22 cluster.addInstance("root@hostname:3306") ;
23 #删除节点 24 cluster.removeInstance("root@hostname:3306") ;
25 #强制删除节点 26 cluster.removeInstance('root@hostname:3306',{force:true});
27 # 状态为 missing 的节点可以重新加入集群 28 cluster.rejoinInstance("root@hostname:3306")
29 #解散集群 30 cluster.dissolve({force:true}) ;
31 #集群描述 32 cluster.describe();
进入主节点创建集群初始化完第一个实例后,就可以创建集群了。
1 # 进入主节点创建集群 2 mysqlsh root@192.168.65.223:3321 --js3 # 创建一个 cluster,命名为 'myCluster'4 var cluster = dba.createCluster('myCluster');
5 # 创建成功后,查看 cluster 状态 6 cluster.status();
当前集群的状态如下

添加副本实例添加副本实例到创建好的集群。
1 #初始化第二个和第三个实例:
2 cluster.addInstance('root@mgr-node2:3306');
3 cluster.addInstance('root@mgr-node3:3306');
4 #查看 cluster 状态 5 cluster.status();

如果提示副本实例的 GTID 与集群不一致,选择通过 Clone 方式覆盖副本实例上的数据即可。

小结:完整的集群创建步骤 1 #进入主节点 2 mysqlsh root@mgr-node1:3306 --js34 #mgr-node15 # 参数权限检查 6 dba.checkInstanceConfiguration('root@mgr-node1:3306');
7 # 初始化 8 dba.configureInstance('root@mgr-node1:3306');
9 # 创建集群 10 var cluster = dba.createCluster('myCluster');
11 #查看 cluster 状态 12 cluster.status();
1314 #mgr-node215 # 参数权限检查

16 dba.checkInstanceConfiguration('root@mgr-node2:3306');
17 # 初始化 18 dba.configureInstance('root@mgr-node2:3306');
19 # 添加副本 20 cluster.addInstance('root@mgr-node2:3306');
2122 #mgr-node323 # 参数权限检查 24 dba.checkInstanceConfiguration('root@mgr-node3:3306');
25 # 初始化 26 dba.configureInstance('root@mgr-node3:3306');
27 # 添加副本 28 cluster.addInstance('root@mgr-node3:3306');
2930 #查看 cluster 状态 31 cluster.status();
32 搭建一主两从集群架构最终效果如下:

注意到集群状态已变为"status": "OK"和"statusText": "Cluster is ONLINE and can tolerate up to ONEfailure."。
集群节点状态:
ONLINE - 节点状态正常。
OFFLINE - 实例在运行,但没有加入任何 Cluster。
RECOVERING - 实例已加入 Cluster,正在同步数据。
ERROR - 同步数据发生异常。
UNREACHABLE - 与其他节点通讯中断,可能是网络问题,可能是节点 crash。
MISSING - 节点已加入集群,但未启动 group replication

测试数据是否同步 1 #主节点 mgr-node12 [root@192-168-65-223 ~]# docker exec -it mgr-node1 bash3 root@mgr-node1:/# mysql -uroot -p1234564 mysql>5 create database test;
6 use test;
7 create table t(x int primary key auto_increment,y int);
8 insert into t(x,y) value(1,1);
注意:如果创建表没有设置主键,会抛出错误:ERROR 3098 (HY000): The table does not complywith the requirements by an external plugin.1 # 查看其他节点,数据是否同步 2 [root@192-168-65-223 ~]# docker exec -it mgr-node2 bash3 root@mgr-node2:/# mysql -uroot -p1234564 mysql> use test;
5 Reading table information for completion of table and column names6 You can turn off this feature to get a quicker startup with -A78 Database changed9 mysql> select * from t;
10 +---+------+11 | x | y |12 +---+------+13 | 1 | 1 |14 +---+------+15 1 row in set (0.00 sec)
测试主从切换 1 #停掉主节点 2 [root@192-168-65-223 ~]# docker stop mgr-node14 # 连接到 mgr-node25 MySQL mgr-node1:3306 ssl JS > \connect root@mgr-node2:33066 # 获取集群实例 7 MySQL mgr-node2:3306 ssl JS > var cluster=dba.getCluster();
8 # 查看集群状态 9 MySQL mgr-node2:3306 ssl JS > cluster.status()
10 {11 "clusterName": "myCluster",12 "defaultReplicaSet": {13 "name": "default",14 "primary": "mgr-node2:3306",15 "ssl": "REQUIRED",16 "status": "OK_NO_TOLERANCE",17 "statusText": "Cluster is NOT tolerant to any failures. 1 member is notactive.",18 "topology": {19 "mgr-node1:3306": {20 "address": "mgr-node1:3306",21 "memberRole": "SECONDARY",22 "mode": "n/a",23 "readReplicas": {},24 "role": "HA",25 "shellConnectError": "MySQL Error 2003: Could not open connection to'mgr-node1:3306': Can't connect to MySQL server on 'mgr-node1:3306' (113)",26 "status": "(MISSING)"
27 },28 "mgr-node2:3306": {29 "address": "mgr-node2:3306",30 "memberRole": "PRIMARY",31 "mode": "R/W",32 "readReplicas": {},33 "replicationLag": null,34 "role": "HA",35 "status": "ONLINE",36 "version": "8.0.27"
37 },38 "mgr-node3:3306": {39 "address": "mgr-node3:3306",40 "memberRole": "SECONDARY",41 "mode": "R/O",

42 "readReplicas": {},43 "replicationLag": null,44 "role": "HA",45 "status": "ONLINE",46 "version": "8.0.27"
47 }48 },49 "topologyMode": "Single-Primary"
50 },51 "groupInformationSourceMember": "mgr-node2:3306"
5253 可以看到 mgr-node2 升级为主节点 1 # 启动 mgr-node1 节点 2 [root@192-168-65-223 ~]# docker start mgr-node13 # 查看集群状态,发现 mgr-node1 正在恢复,最终正常 4 MySQL mgr-node2:3306 ssl JS > cluster.status()
5 {6 "clusterName": "myCluster",7 "defaultReplicaSet": {8 "name": "default",9 "primary": "mgr-node2:3306",10 "ssl": "REQUIRED",11 "status": "OK_NO_TOLERANCE",

12 "statusText": "Cluster is NOT tolerant to any failures. 1 member is notactive.",13 "topology": {14 "mgr-node1:3306": {15 "address": "mgr-node1:3306",16 "instanceErrors": [17 "NOTE: group_replication is stopped."
18 ],19 "memberRole": "SECONDARY",20 "memberState": "OFFLINE",21 "mode": "R/O",22 "readReplicas": {},23 "role": "HA",24 "status": "(MISSING)",25 "version": "8.0.27"
26 },27 "mgr-node2:3306": {28 "address": "mgr-node2:3306",29 "memberRole": "PRIMARY",30 "mode": "R/W",31 "readReplicas": {},32 "replicationLag": null,33 "role": "HA",34 "status": "ONLINE",35 "version": "8.0.27"
36 },37 "mgr-node3:3306": {38 "address": "mgr-node3:3306",39 "memberRole": "SECONDARY",40 "mode": "R/O",41 "readReplicas": {},42 "replicationLag": null,43 "role": "HA",44 "status": "ONLINE",45 "version": "8.0.27"
46 }47 },48 "topologyMode": "Single-Primary"
49 },50 "groupInformationSourceMember": "mgr-node2:3306"

51 }52 MySQL mgr-node2:3306 ssl JS > cluster.status()
53 {54 "clusterName": "myCluster",55 "defaultReplicaSet": {56 "name": "default",57 "primary": "mgr-node2:3306",58 "ssl": "REQUIRED",59 "status": "OK",60 "statusText": "Cluster is ONLINE and can tolerate up to ONE failure.",61 "topology": {62 "mgr-node1:3306": {63 "address": "mgr-node1:3306",64 "memberRole": "SECONDARY",65 "mode": "R/O",66 "readReplicas": {},67 "replicationLag": null,68 "role": "HA",69 "status": "ONLINE",70 "version": "8.0.27"
71 },72 "mgr-node2:3306": {73 "address": "mgr-node2:3306",74 "memberRole": "PRIMARY",75 "mode": "R/W",76 "readReplicas": {},77 "replicationLag": null,78 "role": "HA",79 "status": "ONLINE",80 "version": "8.0.27"
81 },82 "mgr-node3:3306": {83 "address": "mgr-node3:3306",84 "memberRole": "SECONDARY",85 "mode": "R/O",86 "readReplicas": {},87 "replicationLag": null,88 "role": "HA",89 "status": "ONLINE",90 "version": "8.0.27"

91 }92 },93 "topologyMode": "Single-Primary"
94 },95 "groupInformationSourceMember": "mgr-node2:3306"
96 }97 更多的常见操作参数配置可以用 cluster.options()查看当前集群的配置属性,集群参数配置分为两种方式:
cluster.setOption() 用来设置所有节点的参数 cluster.setInstanceOption() 用来对指定节点配置属性 1 # 将所有节点的权重都改为 502 var cluster = dba.getCluster()
3 cluster.setOption("memberWeight",50)
4 # 重新加入集群重试次数改为 5 次 5 cluster.setOption("autoRejoinTries",5)
67 # 将其中一个节点的权重改为 758 cluster.setInstanceOption("mgr-node2:3306","memberWeight",75)
9 # 重新加入集群重试次数改为 10 次 10 cluster.setInstanceOption("mgr-node2:3306","autoRejoinTries",10)
11 配置节点权重 memberWeight 选项的值域为 0 到 100 之间的整数,缺省值为 50。该值是故障转移时自动选举主节点的百分比权重,具有较高 memberWeight 值的实例更有可能在单主群集中被选为主节点 1 // 查看集群的参数配置(包括 memberWeight 优先级配置)
2 cluster.options()
34 // 在集群创建时配置

5 dba.createCluster('myCluster', {memberWeight:75}) // 第一个节点配置方式 6 var cluster = dba.getCluster()
7 cluster.addInstance('mgr-node2:3306',{memberWeight:50})
8 cluster.addInstance('mgr-node3:3306',{memberWeight:25})
910 // 在集群创建完成后修改权重 11 var cluster = dba.getCluster()
12 cluster.setInstanceOption('mgr-node1:3306','memberWeight',100)
13 cluster.setInstanceOption('mgr-node2:3306','memberWeight',50)
14 cluster.setInstanceOption('mgr-node3:3306','memberWeight',25)
将节点重新加入集群状态为 mssing 的节点,通常是组复制关闭或中断状态,可以用 cluster.rejoinInstance()重新加入集群,会重新对该节点设置 MGR 相关参数(持久化到 mysqld-auto.conf 中)
1 cluster.removeInstance('root@hostname:3306',{force:true});
如果一些参数做了修改,如 server_uuid 变更,导致 rejoin 失败,则需要将节点从集群中删除后重新加入 1 cluster.removeInstance("root@hostname:3306",{force:true})
2 cluster.rescan()
3 cluster.addInstance("root@hostname:3306")
集群多数节点异常,恢复当集群多个节点异常,则失去了仲裁机制,剩下的一个节点 1 // 将集群剥离为单节点运行 2 JS > cluster.forceQuorumUsingPartitionOf("root@hostname:3306")
34 // 重新加另外 2 个节点加入 5 JS > cluster.rejoinInstance("root@hostname2:3306")
6 JS > cluster.rejoinInstance("root@hostname3:3306")

集群节点角色切换在 MGR 的管理下提供了一下 3 种方式进行角色切换,mysqlsh 对其进行了封装调用 group_replication_set_as_primary(member_uuid);
cluster.setPrimaryInstance("homename:3306")
group_replication_switch_to_single_primary_mode()
cluster.switchToSinglePrimaryMode("homename:3306")
group_replication_switch_to_multi_primary_mode()
cluster.switchToMultiPrimaryMode()
单主模式-指定主节点切换 1 var cluster = dba.getCluster()
2 cluster.setPrimaryInstance('homename:3306')
3 cluster.status()
4 单主模式和多主模式相互切换 1 // 切换为多主模式 2 var cluster = dba.getCluster()
3 cluster.switchToMultiPrimaryMode()
45 // 指定明确的主节点将多主模式切换为单主模式 6 cluster.switchToSinglePrimaryMode("homename:3306")
7 将单主模式切换为多主模式的效果

销毁集群删除与群集关联的所有元数据和配置,并禁用实例上的组复制,但不会删除在实例之间复制的任何数据。要再次创建集群,使用 dba.createCluster()
1 var cluster = dba.getCluster()
2 cluster.dissolve()
创建集群管理用户 1 cluster.setupAdminAccount('fox')

1 # 经典 MySQL 协议连接 2 mysqlsh --mysql -hmgr-node1 -ufox3 # X 协议连接 4 mysqlsh --mysqlx -hmgr-node1 -ufox7.使用 MySQL Router 连接集群配置路由器 1 mysqlrouter --bootstrap root@mgr-node2:3306 --force --user=root2 #或者指定 host3 mysqlrouter --bootstrap root@mgr-node2:3306 --force --user=root --report-host mgr 注意,如果用户之前为该实例配置过路由,则可以通过指定 force 选项强制引导启动。

上面的内容是引导启动路由器时输出的信息,信息提示,MySQL 经典协议使用 6446 端口和 6447 端口,X 协议使用 6448 端口和 6449 端口,每种协议使用的两个端口分别用于读写和只读。
在一个运行的集群中,AdminAPI 可以引导多个路由器。用户可以使用 cluster.listRouters()方法显示所有注册的路由器列表。
启动路由器 1 mysqlrouter &路由器已经成功启动。现在,使用 MySQL Shell 连接路由器进行验证。

1 #连接 mysqlrouter2 [root@192-168-65-223 ~]# mysqlsh root@localhost:6446 --sql3 MySQL localhost:6446 ssl SQL > use test;
4 MySQL localhost:6446 ssl test SQL > select * from t;
查看集群成员信息 1 MySQL localhost:6446 ssl test SQL > select * fromperformance_schema.replication_group_members;
测试测试读写端口 6446 用户可以通过连接本机的 6446 端口连接到 MySQL 实例 6446 为读写端口,也可以插入数据

测试只读端口 6647:插入数据报错 MySQL InnoDB ReplicaSet 基本概述 MySQL Innodb Cluster = MySQL Shell + MySQL Router + MySQL Group Replication(MGR),全程由 MySQL Shell 来管理操作 MGR 的聚合套件。 MySQL 8.0.19 发布后,这种组合延伸到 MySQLReplication(主从复制),也就是 MySQL Shell + MySQL Router + MySQL Replication。
InnoDB ReplicaSet 至少由两个 MySQL 服务器实例组成,并提供用户熟知的主从复制功能,例如读取横向扩展和数据安全性。 InnoDB ReplicaSet 使用以下 MySQL 技术。
MySQL Shell:MySQL 的高级客户端、管理工具,可以用来管理复制集。
MySQL 复制:一组 MySQL 实例,通过复制能够提供可用性和异步读取的横向扩展。
MySQL Router:一种轻量级的中间件,可在应用程序和 InnoDB ReplicaSet 之间提供透明的路由。 InnoDBReplicaSet 的接口类似于 InnoDB Cluster,用户可以利用 MySQL Shell 使用 MySQL 实例和 MySQL Router。
与 InnoDB 集群相比,InnoDB ReplicaSet 具有多个限制,因此,官方建议尽可能部署 InnoDB 群集。通常,InnoDB ReplicaSet 本身不能提供高可用性。 InnoDB ReplicaSet 的限制包括:
没有自动故障转移。如果主服务器不可用,则需要使用 AdminAPI 手动触发故障转移,然后才能再次进行任何更改。但是,辅助实例仍然可用于读取。
无法防止因意外停止或不可用而导致部分数据丢失。暂停之前尚未应用的事务可能会丢失。
无法防止崩溃或不可用后出现不一致情况。如果故障转移在辅助节点仍可用的情况下提升了辅助节点(例如,由于网络分区),则可能会因脑裂而引起不一致。

搭建一主一从的复制集
1. 安装 2 个数据库实例参考:Docker 安装 MySQL8.0 可以利用 docker 快速部署 2 个 MySQL 实例主机名(角色) server_id 宿主机 IP 容器固定 IP DB Portrs-node1(primary) 21 192.168.65.223 172.20.0.20 3331>3306rs-
node2(Secondary 22 192.168.65.223 172.20.0.21 3332>3306)
1 # 创建组复制的网络 保证三个 mysql 容器之间可以通过容器名访问 2 docker network create --driver bridge --subnet 172.20.0.0/24 --gateway 172.20.0.1 rsnetwork34 mkdir -p /mysql/rs/node1/data /mysql/rs/node1/conf /mysql/rs/node1/log5 mkdir -p /mysql/rs/node2/data /mysql/rs/node2/conf /mysql/rs/node2/log678 #以 rs-node1 配置为例,创建/mysql/rs/node1/conf/custom.cnf,添加以下配置:
9 vim /mysql/rs/node1/conf/custom.cnf10 [mysql]11 # 设置 mysql 客户端默认编码 12 default-character-set=utf813 [mysqld]14 #指定 sever_id,多个 Mysql 实例需要分别改为对应的 sever_id15 server_id=2116 # 必须开启 GTID 支持 17 gtid_mode=ON18 enforce_gtid_consistency=ON19 # 启用二进制日志 20 log-bin=mysql-bin21 #启用并行复制 22 binlog_transaction_dependency_tracking=WRITESET23 replica_preserve_commit_order=ON24 replica_parallel_type=LOGICAL_CLOCK25 transaction_write_set_extraction=XXHASH64

2627 # rs-node2 同上,注意配置文件路径和修改 server_id28 vim /mysql/rs/node2/conf/custom.cnf29 [mysql]30 # 设置 mysql 客户端默认编码 31 default-character-set=utf832 [mysqld]33 #指定 sever_id,多个 Mysql 实例需要分别改为对应的 sever_id34 server_id=2235 # 必须开启 GTID 支持 36 gtid_mode=ON37 enforce_gtid_consistency=ON38 # 启用二进制日志 39 log-bin=mysql-bin40 #启用并行复制 41 binlog_transaction_dependency_tracking=WRITESET42 replica_preserve_commit_order=ON43 replica_parallel_type=LOGICAL_CLOCK44 transaction_write_set_extraction=XXHASH64454647 #运行 mysql 容器 48 # 为了便于测试,启动容器时指定好 IP、hostname49 docker run -d \50 --name rs-node1 \51 --privileged=true \52 --restart=always \53 --ip 172.20.0.20 \54 --hostname rs-node1 \55 --add-host rs-node2:172.20.0.21 \56 --network rs-network \57 -p 3331:3306 \58 -v /mysql/rs/node1/data:/var/lib/mysql \59 -v /mysql/rs/node1/conf:/etc/mysql/conf.d \60 -v /mysql/rs/node1/log:/logs \61 -e MYSQL_ROOT_PASSWORD=123456 \62 -e TZ=Asia/Shanghai mysql:8.0.27 \63 --lower_case_table_names=16566 docker run -d \67 --name rs-node2 \68 --privileged=true \69 --restart=always \70 --ip 172.20.0.21 \71 --hostname rs-node2 \72 --add-host rs-node1:172.20.0.20 \73 --network rs-network \74 -p 3332:3306 \75 -v /mysql/rs/node2/data:/var/lib/mysql \76 -v /mysql/rs/node2/conf:/etc/mysql/conf.d \77 -v /mysql/rs/node2/log:/logs \78 -e MYSQL_ROOT_PASSWORD=123456 \79 -e TZ=Asia/Shanghai mysql:8.0.27 \80 --lower_case_table_names=181828384 # 在宿主机上配置 mysql 容器的 ip 和 host 映射 85 vim /etc/hosts86 172.20.0.20 rs-node187 172.20.0.21 rs-node2 所有实例分别配置远程访问 1 # 以 node1 为例 2 docker exec -it rs-node1 /bin/bash3 mysql -u root -p1234564 #进入 mysql 执行 5 ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '123456';
6 flush privileges;
2. 配置复制集
1)初始化主节点,创建复制集

1 #进入主节点 2 mysqlsh root@rs-node1:3306 --js3 # 初始化 4 dba.configureReplicaSetInstance('root@rs-node1:3306')
5 # 创建复制集,使用异步复制 6 var rs = dba.createReplicaSet("myrs")
7 #查看状态 8 rs.status()
2)添加副本节点 1 #将实例添加到复制集 2 rs.addInstance('root@rs-node2:3306')
测试数据是否同步 1 #主节点 rs-node12 [root@192-168-65-223 ~]# docker exec -it rs-node1 bash3 root@mgr-node1:/# mysql -uroot -p1234564 mysql>5 create datebase test;
6 use test;
7 create table t(x int primary key auto_increment,y int);
8 insert into t(x,y) value(1,1);
9 select * from t;
1011 # 进入从节点 rs-node2,查看数据是否同步过来 12 [root@192-168-65-223 ~]# docker exec -it rs-node2 bash13 root@rs-node2:/# mysql -uroot -p12345614 mysql: [Warning] Using a password on the command line interface can be insecure.15 Welcome to the MySQL monitor. Commands end with ; or \g.16 Your MySQL connection id is 159617 Server version: 8.0.27 MySQL Community Server - GPL1819 Copyright (c) 2000, 2021, Oracle and/or its affiliates.2021 Oracle is a registered trademark of Oracle Corporation and/or its

22 affiliates. Other names may be trademarks of their respective23 owners.2425 Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.2627 mysql> use test;
28 Reading table information for completion of table and column names29 You can turn off this feature to get a quicker startup with -A3031 Database changed32 mysql> select * from t;
33 +---+------+34 | x | y |35 +---+------+36 | 1 | 1 |37 +---+------+38 1 row in set (0.00 sec)
39
3. 配置 MySQL Router 路由器 1 [root@192-168-65-223 ~]# mysqlrouter --bootstrap root@rs-node1:3306 --force --user=root 重启 Mysql Router1 [root@192-168-65-223 ~]# ps -ef|grep mysqlrouter2 root 16993 14238 6 11:30 pts/1 00:18:01 mysqlrouter3 root 21637 14178 0 16:22 pts/0 00:00:00 grep --color=auto mysqlrouter4 [root@192-168-65-223 ~]# kill -9 169935 # 启动 Mysql Router6 [root@192-168-65-223 ~]# mysqlrouter &
4. 测试用户可以通过连接本机的 6446 端口连接到 MySQL 实例

1 [root@192-168-65-223 ~]# mysqlsh root@localhost:6446 --sql2 # 可以查询到插入的测试数据 3 MySQL localhost:6446 ssl SQL > select * from test.t;
4 +---+---+5 | x | y |6 +---+---+7 | 1 | 1 |8 +---+---+9
