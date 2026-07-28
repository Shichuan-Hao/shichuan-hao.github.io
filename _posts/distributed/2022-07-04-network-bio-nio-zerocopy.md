---
layout: post
title: "BIO实战、NIO编程与零拷贝深入辨析"
date: 2022-07-04
categories: [distributed]
tags: [BIO, NIO, 零拷贝, 直接内存, Socket, 网络编程]
comments: true
---

> Socket 是应用层与 TCP/IP 协议族通信的中间软件抽象层，它是一个门面模式，将复杂的 TCP/IP 协议处理隐藏在简单接口后面。

---

## 一、Socket 网络编程常识

### Socket 是什么

Socket 是一组接口，由操作系统提供。在设计模式中，Socket 就是一个**门面模式**，把复杂的 TCP/IP 协议处理和通信缓存管理隐藏在 Socket 接口后面。

```
客户端连接服务端 → 客户端产生一个 socket 实例
服务端接受连接 → 服务端产生一个 socket 实例 → 与客户端 socket 通信
N 个客户端 → N 个 socket 实例
```

### 长连接 vs 短连接

| | 短连接 | 长连接 |
|------|--------|--------|
| 过程 | 连接→传输→关闭 | 连接→传输→保持→传输→...→关闭 |
| 适用 | HTTP 网页（早期） | 数据库连接、即时通讯 |
| 优点 | 节省服务端资源 | 避免频繁建立连接（三次握手开销） |
| 缺点 | 频繁创建消耗资源 | 服务端资源占用多 |

**现代趋势**：HTTP 1.1 已支持长连接（Keep-Alive），HTTP/2 多路复用，HTTP/3 基于 QUIC。

### 网络编程三件事

所有通信编程都围绕三件事：
1. **连接**（服务端等待接收、客户端发起请求）
2. **读网络数据**
3. **写网络数据**

BIO 和 NIO 的区别就在于**处理这三件事的方式不同**。

---

## 二、BIO（Blocking I/O）

### 阻塞的两个地方

1. **等待客户端连接时阻塞**：`ServerSocket.accept()` 主线程一直等待
2. **读取数据时阻塞**：`InputStream.read()` 一直等待数据到达

### 传统 BIO 模型

```
ServerSocket.accept() → 接收连接 → 创建新线程 → 该线程负责读写
                                                ↓
                                            读写完成 → 线程销毁
```

**问题**：客户端并发数增加 → 服务端线程数 1:1 增长 → 系统性能急剧下降 → 最终宕机。

### 伪异步 I/O 模型（线程池改进）

```java
// 使用线程池限制线程数
ExecutorService pool = Executors.newFixedThreadPool(10);

while (true) {
    Socket socket = serverSocket.accept();
    pool.execute(() -> {
        // 处理读写
    });
}
```

**缺点**：限制了线程数量后，读取慢的连接会阻塞其他连接的请求排队等待。

---

## 三、NIO 核心概念

### 三大核心组件

| 组件 | 作用 | 类比 |
|------|------|------|
| **Channel** | 双向数据传输通道 | 铁轨 |
| **Buffer** | 数据缓冲区 | 火车 |
| **Selector** | 多路复用器，监控多个 Channel | 调度员 |

### Buffer 工作模式

```
Buffer核心属性:
  capacity  → 总容量
  position  → 当前位置
  limit     → 读写边界

写模式: position 随写入移动, limit = capacity
         flip() 切换
读模式: position 从0开始, limit = 已写位置
```

### Selector 多路复用

```java
// 核心流程
Selector selector = Selector.open();
channel.configureBlocking(false);
SelectionKey key = channel.register(selector, SelectionKey.OP_READ);

while (true) {
    int readyChannels = selector.select();  // 阻塞直到有就绪事件
    Set<SelectionKey> keys = selector.selectedKeys();
    for (SelectionKey key : keys) {
        if (key.isAcceptable())  { /* 处理连接 */ }
        if (key.isReadable())    { /* 处理读取 */ }
        if (key.isWritable())    { /* 处理写入 */ }
    }
    keys.clear();
}
```

**一个线程管理多个连接**，解决了 BIO 的 1:1 线程膨胀问题。

---

## 四、直接内存与零拷贝

### 普通 I/O 数据流程

```
应用程序 → 用户缓冲区 → 内核缓冲区(读) → 内核缓冲区(写) → 网络
          (context switch 2次)

硬盘 → 内核缓冲区 → 用户缓冲区 → Socket缓冲区 → 网络
    DMA       copy      copy        DMA
```

### 零拷贝（Zero Copy）

**sendfile**：数据不经过用户空间，直接在内核中传输。

```
硬盘 → 内核缓冲区 → Socket缓冲区 → 网络
    DMA      直接传输      DMA
            （零拷贝！）
```

**mmap + write**：文件映射到内存，减少一次拷贝。

### 直接内存 vs 堆内存

| | HeapByteBuffer | DirectByteBuffer |
|------|----------------|-------------------|
| 分配位置 | JVM 堆 | 操作系统本地内存 |
| I/O 操作 | 需复制到直接内存 | 直接操作，**零拷贝** |
| 创建销毁 | 快（JVM 管理） | 慢（系统调用） |
| 适用场景 | 小数据量、短生命周期 | 大数据量、长生命周期 |

---

## 五、RPC 原理解析

### 什么是 RPC

> RPC（Remote Procedure Call）—— 远程过程调用，像调用本地方法一样调用远程服务。

### RPC 调用流程

```
1. Client 调用 client stub（本地代理）
2. client stub 序列化 → 网络发送
3. Server stub 反序列化 → 调用实际方法
4. Server 执行 → 结果序列化 → 网络返回
5. Client stub 反序列化 → 返回结果
```

### RPC 核心要素

- **代理**：远程服务在本地模拟对象（静态/动态代理）
- **序列化**：JDK 原生 / JSON / Protobuf / Kryo
- **网络通信**：BIO / NIO / Netty
- **反射**：将调用名转为实际方法执行

---

## 六、总结

```
BIO（阻塞）：
  accept() 阻塞等待 → read() 阻塞读取
  → 1连接:1线程 → 并发大崩溃

NIO（非阻塞）：
  Channel + Buffer + Selector
  → 1个线程管理多个 Channel

零拷贝：
  sendfile → 数据不走用户空间
  DirectByteBuffer → JVM堆外直接 I/O

RPC：
  代理 + 序列化 + 网络传输 + 反射
  = 远程调用像本地调用
```
