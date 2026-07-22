---



title: "一、快速上手篇"
description: "什么是 MQ,有什么用 2、主流 MQ 产品对比二、 RabbitMQ 快速上手 1、RabbitMQ 产品介绍 2、安装 RabbitMQ1、前置环境 2、安"
author: hsc
date: 2023-01-23 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Kafka', 'RocketMQ', 'Netty']
toc: true



---

### 一、 MQ 介绍
1、什么是 MQ,有什么用 2、主流 MQ 产品对比二、 RabbitMQ 快速上手 1、RabbitMQ 产品介绍 2、安装 RabbitMQ1、前置环境 2、安装 RabbitMQ 服务 3、RabbitMQ 基础使用 1、理解 Queue2、理解 Exchange3、理解 Connection 和 Channel 三、 RabbitMQ 中的核心概念总结 RabbitMQ 快速上手以及核心概念详解-- 楼兰这一章节我们将快速搭建 RabbitMQ 服务,并了解 RabbitMQ 的核心工作机制。
一、 MQ 介绍 1、什么是 MQ,有什么用 MQ 即 MessageQueue,消息对列。我们这次要学习的 RabbitMQ 就是一种典型的 MQ 产品。
那么到底什么是 MQ 呢?可以分两个部分来理解:消息 Message:在不同应用程序之间传递的数据。队列 Queue,一种 FIFO 先进先出的数据结构。将消息以队列的形式存储起来,并且在不同的应用程序之间进行传递,这就成了 MessageQueue。
MQ 产品最直接的作用,是将同步的事件驱动改为异步的消息驱动。这话什么意思?我们从一个最常⻅的 SpringBoot 应用开始说起。
首先搭建一个普通的 Maven 项目,在 pom.xml 中引入 SpringBoot 的依赖:
<dependencies><dependency><groupId>org.springframework.boot</groupId><spanrtifactId>spring-boot-starter</artifactId><version>2.4.5</version></dependency></dependencies>然后增加一个监听器类 public class MyApplicationListener implements ApplicationListener<ApplicationEvent> {@Overridepublic void onApplicationEvent(ApplicationEvent applicationEvent) {System.out.println("=====> MyApplicationListener: "+applicationEvent);
}}接下来,添加一个 SpringBoot 启动类。在启动类中加入自己的这个监听器。
@SpringBootApplicationpublic class AppDemo implements CommandLineRunner {public static void main(String[] args) {SpringApplication application = new SpringApplication(AppDemo.class);
application.addListeners(new MyApplicationListener());
application.run(args);
}@Resourceprivate ApplicationContext applicationContext;
@Overridepublic void run(String... args) throws Exception {applicationContext.publishEvent(new ApplicationEvent("myEvent"){});
}}好了。不用添加配置文件,直接启动就行。 然后可以看到这样的结果:

从这个示例看到,SpringBoot 框架其实在启动时,就会尝试发布各种 ApplicationEvent 事件,表示自己启动到了哪个步骤。这时,SpringBoot 框架就可以称为消息生产者 Producer。同样的,只要有 ApplicationEvent 事件发布了,就会触发 MyApplicationListener 监听器,处理这些事件。 MyApplicationListener 就可以成为消息消费者 Consumer。
Producer 和 Consumer 他们的运行状况互不干涉,不管有没有 Consumer,Producer 一样会发布消息。反过来,不管 Producer 有没有发布消息,Consumer 也一样会监听这些事件。这种方式,实际上就是通过事件中包含的消息在驱动 Producer 和 Consumer 工作,这种工作方式也就称为消息驱动。
与消息驱动形成对比的是常⻅的事件驱动。比如经常写的 Controller,只有通过一个事件主动触发,才会调用。
从这个简单的例子可以看到,SpringBoot 内部就集成了这种消息驱动的机制。但是,这些 Producer 和 Consumer 都只能在一个进程中使用。如果需要跨进行进行调用呢?这就需要独立一个中间服务,才能发布和接受这些消息。而这个中间服务,就是 MQ 中间件。
比如在一个大型电商项目中,订单服务完成下单,就可以发布下单事件,而下游的消费者,就可以消费这个下单事件,进行一些补充的业务。
在这个业务过程中,MQ 中间件应该要起到什么作用呢?
解耦:Producer 和 Consumer 都只跟中间件进行交互,而不需要互相进行交互。这意味着,在 Producer 发送消息时,不需要考虑有没有 Consumer 或者有多少个 Consumer。反之亦然。甚至,即便 Producer 和 Consumer 是用不同语言开发的,只要都能够与 MQ 中间件正常交互,那么他们就可以通过 MQ 中间件进行消息传递。
异步:消息并不是从 Producer 发送出来后,就立即交由 Consumer 处理,而是在 MQ 中间件中暂存下来。等到 Consumer 启动后,自行去 MQ 中间件上处理。也就是说,错开了 Producer 发送消息和 Consumer 消费消息的时间。
削峰:有了 MQ 做消息暂存,那么当 Producer 发送消息的速度与 Consumer 处理消息的速度不一致时,MQ 就能起到削峰填谷的作用。
2、主流 MQ 产品对比在 MQ⻓期发展过程中,诞生了很多 MQ 产品,但是有很多 MQ 产品都已经逐渐被淘汰了。比如早期的 ZeroMQ,ActiveMQ 等。目前最常用的 MQ 产品包括 Kafka、RabbitMQ 和 RocketMQ。我们对这三个产品做下简单的比较,重点需要理解他们的适用场景。
优点 缺点 适用场景吞吐量非常大,性能非常好,技术生 分布式日志收集,大数据采 Kafka 功能比较单一态完整 集 RabbitM 吞吐量较低。消息积压会影响性能。 erlang 语言消息可靠性高,功能全面 企业内部系统调用 Q 比较小众 Rocket 高吞吐、高性能、高可用,高级功能 几乎全场景。尤其适合金融技术生态相对没有那么完整 MQ 非常全 场景

好的产品都是在不断演进的,所以对这些产品的理解也需要与时俱进。比如现在还有个 MQ 产品 Pulsar,非常适合于大型企业内部海量的系统调用,也体现了非常强大的竞争力。
二、 RabbitMQ 快速上手 1、RabbitMQ 产品介绍 RabbitMQ 的历史可以追随到 2005 年,他是一个非常老牌的 MQ 产品,使用非常广泛。同时期的很多 MQ 产品都已经逐渐被业界淘汰了,比如 2003 年诞生的 ActiveMQ,2012 年诞生的 ZeroMQ,但是 RabbitMQ 却依然稳稳占据一席之地,足可⻅他的经典。官网地址 https://www.rabbitmq.com/ 。
目前最新的官网是这样介绍的:
最新的 3.13 版本官网做了一次大改版,由此可⻅RabbitMQ 产品的开发活力依然非常强劲。
2、安装 RabbitMQ1、前置环境我们这次选择的 RabbitMQ 版本是目前最新的 3.13 版本。其实就 RabbitMQ 最近的几个版本,核心的 Quorum Queue 和 Stream Queue 功能早在 3.9.x 版本就已经成型了。后续的版本主要是对这两个核心功能做一些修复以及增强,同时增加了很多新的功能插件。
RabbitMQ 是基于 Erlang 语言开发的,所以安装 RabbitMQ 之前需要安装 Erlang 语言环境。需要注意下的是 RabbitMQ 与 Erlang 语言之间是有版本对应关系的。目前 3.13 版本的 RabbitMQ 需要 Erlang 语言版本 26.0 到 26.2.x 之间。

需要先从官网下载操作系统对应的 RabbitMQ 安装包以及 Erlang 语言的安装包。
2、安装 RabbitMQ 服务 RabbitMQ 服务有多种安装方式。但是在学习阶段,建议大家使用 CentOS 手动进行安装。这样更能接触产品的细节。之后使用其他操作系统或者使用 Docker 等技术安装时,才会更顺利。
需要注意的是,当前版本的 RabbitMQ 建议 CentOS 版本最好升级到 CentOS9 版本。至少不能低于 CentOS8。
Erlang 语言包的安装,建议使用 RabbitMQ 提供的 zero dependency 版本。下载地址:https://github.com/rabbitmq/erlang-rpm/releases[root@192-168-65-112 ~]# rpm -ivh erlang-26.2.5.2-1.el9.x86_64.rpm 警告:erlang-26.2.5.2-1.el9.x86_64.rpm: 头 V4 RSA/SHA256 Signature, 密钥 ID 6026dfca: NOKEYVerifying... ################################# [100%]准备中... ################################# [100%]正在升级/安装...1:erlang-26.2.5.2-1.el9 ################################# [100%][root@192-168-65-112 ~]# erl -versionErlang (SMP,ASYNC_THREADS) (BEAM) emulator version 14.2.5.2 接下来安装 RabbitMQ。这里我们采用 RPM 安装包的方式。安装包下载地址:https://github.com/rabbitmq/rabbitmq-server/releases 。 这里我们下载无依赖版本: rabbitmq-server-3.13.6-1.el8.noarch.rpm[root@192-168-65-112 ~]# rpm -ivh rabbitmq-server-3.13.6-1.el8.noarch.rpm 警告:rabbitmq-server-3.13.6-1.el8.noarch.rpm: 头 V4 RSA/SHA512 Signature, 密 钥 ID 6026dfca: NOKEYVerifying... ################################# [100%]准备中... ################################# [100%]正在升级/安装...1:rabbitmq-server-3.13.6-1.el8 ################################# [100%]/usr/lib/tmpfiles.d/rabbitmq-server.conf:1: Line references path below legacy directory /var/run/, updating /var/run/rabbitmq →/run/rabbitmq; please update the tmpfiles.d/ drop-in file accordingly.

安装完成后,可以使用几个常用的指令维护 RabbitMQ 的服务状态。
service rabbitmq-server start --启动 Rabbitmq 服务。启动应用之前要先启动服务。
rabbitmq-server -deched --后台启动 RabbitMQ 应用 rabbitmqctl start_app --启动 Rabbitmqrabbitmqctl stop --关闭 Rabbitmqrabbitmqctl status -- 查看 RabbitMQ 服务状态。
出现 Status 为 Runtime 表示启动成功。
默认情况下, RabbitMQ 只是一个后台服务,不便于管理。而 RabbitMQ 提供了管理插件,可以使用图形化的方式管理 RabbitMQ。
[root@192-168-65-112 ~]# rabbitmq-plugins enable rabbitmq_managementEnabling plugins on node rabbit@192-168-65-112:
rabbitmq_managementThe following plugins have been configured:
rabbitmq_managementrabbitmq_management_agentrabbitmq_web_dispatchApplying plugin configuration to rabbit@192-168-65-112...The following plugins have been enabled:
rabbitmq_managementrabbitmq_management_agentrabbitmq_web_dispatchset 3 plugins.Offline change; changes will take effect at broker restart.--重启服务后生效 service rabbitmq-server startrabbitmqctl start_app 插件激活后,就可以访问 RabbitMQ 的 Web 控制台了。访问端口 15672.RabbitMQ 提供了默认的用户名 guest,密码 guest。但是默认情况下,只允许本地登录,远程访问是无法登录的。
这时,通常都会创建一个管理员账号单独对 RabbitMQ 进行管理。
[root@192-168-65-112 ~]# rabbitmqctl add_user admin adminAdding user "admin" ...Done. Don't forget to grant the user permissions to some virtual hosts! See 'rabbitmqctl help set_permissions' to learn more.[root@192-168-65-112 ~]# rabbitmqctl set_permissions -p / admin "." "." ".*"
Setting permissions for user "admin" in vhost "/" ...[root@192-168-65-112 ~]# rabbitmqctl set_user_tags admin administratorSetting tags for user "admin" to [administrator] ...这样就可以用 admin/admin 用户登录 Web 控制台了。

3、RabbitMQ 基础使用登录控制台后上方就能看到 RabbitMQ 的主要功能。其中 Overview 是概述,主要展示 RabbitMQ 服务的一些整体运行情况。后面 Conections、Channels、Exchanges 和 Queues 就是 RabbitMQ 的核心功能。最后的 Admin 则是一些管理功能。
例如我们之前创建的 admin 用户,就表现在 Admin 下的用户信息中。
例如,在 Admin 管理⻚面,可以创建一个虚拟机,virtual machine,并配置 admin 用户拥有访问的权限。
在 RabbitMQ 中,不同虚拟机之间的资源是完全隔离的。在资源充足的情况下,每个虚拟机可以当成一个独立的 RabbitMQ 服务来使用。其他管理功能这里就不详细介绍了,后续随着使用深入再做介绍。
接下来我们来上手使用一下 RabbitMQ 的核心功能。
1、理解 QueueExchange 和 Queue 是 RabbitMQ 中用来传递消息的核心组件。我们可以简单体验一下。
1、在 Queues 菜单,创建一个名为 test1 的经典对列

<!-- [image removed: local file path] -->
创建完成后,选择这个 test1 队列,就可以在⻚面上直接发送消息以及消费消息了。
<!-- [image removed: local file path] -->

在 RabbitMQ 中的消息都是通过 Queue 队列传递的,这个 Queue 其实就是一个典型的 FIFO 的队列数据结构。我们当前的演示是通过控制台⻚面来通过 Queue 进行收发消息。未来,我们编写客户端时,就是绑定对应的对列进行消息收发。
2、理解 Exchange 队列 Queue 即可以发消息,也可以收消息,那旁边的 Exchange 交换机是干什么的呢?其实他也是用来辅助发送消息的。 Exchange 与 Queue 之间会建立一种绑定关系,通过绑定关系,Exchange 交换机里发送的消息就可以分发到不同的 Queue 上。
进入 Exchanges 菜单,可以看到针对每个虚拟机,RabbitMQ 都预先创建了多个 Exchange 交换机。
<!-- [image removed: local file path] -->
这里我们选择 amq.direct 交换机,进入交换机详情⻚,选择 Binding,并将 test1 队列绑定到这个交换机上。
注意选择/mirror 虚拟机上的 Exchange

绑定完成后,可以在 Exchange 详情⻚以及 Queue 详情⻚都看到绑定的结果。
<!-- [image removed: local file path] -->
接下来就可以在 Exchange 的详情⻚里发送消息。然后在 test1 这个 queue 里就能消费到这条消息。
<!-- [image removed: local file path] -->
Exchange 交换机并不实际存储消息,只是将发送到 Exchange 的消息转发到绑定的队列上。在具体使用时,通常只有消息生产者需要与 Exchange 打交道。而消费者,则并不需要与 Exchange 打交道,只要从 Queue 中消费消息就可以了。
另外,Exchange 既然可以绑定一个队列,当然也可以绑定多个队列。在实际使用中,Exchange 与 Queue 之间可以建立不同类型的绑定关系,然后通过一些不同的策略,选择将消息转发到哪些 Queue 上。这时候,Messaage 上几个没有用上的参数,像 Routing Key ,Headers,Properties 这些参数就能派上用场了。
在这个过程中,我们都是通过⻚面操作完成的消息发送与接收。在实际应用时,其实就是通过 RabbitMQ 提供的客户端 API 来完成这些功能。但是整个执行的过程,其实跟⻚面操作是相同的。
3、理解 Connection 和 Channel 这两个功能实际上是跟客户端应用的对应关系。一个 Connection 可以理解为一个客户端应用。而一个应用可以创建多个 Channel,用来与 RabbitMQ 进行交互。
我们可以来搭建一个客户端应用了解一下。
1、创建一个 Maven 项目,在 pom.xml 中引入 RabbitMQ 客户端的依赖:

<dependency><groupId>com.rabbitmq</groupId><spanrtifactId>amqp-client</artifactId><version>5.21.0</version></dependency>2、然后就可以创建一个消费者实例,尝试从 RabbitMQ 上的 test1 这个队列上拉取消息。
public class FirstConsumer {private static final String HOST_NAME="192.168.65.112";
private static final int HOST_PORT=5672;
private static final String QUEUE_NAME="test2";
public static final String USER_NAME="admin";
public static final String PASSWORD="admin";
public static final String VIRTUAL_HOST="/mirror";
public static void main(String[] args) throws Exception{ConnectionFactory factory = new ConnectionFactory();
factory.setHost(HOST_NAME);
factory.setPort(HOST_PORT);
factory.setUsername(USER_NAME);
factory.setPassword(PASSWORD);
factory.setVirtualHost(VIRTUAL_HOST);
Connection connection = factory.newConnection();
Channel channel = connection.createChannel();
/*** 声明一个对列。几个参数依次为: 队列名,durable 是否实例化;exclusive:是否独占;autoDelete:是否自动删除;arguments:参数* 这几个参数跟创建队列的⻚面是一致的。
* 如果 Broker 上没有队列,那么就会自动创 建队列。
* 但是如果 Broker 上已经由了这个队列。那么队列的属 性必须匹配,否则会报错。
*/channel.queueDeclare(QUEUE_NAME, true, false, false, null);
//每个 worker 同时最多只处理一个消息 channel.basicQos(1);
//回调函数,处理接收到的 消息 Consumer myconsumer = new DefaultConsumer(channel) {@Overridepublic void handleDelivery(String consumerTag, Envelope envelope,AMQP.BasicProperties properties, byte[] body)
throws IOException {System.out.println("========================");
String routingKey = envelope.getRoutingKey();
System.out.println("routingKey >"+routingKey);
String contentType = properties.getContentType();
System.out.println("contentType >"+contentType);
long deliveryTag = envelope.getDeliveryTag();
System.out.println("deliveryTag >"+deliveryTag);
System.out.println("content:"+new String(body,"UTF-8"));
// (process the message components here ...)
channel.basicAck(deliveryTag, false);
}};
// 从 test1 队列接收消息 channel.basicConsume(QUEUE_NAME, myconsumer);
}}暂时不用过多纠结于实现细节,注意梳理整体实现流程。
执行这个应用程序后,就会在 RabbitMQ 上新创建一个 test2 的队列(如果你之前没有创建过的话),并且启动一个消费者,处理 test2 队列上的消息。这时,我们可以从管理平台⻚面上往 test2 队列发送一条消息,这个消费者程序就会及时消费消息。

<!-- [image removed: local file path] -->
然后在管理平台的 Connections 和 Channels 里就能看到这个消费者程序与 RabbitMQ 建立的一个 Connection 连接与一个 Channel 通道。
这里可以看到 Connection 就是与客户端的一个连接。只要连接还通着,他的状态就是 running。而 Channel 是 RabbitMQ 与客户端进行数据交互的一个通道,没有数据交互时,状态就是 idle 闲置。有数据交互时,就会变成 running。在他们后面,都会展示出数据交互的状态。
另外,从这个简单示例中可以看到,Channel 是从 Connection 中创建出来的,这也意味着,一个 Connection 中可以创建出多个 Channel。从这些 Connection 和 Channel 中可以很方面的了解到 RabbitMQ 当前的服务运行状态。
三、 RabbitMQ 中的核心概念总结通过这些操作,我们就可以了解到 RabbitMQ 的消息流转模型。

<!-- [image removed: local file path] -->
这里包含了很多 RabbitMQ 的重要概念:
1、Queue 对列这是 RabbitMQ 中最核心的概念。他是实际保存数据的最小单元。 Queue 结构天生就具有 FIFO 的顺序。消息最终要被发送到 Queue 当中,然后才能被消费者进行消费处理。
2、Exchange 交换机这是 RabbitMQ 中进行数据路由的重要组件。 Exchange 并不实际保存消息,而是与 Queue 之间建立绑定关系,然后,如果有消息发送到了 Exchange,Exchange 就会将消息转发到 Queue 对列中,从而被对应的消费者消费处理。
在使用 RabbitMQ 时,Exchange 并不是必须的,但是,通常 Exchange 是与应用开发联系最紧密的。因为 RabbitMQ 支持的很多业务场景都要 Exchange 参与。
3、virtual host 虚拟主机 RabbitMQ 出于服务器复用的想法,可以在一个 RabbitMQ 集群中划分出多个虚拟主机,每一个虚拟主机都有全套的基础服务组件,可以针对每个虚拟主机进行权限以及数据分配。不同虚拟主机之间是完全隔离的,如果不考虑资源分配的情况,一个虚拟主机就可以当成一个独立的 RabbitMQ 服务使用。
同时,也意味着不同虚拟主机之间是无法进行通信的,尽管他们是部署在同一个 RabbitMQ 服务上。例如,你无法通过虚拟机 A 的 Exchange 交换机将消息转发到虚拟机 B 的 Queue 上。
4、连接 Connection 客户端与 RabbitMQ 进行交互,首先就需要建立一个 TPC 连接,这个连接就是 Connection。既然是通道,那就需要尽量注意在停止使用时要关闭,释放资源。
5、信道 Channel 一旦客户端与 RabbitMQ 建立了连接,就会分配一个 AMQP 信道 Channel。每个信道都会被分配一个唯一的 ID。也可以理解为是客户端与 RabbitMQ 实际进行数据交互的通道,我们后续的大多数的数据操作都是在信道 Channel 这个层面展开的。
RabbitMQ 为了减少性能开销,也会在一个 Connection 中建立多个 Channel,这样便于客户端进行多线程连接,这些连接会复用同一个 Connection 的 TCP 通道,所以在实际业务中,对于 Connection 和 Channel 的分配也需要根据实际情况进行考量。
最后,对照这几个核心概念,尝试去理解下那个看不懂的 Java 客户端代码,这就是使用 RabbitMQ 的核心。
