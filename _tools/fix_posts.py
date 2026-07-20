"""修复所有博客文章的 YAML front matter 和日期"""
import os
import re
import glob
import shutil
import unicodedata
from datetime import datetime, timedelta

POSTS_ROOT = r"f:\happymaya\web\shichuanhao.github.io\_posts"
BACKUP_ROOT = r"f:\happymaya\web\shichuanhao.github.io\_posts_backup"
TODAY = datetime(2026, 7, 20)  # 目标最终日期

# 各目录按原始日期排序后的文章数量
# 按日期先后顺序：performance-tuning (6/1-7/5), concurrency (7/6-7/23), 
# framework-source (7/24-8/15), microservices (8/16-8/28), distributed (8/29-10/24)
DIR_ORDER = [
    "performance-tuning",
    "concurrency", 
    "framework-source",
    "microservices",
    "distributed",
]


def strip_control_chars(text):
    """移除控制字符（保留 tab, newline, carriage return）"""
    if not text:
        return ""
    result = []
    for ch in text:
        code = ord(ch)
        if code < 0x20 and ch not in ('\t', '\n', '\r'):
            result.append(' ')
        else:
            result.append(ch)
    return ''.join(result)


def clean_description(text):
    """清理描述文本"""
    text = text[:300].replace('\n', ' ').replace('\r', ' ').strip()
    # 移除多余空格
    text = re.sub(r'\s+', ' ', text)
    # 移除首尾引号和特殊字符
    text = text.strip('"\' ')
    return text


def fix_front_matter(content):
    """修复 YAML front matter，使用 block scalar 格式"""
    # 先移除所有控制字符
    content = strip_control_chars(content)
    
    # 查找 front matter 边界
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    if not match:
        return content  # 没有 front matter，跳过
    
    fm_raw = match.group(1)
    body = match.group(2)
    
    # 提取各字段
    fm_dict = {}
    
    # title
    m = re.search(r'^title:\s*"([^"]*)"', fm_raw, re.MULTILINE)
    title = m.group(1).strip() if m else ""
    
    # description  
    m = re.search(r'^description:\s*"(.*?)"(?:\s*$)', fm_raw, re.MULTILINE | re.DOTALL)
    desc = m.group(1).strip() if m else ""
    
    # author
    m = re.search(r'^author:\s*(\S+)', fm_raw, re.MULTILINE)
    author = m.group(1).strip() if m else "hsc"
    
    # date
    m = re.search(r'^date:\s*(.+)', fm_raw, re.MULTILINE)
    date_str = m.group(1).strip() if m else ""
    
    # categories
    m = re.search(r'^categories:\s*(.+)', fm_raw, re.MULTILINE)
    categories = m.group(1).strip() if m else "[]"
    
    # tags
    m = re.search(r'^tags:\s*(.+)', fm_raw, re.MULTILINE)
    tags = m.group(1).strip() if m else "[]"
    
    # toc
    m = re.search(r'^toc:\s*(\S+)', fm_raw, re.MULTILINE)
    toc = m.group(1).strip() if m else "true"
    
    # 清理 title 中的特殊字符
    title = strip_control_chars(title)
    title = title.replace('"', "'").replace('&', 'and')
    
    # 清理 description
    desc = clean_description(strip_control_chars(desc))
    # 转义 description 中的 YAML 特殊字符
    desc = desc.replace('"', "'").replace('\\', '\\\\')
    
    # 使用 block scalar (>) 格式写 description，避免引号问题
    desc_formatted = desc.replace('\n', '\n    ')
    if desc_formatted:
        desc_formatted = '>\n    ' + desc_formatted
    else:
        desc_formatted = '""'
    
    # 重建 front matter
    new_fm = f"""---
title: "{title}"
description: {desc_formatted}
author: {author}
date: {date_str}
categories: {categories}
tags: {tags}
toc: {toc}
---"""
    
    return new_fm + "\n\n" + body


def parse_date_from_content(content):
    """从内容中提取日期"""
    m = re.search(r'^date:\s*(\d{4}-\d{2}-\d{2})', content, re.MULTILINE)
    if m:
        return datetime.strptime(m.group(1), '%Y-%m-%d')
    return None


def main():
    print("=" * 60)
    print("博客文章修复工具")
    print("=" * 60)
    
    # 备份原文件
    if not os.path.exists(BACKUP_ROOT):
        shutil.copytree(POSTS_ROOT, BACKUP_ROOT)
        print(f"已备份到: {BACKUP_ROOT}")
    else:
        print(f"备份已存在: {BACKUP_ROOT}")
    
    print()
    
    # Step 1: 收集所有文章
    all_posts = []
    for dir_name in DIR_ORDER:
        dir_path = os.path.join(POSTS_ROOT, dir_name)
        if not os.path.isdir(dir_path):
            continue
        md_files = sorted(glob.glob(os.path.join(dir_path, "*.md")))
        for f in md_files:
            all_posts.append((dir_name, f, os.path.basename(f)))
    
    print(f"找到 {len(all_posts)} 篇文章")
    
    # Step 2: 先修复所有 front matter
    print("\n修复 YAML front matter...")
    fixed_count = 0
    error_files = []
    
    for i, (dir_name, filepath, filename) in enumerate(all_posts):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                raw = f.read()
            
            # 检查是否有控制字符
            has_ctrl = any(ord(c) < 0x20 and c not in ('\t', '\n', '\r') for c in raw)
            
            if has_ctrl:
                new_content = fix_front_matter(raw)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                fixed_count += 1
                print(f"  [修复] {dir_name}/{filename}")
        except Exception as e:
            error_files.append((dir_name, filename, str(e)))
            print(f"  [错误] {dir_name}/{filename}: {e}")
    
    print(f"\n修复了 {fixed_count} 个文件的前置信息")
    
    # Step 3: 重新分配日期，所有日期 ≤ 2026-07-20
    print(f"\n重新分配日期（结束于 {TODAY.strftime('%Y-%m-%d')}）...")
    
    total = len(all_posts)
    start_date = TODAY - timedelta(days=total - 1)
    print(f"日期范围: {start_date.strftime('%Y-%m-%d')} 到 {TODAY.strftime('%Y-%m-%d')}")
    
    date_map = {}  # old_path -> (new_dir, new_filename)
    
    for i, (dir_name, filepath, filename) in enumerate(all_posts):
        new_date = start_date + timedelta(days=i)
        date_str = new_date.strftime("%Y-%m-%d")
        
        # 读取内容，替换日期
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换 front matter 中的日期
        content_new = re.sub(
            r'^date:\s*\d{4}-\d{2}-\d{2}.*$',
            f'date: {date_str} 00:00:00 +0800',
            content,
            flags=re.MULTILINE
        )
        
        # 生成新文件名
        old_basename = filename
        # 旧文件名格式: YYYY-MM-DD-slug.md
        new_basename = re.sub(r'^\d{4}-\d{2}-\d{2}', date_str, old_basename)
        new_path = os.path.join(os.path.dirname(filepath), new_basename)
        
        # 保存
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content_new)
        
        # 如果日期变了，需要重命名
        if new_basename != old_basename:
            os.rename(filepath, new_path)
        
        if (i + 1) % 20 == 0 or i == total - 1:
            print(f"  进度: {i+1}/{total} - {new_date.strftime('%Y-%m-%d')} {dir_name}/{new_basename[:60]}")
    
    # Step 4: 验证
    print(f"\n{'=' * 60}")
    print("验证结果：")
    for dir_name in DIR_ORDER:
        dir_path = os.path.join(POSTS_ROOT, dir_name)
        if os.path.isdir(dir_path):
            count = len(glob.glob(os.path.join(dir_path, "*.md")))
            print(f"  {dir_name}: {count} 篇")
    
    print(f"\n修复完成！备份保存在: {BACKUP_ROOT}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
