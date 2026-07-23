---
title: Spring之事务底层源码解析
categories: [Java, Spring, 框架源码]
tags: [Spring, 事务, '@Transactional', 传播机制, TransactionInterceptor, 事务管理器, 回滚]
author: hsc
date: 2022-05-29 00:00:00 +0800
description: 深入Spring事务底层源码，解析@EnableTransactionManagement工作原理、事务执行流程、七种传播机制场景分析。
mindmap: https://www.processon.com/view/link/5fab6edf1e0853569633cc06
---

# Spring之事务底层源码解析

## 一、@EnableTransactionManagement 工作原理

开启Spring事务本质上就是增加了一个Advisor。

`@EnableTransactionManagement` 向Spring容器中添加了两个Bean：

| Bean | 作用 |
|------|------|
| `AutoProxyRegistrar` | 注册 `InfrastructureAdvisorAutoProxyCreator` |
| `ProxyTransactionManagementConfiguration` | 配置事务Advisor三件套 |

### InfrastructureAdvisorAutoProxyCreator

继承了 `AbstractAdvisorAutoProxyCreator`，是一个 `BeanPostProcessor`：
- 在Bean初始化后寻找Advisor类型的Bean
- 判断当前Bean是否有匹配的Advisor（是否需要代理）

### ProxyTransactionManagementConfiguration

定义了三个Bean：

| Bean | 角色 |
|------|------|
| `BeanFactoryTransactionAttributeSourceAdvisor` | Advisor |
| `AnnotationTransactionAttributeSource` | Pointcut（判断是否有@Transactional） |
| `TransactionInterceptor` | Advice（代理逻辑） |

> Pointcut 的作用：判断类/方法上是否存在 `@Transactional` 注解。
> Advice 的作用：代理对象执行方法时，最终进入 `TransactionInterceptor#invoke()`。

---

## 二、事务基本执行原理

```
Bean创建时：
  InfrastructureAdvisorAutoProxyCreator.postProcessAfterInitialization()
  └── 判断Bean是否匹配 BeanFactoryTransactionAttributeSourceAdvisor
      ├── 匹配：类或方法上有 @Transactional → 生成代理对象
      └── 不匹配：返回原始Bean

代理对象方法执行时：
  再次判断当前方法是否匹配 Advisior（可能类上有但方法上没有）
  └── 匹配 → 执行 TransactionInterceptor.invoke()
```

**TransactionInterceptor.invoke() 核心流程**：

```
1. 利用 TransactionManager 新建一个数据库连接
2. 修改 autocommit = false
3. 执行 MethodInvocation.proceed() → 执行业务方法（SQL）
4. 无异常 → commit
5. 有异常 → rollback
```

---

## 三、事务传播机制

### 3.1 什么是传播机制

一个方法调用另一个方法时的多种场景：

| 场景 | 传播行为 |
|------|---------|
| a() 和 b() 在同一个事务中 | REQUIRED（默认） |
| a() 和 b() 各自独立的事务 | REQUIRES_NEW |
| b() 不需要事务 | SUPPORTS / NOT_SUPPORTED |
| 必须存在事务 | MANDATORY |
| 绝对不能在事务中 | NEVER |

### 3.2 传播机制实现原理

核心是通过 **ThreadLocal 绑定数据库连接**来管理事务：

**REQUIRES_NEW 实现流程**：

```
1. 代理对象执行 a() 前：
   ├── 新建连接 a
   ├── autocommit = false
   └── 放入 ThreadLocal

2. a() 执行中调用 b()（通过代理对象）：
   ├── 发现 ThreadLocal 已有连接 a → 存在事务
   ├── REQUIRES_NEW → 挂起当前事务
   │   ├── 从 ThreadLocal 移除连接 a
   │   └── 存入挂起资源对象
   ├── 新建连接 b
   ├── autocommit = false
   └── 放入 ThreadLocal

3. b() 执行完：
   ├── 从 ThreadLocal 拿到连接 b → commit
   └── 恢复挂起的连接 a → 放回 ThreadLocal

4. a() 执行完：
   └── 从 ThreadLocal 拿到连接 a → commit
```

> 核心判断：当前线程的 ThreadLocal 中是否存在数据库连接 → 存在即表示已有事务。

### 3.3 七种传播行为

| 传播行为 | 说明 |
|----------|------|
| **REQUIRED** | 有事务则加入，无事务则新建（默认） |
| **REQUIRES_NEW** | 总是新建事务，挂起当前事务 |
| **SUPPORTS** | 有事务则加入，无事务则无事务运行 |
| **NOT_SUPPORTED** | 总是非事务运行，挂起当前事务 |
| **NEVER** | 有事务则抛异常 |
| **MANDATORY** | 有事务则加入，无事务则抛异常 |
| **NESTED** | 嵌套事务（通过savepoint实现） |

### 3.4 案例分析

**场景1：REQUIRED + 内层抛异常**

```java
@Transactional
public void test() {
    // test的SQL
    userService.a();  // a() 也标注 @Transactional(REQUIRED)
}

@Transactional
public void a() {
    // a的SQL
    int result = 100/0;  // 抛异常
}
```

结果：两个方法共享同一个事务 → 同一条连接 → 异常导致整个连接rollback → **两个SQL都回滚**。

**场景2：REQUIRES_NEW + 内层抛异常**

```java
@Transactional
public void test() {
    // test的SQL
    userService.a();
}

@Transactional(propagation = Propagation.REQUIRES_NEW)
public void a() {
    // a的SQL
    int result = 100/0;
}
```

流程：连接2（a的）rollback → 异常被test()收到继续抛 → 连接1（test的）也rollback → **两个SQL都回滚**。

### 3.5 强制回滚

```java
@Transactional
public void test() {
    try {
        b();
    } catch (Exception e) {
        // 捕获异常但希望回滚
        TransactionAspectSupport.currentTransactionStatus().setRollbackOnly();
    }
}
```

---

## 四、TransactionSynchronization

Spring事务提供监听机制，可以在事务的不同阶段执行回调：

```java
TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
    public void suspend() { }       // 挂起时
    public void resume() { }        // 恢复时
    public void beforeCommit(boolean readOnly) { }  // 提交前
    public void beforeCompletion() { }  // 提交或回滚前
    public void afterCommit() { }      // 提交后
    public void afterCompletion(int status) { }  // 提交或回滚后
});
```

---

## 五、总结

```
@EnableTransactionManagement
    ├── InfrastructureAdvisorAutoProxyCreator（= AOP自动代理入口）
    └── ProxyTransactionManagementConfiguration
        ├── BeanFactoryTransactionAttributeSourceAdvisor（Advisor）
        ├── AnnotationTransactionAttributeSource（Pointcut → 判断@Transactional）
        └── TransactionInterceptor（Advice → 事务逻辑）

事务执行流程：
    新建连接 → autocommit=false → 执行业务SQL → commit/rollback

传播机制核心：
    ThreadLocal 绑定连接 → 通过挂起/恢复实现
    
事务失效场景：
    this.method() 调用（绕过代理） → 事务不生效
```
