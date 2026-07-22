---



title: "2 CountDownLatch源码分析"
description: "CountDownLatch 介绍 CountDownLatch 让一个或多个线程等待其他线程执行完成后再执行。"
author: hsc
date: 2021-12-19 00:00:00 +0800
categories: ['Java 后端', '并发编程']
tags: ['并发编程', 'JUC', 'AQS', 'CAS']
toc: true



---

#### 8.2 CountDownLatch 源码分析

1、CountDownLatch 介绍 CountDownLatch 让一个或多个线程等待其他线程执行完成后再执行。在创建 CountDownLatch 对象时,必须指定线程数 count,每当一个线程执行完成调用 countDown()方法,线程数 count 减 1,当 count 减到 0 时,await()方法就不再阻塞。
2、CountDownLatch 源码分析 CountDownLatch 详情如下:
2.1 构造函数 CountDownLatch 没有无参构造函数,在有参构造函数中初始化了 sync 属性。

1 public CountDownLatch(int count) {2 // count 合法校验 3 if (count < 0) throw new IllegalArgumentException("count < 0");
4 // 初始化 sync 属性 5 this.sync = new Sync(count);
6 }2.2 Sync - 队列同步器

1 // 抽象队列同步器 2 private static final class Sync extends AbstractQueuedSynchronizer {3 private static final long serialVersionUID = 4982264981922014374L;
45 // 将 count 赋值给 AQS 的 state 属性 6 Sync(int count) {7 setState(count);
8 }9 // 获取 AQS 的 state 属性 10 int getCount() {11 return getState();
12 }13 // 判断所有线程是否都执行完成, 1 -> 全部执行完成;-1 -> 仍有线程在执行 14 protected int tryAcquireShared(int acquires) {15 return (getState() == 0) ? 1 : -1;
16 }17 // 释放锁 18 protected boolean tryReleaseShared(int releases) {19 // 自旋 20 for (;;) {21 // 获取 AQS 的 state22 int c = getState();
23 // 锁资源已经释放完毕,再次进入,直接返回 false,什么也不做 24 if (c == 0)
25 return false;
26 // state - 127 int nextc = c-1;
28 // CAS 赋值操作 29 if (compareAndSetState(c, nextc))
30 // 最后一个线程执行完,state = 0 ,返回 true。
31 // countDown() 唤醒等待队列中的其他挂起线程 32 return nextc == 0;
33 }34 }35 }2.3 await() - 阻塞等待

CountDownLatch#await(),详情如下:
1 // AQS 的 state 属性不为 0, 阻塞 2 public void await() throws InterruptedException {3 // 调用 AQS 提供的获取共享锁并允许中断的方法 4 sync.acquireSharedInterruptibly(1);
5 }AbstractQueuedSynchronizer#acquireSharedInterruptibly(),详情如下:
1 // 获取共享锁,并允许其中断 2 public final void acquireSharedInterruptibly(int arg) throws InterruptedException {3 // 线程中断,抛出异常 4 if (Thread.interrupted())
5 throw new InterruptedException();
6 // 获取共享锁,由 CountDownLatch 实现 7 if (tryAcquireShared(arg) < 0)
8 // state > 0,说明有线程在持有锁资源,将当前线程添加到 AQS 等待队列中 9 doAcquireSharedInterruptibly(arg);
10 }CountDownLatch#Sync#tryAcquireShared(),详情如下:
1 // 获取共享锁 2 protected int tryAcquireShared(int acquires) {3 // 线程全部执行完成,返回 1;未全部执行完成,返回-14 return (getState() == 0) ? 1 : -1;
5 }AbstractQueuedSynchronizer#acquireSharedInterruptibly(),详情如下:

1 // 将当前线程添加到 AQS 等待队列中 2 private void doAcquireSharedInterruptibly(int arg) throws InterruptedException {3 // 当前线程封装成 Node,添加到 AQS 等待队列中 4 final Node node = addWaiter(Node.SHARED);
5 boolean failed = true;
6 try {7 // 自旋 8 for (;;) {9 // 获取当前线程节点的前驱节点 10 final Node p = node.predecessor();
11 // 前驱节点为等待队列头节点 12 if (p == head) {13 // 调用 CountDownLatch 实现的方法 14 int r = tryAcquireShared(arg);
15 // 返回值为 1,表示 state 为 0 ,所有线程都释放了锁,无其他线程持有锁资源 16 if (r >= 0) {17 // state = 0,将当前线程和后面所有排队的线程都唤醒。
18 setHeadAndPropagate(node, r);
19 p.next = null;
20 failed = false;
21 return;
22 }23 }24 // *** 线程在此处被挂起,待所有线程释放锁资源后,即 state = 0 ,线程被唤醒,再继续往下执行 25 // 挂起获取锁资源失败的线程,并且挂起的线程被中断,抛出 InterruptedException 异常 26 if (shouldParkAfterFailedAcquire(p, node) &&27 parkAndCheckInterrupt())
28 throw new InterruptedException();
29 }30 } finally {31 if (failed)
32 cancelAcquire(node);
33 }34 }2.4 countDown() - 释放锁资源

CountDownLatch#countDown(),详情如下:
1 // countDown 方法, 实际上调用了 AQS 的释放共享锁操作 2 2 public void countDown() {3 3 sync.releaseShared(1);
4 4 }AbstractQueuedSynchronizer#releaseShared(),详情如下:
1 // AQS 提供的释放共享锁方法,CountDownLatch 实现了 tryReleaseShared 方法 2 public final boolean releaseShared(int arg) {3 // 尝试释放锁资源 4 if (tryReleaseShared(arg)) {5 // 没有线程持有锁资源,唤醒等待队列中的其他挂起线程 6 doReleaseShared();
7 return true;
8 }9 return false;
10 }CountDownLatch#Sync#tryReleaseShared(),详情如下:

1 protected boolean tryReleaseShared(int releases) {2 // 自旋 3 for (;;) {4 // 获取当前持有锁资源的线程数 5 int c = getState();
6 // state 已为 0,返回 false,那么再次执行 countDown,什么事情也不做 7 if (c == 0)
8 return false;
9 // count - 110 int nextc = c-1;
11 // CAS 完成赋值操作 12 if (compareAndSetState(c, nextc))
13 // 没有线程持有锁资源,返回 true14 return nextc == 0;
15 }16 }AbstractQueuedSynchronizer#doReleaseShared(),详情如下:

1 // 没有线程持有锁资源的处理 2 private void doReleaseShared() {3 // 自旋 4 for (;;) {5 // 获取等待队列的头节点 6 Node h = head;
7 // 等待队列中有挂起线程待唤醒 8 if (h != null && h != tail) {9 int ws = h.waitStatus;
10 // 线程待唤醒 11 if (ws == Node.SIGNAL) {12 if (!compareAndSetWaitStatus(h, Node.SIGNAL, 0))
13 continue;
14 // 唤醒线程 15 unparkSuccessor(h);
16 }17 // CAS 失败 18 else if (ws == 0 &&19 !compareAndSetWaitStatus(h, 0, Node.PROPAGATE))
20 continue;
21 }22 // 等待队列头节点被改变,结束循环 23 if (h == head)
24 break;
25 }26 }2.5 总结 CountDownLatch 基于 AQS + CAS 实现,CountDownLatch 的构造函数中必须指定 count,同时初始继承 AQS 的内部类 Sync,通过 Sync 对象将 count 赋值给 AQS 的 state 属性,这样就可以基于 AQS 提供的方法完成 CountDownLatch 的功能。
调用 countDown()方法,实际上是将 AQS 中 state 减 1。所有线程执行完成,state 会被修改为 0,在 countDown()中会唤醒等待队列中挂起的线程。

调用 await()方法,实际上是判断 AQS 中的 state 是否为 0。state > 0,表示有线程仍在执行,此时 await()会阻塞线程。当最后一个线程执行结束,state 变为 0,countDown()唤醒线程后,await()正常执行结束,不再阻塞。
