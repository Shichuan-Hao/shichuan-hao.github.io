---
title: Embedding 基础应用案例
description:
author: hsc
date: 2024-09-12 19:27:00 +0800
categories: [AI Agent, RAG]
tags: []
math: true
mermaid: true
---

OpenAI 拥有非常丰富的大模型生态，其 API 是由一系列涵盖对话、图像、审查等具有不同能力和价格选项的多样化模型提供支持，如`gpt-3.5-turbo`、`gpt-4`等，它们都有自己特有的 EndPoint，**每一个 EndPoint 对应着不同的服务模型，这就意味着根据所选的EndPoint，背后为我们服务的模型也会有所不同**。

> 在计算机网络和Web开发中，EndPoint 通常指的是互联网上一个服务的终端或访问点。简单地说，当你希望与一个在线服务进行交互时，你会发送一个请求到这个服务的一个指定的 EndPoint。在OpenAI的上下文中，不同的 EndPoint 代表的是不同的模型或服务，所以你可以根据需求选择合适的EndPoint来访问特定的模型功能。
{: .prompt-info }

> OpenAI Models Overview：[](https://platform.openai.com/docs/models/overview)

总之，**若想使用 OpenAI 的Embedding 模型获取文本的 Embedding向量化表示，只要学会其API调用的方法即可**。也就是说，我们要明确 OpenAI Embedding 模型的 EndPoint 是如何设定的。


## OpenAI Embedding模型：两代模型的迭代升级

OpenAI的大模型一直在快速迭代，每一个新版本都相较于前一代在能力和功能上有显著的增强和完善。

截止目前，GPT模型已经发展到第四代，刚刚发布的 GPT-4 Turbo 相较于早期版本展现出了更为出色的性能，同样地，其**Embedding模型也经历了两代的升级与完善**。如下图所示：

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/image-20231101160420727.png)

**OpenAI 提供了一个第二代 Embedding 模型（在模型 ID 中标记为 -002）和 16 个第一代模型（在模型 ID 中标记为 -001）**。

> OpenAI Embedding Docs：https://developers.openai.com/api/docs/guides/embeddings

### 功能多样：OpenAI 首代 16 个细分的 Embedding 模型

OpenAI 的第一代 Embedding 模型**共发布了16个，均以`-001`标识**。从功能上，由**四种不同的基座模型构成**，如下所示：

| 基座模型类别 |功能| 输出的Embedding长度 |
|:------|:---------|:-------------------|
| Ada  | 能够执行非常简单的任务，通常是GPT-3系列中速度最快且成本最低的模型| 1024              |
| Babbage |能够执行简单的任务，非常快速且成本更低| 2048            |
| Curie | 非常强大，比davinci更快速和成本更低|4096             |
| Davinci |最强大的GPT-3模型。能够执行其他模型能够执行的任何任务，并且通常具有更高的质量| 12288          |

进一步地，**根据不同的搜索任务，可以分为3类**：

| 搜索任务类型 | 描述 |
|:--------------|:------|
| 相似性嵌入 (Similarity embeddings) | 专注于捕获文本片段之间的语义相似性 |
| 文本搜索嵌入 (Text search embeddings) | 有助于衡量哪些长文档与短搜索查询最相关 |
| 代码搜索嵌入 (Code search embeddings) | 擅长自然语言搜索查询和检索的代码片段 |

结合以上基座模型和搜索任务分类，经过**细分后的16个模型都有其独特的应用场景和优势**，同时**模型命名遵循“用途-基座模型-特定功能-版本号”的规范**，如"text-similarity-ada-001"表示用于文本相似性分析的Ada基座模型的第一代模型，具体如下。

#### 相似性模型

**擅长捕捉文本之间的语义相似性**，通过计算文本向量之间的相似度来识别最接近的文本。简单来说，每段文本都被转换成一个 Embedding 向量，然后，模型通过计算这些向量之间的距离或相似度来判断文本之间的相似程度。两个向量距离越近或相似度越高，意味着它们代表的文本在语义上越接近。

<table data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
    <thead data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
        <tr data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
            <th data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                Use cases
                <font class="notranslate immersive-translate-target-wrapper" lang="zh-CN"
                data-immersive-translate-translation-element-mark="1">
                    <font class="notranslate" data-immersive-translate-translation-element-mark="1">
                        &nbsp;
                    </font>
                    <font class="notranslate immersive-translate-target-translation-theme-dashed immersive-translate-target-translation-inline-wrapper-theme-dashed immersive-translate-target-translation-inline-wrapper"
                    data-immersive-translate-translation-element-mark="1">
                        <font class="notranslate immersive-translate-target-inner immersive-translate-target-translation-theme-dashed-inner"
                        data-immersive-translate-translation-element-mark="1">
                            使用案例
                        </font>
                    </font>
                </font>
            </th>
            <th data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                Available models
                <font class="notranslate immersive-translate-target-wrapper" lang="zh-CN"
                data-immersive-translate-translation-element-mark="1">
                    <font class="notranslate" data-immersive-translate-translation-element-mark="1">
                        &nbsp;
                    </font>
                    <font class="notranslate immersive-translate-target-translation-theme-dashed immersive-translate-target-translation-inline-wrapper-theme-dashed immersive-translate-target-translation-inline-wrapper"
                    data-immersive-translate-translation-element-mark="1">
                        <font class="notranslate immersive-translate-target-inner immersive-translate-target-translation-theme-dashed-inner"
                        data-immersive-translate-translation-element-mark="1">
                            可用型号
                        </font>
                    </font>
                </font>
            </th>
        </tr>
        <tr data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
            <td data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                Clustering, regression, anomaly detection, visualization
                <font class="notranslate immersive-translate-target-wrapper" lang="zh-CN"
                data-immersive-translate-translation-element-mark="1">
                    <br>
                    <font class="notranslate immersive-translate-target-translation-theme-dashed immersive-translate-target-translation-block-wrapper-theme-dashed immersive-translate-target-translation-block-wrapper"
                    data-immersive-translate-translation-element-mark="1">
                        <font class="notranslate immersive-translate-target-inner immersive-translate-target-translation-theme-dashed-inner"
                        data-immersive-translate-translation-element-mark="1">
                            聚类分析、回归、异常检测、可视化
                        </font>
                    </font>
                </font>
            </td>
            <td data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                <code data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                    text-similarity-ada-001
                </code>
                <br data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                <code data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                    text-similarity-babbage-001
                </code>
                <br data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                <code data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                    text-similarity-curie-001
                </code>
                <br data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                <code data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                    text-similarity-davinci-001
                </code>
            </td>
        </tr>
</table>

#### 文本搜索模型

文本搜索模型可以衡量长文档与短搜索查询之间的相关性，通过将文本（无论是搜索查询还是文档）转换为向量，然后比较这些向量之间的相似性，来确定哪些文档与特定搜索查询最相关。

<table data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
    <thead data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
        <tr data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
            <th data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                Use cases
                <font class="notranslate immersive-translate-target-wrapper" lang="zh-CN"
                data-immersive-translate-translation-element-mark="1">
                    <font class="notranslate" data-immersive-translate-translation-element-mark="1">
                        &nbsp;
                    </font>
                    <font class="notranslate immersive-translate-target-translation-theme-dashed immersive-translate-target-translation-inline-wrapper-theme-dashed immersive-translate-target-translation-inline-wrapper"
                    data-immersive-translate-translation-element-mark="1">
                        <font class="notranslate immersive-translate-target-inner immersive-translate-target-translation-theme-dashed-inner"
                        data-immersive-translate-translation-element-mark="1">
                            使用场景
                        </font>
                    </font>
                </font>
            </th>
            <th data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                Available models
                <font class="notranslate immersive-translate-target-wrapper" lang="zh-CN"
                data-immersive-translate-translation-element-mark="1">
                    <font class="notranslate" data-immersive-translate-translation-element-mark="1">
                        &nbsp;
                    </font>
                    <font class="notranslate immersive-translate-target-translation-theme-dashed immersive-translate-target-translation-inline-wrapper-theme-dashed immersive-translate-target-translation-inline-wrapper"
                    data-immersive-translate-translation-element-mark="1">
                        <font class="notranslate immersive-translate-target-inner immersive-translate-target-translation-theme-dashed-inner"
                        data-immersive-translate-translation-element-mark="1">
                            可用模型
                        </font>
                    </font>
                </font>
            </th>
        </tr>
        <tr data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
            <td data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                Search, context relevance, information retrieval
                <font class="notranslate immersive-translate-target-wrapper" lang="zh-CN"
                data-immersive-translate-translation-element-mark="1">
                    <br>
                    <font class="notranslate immersive-translate-target-translation-theme-dashed immersive-translate-target-translation-block-wrapper-theme-dashed immersive-translate-target-translation-block-wrapper"
                    data-immersive-translate-translation-element-mark="1">
                        <font class="notranslate immersive-translate-target-inner immersive-translate-target-translation-theme-dashed-inner"
                        data-immersive-translate-translation-element-mark="1">
                            搜索、上下文相关性、信息检索
                        </font>
                    </font>
                </font>
            </td>
            <td data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                <code data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                    text-search-ada-doc-001
                </code>
                <br data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                <code data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                    text-search-ada-query-001
                </code>
                <br data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                <code data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                    text-search-babbage-doc-001
                </code>
                <br data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                <code data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                    text-search-babbage-query-001
                </code>
                <br data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                <code data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                    text-search-curie-doc-001
                </code>
                <br data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                <code data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                    text-search-curie-query-001
                </code>
                <br data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                <code data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                    text-search-davinci-doc-001
                </code>
                <br data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                <code data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                    text-search-davinci-query-001
                </code>
            </td>
        </tr>
</table>

#### 代码搜索模型

与搜索模型一样，**帮助用户在大量的代码库中找到特定的代码片段**。这些模型可以理解自然语言查询（如搜索指令或问题），并将其与存储的代码片段进行比较，从而找到与查询最相关的代码。

<table data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
    <thead data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
        <tr data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
            <th data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                Use cases
                <font class="notranslate immersive-translate-target-wrapper" lang="zh-CN"
                data-immersive-translate-translation-element-mark="1">
                    <font class="notranslate" data-immersive-translate-translation-element-mark="1">
                        &nbsp;
                    </font>
                    <font class="notranslate immersive-translate-target-translation-theme-dashed immersive-translate-target-translation-inline-wrapper-theme-dashed immersive-translate-target-translation-inline-wrapper"
                    data-immersive-translate-translation-element-mark="1">
                        <font class="notranslate immersive-translate-target-inner immersive-translate-target-translation-theme-dashed-inner"
                        data-immersive-translate-translation-element-mark="1">
                            使用场景
                        </font>
                    </font>
                </font>
            </th>
            <th data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                Available models
                <font class="notranslate immersive-translate-target-wrapper" lang="zh-CN"
                data-immersive-translate-translation-element-mark="1">
                    <font class="notranslate" data-immersive-translate-translation-element-mark="1">
                        &nbsp;
                    </font>
                    <font class="notranslate immersive-translate-target-translation-theme-dashed immersive-translate-target-translation-inline-wrapper-theme-dashed immersive-translate-target-translation-inline-wrapper"
                    data-immersive-translate-translation-element-mark="1">
                        <font class="notranslate immersive-translate-target-inner immersive-translate-target-translation-theme-dashed-inner"
                        data-immersive-translate-translation-element-mark="1">
                            可用模型
                        </font>
                    </font>
                </font>
            </th>
        </tr>
        <tr data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
            <td data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                Code search and relevance
                <font class="notranslate immersive-translate-target-wrapper" lang="zh-CN"
                data-immersive-translate-translation-element-mark="1">
                    <br>
                    <font class="notranslate immersive-translate-target-translation-theme-dashed immersive-translate-target-translation-block-wrapper-theme-dashed immersive-translate-target-translation-block-wrapper"
                    data-immersive-translate-translation-element-mark="1">
                        <font class="notranslate immersive-translate-target-inner immersive-translate-target-translation-theme-dashed-inner"
                        data-immersive-translate-translation-element-mark="1">
                            代码搜索和相关性
                        </font>
                    </font>
                </font>
            </td>
            <td data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                <code data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                    code-search-ada-code-001
                </code>
                <br data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                <code data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                    code-search-ada-text-001
                </code>
                <br data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                <code data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                    code-search-babbage-code-001
                </code>
                <br data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                <code data-immersive-translate-effect="1" data-immersive_translate_walked="3911974b-89f1-492c-b246-2cb067ea9caf">
                    code-search-babbage-text-001
                </code>
            </td>
        </tr>
    </tbody>
</table>

**Ada、Babbage、Curie、Davinci这四大基座模型支持的最大输入长度都是2046个token**，在对这16个模型的实际使用效果评估中，在性能方面，Davinci最强，但相应地，其运行速度较慢且成本更高，与此相对，**Ada虽然能力稍逊，但提供了更快的响应速度和更经济的价格**。

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/image-20231101162623480.png)

OpenAI的第一代Embedding模型虽然在发布时展现了强大的能力，但也存在一些明显的局限性。16个模型的多样性可能导致用户在选择上感到困惑，不确定哪个最适合他们的需求。此外，模型按照不同功能进行细分，如文本搜索、文本相似性和代码搜索，也增加了使用的复杂性。

**随着更为强大的第二代Embedding模型的发布，我们不推荐使用这些第一代Embedding模型**。

### 单一高效：OpenAI第二代综合Embedding模型

**OpenAI发布的第二代Embedding仅有一个，即`text-embedding-ada-002`，** 相较于第一代的16个Embedding模型，它进行了如下改进：
- **模型统一**： 取代了文本搜索、文本相似性和代码搜索的三种独立模型；
- **更长的上下文输入**： 上下文长度增加了四倍，从 2048 增加到 8192，可以更方便地处理长文档；
- **更小的输出维度**： 新的Embedding只有 1536 个维度，是 davinci-001 Embedding的八分之一，这使得新的Embedding在使用矢量数据库时更具成本效益；
- **更好的性能**： 在大多数任务上的性能都优于之前功能最强大的模型 Davinci 模型；
- **更低的成本**： 价格降低了99.8%；

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/image-20231101165307324.png)

在不同任务上，第二代新模型 `text-embedding-ada-002` 相较第一代的16个模型，都有比较明显的提升，**在文本搜索、代码搜索和句子相似性任务上优于所有第一代的 Embedding 模型，并在文本分类上获得可比的性能**。其官方评测如下：

#### 文本搜索

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/Snipaste_2023-10-31_15-49-43.jpg)


#### 代码搜索

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/Snipaste_2023-10-31_15-50-05.jpg)

#### 句子相似度

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/Snipaste_2023-10-31_15-50-29.jpg)

#### 文本分类

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/Snipaste_2023-10-31_15-50-40.jpg)

> OpenAI imporved-embedding Blog：https://openai.com/blog/new-and-improved-embedding-model


需要说明的是，**第二代新模型 `text-embedding-ada-002` 是目前应用最广泛的的 Embedding 模型**，


## OpenAI 的 Embedding 第二代模型：`text-embedding-ada-002`的调用方法及参数

OpenAI 的 Embedding 模型的参数配置和使用方法，在OpenAI官方文档中都有详尽的说明和示例。接下来，我们尝试在本地调用`text-embedding-ada-002`模型。


> OpenAI Embeddings：https://platform.openai.com/docs/api-reference/embeddings


### text-embedding-ada-002模型的本地调用测试

在OpenAI的官方文档中，我们可以找到关于 text-embedding-ada-002 模型调用示例，如下图所示： 

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/image-20231101184302178.png)

官方提供了**三种调用`text-embedding-ada-002`模型的方式，分别是curl、python和node.js**，我们这里选择使用Python环境来进行调用测试，代码如下

```python
res = openai.Embedding.create(
  model="text-embedding-ada-002",
  input="The food was delicious and the waiter...",
  encoding_format="float"
)
```

如果能正常接收到输出，说明调用 Embedding 模型成功。通过这样简单的几行代码，就已经完成了`text-embedding-ada-002` 的一次调用流程，还是非常符合OpenAI简单、易用的一贯风格。

### text-embedding-ada-002模型的调用流程和参数介绍

如上一小节中的示例所示，在单次调用中，包括**发送请求与接收请求**两个过程。

text-embedding-ada-002模型需要**通过 `openai.Embedding.create` 方法发起请求**，在这个过程中，涉及三个关键参数： `model`、`input`、`encoding_format` ，具体来说：

|参数|是否必要参数|含义|备注|
|:-------|:-------|:-------|:-------|
|`model`|是|模型名称|Embedding模型的 ID，包含第一代的16个模型和第二代的1个模型|
|`input`|是|输入文本|输入需要进行Embedding的文本|
|`encoding_format`|否|编码格式(float or base64)|`float`用于精确地表示小数和实数<br>`base64`是一种用64个字符来表示任意二进制数据的方法

#### `model`参数决定调用哪个OpenAI Embedding 模型


`model` 参数指定了想调用的模型ID。可以通过更改为相应的模型ID来选择不同的模型，**简而言之，`model` 参数决定了将使用哪个特定的Embedding模型来生成文本Embedding。**

| Embedding模型版本 | 模型ID |
|------|----------------------------------------|
| 第一代 | text-similarity-ada-001<br>text-similarity-babbage-001<br>text-similarity-curie-001<br>text-similarity-davinci-001<br>text-search-ada-query-001<br>text-search-ada-doc-001<br>text-search-babbage-query-001<br>text-search-babbage-doc-001<br>text-search-curie-query-001<br>text-search-curie-doc-001<br>text-search-davinci-query-001<br>text-search-davinci-doc-001<br>code-search-ada-code-001<br>code-search-ada-text-001<br>code-search-babbage-code-001<br>code-search-babbage-text-001 |
| 第二代 | text-embedding-ada-002 |

```python
res = openai.Embedding.create(
  # 调用第二代Embedding
  model="text-embedding-ada-002",
  input="The food was delicious and the waiter...",
  encoding_format="float"
)
res
```

```python
res_1 = openai.Embedding.create(
  # 调用第一代Embedding
  model="text-search-ada-doc-001",
  input="The food was delicious and the waiter...",
  encoding_format="float"
)
res_1
```

如果能正常接收到输出，说明调用的 Embedding 模型成功。

#### `input`参数定义了要处理的文本内容，不同类型的输入将影响返回结果的格式

对于`input`参数来说，**输入的就是需要进行Embedding的文本，但需要注意的是：输入不得超过模型的最大输入限制（ `text-embedding-ada-002`模型为8192 个），并且不能为空字符串**。如果传入的文本为字符串形式：

```python
res = openai.Embedding.create(
  # 调用第二代Embedding
  model="text-embedding-ada-002",
  input="我是字符串格式",
  encoding_format="float"
)
res
```

当发送请求成功后，返回的请求结果 `res` 是一个JSON格式的数据，主要包含四个部分：
- object（数据类型）。
- data（包含Embedding向量的详细信息）。
- model（所用模型的ID）。
- usage（token使用情况）。

格式如下：

```json
{
  "object": "list",             // 请求结果的data类型
  "data": [                     // 结果数据 list[json]
    {
      "object": "embedding",    // 结果种类
      "embedding": [            // `openai.Embedding.create` embedding 结果 长度为1536的列表
        0.0023064255,
        -0.009327292,
        // .... (1536 floats total for ada-002)
        -0.0028842222,
      ],
      "index": 0                // 发送字符串只有一个embedding结果都是0，  发送数组时表示数组对应的index
    }
  ],
  "model": "text-embedding-ada-002",  // embedding 使用的模型
  "usage": {                    // token 使用情况   单向计价
    "prompt_tokens": 8,         // 发送 token数量
    "total_tokens": 8           // 总共 token数量
  }
}
```

**除了传入字符串格式的文本，还可以输入文本数组**，如下：

```python
text_tuples = ("这里是大模型实战课程!", "The food was delicious and the waiter...")
openai.Embedding.create(
  model="text-embedding-ada-002",
  input=text_tuples,
  encoding_format="float"
)
```

可以看到，**不同的输入格式，会导致 Embedding 模型返回的数据结构也发生变化**，对于上述文本数组类型的输入，其返回结果的结构如下：

```java
<OpenAIObject list at 0x15d6930a4f0> JSON: {
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [-0.021023555, ..., -0.027685666]  // 长度为1536的列表
    },
    {
      "object": "embedding",
      "index": 1,
      "embedding": [0.002253932, ..., -0.0027967806]  // 长度为1536的列表
    }
  ],
  "model": "text-embedding-ada-002-v2",
  "usage": {
    "prompt_tokens": 21,
    "total_tokens": 21
  }
}
```

能够发现，当输入为文本数组而非单个字符串时，OpenAI 的Embeddingn模型返回的结果结构会有所不同。我们**输入了一个包含两个文本项的数组（text_tuples）。因此，返回的data部分包含两个独立的Embedding向量对象**。每个对象都有以下信息：
1. object: 类型标记为“embedding”。
2. index: 表示该嵌入向量在输入数组中的位置索引。
3. embedding: 对应文本的嵌入向量，长度为1536

#### `encoding_format`参数用于指定输入数据的编码格式。这是一个非必选参数，其可选值包括 base64 和 float，其中 float 是默认值。

之前的示例我们使用的就是encoding_format="float"参数，现在，我们直接使用 encoding_format="base64" 来进行测试。

```python
res_base64 = openai.Embedding.create(
  model="text-embedding-ada-002",
  input="The food was delicious and the waiter...",
  encoding_format="base64"
)
res_base64
```

> 什么是 `base64`？<br>
base64是一种用64个字符来表示任意**二进制**数据的方法。它常用于在文本中传输二进制数据，例如在邮件中发送附件或在HTML中嵌入图像。<br>
特点: base64编码后的文本会比原始二进制数据稍微长一些（大约增加1/3），但可以确保数据在传输过程中不会受到损坏，因为它只使用ASCII字符。<br>

**float 适用于常规文本输入，而 base64 通常用于处理非文本（如图像）的二进制数据。选择不同的 encoding_format 影响的是数据的编码和传输方式，而非Embedding向量的实际内容**。**建议使用默认的 encoding_format="float"即可**，它简单且高效，适合处理标准文本输入，满足大部分文本Embedding的需求。

总体而言，OpenAI 提供的 Embedding 模型API 对用户是非常友好的，无需繁琐的模型参数配置，且回传结果结构清晰直观。

但需要说明的是，使用OpenAI的Embedding模型同样会产生相应的费用，为了更好地管理成本，我们需要了解如果估算在使用Embedding模型时所需承担的费用。

## text-embedding-ada-002模型的调用费用估算

同 Chat类的 gpt3.5 和 gpt 4 系列模型一样，**OpenAI的Embedding模型API也是按照输入文本的Token数量来计费**。以下是官方对Embedding模型计费方式的说明：

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/Snipaste_2023-10-31_16-43-08.jpg)

> OpenAI Pricing：https://openai.com/pricing


> `ada v2` 和 `text-embedding-ada-002` 实际上指的是同一个模型。在OpenAI的命名规范中，ada系列代表了一种特定的模型架构和训练方式，而v2通常表示这是第二版或者经过改进的版本。在这种情况下，ada v2是模型的简称，而text-embedding-ada-002则是该模型在特定应用场景下的完整名称，这种命名差异主要是为了区分模型的不同版本和应用场景。


从官方信息上可以明确看到**，`text-embedding-ada-002`模型的计价方式是：每1000个Tokens的费用为0.0001美元**。也就是，1美元可以处理 $1000 \times 10000=10,000,000$ 个Tokens。**在 Embedding模型API的调用过程中，费用是基于单向计算的**，这意味着我们仅为发送的字符串所对应的Token数量付费，而接收的返回结果则不收取额外费用。

### 如何计算一个文本有多少Tokens

**Token可以被视为文本的基本单位，它类似于单词或标点符号，如果将一个文本划分为多个子部分，每个子部分即一个Token**。一个最简单的Token切分方式是按空格和标点符号将文本分割成单词和符号，例如：
- 在英文中，句子“Hello, I am learning LLM!”可以被分割成："Hello"，","，"I"，"am"，"learning"，"LLM"，"!"。每个单词和标点符号都被视为独立的Token；
- 在中文中，句子“我正在学习大模型课程”将被分割为"我"，"正"，"在"，"学"，"习"，"大"，"模"，"型"，"课"，"程"。每个汉字单独成为一个Token，因为中文文本通常没有像英文那样的空格分隔符；

这种基于空格和标点符号的简单Token切分方法很直观，但它并未考虑文本的语义和上下文。因此**在实际应用时，通常要依赖更高级的编码器，编码器会遵循一系列复杂的规则将文本地分割成Tokens**。通过高级的文本切分方法，使后续的处理过程能更深入地理解和分析文本的含义和内容。

需要注意的是：不同的编码器会根据它们各自定义的规则来切分文本，这意味着对于相同的文本，当使用不同的编码器时，得到的Tokens可能会有所不同。这是因为每个编码器可能采用不同的方法来理解和解析文本，从而影响最终的Token切分结果。

**当我们利用`text-embedding-ada-002`模型进行文本Embedding时，它所使用的`cl100k_base`编码器将依照其特定的规则来切分文本**。所以当我们向模型输入文本时，编码器会按照这些预设规则先对我们输入的文本进行Token切分。

当我们**每次完成`text-embedding-ada-002` API的一次调用后，返回的数据中就会包含该次调用所消耗的Tokens信息**，我们测试一下：

```python
res = openai.Embedding.create(
  # 调用第二代Embedding
  model="text-embedding-ada-002",
  input="我想测试一下这段文本占用了多少Tokens",
  encoding_format="float"
)
res["usage"]
```

可以看到，输入的文本“我想测试一下这段文本占用了多少Tokens”按照`cl100k_base`编码器的切分规则被分解成了17个Tokens。

> 在使用text-embedding-ada-002模型时，其预设的编码器cl100k_base是不允许我们更改的。

### 如何在调用前计算传入文本的Tokens

虽然成功调用`text-embedding-ada-002` API后，在其返回的数据结果中会指明消耗了多少Tokens，但在处理大量数据时，直接调用可能会导致高额费用。所以很多时候，**我们需要在实际发生调用之前，明确此次将耗费的Tokens**。**OpenAI发布的Python库tiktoken能够在不实际发起API调用的情况下估算字符串的Token数量**。以此帮助我们预先评估使用成本。

```python
# 安装时取消注释并执行
# ! pip install tiktoken
```

安装好tiktoken库后，我们可以使用这个第三方库计算输入文本的Token数量，具体来说：我们可以定义一个工具函数，接收输入文本和编码器的名称，使用该编码器对文本进行切分，最后计算并返回Token的数量和列表。

```python
import tiktoken

def num_tokens_from_string(string: str, encoding_name: str="cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    str_tokens = encoding.encode(string)
    num_tokens = len(str_tokens)
    return num_tokens, str_tokens

print("tiktoken is great!\t编码为 ->", num_tokens_from_string("tiktoken is great!", "cl100k_base"))
print("这里是大模型实战课程!\t编码为 ->", num_tokens_from_string("这里是大模型实战课程!", "cl100k_base"))
```

能够发现，不同的输入的文本经过`cl100k_base`编码器后，返回了其对应的编码结果，其形式为：(Token的数量，[具体的编码])，比如对于英文句子 "tiktoken is great!"来说：
- **Token数量**：6
- **具体编码**：[83, 1609, 5963, 374, 2294, 0]

> 由于中文的特性，每个汉字可能都被视为一个单独的Token，这就是为什么中文句子的Token数量比英文句子多的原因。

### 根据Tokens计算需要支付的费用 

`text-embedding-ada-002`模型的计价方式是：每1000个Tokens的费用为0.0001美元，所以当我们能准确的计算出输入文本的Tokens后，就可以依据这个计费方式来计算出需要支付的费用，我们可以定义如下工具函数，来实现这个计算过程。

```python
def cost_of_Embedding(string:str, encoding_name: str="cl100k_base", max_tokens:int=8191, price_k = 0.0001) -> float:
    """
        Returns the cost of embedding a text string.
    """
    num_tokens = num_tokens_from_string(string, encoding_name, max_tokens)
    if num_tokens:
        return num_tokens / 1000 * price_k

print("这里是大模型实战课程!\t编码价格为 -> $", cost_of_Embedding("这里是大模型实战课程!"))
```

通过上述计算，我们能够计算得到，当Tokens长度分别为11和1100时，对应的费用分别为0.0001美元和0.01美元，**因为每次模型调用都会产生成本，所以了解Tokens的计数方法和OpenAI模型的计价方式对于有效管理费用是至关重要的。**

至此，我们就已经对OpenAI的Embedding API有了一个非常全面的认知。

Embedding技术推动了NLP技术的发展，它在搜索、聚类、推荐等应用领域都扮演着非常关键的作用，但对于之前没了解过Embedding的人来说，学完前面的内容可能只会感觉：Embedding无非就是使用一个所谓的训练过的Embedding模型，将输入的文本转换成我们并不是很理解的浮点数矩阵，它到底为何如此重要，且其到底是如何在不同领域中都能够发挥重要的作用呢，可能并没有一个感性的认知，所以接下来，我们将通过六个典型的案例，涉及推荐、聚类、搜索等多个关键应用场景，来展示Embedding是如何发挥作用的，在学习应用Embedding技术的同时，让大家能够更加深刻地感受到Embedding在现实应用中的真正价值。