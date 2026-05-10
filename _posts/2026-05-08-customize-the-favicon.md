---
title: 自定义网站图标
author: cotes
date: 2026-05-08 18:27:00 +0800
categories: [博客, 教程]
tags: [图标]
---

[**Chirpy**](https://github.com/cotes2020/jekyll-theme-chirpy/) 的 [网站图标](https://www.favicon-generator.org/about/) 位于目录 `assets/img/favicons/`{: .filepath} 中。你可能想用自己的图标替换它们。以下部分将指导你创建和替换默认的网站图标。

## 生成网站图标

准备一张正方形图片（PNG、JPG 或 SVG），尺寸为 512x512 或更大，然后前往在线工具 [**Real Favicon Generator**](https://realfavicongenerator.net/)，点击按钮 <kbd>Pick your favicon image</kbd> 上传你的图片文件。

在下一步中，网页将显示所有使用场景。你可以保持默认选项，滚动到页面底部，点击按钮 <kbd>Next →</kbd> 来生成网站图标。

## 下载并替换

下载生成的压缩包，解压后从提取的文件中删除以下文件：

- `site.webmanifest`{: .filepath}

然后将剩余的图片文件（`.PNG`{: .filepath}、`.ICO`{: .filepath} 和 `.SVG`{: .filepath}）复制并覆盖 Jekyll 网站目录 `assets/img/favicons/`{: .filepath} 中的原始文件。如果你的 Jekyll 网站还没有此目录，只需创建一个即可。

下表将帮助你了解网站图标文件的变化：

| 文件 | 来自在线工具 | 来自 Chirpy |
| :--- | :---------: | :---------: |
| `*.PNG` |        ✓    |      ✗      |
| `*.ICO` |        ✓    |      ✗      |
| `*.SVG` |        ✓    |      ✗      |

<!-- markdownlint-disable-next-line -->
> ✓ 表示保留，✗ 表示删除。
{: .prompt-info }

下次构建网站时，网站图标将被替换为自定义版本。
