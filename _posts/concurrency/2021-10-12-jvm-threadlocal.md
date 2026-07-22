---


title: "导致JVM内存泄露的ThreadLocal详解"
description: "特性: 1. 线程安全: 在多线程并发的场景下保证线程安全 2. 传递数据: 我们可以通过 ThreadLocal 在同一线程,不同组件中传递公共变量 3."
author: hsc
date: 2021-10-12 00:00:00 +0800
categories: ['Java 后端', '并发编程']
tags: ['并发编程', 'JUC', '线程池', 'synchronized', 'ThreadLocal', 'CAS']
toc: true


---

### 1. ThreadLocal 介绍
#### 1.1 什么是 ThreadLocalJava 官方文档中的描述:ThreadLocal 类用来提供线程内部的局部变量。这种变量在多线程环境下访问(通过 get 和 set 方法访问)时能保证各个线程的变量相对独立于其他线程内的变量。 ThreadLocal 实例通常来说都是 private static 类型的,用于关联线程和线程上下文。
特性:
1. 线程安全: 在多线程并发的场景下保证线程安全
2. 传递数据: 我们可以通过 ThreadLocal 在同一线程,不同组件中传递公共变量
3. 线程隔离: 每个线程的变量都是独立的,不会互相影响
1.2 基本使用常用方法在使用之前,我们先来认识几个 ThreadLocal 的常用方法方法声明 描述 ThreadLocal() 创建 ThreadLocal 对象 public void set( T value) 设置当前线程绑定的局部变量 public T get() 获取当前线程绑定的局部变量 public void remove() 移除当前线程绑定的局部变量使用案例我们来看下面这个案例 , 感受一下 ThreadLocal 线程隔离的特点:

1 public class ThreadLocalDemo {2 private String content;
34 private String getContent() {5 return content;
6 }78 private void setContent(String content) {9 this.content = content;
10 }1112 public static void main(String[] args) {13 ThreadLocalDemo demo = new ThreadLocalDemo();
14 for (int i = 0; i < 5; i++) {15 Thread thread = new Thread(new Runnable() {16 @Override17 public void run() {18 demo.setContent(Thread.currentThread().getName() + "的数据");
19 System.out.println(Thread.currentThread().getName() + "--->" +demo.getContent());
20 }21 });
22 thread.setName("线程" + i);
23 thread.start();
24 }25 }26 }输出:
1 线程 0--->线程 1 的数据 2 线程 2--->线程 2 的数据 3 线程 1--->线程 1 的数据 4 线程 4--->线程 4 的数据 5 线程 3--->线程 3 的数据

从结果可以看出多个线程在访问同一个变量的时候出现的异常,线程间的数据没有隔离。下面我们来看下采用 ThreadLocal 的方式来解决这个问题的例子。
1 public class ThreadLocalDemo2 {2 private static ThreadLocal<String> threadLocal = new ThreadLocal<>();
34 private String content;
56 private String getContent() {7 return threadLocal.get();
8 }910 private void setContent(String content) {11 threadLocal.set(content);
12 }1314 public static void main(String[] args) {15 ThreadLocalDemo2 demo = new ThreadLocalDemo2();
16 for (int i = 0; i < 5; i++) {17 Thread thread = new Thread(new Runnable() {18 @Override19 public void run() {20 demo.setContent(Thread.currentThread().getName() + "的数据");
21 System.out.println(Thread.currentThread().getName() + "--->" +demo.getContent());
22 }23 });
24 thread.setName("线程" + i);
25 thread.start();
26 }27 }28 }输出:

1 线程 0--->线程 0 的数据 2 线程 4--->线程 4 的数据 3 线程 1--->线程 1 的数据 4 线程 3--->线程 3 的数据 5 线程 2--->线程 2 的数据从结果来看,这样很好的解决了多线程之间数据隔离的问题,十分方便。
1.3 ThreadLocal 与 synchronized 的区别虽然 ThreadLocal 模式与 synchronized 关键字都用于处理多线程并发访问变量的问题, 不过两者处理问题的角度和思路不同。
synchronized ThreadLocalThreadLocal 采用'以空间换时同步机制采用'以时间换空间'的间'的方式, 为每一个线程都提供原理 方式, 只提供了一份变量,让不同了一份变量的副本,从而实现同的线程排队访问时访问而相不干扰多线程中让每个线程之间的数据侧重点 多个线程之间访问资源的同步相互隔离在刚刚的案例中,虽然使用 ThreadLocal 和 synchronized 都能解决问题,但是使用 ThreadLocal 更为合适,因为这样可以使程序拥有更高的并发性。
1.4 ThreadLocal 的优势在一些特定场景下,ThreadLocal 有两个突出的优势:
1. 传递数据 : 保存每个线程绑定的数据,在需要的地方可以直接获取, 避免参数直接传递带来的代码耦合问题
2. 线程隔离 : 各线程之间的数据相互隔离却又具备并发性,避免同步方式带来的性能损失 ThreadLocal 在 Spring 事务中的应用 Spring 的事务就借助了 ThreadLocal 类。 Spring 会从数据库连接池中获得一个 connection,然会把 connection 放进 ThreadLocal 中,也就和线程绑定了,事务需要提交或者回滚,只要从 ThreadLocal 中拿到 connection 进行操作。
为何 Spring 的事务要借助 ThreadLocal 类?2 以 JDBC 为例,正常的事务代码可能如下:

1 dbc = new DataBaseConnection();//第 1 行 2 Connection con = dbc.getConnection();//第 2 行 3 con.setAutoCommit(false);// //第 3 行 4 con.executeUpdate(...);//第 4 行 5 con.executeUpdate(...);//第 5 行 6 con.executeUpdate(...);//第 6 行 7 con.commit();////第 7 行上述代码,可以分成三个部分:
事务准备阶段:第 1~3 行业务处理阶段:第 4~6 行事务提交阶段:第 7 行可以很明显的看到,不管我们开启事务还是执行具体的 sql 都需要一个具体的数据库连接。
现在我们开发应用一般都采用三层结构,如果我们控制事务的代码都放在 DAO(DataAccessObject)对象中,在 DAO 对象的每个方法当中去打开事务和关闭事务,当 Service 对象在调用 DAO 时,如果只调用一个 DAO,那我们这样实现则效果不错,但往往我们的 Service 会调用一系列的 DAO 对数据库进行多次操作,那么,这个时候我们就无法控制事务的边界了,因为实际应用当中,我们的 Service 调用的 DAO 的个数是不确定的,可根据需求而变化,而且还可能出现 Service 调用 Service 的情况。
如果不使用 ThreadLocal,代码大概就会是这个样子:

但是需要注意一个问题,如何让三个 DAO 使用同一个数据源连接呢?我们就必须为每个 DAO 传递同一个数据库连接,要么就是在 DAO 实例化的时候作为构造方法的参数传递,要么在每个 DAO 的实例方法中作为方法的参数传递。这两种方式无疑对我们的 Spring 框架或者开发人员来说都不合适。为了让这个数据库连接可以跨阶段传递,又不显示的进行参数传递,就必须使用别的办法。
Web 容器中,每个完整的请求周期会由一个线程来处理。因此,如果我们能将一些参数绑定到线程的话,就可以实现在软件架构中跨层次的参数共享(是隐式的共享)。而 JAVA 中恰好提供了绑定的方法-使用 ThreadLocal。
结合使用 Spring 里的 IOC 和 AOP,就可以很好的解决这一点。
只要将一个数据库连接放入 ThreadLocal 中,当前线程执行时只要有使用数据库连接的地方就从 ThreadLocal 获得就行了。
2. ThreadLocal 的内部结构通过以上的学习,我们对 ThreadLocal 的作用有了一定的认识。现在我们一起来看一下 ThreadLocal 的内部结构,探究它能够实现线程数据隔离的原理。
2.1 常见的误解如果我们不去看源代码的话,可能会猜测 ThreadLocal 是这样子设计的:每个 ThreadLocal 都创建一个 Map,然后用线程作为 Map 的 key,要存储的局部变量作为 Map 的 value,这样就能达到各个线程的局部变量隔离的效果。这是最简单的设计方法,JDK 最早期的 ThreadLocal 确实是这样设计的,但现在早已不是了。

#### 2.2 现在的设计但是,JDK 后面优化了设计方案,在 JDK8 中 ThreadLocal 的设计是:每个 Thread 维护一个 ThreadLocalMap,这个 Map 的 key 是 ThreadLocal 实例本身,value 才是真正要存储的值 Object。
具体的过程是这样的:
1. 每个 Thread 线程内部都有一个 Map (ThreadLocalMap)
2. Map 里面存储 ThreadLocal 对象(key)和线程的变量副本(value)
3. Thread 内部的 Map 是由 ThreadLocal 维护的,由 ThreadLocal 负责向 map 获取和设置线程的变量值。
4. 对于不同的线程,每次获取副本值时,别的线程并不能获取到当前线程的副本值,形成了副本的隔离,互不干扰。
2.3 这样设计的好处这个设计与我们一开始说的设计刚好相反,这样设计有如下两个优势:
1. 这样设计之后每个 Map 存储的 Entry 数量就会变少。因为之前的存储数量由 Thread 的数量决定,现在是由 ThreadLocal 的数量决定。在实际运用当中,往往 ThreadLocal 的数量要少于 Thread 的数量。
2. 当 Thread 销毁之后,对应的 ThreadLocalMap 也会随之销毁,能减少内存的使用。

3.ThreadLocal 的核心方法源码基于 ThreadLocal 的内部结构,我们继续分析它的核心方法源码,更深入的了解其操作原理。
除了构造方法之外, ThreadLocal 对外暴露的方法有以下 4 个:
方法声明 描述 protected T initialValue() 返回当前线程局部变量的初始值 public void set( T value) 设置当前线程绑定的局部变量 public T get() 获取当前线程绑定的局部变量 public void remove() 移除当前线程绑定的局部变量以下是这 4 个方法的详细源码分析 3.1 set 方法(1 ) 源码和对应的中文注释

1 /**2 * 设置当前线程对应的 ThreadLocal 的值 3 *4 * @param value 将要保存在当前线程对应的 ThreadLocal 的值 5 */6 public void set(T value) {7 // 获取当前线程对象 8 Thread t = Thread.currentThread();
9 // 获取此线程对象中维护的 ThreadLocalMap 对象 10 ThreadLocalMap map = getMap(t);
11 // 判断 map 是否存在 12 if (map != null)
13 // 存在则调用 map.set 设置此实体 entry14 map.set(this, value);
15 else16 // 1)当前线程 Thread 不存在 ThreadLocalMap 对象 17 // 2)则调用 createMap 进行 ThreadLocalMap 对象的初始化 18 // 3)并将 t(当前线程)和 value(t 对应的值)作为第一个 entry 存放至 ThreadLocalMap 中 19 createMap(t, value);
20 }2122 /**23 * 获取当前线程 Thread 对应维护的 ThreadLocalMap24 *25 * @param t the current thread 当前线程 26 * @return the map 对应维护的 ThreadLocalMap27 */28 ThreadLocalMap getMap(Thread t) {29 return t.threadLocals;
30 }31 /**32 *创建当前线程 Thread 对应维护的 ThreadLocalMap33 *34 * @param t 当前线程 35 * @param firstValue 存放到 map 中第一个 entry 的值 36 */37 void createMap(Thread t, T firstValue) {38 //这里的 this 是调用此方法的 threadLocal

39 t.threadLocals = new ThreadLocalMap(this, firstValue);
(2 ) 代码执行流程 A. 首先获取当前线程,并根据当前线程获取一个 MapB. 如果获取的 Map 不为空,则将参数设置到 Map 中(当前 ThreadLocal 的引用作为 key)
C. 如果 Map 为空,则给该线程创建 Map,并设置初始值 3.2 get 方法(1 ) 源码和对应的中文注释

1 /**2 * 返回当前线程中保存 ThreadLocal 的值 3 * 如果当前线程没有此 ThreadLocal 变量,4 * 则它会通过调用{@link #initialValue} 方法进行初始化值 5 *6 * @return 返回当前线程对应此 ThreadLocal 的值 7 */8 public T get() {9 // 获取当前线程对象 10 Thread t = Thread.currentThread();
11 // 获取此线程对象中维护的 ThreadLocalMap 对象 12 ThreadLocalMap map = getMap(t);
13 // 如果此 map 存在 14 if (map != null) {15 // 以当前的 ThreadLocal 为 key,调用 getEntry 获取对应的存储实体 e16 ThreadLocalMap.Entry e = map.getEntry(this);
17 // 对 e 进行判空 18 if (e != null) {19 @SuppressWarnings("unchecked")
20 // 获取存储实体 e 对应的 value 值 21 // 即为我们想要的当前线程对应此 ThreadLocal 的值 22 T result = (T)e.value;
23 return result;
24 }25 }26 /*27 初始化 : 有两种情况有执行当前代码 28 第一种情况: map 不存在,表示此线程没有维护的 ThreadLocalMap 对象 29 第二种情况: map 存在, 但是没有与当前 ThreadLocal 关联的 entry30 */31 return setInitialValue();
32 }3334 /**35 * 初始化 36 *37 * @return the initial value 初始化后的值 38 */

39 private T setInitialValue() {40 // 调用 initialValue 获取初始化的值 41 // 此方法可以被子类重写, 如果不重写默认返回 null42 T value = initialValue();
43 // 获取当前线程对象 44 Thread t = Thread.currentThread();
45 // 获取此线程对象中维护的 ThreadLocalMap 对象 46 ThreadLocalMap map = getMap(t);
47 // 判断 map 是否存在 48 if (map != null)
49 // 存在则调用 map.set 设置此实体 entry50 map.set(this, value);
51 else52 // 1)当前线程 Thread 不存在 ThreadLocalMap 对象 53 // 2)则调用 createMap 进行 ThreadLocalMap 对象的初始化 54 // 3)并将 t(当前线程)和 value(t 对应的值)作为第一个 entry 存放至 ThreadLocalMap 中 55 createMap(t, value);
56 // 返回设置的值 value57 return value;
58 }(2 ) 代码执行流程 A. 首先获取当前线程, 根据当前线程获取一个 MapB. 如果获取的 Map 不为空,则在 Map 中以 ThreadLocal 的引用作为 key 来在 Map 中获取对应的 Entry e,否则转到 DC. 如果 e 不为 null,则返回 e.value,否则转到 DD. Map 为空或者 e 为空,则通过 initialValue 函数获取初始值 value,然后用 ThreadLocal 的引用和 value 作为 firstKey 和 firstValue 创建一个新的 Map 总结: 先获取当前线程的 ThreadLocalMap 变量,如果存在则返回值,不存在则创建并返回初始值。
3.3 remove 方法(1 ) 源码和对应的中文注释

1 /**2 * 删除当前线程中保存的 ThreadLocal 对应的实体 entry3 */4 public void remove() {5 // 获取当前线程对象中维护的 ThreadLocalMap 对象 6 ThreadLocalMap m = getMap(Thread.currentThread());
7 // 如果此 map 存在 8 if (m != null)
9 // 存在则调用 map.remove10 // 以当前 ThreadLocal 为 key 删除对应的实体 entry11 m.remove(this);
12 }(2 ) 代码执行流程 A. 首先获取当前线程,并根据当前线程获取一个 MapB. 如果获取的 Map 不为空,则移除当前 ThreadLocal 对象对应的 entry3.4 initialValue 方法 1 /**2 * 返回当前线程对应的 ThreadLocal 的初始值 34 * 此方法的第一次调用发生在,当线程通过 get 方法访问此线程的 ThreadLocal 值时 5 * 除非线程先调用了 set 方法,在这种情况下,initialValue 才不会被这个线程调用。
6 * 通常情况下,每个线程最多调用一次这个方法。
7 *8 * <p>这个方法仅仅简单的返回 null {@code null};
9 * 如果程序员想 ThreadLocal 线程局部变量有一个除 null 以外的初始值,10 * 必须通过子类继承{@code ThreadLocal} 的方式去重写此方法 11 * 通常, 可以通过匿名内部类的方式实现 12 *13 * @return 当前 ThreadLocal 的初始值 14 */15 protected T initialValue() {16 return null;
17 }

此方法的作用是 返回该线程局部变量的初始值。
(1) 这个方法是一个延迟调用方法,从上面的代码我们得知,在 set 方法还未调用而先调用了 get 方法时才执行,并且仅执行 1 次。
(2)这个方法缺省实现直接返回一个 null。
(3)如果想要一个除 null 之外的初始值,可以重写此方法。(备注: 该方法是一个 protected 的方法,显然是为了让子类覆盖而设计的)
4. ThreadLocalMap 源码分析在分析 ThreadLocal 方法的时候,我们了解到 ThreadLocal 的操作实际上是围绕 ThreadLocalMap 展开的。 ThreadLocalMap 的源码相对比较复杂, 我们从以下三个方面进行讨论。
4.1 基本结构 ThreadLocalMap 是 ThreadLocal 的内部类,没有实现 Map 接口,用独立的方式实现了 Map 的功能,其内部的 Entry 也是独立实现。
(1) 成员变量

1 /**2 * 初始容量 —— 必须是 2 的整次幂 3 */4 private static final int INITIAL_CAPACITY = 16;
56 /**7 * 存放数据的 table,Entry 类的定义在下面分析 8 * 同样,数组长度必须是 2 的整次幂。
9 */10 private Entry[] table;
1112 /**13 * 数组里面 entrys 的个数,可以用于判断 table 当前使用量是否超过阈值。
14 */15 private int size = 0;
1617 /**18 * 进行扩容的阈值,表使用量大于它的时候进行扩容。
19 */20 private int 2; // Default to 021 跟 HashMap 类似,INITIAL_CAPACITY 代表这个 Map 的初始容量;table 是一个 Entry 类型的数组,用于存储数据;size 代表表中的存储数目; threshold 代表需要扩容时对应 size 的阈值。
(2) 存储结构 - Entry

1 /*2 * Entry 继承 WeakReference,并且用 ThreadLocal 作为 key.3 * 如果 key 为 null(entry.get() == null),意味着 key 不再被引用,4 * 因此这时候 entry 也可以从 table 中清除。
5 */6 static class Entry extends WeakReference<ThreadLocal<?>> {7 /** The value associated with this ThreadLocal. */8 Object value;
910 Entry(ThreadLocal<?> k, Object v) {11 super(k);
12 value = v;
13 }14 }在 ThreadLocalMap 中,也是用 Entry 来保存 K-V 结构数据的。不过 Entry 中的 key 只能是 ThreadLocal 对象,这点在构造方法中已经限定死了。
另外,Entry 继承 WeakReference,也就是 key(ThreadLocal)是弱引用,其目的是将 ThreadLocal 对象的生命周期和线程生命周期解绑。
4.2 弱引用和内存泄漏有些程序员在使用 ThreadLocal 的过程中会发现有内存泄漏的情况发生,就猜测这个内存泄漏跟 Entry 中使用了弱引用的 key 有关系。这个理解其实是不对的。
我们先来回顾这个问题中涉及的几个名词概念,再来分析问题。
(1) 内存泄漏相关概念 Memory overflow:内存溢出,没有足够的内存提供申请者使用。
Memory leak: 内存泄漏是指程序中己动态分配的堆内存由于某种原因程序未释放或无法释放,造成系统内存的浪费,导致程序运行速度减慢甚至系统崩溃等严重后果。内存泄漏的堆积终将导致内存溢出。
(2) 弱引用相关概念 Java 中的引用有 4 种类型: 强、软、弱、虚。当前这个问题主要涉及到强引用和弱引用:
强引用(“Strong” Reference),就是我们最常见的普通对象引用,只要还有强引用指向一个对象,就能表明对象还“活着”,垃圾回收器就不会回收这种对象。
弱引用(WeakReference),垃圾回收器一旦发现了只具有弱引用的对象,不管当前内存空间足够与否,都会回收它的内存。
(3) 如果 key 使用强引用假设 ThreadLocalMap 中的 key 使用了强引用,那么会出现内存泄漏吗?

此时 ThreadLocal 的内存图(实线表示强引用)如下:
假设在业务代码中使用完 ThreadLocal ,threadLocal Ref 被回收了。
但是因为 threadLocalMap 的 Entry 强引用了 threadLocal,造成 threadLocal 无法被回收。
在没有手动删除这个 Entry 以及 CurrentThread 依然运行的前提下,始终有强引用链 threadRef->currentThread->threadLocalMap->entry,Entry 就不会被回收(Entry 中包括了 ThreadLocal 实例和 value),导致 Entry 内存泄漏。
也就是说,ThreadLocalMap 中的 key 使用了强引用, 是无法完全避免内存泄漏的。
(5)如果 key 使用弱引用那么 ThreadLocalMap 中的 key 使用了弱引用,会出现内存泄漏吗?
此时 ThreadLocal 的内存图(实线表示强引用,虚线表示弱引用)如下:
同样假设在业务代码中使用完 ThreadLocal ,threadLocal Ref 被回收了。
由于 ThreadLocalMap 只持有 ThreadLocal 的弱引用,没有任何强引用指向 threadlocal 实例, 所以 threadlocal 就可以顺利被 gc 回收,此时 Entry 中的 key=null。
但是在没有手动删除这个 Entry 以及 CurrentThread 依然运行的前提下,也存在有强引用链 threadRef->currentThread->threadLocalMap->entry -> value ,value 不会被回收, 而这块 value 永远不会被访问到了,导致 value 内存泄漏。
也就是说,ThreadLocalMap 中的 key 使用了弱引用, 也有可能内存泄漏。
(6)出现内存泄漏的真实原因比较以上两种情况,我们就会发现,内存泄漏的发生跟 ThreadLocalMap 中的 key 是否使用弱引用是没有关系的。那么内存泄漏的的真正原因是什么呢?
细心的同学会发现,在以上两种内存泄漏的情况中,都有两个前提:
1 1. 没有手动删除这个 Entry2 2. CurrentThread 依然运行第一点很好理解,只要在使用完 ThreadLocal,调用其 remove 方法删除对应的 Entry,就能避免内存泄漏。
第二点稍微复杂一点, 由于 ThreadLocalMap 是 Thread 的一个属性,被当前线程所引用,所以它的生命周期跟 Thread 一样长。那么在使用完 ThreadLocal 的使用,如果当前 Thread 也随之执行结束,ThreadLocalMap 自然也会被 gc 回收,从根源上避免了内存泄漏。
综上,ThreadLocal 内存泄漏的根源是:由于 ThreadLocalMap 的生命周期跟 Thread 一样长,如果没有手动删除对应 key 就会导致内存泄漏。
(7) 为什么使用弱引用

根据刚才的分析, 我们知道了: 无论 ThreadLocalMap 中的 key 使用哪种类型引用都无法完全避免内存泄漏,跟使用弱引用没有关系。
要避免内存泄漏有两种方式:
1. 使用完 ThreadLocal,调用其 remove 方法删除对应的 Entry
2. 使用完 ThreadLocal,当前 Thread 也随之运行结束相对第一种方式,第二种方式显然更不好控制,特别是使用线程池的时候,线程结束是不会销毁的。
也就是说,只要记得在使用完 ThreadLocal 及时的调用 remove,无论 key 是强引用还是弱引用都不会有问题。那么为什么 key 要用弱引用呢?
事实上,在 ThreadLocalMap 中的 set/getEntry 方法中,会对 key 为 null(也即是 ThreadLocal 为 null)进行判断,如果为 null 的话,那么是会对 value 置为 null 的。
这就意味着使用完 ThreadLocal,CurrentThread 依然运行的前提下,就算忘记调用 remove 方法,弱引用比强引用可以多一层保障:弱引用的 ThreadLocal 会被回收,对应的 value 在下一次 ThreadLocalMap 调用 set,get,remove 中的任一方法的时候会被清除,从而避免内存泄漏。
4.3 hash 冲突的解决 hash 冲突的解决是 Map 中的一个重要内容。我们以 hash 冲突的解决为线索,来研究一下 ThreadLocalMap 的核心源码。
(1) 首先从 ThreadLocal 的 set() 方法入手

1 public void set(T value) {2 Thread t = Thread.currentThread();
3 ThreadLocal.ThreadLocalMap map = getMap(t);
4 if (map != null)
5 //调用了 ThreadLocalMap 的 set 方法 6 map.set(this, value);
7 else8 createMap(t, value);
9 }1011 ThreadLocal.ThreadLocalMap getMap(Thread t) {12 return t.threadLocals;
13 }1415 void createMap(Thread t, T firstValue) {16 //调用了 ThreadLocalMap 的构造方法 17 t.threadLocals = new ThreadLocal.ThreadLocalMap(this, firstValue);
18 }这个方法我们刚才分析过, 其作用是设置当前线程绑定的局部变量 :
A. 首先获取当前线程,并根据当前线程获取一个 MapB. 如果获取的 Map 不为空,则将参数设置到 Map 中(当前 ThreadLocal 的引用作为 key)
(这里调用了 ThreadLocalMap 的 set 方法)
C. 如果 Map 为空,则给该线程创建 Map,并设置初始值(这里调用了 ThreadLocalMap 的构造方法)
这段代码有两个地方分别涉及到 ThreadLocalMap 的两个方法, 我们接着分析这两个方法。
(2)构造方法 ThreadLocalMap(ThreadLocal<?> firstKey, Object firstValue)

1 /*2 * firstKey : 本 ThreadLocal 实例(this)
3 * firstValue : 要保存的线程本地变量 4 */5 ThreadLocalMap(ThreadLocal<?> firstKey, Object firstValue) {6 //初始化 table7 table = new ThreadLocal.ThreadLocalMap.Entry[INITIAL_CAPACITY];
8 //计算索引(重点代码)
9 int i = firstKey.threadLocalHashCode & (INITIAL_CAPACITY - 1);
10 //设置值 11 table[i] = new ThreadLocal.ThreadLocalMap.Entry(firstKey, firstValue);
12 size = 1;
13 //设置阈值 14 setThreshold(INITIAL_CAPACITY);
15 }构造函数首先创建一个长度为 16 的 Entry 数组,然后计算出 firstKey 对应的索引,然后存储到 table 中,并设置 size 和 threshold。
重点分析: int i = firstKey.threadLocalHashCode & (INITIAL_CAPACITY - 1)。
a. 关于 firstKey.threadLocalHashCode:
1 private final int threadLocalHashCode = nextHashCode();
23 private static int nextHashCode() {4 return nextHashCode.getAndAdd(HASH_INCREMENT);
5 }6 //AtomicInteger 是一个提供原子操作的 Integer 类,通过线程安全的方式操作加减,适合高并发情况下的使用 7 private static AtomicInteger nextHashCode = new AtomicInteger();
8 //特殊的 hash 值 9 private static final int HASH_INCREMENT = 0x61c88647;
这里定义了一个 AtomicInteger 类型,每次获取当前值并加上 HASH_INCREMENT,HASH_INCREMENT= 0x61c88647,这个值跟斐波那契数列(黄金分割数)有关,其主要目的就是为了让哈希码能均匀的分布在 2 的 n 次方的数组里, 也就是 Entry[] table 中,这样做可以尽量避免 hash 冲突。
b. 关于& (INITIAL_CAPACITY - 1)

计算 hash 的时候里面采用了 hashCode & (size - 1)的算法,这相当于取模运算 hashCode % size 的一个更高效的实现。正是因为这种算法,我们要求 size 必须是 2 的整次幂,这也能保证在索引不越界的前提下,使得 hash 发生冲突的次数减小。
(3) ThreadLocalMap 中的 set 方法

1 private void set(ThreadLocal<?> key, Object value) {2 ThreadLocal.ThreadLocalMap.Entry[] tab = table;
3 int len = tab.length;
4 //计算索引(重点代码,刚才分析过了)
5 int i = key.threadLocalHashCode & (len-1);
6 /**7 * 使用线性探测法查找元素(重点代码)
8 */9 for (ThreadLocal.ThreadLocalMap.Entry e = tab[i];
10 e != null;
11 e = tab[i = nextIndex(i, len)]) {12 ThreadLocal<?> k = e.get();
13 //ThreadLocal 对应的 key 存在,直接覆盖之前的值 14 if (k == key) {15 e.value = value;
16 return;
17 }18 // key 为 null,但是值不为 null,说明之前的 ThreadLocal 对象已经被回收了,19 // 当前数组中的 Entry 是一个陈旧(stale)的元素 20 if (k == null) {21 //用新元素替换陈旧的元素,这个方法进行了不少的垃圾清理动作,防止内存泄漏 22 replaceStaleEntry(key, value, i);
23 return;
24 }25 }2627 //ThreadLocal 对应的 key 不存在并且没有找到陈旧的元素,则在空元素的位置创建一个新的 Entry。
28 tab[i] = new Entry(key, value);
29 int sz = ++size;
30 /**31 * cleanSomeSlots 用于清除那些 e.get()==null 的元素,32 * 这种数据 key 关联的对象已经被回收,所以这个 Entry(table[index])可以被置 null。
33 * 如果没有清除任何 entry,并且当前使用量达到了负载因子所定义(长度的 2/3),那么进行* rehash(执行一次全表的扫描清理工作)
34 */35 if (!cleanSomeSlots(i, sz) && sz >= threshold)
36 rehash();
37 }

3839 /**40 * 获取环形数组的下一个索引 41 */42 private static int nextIndex(int i, int len) {43 return ((i + 1 < len) ? i + 1 : 0);
44 }45 代码执行流程:
A. 首先还是根据 key 计算出索引 i,然后查找 i 位置上的 Entry,B. 若是 Entry 已经存在并且 key 等于传入的 key,那么这时候直接给这个 Entry 赋新的 value 值,C. 若是 Entry 存在,但是 key 为 null,则调用 replaceStaleEntry 来更换这个 key 为空的 Entry,D. 不断循环检测,直到遇到为 null 的地方,这时候要是还没在循环过程中 return,那么就在这个 null 的位置新建一个 Entry,并且插入,同时 size 增加 1。
最后调用 cleanSomeSlots,清理 key 为 null 的 Entry,最后返回是否清理了 Entry,接下来再判断 sz 是否>= thresgold 达到了 rehash 的条件,达到的话就会调用 rehash 函数执行一次全表的扫描清理。
重点分析 : ThreadLocalMap 使用线性探测法来解决哈希冲突的。
该方法一次探测下一个地址,直到有空的地址后插入,若整个空间都找不到空余的地址,则产生溢出。
举个例子,假设当前 table 长度为 16,也就是说如果计算出来 key 的 hash 值为 14,如果 table[14]上已经有值,并且其 key 与当前 key 不一致,那么就发生了 hash 冲突,这个时候将 14 加 1 得到 15,取 table[15]进行判断,这个时候如果还是冲突会回到 0,取 table[0],以此类推,直到可以插入。
按照上面的描述,可以把 Entry[] table 看成一个环形数组。
