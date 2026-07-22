---


title: "RocketMQ客户端编程模型"
description: "RocketMQ 客户端基本流程 2、消息确认机制 3、广播消息 4、过滤消息 5、顺序消息机制 6、延迟消息 7、批量消息 8、事务消息 9、ACL 权限控制"
    一、回顾RocketMQ的运行架构 二、深入理解RocketMQ的消息模型 1、RocketMQ客户端基本流程 2、消息确认机制 3、广播消息 4、过滤消息 5、顺序消息机制 6、延迟消息 7、批量消息 8、事务消息 9、ACL权限控制机制 三、SpringBoot整合RocketMQ 1、快速实战 2、如何处理各种消息类型 3、实现原理 四、RocketMQ客户端注意事项 1、消息的ID,...
author: hsc
date: 2024-02-26 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Redis', 'Kafka', 'RocketMQ', 'Netty']
toc: true


---

### 一、回顾 RocketMQ 的运行架构二、深入理解 RocketMQ 的消息模型
1、RocketMQ 客户端基本流程 2、消息确认机制 3、广播消息 4、过滤消息 5、顺序消息机制 6、延迟消息 7、批量消息 8、事务消息 9、ACL 权限控制机制三、 SpringBoot 整合 RocketMQ1、快速实战 2、如何处理各种消息类型 3、实现原理四、 RocketMQ 客户端注意事项 1、消息的 ID,Key 和 Tag2、最佳实践 3、消费者端进行幂等控制
4. Are messages delivered exactly once?
4、关注错误消息重试 5、手动处理死信队列 RocketMQ 核心编程模型图灵 楼兰笔记配合视频课程一起学习上一部分,我们可以搭建 RocketMQ 集群,然后也可以用命令行往 RocketMQ 写入消息并进行消费了。这一部分我们就来看怎么在项目中用上 RocketMQ。
一、回顾 RocketMQ 的运行架构上一章节我们从试验整理出了 RocketMQ 的运行架构图同时还总结出了 RocketMQ 的消息模型。

这是我们使用 RocketMQ 时最直接的指导。这一章节,我们就来看下,在这两张图的基础上,如何编写合适的客户端代码,让我们在项目中用好 RocketMQ。
二、深入理解 RocketMQ 的消息模型 1、RocketMQ 客户端基本流程 RocketMQ 基于 Maven 提供了客户端的核心依赖:
<dependency><groupId>org.apache.rocketmq</groupId><spanrtifactId>rocketmq-client</artifactId><version>5.3.0</version></dependency>一个最为简单的消息生产者代码如下:
public class Producer {public static void main(String[] args) throws MQClientException, InterruptedException {//初始化一个消息生产者 DefaultMQProducer producer = new DefaultMQProducer("please_rename_unique_group_name");
// 指定 nameserver 地址 producer.setNamesrvAddr("192.168.65.112:9876");
// 启动消息生产者服务 producer.start();
for (int i = 0; i < 2; i++) {try {/ / 创建消息。消息由 Topic,Tag 和 body 三个属性组成,其中 Body 就是消息内容 Message msg = new Message("TopicTest","TagA",("Hello RocketMQ" +i).getBytes(RemotingHelper.DEFAULT_CHARSET));
//发送消息,获取发送结果 SendResult sendResult = producer.send(msg);
System.out.printf("%s%n", sendResult);
} catch (Exception e) {e.printStackTrace();
Thread.sleep(1000);
}}/ /消息发送完后,停止消息生产者服务。
producer.shutdown();
}}

一个简单的消息消费者代码如下:
public class Consumer {public static void main(String[] args) throws InterruptedException, MQClientException {//构建一个消息消费者 DefaultMQPushConsumer consumer = new DefaultMQPushConsumer("please_rename_unique_group_name_4");
//指定 nameserver 地址 consumer.setNamesrvAddr("192.168.65.112:9876");
consumer.setConsumeFromWhere(ConsumeFromWhere.CONSUME_FROM_LAST_OFFSET);
// 订阅一个感兴趣的话题,这个话题需要与消息的 topic 一致 consumer.subscribe("TopicTest", "*");
// 注册一个消息回调函数,消费到消息后就会触发 回调。
consumer.registerMessageListener(new MessageListenerConcurrently() {@Overridepublic ConsumeConcurrentlyStatus consumeMessage(List<MessageExt> msgs,ConsumeConcurrentlyContext context) {msgs.forEach(messageExt -> {try {System.out.println("收到消息:"+new String(messageExt.getBody(),RemotingHelper.DEFAULT_CHARSET));
} catch (UnsupportedEncodingException e) {}});
return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
}});
//启 动消费者服务 consumer.start();
System.out.print("Consumer Started");
}}RocketMQ 的客户端编程模型相对比较固定,基本都有一个固定的步骤。掌握这个固定步骤,对于学习其他复杂的消息模型也是很有帮助的。
消息生产者的固定步骤 1.创建消息生产者 producer,并指定生产者组名 2.指定 Nameserver 地址 3.启动 producer。 这个步骤比较容易忘记。可以认为这是消息生产者与服务端建立连接的过程。
4.创建消息对象,指定主题 Topic、Tag 和消息体 5.发送消息 6.关闭生产者 producer,释放资源。
消息消费者的固定步骤 1.创建消费者 Consumer,必须指定消费者组名 2.指定 Nameserver 地址 3.订阅主题 Topic 和 Tag4.设置回调函数,处理消息 5.启动消费者 consumer。消费者会一直挂起,持续处理消息。
其中,最为关键的就是 NameServer。从示例中可以看到,RocketMQ 的客户端只需要指定 NameServer 地址,而不需要指定具体的 Broker 地址。
指定 NameServer 的方式有两种。可以在客户端直接指定,例如 consumer.setNameSrvAddr("127.0.0.1 9876")。然后,也可以通过读取系统环境变量 NAMESRV_ADDR 指定。其中第一种方式的优先级更高。
2、消息确认机制 RocketMQ 要支持互联网金融场景,那么消息安全是必须优先保障的。而消息安全有两方面的要求,一方面是生产者要能确保将消息发送到 Broker 上。另一方面是消费者要能确保从 Broker 上争取获取到消息。
1、消息生产端采用消息确认加多次重试的机制保证消息正常发送到 RocketMQ 针对消息发送的不确定性,封装了三种发送消息的方式。
第一种称为单向发送单向发送方式下,消息生产者只管往 Broker 发送消息,而全然不关心 Broker 端有没有成功接收到消息。这就好比生产者向 Broker 发一封电子邮件,Broker 有没有处理电子邮件,生产者并不知道。

public class OnewayProducer {public static void main(String[] args)throws Exception{DefaultMQProducer producer = new DefaultMQProducer("producerGroup");
producer.start();
Message message = new Message("Order","tag","order info : orderId = xxx".getBytes(StandardCharsets.UTF_8));
producer.sendOneway(message);
Thread.sleep(50000);
producer.shutdown();
}}sendOneway 方法没有返回值,如果发送失败,生产者无法补救。
单向发送有一个好处,就是发送消息的效率更高。适用于一些追求消息发送效率,而允许消息丢失的业务场景。比如日志。
第二种称为同步发送同步发送方式下,消息生产者在往 Broker 端发送消息后,会阻塞当前线程,等待 Broker 端的相应结果。这就好比生产者给 Broker 打了个电话。
通话期间生产者就停下手头的事情,直到 Broker 明确表示消息处理成功了,生产者才继续做其他的事情。
SendResult sendResult = producer.send(msg);
SendResult 来自于 Broker 的反馈。 producer 在 send 发出消息,到 Broker 返回 SendResult 的过程中,无法做其他的事情。
在 SendResult 中有一个 SendStatus 属性,这个 SendStatus 是一个枚举类型,其中包含了 Broker 端的各种情况。
public enum SendStatus {SEND_OK,FLUSH_DISK_TIMEOUT,FLUSH_SLAVE_TIMEOUT,SLAVE_NOT_AVAILABLE,}在这几种枚举值中,SEND_OK 表示消息已经成功发送到 Broker 上。至于其他几种枚举值,都是表示消息在 Broker 端处理失败了。使用同步发送的机制,我们就可以在消息生产者发送完消息后,对发送失败的消息进行补救。例如重新发送。
但是此时要注意,如果 Broker 端返回的 SendStatus 不是 SEND_OK,也并不表示消息就一定不会推送给下游的消费者。仅仅只是表示 Broker 端并没有完全正确的处理这些消息。因此,如果要重新发送消息,最好要带上唯一的系统标识,这样在消费者端,才能自行做幂等判断。也就是用具有业务含义的 OrderID 这样的字段来判断消息有没有被重复处理。
这种同步发送的机制能够很大程度上保证消息发送的安全性。但是,这种同步发送机制的发送效率比较低。毕竟,send 方法需要消息在生产者和 Broker 之间传输一个来回后才能结束。如果网速比较慢,同步发送的耗时就会很⻓。
第三种称为异步发送异步发送机制下,生产者在向 Broker 发送消息时,会同时注册一个回调函数。接下来生产者并不等待 Broker 的响应。当 Broker 端有响应数据过来时,自动触发回调函数进行对应的处理。这就好比生产者向 Broker 发电子邮件通知时,另外找了一个代理人专⻔等待 Broker 的响应。而生产者自己则发完消息后就去做其他的事情去了。
producer.send(msg, new SendCallback() {@Overridepublic void onSuccess(SendResult sendResult) {countDownLatch.countDown();
System.out.printf("%-10d OK %s %n", index, sendResult.getMsgId());
}@Overridepublic void onException(Throwable e) {countDownLatch.countDown();
System.out.printf("%-10d Exception %s %n", index, e);
e.printStackTrace();
}});
在 SendCallback 接口中有两个方法,onSuccess 和 onException。当 Broker 端返回消息处理成功的响应信息 SendResult 时,就会调用 onSuccess 方法。当 Broker 端处理消息超时或者失败时,就会调用 onExcetion 方法,生产者就可以在 onException 方法中进行补救措施。

此时同样有几个问题需要注意。一是与同步发送机制类似,触发了 SendCallback 的 onException 方法同样并不一定就表示消息不会向消费者推送。如果 Broker 端返回响应信息太慢,超过了超时时间,也会触发 onException 方法。超时时间默认是 3 秒,可以通过 producer.setSendMsgTimeout 方法定制。而造成超时的原因则有很多,消息太大造成网络拥堵、网速太慢、 Broker 端处理太慢等都可能造成消息处理超时。
二是在 SendCallback 的对应方法被触发之前,生产者不能调用 shutdown()方法。如果消息处理完之前,生产者线程就关闭了,生产者的 SendCallback 对应方法就不会触发。这是因为使用异步发送机制后,生产者虽然不用阻塞下来等待 Broker 端响应,但是 SendCallback 还是需要附属于生产者的主线程才能执行。如果 Broker 端还没有返回 SendResult,而生产者主线程已经停止了,那么 SendCallback 的执行线程也就会随主线程一起停止,对应的方法自然也就无法执行了。
这种异步发送的机制能够比较好的兼容消息的安全性以及生产者的高吞吐需求,是很多 MQ 产品都支持的方式。 RabbitMQ 和 Kafka 都支持这种异步发送的机制。但是异步发送机制也并不是万能的,毕竟异步发送机制对消息生产者的主线业务是有侵入的。具体使用时还是需要根据业务场景考虑。
RocketMQ 提供的这三种发送消息的方式,并不存在绝对的好坏之分。我们更多的是需要根据业务场景进行选择。例如在电商下单这个场景,我们就应该尽量选择同步发送或异步发送,优先保证数据安全。然后,如果下单场景的并发比较高,业务比较繁忙,就应该尽量优先选择异步发送的机制。这时,我们就应该对下单服务的业务进行优化定制,尽量适应异步发送机制的要求。这样就可以尽量保证下单服务能够比较可靠的将用户的订单消息发送到 RocketMQ 了。
2、消息消费者端采用状态确认机制保证消费者一定能正常处理对应的消息我们之前分析生产者的可靠性问题,核心的解决思路就是通过确认 Broker 端的状态来保证生产者发送消息的可靠性。对于 RocketMQ 的消费者来说,保证消息处理可靠性的思路也是类似的。只不过这次换成了 Broker 等待消费者返回消息处理状态。
consumer.registerMessageListener(new MessageListenerConcurrently() {@Overridepublic ConsumeConcurrentlyStatus consumeMessage(List<MessageExt> msgs, ConsumeConcurrentlyContextcontext) {System.out.printf("%s Receive New Messages: %s %n", Thread.currentThread().getName(), msgs);
return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
}});
这个返回值是一个枚举值,有两个选项 CONSUME_SUCCESS 和 RECONSUME_LATER。如果消费者返回 CONSUME_SUCCESS,那么消息自然就处理结束了。但是如果消费者没有处理成功,返回的是 RECONSUME_LATER,Broker 就会过一段时间再发起消息重试。
为了要兼容重试机制的成功率和性能,RocketMQ 设计了一套非常完善的消息重试机制,从而尽可能保证消费者能够正常处理用户的订单信息。
1、Broker 不可能无限制的向消费失败的消费者推送消息。如果消费者一直没有恢复,Broker 显然不可能一直无限制的推送,这会浪费集群很多的性能。所以,Broker 会记录每一个消息的重试次数。如果一个消息经过很多次重试后,消费者依然无法正常处理,那么 Broker 会将这个消息推入到消费者组对应的死信 Topic 中。死信 Topic 相当于 windows 当中的垃圾桶。你可以人工介入对死信 Topic 中的消息进行补救,也可以直接彻底删除这些消息。 RocketMQ 默认的最大重试次数是 16 次。
2、为了让这些重试的消息不会影响 Topic 下其他正常的消息,Broker 会给每个消费者组设计对应的重试 Topic。MessageQueue 是一个具有严格 FIFO 特性的数据结构。如果需要重试的这些消息还是放在原来的 MessageQueue 中,就会对当前 MessageQueue 产生阻塞,让其他正常的消息无法处理。 RocketMQ 的做法是给每个消费者组自动生成一个对应的重试 Topic。在消息需要重试时,会先移动到对应的重试 Topic 中。后续 Broker 只要从这些重试 Topic 中不断拿出消息,往消费者组重新推送即可。这样,这些重试的消息有了自己单独的队列,就不会影响到 Topic 下的其他消息了。
3、RocketMQ 中设定的消费者组都是订阅主题和消费逻辑相同的服务备份,所以当消息重试时,Broker 只要往消费者组中随意一个实例推送即可。这是消息重试机制能够正常运行的基础。但是,在客户端的具体实现时,MQDefaultMQConsumer 并没有强制规定消费者组不能重复。也就是说,你完全可以实现出一些订阅主题和消费逻辑完全不同的消费者服务,共同组成一个消费组。在这种情况下,RocketMQ 不会报错,但是消息的处理逻辑就无法保持一致了。这会给业务带来很大的麻烦。这是在实际应用时需要注意的地方。
4、Broker 端最终只通过消费者组返回的状态来确定消息有没有处理成功。至于消费者组自己的业务执行是否正常,Broker 端是没有办法知道的。因此,在实现消费者的业务逻辑时,应该要尽量使用同步实现方式,保证在自己业务处理完成之后再向 Broker 端返回状态。而应该尽量避免异步的方式处理业务逻辑。
3、消费者组也可以自行指定起始消费位点 Broker 端通过 Consumer 返回的状态来推进所属消费者组对应的 Offset。但是,这里还是会造成一种分裂,消息最终是由 Consumer 来处理,但是消息却是由 Broker 推送过来的,也就是说,Consumer 无法确定自己将要处理的是哪些消息。这就好比你上班做一天事情,公司负责给你发一笔工资。如果一切正常,那么没什么问题。 但是如果出问题了呢?公司拖欠了你的工资,这时,你就还是需要能到公司查账,至少查你自己的工资记录。从上一次发工资的时候计算你该拿的钱。

使用消息对列要如何解决这样的问题呢?这时,就可以创建另外一个新的消费者组,并通过 ConsumerFromWhere 属性指定这个消费者组的消费起点,从而让这个新的消费者组去消费之前发送过的历史消息。而这个 ConsumerFromWhere 属性并不是直接指定 Offset 的数值,因为客户端也不知道 Broker 端记录的 Offset 数值是多少。 RocketMQ 就提供了一个枚举值。名字一目了然。
public enum ConsumeFromWhere {CONSUME_FROM_LAST_OFFSET, //从对列的最后一条消息开始消费 CONSUME_FROM_FIRST_OFFSET, //从对列的第一条消息开始消费 CONSUME_FROM_TIMESTAMP; //从某一个时间点开始重新消费}另外,如果指定了 ConsumerFromWhere.CONSUME_FROM_TIMESTAMP,这就表示要从一个具体的时间开始。具体时间点,需要通过 Consumer 的另一个属性 ConsumerTimestamp。这个属性可以传入一个表示时间的字符串。
consumer.setConsumerTimestamp("20131223171201");
到这里,我们就从客户端的⻆度分析清楚了要如何保证消息的安全性。但是消息安全问题其实是一个非常体系化的问题,涉及到的不光是客户端,还需要服务端配合。关于这个问题,我们会在后面的分享过程当中继续带你一起思考。
3、广播消息应用场景:
广播模式和集群模式是 RocketMQ 的消费者端处理消息最基本的两种模式。集群模式下,一个消息,只会被一个消费者组中的多个消费者实例共同 处理一次。广播模式下,一个消息,则会推送给所有消费者实例处理,不再关心消费者组。
示例代码:
消费者核心代码 consumer.setMessageModel(MessageModel.BROADCASTING);
启动多个消费者,广播模式下,这些消费者都会消费一次消息。
实现思路:
默认模式(也就是集群模式)下,Broker 端会给每个 ConsumerGroup 维护一个统一的 Offset,这样,当 Consumer 来拉取消息时,就可以通过 Offset 保证一个消息,在同一个 ConsumerGroup 内只会被消费一次。而广播模式的本质,是将 Offset 转移到 Consumer 端自行保管,包括 Offset 的记录以及更新,全都放到客户端。这样 Broker 推送消息时,就不再管 ConsumerGroup,只要 Consumer 来拉取消息,就返回对应的消息。
注意点:
1、Broker 端不维护消费进度,意味着,如果消费者处理消息失败了,将无法进行消息重试。
2、Consumer 端维护 Offset 的作用是可以在服务重启时,按照上一次消费的进度,处理后面没有消费过的消息。如果 Offset 丢了,Consuer 依然可以拉取消息。
比如生产者发送了 1~10 号消息。消费者当消费到第 6 个时宕机了。当他重启时,Broker 端已经把第 10 个消息都推送完成了。如果消费者端维护好了自己的 Offset,那么他就可以在服务重启时,重新向 Broker 申请 6 号到 10 号的消息。但是,如果消费者端的 Offset 丢失了,消费者服务依然可以正常运行,但是 6 到 10 号消息就无法再申请了。后续这个消费者就只能获取 10 号以后的消息。
如果你对广播模式下的 Offset 管理确实感兴趣,可以看下我的这篇博客,针对 4.9.1 版本做的详细分析。
https://blog.csdn.net/roykingw/article/details/1263510104、过滤消息应用场景:
同一个 Topic 下有多种不同的消息,消费者只希望关注某一类消息。
例如,某系统中给仓储系统分配一个 Topic,在 Topic 下,会传递过来入库、出库等不同的消息,仓储系统的不同业务消费者就需要过滤出自己感兴趣的消息,进行不同的业务操作。

示例代码 1:简单过滤生产者端需要在发送消息时,增加 Tag 属性。比如我们上面举例当中的入库、出库。核心代码:
String[] tags = new String[] {"TagA", "TagB", "TagC"};
for (int i = 0; i < 15; i++) {Message msg = new Message("TagFilterTest",tags[i % tags.length],"Hello world".getBytes(RemotingHelper.DEFAULT_CHARSET));
SendResult sendResult = producer.send(msg);
System.out.printf("%s%n", sendResult);
}消费者端就可以通过这个 Tag 属性订阅自己感兴趣的内容。核心代码:
consumer.subscribe("TagFilterTest", "TagA");
这样,后续 Consumer 就只会出处理 TagA 的消息。
示例代码 2:SQL 过滤通过 Tag 属性,只能进行简单的消息匹配。如果要进行更复杂的消息过滤,比如数字比较,模糊匹配等,就需要使用 SQL 过滤方式。 SQL 过滤方式可以通过 Tag 属性以及用户自定义的属性一起,以标准 SQL 的方式进行消息过滤。
生产者端在发送消息时,出了 Tag 属性外,还可以增加自定义属性。核心代码:
String[] tags = new String[] {"TagA", "TagB", "TagC"};
for (int i = 0; i < 15; i++) {Message msg = new Message("SqlFilterTest",tags[i % tags.length],("Hello RocketMQ " + i).getBytes(RemotingHelper.DEFAULT_CHARSET)
);
msg.putUserProperty("a", String.valueOf(i));
SendResult sendResult = producer.send(msg);
System.out.printf("%s%n", sendResult);
}消费者端在进行过滤时,可以指定一个标准的 SQL 语句,定制复杂的过滤规则。核心代码:

consumer.subscribe("SqlFilterTest",MessageSelector.bySql("(TAGS is not null and TAGS in ('TagA', 'TagB'))" +"and (a is not null and a between 0 and 3)"));
注意:如果需要使用自定义参数进行过滤,需要在 Broker 端,将参数 enablePropertyFilter 设置成 true。这个参数默认是 false。
实现思路:
实际上,Tags 和用户自定义的属性,都是随着消息一起传递的,所以,消费者端是可以拿到消息的 Tags 和自定义属性的。比如:
consumer.registerMessageListener(new MessageListenerConcurrently() {@Overridepublic ConsumeConcurrentlyStatus consumeMessage(List<MessageExt> msgs,ConsumeConcurrentlyContext context) {for (MessageExt msg : msgs) {System.out.println(msg.getTags());
System.out.println(msg.getProperties());
}System.out.printf("%s Receive New Messages: %s %n", Thread.currentThread().getName(), msgs);
return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
}});
这样,剩下的就是在 Consumer 中对消息进行过滤了。 Broker 会在往 Consumer 推送消息时,在 Broker 端进行消息过滤。是 Consumer 感兴趣的消息,就往 Consumer 推送。
Tag 属性的处理比较简单,就是直接匹配。而 SQL 语句的处理会比较麻烦一点。 RocketMQ 也是通过 ANLTR 引擎来解析 SQL 语句,然后再进行消息过滤的。
ANLTR 是一个开源的 SQL 语句解析框架。很多开源产品都在使用 ANLTR 来解析 SQL 语句。比如 ShardingSphere,Flink 等。
注意点:
1、使用 Tag 过滤时,如果希望匹配多个 Tag,可以使用两个竖线(||)连接多个 Tag 值。另外,也可以使用星号(*)匹配所有。
2、使用 SQL 顾虑时,SQL 语句是按照 SQL92 标准来执行的。 SQL 语句中支持一些常⻅的基本操作:
数值比较,比如:>,>=,<,<=,BETWEEN,=;
字符比较,比如:=,<>,IN;
IS NULL 或者 IS NOT NULL;
逻辑符号 AND,OR,NOT;
2、消息过滤,其实在 Broker 端和在 Consumer 端都可以做。 Consumer 端也可以自行获取用户属性,不感兴趣的消息,直接返回不成功的状态,跳过该消息就行了。但是 RocketMQ 会在 Broker 端完成过滤条件的判断,只将 Consumer 感兴趣的消息推送给 Consumer。这样的好处是减少了不必要的网络 IO,但是缺点是加大了服务端的压力。不过在 RocketMQ 的良好设计下,更建议使用消息过滤机制。
3、Consumer 不感兴趣的消息并不表示直接丢弃。通常是需要在同一个消费者组,定制另外的消费者实例,消费那些剩下的消息。但是,如果一直没有另外的 Consumer,那么,Broker 端还是会推进 Offset。
5、顺序消息机制应用场景:
每一个订单有从下单、锁库存、支付、下物流等几个业务步骤。每个业务步骤都由一个消息生产者通知给下游服务。如何保证对每个订单的业务处理顺序不乱?
示例代码:
生产者核心代码:

for (int i = 0; i < 10; i++) {int orderId = i;
for(int j = 0 ; j <= 5 ; j ++){Message msg =new Message("OrderTopicTest", "order_"+orderId, "KEY" + orderId,("order_"+orderId+" step " + j).getBytes(RemotingHelper.DEFAULT_CHARSET));
SendResult sendResult = producer.send(msg, new MessageQueueSelector() {@Overridepublic MessageQueue select(List<MessageQueue> mqs, Message msg, Object arg) {Integer id = (Integer) arg;
int index = id % mqs.size();
return mqs.get(index);
}}, orderId);
System.out.printf("%s%n", sendResult);
}}通过 MessageSelector,将 orderId 相同的消息,都转发到同一个 MessageQueue 中。
消费者核心代码:
consumer.registerMessageListener(new MessageListenerOrderly() {@Overridepublic ConsumeOrderlyStatus consumeMessage(List<MessageExt> msgs, ConsumeOrderlyContext context) {context.setAutoCommit(true);
for(MessageExt msg:msgs){System.out.println("收 到消息内容 "+new String(msg.getBody()));
}return ConsumeOrderlyStatus.SUCCESS;
}});
注入一个 MessageListenerOrderly 实现。
实现思路:
RocketMQ 实现消息顺序消费,是需要生产者和消费者配合才能实现的。
1、生产者只有将一批有顺序要求的消息,放到同一个 MesasgeQueue 上,通过 MessageQueue 的 FIFO 特性保证这一批消息的顺序。
如果不指定 MessageSelector 对象,那么生产者会采用轮询的方式将多条消息依次发送到不同的 MessageQueue 上。
2、消费者需要实现 MessageListenerOrderly 接口,实际上在服务端,处理 MessageListenerOrderly 时,会给一个 MessageQueue 加锁,拿到 MessageQueue 上所有的消息,然后再去读取下一个 MessageQueue 的消息。
注意点:
1、理解局部有序与全局有序。大部分业务场景下,我们需要的其实是局部有序。如果要保持全局有序,那就只保留一个 MessageQueue。性能显然非常低。

2、生产者端尽可能将有序消息打散到不同的 MessageQueue 上,避免过于集中导致数据热点竞争。
3、消费者端只进行有限次数的重试。如果一条消息处理失败,RocketMQ 会将后续消息阻塞住,让消费者进行重试。但是,如果消费者一直处理失败,超过最大重试次数,那么 RocketMQ 就会跳过这一条消息,处理后面的消息,这会造成消息乱序。
4、消费者端如果确实处理逻辑中出现问题,不建议抛出异常,可以返回 ConsumeOrderlyStatus.SUSPEND_CURRENT_QUEUE_A_MOMENT 作为替代。
6、延迟消息应用场景:
延迟消息发送是指消息发送到 Apache RocketMQ 后,并不期望立⻢投递这条消息,而是延迟一定时间后才投递到 Consumer 进行消费。
虽然不太起眼,但是这是 RocketMQ 非常有特色的一个功能。对比下 RabbitMQ 和 Kafka。RabbitMQ 中只能通过使用死信队列变相实现延迟消息,或者加装一个插件来支持延迟消息。 Kafka 则不太好实现延迟消息。
核心方法:
当前版本 RocketMQ 提供了两种实现延迟消息的机制,一种是指定固定的延迟级别,一种是指定消息发送时间。
生产者端核心代码:
// 指定固定的延迟级别 Message message = new Message(TOPIC, ("Hello scheduled message " + i).getBytes(StandardCharsets.UTF_8));
message.setDelayTimeLevel(3); //10 秒之后发送// 指定消息发送时间 Message message = new Message(TOPIC, ("Hello scheduled message " + i).getBytes(StandardCharsets.UTF_8));
message.setDeliverTimeMs(System.currentTimeMillis() + 10_000L); //指定 10 秒之后的时间点关于延迟级别,RocketMQ 给消息定制了 18 个默认的延迟级别应用只需要根据自己的业务要求,选择对应的延迟级别即可。
实现思路:

对于指定固定延迟级别的延迟消息,RocketMQ 的实现方式是预设一个系统 Topic,名字叫做 SCHEDULE_TOPIC_XXXXX。在这个 Topic 下,预设了 18 个 MessageQueue。这里每个对列就对应了一种延迟级别。然后每次扫描这 18 个队列里的消息,进行延迟操作就可以了。
另外指定时间点的延迟消息,RocketMQ 是通过时间轮算法实现的。
7、批量消息应用场景:
生产者要发送的消息比较多时,可以将多条消息合并成一个批量消息,一次性发送出去。这样可以减少网络 IO,提升消息发送的吞吐量。
示例代码:
生产者核心代码:
List<Message> messages = new ArrayList<>(MESSAGE_COUNT);
for (int i = 0; i < MESSAGE_COUNT; i++) {messages.add(new Message(TOPIC, TAG, "OrderID" + i, ("Hello world " +i).getBytes(StandardCharsets.UTF_8)));
}//split the large batch into small ones:
ListSplitter splitter = new ListSplitter(messages);
while (splitter.hasNext()) {List<Message> listItem = splitter.next();
SendResult sendResult = producer.send(listItem);
System.out.printf("%s", sendResult);
}注意点:
批量消息的使用非常简单,但是要注意 RocketMQ 做了限制。同一批消息的 Topic 必须相同,另外,不支持延迟消息。
还有批量消息的大小不要超过 1M,如果太大就需要自行分割。

另外,当前版本中,RocketMQ 也在尝试实现一种自动化的消息分割机制。只不过目前还没有放到 Example 中。详⻅org.apache.rocketmq.client.producer.ProduceAccumulatorTest 的 testProduceAccumulator_async 和 testProduceAccumulator_sync 方法。
基于客户端内部一个新增的 ProduceAccumulator 组件 8、事务消息应用场景:
事务消息是 RocketMQ 非常有特色的一个高级功能。他的基础诉求是通过 RocketMQ 的事务机制,来保证上下游的数据一致性。
以电商为例,用户支付订单这一核心操作的同时会涉及到下游物流发货、积分变更、购物⻋状态清空等多个子系统的变更。这种场景,非常适合使用 RocketMQ 的解耦功能来进行串联。
考虑到事务的安全性,即要保证相关联的这几个业务一定是同时成功或者同时失败的。如果要将四个服务一起作为一个分布式事务来控制,可以做到,但是会非常麻烦。而使用 RocketMQ 在中间串联了之后,事情可以得到一定程度的简化。由于 RocketMQ 与消费者端有失败重试机制,所以,只要消息成功发送到 RocketMQ 了,那么可以认为 Branch2.1,Branch2.2,Branch2.3 这几个分支步骤,是可以保证最终的数据一致性的。这样,一个复杂的分布式事务问题,就变成了 MinBranch1 和 Branch2 两个步骤的分布式事务问题。
然后,在此基础上,RocketMQ 提出了事务消息机制,采用两阶段提交的思路,保证 Main Branch1 和 Branch2 之间的事务一致性。

具体的实现思路是这样的:
 . 生产者将消息发送至 Apache RocketMQ 服务端。
 . Apache RocketMQ 服务端将消息持久化成功之后,向生产者返回 Ack 确认消息已经发送成功,此时消息被标记为"暂不能投递",这种状态下的消息即为半事务消息。
 . 生产者开始执行本地事务逻辑。
 . 生产者根据本地事务执行结果向服务端提交二次确认结果(Commit 或是 Rollback),服务端收到确认结果后处理逻辑如下:
二次确认结果为 Commit:服务端将半事务消息标记为可投递,并投递给消费者。
二次确认结果为 Rollback:服务端将回滚事务,不会将半事务消息投递给消费者。
 . 在断网或者是生产者应用重启的特殊情况下,若服务端未收到发送者提交的二次确认结果,或服务端收到的二次确认结果为 Unknown 未知状态,经过固定时间后,服务端将对消息生产者即生产者集群中任一生产者实例发起消息回查。
 . 生产者收到消息回查后,需要检查对应消息的本地事务执行的最终结果。
 . 生产者根据检查到的本地事务的最终状态再次提交二次确认,服务端仍按照步骤 4 对半事务消息进行处理。
示例代码:
参⻅ org.apache.rocketmq.example.transaction.TransactionProducer 实现时的重点是使用 RocketMQ 提供的 TransactionMQProducer 事务生产者,在 TransactionMQProducer 中注入一个 TransactionListener 事务监听器来执行本地事务,以及后续对本地事务的检查。

注意点:
1、半消息是对消费者不可⻅的一种消息。实际上,RocketMQ 的做法是将消息转到了一个系统 Topic,RMQ_SYS_TRANS_HALF_TOPIC。
2、事务消息中,本地事务回查次数通过参数 transactionCheckMax 设定,默认 15 次。本地事务回查的间隔通过参数 transactionCheckInterval 设定,默认 60 秒。超过回查次数后,消息将会被丢弃。
3、其实,了解了事务消息的机制后,在具体执行时,可以对事务流程进行适当的调整。
4、如果你还是感觉不到 RocketMQ 事务消息机制的作用,那么可以看看下面这个面试题:

9、ACL 权限控制机制应用场景:
RocketMQ 提供了针对队列、用户等不同维度的非常全面的权限管理机制。通常来说,RocketMQ 作为一个内部服务,是不需要进行权限控制的,但是,如果要通过 RocketMQ 进行跨部⻔甚至跨公司的合作,权限控制的重要性就显现出来了。
权限控制体系:
1、RocketMQ 针对每个 Topic,就有完整的权限控制。比如,在控制平台中,就可以很方便的给每个 Topic 配置权限。
perm 字段表示 Topic 的权限。有三个可选项。 2:禁写禁订阅,4:可订阅,不能写,6:可写可订阅 2、在 Broker 端还提供了更详细的权限控制机制。主要是在 broker.conf 中打开 acl 的标志:aclEnable=true。然后就可以用他提供的 plain_acl.yml 来进行权限配置了。并且这个配置文件是热加载的,也就是说要修改配置时,只要修改配置文件就可以了,不用重启 Broker 服务。
文件的配置方式,也非常简单,一目了然。

#全局白名单,不受 ACL 控制
#通常需要将主从架构中的所有节点加进来
globalWhiteRemoteAddresses:
- 10.10.103.*- 192.168.0.*accounts:
#第一个账户
- accessKey: RocketMQsecretKey: 12345678whiteRemoteAddress:
admin: falsedefaultTopicP erm: DENY #默认 Topic 访问策略是拒绝 defaultGroupPerm: SUB #默认 Group 访问策略是只允许 订阅 topicPerms:
- topicA=DENY #topicA 拒绝- topicB=PUB|SUB #topicB 允 许发布和订阅消息- topicC=SUB #topicC 只允许订阅 groupPerms:
# the group should convert to retry topic
- groupA=DENY- groupB=PUB|SUB- groupC=SUB
#第二个账户,只要 是来自 192.168.1.*的 IP,就可以访问所有资源
- accessKey: rocketmq2secretKey: 12345678whiteRemoteAddress: 192.168.1.*
# if it is admin, it could access all resources
admin: true 接下来,在客户端就可以通过 accessKey 和 secretKey 提交身份信息了。客户端在使用时,需要先引入一个 Maven 依赖包。
<dependency><groupId>org.apache.rocketmq</groupId><spanrtifactId>rocketmq-acl</artifactId><version>4.9.1</version></dependency>然后在声明客户端时,传入一个 RPCHook。
//声明时传入 RPCHookDefaultMQProducer producer = new DefaultMQProducer("ProducerGroupName", getAclRPCHook());
private static final String ACL_ACCESS_KEY = "RocketMQ";
private static final String ACL_SECRET_KEY = "1234567";
static RPCHook getAclRPCHook() {return new AclClientRPCHook(new SessionCredentials(ACL_ACCESS_KEY,ACL_SECRET_KEY));
}三、 SpringBoot 整合 RocketMQ1、快速实战按照 SpringBoot 三板斧,快速创建 RocketMQ 的客户端。创建 Maven 工程,引入关键依赖:

<dependencies><dependency><groupId>org.apache.rocketmq</groupId><spanrtifactId>rocketmq-spring-boot-starter</artifactId><version>2.3.1</version><exclusions><exclusion><groupId>org.apache.rocketmq</groupId><spanrtifactId>rocketmq-client</artifactId></exclusion></exclusions></dependency><dependency><groupId>org.apache.rocketmq</groupId><spanrtifactId>rocketmq-client</artifactId><version>5.3.0</version></dependency><dependency><groupId>org.springframework.boot</groupId><spanrtifactId>spring-boot-starter-web</artifactId><version>3.0.4</version></dependency><dependency><groupId>org.springframework.boot</groupId><spanrtifactId>spring-boot-starter-test</artifactId><version>3.0.4</version></dependency><dependency><groupId>junit</groupId><spanrtifactId>junit</artifactId><version>4.13.2</version><scope>test</scope></dependency></dependencies>使用 SpringBoot 集成时,要非常注意版本!!!
SpringBoot 升级到了 3.0.4 版本后,JDK 要升级到 17 以上启动类@SpringBootApplicationpublic class RocketMQSBApplication {public static void main(String[] args) {SpringApplication.run(RocketMQSBApplication.class,args);
}}配置文件:
rocketmq.name-server=192.168.65.112:9876rocketmq.producer.group=springBootGroup
#如果这里不配,那就需要在消费者的注解中配。
#rocketmq.consumer.topic=
rocketmq.consumer.group=testGroupserver.port=9000 接下来就可以声明生产者,直接使用 RocketMQTemplate 进行消息发送。

package com.roy.rocketmq.basic;
import org.apache.rocketmq.client.producer.SendResult;
import org.apache.rocketmq.spring.core.RocketMQTemplate;
import org.apache.rocketmq.spring.support.RocketMQHeaders;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.stereotype.Component;
import javax.annotation.Resource;
/*** @author :楼兰* @description:
**/@Componentpublic class SpringProducer {@Resourceprivate RocketMQTemplate rocketMQTemplate;
public void sendMessage(String topic,String msg){this.rocketMQTemplate.convertAndSend(topic,msg);
}}另外,这个 rocketMQTemplate 不光可以发消息,还可以主动拉消息。
拉取消息时,需要配置 rocketmq.consumer.topic 和 rocketmq.consumer.group 参数消费者的声明也很简单。所有属性通过@RocketMQMessageListener 注解声明。
@Component@RocketMQMessageListener(consumerGroup = "MyConsumerGroup", topic = "TestTopic",consumeMode=ConsumeMode.CONCURRENTLY,messageModel= MessageModel.BROADCASTING)
public class SpringConsumer implements RocketMQListener<String> {@Overridepublic void onMessage(String message) {System.out.println("Received message : "+ message);
}}这里唯一需要注意下的,就是消息了。 SpringBoot 框架中对消息的封装与原生 API 的消息封装是不一样的。
2、如何处理各种消息类型 1、各种基础的消息发送机制参⻅单元测试类:com.roy.rocketmq.SpringRocketTest2、一个 RocketMQTemplate 实例只能包含一个生产者,也就只能往一个 Topic 下发送消息。如果需要往另外一个 Topic 下发送消息,就需要通过@ExtRocketMQTemplateConfiguration()注解另外声明一个子类实例。
3、对于事务消息机制,最关键的事务监听器需要通过@RocketMQTransactionListener 注解注入到 Spring 容器当中。在这个注解当中可以通过 rocketMQTemplateBeanName 属性,指向具体的 RocketMQTemplate 子类。
3、实现原理 1、RocketMQTemplateRocketMQTemplate 的注入过程参⻅org.apache.rocketmq.spring.autoconfigure.RocketMQAutoConfiguration.2、Push 模式消费者 Push 模式对于@RocketMQMessageListener 注解的处理方式,入口在 rocketmq-spring-boot-2.3.1.jar 中的 org.apache.rocketmq.spring.autoconfigure.ListenerContainerConfiguration 类中。
这个 ListenerContainerConfiguration 配置类会往 Spring 容器中注入一个 RocketMQMessageListenerContainerRegistrar 对象。

@Configuration@ConditionalOnMissingBean(RocketMQMessageListenerContainerRegistrar.class)
public class ListenerContainerConfiguration {@Beanpublic RocketMQMessageListenerContainerRegistrar rocketMQMessageListenerContainerRegistrar(RocketMQMessageConverterrocketMQMessageConverter, ConfigurableEnvironment environment, RocketMQProperties rocketMQProperties) {return new RocketMQMessageListenerContainerRegistrar(rocketMQMessageConverter, environment,rocketMQProperties);
}}注入 R ocketMQMessageListenerContainerRegistrar 后,rocketmq-spring-boot-2.3.1.jar 中会另外注入一个 RocketMQMessageListenerBeanPostProcessor 对象。这个对象继承了 SmartLifecycle 接口,因此会在初始化完成后,调用他的 start 方法。在这里会调用 RocketMQMessageListenerContainerRegistrar 的 startContainer 方法。
@Overridepublic void start() {if (!isRunning()) {this.setRunning(true);
listenerContainerRegistrar.startContainer();
}}在这个方法中,会启动一个 DefaultRocketMQListenerContainer。
public void startContainer() {for (DefaultRocketMQListenerContainer container : containers) {if (!container.isRunning()) {try {container.start();
} catch (Exception e) {log.error("Started container failed. {}", container, e);
throw new RuntimeException(e);
}}}}这里这个 DefaultRocketMQListenerContainer 实际上就是对 RocketMQ 的 DefaultMQPushConsumer 进行封装的一个容器。 start 方法实际上就是在启动一个 RocketMQ 的原生 Consumer。
至于如何创建 Consumer 实例,方法就在 DefaultRocketMQListenerContainer 的 afterPropertiesSet 方法中。其中有个 initRocketMQPushConsuer 方法,就是在创建原生 Consuer 实例。
registerContainer 的方法挺⻓的,我这里截取出跟今天的主题相关的几行重要的源码:
这其中最关注的,当然是创建容器的 createRocketMQListenerContainer 方法中。而在这个方法中,你基本看不到 RocketMQ 的原生 API,都是在创建并维护一个 DefaultRocketMQListenerContainer 对象。而这个 DefaultRocketMQListenerContainer 类,就是我们今天关注的重点。
DefaultRocketMQListenerContainer 类实现了 InitializingBean 接口,自然要先关注他的 afterPropertiesSet 方法。这是 Spring 提供的对象初始化的扩展机制。
public void afterPropertiesSet() throws Exception {initRocketMQPushConsumer();
this.messageType = getMessageType();
this.methodParameter = getMethodParameter();
log.debug("RocketMQ messageType: {}", messageType);
}这个方法就是用来初始化 RocketMQ 消费者的。在这个方法里就会创建一个 RocketMQ 原生的 DefaultMQPushConsumer 消费者。同样,方法很⻓,抽取出比较关注的重点源码。

private void initRocketMQPushConsumer() throws MQClientException {.....//检查 并创建 consumer 对象。
if (Objects.nonNull(rpcHook)) {consumer = new DefaultMQPushConsumer(consumerGroup, rpcHook, new AllocateMessageQueueAveragely(),enableMsgTrace, this.applicationContext.getEnvironment().resolveRequiredPlaceholders(this.rocketMQMessageListener.customizedTraceTopic()));
consumer.setVipChannelEnabled(false);
} else {log.debug("Access-key or secret-key not configure in " + this + ".");
consumer = new DefaultMQPushConsumer(consumerGroup, enableMsgTrace,this.applicationContext.getEnvironment().resolveRequiredPlaceholders(this.rocketMQMessageListener.customizedTraceTopic()));
}/ / 定制 instanceName,有没有很熟悉!!!
consumer.setInstanceName(RocketMQUtil.getInstanceName(nameServer));
.....//设定广播消费还是集群消费。
switch (messageModel) {case BROADCASTING:
consumer.setMessageModel(org.apache.rocketmq.common.protocol.heartbeat.MessageModel.BROADCASTING);
break;
case CLUSTERING:
consumer.setMessageModel(org.apache.rocketmq.common.protocol.heartbeat.MessageModel.CLUSTERING);
break;
default:
throw new IllegalArgumentException("Property 'messageModel' was wrong.");
}//维护消费者的其他属性。
...//指定 Consumer 的消费监听 --》在消费监听中就会去调用 onMessage 方法。
switch (consumeMode) {case ORDERLY:
consumer.setMessageListener(new DefaultMessageListenerOrderly());
break;
case CONCURRENTLY:
consumer.setMessageListener(new DefaultMessageListenerConcurrently());
break;
default:
throw new IllegalArgumentException("Property 'consumeMode' was wrong.");
}}这整个就是在维护 RocketMQ 的原生消费者对象。其中的使用方式,其实有很多地方是很值得借鉴的,尤其是消费监听的处理。
2、Pull 模式 Pull 模式的实现其实是通过在 RocketMQTemplate 实例中注入一个 DefaultLitePullConsumer 实例来实现的。只要注入并启动了这个 DefaultLitePullConsumer 示例后,后续就可以通过 template 实例的 receive 方法,来调用 DefaultLitePullConsumer 的 poll 方法,主动去 Pull 获取消息了。
初始化 DefaultLitePullConsumer 的代码依然是在 rocketmq-spring-boot-2.3.1.jar 包中。不过处理类是 org.apache.rocketmq.spring.autoconfigure.RocketMQAutoConfiguration。这个配置类会配置在 jar 包中的 spring.factories 文件中,通过 SpringBoot 的自动装载机制加载进来。

@Bean(CONSUMER_BEAN_NAME)
@ConditionalOnMissingBean(DefaultLitePullConsumer.class)
@ConditionalOnProperty(prefix = "rocketmq", value = {"na me-server", "consumer.group", "consumer.topic"}) //解析的 springboot 配置属性。
public DefaultLitePullConsumer defaultLitePullConsumer(RocketMQProperties rocketMQProperties)
throws MQClientException {RocketMQProperties.Consumer consumerConfig = rocketMQProperties.getConsumer();
String nameServer = rocketMQProperties.getNameServer();
String groupName = consumerConfig.getGroup();
String topicName = consumerConfig.getTopic();
Assert.hasText(nameServer, "[rocketmq.name-server] must not be null");
Assert.hasText(groupName, "[rocketmq.consumer.group] must not be null");
Assert.hasText(topicName, "[rocketmq.consumer.topic] must not be null");
...//创建消费者 DefaultLitePullConsumer litePullConsumer = RocketMQUtil.createDefaultLitePullConsumer(nameServer,accessChannel,groupName, topicName, messageModel, selectorType, selectorExpression, ak, sk, pullBatchSize, useTLS);
litePullConsumer.setEnableMsgTrace(consumerConfig.isEnableMsgTrace());
litePullConsumer.setCustomizedTraceTopic(consumerConfig.getCustomizedTraceTopic());
litePullConsumer.setNamespace(consumerConfig.getNamespace());
return litePullConsumer;
}RocketMQUtil.createDefaultLitePullConsumer 方法中,就是在维护一个 DefaultLitePullConsumer 实例。这个实例就是 RocketMQ 的原生 API 当中提供的拉模式客户端。
实际开发中,拉模式用得比较少。但是,其实 RocketMQ 针对拉模式也做了非常多的优化。原本提供了一个 DefaultMQPullConsumer 类,进行拉模式消息消费,DefaultLitePullConsumer 在此基础上做了很多优化。有兴趣可以自己研究一下。
四、 RocketMQ 客户端注意事项 1、消息的 ID,Key 和 Tag 这里有个小细节需要注意,producer 生产者端发送的是 Message 对象,而 Consumer 消费端处理的却是 MessageExt 对象。也就是说,虽然都是传递消息,但是 Consumer 端拿到的信息会比 Producer 端发送的消息更多。这里就有几个重点的参数需要理解。那就是 MessageId,Key 和 Tag。
MessageId 是 RocketMQ 内部给每条消息分配的唯一索引 Producer 发送的 Message 对象是没有 msgId 属性的。 Broker 端接收到 Producer 发过来的消息后,会给每条消息单独分配一个唯一的 msgId。这个 msgID 可以作为消息的唯一主键来使用。
但是需要注意,对于客户端来说,毕竟是不知道这个 msgId 是如何产生的。实际上,在 RocketMQ 内部,也会针对批量消息、事务消息等特殊的消息机制,有特殊的 msgId 分配机制。因此,在复杂业务场景下,不建议使用 msgId 来作为消息的唯一索引,而建议采用下面的 key 属性,自行指定业务层面上的唯一索引。
key 是 Message 中的补充信息在 Producer 发送 Message 消息时,同样也是没有 key 属性的。而这里设置的 key,其实是以 RocketMQ 中消息的补充属性的形式插入进去的。
public void setKeys(String keys) {this.putProperty(MessageConst.PROPERTY_KEYS, keys);
}void putProperty(final String name, final String value) {if (null == this.properties) {this.properties = new HashMap<>();
}this.properties.put(name, value);
}从这里可以看出,key 属性的本质只是 Message 中的一个补充信息,我们也可以像使用 key 一样,往消息当中添加一些自定义的属性。 RocketMQ 内部也大量运用了这些自定义的属性,具体可以参⻅源码当中的 MessageConst 类。

针对 key 这一个属性,建议在业务中可以添加一些带有业务唯一性的数据,作为 MessageId 的补充。 RocketMQ 基于 Keys 属性,实现了消息溯源、消息压缩等一系列功能。
通过 Tag 进行消息过滤性能非常高 Tag 属性也是 Producer 发送的 Message 对象的固有属性。其作用主要是用来进行消息过滤。实际上,RocketMQ 的服务端会把消息的 Tag 信息以某种形式(hashCode)写入到检索消息的 ConsumeQueue 索引中。这样当 Consumer 消费消息时,就可以通过过滤 ConsumeQueue 索引中的 Tag 属性,快速找到自己感兴趣的消息。
ConsumeQueue 索引文件后续会做详细介绍。这里你可以简单理解为中华字典前面的索引,通过这个索引可以快速定位到某一条具体的消息。
由于 Tag 信息已经包含在索引中了,所以使用 Tag 进行适当的消息过滤,性能是非常高的,这也是官方推荐的使用 RocketMQ 的一种最佳实践。
2、最佳实践一个应用尽可能用一个 Topic,而消息子类型则可以用 tags 来标识。 tags 可以由应用自由设置,只有生产者在发送消息设置了 tags,消费方在订阅消息时才可以利用 tags 通过 broker 做消息过滤:message.setTags("TagA")。
Kafka 的一大问题是 Topic 过多,会造成 Partition 文件过多,影响性能。而 RocketMQ 中的 Topic 完全不会对消息转发性能有影响。但是 Topic 过多,还是会加大 RocketMQ 的元数据维护的性能消耗。所以,在使用时,还是需要对 Topic 进行合理的分配。
使用 Tag 区分消息时,尽量直接使用 Tag 过滤,不要使用复杂的 SQL 过滤。因为消息过滤机制虽然可以减少网络 IO,但是毕竟会加大 Broker 端的消息处理压力。所以,消息过滤的逻辑,还是越简单越好。
3、消费者端进行幂等控制在 MQ 系统中,对于消息幂等有三种实现语义:
at most once 最多一次:每条消息最多只会被消费一次 at least once 至少一次:每条消息至少会被消费一次 exactly once 刚刚好一次:每条消息都只会确定的消费一次这三种语义都有他适用的业务场景。
其中,at most once 是最好保证的。 RocketMQ 中可以直接用异步发送、 sendOneWay 等方式就可以保证。
而 at least once 这个语义,RocketMQ 也有同步发送、事务消息等很多方式能够保证。
而这个 exactly once 是 MQ 中最理想也是最难保证的一种语义,需要有非常精细的设计才行。 RocketMQ 只能保证 at least once,保证不了 exactly once。所以,使用 RocketMQ 时,需要由业务系统自行保证消息的幂等性。
关于这个问题,官网上有明确的回答:
4. Are messages delivered exactly once?
RocketMQ ensures that all messages are delivered at least once. In most cases, the messages are not repeated.消息幂等的必要性在互联网应用中,尤其在网络不稳定的情况下,消息队列 RocketMQ 的消息有可能会出现重复,这个重复简单可以概括为以下情况:
发送时消息重复当一条消息已被成功发送到服务端并完成持久化,此时出现了网络闪断或者客户端宕机,导致服务端对客户端应答失败。 如果此时生产者意识到消息发送失败并尝试再次发送消息,消费者后续会收到两条内容相同并且 Message ID 也相同的消息。
投递时消息重复消息消费的场景下,消息已投递到消费者并完成业务处理,当客户端给服务端反馈应答的时候网络闪断。 为了保证消息至少被消费一次,消息队列 RocketMQ 的服务端将在网络恢复后再次尝试投递之前已被处理过的消息,消费者后续会收到两条内容相同并且 Message ID 也相同的消息。
负载均衡时消息重复(包括但不限于网络抖动、 Broker 重启以及订阅方应用重启)
当消息队列 RocketMQ 的 Broker 或客户端重启、扩容或缩容时,会触发 Rebalance,此时消费者可能会收到重复消息。
处理方式

从上面的分析中,我们知道,在 RocketMQ 中,是无法保证每个消息只被投递一次的,所以要在业务上自行来保证消息消费的幂等性。
而要处理这个问题,RocketMQ 的每条消息都有一个唯一的 MessageId,这个参数在多次投递的过程中是不会改变的,所以业务上可以用这个 MessageId 来作为判断幂等的关键依据。
但是,这个 MessageId 是无法保证全局唯一的,也会有冲突的情况。所以在一些对幂等性要求严格的场景,最好是使用业务上唯一的一个标识比较靠谱。例如订单 ID。而这个业务标识可以使用 Message 的 Key 来进行传递。
4、关注错误消息重试我们已经知道 RocketMQ 的消费者端,如果处理消息失败了,Broker 是会将消息重新进行投送的。而在重试时,RocketMQ 实际上会为每个消费者组创建一个对应的重试队列。重试的消息会进入一个 “%RETRY%”+ConsumeGroup 的队列中。
多关注重试队列,可以及时了解消费者端的运行情况。这个队列中出现了大量的消息,就意味着消费者的运行出现了问题,要及时跟踪进行干预。
然后 RocketMQ 默认允许每条消息最多重试 16 次,每次重试的间隔时间如下:
重试次数 与上次重试的间隔时间 重试次数 与上次重试的间隔时间 1 10 秒 9 7 分钟 2 30 秒 10 8 分钟 3 1 分钟 11 9 分钟 4 2 分钟 12 10 分钟 5 3 分钟 13 20 分钟 6 4 分钟 14 30 分钟 7 5 分钟 15 1 小时 8 6 分钟 16 2 小时这个重试时间跟延迟消息的延迟级别是对应的。不过取的是延迟级别的后 16 级别。
messageDelayLevel=1s 5s 10s 30s 1m 2m 3m 4m 5m 6m 7m 8m 9m 10m 20m 30m 1h 2h 这个重试时间可以将源码中的 org.apache.rocketmq.example.quickstart.Consumer 里的消息监听器返回状态改为 RECONSUME_LATER 测试一下。
重试次数:
如果消息重试 16 次后仍然失败,消息将不再投递。转为进入死信队列。
然后关于这个重试次数,RocketMQ 可以进行定制。例如通过 consumer.setMaxReconsumeTimes(20);将重试次数设定为 20 次。当定制的重试次数超过 16 次后,消息的重试时间间隔均为 2 小时。
配置覆盖:
消息最大重试次数的设置对相同 GroupID 下的所有 Consumer 实例有效。并且最后启动的 Consumer 会覆盖之前启动的 Consumer 的配置。
5、手动处理死信队列当一条消息消费失败,RocketMQ 就会自动进行消息重试。而如果消息超过最大重试次数,RocketMQ 就会认为这个消息有问题。但是此时,RocketMQ 不会立刻将这个有问题的消息丢弃,而会将其发送到这个消费者组对应的一种特殊队列:死信队列。

通常,一条消息进入了死信队列,意味着消息在消费处理的过程中出现了比较严重的错误,并且无法自行恢复。此时,一般需要人工去查看死信队列中的消息,对错误原因进行排查。然后对死信消息进行处理,比如转发到正常的 Topic 重新进行消费,或者丢弃。
死信队列的名称是%DLQ%+ConsumGroup 死信队列的特征:
一个死信队列对应一个 ConsumGroup,而不是对应某个消费者实例。
如果一个 ConsumeGroup 没有产生死信队列,RocketMQ 就不会为其创建相应的死信队列。
一个死信队列包含了这个 ConsumeGroup 里的所有死信消息,而不区分该消息属于哪个 Topic。
死信队列中的消息不会再被消费者正常消费。
死信队列的有效期跟正常消息相同。默认 3 天,对应 broker.conf 中的 fileReservedTime 属性。超过这个最⻓时间的消息都会被删除,而不管消息是否消费过。
注:默认创建出来的死信队列,他里面的消息是无法读取的,在控制台和消费者中都无法读取。这是因为这些默认的死信队列,他们的权限 perm 被设置成了 2:禁读(这个权限有三种 2:禁读,4:禁写,6:可读可写)。需要手动将死信队列的权限配置成 6,才能被消费(可以通过 mqadmin 指定或者 web 控制台)。
2、RocketMQ 客户端编程模型.md

