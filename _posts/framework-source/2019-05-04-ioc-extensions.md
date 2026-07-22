---
title: "-Spring IOC容器扩展点全景：深入探索与实践演练-徐庶"
description: "Spring IOC容器扩展点全景:深入探索与实践演练 SpringIoc之BeanDefinition注册过程的扩展点详解 动态注册BeanDefinition有几种方式? 好处: 可以在运行时动态决定bean的属性、类型、构造函数等定义信息 比如有些bean在定义期间无法确定是否注册bean,需要在运行时动态决定; 比如有些bean是接口—接口不能实例化,需要在运行时动态决定他的类型; ..."
author: hsc
date: 2019-05-04 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis', '源码分析', '框架']
toc: true
---

> 本文整理自《二、框架源码专题》课程笔记，共 32 页。

Spring IOC容器扩展点全景:深入探索与实践演练
SpringIoc之BeanDefinition注册过程的扩展点详解
动态注册BeanDefinition有几种方式?
好处: 可以在运行时动态决定bean的属性、类型、构造函数等定义信息
比如有些bean在定义期间无法确定是否注册bean,需要在运行时动态决定;
比如有些bean是接口—接口不能实例化,需要在运行时动态决定他的类型;
比如想让bean的顺序放在最后;
...
1. BeanDefinitionRegistryPostProcessor
2. BeanFactoryPostProcessor

1 package com.xushu.extensions.beandefinition;
2
3 import org.springframework.beans.factory.config.BeanDefinition;
4 import org.springframework.beans.factory.config.ConfigurableListableBeanFactory;
5 import org.springframework.beans.factory.support.BeanDefinitionBuilder;
6 import org.springframework.beans.factory.support.BeanDefinitionRegistry;
7 import org.springframework.beans.factory.support.BeanDefinitionRegistryPostProcessor;
8 import org.springframework.stereotype.Component;
9
10 @Component
11 public class MyBeanDefinitionRegistryPostProcessor implements
BeanDefinitionRegistryPostProcessor {
12
13 @Override
14 public void postProcessBeanDefinitionRegistry(BeanDefinitionRegistry registry) {
15 // 动态注册beanDefinition
16 BeanDefinitionBuilder builder =
BeanDefinitionBuilder.genericBeanDefinition(XushuService.class);
17 BeanDefinition beanDefinition = builder.getBeanDefinition();
18 // 动态注入属性
19 beanDefinition.getPropertyValues().add("age",18);
20 // 动态设置定义信息
21 beanDefinition.setLazyInit(true);
22 //beanDefinition.setScope();
23 //beanDefinition.setInitMethodName();
24 //...
25
26 // 动态设置构造函数
27 //beanDefinition.getConstructorArgumentValues().addIndexedArgumentValue(0,..);
28
29
30 registry.registerBeanDefinition("xushuService3", beanDefinition);
31 }
32
33 @Override
34 public void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
35
36 }

37
38 }
3. @import—ImportBeanDefinitionRegistrar
注意: 1. 必须要结合@Import ,单独配置为bean不会起作用!
2.ImportBeanDefinitionRegistrar不是一个bean, 没有bean的生命周期, 没有依赖注入功能。
但是! 它有一个优势, 注意它有一个importingClassMetadata参数, 这个参数可以获取@Import注解
所在类的其他注解信息, 比如@MapperScan根据包创建beandefinition 。 这是
BeanDefinitionRegistryPostProcessor不具备的!
1 package com.xushu.extensions.beandefinition;
2
3 import org.springframework.beans.factory.support.BeanDefinitionRegistry;
4 import org.springframework.context.annotation.ImportBeanDefinitionRegistrar;
5 import org.springframework.core.type.AnnotationMetadata;
6
7 public class MyImportBeanDefinitionRegistrar implements ImportBeanDefinitionRegistrar {
8
9 @Override
10 public void registerBeanDefinitions(AnnotationMetadata importingClassMetadata,
BeanDefinitionRegistry registry) {
11
12
13 }
14 }
15
SpringIoc之Bean创建过程的扩展点详解
1. BeanPostProcessor
更多是为了Spring自己得扩展性, 为以后得版本升级留出更多的扩展余地。
也可以提供给程序员进行扩展,不同阶段的作用不同,实际根据情况进行选择。

不同阶段可以做不同的事情:
2. Aware
基于底层扩展很少会用@Autowired来注入Spring组件, 因为顺序问题, 基本都会通过Aware获取组件

3. 生命周期回调
1. 如果通过aware获取组件, 那么肯定也会用初始化的回调方式进行初始化, 而不是用构造函数
2. 用构造函数初始化, 由于构造函数在实例化这步, 获取不到像aware这些组件。
3. 构造函数不确定性, 所以作为初始化不合适

4. SpringIoc之容器加载完毕的扩展点详解
SmartInitializingSingleton.
它其实是初始化回调的一个补充,可以再所有Bean创建完后初始化.比如想对一批bean一起同时做一些
动作。

1 /**
2 * 在所有单例bean创建完后调用, 做初始化工作
3 * 比如需要依赖创建完后的bean 进行一些初始化工作
4 *
5 */
6
7
8 // 1.有别于初始化回调, 他会在所有单例bean创建完后调用
9 // 2.有别与refreshedEvent事件监听,依赖小
10 // 3.仅仅BeanFactory就有可以完成调用的扩展点
11 @Component
12 public class MySmartInitializingSingleton implements SmartInitializingSingleton {
13 @Override
14 public void afterSingletonsInstantiated() {
15 System.out.println("所有bean创建完后调用..");
16 }
17 }
18
SmartLifecycle
控制一个组件的生命周期 ,比如定时器组件\资源预热\缓存预热
* 容器启动完: 定时任务启动 / 缓存预热
* 容器关闭: 定时任务停止 / 缓存清空
所有同Spring容器同开启/关闭 的服务可以基于SmartLifecycle完成, 就不需要自己单独管理开启关闭
了

1 package com.xushu.extensions.created;
2
3 import org.springframework.context.SmartLifecycle;
4 import org.springframework.stereotype.Component;
5
6 /**
7 * 控制一个组件的生命周期 ,比如定时器组件\资源预热\缓存预热
8 * 容器启动完: 定时任务启动
9 * 容器关闭: 定时任务停止
10 */
11 @Component
12 public class MyLifecycle implements SmartLifecycle {
13 boolean isRunning;
14 @Override
15 public void start() {
16 isRunning=true;
17 System.out.println("容器加载完毕,组件启动!");
18 }
19
20 @Override
21 public void stop() {
22 isRunning=false;
23 System.out.println("容器关闭,组件停止!");
24 }
25
26 // isRunning=false 调用 start isRunning=true 调用stop
27 @Override
28 public boolean isRunning() {
29 System.out.println("组件是否运行判断");
30 return isRunning;
31 }
32
33 @Override
34 public boolean isAutoStartup() {
35 return SmartLifecycle.super.isAutoStartup();
36 }
37 }

38
ContextRefreshedEvent
基于事件
1 @Component
2 public class ContextRefreshedEventListener{ //implements
ApplicationListener<ContextRefreshedEvent> {
3
4 //@Async
5 @EventListener(ContextRefreshedEvent.class)
6 public void onApplicationEvent(ContextRefreshedEvent event) {
7 System.out.println("______________\n容器加载完毕\n———————");
8
9 }
10
11 }
12
利用扩展点实现动态加载线程池小案例演练
此案例根据美团动态线程池dynamic-tp开源项目提取关键扩展点讲解 gitee地址:yanhom/dynamic-tp
在开发中,关于线程池会遇到:
由于不同服务器的资源、不同时刻的请求量不一样, 代码中创建了一个 ThreadPoolExecutor,但是不知道那几
个核心参数设置多少比较合适
参数设置好后,上线发现需要调整,改代码重启服务非常麻烦。
线程池相对于开发人员来说是个黑箱,运行情况在出现问题 前很难被感知。

1 public static void main(String[] args) {
2 // 创建ThreadPoolExecutor对象
3 ThreadPoolExecutor executor = new ThreadPoolExecutor(
4 corePoolSize,
5 maximumPoolSize,
6 keepAliveTime,
7 TimeUnit.SECONDS,
8 workQueue,
9 handler
10 );
11 }
12 /*
13 corePoolSize:核心线程数,表示线程池中始终保持活动状态的线程数。
14 maximumPoolSize:最大线程数,表示线程池中可以同时执行的最大线程数。
15 keepAliveTime:空闲线程销毁的时间,表示当线程池中的线程数超过核心线程数时,多余的空闲线程在被
销毁之前等待的最长时间。
16 TimeUnit:时间单位,用于指定keepAliveTime的单位。
17 workQueue:任务队列,用于存储待执行的任务。
18 handler:拒绝策略,用于处理无法执行的任务。
19 */
**实现思路**:
利用SpringBoot的配置文件(后续还可以利用配置中心)
1. 根据配置的参数, 动态创建线程池
2. 将动态线程池bean交给Spring容器管理
3. 后续使用线程池可以从Spring容器中获取动态线程池bean使用
4. 后续修改可以直接对动态线程池bean进行修改
5. 最好还能监控如果达到阈值进行(发邮件)警告。
需求1: 根据配置动态加载信息并且创建

1 spring:
2 dtp:
3 executors:
4 # 线程池1
5 - poolName: dtpExecutor1
6 corePoolSize: 5
7 maximumPoolSize: 10
8 #...其他参数
9
10 # 线程池2
11 - poolName: dtpExecutor2
12 corePoolSize: 2
13 maximumPoolSize: 15
14 #...其他参数
15
16 #线程池3\4\5
毫无疑问要一个Pojo类接收这些配置
1
2 @Data
3 public class DtpProperties {
4
5 private List<ThreadPoolProperties> executors;
6 }
7

1
2 @Data
3 public class ThreadPoolProperties {
4 /**
5 * 标识每个线程池的唯一名字
6 */
7 private String poolName;
8 private String poolType = "common";
9
10 /**
11 * 是否为守护线程
12 */
13 private boolean isDaemon = false;
14
15 /**
16 * 以下都是核心参数
17 */
18 private int corePoolSize = 1;
19 private int maximumPoolSize = 1;
20 private long keepAliveTime;
21 private TimeUnit timeUnit = TimeUnit.SECONDS;
22 private String queueType = "arrayBlockingQueue";
23 private int queueSize = 5;
24 private String threadFactoryPrefix = "-td-";
25 private String RejectedExecutionHandler;
26 }
27
1.如何获取配置?
1、@Value
通过@Value单个获取;一个个设置,太麻烦

1 @Value("${com.tuling.bean.bean-class}")
2 private Class<?> beanClass;
3
4 // Todo... 一个个获取
2、@ConfigurationProperties
通过@ConfigurationProperties(prefix = "com.tuling")可以批量获取,比较方便
3、EnvironmentAware——选它!
Spring提供很多XXXAware接口、其中EnvironmentAware接口就可以通过其提供的
Environment动态获取。
第一步:实现EnvironmentAware接口
1 @Component
2 public class TestEnvironmentAware implements EnvironmentAware {
3 @Override
4 public void setEnvironment(Environment environment) {
5 // Todo 绑定配置信息...
6 }
7 }
第二步:获取/绑定配置,提供两种方式:
a. 获取方式一:单个获取
1 public void setEnvironment(Environment environment) {
2 environment.getProperty("com.tuling.bean.bean-class");
3 // ToDo: 一个个获取更多配置信息..
4 }
a. 获取方式二:通过Binder绑定到properties对象

1 @Override
2 public void setEnvironment(Environment environment) {
3 BindResult<BeanProperties> bindResult =
Binder.get(environment).bind("com.tuling.bean", BeanProperties.class);
4 BeanProperties beanProperties= bindResult.get();
5 }
@Value 和@ConfigurationProperties 注解方式获取配置为什么不可以?Why?~
因为顺序原因!这里就要清楚:
@Value 和@ConfigurationProperties注解依赖BeanPostProcessor解析,要调用BeanPostProcessor
就要先注册,而BeanPostProcessor的注册是在BeanDefinition的注册之后的。
所以在注册BeanDefinition时是获取不到注解绑定的配置信息的:
2. 动态创建Bean的几种方式:
注意!我们需要的是动态!动态!!是在运行过程中经过逻辑代码创建Bean, 不是通过配置
<bean>、 @Component这种配置方式这种方式不能自由控制业务逻辑。
想要动态创建Bean先了解Bean创建的大概过程:
如果想动态注册Bean,可以通过先动态注册BeanDefintion即可,Spring提供了动态注册BeanDefinition
的接口:
1、ImportBeanDefinitionRegistrar

第一步:创建实现ImportBeanDefinitionRegistrar接口的类, 演示了一个DeanDefintion的注
册
1 public class MyImportBeanDefinitionRegistrar implements ImportBeanDefinitionRegistrar {
2 @Override
3 public void registerBeanDefinitions(AnnotationMetadata importingClassMetadata,
BeanDefinitionRegistry registry, BeanNameGenerator importBeanNameGenerator) {
4 GenericBeanDefinition beandefinition=new GenericBeanDefinition();
5 beandefinition.setBeanClassName("com.tuling.beans.TestComponent");
6 beandefinition.getPropertyValues().add("id",1);
7 beandefinition.getPropertyValues().add("name","图灵");
8
9 registry.registerBeanDefinition("testComponent",beandefinition);
10 }
11 }
第二步:结合@Import让它生效
1 @Import(MyImportBeanDefinitionRegistrar.class)
2、BeanDefinitionRegistryPostProcessor ——选它!
创建实现BeanDefinitionRegistryPostProcessor接口的类, 演示一个DeanDefintion的注册

1 public class MyBeanDefinitionRegistryPostProcessor implements
BeanDefinitionRegistryPostProcessor {
2 @Override
3 public void postProcessBeanDefinitionRegistry(BeanDefinitionRegistry registry)
throws BeansException {
4 GenericBeanDefinition beandefinition=new GenericBeanDefinition();
5 beandefinition.setBeanClassName("com.tuling.beans.TestComponent");
6 beandefinition.getPropertyValues().add("id",1);
7 beandefinition.getPropertyValues().add("name","图灵");
8
9 registry.registerBeanDefinition("testComponent",beandefinition);
10
11 }
12 }
3、通过BeanFactoryPostProcessor
BeanFactoryPostProcessor也可以,但是没有BeanDefinitionRegistryPostProcessor这么明确的责任是
用来注册的,及其他方式就不演示了。
ImportBeanDefinitionRegistrar为什么不行?
ImportBeanDefinitionRegistrar不是一个bean, 没有bean的生命周期, 没有依赖注入功能。
但是!其实ImportBeanDefinitionRegistrar在这个场景也行,啊????? , 不是说不会调用
EnvironmentAware吗
" 是的,这里比较特殊"
在解析@Import的ImportBeanDefinitionRegistrar时候, 会调用BeanClassLoaderAware、
BeanFactoryAwar、EnvironmentAware、ResourceLoaderAware
有兴趣可以看源码:
org.springframework.context.annotation.ParserStrategyUtils#invokeAwareMethods

最终实现:
ImportBeanDefinitionRegistrar+EnvironmentAware
BeanDefinitionRegistryPostProcessor+EnvironmentAware
都行

1
2
3 @Slf4j
4 public class DtpBeanDefinitionRegistrar implements ImportBeanDefinitionRegistrar,
EnvironmentAware {
5 private Environment environment;
6
7 @Override
8 public void registerBeanDefinitions(AnnotationMetadata importingClassMetadata,
BeanDefinitionRegistry registry) {
9
10 //绑定资源
11 BindResult<DtpProperties> bindResult =
Binder.get(environment).bind("spring.dtp", DtpProperties.class);
12 DtpProperties dtpProperties = bindResult.get();
13
14 List<ThreadPoolProperties> executors = dtpProperties.getExecutors();
15 if (Objects.isNull(executors)) {
16 log.info("未检测本地到配置文件线程池");
17 return;
18 }
19
20 // 把动态线程池对象交给Spring管理
21 for (ThreadPoolProperties properties : executors) {
22 BeanDefinitionBuilder builder =
BeanDefinitionBuilder.genericBeanDefinition(DtpThreadPoolExecutor.class);
23 builder.addConstructorArgValue(properties);
24 registry.registerBeanDefinition(properties.getPoolName(),
builder.getBeanDefinition());
25 }
26
27 }
28
29
30 @Override
31 public void setEnvironment(Environment environment) {
32 this.environment = environment;
33 }
34 }

35
36
37
1
2 // 单独声明动态线程池类
3 // 把动态线程池和 内置线程池区分开 方便从容器中获取
4 public class DtpThreadPoolExecutor extends ThreadPoolExecutor{
5
6 public DtpThreadPoolExecutor(ThreadPoolProperties executorProp) {
7 super(
8 executorProp.getCorePoolSize(),
9 executorProp.getMaximumPoolSize(),
10 executorProp.getKeepAliveTime(),
11 executorProp.getTimeUnit(),
12 // 这里的参数我随意写一下, 实际中可以根据配置动态创建
13 new ArrayBlockingQueue<>(executorProp.getQueueSize())
14 );
15 }
16
17
18 public DtpThreadPoolExecutor(int corePoolSize, int maximumPoolSize, long
keepAliveTime, TimeUnit unit, BlockingQueue<Runnable> workQueue) {
19 super(corePoolSize, maximumPoolSize, keepAliveTime, unit, workQueue);
20 }
21 }
22
需求2:
1. 后续使用线程池可以从Spring容器中获取动态线程池bean使用
2. 后续修改可以直接对动态线程池bean进行修改
3. 想实现一个线程池工具类, 快速管理动态线程池

现在提供一个线程池工具类,想把DtpThreadPoolExecutor交给它管理, 在哪个扩展点调用
DtpRegistry.registry方法?

1 public class DtpRegistry {
2 /**
3 * 储存线程池
4 */
5 private static final Map<String, ThreadPoolExecutor> EXECUTOR_MAP = new
ConcurrentHashMap<>();
6
7 /**
8 * 获取线程池
9 * @param executorName 线程池名字
10 */
11 public static ThreadPoolExecutor getExecutor(String executorName) {
12 return EXECUTOR_MAP.get(executorName);
13 }
14
15
16 public static Collection<String> getAllExecutorNames(){
17 return EXECUTOR_MAP.keySet();
18 }
19
20
21 public static Collection<ThreadPoolExecutor> getAllDtpExecutor(){
22 return EXECUTOR_MAP.values();
23 }
24 /**
25 * 线程池注册
26 * @param executorName 线程池名字
27 */
28 public static void registry(String executorName, ThreadPoolExecutor executor) {
29 //注册
30 EXECUTOR_MAP.put(executorName, executor);
31 }
32
33
34 /**
35 * 刷新线程池参数
36 * @param executorName 线程池名字
37 * @param properties 线程池参数

38 */
39 public static void refresh(String executorName, ThreadPoolProperties properties) {
40 ThreadPoolExecutor executor = EXECUTOR_MAP.get(executorName);
41 //刷新参数
42 //.......
43
44 //executor.setCorePoolSize(properties.xxx);
45 //executor.setMaximumPoolSize(properties.xxx);
46
47 }
48 }
49
实现:
1.BeanPostProcessor.postProcessAfterInitialization可以
2.SmartInitializingSingleton也OK
1 public class DtpBeanPostProcessor implements BeanPostProcessor {
2 private DefaultListableBeanFactory beanFactory;
3
4 @Override
5 public Object postProcessAfterInitialization(Object bean, String beanName) throws
BeansException {
6 if (bean instanceof DtpThreadPoolExecutor) {
7 //直接纳入管理
8 DtpRegistry.registry(beanName, (ThreadPoolExecutor) bean);
9 }
10 return bean;
11 }
12 }
动态修改线程池参数
下次变了, 我们调用DtpRegistry.refresh即可。 可以通过前端请求改变,

1
2 @RestController
3 @RequestMapping("/dtp")
4 public class DtpController {
5
6 @PostMapping("/refresh")
7 public String refresh(ThreadPoolProperties properties){
8 DtpRegistry.refresh(properties.getPoolName(),properties);
9 return "success!";
10 }
11
12 }
13
当然正确的做法应该通过集成配置中心(比如Nacos,修改了配置) 再调用refresh, 这个我们在这里不
详讲,后续学了微服务源码自然就知道可以再哪里调用。
所以,以后可能有多处地方调用, 我们可以把它封装成一个事件
4.通过事件通知刷新

1 /***
2 * 事件
3 */
4 public class DtpEvent extends ApplicationEvent {
5
6 private ThreadPoolProperties properties;
7
8 public DtpEvent(ThreadPoolProperties properties) {
9 super(properties);
10 this.properties = properties;
11 }
12
13 public ThreadPoolProperties getProperties() {
14 return properties;
15 }
16 }
1 @Component
2 public class DtpEventListener {//} implements ApplicationListener<OrderEvent> {
3
4 // 基于注解的
5 @EventListener(DtpEvent.class)
6 public void onApplicationEvent(DtpEvent event) {
7 ThreadPoolProperties properties = event.getProperties();
8 DtpRegistry.refresh(properties.getPoolName(),properties);
9 }
10
11 }
12

1 @RestController
2 @RequestMapping("/dtp")
3 public class DtpController implements ApplicationEventPublisherAware {
4
5 ApplicationEventPublisher applicationEventPublisher;
6
7 @PostMapping("/refresh")
8 public String refresh(ThreadPoolProperties properties){
9 applicationEventPublisher.publishEvent(new DtpEvent(properties));
10 return "success!";
11 }
12
13
14 @Override
15 public void setApplicationEventPublisher(ApplicationEventPublisher
applicationEventPublisher) {
16 this.applicationEventPublisher=applicationEventPublisher;
17 }
18 }
并且还可以把时间设置为异步
1 /*往SimpleApplicationEventMulticaster设置taskExecutor则为异步事件
2 或者使用@Async*/
3 @Bean(name = "applicationEventMulticaster")
4 public ApplicationEventMulticaster simpleApplicationEventMulticaster() {
5 SimpleApplicationEventMulticaster eventMulticaster
6 = new SimpleApplicationEventMulticaster();
7
8 //ThreadPoolTaskExecutor
9 eventMulticaster.setTaskExecutor(new SimpleAsyncTaskExecutor());
10 return eventMulticaster;
11 }

测试
1 @Autowired
2 private DtpThreadPoolExecutor dtpExecutor1;
3
4 @GetMapping("/add2")
5 public String addOrder2(){
6
7 dtpExecutor1.execute(() -> {
8 System.out.println("下单...");
9 });
10 return "success!";
11 }
其实到这,我们的功能基本完成, 懂了撒花✿✿ヽ(°▽°)ノ✿
线程池相对于开发人员来说是个黑箱,运行情况在出现问题 前很难被感知。
我还想改造, 我想监听线程池, 如果达到了阈值并且告警。
5.监听线程池
思路很简单, 我就实现一些关键代码

1
2 /**
3 * auther: xushu
4 */
5 public class DtpMonitor {
6
7 private ScheduledFuture<?> scheduledFuture;
8
9
10 private void monitor() {
11 for (String name : DtpRegistry.getAllExecutorNames()) {
12 ThreadPoolExecutor dtpExecutor =(ThreadPoolExecutor)
DtpRegistry.getExecutor(name);
13 System.out.println(String.format("线程池名字:%s", name));
14 System.out.println(String.format("线程池核心线程数:%s",
dtpExecutor.getCorePoolSize()));
15 System.out.println(String.format("线程池最大线程数:%s",
dtpExecutor.getMaximumPoolSize()));
16 System.out.println(String.format("线程池当前线程数:%s",
dtpExecutor.getActiveCount()));
17 }
18 }
19
20 private void alarm() {
21 // 读取配置
22 int max = 10;
23
24 for (Executor executor : DtpRegistry.getAllDtpExecutor()) {
25 ThreadPoolExecutor threadPoolExecutor=(ThreadPoolExecutor)executor;
26 int activeCount = threadPoolExecutor.getActiveCount();
27 if (activeCount >= max) {
28 System.out.println(String.format("告警,当前线程池的线程个数为%s, 告警阈值
为%s", activeCount, max));
29 }
30 }
31 }
32
33 }

34
1. 创建一个定时线程
2. monitor定时记录线程池参数, 后续可以用Grafana收集日志
3. alarm 当线程数量达到了阈值 告警, 告警可以自己自由实现比如发邮件,发短线, 我就不完成了
最后, 这个定时器在哪启动呢???
6.通过SmartLifecycle改造
让它随容器启动一起启动, 随容器销毁一起销毁

1
2 /**
3 * auther: xushu
4 */
5 public class DtpMonitor implements SmartLifecycle {
6
7 private ScheduledFuture<?> scheduledFuture;
8
9 private boolean isRunning=false;
10
11 private void monitor() {
12 for (String name : DtpRegistry.getAllExecutorNames()) {
13 ThreadPoolExecutor dtpExecutor =(ThreadPoolExecutor)
DtpRegistry.getExecutor(name);
14 System.out.println(String.format("线程池名字:%s", name));
15 System.out.println(String.format("线程池核心线程数:%s",
dtpExecutor.getCorePoolSize()));
16 System.out.println(String.format("线程池最大线程数:%s",
dtpExecutor.getMaximumPoolSize()));
17 System.out.println(String.format("线程池当前线程数:%s",
dtpExecutor.getActiveCount()));
18 }
19 }
20
21 private void alarm() {
22 // 读取配置
23 int max = 10;
24
25 for (ThreadPoolExecutor threadPoolExecutor : DtpRegistry.getAllDtpExecutor()) {
26 int activeCount = threadPoolExecutor.getActiveCount();
27 if (activeCount >= max) {
28 System.out.println(String.format("告警,当前线程池的线程个数为%s, 告警阈值
为%s", activeCount, max));
29 }
30 }
31 }
32
33 @Override
34 public void start() {

35 scheduledFuture =
Executors.newSingleThreadScheduledExecutor().scheduleAtFixedRate(() -> {
36 monitor();
37 alarm();
38 }, 5, 5, TimeUnit.SECONDS);
39 isRunning=true;
40 }
41
42 @Override
43 public void stop() {
44 scheduledFuture.cancel(false);
45 isRunning=false;
46 }
47
48 @Override
49 public boolean isRunning() {
50 return isRunning;
51 }
52 }
7. 将动态线程池封装成插件
别的项目如果要用一个@EnableDynamicThreadPool 就行

1
2 @SpringBootApplication
3 @EnableDynamicThreadPool
4 public class DynamicThreadpoolApplication {
5
6 public static void main(String[] args) {
7 SpringApplication.run(DynamicThreadpoolApplication.class, args);
8 }
9
10
11 }
12
很简单, 你会发现很多@EnableXXX 里面都有一个@Import , 把我们刚刚写的那堆组件注册进去就
行
1 @Target(ElementType.TYPE)
2 @Retention(RetentionPolicy.RUNTIME)
3 @Import(DtpImportSelector.class)
4 public @interface EnableDynamicThreadPool {
5 }

1 public class DtpImportSelector implements DeferredImportSelector {
2 @Override
3 public String[] selectImports(AnnotationMetadata importingClassMetadata) {
4 return new String[]{
5 DtpImportBeanDefinitionRegistrar.class.getName(),
6 DtpBeanPostProcessor.class.getName(),
7 DtpMonitor.class.getName()
8 };
9 }
10 }
好, 希望大家通过这个案例, 可以对Spring的扩展点有一个新的认识!并且以后可以灵活运用在工作
中。
有道云链接:https://note.youdao.com/s/UbEHulQo
