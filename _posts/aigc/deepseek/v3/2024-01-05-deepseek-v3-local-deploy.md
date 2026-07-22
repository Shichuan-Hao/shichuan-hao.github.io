---
title: DeepSeek V3 本地部署流程
description: DeepSeek V3 的模型架构、内存需求、及通过 Ollama/SGLang/LMDeploy/vLLM 进行本地部署的完整指南
author: hsc
date: 2024-01-05 08:00:00 +0800
categories: [AI Agent, DeepSeek]
tags: [DeepSeek V3, 本地部署, Ollama, MoE, vLLM]
---

## DeepSeek V3 简介

DeepSeek V3 自发布以来凭借**高性能和低成本**获得了大量关注。其在数学、编程、中文理解等多个领域的基准测试中都展现出优异的性能。

---

## 一、DeepSeek V3 模型架构

### Mixure-of-Experts（MoE，混合专家架构）

DeepSeek V3 采用了先进的 MoE 架构：

| 组件 | 参数规模 | 说明 |
|------|---------|------|
| **总参数量** | 685B | 671B 主模型 + 14B MTP 模块 |
| **激活参数** | 37B | 每个token实际激活的参数量 |
| **架构类型** | MoE | 混合专家模型 |
| **上下文长度** | 128K | 最大支持的上下文窗口 |

> <hl=red>MoE 的核心优势</hl>：虽然有 671B 总参数，但每次推理只激活 37B 参数，大幅降低了推理成本，同时保持了高性能。

### 模型精度与显存估算

| 精度 | 显存需求 | 适用场景 |
|------|---------|---------|
| **FP8** | ~685 GB | 原生训练精度，速度最快 |
| **BF16** | ~1,370 GB | 精度最高，支持微调 |
| **INT4** | ~343 GB | 量化部署，节省显存 |

> 这些需求可通过 Ollama 的 Q4_K_M 量化格式大幅降低

---

## 二、获取模型权重

### 模型下载渠道

| 平台 | 地址 | 说明 |
|------|------|------|
| **GitHub** | https://github.com/deepseek-ai/DeepSeek-V3 | 官方仓库 |
| **HuggingFace** | https://huggingface.co/deepseek-ai/DeepSeek-V3-Base | 海外下载 |
| **ModelScope** | https://modelscope.cn/models/deepseek-ai/DeepSeek-V3 | 国内推荐，速度快 |

> <hl=red>国内用户推荐使用 ModelScope</hl>，无需科学上网，下载速度快。

### 本地下载（ModelScope）

```bash
# 安装 modelscope
pip install modelscope

# 使用 snapshot_download 下载
python -c "
from modelscope import snapshot_download
snapshot_download('deepseek-ai/DeepSeek-V3', cache_dir='./DeepSeek-V3')
"
```

---

## 三、Ollama 部署方案（最简单）

Ollama 是最简单易用的本地大模型部署工具，适合个人学习和测试。

### 3.1 安装 Ollama

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# 启动服务
ollama serve
```

### 3.2 下载并运行 DeepSeek V3

```bash
# Ollama 提供的量化版本
ollama run deepseek-v3

# 查看已下载的模型
ollama list
```

### 3.3 Ollama 常用命令

```bash
# 查看模型信息
ollama show deepseek-v3

# 删除模型
ollama rm deepseek-v3

# API 调用模式
curl http://localhost:11434/api/generate -d '{
  "model": "deepseek-v3",
  "prompt": "你好，请介绍一下自己"
}'

# 对话模式
curl http://localhost:11434/api/chat -d '{
  "model": "deepseek-v3",
  "messages": [{"role": "user", "content": "你好"}]
}'
```

### Ollama 优势总结

- 一行命令秒级部署，开箱即用
- 自动处理量化，无需了解模型格式
- 提供标准 REST API，兼容 OpenAI 格式
- 支持 CPU + GPU 混合推理

---

## 四、SGLang 部署方案（高性能）

SGLang 是专为大语言模型推理设计的高性能框架。

### 4.1 安装 SGLang

```bash
pip install sglang
```

### 4.2 启动 DeepSeek V3 服务

```bash
python -m sglang.launch_server \
    --model deepseek-ai/DeepSeek-V3 \
    --host 0.0.0.0 \
    --port 30000
```

### 4.3 SGLang 特点

- 原生支持 DeepSeek V3 的 MoE 架构
- 提供 RadixAttention 优化
- 支持 FP8 推理加速
- 提供 OpenAI 兼容 API

---

## 五、LMDeploy 部署方案

LMDeploy 是上海人工智能实验室开发的高效推理工具。

### 5.1 安装

```bash
pip install lmdeploy
```

### 5.2 启动服务

```bash
# TurboMind 引擎推理
lmdeploy serve api_server deepseek-ai/DeepSeek-V3 \
    --backend turbomind \
    --server-port 23333

# PyTorch 引擎推理
lmdeploy serve api_server deepseek-ai/DeepSeek-V3 \
    --backend pytorch \
    --server-port 23333
```

### 5.3 LMDeploy 优势

- TurboMind 引擎支持 FP8 推理，速度领先
- 支持 W4A16 量化，大幅降低显存
- API 完全兼容 OpenAI 格式
- 对国产硬件兼容性较好

---

## 六、vLLM 部署方案

vLLM 是目前社区使用最广泛的高性能推理框架。

### 6.1 安装

```bash
pip install vllm
```

### 6.2 启动服务

```bash
python -m vllm.entrypoints.openai.api_server \
    --model deepseek-ai/DeepSeek-V3 \
    --dtype float16 \
    --max-model-len 32768
```

### 6.3 vLLM 关键参数

| 参数 | 说明 |
|------|------|
| `--model` | 模型路径或 HuggingFace ID |
| `--dtype` | 推理精度：float16, bfloat16, auto |
| `--max-model-len` | 最大上下文长度 |
| `--tensor-parallel-size` | 张量并行数（多卡） |
| `--gpu-memory-utilization` | GPU 显存利用率，默认0.9 |
| `--quantization` | 量化方式：fp8, awq, gptq |
| `--port` | API 服务端口，默认8000 |

### 多卡并行示例

```bash
# 4卡张量并行
python -m vllm.entrypoints.openai.api_server \
    --model deepseek-ai/DeepSeek-V3 \
    --tensor-parallel-size 4 \
    --gpu-memory-utilization 0.95 \
    --max-model-len 32768
```

---

## 七、各方案对比

| 方案 | 部署难度 | 推理速度 | 显存优化 | 适用场景 |
|------|---------|---------|---------|---------|
| **Ollama** | ⭐ 极简 | ⭐⭐ | ⭐⭐⭐ | 个人学习、测试 |
| **SGLang** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 高性能推理 |
| **LMDeploy** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 量化部署 |
| **vLLM** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 生产环境 |

### 推荐策略

- **快速体验** → Ollama，一行命令即可
- **日常使用** → vLLM，生态最成熟
- **量化部署** → LMDeploy，W4A16 量化最优
- **极限性能** → SGLang，RadixAttention 加持

---

## 总结

DeepSeek V3本地部署核心要点：

1. **685B 总参数量**，37B 激活参数，MoE 架构大幅降低推理成本
2. **Ollama 一键部署** → 适合快速体验（量化后显存需求大幅降低）
3. **vLLM 多卡并行** → 适合生产环境部署（支持张量并行、PagedAttention）
4. **LMDeploy + W4A16** → 适合显存受限场景
5. 国内下载推荐 **ModelScope**，速度快且稳定
