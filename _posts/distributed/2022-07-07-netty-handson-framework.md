---
layout: post
title: "Netty实战：手写通信框架与面试难题分析"
date: 2022-07-07
categories: [distributed]
tags: [Netty, 实战, 通信框架, 心跳机制, 断线重连, 粘包拆包, 序列化]
comments: true
---

> 从零实现一个基于 Netty 的通信框架，涵盖 TCP 粘包拆包、序列化、心跳检测、断线重连、重复登录保护。

---

## 一、通信框架功能设计

### 六大核心功能

| 功能 | 说明 |
|------|------|
| **NIO 通信** | 基于 Netty 的高性能异步通信 |
| **编解码** | POJO 序列化和反序列化 |
| **防篡改** | 消息体 MD5 摘要 |
| **安全认证** | IP 地址白名单接入 |
| **链路校验** | 有效性校验 |
| **断线重连** | 链路中断后自动修复 |

---

## 二、消息定义

### 消息结构

```
┌──────────┬──────────┐
│  Header  │   Body   │
│  (消息头) │ (消息体)  │
└──────────┴──────────┘
```

### 消息头定义

| 字段 | 类型 | 说明 |
|------|------|------|
| `md5` | String | 消息体摘要（防篡改） |
| `msgID` | Long | 消息唯一 ID |
| `type` | Byte | 0:业务请求 1:业务响应 2:ONE WAY 3:握手请求 4:握手应答 5:心跳请求 6:心跳应答 |
| `priority` | Byte | 消息优先级 0~255 |
| `attachment` | Map | 扩展字段 |

---

## 三、通信模型

### 链路建立流程（握手认证）

```
Client                            Server
  │                                 │
  │──── 连接请求 ──────────────────▶│
  │                                 │  IP 地址校验
  │◀─── 连接建立 ──────────────────│
  │                                 │
  │──── 握手请求(节点ID等) ────────▶│
  │                                 │  节点ID有效性校验
  │                                 │  重复登录校验
  │◀─── 握手应答(0:成功/-1:失败) ──│  IP合法性校验
  │                                 │
  └──── 应用层链路建立成功 ─────────┘
  
  全双工通信：双方都可以主动发消息
```

---

## 四、可靠性设计

### 1、心跳机制（Ping-Pong）

```
链路空闲 → Client 发 Ping → Server 回 Pong
连续 N 次无 Pong → 链路挂死 → Client 关闭连接 → 重连

用 Netty IdleStateHandler：
  检测空闲连接 → 触发 IdleStateEvent
  → ChannelInboundHandler.userEventTriggered() 处理
```

```java
// 心跳检测
pipeline.addLast(new IdleStateHandler(0, 0, 30));  // 30秒没有读写
// → 在 userEventTriggered 中发送心跳
```

### 2、断线重连

```
链路中断 → 等待 INTERVAL 时间 → 发起重连
                            失败 → 间隔 INTERVAL → 再次重连
                            直到成功

注意：
  · 首次断连等待 INTERVAL（给服务端释放资源时间）
  · 每次失败都保证自身资源释放（SocketChannel/Socket）
  · 重连失败打印异常堆栈方便定位
```

### 3、重复登录保护

```
服务端握手校验：
  1. IP 合法性校验
  2. 检查是否已登录（缓存地址表）
     → 已登录 → 拒绝重复登录 → 关闭 TCP 链路 → 返回失败应答
  
客户端：
  收到握手失败 → 关闭连接 → 等待 INTERVAL → 重连
```

---

## 五、TCP 粘包/拆包解决

### 为什么会出现粘包？

TCP 是**面向流的协议**，不维护消息边界。可能：
- 多个小消息合并为一个数据包（粘包）
- 一个大消息被拆成多个数据包（拆包）

### Netty 解决方案

| 方案 | 类 | 原理 |
|------|-----|------|
| 固定长度 | `FixedLengthFrameDecoder` | 定长分割 |
| 分隔符 | `DelimiterBasedFrameDecoder` | 用特定分隔符分割 |
| 长度字段 | `LengthFieldBasedFrameDecoder` | 消息头包含长度 |

**实战方案（长度字段）**：

```java
pipeline.addLast(new LengthFieldBasedFrameDecoder(
    65535, 0, 4, 0, 4));
// 解读：最大65535字节，长度字段偏移0，长度字段占用4字节
pipeline.addLast(new LengthFieldPrepender(4));
```

---

## 六、序列化

### Kryo 序列化

```java
// Kryo 编码器
public class KryoEncoder extends MessageToByteEncoder<Object> {
    @Override
    protected void encode(ChannelHandlerContext ctx, Object msg, ByteBuf out) {
        Kryo kryo = KryoHolder.get();
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        Output output = new Output(baos);
        kryo.writeClassAndObject(output, msg);
        output.close();
        byte[] bytes = baos.toByteArray();
        out.writeInt(bytes.length);
        out.writeBytes(bytes);
    }
}
```

| 序列化框架 | 优点 | 缺点 |
|-----------|------|------|
| JDK Serializable | 内置、使用简单 | 慢、体积大 |
| JSON | 跨语言、可读 | 体积较大 |
| **Kryo** | 快、体积小 | 需手动注册 |
| Protobuf | 快、体积小、跨语言 | 需定义 .proto |

---

## 七、Handler 安装顺序

```
服务端 Handler 链：

  1. LengthFieldBasedFrameDecoder（解决粘包）
  2. LengthFieldPrepender（编码长度）
  3. KryoDecoder（反序列化）
  4. KryoEncoder（序列化）
  5. LoginAuthRespHandler（握手认证响应）→ 认证后移除
  6. HeartBeatRespHandler（心跳响应）
  7. ServerBusinessHandler（业务处理）
```

---

## 八、总结

```
Netty 通信框架五大核心机制：

  编解码    → LengthFieldBasedFrameDecoder + Kryo
  心跳      → IdleStateHandler + Ping-Pong
  重连      → 间隔重试 + 资源释放
  认证      → IP 白名单 + 握手 + 重复登录保护
  防篡改    → MD5/SHA 消息体摘要
```
