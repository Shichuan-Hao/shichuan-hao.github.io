---
title: "深入理解 Redis 线程模型与指令原子性"
date: 2022-06-07
categories: distributed
tags: [Redis, 线程模型, 单线程, 多线程, Pipeline, Lua, Function, 事务]
mermaid: true
---

> "Redis 到底是单线程还是多线程？" 这道面试题几乎伴随了 Redis 的整个发展史。答案远比"客户端多线程，服务端单线程"丰富得多——涉及 IO 多线程、指令原子性保证、Lua/Functions 的取舍和企业级实践经验。

## 一、Redis 到底是什么？

Redis 全称 **REmote DIctionary Server**（远程字典服务），是完全开源的高性能 Key-Value 数据库。

2024 年的 Redis 早已超越了"缓存"的范畴。官方定位已扩展为三大方向：**Cache（缓存）、Database（数据库）、Vector Search（向量搜索）**。Redis Cloud 作为云服务，基于 AWS/Azure 提供企业级服务（含 Redis Enterprise 收费产品）。Redis Insight 是官方图形化客户端，可以直接在 Cloud 上使用。

在功能层面形成了 **Redis OSS**（经典开源）和 **Redis Stack**（完整技术栈）两套服务体系：

```
Redis Stack  =  Redis OSS  +  高级扩展功能
     ↓                           ↓
  Redis Cloud 云服务         Redis Insight 客户端
```

---

## 二、"Redis 到底是单线程还是多线程？"

### 2.1 整体结论

**客户端多线程，服务端以单线程为主。**

- Redis 使用多线程维护与客户端的 Socket 连接（`maxclients` 默认 10000）
- 服务端**响应网络 IO 和键值对读写**由一个主线程完成
- 基于 **epoll IO 多路复用**，单线程同时响应多个客户端请求

在这种模型下，所有客户端的并发请求被**串行化**执行。这意味着：
- 不需要考虑 MySQL 中脏读、幻读、不可重复读之类的并发问题
- 极致的串行 + 内存操作形成了 Redis 极高性能的基础
- Redis 也因此成为**并发问题的解决工具**（分布锁、计数器）

### 2.2 版本演进

| 版本 | 线程模型 | 说明 |
|------|---------|------|
| Redis 4.x 及之前 | **纯单线程** | 真正的单线程处理所有请求 |
| Redis 5.x (2018.10) | 大幅重构 | 核心代码重构，为多线程做准备 |
| Redis 6.x ~ 7.x | **核心单线程 + 异步多线程** | 持久化 RDB/AOF、unlink 异步删除、集群数据同步等由额外线程执行 |

Redis 官方配置中对 IO 多线程的说明（来自 `redis.conf`）：

```
# Redis is mostly single threaded, however there are certain threaded
# operations such as UNLINK, slow I/O accesses and other things that are
# performed on side threads.
#
# Now it is also possible to handle Redis clients socket reads and writes
# in different I/O threads. Using I/O threads it is possible to easily
# speedup two times Redis without resorting to pipelining nor sharding.
#
# By default threading is disabled, we suggest enabling it only in machines
# that have at least 4 or more cores, leaving at least one spare core.
# Using more than 8 threads is unlikely to help much.
```

**IO 多线程使用建议**：

| 核心数 | 建议 IO 线程数 |
|--------|-------------|
| 4 核 | 2~3 个 |
| 8 核 | 6 个 |

> Redis 保持核心线程单线程，因为 **CPU 通常不是 Redis 的性能瓶颈**，内存和网络才是。改多线程会增加资源竞争和业务复杂性，反而可能降低执行效率。Redis 对多线程的采纳非常谨慎。

### 2.3 相关配置

```bash
# IO 线程数（默认关闭）
io-threads 4

# IO 线程读取也异步
io-threads-do-reads yes

# 最大客户端连接数
maxclients 10000
```

---

## 三、Redis 如何保证指令原子性

核心线程单线程保证单条指令的原子性没问题，但**多个指令组合在一起时**不保证原子性。下面这几种场景就需要不同策略。

### 3.1 复合指令（推荐优先使用）

Redis 内置了许多"一条指令干多个活"的复合指令，天然保证原子性：

| 复合指令 | 原子操作 |
|---------|---------|
| `MSET/HMSET` | 原子批量设置 |
| `GETSET` | 先 GET 再 SET |
| `SETNX` | SET if Not eXists |
| `SETEX` | SET with EXpiration |
| `INCR`/`DECR` | 原子增减 |
| `HMGET` | 原子批量获取 |

如果能用复合指令解决，就不需要用事务。

### 3.2 Redis 事务

```bash
127.0.0.1:6379> help @transactions

  MULTI         -- 开启事务
  EXEC          -- 执行事务（提交）
  DISCARD       -- 放弃事务（回滚）
  WATCH key...  -- 监听某个 key，若被修改则事务不执行
  UNWATCH       -- 取消监听
```

基本用法：

```bash
127.0.0.1:6379> MULTI
OK
127.0.0.1:6379(TX)> set k2 2
QUEUED
127.0.0.1:6379(TX)> incr k2
QUEUED
127.0.0.1:6379(TX)> get k2
QUEUED
127.0.0.1:6379(TX)> EXEC
1) OK
2) (integer) 3
3) "3"
```

#### ⚠️ Redis 事务 ≠ 数据库事务

这是一个**致命误区**。看下面这个例子：

```bash
127.0.0.1:6379> MULTI
127.0.0.1:6379(TX)> set k2 2
127.0.0.1:6379(TX)> incr k2
127.0.0.1:6379(TX)> get k2
127.0.0.1:6379(TX)> lpop k2         # ← k2 是 string，lpop 操作 list
127.0.0.1:6379(TX)> incr k2
127.0.0.1:6379(TX)> get k2
127.0.0.1:6379(TX)> exec
1) OK
2) (integer) 3
3) "3"
4) (error) WRONGTYPE Operation against a key holding the wrong kind of value
5) (integer) 4          # ← 即使第4条报错，第5条依然执行！
6) "4"
```

**Redis 事务的真正作用**：仅保证事务中的操作**一起执行，不被其他客户端指令加塞**，而不是保证一起成功或一起失败。

> 开启事务后所有操作返回 `QUEUED`，表示只是排好了队等到 `EXEC` 后一起执行。中间别的客户端的指令进不来，这就是"不被打断"的原子性。

#### WATCH 机制

```bash
127.0.0.1:6379> WATCH mykey
OK
127.0.0.1:6379> MULTI
127.0.0.1:6379(TX)> set mykey newvalue
QUEUED
# 此时另一个客户端修改了 mykey...
127.0.0.1:6379(TX)> EXEC
(nil)    # ← 事务未执行，因为 mykey 被修改了
```

WATCH 是乐观锁机制。`UNWATCH` 只能在**当前客户端**生效。

#### 事务失败与 AOF

**事务失败怎么回滚？**

| 失败时机 | 行为 |
|---------|------|
| EXEC 执行**前**失败（指令敲错、参数不对） | **整个事务不执行**（回滚操作，不是回滚数据） |
| EXEC 执行**后**失败（key 类型不对） | **其他操作不受影响**，错误操作被跳过 |

**事务不完整导致启动失败**：

Redis 执行 `EXEC` 后，会先将事务中**所有操作记录到 AOF 文件**，再执行具体操作。如果 AOF 记录写入后、操作执行过程中服务非正常宕机（`kill -9`），可能导致 AOF 记录与数据不一致。此时 Redis 启动报错，需用 `redis-check-aof --fix` 修复。

### 3.3 Pipeline

#### 什么是 Pipeline？

```bash
$ redis-cli --help
  --pipe             Transfer raw Redis protocol from stdin to server.
  --pipe-timeout <n> In --pipe mode, abort with error if after sending all data
                     no reply is received within <n> seconds.
```

#### 使用案例

Linux 上编辑 `command.txt`：

```
set count 1
incr count
incr count
incr count
```

执行：

```bash
$ cat command.txt | redis-cli -a 123qweasd --pipe
All data transferred. Waiting for the last reply...
Last reply received from server.
errors: 0, replies: 4

$ redis-cli -a 123qweasd
127.0.0.1:6379> get count
"4"
```

#### Pipeline 解决了什么？RTT 优化

当客户端执行一个指令时，数据包从 Client → Server → Client，这个时间消耗称为 **RTT（Round-Trip Time）**。指令越频繁，RTT 消耗越大。

```
无 Pipeline:   Client ---[cmd1]---> Server (RTT1)
               Client <--[res1]--- Server
               Client ---[cmd2]---> Server (RTT2)
               Client <--[res2]--- Server
               ...（N 条指令 = N 次 RTT）

Pipeline:      Client ---[cmd1][cmd2][cmd3]---> Server (1 次 RTT)
               Client <--[res1][res2][res3]--- Server
```

官网案例（用 `nc` 直接发送 RESP 协议）：

```bash
$ printf "AUTH 123qweasd\r\nPING\r\nPING\r\nPING\r\n" | nc localhost 6379
+OK
+PONG
+PONG
+PONG
```

#### Pipeline vs 事务 vs 复合指令

| 特性 | 复合指令 | 事务 | Pipeline |
|------|---------|------|----------|
| **原子性** | ✅ 原子 | ✅ 原子 | ❌ 非原子（可能被其他指令加塞） |
| **命令类型** | 必须相同 | 可混合 | 可混合 |
| **阻塞** | 阻塞 Redis | 阻塞 Redis | **不阻塞 Redis**（阻塞当前客户端） |
| **支持** | 服务端 | 服务端 | 需要客户端+服务端同时支持 |

#### Pipeline 注意事项

- Pipeline 在执行过程中**阻塞当前客户端**（不是 Redis）
- 不要拼装过多指令，否则客户端阻塞时间过长，服务端内存占用也大
- 适合**非热点时段的数据调整任务**，不适合高强度在线业务
- Pipeline 不具备原子性，不适合需要严格原子性的场景

### 3.4 Lua 脚本

Redis 事务和 Pipeline 对指令原子性问题都有水土不服的地方，且都只能拼凑已有指令，无法添加自定义逻辑。**Lua 脚本是企业中使用最多的方案**。

#### 为什么是 Lua？

Lua 是一种小巧的脚本语言，其最大特点是**单线程模型**──天生适合 Nginx、Redis 这类单线程中间件进行功能定制。在 Redis 中执行一段 Lua 脚本，天然就是原子性的。

Redis 7.x 支持的 Lua 版本是 **5.1**。在线调试推荐：https://wiki.luatos.com/（支持 5.3，与 Redis 有差异，注意区别）。

#### 基本用法

```bash
127.0.0.1:6379> help eval

  EVAL script numkeys [key [key ...]] [arg [arg ...]]
  summary: Executes a server-side Lua script.
  since: 2.6.0
```

参数说明：
- `script`：Lua 脚本程序，**不必也不应该定义为 Lua 函数**
- `numkeys`：键名参数个数
- `KEYS[1]...KEYS[N]`：在 Lua 中通过 `KEYS` 数组以 **1 为基址**访问
- `ARGV[1]...ARGV[N]`：通过 `ARGV` 数组以 **1 为基址**访问

```bash
127.0.0.1:6379> eval "return {KEYS[1],KEYS[2],ARGV[1],ARGV[2]}" 2 key1 key2 first second
1) "key1"
2) "key2"
3) "first"
4) "second"
```

#### 实战案例：库存控制

```bash
-- 调整库存：如果库存小于10，就设置为10
127.0.0.1:6379> eval "
  local initcount = redis.call('get', KEYS[1])
  local a = tonumber(initcount)
  local b = tonumber(ARGV[1])
  if a >= b then
    redis.call('set', KEYS[1], a)
    return 1
  end
  redis.call('set', KEYS[1], b)
  return 0
" 1 "stock_1" 10
(integer) 0

127.0.0.1:6379> get stock_1
"10"
```

#### Lua 注意事项

**1. 不要写死循环和耗时运算**

Redis 有 `lua-time-limit`（默认 5000ms）限制脚本最大执行时间。超时后，Redis 对其他请求返回 **BUSY** 错误，而不是一直阻塞：

```bash
# 只允许执行特殊指令
SCRIPT KILL        # 停止未执行写操作的脚本
FUNCTION KILL      # 停止未执行写操作的 Function
SHUTDOWN NOSAVE    # 如果脚本已执行了写操作，只能用这个强制关闭
```

**2. 尽量使用只读脚本**

Redis 7 新增只读脚本机制，通过 `EVAL_RO` 触发。只读脚本可以放心使用 `SCRIPT KILL` 停止，且可以**转移到备份节点执行**，减轻主节点压力。

**3. 热点脚本缓存到服务端**

通过 `SCRIPT LOAD` 加载脚本，获取 SHA1 摘要后用 `EVALSHA` 调用，减少网络传输。

### 3.5 Redis Functions（Redis 7 新增）

如果觉得 Lua 脚本开发有困难，Redis 7 提供了 **Function**──将功能声明为统一函数，**提前加载到 Redis 服务端**，客户端直接调用。

**优势**：Function 中可以**嵌套调用其他 Function**，有利于代码复用（Lua 脚本无法复用）。

#### 示例

创建 `mylib.lua`：

```lua
#!lua name=mylib

local function my_hset(keys, args)
  local hash = keys[1]
  local time = redis.call('TIME')[1]
  return redis.call('HSET', hash, '_last_modified_', time, unpack(args))
end

redis.register_function('my_hset', my_hset)
```

> ⚠️ 第一行 `#!lua name=mylib` 是指定命名空间，不是注释，**不能省略**！

加载到 Redis：

```bash
$ cat mylib.lua | redis-cli -a 123qweasd -x FUNCTION LOAD REPLACE
"mylib"
```

使用：

```bash
127.0.0.1:6379> FUNCTION LIST
1) 1) "library_name"
   2) "mylib"
   3) "engine"
   4) "LUA"
   5) "functions"
   6) 1) 1) "name"
         2) "my_hset"

127.0.0.1:6379> FCALL my_hset 1 myhash myfield "some value" another_field "another value"
(integer) 3

127.0.0.1:6379> HGETALL myhash
1) "_last_modified_"
2) "1717748001"
3) "myfield"
4) "some value"
5) "another_field"
6) "another value"
```

#### Function 注意事项

1. Function 也支持只读调用
2. 集群中使用时，**需要在各节点手动加载**──Redis 不会同步 Function
3. 不建议使用太多太大的 Function（服务端缓存占用）

### 3.6 指令原子性总结

```
简单原子操作  →  复合指令 (MSET/INCR/SETNX...)   最先考虑
    ↓
需要逻辑判断  →  Lua 脚本                         最常用
    ↓
代码复用需求  →  Redis Function (Redis 7+)        服务端缓存
    ↓
批量操作      →  Pipeline (注意非原子性)            非热点时段
    ↓
简单排队      →  事务 (注意不保证一起失败)           较少使用
```

---

## 四、BigKey 的初步发现

BigKey 指占用空间非常大的 key（如 List 含 200W 个元素、String 存一整篇文章）。

Redis 提供了两个参数帮助快速发现 BigKey：

```bash
redis-cli --bigkeys   # 采样查找元素数量最多的 key
redis-cli --memkeys   # 采样查找内存占用最多的 key
```

> BigKey 极易造成 Redis 服务阻塞，详见缓存优化篇的完整解决方案。

---

## 五、线程模型总结

```
┌─────────────────────────────────────────────────┐
│                 Redis 线程架构                     │
├─────────────────────────────────────────────────┤
│  客户端1 ──┐                                     │
│  客户端2 ──┤  多线程 Socket 连接管理                │
│  客户端3 ──┤  (maxclients: 10000)                │
│  客户端N ──┘                                     │
│            │                                     │
│            ▼                                     │
│      epoll 多路复用                                │
│            │                                     │
│            ▼                                     │
│    ┌──────────────────┐                         │
│    │   核心主线程(单线程) │  ← 指令执行              │
│    └──────────────────┘                         │
│            │                                     │
│       ┌────┼────┬──────────┐                    │
│       ▼    ▼    ▼          ▼                    │
│     RDB  AOF  unlink   集群同步                   │
│     (子线程) (子线程)  (异步删除)  (后台同步)        │
└─────────────────────────────────────────────────┘
```

**核心认识**：

1. Redis 的核心指令处理依然是单线程，这样避免了资源竞争、线程上下文切换
2. 费时的后台操作（持久化、大 key 删除、集群同步）已多线程化
3. Redis 6+ 加入了 IO 多线程，可提升约 2 倍性能（需 4 核以上才建议开启）
4. 这种简单线程模型使 Redis 成为**解决线程并发问题的工具**
5. 选择合适的指令执行方式（复合指令 → Lua → Functions → Pipeline → 事务）是企业应用的核心技能
