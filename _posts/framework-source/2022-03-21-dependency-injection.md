---

title: "Spring之依赖注入源码解析（上）"
description: "Spring 之依赖注入源码解析(上).md..."
author: hsc
date: 2022-03-21 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis', 'IOC']
toc: true

---

06-Spring 之依赖注入源码解析(上).md

依赖注入底层原理流程图:
首先分两种:
1. 手动注入
2. 自动注入手动注入在 XML 中定义 Bean 时,就是手动注入,因为是程序员手动给某个属性指定了值。
<bean name="userService" class="com.luban.service.UserService"><property name="orderService" ref="orderService"/></bean>上面这种底层是通过 set 方法进行注入。
<bean name="userService" class="com.luban.service.UserService"><constructor-arg index="0" ref="orderService"/></bean>上面这种底层是通过构造方法进行注入。
所以手动注入的底层也就是分为两种:
1. set 方法注入
2. 构造方法注入自动注入自动注入又分为两种:
1. XML 的 autowire 自动注入
2. @Autowired 注解的自动注入 XML 的 autowire 自动注入在 XML 中,我们可以在定义一个 Bean 时去指定这个 Bean 的自动注入模式:

### 1. byType
### 2. byName
### 3. constructor
### 4. default
### 5. no 比如:
<bean id="userService" class="com.luban.service.UserService" autowire="byType"/>这么写,表示 Spring 会自动的给 userService 中所有的属性自动赋值(不需要这个属性上有@Autowired 注解,但需要这个属性有对应的 set 方法)。
在创建 Bean 的过程中,在填充属性时,Spring 会去解析当前类,把当前类的所有方法都解析出来,Spring 会去解析每个方法得到对应的 PropertyDescriptor 对象,PropertyDescriptor 中有几个属性:
1. name:这个 name 并不是方法的名字,而是拿方法名字进过处理后的名字 i. 如果方法名字以“get”开头,比如“getXXX”,那么 name=XXXii. 如果方法名字以“is”开头,比如“isXXX”,那么 name=XXXiii. 如果方法名字以“set”开头,比如“setXXX”,那么 name=XXX
2. readMethodRef:表示 get 方法的 Method 对象的引用
3. readMethodName:表示 get 方法的名字
4. writeMethodRef:表示 set 方法的 Method 对象的引用
5. writeMethodName:表示 set 方法的名字
6. propertyTypeRef:如果有 get 方法那么对应的就是返回值的类型,如果是 set 方法那么对应的就是 set 方法中唯一参数的类型 get 方法的定义是: 方法参数个数为 0 个,并且 (方法名字以"get"开头 或者 方法名字以"is"开头并且方法的返回类型为 boolean)
**set 方法的定义是:**方法参数个数为 1 个,并且 (方法名字以"set"开头并且方法返回类型为 void)
所以,Spring 在通过 byName 的自动填充属性时流程是:
1. 找到所有 set 方法所对应的 XXX 部分的名字
2. 根据 XXX 部分的名字去获取 beanSpring 在通过 byType 的自动填充属性时流程是:
1. 获取到 set 方法中的唯一参数的参数类型,并且根据该类型去容器中获取 bean
2. 如果找到多个,会报错。
以上,分析了 autowire 的 byType 和 byName 情况,那么接下来分析 constructor,constructor 表示通过构造方法注入,其实这种情况就比较简单了,没有 byType 和 byName 那么复杂。
如果是 constructor,那么就可以不写 set 方法了,当某个 bean 是通过构造方法来注入时,spring 利用构造方法的参数信息从 Spring 容器中去找 bean,找到 bean 之后作为参数传给构造方法,从而实例化得到一个 bean 对象,并完成属性赋值(属性赋值的代码得程序员来写)。

我们这里先不考虑一个类有多个构造方法的情况,后面单独讲推断构造方法。我们这里只考虑只有一个有参构造方法。
其实构造方法注入相当于 byType+byName,普通的 byType 是根据 set 方法中的参数类型去找 bean,找到多个会报错,而 constructor 就是通过构造方法中的参数类型去找 bean,如果找到多个会根据参数名确定。
另外两个:
1. no,表示关闭 autowire
2. default,表示默认值,我们一直演示的某个 bean 的 autowire,而也可以直接在<beans>标签中设置 autowire,如果设置了,那么<bean>标签中设置的 autowire 如果为 default,那么则会用<beans>标签中设置的 autowire。
可以发现 XML 中的自动注入是挺强大的,那么问题来了,为什么我们平时都是用的@Autowired 注解呢?而没有用上文说的这种自动注入方式呢?
@Autowired 注解相当于 XML 中的 autowire 属性的注解方式的替代。这是在官网上有提到的。
Essentially, the @Autowired annotation provides the same capabilities as described in AutowiringCollaborators but with more fine-grained control and wider applicability 翻译一下:
从本质上讲,@Autowired 注解提供了与 autowire 相同的功能,但是拥有更细粒度的控制和更广泛的适用性。
注意:更细粒度的控制。
XML 中的 autowire 控制的是整个 bean 的所有属性,而@Autowired 注解是直接写在某个属性、某个 set 方法、某个构造方法上的。
再举个例子,如果一个类有多个构造方法,那么如果用 XML 的 autowire=constructor,你无法控制到底用哪个构造方法,而你可以用@Autowired 注解来直接指定你想用哪个构造方法。
同时,用@Autowired 注解,还可以控制,哪些属性想被自动注入,哪些属性不想,这也是细粒度的控制。
但是@Autowired 无法区分 byType 和 byName,@Autowired 是先 byType,如果找到多个则 byName。
那么 XML 的自动注入底层其实也就是:
1. set 方法注入
2. 构造方法注入@Autowired 注解的自动注入上文说了@Autowired 注解,是 byType 和 byName 的结合。
@Autowired 注解可以写在:
1. 属性上:先根据属性类型去找 Bean,如果找到多个再根据属性名确定一个
2. 构造方法上:先根据方法参数类型去找 Bean,如果找到多个再根据参数名确定一个
3. set 方法上:先根据方法参数类型去找 Bean,如果找到多个再根据参数名确定一个

而这种底层到了:
1. 属性注入
2. set 方法注入
3. 构造方法注入寻找注入点在创建一个 Bean 的过程中,Spring 会利用 AutowiredAnnotationBeanPostProcessor 的**postProcessMergedBeanDefinition()**找出注入点并缓存,找注入点的流程为:
1. 遍历当前类的所有的属性字段 Field
2. 查看字段上是否存在@Autowired、@Value、@Inject 中的其中任意一个,存在则认为该字段是一个注入点
3. 如果字段是 static 的,则不进行注入
4. 获取@Autowired 中的 required 属性的值
5. 将字段信息构造成一个 AutowiredFieldElement 对象,作为一个注入点对象添加到 currElements 集合中。
6. 遍历当前类的所有方法 Method
7. 判断当前 Method 是否是桥接方法,如果是找到原方法
8. 查看方法上是否存在@Autowired、@Value、@Inject 中的其中任意一个,存在则认为该方法是一个注入点
9. 如果方法是 static 的,则不进行注入
10. 获取@Autowired 中的 required 属性的值
11. 将方法信息构造成一个 AutowiredMethodElement 对象,作为一个注入点对象添加到 currElements 集合中。
12. 遍历完当前类的字段和方法后,将遍历父类的,直到没有父类。
13. 最后将 currElements 集合封装成一个 InjectionMetadata 对象,作为当前 Bean 对于的注入点集合对象,并缓存。
static 的字段或方法为什么不支持@Component@Scope("prototype")
public class OrderService {}

@Component@Scope("prototype")
public class UserService {@Autowiredprivate static OrderService orderService;
public void test() {System.out.println("test123");
}}看上面代码,UserService 和 OrderService 都是原型 Bean,假设 Spring 支持 static 字段进行自动注入,那么现在调用两次
1. UserService userService1 = context.getBean("userService")
2. UserService userService2 = context.getBean("userService")
问此时,userService1 的 orderService 值是什么?还是它自己注入的值吗?
答案是不是,一旦 userService2 创建好了之后,static orderService 字段的值就发生了修改了,从而出现 bug。
桥接方法 public interface UserInterface<T> {void setOrderService(T t);
}@Componentpublic class UserService implements UserInterface<OrderService> {private OrderService orderService;
@Override@Autowiredpublic void setOrderService(OrderService orderService) {this.orderService = orderService;
}public void test() {System.out.println("test123");
}}UserService 对应的字节码为:

// class version 52.0 (52)
// access flags 0x21// signatureLjava/lang/Object;Lcom/zhouyu/service/UserInterface<Lcom/zhouyu/service/OrderService;>;
// declaration: com/zhouyu/service/UserService implementscom.zhouyu.service.UserInterface<com.zhouyu.service.OrderService>public class com/zhouyu/service/UserService implements com/zhouyu/service/UserInterface {// compiled from: UserService.java@Lorg/springframework/stereotype/Component;()
// access flags 0x2private Lcom/zhouyu/service/OrderService; orderService// access flags 0x1public <init>()VL0LINENUMBER 12 L0ALOAD 0INVOKESPECIAL java/lang/Object.<init> ()VRETURNL1LOCALVARIABLE this Lcom/zhouyu/service/UserService; L0 L1 0MAXSTACK = 1MAXLOCALS = 1// access flags 0x1public setOrderService(Lcom/zhouyu/service/OrderService;)V@Lorg/springframework/beans/factory/annotation/Autowired;()
L0LINENUMBER 19 L0ALOAD 0ALOAD 1PUTFIELD com/zhouyu/service/UserService.orderService : Lcom/zhouyu/service/OrderService;
L1LINENUMBER 20 L1RETURNL2LOCALVARIABLE this Lcom/zhouyu/service/UserService; L0 L2 0LOCALVARIABLE orderService Lcom/zhouyu/service/OrderService; L0 L2 1MAXSTACK = 2MAXLOCALS = 2// access flags 0x1public test()VL0LINENUMBER 23 L0GETSTATIC java/lang/System.out : Ljava/io/PrintStream;
LDC "test123"
INVOKEVIRTUAL java/io/PrintStream.println (Ljava/lang/String;)VL1LINENUMBER 24 L1RETURNL2LOCALVARIABLE this Lcom/zhouyu/service/UserService; L0 L2 0MAXSTACK = 2MAXLOCALS = 1

// access flags 0x1041public synthetic bridge setOrderService(Ljava/lang/Object;)V@Lorg/springframework/beans/factory/annotation/Autowired;()
L0LINENUMBER 11 L0ALOAD 0ALOAD 1CHECKCAST com/zhouyu/service/OrderServiceINVOKEVIRTUAL com/zhouyu/service/UserService.setOrderService(Lcom/zhouyu/service/OrderService;)VRETURNL1LOCALVARIABLE this Lcom/zhouyu/service/UserService; L0 L1 0MAXSTACK = 2MAXLOCALS = 2}可以看到在 UserSerivce 的字节码中有两个 setOrderService 方法:
1. public setOrderService(Lcom/zhouyu/service/OrderService;)V
2. public synthetic bridge setOrderService(Ljava/lang/Object;)V 并且都是存在@Autowired 注解的。
所以在 Spring 中需要处理这种情况,当遍历到桥接方法时,得找到原方法。
注入点进行注入 Spring 在 AutowiredAnnotationBeanPostProcessor 的**postProcessProperties()**方法中,会遍历所找到的注入点依次进行注入。
字段注入
1. 遍历所有的 AutowiredFieldElement 对象。
2. 将对应的字段封装为 DependencyDescriptor 对象。
3. 调用 BeanFactory 的 resolveDependency()方法,传入 DependencyDescriptor 对象,进行依赖查找,
找到当前字段所匹配的 Bean 对象。
4. 将 DependencyDescriptor 对象和所找到的结果对象 beanName 封装成一个 ShortcutDependencyDescriptor 对象作为缓存,比如如果当前 Bean 是原型 Bean,那么下次再来创建该 Bean 时,就可以直接拿缓存的结果对象 beanName 去 BeanFactory 中去那 bean 对象了,不用再次进行查找了
5. 利用反射将结果对象赋值给字段。
Set 方法注入

### 1. 遍历所有的 AutowiredMethodElement 对象
### 2. 遍历将对应的方法的参数,将每个参数封装成 MethodParameter 对象
### 3. 将 MethodParameter 对象封装为 DependencyDescriptor 对象
### 4. 调用 BeanFactory 的 resolveDependency()方法,传入 DependencyDescriptor 对象,进行依赖查找,
找到当前方法参数所匹配的 Bean 对象。
5. 将 DependencyDescriptor 对象和所找到的结果对象 beanName 封装成一个 ShortcutDependencyDescriptor 对象作为缓存,比如如果当前 Bean 是原型 Bean,那么下次再来创建该 Bean 时,就可以直接拿缓存的结果对象 beanName 去 BeanFactory 中去那 bean 对象了,不用再次进行查找了
6. 利用反射将找到的所有结果对象传给当前方法,并执行。
