---

title: "SpringBoot启动过程源码解析"
description: "课程内容: 1、SpringBoot 启动过程源码解析 2、SpringBoot 启动过程中扩展点源码解析 3、SpringBoot 配置文件优先级解析 1、推"
author: hsc
date: 2022-12-08 00:00:00 +0800
categories: ['Java 后端', '微服务']
tags: ['微服务', 'SpringCloud', 'SpringBoot', 'Docker']
toc: true

---

课程内容:
1、SpringBoot 启动过程源码解析 2、SpringBoot 启动过程中扩展点源码解析 3、SpringBoot 配置文件优先级解析 1、推测 web 应用类型
1. 如果项目依赖中存在 org.springframework.web.reactive.DispatcherHandler,并且不存在 org.springframework.web.servlet.DispatcherServlet,那么应用类型为 WebApplicationType.REACTIVE
2. 如果项目依赖中不存在 org.springframework.web.reactive.DispatcherHandler,也不存在 org.springframework.web.servlet.DispatcherServlet,那么应用类型为 WebApplicationType.NONE
3. 否则,应用类型为 WebApplicationType.SERVLET
2、获取 BootstrapRegistryInitializer 对象
1. 从"META-INF/spring.factories"中读取 key 为 BootstrapRegistryInitializer 类型的扩展点,并实例化出对应扩展点对象
2. BootstrapRegistryInitializer 的作用是可以初始化 BootstrapRegistry
3. 上面的 DefaultBootstrapContext 对象就是一个 BootstrapRegistry,可以用来注册一些对象,这些对象可以用在从 SpringBoot 启动到 Spring 容器初始化完成的过程中
4. 我的理解:没有 Spring 容器之前就利用 BootstrapRegistry 来共享一些对象,有了 Spring 容器之后就利用 Spring 容器来共享一些对象
3、获取 ApplicationContextInitializer 对象
1. 从"META-INF/spring.factories"中读取 key 为 ApplicationContextInitializer 类型的扩展点,并实例化出对应扩展点对象
2. 顾名思义,ApplicationContextInitializer 是用来初始化 Spring 容器 ApplicationContext 对象的,比如可以利用 ApplicationContextInitializer 来向 Spring 容器中添加 ApplicationListener

4、获取 ApplicationListener 对象
1. 从"META-INF/spring.factories"中读取 key 为 ApplicationListener 类型的扩展点,并实例化出对应扩展点对象
2. ApplicationListener 是 Spring 中的监听器,并不是 SpringBoot 中的新概念,不多解释了
5、推测出 Main 类(main()方法所在的类)
没什么具体的作用,逻辑是根据当前线程的调用栈来判断 main()方法在哪个类,哪个类就是 Main 类 run(String... args)方法
1. 创建 DefaultBootstrapContext 对象
2. 利用 BootstrapRegistryInitializer 初始化 DefaultBootstrapContext 对象
3. 获取 SpringApplicationRunListeners 这三个步骤没什么特殊的
5、触发 SpringApplicationRunListener 的 starting()
默认情况下 SpringBoot 提供了一个 EventPublishingRunListener,它实现了 SpringApplicationRunListener 接口,默认情况下会利用 EventPublishingRunListener 发布一个 ApplicationContextInitializedEvent 事件,程序员可以通过定义 ApplicationListener 来消费这个事件 6、创建 Environment 对象 Environment 对象表示环境变量,该对象内部主要包含了:
1. 当前操作系统的环境变量
2. JVM 的一些配置信息
3. -D 方式所配置的 JVM 环境变量
7、触发 SpringApplicationRunListener 的 environmentPrepared()
默认情况下会利用 EventPublishingRunListener 发布一个 ApplicationEnvironmentPreparedEvent 事件,程序员可以通过定义 ApplicationListener 来消费这个事件,比如默认情况下会有一个 EnvironmentPostProcessorApplicationListener 来消费这个事件,而这个 ApplicationListener 接收到这个事件之后,就会解析 application.properties、application.yml 文件,并添加到 Environment 对象中去。
8、打印 Banner 没什么特殊的

9、创建 Spring 容器对象(ApplicationContext)
会利用 ApplicationContextFactory.DEFAULT,根据应用类型创建对应的 Spring 容器。
ApplicationContextFactory.DEFAULT 为:
1 ApplicationContextFactory DEFAULT = (webApplicationType) -> {2 try {3 switch (webApplicationType) {4 case SERVLET:
5 return new AnnotationConfigServletWebServerApplicationContext();
6 case REACTIVE:
7 return new AnnotationConfigReactiveWebServerApplicationContext();
8 default:
9 return new AnnotationConfigApplicationContext();
10 }11 }12 catch (Exception ex) {13 throw new IllegalStateException("Unable create a default ApplicationContextinstance, "
14 + "you may need a customApplicationContextFactory", ex);
15 }16 };
所以:
1. 应用类型为 SERVLET,则对应 AnnotationConfigServletWebServerApplicationContext
2. 应用类型为 REACTIVE,则对应 AnnotationConfigReactiveWebServerApplicationContext
3. 应用类型为普通类型,则对应 AnnotationConfigApplicationContext
10、利用 ApplicationContextInitializer 初始化 Spring 容器对象默认情况下 SpringBoot 提供了多个 ApplicationContextInitializer,其中比较重要的有 ConditionEvaluationReportLoggingListener,别看到它的名字叫 XXXListener,但是它确实是实现了 ApplicationContextInitializer 接口的。

在它的 initialize()方法中会:
1. 将 Spring 容器赋值给它的 applicationContext 属性
2. 并且往 Spring 容器中添加一个 ConditionEvaluationReportListener(ConditionEvaluationReportLoggingListener 的内部类),它是一个 ApplicationListener
3. 并生成一个 ConditionEvaluationReport 对象赋值给它的 report 属性 ConditionEvaluationReportListener 会负责接收 ContextRefreshedEvent 事件,也就是 Spring 容器一旦启动完毕就会触发 ContextRefreshedEvent,ConditionEvaluationReportListener 就会打印自动配置类的条件评估报告。
11、触发 SpringApplicationRunListener 的 contextPrepared()
默认情况下会利用 EventPublishingRunListener 发布一个 ApplicationContextInitializedEvent 事件,默认情况下暂时没有 ApplicationListener 消费了这个事件 12、调用 DefaultBootstrapContext 对象的 close()
没什么特殊的,忽略 13、将启动类作为配置类注册到 Spring 容器中(load()方法)
将 SpringApplication.run(MyApplication.class);中传入进来的类,比如 MyApplication.class,作为 Spring 容器的配置类
14、 触发 SpringApplicationRunListener 的 contextLoaded()
默认情况下会利用 EventPublishingRunListener 发布一个 ApplicationPreparedEvent 事件 15、刷新 Spring 容器调用 Spring 容器的 refresh()方法,结合第 9、13 步,相当于执行了这样一个流程:
1. AnnotationConfigApplicationContext applicationContext = new AnnotationConfigApplicationContext();
2. applicationContext .register(MyApplication.class)
3. applicationContext .refresh()
16、触发 SpringApplicationRunListener 的 started()

发布 ApplicationStartedEvent 事件和 AvailabilityChangeEvent 事件,AvailabilityChangeEvent 事件表示状态变更状态,变更后的状态为 LivenessState.CORRECTLivenessState 枚举有两个值:
1. CORRECT:表示当前应用正常运行中
2. BROKEN:表示当前应用还在运行,但是内部出现问题,暂时还没发现哪里用到了
17、调用 ApplicationRunner 和 CommandLineRunner
1. 获取 Spring 容器中的 ApplicationRunner 类型的 Bean
2. 获取 Spring 容器中的 CommandLineRunner 类型的 Bean
3. 执行它们的 run()
18、触发 SpringApplicationRunListener 的 ready()
发布 ApplicationReadyEvent 事件和 AvailabilityChangeEvent 事件,AvailabilityChangeEvent 事件表示状态变更状态,变更后的状态为 ReadinessState.ACCEPTING_TRAFFICReadinessState 枚举有两个值:
1. ACCEPTING_TRAFFIC:表示当前应用准备接收请求
2. REFUSING_TRAFFIC:表示当前应用拒绝接收请求,比如 Tomcat 关闭时,就会发布 AvailabilityChangeEvent 事件,并且状态为 REFUSING_TRAFFIC
19、上述过程抛异常了就触发 SpringApplicationRunListener 的 failed()
发布 ApplicationFailedEvent 事件配置文件解析流程图:https://www.processon.com/view/link/62d399e71e08530a89222b23SpringBoot 完整的配置优先级 https://docs.spring.io/spring-boot/docs/current/reference/html/features.html#features.external-config 优先级由低到高(注意和我写的顺序是反的,我写的是由高到底)
1. Default properties (specified by setting SpringApplication.setDefaultProperties).
2. @PropertySource annotations on your @Configuration classes. Please note that such property sources

are not added to the Environment until the application context is being refreshed. This is too late toconfigure certain properties such as logging.* and spring.main.* which are read before refresh begins.
3. Config data (such as application.properties files).
4. A RandomValuePropertySource that has properties only in random.*.
5. OS environment variables.
6. Java System properties (System.getProperties()).
7. JNDI attributes from java:comp/env. 不管它
8. ServletContext init parameters.
9. ServletConfig init parameters.
10. Properties from SPRING_APPLICATION_JSON (inline JSON embedded in an environment variable orsystem property).
11. Command line arguments.
12. properties attribute on your tests. Available on @SpringBootTest and the test annotations for testinga particular slice of your application.
13. @TestPropertySource annotations on your tests.
14. Devtools global settings properties in the $HOME/.config/spring-boot directory when devtools isactive.
