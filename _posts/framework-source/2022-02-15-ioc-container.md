---



title: "Spring IOC容器加载重要组件"
description: "Spring 容器加载流程图: 访问密码:1nfk1.读取配置如果配置了这样的 Bean: 或者"
author: hsc
date: 2022-02-15 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis', 'IOC']
toc: true



---

Spring 容器加载流程图:
https://www.processon.com/view/link/662dd98a21fb06109ba2e316?cid=6624d18e404949098c6c4526 访问密码:1nfk1.读取配置如果配置了这样的 Bean:
或者

或者这些是不同定义 bean 的方式, 他们最终都会生成 bean。 那 Spring 为了生成 bean 代码复用,使用统一的创建流程,所以通过多态方式读取不同的配置会有不同的读取器,读取完后后续创建 bean 的流程是通用的。
不同的 spring 容器会使用不同的读取器:
1. AnnotationConfigApplicationContext-AnnotatedBeanDefinitionReader
2. ClassPathXmlApplicationContext-XmlBeanDefinitionReader
1.读取器:BeanDefinitionReader 接下来,我们来介绍几种在 Spring 源码中所提供的 BeanDefinition 读取器(BeanDefinitionReader),这些 BeanDefinitionReader 在我们使用 Spring 时用得少,但在 Spring 源码中用得多,相当于 Spring 源码的基础设施。
AnnotatedBeanDefinitionReader

可以直接把某个类转换为 BeanDefinition,并且会解析该类上的注解,比如 1 AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(AppConfig.class);
23 AnnotatedBeanDefinitionReader annotatedBeanDefinitionReader = new AnnotatedBeanDefinitionReader(context);
45 // 将 User.class 解析为 BeanDefinition6 annotatedBeanDefinitionReader.register(User.class);
78 System.out.println(context.getBean("user"));
注意:它能解析的注解是:@Conditional,@Scope、@Lazy、@Primary、@DependsOn、@Role、@DescriptionXmlBeanDefinitionReader 可以解析<bean/>标签 1 AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(AppConfig.class);
23 XmlBeanDefinitionReader xmlBeanDefinitionReader = new XmlBeanDefinitionReader(context);
4 int i = xmlBeanDefinitionReader.loadBeanDefinitions("spring.xml");
56 System.out.println(context.getBean("user"));
2. 扫描器 ClassPathBeanDefinitionScannerClassPathBeanDefinitionScanner 是扫描器,但是它的作用和 BeanDefinitionReader 类似,它可以进行扫描,扫描某个包路径,对扫描到的类进行解析,比如,扫描到的类上如果存在@Component 注解,
那么就会把这个类解析为一个 BeanDefinition,比如:
1 AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext();
2 context.refresh();

34 ClassPathBeanDefinitionScanner scanner = new ClassPathBeanDefinitionScanner(context);
5 scanner.scan("com.xs");
67 System.out.println(context.getBean("userService"));
3.注册 BeanDefinition💡Spring 为了使用通用的创建 bean 流程, 不同的配置最终会成为通用的对象:BeanDefinitionBeanDefinition 表示 Bean 定义,BeanDefinition 中存在很多属性用来描述一个 Bean 的特点。比如:
class,表示 Bean 类型 scope,表示 Bean 作用域,单例或原型等 lazyInit:表示 Bean 是否是懒加载 initMethodName:表示 Bean 初始化时要执行的方法 destroyMethodName:表示 Bean 销毁时要执行的方法还有很多...在 Spring 中,我们经常会通过以下几种方式来定义 Bean:
1. <bean/>
2. @Bean
3. @Component(@Service,@Controller)
这些,我们可以称之申明式定义 Bean。
我们还可以编程式定义 Bean,那就是直接通过 BeanDefinition,比如:
1 AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(AppConfig.class);
23 // 生成一个 BeanDefinition 对象,并设置 beanClass 为 User.class,并注册到 ApplicationContext 中 4 AbstractBeanDefinition beanDefinition = BeanDefinitionBuilder.genericBeanDefinition().getBeanDefinition();
5 beanDefinition.setBeanClass(User.class);
6 context.registerBeanDefinition("user", beanDefinition);

78 System.out.println(context.getBean("user"));
我们还可以通过 BeanDefinition 设置一个 Bean 的其他属性 1 beanDefinition.setScope("prototype"); // 设置作用域 2 beanDefinition.setInitMethodName("init"); // 设置初始化方法 3 beanDefinition.setLazyInit(true); // 设置懒加载和申明式事务、编程式事务类似,通过<bean/>,@Bean,@Component 等申明式方式所定义的 Bean,最终都会被 Spring 解析为对应的 BeanDefinition 对象,并放入 Spring 容器中。
MetadataReader、ClassMetadata、AnnotationMetadata 在 Spring 中需要去解析类的信息,比如类名、类中的方法、类上的注解,这些都可以称之为类的元数据,所以 Spring 中对类的元数据做了抽象,并提供了一些工具类。
MetadataReader 表示类的元数据读取器,默认实现类为 SimpleMetadataReader。比如:
1 public class Test {23 public static void main(String[] args) throws IOException {4 SimpleMetadataReaderFactory simpleMetadataReaderFactory = new SimpleMetadataReaderFactory();
56 // 构造一个 MetadataReader7 MetadataReader metadataReader = simpleMetadataReaderFactory.getMetadataReader("
com.xs.service.UserService");
89 // 得到一个 ClassMetadata,并获取了类名 10 ClassMetadata classMetadata = metadataReader.getClassMetadata();
1112 System.out.println(classMetadata.getClassName());
1314 // 获取一个 AnnotationMetadata,并获取类上的注解信息 15 AnnotationMetadata annotationMetadata = metadataReader.getAnnotationMetadata();
16 for (String annotationType : annotationMetadata.getAnnotationTypes()) {

17 System.out.println(annotationType);
18 }1920 }21 }需要注意的是,SimpleMetadataReader 去解析类时,使用的 ASM 技术。
为什么要使用 ASM 技术,Spring 启动的时候需要去扫描,如果指定的包路径比较宽泛,那么扫描的类是非常多的,那如果在 Spring 启动时就把这些类全部加载进 JVM 了,这样不太好,所以使用了 ASM 技术。
4. BeanFactoryBeanFactory 表示 Bean 工厂,所以很明显,BeanFactory 会负责创建 Bean,并且提供获取 Bean 的 API。
而 ApplicationContext 是 BeanFactory 的一种,在 Spring 源码中,是这么定义的:
1 public interface ApplicationContext extends EnvironmentCapable, ListableBeanFactory,HierarchicalBeanFactory,2 MessageSource, ApplicationEventPublisher, ResourcePatternResolver {34 ...5 }首先,在 Java 中,接口是可以多继承的,我们发现 ApplicationContext 继承了 ListableBeanFactory 和 HierarchicalBeanFactory,而 ListableBeanFactory 和 HierarchicalBeanFactory 都继承至 BeanFactory,所以我们可以认为 ApplicationContext 继承了 BeanFactory,相当于苹果继承水果,宝马继承汽车一样,ApplicationContext 也是 BeanFactory 的一种,拥有 BeanFactory 支持的所有功能,不过 ApplicationContext 比 BeanFactory 更加强大,ApplicationContext 还基础了其他接口,也就表示 ApplicationContext 还拥有其他功能,比如 MessageSource 表示国际化,ApplicationEventPublisher 表示事件发布,EnvironmentCapable 表示获取环境变量,等等,关于 ApplicationContext 后面再详细讨论。

在 Spring 的源码实现中,当我们 new 一个 ApplicationContext 时,其底层会 new 一个 BeanFactory 出来,当使用 ApplicationContext 的某些方法时,比如 getBean(),底层调用的是 BeanFactory 的 getBean()方法。
在 Spring 源码中,BeanFactory 接口存在一个非常重要的实现类是:**DefaultListableBeanFactory,也是非常核心的。**具体重要性,随着后续课程会感受更深。
所以,我们可以直接来使用 DefaultListableBeanFactory,而不用使用 ApplicationContext 的某个实现类,比如:
1 DefaultListableBeanFactory beanFactory = new DefaultListableBeanFactory();
23 AbstractBeanDefinition beanDefinition = BeanDefinitionBuilder.genericBeanDefinition().getBeanDefinition();
4 beanDefinition.setBeanClass(User.class);
56 beanFactory.registerBeanDefinition("user", beanDefinition);
78 System.out.println(beanFactory.getBean("user"));
DefaultListableBeanFactory 是非常强大的,支持很多功能,可以通过查看 DefaultListableBeanFactory 的类继承实现结构来看这部分现在看不懂没关系,源码熟悉一点后回来再来看都可以。
它实现了很多接口,表示,它拥有很多功能:
1. AliasRegistry:支持别名功能,一个名字可以对应多个别名

### 2. BeanDefinitionRegistry:可以注册、保存、移除、获取某个 BeanDefinition
### 3. BeanFactory:Bean 工厂,可以根据某个 bean 的名字、或类型、或别名获取某个 Bean 对象
### 4. SingletonBeanRegistry:可以直接注册、获取某个单例 Bean
### 5. SimpleAliasRegistry:它是一个类,实现了 AliasRegistry 接口中所定义的功能,支持别名功能
### 6. ListableBeanFactory:在 BeanFactory 的基础上,增加了其他功能,可以获取所有 BeanDefinition 的 beanNames,可以根据某个类型获取对应的 beanNames,可以根据某个类型获取{类型:对应的 Bean}的映射关系
### 7. HierarchicalBeanFactory:在 BeanFactory 的基础上,添加了获取父 BeanFactory 的功能
### 8. DefaultSingletonBeanRegistry:它是一个类,实现了 SingletonBeanRegistry 接口,拥有了直接注册、获取某个单例 Bean 的功能
### 9. ConfigurableBeanFactory:在 HierarchicalBeanFactory 和 SingletonBeanRegistry 的基础上,添加了设置父 BeanFactory、类加载器(表示可以指定某个类加载器进行类的加载)、设置 Spring EL 表达式解析器(表示该 BeanFactory 可以解析 EL 表达式)、设置类型转化服务(表示该 BeanFactory 可以进行类型转化)、可以添加 BeanPostProcessor(表示该 BeanFactory 支持 Bean 的后置处理器),可以合并 BeanDefinition,可以销毁某个 Bean 等等功能
### 10. FactoryBeanRegistrySupport:支持了 FactoryBean 的功能
### 11. AutowireCapableBeanFactory:是直接继承了 BeanFactory,在 BeanFactory 的基础上,支持在创建 Bean 的过程中能对 Bean 进行自动装配
### 12. AbstractBeanFactory:实现了 ConfigurableBeanFactory 接口,继承了 FactoryBeanRegistrySupport,这个 BeanFactory 的功能已经很全面了,但是不能自动装配和获取 beanNames
### 13. ConfigurableListableBeanFactory:继承了 ListableBeanFactory、AutowireCapableBeanFactory、ConfigurableBeanFactory
### 14. AbstractAutowireCapableBeanFactory:继承了 AbstractBeanFactory,实现了 AutowireCapableBeanFactory,
拥有了自动装配的功能
15. DefaultListableBeanFactory:继承了 AbstractAutowireCapableBeanFactory,实现了 ConfigurableListableBeanFactory 接口和 BeanDefinitionRegistry 接口,所以 DefaultListableBeanFactory 的功能很强大
5. ApplicationContext 上面有分析到,ApplicationContext 是个接口,实际上也是一个 BeanFactory,不过比 BeanFactory 更加强大,比如:
1. HierarchicalBeanFactory:拥有获取父 BeanFactory 的功能
2. ListableBeanFactory:拥有获取 beanNames 的功能
3. ResourcePatternResolver:资源加载器,可以一次性获取多个资源(文件资源等等)
4. EnvironmentCapable:可以获取运行时环境(没有设置运行时环境功能)
5. ApplicationEventPublisher:拥有广播事件的功能(没有添加事件监听器的功能)

### 6. MessageSource:拥有国际化功能具体的功能演示,后面会有。
我们先来看 ApplicationContext 两个比较重要的实现类:
1. AnnotationConfigApplicationContext
2. ClassPathXmlApplicationContextAnnotationConfigApplicationContext 这部分现在看不懂没关系,源码熟悉一点后回来再来看都可以。
1. ConfigurableApplicationContext:继承了 ApplicationContext 接口,增加了,添加事件监听器、添加 BeanFactoryPostProcessor、设置 Environment,获取 ConfigurableListableBeanFactory 等功能
2. AbstractApplicationContext:实现了 ConfigurableApplicationContext 接口
3. GenericApplicationContext:继承了 AbstractApplicationContext,实现了 BeanDefinitionRegistry 接口,拥有了所有 ApplicationContext 的功能,并且可以注册 BeanDefinition,注意这个类中有一个属性(DefaultListableBeanFactory beanFactory)
4. AnnotationConfigRegistry:可以单独注册某个为类为 BeanDefinition(可以处理该类上的**@Configuration 注解**,已经可以处理**@Bean 注解**),同时可以扫描
5. AnnotationConfigApplicationContext:继承了 GenericApplicationContext,实现了 AnnotationConfigRegistry 接口,拥有了以上所有的功能 ClassPathXmlApplicationContext 它也是继承了 AbstractApplicationContext,但是相对于 AnnotationConfigApplicationContext 而言,功能没有 AnnotationConfigApplicationContext 强大,比如不能注册 BeanDefinition

ApplicationContext=BeanFactory 的全自动版+ 服务周到版 1 // 读取配置 2 DefaultListableBeanFactory defaultListableBeanFactory = newDefaultListableBeanFactory();
3 AnnotatedBeanDefinitionReader annotatedBeanDefinitionReader = newAnnotatedBeanDefinitionReader(defaultListableBeanFactory);
4 annotatedBeanDefinitionReader.register(MainStart.class);
567 // 解析配置 8 AnnotatedBeanDefinition beanDefinition = (AnnotatedBeanDefinition)
defaultListableBeanFactory.getBeanDefinition("mainStart");
910 if(beanDefinition.getMetadata().hasAnnotation(ComponentScan.class.getName())){1112 // 读取为 BeanDefintion13 ClassPathBeanDefinitionScanner classPathBeanDefinitionScanner = newClassPathBeanDefinitionScanner(defaultListableBeanFactory);
14 classPathBeanDefinitionScanner.scan("com.xushu.all");
1516 }1718 // 一个个创建 bean19 defaultListableBeanFactory.preInstantiateSingletons();
除了这些基本的以外, 还有国际化、资源加载、 运行时环境、事件、 BeanPostProcessor、BeanFactoryPostProcessor

国际化先定义一个 MessageSource:
1 @Bean2 public MessageSource messageSource() {3 ResourceBundleMessageSource messageSource = new ResourceBundleMessageSource();
4 messageSource.setBasename("messages");
5 return messageSource;
6 }有了这个 Bean,你可以在你任意想要进行国际化的地方使用该 MessageSource。
同时,因为 ApplicationContext 也拥有国家化的功能,所以可以直接这么用:
1 context.getMessage("test", null, new Locale("en_CN"))
资源加载 ApplicationContext 还拥有资源加载的功能,比如,可以直接利用 ApplicationContext 获取某个文件的内容:
1 AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(AppConfig.class);
23 Resource resource = context.getResource("file://D:\\IdeaProjects\\springframework\\luban\\src\\main\\java\\com\\luban\\entity\\User.java");
4 System.out.println(resource.contentLength());

你可以想想,如果你不使用 ApplicationContext,而是自己来实现这个功能,就比较费时间了。
还比如你可以:
1 AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(AppConfig.class);
23 Resource resource = context.getResource("file://D:\\IdeaProjects\\spring-framework5.3.10\\tuling\\src\\main\\java\\com\\xs\\service\\UserService.java");
4 System.out.println(resource.contentLength());
5 System.out.println(resource.getFilename());
67 Resource resource1 = context.getResource("https://www.baidu.com");
8 System.out.println(resource1.contentLength());
9 System.out.println(resource1.getURL());
1011 Resource resource2 = context.getResource("classpath:spring.xml");
12 System.out.println(resource2.contentLength());
13 System.out.println(resource2.getURL());
还可以一次性获取多个:
1 Resource[] resources = context.getResources("classpath:com/xs/*.class");
2 for (Resource resource : resources) {3 System.out.println(resource.contentLength());
4 System.out.println(resource.getFilename());
5 }获取运行时环境

1 AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(AppConfig.class);
23 Map<String, Object> systemEnvironment =context.getEnvironment().getSystemEnvironment();
4 System.out.println(systemEnvironment);
56 System.out.println("=======");
78 Map<String, Object> systemProperties = context.getEnvironment().getSystemProperties();
9 System.out.println(systemProperties);
1011 System.out.println("=======");
1213 MutablePropertySources propertySources = context.getEnvironment().getPropertySources();
14 System.out.println(propertySources);
1516 System.out.println("=======");
1718 System.out.println(context.getEnvironment().getProperty("NO_PROXY"));
19 System.out.println(context.getEnvironment().getProperty("sun.jnu.encoding"));
20 System.out.println(context.getEnvironment().getProperty("xs"));
注意,可以利用

1 @PropertySource("classpath:spring.properties")
来使得某个 properties 文件中的参数添加到运行时环境中事件发布先定义一个事件监听器 1 @Bean2 public ApplicationListener applicationListener() {3 return new ApplicationListener() {4 @Override5 public void onApplicationEvent(ApplicationEvent event) {6 System.out.println("接收到了一个事件");
7 }8 };
9 }然后发布一个事件:
1 context.publishEvent("kkk");
BeanPostProcessorBeanPostProcess 表示 Bena 的后置处理器,我们可以定义一个或多个 BeanPostProcessor,比如通过一下代码定义一个 BeanPostProcessor:
1 @Component2 public class ZhouyuBeanPostProcessor implements BeanPostProcessor {34 @Override5 public Object postProcessBeforeInitialization(Object bean, StringbeanName) throws BeansException {6 if ("userService".equals(beanName)) {7 System.out.println("初始化前");
8 }

910 return bean;
11 }1213 @Override14 public Object postProcessAfterInitialization(Object bean, StringbeanName) throws BeansException {15 if ("userService".equals(beanName)) {16 System.out.println("初始化后");
17 }1819 return bean;
20 }21 }一个 BeanPostProcessor 可以在任意一个 Bean 的初始化之前以及初始化之后去额外的做一些用户自定义的逻辑,当然,我们可以通过判断 beanName 来进行针对性处理(针对某个 Bean,或某部分 Bean)。
我们可以通过定义 BeanPostProcessor 来干涉 Spring 创建 Bean 的过程。
BeanFactoryPostProcessorBeanFactoryPostProcessor 表示 Bean 工厂的后置处理器,其实和 BeanPostProcessor 类似,BeanPostProcessor 是干涉 Bean 的创建过程,BeanFactoryPostProcessor 是干涉 BeanFactory 的创建过程。比如,我们可以这样定义一个 BeanFactoryPostProcessor:
1 @Component2 public class ZhouyuBeanFactoryPostProcessor implements BeanFactoryPostProcessor {34 @Override5 public void postProcessBeanFactory(ConfigurableListableBeanFactorybeanFactory) throws BeansException {6 System.out.println("加工 beanFactory");
7 }8 }我们可以在 postProcessBeanFactory()方法中对 BeanFactory 进行加工。

FactoryBean 上面提到,我们可以通过 BeanPostPorcessor 来干涉 Spring 创建 Bean 的过程,但是如果我们想一个 Bean 完完全全由我们来创造,也是可以的,比如通过 FactoryBean:
1 @Component2 public class ZhouyuFactoryBean implements FactoryBean {34 @Override5 public Object getObject() throws Exception {6 UserService userService = new UserService();
78 return userService;
9 }1011 @Override12 public Class<?> getObjectType() {13 return UserService.class;
14 }15 }通过上面这段代码,我们自己创造了一个 UserService 对象,并且它将成为 Bean。但是通过这种方式创造出来的 UserService 的 Bean,只会经过初始化后,其他 Spring 的生命周期步骤是不会经过的,比如依赖注入。
有同学可能会想到,通过@Bean 也可以自己生成一个对象作为 Bean,那么和 FactoryBean 的区别是什么呢?其实在很多场景下他俩是可以替换的,但是站在原理层面来说的,区别很明显,@Bean 定义的 Bean 是会经过完整的 Bean 生命周期的。
ExcludeFilter 和 IncludeFilter 这两个 Filter 是 Spring 扫描过程中用来过滤的。 ExcludeFilter 表示排除过滤器,IncludeFilter 表示包含过滤器。
比如以下配置,表示扫描 com.xs 这个包下面的所有类,但是排除 UserService 类,也就是就算它上面有@Component 注解也不会成为 Bean。

1 @ComponentScan(value = "com.xs",2 excludeFilters = {@ComponentScan.Filter(3 type = FilterType.ASSIGNABLE_TYPE,4 classes = UserService.class)}.)
5 public class AppConfig {6 }再比如以下配置,就算 UserService 类上没有@Component 注解,它也会被扫描成为一个 Bean。
1 @ComponentScan(value = "com.xs",2 includeFilters = {@ComponentScan.Filter(3 type = FilterType.ASSIGNABLE_TYPE,4 classes = UserService.class)})
5 public class AppConfig {6 }FilterType 分为:
1. ANNOTATION:表示是否包含某个注解
2. ASSIGNABLE_TYPE:表示是否是某个类
3. ASPECTJ:表示否是符合某个 Aspectj 表达式
4. REGEX:表示是否符合某个正则表达式
5. CUSTOM:自定义在 Spring 的扫描逻辑中,默认会添加一个 AnnotationTypeFilter 给 includeFilters,表示默认情况下 Spring 扫描过程中会认为类上有@Component 注解的就是 Bean。
