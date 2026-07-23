---
title: Spring6.0及SpringBoot3.0新特性解析
categories: [Java, Spring, 框架源码]
tags: [Spring6, SpringBoot3, GraalVM, AOT, Native Image, RuntimeHints, Docker]
author: hsc
date: 2022-05-30 00:00:00 +0800
description: 深入Spring6.0及SpringBoot3.0新特性，解析GraalVM原生编译、Spring AOT机制、RuntimeHints与Docker构建实战。
mindmap: https://www.processon.com/view/link/63edeea8440e433d3d6a88b2
---

# Spring6.0及SpringBoot3.0新特性解析

> Spring 6.0 / Spring Boot 3.0 要求 Java 17+，最核心的新特性是 **Spring AOT**。

## 一、GraalVM 简介

GraalVM 可以将 Java 字节码编译为**原生二进制可执行文件（Native Image）**。

### 优势

| 特性 | 常规JVM | Native Image |
|------|---------|--------------|
| 启动速度 | 秒级 | 毫秒/亚秒级 |
| 内存占用 | 高 | 低（无需JIT、类加载） |
| 预热 | 需要 | 不需要 |
| 需要JDK | 是 | 否（独立运行） |

### Hello World 示例

```bash
# 编译
javac -d . src/com/zhouyu/App.java
# 生成原生可执行文件
native-image com.zhouyu.App -o app
# 直接运行
./app
```

### 环境要求
- GraalVM（替代标准JDK）
- Visual Studio Build Tools（C语言环境）
- x64 Native Tools Command Prompt

### GraalVM 限制

编译时需要确定应用用到了哪些类、哪些方法、哪些属性。动态生成的类（反射、代理等）需要通过配置告诉 GraalVM：

- `reflect-config.json`：反射相关配置
- `proxy-config.json`：动态代理配置
- `resource-config.json`：资源文件配置

---

## 二、SpringBoot 3.0 原生编译

### Maven 配置

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.0.0</version>
</parent>

<build>
    <plugins>
        <plugin>
            <groupId>org.graalvm.buildtools</groupId>
            <artifactId>native-maven-plugin</artifactId>
        </plugin>
        <plugin>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-maven-plugin</artifactId>
        </plugin>
    </plugins>
</build>
```

### 编译命令

```bash
mvn -Pnative native:compile
```

---

## 三、Docker 构建

利用 **Buildpacks** 技术，不需要本机安装 GraalVM：

```xml
<properties>
    <spring-boot.build-image.imageName>springboot3demo</spring-boot.build-image.imageName>
</properties>
```

```bash
mvn -Pnative spring-boot:build-image
```

运行容器：

```bash
docker run --rm -p 8080:8080 springboot3demo
```

传参：

```bash
docker run --rm -p 8080:8080 -e methodName=test springboot3demo
# 代码中 System.getenv("methodName") 获取
```

---

## 四、RuntimeHints 机制

### 问题场景

代码中使用反射，编译时 GraalVM 不知道该用哪些方法 → 运行时报错：

```java
Method test = ZhouyuService.class.getMethod("test", null);
test.invoke(ZhouyuService.class.newInstance(), null);
```

### 三种配置方式

#### 方式一：RuntimeHintsRegistrar

```java
@Component
@ImportRuntimeHints(UserService.ZhouyuServiceRuntimeHints.class)
public class UserService {
    
    static class ZhouyuServiceRuntimeHints implements RuntimeHintsRegistrar {
        @Override
        public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
            hints.reflection()
                .registerConstructor(ZhouyuService.class.getConstructor(), ExecutableMode.INVOKE)
                .registerMethod(ZhouyuService.class.getMethod("test"), ExecutableMode.INVOKE);
        }
    }
}
```

#### 方式二：@RegisterReflectionForBinding

```java
@RegisterReflectionForBinding(ZhouyuService.class)
public String test() { ... }
```

#### 方式三：@Reflective（Bean场景）

```java
@Component
public class ZhouyuService {
    @Reflective
    public ZhouyuService() { }
    
    @Reflective
    public String test() { return "zhouyu"; }
}
```

### JDK动态代理配置

```java
hints.proxies().registerJdkProxy(UserInterface.class);
```

---

## 五、Spring AOT 核心原理

### 编译时流程

```
mvn -Pnative native:compile
    ├── 1. 编译Java代码
    ├── 2. 执行 ProcessAotMojo（process-aot阶段）
    │   ├── SpringApplicationAotProcessor.process()
    │   ├── performAotProcessing() 生成：
    │   │   ├── spring-aot/main/sources → Xx_BeanDefinitions.java
    │   │   ├── spring-aot/main/resources → GraalVM配置文件
    │   │   └── spring-aot/main/classes
    │   └── 编译生成的Java文件 → class → 放入target/classes
    └── 3. GraalVM打包二进制可执行文件
```

### AOT 核心代码

```java
// ContextAotProcessor
ApplicationContextAotGenerator generator = new ApplicationContextAotGenerator();

// 扫描并生成 Xx_BeanDefinitions.java
ClassName generatedInitializerClassName = 
    generator.processAheadOfTime(applicationContext, generationContext);

// 将RuntimeHints写入GraalVM配置文件
writeHints(generationContext.getRuntimeHints());
```

**AOT 做了什么？**
1. 扫描 BeanDefinition → 预生成注册代码（替代运行时扫描）
2. 找出代理类 → 预配置到 reflect-config.json
3. RuntimeHints → 生成 GraalVM 配置文件

> AOT 相当于把 Spring 启动时的扫描、解析等工作提前到编译时完成，运行时直接执行，大幅减少启动时间。

---

## 六、总结

```
Spring 6.0 / Boot 3.0 核心变化：
├── 最低要求 Java 17
├── 全面支持 GraalVM Native Image
└── Spring AOT（提前编译）→ 启动速度质的飞跃

GraalVM：
├── 编译时确定代码范围（封闭世界假设）
└── 动态特性需要配置文件声明

RuntimeHints：
├── 声明式配置反射/代理/资源
└── Spring在AOT阶段自动转为GraalVM配置文件
```
