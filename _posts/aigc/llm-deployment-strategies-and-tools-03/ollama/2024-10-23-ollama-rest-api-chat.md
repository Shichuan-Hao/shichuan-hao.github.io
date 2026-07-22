---
title: Ollama REST API - chat 接口
description: Ollama 本地部署 DeepSeek R1 模型
author: hsc
date: 2024-10-23 10:27:00 +0800
categories: [AI Agent]
tags: [DeepSeek, Ollama, DeepSeek R1]
---

Ollama 服务启动后会提供一系列原生 REST API 端点。

通过这些 Endpoints 可以在代码环境下与 ollama 启动的大模型进行交互、管理模型和获取相关信息。

其中有两个 Endpoints 是最重要的，分别是：
- <hl=red>`POST /api/generate`</hl>
- <hl=red>`POST /api/chat`</hl>

其它端点情况：
- `POST /api/create`
- `POST /api/tags`
- `POST /api/show`
- `POST /api/copy`
- `POST /api/delete`
- `POST /api/pull`
- `POST /api/push`
- `POST /api/embed`
- `POST /api/ps`

<hr/>

## /api/generate 接口参数概览

此接口使用提供的模型在聊天中生成下一条消息。

与 `/api/generate` 的参数基本一致，但是在请求的参数上会根据聊天场景进行调整。主要调整的是：
1. 不再使用 `prompt` 参数，而是使用 `messages` 参数
2. 新增 `tools` 参数，用来支持工具调用。

其可以使用的具体参数如下所示：

**常规参数**

| 参数名       | 类型      | 描述                                                         |
| ------------ | --------- | ------------------------------------------------------------ |
| **model**    | *(必需)*  | 模型名称。                                                   |
| <font color="red">**messages**</font> | *(必需)*  | 聊天的消息，用于保持聊天记忆。                               |
| <font color="red">**tools**</font>    | *(可选)*  | JSON 中的工具列表，供模型使用（如果支持）。                 |


**消息对象字段**

| 字段名       | 描述                                                         |
| ------------ | ------------------------------------------------------------ |
| <font color="red">**role**</font>     | 消息的角色，可以是 `system`、`user`、`assistant` 或 `tool`。 |
| <font color="red">**content**</font>  | 消息的内容。                                                 |
| **images**   | *(可选)* 要在消息中包含的图像列表（适用于多模态模型，如 llava）。 |
| **tool_calls** | *(可选)* 模型希望使用的 JSON 中的工具列表。               |

**高级参数（可惜）**

| 参数名       | 描述                                                         |
| ------------ | ------------------------------------------------------------ |
| **format**   | 返回响应的格式。格式可以是 `json` 或 JSON 模式。            |
| <font color="red">**options**</font>  | 文档中列出的其他模型参数，例如 `temperature`。              |
| **stream**   | 如果为 `false`，响应将作为单个响应对象返回，而不是对象流。  |
| <font color="red">**keep_alive**</font> | 控制模型在请求后保持加载的时间（默认：5分钟）。           |

其中，Options 参数说明：

| 参数名 | 描述 | 值类型 | 示例用法 |
| --------------- | ------------------------------------------------------------ | ------ | ---------------------- |
| mirostat | 启用 Mirostat 采样以控制困惑度。（默认：0，0 = 禁用，1 = Mirostat，2 = Mirostat 2.0） | int | mirostat 0 |
| mirostat_eta| 影响算法对生成文本反馈的响应速度。较低的学习率会导致调整较慢，而较高的学习率会使算法更具响应性。（默认：0.1） | float | mirostat_eta 0.1 |
| mirostat_tau| 控制输出的连贯性和多样性之间的平衡。较低的值会导致更集中和连贯的文本。（默认：5.0） | float | mirostat_tau 5.0 |
| <font color="red">num_ctx</font> | 设置用于生成下一个标记的上下文窗口大小。（默认：2048）, 影响的是模型可以一次记住的最大 token 数量。 | int | num_ctx 4096|
| repeat_last_n| 设置模型回溯的范围以防止重复。（默认：64，0 = 禁用，-1 = num_ctx） | int | repeat_last_n 64 |
| repeat_penalty| 设置惩罚重复的强度。较高的值（例如 1.5）会更强烈地惩罚重复，而较低的值（例如 0.9）会更宽松。（默认：1.1） | float | repeat_penalty 1.1 |
| <font color="red">temperature</font> | 模型的温度。增加温度会使模型的回答更具创造性。（默认：0.8） | float | temperature 0.7 |
| seed | 设置用于生成的随机数种子。将其设置为特定数字将使模型对相同提示生成相同的文本。（默认：0） | int | seed 42 |
| <font color="red">stop</font> | 设置使用的停止序列。当遇到此模式时，LLM 将停止生成文本并返回。可以通过在 modelfile 中指定多个单独的停止参数来设置多个停止模式。 | string | stop "AI assistant:" |
| <font color="red">num_predict</font> | 生成文本时要预测的最大标记数。（默认：-1，无限生成）,影响模型最大可以生成的 token 数量。 | int | num_predict 42 |
| top_k | 降低生成无意义文本的概率。较高的值（例如 100）会给出更多样化的答案，而较低的值（例如 10）会更保守。（默认：40） | int | top_k 40 |
| top_p | 与 top-k 一起工作。较高的值（例如 0.95）会导致更具多样性的文本，而较低的值（例如 0.5）会生成更集中和保守的文本。（默认：0.9） | float | top_p 0.9 |
| min_p | top_p 的替代方案，旨在确保质量和多样性之间的平衡。参数 p 表示考虑标记的最小概率，相对于最可能标记的概率。例如，p=0.05 时，最可能的标记概率为 0.9，值小于 0.045 的 logits 会被过滤掉。（默认：0.0） | float | min_p 0.05 |
