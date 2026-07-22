---



title: "Redis7底层数据结构解析"
description: "Redis 数据在底层是什么样的? 2、Redis 常⻅数据类型的底层数据结构总结二、 String 数据结构详解 1、string 数据是如何存储的?"
author: hsc
date: 2024-11-03 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Redis', '分布式事务']
toc: true



---

### 一、整体理解 Redis 底层数据结构
1、Redis 数据在底层是什么样的?
2、Redis 常⻅数据类型的底层数据结构总结二、 String 数据结构详解 1、string 数据是如何存储的?
2、string 类型对应的 int,embstr,raw 有什么区别?
3、string 底层数据结构总结三、 HASH 类型数据结构详解 1、hash 数据是如何存储的 2、hash 底层数据结构详解 3、hash 底层数据结构总结四、 List 类型数据结构详解 1、list 数据是如何存储的 2、list 底层数据结构详解 3、quicklist 简介 4、list 底层数据结构总结五、 SET 类型数据结构详解 1、set 数据是如何存储的 2、set 底层数据结构详解六、 ZSET 类型数据结构详解 1、zset 数据是如何存储的 2、zset 底层数据结构详解 3、zset 底层数据结构总结七、 Redis 课程总结这一章节我们将深入理解 Redis 底层数据结构,也就是尝试真正去了解我们指定的 set k1 v1 这样的指令,是怎么执行的,数据是怎么保存的。
开始之前,做两个简单声明:
第一:作为 Java 程序员,我们研究 Redis 底层结构的目的,只有一个:面试!也就是体现你对 Redis 的理解深度,而并不是要你去写一个 Redis。因此,我们接下来主要分析常用的几种数据类型的底层结构,中间必然会涉及到一些 Redis 底层的 C 源码。对于这些源码,我只抽取其中部分精华,用做知识点的佐证。如果之间有逻辑断层,或者你想要了解一些其他的数据类型,可以自行看源码补充。
第二:Redis 的底层数据结构其实是经常变化的,不光 Redis6 到 Redis7 这样的大版本,就算同样大版本下的不同小版本,底层结构也是经常有变化的。对于讲到的每种数据结构,我会尽量在 Redis 源码中进行验证。如果没有说明,Redis 的版本是目前最新的 7.2.5。

### 一、整体理解 Redis 底层数据结构
1、Redis 数据在底层是什么样的?
在应用层面,我们熟悉 Redis 有多种不同的数据类型,比如 string,hash,list,set,zset 等。但是这些数据在 Redis 的底层是什么样子呢?实际上 Redis 提供了一个指令 OBJECT 可以用来查看数据的底层类型。
127.0.0.1:6379> OBJECT HELP
1) OBJECT <subcommand> [<spanrg> [value] [opt] ...]. Subcommands are:
2) ENCODING <key>
3) Return the kind of internal representation used in order to storethe value
4) associated with a <key>.
5) FREQ <key>
6) Return the access frequency index of the <key>. The returnedinteger is
7) proportional to the logarithm of the recent access frequency ofthe key.
8) IDLETIME <key>
9) Return the idle time of the <key>, that is the approximatednumber of
10) seconds elapsed since the last access to the key.
11) REFCOUNT <key>
12) Return the number of references of the value associated with thespecified
13) <key>.
14) HELP
15) Print this help.127.0.0.1:6379> set k1 v1OK127.0.0.1:6379> OBJECT ENCODING k1"embstr"
可以看到,k1 v1 这个<k,v>键值对,他在底层的数据类型就是 embstr 。Redis 在底层,其实是这样描述这些数据类型的。
< server.h 880 行>

/* Objects encoding. Some kind of objects like Strings and Hashes can be* internally represented in multiple ways. The 'encoding' field of theobject* is set to one of this fields for this object. */
#define OBJ_ENCODING_RAW 0 /* Raw representation */
#define OBJ_ENCODING_INT 1 /* Encoded as integer */
#define OBJ_ENCODING_HT 2 /* Encoded as hash table */
#define OBJ_ENCODING_ZIPMAP 3 /* No longer used: old hash encoding. */
#define OBJ_ENCODING_LINKEDLIST 4 /* No longer used: old list encoding.
*/
#define OBJ_ENCODING_ZIPLIST 5 /* No longer used: old list/hash/zset
encoding. */
#define OBJ_ENCODING_INTSET 6 /* Encoded as intset */
#define OBJ_ENCODING_SKIPLIST 7 /* Encoded as skiplist */
#define OBJ_ENCODING_EMBSTR 8 /* Embedded sds string encoding */
#define OBJ_ENCODING_QUICKLIST 9 /* Encoded as linked list of listpacks
*/
#define OBJ_ENCODING_STREAM 10 /* Encoded as a radix tree of listpacks */
#define OBJ_ENCODING_LISTPACK 11 /* Encoded as a listpack */
这里也能看到有些类型已经不再使用了。比如 ZIPLIST。如果你看过一些以前的 Redis 的文章,就会知道,ZIPLIST 是在 Redis6 中经常使用的一个重要的数据类型。但是现在已经不再使用了。在 Redis7 中,基本已经使用 listpack 替代了 ziplist。
然后,在上面的注释中还可以看到。这些编码方式都是使用在 Object 的 encoding 字段里的。这个 Object 是什么东东呢?
<server.h 900 行>struct redisObject {unsigned type:4;
unsigned encoding:4;
unsigned lru:LRU_BITS; /* LRU time (relative to global lru_clock) or* LFU data (least significant 8 bitsfrequency* and most significant 16 bits access time).*/int refcount;
void *ptr;
};
Redis 是一个<k,v>型的数据库,其中 key 通常都是 string 类型的字符串对象,而 value 在底层就统一是 redisObject 对象。

而这个 redisObject 结构,实际上就是 Redis 内部抽象出来的一个封装所有底层数据结构的统一对象。这就类似于 Java 的面向对象的设计方式。
这里面几个核心字段意义如下:
type:Redis 的上层数据类型。比如 string,hash,set 等,可以使用指令 type key 查看。
encoding: Redis 内部的数据类型。
lru:当内存超限时会采用 LRU 算法清除内存中的对象。关于 LRU 与 LFU,在 redis.conf 中有描述
# LRU means Least Recently Used
# LFU means Least Frequently Used
refcount:表示对象的引用次数。可以使用 OBJECT REFCOUNT key 指令查看。
*ptr:这是一个指针,指向真正底层的数据结构。 encoding 只是一个类型描述。实际数据是保存在 ptr 指向的具体结构里。
2、Redis 常⻅数据类型的底层数据结构总结我们已经知道了 Redis 有上层的应用类型,也有底层的数据结构。那么这些上层数据类型和底层数据结构是怎么对应的呢?
127.0.0.1:6379> set k1 v1OK127.0.0.1:6379> type k1string127.0.0.1:6379> object encoding k1"embstr"
这就是一种对应关系。也就是说,在应用层面,我们操作的是 string 这样的数据类型,但是 Redis 在底层,操作的是 embstr 这样一种数据结构。但是,这些上层的数据类型和底层的数据结构之间,是不是就是简单的一一对应的关系呢?

127.0.0.1:6379> set k2 1OK127.0.0.1:6379> type k2string127.0.0.1:6379> object encoding k2"int"
127.0.0.1:6379> set k3aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaOK127.0.0.1:6379> type k3string0127.0.0.1:6379> OBJECT ENCODING k3"raw"
从这里能够看到,每一种上层数据类型对应底层多种不同的数据结构,也就是说,同样的一个数据类型,Redis 底层的处理方式是不同的。
Redis 提供了一个指令,可以直接调试某一个 key 的结构信息。但是这种方式默认是关闭的。
127.0.0.1:6379> DEBUG Object k1(error) ERR DEBUG command not allowed. If the enable-debug-commandoption is set to "local", you can run it from a local connection,otherwise you need to set this option in the configuration file, andthen restart the server.按照要求,修改配置文件,重启 Redis 服务后,就可以看到每一个 key 的内部结构 127.0.0.1:6379> DEBUG object k1Value at:0x7f0e36264c80 refcount:1 encoding:embstr serializedlength:3lru:7607589 lru_seconds_idle:23 现在搞明白 encoding 是什么了之后,问题就到了下一步,这个 ptr 指针到底指向了哪些数据结构呢?
下面直接列出了 Redis 中上层数据类型和底层真正存储数据的数据结构的对应关系。

Redisstring set zset list hash 版本 SDS(动 Redis intset+hashta skiplist+ quicklist hashtabl 态字符 6 ble ziplist +ziplist e+ziplist 串)
quicklistRedis intset+listpac skiplist+ hashtablSDS +listpac7 k+hashtable listpack e+listk 这个列表里的这些数据结构,如果不理解,先直接记住。 这是 Redis 一个比较高频的面试题(高级职位)。至于具体的细节,后面会慢慢分析。
另外,其他的数据类型,包括一些扩展模块的数据类型,面试中基本不太可能问得太深,自行理解。
Redis6 和 Redis7 最大的区别就在于 Redis7 已经用 listpack 替代了 ziplist。只不过为了保证兼容性,Redis7 中并没有移除 ziplist 的代码以及配置。 listpack 与 ziplist 的区别也是一个高频的面试题,后面会逐步介绍。
二、 String 数据结构详解从之前的简单实验中已经看到,string 数据,在底层对应了 int ,embstr,raw 三种不同的数据结构。他们到底是什么呢?下面分几个问题逐步深入。
1、string 数据是如何存储的?
先上结论,再验证。 string 数据的类型,会根据 value 的类型不同,有以下几种处理方式 int : 如果 value 可以转换成一个 long 类型的数字,那么就用 int 保存 value。只有整数才会使用 int,如果是浮点数,Redis 内部其实是先将浮点数转化成字符串,然后保存 embstr : 如果 value 是一个字符串类型,并且⻓度小于 44 字节的字符串,那么 Redis 就会用 embstr 保存。代表 embstr 的底层数据结构是 SDS(Simple Dynamic String 简单动态字符串)
raw :如果 value 是一个字符串类型,并且⻓度大于 44 字节,就会用 raw 保存。
源码验证:
在客户端执行一个 set k1 v1 这样的指令,会进入<t_string.c>的 setComand 方法处理。

<t_string.c 295 行>这个 tryObjectEncoding 的方法实现,在 object.c 中<object.c 614 行>的*tryObjectEncodingEx 方法。 关键部分如下:
1、从这里可以看到,对于数字⻓度超过 20 的大数字,Redis 是不会用 int 保存的。
2、OBJ_SHARED_INTEGER = 1000 。对于 1000 以内的数字,直接指向内存。
<object.c 685 行>

2、string 类型对应的 int,embstr,raw 有什么区别?
1、int 类型就是尽量在对应的 robj 中的 ptr 指向一个缓存数据对象。

2、embstr 类型如果字符串类型⻓度小于 44,就会创建一个 embstr 的对象。这个创建的方法是这样的:
<object.c 92 行>

embstr 字面意思就是内嵌字符串。 所谓内嵌的核心,其实就是将新创建的 SDS 对象直接分配在对象自己的内存后面。这样内存读取效率明显更高。
这里有一段介绍, SDS 其实是一段不可修改的字符串。这意味着如果使用 APPEND 之类的指令尝试修改一个 key 的值,那么就算 value 的⻓度没有超过 44,Redis 也会使用一个新创建的 raw 类型,而不再使用原来的 SDS。

这个 SDS 是什么呢?其实他就是 Redis 底层对于 String 的一种封装。
<sds.h 45 行>

Redis 根据字符串⻓度不同,封装了多种不同的 SDS 结构。通常,保存字符串,用一个 buf[]就够了。但是 Redis 在这个数组的基础上,封装成了 SDS 结构。通过添加的这些参数,可以更方便解析字符串。
例如,如果用数组方式保存字符串,那么读取完整字符串就只能遍历数组里的各个字节数据,时间复杂度 O(N)。但是 SDS 中预先记录了 len 后,就可以直接读取一定⻓度的字节,时间复杂度 O(1),效率更高。 另外,C 语言中通常用字节数组保存字符串,那么还需要定义一个特殊的结束符\0 表示这一个字符串结束。但是在 Redis 中,如果 value 中就包含\0 这样的字符串,就会产生歧义。但是有 SDS 后,直接读取完整字节,也就不用管这些歧义了。
3、raw 类型从之前分析可以看到,raw 类型其实相当于是兜底的一种类型。特殊的数字类型和小字符串类型处理完了后,就是 raw 类型了。 raw 类型的处理方式就是单独创建一个 SDS,然后将 robj 的 ptr 指向这个 SDS。

3、string 底层数据结构总结对于 string 类型的一系列操作,Redis 内部会根据用户给的不同键值使用不同的编码方式,自适应地选择最优化的内部编码方式。这些逻辑,对于用户是完全隔离的。
对于 string 类型的数据,如果 value 可以转换为数字,Redis 底层就会使用 int 类型。在 RedisObject 中的 ptr 指针中,会直接复制为整数数据,不再额外创建指针指向整数,节省了指针的空间开销。并且,如果数字比较小,小于 1000,将会直接使用预先创建的缓存对象,连创建对象的内存空间也节省了。
如果 value 是字符串且⻓度小于 44 字节,Redis 底层就会使用 embstr 类型。 embstr 类型会调用内存分配函数,分配一块连续的内存空间保存对应的 SDS。这样使用连续的内存空间,不光可以提高数据的读取速度,而且可以避免内存碎片。
如果 value 是字符串类型,但是大于 44 字节,那么 RedisObject 和 SDS 就会分开申请内存。
通过 RedisObject 的 ptr 指针指向新创建的 SDS。
三、 HASH 类型数据结构详解

1、hash 数据是如何存储的还是先上结论,再源码验证。 hash 类型的数据,底层存储时,有两种存储格式。 hashtable 和 listpack127.0.0.1:6379> hset user:1 id 1 name roy(integer) 2127.0.0.1:6379> type user:1hash127.0.0.1:6379> OBJECT ENCODING user:1"listpack"
127.0.0.1:6379> config set hash-max-listpack-entries 3OK127.0.0.1:6379> config set hash-max-listpack-value 8OK127.0.0.1:6379> hset user:1 name royaaaaaaaaaaaaaaaa(integer) 0127.0.0.1:6379> OBJECT ENCODING user:1"hashtable"
127.0.0.1:6379> hset user:2 id 1 name roy score 100 age 18(integer) 4127.0.0.1:6379> OBJECT ENCODING user:2"hashtable"
简单来说,就是 hash 型的数据,如果 value 里的数据比较少,就用 listpack。如果数据比较多,就用 hashtable。
如何判断 value 里的数据少,涉及到两个参数。 hash-max-listpack-entries 限制 value 里键值对的个数(默认 512),hash-max-listpack-value 限制 value 里值的数据大小(默认 64 字节)。
从这两个参数里可以看到,对于 hash 类型数据,大部分正常情况下,都是使用 listpack。所以,对于 hash 类型数据,主要是要理解 listpack 是如何存储的。至于 hashtable,正常基本用不上,面试也就很少会问。
但是 hash 类型的底层数据,只用 ziplist 和 listpack,其实是很像的。 Redis6 里也有 ziplist 相关的这两个参数。
2、hash 底层数据结构详解首先理解 hash 数据底层数据存储的基础结构

hash 数据的 value,是一系列的键值对。 这些<k,v>键值对底层封装成了一个 dictEntry 结构。然后,整个这些键值对,又会被封装成一个 dict 结构。这个 dict 结构就构成了 hash 的整个 value。
<dict.h 84 行>dictEntry 的结构体定义在 dict.c 中<dict.c 63 行>然后,来看 redis 底层是如何执行一个 hset key field1 value1 field2 value2 这样的指令的 Redis 底层处理 hset 指令的方法在 <t_hash.c 606 行>

接下来这个 hashTypeTryConversion 方法就会尝试进行编码转换。 这就验证了 hash 类型数据根据那两个参数选择用 listpack 还是 hashtable 的。
接下来,到底什么是 listpack?
listpack 是 ziplist 的升级版,所以,谈到 listpack 就不得不谈 ziplist。ziplist 字面意义是压缩列表。怎么压缩呢?

ziplist 最大的特点,就是他被设计成一种内存紧凑型的数据结构,占用一块连续的内存空间,不仅可以利用 CPU 缓存,而且会针对不同⻓度的数据,进行响应的编码。这种方法可以及有效的节省内存开销。
在 redis6 中,ziplist 是 Redis 底层非常重要的一种数据结构,不止支持 hash,还支持 list 等其他数据类型 ziplist 是由连续内存块组成的顺序性数据结构,整个结构有点类似于数组。可以在任意一端进行 push/pop 操作,时间复杂度都是 O(1)。整体结构如下:
这些 entry 就可以认为是保存 hash 类型的 value 当中的一个键值对。
然后,每一个 entry 结构又分为三个部分。
previous_entry_length:记录前一个节点的⻓度,占 1 个或者 5 个字节。如果前一个节点的⻓度小于 254 字节,则采用一个字节来保存⻓度值。如果前一个节点的⻓度大于等于 254 字节,则采用 5 个字节来保存这个⻓度值。第一个字节是 0xfe,后面四个字节才是真实⻓度数据为什么要这样?因为 255 已经用在了 ziplist 的最后一个 zlend。
encoding:编码属性,记录 content 的数据类型。表明 content 是字符串还是整数,以及 content 的⻓度。
contents:负责保存节点的数据,可以是字符串或整数。

ziplist 后面的 list 通常是指链表数据结构。而典型的双向链表是在每个节点上通过两个指针指向前和后的相邻节点。而 ziplist 这种数据结构,就不再保存指针,只保留⻓度。极致压缩内存空间。这也是关于 ziplist 紧凑的一种表现。
在这种结构下,对于一个 ziplist,要找到对列的第一个元素和最后一个元素,都是比较容易的,可以通过头部的三个字段直接找到。但是,如果想要找到中间某一些元素(比如 Redis 的 list 数据类型的 LRANGE 指令),那么就只能依次遍历(从前往后单向遍历)。所以,ziplist 不太适合存储太多的元素。
然后,为什么要用 listpack 替换 ziplist 呢?
redis 的作者 antirez 的 github 上提供了 listpack 的实现。里面有一个 md 文档介绍了 listpack。文章地址: https://github.com/antirez/listpack/blob/master/listpack.mdlistpack 的整体结构跟 ziplist 是差不多的,只是做了一些小调整。最核心的原因是要解决 ziplist 的连锁更新问题。
下面介绍连锁更新问题,这个了解即可。
连锁更新问题的核心就是在 enty 的 previous_entry_length 记录方式。如果前一个节点的⻓度小于 254 字节,那么 previous_entry_length 只有 1 个字节。如果大于等于 254 字节,则 previous_entry_length 需要扩展到 5 个字节。
这时假设我们有这样一个 ziplist,每个 entry 的⻓度都是在 250~253 字节之间,previous_entry_length 都只要一个字节。
这时,如果将一个⻓度大于等于 254 字节的新节点加入到压缩列表的表头节点,也就是 e1 的头部。

这时,因为 e1 的 previous_entry_length 只有 1 个字节,无法保存新节点的⻓度,此时就需要扩充 previous_entry_length 到 5 个字节。这样 e1 的整体⻓度就会超过 254 字节。而 e1 一旦⻓度扩展,意味着 e2 的 previous_entry_length 也需要从 1 扩展到 5 字节。接下来,后续每一个 entry 都需要重新调整空间。
这种特殊情况下产生的连续多次空间扩展操作,就称为连锁更新。连锁更新造成的空间连续变动,是非常不安全的,同时效率也是非常低的。正是因为连锁更新问题,才造成 Redis7 中使用新的 listpack 结构替代 ziplists。
listpack 的整体结构如下:
核心是 entry 中原本记录前一个 entry 的⻓度,现在改为记录自己的⻓度。这样,就不会再因为前一个 entry 变化而影响自己的⻓度。这样也就没有了连锁更新的问题。
listpack 在源码中的体现如下:
<listpack.h 49 行>3、hash 底层数据结构总结最后,对于 hash 类型的底层数据结构,做一个总结:
1、hash 底层更多的是使用 listpack 来存储 value。
2、如果 hash 对象保存的键值对超过 512 个,或者所有键值对的字符串⻓度超过 64 字节,底层的数据结构就会由 listpack 升级成为 hashtable。

3、对于同一个 hash 数据,listpack 结构可以升级为 hashtable 结构,但是 hashtable 结构不会降级成为 listpack。
四、 List 类型数据结构详解 1、list 数据是如何存储的老规矩,先上结论,再验证。 list 类型的数据,在 Redis 中还是以 listpack+quicklist 为基础保存的。
127.0.0.1:6379> lpush l1 a1(integer) 1127.0.0.1:6379> rpush l1 a2(integer) 2127.0.0.1:6379> type l1list127.0.0.1:6379> OBJECT ENCODING l1"listpack"
这里看到,list 类型的数据,通常是以 listpack 结构来保存的。但是,如果调整一下参数配置,就会有另外一种结果 127.0.0.1:6379> config set list-max-listpack-size 2OK127.0.0.1:6379> lpush l3 a1 a2 a3(integer) 3127.0.0.1:6379> OBJECT ENCODING l3"quicklist"
关于 list-max-listpack-size 参数,在 redis.conf 文件中有更详细的描述。

# Lists are also encoded in a special way to save a lot of space.
# The number of entries allowed per internal list node can be specified
# as a fixed maximum size or a maximum number of elements.
# For a fixed maximum size, use -5 through -1, meaning:
# -5: max size: 64 Kb <-- not recommended for normal workloads
# -4: max size: 32 Kb <-- not recommended
# -3: max size: 16 Kb <-- probably not recommended
# -2: max size: 8 Kb <-- good
# -1: max size: 4 Kb <-- good
# Positive numbers mean store up to _exactly_ that number of elements
# per list node.
# The highest performing option is usually -2 (8 Kb size) or -1 (4 Kb
size),
# but if your use case is unique, adjust the settings as necessary.
# -- 每个 list 中包含的节点大小或个数。正数表示个数,负数-1 到-5 表示大小。
list-max-listpack-size -2 所以,整体来说,对于 list 数据类型,Redis 是根据 value 中数据的大小判断底层数据结构的。数据比较“小”的 list 类型,底层用 listpack 保存。数据量比较"大"的 list 类型,底层用 quicklist 保存。
这个结论跟 redis 的版本有关系。
2、list 底层数据结构详解先来对 list 的底层数据做源码验证:
在处理 lpush,rpush 这些指令的时候,会进入下面的方法处理。
<t_list.c 484 行>

而这个 createListListpackObject 方法的声明,是在 object.c 文件中。这个方法就是创建一个 listpack 结构,来保存 list 中的元素。
<object.c 242 行>关键是接下来的 listTypeTryConversionAppend 方法,这个方法会尝试对 listpack 进行转换。
<t_list.c 132 行>

然后,在这个 listTypeTryConvertListpack 方法中,终于看到了这个神奇的 quicklist。
<t_list.c 32 行>

在这个方法中,涉及到服务端的另一个配置参数 list-compress-depth 表示 list 的数据压缩级别。可以去配置文件中了解一下。
# Lists may also be compressed.
# Compress depth is the number of quicklist ziplist nodes from *each*
side of
# the list to *exclude* from compression. The head and tail of the
list
# are always uncompressed for fast push/pop operations. Settings
are:
# 0: disable all list compression
# 1: depth 1 means "don't start compressing until after 1 node into
the list,
# going from either the head or tail"
# So: [head]->node->node->...->node->[tail]
# [head], [tail] will always be uncompressed; inner nodes will
compress.
# 2: [head]->[next]->node->node->...->node->[prev]->[tail]
# 2 here means: don't compress head or head->next or tail->prev or
tail,
# but compress all nodes between them.
# 3: [head]->[next]->[next]->node->node->...->node->[prev]->[prev]->
[tail]
# etc.
list-compress-depth 03、quicklist 简介要理解 quicklist 是什么,首先要尝试去理解 Redis 为什么有了 listpack 后,还需要设计一个 quicklist。也就是 listpack 结构有什么不足的地方。
之前已经给大家介绍过 listpack 的数据结构。整体来看,listpack 可以看成是一个数组(Array)结构。而对于数据结构,他的好处是存储数据是连续的,所以,对数组中的数据进行检索是比较快的,通过偏移量就可以快速定位。 listpack 的这种结构非常适合支持 Redis 的 list 数据类型的 LRANGE 这样的检索操作。
但是,对于数组来说,他的数据节点修改就会比较麻烦。 每次新增或者删除一个节点,都需要调整大量节点的位置。这又使得 listpack 的数据结构对于 Redis 的 list 数据类型的 LPUSH 这样增加节点的操作非常不友好。尤其当 list 中的数据节点越多,LPUSH 这样的操作要移动的内存也就会越多。

与数组形成对比的是链表(List)结构。链表的节点之间只通过指针指向相关联的节点,这些节点并不需要占用连续的内存。链表的方式,好处就是对链表的增删节点会非常方便,只需要调整指针就可以了。所以链表能够非常好的支持 list 数据类型的 LPUSH,LPOP 这样的操作。
但是,链表结构也有明显的不足,那就是对数据的检索比较麻烦,只能沿着指针引用关系依次遍历节点。所以纯粹的链表结构也不太适合 Redis 的 list 数据类型。
那么有没有一种数据结构,能够尽量综合数据 Array 和链表 List 的优点呢?这就是 Redis 设计出来的 quicklist 结构。
quicklist 大体上可以认为是一个链表结构。里面的每个节点是一个 quicklistNode。

<quick.h 98 行>每个 quicklistNode 会保存前后节点的指针,这就是一个典型的链表结构。
<quick.h 36 行>在 quicklistNode 中,*entry 实际上就是指向具体保存数据的 listpack 结构。

这样就形成了 quicklist 的整体结构。这个 quicklist 结构,就相当于是数组 Array 和链表 List 的结合体。这就能尽可能的结合这两种数据结构的优点。
quicklist 的整体结构其实在 Redis 很早的版本中就已经成型了。区别在于 quicklistNode 中间保存的数据结构。 在 Redis6 以前是 ziplist,到 Redis7 中改为了 listpack。
4、list 底层数据结构总结如果 list 的底层数据量比较小时,Redis 底层用 listpack 结构保存。当 list 的底层数据量比较大时,Redis 底层用 quicklist 结构保存。
至于这其中数据量大小的判断标准,由参数 list-max-listpack-size 决定。这个参数设置成正数,就是按照 list 结构的数据节点个数判断。负数从-1 到-5,就是按照数据节点的大小判断。
五、 SET 类型数据结构详解 1、set 数据是如何存储的老规矩,先下结论,再源码验证。

Redis 底层综合使用 intset+listpack+hashtable 存储 set 数据。 set 数据的子元素也是<k,v>形式的 entry。其中,key 就是元素的值,value 是 null。
127.0.0.1:6379> sadd s1 1 2 3 4 5(integer) 5127.0.0.1:6379> OBJECT ENCODING s1"intset"
127.0.0.1:6379> sadd s2 a b c d e(integer) 5127.0.0.1:6379> OBJECT ENCODING s2"listpack"
127.0.0.1:6379> config set set-max-listpack-entries 2OK127.0.0.1:6379> sadd s3 a b c d e(integer) 5127.0.0.1:6379> OBJECT ENCODING s3"hashtable"
区分底层结构的相关参数有以下几个:
# Sets have a special encoding when a set is composed
# of just strings that happen to be integers in radix 10 in the range
# of 64 bit signed integers.
# The following configuration setting sets the limit in the size of the
# set in order to use this special memory saving encoding.
# -- 如果 set 的数据都是不超过 64 位的数字(一个 long 数字).就使用 intset 存储
set-max-intset-entries 512
# Sets containing non-integer values are also encoded using a memory
efficient
# data structure when they have a small number of entries, and the
biggest entry
# does not exceed a given threshold. These thresholds can be configured
using
# the following directives.
# -- 如果 set 的数据不是数字,并且数据的大小没有超过下面设定的阈值,就用 listpack 存储
# -- 如果数据大小超过了其中一个阈值,就改为使用 hashtable 存储。
set-max-listpack-entries 128set-max-listpack-value 642、set 底层数据结构详解

首先,关于 set 底层的 intset,listpack,hashtable 这三种数据类型,listpack 之前已经介绍过。 hashtable 基本不太可能面试被问到。而 intset,其实是一种比较简单的数据结构。就是保存一个整数。
<intset.h 35 行>然后,关于这三种数据结构之间如何转换,以 set 数据类型最为典型的 sadd 指令为例,会进入下面这个方法进行处理。
<t_set.c 605 行>在创建 set 元素时,就会根据子元素的类型,判断是用 intset 还是用 listpack。
<t_set.c 40 行>

而在添加元素时,也会根据参数判断是否需要转换底层编码<t_set.c 59 行>六、 ZSET 类型数据结构详解 1、zset 数据是如何存储的老规矩,先上结论,然后源码验证 Redis 底层综合使用 listpack + skiplist 两种结构来保存 zset 类型的数据。

127.0.0.1:6379> config get zset*
1) "zset-max-ziplist-value"
2) "64"
3) "zset-max-listpack-entries"
4) "128"
5) "zset-max-ziplist-entries"
6) "128"
7) "zset-max-listpack-value"
8) "64"
127.0.0.1:6379> zadd z1 80 a(integer) 1127.0.0.1:6379> OBJECT ENCODING z1"listpack"
127.0.0.1:6379> config set zset-max-listpack-entries 3OK127.0.0.1:6379> zadd z2 80 a 90 b 91 c 95 d(integer) 4127.0.0.1:6379> OBJECT ENCODING z2"skiplist"
区分底层数据结构的参数有两个:
# Similarly to hashes and lists, sorted sets are also specially encoded
in
# order to save a lot of space. This encoding is only used when the
length and
# elements of a sorted set are below the following limits:
zset-max-listpack-entries 128zset-max-listpack-value 642、zset 底层数据结构详解首先,zset 类型底层数据结构有 skiplist 和 listpack 两种。 listpack 结构之前已经介绍过。这个 skiplist 是一种什么样的数据结构呢?
zset 类型的数据,底层需要先按照 score 进行排序。排序过程中是需要移动内存的。如果节点数据不是太多,将这些内存移动完后,重新整理成一个类似数据 Array 的 listpack 结果是可以接受的。但是如果数据量太大(节点数和数据大小),那么频繁移动内存,开销就比较大了。这时,显然以链表这种零散的数据结构是比较合适的。
但是,对于一个单链表结构来说,要检索链表中的某一个数据,只能从头到尾遍历链表。
时间复杂度是 O(N),性能是比较低的。

如何对链表结构进行优化呢?skiplist 跳表就是一种思路。 skiplist 的优化思路是构建多层逐级缩减的子索引,用更多的索引来提升搜索的性能。
skiplist 是一种典型的用空间换时间的解决方案,优点是数据检索的性能比较高。时间复杂度是 O(logN),空间复杂度是 O(N)。但是他的缺点也很明显,就是更新链表时,维护索引的成本相对更高。因此,skiplist 适合那些数据量比较大,且是读多写少的应用场景。
Redis 天生就是针对读多写少的应用场景,而数据量的大小通过之前看到的两个参数,从数据条目数和数据大小两个方面来进行区别。
然后,Redis 底层是如何转换数据结构的呢?
还是从 zset 最为常⻅的 zadd 操作入手<t_zset.c 1838 行>往下跟踪这个 zaddGenericCommand 方法,可以看到下面这个方法:
<t_zset.c 1169 行>

3、zset 底层数据结构总结 Redis 底层综合使用 listpack+skiplist 两种数据结构来保存 zset 类型的数据。其中,当 zset 数据的 value 数据量比较小时,使用 listpack 结构保存。 value 数据量比较大时,使用 skiplist 结构保存。 skiplist 是一种典型的用空间换时间的解决方案,适合那些数据量比较大,且读多写少的数据场景。在 Redis 中使用是非常合适的。
Redis 中衡量 zset 的 value 数据大小的参数有两个,zset-max-listpack-entries 和 zsetmax-listpack-value 分别从 value 的元数数量和数据大小两方面进行区分。
七、 Redis 课程总结 Redis 中几种常⻅数据结构的底层结构总结下来就是这张表:
Redisstring set zset list hash 版本 SDS(动 Redis intset+hashta skiplist+ quicklist hashtabl 态字符 6 ble ziplist +ziplist e+ziplist 串)
quicklistRedis intset+listpac skiplist+ hashtablSDS +listpac7 k+hashtable listpack e+listk 另外,关于 Redis,有一个经久不衰的面试题,就是 Redis 为什么这么快。

这其实是一个没有标准答案的问题。 Redis 为了提升整体的运行速度,在各个方面都做了非常极致的优化。无锁化的线程模型,层层递进的集群架构,灵活定制的底层数据结构,极致优化的算法实现,等等,这些都是 Redis 对性能极致要求的体现。
但是,Redis 的价值要求其实并不仅仅是一个快。在快的同时,Redis 也在不断扩展新的业务功能,新的应用场景。集中式缓存、分布式锁、分布式主键生成、 NoSQL 数据库,向量搜索等各个方面的应用都是 Redis 不能忽视的价值。作为 Java 程序员,如何在复杂的业务场景中最大程度用好 Redis,发挥 Redis 的强大性能,就是一个绕不开的基本功。

