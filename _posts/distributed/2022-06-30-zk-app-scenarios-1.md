---
layout: post
title: "Zookeeper应用场景实战（一）：Java客户端与Curator框架详解"
date: 2022-06-30
categories: [distributed]
tags: [Zookeeper, Java客户端, Curator, 原生API, 监听机制]
comments: true
---

> Zookeeper的Watch是一次性的，原生API在实际开发中比较笨重。Curator框架解决了这些问题，提供了更优雅的API。

---

## 一、Zookeeper Java客户端选择

| 客户端 | 说明 |
|--------|------|
| **ZooKeeper官方API** | 基本操作：创建会话/节点、读写数据、删除、检查存在 |
| **Curator**（Netflix） | 封装了原生API，提供了更高级的封装和功能 |
| **ZkClient** | 早期的第三方封装（已较少使用） |

### 原生API的问题

1. **Watch 一次性的**：每次触发后需重新注册
2. **无重连机制**：会话超时后不会自动重连
3. **异常处理繁琐**：很多异常类型，难以正确处理
4. **仅支持 byte[] 数组**：没有 Java POJO 级别的序列化
5. **创建节点异常需自行检查**：节点存在与否需手动判断
6. **无法级联删除**：需递归删除子节点

---

## 二、ZooKeeper 原生API实战

### Maven依赖

```xml
<dependency>
    <groupId>org.apache.zookeeper</groupId>
    <artifactId>zookeeper</artifactId>
    <version>3.8.0</version>
</dependency>
```

> 保持客户端与服务端版本一致！

### 连接Zookeeper

```java
public class ZkClientDemo {
    private static final String CLUSTER_CONNECT_STR = 
        "192.168.65.156:2181,192.168.65.190:2181,192.168.65.200:2181";

    public static void main(String[] args) throws Exception {
        final CountDownLatch countDownLatch = new CountDownLatch(1);
        
        ZooKeeper zooKeeper = new ZooKeeper(CLUSTER_CONNECT_STR, 
            4000, new Watcher() {
            @Override
            public void process(WatchedEvent event) {
                if (Event.KeeperState.SyncConnected == event.getState()
                        && event.getType() == Event.EventType.None) {
                    // 连接建立成功
                    countDownLatch.countDown();
                    System.out.println("连接建立");
                }
            }
        });
        
        System.out.println("连接中...");
        countDownLatch.await();
        System.out.println(zooKeeper.getState());  // CONNECTED
    }
}
```

**构造器参数**：

| 参数 | 说明 |
|------|------|
| `connectString` | 逗号分隔的 host:port 列表，客户端任意选取一个连接 |
| `sessionTimeout` | session 超时时间（毫秒） |
| `watcher` | 用于接收 ZK 集群事件 |

### 创建节点

```java
// 创建持久节点
zooKeeper.create("/user", "fox".getBytes(),
    ZooDefs.Ids.OPEN_ACL_UNSAFE, CreateMode.PERSISTENT);

// 异步创建
zooKeeper.create("/user2", "fox2".getBytes(),
    ZooDefs.Ids.OPEN_ACL_UNSAFE, CreateMode.PERSISTENT,
    (rc, path, ctx, name) -> {
        System.out.println("创建完成: " + name);
    }, "ctx");
```

### 常用操作

```java
// 获取数据 + Watch
byte[] data = zooKeeper.getData("/user", watchedEvent -> {
    System.out.println("节点变化: " + watchedEvent.getPath());
}, null);

// 更新数据
Stat stat = zooKeeper.setData("/user", "newValue".getBytes(), -1);

// 检查是否存在
Stat exist = zooKeeper.exists("/user", false);

// 删除节点
zooKeeper.delete("/user", -1);

// 获取子节点
List<String> children = zooKeeper.getChildren("/", false);
```

---

## 三、Curator 框架

### Curator vs 原生API

| 特性 | 原生API | Curator |
|------|---------|---------|
| Watch注册 | 一次性 | 持久化Watcher |
| 连接重试 | 需手动实现 | 内置重试策略 |
| API风格 | 原始byte[] | Fluent流式API |
| 分布式锁 | 需自行实现 | 内置InterProcessMutex等 |
| Leader选举 | 需自行实现 | 内置LeaderLatch/LeaderSelector |
| 版本兼容 | — | 自动处理版本兼容 |

### Maven依赖

```xml
<dependency>
    <groupId>org.apache.curator</groupId>
    <artifactId>curator-recipes</artifactId>
    <version>5.5.0</version>
</dependency>
```

### Curator基本使用

```java
// 创建客户端（Fluent风格）
CuratorFramework client = CuratorFrameworkFactory.builder()
    .connectString("192.168.65.156:2181,192.168.65.190:2181,192.168.65.200:2181")
    .sessionTimeoutMs(4000)
    .retryPolicy(new ExponentialBackoffRetry(1000, 3))  // 重试策略
    .namespace("myApp")       // 业务命名空间（所有操作自动加 /myApp 前缀）
    .build();

client.start();

// 创建节点（Fluent API）
client.create()
    .creatingParentsIfNeeded()     // 自动创建父节点
    .withMode(CreateMode.PERSISTENT)
    .forPath("/user", "fox".getBytes());

// 获取数据
byte[] data = client.getData().forPath("/user");

// 更新数据
client.setData().forPath("/user", "newValue".getBytes());

// 删除节点（级联删除）
client.delete()
    .deletingChildrenIfNeeded()    // 级联删除子节点
    .forPath("/user");

// 带Watcher的获取
client.getData().usingWatcher(new CuratorWatcher() {
    @Override
    public void process(WatchedEvent event) throws Exception {
        System.out.println("节点变化: " + event.getPath());
    }
}).forPath("/user");
```

### 重试策略

| 策略 | 说明 |
|------|------|
| `ExponentialBackoffRetry` | 指数退避重试（推荐） |
| `RetryNTimes` | 固定次数重试 |
| `RetryOneTime` | 仅重试一次 |
| `RetryUntilElapsed` | 在指定时间内一直重试 |

---

## 四、总结

```
ZK 客户端选型：

  原生 API  → 学习理解原理
  Curator   → 生产环境使用（强烈推荐）

Curator 优势：
  持久化Watch → 自动重连 → Fluent API → 内置分布式锁
  级联删除 → 自动重试 → 命名空间隔离
```

> 有道云笔记：[Zookeeper经典应用场景实战一](https://note.youdao.com/s/a3vbCh9A)
