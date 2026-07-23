---
title: DeepSeek R1 蒸馏模型部署与调用
description: DeepSeek R1 蒸馏版本全系列部署指南，覆盖 1.5B~70B 蒸馏模型的获取、部署与调用
author: hsc
date: 2025-01-08 08:00:00 +0800
categories: [AI Agent, 大模型部署, DeepSeek]
tags: [DeepSeek R1, 蒸馏模型, 模型部署, Ollama]
---

## 什么是蒸馏模型？

知识蒸馏（Knowledge Distillation）是将大模型（教师模型）的知识迁移到小模型（学生模型）的技术。DeepSeek 团队使用 R1 作为教师模型，蒸馏出一系列小型模型，让开发者**在没有海量GPU的情况下也能运行高推理能力的模型**。

---

## 一、R1 蒸馏模型系列

| 模型 | 基座 | 参数量 | 最低显存 | 适用场景 |
|------|------|--------|---------|---------|
| **DeepSeek-R1-Distill-Qwen-1.5B** | Qwen2.5-1.5B | 1.5B | ~6 GB | 学习、测试、边缘设备 |
| **DeepSeek-R1-Distill-Qwen-7B** | Qwen2.5-7B | 7B | ~16 GB | 个人电脑 |
| **DeepSeek-R1-Distill-Llama-8B** | Llama-3.1-8B | 8B | ~18 GB | 个人电脑 |
| **DeepSeek-R1-Distill-Qwen-14B** | Qwen2.5-14B | 14B | ~30 GB | 高配个人电脑 |
| **DeepSeek-R1-Distill-Qwen-32B** | Qwen2.5-32B | 32B | ~64 GB | 工作站 |
| **DeepSeek-R1-Distill-Llama-70B** | Llama-3.3-70B | 70B | ~140 GB | 服务器集群 |

> <hl=red>1.5B 版本仅需 6GB 显存</hl>，RTX 5060 Ti 16GB 可轻松运行，是最适合入门学习的版本。

---

## 二、模型下载

### HuggingFace 下载

```bash
# 1.5B 蒸馏版
git clone https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B

# 7B 蒸馏版
git clone https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B

# 8B 蒸馏版
git clone https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-8B
```

### ModelScope 下载（国内推荐）

```python
from modelscope import snapshot_download

# 下载 1.5B 蒸馏版
snapshot_download(
    'deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B',
    cache_dir='./models/DeepSeek-R1-Distill-Qwen-1.5B'
)

# 下载 7B 蒸馏版
snapshot_download(
    'deepseek-ai/DeepSeek-R1-Distill-Qwen-7B',
    cache_dir='./models/DeepSeek-R1-Distill-Qwen-7B'
)
```

---

## 三、Transformer 原生推理

### 1.5B 蒸馏模型调用示例

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

# 加载模型和分词器
model_name = "./models/DeepSeek-R1-Distill-Qwen-1.5B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"       # 自动分配到GPU
)

# 构造提示
messages = [
    {"role": "user", "content": "解释什么是机器学习？"}
]
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

# 模型推理
inputs = tokenizer([text], return_tensors="pt").to(model.device)
outputs = model.generate(
    **inputs,
    max_new_tokens=512,
    temperature=0.7,
    do_sample=True
)

result = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(result)
```

### 输出结构分析

蒸馏模型的输出包含 `[think]` 标签：

```
[think]
嗯，用户问的是机器学习的定义。这是一个基础但重要的问题...
我需要先解释机器学习的核心概念...
然后再分类说明监督学习、无监督学习和强化学习的区别...
[/think]

机器学习是人工智能的一个分支，它使计算机能够从数据中学习...
主要有三种类型：
1. 监督学习 - 使用带标签的数据训练模型
2. 无监督学习 - 从无标签数据中发现模式
3. 强化学习 - 通过试错与环境交互学习
```

---

## 四、Ollama GGUF 部署

Ollama 提供量化版本，进一步降低显存需求：

### 拉取蒸馏模型

```bash
# 1.5B Q4_K_M 量化版
ollama pull deepseek-r1:1.5b

# 7B 版本
ollama pull deepseek-r1:7b

# 8B 版本
ollama pull deepseek-r1:8b

# 14B 版本
ollama pull deepseek-r1:14b

# 32B 版本
ollama pull deepseek-r1:32b

# 70B 版本
ollama pull deepseek-r1:70b
```

### GGUF 量化格式说明

| 量化格式 | 质量 | 大小 | 推荐场景 |
|---------|------|------|---------|
| **Q4_K_M** | 较好 | 较小 | 推荐默认选择 |
| **Q5_K_M** | 好 | 中等 | 质量优先 |
| **Q8_0** | 几乎无损 | 较大 | 精度优先 |
| **F16** | 无损 | 最大 | 完整精度 |

### Ollama 部署 1.5B 完整示例

```bash
# 1. 拉取模型
ollama pull deepseek-r1:1.5b

# 2. 确认安装
ollama list
# NAME                  ID              SIZE      MODIFIED
# deepseek-r1:1.5b     ...             1.1 GB    2 days ago

# 3. 交互式对话
ollama run deepseek-r1:1.5b

# 4. API 调用
curl http://localhost:11434/api/generate -d '{
  "model": "deepseek-r1:1.5b",
  "prompt": "写一个Python冒泡排序"
}'
```

---

## 五、硬件需求速查表

| 蒸馏版本 | FP16 显存 | Q4_K_M 显存 | 推荐最低 GPU |
|----------|----------|-------------|-------------|
| 1.5B | ~3.5 GB | ~1.5 GB | RTX 3060 6GB |
| 7B | ~15 GB | ~5 GB | RTX 3070 8GB |
| 8B | ~17 GB | ~6 GB | RTX 3080 10GB |
| 14B | ~29 GB | ~9 GB | RTX 3090 24GB |
| 32B | ~65 GB | ~20 GB | A100 40GB |
| 70B | ~140 GB | ~42 GB | 2×A100 80GB |

> 你的 **RTX 5060 Ti 16GB** 可运行：1.5B（极流畅）、7B（流畅）、8B（流畅）、14B（需Q4量化）

---

## 六、蒸馏模型选型建议

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| 学习入门 | 1.5B Qwen | 极低硬件门槛，加载快 |
| 日常开发 | 7B Qwen / 8B Llama | 推理质量与速度的平衡 |
| 高要求任务 | 32B Qwen | 接近教师模型的推理能力 |
| 企业级应用 | 70B Llama | 最强蒸馏能力 |

### 性能对比参考（数学推理）

| 模型 | 显存需求 | MATH基准 | 速度 |
|------|---------|---------|------|
| R1 完整版 (685B) | ~700 GB | 顶尖 | 慢 |
| R1-Distill-70B | ~42 GB(Q4) | 接近R1 | 中 |
| R1-Distill-32B | ~20 GB(Q4) | 较强 | 较快 |
| **R1-Distill-7B** | **~5 GB(Q4)** | **中上** | **快** |

---

## 总结

R1 蒸馏模型把强大的推理能力带到了普通硬件上：

1. **模型系列** — 1.5B 到 70B，六种规格覆盖所有场景
2. **1.5B 仅需 6GB 显存** — 非常适合本地学习和实验
3. **Ollama + Q4_K_M** — 一行命令完成部署
4. **Transformer 原生推理** — `apply_chat_template` + `model.generate`
5. **输出格式** — `[think]...[/think]` + 正文，思考过程可见
