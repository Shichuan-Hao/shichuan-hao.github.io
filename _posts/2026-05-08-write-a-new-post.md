---
title: 撰写新文章
author: cotes
date: 2026-05-08 15:27:00 +0800
categories: [博客, 教程]
tags: [写作]
render_with_liquid: false
---

本教程将指导你如何在 _Chirpy_ 模板中撰写文章。即使你之前使用过 Jekyll，也值得阅读本文，因为许多功能需要设置特定的变量才能使用。

## 命名和路径

新建一个名为 `YYYY-MM-DD-TITLE.EXTENSION`{: .filepath} 的文件，并将其放置在根目录的 `_posts`{: .filepath} 文件夹中。请注意，`EXTENSION`{: .filepath} 必须是 `md`{: .filepath} 或 `markdown`{: .filepath} 之一。如果你想节省创建文件的时间，可以考虑使用插件 [`Jekyll-Compose`](https://github.com/jekyll/jekyll-compose) 来完成此操作。

## Front Matter

基本上，你需要在下方的文章顶部填写 [Front Matter](https://jekyllrb.com/docs/front-matter/)：

```yaml
---
title: 标题
date: YYYY-MM-DD HH:MM:SS +/-TTTT
categories: [主分类, 子分类]
tags: [标签]     # 标签名称应始终使用小写
---
```

> 文章的 _布局_ 已默认设置为 `post`，因此无需在 Front Matter 块中添加 _layout_ 变量。
{: .prompt-tip }

### 日期时区

为了准确记录文章发布日期，你不仅需要在 `_config.yml`{: .filepath} 中设置 `timezone`，还应在 Front Matter 块的 `date` 变量中提供文章的时区。格式：`+/-TTTT`，例如 `+0800`。

### 分类和标签

每篇文章的 `categories` 设计最多包含两个元素，而 `tags` 的元素数量可以为零到无限个。例如：

```yaml
---
categories: [动物, 昆虫]
tags: [蜜蜂]
---
```

### 作者信息

文章的作者信息通常不需要在 _Front Matter_ 中填写，它们会默认从配置文件的 `social.name` 和 `social.links` 第一个条目获取。但你也可以按以下方式覆盖：

在 `_data/authors.yml` 中添加作者信息（如果你的网站没有此文件，请直接创建一个）。

```yaml
<作者ID>:
  name: <全名>
  twitter: <作者推特>
  url: <作者主页>
```
{: file="_data/authors.yml" }

然后使用 `author` 指定单个条目或 `authors` 指定多个条目：

```yaml
---
author: <作者ID>                     # 单个条目
# 或者
authors: [<作者1ID>, <作者2ID>]   # 多个条目
---
```

需要说明的是，`author` 键也可以识别多个条目。

> 从文件 `_data/authors.yml`{: .filepath} 读取作者信息的好处是，页面将包含 `twitter:creator` 元标签，这可以丰富 [Twitter Cards](https://developer.twitter.com/en/docs/twitter-for-websites/cards/guides/getting-started#card-and-content-attribution) 并有助于 SEO。
{: .prompt-info }

### 文章描述

默认情况下，文章的前几句话会显示在首页文章列表、"延伸阅读"部分和 RSS 订阅的 XML 中。如果你不希望显示自动生成的文章描述，可以使用 _Front Matter_ 中的 `description` 字段自定义，如下所示：

```yaml
---
description: 文章简短摘要。
---
```

此外，`description` 文本也会显示在文章页面的标题下方。

## 目录

默认情况下，**目**录（TOC）会显示在文章的右侧面板。如果你想全局关闭目录功能，请进入 `_config.yml`{: .filepath} 并将变量 `toc` 设置为 `false`。如果只想关闭特定文章的目录，请在文章的 [Front Matter](https://jekyllrb.com/docs/front-matter/) 中添加以下内容：

```yaml
---
toc: false
---
```

## 评论

评论的全局设置在 `_config.yml`{: .filepath} 文件的 `comments.provider` 选项中定义。一旦为此变量选择了评论系统，评论将自动对所有文章启用。

如果你想关闭特定文章的评论，请在文章的 **Front Matter** 中添加以下内容：

```yaml
---
comments: false
---
```

## 媒体资源

在 _Chirpy_ 中，我们把图片、音频和视频称为媒体资源。

### URL 前缀

我们经常需要为一篇文章中的多个资源定义重复的 URL 前缀，这是一项繁琐的任务。你可以通过设置两个参数来避免这个问题。

- 如果你使用 CDN 来托管媒体文件，可以在 `_config.yml`{: .filepath} 中指定 `cdn`。媒体资源的 URL（网站头像和文章图片）前面会自动加上 CDN 域名。

  ```yaml
  cdn: https://cdn.com
  ```
  {: file='_config.yml' .nolineno }

- 要为当前文章/页面范围指定资源路径前缀，请在文章的 _front matter_ 中设置 `media_subpath`：

  ```yaml
  ---
  media_subpath: /path/to/media/
  ---
  ```
  {: .nolineno }

`site.cdn` 和 `page.media_subpath` 选项可以单独使用，也可以组合使用，灵活组成最终的资源 URL：`[site.cdn/][page.media_subpath/]file.ext`

### 图片

#### 标题

在图片的下一行添加斜体，它就会变成标题并显示在图片底部：

```markdown
![图片描述](/path/to/image)
:_图片标题_
```
{: .nolineno}

#### 尺寸

为了防止图片加载时页面内容布局发生偏移，我们应该为每张图片设置宽度和高度。

```markdown
![桌面视图](/assets/img/sample/mockup.png){: width="700" height="400" }
```
{: .nolineno}

> 对于 SVG 文件，你必须至少指定其 _宽度_，否则无法渲染。
{: .prompt-info }

从 _Chirpy v5.0.0_ 开始，`height` 和 `width` 支持缩写（`height` → `h`，`width` → `w`）。以下示例与上面的效果相同：

```markdown
![桌面视图](/assets/img/sample/mockup.png){: w="700" h="400" }
```
{: .nolineno}

#### 位置

默认情况下，图片居中显示，但你可以通过使用 `normal`、`left` 和 `right` 类之一来指定位置。

> 一旦指定了位置，就不应再添加图片标题。
{: .prompt-warning }

- **正常位置**

  在以下示例中，图片将左对齐：

  ```markdown
  ![桌面视图](/assets/img/sample/mockup.png){: .normal }
  ```
  {: .nolineno}

- **向左浮动**

  ```markdown
  ![桌面视图](/assets/img/sample/mockup.png){: .left }
  ```
  {: .nolineno}

- **向右浮动**

  ```markdown
  ![桌面视图](/assets/img/sample/mockup.png){: .right }
  ```
  {: .nolineno}

#### 深色/浅色模式

你可以让图片根据深色/浅色模式偏好显示。这需要你准备两张图片，一张用于深色模式，一张用于浅色模式，然后为它们分配特定的类（`dark` 或 `light`）：

```markdown
![仅浅色模式](/path/to/light-mode.png){: .light }
![仅深色模式](/path/to/dark-mode.png){: .dark }
```

#### 阴影

程序窗口的截图可以考虑显示阴影效果：

```markdown
![桌面视图](/assets/img/sample/mockup.png){: .shadow }
```
{: .nolineno}

#### 预览图片

如果你想在文章顶部添加图片，请提供分辨率 `1200 x 630` 的图片。请注意，如果图片宽高比不符合 `1.91 : 1`，图片将被缩放和裁剪。

了解这些前提条件后，你可以开始设置图片属性：

```yaml
---
image:
  path: /path/to/image
  alt: 图片替代文本
---
```

请注意，[`media_subpath`](#url-prefix) 也可以传递给预览图片，即当它被设置后，属性 `path` 只需要图片文件名即可。

对于简单使用，你也可以直接使用 `image` 定义路径。

```yml
---
image: /path/to/image
---
```

#### LQIP

预览图片的 LQIP：

```yaml
---
image:
  lqip: /path/to/lqip-file # 或 base64 URI
---
```

> 你可以在文章"[文本和排版](../text-and-typography/)"的预览图片中观察 LQIP 效果。

普通图片的 LQIP：

```markdown
![图片描述](/path/to/image){: lqip="/path/to/lqip-file" }
```
{: .nolineno }

### 社交媒体平台

你可以使用以下语法嵌入社交媒体平台的视频/音频：

```liquid
{% include embed/{平台}.html id='{ID}' %}
```

其中 `平台` 是平台名称的小写，`ID` 是视频/音频 ID。

下表显示了如何从给定的视频/音频 URL 获取这两个参数，你也可以查看当前支持的视频平台：

| 视频 URL                                                                                                                  | 平台      | ID                       |
| :------------------------------------------------------------------------------------------------------------------------ | :-------- | :----------------------- |
| [https://www.**youtube**.com/watch?v=**H-B46URT4mg**](https://www.youtube.com/watch?v=H-B46URT4mg)                         | `youtube` | `H-B46URT4mg`            |
| [https://www.**twitch**.tv/videos/**1634779211**](https://www.twitch.tv/videos/1634779211)                                 | `twitch`  | `1634779211`             |
| [https://www.**bilibili**.com/video/**BV1Q44y1B7Wf**](https://www.bilibili.com/video/BV1Q44y1B7Wf)                         | `bilibili`| `BV1Q44y1B7Wf`            |
| [https://www.open.**spotify**.com/track/**3OuMIIFP5TxM8tLXMWYPGV**](https://open.spotify.com/track/3OuMIIFP5TxM8tLXMWYPGV) | `spotify` | `3OuMIIFP5TxM8tLXMWYPGV` |

Spotify 支持一些额外参数：

- `compact` - 显示紧凑型播放器（例如 `{% include embed/spotify.html id='3OuMIIFP5TxM8tLXMWYPGV' compact=1 %}`）；
- `dark` - 强制使用深色主题（例如 `{% include embed/spotify.html id='3OuMIIFP5TxM8tLXMWYPGV' dark=1 %}`）。

### 视频文件

如果你想直接嵌入视频文件，请使用以下语法：

```liquid
{% include embed/video.html src='{URL}' %}
```

其中 `URL` 是视频文件的 URL，例如 `/path/to/sample/video.mp4`。

你还可以为嵌入式视频文件指定其他属性。以下是允许的完整属性列表：

- `poster='/path/to/poster.png'` — 视频下载时显示的封面图片
- `title='文本'` — 显示在视频下方且与图片标题样式相同的视频标题
- `autoplay=true` — 视频一旦可以播放就自动开始
- `loop=true` — 到达视频结尾时自动跳回开头
- `muted=true` — 音频最初会被静音
- `types` — 指定以 `|` 分隔的其他视频格式扩展名。确保这些文件与主视频文件位于同一目录中。

以下是使用上述所有属性的示例：

```liquid
{%
  include embed/video.html
  src='/path/to/video.mp4'
  types='ogg|mov'
  poster='poster.png'
  title='Demo video'
  autoplay=true
  loop=true
  muted=true
%}
```

### 音频文件

如果你想直接嵌入音频文件，请使用以下语法：

```liquid
{% include embed/audio.html src='{URL}' %}
```

其中 `URL` 是音频文件的 URL，例如 `/path/to/audio.mp3`。

你还可以为嵌入式音频文件指定其他属性。以下是允许的完整属性列表：

- `title='文本'` — 显示在音频下方且与图片标题样式相同的音频标题
- `types` — 指定以 `|` 分隔的其他音频格式扩展名。确保这些文件与主音频文件位于同一目录中。

以下是使用上述所有属性的示例：

```liquid
{%
  include embed/audio.html
  src='/path/to/audio.mp3'
  types='ogg|wav|aac'
  title='Demo audio'
%}
```

## 置顶文章

你可以将一篇文章或多篇文章置顶在首页顶部，置顶的文章会按发布日期的倒序排列。启用方法：

```yaml
---
pin: true
---
```

## 提示框

有几种类型的提示框：`tip`、`info`、`warning` 和 `danger`。你可以通过在引用块中添加类 `prompt-{type}` 来生成提示框。例如，定义一个类型为 `info` 的提示框如下：

```md
> 示例提示行。
{: .prompt-info }
```
{: .nolineno }

## 语法

### 行内代码

```md
`行内代码部分`
```
{: .nolineno }

### 文件路径高亮

```md
`/path/to/a/file.extend`{: .filepath}
```
{: .nolineno }

### 代码块

Markdown 符号 ```` ``` ```` 可以轻松创建代码块，如下所示：

````md
```
这是纯文本代码片段。
```
````

#### 指定语言

使用 ```` ```{语言} ```` 你将获得带有语法高亮的代码块：

````markdown
```yaml
key: value
```
````

> Jekyll 标签 `{% highlight %}` 与此主题不兼容。
{: .prompt-danger }

#### 行号

默认情况下，除 `plaintext`、`console` 和 `terminal` 外的所有语言都会显示行号。当你想隐藏代码块的行号时，请向其添加类 `nolineno`：

````markdown
```shell
echo 'No more line numbers!'
```
{: .nolineno }
````

#### 指定文件名

你可能已经注意到，代码语言会显示在代码块的顶部。如果你想用文件名替换它，可以添加属性 `file` 来实现：

````markdown
```shell
# 内容
```
{: file="path/to/file" }
````

#### Liquid 代码

如果你想显示 **Liquid** 代码片段，请用 `{% raw %}` 和 `{% endraw %}` 包围 Liquid 代码：

````markdown
{% raw %}
```liquid
{% if product.title contains 'Pack' %}
  This product's title contains the word Pack.
{% endif %}
```
{% endraw %}
````

或在文章的 YAML 块中添加 `render_with_liquid: false`（需要 Jekyll 4.0 或更高版本）。

## 数学公式

我们使用 [**MathJax**][mathjax] 来生成数学公式。出于网站性能考虑，数学功能默认不会加载。但可以通过以下方式启用：

[mathjax]: https://www.mathjax.org/

```yaml
---
math: true
---
```

启用数学功能后，你可以使用以下语法添加数学公式：

- **块级公式**应使用 `$$ math $$` 添加，**必须**在 `$$` 前后留空行
  - **公式编号**应使用 `$$\begin{equation} math \end{equation}$$` 添加
  - **引用公式编号**应在公式块中使用 `\label{eq:标签名}`，并在文本中使用 `\eqref{eq:标签名}`（见下方示例）
- **行内公式**（在行中）应使用 `$$ math $$` 添加，**前后不**留空行
- **行内公式**（在列表中）应使用 `\$$ math $$`

```markdown
<!-- 块级公式，保持所有空行 -->

$$
LaTeX_数学表达式
$$

<!-- 公式编号，保持所有空行  -->

$$
\begin{equation}
  LaTeX_数学表达式
  \label{eq:标签名}
\end{equation}
$$

可以引用为 \eqref{eq:标签名}。

<!-- 行内公式在行中，不留空行 -->

"Lorem ipsum dolor sit amet, $$ LaTeX_数学表达式 $$ consectetur adipiscing elit."

<!-- 行内公式在列表中，转义第一个 `$` -->

1. \$$ LaTeX_数学表达式 $$
2. \$$ LaTeX_数学表达式 $$
3. \$$ LaTeX_数学表达式 $$
```

> 从 v7.0.0 开始，**MathJax** 的配置选项已移至文件 `assets/js/data/mathjax.js`{: .filepath }，你可以根据需要更改选项，例如添加 [扩展][mathjax-exts]。  
> 如果你通过 `chirpy-starter` 构建网站，请从 gem 安装目录（使用命令 `bundle info --path jekyll-theme-chirpy` 检查）将该文件复制到仓库中的同一目录。
{: .prompt-tip }

[mathjax-exts]: https://docs.mathjax.org/en/latest/input/tex/extensions/index.html

## Mermaid

[**Mermaid**](https://github.com/mermaid-js/mermaid) 是一个出色的图表生成工具。要在文章中启用它，请在 YAML 块中添加以下内容：

```yaml
---
mermaid: true
---
```

然后你可以像使用其他 markdown 语言一样使用它：用 ```` ```mermaid ```` 和 ```` ``` ```` 包围图形代码。

## 了解更多

了解更多关于 Jekyll 文章的知识，请访问 [Jekyll 文档：文章](https://jekyllrb.com/docs/posts/)。
