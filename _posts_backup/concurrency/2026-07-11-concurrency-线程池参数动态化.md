---
title: "线程池参数动态化"
description: "【有道云笔记】线程池参数动态化 https://note.youdao.com/s/FBkx8LOR 线程池在业务中的实践 业务背景 在当今的互联网业界,为了最大程度利用CPU的多核性能,并行运算的能力是不可或缺的。通过线程 池管理线程获取并发性是一个非常基础的操作,让我们来看两个典型的使用线程池获取并发性的场 景。 场景1:快速响应用户请求 描述:用户发起的实时请求,服务追求响应时间。比如..."
author: hsc
date: 2026-07-11 00:00:00 +0800
categories: ['Java 后端', '并发编程']
tags: ['并发编程', '多线程', 'JUC', 'AQS', '线程池']
toc: true
---

> 本文整理自《三、并发编程专题》课程笔记，共 11 页。

【有道云笔记】线程池参数动态化
https://note.youdao.com/s/FBkx8LOR
线程池在业务中的实践
业务背景
在当今的互联网业界,为了最大程度利用CPU的多核性能,并行运算的能力是不可或缺的。通过线程
池管理线程获取并发性是一个非常基础的操作,让我们来看两个典型的使用线程池获取并发性的场
景。
场景1:快速响应用户请求
描述:用户发起的实时请求,服务追求响应时间。比如说用户要查看一个商品的信息,那么我们需要
将商品维度的一系列信息如商品的价格、优惠、库存、图片等等聚合起来,展示给用户。
分析:从用户体验角度看,这个结果响应的越快越好,如果一个页面半天都刷不出,用户可能就放弃
查看这个商品了。而面向用户的功能聚合通常非常复杂,伴随着调用与调用之间的级联、多级级联等
情况,业务开发同学往往会选择使用线程池这种简单的方式,将调用封装成任务并行的执行,缩短总
体响应时间。另外,使用线程池也是有考量的,这种场景最重要的就是获取最大的响应速度去满足用
户,所以应该不设置队列去缓冲并发任务,调高corePoolSize和maxPoolSize去尽可能创造多的线程快
速执行任务。
场景2:快速处理批量任务
描述:离线的大量计算任务,需要快速执行。比如说,统计某个报表,需要计算出全国各个门店中有
哪些商品有某种属性,用于后续营销策略的分析,那么我们需要查询全国所有门店中的所有商品,并
且记录具有某属性的商品,然后快速生成报表。

分析:这种场景需要执行大量的任务,我们也会希望任务执行的越快越好。这种情况下,也应该使用
多线程策略,并行计算。但与响应速度优先的场景区别在于,这类场景任务量巨大,并不需要瞬时的
完成,而是关注如何使用有限的资源,尽可能在单位时间内处理更多的任务,也就是吞吐量优先的问
题。所以应该设置队列去缓冲并发任务,调整合适的corePoolSize去设置处理任务的线程数。在这
里,设置的线程数过多可能还会引发线程上下文切换频繁的问题,也会降低处理任务的速度,降低吞
吐量。
实际问题及方案思考
线程池使用面临的核心的问题在于:线程池的参数并不好配置。一方面线程池的运行机制不是很好理
解,配置合理需要强依赖开发人员的个人经验和知识;另一方面,线程池执行的情况和任务类型相关
性较大,IO密集型和CPU密集型的任务运行起来的情况差异非常大,这导致业界并没有一些成熟的经
验策略帮助开发人员参考。
关于线程池配置不合理引发的故障,下面举一些例子:
Case1:XX页面展示接口大量调用降级:
事故描述:XX页面展示接口产生大量调用降级,数量级在几十到上百。
事故原因:该服务展示接口内部逻辑使用线程池做并行计算,由于没有预估好调用的流量,导致最大
线程数设置偏小,大量抛出RejectedExecutionException,触发接口降级条件,示意图如下:

Case2:XX业务服务不可用S2级故障
事故描述:XX业务提供的服务执行时间过长,作为上游服务整体超时,大量下游服务调用失败。
事故原因:该服务处理请求内部逻辑使用线程池做资源隔离,由于队列设置过长,最大线程数设置失
效,导致请求数量增加时,大量任务堆积在队列中,任务执行时间过长,最终导致下游服务的大量调
用超时失败。示意图如下:
业务中要使用线程池,而使用不当又会导致故障,那么我们怎样才能更好地使用线程池呢?
线程池参数动态化
在日常项目开发中,我们通常会使用线程池来处理一些并发场景,来提高任务处理的效率。但是在使
用过程中,无法准确地设置线程池参数,只能在运行过程中,不断去调整参数,然后重启服务。
那如何实现在不重启服务的前提下,动态调整线程池参数呢?

线程池可调整的参数
线程池构造参数有8个,但是最核心的是3个:corePoolSize、maximumPoolSize,workQueue,它们
最大程度地决定了线程池的任务分配和线程分配策略。考虑到在实际应用中我们获取并发性的场景主
要是两种:(1)并行执行子任务,提高响应速度。这种情况下,应该使用同步队列,没有什么任务应
该被缓存下来,而是应该立即执行。(2)并行执行大批次任务,提升吞吐量。这种情况下,应该使用
有界队列,使用队列去缓冲大批量的任务,队列容量必须声明,防止任务无限制堆积。所以线程池只
需要提供这三个关键参数的配置,并且提供两种队列的选择,就可以满足绝大多数的业务需求。
实现思路
JDK原生线程池ThreadPoolExecutor提供了如下几个public的setter方法,如下图所示:
JDK允许线程池使用方通过ThreadPoolExecutor的实例来动态设置线程池的核心策略,以
setCorePoolSize为方法例,在运行期线程池使用方调用此方法设置corePoolSize之后,线程池会直接
覆盖原来的corePoolSize值,并且基于当前值和原始值的比较结果采取不同的处理策略。对于当前值
小于当前工作线程数的情况,说明有多余的worker线程,此时会向当前idle的worker线程发起中断请求
以实现回收,多余的worker在下次idel的时候也会被回收;对于当前值大于原始值且当前队列中有待执
行任务,则线程池会创建新的worker线程来执行队列任务,setCorePoolSize具体流程如下:

示例代码

1 public class DynamicThreadPool {
2 private ThreadPoolExecutor executor;
3
4 public DynamicThreadPool(int corePoolSize, int maximumPoolSize, long keepAliveTime,
TimeUnit unit, BlockingQueue<Runnable> workQueue) {
5 this.executor = new ThreadPoolExecutor(corePoolSize, maximumPoolSize,
keepAliveTime, unit, workQueue);
6 //executor.allowCoreThreadTimeOut(true);
7 }
8
9 public void adjustThreadPool(int newCorePoolSize, int newMaximumPoolSize) {
10 this.executor.setCorePoolSize(newCorePoolSize);
11 this.executor.setMaximumPoolSize(newMaximumPoolSize);
12 }
13
14 public void submitTask(Runnable task) {
15 this.executor.execute(task);
16 }
17
18 public void print(){
19 System.out.println("核心线程数:" + executor.getCorePoolSize()
20 + " " +"最大线程数:" + executor.getMaximumPoolSize()
21 +" " + "活跃线程数:" + executor.getActiveCount());
22 }
23
24 public void shutdown() {
25 this.executor.shutdown();
26 }
27
28 public static void main(String[] args) throws InterruptedException {
29 BlockingQueue<Runnable> workQueue = new LinkedBlockingQueue<>(20);
30 DynamicThreadPool dynamicThreadPool = new DynamicThreadPool(10, 10, 10,
TimeUnit.SECONDS, workQueue);
31
32 // 提交任务给线程池
33 for (int i = 0; i < 30; i++) {
34 dynamicThreadPool.submitTask(() -> {
35 log.info(Thread.currentThread().getName() + "开始执行任务");
36 try {

37 Thread.sleep(10000);
38 //log.info(Thread.currentThread().getName() + "任务执行完成");
39 } catch (InterruptedException e) {
40 e.printStackTrace();
41 }
42 });
43 }
44
45 Thread.sleep(1000);
46 System.out.println("======修改前=======");
47 dynamicThreadPool.print();
48
49 // 动态调整线程池参数
50 dynamicThreadPool.adjustThreadPool(5, 8);
51
52 System.out.println("======修改后=======");
53 dynamicThreadPool.print();
54
55
56 Thread.sleep(10000);
57 dynamicThreadPool.print();
58
59 // // 关闭线程池
60 // dynamicThreadPool.shutdown();
61 }
62 }
实现方案
基于Nacos配置中心动态调整线程池参数
我们可以借助Nacos的Listener,在Bean初始化的时候,开启Nacos配置变更的监听,在监听逻辑里面
更新线程池参数。

1 nacosConfigManager.getConfigService().addListener("threadPool.yml",
nacosConfigProperties.getGroup(),
2 new Listener() {
3 @Override
4 public Executor getExecutor() {
5 return null;
6 }
7 @Override
8 public void receiveConfigInfo(String configInfo) {
9
10 }
11 });
核心代码

1 @Configuration
2 @Data
3 public class MyDynamicThreadPool implements InitializingBean {
4
5 @Value("${threadPool.corePoolSize}")
6 private int corePoolSize;
7 @Value("${threadPool.maxPoolSize}")
8 private int maxPoolSize;
9 @Value("${threadPool.queueCapacity}")
10 private int queueCapacity;
11 @Value("${threadPool.keepAliveSeconds}")
12 private int keepAliveSeconds;
13
14 private static ThreadPoolTaskExecutor threadPoolTaskExecutor;
15
16
17 @Autowired
18 private NacosConfigManager nacosConfigManager;
19
20 @Autowired
21 private NacosConfigProperties nacosConfigProperties;
22
23
24 @Override
25 public void afterPropertiesSet() throws Exception {
26 threadPoolTaskExecutor = new ThreadPoolTaskExecutor();
27 threadPoolTaskExecutor.setCorePoolSize(corePoolSize);
28 threadPoolTaskExecutor.setMaxPoolSize(maxPoolSize);
29 threadPoolTaskExecutor.setQueueCapacity(queueCapacity);
30 threadPoolTaskExecutor.setKeepAliveSeconds(keepAliveSeconds);
31 threadPoolTaskExecutor.setThreadNamePrefix( "Fox--");
32 threadPoolTaskExecutor.setRejectedExecutionHandler(
33 new RejectedExecutionHandler() {
34 @Override
35 public void rejectedExecution(Runnable r, ThreadPoolExecutor
executor) {
36 System.out.println("队列已满,丢弃任务");
37 }

38 });
39 threadPoolTaskExecutor.initialize();
40 nacosConfigManager.getConfigService().addListener("threadPool.yml",
nacosConfigProperties.getGroup(),
41 new Listener() {
42 @Override
43 public Executor getExecutor() {
44 return null;
45 }
46 @Override
47 public void receiveConfigInfo(String configInfo) {
48 System.out.println("动态修改前-->");
49 print();
50 Yaml yaml = new Yaml();
51 InputStream inputStream = new
ByteArrayInputStream(configInfo.getBytes());
52 Map<String, Object> dataMap = yaml.load(inputStream);
53 // 将Map转换为JSONObject
54 JSONObject pool = new
JSONObject(dataMap).getJSONObject("threadPool");
55
threadPoolTaskExecutor.setCorePoolSize(pool.getInteger("corePoolSize"));
56
threadPoolTaskExecutor.setMaxPoolSize(pool.getInteger("maxPoolSize"));
57
threadPoolTaskExecutor.setQueueCapacity(pool.getInteger("keepAliveSeconds"));
58
threadPoolTaskExecutor.setQueueCapacity(pool.getInteger("queueCapacity"));
59 System.out.println("动态修改后-->");
60 print();
61 }
62 });
63
64 }
65 //执行任务
66 public void execute(Runnable runnable){
67 threadPoolTaskExecutor.execute(runnable);
68 }
69
70 public void print(){
71 System.out.println("核心线程数:" +
threadPoolTaskExecutor.getThreadPoolExecutor().getCorePoolSize()

72 + " " +"最大线程数:" +
threadPoolTaskExecutor.getThreadPoolExecutor().getMaximumPoolSize()
73 +" " + "阻塞队列数:" +
threadPoolTaskExecutor.getThreadPoolExecutor().getQueue().size()
74 + "/" + queueCapacity
75 +" " + "活跃线程数:" +
threadPoolTaskExecutor.getThreadPoolExecutor().getActiveCount());
76 }
77 }
使用DynamicTp——基于配置中心的轻量级动态可监控线程池
DynamicTp 是一个基于配置中心实现的轻量级动态线程池管理工具,主要功能可以总结为动态调参、
通知报警、运行监控、三方包线程池管理等几大类。
官网地址:https://dynamictp.cn/
