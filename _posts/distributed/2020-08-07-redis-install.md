---
title: "超详细Redis7.X 安装教程"
description: >
    🚛 超详细Redis .X 安装教程 Redis 安装 1. 本教程将演示在 linux 环境下安装 Redis7,给大家最简单,最快 捷的安装方式,其中包括单机部署、主从部署、哨兵部署、集群 部署的安装以及相应的架构介绍。 单机部署 1.1. 检查安装 gcc 环境 1.1.1. Redis是由C语言编写的,它的运行需要C环境,因此我们需要先 安装gcc。 关闭防火墙 -- systemctl
author: hsc
date: 2020-08-07 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', 'Redis', 'Kafka', 'RocketMQ', 'Netty', 'ElasticSearch', 'ShardingSphere']
toc: true
---

> 本文整理自《四、分布式专题》课程笔记，共 42 页。

🚛 超详细Redis .X 安装教程
Redis 安装
1.
本教程将演示在 linux 环境下安装 Redis7,给大家最简单,最快
捷的安装方式,其中包括单机部署、主从部署、哨兵部署、集群
部署的安装以及相应的架构介绍。
单机部署
1.1.
检查安装 gcc 环境
1.1.1.
Redis是由C语言编写的,它的运行需要C环境,因此我们需要先
安装gcc。
关闭防火墙
--
systemctl stop firewalld.service
状态
--
firewall-cmd --state
卸载防火墙
--
yum remove firewalld
检查版本
--
gcc --version
安装
-- gcc
yum install gcc
1

下载安装 Redis
1.1.2.
安装应用养成良好习惯,文件归类
--
mkdir -p /opt/software/redis
进入 文件夹,使用 下载
-- redis wget
cd /opt/software/redis
wget https://download.redis.io/redis-stable.tar.g
z
解压下载的 包
-- redis
tar -xzf redis-stable.tar.gz
进入 目录,然后使用 编译并安
-- redis-stable make install
装,安装完成后 会生成相应的服务
/usr/local/bin
cd redis-stable
make install
检查是否成功生成
--
ll /usr/local/bin
2

文件介绍:
redis-benchmark:性能测试工具
redis-check-aof:修复有问题的 aof 文件
redis-check-rdb:修复有问题的rdb文件
redis-sentinel:Redis集群使用
redis-server:Redis服务器启动命令
redis-cli:客户端,操作入口
启动 Redis
1.1.3.
到这里其实我们可以在使用 /opt/software/redis/redis-
stable/src 或者 /usr/local/bin 目录下的 redis-server 启动
Redis 服务了。
源码路径下启动
Redis
./src/redis-server
使用 路径下启动(该目录下)
usr/local/bin
redis-server
3

配置Redis
1.1.4.
前面的启动方式无法再后台运行,退出之后直接关闭了 Redis 服
务,所以我们还需要针对 Redis 做一些设置。
-- 修改当前Redis目录下的 Reids.conf 文件
vim redis.conf
需要修改的内容如下:如果大家使用 vim 打开后没有行号,可以
在打开 vim 后输入:“:set number”。
4

行,修改
bind * -::* #87 bin
项, 支持远程连接
d * -::*
行,开启守
daemonize yes #309
护进程,后台运行
logfile /opt/software/redis/redis-stable/redis.lo
行,指定日志文件目录
g #355
行,指定工
dir /opt/software/redis #510
作目录
行,给默认
requirepass 1qaz@WSX #1044
用户设置密码,主要是使用 连接
redis-cli redis-server
时,需要通过密码校验。自行学习,可以不设置。
行,允许远
protected-mode no #111
程连接 如果不设置密码必须讲此设置关闭。
修改完成后,使用配置文件启动 Redis,并使用 redis-cli 连接测
试,需要注意由于前面我们配置了安全密码,所以连接后需要先
验证密码,否则会报错。
redis-server redis.conf
redis-cli
auth 1qaz@WSX
退出 OR 关闭 redis
1.1.5.
5

退出
-- redis
quit
关闭
-- redis
redis-cli shutdown
主从部署(Master-Slave Replication)
1.2.
主从复制,是指将一台Redis服务器的数据,复制到其他的Redis
服务器。前者称为主节点(Master),后者称为从节点(Slave);数
据的复制是单向的,只能由主节点到从节点。默认情况下,每台
Redis服务器都是主节点;且一个主节点可以有多个从节点(或没
有从节点),但一个从节点只能有一个主节点。
主从复制的作用
1.2.1.
a)数据冗余:主从复制实现了数据的热备份,是持久化之外的一
种数据冗余方式。
b)故障恢复:当主节点出现问题时,可以由从节点提供服务,实
6

现快速的故障恢复;实际上是一种服务的冗余。
c)负载均衡:在主从复制的基础上,配合读写分离,可以由主节
点提供写服务,由从节点提供读服务(即写Redis数据时应用连接
主节点,读Redis数据时应用连接从节点),分担服务器负载;尤
其是在写少读多的场景下,通过多个从节点分担读负载,可以大
大提高Redis服务器的并发量。
d)高可用基石:除了上述作用以外,主从复制还是哨兵和集群能
够实施的基础,因此说主从复制是Redis高可用的基础。
主从复制部署
1.2.2.
整体架构图
主节点不需要做任何改变,从节点都需要修改配置加上主节点信
息,配置完成后,可以再主库检查从节点信息
1 # 添加主节点信息
2 replicaof 192.168.75.129 6379
7

1 -- 主节点查看从节点信息
2 info Replication
主从复制缺点
1.2.3.
复制延时,信号衰减
●
由于所有的写操作都是现在master上操作,然后同步更新
到slave上,所以从master同步到slave机器上有一定的延迟,
当系统很繁忙的时候,延迟问题会更加严重,slave机器数量的
增加也会使这个问题更加严重。
master挂了如何办?
●
8

默认情况下,不会在slave节点中自动重选一个master,每
次都要人工干预。
哨兵部署(Sentinel)
1.3.
Redis的主从复制主要用于实现数据的冗余备份和读分担,并不是
为了提供高可用性。因此在系统高可用方面,单纯的主从架构无
法很好的保证整个系统高可用
哨兵模式的原理
1.3.1.
Redis哨兵模式是通过在独立的哨兵节点上运行特定的哨兵进程来
实现的。这些哨兵进程监控主从节点的状态,并在发现故障时自
动完成故障发现和转移,并通知应用方,实现高可用性。
哨兵
1.3.2.
在启动时,每个哨兵节点会执行选举过程,其中一个哨兵节点被
选为领导者(leader),负责协调其他哨兵节点。
选举过程:
●
9

每个在线的哨兵节点都可以成为领导者,每个哨兵节点会向其它
哨兵发is-master-down-by-addr命令,征求判断并要求将自己
设置为领导者;
当其它哨兵收到此命令时,可以同意或者拒绝它成为领导者;
如果哨兵发现自己在选举的票数大于等于num(sentinels)/2+1
时,将成为领导者,如果没有超过,继续选举。
监控主从节点:
●
哨兵节点通过发送命令周期性地检查主从节点的健康状
态,包括主节点是否在线、从节点是否同步等。如果哨兵节
点发现主节点不可用,它会触发一次故障转移。
故障转移:
●
一旦主节点被判定为不可用,哨兵节点会执行故障转移
操作。它会从当前的从节点中选出一个新的主节点,并将其他
从节点切换到新的主节点。这样,系统可以继续提供服务而无
需人工介入。
故障转移过程:
●
由Sentinel节点定期监控发现主节点是否出现了故障:
sentinel会向master发送心跳PING来确认master是否存活,如
果master在“一定时间范围”内不回应PONG 或者是回复了一
个错误消息,那么这个sentinel会主观地(单方面地)认为这个
master已经不可用了。
确认主节点:
●
10

过滤掉不健康的(下线或断线),没有回复过哨兵ping响应
○
的从节点
选择从节点优先级最高的
○
选择复制偏移量最大,此指复制最完整的从节点
○
当主节点出现故障, 由领导者负责处理主节点的故障转
○
移。
客户端重定向:
●
哨兵节点会通知客户端新的主节点的位置,使其能够与
新的主节点建立连接并发送请求。这确保了客户端可以无缝切
换到新的主节点,继续进行操作。
此外,哨兵节点还负责监控从节点的状态。如果从节点出现故
障,哨兵节点可以将其下线,并在从节点恢复正常后重新将其加
入集群。
客观下线
1.3.3.
当主观下线的节点是主节点时,此时该哨兵3节点会通过指令
sentinel is-masterdown-by-addr寻求其它哨兵节点对主节点的
判断,当超过quorum(选举)个数,此时哨兵节点则认为该主节
点确实有问题,这样就客观下线了,大部分哨兵节点都同意下线
操作,也就说是客观下线。
哨兵模式部署
1.3.4.
整体架构图
11

3 个机器都需要修改 sentinel.conf 配置,配置完成之后先从主节
点开始启动哨兵。
1 protected-mode no
行,关闭保护模式
#6
2 daemonize yes
行,指定 为后台启动
#15 sentinel
3 logfile /opt/software/redis/redis-stable/sentin
行,指定日志存放路径
el.log #34
4 dir /opt/software/redis
行,指定数据库存放路径
#73
5 sentinel monitor mymaster 192.168.75.129 6379 2
行,修改 指定该哨兵节点监控 这个主
#93 20.0.0.20:6379
节点,该主节点的名称是 ,最后的 的含义与主节点的
mymaster 2
故障判定有关:至少需要 个哨兵节点同意,才能判定主节点故
2
障并进行故障转移
6 sentinel down-after-milliseconds mymaster 30000
行,判定服务器 掉的时间周期,默认 毫秒
#134 down 30000
( 秒)
30
7 sentinel failover-timeout mymaster 180000
行,故障节点的最大超时时间为 ( 秒)
#234 180000 180
12

启动后检查哨兵状态:
redis-cli -p 26379 info sentinel
故障模拟
可以杀掉主节点的进程,也可以直接停掉主节点服务
--
ps aux | grep redis
redis-cli shutdown
观察哨兵日志, 主节点下线,重新选举 为主节点
-- 129 131
tail -f sentinel.log
重新启动 服务 并观察日志, 加入主从,此时主节点为
-- 129 129
服务
131
redis-server redis.conf
tail -f sentinel.log
redis-cli -p 26379 info sentinel
观察哨兵日志
--
tail -f sentinel.log
停止哨兵
--
redis-cli -p 26379 shutdown
13

切换到 服务,已经为主节点。
-- 131
redis-cli info replication
当触发了哨兵选举之后,会再后台更改 redis.conf 与
sentinel.conf,可以检查每台机器的文件末尾的数据
14

cat redis.conf
cat sentinel.conf
哨兵使用建议
1.3.5.
哨兵节点的数量应为多个,哨兵本身应该集群,保证高可用
●
哨兵节点数应该是奇数
●
各个哨兵结点的配置应一致
●
如果哨兵节点部署在Docker等容器里面,尤其要注意端口号的
●
正确映射
哨兵模式:并不能保证数据零丢失
1.3.6.
复制延迟:
1.
在主从复制中,从节点的数据是异步复制自主节点的。这意
○
味着在主节点故障时,从节点可能还没有完全同步最新的数
据,从而导致数据丢失。
15

故障检测和转移时间:
2.
Sentinel 检测到主节点故障并执行故障转移需要一定的时
○
间。在这段时间内,主节点可能已经接收了一些写操作,但
这些操作尚未被复制到从节点。
网络分区:
3.
在发生网络分区(网络分裂)的情况下,一部分节点可能与
○
主节点失去联系。如果此时主节点继续处理写操作,那么在
网络恢复之前,这些操作可能不会被复制到从节点。
多个从节点同时故障:
4.
如果所有的从节点同时故障或在故障转移之前与主节点失
○
联,那么在主节点故障时,将没有可用的从节点来提升为主
节点。
集群部署(Cluster)
1.4.
Redis 集群是 Redis 的一种分布式运行模式,它通过分片
(sharding)来提供数据的自动分区和管理,从而实现数据的高
可用性和可扩展性。
在集群模式下,数据被分割成多个部分(称为槽或slots),分布
在多个 Redis 节点上。
集群中的节点分为主节点和从节点:主节点负责读写请求和集群
信息的维护;从节点只进行主节点数据和状态信息的复制。
16

Redis集群的作用
1.4.1.
数据分区:数据分区(或称数据分片)是集群最核心的功能。 集群
将数据分散到多个节点,一方面突破了Redis单机内存大小的限
制,存储容量大大增加;
另一方面每个主节点都可以对外提供读服务和写服务,大大提高
了集群的响应能力。 Redis单机内存大小受限问题,在介绍持久
化和主从复制时都有提及;
例如,如果单机内存太大,bgsave和bgrewriteaof的fork操作可
能导致主进程阻塞,主从环境下主机切换时可能导致从节点⻓时
间无法提供服务,全量复制阶段主节点的复制缓冲区可能溢出。
高可用:集群支持主从复制和主节点的自动故障转移(与哨兵类
似);当任一节点发生故障时,集群仍然可以对外提供服务。
Redis集群的数据分片
1.4.2.
Redis集群引入了哈希槽的概念 Redis集群有16384个哈希槽(编
号0-16383) 集群的每个节点负责一部分哈希槽 每个Key通过
CRC16校验后对16384取余来决定放置哪个哈希槽,
通过这个值,去找到对应的插槽所对应的节点,然后直接自动跳
转到这个对应的节点上进行存取操作
以3个节点组成的集群为例: 节点A包含0到5460号哈希槽 节
●
点B包含5461到10922号哈希槽 节点C包含10923到16383号哈
希槽
17

Redis集群的主从复制模型 集群中具有A、B、C三个节点,如
●
果节点B失败了,整个集群就会因缺少5461-10922这个范围的
槽而不可以用。
为每个节点添加一个从节点A1、B1、C1整个集群便有三个Master
节点和三个slave节点组成,在节点B失败后,集群选举B1位为的
主节点继续服务。当B和B1都失败后,集群将不可用
Reids 集群部署
1.4.3.
1.4.3.1. redis 环境简述
Redis Cluster被配置为三主三从模式。这意味着每台服务器上的
两个Redis节点中,一个节点作为主库(master),另一个作为
从库(slave)。
1.4.3.2. redis 集群配置准备
18

创建集群配置文件夹,将下面的配置复制过去,另外两个机器重
--
复这个过程
mkdir -p /opt/software/redis/redis-stable/cluster
mkdir -p /opt/software/redis/cluster
vim ./cluster/redis_6379.conf
vim ./cluster/redis_6380.conf
配置文件准备完成之后,启动所有 服务,用 配
-- redis cluster
置文件
redis-server ./cluster/redis_6379.conf
redis-server ./cluster/redis_6380.conf
检查服务
--
ps aux | grep redis
创建三主三从集群模式,每一个主节点带一个从节点
--
redis-cli --cluster create --cluster-replicas 1 1
92.168.75.129:6379 192.168.75.129:6380 192.168.7
5.131:6379 192.168.75.131:6380 192.168.75.132:637
9 192.168.75.132:6380
查看集群信息
--
redis-cli cluster info
查看单个节点信息
--
redis-cli info replication
查看集群节点身份信息
--
redis-cli cluster nodes
19

停止 服务
-- redis
redis-cli -p 6379 shutdown
redis-cli -p 6380 shutdown
20

6379配置 Shell
允许所有的 地址
# IP
bind * -::*
后台运行
#
daemonize yes
允许远程连接
#
protected-mode no
开启集群模式
#
cluster-enabled yes
集群节点超时时间
#
cluster-node-timeout 5000
配置数据存储目录
#
dir "/opt/software/redis/cluster"
开启 持久化
# AOF
appendonly yes
端口
#
port 6379
日志
# log
logfile "/opt/software/redis/redis-stable/cluste
r/redis6379.log"
集群配置文件
#
cluster-config-file nodes-6379.conf
文件名
# AOF
appendfilename "appendonly6379.aof"
文件名
# RBD
dbfilename "dump6379.rdb"
21

6380配置 Shell
允许所有的 地址
# IP
bind * -::*
后台运行
#
daemonize yes
允许远程连接
#
protected-mode no
开启集群模式
#
cluster-enabled yes
集群节点超时时间
#
cluster-node-timeout 5000
配置数据存储目录
#
dir "/opt/software/redis/cluster"
开启 持久化
# AOF
appendonly yes
端口
#
port 6380
日志
# log
logfile "/opt/software/redis/redis-stable/cluste
r/redis6380.log"
集群配置文件
#
cluster-config-file nodes-6380.conf
文件名
# AOF
appendfilename "appendonly6380.aof"
文件名
# RBD
dbfilename "dump6380.rdb"
22

1.4.3.3. Redis 集群数据读写
连接一个主节点进行写数据
--
redis-cli info replication
直接连接读写可能会出现以下问题,是因为不同的节点的槽位不
--
同,图中就是提示我们去 进行写入数据
132:6379
23

不过我们也可以开启路由规则 ,进行处理
-- -c
redis-cli -c
重新写入数据,恢复正常。
--
set k1 b1
1.4.3.4. 模拟故障转移
注意机器 的区分
-- ip
将 机器的主节点给干掉 的 服务
-- 129 (129 6379 )
redis-cli -p 6379 shutdown
查看 机器从节点工作日志 的 日志
-- 129 (131 6380 )
cat redis6380.log
在切换到 机器上查看当前集群节点信息, 已经升
-- 132 131:6380
为主节点
redis-cli cluster nodes
24

在重新启动 服务
-- 129.6379
redis-server ./cluster/redis_6379.conf
查看 的节点信息,主节点变为从节点
-- 129.6379
redis-cli -p 6379 info replication
观察 日志, 重新加入集群
-- 131.6380 129.6379
25

至此 Redis 部署篇章结束,完结撒花~~~~~
完整的文件目录与配置文件与使用过程中的命令
2.
文件目录
2.1.
手工创建 Shell
应用
/opt/software/redis/ -- Redis
应用根目录
/opt/software/redis/redis-stable -- Redis
集群应用文件目
/opt/software/redis/cluster -- Redis
录 日志,快照等信息
( )
/opt/software/redis/redis-stable/cluster -- Redi
集群配置文件存放路径
s
26

配置文件
2.2.
单机Redis配置文件
2.2.1.
所在目录:/opt/software/redis/redis-stable
27

6379配置 Shell
bind * -::*
protected-mode no
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 300
daemonize yes
pidfile /var/run/redis_6379.pid
loglevel notice
logfile /opt/software/redis/redis-stable/redis.lo
g
databases 16
always-show-logo no
set-proc-title yes
proc-title-template "{title} {listen-addr} {serve
r-mode}"
locale-collate ""
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
rdb-del-sync-files no
dir /opt/software/redis
replica-serve-stale-data yes
replica-read-only yes
repl-diskless-sync yes
repl-diskless-sync-delay 5
repl-diskless-sync-max-replicas 0
repl-diskless-load disabled
28

repl-disable-tcp-nodelay no
replica-priority 100
acllog-max-len 128
lazyfree-lazy-eviction no
lazyfree-lazy-expire no
lazyfree-lazy-server-del no
replica-lazy-flush no
lazyfree-lazy-user-del no
lazyfree-lazy-user-flush no
oom-score-adj no
oom-score-adj-values 0 200 800
disable-thp yes
appendonly no
appendfilename "appendonly.aof"
appenddirname "appendonlydir"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
aof-use-rdb-preamble yes
aof-timestamp-enabled no
slowlog-log-slower-than 10000
slowlog-max-len 128
latency-monitor-threshold 0
notify-keyspace-events ""
hash-max-listpack-entries 512
hash-max-listpack-value 64
list-max-listpack-size -2
list-compress-depth 0
29

set-max-intset-entries 512
set-max-listpack-entries 128
set-max-listpack-value 64
zset-max-listpack-entries 128
zset-max-listpack-value 64
hll-sparse-max-bytes 3000
stream-node-max-bytes 4096
stream-node-max-entries 100
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
hz 10
dynamic-hz yes
aof-rewrite-incremental-fsync yes
rdb-save-incremental-fsync yes
jemalloc-bg-thread yes
主从节点配置
2.2.2.
所在目录:/opt/software/redis/redis-stable
大家可以将不同服务器的端口设置不同的值,以方便区分。
129.6379配置-主节点 Shell
与单机主节点配置一样
30

131.6379配置-从节点 Shell
bind * -::*
protected-mode no
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 300
daemonize yes
pidfile /var/run/redis_6379.pid
loglevel notice
logfile /opt/software/redis/redis-stable/redis.lo
g
databases 16
always-show-logo no
set-proc-title yes
proc-title-template "{title} {listen-addr} {serve
r-mode}"
locale-collate ""
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
rdb-del-sync-files no
dir /opt/software/redis
replicaof 192.168.75.129 6379
replica-serve-stale-data yes
replica-read-only yes
repl-diskless-sync yes
repl-diskless-sync-delay 5
repl-diskless-sync-max-replicas 0
31

repl-diskless-load disabled
repl-disable-tcp-nodelay no
replica-priority 100
acllog-max-len 128
lazyfree-lazy-eviction no
lazyfree-lazy-expire no
lazyfree-lazy-server-del no
replica-lazy-flush no
lazyfree-lazy-user-del no
lazyfree-lazy-user-flush no
oom-score-adj no
oom-score-adj-values 0 200 800
disable-thp yes
appendonly no
appendfilename "appendonly.aof"
appenddirname "appendonlydir"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
aof-use-rdb-preamble yes
aof-timestamp-enabled no
slowlog-log-slower-than 10000
slowlog-max-len 128
latency-monitor-threshold 0
notify-keyspace-events ""
hash-max-listpack-entries 512
hash-max-listpack-value 64
list-max-listpack-size -2
32

list-compress-depth 0
set-max-intset-entries 512
set-max-listpack-entries 128
set-max-listpack-value 64
zset-max-listpack-entries 128
zset-max-listpack-value 64
hll-sparse-max-bytes 3000
stream-node-max-bytes 4096
stream-node-max-entries 100
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
hz 10
dynamic-hz yes
aof-rewrite-incremental-fsync yes
rdb-save-incremental-fsync yes
jemalloc-bg-thread yes
132.6379配置-从节点 Shell
同 配置一样
131.6379
哨兵模式
2.2.3.
所在目录:/opt/software/redis/redis-stable
主从配置无需修改,直接配置 sentinel 文件,3 个机器配置相同
33

26379 Shell
protected-mode no
port 26379
daemonize yes
pidfile /var/run/redis-sentinel.pid
loglevel notice
logfile /opt/software/redis/redis-stable/sentine
l.log
dir /opt/software/redis
sentinel monitor mymaster 192.168.75.129 6379 2
sentinel down-after-milliseconds mymaster 30000
acllog-max-len 128
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 180000
sentinel deny-scripts-reconfig yes
SENTINEL resolve-hostnames no
SENTINEL announce-hostnames no
SENTINEL master-reboot-down-after-period mymaste
r 0
集群
2.2.4.
所在目录:/opt/software/redis/redis-stable/cluster
3 个机器配置相同
34

6379 Shell
允许所有的 地址
# IP
bind * -::*
后台运行
#
daemonize yes
允许远程连接
#
protected-mode no
开启集群模式
#
cluster-enabled yes
集群节点超时时间
#
cluster-node-timeout 5000
配置数据存储目录
#
dir "/opt/software/redis/cluster"
开启 持久化
# AOF
appendonly yes
端口
#
port 6379
日志
# log
logfile "/opt/software/redis/redis-stable/cluste
r/redis6379.log"
集群配置文件
#
cluster-config-file nodes-6379.conf
文件名
# AOF
appendfilename "appendonly6379.aof"
文件名
# RBD
dbfilename "dump6379.rdb"
35

6380 Shell
允许所有的 地址
# IP
bind * -::*
后台运行
#
daemonize yes
允许远程连接
#
protected-mode no
开启集群模式
#
cluster-enabled yes
集群节点超时时间
#
cluster-node-timeout 5000
配置数据存储目录
#
dir "/opt/software/redis/cluster"
开启 持久化
# AOF
appendonly yes
端口
#
port 6380
日志
# log
logfile "/opt/software/redis/redis-stable/cluste
r/redis6380.log"
集群配置文件
#
cluster-config-file nodes-6380.conf
文件名
# AOF
appendfilename "appendonly6380.aof"
文件名
# RBD
dbfilename "dump6380.rdb"
命令
2.2.5.
36

命令汇总 Shell
基础常⻅命
----------------------------------- Redis
令
----------------------------------------
:查看当前库所有的
keys * key
:判断某个 是否存在
exists key key
:查看 值是什么类型
type key key
:删除指定的 数据
del key key
:非阻塞删除,仅仅将 从 元数据中删
unlink key keys keyspace
除,真正的删除会在后续异步中操作
:查看还有多少秒过期, 表示永不过期, 表示已过期
ttl key -1 -2
:秒钟,为给定的 设置过期时间
expire key key
:将当前数据库的 移动到给定的
move key dbindex[0-15] key
数据库 当中
db
:切换数据库 ,默认值为
select dbindex [0-15] 0
:查看当前数据库 的数量
dbsize key
:清空当前库
flushdb
:通杀全部库
flusshall
完整的操作命令
----------------------------------- -
---------------------------------------
关闭防火墙
--
systemctl stop firewalld.service
状态
--
firewall-cmd --state
卸载防火墙
--
yum remove firewalld
单机部署
-------------------------- ---------------
-----------
检查版本
--
gcc --version
37

安装
-- gcc
yum install gcc
安装应用养成良好习惯,文件归类
--
mkdir -p /opt/software/redis
进入 文件夹,使用 下载
-- redis wget
cd /opt/software/redis
wget https://download.redis.io/redis-stable.tar.g
z
解压下载的 包
-- redis
tar -xzf redis-stable.tar.gz
进入 目录,然后使用 编译并安
-- redis-stable make install
装,安装完成后 会生成相应的服务
/usr/local/bin
cd redis-stable
make install
检查是否成功生成
--
ll /usr/local/bin
源码路径下启动
Redis
./src/redis-server
使用 路径下启动(该目录下)
usr/local/bin
redis-server
修改当前 目录下的 文件
-- Redis Reids.conf
vim redis.conf
38

启动 使用密码认证登录
-- Redis,
redis-server redis.conf
redis-cli -a 1qaz@WSX
退出
-- redis
quit
关闭
-- redis
redis-cli shutdown
主从部署
-------------------------- ---------------
-----------
主节点查看从节点信息
--
info Replication
哨兵部署
-------------------------- ---------------
-----------
可以杀掉主节点的进程,也可以直接停掉主节点服务
--
ps aux | grep redis
redis-cli shutdown
观察哨兵日志, 主节点下线,重新选举 为主节点
-- 129 131
tail -f sentinel.log
重新启动 服务 并观察日志, 加入主从,此时主节点为
-- 129 129
服务
131
redis-server redis.conf
tail -f sentinel.log
39

redis-cli -p 26379 info sentinel
观察哨兵日志
--
tail -f sentinel.log
停止哨兵
--
redis-cli -p 26379 shutdown
切换到 服务,已经为主节点。
-- 131
redis-cli info replication
查看文件内容
--
cat redis.conf
cat sentinel.conf
集群部署
-------------------------- ---------------
-----------
创建集群配置文件夹,将下面的配置复制过去,另外两个机器重
--
复这个过程
mkdir -p /opt/software/redis/redis-stable/cluster
mkdir -p /opt/software/redis/cluster
vim ./cluster/redis_6379.conf
vim ./cluster/redis_6380.conf
配置文件准备完成之后,启动所有 服务,用 配
-- redis cluster
置文件
redis-server ./cluster/redis_6379.conf
redis-server ./cluster/redis_6380.conf
40

检查服务
--
ps aux | grep redis
创建三主三从集群模式,每一个主节点带一个从节点
--
redis-cli --cluster create --cluster-replicas 1 1
92.168.75.129:6379 192.168.75.129:6380 192.168.7
5.131:6379 192.168.75.131:6380 192.168.75.132:637
9 192.168.75.132:6380
查看集群信息
--
redis-cli cluster info
查看单个节点信息
--
redis-cli info replication
查看集群节点身份信息
--
redis-cli cluster nodes
停止 服务
-- redis
redis-cli -p 6379 shutdown
redis-cli -p 6380 shutdown
连接一个主节点进行写数据
--
redis-cli info replication
注意机器 的区分
-- ip
将 机器的主节点给干掉 的 服务
-- 129 (129 6379 )
redis-cli -p 6379 shutdown
查看 机器从节点工作日志 的 日志
-- 129 (131 6380 )
41

cat redis6380.log
在切换到 机器上查看当前集群节点信息, 已经升
-- 132 131:6380
为主节点
redis-cli cluster nodes
在重新启动 服务
-- 129.6379
redis-server ./cluster/redis_6379.conf
查看 的节点信息,主节点变为从节点
-- 129.6379
redis-cli -p 6379 info replication
观察 日志, 重新加入集群
-- 131.6380 129.6379
42
