---



title: "Spring之整合Mybatis底层源码解析"
description: "Spring 之整合 Mybatis 底层源码解析.md"
author: hsc
date: 2022-06-09 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis', 'Spring事务']
toc: true



---

13-Spring 之整合 Mybatis 底层源码解析.md

整合核心思路由很多框架都需要和 Spring 进行整合,而整合的核心思想就是把其他框架所产生的对象放到 Spring 容器中,让其成为 Bean。
比如 Mybatis,Mybatis 框架可以单独使用,而单独使用 Mybatis 框架就需要用到 Mybatis 所提供的一些类构造出对应的对象,然后使用该对象,就能使用到 Mybatis 框架给我们提供的功能,和 Mybatis 整合 Spring 就是为了将这些对象放入 Spring 容器中成为 Bean,只要成为了 Bean,在我们的 Spring 项目中就能很方便的使用这些对象了,也就能很方便的使用 Mybatis 框架所提供的功能了。
Mybatis-Spring 1.3.2 版本底层源码执行流程
1. 通过@MapperScan 导入了 MapperScannerRegistrar 类
2. MapperScannerRegistrar 类实现了 ImportBeanDefinitionRegistrar 接口,所以 Spring 在启动时会调用 MapperScannerRegistrar 类中的 registerBeanDefinitions 方法
3. 在 registerBeanDefinitions 方法中定义了一个 ClassPathMapperScanner 对象,用来扫描 mapper
4. 设置 ClassPathMapperScanner 对象可以扫描到接口,因为在 Spring 中是不会扫描接口的
5. 同时因为 ClassPathMapperScanner 中重写了 isCandidateComponent 方法,导致 isCandidateComponent 只会认为接口是备选者 Component
6. 通过利用 Spring 的扫描后,会把接口扫描出来并且得到对应的 BeanDefinition
7. 接下来把扫描得到的 BeanDefinition 进行修改,把 BeanClass 修改为 MapperFactoryBean,把 AutowireMode 修改为 byType
8. 扫描完成后,Spring 就会基于 BeanDefinition 去创建 Bean 了,相当于每个 Mapper 对应一个 FactoryBean
9. 在 MapperFactoryBean 中的 getObject 方法中,调用了 getSqlSession()去得到一个 sqlSession 对象,然后根据对应的 Mapper 接口生成一个 Mapper 接口代理对象,这个代理对象就成为 Spring 容器中的 Bean
10. sqlSession 对象是 Mybatis 中的,一个 sqlSession 对象需要 SqlSessionFactory 来产生
11. MapperFactoryBean 的 AutowireMode 为 byType,所以 Spring 会自动调用 set 方法,有两个 set 方法,一个 setSqlSessionFactory,一个 setSqlSessionTemplate,而这两个方法执行的前提是根据方法参数类型能找到对应的 bean,所以 Spring 容器中要存在 SqlSessionFactory 类型的 bean 或者 SqlSessionTemplate 类型的 bean。
12. 如果你定义的是一个 SqlSessionFactory 类型的 bean,那么最终也会被包装为一个 SqlSessionTemplate 对象,并且赋值给 sqlSession 属性
13. 而在 SqlSessionTemplate 类中就存在一个 getMapper 方法,这个方法中就产生一个 Mapper 接口代理对象
14. 到时候,当执行该代理对象的某个方法时,就会进入到 Mybatis 框架的底层执行流程,详细的请看下图 Spring 整合 Mybatis 之后 SQL 执行流程:
https://www.processon.com/view/link/6152cc385653bb6791db436cMybatis-Spring 2.0.6 版本(最新版)底层源码执行流程

### 1. 通过@MapperScan 导入了 MapperScannerRegistrar 类
### 2. MapperScannerRegistrar 类实现了 ImportBeanDefinitionRegistrar 接口,所以 Spring 在启动时会调用 MapperScannerRegistrar 类中的 registerBeanDefinitions 方法
### 3. 在 registerBeanDefinitions 方法中注册一个 MapperScannerConfigurer 类型的 BeanDefinition
### 4. 而 MapperScannerConfigurer 实现了 BeanDefinitionRegistryPostProcessor 接口,所以 Spring 在启动过程中时会调用它的 postProcessBeanDefinitionRegistry()方法
### 5. 在 postProcessBeanDefinitionRegistry 方法中会生成一个 ClassPathMapperScanner 对象,然后进行扫描
### 6. 后续的逻辑和 1.3.2 版本一样。
带来的好处是,可以不使用@MapperScan 注解,而可以直接定义一个 Bean,比如:
@Beanpublic MapperScannerConfigurer mapperScannerConfigurer() {MapperScannerConfigurer mapperScannerConfigurer = new MapperScannerConfigurer();
mapperScannerConfigurer.setBasePackage("com.luban");
return mapperScannerConfigurer;
}Spring 整合 Mybatis 后一级缓存失效问题先看下图:
Spring 整合 Mybatis 之后 SQL 执行流程:
但是在 Spring 整合 Mybatis 后,如果没有执行某个方法时,该方法上没有加@Transactional 注解,也就是没有开启 Spring 事务,那么后面在执行具体 sql 时,没执行一个 sql 时都会新生成一个 SqlSession 对象来执行该 sql,这就是我们说的一级缓存失效(也就是没有使用同一个 SqlSession 对象),而如果开启了 Spring 事务,那么该 Spring 事务中的多个 sql,在执行时会使用同一个 SqlSession 对象,从而一级缓存生效,具体的底层执行流程在上图。
个人理解:实际上 Spring 整合 Mybatis 后一级缓存失效并不是问题,是正常的实现,因为,一个方法如果没有开启 Spring 事务,那么在执行 sql 时候,那就是每个 sql 单独一个事务来执行,也就是单独一个 SqlSession 对象来执行该 sql,如果开启了 Spring 事务,那就是多个 sql 属于同一个事务,那自然就应该用一个 SqlSession 来执行这多个 sql。所以,在没有开启 Spring 事务的时候,SqlSession 的一级缓存并不是失效了,而是存在的生命周期太短了(执行完一个 sql 后就被销毁了,下一个 sql 执行时又是一个新的 SqlSession 了)。
