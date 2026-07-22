---


title: "Spring之依赖注入源码解析（下）"
description: "Spring 之依赖注入源码解析(下).md..."
author: hsc
date: 2022-04-01 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis', 'IOC']
toc: true


---

07-Spring 之依赖注入源码解析(下).md

上节课我们讲了 Spring 中的自动注入(byName,byType)和@Autowired 注解的工作原理以及源码分析,那么今天这节课,我们来分析还没讲完的,剩下的核心的方法:
@NullableObject resolveDependency(DependencyDescriptor descriptor, @Nullable String requestingBeanName,@Nullable Set<String> autowiredBeanNames, @Nullable TypeConvertertypeConverter) throws BeansException;
该方法表示,传入一个依赖描述(DependencyDescriptor),该方法会根据该依赖描述从 BeanFactory 中找出对应的唯一的一个 Bean 对象。
下面来分析一下 DefaultListableBeanFactory 中**resolveDependency()**方法的具体实现,具体流程图:
1. 找出 BeanFactory 中类型为 type 的所有的 Bean 的名字,注意是名字,而不是 Bean 对象,因为我们可以根据 BeanDefinition 就能判断和当前 type 是不是匹配,不用生成 Bean 对象
2. 把 resolvableDependencies 中 key 为 type 的对象找出来并添加到 result 中
3. 遍历根据 type 找出的 beanName,判断当前 beanName 对应的 Bean 是不是能够被自动注入
4. 先判断 beanName 对应的 BeanDefinition 中的 autowireCandidate 属性,如果为 false,表示不能用来进行自动注入,如果为 true 则继续进行判断
5. 判断当前 type 是不是泛型,如果是泛型是会把容器中所有的 beanName 找出来的,如果是这种情况,那么在这一步中就要获取到泛型的真正类型,然后进行匹配,如果当前 beanName 和当前泛型对应的真实类型匹配,那么则继续判断
6. 如果当前 DependencyDescriptor 上存在@Qualifier 注解,那么则要判断当前 beanName 上是否定义了 Qualifier,并且是否和当前 DependencyDescriptor 上的 Qualifier 相等,相等则匹配
7. 经过上述验证之后,当前 beanName 才能成为一个可注入的,添加到 result 中关于依赖注入中泛型注入的实现首先在 Java 反射中,有一个 Type 接口,表示类型,具体分类为:

### 1. raw types:也就是普通 Class
### 2. parameterized types:对应 ParameterizedType 接口,泛型类型
### 3. array types:对应 GenericArrayType,泛型数组
### 4. type variables:对应 TypeVariable 接口,表示类型变量,也就是所定义的泛型,比如 T、K
### 5. primitive types:基本类型,int、boolean 大家可以好好看看下面代码所打印的结果:

public class TypeTest<T> {private int i;
private Integer it;
private int[] iarray;
private List list;
private List<String> slist;
private List<T> tlist;
private T t;
private T[] tarray;
public static void main(String[] args) throws NoSuchFieldException {test(TypeTest.class.getDeclaredField("i"));
System.out.println("=======");
test(TypeTest.class.getDeclaredField("it"));
System.out.println("=======");
test(TypeTest.class.getDeclaredField("iarray"));
System.out.println("=======");
test(TypeTest.class.getDeclaredField("list"));
System.out.println("=======");
test(TypeTest.class.getDeclaredField("slist"));
System.out.println("=======");
test(TypeTest.class.getDeclaredField("tlist"));
System.out.println("=======");
test(TypeTest.class.getDeclaredField("t"));
System.out.println("=======");
test(TypeTest.class.getDeclaredField("tarray"));
}public static void test(Field field) {if (field.getType().isPrimitive()) {System.out.println(field.getName() + "是基本数据类型");
} else {System.out.println(field.getName() + "不是基本数据类型");
}if (field.getGenericType() instanceof ParameterizedType) {System.out.println(field.getName() + "是泛型类型");
} else {System.out.println(field.getName() + "不是泛型类型");
}if (field.getType().isArray()) {System.out.println(field.getName() + "是普通数组");
} else {System.out.println(field.getName() + "不是普通数组");
}if (field.getGenericType() instanceof GenericArrayType) {System.out.println(field.getName() + "是泛型数组");
} else {System.out.println(field.getName() + "不是泛型数组");
}if (field.getGenericType() instanceof TypeVariable) {System.out.println(field.getName() + "是泛型变量");

} else {System.out.println(field.getName() + "不是泛型变量");
}}}Spring 中,但注入点是一个泛型时,也是会进行处理的,比如:
@Componentpublic class UserService extends BaseService<OrderService, StockService> {public void test() {System.out.println(o);
}}public class BaseService<O, S> {@Autowiredprotected O o;
@Autowiredprotected S s;
}
1. Spring 扫描时发现 UserService 是一个 Bean
2. 那就取出注入点,也就是 BaseService 中的两个属性 o、s
3. 接下来需要按注入点类型进行注入,但是 o 和 s 都是泛型,所以 Spring 需要确定 o 和 s 的具体类型。
4. 因为当前正在创建的是 UserService 的 Bean,所以可以通过 userService.getClass().getGenericSuperclass().getTypeName() 获取到具体的泛型信息,比如 com.zhouyu.service.BaseService<com.zhouyu.service.OrderService, com.zhouyu.service.StockService>
5. 然后再拿到 UserService 的父类 BaseService 的泛型变量: for (TypeVariable<? extends Class<?>>typeParameter : userService.getClass().getSuperclass().getTypeParameters()) {System._out_.println(typeParameter.getName()); }
6. 通过上面两段代码,就能知道,o 对应的具体就是 OrderService,s 对应的具体类型就是 StockService
7. 然后再调用 oField.getGenericType()就知道当前 field 使用的是哪个泛型,就能知道具体类型了@Qualifier 的使用

定义两个注解:
@Target({ElementType.TYPE, ElementType.FIELD})
@Retention(RetentionPolicy.RUNTIME)
@Qualifier("random")
public @interface Random {}@Target({ElementType.TYPE, ElementType.FIELD})
@Retention(RetentionPolicy.RUNTIME)
@Qualifier("roundRobin")
public @interface RoundRobin {}定义一个接口和两个实现类,表示负载均衡:
public interface LoadBalance {String select();
}@Component@Randompublic class RandomStrategy implements LoadBalance {@Overridepublic String select() {return null;
}}@Component@RoundRobinpublic class RoundRobinStrategy implements LoadBalance {@Overridepublic String select() {return null;
}}使用:

@Componentpublic class UserService {@Autowired@RoundRobinprivate LoadBalance loadBalance;
public void test() {System.out.println(loadBalance);
}}@Resource@Resource 注解底层工作流程图:
