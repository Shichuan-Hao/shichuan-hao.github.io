---
title: DeepSeek-R1 蒸馏 1.5B Qwen 模型调用实战
description: 从 ModelScope 加载到本地推理，手把手带你跑通 DeepSeek R1 蒸馏 1.5B 模型的完整流程
author: hsc
date: 2024-01-09 08:00:00 +0800
categories: [AI Agent, DeepSeek]
tags: [DeepSeek R1, 蒸馏模型, 1.5B, Qwen, 本地推理]
---

## 概述

本笔记完整记录 DeepSeek R1 蒸馏 1.5B Qwen 模型的本地加载与调用流程。该模型以 Qwen2.5-1.5B 为基座，通过 R1 教师模型的知识蒸馏训练，继承了 R1 的强大推理能力。

**硬件要求**：仅需约 6GB 显存，RTX 5060 Ti 16GB 完全够用。

---

## 一、环境准备

### 安装依赖

```python
!pip install modelscope transformers torch
```

核心依赖说明：

| 包 | 用途 |
|----|------|
| `modelscope` | 从 ModelScope（魔搭社区）下载模型 |
| `transformers` | HuggingFace 模型加载与推理 |
| `torch` | PyTorch 深度学习框架 |

---

## 二、从 ModelScope 加载模型

ModelScope 是阿里达摩院推出的模型平台，国内下载速度快，无需代理。

```python
from modelscope import AutoModelForCausalLM, AutoTokenizer

# 模型在 ModelScope 上的 ID
model_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"

# 加载分词器
tokenizer = AutoTokenizer.from_pretrained(
    model_name,
    trust_remote_code=True   # 信任模型仓库中的自定义代码
)

# 加载模型
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",      # 自动选择最佳精度（一般为 bfloat16/float16）
    device_map="auto",       # 自动分配模型到 GPU（或 CPU）
    trust_remote_code=True
)
```

### 关键参数解释

| 参数 | 说明 |
|------|------|
| `torch_dtype="auto"` | 自动检测并选择最优数据类型 |
| `device_map="auto"` | 自动将模型层分配到可用设备 |
| `trust_remote_code=True` | <hl=red>加载自定义模型代码时必须开启</hl> |

---

## 三、构造聊天消息

### 使用 apply_chat_template

`apply_chat_template` 是 Transformers 提供的标准方法，将 messages 列表转换为模型可接受的输入格式：

```python
# 构造对话消息
messages = [
    {"role": "system", "content": "你是一个乐于助人的AI助手"},
    {"role": "user", "content": "请给我解释一下什么是深度学习？"}
]

# 使用聊天模板格式化
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,              # 先不转token，便于查看原始格式
    add_generation_prompt=True   # 添加生成提示前缀
)

print("格式化后的输入：")
print(text)
```

### 输出格式预览

```
<|im_start|>system
你是一个乐于助人的AI助手<|im_end|>
<|im_start|>user
请给我解释一下什么是深度学习？<|im_end|>
<|im_start|>assistant
```

> `add_generation_prompt=True` 会在末尾添加 `<|im_start|>assistant\n`，告诉模型开始生成回答

---

## 四、模型推理生成

### 基础推理

```python
# 将文本转为模型输入 tensor
inputs = tokenizer([text], return_tensors="pt").to(model.device)

# 模型生成
outputs = model.generate(
    **inputs,
    max_new_tokens=512,    # 最大生成 token 数
    temperature=0.7,       # 随机性控制
    do_sample=True,        # 开启采样
    top_p=0.9,             # 核采样
)

# 解码输出
result = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(result)
```

### 生成参数详解

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `max_new_tokens` | 最大生成新token数 | 256-2048 |
| `temperature` | 随机性，越高越有创意 | 0.6-0.8 |
| `do_sample` | 是否采样（关闭=贪心） | True |
| `top_p` | 核采样概率质量阈值 | 0.8-0.95 |
| `top_k` | Top-K 采样候选数 | 40-50 |
| `repetition_penalty` | 抑制重复的惩罚因子 | 1.0-1.2 |

---

## 五、输出分析：提取思考过程

蒸馏 1.5B 模型的输出包含 `[think]` 标签包裹的思考过程，以及标签外的最终答案：

```python
# 提取思考过程和最终答案
def parse_r1_output(full_output):
    """解析 R1 蒸馏模型的输出，分离思考过程和最终答案"""
    
    # 找到 [think] 和 [/think] 标签之间的内容
    import re
    think_pattern = re.compile(r'\[think\](.*?)\[/think\]', re.DOTALL)
    think_match = think_pattern.search(full_output)
    
    think_content = ""
    final_answer = full_output
    
    if think_match:
        think_content = think_match.group(1).strip()
        final_answer = full_output.replace(think_match.group(0), "").strip()
    
    return think_content, final_answer

# 使用示例
full_output = result  # 模型原始输出
think, answer = parse_r1_output(full_output)

print("=== 思考过程 ===")
print(think)
print("\n=== 最终答案 ===")
print(answer)
```

### 实际输出示例

```
=== 思考过程 ===
用户问的是深度学习的定义。这是个基础问题，我需要回答清晰。
首先，深度学习是机器学习的一个分支，核心是神经网络...
然后应该提到关键概念：多层网络、反向传播、自动特征提取...
最好举个简单例子帮助理解...
还需要区分深度学习和传统机器学习的区别...

=== 最终答案 ===
深度学习是机器学习的一个重要分支，它使用多层人工神经网络
（深度神经网络）来学习数据的层次化表示。

核心特点：
1. **自动特征提取**：无需人工设计特征，模型自动从原始数据中学习
2. **层次化学习**：浅层学习简单特征（边缘、颜色），深层学习复杂模式
3. **端到端训练**：从输入到输出直接优化

与传统的浅层学习相比，深度学习在处理图像、语音、文本等
非结构化数据时表现出色...
```

---

## 六、批量推理封装

### 封装为通用聊天函数

```python
def chat_with_r1_distill(messages, max_new_tokens=512, temperature=0.7):
    """与 R1 蒸馏模型对话的通用函数"""
    
    # 格式化输入
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    # Tokenize
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    
    # 推理
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        do_sample=True,
        top_p=0.9,
        pad_token_id=tokenizer.eos_token_id
    )
    
    # 解码
    response = tokenizer.decode(
        outputs[0][len(inputs[0]):],  # 只取新生成的部分
        skip_special_tokens=True
    )
    
    return response

# 测试
response = chat_with_r1_distill([
    {"role": "user", "content": "Python中list和tuple有什么区别？"}
])
print(response)
```

---

## 七、模型加载方式对比

### 方式一：ModelScope 加载（推荐）

```python
from modelscope import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained("deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B", ...)
```

**优点**：国内速度快，无需代理

### 方式二：HuggingFace 加载

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained("deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B", ...)
```

**优点**：生态最完整，但国内可能需要镜像

### 方式三：本地路径加载

```python
model = AutoModelForCausalLM.from_pretrained("./models/DeepSeek-R1-Distill-Qwen-1.5B", ...)
```

**优点**：离线可用，无网络依赖

---

## 总结

DeepSeek R1 蒸馏 1.5B Qwen 模型调用流程：

1. **ModelScope 加载** → `AutoModelForCausalLM` + `AutoTokenizer`
2. **构造消息** → messages 列表（system + user）
3. **apply_chat_template** → 转换为模型输入格式
4. **model.generate** → 带参数控制生成
5. **解码输出** → `tokenizer.decode` 还原文本
6. **提取思考链** → 解析 `[think]...[/think]` 标签

1.5B 版本虽然参数少，但通过 R1 蒸馏获得了相当的推理能力，且对硬件要求极低，是入门大模型推理的绝佳选择。
