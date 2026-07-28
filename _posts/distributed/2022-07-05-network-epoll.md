---
layout: post
title: "深入Linux内核理解epoll：select/poll/epoll三剑客全面对比"
date: 2022-07-05
categories: [distributed]
tags: [epoll, select, poll, IO多路复用, Linux内核, 文件描述符, 网络编程]
comments: true
---

> epoll 是 Linux 2.6 内核提出的 select/poll 增强版本。select/epoll 的优势不在于单个连接更快，而在于能处理更多连接。

---

## 一、同步/异步、阻塞/非阻塞

| 概念 | 定义 | 通俗理解 |
|------|------|----------|
| **同步** | 调用方主动等待结果返回 | 你主动去问老板"衣服到了吗" |
| **异步** | 通过回调/通知获取结果 | 老板打电话通知你"衣服到了" |
| **阻塞** | 结果返回前线程被挂起 | 傻站着等，什么也不做 |
| **非阻塞** | 结果返回前线程可做其他事 | 等的时候可以看手机/喝茶 |

**四种组合**：

| 模式 | 场景 |
|------|------|
| **同步阻塞** | BIO编程（最常见） |
| **同步非阻塞** | 轮询模式（select/poll/epoll） |
| **异步阻塞** | 不常用（Future.get()模式） |
| **异步非阻塞** | AIO回调模式 |

---

## 二、Linux 五种 I/O 模型

1. **阻塞 I/O** → JDK BIO
2. **非阻塞 I/O** → 轮询模式（不推荐，费 CPU）
3. **I/O 复用** → JDK NIO（select/poll/epoll）
4. **信号驱动 I/O** → 使用不广
5. **异步 I/O** → Linux AIO（伪异步，不成熟）

> 阻塞 I/O = BIO，I/O 复用 = NIO。信号驱动和异步 I/O 使用较少。

---

## 三、Linux 内核网络结构

```
应用层 Socket (bind/connect/send/recv)
    ↑↓
协议层 (TCP/UDP → IP)
    ↑↓
接口层 (网卡驱动 → 以太网帧)
```

**数据流向**：
- 发送：应用层 → 协议层添加 TCP/UDP/IP 头 → 接口层添加以太网帧 → 网卡发送
- 接收：网卡 FIFO → 协议层剥离各层头部 → Socket → 用户进程

---

## 四、文件描述符（FD）

在 Linux 中**一切皆是文件**。文件描述符是一个非负整数索引，指向内核维护的文件记录表。

```
进程级文件描述符表 → 系统级文件描述符表 → 文件系统 i-node 表
```

---

## 五、select、poll、epoll 详解

### select

```c
int select(int n, fd_set *readfds, fd_set *writefds, 
    fd_set *exceptfds, struct timeval *timeout);
```

| 特点 | 说明 |
|------|------|
| 原理 | 监视 readfds/writefds/exceptfds 三类描述符 |
| 返回 | 有就绪或超时时返回 |
| 获取结果 | **遍历 fdset** 找到就绪的描述符 |

### poll

```c
int poll(struct pollfd *fds, unsigned int nfds, int timeout);
```

| 特点 | 说明 |
|------|------|
| 原理 | 用 pollfd 指针替代 3 个 fdset |
| 优势 | **没有最大数量限制**（select 默认 1024） |
| 获取结果 | 仍需**轮询 pollfd** 找就绪 |

### epoll（主角）

```c
int epoll_create(int size);    // 创建 epoll 句柄
int epoll_ctl(int epfd, int op, int fd, struct epoll_event *event);  // 增删改监听
int epoll_wait(int epfd, struct epoll_event *events, int maxevents, int timeout); // 等待事件
```

**对应 JDK NIO**：

| epoll | JDK NIO |
|-------|---------|
| `epoll_create` | `Selector.open()` |
| `epoll_ctl(ADD/MOD/DEL)` | `socketChannel.register()` |
| `epoll_wait` | `selector.select()` |

---

## 六、select/poll/epoll 三大对比

### 1、最大连接数

| select | poll | epoll |
|--------|------|-------|
| 32位: 1024 | 无限制（链表） | 无限制（红黑树） |
| 64位: 2048 | | 上限是系统最大文件句柄数 |

### 2、效率

| select | poll | epoll |
|--------|------|-------|
| O(N) 轮询 | O(N) 轮询 | **O(1)** 事件驱动 |
| FD越多越慢 | FD越多越慢 | FD多少不影响效率 |

> epoll 使用**回调机制**，只有活跃的 FD 才调用 callback，不像 select/poll 扫描所有 FD。

### 3、消息传递方式

| select | poll | epoll |
|--------|------|-------|
| 内核→用户：复制整个 fd 集合 | 同 select | 内核→用户：**只复制活跃的事件** |

### epoll 高效原理总结

```
epoll 通过三个核心设计实现高性能：

1. mmap 内存映射 → 减少内核与用户空间数据拷贝
2. 红黑树存储 fd → 增删改 O(logN)（select 每次重置整个集合）
3. 就绪链表 + 回调 → 只处理活跃连接，O(1) 获取事件
```

---

## 七、epoll 工作模式

| 模式 | 触发方式 | 特点 |
|------|----------|------|
| **LT**（水平触发，默认） | 只要缓冲区有数据就通知 | 安全，不会丢事件 |
| **ET**（边缘触发） | 只有新数据到达才通知 | 高效，需配合非阻塞 + 循环读取 |

---

## 八、总结

```
select  → 固定1024限制, O(N)轮询, 小规模可用
poll    → 无限制, O(N)轮询, 中等规模
epoll   → 无限制, O(1)事件驱动, 大规模必选！

epoll = mmap + 红黑树 + 就绪链表 + 回调
  → Linux下高性能网络编程的基础
  → Redis / Nginx / Netty 底层都基于 epoll
```
