---
title: 计算机基础知识
description:
author: hsc
date: 2026-05-25 17:27:00 +0800
categories: [软考, 架构师]
tags: [排版]
# pin: true
# math: true
# mermaid: true
# image:
#   path: /assets/img/posts/devices-mockup.png
#   lqip: data:image/webp;base64,UklGRpoAAABXRUJQVlA4WAoAAAAQAAAADwAABwAAQUxQSDIAAAARL0AmbZurmr57yyIiqE8oiG0bejIYEQTgqiDA9vqnsUSI6H+oAERp2HZ65qP/VIAWAFZQOCBCAAAA8AEAnQEqEAAIAAVAfCWkAALp8sF8rgRgAP7o9FDvMCkMde9PK7euH5M1m6VWoDXf2FkP3BqV0ZYbO6NA/VFIAAAA
#   alt: Chirpy 主题在多种设备上的响应式渲染效果。
---

## 计算机系统概述

计算机系统（Computer System）指的是用于数据管理的计算机硬件、软件以及网络组成的系统。它是按人的要求接收和存储信息，自动进行数据处理和计算，并输出结果信息的机器系统。

程序计数器 vs 指令寄存器  

### 计算机体系结构

冯·诺依曼计算机结构将计算机硬件划分为五大基本部件：运算器、控制器、存储器、输入设备和输出设备。

但在现实的硬件构成中，控制单元（控制器）和运算单元（运算器）被集成为一体，封装为通常意义上的处理器（但处理器并不是只有控制单元和运算单元）；输入设备和输出设备则经常被设计者集成为一体，按照传输过程被划分为总线、接口和外部设备。
![冯·诺依曼计算机结构](/assets/img/posts/senior-system-architect/Von-Neumann-compute-architecture.png)_冯·诺依曼计算机结构_
