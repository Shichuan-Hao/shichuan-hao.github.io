---



title: "3 CyclicBarrier的源码分析"
description: "CyclicBarrier 的源码分析与 CountDownLatch、Semaphore 直接基于 AQS 实现不同"
author: hsc
date: 2021-12-31 00:00:00 +0800
categories: ['Java 后端', '并发编程']
tags: ['并发编程', 'JUC', 'AQS']
toc: true



---

#### 8.3 CyclicBarrier 的源码分析

CyclicBarrier 的源码分析与 CountDownLatch、Semaphore 直接基于 AQS 实现不同,CyclicBarrier 是基于 ReentrantLock +ConditionObject 实现的,间接基于 AQS 实现的。
CyclicBarrier 内部结构 Generation,静态内部类,持有布尔类型的属性 broken,默认为 false,只有在重置方法 reset()、执行出现异常或中断调用 breakBarrier() ,属性会被设置为 true。
nextGenerate() 重置 CyclicBarrier 的计数器和 generation 属性。
breakBarrier() 任务执行中断、异常、被重置,将 Generation 中的布尔类型属性设置为 true,将 Waiter 队列中的线程转移到 AQS 队列中,待执行完 unlock 方法后,唤醒 AQS 队列中的挂起线程。
await() :CyclicBarrier 的核心方法,计数器递减处理。
构造函数构造参数重载,最终调用的是 CyclicBarrier(int, Runnable),详情如下:

1 public CyclicBarrier(int parties) {2 this(parties, null);
3 }45 public CyclicBarrier(int parties, Runnable barrierAction) {6 // 参数合法性校验 7 if (parties <= 0) throw new IllegalArgumentException();
8 // final 修饰,所有线程执行完成归为或重置时 使用 9 this.parties = parties;
10 // 在 await 方法中计数值,表示还有多少线程待执行 await11 this.count = parties;
12 // 当计数 count 为 0 时 ,执行此 Runnnable,再唤醒被阻塞的线程 13 this.barrierCommand = barrierAction;
14 }CyclicBarrier 属性核心方法源码分析 await()
在 CyclicBarrier 中,await 有重载方法。 await()表示会一直等待指定数量的线程未准备就绪(执行 await 方法);await(timout, unit)表示等待 timeout 时间后,指定数量的线程未准备就绪,抛出 TimeoutException 超时异常。
CyclicBarrier#await 详情如下:

1 // 执行没有超时时间的 await2 public int await() throws InterruptedException, BrokenBarrierException {3 try {4 // 执行 dowait()
5 return dowait(false, 0L);
6 } catch (TimeoutException toe) {7 throw new Error(toe);
8 }9 }1011 // 执行有超时时间的 await12 public int await(long timeout, TimeUnit unit)
13 throws InterruptedException,14 BrokenBarrierException,15 TimeoutException {16 return dowait(true, unit.toNanos(timeout));
17 }await 最终调用 dowait()方法,CyclicBarrier#dowait 详情如下:

1 private int dowait(boolean timed, long nanos) throws InterruptedException,BrokenBarrierException, TimeoutException {2 // 获取锁对象 3 final ReentrantLock lock = this.lock;
4 // 加锁 5 lock.lock();
6 try {7 // 获取 generation 对象 8 final Generation g = generation;
910 // 这组线程中在执行过程中是否异常、超时、中断、重置 11 if (g.broken)
12 throw new BrokenBarrierException();
1314 // 这组线程被中断,重置标识与计数值,15 // 将 Waiter 队列中的线程转移到 AQS 队列,抛出 InterruptedException16 if (Thread.interrupted()) {17 breakBarrier();
18 throw new InterruptedException();
19 }2021 // 计数值 - 122 int index = --count;
23 // 这组线程都已准备就绪 24 if (index == 0) {25 // 执行结果标识 26 boolean ranAction = false;
27 try {28 // 若使用 2 个参数的有参构造,就传入了自实现任务,index == 0,先执行 CyclicBarrier 有参的任务 29 // 此处设计与 FutureTask 构造参数设计类似 30 final Runnable command = barrierCommand;
31 if (command != null)
32 // 执行任务 33 command.run();
34 // 执行完成,设置为 true35 ranAction = true;
36 // CyclicBarrier 属性归位 37 nextGeneration();

38 return 0;
39 } finally {40 // 执行过程中出现问题 41 if (!ranAction)
42 // 重置标识与计数值,将 Waiter 队列中的线程转移到 AQS 队列 43 breakBarrier();
44 }45 }4647 // -- 之后,count 不为 0,表示还有线程在等待 48 // 自旋 直到被中断、超时、异常、 count = 049 for (;;) {50 try {51 // 未设置超时时间 52 if (!timed)
53 // 挂起线程,将线程转移到 Condition 队列 54 trip.await();
55 // 未达到等待时间 56 else if (nanos > 0L)
57 // 挂起线程,并返回剩余等待时间 58 nanos = trip.awaitNanos(nanos);
59 } catch (InterruptedException ie) {60 // 中断异常 61 if (g == generation && ! g.broken) {62 breakBarrier();
63 throw ie;
64 } else {65 // 线程中断 66 Thread.currentThread().interrupt();
67 }68 }6970 // 该组线程被中断、执行异常、超时,抛出 BrokenBarrierException 异常 71 if (g.broken)
72 throw new BrokenBarrierException();
7374 if (g != generation)
75 return index;
77 // 超时,抛出异常 TimeoutException78 if (timed && nanos <= 0L) {79 breakBarrier();
80 throw new TimeoutException();
81 }82 }83 } finally {84 // 释放锁资源 85 lock.unlock();
86 }87 }breakBarrier() - 结束 CyclicBarrier 的执行 1 // 结束 CyclicBarrier 的执行 2 private void breakBarrier() {3 // 设置线程执行过程中是否异常、中断、重置标识 4 generation.broken = true;
5 // 重置计数值 6 count = parties;
7 // 将 Condition 队列中的 Node 转移到 AQS 队列中,等到执行完 unlock,AQS 队列中的挂起线程会被唤醒 8 // 有后继节点的,设置 ws = -1;
9 // 无后继节点的,设置 ws = 010 trip.signalAll();
11 }reset() - 重置 CyclicBarrier

1 // 重置 CyclicBarrier2 public void reset() {3 // 获取锁对象 4 final ReentrantLock lock = this.lock;
5 // 加锁 6 lock.lock();
7 try {8 // 设置当前 generation 属性,并将 Waiter 队列中线程转移到 AQS 队列 9 breakBarrier();
10 // 重置 generation 属性、计数值 11 nextGeneration();
12 } finally {13 // 释放锁 14 lock.unlock();
15 }16 }nextGeneration() - CyclicBarrier 归位 1 private void nextGeneration() {2 // 将 Waiter 队列中线程转移到 AQS 队列 3 trip.signalAll();
4 // 计数值、 generation 归位 5 count = parties;
6 generation = new Generation();
7 }总结 CyclicBarrier 基于 ReentrantLock + ConditionObject 实现,CyclicBarrier 的构造函数中必须指定 parties,同时对象 generation,内部持有布尔型属性表示当前 CyclicBarrier 执行过程中是否有超时、异常、中断的情况。
parties 是初始待执行线程数,在构造函数中会将 parties 赋给计数值 count,每当一个线程执行 await(),count 就会减 1。

当 count 被减为 0 时,代表所有线程都准备就绪,此时判断构造函数是否初始化了 barrierCommand 属性,若对 barrierCommand 属性做了赋值,优先执行 barrierCommand 任务;
barrierCommand 任务执行完成,再将 Waiter 队列中的线程转移到 AQS 队列中,执行完 unlock,唤醒 AQS 队列中的线程;计数值 count、generation 归位。
