---


title: "三、Kafka集群工作机制详解"
description: "Leader Partition 状态如何记录 2、Leader Partition 选举机制 3、Leader Partition 自动平衡机制四、 Kafk"
    一、zookeeper集群数据梳理 二、Controller Broker选举机制 三、Leader Partition选举机制 1、Leader Partition状态如何记录 2、Leader Partition选举机制 3、Leader Partition自动平衡机制 四、Kafka的Partition故障恢复机制 五、HW一致性保障-Epoch更新机制 六、章节总结 三、Kafka集...
author: hsc
date: 2023-09-20 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Kafka', 'RocketMQ', 'Zookeeper']
toc: true


---

### 一、 zookeeper 集群数据梳理二、 Controller Broker 选举机制三、 Leader Partition 选举机制
1、Leader Partition 状态如何记录 2、Leader Partition 选举机制 3、Leader Partition 自动平衡机制四、 Kafka 的 Partition 故障恢复机制五、 HW 一致性保障-Epoch 更新机制六、章节总结三、 Kafka 集群工作机制详解-- 楼兰这一部分主要是理解 Kafka 的集群工作机制。
Kafka 为了保证高吞吐、高性能、高可扩展的三高架构,做了非常多复杂的设计。为了让这些抽象的设计思路能够更清晰的展现在你面前,后面两个章节会给你找两条简单清晰的主线。一个是存在 Zookeeper 中的数据,一个是存在服务器上的日志。
Kafka 依赖很多的存储数据,但是,总体上是有划分的。 Kafka 会将每个服务的不同之处,也就是状态信息,保存到 Zookeeper 中。通过 Zookeeper 中的数据,指导每个 Kafka 进行与其他 Kafka 节点不同的业务逻辑。而将状态信息抽离后,剩下的数据,就可以直接存在 Kafka 本地,所有 Kafka 服务都以相同的逻辑运行。这种状态信息分离的设计,让 Kafka 有非常好的集群扩展性。
这一章节,我们就先来看看 Zookeeper 中存储的元数据。
一、 zookeeper 集群数据梳理 Kafka 将状态信息保存在 Zookeeper 中,这些状态信息记录了每个 Kafka 的 Broker 服务与另外的 Broker 服务有什么不同。通过这些差异化的功能,共同体现出集群化的业务能力。这些数据,需要在集群中各个 Broker 之间达成共识,因此,需要存储在一个所有集群都能共同访问的第三方存储中。
这些共识数据需要保持强一致性,这样才能保证各个 Broker 的分工是同步、清晰的。而基于 CP 实现的 Zookeeper 就是最好的选择。
另外,Zookeeper 的 Watcher 机制也可以很好的减少 Broker 读取 Zookeeper 的次数。
Kafka 在 Zookeeper 上管理了哪些数据呢?这个问题可以先回顾一下 Kafka 的整体集群状态结构,然后再去 Zookeeper 上验证。
Kafka 的整体集群结构如下图。其中红色字体标识出了重要的状态信息。

Kafka 的集群中,最为主要的状态信息有两个。一个是在多个 Broker 中,需要选举出一个 Broker,担任 Controller⻆色。由 Controller⻆色来管理整个集群中的分区和副本状态。另一个是在同一个 Topic 下的多个 Partition 中,需要选举出一个 Leader⻆色。由 Leader⻆色的 Partition 来负责与客户端进行数据交互。
这些状态信息都被 Kafka 集群注册到了 Zookeeper 中。 Zookeeper 数据整体如下图:

查看 Zookeeper 的数据,可以使用 IDEA 中的 Zookeeper Manager 插件对于 Kafka 往 Zookeeper 上注册的这些节点,大部分都是比较简明的。比如/brokers/ids 下,会记录集群中的所有 BrokerId,/topics 目录下,会记录当前 Kafka 的 Topic 相关的 Partition 分区等信息。下面就从这些 Zookeeper 的基础数据开始,来逐步梳理 Kafka 的 Broker 端的重要流程。
例如集群中每个 Broker 启动后,都会往 Zookeeper 注册一个临时节点/broker/ids/{BrokerId}。而如果 Kafka 服务停了,Zookeeper 上对应的临时节点就会注销。
二、 Controller Broker 选举机制在 Kafka 集群进行工作之前,需要选举出一个 Broker 来担任 Controller⻆色,负责整体管理集群内的分区和副本状态。选举 Controller 的过程就是通过抢占 Zookeeper 的/controller 节点来实现的。
当一个集群内的 Kafka 服务启动时,就会尝试往 Zookeeper 上创建一个/controller 临时节点,并将自己的 brokerid 写入这个节点。节点的内容如下:
{"version":2,"brokerid":2,"timestamp":"1723447688383","kraftControllerEpoch":-1}Zookeeper 会保证在一个集群中,只会有一个 broker 能够成功创建这个节点。后续 broker 创建不成功,就会注册一个监听,一旦/controller 临时节点被删除了,就会重新开始注册/controller 节点,争取成为新的 controller。
这个注册成功的 broker 就成了集群当中的 Controller 节点。这个 broker 注册成功后,就会由 zookeeper 维护与这个 broker 的心跳连接。 broker 会定期向 zookeeper 发送心跳以保持连接状态。一旦 zookeeper⻓时间检测不到这个 broker 的心跳信息,就会删除临时节点。这样就会有下一个 broker 成功注册/contrller,同时更新 version。
成为新的 Controller。这就是 Kafka 基于 Zookeeper 的 Controller 选举机制。
选举产生的 Controller 节点,就会负责监听 Zookeeper 中的其他一些关键节点,触发集群的相关管理工作。例如:
监听 Zookeeper 中的/brokers/ids 节点,感知 Broker 增减变化。
监听/brokers/topics,感知 topic 以及对应的 partition 的增减变化。
监听/admin/delete_topic 节点,处理删除 topic 的动作。
另外,Controller 还需要负责将元数据推送给其他 Broker。
三、 Leader Partition 选举机制 1、Leader Partition 状态如何记录

在 Kafka 中,一个 Topic 下的所有消息,是分开存储在不同的 Partition 中的。在使用 kafka-topics.sh 脚本创建 Topic 时,可以通过--partitions 参数指定 Topic 下包含多少个 Partition,还可以通过--replication-factors 参数指定每个 Partition 有几个备份。
在一个 Partition 的众多备份中,需要选举出一个 Leader Partition,负责对接所有的客户端请求,并将消息优先保存,然后再通知其他 Follower Partition 来同步消息。
在理解 Leader Partition 选举机制前,需要了解几个基础的概念:
AR: Assigned Repllicas。 表示 Kafka 分区中的所有副本(存活的和不存活的)
ISR: 表示在所有 AR 中,服务正常,保持与 Leader 同步的 Follower 集合。如果 Follower⻓时间没有向 Leader 发送通信请求(超时时间由 replica.lag.time.max.ms 参数设定,默认 30S),那么这个 Follower 就会被提出 ISR 中。(在老版本的 Kafka 中,还会考虑 Partition 与 Leader Partition 之间同步的消息差值,大于参数 replica.lag.max.messages 条就会被移除 ISR。现在版本已经移除了这个参数。)
OSR:表示从 ISR 中踢出的节点。记录的是那些服务有问题,延迟过多的副本。
其中,AR 和 ISR 比较关键,可以通过 kafka-topics.sh 的--describe 指令查看。
[root@192-168-65-112 kafka_2.13-3.8.0]# bin/kafka-topics.sh --bootstrap-serverworker1:9092 --describe --topic disTopic[2024-08-12 15:42:57,462] WARN [AdminClient clientId=adminclient-1] TheDescribeTopicPartitions API is not supported, using Metadata API to describe topics.(org.apache.kafka.clients.admin.KafkaAdminClient)
Topic: disTopic TopicId: CNrWfmEgSBqc9gLClemrXw PartitionCount: 3 ReplicationFactor:
2 Configs:
Topic: disTopic Partition: 0 Leader: 1 Replicas: 1,0 Isr: 0,1Elr: N/A LastKnownElr: N/ATopic: disTopic Partition: 1 Leader: 2 Replicas: 0,2 Isr: 2,0Elr: N/A LastKnownElr: N/ATopic: disTopic Partition: 2 Leader: 2 Replicas: 2,1 Isr: 2,1Elr: N/A LastKnownElr: N/A 这个结果中,AR 就是 Replicas 列中的 Broker 集合。而这个指令中的所有信息,其实都是被记录在 Zookeeper 中的。

2、Leader Partition 选举机制接下来,Kafka 是如何在这些 Partition 中选举产生 Leader Partition 的呢?
我们不妨来做一个实验。

# 1、创建一个备份因子为 3 的 Topic。每个 Partition 有 3 个备份
[root@192-168-65-112 kafka_2.13-3.8.0]# bin/kafka-topics.sh --bootstrap-serverworker1:9092 --create --replication-factor 3 --partitions 4 --topic secondTopicCreated topic secondTopic.
# 2、查看 Topic 的 Partition 情况。可以注意到,默认的 Leader 就是 Replicas 中的第一个。
[root@192-168-65-112 kafka_2.13-3.8.0]# bin/kafka-topics.sh -bootstrap-server worker1:9092--describe --topic secondTopic[2024-08-12 16:50:33,594] WARN [AdminClient clientId=adminclient-1] TheDescribeTopicPartitions API is not supported, using Metadata API to describe topics.(org.apache.kafka.clients.admin.KafkaAdminClient)
Topic: secondTopic TopicId: DNNw-hXqQCOW61shM7zZ2Q PartitionCount: 4ReplicationFactor: 3 Configs:
Topic: secondTopic Partition: 0 Leader: 1 Replicas: 1,0,2 Isr: 1,0,2Elr: N/A LastKnownElr: N/ATopic: secondTopic Partition: 1 Leader: 0 Replicas: 0,2,1 Isr: 0,2,1Elr: N/A LastKnownElr: N/ATopic: secondTopic Partition: 2 Leader: 2 Replicas: 2,1,0 Isr: 2,1,0Elr: N/A LastKnownElr: N/ATopic: secondTopic Partition: 3 Leader: 1 Replicas: 1,2,0 Isr: 1,2,0Elr: N/A LastKnownElr: N/A
# 3,在 worker3 上停掉 kafka 服务
[root@192-168-65-193 kafka_2.13-3.8.0]# bin/kafka-server-stop.sh
# 4、再次查看 SecondTopic 上的 Partiton 分区情况 Leader 依然是 Replicas 中的第一个存活的 Broker。
[root@192-168-65-112 kafka_2.13-3.8.0]# bin/kafka-topics.sh -bootstrap-server worker1:9092--describe --topic secondTopic[2024-08-12 16:52:51,510] WARN [AdminClient clientId=adminclient-1] TheDescribeTopicPartitions API is not supported, using Metadata API to describe topics.(org.apache.kafka.clients.admin.KafkaAdminClient)
Topic: secondTopic TopicId: DNNw-hXqQCOW61shM7zZ2Q PartitionCount: 4ReplicationFactor: 3 Configs:
Topic: secondTopic Partition: 0 Leader: 1 Replicas: 1,0,2 Isr: 1,2Elr: N/A LastKnownElr: N/ATopic: secondTopic Partition: 1 Leader: 2 Replicas: 0,2,1 Isr: 2,1Elr: N/A LastKnownElr: N/ATopic: secondTopic Partition: 2 Leader: 2 Replicas: 2,1,0 Isr: 2,1Elr: N/A LastKnownElr: N/ATopic: secondTopic Partition: 3 Leader: 1 Replicas: 1,2,0 Isr: 1,2Elr: N/A LastKnownElr: N/A 从实验中可以看到,当 BrokerId=0 的 kafka 服务停止后,0 号 BrokerId 就从所有 Partiton 的 ISR 列表中剔除了。
然后,Partition 1 的 Leader 节点原本是 Broker 0,当 Broker 0 的 Kafka 服务停止后,都重新进行了 Leader 选举。
Parition 1 预先评估的是 Replicas 列表中 Broker 0 后面的 Broker 2,Broker2 在 ISR 列表中,所以他被最终选举成为 Leader。
所以,Kafka 选举 Leader Partition 的机制非常简单高效。在选举 Leader Partition 时,会按照 AR 中的排名顺序,靠前的优先选举。只要当前 Partition 在 ISR 列表中,也就是是存活的,那么这个节点就会被选举成为 Leader Partition。
当 Partiton 选举完成后,Zookeeper 中的信息也被及时更新了。这样这些选举结果,就可以在集群所有 Broker 中达成共识。
# Zookeeper 上的/brokers/topics/secondTopic
{"partitions":{"0":[1,0,2],"1":[0,2,1],"2":[2,1,0],"3":[1,2,0]},"topic_id":"DNNwhXqQCOW61shM7zZ2Q","adding_replicas":{},"removing_replicas":{},"version":3}

3、Leader Partition 自动平衡机制 Leader Partitoin 选举机制能够保证每一个 Partition 同一时刻有且仅有一个 Leader Partition。但是,是不是只要分配好了 Leader Partition 就够了呢?
在一组 Partiton 中,Leader Partition 通常是比较繁忙的节点,因为他要负责与客户端的数据交互,以及向 Follower 同步数据。默认情况下,Kafka 会尽量将 Leader Partition 分配到不同的 Broker 节点上,用以保证整个集群的性能压力能够比较平均。
但是,经过 Leader Partition 选举后,这种平衡就有可能会被打破,让 Leader Partition 过多的集中到同一个 Broker 上。这样,这个 Broker 的压力就会明显高于其他 Broker,从而影响到集群的整体性能。
为此,Kafka 设计了 Leader Partition 自动平衡机制,当发现 Leader 分配不均衡时,自动进行 Leader Partition 调整。
Kafka 在进行 Leader Partition 自平衡时的逻辑是这样的:他会认为 AR 当中的第一个节点就应该是 Leader 节点。这种选举结果成为 preferred election 理想选举结果。 Controller 会定期检测集群的 Partition 平衡情况,在开始检测时,Controller 会依次检查所有的 Broker。当发现这个 Broker 上的不平衡的 Partition 比例高于 leader.imbalance.per.broker.percentage 阈值时,就会触发一次 Leader Partiton 的自平衡。
这是官方文档的部分截图。
这个机制涉及到 Broker 中 server.properties 配置文件中的几个重要参数:

#1 自平衡开关。默认 true
auto.leader.rebalance.enableEnables auto leader balancing. A background thread checks the distribution of partitionleaders at regular intervals, configurable by `leader.imbalance.check.interval.seconds`.If the leader imbalance exceeds `leader.imbalance.per.broker.percentage`, leader rebalanceto the preferred leader for partitions is triggered.Type: booleanDefault: trueValid Values:
Importance: highUpdate Mode: read-only
#2 自平衡扫描间隔
leader.imbalance.check.interval.secondsThe frequency with which the partition rebalance check is triggered by the controllerType: longDefault: 300Valid Values: [1,...]Importance: highUpdate Mode: read-only
#3 自平衡触发比例
leader.imbalance.per.broker.percentageThe ratio of leader imbalance allowed per broker. The controller would trigger a leaderbalance if it goes above this value per broker. The value is specified in percentage.Type: intDefault: 10Valid Values:
Importance: highUpdate Mode: read-only 这几个参数可以到 broker 的 server.properties 文件中修改。但是注意要修改集群中所有 broker 的文件,并且要重启 Kafka 服务才能生效。
另外,你也可以通过手动调用 kafka-leader-election.sh 脚本,触发一次自平衡。例如:

# 启动 worker3 上的 Kafka 服务,Broker 上线。
# secondTopic 的 partion1 不是理想状态。理想的 leader 应该是 Replcas 中的 0,因为此时 0 已经在 ISR 列表中了。
[root@192-168-65-112 kafka_2.13-3.8.0]# bin/kafka-topics.sh -bootstrap-server worker1:9092--describe --topic secondTopic[2024-08-12 17:16:48,966] WARN [AdminClient clientId=adminclient-1] TheDescribeTopicPartitions API is not supported, using Metadata API to describe topics.(org.apache.kafka.clients.admin.KafkaAdminClient)
Topic: secondTopic TopicId: DNNw-hXqQCOW61shM7zZ2Q PartitionCount: 4ReplicationFactor: 3 Configs:
Topic: secondTopic Partition: 0 Leader: 1 Replicas: 1,0,2 Isr: 1,2,0Elr: N/A LastKnownElr: N/ATopic: secondTopic Partition: 1 Leader: 2 Replicas: 0,2,1 Isr: 2,1,0Elr: N/A LastKnownElr: N/ATopic: secondTopic Partition: 2 Leader: 2 Replicas: 2,1,0 Isr: 2,1,0Elr: N/A LastKnownElr: N/ATopic: secondTopic Partition: 3 Leader: 1 Replicas: 1,2,0 Isr: 1,2,0Elr: N/A LastKnownElr: N/A
# 手动触发所有 Topic 的 Leader Partition 自平衡
[root@192-168-65-112 kafka_2.13-3.8.0]# bin/kafka-leader-election.sh --bootstrap-serverworker1:9092 --election-type preferred --topic secondTopic --partition 1Valid replica already elected for partitions secondTopic-1
# 自平衡后 secondTopic 的 partition2 就变成理想状态了。
[root@192-168-65-112 kafka_2.13-3.8.0]# bin/kafka-topics.sh -bootstrap-server worker1:9092--describe --topic secondTopic[2024-08-12 17:18:50,015] WARN [AdminClient clientId=adminclient-1] TheDescribeTopicPartitions API is not supported, using Metadata API to describe topics.(org.apache.kafka.clients.admin.KafkaAdminClient)
Topic: secondTopic TopicId: DNNw-hXqQCOW61shM7zZ2Q PartitionCount: 4ReplicationFactor: 3 Configs:
Topic: secondTopic Partition: 0 Leader: 1 Replicas: 1,0,2 Isr: 1,2,0Elr: N/A LastKnownElr: N/ATopic: secondTopic Partition: 1 Leader: 0 Replicas: 0,2,1 Isr: 2,1,0Elr: N/A LastKnownElr: N/ATopic: secondTopic Partition: 2 Leader: 2 Replicas: 2,1,0 Isr: 2,1,0Elr: N/A LastKnownElr: N/ATopic: secondTopic Partition: 3 Leader: 1 Replicas: 1,2,0 Isr: 1,2,0Elr: N/A LastKnownElr: N/A 但是要注意,这样**Leader Partition 自平衡的过程是一个非常重的操作,因为要涉及到大量消息的转移与同步。**所以在很多对性能要求比较高的线上环境,会选择将参数 auto.leader.rebalance.enable 设置为 false,关闭 Kafka 的 Leader Partition 自平衡操作,而用其他运维的方式,在业务不繁忙的时间段,手动进行 LeaderPartiton 自平衡,尽量减少自平衡过程对业务的影响。
四、 Kafka 的 Partition 故障恢复机制 Kafka 设计时要面对的就是各种不稳定的网络以及服务环境。如果 Broker 的服务不稳定,随时崩溃,Kafka 集群要怎么保证数据安全呢?
当一组 Partition 中选举出了一个 Leader 节点后,这个 Leader 节点就会优先写入并保存 Producer 传递过来的消息,然后再同步给其他 Follower。当 Leader Partition 所在的 Broker 服务发生宕机时,Kafka 就会触发 LeaderPartition 的重新选举。但是,在选举过程中,原来 Partition 上的数据是如何处理的呢?
Kafka 为了保证消息能够在多个 Parititon 中保持数据同步,内部记录了两个关键的数据:

LEO(Log End Offset): 每个 Partition 的最后一个 Offset 这个参数比较好理解,每个 Partition 都会记录自己保存的消息偏移量。 leader partition 收到并记录了生产者发送的一条消息,就将 LEO 加 1。而接下来,follower partition 需要从 leader partition 同步消息,每同步到一个消息,自己的 LEO 就加 1。通过 LEO 值,就知道各个 follower partition 与 leader partition 之间的消息差距。
HW(High Watermark): 一组 Partiton 中最小的 LEO。
follower partition 每次往 leader partition 同步消息时,都会同步自己的 LEO 给 leader partition。这样 leaderpartition 就可以计算出这个 HW 值,并最终会同步给各个 follower partition。leader partition 认为这个 HW 值以前的消息,都是在所有 follower partition 之间完成了同步的,是安全的。这些安全的消息就可以被消费者拉取过去了。而 HW 值之后的消息,就是不安全的,是可能丢失的。这些消息如果被消费者拉取过去消费了,就有可能造成数据不一致。
也就是说,在所有服务都正常的情况下,当一个消息写入到 Leader Partition 后,并不会立即让消费者感知。
而是会等待其他 Follower Partition 同步。这个过程中就会推进 HW。当 HW 超过当前消息时,才会让消费者感知。比如在上图中,4 号往后的消息,虽然写入了 Leader Partition,但是消费者是消费不到的。
这跟生产者的 acks 应答参数是不一样的当服务出现故障时,如果是 Follower 发生故障,这不会影响消息写入,只不过是少了一个备份而已。处理相对简单一点。 Kafka 会做如下处理:
 . 将故障的 Follower 节点临时提出 ISR 集合。而其他 Leader 和 Follower 继续正常接收消息。
 . 出现故障的 Follower 节点恢复后,不会立即加入 ISR 集合。该 Follower 节点会读取本地记录的上一次的 HW,将自己的日志中高于 HW 的部分信息全部删除掉,然后从 HW 开始,向 Leader 进行消息同步。
 . 等到该 Follower 的 LEO 大于等于整个 Partiton 的 HW 后,就重新加入到 ISR 集合中。这也就是说这个 Follower 的消息进度追上了 Leader。

如果是 Leader 节点出现故障,Kafka 为了保证消息的一致性,处理就会相对复杂一点。
 . Leader 发生故障,会从 ISR 中进行选举,将一个原本是 Follower 的 Partition 提升为新的 Leader。这时,消息有可能没有完成同步,所以新的 Leader 的 LEO 会低于之前 Leader 的 LEO。
 . Kafka 中的消息都只能以 Leader 中的备份为准。其他 Follower 会将各自的 Log 文件中高于 HW 的部分全部清理掉,然后从新的 Leader 中同步数据。
 . 旧的 Leader 恢复后,将作为 Follower 节点,进行数据恢复。
在这个过程当中,Kafka 注重的是保护多个副本之间的数据一致性。但是这样,消息的安全性就得不到保障。
例如在上述示例中,原本 Partition0 中的 4,5,6,7 号消息就被丢失掉了。也就是说,Kafka 在 Partition 恢复的过程当中,有可能会有消息丢失。

从这个⻆度来看,在服务极端不稳定的极端情况下,Kafka 为了保证高性能,其实是牺牲了数据安全性的。 Kafka 并没有保证消息绝对安全。而 RocketMQ 在这一方面做了改善,优先保证数据安全。后续学习 RocketMQ 时,可以对比 Kafka 理解一下。
这种情况下,既然消息不安全,那么如何提升消息的安全性呢?基本思路是,服务端处理不了,那就交给客户端自己处理。例如,将 Producer 的 ACKS 参数设置成 all 或者-1,然后 Producer 根据每次发消息的返回值,自行进行消息确认或者重复投递。
在这里你或许会有一个疑问,这个机制中有一个很重要的前提,就是各个 Broker 中记录的 HW 是一致的。但是 HW 和 LEO 同样是一个分布式的值,怎么保证 HW 在多个 Broker 中是一致的呢?
五、 HW 一致性保障-Epoch 更新机制有了 HW 机制后,各个 Partiton 的数据都能够比较好的保持统一。但是,实际上,HW 值在一组 Partition 里并不是总是一致的。
Leader Partition 需要计算出 HW 值,就需要保留所有 Follower Partition 的 LEO 值。
但是,对于 Follower Partition,他需要先将消息从 Leader Partition 拉取到本地,才能向 Leader Partition 上报 LEO 值。所有 Follower Partition 上报后,Leader Partition 才能更新 HW 的值,然后 Follower Partition 在下次拉取消息时,才能更新 HW 值。所以,Leader Partiton 的 LEO 更新和 Follower Partition 的 LEO 更新,在时间上是有延迟的。这也导致了 Leader Partition 上更新 HW 值的时刻与 Follower Partition 上跟新 HW 值的时刻,是会出现延迟的。这样,如果有多个 Follower Partition,这些 Partition 保存的 HW 的值是不统一的。当然,如果服务一切正常,最终 Leader Partition 还是会正常推进 HW,能够保证 HW 的最终一致性。但是,当 Leader Partition 出现切换,所有的 Follower Partition 都按照自己的 HW 进行数据恢复,就会出现数据不一致的情况。
因此,Kafka 还设计了 Epoch 机制,来保证 HW 的一致性。

 . Epoch 是一个单调递增的版本号,每当 Leader Partition 发生变更时,该版本号就会更新。所以,当有多个 Epoch 时,只有最新的 Epoch 才是有效的,而其他 Epoch 对应的 Leader Partition 就是过期的,无用的 Leader。
 . 每个 Leader Partition 在上任之初,都会新增一个新的 Epoch 记录。这个记录包含更新后端的 epoch 版本号,以及当前 Leader Partition 写入的第一个消息的偏移量。例如(1,100)。表示 epoch 版本号是 1,当前 Leader Partition 写入的第一条消息是 100. Broker 会将这个 epoch 数据保存到内存中,并且会持久化到本地一个 leader-epoch-checkpoint 文件当中。
 . 这个 leader-epoch-checkpoint 会在所有 Follower Partition 中同步。当 Leader Partition 有变更时,新的 Leader Partition 就会读取这个 Epoch 记录,更新后添加自己的 Epoch 记录。
 . 接下来其他 Follower Partition 要更新数据时,就可以不再依靠自己记录的 HW 值判断拉取消息的起点。而可以根据这个最新的 epoch 条目来判断。
这个关键的 leader-epoch-checkpoint 文件保存在 Broker 上每个 partition 对应的本地目录中。这是一个文本文件,可以直接查看。他的内容大概是这样样子的:
[root@192-168-65-193 secondTopic-1]# pwd/app/kafka/logs/secondTopic-1[root@192-168-65-193 secondTopic-1]# cat leader-epoch-checkpoint012 0 其中第一行版本号第二行表示下面的记录数。这两行数据没有太多的实际意义。

从第三行开始,可以看到两个数字。这两个数字就是 epoch 和 offset。epoch 就是表示 leader 的 epoch 版本。
从 0 开始,当 leader 变更一次 epoch 就会+1。offset 则对应该 epoch 版本的 leader 写入第一条消息的 offset。可以理解为用户可以消费到的最早的消息 offset。
例如对于之前创建的 secondTopic,partition1 经过了两次 Leader 切换,所有 epoch 更新为 2。而由于还没有写入消息,所以切换时的 offset 是 0。
六、章节总结 Kafka 其实天生就是为了集群而生,即使单个节点运行 Kafka,他其实也是作为一个集群运行的。而 Kafka 为了保证在各种网络抽⻛,服务器不稳定等复杂情况下,保证集群的高性能,高可用,高可扩展三高,做了非常多的设计。而这一章节,其实是从可⻅的 Zookeeper 注册信息为入口,理解 Kafka 的核心集群机制。回头来看今天总结的这些集群机制,其实核心都是为了保持整个集群中 Partition 内的数据一致性。有了这一系列的数据一致性保证,Kafka 集群才能在复杂运行环境下保持高性能、高可用、高可扩展三高特性。而这其实也是我们去理解互联网三高问题最好的经验。
三、 Kafka 集群工作机制详解.md

