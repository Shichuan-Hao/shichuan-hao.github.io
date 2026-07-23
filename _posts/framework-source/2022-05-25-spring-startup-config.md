---
title: Spring之推断构造方法、启动过程与配置类解析
categories: [Java, Spring, 框架源码]
tags: [Spring, 推断构造方法, refresh, 启动过程, 配置类解析, ConfigurationClassPostProcessor]
author: hsc
date: 2022-05-25 00:00:00 +0800
description: 深入Spring推断构造方法、启动过程refresh()全流程、ConfigurationClassPostProcessor配置类解析源码分析。
mindmap: https://www.processon.com/view/link/5f60a7d71e08531edf26a919
---

# Spring之推断构造方法、启动过程与配置类解析

## 一、推断构造方法

### 1.1 决策流程

```
一个类有多个构造方法，Spring怎么选？
    ├── 开发者指定了构造方法？
    │   ├── xml <constructor-arg> → 按参数个数确定
    │   └── @Autowired 注解标记 → 使用该构造方法
    ├── 需要Spring自动选择？（autowire=constructor）
    ├── 多个 @Autowired(required=false) → 自动选择最佳
    └── 都没有 → 用无参构造方法（没有则报错）
```

**唯一有参**：Spring自动去容器中找参数，`AnnotationConfigApplicationContext` 支持。

### 1.2 源码流程（autowireConstructor）

```java
// AbstractAutowireCapableBeanFactory.createBeanInstance():
1. 检查Supplier → 调用get()
2. 检查factoryMethod → 调用对应工厂方法
3. SmartInstantiationAwareBeanPostProcessor.determineCandidateConstructors()
   → 返回可用的构造方法数组
4. 有可用构造方法 → autowireConstructor()
5. 没有 → 用无参构造实例化
```

**autowireConstructor()核心**：
1. 有缓存直接用缓存
2. 找出所有构造方法，**参数多的排前面**
3. 遍历构造方法 → 根据参数类型找bean
4. **匹配度打分**：选分数最低（最匹配）的

### 1.3 匹配度打分规则

```java
// MethodInvoker.getTypeDifferenceWeight()
参数类型 = A，候选bean类型 = A  → 得分 0（完美匹配）
参数类型 = B，候选bean类型 = A  → 得分 2（B是A的父类）
参数类型 = C，候选bean类型 = A  → 得分 4（C是A的祖父类）
参数类型 = D，候选bean类型 = A  → 得分 1（D是A的接口）
```

**分数越低越匹配**，可能多个构造方法得分相同 → 报错（选择不唯一）。

### 1.4 @Bean 方法重载

多个 @Bean 同名方法（重载）→ 只有一个BeanDefinition → `isFactoryMethodUnique=false`。

创建时和推断构造方法逻辑一致，根据参数匹配度选择合适的 factoryMethod。

---

## 二、启动过程（refresh方法）

Spring启动 = 构建ApplicationContext + 调用 `refresh()`。

### 2.1 refresh() 完整流程

```
1. prepareRefresh()
   └── 记录时间、校验Environment必要属性

2. obtainFreshBeanFactory()
   └── 获取/刷新 BeanFactory（默认 DefaultListableBeanFactory）

3. prepareBeanFactory(beanFactory)
   └── 设置类加载器、表达式解析器、注册默认的BeanPostProcessor等

4. postProcessBeanFactory(beanFactory)
   └── 子类扩展点

5. invokeBeanFactoryPostProcessors(beanFactory)
   └── ★ 执行 BeanFactoryPostProcessor
      ├── ConfigurationClassPostProcessor 扫描解析配置
      ├── 注册所有 BeanDefinition
      └── 其他 BeanFactoryPostProcessor

6. registerBeanPostProcessors(beanFactory)
   └── 注册用户自定义 BeanPostProcessor

7. initMessageSource()
   └── 初始化国际化组件

8. initApplicationEventMulticaster()
   └── 初始化事件广播器

9. onRefresh()
   └── 子类扩展（SpringBoot在这里启动Tomcat）

10. registerListeners()
    └── 注册 ApplicationListener

11. finishBeanFactoryInitialization(beanFactory)
    └── ★ 初始化所有非懒加载的单例Bean

12. finishRefresh()
    └── 启动Lifecycle组件 + 发布 ContextRefreshedEvent
```

### 2.2 BeanFactoryPostProcessor 执行顺序

```
1. 执行 手动添加的 BeanDefinitionRegistryPostProcessor
2. 执行 实现了 PriorityOrdered 的 BeanDefinitionRegistryPostProcessor
3. 执行 实现了 Ordered 的 BeanDefinitionRegistryPostProcessor
4. 执行 其余的 BeanDefinitionRegistryPostProcessor
5. 执行上面所有的 postProcessBeanFactory()
6. 执行 手动添加的 BeanFactoryPostProcessor
7. 执行 PriorityOrdered 的 BeanFactoryPostProcessor
8. 执行 Ordered 的 BeanFactoryPostProcessor
9. 执行其余的 BeanFactoryPostProcessor
```

### 2.3 关键接口区分

| 接口 | 作用 | 时机 |
|------|------|------|
| `BeanDefinitionRegistryPostProcessor` | 动态注册BeanDefinition | refresh 第5步 |
| `BeanFactoryPostProcessor` | 修改BeanDefinition | refresh 第5步 |
| `SmartLifecycle` | 容器生命周期管理 | refresh 第12步 |

### 2.4 可刷新的 vs 不可刷新

| ApplicationContext | 可刷新？ |
|--------------------|---------|
| `GenericApplicationContext` | ❌ 只能调用一次 refresh() |
| `AbstractRefreshableApplicationContext` | ✅ 可多次刷新 |
| `AnnotationConfigApplicationContext` | ❌ （继承GenericApplicationContext） |
| `AnnotationConfigWebApplicationContext` | ✅ （继承AbstractRefreshableWebApplicationContext） |

---

## 三、配置类解析

### 3.1 ConfigurationClassPostProcessor 流程

1. 取出配置类BeanDefinition（AppConfig）
2. `ConfigurationClassParser` 解析 → 生成 `ConfigurationClass` 对象
3. 遍历处理 ConfigurationClass → 注册更多 BeanDefinition

### 3.2 解析配置类的步骤

```
解析 AppConfig 类：
├── @ComponentScan → 扫描包路径 → 注册扫描到的BeanDefinition
├── @PropertySource → 添加PropertySource到Environment
├── @Import
│   ├── ImportSelector → 调用selectImports → 递归解析
│   └── ImportBeanDefinitionRegistrar → 注册到ConfigurationClass
├── @ImportResource → 记录XML路径
├── @Bean 方法 → 记录beanMethods
├── 实现接口的 @Bean 默认方法
└── 父类递归解析
```

之后，通过 `ConfigurationClassBeanDefinitionReader` 处理生成的 ConfigurationClass：
- `@Import` 导入的类 → 生成BeanDefinition
- `@Bean` 方法 → 生成 @Bean 类型的BeanDefinition
- `@ImportResource` → 解析XML并注册BeanDefinition
- `ImportBeanDefinitionRegistrar` → 执行 `registerBeanDefinitions()`

---

## 四、Spring核心创建Bean流程总结

```
getBean("userService") →
  1. 实例化前 → BeanPostProcessor.postProcessBeforeInstantiation()
  2. 推断构造方法 → 反射 + 加权打分选择最佳
  3. 实例化 → 空壳对象
  4. BeanDefinition后置处理 → 解析@Autowired/@Value缓存
  5. 实例化后 → BeanPostProcessor.postProcessAfterInstantiation()
  6. 依赖注入 → populateBean()
  7. Aware回调 → BeanNameAware/BeanFactoryAware/...
  8. 初始化前 → @PostConstruct
  9. 初始化 → afterPropertiesSet / initMethod
  10. 初始化后 → AOP代理（如有）
  11. 存入单例池 → singletonObjects
```

> Spring 的核心 = BeanDefinition 的注册 + Bean的创建生命周期
