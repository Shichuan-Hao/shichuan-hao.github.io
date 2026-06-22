---
title: LoRA 微调原理详解
description: 深入浅出讲解 LoRA（低秩适应）的核心原理、本征维度概念、矩阵秩的通俗理解、资源对比及 PyTorch 代码实现。
author: hsc
date: 2024-11-01 23:27:00 +0800
categories: [AI, Fine-tuning]
tags: [LoRA, Fine-tuning, LLM]
math: true
mermaid: true
---

## 为什么需要 LoRA


全参数微调的难点：
- 大型语言模型的微调成本高昂：完整微调需要存储和更新所有模型参数的副本
- 部署困难：每个任务都需要存储完整的模型副本，占用大量存储空间
- 计算资源要求高：完整微调需要大量计算资源与 GPU 内存

LoRA 的核心思想：
1. 假设模型权重的更新可以通过低秩分解来近似
2. 不直接更新原始权重矩阵，而是训练两个更小的矩阵（低秩分解）
3. 通过这种方式大大减少了需要训练和存储的参数数量


LoRA 的优势：
1. 显著减少可训练参数数量
2. 降低 GPU 内存需求
3. 加快训练速度
4. 多个任务可以共享基础模型，只需存储小型任务特定适配器
5. 训练稳定性好，性能接近完整微调


以在线客服场景为例：
- 公司有一个基础的大语言模型用于客服对话，需要为不同产品线（如手机、电脑、家电等）定制专门的客服机器人。传统方法需要为每个产品线存储一个完整模型副本
- 使用 LoRA 后：
  - 只需维护一个基础模型
  - 为每个产品线训练小型 LoRA 适配器
  - 运行时动态加载对应产品线的适配器
  - 大大节省存储空间和训练成本
  - 方便快速增加新产品线的支持

这样不仅降低了部署和维护成本，还提高了模型更新和扩展的灵活性。


## LoRA 微调方法讲解

### LoRA 原理介绍


LoRA 来源于微软在 2021 年发布的论文：《LORA: LOW-RANK ADAPTATION OF LARGE LANGUAGE MODELS》（低秩矩阵微调）。

论文地址：<https://arxiv.org/pdf/2106.09685.pdf>，GitHub 开源地址：<https://github.com/microsoft/LoRA>。

> 适配器微调（Adapter Tuning）是在模型中引入了额外计算模块，本质还是在模型本身增加层次，会让模型推理走更长的路径。<br/>LoRA 的核心思想是：**基准模型保持不变**，额外引入一部分参数来做专属内容处理，同时保留原有模型的推理能力，这部分新增的内容就是要训练的参数矩阵。


新的矩阵 $h$ 可以表示为：

$$ 
    h = W_0 x + \Delta W x 
$$

其中：
- $W_0$ 是原始的权重矩阵
- $x$ 是输入向量
- $\Delta W$ 是新增的权重矩阵，用于学习任务特定的知识

输入 $x$ 经过原有矩阵 $W_0$ 和新增矩阵 $\Delta W$ 的联合计算后，输出带有任务适配能力的结果。

![](https://typora-photo1220.oss-cn-beijing.aliyuncs.com/DataAnalysis/muyan/image-20241110165413671.png)


LoRA 的关键在于：$\Delta W$ 如果直接作为全量参数矩阵来训练，就和全参数微调没有区别了，无法节省资源。因此需要引入**低秩分解**。

从线性代数角度看，一个矩阵可以由两个更小的矩阵相乘得到。同理，$\Delta W$ 可以分解为矩阵 $A$ 和矩阵 $B$ 的乘积：

$$\Delta W = BA$$

原式 $h = W_0 x + \Delta W x$ 变为：

$$h = W_0x + \Delta Wx = W_0x + BAx$$

（$x$ 作为输入向量保持不变）

这里引入一个关键概念：
> **本征维度（Intrinsic Dimension）**：是指数据或空间中所需的最小维度，以便充分描述其中的结构或特征。尽管数据可能存在于高维空间中，但其实际包含的信息可能集中在一个更低维度的子空间内。本征维度就是描述这个低维子空间的维度。


LoRA 与本征维度的关系：
- LoRA 的核心假设是神经网络的权重更新矩阵通常具有较低的"本征秩"
- 虽然模型权重是高维的，但实际的任务相关更新可能位于一个低维子空间中
- LoRA 正是利用了这一特性，使用低秩分解来捕获权重更新


![](https://typora-photo1220.oss-cn-beijing.aliyuncs.com/DataAnalysis/muyan/image-20241117150602234.png){: width="20%"} ![](https://typora-photo1220.oss-cn-beijing.aliyuncs.com/DataAnalysis/muyan/image-20241117150516158.png){: width="20%"}
{: .img-row}

> 一张苹果图片，展示很精细，有光线、斑点、叶子脉络、细微的色差等。<br/>但如果目标仅仅是"让人认出这是苹果"，那么只需要几个像素级别极低的色块就足够了。这几个核心特征就是最关键的信息。
{: .prompt-info }


同理，如果将 $\Delta W$ 拆成矩阵 $A$ 和矩阵 $B$，而这两个矩阵的秩与原矩阵相同，那分解就失去了意义。因为训练某个方向的专属技能时，其他方向的参数在目标输出上没那么重要，提炼最相关的特征才是关键。这就引出了**低秩矩阵**的概念。

### 通俗理解矩阵的秩

![](https://typora-photo1220.oss-cn-beijing.aliyuncs.com/DataAnalysis/muyan/image-20241117154303169.png)

$$
\begin{bmatrix}
2 \times 3 & 2 \times 2 & 10 \\
1 \times 3 & 3 \times 2 & 9 \\
3 \times 3 & 1 \times 2 & 11
\end{bmatrix}
\quad
\begin{bmatrix}
2 \times 3 & 1 \times 2 & 8 \\
1 \times 3 & 1 \times 2 & 5
\end{bmatrix}
\quad
\begin{bmatrix}
1 \times 3 & 1 \times 2 & 5
\end{bmatrix}
$$


一个矩阵的**秩**是指矩阵中线性独立行或列的最大数目。用购物场景理解：
- **第一个矩阵（秩=3）**：A、B、C 各自买了不同的东西，谁也不能被替代
- **第二个矩阵（秩=2）**：C 花的钱恰好是 A 和 B 的和，C 可被替代
- **第三个矩阵（秩=1）**：C 是 A 的 3 倍，B 是 A 的 2 倍，三者线性相关，只剩一个独立维度

秩越低，矩阵信息含量越少，占用空间也越小。**这就是 LoRA 使用低秩的核心原因。**

具体体现：

```python
# 假设原始权重矩阵 W ∈ R^{d×k}
# LoRA 将权重更新分解为:
ΔW = BA   # 其中 B ∈ R^{d×r}, A ∈ R^{r×k}, r << min(d,k)
```

- $r$ 是 LoRA 的秩（rank），通常远小于原始维度
- $r$ 实际上反映了任务适配所需的本征维度
- 较小的 $r$ 就足够表达任务所需的权重更新，说明更新确实存在于低维子空间


### 矩阵分解的直观理解

小明想去三个地方，距离分别是 10、20、30km，他可以选择步行、自行车、骑摩托三种方式，每种方式花费的时间不同——这些数据构成一个 $3 \times 3$ 的矩阵。

![](https://typora-photo1220.oss-cn-beijing.aliyuncs.com/DataAnalysis/muyan/image-20241117161939882.png)

$$
\begin{bmatrix}
@ \\
@ \\
@ \\
\end{bmatrix}
\times
\begin{bmatrix}
@ & @ & @ \\
\end{bmatrix}
\;=\;
\begin{bmatrix}
@ & @ & @ \\
@ & @ & @ \\
@ & @ & @
\end{bmatrix}
$$

> @ 符号仅作为数字占位符，用来表达：一个列向量和一个行向量相乘，就能得到一个完整的矩阵。
{: .prompt-tip }


原矩阵需要 $3 \times 3 = 9$ 个参数，而分解后的两个小矩阵仅需 $3 + 3 = 6$ 个参数，**减少了 3 个参数**。

推广到大规模场景：假设原始权重矩阵为 $1000 \times 1000$，共 100 万个参数。取秩 $r = 8$，分解后参数量仅为：

$$1000 \times 8 + 8 \times 1000 = 16000$$

占原有参数量的 $16000 / 1000000 = 1.6\%$。对于动辄数十亿参数的大模型，节约的空间非常可观。

> **过参数化模型（Over-parametrized models）**：指参数数量远超训练数据样本数量的模型。GPT 系列和 Transformer 均属此类。大量参数带来的冗余意味着，对于某个垂直任务，只需一小部分关键参数就能做得足够好——模型适应所需的"内在秩"较低。这正是 LoRA 的灵感来源。
{: .prompt-tip }

以客服机器人场景为例：
- **原始模型（过参数化）**：通用语言理解、基础对话能力、大量冗余参数
- **特定任务适配（如手机客服）**：只需学习手机专业词汇、特定问答模式、服务流程

通俗来讲，LoRA 的策略是：用较小规模的矩阵来近似大模型的权重更新。基于低秩分解的数学原理，通过较少的参数实现对大模型复杂功能的有效捕捉和适配，在减少计算资源的同时保持甚至提升模型在特定任务上的性能。

**参数量对比（以 $d \times d$ 矩阵为例）**：

$$
h = W_0x + \Delta Wx = W_0x + ABx
$$

- $W_0$：$d \times d$ 矩阵
- $A$：$d \times r$ 矩阵，$B$：$r \times d$ 矩阵
- 全参数量：$d \times d$，LoRA 参数量：$d \times r + r \times d = 2dr$

举个例子：设 $\Delta W$ 有 20,000 行、30,000 列，共 **6 亿个参数**。取 $r = 8$，实际所需参数量为：

$$20000 \times 8 + 8 \times 30000 = 400000$$

仅为全参数量的 **1/1500**，可见优化效果非常可观，这也让单卡微调训练成为可能。


### LoRA 的初始化与训练

![](https://typora-photo1220.oss-cn-beijing.aliyuncs.com/DataAnalysis/muyan/image-20241117171209788.png)

**A 矩阵的初始化**：元素服从正态分布 $N(0, 1)$，例如：

$$
A=
\begin{pmatrix}
0.5 & -0.2 & 0.1 & 0.3 & \cdots & 0.7 \\
-0.4 & 0.3 & -0.2 & 0.5 & \cdots & -0.6 \\
0.6 & 0.4 & -0.3 & -0.1 & \cdots & 0.2 \\
-0.5 & 0.4 & -0.3 & -0.1 & \cdots & 0.5
\end{pmatrix}
$$

**B 矩阵的初始化**：全零矩阵，确保训练初期 $\Delta W = BA = 0$，不破坏预训练模型的初始性能。

$$
B =
\begin{pmatrix}
0 & 0 & 0 & 0 \\
0 & 0 & 0 & 0 \\
0 & 0 & 0 & 0 \\
\vdots & \vdots & \vdots & \vdots \\
0 & 0 & 0 & 0
\end{pmatrix}
$$

**训练过程**：仅更新 $A$ 和 $B$ 的值。随着训练的进行，$B$ 的值逐渐变得非零。

1. **B 的变化原理**：
   - 初始 B = 0，最初的权重更新没有效果
   - 通过反向传播计算损失对 B 的梯度
   - 梯度下降逐步更新 B，使其偏离 0
   - 随着训练进行，B 逐渐收敛到有助于完成任务的值

2. **B 为什么必须变得非零**：如果 B 保持为 0，模型就无法学习任何任务特定的适配，损失函数会推动 B 向着减小任务损失的方向变化。

3. **影响 B 变化的因素**：
   - 学习率：决定每次更新的步长
   - 任务性质：不同任务需要不同程度的适配
   - 优化器选择：影响 B 的收敛路径
   - 初始化方式：A 的初始值会影响 B 的学习

4. **B 的收敛过程**：
   - 训练初期：B 快速从 0 变化
   - 训练中期：变化速度放缓，开始形成有意义的特征
   - 训练后期：B 的值趋于稳定


> **问：为什么 A 使用正态分布初始化？**
> **答：** ① 确保初始梯度有效传播，避免梯度消失或爆炸；② 提供足够的随机性，探索更广泛的参数空间；③ 正态初始化的值较小，结合 B 初始化为零，确保训练初期不影响预训练模型的初始性能。
{: .prompt-info }


### LoRA 在 Transformer 中的作用位置

1. 基本概念：
- Q (Query): 查询向量，表示"我想要查什么"
- K (Key): 键向量，表示"我有什么信息"
- V (Value): 值向量，表示"实际的信息内容"
- O (Output): 输出投影，将注意力的输出映射到所需的维度

2. 在 Transformer 中的位置：
```mermaid
graph LR
    A[输入序列] --> B[Linear 投影层]
    B --> C[Q、K、V 矩阵变换]
    C --> D[注意力计算]
    D --> E[O 矩阵变换<br/>输出投影]
    E --> F[输出结果]
```

3. 具体作用：
- Q 矩阵：将输入转换为查询形式
- K 矩阵：将输入转换为可被查询的键
- V 矩阵：存储实际的信息内容
- O 矩阵：将注意力机制的输出转换为所需的表示


4. 在 LoRA 中的应用：
- LoRA 主要应用在这些权重矩阵的更新上
- 对每个权重矩阵 ($W_Q$, $W_K$, $W_V$, $W_O$) 都可以应用 LoRA
```python
# 以 Q 为例
原始: Q = input x Wq
LoRA: Q = input x (Wq + BA)  # B 和 A 是低秩矩阵
```


5. LoRA 的选择性应用：
- 可以只对部分矩阵应用 LoRA
- 常见组合：
  - 仅 Q 和 V
  - Q、K、V 全部
  - Q、K、V、O 全部

LoRA 对 Q/K/V/O 的更新方式：

$$\begin{aligned}
Q &= W_0^{Q} + \Delta W^{Q} \\
K &= W_0^{K} + \Delta W^{K} \\
V &= W_0^{V} + \Delta W^{V} \\
O &= W_0^{O} + \Delta W^{O}
\end{aligned}$$

6. 实际影响：
- Q 的更新影响查询方式
- K 的更新影响键的表示
- V 的更新影响值的内容
- O 的更新影响最终输出

![](https://typora-photo1220.oss-cn-beijing.aliyuncs.com/DataAnalysis/muyan/image-20241117181759857.png)


GPT-3 使用 LoRA 在不同注意力矩阵组合上的实验效果如上图所示。可以看到：不限制参数预算时，同时对 $W_Q$、$W_K$、$W_V$、$W_O$ 应用 LoRA 效果最好；有限预算下，仅对 $W_Q$、$W_K$ 应用的性价比最高。

![](https://typora-photo1220.oss-cn-beijing.aliyuncs.com/DataAnalysis/muyan/image-20241117183212261.png)

相同参数预算下训练 $W_Q + W_K$ 比单独训练 $W_Q$ 效果更好。同时可以看到 $r$（Rank）并非越大越好，建议值 8-64，通常默认为 8。


### 资源对比：全参数微调 vs LoRA

以 **1B（10 亿）参数模型**、AdamW 优化器为例：

| 项目 | 全参数微调 | LoRA（r=8） |
|------|-----------|-------------|
| 模型权重 | 4 GB | 4 GB |
| 优化器状态 | 8 GB | ≈ 128 MB |
| 梯度 | 4 GB | ≈ 64 MB |
| **总占用** | **≈ 16 GB** | **≈ 4.2 GB** |

> 全参微调可粗略估算为 **$4 \times N$ GB**（$N$ 为模型参数量的 GB 数）。以上仅作估量参考，实际生产环境还受批处理大小、序列长度等因素影响。
{: .prompt-tip }


## 总结

LoRA 的核心思想可以概括为以下几点：

1. **低秩假设**：大模型在下游任务上的权重更新存在于低维子空间中，用较小的秩 $r$ 即可捕获
2. **参数效率**：将 $\Delta W$ 分解为 $BA$，训练参数量从 $d \times k$ 降至 $2dr$，通常减少 99% 以上
3. **冻结基座**：原始权重 $W_0$ 始终不变，仅训练低秩矩阵 $A$ 和 $B$，不破坏预训练能力
4. **即插即用**：多个 LoRA 适配器可共享同一基础模型，动态切换，极大降低部署成本
5. **实践建议**：秩 $r$ 建议 8-64，通常默认 8；优先对 $W_Q$ 和 $W_V$ 应用 LoRA 性价比最高

LoRA 并不是微调技术的终点，但其简洁、高效的特性使其成为当前最主流的大模型微调方法之一。配合 QLoRA、AdaLoRA 等改进方案，可以进一步降低门槛，让单卡微调千亿参数模型成为现实。

### LoRA 代码实现

```python
import numpy as np
import torch
import matplotlib.pyplot as plt

# 1. 创建一个模拟的原始权重矩阵
def create_original_matrix(d=512, k=512):
    """
    创建一个模拟的原始权重矩阵
    d: 输入维度
    k: 输出维度
    """
    original_weight = torch.randn(d, k)  # 随机初始化一个权重矩阵
    return original_weight

# 2. 实现LoRA分解
class LoRALayer:
    def __init__(self, d, k, r):
        """
        d: 输入维度
        k: 输出维度
        r: LoRA秩 (rank)
        """
        self.d = d
        self.k = k
        self.r = r
        
        # 初始化A和B矩阵
        self.lora_A = torch.randn(d, r) / np.sqrt(r)  # 缩放初始化
        self.lora_B = torch.zeros(r, k)  # B初始化为0
        
        # 使其需要梯度
        self.lora_A.requires_grad_(True)
        self.lora_B.requires_grad_(True)

    def forward(self, x):
        """前向传播"""
        return (self.lora_A @ self.lora_B) @ x

    def get_weight_update(self):
        """获取权重更新矩阵"""
        return self.lora_A @ self.lora_B
    
# 3. 演示训练过程
def train_lora(original_weight, lora_layer, num_iterations=1000):
    """
    训练LoRA来近似原始权重矩阵
    Adam是一种优化器，用于更新模型参数
    [lora_layer.lora_A, lora_layer.lora_B]指定需要优化的参数
    lr=0.01是学习率，控制每次更新的步长
    优化器的作用是根据梯度更新A和B矩阵，使得BA的乘积逐渐接近原始权重矩阵
    """
    optimizer = torch.optim.Adam([lora_layer.lora_A, lora_layer.lora_B], lr=0.01)
    losses = []

    for i in range(num_iterations):
        # 计算当前LoRA权重
        current_weight = lora_layer.get_weight_update()
        
        # 计算与原始权重的差异
        # 计算当前LoRA权重与原始权重的差异
        # 使用均方误差损失函数（MSE）来衡量差异
        # 损失函数越小，表示当前LoRA权重越接近原始权重
        loss = torch.nn.functional.mse_loss(current_weight, original_weight)
        
        # 反向传播
        optimizer.zero_grad()  # 清除之前的梯度
        loss.backward()       # 计算梯度
        optimizer.step()      # 根据梯度更新参数
        
        if i % 100 == 0:
            losses.append(loss.item())
            print(f"Iteration {i}, Loss: {loss.item():.6f}")
    
    return losses


# 4. 可视化结果
# 修改可视化函数
def visualize_results(original_weight, lora_approximation, losses):
    plt.figure(figsize=(15, 5))
    
    # 绘制损失曲线
    plt.subplot(131)
    plt.plot(losses)
    plt.title('Training Loss')
    plt.xlabel('Iterations (x100)')
    plt.ylabel('MSE Loss')
    
    # 绘制原始权重矩阵
    plt.subplot(132)
    plt.imshow(original_weight.detach().numpy(), cmap='viridis')
    plt.title('Original Weight Matrix')
    plt.colorbar()
    
    # 绘制LoRA近似后的矩阵
    plt.subplot(133)
    plt.imshow(lora_approximation.detach().numpy(), cmap='viridis')
    plt.title('LoRA Approximation')
    plt.colorbar()
    
    plt.tight_layout()
    plt.show()
    
    # 打印矩阵数值
    print("\n原始权重矩阵的一部分(5x5):")
    print(original_weight.detach().numpy()[:5, :5])
    
    print("\nLoRA近似后的矩阵的一部分(5x5):")
    print(lora_approximation.detach().numpy()[:5, :5])
    
    # 计算误差矩阵
    error_matrix = original_weight.detach().numpy() - lora_approximation.detach().numpy()
    print("\n误差矩阵的一部分(5x5):")
    print(error_matrix[:5, :5])
    
    # 计算一些统计指标
    print("\n统计指标:")
    print(f"最大误差: {np.abs(error_matrix).max():.6f}")
    print(f"平均误差: {np.abs(error_matrix).mean():.6f}")
    print(f"误差标准差: {np.abs(error_matrix).std():.6f}")
    
    # 计算相似度
    from scipy.stats import pearsonr
    orig_flat = original_weight.detach().numpy().flatten()
    lora_flat = lora_approximation.detach().numpy().flatten()
    correlation, _ = pearsonr(orig_flat, lora_flat)
    print(f"矩阵相似度(相关系数): {correlation:.6f}")
    
# 5. 主函数
def main():
    # 设置维度
    d, k = 10, 10  # 使用较小的维度便于演示
    r = 2  # LoRA秩
    
    # 创建原始权重
    original_weight = create_original_matrix(d, k)
    
    # 创建LoRA层
    lora_layer = LoRALayer(d, k, r)
    
    # 训练LoRA
    losses = train_lora(original_weight, lora_layer)
    
    # 获取最终的LoRA近似
    final_approximation = lora_layer.get_weight_update()
    
    # 计算参数量的节省
    original_params = d * k
    lora_params = r * (d + k)
    reduction = (1 - lora_params/original_params) * 100
    
    print(f"\n原始参数量: {original_params}")
    print(f"LoRA参数量: {lora_params}")
    print(f"参数减少: {reduction:.2f}%")
    
    # 可视化结果
    visualize_results(original_weight, final_approximation, losses)


if __name__ == "__main__":
    main()
```

```Response
Iteration 0, Loss: 1.099842
Iteration 100, Loss: 0.589540
Iteration 200, Loss: 0.439351
Iteration 300, Loss: 0.435789
Iteration 400, Loss: 0.435765
Iteration 500, Loss: 0.435765
Iteration 600, Loss: 0.435765
Iteration 700, Loss: 0.435765
Iteration 800, Loss: 0.435765
Iteration 900, Loss: 0.435765

原始参数量: 100
LoRA参数量: 40
参数减少: 60.00%

原始权重矩阵的一部分(5x5):
[[ 1.9020243  -0.98042786  0.47197205  0.00751896  0.45111972]
 [-0.6989953  -0.7539018  -1.6730322   0.895078    0.72842824]
 [ 1.1006526   0.32565323 -0.13668585  0.4227683   0.05465927]
 [-0.88375205  0.60963565 -1.5299315   0.43329597 -1.7178423 ]
 [ 1.3465533  -0.571326    0.07685361 -1.1320914  -1.1538632 ]]

LoRA近似后的矩阵的一部分(5x5):
[[ 1.4178535  -0.10202433  0.97077304 -0.0949342   0.46077988]
 [-1.1337396   0.3354595  -0.7775882   0.9027459   0.12311662]
 [ 1.002753    0.09579059  0.6856753   0.4798254   0.6510572 ]
 [-0.72393465  0.1751302  -0.49631235  0.4491832   0.00296068]
 [ 0.8751194  -0.5518392   0.6017585  -1.6507436  -0.66215307]]

误差矩阵的一部分(5x5):
[[ 0.4841708  -0.87840354 -0.498801    0.10245315 -0.00966015]
 [ 0.4347443  -1.0893613  -0.895444   -0.0076679   0.60531163]
 [ 0.09789956  0.22986263 -0.8223612  -0.05705711 -0.59639794]
 [-0.1598174   0.43450546 -1.0336192  -0.01588723 -1.720803  ]
 [ 0.47143394 -0.01948684 -0.52490485  0.5186522  -0.49171013]]

统计指标:
最大误差: 1.733717
平均误差: 0.537437
误差标准差: 0.383309
矩阵相似度(相关系数): 0.776545
```


![自定义 basejre]({{ site.url }}/assets/img/lora-expamle/lora-example-result.png)