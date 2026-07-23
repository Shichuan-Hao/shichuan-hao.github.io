---
title: MyBatis执行SQL的流程分析
categories: [Java, MyBatis, 框架源码]
tags: [MyBatis, SQL执行, Executor, 一级缓存, 二级缓存, 设计模式, 插件拦截器]
author: hsc
date: 2022-06-03 00:00:00 +0800
description: 深入MyBatis执行SQL全流程源码，剖析Executor架构、一二级缓存机制、插件拦截器原理及涉及的设计模式全景。
mindmap: https://www.processon.com/view/link/6633749533bdbe4f3815a34b
---

# MyBatis执行SQL的流程分析

## 一、设计模式在MyBatis中的应用

MyBatis源码大量使用设计模式：

| 设计模式 | 应用场景 | 说明 |
|----------|---------|------|
| **建造者模式** | `SqlSessionFactoryBuilder` | 逐步构建复杂配置 |
| **工厂模式** | `SqlSessionFactory` | 创建SqlSession |
| **代理模式** | Mapper 接口代理 | `MapperProxy` 代理接口 |
| **模板方法模式** | `BaseExecutor`、`BaseTypeHandler` | 定义骨架，子类实现细节 |
| **装饰器模式** | `Cache` 系列 | LruCache、FifoCache 等装饰包装 |
| **策略模式** | `ExecutorType` | Simple/Reuse/Batch 三种执行器 |
| **责任链模式** | `InterceptorChain` | 插件拦截器链 |
| **外观模式** | `SqlSession` | 统一对外API |

---

## 二、核心执行流程

```
SqlSession.selectOne()
    │
    ▼
Configuration.getMappedStatement(statementId)
    │
    ▼
Executor.query(ms, parameter)
    │
    ▼ (CachingExecutor)
├── 二级缓存命中？
│   └── Yes → 直接返回
│   └── No → delegate.query()
    │
    ▼ (BaseExecutor)
├── 一级缓存命中？
│   └── Yes → 直接返回
│   └── No → queryFromDatabase()
    │
    ▼
StatementHandler → ParameterHandler → TypeHandler
    │
    ▼
JDBC 执行 SQL → ResultSetHandler → 结果映射
```

---

## 三、Executor 执行器架构

### 3.1 继承体系

```
Executor (接口)
  ├── BaseExecutor (抽象类，模板方法)
  │   ├── SimpleExecutor (默认，每次"执行"预处理Statement)
  │   ├── ReuseExecutor (复用Statement)
  │   └── BatchExecutor (批量执行)
  └── CachingExecutor (装饰器，二级缓存)
```

```
ExecutorType: SIMPLE | REUSE | BATCH
    │
    ▼
Configuration.newExecutor(type) → interceptorChain.pluginAll(executor) → 层层代理
```

### 3.2 BaseExecutor 核心方法

```java
// 模板方法
public <E> List<E> query(MappedStatement ms, Object parameter, RowBounds rowBounds,
                          ResultHandler resultHandler) throws SQLException {
    BoundSql boundSql = ms.getBoundSql(parameter);
    CacheKey key = createCacheKey(ms, parameter, rowBounds, boundSql);  // 缓存键
    
    // 一级缓存查询
    list = resultHandler == null ? (List<E>) localCache.getObject(key) : null;
    if (list != null) {
        return list;
    }
    
    // 查数据库
    list = queryFromDatabase(ms, parameter, rowBounds, resultHandler, key, boundSql);
    return list;
}
```

**一级缓存存储级别**：SQL语句 + 参数值 + 分页边界 → 生成 CacheKey。

### 3.3 执行器对比

| 执行器 | 特点 | 适用场景 |
|--------|------|---------|
| **SimpleExecutor** | 每次执行都预编译Statement | 默认，简单场景 |
| **ReuseExecutor** | Statement可复用 | 同SQL多次执行 |
| **BatchExecutor** | 批量执行，不会自动commit | 批量插入/更新 |
| **CachingExecutor** | 装饰BaseExecutor，增加二级缓存 | 开启二级缓存时 |

---

## 四、StatementHandler

负责与 JDBC Statement 交互：

```
StatementHandler (接口)
  ├── RoutingStatementHandler (路由)
  ├── SimpleStatementHandler (普通Statement)
  ├── PreparedStatementHandler (预编译，默认)
  └── CallableStatementHandler (存储过程)
```

PreparedStatementHandler 执行：
```java
// 1. ParameterHandler 设置参数
parameterHandler.setParameters((PreparedStatement) statement);
// 2. 执行SQL
ps.execute();
// 3. ResultSetHandler 处理结果集
resultSetHandler.handleResultSets(ps);
```

---

## 五、ResultSetHandler 结果映射

将 JDBC ResultSet 映射为 Java 对象：

```
ResultSetHandler
  └── DefaultResultSetHandler
      ├── handleResultSets() → 遍历全部 ResultSet
      ├── handleRowValues() → 处理行数据
      │   ├── 简单类型 → TypeHandler 转换
      │   └── 复杂对象（嵌套映射） → 递归解析
      ├── 一对多关联处理 → <collection>
      └── 一对一关联处理 → <association>
```

### 懒加载实现

```java
// 结果对象是 proxy，访问延迟属性时才去查
// 需要 <collection fetchType="lazy"> 配合
```

---

## 六、插件（拦截器）机制

MyBatis支持拦截四个核心接口：

| 可拦截对象 | 方法 |
|-----------|------|
| **Executor** | update / query / flushStatements / commit / rollback 等 |
| **StatementHandler** | prepare / parameterize / batch / update / query |
| **ParameterHandler** | getParameterObject / setParameters |
| **ResultSetHandler** | handleResultSets / handleOutputParameters |

### 插件示例（SQL打印拦截器）

```java
@Intercepts({
    @Signature(type = StatementHandler.class, method = "prepare", args = {Connection.class})
})
public class SqlPrintInterceptor implements Interceptor {
    @Override
    public Object intercept(Invocation invocation) throws Throwable {
        StatementHandler handler = (StatementHandler) invocation.getTarget();
        String sql = handler.getBoundSql().getSql();
        System.out.println("SQL: " + sql);
        return invocation.proceed();
    }
}
```

### 插件原理（责任链+动态代理）

```java
// InterceptorChain.pluginAll(target)
for (Interceptor interceptor : interceptors) {
    target = interceptor.plugin(target);   // Plugin.wrap()
}

// Plugin.wrap() → 用 JDK 动态代理层层包装
```

每个拦截器都会生成一个 `Plugin`（实现 `InvocationHandler`）：
1. 调用时判断是否被拦截
2. 被拦截 → 执行 `interceptor.intercept()`
3. 不被拦截 → `invocation.proceed()` → 交给下一个 Plugin

---

## 七、缓存机制

### 一级缓存（Local Cache）

- **作用范围**：SqlSession 级别
- **默认开启**，无法关闭
- **清除时机**：commit / close / CUD 操作 / clearCache()

**失效场景**：
- 不同 SqlSession
- 同一 SqlSession 中执行了 CUD（insert/update/delete）
- 手动 clearCache()
- Spring 整合下每个SQL独立SqlSession（见Spring整合MyBatis篇章）

### 二级缓存

- **作用范围**：Mapper 命名空间级别
- **默认关闭**，需配置 `<cache/>` 开启
- 跨 SqlSession 共享
- 先查二级缓存，再查一级缓存

```xml
<cache eviction="LRU" flushInterval="60000" size="512" readOnly="true"/>
```

**执行顺序**：

```
CachingExecutor.query()
   ├── 二级缓存命中？ → 返回
   └── 未命中 → BaseExecutor.query()
       ├── 一级缓存命中？ → 返回 + 存二级缓存
       └── 未命中 → DB → 存一级缓存 + 存二级缓存
```

---

## 八、完整SQL执行流程总结

```
1. SqlSession.selectOne()
2. Configuration.getMappedStatement()
3. Executor.query()
    ├── CachingExecutor: 查二级缓存
    └── BaseExecutor: 查一级缓存
4. queryFromDatabase() → doQuery()
5. StatementHandler:
    ├── prepare() → 获取JDBC Connection + 预编译SQL
    └── parameterize() → ParameterHandler.setParameters() 设参
6. StatementHandler.query() → JDBC执行
7. ResultSetHandler.handleResultSets() → 结果集映射为对象
8. 返回结果
```

```
涉及的设计模式：
建造者 → SqlSessionFactoryBuilder
工厂 → SqlSessionFactory
代理 → MapperProxy, Plugin
模板方法 → BaseExecutor
装饰器 → CachingExecutor, Cache系列
策略 → ExecutorType
责任链 → InterceptorChain
```
