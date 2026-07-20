---
title: "VIP-04-Zookeeper选举Leader源码剖析(2)"
description: "为什么要看源码: 1、提升技术功底:学习源码里的优秀设计思想,比如一些疑难问题的解决思路,还有一些优秀的设计模式,整体提升自己的技术功底 2、深度掌握技术框架:源码看多了,对于一个新技术或框架的掌握速度会有大幅提升,看下框架demo大致就能知道底层的实现,技术框 架更新再快也不怕 3、快速定位线上问题:遇到线上问题,特别是框架源码里的问题(比如bug),能够快速定位,这就是相比其他没看过源码..."
author: hsc
date: 2020-09-10 00:00:00 +0800
categories: ['Java 后端', '分布式']
tags: ['分布式', 'Redis', 'Kafka', 'RocketMQ', 'Netty', 'ElasticSearch', 'ShardingSphere', '源码分析']
toc: true
---

> 本文整理自《四、分布式专题》课程笔记，共 4 页。

为什么要看源码:
1、提升技术功底:学习源码里的优秀设计思想,比如一些疑难问题的解决思路,还有一些优秀的设计模式,整体提升自己的技术功底
2、深度掌握技术框架:源码看多了,对于一个新技术或框架的掌握速度会有大幅提升,看下框架demo大致就能知道底层的实现,技术框
架更新再快也不怕
3、快速定位线上问题:遇到线上问题,特别是框架源码里的问题(比如bug),能够快速定位,这就是相比其他没看过源码的人的优势
4、对面试大有裨益:面试一线互联网公司对于框架技术一般都会问到源码级别的实现
5、知其然知其所以然:对技术有追求的人必做之事,使用了一个好的框架,很想知道底层是如何实现的
6、拥抱开源社区:参与到开源项目的研发,结识更多大牛,积累更多优质人脉
看源码方法:
1、先使用:先看官方文档快速掌握框架的基本使用
2、抓主线:找一个demo入手,顺藤摸瓜快速静态看一遍框架的主线源码,画出源码主流程图,切勿一开始就陷入源码的细枝末节,否则
会把自己绕晕,凭经验猜
3、画图做笔记:总结框架的一些核心功能点,从这些功能点入手深入到源码的细节,边看源码边画源码走向图,并对关键源码的理解做
笔记,把源码里的闪光点都记录下来,后续借鉴到工作项目中,理解能力强的可以直接看静态源码,也可以边看源码边debug源码执行过
程,观察一些关键变量的值
4、整合总结:所有功能点的源码都分析完后,回到主流程图再梳理一遍,争取把自己画的所有图都在脑袋里做一个整合
从源码启动zookeeper
zookeeper源码下载地址:
1 //选择分支3.5.8
2 https://github.com/apache/zookeeper.git
源码导入idea后,org.apache.zookeeper.Version类会报错,需要建一个辅助类
1 package org.apache.zookeeper.version;
2
3 public interface Info {
4 int MAJOR = 1;
5 int MINOR = 0;
6 int MICRO = 0;
7 String QUALIFIER = null;
8 int REVISION = ‐1;
9 String REVISION_HASH = "1";
10 String BUILD_DATE = "2020‐10‐15";

11 }
然后在根目录编译执行:
1 mvn clean install ‐DskipTests
开源项目找入口类一般都是从启动脚本去找,可以从bin目录下的zkServer.sh或zkServer.cmd里找到启动主类运行即可
1 org.apache.zookeeper.server.quorum.QuorumPeerMain
注意:
1、将conf文件夹里的zoo_sample.cfg文件复制一份改名为zoo.cfg,将zoo.cfg文件位置配置到启动参数里
2、启动之前需要先将zookeeper-server项目里pom.xml文件里依赖的包(除了jline)的scope为provided这一行全部注释掉
2、将conf文件夹里的log4j.properties文件复制一份到zookeeper-server项目的 \target\classes 目录下,这样项目启动时才会打印日志
用客户端命令连接源码启动的server:
1 bin/zkCli.sh ‐server 192.168.50.190:2181
从源码里运行客户端(org.apache.zookeeper.ZooKeeperMain),注意需要加入启动参数,见下图:
从源码启动zookeeper集群(参考视频讲解)
复制3个zoo.cfg文件,修改对应集群配置,并在data目录里分别建各自的myid文件填入机器id,并创建三个不同配置的启动节点,见下
图:

分别运行每个节点,集群启动完毕!
启动或leader宕机选举leader流程
leader选举多层队列架构
整个zookeeper选举底层可以分为选举应用层和消息传输层,应用层有自己的队列统一接收和发送选票,传输层也设计了自己的队列,但
是按发送的机器分了队列,避免给每台机器发送消息时相互影响,比如某台机器如果出问题发送不成功则不会影响对正常机器的消息发
送。

Leader选举源码流程图(务必跟着视频看)
1 文档:VIP‐04‐Zookeeper选举Leader源码剖析
2 链接:http://note.youdao.com/noteshare?id=dfa894cfaf0fde76405dd205dc1d1b47&sub=EC25858AA1E340BB942910297FBF5A5D
