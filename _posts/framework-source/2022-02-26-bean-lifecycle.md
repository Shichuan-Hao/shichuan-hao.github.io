---



title: "Spring之Bean生命周期源码解析上"
description: "Spring 之 Bean 生命周期源码解析上.md"
author: hsc
date: 2022-02-26 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis', 'IOC', 'AOP']
toc: true



---

04-Spring 之 Bean 生命周期源码解析上.md

Spring 最重要的功能就是帮助程序员创建对象(也就是 IOC),而启动 Spring 就是为创建 Bean 对象做准备,所以我们先明白 Spring 到底是怎么去创建 Bean 的,也就是先弄明白 Bean 的生命周期。
Bean 的生命周期就是指:在 Spring 中,一个 Bean 是如何生成的,如何销毁的 Bean 生命周期流程图:https://www.processon.com/view/link/5f8588c87d9c0806f27358c1 附带资料 JFR 介绍:https://zhuanlan.zhihu.com/p/122247741Bean 的生成过程
1. 生成 BeanDefinitionSpring 启动的时候会进行扫描,会先调用 org.springframework.context.annotation.ClassPathScanningCandidateComponentProvider#scanCandidateComponents(String basePackage)
扫描某个包路径,并得到 BeanDefinition 的 Set 集合。
关于 Spring 启动流程,后续会单独的课详细讲,这里先讲一下 Spring 扫描的底层实现:
Spring 扫描底层流程:https://www.processon.com/view/link/61370ee60e3e7412ecd95d43
1. 首先,通过 ResourcePatternResolver 获得指定包路径下的所有.class 文件(Spring 源码中将此文件包装成了 Resource 对象)
2. 遍历每个 Resource 对象
3. 利用 MetadataReaderFactory 解析 Resource 对象得到 MetadataReader(在 Spring 源码中 MetadataReaderFactory 具体的实现类为 CachingMetadataReaderFactory,MetadataReader 的具体实现类为 SimpleMetadataReader)
4. 利用 MetadataReader 进行 excludeFilters 和 includeFilters,以及条件注解@Conditional 的筛选(条件注解并不能理解:某个类上是否存在@Conditional 注解,如果存在则调用注解中所指定的类的 match 方法进行匹配,匹配成功则通过筛选,匹配失败则 pass 掉。)
5. 筛选通过后,基于 metadataReader 生成 ScannedGenericBeanDefinition
6. 再基于 metadataReader 判断是不是对应的类是不是接口或抽象类
7. 如果筛选通过,那么就表示扫描到了一个 Bean,将 ScannedGenericBeanDefinition 加入结果集 MetadataReader 表示类的元数据读取器,主要包含了一个 AnnotationMetadata,功能有

### 1. 获取类的名字、
### 2. 获取父类的名字
### 3. 获取所实现的所有接口名
### 4. 获取所有内部类的名字
### 5. 判断是不是抽象类
### 6. 判断是不是接口
### 7. 判断是不是一个注解
### 8. 获取拥有某个注解的方法集合
### 9. 获取类上添加的所有注解信息
### 10. 获取类上添加的所有注解类型集合值得注意的是,CachingMetadataReaderFactory 解析某个.class 文件得到 MetadataReader 对象是利用的 ASM 技术,并没有加载这个类到 JVM。并且,最终得到的 ScannedGenericBeanDefinition 对象,beanClass 属性存储的是当前类的名字,而不是 class 对象。(beanClass 属性的类型是 Object,它即可以存储类的名字,
也可以存储 class 对象)
最后,上面是说的通过扫描得到 BeanDefinition 对象,我们还可以通过直接定义 BeanDefinition,或解析 spring.xml 文件的<bean/>,或者@Bean 注解得到 BeanDefinition 对象。(后续课程会分析@Bean 注解是怎么生成 BeanDefinition 的)。
2. 合并 BeanDefinition 通过扫描得到所有 BeanDefinition 之后,就可以根据 BeanDefinition 创建 Bean 对象了,但是在 Spring 中支持父子 BeanDefinition,和 Java 父子类类似,但是完全不是一回事。
父子 BeanDefinition 实际用的比较少,使用是这样的,比如:
<bean id="parent" class="com.zhouyu.service.Parent" scope="prototype"/><bean id="child" class="com.zhouyu.service.Child"/>这么定义的情况下,child 是单例 Bean。
<bean id="parent" class="com.zhouyu.service.Parent" scope="prototype"/><bean id="child" class="com.zhouyu.service.Child" parent="parent"/>但是这么定义的情况下,child 就是原型 Bean 了。
因为 child 的父 BeanDefinition 是 parent,所以会继承 parent 上所定义的 scope 属性。
而在根据 child 来生成 Bean 对象之前,需要进行 BeanDefinition 的合并,得到完整的 child 的 BeanDefinition。

### 3. 加载类 BeanDefinition 合并之后,就可以去创建 Bean 对象了,而创建 Bean 就必须实例化对象,而实例化就必须先加载当前 BeanDefinition 所对应的 class,在 AbstractAutowireCapableBeanFactory 类的 createBean()方法中,
一开始就会调用:
Class<?> resolvedClass = resolveBeanClass(mbd, beanName);
这行代码就是去加载类,该方法是这么实现的:
if (mbd.hasBeanClass()) {return mbd.getBeanClass();
}if (System.getSecurityManager() != null) {return AccessController.doPrivileged((PrivilegedExceptionAction<Class<?>>) () ->doResolveBeanClass(mbd, typesToMatch), getAccessControlContext());
}else {return doResolveBeanClass(mbd, typesToMatch);
}public boolean hasBeanClass() {return (this.beanClass instanceof Class);
}如果 beanClass 属性的类型是 Class,那么就直接返回,如果不是,则会根据类名进行加载(doResolveBeanClass 方法所做的事情)
会利用 BeanFactory 所设置的类加载器来加载类,如果没有设置,则默认使用**ClassUtils.getDefaultClassLoader()**所返回的类加载器来加载。
ClassUtils.getDefaultClassLoader()
1. 优先返回当前线程中的 ClassLoader
2. 线程中类加载器为 null 的情况下,返回 ClassUtils 类的类加载器
3. 如果 ClassUtils 类的类加载器为空,那么则表示是 Bootstrap 类加载器加载的 ClassUtils 类,那么则返回系统类加载器
4. 实例化前当前 BeanDefinition 对应的类成功加载后,就可以实例化对象了,但是...
在 Spring 中,实例化对象之前,Spring 提供了一个扩展点,允许用户来控制是否在某个或某些 Bean 实例化之前做一些启动动作。这个扩展点叫 InstantiationAwareBeanPostProcessor.postProcessBeforeInstantiation()。比如:

@Componentpublic class ZhouyuBeanPostProcessor implements InstantiationAwareBeanPostProcessor {@Overridepublic Object postProcessBeforeInstantiation(Class<?> beanClass, StringbeanName) throws BeansException {if ("userService".equals(beanName)) {System.out.println("实例化前");
}return null;
}}如上代码会导致,在 userService 这个 Bean 实例化前,会进行打印。
值得注意的是,postProcessBeforeInstantiation()是有返回值的,如果这么实现:
@Componentpublic class ZhouyuBeanPostProcessor implements InstantiationAwareBeanPostProcessor {@Overridepublic Object postProcessBeforeInstantiation(Class<?> beanClass, StringbeanName) throws BeansException {if ("userService".equals(beanName)) {System.out.println("实例化前");
return new UserService();
}return null;
}}userService 这个 Bean,在实例化前会直接返回一个由我们所定义的 UserService 对象。如果是这样,表示不需要 Spring 来实例化了,并且后续的 Spring 依赖注入也不会进行了,会跳过一些步骤,直接执行初始化后这一步。
5. 实例化在这个步骤中就会根据 BeanDefinition 去创建一个对象了。
5.1 Supplier 创建对象首先判断 BeanDefinition 中是否设置了 Supplier,如果设置了则调用 Supplier 的 get()得到对象。
得直接使用 BeanDefinition 对象来设置 Supplier,比如:

AbstractBeanDefinition beanDefinition = BeanDefinitionBuilder.genericBeanDefinition().getBeanDefinition();
beanDefinition.setInstanceSupplier(new Supplier<Object>() {@Overridepublic Object get() {return new UserService();
}});
context.registerBeanDefinition("userService", beanDefinition);
5.2 工厂方法创建对象如果没有设置 Supplier,则检查 BeanDefinition 中是否设置了 factoryMethod,也就是工厂方法,有两种方式可以设置 factoryMethod,比如:
方式一:
<bean id="userService" class="com.zhouyu.service.UserService" factorymethod="createUserService" />对应的 UserService 类为:
public class UserService {public static UserService createUserService() {System.out.println("执行 createUserService()");
UserService userService = new UserService();
return userService;
}public void test() {System.out.println("test");
}}方式二:
<bean id="commonService" class="com.zhouyu.service.CommonService"/><bean id="userService1" factory-bean="commonService" factory-method="createUserService" />对应的 CommonService 的类为:

public class CommonService {public UserService createUserService() {return new UserService();
}}Spring 发现当前 BeanDefinition 方法设置了工厂方法后,就会区分这两种方式,然后调用工厂方法得到对象。
值得注意的是,我们通过@Bean 所定义的 BeanDefinition,是存在 factoryMethod 和 factoryBean 的,也就是和上面的方式二非常类似,@Bean 所注解的方法就是 factoryMethod,AppConfig 对象就是 factoryBean。
如果@Bean 所所注解的方法是 static 的,那么对应的就是方式一。
5.3 推断构造方法第一节已经讲过一遍大概原理了,后面有一节课单独分析源码实现。推断完构造方法后,就会使用构造方法来进行实例化了。
额外的,在推断构造方法逻辑中除开会去选择构造方法以及查找入参对象意外,会还判断是否在对应的类中是否存在使用**@Lookup 注解**了方法。如果存在则把该方法封装为 LookupOverride 对象并添加到 BeanDefinition 中。
在实例化时,如果判断出来当前 BeanDefinition 中没有 LookupOverride,那就直接用构造方法反射得到一个实例对象。如果存在 LookupOverride 对象,也就是类中存在@Lookup 注解了的方法,那就会生成一个代理对象。
@Lookup 注解就是方法注入,使用 demo 如下:
@Componentpublic class UserService {private OrderService orderService;
public void test() {OrderService orderService = createOrderService();
System.out.println(orderService);
}@Lookup("orderService")
public OrderService createOrderService() {return null;
}}

### 6. BeanDefinition 的后置处理 Bean 对象实例化出来之后,接下来就应该给对象的属性赋值了。在真正给属性赋值之前,Spring 又提供了一个扩展点 MergedBeanDefinitionPostProcessor.postProcessMergedBeanDefinition(),可以对此时的 BeanDefinition 进行加工,比如:
@Componentpublic class ZhouyuMergedBeanDefinitionPostProcessor implements MergedBeanDefinitionPostProcessor{@Overridepublic void postProcessMergedBeanDefinition(RootBeanDefinition beanDefinition, Class<?> beanType,String beanName) {if ("userService".equals(beanName)) {beanDefinition.getPropertyValues().add("orderService", new OrderService());
}}}在 Spring 源码中,AutowiredAnnotationBeanPostProcessor 就是一个 MergedBeanDefinitionPostProcessor,它的 postProcessMergedBeanDefinition()中会去查找注入点,并缓存在 AutowiredAnnotationBeanPostProcessor 对象的一个 Map 中(injectionMetadataCache)。
7. 实例化后在处理完 BeanDefinition 后,Spring 又设计了一个扩展点:
InstantiationAwareBeanPostProcessor.postProcessAfterInstantiation(),比如:
@Componentpublic class ZhouyuInstantiationAwareBeanPostProcessor implements InstantiationAwareBeanPostProcessor {@Overridepublic boolean postProcessAfterInstantiation(Object bean, String beanName) throws BeansException{if ("userService".equals(beanName)) {UserService userService = (UserService) bean;
userService.test();
}return true;
}}上述代码就是对 userService 所实例化出来的对象进行处理。
这个扩展点,在 Spring 源码中基本没有怎么使用。

### 8. 自动注入这里的自动注入指的是 Spring 的自动注入,后续依赖注入课程中单独讲
### 9. 处理属性这个步骤中,就会处理@Autowired、@Resource、@Value 等注解,也是通过**InstantiationAwareBeanPostProcessor.postProcessProperties()**扩展点来实现的,比如我们甚至可以实现一个自己的自动注入功能,比如:
@Componentpublic class ZhouyuInstantiationAwareBeanPostProcessor implements InstantiationAwareBeanPostProcessor {@Overridepublic PropertyValues postProcessProperties(PropertyValues pvs, Object bean, StringbeanName) throws BeansException {if ("userService".equals(beanName)) {for (Field field : bean.getClass().getFields()) {if (field.isAnnotationPresent(ZhouyuInject.class)) {field.setAccessible(true);
try {field.set(bean, "123");
} catch (IllegalAccessException e) {e.printStackTrace();
}}}}return pvs;
}}关于@Autowired、@Resource、@Value 的底层源码,会在后续的依赖注入课程中详解。
10. 执行 Aware 完成了属性赋值之后,Spring 会执行一些回调,包括:
1. BeanNameAware:回传 beanName 给 bean 对象。
2. BeanClassLoaderAware:回传 classLoader 给 bean 对象。
3. BeanFactoryAware:回传 beanFactory 给对象。
11. 初始化前初始化前,也是 Spring 提供的一个扩展点:BeanPostProcessor.postProcessBeforeInitialization(),比如

@Componentpublic class ZhouyuBeanPostProcessor implements BeanPostProcessor {@Overridepublic Object postProcessBeforeInitialization(Object bean, String beanName) throws BeansException{if ("userService".equals(beanName)) {System.out.println("初始化前");
}return bean;
}}利用初始化前,可以对进行了依赖注入的 Bean 进行处理。
在 Spring 源码中:
1. InitDestroyAnnotationBeanPostProcessor 会在初始化前这个步骤中执行@PostConstruct 的方法,
2. ApplicationContextAwareProcessor 会在初始化前这个步骤中进行其他 Aware 的回调:
i. EnvironmentAware:回传环境变量 ii. EmbeddedValueResolverAware:回传占位符解析器 iii. ResourceLoaderAware:回传资源加载器 iv. ApplicationEventPublisherAware:回传事件发布器 v. MessageSourceAware:回传国际化资源 vi. ApplicationStartupAware:回传应用其他监听对象,可忽略 vii. ApplicationContextAware:回传 Spring 容器 ApplicationContext
12. 初始化
1. 查看当前 Bean 对象是否实现了 InitializingBean 接口,如果实现了就调用其 afterPropertiesSet()方法
2. 执行 BeanDefinition 中指定的初始化方法
13. 初始化后这是 Bean 创建生命周期中的最后一个步骤,也是 Spring 提供的一个扩展点:
BeanPostProcessor.postProcessAfterInitialization(),比如:

@Componentpublic class ZhouyuBeanPostProcessor implements BeanPostProcessor {@Overridepublic Object postProcessAfterInitialization(Object bean, String beanName) throws BeansException{if ("userService".equals(beanName)) {System.out.println("初始化后");
}return bean;
}}可以在这个步骤中,对 Bean 最终进行处理,Spring 中的 AOP 就是基于初始化后实现的,初始化后返回的对象才是最终的 Bean 对象。
总结 BeanPostProcessor
1. InstantiationAwareBeanPostProcessor.postProcessBeforeInstantiation()
2. 实例化
3. MergedBeanDefinitionPostProcessor.postProcessMergedBeanDefinition()
4. InstantiationAwareBeanPostProcessor.postProcessAfterInstantiation()
5. 自动注入
6. InstantiationAwareBeanPostProcessor.postProcessProperties()
7. Aware 对象
8. BeanPostProcessor.postProcessBeforeInitialization()
9. 初始化
10. BeanPostProcessor.postProcessAfterInitialization()
