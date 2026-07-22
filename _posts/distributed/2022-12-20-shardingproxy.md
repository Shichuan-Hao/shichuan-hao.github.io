---

title: "四、登堂入室：深入理解ShardingProxy服务端分库分表"
description: "登堂入室:深入理解 ShardingProxy 服务端分库分表-- 楼兰通常程序员可以使用 ShardingSphere 完成分库分表功能。"
author: hsc
date: 2022-12-20 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Redis', 'Netty', 'Zookeeper', '分库分表']
toc: true

---

登堂入室:深入理解 ShardingProxy 服务端分库分表-- 楼兰通常程序员可以使用 ShardingSphere 完成分库分表功能。但是,管理数据这事从来不只是开发人员的事情。
ShardingProxy,是 ShardingSphere 进行服务端分库分表的工具。他给数据管理提供了另外一种视⻆。在这一章,我们来深入理解 ShardingProxy 分库分表。但是在开始之前,不要仅仅把 ShardingProxy 当做一个简单的数据库产品,而是要结合之前对于 ShardingJDBC 的理解,相互印证,相互不足。更重要的是要开始思考如何将 ShardingJDBC 和 ShardingProxy 协同使用,共同处理好分库分表的各种问题。
一、为什么要有服务端分库分表?
ShardingProxy,定位为一个透明化的数据库代理,是 ShardingSphere 重要的服务端分库分表产品。目前提供 MySQL 和 PostgreSQL 协议,透明化数据库操作。简单理解就是,他会部署成一个 MySQL 或者 PostgreSQL 的数据库服务,应用程序只需要像操作单个数据库一样去访问 ShardingProxy,由 ShardingProxy 去完成分库分表功能。
<!-- [image removed: local file path] -->
这些配置文件的作用一目了然。 server.yaml 配置一些服务通用的参数。 config-sharding 配置数据分片逻辑。
config-encrypt 配置数据加密逻辑。 config-readwrite-splitting 配置读写分离逻辑。文件当中的配置项,就是 ShardingJDBC 的 ShardingSphereDatasource 可以理解的 yaml 配置文件。如果你熟悉了之前 ShardingJDBC 的示例,几乎可以零⻔槛看懂这些配置文件。
先打开 server.yaml,把其中的 rule 部分和 props 部分注释打开

rules:
- !AUTHORITYusers:
- root@%:root- sharding@:shardingprovider:
type: ALL_PERMITTED- !TRANSACTIONdefaultType: XAproviderType: Atomikos- !SQL_PARSERsqlCommentParseEnabled: truesqlStatementCache:
initialCapacity: 2000maximumSize: 65535parseTreeCache:
initialCapacity: 128maximumSize: 1024props:
max-connections-size-per-query: 1kernel-executor-size: 16 # Infinite by default.proxy-frontend-flush-threshold: 128 # The default value is 128.proxy-hint-enabled: falsesql-show: falsecheck-table-metadata-enabled: false
# Proxy backend query fetch size. A larger value may increase the memory usage of
ShardingSphere Proxy.
# The default value is -1, which means set the minimum value for different JDBC drivers.
proxy-backend-query-fetch-size: -1proxy-frontend-executor-size: 0 # Proxy frontend executor size. The default value is 0,which means let Netty decide.
# Available options of proxy backend executor suitable: OLAP(default), OLTP. The OLTP
option may reduce time cost of writing packets to client, but it may increase the latency ofSQL execution
# and block other clients if client connections are more than `proxy-frontend-executor-
size`, especially executing slow SQL.proxy-backend-executor-suitable: OLAPproxy-frontend-max-connections: 0 # Less than or equal to 0 means no limitation.
# Available sql federation type: NONE (default), ORIGINAL, ADVANCED
sql-federation-type: NONE
# Available proxy backend driver type: JDBC (default), ExperimentalVertx
proxy-backend-driver-type: JDBCproxy-mysql-default-version: 8.0.20 # In the absence of schema name, the default versionwill be used.proxy-default-port: 3307 # Proxy default port.proxy-netty-backlog: 1024 # Proxy netty backlog.rules 下的 AUTHORITY 部分配置 ShardingProxy 的用户以及权限。 TRANSACTION 部分维护的是事务控制器,下一章节再做分析。
props 部分配置服务端的一些参数。 max-connections-size-per-query 参数在上一章节介绍 ShardingSphere 的执行引擎以及结果归并时介绍到了。 proxy-mysql-default-version 表示 ShardingProxy 所模拟的 MySQL 服务版本。为了与之前的示例兼容,我们这里可以将它改成 8.0.20 版本。 proxy-default-port 表示模拟的 MySQL 服务的端口。
修改完成后,就可以启动 ShardingProxy 了。 启动脚本在 bin 目录下。

服务启动后,就可以使用客户端直接访问 ShardingProxy 了。
唯一需要注意的是,如果你希望使用 MySQL 的客户端连接 ShardingProxy,需要手动将 MySQL 的 JDBC 驱动包拷⻉到 ShardingProxy 的 lib 目录下。 ShardingProxy 默认只支持 PostgreSQL 协议。
然后,你可以像用 MySQL 一样去使用 shardingProxy

mysql> show databases;
+--------------------+
| schema_name |
+--------------------+
| shardingsphere |
| information_schema |
| performance_schema |
| mysql |
| sys |
+--------------------+5 rows in set (0.01 sec)
mysql> use shardingsphereDatabase changedmysql> show tables;
+---------------------------+------------+
| Tables_in_shardingsphere | Table_type |
+---------------------------+------------+
| sharding_table_statistics | BASE TABLE |
+---------------------------+------------+1 row in set (0.01 sec)
mysql> select * from sharding_table_statistics;
Empty set (1.25 sec)
不过你要注意,此时 ShardingProxy 只是一个虚拟库,所以你并不能真的像 MYSQL 一样去随意的建表,修改数据。
mysql> CREATE TABLE test (id varchar(255) NOT NULL);
Query OK, 0 rows affected (0.00 sec)
mysql> select * from test;
30000 - Unknown exception: At line 0, column 0: Object 'test' not foundmysql> show tables;
+---------------------------+------------+
| Tables_in_shardingsphere | Table_type |
+---------------------------+------------+
| sharding_table_statistics | BASE TABLE |
+---------------------------+------------+1 row in set (0.01 sec)
2、配置常用分库分表策略当然,现在 ShardingProxy 里还没什么东⻄,因为还没有配置逻辑表。打开 config-sharding.xml,像我们之前章节使用 shardingJDBC 时一样,配置逻辑表 course。

databaseName: sharding_dbdataSources:
m0:
url: jdbc:mysql://192.168.65.212:3306/shardingdb1?serverTimezone=UTC&useSSL=falseusername: rootpassword: rootconnectionTimeoutMilliseconds: 30000idleTimeoutMilliseconds: 60000maxLifetimeMilliseconds: 1800000maxPoolSize: 50minPoolSize: 1m1:
url: jdbc:mysql://192.168.65.212:3306/shardingdb2?serverTimezone=UTC&useSSL=falseusername: rootpassword: rootconnectionTimeoutMilliseconds: 30000idleTimeoutMilliseconds: 60000maxLifetimeMilliseconds: 1800000maxPoolSize: 50minPoolSize: 1rules:
- !SHARDINGtables:
course:
actualDataNodes: m${0..1}.course_${1..2}databaseStrategy:
standard:
shardingColumn: cidshardingAlgorithmName: course_db_algtableStrategy:
standard:
shardingColumn: cidshardingAlgorithmName: course_tbl_algkeyGenerateStrategy:
column: cidkeyGeneratorName: alg_snowflakeshardingAlgorithms:
course_db_alg:
type: MODprops:
sharding-count: 2course_tbl_alg:
type: INLINEprops:
algorithm-expression: course_${cid%2+1}keyGenerators:
alg_snowflake:
type: SNOWFLAKE 详细到现在,这个配置信息已经不难理解了。
然后重新启动 ShardingProxy 服务,再看看服务中有哪些东⻄。

mysql> show databases;
+--------------------+
| schema_name |
+--------------------+
| information_schema |
| performance_schema |
| sys |
| shardingsphere |
| sharding_db |
| mysql |
+--------------------+6 rows in set (0.02 sec)
mysql> use sharding_db;
Database changedmysql> show tables;
+-----------------------+------------+
| Tables_in_sharding_db | Table_type |
+-----------------------+------------+
| course | BASE TABLE |
| user_2 | BASE TABLE |
| user | BASE TABLE |
| user_1 | BASE TABLE |
+-----------------------+------------+4 rows in set (0.02 sec)
mysql> select * from course;
+---------------------+-------+---------+---------+
| cid | cname | user_id | cstatus |
+---------------------+-------+---------+---------+
| 1017125767709982720 | java | 1001 | 1 |
| 1017125769383510016 | java | 1001 | 1 |
mysql> select * from course_1;
+---------------------+-------+---------+---------+
| cid | cname | user_id | cstatus |
+---------------------+-------+---------+---------+
| 1017125767709982720 | java | 1001 | 1 |
| 1017125769383510016 | java | 1001 | 1 |
这里可以看到,在 ShardingProxy 中就增加了一个 Sharding_db 库,包含了配置的逻辑表。
另外,这也解释了在使用 ShardingJDBC 时,大家经常会问的一个问题,就是对于数据库中没有配置虚拟表的真实表,要怎么查。这里就给出了答案。
接下来,在 ShardingProxy 的其他配置文件中,基本都给出了各种功能的示例配置。你都可以去尝试一下。
二、 ShardingSphere 中的分布式事务机制如果你比较仔细,会发现,在之前的配置中,server.yaml 中的 rules 部分,还有一个不太眼熟的配置 TRANSACTION 分布式事务管理器。
rules:
- !TRANSACTIONdefaultType: XAproviderType: Atomikos

由于 ShardingSphere 是需要操作分布式的数据库集群,所以数据库内部的本地事务机制是无法保证 ShardingProxy 中的事务安全的,这就需要引入分布式事务管理机制,保证 ShardingProxy 中的 SQL 语句执行的原子性。也就是说,在 ShardingProxy 中打开分布式事务机制后,你就不需要考虑 SQL 语句执行时的分布式事务问题了。
1、什么是 XA 事务?
这其中 XA 是由 X/Open Group 组织定义的,处理分布式事务的标准。主流的关系型数据库产品都实现了 XA 协议。例如,MySQL 从 5.0.3 版本开始,就已经可以直接支持 XA 事务了。但是要注意,只有 InnoDB 引擎才提供支持:
//1、 XA START|BEGIN 开启事务,这个 test 就相当于是事务 ID,将事务置于 ACTIVE 状态 XA START 'test';
//2、对一个 ACTIVE 状 态的 XA 事务,执行构成事务的 SQL 语句。
insert into dict values(1,'t','test');//business sql//3、发布一个 XA END 指令,将事务置于 IDLE 状态 XA END 'test'; //事务结束//4、对于 IDLE 状态的 XACT 事务 ,执行 XA PREPARED 指令 将事务置于 PREPARED 状态。
//也可以执行 XA COMMIT 'test' ON PHASE 将预备和提交一起操作。
XA PREPARE 'test'; //准备事务//PREPARED 状态的事务可以用 XA RE COVER 指令列出。列出的事务 ID 会包含 gtrid,bqual,formatID 和 data 四个字段。
XA RECOVER;
//5、对于 PREP ARED 状态的 XA 事务,可以进行提交或者回滚。
XA COMMIT 'test'; //提交事务 XA ROLLBACK 'test'; //回滚事务。
在这个标准下有多种具体的实现框架。 ShardingSphere 集成了 Atomikos、Bitronix 和 Narayana 三个框架。其中在 ShardingProxy 中默认只集成了 Atomikos 实现。

2、实战理解 XA 事务回到之前的 ShardingJDBC 示例项目,我们做一个简单的示例来理解一下 XA 事务。
引入 Maven 依赖

<!--XA 分布式事务 -->
<dependency><groupId>org.apache.shardingsphere</groupId><spanrtifactId>shardingsphere-transaction-xa-core</artifactId><version>5.2.1</version><exclusions><exclusion><spanrtifactId>transactions-jdbc</artifactId><groupId>com.atomikos</groupId></exclusion><exclusion><spanrtifactId>transactions-jta</artifactId><groupId>com.atomikos</groupId></exclusion></exclusions></dependency><!-- 版本滞后了 --><dependency><spanrtifactId>transactions-jdbc</artifactId><groupId>com.atomikos</groupId><version>5.0.8</version></dependency><dependency><spanrtifactId>transactions-jta</artifactId><groupId>com.atomikos</groupId><version>5.0.8</version></dependency><!-- 使用 XA 事务时,可以引入其他几种事务管理器 --><!-- <dependency>--><!-- <groupId>org.apache.shardingsphere</groupId>--><!-- <spanrtifactId>shardingsphere-transaction-xa-bitronix</artifactId>--><!-- <version>5.2.1</version>--><!-- </dependency>--><!-- <dependency>--><!-- <groupId>org.apache.shardingsphere</groupId>--><!-- <spanrtifactId>shardingsphere-transaction-xa-narayana</artifactId>--><!-- <version>5.2.1</version>--><!-- </dependency>-->配置事务管理器@Configuration@EnableTransactionManagementpublic class TransactionConfiguration {@Beanpublic PlatformTransactionManager txManager(final DataSource dataSource) {return new DataSourceTransactionManager(dataSource);
}}然后就可以写一个示例

public class MySQLXAConnectionTest {public static void main(String[] args) throws SQLException {//true 表示打印 XA 语句,,用于调试 boolean logXaCommands = true;
// 获得资源管理器操作接口实例 RM1Connection conn1 = DriverManager.getConnection("jdbc:mysql://localhost:3306/coursedb?
serverTimezone=UTC", "root", "root");
XAConnection xaConn1 = new MysqlXAConnection((com.mysql.cj.jdbc.JdbcConnection) conn1,logXaCommands);
XAResource rm1 = xaConn1.getXAResource();
// 获得资源管理器操作接口实例 RM2Connection conn2 = DriverManager.getConnection("jdbc:mysql://localhost:3306/coursedb2?
serverTimezone=UTC", "root", "root");
XAConnection xaConn2 = new MysqlXAConnection((com.mysql.cj.jdbc.JdbcConnection) conn2,logXaCommands);
XAResource rm2 = xaConn2.getXAResource();
// AP 请求 TM 执行一个分布式事务,TM 生成全局事务 idbyte[] gtrid = "g12345".getBytes();
int formatId = 1;
try {/ / ==============分别执行 RM1 和 RM2 上的事务分支====================// TM 生成 rm1 上的事务分支 idbyte[] bqual1 = "b00001".getBytes();
Xid xid1 = new MysqlXid(gtrid, bqual1, formatId);
// 执行 rm1 上的事务分支 rm1.start(xid1, XAResource.TMNOFLAGS);//One of TMNOFLAGS, TMJOIN, or TMRESUME.PreparedStatement ps1 = conn1.prepareStatement("INSERT INTO `dict` VALUES (1, 'T','测试 1');");
ps1.execute();
rm1.end(xid1, XAResource.TMSUCCESS);
// TM 生成 rm2 上的事务分支 idbyte[] bqual2 = "b00002".getBytes();
Xid xid2 = new MysqlXid(gtrid, bqual2, formatId);
// 执行 rm2 上的事务分支 rm2.start(xid2, XAResource.TMNOFLAGS);
PreparedStatement ps2 = conn2.prepareStatement("INSERT INTO `dict` VALUES (2, 'F','测试 2');");
ps2.execute();
rm2.end(xid2, XAResource.TMSUCCESS);
// ===================两阶段提交====== ==========================// phase1:询问所有的 RM 准备提交事务分支 int rm1_prepare = rm1.prepare(xid1);
int rm2_prepare = rm2.prepare(xid2);
// phase2:提交所有事务分支 boolean onePhase = false ; //TM 判断有 2 个事务分支,所以不能优化为一阶段提交 if (rm1_prepare == XAResource.XA_OK&& rm2_prepare == XAResource.XA_OK) {//所有事务分支都 prepare 成功,提交所有事务分支 rm1.commit(xid1, onePhase);
rm2.commit(xid2, onePhase);
} else {//如果有事务分支没有成功,则 回滚 rm1.rollback(xid1);
rm1.rollback(xid2);
}} catch (XAException e) {// 如果出现异常,也要进行 回滚 e.printStackTrace();
}}}

这其中,XA 标准规范了事务 XID 的格式。有三个部分: gtrid [, bqual [, formatID ]] 其中 gtrid 是一个全局事务标识符 global transaction identifierbqual 是一个分支限定符 branch qualifier 。如果没有提供,会使用默认值就是一个空字符串。
formatID 是一个数字,用于标记 gtrid 和 bqual 值的格式,这是一个正整数,最小为 0,默认值就是 1。
但是使用 XA 事务时需要注意以下几点:
XA 事务无法自动提交 XA 事务效率非常低下,全局事务的状态都需要持久化。性能非常低下,通常耗时能达到本地事务的 10 倍。
XA 事务在提交前出现故障的话,很难将问题隔离开。
3、如何在 ShardingProxy 中使用另外两种事务管理器?
例如如果希望在 ShardingProxy 中使用 narayana 事务管理器,只需要两个步骤:
1、将 narayana 的事务集成 Jar 包 shardingsphere-transaction-xa-narayana-5.2.1.jar 放入到 ShardingProxy 的 lib 目录下。
这个 jar 包可以通过 Maven 依赖下载 2、在 server.yaml 中就可以将事务的 Provider 配置成 Narayanarules:
- !TRANSACTIONdefaultType: XAproviderType: Narayana 这个字符串 Narayana 是哪里来的?按照之前的思路,看一下 XATransactionManagerProvider 的实现类你就知道了。
但是要注意有些组件版本冲突的问题!最近几个 ShardingSphere 的版本太新了,有些依赖没有维护好。
三、 ShardingProxy 集群化部署 1、理解 ShardingProxy 运行模式在之前测试中,对于 server.yaml 文件,还有一段 mode 配置,没有打开注释。这是干什么用的?
#mode:
# type: Cluster
# repository:
# type: ZooKeeper
# props:
# namespace: governance_ds
# server-lists: localhost:2181
# retryIntervalMilliseconds: 500
# timeToLiveSeconds: 60
# maxRetries: 3
# operationTimeoutMilliseconds: 500

这个表示 ShardingSphere 的运行模式。简单理解也就是 ShardingSphere 怎么管理这么多复杂的配置信息。
ShardingSphere 支持两种运行模式,Standalone 独立模式和 Cluster 集群模式。
在 Standalone 独立模式下,ShardingSphere 不需要考虑其他实例的影响,直接在内存中管理核心配置规则就可以了。他是 ShardingSphere 默认的运行模式。
而在 Cluster 集群模式下,ShardingSphere 不光要考虑自己的配置规则,还需要考虑如何跟集群中的其他实例同步自己的配置规则。这就需要引入第三方组件来提供配置信息同步。 ShardingSphere 目前支持的配置中心包括:
Zookeeper、etcd、Nacos、Consule。但是在 ShardingSphere 分库分表的场景下,这些配置信息几乎不会变动,访问频率也不会太高。所以,最为推荐的,是基于 CP 架构的 Zookeeper。另外,如果应用的本地和 Zookeeper 中都有配置信息,那么 ShardingSphere 会以 Zookeeper 中的配置为准。
在进行选择时,Standalone 适用于小型项目或对性能要求较高的场景,比较适合配合 ShardingJDBC 使用。 Cluster 适合大规模集群环境,比较适合配合 ShardingProxy 使用。
2、使用 Zookeeper 进行集群部署接下来我们可以基于 Zookeeper 部署一下 ShardingProxy 集群,看一下 ShardingSphere 需要同步的配置有哪些。
我们只需要在本地部署一个 Zookeeper,然后将 server.yaml 中的 mode 部分解除注释:
mode:
type: Clusterrepository:
type: ZooKeeperprops:
namespace: governance_dsserver-lists: 192.168.65.212:2181retryIntervalMilliseconds: 500timeToLiveSeconds: 60maxRetries: 3operationTimeoutMilliseconds: 500 启动 ShardingProxy 服务后,可以看到 Zookeeper 注册中心的信息如下是:

namespace├──rules # 全局规则配置├──props # 属性配置├──metadata # Metadata 配置├ ├──${databaseName} # 逻辑数据库名称├ ├ ├──schemas # Schema 列表├ ├ ├ ├──${schemaName} # 逻辑 Schema 名称├ ├ ├ ├ ├──tables # 表结构配置├ ├ ├ ├ ├ ├──${tableName}├ ├ ├ ├ ├ ├──...├ ├ ├ ├──...├ ├ ├──versions # 元数据版本列表├ ├ ├ ├ ├──views # 视图结构配置├ ├ ├ ├ ├ ├──${viewName}├ ├ ├ ├ ├ ├──...├ ├ ├ ├──${versionNumber} # 元数据版本号├ ├ ├ ├ ├──dataSources # 数据源配置├ ├ ├ ├ ├──rules # 规则配置├ ├ ├ ├──...├ ├ ├──active_version # 激活的元数据版本号├ ├──...├──nodes├ ├──compute_nodes├ ├ ├──online├ ├ ├ ├──proxy├ ├ ├ ├ ├──UUID # Proxy 实例唯一标识├ ├ ├ ├ ├──....├ ├ ├ ├──jdbc├ ├ ├ ├ ├──UUID # JDBC 实例唯一标识├ ├ ├ ├ ├──....├ ├ ├──status├ ├ ├ ├──UUID├ ├ ├ ├──....├ ├ ├──worker_id├ ├ ├ ├──UUID├ ├ ├ ├──....├ ├ ├──process_trigger├ ├ ├ ├──process_list_id:UUID├ ├ ├ ├──....├ ├ ├──labels├ ├ ├ ├──UUID├ ├ ├ ├──....├ ├──storage_nodes├ ├ ├──${databaseName.groupName.ds}├ ├ ├──${databaseName.groupName.ds}而在 rules 部分,就是我们配置的 ShardingProxy 的核心属性

- !AUTHORITYprovider:
type: ALL_PERMITTEDusers:
- root@%:root- sharding@%:sharding- !TRANSACTIONdefaultType: XAproviderType: Atomikos- !SQL_PARSERparseTreeCache:
initialCapacity: 128maximumSize: 1024sqlCommentParseEnabled: truesqlStatementCache:
initialCapacity: 2000maximumSize: 65535 而分库分表的信息,则配置在/governance_ds/metadata/sharding_db/versions/0/rules 节点下- !SHARDINGkeyGenerators:
alg_snowflake:
type: SNOWFLAKEshardingAlgorithms:
course_db_alg:
props:
sharding-count: 2type: MODcourse_tbl_alg:
props:
algorithm-expression: course_$->{cid%2+1}type: INLINEtables:
course:
actualDataNodes: m${0..1}.course_${1..2}databaseStrategy:
standard:
shardingAlgorithmName: course_db_algshardingColumn: cidkeyGenerateStrategy:
column: cidkeyGeneratorName: alg_snowflakelogicTable: coursetableStrategy:
standard:
shardingAlgorithmName: course_tbl_algshardingColumn: cid3、统一 ShardingJDBC 和 ShardingProxy 配置信息这时,回过头来想一想,既然 ShardingProxy 可以通过 Zookeeper 同步配置信息,那么我们可不可以在 ShardingJDBC 中也采用 Zookeeper 的配置呢?当然是可以的。
1、通过注册中心同步配置

第一种简单的思路就是将 ShardingProxy 中的 mod 部分配置移植到之前的 ShardingJDBC 示例中。
将 application.properties 中的配置信息全部删除,只配置 Zookeeper 地址:
spring.shardingsphere.mode.type=Clusterspring.shardingsphere.mode.repository.type=ZooKeeperspring.shardingsphere.mode.repository.props.namespace=governance_dsspring.shardingsphere.mode.repository.props.server-lists=localhost:2181spring.shardingsphere.mode.repository.props.retryIntervalMilliseconds=600spring.shardingsphere.mode.repository.props.timeToLiveSecoonds=60spring.shardingsphere.mode.repository.props.maxRetries=3spring.shardingsphere.mode.repository.props.operationTimeoutMilliseconds=500 然后,就可以继续验证对 course 表的分库分表操作了。
有一个小问题需要注意下,如果在 ShardingJDBC 中读取配置中心的配置,需要使用 spring.shardingsphere.database.name 指定对应的虚拟库。这个参数如果不配置的话,默认是 logic_db。
2、直接使用 ShardingProxy 提供的 JDBC 驱动读取配置文件 ShardingSphere 一直以来都是通过兼容 MySQL 或者 PostgreSQL 服务的方式,提供分库分表功能。应用端可以通过 MySQL 或者 PostgreSQL 的 JDBC 驱动来访问 ShardignSphereDataSource。而在当前版本中,ShardingSphere 则在这条道路上又往前进了一大步。直接提供了自己的 JDBC 驱动。
例如在之前 ShardingJDBC 的 classpath 下增加一个 config.xml,然后将我们之前在 ShardingProxy 中的几个关键配置整合到一起

rules:
- !AUTHORITYusers:
- root@%:root- sharding@:shardingprovider:
type: ALL_PERMITTED- !TRANSACTIONdefaultType: XAproviderType: Atomikos- !SQL_PARSERsqlCommentParseEnabled: truesqlStatementCache:
initialCapacity: 2000maximumSize: 65535parseTreeCache:
initialCapacity: 128maximumSize: 1024- !SHARDINGtables:
course:
actualDataNodes: m${0..1}.course_${1..2}databaseStrategy:
standard:
shardingColumn: cidshardingAlgorithmName: course_db_algtableStrategy:
standard:
shardingColumn: cidshardingAlgorithmName: course_tbl_algkeyGenerateStrategy:
column: cidkeyGeneratorName: alg_snowflakeshardingAlgorithms:
course_db_alg:
type: MODprops:
sharding-count: 2course_tbl_alg:
type: INLINEprops:
algorithm-expression: course_$->{cid%2+1}keyGenerators:
alg_snowflake:
type: SNOWFLAKEprops:
max-connections-size-per-query: 1kernel-executor-size: 16 # Infinite by default.proxy-frontend-flush-threshold: 128 # The default value is 128.proxy-hint-enabled: falsesql-show: falsecheck-table-metadata-enabled: false
# Proxy backend query fetch size. A larger value may increase the memory usage of
ShardingSphere Proxy.
# The default value is -1, which means set the minimum value for different JDBC drivers.
proxy-backend-query-fetch-size: -1proxy-frontend-executor-size: 0 # Proxy frontend executor size. The default value is 0,which means let Netty decide.
# Available options of proxy backend executor suitable: OLAP(default), OLTP. The OLTP

option may reduce time cost of writing packets to client, but it may increase the latency ofSQL execution
# and block other clients if client connections are more than `proxy-frontend-executor-
size`, especially executing slow SQL.proxy-backend-executor-suitable: OLAPproxy-frontend-max-connections: 0 # Less than or equal to 0 means no limitation.
# Available sql federation type: NONE (default), ORIGINAL, ADVANCED
sql-federation-type: NONE
# Available proxy backend driver type: JDBC (default), ExperimentalVertx
proxy-backend-driver-type: JDBCproxy-mysql-default-version: 8.0.20 # In the absence of schema name, the default versionwill be used.proxy-default-port: 3307 # Proxy default port.proxy-netty-backlog: 1024 # Proxy netty backlog.databaseName: sharding_dbdataSources:
m0:
#这个参数必须新增
dataSourceClassName: com.zaxxer.hikari.HikariDataSourceurl: jdbc:mysql://127.0.0.1:3306/coursedb?serverTimezone=UTC&useSSL=falseusername: rootpassword: rootconnectionTimeoutMilliseconds: 30000idleTimeoutMilliseconds: 60000maxLifetimeMilliseconds: 1800000maxPoolSize: 50minPoolSize: 1m1:
#这个参数必须新增
dataSourceClassName: com.zaxxer.hikari.HikariDataSourceurl: jdbc:mysql://127.0.0.1:3306/coursedb2?serverTimezone=UTC&useSSL=falseusername: rootpassword: rootconnectionTimeoutMilliseconds: 30000idleTimeoutMilliseconds: 60000maxLifetimeMilliseconds: 1800000maxPoolSize: 50minPoolSize: 1 然后,可以直接用 JDBC 的方式访问带有分库分表的虚拟库。
public class ShardingJDBCDriverTest {@Testpublic void test() throws ClassNotFoundException, SQLException {String jdbcDriver = "org.apache.shardingsphere.driver.ShardingSphereDriver";
String jdbcUrl = "jdbc:shardingsphere:classpath:config.yaml";
String sql = "select * from sharding_db.course";
Class.forName(jdbcDriver);
try(Connection connection = DriverManager.getConnection(jdbcUrl);) {Statement statement = connection.createStatement();
ResultSet resultSet = statement.executeQuery(sql);
while (resultSet.next()){System.out.println("course cid= "+resultSet.getLong("cid"));
}}}}

官方的说明是 ShardingSphereDriver 读取 config.yaml 时, 这个 config.yaml 配置信息与 ShardingProxy 中的配置文件完全是相同的,你甚至可以直接将 ShardingProxy 中的配置文件拿过来用。但是从目前版本来看,还是有不少小问题的。静待后续版本跟踪把。
到这里,你对于之前介绍的 ShardingSphere 的混合架构,有没有更新的了解?
四、 ShardingProxy 功能扩展其实到这,你应该已经对 ShardingProxy 非常熟练了。最后就补充够一个在 ShardingProxy 中进行自定义扩展的方式。在 ShardingProxy 中,只需要将自定义的扩展功能按照 SPI 机制的要求打成 jar 包,就可以直接把 jar 包放入 lib 目录,然后就配置使用了。
例如,之前在 ShardingJDBC 章节我们已经创建了一个自己扩展的主键生成策略。 MyKeyGeneratorAlgorithm

public class MyKeyGeneratorAlgorithm implements KeyGenerateAlgorithm {private AtomicLong atom = new AtomicLong(0);
private Properties props;
@Overridepublic Comparable<?> generateKey() {LocalDateTime ldt = LocalDateTime.now();
String timestampS = DateTimeFormatter.ofPattern("HHmmssSSS").format(ldt);
return Long.parseLong(""+timestampS+atom.incrementAndGet());
}@Overridepublic Properties getProps() {return this.props;
}public String getType() {return "MYKEY";
}@Overridepublic void init(Properties props) {this.props = props;
}}然后,我们只需要将这个类以及对应的 SPI 文件打成一个 Jar 包,放到 ShardingProxy 的 lib 目录下就可以使用了。使用的方式跟在 ShardingJDBC 中一样,配置到主键生成算法中就行。这里就不多说了。
只补充一个在之前的 ShardingJDBC 项目中,单独打功能扩展 jar 包的方式。在 pom.xml 中引入 maven-jar-plugin 插件就可以了。
<build><plugins><!-- 将 SPI 扩展功能单独打成 jar 包 --><plugin><groupId>org.apache.maven.plugins</groupId><spanrtifactId>maven-jar-plugin</artifactId><version>3.2.0</version><executions><execution><id>ShardingSPIDemo</id><phase>package</phase><goals><goal>jar</goal></goals><configuration><classifier>spiextention</classifier><includes><include>com/roy/shardingDemo/algorithm/*</include><include>META-INF/services/*</include></includes></configuration></execution></executions></plugin></plugins></build>

### 五、分库分表数据迁移方案对于分库分表场景,还有一个非常让人头疼的事情,就是数据迁移。之前项目没有分库分表,现在数据大了之后要进行分库分表改造。或者数据采用取模分片,发现数据量太大了,需要增加数据分片数量,等等这些场景都需要进行数据迁移。而分库分表通常面临的就是海量数据的场景,这使得数据迁移通常是一个非常庞大,非常耗时的工作。业界有很多零迁移数据扩缩容方案可以用来预防未来可能需要的数据迁移工作。但是,如果你没有提前进行设计,在调整分片方案时,确实需要进行数据迁移,应该怎么办呢?
数据迁移的难点往往不在于数据怎么转移,而是在数据转移的过程中,如何保证不影响业务正常进行。通常的思路都是冷热数据分开迁移。冷数据是指那些存量的历史数据。这一部分数据往往数据量非常大,不可能一次性迁移完成,那就只能用定时任务的方式,一点点的逐步完成迁移。热数据是指那些业务进行过程当中产生的实时数据。这一部分数据就要保证数据迁移过程中实时双写。在冷数据迁移过程中,既要写入旧数据库当中,保证业务正常运行,同时又要写入新的数据库集群当中,保证数据正常更新。等冷数据迁移完成后,再将旧数据库完全淘汰,用新的数据库集群承载业务。
目标清晰了,具体怎么设计过渡方案呢?实际上,你不是在孤军作战,ShardingSphere 也在考虑这个问题。
ShardingSphere 已经包含了一个子项目 ElasticJob 可以帮助定制定时任务调度。在 ShardingSphere 未来的规划中,也设计一个 Scaling 组件。预计结合 ElasticJob 定制出一个比较标准的数据迁移指导方案。但是,在这之前,我们其实可以利用 ShardingSphere 的混合架构来辅助进行分库分表数据迁移。
![](<!-- [svg placeholder removed] -->)

热数据可以在旧业务数据通道外,通过 ShardingJDBC 往新的数据库进行实时双写。在这里主要是要考虑尽量少的影响旧业务的数据通道。而我们要做的, 就是用一个 ShardingSphereDataSource,去替换旧的 DataSource。首先可以在应用中配置一个 ShardingJDBC 数据双写库。在这个库中主要是让核心业务表能够保持在新旧两套数据库集群中同时进行双写。在这个过程中,旧的业务通道不需要做任何修改,只要在 ShardingJDBC 数据双写库中针对要迁移的核心业务表配置分片规则这就行。 数据双写可以通过定制分片算法实现。
配置完数据双写后,就需要针对新数据库集群配置,配置一个 ShardingJDBC 数据写入库,主要完整针对细新数据库集群的数据分片。这个 ShardingJDBC 数据写入库可以使用 ShardingSphere 的 JDBC 来创建,然后作为一个真实库,配置到之前的数据双写库当中,这样就可以完成针对新数据库集群的数据分片写入冷数据部分主要是查询旧数据库中的数据,按照新的数据分片规则,转移到新数据库集群当中。这部分数据通常非常巨大,对内存的消耗非常大。所以可以通过定时任务进行增量更新,每次只读一部分数据。然后,为了简化数据转移的逻辑,可以搭建一个 ShardingProxy 服务,用来完成针对新数据库集群的分片规则。这样定时任务的逻辑就比较简单了,只要从一个 MySQL 服务读数据,然后写入另一个 MySQL 服务就可以了。而为了保持在写入新数据库集群时,与热数据保持相同的分片逻辑,ShardingProxy 与 ShardingJDBC 数据写入库之间,可以通过 ShardingSphere 的管理中心来保持规则同步。
这样,整个数据迁移过程中,旧的业务数据通道几乎不需要做任何改变。等数据迁移完成后,只要把 ShardingJDBC 数据写入库保留下来,把 ShardingJDBC 数据双写库和旧数据通道直接删掉即可。在整个迁移过程中,对应用来说,都只是访问一个 DataSource,只不过是 DataSource 的具体实例根据配置做了变动而已,业务层面几乎不需要做任何修改。
当然,具体实施时,还是有很多具体的细节需要你自己去补充的。例如对于业务 SQL 需要做梳理。如果原本只是访问一个 MySQL 服务,而 SQL 语句写得比较放⻜自我的话,那就需要按照 ShardingJDBC 的要求进行调整,尽量不要使用 ShardingSphere 不支持的 SQL 语句。
六、章节总结到这里,ShardingSphere 的主要功能模块我们就介绍得差不多了。但是,ShardingSphere 是一个生态,所以,还有一些平常开发过程中用得不是太多的功能,比如像影子库,这里就不多做介绍了。有兴趣希望你按照我们这个路线,自己进行尝试。虽然现在新的版本还不太稳定,有很多隐藏的坑,但是,通过你自己的尝试,才能真正加深对于分库分表场景的理解。
另外,还是像之前一直强调的,ShardingSphere 的重点是扩展。所以,理解 ShardingSphere 的这些功能扩展点,并在真实开发过程中进行自定义扩展,这应该是比学习 ShardingSphere 的 API 更重要的事情。
四、登堂入室:深入理解 ShardingProxy 服务端分库分表.md

