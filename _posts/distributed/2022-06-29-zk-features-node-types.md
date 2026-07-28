---
layout: post
title: "Zookeeper特性与节点数据类型详解"
date: 2022-06-29
categories: [distributed]
tags: [Zookeeper]
comments: true
---

## 一、Zookeeper概述

Zookeeper 是一个开源的分布式协调服务，由雅虎研究院开发，后来贡献给Apache基金会。它是Google Chubby的开源实现，主要用于解决分布式环境下的数据一致性、命名服务、配置管理、集群管理、分布式锁、分布式队列等问题。

### 1.1 Zookeeper的核心设计目标

Zookeeper的设计目标非常明确：

- **简单性**：Zookeeper允许分布式进程通过一个共享的、类似标准文件系统的分层命名空间来相互协调。命名空间由数据寄存器（znode）组成，这些寄存器类似于文件和目录。与典型的文件系统不同，Zookeeper数据存储在内存中，这意味着Zookeeper可以实现高吞吐量和低延迟。
- **可靠性**：Zookeeper被设计为可复制的，一组Zookeeper服务器构成一个集群。只要集群中大多数服务器可用，Zookeeper服务就可用。
- **有序性**：Zookeeper通过维护全局递增的事务ID（zxid）来保证所有更新操作的全局顺序。
- **快速性**：Zookeeper在读多写少的场景下表现优异，读写比约为10:1时性能最佳。

### 1.2 Zookeeper的数据模型

Zookeeper的数据模型类似于一个树形结构的文件系统，每个节点称为**ZNode**。每个ZNode既可以保存数据，也可以拥有子节点。

```
/
├── /app1
│   ├── /app1/config
│   └── /app1/workers
├── /app2
│   └── /app2/locks
└── /zookeeper
    ├── /zookeeper/quota
    └── /zookeeper/config
```

**ZNode的核心特性**：

1. **路径唯一性**：每个ZNode由绝对路径唯一标识，路径中的每个部分用"/"分隔。
2. **数据存储**：每个ZNode可以存储少量数据（默认最大1MB），适合存储配置信息、状态信息等小数据。
3. **版本控制**：每个ZNode的数据、ACL（访问控制列表）和时间戳都有版本号（version），每次修改版本号递增。
4. **时间戳**：每个ZNode包含三个时间戳：
   - `czxid`：创建该节点时的事务ID
   - `mzxid`：最后一次修改该节点时的事务ID
   - `ctime/mtime`：创建时间/修改时间

## 二、Zookeeper的节点类型详解

Zookeeper提供了四种节点类型，每种类型都有不同的生命周期和语义。

### 2.1 持久节点（PERSISTENT）

**特点**：
- 一旦创建，除非主动删除，否则将一直存在于Zookeeper中
- 是最基础的节点类型
- 适用场景：存储固定的配置信息、服务注册信息等

```java
// 创建持久节点
String path = zookeeper.create("/config/db", 
    "jdbc:mysql://localhost:3306/mydb".getBytes(),
    ZooDefs.Ids.OPEN_ACL_UNSAFE, 
    CreateMode.PERSISTENT);
```

### 2.2 持久顺序节点（PERSISTENT_SEQUENTIAL）

**特点**：
- 在持久节点的基础上，Zookeeper会自动在节点名称后添加一个10位的递增序号
- 序号由父节点维护，全局递增
- 适用场景：分布式队列、分布式锁等需要顺序的场景

```java
// 创建持久顺序节点，实际节点名类似 /queue/task-0000000001
String path = zookeeper.create("/queue/task-", 
    data.getBytes(),
    ZooDefs.Ids.OPEN_ACL_UNSAFE, 
    CreateMode.PERSISTENT_SEQUENTIAL);
```

**序号生成规则**：
- 序号使用10位数字，从0000000000开始
- 序号是全局唯一的，且单调递增
- 格式：`节点前缀` + 10位数字，如 `/locks/lock-0000000001`

### 2.3 临时节点（EPHEMERAL）

**特点**：
- 节点的生命周期与客户端会话绑定
- 当创建该节点的客户端会话断开时，该节点会被自动删除
- 临时节点不能拥有子节点
- 适用场景：服务发现、集群成员管理等

```java
// 创建临时节点
String path = zookeeper.create("/services/service-1", 
    "192.168.1.100:8080".getBytes(),
    ZooDefs.Ids.OPEN_ACL_UNSAFE, 
    CreateMode.EPHEMERAL);
```

**重要机制**：
- 客户端会话超时后，Zookeeper会自动清理该客户端创建的所有临时节点
- 可以通过临时节点的存在与否来判断服务是否在线
- 临时节点在客户端主动断开连接时也会被删除

### 2.4 临时顺序节点（EPHEMERAL_SEQUENTIAL）

**特点**：
- 结合了临时节点和顺序节点的特性
- 节点名称自动添加递增序号
- 客户端会话断开时自动删除
- 适用场景：分布式锁（特别是公平锁）、Leader选举等

```java
// 创建临时顺序节点
String path = zookeeper.create("/election/candidate-", 
    "host-001".getBytes(),
    ZooDefs.Ids.OPEN_ACL_UNSAFE, 
    CreateMode.EPHEMERAL_SEQUENTIAL);
```

### 2.5 节点类型对比表

| 节点类型 | 持久性 | 顺序性 | 子节点 | 典型场景 |
|---------|--------|--------|--------|---------|
| PERSISTENT | 持久存在 | 无 | 可拥有 | 配置存储 |
| PERSISTENT_SEQUENTIAL | 持久存在 | 有 | 可拥有 | 分布式队列 |
| EPHEMERAL | 会话结束即删除 | 无 | 不能有 | 服务注册 |
| EPHEMERAL_SEQUENTIAL | 会话结束即删除 | 有 | 不能有 | 分布式锁/选举 |

## 三、Zookeeper的核心特性

### 3.1 顺序一致性（Sequential Consistency）

从一个客户端发起的更新请求，会严格按照该客户端发送的顺序被处理。

**实现机制**：
- Zookeeper为每个更新操作分配一个全局唯一的递增事务ID（zxid）
- zxid是一个64位数字，高32位表示epoch（Leader任期），低32位表示事务计数器
- 所有的更新操作按zxid的顺序被处理

```
zxid结构：
┌─────────────────────┬─────────────────────┐
│   高32位: epoch      │   低32位: counter     │
└─────────────────────┴─────────────────────┘
```

### 3.2 原子性（Atomicity）

更新操作要么在所有服务器上成功，要么在所有服务器上失败，不存在部分成功的情况。

**关键保证**：
- 写操作是原子的：要么完全成功，要么完全失败
- 不存在"写了部分数据"的中间状态
- 通过ZAB协议保证原子性

### 3.3 单一系统镜像（Single System Image）

无论客户端连接到哪个Zookeeper服务器，看到的服务视图都是一致的。

**实现要点**：
- 读请求可以在任意服务器上处理（包括Follower）
- 写请求必须经过Leader处理
- Follower上的数据可能与Leader有短暂的不一致（因为同步延迟）
- 如果需要强一致性读，可以使用`sync()`操作

### 3.4 可靠性（Reliability）

一旦一个更新操作被应用，它将一直保持到另一个客户端覆盖该更新。

**具体含义**：
- 已提交的数据不会丢失，除非被显式覆盖
- 通过持久化到磁盘和复制到多数派服务器来保证
- 事务日志和快照文件双重保障

### 3.5 实时性（Timeliness）

Zookeeper保证在一定的时延范围内，客户端能看到最新的数据。注意Zookeeper不保证绝对的实时性，而是保证最终一致性。

**watch机制的时间线**：
1. 客户端发起读操作并注册watch
2. 数据发生变更
3. 客户端收到watch通知
4. 客户端重新读取最新数据

## 四、Zookeeper的Watcher机制

### 4.1 Watcher原理

Watcher是Zookeeper中实现发布/订阅模式的核心机制。客户端可以在某个ZNode上注册Watcher，当该ZNode发生变化时，Zookeeper会向客户端发送通知。

**Watcher的核心特性**：
- **一次性触发**：Watcher一旦被触发，就会自动失效。如果客户端需要持续监听，必须在收到通知后重新注册
- **异步通知**：Watcher的触发和通知是异步的
- **先通知后数据**：Zookeeper保证先向客户端发送Watcher通知，然后才允许客户端读取到变化后的数据
- **顺序性**：Watcher通知的顺序与数据变更的顺序一致

### 4.2 Watcher的类型

| 类型 | 触发条件 | 说明 |
|------|---------|------|
| NodeCreated | ZNode被创建 | 父节点需要设置watcher |
| NodeDeleted | ZNode被删除 | 需要对该节点设置watcher |
| NodeDataChanged | ZNode数据变化 | 只关注数据，不关注子节点 |
| NodeChildrenChanged | 子节点列表变化 | 只关注子节点增删，不关注子节点数据 |

### 4.3 Watcher的Java API示例

```java
// 创建Zookeeper客户端
ZooKeeper zk = new ZooKeeper("localhost:2181", 3000, null);

// exists()注册watcher - 监听节点创建/删除/数据变更
Stat stat = zk.exists("/config", new Watcher() {
    @Override
    public void process(WatchedEvent event) {
        if (event.getType() == EventType.NodeDataChanged) {
            // 数据变更处理
            System.out.println("配置数据已更新");
        }
    }
});

// getChildren()注册watcher - 监听子节点变更
List<String> children = zk.getChildren("/services", new Watcher() {
    @Override
    public void process(WatchedEvent event) {
        if (event.getType() == EventType.NodeChildrenChanged) {
            // 子节点变更处理
            System.out.println("服务列表发生变化");
        }
    }
});

// getData()注册watcher - 监听数据变更
byte[] data = zk.getData("/config/db", new Watcher() {
    @Override
    public void process(WatchedEvent event) {
        if (event.getType() == EventType.NodeDataChanged) {
            // 数据变更处理
            System.out.println("数据库配置已更新");
        }
    }
}, stat);
```

### 4.4 Watcher的注意事项

1. **一次性触发需要重新注册**：每次收到Watcher通知后，如果需要继续监听，必须再次调用相应的API重新注册。
2. **会话过期后Watcher丢失**：如果客户端与Zookeeper的会话过期，之前注册的所有Watcher都会丢失。重连后需要重新注册。
3. **Watcher与版本的关系**：客户端收到Watcher通知和数据之间有时间差，所以读取到的数据版本可能与触发Watcher的版本不同。

## 五、Zookeeper的ACL权限控制

### 5.1 ACL权限模式

Zookeeper提供了五种权限控制模式：

| 模式 | 说明 |
|------|------|
| world | 默认模式，所有用户都有权限 |
| auth | 已认证的用户 |
| digest | 用户名:密码方式认证 |
| ip | 基于IP地址的认证 |
| super | 超级用户，可以操作任何节点 |

### 5.2 权限类型

| 权限 | 说明 | 对应值 |
|------|------|--------|
| CREATE | 可以创建子节点 | 1 << 0 |
| READ | 可以获取节点数据和子节点列表 | 1 << 1 |
| WRITE | 可以设置节点数据 | 1 << 2 |
| DELETE | 可以删除子节点 | 1 << 3 |
| ADMIN | 可以设置ACL权限 | 1 << 4 |
| ALL | 所有权限 | 31 |

### 5.3 ACL代码示例

```java
// 使用digest模式设置ACL
String auth = "username:password";
zk.addAuthInfo("digest", auth.getBytes());

// 创建带ACL的节点
ACL acl = new ACL(ZooDefs.Perms.ALL, 
    new Id("digest", DigestAuthenticationProvider.generateDigest("user:pass")));
List<ACL> acls = new ArrayList<>();
acls.add(acl);
zk.create("/secure/data", "secret".getBytes(), acls, CreateMode.PERSISTENT);

// 使用IP模式设置ACL
ACL ipAcl = new ACL(ZooDefs.Perms.READ, 
    new Id("ip", "192.168.1.0/24"));
acls.add(ipAcl);
```

## 六、Zookeeper的Session机制

### 6.1 会话的生命周期

Zookeeper客户端与服务器之间的连接是通过会话（Session）来维护的。

**会话状态转换**：

```
CONNECTING -> CONNECTED -> CLOSED
     |            |
     +----> EXPIRED
```

### 6.2 会话超时时间

- 客户端在创建连接时可以指定`sessionTimeout`（单位：毫秒）
- 服务器会根据自身配置调整实际超时时间（通常在 `tickTime * 2` 到 `tickTime * 20` 之间）
- 如果客户端在此时间内没有向服务器发送心跳（ping），会话将被判定为过期

### 6.3 会话管理要点

1. **心跳机制**：客户端在 `sessionTimeout/3` 的时间内没有发送请求，会自动发送PING包
2. **会话迁移**：当客户端连接的服务器故障时，会话可以迁移到其他服务器（要求在新服务器上会话未过期）
3. **会话ID**：每个会话都有一个全局唯一的ID，由Leader统一分配

## 七、Zookeeper的版本控制

### 7.1 三种版本号

| 版本号 | 说明 | 作用 |
|--------|------|------|
| version | 数据版本号 | 每次setData操作递增 |
| cversion | 子节点版本号 | 每次子节点增删递增 |
| aversion | ACL版本号 | 每次ACL变更递增 |

### 7.2 乐观锁机制

Zookeeper使用版本号实现乐观锁：

```java
// 读取当前版本
Stat stat = new Stat();
byte[] data = zk.getData("/config", false, stat);
int currentVersion = stat.getVersion();

// 基于当前版本号写入（如果版本号不匹配则写入失败）
try {
    zk.setData("/config", newData.getBytes(), currentVersion);
} catch (BadVersionException e) {
    // 版本号不匹配，说明有其他客户端修改过数据
    // 需要重新读取、修改、再写入
}
```

### 7.3 版本号的使用场景

- **CAS操作**：compare-and-set，确保数据未被他人修改
- **配置更新**：确保配置变更的安全性和一致性
- **分布式锁**：基于版本号的锁实现

## 八、Zookeeper的内存数据模型

### 8.1 DataTree

Zookeeper在内存中维护了一个`DataTree`结构来管理所有的ZNode数据。

**DataTree的核心组件**：
- `nodes: ConcurrentHashMap<String, DataNode>` — 存储所有ZNode
- `dataWatches: WatchManager` — 数据变更的Watcher管理器
- `childWatches: WatchManager` — 子节点变更的Watcher管理器
- `ephemerals: Map<Long, HashSet<String>>` — 会话ID到临时节点的映射

### 8.2 DataNode

每个ZNode在内存中对应一个DataNode对象：

```java
public class DataNode {
    byte[] data;           // 节点数据
    Long acl;              // ACL标识
    StatPersisted stat;    // 持久化的状态信息
    Set<String> children;  // 子节点集合
}
```

### 8.3 数据存储的层级结构

```
DataTree
  ├── DataNode("/")
  │   ├── DataNode("/app1")
  │   │   ├── DataNode("/app1/config")
  │   │   └── DataNode("/app1/workers")
  │   └── DataNode("/zookeeper")
  │       └── DataNode("/zookeeper/config")
  └── WatchManager
```

## 九、总结

Zookeeper通过简洁的数据模型（类文件系统的树形结构）和四种节点类型（持久/持久顺序/临时/临时顺序），为分布式系统提供了强大的协调能力。其核心特性包括顺序一致性、原子性、单一系统镜像、可靠性和实时性，配合Watcher机制、ACL权限控制和Session管理，使得Zookeeper成为分布式系统中不可或缺的基础设施。

理解Zookeeper的节点类型和核心特性是后续学习其应用场景（配置管理、服务发现、分布式锁、Leader选举等）以及深入理解ZAB协议和Leader选举机制的基石。
