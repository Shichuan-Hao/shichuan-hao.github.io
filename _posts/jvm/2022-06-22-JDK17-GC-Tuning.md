---
title: "JDK17 GC 调优策略：从 RocketMQ 实战中学到的调优秘籍"
date: 2022-06-22 16:35:00 +0800
categories: [Java, JVM]
tags: [JDK17, GC调优, RocketMQ, G1, ZGC, JVM参数]
---

## 前言

GC 的性能极大程度决定了整个 Java 程序的执行效率。对整个 JVM 调优或许难度太大，但**对 GC 进行调优**，是每个 Java 程序员都应该掌握的技能。

本文以 **RocketMQ** 的启动脚本为切入点，带你学习真实项目中 GC 调优的正确姿势。

---

## 一、JVM 有哪些参数可以调？

JVM 提供了三类参数：

| 类型 | 前缀 | 示例 | 说明 |
|------|------|------|------|
| **标准参数** | `-` | `java -version` | 所有 HotSpot 都支持 |
| **非标准参数** | `-X` | `-Xms200M -Xmx200M` | 特定版本支持，比较稳定 |
| **不稳定参数** | `-XX` | `-XX:+UseG1GC` | 随版本变化，换版本可能失效 |

### 常用标准参数

```bash
--list-modules              # 查看当前进程中的模块
--show-module-resolution    # 查看模块依赖关系
-verbose:class              # 显示类加载信息
-verbose:gc                 # 显示 GC 事件
```

### 常用非标准参数

```bash
-Xint    # 只采用解释执行
-Xcomp   # 只采用编译执行
-Xmixed  # 混合模式（默认）
-Xbatch  # 禁用后台编译
```

### 查看不稳定参数

```bash
java -XX:+PrintFlagsFinal     # 所有最终生效的不稳定参数
java -XX:+PrintFlagsInitial   # 默认的不稳定参数
java -XX:+PrintCommandLineFlags # 当前命令的不稳定参数
```

**如何设置不稳定参数？**
- 数字型：直接指定值，如 `-XX:ActiveProcessorCount=1`
- Boolean 型：`+` 表示 true，`-` 表示 false，如 `-XX:+PrintFlagsFinal`

> **小问题：JDK17 默认用的是哪种垃圾回收器？** → G1。

---

## 二、从 RocketMQ 学习常用 GC 调优三部曲

### 2.1 为何跟开源项目学？

> 你没有线上服务器调优经验 → 更不会让你碰服务器 → 死循环。

**解决之道**：跟优秀的开源软件学！因为这是所有人都能接触到、质量最靠谱的 Java 程序了。

以 RocketMQ 的 **NameServer** 启动脚本为例，它定制了大量的 JVM 参数。

![RocketMQ 启动脚本]({{ site.url }}/assets/img/jvm/jdk17-gc/page2_img1.png)

### 2.2 根据 JDK 版本选择不同 GC 策略

RocketMQ 根据 JDK 版本动态选择 GC 参数：

**JDK 9 以前 → CMS：**

```bash
JAVA_OPT="${JAVA_OPT} -server -Xms4g -Xmx4g -Xmn2g \
    -XX:MetaspaceSize=128m -XX:MaxMetaspaceSize=320m"
JAVA_OPT="${JAVA_OPT} -XX:+UseConcMarkSweepGC \
    -XX:+UseCMSCompactAtFullCollection \
    -XX:CMSInitiatingOccupancyFraction=70 \
    -XX:+CMSParallelRemarkEnabled \
    -XX:SoftRefLRUPolicyMSPerMB=0 \
    -XX:+CMSClassUnloadingEnabled \
    -XX:SurvivorRatio=8 -XX:-UseParNewGC"
JAVA_OPT="${JAVA_OPT} -verbose:gc \
    -Xloggc:${GC_LOG_DIR}/rmq_srv_gc_%p_%t.log \
    -XX:+PrintGCDetails -XX:+PrintGCDateStamps"
```

**JDK 9 以后 → G1：**

```bash
JAVA_OPT="${JAVA_OPT} -server -Xms4g -Xmx4g \
    -XX:MetaspaceSize=128m -XX:MaxMetaspaceSize=320m"
JAVA_OPT="${JAVA_OPT} -XX:+UseG1GC \
    -XX:G1HeapRegionSize=16m \
    -XX:G1ReservePercent=25 \
    -XX:InitiatingHeapOccupancyPercent=30 \
    -XX:SoftRefLRUPolicyMSPerMB=0"
JAVA_OPT="${JAVA_OPT} -Xlog:gc*:file=${GC_LOG_DIR}/rmq_srv_gc_%p_%t.log:\
    time,tags:filecount=5,filesize=30M"
```

### 2.3 GC 调优三部曲

不管在哪个 JDK 版本，RocketMQ 的参数都可以概括为三个步骤：

| 步骤 | 内容 | 对应参数 |
|------|------|---------|
| **第一步** | 调整内存布局 | `-Xms/-Xmx`、`-XX:MetaspaceSize` 等 |
| **第二步** | 选择 GC 算法 + 定制参数 | `-XX:+UseG1GC`、`G1HeapRegionSize` 等 |
| **第三步** | 打印 GC 日志 | `-Xlog:gc*` 配置 |

![GC 调优三部曲]({{ site.url }}/assets/img/jvm/jdk17-gc/page4_img1.png)

> 即使 NameServer 和 Broker 业务场景不同，RocketMQ 都按这个思路调优。**我们要学的是思路，不是复制粘贴。**

---

## 三、基于 JDK17 优化 JVM 内存布局

所有方法及 GC 活动都发生在 JVM 内存中，**第一步必须先定制内存整体布局**。

### 3.1 定制堆内存大小

| 参数 | 说明 |
|------|------|
| `-Xms` | 堆内存初始大小。必须是 1024 的整数倍且大于 1M。示例：`-Xms6m`、`-Xms8G` |
| `-Xmx` | 堆内存最大大小。等同于 `-XX:MaxHeapSize` |
| `-XX:InitialHeapSize` | 不稳定参数，出现在 `-Xms` 之后时优先于 `-Xms` |

> **最佳实践**：生产环境将 `-Xms` 和 `-Xmx` 设置为相同值，避免运行时动态扩容。

如果内存紧张，需要按需申请，关注以下参数：
- `-XX:MinHeapFreeRatio`：GC 后堆空间最小比例，低于此值触发扩容
- `-XX:MinHeapSize`：GC 后堆空间最小大小

### 3.2 定制非堆内存大小

#### 设置元空间 Metaspace

| 参数 | 说明 |
|------|------|
| `-XX:MetaspaceSize` | 元空间超过此阈值时触发 GC，后续会自动调整 |
| `-XX:MaxMetaspaceSize` | 元空间最大值，默认无限制 |

> JDK8 后，**永久代（PermGen）被移除**，元空间直接使用本地内存，不再受 JVM 堆内存限制。但如果本地内存耗尽，同样会 OOM。

#### 设置线程栈空间

| 参数 | 说明 |
|------|------|
| `-Xss` | 线程栈大小。Linux/MacOS 默认 1024KB。如 `-Xss1m` |
| `-XX:ThreadStackSize` | 等效参数。如 `-XX:ThreadStackSize=1K` |

> 如果方法嵌套非常多，或有长期执行的复杂方法，需调大栈空间。不足时抛出 `StackOverflowError`。

#### 设置热点代码缓存空间

| 参数 | 说明 |
|------|------|
| `-XX:InitialCodeCacheSize` | 代码缓存初始大小 |
| `-XX:ReservedCodeCacheSize` | 代码缓存最大值，默认 240MB |
| `-XX:+SegmentedCodeCache` | JDK17 默认开启，将代码缓存分割为三部分优化内存使用 |

![代码缓存分割]({{ site.url }}/assets/img/jvm/jdk17-gc/page7_img1.png)

代码缓存分割的三个子参数：
- `-XX:ProfiledCodeHeapSize`
- `-XX:NonNMethodCodeHeapSize`
- `-XX:NonProfiledCodeHeapSize`

> 需要 `-XX:+TieredCompilation` 且 `-XX:ReservedCodeCacheSize >= 240MB` 才能生效。

#### 应用程序类数据共享（AppCDS）

一种旨在**提高多 JVM 启动时间、减少内存占用**的优化机制：

```bash
# 将类信息归档
java -Xshare:dump -XX:SharedArchiveFile=hello.jsa -version

# 使用归档文件启动
java -XX:SharedArchiveFile=hello.jsa -Xlog:class+load -version
```

> 部署微服务时，多个 JVM 实例可共享同一份类数据归档，减少初始化开销。

---

## 四、基于 JDK17 定制 GC 参数

> **核心提醒**：GC 调优没有标准答案，不要希望一套配置打天下。多上阵、多试错才是唯一正确的方法。

### 关于 `-Xmn` 参数

- 设置**年轻代**最大大小
- 对于分代收集器（Parallel），建议保持年轻代为堆的 **25% ~ 50%**
- **对于 G1 收集器，官方明确建议：不要设置 `-Xmn`！**

### 4.1 G1 重要参数

G1 是一种**分代的、并发的、基于区域**的垃圾回收器。它将堆划分为多个独立的 Region，每个 Region 可以是 Eden / Survivor / Old。

**G1 最核心的三个参数：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-XX:+UseG1GC` | 启用 G1（JDK17 默认） | ✓ |
| `-Xmx` | 最大堆大小 | - |
| `-XX:MaxGCPauseMillis` | 期望最大停顿时间 | **200ms** |

> 在 G1 下，请忘记 `-Xmn`、`-XX:NewRatio`、`-XX:SurvivorRatio` 这些参数。

![G1 参数详解]({{ site.url }}/assets/img/jvm/jdk17-gc/page8_img1.png)

**RocketMQ 中的 G1 参数解读：**

| 参数 | RocketMQ 值 | 默认值 | 解读 |
|------|-----------|--------|------|
| `-XX:G1HeapRegionSize` | **16m** | 堆/2048 | 偏大，减少 GC 频率，减少次数但每次时间长 |
| `-XX:G1ReservePercent` | **25%** | 10% | 空间换时间，保留更多空闲缓冲避免长时间停顿 |
| `-XX:InitiatingHeapOccupancyPercent` | **30%** | 45% | 更激进地启动并发标记，启动时更稳健 |
| `-XX:SoftRefLRUPolicyMSPerMB` | **0** | 1000（1秒） | 立即清理软引用，配合 G1 内存管理 |

**JDK17 新增的 G1 参数：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-XX:ParallelGCThreads` | GC 工作线程数 | 取决于 CPU 核数 |
| `-XX:G1HeapWastePercent` | 堆空间浪费比例，低于此不启动 GC | 5% |
| `-XX:G1OldCSetRegionThresholdPercent` | 一次混合 GC 清理 Old 区比例 | 10% |
| `-XX:G1MixedGCCountTarget` | 混合 GC 的线程数上限 | 8 |

### 4.2 ZGC 重要参数

ZGC 从 JDK11 引入，JDK17 中已基本稳定，官方建议可用于生产环境。

**ZGC 的特点**：
- 最大停顿时间**几毫秒**级别
- 停顿时间**不随堆大小增长**
- 支持 8MB ~ 16TB 的堆

**ZGC 核心参数：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-XX:+UseZGC` | 启用 ZGC | - |
| `-XX:ZAllocationSpikeTolerance` | 分配尖峰容忍度因子 | 2.0 |
| `-XX:ZCollectionInterval` | 两次 GC 最大间隔（秒） | 0（禁用） |
| `-XX:ZFragmentationLimit` | 最大可接受碎片率（%） | 25 |
| `-XX:+ZProactive` | 主动 GC 周期 | ✓ 启用 |
| `-XX:+ZUncommit` | 回收未使用的堆内存 | ✓ 启用 |
| `-XX:ZUncommitDelay` | 堆内存空闲多久后才回收（秒） | 300（5分钟） |

> **ZGC 的设计哲学**：暴露的参数极少，大部分算法细节已实现**自适应调整**。基本只需要指定 `-Xmx`。

---

## 五、GC 日志处理

### JDK8 vs JDK17 日志参数对比

| 功能 | JDK8 | JDK17 |
|------|------|-------|
| 打印 GC 详情 | `-XX:+PrintGCDetails` | `-Xlog:gc*` |
| 打印 GC 时间 | `-XX:+PrintGCDateStamps` | `-Xlog` 中 `time` 参数 |
| 指定日志文件 | `-Xloggc:路径` | `-Xlog` 中 `file=路径` |
| 日志轮转 | `-XX:+UseGCLogFileRotation` 等 | `filecount=5,filesize=30M` |

### JDK17 统一日志格式

```bash
-Xlog:gc*:file=路径/log_%p_%t.log:time,tags:filecount=5,filesize=30M
```

- `gc*`：打印每次 GC 详细信息
- `file=`：日志文件路径，`%p` = PID，`%t` = 时间戳
- `time,tags`：日志后缀选项
- `filecount=5,filesize=30M`：保留 5 个文件，每个 30M 轮转

![GC Easy 分析]({{ site.url }}/assets/img/jvm/jdk17-gc/page12_img1.png)

> 将日志上传到 **gceasy.io** 在线分析，可快速得到 GC 健康状况报告。

![gceasy 分析结果]({{ site.url }}/assets/img/jvm/jdk17-gc/page13_img1.png)

---

## 六、其他 JVM 调优小经验

### 6.1 远程断点调试

RocketMQ 脚本中保留了一段注释掉的配置：

```bash
#JAVA_OPT="${JAVA_OPT} -Xdebug \
#  -Xrunjdwp:transport=dt_socket,address=9555,server=y,suspend=n"
```

这是**远程断点调试**配置，允许用本地 IDEA 调试远端服务器上运行的程序。

**示例：**

```java
// RemoteDebugTest.java - 模拟长时间运行程序
public class RemoteDebugTest {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        String command = "";
        int count = 0;
        do {
            command = scanner.next();
            System.out.println("第" + (++count) + "个指令：" + command);
        } while (!"quit".equals(command));
    }
}
```

**服务端启动（带调试参数）：**

```bash
# suspend=y 表示启动后阻塞等待调试器连接
java -Xdebug -Xrunjdwp:transport=dt_socket,server=y,suspend=y,address=5005 \
     com.roy.RemoteDebugTest

# 输出：Listening for transport dt_socket at address: 5005
```

![远程调试配置]({{ site.url }}/assets/img/jvm/jdk17-gc/page15_img1.png)

![IDEA 远程调试]({{ site.url }}/assets/img/jvm/jdk17-gc/page16_img1.png)

> **注意**：远程调试不能用于生产环境！断开调试连接后，服务端会重新阻塞。

---

## 七、章节总结

### 从 RocketMQ 学到的 GC 调优公式

```text
GC 调优 = 定内存布局 → 选 GC 算法 → 打 GC 日志
       = (-Xms/-Xmx) + (-XX:+UseG1GC) + (-Xlog:gc*)
```

### JVM 学习的三条建议

| 建议 | 说明 |
|------|------|
| **1. 重框架** | 注重各层面的逻辑自洽，不要纠结细节 |
| **2. 形成习惯** | 每接触新环境都梳理优化思路，补充知识盲区 |
| **3. 重表达** | 搞懂原理后多练习表达，能在短时间内向别人讲清楚 |

> JVM 底层的知识就像武林高手的内功——见面三招可能用不上，但越往后，越能体现它的价值。

---

**参考链接：**

- [JDK17 工具官方文档](https://docs.oracle.com/en/java/javase/17/docs/specs/man/index.html)
- [JDK17 java 命令文档](https://docs.oracle.com/en/java/javase/17/docs/specs/man/java.html)
- [JDK8 java 命令文档](https://docs.oracle.com/javase/8/docs/technotes/tools/unix/java.html)
- [有道云笔记原文](https://note.youdao.com/s/SxNl4ZdO)
