---
title: DeepSeek V3 API 接入指南
description: DeepSeek V3 API 调用全流程解析，从注册到多轮对话机器人开发
author: hsc
date: 2024-01-02 08:00:00 +0800
categories: [AI Agent, DeepSeek]
tags: [DeepSeek V3, API, Chat Completion]
---

## 背景：DeepSeek V3 为何值得关注？

DeepSeek V3 是深度求索公司推出的旗舰大模型，API调用风格与OpenAI <hl=red>完全兼容</hl>，意味着你可以直接使用 `openai` Python库无缝迁移。

### 核心优势
- 价格仅为GPT-4o的**3%-6%**（输入价格是GPT-4o的6%，输出价格是GPT-4o的3%）
- 新用户注册即送**10元额度**（约500万token）
- API调用**不限速**
- 完全支持 Function Calling、提示词缓存、Json Output 等功能

---

## 一、账号注册与API Key获取

### 注册流程

1. 访问 DeepSeek 官网：https://platform.deepseek.com/
2. 点击注册，使用手机号或邮箱完成注册
3. 在 API Keys 页面创建新的 API Key：https://platform.deepseek.com/api_keys
4. 新用户注册即赠送10元体验额度

### API Key 管理

建议将API Key设置为环境变量，避免硬编码在代码中：

- Linux/Mac：`export DEEPSEEK_API_KEY="your-api-key"`
- 或在Python中读取：`ds_api_key = os.getenv("DEEPSEEK_API_KEY")`

---

## 二、DeepSeek V3 基本调用流程

### 安装依赖

```python
!pip install openai
```

### 调用对比：GPT-4o vs DeepSeek V3

两者的调用代码几乎**完全相同**，只需修改两个参数：

| 参数 | GPT-4o | DeepSeek V3 |
|------|--------|-------------|
| `model` | `"gpt-4o-mini"` | `"deepseek-chat"` |
| `base_url` | `"https://api.openai.com/v1"` | `"https://api.deepseek.com"` |

### 基础调用示例

```python
from openai import OpenAI

# 实例化客户端 — 关键区别：base_url指向DeepSeek
client = OpenAI(
    api_key=ds_api_key, 
    base_url="https://api.deepseek.com"
)

# 调用 deepseek-chat 模型
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "你好，好久不见!"}
    ]
)

# 输出响应内容
print(response.choices[0].message.content)
# 输出: 你好！好久不见！最近过得怎么样？有什么想聊的吗？
```

### 查看支持的模型列表

```python
models_list = client.models.list()
print(models_list.data)
# [Model(id='deepseek-chat'), Model(id='deepseek-coder')]
```

<hl=red>当前支持 `deepseek-chat`（通用对话）和 `deepseek-coder`（代码生成）两个模型</hl>。

---

## 三、Messages 消息结构详解

`messages` 是API最核心的参数，支持三种角色：

### 3.1 System Message（系统消息）

用于设定AI的行为规则和背景信息：

```python
system_message = {
    "role": "system",
    "content": "你是一位大学教授。"
}
```

### 3.2 User Message（用户消息）

用户的输入内容，可以是纯文本或包含图片：

```python
# 纯文本
user_message = {
    "role": "user",
    "content": "你好，请介绍下你自己。"
}

# 带图片（DeepSeek v2.5+ 支持）
user_message_with_image = {
    "role": "user",
    "content": [
        {"type": "text", "text": "你能帮我介绍下这张图片吗？"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.png"}}
    ]
}
```

### 3.3 完整调用示例

```python
# 配置系统消息 + 用户消息
system_message = {"role": "system", "content": "你是一位大学教授。"}
user_message = {"role": "user", "content": "你好，请介绍下你自己。"}

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[system_message, user_message]
)

print(response.choices[0].message.content)
```

---

## 四、构建多轮对话机器人

核心原理：<hl=red>持续追加 `user` 和 `assistant` 消息到 messages 列表</hl>，模型即可"记住"对话历史。

### 核心函数实现

```python
def chat_with_DeepSeek(client, messages):
    """使用DeepSeek模型进行多轮对话的核心函数"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages
    )
    return response.choices[0].message.content

def create_message(role, content):
    """创建标准消息格式"""
    return {"role": role, "content": content}

def multi_round_chat():
    """多轮对话机器人"""
    messages = []
    # 初始化系统消息
    messages.append(create_message("system", "You are a helpful assistant."))
    
    while True:
        user_input = input("User: ")
        if user_input.lower() == 'exit':
            print("对话结束。")
            break
        
        # 追加用户消息
        messages.append(create_message("user", user_input))
        
        # 获取助手回复
        reply = chat_with_DeepSeek(client, messages)
        print(f"Assistant: {reply}")
        
        # 追加助手消息（关键：维持对话记忆）
        messages.append(create_message("assistant", reply))
```

### 对话效果演示

```
User: 你好，好久不见！
Assistant: 你好！好久不见，很高兴再次见到你！

User: 我叫陈明，请介绍下你自己
Assistant: 陈明，你好！我是一个人工智能助手...

User: 请问我叫什么名字？
Assistant: 你刚才告诉我，你的名字是陈明。
```

> <hl=red>关键机制</hl>：每次对话都将完整的 messages 历史传给模型，模型因此能"记住"上文信息。

---

## 五、核心参数汇总表

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| **model** | string | *必填* | 模型ID，如 `deepseek-chat` |
| **messages** | array | *必填* | 对话消息列表 |
| **temperature** | float | 1 | 控制随机性，0-2之间 |
| **top_p** | float | 1 | 核采样概率阈值 |
| **max_tokens** | int | — | 生成最大token数 |
| **frequency_penalty** | float | 0 | 降低重复惩罚，-2.0到2.0 |
| **presence_penalty** | float | 0 | 鼓励新话题惩罚，-2.0到2.0 |
| **stop** | string/array | — | 停止生成的序列 |
| **stream** | bool | false | 是否启用流式响应 |
| **tools** | array | — | Function Calling工具列表 |
| **response_format** | object | — | 输出格式，如 `json_object` |

### 参数调优建议

- **控制随机性**：`temperature` 和 `top_p` 二选一调整即可
- **降低重复**：适当增加 `frequency_penalty`
- **固定格式输出**：使用 `response_format={"type": "json_object"}`
- **实时展示**：开启 `stream=True`

---

## 六、函数封装技巧

在实际开发中，建议将URL识别等逻辑封装为可复用函数：

```python
import re

def extract_url_and_text(input_text):
    """提取用户输入中的URL和描述文本"""
    url_pattern = re.compile(r'(https?://[^\s]+)')
    url_match = url_pattern.search(input_text)
    
    if url_match:
        url = url_match.group(0)
        description = input_text.replace(url, '').strip()
        return description, url
    else:
        return input_text, None

def process_user_input(input_text):
    """根据是否包含URL，生成不同格式的消息"""
    description, url = extract_url_and_text(input_text)
    
    if url:
        # 带图片的消息
        return create_user_message_with_image(
            description or "请帮我分析这张图片的内容", 
            url
        )
    else:
        return create_message("user", description)
```

---

## 总结

DeepSeek V3的API接入流程可以概括为：

1. **注册获取API Key** → platform.deepseek.com
2. **安装openai库** → `pip install openai`
3. **创建客户端** → `base_url="https://api.deepseek.com"`
4. **选择模型** → `model="deepseek-chat"`
5. **构造messages** → System + User + Assistant历史
6. **调用create方法** → 获取响应

与OpenAI API的最大区别只有 `base_url` 和 `model` 两个参数。迁移成本极低，价格却便宜了90%以上。
