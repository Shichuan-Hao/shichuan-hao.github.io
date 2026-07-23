---
title: MyBatis解析全局配置文件源码解析
categories: [Java, MyBatis, 框架源码]
tags: [MyBatis, 全局配置, SqlSessionFactory, Configuration, XML解析, ORM]
author: hsc
date: 2022-06-01 00:00:00 +0800
description: 深入MyBatis全局配置文件解析源码，拆解SqlSessionFactory构建过程、Configuration初始化及XML标签解析全流程。
mindmap:
---

# MyBatis解析全局配置文件源码解析

## 一、MyBatis 概述

MyBatis 是一个**半自动ORM框架**：
- 需手写SQL，灵活性强
- 自动化程度不高，数据库迁移需修改配置

### 传统JDBC的四大问题

| 问题 | MyBatis 解决方案 |
|------|-----------------|
| 连接创建/释放频繁 | 配置数据连接池 |
| SQL硬编码在代码中 | SQL写道 XML 中与 Java 分离 |
| 占位符传参硬编码 | 自动映射 parameterType |
| 结果集解析硬编码 | 自动映射 resultType |

---

## 二、MyBatis 使用示例

```java
String resource = "mybatis-config.xml";
Reader reader = Resources.getResourceAsReader(resource);
SqlSessionFactory sqlMapper = new SqlSessionFactoryBuilder().build(reader);
SqlSession session = sqlMapper.openSession();
try {
    UserMapper mapper = session.getMapper(UserMapper.class);
    User user = mapper.selectById(1L);
    System.out.println(user.getUserName());
} finally {
    session.close();
}
```

四个步骤：
1. 解析配置文件 → SqlSessionFactory
2. SqlSessionFactory → SqlSession
3. SqlSession 执行 CRUD / 事务
4. 关闭 Session

---

## 三、启动流程分析

### 核心入口

```java
SqlSessionFactory sqlMapper = new SqlSessionFactoryBuilder().build(reader);
```

```java
public SqlSessionFactory build(InputStream inputStream, String environment, Properties properties) {
    XMLConfigBuilder parser = new XMLConfigBuilder(inputStream, environment, properties);
    return build(parser.parse());
}

public SqlSessionFactory build(Configuration config) {
    return new DefaultSqlSessionFactory(config);
}
```

**整个启动过程 = 将XML配置解析为 Configuration 对象，然后创建 SqlSessionFactory**。

### 解析配置核心方法

```java
private void parseConfiguration(XNode root) {
    propertiesElement(root.evalNode("properties"));           // 1. properties
    Properties settings = settingsAsProperties(...);          // 2. settings
    loadCustomVfs(settings);
    typeAliasesElement(root.evalNode("typeAliases"));         // 3. 类型别名
    pluginElement(root.evalNode("plugins"));                  // 4. 插件/拦截器
    objectFactoryElement(root.evalNode("objectFactory"));
    settingsElement(settings);                                // 5. 应用settings
    environmentsElement(root.evalNode("environments"));       // 6. 环境（数据源+事务管理器）
    databaseIdProviderElement(root.evalNode("databaseIdProvider"));
    typeHandlerElement(root.evalNode("typeHandlers"));        // 7. 类型处理器
    mapperElement(root.evalNode("mappers"));                  // 8. Mapper映射文件
}
```

### 各标签解析详情

| 解析步骤 | 说明 |
|----------|------|
| **properties** | 解析属性配置，优先级：代码传入 > properties文件 > property标签 |
| **settings** | 全局设置（缓存、懒加载、日志等），set到Configuration |
| **typeAliases** | 别名配置，MyBatis默认注册了大量别名 |
| **plugins** | 拦截器配置，可拦截 Executor/ParameterHandler/ResultSetHandler/StatementHandler |
| **environments** | 数据源 + 事务管理器配置 |
| **mappers** | 解析 mapper 映射文件（package/resource 两种方式） |

### 配置文件示例

```xml
<configuration>
    <properties resource="config.properties">
        <property name="username" value="dev_user"/>
    </properties>
    
    <settings>
        <setting name="cacheEnabled" value="true"/>
    </settings>
    
    <plugins>
        <plugin interceptor="com.github.pagehelper.PageInterceptor">
            <property name="pageSizeZero" value="true"/>
        </plugin>
    </plugins>
    
    <environments default="development">
        <environment id="development">
            <transactionManager type="JDBC"/>
            <dataSource type="POOLED">
                <property name="driver" value="com.mysql.jdbc.Driver"/>
                <property name="url" value="jdbc:mysql://localhost:3306/test"/>
            </dataSource>
        </environment>
    </environments>
    
    <mappers>
        <mapper resource="./mappers/UserMapper.xml"/>
    </mappers>
</configuration>
```

---

## 四、Configuration 对象

解析完成后生成 `Configuration` 对象，包含 MyBatis 所有配置信息：

| 属性 | 内容 |
|------|------|
| **environment** | 数据源配置 + 事务管理器 |
| **mappedStatements** | Map<String, MappedStatement>（每条SQL对应的配置） |
| **mapperRegistry** | Mapper 接口注册表 |
| **typeAliasRegistry** | 类型别名注册表 |
| **interceptorChain** | 拦截器链 |
| **cache** | 二级缓存配置 |

---

## 五、MyBatis 全局架构总结

```
mybatis-config.xml → SqlSessionFactoryBuilder.build()
    └── XMLConfigBuilder.parse()
        └── parseConfiguration()
            ├── properties → 属性注入
            ├── settings → 全局设置
            ├── typeAliases → 别名注册
            ├── plugins → 拦截器链
            ├── environments → 数据源 + 事务
            ├── typeHandlers → 类型转换
            └── mappers → SQL映射解析
    └── → Configuration 对象
    └── → DefaultSqlSessionFactory(configuration)
```
