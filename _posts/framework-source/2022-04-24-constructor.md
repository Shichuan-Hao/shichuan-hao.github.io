---

title: "Spring之推断构造方法源码解析"
description: "Spring 之推断构造方法源码解析.md..."
author: hsc
date: 2022-04-24 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis', 'IOC']
toc: true

---

09-Spring 之推断构造方法源码解析.md

推断构造方法流程图:https://www.processon.com/view/link/5f97bc717d9c0806f291d7ebAutowiredAnnotationBeanPostProcessor 中推断构造方法不同情况思维脑图:
一般情况下,一个类只有一个构造方法:
1. 要么是无参的构造方法
2. 要么是有参的构造方法如果只有一个无参的构造方法,那么实例化就只能使用这个构造方法了。
如果只有一个有参的构造方法,那么实例化时能使用这个构造方法吗?要分情况讨论:
1. 使用 AnnotationConfigApplicationContext,会使用这个构造方法进行实例化,那么 Spring 会根据构造方法的参数信息去寻找 bean,然后传给构造方法
2. 使用 ClassPathXmlApplicationContext,表示使用 XML 的方式来使用 bean,要么在 XML 中指定构造方法的参数值(手动指定),要么配置 autowire=constructor 让 Spring 自动去寻找 bean 做为构造方法参数值。
上面是只有一个构造方法的情况,那么如果有多个构造方法呢?
又分为两种情况,多个构造方法中存不存在无参的构造方法。
分析:一个类存在多个构造方法,那么 Spring 进行实例化之前,该如何去确定到底用哪个构造方法呢?
1. 如果开发者指定了想要使用的构造方法,那么就用这个构造方法
2. 如果开发者没有指定想要使用的构造方法,则看开发者有没有让 Spring 自动去选择构造方法
3. 如果开发者也没有让 Spring 自动去选择构造方法,则 Spring 利用无参构造方法,如果没有无参构造方法,
则报错针对第一点,开发者可以通过什么方式来指定使用哪个构造方法呢?
1. xml 中的<constructor-arg>标签,这个标签表示构造方法参数,所以可以根据这个确定想要使用的构造方法的参数个数,从而确定想要使用的构造方法
2. 通过@Autowired 注解,@Autowired 注解可以写在构造方法上,所以哪个构造方法上写了@Autowired 注解,表示开发者想使用哪个构造方法,当然,它和第一个方式的不同点是,通过 xml 的方式,我们直接指定了构造方法的参数值,而通过@Autowired 注解的方式,需要 Spring 通过 byType+byName 的方式去找到符合条件的 bean 作为构造方法的参数值

再来看第二点,如果开发者没有指定想要使用的构造方法,则看开发者有没有让 Spring 自动去选择构造方法,对于这一点,只能用在 ClassPathXmlApplicationContext,因为通过 AnnotationConfigApplicationContext 没有办法去指定某个 bean 可以自动去选择构造方法,而通过 ClassPathXmlApplicationContext 可以在 xml 中指定某个 bean 的 autowire 为 constructor,虽然这个属性表示通过构造方法自动注入,所以需要自动的去选择一个构造方法进行自动注入,因为是构造方法,所以顺便是进行实例化。
当然,还有一种情况,就是多个构造方法上写了@Autowired 注解,那么此时 Spring 会报错。
但是,因为@Autowired 还有一个属性 required,默认为 ture,所以一个类中,只有能一个构造方法标注了@Autowired 或@Autowired(required=true),有多个会报错。但是可以有多个@Autowired(required=false),这种情况下,需要 Spring 从这些构造方法中去自动选择一个构造方法。
源码思路
1. AbstractAutowireCapableBeanFactory 类中的 createBeanInstance()方法会去创建一个 Bean 实例
2. 根据 BeanDefinition 加载类得到 Class 对象
3. 如果 BeanDefinition 绑定了一个 Supplier,那就调用 Supplier 的 get 方法得到一个对象并直接返回
4. 如果 BeanDefinition 中存在 factoryMethodName,那么就调用该工厂方法得到一个 bean 对象并返回
5. 如果 BeanDefinition 已经自动构造过了,那就调用 autowireConstructor()自动构造一个对象
6. 调用 SmartInstantiationAwareBeanPostProcessor 的 determineCandidateConstructors()方法得到哪些构造方法是可以用的
7. 如果存在可用得构造方法,或者当前 BeanDefinition 的 autowired 是 AUTOWIRE_CONSTRUCTOR,或者 BeanDefinition 中指定了构造方法参数值,或者创建 Bean 的时候指定了构造方法参数值,那么就调用**autowireConstructor()**方法自动构造一个对象
8. 最后,如果不是上述情况,就根据无参的构造方法实例化一个对象 autowireConstructor()
1. 先检查是否指定了具体的构造方法和构造方法参数值,或者在 BeanDefinition 中缓存了具体的构造方法或构造方法参数值,如果存在那么则直接使用该构造方法进行实例化
2. 如果没有确定的构造方法或构造方法参数值,那么 i. 如果没有确定的构造方法,那么则找出类中所有的构造方法 ii. 如果只有一个无参的构造方法,那么直接使用无参的构造方法进行实例化 iii. 如果有多个可用的构造方法或者当前 Bean 需要自动通过构造方法注入 iv. 根据所指定的构造方法参数值,确定所需要的最少的构造方法参数值的个数 v. 对所有的构造方法进行排序,参数个数多的在前面 vi. 遍历每个构造方法 vii. 如果不是调用 getBean 方法时所指定的构造方法参数值,那么则根据构造方法参数类型找值 viii. 如果时调用 getBean 方法时所指定的构造方法参数值,就直接利用这些值 ix. 如果根据当前构造方法找到了对应的构造方法参数值,那么这个构造方法就是可用的,但是不一定这个构造方法就是最佳的,所以这里会涉及到是否有多个构造方法匹配了同样的值,这个时候就会用值和构造方法类型进行匹配程度的打分,找到一个最匹配的

为什么分越少优先级越高?
主要是计算找到的 bean 和构造方法参数类型匹配程度有多高。
假设 bean 的类型为 A,A 的父类是 B,B 的父类是 C,同时 A 实现了接口 D 如果构造方法的参数类型为 A,那么完全匹配,得分为 0 如果构造方法的参数类型为 B,那么得分为 2 如果构造方法的参数类型为 C,那么得分为 4 如果构造方法的参数类型为 D,那么得分为 1 可以直接使用如下代码进行测试:
Object[] objects = new Object[]{new A()};
// 0System.out.println(MethodInvoker.getTypeDifferenceWeight(new Class[]{A.class}, objects));
// 2System.out.println(MethodInvoker.getTypeDifferenceWeight(new Class[]{B.class}, objects));
// 4System.out.println(MethodInvoker.getTypeDifferenceWeight(new Class[]{C.class}, objects));
// 1System.out.println(MethodInvoker.getTypeDifferenceWeight(new Class[]{D.class}, objects));
所以,我们可以发现,越匹配分数越低。
@Bean 的情况首先,Spring 会把@Bean 修饰的方法解析成 BeanDefinition:
1. 如果方法是 static 的,那么解析出来的 BeanDefinition 中:
i. factoryBeanName 为 AppConfig 所对应的 beanName,比如"appConfig"
ii. factoryMethodName 为对应的方法名,比如"aService"
iii. factoryClass 为 AppConfig.class
2. 如果方法不是 static 的,那么解析出来的 BeanDefinition 中:
i. factoryBeanName 为 nullii. factoryMethodName 为对应的方法名,比如"aService"
iii. factoryClass 也为 AppConfig.class 在由@Bean 生成的 BeanDefinition 中,有一个重要的属性 isFactoryMethodUnique,表示 factoryMethod 是不是唯一的,在普通情况下@Bean 生成的 BeanDefinition 的 isFactoryMethodUnique 为 true,但是如果出现了方法重载,那么就是特殊的情况,比如:

@Beanpublic static AService aService(){return new AService();
}@Beanpublic AService aService(BService bService){return new AService();
}虽然有两个@Bean,但是肯定只会生成一个 aService 的 Bean,那么 Spring 在处理@Bean 时,也只会生成一个 aService 的 BeanDefinition,比如 Spring 先解析到第一个@Bean,会生成一个 BeanDefinition,此时 isFactoryMethodUnique 为 true,但是解析到第二个@Bean 时,会判断出来 beanDefinitionMap 中已经存在一个 aService 的 BeanDefinition 了,那么会把之前的这个 BeanDefinition 的 isFactoryMethodUnique 修改为 false,并且不会生成新的 BeanDefinition 了。
并且后续在根据 BeanDefinition 创建 Bean 时,会根据 isFactoryMethodUnique 来操作,如果为 true,那就表示当前 BeanDefinition 只对应了一个方法,那也就是只能用这个方法来创建 Bean 了,但是如果 isFactoryMethodUnique 为 false,那就表示当前 BeanDefition 对应了多个方法,需要和推断构造方法的逻辑一样,去选择用哪个方法来创建 Bean。
