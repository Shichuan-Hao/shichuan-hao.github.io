---
layout: post
title: "Netty核心组件详解：Bootstrap/Channel/Pipeline/EventLoop全解析"
date: 2022-07-06
categories: [distributed]
tags: [Netty, Channel, EventLoop, Pipeline, ChannelHandler, 网络编程]
comments: true
---

> Netty 是一个异步事件驱动的网络应用框架，用于快速开发可维护的高性能协议服务器和客户端。版本：4.1.42.Final。

---

## 一、Netty 七大优势

| # | 优势 | 说明 |
|------|------|------|
| 1 | API 简单 | 开发门槛低 |
| 2 | 功能强大 | 预置多种编解码，支持主流协议 |
| 3 | 定制灵活 | 通过 ChannelHandler 灵活扩展 |
| 4 | 性能最高 | 业界 NIO 框架综合性能最优 |
| 5 | 成熟稳定 | 修复了所有 JDK NIO BUG |
| 6 | 社区活跃 | 快速迭代，BUG 及时修复 |
| 7 | 商业验证 | 大规模商业应用考验 |

---

## 二、为什么 Netty 不用 NIO5 / AIO / Mina？

| 问题 | 答案 |
|------|------|
| **Netty5** | 已停止开发，性能反而不如 Netty4 |
| **AIO** | Linux 底层仍用 epoll 实现，无性能优势；需预分配缓存，连接多时内存浪费 |
| **Mina** | 几乎不再更新，Netty 就是因 Mina 不够好而诞生的 |

---

## 三、Hello, Netty! 第一个程序

```java
// Echo 服务端
public class EchoServer {
    public static void main(String[] args) throws Exception {
        EventLoopGroup bossGroup = new NioEventLoopGroup(1);
        EventLoopGroup workerGroup = new NioEventLoopGroup();
        
        try {
            ServerBootstrap b = new ServerBootstrap();
            b.group(bossGroup, workerGroup)
                .channel(NioServerSocketChannel.class)
                .childHandler(new ChannelInitializer<SocketChannel>() {
                    @Override
                    protected void initChannel(SocketChannel ch) {
                        ch.pipeline().addLast(new EchoServerHandler());
                    }
                });
            
            ChannelFuture f = b.bind(9999).sync();
            f.channel().closeFuture().sync();
        } finally {
            bossGroup.shutdownGracefully();
            workerGroup.shutdownGracefully();
        }
    }
}
```

---

## 四、核心组件拆解

### 1、Bootstrap / ServerBootstrap

| | Bootstrap | ServerBootstrap |
|------|-----------|-----------------|
| 角色 | 客户端启动类 | 服务端启动类 |
| EventLoopGroup | 1个 | 2个（boss + worker） |

### 2、EventLoop 和 EventLoopGroup

```
EventLoop → 一个永远不变的 Thread
EventLoopGroup → 多个 EventLoop 的集合（线程池）

分配规则：
  Channel 创建 → round-robin 分配 EventLoop
  → 该 Channel 整个生命周期绑定同一个 EventLoop
  
重要影响：
  同一 EventLoop 的多个 Channel → 共享 ThreadLocal！
  不适合做状态追踪
```

**Netty 线程模型**：

```
Boss EventLoopGroup (1个线程) 
  → 接收连接 → 注册到 Worker EventLoopGroup

Worker EventLoopGroup (默认 CPU*2 个线程)
  → 处理 I/O 读写 → 执行 ChannelHandler
```

### 3、Channel 接口

| 生命周期状态 | 说明 |
|-------------|------|
| `ChannelUnregistered` | Channel 创建但未注册到 EventLoop |
| `ChannelRegistered` | 已注册到 EventLoop |
| `ChannelActive` | 处于活动状态（已连接远端） |
| `ChannelInactive` | 未连接到远端 |

**核心方法**：

| 方法 | 说明 |
|------|------|
| `eventLoop()` | 返回分配的 EventLoop |
| `pipeline()` | 返回 ChannelPipeline |
| `write()` | 写入内部缓存（未真正写 socket） |
| `flush()` | 刷新到底层 socket |
| `writeAndFlush()` | write + flush |

### 4、ChannelPipeline 和 ChannelHandler

```
Channel 创建 → 自动分配新 ChannelPipeline → 永久关联

ChannelPipeline = ChannelHandler 链
    入站事件: Head → InboundHandler1 → InboundHandler2 → ... → Tail
    出站事件: Tail → OutboundHandler2 → OutboundHandler1 → ... → Head
```

**事件分类**：

| 事件类型 | 触发场景 |
|----------|----------|
| **入站事件** | 连接激活/关闭、数据读取、用户事件、错误 |
| **出站事件** | 打开/关闭连接、写数据、冲刷数据 |

**Handler 执行顺序**：
- 入站：按 addLast 顺序执行
- 出站：按 addLast **逆序**执行

### 5、ChannelFuture

Netty 所有 I/O 操作都是**异步的**，返回 `ChannelFuture`。相比 JDK 的 `Future`（需手动检查或阻塞等待），Netty 提供更优的异步回调机制：

```java
ChannelFuture f = channel.writeAndFlush(msg);
f.addListener((ChannelFutureListener) future -> {
    if (future.isSuccess()) {
        System.out.println("写入成功");
    } else {
        future.cause().printStackTrace();
    }
});
```

---

## 五、ChannelHandler 的生命周期

| 方法 | 触发时机 |
|------|----------|
| `handlerAdded` | Handler 被添加到 Pipeline |
| `channelRegistered` | Channel 注册到 EventLoop |
| `channelActive` | Channel 激活 |
| `channelRead` | 读取到数据 |
| `channelReadComplete` | 数据读取完毕 |
| `channelInactive` | Channel 断开 |
| `channelUnregistered` | Channel 取消注册 |
| `handlerRemoved` | Handler 被移除 |

---

## 六、总结

```
Netty 组件关系：

  ServerBootstrap → BossGroup(NioEventLoop) 
                    → accept → 注册到 WorkerGroup(NioEventLoop)
                                 → Channel(SocketChannel)
                                    → ChannelPipeline
                                       → ChannelHandler 链

  一个 EventLoop 可以绑定多个 Channel
  但一个 Channel 只绑定一个 EventLoop（整个生命周期）
```
