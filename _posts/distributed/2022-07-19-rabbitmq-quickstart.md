---
layout: post
title: "RabbitMQ快速上手：AMQP核心模型与Exchange路由机制详解"
date: 2022-07-19
categories: [distributed]
tags: [RabbitMQ, AMQP, Exchange, 队列, 消息中间件, 路由]
comments: true
---

> RabbitMQ 是基于 AMQP 协议的开源消息代理软件，使用 Erlang 语言开发。特点是消息可靠性高、功能全面。

---

## 一、AMQP 核心模型

### 四大核心组件

```
Producer → Exchange → Queue → Consumer
           (路由)     (存储)    (消费)

                  [Routing Key -> Queue 绑定]
```

| 组件 | 职责 |
|------|------|
| **Producer** | 发送消息到 Exchange |
| **Exchange** | 接收消息，按路由规则转发到 Queue |
| **Queue** | 消息存储，等待消费 |
| **Consumer** | 从 Queue 拉取或接收推送 |

**Connection 和 Channel**：
- Connection = TCP 长连接
- Channel = 连接内的虚拟通道（复用 TCP 连接，节省资源）
- 一个 Connection 可以有多个 Channel

---

## 二、四种 Exchange 类型

### 1、Direct Exchange（直连交换机）

```
Routing Key 精确匹配

Exchange (direct)
  ├── routingKey:"order" → Queue A
  ├── routingKey:"pay"   → Queue B
  └── routingKey:"log"   → Queue C
```

### 2、Fanout Exchange（广播交换机）

```
忽略 Routing Key，广播到所有绑定 Queue

Exchange (fanout)
  ├── Queue A  ← 收到所有消息
  ├── Queue B  ← 收到所有消息
  └── Queue C  ← 收到所有消息
```

### 3、Topic Exchange（主题交换机）

```
Routing Key 模式匹配

Exchange (topic)
  ├── "order.*"   → Queue A  (order.create, order.cancel)
  ├── "*.log"     → Queue B  (order.log, pay.log)
  └── "#"         → Queue C  (匹配所有)
```

通配符：`*` 匹配一个词，`#` 匹配零或多个词。

### 4、Headers Exchange

根据消息 Header 属性匹配（不用 Routing Key），较少使用。

---

## 三、RabbitMQ 安装

```bash
# 依赖 Erlang 环境（RabbitMQ 自带）
# 下载并安装
yum install erlang   # 或从 Erlang Solutions 获取
rpm -ivh rabbitmq-server-3.x.x.noarch.rpm

# 启动
systemctl start rabbitmq-server

# 启用管理插件（Web UI）
rabbitmq-plugins enable rabbitmq_management

# 访问: http://localhost:15672
# 默认账号：guest/guest
```

---

## 四、Java 客户端快速上手

```java
// 1. 创建连接
ConnectionFactory factory = new ConnectionFactory();
factory.setHost("localhost");
Connection connection = factory.newConnection();

// 2. 创建 Channel
Channel channel = connection.createChannel();

// 3. 声明 Exchange + Queue + 绑定
channel.exchangeDeclare("order_exchange", BuiltinExchangeType.DIRECT);
channel.queueDeclare("order_queue", true, false, false, null);
channel.queueBind("order_queue", "order_exchange", "order.create");

// 4. 发送消息
channel.basicPublish("order_exchange", "order.create", 
    null, "Hello RabbitMQ".getBytes());

// 5. 消费消息
channel.basicConsume("order_queue", true, (consumerTag, message) -> {
    System.out.println(new String(message.getBody()));
}, consumerTag -> {});
```

---

## 五、关键配置

```yaml
spring:
  rabbitmq:
    host: localhost
    port: 5672
    username: guest
    password: guest
    virtual-host: /
    
    # 生产者确认
    publisher-confirm-type: correlated
    publisher-returns: true
    
    # 消费者确认
    listener:
      simple:
        acknowledge-mode: manual  # 手动确认
```

---

## 六、RabbitMQ 高级特性概览

| 特性 | 说明 |
|------|------|
| **消息确认** | Publisher Confirm + Consumer Ack |
| **持久化** | 消息和队列持久化到磁盘（防丢） |
| **TTL** | 消息过期时间 |
| **死信队列** | 过期/拒绝/队列满的消息放入死信 |
| **延迟队列** | TTL + 死信队列实现延迟消费 |
| **优先级队列** | 队列设置优先级 |
| **镜像队列** | 队列数据多节点备份（高可用经典方案） |
| **Quorum 队列** | 基于 Raft 的新一代高可用（替代镜像队列） |

---

## 七、总结

```
AMQP 模型：
  Producer → Exchange(routing) → Queue(storage) → Consumer

Exchange 四种类型：
  Direct → 精确匹配 Routing Key
  Fanout → 广播所有
  Topic  → 模式匹配 (* 和 #)
  Headers → Header 属性匹配

核心优势：可靠性高 + 功能全面 + 管理界面友好
核心短板：吞吐量较低 + Erlang 小众 + 消息积压影响性能
```
