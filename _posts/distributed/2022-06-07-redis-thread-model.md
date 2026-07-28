---
layout: post
title: "深入理解Redis线程模型"
date: 2022-06-07
categories: [distributed]
tags: [Redis, 线程模型, 原子性, Lua, 事务, Pipeline]
comments: true
---

## 一、Redis是什么？有什么用？

Redis 全称 **REmote DIctionary Server**（远程字典服务），是一个完全开源的、高性能的 Key-Value 数据库。

**核心总结**：
- **数据结构复杂**：相比于传统 K-V 数据库，Redis 支持更复杂的数据类型，可以支撑很多复杂业务场景
- **数据全在内存，但持久化到硬盘**：读写性能极高，同时数据安全可靠
- **官方定位三个方向**：Cache（缓存）、Database（数据库）、Vector Search（向量搜索）

**2024 年的 Redis 生态**：

Redis 已经从单纯的开源数据库蜕变为一整套生态服务：

| 产品 | 定位 |
|------|------|
| **Redis Cloud** | 基于 AWS/Azure 等公有云的云服务 |
| **Redis Enterprise** | 企业级收费产品，提供更全面高可用保障 |
| **Redis Insight** | 官方图形化客户端，无需第三方客户端 |
| **Redis OSS** | 传统开源服务体系 |
| **Redis Stack** | 基于 OSS 的更完整技术栈，提供 JSON/Search/Bloom 等高级扩展 |

核心配置文件建议：
```
daemonize yes           # 允许后台启动
protected-mode no       # 关闭保护模式
#bind 127.0.0.1         # 注释掉允许远程访问
requirepass 123qweasd   # 建议开启密码
```

---

## 二、Redis到底是单线程还是多线程？

这是 Redis 面试中**最喜欢问的问题**，几乎伴随 Redis 整个发展过程。

### 整体概括：客户端多线程，服务端单线程

- **客户端**：Redis 使用多线程来维护与客户端的 Socket 连接。`maxclients` 参数控制最大客户端连接数（默认 10000）
- **服务端**：响应网络 IO 和键值对读写的请求，由**一个单独的主线程**完成

Redis 基于 **epoll** 实现了 IO 多路复用，用一个主线程同时响应多个客户端的 Socket 连接请求。所有客户端的并发请求被转成**串行执行**，因此完全不用考虑 MySQL 中的脏读、幻读、不可重复读等并发问题。

### 版本演进

```
Redis 4.x 以前：纯单线程

Redis 5.x (2018.10)：核心代码重构

Redis 6.x ~ 7.x：全新多线程机制
  - 持久化 RDB、AOF 文件 → 额外线程
  - unlink 异步删除 → 额外线程
  - 集群数据同步 → 额外线程
  - FLUSHALL → 支持异步方式
  - IO threads 网络读写线程
```

Redis6/Redis7 中关于 IO 多线程的官方配置说明：

```
# io-threads 4
# 默认关闭，建议在至少4核以上机器开启
# 使用8个以上线程不太可能提供更多帮助
# 建议只在确实有性能问题时才开启
# 4核机器：用2-3个IO线程
# 8核机器：用6个IO线程
```

### 为什么核心线程保持单线程？

1. **CPU 通常不是性能瓶颈**：Redis 的性能瓶颈大部分在**内存和网络**
2. **减少线程上下文切换**的性能消耗
3. **避免资源竞争**：改多线程会极大增加 Redis 的业务复杂性

---

## 三、Redis如何保证指令原子性

对于核心的读写键值操作，Redis **单线程串行**处理。多个客户端同时请求时，Redis 只会排队执行。但是针对**单个客户端**的多个操作，Redis 并没有类似 MySQL 的事务机制来保证原子性。

下面从 5 个维度介绍 Redis 的原子性保证方案：

### 1、复合指令（原子操作）

Redis 内部提供了很多**复合指令**，一条指令做多件事：

| 指令 | 说明 |
|------|------|
| `MSET` / `HMSET` | 批量设置，原子性 |
| `GETSET` | 设置新值并返回旧值 |
| `SETNX` | 不存在才设置 |
| `SETEX` | 设置并指定过期时间 |
| `SET key value EX 10 NX` | 原子性设置过期时间和NX条件 |

**特点**：复合指令天然保持原子性，是最简单的原子性保证方式。

### 2、Redis事务

Redis 事务指令：`MULTI` → 添加操作 → `EXEC` / `DISCARD`

**示例**：
```
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

**关键问题：Redis事务 ≠ 数据库事务**

```
127.0.0.1:6379> MULTI
127.0.0.1:6379(TX)> set k2 2
QUEUED
127.0.0.1:6379(TX)> incr k2
QUEUED
127.0.0.1:6379(TX)> lpop k2        # k2是string类型，lpop会报错
QUEUED
127.0.0.1:6379(TX)> incr k2         # 但后面的指令不受影响！
QUEUED
127.0.0.1:6379(TX)> exec
1) OK
2) (integer) 3
3) "3"
4) (error) WRONGTYPE Operation against a key holding the wrong kind of value
5) (integer) 4    # ← 仍然执行了！
```

**核心结论**：
- Redis 事务仅保证事务中的操作**一起执行**，不会在中间被其他指令加塞
- 所有操作在 `MULTI` 后返回 `QUEUED`，表示排队，等 `EXEC` 后一起执行
- 执行过程中某条指令出错，**不回滚**，其他指令照常执行

**WATCH 机制**：

`WATCH key` 可以监听某个 key 的变化，在事务执行前检查 key 是否被修改。如果被修改，事务执行失败。

**事务回滚逻辑**：
1. **EXEC 执行前失败**（指令敲错/参数不对）→ 整个事务操作都不会执行
2. **EXEC 执行后失败**（key 类型不对）→ 其他操作正常执行，不受影响

**事务与 AOF 的数据一致性问题**：Redis 先将事务操作记录到 AOF 文件再执行具体操作。如果记录 AOF 后、操作执行过程中服务宕机，会导致 AOF 和数据不一致。此时需要用 `redis-check-aof` 工具修复 AOF 文件。

### 3、Pipeline（管道）

**核心概念**：将客户端多个指令打包，一起推送服务端，优化 **RTT**（Round Trip Time）。

```
# 使用案例
cat command.txt | redis-cli -a 123qweasd --pipe
```

```
[root]# printf "AUTH 123qweasd\r\nPING\r\nPING\r\nPING\r\n" | nc localhost 6379
+OK
+PONG
+PONG
+PONG
```

**Pipeline 注意点**：
- Pipeline **不具备原子性**，可能被其他客户端的指令加塞
- Pipeline 执行期间**阻塞当前客户端**，不建议拼装过多指令
- 适合**非热点时段**的数据调整任务
- 与事务的区别：复合指令和事务是原子性的，Pipeline 不是

### 4、Lua脚本（重点）

**为什么 Redis 支持 Lua？**

Lua 是一种小巧的脚本语言，**单线程模型**使得它天生适合嵌入 Redis、Nginx 等中间件。在 Redis 中执行 Lua 脚本，**天然就是原子性的**。

**基本用法**：
```
EVAL script numkeys [key [key ...]] [arg [arg ...]]
```

```lua
-- 实例：库存调整
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
```

**Lua 注意点**：
1. **不要出现死循环和耗时运算**：默认最长执行时间 5 秒（`lua-time-limit` 配置），超时会返回 BUSY 错误
2. **尽量使用只读脚本**（Redis7 新增 `EVAL_RO` 指令）：只读脚本可以转移到备份节点执行，可以使用 `SCRIPT KILL` 随时停止
3. **热点脚本可以缓存到服务端**：减少网络传输

### 5、Redis Function（Redis7 新增）

**什么是 Function？**

Function 允许将功能声明为统一函数，提前加载到 Redis 服务端，客户端直接调用，无需开发具体实现。更大的好处是可以**嵌套调用**其他 Function，有利于代码复用（Lua 脚本无法复用）。

**使用示例**：

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

加载并使用：
```
[root]# cat mylib.lua | redis-cli -a 123qweasd -x FUNCTION LOAD REPLACE
"mylib"

127.0.0.1:6379> FCALL my_hset 1 myhash myfield "some value" another_field "another value"
(integer) 3
```

**Function 注意点**：
1. 支持只读调用
2. 集群中需要在**各个节点都手动加载**，Redis 不会自动同步 Function
3. Function 在服务端缓存，不建议使用太多太大的 Function

### 6、五种原子性方案对比总结

| 方案 | 原子性 | 灵活性 | 阻塞特性 | 适用场景 |
|------|--------|--------|----------|----------|
| 复合指令 | ✅ 原子 | ❌ 固定组合 | 阻塞其他命令 | 简单原子操作 |
| Redis事务 | ✅ 原子 | ⚠️ 有限 | 阻塞其他命令 | 批量操作需按序执行 |
| Pipeline | ❌ 非原子 | ✅ 任意组合 | 阻塞当前客户端 | 批量数据导入 |
| Lua脚本 | ✅ 原子 | ✅ 编程逻辑 | 阻塞其他命令 | **最常用**，复杂业务逻辑 |
| Function | ✅ 原子 | ✅ 代码复用 | 阻塞其他命令 | 函数复用场景 |

---

## 四、Redis中的Bigkey问题

**Bigkey** 指那些占用空间非常大的 key，基于 Redis 单线程为主的工作机制，非常容易造成**服务阻塞**。

### 如何发现 Bigkey

```bash
redis-cli --bigkeys    # 查找元素较多的 key
redis-cli --memkeys    # 查找内存占用较多的 key
```

### Bigkey 的危害

1. **导致 Redis 阻塞**：删除大 key 时主线程长时间占用
2. **网络拥塞**：Bigkey 每次获取产生较大网络流量
3. **过期删除阻塞**：Bigkey 过期时如果没有开启异步删除（`lazyfree-lazy-expire yes`），会阻塞 Redis

---

## 五、Redis线程模型总结

```
                          ┌─────────────┐
         Socket           │  Redis 主线程 │
Client 1 ──────┐          │               │
               ├─ epoll ──│  单线程串行    │
Client 2 ──────┤          │  处理所有指令   │
               │          │               │
Client n ──────┘          │  (核心操作)    │
                          └───────────────┘
                          │
                    ┌─────┴─────┐
                    │ 后台线程    │
                    │ · RDB备份  │
                    │ · AOF刷盘  │
                    │ · unlink   │
                    │ · 集群同步  │
                    └───────────┘
```

**核心结论**：
- Redis 线程模型整体是**多线程**的，但执行指令的核心线程是**单线程**的
- 这种单线程为主的模型使得 Redis 处理并发问题简单高效，甚至成为**解决分布式并发问题的工具**
- Redis 的应用场景与高性能深度绑定，使用时要时刻思考**指令执行方式**，才能最大限度发挥性能优势

> 有道云笔记链接：[深入理解Redis线程模型](https://note.youdao.com/s/AIoVOBQP)
