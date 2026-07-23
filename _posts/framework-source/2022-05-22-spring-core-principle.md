---
title: Spring底层核心原理解析
categories: [Java, Spring, 框架源码]
tags: [Spring, IOC, Bean生命周期, 依赖注入, 推断构造方法, AOP, 事务]
author: hsc
date: 2022-05-22 00:00:00 +0800
description: Spring底层核心原理串讲，涵盖Bean生命周期、依赖注入、推断构造方法、AOP、事务等核心流程的宏观理解。
mindmap:
---

# Spring底层核心原理解析

## 一、Spring入门回顾

```java
AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(AppConfig.class);
UserService userService = (UserService) context.getBean("userService");
userService.test();
```

三行代码底层做了什么？

| 代码 | 底层逻辑 |
|------|---------|
| `new AnnotationConfigApplicationContext()` | 构造容器 + 解析配置 + 扫描注册BeanDefinition |
| `context.getBean("userService")` | 根据BeanDefinition创建Bean（生命周期） |
| `userService.test()` | 调用业务方法 |

Spring Boot 底层用的也是 `AnnotationConfigApplicationContext`。

---

## 二、Spring如何创建对象

### 2.1 解析与注册

`new AnnotationConfigApplicationContext(AppConfig.class)` 时做：

1. 解析 `AppConfig.class`，获取扫描路径
2. 遍历扫描路径下的Java类，找到带 `@Component`、`@Service` 等注解的类
3. 生成 `beanName` → 存入 `BeanDefinitionMap`（Map<String, BeanDefinition>）
4. `getBean("userService")` 时根据 beanName 找到对应的 Class，去创建对象

### 2.2 Bean创建生命周期（宏观）

```
1. 推断构造方法 → 实例化
2. 依赖注入（@Autowired 属性赋值）
3. Aware回调（BeanNameAware, BeanFactoryAware...）
4. 初始化前（@PostConstruct）
5. 初始化（InitializingBean.afterPropertiesSet()）
6. 初始化后（AOP → 生成代理对象）
```

> 如果需要AOP，最终Bean是代理对象；不需要AOP，Bean就是原始实例。

### 2.3 单例Bean vs 原型Bean

| 类型 | 存储 | 每次getBean |
|------|------|-------------|
| 单例 | 存入单例池（Map） | 返回同一个对象 |
| 原型 | 不存单例池 | 重新执行整个创建流程 |

---

## 三、推断构造方法

Spring 选择构造方法的逻辑：

```
类的构造方法情况 → Spring策略：
├── 只有1个构造方法
│   ├── 无参 → 使用无参
│   └── 有参 → 使用该有参，参数从容器找
├── 多个构造方法 + 无@Autowired
│   ├── 有无参 → 使用无参
│   └── 无无参 → 报错
└── 有@Autowired 标记 → 使用标记的那个
    └── @Autowired(required=false) 多个 → 自动选择最佳匹配
```

**参数查找**：先按类型 → 多个则按名称 → 找不到报错。

---

## 四、AOP大致流程

判断是否需要 AOP：
1. 找出所有切面Bean
2. 遍历 `@Before`、`@After` 等切面方法
3. 匹配 Pointcut 是否与当前Bean匹配

CGLIB动态代理流程：
```
UserServiceProxy extends UserService {
    target = 原始对象
    
    test() {
        @Before 切面逻辑
        target.test()
        @After 切面逻辑
    }
}
```

`getBean()` 返回的是代理对象（`UserServiceProxy`）。

---

## 五、Spring事务

`@Transactional` 方法执行流程：

```
1. 判断方法是否有 @Transactional
2. 利用 TransactionManager 建立数据库连接
3. 设置 autocommit = false
4. 执行业务逻辑（执行SQL）
5. 无异常 → commit / 有异常 → rollback
```

**事务是否生效的判断标准**：被 `@Transactional` 修饰的方法是否直接被代理对象调用。
- 直接调用 → 事务生效
- 同类内 this.method() → 事务失效（绕过代理）

---

## 六、总结

| 核心概念 | 要点 |
|----------|------|
| **BeanFactory/ApplicationContext** | Spring核心容器 |
| **BeanDefinition** | Bean的定义信息载体 |
| **Bean生命周期** | 实例化 → 注入 → Aware → 初始化 → AOP |
| **推断构造方法** | 自动选择最合适的构造方法 |
| **AOP** | 初始化后通过CGLIB/JDK动态代理实现 |
| **Spring事务** | 基于AOP代理，TransactionManager管理连接和提交/回滚 |
