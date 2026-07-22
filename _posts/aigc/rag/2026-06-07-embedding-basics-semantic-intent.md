---
title: Embedding 初级应用：语义分类与用户意图挖掘
description:
author: hsc
date: 2026-06-07 19:27:00 +0800
categories: [AI Agent, RAG]
tags: []
math: true
mermaid: true
---

在快速建立了对 Embedding 系列技术的基本认知、以及掌握了 OpenAI Embedding 模型 API 的调用方法之后，接下来就可以尝试将 Embedding 技术应用到一些实际开发场景中，探索 Embedding 在大模型技术开发领域的实际用途，并在这个过程中逐渐深入了解 OpenAI Embedding模型性能。

本文从一个相对简单的场景入手使用 Embedding 模型：先围绕一组带有标签文本数据集尝试进行 Embedding 编码，并围绕此向量化之后的结果进行分析和建模，以此探究 Embedding 在语义分类问题中的表现，以及语义分类在大模型开发技术的实际应用。

<hr/>

## 语义分类与用户意图挖掘

### 语义分类问题

按照大模型领域的专业术语来说，所谓**语义分类问题就是根据用户语义判断用户背后意图**。

本文采用一个 Kaggle 竞赛数据集：<u>亚马逊精选美食评论数据集</u>进行语义分类应用方法的学习。该数据集是一个带标签的语义分类数据集，包含了用户对亚马逊部分商品（美食）的评价，包括文本评价和评分，很明显，评分就是用户意图的量化表示，也就是文本评价的“标签”。

在传统NLP领域，该数据集是情感分析的经典数据集，而在大模型技术领域，我们尝试借助该数据集来介绍用户意图挖掘的一种方法，并将其用于提高 Agent 运行稳定性。

### 用户意图挖掘

用户意图对齐是大模型普适性的最根本保证，在 Agent 开发过程中尤为重要。例如在我开发MateGen 的过程中，能否正确识别用户意图会直接复杂任务拆解的准确性、调用外部函数的准确性等环节。

当然，Agent 开发的各环节中，模型语义分类性能的提升，最直接的效果就是能够大幅提升Function calling 的准确性。

## 语义分类性能提升与 Function calling 稳定性

Function calling的诞生大幅加快了Agent开发效率，使得大模型不再是一个单纯的知识渊博的对话机器人，而是可以调用各类工具帮我们切实完成一些工作的 Agent。然而 Function calling 到底如何实现，OpenAI 从未公开其背后的技术细节。不过经过长期实践，大家发现，Function calling 运行的稳定性和大模型本身的性能直接相关。例如GPT-4的Function calling稳定性就要强于GPT-3.5，GPT-4能够在大量外部函数中精确识别满足当前用户需求所需要的外部函数，并且能够顺利识别外部函数参数并进行参数便携，相比之下GPT-3.5性能要弱一些，面对一些功能相似的外部函数往往无法进行有效分辨，例如对于本地代码解释器Python函数和Python绘图函数。而如果是对于类似谷歌Gemini Pro模型（该模型也提供了Function calling功能），则对于大量复杂外部函数进行有效调用都难以做到，而如果是对于目前国内开源大模型，例如ChatGLM3，则围绕单独一个外部函数都无法做到每次“有求必应”。

当模型本身自带的 Function calling 无法满足使用需求（Function calling 又是构建 Agent 必不可少的功能）时，我们就需要考虑尝试一些其他方法来提高 Fucntion calling 稳定性，其中最核心的思路就是**能否将此前完全在大模型内部自动完成的外部函数选取工作来手动完成**，即能不能通过一些其他方法来先确定当前需求要使用的外部函数，进而手动创建 Function call message 和 Function response message。

很明显，如果这个手动执行的方法得到的 Function calling调用准确性高于模型全自动调用Function calling的准确性，那么我们会更加倾向于手动来完成这个Function calling的外部函数选取+外部函数计算流程。不过很明显的问题是，如果不依靠大模型来判断“哪个问题要调用哪个外部函数”，又有什么方法能够稳定实现这一过程呢？答案就是：**借助Embedding提升手动Function calling稳定性**

在不考虑其他复杂流程和方法的前提下，借助Embedding来完成手动Function calling，是最为高效实用的方法。总的来看，借助Embedding来实现手动Function calling有以下两个核心思路：
1. 借助 Embedding 模型根据词义进行编码的特性，进行零样本分类。即直接根据用户需求和外部函数的函数说明相似度，判断是否需要进行外部函数调用。
2. 进行用户需求的有监督学习和分类


### 思路一：借助 Embedding 模型根据词义进行编码的特性，进行零样本分类

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

能够发现，对于基于词义进行Embedding的模型而言，词向量编码结果本身就能一定程度反应用户问题和外部函数调用之间的关联度。

当然，基于零样本分类来判断到底需要调用哪个外部函数，还需要一些额外的辅助手段，例如需要海量的用户调用某函数需求来判断相似度基准值，或者通过聚类的方法先将用户需求进行分类并将不同大类对应调用不同类型外部函数，然后再根据编码结果判断当前需求应该属于哪类，再据此判断所需调用的外部函数。

### 思路二：用户需求的有监督学习和分类。

流程如下：

```
Step 1: 积累大量用户需求文本（用户问题），人工标注每个问题该调用哪个函数
Step 2: 对所有问题做 Embedding → 得到数值特征
Step 3: 用这些特征训练一个分类模型（如 SVM、随机森林等）
Step 4: 新问题来了 → Embedding → 模型预测 → 决定调用哪个函数
```

这本质上是经典的 **Word2Vec + 机器学习** 文本分类流水线，只是因为现在 Embedding 模型更强了（能理解上下文语义），效果比早年更好。

> **标注小技巧：** 如果人工标注成本太高，可以用 GPT-4 的 Function calling 结果来自动打标签，相当于"强模型为弱模型生产训练数据"。


> 当然，除了 Embedding 方法可以提升模型 Function calling 性能之外，微调也能在这个过程中发挥作用。

具体实现流程为先积累大量用户需求文本（即用户问题），然后手动对其进行标注，需要注明在当前用户问题需要调用哪个外部函数（或者无需调用外部函数）来进行回答。考虑到对于大多数Agent来说外部函数不会轻易发生变化（Agent功能不会轻易变动），因此是有机会能够积累到足够大体量的用户需求数据的。而当我们完成用户需求文本数据标注之后，接下来即可对其进行Embedding编码，并且对于新需求也可以实时进行编码，并将编码结果视作数值型特性并进行机器学习建模预测，预测当前用户需求属于哪一类需求，并由此判断回答当前用户问题需要调用哪个外部函数。先进行Embedding、再进行机器学习建模，这类方法也是Word2Vec这类基于语义的Embedding方法诞生之后被广泛尝试行之有效的文本分类方法。


## 三、借助亚马逊精选美食评论数据集实现上述过程

### 数据集准备
为了证 Embedding 在语义分类上的效果，我使用 **Amazon Fine Food Reviews** 数据集。选择它有三个理由：

1. **带标签**：每条评论有 1-5 星评分，天然就是"意图标签"（好评/差评 = 不同的意图类别）
2. **数据量大**：50 万+ 条评论，覆盖 1999-2012 年
3. **业界认可**：OpenAI 官方 cookbook 推荐使用的教学数据集

在这个数据集上，我们可以依次验证：

- **零样本分类**：将评论 Embedding 后，用聚类观察不同评分是否自然分开
- **有监督分类**：用评分作为标签，训练分类器预测一条评论是好评还是差评
- **迁移到 Agent**：将"好评/差评分类"的方法论，直接搬到"选函数/不选函数"的场景

最终目标是将这套方法迁移到 Agent 开发中——当你对 Embedding 分类的流程足够熟悉，把它套用到 Function calling 场景只需要改变"标签的含义"即可。

#### 数据集简介

Amazon Fine Food Reviews（亚马逊精选美食评论）数据集包含从1999年~2012年10月时间范围内的用户评论，共计568,454条，我们会**从中提取1,000或2000等不同大小的小样本数据集，使用OpenAI 的 Embedding 第二代模型：`text-embedding-ada-002` 模型对抽取出来的小样本数据集中评论文本进行Embedding，将其应用于各个案例中**。

此数据集是来自Kaggle平台的 `Amazon Fine Food Reviews`（亚马逊精选美食评论）数据集，此数据集包含了从1999年~2012年10月时间范围内的用户评论，共计568,454条，可以直接从Kaggle平台将该数据集下载到本地：

> Amazon Fine Food Reviews 数据集下载链接：https://www.kaggle.com/datasets/snap/amazon-fine-food-reviews/

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/image-20231102174129099.png)

亚马逊精选食品评论数据集是一个公开的数据集，其数据量大、时间跨度长，且详细记录了各种产品的用户反馈，因为是真实用户生成的内容，这些评论在自然语言的多样性、情感表达的深度以及日常表述的真实性方面都提供了极为丰富的信息，在自然语言处理研究领域（NLP）是非常有价值的数据资源。

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/image-20231102180405697.png)

如上所示，完整的数据集中共有10个特征字段, 非常细致的记录了用户的评价行为和产品的接受度，除了基本的用户和产品信息，还有用户互动和反馈的相关内容，例如该评价对其他人是否有用、评价者的个人感受等等。具体的特征字段解释如下：

| 字段名               | 中文释义             | 描述                                                  |
|:-----------------------|:--------------------|:-----------------------------------------------------|
| Id                    | 行标识符             |                                                      |
| ProductId             | 产品标识符           | 产品的唯一识别码                                          |
| UserId                | 用户标识符           | 用户的唯一识别码                                          |
| ProfileName           | 用户昵称             | 用户的个人昵称                                            |
| HelpfulnessNumerator  | 有用的正面评价数       | 认为该评论有帮助的用户数量                                      |
| HelpfulnessDenominator| 有用评价的总数        | 表示有多少用户表示该评论有帮助或无帮助                                |
| Score                 | 评分                | 产品的评分，介于1到5之间                                       |
| Time                  | 评论时间             | 评论发表的时间戳                                           |
| Summary               | 评论摘要             | 对评论内容的简短总结                                         |
| Text                  | 评论文本             | 用户对产品的具体评价内容                                       |

正是因为该数据集的多样性和丰富性，使其成为研究各种 NLP 任务的理想选择，利用该数据集的不同信息组合，可以构建多种自然语言处理的应用场景，比如：
- **情感分析**：利用评论文本（Text）对情感进行分类，判断用户的情绪是积极的、消极的还是中性的。通过将评分（Score）作为情感强度的标签，可以训练一个模型来识别评论中的情感色彩；
- **用户行为分析**：分析不同用户（UserId）和用户昵称（ProfileName）的用户行为模式，例如，哪些用户更倾向于给出高评分或低评分，或者哪些用户更活跃在评论区；
- **有用性评价预测**：结合有用性投票（HelpfulnessNumerator和HelpfulnessDenominator）来预测评论的有用性。理解什么样的评论内容更可能被视为有用，指导用户如何撰写更具帮助性的评论；
- **推荐系统**：基于用户给出的评分（Score）以及他们对产品的评价（Text），开发推荐算法，为用户推荐他们可能喜欢的其他产品；
- **文本摘要与关键词提取**：使用评论的摘要（Summary）和评论文本（Text）字段来训练模型进行自动文本摘要和关键词提取，快速把握评论的主要内容；
- **文本相似度和聚类**：利用Embedding来理解文本之间的相似度，并将相似的评论聚类，以发现共同主题或意见；
- **异常检测**：通过不同用户（UserId）、用户昵称（ProfileName）、评论时间（Time）等多个字段识别出异常的评论，比如检测出不真实的（可能是机器生成的）评论或者是操纵评分的行为；


这也是我们选择该数据集作为后续所有案例的基本数据的根本原因，它不仅适合于开展不同的自然语言处理（NLP）任务，也非常适合探索Embedding在不同NLP任务中的应用效果。接下来，就**尝试通过巧妙地将Embedding技术应用于融入到NLP场景中，来了解Embedding的应用技巧和体会其存在的实际价值**。

深入了解亚马逊精选食品评论数据集之后，在实践之前，还有一项重要且关键的步骤需要完成，就是**数据集预处理**。这是出于以下几点考虑：
1. **虽然原始数据集提供了丰富的字段，但并非所有字段都对即将展开的案例分析有实际价值，因此需要筛选出对我们分析有帮助的信息，移除不必要的数据列**。
2. 鉴于整个数据集包含56万+条评论，若**直接使用全量数据，在调用 OpenAI 的 Embedding API 时会产生相对较高的费用，且运行效率较低，出于实际需求，将从原始数据集中提取最新的1,000条评论**，形成一个比较高效的子集供后续使用。
3. 最后，为了确保 Embedding 技术能够发挥最佳效果，我们还会对选定的数据进行适当的预处理，以提升数据质量和分析的准确性。

#### Step 1. 导入三方库

首先，统一导入需要的一些第三方库，以确保代码能够顺利执行

```python
import pandas as pd
import numpy as np
import matplotlib
import tiktoken
import time
from pprint import pprint

from openai.embeddings_utils import get_embedding

from sklearn.manifold import TSNE
from ast import literal_eval
from sklearn.decomposition import PCA

# imports
from ast import literal_eval
from sklearn.metrics import classification_report

from openai.embeddings_utils import cosine_similarity, get_embedding
from sklearn.metrics import PrecisionRecallDisplay

from sklearn.model_selection import train_test_split


from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

from openai.embeddings_utils import plot_multiclass_precision_recall

import matplotlib.pyplot as plt
from openai.embeddings_utils import cosine_similarity  

from sklearn.cluster import KMeans

import matplotlib.pyplot as plt
import seaborn as sns

import os
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")
```

#### Step2. 读取数据集

这里读取的数据集是我们从原数据集中筛选出来的子数据集，即仅包含最新的1,000条评论。

```python
# 使用 1,000 条最新评论的子集
input_datapath = "00_data/01_Base/fine_food_reviews_1k.csv"   # 注意，请将此路径替换为数据集的实际本地存放路径
df = pd.read_csv(input_datapath, index_col=0)
df.head(5)
```

在这个英文数据集，`Text`字段的评论具有明确的情感倾向，比如"Not pleased at all" (一点也不高兴)、"I like the fact"（我喜欢这一点）....，通过如下所示的饼图，可以直观地看到我们抽取的这1000份数据中评分的分布情况。

```python
df['Score'].value_counts().sort_index().plot(kind='pie', title='Score Distribution', figsize=(4, 4), autopct='%1.2f%%')
```

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/image-20231103151609001.png)


能够看出，在筛选得到的1000条样本中，5星级评价的占比最高，为65.10%，而2星级评价的占比最低，仅为4.90%。除此之外，还可以通过其他多种方法来深入分析和探索数据集的更多特性。

#### Step.3 数据预处理

在预处理的过程中，首先我们需要剔除掉一些对我们后续分析没有实际意义的字段，仅保留以下5个字段：
- ProductId：产品的唯一识别码；
- UserId：用户的唯一识别码；
- Score：产品的评分星级，介于1到5之间；
- Summary：对评论内容的简短总结；
- Text：用户对产品的具体评价内容。

```python
df = df[["ProductId", "UserId", "Score", "Summary", "Text"]]             # 使用主要列
df = df.dropna()
df.head(5)
```

将`Summary`字段和`Text`字段合并成一个新的字段`combined`，也就是说我们要将评论的简短总结和评论的具体内容合并为一个组合文本。代码如下：

```python
# '\n' 会影响Embedding结果，直接用空格代替
df["combined"] = (
    "Title: " + df.Summary.str.strip() + "; Content: " + df.Text.str.strip()     # 合并字段
)
df.head(5)
```

> 在实际应用中，我们发现当做文本 Embedding 时，如果将输入文本中的换行符（\n）替换为空格可以得到更好的效果，因为包含换行符时，结果可能会受到负面影响。

<hr/>

#### Step4. 设置 OpenAI Embdding 模型参数

这里我们使用OpenAI的第二代Embedding模型`text-embedding-ada-002`来获取评论文本(组合文本`combined`)的Embedding表示，因为`text-embedding-ada-002`的最大输入长度是8191，为了避免评论文本因超出最大限制而被意外截断，我们设置`max_tokens` 为8000，超过这个数值的文本，将不再使用。参数设置如下：
```python
# embedding model parameters
embedding_model = "text-embedding-ada-002"
embedding_encoding = "cl100k_base"  # this the encoding for text-embedding-ada-002
max_tokens = 8000  # the maximum for text-embedding-ada-002 is 8191
```

#### Step5. 计算数据集中每一行 `combined` 字段所占用的 Tokens

使用 tiktoken.get_encoding 方法，计算出组合文本`combined`列中每项内容占用的Tokens，如果小于我们设置的max_tokens = 8000，则将其作为一个新的列n_tokens记录下来。

```
top_n = 1000

encoding = tiktoken.get_encoding(embedding_encoding)  # embedding token 计数

# 抽取 token_len 小于 max_tokens
df["n_tokens"] = df.combined.apply(lambda x: len(encoding.encode(x)))
df = df[df.n_tokens <= max_tokens].tail(top_n)

df.head(5)
```

```python
len(df)

# 输出：1000
```

能够发现，筛选出来的1000条数据子集中，组合文本`combined`列中文本内容的Tokens全部小于`text-embedding-ada-002`模型的最大输入长度，其中`n_tokens`列中明确计算出了每条评论内容在`cl100k_base`编码后的Token数量。

#### 6. 对组合文本 `combined` 进行 Embedding 编码

可以先按照在`2.3 text-embedding-ada-002模型的调用费用估算`中介绍的 OpenAI的 Embedding API的费用计算方式，在实际调用前进行一个具体的测算。

```python
# 计算花费
print('Total tokens :%d, $ %.6f'%(df['n_tokens'].sum(), df['n_tokens'].sum() * 0.0001/1000))

## 输出：
## Total tokens :95895, $ 0.009590
```

可以看出，该数据集的组合文本`combined`列中一共有95895个Tokens需要进行Embedding，需要花费0.009590美元。

在明确了此次调用的费用后，接下来我们开始对组合文本`combined`进行编码，输出单个向量Embedding，最后将结果存储到本地。

需要说明的是，在`2.2.1 text-embedding-ada-002模型的本地调用测试`中，已经介绍了如何通过OpenAI的Embedding API Python 端点（EndPoint）实现文本的Embedding。除此之外，还可以利用`openai.embeddings_utils`提供的`get_embedding`函数直接获取文本的Embedding结果。这里我们选择直接使用get_embedding函数。

先尝试使用一条数据进行测试，代码如下：

```python
# 取 df 数据集中的第一行数据，作为测试数据
df_embedding_test = df.head(1)

df_embedding_test
```

```python
pprint(df_embedding_test["combined"].to_list())

# ('Title: where does one  start...and stop... with a treat like this; Content: '
#  'Wanted to save some to bring to my Chicago family but my North Carolina '
#  'family ate all 4 boxes before I could pack. These are excellent...could '
#  'serve to anyone')
```

> pprint 是Python的一个模块，它提供了格式化输出的功能，特别是当输出内容较长或者结构较复杂时，pprint能够提供更加阅读友好的格式。

```python
# 使用 get_embedding 函数对 组合文本 combined 进行编码，并将结果存储在df_embedding_test的新列embedding中。
df_embedding_test["embedding"] = df_embedding_test.combined.apply(lambda x: get_embedding(x, engine=embedding_model)) 
```

> 注意：执行此操作前，请确保已经正确加载 openai.api_key

```python
df_embedding_test
```

能够发现，通过 get_embedding，我们已经成功获取到组合文本`combined`对应的Embeding表示。

在测试成功后，我们对全部的1000条数据集中的组合文本`combined`进行Embedding编码，并将最终结果保存为本地的.csv文件。

```python
# get_embedding 获取embedding编码
# 1000 条评论将花费10mins左右
# df["embedding"] = df.combined.apply(lambda x: get_embedding(x, engine=embedding_model))   
# df.to_csv("ttachment/Amazon_Fine_Food_Reviews/fine_food_reviews_with_embeddings_1k.csv")
```

> 编码过程需要大约10分钟的时间

#### Step7. 查看 Embdding 编码数据集

```python
# 注：此处需要将读取文件路径替换为本地实际的文件存储路径
df = pd.read_csv("00_data/01_Base/fine_food_reviews_with_embeddings_1k.csv", index_col="Unnamed: 0")
df.head()
```

至此，我们就完成了Embedding的数据集准备工作，接下来，我们将使用这个数据集来进行后续案例的实践。

### 基于 Embedding 的零样本分类实现流程

**零样本学习 (Zero-Shot Learning, ZSL)** 是一种机器学习范式。在这种范式中，模型被训练来处理它在训练阶段从未见过的类别。

传统的机器学习和深度学习方法通常需要每个类别都有大量的标注数据来学习，但在许多实际应用中，对某些类别的数据进行收集和标注可能是困难的或代价高昂的。

ZSL的目的是利用已有的知识来识别、分类或处理这些没有标注样本的新类别。而**零样本分类**，特指在分类任务中应用**零样本学习**的概念，它希望做到的是：利用已知类别的信息来正确分类未知类别的实例。

在这个任务中，Embedding 也能够发挥出比较关键的作用，因为Embedding本身就具备语义信息，比如像“犬”和“狗”这样语义上相近的词语会被映射到接近的点，如果通过Embedding将与类别相关的辅助信息（例如类别的描述或者属性）转化为一个连续的向量空间，这样，即使模型在训练时没有见过某个类别的样本，它也可以通过这个语义空间中的位置来识别或分类这个类别。

> 对于评论数据，与类别相关的辅助信息可能包括评论的情感、主题或其他与评论相关的描述性信息。例如，对于一个产品的评论，辅助信息可能是产品的类别、功能或其他属性。

为实现这一点，我们可以首先对每个标签的描述（如“正面”和“负面”）进行 Embedding 转换，然后我们计算每个评论与这些分类描述之间的余弦相似度，评论与哪个分类标签的描述更接近，那么该评论就更可能属于该分类。同时为了使结果更具解释性，我们还可以设计一个预测分数，该分数是评论与“正面”标签的余弦相似度与其与“负面”标签的余弦相似度之差，如果这个差值大于0，标识为"积极"，如果小于0，标识为"消极"。

例如各个评论与标签的余弦值结果如下：

|评论|星级（$y$）|积极|消极|余弦分类（$\hat y$ ）|
|:----:|:----:|:----:|:----:|:----:|
|A|5|0.36|0.75|消极|
|B|2|0.85|0.15|积极|
|C|4|0.62|0.38|积极|
|D|1|0.29|0.71|消极|

> 需要说明的是，我们将4星和5星的评价定义为正面情绪，把1星和2星的评价定义为负面情绪，3星的评价被视为中立，在这个例子中不会使用它们。

#### Step 1. 标记情感标签

按照前面提到的思路，我们先过滤掉评分为3的评论，1星和2星的评价标记为“negative”，而4星和5星的评价标记为“positive”。

```python
# 注：此处需要将读取文件路径替换为您本地实际的文件存储路径
datafile_path = "00_data/01_Base/fine_food_reviews_with_embeddings_1k.csv"

df = pd.read_csv(datafile_path)
df["embedding"] = df.embedding.apply(literal_eval).apply(np.array)

# 选取1245评分并归为积极、消极评分
df = df[df.Score != 3]
df["sentiment"] = df.Score.replace({1: "negative", 2: "negative", 4: "positive", 5: "positive"})
```

```python
df.head(5)
```

#### Step 2. 样本分类预测及其可视化

在这个过程中，首先需要再次调用`get_embedding`函数，先获取到标签（negative和positive）的Embedding，然后计算给定评论 Embedding 与正面标签 Embedding 的余弦相似度与其与负面标签Embedding 的余弦相似度之差，这个差值如果大于0，就归为 positive 类，如果小于0，就归为negative类，并绘制精确度-召回率曲线。具体代码如下：

```python
# 设置Embedding模型名称
EMBEDDING_MODEL = "text-embedding-ada-002"

# 定义零样本分类的评估函数
def evaluate_embeddings_approach(
    labels = ['negative', 'positive'], 
    model = EMBEDDING_MODEL,
):
    # 获取标签的Embedding
    label_embeddings = [get_embedding(label, engine=model) for label in labels]

    # 定义标签评分函数
    def label_score(review_embedding, label_embeddings):
        # 计算给定评论Embedding与正面标签Embedding的余弦相似度与其与负面标签Embedding的余弦相似度之差
        return cosine_similarity(review_embedding, label_embeddings[1]) - cosine_similarity(review_embedding, label_embeddings[0])
        
    # 计算每个评论的评分
    probas = df["embedding"].apply(lambda x: label_score(x, label_embeddings))
    # 基于评分做出最终的预测情感
    preds = probas.apply(lambda x: 'positive' if x>0 else 'negative')

    # 打印分类报告
    report = classification_report(df.sentiment, preds)
    print(report)

    # 绘制精确度-召回率曲线
    display = PrecisionRecallDisplay.from_predictions(df.sentiment, probas, pos_label='positive')
    _ = display.ax_.set_title("2-class Precision-Recall curve")

evaluate_embeddings_approach(labels=['negative', 'positive'], model=EMBEDDING_MODEL)
```

首先来看下分类报告：

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/image-20231103172908846.png)

- 对于**负面**评论：
    - **精确度(Precision)**: 0.61，意味着模型预测为负面的评论中，有61%确实是负面评论;
    - **召回率(Recall)**: 0.88，说明能够检测到88%的实际负面评论;
    - **F1得分**: 0.72，是精确度和召回率的调和平均值，为模型性能提供了一个整体评价;
    - **样本(Support)**: 136，意味着测试数据中一共有136条负面评论;
- 对于**正面**评论：
    - **精确度**: 0.98，意味着模型预测为正面的评论中，有98%确实是正面评论;
    - **召回率**: 0.90，说明能够检测到90%的实际正面评论;
    - **F1得分**: 0.94;
    - **样本**: 789，意味着测试数据中有789条正面评论;
- **总体评价**：
    - **准确率(Accuracy)**: 0.90，意味着模型对90%的评论做出了正确的预测;
    - **宏平均(Macro avg)** 和 **加权平均(Weighted avg)** 分别对各个标签的评价指标进行了平均，用于评估模型在整体上的性能;

再看下精确度-召回率曲线：

从图中可以看到，随着召回率的提高，精确度在某些点上有所下降。这是因为为了捕获更多的正样本，可能会误判一些负样本。理想的曲线应该尽可能地靠近图的右上角，意味即使召回率很高，精确度也保持在高水平，在本图中，大部分时间的精确度都保持在较高的水平，尤其是在召回率较高时，这说明模型的性能相当不错。

总体而言，当前的分类器性能已经相当出色，特别是考虑到我们只利用了简单的相似性嵌入，并用最基本的标签名称进行分类。当然，我们还可以进一步提高分类器的准确性，因为“积极”和“消极”描述过于简洁，我们可以尝试优化为更丰富的：
- negative（消极） --> 'An Amazon review with a negative sentiment.'（带有消极情绪的亚马逊评论）
- positive（积极） --> 'An Amazon review with a positive sentiment.'（带有积极情绪的亚马逊评论）

```python
evaluate_embeddings_approach(labels=['An Amazon review with a negative sentiment.', 'An Amazon review with a positive sentiment.'])
```

其对应的分类结果如下所示：

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/image-20231103174740807.png)

![](https://snowball101.oss-cn-beijing.aliyuncs.com/img/image-20231103174749012.png)

从结果上看，经过简单优化后的分类器在多个指标上都有所提升，尤其是负面评论的精确度和整体的F1-得分。虽然负面评论的召回率有所下降，但考虑到精确度的显著提高，整体性能仍然更为出色。所以**Embedding在进行零样本分类任务时，对模型效果的提示是非常显著的，尤其是在分类标签更丰富、更具描述性的情况下。**

### 将 Embedding 作为文本特征编码器进行有监督学习

在机器学习的算法建模中，通常会经历三个关键阶段：
- Stage 1.业务背景解读与数据探索
- Stage 2.数据预处理与特征工程
- Stage 3.算法建模与模型调优<

特别是在特征工程阶段，我们专注于优化和转换数据特征，使得数据的内在规律更易于被模型捕捉和学习，这一步骤对于提升模型的训练效果至关重要。在处理特征时，除了必须对离散变量和连续变量进行区分和处理外，另一个重要的任务是有效地处理文本型变量。

> 需要说明的是，为确保模型能在一组独立数据上进行公平的评估，我们会将数据集分为训练集和测试集。

#### 回归任务建模流程

回归意味着预测一个数字，而不是其中一个类别，我们的目标是预测产品评论的评分星级，这个评分星级是一个介于1到5的连续数字，它表征了用户对产品的满意程度。其中，1分代表用户的强烈不满（负面评价），而5分则表示用户的高度认可（正面评价）。

我们使用在`预处理统一的数据集并获取评论文本的 Embedding表示`中生成的文本Embedding向量，作为特征输入到一个随机森林回归器中，以预测评论的评分星级。具体步骤如下：

##### Step 1. 划分训练集和测试集

为确保模型评估的客观性和有效性

#### 分类任务建模流程


### 借助 Embedding 进行聚类分析

### 借助 Embedding 实现文本搜索


## 四、总结与延伸

**一句话回顾：** 当模型自带的 Function calling 不够稳，用 Embedding + 相似度（或分类模型）手动判断该调用哪个函数，是成本最低、效果可观的替代方案。

**补充两点背景知识：**

1. OpenAI 从未公开 Function calling 的技术细节，但业界普遍猜测其内部就是"意图识别模型 + Embedding 辅助判断"的组合。换句话说，我们这节讲的思路，很可能就是 Function calling 的底层实现原理。

2. 除了 Embedding，**微调（Fine-tuning）** 也是提升 Function calling 稳定性的手段。两者可以互补——Embedding 做粗筛，微调做精判。


