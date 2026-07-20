---
title: "三、高级功能篇"
description: "一、选择合适的队列 1、Classic经典队列 2、Quorum仲裁队列 3、Stream流式队列 4、如何使用不同类型的队列 二、用Quorum队列代替懒队列 三、死信队列 1、何时会产生死信 2、死信队列的配置方式 3、关于参数x-dead-letter-routing-key 4、如何确定一个消息是不是死信 5、基于死信队列实现延迟队列 四、消息分片存储插件 1、插件的作用 2、使用步..."
author: hsc
date: 2020-05-13 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', 'Redis', 'Kafka', 'RocketMQ', 'Netty', 'ElasticSearch', 'ShardingSphere']
toc: true
---

> 本文整理自《四、分布式专题》课程笔记，共 16 页。

一、选择合适的队列
1、Classic经典队列
2、Quorum仲裁队列
3、Stream流式队列
4、如何使用不同类型的队列
二、用Quorum队列代替懒队列
三、死信队列
1、何时会产生死信
2、死信队列的配置方式
3、关于参数x-dead-letter-routing-key
4、如何确定一个消息是不是死信
5、基于死信队列实现延迟队列
四、消息分片存储插件
1、插件的作用
2、使用步骤
1、启用Sharding插件
2、配置Sharding策略
3、新增带Sharding的Exchange交换机
4、往分片交换机上发送消息
5、消费分片交换机上的消息
3、注意事项
五、章节总结
RabbitMQ核心功能拓展
-- 楼兰
这一章节主要来熟悉一下RabbitMQ的一些扩展功能,以便在项目中更深入的使用RabbitMQ。
一、选择合适的队列
之前我们一直在使用Classic经典队列。其实在创建队列时可以看到,我们实际上是可以选择三种队列类型的,Classic经典队列,
Quorum仲裁队列,Stream流式队列。RabbitMQ自3.8.x版本推出了Quorum仲裁队列,3.9.x版本推出了Stream流式队列。这些新的
队列类型都是RabbitMQ针对现代新的业务场景做出的大的改善。最明显的,以往的RabbitMQ版本,如果消息产生大量积累就会严重
影响消息收发的性能。而这两种新的队列可以极大的提升RabbitMQ的消息堆积性能。
1、Classic经典队列
这是RabbitMQ最为经典的队列类型。

在这个图中可以看到,经典队列可以选择是否持久化(Durability)以及是否自动删除(Auto delete)两个属性。
其中,Durability有两个选项,Durable和Transient。 Durable表示队列会将消息保存到硬盘,这样消息的安全性更高。但是同时,由
于需要有更多的IO操作,所以生产和消费消息的性能,相比Transient会比较低。
Auto delete属性如果选择为是,那队列将在至少一个消费者已经连接,然后所有的消费者都断开连接后删除自己。
后面的Arguments部分,还有非常多的参数,可以点击后面的问号逐步了解。
在RabbitMQ中,经典队列是一种非常传统的队列结构。消息以FIFO先进先出的方式存入队列。消息被Consumer从队列中取出后就会
从队列中删除。如果消息需要重新投递,就需要再次入队。
关于Classic如何持久化数据,RabbitMQ目前提供了两个实现版本。其中Version1就是将数据文件整体写入和读取,这种实现方式比较
简单,但是如果消息有积压,对服务端的压力就会比较大。另一种方式是只读取一部分索引,数据会在需要的时候再加载到内存当中。
这也就是之前版本当中提到的懒对列。这种方式在消息积压时,性能影响就会相对小一点。
这种队列都依靠各个Broker自己进行管理,在分布式场景下,管理效率是不太高的。并且这种经典队列不适合积累太多的消息。如果队
列中积累的消息太多了,会严重影响客户端生产消息以及消费消息的性能。因此,经典队列主要用在数据量比较小,并且生产消息和消
费消息的速度比较稳定的业务场景。比如内部系统之间的服务调用。
2、Quorum仲裁队列
仲裁队列,是RabbitMQ从3.8.0版本,引入的一个新的队列类型,也是目前官方比较推荐的一种对列类型。仲裁队列相比Classic经典
队列,在分布式环境下对消息的可靠性保障更高。官方文档中表示,未来会使用Quorum仲裁队列代替传统Classic队列。
![](file:///Users/roykingw/Desktop/a-work/RabbitMQ/%E7%AC%AC%E5%85%AD%E6%9C%9FVIP//img/Queue2.png?
lastModify=1722156434)
关于Quorum的详细介绍⻅https://www.rabbitmq.com/docs/quorum-queues,这里只是对其中的重点进行下解读

Quorum是基于Raft一致性协议实现的一种新型的分布式消息队列,他实现了持久化,多备份的FIFO队列,主要就是针对RabbitMQ的
集群设计的。简单理解就是quorum队列中的消息需要有集群中多半节点同意确认后,才会写入到队列中。这种方式可以保证消息在集
群内部不会丢失。同时,Quorum是以牺牲很多高级队列特性为代价,来进一步保证消息在分布式环境下的高可靠。
从整体功能上来说,Quorum队列是在Classic经典队列的基础上做减法,因此对于RabbitMQ的⻓期使用者而言,其实是会影响使用体
验的。他与普通队列的区别:
Quorum队列大部分功能都是在Classic队列基础上做减法,比如Non-durable queues表示是非持久化的内存队列。Exclusivity表示独
占队列,即表示队列只能由声明该队列的Connection连接来进行使用,包括队列创建、删除、收发消息等,并且独占队列会在声明该
队列的Connection断开后自动删除。
其中有个特例就是Poison Message handling(处理有毒的消息)。所谓毒消息是指消息一直不能被消费者正常消费(可能是由于消费者失
败或者消费逻辑有问题等),就会导致消息不断的重新入队,这样这些消息就成为了毒消息。这些读消息应该有保障机制进行标记并及
时删除。Quorum队列会持续跟踪消息的失败投递尝试次数,并记录在"x-delivery-count"这样一个头部参数中。然后,就可以通过设
置 Delivery limit参数来定制一个毒消息的删除策略。当消息的重复投递次数超过了Delivery limit参数阈值时,RabbitMQ就会删除这些
毒消息。当然,如果配置了死信队列的话,就会进入对应的死信队列。
在数据安全性方面,Quorum对列主要针对网络分区、通信失败等复杂网络情况下,可以提升数据的安全性。通常建议配合Publisher
Confirms机制使用。RabbitMQ能够保证经生产者确认过的消息,在集群内时安全的。但是,对于未经生产者确认的消息,RabbitMQ
并不能保证消息安全。
Quorum队列更适合于 队列⻓期存在,并且对容错、数据安全方面的要求比低延迟、不持久等高级队列更能要求更严格的场景。 例如
电商系统的订单,引入MQ后,处理速度可以慢一点,但是订单不能丢失。

也对应以下一些不适合使用的场景:
1、一些临时使用的队列:比如transient临时队列,exclusive独占队列,或者经常会修改和删除的队列。
2、对消息低延迟要求高: 一致性算法会影响消息的延迟。
3、对数据安全性要求不高:Quorum队列需要消费者手动通知或者生产者手动确认。
4、队列消息积压严重 : 如果队列中的消息很大,或者积压的消息很多,就不要使用Quorum队列。Quorum队列当前会将所有消息始
终保存在内存中,直到达到内存使用极限。这种情况下,stream流式对列是一种比较好的选择。
3、Stream流式队列
Stream队列是RabbitMQ自3.9.0版本开始引入的一种新的数据队列类型。这种队列类型的消息是持久化到磁盘并且具备分布式备份
的,更适合于消费者多,读消息非常频繁的场景。
![](file:///Users/roykingw/Desktop/a-work/RabbitMQ/%E7%AC%AC%E5%85%AD%E6%9C%9FVIP//img/Queue3.png?
lastModify=1722156434)
Stream队列的官方文档地址: https://www.rabbitmq.com/docs/streams
Stream队列的核心是以append-only只添加的日志来记录消息,整体来说,就是消息将以append-only的方式持久化到日志文件中,然
后通过调整每个消费者的消费进度offset,来实现消息的多次分发。下方有几个属性也都是来定义日志文件的大小以及保存时间。
Stream对列和Classic对列的功能对比如下:

Stream不支持死信交换机,不支持处理毒消息。

这种队列提供了RabbitMQ已有的其他队列类型不太好实现的四个特点:
1、large fan-outs 大规模分发
当想要向多个订阅者发送相同的消息时,以往的队列类型必须为每个消费者绑定一个专用的队列。如果消费者的数量很大,这就会导致
性能低下。而Stream队列允许任意数量的消费者使用同一个队列的消息,从而消除绑定多个队列的需求。
2、Replay/Time-travelling 消息回溯
RabbitMQ已有的这些队列类型,在消费者处理完消息后,消息都会从队列中删除,因此,无法重新读取已经消费过的消息。而Stream
队列允许用户在日志的任何一个连接点开始重新读取数据。
3、Throughput Performance 高吞吐性能
Strem队列的设计以性能为主要目标,对消息传递吞吐量的提升非常明显。
4、Large logs 大日志
RabbitMQ一直以来有一个让人诟病的地方,就是当队列中积累的消息过多时,性能下降会非常明显。但是Stream队列的设计目标就是
以最小的内存开销高效地存储大量的数据。使用Stream队列可以比较轻松的在队列中积累百万级别的消息。
整体上来说,RabbitMQ的Stream队列,其实有很多地方借鉴了其他MQ产品的优点,在保证消息可靠性的基础上,着力提高队列的消
息吞吐量以及消息转发性能。因此,Stream也是在视图解决一个RabbitMQ一直以来,让人诟病的缺点,就是当队列中积累的消息过多
时,性能下降会非常明显的问题。RabbitMQ以往更专注于企业级的内部使用,但是从这些队列功能可以看到,Rabbitmq也在向更复
杂的互联网环境靠拢,未来对于RabbitMQ的了解,也需要随着版本推进,不断更新。
4、如何使用不同类型的队列
这几种不同类型的队列,虽然实现方式各有不同,但是本质上都是一种存储消息的数据结构。在之前章节,已经对Classic队列的各种
编程模型进行了详细分析。而Quorum队列和Stream队列的使用方式也是大同小异的。
1、Quorum队列
Quorum队列与Classic队列的使用方式是差不多的。最主要的差别就是在声明队列时有点不同。
如果要声明一个Quorum队列,则只需要在后面的arguments中传入一个参数,x-queue-type,参数值设定为quorum。
Map<String,Object> params = new HashMap<>();
params.put("x-queue-type","quorum");
//声明Quorum队列的方式就是添加一个x-queue -type参数,指定为quorum。默认是classic
channel.queueDeclare(QUEUE_NAME, true, false, false, params);
Quorum队列的消息是必须持久化的,所以durable参数必须设定为true,如果声明为false,就会报错。同样,exclusive参数必须设置
为false。这些声明,在Producer和Consumer中是要保持一致的。
2、Stream队列
Stream队列相比于Classic队列,在使用上就要稍微复杂一点。
如果要声明一个Stream队列,则 x-queue-type参数要设置为 stream 。
Map<String,Object> params = new HashMap<>();
params.put("x-queue-type","stream");
params.put("x-max-length-bytes", 20_000_000_000L); // maximum stream size: 20 GB
params.put("x-stream-max-segment-size-bytes", 100_000_000); // size of segment files: 100 MB
channel.queueDeclare(QUEUE_NAME, true, false, false, params);
与Quorum队列类似, Stream队列的durable参数必须声明为true,exclusive参数必须声明为false。
这其中,x-max-length-bytes 表示日志文件的最大字节数。x-stream-max-segment-size-bytes 每一个日志文件的最大大小。这两个
是可选参数,通常为了防止stream日志无限制累计,都会配合stream队列一起声明。

然后,当要消费Stream队列时,要重点注意他的三个必要的步骤:
channel必须设置basicQos属性。 与Spring框架集成使用时,channel对象可以在@RabbitListener声明的消费者方法中直接引
用,Spring框架会进行注入。
正确声明Stream队列。 在Queue对象中传入声明Stream队列所需要的参数。
消费时需要指定offset。 与Spring框架集成时,可以通过注入Channel对象,使用原生API传入offset属性。
例如用原生API创建Stream类型的Consumer时,还必须添加一个参数x-stream-offset,表示从队列的哪个位置开始消费。
Map<String,Object> consumeParam = new HashMap<>();
consumeParam.put("x-stream-offset","last");
channel.basicConsume(QUEUE_NAME, false,consumeParam, myconsumer);
x-stream-offset的可选值有以下几种:
first: 从日志队列中第一个可消费的消息开始消费
last: 消费消息日志中最后一个消息
next: 相当于不指定offset,消费不到消息。
Offset: 一个数字型的偏移量
Timestamp:一个代表时间的Data类型变量,表示从这个时间点开始消费。例如 一个小时前 Date timestamp = new
Date(System.currentTimeMillis() - 60 * 60 * 1_000)
由于在Consumer中必须传入x-stream-offset这个参数,所以在与SpringBoot集成时,stream队列目前暂时无法正常消费。在目前版
本下,使用RabbitMQ的SpringBoot框架集成,可以正常声明Stream队列,往Stream队列发送消息,但是无法直接消费Stream队列
了。
关于这个问题,还是需要从Stream队列的三个重点操作入手。SpringBoot框架集成RabbitMQ后,为了简化编程模型,就把channel,
connection等这些关键对象给隐藏了,目前框架下,无法直接接入这些对象的注入过程,所以无法直接使用。
如果非要使用Stream队列,那么有两种方式,一种是使用原生API的方式,在SpringBoot框架下自行封装。另一种是使用RabbitMQ的
Stream 插件。在服务端通过Strem插件打开TCP连接接口,并配合单独提供的Stream客户端使用。这种方式对应用端的影响太重了,
并且并没有提供与SpringBoot框架的集成,还需要自行完善,因此选择使用的企业还比较少。
这里就不详细介绍使用方式了。关于Stream插件的使用和配置方式参⻅官方文档:https://www.rabbitmq.com/docs/stream。至于
stream的客户端,课程编写时,官网给出的进度是这样的
最后,在企业中,目前用的最多的还是Classic经典队列。而从RabbitMQ的官网就能看出,RabbitMQ目前主推的是Quorum队列,甚
至有传言未来会用Quorum队列全面替代Classic经典队列。至于Stream队列,虽然已经经历了几个版本的完善修复,但是目前还是不
太稳定,企业用得还比较少。

二、用Quorum队列代替懒队列
从3.6.x版本到3.12.x版本,RabbitMQ提供了一种针对Classic Queue的优化配置,lazy-mode,懒对列。懒队列会尽可能早的将消息内
容保存到硬盘当中,并且只有在用户请求到时,才临时从硬盘加载到RAM内存当中。
默认情况下,RabbitMQ接收到消息时,会保存到内存以便使用,同时把消息写到硬盘。但是,消息写入硬盘的过程中,是会阻塞队列
的。RabbitMQ虽然针对写入硬盘速度做了很多算法优化,但是在⻓队列中,依然表现不是很理想,所以就有了懒队列的出现。
懒队列会尝试尽可能早的把消息写到硬盘中。这意味着在正常操作的大多数情况下,RAM中要保存的消息要少得多。当然,这是以增
加磁盘IO为代价的。
懒队列适合消息量大且⻓期有堆积的队列,可以减少内存使用,加快消费速度。但是这是以大量消耗集群的网络及磁盘IO为代价的。
但是在3.13版本,官方已经建议使用Quorum对列代替懒对列。这一次,官网明确建议从3.11版本往后的版本都使用Quorum对列代替
懒对列。
三、死信队列
死信队列是RabbitMQ中非常重要的一个特性。简单理解,他是RabbitMQ对于未能正常消费的消息进行的一种补救机制。死信队列也
是一个普通的队列,同样可以在队列上声明消费者,继续对消息进行消费处理。
对于死信队列,在RabbitMQ中主要涉及到几个参数。
x-dead-letter-exchange: mirror.dlExchange 对应的死信交换机
x-dead-letter-routing-key: mirror.messageExchange1.messageQueue1 死信交换机routing-key
x-message-ttl: 3000 消息过期时间
durable: true 持久化,这个是必须的。
在这里,x-dead-letter-exchange指定一个交换机作为死信交换机,然后x-dead-letter-routing-key指定交换机的RoutingKey。而接
下来,死信交换机就可以像普通交换机一样,通过RoutingKey将消息转发到对应的死信队列中。
1、何时会产生死信
有以下三种情况,RabbitMQ会将一个正常消息转成死信
消息被消费者确认拒绝。消费者把requeue参数设置为true(false),并且在消费后,向RabbitMQ返回拒绝。channel.basicReject
或者channel.basicNack。
消息达到预设的TTL时限还一直没有被消费。
消息由于队列已经达到最⻓⻓度限制而被丢掉
TTL即最⻓存活时间 Time-To-Live 。消息在队列中保存时间超过这个TTL,即会被认为死亡。死亡的消息会被丢入死信队列,如
果没有配置死信队列的话,RabbitMQ会保证死了的消息不会再次被投递,并且在未来版本中,会主动删除掉这些死掉的消息。
设置TTL有两种方式,一是通过配置策略指定,另一种是给队列单独声明TTL
策略配置方式 - Web管理平台配置 或者 使用指令配置 60000为毫秒单位
rabbitmqctl set_policy TTL ".*" '{"message-ttl":60000}' --apply-to queues
在声明队列时指定 - 同样可以在Web管理平台配置,也可以在代码中配置:
Map<String, Object> args = new HashMap<String, Object>();
args.put("x-message-ttl", 60000);
channel.queueDeclare("myqueue", false, false, false, args);

2、死信队列的配置方式
RabbitMQ中有两种方式可以声明死信队列,一种是针对某个单独队列指定对应的死信队列。另一种就是以策略的方式进行批量死信队
列的配置。
针对多个队列,可以使用策略方式,配置统一的死信队列。、
rabbitmqctl set_policy DLX ".*" '{"dead-letter-exchange":"my-dlx"}' --apply-to queues
针对队列单独指定死信队列的方式主要是之前提到的三个属性。
channel.exchangeDeclare("some.exchange.name", "direct");
Map<String, Object> args = new HashMap<String, Object>();
args.put("x-dead-letter-exchange", "some.exchange.name");
channel.queueDeclare("myqueue", false, false, false, args);
这些参数,也可以在RabbitMQ的管理⻚面进行配置。例如配置策略时:
![](file:///Users/roykingw/Desktop/a-
work/RabbitMQ/%E7%AC%AC%E5%85%AD%E6%9C%9FVIP/img/%E6%AD%BB%E4%BF%A1%E7%AD%96%E7%95%A5.png?
lastModify=1722156205)
另外,你会注意到,在对队列进行配置时,只有Classic经典队列和Quorum仲裁队列才能配置死信队列,而目前Stream流式队列,并
不支持配置死信队列。
3、关于参数x-dead-letter-routing-key
死信在转移到死信队列时,他的Routing key 也会保存下来。但是如果配置了x-dead-letter-routing-key这个参数的话,routingkey就
会被替换为配置的这个值。

另外,死信在转移到死信队列的过程中,是没有经过消息发送者确认的,所以并不能保证消息的安全性。
4、如何确定一个消息是不是死信
消息被作为死信转移到死信队列后,会在Header当中增加一些消息。在官网的详细介绍中,可以看到很多内容,比如时间、原因
(rejected,expired,maxlen)、队列等。然后header中还会加上第一次成为死信的三个属性,并且这三个属性在以后的传递过程中都不会
更改。
x-first-death-reason
x-first-death-queue
x-first-death-exchange
5、基于死信队列实现延迟队列
其实从前面的配置过程能够看到,所谓死信交换机或者死信队列,不过是在交换机或者队列之间建立一种死信对应关系,而死信队列可
以像正常队列一样被消费。他与普通队列一样具有FIFO的特性。对死信队列的消费逻辑通常是对这些失效消息进行一些业务上的补
偿。
RabbitMQ中,是不存在延迟队列的功能的,而通常如果要用到延迟队列,就会采用TTL+死信队列的方式来处理。
RabbitMQ提供了一个rabbitmq_delayed_message_exchange插件,可以实现延迟队列的功能,但是并没有集成到官方的发布包
当中,需要单独去下载。这里就不去讨论了。
四、消息分片存储插件
1、插件的作用
之前介绍过,RabbitMQ的客户端TPS跟Kafka和RocketMQ还是有挺大差距的,那么如何在消费者的处理能力有限的前提下提升消费者
的消费速度呢?RabbitMQ提供的Sharding插件,就提供了一种思路。
谈到Sharding,你是不是就想到了分库分表?对于数据库的分库分表,分库可以减少数据库的IO性能压力,而真正要解决单表数据太
大的问题,就需要分表。
对于RabbitMQ同样,针对单个对列,如何增加吞吐量呢?增加消费者的个数以及消息处理速度,当然是最有效的办法。但是,这无疑
需要更大的资源投入。如何在消费者的处理能力有限的前提下提升消费进度呢?RabbitMQ的Sharding插件就提供了一种方案,将一个
队列中的消息分散存储到不同的节点上,并提供多个节点的负载均衡策略实现对等的读与写功能。
2、使用步骤
1、启用Sharding插件
在当前RabbitMQ的运行版本中,已经包含了Sharding插件,需要使用插件时,只需要安装启用即可。
rabbitmq-plugins enable rabbitmq_sharding
2、配置Sharding策略
启用完成后,需要配置Sharding的策略。

![](file:///Users/roykingw/Desktop/a-work/RabbitMQ/%E7%AC%AC%E5%85%AD%E6%9C%9FVIP/img/sharding1.png?
lastModify=1722156205)
按照要求,就可以配置一个针对sharding_开头的交换机和队列的策略。
![](file:///Users/roykingw/Desktop/a-work/RabbitMQ/%E7%AC%AC%E5%85%AD%E6%9C%9FVIP/img/sharding2.png?
lastModify=1722156596)
3、新增带Sharding的Exchange交换机
在创建Exchange时,可以看到,安装了Sharding插件后,多出了一种队列类型,x-modulus-hash

![](file:///Users/roykingw/Desktop/a-work/RabbitMQ/%E7%AC%AC%E5%85%AD%E6%9C%9FVIP/img/sharding3.png?
lastModify=1722156596)
4、往分片交换机上发送消息
接下来,就可以用下面的生产者代码,在RabbitMQ上声明一个x-modulus-hash类型的交换机,并往里面发送一万条消息。
public class ShardingProducer {
private static final String EXCHANGE_NAME = "sharding_exchange";
public static void main(String[] args) throws Exception{
ConnectionFactory factory = new ConnectionFactory();
factory.setHost("192.168.65.112");
factory.setPort(5672);
factory.setUsername("admin");
factory.setPassword("admin");
factory.setVirtualHost("/mirror");
Connection connection = factory.newConnection();
Channel channel = connection.createChannel();
//发送者只管往exchange里发消息,而不用关心具体发到哪些queue里。
channel.exchangeDeclare(EXCHANGE_NAME, "x-modulus-hash");
for(int i = 0 ; i < 3000 ; i ++){
String message = "Sharding message "+i;
channel.basicPublish(EXCHANGE_NAME, String.valueOf(i), null, message.getBytes());
}
channel.close();
connection.close();
}
}
启动后,就会在RabbitMQ上声明一个sharding_exchange。查看这个交换机的详情,可以看到他的绑定情况:

![](file:///Users/roykingw/Desktop/a-work/RabbitMQ/%E7%AC%AC%E5%85%AD%E6%9C%9FVIP/img/sharding4.png?
lastModify=1722156596)
并且,三千条消息被平均分配到了三个队列当中。
![](file:///Users/roykingw/Desktop/a-work/RabbitMQ/%E7%AC%AC%E5%85%AD%E6%9C%9FVIP/img/sharding5.png?
lastModify=1722156596)
Sharding插件带来的x-modulus-hash类型Exchange,会忽略之前的routingkey配置,而将消息以轮询的方式平均分配到Exchange绑
定的所有队列上。
5、消费分片交换机上的消息
现在sharding_exchange交换机上的消息已经平均分配到了三个碎片队列上。这时如何去消费这些消息呢?你会发现这些碎片队列的名
字并不是毫无规律的,他是有一个固定的格式的。都是固定的这种格式:sharding: {exchangename}-{node}-{shardingindex} 。你
当然可以针对每个队列去单独声明消费者,这样当然是能够消费到消息的,但是这样,你消费到的消息就是一些零散的消息了,这不符
合分片的业务场景要求。

数据分片后,还是希望能够像一个普通队列一样消费到完整的数据副本。这时,Sharding插件提供了一种伪队列的消费方式。你可以
声明一个名字为 exchangename 的伪队列,然后像消费一个普通队列一样去消费这一系列的碎片队列。
为什么说是伪队列?exchange、queue傻傻分不清楚?因为名为exchangename的队列实际是不存在的。
public class ShardingConsumer {
public static final String QUEUENAME="sharding_exchange";
public static void main(String[] args) throws IOException, TimeoutException {
ConnectionFactory factory = new ConnectionFactory();
factory.setHost("192.168.65.112");
factory.setPort(5672);
factory.setUsername("admin");
factory.setPassword("admin");
factory.setVirtualHost("/mirror");
Connection connection = factory.newConnection();
Channel channel = connection.createChannel();
channel.queueDeclare(QUEUENAME,false,false,false,null);
Consumer myconsumer = new DefaultConsumer(channel) {
@Override
public void handleDelivery(String consumerTag, Envelope envelope,
AMQP.BasicProperties properties, byte[] body)
throws IOException {
System.out.println("========================");
String routingKey = envelope.getRoutingKey();
System.out.println("routingKey >" + routingKey);
String contentType = properties.getContentType();
System.out.println("contentType >" + contentType);
long deliveryTag = envelope.getDeliveryTag();
System.out.println("deliveryTag >" + deliveryTag);
System.out.println("content:" + new String(body, "UTF-8"));
// (process the message components here ...)
//消息处理完后,进行答复。答复过的消息,服务器就不会再次转发。
//没有答复过的消息,服务器会一直不停转发。
// channel.basicAck(deliveryTag, false);
}
};
// 三个分片就需要消费三次。
//sharding插件的实现原理就 是将basicConsume方法绑定到分片队列中连接最少的一个队列上。
String consumeerFlag1 = channel.basicConsume(QUEUENAME, true, myconsumer);
System.out.println("c1:"+consumeerFlag1);
String consumeerFlag2 = channel.basicConsume(QUEUENAME, true, myconsumer);
System.out.println("c2:"+consumeerFlag2);
String consumeerFlag3 = channel.basicConsume(QUEUENAME, true, myconsumer);
System.out.println("c3:"+consumeerFlag3);
}
}
3、注意事项
使用Sharding插件后,Producer发送消息时,只需要指定虚拟Exchange,并不能确定消息最终会发往哪一个分片队列。而Sharding插
件在进行消息分散存储时,虽然尽量是按照轮询的方式,均匀的保存消息。但是,这并不能保证消息就一定是均匀的。
首先,这些消息在分片的过程中,是没有考虑消息顺序的,这会让RabbitMQ中原本就不是很严谨的消息顺序变得更加雪上加霜。所
以,Sharding插件适合于那些对于消息延迟要求不严格,以及对消费顺序没有任何要求的的场景。
然后,Sharding插件消费伪队列的消息时,会从消费者最少的碎片中选择队列。这时,如果你的这些碎片队列中已经有了很多其他的
消息,那么再去消费伪队列消息时,就会受到这些不均匀数据的影响。所以,如果使用Sharding插件,这些碎片队列就尽量不要单独
使用了。
五、章节总结

从目前的版本来看, RabbitMQ正在快速迭代过程中。尤其是现在的3.13.x版本,就连官网都做了一次很大的更新,由此可⻅
RabbitMQ的更新力度。而这背后,万变不离其宗的,是RabbitMQ解决各种问题的思路。这些解决问题的思路才是技术人员最需要掌
握的核心。
【有道云笔记】三、高级功能篇.mdhttps://note.youdao.com/s/CbSGNmEc
