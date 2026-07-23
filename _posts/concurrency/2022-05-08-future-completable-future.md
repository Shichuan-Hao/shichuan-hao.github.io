---
title: Future&CompletableFuture实战
categories: [Java, 并发编程]
tags: [Future, FutureTask, CompletableFuture, 异步编程, 任务编排, Callable]
author: hsc
date: 2022-05-08 17:00:00 +0800
description: 深入讲解Future与CompletableFuture异步编程实战，涵盖任务创建、结果处理、任务编排、多任务组合等核心用法。
---


## 一、Callable&Future&FutureTask

### 1.1 为什么需要 Callable？

直接继承 `Thread` 或实现 `Runnable` 接口都可以创建线程，但这两种方法都有一个共同的问题：**没有返回值**，无法获取任务执行结果。Java 1.5 提供了 `Callable` 接口来解决这一场景。

```java
@FunctionalInterface
public interface Runnable {
    public abstract void run();
}

@FunctionalInterface
public interface Callable<V> {
    V call() throws Exception;
}
```

**Runnable 的缺陷：**
- 不能返回一个返回值
- 不能抛出 checked Exception

**Callable 的优势：**
- `call()` 方法可以有返回值
- 可以声明抛出异常
- 配合 `Future` 可了解任务执行情况、取消任务执行、获取任务执行结果

### 1.2 基本使用对比

```java
// Runnable方式 — 无返回值
new Thread(new Runnable() {
    @Override
    public void run() {
        System.out.println("通过Runnable方式执行任务");
    }
}).start();

// Callable + FutureTask方式 — 有返回值
FutureTask task = new FutureTask(new Callable() {
    @Override
    public Object call() throws Exception {
        System.out.println("通过Callable方式执行任务");
        Thread.sleep(3000);
        return "返回任务结果";
    }
});
new Thread(task).start();
System.out.println(task.get());  // 阻塞等待结果
```

### 1.3 Future 的 API

`Future` 是对 `Runnable` 或 `Callable` 任务执行结果进行**取消、查询是否完成、获取结果**的接口。`get()` 方法会阻塞直到任务返回结果。

| 方法 | 说明 |
|------|------|
| `boolean cancel(boolean mayInterruptIfRunning)` | 取消任务执行，参数指定是否立即中断任务 |
| `boolean isCancelled()` | 任务是否已经取消（正常完成前取消返回true） |
| `boolean isDone()` | 任务是否已经完成（正常终止、异常或取消都返回true） |
| `V get()` | 等待任务执行结束，获取V类型结果。可能抛出 `InterruptedException`、`ExecutionException`、`CancellationException` |
| `V get(long timeout, TimeUnit unit)` | 带超时的获取结果，超时抛出 `TimeoutException` |

### 1.4 FutureTask 说明

- `FutureTask` 是 `Future` 接口的实现类
- 相当于**消费者和生产者之间的桥梁**
- 消费者通过 `FutureTask` 存储任务处理结果，更新任务状态（未开始、正在处理、已完成等）
- 生产者拿到的 `FutureTask` 被转型为 `Future` 接口，可以阻塞获取结果
- `FutureTask` 同时实现了 `RunnableFuture` 接口，既是 `Runnable` 也是 `Future`

```java
public class FutureTaskDemo {
    public static void main(String[] args) throws ExecutionException, InterruptedException {
        Task task = new Task();
        FutureTask<Integer> futureTask = new FutureTask<>(task);   // 构建FutureTask
        new Thread(futureTask).start();                            // 作为Runnable入参
        System.out.println("task运行结果：" + futureTask.get());    // 获取结果
    }

    static class Task implements Callable<Integer> {
        @Override
        public Integer call() throws Exception {
            System.out.println("子线程正在计算");
            int sum = 0;
            for (int i = 0; i < 100; i++) {
                sum += i;
            }
            return sum;
        }
    }
}
```

### 1.5 实战案例：促销活动商品信息查询

**场景：** 维护促销活动时需要查询商品的基本信息、价格、库存、图片、销售状态等。这些信息分布在不同业务中心，由不同系统提供服务。

**同步方式问题：** 假设每个接口需要50ms，一个商品查询需要 200ms-300ms。

**Future改造后：** 并行查询，只需最长耗时接口的时间（约50ms）。

```java
public class FutureTaskDemo2 {
    public static void main(String[] args) throws ExecutionException, InterruptedException {
        FutureTask<String> ft1 = new FutureTask<>(new T1Task());  // 商品基本信息
        FutureTask<String> ft2 = new FutureTask<>(new T2Task());  // 商品价格
        FutureTask<String> ft3 = new FutureTask<>(new T3Task());  // 商品库存
        FutureTask<String> ft4 = new FutureTask<>(new T4Task());  // 商品图片
        FutureTask<String> ft5 = new FutureTask<>(new T5Task());  // 商品销售状态

        ExecutorService executorService = Executors.newFixedThreadPool(5);
        executorService.submit(ft1);
        executorService.submit(ft2);
        executorService.submit(ft3);
        executorService.submit(ft4);
        executorService.submit(ft5);

        // 获取执行结果
        System.out.println(ft1.get());
        System.out.println(ft2.get());
        System.out.println(ft3.get());
        System.out.println(ft4.get());
        System.out.println(ft5.get());

        executorService.shutdown();
    }

    static class T1Task implements Callable<String> {
        @Override
        public String call() throws Exception {
            System.out.println("T1:查询商品基本信息...");
            TimeUnit.MILLISECONDS.sleep(50);
            return "商品基本信息查询成功";
        }
    }
    // T2Task ~ T5Task 类似...
}
```

### 1.6 Future 的局限性

1. **并发执行多任务：** `get()` 是阻塞的，除了等待没有其他方式
2. **无法链式调用：** 任务完成后无法自动触发特定动作（如发邮件）
3. **无法组合多个任务：** 10个任务全部执行完后触发特定动作，Future无能为力
4. **没有异常处理：** Future接口中没有异常处理方法

---

## 二、CompletableFuture 使用详解

`CompletableFuture` 是 `Future` 接口的扩展和增强，完美弥补了 Future 的种种问题。**核心能力是任务编排**——可以轻松组织不同任务的运行顺序、规则及方式。

### 2.1 应用场景总览

| 关系类型 | 方法 | 说明 |
|---------|------|------|
| **依赖关系** | `thenApply()` | 将前面任务的结果交给后面的 Function |
| **依赖关系** | `thenCompose()` | 连接两个有依赖关系的任务，结果由第二个任务返回 |
| **and聚合** | `thenCombine` | 任务合并，有返回值 |
| **and聚合** | `thenAcceptBoth` | 两个任务完成后交给消耗，无返回值 |
| **and聚合** | `runAfterBoth` | 两个任务完成后执行下一步（Runnable） |
| **or聚合** | `applyToEither` | 两个任务谁快用谁的结果，有返回值 |
| **or聚合** | `acceptEither` | 两个任务谁快消耗谁的结果，无返回值 |
| **or聚合** | `runAfterEither` | 任意一个完成即执行下一步（Runnable） |
| **并行执行** | `anyOf()` / `allOf()` | 多 CompletableFuture 并行执行 |

### 2.2 创建异步操作

```java
// 无返回值
public static CompletableFuture<Void> runAsync(Runnable runnable)
public static CompletableFuture<Void> runAsync(Runnable runnable, Executor executor)

// 有返回值
public static <U> CompletableFuture<U> supplyAsync(Supplier<U> supplier)
public static <U> CompletableFuture<U> supplyAsync(Supplier<U> supplier, Executor executor)
```

**区别：**
- `runAsync` — `Runnable` 参数，无返回结果
- `supplyAsync` — `Supplier` 参数，返回结果类型为 `U`（`get()` 有返回值但会阻塞）
- 不指定 `Executor` → 使用 `ForkJoinPool.commonPool()`（默认线程数 = CPU核数）
- 指定 `Executor` → 使用自定义线程池

> ⚠️ **重要：** 所有 `CompletableFuture` 共享一个线程池时，有任务执行慢I/O操作会导致所有线程都阻塞，造成**线程饥饿**。强烈建议根据不同业务类型创建不同的线程池。

```java
// runAsync — 无返回值
Runnable runnable = () -> System.out.println("执行无返回结果的异步任务");
CompletableFuture.runAsync(runnable);

// supplyAsync — 有返回值
CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> {
    System.out.println("执行有返回值的异步任务");
    try { Thread.sleep(5000); } catch (InterruptedException e) { e.printStackTrace(); }
    return "Hello World";
});
String result = future.get();
System.out.println(result);
```

### 2.3 获取结果：join & get

| 方法 | 异常处理 |
|------|---------|
| `join()` | 抛出 unchecked 异常，不强制开发者处理 |
| `get()` | 抛出 checked 异常（`ExecutionException`, `InterruptedException`），需手动 try-catch 或 throws |

### 2.4 结果处理

```java
public CompletableFuture<T> whenComplete(BiConsumer<? super T, ? super Throwable> action)
public CompletableFuture<T> whenCompleteAsync(BiConsumer<? super T, ? super Throwable> action)
public CompletableFuture<T> whenCompleteAsync(BiConsumer<? super T, ? super Throwable> action, Executor executor)
public CompletableFuture<T> exceptionally(Function<Throwable, ? extends T> fn)
```

- `BiConsumer<? super T, ? super Throwable>` — 可处理正常结果或异常情况
- 不以 `Async` 结尾 → Action 使用相同线程执行
- 以 `Async` 结尾 → 可能使用其他线程执行
- 这些都返回 `CompletableFuture`，结果返回原始计算结果或异常

```java
CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> {
    try { TimeUnit.SECONDS.sleep(1); } catch (InterruptedException e) { }
    if (new Random().nextInt(10) % 2 == 0) {
        int i = 12 / 0;     // 随机触发异常
    }
    System.out.println("执行结束！");
    return "test";
});

future.whenComplete(new BiConsumer<String, Throwable>() {
    @Override
    public void accept(String t, Throwable action) {
        System.out.println(t + " 执行完成！");
    }
});

future.exceptionally(new Function<Throwable, String>() {
    @Override
    public String apply(Throwable t) {
        System.out.println("执行失败：" + t.getMessage());
        return "异常xxxx";
    }
}).join();

// 正常输出：  test 执行完成！
// 异常输出：  执行失败：java.lang.ArithmeticException: / by zero
//            null 执行完成！
```

### 2.5 结果转换

#### thenApply

将上一阶段任务的执行结果作为入参，产生新的结果。

```java
public <U> CompletableFuture<U> thenApply(Function<? super T, ? extends U> fn)
public <U> CompletableFuture<U> thenApplyAsync(Function<? super T, ? extends U> fn)
public <U> CompletableFuture<U> thenApplyAsync(Function<? super T, ? extends U> fn, Executor executor)
```

```java
CompletableFuture<Integer> future = CompletableFuture.supplyAsync(() -> {
    int result = 100;
    System.out.println("一阶段：" + result);
    return result;
}).thenApply(number -> {
    int result = number * 3;
    System.out.println("二阶段：" + result);
    return result;
});

System.out.println("最终结果：" + future.get());
// 一阶段：100
// 二阶段：300
// 最终结果：300
```

#### thenCompose

参数为返回 `CompletableFuture` 实例的函数，该函数的参数是上一阶段的计算结果。用于**连接两个有依赖关系的任务**。

```java
public <U> CompletableFuture<U> thenCompose(Function<? super T, ? extends CompletionStage<U>> fn);
public <U> CompletableFuture<U> thenComposeAsync(Function<? super T, ? extends CompletionStage<U>> fn);
```

```java
CompletableFuture<Integer> future = CompletableFuture
    .supplyAsync(new Supplier<Integer>() {
        @Override
        public Integer get() {
            int number = new Random().nextInt(30);
            System.out.println("第一阶段：" + number);
            return number;
        }
    })
    .thenCompose(new Function<Integer, CompletionStage<Integer>>() {
        @Override
        public CompletionStage<Integer> apply(Integer param) {
            return CompletableFuture.supplyAsync(new Supplier<Integer>() {
                @Override
                public Integer get() {
                    int number = param * 2;
                    System.out.println("第二阶段：" + number);
                    return number;
                }
            });
        }
    });
System.out.println("最终结果: " + future.get());
// 第一阶段：10
// 第二阶段：20
// 最终结果: 20
```

#### thenApply vs thenCompose 的区别

| | thenApply | thenCompose |
|------|------|------|
| 转换对象 | 泛型中的类型 | 将内部 `CompletableFuture` 展开 |
| 返回 | **同一个** CompletableFuture | **新的** CompletableFuture |

```java
CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> "Hello");

CompletableFuture<String> result1 = future.thenApply(param -> param + " World");
CompletableFuture<String> result2 = future
    .thenCompose(param -> CompletableFuture.supplyAsync(() -> param + " World"));

System.out.println(result1.get());  // Hello World
System.out.println(result2.get());  // Hello World
```

### 2.6 结果消费

与结果转换不同，结果消费只对结果执行 Action，**不返回新的计算值**。

#### thenAccept — 单个结果消费

```java
public CompletionStage<Void> thenAccept(Consumer<? super T> action);
public CompletionStage<Void> thenAcceptAsync(Consumer<? super T> action);
public CompletionStage<Void> thenAcceptAsync(Consumer<? super T> action, Executor executor);
```

```java
CompletableFuture<Void> future = CompletableFuture
    .supplyAsync(() -> {
        int number = new Random().nextInt(10);
        System.out.println("第一阶段：" + number);
        return number;
    }).thenAccept(number ->
        System.out.println("第二阶段：" + number * 5));

System.out.println("最终结果：" + future.get());
// 第一阶段：8
// 第二阶段：40
// 最终结果：null   <- Void类型
```

#### thenAcceptBoth — 两个结果消费

两个 `CompletionStage` 都正常完成计算后，执行提供的 action 消费两个异步结果。

```java
public <U> CompletionStage<Void> thenAcceptBoth(CompletionStage<? extends U> other,
    BiConsumer<? super T, ? super U> action);
```

```java
CompletableFuture<Integer> future1 = CompletableFuture.supplyAsync(() -> {
    int number = new Random().nextInt(3) + 1;
    try { TimeUnit.SECONDS.sleep(number); } catch (InterruptedException e) { e.printStackTrace(); }
    System.out.println("第一阶段：" + number);
    return number;
});

CompletableFuture<Integer> future2 = CompletableFuture.supplyAsync(() -> {
    int number = new Random().nextInt(3) + 1;
    try { TimeUnit.SECONDS.sleep(number); } catch (InterruptedException e) { e.printStackTrace(); }
    System.out.println("第二阶段：" + number);
    return number;
});

future1.thenAcceptBoth(future2, new BiConsumer<Integer, Integer>() {
    @Override
    public void accept(Integer x, Integer y) {
        System.out.println("最终结果：" + (x + y));
    }
}).join();
// 第二阶段：1
// 第一阶段：2
// 最终结果：3
```

#### thenRun — 不关心结果

上一阶段完成后执行一个 `Runnable`，**不使用计算结果**。

```java
public CompletionStage<Void> thenRun(Runnable action);
public CompletionStage<Void> thenRunAsync(Runnable action);
```

```java
CompletableFuture<Void> future = CompletableFuture.supplyAsync(() -> {
    int number = new Random().nextInt(10);
    System.out.println("第一阶段：" + number);
    return number;
}).thenRun(() -> System.out.println("thenRun 执行"));

System.out.println("最终结果：" + future.get());
// 第一阶段：2
// thenRun 执行
// 最终结果：null
```

### 2.7 结果组合：thenCombine

合并两个线程任务的结果，并进一步处理。**有返回值。**

```java
public <U,V> CompletionStage<V> thenCombine(CompletionStage<? extends U> other,
    BiFunction<? super T, ? super U, ? extends V> fn);
```

```java
CompletableFuture<Integer> future1 = CompletableFuture.supplyAsync(() -> {
    int number = new Random().nextInt(10);
    System.out.println("第一阶段：" + number);
    return number;
});
CompletableFuture<Integer> future2 = CompletableFuture.supplyAsync(() -> {
    int number = new Random().nextInt(10);
    System.out.println("第二阶段：" + number);
    return number;
});

CompletableFuture<Integer> result = future1.thenCombine(future2, new BiFunction<Integer, Integer, Integer>() {
    @Override
    public Integer apply(Integer x, Integer y) {
        return x + y;
    }
});
System.out.println("最终结果：" + result.get());
// 第一阶段：9
// 第二阶段：5
// 最终结果：14
```

### 2.8 任务交互（竞速）

#### applyToEither — 谁快用谁，有返回值

```java
public <U> CompletionStage<U> applyToEither(CompletionStage<? extends T> other,
    Function<? super T, U> fn);
```

```java
future1.applyToEither(future2, new Function<Integer, Integer>() {
    @Override
    public Integer apply(Integer number) {
        System.out.println("最快结果：" + number);
        return number * 2;
    }
}).join();
// 第一阶段start：6
// 第二阶段start：5
// 第二阶段end：5
// 最快结果：5
```

#### acceptEither — 谁快消耗谁，无返回值

```java
public CompletionStage<Void> acceptEither(CompletionStage<? extends T> other, Consumer<? super T> action);
```

```java
future1.acceptEither(future2, new Consumer<Integer>() {
    @Override
    public void accept(Integer number) {
        System.out.println("最快结果：" + number);
    }
}).join();
// 第二阶段：3
// 最快结果：3
```

#### runAfterEither — 任意完成即执行

不关心运行结果，任意一个任务完成即进行下一步操作。

```java
public CompletionStage<Void> runAfterEither(CompletionStage<?> other, Runnable action);
```

```java
future1.runAfterEither(future2, new Runnable() {
    @Override
    public void run() {
        System.out.println("已经有一个任务完成了");
    }
}).join();
// 第一阶段：3
// 已经有一个任务完成了
```

#### runAfterBoth — 两个都完成才执行

两个全部执行完成后才进行下一步，不关心结果。

```java
public CompletionStage<Void> runAfterBoth(CompletionStage<?> other, Runnable action);
```

```java
CompletableFuture<Integer> future1 = CompletableFuture.supplyAsync(() -> {
    try { TimeUnit.SECONDS.sleep(1); } catch (InterruptedException e) { }
    System.out.println("第一阶段：1");
    return 1;
});
CompletableFuture<Integer> future2 = CompletableFuture.supplyAsync(() -> {
    try { TimeUnit.SECONDS.sleep(2); } catch (InterruptedException e) { }
    System.out.println("第二阶段：2");
    return 2;
});

future1.runAfterBoth(future2, new Runnable() {
    @Override
    public void run() {
        System.out.println("上面两个任务都执行完成了。");
    }
}).get();
// 第一阶段：1
// 第二阶段：2
// 上面两个任务都执行完成了。
```

#### anyOf — 任意一个完成即返回

参数是多个 `CompletableFuture`，当**任何一个**完成时返回该 `CompletableFuture`。

```java
public static CompletableFuture<Object> anyOf(CompletableFuture<?>... cfs)
```

```java
Random random = new Random();
CompletableFuture<String> future1 = CompletableFuture.supplyAsync(() -> {
    try { TimeUnit.SECONDS.sleep(random.nextInt(5)); } catch (InterruptedException e) { }
    return "hello";
});
CompletableFuture<String> future2 = CompletableFuture.supplyAsync(() -> {
    try { TimeUnit.SECONDS.sleep(random.nextInt(1)); } catch (InterruptedException e) { }
    return "world";
});
CompletableFuture<Object> result = CompletableFuture.anyOf(future1, future2);
System.out.println(result.get());
// world     (future2 更快完成)
```

#### allOf — 全部完成才返回

多 `CompletableFuture` 同步等待全部完成。

```java
public static CompletableFuture<Void> allOf(CompletableFuture<?>... cfs)
```

```java
CompletableFuture<String> future1 = CompletableFuture.supplyAsync(() -> {
    try { TimeUnit.SECONDS.sleep(2); } catch (InterruptedException e) { }
    System.out.println("future1完成！");
    return "future1完成！";
});
CompletableFuture<String> future2 = CompletableFuture.supplyAsync(() -> {
    System.out.println("future2完成！");
    return "future2完成！";
});

CompletableFuture<Void> combinedFuture = CompletableFuture.allOf(future1, future2);
combinedFuture.get();
System.out.println("future1: " + future1.isDone() + "，future2: " + future2.isDone());
// future2完成！
// future1完成！
// future1: true，future2: true
```

### 2.9 综合案例：烧水泡茶

著名数学家华罗庚《统筹方法》中的经典问题。最优分工：

- **T1：** 洗水壶 → 烧开水 → 泡茶（泡茶需等待 T2 的茶叶）
- **T2：** 洗茶壶 → 洗茶杯 → 拿茶叶

#### 基于 Future 实现

```java
public class FutureTaskDemo3 {
    public static void main(String[] args) throws ExecutionException, InterruptedException {
        FutureTask<String> ft2 = new FutureTask<>(new T2Task());
        FutureTask<String> ft1 = new FutureTask<>(new T1Task(ft2));

        Thread T1 = new Thread(ft1);
        T1.start();
        Thread T2 = new Thread(ft2);
        T2.start();

        System.out.println(ft1.get());  // 等待T1执行结果
    }
}

// T1：洗水壶 → 烧开水 → 泡茶
class T1Task implements Callable<String> {
    FutureTask<String> ft2;
    T1Task(FutureTask<String> ft2) { this.ft2 = ft2; }

    @Override
    public String call() throws Exception {
        System.out.println("T1:洗水壶...");
        TimeUnit.SECONDS.sleep(1);

        System.out.println("T1:烧开水...");
        TimeUnit.SECONDS.sleep(15);

        String tf = ft2.get();                     // 获取T2的茶叶
        System.out.println("T1:拿到茶叶:" + tf);

        System.out.println("T1:泡茶...");
        return "上茶:" + tf;
    }
}

// T2：洗茶壶 → 洗茶杯 → 拿茶叶
class T2Task implements Callable<String> {
    @Override
    public String call() throws Exception {
        System.out.println("T2:洗茶壶...");
        TimeUnit.SECONDS.sleep(1);

        System.out.println("T2:洗茶杯...");
        TimeUnit.SECONDS.sleep(2);

        System.out.println("T2:拿茶叶...");
        TimeUnit.SECONDS.sleep(1);
        return "龙井";
    }
}
```

#### 基于 CompletableFuture 实现（推荐）

```java
public class CompletableFutureDemo2 {
    public static void main(String[] args) {
        // 任务1：洗水壶 → 烧开水
        CompletableFuture<Void> f1 = CompletableFuture.runAsync(() -> {
            System.out.println("T1:洗水壶...");
            sleep(1, TimeUnit.SECONDS);
            System.out.println("T1:烧开水...");
            sleep(15, TimeUnit.SECONDS);
        });

        // 任务2：洗茶壶 → 洗茶杯 → 拿茶叶
        CompletableFuture<String> f2 = CompletableFuture.supplyAsync(() -> {
            System.out.println("T2:洗茶壶...");
            sleep(1, TimeUnit.SECONDS);
            System.out.println("T2:洗茶杯...");
            sleep(2, TimeUnit.SECONDS);
            System.out.println("T2:拿茶叶...");
            sleep(1, TimeUnit.SECONDS);
            return "龙井";
        });

        // 任务3：任务1和任务2完成后执行 → 泡茶
        CompletableFuture<String> f3 = f1.thenCombine(f2, (__, tf) -> {
            System.out.println("T1:拿到茶叶:" + tf);
            System.out.println("T1:泡茶...");
            return "上茶:" + tf;
        });

        System.out.println(f3.join());
    }

    static void sleep(int t, TimeUnit u) {
        try { u.sleep(t); } catch (InterruptedException e) { }
    }
}
```

> `CompletableFuture` 版代码更简洁，任务编排清晰，无需手动传递 `FutureTask` 引用。

---

## 三、总结

| 主题 | 要点 |
|------|------|
| **Callable vs Runnable** | Callable 有返回值、可抛异常，功能更强 |
| **Future** | 取消/查询/获取结果，`get()` 阻塞 |
| **FutureTask** | Future 实现类，同时是 Runnable 和 Future |
| **Future局限性** | 阻塞获取、无法链式调用、无法组合任务、无异常处理 |
| **CompletableFuture** | 完善的异步编程工具，核心是**任务编排能力** |
| **创建** | `runAsync`（无返回值）、`supplyAsync`（有返回值），建议指定线程池 |
| **结果处理** | `whenComplete` / `exceptionally` |
| **结果转换** | `thenApply` / `thenCompose`（依赖型） |
| **结果消费** | `thenAccept` / `thenAcceptBoth` / `thenRun` |
| **结果组合** | `thenCombine`（and关系） |
| **竞速** | `applyToEither` / `acceptEither` / `runAfterEither`（or关系） |
| **并行** | `anyOf` / `allOf` |
