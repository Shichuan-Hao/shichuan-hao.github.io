---
title: Dify + DeepSeek搭建微信智能客服：Chatflow工作流全解析
description: 使用Dify和DeepSeek构建微信公众号智能客服工作流，涵盖Chatflow设计、LLM节点、知识检索、HTTP请求、问题分类器等核心环节。
excerpt: 使用Dify和DeepSeek构建微信公众号智能客服工作流，涵盖Chatflow设计、LLM节点、知识检索、HTTP请求、问题分类器等核心环节。
author: hsc
date: 2025-03-21 10:00:00 +0800
categories: [AI Agent, 低代码平台, Dify]
tags: [Dify, DeepSeek, 微信客服, Chatflow, 工作流, LLM, 知识检索]
math: true
mermaid: true
---
{% raw %}

## 从魔法书到智能助手：一场AI的进化之旅

想象一下，你手中有一本古老的魔法书，书中记载了无数知识和咒语。只要你提出问题，它就能给出答案。这本书就像早期的 **纯LLM对话机器人** ，它非常聪明，能够理解你的问题并给出准确的回答。但它有一个局限：它只能回答问题，无法主动采取行动。就像魔法书只能告诉你如何施展咒语，却不能帮你真正施展出来。

现在，想象一下，魔法书突然进化了！它不再只是一本书，而是变成了一个 **智能助手（Agent）** 。这个助手不仅能回答问题，还能主动帮你完成任务。比如，你告诉它：“帮我订一张去巴黎的机票”，它不仅能理解你的需求，还能自动搜索航班、比较价格，甚至帮你完成支付。它就像一个拥有自主意识的魔法精灵，能够独立思考和行动。

接下来，我们再想象一下，这个智能助手变得更加强大，它开始按照一套 **流程** 来执行任务。比如，当你告诉它：“帮我策划一次旅行”，它会按照预设的流程，依次完成订机票、订酒店、规划行程等步骤。工作流就像一条自动化的流水线，确保每个任务都能高效、准确地完成。


# Dify 中的概念

本处所讲的概念均为DIFY平台相关内容，切勿带入其他大模型开发流程。

## 聊天助手  

基本就是与大模型一问一答的状态，同时还会再增加上部分变量的引用来更好的回答问题。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217150050435_ff428a05.png)

## Agent  

利用大语言模型的推理能力，能够自主对复杂的人类任务进行目标规划、任务拆解、工具调用、过程迭代，并在没有人类干预的情况下完成任务。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217150432881_a88d2a25.png)

## 工作流  
工作流通过将复杂的任务分解成较小的步骤（dify中称节点）降低系统复杂度，减少了对提示词技术和模型推理能力的依赖，提高了 LLM 应用面向复杂任务的性能，提升了系统的可解释性、稳定性和容错性。

Dify 工作流分为两种类型：
- `Chatflow`：面向对话类情景，包括客户服务、语义搜索、以及其他需要在构建响应时进行多步逻辑的对话式应用程序。路径为：给出指令 → 生成内容 → 就内容进行多次讨论 → 重新生成结果 → 结束  
- `Workflow`：面向自动化和批处理情景，适合高质量翻译、数据分析、内容生成、电子邮件自动化等应用程序。路径为：给出指令 → 生成内容 → 结束

![image](/assets/img/posts/low-code-dify-coze-12/image-20250217141717348_54187818.png)

当前就是路径的展示，其中会涉及到两个关键的概念。

### 节点  
节点是工作流的关键构成，通过连接不同功能的节点，执行工作流的一系列操作，每个节点都可以做出特有的技能，比如常用的分类功能，或者是工具也可以作为节点来使用。

### 变量

变量用于串联工作流内前后节点的输入与输出，实现流程中的复杂处理逻辑，包含系统变量、环境变量和会话变量。用于每个节点处理完数据后传递给下一个节点使用。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217152342962_49e5ffd7.png)
变量展示。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217153351570_53c31f97.png)

# 2.节点介绍 
内置节点种类
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217153801980_81a05c8d.png)
内置工具种类
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217153849435_4bfa93aa.png)
主页面查看工具
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217154454329_846f59f6.png)

## 重点工作节点讲解

### 开始节点 

"开始" 节点是每个工作流应用（Chatflow / Workflow）必备的预设节点，为后续工作流节点以及应用的正常流转提供必要的初始信息，例如应用使用者所输入的内容、以及上传的文件等。
输入字段以及已经预设的系统变量
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217155211123_907d49ae.png)
输入字段部分可以设置为必填或者选填项，用于让应用使用者主动补全更多信息。例如在体检中要求使用者按照格式预先提供更多背景信息，如姓名、年龄、身体状况等。这些前置信息将有助于LLM生成质量更高的答复。
填入格式可以分为
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217155535762_c1b7bd32.png)

- 文本  
短文本，由应用使用者自行填写内容，最大长度 256 字符。  
- 段落  
长文本，允许应用使用者输入较长字符。 
- 下拉选项  
由应用开发者固定选项，应用使用者仅能选择预设选项，无法自行填写内容。 
- 数字  
仅允许用户输入数字。  
- 单文件  
允许应用使用者单独上传文件，支持文档类型文件、图片、音频、视频和其它文件类型。  
- 文件列表  
允许应用使用者批量上传文件，支持文档类型文件、图片、音频、视频和其它文件类型。 

### 系统变量
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217155211123_907d49ae.png)
| 变量名称           | 数据类型         | 说明                                                                 |
|------------------|--------------|--------------------------------------------------------------------|
| `sys.query`      | String       | 用户在对话框中初始输入的内容                                             |            
| `sys.files`      | Array[File]  | 用户在对话框内上传的图片                                                | 
| `sys.dialogue_count` | Number       | 用户在与 Chatflow 类型应用交互时的对话轮数。每轮对话后自动计数增加 1，可以和 if-else 节点搭配出丰富的分支逻辑。 | 
| `sys.conversation_id` | String       | 对话框交互会话的唯一标识符，将所有相关的消息分组到同一个对话中，确保 LLM 针对同一个主题和上下文持续对话   |   
| `sys.user_id`    | String       | 分配给每个应用用户的唯一标识符，用以区分不同的对话用户                                            |   
| `sys.app_id`     | String       | 应用 ID，系统会向每个 Workflow 应用分配一个唯一的标识符，用以区分不同的应用，并通过此参数记录当前应用的基本信息 | 
| `sys.workflow_id` | String       | Workflow ID，用于记录当前 Workflow 应用内所包含的所有节点信息                                    | 
| `sys.workflow_run_id` | String       | Workflow 应用运行 ID，用于记录 Workflow 应用中的运行情况                                      | 

### LLM节点

调用大语言模型的能力，处理用户在上一个节点传递过来的消息，并按照期望格式与内容进行输出，同时可以引入知识库内容做知识背景，方便答案生成。

进行模型参数配置  
温度： 通常是0-1的一个值，控制随机性。温度越接近0，结果越确定和重复，温度越接近1，结果越随机。

Top P： 控制结果的多样性。模型根据概率从候选词中选择，确保累积概率不超过预设的阈值P。

存在惩罚： 用于减少重复生成同一实体或信息，通过对已经生成的内容施加惩罚，使模型倾向于生成新的或不同的内容。参数值增加时，对于已经生成过的内容，模型在后续生成中被施加更大的惩罚，生成重复内容的可能性越低。

频率惩罚： 对过于频繁出现的词或短语施加惩罚，通过降低这些词的生成概率。随着参数值的增加，对频繁出现的词或短语施加更大的惩罚。较高的参数值会减少这些词的出现频率，从而增加文本的词汇多样性。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217161742256_c2df9a47.png)
上下文(可选)，一般用于只是检索之后使用，然后再将上下文内容引入到system prompt 或者user prompt。  
system部分直接输入想用的prompt即可，如果想引用变量直接输入{{变量名称}}  

主要场景：  

- 意图识别，在客服对话情景中，对用户问题进行意图识别和分类，导向下游不同的流程。

- 文本生成，在文章生成情景中，作为内容生成的节点，根据主题、关键词生成符合的文本内容。

- 内容分类，在邮件批处理情景中，对邮件的类型进行自动化分类，如咨询/投诉/垃圾邮件。  
**. . .**

### 知识检索

从知识库中检索与用户问题相关的文本内容，可作为下游 LLM 节点的上下文来使用。构建基于外部数据/知识的 AI 问答系统（RAG）工作流时候使用。(需要提前创建知识库)

知识库检索的下游节点一般为 LLM 节点，知识检索的输出变量 **result** 需要配置在 **LLM** 节点中的 上下文变量 内关联赋值。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217174039012_d6e29164.png)
当用户提问时，若在知识检索中召回了相关文本，文本内容会作为上下文变量中的值填入提示词，提供LLM回复问题。

### 问题分类

通过定义分类描述，问题分类器能够根据用户输入，使用 LLM 推理与之相匹配的分类并输出分类结果，向下游节点提供更加精确的信息。 
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217174631849_abcd329e.png)

- 分类 1 ：与人工相关

- 分类 2：产品咨询相关


当用户输入不同的问题时，问题分类器会根据已设置的分类标签 / 描述自动完成分类：

“你家有没有鞋子？” —> “产品咨询相关”

“客服服务” —> “与人工相关”

### 条件分支  

作用根据 If/else/elif 条件将 Chatflow / Workflow 流程拆分成多个分支。

条件分支的运行机制包含以下六个路径：  
IF 条件：选择变量，设置条件和满足条件的值；  
IF 条件判断为 True，执行 IF 路径；   
IF 条件判断为 False，执行 ELSE 路径；  
ELIF 条件判断为 True，执行 ELIF 路径；   
ELIF 条件判断为 False，继续判断下一个 ELIF 路径或执行最后的 ELSE 路径；    

判断方式：   

- 包含（Contains）   
- 不包含（Not contains）   
- 开始是（Start with）   
- 结束是（End with）   
- 是（Is）   
- 不是（Is not）   
- 为空（Is empty）   
- 不为空（Is not empty）    

讲解示例  
```python
def 制作咖啡(咖啡类型):
    print(f"正在制作：{咖啡类型}...请稍候！")

def 咖啡推荐系统(甜度, 咖啡浓度):
    if 甜度 == "高" and 咖啡浓度 == "低":
        print("为您推荐：焦糖玛奇朵")
        制作咖啡("焦糖玛奇朵")
    elif 甜度 == "中" and 咖啡浓度 == "中":
        print("为您推荐：拿铁咖啡")
        制作咖啡("拿铁咖啡")
    elif 甜度 == "低" and 咖啡浓度 == "高":
        print("为您推荐：美式咖啡")
        制作咖啡("美式咖啡")
    else:
        print("为您推荐：经典咖啡")
        制作咖啡("经典咖啡")

# 用户输入
甜度 = input("请选择甜度（高/中/低）：")
咖啡浓度 = input("请选择咖啡浓度（高/中/低）：")

# 调用咖啡推荐系统
咖啡推荐系统(甜度, 咖啡浓度)
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217181421375_f6eecfe8.png)

### Http请求

- GET，用于请求服务器发送某个资源。   
- POST，用于向服务器提交数据，通常用于提交表单或上传文件。   
- HEAD，类似于 GET 请求，但服务器不返回请求的资源主体，只返回响应头。   
- PATCH，用于在请求-响应链上的每个节点获取传输路径。   
- PUT，用于向服务器上传资源，通常用于更新已存在的资源或创建新的资源。   
- DELETE，用于请求服务器删除指定的资源。  
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217182407148_53c400e5.png)

### 直接回复节点

对整个流程链路有一个输出，如果是多个链路可以每个链路单独有输出即可。可随时加入节点将内容流式输出至对话回复，支持所见即所得配置模式并支持图文混排
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217182633061_1a21c95e.png)

### 结束节点(工作流)

定义一个工作流程结束的最终输出内容。每一个工作流在完整执行后都需要至少一个结束节点，用于输出完整执行的最终结果。    
结束节点为流程终止节点，后面无法再添加其他节点，工作流应用中只有运行到结束节点才会输出执行结果。若流程中出现条件分叉，则需要定义多个结束节点。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217183220311_9455bf25.png)

## 工具

工具可以扩展 LLM 的能力，比如联网搜索、科学计算或绘制图片，赋予并增强了 LLM 连接外部世界的能力。Dify 提供了两种工具类型：第一方工具和自定义工具。

工具的作用：

工具使用户可以在 Dify 上创建更强大的 AI 应用，如你可以为智能助理型应用（Agent）编排合适的工具，它可以通过任务推理、步骤拆解、调用工具完成复杂任务。

方便将你的应用与其他系统或服务连接，与外部环境交互，如代码执行、对专属信息源的访问等。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217154454329_846f59f6.png)

# 3 Agent构建
prompt：请根据{{type}}和用户问题优先使用知识库中内容进行回答，如果知识库中没有请使用工具搜索到信息后回答。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217221541989_32e0d0f2.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217221802497_acf1b625.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217222132913_0d716ef2.png)
额外的设置：

可能以有用且准确的方式回复人类。

{{instruction}}

您可以访问以下工具：

{{tools}}

使用 json blob 通过提供 {{TOOL_NAME_KEY}} 键（工具名称）和 {{ACTION_INPUT_KEY}} 键（工具输入）来指定工具。
有效的“{{TOOL_NAME_KEY}}”值：“最终答案”或{{tool_names}}

每个$JSON_BLOB仅提供一个操作，如下所示：

```
{
“{{TOOL_NAME_KEY}}”：$TOOL_NAME，
“{{ACTION_INPUT_KEY}}”：$ACTION_INPUT
}
```

遵循以下格式：

问题：输入要回答的问题

想法：考虑之前和后续步骤

操作：
```
$JSON_BLOB
```
观察：操作结果
...（重复想法/操作/观察 N 次）

想法：我知道该如何回应

操作：
```
{
“{{TOOL_NAME_KEY}}”：“最终答案”，
“{{ACTION_INPUT_KEY}}”：“对人类的最终回应”
}
```

开始！提醒您始终使用单个操作的有效 json blob 进行响应。如有必要，请使用工具。如果合适，请直接回复。格式为 Action:```$JSON_BLOB```then Observation:。

![image](/assets/img/posts/low-code-dify-coze-12/image-20250217191321396_7f9cc943.png)
ReAct 模式是一种结合 **推理（Reasoning）和行动（Acting）** 的框架，旨在让 LLM 更像一个“思考者”和“执行者”。它通过交替进行推理和行动来解决复杂问题。

核心特点：   
- 推理（Reasoning）：LLM 通过思考（生成中间推理步骤）来理解问题并规划解决方案。   
- 行动（Acting）：LLM 调用外部工具或执行具体操作来获取信息或完成任务。   
- 循环迭代：ReAct 模式通常是一个循环过程，模型在推理和行动之间不断交替，直到问题解决。   

ReAct 的工作流程：   
- 思考（Think）：模型生成一个推理步骤，明确下一步需要做什么。   
- 行动（Act）：模型调用工具或执行操作（如搜索、计算等）。   
- 观察（Observe）：模型获取行动的结果，并基于结果进行下一步推理。   
- 重复：直到问题解决或达到终止条件。

示例假设：   
用户问：“爱因斯坦获得诺贝尔奖的年份是哪一年？”   

ReAct 的执行过程：   
- 思考：“我需要查找爱因斯坦获得诺贝尔奖的年份。”   
- 行动：调用搜索引擎 API，搜索“爱因斯坦 诺贝尔奖 年份”。   
- 观察：获取搜索结果“爱因斯坦于1921年获得诺贝尔奖。”   
- 思考：“我已经找到了答案，可以返回给用户。”   

返回结果：“爱因斯坦于1921年获得诺贝尔奖。”
# 4. 构建对话流
**“智能客服自动回复系统”**   

**1. 产品概述**   
本产品旨在构建一个智能客服系统，能够自动回复用户多系列产品的咨询。系统优先从运营范围内中查询信息并返回；如果运营范围内中没有相关信息，则自动调用互联网搜索功能，获取最新信息并回复用户。   
**功能拆分**   
- 确定用户运营产品范围
- 将产品范围构建成知识库并录入系统
- 每次用户查询优先查询知识库范围内
- 如果知识库没有或者一开始就知道不在知识库内，直接进行搜索。

构建工作流
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217224838043_35821392.png)
## 前提准备
### 获取API key
当前使用deepseek模型，但是后续涉及会用到其他系列模型，可以选择模型供应商。
建议选择种类丰富的模型供应商
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217225858463_caf99918.png)

点击链接跳转到创建API key界面
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217225924906_ab46a319.png)

创建API key 注意保密
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217230041296_ddf04f6c.png)

点击 **返回控制台** 查看模型列表
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217230146104_de34dd5f.png)

点击模型名称进去后复制模型名称，方便后续注册
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217230213339_8b02425a.png)

回到dify进行模型注册
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217230316351_94040e9e.png)

注册后模型列表
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217230333927_c5378c9e.png)
### 构建知识库
知识库构建方式与课件《【Dify】Ch2 源码部署Dify构建RAG》流程一致。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217225614536_3f198d3c.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217225550718_12e222f8.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217225139347_6cf419f8.png)
## 开始构建对话流
选择创建对话流
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217233821797_0c1e474a.png)

创建开始节点
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217231955439_0aac5c5f.png)

创建问题分类器方便进行意图识别，亦可以拆分成条件分支节点，主要目的是做用户意图识别。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217232043301_d6cd3a6d.png)

创建知识检索节点，增加知识库信息。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217232130082_5168e21e.png)

增加LLM节点，方便引入用户信息来对检索出来的知识进行总结使用。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217232218738_3c9706c9.png)

直接回复节点，可以编辑使用，也可以直接将上游信息进行返回。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217232240292_c58bdf61.png)

以上不同知识库检索链路相似，本次不做额外展示。直接进行第三条链路展示。   
注意(当前搜索引擎不需要APIkey 但是需要科学上网才能使用) 
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217233507412_12f90472.png)

查询后的语句录入到LLM节点中进行总结
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217233533538_80472dc6.png)

直接回复内容可以进行前后编辑然后再输出。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217233432457_b16ae0e1.png)
工作流构建完成点击预览开始测试。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217224838043_35821392.png)
可点击每一步进行过程校验和查看。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217235414748_4cc718c0.png)
发布后测试
![image](/assets/img/posts/low-code-dify-coze-12/image-20250217235614914_dd224f7e.png)
# 5.连接微信
## 软件下载
代码下载路径：https://github.com/hanfangyuan4396/dify-on-wechat?tab=readme-ov-file


![image](/assets/img/posts/low-code-dify-coze-12/image-20250218000323195_adaae338.png)

## 项目部署

部署gewechat服务 docker 安装 （相对直接登录比较稳定不易被封号）

```
# 从阿里云镜像仓库拉取(国内)
docker pull registry.cn-chengdu.aliyuncs.com/tu1h/wechotd:alpine
docker tag registry.cn-chengdu.aliyuncs.com/tu1h/wechotd:alpine gewe

# 创建数据目录并启动服务
mkdir -p gewechat/data  
docker run -itd -v ./gewechat/data:/root/temp -p 2531:2531 -p 2532:2532 --restart=always --name=gewe gewe
```

![image](/assets/img/posts/low-code-dify-coze-12/image-20250218002346919_03645689.png)

下载文件后进行解压或者直接使用，命名为dify-on-wechat   
进入dify-on-wechat路径下创建config.json录入配置信息
![image](/assets/img/posts/low-code-dify-coze-12/image-20250218000921041_f4a2410e.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250218000958454_5d62fd1d.png)

```json
{
​    "channel_type": "gewechat",
​    "dify_api_base": "http://localhost/v1",  #服务启动地址
​    "dify_api_key": "app-",   # 工作流对应的秘钥
​    "dify_app_type": "chatbot",  
​    "gewechat_app_id": "",
​    "gewechat_base_url": "http://当前部署IP地址(ifconfig获取):2531/v2/api",
​    "gewechat_callback_url": "http://当前部署IP地址(ifconfig获取):9919/v2/api/callback/collect",
​    "gewechat_download_url": "http://当前部署IP地址(ifconfig获取):2532/download",
​    "gewechat_token": "",
​    "group_chat_prefix": [
​        "@bot"
​    ],
​    "group_name_white_list": [
​        "ALL_GROUP"
​    ],
​    "model": "dify",
​    "single_chat_prefix": [
​        ""
​    ],
​    "single_chat_reply_prefix": ""
}
```
创建虚拟环境部署dify-on-wechat   
创建conda环境： conda create 环境名称 python=3.11    
conda activate 环境名称    

安装依赖(进入到dify-on-wechat路径下)

```
pip3 install -r requirements.txt  # 国内可以在该命令末尾添加 "-i https://mirrors.aliyun.com/pypi/simple" 参数，使用阿里云镜像源安装依赖

pip install -r requirements-optional.txt # 国内可以在该命令末尾添加 "-i https://mirrors.aliyun.com/pypi/simple" 参数，使用阿里云镜像源安装依赖
```

启动前注意：关闭科学上网    
启动前注意：关闭科学上网    
启动前注意：关闭科学上网    
可能会导致工作流中部分需要科学上网的功能不可用。   

```
cd dify-on-wechat
python3 app.py 
```
![image](/assets/img/posts/low-code-dify-coze-12/image-20250218001746566_46883ad0.png)

直接个人微信扫码登录。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250218001839948_adeae276.png)

个人微信与登录的微信进行对话。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250218002103854_ffe7d7eb.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250218002122169_0ed5f929.png)

后端可以查看
![image](/assets/img/posts/low-code-dify-coze-12/image-20250218001930721_43e305a3.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250218001955806_ed12a3a9.png)
## 项目讲解
### 1. 项目完整结构

```
dify-on-wechat/
├── bridge/          # 桥接层，连接不同的服务
├── channel/         # 通道层，处理不同平台的消息
├── common/          # 公共组件
├── docker/          # Docker 相关配置
├── plugins/         # 插件系统
├── voice/          # 语音处理模块
└── bot/            # 机器人核心实现
```
### 2. 核心启动链路

1. **入口文件 `app.py`**
```python
# 主要职责：
- 加载配置
- 初始化日志
- 启动机器人服务
```

2. **配置加载 `config.json`**
### 3. 核心处理链路


层级有多层嵌入，路径仅供参考！
```mermaid
    A[app.py] --> B[channel/gewechat_channel.py]
    B --> C[bridge/bridge.py]
    C --> D1[bot/dify_bot.py]
    C --> D2[voice/xunfei/xunfei_voice.py]
    D1 --> E[Dify API]
    D2 --> F[讯飞语音API]
```

### 4. Docker 部署

1. **Docker 目录结构**
```
docker/
├── Dockerfile           # 主镜像构建文件
├── docker-compose.yml   # 服务编排配置
└── requirements.txt     # Python 依赖
```

### 6. 详细的组件说明

1. **Bridge 模块**   
层级有多层嵌入，路径仅供参考！   
```python
bridge/
├── bridge.py          # 核心桥接逻辑
├── context.py         # 上下文管理
└── reply.py          # 回复处理
```

主要职责：
- 连接不同的服务组件
- 管理消息上下文
- 处理回复格式化

2. **Bot 模块**
```python
bot/
├── bot.py            # 机器人基类
├── dify_bot.py       # Dify机器人实现
└── openai_bot.py     # OpenAI机器人实现
```

3. **Channel 模块**
```python
channel/
├── channel.py         # 通道基类
├── chat_channel.py    # 聊天通道基类
└── gewechat_channel.py # 个微通道实现
```
### 7. 核心流程示例

1. **文本消息处理流程**
```python
Message --> GewechatChannel.handle_message()
  --> ChatChannel._handle()
    --> Bridge.build_reply_content()
      --> DifyBot.reply()
        --> Dify API
```

2. **语音消息处理流程**
```python
Voice Message --> GewechatChannel.handle_voice()
  --> XunfeiVoice.voice_to_text()
    --> Process Text Message
      --> XunfeiVoice.text_to_voice()
        --> Send Voice Reply
```
### 8. 开发建议

1. **代码阅读顺序**
```
app.py --> config.json --> gewechat_channel.py --> chat_channel.py --> bridge.py --> dify_bot.py
```

2. **关键点关注**
- 配置文件的设置
- 通道的实现
- 消息的处理流程
- 语音服务的集成

3. **扩展开发**
- 新增通道
- 添加新的机器人实现
- 扩展语音服务提供商
# 6. 总结
![image](/assets/img/posts/low-code-dify-coze-12/image-20250219153159453_a13d0112.png)
{% endraw %}