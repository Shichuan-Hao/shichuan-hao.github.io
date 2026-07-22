---


title: "Spring之事务底层源码解析"
description: "Spring 之事务底层源码解析.md..."
author: hsc
date: 2022-07-13 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis', 'IOC', 'AOP', 'Spring事务']
toc: true


---

16-Spring 之事务底层源码解析.md

@EnableTransactionManagement 工作原理开启 Spring 事务本质上就是增加了一个 Advisor,但我们使用@EnableTransactionManagement 注解来开启 Spring 事务是,该注解代理的功能就是向 Spring 容器中添加了两个 Bean:
1. AutoProxyRegistrar
2. ProxyTransactionManagementConfigurationAutoProxyRegistrar 主要的作用是向 Spring 容器中注册了一个 InfrastructureAdvisorAutoProxyCreator 的 Bean。
而 InfrastructureAdvisorAutoProxyCreator 继承了 AbstractAdvisorAutoProxyCreator,所以这个类的主要作用就是开启自动代理的作用,也就是一个 BeanPostProcessor,会在初始化后步骤中去寻找 Advisor 类型的 Bean,并判断当前某个 Bean 是否有匹配的 Advisor,是否需要利用动态代理产生一个代理对象。
ProxyTransactionManagementConfiguration 是一个配置类,它又定义了另外三个 bean:
1. BeanFactoryTransactionAttributeSourceAdvisor:一个 Advisor
2. AnnotationTransactionAttributeSource:相当于 BeanFactoryTransactionAttributeSourceAdvisor 中的 Pointcut
3. TransactionInterceptor:相当于 BeanFactoryTransactionAttributeSourceAdvisor 中的 AdviceAnnotationTransactionAttributeSource 就是用来判断某个类上是否存在@Transactional 注解,或者判断某个方法上是否存在@Transactional 注解的。
TransactionInterceptor 就是代理逻辑,当某个类中存在@Transactional 注解时,到时就产生一个代理对象作为 Bean,代理对象在执行某个方法时,最终就会进入到 TransactionInterceptor 的 invoke()方法。
Spring 事务基本执行原理一个 Bean 在执行 Bean 的创建生命周期时,会经过 InfrastructureAdvisorAutoProxyCreator 的初始化后的方法,会判断当前当前 Bean 对象是否和 BeanFactoryTransactionAttributeSourceAdvisor 匹配,匹配逻辑为判断该 Bean 的类上是否存在@Transactional 注解,或者类中的某个方法上是否存在@Transactional 注解,如果存在则表示该 Bean 需要进行动态代理产生一个代理对象作为 Bean 对象。
该代理对象在执行某个方法时,会再次判断当前执行的方法是否和 BeanFactoryTransactionAttributeSourceAdvisor 匹配,如果匹配则执行该 Advisor 中的 TransactionInterceptor 的 invoke()方法,执行基本流程为:

### 1. 利用所配置的 PlatformTransactionManager 事务管理器新建一个数据库连接
### 2. 修改数据库连接的 autocommit 为 false
### 3. 执行 MethodInvocation.proceed()方法,简单理解就是执行业务方法,其中就会执行 sql
### 4. 如果没有抛异常,则提交
### 5. 如果抛了异常,则回滚 Spring 事务详细执行流程 Spring 事务执行流程图:https://www.processon.com/view/link/5fab6edf1e0853569633cc06Spring 事务传播机制在开发过程中,经常会出现一个方法调用另外一个方法,那么这里就涉及到了多种场景,比如 a()调用 b():
### 1. a()和 b()方法中的所有 sql 需要在同一个事务中吗?
### 2. a()和 b()方法需要单独的事务吗?
### 3. a()需要在事务中执行,b()还需要在事务中执行吗?
### 4. 等等情况...
所以,这就要求 Spring 事务能支持上面各种场景,这就是 Spring 事务传播机制的由来。那 Spring 事务传播机制是如何实现的呢?
先来看上述几种场景中的一种情况,a()在一个事务中执行,调用 b()方法时需要新开一个事务执行:
1. 首先,代理对象执行 a()方法前,先利用事务管理器新建一个数据库连接 a
2. 将数据库连接 a 的 autocommit 改为 false
3. 把数据库连接 a 设置到 ThreadLocal 中
4. 执行 a()方法中的 sql
5. 执行 a()方法过程中,调用了 b()方法(注意用代理对象调用 b()方法)
i. 代理对象执行 b()方法前,判断出来了当前线程中已经存在一个数据库连接 a 了,表示当前线程其实已经拥有一个 Spring 事务了,则进行挂起 ii. 挂起就是把 ThreadLocal 中的数据库连接 a 从 ThreadLocal 中移除,并放入一个挂起资源对象中 iii. 挂起完成后,再次利用事务管理器新建一个数据库连接 biv. 将数据库连接 b 的 autocommit 改为 falsev. 把数据库连接 b 设置到 ThreadLocal 中 vi. 执行 b()方法中的 sqlvii. b()方法正常执行完,则从 ThreadLocal 中拿到数据库连接 b 进行提交 viii. 提交之后会恢复所挂起的数据库连接 a,这里的恢复,其实只是把在挂起资源对象中所保存的数据库连接 a 再次设置到 ThreadLocal 中
6. a()方法正常执行完,则从 ThreadLocal 中拿到数据库连接 a 进行提交

这个过程中最为核心的是:在执行某个方法时,判断当前是否已经存在一个事务,就是判断当前线程的 ThreadLocal 中是否存在一个数据库连接对象,如果存在则表示已经存在一个事务了。
Spring 事务传播机制分类其中,以非事务方式运行,表示以非 Spring 事务运行,表示在执行这个方法时,Spring 事务管理器不会去建立数据库连接,执行 sql 时,由 Mybatis 或 JdbcTemplate 自己来建立数据库连接来执行 sql。
案例分析情况 1@Componentpublic class UserService {@Autowiredprivate UserService userService;
@Transactionalpublic void test() {// test 方法中的 sqluserService.a();
}@Transactionalpublic void a() {// a 方法中的 sql}}默认情况下传播机制为 REQUIRED,表示当前如果没有事务则新建一个事务,如果有事务则在当前事务中执行。
所以上面这种情况的执行流程如下:
1. 新建一个数据库连接 conn
2. 设置 conn 的 autocommit 为 false
3. 执行 test 方法中的 sql
4. 执行 a 方法中的 sql
5. 执行 conn 的 commit()方法进行提交情况 2 假如是这种情况

@Componentpublic class UserService {@Autowiredprivate UserService userService;
@Transactionalpublic void test() {// test 方法中的 sqluserService.a();
int result = 100/0;
}@Transactionalpublic void a() {// a 方法中的 sql}}所以上面这种情况的执行流程如下:
1. 新建一个数据库连接 conn
2. 设置 conn 的 autocommit 为 false
3. 执行 test 方法中的 sql
4. 执行 a 方法中的 sql
5. 抛出异常
6. 执行 conn 的 rollback()方法进行回滚,所以两个方法中的 sql 都会回滚掉情况 3 假如是这种情况:
@Componentpublic class UserService {@Autowiredprivate UserService userService;
@Transactionalpublic void test() {// test 方法中的 sqluserService.a();
}@Transactionalpublic void a() {// a 方法中的 sqlint result = 100/0;
}}所以上面这种情况的执行流程如下:

### 1. 新建一个数据库连接 conn
### 2. 设置 conn 的 autocommit 为 false
### 3. 执行 test 方法中的 sql
### 4. 执行 a 方法中的 sql
### 5. 抛出异常
### 6. 执行 conn 的 rollback()方法进行回滚,所以两个方法中的 sql 都会回滚掉情况 4 如果是这种情况:
@Componentpublic class UserService {@Autowiredprivate UserService userService;
@Transactionalpublic void test() {// test 方法中的 sqluserService.a();
}@Transactional(propagation = Propagation.REQUIRES_NEW)
public void a() {// a 方法中的 sqlint result = 100/0;
}}所以上面这种情况的执行流程如下:
1. 新建一个数据库连接 conn
2. 设置 conn 的 autocommit 为 false
3. 执行 test 方法中的 sql
4. 又新建一个数据库连接 conn2
5. 执行 a 方法中的 sql
6. 抛出异常
7. 执行 conn2 的 rollback()方法进行回滚
8. 继续抛异常,对于 test()方法而言,它会接收到一个异常,然后抛出
9. 执行 conn 的 rollback()方法进行回滚,最终还是两个方法中的 sql 都回滚了 Spring 事务强制回滚正常情况下,a()调用 b()方法时,如果 b()方法抛了异常,但是在 a()方法捕获了,那么 a()的事务还是会正常提交的,但是有的时候,我们捕获异常可能仅仅只是不把异常信息返回给客户端,而是为了返回一些更友好的错误信息,而这个时候,我们还是希望事务能回滚的,那这个时候就得告诉 Spring 把当前事务回滚掉,做法就是:

@Transactionalpublic void test(){// 执行 sqltry {b();
} catch (Exception e) {// 构造友好的错误信息返回 TransactionAspectSupport.currentTransactionStatus().setRollbackOnly();
}}public void b() throws Exception {throw new Exception();
}TransactionSynchronizationSpring 事务有可能会提交,回滚、挂起、恢复,所以 Spring 事务提供了一种机制,可以让程序员来监听当前 Spring 事务所处于的状态。

@Componentpublic class UserService {@Autowiredprivate JdbcTemplate jdbcTemplate;
@Autowiredprivate UserService userService;
@Transactionalpublic void test(){TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {@Overridepublic void suspend() {System.out.println("test 被挂起了");
}@Overridepublic void resume() {System.out.println("test 被恢复了");
}@Overridepublic void beforeCommit(boolean readOnly) {System.out.println("test 准备要提交了");
}@Overridepublic void beforeCompletion() {System.out.println("test 准备要提交或回滚了");
}@Overridepublic void afterCommit() {System.out.println("test 提交成功了");
}@Overridepublic void afterCompletion(int status) {System.out.println("test 提交或回滚成功了");
}});
jdbcTemplate.execute("insert into t1 values(1,1,1,1,'1')");
System.out.println("test");
userService.a();
}@Transactional(propagation = Propagation.REQUIRES_NEW)
public void a(){TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {@Overridepublic void suspend() {System.out.println("a 被挂起了");
}@Override

public void resume() {System.out.println("a 被恢复了");
}@Overridepublic void beforeCommit(boolean readOnly) {System.out.println("a 准备要提交了");
}@Overridepublic void beforeCompletion() {System.out.println("a 准备要提交或回滚了");
}@Overridepublic void afterCommit() {System.out.println("a 提交成功了");
}@Overridepublic void afterCompletion(int status) {System.out.println("a 提交或回滚成功了");
}});
jdbcTemplate.execute("insert into t1 values(2,2,2,2,'2')");
System.out.println("a");
}}
