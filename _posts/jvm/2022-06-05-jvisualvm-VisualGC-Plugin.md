---
title: JVM 调优利器：jvisualvm 安装 Visual GC 插件及界面详解
date: 2022-06-05 16:33:00 +0800
categories: [Java, JVM]
tags: [jvisualvm, VisualGC, JVM调优, GC监控]
---

## 前言

jvisualvm 是 JDK 自带的一款强大的 JVM 监控和性能分析工具。其中 **Visual GC** 插件能够以图形化方式实时展示 JVM 堆内存各区域的使用情况、GC 活动、类加载、编译时间等关键指标，是调优必备神器。

但当你尝试安装时，可能会遇到 `We're sorry the java.net site has closed` 的错误——因为 Oracle 已经关闭了旧的 java.net 插件中心。本文将手把手教你如何正确安装以及详解 Visual GC 界面的每个指标。

---

## 一、安装 Visual GC 插件

### 1.1 问题背景

旧版 jvisualvm 的插件更新地址指向 `java.net`，该网站已关闭，导致无法在线安装插件。

### 1.2 找到新的更新地址

VisualVM 的新官网已迁移到 GitHub Pages：

> **https://visualvm.github.io/index.html**

进入 **Plugins** 页面，找到对应自己 JDK 版本的更新地址（`updates.xml` 文件 URL）。

![VisualVM 新官网]({{ site.url }}/assets/img/jvm/visualgc/page1_img1.png)

以 **JDK 8** 为例，插件中心的地址为：

```
https://visualvm.github.io/archive/uc/8u40/updates.xml
```

不同 JDK 版本对应不同路径，请根据实际情况选择。

![选择对应 JDK 版本的更新地址]({{ site.url }}/assets/img/jvm/visualgc/page1_img2.png)

### 1.3 修改插件中心地址

打开 jvisualvm，进入 **工具 → 插件**（Tools → Plugins）：

![工具-插件菜单]({{ site.url }}/assets/img/jvm/visualgc/page2_img1.png)

在 **设置（Settings）** 选项卡中，将原有已失效的 URL 修改为刚才从 GitHub 找到的对应你 JDK 版本的地址：

![修改插件更新地址]({{ site.url }}/assets/img/jvm/visualgc/page2_img2.png)

修改成功后，**可用插件** 列表即可刷新出来。找到 **Visual GC**，勾选并安装。

### 1.4 安装完成

安装完成后重启 jvisualvm，即可在监控界面看到新增的 **Visual GC** 选项卡。

---

## 二、Visual GC 界面详解

打开任意 Java 应用的 Visual GC 面板，整个区域分为三大部分：**Spaces**、**Graphs**、**Histogram**。

![Visual GC 界面全貌]({{ site.url }}/assets/img/jvm/visualgc/page3_img1.png)

---

### 2.1 Spaces 区域 —— 虚拟机内存分布

直观展示堆内存的区域划分和当前使用比例：

| 区域 | 全称 | 说明 |
|------|------|------|
| **Perm** | Permanent Generation | 永久代（JDK 7 及以前的方法区实现，JDK 8 改为 Metaspace） |
| **Old** | Old Generation | 老年代 |
| **Eden** | Eden Space | 新生代 Eden 区 |
| **S0** | Survivor 0 | 新生代 Survivor 区 0（From 区） |
| **S1** | Survivor 1 | 新生代 Survivor 区 1（To 区） |

> **注意**：关于 Perm 的说法——严格来说 HotSpot 虚拟机设计者只是把 GC 分代收集扩展到了方法区，正确的叫法应该是**方法区**或**非堆（Non-Heap）**内存。

#### Perm 永久代参数

```bash
-XX:PermSize=128m      # 永久代初始大小
-XX:MaxPermSize=256m   # 永久代最大值
```

#### Heap 堆参数

新生代（Young）包括 Eden + S0 + S1，默认比例为 `8 : 1 : 1`：

```bash
-Xms512m                       # 初始堆内存
-Xmx512m                       # 最大堆内存（建议与 -Xms 保持一致）
-Xmn100m                       # 新生代大小
-XX:SurvivorRatio=8            # Eden:S0:S1 = 8:1:1
-XX:+HeapDumpOnOutOfMemoryError  # OOM 时自动 dump
```

老年代大小 = 堆总大小 - 新生代大小 = 512M - 100M = **412M**。

> **最佳实践**：`-Xms` 与 `-Xmx` 最好设置为相等，防止运行时堆内存动态扩容或 Full GC 带来的性能抖动。

---

### 2.2 Graphs 区域 —— 实时监控曲线

Graphs 区域通过实时曲线图展示各项指标的历史变化趋势。

#### 2.2.1 Compile Time（编译时间）

| 指标 | 说明 |
|------|------|
| `6368 compiles` | JIT 编译总次数 |
| `4.407s` | 编译累计耗时 |

图中每个脉冲代表一次 **JIT 编译**：
- **窄脉冲**：编译持续时间短
- **宽脉冲**：编译持续时间长（通常是热点方法被深度优化）

#### 2.2.2 Class Loader Time（类加载时间）

| 指标 | 说明 |
|------|------|
| `20869 loaded` | 已加载的类数量 |
| `139 unloaded` | 已卸载的类数量 |
| `40.630s` | 类加载累计耗时 |

#### 2.2.3 GC Time（垃圾收集时间）

| 指标 | 说明 |
|------|------|
| `2392 collections` | GC 总次数 |
| `37.454s` | GC 累计耗时 |
| `last cause` | 最近一次 GC 的触发原因 |

> 这是最需要关注的指标之一——如果 GC Time 占程序运行时间的比例过高（超过 5%），说明 GC 可能成为性能瓶颈。

#### 2.2.4 Eden Space（Eden 区）

| 指标 | 示例值 | 说明 |
|------|--------|------|
| 最大容量 | `31.500M` | Eden 区上限 |
| 当前容量 | `9.750M` | 当前分配的大小 |
| 当前使用 | `4.362M` | 实际占用 |
| 收集次数 | `2313` | Eden 区 GC 次数 |
| 收集耗时 | `8.458s` | Eden 区 GC 累计时间 |

#### 2.2.5 Survivor 0 / Survivor 1（S0 和 S1 区）

| 指标 | 说明 |
|------|------|
| 最大容量 | S0/S1 区上限（如 `3.938M`） |
| 当前容量 | 当前分配大小 |
| 当前使用 | 实际占用 |

> S0 和 S1 同一时间只有一个在工作，另一个为空，用于 Minor GC 时对象的复制。

#### 2.2.6 Old Gen（老年代）

| 指标 | 示例值 | 说明 |
|------|--------|------|
| 最大容量 | `472.625M` | 老年代上限 |
| 当前容量 | `145.031M` | 当前分配大小 |
| 当前使用 | `87.031M` | 实际占用 |
| 收集次数 | `79` | Major/Full GC 次数 |
| 收集耗时 | `28.996s` | 老年代 GC 累计时间 |

#### 2.2.7 Perm Gen（永久代）

| 指标 | 示例值 | 说明 |
|------|--------|------|
| 最大容量 | `256.000M` | 永久代上限 |
| 当前容量 | `105.250M` | 当前分配大小 |
| 当前使用 | `105.032M` | 实际占用 |

> 如果 Perm Gen 的使用量持续接近最大值，可能原因：动态生成大量类（如 CGLIB 代理）、常量池溢出等。

---

### 2.3 Histogram 区域 —— 年龄柱状图与晋升机制

Histogram 展示了 Survivor 区域中各年龄段对象的分布柱状图。

#### 核心参数说明

| 参数 | 说明 |
|------|------|
| **Tenuring Threshold** | 动态计算出的**当前晋升阈值**，对象年龄超过此值则进入老年代 |
| **Max Tenuring Threshold** | **最大年龄上限**（默认 15），可通过 `-XX:MaxTenuringThreshold` 设置 |
| **Desired Survivor Size** | Survivor 空间大小的**验证阈值**（默认为 Survivor 空间的一半） |
| **Current Survivor Size** | 当前 Survivor 空间大小 |
| **histogram 柱状图** | 每个年龄段对象的存储量柱状图 |

#### Tenuring Threshold 与 Max Tenuring Threshold 的区别

这是理解对象晋升机制的关键：

| | Tenuring Threshold | Max Tenuring Threshold |
|------|------|------|
| **性质** | 动态计算，随 GC 变化 | 固定上限值 |
| **作用** | 实际用于判断对象是否进入老年代 | 限制对象年龄最大值 |
| **默认关系** | 通常与 Max Tenuring Threshold 相等 | 默认值为 15 |

**动态调整机制**：

如果在 Survivor 空间中，**相同年龄所有对象的大小总和 > Survivor 空间的一半（Desired Survivor Size）**，则年龄大于或等于该年龄的对象都可以**提前晋升**到老年代。

> 举例：假设 Survivor 空间为 10M，年龄为 5 的对象总大小为 6M（超过 5M 的一半），则 Tenuring Threshold 被调整为 5，所有 `age >= 5` 的对象都将晋升到老年代。

**公式梳理**：
- `Sum(age==N) > Desired Survivor Size` → Tenuring Threshold = N
- `age >= Tenuring Threshold` → 对象晋升老年代

#### 注意事项

如果显式指定了 **`-XX:+UseParallelGC`**（新生代并行、老年代串行收集器），则 **Histogram 柱状图不支持**该收集器的数据显示。

---

## 三、总结

Visual GC 是三部分信息的有机结合：

| 区域 | 作用 | 关注重点 |
|------|------|---------|
| **Spaces** | 堆内存分布快照 | Eden/Old/Perm 的使用比例是否健康 |
| **Graphs** | 历史趋势曲线 | GC 频率和耗时是否异常 |
| **Histogram** | 对象年龄段分布 | Survivor 空间压力是否过大，晋升是否正常 |

通过 Visual GC 插件，你可以直观地观察 JVM 运行时的内存动态，是日常调优和排查内存问题的第一手信息来源。

---

## 参考链接

- [VisualVM 官网](https://visualvm.github.io/index.html)
- [Visual GC 官方文档](http://www.oracle.com/technetwork/java/visualgc-136680.html)
- [JVM Options 参考](http://www.oracle.com/technetwork/java/javase/tech/vmoptions-jsp-140102.html)
