---
title: DeepSeek + Dify本地部署实战：Ollama一键运行大模型
description: 在Windows环境下使用Ollama和Dify本地部署DeepSeek模型，并通过Postman进行API测试验证。
author: hsc
date: 2025-03-17 10:00:00 +0800
categories: [AI Agent, 低代码平台, Dify]
tags: [DeepSeek, Dify, Ollama, 本地部署, API测试, Postman]
math: true
mermaid: true
---

# 背景
   最近，AI 领域真是火得不行，尤其是DeepSeek模型，简直成了各行各业的‘神器’。它不仅能聊天、写文案，还能帮你分析数据、生成代码，功能强大到让人惊叹！但问题是，很多朋友想用却不知道怎么上手——技术门槛高、开发成本大，让人望而却步。

今天咱们就来极低代码部署调用DeepSeek，就是为了解决这个问题。你不需要懂编程，也不用折腾复杂的配置，只要跟着课程走，就能轻松调用 DeepSeek 的强大能力，快速把它用到你的工作或项目中。无论你是完全不懂技术的小白，还是想快速上手的行业老手，这节课都能帮你轻松玩转DeepSeek！
# 1. Ollama
Ollama 和 Xinference 都是用于运行和部署大模型的工具，但它们的设计目标、功能和使用场景有所不同：

### Ollama简介
Ollama 是一个专注于简化本地大模型运行的工具，特别适合个人开发者或小团队快速上手和使用大模型。

 **特点：**
1. **本地运行**：
   - Ollama 主要设计用于在本地机器上运行大模型，支持 CPU 和 GPU 加速。
   - 适合个人开发者或小规模团队快速测试和部署模型。

2. **简单易用**：
   - 提供命令行工具，用户可以通过简单的命令下载、运行和管理模型。
   - 支持多种开源模型，无需复杂配置。

3. **轻量级**：
   - Ollama 的设计目标是轻量化，适合资源有限的本地环境。
   - 默认使用单个 GPU 或 CPU 运行模型。



### Xinference简介
Xinference 是一个分布式推理框架，专注于为企业级用户提供高性能、可扩展的大模型部署和推理服务。

 **特点：**
1. **分布式推理**：
   - Xinference 支持多节点、多 GPU 的分布式推理，适合处理大规模模型和数据。
   - 可以动态扩展计算资源，满足高并发需求。

2. **企业级功能**：
   - 提供高性能的模型推理服务，支持负载均衡、自动扩缩容等功能。
   - 适合需要高可用性和高稳定性的生产环境。

3. **模型管理**：
   - 支持多种模型格式和框架，并提供统一的 API 接口。
   - 可以方便地管理和部署多个模型。

4. **可扩展性**：
   - 支持自定义插件和扩展，方便用户根据需求定制功能。


根据你的需求和场景，可以选择适合的工具！
## Ollama部署安装
主要特点：


- 简化部署：
Ollama 通过将模型权重、配置和数据捆绑到一个称为 Modelfile 的包中，简化了模型的安装和配置过程，使得用户可以更方便地管理和运行这些模型。

- 跨平台支持：
Ollama 支持多种操作系统，包括 macOS、Linux 和 Windows。用户只需下载相应平台的安装包即可快速安装和使用。

- 命令行操作：
用户可以通过简单的命令行指令来启动和运行模型。例如，运行一个模型只需执行类似 ollama run model_name 的命令。

- 资源要求：
相较于传统部署调用模型的方法，Ollama模型支持推理的大部分为量化后的模型，这种方式对硬件资源的需求更低，更适合开发者快速上手。

当前电脑环境配置
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211160040900_9465f05b.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250211160131537_e5c7aaf3.png)

官网地址：https://ollama.com/

![image](/assets/img/posts/low-code-dify-coze-12/image-20250211034222964_a4f48e1f.png)

进行下载
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211140655068_b430a1b9.png)

双击安装即可
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211143209123_10e0df35.png)

安装过程展示
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211143344177_64c9abe3.png)

安装完成后电脑右下角可以看到Ollama的标识
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211143432868_e2f33db8.png)

cmd启动命令窗口  
输入Ollama list 查看运行状况 
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211150127893_db01b397.png)

## 常用命令

| 命令格式                     | 说明                                |
|--------------------------|-----------------------------------|
| `ollama [flags]`         | 使用标志（flags）运行 ollama。          |
| `ollama [command]`       | 运行 ollama 的某个具体命令。            |

可用命令

| 命令        | 说明                      |
| ----------- | ----------------------- |
| `serve`     | 启动 ollama 服务。           |
| `create`    | 根据一个 Modelfile 创建一个模型。 |
| `show`      | 显示某个模型的详细信息。        |
| `run`       | 运行一个模型。               |
| `stop`      | 停止一个正在运行的模型。        |
| `pull`      | 从一个模型仓库（registry）拉取一个模型。 |
| `push`      | 将一个模型推送到一个模型仓库。      |
| `list`      | 列出所有模型。              |
| `ps`        | 列出所有正在运行的模型。         |
| `cp`        | 复制一个模型。              |
| `rm`        | 删除一个模型。              |
| `help`      | 获取关于任何命令的帮助信息。      |

标志（Flags）

| 标志              | 说明                |
| ----------------- | ------------------- |
| `-h, --help`      | 显示 ollama 的帮助信息。 |
| `-v, --version`   | 显示版本信息。         |

也可以使用浏览器方式进行验证 
打开浏览器，输入 “http://localhost:11434/”，显示 “Ollama is running”。

![image](/assets/img/posts/low-code-dify-coze-12/image-20250211161220328_cba5bf6b.png)

下载模型： 
返回官网页面选择Model，可以直接搜索想要下载的模型，也可以直接选择当前模型。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211145915207_a8caf705.png)

进入模型链接后会有更为丰富模型体积选择与讲解。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211152027477_d2e1887f.png)

说明模型下载命令对应的模型
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211154626817_c1eae080.png)

以上详细内容可以去魔撘社区中查看详细内容：https://www.modelscope.cn/models/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B

下载一个小模型进行验证 ollama run deepseek-r1:1.5 
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211152211389_7cd6bdc5.png)

想要再次运行直接再次启动命令即可 ollama run 命令
![image](/assets/img/posts/low-code-dify-coze-12/image-20250213165354398_6581d63a.png)

问答效果验证
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211155501377_65c704ea.png)

ollama run deepseek-r1 默认命令为 ollama run deepseek-r1:7b

![image](/assets/img/posts/low-code-dify-coze-12/image-20250211164525591_c3d94659.png)

更改模型默认下载地址   
```
ollama 模型存放默认地址为 C:\Users\%username%\.ollama\models 
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211162947942_3bac8267.png)

环境变量中增加变量名称：OLLAMA_MODELS  
变量值为：目标路径(例如当前为C:\ollama_model) 建议存放到其他硬盘
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211170321445_3731d5aa.png)

重启后生效(关闭当前窗口退出ollama程序 ，再次打开cmd窗口)  同时运行刚刚执行过命令会重新下载模型。

![image](/assets/img/posts/low-code-dify-coze-12/image-20250211170631267_0cec1904.png)

到环境变量配置好的路径下进行查看配置是否生效
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211170652582_7cbe37dc.png)

OLLAMA_SCHED_SPREAD=1   加载到所有GPU上
![image](/assets/img/posts/low-code-dify-coze-12/image-20250213145849026_96f5c5ee.png)

# 2. Dify安装
## docker安装
当前为最新版本安装，更关注细节的小伙伴请看《Ch 1 window&Dify&xinference环境部署与安装》课件  
主要安装过程是使用新版本deepseek模型，安装流程基本一致。
本次目的是使用docker快速部署dify，如果想尝试源码安装dify请参考课件《Ch2 源码部署Dify构建RAG》
https://www.docker.com/

![image](/assets/img/posts/low-code-dify-coze-12/image-20250211174246819_49ffbfe7.png)

双击安装即可
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211174158042_45caddf9.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250211174310348_143116ea.png)

如遇到类似以下报错：
Wsl/Service/RegisterDistro/CreateVm/HCS/HCS_E_HYPERV_NOT_INSTALLED\r\n" output="docker-desktop": exit code: 4294967295: running WSL command wsl.exe C:\WINDOWS\System32\wsl.exe --import docker-desktop <HOME>\AppData\Local\Docker\wsl\main C:\Program Files\Docker\Docker\resources\wsl\wsl-bootstrap.tar --version 2: 当前计算机配置不支持 WSL2。 请启用“虚拟机平台”可选组件，并确保在 BIOS 中启用虚拟化。 通过运行以下命令启用“虚拟机平台”: wsl.exe --install --no-distribution 有关信息，请访问 https://aka.ms/enablevirtualization 错误代码: Wsl/Service/RegisterDistro/CreateVm/HCS/HCS_E_HYPERV_NOT_INSTALLED : exit status 0xffffffff checking if isocache exists: CreateFile \wsl$\docker-desktop-data\isocache: The network name cannot be found.

可能会涉及到WSL2版本问题，重新安装即可。
**WSL2 安装问题解决步骤**

要在 Windows 11 启用 WSL2，按照以下步骤操作：

 1. 启用必要的 Windows 功能
在管理员权限的 PowerShell 中运行以下命令：
```shell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```
2. 启用 Hyper-V
运行：

```powershell
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```
3. 设置 WSL2 为默认版本
```powershell
wsl --set-default-version 2

使用
wsl --status
wsl --version
验证安装状态
```
4. 启用虚拟化(不同主板型号不一样，但是处理方式一样)  
重启电脑进入 BIOS 设置。  
找到并启用以下选项（根据主板品牌可能名称不同当前主板为华硕F2进入控制界面）：  
选择-》高级选项-》CPU****(可能有所不同)-》SVM类型 设置为开启。

暂时不登录，有账号同学可以直接登录使用
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230143139484_982935c9.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230143159408_8eb41e87.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211183111913_b79f285e.png)

### docker desktop 汉化安装(看个人喜好)
安装包地址 https://github.com/asxez/DockerDesktop-CN  自行选择合适版本安装包
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230143825045_a834a46e.png)
选择后下载
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230143848977_2772e3aa.png)
找到docker安装路径
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230144431998_4c12837c.png)
退出docker
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230144850481_1f7d035b.png)
找到app.asar 文件并进行备份(防止异常后无法恢复)
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230144446506_c2517da1.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230144518195_e6ab092b.png)
将刚刚下载内容重新命名app.asar  并将原文件替换
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230144553525_f78ee483.png)
重新启动docker
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230150523938_3ddf6712.png)
## 安装Dify
Dify 下载地址 https://github.com/langgenius/dify
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230151304937_e33f63ca.png)
下载完成后自行指定位置与名称，当前使用的是下载压缩包方式进行安装
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230151316792_b41a02f7.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230151402225_40d6f098.png)
重新命名为dify
![image](/assets/img/posts/low-code-dify-coze-12/image-20250212172404643_b2f9ac72.png)
进入Dify目录中docker路径下，复制.env.example 为.env 方便后续docker执行
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211184557473_790ff0d0.png)

可以通过 $ docker compose version 命令检查版本，详细说明请参考 Docker 官方文档：https://docs.docker.com/compose/#compose-v2-and-the-new-docker-compose-command

进入当前路径docker文件夹下

如果版本是 Docker Compose V2，使用以下命令：

docker compose up -d

如果版本是 Docker Compose V1，使用以下命令：

docker-compose up -d
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211184823382_9e12162e.png)

运行成功
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211185410454_71377b48.png)

执行docker compose ps 进行验证
可以看到包括 3 个业务服务 api /worker /web，以及 6 个基础组件 weaviate /db /redis /nginx /ssrf_proxy /sandbox
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211185640074_16f633bb.png)

## Dify注册验证

本地环境
http://localhost/install

先前往管理员初始化页面设置设置管理员账户
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230183627360_8420e6c0.png)
创建账户名称，可根据自己想法进行设定(当前界面为随机填写邮箱，并未有验证码要求)
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230183709593_bd7f499b.png)
注册完成后进行登录
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230183813971_6b4d9da4.png)
登录后界面
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230184512235_7e9686eb.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211190012683_9d61a3f6.png)

选择创建类型，自行编辑聊天名称、头像及描述
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230192916103_4aec12a8.png)
点击进入机器人，开始配置大模型相关内容
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230193141510_9d09ea97.png)
### ollama+dify调试
可供选择的大模型及框架接入
![image](/assets/img/posts/low-code-dify-coze-12/image-20250212173646799_c71babe3.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230193315282_91bbc328.png)
配置异常通常是IP地址没写对或者模型名称不明确
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211191821651_6b77ed96.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250211191834653_38f59b11.png)

当前是使用docker启动dify，直接使用localhost是无法访问本地ollama的。
http://host.docker.internal:11434

![image](/assets/img/posts/low-code-dify-coze-12/image-20250211193133858_f0566d9d.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250211191942476_c4a08862.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250211193151655_836c4bb2.png)

返回聊天界面进行模型更换并校验。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211193315720_76921ea3.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250211193345124_a6648d2e.png)

调试完成。
# 3. xinference安装
## 安装Anaconda 

(建议直接使用conda安装，做好环境隔离)建议使用miniconda


conda官网：https://anaconda.org/anaconda/conda 可以考虑下载使用
![image](/assets/img/posts/low-code-dify-coze-12/image-20250212182726742_17721fe4.png)

安装mini conda

选择镜像源下载  https://www.cnblogs.com/ajianbeyourself/p/17310681.html
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230200044980_68c8cdcc.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230200101354_4fd29570.png)
选择合适的版本
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230200236638_94faa5b7.png)
下载完成点击安装
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230200432306_d5a36e20.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230200448720_2f239a33.png)
中间根据个人需求来选择是否默认python版本和对应配置环境变量
继续安装
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230200558764_f8ec23e5.png)
到开始环境下找命令窗口来启动conda
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230200944747_2e2926ae.png)
conda使用时候需要到全部中寻找，然后选择PowerShell Prompt ,遇到权限不足时右键选择使用管理员身份运行即可。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250211200139420_53928dd0.png)

创建环境xinference：  conda create -n xinference python=3.11
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230201051338_7387a1d2.png)
进行环境切换 conda activate 创建的环境名称

pip install "xinference[all]"
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230201313811_6d1dac21.png)
遇到报错：
![image](/assets/img/posts/low-code-dify-coze-12/image-20250212183716571_7a59018a.png)
点击链接进行跳转下载C编译器  https://visualstudio.microsoft.com/zh-hans/vs/
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230191649165_77165c32.png)
进行下载
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230191727944_4a52bfe8.png)
直接点击安装即可
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230191751324_0a7d5533.png)
默认方式进行
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230191808255_c6ccc40f.png)
选择C++桌面开发，每人选择安装内容不一样，对应占据空间大小也不一样。
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230191854005_4a3f126f.png)
选择完成后开始安装即可
![image](/assets/img/posts/low-code-dify-coze-12/image-20241230191927795_675f9621.png)
如果还没解决，直接去github上去下载对应版本软件，不建议直接pip安装。
https://github.com/abetlen/llama-cpp-python/releases

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212111128750_426ff176.png)

进入下载whl的路径下：pip install .\llama_cpp_python-0.2.90-cp311-cp311-win_amd64.whl

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212111034877_96b8c0d1.png)

如果遇到chatglm缺失的情况下同样处理办法
https://github.com/li-plus/chatglm.cpp/releases

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212111324953_e94efdad.png)

xinference-local --host localhost --port 9997

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212112430807_c7eb6eda.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212112310054_53a458a3.png)

 xinference window环境默认模型下载路径为  
 ```
 C:\Users\%用户名称% \.cache\  
 ```
 如果想更改模型存储路径及默认下载链接更改环境变量  
XINFERENCE_MODEL_SRC=modelscope  
XINFERENCE_HOME=C:\xinference_model  
(如果配置完成不生效建议关闭命令窗口重新启动)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212115911342_83597856.png)

选择模型进行发布
![image](/assets/img/posts/low-code-dify-coze-12/image-20250212120210103_af63233d.png)

后台查看下载路径
![image](/assets/img/posts/low-code-dify-coze-12/image-20250212141140203_7a2a8480.png)

发布后可以直接来到运行的模型页面进行测试使用。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250212191756497_07dd2f25.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212192338604_3020dda3.png)

## Dify连接xinference
![image](/assets/img/posts/low-code-dify-coze-12/image-20250212192412784_85174e7d.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212192456289_966e3d45.png)

http://host.docker.internal:9997

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212193102062_d67fef58.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212193122664_c8ac333d.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212193151780_c24258cc.png)

## 模型横向对比
![image](/assets/img/posts/low-code-dify-coze-12/image-20250212193421206_19eb452c.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212193448628_a656e87a.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212193512558_39bb9e4c.png)

两个模型设置参数相同。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250212193538860_634a55a1.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212193633678_6ca4c862.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212193821007_fa409305.png)

单独更新发布。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250212195641799_48948989.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212195727515_992522be.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212195829477_4b0a4466.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212204109109_9ea945a1.png)

# 4. 使用API调用检验
使用post请求方式来对发布的程序进行校验。
Postman 是一款用于开发和测试 API 的工具，主要功能包括：

1. **API 测试**：支持发送 HTTP 请求（如 GET、POST、PUT、DELETE），并查看响应结果。
2. **自动化测试**：通过编写测试脚本，自动验证 API 的响应状态码、数据格式等。
3. **环境管理**：允许设置不同环境变量，方便在开发、测试、生产等环境中切换。  
4. **...**
https://www.postman.com/downloads/

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212202635402_937a02ca.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212202658503_4cf55fe1.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212202712693_e6d8eabe.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212202546817_9a2dee91.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212202444226_27c78047.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250212202349415_3f527c68.png)
# 5. 总结
![image](/assets/img/posts/low-code-dify-coze-12/image-20250213171018869_b508d483.png)