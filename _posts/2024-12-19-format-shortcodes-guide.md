---
title: "格式化短标签使用指南"
description: '写 Markdown 时，给文字加颜色需要写一长串 &lt;span style="color:red;"&gt;，非常繁琐。'
author: hsc
date: 2024-12-19 15:00:00 +0800
categories: [博客运营]
tags: []
published: false
---

## 为什么需要短标签？

<tip>写 Markdown 时，给文字加颜色需要写一长串 &lt;span style="color:red;"&gt;，非常繁琐。
这套短标签系统让你用简洁的语法，实现丰富的格式化效果。
</tip>

## 内联标签

### 加粗 / 斜体 / 下划线 / 删除线

| 标签 | 效果 |
|------|------|
| `<b>加粗文字</b>` | <b>加粗文字</b> |
| `<i>斜体文字</i>` | <i>斜体文字</i> |
| `<u>下划线</u>` | <u>下划线</u> |
| `<s>删除线</s>` | <s>删除线</s> |

### 文字颜色

使用 `<color=颜色值>文字</color>`，支持颜色名、十六进制、 rgb()。

| 标签 | 效果 |
|------|------|
| `<color=red>红色</color>` | <color=red>红色</color> |
| `<color=blue>蓝色</color>` | <color=blue>蓝色</color> |
| `<color=green>绿色</color>` | <color=green>绿色</color> |
| `<color=orange>橙色</color>` | <color=orange>橙色</color> |
| `<color=purple>紫色</color>` | <color=purple>紫色</color> |
| `<color=#3498db>自定义色</color>` | <color=#3498db>自定义色</color> |

### 背景颜色

| 标签 | 效果 |
|------|------|
| `<bg=yellow>黄色背景</bg>` | <bg=yellow>黄色背景</bg> |
| `<bg=cyan>青色背景</bg>` | <bg=cyan>青色背景</bg> |
| `<bg=#ffe0b2>暖色背景</bg>` | <bg=#ffe0b2>暖色背景</bg> |

### 高亮（加粗 + 颜色）

| 标签 | 效果 |
|------|------|
| `<hl=red>重点高亮</hl>` | <hl=red>重点高亮</hl> |
| `<hl=blue>蓝色高亮</hl>` | <hl=blue>蓝色高亮</hl> |

### 荧光笔标记

`<mark>这是重点内容</mark>` → <mark>这是重点内容</mark>

### 字号调整

`<size=24px>大号文字</size>` → <size=24px>大号文字</size>

## 块级标签

### 居中

<center>这段文字会居中显示</center>

### 提示框

<tip>这是一个提示信息框，用于强调重要但非紧急的信息。
比如：在生产环境中部署前，建议先在测试环境验证。
</tip>

### 警告框

<warn>这是一个警告信息框，用于提醒需要注意的风险。
比如：此操作不可逆，请在执行前做好数据备份！
</warn>

## 实际文章中的用法

在写技术文章时，可以这样使用：

<hl=purple>Elasticsearch</hl> 是一个分布式的 <color=red>搜索引擎</color>，它的核心优势在于 <b>全文检索</b> 和 <u>近实时搜索</u>。

<tip>ES 默认使用 <mark>倒排索引</mark> 来加速全文检索，这是其高性能的关键。
</tip>

<warn>集群节点数量应为奇数，使用 <color=red>3</color> 个或更多主节点来避免脑裂问题。
</warn>

## 使用方式

### 方式一： Jekyll 插件（推荐，自动生效）

插件文件：`_plugins/format-shortcodes.rb`

在 Markdown 中直接使用标签，运行 `jekyll serve` 即可自动转换，无需额外操作。

### 方式二： Python 脚本（独立使用）

```bash
# 处理单个文件
python tools/format_md.py _posts/my-article.md

# 预览模式（不修改文件）
python tools/format_md.py _posts/my-article.md --dry-run

# 输出到新文件
python tools/format_md.py _posts/my-article.md -o output.md

# 批量处理目录
python tools/format_md.py _posts/ -r
```

## 支持的完整标签列表

| 标签 | 说明 | 示例 |
|------|------|------|
| `<b>` | 加粗 | `<b>text</b>` |
| `<i>` | 斜体 | `<i>text</i>` |
| `<u>` | 下划线 | `<u>text</u>` |
| `<s>` | 删除线 | `<s>text</s>` |
| `<color=COLOR>` | 文字颜色 | `<color=red>text</color>` |
| `<bg=COLOR>` | 背景颜色 | `<bg=yellow>text</bg>` |
| `<hl=COLOR>` | 高亮(加粗+色) | `<hl=red>text</hl>` |
| `<mark>` | 荧光标记 | `<mark>text</mark>` |
| `<size=N>` | 字号 | `<size=20px>text</size>` |
| `<center>` | 居中 | `<center>text</center>` |
| `<right>` | 右对齐 | `<right>text</right>` |
| `<tip>` | 提示框 | `<tip>content</tip>` |
| `<warn>` | 警告框 | `<warn>content</warn>` |
