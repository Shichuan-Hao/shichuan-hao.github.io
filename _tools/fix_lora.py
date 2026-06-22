"""临时脚本：清理 LoRA 文章中遗留的重复内容"""
import re

path = r"f:\happymaya\web\shichuanhao.github.io\_posts\aigc\fine-tuning\2024-11-01-LoRA-Fine-tuning-Principles-Explained.md"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 删除 {: .prompt-tip } 之后到 ### LoRA 代码实现 之前的重复残留内容
old = re.search(
    r'(\{: \.prompt-tip \}\n)(.*?)(\n### LoRA 代码实现)',
    content, re.DOTALL
)

if old:
    # 中间部分替换为空行
    new_block = old.group(1) + "\n" + old.group(3)
    content = content[:old.start()] + new_block + content[old.end():]

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done!")
