---


title: "手写模拟SpringBoot核心流程"
description: "课程内容: 1、手写模拟 SpringBoot 启动过程 2、手写模拟 SpringBoot 条件注解功能 3、手写模拟 SpringBoot 自动配置功能 4"
author: hsc
date: 2022-10-01 00:00:00 +0800
categories: ['Java 后端', '微服务']
tags: ['微服务', 'SpringCloud', 'SpringBoot', 'Docker']
toc: true


---

课程内容:
1、手写模拟 SpringBoot 启动过程 2、手写模拟 SpringBoot 条件注解功能 3、手写模拟 SpringBoot 自动配置功能 4、SpringBoot 整合 Tomcat 底层源码分析 5、spring.factories 文件解析源码分析 6、SpringBoot 自动配置类加载过程源码分析通过手写模拟实现一个 Spring Boot,让大家能以非常简单的方式就能知道 Spring Boot 大概是如何工作的。
1. springboot 模块,表示 springboot 框架的源码实现
2. user 包,表示用户业务系统,用来写业务代码来测试我们所模拟出来的 SpringBoot 首先,SpringBoot 是基于的 Spring,所以我们要依赖 Spring,然后我希望我们模拟出来的 SpringBoot 也支持 Spring MVC 的那一套功能,所以也要依赖 Spring MVC,包括 Tomcat 等,所以在 SpringBoot 模块中要添加以下依赖:
1 <dependencies>2 <dependency>3 <groupId>org.springframework</groupId>

4 <spanrtifactId>spring-context</artifactId>5 <version>5.3.18</version>6 </dependency>7 <dependency>8 <groupId>org.springframework</groupId>9 <spanrtifactId>spring-web</artifactId>10 <version>5.3.18</version>11 </dependency>12 <dependency>13 <groupId>org.springframework</groupId>14 <spanrtifactId>spring-webmvc</artifactId>15 <version>5.3.18</version>16 </dependency>1718 <dependency>19 <groupId>javax.servlet</groupId>20 <spanrtifactId>javax.servlet-api</artifactId>21 <version>4.0.1</version>22 </dependency>2324 <dependency>25 <groupId>org.apache.tomcat.embed</groupId>26 <spanrtifactId>tomcat-embed-core</artifactId>27 <version>9.0.60</version>28 </dependency>29 </dependencies>在 User 模块下我们进行正常的开发就行了,比如先添加 SpringBoot 依赖:
1 <dependencies>2 <dependency>3 <groupId>org.example</groupId>4 <spanrtifactId>springboot</artifactId>5 <version>1.0-SNAPSHOT</version>6 </dependency>7 </dependencies>然后定义相关的 Controller 和 Service:

1 @RestController2 public class UserController {34 @Autowired5 private UserService userService;
67 @GetMapping("test")
8 public String test(){9 return userService.test();
10 }11 }因为我们模拟实现的是 SpringBoot,而不是 SpringMVC,所以我直接在 user 包下定义了 UserController 和 UserService,最终我希望能运行 MyApplication 中的 main 方法,就直接启动了项目,并能在浏览器中正常的访问到 UserController 中的某个方法。
核心注解和核心类我们在真正使用 SpringBoot 时,核心会用到 SpringBoot 一个类和注解:
1. @SpringBootApplication,这个注解是加在应用启动类上的,也就是 main 方法所在的类
2. SpringApplication,这个类中有个 run()方法,用来启动 SpringBoot 应用的所以我们也来模拟实现他们。

一个@ZhouyuSpringBootApplication 注解:
1 @Target(ElementType.TYPE)
2 @Retention(RetentionPolicy.RUNTIME)
3 @Configuration4 @ComponentScan5 public @interface ZhouyuSpringBootApplication {6 }一个用来实现启动逻辑的 ZhouyuSpringApplication 类。
1 public class ZhouyuSpringApplication {23 public static void run(Class clazz){45 }67 }注意 run 方法需要接收一个 Class 类型的参数,这个 class 是用来干嘛的,等会就知道了。
有了以上两者,我们就可以在 MyApplication 中来使用了,比如:
1 @ZhouyuSpringBootApplication2 public class MyApplication {34 public static void main(String[] args) {5 ZhouyuSpringApplication.run(MyApplication.class);
6 }7 }现在用来是有模有样了,但中看不中用,所以我们要来好好实现以下 run 方法中的逻辑了。
run 方法 run 方法中需要实现什么具体的逻辑呢?

首先,我们希望 run 方法一旦执行完,我们就能在浏览器中访问到 UserController,那势必在 run 方法中要启动 Tomcat,通过 Tomcat 就能接收到请求了。
大家如果学过 Spring MVC 的底层原理就会知道,在 SpringMVC 中有一个 Servlet 非常核心,那就是 DispatcherServlet,这个 DispatcherServlet 需要绑定一个 Spring 容器,因为 DispatcherServlet 接收到请求后,就会从所绑定的 Spring 容器中找到所匹配的 Controller,并执行所匹配的方法。
所以,在 run 方法中,我们要实现的逻辑如下:
1. 创建一个 Spring 容器
2. 创建 Tomcat 对象
3. 生成 DispatcherServlet 对象,并且和前面创建出来的 Spring 容器进行绑定
4. 将 DispatcherServlet 添加到 Tomcat 中
5. 启动 Tomcat 创建 Spring 容器这个步骤比较简单,代码如下:
1 public class ZhouyuSpringApplication {23 public static void run(Class clazz){4 AnnotationConfigWebApplicationContext applicationContext = newAnnotationConfigWebApplicationContext();
5 applicationContext.register(clazz);
6 applicationContext.refresh();
789 }10 }我们创建的是一个 AnnotationConfigWebApplicationContext 容器,并且把 run 方法传入进来的 class 作为容器的配置类,比如在 MyApplication 的 run 方法中,我们就是把 MyApplication.class 传入到了 run 方法中,最终 MyApplication 就是所创建出来的 Spring 容器的配置类,并且由于 MyApplication 类上有@ZhouyuSpringBootApplication 注解,而@ZhouyuSpringBootApplication 注解的定义上又存在@ComponentScan 注解,所以 AnnotationConfigWebApplicationContext 容器在执行 refresh

时,就会解析 MyApplication 这个配置类,从而发现定义了@ComponentScan 注解,也就知道了要进行扫描,只不过扫描路径为空,而 AnnotationConfigWebApplicationContext 容器会处理这种情况,如果扫描路径会空,则会将 MyApplication 所在的包路径做为扫描路径,从而就会扫描到 UserService 和 UserController。
所以 Spring 容器创建完之后,容器内部就拥有了 UserService 和 UserController 这两个 Bean。
启动 Tomcat 图灵课堂:周瑜我们用的是 Embed-Tomcat,也就是内嵌的 Tomcat,真正的 SpringBoot 中也用的是内嵌的 Tomcat,而对于启动内嵌的 Tomcat,也并不麻烦,代码如下:
1 public static void startTomcat(WebApplicationContext applicationContext){23 Tomcat tomcat = new Tomcat();
45 Server server = tomcat.getServer();
6 Service service = server.findService("Tomcat");
78 Connector connector = new Connector();
9 connector.setPort(8081);
1011 Engine engine = new StandardEngine();
12 engine.setDefaultHost("localhost");
1314 Host host = new StandardHost();
15 host.setName("localhost");
1617 String contextPath = "";
18 Context context = new StandardContext();
19 context.setPath(contextPath);
20 context.addLifecycleListener(new Tomcat.FixContextListener());
2122 host.addChild(context);
23 engine.addChild(host);

2425 service.setContainer(engine);
26 service.addConnector(connector);
2728 tomcat.addServlet(contextPath, "dispatcher", newDispatcherServlet(applicationContext));
29 context.addServletMappingDecoded("/*", "dispatcher");
3031 try {32 tomcat.start();
33 } catch (LifecycleException e) {34 e.printStackTrace();
35 }3637 }代码虽然看上去比较多,但是逻辑并不复杂,比如配置了 Tomcat 绑定的端口为 8081,后面向当前 Tomcat 中添加了 DispatcherServlet,并设置了一个 Mapping 关系,最后启动,其他代码则不用太过关心。
而且在构造 DispatcherServlet 对象时,传入了一个 ApplicationContext 对象,也就是一个 Spring 容器,就是我们前文说的,DispatcherServlet 对象和一个 Spring 容器进行绑定。
接下来,我们只需要在 run 方法中,调用 startTomcat 即可:
1 public static void run(Class clazz){2 AnnotationConfigWebApplicationContext applicationContext = newAnnotationConfigWebApplicationContext();
3 applicationContext.register(clazz);
4 applicationContext.refresh();
56 startTomcat(applicationContext);
78 }实际上代码写到这,一个极度精简版的 SpringBoot 就写出来了,比如现在运行 MyApplication,就能正常的启动项目,并能接收请求。

启动能看到 Tomcat 的启动日志:
然后在浏览器上访问:http://localhost:8081/test 也能正常的看到结果:
此时,你可以继续去写其他的 Controller 和 Service 了,照样能正常访问到,而我们的业务代码中仍然只用到了 ZhouyuSpringApplication 类和@ZhouyuSpringBootApplication 注解。
实现 Tomcat 和 Jetty 的切换虽然我们前面已经实现了一个比较简单的 SpringBoot,不过我们可以继续来扩充它的功能,比如现在我有这么一个需求,这个需求就是我现在不想使用 Tomcat 了,而是想要用 Jetty,那该怎么办?
我们前面代码中默认启动的是 Tomcat,那我现在想改成这样子:
1. 如果项目中有 Tomcat 的依赖,那就启动 Tomcat
2. 如果项目中有 Jetty 的依赖就启动 Jetty
3. 如果两者都没有则报错

### 4. 如果两者都有也报错这个逻辑希望 SpringBoot 自动帮我实现,对于程序员用户而言,只要在 Pom 文件中添加相关依赖就可以了,想用 Tomcat 就加 Tomcat 依赖,想用 Jetty 就加 Jetty 依赖。
那 SpringBoot 该如何实现呢?
我们知道,不管是 Tomcat 还是 Jetty,它们都是应用服务器,或者是 Servlet 容器,所以我们可以定义接口来表示它们,这个接口叫做 WebServer(别问我为什么叫这个,因为真正的 SpringBoot 源码中也叫这个)。
并且在这个接口中定义一个 start 方法:
1 public interface WebServer {23 public void start();
45 }有了 WebServer 接口之后,就针对 Tomcat 和 Jetty 提供两个实现类:
1 public class TomcatWebServer implements WebServer{23 @Override4 public void start() {5 System.out.println("启动 Jetty");
6 }7 }1 public class JettyWebServer implements WebServer{23 @Override4 public void start() {5 System.out.println("启动 Tomcat");

6 }7 }而在 ZhouyuSpringApplication 中的 run 方法中,我们就要去获取对应的 WebServer,然后启动对应的 webServer,代码为:
1 public static void run(Class clazz){2 AnnotationConfigWebApplicationContext applicationContext = newAnnotationConfigWebApplicationContext();
3 applicationContext.register(clazz);
4 applicationContext.refresh();
56 WebServer webServer = getWebServer(applicationContext);
7 webServer.start();
89 }1011 public static WebServer getWebServer(ApplicationContext applicationContext){12 return null;
13 }这样,我们就只需要在 getWebServer 方法中去判断到底该返回 TomcatWebServer 还是 JettyWebServer。
前面提到过,我们希望根据项目中的依赖情况,来决定到底用哪个 WebServer,我就直接用 SpringBoot 中的源码实现方式来模拟了。
模拟实现条件注解图灵课堂:周瑜首先我们得实现一个条件注解@ZhouyuConditionalOnClass,对应代码如下:
1 @Target({ ElementType.TYPE, ElementType.METHOD })
2 @Retention(RetentionPolicy.RUNTIME)
3 @Conditional(ZhouyuOnClassCondition.class)

4 public @interface ZhouyuConditionalOnClass {5 String value() default "";
6 }注意核心为@Conditional(ZhouyuOnClassCondition.class)中的 ZhouyuOnClassCondition,因为它才是真正得条件逻辑:
1 public class ZhouyuOnClassCondition implements Condition {23 @Override4 public boolean matches(ConditionContext context, AnnotatedTypeMetadata metadata) {5 Map<String, Object> annotationAttributes =6metadata.getAnnotationAttributes(ZhouyuConditionalOnClass.class.getName());
78 String className = (String) annotationAttributes.get("value");
910 try {11 context.getClassLoader().loadClass(className);
12 return true;
13 } catch (ClassNotFoundException e) {14 return false;
15 }16 }17 }具体逻辑为,拿到@ZhouyuConditionalOnClass 中的 value 属性,然后用类加载器进行加载,如果加载到了所指定的这个类,那就表示符合条件,如果加载不到,则表示不符合条件。
模拟实现自动配置类有了条件注解,我们就可以来使用它了,那如何实现呢?
这里就要用到自动配置类的概念,我们先看代码:
1 @Configuration

2 public class WebServiceAutoConfiguration {34 @Bean5 @ZhouyuConditionalOnClass("org.apache.catalina.startup.Tomcat")
6 public TomcatWebServer tomcatWebServer(){7 return new TomcatWebServer();
8 }910 @Bean11 @ZhouyuConditionalOnClass("org.eclipse.jetty.server.Server")
12 public JettyWebServer jettyWebServer(){13 return new JettyWebServer();
14 }15 }这个代码还是比较简单的,通过一个 WebServiceAutoConfiguration 的 Spring 配置类,在里面定义了两个 Bean,一个 TomcatWebServer,一个 JettyWebServer,不过这两个要生效的前提是符合当前所指定的条件,比如:
1. 只有存在"org.apache.catalina.startup.Tomcat"类,那么才有 TomcatWebServer 这个 Bean
2. 只有存在"org.eclipse.jetty.server.Server"类,那么才有 TomcatWebServer 这个 Bean 并且我们只需要在 ZhouyuSpringApplication 中 getWebServer 方法,如此实现:
1 public static WebServer getWebServer(ApplicationContext applicationContext){2 // key 为 beanName, value 为 Bean 对象 3 Map<String, WebServer> webServers =applicationContext.getBeansOfType(WebServer.class);
45 if (webServers.isEmpty()) {6 throw new NullPointerException();
7 }8 if (webServers.size() > 1) {9 throw new IllegalStateException();
10 }1112 // 返回唯一的一个 13 return webServers.values().stream().findFirst().get();
14 }

这样整体 SpringBoot 启动逻辑就是这样的:
1. 创建一个 AnnotationConfigWebApplicationContext 容器
2. 解析 MyApplication 类,然后进行扫描
3. 通过 getWebServer 方法从 Spring 容器中获取 WebServer 类型的 Bean
4. 调用 WebServer 对象的 start 方法有了以上步骤,我们还差了一个关键步骤,就是 Spring 要能解析到 WebServiceAutoConfiguration 这个自动配置类,因为不管这个类里写了什么代码,Spring 不去解析它,那都是没用的,此时我们需要 SpringBoot 在 run 方法中,能找到 WebServiceAutoConfiguration 这个配置类并添加到 Spring 容器中。
MyApplication 是 Spring 的一个配置类,但是 MyApplication 是我们传递给 SpringBoot,从而添加到 Spring 容器中去的,而 WebServiceAutoConfiguration 就需要 SpringBoot 去自动发现,而不需要程序员做任何配置才能把它添加到 Spring 容器中去,而且要注意的是,Spring 容器扫描也是扫描不到 WebServiceAutoConfiguration 这个类的,因为我们的扫描路径是"com.zhouyu.user",而 WebServiceAutoConfiguration 所在的包路径为"com.zhouyu.springboot"。
那 SpringBoot 中是如何实现的呢?通过 SPI,当然 SpringBoot 中自己实现了一套 SPI 机制,也就是我们熟知的 spring.factories 文件,那么我们模拟就不搞复杂了,就直接用 JDK 自带的 SPI 机制。
发现自动配置类图灵课堂:周瑜为了实现这个功能,以及为了最后的效果演示,我们需要把 springboot 源码和业务代码源码拆分两个 maven 模块,也就相当于两个项目,最后的源码结构为:

现在我们只需要在 springboot 项目中的 resources 目录下添加如下目录(META-INF/services)和文件:
SPI 的配置就完成了,相当于通过 com.zhouyu.springboot.AutoConfiguration 文件配置了 springboot 中所提供的配置类。
并且提供一个接口:
1 public interface AutoConfiguration {2 }并且 WebServiceAutoConfiguration 实现该接口:

1 @Configuration2 public class WebServiceAutoConfiguration implements AutoConfiguration {34 @Bean5 @ZhouyuConditionalOnClass("org.apache.catalina.startup.Tomcat")
6 public TomcatWebServer tomcatWebServer(){7 return new TomcatWebServer();
8 }910 @Bean11 @ZhouyuConditionalOnClass("org.eclipse.jetty.server.Server")
12 public JettyWebServer jettyWebServer(){13 return new JettyWebServer();
14 }15 }然后我们再利用 spring 中的@Import 技术来导入这些配置类,我们在@ZhouyuSpringBootApplication 的定义上增加如下代码:
1 @Target(ElementType.TYPE)
2 @Retention(RetentionPolicy.RUNTIME)
3 @Configuration4 @ComponentScan5 @Import(ZhouyuImportSelect.class)
6 public @interface ZhouyuSpringBootApplication {7 }ZhouyuImportSelect 类为:
1 public class ZhouyuImportSelect implements DeferredImportSelector {2 @Override3 public String[] selectImports(AnnotationMetadata importingClassMetadata) {4 ServiceLoader<AutoConfiguration> serviceLoader =ServiceLoader.load(AutoConfiguration.class);
56 List<String> list = new ArrayList<>();
7 for (AutoConfiguration autoConfiguration : serviceLoader) {

8 list.add(autoConfiguration.getClass().getName());
9 }1011 return list.toArray(new String[0]);
12 }13 }这就完成了从 com.zhouyu.springboot.AutoConfiguration 文件中获取自动配置类的名字,并导入到 Spring 容器中,从而 Spring 容器就知道了这些配置类的存在,而对于 user 项目而言,是不需要修改代码的。
此时运行 MyApplication,就能看到启动了 Tomcat:
因为 SpringBoot 默认在依赖中添加了 Tomcat 依赖,而如果在 User 模块中再添加 jetty 的依赖:
1 <dependencies>2 <dependency>3 <groupId>org.example</groupId>4 <spanrtifactId>springboot</artifactId>5 <version>1.0-SNAPSHOT</version>6 </dependency>78 <dependency>9 <groupId>org.eclipse.jetty</groupId>10 <spanrtifactId>jetty-server</artifactId>11 <version>9.4.43.v20210629</version>12 </dependency>13 </dependencies>

那么启动 MyApplication 就会报错:
只有先排除到 Tomcat 的依赖,再添加 Jetty 的依赖才能启动 Jetty:
注意:由于没有了 Tomcat 的依赖,记得把最开始写的 startTomcat 方法给注释掉,并删除掉相关依赖。

总结到此,我们实现了一个简单版本的 SpringBoot,因为 SpringBoot 首先是基于 Spring 的,而且提供的功能也更加强大,随着后续内容的展开,相信大家会对本文中的各个功能会有更加深刻的理解,也希望大家都自己去实现一边,完整的代码地址:https://gitee.com/archguide/zhouyu-springboot
