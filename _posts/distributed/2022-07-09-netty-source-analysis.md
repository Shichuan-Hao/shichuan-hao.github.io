---
layout: post
title: "Netty核心源码剖析：主从Reactor线程模型与高性能架构设计"
date: 2022-07-09
categories: [distributed]
tags: [Netty, 源码分析, Reactor, 线程模型, 无锁串行, ByteBuf, 零拷贝]
comments: true
---

> Netty 源码核心看点：主从 Reactor 线程模型、无锁串行化设计、ByteBuf 内存池、零拷贝。

---

## 一、Netty 高并发高性能架构设计精髓

| 设计要点 | 说明 |
|----------|------|
| **主从 Reactor 线程模型** | Boss 负责连接，Worker 负责读写 |
| **NIO 多路复用** | 一个线程处理多个 Channel |
| **无锁串行化设计** | 消息在同一个线程内处理，避免锁竞争 |
| **高性能序列化** | 支持 Protobuf 等高效协议 |
| **零拷贝** | DirectByteBuffer 直接内存 |
| **ByteBuf 内存池** | 减少内存分配和 GC |
| **灵活 TCP 参数** | 可精细调优 |

---

## 二、无锁串行化设计思想

### 为什么不用多线程？

多线程处理共享资源 → 锁竞争 → 性能下降。

### Netty 的无锁设计

```
NioEventLoop 读取消息 → 直接调用 ChannelPipeline.fireChannelRead()
→ 一直由同一个 NioEventLoop 调用到用户 Handler
→ 全程不切换线程 → 无锁竞争
```

**Redis 为什么快也是类似原因** — 单线程 + 串行处理。

### 表面矛盾的分析

```
串行化设计 → 看似 CPU 利用率不高
但 → 通过调整 NIO 线程池参数
  → 可同时启动多个串行化线程并行运行
  → 局部无锁 + 全局并行
  → 比 1个队列:N个Worker线程 模式更优
```

---

## 三、直接内存 vs 堆内存

```java
public class DirectMemoryTest {
    
    public static void heapAccess() {
        long startTime = System.currentTimeMillis();
        ByteBuffer buffer = ByteBuffer.allocate(1000);
        for (int i = 0; i < 100000; i++) {
            for (int j = 0; j < 200; j++) {
                buffer.putInt(j);
            }
            buffer.flip();
            for (int j = 0; j < 200; j++) {
                buffer.getInt();
            }
            buffer.clear();
        }
        System.out.println("堆内存访问:" + (System.currentTimeMillis() - startTime) + "ms");
    }

    public static void directAccess() {
        long startTime = System.currentTimeMillis();
        ByteBuffer buffer = ByteBuffer.allocateDirect(1000);
        // 同样的操作...
        System.out.println("直接内存访问:" + (System.currentTimeMillis() - startTime) + "ms");
    }
}
```

**结果**：直接内存明显更快，因为避免了 JVM 堆 → 内核缓冲区的拷贝。

---

## 四、主从 Reactor 线程模型

```
                    ┌───────────┐
   Client 1 ──────▶│           │
   Client 2 ──────▶│  Boss     │  accept
   Client N ──────▶│ NioEventLoop │
                    └─────┬─────┘
                          │ 注册到 Worker
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
    ┌─────────┐     ┌─────────┐     ┌─────────┐
    │ Worker  │     │ Worker  │     │ Worker  │
    │ EventLoop│    │ EventLoop│    │ EventLoop│
    │ (read/  │     │ (read/  │     │ (read/  │
    │  write/ │     │  write/ │     │  write/ │
    │  handler)│    │  handler)│    │  handler)│
    └─────────┘     └─────────┘     └─────────┘
```

**核心要点**：
- Boss Group（通常 1 个线程）：负责接收连接
- Worker Group（默认 CPU×2 线程）：负责 I/O 读写和 Pipeline 处理
- 一个 Channel 绑定一个 EventLoop（整个生命周期）

---

## 五、ByteBuf 内存池设计

| 分配方式 | 特点 | 适用 |
|----------|------|------|
| `PooledByteBufAllocator` | 内存池化，减少 GC | **生产环境默认** |
| `UnpooledByteBufAllocator` | 每次新建 | 测试/特殊情况 |

```java
// 池化分配
ByteBuf buf = PooledByteBufAllocator.DEFAULT.buffer(1024);
// 堆分配
ByteBuf heapBuf = Unpooled.buffer(1024);
// 直接内存分配
ByteBuf directBuf = Unpooled.directBuffer(1024);
```

---

## 六、零拷贝在 Netty 中的体现

1. **DirectByteBuffer**：堆外内存，I/O 直接操作，避免拷贝到堆
2. **CompositeByteBuf**：多个 ByteBuf 合并，物理上零拷贝
3. **FileRegion**：`transferTo()` 实现文件传输零拷贝
4. **slice/duplicate**：共享同一块内存的视图

---

## 七、总结

```
Netty 高性能架构核心：

  Reactor 模型 → Boss(accept) + Worker(read/write)
  无锁串行化   → 同线程处理避免锁竞争
  直接内存     → 避免堆拷贝
  ByteBuf 池   → 减少 GC 压力
  零拷贝       → DirectBuf + CompositeBuf + FileRegion

  源码 = 设计思想 + 算法实现 + 工程优化
```

> 有道云笔记：[Netty核心源码剖析](https://vip.tulingxueyuan.cn/detail/p_6006d2b8e4b0ab9a254a57fc/6)
