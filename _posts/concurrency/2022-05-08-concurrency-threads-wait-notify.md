---
title: 从0开始深入理解并发、线程与等待通知机制
categories: [Java, 并发编程]
tags: [并发, 线程, wait/notify, LockSupport, JUC]
author: hsc
date: 2022-05-08 00:00:00 +0800
description: 深入浅出并发编程系列第一课，从基础概念到线程通信全面讲解。
---


## 一、为什么学习并发编程？

最直白的原因——**面试需要**。大厂（如阿里、美团）的Java岗位对并发编程能力属于标配要求。

而在非大厂的公司，并发编程能力也是面试的极大加分项，工作时善用并发编程则可以极大提升程序员在公司的技术话语权。

### 开发中为什么需要并发编程？

1. **加快响应用户的时间**
   - 比如迅雷多线程下载，多个线程下载更快
   - 网页响应时间提升1s，流量大时能增加不少转化量
   - 静态资源用多个子域名加载，浏览器会多开线程加载页面资源

2. **使代码模块化、异步化、简单化**
   - 电商系统下订单和发送短信/邮件可以拆分，交给不同线程异步执行
   - 提升系统性能的同时使程序更加清晰

3. **充分利用CPU资源**
   - 目前CPU都是多核的，单线程无法充分利用多核优势
   - 多线程可以在多核上同时运行，减少CPU空闲时间
   - 单核CPU同样受益：类似QQ聊天时同时处理键盘输入、网络收发、屏幕显示

---

## 二、课程章节安排

完整系列共14章：

1. 从0开始深入理解并发、线程与等待通知机制 ← **（本文）**
2. 异步编程Future&CompletableFuture实战
3. 导致JVM内存泄露的ThreadLocal详解
4. 并发编程之CAS&Atomic原子操作详解
5. 深入理解独占锁Synchronized底层原理
6. JUC并发工具类在大厂的应用场景详解
7. 深入理解AQS之ReentrantLock源码分析
8. Semaphore&CountDownlatch&CyclicBarrier源码分析
9. 并发容器（Map、List、Set）实战及其原理
10. 阻塞队列BlockingQueue实战及其原理分析
11. 线程池ThreadPoolExecutor实战及其原理分析
12. 线程池ForkJoinPool工作原理分析
13. 深入理解并发可见性、有序性、原子性与JMM内存模型
14. CPU缓存架构详解&高性能内存队列Disruptor实战

**学习建议：**
- 初学者：重点掌握第1~5章、第9~12章（基础概念、基础用法、并发工具类和容器）
- 有经验者：建议全部学习

---

## 三、基础概念

### 3.1 进程和线程

#### 进程（Process）

- 应用程序（app）由指令和数据组成，存放在磁盘上
- 运行程序时，指令加载至CPU，数据加载至内存
- **进程 = 加载指令、管理内存、管理IO的实体**
- 进程是程序的实例，是动态的
- 分为**系统进程**和**用户进程**
- 站在操作系统角度：**进程是程序运行资源分配（以内存为主）的最小单位**

#### 线程（Thread）

- CPU有限，需要在程序间协调调度，线程就是**CPU调度的最小单位**
- 线程必须依赖于进程而存在，是进程中的一个实体
- 线程几乎不拥有系统资源，只拥有运行中必不可少的资源（程序计数器、寄存器和栈）
- 同一进程内的线程共享进程所拥有的全部资源
- 线程又称**轻量级进程（Lightweight Process, LWP）**

**进程与线程的区别：**

| 对比维度 | 进程 | 线程 |
|---------|------|------|
| 关系 | 相互独立 | 存在于进程内，是进程的子集 |
| 资源共享 | 进程拥有共享资源 | 线程间共享进程内存空间 |
| 通信方式 | IPC（进程间通信），较复杂 | 相对简单，通过共享变量 |
| 跨机通信 | 需通过网络 + 协议（如HTTP） | 不适用 |
| 上下文切换 | 成本较高 | 成本较低（更轻量） |

### 3.2 CPU核心数和线程数的关系

- 同一时刻，一个CPU核心只能运行一个线程
- **1个核心 : 1个同时运行的线程**
- Intel超线程技术：1核心 : 2逻辑处理器
- Java中获取CPU核心数：`Runtime.getRuntime().availableProcessors()`（逻辑处理器数）

> 并发编程下的性能优化往往和CPU核心数密切相关。

### 3.3 上下文切换（Context Switch）

**定义：** CPU从一个进程/线程切换到另一个进程/线程的过程。

- **上下文** = CPU寄存器和程序计数器在任何时间点的内容
- **寄存器** = CPU内部极快的内存，加速程序执行
- **程序计数器** = 指示CPU在指令序列中的位置

**上下文切换过程：**
1. 暂停一个进程的处理，将其CPU状态（上下文）存储在内存中
2. 从内存获取下一个进程的上下文，恢复到CPU寄存器中
3. 返回到程序计数器指示的位置继续执行

**成本：** 一次上下文切换约需 **5000~20000个时钟周期**（简单指令仅需几个~十几个周期），成本巨大。

引发原因：线程/进程切换、系统调用等。

### 3.4 并发和并行

| 概念 | 英文 | 定义 |
|------|------|------|
| 并发 | Concurrent | 交替执行不同任务，单CPU下通过快速切换达到"同时执行"效果。**微观串行，宏观并行** |
| 并行 | Parallel | 同时执行不同任务，多核CPU下每个核调度不同线程。**真正的同时执行** |

---

## 四、认识Java里的线程

### 4.1 Java程序天生就是多线程的

执行main()方法的线程名为`main`，但除此之外JVM会自动启动很多系统线程：

```java
ThreadMXBean threadMXBean = ManagementFactory.getThreadMXBean();
ThreadInfo[] threadInfos = threadMXBean.dumpAllThreads(false, false);
for (ThreadInfo threadInfo : threadInfos) {
    System.out.println("[" + threadInfo.getThreadId() + "] " + threadInfo.getThreadName());
}
```

典型JVM后台线程：
- **Monitor Ctrl-Break** — 监控Ctrl-Break中断信号
- **Attach Listener** — 内存dump、线程dump、类信息统计等
- **Signal Dispatcher** — 分发处理发送给JVM的信号
- **Finalizer** — 调用对象finalize方法
- **Reference Handler** — 清除Reference
- **main** — 用户程序入口

### 4.2 线程的创建和启动

#### 方式1：使用Thread类或继承Thread类

```java
// 线程和任务合并在一起
Thread t1 = new Thread("t1") {
    @Override
    public void run() {
        log.debug("Hello Thread");
    }
};
t1.start();
```

#### 方式2：实现 Runnable 接口配合Thread（推荐）

```java
// 线程和任务分离
Runnable task2 = () -> log.debug("hello");  // Java 8+ lambda
Thread t2 = new Thread(task2, "t2");
t2.start();
```

> **小结：** Thread是Java对线程的唯一抽象，Runnable只是对任务（业务逻辑）的抽象。方式2更灵活，更容易与线程池等高级API配合。

#### 方式3：使用FutureTask 配合 Thread

```java
FutureTask<Integer> task3 = new FutureTask<>(() -> {
    log.debug("hello");
    return 100;
});
new Thread(task3, "t3").start();
Integer result = task3.get();  // 阻塞等待结果
log.debug("结果是:{}", result);
```

- **Runnable**：`run()`返回void，无法返回结果
- **Callable**：`call()`返回泛型V类型结果
- **Future**：对任务执行结果进行取消、查询是否完成、获取结果
- **FutureTask**：实现RunnableFuture接口，既是Runnable又是Future

### 4.3 面试题：创建线程有几种方式？

**官方说法（Thread源码注释）：** 两种方式

1. 派生自Thread类
2. 实现Runnable接口

**本质：** Java中只有一种方式 — `new Thread()` 创建线程对象，调用 `Thread#start` 启动线程。

- Callable方式 → FutureTask包装成Runnable → 交给Thread → 等同于Runnable方式
- 线程池方式 → 池化技术，资源复用，与新启线程无关

### 4.4 run() vs start()

- `new Thread()` 只是创建Thread实例，还未与操作系统线程挂钩
- `start()` 才真正启动线程（调用native `start0()`方法）
- `start()` 让线程进入就绪队列等待CPU分配，分到CPU后才执行 `run()`
- `start()` **不能重复调用**，否则抛出 `IllegalThreadStateException`
- `run()` 可以重复执行，也可以被单独调用

---

## 五、深入学习Java的线程

### 5.1 线程的状态/生命周期

#### 操作系统层面的五种状态

```
【初始状态】→ 【可运行状态】↔ 【运行状态】→ 【终止状态】
                  ↑              ↓
                  ← 【阻塞状态】←
```

- **初始状态：** 仅语言层面创建了线程对象，未与操作系统线程关联
- **可运行状态（就绪）：** 线程已创建，等待CPU调度
- **运行状态：** 获取了CPU时间片，正在执行
- **阻塞状态：** 调用了阻塞API（如BIO），不消耗CPU；BIO完成后被唤醒回可运行状态
- **终止状态：** 线程执行完毕，生命周期结束

#### Java API层面的六种状态（Thread.State枚举）

| 状态 | 说明 |
|------|------|
| **NEW** | 新创建线程对象，未调用start() |
| **RUNNABLE** | 就绪(ready) + 运行中(running) 统称 |
| **BLOCKED** | 阻塞于锁 |
| **WAITING** | 等待其他线程的特定动作（通知或中断） |
| **TIMED_WAITING** | 超时等待，可在指定时间后自行返回 |
| **TERMINATED** | 线程已执行完毕 |

### 5.2 线程常见方法

| 方法 | static | 功能 | 注意事项 |
|------|--------|------|---------|
| `start()` | | 启动新线程 | 只能调用一次，重复调用抛异常 |
| `run()` | | 新线程启动后调用的方法 | 可通过Runnable参数或继承覆盖 |
| `join()` / `join(long n)` | | 等待线程运行结束 | 阻塞当前线程 |
| `getId()` | | 获取线程长整型id | id唯一 |
| `getName()` / `setName(String)` | | 获取/修改线程名 | |
| `getPriority()` / `setPriority(int)` | | 获取/修改优先级 | 1~10，较大者提高被调度几率 |
| `getState()` | | 获取线程状态 | 返回6种状态枚举 |
| `isInterrupted()` | | 判断是否被中断 | **不会清除中断标记** |
| `interrupt()` | | 中断线程 | sleep/wait/join时抛InterruptedException并清除标记；park时设置标记 |
| `interrupted()` | √ | 判断当前线程是否被中断 | **会清除中断标记** |
| `currentThread()` | √ | 获取当前执行线程 | |
| `sleep(long n)` | √ | 休眠n毫秒，让出CPU | 不会释放对象锁 |
| `yield()` | √ | 提示调度器让出CPU | |

**已废弃的方法（容易破坏同步，造成死锁）：** `stop()`、`suspend()`、`resume()`

### 5.3 sleep 与 yield

#### sleep方法

```java
Thread t1 = new Thread(() -> {
    try {
        Thread.sleep(3000);
    } catch (InterruptedException e) {
        throw new RuntimeException(e);
    }
    log.debug("执行完成");
}, "t1");
t1.start();
log.debug("线程t1的状态：" + t1.getState());  // RUNNABLE
Thread.sleep(500);
log.debug("线程t1的状态：" + t1.getState());  // TIMED_WAITING
```

特点：
- 让当前线程从 Running → Timed Waiting，**不释放对象锁**
- 可被 `interrupt()` 打断，抛出 `InterruptedException`
- 建议用 `TimeUnit.XXX.sleep()` 代替，可读性更好
- `sleep(0)` 等同于 `yield()`

**避免空转：** 不用CPU时用 `sleep` 或 `yield` 替代 `while(true)` 空转

```java
while(true) {
    try {
        Thread.sleep(50);
    } catch (InterruptedException e) {
        e.printStackTrace();
    }
}
```

- `wait` 或条件变量也能达到类似效果，但需要加锁，适用于同步场景
- `sleep` 适用于无需锁同步的场景

#### yield方法

- 让当前线程从 Running → Runnable，**不释放对象锁**
- 让优先级更高（至少相同）的线程获得执行机会
- 依赖操作系统调度器实现
- 实际应用：`ConcurrentHashMap#initTable` 中用 yield 让初始化线程更快执行，避免阻塞/等待的上下文切换开销

### 5.4 线程的优先级

- 优先级范围：1~10，默认5
- `setPriority(int)` 修改优先级
- 优先级仅作为调度器**提示**，可被忽略
- CPU忙时优先级高的获得更多时间片；闲时几乎无作用

**设置原则：**
- 频繁阻塞的线程（sleep/I/O操作）→ 较高优先级
- 偏重计算的线程（需较多CPU时间）→ 较低优先级

```java
Thread t1 = new Thread(task1, "t1");
Thread t2 = new Thread(task2, "t2");
t1.setPriority(Thread.MIN_PRIORITY);  // 1
t2.setPriority(Thread.MAX_PRIORITY);  // 10
```

> 不同JVM和操作系统上线程规划有差异，有些甚至会忽略优先级设定。

### 5.5 join方法

**作用：** 等待调用join方法的线程结束后，当前线程再继续执行。用于等待异步线程结果。

#### 为什么需要join？

```java
private static int count = 0;

public static void main(String[] args) throws InterruptedException {
    log.debug("开始执行");
    Thread t1 = new Thread(() -> {
        log.debug("开始执行");
        SleepTools.second(1);
        count = 5;
        log.debug("执行完成");
    }, "t1");
    t1.start();
    log.debug("结果为:{}", count);  // 打印 0！
    log.debug("执行完成");
}
```

问题：主线程和t1并行执行，t1需要1秒才能算出count=5，主线程一开始就打印了count=0。

#### 解决方案：join

```java
t1.start();
t1.join();  // 等待t1执行完毕
log.debug("结果为:{}", count);  // 正确打印 5
```

**同步 vs 异步：**
- 需要等待结果返回才能继续运行 → 同步
- 不需要等待结果返回 → 异步

#### 面试题：三个线程T1、T2、T3顺序执行

```java
Thread t1 = new Thread(() -> log.debug("线程t1执行完成"), "t1");
Thread t2 = new Thread(() -> {
    t1.join();
    log.debug("线程t2执行完成");
}, "t2");
Thread t3 = new Thread(() -> {
    t2.join();
    log.debug("线程t3执行完成");
}, "t3");

t1.start();
t2.start();
t3.start();
```

> join的实现本质上是基于等待通知机制的。

### 5.6 守护线程（Daemon Thread）

- 默认情况下，Java进程需等待所有线程结束后才结束
- **守护线程**：只要非守护线程运行结束，守护线程即使未执行完也会强制结束

```java
Thread t1 = new Thread(() -> {
    log.debug("开始运行...");
    SleepTools.second(3);
    log.debug("运行结束...");
}, "t1");
t1.setDaemon(true);
t1.start();
SleepTools.second(1);
log.debug("运行结束...");  // 主线程1秒后结束，t1守护线程被强制终止
```

**应用场景：**
- JVM垃圾回收器（无用户线程则不产生垃圾，不需要工作）
- 中间件的心跳检测、事件监听等后台任务
- 不希望阻止JVM进程结束的后台任务

### 5.7 线程的终止

#### 自然终止

- `run()` 方法执行完成
- 抛出未处理的异常导致提前结束

#### stop() — ❌ 不要使用！

**已被废弃的原因：**
1. 立即抛出 `ThreadDeath` 异常，run()中任何指令都可能被中断
2. **会释放当前线程持有的所有锁**，这种释放是不可控的（导致线程不安全）

**示例：转账被stop的灾难**

```java
// 线程A的转账逻辑
synchronized (lock) {
    account1 -= 100;   // 1号账户少了100元
    // 如果这里被stop，锁被释放
    account2 += 100;   // 2号账户没有增加100元！
}
```

#### 中断机制（推荐）

中断是**协作式**的：其他线程调用 `interrupt()` 打个招呼，线程自己决定是否响应。

```java
Thread t1 = new Thread(() -> {
    while (true) {
        Thread current = Thread.currentThread();
        if (current.isInterrupted()) {
            log.debug("中断状态: {}", current.isInterrupted());
            break;
        }
    }
}, "t1");
t1.start();
t1.interrupt();
```

**中断阻塞线程（sleep/wait/join）：**

```java
Thread t1 = new Thread(() -> {
    while (true) {
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
            e.printStackTrace();  // 中断状态被清除
        }
    }
}, "t1");
t1.start();
Thread.sleep(100);
t1.interrupt();
log.debug("中断状态：{}", t1.isInterrupted());  // false，已被清除
```

**关键区别：**

| 方法 | 清除中断标记 |
|------|:---:|
| `isInterrupted()` | ❌ |
| `interrupted()` | ✅ |

> - 中断正常运行的线程 → **不会清空中断状态**
> - 中断sleep/wait/join的线程 → **会清空中断状态**（抛InterruptedException）
> - **处于死锁状态的线程无法被中断**
> - 不建议自定义取消标志位：阻塞调用时无法及时检测，中断机制更好

---

## 六、线程的调度机制

### 6.1 两种调度方式

| 方式 | 说明 | 优缺点 |
|------|------|--------|
| **协同式** | 线程执行时间由线程本身控制，主动通知系统切换 | 实现简单，无线程同步问题；一个线程出问题则进程全部阻塞 |
| **抢占式** | 执行时间及切换由系统决定 | 线程执行时间不可控，但不会出现"一个线程导致整个进程阻塞" |

**Java采用抢占式调度。** `Thread.yield()` 可以让出CPU，但获取CPU执行时间线程无法控制，只能通过优先级提示调度器。

### 6.2 Java线程模型

#### 三种实现方式

| 方式 | 说明 | 特点 |
|------|------|------|
| **1:1（内核线程）** | 直接由操作系统内核支持的线程 | 调度由内核完成，系统调用开销大（User Mode ↔ Kernel Mode切换），线程数有限 |
| **1:N（用户线程）** | 完全在用户空间实现 | 快速低消耗，支持大规模并发；但阻塞处理、多处理器映射困难 |
| **N:M（混合）** | 内核线程+用户线程 | 折中方案，兼顾规模和调度能力 |

#### Java的实现（HotSpot）

- JDK 1.2以前：用户线程
- **JDK 1.3起：1:1内核线程模型**
- 每个Java线程直接映射到一个操作系统原生线程
- HotSpot不干涉线程调度，全权交给操作系统
- **线程优先级通过映射到操作系统原生线程实现，最终取决于操作系统，并非完全可靠**

### 6.3 虚拟线程（Java 21 Virtual Threads）

- 用户级线程，轻量级
- 可创建数千甚至数万个虚拟线程，不占用大量OS资源
- 适合**阻塞式任务**（阻塞期间CPU让渡给其他任务）
- **不适合CPU密集计算或非阻塞任务**（不会更快，只增加了规模）
- 用完即抛，**不需要池化**
- Tomcat、Jetty、Netty、Spring Boot等已支持虚拟线程

```java
// 平台线程
Thread.ofPlatform().start(() -> {
    System.out.println(Thread.currentThread());
});

// 虚拟线程
Thread vt = Thread.ofVirtual().start(() -> {
    System.out.println(Thread.currentThread());
});
vt.join();
// 输出：
// Thread[#22,Thread-0,5,main]
// VirtualThread[#23]/runnable@ForkJoinPool-1-worker-1
```

---

## 七、线程间的通信

### 7.1 管道输入输出流（Piped Stream）

线程之间的数据传输，媒介为内存。避免中间写入磁盘。

四种实现：
- `PipedOutputStream` / `PipedInputStream`（字节流）
- `PipedWriter` / `PipedReader`（字符流）

```java
PipedWriter out = new PipedWriter();
PipedReader in = new PipedReader();
out.connect(in);  // 必须连接，否则IOException

Thread printThread = new Thread(new Print(in), "PrintThread");
printThread.start();

int receive;
while ((receive = System.in.read()) != -1) {
    out.write(receive);
}
out.close();
```

### 7.2 volatile — 最轻量的通信/同步机制

保证不同线程对该变量操作的**可见性**：一个线程修改后，其他线程立即可见。

```java
private static volatile boolean stop = false;

// 线程t1
while (!stop) {
    i++;
}
// 主线程
stop = true;  // t1立即感知并退出循环
```

- 不加volatile → 子线程无法感知主线程修改 → 不会退出循环
- 加了volatile → 子线程立即可见 → 迅速退出
- **volatile不保证多线程同时写时的线程安全**
- **最适用场景：一个线程写，多个线程读**

> JMM（Java内存模型）控制线程间共享变量的可见性。线程对共享变量的操作都在自己的本地内存中进行，JMM控制主内存与本地内存的交互。

### 7.3 Thread.join()

join基于等待通知机制实现。让当前线程阻塞等待被调用join的线程执行完毕，保证执行顺序。本质上是串行执行，失去了并行意义。

### 7.4 等待/通知机制（wait/notify）

#### 原始轮询方式的问题

消费者线程不断循环检查变量：

```java
while (conditionNotMet) {
    Thread.sleep(1);  // 难以确保及时性，消耗处理器资源
}
```

问题：
- 睡眠时间长 → 无法确保及时性
- 睡眠时间短 → 消耗更多处理器资源

#### Object#wait/notify/notifyAll

- `notify()`：通知一个在对象上等待的线程，前提是该线程获取到对象锁
- `notifyAll()`：通知所有等待的线程。**尽量用notifyAll()**，谨慎用notify()（无法确保唤醒的就是目标线程）
- `wait()`：进入WAITING状态，**释放对象的锁**，等待通知或中断
- `wait(long)`：超时等待n毫秒
- `wait(long, int)`：更细粒度控制，可达纳秒

**等待方原则：**

```java
synchronized(对象) {
    while (条件不满足) {
        对象.wait();  // 被通知后仍要检查条件
    }
    对应的逻辑;
}
```

**通知方原则：**

```java
synchronized(对象) {
    改变条件
    对象.notifyAll();
}
```

**完整示例：**

```java
public class WaitDemo {
    public static void main(String[] args) throws InterruptedException {
        Object locker = new Object();
        
        Thread t1 = new Thread(() -> {
            try {
                System.out.println("wait开始");
                synchronized (locker) {
                    locker.wait();
                }
                System.out.println("wait结束");
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        });
        t1.start();
        
        Thread.sleep(1000);  // 保证t1先启动，wait()先执行
        
        Thread t2 = new Thread(() -> {
            synchronized (locker) {
                System.out.println("notify开始");
                locker.notifyAll();
                System.out.println("notify结束");
            }
        });
        t2.start();
    }
}
```

### 7.5 LockSupport#park/unpark

JDK中实现线程阻塞和唤醒的工具。类似**二元信号量**（只有1个许可证）。

- `park()`：等待"许可"，无许可则阻塞
- `unpark(Thread t)`：为指定线程发放"许可"

**AQS（AbstractQueuedSynchronizer）** 的核心就是通过 LockSupport.park() 和 LockSupport.unpark() 实现线程阻塞和唤醒。

```java
public class LockSupportDemo {
    public static void main(String[] args) throws InterruptedException {
        Thread parkThread = new Thread(() -> {
            System.out.println("ParkThread开始执行");
            LockSupport.park();  // 等待许可
            System.out.println("ParkThread执行完成");
        });
        parkThread.start();
        
        Thread.sleep(1000);
        System.out.println("唤醒parkThread");
        LockSupport.unpark(parkThread);  // 发放许可
    }
}
```

**LockSupport vs wait/notify：**

| 对比维度 | LockSupport | wait/notify |
|---------|-------------|-------------|
| 调用位置 | 随时随地 | 只能在synchronized代码块中 |
| 调用顺序 | 可以先unpark再park（不阻塞） | 先notify再wait会被阻塞 |
| 多次unpark效果 | 等同于一次 | - |
| 无需加锁 | ✅ | ❌ |

---

## 八、总结

本文从并发编程的基础概念出发，系统讲解了：

1. **为什么学并发** — 面试标配 + 性能优化核心能力
2. **进程与线程** — 资源分配 vs CPU调度
3. **上下文切换** — 成本巨大的CPU操作
4. **并发 vs 并行** — 交替执行 vs 同时执行
5. **Java线程** — 创建方式、生命周期、常用方法
6. **线程调度** — 抢占式调度、1:1内核线程模型、虚拟线程
7. **线程通信** — Piped Stream、volatile、join、wait/notify、LockSupport

掌握这些基础是后续深入学习JUC并发工具类、锁机制、线程池等高级主题的必备前提。
