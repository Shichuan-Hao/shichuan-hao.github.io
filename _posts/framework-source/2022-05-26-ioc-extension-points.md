---
title: Spring IOC容器扩展点全景与实践演练
categories: [Java, Spring, 框架源码]
tags: [Spring, IOC, 扩展点, BeanFactoryPostProcessor, BeanPostProcessor, SmartLifecycle, 动态线程池, 环境感知]
author: hsc
date: 2022-05-26 00:00:00 +0800
description: 全景剖析Spring IOC容器扩展点，包括BeanDefinition注册、Bean创建、容器加载完毕等阶段的扩展机制，并通过动态线程池案例实战演练。
mindmap:
---

# Spring IOC容器扩展点全景与实践演练

## 一、扩展点分类

Spring IOC的扩展点按阶段分为四大类：

| 阶段 | 扩展接口 | 作用 |
|------|---------|------|
| BeanDefinition注册 | `BeanDefinitionRegistryPostProcessor` | 动态注册BeanDefinition |
| BeanDefinition修改 | `BeanFactoryPostProcessor` | 修改已注册的BeanDefinition |
| Bean创建过程 | `BeanPostProcessor` / `Aware` | 干预Bean创建的各环节 |
| 容器加载完毕 | `SmartInitializingSingleton` / `SmartLifecycle` / `ContextRefreshedEvent` | 容器启动后的初始化 |

---

## 二、BeanDefinition注册阶段扩展

### 2.1 三种注册方式

| 方式 | 特点 | 优缺点 |
|------|------|--------|
| **BeanDefinitionRegistryPostProcessor** | 标准Spring Bean，有完整生命周期 | ✅ 可注入依赖 / ❌ 无法获取Import注解信息 |
| **ImportBeanDefinitionRegistrar** | 需配合@Import使用，非Bean | ✅ 可获取`importingClassMetadata`（@Import所在类的注解）/ ❌ 无依赖注入 |
| **BeanFactoryPostProcessor** | 也可以做，但不明确 | ❌ 职责不清晰 |

### 2.2 BeanDefinitionRegistryPostProcessor 示例

```java
@Component
public class MyBeanDefinitionRegistryPostProcessor implements BeanDefinitionRegistryPostProcessor {
    @Override
    public void postProcessBeanDefinitionRegistry(BeanDefinitionRegistry registry) {
        BeanDefinitionBuilder builder = BeanDefinitionBuilder.genericBeanDefinition(XushuService.class);
        BeanDefinition bd = builder.getBeanDefinition();
        bd.getPropertyValues().add("age", 18);
        bd.setLazyInit(true);
        registry.registerBeanDefinition("xushuService3", bd);
    }
    
    @Override
    public void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
        // 修改BeanDefinition
    }
}
```

### 2.3 ImportBeanDefinitionRegistrar 特别之处

虽然不是Bean，但在Spring解析@Import时，会主动调用Aware方法：
- `BeanClassLoaderAware`
- `BeanFactoryAware`
- `EnvironmentAware`
- `ResourceLoaderAware`

```java
public class MyImportBeanDefinitionRegistrar implements ImportBeanDefinitionRegistrar {
    @Override
    public void registerBeanDefinitions(AnnotationMetadata metadata, BeanDefinitionRegistry registry) {
        // metadata可以获取@Import所在类上的所有注解信息
        // 这是MapperScan能拿到包路径做扫描的关键
    }
}
```

---

## 三、Bean创建阶段扩展

### 3.1 BeanPostProcessor

贯穿整个Bean生命周期，不同阶段做不同的事：

| 方法 | 时机 | 常用实现 |
|------|------|---------|
| `postProcessBeforeInstantiation` | 实例化前 | 可提前返回自定义对象 |
| `postProcessMergedBeanDefinition` | 合并BeanDefinition后 | Autowired解析注入点 |
| `postProcessAfterInstantiation` | 实例化后 | 控制是否属性填充 |
| `postProcessProperties` | 属性填充时 | @Autowired/@Value注入 |
| `postProcessBeforeInitialization` | 初始化前 | @PostConstruct |
| `postProcessAfterInitialization` | 初始化后 | AOP代理生成 |

### 3.2 Aware系列

基于Aware获取Spring组件（不用@Autowired，因为顺序问题）：

| Aware | 获取内容 |
|-------|---------|
| `BeanNameAware` | beanName |
| `BeanFactoryAware` | BeanFactory |
| `ApplicationContextAware` | ApplicationContext |
| `EnvironmentAware` | Environment |
| `ResourceLoaderAware` | ResourceLoader |

### 3.3 生命周期回调

用构造方法初始化不合适（拿不到Aware组件）→ 用初始化回调：

```
@PostConstruct → 早于 InitializingBean.afterPropertiesSet()
```

---

## 四、容器加载完毕扩展

### 4.1 SmartInitializingSingleton

所有单例Bean创建完后调用（不是SpringBoot的ApplicationRunner！）：

```java
@Component
public class MySmartInitializingSingleton implements SmartInitializingSingleton {
    @Override
    public void afterSingletonsInstantiated() {
        // 所有单例Bean都创建完了
    }
}
```

### 4.2 SmartLifecycle

控制组件随容器启停：

```java
@Component
public class MyLifecycle implements SmartLifecycle {
    boolean isRunning;
    
    @Override
    public void start() {
        isRunning = true;
        // 容器启动 → 定时任务启动 / 缓存预热
    }
    
    @Override
    public void stop() {
        isRunning = false;
        // 容器关闭 → 定时任务停止 / 缓存清空
    }
}
```

### 4.3 ContextRefreshedEvent

```java
@EventListener(ContextRefreshedEvent.class)
public void onRefresh(ContextRefreshedEvent event) {
    // 容器加载完毕
}
```

---

## 五、实战：动态线程池

### 5.1 需求

1. 根据配置动态创建线程池
2. 纳入Spring容器管理
3. 运行时可动态修改参数
4. 线程池监控与告警

### 5.2 实现步骤

#### Step 1：配置建模

```yaml
spring:
  dtp:
    executors:
      - poolName: dtpExecutor1
        corePoolSize: 5
        maximumPoolSize: 10
      - poolName: dtpExecutor2
        corePoolSize: 2
        maximumPoolSize: 15
```

#### Step 2：获取配置（EnvironmentAware + Binder）

```java
public class DtpBeanDefinitionRegistrar implements ImportBeanDefinitionRegistrar, EnvironmentAware {
    private Environment environment;
    
    @Override
    public void registerBeanDefinitions(AnnotationMetadata metadata, BeanDefinitionRegistry registry) {
        // Binder批量绑定
        BindResult<DtpProperties> bindResult = Binder.get(environment)
            .bind("spring.dtp", DtpProperties.class);
        DtpProperties dtpProperties = bindResult.get();
        
        // 动态注册BeanDefinition
        for (ThreadPoolProperties p : dtpProperties.getExecutors()) {
            BeanDefinitionBuilder builder = BeanDefinitionBuilder
                .genericBeanDefinition(DtpThreadPoolExecutor.class);
            builder.addConstructorArgValue(p);
            registry.registerBeanDefinition(p.getPoolName(), builder.getBeanDefinition());
        }
    }
}
```

> 为什么不用 `@Value`/`@ConfigurationProperties`？— 因为顺序原因！注册BeanDefinition时注解还没被解析。

#### Step 3：纳入管理（BeanPostProcessor）

```java
public class DtpBeanPostProcessor implements BeanPostProcessor {
    @Override
    public Object postProcessAfterInitialization(Object bean, String beanName) {
        if (bean instanceof DtpThreadPoolExecutor) {
            DtpRegistry.registry(beanName, (ThreadPoolExecutor) bean);
        }
        return bean;
    }
}
```

#### Step 4：动态刷新

```java
// 通过事件解耦
@EventListener(DtpEvent.class)
public void onDtpEvent(DtpEvent event) {
    DtpRegistry.refresh(event.getProperties().getPoolName(), event.getProperties());
}
```

#### Step 5：监控告警（SmartLifecycle）

```java
public class DtpMonitor implements SmartLifecycle {
    @Override
    public void start() {
        // 定时调度监控任务
        scheduledFuture = Executors.newSingleThreadScheduledExecutor()
            .scheduleAtFixedRate(() -> {
                monitor();  // 记录指标
                alarm();    // 超阈值告警
            }, 5, 5, TimeUnit.SECONDS);
        isRunning = true;
    }
    
    @Override
    public void stop() {
        scheduledFuture.cancel(false);
    }
}
```

#### Step 6：封装为插件（@EnableXXX）

```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Import(DtpImportSelector.class)
public @interface EnableDynamicThreadPool {}

// 使用
@EnableDynamicThreadPool
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

---

## 六、总结

Spring扩展点全景图：

```
BeanDefinition注册阶段：
  ImportBeanDefinitionRegistrar (可获取@Import注解信息)
  BeanDefinitionRegistryPostProcessor (标准Bean，可注入依赖)

BeanDefinition修改阶段：
  BeanFactoryPostProcessor

Bean创建阶段：
  BeanPostProcessor 全系列
  Aware 系列
  生命周期回调 (@PostConstruct / InitializingBean)

容器加载完毕：
  SmartInitializingSingleton
  SmartLifecycle (随容器启停)
  ContextRefreshedEvent (事件通知)
```
