---



title: "Redis数据安全性分析"
description: "整体介绍 Redis 的数据持久化机制 2、RDB 详解 3、AOF 详解 4、混合持久化策略三、 Redis 主从复制 Replica 机制详解 1、Repl"
author: hsc
date: 2024-02-04 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Redis', 'Kafka', '分布式事务']
toc: true



---

### 一、 Redis 性能压测脚本介绍二、 Redis 数据持久化机制详解
1、整体介绍 Redis 的数据持久化机制 2、RDB 详解 3、AOF 详解 4、混合持久化策略三、 Redis 主从复制 Replica 机制详解 1、Replica 是什么?有什么用?
2、如何配置 Replica?
3、如何确定主从状态?从库可以写数据吗?
4、如果 Slave 上已经有数据了,同步时会如何处理?
5、主从复制工作流程 6、主从复制的缺点四、 Redis 哨兵集群 Sentinel 机制详解 1、Sentinel 是什么?有什么用 2、Sentinel 核心配置 3、解析 Sentinel 工作原理 4、Sentinel 的缺点五、 Redis 集群 Cluster 机制详解 1、Cluster 是什么?有什么用?
2、Cluster 的核心配置 3、详解 Slot 槽位 4、Redis 集群选举原理-了解 5、Redis 集群能不能保证数据安全?
六、 Redis 数据安全性方案总结前置课程主要包括 Redis 基础的安装及使用。后续课程,不是教你怎么用 Redis,而是教你怎么把 Redis 用得比别人深一点。
前置目标:搭建 Redis 的主从复制、哨兵集群以及数据集群。
这一章节主要是从数据安全性的⻆度,重新理解 Redis 的集群架构。
一、 Redis 性能压测脚本介绍 Redis 的所有数据是保存在内存当中的,得益于内存高效的读写性能,Redis 的性能是非常强悍的。但是,内存的缺点是断电即丢失,所以,在实际项目中,Redis 一旦需要保存一些重要的数据,就不可能完全使用内存保存数据。因此,在真实项目中要使用 Redis,一定需要针对应用场景,对 Redis 的性能进行估算,从而在数据安全性与读写性能之间找到一个平衡点。
Redis 提供了压测脚本 redis-benchmark,可以对 Redis 进行快速的基准测试。

# 20 个线程,100W 个请求,测试 redis 的 set 指令(写数据)
redis-benchmark -a 123qweasd -t set -n 1000000 -c 20...Summary:
throug hput summary: 116536.53 requests per second ##平均每秒 11W 次写操作。
latency summary (msec):
avg min p50 p95 p99 max0.111 0.032 0.111 0.167 0.215 3.199redis-benchmark 更多参数,使用 redis-benchmark --help 指令查看后续逐步调整 Redis 的各种部署架构后,建议大家自行多进行几次对比测试。
二、 Redis 数据持久化机制详解 1、整体介绍 Redis 的数据持久化机制官网介绍地址: https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/Redis 提供了很多跟数据持久化相关的配置,大体上,可以组成以下几种策略:
无持久化:完全关闭数据持久化,不保证数据安全。相当于将 Redis 完全当做缓存来用 RDB(RedisDatabase):按照一定的时间间隔缓存 Redis 所有数据快照。
AOF(Append Only File):记录 Redis 收到的每一次写操作。这样可以通过操作重演的方式恢复 Redis 的数据 RDB+AOF:同时保存 Redis 的数据和操作。
两种方式的优缺点:

RDB 优点:
1、RDB 文件非常紧凑,非常适合定期备份数据。
2、RDB 快照非常适合灾难恢复。
3、RDB 备份时性能非常快,对主线程的性能几乎没有影响。 RDB 备份时,主线程只需要启动一个负责数据备份的子线程即可。所有的备份工作都由子线程完成,这对主线程的 IO 性能几乎没有影响。
4、与 AOF 相比,RDB 在进行大数据量重启时会快很多。
缺点:
1、RDB 不能对数据进行实时备份,所以,总会有数据丢失的可能。
2、RDB 需要 fork 化子线程的数据写入情况,在 fork 的过程中,需要将内存中的数据克隆一份。如果数据量太大,或者 CPU 性能不是很好,RDB 方式就容易造成 Redis 短暂的服务停用。相比之下,AOF 也需要进行持久化,但频率较低。并且你可以调整日志重写的频率。
AOF 优点:
1、AOF 持久化更安全。例如 Redis 默认每秒进行一次 AOF 写入,这样,即使服务崩溃,最多损失一秒的操作。
2、AOF 的记录方式是在之前基础上每次追加新的操作。因此 AOF 不会出现记录不完整的情况。即使因为一些特殊原因,造成一个操作没有记录完整,也可以使用 redis-check-aof 工具轻松恢复。
3、当 AOF 文件太大时,Redis 会自动切换新的日志文件。这样就可以防止单个文件太大的问题。
4、AOF 记录操作的方式非常简单易懂,你可以很轻松的自行调整日志。比如,如果你错误的执行了一次 FLUSHALL 操作,将数据误删除了。使用 AOF,你可以简单的将日志中最后一条 FLUSHALL 指令删掉,然后重启数据库,就可以恢复所有数据。
缺点:
1、针对同样的数据集,AOF 文件通常比 RDB 文件更大。
2、在写操作频繁的情况下,AOF 备份的性能通常比 RDB 更慢。
整体使用建议:
1、如果你只是把 Redis 当做一个缓存来用,可以直接关闭持久化。

2、如果你更关注数据安全性,并且可以接受服务异常宕机时的小部分数据损失,那么可以简单的使用 RDB 策略。这样性能是比较高的。
3、不建议单独使用 AOF。RDB 配合 AOF,可以让数据恢复的过程更快。
2、RDB 详解
1、 RDB 能干什么 RDB 可以在指定的时间间隔,备份当前时间点的内存中的全部数据集,并保存到餐盘文件当中。通常是 dump.rdb 文件。在恢复时,再将磁盘中的快照文件直接都会到内存里。
由于 RDB 存的是全量数据,你甚至可以直接用 RDB 来传递数据。例如如果需要从一个 Redis 服务中将数据同步到另一个 Redis 服务(最好是同版本),就可以直接复制最近的 RDB 文件。
2、相关重要配置 1> save 策略: 核心配置
# Save the DB to disk.
#
# save <seconds> <changes> [<seconds> <changes> ...]
#
# Redis will save the DB if the given number of seconds elapsed and it
# surpassed the given number of write operations against the DB.
#
# Snapshotting can be completely disabled with a single empty string argument
# as in following example:
#
# save ""
#
# Unless specified otherwise, by default Redis will save the DB:
# * After 3600 seconds (an hour) if at least 1 change was performed
# * After 300 seconds (5 minutes) if at least 100 changes were performed
# * After 60 seconds if at least 10000 changes were performed
#
# You can set these explicitly by uncommenting the following line.
#
# save 3600 1 300 100 60 10000
2> dir 文件目录 3> dbfilename 文件名 默认 dump.rdb4> rdbcompression 是否启用 RDB 压缩,默认 yes。 如果不想消耗 CPU 进行压缩,可以设置为 no5> stop-writes-oin-bgsave-error 默认 yes。如果配置成 no,表示你不在乎数据不一致或者有其他的手段发现和控制这种不一致。在快照写入失败时,也能确保 redis 继续接受新的写入请求。

6>rdbchecksum 默认 yes。在存储快照后,还可以让 redis 使用 CRC64 算法来进行数据校验,但是这样做会增加大约 10%的性能消耗。如果希望获得最大的性能提升,可以关闭此功能。
3、何时会触发 RDB 备份 1> 到达配置文件中默认的快照配置时,会自动触发 RDB 快照 2>手动执行 save 或者 bgsave 指令时,会触发 RDB 快照。 其中 save 方法会在备份期间阻塞主线程。
bgsve 则不会阻塞主线程。但是他会 fork 一个子线程进行持久化,这个过程中会要将数据复制一份,因此会占用更多内存和 CPU。
3> 主从复制时会触发 RDB 备份。
LASTSAVE 指令查看最后一次成功执行快照的时间。时间是一个代表毫秒的 LONG 数字,在 linux 中可以使用 date -d @{timestamp} 快速格式化。
3、AOF 详解 1、AOF 能干什么以日志的形式记录每个写操作(读操作不记录)。只允许追加文件而不允许改写文件。
2、相关重要配置 1> appendonly 是否开启 aof。 默认是不开启的。
2> appendfilename 文件名称。

# The base name of the append only file.
#
# Redis 7 and newer use a set of append-only files to persist the dataset
# and changes applied to it. There are two basic types of files in use:
#
# - Base files, which are a snapshot representing the complete state of the
# dataset at the time the file was created. Base files can be either in
# the form of RDB (binary serialized) or AOF (textual commands).
# - Incremental files, which contain additional commands that were applied
# to the dataset following the previous file.
#
# In addition, manifest files are used to track the files and the order in
# which they were created and should be applied.
#
# Append-only file names are created by Redis following a specific pattern.
# The file name's prefix is based on the 'appendfilename' configuration
# parameter, followed by additional information about the sequence and type.
#
# For example, if appendfilename is set to appendonly.aof, the following file
# names could be derived:
#
# - appendonly.aof.1.base.rdb as a base file.
# - appendonly.aof.1.incr.aof, appendonly.aof.2.incr.aof as incremental files.
# - appendonly.aof.manifest as a manifest file.
appendfilename "appendonly.aof"
Redis7 中,对文件名称做了调整。原本只是一个文件,现在换成了三个文件。 base.rdb 文件即二进制的数据文件。 incr.aof 是增量的操作日志。 manifest 则是记录文件信息的元文件。其实在 Redis7 之前的版本中,aof 文件也会包含二进制的 RDB 部分和文本的 AOF 部分。在 Redis7 中,将这两部分分成了单独的文件,这样,即可以分别用来恢复文件,也便于控制 AOF 文件的大小。

从这几个文件中能够看到, 现在的 AOF 已经具备了 RDB+AOF 的功能。并且,拆分增量文件的方式,也能够进一步控制 aof 文件的大小。
3> appendfsync 同步方式。默认 everysecond 每秒记录一次。 no 不记录(交由操作系统进行内存刷盘)。 always 记录每次操作,数据更安全,但性能较低。
4> appenddirname AOF 文件目录。新增参数,指定 aof 日志的文件目录。 实际目录是 {dir}+{appenddirname}5> auto-aof-rewrite-percentage, auto-aof-rewrite-min-size 文件重写触发策略。默认每个文件 64M, 写到 100%,进行一次重写。
Redis 会定期对 AOF 中的操作进行优化重写,让 AOF 中的操作更为精简。例如将多个 INCR 指令,合并成一个 SET 指令。同时,在 Redis7 的 AOF 文件中,会生成新的 base rdb 文件和 incr.aof 文件。
AOF 重写也可以通过指令 BGREWRITEAOF 手动触发 6> no-appendfsync-on-rewrite aof 重写期间是否同步 3、AOF 文件内容解析

示例:打开 aof 配置,aof 日志文件 appendonly.aof。然后使用 redis-cli 连接 redis 服务,简单执行两个 set 操作。
[root@192-168-65-214 myredis]# redis-cli -a 123qweasdWarning: Using a password with '-a' or '-u' option on the command line interfacemay not be safe.127.0.0.1:6379> keys *(empty array)
127.0.0.1:6379> set k1 v1OK127.0.0.1:6379> set k2 v2OK 然后,就可以打开 appendonly.aof.1.incr.aof 增量文件。里面其实就是按照 Redis 的协议记录了每一次操作。

这就是 redis 的指令协议。 redis 就是通过 TCP 协议,一次次解析各个指令。比如一个 set k1 v1 这样的指令,*3 表示由三个部分组成, 第一个部分 $3 set 表示三个字符⻓度的 set 组成第一个部分。
了解这个协议后,你甚至可以很轻松的自己写一个 Redis 的客户端。例如:

package com.roy.redis;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.Socket;
/*** Author: roy* Description:
**/public class MyRedisClient {OutputStream write;
InputStream reader;
public MyRedisClient(String host,int port) throws IOException {Socket socket = new Socket(host,port);
write = socket.getOutputStream();
reader = socket.getInputStream();
}//auth 123qweasdpublic String auth(String password){//1 组装报文 StringBuffer command = new StringBuffer();
command.append("*2").append("\r\n");//参数数量 command.append("$4").append("\r\n");//第一个参 数⻓度 command.append("AUTH").append("\r\n");//第一个参数值//socket 编程需要关注二进制⻓度。
command.append("$").append(p assword.getBytes().length).append("\r\n");//第二个参数⻓度 co mmand.append(password).append("\r\n");//第二个参数值//2 发送报文到 try {write.write(command.toString().getBytes());
//3 接收 redis 响应 byte[] response = new byte[1024];
reader.read(response);
return new String(response);
} catch (IOException e) {throw new RuntimeException(e);
}}//set k4 v4public String set(String key, String value){//1 组装报文 StringBuffer command = new StringBuffer();
command.append("*3").append("\r\n");//参数数 量 command.append("$3").append("\r\n");//第一个参数⻓度 command.append("SET").append("\r\n");//第一个参数值//socket 编程需要关注二进制⻓度。
command.append("$").append(k ey.getBytes().length).append("\r\n");//第二个参

数⻓度 command.append(key).append("\r\n");//第二个参数值 command.append("$").append(value.getBytes().length).append("\r\n");//第三个参数⻓度 c ommand.append(value).append("\r\n");//第三个参数值//2 发送报文到 try {write.write(command.toString().getBytes());
//3 接收 redis 响应 byte[] response = new byte[1024];
reader.read(response);
return new String(response);
} catch (IOException e) {throw new RuntimeException(e);
}}public static void main(String[] args) throws IOException {MyRedisClient client = new MyRedisClient("192.168.65.214",6379);
System.out.println(client.auth("123qweasd"));
System.out.println(client.set("test","test"));
}}4、AOF 日志恢复如果 Redis 服务出现一些意外情况,就会造成 AOF 日志中指令记录不完整。例如,手动编辑 appendonly.aof.1.incr.aof 日志文件,在最后随便输入一段文字,就可以模拟指令记录不完整的情况。这时,将 Redis 服务重启,就会发现重启失败。日志文件中会有如下错误日志:
21773:M 11 Jun 2024 18:22:43.928 * DB loaded from base fileappendonly.aof.1.base.rdb: 0.019 seconds21773:M 11 Jun 2024 18:22:43.928 # Bad file format reading the append only fileappendonly.aof.1.incr.aof: make a backup of your AOF file, then use ./redischeck-aof --fix <filename.manifest>需要配置日志文件,例如: logfile "/root/myredis/logs/6379.log"
这时就需要先将日志文件修复,然后才能启动。

[root@192-168-65-214 appendonlydir]# redis-check-aof --fixappendonly.aof.1.incr.aofStart checking Old-Style AOFAOF appendonly.aof.1.incr.aof format errorAOF analyzed: filename=appendonly.aof.1.incr.aof, size=132, ok_up_to=114,ok_up_to_line=27, diff=18This will shrink the AOF appendonly.aof.1.incr.aof from 132 bytes, with 18 bytes,to 114 bytesContinue? [y/N]: ySuccessfully truncated AOF appendonly.aof.1.incr.aof--修复的过程实际上就是将最后那一条指令删除掉。
注,对于 RDB 文件,Redis 同样提供了修复指令 redis-check-rdb,但是,由于 RDB 是二进制压缩文件,一般不太可能被篡改,所以一般用得并不太多。
4、混合持久化策略 RDB 和 AOF 两种持久化策略各有优劣,所以在使用 Redis 时,是支持同时开启两种持久化策略的。在 redis.conf 配置文件中,有一个参数可以同时打开 RDB 和 AOF 两种持久化策略。
# Redis can create append-only base files in either RDB or AOF formats. Using
# the RDB format is always faster and more efficient, and disabling it is only
# supported for backward compatibility purposes.
aof-use-rdb-preamble yes 这也说明,如果同时开启 RDB 和 AOF 两种持久化策略,那么 Redis 在恢复数据时,其实还是会优先选择从 AOF 的持久化文件开始恢复。因为通常情况下,AOF 的数据集比 RDB 更完整。而且 AOF 的持久化策略现在已经明确包含了 RDB 和 AOF 两种格式,所以 AOF 恢复数据的效率也还是比较高的。
但是要注意,既然服务重启时只找 AOF 文件,那是不是就不需要做 RDB 备份了呢?通常建议还是增加 RDB 备份。因为 AOF 数据通常在不断变化,这样其实不太利于定期做数据备份。所以通常建议保留 RDB 文件并定期进行备份,作为保证数据安全的后手。
最后要注意,Redis 的持久化策略只能保证单机的数据安全。如果服务器的磁盘坏了,那么再好的持久化策略也无法保证数据安全。如果希望进一步保证数据安全,那就需要增加以下几种集群化的方案了。
三、 Redis 主从复制 Replica 机制详解接下来的三种 Redis 分布式优化方案,主从复制、哨兵集群、 Redis 集群,都是在分布式场景下保护 Redis 数据安全以及流量分摊的方案。他们是层层递进的。

1、Replica 是什么?有什么用?
官网介绍:https://redis.io/docs/latest/operate/oss_and_stack/management/replication/redis.conf 中的描述
# Master-Replica replication. Use replicaof to make a Redis instance a copy of
# another Redis server. A few things to understand ASAP about Redis replication.
#
# +------------------+ +---------------+
# | Master | ---> | Replica |
# | (receive writes) | | (exact copy) |
# +------------------+ +---------------+
#
# 1) Redis replication is asynchronous, but you can configure a master to
# stop accepting writes if it appears to be not connected with at least
# a given number of replicas.
# 2) Redis replicas are able to perform a partial resynchronization with the
# master if the replication link is lost for a relatively small amount of
# time. You may want to configure the replication backlog size (see the next
# sections of this file) with a sensible value depending on your needs.
# 3) Replication is automatic and does not need user intervention. After a
# network partition replicas automatically try to reconnect to masters
# and resynchronize with them.
简单总结:主从复制。当 Master 数据有变化时,自动将新的数据异步同步到其他 slave 中。
最典型的作用:
读写分离:mater 以写为主,Slave 以读为主数据备份+容灾恢复 2、如何配置 Replica?
配置方式在基础课程部分有详细讲解,这里不做过多重复。简单总结一个原则:配从不配主。 这意味着对于一个 Redis 服务,可以在几乎没有影响的情况下,给他配置一个或者多个从节点。
相关核心操作简化为以下几点:
REPLICAOF host port|NO ONE : 一般配置到 redis.conf 中。
SLAVEOF host port|NO ONE: 在运行期间修改 slave 节点的信息。如果该服务已经是某个主库的从库了,那么就会停止和原 master 的同步关系。
3、如何确定主从状态?从库可以写数据吗?

主从状态可以通过 info replication 查看。例如,在一个主从复制的 master 节点上查看到的主从状态是这样的:
127.0.0.1:6379> info replication
# Replication
role:masterconnected_slaves:1slave0:ip=192.168.65.214,port=6380,state=online,offset=56,lag=1master_failover_state:no-failovermaster_replid:56a1835bdb1f02d2398fac3c34a321e665b07d36master_replid2:0000000000000000000000000000000000000000master_repl_offset:56second_repl_offset:-1repl_backlog_active:1repl_backlog_size:1048576repl_backlog_first_byte_offset:1repl_backlog_histlen:56 重点要观察 slave 的 state 状态。 另外,可以观察下 master_repl_offset 参数。如果是刚建立 Replica,数据同步是需要过程的,这时可以看到 offset 往后推移的过程。
从节点上查看到的主从状态是这样的:
127.0.0.1:6380> info replication
# Replication
role:slavemaster_host:192.168.65.214master_port:6379master_link_status:upmaster_last_io_seconds_ago:6master_sync_in_progress:0slave_read_repl_offset:574slave_repl_offset:574slave_priority:100slave_read_only:1replica_announced:1connected_slaves:0master_failover_state:no-failovermaster_replid:56a1835bdb1f02d2398fac3c34a321e665b07d36master_replid2:0000000000000000000000000000000000000000master_repl_offset:574second_repl_offset:-1repl_backlog_active:1repl_backlog_size:1048576repl_backlog_first_byte_offset:15repl_backlog_histlen:560 重点要观察 master_link_status

默认情况下,从库是只读的,不允许写入数据。因为数据只能从 master 往 slave 同步,如果 slave 修改数据,就会造成数据不一致。
127.0.0.1:6380> set k4 v4(error) READONLY You can't write against a read only replica.redis.conf 中配置了 slave 的默认权限
# Since Redis 2.6 by default replicas are read-only.
#
# Note: read only replicas are not designed to be exposed to untrusted clients
# on the internet. It's just a protection layer against misuse of the instance.
# Still a read only replica exports by default all the administrative commands
# such as CONFIG, DEBUG, and so forth. To a limited extent you can improve
# security of read only replicas using 'rename-command' to shadow all the
# administrative / dangerous commands.
replica-read-only yes 这里也提到,对于 slave 从节点,虽然禁止了对数据的写操作,但是并没有禁止 CONFIG、DEBUG 等管理指令,这些指令如果和主节点不一致,还是容易造成数据不一致。如果为了安全起⻅,可以使用 rename-command 方法屏蔽这些危险的指令。
例如在 redis.conf 配置文件中增加配置 rename-command CONFIG "" 。就可以屏蔽掉 slave 上的 CONFIG 指令。
很多企业在维护 Redis 时,都会通过 rename 直接禁用 keys , flushdb, flushall 等这一类危险的指令。
4、如果 Slave 上已经有数据了,同步时会如何处理?
在从节点的日志当中其实能够分析出结果:

也可以在从节点尝试解除主从关系,再重新建立主从关系测试一下。

5、主从复制工作流程 1》 Slave 启动后,向 master 发送一个 sync 请求。等待建立成功后,slave 会删除掉自己的数据日志文件,等待主节点同步。
2》master 接收到 slave 的 sync 请求后,会触发一次 RDB 全量备份,同时收集所有接收到的修改数据的指令。然后 master 将 RDB 和操作指令全量同步给 slave。完成第一次全量同步。
3》主从关系建立后,master 会定期向 slave 发送心跳包,确认 slave 的状态。心跳发送的间隔通过参数 repl-ping-replica-period 指定。默认 10 秒。
4》只要 slave 定期向 master 回复心跳请求,master 就会持续将后续收集到的修改数据的指令传递给 slave。同时,master 会记录 offset,即已经同步给 slave 的消息偏移量。
5》如果 slave 短暂不回复 master 的心跳请求,master 就会停止向 slave 同步数据。直到 slave 重新上线后,master 从 offset 开始,继续向 slave 同步数据。
6、主从复制的缺点 1》复制延时,信号衰减: 所有写操作都是先在 master 上操作,然后再同步到 slave,所以数据同步一定会有延迟。当系统繁忙,或者 slave 数量增加时,这个延迟会更加严重。
2》master 高可用问题: 如果 master 挂了,slave 节点是不会自动切换 master 的,只能等待人工干预,重启 master 服务,或者调整主从关系,将一个 slave 切换成 master,同时将其他 slave 的主节点调整为新的 master。
后续的哨兵集群,就相当于做这个人工干预的工作。当检测到 master 挂了之后,自动从 slave 中选择一个节点,切换成 master。
3》从数据安全性的⻆度,主从复制牺牲了服务高可用,但是增加了数据安全。
四、 Redis 哨兵集群 Sentinel 机制详解 1、Sentinel 是什么?有什么用官网介绍: https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/

Redis 的 Sentinel 不负责数据读写,主要就是给 Redis 的 Replica 主从复制提供高可用功能。主要作用有四个:
主从监控:监控主从 Redis 运行是否正常消息通知:将故障转移的结果发送给客户端故障转移:如果 master 异常,则会进行主从切换。将其中一个 slave 切换成为 master。
配置中心:客户端通过连接哨兵可以获取当前 Redis 服务的 master 地址。
2、Sentinel 核心配置 Sentinel 的环境搭建以及基础使用,在基础版中已经有详细过程。这里不再赘述。这里以单机模拟搭建 Sentinel 以及主从集群。 Redis 的服务端口为 6379(master),6380,6381。Sentinel 的服务端口为 26379,26380,26381Sentinel 最核心的配置其实就是 sentinel.conf 中的 sentinel monitor <master-name> <ip> <redisport> <quorum>

这个配置中,最抽象的参数就最后的那个 quorum。这个参数是什么意思呢?这就需要了解一下 Sentinel 的工作原理。
3、解析 Sentinel 工作原理 Sentinel 的核心工作原理分两个步骤,一是如何发现 master 服务宕机了。二是发现 master 服务宕机后,如何切换新的 master。
1》如何发现 master 服务宕机这里有两个概念需要了解,S_DOWN(主观下线)和 O_DOWN(客观下线)
对于每一 Sentinel 服务,他会不断地往 master 发送心跳,监听 master 的状态。如果经过一段时间(参数 sentinel down-after-milliseconds <master-name> <milliseconds> 指定。默认 30 秒)没有收到 master 的响应,他就会主观的认为这个 master 服务下线了。也就是 S_DOWN。
但是主观下线并不一定是 master 服务的问题,如果网络出现抖动或者阻塞,也会造成 master 的响应超时。为了防止网络抖动造成的误判,Redis 的 Sentinel 就会互相进行沟通,当超过 quorum 个 Sentinel 节点都认为 master 已经出现 S_DOWN 后,就会将 master 标记为 O_DOWN。此时才会真正确定 master 的服务是宕机的,然后就可以开始故障切换了。
在配置 Sentinel 集群时,通常都会搭建奇数个节点,而将 quorum 配置为集群中的过半个数。这样可以最大化的保证 Sentinel 集群的可用性。
2》发现 master 服务宕机后,如何切换新的 master 当确定 master 宕机后,Sentinel 会主动将一个新的 slave 切换为 mater。这个过程是怎么做的呢?通过以下一个 Sentinel 服务的日志,可以看到整个过程:

从这个日志中,可以看到 Sentinel 在做故障切换时,是经过了以下几个步骤的:
<1> master 变成 O_DOWN 后,Sentinel 会在集群中选举产生一个服务节点作为 Leader。Leader 将负责向其他 Redis 节点发送命令,协调整个故障切换过程。在选举过程中,Sentinel 是采用的 Raft 算法,这是一种多数派统一的机制,其基础思想是对集群中的重大决议,只要集群中超过半数的节点投票同意,那么这个决议就会成为整个集群的最终决议。这也是为什么建议 Sentinel 的 quorum 设置为集群超半数的原因。
<2>Sentinel 会在剩余健康的 Slave 节点中选举出一个节点作为新的 Master。 选举的规则如下:
首先检查是否有提前配置的优先节点:各个服务节点的 redis.conf 中的 replica-priority 配置最低的从节点。这个配置的默认值是 100。如果大家的配置都一样,就进入下一个检查规则。
然后检查复制偏移量 offset 最大的从节点。也就是找同步数据最快的 slave 节点。因为他的数据是最全的。如果大家的 offset 还是一样的,就进入下一个规则最后按照 slave 的 RunID 字典顺序最小的节点。
<3>切换新的主节点。 Sentinel Leader 给新的 mater 节点执行 slave of no one 操作,将他提升为 master 节点。 然后给其他 slave 发送 slave of 指令。让其他 slave 成为新 Master 的 slave。
<4>如果旧的 master 恢复了,Sentinel Leader 会让旧的 master 降级为 slave,并从新的 master 上同步数据,恢复工作。
最终,各个 Redis 的配置信息,会输出到 Redis 服务对应的 redis.conf 文件中,完成配置覆盖。
4、Sentinel 的缺点 Sentinel+Replica 的集群服务,可以实现自动故障恢复,所以可用性以及性能都还是比较好的。但是这种方案也有一些问题。
1》 对客户端不太友好由于 master 需要切换,这也就要求客户端也要将写请求频繁切换到 master 上。

2》数据不安全在主从复制集群中,不管 master 是谁,所有的数据都以 master 为主。当 master 宕机后,那些在 master 上已经完成了,但是还没有同步给其他 slave 的操作,就会彻底丢失。因为只要 master 一完成了切换,所有数据就以新的 master 为准了。
因此,在企业实际运用中,用得更多的是下面的 Redis 集群服务。
五、 Redis 集群 Cluster 机制详解 1、Cluster 是什么?有什么用?
官网地址:https://redis.io/docs/latest/operate/oss_and_stack/management/scaling/一句话总结:将多组 Redis Replica 主从集群整合到一起,像一个 Redis 服务一样对外提供服务。
所以 Redis Cluster 的核心依然是 Replica 复制集。
Redis Cluster 通过对复制集进行合理整合后,核心是要解决三个问题:
1》 客户端需要频繁切换 master 的问题。
2》服务端数据量太大后,单个复制集难以承担的问题。

3》master 节点挂了之后,主动将 slave 切换成 master,保证服务稳定 2、Cluster 的核心配置 Cluster 的基础搭建工作在基础版中已经给大家逐一演示,这里同样不再赘述。接下来还是以单机快速模拟三主三从的 Redis 集群服务,带大家深入理解集群的原理。
构建 Redis 集群的核心配置是要在 redis.conf 中开启集群模式。并且指定一个给集群进行修改的配置文件。
# Normal Redis instances can't be part of a Redis Cluster; only nodes that are
# started as cluster nodes can. In order to start a Redis instance as a
# cluster node enable the cluster support uncommenting the following:
#
cluster-enabled yes
# Every cluster node has a cluster configuration file. This file is not
# intended to be edited by hand. It is created and updated by Redis nodes.
# Every Redis Cluster node requires a different cluster configuration file.
# Make sure that instances running in the same system do not have
# overlapping cluster configuration file names.
#
cluster-config-file nodes-6379.conf 以下是其中一个服务的配置文件示例:

# 允许所有的 IP 地址
bind * -::*
# 后台运行
daemonize yes
# 允许远程连接
protected-mode no
# 密码
requirepass 123qweasd
# 主节点密码
masterauth 123qweasd
# 端口
port 6381
# 开启集群模式
cluster-enabled yes
# 集群配置文件
cluster-config-file nodes-6381.conf
# 集群节点超时时间
cluster-node-timeout 5000
# log 日志
logfile "/root/myredis/cluster/redis6381.log"
# pid 文件
pidfile /var/run/redis_6381.pid
# 开启 AOF 持久化
appendonly yes
# 配置数据存储目录
dir "/root/myredis/cluster"
# AOF 目录
appenddirname "aof"
# AOF 文件名
appendfilename "appendonly6381.aof"
# RBD 文件名
dbfilename "dump6381.rdb"
接下来依次创建 6381,6382,6383,6384,6385,6386 六个端口的 Redis 配置文件,并启动服务。
接下来就可以构建 Redis 集群。将多个独立的 Redis 服务整合成一个统一的集群。
[root@192-168-65-214 cluster]# redis-cli -a 123qweasd --cluster create --clusterreplicas 1 192.168.65.214:6381 192.168.65.214:6382 192.168.65.214:6383192.168.65.214:6384 192.168.65.214:6385 192.168.65.214:6386 其中 --cluster create 表示创建集群。 --cluster-replicas 表示为每个 master 创建一个 slave 节点。接下来,Redis 会自动分配主从关系,形成 Redis 集群。
集群启动完成后,可以使用客户端连接上其中任意一个服务端,验证集群。

--连接 Redis 集群。-c 表示集群模式 redis-cli -p 6381 -a 123qweasd -c--查看集群节点 cluster nodes--查看集群状态 cluster infoRedis 在分配主从关系时,会优先将主节点和从节点分配在不同的机器上。我们这里用一台服务器模拟集群,就无法体现出这种特性。
接下来再来逐步验证之前提到的 Redis 集群要解决的三个问题。
-- 客户端连接集群[root@192-168-65-214 cluster]# redis-cli -a 123qweasd -p 6381 -cWarning: Using a password with '-a' or '-u' option on the command line interfacemay not be safe.!!! 设置 k1 时,集群会将 k1 分配到 6383 节点,解决了数据太大的问题。
!!! 客户端会自动切换到 6383 服务上,解决了服务端切换 master 的问题 127.0.0.1:6381> set k1 v1-> Redirected to slot [12706] located at 192.168.65.214:6383OK192.168.65.214:6383> set k2 v2-> Redirected to slot [449] located at 192.168.65.214:6381OK192.168.65.214:6381> set k3 v3OK 下面验证集群的高可用

-- 查看集群状态[root@192-168-65-214 cluster]# redis-cli -a 123qweasd -p 6381 -c cluster nodesWarning: Using a password with '-a' or '-u' option on the command line interfacemay not be safe.4bc8ba4aa07fbed559befbc7af14424e78ebf3ef 192.168.65.214:6384@16384 slaveff9437319ceee739d72cc23b987bd28002b72eae 0 1718353142000 3 connected3b1848099a74e6de1669bde3af108132d8b03e41 192.168.65.214:6385@16385 slavefd3cbd892f11e950104955f7297adb20fab0253c 0 1718353143567 1 connectedff9437319ceee739d72cc23b987bd28002b72eae 192.168.65.214:6383@16383 master - 01718353143065 3 connected 10923-16383883a01f49ad112220253dcf4e6dc54ac12db6355 192.168.65.214:6386@16386 slave698f36253e9f01470a179f4f04f5d6c683437851 0 1718353142000 2 connected698f36253e9f01470a179f4f04f5d6c683437851 192.168.65.214:6382@16382 master - 01718353143000 2 connected 5461-10922fd3cbd892f11e950104955f7297adb20fab0253c 192.168.65.214:6381@16381 myself,master- 0 1718353141000 1 connected 0-5460--关闭 6383 服务[root@192-168-65-214 cluster]# redis-cli -a 123qweasd -p 6383 -c shutdown-- 重新查看集群状态[root@192-168-65-214 cluster]# redis-cli -a 123qweasd -p 6381 -c cluster nodesWarning: Using a password with '-a' or '-u' option on the command line interfacemay not be safe.4bc8ba4aa07fbed559befbc7af14424e78ebf3ef 192.168.65.214:6384@16384 master - 01718353206000 8 connected 10923-163833b1848099a74e6de1669bde3af108132d8b03e41 192.168.65.214:6385@16385 slavefd3cbd892f11e950104955f7297adb20fab0253c 0 1718353207256 1 connectedff9437319ceee739d72cc23b987bd28002b72eae 192.168.65.214:6383@16383 master,fail 1718353192017 1718353189508 3 disconnected883a01f49ad112220253dcf4e6dc54ac12db6355 192.168.65.214:6386@16386 slave698f36253e9f01470a179f4f04f5d6c683437851 0 1718353206252 2 connected698f36253e9f01470a179f4f04f5d6c683437851 192.168.65.214:6382@16382 master - 01718353206553 2 connected 5461-10922fd3cbd892f11e950104955f7297adb20fab0253c 192.168.65.214:6381@16381 myself,master- 0 1718353206000 1 connected 0-5460!!! 集群信息发生了切换,6384 服务从 slave 切 换成了 master(节点切换需要一点点时间)
--重新启动 6383 服务[root@192-168-65-214 cluster]# redis-server redis6383.conf--重新查看集群状态[root@192-168-65-214 cluster]# redis-cli -a 123qweasd -p 6381 -c cluster nodesWarning: Using a password with '-a' or '-u' option on the command line interfacemay not be safe.4bc8ba4aa07fbed559befbc7af14424e78ebf3ef 192.168.65.214:6384@16384 master - 01718353409018 8 connected 10923-163833b1848099a74e6de1669bde3af108132d8b03e41 192.168.65.214:6385@16385 slavefd3cbd892f11e950104955f7297adb20fab0253c 0 1718353409000 1 connectedff9437319ceee739d72cc23b987bd28002b72eae 192.168.65.214:6383@16383 slave4bc8ba4aa07fbed559befbc7af14424e78ebf3ef 0 1718353409519 8 connected883a01f49ad112220253dcf4e6dc54ac12db6355 192.168.65.214:6386@16386 slave698f36253e9f01470a179f4f04f5d6c683437851 0 1718353409519 2 connected698f36253e9f01470a179f4f04f5d6c683437851 192.168.65.214:6382@16382 master - 0

1718353410022 2 connected 5461-10922fd3cbd892f11e950104955f7297adb20fab0253c 192.168.65.214:6381@16381 myself,master- 0 1718353409000 1 connected 0-5460!!! 6383 成为了 6384 的 slave。
注:集群故障转移也可以通过手动形式触发。例如在一个 slave 节点上执行 cluster failover,就会触发一次故障转移,尝试将这个 slave 提升为 master。
从节点信息可以看到,集群中在每个 master 的最后,都记录了他负责的 slot 槽位,这些 slot 就是 Redis 集群工作的核心。
3、详解 Slot 槽位 Redis 集群设置 16384 个哈希槽。每个 key 会通过 CRC16 校验后,对 16384 取模,来决定放到哪个槽。集群的每个节点负责一部分的 hash 槽。
问题 1、Slot 如何分配 Redis 集群中内置 16384 个槽位。在建立集群时,Redis 会根据集群节点数量,将这些槽位尽量平均的分配到各个节点上。并且,如果集群中的节点数量发生了变化。(增加了节点或者减少了节点)。就需要触发一次 reshard,重新分配槽位。而槽位中对应的 key,也会随着进行数据迁移。

# 增加 6387,6388 两个 Redis 服务,并启动
# 添加到集群当中
redis-cli -a 123qweasd -p 6381 --cluster add-node 192.168.65.214:6387192.168.65.214:6388
# 确定集群状态 此时新节点上是没有 slot 分配的
redis-cli -a 123qweasd -p 6381 --cluster check 192.168.65.214:6381
# 手动触发 reshard,重新分配槽位
redis-cli -a 123qweasd -p 6381 reshard 192.168.65.214:6381
# 再次确定集群状态 此时新节点上会有一部分槽位分配
redis-cli -a 123qweasd -p 6381 --cluster check 192.168.65.214:6381reshard 操作会从三个旧节点当中分配一部分新的槽位给新的节点。在这个过程中,Redis 也就并不需要移动所有的数据,只需要移动那一部分槽位对应的数据。
除了这种自动调整槽位的机制,Redis 也提供了手动调整槽位的指令。可以使用 cluster help 查看相关调整指令。
这些指令通常用得比较少,大家自行了解。
另外,Redis 集群也会检查每个槽位是否有对应的节点负责。如果负责一部分槽位的一组复制节点都挂了,默认情况下 Redis 集群就会停止服务。其他正常的节点也无法接收写数据的请求。
如果此时,需要强制让 Redis 集群提供服务,可以在配置文件中,将 cluster-require-full-coverage 参数手动调整为 no。
# By default Redis Cluster nodes stop accepting queries if they detect there
# is at least a hash slot uncovered (no available node is serving it).
# This way if the cluster is partially down (for example a range of hash slots
# are no longer covered) all the cluster becomes, eventually, unavailable.
# It automatically returns available as soon as all the slots are covered again.
#
# However sometimes you want the subset of the cluster which is working,
# to continue to accept queries for the part of the key space that is still
# covered. In order to do so, just set the cluster-require-full-coverage
# option to no.
#
# cluster-require-full-coverage yes
通常不建议这样做,因为这意味着 Redis 提供的数据服务是不完整的。
问题 2、如何确定 key 与 slot 的对应关系?
Redis 集群中,对于每一个要写入的 key,都会寻找所属的槽位。计算的方式是 CRC16(key) mod16384。
首先,这意味着在集群当中,那些批量操作的复合指令(如 mset,mhset)支持会不太好。如果他们分属不同的槽位,就无法保证他们能够在一个服务上进行原子性操作。

127.0.0.1:6381> mset k1 v1 k2 v2 k3 v3(error) CROSSSLOT Keys in request don't hash to the same slot 这也是对分布式事务的一种思考。如果这种批量指令需要分到不同的 Redis 节点上操作,那么这个指令的操作原子性问题就称为了一个分布式事务问题。而分布式事务是一件非常复杂的事情,不要简单的认为用上 seata 这样的框架就很容易解决。在大部分业务场景下,直接拒绝分布式事务,是一种很好的策略。
然后,在 Redis 中,提供了指令 CLUSTER KEYSLOT 来计算某一个 key 属于哪个 Slot127.0.0.1:6381> CLUSTER KEYSLOT k1(integer) 12706 另外,Redis 在计算 hash 槽时,会使用 hashtag。如果 key 中有大括号{},那么只会根据大括号中的 hash tag 来计算槽位。
127.0.0.1:6381> CLUSTER KEYSLOT k1(integer) 12706127.0.0.1:6381> CLUSTER KEYSLOT roy{k1}(integer) 12706127.0.0.1:6381> CLUSTER KEYSLOT roy:k1(integer) 12349-- 使用相同的 hash tag,能保证这些数据都是保存在同一个节点上的。
127.0.0.1:6381> mset user_{1}_name roy user_{1}_id 1 user_{1}_password 123-> Redirected to slot [9842] located at 192.168.65.214:6382OK 在大型 Redis 集群中,经常会出现数据倾斜的问题。也就是大量的数据被集中存储到了集群中某一个热点 Redis 节点上。从而造成这一个节点的负载明显大于其他节点。这种数据倾斜问题就容易造成集群的资源浪费。
调整数据倾斜的问题,常⻅的思路就是分两步。第一步,调整 key 的结构,尤其是那些访问频繁的热点 key,让数据能够尽量平均的分配到各个 slot 上。第二步,调整 slot 的分布,将那些数据量多,访问频繁的热点 slot 进行重新调配,让他们尽量平均的分配到不同的 Redis 节点上。
4、Redis 集群选举原理-了解 1、gossip 协议 Redis 集群之间通过 gossip 协议进行频繁的通信,用于传递消息和更新节点状态。
主要作用有:

节点间发送心跳和确认其他节点的存在。
通知其他节点新节点的加入或已经下线的节点。
通过反馈机制更新节点的状态,如权重、过期时间等 gossip 协议包含多种消息,包括 ping,pong,meet,fail 等等。
meet:某个节点发送 meet 给新加入的节点,让新节点加入集群中,然后新节点就会开始与其他节点进行通信;
ping:每个节点都会频繁给其他节点发送 ping,其中包含自己的状态还有自己维护的集群元数据,互相通过 ping 交换元数据(类似自己感知到的集群节点增加和移除,hash slot 信息等);
pong: 对 ping 和 meet 消息的返回,包含自己的状态和其他信息,也可以用于信息广播和更新;
fail: 某个节点判断另一个节点 fail 之后,就发送 fail 给其他节点,通知其他节点,指定的节点宕机了。
gossip 集群是去中心化的,各个节点彼此之间通过 gossip 协议互相通信,保证集群内部各个节点最终能够达成统一。 gossip 协议更新元数据并不是同时在集群内部同步,而是陆陆续续请求到所有节点上。因此 gossip 协议的数据统一是有一定的延迟的。
gossip 协议最大的好处在于,即使集群节点的数量增加,每个节点的负载也不会增加很多,几乎是恒定的。因此在 Redis 集群中,哪怕构建非常多的节点,也不会对服务性能造成很大的影响。但是 gossip 协议的数据同步是有延迟的,如果集群节点太多,数据同步的延迟时间也会增加。这对于 Redis 是不合适的。因此,通常不建议构建太大的 Redis 集群。
需要注意下的是,Redis 集群中,每个节点都有一个专⻔用于节点之间进行 gossip 通信的端口,就是自己提供服务的端口+10000.因此,在部署 Redis 集群时,要注意防火墙配置,不要把这个端口屏蔽了。

2、Redis 集群选举流程当 slave 发现自己的 master 变为 FAIL 状态时,便尝试进行 Failover,以期成为新的 master。由于挂掉的 master 可能会有多个 slave,从而存在多个 slave 竞争成为 master 节点的过程, 其过程如下:
1》slave 发现自己的 master 变为 FAIL2》将自己记录的集群 currentEpoch 加 1,并广播 FAILOVER_AUTH_REQUEST 信息(currentEpoch 可以理解为选举周期,通过 cluster info 指令可以看到)
3》其他节点收到该信息,只有 master 响应,判断请求者的合法性,并发送 FAILOVER_AUTH_ACK,对每一个 epoch 只发送一次 ack4》尝试 failover 的 slave 收集 master 返回的 FAILOVER_AUTH_ACK5》slave 收到超过半数 master 的 ack 后变成新 Master(这里解释了集群为什么至少需要三个主节点,如果只有两 个,当其中一个挂了,只剩一个主节点是不能选举成功的)
6》slave 广播 Pong 消息通知其他集群节点从节点并不是在主节点一进入 FAIL 状态就⻢上尝试发起选举,而是有一定延迟,一定的延迟确保我们等待 FAIL 状态在集群中传播,slave 如果立即尝试选举,其它 masters 或许尚未意识到 FAIL 状态,可能会拒绝投票延迟计算公式: DELAY = 500ms + random(0 ~ 500ms) + SLAVE_RANK * 1000msSLAVE_RANK 表示此 slave 已经从 master 复制数据的总量的 rank。Rank 越小代表已复制的数据越新。这种方 式下,持有最新数据的 slave 将会首先发起选举(理论上)。
5、Redis 集群能不能保证数据安全?
首先,在 Redis 集群相对比较稳定的时候,Redis 集群是能够保证数据安全的。
因为 Redis 集群中每个 master 都是可以配置 slave 从节点的。这些 slave 节点会即时备份 master 的数据。在 master 宕机时,slave 会自动切换成 master。继续提供服务。
在 Redis 的配置文件中,有两个参数用来保证每个 master 必须有健康的 slave 进行备份。

# It is possible for a master to stop accepting writes if there are less than
# N replicas connected, having a lag less or equal than M seconds.
#
# The N replicas need to be in "online" state.
#
# The lag in seconds, that must be <= the specified value, is calculated from
# the last ping received from the replica, that is usually sent every second.
#
# This option does not GUARANTEE that N replicas will accept the write, but
# will limit the window of exposure for lost writes in case not enough replicas
# are available, to the specified number of seconds.
#
# For example to require at least 3 replicas with a lag <= 10 seconds use:
#
# min-replicas-to-write 3
# min-replicas-max-lag 10
#
# Setting one or the other to 0 disables the feature.
#
# By default min-replicas-to-write is set to 0 (feature disabled) and
# min-replicas-max-lag is set to 10
然后,由于 Redis 集群的 gossip 协议在同步元数据时不保证强一致性,这意味着在特定的条件下,Redis 集群可能会丢掉一些被系统收到的写入请求命令。
这些特定条件通常都比较苛刻,概率比较小。比如网络抖动产生的脑裂问题。
在企业中,有良好运维支持,通常可以认为 Redis 集群的数据是安全的。
六、 Redis 数据安全性方案总结对于任何数据存储系统来说,数据安全都是重中之重。 Redis 也不例外。从数据安全性的⻆度来梳理 Redis 从单机到集群的各种部署架构,可以看到用 Redis 保存数据基本上还是非常靠谱的。甚至 Redis 的数据保存策略,在很多场景下,都是一种教科书级别的解决方案。另外,之前介绍过,Redis 现在推出了企业版本。企业版在业务功能层面并没有做太多的加法,核心就是在服务高可用以及数据安全方面提供了更加全面的支持。有兴趣的朋友可以自行去了解补充。
但是,基于内存和硬盘的成本对比,Redis 通常还是不建议作为独立的数据库使用。大部分情况下,还是发挥 Redis 高性能的优势,作为一个数据缓存来使用。其实,如果有非常靠谱的运维支撑,Redis 作为数据库来使用完全是可以的。比如,Redis 现在提供了基于云服务器的 RedisCloud 服务。其中就可以购买作为数据库使用的 Redis 实例。

