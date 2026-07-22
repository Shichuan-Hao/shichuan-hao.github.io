---


title: "JVM对象创建与内存分配机制深度剖析"
description: "对象的创建对象创建的主要流程: 1.类加载检查虚拟机遇到一条 new 指令时,首先将去检查这个指令的参数是否能在常量池中定位到一个类的符号引用"
author: hsc
date: 2021-03-21 00:00:00 +0800
categories: ['Java 后端', '性能调优']
tags: ['性能调优', 'MySQL', 'MySQL优化', 'JVM调优', '索引优化']
toc: true


---

对象的创建对象创建的主要流程:
1.类加载检查虚拟机遇到一条 new 指令时,首先将去检查这个指令的参数是否能在常量池中定位到一个类的符号引用,并且检查这个符号引用代表的类是否已被加载、解析和初始化过。如果没有,那必须先执行相应的类加载过程。
new 指令对应到语言层面上讲是,new 关键词、对象克隆、对象序列化等。
2.分配内存在类加载检查通过后,接下来虚拟机将为新生对象分配内存。对象所需内存的大小在类 加载完成后便可完全确定,为对象分配空间的任务等同于把 一块确定大小的内存从 Java 堆中划分出来。
这个步骤有两个问题:
1.如何划分内存。
2.在并发情况下, 可能出现正在给对象 A 分配内存,指针还没来得及修改,对象 B 又同时使用了原来的指针来分配内存的情况。
划分内存的方法:
“指针碰撞”(Bump the Pointer)(默认用指针碰撞)
如果 Java 堆中内存是绝对规整的,所有用过的内存都放在一边,空闲的内存放在另一边,中间放着一个指针作为分界点的指示器,那所分配内存就仅仅是把那个指针向空闲空间那边挪动一段与对象大小相等的距离。
“空闲列表”(Free List)
如果 Java 堆中的内存并不是规整的,已使用的内存和空 闲的内存相互交错,那就没有办法简单地进行指针碰撞了,虚拟机就必须维护一个列表,记 录上哪些内存块是可用的,在分配的时候从列表中找到一块足够大的空间划分给对象实例,并更新列表上的记录解决并发问题的方法:
CAS(compare and swap)
虚拟机采用 CAS 配上失败重试的方式保证更新操作的原子性来对分配内存空间的动作进行同步处理。
本地线程分配缓冲(Thread Local Allocation Buffer,TLAB)

把内存分配的动作按照线程划分在不同的空间之中进行,即每个线程在 Java 堆中预先分配一小块内存。通过­XX:+/­UseTLAB 参数来设定虚拟机是否使用 TLAB(JVM 会默认开启­XX:+UseTLAB),­XX:TLABSize 指定 TLAB 大小。
3.初始化内存分配完成后,虚拟机需要将分配到的内存空间都初始化为零值(不包括对象头), 如果使用 TLAB,这一工作过程也可以提前至 TLAB 分配时进行。这一步操作保证了对象的实例字段在 Java 代码中可以不赋初始值就直接使用,程序能访问到这些字段的数据类型所对应的零值。
4.设置对象头初始化零值之后,虚拟机要对对象进行必要的设置,例如这个对象是哪个类的实例、如何才能找到类的元数据信息、对象的哈希码、对象的 GC 分代年龄等信息。这些信息存放在对象的对象头 Object Header 之中。
在 HotSpot 虚拟机中,对象在内存中存储的布局可以分为 3 块区域:对象头(Header)、 实例数据(Instance Data)
和对齐填充(Padding)。 HotSpot 虚拟机的对象头包括两部分信息,第一部分用于存储对象自身的运行时数据, 如哈希码(HashCode)、GC 分代年龄、锁状态标志、线程持有的锁、偏向线程 ID、偏向时 间戳等。对象头的另外一部分是类型指针,即对象指向它的类元数据的指针,虚拟机通过这个指针来确定这个对象是哪个类的实例。
对象头在 hotspot 的 C++源码里的注释如下:
1 Bit‐format of an object header (most significant first, big endian layout below):
2 //3 // 32 bits:
4 // ‐‐‐‐‐‐‐‐5 // hash:25 ‐‐‐‐‐‐‐‐‐‐‐‐>| age:4 biased_lock:1 lock:2 (normal object)
6 // JavaThread*:23 epoch:2 age:4 biased_lock:1 lock:2 (biased object)
7 // size:32 ‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐>| (CMS free block)
8 // PromotedObject*:29 ‐‐‐‐‐‐‐‐‐‐>| promo_bits:3 ‐‐‐‐‐>| (CMS promoted object)
9 //10 // 64 bits:
11 // ‐‐‐‐‐‐‐‐12 // unused:25 hash:31 ‐‐>| unused:1 age:4 biased_lock:1 lock:2 (normal object)
13 // JavaThread*:54 epoch:2 unused:1 age:4 biased_lock:1 lock:2 (biased object)
14 // PromotedObject*:61 ‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐>| promo_bits:3 ‐‐‐‐‐>| (CMS promoted object)
15 // size:64 ‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐>| (CMS free block)
16 //17 // unused:25 hash:31 ‐‐>| cms_free:1 age:4 biased_lock:1 lock:2 (COOPs && normal object)
18 // JavaThread*:54 epoch:2 cms_free:1 age:4 biased_lock:1 lock:2 (COOPs && biased object)
19 // narrowOop:32 unused:24 cms_free:1 unused:4 promo_bits:3 ‐‐‐‐‐>| (COOPs && CMS promoted object)
20 // unused:21 size:35 ‐‐>| cms_free:1 unused:7 ‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐‐>| (COOPs && CMS free block)
5.执行<init>方法执行<init>方法,即对象按照程序员的意愿进行初始化。对应到语言层面上讲,就是为属性赋值(注意,这与上面的赋零值不同,这是由程序员赋的值),和执行构造方法。
对象大小与指针压缩对象大小可以用 jol­core 包查看,引入依赖 1 <dependency>2 <groupId>org.openjdk.jol</groupId>3 <spanrtifactId>jol‐core</artifactId>

4 <version>0.9</version>5 </dependency>1 import org.openjdk.jol.info.ClassLayout;
23 /**4 * 计算对象大小 5 */6 public class JOLSample {78 public static void main(String[] args) {9 ClassLayout layout = ClassLayout.parseInstance(new Object());
10 System.out.println(layout.toPrintable());
1112 System.out.println();
13 ClassLayout layout1 = ClassLayout.parseInstance(new int[]{});
14 System.out.println(layout1.toPrintable());
1516 System.out.println();
17 ClassLayout layout2 = ClassLayout.parseInstance(new A());
18 System.out.println(layout2.toPrintable());
19 }2021 // ‐XX:+UseCompressedOops 默认开启的压缩所有指针 22 // ‐XX:+UseCompressedClassPointers 默认开启的压缩对象头里的类型指针 Klass Pointer23 // Oops : Ordinary Object Pointers24 public static class A {25 //8B mark word26 //4B Klass Pointer 如果关闭压缩‐XX:‐UseCompressedClassPointers 或‐XX:‐UseCompressedOops,则占用 8B27 int id; //4B28 String name; //4B 如果关闭压缩‐XX:‐UseCompressedOops,则占用 8B29 byte b; //1B30 Object o; //4B 如果关闭压缩‐XX:‐UseCompressedOops,则占用 8B31 }32 }333435 运行结果:
36 java.lang.Object object internals:
37 OFFSET SIZE TYPE DESCRIPTION VALUE38 0 4 (object header) 01 00 00 00 (00000001 00000000 00000000 00000000) (1) //mark word39 4 4 (object header) 00 00 00 00 (00000000 00000000 00000000 00000000) (0) //mark word40 8 4 (object header) e5 01 00 f8 (11100101 00000001 00000000 11111000) (‐134217243) //Klass Pointer41 12 4 (loss due to the next object alignment)
42 Instance size: 16 bytes43 Space losses: 0 bytes internal + 4 bytes external = 4 bytes total444546 [I object internals:
47 OFFSET SIZE TYPE DESCRIPTION VALUE48 0 4 (object header) 01 00 00 00 (00000001 00000000 00000000 00000000) (1)
49 4 4 (object header) 00 00 00 00 (00000000 00000000 00000000 00000000) (0)
50 8 4 (object header) 6d 01 00 f8 (01101101 00000001 00000000 11111000) (‐134217363)
51 12 4 (object header) 00 00 00 00 (00000000 00000000 00000000 00000000) (0)
52 16 0 int [I.<elements> N/A53 Instance size: 16 bytes54 Space losses: 0 bytes internal + 0 bytes external = 0 bytes total555657 com.tuling.jvm.JOLSample$A object internals:
58 OFFSET SIZE TYPE DESCRIPTION VALUE

59 0 4 (object header) 01 00 00 00 (00000001 00000000 00000000 00000000) (1)
60 4 4 (object header) 00 00 00 00 (00000000 00000000 00000000 00000000) (0)
61 8 4 (object header) 61 cc 00 f8 (01100001 11001100 00000000 11111000) (‐134165407)
62 12 4 int A.id 063 16 1 byte A.b 064 17 3 (alignment/padding gap)
65 20 4 java.lang.String A.name null66 24 4 java.lang.Object A.o null67 28 4 (loss due to the next object alignment)
68 Instance size: 32 bytes69 Space losses: 3 bytes internal + 4 bytes external = 7 bytes total 什么是 java 对象的指针压缩?
1.jdk1.6 update14 开始,在 64bit 操作系统中,JVM 支持指针压缩 2.jvm 配置参数:UseCompressedOops,compressed­­压缩、 oop(ordinary object pointer)­­对象指针 3.启用指针压缩:­XX:+UseCompressedOops(默认开启),禁止指针压缩:­XX:­UseCompressedOops 为什么要进行指针压缩?
1.在 64 位平台的 HotSpot 中使用 32 位指针,内存使用会多出 1.5 倍左右,使用较大指针在主内存和缓存之间移动数据,占用较大宽带,同时 GC 也会承受较大压力 2.为了减少 64 位平台下内存的消耗,启用指针压缩功能 3.在 jvm 中,32 位地址最大支持 4G 内存(2 的 32 次方),可以通过对对象指针的压缩编码、解码方式进行优化,使得 jvm 只用 32 位地址就可以支持更大的内存配置(小于等于 32G)
4.堆内存小于 4G 时,不需要启用指针压缩,jvm 会直接去除高 32 位地址,即使用低虚拟地址空间 5.堆内存大于 32G 时,压缩指针会失效,会强制使用 64 位(即 8 字节)来对 java 对象寻址,这就会出现 1 的问题,所以堆内存不要大于 32G 为好对象内存分配对象内存分配流程图对象栈上分配我们通过 JVM 内存分配可以知道 JAVA 中的对象都是在堆上进行分配,当对象没有被引用的时候,需要依靠 GC 进行回收内存,如果对象数量较多的时候,会给 GC 带来较大压力,也间接影响了应用的性能。为了减少临时对象在堆内分配的数

量,JVM 通过逃逸分析确定该对象不会被外部访问。如果不会逃逸可以将该对象在栈上分配内存,这样该对象所占用的内存空间就可以随栈帧出栈而销毁,就减轻了垃圾回收的压力。
对象逃逸分析:就是分析对象动态作用域,当一个对象在方法中被定义后,它可能被外部方法所引用,例如作为调用参数传递到其他地方中。
1 public User test1() {2 User user = new User();
3 user.setId(1);
4 user.setName("zhuge");
5 //TODO 保存到数据库 6 return user;
7 }89 public void test2() {10 User user = new User();
11 user.setId(1);
12 user.setName("zhuge");
13 //TODO 保存到数据库 14 }很显然 test1 方法中的 user 对象被返回了,这个对象的作用域范围不确定,test2 方法中的 user 对象我们可以确定当方法结束这个对象就可以认为是无效对象了,对于这样的对象我们其实可以将其分配在栈内存里,让其在方法结束时跟随栈内存一起被回收掉。
JVM 对于这种情况可以通过开启逃逸分析参数(-XX:+DoEscapeAnalysis)来优化对象内存分配位置,使其通过标量替换优先分配在栈上(栈上分配),JDK7 之后默认开启逃逸分析,如果要关闭使用参数(-XX:-DoEscapeAnalysis)
标量替换:通过逃逸分析确定该对象不会被外部访问,并且对象可以被进一步分解时,JVM 不会创建该对象,而是将该对象成员变量分解若干个被这个方法使用的成员变量所代替,这些代替的成员变量在栈帧或寄存器上分配空间,这样就不会因为没有一大块连续空间导致对象内存不够分配。开启标量替换参数(-XX:+EliminateAllocations),JDK7 之后默认开启。
标量与聚合量:标量即不可被进一步分解的量,而 JAVA 的基本数据类型就是标量(如:int,long 等基本数据类型以及 reference 类型等),标量的对立就是可以被进一步分解的量,而这种量称之为聚合量。而在 JAVA 中对象就是可以被进一步分解的聚合量。
栈上分配示例:
1 /**2 * 栈上分配,标量替换 3 * 代码调用了 1 亿次 alloc(),如果是分配到堆上,大概需要 1GB 以上堆空间,如果堆空间小于该值,必然会触发 GC。
4 *5 * 使用如下参数不会发生 GC6 * ‐Xmx15m ‐Xms15m ‐XX:+DoEscapeAnalysis ‐XX:+PrintGC ‐XX:+EliminateAllocations7 * 使用如下参数都会发生大量 GC8 * ‐Xmx15m ‐Xms15m ‐XX:‐DoEscapeAnalysis ‐XX:+PrintGC ‐XX:+EliminateAllocations9 * ‐Xmx15m ‐Xms15m ‐XX:+DoEscapeAnalysis ‐XX:+PrintGC ‐XX:‐EliminateAllocations10 */11 public class AllotOnStack {1213 public static void main(String[] args) {14 long start = System.currentTimeMillis();
15 for (int i = 0; i < 100000000; i++) {16 alloc();
17 }18 long end = System.currentTimeMillis();
19 System.out.println(end ‐ start);
20 }2122 private static void alloc() {23 User user = new User();
24 user.setId(1);
25 user.setName("zhuge");

26 }27 }结论:栈上分配依赖于逃逸分析和标量替换对象在 Eden 区分配大多数情况下,对象在新生代中 Eden 区分配。当 Eden 区没有足够空间进行分配时,虚拟机将发起一次 Minor GC。我们来进行实际测试一下。
在测试之前我们先来看看 Minor GC 和 Full GC 有什么不同呢?
Minor GC/Young GC:指发生新生代的的垃圾收集动作,Minor GC 非常频繁,回收速度一般也比较快。
Major GC/Full GC:一般会回收老年代 ,年轻代,方法区的垃圾,Major GC 的速度一般会比 Minor GC 的慢 10 倍以上。
Eden 与 Survivor 区默认 8:1:1 大量的对象被分配在 eden 区,eden 区满了后会触发 minor gc,可能会有 99%以上的对象成为垃圾被回收掉,剩余存活的对象会被挪到为空的那块 survivor 区,下一次 eden 区满了后又会触发 minor gc,把 eden 区和 survivor 区垃圾对象回收,把剩余存活的对象一次性挪动到另外一块为空的 survivor 区,因为新生代的对象都是朝生夕死的,存活时间很短,所以 JVM 默认的 8:1:1 的比例是很合适的,让 eden 区尽量的大,survivor 区够用即可,JVM 默认有这个参数-XX:+UseAdaptiveSizePolicy(默认开启),会导致这个 8:1:1 比例自动变化,如果不想这个比例有变化可以设置参数-XX:-UseAdaptiveSizePolicy 示例:
1 //添加运行 JVM 参数: ‐XX:+PrintGCDetails2 public class GCTest {3 public static void main(String[] args) throws InterruptedException {4 byte[] allocation1, allocation2/*, allocation3, allocation4, allocation5, allocation6*/;
5 allocation1 = new byte[60000*1024];
67 //allocation2 = new byte[8000*1024];
89 /*allocation3 = new byte[1000*1024];
10 allocation4 = new byte[1000*1024];
11 allocation5 = new byte[1000*1024];
12 allocation6 = new byte[1000*1024];*/13 }14 }1516 运行结果:
17 Heap18 PSYoungGen total 76288K, used 65536K [0x000000076b400000, 0x0000000770900000, 0x00000007c0000000)
19 eden space 65536K, 100% used [0x000000076b400000,0x000000076f400000,0x000000076f400000)
20 from space 10752K, 0% used [0x000000076fe80000,0x000000076fe80000,0x0000000770900000)
21 to space 10752K, 0% used [0x000000076f400000,0x000000076f400000,0x000000076fe80000)
22 ParOldGen total 175104K, used 0K [0x00000006c1c00000, 0x00000006cc700000, 0x000000076b400000)
23 object space 175104K, 0% used [0x00000006c1c00000,0x00000006c1c00000,0x00000006cc700000)
24 Metaspace used 3342K, capacity 4496K, committed 4864K, reserved 1056768K25 class space used 361K, capacity 388K, committed 512K, reserved 1048576K 我们可以看出 eden 区内存几乎已经被分配完全(即使程序什么也不做,新生代也会使用至少几 M 内存)。假如我们再为 allocation2 分配内存会出现什么情况呢?
1 //添加运行 JVM 参数: ‐XX:+PrintGCDetails2 public class GCTest {3 public static void main(String[] args) throws InterruptedException {4 byte[] allocation1, allocation2/*, allocation3, allocation4, allocation5, allocation6*/;
5 allocation1 = new byte[60000*1024];
7 allocation2 = new byte[8000*1024];
89 /*allocation3 = new byte[1000*1024];
10 allocation4 = new byte[1000*1024];
11 allocation5 = new byte[1000*1024];
12 allocation6 = new byte[1000*1024];*/13 }14 }1516 运行结果:
17 [GC (Allocation Failure) [PSYoungGen: 65253K‐>936K(76288K)] 65253K‐>60944K(251392K), 0.0279083 secs] [Times:
user=0.13 sys=0.02, real=0.03 secs]18 Heap19 PSYoungGen total 76288K, used 9591K [0x000000076b400000, 0x0000000774900000, 0x00000007c0000000)
20 eden space 65536K, 13% used [0x000000076b400000,0x000000076bc73ef8,0x000000076f400000)
21 from space 10752K, 8% used [0x000000076f400000,0x000000076f4ea020,0x000000076fe80000)
22 to space 10752K, 0% used [0x0000000773e80000,0x0000000773e80000,0x0000000774900000)
23 ParOldGen total 175104K, used 60008K [0x00000006c1c00000, 0x00000006cc700000, 0x000000076b400000)
24 object space 175104K, 34% used [0x00000006c1c00000,0x00000006c569a010,0x00000006cc700000)
25 Metaspace used 3342K, capacity 4496K, committed 4864K, reserved 1056768K26 class space used 361K, capacity 388K, committed 512K, reserved 1048576K 简单解释一下为什么会出现这种情况: 因为给 allocation2 分配内存的时候 eden 区内存几乎已经被分配完了,我们刚刚讲了当 Eden 区没有足够空间进行分配时,虚拟机将发起一次 Minor GC,GC 期间虚拟机又发现 allocation1 无法存入 Survior 空间,所以只好把新生代的对象提前转移到老年代中去,老年代上的空间足够存放 allocation1,所以不会出现 Full GC。执行 Minor GC 后,后面分配的对象如果能够存在 eden 区的话,还是会在 eden 区分配内存。可以执行如下代码验证:
1 public class GCTest {2 public static void main(String[] args) throws InterruptedException {3 byte[] allocation1, allocation2, allocation3, allocation4, allocation5, allocation6;
4 allocation1 = new byte[60000*1024];
56 allocation2 = new byte[8000*1024];
78 allocation3 = new byte[1000*1024];
9 allocation4 = new byte[1000*1024];
10 allocation5 = new byte[1000*1024];
11 allocation6 = new byte[1000*1024];
12 }13 }1415 运行结果:
16 [GC (Allocation Failure) [PSYoungGen: 65253K‐>952K(76288K)] 65253K‐>60960K(251392K), 0.0311467 secs] [Times:
user=0.08 sys=0.02, real=0.03 secs]17 Heap18 PSYoungGen total 76288K, used 13878K [0x000000076b400000, 0x0000000774900000, 0x00000007c0000000)
19 eden space 65536K, 19% used [0x000000076b400000,0x000000076c09fb68,0x000000076f400000)
20 from space 10752K, 8% used [0x000000076f400000,0x000000076f4ee030,0x000000076fe80000)
21 to space 10752K, 0% used [0x0000000773e80000,0x0000000773e80000,0x0000000774900000)
22 ParOldGen total 175104K, used 60008K [0x00000006c1c00000, 0x00000006cc700000, 0x000000076b400000)
23 object space 175104K, 34% used [0x00000006c1c00000,0x00000006c569a010,0x00000006cc700000)
24 Metaspace used 3343K, capacity 4496K, committed 4864K, reserved 1056768K25 class space used 361K, capacity 388K, committed 512K, reserved 1048576K 大对象直接进入老年代大对象就是需要大量连续内存空间的对象(比如:字符串、数组)。JVM 参数 -XX:PretenureSizeThreshold 可以设置大对象的大小,如果对象超过设置大小会直接进入老年代,不会进入年轻代,这个参数只在 Serial 和 ParNew 两个收集器下有效。

比如设置 JVM 参数:-XX:PretenureSizeThreshold=1000000 (单位是字节) -XX:+UseSerialGC ,再执行下上面的第一个程序会发现大对象直接进了老年代为什么要这样呢?
为了避免为大对象分配内存时的复制操作而降低效率。
长期存活的对象将进入老年代既然虚拟机采用了分代收集的思想来管理内存,那么内存回收时就必须能识别哪些对象应放在新生代,哪些对象应放在老年代中。为了做到这一点,虚拟机给每个对象一个对象年龄(Age)计数器。
如果对象在 Eden 出生并经过第一次 Minor GC 后仍然能够存活,并且能被 Survivor 容纳的话,将被移动到 Survivor 空间中,并将对象年龄设为 1。对象在 Survivor 中每熬过一次 MinorGC,年龄就增加 1 岁,当它的年龄增加到一定程度(默认为 15 岁,CMS 收集器默认 6 岁,不同的垃圾收集器会略微有点不同),就会被晋升到老年代中。对象晋升到老年代的年龄阈值,可以通过参数 -XX:MaxTenuringThreshold 来设置。
对象动态年龄判断当前放对象的 Survivor 区域里(其中一块区域,放对象的那块 s 区),一批对象的总大小大于这块 Survivor 区域内存大小的 50%(-XX:TargetSurvivorRatio 可以指定),那么此时大于等于这批对象年龄最大值的对象,就可以直接进入老年代了,例如 Survivor 区域里现在有一批对象,年龄 1+年龄 2+年龄 n 的多个年龄对象总和超过了 Survivor 区域的 50%,此时就会把年龄 n(含)以上的对象都放入老年代。这个规则其实是希望那些可能是长期存活的对象,尽早进入老年代。对象动态年龄判断机制一般是在 minor gc 之后触发的。
老年代空间分配担保机制年轻代每次 minor gc 之前 JVM 都会计算下老年代剩余可用空间如果这个可用空间小于年轻代里现有的所有对象大小之和(包括垃圾对象)
就会看一个“-XX:-HandlePromotionFailure”(jdk1.8 默认就设置了)的参数是否设置了如果有这个参数,就会看看老年代的可用内存大小,是否大于之前每一次 minor gc 后进入老年代的对象的平均大小。
如果上一步结果是小于或者之前说的参数没有设置,那么就会触发一次 Full gc,对老年代和年轻代一起回收一次垃圾,如果回收完还是没有足够空间存放新的对象就会发生"OOM"
当然,如果 minor gc 之后剩余存活的需要挪动到老年代的对象大小还是大于老年代可用空间,那么也会触发 full gc,fullgc 完之后如果还是没有空间放 minor gc 之后的存活对象,则也会发生“OOM”

对象内存回收堆中几乎放着所有的对象实例,对堆垃圾回收前的第一步就是要判断哪些对象已经死亡(即不能再被任何途径使用的对象)。
引用计数法给对象中添加一个引用计数器,每当有一个地方引用它,计数器就加 1;当引用失效,计数器就减 1;任何时候计数器为 0 的对象就是不可能再被使用的。
这个方法实现简单,效率高,但是目前主流的虚拟机中并没有选择这个算法来管理内存,其最主要的原因是它很难解决对象之间相互循环引用的问题。 所谓对象之间的相互引用问题,如下面代码所示:除了对象 objA 和 objB 相互引用着对方之外,这两个对象之间再无任何引用。但是他们因为互相引用对方,导致它们的引用计数器都不为 0,于是引用计数算法无法通知 GC 回收器回收他们。
1 public class ReferenceCountingGc {2 Object instance = null;
34 public static void main(String[] args) {5 ReferenceCountingGc objA = new ReferenceCountingGc();
6 ReferenceCountingGc objB = new ReferenceCountingGc();
7 objA.instance = objB;
8 objB.instance = objA;
9 objA = null;
10 objB = null;
11 }12 }可达性分析算法

将“GC Roots” 对象作为起点,从这些节点开始向下搜索引用的对象,找到的对象都标记为非垃圾对象,其余未标记的对象都是垃圾对象 GC Roots 根节点:线程栈的本地变量、静态变量、本地方法栈的变量等等常见引用类型 java 的引用类型一般分为四种:强引用、软引用、弱引用、虚引用强引用:普通的变量引用 1 public static User user = new User();
软引用:将对象用 SoftReference 软引用类型的对象包裹,正常情况不会被回收,但是 GC 做完后发现释放不出空间存放新的对象,则会把这些软引用的对象回收掉。软引用可用来实现内存敏感的高速缓存。
1 public static SoftReference<User> user = new SoftReference<User>(new User());
软引用在实际中有重要的应用,例如浏览器的后退按钮。按后退时,这个后退时显示的网页内容是重新进行请求还是从缓存中取出呢?这就要看具体的实现策略了。
(1)如果一个网页在浏览结束时就进行内容的回收,则按后退查看前面浏览过的页面时,需要重新构建(2)如果将浏览过的网页存储到内存中会造成内存的大量浪费,甚至会造成内存溢出弱引用:将对象用 WeakReference 软引用类型的对象包裹,弱引用跟没引用差不多,GC 会直接回收掉,很少用 1 public static WeakReference<User> user = new WeakReference<User>(new User());
虚引用:虚引用也称为幽灵引用或者幻影引用,它是最弱的一种引用关系,几乎不用 finalize()方法最终判定对象是否存活即使在可达性分析算法中不可达的对象,也并非是“非死不可”的,这时候它们暂时处于“缓刑”阶段,要真正宣告一个对象死亡,至少要经历再次标记过程。
标记的前提是对象在进行可达性分析后发现没有与 GC Roots 相连接的引用链。
1. 第一次标记并进行一次筛选。
筛选的条件是此对象是否有必要执行 finalize()方法。
当对象没有覆盖 finalize 方法,对象将直接被回收。
2. 第二次标记如果这个对象覆盖了 finalize 方法,finalize 方法是对象脱逃死亡命运的最后一次机会,如果对象要在 finalize()中成功拯救自己,只要重新与引用链上的任何的一个对象建立关联即可,譬如把自己赋值给某个类变量或对象的成员变量,那在第二次标记时它将移除出“即将回收”的集合。如果对象这时候还没逃脱,那基本上它就真的被回收了。
注意:一个对象的 finalize()方法只会被执行一次,也就是说通过调用 finalize 方法自我救命的机会就一次。
示例代码:

1 public class OOMTest {23 public static void main(String[] args) {4 List<Object> list = new ArrayList<>();
5 int i = 0;
6 int j = 0;
7 while (true) {8 list.add(new User(i++, UUID.randomUUID().toString()));
9 new User(j‐‐, UUID.randomUUID().toString());
10 }11 }12 }如何判断一个类是无用的类方法区主要回收的是无用的类,那么如何判断一个类是无用的类的呢?
类需要同时满足下面 3 个条件才能算是 “无用的类” :
该类所有的实例都已经被回收,也就是 Java 堆中不存在该类的任何实例。
加载该类的 ClassLoader 已经被回收。
该类对应的 java.lang.Class 对象没有在任何地方被引用,无法在任何地方通过反射访问该类的方法。
id=0e14c4e1fa9ee6b3fda6da53fd20a04d&sub=1E31F1D71A644ECE84476D66B1E43FE6
