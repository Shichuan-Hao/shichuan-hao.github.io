---


title: "Zookeeper选举Leader源码剖析(2)"
description: "为什么要看源码: 1、提升技术功底:学习源码里的优秀设计思想,比如一些疑难问题的解决思路,还有一些优秀的设计模式,整体提升自己的技术功底 2、深度掌握技术框架:源码看多了"
author: hsc
date: 2023-06-20 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', '中间件', 'Zookeeper']
toc: true


---

为什么要看源码:
1、提升技术功底:学习源码里的优秀设计思想,比如一些疑难问题的解决思路,还有一些优秀的设计模式,整体提升自己的技术功底 2、深度掌握技术框架:源码看多了,对于一个新技术或框架的掌握速度会有大幅提升,看下框架 demo 大致就能知道底层的实现,技术框架更新再快也不怕 3、快速定位线上问题:遇到线上问题,特别是框架源码里的问题(比如 bug),能够快速定位,这就是相比其他没看过源码的人的优势 4、对面试大有裨益:面试一线互联网公司对于框架技术一般都会问到源码级别的实现 5、知其然知其所以然:对技术有追求的人必做之事,使用了一个好的框架,很想知道底层是如何实现的 6、拥抱开源社区:参与到开源项目的研发,结识更多大牛,积累更多优质人脉看源码方法:
1、先使用:先看官方文档快速掌握框架的基本使用 2、抓主线:找一个 demo 入手,顺藤摸瓜快速静态看一遍框架的主线源码,画出源码主流程图,切勿一开始就陷入源码的细枝末节,否则会把自己绕晕,凭经验猜 3、画图做笔记:总结框架的一些核心功能点,从这些功能点入手深入到源码的细节,边看源码边画源码走向图,并对关键源码的理解做笔记,把源码里的闪光点都记录下来,后续借鉴到工作项目中,理解能力强的可以直接看静态源码,也可以边看源码边 debug 源码执行过程,观察一些关键变量的值 4、整合总结:所有功能点的源码都分析完后,回到主流程图再梳理一遍,争取把自己画的所有图都在脑袋里做一个整合从源码启动 zookeeperzookeeper 源码下载地址:
1 //选择分支 3.5.82 https://github.com/apache/zookeeper.git 源码导入 idea 后,org.apache.zookeeper.Version 类会报错,需要建一个辅助类 1 package org.apache.zookeeper.version;
23 public interface Info {4 int MAJOR = 1;
5 int MINOR = 0;
6 int MICRO = 0;
7 String QUALIFIER = null;
8 int REVISION = ‐1;
9 String REVISION_HASH = "1";
10 String BUILD_DATE = "2020‐10‐15";

11 }然后在根目录编译执行:
1 mvn clean install ‐DskipTests 开源项目找入口类一般都是从启动脚本去找,可以从 bin 目录下的 zkServer.sh 或 zkServer.cmd 里找到启动主类运行即可 1 org.apache.zookeeper.server.quorum.QuorumPeerMain 注意:
1、将 conf 文件夹里的 zoo_sample.cfg 文件复制一份改名为 zoo.cfg,将 zoo.cfg 文件位置配置到启动参数里 2、启动之前需要先将 zookeeper-server 项目里 pom.xml 文件里依赖的包(除了 jline)的 scope 为 provided 这一行全部注释掉 2、将 conf 文件夹里的 log4j.properties 文件复制一份到 zookeeper-server 项目的 \target\classes 目录下,这样项目启动时才会打印日志用客户端命令连接源码启动的 server:
1 bin/zkCli.sh ‐server 192.168.50.190:2181 从源码里运行客户端(org.apache.zookeeper.ZooKeeperMain),注意需要加入启动参数,见下图:
从源码启动 zookeeper 集群(参考视频讲解)
复制 3 个 zoo.cfg 文件,修改对应集群配置,并在 data 目录里分别建各自的 myid 文件填入机器 id,并创建三个不同配置的启动节点,见下图:

分别运行每个节点,集群启动完毕!
启动或 leader 宕机选举 leader 流程 leader 选举多层队列架构整个 zookeeper 选举底层可以分为选举应用层和消息传输层,应用层有自己的队列统一接收和发送选票,传输层也设计了自己的队列,但是按发送的机器分了队列,避免给每台机器发送消息时相互影响,比如某台机器如果出问题发送不成功则不会影响对正常机器的消息发送。

Leader 选举源码流程图(务必跟着视频看)
