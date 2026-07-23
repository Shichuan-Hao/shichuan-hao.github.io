---
title: Spring之AOP底层源码解析
categories: [Java, Spring, 框架源码]
tags: [Spring, AOP, 动态代理, CGLIB, JDK Proxy, Advisor, PointCut, '@EnableAspectJAutoProxy']
author: hsc
date: 2022-05-28 00:00:00 +0800
description: 深入Spring AOP底层源码，从动态代理技术到AspectJ注解解析、自动代理创建全流程，含proxyFactory、Advisor、PointCut原理解析。
mindmap:
---

# Spring之AOP底层源码解析

## 一、动态代理技术

### 1.1 CGLIB — 基于父子类

```java
UserService target = new UserService();
Enhancer enhancer = new Enhancer();
enhancer.setSuperclass(UserService.class);
enhancer.setCallbacks(new Callback[]{new MethodInterceptor() {
    @Override
    public Object intercept(Object o, Method method, Object[] objects, MethodProxy proxy) throws Throwable {
        System.out.println("before...");
        Object result = proxy.invoke(target, objects);
        System.out.println("after...");
        return result;
    }
}});
UserService userService = (UserService) enhancer.create();
```

- 被代理类 = 父类，代理类 = 子类
- **不需要接口**
- 不能代理 `final` 类 / `final` 方法

### 1.2 JDK动态代理 — 基于接口

```java
UserService target = new UserService();
Object proxy = Proxy.newProxyInstance(
    UserService.class.getClassLoader(),
    new Class[]{UserInterface.class},   // 必须是接口！
    new InvocationHandler() {
        @Override
        public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
            System.out.println("before...");
            Object result = method.invoke(target, args);
            System.out.println("after...");
            return result;
        }
    });
UserInterface userService = (UserInterface) proxy;
```

- 必须基于接口
- 代理对象类型是 `UserInterface`，不是 `UserService`
- `new Class[]{UserService.class}` → 报错（不是接口）

---

## 二、Spring对代理的封装

### 2.1 ProxyFactory

```java
UserService target = new UserService();
ProxyFactory proxyFactory = new ProxyFactory();
proxyFactory.setTarget(target);
proxyFactory.addAdvice(new MethodInterceptor() {
    @Override
    public Object invoke(MethodInvocation invocation) throws Throwable {
        System.out.println("before...");
        Object result = invocation.proceed();  // 调用链传递
        System.out.println("after...");
        return result;
    }
});
UserInterface userService = (UserInterface) proxyFactory.getProxy();
```

- 自动选择代理方式：有接口 → JDK / 无接口 → CGLIB
- 可强制CGLIB：`proxyFactory.setProxyTargetClass(true)`

### 2.2 Advice 五种类型

| Advice | 执行时机 |
|--------|---------|
| Before Advice | 方法执行前 |
| AfterReturning | return 之后 |
| AfterThrowing | 抛异常后 |
| After (finally) | finally 之后，最晚执行 |
| Around | 包裹整个方法，最强大 |

### 2.3 Advisor = Pointcut + Advice

```java
proxyFactory.addAdvisor(new PointcutAdvisor() {
    @Override
    public Pointcut getPointcut() {
        return new StaticMethodMatcherPointcut() {
            @Override
            public boolean matches(Method method, Class<?> targetClass) {
                return method.getName().equals("test");  // 只代理 test 方法
            }
        };
    }
    @Override
    public Advice getAdvice() {
        return new MethodInterceptor() { /* 代理逻辑 */ };
    }
});
```

**Advisor = Pointcut（切哪里） + Advice（做什么）**

---

## 三、自动代理的演进之路

### 3.1 ProxyFactoryBean（手动版）

```java
@Bean
public ProxyFactoryBean userServiceProxy() {
    UserService userService = new UserService();
    ProxyFactoryBean proxyFactoryBean = new ProxyFactoryBean();
    proxyFactoryBean.setTarget(userService);
    proxyFactoryBean.setInterceptorNames("zhouyuAroundAdvise");
    return proxyFactoryBean;
}
```

- ✅ FactoryBean 让代理对象成为 Bean
- ❌ 只能代理单个Bean

### 3.2 BeanNameAutoProxyCreator（按名称）

```java
@Bean
public BeanNameAutoProxyCreator beanNameAutoProxyCreator() {
    BeanNameAutoProxyCreator creator = new BeanNameAutoProxyCreator();
    creator.setBeanNames("userSe*");              // 按名称匹配
    creator.setInterceptorNames("zhouyuAroundAdvise");
    creator.setProxyTargetClass(true);
    return creator;
}
```

- ✅ 可批量代理
- ❌ 只能按beanName匹配

### 3.3 DefaultAdvisorAutoProxyCreator（按Advisor）

```java
@Bean
public DefaultAdvisorAutoProxyCreator defaultAdvisorAutoProxyCreator() {
    return new DefaultAdvisorAutoProxyCreator();
}

@Bean
public DefaultPointcutAdvisor defaultPointcutAdvisor() {
    NameMatchMethodPointcut pointcut = new NameMatchMethodPointcut();
    pointcut.addMethodName("test");
    return new DefaultPointcutAdvisor(pointcut, new ZhouyuAfterReturningAdvise());
}
```

- 自动找到所有 `Advisor` 类型的Bean
- 根据 Pointcut 判定代理哪些Bean
- **这就是现代Spring AOP的雏形**

### 3.4 @EnableAspectJAutoProxy（注解版，最终方案）

```java
@Aspect
@Component
public class ZhouyuAspect {
    @Before("execution(public void com.example.service.UserService.test())")
    public void zhouyuBefore(JoinPoint joinPoint) {
        System.out.println("zhouyuBefore");
    }
}
```

只需要 `@Aspect` + `@Before/@After/@Around` + `@EnableAspectJAutoProxy`。

**Spring做了什么**：解析注解 → 生成Pointcut + Advice → 包装成Advisor → ProxyFactory创建代理。

---

## 四、@EnableAspectJAutoProxy 工作流程

### 4.1 核心入口

`@EnableAspectJAutoProxy` → `@Import(AspectJAutoProxyRegistrar.class)` → 注册 `AnnotationAwareAspectJAutoProxyCreator`（一个 `BeanPostProcessor`）。

### 4.2 AnnotationAwareAspectJAutoProxyCreator 的职责

1. 找到所有 `@Aspect` Bean
2. 解析每个切面类中的 `@Before/@After/@Around等` → 生成 Advisor 列表
3. 在 `postProcessAfterInitialization` 阶段判断是否需要创建代理
4. 如果需要 → `ProxyFactory` 创建代理 → 替换原Bean

### 4.3 注解 → Advice 映射

| 注解 | Spring实现类 | 类型 |
|------|-------------|------|
| `@Before` | `AspectJMethodBeforeAdvice` | MethodBeforeAdvice |
| `@AfterReturning` | `AspectJAfterReturningAdvice` | AfterReturningAdvice |
| `@AfterThrowing` | `AspectJAfterThrowingAdvice` | MethodInterceptor |
| `@After` | `AspectJAfterAdvice` | MethodInterceptor |
| `@Around` | `AspectJAroundAdvice` | MethodInterceptor |

> 注意：Spring只是借用了AspectJ的注解定义，**解析逻辑是Spring自己做的**。真正的AspectJ是编译时织入，Spring AOP是运行时动态代理。

---

## 五、AOP核心概念回顾

| 概念 | 说明 |
|------|------|
| **Aspect** | 切面，@Aspect注解的类 |
| **Join point** | 连接点，程序执行中的点（方法执行） |
| **Advice** | 通知，在连接点执行的动作 |
| **Pointcut** | 切点，匹配连接点的表达式 |
| **Target Object** | 目标对象，被代理的对象 |
| **AOP Proxy** | 代理对象（JDK/CGLIB） |
| **Weaving** | 织入，创建代理对象的过程 |

---

## 六、TargetSource机制

允许自定义"从哪获取被代理对象"的逻辑：

```java
TargetSource ts = new TargetSource() {
    @Override
    public Object getTarget() {
        return context.getBean("userService");  // 每次调用时动态获取
    }
};
```

**典型应用**：`@Lazy` 注解 — 注入一个代理对象，代理对象的每次方法调用时去容器获取真正的Bean。

---

## 七、CGLIB vs JDK Proxy 选择规则

| 条件 | 选择 |
|------|------|
| 类实现了接口 + `proxyTargetClass=false` | JDK动态代理 |
| 类实现了接口 + `proxyTargetClass=true` | CGLIB |
| 类没有实现接口 | CGLIB（强制） |
| `@EnableAspectJAutoProxy(proxyTargetClass=true)` | CGLIB强制 |

---

## 八、总结

```
Spring AOP 演进：
  ProxyFactory（手动） → ProxyFactoryBean（单个Bean）
  → BeanNameAutoProxyCreator（按名称批量）
  → DefaultAdvisorAutoProxyCreator（按Advisor自动）
  → @EnableAspectJAutoProxy（注解驱动，现在的标准）

底层：
  Advisors = findAspect + parseAnnotation → Pointcut + Advice
  proxy = ProxyFactory(Advisors).getProxy()
  → postProcessAfterInitialization 返回代理替换原Bean
```
