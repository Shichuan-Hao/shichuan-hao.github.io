---
title: 线程池ForkJoinPool实战及其工作原理分析
categories: [Java, 并发编程]
tags: [ForkJoinPool, 工作窃取, ForkJoinTask, RecursiveTask, RecursiveAction, ForkJoin框架, 分治算法]
author: hsc
date: 2022-05-19 00:00:00 +0800
description: 深入讲解ForkJoinPool的分治思想、工作窃取算法、核心API使用及与普通线程池的区别，涵盖实战案例与源码分析。
mindmap:
---

# 线程池ForkJoinPool实战及其工作原理分析

## 一、ForkJoinPool 概述

### 1.1 什么是 Fork/Join 框架？

Fork/Join 是 Java 7 引入的并行执行框架，核心思想是**分治算法（Divide and Conquer）**：

- **Fork**（分解）：将大任务递归拆分为多个小任务
- **Join**（合并）：等待子任务完成并汇总结果

```
            大任务
          /   |   \
       子任务 子任务 子任务
       /  \     /  \
     小  小   小   小
   任务 任务 任务 任务
      \  /    \  /
      合并    合并
        \    /
        最终结果
```

### 1.2 适用场景

- CPU 密集型的大规模并行计算
- 递归可分解的问题（如数组排序、求和、文件搜索）
- 计算量足够大、任务划分粒度适中的场景

---

## 二、工作窃取算法（Work-Stealing）

### 2.1 核心原理

每个工作线程维护一个**双端队列（Deque）**：

- 自己产生的任务从**队头**取（LIFO）
- 空闲线程从其他线程的**队尾**"窃取"任务（FIFO）

```
线程A队列: [T1, T2, T3]   ← 线程A从队头取任务
              ↑
         线程B取走T1（从队尾偷）
```

### 2.2 工作窃取的优势

| 特性 | 说明 |
|------|------|
| 负载均衡 | 空闲线程主动从繁忙线程的队列窃取任务 |
| 减少竞争 | 自己的线程操作队头，窃取线程操作队尾，减少锁冲突 |
| 提高利用率 | 避免部分线程空闲而其他线程积压大量任务 |

### 2.3 与普通线程池的区别

| 对比维度 | ForkJoinPool | ThreadPoolExecutor |
|----------|--------------|--------------------|
| **任务队列** | 每个线程有双端队列 + 公共队列 | 单一共享阻塞队列 |
| **调度算法** | 工作窃取（Work-Stealing） | 任务队列先进先出 |
| **线程数** | 默认 CPU 核心数（并行度） | 手动设置 core/max |
| **任务类型** | 分治递归的大规模任务 | 一般的短小任务 |
| **适用场景** | CPU 密集型并行计算 | 通用任务处理 |

---

## 三、核心 API

### 3.1 ForkJoinTask 继承体系

```
ForkJoinTask<V> (抽象类)
    ├── RecursiveAction   (无返回值)
    └── RecursiveTask<V>  (有返回值)
```

### 3.2 RecursiveTask — 有返回值的任务

```java
public class SumTask extends RecursiveTask<Long> {
    private static final int THRESHOLD = 10000;
    private long[] array;
    private int start, end;
    
    public SumTask(long[] array, int start, int end) {
        this.array = array;
        this.start = start;
        this.end = end;
    }
    
    @Override
    protected Long compute() {
        int length = end - start;
        // 任务足够小，直接计算
        if (length <= THRESHOLD) {
            long sum = 0;
            for (int i = start; i < end; i++) {
                sum += array[i];
            }
            return sum;
        }
        // 任务太大，一分为二
        int mid = start + length / 2;
        SumTask leftTask = new SumTask(array, start, mid);
        SumTask rightTask = new SumTask(array, mid, end);
        
        leftTask.fork();                              // 异步执行左子任务
        Long rightResult = rightTask.compute();       // 同步执行右子任务
        Long leftResult = leftTask.join();            // 等待左子任务结果
        
        return leftResult + rightResult;
    }
}

// 使用
ForkJoinPool pool = new ForkJoinPool();
SumTask task = new SumTask(array, 0, array.length);
Long result = pool.invoke(task);
```

### 3.3 RecursiveAction — 无返回值的任务

```java
public class PrintTask extends RecursiveAction {
    private static final int THRESHOLD = 50;
    private int start, end;
    
    public PrintTask(int start, int end) {
        this.start = start;
        this.end = end;
    }
    
    @Override
    protected void compute() {
        if ((end - start) <= THRESHOLD) {
            for (int i = start; i < end; i++) {
                System.out.println(Thread.currentThread().getName() + ": " + i);
            }
        } else {
            int mid = start + (end - start) / 2;
            PrintTask left = new PrintTask(start, mid);
            PrintTask right = new PrintTask(mid, end);
            // 并行执行两个子任务
            invokeAll(left, right);
        }
    }
}
```

### 3.4 核心方法

| 方法 | 说明 |
|------|------|
| `fork()` | 异步执行，将任务放入当前线程的队列 |
| `join()` | 等待任务完成并返回结果，阻塞 |
| `invoke(task)` | 提交任务并等待结果（阻塞调用） |
| `invokeAll(t1, t2)` | 批量提交任务等待全部完成 |
| `execute(task)` | 异步提交任务 |
| `submit(task)` | 提交任务返回ForkJoinTask |

### 3.5 Fork/Join 最佳实践

```java
// fork + join 模式
leftTask.fork();
rightTask.fork();
return leftTask.join() + rightTask.join();

// 优化：让一个任务直接compute，减少线程切换
leftTask.fork();
Long rightResult = rightTask.compute();   // 当前线程直接计算
return leftTask.join() + rightResult;
```

---

## 四、ForkJoinPool 内部结构

### 4.1 架构组成

```
ForkJoinPool
    ├── WorkQueue[] 数组
    │   ├── 偶数索引：外部提交队列（共享）
    │   └── 奇数索引：工作线程队列（私有）
    ├── ForkJoinWorkerThread[] 工作线程数组
    └── 状态控制字段
```

### 4.2 关键参数

| 参数 | 说明 |
|------|------|
| `parallelism` | 并行度，默认 `Runtime.getRuntime().availableProcessors()` |
| `factory` | 线程工厂 |
| `handler` | 异常处理器 |
| `asyncMode` | 是否异步模式（影响队列操作顺序） |

### 4.3 创建方式

```java
// 方式1：使用静态公共池（推荐用于简单场景）
ForkJoinPool commonPool = ForkJoinPool.commonPool();

// 方式2：自定义并行度
ForkJoinPool pool = new ForkJoinPool();
ForkJoinPool pool = new ForkJoinPool(4);  // 4个工作线程

// 方式3：完整自定义
ForkJoinPool pool = new ForkJoinPool(
    4,                         // parallelism
    ForkJoinPool.defaultForkJoinWorkerThreadFactory,
    null,                      // 异常处理器
    false                      // asyncMode
);
```

### 4.4 任务提交方式

```java
ForkJoinPool pool = new ForkJoinPool();

// 方式1：invoke - 阻塞获取结果
Long result = pool.invoke(new SumTask(array, 0, array.length));

// 方式2：submit - 异步返回Future
ForkJoinTask<Long> future = pool.submit(new SumTask(array, 0, array.length));
Long result = future.get();

// 方式3：execute - 异步无返回
pool.execute(new PrintTask(0, 100));
```

---

## 五、工作窃取算法详解

### 5.1 任务入队规则

```
自己产生的子任务 → push (队头) -- LIFO
窃取其他线程的任务 → pop (队尾) -- FIFO
外部提交的任务 → push (队头)
```

### 5.2 为何不同端操作？

- **自己取自己的**：从队头取，利用了LIFO的缓存局部性
- **窃取别人的**：从队尾取，减少与持有者的竞争

### 5.3 窃取流程

```
1. 线程完成自己所有任务
2. 随机选择一个其他线程的工作队列
3. 检查该队列是否为空
4. 如果不为空，从队尾取一个任务执行
5. 如果为空，换一个线程重试
6. 如果一直找不到任务，线程可能阻塞等待
```

---

## 六、实战案例

### 6.1 大数组求和的完整实现

```java
public class ForkJoinSumDemo {
    
    static class SumTask extends RecursiveTask<Long> {
        private static final int THRESHOLD = 1000;
        private final int[] arr;
        private final int start, end;
        
        SumTask(int[] arr, int start, int end) {
            this.arr = arr;
            this.start = start;
            this.end = end;
        }
        
        @Override
        protected Long compute() {
            if (end - start <= THRESHOLD) {
                long sum = 0;
                for (int i = start; i < end; i++) sum += arr[i];
                return sum;
            }
            int mid = (start + end) >>> 1;
            SumTask left = new SumTask(arr, start, mid);
            SumTask right = new SumTask(arr, mid, end);
            left.fork();
            return right.compute() + left.join();
        }
    }
    
    public static void main(String[] args) {
        int[] arr = new int[10_000_000];
        Arrays.parallelSetAll(arr, i -> 1);
        
        ForkJoinPool pool = new ForkJoinPool();
        long startTime = System.currentTimeMillis();
        long result = pool.invoke(new SumTask(arr, 0, arr.length));
        long endTime = System.currentTimeMillis();
        
        System.out.println("Sum: " + result);
        System.out.println("Time: " + (endTime - startTime) + "ms");
    }
}
```

### 6.2 快速排序

```java
class QuickSortTask extends RecursiveAction {
    private final int[] arr;
    private final int low, high;
    private static final int THRESHOLD = 1000;
    
    QuickSortTask(int[] arr, int low, int high) {
        this.arr = arr;
        this.low = low;
        this.high = high;
    }
    
    @Override
    protected void compute() {
        if (high - low <= THRESHOLD) {
            Arrays.sort(arr, low, high + 1);
            return;
        }
        int pivot = partition(arr, low, high);
        invokeAll(
            new QuickSortTask(arr, low, pivot - 1),
            new QuickSortTask(arr, pivot + 1, high)
        );
    }
    
    private int partition(int[] arr, int low, int high) {
        int pivot = arr[high];
        int i = low - 1;
        for (int j = low; j < high; j++) {
            if (arr[j] < pivot) {
                i++;
                int temp = arr[i]; arr[i] = arr[j]; arr[j] = temp;
            }
        }
        int temp = arr[i + 1]; arr[i + 1] = arr[high]; arr[high] = temp;
        return i + 1;
    }
}
```

### 6.3 大规模文件搜索

```java
class FileSearchTask extends RecursiveTask<List<String>> {
    private final File directory;
    private final String keyword;
    private static final int MAX_FILES_PER_TASK = 100;
    
    FileSearchTask(File directory, String keyword) {
        this.directory = directory;
        this.keyword = keyword;
    }
    
    @Override
    protected List<String> compute() {
        List<String> results = new ArrayList<>();
        File[] files = directory.listFiles();
        if (files == null) return results;
        
        if (files.length <= MAX_FILES_PER_TASK) {
            for (File file : files) {
                if (file.getName().contains(keyword))
                    results.add(file.getAbsolutePath());
            }
            return results;
        }
        
        List<FileSearchTask> subTasks = new ArrayList<>();
        for (File file : files) {
            if (file.isDirectory()) {
                subTasks.add(new FileSearchTask(file, keyword));
            } else if (file.getName().contains(keyword)) {
                results.add(file.getAbsolutePath());
            }
        }
        
        invokeAll(subTasks);
        for (FileSearchTask task : subTasks)
            results.addAll(task.join());
        
        return results;
    }
}
```

---

## 七、ForkJoinPool vs ThreadPoolExecutor 对比总结

| 特性 | ForkJoinPool | ThreadPoolExecutor |
|------|--------------|--------------------|
| **任务模型** | 分治递归（大拆小） | 独立任务 |
| **队列模型** | 每线程双端队列 | 单一共享阻塞队列 |
| **调度** | 工作窃取 | FIFO 队列 |
| **线程数** | 自动（CPU核心数） | 手动配置 |
| **适用** | CPU密集型、可拆分任务 | 通用任务、IO密集型 |
| **子任务** | 原生支持 fork/join | 不支持 |
| **负载均衡** | 自动（窃取） | 无 |

---

## 八、总结

- ForkJoinPool 专为**分治并行计算**设计，通过递归拆分任务+合并结果
- **工作窃取算法**确保线程负载均衡，减少空闲等待
- 适用于大规模可拆分的**CPU密集型**任务
- 使用 `RecursiveTask`（有返回值）/ `RecursiveAction`（无返回值）
- `fork()` 异步 + `join()` 等待，注意避免阻塞当前线程
- 建议 `compute()` 当前任务时一个fork一个compute，减少线程切换
