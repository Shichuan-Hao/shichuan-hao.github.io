---
title: 文本与排版
description: 文本、排版、数学公式、图表、流程图、图片、视频等示例。
author: cotes
date: 2026-05-08 17:27:00 +0800
categories: [博客, 示例]
tags: [排版]
pin: true
math: true
mermaid: true
image:
  path: /assets/img/posts/devices-mockup.png
  lqip: data:image/webp;base64,UklGRpoAAABXRUJQVlA4WAoAAAAQAAAADwAABwAAQUxQSDIAAAARL0AmbZurmr57yyIiqE8oiG0bejIYEQTgqiDA9vqnsUSI6H+oAERp2HZ65qP/VIAWAFZQOCBCAAAA8AEAnQEqEAAIAAVAfCWkAALp8sF8rgRgAP7o9FDvMCkMde9PK7euH5M1m6VWoDXf2FkP3BqV0ZYbO6NA/VFIAAAA
  alt: Chirpy 主题在多种设备上的响应式渲染效果。
---

## 标题

<!-- markdownlint-capture -->
<!-- markdownlint-disable -->
# H1 — 标题
{: .mt-4 .mb-0 }

## H2 — 标题
{: data-toc-skip='' .mt-4 .mb-0 }

### H3 — 标题
{: data-toc-skip='' .mt-4 .mb-0 }

#### H4 — 标题
{: data-toc-skip='' .mt-4 }
<!-- markdownlint-restore -->

## 段落

Quisque egestas convallis ipsum, ut sollicitudin risus tincidunt a. Maecenas interdum malesuada egestas. Duis consectetur porta risus, sit amet vulputate urna facilisis ac. Phasellus semper dui non purus ultrices sodales. Aliquam ante lorem, ornare a feugiat ac, finibus nec mauris. Vivamus ut tristique nisi. Sed vel leo vulputate, efficitur risus non, posuere mi. Nullam tincidunt bibendum rutrum. Proin commodo ornare sapien. Vivamus interdum diam sed sapien blandit, sit amet aliquam risus mattis. Nullam arcu turpis, mollis quis laoreet at, placerat id nibh. Suspendisse venenatis eros eros.

## 列表

### 有序列表

1. 第一
2. 第二
3. 第三

### 无序列表

- 章节
  - 小节
    - 段落

### 待办事项列表

- [ ] 任务
  - [x] 第一步
  - [x] 第二步
  - [ ] 第三步

### 定义列表

太阳
: 地球环绕运行的恒星

月亮
: 地球的天然卫星，通过反射太阳光可见

## 引用块

> 这行显示的是 _引用块_。

## 提示框

<!-- markdownlint-capture -->
<!-- markdownlint-disable -->
> `tip` 类型提示框示例。
{: .prompt-tip }

> `info` 类型提示框示例。
{: .prompt-info }

> `warning` 类型提示框示例。
{: .prompt-warning }

> `danger` 类型提示框示例。
{: .prompt-danger }
<!-- markdownlint-restore -->

## 表格

| 公司                      | 联系人           | 国家 |
| :------------------------ | :--------------- | ---: |
| Alfreds Futterkiste       | Maria Anders     | 德国 |
| Island Trading            | Helen Bennett    |   英国 |
| Magazzini Alimentari Riuniti | Giovanni Rovelli | 意大利 |

## 链接

<http://127.0.0.1:4000>

## 脚注

点击钩子将定位到脚注[^脚注]，这里还有另一个脚注[^fn-nth-2]。

## 行内代码

这是 `行内代码` 的示例。

## 文件路径

这是 `/path/to/the/file.extend`{: .filepath}。

## 代码块

### 普通代码块

<!-- markdownlint-disable-next-line MD040 -->
```
这是一个普通代码片段，没有语法高亮和行号。
```

### 指定语言

```bash
if [ $? -ne 0 ]; then
  echo "命令执行失败。";
  #do the needful / exit
fi;
```

### 指定文件名

```sass
@import
  "colors/light-typography",
  "colors/dark-typography";
```
{: file='_sass/jekyll-theme-chirpy.scss'}

## 数学公式

由 [**MathJax**](https://www.mathjax.org/) 驱动的数学公式：

$$
\begin{equation}
  \sum_{n=1}^\infty 1/n^2 = \frac{\pi^2}{6}
  \label{eq:series}
\end{equation}
$$

我们可以引用这个公式为 \eqref{eq:series}。

当 $a \ne 0$ 时，$ax^2 + bx + c = 0$ 有两个解，它们是

$$ x = {-b \pm \sqrt{b^2-4ac} \over 2a} $$

## Mermaid SVG

```mermaid
 gantt
  title  为 mermaid 添加甘特图功能
  苹果 :a, 2017-07-20, 1w
  香蕉 :crit, b, 2017-07-23, 1d
  樱桃 :active, c, after b a, 1d
```

## 图片

### 默认（带标题）

![桌面视图](/assets/img/posts/devices-mockup.png){: width="972" height="589" }
_全屏宽度并居中对齐_

### 左对齐

![桌面视图](/assets/img/posts/left_align.png){: width="972" height="589" .w-75 .normal}

### 向左浮动

![桌面视图](/assets/img/posts/float-to-left-mockup.png){: width="972" height="589" .w-50 .left}
Praesent maximus aliquam sapien. Sed vel neque in dolor pulvinar auctor. Maecenas pharetra, sem sit amet interdum posuere, tellus lacus eleifend magna, ac lobortis felis ipsum id sapien. Proin ornare rutrum metus, ac convallis diam volutpat sit amet. Phasellus volutpat, elit sit amet tincidunt mollis, felis mi scelerisque mauris, ut facilisis leo magna accumsan sapien. In rutrum vehicula nisl eget tempor. Nullam maximus ullamcorper libero non maximus. Integer ultricies velit id convallis varius. Praesent eu nisl eu urna finibus ultrices id nec ex. Mauris ac mattis quam. Fusce aliquam est nec sapien bibendum, vitae malesuada ligula condimentum.

### 向右浮动

![桌面视图](/assets/img/posts/float-to-right-mockup.png){: width="972" height="589" .w-50 .right}
Praesent maximus aliquam sapien. Sed vel neque in dolor pulvinar auctor. Maecenas pharetra, sem sit amet interdum posuere, tellus lacus eleifend magna, ac lobortis felis ipsum id sapien. Proin ornare rutrum metus, ac convallis diam volutpat sit amet. Phasellus volutpat, elit sit amet tincidunt mollis, felis mi scelerisque mauris, ut facilisis leo magna accumsan sapien. In rutrum vehicula nisl eget tempor. Nullam maximus ullamcorper libero non maximus. Integer ultricies velit id convallis varius. Praesent eu nisl eu urna finibus ultrices id nec ex. Mauris ac mattis quam. Fusce aliquam est nec sapien bibendum, vitae malesuada ligula condimentum.

### 深色/浅色模式 & 阴影

下面的图片会根据主题偏好切换深色/浅色模式，注意它带有阴影。

![仅浅色模式](/assets/img/posts/shadow.png){: .light .w-75 .shadow .rounded-10 w='1212' h='668' }
![仅深色模式](/assets/img/posts/shadow-1.png){: .dark .w-75 .shadow .rounded-10 w='1212' h='668' }

## 视频

{% include embed/youtube.html id='Balreaj8Yqs' %}

## 脚注回链

[^脚注]: 脚注来源
[^fn-nth-2]: 第二个脚注来源
