---
title: 线程池ThreadPoolExecutor实战及其原理分析
categories: [Java, 并发编程]
tags: [ThreadPoolExecutor, 线程池, 核心参数, 源码分析, execute, addWorker, runWorker, getTask, shutdown, 拒绝策略]
author: hsc
date: 2022-05-18 00:00:00 +0800
description: 深入剖析ThreadPoolExecutor的核心参数、执行流程与源码实现，涵盖线程创建、任务调度、线程回收、关闭机制等完整分析。
mindmap:
---

# 线程池ThreadPoolExecutor实战及其原理分析

## 一、线程池基础概念

### 1.1 为什么需要线程池？

- **线程的创建和销毁开销大**：频繁创建/销毁线程会消耗大量系统资源
- **线程管理复杂**：需要控制并发数量，防止资源耗尽
- **任务与线程解耦**：提交任务后由线程池统一调度执行

### 1.2 线程池的核心优势

| 优势 | 说明 |
|------|------|
| 降低资源消耗 | 复用已创建的线程，减少创建和销毁的开销 |
| 提高响应速度 | 任务到达时无需等待创建线程即可立即执行 |
| 提高线程可管理性 | 统一分配、调优和监控线程 |
| 提供更多功能 | 支持定时执行、定期执行、单线程、并发数控制等 |

---

## 二、ThreadPoolExecutor 核心参数

### 2.1 七大核心参数

```java
public ThreadPoolExecutor(int corePoolSize,
                          int maximumPoolSize,
                          long keepAliveTime,
                          TimeUnit unit,
                          BlockingQueue<Runnable> workQueue,
                          ThreadFactory threadFactory,
                          RejectedExecutionHandler handler)
```

| 参数 | 含义 |
|------|------|
| **corePoolSize** | 核心线程数，线程池中长期保持的线程数量 |
| **maximumPoolSize** | 最大线程数，核心线程+非核心线程的总上限 |
| **keepAliveTime** | 非核心线程的空闲存活时间 |
| **unit** | 时间单位 |
| **workQueue** | 阻塞队列，用于存放待执行的任务 |
| **threadFactory** | 线程工厂，用于创建线程 |
| **rejectedExecutionHandler** | 拒绝策略，当线程池无法处理新任务时触发 |

### 2.2 线程池状态流转

ThreadPoolExecutor 使用 `ctl`（一个 AtomicInteger）的高3位表示状态，低29位表示工作线程数。

| 状态 | 值 | 含义 |
|------|------|------|
| **RUNNING** | -1 | 接受新任务，处理队列中的任务 |
| **SHUTDOWN** | 0 | 不接受新任务，但处理队列中的任务 |
| **STOP** | 1 | 不接受新任务，不处理队列中的任务，中断正在执行的任务 |
| **TIDYING** | 2 | 所有任务已终止，工作线程数为0，将调用 `terminated()` |
| **TERMINATED** | 3 | `terminated()` 方法已执行完毕 |

状态转换：
```
RUNNING -> SHUTDOWN (调用shutdown())
RUNNING -> STOP (调用shutdownNow())
SHUTDOWN -> TIDYING (队列和线程都为空)
STOP -> TIDYING (线程池为空)
TIDYING -> TERMINATED (terminated()执行完毕)
```

---

## 三、线程池执行流程

### 3.1 execute 方法 — 任务提交流程

```java
public void execute(Runnable command) {
    if (command == null)
        throw new NullPointerException();
    
    int c = ctl.get();
    // 1. 当前工作线程数 < corePoolSize：直接创建核心线程执行
    if (workerCountOf(c) < corePoolSize) {
        if (addWorker(command, true))
            return;
        c = ctl.get();
    }
    // 2. 线程池是RUNNING状态，尝试将任务入队
    if (isRunning(c) && workQueue.offer(command)) {
        int recheck = ctl.get();
        // 再次检查：如果线程池已经不是RUNNING，则移除任务并拒绝
        if (!isRunning(recheck) && remove(command))
            reject(command);
        // 如果线程池仍是RUNNING但工作线程为0，则创建一个空任务线程
        else if (workerCountOf(recheck) == 0)
            addWorker(null, false);
    }
    // 3. 队列满了，尝试创建非核心线程
    else if (!addWorker(command, false))
        // 4. 超过maximumPoolSize，执行拒绝策略
        reject(command);
}
```

执行流程总结：

```
提交任务
  ├── 工作线程 < corePoolSize？ → 创建核心线程
  ├── 队列未满？ → 入队等待
  ├── 工作线程 < maximumPoolSize？ → 创建非核心线程
  └── 否则 → 执行拒绝策略
```

### 3.2 四种拒绝策略

| 策略 | 说明 |
|------|------|
| **AbortPolicy**（默认） | 直接抛出 `RejectedExecutionException` |
| **CallerRunsPolicy** | 由调用者线程执行该任务 |
| **DiscardPolicy** | 直接丢弃，不抛异常 |
| **DiscardOldestPolicy** | 丢弃队列中最旧的任务，然后重试提交 |

---

## 四、源码深度分析

### 4.1 addWorker 方法 — 添加工作线程

核心逻辑分为两大步骤：

**第一步：判断是否允许创建**

```java
private boolean addWorker(Runnable firstTask, boolean core) {
    retry:
    for (;;) {
        int c = ctl.get();
        int rs = runStateOf(c);
        
        // 线程池状态检查
        // SHUTDOWN + 队列为空 → 不创建
        // STOP → 不创建
        if (rs >= SHUTDOWN &&
            !(rs == SHUTDOWN && firstTask == null && !workQueue.isEmpty()))
            return false;
        
        // 工作线程数检查
        for (;;) {
            int wc = workerCountOf(c);
            // core=true: 比较corePoolSize; core=false: 比较maximumPoolSize
            if (wc >= CAPACITY ||
                wc >= (core ? corePoolSize : maximumPoolSize))
                return false;
            // CAS 增加工作线程数
            if (compareAndIncrementWorkerCount(c))
                break retry;
            c = ctl.get();
            if (runStateOf(c) != rs)
                continue retry;
        }
    }
    // ... 第二步：创建并启动线程
}
```

**第二步：创建 Worker 并启动**

```java
    boolean workerStarted = false;
    boolean workerAdded = false;
    Worker w = null;
    try {
        w = new Worker(firstTask);   // Worker构造时会通过ThreadFactory创建线程
        final Thread t = w.thread;
        if (t != null) {
            final ReentrantLock mainLock = this.mainLock;
            mainLock.lock();
            try {
                int rs = runStateOf(ctl.get());
                // RUNNING 状态，或 SHUTDOWN + firstTask==null（特例）
                if (rs < SHUTDOWN ||
                    (rs == SHUTDOWN && firstTask == null)) {
                    if (t.isAlive()) throw new IllegalThreadStateException();
                    workers.add(w);
                    int s = workers.size();
                    if (s > largestPoolSize)
                        largestPoolSize = s;  // 记录峰值
                    workerAdded = true;
                }
            } finally {
                mainLock.unlock();
            }
            if (workerAdded) {
                t.start();          // 启动线程
                workerStarted = true;
            }
        }
    } finally {
        if (!workerStarted)
            addWorkerFailed(w);     // 失败处理：移除Worker，工作线程数-1
    }
    return workerStarted;
}
```

**核心线程 vs 非核心线程区别**：

- `core=true`：判断是否超过 `corePoolSize`，核心线程默认可不回收
- `core=false`：判断是否超过 `maximumPoolSize`，非核心超时后会回收

**特例情况**：当线程池状态为 `SHUTDOWN`，但队列中还有任务，且所有线程都被回收后，需要创建一个空任务的线程来处理队列。

### 4.2 Worker 结构与 runWorker 方法

```java
// Worker 构造方法
Worker(Runnable firstTask) {
    setState(-1);     // 禁止中断（直到 runWorker）
    this.firstTask = firstTask;
    this.thread = getThreadFactory().newThread(this);  // this作为Runnable传入
}

// Worker 的 run 方法
public void run() {
    runWorker(this);
}
```

**runWorker 核心循环**：

```java
final void runWorker(Worker w) {
    Thread wt = Thread.currentThread();
    Runnable task = w.firstTask;
    w.firstTask = null;
    w.unlock();     // 允许中断
    
    boolean completedAbruptly = true;
    try {
        // 循环获取任务：先取firstTask，再通过getTask()从队列取
        while (task != null || (task = getTask()) != null) {
            w.lock();
            
            // 中断处理：线程池STOP时确保线程被中断
            if ((runStateAtLeast(ctl.get(), STOP) ||
                 (Thread.interrupted() && runStateAtLeast(ctl.get(), STOP))) &&
                !wt.isInterrupted())
                wt.interrupt();
            
            try {
                beforeExecute(wt, task);   // 扩展点
                Throwable thrown = null;
                try {
                    task.run();            // 执行任务
                } catch (RuntimeException x) {
                    thrown = x; throw x;
                } catch (Error x) {
                    thrown = x; throw x;
                } catch (Throwable x) {
                    thrown = x; throw new Error(x);
                } finally {
                    afterExecute(task, thrown);  // 扩展点
                }
            } finally {
                task = null;
                w.completedTasks++;
                w.unlock();
            }
        }
        completedAbruptly = false;  // 正常退出标记
    } finally {
        processWorkerExit(w, completedAbruptly);  // 退出处理
    }
}
```

### 4.3 getTask 方法 — 从队列获取任务

```java
private Runnable getTask() {
    boolean timedOut = false;
    for (;;) {
        int c = ctl.get();
        int rs = runStateOf(c);
        
        // 线程池状态检查：STOP 或 SHUTDOWN+队列空 → 线程退出
        if (rs >= SHUTDOWN && (rs >= STOP || workQueue.isEmpty())) {
            decrementWorkerCount();
            return null;
        }
        
        int wc = workerCountOf(c);
        
        // 是否需要超时控制
        // allowCoreThreadTimeOut=true → 所有线程超时
        // allowCoreThreadTimeOut=false → 仅非核心线程超时
        boolean timed = allowCoreThreadTimeOut || wc > corePoolSize;
        
        // 超时退出判断
        if ((wc > maximumPoolSize || (timed && timedOut))
            && (wc > 1 || workQueue.isEmpty())) {
            if (compareAndDecrementWorkerCount(c))
                return null;
            continue;
        }
        
        try {
            // timed: 带超时的poll  /  !timed: 无限阻塞的take
            Runnable r = timed ?
                workQueue.poll(keepAliveTime, TimeUnit.NANOSECONDS) :
                workQueue.take();
                
            if (r != null)
                return r;
            timedOut = true;  // 超时标记
        } catch (InterruptedException retry) {
            timedOut = false; // 中断不视为超时
        }
    }
}
```

线程退出的三种情况：
1. **被中断** → getTask 返回 null → 退出循环
2. **阻塞超时** → getTask 返回 null → 退出循环
3. **执行任务抛异常** → 直接跳出 while → completedAbruptly=true

### 4.4 processWorkerExit 方法 — 线程退出处理

```java
private void processWorkerExit(Worker w, boolean completedAbruptly) {
    // 异常退出：工作线程数-1（正常退出时getTask已完成）
    if (completedAbruptly)
        decrementWorkerCount();
    
    final ReentrantLock mainLock = this.mainLock;
    mainLock.lock();
    try {
        completedTaskCount += w.completedTasks;
        workers.remove(w);          // 从workers集合移除
    } finally {
        mainLock.unlock();
    }
    
    tryTerminate();                 // 尝试终止线程池
    
    int c = ctl.get();
    if (runStateLessThan(c, STOP)) {
        if (!completedAbruptly) {
            int min = allowCoreThreadTimeOut ? 0 : corePoolSize;
            if (min == 0 && !workQueue.isEmpty())
                min = 1;
            // 当前线程数 >= 最小保留数 → 不需要补充
            if (workerCountOf(c) >= min)
                return;
        }
        // 需要补充线程：异常退出必须补，或线程数不足
        addWorker(null, false);
    }
}
```

要点：
- `completedAbruptly=true`（异常退出）→ 必须新开一个线程替补
- `completedAbruptly=false`（正常退出）→ 线程数不足时补充

### 4.5 shutdown 与 shutdownNow

**shutdown()**：不接受新任务，但把队列中的任务执行完

```java
public void shutdown() {
    final ReentrantLock mainLock = this.mainLock;
    mainLock.lock();
    try {
        checkShutdownAccess();
        advanceRunState(SHUTDOWN);      // 状态 → SHUTDOWN
        interruptIdleWorkers();         // 中断空闲线程
        onShutdown();                   // 扩展点
    } finally {
        mainLock.unlock();
    }
    tryTerminate();
}

// 只中断空闲线程（加锁=执行中，未加锁=空闲）
private void interruptIdleWorkers(boolean onlyOne) {
    final ReentrantLock mainLock = this.mainLock;
    mainLock.lock();
    try {
        for (Worker w : workers) {
            Thread t = w.thread;
            if (!t.isInterrupted() && w.tryLock()) {  // 拿得到锁=空闲
                try {
                    t.interrupt();
                } catch (SecurityException ignore) {
                } finally {
                    w.unlock();
                }
            }
            if (onlyOne) break;
        }
    } finally {
        mainLock.unlock();
    }
}
```

> **关键设计**：Worker 在执行任务时会 `w.lock()`，`tryLock()` 拿不到锁说明正在执行，不中断。但被中断的线程会在 `processWorkerExit` 中重新补充新线程，确保队列中的任务最终都能执行完。

**shutdownNow()**：不接受新任务，中断所有线程，返回队列中未执行的任务

```java
public List<Runnable> shutdownNow() {
    List<Runnable> tasks;
    final ReentrantLock mainLock = this.mainLock;
    mainLock.lock();
    try {
        checkShutdownAccess();
        advanceRunState(STOP);           // 状态 → STOP
        interruptWorkers();              // 中断所有线程
        tasks = drainQueue();            // 清空队列并返回
    } finally {
        mainLock.unlock();
    }
    tryTerminate();
    return tasks;
}
```

### 4.6 mainLock 的作用

`mainLock` 是线程池中的全局锁，用于保护 `workers` 集合的并发安全：

- 防止在 `shutdown` 时新任务提交导致状态不一致
- 确保 `workers.add/remove` 的原子性
- 保证中断操作与线程启停的有序性

---

## 五、线程池的工作机制总结

```
提交任务 execute(command)
    │
    ▼
核心线程数未满？ ──Yes──▶ addWorker(command, true) → 创建核心线程直接执行
    │
    No
    │
    ▼
队列未满？ ──Yes──▶ workQueue.offer(command) → 入队等待
    │
    No
    │
    ▼
线程数 < maximumPoolSize？ ──Yes──▶ addWorker(command, false) → 创建非核心线程
    │
    No
    │
    ▼
reject(command) → 执行拒绝策略

工作线程生命周期：
    Worker.start() → runWorker() → while循环执行 + getTask()获取
        ├── 执行完 → 继续 getTask()
        ├── 超时 → getTask()=null → processWorkerExit → 可能补充线程
        ├── 中断 → getTask()=null → processWorkerExit → 可能补充线程
        └── 异常 → completedAbruptly=true → processWorkerExit → 必须补充线程
```

---

## 六、常用线程池及使用建议

### 6.1 Executors 提供的线程池

| 工厂方法 | 特点 | 风险 |
|----------|------|------|
| `newFixedThreadPool` | 固定核心线程，无界队列 | OOM（队列无限增长） |
| `newCachedThreadPool` | 可缓存线程，同步队列 | 线程无限增长 |
| `newSingleThreadExecutor` | 单线程，无界队列 | OOM |
| `newScheduledThreadPool` | 定时任务线程池 | - |

### 6.2 最佳实践

1. **不要用 Executors 创建**，使用 `new ThreadPoolExecutor` 显式指定参数
2. **合理设置线程数**：CPU密集型 = N+1，IO密集型 = 2N
3. **使用有界队列**：配合恰当的拒绝策略
4. **给线程命名**：方便排查问题
5. **监控线程池状态**：`getActiveCount()`, `getCompletedTaskCount()` 等

---

## 七、总结

ThreadPoolExecutor 是 Java 并发编程的核心基础设施，理解其源码有助于：

- 合理配置线程池参数，避免线上故障
- 理解任务提交流程，排查性能问题
- 掌握线程生命周期管理机制
- 深入理解 `shutdown`/`shutdownNow` 的差异
- 理解 `mainLock` 在并发控制中的作用
