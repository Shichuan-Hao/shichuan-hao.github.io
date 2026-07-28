---
layout: post
title: "一台新机器进行Web页面请求的历程：从DHCP到HTTP完整链路"
date: 2022-07-29
categories: [distributed]
tags: [网络协议, DHCP, DNS, ARP, HTTP, 网络通信, 全链路]
comments: true

---

## 场景

小明组装了一台新电脑，插上网线，开机，打开浏览器输入 `www.baidu.com`，按下回车。

**在这几秒内发生了什么？**

---

## 一、DHCP（获取IP地址）

```
新电脑 → 没有IP地址 → 无法上网
       ↓
    DHCP Discover（广播：谁的DHCP服务器？）
       ↓
    DHCP Offer（路由器的DHCP服务器响应：给你IP 192.168.1.100）
       ↓
    DHCP Request（确认接受）
       ↓
    DHCP ACK（分配成功）
```

**现在电脑有了**：IP地址 + 子网掩码 + 默认网关 + DNS服务器地址

---

## 二、DNS（域名解析）

```
浏览器输入 www.baidu.com
       ↓
查本地 DNS 缓存 → 无
查 hosts 文件 → 无
向 DNS 服务器（192.168.1.1 或 8.8.8.8）发起递归查询
       ↓
DNS 服务器返回：www.baidu.com → 110.242.68.66
```

---

## 三、ARP（获取MAC地址）

```
有了目标 IP → 还需要下一跳的 MAC 地址

查本地 ARP 缓存 → 无
       ↓
ARP 请求（广播：谁有 IP 192.168.1.1 的 MAC？）
       ↓
网关响应（MAC: aa:bb:cc:dd:ee:ff）
```

**ARP 缓存**：收到响应后缓存，下次直接用。

---

## 四、TCP 三次握手

```
浏览器（Client）                 百度服务器（Server）
  192.168.1.100                     110.242.68.66
       │                                  │
       │──── SYN, seq=x ─────────────▶   │  (1)
       │                                  │
       │◀─── SYN+ACK, seq=y, ack=x+1 ───│  (2)
       │                                  │
       │──── ACK, seq=x+1, ack=y+1 ────▶│  (3)
       │                                  │
       └──── 连接建立 ────────────────────┘
```

---

## 五、HTTP 请求-响应

```
浏览器 → 百度服务器：
  GET / HTTP/1.1
  Host: www.baidu.com
  Connection: keep-alive

百度服务器 → 浏览器：
  HTTP/1.1 200 OK
  Content-Type: text/html

  <!DOCTYPE html>
  <html>...</html>
```

---

## 六、浏览器渲染

```
解析 HTML → 构建 DOM 树
解析 CSS → 构建 CSSOM 树
合并 → 构建 Render 树
布局（Layout）→ 计算位置和大小
绘制（Paint）→ 渲染到屏幕
```

---

## 七、全链路时间轴

```
T=0ms:     DHCP 分配IP
T=50ms:    DNS 解析 www.baidu.com
T=52ms:    ARP 获取网关MAC
T=55ms:    TCP 三次握手（RTT~3ms）
T=58ms:    HTTP 请求发送
T=80ms:    HTTP 响应接收
T=200ms:   页面渲染完成

总计约 200ms（局域网 + 高速网络下）
```

---

## 八、总结

```
DHCP → IP地址
DNS  → 域名→IP
ARP  → IP→MAC
TCP  → 可靠连接(三次握手)
HTTP → 请求/响应
Render → 页面展示
```
