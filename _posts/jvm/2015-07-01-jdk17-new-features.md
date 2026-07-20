---
title: JDK17 新特性全面梳理：从 JDK8 迈向新时代
date: 2015-07-01 20:35:00 +0800
categories: [Java 后端]
tags: [JDK17, Java17, LTS, 模块化, GraalVM, Record, Sealed Classes]
---

## 前言

"So you release you, I use Java 8." 虽然业界对 JDK8 后每半年更新一次的新版本保持着谨慎，但 **JDK17** 是每个 Java 程序员不得不去关注的新版本。最直观的理由是：Spring Boot 3.x 已经**抛弃 JDK8，最低要求 JDK17**。

跳过 JDK11，直接从 JDK8 升到 JDK17，对老程序员来说是一个更加实惠的选择。JDK17 不仅是 JDK8 后最重要的 **LTS 长期支持版本**，更在应用生态上比 JDK11 更成熟。

![JDK17新特性概览]({{ site.url }}/assets/img/jvm/jdk17-features/page1_img1.png)

---

## 一、为什么是 JDK17

| 对比维度 | JDK8 | JDK11 | JDK17 |
|---------|------|-------|-------|
| LTS 长期支持 | ✓ | ✓ | ✓ |
| Spring Boot 3.x 支持 | ✗ | ✓ | ✓ |
| 模块化 | ✗ | 引入 | 成熟 |
| ZGC 生产可用 | ✗ | 实验性 | **正式版** |
| GraalVM 支持 | ✗ | 实验性 | 成熟 |
| 语法增强 | 基础 | Switch 增强 | Record/Sealed/Hidden 类 |

个人认为：**跳过 JDK11，直接入手 JDK17**，对 JDK8 时代的程序员来说是最佳路径。

---

## 二、语法层面新特性

先从一些无关痛痒的语法增强开始。

### 2.1 文本块（Text Blocks）

文本块使用**连续三个双引号**包围多行文字，避免了换行转义的需求，并支持 `String.format`：

```java
String query =
    """
    SELECT `EMP_ID`, `LAST_NAME` FROM `EMPLOYEE_TB` \s
    WHERE `CITY` = '%s' \
    ORDER BY `EMP_ID`, `LAST_NAME`;
    """;
System.out.println(String.format(query, "合肥"));
```

新增两个转义字符：
- **`\`**（行尾）：将两行连接为一行
- **`\s`**：单个空白字符

### 2.2 Switch 表达式增强

从 JDK8 到 JDK17，Switch 已不再是简单的 if-else 替代品。添加了 `yield` 关键字，支持返回值。

**示例 1：多匹配合并（箭头语法）**

```java
switch (name) {
    case "李白", "杜甫", "白居易" -> System.out.println("唐代诗人");
    case "苏轼", "辛弃疾" -> System.out.println("宋代诗人");
    default -> System.out.println("其他朝代诗人");
}
```

**示例 2：每个分支返回值**

```java
int tmp = switch (name) {
    case "李白", "杜甫", "白居易" -> 1;
    case "苏轼", "辛弃疾" -> 2;
    default -> {
        System.out.println("其他朝代诗人");
        yield 3;
    }
};
```

### 2.3 instanceof 模式匹配

变量类型经过 `instanceof` 判断后，分支内无需再做类型强转：

```java
if (o instanceof Integer i && i > 0) {
    System.out.println(i.intValue());
} else if (o instanceof String s && s.startsWith("t")) {
    System.out.println(s.charAt(0));
}
```

### 2.4 var 局部变量推导

```java
var nums = new int[] {1, 2, 3, 4, 5};
var sum = Arrays.stream(nums).sum();
```

> 个人评价：仁者见仁。Java 的强类型语法更能保护代码安全，适当使用即可。

---

## 三、模块化及类封装

从 JDK8 开始，JDK 陆续借鉴了很多动态语言的特征，让 Java 变得更年轻、更有活力。

### 3.1 记录类 record

`record` 是一种**不可变的数据载体类**（JDK14 引入，JDK16 转正），可以用来替代繁琐的 POJO / BO / VO / DTO：

```java
public record Point(int x, int y) {}
```

特征：
- 属性自动添加 `private final`，初始化后**不可修改**（反射也不行）
- 获取属性的方法**与属性同名**（如 `p.x()` 而非 `getX()`）
- 自动生成 `toString`、`hashCode`、`equals`（且都是 `final`）

```java
Point p = new Point(10, 20);
System.out.println(p.x() + "====" + p.y());  // 10====20
// 不允许通过反射修改值
```

### 3.2 隐藏类 Hidden Classes

JDK15 引入，允许**绕过类加载器**，直接从 `class` 字节码创建类对象：

```java
byte[] classInBytes = Base64.getDecoder().decode(CLASS_INFO);
Class<?> proxy = MethodHandles.lookup()
        .defineHiddenClass(classInBytes, true, ClassOption.NESTMATE)
        .lookupClass();
```

![Hidden Class 示例]({{ site.url }}/assets/img/jvm/jdk17-features/page5_img1.png)

**应用价值**：极大提升 Java 的动态语言能力。框架（如 Spring）可以基于此机制高效生成动态类，替代繁琐低效的 ASM 字节码操作。

### 3.3 密封类 Sealed Classes

JDK15 引入，JDK17 转正。用来**限制父类可以被哪些子类继承或实现**：

```java
public sealed abstract class Shape permits Circle, Rectangle, Square {
    public abstract int lines();
}
```

子类有三种声明方式：

```java
// final: 不能再被继承
public final class Circle extends Shape { ... }

// non-sealed: 可以随意继承
public non-sealed class Square extends Shape { ... }

// sealed: 继续密封，声明自己的子类
public sealed class Rectangle extends Shape permits FilledRectangle { ... }
public final class FilledRectangle extends Rectangle { ... }
```

![Sealed Classes 层级示意]({{ site.url }}/assets/img/jvm/jdk17-features/page8_img1.png)

> 限制：父类和指定子类必须在**同一个显式命名的 Module** 下，且子类必须**直接继承**父类。

### 3.4 模块化 Module System

这是从 JDK9 引入的重磅特性，对 JDK8 开发者是一个**颠覆性的大变革**。

#### 什么是模块化？

Module 是 Package 的**上一级抽象**，包括一组紧密相关的包和资源，以及一个 `module-info.java` 描述符文件。

在 JDK17 安装目录下，原来那些 Jar 包变成了以 **`.jmod`** 后缀的文件：

![JDK 模块化目录]({{ site.url }}/assets/img/jvm/jdk17-features/page9_img1.png)

JMOD 设计用于**编译时和链接时**，不在运行时使用。你可以通过 `jlink` 命令定制自己的 JRE：

```bash
jlink -p $JAVA_HOME/jmods --add-modules java.base --output basejre
```

![自定义 basejre]({{ site.url }}/assets/img/jvm/jdk17-features/page10_img1.png)

#### 声明一个 Module

在模块根目录创建 `module-info.java`：

```java
module roy.demomodule {
}
```

#### require 声明模块依赖

```java
module roy.demomodule {
    requires junit;       // 第三方依赖
    requires java.sql;    // JDK 内置模块
}
```

如果只需要编译时依赖，可以加 `static`：
```java
requires static moduleB;  // 类似 Maven 的 compile scope
```

#### exports 和 opens 声明对外 API

```java
module roy.demomodule {
    exports com.roy.language;   // 对外暴露包（编译+运行时可用，不可反射）
    opens com.roy.internal;     // 允许反射访问
}
```

![exports 声明示例]({{ site.url }}/assets/img/jvm/jdk17-features/page12_img1.png)

#### uses 服务开放机制

基于模块化重新定制的 SPI 机制，实现接口与服务实现类的解耦：

**服务提供方（demoModule2）：**

```java
module roy.demomodule2 {
    exports com.roy.service;
    provides com.roy.service.HelloService with
            com.roy.service.impl.MorningHello,
            com.roy.service.impl.EveningHello;
}
```

**服务调用方（demoModule）：**

```java
module roy.demomodule {
    requires roy.demomodule2;
    uses com.roy.service.HelloService;
}
```

**代码调用：**

```java
ServiceLoader<HelloService> services = ServiceLoader.load(HelloService.class);
for (HelloService service : services) {
    System.out.println(service.sayHello("loulan"));
}
// 输出：good morning loulan
//       good evening loulan
```

![uses 服务调用]({{ site.url }}/assets/img/jvm/jdk17-features/page13_img1.png)

#### 构建模块化 Jar 包

```bash
# 指定模块路径运行
java --module-path demoModule/demoModule.jar:demoModule2/demoModule2.jar \
     -m roy.demomodule/com.roy.spi.ServiceDemo

# 列出模块
java --module-path demoModule:demoModule2_jar --list-modules
```

#### 类加载机制调整

![类加载器变化]({{ site.url }}/assets/img/jvm/jdk17-features/page16_img1.png)

| 调整项 | JDK8 | JDK17 |
|-------|------|-------|
| 扩展类加载器 | ExtClassLoader | **PlatformClassLoader**（平台类加载器） |
| 实现继承 | URLClassLoader | **BuiltinClassLoader**（内建类加载器） |
| Bootstrap | 无具体类 | 有明确类描述，但 `getClassLoader()` 仍返回 `null` |
| 双亲委派 | 先向上委派 | 先判断模块归属，优先委派给负责该模块的加载器 |

---

## 四、GC 调整

### 4.1 ZGC 转正

ZGC 自 JDK11 引入，**JDK15 正式投入生产使用**：

```bash
-XX:+UseZGC
```

在 JDK17 中，ZGC 相关的不稳定参数已基本取消，说明其算法优化已经相当成熟。

随 ZGC 登场的还有 RedHat 推出的 **Shenandoah** 垃圾回收器：

```bash
-XX:+UseShenandoahGC
```

### 4.2 废除 CMS

![CMS 废除]({{ site.url }}/assets/img/jvm/jdk17-features/page18_img1.png)

在 **JDK14** 中彻底删除 CMS 垃圾回收器。与 CMS 一起退场的还有 **SerialOld**。

> 虽然 CMS 在 JDK8 时代扮演重要角色，但 G1 已足够完善，ZGC/Shenandoah 也已登场，过于复杂的 CMS 终于退出历史舞台。

此外，JDK15 开始**默认废弃偏向锁**（可通过 `-XX:+UseBiasedLocking` 手动开启）。

---

## 五、GraalVM 虚拟机

虽然 GraalVM 目前仍在实验阶段，但它**极有可能替代 HotSpot**，成为 Java 生态的下一代技术基础。

### 5.1 关于 Graal

Graal 编译器最早是 HotSpot C1 编译器的下一代设计，使用 **Java 语言编写**。随着 JDK9 推出 **JVMCI**（Java 虚拟机编译器接口），Graal 从 HotSpot 中独立出来，形成了 GraalVM。

**为什么需要 GraalVM？**

在微服务、容器化时代，Java 的传统弱点凸显：
- 启动速度慢
- 预热时间长才能达到最佳性能
- 不适合短生命周期服务

而 GraalVM 的 AOT 编译能生成**不需要 JVM 即可运行的本地镜像**，这正是云原生时代需要的。

### 5.2 使用 GraalVM

![GraalVM 整体描述]({{ site.url }}/assets/img/jvm/jdk17-features/page19_img1.png)

官网：**https://www.graalvm.org**，提供 JDK17 和 JDK21 两个版本。

**下载安装：**

```bash
# 下载 tar 包后解压使用
tar -xzf graalvm-jdk-17.0.9-linux-aarch64.tar.gz
export JAVA_HOME=/path/to/graalvm
export PATH=$JAVA_HOME/bin:$PATH
java -version
# java version "17.0.9" 2023-10-17 LTS
# Java(TM) SE Runtime Environment Oracle GraalVM 17.0.9+11.1
```

**管理工具 `gu`：**

```bash
gu list
# ComponentId     Version     Component name
# graalvm         23.0.2      GraalVM Core
# native-image    23.0.2      Native Image
```

**体验 AOT 编译（Native Image）：**

```java
public class Hello {
    public static void main(String[] args) {
        System.out.println("Hello World!");
    }
}
```

```bash
# JIT 模式运行
time java Hello
# real 0m0.062s

# AOT 编译成本地镜像
native-image Hello

# 本地镜像运行 - 无需 JDK！
time ./hello
# real 0m0.006s  ← 速度提升近 10 倍！
```

![Native Image 编译过程]({{ site.url }}/assets/img/jvm/jdk17-features/page23_img1.png)

> 常见问题：如遇到 `找不到 -lz` 错误，需要安装 zlib：`sudo yum install zlib-devel`

![Native Image 运行对比]({{ site.url }}/assets/img/jvm/jdk17-features/page24_img1.png)

### 5.3 Truffle 框架

基于 GraalVM 的 **Truffle 框架**，未来可以开发各种语言的翻译器——**JS、Python、PHP、Lua** 等都可以在 GraalVM 上运行，再加上本地镜像执行方式，想象空间巨大。

---

## 六、总结

从 JDK8 到 JDK17 的核心变化一览：

| 类别 | JDK8 | JDK17 |
|------|------|-------|
| 字符串 | 手动拼接 | 文本块 `"""` |
| 条件分支 | switch 语句 | switch 表达式 + 箭头语法 + yield |
| 类型判断 | `instanceof` + 强转 | `instanceof` 模式匹配 |
| 数据载体 | POJO / DTO | record 记录类 |
| 类继承 | 无限制 | sealed / non-sealed / final |
| 动态类 | ASM 操作字节码 | Hidden Classes |
| 项目组织 | Jar 包 | Module + JMOD |
| 类加载器 | ExtClassLoader | PlatformClassLoader |
| GC | CMS / G1 | G1（默认）/ ZGC（可用） |
| 虚拟机 | HotSpot | HotSpot + GraalVM（可选） |

> Java 未来可期，你我不必再说 Java 没落了。

---

**参考链接：**

- [有道云笔记原文](https://note.youdao.com/s/6cCF3AsL)
- [GraalVM 官网](https://www.graalvm.org)
