---


title: "二、Kafka客户端消息流转流程"
description: "消息发送者主流程 2、消息消费者主流程二、从客户端属性来梳理客户端工作机制 1、消费者分组消费机制 2、生产者拦截器机制 3、消息序列化机制 4、消息分区路由机"
    一、从基础的客户端说起 1、消息发送者主流程 2、消息消费者主流程 二、从客户端属性来梳理客户端工作机制 1、消费者分组消费机制 2、生产者拦截器机制 3、消息序列化机制 4、消息分区路由机制 5、生产者消息缓存机制 6、发送应答机制 7、生产者消息幂等性 8、生产者数据压缩机制 9、生产者消息事务 三、客户端流程总结 四、SpringBoot集成Kafka 二、Kafka客户端消息流转流程...
author: hsc
date: 2023-08-28 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Redis', 'Kafka', 'RocketMQ', 'Netty']
toc: true


---

### 一、从基础的客户端说起
1、消息发送者主流程 2、消息消费者主流程二、从客户端属性来梳理客户端工作机制 1、消费者分组消费机制 2、生产者拦截器机制 3、消息序列化机制 4、消息分区路由机制 5、生产者消息缓存机制 6、发送应答机制 7、生产者消息幂等性 8、生产者数据压缩机制 9、生产者消息事务三、客户端流程总结四、 SpringBoot 集成 Kafka 二、 Kafka 客户端消息流转流程-- 楼兰这一章节将重点介绍 Kafka 的 HighLevel API 使用,并通过这些 API,构建起 Kafka 整个消息发送以及消费的主线流程。
Kafka 提供了两套客户端 API,HighLevel API 和 LowLevel API。 HighLevel API 封装了 kafka 的运行细节,使用起来比较简单,是企业开发过程中最常用的客户端 API。 而 LowLevel API 则需要客户端自己管理 Kafka 的运行细节,Partition,Offset 这些数据都由客户端自行管理。这层 API 功能更灵活,但是使用起来非常复杂,也更容易出错。只在极少数对性能要求非常极致的场景才会偶尔使用。我们的重点是 HighLeve API 。
一、从基础的客户端说起 Kafka 提供了非常简单的客户端 API。只需要引入一个 Maven 依赖即可:
<dependency><groupId>org.apache.kafka</groupId><spanrtifactId>kafka_2.13</artifactId><version>3.8.0</version></dependency>1、消息发送者主流程然后可以使用 Kafka 提供的 Producer 类,快速发送消息。
发送消息前,Topic 需要提前创建。建议创建指令: bin/kafka-topics.sh --bootstrap-server worker1 9092 --create --topic Topic --partitions 3--replication-factor 2 或者参⻅配套案例。

public class MyProducer {private static final String BOOTSTRAP_SERVERS = "worker1:9092,worker2:9092,worker3:9092";
private static final String TOPIC = "disTopic";
public static void main(String[] args) throws ExecutionException, InterruptedException {//PART1:设置发送者相关属性 Properties props = new Properties();
// 此处配置的是 kafka 的端口 props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP_SERVERS);
// 配置 key 的序列化类 props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG,"org.apache.kafka.common.serialization.StringSerializer");
// 配置 value 的序列化类 props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG,"org.apache.kafka.common.serialization.StringSerializer");
Producer<String,String> producer = new KafkaProducer<>(props);
CountDownLatch latch = new CountDownLatch(5);
for(int i = 0; i < 5; i++) {//Part2:构建消息 ProducerRecord<String, String> record = new ProducerRecord<>(TOPIC, Integer.toString(i), "MyProducer" + i);
//Part3:发送消息//单向发送:不关心 服务端的应答。
producer.send(record);
System.out.println("message "+i+" sended");
//同步发送:获取服务端应答消息前,会阻塞当前线程。
RecordMetadata recordMetadata = producer.send(record).get();
String topic = recordMetadata.topic();
int partition = recordMetadata.partition();
long offset = recordMetadata.offset();
String message = recordMetadata.toString();
System.out.println("message:["+ message+"] sended with topic:"+topic+"; partition:"+partition+ ";offset:"+offset);
//异步发送:消息发送后不阻塞,服务端有应答后会触发回调函数 producer.send(record, new Callback() {@Overridepublic void onCompletion(RecordMetadata recordMetadata, Exception e) {if(null != e){System.out .println("消息发送失败,"+e.getMessage());
e.printStackTrace();
}else{String topic = recordMetadata.topic();
long offset = recordMetadata.offset();
String message = recordMetadata.toString();
System.out.println("message:["+ message+"] sended with topic:"+topic+";offset:"+offset);
}latch.countDown();
}});
}/ /消息处理完才停止发送者。
latch.await();
producer.close();
}}整体来说,构建 Producer 分为三个步骤:
 . 设置 Producer 核心属性 :Producer 可选的属性都可以由 ProducerConfig 类管理。比如 ProducerConfig.BOOTSTRAP_SERVERS_CONFIG 属性,显然就是指发送者要将消息发到哪个 Kafka 集群上。这是每个 Producer 必选的属性。在 ProducerConfig 中,对于大部分比较重要的属性,都配置了对应的 DOC 属性进行描述。
 . 构建消息:Kafka 的消息是一个 Key-Value 结构的消息。其中,key 和 value 都可以是任意对象类型。其中,key 主要是用来进行 Partition 分区的,业务上更关心的是 value。
 . 使用 Producer 发送消息。:通常用到的就是单向发送、同步发送和异步发送者三种发送方式。
2、消息消费者主流程接下来可以使用 Kafka 提供的 Consumer 类,快速消费消息。

public class MyConsumer {private static final String BOOTSTRAP_SERVERS = "worker1:9092,worker2:9092,worker3:9092";
private static final String TOPIC = "disTopic";
public static void main(String[] args) {//PART1:设置发送者相关属性 Properties props = new Properties();
//kafka 地址 props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP_SERVERS);
//每个消费者要指定一个 groupprops.put(ConsumerConfig.GROUP_ID_CONFIG, "test");
//key 序列化类 props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, "org.apache.kafka.common.serialization.StringDeserializer");
//value 序列化类 props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, "org.apache.kafka.common.serialization.StringDeserializer");
Consumer<String, String> consumer = new KafkaConsumer<>(props);
consumer.subscribe(Arrays.asList(TOPIC));
while (true) {//PART2:拉取 消息// 100 毫秒超时时间 ConsumerRecords<String, String> records = consumer.poll(Duration.ofNanos(100));
//PART3:处理消息 for (ConsumerRecord<String, String> record : records) {System.out.println("offset = " + record.offset() + ";key = " + record.key() + "; value= " + record.value());
}/ /提交 offset,消息就不会重复推送。
consumer.commitSync(); //同步提 交,表示必须等到 offset 提交完毕,再去消费下一批数据。
// consumer.commitAsync(); //异步提交,表示发送完提交 offset 请求后,就开始消费下一批数 据了。不用等到 Broker 的确认。
}}}整体来说,Consumer 同样是分为三个步骤:
 . 设置 Consumer 核心属性 :可选的属性都可以由 ConsumerConfig 类管理。在这个类中,同样对于大部分比较重要的属性,都配置了对应的 DOC 属性进行描述。同样 BOOTSTRAP_SERVERS_CONFIG 是必须设置的属性。
 . 拉取消息:Kafka 采用 Consumer 主动拉取消息的 Pull 模式。 consumer 主动从 Broker 上拉取一批感兴趣的消息。
 . 处理消息,提交位点:消费者将消息拉取完成后,就可以交由业务自行处理对应的这一批消息了。只是消费者需要向 Broker 提交偏移量 offset。如果不提交 Offset,Broker 会认为消费者端消息处理失败了,还会重复进行推送。
Kafka 的客户端基本就是固定的按照这三个大的步骤运行。在具体使用过程中,最大的变数基本上就是给生产者和消费者的设定合适的属性。这些属性极大的影响了客户端程序的执行方式。
改改配置就学会 Kafka 了?kafka 官方配置: https://kafka.apache.org/documentation/#configuration。看看你晕不晕。
二、从客户端属性来梳理客户端工作机制其实 Kafka 的设计精髓,是在网络不稳定,服务也随时会崩溃的这些作死的复杂场景下,如何保证消息的高并发、高吞吐,那才是 Kafka 最为精妙的地方。但是要理解那些复杂的问题,都是需要建立在这个基础模型基础上的。
1、消费者分组消费机制这是我们在使用 kafka 时,最为重要的一个机制,因此最先进行梳理。
在 Consumer 中,都需要指定一个 GROUP_ID_CONFIG 属性,这表示当前 Consumer 所属的消费者组。他的描述是这样的:
public static final String GROUP_ID_CONFIG = "group.id";
public static final String GROUP_ID_DOC = "A unique string that identifies the consumer group this consumer belongs to.This property is required if the consumer uses either the group management functionality by using <code>subscribe(topic)
</code> or the Kafka-based offset management strategy.";
既然这里提到了 kafka-based offset management strategy,那是不是也有非 Kafka 管理 Offset 的策略呢?
另外,还有一个相关的参数 GROUP_INSTANCE_ID_CONFIG,可以给组成员设置一个固定的 instanceId,这个参数通常可以用来减少 Kafka 不必要的 rebalance。
从这段描述中看到,对于 Consumer,如果需要在 subcribe 时使用组管理功能以及 Kafka 提供的 offset 管理策略,那就必须要配置 GROUP_ID_CONFIG 属性。这个分组消费机制简单描述就是这样的:

生产者往 Topic 下发消息时,会尽量均匀的将消息发送到 Topic 下的各个 Partition 当中。而这个消息,会向所有订阅了该 Topic 的消费者推送。推送时,每个 ConsumerGroup 中只会推送一份。也就是同一个消费者组中的多个消费者实例,只会共同消费一个消息副本。而不同消费者组之间,会重复消费消息副本。这就是消费者组的作用。
与之相关的还有 Offset 偏移量。这个偏移量表示每个消费者组在每个 Partiton 中已经消费处理的进度。在 Kafka 中,可以看到消费者组的 Offset 记录情况。
[oper@worker1 bin]$ ./kafka-consumer-groups.sh --bootstrap-server worker1:9092 --describe --group test 这个 Offset 偏移量,需要消费者处理完成后主动向 Kafka 的 Broker 提交。提交完成后,Broker 就会更新消费进度,表示这个消息已经被这个消费者组处理完了。但是如果消费者没有提交 Offset,Broker 就会认为这个消息还没有被处理过,就会重新往对应的消费者组进行推送,不过这次,一般会尽量推送给同一个消费者组当中的其他消费者实例。
在示例当中,是通过业务端主动调用 Consumer 的 commitAsync 方法或者 commitSync 方法主动提交的,Kafka 中自然也提供了自动提交 Offset 的方式。
使用自动提交,只需要在 Comsumer 中配置 ENABLE_AUTO_COMMIT_CONFIG 属性即可。
public static final String ENABLE_AUTO_COMMIT_CONFIG = "enable.auto.commit";
private static final String ENABLE_AUTO_COMMIT_DOC = "If true the consumer's offset will be periodically committed in thebackground.";
从这里可以看到,Offset 是 Kafka 进行消息推送控制的关键之处。这里需要思考两个问题:
一、 Offset 是根据 Group、Partition 分开记录的。消费者如果一个 Partition 对应多个 Consumer 消费者实例,那么每个 Consumer 实例都会往 Broker 提交同一个 Partition 的不同 Offset,这时候 Broker 要听谁的?所以一个 Partition 最多只能同时被一个 Consumer 消费。也就是说,示例中四个 Partition 的 Topic,那么同一个消费者组中最多就只能配置四个消费者实例。
二、这么关键的 Offset 数据,保存在 Broker 端,但是却是由"不靠谱"的消费者主导推进,这显然是不够安全的。那么应该如何提高 Offset 数据的安全性呢?如果你有兴趣自己观察,会发现在 Consumer 中,实际上也提供了 AUTO_OFFSET_RESET_CONFIG 参数,来指定消费者组在服务端的 Offset 不存在时如何进行后续消费。(有可能服务端初始化 Consumer Group 的 Offset 失败,也有可能 Consumer Group 当前的 Offset 对应的数据文件被过期删除了。)这就相当于服务端做的兜底保障。
ConsumerConfig.AUTO_OFFSET_RESEWT_CONFIG :当 Server 端没有对应的 Offset 时,要如何处理。 可选项:
earliest: 自动设置为当前最早的 offsetlatest:自动设置为当前最晚的 offsetnone: 如果消费者组对应的 offset 找不到,就向 Consumer 抛异常。
其他选项: 向 Consumer 抛异常。
有了服务端兜底后,消费者应该要如何保证 offset 的安全性呢?有两种方式:一种是异步提交。就是消费者在处理业务的同时,异步向 Broker 提交 Offset。这样好处是消费者的效率会比较高,但是如果消费者的消息处理失败了,而 offset 又成功提交了。这就会造成消息丢失。另一种方式是同步提交。消费者保证处理完所有业务后,再提交 Offset。这样的好处自然是消息不会因为 offset 丢失了。因为如果业务处理失败,消费者就可以不去提交 Offset,这样消息还可以重试。但是坏处是消费者处理信息自然就慢了。另外还会产生消息重复。因为 Broker 端不可能一直等待消费者提交。如果消费者的业务处理时间比较⻓,这时在消费者正常处理消息的过程中,Broker 端就已经等不下去了,认为这个消费者处理失败了。这时就会往同组的其他消费者实例投递消息,这就造成了消息重复处理。

这时,如果采取头疼医头,脚疼医脚的方式,当然都有对应的办法。但是都会显得过于笨重。其实这类问题的根源在于 Offset 反映的是消息的处理进度。而消息处理进度跟业务的处理进度又是不同步的。所有我们可以换一种思路,将 Offset 从 Broker 端抽取出来,放到第三方存储比如 Redis 里自行管理。这样就可以自己控制用业务的处理进度推进 Offset 往前更新。
2、生产者拦截器机制生产者拦截机制允许客户端在生产者在消息发送到 Kafka 集群之前,对消息进行拦截,甚至可以修改消息内容。
这涉及到 Producer 中指定的一个参数:INTERCEPTOR_CLASSES_CONFIGpublic static final String INTERCEPTOR_CLASSES_CONFIG = "interceptor.classes";
public static final String INTERCEPTOR_CLASSES_DOC = "A list of classes to use as interceptors. "
+ "Implementing the<code>org.apache.kafka.clients.producer.ProducerInterceptor</code> interface allows you to intercept (and possibly mutate) therecords "
+ "received by the producer before they are published to the Kafkacluster. By default, there are no interceptors.";
于是,按照他的说明,我们可以定义一个自己的拦截器实现类:
public class MyInterceptor implements ProducerInterceptor {//发送消息时触发@Overridepublic ProducerRecord onSend(ProducerRecord producerRecord) {System.out.println("prudocerRecord : " + producerRecord.toString());
return producerRecord;
}//收到服务端响应时触发@Overridepublic void onAcknowledgement(RecordMetadata recordMetadata, Exception e) {System.out.println("acknowledgement recordMetadata:"+recordMetadata.toString());
}//连接关闭时触发@Overridepublic void close() {System.out.println("producer closed");
}//整理配置项@Overridepublic void configure(Map<String, ?> map) {System.out.println("=====config start======");
for (Map.Entry<String, ?> entry : map.entrySet()) {System.out.println("entry.key:"+entry.getKey()+" === entry.value: "+entry.getValue());
}System.out.println("=====config end======");
}}然后在生产者中指定拦截器类(多个拦截器类,用逗号隔开)
props.put(ProducerConfig.INTERCEPTOR_CLASSES_CONFIG,"com.roy.kfk.basic.MyInterceptor");
拦截器机制一般用得比较少,主要用在一些统一添加时间等类似的业务场景。比如,用 Kafka 传递一些 POJO,就可以用拦截器统一添加时间属性。但是我们平常用 Kafka 传递的都是 String 类型的消息,POJO 类型的消息,Kafka 可以传吗?这就要用到下面的消息序列化机制。
3、消息序列化机制在之前的简单示例中,Producer 指定了两个属性 KEY_SERIALIZER_CLASS_CONFIG 和 VALUE_SERIALIZER_CLASS_CONFIG,对于这两个属性,在 ProducerConfig 中都有配套的说明属性。

public static final String KEY_SERIALIZER_CLASS_CONFIG = "key.serializer";
public static final String KEY_SERIALIZER_CLASS_DOC = "Serializer class for key that implements the<code>org.apache.kafka.common.serialization.Serializer</code> interface.";
public static final String VALUE_SERIALIZER_CLASS_CONFIG = "value.serializer";
public static final String VALUE_SERIALIZER_CLASS_DOC = "Serializer class for value that implements the<code>org.apache.kafka.common.serialization.Serializer</code> interface.";
通过这两个参数,可以指定消息生产者如何将消息的 key 和 value 序列化成二进制数据。在 Kafka 的消息定义中,key 和 value 的作用是不同的。
key 是用来进行分区的可选项。 Kafka 通过 key 来判断消息要分发到哪个 Partition。
如果没有填写 key,那么 Kafka 会自动选择 Partition。
如果填写了 key,那么会通过声明的 Serializer 序列化接口,将 key 转换成一个 byte[]数组,然后对 key 进行 hash,选择 Partition。这样可以保证 key 相同的消息会分配到相同的 Partition 中。
Value 是业务上比较关心的消息。 Kafka 同样需要将 Value 对象通过 Serializer 序列化接口,将 Key 转换成 byte[]数组,这样才能比较好的在网络上传输 Value 信息,以及将 Value 信息落盘到操作系统的文件当中。
生产者要对消息进行序列化,那么消费者拉取消息时,自然需要进行反序列化。所以,在 Consumer 中,也有反序列化的两个配置 public static final String KEY_DESERIALIZER_CLASS_CONFIG = "key.deserializer";
public static final String KEY_DESERIALIZER_CLASS_DOC = "Deserializer class for key that implements the<code>org.apache.kafka.common.serialization.Deserializer</code> interface.";
public static final String VALUE_DESERIALIZER_CLASS_CONFIG = "value.deserializer";
public static final String VALUE_DESERIALIZER_CLASS_DOC = "Deserializer class for value that implements the<code>org.apache.kafka.common.serialization.Deserializer</code> interface.";
在 Kafka 中,对于常用的一些基础数据类型,都已经提供了对应的实现类。但是,如果需要使用一些自定义的消息格式,比如自己定制的 POJO,就需要定制具体的实现类了。
在自己进行序列化机制时,需要考虑的是如何用二进制来描述业务数据。例如对于一个通常的 POJO 类型,可以将他的属性拆分成两种类型:一种类型是定⻓的基础类型,比如 Integer,Long,Double 等。这些基础类型转化成二进制数组都是定⻓的。这类属性可以直接转成序列化数组,在反序列化时,只要按照定⻓去读取二进制数据就可以反序列化了。另一种是不定⻓的浮动类型,比如 String,或者基于 String 的 JSON 类型等。这种浮动类型的基础数据转化成二进制数组,⻓度都是不一定的。对于这类数据,通常的处理方式都是先往二进制数组中写入一个定⻓的数据的⻓度数据(Integer 或者 Long 类型),然后再继续写入数据本身。这样,反序列化时,就可以先读取一个定⻓的⻓度,再按照这个⻓度去读取对应⻓度的二进制数据,这样就能读取到数据的完整二进制内容。
** 渔与⻥** 序列化机制是在高并发场景中非常重要的一个优化机制。高效的系列化实现能够极大的提升分布式系统的网络传输以及数据落盘的能力。例如对于一个 User 对象,即可以使用 JSON 字符串这种简单粗暴的序列化方式,也可以选择按照各个字段进行组合序列化的方式。但是显然后者的占用空间比较小,序列化速度也会比较快。而 Kafka 在文件落盘时,也设计了非常高效的数据序列化实现,这也是 Kafka 高效运行的一大支撑。
在很多其他业务场景中,也需要我们提供更高效的序列化实现。例如使用 MapReduce 框架时,就需要自行定义数据的序列化方式。使用 Netty 框架进行网络调用时,为了防止粘包,也需要定制数据的序列化机制。在这些场景下,进行序列化的基础思想,和我们这里介绍的也是一样的。当然,如果我们可以进一步设计出更简短高效的数据压缩算法,那也就能更进一步提高数据传输的效率。比如对二进制数据进行压缩。而这就是算法最直接的作用。
4、消息分区路由机制

了解前面两个机制后,你自然会想到一个问题。就是消息如何进行路由?也即是两个相关联的问题。
Producer 会根据消息的 key 选择 Partition,具体如何通过 key 找 Partition 呢?
一个消费者组会共同消费一个 Topic 下的多个 Partition 中的同一套消息副本,那 Consumer 节点是不是可以决定自己消费哪些 Partition 的消息呢?
这两个问题其实都不难,你只要在几个 Config 类中稍微找一找就能找到答案。
首先,在 Producer 中,可以指定一个 Partitioner 来对消息进行分配。
public static final String PARTITIONER_CLASS_CONFIG = "partitioner.class";
private static final String PARTITIONER_CLASS_DOC = "A class to use to determine which partition to be send to whenproduce the records. Available options are:" +"<ul>" +"<li>If not set, the default partitioning logic is used. " +"This strategy will try sticking to a partition until at least " + BATCH_SIZE_CONFIG + " bytes is produced to thepartition. It works with the strategy:" +"<ul>" +"<li>If no partition is specified but a key is present, choose a partition based on a hash of thekey</li>" +"<li>If no partition or key is present, choose the sticky partition that changes when at least " +BATCH_SIZE_CONFIG + " bytes are produced to the partition.</li>" +"</ul>" +"</li>" +"<li><code>org.apache.kafka.clients.producer.RoundRobinPartitioner</code>: This partitioning strategy is that " +"each record in a series of consecutive records will be sent to a different partition(no matter if the 'key' isprovided or not), " +"until we run out of partitions and start over again. Note: There's a known issue that will cause uneven distributionwhen new batch is created. " +"Please check KAFKA-9965 for more detail." +"</li>" +"</ul>" +"<p>Implementing the <code>org.apache.kafka.clients.producer.Partitioner</code> interface allows you to plug in acustom partitioner.";
这里就说明了 Kafka 是通过一个 Partitioner 接口的具体实现来决定一个消息如何根据 Key 分配到对应的 Partition 上的。你甚至可以很简单的实现一个自己的分配策略。
在之前的 3.2.0 版本,Kafka 提供了三种默认的 Partitioner 实现类,RoundRobinPartitioner,DefaultPartitioner 和 UniformStickyPartitioner。目前后面两种实现已经标记为过期,被替换成了默认的实现机制。
对于生产者,默认的 Sticky 策略在给一个生产者分配了一个分区后,会尽可能一直使用这个分区。等待该分区的 batch.size(默认 16K)已满,或者这个分区的消息已完成 linger.ms(默认 0 毫秒,表示如果 batch.size 迟迟没有满后的等待时间)。RoundRobinPartitioner 是在各个 Partition 中进行轮询发送,这种方式没有考虑到消息大小以及各个 Broker 性能差异,用得比较少。
另外可以自行指定一个 Partitioner 实现类,定制分区逻辑。在 Partitioner 接口中,核心要实现的就是 partition 方法。根据相关信息,选择一个 Partition。
比如用 key 对 partition 的个数取模之类的。而 Topic 下的所有 Partition 信息都在 cluster 参数中。
//获取所有的 Partition 信息。
List<PartitionInfo> partitions = cluster.partitionsForTopic(topic);
然后,在 Consumer 中,可以指定一个 PARTITION_ASSIGNMENT_STRATEGY 分区分配策略,决定如何在多个 Consumer 实例和多个 Partitioner 之间建立关联关系。

public static final String PARTITION_ASSIGNMENT_STRATEGY_CONFIG ="partition.assignment.strategy";
private static final String PARTITION_ASSIGNMENT_STRATEGY_DOC = "A list of class names or class types, " +"ordered by preference, of supported partition assignment strategies that the client will use to distribute " +"partition ownership amongst consumer instances when group management is used. Available options are:" +"<ul>" +"<li><code>org.apache.kafka.clients.consumer.RangeAssignor</code>: Assigns partitions on a per-topic basis.</li>" +"<li><code>org.apache.kafka.clients.consumer.RoundRobinAssignor</code>: Assigns partitions to consumers in a roundrobin fashion.</li>" +"<li><code>org.apache.kafka.clients.consumer.StickyAssignor</code>: Guarantees an assignment that is " +"maximally balanced while preserving as many existing partition assignments as possible.</li>" +"<li><code>org.apache.kafka.clients.consumer.CooperativeStickyAssignor</code>: Follows the same StickyAssignor " +"logic, but allows for cooperative rebalancing.</li>" +"</ul>" +"<p>The default assignor is [RangeAssignor, CooperativeStickyAssignor], which will use the RangeAssignor by default," +"but allows upgrading to the CooperativeStickyAssignor with just a single rolling bounce that removes theRangeAssignor from the list.</p>" +"<p>Implementing the <code>org.apache.kafka.clients.consumer.ConsumerPartitionAssignor</code> " +"interface allows you to plug in a custom assignment strategy.</p>";
同样,Kafka 内置了一些实现方式,在通常情况下也都是最优的选择。你也可以实现自己的分配策略。
从上面介绍可以看到 Kafka 默认提供了三种消费者的分区分配策略 range 策略: 比如一个 Topic 有 10 个 Partiton(partition 0-9) 一个消费者组下有三个 Consumer(consumer1-3)。Range 策略就会将分区 0-3 分给一个 Consumer,4-6 给一个 Consumer,7-9 给一个 Consumer。
round-robin 策略:轮询分配策略,可以理解为在 Consumer 中一个一个轮流分配分区。比如 0,3,6,9 分区给一个 Consumer1,1,4,7 分区给一个 Consumer2,然后 2,5,8 给一个 Consumer3sticky 策略:粘性策略。这个策略有两个原则:
1、在开始分区时,尽量保持分区的分配均匀。比如按照 Range 策略分(这一步实际上是随机的)。
2、分区的分配尽可能的与上一次分配的保持一致。比如在 range 分区的情况下,第三个 Consumer 的服务宕机了,那么按照 sticky 策略,就会保持 consumer1 和 consumer2 原有的分区分配情况。然后将 consumer3 分配的 7~9 分区尽量平均的分配到另外两个 consumer 上。这种粘性策略可以很好的保持 Consumer 的数据稳定性。
另外可以通过继承 AbstractPartitionAssignor 抽象类自定义消费者的订阅方式。
官方默认提供的生产者端的默认分区器以及消费者端的 RangeAssignor+CooperativeStickyAssignor 分配策略,在大部分场景下都是非常高效的算法。
深入理解这些算法,对于你深入理解 MQ 场景,以及借此去横向对比理解其他的 MQ 产品,都是非常有帮助的。
那么在哪些场景下我们可以自己来定义分区器呢?例如如果在部署消费者时,如果我们的服务器配置不一样,就可以通过定制消费者分区器,让性能更好的服务器上的消费者消费较多的消息,而其他服务器上的消费者消费较少的消息,这样就能更合理的运用上消费者端的服务器性能,提升消费者的整体消费速度。
5、生产者消息缓存机制接下来就是如何具体发送消息了。
Kafka 生产者为了避免高并发请求对服务端造成过大压力,每次发消息时并不是一条一条发往服务端,而是增加了一个高速缓存,将消息集中到缓存后,批量进行发送。这种缓存机制也是高并发处理时非常常用的一种机制。
Kafka 的消息缓存机制涉及到 KafkaProducer 中的两个关键组件: accumulator 和 sender//1.记录累加器 int batchSize = Math.max(1, config.getInt(ProducerConfig.BATCH_SIZE_CONFIG));
this.accumulator= new RecordAccumulator(logContext,batchSize,this.compressionType,lingerMs(config),retryBackoffMs,deliveryTimeoutMs,partitionerConfig,metrics,PRODUCER_METRIC_GROUP_NAME,time,apiVersions,transactionManager,new BufferPool(this.totalMemorySize,batchSize, metrics, time, PRODUCER_METRIC_GROUP_NAME));
//2. 数据发送线程 this.sender = newSender(logContext, kafkaClient, this.metadata);
其中 RecordAccumulator,就是 Kafka 生产者的消息累加器。 KafkaProducer 要发送的消息都会在 ReocrdAccumulator 中缓存起来,然后再分批发送给 kafka broker。
在 RecordAccumulator 中,会针对每一个 Partition,维护一个 Deque 双端队列,这些 Dequeue 队列基本上是和 Kafka 服务端的 Topic 下的 Partition 对应的。每个 Dequeue 里会放入若干个 ProducerBatch 数据。 KafkaProducer 每次发送的消息,都会根据 key 分配到对应的 Deque 队列中。然后每个消息都会保存在这些队列中的某一个 ProducerBatch 中。而消息分发的规则,就是由上面的 Partitioner 组件完成的。

这里主要涉及到两个参数//RecordAccumulator 缓冲区大小 public static final String BUFFER_MEMORY_CONFIG = "buffer.memory";
private static final String BUFFER_MEMORY_DOC = "The total bytes of memory the producer can use to buffer records waiting tobe sent to the server. If records are "
+ "sent faster than they can be delivered to the server the producer willblock for <code>" + MAX_BLOCK_MS_CONFIG + "</code> after which it will throw an exception."
+ "<p>"
+ "This setting should correspond roughly to the total memory the producerwill use, but is not a hard bound since "
+ "not all memory the producer uses is used for buffering. Some additionalmemory will be used for compression (if "
+ "compression is enabled) as well as for maintaining in-flightrequests.";
//缓冲区每一个 batch 的大小 public static final String BATCH_SIZE_CONFIG = "batch.size";
private static final String BATCH_SIZE_DOC = "The producer will attempt to batch records together into fewer requests whenevermultiple records are being sent"
+ " to the same partition. This helps performance on both the client and theserver. This configuration controls the "
+ "default batch size in bytes. "
+ "<p>"
+ "No attempt will be made to batch records larger than this size. "
+ "<p>"
+ "Requests sent to brokers will contain multiple batches, one for eachpartition with data available to be sent. "
+ "<p>"
+ "A small batch size will make batching less common and may reducethroughput (a batch size of zero will disable "
+ "batching entirely). A very large batch size may use memory a bit morewastefully as we will always allocate a "
+ "buffer of the specified batch size in anticipation of additional records."
+ "<p>"
+ "Note: This setting gives the upper bound of the batch size to be sent. Ifwe have fewer than this many bytes accumulated "
+ "for this partition, we will 'linger' for the <code>linger.ms</code> timewaiting for more records to show up. "
+ "This <code>linger.ms</code> setting defaults to 0, which means we'llimmediately send out a record even the accumulated "
+ "batch size is under this <code>batch.size</code> setting.";
这里面也提到了几个其他的参数,比如 MAX_BLOCK_MS_CONFIG ,默认 60 秒

接下来,sender 就是 KafkaProducer 中用来发送消息的一个单独的线程。从这里可以看到,每个 KafkaProducer 对象都对应一个 sender 线程。他会负责将 RecordAccumulator 中的消息发送给 Kafka。
Sender 也并不是一次就把 RecordAccumulator 中缓存的所有消息都发送出去,而是每次只拿一部分消息。他只获取 RecordAccumulator 中缓存内容达到 BATCH_SIZE_CONFIG 大小的 ProducerBatch 消息。当然,如果消息比较少,ProducerBatch 中的消息大小⻓期达不到 BATCH_SIZE_CONFIG 的话,Sender 也不会一直等待。最多等待 LINGER_MS_CONFIG 时⻓。然后就会将 ProducerBatch 中的消息读取出来。 LINGER_MS_CONFIG 默认值是 0。
然后,Sender 对读取出来的消息,会以 Broker 为 key,缓存到一个对应的队列当中。这些队列当中的消息就称为 InflightRequest。接下来这些 Inflight 就会一一发往 Kafka 对应的 Broker 中,直到收到 Broker 的响应,才会从队列中移除。这些队列也并不会无限缓存,最多缓存 MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION(默认值为 5)个请求。
生产者缓存机制的主要目的是将消息打包,减少网络 IO 频率。所以,在 Sender 的 InflightRequest 队列中,消息也不是一条一条发送给 Broker 的,而是一批消息一起往 Broker 发送。而这就意味着这一批消息是没有固定的先后顺序的。
其中涉及到的几个主要参数如下:

public static final String LINGER_MS_CONFIG = "linger.ms";
private static final String LINGER_MS_DOC = "The producer groups together any records that arrive in between requesttransmissions into a single batched request. "
+ "Normally this occurs only under load when records arrive faster than theycan be sent out. However in some circumstances the client may want to "
+ "reduce the number of requests even under moderate load. This settingaccomplishes this by adding a small amount "
+ "of artificial delay&mdash;that is, rather than immediately sending out arecord, the producer will wait for up to "
+ "the given delay to allow other records to be sent so that the sends can bebatched together. This can be thought "
+ "of as analogous to Nagle's algorithm in TCP. This setting gives the upperbound on the delay for batching: once "
+ "we get <code>" + BATCH_SIZE_CONFIG + "</code> worth of records for apartition it will be sent immediately regardless of this "
+ "setting, however if we have fewer than this many bytes accumulated for thispartition we will 'linger' for the "
+ "specified time waiting for more records to show up. This setting defaultsto 0 (i.e. no delay). Setting <code>" + LINGER_MS_CONFIG + "=5</code>, "
+ "for example, would have the effect of reducing the number of requests sentbut would add up to 5ms of latency to records sent in the absence of load.";
public static final String MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION = "max.in.flight.requests.per.connection";
private static final String MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION_DOC = "The maximum number of unacknowledged requests theclient will send on a single connection before blocking."
+ " Note that if this configuration is set to begreater than 1 and <code>enable.idempotence</code> is set to false, there is a risk of"
+ " message reordering after a failed send due toretries (i.e., if retries are enabled); "
+ " if retries are disabled or if<code>enable.idempotence</code> is set to true, ordering will be preserved."
+ " Additionally, enabling idempotence requiresthe value of this configuration to be less than or equal to " + MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION_FOR_IDEMPOTENCE + "."
+ " If conflicting configurations are set andidempotence is not explicitly enabled, idempotence is disabled. ";
最后,Sender 会通过其中的一个 Selector 组件完成与 Kafka 的 IO 请求,并接收 Kafka 的响应。
//org.apache.kafka.clients.producer.KafkaProducer#doSendif (result.batchIsFull || result.newBatchCreated) {log.trace("Waking up the sender since topic {} partition {} is either full or getting a new batch",record.topic(), appendCallbacks.getPartition());
this.sender.wakeup();
}Kafka 的生产者缓存机制是 Kafka 面对海量消息时非常重要的优化机制。合理优化这些参数,对于 Kafka 集群性能提升是非常重要的。比如如果你的消息体比较大,那么应该考虑加大 batch.size,尽量提升 batch 的缓存效率。而如果 Producer 要发送的消息确实非常多,那么就需要考虑加大 total.memory 参数,尽量避免缓存不够造成的阻塞。如果发现生产者发送消息比较慢,那么可以考虑提升 max.in.flight.requests.per.connection 参数,这样能加大消息发送的吞吐量。
6、发送应答机制在 Producer 将消息发送到 Broker 后,要怎么确定消息是不是成功发到 Broker 上了呢?
这是在开发过程中比较重要的一个机制,也是面试过程中最喜欢问的一个机制,被无数教程指导吹得神乎其神。所以这里也简单介绍一下。
其实这里涉及到的,就是在 Producer 端一个不太起眼的属性 ACKS_CONFIG。

public static final String ACKS_CONFIG = "acks";
private static final String ACKS_DOC = "The number of acknowledgments the producer requires the leader to have receivedbefore considering a request complete. This controls the "
+ " durability of records that are sent. The following settings are allowed: "
+ " <ul>"
+ " <li><code>acks=0</code> If set to zero then the producer will not wait for anyacknowledgment from the"
+ " server at all. The record will be immediately added to the socket buffer andconsidered sent. No guarantee can be"
+ " made that the server has received the record in this case, and the<code>retries</code> configuration will not"
+ " take effect (as the client won't generally know of any failures). The offsetgiven back for each record will"
+ " always be set to <code>-1</code>."
+ " <li><code>acks=1</code> This will mean the leader will write the record to itslocal log but will respond"
+ " without awaiting full acknowledgement from all followers. In this case shouldthe leader fail immediately after"
+ " acknowledging the record but before the followers have replicated it then therecord will be lost."
+ " <li><code>acks=all</code> This means the leader will wait for the full set ofin-sync replicas to"
+ " acknowledge the record. This guarantees that the record will not be lost aslong as at least one in-sync replica"
+ " remains alive. This is the strongest available guarantee. This is equivalent tothe acks=-1 setting."
+ "</ul>"
+ "<p>"
+ "Note that enabling idempotence requires this config value to be 'all'."
+ " If conflicting configurations are set and idempotence is not explicitlyenabled, idempotence is disabled.";
官方给出的这段解释,同样比任何外部的资料都要准确详细了。如果你理解了 Topic 的分区模型,这个属性就非常容易理解了。这个属性更大的作用在于保证消息的安全性,尤其在 replica-factor 备份因子比较大的 Topic 中,尤为重要。
acks=0,生产者不关心 Broker 端有没有将消息写入到 Partition,只发送消息就不管了。吞吐量是最高的,但是数据安全性是最低的。
acks=all or -1,生产者需要等 Broker 端的所有 Partiton(Leader Partition 以及其对应的 Follower Partition 都写完了才能得到返回结果,这样数据是最安全的,但是每次发消息需要等待更⻓的时间,吞吐量是最低的。
acks 设置成 1,则是一种相对中和的策略。 Leader Partition 在完成自己的消息写入后,就向生产者返回结果。
在示例代码中可以验证,acks=0 的时候,消息发送者就拿不到 partition,offset 这一些数据。
在生产环境中,acks=0 可靠性太差,很少使用。 acks=1,一般用于传输日志等,允许个别数据丢失的场景。使用范围最广。 acks=-1,一般用于传输敏感数据,比如与钱相关的数据。
如果 ack 设置为 all 或者-1 ,Kafka 也并不是强制要求所有 Partition 都写入数据后才响应。在 Kafka 的 Broker 服务端会有一个配置参数 min.insync.replicas,控制 Leader Partition 在完成多少个 Partition 的消息写入后,往 Producer 返回响应。这个参数可以在 broker.conf 文件中进行配置。
min.insync.replicasWhen a producer sets acks to "all" (or "-1"), min.insync.replicas specifies the minimum number of replicas that mustacknowledge a write for the write to be considered successful. If this minimum cannot be met, then the producer will raise anexception (either NotEnoughReplicas or NotEnoughReplicasAfterAppend).When used together, min.insync.replicas and acks allow you to enforce greater durability guarantees. A typical scenario wouldbe to create a topic with a replication factor of 3, set min.insync.replicas to 2, and produce with acks of "all". This willensure that the producer raises an exception if a majority of replicas do not receive a write.Type: intDefault: 1Valid Values: [1,...]Importance: highUpdate Mode: cluster-wide 关于消息应答机制,最后强调一点:acks 设置成 all 或者-1,能够有效提高消息的安全性。但是从消息安全性方面考虑,应答机制只是保证 Broker 可以给 Producer 一个比较靠谱的响应,但并不代表就保证了消息不丢失。 Producer 拿到响应后如何进行后续处理,Kafka 是不参与的。
7、生产者消息幂等性当你仔细看下源码中对于 acks 属性的说明,会看到另外一个单词,idempotence。这个单词的意思就是幂等性。这个幂等性是什么意思呢?
之前分析过,当 Producer 的 acks 设置成 1 或-1 时,Producer 每次发送消息都是需要获取 Broker 端返回的 RecordMetadata 的。这个过程中就需要两次跨网络请求。

如果要保证消息安全,那么对于每个消息,这两次网络请求就必须要求是幂等的。但是,网络是不靠谱的,在高并发场景下,往往没办法保证这两个请求是幂等的。 Producer 发送消息的过程中,如果第一步请求成功了, 但是第二步却没有返回。这时,Producer 就会认为消息发送失败了。那么 Producer 必然会发起重试。重试次数由参数 ProducerConfig.RETRIES_CONFIG,默认值是 Integer.MAX。
这时问题就来了。 Producer 会重复发送多条消息到 Broker 中。 Kafka 如何保证无论 Producer 向 Broker 发送多少次重复的数据,Broker 端都只保留一条消息,而不会重复保存多条消息呢?这就是 Kafka 消息生产者的幂等性问题。
先来看 Kafka 中对于幂等性属性的介绍 public static final String ENABLE_IDEMPOTENCE_CONFIG = "enable.idempotence";
public static final String ENABLE_IDEMPOTENCE_DOC = "When set to 'true', the producer will ensure that exactly one copy ofeach message is written in the stream. If 'false', producer "
+ "retries due to broker failures, etc., may write duplicates of the retried message in the stream. "
+ "Note that enabling idempotence requires <code>" + MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION + "</code> to be less thanor equal to " + MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION_FOR_IDEMPOTENCE+ " (with message ordering preserved for any allowable value), <code>" + RETRIES_CONFIG + "</code> to be greater than0, and <code>"
+ ACKS_CONFIG + "</code> must be 'all'. "
+ "<p>"
+ "Idempotence is enabled by default if no conflicting configurations are set. "
+ "If conflicting configurations are set and idempotence is not explicitly enabled, idempotence is disabled. "
+ "If idempotence is explicitly enabled and conflicting configurations are set, a <code>ConfigException</code> isthrown.";
这段介绍中涉及到另外两个参数,也一并列出来// max.in.flight.requests.per.connection should be less than or equal to 5 when idempotence producer enabled to ensuremessage orderingprivate static final int MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION_FOR_IDEMPOTENCE = 5;
/** <code>max.in.flight.requests.per.connection</code> */public static final String MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION = "max.in.flight.requests.per.connection";
private static final String MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION_DOC = "The maximum number of unacknowledged requests theclient will send on a single connection before blocking."
+ " Note that if this config is set to be greaterthan 1 and <code>enable.idempotence</code> is set to false, there is a risk of"
+ " message re-ordering after a failed send due toretries (i.e., if retries are enabled)."
+ " Additionally, enabling idempotence requiresthis config value to be less than or equal to " + MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION_FOR_IDEMPOTENCE + "."
+ " If conflicting configurations are set andidempotence is not explicitly enabled, idempotence is disabled.";
可以看到,Kafka 围绕生产者幂等性问题,其实是做了一整套设计的。只是在这些描述中并没有详细解释幂等性是如何实现的。
这里首先需要理解分布式数据传递过程中的三个数据语义:at-least-once:至少一次;at-most-once:最多一次;exactly-once:精确一次。

比如,你往银行存 100 块钱,这时银行往往需要将存钱动作转化成一个消息,发到 MQ,然后通过 MQ 通知另外的系统去完成修改你的账户余额以及其他一些其他的业务动作。而这个 MQ 消息的安全性,往往是需要分层次来设计的。首先,你要保证存钱的消息能够一定发送到 MQ。如果一次发送失败了,那就重试几次,只到成功为止。这就是 at-least-once 至少一次。如果保证不了这个语义,那么你肯定不会接受。然后,你往银行存 100 块,不管这个消息你发送了多少次,银行最多只能记录一次,也就是 100 块存款,可以少,但决不能多。这就是 at-most-once 最多一次。如果保证不了这个语义,那么银行肯定也不能接收。最后,这个业务动作要让双方都满意,就必须保证存钱这个消息正正好好被记录一次,不多也不少。这就是 Exactly-once 语义。
所以,通常意义上,at-least-once 可以保证数据不丢失,但是不能保证数据不重复。而 at-most-once 保证数据不重复,但是又不能保证数据不丢失。
这两种语义虽然都有缺陷,但是实现起来相对来说比较简单。但是对一些敏感的业务数据,往往要求数据即不重复也不丢失,这就需要支持 Exactlyonce 语义。而要支持 Exactly-once 语义,需要有非常精密的设计。
回到 Producer 发消息给 Broker 这个场景,如果要保证 at-most-once 语义,可以将 ack 级别设置为 0 即可,此时,是不存在幂等性问题的。如果要保证 atleast-once 语义,就需要将 ack 级别设置为 1 或者-1,这样就能保证 Leader Partition 中的消息至少是写成功了一次的,但是不保证只写了一次。如果要支持 Exactly-once 语义怎么办呢?这就需要使用到 idempotence 幂等性属性了。
Kafka 为了保证消息发送的 Exactly-once 语义,增加了几个概念:
PID:每个新的 Producer 在初始化的过程中就会被分配一个唯一的 PID。这个 PID 对用户是不可⻅的。
Sequence Numer: 对于每个 PID,这个 Producer 针对 Partition 会维护一个 sequenceNumber。这是一个从 0 开始单调递增的数字。当 Producer 要往同一个 Partition 发送消息时,这个 Sequence Number 就会加 1。然后会随着消息一起发往 Broker。
Broker 端则会针对每个<PID,Partition>维护一个序列号(SN),只有当对应的 SequenceNumber = SN+1 时,Broker 才会接收消息,同时将 SN 更新为 SN+1。否则,SequenceNumber 过小就认为消息已经写入了,不需要再重复写入。而如果 SequenceNumber 过大,就会认为中间可能有数据丢失了。对生产者就会抛出一个 OutOfOrderSequenceException。
这样,Kafka 在打开 idempotence 幂等性控制后,在 Broker 端就会保证每条消息在一次发送过程中,Broker 端最多只会刚刚好持久化一条。这样就能保证 at-most-once 语义。再加上之前分析的将生产者的 acks 参数设置成 1 或-1,保证 at-least-once 语义,这样就整体上保证了 Exactaly-once 语义。
给 Producer 打开幂等性后,不管 Producer 往同一个 Partition 发送多少条消息,都可以通过幂等机制保证消息的 Exactly-only 语义。但是是不是这样消息就安全了呢?
8、生产者数据压缩机制当生产者往 Broker 发送消息时,还会对每个消息进行压缩,从而降低 Producer 到 Broker 的网络数据传输压力,同时也降低了 Broker 的数据存储压力。
具体涉及到 ProducerConfig 中的 COMPRESSION_TYPE_CONFIG,配置项。
/** <code>compression.type</code> */public static final String COMPRESSION_TYPE_CONFIG = "compression.type";
private static final String COMPRESSION_TYPE_DOC = "The compression type for all data generated by the producer. Thedefault is none (i.e. no compression). Valid "
+ " values are <code>none</code>, <code>gzip</code>,<code>snappy</code>, <code>lz4</code>, or <code>zstd</code>. "
+ "Compression is of full batches of data, so the efficacy of batchingwill also impact the compression ratio (more batching means better compression).";
从介绍中可以看到,Kafka 的生产者支持四种压缩算法。这几种压缩算法中,zstd 算法具有最高的数据压缩比,但是吞吐量不高。 lz4 在吞吐量方面的优势比较明显。在实际使用时,可以根据业务情况选择合适的压缩算法。但是要注意下,压缩消息必然增加 CPU 的消耗,如果 CPU 资源紧张,就不要压缩了。

关于数据压缩机制,在 Broker 端的 broker.conf 文件中,也是可以配置压缩算法的。正常情况下,Broker 从 Producer 端接收到消息后不会对其进行任何修改,但是如果 Broker 端和 Producer 端指定了不同的压缩算法,就会产生很多异常的表现。
compression.typeSpecify the final compression type for a given topic. This configuration accepts the standardcompression codecs ('gzip', 'snappy', 'lz4', 'zstd'). It additionally accepts 'uncompressed' which is equivalent to nocompression; and 'producer' which means retain the original compression codec set by the producer.Type: stringDefault: producerValid Values: [uncompressed, zstd, lz4, snappy, gzip, producer]Server Default Property: compression.typeImportance: medium 如果开启了消息压缩,那么在消费者端自然是要进行解压缩的。在 Kafka 中,消息从 Producer 到 Broker 再到 Consumer 会一直携带消息的压缩方式,这样当 Consumer 读取到消息集合时,自然就知道了这些消息使用的是哪种压缩算法,也就可以自己进行解压了。但是这时要注意的是应用中使用的 Kafka 客户端版本和 Kafka 服务端版本是否匹配。
9、生产者消息事务接下来,通过生产者消息幂等性问题,能够解决单生产者消息写入单分区的的幂等性问题。但是,如果是要写入多个分区呢?比如生产者一次发送多条消息,然后给不同的消息指定不同的 key。这批消息就有可能写入多个 Partition,而这些 Partition 是分布在不同 Broker 上的。这意味着,Producer 需要对多个 Broker 同时保证消息的幂等性。
这时候,通过上面的生产者消息幂等性机制就无法保证所有消息的幂等了。这时候就需要有一个事务机制,保证这一批消息最好同时成功的保持幂等性。或者这一批消息同时失败,这样生产者就可以开始进行整体重试,消息不至于重复。
而针对这个问题, Kafka 就引入了消息事务机制。这涉及到 Producer 中的几个 API:
// 1 初始化事务 void initTransactions();
// 2 开启事务 void beginTransaction() throws ProducerFencedException;
// 3 提交事务 void commitTransaction() throws ProducerFencedException;
// 4 放弃事务(类似于回滚事务的操作)
void abortTransaction() throws ProducerFencedException;
例如我们可以做个这样的测试:

public class TransactionErrorDemo {private static final String BOOTSTRAP_SERVERS = "worker1:9092,worker2:9092,worker3:9092";
private static final String TOPIC = "disTopic";
public static void main(String[] args) throws ExecutionException, InterruptedException {Properties props = new Properties();
// 此处配置的是 kafka 的端口 props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP_SERVERS);
// 事务 IDprops.put(ProducerConfig.TRANSACTIONAL_ID_CONFIG,"111");
// 配置 key 的序列化类 props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG,"org.apache.kafka.common.serialization.StringSerializer");
// 配置 value 的序列化类 props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG,"org.apache.kafka.common.serialization.StringSerializer");
Producer<String,String> producer = new KafkaProducer<>(props);
producer.initTransactions();
producer.beginTransaction();
for(int i = 0; i < 5; i++) {ProducerRecord<String, String> record = new ProducerRecord<>(TOPIC, Integer.toString(i), "MyProducer" + i);
//异步发送。
producer.send(record);
if(i == 3){//第三条消 息放弃事务之后,整个这一批消息都回退了。
System.out.println("error");
producer.abortTransaction();
}}System.out.println("message sended");
try {Thread.sleep(10000);
} catch (Exception e) {e.printStackTrace();
}// producer.commitTransaction();
producer.close();
}}可以先启动一个订阅了 disTopic 这个 Topic 的消费者,然后启动这个生产者,进行试验。在这个试验中,发送到第 3 条消息时,主动放弃事务,此时之前的消息也会一起回滚。
实际上,Kafka 的事务消息还会做两件事情:
1、一个 TransactionId 只会对应一个 PID 如果当前一个 Producer 的事务没有提交,而另一个新的 Producer 保持相同的 TransactionId,这时旧的生产者会立即失效,无法继续发送消息。
2、跨会话事务对⻬如果某个 Producer 实例异常宕机了,事务没有被正常提交。那么新的 TransactionId 相同的 Producer 实例会对旧的事务进行补⻬。保证旧事务要么提交,要么终止。这样新的 Producer 实例就可以以一个正常的状态开始工作。
如果你对消息事务的实现机制比较感兴趣,可以自行参看下 Apache 下的这篇文章: https://cwiki.apache.org/confluence/display/KAFKA/KIP98+-+Exactly+Once+Delivery+and+Transactional+Messaging#KIP98ExactlyOnceDeliveryandTransactionalMessagingAnExampleApplication 所以,如果一个 Producer 需要发送多条消息,通常比较安全的发送方式是这样的:

public class TransactionProducer {private static final String BOOTSTRAP_SERVERS = "worker1:9092,worker2:9092,worker3:9092";
private static final String TOPIC = "disTopic";
public static void main(String[] args) throws ExecutionException, InterruptedException {Properties props = new Properties();
// 此处配置的是 kafka 的端口 props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP_SERVERS);
// 事务 ID。
props.put(ProducerConfig.TRANSACTIONAL_ID_CONFIG,"111");
// 配置 key 的序列化类 props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG,"org.apache.kafka.common.serialization.StringSerializer");
// 配置 value 的序列化类 props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG,"org.apache.kafka.common.serialization.StringSerializer");
Producer<String,String> producer = new KafkaProducer<>(props);
producer.initTransactions();
producer.beginTransaction();
try{for(int i = 0; i < 5; i++) {ProducerRecord<String, String> record = new ProducerRecord<>(TOPIC, Integer.toString(i), "MyProducer" + i);
//异步发送。
producer.send(record);
}producer.commitTransaction();
}catch (ProducerFencedException e){producer.abortTransaction();
}finally {producer.close();
}}}其中对于事务 ID 这个参数,可以任意起名,但是建议包含一定的业务唯一性。
生产者的事务消息机制保证了 Producer 发送消息的安全性,但是,他并不保证已经提交的消息就一定能被所有消费者消费。
三、客户端流程总结对于这些属性,你并不需要煞有介事的强行去记忆,随时可以根据 ProducerConfig 和 ConsumerConfig 以及他们的父类 CommonClientConfig 去理解,大部分的属性都配有非常简明扼要的解释。但是,你一定需要尝试自己建立一个消息流转模型,理解其中比较重要的过程。然后重点从高可用,高并发的⻆度去理解 Kafka 客户端的设计,最后再尝试往其中填充具体的参数。
四、 SpringBoot 集成 Kafka 对于 Kafka,你更应该从各个⻆度建立起一个完整的数据流转的模型,通过这些模型去回顾 Kafka 的重要设计,并且尝试去验证自己的一些理解。这样才能真正去理解 Kafka 的强大之处。
当你掌握了 Kafka 的核心消息流转模型时,也可以帮助你去了解 Kafka 更多的应用生态。比如 SpringBoot 集成 Kafka,其实非常简单。就分三步 1、在 SpringBoot 项目中,引入 Maven 依赖

<dependency><groupId>org.springframework.kafka</groupId><spanrtifactId>spring-kafka</artifactId></dependency>2、在 application.properties 中配置 kafka 相关参数 例如
###########【Kafka 集群】###########
spring.kafka.bootstrap-servers=worker1:9092,worker2:9093,worker3:9093
###########【初始化生产者配置】###########
# 重试次数
spring.kafka.producer.retries=0
# 应答级别:多少个分区副本备份完成时向 生产者发送 ack 确认(可选 0、1、all/-1)
spring.kafka.producer.acks=1
# 批量大小
spring.kafka.producer.batch-size=16384
# 提交延时
spring.kafka.producer.properties.linger.ms=0
# 生产端缓冲区大小
spring.kafka.producer.buffer-memory = 33554432
# Kafka 提供的序列化和反序列化类
spring.kafka.producer.key-serializer=org.apache.kafka.common.serialization.StringSerializerspring.kafka.producer.value-serializer=org.apache.kafka.common.serialization.StringSerializer
###########【初始化消费者配置】###########
# 默认的消费组 ID
spring.kafka.consumer.properties.group.id=defaultConsumerGroup
# 是否自动提交 offset
spring.kafka.consumer.enable-auto-commit=true
# 提交 offset 延时(接收到消息后多久提交 offset)
spring.kafka.consumer.auto-commit-interval=1000
# 当 kafka 中没有初始 offset 或 offset 超出范围时将自动重置 offset
# earliest:重置为分区中最小的 offset;
# latest:重置为分区中最新的 offset(消费 分区中新产生的数据);
# none:只要有一个分区不存在已提交的 offset,就抛出异常;
spring.kafka.consumer.auto-offset-reset=latest
# 消费会话超时时间(超过这个时间 consumer 没有发送心跳,就 会触发 rebalance 操作)
spring.kafka.consumer.properties.session.timeout.ms=120000
# 消费请求超时时间
spring.kafka.consumer.properties.request.timeout.ms=180000
# Kafka 提供的序列化和反序列化类
spring.kafka.consumer.key-deserializer=org.apache.kafka.common.serialization.StringDeserializerspring.kafka.consumer.value-deserializer=org.apache.kafka.common.serialization.StringDeserializer 这些参数非常多,非常乱,如果你只是靠记忆,是记不住的。但是经过这一轮梳理,有没有觉得这些参数看着眼熟一点了?配的都是 Kafka 原生的这些参数。如果你真的把上面个模型中的参数补充完整了,SpringBoot 框架当中的这些参数就不难整理了。
3、应用中使用框架注入的 KafkaTemplate 发送消息 例如@RestControllerpublic class KafkaProducer {@Autowiredprivate KafkaTemplate<String, Object> kafkaTemplate;
// 发送消息@GetMapping("/kafka/normal/{message}")
public void sendMessage1(@PathVariable("message") String normalMessage) {kafkaTemplate.send("topic1", normalMessage);
}}4、使用@KafkaListener 注解声明消息消费者 例如:
@Componentpublic class KafkaConsumer {// 消费监听@KafkaListener(topics = {"topic1"})
public void onMessage1(ConsumerRecord<?, ?> record){// 消费的哪个 topic、partition 的消息,打印出消息内容 System.out.println("简单消费:"+record.topic()+ "-"+record.partition()+"-"+record.value());
}}

这部分的应用本来就非常简单,而且他的本质也是在框架中构建 Producer 和 Consumer。当你了解了 kafka 的核心消息流转流程,对这些应用参数就可以进行合理的组装,那么分分钟就可以上手 SpringBoot 集成 Kafka 框架的。
二、 Kafka 客户端消息流转流程.md

