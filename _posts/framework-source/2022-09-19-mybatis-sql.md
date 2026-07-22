---


title: "MyBatis-执行Sql的流程分析"
description: "id=aa06a61ba9eaa8a01e54e28ca18245cc&sub=71B0996CEF2342B59AD757ADCFCCA1EEMyBat..."
author: hsc
date: 2022-09-19 00:00:00 +0800
categories: ['Java 后端', '框架源码']
tags: ['Spring', 'MyBatis', 'AOP', 'Spring事务']
toc: true


---

id=aa06a61ba9eaa8a01e54e28ca18245cc&sub=71B0996CEF2342B59AD757ADCFCCA1EEMyBatis 执行 Sql 的流程分析 openSession 的过程:
id=4975cd9e83f1e73e14a369598a232abe&sub=5D52C27921074712B1AB91C9A72455C0 本章着重介绍 MyBatis 执行 Sql 的流程,关于在执行过程中缓存、动态 SQl 生成等细节不在本章中体现还是以之前的查询作为列子:
12 /***3 * @Author 徐庶 QQ:10920027294 * @Slogan 致敬大师,致敬未来的你 5 */6 public class App {7 public static void main(String[] args) {8 String resource = "mybatis‐config.xml";
9 Reader reader;
10 try {11//将 XML 配置文件构建为 Configuration 配置类 12 reader = Resources.getResourceAsReader(resource);

13 // 通过加载配置文件流构建一个 SqlSessionFactory DefaultSqlSessionFactory14 SqlSessionFactory sqlMapper = new SqlSessionFactoryBuilder().build(reader);
15 // 数据源 执行器 DefaultSqlSession16 SqlSession session = sqlMapper.openSession();
17 try {18 // 执行查询 底层执行 jdbc19 //User user = (User)session.selectOne("com.tuling.mapper.selectById", 1);
2021 UserMapper mapper = session.getMapper(UserMapper.class);
22 System.out.println(mapper.getClass());
23 User user = mapper.selectById(1L);
24 System.out.println(user.getUserName());
25 } catch (Exception e) {26 e.printStackTrace();
27 }finally {28 session.close();
29 }30 } catch (IOException e) {31 e.printStackTrace();
32 }33 }34 }之前提到拿到 sqlSession 之后就能进行各种 CRUD 操作了,所以我们就从 sqlSession.getMapper 这个方法开始分析,看下整个 Sql 的执行流程是怎么样的。
openSession 的过程:
Copy1 private SqlSession openSessionFromDataSource(ExecutorType execType, TransactionIsolationLevel level, boolean autoCommit) {2 Transaction tx = null;
3 try {4 final Environment environment = configuration.getEnvironment();
5 final TransactionFactory transactionFactory = getTransactionFactoryFromEnvironment(environment);

6 tx = transactionFactory.newTransaction(environment.getDataSource(), level, autoCommit);
7//获取执行器,这边获得的执行器已经代理拦截器的功能(见下面代码)
8 final Executor executor = configuration.newExecutor(tx, execType);
9//根据获取的执行器创建 SqlSession10 return new DefaultSqlSession(configuration, executor, autoCommit);
11 } catch (Exception e) {12 closeTransaction(tx); // may have fetched a connection so lets callclose()
13 throw ExceptionFactory.wrapException("Error opening session. Cause:
" + e, e);
14 } finally {15 ErrorContext.instance().reset();
16 }17 }18 Copy19//interceptorChain 生成代理类,具体参见 Plugin 这个类的方法 20 public Executor newExecutor(Transaction transaction, ExecutorType executorType) {21 executorType = executorType == null ? defaultExecutorType : executorType;
22 executorType = executorType == null ? ExecutorType.SIMPLE : executorType;
23 Executor executor;
24 if (ExecutorType.BATCH == executorType) {25 executor = new BatchExecutor(this, transaction);
26 } else if (ExecutorType.REUSE == executorType) {27 executor = new ReuseExecutor(this, transaction);
28 } else {29 executor = new SimpleExecutor(this, transaction);
30 }31 if (cacheEnabled) {32 executor = new CachingExecutor(executor);
33 }34 executor = (Executor) interceptorChain.pluginAll(executor);
35 return executor;
36 }Executor 分成两大类,一类是 CacheExecutor,另一类是普通 Executor。

普通 Executor 又分为三种基本的 Executor 执行器,SimpleExecutor、ReuseExecutor、BatchExecutor。
SimpleExecutor:每执行一次 update 或 select,就开启一个 Statement 对象,用完立刻关闭 Statement 对象。
ReuseExecutor:执行 update 或 select,以 sql 作为 key 查找 Statement 对象,存在就使用,不存在就创建,用完后,不关闭 Statement 对象,而是放置于 Map<String, Statement>内,供下一次使用。简言之,就是重复使用 Statement 对象。
BatchExecutor:执行 update(没有 select,JDBC 批处理不支持 select),将所有 sql 都添加到批处理中(addBatch()),等待统一执行(executeBatch()),它缓存了多个 Statement 对象,每个 Statement 对象都是 addBatch()完毕后,等待逐一执行 executeBatch()批处理。与 JDBC 批处理相同。
作用范围:Executor 的这些特点,都严格限制在 SqlSession 生命周期范围内。
CacheExecutor 其实是封装了普通的 Executor,和普通的区别是在查询前先会查询缓存中是否存在结果,如果存在就使用缓存中的结果,如果不存在还是使用普通的 Executor 进行查询,再将查询出来的结果存入缓存。

到此为止,我们已经获得了 SqlSession,拿到 SqlSession 就可以执行各种 CRUD 方法了。
简单总结拿到 SqlSessionFactory 对象后,会调用 SqlSessionFactory 的 openSesison 方法,这个方法会创建一个 Sql 执行器(Executor),这个 Sql 执行器会代理你配置的拦截器方法。
获得上面的 Sql 执行器后,会创建一个 SqlSession(默认使用 DefaultSqlSession),这个 SqlSession 中也包含了 Configration 对象,所以通过 SqlSession 也能拿到全局配置;
获得 SqlSession 对象后就能执行各种 CRUD 方法了。
SQL 的具体执行流程见后续博客。
一些重要类总结:
SqlSessionFactorySqlSessionFactoryBuilderSqlSession(默认使用 DefaultSqlSession)
Executor 接口 Plugin、InterceptorChain 的 pluginAll 方法获取 Mapper 的流程进入 sqlSession.getMapper 方法,会发现调的是 Configration 对象的 getMapper 方法:
1 public <T> T getMapper(Class<T> type, SqlSession sqlSession) {2//mapperRegistry 实质上是一个 Map,里面注册了启动过程中解析的各种 Mapper.xml3//mapperRegistry 的 key 是接口的 Class 类型 4//mapperRegistry 的 Value 是 MapperProxyFactory,用于生成对应的 MapperProxy(动态代理类)
5 return mapperRegistry.getMapper(type, sqlSession);
6 }进入 getMapper 方法:
1 public <T> T getMapper(Class<T> type, SqlSession sqlSession) {2 final MapperProxyFactory<T> mapperProxyFactory =(MapperProxyFactory<T>) knownMappers.get(type);
3//如果配置文件中没有配置相关 Mapper,直接抛异常 4 if (mapperProxyFactory == null) {

5 throw new BindingException("Type " + type + " is not known to the MapperRegistry.");
6 }7 try {8//关键方法 9 return mapperProxyFactory.newInstance(sqlSession);
10 } catch (Exception e) {11 throw new BindingException("Error getting mapper instance. Cause: "
+ e, e);
12 }13 }进入 MapperProxyFactory 的 newInstance 方法:
12 public class MapperProxyFactory<T> {34 private final Class<T> mapperInterface;
5 private final Map<Method, MapperMethod> methodCache = new ConcurrentHashMap<Method, MapperMethod>();
67 public MapperProxyFactory(Class<T> mapperInterface) {8 this.mapperInterface = mapperInterface;
9 }1011 public Class<T> getMapperInterface() {12 return mapperInterface;
13 }1415 public Map<Method, MapperMethod> getMethodCache() {16 return methodCache;
17 }1819//生成 Mapper 接口的动态代理类 MapperProxy,MapperProxy 实现了 InvocationHandler 接口 20 @SuppressWarnings("unchecked")
21 protected T newInstance(MapperProxy<T> mapperProxy) {22 return (T) Proxy.newProxyInstance(mapperInterface.getClassLoader(),new Class[] { mapperInterface }, mapperProxy);
23 }25 public T newInstance(SqlSession sqlSession) {26 final MapperProxy<T> mapperProxy = new MapperProxy<T>(sqlSession, mapperInterface, methodCache);
27 return newInstance(mapperProxy);
28 }2930 }获取 Mapper 的流程总结如下:
Mapper 方法的执行流程下面是动态代理类 MapperProxy,调用 Mapper 接口的所有方法都会先调用到这个代理类的 invoke 方法(注意由于 Mybatis 中的 Mapper 接口没有实现类,所以 MapperProxy 这个代理对象中没有委托类,也就是说 MapperProxy 干了代理类和委托类的事情)。好了下面重点看下 invoke 方法。
12//MapperProxy 代理类 3 public class MapperProxy<T> implements InvocationHandler, Serializable{45 private static final long serialVersionUID = ‐6424540398559729838L;
6 private final SqlSession sqlSession;
7 private final Class<T> mapperInterface;
8 private final Map<Method, MapperMethod> methodCache;
910 public MapperProxy(SqlSession sqlSession, Class<T> mapperInterface,Map<Method, MapperMethod> methodCache) {11 this.sqlSession = sqlSession;
12 this.mapperInterface = mapperInterface;
13 this.methodCache = methodCache;

14 }1516 @Override17 public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {18 try {19 if (Object.class.equals(method.getDeclaringClass())) {20 return method.invoke(this, args);
21 } else if (isDefaultMethod(method)) {22 return invokeDefaultMethod(proxy, method, args);
23 }24 } catch (Throwable t) {25 throw ExceptionUtil.unwrapThrowable(t);
26 }27//获取 MapperMethod,并调用 MapperMethod28 final MapperMethod mapperMethod = cachedMapperMethod(method);
29 return mapperMethod.execute(sqlSession, args);
30 }MapperProxy 的 invoke 方法非常简单,主要干的工作就是创建 MapperMethod 对象或者是从缓存中获取 MapperMethod 对象。获取到这个对象后执行 execute 方法。
所以这边需要进入 MapperMethod 的 execute 方法:这个方法判断你当前执行的方式是增删改查哪一种,并通过 SqlSession 执行相应的操作。(这边以 sqlSession.selectOne 这种方式进行分析~)
1 public Object execute(SqlSession sqlSession, Object[] args) {2 Object result;
3//判断是 CRUD 那种方法 4 switch (command.getType()) {5 case INSERT: {6 Object param = method.convertArgsToSqlCommandParam(args);
7 result = rowCountResult(sqlSession.insert(command.getName(), param));
8 break;
9 }10 case UPDATE: {11 Object param = method.convertArgsToSqlCommandParam(args);

12 result = rowCountResult(sqlSession.update(command.getName(),param));
13 break;
14 }15 case DELETE: {16 Object param = method.convertArgsToSqlCommandParam(args);
17 result = rowCountResult(sqlSession.delete(command.getName(),param));
18 break;
19 }20 case SELECT:
21 if (method.returnsVoid() && method.hasResultHandler()) {22 executeWithResultHandler(sqlSession, args);
23 result = null;
24 } else if (method.returnsMany()) {25 result = executeForMany(sqlSession, args);
26 } else if (method.returnsMap()) {27 result = executeForMap(sqlSession, args);
28 } else if (method.returnsCursor()) {29 result = executeForCursor(sqlSession, args);
30 } else {31 Object param = method.convertArgsToSqlCommandParam(args);
32 result = sqlSession.selectOne(command.getName(), param);
33 }34 break;
35 case FLUSH:
36 result = sqlSession.flushStatements();
37 break;
38 default:
39 throw new BindingException("Unknown execution method for: " + command.getName());
40 }41 if (result == null && method.getReturnType().isPrimitive() && !method.returnsVoid()) {42 throw new BindingException("Mapper method '" + command.getName()
43 + " attempted to return null from a method with a primitive return type (" + method.getReturnType() + ").");
44 }45 return result;

46 }详细流程图 https://www.processon.com/view/link/5efc23966376891e81f2a37esqlSession.selectOne 方法会会调到 DefaultSqlSession 的 selectList 方法。这个方法获取了获取了 MappedStatement 对象,并最终调用了 Executor 的 query 方法。
1 public <E> List<E> selectList(String statement, Object parameter, RowBounds rowBounds) {2 try {3 MappedStatement ms = configuration.getMappedStatement(statement);
4 return executor.query(ms, wrapCollection(parameter), rowBounds, Executor.NO_RESULT_HANDLER);
5 } catch (Exception e) {6 throw ExceptionFactory.wrapException("Error querying database. Cause:
" + e, e);
7 } finally {8 ErrorContext.instance().reset();
9 }10 }然后,通过一层一层的调用(这边省略了缓存操作的环节,会在后面的文章中介绍),最终会来到 doQuery 方法, 这儿咱们就随便找个 Excutor 看看 doQuery 方法的实现吧,我这儿选择了 SimpleExecutor:
Copy1 public <E> List<E> doQuery(MappedStatement ms, Object parameter, RowBounds rowBounds, ResultHandler resultHandler, BoundSql boundSql) throwsSQLException {2 Statement stmt = null;
3 try {4 Configuration configuration = ms.getConfiguration();
5//内部封装了 ParameterHandler 和 ResultSetHandler6 StatementHandler handler = configuration.newStatementHandler(wrapper,ms, parameter, rowBounds, resultHandler, boundSql);
7 stmt = prepareStatement(handler, ms.getStatementLog());
8 //StatementHandler 封装了 Statement, 让 StatementHandler 去处理 9 return handler.<E>query(stmt, resultHandler);
10 } finally {11 closeStatement(stmt);

12 }13 }接下来,咱们看看 StatementHandler 的一个实现类 PreparedStatementHandler(这也是我们最常用的,封装的是 PreparedStatement), 看看它使怎么去处理的:
Copy1 public <E> List<E> query(Statement statement, ResultHandler resultHandler) throws SQLException {2 //到此,原形毕露, PreparedStatement, 这个大家都已经滚瓜烂熟了吧 3 PreparedStatement ps = (PreparedStatement) statement;
4 ps.execute();
5//结果交给了 ResultSetHandler 去处理,处理完之后返回给客户端 6 return resultSetHandler.<E> handleResultSets(ps);
7 }到此,整个调用流程结束。
简单总结这边结合获取 SqlSession 的流程,做下简单的总结:
SqlSessionFactoryBuilder 解析配置文件,包括属性配置、别名配置、拦截器配置、环境(数据源和事务管理器)、Mapper 配置等;解析完这些配置后会生成一个 Configration 对象,这个对象中包含了 MyBatis 需要的所有配置,然后会用这个 Configration 对象创建一个 SqlSessionFactory 对象,这个对象中包含了 Configration 对象;

拿到 SqlSessionFactory 对象后,会调用 SqlSessionFactory 的 openSesison 方法,这个方法会创建一个 Sql 执行器(Executor 组件中包含了 Transaction 对象),这个 Sql 执行器会代理你配置的拦截器方法。
获得上面的 Sql 执行器后,会创建一个 SqlSession(默认使用 DefaultSqlSession),这个 SqlSession 中也包含了 Configration 对象和上面创建的 Executor 对象,所以通过 SqlSession 也能拿到全局配置;
获得 SqlSession 对象后就能执行各种 CRUD 方法了。
以上是获得 SqlSession 的流程,下面总结下本博客中介绍的 Sql 的执行流程:
调用 SqlSession 的 getMapper 方法,获得 Mapper 接口的动态代理对象 MapperProxy,调用 Mapper 接口的所有方法都会调用到 MapperProxy 的 invoke 方法(动态代理机制);
MapperProxy 的 invoke 方法中唯一做的就是创建一个 MapperMethod 对象,然后调用这个对象的 execute 方法,sqlSession 会作为 execute 方法的入参;
往下,层层调下来会进入 Executor 组件(如果配置插件会对 Executor 进行动态代理)的 query 方法,这个方法中会创建一个 StatementHandler 对象,这个对象中同时会封装 ParameterHandler 和 ResultSetHandler 对象。调用 StatementHandler 预编译参数以及设置参数值,使用 ParameterHandler 来给 sql 设置参数。
Executor 组件有两个直接实现类,分别是 BaseExecutor 和 CachingExecutor。CachingExecutor 静态代理了 BaseExecutor。Executor 组件封装了 Transction 组件,Transction 组件中又分装了 Datasource 组件。
调用 StatementHandler 的增删改查方法获得结果,ResultSetHandler 对结果进行封装转换,请求结束。
Executor、StatementHandler 、ParameterHandler、ResultSetHandler,Mybatis 的插件会对上面的四个组件进行动态代理。
id=80acf548788cef82ffb924f043241365&sub=FAE1C62BE5C4422EBA80EF27A171C067

重要类 MapperRegistry:本质上是一个 Map,其中的 key 是 Mapper 接口的全限定名,value 的 MapperProxyFactory;
MapperProxyFactory:这个类是 MapperRegistry 中存的 value 值,在通过 sqlSession 获取 Mapper 时,其实先获取到的是这个工厂,然后通过这个工厂创建 Mapper 的动态代理类;
MapperProxy:实现了 InvocationHandler 接口,Mapper 的动态代理接口方法的调用都会到达这个类的 invoke 方法;
MapperMethod:判断你当前执行的方式是增删改查哪一种,并通过 SqlSession 执行相应的操作;
SqlSession:作为 MyBatis 工作的主要顶层 API,表示和数据库交互的会话,完成必要数据库增删改查功能;
Executor:MyBatis 执行器,是 MyBatis 调度的核心,负责 SQL 语句的生成和查询缓存的维护;
StatementHandler:封装了 JDBC Statement 操作,负责对 JDBC statement 的操作,如设置参数、将 Statement 结果集转换成 List 集合。
ParameterHandler:负责对用户传递的参数转换成 JDBC Statement 所需要的参数,ResultSetHandler:负责将 JDBC 返回的 ResultSet 结果集对象转换成 List 类型的集合;
TypeHandler:负责 java 数据类型和 jdbc 数据类型之间的映射和转换 MappedStatement:MappedStatement 维护了一条<select|update|delete|insert>节点的封装,SqlSource:负责根据用户传递的 parameterObject,动态地生成 SQL 语句,将信息封装到 BoundSql 对象中,并返回 BoundSql:表示动态生成的 SQL 语句以及相应的参数信息 Configuration:MyBatis 所有的配置信息都维持在 Configuration 对象之中。
调试主要关注点

MapperProxy.invoke 方法:MyBatis 的所有 Mapper 对象都是通过动态代理生成的,任何方法的调用都会调到 invoke 方法,这个方法的主要功能就是创建 MapperMethod 对象,并放进缓存。所以调试时我们可以在这个位置打个断点,看下是否成功拿到了 MapperMethod 对象,并执行了 execute 方法。
MapperMethod.execute 方法:这个方法会判断你当前执行的方式是增删改查哪一种,并通过 SqlSession 执行相应的操作。 Debug 时也建议在此打个断点看下。
DefaultSqlSession.selectList 方法:这个方法获取了获取了 MappedStatement 对象,并最终调用了 Executor 的 query 方法;
问题:
1.请介绍下 MyBatissql 语句的解析过程原理 2.请介绍下 MyBatis 缓存的原理 3.请介绍下 MyBatis 插件的原理
