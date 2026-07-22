---

title: "Zookeeper经典应用场景实战（一）"
description: "学习本节课的基础: 掌握 Zookeeper 的节点特性和监听机制 1."
author: hsc
date: 2023-04-13 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Redis', 'Kafka', 'RocketMQ', 'Zookeeper']
toc: true

---

学习本节课的基础: 掌握 Zookeeper 的节点特性和监听机制
1. Zookeeper Java 客户端实战 ZooKeeper 应用的开发主要通过 Java 客户端 API 去连接和操作 ZooKeeper 集群。可供选择的 Java 客户端 API 有:
ZooKeeper 官方的 Java 客户端 API。
第三方的 Java 客户端 API,比如 Curator。
ZooKeeper 官方的客户端 API 提供了基本的操作。例如,创建会话、创建节点、读取节点、更新数据、删除节点和检查节点是否存在等。不过,对于实际开发来说,ZooKeeper 官方 API 有一些不足之处,具体如下:
ZooKeeper 的 Watcher 监测是一次性的,每次触发之后都需要重新进行注册。
会话超时之后没有实现重连机制。
异常处理烦琐,ZooKeeper 提供了很多异常,对于开发人员来说可能根本不知道应该如何处理这些抛出的异常。
仅提供了简单的 byte[]数组类型的接口,没有提供 Java POJO 级别的序列化数据处理接口。
创建节点时如果抛出异常,需要自行检查节点是否存在。
无法实现级联删除。
总之,ZooKeeper 官方 API 功能比较简单,在实际开发过程中比较笨重,一般不推荐使用。
1.1 Zookeeper 原生 Java 客户端使用引入 zookeeper client 依赖 1 <!-- zookeeper client -->2 <dependency>3 <groupId>org.apache.zookeeper</groupId>4 <spanrtifactId>zookeeper</artifactId>5 <version>3.8.0</version>6 </dependency>注意:保持与服务端版本一致,不然会有很多兼容性的问题

ZooKeeper 原生客户端主要使用 org.apache.zookeeper.ZooKeeper 这个类来使用 ZooKeeper 服务。
ZooKeeper 常用构造器 1 ZooKeeper (connectString, sessionTimeout, watcher)
connectString:使用逗号分隔的列表,每个 ZooKeeper 节点是一个 host.port 对,host 是机器名或者 IP 地址,port 是 ZooKeeper 节点对客户端提供服务的端口号。客户端会任意选取 connectString 中的一个节点建立连接。
sessionTimeout : session timeout 时间。
watcher:用于接收到来自 ZooKeeper 集群的事件。
使用 zookeeper 原生 API,连接 zookeeper 集群 1 public class ZkClientDemo {23 private static final String CONNECT_STR="localhost:2181";
4 private final static StringCLUSTER_CONNECT_STR="192.168.65.156:2181,192.168.65.190:2181,192.168.65.200:2181";
56 public static void main(String[] args) throws Exception {78 final CountDownLatch countDownLatch=new CountDownLatch(1);
9 ZooKeeper zooKeeper = new ZooKeeper(CLUSTER_CONNECT_STR,10 4000, new Watcher() {11 @Override12 public void process(WatchedEvent event) {13 if(Event.KeeperState.SyncConnected==event.getState()
14 && event.getType()== Event.EventType.None){15 //如果收到了服务端的响应事件,连接成功 16 countDownLatch.countDown();
17 System.out.println("连接建立");
18 }19 }20 });
21 System.out.printf("连接中");
22 countDownLatch.await();
23 //CONNECTED

24 System.out.println(zooKeeper.getState());
2526 //创建持久节点 27 zooKeeper.create("/user","fox".getBytes(),28 ZooDefs.Ids.OPEN_ACL_UNSAFE, CreateMode.PERSISTENT);
2930 }3132 }Zookeeper 主要方法 create(path, data, acl,createMode): 创建一个给定路径的 znode,并在 znode 保存 data[]的 数据,createMode 指定 znode 的类型。
delete(path, version):如果给定 path 上的 znode 的版本和给定的 version 匹配, 删除 znode。
exists(path, watch):判断给定 path 上的 znode 是否存在,并在 znode 设置一个 watch。
getData(path, watch):返回给定 path 上的 znode 数据,并在 znode 设置一个 watch。
setData(path, data, version):如果给定 path 上的 znode 的版本和给定的 version 匹配,设置 znode 数据。
getChildren(path, watch):返回给定 path 上的 znode 的孩子 znode 名字,并在 znode 设置一个 watch。
sync(path):把客户端 session 连接节点和 leader 节点进行同步。
方法特点:
所有获取 znode 数据的 API 都可以设置一个 watch 用来监控 znode 的变化。
所有更新 znode 数据的 API 都有两个版本: 无条件更新版本和条件更新版本。如果 version 为 -1,更新为无条件更新。否则只有给定的 version 和 znode 当前的 version 一样,才会进行更新,这样的更新是条件更新。
所有的方法都有同步和异步两个版本。同步版本的方法发送请求给 ZooKeeper 并等待服务器的响 应。异步版本把请求放入客户端的请求队列,然后马上返回。异步版本通过 callback 来接受来 自服务端的响应。
同步创建节点:
1 @Test2 public void createTest() throws KeeperException, InterruptedException {3 String path = zooKeeper.create(ZK_NODE, "data".getBytes(),ZooDefs.Ids.OPEN_ACL_UNSAFE, CreateMode.PERSISTENT);
4 log.info("created path: {}",path);
5 }

异步创建节点:
1 @Test2 public void createAsycTest() throws InterruptedException {3 zooKeeper.create(ZK_NODE, "data".getBytes(), ZooDefs.Ids.OPEN_ACL_UNSAFE,4 CreateMode.PERSISTENT,5 (rc, path, ctx, name) -> log.info("rc {},path {},ctx {},name{}",rc,path,ctx,name),"context");
6 TimeUnit.SECONDS.sleep(Integer.MAX_VALUE);
7 }修改节点数据 1 @Test2 public void setTest() throws KeeperException, InterruptedException {34 Stat stat = new Stat();
5 byte[] data = zooKeeper.getData(ZK_NODE, false, stat);
6 log.info("修改前: {}",new String(data));
7 zooKeeper.setData(ZK_NODE, "changed!".getBytes(), stat.getVersion());
8 byte[] dataAfter = zooKeeper.getData(ZK_NODE, false, stat);
9 log.info("修改后: {}",new String(dataAfter));
10 }1.2 Curator 开源客户端使用 Curator 是 Netflix 公司开源的一套 ZooKeeper 客户端框架,和 ZkClient 一样它解决了非常底层的细节开发工作,包括连接、重连、反复注册 Watcher 的问题以及 NodeExistsException 异常等。
Curator 是 Apache 基金会的顶级项目之一,Curator 具有更加完善的文档,另外还提供了一套易用性和可读性更强的 Fluent 风格的客户端 API 框架。
Curator 还为 ZooKeeper 客户端框架提供了一些比较普遍的、开箱即用的、分布式开发用的解决方案,例如 Recipe、共享锁服务、 Master 选举机制和分布式计算器等,帮助开发者避免了“重复造轮子”的

无效开发工作。
Guava is to Java that Curator to ZooKeeper 在实际的开发场景中,使用 Curator 客户端就足以应付日常的 ZooKeeper 集群操作的需求。
官网:https://curator.apache.org/引入依赖 Curator 包含了几个包:
curator-framework 是对 ZooKeeper 的底层 API 的一些封装。
curator-client 提供了一些客户端的操作,例如重试策略等。
curator-recipes 封装了一些高级特性,如:Cache 事件监听、选举、分布式锁、分布式计数器、分布式 Barrier 等。
1 <!-- zookeeper client -->2 <dependency>3 <groupId>org.apache.zookeeper</groupId>4 <spanrtifactId>zookeeper</artifactId>5 <version>3.8.0</version>6 </dependency>78 <!--curator-->9 <dependency>10 <groupId>org.apache.curator</groupId>11 <spanrtifactId>curator-recipes</artifactId>12 <version>5.1.0</version>13 <exclusions>14 <exclusion>15 <groupId>org.apache.zookeeper</groupId>16 <spanrtifactId>zookeeper</artifactId>17 </exclusion>18 </exclusions>19 </dependency>创建一个客户端实例

在使用 curator-framework 包操作 ZooKeeper 前,首先要创建一个客户端实例。这是一个 CuratorFramework 类型的对象,有两种方法:
使用工厂类 CuratorFrameworkFactory 的静态 newClient()方法。
1 // 重试策略 2 RetryPolicy retryPolicy = new ExponentialBackoffRetry(1000, 3)
3 //创建客户端实例 4 CuratorFramework client = CuratorFrameworkFactory.newClient(zookeeperConnectionString,retryPolicy);
5 //启动客户端 6 client.start();
使用工厂类 CuratorFrameworkFactory 的静态 builder 构造者方法。
1 RetryPolicy retryPolicy = new ExponentialBackoffRetry(1000, 3);
2 CuratorFramework client = CuratorFrameworkFactory.builder()
3 .connectString("192.168.128.129:2181")
4 .sessionTimeoutMs(5000) // 会话超时时间 5 .connectionTimeoutMs(5000) // 连接超时时间 6 .retryPolicy(retryPolicy)
7 .namespace("base") // 包含隔离名称 8 .build();
9 client.start();
connectionString:服务器地址列表,在指定服务器地址列表的时候可以是一个地址,也可以是多个地址。如果是多个地址,那么每个服务器地址列表用逗号分隔, 如 host1:port1,host2:port2,host3;port3 。
retryPolicy:重试策略,当客户端异常退出或者与服务端失去连接的时候,可以通过设置客户端重新连接 ZooKeeper 服务端。而 Curator 提供了 一次重试、多次重试等不同种类的实现方式。在 Curator 内部,可以通过判断服务器返回的 keeperException 的状态代码来判断是否进行重试处理,如果返回的是 OK 表示一切操作都没有问题,而 SYSTEMERROR 表示系统或服务端错误。
策略名称 描述 ExponentialBackoffRetry 重试一组次数,重试之间的睡眠时间增加 RetryNTimes 重试最大次数

RetryOneTime 只重试一次 RetryUntilElapsed 在给定的时间结束之前重试超时时间:Curator 客户端创建过程中,有两个超时时间的设置。一个是 sessionTimeoutMs 会话超时时间,用来设置该条会话在 ZooKeeper 服务端的失效时间。另一个是 connectionTimeoutMs 客户端创建会话的超时时间,用来限制客户端发起一个会话连接到接收 ZooKeeper 服务端应答的时间。 sessionTimeoutMs 作用在服务端,而 connectionTimeoutMs 作用在客户端。
创建节点创建节点的方式如下面的代码所示,回顾我们之前课程中讲到的内容,描述一个节点要包括节点的类型,即临时节点还是持久节点、节点的数据信息、节点是否是有序节点等属性和性质。
1 @Test2 public void testCreate() throws Exception {3 String path = curatorFramework.create().forPath("/curator-node");
4 curatorFramework.create().withMode(CreateMode.PERSISTENT).forPath("/curatornode","some-data".getBytes())
5 log.info("curator create node :{} successfully.",path);
6 }在 Curator 中,可以使用 create 函数创建数据节点,并通过 withMode 函数指定节点类型(持久化节点,临时节点,顺序节点,临时顺序节点,持久化顺序节点等),默认是持久化节点,之后调用 forPath 函数来指定节点的路径和数据信息。
一次性创建带层级结构的节点 1 @Test2 public void testCreateWithParent() throws Exception {3 String pathWithParent="/node-parent/sub-node-1";
4 String path =curatorFramework.create().creatingParentsIfNeeded().forPath(pathWithParent);
5 log.info("curator create node :{} successfully.",path);
6 }

获取数据 1 @Test2 public void testGetData() throws Exception {3 byte[] bytes = curatorFramework.getData().forPath("/curator-node");
4 log.info("get data from node :{} successfully.",new String(bytes));
5 }更新节点我们通过客户端实例的 setData() 方法更新 ZooKeeper 服务上的数据节点,在 setData 方法的后边,通过 forPath 函数来指定更新的数据节点路径以及要更新的数据。
1 @Test2 public void testSetData() throws Exception {3 curatorFramework.setData().forPath("/curator-node","changed!".getBytes());
4 byte[] bytes = curatorFramework.getData().forPath("/curator-node");
5 log.info("get data from node /curator-node :{} successfully.",new String(bytes));
6 }删除节点 1 @Test2 public void testDelete() throws Exception {

3 String pathWithParent="/node-parent";
4curatorFramework.delete().guaranteed().deletingChildrenIfNeeded().forPath(pathWithParent);
5 }guaranteed:该函数的功能如字面意思一样,主要起到一个保障删除成功的作用,其底层工作方式是:只要该客户端的会话有效,就会在后台持续发起删除请求,直到该数据节点在 ZooKeeper 服务端被删除。
deletingChildrenIfNeeded:指定了该函数后,系统在删除该数据节点的时候会以递归的方式直接删除其子节点,以及子节点的子节点。
异步接口 Curator 引入了 BackgroundCallback 接口,用来处理服务器端返回来的信息,这个处理过程是在异步线程中调用,默认在 EventThread 中调用,也可以自定义线程池。
1 public interface BackgroundCallback2 {3 /**4 * Called when the async background operation completes5 *6 * @param client the client7 * @param event operation result details8 * @throws Exception errors9 */10 public void processResult(CuratorFramework client, CuratorEvent event) throwsException;
11 }如上接口,主要参数为 client 客户端, 和 服务端事件 event。
inBackground 异步处理默认在 EventThread 中执行 1 @Test2 public void test() throws Exception {

3 curatorFramework.getData().inBackground((item1, item2) -> {4 log.info(" background: {}", item2);
5 }).forPath(ZK_NODE);
67 TimeUnit.SECONDS.sleep(Integer.MAX_VALUE);
8 }指定线程池 1 @Test2 public void test() throws Exception {3 ExecutorService executorService = Executors.newSingleThreadExecutor();
45 curatorFramework.getData().inBackground((item1, item2) -> {6 log.info(" background: {}", item2);
7 },executorService).forPath(ZK_NODE);
89 TimeUnit.SECONDS.sleep(Integer.MAX_VALUE);
10 }Curator 监听器 1 /**2 * Receives notifications about errors and background events3 */4 public interface CuratorListener5 {6 /**7 * Called when a background task has completed or a watch has triggered8 *9 * @param client client10 * @param event the event

11 * @throws Exception any errors12 */13 public void eventReceived(CuratorFramework client, CuratorEvent event)
throws Exception;
14 }针对 background 通知和错误通知。使用此监听器之后,调用 inBackground 方法会异步获得监听 Curator Caches:
Curator 引入了 Cache 来实现对 Zookeeper 服务端事件监听,Cache 事件监听可以理解为一个本地缓存视图与远程 Zookeeper 视图的对比过程。 Cache 提供了反复注册的功能。 Cache 分为两类注册类型:节点监听和子节点监听。
node cache:
NodeCache 对某一个节点进行监听 1 public NodeCache(CuratorFramework client,2 String path)
3 Parameters:
4 client - the client5 path - path to cache 可以通过注册监听器来实现,对当前节点数据变化的处理 1 public void addListener(NodeCacheListener listener)
2 Add a change listener3 Parameters:
4 listener - the listener1 @Slf4j

2 public class NodeCacheTest extends AbstractCuratorTest{34 public static final String NODE_CACHE="/node-cache";
56 @Test7 public void testNodeCacheTest() throws Exception {89 createIfNeed(NODE_CACHE);
10 NodeCache nodeCache = new NodeCache(curatorFramework, NODE_CACHE);
11 nodeCache.getListenable().addListener(new NodeCacheListener() {12 @Override13 public void nodeChanged() throws Exception {14 log.info("{} path nodeChanged: ",NODE_CACHE);
15 printNodeData();
16 }17 });
1819 nodeCache.start();
20 }212223 public void printNodeData() throws Exception {24 byte[] bytes = curatorFramework.getData().forPath(NODE_CACHE);
25 log.info("data: {}",new String(bytes));
26 }27 }path cache:
PathChildrenCache 会对子节点进行监听,但是不会对二级子节点进行监听,1 public PathChildrenCache(CuratorFramework client,2 String path,3 boolean cacheData)
4 Parameters:
5 client - the client6 path - path to watch7 cacheData - if true, node contents are cached in addition to the stat

可以通过注册监听器来实现,对当前节点的子节点数据变化的处理 1 public void addListener(PathChildrenCacheListener listener)
2 Add a change listener3 Parameters:
4 listener - the listener1 @Slf4j2 public class PathCacheTest extends AbstractCuratorTest{34 public static final String PATH="/path-cache";
56 @Test7 public void testPathCache() throws Exception {89 createIfNeed(PATH);
10 PathChildrenCache pathChildrenCache = new PathChildrenCache(curatorFramework,PATH, true);
11 pathChildrenCache.getListenable().addListener(new PathChildrenCacheListener() {12 @Override13 public void childEvent(CuratorFramework client, PathChildrenCacheEventevent) throws Exception {14 log.info("event: {}",event);
15 }16 });
1718 // 如果设置为 true 则在首次启动时就会缓存节点内容到 Cache 中 19 pathChildrenCache.start(true);
20 }21 }tree cache:
TreeCache 使用一个内部类 TreeNode 来维护这个一个树结构。并将这个树结构与 ZK 节点进行了映射。所以 TreeCache 可以监听当前节点下所有节点的事件。

1 public TreeCache(CuratorFramework client,2 String path,3 boolean cacheData)
4 Parameters:
5 client - the client6 path - path to watch7 cacheData - if true, node contents are cached in addition to the stat 可以通过注册监听器来实现,对当前节点的子节点,及递归子节点数据变化的处理 1 public void addListener(TreeCacheListener listener)
2 Add a change listener3 Parameters:
4 listener - the listener1 @Slf4j2 public class TreeCacheTest extends AbstractCuratorTest{34 public static final String TREE_CACHE="/tree-path";
56 @Test7 public void testTreeCache() throws Exception {8 createIfNeed(TREE_CACHE);
9 TreeCache treeCache = new TreeCache(curatorFramework, TREE_CACHE);
10 treeCache.getListenable().addListener(new TreeCacheListener() {11 @Override12 public void childEvent(CuratorFramework client, TreeCacheEvent event)
throws Exception {13 log.info(" tree cache: {}",event);
14 }15 });
16 treeCache.start();
17 }

18 }
2. Zookeeper 在分布式命名服务中的实战命名服务是为系统中的资源提供标识能力。 ZooKeeper 的命名服务主要是利用 ZooKeeper 节点的树形分层结构和子节点的顺序维护能力,来为分布式系统中的资源命名。
哪些应用场景需要用到分布式命名服务呢?典型的有:
分布式 API 目录分布式节点命名分布式 ID 生成器 2.1 分布式 API 目录为分布式系统中各种 API 接口服务的名称、链接地址,提供类似 JNDI(Java 命名和目录接口)中的文件系统的功能。借助于 ZooKeeper 的树形分层结构就能提供分布式的 API 调用功能。
著名的 Dubbo 分布式框架就是应用了 ZooKeeper 的分布式的 JNDI 功能。在 Dubbo 中,使用 ZooKeeper 维护的全局服务接口 API 的地址列表。大致的思路为:
服务提供者(Service Provider)在启动的时候,向 ZooKeeper 上的指定节点/dubbo/${serviceName}/providers 写入自己的 API 地址,这个操作就相当于服务的公开。
服务消费者(Consumer)启动的时候,订阅节点/dubbo/{serviceName}/providers 下的服务提供者的 URL 地址,获得所有服务提供者的 API。
2.2 分布式节点的命名一个分布式系统通常会由很多的节点组成,节点的数量不是固定的,而是不断动态变化的。比如说,当业务不断膨胀和流量洪峰到来时,大量的节点可能会动态加入到集群中。而一旦流量洪峰过去了,就需要下线大量的节点。再比如说,由于机器或者网络的原因,一些节点会主动离开集群。
如何为大量的动态节点命名呢?一种简单的办法是可以通过配置文件,手动为每一个节点命名。但是,如果节点数据量太大,或者说变动频繁,手动命名则是不现实的,这就需要用到分布式节点的命名服务。
可用于生成集群节点的编号的方案:
(1)使用数据库的自增 ID 特性,用数据表存储机器的 MAC 地址或者 IP 来维护。
(2)使用 ZooKeeper 持久顺序节点的顺序特性来维护节点的 NodeId 编号。
在第 2 种方案中,集群节点命名服务的基本流程是:

启动节点服务,连接 ZooKeeper,检查命名服务根节点是否存在,如果不存在,就创建系统的根节点。
在根节点下创建一个临时顺序 ZNode 节点,取回 ZNode 的编号把它作为分布式系统中节点的 NODEID。
[[如果临时节点太多,可以根据需要删除临时顺序 ZNode 节点。
2.3 分布式的 ID 生成器在分布式系统中,分布式 ID 生成器的使用场景非常之多:
大量的数据记录,需要分布式 ID。
大量的系统消息,需要分布式 ID。
大量的请求日志,如 restful 的操作记录,需要唯一标识,以便进行后续的用户行为分析和调用链路分析。
分布式节点的命名服务,往往也需要分布式 ID。
。。。
传统的数据库自增主键已经不能满足需求。在分布式系统环境中,迫切需要一种全新的唯一 ID 系统,这种系统需要满足以下需求:
(1)全局唯一:不能出现重复 ID。
(2)高可用:ID 生成系统是基础系统,被许多关键系统调用,一旦宕机,就会造成严重影响。
有哪些分布式的 ID 生成器方案呢?大致如下:
1. Java 的 UUID。
2. 分布式缓存 Redis 生成 ID:利用 Redis 的原子操作 INCR 和 INCRBY,生成全局唯一的 ID。
3. Twitter 的 SnowFlake 算法。
4. ZooKeeper 生成 ID:利用 ZooKeeper 的顺序节点,生成全局唯一的 ID。
5. MongoDb 的 ObjectId:MongoDB 是一个分布式的非结构化 NoSQL 数据库,每插入一条记录会自动生成全局唯一的一个“_id”字段值,它是一个 12 字节的字符串,可以作为分布式系统中全局唯一的 ID。
基于 Zookeeper 实现分布式 ID 生成器在 ZooKeeper 节点的四种类型中,其中有以下两种类型具备自动编号的能力 PERSISTENT_SEQUENTIAL 持久化顺序节点。
EPHEMERAL_SEQUENTIAL 临时顺序节点。
ZooKeeper 的每一个节点都会为它的第一级子节点维护一份顺序编号,会记录每个子节点创建的先后顺序,这个顺序编号是分布式同步的,也是全局唯一的。
可以通过创建 ZooKeeper 的临时顺序节点的方法,生成全局唯一的 ID1 @Slf4j2 public class IDMaker extends CuratorBaseOperations {4 private String createSeqNode(String pathPefix) throws Exception {5 CuratorFramework curatorFramework = getCuratorFramework();
6 //创建一个临时顺序节点 7 String destPath = curatorFramework.create()
8 .creatingParentsIfNeeded()
9 .withMode(CreateMode.EPHEMERAL_SEQUENTIAL)
10 .forPath(pathPefix);
11 return destPath;
12 }1314 public String makeId(String path) throws Exception {15 String str = createSeqNode(path);
16 if(null != str){17 //获取末尾的序号 18 int index = str.lastIndexOf(path);
19 if(index>=0){20 index+=path.length();
21 return index<=str.length() ? str.substring(index):"";
22 }23 }24 return str;
25 }26 }测试 1 @Test2 public void testMarkId() throws Exception {3 IDMaker idMaker = new IDMaker();
4 idMaker.init();
5 String pathPrefix = "/idmarker/id-";
67 for(int i=0;i<5;i++){8 new Thread(()->{9 for (int j=0;j<10;j++){10 String id = null;
11 try {12 id = idMaker.makeId(pathPrefix);

13 log.info("{}线程第{}个创建的 id 为{}",Thread.currentThread().getName(),14 j,id);
15 } catch (Exception e) {16 e.printStackTrace();
17 }18 }19 },"thread"+i).start();
20 }2122 Thread.sleep(Integer.MAX_VALUE);
2324 }测试结果基于 Zookeeper 实现 SnowFlakeID 算法 Twitter(推特)的 SnowFlake 算法是一种著名的分布式服务器用户 ID 生成算法。 SnowFlake 算法所生成的 ID 是一个 64bit 的长整型数字,如图 10-2 所示。这个 64bit 被划分成四个部分,其中后面三个部分分别表示时间戳、工作机器 ID、序列号。
SnowFlakeID 的四个部分,具体介绍如下:
(1)第一位 占用 1 bit,其值始终是 0,没有实际作用。
(2)时间戳 占用 41 bit,精确到毫秒,总共可以容纳约 69 年的时间。
(3)工作机器 id 占用 10 bit,最多可以容纳 1024 个节点。
(4)序列号 占用 12 bit。这个值在同一毫秒同一节点上从 0 开始不断累加,最多可以累加到 4095。
在工作节点达到 1024 顶配的场景下,SnowFlake 算法在同一毫秒最多可以生成的 ID 数量为: 1024 *4096 =4194304,在绝大多数并发场景下都是够用的。
SnowFlake 算法的优点:
生成 ID 时不依赖于数据库,完全在内存生成,高性能和高可用性。
容量大,每秒可生成几百万个 ID。
ID 呈趋势递增,后续插入数据库的索引树时,性能较高。
SnowFlake 算法的缺点:
依赖于系统时钟的一致性,如果某台机器的系统时钟回拨了,有可能造成 ID 冲突,或者 ID 乱序。
在启动之前,如果这台机器的系统时间回拨过,那么有可能出现 ID 重复的危险。

基于 zookeeper 实现雪花算法:
1 public class SnowflakeIdGenerator {23 /**4 * 单例 5 */6 public static SnowflakeIdGenerator instance =7 new SnowflakeIdGenerator();
8910 /**11 * 初始化单例 12 *13 * @param workerId 节点 Id,最大 809114 * @return the 单例 15 */16 public synchronized void init(long workerId) {17 if (workerId > MAX_WORKER_ID) {18 // zk 分配的 workerId 过大 19 throw new IllegalArgumentException("woker Id wrong: " + workerId);
20 }21 instance.workerId = workerId;
22 }2324 private SnowflakeIdGenerator() {2526 }272829 /**30 * 开始使用该算法的时间为: 2017-01-01 00:00:0031 */32 private static final long START_TIME = 1483200000000L;
3334 /**35 * worker id 的 bit 数,最多支持 8192 个节点 36 */37 private static final int WORKER_ID_BITS = 13;

3839 /**40 * 序列号,支持单节点最高每毫秒的最大 ID 数 102441 */42 private final static int SEQUENCE_BITS = 10;
4344 /**45 * 最大的 worker id ,809146 * -1 的补码(二进制全 1)右移 13 位, 然后取反 47 */48 private final static long MAX_WORKER_ID = ~(-1L << WORKER_ID_BITS);
4950 /**51 * 最大的序列号,102352 * -1 的补码(二进制全 1)右移 10 位, 然后取反 53 */54 private final static long MAX_SEQUENCE = ~(-1L << SEQUENCE_BITS);
5556 /**57 * worker 节点编号的移位 58 */59 private final static long WORKER_ID_SHIFT = SEQUENCE_BITS;
6061 /**62 * 时间戳的移位 63 */64 private final static long TIMESTAMP_LEFT_SHIFT = WORKER_ID_BITS + SEQUENCE_BITS;
6566 /**67 * 该项目的 worker 节点 id68 */69 private long workerId;
7071 /**72 * 上次生成 ID 的时间戳 73 */74 private long lastTimestamp = -1L;
7576 /**77 * 当前毫秒生成的序列

78 */79 private long sequence = 0L;
8081 /**82 * Next id long.83 *84 * @return the nextId85 */86 public Long nextId() {87 return generateId();
88 }8990 /**91 * 生成唯一 id 的具体实现 92 */93 private synchronized long generateId() {94 long current = System.currentTimeMillis();
9596 if (current < lastTimestamp) {97 // 如果当前时间小于上一次 ID 生成的时间戳,说明系统时钟回退过,出现问题返回-198 return -1;
99 }100101 if (current == lastTimestamp) {102 // 如果当前生成 id 的时间还是上次的时间,那么对 sequence 序列号进行+1103 sequence = (sequence + 1) & MAX_SEQUENCE;
104105 if (sequence == MAX_SEQUENCE) {106 // 当前毫秒生成的序列数已经大于最大值,那么阻塞到下一个毫秒再获取新的时间戳 107 current = this.nextMs(lastTimestamp);
108 }109 } else {110 // 当前的时间戳已经是下一个毫秒 111 sequence = 0L;
112 }113114 // 更新上次生成 id 的时间戳 115 lastTimestamp = current;
116117 // 进行移位操作生成 int64 的唯一 ID

118119 //时间戳右移动 23 位 120 long time = (current - START_TIME) << TIMESTAMP_LEFT_SHIFT;
121122 //workerId 右移动 10 位 123 long workerId = this.workerId << WORKER_ID_SHIFT;
124125 return time | workerId | sequence;
126 }127128 /**129 * 阻塞到下一个毫秒 130 */131 private long nextMs(long timeStamp) {132 long current = System.currentTimeMillis();
133 while (current <= timeStamp) {134 current = System.currentTimeMillis();
135 }136 return current;
137 }138 }
3. zookeeper 实现分布式队列常见的消息队列有:RabbitMQ,RocketMQ,Kafka 等。 Zookeeper 作为一个分布式的小文件管理系统,同样能实现简单的队列功能。 Zookeeper 不适合大数据量存储,官方并不推荐作为队列使用,但由于实现简单,集群搭建较为便利,因此在一些吞吐量不高的小型系统中还是比较好用的。
3.1 设计思路
1. 创建队列根节点:在 Zookeeper 中创建一个持久节点,用作队列的根节点。所有队列元素的节点将放在这个根节点下。
2. 实现入队操作:当需要将一个元素添加到队列时,可以在队列的根节点下创建一个临时有序节点。节点的数据可以包含队列元素的信息。
3. 实现出队操作:当需要从队列中取出一个元素时,可以执行以下操作:

获取根节点下的所有子节点。
找到具有最小序号的子节点。
获取该节点的数据。
删除该节点。
返回节点的数据。
1 /**2 * 入队 3 * @param data4 * @throws Exception5 */6 public void enqueue(String data) throws Exception {7 // 创建临时有序子节点 8 zk.create(QUEUE_ROOT + "/queue-", data.getBytes(StandardCharsets.UTF_8),9 ZooDefs.Ids.OPEN_ACL_UNSAFE, CreateMode.EPHEMERAL_SEQUENTIAL);
10 }1112 /**13 * 出队 14 * @return15 * @throws Exception16 */17 public String dequeue() throws Exception {18 while (true) {19 List<String> children = zk.getChildren(QUEUE_ROOT, false);
20 if (children.isEmpty()) {21 return null;
22 }2324 Collections.sort(children);
2526 for (String child : children) {27 String childPath = QUEUE_ROOT + "/" + child;
28 try {29 byte[] data = zk.getData(childPath, false, null);
30 zk.delete(childPath, -1);
31 return new String(data, StandardCharsets.UTF_8);
32 } catch (KeeperException.NoNodeException e) {

33 // 节点已被其他消费者删除,尝试下一个节点 34 }35 }36 }37 }3.2 使用 Apache Curator 实现分布式队列 Apache Curator 是一个 ZooKeeper 客户端的封装库,提供了许多高级功能,包括分布式队列。
1 public class CuratorDistributedQueueDemo {2 private static final String QUEUE_ROOT = "/curator_distributed_queue";
34 public static void main(String[] args) throws Exception {5 CuratorFramework client = CuratorFrameworkFactory.newClient("localhost:2181",6 new ExponentialBackoffRetry(1000, 3));
7 client.start();
89 // 定义队列序列化和反序列化 10 QueueSerializer<String> serializer = new QueueSerializer<String>() {11 @Override12 public byte[] serialize(String item) {13 return item.getBytes();
14 }1516 @Override17 public String deserialize(byte[] bytes) {18 return new String(bytes);
19 }20 };
2122 // 定义队列消费者 23 QueueConsumer<String> consumer = new QueueConsumer<String>() {24 @Override25 public void consumeMessage(String message) throws Exception {26 System.out.println("消费消息: " + message);
27 }

2829 @Override30 public void stateChanged(CuratorFramework curatorFramework, ConnectionStateconnectionState) {3132 }33 };
3435 // 创建分布式队列 36 DistributedQueue<String> queue = QueueBuilder.builder(client, consumer,serializer, QUEUE_ROOT)
37 .buildQueue();
38 queue.start();
3940 // 生产消息 41 for (int i = 0; i < 5; i++) {42 String message = "Task-" + i;
43 System.out.println("生产消息: " + message);
44 queue.put(message);
45 Thread.sleep(1000);
46 }4748 Thread.sleep(10000);
49 queue.close();
50 client.close();
51 }52 }533.3 注意事项使用 Curator 的 DistributedQueue 时,默认情况下不使用锁。当调用 QueueBuilder 的 lockPath()方法并指定一个锁节点路径时,才会启用锁。如果不指定锁节点路径,那么队列操作可能会受到并发问题的影响。
在创建分布式队列时,指定一个锁节点路径可以帮助确保队列操作的原子性和顺序性。分布式环境中,多个消费者可能同时尝试消费队列中的消息。如果不使用锁来同步这些操作,可能会导致消息被多次处理或者处理顺序出现混乱。当然,并非所有场景都需要指定锁节点路径。如果您的应用场景允

许消息被多次处理,或者处理顺序不是关键问题,那么可以不使用锁。这样可以提高队列操作的性能,因为不再需要等待获取锁。
1 // 创建分布式队列 2 QueueBuilder<String> builder = QueueBuilder.builder(client, consumer, serializer,"/order");
3 //指定了一个锁节点路径/orderlock,用于实现分布式锁,以保证队列操作的原子性和顺序性。
4 queue = builder.lockPath("/orderlock").buildQueue();
5 //启动队列,这时队列开始监听 ZooKeeper 中/order 节点下的消息。
6 queue.start();
