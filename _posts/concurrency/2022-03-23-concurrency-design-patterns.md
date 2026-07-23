---
title: 在并发中常用的设计模式
categories: [Java, 并发编程]
tags: [并发设计模式, Two-phase Termination, Immutability, Copy-on-Write, ThreadLocal, Guarded Suspension, Balking, Worker Thread, 生产者消费者]
author: hsc
date: 2022-05-08 00:00:00 +0800
description: 深入讲解常用并发设计模式，涵盖线程终止、避免共享、多线程if、多线程分工四大类模式。
mindmap: https://www.processon.com/view/link/615d4a610e3e74663e97fa0e
---

## 文章概览

本文系统讲解四大类并发设计模式：

| 类别 | 模式 | 核心思想 |
|------|------|---------|
| **优雅终止** | 两阶段终止 | 发送终止请求 → 等待线程终止 |
| **避免共享** | 不变性、Copy-on-Write、ThreadLocal | 没有共享就没有并发问题 |
| **多线程if** | Guarded Suspension、Balking | 条件满足则继续，否则等待/放弃 |
| **多线程分工** | Thread-Per-Message、Worker Thread、生产者-消费者 | 合理分配任务执行 |

---

## 一、优雅终止线程的设计模式

> 思考：在一个线程 T1 中如何优雅地终止线程 T2？

**错误做法：** `stop()` — Java 已废弃，会立即释放所有锁，导致线程不安全。

**正确思路：** 两阶段终止模式。

### 1.1 两阶段终止（Two-phase Termination）模式

两阶段终止模式通过两个阶段来终止线程：

- **第一阶段：发送终止请求**
- **第二阶段：等待线程终止**

#### 第一阶段：如何发送终止请求？

线程进入终止状态的前提是线程进入 `RUNNABLE` 状态，但线程可能处于休眠状态。利用 `interrupt()` 方法可以让线程从休眠状态转换到 `RUNNABLE` 状态。

#### 第二阶段：如何终止 RUNNABLE 状态的线程？

RUNNABLE → 终止，优雅的方式是让线程自己执行完 `run()` 方法。一般采用**标志位**，线程在适当时机检查标志位，符合条件时自动退出 `run()` 方法。

**总结：终止指令 = interrupt() 方法 + 线程终止标志位。**

#### 两阶段终止模式的好处

1. **优雅终止** — 避免突然终止线程带来的副作用
2. **安全性** — 线程终止前可执行必要的清理工作
3. **灵活性** — 可根据具体情况灵活设置终止条件和清理工作

### 1.2 使用场景

- 服务器应用程序 — 终止时正确保存和释放资源
- 大规模并发系统 — 正确关闭和释放所有线程和资源
- 定时任务系统 — 任务执行完毕后正确终止并清理
- 数据处理系统 — 处理完所有数据后正确终止
- 消息订阅系统 — 订阅结束后正确终止订阅线程

### 1.3 代码实现

#### 基础版：标志位 + join

```java
public class MonitorThread extends Thread {
    // volatile 标志变量，用于标识是否需要终止线程
    private volatile boolean terminated = false;

    public void run() {
        while (!terminated) {
            // 执行监控操作
            System.out.println("监控线程正在执行监控操作...");
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
        // 执行清理操作
        System.out.println("监控线程正在执行清理操作...");
        releaseResources();
    }

    public void terminate() {
        // 设置标志变量为 true，并等待一段时间
        terminated = true;
        try {
            join(5000); // 等待5秒钟，期间监控线程会检查 terminated 的状态
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    private void releaseResources() {
        System.out.println("监控线程正在释放资源和进行必要的清理工作...");
    }

    public static void main(String[] args) throws InterruptedException {
        MonitorThread thread = new MonitorThread();
        thread.start();                     // 启动监控线程
        Thread.sleep(10000);                // 主线程休眠，监控线程执行监控操作
        thread.terminate();                 // 终止监控线程
        Thread.sleep(100000);
    }
}
```

#### 进阶版：结合中断机制

```java
public class MonitorThread2 extends Thread {
    private volatile boolean terminated = false;

    public void run() {
        while (!Thread.interrupted() && !terminated) {
            System.out.println("监控线程正在执行监控操作...");
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                System.out.println("监控线程被中断，准备退出...");
                Thread.currentThread().interrupt();  // 重新设置中断状态
                e.printStackTrace();
            }
        }
        // 执行清理操作
        System.out.println("监控线程正在执行清理操作...");
        releaseResources();
    }

    public void terminate() {
        terminated = true;
        try {
            join(5000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    private void releaseResources() {
        System.out.println("监控线程正在释放资源和进行必要的清理工作...");
    }

    public static void main(String[] args) throws InterruptedException {
        MonitorThread2 thread = new MonitorThread2();
        thread.start();
        Thread.sleep(10000);
        thread.interrupt();  // 设置中断标志位
        // thread.terminate();  // 也可使用 terminate 方式
        Thread.sleep(100000);
    }
}
```

### 1.4 优雅终止线程池

在线程池中应使用以下方法：

| 方法 | 行为 |
|------|------|
| `shutdown()` | 停止接受新任务，等待所有已提交任务执行完毕后再关闭 |
| `shutdownNow()` | 停止接受新任务，尝试中断正在执行任务的线程，返回未执行的任务列表 |

```java
public class ThreadPoolDemo {
    public static void main(String[] args) throws InterruptedException {
        ExecutorService executorService = Executors.newFixedThreadPool(5);

        for (int i = 0; i < 10; i++) {
            executorService.submit(() -> {
                try {
                    System.out.println(Thread.currentThread().getName() + "正在执行任务...");
                    Thread.sleep(5000);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();  // 重新设置中断状态
                    e.printStackTrace();
                } finally {
                    System.out.println(Thread.currentThread().getName() + "任务执行完毕");
                }
            });
        }

        // 停止线程池接受新的任务，但不能强制停止已经提交的任务
        executorService.shutdown();

        // 等待线程池中的任务执行完毕，或者超时时间到达
        boolean terminated = executorService.awaitTermination(8, TimeUnit.SECONDS);
        if (!terminated) {
            // 如果还有未执行完毕的任务，则调用 shutdownNow 中断所有正在执行的任务
            List<Runnable> tasks = executorService.shutdownNow();
            System.out.println("剩余未执行的任务数：" + tasks.size());
        }
    }
}
```

### 1.5 注意事项

> ⚠️ **两个关键点：**
>
> 1. **仅检查终止标志位是不够的** — 线程可能处于休眠态
> 2. **仅检查中断状态也是不够的** — 第三方类库可能没有正确处理中断异常（如捕获 `InterruptedException` 后未重新设置中断状态）

- 建议**自定义线程终止标志位**用于终止线程
- 使用 `shutdownNow()` 时务必谨慎

---

## 二、避免共享的设计模式

> **核心思想：没有共享就没有并发问题。**

三种避免共享的设计模式：

| 模式 | 做法 | 适用场景 |
|------|------|---------|
| 不变性（Immutability） | 对象创建后不可修改 | 缓存、值对象、配置信息 |
| 写时复制（Copy-on-Write） | 修改时先复制再替换 | 读多写少场景 |
| 线程本地存储（ThreadLocal） | 每个线程独立存储 | 上下文信息、线程安全对象 |

### 2.1 不变性（Immutability）模式

**核心思想：** 让共享变量只有读操作，没有写操作，最简单地解决并发问题。

#### 优点

1. **线程安全性** — 多线程环境下无需同步
2. **可读性** — 状态创建后不变，语义清晰
3. **性能** — 可进行更有效的缓存和优化
4. **可测试性** — 对单元测试非常友好

#### 使用场景

- **缓存系统** — 缓存数据不可变，避免被修改
- **值对象** — 常量或不可变对象
- **配置信息** — 系统配置通常是不变的

#### JDK 中的不可变类

`String`、`Long`、`Integer`、`Double` 等基础类型包装类都具备不可变性。它们严格遵守了不可变类的三点要求：

1. 类和属性都是 `final` 的
2. 所有方法均是只读的

#### 实现注意事项

**注意1：属性 final 不保证完全不可变**

```java
class Foo {
    int age = 0;
    String name = "abc";
}

final class Bar {
    final Foo foo;
    void setAge(int a) {
        foo.age = a;  // 虽然 foo 是 final，但 foo.age 仍可被修改！
    }
}
```

**注意2：引用不可变对象的对象不一定是线程安全的**

```java
// Foo 线程安全
final class Foo {
    final int age = 0;
    final String name = "abc";
}

// Bar 线程不安全
class Bar {
    Foo foo;
    void setFoo(Foo f) {
        this.foo = f;  // 对 foo 引用的修改不能保证可见性和原子性
    }
}
```

### 2.2 写时复制（Copy-on-Write）模式

**核心思想：** 共享数据被修改时，先复制一份，对副本进行修改，最后将副本替换为原始共享数据。

> Copy-on-Write 是最简单的并发解决方案，Java 中的 `String`、`Integer`、`Long` 等都基于此方案实现。

#### 优缺点

| 优点 | 缺点 |
|------|------|
| 读操作无锁，性能极致 | 消耗内存，每次修改都需复制新对象 |
| 实现简单 | 不适合写操作频繁的场景 |

> 随着 GC 算法成熟和硬件发展，内存消耗已逐渐可以接受。**读多写少的场景**非常适合使用 Copy-on-Write。

#### 使用场景

- **Java 并发容器：** `CopyOnWriteArrayList`、`CopyOnWriteArraySet` — 读操作无锁
- **操作系统：** Linux `fork()` 子进程时父子共享地址空间，写入时才复制（写时复制）
- **函数式编程：** 不可变性的基础，所有修改操作都需要 Copy-on-Write
- **RPC框架/服务注册中心：** 维护服务路由表（读多写少，一致性要求不高，5秒延迟可接受）

### 2.3 线程本地存储（ThreadLocal）模式

**核心思想：** 为每个线程创建独立的存储空间，存储线程私有的数据，实现数据隔离。

> 本质上是一种避免共享的方案——没有共享，就没有并发问题。

#### 两种避免共享的方案

| 方案 | 做法 | 缺点 |
|------|------|------|
| 局部变量 | 工具类作为局部变量使用 | 高并发场景下频繁创建对象 |
| ThreadLocal | 每个线程只创建一个工具类实例 | 需注意内存泄漏 |

#### 使用场景

1. **保存上下文信息** — 线程状态、环境变量、运行时状态
2. **管理线程安全对象** — 无需同步的对象实例
3. **实现线程特定的行为** — 跟踪日志、统计数据、授权访问

#### 线程池中使用 ThreadLocal 的注意事项

```java
ExecutorService es;
ThreadLocal tl;
es.execute(() -> {
    tl.set(obj);          // ThreadLocal 增加变量
    try {
        // 省略业务逻辑代码
    } finally {
        tl.remove();      // 手动清理 ThreadLocal，避免内存泄漏！
    }
});
```

> ⚠️ 在线程池中使用 ThreadLocal 必须手动调用 `remove()`，否则可能导致**内存泄漏**和**线程安全**问题。

---

## 三、多线程版本的 if 模式

| 模式 | 条件不满足时的行为 | 类比 |
|------|-------------------|------|
| 守护挂起（Guarded Suspension） | 一直等待直到条件满足 | 多线程版本的 `while(condition)` |
| 避免执行（Balking） | 直接放弃，不再执行 | 多线程版本的 `if(!condition) return` |

### 3.1 守护挂起（Guarded Suspension）模式

**核心思想：** 通过让线程等待来保护实例的安全性。多个线程访问实例资源时，资源本身对请求的分配做出管理。

> 别名：Guarded Wait 模式、Spin Lock 模式。更形象的非官方名：**多线程版本的 if**。

#### 实现依赖

此模式依赖于 Java 线程的等待唤醒机制：

- `synchronized` + `wait/notify/notifyAll`
- `ReentrantLock` + `Condition`（`await/signal/signalAll`）
- `CAS` + `park/unpark`

底层原理：Linux `pthread_mutex_lock/unlock`、`pthread_cond_wait/signal`

#### 代码实现

```java
public class GuardedObject<T> {
    // 结果
    private T obj;

    // 获取结果（等待方）
    public T get() {
        synchronized (this) {
            // 没有结果则等待，防止虚假唤醒
            while (obj == null) {
                try {
                    this.wait();
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
        }
        return obj;
    }

    // 产生结果（通知方）
    public void complete(T obj) {
        synchronized (this) {
            // 获取到结果，给 obj 赋值
            this.obj = obj;
            // 唤醒等待结果的线程
            this.notifyAll();
        }
    }
}
```

#### 使用场景

- JDK 中 `join()` 的实现、`Future` 的实现都采用了此模式
- 多个线程访问相同实例资源，从实例资源中获取资源并处理
- 实例资源需要管理自身拥有的资源，并对请求做出允许与否的判断

**规范实现要点：**
1. 使用 `while` 循环检查条件（防止虚假唤醒）
2. 使用 `notifyAll()` 而不是 `notify()`（确保唤醒正确的线程）

### 3.2 避免执行（Balking）模式

**核心思想：** 如果现在不适合或没必要执行某个操作，就停止处理，直接返回。

> 常用于：一个线程发现另一个线程已经做了某件事，本线程无需再做，直接结束返回。

#### Balking vs Guarded Suspension

| | Guarded Suspension | Balking |
|------|------|------|
| 条件不满足时 | 一直等待至可以运行 | 中断处理，直接返回 |
| 策略 | 等待 | 放弃 |

#### 使用场景

- `synchronized` 轻量级锁膨胀逻辑（只需一个线程膨胀获取 monitor 对象）
- DCL（Double-Checked Locking）单例实现
- 服务组件的初始化
- 编辑器的**自动保存功能**（文件没修改就直接放弃存盘）

#### 实现方式

- 锁机制：`synchronized`、`ReentrantLock`
- CAS
- 不要求原子性的场景可使用 `volatile`

#### 代码示例：自动保存

```java
boolean changed = false;

// 自动存盘操作
void autoSave() {
    synchronized (this) {
        if (!changed) {
            return;  // 没修改，直接放弃
        }
        changed = false;
    }
    // 执行存盘操作
    this.execSave();
}

// 编辑操作
void edit() {
    // 省略编辑逻辑
    // ...
    change();
}

// 改变状态
void change() {
    synchronized (this) {
        changed = true;
    }
}
```

#### 单次初始化示例

```java
boolean inited = false;

synchronized void init() {
    if (inited) {
        return;  // 已初始化，直接返回
    }
    doInit();
    inited = true;
}
```

---

## 四、多线程分工模式

| 模式 | 核心思想 | 注意事项 |
|------|---------|---------|
| Thread-Per-Message | 每个任务分配一个独立线程 | 线程创建销毁成本高，可能导致OOM |
| Worker Thread | 线程池复用线程 | 提交的任务之间不要有依赖性，避免死锁 |
| 生产者-消费者 | 任务队列解耦生产与消费 | 可直接使用线程池实现 |

### 4.1 Thread-Per-Message 模式

**核心思想：** 为每个任务分配一个独立的线程，最简单的分工方法。

#### 经典应用：网络服务端

```java
final ServerSocketChannel ssc =
    ServerSocketChannel.open().bind(new InetSocketAddress(8080));

try {
    while (true) {
        SocketChannel sc = ssc.accept();  // 接收请求
        // 每个请求都创建一个线程
        new Thread(() -> {
            try {
                ByteBuffer rb = ByteBuffer.allocateDirect(1024);
                sc.read(rb);               // 读 Socket
                Thread.sleep(2000);         // 模拟处理请求
                ByteBuffer wb = (ByteBuffer) rb.flip();
                sc.write(wb);              // 写 Socket
                sc.close();                // 关闭 Socket
            } catch (Exception e) {
                throw new UncheckedIOException(e);
            }
        }).start();
    }
} finally {
    ssc.close();
}
```

#### 适用场景

- 并发度不高的异步场景（如定时任务）
- 更适合 Go 等支持轻量级线程的语言

> ⚠️ **Java 中的局限：** Java 线程是重量级对象，创建成本高、内存占用大，不适合高并发场景。Java 中应使用线程池代替。

### 4.2 Worker Thread 模式

**核心思想：** 类比工厂车间 — 工人有活就干，没活就等着。通过线程池复用线程，避免频繁创建销毁。

#### 代码实现：用线程池改造服务端

```java
ExecutorService es = Executors.newFixedThreadPool(200);
final ServerSocketChannel ssc =
    ServerSocketChannel.open().bind(new InetSocketAddress(8080));

try {
    while (true) {
        SocketChannel sc = ssc.accept();
        // 将请求处理任务提交给线程池
        es.execute(() -> {
            try {
                ByteBuffer rb = ByteBuffer.allocateDirect(1024);
                sc.read(rb);
                Thread.sleep(2000);
                ByteBuffer wb = (ByteBuffer) rb.flip();
                sc.write(wb);
                sc.close();
            } catch (Exception e) {
                throw new UncheckedIOException(e);
            }
        });
    }
} finally {
    ssc.close();
    es.shutdown();
}
```

#### 特点

- 避免线程频繁创建、销毁
- 限制线程最大数量
- Java 中**直接使用线程池实现**

> ⚠️ 很多大厂编码规范不允许 `new Thread()` 创建线程，必须使用线程池。

### 4.3 生产者-消费者模式

**核心思想：** 类比工厂流水线 — 核心是一个任务队列，生产者线程生产任务并加入队列，消费者线程从队列获取任务并执行。

#### 代码实现

```java
public class BlockingQueueExample {
    private static final int QUEUE_CAPACITY = 5;
    private static final int PRODUCER_DELAY_MS = 1000;
    private static final int CONSUMER_DELAY_MS = 2000;

    public static void main(String[] args) throws InterruptedException {
        // 创建一个容量为 QUEUE_CAPACITY 的阻塞队列
        BlockingQueue<String> queue = new ArrayBlockingQueue<>(QUEUE_CAPACITY);

        // 生产者线程
        Runnable producer = () -> {
            while (true) {
                try {
                    queue.put("producer");  // 队列满时阻塞
                    System.out.println("生产了一个元素，队列中元素个数：" + queue.size());
                    Thread.sleep(PRODUCER_DELAY_MS);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
        };
        new Thread(producer).start();

        // 消费者线程
        Runnable consumer = () -> {
            while (true) {
                try {
                    String element = queue.take();  // 队列为空时阻塞
                    System.out.println("消费了一个元素，队列中元素个数：" + queue.size());
                    Thread.sleep(CONSUMER_DELAY_MS);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
        };
        new Thread(consumer).start();
    }
}
```

#### 三大优点

| 优点 | 说明 |
|------|------|
| **支持异步处理** | 用户注册后异步发送邮件和短信 |
| **解耦** | 订单系统通知库存系统时通过消息队列解耦 |
| **削峰填谷** | 任务队列缓冲生产者与消费者之间的速度差异 |

> 创建线程并非越多越好，线程过多会导致 CPU 上下文切换成本增大。生产者-消费者模式支持使用适量线程完成任务。

#### 过饱问题与解决方案

过饱：生产者速度 > 消费者速度，导致任务不断堆积，队列最终塞满。

**核心判断：在业务可容忍的最长响应时间内，能否处理完堆积的任务？**

| 场景 | 描述 | 解决方案 |
|------|------|---------|
| 场景一 | 消费者处理能力 < 生产者（如每天产1万件，只能消费5千件） | **消费者加机器** |
| 场景二 | 消费者能力 > 生产者，但高峰期队列被塞爆 | **适当加大队列** |
| 场景三 | 消费者能力 > 生产者，但队列无法设大 | **生产者限流** |

---

## 五、总结

本文系统讲解的四大类并发设计模式：

| 大类 | 模式 | 一句话总结 |
|------|------|-----------|
| 优雅终止 | 两阶段终止 | interrupt + 标志位，让线程自己退出 |
| 避免共享 | 不变性 | 对象不可变，谁也无法破坏 |
| 避免共享 | Copy-on-Write | 修改时复制，读多写少场景利器 |
| 避免共享 | ThreadLocal | 线程各有自己的副本，互不干扰 |
| 多线程if | Guarded Suspension | 条件不满足就一直等 |
| 多线程if | Balking | 条件不满足就直接放弃 |
| 多线程分工 | Thread-Per-Message | 每任务一线程，最简单但有成本 |
| 多线程分工 | Worker Thread | 线程池复用，大厂标配 |
| 多线程分工 | 生产者-消费者 | 流水线协作，解耦又缓冲 |

掌握这些设计模式，是写出高质量并发代码的基础。
