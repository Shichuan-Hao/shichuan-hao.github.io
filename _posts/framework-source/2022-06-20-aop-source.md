---


title: "Spring之AOP底层源码解析（上）"
description: "Spring 之 AOP 底层源码解析(上).md"
author: hsc
date: 2022-06-20 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis', 'IOC', 'AOP']
toc: true


---

14-Spring 之 AOP 底层源码解析(上).md

动态代理代理模式的解释:为其他对象提供一种代理以控制对这个对象的访问,增强一个类中的某个方法,对程序进行扩展。
比如,现在存在一个 UserService 类:
public class UserService {public void test() {System.out.println("test...");
}}此时,我们 new 一个 UserService 对象,然后执行 test()方法,结果是显而易见的。
如果我们现在想在不修改 UserService 类的源码前提下,给 test()增加额外逻辑,那么就可以使用动态代理机制来创建 UserService 对象了,比如:
UserService target = new UserService();
// 通过 cglib 技术 Enhancer enhancer = new Enhancer();
enhancer.setSuperclass(UserService.class);
// 定义额外逻辑,也就是代理逻辑 enhancer.setCallbacks(new Callback[]{new MethodInterceptor() {@Overridepublic Object intercept(Object o, Method method, Object[] objects, MethodProxymethodProxy) throws Throwable {System.out.println("before...");
Object result = methodProxy.invoke(target, objects);
System.out.println("after...");
return result;
}}});
// 动态代理所创建出来的 UserService 对象 UserService userService = (UserService) enhancer.create();
// 执行这个 userService 的 test 方法时,就会额外会执行一些其他逻辑 userService.test();
得到的都是 UserService 对象,但是执行 test()方法时的效果却不一样了,这就是代理所带来的效果。

上面是通过 cglib 来实现的代理对象的创建,是基于父子类的,被代理类(UserService)是父类,代理类是子类,代理对象就是代理类的实例对象,代理类是由 cglib 创建的,对于程序员来说不用关心。
除开 cglib 技术,jdk 本身也提供了一种创建代理对象的动态代理机制,但是它只能代理接口,也就是 UserService 得先有一个接口才能利用 jdk 动态代理机制来生成一个代理对象,比如:
public interface UserInterface {public void test();
}public class UserService implements UserInterface {public void test() {System.out.println("test...");
}}利用 JDK 动态代理来生成一个代理对象:
UserService target = new UserService();
// UserInterface 接口的代理对象 Object proxy = Proxy.newProxyInstance(UserService.class.getClassLoader(), new Class[]{UserInterface.class}, new InvocationHandler() {@Overridepublic Object invoke(Object proxy, Method method, Object[] args) throws Throwable {System.out.println("before...");
Object result = method.invoke(target, args);
System.out.println("after...");
return result;
}});
UserInterface userService = (UserInterface) proxy;
userService.test();
如果你把 new Class[]{UserInterface.class},替换成 new Class[]{UserService.class},允许代码会直接报错:
Exception in thread "main" java.lang.IllegalArgumentException: com.zhouyu.service.UserService isnot an interface 表示一定要是个接口。
由于这个限制,所以产生的代理对象的类型是 UserInterface,而不是 UserService,这是需要注意的。
ProxyFactory

上面我们介绍了两种动态代理技术,那么在 Spring 中进行了封装,封装出来的类叫做 ProxyFactory,表示是创建代理对象的一个工厂,使用起来会比上面的更加方便,比如:
UserService target = new UserService();
ProxyFactory proxyFactory = new ProxyFactory();
proxyFactory.setTarget(target);
proxyFactory.addAdvice(new MethodInterceptor() {@Overridepublic Object invoke(MethodInvocation invocation) throws Throwable {System.out.println("before...");
Object result = invocation.proceed();
System.out.println("after...");
return result;
}});
UserInterface userService = (UserInterface) proxyFactory.getProxy();
userService.test();
通过 ProxyFactory,我们可以不再关系到底是用 cglib 还是 jdk 动态代理了,ProxyFactory 会帮我们去判断,如果 UserService 实现了接口,那么 ProxyFactory 底层就会用 jdk 动态代理,如果没有实现接口,就会用 cglib 技术,上面的代码,就是由于 UserService 实现了 UserInterface 接口,所以最后产生的代理对象是 UserInterface 类型。
Advice 的分类
1. Before Advice:方法之前执行
2. After returning advice:方法 return 后执行
3. After throwing advice:方法抛异常后执行
4. After (finally) advice:方法执行完 finally 之后执行,这是最后的,比 return 更后
5. Around advice:这是功能最强大的 Advice,可以自定义执行顺序看课上给的代码例子将一目了然 Advisor 的理解跟 Advice 类似的还有一个 Advisor 的概念,一个 Advisor 是有一个 Pointcut 和一个 Advice 组成的,通过 Pointcut 可以指定要需要被代理的逻辑,比如一个 UserService 类中有两个方法,按上面的例子,这两个方法都会被代理,被增强,那么我们现在可以通过 Advisor,来控制到具体代理哪一个方法,比如:

UserService target = new UserService();
ProxyFactory proxyFactory = new ProxyFactory();
proxyFactory.setTarget(target);
proxyFactory.addAdvisor(new PointcutAdvisor() {@Overridepublic Pointcut getPointcut() {return new StaticMethodMatcherPointcut() {@Overridepublic boolean matches(Method method, Class<?> targetClass) {return method.getName().equals("testAbc");
}};
}@Overridepublic Advice getAdvice() {return new MethodInterceptor() {@Overridepublic Object invoke(MethodInvocation invocation) throws Throwable {System.out.println("before...");
Object result = invocation.proceed();
System.out.println("after...");
return result;
}};
}@Overridepublic boolean isPerInstance() {return false;
}});
UserInterface userService = (UserInterface) proxyFactory.getProxy();
userService.test();
上面代码表示,产生的代理对象,只有在执行 testAbc 这个方法时才会被增强,会执行额外的逻辑,而在执行其他方法时是不会增强的。
创建代理对象的方式上面介绍了 Spring 中所提供了 ProxyFactory、Advisor、Advice、PointCut 等技术来实现代理对象的创建,但是我们在使用 Spring 时,我们并不会直接这么去使用 ProxyFactory,比如说,我们希望 ProxyFactory 所产生的代理对象能直接就是 Bean,能直接从 Spring 容器中得到 UserSerivce 的代理对象,而这些,Spring 都是支持的,只不过,作为开发者的我们肯定得告诉 Spring,那些类需要被代理,代理逻辑是什么。
ProxyFactoryBean

@Beanpublic ProxyFactoryBean userServiceProxy(){UserService userService = new UserService();
ProxyFactoryBean proxyFactoryBean = new ProxyFactoryBean();
proxyFactoryBean.setTarget(userService);
proxyFactoryBean.addAdvice(new MethodInterceptor() {@Overridepublic Object invoke(MethodInvocation invocation) throws Throwable {System.out.println("before...");
Object result = invocation.proceed();
System.out.println("after...");
return result;
}});
return proxyFactoryBean;
}通过这种方法来定义一个 UserService 的 Bean,并且是经过了 AOP 的。但是这种方式只能针对某一个 Bean。
它是一个 FactoryBean,所以利用的就是 FactoryBean 技术,间接的将 UserService 的代理对象作为了 Bean。
ProxyFactoryBean 还有额外的功能,比如可以把某个 Advise 或 Advisor 定义成为 Bean,然后在 ProxyFactoryBean 中进行设置@Beanpublic MethodInterceptor zhouyuAroundAdvise(){return new MethodInterceptor() {@Overridepublic Object invoke(MethodInvocation invocation) throws Throwable {System.out.println("before...");
Object result = invocation.proceed();
System.out.println("after...");
return result;
}};
}@Beanpublic ProxyFactoryBean userService(){UserService userService = new UserService();
ProxyFactoryBean proxyFactoryBean = new ProxyFactoryBean();
proxyFactoryBean.setTarget(userService);
proxyFactoryBean.setInterceptorNames("zhouyuAroundAdvise");
return proxyFactoryBean;
}BeanNameAutoProxyCreator

ProxyFactoryBean 得自己指定被代理的对象,那么我们可以通过 BeanNameAutoProxyCreator 来通过指定某个 bean 的名字,来对该 bean 进行代理@Beanpublic BeanNameAutoProxyCreator beanNameAutoProxyCreator() {BeanNameAutoProxyCreator beanNameAutoProxyCreator = new BeanNameAutoProxyCreator();
beanNameAutoProxyCreator.setBeanNames("userSe*");
beanNameAutoProxyCreator.setInterceptorNames("zhouyuAroundAdvise");
beanNameAutoProxyCreator.setProxyTargetClass(true);
return beanNameAutoProxyCreator;
}通过 BeanNameAutoProxyCreator 可以对批量的 Bean 进行 AOP,并且指定了代理逻辑,指定了一个 InterceptorName,也就是一个 Advise,前提条件是这个 Advise 也得是一个 Bean,这样 Spring 才能找到的,但是 BeanNameAutoProxyCreator 的缺点很明显,它只能根据 beanName 来指定想要代理的 Bean。
DefaultAdvisorAutoProxyCreator@Beanpublic DefaultPointcutAdvisor defaultPointcutAdvisor(){NameMatchMethodPointcut pointcut = new NameMatchMethodPointcut();
pointcut.addMethodName("test");
DefaultPointcutAdvisor defaultPointcutAdvisor = new DefaultPointcutAdvisor();
defaultPointcutAdvisor.setPointcut(pointcut);
defaultPointcutAdvisor.setAdvice(new ZhouyuAfterReturningAdvise());
return defaultPointcutAdvisor;
}@Beanpublic DefaultAdvisorAutoProxyCreator defaultAdvisorAutoProxyCreator() {DefaultAdvisorAutoProxyCreator defaultAdvisorAutoProxyCreator = new DefaultAdvisorAutoProxyCreator();
return defaultAdvisorAutoProxyCreator;
}通过 DefaultAdvisorAutoProxyCreator 会直接去找所有 Advisor 类型的 Bean,根据 Advisor 中的 PointCut 和 Advice 信息,确定要代理的 Bean 以及代理逻辑。
但是,我们发现,通过这种方式,我们得依靠某一个类来实现定义我们的 Advisor,或者 Advise,或者 Pointcut,那么这个步骤能不能更加简化一点呢?
对的,通过注解!
比如我们能不能只定义一个类,然后通过在类中的方法上通过某些注解,来定义 PointCut 以及 Advice,可以的,比如:

@Aspect@Componentpublic class ZhouyuAspect {@Before("execution(public void com.zhouyu.service.UserService.test())")
public void zhouyuBefore(JoinPoint joinPoint) {System.out.println("zhouyuBefore");
}}通过上面这个类,我们就直接定义好了所要代理的方法(通过一个表达式),以及代理逻辑(被@Before 修饰的方法),简单明了,这样对于 Spring 来说,它要做的就是来解析这些注解了,解析之后得到对应的 Pointcut 对象、 Advice 对象,生成 Advisor 对象,扔进 ProxyFactory 中,进而产生对应的代理对象,具体怎么解析这些注解就是**@EnableAspectJAutoProxy 注解**所要做的事情了,后面详细分析。
对 Spring AOP 的理解 OOP 表示面向对象编程,是一种编程思想,AOP 表示面向切面编程,也是一种编程思想,而我们上面所描述的就是 Spring 为了让程序员更加方便的做到面向切面编程所提供的技术支持,换句话说,就是 Spring 提供了一套机制,可以让我们更加容易的来进行 AOP,所以这套机制我们也可以称之为 Spring AOP。
但是值得注意的是,上面所提供的注解的方式来定义 Pointcut 和 Advice,Spring 并不是首创,首创是 AspectJ,而且也不仅仅只有 Spring 提供了一套机制来支持 AOP,还有比如 JBoss 4.0、aspectwerkz 等技术都提供了对于 AOP 的支持。而刚刚说的注解的方式,Spring 是依赖了 AspectJ 的,或者说,Spring 是直接把 AspectJ 中所定义的那些注解直接拿过来用,自己没有再重复定义了,不过也仅仅只是把注解的定义赋值过来了,每个注解具体底层是怎么解析的,还是 Spring 自己做的,所以我们在用 Spring 时,如果你想用@Before、@Around 等注解,是需要单独引入 aspecj 相关 jar 包的,比如:
compile group: 'org.aspectj', name: 'aspectjrt', version: '1.9.5'compile group: 'org.aspectj', name: 'aspectjweaver', version: '1.9.5'值得注意的是:AspectJ 是在编译时对字节码进行了修改,是直接在 UserService 类对应的字节码中进行增强的,也就是可以理解为是在编译时就会去解析@Before 这些注解,然后得到代理逻辑,加入到被代理的类中的字节码中去的,所以如果想用 AspectJ 技术来生成代理对象 ,是需要用单独的 AspectJ 编译器的。我们在项目中很少这么用,我们仅仅只是用了@Before 这些注解,而我们在启动 Spring 的过程中,Spring 会去解析这些注解,然后利用动态代理机制生成代理对象的。
IDEA 中使用 Aspectj:https://blog.csdn.net/gavin_john/article/details/80156963AOP 中的概念上面我们已经提到 Advisor、Advice、PointCut 等概念了,还有一些其他的概念,首先关于 AOP 中的概念本身是比较难理解的,Spring 官网上是这么说的:

Let us begin by defining some central AOP concepts and terminology. These terms are notSpring-specific. Unfortunately, AOP terminology is not particularly intuitive. However, it wouldbe even more confusing if Spring used its own terminology 意思是,AOP 中的这些概念不是 Spring 特有的,不幸的是,AOP 中的概念不是特别直观的,但是,如果 Spring 重新定义自己的那可能会导致更加混乱
1. Aspect:表示切面,比如被@Aspect 注解的类就是切面,可以在切面中去定义 Pointcut、Advice 等等
2. Join point:表示连接点,表示一个程序在执行过程中的一个点,比如一个方法的执行,比如一个异常的处理,在 Spring AOP 中,一个连接点通常表示一个方法的执行。
3. Advice:表示通知,表示在一个特定连接点上所采取的动作。 Advice 分为不同的类型,后面详细讨论,在很多 AOP 框架中,包括 Spring,会用 Interceptor 拦截器来实现 Advice,并且在连接点周围维护一个 Interceptor 链
4. Pointcut:表示切点,用来匹配一个或多个连接点,Advice 与切点表达式是关联在一起的,Advice 将会执行在和切点表达式所匹配的连接点上
5. Introduction:可以使用@DeclareParents 来给所匹配的类添加一个接口,并指定一个默认实现
6. Target object:目标对象,被代理对象
7. AOP proxy:表示代理工厂,用来创建代理对象的,在 Spring Framework 中,要么是 JDK 动态代理,要么是 CGLIB 代理
8. Weaving:表示织入,表示创建代理对象的动作,这个动作可以发生在编译时期(比如 Aspejctj),或者运行时,比如 Spring AOPAdvice 在 Spring AOP 中对应 API 上面说到的 Aspject 中的注解,其中有五个是用来定义 Advice 的,表示代理逻辑,以及执行时机:
1. @Before
2. @AfterReturning
3. @AfterThrowing
4. @After
5. @Around 我们前面也提到过,Spring 自己也提供了类似的执行实际的实现类:
1. 接口 MethodBeforeAdvice,继承了接口 BeforeAdvice
2. 接口 AfterReturningAdvice
3. 接口 ThrowsAdvice
4. 接口 AfterAdvice
5. 接口 MethodInterceptor

Spring 会把五个注解解析为对应的 Advice 类:
1. @Before:AspectJMethodBeforeAdvice,实际上就是一个 MethodBeforeAdvice
2. @AfterReturning:AspectJAfterReturningAdvice,实际上就是一个 AfterReturningAdvice
3. @AfterThrowing:AspectJAfterThrowingAdvice,实际上就是一个 MethodInterceptor
4. @After:AspectJAfterAdvice,实际上就是一个 MethodInterceptor
5. @Around:AspectJAroundAdvice,实际上就是一个 MethodInterceptorTargetSource 的使用在我们日常的 AOP 中,被代理对象就是 Bean 对象,是由 BeanFactory 给我们创建出来的,但是 Spring AOP 中提供了 TargetSource 机制,可以让我们用来自定义逻辑来创建被代理对象。
比如之前所提到的@Lazy 注解,当加在属性上时,会产生一个代理对象赋值给这个属性,产生代理对象的代码为:

protected Object buildLazyResolutionProxy(final DependencyDescriptordescriptor, final @Nullable String beanName) {BeanFactory beanFactory = getBeanFactory();
Assert.state(beanFactory instanceof DefaultListableBeanFactory,"BeanFactory needs to be a DefaultListableBeanFactory");
final DefaultListableBeanFactory dlbf = (DefaultListableBeanFactory) beanFactory;
TargetSource ts = new TargetSource() {@Overridepublic Class<?> getTargetClass() {return descriptor.getDependencyType();
}@Overridepublic boolean isStatic() {return false;
}@Overridepublic Object getTarget() {Set<String> autowiredBeanNames = (beanName != null ? new LinkedHashSet<>(1) : null);
Object target = dlbf.doResolveDependency(descriptor, beanName, autowiredBeanNames, null);
if (target == null) {Class<?> type = getTargetClass();
if (Map.class == type) {return Collections.emptyMap();
}else if (List.class == type) {return Collections.emptyList();
}else if (Set.class == type || Collection.class == type) {return Collections.emptySet();
}throw new NoSuchBeanDefinitionException(descriptor.getResolvableType(),"Optional dependency not present for lazy injection point");
}if (autowiredBeanNames != null) {for (String autowiredBeanName : autowiredBeanNames) {if (dlbf.containsBean(autowiredBeanName)) {dlbf.registerDependentBean(autowiredBeanName, beanName);
}}}return target;
}@Overridepublic void releaseTarget(Object target) {}};
ProxyFactory pf = new ProxyFactory();
pf.setTargetSource(ts);
Class<?> dependencyType = descriptor.getDependencyType();
if (dependencyType.isInterface()) {pf.addInterface(dependencyType);
}return pf.getProxy(dlbf.getBeanClassLoader());
}

这段代码就利用了 ProxyFactory 来生成代理对象,以及使用了 TargetSource,以达到代理对象在执行某个方法时,调用 TargetSource 的 getTarget()方法实时得到一个被代理对象。
Introductionhttps://www.cnblogs.com/powerwu/articles/5170861.htmlLoadTimeWeaverhttps://www.cnblogs.com/davidwang456/p/5633609.html
