---

title: "Abibaba分布式事务组件Seata内核源码剖析"
description: "Seata 源码分析会讲两节课: 1. 从全局事务角度分析 Seata 设计(侧重点在全局事务的设计) 2."
author: hsc
date: 2023-04-24 00:00:00 +0800
categories: ['Java 后端', '微服务']
tags: ['微服务', 'SpringCloud', 'Docker']
toc: true

---

Seata 源码分析会讲两节课:
1. 从全局事务角度分析 Seata 设计(侧重点在全局事务的设计)
2. 从两阶段提交,自动补偿机制,隔离性的角度分析 Seata 设计(侧重点在分支事务的设计)
1. Seata 整体架构
1.1 Seata 的三大角色在 Seata 的架构中,一共有三个角色:
TC (Transaction Coordinator) - 事务协调者维护全局和分支事务的状态,驱动全局事务提交或回滚。
TM (Transaction Manager) - 事务管理器定义全局事务的范围:开始全局事务、提交或回滚全局事务。
RM (Resource Manager) - 资源管理器管理分支事务处理的资源,与 TC 交谈以注册分支事务和报告分支事务的状态,并驱动分支事务提交或回滚。
其中,TC 为单独部署的 Server 服务端,TM 和 RM 为嵌入到应用中的 Client 客户端。
1.2 Seata 的生命周期在 Seata 中,一个分布式事务的生命周期如下:
1. TM 请求 TC 开启一个全局事务。 TC 会生成一个 XID 作为该全局事务的编号。 XID 会在微服务的调用链路中传播,保证将多个微服务的子事务关联在一起。
2. RM 请求 TC 将本地事务注册为全局事务的分支事务,通过全局事务的 XID 进行关联。
3. TM 请求 TC 告诉 XID 对应的全局事务是进行提交还是回滚。
4. TC 驱动 RM 们将 XID 对应的自己的本地事务进行提交还是回滚。
1.3 AT 模式设计思路

Seata AT 模式的核心是对业务无侵入,是一种改进后的两阶段提交,其设计思路如下:
一阶段:业务数据和回滚日志记录在同一个本地事务中提交,释放本地锁和连接资源。
二阶段:
提交异步化,非常快速地完成。
回滚通过一阶段的回滚日志进行反向补偿。
一阶段业务数据和回滚日志记录在同一个本地事务中提交,释放本地锁和连接资源。核心在于对业务 sql 进行解析,转换成 undolog,并同时入库,这是怎么做的呢?
二阶段分布式事务操作成功,则 TC 通知 RM 异步删除 undolog 分布式事务操作失败,TM 向 TC 发送回滚请求,RM 收到协调器 TC 发来的回滚请求,通过 XID 和 Branch ID 找到相应的回滚日志记录,通过回滚记录生成反向的更新 SQL 并执行,以完成分支的回滚。
2. Seata 核心接口和实现类 TransactionManagerDefaultTransactionManagerTransactionManagerHolder 为创建单例 TransactionManager 的工厂,可以使用 EnhancedServiceLoader 的 spi 机制加载用户自定义的类,默认为 DefaultTransactionManager。
GlobalTransactionGlobalTransaction 接口提供给用户开启事务,提交,回滚,获取状态等方法。
DefaultGlobalTransactionDefaultGlobalTransaction 是 GlobalTransaction 接口的默认实现,它持有 TransactionManager 对象,默认开启事务超时时间为 60 秒,默认名称为 default,因为调用者的业务方法可能多重嵌套创建多

个 GlobalTransaction 对象开启事务方法,因此 GlobalTransaction 有 GlobalTransactionRole 角色属性,只有 Launcher 角色的才有开启、提交、回滚事务的权利。
GlobalTransactionContextGlobalTransactionContext 为操作 GlobalTransaction 的工具类,提供创建新的 GlobalTransaction,获取当前线程有的 GlobalTransaction 等方法。
GlobalTransactionScannerGlobalTransactionScanner 继承 AbstractAutoProxyCreator 类,即实现了 SmartInstantiationAwareBeanPostProcessor 接口,会在 spring 容器启动初始化 bean 的时候,对 bean 进行代理操作。 wrapIfNecessary 为继承父类代理 bean 的核心方法,如果用户配置了 service.disableGlobalTransaction 为 false 属性则注解不生效直接返回,否则对 GlobalTransactional 或 GlobalLock 的方法进行拦截代理。
GlobalTransactionalInterceptorGlobalTransactionalInterceptor 实现 aop 的 MethodInterceptor 接口,对有@GlobalTransactional 或 GlobalLock 注解的方法进行代理。
TransactionalTemplateTransactionalTemplate 模板类提供了一个开启事务,执行业务,成功提交和失败回滚的模板方法 execute(TransactionalExecutor business)。
DefaultCoordinatorDefaultCoordinator 即为 TC,全局事务默认的事务协调器。它继承 AbstractTCInboundHandler 接口,为 TC 接收 RM 和 TM 的 request 请求数据,是进行相应处理的处理器。实现 TransactionMessageHandler 接口,去处理收到的 RPC 信息。实现 ResourceManagerInbound 接口,发送至 RM 的 branchCommit,branchRollback 请求。
CoreCore 接口为 seata 处理全球事务协调器 TC 的核心处理器,它继承 ResourceManagerOutbound 接口,接受来自 RM 的 rpc 网络请求(branchRegister,branchReport,lockQuery)。同时继承

TransactionManager 接口,接受来自 TM 的 rpc 网络请求(begin,commit,rollback,getStatus),另外提供提供 3 个接口方法。
ATCoreGlobalSessionGlobalSession 是 seata 协调器 DefaultCoordinator 管理维护的重要部件,当用户开启全局分布式事务,TM 调用 begin 方法请求至 TC,TC 则创建 GlobalSession 实例对象,返回唯一的 xid。它实现 SessionLifecycle 接口,提供 begin,changeStatus,changeBranchStatus,addBranch,removeBranch 等操作 session 和 branchSession 的方法。
BranchSessionBranchSession 为分支 session,管理分支数据,受 globalSession 统一调度管理,它的 lock 和 unlock 方法由 lockManger 实现。
LockManagerDefaultLockManager 是 LockManager 的默认实现,它获取 branchSession 的 lockKey,转换成 List<RowLock>,委派 Locker 进行处理。
LockerLocker 接口提供根据行数据获取锁,释放锁,是否锁住和清除所有锁的方法。
ResourceManagerResourceManager 是 seata 的重要组件之一,RM 负责管理分支数据资源的事务。
AbstractResourceManager 实现 ResourceManager 提供模板方法。 DefaultResourceManager 适配所有的 ResourceManager,所有方法调用都委派给对应负责的 ResourceManager 处理。
DataSourceManager 此为 AT 模式核心管理器,DataSourceManager 继承 AbstractResourceManager,管理数据库 Resouce 的注册,提交以及回滚等

AsyncWorker DataSourceManager 事务提交委派给 AsyncWorker 进行提交的,因为都成功了,无需回滚成功的数据,只需要删除生成的操作日志就行,采用异步方式,提高效率。
1 AsyncWorker#doBranchCommits2 > UndoLogManagerFactory.getUndoLogManager(dataSourceProxy.getDbType())
3 .batchDeleteUndoLog(xids, branchIds, conn)
UndoLogManagerResourceResource 能被 ResourceManager 管理并且能够关联 GlobalTransaction。
DataSourceProxyDataSourceProxy 实现 Resource 接口,BranchType 为 AT 自动模式。它继承 AbstractDataSourceProxy 代理类,所有的 DataSource 相关的方法调用传入的 targetDataSource 代理类的方法,除了创建 connection 方法为创建 ConnectionProxy 代理类。对象初始化时获取连接的 jdbcUrl 作为 resourceId,并注册至 DefaultResourceManager 进行管理。同时还提供获取原始连接不被代理的 getPlainConnection 方法。
ConnectionProxy1 private void doCommit() throws SQLException {2 if (context.inGlobalTransaction()) {3 processGlobalTransactionCommit();
4 } else if (context.isGlobalLockRequire()) {5 processLocalCommitWithGlobalLocks();
6 } else {7 targetConnection.commit();
8 }9 }

10 private void processGlobalTransactionCommit() throws SQLException {11 try {12 register();
13 } catch (TransactionException e) {14 recognizeLockKeyConflictException(e, context.buildLockKeys());
15 }16 try {17 UndoLogManagerFactory.getUndoLogManager(this.getDbType()).flushUndoLogs(this);
18 targetConnection.commit();
19 } catch (Throwable ex) {20 LOGGER.error("process connectionProxy commit error: {}", ex.getMessage(), ex);
21 report(false);
22 throw new SQLException(ex);
23 }24 if (IS_REPORT_SUCCESS_ENABLE) {25 report(true);
26 }27 context.reset();
28 }ExecuteTemplateExecuteTemplate 为具体 statement 的 execute,executeQuery 和 executeUpdate 执行提供模板方法 ExecutorSQLRecognizerSQLRecognizer 识别 sql 类型,获取表名,表别名以及原生 sqlUndoExecutorFactoryUndoExecutorFactory 根据 sqlType 生成对应的 AbstractUndoExecutor。
UndoExecutor 为生成执行 undoSql 的核心。如果全局事务回滚,它会根据 beforeImage 和 afterImage 以及 sql 类型生成对应的反向 sql 执行回滚数据,并添加脏数据校验机制,使回滚数据更加可靠。

### 3. Seata AT 模式源码分析 Seata 设计流程: https://www.processon.com/view/link/6311bfda1e0853187c0ecd8chttps://www.processon.com/view/link/6007f5c00791294a0e9b611a
