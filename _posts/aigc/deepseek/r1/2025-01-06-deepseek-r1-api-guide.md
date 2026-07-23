---
title: DeepSeek R1 API 调用指南
description: 深入解析 DeepSeek R1 推理模型 API，掌握 reasoning_content 提取与代码生成应用
author: hsc
date: 2025-01-06 08:00:00 +0800
categories: [AI Agent, 大模型部署, DeepSeek]
tags: [DeepSeek R1, API, Reasoning, 推理模型]
---

## 背景：DeepSeek R1 是什么？

DeepSeek R1 是 DeepSeek 推出的**推理增强模型**，对应 `deepseek-reasoner`。它的核心设计理念是：<hl=red>在回答问题之前，先进行深度思考（Chain of Thought, CoT）</hl>，然后用自然语言输出最终答案。

### R1 与 V3 的定位对比

| 特性 | DeepSeek V3 | DeepSeek R1 |
|------|------------|------------|
| **模型ID** | `deepseek-chat` | `deepseek-reasoner` |
| **核心能力** | 通用对话 | 深度推理 |
| **思考过程** | 不提供 | 提供 `reasoning_content` |
| **Function Calling** | ✅ 支持 | ❌ 不支持 |
| **适用场景** | 聊天、翻译、摘要 | 数学、编程、逻辑推理 |

### R1 vs OpenAI o1 价格对比

<hl=red>R1 的价格仅为 OpenAI o1 的 1/50！</hl>

| 模型 | 输入价格 (每百万token) | 输出价格 (每百万token) |
|------|---------------------|---------------------|
| OpenAI o1 | $15.00 | $60.00 |
| **DeepSeek R1** | **$0.55** | **$2.19** |
| DeepSeek V3 | $0.27 | $1.10 |

---

## 一、R1 API 调用基础

### 安装依赖

```python
!pip install openai
```

### 基础调用

```python
from openai import OpenAI

client = OpenAI(
    api_key=ds_api_key,
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-reasoner",  # ← 关键：使用 deepseek-reasoner
    messages=[
        {"role": "user", "content": "9.11和9.8哪个更大？"}
    ]
)
```

### 返回值分析

R1 的返回与 V3 有重要区别：

```python
# V3 返回结构
response.choices[0].message.content          # 直接答案
# → "9.8更大。"

# R1 返回结构
response.choices[0].message.content          # 最终答案
response.choices[0].message.reasoning_content # ← 思考过程（CoT）
```

<hl=red>reasoning_content 是 R1 最独特的特性</hl>，它记录了模型的中间推理步骤。

---

## 二、提取推理过程

### reasoning_content 示例

```python
response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[
        {"role": "user", "content": "9.11和9.8哪个更大？"}
    ]
)

# 思考过程：模型逐步推理
print(response.choices[0].message.reasoning_content)
```

模型内部推理过程可能是：
```
首先，对比9.11和9.8...
9.11的整数部分是9，9.8的整数部分也是9...
比较小数部分：0.11 vs 0.8...
0.11 < 0.8，所以9.11 < 9.8...
因此9.8更大。
```

### 处理 reasoning_content 为 None

并非所有情况下 R1 都会返回 reasoning_content。当回答较简单时可能为 None：

```python
reasoning_content = response.choices[0].message.reasoning_content

if reasoning_content:
    print(f"思考过程：\n{reasoning_content}")
    print(f"\n最终答案：\n{response.choices[0].message.content}")
else:
    print(f"答案：\n{response.choices[0].message.content}")
```

---

## 三、R1 的参数限制

<hl=red>R1 不支持以下 V3 中的参数</hl>：

| 不支持的参数 | 替代方案 |
|------------|---------|
| `temperature` | 不可调整 |
| `top_p` | 不可调整 |
| `presence_penalty` | 不可调整 |
| `frequency_penalty` | 不可调整 |
| `tools`（Function Calling） | 使用 V3 |
| `logprobs` | 不可用 |

### 支持的参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `model` | `"deepseek-reasoner"` | 必填 |
| `messages` | 对话消息列表 | 必填 |
| `max_tokens` | 最大输出token数 | 8,000 |
| `stream` | 是否流式输出 | false |

> `max_tokens` 最大为 8K，上下文窗口支持 64K。

---

## 四、R1 代码生成实战：贪吃蛇游戏

### 提示词设计

```python
prompt = """
写一个完整的贪吃蛇游戏HTML代码，要求：
1. 包含完整的HTML/CSS/JavaScript
2. 游戏界面美观，使用现代设计风格
3. 支持键盘方向键控制蛇的移动
4. 显示得分
5. 游戏结束时有重新开始按钮
6. 不需要额外说明，直接输出完整可运行的HTML代码
"""
```

### 调用 R1 生成游戏代码

```python
response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[
        {"role": "user", "content": prompt}
    ],
    max_tokens=8000
)

# 查看推理过程
print("=== 思考过程 ===")
print(response.choices[0].message.reasoning_content[:500])

# 查看生成的代码
print("\n=== 生成的代码 ===")
print(response.choices[0].message.content[:1000])
```

### R1 推理过程分析

在生成贪吃蛇游戏的代码前，R1 的 reasoning_content 会展示类似以下的思考：

```
我需要创建一个完整的贪吃蛇游戏HTML文件...
游戏需要的元素：
1. 画布用于绘制游戏
2. 蛇的身体用数组存储坐标
3. 食物的随机位置
4. 方向控制
5. 碰撞检测（墙壁和自身）
6. 得分系统
7. 重新开始按钮
...
```

---

## 五、R1 在ML建模中的应用

### 场景：使用机器学习预测房价

```python
prompt = """
请用Python实现一个房价预测模型。要求：
1. 使用加州房价数据集（sklearn California Housing）
2. 数据预处理：处理缺失值、标准化
3. 使用随机森林回归模型
4. 输出RMSE作为评估指标
5. 包含完整注释
"""
```

### R1 生成的代码（核心结构）

```python
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
import numpy as np

# 1. 加载加州房价数据集
data = fetch_california_housing()
X, y = data.data, data.target

# 2. 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 3. 特征标准化
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# 4. 随机森林回归
model = RandomForestRegressor(n_estimators=150, random_state=42)
model.fit(X_train, y_train)

# 5. 预测与评估
y_pred = model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"RMSE: {rmse:.3f}")
```

---

## 六、V3 vs R1 选择策略

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| 日常对话、翻译 | V3 | 快速、便宜 |
| 复杂数学问题 | **R1** | 推理能力强，CoT减少错误 |
| 代码开发 | **R1** | 思考过程通常包含架构设计 |
| 逻辑推理 | **R1** | CoT有助于逐步推理 |
| 需要外部工具 | V3 | R1不支持Function Calling |
| 需要控制随机性 | V3 | R1不支持temperature参数 |

### 最佳实践

<hl=red>先用 R1 解决复杂问题（数学、代码），需要外部工具时再切换回 V3</hl>。可以在同一个应用中混合使用两个模型：

```python
def smart_chat(messages, need_tools=False):
    """智能选择模型"""
    if need_tools:
        # 需要Function Calling → 使用V3
        return client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools
        )
    else:
        # 复杂推理 → 使用R1
        return client.chat.completions.create(
            model="deepseek-reasoner",
            messages=messages
        )
```

---

## 总结

DeepSeek R1 作为推理增强模型，核心差异在于：

1. **reasoning_content** — 可查看模型的思考链（CoT），这是理解模型决策逻辑的窗口
2. **价格仅为 o1 的 1/50** — 极致的性价比
3. **参数精简** — 不支持 Function Calling 和温度控制，但换来了更强的推理能力
4. **适用场景** — 数学、编程、逻辑推理等需要深度思考的任务
5. **最佳实践** — 与 V3 搭配使用，根据任务类型灵活切换
