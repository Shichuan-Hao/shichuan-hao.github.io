---
title: Spring IOC容器加载重要组件全景
categories: [Java, Spring, 框架源码]
tags: [IOC, ApplicationContext, BeanFactory, BeanDefinitionReader, MetadataReader, 国际化, 资源加载, 事件机制, BeanPostProcessor, FactoryBean]
author: hsc
date: 2022-06-05 00:00:00 +0800
description: 全景梳理Spring IOC容器加载所有重要组件，涵盖BeanDefinitionReader/Scanner、ApplicationContext、国际化、资源加载、事件发布等基础设施。
mindmap: https://www.processon.com/view/link/5f15341b07912906d9ae8642
---


> [流程图](https://www.processon.com/view/link/5f15341b07912906d9ae8642)

## 一、读取配置

### 1.1 BeanDefinitionReader

不同的Spring容器使用不同的读取器，但读取后的Bean创建流程统一：

| 容器 | 读取器 |
|------|--------|
| `AnnotationConfigApplicationContext` | `AnnotatedBeanDefinitionReader` |
| `ClassPathXmlApplicationContext` | `XmlBeanDefinitionReader` |

**AnnotatedBeanDefinitionReader**

直接把类转换为BeanDefinition，解析类上的注解（`@Conditional`、`@Scope`、`@Lazy`、`@Primary`、`@DependsOn`、`@Role`、`@Description`）。

```java
AnnotatedBeanDefinitionReader reader = new AnnotatedBeanDefinitionReader(context);
reader.register(User.class);
System.out.println(context.getBean("user"));
```

**XmlBeanDefinitionReader**

解析 `<bean/>` 标签：

```java
XmlBeanDefinitionReader reader = new XmlBeanDefinitionReader(context);
int i = reader.loadBeanDefinitions("spring.xml");
System.out.println(context.getBean("user"));
```

### 1.2 ClassPathBeanDefinitionScanner

扫描指定包路径，扫描到的类上有 `@Component` → 解析为 BeanDefinition：

```java
ClassPathBeanDefinitionScanner scanner = new ClassPathBeanDefinitionScanner(context);
scanner.scan("com.xs");
System.out.println(context.getBean("userService"));
```

> 默认IncludeFilter = AnnotationTypeFilter(Component.class)

---

## 二、注册BeanDefinition

不同的Bean配置方式最终统一为 `BeanDefinition`：

| 方式 | 解析为 |
|------|--------|
| `<bean/>` | BeanDefinition |
| `@Bean` | BeanDefinition |
| `@Component`/`@Service`/`@Controller` | BeanDefinition |
| 编程式 `BeanDefinitionBuilder` | BeanDefinition |

### 编程式注册

```java
AbstractBeanDefinition bd = BeanDefinitionBuilder.genericBeanDefinition().getBeanDefinition();
bd.setBeanClass(User.class);
bd.setScope("prototype");          // 作用域
bd.setInitMethodName("init");      // 初始化方法
bd.setLazyInit(true);              // 懒加载
context.registerBeanDefinition("user", bd);
```

---

## 三、MetadataReader（元数据读取）

Spring 用 **ASM 技术** 解析类元数据（避免启动时加载所有类到JVM）：

```java
SimpleMetadataReaderFactory factory = new SimpleMetadataReaderFactory();
MetadataReader metadataReader = factory.getMetadataReader("com.xs.service.UserService");

ClassMetadata classMetadata = metadataReader.getClassMetadata();
System.out.println(classMetadata.getClassName());  // 类名

AnnotationMetadata annotationMetadata = metadataReader.getAnnotationMetadata();
annotationMetadata.getAnnotationTypes();  // 获取所有注解
```

> 为什么用ASM？ → 包扫描范围大时，用ASM解析.class文件，不需要把类加载到JVM，性能更高。

---

## 四、BeanFactory 继承体系

`ApplicationContext` 也是一种 `BeanFactory`（继承关系）：

```java
public interface ApplicationContext extends EnvironmentCapable, ListableBeanFactory,
    HierarchicalBeanFactory, MessageSource, ApplicationEventPublisher, ResourcePatternResolver { }
```

### DefaultListableBeanFactory — 核心实现

它实现了多个接口，功能极强大：

| 接口 | 功能 |
|------|------|
| `AliasRegistry` | 别名支持 |
| `BeanDefinitionRegistry` | BeanDefinition 注册/移除/获取 |
| `BeanFactory` | 按 name/type/alias 获取 Bean |
| `SingletonBeanRegistry` | 直接注册/获取单例 |
| `ListableBeanFactory` | 批量获取 beanNames、按类型获取 |
| `HierarchicalBeanFactory` | 父子容器 |
| `ConfigurableBeanFactory` | 设置类加载器、SPEL解析器、类型转换服务 |
| `AutowireCapableBeanFactory` | Bean创建过程自动装配 |

直接使用 DefaultListableBeanFactory（不依赖 ApplicationContext）：

```java
DefaultListableBeanFactory beanFactory = new DefaultListableBeanFactory();
AbstractBeanDefinition bd = BeanDefinitionBuilder.genericBeanDefinition().getBeanDefinition();
bd.setBeanClass(User.class);
beanFactory.registerBeanDefinition("user", bd);
System.out.println(beanFactory.getBean("user"));
```

---

## 五、ApplicationContext 附加功能

### 5.1 国际化（MessageSource）

```java
@Bean
public MessageSource messageSource() {
    ResourceBundleMessageSource m = new ResourceBundleMessageSource();
    m.setBasename("messages");
    return m;
}
// 使用
context.getMessage("test", null, new Locale("en_CN"));
```

### 5.2 资源加载

```java
// 文件
Resource r = context.getResource("file://D:/.../User.java");
// HTTP
Resource r = context.getResource("https://www.baidu.com");
// classpath
Resource r = context.getResource("classpath:spring.xml");
// 批量
Resource[] resources = context.getResources("classpath:com/xs/*.class");
```

### 5.3 运行时环境

```java
context.getEnvironment().getSystemEnvironment();
context.getEnvironment().getSystemProperties();
context.getEnvironment().getProperty("NO_PROXY");

// @PropertySource 添加properties文件到环境
@PropertySource("classpath:spring.properties")
```

### 5.4 事件发布

```java
// 定义监听器
@Bean
public ApplicationListener applicationListener() {
    return event -> System.out.println("收到事件: " + event);
}
// 发布事件
context.publishEvent("kkk");
```

### 5.5 BeanPostProcessor

干涉Bean创建过程：

```java
@Component
public class MyBPP implements BeanPostProcessor {
    @Override
    public Object postProcessBeforeInitialization(Object bean, String beanName) {
        if ("userService".equals(beanName)) {
            System.out.println("初始化前");
        }
        return bean;
    }
    @Override
    public Object postProcessAfterInitialization(Object bean, String beanName) {
        return bean;
    }
}
```

### 5.6 BeanFactoryPostProcessor

干涉BeanFactory的创建：

```java
@Component
public class MyBFPP implements BeanFactoryPostProcessor {
    @Override
    public void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
        System.out.println("加工beanFactory");
    }
}
```

### 5.7 FactoryBean

完全自定义Bean创建：

```java
@Component
public class ZhouyuFactoryBean implements FactoryBean<UserService> {
    @Override
    public UserService getObject() {
        return new UserService();  // 完全自己创建
    }
    @Override
    public Class<?> getObjectType() { return UserService.class; }
}
```

> FactoryBean vs @Bean：FactoryBean创建的对象**不经过完整生命周期**（不经过依赖注入等），而@Bean创建的Bean会经过完整生命周期。

### 5.8 ApplicationContext 启动流程手写版

```java
// 手动实现ApplicationContext的核心功能
DefaultListableBeanFactory factory = new DefaultListableBeanFactory();

// 1. 读取配置
AnnotatedBeanDefinitionReader reader = new AnnotatedBeanDefinitionReader(factory);
reader.register(AppConfig.class);

// 2. 解析@ComponentScan
AnnotatedBeanDefinition bd = (AnnotatedBeanDefinition) factory.getBeanDefinition("appConfig");
if (bd.getMetadata().hasAnnotation(ComponentScan.class.getName())) {
    ClassPathBeanDefinitionScanner scanner = new ClassPathBeanDefinitionScanner(factory);
    scanner.scan("com.xxx");
}

// 3. 创建所有Bean
factory.preInstantiateSingletons();
```

---

## 六、扫描过滤器

| FilterType | 说明 |
|-----------|------|
| `ANNOTATION` | 是否有某个注解 |
| `ASSIGNABLE_TYPE` | 是否是某个类 |
| `ASPECTJ` | 符合AspectJ表达式 |
| `REGEX` | 符合正则表达式 |
| `CUSTOM` | 自定义过滤逻辑 |

```java
@ComponentScan(value = "com.xs",
    excludeFilters = {@ComponentScan.Filter(type = FilterType.ASSIGNABLE_TYPE, classes = UserService.class)})
```

---

## 七、总结

```
Spring IOC = BeanDefinition 注册 + Bean 创建

容器层：
├── AnnotationConfigApplicationContext (注解驱动)
├── ClassPathXmlApplicationContext (XML驱动)
├── BeanDefinitionReader → 读取配置 → BeanDefinition
├── ClassPathBeanDefinitionScanner → 扫描+解析
└── DefaultListableBeanFactory → 核心Factory实现

ApplicationContext 附加能力：
├── 国际化 (MessageSource)
├── 资源加载 (ResourcePatternResolver)
├── 运行时环境 (EnvironmentCapable)
├── 事件机制 (ApplicationEventPublisher)
├── BeanPostProcessor → 干预Bean创建
├── BeanFactoryPostProcessor → 干预容器创建
└── FactoryBean → 完全自定义Bean
```
