---



title: "四、Kafka日志索引详解"
description: "log 文件追加记录所有消息 2 index 和 timeindex 加速读取 log 消息日志。"
author: hsc
date: 2023-10-01 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Redis', 'Kafka', 'RocketMQ', 'Netty']
toc: true



---

### 一、 Topic 下的消息是如何存储的?
1 log 文件追加记录所有消息 2 index 和 timeindex 加速读取 log 消息日志。
二、文件清理机制三、客户端消费进度管理四、 Kafka 的文件高效读写机制 1、Kafka 的文件结构 2、顺序写磁盘 3、零拷⻉4、合理配置刷盘频率四、 Kafka 日志索引详解-- 楼兰上一章节 Kafka 的核心集群机制,重点保证了在复杂运行环境下,整个 Kafka 集群如何保证 Partition 内消息的一致性。这就相当于一个军队,有了完整统一的编制。但是,在进行具体业务时,还是需要各个 Broker 进行分工,各自处理好自己的工作。
每个 Broker 如何高效的处理以及保存消息,也是 Kafka 高性能背后非常重要的设计。这一章节还是按照之前的方式,从可⻅的 Log 文件入手,来逐步梳理 Kafka 是如何进行高效消息流转的。 Kafka 的日志文件记录机制也是 Kafka 能够支撑高吞吐、高性能、高可扩展的核心所在。对于业界的影响也是非常巨大的。
这一部分数据主要包含当前 Broker 节点的消息数据(在 Kafka 中称为 Log 日志)。这是一部分无状态的数据,也就是说每个 Kafka 的 Broker 节点都是以相同的逻辑运行。这种无状态的服务设计让 Kafka 集群能够比较容易的进行水平扩展。比如你需要用一个新的 Broker 服务来替换集群中一个旧的 Broker 服务,那么只需要将这部分无状态的数据从旧的 Broker 上转移到新的 Broker 上就可以了。
当然,这里说的的数据转移,并不是复制,粘贴这么简单,因为底层的数据文件中的细节还是非常多的,并且是二进制文件,操作也不容易。
实际上 Kafka 也提供了很多工具来协助进行数据迁移,例如 bin 目录下的 kafka-reassign-partitions.sh 都可以帮助进行服务替换。感兴趣可以使用脚本的--help 指令了解一下一、 Topic 下的消息是如何存储的?
在搭建 Kafka 服务时,我们在 server.properties 配置文件中通过 log.dir 属性指定了 Kafka 的日志存储目录。实际上,Kafka 的所有消息就全都存储在这个目录下。

这些核心数据文件中,.log 结尾的就是实际存储消息的日志文件。他的大小固定为 1G(由参数 log.segment.bytes 参数指定),写满后就会新增一个新的文件。一个文件也成为一个 segment 文件名表示当前日志文件记录的第一条消息的偏移量。
.index 和.timeindex 是日志文件对应的索引文件。不过.index 是以偏移量为索引来记录对应的.log 日志文件中的消息偏移量。而.timeindex 则是以时间戳为索引。
另外的两个文件,partition.metadata 简单记录当前 Partition 所属的 cluster 和 Topic。leader-epochcheckpoint 文件参⻅上面的 epoch 机制。
这些文件都是二进制的文件,无法使用文本工具直接查看。但是,Kafka 提供了工具可以用来查看这些日志文件的内容。

#1、查看 timeIndex 文件
[root@192-168-65-112 bin]# ./kafka-dump-log.sh --files /app/kafka/logs/disTopic0/00000000000000000000.timeindexDumping /app/kafka/logs/disTopic-0/00000000000000000000.timeindextimestamp: 1723519364827 offset: 50timestamp: 1723519365630 offset: 99timestamp: 1723519366162 offset: 148timestamp: 1723519366562 offset: 197timestamp: 1723519367013 offset: 246timestamp: 1723519367364 offset: 295timestamp: 1723519367766 offset: 344
#2、查看 index 文件
[root@192-168-65-112 bin]# ./kafka-dump-log.sh --files /app/kafka/logs/disTopic0/00000000000000000000.indexDumping /app/kafka/logs/disTopic-0/00000000000000000000.indexoffset: 50 position: 4098offset: 99 position: 8214offset: 148 position: 12330offset: 197 position: 16446offset: 246 position: 20562offset: 295 position: 24678offset: 344 position: 28794
#3、查看 log 文件
[root@192-168-65-112 bin]# ./kafka-dump-log.sh --files /app/kafka/logs/disTopic0/00000000000000000000.logDumping /app/kafka/kafka-logs/secondTopic-0/00000000000000000000.logStarting offset: 0.....baseOffset: 350 lastOffset: 350 count: 1 baseSequence: 349 lastSequence: 349 producerId:
5002 producerEpoch: 0 partitionLeaderEpoch: 7 isTransactional: false isControl: falsedeleteHorizonMs: OptionalLong.empty position: 29298 CreateTime: 1723519367827 size: 84magic: 2 compresscodec: none crc: 400306231 isvalid: truebaseOffset: 351 lastOffset: 351 count: 1 baseSequence: 350 lastSequence: 350 producerId:
5002 producerEpoch: 0 partitionLeaderEpoch: 7 isTransactional: false isControl: falsedeleteHorizonMs: OptionalLong.empty position: 29382 CreateTime: 1723519367829 size: 84magic: 2 compresscodec: none crc: 2036034757 isvalid: true.......这些数据文件的记录方式,就是我们去理解 Kafka 本地存储的主线。
1 log 文件追加记录所有消息首先:在每个文件内部,Kafka 都会以追加的方式写入到 log 日志文件中。 Kafka 中的消息日志,只允许追加,不支持删除和修改。所以,只有文件名最大的一个 log 文件是当前写入消息的日志文件,其他文件都是不可修改的历史日志。
然后:每个 Log 文件都保持固定的大小。如果当前文件记录不下了,就会重新创建一个 log 文件,并以这个 log 文件写入的第一条消息的偏移量命名。这种设计其实是为了更方便进行文件映射,加快读消息的效率。
2 index 和 timeindex 加速读取 log 消息日志。
详细看下这几个文件的内容,就可以总结出 Kafka 记录消息日志的整体方式:

首先:index 和 timeindex 都是以相对偏移量的方式建立 log 消息日志的数据索引。比如说 0000.index 和 0550.index 中记录的索引数字,都是从 0 开始的。表示相对日志文件起点的消息偏移量。而绝对的消息偏移量可以通过日志文件名 + 相对偏移量得到。
然后:这两个索引并不是对每一条消息都建立索引。而是 Broker 每写入 40KB 的数据,就建立一条 index 索引。
由参数 log.index.interval.bytes 定制。
log.index.interval.bytesThe interval with which we add an entry to the offset indexType: intDefault: 4096 (4 kibibytes)
Valid Values: [0,...]Importance: mediumUpdate Mode: cluster-wideindex 文件的作用类似于数据结构中的跳表,他的作用是用来加速查询 log 文件的效率。而 timeindex 文件的作用则是用来进行一些跟时间相关的消息处理。比如文件清理。
这两个索引文件也是 Kafka 的消费者能够指定从某一个 offset 或者某一个时间点读取消息的原因。
二、文件清理机制 Kafka 为了防止过多的日志文件给服务器带来过大的压力,他会定期删除过期的 log 文件。 Kafka 的删除机制涉及到几组配置属性:
1、如何判断哪些日志文件过期了

log.retention.check.interval.ms:定时检测文件是否过期。默认是 300000 毫秒,也就是五分钟。
log.retention.hours , log.retention.minutes, log.retention.ms 。 这一组参数表示文件保留多⻓时间。
默认生效的是 log.retention.hours,默认值是 168 小时,也就是 7 天。如果设置了更高的时间精度,以时间精度最高的配置为准。
在检查文件是否超时时,是以每个.timeindex 中最大的那一条记录为准。
2、过期的日志文件如何处理 log.cleanup.policy:日志清理策略。有两个选项,delete 表示删除日志文件。 compact 表示压缩日志文件。
当 log.cleanup.policy 选择 delete 时,还有一个参数可以选择。 log.retention.bytes:表示所有日志文件的大小。当总的日志文件大小超过这个阈值后,就会删除最早的日志文件。默认是-1,表示无限大。
压缩日志文件虽然不会直接删除日志文件,但是会造成消息丢失。压缩的过程中会将 key 相同的日志进行压缩,只保留最后一条。
三、客户端消费进度管理 kafka 为了实现分组消费的消息转发机制,需要在 Broker 端保持每个消费者组的消费进度。而这些消费进度,就被 Kafka 管理在自己的一个内置 Topic 中。这个 Topic 就是__consumer__offsets。这是 Kafka 内置的一个系统 Topic,在日志文件可以看到这个 Topic 的相关目录。 Kafka 默认会将这个 Topic 划分为 50 个分区。

同时,Kafka 也会将这些消费进度的状态信息记录到 Zookeeper 中。

这个系统 Topic 中记录了所有 ConsumerGroup 的消费进度。那他的数据是怎么保存的呢?在 Zookeeper 中似乎并没有记载 Offset 数据啊。
既然他是 Kafka 的一个 Topic,那消费者是不是可以直接消费其中的消息?
这个 Topic 是 Kafka 内置的一个系统 Topic,可以启动一个消费者订阅这个 Topic 中的消息。
[root@192-168-65-112 kafka_2.13-3.8.0]# bin/kafka-console-consumer.sh --topic__consumer_offsets --bootstrap-server worker1:9092 --consumer.configconfig/consumer.properties --formatter"kafka.coordinator.group.GroupMetadataManager\$OffsetsMessageFormatter" --from-beginning 查看到结果:

```
[test,disTopic,1]::OffsetAndMetadata(offset=3, leaderEpoch=Optional[1], metadata=,commitTimestamp=1661351768150, expireTimestamp=None)
[test,disTopic,2]::OffsetAndMetadata(offset=0, leaderEpoch=Optional.empty, metadata=,commitTimestamp=1661351768150, expireTimestamp=None)
[test,disTopic,0]::OffsetAndMetadata(offset=6, leaderEpoch=Optional[2], metadata=,commitTimestamp=1661351768150, expireTimestamp=None)
[test,disTopic,3]::OffsetAndMetadata(offset=6, leaderEpoch=Optional[3], metadata=,commitTimestamp=1661351768151, expireTimestamp=None)
[test,disTopic,1]::OffsetAndMetadata(offset=3, leaderEpoch=Optional[1], metadata=,commitTimestamp=1661351768151, expireTimestamp=None)
[test,disTopic,2]::OffsetAndMetadata(offset=0, leaderEpoch=Optional.empty, metadata=,commitTimestamp=1661351768151, expireTimestamp=None)
[test,disTopic,0]::OffsetAndMetadata(offset=6, leaderEpoch=Optional[2], metadata=,commitTimestamp=1661351768151, expireTimestamp=None)
[test,disTopic,3]::OffsetAndMetadata(offset=6, leaderEpoch=Optional[3], metadata=,commitTimestamp=1661351768153, expireTimestamp=None)
[test,disTopic,1]::OffsetAndMetadata(offset=3, leaderEpoch=Optional[1], metadata=, commitTimestamp=1661351768153, expireTimestamp=None)
[test,disTopic,2]::OffsetAndMetadata(offset=0, leaderEpoch=Optional.empty, metadata=, commitTimestamp=1661351768153, expireTimestamp=None)
```
从这里可以看到,Kafka 也是像普通数据一样,以 Key-Value 的方式来维护消费进度。 key 是 groupid+topic+partition,value 则是表示当前的 offset。
而这些 Offset 数据,其实也是可以被消费者修改的,在之前章节已经演示过消费者如何从指定的位置开始消费消息。而一旦消费者主动调整了 Offset,Kafka 当中也会更新对应的记录。
在早期版本中,Offset 确实是存在 Zookeeper 中的。但是 Kafka 在很早就选择了将 Offset 从 Zookeeper 中转移到 Broker 上。这也体现了 Kafka 其实早就意识到,Zookeeper 这样一个外部组件在面对三高问题时,是不太"靠谱"的,所以 Kafka 逐渐转移了 Zookeeper 上的数据。而后续的 Kraft 集群,其实也是这种思想的延伸。
另外,这个系统 Topic 里面的数据是非常重要的,因此 Kafka 在消费者端也设计了一个参数来控制这个 Topic 应该从订阅关系中剔除。
public static final String EXCLUDE_INTERNAL_TOPICS_CONFIG = "exclude.internal.topics";
private static final String EXCLUDE_INTERNAL_TOPICS_DOC = "Whether internal topicsmatching a subscribed pattern should " +"be excluded from the subscription. It is always possible to explicitlysubscribe to an internal topic.";
public static final boolean DEFAULT_EXCLUDE_INTERNAL_TOPICS = true;
这个参数简单测试了一下,在当前版本是没有用的。
四、 Kafka 的文件高效读写机制这是 Kafka 非常重要的一个设计,同时也是面试频率超高的问题。可以分几个方向来理解。
1、Kafka 的文件结构

Kafka 的数据文件结构设计可以加速日志文件的读取。比如同一个 Topic 下的多个 Partition 单独记录日志文件,并行进行读取,这样可以加快 Topic 下的数据读取速度。然后 index 的稀疏索引结构,可以加快 log 日志检索的速度。
2、顺序写磁盘这个跟操作系统有关,主要是硬盘结构。
对每个 Log 文件,Kafka 会提前规划固定的大小,这样在申请文件时,可以提前占据一块连续的磁盘空间。然后,Kafka 的 log 文件只能以追加的方式往文件的末端添加(这种写入方式称为顺序写),这样,新的数据写入时,就可以直接往直前申请的磁盘空间中写入,而不用再去磁盘其他地方寻找空闲的空间(普通的读写文件需要先寻找空闲的磁盘空间,再写入。这种写入方式称为随机写)。由于磁盘的空闲空间有可能并不是连续的,也就是说有很多文件碎片,所以磁盘写的效率会很低。
kafka 的官网有测试数据,表明了同样的磁盘,顺序写速度能达到 600M/s,基本与写内存的速度相当。而随机写的速度就只有 100K/s,差距比加大。
3、零拷⻉零拷⻉是 Linux 操作系统提供的一种 IO 优化机制,而 Kafka 大量的运用了零拷⻉机制来加速文件读写。
传统的一次硬件 IO 是这样工作的。如下图所示:
其中,内核态的内容复制是在内核层面进行的,而零拷⻉的技术,重点是要配合内核态的复制机制,减少用户态与内核态之间的内容拷⻉。
具体实现时有两种方式:

1、mmap 文件映射机制这种方式是在用户态不再缓存整个 IO 的内容,改为只持有文件的一些映射信息。通过这些映射,"遥控"内核态的文件读写。这样就减少了内核态与用户态之间的拷⻉数据大小,提升了 IO 效率。
这都说的是些什么?去参考下 JDK 中的 DirectByteBuffer 实现机制吧。
mmap 文件映射机制是操作系统提供的一种文件操作机制,可以使用 man 2 mmap 查看。实际上在 Java 程序执行过程当中就会被大量使用。
这种 mmap 文件映射方式,适合于操作不是很大的文件,通常映射的文件不建议超过 2G。所以 kafka 将.log 日志文件设计成 1G 大小,超过 1G 就会另外再新写一个日志文件。这就是为了便于对文件进行映射,从而加快对.log 文件等本地文件的写入效率。
2、sendfile 文件传输机制这种机制可以理解为用户态,也就是应用程序不再关注数据的内容,只是向内核态发一个 sendfile 指令,要他去复制文件就行了。这样数据就完全不用复制到用户态,从而实现了零拷⻉。
相比 mmap,连索引都不读了,直接通知操作系统去拷⻉就是了。好处,自然是效率更高了。但是坏处是在用户态对文件内容完全无感知,也就是说无法在用户态中对文件内容做解析。

例如在 Kafka 中,当 Consumer 要从 Broker 上 poll 消息时,Broker 需要读取自己本地的数据文件,然后通过网卡发送给 Consumer。这个过程当中,Broker 只负责传递消息,而不对消息进行任何的加工。所以 Broker 只需要将数据从磁盘读取出来,复制到网卡的 Socket 缓冲区,然后通过网络发送出去。这个过程当中,用户态就只需要往内核态发一个 sendfile 指令,而不需要有任何的数据拷⻉过程。 Kafka 大量的使用了 sendfile 机制,用来加速对本地数据文件的读取过程。
具体细节可以在 linux 机器上使用 man 2 sendfile 指令查看操作系统的帮助文件。
SENDFILE(2) LinuxProgrammer's ManualSENDFILE(2)
NAMEsendfile - transfer data between file descriptorsSYNOPSIS......In Linux kernels before 2.6.33, out_fd must refer to a socket. Since Linux2.6.33 it can be any file. If it is a regular file, then sendfile() changes thefile offsetappropriately.RETURN VALUEIf the transfer was successful, the number of bytes written to out_fd isreturned. On error, -1 is returned, and errno is set appropriately.JDK 中 8 中 java.nio.channels.FileChannel 类提供了 transferTo 和 transferFrom 方法,底层就是使用了操作系统的 sendfile 机制。
这些底层的优化机制都是操作系统提供的优化机制,其实针对任何上层应用语言来说,都是一个黑盒,只能去调用,但是控制不了具体的实现过程。而上层的各种各样的语言,也只能根据操作系统提供的支持进行自己的实现。虽然不同语言的实现方式会有点不同,但是本质都是一样的。

4、合理配置刷盘频率缓存数据断电就会丢失,这是大家都能理解的,所以缓存中的数据如果没有及时写入到硬盘,也就是常说的刷盘,那么当服务突然崩溃,就会有丢消息的可能。所以,最安全的方式是写一条数据,就刷一次盘,成为同步刷盘。刷盘操作在 Linux 系统中对应了一个 fsync 的系统调用。
FSYNC(2) LinuxProgrammer's ManualFSYNC(2)
NAMEfsync, fdatasync - synchronize a file's in-core state with storage device 但是,这里真正容易产生困惑的,是这里所提到的 in-core state。这并不是我们平常开发过程中接触到的缓存,而是操作系统内核态的缓存-pageCache。这是应用程序接触不到的一部分缓存。比如我们用应用程序打开一个文件,实际上文件里的内容,是从内核态的 PageCache 中读取出来的。因为与磁盘这样的硬件交互,相比于内存,效率是很低的。操作系统为了提升性能,会将磁盘中的文件加载到 PageCache 缓存中,再向应用程序提供数据。修改文件时也是一样的。用记事本修改一个文件的内容,不管你保存多少次,内容都是写到 PageCache 里的。然后操作系统会通过他自己的缓存管理机制,在未来的某个时刻将所有的 PageCache 统一写入磁盘。这个操作就是刷盘。比如在操作系统正常关系的过程中,就会触发一次完整的刷盘机制。
说这么多,就是告诉你,其实对于缓存断掉,造成数据丢失,这个问题,应用程序其实是没有办法插手的。他并不能够决定自己产生的数据在什么时候刷入到硬盘当中。应用程序唯一能做的,就是尽量频繁的通知操作系统进行刷盘操作。但是,这必然会降低应用的执行性能,而且,也不是能百分之百保证数据安全的。应用程序在这个问题上,只能取舍,不能解决。
Kafka 其实在 Broker 端设计了一系列的参数,来控制刷盘操作的频率。如果对这些频率进行深度定制,是可以实现来一个消息就进行一次刷盘的“同步刷盘”效果的。但是,这样的定制显然会大大降低 Kafka 的执行效率,这与 Kafka 的设计初衷是不符合的。所以,在实际应用时,我们通常也只能根据自己的业务场景进行权衡。
Kafka 在服务端设计了几个参数,来控制刷盘的频率:

flush.ms : 多⻓时间进行一次强制刷盘。
flush.msThis setting allows specifying a time interval at which we will force an fsync of data written to thelog. For example if this was set to 1000 we would fsync after 1000 ms had passed. In general werecommend you not set this and use replication for durability and allow the operating system'sbackground flush capabilities as it is more efficient.Type: longDefault: 9223372036854775807Valid Values: [0,...]Server Default Property: log.flush.interval.msImportance: mediumlog.flush.interval.messages:表示当同一个 Partiton 的消息条数积累到这个数量时,就会申请一次刷盘操作。默认是 Long.MAX。
The number of messages accumulated on a log partition before messages are flushed to diskType: longDefault: 9223372036854775807Valid Values: [1,...]Importance: highUpdate Mode: cluster-widelog.flush.interval.ms:当一个消息在内存中保留的时间,达到这个数量时,就会申请一次刷盘操作。他的默认值是空。如果这个参数配置为空,则生效的是下一个参数。
log.flush.interval.msThe maximum time in ms that a message in any topic is kept in memory before flushed to disk. If notset, the value in log.flush.scheduler.interval.ms is usedType: longDefault: nullValid Values:
Importance: highUpdate Mode: cluster-widelog.flush.scheduler.interval.ms:检查是否有日志文件需要进行刷盘的频率。默认也是 Long.MAX。
log.flush.scheduler.interval.msThe frequency in ms that the log flusher checks whether any log needs to be flushed to diskType: longDefault: 9223372036854775807Valid Values:
Importance: highUpdate Mode: read-only 这里可以看到,Kafka 为了最大化性能,默认是将刷盘操作交由了操作系统进行统一管理。

另外在这里也能看出,Kafka 并没有实现写一个消息依旧进行一次刷盘的“同步刷盘”机制。也就是说,Kafka 无法保证非正常断电情况下的消息安全。这其实不光是 Kafka 面临的问题,而是所有应用程序都需要面临的问题。在 RabbitMQ 中,官网明确提出,服务端并不完全保证消息不丢失,如果需要提升消息安全性,就只能通过 Publisher Confirms 机制,让客户端参与验证。而 RocketMQ 提供了“同步刷盘”的配置选项。但是如果真的每来一个消息就调用一次刷盘操作,那么任何服务器都是无法承受的。 RocketMQ 是如何实现同步刷盘的呢?
日后可以关注一下。
四、 Kafka 日志索引详解.md

