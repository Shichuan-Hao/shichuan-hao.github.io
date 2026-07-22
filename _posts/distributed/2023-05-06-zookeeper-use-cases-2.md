---


title: "Zookeeper经典应用场景实战（二）"
description: "Zookeeper 分布式锁实战 1.1 什么是分布式锁在单体的应用开发场景中涉及并发同步的时候"
author: hsc
date: 2023-05-06 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Redis', 'Zookeeper']
toc: true


---

### 1. Zookeeper 分布式锁实战
#### 1.1 什么是分布式锁在单体的应用开发场景中涉及并发同步的时候,大家往往采用 Synchronized(同步)或者其他同一个 JVM 内 Lock 机制来解决多线程间的同步问题。在分布式集群工作的开发场景中,就需要一种更加高级的锁机制来处理跨机器的进程之间的数据同步问题,这种跨机器的锁就是分布式锁。
目前分布式锁,比较成熟、主流的方案:
(1)基于数据库的分布式锁。这种方案使用数据库的事务和锁机制来实现分布式锁。虽然在某些场景下可以实现简单的分布式锁,但由于数据库操作的性能相对较低,并且可能面临锁表的风险,所以一般不是首选方案。
(2)基于 Redis 的分布式锁。 Redis 分布式锁是一种常见且成熟的方案,适用于高并发、性能要求高且可靠性问题可以通过其他方案弥补的场景。 Redis 提供了高效的内存存储和原子操作,可以快速获取和释放锁。它在大规模的分布式系统中得到广泛应用。
(3)基于 ZooKeeper 的分布式锁。这种方案适用于对高可靠性和一致性要求较高,而并发量不是太高的场景。由于 ZooKeeper 的选举机制和强一致性保证,它可以处理更复杂的分布式锁场景,但相对于 Redis 而言,性能可能较低。
基于 Redis 实现分布式锁 https://vip.tulingxueyuan.cn/detail/p_602e53b3e4b035d3cdb8f856/61.2 基于数据库设计思路可以利用数据库的唯一索引来实现,唯一索引天然具有排他性

思考:基于数据库实现分布式锁存在什么问题?
1.3 基于 Zookeeper 设计思路一使用临时 znode 来表示获取锁的请求,创建 znode 成功的用户拿到锁。

思考:上述设计存在什么问题?
如果所有的锁请求者都 watch 锁持有者,当代表锁持有者的 znode 被删除以后,所有的锁请求者都会通知到,但是只有一个锁请求者能拿到锁。这就是羊群效应。
1.4 基于 Zookeeper 设计思路二使用临时有序 znode 来表示获取锁的请求,创建最小后缀数字 znode 的用户成功拿到锁。
公平锁的实现

在实际的开发中,如果需要使用到分布式锁,不建议去自己“重复造轮子”,而建议直接使用 Curator 客户端中的各种官方实现的分布式锁,例如其中的 InterProcessMutex 可重入锁。
1.5 Curator 可重入分布式锁工作流程 https://www.processon.com/view/link/5cadacd1e4b0375afbef4320

#### 1.6 总结优点:ZooKeeper 分布式锁(如 InterProcessMutex),具备高可用、可重入、阻塞锁特性,可解决失效死锁问题,使用起来也较为简单。
缺点:因为需要频繁的创建和删除节点,性能上不如 Redis。
在高性能、高并发的应用场景下,不建议使用 ZooKeeper 的分布式锁。而由于 ZooKeeper 的高可靠性,因此在并发量不是太高的应用场景中,还是推荐使用 ZooKeeper 的分布式锁。
2. 基于 Zookeeper 实现服务的注册与发现基于 ZooKeeper 本身的特性可以实现服务注册中心
2.1 设计思路

#### 2.2 Zookeeper 实现注册中心的优缺点优点:
高可用性:ZooKeeper 是一个高可用的分布式系统,可以通过配置多个服务器实例来提供容错能力。如果其中一个实例出现故障,其他实例仍然可以继续提供服务。
强一致性:ZooKeeper 保证了数据的强一致性。当一个更新操作完成时,所有的服务器都将具有相同的数据视图。这使得 ZooKeeper 非常适合作为服务注册中心,因为可以确保所有客户端看到的服务状态是一致的。
实时性:ZooKeeper 的监视器(Watcher)机制允许客户端监听节点的变化。当服务提供者的状态发生变化时(例如,上线或下线),客户端会实时收到通知。这使得服务消费者能够快速响应服务的变化,从而实现动态服务发现。
缺点:
性能限制:ZooKeeper 的性能可能不如一些专为服务注册中心设计的解决方案,如 nacos 或 Consul。尤其是在大量的读写操作或大规模集群的情况下,ZooKeeper 可能会遇到性能瓶颈。
2.3 整合 Spring Cloud Zookeeper 实现微服务注册中心 https://spring.io/projects/spring-cloud-zookeeper#learn 第一步:在父 pom 文件中指定 Spring Cloud 版本 1 <parent>2 <groupId>org.springframework.boot</groupId>3 <spanrtifactId>spring-boot-starter-parent</artifactId>

4 <version>2.3.2.RELEASE</version>5 <relativePath/> <!-- lookup parent from repository -->6 </parent>7 <properties>8 <java.version>1.8</java.version>9 <spring-cloud.version>Hoxton.SR8</spring-cloud.version>10 </properties>11 <dependencyManagement>12 <dependencies>13 <dependency>14 <groupId>org.springframework.cloud</groupId>15 <spanrtifactId>spring-cloud-dependencies</artifactId>16 <version>${spring-cloud.version}</version>17 <type>pom</type>18 <scope>import</scope>19 </dependency>20 </dependencies>21 </dependencyManagement>注意: springboot 和 springcloud 的版本兼容问题第二步:微服务 pom 文件中引入 Spring Cloud Zookeeper 注册中心依赖 1 <!-- zookeeper 服务注册与发现 -->2 <dependency>3 <groupId>org.springframework.cloud</groupId>4 <spanrtifactId>spring-cloud-starter-zookeeper-discovery</artifactId>5 <exclusions>6 <exclusion>7 <groupId>org.apache.zookeeper</groupId>8 <spanrtifactId>zookeeper</artifactId>9 </exclusion>10 </exclusions>11 </dependency>1213 <!-- zookeeper client -->14 <dependency>15 <groupId>org.apache.zookeeper</groupId>

16 <spanrtifactId>zookeeper</artifactId>17 <version>3.8.0</version>18 </dependency>注意: zookeeper 客户端依赖和 zookeeper sever 的版本兼容问题 Spring Cloud 整合 Zookeeper 注册中心核心源码入口: ZookeeperDiscoveryClientConfiguration 第三步: 微服务配置文件 application.yml 中配置 zookeeper 注册中心地址 1 spring:
2 cloud:
3 zookeeper:
4 connect-string: localhost:21815 discovery:
6 instance-host: 127.0.0.1 注册到 zookeeper 的服务实例元数据信息如下:
注意:如果 address 有问题,会出现找不到服务的情况,可以通过 instance-host 配置指定第四步:整合 feign 进行服务调用 1 @RequestMapping(value = "/findOrderByUserId/{id}")
2 public R findOrderByUserId(@PathVariable("id") Integer id) {3 log.info("根据 userId:"+id+"查询订单信息");
4 //feign 调用 5 R result = orderFeignService.findOrderByUserId(id);
6 return result;
7 }测试:http://localhost:8040/user/findOrderByUserId/1
