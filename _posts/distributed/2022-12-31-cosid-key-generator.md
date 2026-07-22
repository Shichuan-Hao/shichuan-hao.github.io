---


title: "五、融会贯通：详细分析ShardingSphere新接入的CosID主键生成框架"
description: "融汇贯通:详细分析 ShardingSphere 新接入的 CosID 主键生成框架-- 楼兰前面几个章节,带你体验了非常多 ShardingSphere 的功能。"
author: hsc
date: 2022-12-31 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Redis', 'Kafka', 'Zookeeper', '分库分表']
toc: true


---

融汇贯通:详细分析 ShardingSphere 新接入的 CosID 主键生成框架-- 楼兰前面几个章节,带你体验了非常多 ShardingSphere 的功能。有没有那么一刻,你会觉得分库分表也没那么麻烦。用好 ShardingSphere 框架就是了。但分表所带来的问题,其实远比你想象的复杂。这次,我带你一起来看看 ShardingSphere5.x 版本集成了一个新的主键生成框架 CosId,看看分布式主键生么一个不起眼的问题,水能够有多深。只有你有足够能力自己去研究分库分表这些问题,你才能真正融会贯通,把 ShardingSphere 框架真正当成一个灵具来用,而不是一个呆板的框架。
一、从分库分表的一个小坑说起或许你会觉得我小题大做了。那我们不多啰嗦,从一个分库分表的小实验开始。
现在,我想要将一个 course 表的数据分到两个库两张表,一共四个分片中。这是一个最典型的分库分表的场景。
Course 课程信息按照 cid 字段进行分片,那么分库的算法可以简单设置为按 cid 奇偶拆分,定制算法 m$->{cid%2}就行了。而分表的算法呢?如果也是简照 cid 奇偶拆分,算法定制为 course_$->{cid%2+1}。这个时候,所有的 Course 课程记录,实际上只能分配到 m0.course_1 和 m2.course_2 两个分片表不是我们期待的结果啊。我们是希望把数据分到四张表里。这时候怎么办?一种很自然的想法是调整分表的算法,让他按照 4 去轮询,定制分片算法 c>{((cid+1)%4).intdiv(2)+1}。 这样简单看起来是没有问题的。如果 ID 是连续递增的,那么这个算法就可以将数据均匀的分到四个分片中。

算法验证完成,接下来,配置到 ShadingSphere 中使用一下。下面是是示例配置:

# 打印 SQL
spring.shardingsphere.props.sql-show = truespring.main.allow-bean-definition-overriding = true
# ----------------数据源配置
# 指定对应的库
spring.shardingsphere.datasource.names=m0,m1spring.shardingsphere.datasource.m0.type=com.alibaba.druid.pool.DruidDataSourcespring.shardingsphere.datasource.m0.driver-class-name=com.mysql.cj.jdbc.Driverspring.shardingsphere.datasource.m0.url=jdbc:mysql://192.168.65.212:3306/shardingdb1?serverTimezone=UTCspring.shardingsphere.datasource.m0.username=rootspring.shardingsphere.datasource.m0.password=rootspring.shardingsphere.datasource.m1.type=com.alibaba.druid.pool.DruidDataSourcespring.shardingsphere.datasource.m1.driver-class-name=com.mysql.cj.jdbc.Driverspring.shardingsphere.datasource.m1.url=jdbc:mysql://192.168.65.212:3306/shardingdb2?serverTimezone=UTCspring.shardingsphere.datasource.m1.username=rootspring.shardingsphere.datasource.m1.password=root
#------------------------分布式序列算法配置
# 雪花算法,生成 Long 类型主键。
spring.shardingsphere.rules.sharding.key-generators.alg_snowflake.type=SNOWFLAKE
#spring.shardingsphere.rules.sharding.key-generators.alg_snowflake.type=COSID_SNOWFLAKE
spring.shardingsphere.rules.sharding.key-generators.alg_snowflake.props.worker-id=1
# 指定分布式主键生成策略
spring.shardingsphere.rules.sharding.tables.course.key-generate-strategy.column=cidspring.shardingsphere.rules.sharding.tables.course.key-generate-strategy.key-generator-name=alg_snowflake
#-----------------------配置实际分片节点
spring.shardingsphere.rules.sharding.tables.course.actual-data-nodes=m$->{0..1}.course_$->{1..2}
#MOD 分库策略
spring.shardingsphere.rules.sharding.tables.course.database-strategy.standard.sharding-column=cidspring.shardingsphere.rules.sharding.tables.course.database-strategy.standard.sharding-algorithm-name=course_db_algspring.shardingsphere.rules.sharding.sharding-algorithms.course_db_alg.type=MODspring.shardingsphere.rules.sharding.sharding-algorithms.course_db_alg.props.sharding-count=2
#给 course 表指定分表策略 standard-按单一分片键进行精确或范围分片
spring.shardingsphere.rules.sharding.tables.course.table-strategy.standard.sharding-column=cidspring.shardingsphere.rules.sharding.tables.course.table-strategy.standard.sharding-algorithm-name=course_tbl_alg
# 分表策略-INLINE:按单一分片键分表
spring.shardingsphere.rules.sharding.sharding-algorithms.course_tbl_alg.type=INLINE
#spring.shardingsphere.rules.sharding.sharding-algorithms.course_tbl_alg.props.algorithm-expression=course_$->{cid%2+1}
#这种算法如果 cid 是严格递增的,就可以将数据均匀分到四个片。但是雪花算法并不是严格递增的。
#如果需要做到均匀分片,修改算法同时,还要修改雪花算法。把 SNOWFLAKE 换成 MYSNOWFLAKE
spring.shardingsphere.rules.sharding.sharding-algorithms.course_tbl_alg.props.algorithm-expression=course_$->{((cid+1)%4).intdiv(2)+1}应用层,就直接往 course 表里插入多条消息@Testpublic void addcourse() {for (int i = 0; i < 10; i++) {Course c = new Course();
//Course 表的主键字段 cid 交由 雪花算法生成。
c.setCname("java");
c.setUserId(1001L);
c.setCstatus("1");
courseMapper.insert(c);
//insert into course values ....System.out.println(c);
}}那么你一定会发现,这十条 course 信息,很奇怪。库倒是分得挺均匀,但是表却分得很奇怪。就是没有办法插入到四张表的。只能插入到 m0.course_m2.course_2 两张表中。要怎么解决呢?
解决方案很简单,将表分片算法的 type 换成 COSID_SNOWFLAKE。
spring.shardingsphere.rules.sharding.key-generators.alg_snowflake.type=COSID_SNOWFLAKE 再次尝试,course 表数据就能均匀的分配到四张表中。

为什么会这样呢?这就需要你能够真正理解在分库分表的场景下,要怎么解决分布式主键生成这么一个看似不起眼的问题。
二、雪花算法详细拆解 1、什么是雪花算法雪花算法是 twitter 公司开源的 ID 生成算法。他不需要依赖外部组件,算法简单,效率也高。也是实际企业开发过程中,用得最为广泛的一种分布式主键略。
雪花算法的基础思想是采用一个 8 字节的二进制序列来生成一个主键。为什么用 8 个字节?因为 8 字节正好就是一个 Long 类型的变量。即保持足够的区分能比较自然的与业务结合。
可以看到,SNOWFLAKE 其实还是以 41 个 bit 的时间戳为主体,放在最高位。接下来 10 个 bit 位的工作进程位,是用来标识每一台机器的。但是实现时,用自行扩展的。后面 12 个 bit 的序列号则就是一个自增的序列位。
其核心思想就是将唯一值拼接成一个整体唯一值。首先从整体上来说,时间戳是一个最好的保证趋势递增的数字,所以时间戳自然是主体,放到最高位如果有多个节点同时生成,那么就有可能产生相同的时间戳。怎么办?那就把进程 ID 给拼接上来。接下来如果在同一个进程中有多个线程同时生成,那会产生相同的 ID,怎么办?那就再加上一个严格递增的序列位。这样就整体保证了全局的唯一性。
在标准的雪花算法基础上,也诞生了很多类似的雪花算法实现。无非就是对这些数据根据业务场景进行重组。比如缩短时间戳位,将工作进程位加⻓分成为 datacenter 和 worker 两个部分,等等,但是其实万变不离其宗。
2、COSID_SNOWFLAKE 如何解决取模分片数据不均匀的问题回到我们之前说的取模分片数据不均匀的问题。
首先,你要明白一个数学规律。对于任何一个数字,对 2 取模的结果,实际上就是在取这个数字的二进制表达时的最后一位。对 4 取模的结果,实际上就这个数字的二进制表达时的最后两位。依次类推。所以,回到我们的问题。要让数据均匀分到四个真实片,那么实际上是需要保证生成的一系列雪花算他们的二进制表达的最后两位是连续递增的。
然后,回到之前的问题。自然就是要比对 SNOWFLAKE 算法和 COSID_SNOWFLAKE 算法他们的最后一个序列位有什么区别。
到现在,你应该能够找到分库分表中配置 SNOWFLAKE 和 COSID_SNOWFLAKE 两种不同算法,分别对应的源码在哪里了。那么我们直接拿来比较。
先来看 SNOWFLAKE 对应算法实现类是 SnowflakeKeyGenerateAlgorithm。他是这样生成雪花算法 ID 的。

@Overridepublic synchronized Long generateKey() {long currentMilliseconds = timeService.getCurrentMillis();
if (waitTolerateTimeDifferenceIfNeed(currentMilliseconds)) {currentMilliseconds = timeService.getCurrentMillis();
}// 时间重 复,序列位就加 1。
if (lastMilliseconds == currentMilliseconds) {if (0L == (sequence = (sequence + 1) & SEQUENCE_MASK)) {currentMilliseconds = waitUntilNextTime(currentMilliseconds);
}} else {//如果时间更新了, 序列位就会重置 vibrateSequenceOffset();
sequence = sequenceOffset;
}lastMilliseconds = currentMilliseconds;
return ((currentMilliseconds - EPOCH) << TIMESTAMP_LEFT_SHIFT_BITS) | (getWorkerId() << WORKER_ID_LEFT_SHIFT_BITS) |sequence;
}在这种雪花算法下,只要两次生成 ID 的时间不同,那么这个 sequence 就会在 0 和 1 之间震荡。而在我们的项目中,每生成一次 ID 后,还有写入数据库的作,时间必然是要往后推延的。这样,对 4 取模的结果就当然只能有 0 或 1 这两个结果。2 和 3 对应的两个分片就分不到了。
具体查看 vibrateSequenceOffset 方法。默认情况下,他会让 sequenceOffset 分别在 0 和 1 之间震荡。
实际上,如果你看懂了源码。就会发现,在使用 SNOWFLAKE 算法时,如果在 props 中增加配置一个参数 max-vibration-offset=12 。 那么这个 sequence,就可以从 0 递增到 10。这样,也是可以解决之前的数据分配不均匀的问题。也就是 spring.shardingsphere.rules.sharding.key-generators.alg_snowflake.type=SNOWFLAKEspring.shardingsphere.rules.sharding.key-generators.alg_snowflake.props.worker-id=1spring.shardingsphere.rules.sharding.key-generators.alg_snowflake.props.max-vibration-offset=12 但是这个莫名其妙的配置,除了源码,你找不到任何其他的资料说明。
然后再来看 COSID_SNOWFLAKE 算法生成雪花 ID 的过程。他的源码在这个地方:
//me.ahoo.cosid.snowflake.AbstractSnowflakeId 类@Overridepublic synchronized long generate() {long currentTimestamp = getCurrentTime();
if (currentTimestamp < lastTimestamp) {throw new ClockBackwardsException(lastTimestamp, currentTimestamp);
}//region Reset sequence based on sequence reset threshold,Optimize the problem of uneven sharding.if (currentTimestamp > lastTimestamp&& sequence >= sequenceResetThreshold) {sequence = 0L;
}/ /sequnce 直接递增。到达 maxSequence 后再重置。
sequence = (sequence + 1) & maxSequence;
if (sequence == 0L) {currentTimestamp = nextTime();
}//endregionlastTimestamp = currentTimestamp;
long diffTimestamp = (currentTimestamp - epoch);
if (diffTimestamp > maxTimestamp) {throw new TimestampOverflowException(epoch, diffTimestamp, maxTimestamp);
}return diffTimestamp << timestampLeft
| machineId << machineLeft
| sequence;
}可以看到,对于 seqence 序列位。 CosID 提供的实现就简单粗暴得多。在达到 maxSequence 最大值之前,sequence 都是直接递增的。这样递增的结果花 ID 的二进制最后几位,都是严格递增的,数据自然也就分布均匀了。

这还只是雪花算法中的最后序列位。实际上,在分库分表场景下,雪花算法的问题还不仅仅在于最后的序列位。
下一个问题,就是雪花算法中间的工作进程位。之前分析过,雪花算法的工作进程位是用来区分不同的工作进程的。也就是说,如果我们的这个服务是布式的微服务,那么每一个服务的工作进程位都应该是要不同的。但是,在实际项目中,这个小小的问题其实是很难的。
一方面,绝大部分程序员在用的时候,不会专⻔为了雪花算法单独设置工作进程位。 例如在 ShardingSphere 中,实际上是可以给 SNOWFLAKE 主键生 worker-id 参数来设置进程位的。
spring.shardingsphere.rules.sharding.key-generators.alg_snowflake.type=SNOWFLAKEspring.shardingsphere.rules.sharding.key-generators.alg_snowflake.props.worker-id=1 但是,这个 worker-id 参数,就连官方文档中也没有做过单独的说明,基本也就不可能要求所有人在用 SNOWFLAKE 时都去单独设置了。
另一方面,要给每个进程设置一个不重复的工作进程位,是有点困难的。如果只是简单的一两个服务,那么手动指定一下 worker-id 参数也就完成了。但果是一个几十个服务的大型微服务系统呢?你如何保证程序员或者运维人员能够保证这几十个服务的 worker-id 是不重复的?这基本上就是一个不可能完务。
这个问题很隐蔽,之前基本上很少有人想到这个事情。但是,别急,这个小小的 COSID 框架想到了。接下来,我带你去 COSID 的源码当中做详细的拆解三、深入源码全面理解 CosID 框架 1、搭建 CosID 测试应用虽然 CosID 目前已经集成进了 ShardingSphere,但是,实际的情况是,ShardingSphere 默认只集成了 CosID 的一部分功能,并没有全部集成进来。这是 CosID 实际上有很多核心功能是需要额外的存储系统的。这必然给 ShardingSphere 带来更大的复杂性。
这么说有点虚,你可能还难以理解。所以,这次我们单独搭建一个 CosID 的测试应用,把 CosID 拆解明白了,你就知道怎么回事了。
搭建步骤,还是以 SpringBoot 为核心,来引入 CosID 的支持。
step1、在之前示例项目中增加一个模块 CosIDDemo。其中的 pom.xml 依赖<properties><cosid.version>2.9.1</cosid.version></properties><dependencies><dependency><groupId>me.ahoo.cosid</groupId><spanrtifactId>cosid-spring-boot-starter</artifactId><version>${cosid.version}</version></dependency><dependency><groupId>org.springframework.boot</groupId><spanrtifactId>spring-boot-starter</artifactId></dependency><dependency><groupId>org.springframework.boot</groupId><spanrtifactId>spring-boot-starter-test</artifactId><scope>test</scope></dependency><dependency><groupId>junit</groupId><spanrtifactId>junit</artifactId><version>4.13.2</version><scope>test</scope></dependency></dependencies>注意这个 cosid 组件的版本。不同的版本是有一些不同的小坑的。
step2、启动类。没什么特别的

@SpringBootApplicationpublic class DistIDApp {public static void main(String[] args) {SpringApplication.run(DistIDApp.class, args);
}}step3、application.properties 配置文件 cosid.namespace=cosid-examplecosid.enabled=truecosid.machine.enabled=truecosid.machine.distributor.manual.machine-id=1cosid.snowflake.enabled=true 有了前面的铺垫,你应该能猜到这个配置是用来生成一个雪花 ID 的,其中 machine 就是工作进程位 1.step4、应用中生成主键在应用中使用 CosID 就非常简单了。只要从 Spring 的 IOC 容器中获取一个 IdGeneratorProvider 实例,就可以获取 ID 了。
@SpringBootTest@RunWith(SpringRunner.class)
public class DistIDTest {@Resourceprivate IdGeneratorProvider provider;
@Testpublic void getId(){for (int i = 0; i < 100; i++) {System.out.println(provider.getShare().generate());
}}}实际上,ShardingSphere 中集成 CosId 框架的原理也是这样的,通过对 IdGeneratorProvider 进行封装,从而获取主键。
唯一需要特别注意的是 SpringSphere 中集成的 CosID 的版本,没有目前案例新。案例当中默认集成的 cosid 版本是 1.14.1。在这个版本下,有一个小 B 需要在 SpringBoot 的启动类上增加如下两个注解才能用。 --现在最新的 2.9.1 版本已经不需要了。
@EnableConfigurationProperties({MachineProperties.class})
@ComponentScans(value = {@ComponentScan("me.ahoo.cosid")})
CosID 框架主要集成了三种主键生成模式,1、SnowFlake 雪花算法。2、SengmentID 号段模式。3、SegmentChainID 号段链模式。其中后两种的思路的,都是用的 Segment 号段模式,只是实现思路不同。主要用来生成严格递增的主键序列。
而这些不同的生成模式,在应用层面,统一由 IdGeneratorProvider 提供服务。也就是说,应用代码不用做任何调整,只需要调整相关配置,就可以成成型的分布式主键。
接下来逐一了解这几种模式。
2、SnowFlake 雪花算法 1、基础使用之前搭建的简单示例,就是一个使用雪花算法的示例。在之前的演示中,这个 machineID 就是雪花算法的工作进程位,不过之前配置的 manual 方式,实手动设置的。那么按照之前的分析,他依然会有与大型项目水土不服的问题。
那么怎么解决呢?当然是自动生成。这其实是不容易的。主键生成框架是要生成一系列唯一的主键。现在为了生成主键,又要先生成一系列不唯一的 machineID。这不就成了一个鸡生蛋,蛋生鸡的问题了。怎么办呢?来看看 CosID 的处理方式。
CosID 对于 MachineID 提供了多种实现形式。关于这些可选方式,具体可以看下他源码当中的这个枚举类型:

//#me.ahoo.cosid.spring.boot.starter.machine.MachinePropertiespublic enum Type {MANUAL, //手动分 配 STATEFUL_SET, //与 K8s 结合的状态机机制 JDBC,MONGO,REDIS,ZOOKEEPER,PROXY //类似 ShardingProxy,搭建一个第三方 CosID 服务分配}这里可以引入很多的第三方存储来辅助分发 machineID。
如果你想要使用最为常⻅的 JDBC 的方式,那么只要指定配置即可。
cosid.machine.distributor.type=jdbc 如果你要使用 jdbc 模式,那么还需要添加 cosid-jdbc 的扩展依赖包,并且自行引入 jdbc 相关的依赖。
<dependency><groupId>me.ahoo.cosid</groupId><spanrtifactId>cosid-jdbc</artifactId><version>${cosid.version}</version></dependency><dependency><groupId>com.alibaba</groupId><spanrtifactId>druid-spring-boot-starter</artifactId><version>1.1.20</version><!-- 版本冲突 --><exclusions><exclusion><spanrtifactId>spring-boot-autoconfigure</artifactId><groupId>org.springframework.boot</groupId></exclusion></exclusions></dependency><dependency><groupId>org.springframework.boot</groupId><spanrtifactId>spring-boot-starter-jdbc</artifactId><version>${spring.boot.version}</version></dependency><dependency><groupId>mysql</groupId><spanrtifactId>mysql-connector-java</artifactId><version>8.0.20</version></dependency>其中 cosid-jdbc 是 cosid 的核心扩展包。而其他相关依赖则是 SpringBoot 应用操作 MySQL 数据库所需要的一系列依赖。 cosid 和 mybatis 等框架类似,也从 Spring 容器当中获取 DataSource 数据源,而不关心如何构建 DataSource。
接下来,修改应用的配置文件 cosid.machine.distributor.type=jdbcspring.datasource.type=com.alibaba.druid.pool.DruidDataSourcespring.datasource.driver-class-name=com.mysql.cj.jdbc.Driverspring.datasource.url=jdbc:mysql://192.168.65.212:3306/test?serverTimezone=UTCspring.datasource.username=rootspring.datasource.password=root 接下来,需要创建对应的数据库,并且还需要在数据库中手动创建一张表。建表语句为;

create table if not exists cosid_machine(name varchar(100) not null comment '{namespace}.{machine_id}',namespace varchar(100) not null,machine_id integer unsigned not null default 0,last_timestamp bigint unsigned not null default 0,instance_id varchar(100) not null default '',distribute_time bigint unsigned not null default 0,revert_time bigint unsigned not null default 0,constraint cosid_machine_pkprimary key (name)
) engine = InnoDB;
create index idx_namespace on cosid_machine (namespace);
create index idx_instance_id on cosid_machine (instance_id);
好了,如果没有依赖版本冲突,那么接下来就可以愉快的跑单元测试案例,获取分布式 ID 了。
2、重点机制剖析关于 CosId 的雪花算法,之前已经做了铺垫。这里重点要了解的是他如何给雪花算法生成中间的那一段 MachineID。关于这个问题,另外做一个单元测了。
public class SnowFlakeTest {@Resourceprivate MachineId machineId;
@Resourceprivate SnowflakeId snowflakeId;
@Testpublic void snowflakeTest(){System.out.println("machineId:"+machineId.getMachineId());
for (int i = 0; i < 100; i++) {System.out.println("snowflakeId: "+snowflakeId.generate());
}}}可以看到,其实 CosId 就是通过注入一个 MachineId 实例,提供机器位。然后这个 MachineId 实例,会被一个 SnowFlakeId 实例引用,生成雪花算法。其终,这个 SnowFlakeId 也会被 IdGeneratorProvider 引用。
接下来,我们就一起到源码当中逛逛,看下这些具体的实例是如何构建的。
首先,雪花算法的 SnowFlakeId 示例的注入方式是这样的:

// me.ahoo.cosid.spring.boot.starter.snowflake.SnowflakeIdBeanRegistrar// 注册 Beanpublic void register() {if (customizeSnowflakeIdProperties != null) {customizeSnowflakeIdProperties.customize(snowflakeIdProperties);
}SnowflakeIdProperties.ShardIdDefinition shareIdDefinition = snowflakeIdProperties.getShare();
if (shareIdDefinition.isEnabled()) {// 核心构建方法 registerIdDefinition(IdGeneratorProvider.SHARE, shareIdDefinition);
}snowflakeIdProperties.getProvider().forEach(this::registerIdDefinition);
}private void registerIdDefinition(String name, SnowflakeIdProperties.IdDefinition idDefinition) {//创建 SnowFlakeIdSnowflakeId idGenerator = createIdGen(idDefinition, clockBackwardsSynchronizer);
//注册到 IdGeneratorProvider 中 registerSnowflakeId(name, idGenerator);
}private void registerSnowflakeId(String name, SnowflakeId snowflakeId) {if (idGeneratorProvider.get(name).isEmpty()) {idGeneratorProvider.set(name, snowflakeId);
}String beanName = name + "SnowflakeId";
applicationContext.getBeanFactory().registerSingleton(beanName, snowflakeId);
}/ /构建 SnowFlakeId 方法 private SnowflakeId createIdGen(SnowflakeIdProperties.IdDefinition idDefinition,ClockBackwardsSynchronizer clockBackwardsSynchronizer) {long epoch = getEpoch(idDefinition);
int machineBit = MoreObjects.firstNonNull(idDefinition.getMachineBit(), machineProperties.getMachineBit());
String namespace = Namespaces.firstNotBlank(idDefinition.getNamespace(), cosIdProperties.getNamespace());
// 分配 machineIdint machineId = machineIdDistributor.distribute(namespace, machineBit, instanceId,machineProperties.getSafeGuardDuration()).getMachineId();
//根据配置创建不同的雪花算法实例 SnowflakeId snowflakeId;
if (SnowflakeIdProperties.IdDefinition.TimestampUnit.SECOND.equals(idDefinition.getTimestampUnit())) {snowflakeId = new SecondSnowflakeId(epoch, idDefinition.getTimestampBit(), machineBit, idDefinition.getSequenceBitmachineId, idDefinition.getSequenceResetThreshold());
} else {snowflakeId =new MillisecondSnowflakeId(epoch, idDefinition.getTimestampBit(), machineBit, idDefinition.getSequenceBit(),machineId, idDefinition.getSequenceResetThreshold());
}if (idDefinition.isClockSync()) {snowflakeId = new ClockSyncSnowflakeId(snowflakeId, clockBackwardsSynchronizer);
}IdConverterDefinition converterDefinition = idDefinition.getConverter();
final ZoneId zoneId = ZoneId.of(snowflakeIdProperties.getZoneId());
return new SnowflakeIdConverterDecorator(snowflakeId, converterDefinition, zoneId, idDefinition.isFriendly()).decorate}这段方法有个重点需要关注的地方。
1、createIdGen 方法构建雪花算法实例时,会根据配置信息选择创建 SecondSnowflakeId 还是 MillisecondSnowflakeId。这两个具体实例的区别是他们前时间的单位不同。一个是获取秒,一个是获取毫秒。
这个区别会涉及到 CosId 对于雪花算法时钟回拨问题的处理。时钟回拨问题就是雪花算法的第一个部分时间戳可能面临的一种问题。因为计算机中记录会产生波动的。有可能下一刻产生的时间反而比上一刻的时间更早,这就是时钟回拨问题。这种回拨的时钟很显然就有可能会造成时钟回拨的问题。
因此雪花算法通常都需要对时钟回拨进行处理。如果在要生成 ID 时,发现当前时间比上一次生成的时间还早,那就要休眠一段时间,直到时间往后延续重新生成 ID。
2、CosID 中,实际生成雪花算法的方法在 AbstractSnowflakeId 中

//me.ahoo.cosid.snowflake.AbstractSnowflakeId@Overridepublic synchronized long generate() {long currentTimestamp = getCurrentTime();
if (currentTimestamp < lastTimestamp) {throw new ClockBackwardsException(lastTimestamp, currentTimestamp);
}//region Reset sequence based on sequence reset threshold,Optimize the problem of uneven sharding.if (currentTimestamp > lastTimestamp&& sequence >= sequenceResetThreshold) {sequence = 0L;
}sequence = (sequence + 1) & maxSequence;
if (sequence == 0L) {currentTimestamp = nextTime();
}//endregionlastTimestamp = currentTimestamp;
long diffTimestamp = (currentTimestamp - epoch);
if (diffTimestamp > maxTimestamp) {throw new TimestampOverflowException(epoch, diffTimestamp, maxTimestamp);
}return diffTimestamp << timestampLeft
| machineId << machineLeft //注入 机器位
| sequence;
}从这里可以看到,这个 machine 就是作为雪花算法的工作进程位使用的。
然后,其中的机器位 MachineId,就是通过注入到 Spring 容器当中的 MachineID 对象获取的。
//me.ahoo.cosid.spring.boot.starter.machine.CosIdMachineAutoConfiguration@Bean@ConditionalOnMissingBean({MachineId.class})
public MachineId machineId(MachineIdDistributor machineIdDistributor, InstanceId instanceId) {int machineId = machineIdDistributor.distribute(this.cosIdProperties.getNamespace(), this.machineProperties.getMachineinstanceId, this.machineProperties.getSafeGuardDuration()).getMachineId();
return new MachineId(machineId);
}所以,对于 MachineId 分配这个功能,在 CosId 框架当中,都是通过 MachineIdDistributor 接口的 distribute 方法扩展出来的。
而使用 JDBC 方式,具体的 MachineIdDistributor 对象实例,是这样注入的。
@AutoConfiguration@ConditionalOnCosIdEnabled@ConditionalOnCosIdMachineEnabled@ConditionalOnClass({JdbcMachineIdDistributor.class})
@ConditionalOnProperty(value = {"cosid.machine.distributor.type"},havingValue = "jdbc"
)
public class CosIdJdbcMachineIdDistributorAutoConfiguration {public CosIdJdbcMachineIdDistributorAutoConfiguration() {}@Bean@ConditionalOnMissingBeanpublic JdbcMachineIdDistributor jdbcMachineIdDistributor(DataSource dataSource, MachineStateStorage localMachineState,ClockBackwardsSynchronizer clockBackwardsSynchronizer) {return new JdbcMachineIdDistributor(dataSource, localMachineState, clockBackwardsSynchronizer);
}}CosId 就是通过配置类上一通眼花缭乱的@Conditional 注解,注入不同的 MachineIdDistributor 实例,从而实现 MachineId 生成。
其他类型的机器生成器也都是类似的。例如,手动指定机器 ID 时,他注入的 MachineIdDistributor 实例是这样的:

// me.ahoo.cosid.spring.boot.starter.machine.CosIdMachineAutoConfiguration@Bean@ConditionalOnMissingBean@ConditionalOnProperty(value = {"cosid.machine.distributor.type"},matchIfMissing = true,havingValue = "manual"
)
public ManualMachineIdDistributor machineIdDistributor(MachineStateStorage localMachineState, ClockBackwardsSynchronizerclockBackwardsSynchronizer) {MachineProperties.Manual manual = this.machineProperties.getDistributor().getManual();
Preconditions.checkNotNull(manual, "cosid.machine.distributor.manual can not be null.");
Integer machineId = manual.getMachineId();
Preconditions.checkNotNull(machineId, "cosid.machine.distributor.manual.machineId can not be null.");
Preconditions.checkArgument(machineId >= 0, "cosid.machine.distributor.manual.machineId can not be less than 0.");
return new ManualMachineIdDistributor(machineId, localMachineState, clockBackwardsSynchronizer);
}未来如果你想要自己实现一个 MachineId 分配机制,其实也可以参照这种方式,往里面注入一个 MachineIdDistributor 的实现类即可。
当然,说起来简单,但是,具体实现时还是会有一些小问题的。如果你真有这样的想法,我非常鼓励你自己动手试试。相信我。这种成熟的开源框架比的任何项目都更有锻炼价值。
3、基于 JDBC 的工作进程 ID 分发机制实现分析上层的这些接口其实还只是与 Spring 框架集成的一层入口。那么从 MachineIdDistributor 接口往下的具体实现,才算是进入了 Cosid 的核心。那么 cosid 现机器位分配的呢?这就开始进入了真正让人迷糊的阶段了。
其实工作进程 ID 原本认为是一个比较简单的东⻄,只要在不同进程之间进行区分就行了。他并不需要有什么实际的意义。
cosid 定制了一套基础的机器位分发的流程,与每种第三方服务结合时,都是按这一套相同的流程工作。 这个流程是什么样呢?那就从最熟悉的 JDBC 的制往下看看把。其实这个问题,可以分两步来看。
首先:如何区分不同的工作进程?
cosid 中区分不同的工作进程主要是依靠两个数据,cosid 的命名空间 + 应用的 IP 和端口??
其中命名空间可以在配置文件中通过 cosid.namespace 参数指定。这属于 cosid 自己的定义,没什么解释。
然后应用的 IP 可以直接通过应用读取。但是端口还是需要通过参数配置。
//me.ahoo.cosid.spring.boot.starter.machine.CosIdMachineAutoConfiguration@Bean@ConditionalOnMissingBeanpublic InstanceId instanceId(HostAddressSupplier hostAddressSupplier) {boolean stable = Boolean.TRUE.equals(this.machineProperties.getStable());
if (!Strings.isNullOrEmpty(this.machineProperties.getInstanceId())) {return InstanceId.of(this.machineProperties.getInstanceId(), stable);
} else {int port = ProcessId.CURRENT.getProcessId();
if (Objects.nonNull(this.machineProperties.getPort()) && this.machineProperties.getPort() > 0) {port = this.machineProperties.getPort();
}return InstanceId.of(hostAddressSupplier.getHostAddress(), port, stable);
}}这个 InstanceId 是用来区分不同的服务实例的。那怎么区分呢?
首先读取 machineProperties 的 instanceId。这个是由应用自己配的。如果应用有这个功夫单独配置 instanceId,那就不用自动生成 machineID 了,所个 instanceId,大概率是不会配的。
然后接下来就是从 IP+port 的方式进行区分。
接下来这个 stable 参数,实际上用来保持 IP 稳定的。因为 cosId 考虑到 machineid 还是可以回收利用的,比如 machineid 为 1 的进程,如果下线了,而这号进程又不是一个稳定的服务,那么后面的进程还可以重新分到 1 这个进程号。但是如果 1 是稳定的,后面的进程就不能再用 1 这个进程号了。
然后:如何给不同的工作进程分发不同的 MachineId?

分发 MachineId 时,首先有一层统一的入口逻辑,维护一个本地缓存。
// me.ahoo.cosid.machine.AbstractMachineIdDistributor@Nonnullpublic MachineState distribute(String namespace, int machineBit, InstanceId instanceId, DurationsafeGuardDuration) throws MachineIdOverflowException {Preconditions.checkArgument(!Strings.isNullOrEmpty(namespace), "namespace can not be empty!");
Preconditions.checkArgument(machineBit > 0, "machineBit:[%s] must be greater than 0!", machineBit);
Preconditions.checkNotNull(instanceId, "instanceId can not be null!");
MachineState localState = this.machineStateStorage.get(namespace, instanceId);
if (!MachineState.NOT_FOUND.equals(localState)) {this.clockBackwardsSynchronizer.syncUninterruptibly(localState.getLastTimeStamp());
return localState;
} else {localState = this.distributeRemote(namespace, machineBit, instanceId, safeGuardDuration);
if (ClockBackwardsSynchronizer.getBackwardsTimeStamp(localState.getLastTimeStamp()) > 0L) {this.clockBackwardsSynchronizer.syncUninterruptibly(localState.getLastTimeStamp());
localState = MachineState.of(localState.getMachineId(), System.currentTimeMillis());
}this.machineStateStorage.set(namespace, localState.getMachineId(), instanceId);
return localState;
}}这个本地缓存就跟之前看不懂的 stable 是否稳定扯上关系了。如果 stable 是 true,那就基于本地文件进行持久化保存。 文件地址通过参数 cosid.machinstorage.local.state-location 指定。否则,就基于本地内存维护缓存,应用停止就消失了。这里可以证明,stable 稳定的服务,就会占用稳定的 machin 算应用停了,文件里还记着呢。
后面的 distributeRemote 方法就是交由各种具体实现类去扩展实现的抽象方法了。例如 JDBC 的分发方式是这样的:
//me.ahoo.cosid.jdbc.JdbcMachineIdDistributor@Overrideprotected MachineState distributeRemote(String namespace, int machineBit, InstanceId instanceId, Duration safeGuardDuratioif (log.isInfoEnabled()) {log.info("Distribute Remote instanceId:[{}] - machineBit:[{}] @ namespace:[{}].", instanceId, machineBit, namespac}try (Connection connection = dataSource.getConnection()) {//本地发 MachineState machineState = distributeBySelf(namespace, instanceId, connection, safeGuardDuration);
if (machineState != null) {return machineState;
}/ /回滚发 machineState = distributeByRevert(namespace, instanceId, connection, safeGuardDuration);
if (machineState != null) {return machineState;
}/ /远程发 return distributeMachine(namespace, machineBit, instanceId, connection);
} catch (SQLException sqlException) {if (log.isErrorEnabled()) {log.error(sqlException.getMessage(), sqlException);
}throw new CosIdException(sqlException.getMessage(), sqlException);
}}虽然各种服务的具体实现各不相同,但是基本的分发逻辑都是这三个步骤。 先自己发布,然后再回滚发布,然后再远程发布。
1、自己发布执行的 SQL 语句是 select machine_id, last_timestamp from cosid_machine where namespace=? and instance_id=? and last_timestamp>?
意思就是获取当前实例获取过的 machine_id。不过在分配时,会根据 last_timestamp 进行安全监测。简单来说,就是只获取在安全时间内分配过的 ID 间外的不算。这个安全时间,如果对于 stable 稳定的机器,那么安全时间就是从 0 开始。不稳定的机器,安全时间可以通过参数 cosid.machine.guardeguard-duration 指定。默认 5 分钟。然后源码中甚至还定了一个永久的安全时间。 Duration FOREVER_SAFE_GUARD_DURATION =Duration.ofMillis(Long.MAX_VALUE); 这样也会忽略安全时间的查询条件。

如果查到了历史记录,那么就更新 last_timestamp,然后返回历史的 machine_id。如果没查到,就进行回滚发布。
2、回滚发布执行的 SQL 语句是 select machine_id, last_timestamp from cosid_machine where namespace=? and (instance_id='' or last_timestamp<=?)
这个意思应该是获取别的进程不用了的 MachineId。可能是无人认领的,也可能是超过了安全时间的。查到了就更新 instance_id,last_timestamp 和 distribute_time,然后返回历史的 machine_id。如果没查到,就进行远程发布。
是不是表示认领不包含具体实例的公共 machine_id?但是我把源码看到最后也没看到 instance_id=''的数据是怎么插入进去的。
3、远程发布远程发布时,获取机器 ID 的 SQL 是 select max(machine_id)+1 as next_machine_id from cosid_machine where namespace=?
从 MySQL 中重新分配一个新的 machine_id。获取到的 next_machine_id 就是分配的机器 ID。如果没有记录,就返回 1。获取完机器 ID 后,就会往 cosid_machine 里插入一条记录,把这个分配的机器 ID 记录下来。
虽然这样每获取一次 MachineId 就会要往 MySQL 里插入一条数据,但是已插入的旧数据还可以被后面的进程重复利用,所以使用的效率还是挺高的这个流程很容易移植到其他服务中。例如 MongoDB。cosid 的其他几种服务实现也都按照这样一个统一的流程。
3、Segment 数据段模式 1、Segment 模式基础使用雪花算法生成的主键 ID 属于趋势递增,但并不连续。 Segment 号段模式主要是用来生成一系列连续增⻓的分布式主键 ID。先来看看 CosID 怎么生成连续后再来分析里面的⻔道。
CosID 使用 segnment 号段非常方便。应用中依然只要从 Spring 容器里获取 IdGeneratorProvider 实例,然后通过这个实例获取 ID 即可。唯一需要修改的信息。
以最常用的 JDBC 为例,pom 依赖已经在上一个章节当中添加完了,这里直接修改配置,就可以换成 segment 的实现。
spring.datasource.type=com.alibaba.druid.pool.DruidDataSourcespring.datasource.driver-class-name=com.mysql.cj.jdbc.Driverspring.datasource.url=jdbc:mysql://192.168.65.212:3306/test?serverTimezone=UTCspring.datasource.username=rootspring.datasource.password=rootcosid.namespace=cosid-examplecosid.enabled=true
#关闭雪花算法功能
cosid.snowflake.enabled=false
#machineid 还是要注入
cosid.machine.enabled=truecosid.machine.distributor.type=jdbc
#使用 segment 模式
cosid.segment.enabled=true
#单 segment 模式,chain:segmen tchain 模式
cosid.segment.mode=segmentcosid.segment.distributor.type=jdbc
#初始化建表
cosid.segment.distributor.jdbc.enable-auto-init-cosid-table=true
#安全距离,segment 缓存数量 默认 2
#cosid.segment.chain.safe-distance=10
#步数,每个 segment 里的 ID 数量,默认 10
cosid.segment.share.step=100 改完配置之后,就可以运行之前的单元测试案例获取分布式 ID 了。

@SpringBootTest@RunWith(SpringRunner.class)
public class DistIDTest {@Resourceprivate IdGeneratorProvider provider;
@Testpublic void getId(){for (int i = 0; i < 100; i++) {System.out.println(provider.getShare().generate());
}}}这次就会拿到从 1 到 100 的 ID。
执行完成后,会在 MySQL 中自动创建一张 cosid 表。里面记录了主键的 segment 信息。这次不用手动建表了。
从这个数据就能看到,cosid 表中的 name 字段就是表示一个命名空间。当应用来申请 ID 时,cosid 框架会把对应命名空间的一段 ID 一起分配给这个应用 last_max_id 就是记录上一次分配后的最大 ID。应用拿到这一批 ID 后,就可以自由分配。在全部使用完之前,不需要再次向 cosid 框架申请新的 ID 段,从了与主键生成服务的交互频率。这种模式就是典型的 segment 模式。
2、Segment 模式的优化方案 segment 模式其实并不复杂,但是要用好却并不容易。
segment 模式的基本思想就是很多应用从一个统一的第三方服务中获取 ID,但是不是每次获取一个 ID,而是每次获取一段 ID。然后在本地进行 ID 分发。
段 ID 分发完了,再去第三方服务中获取下一段 ID。
以最常用的数据库为例,一个典型的 segment 服务,可以用这样一张表来设计。
biz_tag 只是表示业务,用户服务和订单服务对应的都可能是一大批集群应用。 max_id 表示现在整个系统中已经分配的最大 ID。step 表示每个 segment 数量。
然后,当第一个订单应用过来申请 ID 时,就将 max_id 往前加一个 step,变成 2000。就表示这 2000 个 ID 就分配给这个订单应用了。然后这个订单应用就内存中随意去分配[0,2000)这些 ID。而第二个订单应用过来申请 ID 时,获得的就是[2000,4000)这一批订单应用。这样两个订单应用的 ID 可以保证不会这个策略中有一个最大的问题,就是申请 ID 是需要消耗网络资源的,在申请资源期间,应用就无法保持高可用了。所以有一种解决方案就是双 Buffer 写

应用既然可以接收一段 ID,那就可以再准备一个 Buffer,接收另一段 ID。当 Buffer1 的 ID 使用了 10%后,就发起线程去请求 ID,放到 Buffer2 中。等 Buffe 用完了,应用就直接从 Buffer2 中分配 ID。然后等 Buffer2 用到 10%,再同样反过来,申请一段新的 ID 放到 Buffer1 里。通过双 Buffer 的交替使用,保证在请 ID 期间,本地的 JVM 缓存中一直都是有 ID 可以分配的。
没错,这就是美团 Leaf 的完整方案。而其实很多互联网主流的分布式主键生成框架也都是用的这样一个思路,比如百度的 Uid。
他的好处比较明显。 ID 单调递增,在一定范围内,还可以保持严格递增。通过 JVM 本地进行号段缓存,性能也很高。
但是这种方案面向复杂业务时,其实也是有很多不足的。 CosID 框架就主要针对下面两个问题,对这种方案进行了改进。
1、强依赖于 DB。虽然 DB 是几乎所有项目的标配。但是,DB 是用来存储重要的业务数据的,将主键生成这样一个边缘服务强行依赖于 DB 是否合理呢?
其实你可以想象,DB 中最为核心的就是 max_id 和 step 两个字段而已。这两个字段其实可以往其他存储迁移。想用那个就用哪个不是更方便?这个想法要自己动手了,CosID 已经实现了。数据库、 Redis、Zookeeper、MongoDB,想用哪个就用哪个。程序员又找到了一个偷懒的理由。
2、延⻓本地缓存。不管你用哪种中间件来充当号段分配器,还是会有一个问题。如果号段分配器挂了,本地应用就只能通过本地缓存撑一段时间。这是可以考虑多缓存几个号段,延⻓一下支撑的时间呢?
CosId 也想到了,直接将双 Buffer 升级成了 SegmentChain。用一个链表的方式可以灵活缓存更多的号段。默认保留 10 个 Segment,并且在后面分配 ID 中,也尽量保证 SegmentChain 中的 Segment 个数不少于 10 个。这不就是为了保证本地缓存能够比较充足吗?
3、理解 SegmentChain 模式之前已经演示了基础的 Segment 模式的使用案例。 CosID 的 Segment 模式也是缓存一个单独的号段。一个号段用完了,就再去申请下一个号段。之前分在申请新号段的过程中,服务是短暂不可用的。

对于 Segment 号段,需要维护两个核心参数,NextMaxId 和 Step。一个表示已经分配的最大 ID,一个表示每次分配号段的步⻓。
SegmentChainID 号段链模式的基础思路之前也介绍过。用一个链表结构把多个 segment 串起来。整个设计图是这样的:
这种 SegmentChain 模式看起来挺眼花缭乱的,但是使用起来,相当的简单。就在之前的 Segment 案例的基础上,只要修改一个配置就可以了。
cosid.segment.mode=chain 其他的单元测试和配置都不需要再做任何额外的改动,运行后,就能同样拿到 100 个 ID。只不过,在执行完 DistIDApp 的单元测试后,cosid 表中的数据样:

为什么这个 last_max_id 更新成了 300。就是因为这次申请了两个 Segment 段,每个 segment 段的 ID⻓度是 100。 这两个参数也可以通过配置文件进行
#安全距离,segment 缓存数量 默认 2
cosid.segment.chain.safe-distance=10
#步数,每个 segment 里的 ID 数量。默认 10
cosid.segment.share.step=100 其中这个安全距离就可以简单理解为 SegmentChain 中 Segment 的个数。 CosID 会尽量保证 SegmentChain 能够保持这个安全距离。
4、Segment 机制源码解析 CosID 框架到底是怎么实现 Segment 模式的呢?同样可以从一个简单的单元测试案例入手@Resourceprivate SegmentId segmentId;
@Testpublic void getId(){for (int i = 0; i < 100; i++) {System.out.println(segmentId.generate());
}}也就是说,CosID 实现 Segment 模式的核心,就是通过往 Spring 的 IOC 容器当中注入的这个 SegmentID 实例。
那么接下来就来看看这个实例是怎么创建的。
//me.ahoo.cosid.spring.boot.starter.segment.SegmentIdBeanRegistrarprivate static SegmentId createSegment(SegmentIdProperties segmentIdProperties, SegmentIdProperties.IdDefinition idDefinition,IdSegmentDistributor idSegmentDistributor,PrefetchWorkerExecutorService prefetchWorkerExecutorService) {long ttl = MoreObjects.firstNonNull(idDefinition.getTtl(), segmentIdProperties.getTtl());
SegmentIdProperties.Mode mode = MoreObjects.firstNonNull(idDefinition.getMode(), segmentIdProperties.getMode());
//构建 SegmentID 实例。
SegmentId segmentId;
if (SegmentIdProperties.Mode.SEGMENT.equals(mode)) {segmentId = new DefaultSegmentId(ttl, idSegmentDistributor);
} else {SegmentIdProperties.Chain chain = MoreObjects.firstNonNull(idDefinition.getChain(), segmentIdProperties.getChain()
segmentId = new SegmentChainId(ttl, chain.getSafeDistance(), idSegmentDistributor, prefetchWorkerExecutorService);
}IdConverterDefinition converterDefinition = idDefinition.getConverter();
return new SegmentIdConverterDecorator(segmentId, converterDefinition).decorate();
}可以看到。在创建 SegmentID 实例时,会根据配置信息选择创建 DefaultSegmentId 还是 SegmentChainId。其中 DefaultSegmentId 就是单 Segment 模器,而 SegmentChainId 自然就是 SegmentChain 模式的分发器。
接下来,将这个 SegmentID 实例注入到 Spring 的 IOC 容器当中,同时保存到 idGeneratorProvider 中。
//me.ahoo.cosid.spring.boot.starter.segment.SegmentIdBeanRegistrarprivate void registerSegmentId(String name, SegmentId segmentId) {if (!idGeneratorProvider.get(name).isPresent()) {idGeneratorProvider.set(name, segmentId);
}String beanName = name + "SegmentId";
applicationContext.getBeanFactory().registerSingleton(beanName, segmentId);
}了解了这个工作机制后,再来看看 ID 是如何分发的。首先来看单 Segment 模式的实现方式。这个实现比较简单,就是获取号段之后本地分配,本地分配去重新申请。

//me.ahoo.cosid.segment.DefaultSegmentIdpublic long generate() {if (this.maxIdDistributor.getStep() == 1L) {GroupedAccessor.setIfNotNever(this.maxIdDistributor.group());
return this.maxIdDistributor.nextMaxId();
} else {long nextSeq;
if (this.segment.isAvailable()) {nextSeq = this.segment.incrementAndGet();
if (!this.segment.isOverflow(nextSeq)) {return nextSeq;
}}synchronized(this) {while(true) {if (this.segment.isAvailable()) {nextSeq = this.segment.incrementAndGet();
if (!this.segment.isOverflow(nextSeq)) {return nextSeq;
}}IdSegment nextIdSegment = this.maxIdDistributor.nextIdSegment(this.idSegmentTtl);
if (!this.maxIdDistributor.allowReset()) {this.segment.ensureNextIdSegment(nextIdSegment);
}this.segment = nextIdSegment;
}}}}接下来看看 SegmentChain 模式分发 ID 的实现方式:
//me.ahoo.cosid.segment.SegmentChainIdpublic long generate() {while(true) {//找到一个可用的 segme nt,分发 ID。
for(IdSegmentChain currentChain = this.headChain; currentChain != null; currentChain = currentChain.getNext()) {if (currentChain.isAvailable()) {long nextSeq = currentChain.incrementAndGet();
if (!currentChain.isOverflow(nextSeq)) {this.forward(currentChain);
return nextSeq;
}}}//找不到,链 表空了就添加一个 try {IdSegmentChain preIdSegmentChain = this.headChain;
if (preIdSegmentChain.trySetNext((preChain) -> {return this.generateNext(preChain, this.safeDistance);
})) {IdSegmentChain nextChain = preIdSegmentChain.getNext();
this.forward(nextChain);
if (log.isDebugEnabled()) {log.debug("Generate [{}] - headChain.version:[{}->{}].", new Object[]{this.maxIdDistributor.getNamespacedName(), preIdSegmentChain.getVersion(), nextChain.getVersion()});
}}} catch (NextIdSegmentExpiredException var4) {NextIdSegmentExpiredException nextIdSegmentExpiredException = var4;
if (log.isWarnEnabled()) {log.warn("Generate [{}] - gave up this next IdSegmentChain.", this.maxIdDistributor.getNamespacedName(),nextIdSegmentExpiredException);
}}//通过 hungr u 模式激发 prefetchService 去检查链表上的 segment 是否充足 this.prefetchJob.hungry();
}}CosID 在后台会启动一个线程池 PrefetchWorker,异步进行链表扩中。而具体进行链表扩充的方法,就是这个 prefetchJob 任务。

线程调度的逻辑这里就不多做梳理了,挺多挺复杂的。最终核心的扩充 Segment 的逻辑是这样的。
//me.ahoo.cosid.segment.SegmentChainId#PrefetchJobpublic class PrefetchJob implements AffinityJob {public void prefetch() {long wakeupTimeGap = Clock.SYSTEM.secondTime() - this.lastHungerTime;
boolean hunger = wakeupTimeGap < 5L;
//安全距离 int prePrefetchDistance = this.prefetchDistance;
if (hunger) {this.prefetchDistance = Math.min(Math.multiplyExact(this.prefetchDistance, 2), 100000000);
if (SegmentChainId.log.isInfoEnabled()) {SegmentChainId.log.info("Prefetch [{}] - Hunger, Safety distance expansion.[{}->{}]", new Object[]{SegmentChainId.this.maxIdDistributor.getNamespacedName(), prePrefetchDistance, this.prefetchDistance});
}} else {this.prefetchDistance = Math.max(Math.floorDiv(this.prefetchDistance, 2), SegmentChainId.this.safeDistance);
if (prePrefetchDistance > this.prefetchDistance && SegmentChainId.log.isInfoEnabled()) {SegmentChainId.log.info("Prefetch [{}] - Full, Safety distance shrinks.[{}->{}]", new Object[]{SegmentChainId.this.maxIdDistributor.getNamespacedName(), prePrefetchDistance, this.prefetchDistance});
}}IdSegmentChain availableHeadChain = SegmentChainId.this.headChain;
while(!availableHeadChain.getIdSegment().isAvailable()) {availableHeadChain = availableHeadChain.getNext();
if (availableHeadChain == null) {availableHeadChain = this.tailChain;
break;
}}SegmentChainId.this.forward(availableHeadChain);
//计算链表当中的 Segment 数量。
int headToTailGap = availableHeadChain.gap(this.tailChain, SegmentChainId.this.maxIdDistributor.getStep());
//计算链表数量与安全距离之间的差距 int safeGap = SegmentChainId.this.safeDistance - headToTailGap;
//链表中的 segment 个数已经不够了,但是不急着要。
if (safeGap <= 0 && !hunger) {if (SegmentChainId.log.isTraceEnabled()) {SegmentChainId.log.trace("Prefetch [{}] - safeGap is less than or equal to 0, and is not hungry headChain.version:[{}] - tailChain.version:[{}].", new Object[]{SegmentChainId.this.maxIdDistributor.getNamespacedName(),availableHeadChain.getVersion(), this.tailChain.getVersion()});
}} else {//需要添加几个 Segme ntint prefetchSegments = hunger ? this.prefetchDistance : safeGap;
//申请并添加 Segment 到 SegmentChain 链表当中。
this.appendChain(availableHeadChain, prefetchSegments);
}}}这里核心的 hungry 模式,其实就是用来保证数据库不可用时,也还是用自己的 segmentChain 先撑着。只要数据库可用,⻢上开始扩充 Segment。
5、基于 JDBC 的 ID 分发机制实现分析接下来在实际构建新的 segment 时,就需要注册一个 IdSegmentDistributor 接口,来计算新 Segment 的 maxId。这个接口的具体实现,就会交由与各种务集成的扩展组件去完成。例如基于 JDBC 的 ID 分发器提供的实现类是 JdbcIdSegmentDistributor。他的具体实现是这样的:

//me.ahoo.cosid.jdbc.JdbcIdSegmentDistributor@Overridepublic long nextMaxId(long step) {IdSegmentDistributor.ensureStep(step);
try (Connection connection = dataSource.getConnection()) {connection.setAutoCommit(false);
try (PreparedStatement accStatement = connection.prepareStatement(incrementMaxIdSql)) {accStatement.setLong(1, step);
accStatement.setString(2, getNamespacedName());
int affected = accStatement.executeUpdate();
if (affected == 0) {throw new SegmentNameMissingException(getNamespacedName());
}}long nextMaxId;
try (PreparedStatement fetchStatement = connection.prepareStatement(fetchMaxIdSql)) {fetchStatement.setString(1, getNamespacedName());
try (ResultSet resultSet = fetchStatement.executeQuery()) {if (!resultSet.next()) {throw new NotFoundMaxIdException(getNamespacedName());
}nextMaxId = resultSet.getLong(1);
}}connection.commit();
return nextMaxId;
} catch (SQLException sqlException) {if (log.isErrorEnabled()) {log.error(sqlException.getMessage(), sqlException);
}throw new CosIdException(sqlException.getMessage(), sqlException);
}}这段逻辑,如果你觉得挺麻烦,那么,其实只要看懂下面这两个 SQL 语句,就知道怎么回事了。
public static final String INCREMENT_MAX_ID_SQL= "update cosid set last_max_id=(last_max_id + ?),last_fetch_time=unix_timestamp() where name = ?;";
public static final String FETCH_MAX_ID_SQL= "select last_max_id from cosid where name = ?;";
四、章节总结在这个不短的过程当中,我们从一个简单的分库分表常⻅问题入手,又借着了解 ShardingSphere 新接入的 Cosid 框架的机会,把分布式 ID 这样一个不太问题详细梳理了一下。分布式主键生成策略,这或许是一个不起眼的技术路线,但是当他与具体业务结合时,却也是一个很重要的技术。
其实在分库分表这个小领域,早就有了美团 Leaf,百度 Uid 等等很多成熟的方案在前了。但是依然冒出了 CosID 这样一个后起之秀。可⻅深挖需求,融会才是技术的发展之道。而且 CosID 框架现在也在不断发展。现在也在不断的和更多其他业务场景融合,不断折腾出更大的水花。所以,今天这个章节,家一个学习新框架的思路,同时也是个大家一个新的发展方向。分布式主键这只是一个不起眼的小领域,尚且有这么大的发展空间。那么其他方向呢?
五、融会贯通:详细分析 ShardingSphere 新接入的 CosID 主键生成框架.md

