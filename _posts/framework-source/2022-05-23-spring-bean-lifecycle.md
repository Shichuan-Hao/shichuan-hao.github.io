---
title: Spring之Bean生命周期源码解析
categories: [Java, Spring, 框架源码]
tags: [Spring, Bean生命周期, BeanDefinition, BeanPostProcessor, 实例化, 初始化, Aware, 销毁过程]
author: hsc
date: 2022-05-23 00:00:00 +0800
description: 深入Spring Bean生命周期源码，从扫描生成BeanDefinition到实例化、初始化、AOP、销毁的全流程分析。
mindmap: https://www.processon.com/view/link/5f8588c87d9c0806f27358c1
---

# Spring之Bean生命周期源码解析

## 一、Bean生命周期流程图

Bean的生命周期指：**Spring中一个Bean如何生成，如何销毁**。

整合流程图：[ProcessOn](https://www.processon.com/view/link/5f8588c87d9c0806f27358c1)

---

## 二、Bean的生成过程（上）

### 1. 生成BeanDefinition

Spring启动时调用 `ClassPathScanningCandidateComponentProvider#scanCandidateComponents()` 扫描包路径。

**扫描底层流程**：
```
1. ResourcePatternResolver 获取指定包下所有 .class 文件（包装为 Resource）
2. 遍历 Resource
3. MetadataReaderFactory 解析 Resource → MetadataReader（ASM技术，不加载类到JVM）
4. excludeFilters / includeFilters / @Conditional 筛选
5. 通过筛选 → 生成 ScannedGenericBeanDefinition
6. 判断是否是接口/抽象类
7. 加入结果集
```

**MetadataReader 的能力**：
- 获取类名、父类名、实现接口名、内部类名
- 判断是不是抽象类/接口/注解
- 获取类上的注解信息

> `beanClass` 属性存储的是**类名**，不是Class对象（此时未加载类到JVM）。

### 2. 合并BeanDefinition

支持父子BeanDefinition（与Java父子类不同）：

```xml
<bean id="parent" class="..." scope="prototype"/>
<bean id="child" class="..." parent="parent"/>  <!-- child继承parent的scope -->
```

在创建Bean前需要合并，得到完整的BeanDefinition。

### 3. 加载类

```java
Class<?> resolvedClass = resolveBeanClass(mbd, beanName);
```

如果 `beanClass` 是Class类型直接返回，否则用类名加载。

**类加载器选择**：`ClassUtils.getDefaultClassLoader()`
1. 优先当前线程的ClassLoader
2. 其次ClassUtils的类加载器
3. 最后用系统类加载器

### 4. 实例化前 — 扩展点

`InstantiationAwareBeanPostProcessor.postProcessBeforeInstantiation()`

```java
@Component
public class MyBeanPostProcessor implements InstantiationAwareBeanPostProcessor {
    @Override
    public Object postProcessBeforeInstantiation(Class<?> beanClass, String beanName) {
        if ("userService".equals(beanName)) {
            return new UserService();  // 直接返回自定义对象，跳过后续Spring实例化
        }
        return null;  // 返回null，Spring继续正常流程
    }
}
```

> 如果返回非null对象，则跳过Spring的实例化，直接进入"初始化后"步骤。

### 5. 实例化

三种方式：

| 方式 | 说明 |
|------|------|
| **Supplier** | BeanDefinition 设置了 `instanceSupplier`，调用 `get()` |
| **工厂方法** | BeanDefinition 设置了 `factoryMethod`（静态/实例工厂） |
| **推断构造方法** | 自动选择构造方法反射实例化 |

`@Bean` 注解本质就是工厂方法：
- `static` 方法 → 静态工厂（factoryMethod存在，factoryBeanName为null）
- 非 `static` 方法 → 实例工厂（factoryBeanName=AppConfig的beanName）

**@Lookup 方法注入**：
```java
@Component
public class UserService {
    @Lookup("orderService")
    public OrderService createOrderService() { return null; }
}
```
有 `@Lookup` 时会生成代理对象（不是普通反射实例化）。

### 6. BeanDefinition后置处理 — 扩展点

`MergedBeanDefinitionPostProcessor.postProcessMergedBeanDefinition()`

`AutowiredAnnotationBeanPostProcessor` 在这里找出并缓存注入点（`injectionMetadataCache`）。

### 7. 实例化后 — 扩展点

`InstantiationAwareBeanPostProcessor.postProcessAfterInstantiation()`

返回 `false` 可阻止后续属性赋值。

### 8. 属性赋值（依赖注入）

`InstantiationAwareBeanPostProcessor.postProcessProperties()` 处理 `@Autowired`、`@Value`、`@Resource`。

### 9. Aware回调

1. `BeanNameAware.setBeanName()`
2. `BeanClassLoaderAware.setBeanClassLoader()`
3. `BeanFactoryAware.setBeanFactory()`

### 10. 初始化前 — 扩展点

`BeanPostProcessor.postProcessBeforeInitialization()`

执行：
- `@PostConstruct` 方法（由 `InitDestroyAnnotationBeanPostProcessor` 处理）
- 其他Aware：`EnvironmentAware`、`ApplicationContextAware`、`ResourceLoaderAware` 等

### 11. 初始化

1. `InitializingBean.afterPropertiesSet()`
2. `@Bean(initMethod="xxx")` 指定的初始化方法

### 12. 初始化后 — 扩展点

`BeanPostProcessor.postProcessAfterInitialization()`

**AOP 就是在这里实现的**：返回的对象才是最终的Bean。

---

## 三、BeanPostProcessor 完整时序总结

```
1. InstantiationAwareBeanPostProcessor.postProcessBeforeInstantiation()
2. 实例化
3. MergedBeanDefinitionPostProcessor.postProcessMergedBeanDefinition()
4. InstantiationAwareBeanPostProcessor.postProcessAfterInstantiation()
5. 属性赋值（依赖注入）
6. InstantiationAwareBeanPostProcessor.postProcessProperties()
7. Aware 回调
8. BeanPostProcessor.postProcessBeforeInitialization()
9. 初始化（InitializingBean + init-method）
10. BeanPostProcessor.postProcessAfterInitialization()
```

## 四、Bean的销毁过程

销毁发生在 `context.close()` 时。

判断是否为 DisposableBean：
1. 实现了 `DisposableBean` 接口
2. 实现了 `AutoCloseable` 接口
3. BeanDefinition 指定了 `destroyMethod`
4. `DestructionAwareBeanPostProcessor.requiresDestruction()` 判断
5. 有 `@PreDestroy` 方法的Bean

**销毁流程**：
```
1. 发布 ContextClosedEvent 事件
2. 调用 lifecycleProcessor.onClose()
3. 遍历 disposableBeans：
   a. 从单例池移除
   b. 调用 disposableBean.destroy()
   c. 递归销毁被依赖的Bean
   d. 销毁 inner beans
4. 清空 manualSingletonNames、allBeanNamesByType 等
```

**适配器模式**：不同销毁方式（`DisposableBean`/`AutoCloseable`/`destroyMethod`）统一适配为 `DisposableBeanAdapter`。

---

## 五、总结

Bean生命周期是Spring最核心的知识点，所有扩展点（BeanPostProcessor系列）都嵌入在生命周期中：

- **容器级**：`BeanFactoryPostProcessor`、`BeanDefinitionRegistryPostProcessor`
- **Bean级**：`BeanPostProcessor`、`InstantiationAwareBeanPostProcessor`、`MergedBeanDefinitionPostProcessor`
- **生命周期**：`@PostConstruct`、`InitializingBean`、`@PreDestroy`、`DisposableBean`
- **Aware**：`BeanNameAware`、`BeanFactoryAware`、`ApplicationContextAware` 等
