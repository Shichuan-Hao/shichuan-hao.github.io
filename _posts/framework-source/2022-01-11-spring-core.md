---


title: "Spring底层核心原理解析"
description: "依赖注入底层原理 3. 初始化底层原理 4. 推断构造方法底层原理 5. AOP 底层原理 6."
author: hsc
date: 2022-01-11 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis', 'IOC', 'AOP', 'Spring事务', 'SpringBoot']
toc: true


---

### 1. Bean 的生命周期底层原理
2. 依赖注入底层原理
3. 初始化底层原理
4. 推断构造方法底层原理
5. AOP 底层原理
6. Spring 事务底层原理但都只是大致流程,后续会针对每个流程详细深入的讲解并分析源码实现。
先来看看入门使用 Spring 的代码:
ClassPathXmlApplicationContext context = new ClassPathXmlApplicationContext("spring.xml");
UserService userService = (UserService) context.getBean("userService");
userService.test();
对于这三行代码应该,大部分同学应该都是比较熟悉,这是学习 Spring 的 hello world。可是,这三行代码底层都做了什么,比如:
1. 第一行代码,会构造一个 ClassPathXmlApplicationContext 对象,ClassPathXmlApplicationContext 该如何理解,调用该构造方法除开会实例化得到一个对象,还会做哪些事情?
2. 第二行代码,会调用 ClassPathXmlApplicationContext 的 getBean 方法,会得到一个 UserService 对象,
getBean()是如何实现的?返回的 UserService 对象和我们自己直接 new 的 UserService 对象有区别吗?
3. 第三行代码,就是简单的调用 UserService 的 test()方法,不难理解。
光看这三行代码,其实并不能体现出来 Spring 的强大之处,也不能理解为什么需要 ClassPathXmlApplicationContext 和 getBean()方法,随着课程的深入将会改变你此时的观念,而对于上面的这些疑问,也会随着课程深入逐步得到解决。对于这三行代码,你现在可以认为:如果你要用 Spring,你就得这么写。就像你要用 Mybatis,你就得写各种 Mapper 接口。
但是用 ClassPathXmlApplicationContext 其实已经过时了,在新版的 Spring MVC 和 Spring Boot 的底层主要用的都是 AnnotationConfigApplicationContext,比如:
AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(AppConfig.class);
//ClassPathXmlApplicationContext context = new ClassPathXmlApplicationContext("spring.xml");
UserService userService = (UserService) context.getBean("userService");
userService.test();

可以看到 AnnotationConfigApplicationContext 的用法和 ClassPathXmlApplicationContext 是非常类似的,只不过需要传入的是一个 class,而不是一个 xml 文件。
而 AppConfig.class 和 spring.xml 一样,表示 Spring 的配置,比如可以指定扫描路径,可以直接定义 Bean,比如:
spring.xml 中的内容为:
<context:component-scan base-package="com.zhouyu"/><bean id="userService" class="com.zhouyu.service.UserService"/>AppConfig 中的内容为:
@ComponentScan("com.zhouyu")
public class AppConfig {@Beanpublic UserService userService(){return new UserService();
}}所以 spring.xml 和 AppConfig.class 本质上是一样的。
目前,我们基本很少直接使用上面这种方式来用 Spring,而是使用 Spring MVC,或者 Spring Boot,但是它们都是基于上面这种方式的,都需要在内部去创建一个 ApplicationContext 的,只不过:
1. Spring MVC 创建的是 XmlWebApplicationContext,和 ClassPathXmlApplicationContext 类似,都是基于 XML 配置的
2. Spring Boot 创建的是 AnnotationConfigApplicationContext 因为 AnnotationConfigApplicationContext 是比较重要的,并且 AnnotationConfigApplicationContext 和 ClassPathXmlApplicationContext 大部分底层都是共同的,后续课程我们会着重将 AnnotationConfigApplicationContext 的底层实现,对于 ClassPathXmlApplicationContext,同学们可以在课程结束后作为作业,业余时间看看相关源码即可。
Spring 中是如何创建一个对象?

其实不管是 AnnotationConfigApplicationContext 还是 ClassPathXmlApplicationContext,目前,我们都可以简单的将它们理解为就是用来创建 Java 对象的,比如调用 getBean()就会去创建对象(此处不严谨,getBean 可能也不会去创建对象,后续课程详解)。
在 Java 语言中,肯定是根据某个类来创建一个对象的。我们在看一下实例代码:
AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(AppConfig.class);
UserService userService = (UserService) context.getBean("userService");
userService.test();
当我们调用 context.getBean("userService")时,就会去创建一个对象,但是 getBean 方法内部怎么知道"userService"对应的是 UserService 类呢?
所以,我们就可以分析出来,在调用 AnnotationConfigApplicationContext 的构造方法时,也就是第一行代码,会去做一些事情:
1. 解析 AppConfig.class,得到扫描路径
2. 遍历扫描路径下的所有 Java 类,如果发现某个类上存在@Component、@Service 等注解,那么 Spring 就把这个类记录下来,存在一个 Map 中,比如 Map<String, Class>。(实际上,Spring 源码中确实存在类似的这么一个 Map,叫做 BeanDefinitionMap,后续课程会讲到)
3. Spring 会根据某个规则生成当前类对应的 beanName,作为 key 存入 Map,当前类作为 value 这样,但调用 context.getBean("userService")时,就可以根据"userService"找到 UserService 类,从而就可以去创建对象了。
Bean 的创建过程那么 Spring 到底是如何来创建一个 Bean 的呢,这个就是 Bean 创建的生命周期,大致过程如下

### 1. 利用该类的构造方法来实例化得到一个对象(但是如何一个类中有多个构造方法,Spring 则会进行选择,
这个叫做推断构造方法)
2. 得到一个对象后,Spring 会判断该对象中是否存在被@Autowired 注解了的属性,把这些属性找出来并由 Spring 进行赋值(依赖注入)
3. 依赖注入后,Spring 会判断该对象是否实现了 BeanNameAware 接口、 BeanClassLoaderAware 接口、 BeanFactoryAware 接口,如果实现了,就表示当前对象必须实现该接口中所定义的 setBeanName()、setBeanClassLoader()、setBeanFactory()方法,那 Spring 就会调用这些方法并传入相应的参数(Aware 回调)
4. Aware 回调后,Spring 会判断该对象中是否存在某个方法被@PostConstruct 注解了,如果存在,Spring 会调用当前对象的此方法(初始化前)
5. 紧接着,Spring 会判断该对象是否实现了 InitializingBean 接口,如果实现了,就表示当前对象必须实现该接口中的 afterPropertiesSet()方法,那 Spring 就会调用当前对象中的 afterPropertiesSet()方法(初始化)
6. 最后,Spring 会判断当前对象需不需要进行 AOP,如果不需要那么 Bean 就创建完了,如果需要进行 AOP,则会进行动态代理并生成一个代理对象做为 Bean(初始化后)
通过最后一步,我们可以发现,当 Spring 根据 UserService 类来创建一个 Bean 时:
1. 如果不用进行 AOP,那么 Bean 就是 UserService 类的构造方法所得到的对象。
2. 如果需要进行 AOP,那么 Bean 就是 UserService 的代理类所实例化得到的对象,而不是 UserService 本身所得到的对象。
Bean 对象创建出来后:
1. 如果当前 Bean 是单例 Bean,那么会把该 Bean 对象存入一个 Map<String, Object>,Map 的 key 为 beanName,value 为 Bean 对象。这样下次 getBean 时就可以直接从 Map 中拿到对应的 Bean 对象了。
(实际上,在 Spring 源码中,这个 Map 就是单例池)
2. 如果当前 Bean 是原型 Bean,那么后续没有其他动作,不会存入一个 Map,下次 getBean 时会再次执行上述创建过程,得到一个新的 Bean 对象。
推断构造方法 Spring 在基于某个类生成 Bean 的过程中,需要利用该类的构造方法来实例化得到一个对象,但是如果一个类存在多个构造方法,Spring 会使用哪个呢?
Spring 的判断逻辑如下:
1. 如果一个类只存在一个构造方法,不管该构造方法是无参构造方法,还是有参构造方法,Spring 都会用这个构造方法
2. 如果一个类存在多个构造方法 i. 这些构造方法中,存在一个无参的构造方法,那么 Spring 就会用这个无参的构造方法 ii. 这些构造方法中,不存在一个无参的构造方法,那么 Spring 就会报错

Spring 的设计思想是这样的:
1. 如果一个类只有一个构造方法,那么没得选择,只能用这个构造方法
2. 如果一个类存在多个构造方法,Spring 不知道如何选择,就会看是否有无参的构造方法,因为无参构造方法本身表示了一种默认的意义
3. 不过如果某个构造方法上加了@Autowired 注解,那就表示程序员告诉 Spring 就用这个加了注解的方法,
那 Spring 就会用这个加了@Autowired 注解构造方法了需要重视的是,如果 Spring 选择了一个有参的构造方法,Spring 在调用这个有参构造方法时,需要传入参数,那这个参数是怎么来的呢?
Spring 会根据入参的类型和入参的名字去 Spring 中找 Bean 对象(以单例 Bean 为例,Spring 会从单例池那个 Map 中去找):
1. 先根据入参类型找,如果只找到一个,那就直接用来作为入参
2. 如果根据类型找到多个,则再根据入参名字来确定唯一一个
3. 最终如果没有找到,则会报错,无法创建当前 Bean 对象确定用哪个构造方法,确定入参的 Bean 对象,这个过程就叫做推断构造方法。
AOP 大致流程 AOP 就是进行动态代理,在创建一个 Bean 的过程中,Spring 在最后一步会去判断当前正在创建的这个 Bean 是不是需要进行 AOP,如果需要则会进行动态代理。
如何判断当前 Bean 对象需不需要进行 AOP:
1. 找出所有的切面 Bean
2. 遍历切面中的每个方法,看是否写了@Before、@After 等注解
3. 如果写了,则判断所对应的 Pointcut 是否和当前 Bean 对象的类是否匹配
4. 如果匹配则表示当前 Bean 对象有匹配的的 Pointcut,表示需要进行 AOP 利用 cglib 进行 AOP 的大致流程:
1. 生成代理类 UserServiceProxy,代理类继承 UserService
2. 代理类中重写了父类的方法,比如 UserService 中的 test()方法
3. 代理类中还会有一个 target 属性,该属性的值为被代理对象(也就是通过 UserService 类推断构造方法实例化出来的对象,进行了依赖注入、初始化等步骤的对象)
4. 代理类中的 test()方法被执行时的逻辑如下:
i. 执行切面逻辑(@Before)
ii. 调用 target.test()

当我们从 Spring 容器得到 UserService 的 Bean 对象时,拿到的就是 UserServiceProxy 所生成的对象,也就是代理对象。
UserService 代理对象.test()--->执行切面逻辑--->target.test(),注意 target 对象不是代理对象,而是被代理对象。
Spring 事务当我们在某个方法上加了@Transactional 注解后,就表示该方法在调用时会开启 Spring 事务,而这个方法所在的类所对应的 Bean 对象会是该类的代理对象。
Spring 事务的代理对象执行某个方法时的步骤:
1. 判断当前执行的方法是否存在@Transactional 注解
2. 如果存在,则利用事务管理器(TransactionMananger)新建一个数据库连接
3. 修改数据库连接的 autocommit 为 false
4. 执行 target.test(),执行程序员所写的业务逻辑代码,也就是执行 sql
5. 执行完了之后如果没有出现异常,则提交,否则回滚 Spring 事务是否会失效的判断标准:某个加了@Transactional 注解的方法被调用时,要判断到底是不是直接被代理对象调用的,如果是则事务会生效,如果不是则失效。
