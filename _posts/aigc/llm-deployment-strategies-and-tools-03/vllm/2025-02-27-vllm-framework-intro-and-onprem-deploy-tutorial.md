---
title: vLLM 框架介绍与本地私有化部署
description: vLLM 框架从入门到部署的完整实战教程，涵盖离线推理、采样参数调优、DeepSeek R1 推理模型格式化输出及多模态模型支持
author: hsc
date: 2025-02-27 19:27:00 +0800
categories: [AI Agent]
tags: [vLLM, Ollama, DeepSeek, Qwen, 大模型部署, 离线推理, DeepSeek R1]
---

对于开源大模型来说，虽然模型权重开源，但并不意味着这样的模型可以开箱即用，而是需要一个框架来支撑其运行和推理。

无论哪个公司旗下的模型，现在都在兼容同一个接入规范，即 `Open AI` 兼容接口，因为这种 `API` 规范几乎可以和任何 `SDK` 或者客户端无缝集成，所以对大模型部署框架而言，是否兼容 `Open AI` 规范就成为了衡量一个其是否成熟、是否可以被广泛使用的重要指标。

因此，大家都关注的问题就是：部署与 `OpenAI API` 规范兼容模型的最佳框架是什么？

如下所示，目前主流的大模型部署框架以 `llama.cpp`、`Ollama` 和 `vLLM` 为主，其各自在 Github 上的 Stars 的增长曲线如下所示。其中 `Ollama` 的 Stars 增长曲线是断档式领先，而 `llama.cpp`和 `vLLM`的 Stars 增长曲线则相对平缓，处于一个稳步增长的趋势。

![`llama.cpp`、`Ollama` 和 `vLLM` 在 Github 上的 Stars 的增长曲线](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504181034368.png)

之所以会呈现这种现状，其实与各个框架的定位有本质区别：
- `llama.cpp` 是使用没有任何依赖关系的纯 C/C++ 实现，性能很高，可定制化和优化项非常多，但也因为底层是`C`语言，直接导致上手难度极高。
- `Ollama` 之所以能够受到最多开发者的关注，一个最根本的原因就是其部署和使用太简单了，兼容多种操作系统，且都提供了一键安装、单命令启动的快捷方式，可以极大降低初学者使用开源大模型的门槛，同时`Ollama`框架提供原生 `REST API` 和 `OpenAI API` 兼容性，也可以非常轻松的接入到其他的客户端中。


## vLLM 框架整体概览

如果说 `Ollama` 的优势在于其简洁性，那么 `vLLM` 就是一个另辟蹊径、优先考虑性能和可扩展性的大模型部署框架。

`vLLM` 核心优化点是：
1. 高效内存管理
2. 持续批处理功能
3. 张量并行性
从而在生产环境中的高吞吐量场景中表现极佳，同时这也是为什么 vLLM 框架是目前最适用于企业真实生产环境部署的根本原因。

vLLM 底层是基于 Pytorch 构建，其 GitHub 开源地址是：[https://github.com/vllm-project/vllm](https://github.com/vllm-project/vllm)

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504181137533.png)

从各种基准测试数据来看，同等配置下，使用 vLLM 框架与 Transformer 等传统推理库相比，其吞吐量可以提高一个数量级，这归功于以下几个特性：
- 高级 GPU 优化：利用 CUDA 和 PyTorch 最大限度地提高 GPU 利用率，从而实现更快的推理速度。Ollama其实是对CPU-GPU的混合应用，但vLLM是针对纯GPU的优化。
- 高级内存管理：通过PagedAttention算法实现对 KV cache的高效管理，减少内存浪费，从而优化大模型的运行效率。
- 批处理功能：支持连续批处理和异步处理，从而提高多个并发请求的吞吐量。
- 安全特性：内置 API 密钥支持和适当的请求验证，不像其他完全跳过身份验证的框架。
- 易用性：vLLM 与 HuggingFace 模型无缝集成，支持多种流行的大型语言模型，并兼容 OpenAI 的 API 服务器。

以上核心的优化点原理以及应用方法，会今后逐步学习和实践。本文先进行vLLM 框架的私有化部署的学习。

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171511604.png)

其次是多模态模型，vLLM框架目前已经支持文本、图片、视频和音频四种模态的输入输出格式兼容规范，但是多模态模型官方并没有给出具体的模型列表，所以这里我们要进入到源码中对模型的集成文件中去匹配：![](https://github.com/vllm-project/vllm/tree/main/vllm/model_executor/models)

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504181304597.png)

根据各个模型支持.py文件中的代码细节，这里梳理了一份目前最新版本vLLM 0.8.4支持的多模态模型如下表所示：

| .py 文件                                                            | 模型名称         | 描述                                                                |
| ------------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------- |
| aya_vision.py                                                       | aya-vision       | https://huggingface.co/CohereLabs/aya-vision-8b                     |
| blip.py / blip2.py                                                  | BLIP             | 经典视觉-语言模型（BLIP 系列）。                                    |
| clip.py                                                             | CLIP             | 经典的多模态对比学习模型（CLIP）。                                  |
| deepseek_vl2.py                                                     | DeepSeek         | DeepSeek 的多模态版本（VL 表示 Vision-Language）。                  |
| florence2.py                                                        | 微软模型         | 微软的多模态模型。https://huggingface.co/microsoft/Florence-2-large |
| fuyu.py                                                             | Fuyu             | Adept 的多模态模型（Fuyu 系列）。                                   |
| gemma3_mm.py                                                        | Gemma            | mm 表示 Multimodal（Gemma 的多模态扩展）。                          |
| glm4v.py                                                            | GLM-4            | GLM-4 的多模态版本（v 表示 Vision）。                               |
| h2ovl.py                                                            | H2O              | H2O 的视觉-语言模型（vl 后缀）。                                    |
| idefics2_vision_model.py / idefics3.py                              | Idefics          | Meta 的多模态模型（Idefics 系列）。                                 |
| internvl.py                                                         | InternVL-Chat    | 上海 AI Lab 的多模态模型。                                          |
| kimi_vl.py                                                          | Kimi-VL-A3B      | 新增的 Kimi-VL 模型                                                 |
| llava.py / llava_next.py / llava_next_video.py / llava_onevision.py | LLaVA            | LLaVA 系列及其变种（开源视觉-语言模型）。                           |
| mllama4.py                                                          | LLaMA-4          | 多模态版本的 LLaMA-4。                                              |
| molmo.py                                                            | Molmo            | 提交记录涉及多模态数据处理。                                        |
| moonvit.py                                                          | Kimi-VL          | 与 Kimi-VL 同时新增的多模态模型。                                   |
| nvlm_d.py                                                           | NVLM-D-72B       | NVIDIA 的多模态模型（vl 相关）。                                    |
| paligemma.py                                                        | PaLI-Gemma       | Google 的 PaLI-Gemma 多模态模型。                                   |
| phi3v.py / phi4mm.py / phi4mm_audio.py                              | Phi-3 / Phi-4    | Phi-3 和 Phi-4 的多模态版本（支持视觉或音频）。                     |
| prithvi_geospatial_mae.py                                           | Prithvi-EO-1.0   | 地理空间多模态模型（NASA 合作项目）。                               |
| qwen2_5_vl.py / qwen2_audio.py / qwen2_vl.py / qwen_vl.py           | 通义千问         | 通义千问的多模态版本（视觉或音频）。                                |
| siglip.py                                                           | SigLIP           | Google 的 SigLIP（多模态对比学习）。                                |
| skyworkr1v.py                                                       | Skywork-R1V-38B  | 幻方多模态模型（v 后缀）。                                          |
| smolvlm.py                                                          | SmolVLM          | 轻量级多模态模型（新增支持）。                                      |
| whisper.py                                                          | whisper-large-v3 | OpenAI 的语音-文本多模态模型（虽然主要处理音频，但属于跨模态）。    |


## 部署 vLLM

首先需要重点说明的是：vLLM 框架仅支持 Linux 操作系统，官方没有提供 Windows 的兼容版本。同时除了有操作的限制，对运行的 Python 版本也要求在 Python 3.8 ~ Python 3.12。这两个条件限制是部署 vLLM 的先决条件，即必须满足才可以顺利使用 vLLM 启动大模型并提供推理服务。

这个策略非常符合企业级的部署策略，vLLM 框架作为目前在实际生成环境中使用最为广泛的框架之一，其对 Linux 操作系统的支持，以及对 Python 版本的限制，都是为了确保在生产环境中能否稳定运行，并且能够提供高性能的推理服务。

这里我采用的 Linux 操作系统是 Ubuntu 24.04，同时配置 4 张 3090 显卡来进行 vLLM 框架的部署和使用。

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171511611.png)

vLLM 工具已经通过编译并上传到 PYPI 仓库以及主流的包管理平台中，所以可以直接使用如 `pip`、`conda` 等工具进行快速安装。这里我使用毕竟常用的 conda 包版本管理工具进行安装部署。

### Step1. 安装 `conda` 包版本管理工具

首先需要检查当前使用的操作系统是否已经安装了`conda` 包版本管理工具，可以通过`conda --version` 命令查看`Conda` 版本，如下图所示：
![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171523767.png)

### Step2. 创建 Python 虚拟环境

如果出现Conda not found 等报错，需要先安装Conda 环境，再执行接下来的步骤。

`vllm`官方要求的是`Python 3.9` ~ `Python 3.12` 之间的版本，这里我们选择`Python 3.12` 版本。执行如下命令进行创建：

```bash
conda create --name vllm python=3.12
```

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171511612.png)

### Step3. 激活虚拟环境

创建完虚拟环境后，使用 Conda 激活虚拟环境，通过 `conda activate vllm` 命令激活，如下图所示：

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171511613.png)

接下来，使用 pip 安装 vLLM 框架，执行命令：`pip install vllm`

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171511614.png)

此时耐心等待安装完成即可。待安装完成后，可以使用 `pip show vllm` 命令查看 vLLM 框架的安装信息，可以明确看到当前安装的 vLLM 版本号，如下图所示：

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171511615.png)

至此，vLLM 框架的安装就已经完成了。整个过程就是非常常规的依赖包安装过程，唯一需要注意的就是 Python 版本的要求。

在完成 vLLM 框架安装后，就可以开始进行大模型推理服务的启动和调用了。vLLM 框架提供了两种启动并调用大模型生成推理服务的方式，分别是离线推理和在线推理。其中：
- **离线推理**： 离线推理类似于使用 `Pytorch` 模块一样，当我们需要使用大模型生成推理服务时，先加载模型，然后使用输入数据运行该模型，并获取输出结果。
- **在线推理**： 在线推理类似于有一个服务器，可以先启动大模型，然后等待来自客户端的请求，一旦接收到请求，就会使用大模型生成推理服务，并返回结果，并且可以同时处理多个请求。

这是两种不同推理方式最本质的区别，毫无疑问在线推理是更加符合实际生产环境的。但为了更好的理解vLLM 框架，熟悉离线推理是非常有必要的。

## vLLM 离线推理

无论是在线推理还是离线推理，都采用的是 API 接口的方式来调用大模型生成推理服务。对离线推理来说，其加载模型、传输数据、获取结果的 API 调用形式如下所示：

```python
    from vllm import LLM
    # 加载模型
    llm = LLM(model="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")
    
    # 传输数据
    outputs = llm.generate("你好，我是清锋")

    # 获取结果
    for output in outputs:
        prompt = output.prompt
        generated_text = output.outputs[0].text
        print(f"Prompt: {prompt!r}, Generated text: {generated_text!r}")
```

代码看起来简单，但如果想要跑通这几行代码，则需要提前做2件非常关键的准备工作：
1. 下载大模型权重
2. 配置一个可以加载服务器虚拟环境（即上一步创建的 vllm 虚拟环境）的 Python IDE 解释器。

以 DeepSeek-R1-Distill-Qwen-32B 大模型为例，默认情况下，`LLM(model="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")` 这行命令的执行逻辑是：先检测当前服务器中是否存在 `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` 的模型权重，如果存在则直接加载该目录下的模型权重，否则会从 Hugging Face 上下载大模型权重。其存在的主要问题是：国内的服务器是没有办法访问 Hugging Face 网站的，所以一定会报错。因此，国内的开发者需要采用更有效的方式来确保大模型权重的正确下载，即使用国内镜像源 ModelScope 来执行模型权重的本地化存储。

回到 Linux 服务器中，首先通过如下命令安装 ModelScope 的 pip 包：

```bash
pip install modelscope
```

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171511620.png)

接下来，进入到 ModelScope 的主页：[https://www.modelscope.cn/home](https://www.modelscope.cn/home)

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171613863.png)

通过关键词找到对应的模型详情页，比如我这里以 `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` 为例，点击进入详情页，如下图所示：
![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171613865.png)

进入到模型详情页，点击 `模型文件`，然后再找到 `下载模型` 按钮，如下图所示：

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171613866.png)

在弹出来的会话框中，找到 SDK 下载标签，复制对应的模型服务指针标识，如下所示：

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171613867.png)

接下来回到 Linux 服务器中，通过 vim 新建一个 model_download.py 文件：
```bash
vim model_download.py
```
![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171511621.png)

然后，按 i 键进入编辑模式，将赋值的代码粘贴到文件中：

```python
    from modelscope import snapshot_download

    # model_dir = snapshot_download('deepseek-ai/DeepSeek-R1-Distill-Qwen-32B', cache_dir='/root/autodl-tmp', revision='master')
    model_dir = snapshot_download('deepseek-ai/DeepSeek-R1-Distill-Qwen-32B', cache_dir='/home/08_vllm', revision='master')
```
![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171511622.png)

修改完成后，按`Esc` 键退出编辑模式，再按`Shift+:` 键进入命令模式，输入`wq` 保存并退出。执行如下命令，运行`model_download.py` 文件：

```bash
    python model_download.py
```

[](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171511623.png)

耐心等待模型权重下载完成即可。待下载完成后，可以看到`/home/08_vllm` 目录下会多出一个`deepseek-ai` 文件夹，里面存放的就是`DeepSeek-R1-Distill-Qwen-32B` 大模型的权重文件。如下图所示：

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171622553.png)

按照上述流程中 `model_download.py` 下载模型的方式，可以允许我们随意下载任意在 ModelScope 中托管的模型权重至本地。因此我这里依次下载了 Qwen2.5 系列和 DeepSeek R1 系列的不同尺寸的模型，也可以根据自己的需求灵活选择模型。

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504181342835.png)

至此，大模型权重就已经下载完成了。接下来，需要做的是配置一个可以加载服务器虚拟环境（即上一步创建的 vllm 虚拟环境）的 Python IDE 解释器。这一步会根据实际开发情况产生不同的配置方法，总的来说分成以下两种情况：
1. 部署大模型的服务器和你要执行代码调用的 python ide 是同一台服务器，就可以直接选择到对应的虚拟环境并执行代码；
2. 部署大模型的服务器和你要执行代码调用的 python ide 不是同一台服务器，则需要通过 SSH 连接到部署大模型的服务器，然后选择到对应的虚拟环境并执行代码。

同一台服务器的情况非常简单，直接打开 Python IDE，选择到对应的虚拟环境并执行代码即可。这里重点介绍第二种情况，即部署大模型的服务器和你要执行代码调用的 Python IDE 不是同一台服务器。同时这也是最常见的企业开发环境。

这类情况最通俗的理解就是：我们把大模型部署在了局域网/租赁的云服务器中，希望可以在本地电脑上执行代码调用模型服务。这类情况我们要做如下配置：（以 Jupyter Notebook 为例：

首先进入在局域网/租赁的云服务器的 Linux 服务器中，在 vllm 虚拟环境中安装 ipykernel 和 jupyter 包，执行如下命令：
```bash
pip install ipykernel jupyter
```

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171511616.png)

安全起见，对连接时的秘密进行加密处理，否则明文写在配置文件中，容易造成数据安全风险，依次执行如下操作：

```python
form jupyter_server.auth import passwd
passwd()
```

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/202401261753935.png)

完成密码加密后，执行如下命令生成 Jupyter Lab 的配置文件（jupyter_lab_config.py）
```python
jupyter lab --generate-config
```

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/202401261753934.png)

使用 Vim 编辑器，找到如下配置，执行修改：

```python
    c.ServerApp.allow_origin = '*'
    c.ServerApp.allow_remote_access = True
    c.ServerApp.ip = '0.0.0.0'
    c.ServerApp.open_browser = False  
    c.ServerApp.password = '加密后的密码'（上一步复制的加密串）
    c.ServerApp.port = 8002 
```

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/202401261753936.png)

全部配置完成后，在服务器端启动 Jupyter Lab 服务，通过如下命令后台启动。

```bash
nohup jupyter lab --allow-root > jupyterlab.log 2>&1 &
```

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/202401261753937.png)

然后，将虚拟环境的 Kernel 写入 Jupyter Lab，执行如下命令，创建一个 ipykernel 内核：
```bash
 python -m ipykernel install --user --name vllm --display-name "vllm"
```

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171511617.png)

接下来，在浏览器中打开`Jupyter Notebook` 服务，在`Jupyter kernel` 中就会出现选择`vllm` 内核的选项，如下图所示：

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171511618.png)

选择`vllm` 内核并创建一个新的`notebook` 笔记本，可以通过`! pip show vllm` 快速验证是否正常加载到了`vllm` 的虚拟环境：

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504171511619.png)

如果正常加载到了`vllm` 的虚拟环境，则可以看到`vllm` 的版本号，这里可以看到，与我们在服务器上安装的版本号是一致的。说明我们已经在本地电脑上成功加载到了`vllm` 的虚拟环境。

接下来，我们可以通过离线推理的API 接口来调用大模型生成推理服务。我们会对对话模型和推理模型依次展开详细的测试。

首先以`Qwen2.5`系列为例测试在`vLLM`框架下对对话类模型的使用。默认情况下，`vLLM` 从`huggingface`下载模型权重，并使用`transformers`库加载模型。这里我们的模型是从`ModelScope`下载的，所以在调用离线推理`API`时，需要搭配`trust_remote_code=True`参数，其次，对`model` 参数，指的是模型权重文件的本地路径，因此需要大家根据模型下载路径进行修改。即实例化代码如下图所示：

```python
from vllm import LLM

llm = LLM(
    model="/home/08_vllm/qwen/Qwen2___5-7B",
    trust_remote_code=True,
    max_model_len=4096,
)
```

```Response
INFO 04-18 14:21:53 [__init__.py:239] Automatically detected platform cuda.
INFO 04-18 14:22:03 [config.py:689] This model supports multiple tasks: {'generate', 'embed', 'classify', 'reward', 'score'}. Defaulting to 'generate'.
INFO 04-18 14:22:03 [config.py:1901] Chunked prefill is enabled with max_num_batched_tokens=8192.
INFO 04-18 14:22:04 [core.py:61] Initializing a V1 LLM engine (v0.8.4) with config: model='/home/08_vllm/qwen/Qwen2___5-7B', speculative_config=None, tokenizer='/home/08_vllm/qwen/Qwen2___5-7B', skip_tokenizer_init=False, tokenizer_mode=auto, revision=None, override_neuron_config=None, tokenizer_revision=None, trust_remote_code=True, dtype=torch.bfloat16, max_seq_len=4096, download_dir=None, load_format=LoadFormat.AUTO, tensor_parallel_size=1, pipeline_parallel_size=1, disable_custom_all_reduce=False, quantization=None, enforce_eager=False, kv_cache_dtype=auto,  device_config=cuda, decoding_config=DecodingConfig(guided_decoding_backend='auto', reasoning_backend=None), observability_config=ObservabilityConfig(show_hidden_metrics=False, otlp_traces_endpoint=None, collect_model_forward_time=False, collect_model_execute_time=False), seed=None, served_model_name=/home/08_vllm/qwen/Qwen2___5-7B, num_scheduler_steps=1, multi_step_stream_outputs=True, enable_prefix_caching=True, chunked_prefill_enabled=True, use_async_output_proc=True, disable_mm_preprocessor_cache=False, mm_processor_kwargs=None, pooler_config=None, compilation_config={"level":3,"custom_ops":["none"],"splitting_ops":["vllm.unified_attention","vllm.unified_attention_with_output"],"use_inductor":true,"compile_sizes":[],"use_cudagraph":true,"cudagraph_num_of_warmups":1,"cudagraph_capture_sizes":[512,504,496,488,480,472,464,456,448,440,432,424,416,408,400,392,384,376,368,360,352,344,336,328,320,312,304,296,288,280,272,264,256,248,240,232,224,216,208,200,192,184,176,168,160,152,144,136,128,120,112,104,96,88,80,72,64,56,48,40,32,24,16,8,4,2,1],"max_capture_size":512}
WARNING 04-18 14:22:05 [utils.py:2444] Methods determine_num_available_blocks,device_config,get_cache_block_size_bytes,initialize_cache not implemented in <vllm.v1.worker.gpu_worker.Worker object at 0x7f4ec3dd74a0>
INFO 04-18 14:22:05 [parallel_state.py:959] rank 0 in world size 1 is assigned as DP rank 0, PP rank 0, TP rank 0
INFO 04-18 14:22:05 [cuda.py:221] Using Flash Attention backend on V1 engine.
INFO 04-18 14:22:05 [gpu_model_runner.py:1276] Starting to load model /home/08_vllm/qwen/Qwen2___5-7B...
WARNING 04-18 14:22:06 [topk_topp_sampler.py:69] FlashInfer is not available. Falling back to the PyTorch-native implementation of top-p & top-k sampling. For the best performance, please install FlashInfer.
Loading safetensors checkpoint shards:   0% Completed | 0/4 [00:00<?, ?it/s]
INFO 04-18 14:22:10 [loader.py:458] Loading weights took 4.76 seconds
INFO 04-18 14:22:11 [gpu_model_runner.py:1291] Model loading took 14.2717 GiB and 4.991946 seconds
INFO 04-18 14:22:21 [backends.py:416] Using cache directory: /root/.cache/vllm/torch_compile_cache/f2ded477b0/rank_0_0 for vLLM's torch.compile
INFO 04-18 14:22:21 [backends.py:426] Dynamo bytecode transform time: 10.11 s
INFO 04-18 14:22:22 [backends.py:115] Directly load the compiled graph for shape None from the cache
INFO 04-18 14:22:28 [monitor.py:33] torch.compile takes 10.11 s in total
INFO 04-18 14:22:31 [kv_cache_utils.py:634] GPU KV cache size: 97,680 tokens
INFO 04-18 14:22:31 [kv_cache_utils.py:637] Maximum concurrency for 4,096 tokens per request: 23.85x
INFO 04-18 14:22:55 [gpu_model_runner.py:1626] Graph capturing finished in 24 secs, took 1.44 GiB
INFO 04-18 14:22:55 [core.py:163] init engine (profile, create kv cache, warmup model) took 43.92 seconds
INFO 04-18 14:22:55 [core_client.py:435] Core engine process 0 ready.
```

LLM 类是运行离线推理的主要类。当使用 LLM 类进行模型初始化的加载时，有几个初级且重要的参数如下：
- <hl=red>device<hl/>：该参数会指定模型加载的设备，vLLM 支持在 cuda neuron cpu tpu xpu hpu，默认是 auto，即初始化时会自动识别当前系统中可用的设备
- <hl=red>tensor_paralleisze<hl/>：该参数会指定模型可以通过GPU的Tensor并行运行，默认是1，即不使用GPU的Tensor并行，但如果加载的模型参数超过单个GPU的显存，即使服务器上有多个GPU，也会报错Out of memory，并不会自动使用其他GPU进行并行。
- <hl=red>gpu_memory_utilization<hl/>：该参数会指定模型加载时，GPU的显存取值范围为0~1，使用率，默认是0.90，即GPU的显存使用率不会0过95%，但该参数会直接占用GPU的显存，以避免GPU的显存被其他进占用。

比如对 Qwen2.5-7B 模型，采用默认配置其显存占用情况如下所示：
![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504181430516.png)

如果模型比较大，则可以指定多块 GPU，比如如下所示的参数调整：

```python
from vllm import LLM

llm = LLM(
    model="/home/08_vllm/qwen/Qwen2___5-7B",
    trust_remote_code=True,
    tensor_parallel_size=2,
    gpu_memory_utilization=0.8,
    max_model_len=4096,
)
```

```Response
INFO 04-18 14:33:04 [__init__.py:239] Automatically detected platform cuda.
INFO 04-18 14:33:13 [config.py:689] This model supports multiple tasks: {'embed', 'reward', 'generate', 'classify', 'score'}. Defaulting to 'generate'.
INFO 04-18 14:33:13 [config.py:1713] Defaulting to use mp for distributed inference
INFO 04-18 14:33:13 [config.py:1901] Chunked prefill is enabled with max_num_batched_tokens=8192.
INFO 04-18 14:33:15 [core.py:61] Initializing a V1 LLM engine (v0.8.4) with config: model='/home/08_vllm/qwen/Qwen2___5-7B', speculative_config=None, tokenizer='/home/08_vllm/qwen/Qwen2___5-7B', skip_tokenizer_init=False, tokenizer_mode=auto, revision=None, override_neuron_config=None, tokenizer_revision=None, trust_remote_code=True, dtype=torch.bfloat16, max_seq_len=4096, download_dir=None, load_format=LoadFormat.AUTO, tensor_parallel_size=2, pipeline_parallel_size=1, disable_custom_all_reduce=False, quantization=None, enforce_eager=False, kv_cache_dtype=auto,  device_config=cuda, decoding_config=DecodingConfig(guided_decoding_backend='auto', reasoning_backend=None), observability_config=ObservabilityConfig(show_hidden_metrics=False, otlp_traces_endpoint=None, collect_model_forward_time=False, collect_model_execute_time=False), seed=None, served_model_name=/home/08_vllm/qwen/Qwen2___5-7B, num_scheduler_steps=1, multi_step_stream_outputs=True, enable_prefix_caching=True, chunked_prefill_enabled=True, use_async_output_proc=True, disable_mm_preprocessor_cache=False, mm_processor_kwargs=None, pooler_config=None, compilation_config={"level":3,"custom_ops":["none"],"splitting_ops":["vllm.unified_attention","vllm.unified_attention_with_output"],"use_inductor":true,"compile_sizes":[],"use_cudagraph":true,"cudagraph_num_of_warmups":1,"cudagraph_capture_sizes":[512,504,496,488,480,472,464,456,448,440,432,424,416,408,400,392,384,376,368,360,352,344,336,328,320,312,304,296,288,280,272,264,256,248,240,232,224,216,208,200,192,184,176,168,160,152,144,136,128,120,112,104,96,88,80,72,64,56,48,40,32,24,16,8,4,2,1],"max_capture_size":512}
WARNING 04-18 14:33:15 [multiproc_worker_utils.py:306] Reducing Torch parallelism from 40 threads to 1 to avoid unnecessary CPU contention. Set OMP_NUM_THREADS in the external environment to tune this value as needed.
INFO 04-18 14:33:15 [shm_broadcast.py:264] vLLM message queue communication handle: Handle(local_reader_ranks=[0, 1], buffer_handle=(2, 10485760, 10, 'psm_ad6622e3'), local_subscribe_addr='ipc:///tmp/6eb1b784-bdf4-4c11-ba37-f222d94246a2', remote_subscribe_addr=None, remote_addr_ipv6=False)
WARNING 04-18 14:33:16 [utils.py:2444] Methods determine_num_available_blocks,device_config,get_cache_block_size_bytes,initialize_cache not implemented in <vllm.v1.worker.gpu_worker.Worker object at 0x7efc8e96ff20>
(VllmWorker rank=0 pid=182840) INFO 04-18 14:33:16 [shm_broadcast.py:264] vLLM message queue communication handle: Handle(local_reader_ranks=[0], buffer_handle=(1, 10485760, 10, 'psm_890e1d29'), local_subscribe_addr='ipc:///tmp/a95244a5-9599-4d5d-9fec-d82149cb0e70', remote_subscribe_addr=None, remote_addr_ipv6=False)
WARNING 04-18 14:33:17 [utils.py:2444] Methods determine_num_available_blocks,device_config,get_cache_block_size_bytes,initialize_cache not implemented in <vllm.v1.worker.gpu_worker.Worker object at 0x7efbdc5a7530>
(VllmWorker rank=1 pid=182914) INFO 04-18 14:33:17 [shm_broadcast.py:264] vLLM message queue communication handle: Handle(local_reader_ranks=[0], buffer_handle=(1, 10485760, 10, 'psm_c451570d'), local_subscribe_addr='ipc:///tmp/10da074b-b273-4437-a274-c18c12b52edd', remote_subscribe_addr=None, remote_addr_ipv6=False)
(VllmWorker rank=1 pid=182914) INFO 04-18 14:33:17 [utils.py:993] Found nccl from library libnccl.so.2
(VllmWorker rank=1 pid=182914) (VllmWorker rank=0 pid=182840) INFO 04-18 14:33:17 [pynccl.py:69] vLLM is using nccl==2.21.5
INFO 04-18 14:33:17 [utils.py:993] Found nccl from library libnccl.so.2
(VllmWorker rank=0 pid=182840) INFO 04-18 14:33:17 [pynccl.py:69] vLLM is using nccl==2.21.5
(VllmWorker rank=1 pid=182914) (VllmWorker rank=0 pid=182840) INFO 04-18 14:33:18 [custom_all_reduce_utils.py:244] reading GPU P2P access cache from /root/.cache/vllm/gpu_p2p_access_cache_for_0,1,2,3.json
INFO 04-18 14:33:18 [custom_all_reduce_utils.py:244] reading GPU P2P access cache from /root/.cache/vllm/gpu_p2p_access_cache_for_0,1,2,3.json
(VllmWorker rank=1 pid=182914) (VllmWorker rank=0 pid=182840) WARNING 04-18 14:33:18 [custom_all_reduce.py:146] Custom allreduce is disabled because your platform lacks GPU P2P capability or P2P test failed. To silence this warning, specify disable_custom_all_reduce=True explicitly.
WARNING 04-18 14:33:18 [custom_all_reduce.py:146] Custom allreduce is disabled because your platform lacks GPU P2P capability or P2P test failed. To silence this warning, specify disable_custom_all_reduce=True explicitly.
(VllmWorker rank=0 pid=182840) INFO 04-18 14:33:18 [shm_broadcast.py:264] vLLM message queue communication handle: Handle(local_reader_ranks=[1], buffer_handle=(1, 4194304, 6, 'psm_3de6487b'), local_subscribe_addr='ipc:///tmp/a6d31194-67b7-490c-a33e-5d3ae39750df', remote_subscribe_addr=None, remote_addr_ipv6=False)
(VllmWorker rank=0 pid=182840) (VllmWorker rank=1 pid=182914) INFO 04-18 14:33:18 [parallel_state.py:959] rank 0 in world size 2 is assigned as DP rank 0, PP rank 0, TP rank 0
INFO 04-18 14:33:18 [parallel_state.py:959] rank 1 in world size 2 is assigned as DP rank 0, PP rank 0, TP rank 1
(VllmWorker rank=1 pid=182914) (VllmWorker rank=0 pid=182840) INFO 04-18 14:33:18 [cuda.py:221] Using Flash Attention backend on V1 engine.
INFO 04-18 14:33:18 [cuda.py:221] Using Flash Attention backend on V1 engine.
(VllmWorker rank=1 pid=182914) (VllmWorker rank=0 pid=182840) INFO 04-18 14:33:18 [gpu_model_runner.py:1276] Starting to load model /home/08_vllm/qwen/Qwen2___5-7B...
INFO 04-18 14:33:18 [gpu_model_runner.py:1276] Starting to load model /home/08_vllm/qwen/Qwen2___5-7B...
(VllmWorker rank=0 pid=182840) WARNING 04-18 14:33:18 [topk_topp_sampler.py:69] FlashInfer is not available. Falling back to the PyTorch-native implementation of top-p & top-k sampling. For the best performance, please install FlashInfer.
(VllmWorker rank=1 pid=182914) WARNING 04-18 14:33:18 [topk_topp_sampler.py:69] FlashInfer is not available. Falling back to the PyTorch-native implementation of top-p & top-k sampling. For the best performance, please install FlashInfer.
Loading safetensors checkpoint shards:   0% Completed | 0/4 [00:00<?, ?it/s]
(VllmWorker rank=1 pid=182914) INFO 04-18 14:33:22 [loader.py:458] Loading weights took 4.17 seconds
(VllmWorker rank=0 pid=182840) INFO 04-18 14:33:22 [loader.py:458] Loading weights took 4.19 seconds
(VllmWorker rank=1 pid=182914) INFO 04-18 14:33:23 [gpu_model_runner.py:1291] Model loading took 7.1441 GiB and 4.411589 seconds
(VllmWorker rank=0 pid=182840) INFO 04-18 14:33:23 [gpu_model_runner.py:1291] Model loading took 7.1441 GiB and 4.425101 seconds
(VllmWorker rank=0 pid=182840) INFO 04-18 14:33:34 [backends.py:416] Using cache directory: /root/.cache/vllm/torch_compile_cache/b6232da3fe/rank_0_0 for vLLM's torch.compile
(VllmWorker rank=1 pid=182914) INFO 04-18 14:33:34 [backends.py:416] Using cache directory: /root/.cache/vllm/torch_compile_cache/b6232da3fe/rank_1_0 for vLLM's torch.compile
(VllmWorker rank=0 pid=182840) INFO 04-18 14:33:34 [backends.py:426] Dynamo bytecode transform time: 11.84 s
(VllmWorker rank=1 pid=182914) INFO 04-18 14:33:34 [backends.py:426] Dynamo bytecode transform time: 11.84 s
(VllmWorker rank=0 pid=182840) INFO 04-18 14:33:39 [backends.py:132] Cache the graph of shape None for later use
(VllmWorker rank=1 pid=182914) INFO 04-18 14:33:39 [backends.py:132] Cache the graph of shape None for later use
(VllmWorker rank=1 pid=182914) INFO 04-18 14:34:06 [backends.py:144] Compiling a graph for general shape takes 30.69 s
(VllmWorker rank=0 pid=182840) INFO 04-18 14:34:07 [backends.py:144] Compiling a graph for general shape takes 32.22 s
(VllmWorker rank=0 pid=182840) (VllmWorker rank=1 pid=182914) INFO 04-18 14:34:19 [monitor.py:33] torch.compile takes 44.07 s in total
INFO 04-18 14:34:19 [monitor.py:33] torch.compile takes 42.53 s in total
INFO 04-18 14:34:20 [kv_cache_utils.py:634] GPU KV cache size: 359,328 tokens
INFO 04-18 14:34:20 [kv_cache_utils.py:637] Maximum concurrency for 4,096 tokens per request: 87.73x
INFO 04-18 14:34:20 [kv_cache_utils.py:634] GPU KV cache size: 359,712 tokens
INFO 04-18 14:34:20 [kv_cache_utils.py:637] Maximum concurrency for 4,096 tokens per request: 87.82x
(VllmWorker rank=0 pid=182840) INFO 04-18 14:34:49 [gpu_model_runner.py:1626] Graph capturing finished in 29 secs, took 2.13 GiB
(VllmWorker rank=1 pid=182914) INFO 04-18 14:34:49 [gpu_model_runner.py:1626] Graph capturing finished in 29 secs, took 2.13 GiB
INFO 04-18 14:34:49 [core.py:163] init engine (profile, create kv cache, warmup model) took 86.61 seconds
INFO 04-18 14:34:49 [core_client.py:435] Core engine process 0 ready.
```

此时服务的 GPU 资源占用情况就如下图所示：

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504181435870.png)

可以根据自己实际加载模型的大小及硬件资源情况进行灵活的调整。

在加载好模型实例后，便可以进行远程模型服务的调用。发送数据并获取模型推理响应的接口是`.generate`方法，如下代码所示：

```python
outputs = llm.generate("你好，请你介绍一下你自己")

outputs
```

```Response
WARNING 04-18 14:42:31 [config.py:1177] Default sampling parameters have been overridden by the model's Hugging Face generation config recommended from the model creator. If this is not intended, please relaunch vLLM instance with `--generation-config vllm`.
Processed prompts:   0%|          | 0/1 [00:00<?, ?it/s, est. speed input: 0.00 toks/s, output: 0.00 toks/s]
[RequestOutput(request_id=0, prompt='你好，请你介绍一下你自己', prompt_token_ids=[108386, 37945, 56568, 109432, 107828], encoder_prompt=None, encoder_prompt_token_ids=None, prompt_logprobs=None, outputs=[CompletionOutput(index=0, text='。\n\n你好！我是一名大型的语言模型，基于深度学习技术训练而成。我可以回答各种问题，提供信息和帮助您解决一些问题。\n\n哦，你是针对人类的聊天机器人吗？\n\n没错，我可以和人类进行自然语言交互，以提供高质量的信息回答和智能聊天体验。', token_ids=[3407, 108386, 6313, 35946, 110124, 101951, 109824, 104949, 3837, 104210, 102217, 100134, 99361, 104034, 106042, 1773, 109944, 102104, 100646, 86119, 3837, 99553, 27369, 33108, 100364, 87026, 100638, 101883, 86119, 3407, 104170, 3837, 105043, 101092, 103971, 9370, 105292, 104354, 101037, 26850, 109012, 3837, 109944, 33108, 103971, 71817, 99795, 102064, 108221, 3837, 23031, 99553, 104129, 105427, 102104, 33108, 100168, 105292, 101904, 1773, 151643], cumulative_logprob=None, logprobs=None, finish_reason=stop, stop_reason=None)], finished=True, metrics=None, lora_request=None, num_cached_tokens=None, multi_modal_placeholders={})]
```

响应结果返回的是一个`RequestOutput`对象，通过`RequestOutput.outputs[0].text`可以获取到模型的推理结果。

```python
for output in outputs:
    generated_text = output.outputs[0].text
    print(f"Generated text: {generated_text!r}")
```

```Response
Generated text: '。\n\n你好！我是一名大型的语言模型，基于深度学习技术训练而成。我可以回答各种问题，提供信息和帮助您解决一些问题。\n\n哦，你是针对人类的聊天机器人吗？\n\n没错，我可以和人类进行自然语言交互，以提供高质量的信息回答和智能聊天体验。'
```

除了传入字符串，当输入一个列表时，.generate方法会执行批量推理，针对每一个prompt执行一次推理，并返回一个RequestOutput对象的列表。

```Response
text = [
    "你好，请你介绍一下你自己",
    "请问什么是机器学习",
    "请问如何理解大模型？"
]
```

```python
outputs = llm.generate(text)

outputs
```

```Response
Processed prompts:   0%|          | 0/3 [00:00<?, ?it/s, est. speed input: 0.00 toks/s, output: 0.00 toks/s]
[RequestOutput(request_id=1, prompt='你好，请你介绍一下你自己', prompt_token_ids=[108386, 37945, 56568, 109432, 107828], encoder_prompt=None, encoder_prompt_token_ids=None, prompt_logprobs=None, outputs=[CompletionOutput(index=0, text='。\n你好！很高兴认识你，我是一个人工智能助手，旨在提供各种信息和服务，帮助用户解决各种问题。你可以询问任何你想了解的事情，从天气到健康，从美食到旅游，从科技到生活，我都会尽我所能提供帮助和建议。如果我回答不了问题，我会不断学习，提升自己，以便更好地为你服务。有什么可以帮你的吗？', token_ids=[8997, 108386, 6313, 112169, 100720, 56568, 3837, 35946, 101909, 104455, 110498, 3837, 106166, 99553, 100646, 27369, 106510, 3837, 100364, 20002, 100638, 100646, 86119, 1773, 105048, 105396, 99885, 107409, 99794, 103976, 3837, 45181, 104307, 26939, 99722, 3837, 45181, 104365, 26939, 99790, 3837, 45181, 99602, 26939, 99424, 3837, 35946, 101938, 99739, 35946, 111079, 99553, 100364, 33108, 101898, 1773, 62244, 35946, 102104, 101195, 86119, 3837, 105351, 99607, 100134, 3837, 100341, 99283, 3837, 105920, 105344, 106184, 47874, 1773, 104139, 73670, 99663, 103929, 101037, 11319, 151643], cumulative_logprob=None, logprobs=None, finish_reason=stop, stop_reason=None)], finished=True, metrics=None, lora_request=None, num_cached_tokens=None, multi_modal_placeholders={}),
 RequestOutput(request_id=2, prompt='请问什么是机器学习', prompt_token_ids=[109194, 106582, 102182, 100134], encoder_prompt=None, encoder_prompt_token_ids=None, prompt_logprobs=None, outputs=[CompletionOutput(index=0, text='，它在金融行业中的应用是什么？ 机器学习是一种人工智能技术，它使计算机系统能够通过经验自动改进和适应。在金融行业中，机器学习被用于各种目的，如欺诈检测、信用评分、客户细分、风险评估等。机器学习算法可以从历史数据中学习模式并预测未来趋势，从而帮助金融机构更好地理解和管理风险。\n\n在欺诈检测方面，机器学习可以帮助银行和其他金融机构识别可疑交易并及时采取行动。在信用评分方面，机器学习可以帮助金融机构更好地理解借款人的信用状况，并提供更准确的风险评估。在客户细分方面，机器学习可以帮助金融机构更好地了解客户需求，并为客户提供个性化服务。在风险评估方面，机器学习可以帮助金融机构更好地了解市场风险、信用风险、流动性风险等，并采取相应措施来减轻风险。', token_ids=[3837, 99652, 18493, 100015, 99717, 101047, 99892, 102021, 11319, 220, 102182, 100134, 101158, 104455, 99361, 3837, 99652, 32555, 104564, 72448, 100006, 67338, 100034, 100756, 105023, 33108, 104117, 1773, 18493, 100015, 111658, 3837, 102182, 100134, 99250, 100751, 100646, 100466, 3837, 29524, 112894, 101978, 5373, 102156, 110683, 5373, 100017, 110837, 5373, 101052, 102086, 49567, 1773, 102182, 100134, 107018, 112255, 100022, 20074, 15946, 100134, 100144, 62926, 104538, 100353, 101226, 3837, 101982, 100364, 106107, 105344, 115167, 39352, 101052, 3407, 18493, 112894, 101978, 99522, 3837, 102182, 100134, 111728, 100358, 105504, 106107, 102450, 118910, 99886, 62926, 100667, 103975, 100675, 1773, 18493, 102156, 110683, 99522, 3837, 102182, 100134, 111728, 106107, 105344, 101128, 102735, 103947, 102156, 104215, 90395, 99553, 33126, 102188, 106066, 102086, 1773, 18493, 100017, 110837, 99522, 3837, 102182, 100134, 111728, 106107, 105344, 99794, 116932, 90395, 17714, 108064, 106412, 47874, 1773, 18493, 101052, 102086, 99522, 3837, 102182, 100134, 111728, 106107, 105344, 99794, 99345, 101052, 5373, 102156, 101052, 5373, 108070, 101052, 49567, 90395, 103975, 102487, 101082, 36407, 106104, 101052, 1773, 151643], cumulative_logprob=None, logprobs=None, finish_reason=stop, stop_reason=None)], finished=True, metrics=None, lora_request=None, num_cached_tokens=None, multi_modal_placeholders={}),
 RequestOutput(request_id=3, prompt='请问如何理解大模型？', prompt_token_ids=[109194, 100007, 101128, 26288, 104949, 11319], encoder_prompt=None, encoder_prompt_token_ids=None, prompt_logprobs=None, outputs=[CompletionOutput(index=0, text=' 如何理解大模型？\n\n大模型是指在计算机科学和人工智能领域中，具有大规模参数和容量的模型。这些模型通常用于处理大规模数据和复杂任务，例如自然语言处理、计算机视觉和机器学习等。\n\n大模型通常包括深度神经网络，例如卷积神经网络和循环神经网络，并且通过大量训练数据进行训练，以提高模型的准确性和鲁棒性。\n\n大模型的好处是可以处理大量数据和复杂任务，但是也会面临一些挑战，例如训练时间长和计算资源需求高。因此，研究人员一直在寻找优化大模型的方法，以便更高效地使用计算资源和处理大规模数据。\n\n总的来说，大模型是一种具有大规模参数和容量的模型，用于处理大规模数据和复杂任务，具有广泛的应用前景。\n\nchatglm的编码原理 ChatGLM是一种大型语言模型，它基于开源的GPT-3.5架构进行训练，具有出色的文本生成能力。在ChatGLM的编码原理中，主要包括以下几个方面：\n\n1. 模型结构：ChatGLM采用了Transformer架构，包括一个编码器和一个解码器。编码器负责将输入的文本序列转换成向量表示，解码器则负责将这个向量表示转换成文本，从而生成回答。\n\n2. 模型训练：ChatGLM采用了基于监督学习的方法进行训练。具体地，训练数据包括大量对人类对话的样本，每个样本包含问题和答案。模型对每个样本进行训练，尝试预测正确答案，从而优化模型的权重和参数。\n\n3. 模型量化：为了提高模型在实际应用中的性能，ChatGLM采用了模型量化技术，将模型参数从浮点数转换为更小的整数，从而减少模型的存储和计算开销。\n\n4. 模型融合：ChatGLM还采用了模型融合技术，将多个不同的模型进行融合，通过将它们的输出加权平均，来提高模型的准确性和稳定性。\n\n5. 模型推理：在实际应用中，模型需要进行推理和预测。ChatGLM采用了基于Softmax的模型推理方法，将解码器的输出转换为概率分布，从而预测下一个可能的文本序列。\n\n综上所述，ChatGLM的编码原理包括模型结构、模型训练、模型量化、模型融合和模型推理等方面，这些技术的综合应用使得ChatGLM具有高效的文本生成能力和优良的性能。\n\nGPT-3的原理和原理 PPT分享 GPT-3（Generative Pre-trained Transformer 3）是由OpenAI开发的一个大型自然语言处理模型，其原理主要是基于Transformer架构的生成预训练模型。下面是对这个问题的回答，同时附上GPT-3的原理和原理PPT分享。\n\nGPT-3的原理：\n\nGPT-3是一种生成预训练模型，它基于Transformer架构实现。该模型由一组编码器和解码器组成，能够进行自然语言处理任务，如文本生成、隐写分析、自动摘要等。GPT-3的训练阶段包括预训练和微调。在预训练阶段，模型使用大量无标签文本对进行自监督训练，再通过微调的过程中，将模型微调适配到特定任务。GPT-3具有多个单词编码的表示，每个单词被映射为不同维数的稠密向量。模型使用Attention机制捕捉单词之间的内部关系以及单词的上下文。模型的参数数量非常多，高达1750亿，这需要使用大量的硬件资源进行训练。\n\nGPT-3的原理PPT分享：\n\n下面是GPT-3原理的PPT分享（本文中的PPT提供PDF下载地址）：\n\nGPT-3原理PPT：https://www.cnblogs.com/BaoDingDuo/p/16017864.html#_Toc\n（在浏览器中打开以上链接，然后在页面右上角点击“下载”即可获取PPT）\n\nPPT内容主要介绍了GPT-3的架构、训练方法、预训练和微调等方面的内容，详细解释了GPT-3模型的原理和实现方式，对于理解GPT-3的工作原理非常有帮助。', token_ids=[69372, 98749, 101128, 26288, 104949, 26850, 26288, 104949, 104442, 18493, 104564, 99891, 33108, 104455, 100650, 15946, 3837, 100629, 105483, 32665, 33108, 106656, 9370, 104949, 1773, 100001, 104949, 102119, 100751, 54542, 105483, 20074, 33108, 102181, 88802, 3837, 77557, 99795, 102064, 54542, 5373, 104564, 104916, 33108, 102182, 100134, 49567, 3407, 26288, 104949, 102119, 100630, 102217, 102398, 71356, 3837, 77557, 100199, 99263, 102398, 71356, 33108, 101353, 102398, 71356, 90395, 100136, 67338, 100722, 104034, 20074, 71817, 104034, 3837, 23031, 100627, 104949, 9370, 102188, 105178, 100221, 102321, 33071, 3407, 26288, 104949, 111204, 105903, 54542, 100722, 20074, 33108, 102181, 88802, 3837, 100131, 103977, 101310, 101883, 104036, 3837, 77557, 104034, 20450, 45861, 33108, 100768, 85329, 100354, 44636, 1773, 101886, 3837, 113299, 105078, 104243, 103983, 26288, 104949, 104339, 3837, 105920, 33126, 102202, 29490, 37029, 100768, 85329, 33108, 54542, 105483, 20074, 3407, 116880, 3837, 26288, 104949, 101158, 100629, 105483, 32665, 33108, 106656, 9370, 104949, 3837, 100751, 54542, 105483, 20074, 33108, 102181, 88802, 3837, 100629, 100789, 106736, 102653, 3407, 9686, 42219, 9370, 112950, 105318, 12853, 3825, 44, 101158, 101951, 102064, 104949, 3837, 99652, 104210, 115462, 9370, 38, 2828, 12, 18, 13, 20, 106379, 71817, 104034, 3837, 100629, 110248, 108704, 43959, 99788, 1773, 18493, 15672, 3825, 44, 9370, 112950, 105318, 15946, 3837, 110800, 116420, 99522, 48443, 16, 13, 6567, 44401, 24300, 100166, 5122, 15672, 3825, 44, 107359, 46358, 106379, 3837, 100630, 46944, 112950, 31548, 33108, 46944, 49238, 16476, 31548, 1773, 112950, 31548, 100668, 44063, 31196, 9370, 108704, 116951, 105359, 12857, 69041, 32757, 51463, 3837, 49238, 16476, 31548, 46448, 100668, 44063, 99487, 69041, 32757, 51463, 105359, 12857, 108704, 3837, 101982, 43959, 102104, 3407, 17, 13, 6567, 44401, 24300, 104034, 5122, 15672, 3825, 44, 107359, 104210, 101116, 100134, 104339, 71817, 104034, 1773, 100398, 29490, 3837, 104034, 20074, 100630, 100722, 32664, 103971, 105051, 9370, 110241, 3837, 103991, 110241, 102298, 86119, 33108, 102349, 1773, 104949, 32664, 103991, 110241, 71817, 104034, 3837, 104482, 104538, 88991, 102349, 3837, 101982, 103983, 104949, 9370, 112142, 33108, 32665, 3407, 18, 13, 6567, 44401, 24300, 108048, 5122, 100012, 100627, 104949, 18493, 99912, 99892, 101047, 102111, 3837, 15672, 3825, 44, 107359, 104949, 108048, 99361, 3837, 44063, 104949, 32665, 45181, 100825, 27442, 8863, 105359, 17714, 33126, 30709, 9370, 63431, 8863, 3837, 101982, 101940, 104949, 9370, 105653, 33108, 100768, 29767, 91453, 3407, 19, 13, 6567, 44401, 24300, 101164, 5122, 15672, 3825, 44, 97706, 107359, 104949, 101164, 99361, 3837, 44063, 101213, 101970, 104949, 71817, 101164, 3837, 67338, 44063, 104017, 9370, 66017, 20929, 40981, 101200, 3837, 36407, 100627, 104949, 9370, 102188, 105178, 108239, 3407, 20, 13, 6567, 44401, 24300, 113272, 5122, 18493, 99912, 99892, 15946, 3837, 104949, 85106, 71817, 113272, 33108, 104538, 1773, 15672, 3825, 44, 107359, 104210, 30531, 2810, 9370, 104949, 113272, 39907, 3837, 44063, 49238, 16476, 31548, 9370, 66017, 105359, 17714, 103112, 101450, 3837, 101982, 104538, 108725, 87267, 9370, 108704, 116951, 3407, 99611, 17447, 113110, 3837, 15672, 3825, 44, 9370, 112950, 105318, 100630, 104949, 100166, 5373, 104949, 104034, 5373, 104949, 108048, 5373, 104949, 101164, 33108, 104949, 113272, 102159, 3837, 100001, 99361, 9370, 99799, 99892, 104193, 15672, 3825, 44, 100629, 110012, 108704, 43959, 106712, 105615, 9370, 102111, 3407, 38, 2828, 12, 18, 9370, 105318, 33108, 105318, 393, 2828, 93149, 479, 2828, 12, 18, 9909, 5531, 1388, 4968, 68924, 62379, 220, 18, 7552, 104625, 5002, 15469, 100013, 104111, 101951, 99795, 102064, 54542, 104949, 3837, 41146, 105318, 104312, 104210, 46358, 106379, 9370, 43959, 98841, 104034, 104949, 1773, 100431, 106273, 105073, 111423, 3837, 91572, 100093, 17447, 38, 2828, 12, 18, 9370, 105318, 33108, 105318, 47, 2828, 93149, 3407, 38, 2828, 12, 18, 9370, 105318, 48443, 38, 2828, 12, 18, 101158, 43959, 98841, 104034, 104949, 3837, 99652, 104210, 46358, 106379, 101884, 1773, 75882, 104949, 67071, 108940, 112950, 31548, 33108, 49238, 16476, 31548, 101286, 3837, 100006, 71817, 99795, 102064, 54542, 88802, 3837, 29524, 108704, 43959, 5373, 99707, 61443, 101042, 5373, 100756, 106208, 49567, 1773, 38, 2828, 12, 18, 9370, 104034, 100385, 100630, 98841, 104034, 33108, 48934, 47872, 1773, 18493, 98841, 104034, 100385, 3837, 104949, 37029, 100722, 42192, 105151, 108704, 32664, 71817, 35926, 101116, 104034, 3837, 87256, 67338, 48934, 47872, 104915, 3837, 44063, 104949, 48934, 47872, 99340, 54387, 26939, 105149, 88802, 1773, 38, 2828, 12, 18, 100629, 101213, 110011, 112950, 9370, 51463, 3837, 103991, 110011, 99250, 100261, 99759, 17714, 99604, 99479, 8863, 9370, 112705, 27641, 69041, 32757, 1773, 104949, 37029, 69329, 100674, 111781, 110011, 104186, 101979, 100145, 101034, 110011, 9370, 102285, 16744, 1773, 104949, 9370, 32665, 81800, 113370, 3837, 104930, 16, 22, 20, 15, 53356, 3837, 43288, 85106, 37029, 101514, 105433, 85329, 71817, 104034, 3407, 38, 2828, 12, 18, 9370, 105318, 47, 2828, 93149, 48443, 112918, 38, 2828, 12, 18, 105318, 9370, 47, 2828, 93149, 9909, 104817, 101047, 47, 2828, 99553, 23424, 62189, 46477, 7552, 48443, 38, 2828, 12, 18, 105318, 47, 2828, 5122, 2428, 1110, 2136, 22057, 53903, 905, 16276, 3441, 35, 287, 35, 23137, 4322, 14, 16, 21, 15, 16, 22, 23, 21, 19, 2564, 2, 62, 51, 509, 198, 9909, 18493, 110821, 15946, 104089, 70589, 82237, 3837, 101889, 18493, 36295, 64817, 17447, 63836, 72651, 2073, 62189, 854, 104180, 45912, 47, 2828, 27866, 47, 2828, 43815, 99558, 106661, 38, 2828, 12, 18, 9370, 106379, 5373, 104034, 39907, 5373, 98841, 104034, 33108, 48934, 47872, 102159, 104597, 3837, 100700, 104136, 34187, 38, 2828, 12, 18, 104949, 9370, 105318, 33108, 101884, 75768, 3837, 100002, 101128, 38, 2828, 12, 18, 104066, 105318, 99491, 18830, 100364, 1773, 151643], cumulative_logprob=None, logprobs=None, finish_reason=stop, stop_reason=None)], finished=True, metrics=None, lora_request=None, num_cached_tokens=None, multi_modal_placeholders={})]
```

```python
for output in outputs:
    prompt = output.prompt
    generated_text = output.outputs[0].text
    print(f"Prompt: {prompt!r}, Generated text: {generated_text!r}")
```

```Response
Prompt: '你好，请你介绍一下你自己', Generated text: '。\n你好！很高兴认识你，我是一个人工智能助手，旨在提供各种信息和服务，帮助用户解决各种问题。你可以询问任何你想了解的事情，从天气到健康，从美食到旅游，从科技到生活，我都会尽我所能提供帮助和建议。如果我回答不了问题，我会不断学习，提升自己，以便更好地为你服务。有什么可以帮你的吗？'
Prompt: '请问什么是机器学习', Generated text: '，它在金融行业中的应用是什么？ 机器学习是一种人工智能技术，它使计算机系统能够通过经验自动改进和适应。在金融行业中，机器学习被用于各种目的，如欺诈检测、信用评分、客户细分、风险评估等。机器学习算法可以从历史数据中学习模式并预测未来趋势，从而帮助金融机构更好地理解和管理风险。\n\n在欺诈检测方面，机器学习可以帮助银行和其他金融机构识别可疑交易并及时采取行动。在信用评分方面，机器学习可以帮助金融机构更好地理解借款人的信用状况，并提供更准确的风险评估。在客户细分方面，机器学习可以帮助金融机构更好地了解客户需求，并为客户提供个性化服务。在风险评估方面，机器学习可以帮助金融机构更好地了解市场风险、信用风险、流动性风险等，并采取相应措施来减轻风险。'
Prompt: '请问如何理解大模型？', Generated text: ' 如何理解大模型？\n\n大模型是指在计算机科学和人工智能领域中，具有大规模参数和容量的模型。这些模型通常用于处理大规模数据和复杂任务，例如自然语言处理、计算机视觉和机器学习等。\n\n大模型通常包括深度神经网络，例如卷积神经网络和循环神经网络，并且通过大量训练数据进行训练，以提高模型的准确性和鲁棒性。\n\n大模型的好处是可以处理大量数据和复杂任务，但是也会面临一些挑战，例如训练时间长和计算资源需求高。因此，研究人员一直在寻找优化大模型的方法，以便更高效地使用计算资源和处理大规模数据。\n\n总的来说，大模型是一种具有大规模参数和容量的模型，用于处理大规模数据和复杂任务，具有广泛的应用前景。\n\nchatglm的编码原理 ChatGLM是一种大型语言模型，它基于开源的GPT-3.5架构进行训练，具有出色的文本生成能力。在ChatGLM的编码原理中，主要包括以下几个方面：\n\n1. 模型结构：ChatGLM采用了Transformer架构，包括一个编码器和一个解码器。编码器负责将输入的文本序列转换成向量表示，解码器则负责将这个向量表示转换成文本，从而生成回答。\n\n2. 模型训练：ChatGLM采用了基于监督学习的方法进行训练。具体地，训练数据包括大量对人类对话的样本，每个样本包含问题和答案。模型对每个样本进行训练，尝试预测正确答案，从而优化模型的权重和参数。\n\n3. 模型量化：为了提高模型在实际应用中的性能，ChatGLM采用了模型量化技术，将模型参数从浮点数转换为更小的整数，从而减少模型的存储和计算开销。\n\n4. 模型融合：ChatGLM还采用了模型融合技术，将多个不同的模型进行融合，通过将它们的输出加权平均，来提高模型的准确性和稳定性。\n\n5. 模型推理：在实际应用中，模型需要进行推理和预测。ChatGLM采用了基于Softmax的模型推理方法，将解码器的输出转换为概率分布，从而预测下一个可能的文本序列。\n\n综上所述，ChatGLM的编码原理包括模型结构、模型训练、模型量化、模型融合和模型推理等方面，这些技术的综合应用使得ChatGLM具有高效的文本生成能力和优良的性能。\n\nGPT-3的原理和原理 PPT分享 GPT-3（Generative Pre-trained Transformer 3）是由OpenAI开发的一个大型自然语言处理模型，其原理主要是基于Transformer架构的生成预训练模型。下面是对这个问题的回答，同时附上GPT-3的原理和原理PPT分享。\n\nGPT-3的原理：\n\nGPT-3是一种生成预训练模型，它基于Transformer架构实现。该模型由一组编码器和解码器组成，能够进行自然语言处理任务，如文本生成、隐写分析、自动摘要等。GPT-3的训练阶段包括预训练和微调。在预训练阶段，模型使用大量无标签文本对进行自监督训练，再通过微调的过程中，将模型微调适配到特定任务。GPT-3具有多个单词编码的表示，每个单词被映射为不同维数的稠密向量。模型使用Attention机制捕捉单词之间的内部关系以及单词的上下文。模型的参数数量非常多，高达1750亿，这需要使用大量的硬件资源进行训练。\n\nGPT-3的原理PPT分享：\n\n下面是GPT-3原理的PPT分享（本文中的PPT提供PDF下载地址）：\n\nGPT-3原理PPT：https://www.cnblogs.com/BaoDingDuo/p/16017864.html#_Toc\n（在浏览器中打开以上链接，然后在页面右上角点击“下载”即可获取PPT）\n\nPPT内容主要介绍了GPT-3的架构、训练方法、预训练和微调等方面的内容，详细解释了GPT-3模型的原理和实现方式，对于理解GPT-3的工作原理非常有帮助。'
```

 以上就是在不修改任何模型加载和推理代码的情况下，快速使用vLLM 框架调用本地模型进行推理的方式。整个过程看并不是特别复杂。

 接下来我们再看推理类模型的在vLLM 离线推理API中的使用，这里我们以DeepSeek-R1-Distill-Qwen-7B为例。

```python
from vllm import LLM

llm = LLM(model="/home/08_vllm/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
          trust_remote_code=True,
          tensor_parallel_size=2,
          gpu_memory_utilization=0.8,
          max_model_len=4096,
)
```

```Response
INFO 04-18 15:02:59 [__init__.py:239] Automatically detected platform cuda.
INFO 04-18 15:03:09 [config.py:689] This model supports multiple tasks: {'classify', 'generate', 'reward', 'score', 'embed'}. Defaulting to 'generate'.
INFO 04-18 15:03:09 [config.py:1713] Defaulting to use mp for distributed inference
INFO 04-18 15:03:09 [config.py:1901] Chunked prefill is enabled with max_num_batched_tokens=8192.
INFO 04-18 15:03:11 [core.py:61] Initializing a V1 LLM engine (v0.8.4) with config: model='/home/08_vllm/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B', speculative_config=None, tokenizer='/home/08_vllm/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B', skip_tokenizer_init=False, tokenizer_mode=auto, revision=None, override_neuron_config=None, tokenizer_revision=None, trust_remote_code=True, dtype=torch.bfloat16, max_seq_len=4096, download_dir=None, load_format=LoadFormat.AUTO, tensor_parallel_size=2, pipeline_parallel_size=1, disable_custom_all_reduce=False, quantization=None, enforce_eager=False, kv_cache_dtype=auto,  device_config=cuda, decoding_config=DecodingConfig(guided_decoding_backend='auto', reasoning_backend=None), observability_config=ObservabilityConfig(show_hidden_metrics=False, otlp_traces_endpoint=None, collect_model_forward_time=False, collect_model_execute_time=False), seed=None, served_model_name=/home/08_vllm/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B, num_scheduler_steps=1, multi_step_stream_outputs=True, enable_prefix_caching=True, chunked_prefill_enabled=True, use_async_output_proc=True, disable_mm_preprocessor_cache=False, mm_processor_kwargs=None, pooler_config=None, compilation_config={"level":3,"custom_ops":["none"],"splitting_ops":["vllm.unified_attention","vllm.unified_attention_with_output"],"use_inductor":true,"compile_sizes":[],"use_cudagraph":true,"cudagraph_num_of_warmups":1,"cudagraph_capture_sizes":[512,504,496,488,480,472,464,456,448,440,432,424,416,408,400,392,384,376,368,360,352,344,336,328,320,312,304,296,288,280,272,264,256,248,240,232,224,216,208,200,192,184,176,168,160,152,144,136,128,120,112,104,96,88,80,72,64,56,48,40,32,24,16,8,4,2,1],"max_capture_size":512}
WARNING 04-18 15:03:11 [multiproc_worker_utils.py:306] Reducing Torch parallelism from 40 threads to 1 to avoid unnecessary CPU contention. Set OMP_NUM_THREADS in the external environment to tune this value as needed.
INFO 04-18 15:03:11 [shm_broadcast.py:264] vLLM message queue communication handle: Handle(local_reader_ranks=[0, 1], buffer_handle=(2, 10485760, 10, 'psm_e08c358b'), local_subscribe_addr='ipc:///tmp/197feaaf-8416-4196-849f-5924a6a3bf6b', remote_subscribe_addr=None, remote_addr_ipv6=False)
WARNING 04-18 15:03:11 [utils.py:2444] Methods determine_num_available_blocks,device_config,get_cache_block_size_bytes,initialize_cache not implemented in <vllm.v1.worker.gpu_worker.Worker object at 0x7f52d8f08950>
(VllmWorker rank=0 pid=259237) INFO 04-18 15:03:11 [shm_broadcast.py:264] vLLM message queue communication handle: Handle(local_reader_ranks=[0], buffer_handle=(1, 10485760, 10, 'psm_4a557edc'), local_subscribe_addr='ipc:///tmp/46260376-b78e-4a4a-b5b9-b029768e727a', remote_subscribe_addr=None, remote_addr_ipv6=False)
WARNING 04-18 15:03:12 [utils.py:2444] Methods determine_num_available_blocks,device_config,get_cache_block_size_bytes,initialize_cache not implemented in <vllm.v1.worker.gpu_worker.Worker object at 0x7f5226f4fce0>
(VllmWorker rank=1 pid=259276) INFO 04-18 15:03:12 [shm_broadcast.py:264] vLLM message queue communication handle: Handle(local_reader_ranks=[0], buffer_handle=(1, 10485760, 10, 'psm_c2aa03da'), local_subscribe_addr='ipc:///tmp/bffaf953-04b1-4a07-8dce-f49734214da2', remote_subscribe_addr=None, remote_addr_ipv6=False)
(VllmWorker rank=1 pid=259276) INFO 04-18 15:03:13 [utils.py:993] Found nccl from library libnccl.so.2
(VllmWorker rank=1 pid=259276) INFO 04-18 15:03:13 [pynccl.py:69] vLLM is using nccl==2.21.5
(VllmWorker rank=0 pid=259237) INFO 04-18 15:03:13 [utils.py:993] Found nccl from library libnccl.so.2
(VllmWorker rank=0 pid=259237) INFO 04-18 15:03:13 [pynccl.py:69] vLLM is using nccl==2.21.5
(VllmWorker rank=1 pid=259276) (VllmWorker rank=0 pid=259237) INFO 04-18 15:03:13 [custom_all_reduce_utils.py:244] reading GPU P2P access cache from /root/.cache/vllm/gpu_p2p_access_cache_for_0,1,2,3.json
INFO 04-18 15:03:13 [custom_all_reduce_utils.py:244] reading GPU P2P access cache from /root/.cache/vllm/gpu_p2p_access_cache_for_0,1,2,3.json
(VllmWorker rank=1 pid=259276) (VllmWorker rank=0 pid=259237) WARNING 04-18 15:03:13 [custom_all_reduce.py:146] Custom allreduce is disabled because your platform lacks GPU P2P capability or P2P test failed. To silence this warning, specify disable_custom_all_reduce=True explicitly.
WARNING 04-18 15:03:13 [custom_all_reduce.py:146] Custom allreduce is disabled because your platform lacks GPU P2P capability or P2P test failed. To silence this warning, specify disable_custom_all_reduce=True explicitly.
(VllmWorker rank=0 pid=259237) INFO 04-18 15:03:13 [shm_broadcast.py:264] vLLM message queue communication handle: Handle(local_reader_ranks=[1], buffer_handle=(1, 4194304, 6, 'psm_fbf72858'), local_subscribe_addr='ipc:///tmp/b8931c28-211e-4caa-ad9b-39f1db1e7ad6', remote_subscribe_addr=None, remote_addr_ipv6=False)
(VllmWorker rank=0 pid=259237) (VllmWorker rank=1 pid=259276) INFO 04-18 15:03:13 [parallel_state.py:959] rank 0 in world size 2 is assigned as DP rank 0, PP rank 0, TP rank 0
INFO 04-18 15:03:13 [parallel_state.py:959] rank 1 in world size 2 is assigned as DP rank 0, PP rank 0, TP rank 1
(VllmWorker rank=1 pid=259276) (VllmWorker rank=0 pid=259237) INFO 04-18 15:03:13 [cuda.py:221] Using Flash Attention backend on V1 engine.
INFO 04-18 15:03:13 [cuda.py:221] Using Flash Attention backend on V1 engine.
(VllmWorker rank=1 pid=259276) (VllmWorker rank=0 pid=259237) INFO 04-18 15:03:13 [gpu_model_runner.py:1276] Starting to load model /home/08_vllm/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B...
INFO 04-18 15:03:13 [gpu_model_runner.py:1276] Starting to load model /home/08_vllm/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B...
(VllmWorker rank=0 pid=259237) (VllmWorker rank=1 pid=259276) WARNING 04-18 15:03:13 [topk_topp_sampler.py:69] FlashInfer is not available. Falling back to the PyTorch-native implementation of top-p & top-k sampling. For the best performance, please install FlashInfer.
WARNING 04-18 15:03:13 [topk_topp_sampler.py:69] FlashInfer is not available. Falling back to the PyTorch-native implementation of top-p & top-k sampling. For the best performance, please install FlashInfer.
Loading safetensors checkpoint shards:   0% Completed | 0/2 [00:00<?, ?it/s]
(VllmWorker rank=1 pid=259276) INFO 04-18 15:03:18 [loader.py:458] Loading weights took 4.54 seconds
(VllmWorker rank=0 pid=259237) INFO 04-18 15:03:18 [loader.py:458] Loading weights took 4.77 seconds
(VllmWorker rank=1 pid=259276) INFO 04-18 15:03:18 [gpu_model_runner.py:1291] Model loading took 7.1441 GiB and 4.815520 seconds
(VllmWorker rank=0 pid=259237) INFO 04-18 15:03:18 [gpu_model_runner.py:1291] Model loading took 7.1441 GiB and 5.042643 seconds
(VllmWorker rank=1 pid=259276) INFO 04-18 15:03:30 [backends.py:416] Using cache directory: /root/.cache/vllm/torch_compile_cache/0047d2f046/rank_1_0 for vLLM's torch.compile
(VllmWorker rank=1 pid=259276) INFO 04-18 15:03:30 [backends.py:426] Dynamo bytecode transform time: 11.14 s
(VllmWorker rank=0 pid=259237) INFO 04-18 15:03:30 [backends.py:416] Using cache directory: /root/.cache/vllm/torch_compile_cache/0047d2f046/rank_0_0 for vLLM's torch.compile
(VllmWorker rank=0 pid=259237) INFO 04-18 15:03:30 [backends.py:426] Dynamo bytecode transform time: 11.51 s
(VllmWorker rank=1 pid=259276) INFO 04-18 15:03:30 [backends.py:115] Directly load the compiled graph for shape None from the cache
(VllmWorker rank=0 pid=259237) INFO 04-18 15:03:31 [backends.py:115] Directly load the compiled graph for shape None from the cache
(VllmWorker rank=0 pid=259237) INFO 04-18 15:03:37 [monitor.py:33] torch.compile takes 11.51 s in total
(VllmWorker rank=1 pid=259276) INFO 04-18 15:03:37 [monitor.py:33] torch.compile takes 11.14 s in total
INFO 04-18 15:03:40 [kv_cache_utils.py:634] GPU KV cache size: 367,968 tokens
INFO 04-18 15:03:40 [kv_cache_utils.py:637] Maximum concurrency for 4,096 tokens per request: 89.84x
INFO 04-18 15:03:40 [kv_cache_utils.py:634] GPU KV cache size: 368,352 tokens
INFO 04-18 15:03:40 [kv_cache_utils.py:637] Maximum concurrency for 4,096 tokens per request: 89.93x
(VllmWorker rank=0 pid=259237) (VllmWorker rank=1 pid=259276) INFO 04-18 15:04:06 [gpu_model_runner.py:1626] Graph capturing finished in 26 secs, took 2.13 GiB
INFO 04-18 15:04:06 [gpu_model_runner.py:1626] Graph capturing finished in 26 secs, took 2.13 GiB
INFO 04-18 15:04:06 [core.py:163] init engine (profile, create kv cache, warmup model) took 47.49 seconds
INFO 04-18 15:04:06 [core_client.py:435] Core engine process 0 ready.
```

其显存占用情况与Qwen2.5:7b 并无差异：

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504181456307.png)

接下来我们进行推理模型的调用测试。

```python
outputs = llm.generate("你好，请你介绍一下你自己")

outputs
```

```Response
Processed prompts:   0%|          | 0/1 [00:00<?, ?it/s, est. speed input: 0.00 toks/s, output: 0.00 toks/s]
[RequestOutput(request_id=11, prompt='你好，请你介绍一下你自己', prompt_token_ids=[151646, 108386, 37945, 56568, 109432, 107828], encoder_prompt=None, encoder_prompt_token_ids=None, prompt_logprobs=None, outputs=[CompletionOutput(index=0, text='！\n\n好的，用户让我介绍一下我自己，我得先理清楚自己现在的情况', token_ids=[17701, 99692, 3837, 20002, 104029, 109432, 106749, 3837, 35946, 49828, 60726, 21887, 101222, 99283, 99601, 102072], cumulative_logprob=None, logprobs=None, finish_reason=length, stop_reason=None)], finished=True, metrics=None, lora_request=None, num_cached_tokens=None, multi_modal_placeholders={})]
```

```python
outputs = llm.generate("请问什么是黑洞？")

outputs
```

```Response
Processed prompts:   0%|          | 0/1 [00:00<?, ?it/s, est. speed input: 0.00 toks/s, output: 0.00 toks/s]
[RequestOutput(request_id=15, prompt='请问什么是黑洞？', prompt_token_ids=[151646, 109194, 106582, 118718, 11319], encoder_prompt=None, encoder_prompt_token_ids=None, prompt_logprobs=None, outputs=[CompletionOutput(index=0, text='黑洞的形成条件是什么？它有什么特性呢？\n\n好的，我需要详细', token_ids=[118718, 9370, 101894, 76095, 102021, 11319, 99652, 104139, 105539, 101036, 26850, 99692, 3837, 35946, 85106, 100700], cumulative_logprob=None, logprobs=None, finish_reason=length, stop_reason=None)], finished=True, metrics=None, lora_request=None, num_cached_tokens=None, multi_modal_placeholders={})]
```

```python
for output in outputs:
    generated_text = output.outputs[0].text
    print(f"Generated text: {generated_text!r}")
```

```Response
Generated text: '黑洞的形成条件是什么？它有什么特性呢？\n\n好的，我需要详细'
```

这里能看到从返回结果上看，当改用了推理模型后，其返回的text字段中的内容会被截断的非常短，这是因为推理模型会包含思考过程，所以需要对generate接口要求输出的Token数需求更大，因此这里要引入一个SamplingParams 的概念。默认情况下，vLLM 的离线推理API会使用模型原生定义的采样参数，也就是本地存储权重中的generation_config.json文件中的配置。

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504181521542.png)

当然，如果某些开源的模型权重中没有提供该文件，vLLM会根据其定义的SamplingParams类自动指定默认值。其源码位置如下所示：

![](https://muyu20241105.oss-cn-beijing.aliyuncs.com/images/202504181524308.png)

其中包含的全部可定义参数如下表所示:

| 参数                            | 描述                                                                                                                                                                                                                                                              |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `n`                             | 要返回的输出序列数量。                                                                                                                                                                                                                                            |
| `best_of`                       | 从提示生成的输出序列数量。从这些 `best_of` 序列中返回前 `n` 个序列。`best_of` 必须大于或等于 `n`。默认情况下，`best_of` 设置为 `n`。警告：此功能仅在 V0 中支持。                                                                                                  |
| `presence_penalty`              | 浮点数，根据新 token 是否出现在已生成的文本中对其进行惩罚。值 > 0 鼓励模型使用新 token，值 < 0 鼓励模型重复 token。                                                                                                                                               |
| `frequency_penalty`             | 浮点数，根据新 token 在已生成文本中的频率对其进行惩罚。值 > 0 鼓励模型使用新 token，值 < 0 鼓励模型重复 token。                                                                                                                                                   |
| `repetition_penalty`            | 浮点数，根据新 token 是否出现在提示和已生成文本中对其进行惩罚。值 > 1 鼓励模型使用新 token，值 < 1 鼓励模型重复 token。                                                                                                                                           |
| `temperature`                   | 浮点数，控制采样的随机性。较低的值使模型更确定，较高的值使模型更随机。零表示贪婪采样。                                                                                                                                                                            |
| `top_p`                         | 浮点数，控制考虑的 top token 的累积概率。必须在 (0, 1] 之间。设置为 1 以考虑所有 token。                                                                                                                                                                          |
| `top_k`                         | 整数，控制考虑的 top token 数量。设置为 -1 以考虑所有 token。                                                                                                                                                                                                     |
| `min_p`                         | 浮点数，表示相对于最可能 token 的概率，考虑 token 的最小概率。必须在 [0, 1] 之间。设置为 0 以禁用此功能。                                                                                                                                                         |
| `seed`                          | 用于生成的随机种子。                                                                                                                                                                                                                                              |
| `stop`                          | 停止生成的字符串列表。当生成这些字符串时，生成将停止。返回的输出将不包含停止字符串。                                                                                                                                                                              |
| `stop_token_ids`                | 停止生成的 token 列表。当生成这些 token 时，生成将停止。返回的输出将包含停止 token，除非停止 token 是特殊 token。                                                                                                                                                 |
| `bad_words`                     | 不允许生成的单词列表。更准确地说，只有当下一个生成的 token 可以完成序列时，才不允许对应 token 序列的最后一个 token。                                                                                                                                              |
| `include_stop_str_in_output`    | 是否在输出文本中包含停止字符串。默认值为 False。                                                                                                                                                                                                                  |
| `ignore_eos`                    | 是否忽略 EOS token，并在生成 EOS token 后继续生成 token。                                                                                                                                                                                                         |
| `max_tokens`                    | 每个输出序列生成的最大 token 数量。                                                                                                                                                                                                                               |
| `min_tokens`                    | 每个输出序列生成的最小 token 数量，直到可以生成 EOS 或 stop_token_ids。                                                                                                                                                                                           |
| `logprobs`                      | 每个输出 token 返回的 log 概率数量。当设置为 None 时，不返回概率。如果设置为非 None 值，结果将包括指定数量的最可能 token 的 log 概率，以及选择的 token。注意，实施遵循 OpenAI API：API 将始终返回采样 token 的 log 概率，因此响应中可能有多达 logprobs+1 个元素。 |
| `prompt_logprobs`               | 每个提示 token 返回的 log 概率数量。                                                                                                                                                                                                                              |
| `detokenize`                    | 是否对输出进行反分词。默认值为 True。                                                                                                                                                                                                                             |
| `skip_special_tokens`           | 是否在输出中跳过特殊 token。                                                                                                                                                                                                                                      |
| `spaces_between_special_tokens` | 是否在输出中的特殊 token 之间添加空格。默认值为 True。                                                                                                                                                                                                            |
| `logits_processors`             | 修改 logits 的函数列表，基于先前生成的 token，并可选地将提示 token 作为第一个参数。                                                                                                                                                                               |
| `truncate_prompt_tokens`        | 如果设置为整数 k，将仅使用提示的最后 k 个 token（即左截断）。默认值为 None（即不截断）。                                                                                                                                                                          |
| `guided_decoding`               | 如果提供，引擎将根据这些参数构建引导解码 logits 处理器。默认值为 None。                                                                                                                                                                                           |
| `logit_bias`                    | 如果提供，引擎将构建一个应用这些 logit 偏置的 logits 处理器。默认值为 None。                                                                                                                                                                                      |
| `allowed_token_ids`             | 如果提供，引擎将构建一个 logits 处理器，仅保留给定 token ids 的分数。默认值为 None。                                                                                                                                                                              |
| `extra_args`                    | 任意额外参数，可供自定义采样实现使用。未被任何树内采样实现使用。                                                                                                                                                                                                  |

所以与Qwen2.5:7b不同的是，DeepSeek-R1-Distill-Qwen-7B 没有设置max_tokens，从而导致会用vLLM的默认值。因此，对大模型推理生成定制化的配置方法，则是按照上表中的参数说明定义sampling_params实例，设置更长的max_tokens参数，因为推理模型包含思考过程，需要输出更多的 Token，如下所示：

```python
# vllm_model.py
from vllm import SamplingParams

# 根据 DeepSeek 官方的建议，temperature应在 0.5-0.7，推荐 0.6 
sampling_params = SamplingParams(max_tokens=8192, temperature=0.6, top_p=0.95)
```

构建好自定义的采样参数后，在generate方法中与输入的问题同步传递，代码如下：

```python
outputs = llm.generate("你好，请你介绍一下你自己。", sampling_params=sampling_params)

outputs
```

```Response
Processed prompts:   0%|          | 0/1 [00:00<?, ?it/s, est. speed input: 0.00 toks/s, output: 0.00 toks/s]
[RequestOutput(request_id=16, prompt='你好，请你介绍一下你自己。', prompt_token_ids=[151646, 108386, 37945, 56568, 109432, 107828, 1773], encoder_prompt=None, encoder_prompt_token_ids=None, prompt_logprobs=None, outputs=[CompletionOutput(index=0, text='\n\n\n好，我现在要回答用户的问题：“你好，请你介绍一下你自己。” 用户可能是在进行自我介绍，或者想了解我作为AI的特点。首先，我需要明确用户的需求，他们可能想要了解我的功能、特点，或者使用场景。\n\n接下来，我应该从多个方面来介绍自己，比如我的功能、使用方法、适用场景、优势以及未来的发展。这样可以让用户全面了解我，同时也能引导他们如何更好地使用我。\n\n在结构上，可以分为几个部分：功能简介、使用方法、适用场景、优势与特点、未来发展。这样条理清晰，用户也容易理解。\n\n另外，语言要简洁明了，避免过于技术化，让所有用户都能轻松理解。同时，加入一些鼓励性的语言，比如邀请用户提出问题，这样能增加互动感。\n\n最后，检查一下内容是否全面，有没有遗漏的重要信息，确保用户能获得有价值的信息。这样回答应该能满足用户的需求，帮助他们更好地了解我。\n</think>\n\n你好！我是一个人工智能助手，由中国的深度求索（DeepSeek）公司独立开发，基于DeepSeek大语言模型构建。我擅长通过思考来帮您解答复杂的数学、代码、逻辑推理等理工类问题，同时也能提供一些建议和信息。如果有什么问题，欢迎随时向我提问！', token_ids=[1406, 52801, 3837, 107520, 30534, 102104, 20002, 103936, 36987, 108386, 37945, 56568, 109432, 107828, 32945, 50042, 87267, 101219, 71817, 104049, 100157, 3837, 100631, 99172, 99794, 35946, 100622, 15469, 105117, 1773, 101140, 3837, 35946, 85106, 100692, 20002, 104378, 3837, 99650, 87267, 103945, 99794, 97611, 98380, 5373, 100772, 3837, 100631, 37029, 102122, 3407, 104326, 3837, 35946, 99730, 45181, 101213, 99522, 36407, 100157, 99283, 3837, 101912, 97611, 98380, 5373, 37029, 39907, 5373, 105255, 102122, 5373, 100661, 101034, 100353, 103949, 1773, 99654, 107366, 20002, 100011, 99794, 35946, 3837, 91572, 104425, 104042, 99650, 100007, 105344, 37029, 35946, 3407, 18493, 100166, 17447, 3837, 73670, 102239, 100204, 99659, 5122, 98380, 102335, 5373, 37029, 39907, 5373, 105255, 102122, 5373, 100661, 57218, 100772, 5373, 113053, 1773, 99654, 38989, 21887, 104542, 3837, 20002, 74763, 100047, 101128, 3407, 101948, 3837, 102064, 30534, 110485, 30858, 34187, 3837, 101153, 102767, 99361, 32108, 3837, 99258, 55338, 20002, 104297, 104261, 101128, 1773, 91572, 3837, 101963, 101883, 104125, 104196, 102064, 3837, 101912, 104331, 20002, 101080, 86119, 3837, 99654, 26232, 100649, 104199, 98650, 3407, 100161, 3837, 101071, 100158, 43815, 64471, 100011, 3837, 104710, 114078, 101945, 27369, 3837, 103944, 20002, 26232, 100350, 111185, 105427, 1773, 99654, 102104, 99730, 112809, 20002, 104378, 3837, 100364, 99650, 105344, 99794, 35946, 8997, 151649, 271, 108386, 6313, 35946, 101909, 104455, 110498, 3837, 67071, 105538, 102217, 30918, 50984, 9909, 33464, 39350, 7552, 73218, 102024, 100013, 3837, 104210, 33464, 39350, 26288, 102064, 104949, 104004, 1773, 35946, 107618, 67338, 104107, 36407, 99663, 87026, 106185, 106888, 104552, 5373, 46100, 5373, 104913, 113272, 49567, 103538, 21515, 86119, 3837, 91572, 104425, 99553, 14777, 6684, 31338, 96422, 33108, 27369, 1773, 62244, 104139, 86119, 3837, 100437, 102422, 69041, 35946, 107666, 6313, 151643], cumulative_logprob=None, logprobs=None, finish_reason=stop, stop_reason=None)], finished=True, metrics=None, lora_request=None, num_cached_tokens=None, multi_modal_placeholders={})]
```

```Python
outputs = llm.generate("你好，请问什么是黑洞？", sampling_params=sampling_params)

outputs
```

```Response
Processed prompts:   0%|          | 0/1 [00:00<?, ?it/s, est. speed input: 0.00 toks/s, output: 0.00 toks/s]
[RequestOutput(request_id=17, prompt='你好，请问什么是黑洞？', prompt_token_ids=[151646, 108386, 37945, 56007, 106582, 118718, 11319], encoder_prompt=None, encoder_prompt_token_ids=None, prompt_logprobs=None, outputs=[CompletionOutput(index=0, text='为什么会有黑洞？这是不是说宇宙中存在一种极端的引力场，使得任何物体都无法逃脱它的引力束缚？\n\n好的，我需要详细回答这个问题。首先，我需要解释什么是黑洞，然后说明为什么会有黑洞，最后回答关于引力场的问题。确保语言通俗易懂，避免使用过于专业的术语，但如果有需要，可以适当解释。\n\n好的，我先从黑洞的定义开始。黑洞是一个引力极其强大的区域，以至于没有任何物质或光能能够逃脱它的引力束缚。接下来，我需要解释为什么会有黑洞。这可能涉及到引力的作用、时空的弯曲，以及在极端条件下引力如何变得如此强。\n\n最后，我要确认我的回答是否准确，确保没有错误。如果有需要，我可以调整解释，使其更清晰易懂。\n\n好的，现在开始组织语言，确保每个部分都涵盖到，并且逻辑连贯。\n</think>\n\n黑洞是宇宙中极端存在的引力区域，其中引力强到连光都无法逃脱。它们通常由大质量恒星在生命末期形成，通过引力坍缩最终形成奇点，周围被所谓的“事件视界”所包围。这一现象基于广义相对论中对时空弯曲的理解，当物质质量足够大时，时空的弯曲程度超过了一定限度，引力场变得无法对抗，导致了黑洞的形成。这一过程解释了为什么黑洞存在以及它们为何具有如此强大的引力场。', token_ids=[100678, 104330, 118718, 11319, 100346, 99520, 36587, 105339, 15946, 47606, 101053, 107601, 9370, 117794, 82224, 3837, 104193, 99885, 109840, 114279, 118260, 104121, 117794, 113706, 26850, 99692, 3837, 35946, 85106, 100700, 102104, 105073, 1773, 101140, 3837, 35946, 85106, 104136, 106582, 118718, 3837, 101889, 66394, 100678, 104330, 118718, 3837, 100161, 102104, 101888, 117794, 82224, 103936, 1773, 103944, 102064, 116336, 86744, 100272, 3837, 101153, 37029, 102767, 104715, 116925, 3837, 77288, 107055, 85106, 3837, 73670, 102618, 104136, 3407, 99692, 3837, 35946, 60726, 45181, 118718, 9370, 91282, 55286, 1773, 118718, 101909, 117794, 106471, 104795, 101065, 3837, 111395, 105283, 101252, 57191, 99225, 26232, 100006, 118260, 104121, 117794, 113706, 1773, 104326, 3837, 35946, 85106, 104136, 100678, 104330, 118718, 1773, 43288, 87267, 109228, 117794, 104149, 5373, 109113, 9370, 112263, 3837, 101034, 18493, 107601, 107219, 117794, 100007, 101197, 101073, 99193, 3407, 100161, 3837, 104515, 81167, 97611, 102104, 64471, 102188, 3837, 103944, 80443, 32100, 1773, 107055, 85106, 3837, 109944, 101921, 104136, 3837, 102989, 33126, 104542, 86744, 100272, 3407, 99692, 3837, 99601, 55286, 99877, 102064, 3837, 103944, 103991, 99659, 71268, 102994, 26939, 90395, 100136, 104913, 54926, 100116, 8997, 151649, 271, 118718, 20412, 105339, 15946, 107601, 102670, 117794, 101065, 3837, 90919, 117794, 99193, 26939, 54926, 99225, 114279, 118260, 1773, 104017, 102119, 67071, 26288, 99570, 101261, 77419, 18493, 100702, 100072, 22704, 101894, 3837, 67338, 117794, 119659, 99872, 103941, 101894, 99309, 27442, 3837, 102385, 99250, 105381, 2073, 57621, 57452, 97120, 854, 31838, 109423, 1773, 100147, 102060, 104210, 80942, 64559, 101162, 67831, 15946, 32664, 109113, 112263, 108894, 3837, 39165, 101252, 99570, 101447, 26288, 13343, 3837, 109113, 9370, 112263, 100069, 100381, 99593, 22382, 103304, 3837, 117794, 82224, 101197, 101068, 107126, 3837, 100673, 34187, 118718, 9370, 101894, 1773, 100147, 100178, 104136, 34187, 100678, 118718, 47606, 101034, 104017, 104499, 100629, 101073, 104795, 117794, 82224, 1773, 151643], cumulative_logprob=None, logprobs=None, finish_reason=stop, stop_reason=None)], finished=True, metrics=None, lora_request=None, num_cached_tokens=None, multi_modal_placeholders={})]
```

这里能够明显看到是可以正常的返回推理过程和最终的推理结果的全部内容了。但是从结果上看，很难区分哪些是推理过程，哪些是推理的最红结果，因此，在vLLM框架下使用推理模型时，一个比较有效的技巧是每个输入的文本问题，都要以<think>\n 结尾，便可以直接改善推理模型返回的数据格式，如下代码所示：

```python
prompts = [
    "你好， 请你介绍一下你自己<think>\n",
]

outputs = llm.generate(prompts, sampling_params=sampling_params)
outputs
```

```python
Processed prompts:   0%|          | 0/1 [00:00<?, ?it/s, est. speed input: 0.00 toks/s, output: 0.00 toks/s]
[RequestOutput(request_id=19, prompt='你好， 请你介绍一下你自己<think>\n', prompt_token_ids=[151646, 108386, 3837, 220, 112720, 109432, 107828, 151648, 198], encoder_prompt=None, encoder_prompt_token_ids=None, prompt_logprobs=None, outputs=[CompletionOutput(index=0, text='您好！我是由中国的深度求索（DeepSeek）公司开发的智能助手DeepSeek-R1。如您有任何任何问题，我会尽我所能为您提供帮助。\n</think>\n\n您好！我是由中国的深度求索（DeepSeek）公司开发的智能助手DeepSeek-R1。如您有任何任何问题，我会尽我所能为您提供帮助。', token_ids=[111308, 6313, 104198, 67071, 105538, 102217, 30918, 50984, 9909, 33464, 39350, 7552, 73218, 100013, 9370, 100168, 110498, 33464, 39350, 10911, 16, 1773, 29524, 87026, 110117, 99885, 86119, 3837, 105351, 99739, 35946, 111079, 113445, 100364, 8997, 151649, 271, 111308, 6313, 104198, 67071, 105538, 102217, 30918, 50984, 9909, 33464, 39350, 7552, 73218, 100013, 9370, 100168, 110498, 33464, 39350, 10911, 16, 1773, 29524, 87026, 110117, 99885, 86119, 3837, 105351, 99739, 35946, 111079, 113445, 100364, 1773, 151643], cumulative_logprob=None, logprobs=None, finish_reason=stop, stop_reason=None)], finished=True, metrics=None, lora_request=None, num_cached_tokens=None, multi_modal_placeholders={})]
```

```python
prompts = [
    "帮我制定一个北京的三天旅游计划<think>\n",
]

outputs = llm.generate(prompts, sampling_params=sampling_params)
outputs
```

```Response
Processed prompts:   0%|          | 0/1 [00:00<?, ?it/s, est. speed input: 0.00 toks/s, output: 0.00 toks/s]
[RequestOutput(request_id=20, prompt='帮我制定一个北京的三天旅游计划<think>\n', prompt_token_ids=[151646, 108965, 104016, 46944, 68990, 9370, 106635, 99790, 101039, 151648, 198], encoder_prompt=None, encoder_prompt_token_ids=None, prompt_logprobs=None, outputs=[CompletionOutput(index=0, text='嗯，用户让我帮他制定一个北京的三天旅游计划。好的，首先我得考虑他可能的行程安排。北京是一个非常著名的旅游城市，有很多景点可以去，但三天时间有限，所以得合理安排。\n\n首先，我应该考虑第一天到哪里比较合适。一般来说，第一天可以安排比较经典的景点，比如故宫，因为这是北京的标志性景点，很多人都想去。然后，故宫附近有很多美食，比如簋街，可以安排中午吃午饭，晚上逛逛附近的商业街，比如三里屯或者南锣鼓巷，这样晚上活动比较丰富。\n\n第二天的话，可以考虑一些自然景观，比如香山公园，那里有美丽的红叶，适合登高望远，欣赏秋天的景色。下午去颐和园，那里的昆明湖和万人大观楼都是不错的景点，晚上可以在圆明园附近吃晚饭，那里有很多小吃。\n\n第三天可能可以安排一些历史文化景点，比如景山公园，那里有 nice 的环境，适合散步。下午去天坛公园，虽然有点远，但天坛是很多游客想去的地方，晚上可以在夜市品尝地道小吃，比如烤鸭。\n\n另外，还要考虑交通问题，可能需要推荐一些地铁线路，方便用户出行。比如第一天的故宫在故宫博物院附近，地铁10号线，比较方便。第二天去香山的话，地铁5号线到香山站，或者打车过去。颐和园在昌平区，可能需要地铁转乘，或者打车。第三天的景山和天坛都在市中心，交通相对便利。\n\n还有，用户可能对美食感兴趣，所以推荐一些必吃的小吃摊点，比如三里屯的三里屯美食街，簋街，南锣鼓巷，还有圆明园附近的美食街，这些地方都有很多地道的北京小吃，比如炸酱面，烤鸭，炸鸡等等。\n\n另外，可能用户希望行程不要太赶，所以每半天安排两到三个景点，这样既不会太累，又能体验到不同的景点。同时，考虑到北京的早晚温差大，建议用户带好保暖衣物和防晒用品，尤其是在故宫和天坛这样的户外景点。\n\n最后，还要提醒用户注意交通和安全，比如地铁票务，提前购票，避免晚点影响行程。还有，建议用户根据自己的兴趣调整行程，比如如果喜欢历史的话，可以多花时间在故宫和景山附近，如果喜欢自然，可以多花时间在香山公园。\n\n总之，这个三天旅游计划需要兼顾景点的多样性，美食体验，以及交通便利性，同时考虑到用户的时间安排和兴趣点，希望这个计划能满足他的需求。\n</think>\n\n好的！以下是一个为期三天的北京旅游计划，涵盖经典景点、美食和文化体验，帮助你充分感受北京的魅力。\n\n---\n\n### **第一天：故宫之旅**\n**上午：**\n- **8:00-10:00**：乘坐地铁10号线至“故宫博物院站”，参观**故宫博物院**。这里可以了解中国丰富的历史文化，欣赏精美的文物展览。\n- **10:00-12:00**：参观**午门**、**太和殿**、**景仁宫**等重要建筑，感受 imperial（ imperial style）的北京 royal style。\n\n**中午：**\n- **12:00-13:30**：在**簋街**品尝地道北京小吃，如炸酱面、豆汁儿、炸鸡腿等。\n\n**下午：**\n- **14:00-16:00**：逛**三里屯商业街**或**南锣鼓巷**，感受北京的时尚与老北京风情。\n\n**晚上：**\n- **18:00-21:00**：在**三里屯步行街**或**798艺术区**体验夜生活，欣赏霓虹灯下的北京夜景。\n\n---\n\n### **第二天：自然与文化结合的旅程**\n**上午：**\n- **9:00-12:00**：乘坐地铁5号线至“香山公园站”，参观**香山公园**，欣赏秋天的红叶和壮丽的山景。\n\n**中午：**\n- **12:00-13:30**：在**香山公园**附近的**茶马院**品尝当地美食，如山药饺子、酸梅汤等。\n\n**下午：**\n- **14:00-17:00**：参观**颐和园**，欣赏昆明湖、万人大观楼等景点，感受 classical园林的魅力。\n\n**晚上：**\n- **18:00-21:00**：在**圆明园**附近的**圆明园夜市**品尝地道小吃，如烤鸭、糖葫芦、炸鸡腿等。\n\n---\n\n### **第三天：历史与现代的碰撞**\n**上午：**\n- **9:00-12:00**：参观**景山公园**，漫步于景山南北 gardens，感受北京的自然与人文景观。\n\n**中午：**\n- **12:00-13:30**：在**景山公园**附近的**北土城**品尝地道小吃，如烤鸭、炸鸡腿等。\n\n**下午：**\n- **14:00-17:00**：参观**天坛公园**，欣赏圜丘和香山的祈年殿等景点。天坛离市中心较远，建议乘坐地铁1号线到“回龙观地铁站”再打车前往。\n\n**晚上：**\n- **18:00-21:00**：在**簋街**或**798艺术区**品尝夜市小吃，如烤鸭、烤羊肉串等，体验地道的北京夜生活。\n\n---\n\n### **交通提示：**\n- 建议提前在地铁官方平台购票，避免购票高峰期的延误。\n- 北京地铁线路较多，建议根据景点位置选择合适的地铁线路。\n- 天坛公园距离市中心较远，建议提前规划交通。\n\n---\n\n### **美食推荐：**\n- **簋街**：正宗的北京小吃，如炸酱面、豆汁儿、炸鸡腿。\n- **南锣鼓巷**：传统小吃和手工艺品的聚集地。\n- **三里屯**：时尚美食和购物的好去处。\n- **圆明园夜市**：夜晚的美食天堂。\n- **798艺术区**：创意美食和文化体验。\n\n希望这份计划能帮助你玩转北京！如果有其他需求，随时告诉我！', token_ids=[106287, 3837, 20002, 104029, 115072, 104016, 46944, 68990, 9370, 106635, 99790, 101039, 1773, 99692, 3837, 101140, 35946, 49828, 101118, 42411, 87267, 9370, 106318, 103956, 1773, 68990, 101909, 99491, 105891, 99790, 99490, 3837, 101194, 105869, 73670, 85336, 3837, 77288, 106635, 20450, 101035, 3837, 99999, 49828, 100745, 103956, 3407, 101140, 3837, 35946, 99730, 101118, 110120, 26939, 101314, 99792, 100968, 1773, 109691, 3837, 110120, 73670, 103956, 99792, 110536, 105869, 3837, 101912, 113508, 3837, 99519, 100346, 68990, 9370, 114737, 105869, 3837, 107127, 99172, 85336, 1773, 101889, 3837, 113508, 102205, 101194, 104365, 3837, 101912, 121907, 99913, 3837, 73670, 103956, 105747, 99405, 117371, 3837, 104030, 102946, 102946, 107922, 100386, 99913, 3837, 101912, 44991, 69249, 107551, 100631, 58463, 115807, 101182, 105486, 3837, 99654, 104030, 99600, 99792, 100733, 3407, 105350, 100363, 3837, 73670, 101118, 101883, 99795, 104819, 3837, 101912, 99662, 57811, 102077, 3837, 102302, 18830, 105664, 99425, 100027, 3837, 100231, 28641, 44636, 99317, 99427, 3837, 105012, 109127, 9370, 109398, 1773, 102172, 85336, 113085, 33108, 99354, 3837, 99212, 102073, 106003, 99529, 33108, 31207, 101012, 99237, 99432, 100132, 105522, 105869, 3837, 104030, 104964, 100213, 30858, 99354, 102205, 99405, 114293, 3837, 102302, 101194, 107600, 3407, 99749, 35727, 87267, 73670, 103956, 101883, 110142, 105869, 3837, 101912, 85254, 57811, 102077, 3837, 102302, 18830, 6419, 43589, 99719, 3837, 100231, 111261, 1773, 102172, 85336, 35727, 101152, 102077, 3837, 103925, 104037, 99427, 3837, 77288, 35727, 101152, 20412, 99555, 104090, 109969, 103958, 3837, 104030, 104964, 99530, 22697, 110219, 110810, 107600, 3837, 101912, 102554, 105397, 3407, 101948, 3837, 104019, 101118, 99735, 86119, 3837, 87267, 85106, 101914, 101883, 104851, 104634, 3837, 101147, 20002, 104434, 1773, 101912, 110120, 9370, 113508, 18493, 113508, 104645, 93823, 102205, 3837, 104851, 16, 15, 106762, 3837, 99792, 101147, 1773, 105350, 85336, 99662, 57811, 100363, 3837, 104851, 20, 106762, 26939, 99662, 57811, 70790, 3837, 100631, 75437, 39953, 100688, 1773, 113085, 33108, 99354, 18493, 100763, 49111, 23836, 3837, 87267, 85106, 104851, 46670, 100252, 3837, 100631, 75437, 39953, 1773, 99749, 35727, 9370, 85254, 57811, 33108, 35727, 101152, 102070, 111622, 3837, 99735, 101162, 102421, 3407, 100626, 3837, 20002, 87267, 32664, 104365, 103198, 3837, 99999, 101914, 101883, 58514, 99405, 104006, 99405, 105199, 27442, 3837, 101912, 44991, 69249, 107551, 9370, 44991, 69249, 107551, 104365, 99913, 3837, 121907, 99913, 3837, 58463, 115807, 101182, 105486, 3837, 100626, 100213, 30858, 99354, 107922, 104365, 99913, 3837, 100001, 100371, 101103, 99555, 110810, 9370, 68990, 107600, 3837, 101912, 100893, 102675, 27091, 3837, 102554, 105397, 3837, 100893, 100417, 104008, 3407, 101948, 3837, 87267, 20002, 99880, 106318, 115596, 99970, 3837, 99999, 73157, 103554, 103956, 77540, 26939, 101124, 105869, 3837, 99654, 99929, 99670, 99222, 99847, 3837, 107713, 101904, 26939, 101970, 105869, 1773, 91572, 3837, 106350, 68990, 9370, 113220, 99416, 99572, 26288, 3837, 101898, 20002, 99278, 52801, 114331, 111703, 33108, 113222, 104784, 3837, 110700, 113508, 33108, 35727, 101152, 101893, 105813, 105869, 3407, 100161, 3837, 104019, 104211, 20002, 60533, 99735, 33108, 99464, 3837, 101912, 104851, 94444, 31952, 3837, 104154, 117555, 3837, 101153, 99438, 27442, 99564, 106318, 1773, 100626, 3837, 101898, 20002, 100345, 100005, 100565, 101921, 106318, 3837, 101912, 62244, 99729, 100022, 100363, 3837, 73670, 42140, 99232, 20450, 18493, 113508, 33108, 85254, 57811, 102205, 3837, 62244, 99729, 99795, 3837, 73670, 42140, 99232, 20450, 18493, 99662, 57811, 102077, 3407, 106279, 3837, 99487, 106635, 99790, 101039, 85106, 110896, 105869, 9370, 113702, 3837, 104365, 101904, 3837, 101034, 99735, 102421, 33071, 3837, 91572, 106350, 20002, 101975, 103956, 33108, 100565, 27442, 3837, 99880, 99487, 101039, 112809, 100648, 100354, 8997, 151649, 271, 99692, 6313, 87752, 101909, 109134, 106635, 9370, 68990, 99790, 101039, 3837, 102994, 101297, 105869, 5373, 104365, 33108, 99348, 101904, 3837, 100364, 56568, 100418, 101224, 68990, 108847, 3407, 44364, 14374, 3070, 110120, 5122, 113508, 106399, 1019, 334, 102449, 5122, 1019, 12, 3070, 23, 25, 15, 15, 12, 16, 15, 25, 15, 15, 334, 5122, 106825, 104851, 16, 15, 106762, 56137, 2073, 113508, 104645, 93823, 70790, 33590, 104682, 334, 113508, 104645, 93823, 334, 1773, 99817, 73670, 99794, 58695, 104653, 110142, 3837, 105012, 99219, 101607, 102609, 102475, 8997, 12, 3070, 16, 15, 25, 15, 15, 12, 16, 17, 25, 15, 15, 334, 5122, 104682, 334, 34324, 64689, 334, 5373, 334, 99222, 33108, 100881, 334, 5373, 334, 85254, 102030, 99921, 334, 49567, 99335, 99893, 3837, 101224, 34279, 9909, 34279, 1707, 7552, 9370, 68990, 29236, 1707, 3407, 334, 105747, 5122, 1019, 12, 3070, 16, 17, 25, 15, 15, 12, 16, 18, 25, 18, 15, 334, 5122, 18493, 334, 121907, 99913, 334, 110219, 110810, 68990, 107600, 3837, 29524, 100893, 102675, 27091, 5373, 99955, 102514, 99261, 5373, 100893, 100417, 100447, 49567, 3407, 334, 102172, 5122, 1019, 12, 3070, 16, 19, 25, 15, 15, 12, 16, 21, 25, 15, 15, 334, 5122, 102946, 334, 44991, 69249, 107551, 100386, 99913, 334, 57191, 334, 58463, 115807, 101182, 105486, 334, 3837, 101224, 68990, 9370, 104070, 57218, 91777, 68990, 107259, 3407, 334, 104030, 5122, 1019, 12, 3070, 16, 23, 25, 15, 15, 12, 17, 16, 25, 15, 15, 334, 5122, 18493, 334, 44991, 69249, 107551, 109019, 99913, 334, 57191, 334, 22, 24, 23, 100377, 23836, 334, 101904, 99530, 99424, 3837, 105012, 119097, 101522, 100183, 101373, 68990, 99530, 85254, 3407, 44364, 14374, 3070, 105350, 5122, 99795, 57218, 99348, 100374, 9370, 112482, 1019, 334, 102449, 5122, 1019, 12, 3070, 24, 25, 15, 15, 12, 16, 17, 25, 15, 15, 334, 5122, 106825, 104851, 20, 106762, 56137, 2073, 99662, 57811, 102077, 70790, 33590, 104682, 334, 99662, 57811, 102077, 334, 3837, 105012, 109127, 9370, 99425, 100027, 33108, 100511, 99686, 9370, 57811, 85254, 3407, 334, 105747, 5122, 1019, 12, 3070, 16, 17, 25, 15, 15, 12, 16, 18, 25, 18, 15, 334, 5122, 18493, 334, 99662, 57811, 102077, 334, 107922, 334, 100019, 99313, 93823, 334, 110219, 100198, 104365, 3837, 29524, 57811, 99471, 113132, 5373, 99918, 100711, 102022, 49567, 3407, 334, 102172, 5122, 1019, 12, 3070, 16, 19, 25, 15, 15, 12, 16, 22, 25, 15, 15, 334, 5122, 104682, 334, 113085, 33108, 99354, 334, 3837, 105012, 106003, 99529, 5373, 31207, 101012, 99237, 99432, 49567, 105869, 3837, 101224, 28824, 106451, 108847, 3407, 334, 104030, 5122, 1019, 12, 3070, 16, 23, 25, 15, 15, 12, 17, 16, 25, 15, 15, 334, 5122, 18493, 334, 100213, 30858, 99354, 334, 107922, 334, 100213, 30858, 99354, 99530, 22697, 334, 110219, 110810, 107600, 3837, 29524, 102554, 105397, 5373, 100443, 111065, 5373, 100893, 100417, 100447, 49567, 3407, 44364, 14374, 3070, 99749, 35727, 5122, 100022, 57218, 100390, 9370, 107845, 1019, 334, 102449, 5122, 1019, 12, 3070, 24, 25, 15, 15, 12, 16, 17, 25, 15, 15, 334, 5122, 104682, 334, 85254, 57811, 102077, 334, 3837, 114208, 34204, 85254, 57811, 107280, 35436, 3837, 101224, 68990, 9370, 99795, 57218, 105131, 104819, 3407, 334, 105747, 5122, 1019, 12, 3070, 16, 17, 25, 15, 15, 12, 16, 18, 25, 18, 15, 334, 5122, 18493, 334, 85254, 57811, 102077, 334, 107922, 334, 48309, 72990, 59074, 334, 110219, 110810, 107600, 3837, 29524, 102554, 105397, 5373, 100893, 100417, 100447, 49567, 3407, 334, 102172, 5122, 1019, 12, 3070, 16, 19, 25, 15, 15, 12, 16, 22, 25, 15, 15, 334, 5122, 104682, 334, 35727, 101152, 102077, 334, 3837, 105012, 121772, 105697, 33108, 99662, 57811, 9370, 103706, 7948, 100881, 49567, 105869, 1773, 35727, 101152, 99372, 111622, 99260, 99427, 3837, 101898, 106825, 104851, 16, 106762, 26939, 2073, 18397, 99465, 99237, 104851, 70790, 854, 87256, 75437, 39953, 104374, 3407, 334, 104030, 5122, 1019, 12, 3070, 16, 23, 25, 15, 15, 12, 17, 16, 25, 15, 15, 334, 5122, 18493, 334, 121907, 99913, 334, 57191, 334, 22, 24, 23, 100377, 23836, 334, 110219, 99530, 22697, 107600, 3837, 29524, 102554, 105397, 5373, 102554, 110353, 51575, 49567, 3837, 101904, 110810, 9370, 68990, 99530, 99424, 3407, 44364, 14374, 3070, 99735, 45139, 5122, 1019, 12, 4891, 119, 118, 96422, 104154, 18493, 104851, 100777, 100133, 117555, 3837, 101153, 117555, 116844, 9370, 118969, 8997, 12, 94305, 245, 46553, 104851, 104634, 106204, 3837, 101898, 100345, 105869, 81812, 50404, 106873, 104851, 104634, 8997, 12, 40666, 102, 101152, 102077, 100764, 111622, 99260, 99427, 3837, 101898, 104154, 100367, 99735, 3407, 44364, 14374, 3070, 104365, 101914, 5122, 1019, 12, 3070, 121907, 99913, 334, 5122, 115146, 9370, 68990, 107600, 3837, 29524, 100893, 102675, 27091, 5373, 99955, 102514, 99261, 5373, 100893, 100417, 100447, 8997, 12, 3070, 58463, 115807, 101182, 105486, 334, 5122, 100169, 107600, 33108, 44934, 115194, 9370, 105061, 29490, 8997, 12, 3070, 44991, 69249, 107551, 334, 5122, 104070, 104365, 33108, 102297, 102513, 85336, 44290, 8997, 12, 3070, 100213, 30858, 99354, 99530, 22697, 334, 5122, 108036, 9370, 104365, 106997, 8997, 12, 3070, 22, 24, 23, 100377, 23836, 334, 5122, 102343, 104365, 33108, 99348, 101904, 3407, 99880, 106039, 101039, 26232, 100364, 56568, 99366, 46670, 68990, 6313, 107055, 92894, 100354, 3837, 102422, 106525, 6313, 151643], cumulative_logprob=None, logprobs=None, finish_reason=stop, stop_reason=None)], finished=True, metrics=None, lora_request=None, num_cached_tokens=None, multi_modal_placeholders={})]
```

通过格式化输出可以直接区分出思考内容和最终的回复内容，如下：

```python
for output in outputs:
    prompt = output.prompt
    generated_text = output.outputs[0].text
    if r"</think>" in generated_text:
        think_content, answer_content = generated_text.split(r"</think>")
    else:
        think_content = ""
        answer_content = generated_text
    print(f"Prompt: {prompt!r}\nThink: {think_content!r}\nAnswer: {answer_content!r}\n")
```

```Response
Prompt: '帮我制定一个北京的三天旅游计划<think>\n'
Think: '嗯，用户让我帮他制定一个北京的三天旅游计划。好的，首先我得考虑他可能的行程安排。北京是一个非常著名的旅游城市，有很多景点可以去，但三天时间有限，所以得合理安排。\n\n首先，我应该考虑第一天到哪里比较合适。一般来说，第一天可以安排比较经典的景点，比如故宫，因为这是北京的标志性景点，很多人都想去。然后，故宫附近有很多美食，比如簋街，可以安排中午吃午饭，晚上逛逛附近的商业街，比如三里屯或者南锣鼓巷，这样晚上活动比较丰富。\n\n第二天的话，可以考虑一些自然景观，比如香山公园，那里有美丽的红叶，适合登高望远，欣赏秋天的景色。下午去颐和园，那里的昆明湖和万人大观楼都是不错的景点，晚上可以在圆明园附近吃晚饭，那里有很多小吃。\n\n第三天可能可以安排一些历史文化景点，比如景山公园，那里有 nice 的环境，适合散步。下午去天坛公园，虽然有点远，但天坛是很多游客想去的地方，晚上可以在夜市品尝地道小吃，比如烤鸭。\n\n另外，还要考虑交通问题，可能需要推荐一些地铁线路，方便用户出行。比如第一天的故宫在故宫博物院附近，地铁10号线，比较方便。第二天去香山的话，地铁5号线到香山站，或者打车过去。颐和园在昌平区，可能需要地铁转乘，或者打车。第三天的景山和天坛都在市中心，交通相对便利。\n\n还有，用户可能对美食感兴趣，所以推荐一些必吃的小吃摊点，比如三里屯的三里屯美食街，簋街，南锣鼓巷，还有圆明园附近的美食街，这些地方都有很多地道的北京小吃，比如炸酱面，烤鸭，炸鸡等等。\n\n另外，可能用户希望行程不要太赶，所以每半天安排两到三个景点，这样既不会太累，又能体验到不同的景点。同时，考虑到北京的早晚温差大，建议用户带好保暖衣物和防晒用品，尤其是在故宫和天坛这样的户外景点。\n\n最后，还要提醒用户注意交通和安全，比如地铁票务，提前购票，避免晚点影响行程。还有，建议用户根据自己的兴趣调整行程，比如如果喜欢历史的话，可以多花时间在故宫和景山附近，如果喜欢自然，可以多花时间在香山公园。\n\n总之，这个三天旅游计划需要兼顾景点的多样性，美食体验，以及交通便利性，同时考虑到用户的时间安排和兴趣点，希望这个计划能满足他的需求。\n'
Answer: '\n\n好的！以下是一个为期三天的北京旅游计划，涵盖经典景点、美食和文化体验，帮助你充分感受北京的魅力。\n\n---\n\n### **第一天：故宫之旅**\n**上午：**\n- **8:00-10:00**：乘坐地铁10号线至“故宫博物院站”，参观**故宫博物院**。这里可以了解中国丰富的历史文化，欣赏精美的文物展览。\n- **10:00-12:00**：参观**午门**、**太和殿**、**景仁宫**等重要建筑，感受 imperial（ imperial style）的北京 royal style。\n\n**中午：**\n- **12:00-13:30**：在**簋街**品尝地道北京小吃，如炸酱面、豆汁儿、炸鸡腿等。\n\n**下午：**\n- **14:00-16:00**：逛**三里屯商业街**或**南锣鼓巷**，感受北京的时尚与老北京风情。\n\n**晚上：**\n- **18:00-21:00**：在**三里屯步行街**或**798艺术区**体验夜生活，欣赏霓虹灯下的北京夜景。\n\n---\n\n### **第二天：自然与文化结合的旅程**\n**上午：**\n- **9:00-12:00**：乘坐地铁5号线至“香山公园站”，参观**香山公园**，欣赏秋天的红叶和壮丽的山景。\n\n**中午：**\n- **12:00-13:30**：在**香山公园**附近的**茶马院**品尝当地美食，如山药饺子、酸梅汤等。\n\n**下午：**\n- **14:00-17:00**：参观**颐和园**，欣赏昆明湖、万人大观楼等景点，感受 classical园林的魅力。\n\n**晚上：**\n- **18:00-21:00**：在**圆明园**附近的**圆明园夜市**品尝地道小吃，如烤鸭、糖葫芦、炸鸡腿等。\n\n---\n\n### **第三天：历史与现代的碰撞**\n**上午：**\n- **9:00-12:00**：参观**景山公园**，漫步于景山南北 gardens，感受北京的自然与人文景观。\n\n**中午：**\n- **12:00-13:30**：在**景山公园**附近的**北土城**品尝地道小吃，如烤鸭、炸鸡腿等。\n\n**下午：**\n- **14:00-17:00**：参观**天坛公园**，欣赏圜丘和香山的祈年殿等景点。天坛离市中心较远，建议乘坐地铁1号线到“回龙观地铁站”再打车前往。\n\n**晚上：**\n- **18:00-21:00**：在**簋街**或**798艺术区**品尝夜市小吃，如烤鸭、烤羊肉串等，体验地道的北京夜生活。\n\n---\n\n### **交通提示：**\n- 建议提前在地铁官方平台购票，避免购票高峰期的延误。\n- 北京地铁线路较多，建议根据景点位置选择合适的地铁线路。\n- 天坛公园距离市中心较远，建议提前规划交通。\n\n---\n\n### **美食推荐：**\n- **簋街**：正宗的北京小吃，如炸酱面、豆汁儿、炸鸡腿。\n- **南锣鼓巷**：传统小吃和手工艺品的聚集地。\n- **三里屯**：时尚美食和购物的好去处。\n- **圆明园夜市**：夜晚的美食天堂。\n- **798艺术区**：创意美食和文化体验。\n\n希望这份计划能帮助你玩转北京！如果有其他需求，随时告诉我！'
```

同理，对于批量推理来说：

```python
prompts = [
    "给我制定一个大模型的学习计划<think>\n",
    "帮我制定一个北京的三天旅游计划<think>\n",
]

outputs = llm.generate(prompts, sampling_params=sampling_params)

for output in outputs:
    prompt = output.prompt
    generated_text = output.outputs[0].text
    if r"</think>" in generated_text:
        think_content, answer_content = generated_text.split(r"</think>")
    else:
        think_content = ""
        answer_content = generated_text
    print(f"Prompt: {prompt!r}\nThink: {think_content!r}\nAnswer: {answer_content!r}\n")
```

```Response
Processed prompts:   0%|          | 0/3 [00:00<?, ?it/s, est. speed input: 0.00 toks/s, output: 0.00 toks/s]
```