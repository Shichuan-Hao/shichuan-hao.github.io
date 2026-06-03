#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown 格式化短标签处理器
=============================

一个独立的 Python 脚本，用于将自定义格式化短标签转换为标准 HTML。
可在任意 Markdown 项目中使用，不依赖 Jekyll。

支持的标签：
  内联标签：
    <b>text</b>               加粗
    <i>text</i>               斜体
    <u>text</u>               下划线
    <s>text</s>               删除线
    <color=COLOR>text</color>  文字颜色（red, #ff0000, rgb(255,0,0) 等）
    <bg=COLOR>text</bg>        背景颜色
    <hl=COLOR>text</hl>        高亮（加粗+颜色）
    <mark>text</mark>          荧光笔高亮
    <size=N>text</size>        指定字号（如 20px）
    <center>text</center>      居中
    <right>text</right>        右对齐

  块级标签：
    <tip>...</tip>             绿色提示框
    <warn>...</warn>           橙色警告框

用法：
  # 处理单个文件（原地修改）
  python tools/format_md.py _posts/my-post.md

  # 处理单个文件（输出到新文件）
  python tools/format_md.py _posts/my-post.md -o output.md

  # 处理整个目录
  python tools/format_md.py _posts/

  # 预览模式（只打印，不修改）
  python tools/format_md.py _posts/my-post.md --dry-run

  # 递归处理目录下所有 .md 文件
  python tools/format_md.py _posts/ -r

Author: Hao Shichuan
"""

import re
import sys
import os
import argparse
from pathlib import Path


# =============================================================
#  转换规则定义
# =============================================================

# 颜色名称到十六进制的映射（常用颜色）
COLOR_MAP = {
    'red':        '#e74c3c',
    'blue':       '#2980b9',
    'green':      '#27ae60',
    'orange':     '#e67e22',
    'purple':     '#8e44ad',
    'yellow':     '#f1c40f',
    'pink':       '#e91e63',
    'cyan':       '#00bcd4',
    'teal':       '#009688',
    'brown':      '#795548',
    'grey':       '#9e9e9e',
    'gray':       '#9e9e9e',
    'black':      '#333333',
    'white':      '#ffffff',
    'lime':       '#cddc39',
    'indigo':     '#3f51b5',
    'amber':      '#ffc107',
}


def resolve_color(color_str: str) -> str:
    """解析颜色值，支持名称、十六进制、rgb()"""
    c = color_str.strip().lower()
    if c in COLOR_MAP:
        return COLOR_MAP[c]
    # 如果是有效 CSS 颜色值，直接使用
    if re.match(r'^(#[0-9a-fA-F]{3,8}|rgb\(|rgba\(|hsl\(|hsla\()', c):
        return color_str.strip()
    # 默认当作十六进制处理
    return color_str.strip()


# =============================================================
#  内联标签转换函数
# =============================================================

def convert_color(match: re.Match) -> str:
    """<color=COLOR>text</color>"""
    color = resolve_color(match.group(1))
    text = match.group(2)
    return f'<span style="color:{color};">{text}</span>'


def convert_bg(match: re.Match) -> str:
    """<bg=COLOR>text</bg>"""
    color = resolve_color(match.group(1))
    text = match.group(2)
    return f'<span style="background-color:{color};padding:0 4px;">{text}</span>'


def convert_hl(match: re.Match) -> str:
    """<hl=COLOR>text</hl>"""
    color = resolve_color(match.group(1))
    text = match.group(2)
    return f'<span style="color:{color};font-weight:bold;">{text}</span>'


def convert_mark(match: re.Match) -> str:
    """<mark>text</mark>"""
    text = match.group(1)
    return f'<mark style="background-color:#fff59d;padding:0 2px;">{text}</mark>'


def convert_size(match: re.Match) -> str:
    """<size=N>text</size>"""
    size = match.group(1).strip()
    text = match.group(2)
    return f'<span style="font-size:{size};">{text}</span>'


def convert_center(match: re.Match) -> str:
    """<center>text</center>"""
    text = match.group(1)
    return f'<div style="text-align:center;">{text}</div>'


def convert_right(match: re.Match) -> str:
    """<right>text</right>"""
    text = match.group(1)
    return f'<div style="text-align:right;">{text}</div>'


def convert_tip(match: re.Match) -> str:
    """<tip>content</tip>"""
    inner = match.group(1)
    return (
        '<blockquote style="background:#e8f5e9;border-left:4px solid #4caf50;'
        'padding:10px 16px;margin:12px 0;border-radius:4px;">\n'
        f'💡 <b>提示：</b>{inner}\n'
        '</blockquote>'
    )


def convert_warn(match: re.Match) -> str:
    """<warn>content</warn>"""
    inner = match.group(1)
    return (
        '<blockquote style="background:#fff3e0;border-left:4px solid #ff9800;'
        'padding:10px 16px;margin:12px 0;border-radius:4px;">\n'
        f'⚠️ <b>警告：</b>{inner}\n'
        '</blockquote>'
    )


# =============================================================
#  转换规则列表（按顺序执行）
# =============================================================

# (正则表达式, 替换函数, 是否跨行匹配)
INLINE_RULES = [
    # 注意：<b>, <i>, <u>, <s> 是标准 HTML，Markdown 会自动放行，这里也做显式保证
    (r'<b>(.*?)</b>',                lambda m: f'<b>{m.group(1)}</b>'),
    (r'<i>(.*?)</i>',                lambda m: f'<i>{m.group(1)}</i>'),
    (r'<u>(.*?)</u>',                lambda m: f'<u>{m.group(1)}</u>'),
    (r'<s>(.*?)</s>',                lambda m: f'<s>{m.group(1)}</s>'),
    (r'<color=([^>]+)>(.*?)</color>', convert_color),
    (r'<bg=([^>]+)>(.*?)</bg>',      convert_bg),
    (r'<hl=([^>]+)>(.*?)</hl>',      convert_hl),
    (r'<mark>(.*?)</mark>',          convert_mark),
    (r'<size=([^>]+)>(.*?)</size>',  convert_size),
]

BLOCK_RULES = [
    (r'<center>(.*?)</center>', convert_center),
    (r'<right>(.*?)</right>',   convert_right),
    (r'<tip>(.*?)</tip>',       convert_tip),
    (r'<warn>(.*?)</warn>',     convert_warn),
]


# =============================================================
#  核心处理函数
# =============================================================

def process_content(text: str) -> tuple:
    """
    处理 Markdown 文本内容，转换所有短标签。

    返回:
        (processed_text, change_count)
    """
    original = text
    changes = 0

    # 1. 先处理块级标签（跨行匹配）
    for pattern, replacer in BLOCK_RULES:
        new_text, n = re.subn(pattern, replacer, text, flags=re.DOTALL)
        if n > 0:
            changes += n
            text = new_text

    # 2. 再处理内联标签（跨行匹配，因为标签内可能有换行）
    for pattern, replacer in INLINE_RULES:
        new_text, n = re.subn(pattern, replacer, text, flags=re.DOTALL)
        if n > 0:
            changes += n
            text = new_text

    return text, changes


def process_file(filepath: Path, dry_run: bool = False, output: Path = None) -> int:
    """
    处理单个 Markdown 文件。

    参数:
        filepath: 输入文件路径
        dry_run: 为 True 时只打印预览，不修改文件
        output: 输出文件路径（为 None 则原地修改）

    返回:
        转换次数
    """
    if not filepath.exists():
        print(f"[ERROR] 文件不存在: {filepath}")
        return 0

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"[ERROR] 读取文件失败 {filepath}: {e}")
        return 0

    processed, changes = process_content(content)

    if changes == 0:
        print(f"[SKIP] 无需转换: {filepath}")
        return 0

    print(f"[OK] {changes} 处转换: {filepath}")

    if dry_run:
        # 打印 diff 预览
        print(f"\n{'='*60}")
        print(f"预览: {filepath}")
        print(f"{'='*60}")
        # 简单显示转换后的内容
        lines_orig = content.split('\n')
        lines_new = processed.split('\n')
        for i, (old, new) in enumerate(zip(lines_orig, lines_new)):
            if old != new:
                print(f"  行 {i+1}:")
                print(f"    原: {old[:100]}")
                print(f"    新: {new[:100]}")
        print(f"{'='*60}\n")
    else:
        out_path = output if output else filepath
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(processed)
        except Exception as e:
            print(f"[ERROR] 写入文件失败 {out_path}: {e}")
            return 0
        if output:
            print(f"       → 输出到: {output}")

    return changes


def process_directory(dirpath: Path, recursive: bool = False,
                      dry_run: bool = False) -> tuple:
    """
    处理目录下的所有 Markdown 文件。

    返回:
        (file_count, total_changes)
    """
    pattern = '**/*.md' if recursive else '*.md'
    md_files = sorted(dirpath.glob(pattern))

    # 排除 _site 等构建输出目录
    md_files = [f for f in md_files if '_site' not in f.parts]

    if not md_files:
        print(f"[INFO] 未找到 .md 文件: {dirpath}")
        return 0, 0

    total_changes = 0
    for f in md_files:
        changes = process_file(f, dry_run=dry_run)
        total_changes += changes

    return len(md_files), total_changes


# =============================================================
#  CLI 入口
# =============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Markdown 格式化短标签处理器 - 将自定义标签转换为标准 HTML',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s post.md                 处理单个文件（原地修改）
  %(prog)s post.md -o out.md       输出到新文件
  %(prog)s _posts/                 处理目录下所有 .md 文件
  %(prog)s _posts/ -r              递归处理
  %(prog)s post.md --dry-run       预览模式，不修改文件

支持的标签:
  <b>加粗</b>  <i>斜体</i>  <u>下划线</u>  <s>删除线</s>
  <color=red>颜色</color>  <color=#3498db>蓝色</color>
  <bg=yellow>背景</bg>  <hl=red>高亮</hl>  <mark>标记</mark>
  <size=20px>字号</size>  <center>居中</center>
  <tip>提示框</tip>  <warn>警告框</warn>
        """
    )
    parser.add_argument('path', help='文件或目录路径')
    parser.add_argument('-o', '--output', help='输出文件路径（仅单文件模式）')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='递归处理子目录')
    parser.add_argument('--dry-run', action='store_true',
                        help='预览模式，不实际修改文件')

    args = parser.parse_args()
    target = Path(args.path)
    output = Path(args.output) if args.output else None

    if not target.exists():
        print(f"[ERROR] 路径不存在: {target}")
        sys.exit(1)

    if target.is_file():
        if target.suffix != '.md':
            print(f"[WARN] 文件不是 .md 格式: {target}")
        changes = process_file(target, dry_run=args.dry_run, output=output)
    elif target.is_dir():
        files, total = process_directory(target, recursive=args.recursive,
                                         dry_run=args.dry_run)
        if args.dry_run:
            print(f"\n[DRY-RUN] 共发现 {files} 个文件，{total} 处待转换")
        else:
            print(f"\n[DONE] 处理了 {files} 个文件，共 {total} 处转换")
    else:
        print(f"[ERROR] 无效路径: {target}")
        sys.exit(1)


if __name__ == '__main__':
    main()
