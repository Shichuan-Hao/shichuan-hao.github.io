---
title: Spring整合MyBatis底层源码解析
categories: [Java, Spring, MyBatis, 框架源码]
tags: [Spring, MyBatis, MapperScan, MapperScannerRegistrar, MapperFactoryBean, SqlSession, 一级缓存]
author: hsc
date: 2022-05-27 00:00:00 +0800
description: 深入Spring整合MyBatis底层原理，剖析@MapperScan扫描注册流程、MapperFactoryBean、SqlSession集成及一级缓存失效根因分析。
mindmap: https://www.processon.com/view/link/6152cc385653bb6791db436c
---

# Spring整合MyBatis底层源码解析

## 一、整合核心思想

框架整合的核心思想：**把其他框架所产生的对象放到Spring容器中，让其成为Bean。**

MyBatis框架可以单独使用：
```java
SqlSessionFactory factory = new SqlSessionFactoryBuilder().build(inputStream);
SqlSession session = factory.openSession();
UserMapper mapper = session.getMapper(UserMapper.class);
```

整合Spring后：`@Autowired UserMapper mapper` 就能直接用。

---

## 二、MyBatis-Spring 1.3.2 版本流程

```
1. @MapperScan("com.xxx.mapper") 导入 MapperScannerRegistrar
2. MapperScannerRegistrar 实现 ImportBeanDefinitionRegistrar
   └── registerBeanDefinitions() 中创建 ClassPathMapperScanner 扫描
3. 设置 scanner 可以扫描接口（Spring默认不扫描接口）
4. 重写 isCandidateComponent → 只认接口
5. 扫描得到的接口 → 生成 BeanDefinition
6. 修改 BeanDefinition:
   ├── beanClass 改为 MapperFactoryBean
   └── autowireMode 改为 byType
7. Spring 基于 BeanDefinition 创建 Bean
8. MapperFactoryBean.getObject():
   └── getSqlSession() → sqlSession.getMapper(接口) → 返回代理对象
9. sqlSession 需要 SqlSessionFactory 来产生
10. MapperFactoryBean 的 autowireMode=byType → 自动注入:
    └── setSqlSessionFactory() / setSqlSessionTemplate()
```

### 关键设计点

| 步骤 | 设计 |
|------|------|
| 扫描接口 | 重写 `isCandidateComponent`，让Spring扫描MyBatis Mapper接口 |
| BeanDefinition伪装 | `beanClass` 从接口改为 `MapperFactoryBean` |
| 自动注入 | `autowireMode=byType` 自动找到 `SqlSessionFactory` |

---

## 三、MyBatis-Spring 2.0.6 版本改进

```
1. @MapperScan 导入 MapperScannerRegistrar
2. MapperScannerRegistrar.registerBeanDefinitions() → 注册 MapperScannerConfigurer 的BeanDefinition
3. MapperScannerConfigurer 实现 BeanDefinitionRegistryPostProcessor
   └── postProcessBeanDefinitionRegistry() 中扫描
4. 后续逻辑与1.3.2一致
```

**改进优势**：可以不使用 `@MapperScan`，直接定义Bean：

```java
@Bean
public MapperScannerConfigurer mapperScannerConfigurer() {
    MapperScannerConfigurer configurer = new MapperScannerConfigurer();
    configurer.setBasePackage("com.example.mapper");
    return configurer;
}
```

---

## 四、核心类关系

```
@MapperScan("xxx")
    │
    ▼
MapperScannerRegistrar (ImportBeanDefinitionRegistrar)
    │
    ▼
ClassPathMapperScanner (扫描接口)
    │
    ▼
interface UserMapper → BeanDefinition { beanClass = MapperFactoryBean }
    │
    ▼
MapperFactoryBean (FactoryBean)
    │
    ├── SqlSessionFactory / SqlSessionTemplate (byType注入)
    └── getObject() → Mapper代理对象 → 最终存入Spring容器
```

**SqlSessionFactory → SqlSessionTemplate 转换**：如果定义的是 `SqlSessionFactory`，会被包装成 `SqlSessionTemplate`：

```java
// SqlSessionTemplate 内部持有 SqlSession
// 每次真正操作时通过 SqlSessionInterceptor 获取新的 SqlSession
```

---

## 五、一级缓存失效问题

### 5.1 表现

同一事务中的多个SQL使用同一个SqlSession → 一级缓存有效  
没有事务的每个SQL各自获得新SqlSession → 一级缓存"失效"

### 5.2 根因

```
Spring整合后的SQL执行时序：

有 @Transactional：
  getSqlSession() → 当前事务的SqlSession（同一个）→ 一级缓存有效

无 @Transactional：
  getSqlSession() → 每次new SqlSession → 执行SQL → close → 一级缓存"无效"
```

### 5.3 结论

> **这不是Bug，是合理设计。**

- 无事务 → 每个SQL独立执行 → 独立SqlSession → 用完关闭
- 有事务 → 多个SQL同一事务 → 共享SqlSession → 一级缓存自然生效

一级缓存没有失效，只是生命周期太短（执行完一个SQL就销毁了）。

---

## 六、总结

```
Spring整合MyBatis本质：
1. @MapperScan 扫描接口 → BeanDefinition(beanClass=MapperFactoryBean)
2. MapperFactoryBean 是一个 FactoryBean
3. getObject() → SqlSession.getMapper() → 返回Mapper代理对象
4. 代理对象存入Spring容器 → @Autowired 注入即可使用

一级缓存：
├── 有 @Transactional → 共享SqlSession → 有效
└── 无 @Transactional → 独立SqlSession → 生命周期极短
```
