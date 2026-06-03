---
title: DeepSeek v3 本地部署流程
description: 
author: 郝世川
date: 2024-12-27 10:27:00 +0800
categories: [Ai]
tags: [DeepSeek]
# pin: true
# math: true
# mermaid: true
# image:
#   path: /assets/img/posts/devices-mockup.png
#   lqip: data:image/webp;base64,UklGRpoAAABXRUJQVlA4WAoAAAAQAAAADwAABwAAQUxQSDIAAAARL0AmbZurmr57yyIiqE8oiG0bejIYEQTgqiDA9vqnsUSI6H+oAERp2HZ65qP/VIAWAFZQOCBCAAAA8AEAnQEqEAAIAAVAfCWkAALp8sF8rgRgAP7o9FDvMCkMde9PK7euH5M1m6VWoDXf2FkP3BqV0ZYbO6NA/VFIAAAA
#   alt: Chirpy 主题在多种设备上的响应式渲染效果。
---

DeepSeek-V3 与昨日（2024/12/26）正式发布，详细发布公告详见：https://api-docs.deepseek.com/zh-cn/news/news1226

## DeepSeek 开源情况介绍

DeepSeek 开源项目地址：https://github.com/deepseek-ai/DeepSeek-V3

其中技术报告和模型代码部分值得关注：
- 模型代码：inference/
- 技术报告：DeepSeek_V3.pdf

开源代码部分内容如下：
- `convert.py`：用来进行格式转化，将一个已经训练好的<color=#3498db>模型检查点（checkpoint）</color>文件从一个格式（比如 safetensors）转换并保存成一个适合特定<color=#3498db>模型并行度（model parallelism）</color>和<color=#3498db>专家数（n_experts）</color>的格式。
- `fp8_cast_bf16.py`：代码的功能是将存储在 FP8 格式中的模型权重转换为 BF16 格式，并保存转换后的权重。它还更新了模型的索引文件，去除了 `scale_inv` 的引用。
- `generate.py`：是一个用来生成文本的示例程序，支持交互式和批量文本生成。它使用一个 Transformer 模型并进行分布式训练。
- `kernel.py`: 主要涉及量化和矩阵乘法操作，使用了 <hl=red>Triton</hl> 库进行加速，特别是针对 `<hl=red>FP8</hl> 精度（浮点8位）进行了优化。<hl=red>Triton</hl> 是一个专为 GPU 上高效自定义操作而设计的编程框架，支持 Python 和 PyTorch，可以通过简洁的代码来实现高效的 GPU 核心。
- `model.py`: 定义了 DeepSeek v3 模型架构。

目前模型权重已经在 Hugging Face 上开源了，具体情况见：https://github.com/deepseek-ai/DeepSeek-V3/blob/main/README.md
> DeepSeek-V3 模型在 Hugging Face 上的总大小为 685B，包括 671B 的主模型权重和 14B 的多标记预测（MTP）模块权重。
> 为确保最佳性能和灵活性，我们与开源社区和硬件供应商合作，提供多种在本地运行模型的方式。有关逐步指导，请参阅第6节：如何在本地运行（How_to_Run_Locally）
> 对于希望深入了解的开发者，我们建议查阅 README_WEIGHTS.md 文件，了解主模型权重和多标记预测（MTP）模块的详细信息。请注意，MTP 支持目前仍在社区内积极开发中，我们欢迎您的贡献和反馈。

并且还非常贴心的介绍了权重情况：https://github.com/deepseek-ai/DeepSeek-V3/blob/main/README_WEIGHTS.md

DeepSeek V3 模型权重可在 Hugging Face 上主页上下载：https://huggingface.co/deepseek-ai/DeepSeek-V3，权重总共约 650G 大小。

此外，也可以在魔搭社区上下载：https://www.modelscope.cn/models/deepseek-ai/DeepSeek-V3。

既然是权重全开源，那肯定是可以在本地运行的，以下官方介绍的本地运行方法：
![How to Run Locally]()
> 6. 如何本地运行
> DeepSeek-V3可以使用以下硬件和开源社区软件在本地部署：
> - DeepSeek-Infer Demo：我们提供了一个简单且轻量的演示，支持FP8和FP16推理。
> - SGLang：完全支持 DeepSeek-V3 模型在 BF16 和 FP8 推理模式下运行，且即将支持多标记预测（MTP）
> - LMDeploy：支持高效的FP8和BF16推理，适合于本地和云端部署。
> - TensorRT-LLM：目前支持 BF16 推理和 INT4/8 量化，FP8支持即将推出。
> - vLLM：支持 DeepSeek-V3 模型在 FP8 和 BF16 模式下进行张量并行和流水线并行。
> - AMD GPU：通过 SGLang，在 BF16 和 FP8 模式下支持在 AMD GPU 上运行 DeepSeek-V3 模型。
> - 华为 Ascend NPU：支持在华为 Ascend 设备上运行 DeepSeek-V3 模型。
> 由于 DeepSeek 的框架原生采用 FP8 训练，因此仅提供 FP8 权重，预估仅仅 700GB+ 显存便可轻松运行。搭

由于 DeepSeek 的框架原生采用 FP8 训练，因此仅提供 FP8 权重，预估仅仅 700GB+ 显存便可轻松运行。当然也可以转换为 BF16，在半精度下，需要1400GB+，而量化到int4时需要450GB+。以下是半精度下显存占用情况：（占用 490G 显存，需要 7 张 80G A100，租赁成本约 1000 元 1 天）。
![半精度下显存占用情况]()

## DeepSeek V3 本地部署和调用流程

本次 DeepSeek V3 的本地部署将使用模型的 Int4 量化版进行运行，基本配置如下：

- 服务器硬件配置：
    - GPU：Nvidia H20 (98G) GPU * 8
    - CPU：AMD EPYC 9K84 96-Core
    - 桥接方式：NVLink
    - 内存：150G
    - 存储：2T

- 深度学习环境配置：
    - 操作系统：Ubuntu 22.04
    - PyTorch 版本：2.5.1
    - Python 版本：3.12
    - CUDA 版本：12.4
    - 其它软件包版本根据 DeepSeek V3 项目 requirement 决定。

> `tip` 
硬件环境可以考虑在 AutoDL 上进行租赁。
{: .prompt-tip }

1. 创建虚拟环境
:
   ```bash
   conda create --name dv3 python=3.12
   conda init
   source ~/.bashrc
   conda activate dv3
   ```
   ![]()
   ```bash
   conda install jupyterlab
   conda install ipykernel
   python -m ipykernel install --user --name dv3 --display-name "Python（dv3）"
   ```
   ![]()

2. 登录 GitHub 主页拉取项目
:
    访问 DeepSeek V3 主页：https://github.com/deepseek-ai/DeepSeek-V3
    ```bash
    git clone https://github.com/deepseek-ai/DeepSeek-V3.git
    ```
    
3. 下载模型权重
:
    可以在 HuggingFace 或者 魔搭社区上下载模型权重，考虑到国内网络情况，推荐使用魔搭社区进行下载。

    DeepSeek V3 魔搭社区官网地址：https://www.modelscope.cn/models/deepseek-ai/DeepSeek-V3

    > `tip` 
    下载前需要提前留出 600G 左右存储空间，用于保存模型权重
    {: .prompt-tip }

    具体下载流程如下：
    ```bash
    pip install modelscope
    ```
    ![pip install modelscope]()
    
    ```bash
    mkdir ./deepseek
    modelscope download --model OPEA/DeepSeek-V3-int4-sym-gptq-inc --local_dir ./deepseek
    ```
    ![modelscope pull deepseek-ai/DeepSeek-V3]()

    > `tip` 
    这里在下载的时候就是下载 Int4 类型的权重
    {: .prompt-tip }

4. 在 Jupyter 中进行推理
:
    ```python
    import torch

    from modelscope import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
    
    model_name = "./deepseek"
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.bfloat16, device_map="auto")
    
    model.generation_config = GenerationConfig.from_pretrained(model_name)

    model.generation_config.pad_token_id = model.generation_config.eos_token_id
    ```

    ![]()
    
    ```python
    messages = [
        {
            "role": "user",
            "content": "你好，好久不见，请介绍下你自己！"
        }
    ]
    
    input_tensor = tokenizer.apply_chat_template(message, add_generation_prompt=True, return_tensors="pt")

    optputs = model.generate(input_tensor.to(model.device), max_new_tokens=100)

    result = tokenizer.decode(optputs[0][input_tensor_shape[1]:],skip_special_tokens=True)

    print(result)
    ```
    ![]()

## DeepSeek V3 + SGLang 部署方案

[SGLang 项目主页](https://github.com/sgl-project/sglang)

SGLang 目前支持 MLA 优化、DP Attention、FP8(W8A8)、FP8 KV 缓存和 Torch Compile，在开源框架中提供了领先的延迟和吞吐量性能。

需要注意的是：
- SGLang v0.4.1 完全支持在 NVIDIA 和 AMD GPU 上运行 DeepSeek-V3，使其成为一个高度通用且稳健的解决方案。
- SGLang 还支持多节点张量并行，允许你在多个网络连接的机器上允许该模型。目前多标记预测（MTP）正在开发中，进行可以在优化计划中追踪。

1. 安装 SGLang
:
   ```bash
   pip install "sglang[all]>=0.4.1.post5" --find-links
   https://flashinfer.ai/whl/cu124/torch2.4/flashinfer
   ```
   
2. 调用 DeepSeek V3
: 
   ```bash
   python3 -m sglang.launch_server --model deepseek-ai/DeepSeek-V3 --tp 8 --trust-remote-code
   ```
   
   此时服务将在30000端口启动，接下来即可使用 OpenAI 风格 API 来调用 DeepSeek V3 模型了：

   ```python
   import openai
   client = openai.Client(base_url="http://127.0.0.1:30000/v1", api_key="EMPTY")

   # Chat completion
   response = client.Completions.create(
      model="default",
      messages=[
         {
            "role": "system",
            "content": "You are a helpful assistant."
         },
         {
            "role": "user",
            "content": "List 3 countries and their captial."
         }
      ],
      temperature=0,
      max_tokens=100,
   )
   print(response)
   ```

   ## DeepSeek v3 + LMDeploy 部署方案

   [LMDeploy项目主页](https://github.com/InternLM/lmdeploy)

   LMDeploy 是一个灵活且高性能的推理与服务框架，专为大语言模型量身定制，现在支持 DeeepSeek-V3。它提供了离线管道处理和在线部署能力，能够与基于 PyTorch 的工作流无缝集成。具体使用 LMDeploy 调用 DeepSeek v3 流程如下：

   1. 安装 LMDeploy
   :
      ```bash
      git clone -b support-dsv3 https://github.com/InternLM/lmdeploy.git
      cd lmdeploy
      pip install -e .
      ```
   2. 单任务推理，编写 Python 脚本执行
   :
      ```python
      from lmdeploy import pipeline, PytorchEngineConfig

      if __name__ == "__main__":
          pipe = pipeline("deepseek-ai/DeepSeek-V3-FP8",  backend_config=PytorchEngineConfig(tp=8))
          
          messge_list = [
            [
                {
                    "role": "user",
                    "content": "who are you ?"
                }
            ],
            [
                {
                    "role": "user",
                    "content": "Translate the following content into
                    Chinese directly: DeepSeek-V3 adopts innovative architectures to guarantee enconmical traning and efficient inference."
                }
            ],
            [
                {
                    "role": "user",
                    "content": "Write a piece of quicksort code in C++."
                }
            ]
          ]

          output = pipe(messages_list)
          
          print(output)
      ```
    3. 在线服务调用
    :
      先运行如下命令:  

      ```bash
      # run
      lmdeploy serve api_server deepseek-ai/DeepSeek-V3-FP8 --tp 8 --backend pytorch
      ```

      接下来即可在 23333 端口调用 DeepSeek v3 模型了：
      
      ```python
      from openai import OpenAI

      client_OpenAI(
        api_key="YOUR_API_KEY",
        base_url="http://0.0.0.0:23333/v1"
      )

      model_name = client.model.list().data[0].id

      response = client.Completions.create(
        model=model_name,
        messages=[
          {
            "role": "user",
            "content": "Write a piece of quicksort code in C++."
          }
        ],
        temperature=0.8
        top_p=0.8,
      )
      print(response)
      ```

## DeepSeek V3 + vLLM 部署方案

[vLLM 项目主页](https://github.com/vllm-project/vllm)

vLLM v0.6.6 支持在 NVIDIA 和 AMD GPU 上以 FP8 和 BF16 模式进行 DeepSeek-V3 推理。除了标准技术外，vLLM 还提供了管道并行性，允许在多个网络连接的机器上运行该模型。

1. vLLM 安装
:
   ```bash
   pip install vllm
   ```

2. DeepSeek v3调用
:
   目前 vLLM 已支持 DeepSeek v3 模型调用，可以在[模型支持列表](https://docs.vllm.ai/en/latest/models/supported_models/)中查看模型关键字。
   
   接下来即可使用下面代码进行调用：
   ```python
   from vllm import VLLM

   # For generative models (task=generate) only
   llm = LLM(model=deepseek-ai/DeepSeek-V3, task="generate") # Name or path of your model

   output = llm.generate("Hello, my name is")
   print(output)
   ```





    

