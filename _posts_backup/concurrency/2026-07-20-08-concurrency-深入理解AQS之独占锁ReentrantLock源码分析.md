---
title: "深入理解AQS之独占锁ReentrantLock源码分析"
description: "主讲老师:Fox 有道云笔记链接:https://note.youdao.com/s/YlbEAToq 1. 管程 — Java同步的设计思想 管程:指的是管理共享变量以及对共享变量的操作过程,让他们支持并发。 互斥:同一时刻只允许一个线程访问共享资源; 同步:线程之间如何通信、协作。 MESA模型 在管程的发展史上,先后出现过三种不同的管程模型,分别是Hasen模型、Hoare模型和MESA模"
author: hsc
date: 2026-07-20 00:00:00 +0800
categories: ['Java 后端', '并发编程']
tags: ['并发编程', '多线程', 'JUC', 'AQS', '线程池', '源码分析', '锁']
toc: true
---

> 本文整理自《三、并发编程专题》课程笔记，共 18 页。

主讲老师:Fox
有道云笔记链接:https://note.youdao.com/s/YlbEAToq
1. 管程 — Java同步的设计思想
管程:指的是管理共享变量以及对共享变量的操作过程,让他们支持并发。
互斥:同一时刻只允许一个线程访问共享资源;
同步:线程之间如何通信、协作。
MESA模型
在管程的发展史上,先后出现过三种不同的管程模型,分别是Hasen模型、Hoare模型和MESA模
型。现在正在广泛使用的是MESA模型。
管程中引入了条件变量的概念,而且每个条件变量都对应有一个等待队列。条件变量和等待队列的作
用是解决线程之间的同步问题。
Java中针对管程有两种实现
一种是基于Object的Monitor机制,用于synchronized内置锁的实现
一种是抽象队列同步器AQS,用于JUC包下Lock锁机制的实现
示例代码

1 @Slf4j
2 public class ConditionDemo2 {
3
4 private static final ReentrantLock lock = new ReentrantLock();
5 private static final Condition condition = lock.newCondition();
6
7 public static void main(String[] args) throws InterruptedException {
8 new Thread(() -> {
9 log.debug("t1开始执行....");
10 lock.lock();
11 try {
12 log.debug("t1获取锁....");
13 // 让线程在obj上一直等待下去
14 condition.await();
15 } catch (InterruptedException e) {
16 e.printStackTrace();
17 } finally {
18 lock.unlock();
19 log.debug("t1执行完成....");
20 }
21 }, "t1").start();
22
23 new Thread(() -> {
24 log.debug("t2开始执行....");
25 lock.lock();
26 try {
27 log.debug("t2获取锁....");
28 // 让线程在obj上一直等待下去
29 condition.await();
30 } catch (InterruptedException e) {
31 e.printStackTrace();
32 } finally {
33 lock.unlock();
34 log.debug("t2执行完成....");
35 }
36 }, "t2").start();
37
38 // 主线程两秒后执行

39 Thread.sleep(2000);
40 log.debug("准备获取锁,去唤醒 condition上阻塞的线程");
41 lock.lock();
42 try {
43 // 唤醒condition上所有阻塞的线程
44 condition.signalAll();
45 log.debug("唤醒condition上阻塞的线程");
46 } catch (Exception e) {
47 e.printStackTrace();
48 } finally {
49 lock.unlock();
50 }
51
52
53 }
54 }
2. AQS原理分析
2.1 什么是AQS
java.util.concurrent包中的大多数同步器实现都是围绕着共同的基础行为,比如等待队列、条件队
列、独占获取、共享获取等,而这些行为的抽象就是基于AbstractQueuedSynchronizer(简称AQS)
实现的,AQS是一个抽象同步框架,可以用来实现一个依赖状态的同步器。
JDK中提供的大多数的同步器如Lock, Latch, Barrier等,都是基于AQS框架来实现的
一般是通过一个内部类Sync继承 AQS
将同步器所有调用都映射到Sync对应的方法
AQS具备的特性:
阻塞等待队列
共享/独占
公平/非公平
可重入
允许中断

2.2 AQS核心结构
1 private volatile int state;//共享变量,使用volatile修饰保证线程可见性
2 //返回同步状态的当前值
3 protected final int getState() {
4 return state;
5 }
6 // 设置同步状态的值
7 protected final void setState(int newState) {
8 state = newState;
9 }
10 //原子地(CAS操作)将同步状态值设置为给定值update如果当前同步状态的值等于expect(期望值)
11 protected final boolean compareAndSetState(int expect, int update) {
12 return unsafe.compareAndSwapInt(this, stateOffset, expect, update);
13 }
AQS内部维护属性volatile int state
state表示资源的可用状态
State三种访问方式:
getState()
setState()
compareAndSetState()
定义了两种资源访问方式:
Exclusive-独占,只有一个线程能执行,如ReentrantLock
Share-共享,多个线程可以同时执行,如Semaphore/CountDownLatch
AQS实现时主要实现以下几种方法:
isHeldExclusively():该线程是否正在独占资源。只有用到condition才需要去实现它。
tryAcquire(int):独占方式。尝试获取资源,成功则返回true,失败则返回false。
tryRelease(int):独占方式。尝试释放资源,成功则返回true,失败则返回false。
tryAcquireShared(int):共享方式。尝试获取资源。负数表示失败;0表示成功,但没有剩余可用资源;正数表示
成功,且有剩余资源。
tryReleaseShared(int):共享方式。尝试释放资源,如果释放后允许唤醒后续等待结点返回true,否则返回
false。
2.3 AQS定义两种队列

同步等待队列: 主要用于维护获取锁失败时入队的线程。
条件等待队列: 调用await()的时候会释放锁,然后线程会加入到条件队列,调用signal()唤醒的时候会把条件队
列中的线程节点移动到同步队列中,等待再次获得锁。
AQS 定义了5个队列中节点状态:
1. 值为0,初始化状态,表示当前节点在sync队列中,等待着获取锁。
2. CANCELLED,值为1,表示当前的线程被取消;
3. SIGNAL,值为-1,表示当前节点的后继节点包含的线程需要运行,也就是unpark;
4. CONDITION,值为-2,表示当前节点在等待condition,也就是在condition队列中;
5. PROPAGATE,值为-3,表示当前场景下后续的acquireShared能够得以执行;
同步等待队列
AQS当中的同步等待队列也称CLH队列,CLH队列是Craig、Landin、Hagersten三人发明的一种基
于双向链表数据结构的队列,是FIFO先进先出线程等待队列,Java中的CLH队列是原CLH队列的一个
变种,线程由原自旋机制改为阻塞机制。
AQS 依赖CLH同步队列来完成同步状态的管理:
当前线程如果获取同步状态失败时,AQS则会将当前线程已经等待状态等信息构造成一个节点(Node)并将其
加入到CLH同步队列,同时会阻塞当前线程
当同步状态释放时,会把首节点唤醒(公平锁),使其再次尝试获取同步状态。
通过signal或signalAll将条件队列中的节点转移到同步队列。(由条件队列转化为同步队列)
条件等待队列
AQS中条件队列是使用单向列表保存的,用nextWaiter来连接:
调用await方法阻塞线程;
当前线程存在于同步队列的头结点,调用await方法进行阻塞(从同步队列转化到条件队列)
2.4 基于AQS实现一把独占锁
思考: 基于AQS 如何设计一把独占锁?

1 /**
2 * @author Fox
3 * 基于AQS实现一把独占锁
4 */
5 public class TulingLock extends AbstractQueuedSynchronizer{
6
7 @Override
8 protected boolean tryAcquire(int unused) {
9 //cas 加锁 state=0
10 if (compareAndSetState(0, 1)) {
11 setExclusiveOwnerThread(Thread.currentThread());
12 return true;
13 }
14
15 return false;
16 }
17
18 @Override
19 protected boolean tryRelease(int unused) {
20 //释放锁
21 setExclusiveOwnerThread(null);
22 setState(0);
23 return true;
24 }
25
26 public void lock() {
27 acquire(1);
28 }
29
30 public boolean tryLock() {
31 return tryAcquire(1);
32 }
33
34 public void unlock() {
35 release(1);
36 }
37
38 public boolean isLocked() {

39 return getState() != 0;
40 }
41
42
43 }
3. ReentrantLock源码分析
ReentrantLock是一种基于AQS框架的应用实现,是JDK中的一种线程并发访问的同步手段,它的
功能类似于synchronized是一种互斥锁,可以保证线程安全。
ReentrantLock使用方式
1 public class ReentrantLockTest {
2 private final ReentrantLock lock = new ReentrantLock();
3 // ...
4
5 public void doSomething() {
6 lock.lock(); // block until condition holds
7 try {
8 // ... method body
9 } finally {
10 lock.unlock();
11 }
12 }
13 }
3.1 ReentrantLock原理
ReentrantLock基于 AQS + CAS 实现。
lock()流程图

ReentrantLock基于抽象队列同步器AQS + CAS 实现的加锁、释放锁。ReentrantLock实现了公平锁、
非公平锁,公平锁与非公平锁唯一的区别在于,非公平锁不会判断等待队列中是否节点等待获取锁,
而是直接尝试获取锁,获取不到,再将当前线程节点添加进等待队列的尾节点,判断当前线程节点是
否挂起。
unlock()流程图
ReentrantLock释放锁的流程较为简单,优先判断持有锁资源的线程是否为当前线程,若不为当前线程
抛出异常;若为当前线程,AQS的state的属性值减1,再判断减1后的值是否为0,若为0表示当前线程
彻底释放锁资源,唤醒等待队列中的挂起线程节点,开始抢占锁资源。
3.2 ReentrantLock源码分析
构造函数
1 private final Sync sync;
2
3 // 默认使用非公平锁
4 public ReentrantLock() {
5 sync = new NonfairSync();
6 }
7
8 // fair=true,公平锁;否则,非公平锁
9 public ReentrantLock(boolean fair) {
10 sync = fair ? new FairSync() : new NonfairSync();
11 }
Sync是ReentrantLock的抽象静态内部类,继承自AQS(AbstractQueuedSynchronizer) - 抽象队列同步
器,AQS中定义了锁的基本行为,AQS中用volatile修饰的state表示当前锁重入的次数。
NonfairSync、FairSync是ReentrantLock的静态内部类,继承ReentrantLock$Sync,NonfairSync实现
非公平锁,FairSync实现公平锁。
lock()加锁

1 private final Sync sync;
2
3 // 加锁
4 public void lock() {
5 sync.lock();
6 }
公平锁
调用AQS的acquire方法。ReentrantLock$FairSync#lock() 核心代码:
1 // 加锁
2 final void lock() {
3 acquire(1);
4 }
非公平锁
通过CAS尝试获取锁(将AQS的state由0修改为1),若成功,代表当前线程获取锁资源成功;若失败
调用AQS的acquire方法。ReentrantLock$NonfairSync#lock() 核心代码:
1 // 加锁
2 final void lock() {
3 // 获取锁资源,CAS 修改 AQS 的 state 属性值,,获取成功,设置当前线程
4 if (compareAndSetState(0, 1))
5 setExclusiveOwnerThread(Thread.currentThread());
6 // 获取失败,执行AQS的acquire
7 else
8 acquire(1);
9 }
acquire()
acquire()方法是Sync父类AQS中的方法,AbstractQueuedSynchronizer#acquire() 核心代码:

1 // 获取锁资源
2 public final void acquire(int arg) {
3 // 尝试获取锁资源
4 if (!tryAcquire(arg) &&
5 // 当前线程为获取到锁资源,加入等待队列,同时挂起线程,等待唤醒
6 acquireQueued(addWaiter(Node.EXCLUSIVE), arg))
7 selfInterrupt();
8 }
tryAcquire()
tryAcquire()方法在FairSync、NonFairSync中均有实现,尝试获取锁资源,核心代码如下:

1 // 公平锁 FairSync#tryAcquire() 方法
2 protected final boolean tryAcquire(int acquires) {
3 // 获取当前线程
4 final Thread current = Thread.currentThread();
5 // 获取AQS的 state
6 int c = getState();
7 // state == 0 当前没有线程占用锁资源
8 if (c == 0) {
9 // 判断是否有线程在排队,若有线程在排队,返回true
10 if (!hasQueuedPredecessors() &&
11 // 尝试抢锁
12 compareAndSetState(0, acquires)) {
13 // 无线程排队,将线程属性设置为当前线程
14 setExclusiveOwnerThread(current);
15 return true;
16 }
17 }
18 // state != 0 有线程占用锁资源
19 // 占用锁资源的线程是否为当前线程
20 else if (current == getExclusiveOwnerThread()) {
21 // state + 1
22 int nextc = c + acquires;
23 // 锁重入超出最大限制 (int的最大值),抛异常
24 if (nextc < 0)
25 throw new Error("Maximum lock count exceeded");
26 // 将 state + 1 设置给 state
27 setState(nextc);
28 // 当前线程拿到锁资源,返回true
29 return true;
30 }
31 return false;
32 }
33
34 // 非公平锁 NonFairSync#tryAcquire() 方法
35 protected final boolean tryAcquire(int acquires) {
36 return nonfairTryAcquire(acquires);
37 }
38

39 // 非公平锁 Sync#nonfairTryAcquire() 方法
40 final boolean nonfairTryAcquire(int acquires) {
41 // 获取当前线程
42 final Thread current = Thread.currentThread();
43 // 获取AQS的 state
44 int c = getState();
45 // 无线程占用锁资源
46 if (c == 0) {
47 // CAS 修改 state 的值,修改成功,设置线程属性为当前线程,返回占用锁资源标识
48 if (compareAndSetState(0, acquires)) {
49 setExclusiveOwnerThread(current);
50 return true;
51 }
52 }
53 // 有线程占用锁资源
54 // 占用锁资源的线程是当前线程(重入)
55 else if (current == getExclusiveOwnerThread()) {
56 // AQS 的 state + acquires
57 int nextc = c + acquires;
58 // 超出锁重入的上限(int的最大值),抛异常
59 if (nextc < 0)
60 throw new Error("Maximum lock count exceeded");
61 // 将 state + acquires 设置到 state 属性
62 setState(nextc);
63 return true;
64 }
65 return false;
66 }
获取当前线程、AQS的state。AQS的state属性值为0,表示无线程占用锁资源,判断等待队列中是否
有线程在排队,若有线程在排队,返回尝试抢锁失败标识,将线程添加进等待队列中。
若state属性值不为0,判断持有锁资源的线程是否为当前线程,若为当前线程,AQS的state属性
值 + 1,返回尝试抢锁成功标识。
公平锁与非公平锁的整体实现流程类似,唯一不同的是,AQS的state属性值为0,无线程占用锁资
源时,非公平锁不会判断是否有线程在等待队列中排队,而是直接通过CAS抢锁。
addWaiter()

为当前线程创建入队节点AbstractQueuedSynchronizer$Node,入参mode表示锁类型,在AQS的
静态内部类Node中有SHARE、EXCLUSIVE两个属性,SHARE代表共享锁、EXCLUSIVE代表排它
锁。
AbstractQueuedSynchronizer#addWaiter() 核心代码:
1 // 等待队列的尾节点,懒加载,只能通过enq方法添加节点
2 private transient volatile Node tail;
3
4 private Node addWaiter(Node mode) {
5 // 当前线程、获取的锁类型封装为Node对象
6 Node node = new Node(Thread.currentThread(), mode);
7 // 获取等待队列的尾节点
8 Node pred = tail;
9 // 尾节点不为null
10 if (pred != null) {
11 // 将当前节点设置为等待队列的尾节点
12 node.prev = pred;
13 if (compareAndSetTail(pred, node)) {
14 pred.next = node;
15 return node;
16 }
17 }
18 // 等待队列为空,初始化等待队列节点信息
19 enq(node);
20 // 返回当前线程节点
21 return node;
22 }
等待队列不为空,将当前线程封装的Node节点添加进队列尾部;若等待队列为空,先初始化等待队
列,然后在将Node节点添加进队列尾部。
enq()
等待队列尾节点为空时,执行enq()方法初始化等待队列,并将Node节点添加进等待队列中。

1 private Node enq(final Node node) {
2 for (;;) {
3 // 获取等待队列的尾节点
4 Node t = tail;
5 // 等待队列为空,初始化等待队列
6 if (t == null) {
7 // 初始化等待队列头尾节点
8 if (compareAndSetHead(new Node()))
9 tail = head;
10 } else {
11 // 当前线程的Node添加到等待队列中
12 node.prev = t;
13 if (compareAndSetTail(t, node)) {
14 t.next = node;
15 return t;
16 }
17 }
18 }
19 }
acquireQueued()
当前线程是否挂起,AbstractQueuedSynchronizer#acquireQueued() 核心代码:

1 final boolean acquireQueued(final Node node, int arg) {
2 // 获取锁资源标识
3 boolean failed = true;
4 try {
5 boolean interrupted = false;
6 // 自旋
7 for (;;) {
8 // 获取当前节点的前驱节点
9 final Node p = node.predecessor();
10 // 当前节点的前驱节点为头节点,并获取锁资源成功
11 if (p == head && tryAcquire(arg)) {
12 // 将当前节点设置到head - 头节点
13 setHead(node);
14 // 原头节点的下一节点指向设置为null,GC回收
15 p.next = null;
16 // 设置获取锁资源成功
17 failed = false;
18 // 不管线程GC
19 return interrupted;
20 }
21 // 如果当前节点不是head的下一节点,获取锁资源失败,尝试将线程挂起
22 if (shouldParkAfterFailedAcquire(p, node) &&
23 // 线程挂起, UNSAFE.park()
24 parkAndCheckInterrupt())
25 interrupted = true;
26 }
27 } finally {
28 if (failed)
29 cancelAcquire(node);
30 }
31 }
查看当前排队的Node是否是head的next, 如果是,尝试获取锁资源, 如果不是或者获取锁资源失败
那么就尝试将当前Node的线程挂起(unsafe.park())。
shouldParkAfterFailedAcquire检查并更新未成功获取锁资源的状态,返回true表示线程被挂起。
AbstractQueuedSynchronizer#shouldParkAfterFailedAcquire() 核心代码:

1 static final class Node {
2 // 线程被取消
3 static final int CANCELLED = 1;
4 // 等待队列中存在待被唤醒的挂起线程
5 static final int SIGNAL = -1;
6 // 当前线程在Condition队列中,未在AQS对列中
7 static final int CONDITION = -2;
8 // 解决JDK1.5的BUG。共享锁在释放资源后,若头节点为0,无法确定真的没有后继节点
9 // 如果头节点为0,需要将头节点的状态改为 -3 ,当最新拿到锁资源的线程查看
10 // 是否有后继节点并且为当前锁为共享锁,需唤醒排队的线程。
11 static final int PROPAGATE = -3;
12 }
13
14 // 获取锁资源失败,挂起线程
15 private static boolean shouldParkAfterFailedAcquire(Node pred, Node node) {
16 // 获取当前节点的上一个节点的状态
17 int ws = pred.waitStatus;
18 // 上一节点被挂起
19 if (ws == Node.SIGNAL)
20 // 返回true,挂起当前线程
21 return true;
22 if (ws > 0) {
23 // 上一节点被取消,获取最近的线程挂起节点,
24 // 并将当前节点的上一节点指向最近的线程挂起节点
25 do {
26 node.prev = pred = pred.prev;
27 } while (pred.waitStatus > 0);
28 // 最近线程挂起节点的下一节点指向当前节点
29 pred.next = node;
30 } else {
31 // 上一节点状态小于等于0,存在线程处于等待状态,但未被挂起的场景
32 // 通过CAS将处于等待的线程挂起,避免在挂起前节点获取到锁资源
33 compareAndSetWaitStatus(pred, ws, Node.SIGNAL);
34 }
35 // 返回true,不挂起当前线程
36 return false;
37 }

在挂起线程前,确认当前节点的上一个节点的状态。若为1,代表是取消的节点,不能挂起;若为-1,
代表后续节点中有挂起的线程;若为-2 (线程在等待队列 - Condition队列中)、-3 (避免线程无法唤醒的
一个状态),需要将状态改为-1之后,才能挂起当前线程。
unlock()释放锁
释放锁,ReentrantLock#unlock() 核心代码:
1 // 释放锁
2 public void unlock() {
3 sync.release(1);
4 }
unlock方法实际调用的是AQS的release方法,AbstractQueuedSynchronizer#release() 核心代码:
1 // 等待队列的头节点,懒加载,通过setHead方法初始化
2 private transient volatile Node head;
3
4 // 释放锁
5 public final boolean release(int arg) {
6 // 当前线程释放锁资源的计数值
7 if (tryRelease(arg)) {
8 // 当前线程玩去释放锁资源,获取等待队列头节点
9 Node h = head;
10 if (h != null && h.waitStatus != 0)
11 // 唤醒等待队列中待唤醒的节点
12 unparkSuccessor(h);
13 // 完全释放锁资源
14 return true;
15 }
16 // 当前线程未完全释放锁资源
17 return false;
18 }
tryRelease()
释放锁,Reenttrant$Sync#tryRelease()的核心代码:

1 // 释放锁
2 protected final boolean tryRelease(int releases) {
3 // 修改 AQS 的 state
4 int c = getState() - releases;
5 // 当前线程不是持有锁的线程,抛出异常
6 if (Thread.currentThread() != getExclusiveOwnerThread())
7 throw new IllegalMonitorStateException();
8 // 是否成功的将锁资源完全释放标识 (state == 0)
9 boolean free = false;
10 // 锁资源完全释放
11 if (c == 0) {
12 // 修改标识
13 free = true;
14 // 将占用锁资源的属性设置为null
15 setExclusiveOwnerThread(null);
16 }
17 // state赋值
18 setState(c);
19 // 返回true表示当前线程完全释放锁资源;
20 // 返回false标识当前线程是由锁资源,持有计数值减少
21 return free;
22 }
