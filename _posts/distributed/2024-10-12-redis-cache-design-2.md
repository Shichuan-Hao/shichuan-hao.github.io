---


title: "Redis缓存设计与性能优化(1)"
description: "多级缓存架构缓存设计缓存穿透缓存穿透是指查询一个根本不存在的数据, 缓存层和存储层都不会命中, 通常出于容错的考虑, 如果从存储层查不到数据则不写入缓存层。"
author: hsc
date: 2024-10-12 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Redis', '分布式事务']
toc: true


---

多级缓存架构缓存设计缓存穿透缓存穿透是指查询一个根本不存在的数据, 缓存层和存储层都不会命中, 通常出于容错的考虑, 如果从存储层查不到数据则不写入缓存层。
缓存穿透将导致不存在的数据每次请求都要到存储层去查询, 失去了缓存保护后端存储的意义。
造成缓存穿透的基本原因有两个:
第一, 自身业务代码或者数据出现问题。
第二, 一些恶意攻击、 爬虫等造成大量空命中。
缓存穿透问题解决方案:
1、缓存空对象 1 String get(String key) {2 // 从缓存中获取数据 3 String cacheValue = cache.get(key);
4 // 缓存为空 5 if (StringUtils.isBlank(cacheValue)) {6 // 从存储中获取 7 String storageValue = storage.get(key);
8 cache.set(key, storageValue);
9 // 如果存储数据为空, 需要设置一个过期时间(300 秒)

10 if (storageValue == null) {11 cache.expire(key, 60 * 5);
12 }13 return storageValue;
14 } else {15 // 缓存非空 16 return cacheValue;
17 }18 }2、布隆过滤器对于恶意攻击,向服务器请求大量不存在的数据造成的缓存穿透,还可以用布隆过滤器先做一次过滤,对于不存在的数据布隆过滤器一般都能够过滤掉,不让请求再往后端发送。当布隆过滤器说某个值存在时,这个值可能不存在;当它说不存在时,那就肯定不存在。
布隆过滤器就是一个大型的位数组和几个不一样的无偏 hash 函数。所谓无偏就是能够把元素的 hash 值算得比较均匀。
向布隆过滤器中添加 key 时,会使用多个 hash 函数对 key 进行 hash 算得一个整数索引值然后对位数组长度进行取模运算得到一个位置,每个 hash 函数都会算得一个不同的位置。再把位数组的这几个位置都置为 1 就完成了 add 操作。
向布隆过滤器询问 key 是否存在时,跟 add 一样,也会把 hash 的几个位置都算出来,看看位数组中这几个位置是否都为 1,只要有一个位为 0,那么说明布隆过滤器中这个 key 不存在。如果都是 1,这并不能说明这个 key 就一定存在,只是极有可能存在,因为这些位被置为 1 可能是因为其它的 key 存在所致。如果这个位数组比较稀疏,这个概率就会很大,如果这个位数组比较拥挤,这个概率就会降低。
这种方法适用于数据命中不高、 数据相对固定、 实时性低(通常是数据集较大) 的应用场景, 代码维护较为复杂, 但是缓存空间占用很少。
可以用 redisson 实现布隆过滤器,引入依赖:
1 <dependency>2 <groupId>org.redisson</groupId>3 <spanrtifactId>redisson</artifactId>4 <version>3.6.5</version>5 </dependency>示例伪代码:
1 package com.redisson;
23 import org.redisson.Redisson;

4 import org.redisson.api.RBloomFilter;
5 import org.redisson.api.RedissonClient;
6 import org.redisson.config.Config;
78 public class RedissonBloomFilter {910 public static void main(String[] args) {11 Config config = new Config();
12 config.useSingleServer().setAddress("redis://localhost:6379");
13 //构造 Redisson14 RedissonClient redisson = Redisson.create(config);
1516 RBloomFilter<String> bloomFilter = redisson.getBloomFilter("nameList");
17 //初始化布隆过滤器:预计元素为 100000000L,误差率为 3%,根据这两个参数会计算出底层的 bit 数组大小 18 bloomFilter.tryInit(100000000L,0.03);
19 //将 zhuge 插入到布隆过滤器中 20 bloomFilter.add("zhuge");
2122 //判断下面号码是否在布隆过滤器中 23 System.out.println(bloomFilter.contains("guojia"));//false24 System.out.println(bloomFilter.contains("baiqi"));//false25 System.out.println(bloomFilter.contains("zhuge"));//true26 }27 }使用布隆过滤器需要把所有数据提前放入布隆过滤器,并且在增加数据时也要往布隆过滤器里放,布隆过滤器缓存过滤伪代码:
1 //初始化布隆过滤器 2 RBloomFilter<String> bloomFilter = redisson.getBloomFilter("nameList");
3 //初始化布隆过滤器:预计元素为 100000000L,误差率为 3%4 bloomFilter.tryInit(100000000L,0.03);
56 //把所有数据存入布隆过滤器 7 void init(){8 for (String key: keys) {9 bloomFilter.put(key);
10 }11 }1213 String get(String key) {14 // 从布隆过滤器这一级缓存判断下 key 是否存在 15 Boolean exist = bloomFilter.contains(key);
16 if(!exist){17 return "";
18 }19 // 从缓存中获取数据 20 String cacheValue = cache.get(key);
21 // 缓存为空

22 if (StringUtils.isBlank(cacheValue)) {23 // 从存储中获取 24 String storageValue = storage.get(key);
25 cache.set(key, storageValue);
26 // 如果存储数据为空, 需要设置一个过期时间(300 秒)
27 if (storageValue == null) {28 cache.expire(key, 60 * 5);
29 }30 return storageValue;
31 } else {32 // 缓存非空 33 return cacheValue;
34 }35 }注意:布隆过滤器不能删除数据,如果要删除得重新初始化数据。
缓存失效(击穿)
由于大批量缓存在同一时间失效可能导致大量请求同时穿透缓存直达数据库,可能会造成数据库瞬间压力过大甚至挂掉,对于这种情况我们在批量增加缓存时最好将这一批数据的缓存过期时间设置为一个时间段内的不同时间。
示例伪代码:
1 String get(String key) {2 // 从缓存中获取数据 3 String cacheValue = cache.get(key);
4 // 缓存为空 5 if (StringUtils.isBlank(cacheValue)) {6 // 从存储中获取 7 String storageValue = storage.get(key);
8 cache.set(key, storageValue);
9 //设置一个过期时间(300 到 600 之间的一个随机数)
10 int expireTime = new Random().nextInt(300) + 300;
11 if (storageValue == null) {12 cache.expire(key, expireTime);
13 }14 return storageValue;
15 } else {16 // 缓存非空 17 return cacheValue;
18 }19 }缓存雪崩缓存雪崩指的是缓存层支撑不住或宕掉后, 流量会像奔逃的野牛一样, 打向后端存储层。
由于缓存层承载着大量请求, 有效地保护了存储层, 但是如果缓存层由于某些原因不能提供服务(比如超大并发过来,缓存层支撑不住,或者由于缓存设计不好,类似大量请求访问 bigkey,导致缓存能支撑的并发急剧下降), 于是大量请求都会打到存储层, 存储层的调用量会暴增, 造成存储层也会级联宕机的情况。

预防和解决缓存雪崩问题, 可以从以下三个方面进行着手。
1) 保证缓存层服务高可用性,比如使用 Redis Sentinel 或 Redis Cluster。
2) 依赖隔离组件为后端限流熔断并降级。比如使用 Sentinel 或 Hystrix 限流降级组件。
比如服务降级,我们可以针对不同的数据采取不同的处理方式。当业务应用访问的是非核心数据(例如电商商品属性,用户信息等)时,暂时停止从缓存中查询这些数据,而是直接返回预定义的默认降级信息、空值或是错误提示信息;当业务应用访问的是核心数据(例如电商商品库存)时,仍然允许查询缓存,如果缓存缺失,也可以继续通过数据库读取。
3) 提前演练。 在项目上线前, 演练缓存层宕掉后, 应用以及后端的负载情况以及可能出现的问题, 在此基础上做一些预案设定。
热点缓存 key 重建优化开发人员使用“缓存+过期时间”的策略既可以加速数据读写, 又保证数据的定期更新, 这种模式基本能够满足绝大部分需求。 但是有两个问题如果同时出现, 可能就会对应用造成致命的危害:
当前 key 是一个热点 key(例如一个热门的娱乐新闻),并发量非常大。
重建缓存不能在短时间完成, 可能是一个复杂计算, 例如复杂的 SQL、 多次 IO、 多个依赖等。
在缓存失效的瞬间, 有大量线程来重建缓存, 造成后端负载加大, 甚至可能会让应用崩溃。
要解决这个问题主要就是要避免大量线程同时重建缓存。
我们可以利用互斥锁来解决,此方法只允许一个线程重建缓存, 其他线程等待重建缓存的线程执行完, 重新从缓存获取数据即可。
示例伪代码:
1 String get(String key) {2 // 从 Redis 中获取数据 3 String value = redis.get(key);
4 // 如果 value 为空, 则开始重构缓存 5 if (value == null) {6 // 只允许一个线程重建缓存, 使用 nx, 并设置过期时间 ex7 String mutexKey = "mutext:key:" + key;
8 if (redis.set(mutexKey, "1", "ex 180", "nx")) {9 // 从数据源获取数据 10 value = db.get(key);
11 // 回写 Redis, 并设置过期时间 12 redis.setex(key, timeout, value);
13 // 删除 key_mutex14 redis.delete(mutexKey);
15 }// 其他线程休息 50 毫秒后重试 16 else {17 Thread.sleep(50);
18 get(key);
19 }20 }21 return value;
22 }缓存与数据库双写不一致在大并发下,同时操作数据库与缓存会存在数据不一致性问题

1、双写不一致情况 2、读写并发不一致解决方案:
1、对于并发几率很小的数据(如个人维度的订单数据、用户数据等),这种几乎不用考虑这个问题,很少会发生缓存不一致,可以给缓存数据加上过期时间,每隔一段时间触发读的主动更新即可。
2、就算并发很高,如果业务上能容忍短时间的缓存数据不一致(如商品名称,商品分类菜单等),缓存加上过期时间依然可以解决大部分业务对于缓存的要求。
3、如果不能容忍缓存数据不一致,可以通过加分布式读写锁保证并发读写或写写的时候按顺序排好队,读读的时候相当于无锁。
4、也可以用阿里开源的 canal 通过监听数据库的 binlog 日志及时的去修改缓存,但是引入了新的中间件,增加了系统的复杂度。

总结:
以上我们针对的都是读多写少的情况加入缓存提高性能,如果写多读多的情况又不能容忍缓存数据不一致,那就没必要加缓存了,可以直接操作数据库。当然,如果数据库抗不住压力,还可以把缓存作为数据读写的主存储,异步将数据同步到数据库,数据库只是作为数据的备份。
放入缓存的数据应该是对实时性、一致性要求不是很高的数据。切记不要为了用缓存,同时又要保证绝对的一致性做大量的过度设计和控制,增加系统复杂性!
开发规范与性能优化一、键值设计
1. key 名设计(1)【建议】: 可读性和可管理性以业务名(或数据库名)为前缀(防止 key 冲突),用冒号分隔,比如业务名:表名:id1 trade:order:1(2)【建议】:简洁性保证语义的前提下,控制 key 的长度,当 key 较多时,内存占用也不容忽视,例如:
1 user:{uid}:friends:messages:{mid} 简化为 u:{uid}:fr:m:{mid}(3)【强制】:不要包含特殊字符反例:包含空格、换行、单双引号以及其他转义字符
2. value 设计(1)【强制】:拒绝 bigkey(防止网卡流量、慢查询)
在 Redis 中,一个字符串最大 512MB,一个二级数据结构(例如 hash、list、set、zset)可以存储大约 40 亿个(2^32-1)个元素,但实际中如果下面两种情况,我就会认为它是 bigkey。
1. 字符串类型:它的 big 体现在单个 value 值很大,一般认为超过 10KB 就是 bigkey。
2. 非字符串类型:哈希、列表、集合、有序集合,它们的 big 体现在元素个数太多。
一般来说,string 类型控制在 10KB 以内,hash、list、set、zset 元素个数不要超过 5000。
反例:一个包含 200 万个元素的 list。

非字符串的 bigkey,不要使用 del 删除,使用 hscan、sscan、zscan 方式渐进式删除,同时要注意防止 bigkey 过期时间自动删除问题(例如一个 200 万的 zset 设置 1 小时过期,会触发 del 操作,造成阻塞)
bigkey 的危害:
1.导致 redis 阻塞 2.网络拥塞 bigkey 也就意味着每次获取要产生的网络流量较大,假设一个 bigkey 为 1MB,客户端每秒访问量为 1000,那么每秒产生 1000MB 的流量,对于普通的千兆网卡(按照字节算是 128MB/s)的服务器来说简直是灭顶之灾,而且一般服务器会采用单机多实例的方式来部署,也就是说一个 bigkey 可能会对其他实例也造成影响,其后果不堪设想。
3. 过期删除有个 bigkey,它安分守己(只执行简单的命令,例如 hget、lpop、zscore 等),但它设置了过期时间,当它过期后,会被删除,如果没有使用 Redis 4.0 的过期异步删除(lazyfree-lazy-
expire yes),就会存在阻塞 Redis 的可能性。
bigkey 的产生:
一般来说,bigkey 的产生都是由于程序设计不当,或者对于数据规模预料不清楚造成的,来看几个例子:
(1) 社交类:粉丝列表,如果某些明星或者大 v 不精心设计下,必是 bigkey。
(2) 统计类:例如按天存储某项功能或者网站的用户集合,除非没几个人用,否则必是 bigkey。
(3) 缓存类:将数据从数据库 load 出来序列化放到 Redis 里,这个方式非常常用,但有两个地方需要注意,第一,是不是有必要把所有字段都缓存;第二,有没有相关关联的数据,有的同学为了图方便把相关数据都存一个 key 下,产生 bigkey。
如何优化 bigkey
1. 拆 big list: list1、list2、...listNbig hash:可以讲数据分段存储,比如一个大的 key,假设存了 1 百万的用户数据,可以拆分成 200 个 key,每个 key 下面存放 5000 个用户数据
2. 如果 bigkey 不可避免,也要思考一下要不要每次把所有元素都取出来(例如有时候仅仅需要 hmget,而不是 hgetall),删除也是一样,尽量使用优雅的方式来处理。
(2)【推荐】:选择适合的数据类型。
例如:实体类型(要合理控制和使用数据结构,但也要注意节省内存和性能之间的平衡)
反例:
1 set user:1:name tom2 set user:1:age 193 set user:1:favor football

正例:
1 hmset user:1 name tom age 19 favor football3.【推荐】:控制 key 的生命周期,redis 不是垃圾桶。
建议使用 expire 设置过期时间(条件允许可以打散过期时间,防止集中过期)。
二、命令使用 1.【推荐】 O(N)命令关注 N 的数量例如 hgetall、lrange、smembers、zrange、sinter 等并非不能使用,但是需要明确 N 的值。有遍历的需求可以使用 hscan、sscan、zscan 代替。
2.【推荐】:禁用命令禁止线上使用 keys、flushall、flushdb 等,通过 redis 的 rename 机制禁掉命令,或者使用 scan 的方式渐进式处理。
3.【推荐】合理使用 selectredis 的多数据库较弱,使用数字进行区分,很多客户端支持较差,同时多业务用多数据库实际还是单线程处理,会有干扰。
4.【推荐】使用批量操作提高效率 1 原生命令:例如 mget、mset。
2 非原生命令:可以使用 pipeline 提高效率。
但要注意控制一次批量操作的元素个数(例如 500 以内,实际也和元素字节数有关)。
注意两者不同:
1 1. 原生命令是原子操作,pipeline 是非原子操作。
2 2. pipeline 可以打包不同的命令,原生命令做不到 3 3. pipeline 需要客户端和服务端同时支持。
5.【建议】Redis 事务功能较弱,不建议过多使用,可以用 lua 替代三、客户端使用 1.【推荐】避免多个应用使用一个 Redis 实例正例:不相干的业务拆分,公共数据做服务化。
2.【推荐】使用带有连接池的数据库,可以有效控制连接,同时提高效率,标准使用方式:
1 JedisPoolConfig jedisPoolConfig = new JedisPoolConfig();
2 jedisPoolConfig.setMaxTotal(5);
3 jedisPoolConfig.setMaxIdle(2);
4 jedisPoolConfig.setTestOnBorrow(true);
56 JedisPool jedisPool = new JedisPool(jedisPoolConfig, "192.168.0.60", 6379, 3000, null);
78 Jedis jedis = null;

9 try {10 jedis = jedisPool.getResource();
11 //具体的命令 12 jedis.executeCommand()
13 } catch (Exception e) {14 logger.error("op key {} error: " + e.getMessage(), key, e);
15 } finally {16 //注意这里不是关闭连接,在 JedisPool 模式下,Jedis 会被归还给资源池。
17 if (jedis != null)
18 jedis.close();
19 }连接池参数含义:
序号 参数名 含义 默认值 使用建议 1 maxTotal 资源池中最大连接数 8 设置建议见下面资源池允许最大空闲 2 maxIdle 8 设置建议见下面的连接数资源池确保最少空闲 3 minIdle 0 设置建议见下面的连接数当资源池用尽后,调用者是否要等待。只 blockWhenExhauste4 有当为 true 时,下面 true 建议使用默认值 d 的 maxWaitMillis 才会生效当资源池连接用尽 5 maxWaitMillis 后,调用者的最大等 -1:表示永不超时 不建议使用默认值待时间(单位为毫秒)
向资源池借用连接时业务量很大时候建议是否做连接有效性检 6 testOnBorrow false 设置为 false(多一次测(ping),无效连接 ping 的开销)。
会被移除向资源池归还连接时业务量很大时候建议是否做连接有效性检 7 testOnReturn false 设置为 false(多一次测(ping),无效连接 ping 的开销)。
会被移除是否开启 jmx 监控,可 建议开启,但应用本 8 jmxEnabled true 用于监控 身也要开启优化建议:
1)maxTotal:最大连接数,早期的版本叫 maxActive 实际上这个是一个很难回答的问题,考虑的因素比较多:
业务希望 Redis 并发量客户端执行命令时间 Redis 资源:例如 nodes(例如应用个数) * maxTotal 是不能超过 redis 的最大连接数 maxclients。
资源开销:例如虽然希望控制空闲连接(连接池此刻可马上使用的连接),但是不希望因为连接池的频繁释放创建连接造成不必靠开销。
以一个例子说明,假设:
一次命令时间(borrow|return resource + Jedis 执行命令(含网络) )的平均耗时约为 1ms,一个连接的 QPS 大约是 1000

业务期望的 QPS 是 50000 那么理论上需要的资源池大小是 50000 / 1000 = 50 个。但事实上这是个理论值,还要考虑到要比理论值预留一些资源,通常来讲 maxTotal 可以比理论值大一些。
但这个值不是越大越好,一方面连接太多占用客户端和服务端资源,另一方面对于 Redis 这种高 QPS 的服务器,一个大命令的阻塞即使设置再大资源池仍然会无济于事。
2)maxIdle 和 minIdlemaxIdle 实际上才是业务需要的最大连接数,maxTotal 是为了给出余量,所以 maxIdle 不要设置过小,否则会有 new Jedis(新连接)开销。
连接池的最佳性能是 maxTotal = maxIdle,这样就避免连接池伸缩带来的性能干扰。但是如果并发量不大或者 maxTotal 设置过高,会导致不必要的连接资源浪费。一般推荐 maxIdle 可以设置为按上面的业务期望 QPS 计算出来的理论连接数,maxTotal 可以再放大一倍。
minIdle(最小空闲连接数),与其说是最小空闲连接数,不如说是"至少需要保持的空闲连接数",在使用连接的过程中,如果连接数超过了 minIdle,那么继续建立连接,如果超过了 maxIdle,当超过的连接执行完业务后会慢慢被移出连接池释放掉。
如果系统启动完马上就会有很多的请求过来,那么可以给 redis 连接池做预热,比如快速的创建一些 redis 连接,执行简单命令,类似 ping(),快速的将连接池里的空闲连接提升到 minIdle 的数量。
连接池预热示例代码:
1 List<Jedis> minIdleJedisList = new ArrayList<Jedis>(jedisPoolConfig.getMinIdle());
23 for (int i = 0; i < jedisPoolConfig.getMinIdle(); i++) {4 Jedis jedis = null;
5 try {6 jedis = pool.getResource();
7 minIdleJedisList.add(jedis);
8 jedis.ping();
9 } catch (Exception e) {10 logger.error(e.getMessage(), e);
11 } finally {12 //注意,这里不能马上 close 将连接还回连接池,否则最后连接池里只会建立 1 个连接。。
13 //jedis.close();
14 }15 }16 //统一将预热的连接还回连接池 17 for (int i = 0; i < jedisPoolConfig.getMinIdle(); i++) {18 Jedis jedis = null;
19 try {20 jedis = minIdleJedisList.get(i);
21 //将连接归还回连接池 22 jedis.close();
23 } catch (Exception e) {24 logger.error(e.getMessage(), e);
25 } finally {

26 }27 }总之,要根据实际系统的 QPS 和调用 redis 客户端的规模整体评估每个节点所使用的连接池大小。
3.【建议】高并发下建议客户端添加熔断功能(例如 sentinel、hystrix)
4.【推荐】设置合理的密码,如有必要可以使用 SSL 加密访问 5.【建议】Redis 对于过期键有三种清除策略:
1. 被动删除:当读/写一个已经过期的 key 时,会触发惰性删除策略,直接删除掉这个过期 key
2. 主动删除:由于惰性删除策略无法保证冷数据被及时删掉,所以 Redis 会定期主动淘汰一批已过期的 key
3. 当前已用内存超过 maxmemory 限定时,触发主动清理策略主动清理策略在 Redis 4.0 之前一共实现了 6 种内存淘汰策略,在 4.0 之后,又增加了 2 种策略,总共 8 种:
a) 针对设置了过期时间的 key 做处理:
1. volatile-ttl:在筛选时,会针对设置了过期时间的键值对,根据过期时间的先后进行删除,越早过期的越先被删除。
2. volatile-random:就像它的名称一样,在设置了过期时间的键值对中,进行随机删除。
3. volatile-lru:会使用 LRU 算法筛选设置了过期时间的键值对删除。
4. volatile-lfu:会使用 LFU 算法筛选设置了过期时间的键值对删除。
b) 针对所有的 key 做处理:
5. allkeys-random:从所有键值对中随机选择并删除数据。
6. allkeys-lru:使用 LRU 算法在所有数据中进行筛选删除。
7. allkeys-lfu:使用 LFU 算法在所有数据中进行筛选删除。
c) 不处理:
8. noeviction:不会剔除任何数据,拒绝所有写入操作并返回客户端错误信息"(error)
OOM command not allowed when used memory",此时 Redis 只响应读操作。
LRU 算法(Least Recently Used,最近最少使用)
淘汰很久没被访问过的数据,以最近一次访问时间作为参考。
LFU 算法(Least Frequently Used,最不经常使用)
淘汰最近一段时间被访问次数最少的数据,以次数作为参考。

当存在热点数据时,LRU 的效率很好,但偶发性的、周期性的批量操作会导致 LRU 命中率急剧下降,缓存污染情况比较严重。这时使用 LFU 可能更好点。
根据自身业务类型,配置好 maxmemory-policy(默认是 noeviction),推荐使用 volatile-lru。如果不设置最大内存,当 Redis 内存超出物理内存限制时,内存的数据会开始和磁盘产生频繁的交换 (swap),会让 Redis 的性能急剧下降。
当 Redis 运行在主从模式时,只有主结点才会执行过期删除策略,然后把删除操作”del key”同步到从结点删除数据。
四、系统内核参数优化 vm.swapinessswap 对于操作系统来说比较重要,当物理内存不足时,可以将一部分内存页进行 swap 到硬盘上,以解燃眉之急。但世界上没有免费午餐,swap 空间由硬盘提供,对于需要高并发、高吞吐的应用来说,磁盘 IO 通常会成为系统瓶颈。在 Linux 中,并不是要等到所有物理内存都使用完才会使用到 swap,系统参数 swppiness 会决定操作系统使用 swap 的倾向程度。 swappiness 的取值范围是 0~100,swappiness 的值越大,说明操作系统可能使用 swap 的概率越高,swappiness 值越低,表示操作系统更加倾向于使用物理内存。 swappiness 的取值越大,说明操作系统可能使用 swap 的概率越高,越低则越倾向于使用物理内存。
如果 linux 内核版本<3.5,那么 swapiness 设置为 0,这样系统宁愿 swap 也不会 oom killer(杀掉进程)
如果 linux 内核版本>=3.5,那么 swapiness 设置为 1,这样系统宁愿 swap 也不会 oom killer 一般需要保证 redis 不会被 kill 掉:
1 cat /proc/version #查看 linux 内核版本 2 echo 1 > /proc/sys/vm/swappiness3 echo vm.swapiness=1 >> /etc/sysctl.confPS:OOM killer 机制是指 Linux 操作系统发现可用内存不足时,强制杀死一些用户进程(非内核进程),来保证系统有足够的可用内存进行分配。
vm.overcommit_memory(默认 0)
0:表示内核将检查是否有足够的可用物理内存(实际不一定用满)供应用进程使用;如果有足够的可用物理内存,内存申请允许;否则,内存申请失败,并把错误返回给应用进程 1:表示内核允许分配所有的物理内存,而不管当前的内存状态如何如果是 0 的话,可能导致类似 fork 等操作执行失败,申请不到足够的内存空间 Redis 建议把这个值设置为 1,就是为了让 fork 操作能够在低内存下也执行成功。
1 cat /proc/sys/vm/overcommit_memory2 echo "vm.overcommit_memory=1" >> /etc/sysctl.conf3 sysctl vm.overcommit_memory=1

合理设置文件句柄数操作系统进程试图打开一个文件(或者叫句柄),但是现在进程打开的句柄数已经达到了上限,继续打开会报错:“Too many open files”1 ulimit ‐a #查看系统文件句柄数,看 open files 那项 2 ulimit ‐n 65535 #设置系统文件句柄数慢查询日志:slowlog1 Redis 慢日志命令说明:
