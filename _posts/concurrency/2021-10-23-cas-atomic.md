---

title: "深入理解CASandAtomic原子操作类详解"
description: "CAS 介绍什么是 CASCAS(Compare And Swap,比较与交换),是非阻塞同步的实现原理,它是 CPU 硬件层面的一种指令"
    主讲老师:Fox 有道笔记: https://note.youdao.com/s/AJECfbdA 1.CAS介绍 什么是 CAS CAS(Compare And Swap,比较与交换),是非阻塞同步的实现原理,它是CPU硬件层面的一种指 令,从CPU层面能保证"比较与交换"两个操作的原子性。CAS指令操作包括三个参数:内存值(内存地 址值)V、预期值E、新值N,当CAS指令执行时,当且仅当...
author: hsc
date: 2021-10-23 00:00:00 +0800
categories: ['Java 后端', '并发编程']
tags: ['并发编程', 'JUC', 'AQS', 'synchronized', 'volatile', 'CAS']
toc: true

---

1.CAS 介绍什么是 CASCAS(Compare And Swap,比较与交换),是非阻塞同步的实现原理,它是 CPU 硬件层面的一种指令,从 CPU 层面能保证"比较与交换"两个操作的原子性。 CAS 指令操作包括三个参数:内存值(内存地址值)V、预期值 E、新值 N,当 CAS 指令执行时,当且仅当预期值 E 和内存值 V 相同时,才更新内存值为 N,否则就不执行更新,无论更新与否都会返回否会返回旧的内存值 V,上述的处理过程是一个原子操作。
用 Java 代码等效实现一下 CAS 的执行过程:

1 public class CASDemo {23 // 内存中当前的值 4 private volatile int ramAddress;
56 /**7 * @param expectedValue 期望值 8 * @return newValue 更新的值 9 **/10 public synchronized int compareAndSwap(int expectedValue, int newValue) {11 //TODO 模拟直接从内存地址读取到内存中的值 12 int oldRamAddress = accessMemory(ramAddress);
13 //内存中的值和期望的值进行比较 14 if (oldRamAddress == expectedValue) {15 ramAddress = newValue;
16 }17 return oldRamAddress;
18 }1920 private int accessMemory(int ramAddress) {21 //TODO 模拟直接从内存地址读取到内存中的值 22 return ramAddress;
23 }2425 }以上伪代码描述了一个由比较和赋值两阶段组成的复合操作,CAS 可以看作是它们合并后的整体——一个不可分割的原子操作,并且其原子性是直接在硬件层面得到保障的。
CAS 是一种无锁算法,在不使用锁(没有线程被阻塞)的情况下实现多线程之间的变量同步。 CAS 可以看做是乐观锁(对比数据库的悲观、乐观锁)的一种实现方式,Java 原子类中的递增操作就通过 CAS 自旋实现的。
CAS 使用在 Java 中,CAS 操作是由 Unsafe 类提供支持的,该类定义了三种针对不同类型变量的 CAS 操作,如图

它们都是 native 方法,由 Java 虚拟机提供具体实现,这意味着不同的 Java 虚拟机对它们的实现可能会略有不同。
Unsafe 是位于 sun.misc 包下的一个类,主要提供一些用于执行低级别、不安全操作的方法,如直接访问系统内存资源、自主管理内存资源等,这些方法在提升 Java 运行效率、增强 Java 语言底层资源操作能力方面起到了很大的作用。但由于 Unsafe 类使 Java 语言拥有了类似 C 语言指针一样操作内存空间的能力,这无疑也增加了程序发生相关指针问题的风险。在程序中过度、不正确使用 Unsafe 类会使得程序出错的概率变大,使得 Java 这种安全的语言变得不再“安全”,因此对 Unsafe 的使用一定要慎重。
以 compareAndSwapInt 为例,Unsafe 的 compareAndSwapInt 方法接收 4 个参数,分别是:对象实例、内存偏移量、字段期望值、字段新值。该方法会针对指定对象实例中的相应偏移量的字段执行 CAS 操作。

1 public class CASTest {23 public static void main(String[] args) {4 Entity entity = new Entity();
56 Unsafe unsafe = UnsafeFactory.getUnsafe();
78 long offset = UnsafeFactory.getFieldOffset(unsafe, Entity.class, "x");
910 boolean successful;
1112 // 4 个参数分别是:对象实例、字段的内存偏移量、字段期望值、字段新值 13 successful = unsafe.compareAndSwapInt(entity, offset, 0, 3);
14 System.out.println(successful + "\t" + entity.x);
1516 successful = unsafe.compareAndSwapInt(entity, offset, 3, 5);
17 System.out.println(successful + "\t" + entity.x);
1819 successful = unsafe.compareAndSwapInt(entity, offset, 3, 8);
20 System.out.println(successful + "\t" + entity.x);
21 }22 }2324 public class UnsafeFactory {2526 /**27 * 获取 Unsafe 对象 28 * @return29 */30 public static Unsafe getUnsafe() {31 try {32 Field field = Unsafe.class.getDeclaredField("theUnsafe");
33 field.setAccessible(true);
34 return (Unsafe) field.get(null);
35 } catch (Exception e) {36 e.printStackTrace();
37 }

38 return null;
39 }4041 /**42 * 获取字段的内存偏移量 43 * @param unsafe44 * @param clazz45 * @param fieldName46 * @return47 */48 public static long getFieldOffset(Unsafe unsafe, Class clazz, String fieldName) {49 try {50 return unsafe.objectFieldOffset(clazz.getDeclaredField(fieldName));
51 } catch (NoSuchFieldException e) {52 throw new Error(e);
53 }54 }55 }测试针对 entity.x 的 3 次 CAS 操作,分别试图将它从 0 改成 3、从 3 改成 5、从 3 改成 8。执行结果如下:
CAS 应用场景 CAS 在 java.util.concurrent.atomic 相关类、 Java AQS、CurrentHashMap 等实现上有非常广泛的应用。
如下图所示,AtomicInteger 的实现中,静态字段 valueOffset 即为字段 value 的内存偏移地址,valueOffset 的值在 AtomicInteger 初始化时,在静态代码块中通过 Unsafe 的 objectFieldOffset 方法获取。
在 AtomicInteger 中提供的线程安全方法中,通过字段 valueOffset 的值可以定位到 AtomicInteger 对象中 value 的内存地址,从而可以根据 CAS 实现对 value 字段的原子操作。

下图为某个 AtomicInteger 对象自增操作前后的内存示意图,对象的基地址 baseAddress=“0x110000”,通过 baseAddress+valueOffset 得到 value 的内存地址 valueAddress=“0x11000c”;然后通过 CAS 进行原子性的更新操作,成功则返回,否则继续重试,直到更新成功为止。
CAS 源码分析 Hotspot 虚拟机对 compareAndSwapInt 方法的实现如下:

1 #unsafe.cpp2 UNSAFE_ENTRY(jboolean, Unsafe_CompareAndSwapInt(JNIEnv *env, jobject unsafe, jobjectobj, jlong offset, jint e, jint x))
3 UnsafeWrapper("Unsafe_CompareAndSwapInt");
4 oop p = JNIHandles::resolve(obj);
5 // 根据偏移量,计算 value 的地址 6 jint* addr = (jint *) index_oop_from_field_offset_long(p, offset);
7 // Atomic::cmpxchg(x, addr, e) cas 逻辑 x:要交换的值 e:要比较的值 8 //cas 成功,返回期望值 e,等于 e,此方法返回 true9 //cas 失败,返回内存中的 value 值,不等于 e,此方法返回 false10 return (jint)(Atomic::cmpxchg(x, addr, e)) == e;
11 UNSAFE_END2 核心逻辑在 Atomic::cmpxchg 方法中,这个根据不同操作系统和不同 CPU 会有不同的实现。这里我们以 linux_64x 的为例,查看 Atomic::cmpxchg 的实现 1 #atomic_linux_x86.inline.hpp2 inline jint Atomic::cmpxchg (jint exchange_value, volatile jint* dest,jint compare_value) {3 //判断当前执行环境是否为多处理器环境 4 int mp = os::is_MP();
5 //LOCK_IF_MP(%4) 在多处理器环境下,为 cmpxchgl 指令添加 lock 前缀,以达到内存屏障的效果 6 //cmpxchgl 指令是包含在 x86 架构及 IA-64 架构中的一个原子条件指令,7 //它会首先比较 dest 指针指向的内存值是否和 compare_value 的值相等,8 //如果相等,则双向交换 dest 与 exchange_value,否则就单方面地将 dest 指向的内存值交给 exchange_value。
9 //这条指令完成了整个 CAS 操作,因此它也被称为 CAS 指令。
10 __asm__ volatile (LOCK_IF_MP(%4) "cmpxchgl %1,(%3)"
11 : "=a" (exchange_value)
12 : "r" (exchange_value), "a" (compare_value), "r" (dest), "r" (mp)
13 : "cc", "memory");
14 return exchange_value;
15 }

cmpxchgl 的详细执行过程:
首先,输入是"r" (exchange_value), “a” (compare_value), “r” (dest), “r” (mp),表示 compare_value 存入 eax 寄存器,而 exchange_value、dest、mp 的值存入任意的通用寄存器。嵌入式汇编规定把输出和输入寄存器按统一顺序编号,顺序是从输出寄存器序列从左到右从上到下以“%0”开始,分别记为%0、%1···%9。也就是说,输出的 eax 是%0,输入的 exchange_value、compare_value、dest、mp 分别是%1、%2、%3、%4。
因此,cmpxchg %1,(%3)实际上表示 cmpxchg exchange_value,(dest)
需要注意的是 cmpxchg 有个隐含操作数 eax,其实际过程是先比较 eax 的值(也就是 compare_value)
和 dest 地址所存的值是否相等,输出是"=a" (exchange_value),表示把 eax 中存的值写入 exchange_value 变量中。
Atomic::cmpxchg 这个函数最终返回值是 exchange_value,也就是说,如果 cmpxchgl 执行时 compare_value 和 dest 指针指向内存值相等则会使得 dest 指针指向内存值变成 exchange_value,最终 eax 存的 compare_value 赋值给了 exchange_value 变量,即函数最终返回的值是原先的 compare_value。此时 Unsafe_CompareAndSwapInt 的返回值(jint)(Atomic::cmpxchg(x, addr, e))
== e 就是 true,表明 CAS 成功。如果 cmpxchgl 执行时 compare_value 和(dest)不等则会把当前 dest 指针指向内存的值写入 eax,最终输出时赋值给 exchange_value 变量作为返回值,导致(jint)
(Atomic::cmpxchg(x, addr, e)) == e 得到 false,表明 CAS 失败。
现代处理器指令集架构基本上都会提供 CAS 指令,例如 x86 和 IA-64 架构中的 cmpxchgl 指令和 comxchgq 指令,sparc 架构中的 cas 指令和 casx 指令。
不管是 Hotspot 中的 Atomic::cmpxchg 方法,还是 Java 中的 compareAndSwapInt 方法,它们本质上都是对相应平台的 CAS 指令的一层简单封装。 CAS 指令作为一种硬件原语,有着天然的原子性,这也正是 CAS 的价值所在。
CAS 缺陷 CAS 虽然高效地解决了原子操作,但是还是存在一些缺陷的,主要表现在三个方面:
自旋 CAS 长时间不成功,则会给 CPU 带来非常大的开销只能保证一个共享变量原子操作 ABA 问题 ABA 问题及其解决方案 CAS 算法实现一个重要前提需要取出内存中某时刻的数据,而在下时刻比较并替换,那么在这个时间差类会导致数据的变化。
什么是 ABA 问题

当有多个线程对一个原子类进行操作的时候,某个线程在短时间内将原子类的值 A 修改为 B,又马上将其修改为 A,此时其他线程不感知,还是会修改成功。
测试

1 @Slf4j2 public class ABATest {34 public static void main(String[] args) {5 AtomicInteger atomicInteger = new AtomicInteger(1);
67 new Thread(()->{8 int value = atomicInteger.get();
9 log.debug("Thread1 read value: " + value);
1011 // 阻塞 1s12 LockSupport.parkNanos(1000000000L);
1314 // Thread1 通过 CAS 修改 value 值为 315 if (atomicInteger.compareAndSet(value, 3)) {16 log.debug("Thread1 update from " + value + " to 3");
17 } else {18 log.debug("Thread1 update fail!");
19 }20 },"Thread1").start();
2122 new Thread(()->{23 int value = atomicInteger.get();
24 log.debug("Thread2 read value: " + value);
25 // Thread2 通过 CAS 修改 value 值为 226 if (atomicInteger.compareAndSet(value, 2)) {27 log.debug("Thread2 update from " + value + " to 2");
2829 // do something30 value = atomicInteger.get();
31 log.debug("Thread2 read value: " + value);
32 // Thread2 通过 CAS 修改 value 值为 133 if (atomicInteger.compareAndSet(value, 1)) {34 log.debug("Thread2 update from " + value + " to 1");
35 }36 }37 },"Thread2").start();
38 }

39 }Thread1 不清楚 Thread2 对 value 的操作,误以为 value=1 没有修改过 ABA 问题的解决方案数据库有个锁称为乐观锁,是一种基于数据版本实现数据同步的机制,每次修改一次数据,版本就会进行累加。
同样,Java 也提供了相应的原子引用类 AtomicStampedReference<V>reference 即我们实际存储的变量,stamp 是版本,每次修改可以通过+1 保证版本唯一性。这样就可以保证每次修改后的版本也会往上递增。

1 @Slf4j2 public class AtomicStampedReferenceTest {34 public static void main(String[] args) {5 // 定义 AtomicStampedReference Pair.reference 值为 1, Pair.stamp 为 16 AtomicStampedReference atomicStampedReference = newAtomicStampedReference(1,1);
78 new Thread(()->{9 int[] stampHolder = new int[1];
10 int value = (int) atomicStampedReference.get(stampHolder);
11 int stamp = stampHolder[0];
12 log.debug("Thread1 read value: " + value + ", stamp: " + stamp);
1314 // 阻塞 1s15 LockSupport.parkNanos(1000000000L);
16 // Thread1 通过 CAS 修改 value 值为 317 if (atomicStampedReference.compareAndSet(value, 3,stamp,stamp+1)) {18 log.debug("Thread1 update from " + value + " to 3");
19 } else {20 log.debug("Thread1 update fail!");
21 }22 },"Thread1").start();
2324 new Thread(()->{25 int[] stampHolder = new int[1];
26 int value = (int)atomicStampedReference.get(stampHolder);
27 int stamp = stampHolder[0];
28 log.debug("Thread2 read value: " + value+ ", stamp: " + stamp);
29 // Thread2 通过 CAS 修改 value 值为 230 if (atomicStampedReference.compareAndSet(value, 2,stamp,stamp+1)) {31 log.debug("Thread2 update from " + value + " to 2");
3233 // do something3435 value = (int) atomicStampedReference.get(stampHolder);
36 stamp = stampHolder[0];
37 log.debug("Thread2 read value: " + value+ ", stamp: " + stamp);

38 // Thread2 通过 CAS 修改 value 值为 139 if (atomicStampedReference.compareAndSet(value, 1,stamp,stamp+1)) {40 log.debug("Thread2 update from " + value + " to 1");
41 }42 }43 },"Thread2").start();
44 }45 }Thread1 并没有成功修改 value 补充:AtomicMarkableReference 可以理解为上面 AtomicStampedReference 的简化版,就是不关心修改过几次,仅仅关心是否修改过。因此变量 mark 是 boolean 类型,仅记录值是否有过修改。
2.Atomic 原子操作类介绍在并发编程中很容易出现并发安全的问题,有一个很简单的例子就是多线程更新变量 i=1,比如多个线程执行 i++操作,就有可能获取不到正确的值,而这个问题,最常用的方法是通过 Synchronized 进行控制来达到线程安全的目的。但是由于 synchronized 是采用的是悲观锁策略,并不是特别高效的一种解决方案。实际上,在 J.U.C 下的 atomic 包提供了一系列的操作简单,性能高效,并能保证线程安全的类去更新基本类型变量,数组元素,引用类型以及更新对象中的字段类型。 atomic 包下的这些类都是采用的是乐观锁策略去原子更新数据,在 java 中则是使用 CAS 操作具体实现。
在 java.util.concurrent.atomic 包里提供了一组原子操作类:
基本类型:AtomicInteger、AtomicLong、AtomicBoolean;
引用类型:AtomicReference、AtomicStampedRerence、AtomicMarkableReference;
数组类型:AtomicIntegerArray、AtomicLongArray、AtomicReferenceArray 对象属性原子修改器:AtomicIntegerFieldUpdater、AtomicLongFieldUpdater、AtomicReferenceFieldUpdater 原子类型累加器(jdk1.8 增加的类):DoubleAccumulator、DoubleAdder、LongAccumulator、LongAdder、Striped64 原子更新基本类型以 AtomicInteger 为例总结常用的方法

1 //以原子的方式将实例中的原值加 1,返回的是自增前的旧值;
2 public final int getAndIncrement() {3 return unsafe.getAndAddInt(this, valueOffset, 1);
4 }56 //getAndSet(int newValue):将实例中的值更新为新值,并返回旧值;
7 public final boolean getAndSet(boolean newValue) {8 boolean prev;
9 do {10 prev = get();
11 } while (!compareAndSet(prev, newValue));
12 return prev;
13 }1415 //incrementAndGet() :以原子的方式将实例中的原值进行加 1 操作,并返回最终相加后的结果;
16 public final int incrementAndGet() {17 return unsafe.getAndAddInt(this, valueOffset, 1) + 1;
18 }1920 //addAndGet(int delta) :以原子方式将输入的数值与实例中原本的值相加,并返回最后的结果;
21 public final int addAndGet(int delta) {22 return unsafe.getAndAddInt(this, valueOffset, delta) + delta;
23 测试

1 public class AtomicIntegerTest {2 static AtomicInteger sum = new AtomicInteger(0);
34 public static void main(String[] args) {56 for (int i = 0; i < 10; i++) {7 Thread thread = new Thread(() -> {8 for (int j = 0; j < 10000; j++) {9 // 原子自增 CAS10 sum.incrementAndGet();
11 //TODO12 }13 });
14 thread.start();
15 }1617 try {18 Thread.sleep(3000);
19 } catch (InterruptedException e) {20 e.printStackTrace();
21 }22 System.out.println(sum.get());
2324 }2526 }incrementAndGet()方法通过 CAS 自增实现,如果 CAS 失败,自旋直到成功+1。
思考:这种 CAS 失败自旋的操作存在什么问题?
原子更新数组类型 AtomicIntegerArray 为例总结常用的方法

1 //addAndGet(int i, int delta):以原子更新的方式将数组中索引为 i 的元素与输入值相加;
2 public final int addAndGet(int i, int delta) {3 return getAndAdd(i, delta) + delta;
4 }56 //getAndIncrement(int i):以原子更新的方式将数组中索引为 i 的元素自增加 1;
7 public final int getAndIncrement(int i) {8 return getAndAdd(i, 1);
9 }1011 //compareAndSet(int i, int expect, int update):将数组中索引为 i 的位置的元素进行更新 12 public final boolean compareAndSet(int i, int expect, int update) {13 return compareAndSetRaw(checkedByteOffset(i), expect, update);
14 }测试 1 public class AtomicIntegerArrayTest {23 static int[] value = new int[]{ 1, 2, 3, 4, 5 };
4 static AtomicIntegerArray atomicIntegerArray = new AtomicIntegerArray(value);
567 public static void main(String[] args) throws InterruptedException {89 //设置索引 0 的元素为 10010 atomicIntegerArray.set(0, 100);
11 System.out.println(atomicIntegerArray.get(0));
12 //以原子更新的方式将数组中索引为 1 的元素与输入值相加 13 atomicIntegerArray.getAndAdd(1,5);
1415 System.out.println(atomicIntegerArray);
16 }17 }

原子更新引用类型 AtomicReference 作用是对普通对象的封装,它可以保证你在修改对象引用时的线程安全性。
1 public class AtomicReferenceTest {23 public static void main( String[] args ) {4 User user1 = new User("张三", 23);
5 User user2 = new User("李四", 25);
6 User user3 = new User("王五", 20);
78 //初始化为 user19 AtomicReference<User> atomicReference = new AtomicReference<>();
10 atomicReference.set(user1);
1112 //把 user2 赋给 atomicReference13 atomicReference.compareAndSet(user1, user2);
14 System.out.println(atomicReference.get());
1516 //把 user3 赋给 atomicReference17 atomicReference.compareAndSet(user1, user3);
18 System.out.println(atomicReference.get());
1920 }2122 }232425 @Data26 @AllArgsConstructor27 class User {28 private String name;
29 private Integer age;
30 }

对象属性原子修改器 AtomicIntegerFieldUpdater 可以线程安全地更新对象中的整型变量。

1 public class AtomicIntegerFieldUpdaterTest {23 public static class Candidate {45 volatile int score = 0;
67 AtomicInteger score2 = new AtomicInteger();
8 }910 public static final AtomicIntegerFieldUpdater<Candidate> scoreUpdater =11 AtomicIntegerFieldUpdater.newUpdater(Candidate.class, "score");
1213 public static AtomicInteger realScore = new AtomicInteger(0);
1415 public static void main(String[] args) throws InterruptedException {1617 final Candidate candidate = new Candidate();
1819 Thread[] t = new Thread[10000];
20 for (int i = 0; i < 10000; i++) {21 t[i] = new Thread(new Runnable() {22 @Override23 public void run() {24 if (Math.random() > 0.4) {25 candidate.score2.incrementAndGet();
26 scoreUpdater.incrementAndGet(candidate);
27 realScore.incrementAndGet();
28 }29 }30 });
31 t[i].start();
32 }33 for (int i = 0; i < 10000; i++) {34 t[i].join();
35 }36 System.out.println("AtomicIntegerFieldUpdater Score=" + candidate.score);
37 System.out.println("AtomicInteger Score=" + candidate.score2.get());
38 System.out.println("realScore=" + realScore.get());

3940 }41 }对于 AtomicIntegerFieldUpdater 的使用稍微有一些限制和约束,约束如下:
(1)字段必须是 volatile 类型的,在线程之间共享变量时保证立即可见.eg:volatile int value = 3(2)字段的描述类型(修饰符 public/protected/default/private)与调用者与操作对象字段的关系一致。也就是说调用者能够直接操作对象字段,那么就可以反射进行原子操作。但是对于父类的字段,子类是不能直接操作的,尽管子类可以访问父类的字段。
(3)只能是实例变量,不能是类变量,也就是说不能加 static 关键字。
(4)只能是可修改变量,不能使 final 变量,因为 final 的语义就是不可修改。实际上 final 的语义和 volatile 是有冲突的,这两个关键字不能同时存在。
(5)对于 AtomicIntegerFieldUpdater 和 AtomicLongFieldUpdater 只能修改 int/long 类型的字段,不能修改其包装类型(Integer/Long)。如果要修改包装类型就需要使用 AtomicReferenceFieldUpdater。
LongAdder/DoubleAdder 详解 AtomicLong 是利用了底层的 CAS 操作来提供并发性的,比如 addAndGet 方法:
上述方法调用了 Unsafe 类的 getAndAddLong 方法,该方法内部是个 native 方法,它的逻辑是采用自旋的方式不断更新目标值,直到更新成功。
在并发量较低的环境下,线程冲突的概率比较小,自旋的次数不会很多。但是,高并发环境下,N 个线程同时进行自旋操作,会出现大量失败并不断自旋的情况,此时 AtomicLong 的自旋会成为瓶颈。
这就是 LongAdder 引入的初衷——解决高并发环境下 AtomicInteger,AtomicLong 的自旋瓶颈问题。
性能测试

1 public class LongAdderTest {23 public static void main(String[] args) {4 testAtomicLongVSLongAdder(10, 10000);
5 System.out.println("==================");
6 testAtomicLongVSLongAdder(10, 200000);
7 System.out.println("==================");
8 testAtomicLongVSLongAdder(100, 200000);
9 }1011 static void testAtomicLongVSLongAdder(final int threadCount, final int times) {12 try {13 long start = System.currentTimeMillis();
14 testLongAdder(threadCount, times);
15 long end = System.currentTimeMillis() - start;
16 System.out.println("条件>>>>>>线程数:" + threadCount + ", 单线程操作计数" +times);
17 System.out.println("结果>>>>>>LongAdder 方式增加计数" + (threadCount * times)
+ "次,共计耗时:" + end);
1819 long start2 = System.currentTimeMillis();
20 testAtomicLong(threadCount, times);
21 long end2 = System.currentTimeMillis() - start2;
22 System.out.println("条件>>>>>>线程数:" + threadCount + ", 单线程操作计数" +times);
23 System.out.println("结果>>>>>>AtomicLong 方式增加计数" + (threadCount *times) + "次,共计耗时:" + end2);
24 } catch (InterruptedException e) {25 e.printStackTrace();
26 }27 }2829 static void testAtomicLong(final int threadCount, final int times) throwsInterruptedException {30 CountDownLatch countDownLatch = new CountDownLatch(threadCount);
31 AtomicLong atomicLong = new AtomicLong();
32 for (int i = 0; i < threadCount; i++) {33 new Thread(new Runnable() {34 @Override35 public void run() {

36 for (int j = 0; j < times; j++) {37 atomicLong.incrementAndGet();
38 }39 countDownLatch.countDown();
40 }41 }, "my-thread" + i).start();
42 }43 countDownLatch.await();
44 }4546 static void testLongAdder(final int threadCount, final int times) throwsInterruptedException {47 CountDownLatch countDownLatch = new CountDownLatch(threadCount);
48 LongAdder longAdder = new LongAdder();
49 for (int i = 0; i < threadCount; i++) {50 new Thread(new Runnable() {51 @Override52 public void run() {53 for (int j = 0; j < times; j++) {54 longAdder.add(1);
55 }56 countDownLatch.countDown();
57 }58 }, "my-thread" + i).start();
59 }6061 countDownLatch.await();
62 }63 }测试结果:线程数越多,并发操作数越大,LongAdder 的优势越明显低并发、一般的业务场景下 AtomicLong 是足够了。如果并发量很多,存在大量写多读少的情况,那 LongAdder 可能更合适。
LongAdder 原理设计思路

AtomicLong 中有个内部变量 value 保存着实际的 long 值,所有的操作都是针对该变量进行。也就是说,高并发环境下,value 变量其实是一个热点,也就是 N 个线程竞争一个热点。 LongAdder 的基本思路就是分散热点,将 value 值分散到一个数组中,不同线程会命中到数组的不同槽中,各个线程只对自己槽中的那个值进行 CAS 操作,这样热点就被分散了,冲突的概率就小很多。如果要获取真正的 long 值,只要将各个槽中的变量值累加返回。
LongAdder 的内部结构 LongAdder 内部有一个 base 变量,一个 Cell[]数组:
base 变量:非竞态条件下,直接累加到该变量上 Cell[]数组:竞态条件下,累加个各个线程自己的槽 Cell[i]中

1 /** Number of CPUS, to place bound on table size */2 // CPU 核数,用来决定槽数组的大小 3 static final int NCPU = Runtime.getRuntime().availableProcessors();
45 /**6 * Table of cells. When non-null, size is a power of 2.7 */8 // 数组槽,大小为 2 的次幂 9 transient volatile Cell[] cells;
1011 /**12 * Base value, used mainly when there is no contention, but also as13 * a fallback during table initialization races. Updated via CAS.14 */15 /**16 * 基数,在两种情况下会使用:
17 * 1. 没有遇到并发竞争时,直接使用 base 累加数值 18 * 2. 初始化 cells 数组时,必须要保证 cells 数组只能被初始化一次(即只有一个线程能对 cells 初始化),19 * 其他竞争失败的线程会将数值累加到 base 上 20 */21 transient volatile long base;
2223 /**24 * Spinlock (locked via CAS) used when resizing and/or creating Cells.25 */26 transient volatile int cellsBusy;
定义了一个内部 Cell 类,这就是我们之前所说的槽,每个 Cell 对象存有一个 value 值,可以通过 Unsafe 来 CAS 操作它的值:
LongAdder#add 方法 LongAdder#add 方法的逻辑如下图:
只有从未出现过并发冲突的时候,base 基数才会使用到,一旦出现了并发冲突,之后所有的操作都只针对 Cell[]数组中的单元 Cell。
如果 Cell[]数组未初始化,会调用父类的 longAccumelate 去初始化 Cell[],如果 Cell[]已经初始化但是冲突发生在 Cell 单元内,则也调用父类的 longAccumelate,此时可能就需要对 Cell[]扩容了。

这也是 LongAdder 设计的精妙之处:尽量减少热点冲突,不到最后万不得已,尽量将 CAS 操作延迟。
Striped64#longAccumulate 方法整个 Striped64#longAccumulate 的流程图如下:
LongAdder#sum 方法 1 /**2 * 返回累加的和,也就是"当前时刻"的计数值 3 * 注意: 高并发时,除非全局加锁,否则得不到程序运行中某个时刻绝对准确的值 4 * 此返回值可能不是绝对准确的,因为调用这个方法时还有其他线程可能正在进行计数累加,5 * 方法的返回时刻和调用时刻不是同一个点,在有并发的情况下,这个值只是近似准确的计数值 6 */7 public long sum() {8 Cell[] as = cells; Cell a;
9 long sum = base;
10 if (as != null) {11 for (int i = 0; i < as.length; ++i) {12 if ((a = as[i]) != null)
13 sum += a.value;
14 }15 }16 return sum;
17 }由于计算总和时没有对 Cell 数组进行加锁,所以在累加过程中可能有其他线程对 Cell 中的值进行了修改,也有可能对数组进行了扩容,所以 sum 返回的值并不是非常精确的,其返回值并不是一个调用 sum 方法时的原子快照值。
