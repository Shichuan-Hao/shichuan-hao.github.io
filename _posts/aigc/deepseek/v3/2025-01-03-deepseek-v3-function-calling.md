---
title: DeepSeek V3 Function Calling 实现方法
description: 通过OpenWeather API集成，详解DeepSeek V3的Function Calling功能实现全流程
author: hsc
date: 2025-01-03 08:00:00 +0800
categories: [AI Agent, 大模型部署, DeepSeek]
tags: [DeepSeek V3, Function Calling, API, Agent]
---

## 背景：什么是Function Calling？

Function Calling（函数调用）是让大语言模型<hl=red>调用外部函数</hl>的核心能力。模型不再仅凭借自身训练数据进行回答，而是可以额外挂载一个函数库，根据用户提问自动检索并调用合适的外部函数获取实时数据，再基于函数运行结果进行回答。

### 基本流程

```
用户提问 → 模型分析意图 → 自动选择函数 → 本地执行函数 → 
获取结果 → 模型基于结果生成回答
```

核心价值：<hl=red>让模型"长出双手"，能够与外部世界交互</hl>，例如：
- 查询实时天气
- 搜索最新信息
- 调用数据库
- 执行计算

---

## 一、外部工具API简介

API（Application Program Interface）即应用程序接口。以 OpenWeather 为例：

- **OpenWeather**：提供全球气象数据服务
- **免费额度**：一定限度内完全免费
- **无需科学上网**：国内可直接访问注册
- 注册地址：https://openweathermap.org/

---

## 二、OpenWeather 注册与API Key获取

### Step 1：注册账号
访问 https://openweathermap.org/ → 点击 Sign → Create Account 完成注册（支持国内邮箱）

### Step 2：获取 API Key
注册完成后，在 API Keys 页面查看已激活的Key

### Step 3：设为环境变量

```python
import os
open_weather_key = os.getenv("OPENWEATHER_API_KEY")
```

---

## 三、封装天气查询函数

### 通过API获取天气数据

```python
import requests

url = "https://api.openweathermap.org/data/2.5/weather"
params = {
    "q": "Beijing",               # 城市名（必须英文）
    "appid": open_weather_key,    # API key
    "units": "metric",            # 摄氏度
    "lang": "zh_cn"               # 中文输出
}

response = requests.get(url, params=params)  # 200表示成功
data = response.json()
```

### 封装为可复用函数

```python
import json

def get_weather(loc):
    """
    查询即时天气函数
    :param loc: 城市英文名称，如 'Beijing'
    :return: JSON格式的天气信息字符串
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": loc,
        "appid": open_weather_key,
        "units": "metric",
        "lang": "zh_cn"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return json.dumps(data)
```

---

## 四、Function Calling 核心步骤

### 4.1 定义函数描述（Tools）

模型需要知道有哪些函数可以调用、每个函数的功能和参数：

```python
# Step 1: 定义函数描述（JSON Schema格式）
get_weather_function = {
    'name': 'get_weather',
    'description': '查询即时天气函数，根据输入的城市名称，查询对应城市的实时天气',
    'parameters': {
        'type': 'object',
        'properties': {
            'loc': {
                'description': "城市名称，注意，中国的城市需要用对应城市的英文名称代替，例如如果需要查询北京市天气，则loc参数需要输入'Beijing'",
                'type': 'string'
            }
        },
        'required': ['loc']
    }
}

# Step 2: 创建函数名→函数对象的映射
available_functions = {
    "get_weather": get_weather,
}

# Step 3: 封装为 tools 对象
tools = [
    {
        "type": "function",
        "function": get_weather_function
    }
]
```

### 三个关键参数说明

| 参数 | 说明 |
|------|------|
| **name** | 函数名称，用于函数库检索（a-z, A-Z, 0-9, 下划线） |
| **description** | <hl=red>模型识别函数功能的核心依据</hl>，需详细描述 |
| **parameters** | JSON Schema格式，描述函数参数类型和要求 |

---

## 五、First Response：模型自动选择函数

### 不传tools：模型无法查询天气

```python
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "请帮我查询北京地区今日天气情况"}]
)
print(response.choices[0].message.content)
# 输出：您好，建议您联网获取时效性较强的信息...
```

### 传入tools：模型自动识别并调用函数

```python
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "请帮我查询北京地区今日天气情况"}],
    tools=tools,          # 传入函数库
)

response_message = response.choices[0].message
```

此时返回的 `response_message` 中：
- `content` 为空字符串
- `tool_calls` 包含调用函数的完整信息

### 提取函数调用信息

```python
# 获取函数名
function_name = response_message.tool_calls[0].function.name
# → 'get_weather'

# 获取函数参数（JSON字符串，需解析）
function_args = json.loads(response_message.tool_calls[0].function.arguments)
# → {'loc': 'Beijing'}

# 获取对应的函数对象
fuction_to_call = available_functions[function_name]
```

> <hl=red>model='deepseek-chat'</hl> —— DeepSeek v3自动将"北京"识别为需要传入`loc='Beijing'`的参数！

---

## 六、Second Response：基于函数结果生成回答

### Step 1：本地执行函数

```python
# 使用 ** 语法将字典展开为关键字参数
function_response = fuction_to_call(**function_args)
# 返回完整的天气JSON数据
```

`**` 展开语法说明：
```python
def test(a, b, c):
    return a + b + c

args = {'a': 1, 'b': 2, 'c': 3}
result = test(**args)  # 等价于 test(a=1, b=2, c=3)
# → 6
```

### Step 2：追加消息到对话历史

<hl=red>这是Function Calling最关键的一步</hl>：

```python
# 追加第一次模型返回的assistant消息
messages.append(response_message.model_dump())

# 追加外部函数执行结果（role="tool"）
messages.append({
    "role": "tool",
    "content": function_response,
    "tool_call_id": response_message.tool_calls[0].id
})
```

### Step 3：第二次调用模型

```python
second_response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages
)

print(second_response.choices[0].message.content)
# 输出：
# 北京地区今日天气情况如下：
# - 天气状况：阴，多云
# - 当前温度：4.94°C
# - 体感温度：1.77°C
# - 湿度：25%
# - 风速：4.03米/秒
# - 能见度：10000米
# - 气压：1020 hPa
# 请注意保暖，适当增添衣物！
```

---

## 七、封装通用 run_conv 函数

将上述完整流程封装为一个自动判断的通用函数：

```python
def run_conv(messages, api_key, tools=None, functions_list=None, model="deepseek-chat"):
    """能够自动执行外部函数调用的Chat对话模型"""
    
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    # 没有外部函数库 → 普通对话
    if tools == None:
        response = client.chat.completions.create(
            model=model, messages=messages
        )
        return response.choices[0].message.content
    
    # 有外部函数库 → Function Calling流程
    else:
        available_functions = {func.__name__: func for func in functions_list}
        
        # First response: 获取函数调用信息
        response = client.chat.completions.create(
            model=model, messages=messages, tools=tools,
        )
        response_message = response.choices[0].message
        
        function_name = response_message.tool_calls[0].function.name
        fuction_to_call = available_functions[function_name]
        function_args = json.loads(response_message.tool_calls[0].function.arguments)
        
        # 本地执行函数
        function_response = fuction_to_call(**function_args)
        
        # 拼接消息
        messages.append(response_message.model_dump())
        messages.append({
            "role": "tool",
            "content": function_response,
            "tool_call_id": response_message.tool_calls[0].id
        })
        
        # Second response: 基于函数结果的回答
        second_response = client.chat.completions.create(
            model=model, messages=messages
        )
        return second_response.choices[0].message.content
```

### 使用示例

```python
# 普通问答（无tools）
messages = [{"role": "user", "content": "请问什么是机器学习？"}]
result = run_conv(messages=messages, api_key=ds_api_key)

# 天气查询（有tools）
messages = [{"role": "user", "content": "请问北京今天天气如何？"}]
result = run_conv(
    messages=messages, 
    api_key=ds_api_key,
    tools=tools,                    # 函数描述
    functions_list=[get_weather]    # 函数对象列表
)
```

---

## 总结：Function Calling 完整流程

```
1. 定义函数（get_weather）
       ↓
2. 创建函数描述（JSON Schema）
       ↓
3. 封装为 tools 对象
       ↓
4. First Call: 传入 messages + tools
   → 模型返回 tool_calls（含函数名 + 参数）
       ↓
5. 提取 function_name + function_args
       ↓
6. 本地执行函数：fuction(**function_args)
       ↓
7. 追加 tool 消息到 messages
       ↓
8. Second Call: 传入更新后的 messages
   → 模型基于函数结果生成自然语言回答
```

<hl=red>核心要点</hl>：
- Functions参数的 `description` 是模型理解函数用途的**唯一渠道**
- 函数在**本地执行**，不在模型服务器执行
- 必须手动追加 `role: "tool"` 消息，模型才能"看到"函数结果
- `tool_choice` 参数可控制是否自动选择函数（`"auto"`）或强制指定某个函数
