---
title: "ZooKeeper 核心特性、节点类型与经典应用场景"
date: 2022-06-16
categories: distributed
tags: [ZooKeeper, ZNode, Watcher, ACL, 选举, 集群, 分布式协调]
mermaid: true
---

> ZooKeeper = 文件系统 + 监听机制。这个简单的公式涵盖了 ZK 的全部核心价值。从节点分类到 Watch 机制，从 ACL 到集群角色，从分布式锁到配置中心——本文从源码级别带你深入理解 ZK 的完整能力。

## 一、ZooKeeper 本质

ZooKeeper 是一个开源的分布式协调框架，是 Apache Hadoop 的子项目，主要解决分布式集群中应用系统的**一致性**问题。

> **ZooKeeper = 文件系统 + 监听机制**

它提供基于文件系统目录树方式的数据存储，并可以对树中的节点进行有效管理，维护和监控数据状态变化。

**核心架构**（来自 `DataTree` 源码）：

```java
public class DataTree {
    // 内存存储：路径 → ZNode 的映射
    private final ConcurrentHashMap<String, DataNode> nodes =
        new ConcurrentHashMap<String, DataNode>();

    // 数据监听器
    private final WatchManager dataWatches = new WatchManager();

    // 子节点监听器
    private final WatchManager childWatches = new WatchManager();
}

public class DataNode implements Record {
    byte data[];                    // 节点数据
    Long acl;                       // 访问控制
    public StatPersisted stat;      // 统计信息
    private Set<String> children = null;  // 子节点列表
}
```

**设计模式**：基于**观察者模式**。ZK 存储数据 → 接受观察者注册 → 数据变化时通知观察者。

---

## 二、ZNode 节点详解

### 2.1 数据模型

ZK 的数据模型与 Unix 文件系统类似，整体是一棵树：

```
/
├── /servers
│   ├── /servers/host1
│   └── /servers/host2
├── /config
│   └── /config/db
└── /locks
    └── /locks/order_lock
```

**关键特性**：
- 每个 ZNode 最大存储 **1MB** 数据
- 每个 ZNode 有唯一的路径标识
- 每个节点有版本号（version），从 0 开始计数
- 每次变更产生唯一事务 ID（zxid），全局递增，用于确定操作先后顺序

### 2.2 六种节点类型

> 这六种节点类型是 ZK 经典应用场景（分布式锁、配置中心、注册中心）的实现基石。

| 类型 | 命令 | 生命周期 | 应用 |
|------|------|---------|------|
| **持久节点** | `create /path` | 一直存在，即使创建者会话关闭 | 配置存储 |
| **临时节点** | `create -e /path` | 创建者会话关闭时删除 | 服务注册、分布式锁 |
| **持久有序节点** | `create -s /path` | 持久 + 名称带递增序号 | ID 生成器 |
| **临时有序节点** | `create -e -s /path` | 临时 + 名称带递增序号 | 公平锁、Leader 选举 |
| **容器节点**(3.5.3+) | `create -c /path` | 子节点全删后，容器被自动删除 | 锁管理 |
| **TTL 节点**(3.5.3+) | `create -t 3000 /path` | TTL 内无修改且无子节点则过期删除 | 临时数据 |

**临时有序节点**最重要，演示一下：

```bash
create -e -s /jobs/job  # 返回 /jobs/job0000000001
create -e -s /jobs/job  # 返回 /jobs/job0000000002
create -e -s /jobs/job  # 返回 /jobs/job0000000003
```

> 10 位数字后缀 + 会话关闭自动删除 = 天生的分布式公平锁实现。

### 2.3 节点状态信息（stat）

| 字段 | 含义 |
|------|------|
| `cZxid` | 创建该节点的事务 ID |
| `ctime` | 创建时间戳 |
| `mZxid` | 最后修改的事务 ID |
| `mtime` | 最后修改时间戳 |
| `pZxid` | 子节点列表最后修改的事务 ID（**增删子节点才变**，修改子节点内容不算） |
| `cversion` | 子节点版本号 |
| `dataVersion` | 数据版本号，每 `set` 一次 +1 |
| `ephemeralOwner` | 绑定的会话 ID（0 表示非临时节点） |
| `dataLength` | 数据长度 |
| `numChildren` | 直接子节点数量 |

### 2.4 客户端命令行操作

```bash
help                              # 查看所有命令
ls [-s] [-w] [-R] path            # 查看子节点，-w 监听，-R 递归
create [-s] [-e] [-c] path [data] # 创建节点
get [-s] [-w] path                # 获取节点数据
set [-v version] path data        # 设置节点数据（可带版本号做乐观锁）
delete [-v version] path          # 删除单个节点
deleteall path                    # 递归删除
stat [-w] path                    # 查看状态
```

**条件更新（乐观锁）**：

```bash
# 基于版本号的条件更新
set -v 1 /counter 2   # 只有 version=1 时才执行，防止并发覆盖
```

---

## 三、Watch 监听机制

Watch 是 ZK 最核心的能力。**必须客户端先注册监听，事件触发后才通知**。

### 3.1 事件类型

| 事件 | 含义 |
|------|------|
| `None` | 连接建立事件 |
| `NodeCreated` | 节点被创建 |
| `NodeDeleted` | 节点被删除 |
| `NodeDataChanged` | 节点数据被修改 |
| `NodeChildrenChanged` | 子节点列表变化（增删子节点） |

### 3.2 Watch 的四个特性

| 特性 | 说明 |
|------|------|
| **一次性触发** | watch 触发后即失效，**需要重新注册**（3.6.0 后可设永久 Watch） |
| **客户端顺序回调** | 回调串行执行，一个 watcher 逻辑不应太重 |
| **轻量级** | WatchEvent 只有状态、事件类型、节点路径，**不包含变更内容** |
| **时效性** | 在 session 有效期内快速重连，watcher 依然保留 |

### 3.3 注册方式

```bash
get -w /path      # 监听节点数据变化
stat -w /path     # 监听节点数据变化（不同命令，相同效果）
ls -w /path       # 监听子节点增减变化
```

### 3.4 永久 Watch（3.6.0+）

```bash
addWatch /path                         # PERSISTENT_RECURSIVE 模式
addWatch -m PERSISTENT /path           # 仅监听节点自身 + 子节点增删
```

- **PERSISTENT**：监听节点的修改/删除 + 子节点的增删
- **PERSISTENT_RECURSIVE**（默认）：在 PERSISTENT 基础上 + 子节点的修改 + 孙节点的变化（递归）

---

## 四、ACL 权限控制

生产环境必须配置 ACL。格式：`[scheme:id:permissions]`

### 4.1 权限模式（scheme）

| 模式 | 说明 |
|------|------|
| **world** | 默认模式，授权对象 `anyone`，所有客户端可操作 |
| **ip** | 基于 IP 地址认证 |
| **auth** | 基于已添加认证的用户 |
| **digest** | 基于 `用户名:密码` 的加密认证 |
| **super** | 超级管理员，需在启动参数中配置 |

### 4.2 权限类型

| 权限 | 缩写 | 含义 |
|------|------|------|
| **CREATE** | c | 创建子节点 |
| **DELETE** | d | 删除子节点 |
| **READ** | r | 读取节点数据、查看子节点列表 |
| **WRITE** | w | 设置节点数据 |
| **ADMIN** | a | 设置 ACL 权限 |

### 4.3 auth 模式实战

```bash
addauth digest fox:123456
setAcl /name auth:fox:123456:cdrwa
```

### 4.4 digest 模式实战

```bash
# 1. 生成加密密码
echo -n fox:123456 | openssl dgst -binary -sha1 | openssl base64
# 输出: ZsWwgmtnTnx1usRF1voHFJAYGQU=

# 2. 设置权限
setAcl /name digest:fox:ZsWwgmtnTnx1usRF1voHFJAYGQU=:cdrwa

# 3. 其他客户端访问前需先认证
addauth digest fox:123456
```

### 4.5 IP 模式

```bash
setAcl /node-ip ip:192.168.109.128:cdwra
create /node-ip data ip:192.168.109.128:cdwra
```

### 4.6 Super 超级管理员

```bash
# 启动参数
-Dzookeeper.DigestAuthenticationProvider.superDigest=admin:<base64(SHA1(123456))>
```

### 4.7 可插拔认证

```java
public interface AuthenticationProvider {
    String getScheme();                    // 标识插件
    KeeperException.Code handleAuthentication(ServerCnxn cnxn, byte authData[]);
    boolean isValid(String id);            // 验证 ID 格式
    boolean matches(String id, String aclExpr);  // 匹配 ACL
    boolean isAuthenticated();             // 是否已认证
}
```

---

## 五、集群架构

### 5.1 三种角色

| 角色 | 职责 | 读写 | 投票 |
|------|------|------|------|
| **Leader** | 事务请求的唯一调度和处理者，保证集群事务顺序性 | 读+写 | ✅ |
| **Follower** | 处理非事务请求，转发事务请求给 Leader，参与投票 | 只读 | ✅ |
| **Observer** | 处理非事务请求，不参与投票（只同步数据） | 只读 | ❌ |

**Observer 的应用**：
1. **提升读性能**：添加 Observer 不影响写入性能
2. **跨数据中心**：北京部署 Leader+ Follower，香港部署 Observer——香港读延迟低，同时不参与投票避免跨地域网络延迟

### 5.2 三节点集群搭建

```bash
# zoo.cfg 配置
dataDir=/data/zookeeper
server.1=192.168.65.163:2888:3888
server.2=192.168.65.184:2888:3888
server.3=192.168.65.186:2888:3888

# 在每个节点的 dataDir 下创建 myid 文件
echo 1 > /data/zookeeper/myid      # 节点1
echo 2 > /data/zookeeper/myid      # 节点2
echo 3 > /data/zookeeper/myid      # 节点3

# 依次启动
bin/zkServer.sh start
```

**server.A=B:C:D 含义**：
- A：服务器 ID（对应 myid）
- B：IP 地址
- C：Follower 与 Leader 交换信息的端口
- D：选举通信端口

### 5.3 四字命令

```bash
yum install nc
echo ruok | nc 192.168.65.186 2181    # 服务是否正常 → "imok"
echo stat | nc 192.168.65.186 2181    # 当前状态
echo mntr | nc 192.168.65.186 2181    # 健康检查指标
echo cons | nc 192.168.65.186 2181    # 所有客户端连接详情
```

开启四字命令：
```bash
# zoo.cfg
4lw.commands.whitelist=*
```

---

## 六、Leader 选举原理（启动期）

### 6.1 投票对比规则（源码级）

```java
protected boolean totalOrderPredicate(
    long newId, long newZxid, long newEpoch,
    long curId, long curZxid, long curEpoch) {

    return ((newEpoch > curEpoch)
            || ((newEpoch == curEpoch)
                && ((newZxid > curZxid)
                    || ((newZxid == curZxid)
                        && (newId > curId)))));
}
```

**优先级**：epoch > zxid > myid

| 优先级 | 字段 | 含义 |
|--------|------|------|
| 1 | **epoch** | 选举轮次，每次重新选举 +1 |
| 2 | **zxid** | 最后提交的事务 ID，数据越新越优先 |
| 3 | **myid** | 服务器 ID，最后兜底 |

### 6.2 zxid 数据结构

```java
public class ZxidUtils {
    public static long getEpochFromZxid(long zxid) {
        return zxid >> 32L;          // 高 32 位：epoch
    }
    public static long getCounterFromZxid(long zxid) {
        return zxid & 0xffffffffL;   // 低 32 位：事务计数器
    }
    public static long makeZxid(long epoch, long counter) {
        return (epoch << 32L) | (counter & 0xffffffffL);
    }
}
```

> zxid 是一个 64 位整数：高 32 位是 epoch（选举轮次），低 32 位是 counter（事务递增计数器）。

---

## 七、经典应用场景

### 7.1 分布式锁

**非公平锁**：`create -e /lock`。所有人试图创建同一个临时节点，成功的获得锁，失败的监听 `/lock` 等待删除通知。

**公平锁**：`create -e -s /lock/seq-`。所有人创建临时有序节点，序号最小的获得锁，其他监听前一个节点的删除事件。

### 7.2 注册中心 / 配置中心

```
/config
  └── /config/db_url = "jdbc:mysql://..."
  └── /config/redis_url = "redis://..."
```

- **推拉结合**：数据变更时 ZK 推送 Watcher 事件 → 客户端收到通知后主动拉取最新数据
- 适合**数据量小的 KV 配置**

### 7.3 Master-Worker 架构

```bash
# master1
create -e /master "m1:2223"        # 成功 → 成为 master

# master2
create -e /master "m2:2223"        # Node already exists → 备用
stat -w /master                     # 监听 master 节点，等待接管
```

**master 监控 worker**：

```bash
# master
create /workers
ls -w /workers                     # 监听 worker 子节点变化

# worker1
create -e /workers/w1 "w1:2224"    # 上线 → master 收到通知
```

### 7.4 统一命名服务 / ID 生成器

```
/order
  └── /order/order-date1-000000000000001
  └── /order/order-date1-000000000000002
  └── /order/order-date2-000000000000003
```

利用**持久有序节点**的特性，生成全局唯一且有顺序的分布式 ID。

---

## 八、总结

| 维度 | 核心要点 |
|------|---------|
| 本质 | 文件系统 + 监听机制，基于观察者模式 |
| 节点 | 6 种：持久/临时/持久顺序/临时顺序/容器/TTL |
| Watch | 一次性触发、串行回调、轻量级、不包含变更内容 |
| ACL | scheme:id:permissions（world/ip/auth/digest/super） |
| 集群 | Leader(读写+投票) / Follower(只读+投票) / Observer(只读) |
| 选举 | epoch > zxid > myid，源码在 totalOrderPredicate |
| 场景 | 分布式锁、配置中心、注册中心、命名服务、Master-Worker |

> ZK 不是数据库，它是存储和协调**关键数据**的中枢。设计时要控制数据量（每个 ZNode ≤ 1MB），让 ZK 做好它最擅长的事——协调。
