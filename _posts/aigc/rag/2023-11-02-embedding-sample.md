---
title: Embedding 初级应用：用向量相似度提升 Function Calling 稳定性
description:
author: hsc
date: 2024-09-12 19:27:00 +0800
categories: [AI Agent, RAG]
tags: []
math: true
mermaid: true
---

Function calling 是构建 Agent 的核心能力，但**并不是所有模型都能稳定地选对外部函数**。本文介绍一种低成本、易落地的替代方案：用 Embedding 将"用户问题"和"函数说明"都转成向量，通过计算相似度来判断该调用哪个函数，从而绕过模型自身 Function calling 不稳定的问题。

我们会先用一个简化的代码示例讲清楚原理，再以亚马逊美食评论数据集为例，演示如何将这套方法迁移到真实的语义分类场景中。

---

## 一、问题：Function calling 为什么不总是可靠？

Function calling 让大模型从"聊天机器人"升级为"能干活儿的 Agent"——它能查数据库、发邮件、调 API。但它的准确性高度依赖模型自身能力：

| 模型 | Function calling 表现 |
|---|---|
| GPT-4 / GPT-4-turbo | 准确率高，但功能极为相似的函数间仍会误判 |
| GPT-3.5 | 相似函数容易混淆（如：代码执行 vs 绘图函数） |
| Gemini Pro | 面对大量复杂函数时难以有效调用 |
| ChatGLM3 等国产开源模型 | 单一函数也难以做到每次响应 |

也就是说，**当你用的模型不够强，Function calling 就不可靠；但 Agent 又不能没有这个能力。**

一个自然的思路是：能不能不依赖模型自动选函数，而是**自己手动判断**该用哪个？问题来了——不用模型判断，还有什么方法能做到？

答案是 **Embedding**。

---

## 二、核心思路：用 Embedding 替代模型做函数选择

Embedding 的本质是将文本映射为高维向量，语义相近的文本，向量在空间中距离也更近。利用这个特性，我们可以：

> 把「用户说的话」和「每个函数的描述文档」都转成向量，比较它们的相似度，相似度最高的就是要调用的函数。

具体有两种落地方式：

### 方法一：零样本分类（无需标注数据，直接上）

直接拿用户问题与函数说明做相似度匹配：

```
用户问题 → Embedding → 向量A
函数说明 → Embedding → 向量B
计算 cos(A, B) → 相似度越高，越该调用这个函数
```

**示例代码：**

```python
import os
from openai import OpenAI
from zai import ZhipuAiClient
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# ---------- 初始化 Embedding 模型 ----------
zhipu_client = ZhipuAiClient(api_key=os.getenv("ZHIPUAI_API_KEY"))

# ---------- 准备数据：函数描述 + 两个用户问题 ----------
sql_func_desc = (
    "用于执行一段SQL代码，并最终获取telco_db数据库数据查询结果，"
    "核心功能是将输入的SQL代码传输至MySQL环境中进行运行，"
    "并最终返回SQL代码运行结果。"
)

q1 = "请帮我查下telco_db数据库中所有用户的性别和年龄信息。"  # 相关
q2 = "请帮我介绍下什么是机器学习？"                            # 无关

# ---------- 批量 Embedding ----------
texts = (sql_func_desc, q1, q2)
res = zhipu_client.embeddings.create(
    model="embedding-2",
    input=texts,
    encoding_format="float"
)

# ---------- 计算余弦相似度矩阵 ----------
similarity_matrix = cosine_similarity([
    res.data[0].embedding,  # 函数描述
    res.data[1].embedding,  # q1: 查数据库
    res.data[2].embedding,  # q2: 闲聊
])

print(similarity_matrix)
```

输出结果：

```
索引 [0] = 函数描述，[1] = 数据库查询，[2] = 闲聊问题

                  [0]函数    [1]查库    [2]闲聊
[0] 函数描述      1.00       0.52      0.31
[1] 查数据库      0.52       1.00      0.23
[2] 闲聊问题      0.31       0.23      1.00
```

**解读：** 函数描述与查数据库问题相似度 0.52，与闲聊问题仅 0.31。差距明显，足以做判断。

**零样本分类的局限：** 需要预先确定一个"相似度阈值"（比如 > 0.5 才调用），这个阈值的设定需要经验积累，或通过聚类分析来辅助决策。

---

### 方法二：有监督分类（需要标注数据，但更精准）

流程如下：

```
Step 1: 积累用户问题，人工标注每个问题该调用哪个函数
Step 2: 对所有问题做 Embedding → 得到数值特征
Step 3: 用这些特征训练一个分类模型（如 SVM、随机森林等）
Step 4: 新问题来了 → Embedding → 模型预测 → 决定调用哪个函数
```

这本质上是经典的 **Word2Vec + 机器学习** 文本分类流水线，只是因为现在 Embedding 模型更强了（能理解上下文语义），效果比早年更好。

> **标注小技巧：** 如果人工标注成本太高，可以用 GPT-4 的 Function calling 结果来自动打标签，相当于"强模型为弱模型生产训练数据"。

---

### 两种方法对比

| | 零样本分类 | 有监督分类 |
|---|---|---|
| 是否需要标注数据 | 否 | 是 |
| 实现难度 | 低 | 中 |
| 准确率 | 一般 | 较高 |
| 适用场景 | 函数少、快速验证 | 函数多、生产环境 |
| 维护成本 | 调阈值 | 重训练 |

---

## 三、实战：用亚马逊美食评论数据集验证

为了验证 Embedding 在语义分类上的效果，我们使用 **Amazon Fine Food Reviews** 数据集。选择它有三个理由：

1. **带标签**：每条评论有 1-5 星评分，天然就是"意图标签"（好评/差评 = 不同的意图类别）
2. **数据量大**：50 万+ 条评论，覆盖 1999-2012 年
3. **业界认可**：OpenAI 官方 cookbook 推荐使用的教学数据集

在这个数据集上，我们可以依次验证：

- **零样本分类**：将评论 Embedding 后，用聚类观察不同评分是否自然分开
- **有监督分类**：用评分作为标签，训练分类器预测一条评论是好评还是差评
- **迁移到 Agent**：将"好评/差评分类"的方法论，直接搬到"选函数/不选函数"的场景

最终目标是将这套方法迁移到 Agent 开发中——当你对 Embedding 分类的流程足够熟悉，把它套用到 Function calling 场景只需要改变"标签的含义"即可。

---

## 四、总结与延伸

**一句话回顾：** 当模型自带的 Function calling 不够稳，用 Embedding + 相似度（或分类模型）手动判断该调用哪个函数，是成本最低、效果可观的替代方案。

**补充两点背景知识：**

1. OpenAI 从未公开 Function calling 的技术细节，但业界普遍猜测其内部就是"意图识别模型 + Embedding 辅助判断"的组合。换句话说，我们这节讲的思路，很可能就是 Function calling 的底层实现原理。

2. 除了 Embedding，**微调（Fine-tuning）** 也是提升 Function calling 稳定性的手段。两者可以互补——Embedding 做粗筛，微调做精判。

---

*下一篇将具体展示在亚马逊评论数据集上的 Embedding 分类实验及代码。*
