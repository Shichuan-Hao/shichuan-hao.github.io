---



title: "Redis Stack扩展功能"
description: "RedisStack 有哪些扩展? 2、Redis JSON1、Redis JSON 是什么 2、Redis JSON 有什么用 3、Redis JSON 的优"
author: hsc
date: 2024-10-23 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Redis', 'ElasticSearch']
toc: true



---

### 一、了解 Redis 产品二、申请 RedisCloud 实例三、 Redis Stack 体验
1、RedisStack 有哪些扩展?
2、Redis JSON1、Redis JSON 是什么 2、Redis JSON 有什么用 3、Redis JSON 的优势 3、Search And Query1、传统 Scan 搜索 2、Search And Query 搜索 4、Bloom Filter1、布隆过滤器是什么 2、Guava 的布隆过滤器示例 3、Redis 的 BloomFilter 使用示例 5、Cuckoo Filter1、CuckooFilter 是什么?
2、CuckooFilter 使用示例四、 Redis Stack 补充 1、手动安装 Redis 扩展模块 2、Java 客户端调用扩展模块一、了解 Redis 产品目前,在 Redis 的官网上,可以看到 Redis 已经包含了多个产品。
其中,Redis Cloud 是 Redis 的云服务,Redis Insight 是 Redis 官方推出的图形化客户端。解决了 Redis 客户端群⻰无首的囧境。
而 Redis 本身,也已经划分成了几个版本。 Redis OSS 就是我们之前用的 Redis。 Redis Stack 可以理解为是 Redis 加上一系列的扩展产品。 Redis Enterprise 是 Redis 的企业版。
这次我们就一起来体验一下 Redis Stack 的扩展功能。

### 二、申请 RedisCloud 实例 Redis Stack 可以在我们之前安装的 Redis 服务上,自行下载安装新的扩展模块。在目前阶段,在 RedisCloud 上可以申请一个免费的 RedisStack 实例,快速体验 Redis Stack 的功能。
从 Redis 官网的右上⻆,就有 Redis Cloud 的登录链接。目前 Redis Cloud 提供了多种第三方登录的方式,可以选择合适的方式注册账号。
注册登录后,Redis Cloud 就会分配一个免费的 Redis 实例。提供了 Redis Stack 功能支持。

接下来使用命令行,就可以连上这个 Redis 实例。
这个实例空间非常有限,而且无法⻓期使用。如果有更多需求,可以去了解一下付费版本。基础付费 5 美元/月三、 Redis Stack 体验 1、RedisStack 有哪些扩展?
目前 Redis 的官网上,单独构建了 Redis 的指令⻚面。在这个⻚面可以直接搜索相关的功能。
另外, 在 redis-cli 客户端也可以使用 module list 指令查看当前 Redis 服务中有哪些扩展。
Redis Stack 的这些扩展功能,也可以手动添加到自己的 Redis 服务中。但是通常并不是必须的。我们可以使用 Redis Cloud 上的实例先完整体验一下,再考虑要不要使用这些扩展。
接下来找几个比较常⻅的扩展模块,体验一下。

2、Redis JSON1、Redis JSON 是什么 RedisJSON 是 Redis 的一个扩展模块,它提供了对 JSON 数据的原生支持。通过 RedisJSON,我们可以将 JSON 数据直接存储在 Redis 中,并利用丰富的命令集进行高效的查询和操作。 RedisJSON 不仅简化了数据处理的流程,还大幅提升了处理 JSON 数据的性能。
2、Redis JSON 有什么用 Redis JSON 的常用指令,在官网的 Commands⻚面搜索 JSON 组就能看到在 Redis 服务端,这些扩展指令并没有严格分组,而是都放在一个叫做 module 的组 redis-17998.c295.ap-southeast-1-1.ec2.redns.redis-cloud.com:17998> help JSON.SETJSON.SET (null)
summary: (null)
group: moduleRedis JSON 模块为 Redis 添加了 JSON 数据类型的支持,并且对 JSON 数据提供了快速进行增、删、改、查的操作。
-- 设置一个 JSON 数据 JSON.SET user $ '{"name":"loulan","age":18}'
## key 是 user,value 就是一个 JSON 数据。其中$表示 JSON 数据的根节点。
-- 查询 JSON 数据 JSON.GET user-- 查询 JSON 对象的 name 属性 JSON.GET user $.name-- 查看数据类型 JSON.TYPE user -- objectJSON.TYPE user $.name --- stringJSON.TYPE user $.age --- integer--修改 JSON 数据 年龄加 2JSON.NUMINCRBY user $.age 2-- 添加新的字段 JSON.SET user $.address '{"city": "Changsha", "country": "China"}' NX
## NX 表示只有当 address 字段不存在的时候才进行设置。
-- 在 JSON 数组中添加元素 JSON.SET user $.hobbies '["reading"]'JSON.ARRAPPEND user $.hobbies '"swimming"'-- 查看 JSON 对象中 key 的个数 JSON.OBJLEN user $.address-- 查看 user 对象的所有 keyJSON.OBJKEYS user-- 删除 JSON 中的 keyJSON.DEL user $.address

3、Redis JSON 的优势 JSON 是现代应用程序中经常用到的一种数据类型。很多时候,就算没有 Redis JSON 插件,我们也会采用 JSON 格式来缓存复杂的数据类型。比如在分布式场景下做用户登录功能,我们就可以将用户信息以 JSON 字符串的形式保存到 Redis 中,来代替单体应用中的 Session,从而实现统一的登录状态管理。这些数据使用 RedisJSON 插件来管理,就显得顺理成章了。
并且 Redis JSON 插件相比用 string 管理这种 JSON 数据,还能带来一些很明显的优势。
Redis JSON 存储数据的性能更高。 Redis JSON 底层其实是以一种高效的二进制的格式存储。相比简单的文本格式,二进制格式进行 JOSN 格式读写的性能更高,也更节省内存。根据官网的性能测试报告,使用 Redis JSON 读写 JSON 数据,性能已经能够媲美 MongoDB 以及 ElasticSearch 等传统 NoSQL 数据库。
Redis JSON 使用树状结构来存储 JSON。这种存储方式可以快速访问子元素。与传统的文本存储方案相比,树状存储结构能够更高效的执行查询操作。
与 Redis 生态集成度高。作为 Redis 的扩展模块,Redis JSON 和 Redis 的其他功能和工具无缝集成。这意味着开发者可以继续使用 TTL、Redis 事务、发布/订阅、 Lua 脚本等功能。
3、Search And Query 当 Redis 中存储的数据比较多时,搜索 Redis 中的数据是一件比较麻烦的事情。通常使用的 keys * 这样的指令,在生产环境一般都是直接禁用的,因为这样会产生严重的线程阻塞,影响其他的读写操作。
如何快速搜索 Redis 中的数据(主要是 key)呢? Redis 中原生提供了 Scan 指令,另外在 Redis Stack 中也增加了 Search And Query 模块。
1、传统 Scan 搜索 Scan 指令的官方介绍:https://redis.io/docs/latest/commands/scan/Scan 指令的基础思想就是每次只返回想要查询的一部分结果数据,然后通过迭代的方式,逐步返回完整数据。
scan 指令的基础使用方式:
SCAN cursor [MATCH pattern] [COUNT count] [TYPE type]这几个核心参数介绍如下:
cursor: 游标。代表每次迭代返回的偏移量。通常一次查询,cursor 从 0 开始,然后 scan 指令会返回下一次迭代的起始偏移量。用户可以用这个返回值作为 cursor,继续迭代下一批。直到 cursor 返回 0,表示所有数据都过滤完成了。
pattern:匹配字符串。用来匹配要查询的 key。 例如 user* 表示以 user 开头的字符串。
count:数字,表示每次迭代多少条数据。
type 是 key 的类型,比如可以指定 string ,set,zset 等。
另外,针对不同 key 类型,还有一些不同的指令。 比如 SSCAN 针对 Set 类型。 HSCAN 针对 HASH 类型。
ZSCAN 针对 ZSet 类型。
简单示例如下:

-- 准备数据 eval 'for i = 1,30,1 do redis.call("SET","k"..tostring(i),"v"..tostring(i)) end' 0--简单按照 cursor 过滤所有 key。
scan 0
1) 18 ## 下一次迭代的 cursor....scan 18
1) 21....scan 21
1) 0 ## 返回 0 表述所有数据过滤完成....-- 按照 patern 过滤 查询所有 k 开头的 keyscan 0 MATCH k*
1) 18...scan 18 MATCH k*
1) 21...scan 21 MATCH k*
1) 0-- 设置迭代次数 scan 0 MATCH k* count 20
1) 21...scan 21 MATCH k* count 20
1) 02、Search And Query 搜索传统的 SCAN 搜索方式,只能简单的过滤 Key。如果想要做一些复杂的搜索,就力不从心了。
比如在电商场景中,我们通常会用 Redis 来缓存商品信息,但是如果要做按品牌、型号、价格等等各种条件过滤商品的场景,Redis 就不够用了。以往我们会选择将商品数据导入到 MongoDB 或者 ElasticSearch 这样的搜索引擎进行复杂过滤。
而 Redis 提供了 RedisSearch 插件,基本就可以认为是 ElasticSearch 这类搜索引擎的平替。大部分 ES 能够实现的搜索功能,在 Redis 里就能直接进行。这样就极大的减少了数据迁移带来的麻烦。

既然要做搜索,那就需要有能够支持搜索的数据结构。 Redis 的哪些数据结构能够支持结构化查询呢?只有 HASH 和 JSON。
--清空数据 flushall-- 创建一个产品的索引 FT.CREATE productIndex ON JSON SCHEMA $.name AS name TEXT $.price AS price NUMERIC
## 索引为 productIndex.
## ON JSON 表示 这个索引会基于 JSON 数据构建,需要 RedisJSON 模块的支持。默认是 ON HASH 表示检索所有 HASH 格
式的数据
## SCHEMA 表示根据哪些字段建立索引。 字段名 AS 索引字段名 数据类型 这样的组合。如果是 JSON 格式,字段名用$.
路径表示-- 模拟一批产品信息 JSON.SET phone:1 $ '{"id":1,"name":"HUAWEI 1","description":"HUAWEI PHONE1","price":1999}'JSON.SET phone:2 $ '{"id":2,"name":"HUAWEI 2","description":"HUAWEI PHONE2","price":2999}'JSON.SET phone:3 $ '{"id":3,"name":"HUAWEI 3","description":"HUAWEI PHONE3","price":3999}'JSON.SET phone:4 $ '{"id":4,"name":"HUAWEI 4","description":"HUAWEI PHONE4","price":4999}'JSON.SET phone:5 $ '{"id":5,"name":"HUAWEI 5","description":"HUAWEI PHONE5","price":5999}'JSON.SET phone:6 $ '{"id":6,"name":"HUAWEI 6","description":"HUAWEI PHONE6","price":6999}'JSON.SET phone:7 $ '{"id":7,"name":"HUAWEI 7","description":"HUAWEI PHONE7","price":7999}'JSON.SET phone:8 $ '{"id":8,"name":"HUAWEI 8","description":"HUAWEI PHONE8","price":8999}'JSON.SET phone:9 $ '{"id":9,"name":"HUAWEI 9","description":"HUAWEI PHONE9","price":9999}'JSON.SET phone:10 $ '{"id":10,"name":"HUAWEI 10","description":"HUAWEI PHONE10","price":19999}'
## 如果是 ON HASH ,可以直接通过索引添加数据
## FT.ADD productIndex 'product:1' 1.0 FIELDS "id" 1 "name" "HUAWEI1" "description"
"HUAWEI PHONE 1" "PRICE" 3999
## 数据的 key 是 producr:1
## FIELDS 数据。 按照 key value 的格式组织
-- 查看索引状态 FT.INFO productIndex-- 搜索产品
## 搜索条件: name 包含 HUAWEI, price 在 1000 到 5000 之间。返回 id 和 name
FT.SEARCH productIndex "@name:HUAWEI @price:[1000 5000]" RETURN 2 id name
## 查询条件构建,参⻅官网 https://redis.io/docs/latest/develop/interact/search-and-
query/query/4、Bloom Filter1、布隆过滤器是什么

一句话解释:一种快速检索一个元素是否在一个海量集合中的算法。
比如现在有一个签到活动,要求每个用户只能签到一次,重复签到无效。这种常⻅的需求怎么做?如果不考虑数量级,那么非常简单。把所有签到的用户 ID 存到一个集合里。签到前到集合里检查一下用户 ID 有没有就可以了。
但是,如果你要面对的是淘宝的海量用户信息呢?这个集合得要多大?在一个海量集合里检索一个数据,是不是很慢?这就需要一个更节省空间同时更高效的算法,能够在海量数据集合中快速判断一个元素存不存在。这就可以用布隆过滤器。
布隆过滤器的使用场景非常多,最典型的应用是作为缓存数据的前端过滤缓存。快速比如,在淘宝这种海量用户的登录场景,也可以用布隆过滤器,快速判断用户输入的用户名是不是存在。如果用户名不存在,那么就可以直接拒绝,不再需要去数据库里查了。这样就可以防止大部分无效数据查询,屏蔽很多恶意的请求。
布隆过滤器使用一个很⻓的二进制位数组和一系列哈希函数来保存元素。优点是非常节省空间,并且查询时间也非常快。缺点是有一定的误失败概率以及无法删除元素 ,也无法给元素计数。
位数组(Bit Array):布隆过滤器使用一个⻓度固定的位数组来存储数据。每个位置只占用一个比特(0 或 1),初始时所有位都设置为 0。位数组的⻓度和哈希函数的数量决定了过滤器的误报率和容量。
哈希函数集合:布隆过滤器使用多个哈希函数,每个函数都会将输入数据映射到位数组的一个不同位置。
哈希函数的选择对过滤器的性能有很大影响,理想的哈希函数应该具有良好的散列性,使得不同的输入尽可能均匀地映射到位数组的不同位置。
布隆过滤器判断一个元素不在集合中,那么这个元素肯定不在集合中。但是,布隆过滤器判断一个元素在集合中,那么这个元素有可能不在集合中。
2、Guava 的布隆过滤器示例布隆过滤器中,将一个原本不在集合中的元素判断成为在集合中,这就是误判。而误判率是布隆过滤器一个很重要的控制指标。
在算法实现时,误判率是可以通过设定更复杂的哈希函数组合以及做更大的位数组来进行控制的。所以,在布隆过滤器的初始化过程中,通常只需要指定过滤器的容量和误判率,就足够了。
pom.xml 引入 Guava

<dependency><groupId>com.google.guava</groupId><spanrtifactId>guava</artifactId><version>33.1.0-jre</version></dependency>使用 Guava 提供的布隆过滤器实现 public static void main(String[] args) {BloomFilter<String> bloomFilter =BloomFilter.create(Funnels.stringFunnel(StandardCharsets.UTF_8),10000,0.01);
//把 A~Z 放入布隆过滤器 for (int i = 64; i <= 90 ; i++) {bloomFilter.put(String.valueOf((char) i));
}System.out.println(bloomFilter.mightContain("A")); //trueSystem.out.println(bloomFilter.mightContain("a")); //false}3、Redis 的 BloomFilter 使用示例布隆过滤器是用的二进制数组来保存数据,所以,Redis 的 BitMap 数据结构天生就非常适合做一个分布式的布隆过滤器底层存储。只是算法还是需要自己实现。有很多企业实际上也是这么做的。
现在 Redis 提供了 BloomFilter 模块后,BloomFilter 的使用⻔槛就更低了。
-- 创建一个 key 为 bf 的布隆过滤器,容错率 0.01,容量 1000。NONSCALING 表示不扩容。如果这个过滤器里的数据满了,就直接报错 BF.RESERVE bf 0.01 1000 NONSCALING-- 添加元素 BF.ADD bf A.....-- 批量添加元素 BF.MADD bf B C D E F G H I-- 如果 bf 不存在,就创建一个 key 为 bf 的过滤器。
BF.INSERT bf CAPACITY 1000 ERROR 0.01 ITEMS hello-- 查看容量 BF.CARD bf-- 判断元素是否在过滤器中
## 返回值 0 表示不在,1 表示在
BF.EXISTS bf a-- 批量判断 BF.MEXISTS bf A a B b-- 查看布隆过滤器状态 BF.INFO bf
# 依次迭代布隆过滤器中的位数组
BF.SCANDUMP bf 0
## 和 SCAN 指令使用很像,返回当前访问到的数据和下一次迭代的起点。 当下次迭代起点为 0 表示数据已经全部迭代完
成。
## 主要是可以配合 BF.LOADCHUNK 进行备份。

5、Cuckoo Filter1、CuckooFilter 是什么?
布隆过滤器最大的问题是无法删除数据。因此,后续诞生了很多布隆过滤器的改进版本。 Cuckoo Filter 布谷⻦过滤器就是其中一种。
相比于布隆过滤器,Cuckoo Filter 可以删除数据。而且基于相同的集合和误报率,Cuckoo Filter 通常占用空间更少。相对的,算法实现也就更复杂。
不过他同样有误判率。即有可能将一个不在集合中的元素错误的判断成在集合中。布隆过滤器的误报率通过调整位数组的大小和哈希函数来控制,而 CuckooFilter 的误报率受指纹大小和桶大小控制。
BUSKETSIZE,表示每个桶 Busket 中存放的元素个数。 Cuckoo Filter 的数组里存的不是位,而是桶 busket,每个桶里可以存放多个数据。同一个桶中存放的数据越多,空间利用率更高,相应的误判率也就越高,性能也更慢。 Redis 的 CuckooFilter 实现中,BUSKETSIZE 应该是一个在 1 到 255 之间的整数,默认的 BUSKETSIZE 是 2。
桶 Busket 中并不实际保存数据本身,而是保存数据的指纹(可以认为是压缩后的数据,实际上是数据对象的几个低位数据)。指纹越小,HASH 冲突造成误判的几率就越小。这个参数的调整比较复杂,Redis 的 CuckooFilter 中不支持调整这个参数。
2、CuckooFilter 使用示例-- 创建默认值
## 容量 1000,这个是必填参数。后面几个都是可选参数。这里填的几个就是 Redis 中的 CuckooFilter 的默认值
## BUSKETSIZE 越大,空间利用率更高,但是误判率也更高,性能更差
## MAXITARATIONS 越小,性能越好。如果设置越大,空间利用率就越好。
## EXPANSION 是指空间扩容的比例。
CF.RESERVE cf 1000 BUSKETSIZE 2 MAXITERATIONS 20 EXPANSION 1 其他使用,和布隆过滤器差不多。就是多了个 CF.DEL 删除元素的指令。
四、 Redis Stack 补充 1、手动安装 Redis 扩展模块 Redis Stack 的这些扩展模块除了在 Redis Cloud 上直接使用外,也可以手动集成到自己的 Redis 服务当中。
登录 Redis Cloud,进入下载中心,可以手动下载对应的扩展模块。下载时注意选择对应的 Redis 版本以及操作系统。

这是一个最简单的下载途径。另外更建议的方式,是去下载这些扩展模块的源码,然后编译,安装。
下载后获取以.so 为后缀的扩展文件。上传到服务器后,在 Redis 的配置文件中加载这个扩展模块
# Load modules at startup. If the server is not able to load modules
# it will abort. It is possible to use multiple loadmodule directives.
#
loadmodule /root/myredis/redisbloom.so 然后重启 Redis 服务,就可以使用客户端,登录 Redis 后查看扩展模块的加载情况。
127.0.0.1:6379> MODULE LIST1.
1. "name"
2. "bf"
3. "ver"
4. (integer) 20612
5. "path"
6. "/root/myredis/redisbloom.so"
7. "args"
8. (empty array)

注意:如果模块加载错误,那么 Redis 服务启动会失败的。这时要去查看日志逐步排查问题。
例如,如果 redisbloom.so 文件在 Linux 服务器上,没有添加可执行的 x 权限,那么 Redis 就会启动失败 27425:M 18 Jun 2024 14:07:29.670 # Module /root/myredis/redisbloom.so failed to load:
It does not have execute permissions.27425:M 18 Jun 2024 14:07:29.670 # Can't load module from/root/myredis/redisbloom.so: server aborting2、Java 客户端调用扩展模块这些扩展模块目前阶段都还是比较新的功能,需要手动进行扩展。所以目前 Java 的一些客户端工具都还没有集成这些功能。大部分情况下,只能通过 lua 脚本手动调用这些扩展功能。但是由于在客户端无法确定服务端是否安装了对应的扩展模块,所以,在写 lua 脚本调用时,一定要注意处理好各种各样的异常情况。
例如,以布隆过滤器为例

@SpringBootTest@RunWith(SpringRunner.class)
public class RedisStackTest {@ResourceRedisTemplate<String,Object> redisTemplate;
List<String> keys = List.of("a-bf");
@Testpublic void createBloomFilter(){if(!redisTemplate.hasKey("a-bf")){try{String createFilterScriptText= """
return redis.call('BF.RESERVE', KEYS[1], '0.01','1000','NONSCALING')
""";
DefaultRedisScript<String> redisScript = new DefaultRedisScript<>(createFilterScriptText, String.class);
String execute = redisTemplate.execute(redisScript,keys);
System.out.println("CREATE BF:"+execute);
}catch (Exception e){// e.printStackTrace();
System.out.println("COMMAND NOT SUPPORT");
}}else{System.out.println("BF KEY is already exists");
}}@Testpublic void addData(){if(!redisTemplate.hasKey("a-bf")){System.out.println("BF KEY is not exists");
}else{try{String[] args = new String[]{"A","B","C","D","E","F","G"};
String addDataScriptText= """
for i,arg in ipairs(ARGV) dolocal addRes = redis.call('BF.ADD',KEYS[1],arg)
endreturn 'OK'""";
DefaultRedisScript<String> redisScript = new DefaultRedisScript<>(addDataScriptText, String.class);
System.out.println("ADDDATA BF:"+redisTemplate.execute(redisScript, keys,args));
}catch (Exception e){// e.printStackTrace();
System.out.println("COMMAND NOT SUPPORTED");
}}}@Testpublic void checkData(){if(!redisTemplate.hasKey("a-bf")){System.out.println("BF KEY is not exists");
}else{String[] args = new String[]{"A","B","C","D","E","F","G"};
String checkDataScriptText= """

local checkRes = redis.call('BF.EXISTS',KEYS[1],ARGV[1])
return checkRes""";
DefaultRedisScript<Long> redisScript = new DefaultRedisScript<>(checkDataScriptText, Long.class);
try{Long res = redisTemplate.execute(redisScript, keys, args);
if(1L == res){System.out.println("KEY EXISTS");
} else if (0L==res) {System.out.println("KEY NOT EXISTS");
}else{System.out.println("ERROR");
}}catch (Exception e){// e.printStackTrace();
System.out.println("COMMAND NOT SUPPORTED");

