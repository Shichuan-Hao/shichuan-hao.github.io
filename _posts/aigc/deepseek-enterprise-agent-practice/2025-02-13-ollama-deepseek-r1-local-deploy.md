---
title: Ollama 本地部署 DeepSeek R1 模型
description: Ollama 本地部署 DeepSeek R1 模型
author: hsc
date: 2025-02-13 12:27:00 +0800
categories: [AI Agent]
tags: [DeepSeek, Ollama, DeepSeek R1]
---

## Ollama 项目介绍

`Ollama` 是在 Github 上的开源项目，其项目定位是：<hl=red>一个本地运行大模型的集成框架</hl>。

目前主要针对主流的 <hl=red>LLaMA</hl> 架构的开源大模型设计，通过将模型权重、配置文件和必要数据封装进由<hl=red>Modelfile</hl>定义的包中，从而实现大模型的下载，启动和本地运行的自动化部署及推流流程。

此外，<hl=red>Ollama</hl> 内置了一系列针对大模型运行和推理的优化策略，目前作为一个非常热门的<color=red>大模型托管平台</color>，基本主流的大模型应用开发框架如 `LangChain`、`AutoGen`、`Microsoft GraphRAG`及热门项目`AnythingLLM`、`OpenWebUI` 等高度集成。

> `Ollama` 通过将大模型运行的所有必要组件（如权重文件、配置设置和相关数据）封装在一个单一的文件或包中，`Modelfile` 允许用户更容易地下载、安装、配置和启动模型。这种方法类似于其它软件或应用程序的安装包，它们将所有必要的文件打包在一起，以便用户可以通过简单的安装过程将软件添加到他们的系统中。<br/>
Ollama 项目地址：[https://github.com/Ollama/ollama](https://github.com/Ollama/ollama) <br/>
Ollama 官方地址：[https://ollama.com/](https://ollama.com/)

![Ollama 官方地址](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502131249751.png)

Ollama 项目支持跨平台部署，目前已兼容 Mac、Linux 和 Windows 操作系统。特别地对 Mac 和 Windows 用户提供了非常直观的预览版，包括内置的 GPU 加速功能、访问完整模型库的能力，以及对 OpenAI 的兼容性在内的 Ollama REST API，对用户使用尤为友好。

但无论使用哪个操作系统，Ollama 项目的安装过程都设计得非常简单。不过根据研发需求以及真实企业得应用需求，还是建议使用 Linux 操作系统进行部署/实践。可以通过[https://github.com/ollama/ollama](https://github.com/ollama/ollama) 依据实际情况进行安装体验。

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/202403081646978.png)

本人是在 Ubuntu 24.04 系统下安装部署 Ollama 项目，因此本文重点总结改版本操作系统得详细步骤。具体来说，Ollama 在 Ubuntu 系统上安装方式由两种，分别是：<hl=red>Olla一键安装和手动安装ma</hl>，但不论使用哪种方法进行安装，都需要安装Ollama项目的服务器上具备网络连通环境，因为不仅涉及Ollama安装包的更新，还会涉及后续大模型的下载。

## Ollama 项目本地安装

Ollama 项目本地安装得方法极为简单，这里以 Ubuntu 24.04 系统为例，先进入命令行终端，执行如下一条命令即可自动化完成：

```bash
 curl -fsSL https://ollama.com/install.sh | sh
```

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502111855169.png)

这行命令的目的是从 [https://ollama.com/install.sh](https://ollama.com/install.sh) 下载安装脚本，并执行安装,，在安装过程中会包含以下几个主要的操作：
1. 检查当前服务器的基础环境，如系统版本等；
2. 下载 Ollama 的二进制文件；
3. 配置系统服务，包括创建用户和用户组，添加 Ollama 的配置信息；
4. 启动 Ollama 服务。
这个过程会比较慢，拉取的文件约 2G 左右，如果安装过程中未出现任何错误信息，通常情况下能够表明安装已经成功。可以通过执行下命令来检查 Ollama 服务的运行状态：

```bash
systemctl status ollama
```

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502111857348.png)

如果 Active 状态显示为 active，则说明 Ollama 服务目前处于正常运行状态。同时还可以通过以下命令查询当前安装的 Ollama 版本信息：

```bash
$ ollama --version
$ sudo ollama -v
```

> 请注意：这种安装方式需要服务器保持联网状态以自动下载 Ollama 的二进制文件，如果出现下述报错，则说明网络环境不同，需要根据实际情况处理网络连接。
![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/202403081606383.png)
{: .prompt-tip }

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502111858360.png)

至此，已经成功完成 Ollama 项目的本地部署，并顺利启动了 Ollama 服务。


## Ollama 下载 DeepSeek R1 及启动

> 需要说明的一点是：`Ollama`项目虽然提供了本地化大模型的能力，但这并不意味着所有大模型都可以通过它下载和使用，其支持的大模型的详细列表可在`Ollama`的官方模型库页面查看：[https://ollama.com/library](https://ollama.com/library)。
{: .prompt-tip }

![Ollama 支持的大模型   ](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202502121017505.png)
## Ollama 启动和使用方法

## Ollama 多 GPU 部署及 server 启动

## Ollama REST API 服务启动及调用

## 
