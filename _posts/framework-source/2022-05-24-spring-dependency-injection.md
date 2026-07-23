---
title: Spring之依赖注入源码解析
categories: [Java, Spring, 框架源码]
tags: [Spring, 依赖注入, '@Autowired', '@Resource', '@Value', 循环依赖, 注入点, populateBean]
author: hsc
date: 2022-05-24 00:00:00 +0800
description: 深入Spring依赖注入源码，拆解@Autowired、@Resource、@Value的注入流程与循环依赖的三级缓存解决方案。
mindmap: https://www.processon.com/view/link/5f8d4c45e401fd06fda0b2dd
---

# Spring之依赖注入源码解析

## 一、注入点解析

Spring在创建Bean时，`AutowiredAnnotationBeanPostProcessor#postProcessMergedBeanDefinition()` 找出所有的注入点：

```
遍历BeanClass的所有Field和Method：
├── 找到带有 @Autowired / @Value 的字段 → 封装为AutowiredFieldElement
├── 找到带有 @Autowired / @Value 的方法 → 封装为AutowiredMethodElement
└── 找到带有 @Resource 的字段/方法 → 通过CommonAnnotationBeanPostProcessor解析
```

注入元信息缓存：`injectionMetadataCache`（ConcurrentHashMap<beanName, InjectionMetadata>）。

### 为什么需要缓存？
- 父类的注入点也会被子类继承
- 避免每次创建Bean都去反射查找

---

## 二、@Autowired 注入流程

### 2.1 字段注入

`AutowiredFieldElement#inject()`：

```java
protected void inject(Object bean, String beanName, PropertyValues pvs) {
    Field field = (Field) this.member;
    Object value;
    // 1. 解析依赖
    DependencyDescriptor desc = new DependencyDescriptor(field, this.required);
    value = beanFactory.resolveDependency(desc, beanName, autowiredBeanNames, typeConverter);
    // 2. 反射设置值
    if (value != null) {
        ReflectionUtils.makeAccessible(field);
        field.set(bean, value);
    }
}
```

### 2.2 resolveDependency 解析过程

```
doResolveDependency():
1. 获取 @Qualifier 上的 value（如果存在）
2. 多个候选 → 按 @Primary → @Priority → 名称匹配 选择
3. 延迟注入 → 返回代理对象（Lazy proxy）
4. 数组/Collection/Map 类型批量注入
5. findAutowireCandidates() 找到所有候选bean
6. 确定最终结果
```

### 2.3 找候选Bean

`findAutowireCandidates(beanName, type, descriptor)`：

1. 从 `resolvableDependencies` 找（内置对象如BeanFactory、ApplicationContext等）
2. 从每个已注册的 `beanName` 中找类型匹配的
3. 工厂方法创建的类型匹配
4. `isAutowireCandidate()` 过滤

### 2.4 结果过滤

- `@Qualifier` 匹配
- `@Primary` 优先
- `@Priority` 排序
- **fallback**：按 `beanName`（字段名/方法参数名）匹配

---

## 三、@Resource 注入流程

`CommonAnnotationBeanPostProcessor` 处理：

**与 @Autowired 的区别**：
- `@Autowired` = Spring原生
- `@Resource` = JSR-250标准

| 特性 | @Autowired | @Resource |
|------|----------|----------|
| 注入方式 | byType → byName | byName → byType |
| @Qualifier | 支持 | 不支持，用 @Resource(name) 代替 |
| @Primary | 支持 | 不支持 |
| required | 默认true | 默认true |

**@Resource 查找逻辑**：
1. 指定 `name` → 按名称查找
2. 未指定 `name` → 用字段名/方法参数名
3. 按名称找到 → 返回
4. 未找到 → 按类型查找 + byType

---

## 四、@Value 注入

`@Value` 本质也是 `AutowiredAnnotationBeanPostProcessor` 处理。

可以注入的内容：
1. **字面量**：`@Value("hello")`
2. **SpEL**：`@Value("#{1+2}")` → 3
3. **配置文件**：`@Value("${key}")`→ Environment 中取

处理类：`StringValueResolver` → `PropertySourcesPlaceholderConfigurer` 注册。

```java
// @Value("${name}") 解析流程：
1. PropertySourcesPlaceholderConfigurer 在postProcessBeanFactory中注册
2. @Value 注解被 AutowiredAnnotationBeanPostProcessor 解析
3. 调用 DefaultListableBeanFactory#resolveEmbeddedValue()
4. 遍历StringValueResolver（优先级：PropertySources → Environment → System）
```

---

## 五、循环依赖原理

### 5.1 什么是循环依赖

```java
@Component
class A {
    @Autowired B b;  // A依赖B
}
@Component
class B {
    @Autowired A a;  // B依赖A
}
```

A创建时需要B，B创建时需要A → 死循环！

### 5.2 三级缓存

| 缓存 | 名称 | 存储内容 |
|------|------|---------|
| 一级 | `singletonObjects` | 完整可用的单例Bean |
| 二级 | `earlySingletonObjects` | 提前暴露的不完整Bean实例 |
| 三级 | `singletonFactories` | `ObjectFactory`，可生成Bean的早期引用 |

### 5.3 循环依赖解决流程

```
getBean("a"):
1. 实例化A（反射创建空壳对象）→ a原始对象
2. 将 a原始对象 的 ObjectFactory 放入三级缓存
3. 注入属性 → 发现需要B
4. getBean("b"):
   a. 实例化B（反射创建空壳对象）→ b原始对象
   b. 将 b原始对象 的 ObjectFactory 放入三级缓存
   c. 注入属性 → 发现需要A
   d. getBean("a"):
      - 从三级缓存找到ObjectFactory → 生成a早期引用
      - 放入二级缓存（earlySingletonObjects）
      - 返回 a早期引用
   e. 注入a早期引用到b
   f. b 初始化完成 → 一级缓存
5. 注入b到a
6. a 初始化完成 → 一级缓存
```

### 5.4 为什么需要三级缓存？（不是二级）

```
1. 正常Bean → 生成原始对象 → 放入三级缓存
2. 有AOP的Bean → 需要生成代理对象
   - 原始对象 vs 代理对象 不同！
   - 三级缓存 ObjectFactory → 在getObject()时判断是否需要AOP
   - 如果需要AOP，这里返回代理对象
```

**如果只有二级缓存**：存的是原始对象，若被AOP则别人拿到的是错误的原始对象。

### 5.5 不能解决的循环依赖

| 情况 | 能否解决 |
|------|---------|
| 单例setter注入 | ✅ 能 |
| 单例构造器注入 | ❌ 不能（实例化前就需要注入） |
| 原型模式 | ❌ 不能（没有单例缓存） |
| 单例 + AOP | ✅ 能（通过三级缓存的ObjectFactory） |

---

## 六、总结

```
依赖注入两大处理器：
├── AutowiredAnnotationBeanPostProcessor → @Autowired/@Value
└── CommonAnnotationBeanPostProcessor → @Resource/@PostConstruct/@PreDestroy

循环依赖三级缓存：
├── singletonObjects (一级)：成品Bean
├── earlySingletonObjects (二级)：早期引用（AOP代理/原始对象）
└── singletonFactories (三级)：ObjectFactory（延迟生成代理）

@Autowired 优先级：
@Qualifier > @Primary > @Priority > beanName匹配
```
