---
title: DeepSeek R1 本地部署与调用方法
description: DeepSeek R1 推理模型的本地部署方案详解，涵盖模型获取、Ollama部署和主流推理框架
author: hsc
date: 2025-01-07 08:00:00 +0800
categories: [AI Agent, 大模型部署, DeepSeek]
tags: [DeepSeek R1, 本地部署, Ollama, SGLang, vLLM]
---

## DeepSeek R1 简介

2024年1月20日，深度求索发布了 **DeepSeek R1**，采用与 V3 相同的 MoE 架构，但通过强化学习（RL）在推理能力上取得了突破性提升。

### R1 vs R1-Zero

| 版本 | 训练方式 | 特点 |
|------|---------|------|
| **R1-Zero** | 纯RL训练，无监督数据 | 原始推理能力，但输出格式不稳定 |
| **R1** | RL + 冷启动SFT数据 | 推理能力强 + 输出质量高 |

R1-Zero 证明了纯粹通过强化学习也可以激发推理能力，但由于完全没有任何监督数据，输出有时会出现语言混杂等问题。R1 在此基础上加入了少量高质量冷启动数据，获得了更好的效果。

---

## 一、模型架构特点

### 与 V3 相同的基础架构

R1 与 V3 使用相同的 MoE 基础架构：

- 总参数量一致：685B（671B 主模型 + 14B MTP 模块）
- 激活参数量：37B
- 上下文窗口：128K

### 与 V3 的核心区别

| 维度 | DeepSeek V3 | DeepSeek R1 |
|------|------------|------------|
| 训练重点 | 通用能力 | 推理能力 |
| 训练方法 | 标准预训练 + SFT + RLHF | 强化学习 + 冷启动数据 |
| 输出特点 | 直接回答 | 思考链 + 最终答案 |
| 编程能力 | 较强 | 更强（CoT推理） |

---

## 二、获取模型权重

### 下载渠道

| 平台 | 地址 |
|------|------|
| **HuggingFace** | https://huggingface.co/deepseek-ai/DeepSeek-R1 |
| **ModelScope** | https://modelscope.cn/models/deepseek-ai/DeepSeek-R1 |

```bash
# ModelScope 下载（国内推荐）
pip install modelscope

python -c "
from modelscope import snapshot_download
snapshot_download('deepseek-ai/DeepSeek-R1', cache_dir='./DeepSeek-R1')
"
```

---

## 三、Ollama 一键部署

Ollama 是部署 R1 最简单的方式：

```bash
# 1. 安装 Ollama（如未安装）
curl -fsSL https://ollama.com/install.sh | sh

# 2. 拉取 DeepSeek R1 模型
ollama pull deepseek-r1:latest

# 3. 运行模型
ollama run deepseek-r1:latest
```

### 对话示例

```
>>> 证明根号2是无理数

思考过程：
首先，我们要证明√2是无理数...
采用反证法：假设√2是有理数...
那么存在两个互质的正整数p和q，使得√2 = p/q...
两边平方：2 = p²/q²...
则 p² = 2q²，说明p²是偶数...
由此推出p是偶数...
...
这与p和q互质的假设矛盾，因此√2不能写成两个整数之比...
所以√2是无理数。□

最终答案：
√2是无理数。
```

> Ollama 版本的 R1 会自动在输出中包含思考链（think标签包裹的部分）

---

## 四、SGLang 部署 R1

SGLang 对 DeepSeek 系列模型有原生优化支持：

### 安装与启动

```bash
pip install sglang

python -m sglang.launch_server \
    --model deepseek-ai/DeepSeek-R1 \
    --host 0.0.0.0 \
    --port 30000 \
    --trust-remote-code
```

### 调用示例

```python
import openai

client = openai.Client(
    base_url="http://localhost:30000/v1",
    api_key="EMPTY"
)

response = client.chat.completions.create(
    model="default",
    messages=[
        {"role": "user", "content": "写一个快速排序的Python实现"}
    ]
)
print(response.choices[0].message.content)
```

---

## 五、LMDeploy 部署 R1

```bash
# 安装
pip install lmdeploy

# TurboMind 引擎启动
lmdeploy serve api_server deepseek-ai/DeepSeek-R1 \
    --backend turbomind \
    --server-port 23333

# 或使用 PyTorch 后端
lmdeploy serve api_server deepseek-ai/DeepSeek-R1 \
    --backend pytorch \
    --server-port 23333
```

---

## 六、vLLM 部署 R1

```bash
# 单卡部署
python -m vllm.entrypoints.openai.api_server \
    --model deepseek-ai/DeepSeek-R1 \
    --dtype float16 \
    --max-model-len 32768

# 多卡张量并行（4卡）
python -m vllm.entrypoints.openai.api_server \
    --model deepseek-ai/DeepSeek-R1 \
    --tensor-parallel-size 4 \
    --gpu-memory-utilization 0.95 \
    --max-model-len 32768
```

---

## 七、部署方案对比

| 方案 | 上手难度 | 性能 | 推荐场景 |
|------|---------|------|---------|
| **Ollama** | ⭐ 极简 | ⭐⭐ | 个人快速体验 |
| **SGLang** | ⭐⭐ | ⭐⭐⭐ | 高性能推理 |
| **LMDeploy** | ⭐⭐ | ⭐⭐⭐ | 量化 + W4A16 |
| **vLLM** | ⭐⭐ | ⭐⭐⭐ | 生产标准方案 |

---

## 总结

R1 本地部署的核心要点：

1. **MoE 架构** — 685B 总参数，37B 激活参数，推理成本低
2. **强化学习训练** — 通过 RL 激发推理能力，CoT 思考链可见
3. **Ollama 一键部署** — 个人测试首选，操作最简单
4. **vLLM/SGLang** — 生产环境标准方案，性能最优
5. **R1 输出格式** — 思考过程 + 最终答案，与 V3 的核心区别
