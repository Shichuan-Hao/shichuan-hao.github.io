---


title: "线程池ThreadPoolExecutor实战及其原理分析"
description: "线程池简介线程池(Thread Pool)是一种基于池化思想管理线程的工具,经常出现在多线程服务器中,如 Tomcat。"
author: hsc
date: 2021-08-05 00:00:00 +0800
categories: ['Java 后端', '并发编程']
tags: ['并发编程', 'JUC', '线程池', 'AQS', 'CAS']
toc: true


---

### 1. 线程池简介线程池(Thread Pool)是一种基于池化思想管理线程的工具,经常出现在多线程服务器中,如 Tomcat。
线程过多会带来额外的开销,其中包括创建销毁线程的开销、调度线程的开销等等,同时也降低了计算机的整体性能。线程池维护多个线程,等待监督管理者分配可并发执行的任务。这种做法,一方面避免了处理任务时创建销毁线程开销的代价,另一方面避免了线程数量膨胀导致的过分调度问题,保证了对内核的充分利用。
线程池有如下的优势:
降低资源消耗:通过池化技术重复利用已创建的线程,降低线程创建和销毁造成的损耗。
提高响应速度:任务到达时,无需等待线程创建即可立即执行。
提高线程的可管理性:线程是稀缺资源,如果无限制创建,不仅会消耗系统资源,还会因为线程的不合理分布导致资源调度失衡,降低系统的稳定性。使用线程池可以进行统一的分配、调优和监控。
提供更多更强大的功能:线程池具备可拓展性,允许开发人员向其中增加更多的功能。比如延时定时线程池 ScheduledThreadPoolExecutor,就允许任务延期执行或定期执行。
2. 线程池的使用创建线程池 ThreadPoolExecutor——推荐使用利用 ThreadPoolExecutor 提供的构造方法创建线程池主要看参数最全的构造方法,其他构造方法最终还是会调用该改造方法

线程池的核心参数 corePoolSize:核心线程数,线程池初始化时默认是没有线程的,当任务来临时才开始创建线程去执行任务 maximumPoolSize:最大线程数,在核心线程数已满,且队列已满时,如果池子里的工作线程数小于 maximumPoolSize,则会创建非核心线程执行任务 keepAliveTime:非核心线程数的空闲时间超过 keepAliveTime 就会被自动终止回收掉,但在 corePoolSize=maximumPoolSize 时,该值无效,因为不存在非核心线程 unit:keepAliveTime 的时间单位 workQueue:用于保存线程任务的队列,主要分为无界、有界、同步移交等队列,当池子里的工作线程数大于 corePoolSize,就会将新进来的线程任务放入队列中 ArrayBlockingQueue(有界队列):队列长度有限,当队列满了就需要创建非核心线程执行任务,如果最大线程数已满,则执行拒绝策略 LinkedBlockingQueue(无界队列):队列长度无限,当任务处理速度跟不上任务创建速度,可能会导致内存占用过多或 OOMSynchronousQueue(同步队列):队列不作为任务的缓冲处理,队列长度为 0threadFactory:
创建线程的工厂接口,默认使用 Executors.defaultThreadFactory()
另外可以实现 ThreadFactory 接口,自定义线程工厂 handler:线程池无法继续接收任务时(workQueue 已满和 maximumPoolSize 已满)的拒绝策略 AbortPolicy:默认拒绝策略,中断抛出 RejectedExecutionException 异常 CallerRunsPolicy:让提交任务的主线程来执行任务 DiscardOldestPolicy:丢弃在队列中存在时间最久的任务,重复执行 DiscardPolicy:丢弃任务,不进行任何通知另外可以实现 RejectedExecutionHandler 接口,自定义拒绝策略

以下是一个使用 ThreadPoolExecutor 创建线程池的示例:

1 import java.util.concurrent.ArrayBlockingQueue;
2 import java.util.concurrent.ThreadPoolExecutor;
3 import java.util.concurrent.TimeUnit;
4 import java.util.concurrent.RejectedExecutionHandler;
5 import java.util.concurrent.ThreadPoolExecutor.AbortPolicy;
67 public class ThreadPoolExample2 {89 public static void main(String[] args) {10 // 线程池的核心线程数 11 int corePoolSize = 5;
12 // 线程池的最大线程数 13 int maximumPoolSize = 10;
14 // 线程池的任务队列 15 ArrayBlockingQueue<Runnable> workQueue = new ArrayBlockingQueue<>(100);
16 // 线程池保持空闲的时间 17 long keepAliveTime = 60L;
18 // 时间单位 19 TimeUnit unit = TimeUnit.SECONDS;
20 // 线程池的拒绝策略 21 RejectedExecutionHandler handler = new ThreadPoolExecutor.AbortPolicy();
2223 // 创建线程池 24 ThreadPoolExecutor executor = new ThreadPoolExecutor(25 corePoolSize,26 maximumPoolSize,27 keepAliveTime,28 unit,29 workQueue,30 handler31 );
3233 // 提交任务到线程池 34 for (int i = 0; i < 15; i++) {35 final int taskId = i;
36 executor.execute(() -> {37 System.out.println("Task " + taskId + " is running by " +Thread.currentThread().getName());
38 });

39 }4041 // 关闭线程池 42 executor.shutdown();
43 try {44 // 等待所有任务完成,超时时间为 60 秒 45 if (!executor.awaitTermination(60, TimeUnit.SECONDS)) {46 // 如果超时后任务仍未完成,则强制关闭线程池 47 executor.shutdownNow();
48 }49 } catch (InterruptedException e) {50 // 如果等待过程中被中断,也强制关闭线程池 51 executor.shutdownNow();
52 }5354 System.out.println("All tasks are done or interrupted.");
55 }56 }在这个示例中,我们直接通过 ThreadPoolExecutor 的构造器来创建线程池,并设置了核心线程数、最大线程数、任务队列、空闲线程存活时间以及拒绝策略。然后,我们向线程池提交任务,并在所有任务提交完毕后调用 shutdown()方法来关闭线程池。我们还使用 awaitTermination()方法来等待所有任务完成,如果超时或等待过程中被中断,则调用 shutdownNow()方法强制关闭线程池。
Executors——不推荐使用 Executors 提供了各种线程池类型创建的静态方法,如常见的 newFixedThreadPool、newSingleThreadExecutor、newCachedThreadPool、newSingleThreadScheduledExecutor。

以下是一个使用 Java 中的 ExecutorService 和 Executors 创建线程池的简单示例:
1 import java.util.concurrent.ExecutorService;
2 import java.util.concurrent.Executors;
34 public class ThreadPoolExample {56 public static void main(String[] args) {7 // 创建一个固定大小的线程池 8 ExecutorService executor = Executors.newFixedThreadPool(5);
910 // 提交任务到线程池 11 for (int i = 0; i < 10; i++) {12 final int taskId = i;
13 executor.submit(() -> {14 System.out.println("Task " + taskId + " is running by " +Thread.currentThread().getName());
15 });
16 }1718 // 关闭线程池 19 executor.shutdown();
20 while (!executor.isTerminated()) {21 // 等待所有任务完成 22 }2324 System.out.println("All tasks are done.");
25 }26 }但不提倡使用该种方式创建线程池,在阿里巴巴 JAVA 开发手册,对于线程池创建要求:

提交任务线程池提交任务有两种方法:
无返回值的任务使用 public void execute(Runnable command) 方法提交;
有返回值的任务使用:
Future<?> submit(Runnable task) : 提交 Runnable 任务 Future<T> submit(Runnable task, T result): 提交 Runnable 任务并指定执行结果 Future<T> submit(Callable<T> task) : 提交 Callable 任务如何执行批量任务 1 # 执行批量任务,返回它们的执行结果 2 public <T> List<Future<T>> invokeAll(Collection<? extends Callable<T>> tasks) throwsInterruptedException3 #执行批量任务,返回指定时间内完成的执行结果,取消未完成的任务 4 public <T> List<Future<T>> invokeAll(Collection<? extends Callable<T>> tasks,longtimeout, TimeUnit unit)
5 # 执行批量任务,返回最先完成的执行结果 6 public <T> T invokeAny(Collection<? extends Callable<T>> tasks) throwsInterruptedException, ExecutionException7 #执行批量任务,返回指定时间内最先完成的执行结果,取消未完成的任务 8 public <T> T invokeAny(Collection<? extends Callable<T>> tasks,long timeout, TimeUnitunit)
示例

1 public class InvokeAllDemo {23 public static void main(String[] args) {4 List<Task> tasks = new ArrayList<>();
5 for (int i = 1; i <= 10; i++) {6 tasks.add(new Task(i));
7 }89 //创建线程池 10 ExecutorService threadpool = Executors.newFixedThreadPool(5);
11 try {12 //批量提交任务 13 List<Future<Integer>> futures = threadpool.invokeAll(tasks);
14 for (Future<Integer> future : futures){15 System.out.println(future.get());
16 }1718 } catch (InterruptedException | ExecutionException e) {19 throw new RuntimeException(e);
20 }finally {21 //关闭线程池 22 threadpool.shutdown();
23 }242526 }272829 static class Task implements Callable<Integer> {3031 private int index;
3233 Task(int index) {34 this.index = index;
35 }3637 @Override

38 public Integer call() throws Exception {39 Thread.sleep(1000);
40 return index;
41 }42 }4344 }如何执行定时、延时任务 1 #具备执行定时、延时、周期性任务的线程池 2 public class ScheduledThreadPoolExecutor extends ThreadPoolExecutor implementsScheduledExecutorService {3 #延时执行 Runnable 任务,只执行一次 4 public ScheduledFuture<?> schedule(Runnable command,long delay,TimeUnit unit)
5 #延时执行 Callable 任务,只执行一次 6 public <V> ScheduledFuture<V> schedule(Callable<V> callable,long delay,TimeUnit unit)
如何执行周期、重复性任务 1 #廷时一段时间后,周期性执行 Runnable 任务,周期为固定时间 2 public ScheduledFuture<?> scheduleAtFixedRate(Runnable command,long initialDelay,longperiod,TimeUnit unit)
3 #廷时一段时间后,周期性执行 Runnable 任务,周期为间隔时间 4 public ScheduledFuture<?> scheduleWithFixedDelay(Runnable command,longinitialDelay,long delay,TimeUnit unit)
关闭线程池 shutdownNow():立即关闭线程池,正在执行中的任务和队列中的任务都会被中断,同时返回被中断的队列中的任务列表。

shutdown():关闭线程池,正在执行中的任务和队列中的任务都能执行完成,后续进来的新任务会被执行拒绝策略。
isTerminated():当正在执行的任务和队列中的任务全部都执行完时返回 true。
shutdown 和 shutdownNow 的区别 shutdown shutdownNow 立即关闭线程池 否 是延时关闭线程池 是 否不再接收新任务 是 是继续执行完任务队列中的任务 是 否返回任务队列中的任务 否 是线程池状态 SHUTDOWN STOP 线程池的参数设计分析核心线程数(corePoolSize)
核心线程数的设计需要依据任务的处理时间和每秒产生的任务数量来确定。
例如:一个线程执行一个任务需要 0.1 秒,1 秒就执行 10 个任务;系统 80%的时间每秒都会产生 100 个任务,那么要想在 1 秒内处理完这 100 个任务,就需要 10 个线程。
此时我们就可以设计核心线程数为 10;
当然实际情况不可能这么平均,所以我们一般按照二八原则设计即可,即按照 80%的情况设计核心线程数,剩下的 20%可以利用最大线程数处理;
任务队列长度(workQueue)
任务队列长度,也就是设计 阻塞队列 能缓存多少个任务。
任务队列长度一般设计为:
核心线程数 / 单个任务执行时间 *2 即可;
例如上面的场景中,核心线程数设计为 10,单个任务执行时间为 0.1 秒,则队列长度可以设计为 200 ;
最大线程数(maximumPoolSize)
最大线程数的设计除了需要参照核心线程数的条件外,还需要参照系统每秒产生的最大任务数决定;
例如:上述环境中,如果系统每秒最大产生的任务是 1000 个,那么:

最大线程数 = ( 最大任务数 - 任务队列长度 ) * 单个任务执行时间;
即: 最大线程数 = (1000 - 200 ) * 0.1 = 80 个;
最大空闲时间(keepAliveTime)
这个参数的设计完全参考系统运行环境和硬件压力设定,没有固定的参考值,用户可以根据经验和系统产生任务的时间间隔合理设置一个值即可。
3. 线程池原理分析线程池执行任务的具体流程是怎样的?
ThreadPoolExecutor 中提供了两种执行任务的方法:
1. void execute(Runnable command)
2. Future<?> submit(Runnable task)
实际上 submit 中最终还是调用的 execute()方法,只不过会返回一个 Future 对象,用来获取任务执行结果:
1 public Future<?> submit(Runnable task) {2 if (task == null) throw new NullPointerException();
3 RunnableFuture<Void> ftask = newTaskFor(task, null);
4 execute(ftask);
5 return ftask;
6 }execute(Runnable command)方法执行时会分为三步:

注意:提交一个 Runnable 时,不管当前线程池中的线程是否空闲,只要数量小于核心线程数就会创建新线程。
注意:ThreadPoolExecutor 相当于是非公平的,比如队列满了之后提交的 Runnable 可能会比正在排队的 Runnable 先执行。
线程池的五种状态是如何流转的?
线程池有五种状态:
RUNNING:会接收新任务并且会处理队列中的任务 SHUTDOWN:不会接收新任务并且会处理队列中的任务 STOP:不会接收新任务并且不会处理队列中的任务,并且会中断在处理的任务(注意:一个任务能不能被中断得看任务本身)
TIDYING:所有任务都终止了,线程池中也没有线程了,这样线程池的状态就会转为 TIDYING,一旦达到此状态,就会调用线程池的 terminated()
TERMINATED:terminated()执行完之后就会转变为 TERMINATED 这五种状态并不能任意转换,只会有以下几种转换情况:

### 1. RUNNING -> SHUTDOWN:手动调用 shutdown()触发,或者线程池对象 GC 时会调用 finalize()从而调用 shutdown()
### 2. (RUNNING or SHUTDOWN) -> STOP:调用 shutdownNow()触发,如果先调 shutdown()紧着调 shutdownNow(),就会发生 SHUTDOWN -> STOP
### 3. SHUTDOWN -> TIDYING:队列为空并且线程池中没有线程时自动转换
### 4. STOP -> TIDYING:线程池中没有线程时自动转换(队列中可能还有任务)
### 5. TIDYING -> TERMINATED:terminated()执行完后就会自动转换线程池中的线程是如何关闭的?
我们一般会使用 thread.start()方法来开启一个线程,那如何停掉一个线程呢?
线程池中就是利用线程中断机制来停止线程的。比如 shutdownNow()方法中会调用:
1 void interruptIfStarted() {2 Thread t;
3 if (getState() >= 0 && (t = thread) != null && !t.isInterrupted()) {4 try {5 t.interrupt();
6 } catch (SecurityException ignore) {7 }8 }9 }线程池为什么一定得是阻塞队列?

线程池中的线程在运行过程中,执行完创建线程时绑定的第一个任务后,就会不断的从队列中获取任务并执行,那么如果队列中没有任务了,线程为了不自然消亡,就会阻塞在获取队列任务时,等着队列中有任务过来就会拿到任务从而去执行任务。
通过这种方法能最终确保,线程池中能保留指定个数的核心线程数,关键代码为:
1 try {2 Runnable r = timed ?
3 workQueue.poll(keepAliveTime, TimeUnit.NANOSECONDS) :
4 workQueue.take();
5 if (r != null)
6 return r;
7 timedOut = true;
8 } catch (InterruptedException retry) {9 timedOut = false;
10 }某个线程在从队列获取任务时,会判断是否使用超时阻塞获取,我们可以认为非核心线程会 poll(),核心线程会 take(),非核心线程超过时间还没获取到任务后面就会自然消亡了。
线程发生异常,会被移出线程池吗?
答案是会的,那有没有可能核心线程数在执行任务时都出错了,导致所有核心线程都被移出了线程池?

在源码中,当执行任务时出现异常时,最终会执行 processWorkerExit(),执行完这个方法后,当前线程也就自然消亡了,但是!processWorkerExit()方法中会额外再新增一个线程,这样就能维持住固定的核心线程数。
4. 线程池源码分析线程池源码的基础属性和方法在线程池的源码中,会通过一个 AtomicInteger 类型的变量 ctl,来表示线程池的状态和当前线程池中的工作线程数量。
一个 Integer 占 4 个字节,也就是 32 个 bit,线程池有 5 个状态:
1. RUNNING
2. SHUTDOWN
3. STOP
4. TIDYING
5. TERMINATED2 个 bit 能表示 4 种状态,那 5 种状态就至少需要三个 bit 位,比如在线程池的源码中就是这么来表示的:

1 private static final int COUNT_BITS = Integer.SIZE - 3;
23 private static final int RUNNING = -1 << COUNT_BITS;
4 private static final int SHUTDOWN = 0 << COUNT_BITS;
5 private static final int STOP = 1 << COUNT_BITS;
6 private static final int TIDYING = 2 << COUNT_BITS;
7 private static final int TERMINATED = 3 << COUNT_BITS;
Integer.SIZE 为 32,所以 COUNT_BITS 为 29,最终各个状态对应的二级制为:
1. RUNNING:11100000 00000000 00000000 00000000
2. SHUTDOWN:00000000 00000000 00000000 00000000
3. STOP:00100000 00000000 00000000 00000000
4. TIDYING:01000000 00000000 00000000 00000000
5. TERMINATED:01100000 00000000 00000000 00000000 所以,只需要使用一个 Integer 数字的最高三个 bit,就可以表示 5 种线程池的状态,而剩下的 29 个 bit 就可以用来表示工作线程数,比如,假如 ctl 为:11100000 00000000 00000000 00001010,就表示线程池的状态为 RUNNING,线程池中目前在工作的线程有 10 个,这里说的“在工作”意思是线程活着,要么在执行任务,要么在阻塞等待任务。
同时,在线程池中也提供了一些方法用来获取线程池状态和工作线程数,比如:

1 // 29,二进制为 00000000 00000000 00000000 000111012 private static final int COUNT_BITS = Integer.SIZE - 3;
34 // 00011111 11111111 11111111 111111115 private static final int CAPACITY = (1 << COUNT_BITS) - 1;
67 // ~CAPACITY 为 11100000 00000000 00000000 000000008 // &操作之后,得到就是 c 的高 3 位 9 private static int runStateOf(int c) {10 return c & ~CAPACITY;
11 }1213 // CAPACITY 为 00011111 11111111 11111111 1111111114 // &操作之后,得到的就是 c 的低 29 位 15 private static int workerCountOf(int c) {16 return c & CAPACITY;
17 }同时,还有一个方法:
1 private static int ctlOf(int rs, int wc) {2 return rs | wc;
3 }就是用来把运行状态和工作线程数量进行合并的一个方法,不过传入这个方法的两个 int 数字有限制,rs 的低 29 位都得为 0,wc 的高 3 位都得为 0,这样经过或运算之后,才能得到准确的 ctl。
同时,还有一些相关的方法:

1 private static final int RUNNING = -1 << COUNT_BITS;
2 private static final int SHUTDOWN = 0 << COUNT_BITS;
3 private static final int STOP = 1 << COUNT_BITS;
4 private static final int TIDYING = 2 << COUNT_BITS;
5 private static final int TERMINATED = 3 << COUNT_BITS;
67 // c 状态是否小于 s 状态,比如 RUNNING 小于 SHUTDOWN8 private static boolean runStateLessThan(int c, int s) {9 return c < s;
10 }1112 // c 状态是否大于等于 s 状态,比如 STOP 大于 SHUTDOWN13 private static boolean runStateAtLeast(int c, int s) {14 return c >= s;
15 }1617 // c 状态是不是 RUNNING,只有 RUNNING 是小于 SHUTDOWN 的 18 private static boolean isRunning(int c) {19 return c < SHUTDOWN;
20 }2122 // 通过 cas 来增加工作线程数量,直接对 ctl 进行加 123 // 这个方法没考虑是否超过最大工作线程数的(2 的 29 次方)限制,源码中在调用该方法之前会进行判断的 24 private boolean compareAndIncrementWorkerCount(int expect) {25 return ctl.compareAndSet(expect, expect + 1);
26 }2728 // 通过 cas 来减少工作线程数量,直接对 ctl 进行减 129 private boolean compareAndDecrementWorkerCount(int expect) {30 return ctl.compareAndSet(expect, expect - 1);
31 }前面说到线程池有 5 个状态,这 5 个状态分别表示:
1. RUNNING:线程池正常运行中,可以正常的接受并处理任务
2. SHUTDOWN:线程池关闭了,不能接受新任务,但是线程池会把阻塞队列中的剩余任务执行完,剩余任务都处理完之后,会中断所有工作线程
3. STOP:线程池停止了,不能接受新任务,并且也不会处理阻塞队列中的任务,会中断所有工作线程

### 4. TIDYING:当前线程池中的工作线程都被停止后,就会进入 TIDYING
### 5. TERMINATED:线程池处于 TIDYING 状态后,会执行 terminated()方法,执行完后就会进入 TERMINATED 状态,
在 ThreadPoolExecutor 中 terminated()是一个空方法,可以自定义线程池重写这个方法 execute 方法当执行线程池的 execute 方法时:

1 public void execute(Runnable command) {23 if (command == null)
4 throw new NullPointerException();
56 // 获取 ctl7 // ctl 初始值是 ctlOf(RUNNING, 0),表示线程池处于运行中,工作线程数为 08 int c = ctl.get();
910 // 工作线程数小于 corePoolSize,则添加工作线程,并把 command 作为该线程要执行的任务 11 if (workerCountOf(c) < corePoolSize) {12 // true 表示添加的是核心工作线程,具体一点就是,在 addWorker 内部会判断当前工作线程数是不是超过了 corePoolSize13 // 如果超过了则会添加失败,addWorker 返回 false,表示不能直接开启新的线程来执行任务,而是应该先入队 14 if (addWorker(command, true))
15 return;
1617 // 如果添加核心工作线程失败,那就重新获取 ctl,可能是线程池状态被其他线程修改了 18 // 也可能是其他线程也在向线程池提交任务,导致核心工作线程已经超过了 corePoolSize19 c = ctl.get();
20 }2122 // 线程池状态是否还是 RUNNING,如果是就把任务添加到阻塞队列中 23 if (isRunning(c) && workQueue.offer(command)) {2425 // 在任务入队时,线程池的状态可能也会发生改变 26 // 再次检查线程池的状态,如果线程池不是 RUNNING 了,那就不能再接受任务了,就得把任务从队列中移除,并进行拒绝策略 2728 // 如果线程池的状态没有发生改变,仍然是 RUNNING,那就不需要把任务从队列中移除掉 29 // 不过,为了确保刚刚入队的任务有线程会去处理它,需要判断一下工作线程数,如果为 0,那就添加一个非核心的工作线程 30 // 添加的这个线程没有自己的任务,目的就是从队列中获取任务来执行 31 int recheck = ctl.get();
32 if (! isRunning(recheck) && remove(command))
33 reject(command);
34 else if (workerCountOf(recheck) == 0)

35 addWorker(null, false);
36 }37 // 如果线程池状态不是 RUNNING,或者线程池状态是 RUNNING 但是队列满了,则去添加一个非核心工作线程 38 // 实际上,addWorker 中会判断线程池状态如果不是 RUNNING,是不会添加工作线程的 39 // false 表示非核心工作线程,作用是,在 addWorker 内部会判断当前工作线程数已经超过了 maximumPoolSize,如果超过了则会添加不成功,执行拒绝策略 40 else if (!addWorker(command, false))
41 reject(command);
42 }addWorker 方法 addWorker 方法是核心方法,是用来添加线程的,core 参数表示添加的是核心线程还是非核心线程。
在看这个方法之前,我们不妨先自己来分析一下,什么是添加线程?
实际上就要开启一个线程,不管是核心线程还是非核心线程其实都只是一个普通的线程,而核心和非核心的区别在于:
1. 如果是要添加核心工作线程,那么就得判断目前的工作线程数是否超过 corePoolSizea. 如果没有超过,则直接开启新的工作线程执行任务 b. 如果超过了,则不会开启新的工作线程,而是把任务进行入队
1. 如果要添加的是非核心工作线程,那就要判断目前的工作线程数是否超过 maximumPoolSizea. 如果没有超过,则直接开启新的工作线程执行任务 b. 如果超过了,则拒绝执行任务所以在 addWorker 方法中,首先就要判断工作线程有没有超过限制,如果没有超过限制再去开启一个线程。
并且在 addWorker 方法中,还得判断线程池的状态,如果线程池的状态不是 RUNNING 状态了,那就没必要要去添加线程了,当然有一种特例,就是线程池的状态是 SHUTDOWN,但是队列中有任务,那此时还是需要添加添加一个线程的。
那这种特例是如何产生的呢?
我们前面提到的都是开启新的工作线程,那么工作线程怎么回收呢?不可能开启的工作线程一直活着,因为如果任务由多变少,那也就不需要过多的线程资源,所以线程池中会有机制对开启的工作线程进行回收,如何回收的,后文会提到,我们这里先分析,有没有可能线程池中所有的线程都被回收了,答案的是有的。

首先非核心工作线程被回收是可以理解的,那核心工作线程要不要回收掉呢?其实线程池存在的意义,就是提前生成好线程资源,需要线程的时候直接使用就可以,而不需要临时去开启线程,所以正常情况下,开启的核心工作线程是不用回收掉的,就算暂时没有任务要处理,也不用回收,就让核心工作线程在那等着就可以了。
但是!在线程池中有这么一个参数:allowCoreThreadTimeOut,表示是否允许核心工作线程超时,意思就是是否允许核心工作线程回收,默认这个参数为 false,但是我们可以调用 allowCoreThreadTimeOut(boolean value)来把这个参数改为 true,只要改了,那么核心工作线程也就会被回收了,那这样线程池中的所有工作线程都可能被回收掉,那如果所有工作线程都被回收掉之后,阻塞队列中来了一个任务,这样就形成了特例情况。

1 private boolean addWorker(Runnable firstTask, boolean core) {2 retry:
3 for (;;) {4 int c = ctl.get();
5 int rs = runStateOf(c);
67 // 线程池如果是 SHUTDOWN 状态并且队列非空则创建线程,如果队列为空则不创建线程了 8 // 线程池如果是 STOP 状态则直接不创建线程了 9 // Check if queue empty only if necessary.10 if (rs >= SHUTDOWN &&11 ! (rs == SHUTDOWN &&12 firstTask == null &&13 ! workQueue.isEmpty()))
14 return false;
1516 // 判断工作线程数是否超过了限制 17 // 如果超过限制了,则 return false18 // 如果没有超过限制,则修改 ctl,增加工作线程数,cas 成功则退出外层 retry 循环,去创建新的工作线程 19 // 如果 cas 失败,则表示有其他线程也在提交任务,也在增加工作线程数,此时重新获取 ctl20 // 如果发现线程池的状态发生了变化,则继续回到 retry,重新判断线程池的状态是不是 SHUTDOWN 或 STOP21 // 如果状态没有变化,则继续利用 cas 来增加工作线程数,直到 cas 成功 22 for (;;) {23 int wc = workerCountOf(c);
24 if (wc >= CAPACITY ||25 wc >= (core ? corePoolSize : maximumPoolSize))
26 return false;
27 if (compareAndIncrementWorkerCount(c))
28 break retry;
29 c = ctl.get(); // Re-read ctl30 if (runStateOf(c) != rs)
31 continue retry;
32 // else CAS failed due to workerCount change; retry inner loop33 }34 }3536 // ctl 修改成功,也就是工作线程数+1 成功

37 // 接下来就要开启一个新的工作线程了 3839 boolean workerStarted = false;
40 boolean workerAdded = false;
41 Worker w = null;
42 try {43 // Worker 实现了 Runnable 接口 44 // 在构造一个 Worker 对象时,就会利用 ThreadFactory 新建一个线程 45 // Worker 对象有两个属性:
46 // Runnable firstTask:表示 Worker 待执行的第一个任务,第二个任务会从阻塞队列中获取 47 // Thread thread:表示 Worker 对应的线程,就是这个线程来获取队列中的任务并执行的 48 w = new Worker(firstTask);
4950 // 拿出线程对象,还没有 start51 final Thread t = w.thread;
52 if (t != null) {53 final ReentrantLock mainLock = this.mainLock;
54 mainLock.lock();
55 try {56 // Recheck while holding lock.57 // Back out on ThreadFactory failure or if58 // shut down before lock acquired.59 int rs = runStateOf(ctl.get());
6061 // 如果线程池的状态是 RUNNING62 // 或者线程池的状态变成了 SHUTDOWN,但是当前线程没有自己的第一个任务,那就表示当前调用 addWorker 方法是为了从队列中获取任务来执行 63 // 正常情况下线程池的状态如果是 SHUTDOWN,是不能创建新的工作线程的,但是队列中如果有任务,那就是上面说的特例情况 64 if (rs < SHUTDOWN ||65 (rs == SHUTDOWN && firstTask == null)) {6667 // 如果 Worker 对象对应的线程已经在运行了,那就有问题,直接抛异常 68 if (t.isAlive()) // precheck that t isstartable69 throw newIllegalThreadStateException();
71 // workers 用来记录当前线程池中工作线程,调用线程池的 shutdown 方法时会遍历 worker 对象中断对应线程 72 workers.add(w);
7374 // largestPoolSize 用来跟踪线程池在运行过程中工作线程数的峰值 75 int s = workers.size();
76 if (s > largestPoolSize)
77 largestPoolSize = s;
78 workerAdded = true;
79 }80 } finally {81 mainLock.unlock();
82 }8384 // 运行线程 85 if (workerAdded) {86 t.start();
87 workerStarted = true;
88 }89 }90 } finally {91 // 在上述过程中如果抛了异常,需要从 works 中移除所添加的 work,并且还要修改 ctl,工作线程数-1,表示新建工作线程失败 92 if (! workerStarted)
93 addWorkerFailed(w);
94 }9596 // 最后表示添加工作线程成功 97 return workerStarted;
98 }所以,对于 addWorker 方法,核心逻辑就是:
1. 先判断工作线程数是否超过了限制
2. 修改 ctl,使得工作线程数+1
3. 构造 Work 对象,并把它添加到 workers 集合中
4. 启动 Work 对象对应的工作线程

runWorker 方法那工作线程在运行过程中,到底在做什么呢?
我们看看 Work 的构造方法:
1 Worker(Runnable firstTask) {2 setState(-1); // inhibit interrupts until runWorker3 this.firstTask = firstTask;
4 this.thread = getThreadFactory().newThread(this);
5 }在利用 ThreadFactory 创建线程时,会把 this,也就是当前 Work 对象作为 Runnable 传给线程,所以工作线程运行时,就会执行 Worker 的 run 方法:
1 public void run() {2 // 这个方法就是工作线程运行时的执行逻辑 3 runWorker(this);
4 }

1 final void runWorker(Worker w) {2 // 就是当前工作线程 3 Thread wt = Thread.currentThread();
45 // 把 Worker 要执行的第一个任务拿出来 6 Runnable task = w.firstTask;
7 w.firstTask = null;
89 // 这个地方,后面单独分析中断的时候来分析 10 w.unlock(); // allow interrupts1112 boolean completedAbruptly = true;
13 try {1415 // 判断当前线程是否有自己的第一个任务,如果没有就从阻塞队列中获取任务 16 // 如果阻塞队列中也没有任务,那线程就会阻塞在这里 17 // 但是并不会一直阻塞,在 getTask 方法中,会根据我们所设置的 keepAliveTime 来设置阻塞时间 18 // 如果当前线程去阻塞队列中获取任务时,等了 keepAliveTime 时间,还没有获取到任务,则 getTask 方法返回 null,相当于退出循环 19 // 当然并不是所有线程都会有这个超时判断,主要还得看 allowCoreThreadTimeOut 属性和当前的工作线程数等等,后面单独分析 20 // 目前,我们只需要知道工作线程在执行 getTask()方法时,可能能直接拿到任务,也可能阻塞,也可能阻塞超时最终返回 null21 while (task != null || (task = getTask()) != null) {22 // 只要拿到了任务,就要去执行任务 2324 // Work 先加锁,跟 shutdown 方法有关,先忽略,后面会分析 25 w.lock();
262728 // If pool is stopping, ensure thread is interrupted;
29 // if not, ensure thread is not interrupted. This30 // requires a recheck in second case to deal with31 // shutdownNow race while clearing interrupt3233 // 下面这个 if,最好把整篇文章都看完之后再来看这个 if 的逻辑 3435 // 工作线程在运行过程中

36 // 如果发现线程池的状态变成了 STOP,正常来说当前工作线程的中断标记应该为 true,如果发现中断标记不为 true,则需要中断自己 3738 // 如果线程池的状态不是 STOP,要么是 RUNNING,要么是 SHUTDOWN39 // 但是如果发现中断标记为 true,那是不对的,因为线程池状态不是 STOP,工作线程仍然是要正常工作的,不能中断掉 40 // 就算是 SHUTDOWN,也要等任务都执行完之后,线程才结束,而目前线程还在执行任务的过程中,不能中断 41 // 所以需要重置线程的中断标记,不过 interrupted 方法会自动清空中断标记 42 // 清空为中断标记后,再次判断一下线程池的状态,如果又变成了 STOP,那就仍然中断自己 4344 // 中断了自己后,会把当前任务执行完,在下一次循环调用 getTask()方法时,从阻塞队列获取任务时,阻塞队列会负责判断当前线程的中断标记 45 // 如果发现中断标记为 true,那就会抛出异常,最终退出 while 循环,线程执行结束 46 if ((runStateAtLeast(ctl.get(), STOP) ||47 (Thread.interrupted() &&48 runStateAtLeast(ctl.get(), STOP))) &&49 !wt.isInterrupted())
50 wt.interrupt();
515253 try {54 // 空方法,给自定义线程池来实现 55 beforeExecute(wt, task);
56 Throwable thrown = null;
57 try {58 // 执行任务 59 // 注意执行任务时可能会抛异常,如果抛了异常会先依次执行三个 finally,从而导致 completedAbruptly = false 这行代码没有执行 60 task.run();
61 } catch (RuntimeException x) {62 thrown = x; throw x;
63 } catch (Error x) {64 thrown = x; throw x;
65 } catch (Throwable x) {66 thrown = x; throw new Error(x);
67 } finally {68 // 空方法,给自定义线程池来实现 69 afterExecute(task, thrown);
70 }

71 } finally {72 task = null;
73 w.completedTasks++; // 跟踪当前 Work 总共执行了多少了任务 74 w.unlock();
75 }76 }7778 // 正常退出了 While 循环 79 // 如果是执行任务的时候抛了异常,虽然也退出了循环,但是是不会执行这行代码的,只会直接进去下面的 finally 块中 8081 // 所以,要么是线程从队列中获取任务时阻塞超时了从而退出了循环会进入到这里 82 // 要么是线程在阻塞的过程中被中断了,在 getTask()方法中会处理中断的情况,如果被中断了,那么 getTask()方法会返回 null,从而退出循环 83 // completedAbruptly=false,表示线程正常退出 84 completedAbruptly = false;
85 } finally {86 // 因为当前线程退出了循环,如果不做某些处理,那么这个线程就运行结束了,就是上文说的回收(自然消亡)掉了,线程自己运行完了也就结束了 87 // 但是如果是由于执行任务的时候抛了异常,那么这个线程不应该直接结束,而应该继续从队列中获取下一个任务 88 // 可是代码都执行到这里了,该怎么继续回到 while 循环呢,怎么实现这个效果呢?
89 // 当然,如果是由于线程被中断了,或者线程阻塞超时了,那就应该正常的运行结束 90 // 只不过有一些善后工作要处理,比如修改 ctl,工作线程数-191 processWorkerExit(w, completedAbruptly);
92 }93 }processWorkerExit 方法

1 private void processWorkerExit(Worker w, boolean completedAbruptly) {23 // 如果 completedAbruptly 为 true,表示是执行任务的时候抛了异常,那就修改 ctl,工作线程数-14 // 如果 completedAbruptly 为 false,表示是线程阻塞超时了或者被中断了,实际上也要修改 ctl,工作线程数-15 // 只不过在 getTask 方法中已经做过了,这里就不用再做一次了 6 if (completedAbruptly) // If abrupt, then workerCount wasn't adjusted7 decrementWorkerCount();
89 final ReentrantLock mainLock = this.mainLock;
10 mainLock.lock();
11 try {12 // 当前 Work 要运行结束了,将完成的任务数累加到线程池上 13 completedTaskCount += w.completedTasks;
1415 // 将当前 Work 对象从 workers 中移除 16 workers.remove(w);
17 } finally {18 mainLock.unlock();
19 }2021 // 因为当前是处理线程退出流程中,所以要尝试去修改线程池的状态为 TINDYING22 tryTerminate();
232425 int c = ctl.get();
26 // 如果线程池的状态为 RUNNING 或者 SHUTDOWN,则可能要替补一个线程 27 if (runStateLessThan(c, STOP)) {2829 // completedAbruptly 为 false,表示线程是正常要退出了,则看是否需要保留线程 30 if (!completedAbruptly) {3132 // 如果 allowCoreThreadTimeOut 为 true,但是阻塞队列中还有任务,那就至少得保留一个工作线程来处理阻塞队列中的任务 33 // 如果 allowCoreThreadTimeOut 为 false,那 min 就是 corePoolSize,表示至少得保留 corePoolSize 个工作线程活着 34 int min = allowCoreThreadTimeOut ? 0 : corePoolSize;
35 if (min == 0 && ! workQueue.isEmpty())
36 min = 1;

3738 // 如果当前工作线程数大于等于 min,则表示符合所需要保留的最小线程数,那就直接 return,不会调用下面的 addWorker 方法新开一个工作线程了 39 if (workerCountOf(c) >= min)
40 return; // replacement not needed41 }4243 // 如果线程池的状态为 RUNNING 或者 SHUTDOWN44 // 如果 completedAbruptly 为 true,表示当前线程是执行任务时抛了异常,那就得新开一个工作线程 45 // 如果 completedAbruptly 为 false,但是不符合所需要保留的最小线程数,那也得新开一个工作线程 46 addWorker(null, false);
47 }48 }总结一下,某个工作线程正常情况下会不停的循环从阻塞队列中获取任务来执行,正常情况下就是通过阻塞来保证线程永远活着,但是会有一些特殊情况:
1. 如果线程被中断了,那就会退出循环,然后做一些善后处理,比如 ctl 中的工作线程数-1,然后自己运行结束
2. 如果线程阻塞超时了,那也会退出循环,此时就需要判断线程池中的当前工作线程够不够,比如是否有 corePoolSize 个工作线程,如果不够就需要新开一个线程,然后当前线程自己运行结束,这种看上去效率比较低,但是也没办法,当然如果当前工作线程数足够,那就正常,自己正常的运行结束即可
3. 如果线程是在执行任务的时候抛了移除,从而退出循环,那就直接新开一个线程作为替补,当然前提是线程池的状态是 RUNNINGgetTask 方法上面一直提到了 getTask 这个放,我们来看看这个方法。

1 private Runnable getTask() {2 boolean timedOut = false; // Did the last poll() time out?
34 for (;;) {5 int c = ctl.get();
6 int rs = runStateOf(c);
78 // Check if queue empty only if necessary.9 // 如果线程池状态是 STOP,表示当前线程不需要处理任务了,那就修改 ctl 工作线程数-110 // 如果线程池状态是 SHUTDOWN,但是阻塞队列中为空,表示当前任务没有任务要处理了,那就修改 ctl 工作线程数-111 // return null 表示当前线程无需处理任务,线程退出 12 if (rs >= SHUTDOWN && (rs >= STOP || workQueue.isEmpty())) {13 decrementWorkerCount();
14 return null;
15 }1617 // 当前工作线程数 18 int wc = workerCountOf(c);
1920 // Are workers subject to culling?
21 // 用来判断当前线程是无限阻塞还是超时阻塞,如果一个线程超时阻塞,那么一旦超时了,那么这个线程最终就会退出 22 // 如果是无限阻塞,那除非被中断了,不然这个线程就一直等着获取队列中的任务 2324 // allowCoreThreadTimeOut 为 true,表示线程池中的所有线程都可以被回收掉,则当前线程应该直接使用超时阻塞,一旦超时就回收 25 // allowCoreThreadTimeOut 为 false,则要看当前工作线程数是否超过了 corePoolSize,如果超过了,则表示超过部分的线程要用超时阻塞,一旦超时就回收 2627 boolean timed = allowCoreThreadTimeOut || wc > corePoolSize;
2829 // 如果工作线程数超过了工作线程的最大限制或者线程超时了,则要修改 ctl,工作线程数减 1,并且 return null30 // return null 就会导致外层的 while 循环退出,从而导致线程直接运行结束 31 // 直播课程里会细讲 timed && timedOut32 if ((wc > maximumPoolSize || (timed && timedOut))
33 && (wc > 1 || workQueue.isEmpty())) {34 if (compareAndDecrementWorkerCount(c))

35 return null;
36 continue;
37 }383940 try {41 // 要么超时阻塞,要么无限阻塞 42 Runnable r = timed ? workQueue.poll(keepAliveTime,TimeUnit.NANOSECONDS) : workQueue.take();
4344 // 表示没有超时,在阻塞期间获取到了任务 45 if (r != null)
46 return r;
4748 // 超时了,重新进入循环,上面的代码会判断出来当前线程阻塞超时了,最后 return null,线程会运行结束 49 timedOut = true;
50 } catch (InterruptedException retry) {51 // 从阻塞队列获取任务时,被中断了,也会再次进入循环,此时并不是超时,但是重新进入循环后,会判断线程池的状态 52 // 如果线程池的状态变成了 STOP 或者 SHUTDOWN,最终也会 return null,线程会运行结束 53 // 但是如果线程池的状态仍然是 RUNNING,那当前线程会继续从队列中去获取任务,表示忽略了本次中断 54 // 只有通过调用线程池的 shutdown 方法或 shutdownNow 方法才能真正中断线程池中的线程 55 timedOut = false;
56 }57 }58 }特别注意:只有通过调用线程池的 shutdown 方法或 shutdownNow 方法才能真正中断线程池中的线程。
因为在 java,中断一个线程,只是修改了该线程的一个标记,并不是直接 kill 了这个线程,被中断的线程到底要不要消失,由被中断的线程自己来判断,比如上面代码中,线程遇到了中断异常,它可以选择什么都不做,那线程就会继续进行外层循环,如果选择 return,那就退出了循环,后续就会运行结束从而消失。

shutdown 方法调用线程池的 shutdown 方法,表示要关闭线程池,不接受新任务,但是要把阻塞队列中剩余的任务执行完。
根据前面 execute 方法的源码,只要线程池的状态不是 RUNNING,那么就表示线程池不接受新任务,所以 shutdown 方法要做的第一件事情就是修改线程池状态。
那第二件事情就是要中断线程池中的工作线程,这些工作线程要么在执行任务,要么在阻塞等待任务:
1. 对于在阻塞等待任务的线程,直接中断即可,
2. 对于正在执行任务的线程,其实只要等它们把任务执行完,就可以中断了,因为此时线程池不能接受新任务,所以正在执行的任务就是最后剩余的任务 1 public void shutdown() {2 final ReentrantLock mainLock = this.mainLock;
3 mainLock.lock();
4 try {5 checkShutdownAccess();
6 // 修改 ctl,将线程池状态改为 SHUTDOWN7 advanceRunState(SHUTDOWN);
8 // 中断工作线程 9 interruptIdleWorkers();
10 // 空方法,给子类扩展使用 11 onShutdown(); // hook for ScheduledThreadPoolExecutor12 } finally {13 mainLock.unlock();
14 }15 // 调用 terminated 方法 16 tryTerminate();
17 }

1 private void interruptIdleWorkers() {2 interruptIdleWorkers(false);
3 }456 private void interruptIdleWorkers(boolean onlyOne) {7 final ReentrantLock mainLock = this.mainLock;
8 mainLock.lock();
9 try {10 // 遍历所有正在工作的线程,要么在执行任务,要么在阻塞等待任务 11 for (Worker w : workers) {12 Thread t = w.thread;
1314 // 如果线程没有被中断,并且能够拿到锁,就中断线程 15 // Worker 在执行任务时会先加锁,执行完任务之后会释放锁 16 // 所以只要这里拿到了锁,就表示线程空出来了,可以中断了 17 if (!t.isInterrupted() && w.tryLock()) {18 try {19 t.interrupt();
20 } catch (SecurityException ignore) {21 } finally {22 w.unlock();
23 }24 }25 if (onlyOne)
26 break;
27 }28 } finally {29 mainLock.unlock();
30 }31 }不过还有一个种情况,就是目前所有工作线程都在执行任务,但是阻塞队列中还有剩余任务,那逻辑应该就是这些工作线程执行完当前任务后要继续执行队列中的剩余任务,但是根据我们看到的 shutdown 方法的逻辑,发现这些工作线程在执行完当前任务后,就会释放锁,那就可能会被中断掉,那队列中剩余的任务怎么办呢?

工作线程一旦被中断,就会进入 processWorkerExit 方法,根据前面的分析,我们发现,在这个方法中会会线程池状态为 SHUTDOWN 进行判断,会重新生成新的工作线程,那么这样就能保证队列中剩余的任务一定会被执行完。
shutdownNow 方法看懂了 shutdown 方法,再来看 shutdownNow 方法就简单了。
1 public List<Runnable> shutdownNow() {2 List<Runnable> tasks;
3 final ReentrantLock mainLock = this.mainLock;
4 mainLock.lock();
5 try {6 checkShutdownAccess();
7 // 修改 ctl,将线程池状态改为 STOP8 advanceRunState(STOP);
9 // 中断工作线程 10 interruptWorkers();
11 // 返回阻塞队列中剩余的任务 12 tasks = drainQueue();
13 } finally {14 mainLock.unlock();
15 }1617 // 调用 terminated 方法 18 tryTerminate();
19 return tasks;
20 }

1 private void interruptWorkers() {2 final ReentrantLock mainLock = this.mainLock;
3 mainLock.lock();
4 try {5 // 中断所有工作线程,不管有没有在执行任务 6 for (Worker w : workers)
7 w.interruptIfStarted();
8 } finally {9 mainLock.unlock();
10 }11 }121314 void interruptIfStarted() {15 Thread t;
1617 // 只要线程没有被中断,那就中断线程,中断的线程虽然也会进入 processWorkerExit 方法,但是该方法中判断了线程池的状态 18 // 线程池状态为 STOP 的情况下,不会再开启新的工作线程了 19 // 这里 getState>-0 表示,一个工作线程在创建好,但是还没运行时,这时 state 为-1,可以看看 Worker 的构造方法就知道了 20 // 表示一个工作线程还没开始运行,不能被中断,就算中断也没意义,都还没运行 21 if (getState() >= 0 && (t = thread) != null && !t.isInterrupted()) {22 try {23 t.interrupt();
24 } catch (SecurityException ignore) {25 }26 }27 }mainLock

在上述源码中,发现很多地方都会用到 mainLock,它是线程池中的一把全局锁,主要是用来控制 workers 集合的并发安全,因为如果没有这把全局锁,就有可能多个线程公用同一个线程池对象,如果一个线程在向线程池提交任务,一个线程在 shutdown 线程池,如果不做并发控制,那就有可能线程池 shutdown 了,但是还有工作线程没有被中断,如果 1 个线程在 shutdown,99 个线程在提交任务,那么最终就可能导致线程池关闭了,但是线程池中的很多线程都没有停止,仍然在运行,这肯定是不行,所以需要这把全局锁来对 workers 集合的操作进行并发安全控制。
到此,线程池中的所有核心方法的源码都分析一遍,自我感觉良好,不知道你啥感觉,哈哈,希望你能看懂,看不懂的欢迎交流。
