---
layout: post
title: "RocketMQ客户端编程模型：Producer/Consumer/Filter三种编程范式"
date: 2022-07-11
categories: [distributed]
tags: [RocketMQ, 客户端, Producer, Consumer, 消息过滤, 编程模型]
comments: true
---

## 一、RocketMQ 客户端 SDK 概述

RocketMQ 提供多种语言的客户端 SDK。Java 客户端是最成熟、最完善的。

```xml
<dependency>
    <groupId>org.apache.rocketmq</groupId>
    <artifactId>rocketmq-client</artifactId>
    <version>5.3.0</version>
</dependency>
```

---

## 二、Producer 三种发送方式

### 1、同步发送

```java
DefaultMQProducer producer = new DefaultMQProducer("producer_group");
producer.setNamesrvAddr("localhost:9876");
producer.start();

Message msg = new Message("TopicTest", "TagA", "Hello RocketMQ".getBytes());
SendResult result = producer.send(msg);
// result.getSendStatus() = SEND_OK / FLUSH_DISK_TIMEOUT / ...

producer.shutdown();
```

### 2、异步发送

```java
producer.send(msg, new SendCallback() {
    @Override
    public void onSuccess(SendResult result) {
        System.out.println("发送成功: " + result.getMsgId());
    }
    @Override
    public void onException(Throwable e) {
        System.err.println("发送失败: " + e.getMessage());
    }
});
```

### 3、单向发送（不关心结果）

```java
producer.sendOneway(msg);  // 不等待响应，性能最高
```

### 三种方式对比

| 方式 | 可靠性 | 性能 | 适用 |
|------|--------|------|------|
| 同步 | 高 | 低 | 重要消息 |
| 异步 | 中 | 中 | 普通业务 |
| 单向 | 低 | 高 | 日志类 |

---

## 三、Consumer 两种消费模式

### 1、PushConsumer（主动推送）

```java
DefaultMQPushConsumer consumer = new DefaultMQPushConsumer("consumer_group");
consumer.setNamesrvAddr("localhost:9876");
consumer.subscribe("TopicTest", "*");  // * = 所有Tag

consumer.registerMessageListener((MessageListenerConcurrently) (msgs, context) -> {
    for (MessageExt msg : msgs) {
        System.out.println(new String(msg.getBody()));
    }
    return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
    // 失败返回 RECONSUME_LATER，稍后重试
});

consumer.start();
```

### 2、PullConsumer（拉取）

```java
DefaultLitePullConsumer consumer = new DefaultLitePullConsumer("consumer_group");
consumer.setNamesrvAddr("localhost:9876");
consumer.subscribe("TopicTest", "*");
consumer.start();

while (true) {
    List<MessageExt> msgs = consumer.poll(1000);
    msgs.forEach(msg -> {
        System.out.println(new String(msg.getBody()));
    });
    consumer.commitSync();  // 手动提交offset
}
```

---

## 四、消息过滤

### Tag 过滤

```java
// Producer：带 Tag 发送
Message msg = new Message("TopicTest", "TagA|TagB", "message".getBytes());

// Consumer：过滤 Tag
consumer.subscribe("TopicTest", "TagA || TagB");
```

### SQL92 过滤（需 Broker 配置 `enablePropertyFilter=true`）

```java
// Producer：设置属性
msg.putUserProperty("age", "25");
msg.putUserProperty("name", "张三");

// Consumer：SQL 过滤
consumer.subscribe("TopicTest", 
    MessageSelector.bySql("age > 18 and name = '张三'"));
```

---

## 五、顺序消息

```java
// 同一业务ID → 同一MessageQueue
producer.send(msg, (mqs, msg1, arg) -> {
    Long orderId = (Long) arg;
    int index = (int) (orderId % mqs.size());
    return mqs.get(index);
}, orderId);

// Consumer 端
consumer.registerMessageListener((MessageListenerOrderly) (msgs, context) -> {
    // 同一个 MessageQueue 的消息在这个回调里有序
    return ConsumeOrderlyStatus.SUCCESS;
});
```

---

## 六、延迟消息

```java
Message msg = new Message("TopicTest", "TagA", "message".getBytes());
msg.setDelayTimeLevel(3);  // 延迟10秒（预设等级 1s~2h）
producer.send(msg);
```

延迟等级：`1=1s, 2=5s, 3=10s, 4=30s, 5=1m, 6=2m, ... 18=2h`

---

## 七、总结

```
Producer 三模式：同步 / 异步 / 单向
Consumer 两模式：Push / Pull (LitePull)
消息过滤：Tag + SQL92
顺序消息：同一ID → 同一队列 + MessageListenerOrderly
延迟消息：setDelayTimeLevel
```
