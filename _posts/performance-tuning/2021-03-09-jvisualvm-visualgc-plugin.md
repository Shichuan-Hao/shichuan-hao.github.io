---

title: "jvisualvm安装Visual GC插件"
description: "给 jdk 自带的 jvisualvm 安装 Visual GC 插件"
author: hsc
date: 2021-03-09 00:00:00 +0800
categories: ['Java 后端', '性能调优']
tags: ['性能调优', 'MySQL', 'JVM调优']
toc: true

---

给 jdk 自带的 jvisualvm 安装 Visual GC 插件,遇到 We're sorry the java.net site hasclosed(我们很抱歉 java.net 网站已经关闭)
1、找到新的更新地址 visualvm 新访问地址:https://visualvm.github.io/index.html 进入“Plugins”,找到对应自己 JDK 版本的更新地址

2、进入 jvisualvm 的插件管理"工具" - "插件"
在"设置"中修改 url 地址为刚才我们在 github 上找到的对应我们 JDK 版本的地址修改成功后,可用插件即可刷新出来 3、安装 VisualGC 插件 4、重启即可看到 VisualGC

一:整个区域分为三部分:spaces、graphs、histogram1,spaces 区域:代表虚拟机内存分布情况。从图中可以看出,虚拟机被分为 Perm、Old、Eden、S0、S1 注意:如果对每个区域基本概念不是很熟悉的可以先了解下 java 虚拟机运行时数据区这篇文字。
1.1)perm:英文叫做 Permanent Generation,我们称之为永久代。(根据深入 java 虚拟机作者说明,这里说法不是不是很正确,因为 hotspot 虚拟机的设计团队选择把 GC 分代收集扩展至此而已,正确的应该叫做方法区或者非堆)。
1.1.1)通过 VM Args:-XX:PermSize=128m -XX:MaxPermSize=256m 设置初始值与最大值

1.2)heap:java 堆(java heap)。它包括老年代(图中 Old 区域)和新生代(图中 Eden/S0/S1 三个统称新生代,分为 Eden 区和两个 Survivor 区域),他们默认是 8:1 分配内存 1.2.1)通过 VM Args:-xms512m -Xmx512m -XX:+HeapDumpOnOutofMemoryError-Xmn100m -XX:SurvivorRatio=8 设置初始堆内存、最大堆内存、内存异常打印 dump、新生代内存、新生代内存分配比例(8:1:1),因为 Heap 分为新生代跟老年代,所以 512M100M=412M,老年代就是 412M(初始内存跟最大内存最好相等,防止内存不够时扩充内存或者 Full GC,导致性能降低)
2,Graphs 区域:内存使用详细介绍 2.1)Compile Time(编译时间):6368compiles 表示编译总数,4.407s 表示编译累计时间。一个脉冲表示一次 JIT 编译,窄脉冲表示持续时间短,宽脉冲表示持续时间长。
2.2)Class Loader Time(类加载时间): 20869loaded 表示加载类数量, 139 unloaded 表示卸载的类数量,40.630s 表示类加载花费的时间 2.3)GC Time(GC Time):2392collections 表示垃圾收集的总次数,37.454s 表示垃圾收集花费的时间,last cause 表示最近垃圾收集的原因 2.4)Eden Space(Eden 区):括号内的 31.500M 表示最大容量,9.750M 表示当前容量,后面的 4.362M 表示当前使用情况,2313collections 表示垃圾收集次数,8.458s 表示垃圾收集花费时间 2.5)Survivor 0/Survivor 1(S0 和 S1 区):括号内的 3.938M 表示最大容量,1.188M 表示当前容量,之后的值是当前使用情况 2.6)Old Gen(老年代):括号内的 472.625M 表示最大容量,145.031M 表示当前容量,之后的 87.031 表示当前使用情况,79collections 表示垃圾收集次数 ,28.996s 表示垃圾收集花费时间 2.7)Perm Gen(永久代):括号内的 256.000M 表示最大容量,105.250M 表示当前容量,之后的 105.032M 表示当前使用情况 3,Histogram 区域:survivor 区域参数跟年龄柱状图

3.1)Tenuring Threshold:表示新生代年龄大于当前值则进入老年代 3.2)Max Tenuring Threshold:表示新生代最大年龄值。
3.3)Tenuring Threshold 与 Max Tenuring Threshold 区别:Max TenuringThreshold 是一个最大限定,所有的新生代年龄都不能超过当前值,而 TenuringThreshold 是个动态计算出来的临时值,一般情况与 Max Tenuring Threshold 相等,如果在 Suivivor 空间中,相同年龄所有对象大小的总和大于 Survivor 空间的一半,则年龄大于或者等于该年龄的对象就都可以直接进入老年代(如果计算出来年龄段是 5,则 TenuringThreshold=5,age>=5 的 Suivivor 对象都符合要求),它才是新生代是否进入老年代判断的依据。
3.4)Desired Survivor Size:Survivor 空间大小验证阙值(默认是 survivor 空间的一半),用于 Tenuring Threshold 判断对象是否提前进入老年代。
3.5)Current Survivor Size:当前 survivor 空间大小 3.6)histogram 柱状图:表示年龄段对象的存储柱状图 3.7)如果显示指定-XX:+UseParallelGC --新生代并行、老年代串行收集器 ,则 histogram 柱状图不支持当前收集器引用:
http://www.oracle.com/technetwork/java/visualgc-136680.htmlhttp://www.oracle.com/technetwork/java/javase/tech/vmoptions-jsp-140102.html
