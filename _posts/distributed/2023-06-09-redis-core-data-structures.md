---


title: "Redis7核心数据结构"
description: "核心数据结构 Redis7 实战版-- 楼兰"
author: hsc
date: 2023-06-09 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Redis', 'Kafka', 'Netty', '分布式事务']
toc: true


---

核心数据结构 Redis7 实战版-- 楼兰

Redis7 有哪些数据结构扩展版核心版

永远的神: help

String 结构• 字符串常用操作 SET key value //存入字符串键值对 MSET key value [key value ...] //批量存储字符串键值对 SETNX key value //存入一个不存在的字符串键值对 GET key //获取一个字符串键值 MGET key [key ...] //批量获取字符串键值 DEL key [key ...] //删除一个键 EXPIRE key seconds //设置一个键的过期时间(秒)
• 原子加减 INCR key //将 key 中储存的数字值加 1DECR key //将 key 中储存的数字值减 1INCRBY key increment //将 key 所储存的值加上 incrementDECRBY key decrement //将 key 所储存的值减去 decrement

String 常见应用场景• 单值缓存 SET key value APPEND key value• 对象缓存
1) set user:1 '{"name":"roy","balance":1888}'
2) MSET user:1:name roy user:1:balance 1888MGET user:1:name user:1:balance• 分布式锁 SETNX product:10001 true //返回 1 代表获取锁成功 SETNX product:10001 true //返回 0 代表获取锁失败。。。执行业务操作 DEL product:10001 //执行完业务释放锁 SET product:10001 true ex 10 nx //防止程序意外终止导致死锁

Hash 结构• Hash 常用操作 HSET key field value //存储一个哈希表 key 的键值 HSETNX key field value //存储一个不存在的哈希表 key 的键值 HMSET key field value [field value ...] //在一个哈希表 key 中存储多个键值对 HGET key field //获取哈希表 key 对应的 field 键值 HMGET key field [field ...] //批量获取哈希表 key 中多个 field 键值 HDEL key field [field ...] //删除哈希表 key 中的 field 键值 HLEN key //返回哈希表 key 中 field 的数量 HGETALL key //返回哈希表 key 中所有的键值 HINCRBY key field increment //为哈希表 key 中 field 键的值加上增量 increment

Hash 应用场景• 对象缓存 HSET user:1 name roy balance 1888HMGET user:1 name balance 1888HSET user 1:name roy 1:balance 1888HMGET user 1:name 1:balance

Hash 应用场景• 电商购物车 1)以用户 id 为 key2)商品 id 为 field3)商品数量为 value• 购物车操作
1) 添加商品hset cart:1001 10088 1
2) 增加数量hincrby cart:1001 10088 1
3) 商品总数hlen cart:1001
4) 删除商品hdel cart:1001 10088
5) 获取购物车所有商品hgetall cart:1001

Hash 结构优缺点• 优点 1)同类数据归类整合储存,方便数据管理 2)相比 string 操作消耗内存与 cpu 更小 3)相比 string 储存更节省空间• 缺点
1) 过期功能不能使用在 field 上,只能用在 key 上
2) Redis 集群架构下不适合大规模使用

List 类型• List 常用操作 LPUSH key value [value ...] //将一个或多个值 value 插入到 key 列表的表头(最左边)
RPUSH key value [value ...] //将一个或多个值 value 插入到 key 列表的表尾(最右边)
LPOP key //移除并返回 key 列表的头元素 RPOP key //移除并返回 key 列表的尾元素 LRANGE key start stop //返回列表 key 中指定区间内的元素,区间以偏移量 start 和 stop 指定 BLPOP key [key ...] timeout //从 key 列表表头弹出一个元素,若列表中没有元素,阻塞等待 timeout 秒,如果 timeout=0,一直阻塞等待 BRPOP key [key ...] timeout //从 key 列表表尾弹出一个元素,若列表中没有元素,阻塞等待 timeout 秒,如果 timeout=0,一直阻塞等待

List 类型应用场景• 常用数据结构 Stack(栈) = LPUSH + LPOPQueue(队列)= LPUSH + RPOPBlocking MQ(阻塞队列)= LPUSH + BRPOP• 常见应用场景视频列表、签到列表排队机简化版的 MQ

List 类型注意点 1)一个 list 的容量是 2 的 32 次方减 1 个元素,大概 40 多亿。但是在应用时,要注意大 key 的问题。
2)list 的底层是一个双向链表,对双端的操作性能很高。但是通过索引下表直接操作某一个中间节点的性能就会比较低。

Set 类型• Set 常用操作 SADD key member [member ...] //往集合 key 中存入元素,元素存在则忽略,若 key 不存在则新建 SREM key member [member ...] //从集合 key 中删除元素 SMEMBERS key //获取集合 key 中所有元素 SCARD key //获取集合 key 的元素个数 SISMEMBER key member //判断 member 元素是否存在于集合 key 中 SRANDMEMBER key [count] //从集合 key 中选出 count 个元素,元素不从 key 中删除 SPOP key [count] //从集合 key 中选出 count 个元素,元素从 key 中删除 Set 运算操作 SINTER key [key ...] //交集运算 SINTERSTORE destination key [key ..] //将交集结果存入新集合 destination 中 SUNION key [key ..] //并集运算 SUNIONSTORE destination key [key ...] //将并集结果存入新集合 destination 中 SDIFF key [key ...] //差集运算 SDIFFSTORE destination key [key ...] //将差集结果存入新集合 destination 中

Set 应用场景• 微信抽奖小程序 1)点击参与抽奖加入集合 SADD key {userlD}2)查看参与抽奖所有用户 SMEMBERS key3)抽取 count 名中奖者 SRANDMEMBER key [count] / SPOP key [count]

Set 应用场景• 微信微博点赞,收藏,标签
1) 点赞 SADD like:{消息 ID} {用户 ID}
2) 取消点赞 SREM like:{消息 ID} {用户 ID}
3) 检查用户是否点过赞 SISMEMBER like:{消息 ID} {用户 ID}
4) 获取点赞的用户列表 SMEMBERS like:{消息 ID}
5) 获取点赞用户数 SCARD like:{消息 ID}

Set 应用场景• 集合操作 SINTER set1 set2 set3  { c } 共同关注的人 SUNION set1 set2 set3  { a,b,c,d,e } 朋友圈的人 SDIFF set1 set2 set3  { a } 推荐好友

ZSet 有序列表类型• ZSet 常用操作 ZADD key score member [[score member]...] //往有序集合 key 中加入带分值元素 ZREM key member [member ...] //从有序集合 key 中删除元素 ZSCORE key member //返回有序集合 key 中元素 member 的分值 ZINCRBY key increment member //为有序集合 key 中元素 member 的分值加上 incrementZCARD key //返回有序集合 key 中元素个数 ZRANGE key start stop [WITHSCORES] //正序获取有序集合 key 从 start 下标到 stop 下标的元素 ZREVRANGE key start stop [WITHSCORES] //倒序获取有序集合 key 从 start 下标到 stop 下标的元素• Zset 集合操作 ZUNIONSTORE destkey numkeys key [key ...] //并集计算 ZINTERSTORE destkey numkeys key [key ...] //交集计算

ZSet 应用场景• Zset 集合操作实现排行榜 1)点击新闻 ZINCRBY hotNews:20190819 1 守护香港 2)展示当日排行前十 ZREVRANGE hotNews:20190819 0 9 WITHSCORES3)七日搜索榜单计算 ZUNIONSTORE hotNews:20190813-20190819 7hotNews:20190813 hotNews:20190814... hotNews:201908194)展示七日排行前十 ZREVRANGE hotNews:20190813-20190819 0 9 WITHSCORES

Bitmap 类型• Bitmap 常用操作 SETBIT key offset value //将一个二进制数组的 offset 位置设置成 value。value 只能是 0 或者 1。
GETBIT key offset //返回一个二进制数组的 offset 位置的值。
BITCOUNT key [start end [BYTE|BIT]] //返回二进制数组中 1 的个数 BITPOS key bit [start [end [BYTE|BIT]]] //返回 bitmap 中第一个值为 bit 的 offset 位置。
BITOP AND|OR|XOR|NOT destkey key [key ...] //对两个 bitmap 做二进制的与或非计算。

Bitmap 应用场景• 每日签到 SETBIT dailycheck:1 100 1 1 号用户第 100 天完成了签到 BITCOUNT dailycheck:1 统计 1 号用户的签到次数 BITPOS dailycheck:1 统计 1 号用户第一天签到的时间• 优点快速、高效、节省空间

Hyperloglog 类型• 作用介绍:
用于统计一个集合中不重复的元素个数。
典型应用场景例如根据用户访问记录统计网站的 UV。
• Hyperloglog 常用操作 PFADD visitlog 192.168.65.111 192.168.65.112 192.168.65.111 //添加用户访问记录 PFCOUNT visitlog //统计不同的独立访客• Hyperloglog 其他操作 PFMERGE destkey [sourcekey [sourcekey ...]] //将多个 hyperloglong 数据整合成一条记录。

Geo 类型• 常用操作 GEOADD key [NX|XX] [CH] longitude latitude member [longitude latitude member ...] //添加一个或多个地点 GEOPOS key [member [member ...]] //返回地址的经纬度 GEODIST key member1 member2 [M|KM|FT|MI] //计算两个地点之间的距离 GEORADIUS key longitude latitude radius M|KM|FT|MI [WITHCOORD] [WITHDIST] [WITHHASH] [COUNT count[ANY]] [ASC|DESC] [STORE key|STOREDIST key] //查询某个经纬度地址附近的地点 GEOSEARCH key FROMMEMBER member|FROMLONLAT longitude latitude BYRADIUS radiusM|KM|FT|MI|BYBOX width height M|KM|FT|MI [ASC|DESC] [COUNT count [ANY]] [WITHCOORD][WITHDIST] [WITHHASH] //查询某个地点附近的地点

Geo 应用场景• 获取经纬度 https://api.map.baidu.com/lbsapi/getpoint/index.html• 添加商家地址 GEOADD changsha 113.017489 28.200454 火车站 112.96903 28.201195 橘子洲 113.017031 28.199706 赛格广场 113.017004 28.197677 国储• 查询距离 GEODIST changsha 火车站 橘子洲 M• 查找火车站附近的景点 GEORADIUSBYMEMBER changsha 火车站 2 KM withdistwithcoord count 4 withhash

stream 类型• 作用介绍:
Redis 版的 MQ -- 阻塞队列 + pub/sub 了解即可,企业应用比较少。
• 常用操作 XADD key [NOMKSTREAM] [MAXLEN|MINID [=|~] threshold [LIMIT count]] *|id field value [field value ...]//往对列的末尾发布一条消息 XDEL key id [id ...] // 删除队列中的一条消息 XLEN key //获取队列的长度 XRANGE key start end [COUNT count] //查询队列中的消息

stream 应用示例• 创建队列,并添加消息 *表示让系统自动生成 IDXADD mystream * name loulan name roy name admin• 查看对列消息 - 对列开始 + 对列结尾 XRANGE mystream - +• 创建消费者组 0 从队列头部开始消费。 $ 从队列尾部开始消费 XGROUP CREATE mystream groupA 0• 消费消息 > 表示从第一条未被消费过的消息消费。也可以指定 IDXREADGROUP GROUP groupA consumer1 count 2 STREAMS mystream >• 查看消费者组的消费进度 XPENDING mystream groupA

补充:SpringBoot 集成 RedisMaven 依赖:
<dependency><groupId>org.springframework.boot</groupId><spanrtifactId>spring-boot-starter-data-redis</artifactId></dependency>核心配置:
spring:
data:
redis:
host: 192.168.65.214port: 6379password: 123qweasd......

补充:RestTemplate 快速上手记住一个对象:
@Resourceprivate RedisTemplate<String,Object> redisTemplate;
按组操作 redisTemplate.opsForValue().xxx //string 类型 redisTemplate.opsForSet().xxx //set 类型 redisTemplate.opsForHash().xxx //hash 类型 redisTemplate.opsForList().xxx //list 类型 redisTemplate.opsForZset().xxx //Zset 类型 redisTemplate.opsForGeo().xxx //Geo 类型 redisTemplate.opsForHyperLogLog().xxx //hyperLogLog 类型 redisTemplate.opsForStream().xxx //stream 类型 redisTemplate.opsForValue().setBit() //bit 类型 为什么 bit 没有一个单独的操作类型?

补充:RedisTemplate 中文乱码问题@Beanpublic RedisTemplate<String,Object> redisTemplate(RedisConnectionFactory redisConnectionFactory){RedisTemplate<String, Object> redisTemplate = new RedisTemplate<>();
redisTemplate.setConnectionFactory(redisConnectionFactory);
// GenericJackson2JsonRedisSerializer jsonSerializer = new GenericJackson2JsonRedisSerializer();
StringRedisSerializer stringRedisSerializer = new StringRedisSerializer();
GenericToStringSerializer<String> genericToStringSerializer = newGenericToStringSerializer<>(String.class);
//指定 key 和 value 的序列化方式 redisTemplate.setKeySerializer(stringRedisSerializer);
redisTemplate.setValueSerializer(genericToStringSerializer);
redisTemplate.setHashKeySerializer(stringRedisSerializer);
redisTemplate.setHashValueSerializer(stringRedisSerializer);
redisTemplate.afterPropertiesSet();
return redisTemplate;
}

理解 》 熟练 》 记忆楼兰
