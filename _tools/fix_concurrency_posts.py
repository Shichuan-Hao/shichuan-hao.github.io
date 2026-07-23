#!/usr/bin/env python3
"""
批量修复 _posts/concurrency/ 下 Markdown 文件的格式问题:
1. 标题与正文粘连 → 分开
2. 连续的内联代码行 → 合并为一个代码块
3. 删除课程笔记残留元信息
"""
import os
import re

POSTS_DIR = os.path.join(os.path.dirname(__file__), '..', '_posts', 'concurrency')


def is_front_matter_delimiter(line):
    return line.strip() == '---'


def is_heading(line):
    return bool(re.match(r'^#{1,6}\s', line))


def is_list_item(line):
    return bool(re.match(r'^[\-\*]\s', line.strip())) or bool(re.match(r'^\d+[\.\、\)]\s', line.strip()))


def is_blank(line):
    return not line.strip()


def count_inline_code_numbers(line):
    """统计行内疑似代码行号的模式数量。
    代码行号模式: 数字后面紧跟一个字母/特殊符号，看起来像代码行的开头。
    例如: "23 private int x" 中的 "23 private"
    """
    return len(re.findall(r'(?:^|\s)(\d{1,3})\s+[a-zA-Z@/#<"\']', line))


def looks_like_code(line):
    """判断一行是否可能是内联代码（基于行号模式密度）"""
    if not line.strip():
        return False
    # 至少 2 个代码行号模式
    count = count_inline_code_numbers(line)
    # 如果整行都是短模式（数字+空格+短代码），很可能就是内联代码
    return count >= 2


def fix_heading_merge(content):
    """修复标题与中文正文粘连:
    '### 1. 线程池简介线程池(Thread Pool)是...'
    → '### 1. 线程池简介\n\n线程池(Thread Pool)是...'
    """
    lines = content.split('\n')
    result = []
    fm_closed = False
    fm_delimiters = 0

    for line in lines:
        if is_front_matter_delimiter(line):
            fm_delimiters += 1
            result.append(line)
            continue
        
        if fm_delimiters < 2:
            result.append(line)
            continue
        
        # 过了 front matter，处理正文
        m = re.match(r'^(#{1,6})\s+(.+)$', line)
        if not m:
            result.append(line)
            continue
        
        hashes = m.group(1)
        rest = m.group(2)
        
        # 查找第一个中文句号、逗号、分号、冒号后的位置来切分
        # 标题通常以"概念"、"简介"、"介绍"等词结束
        split_patterns = [
            r'(.{3,}?[概简介绍析明解述类型式理点源因果别法策制型用义征])([\u4e00-\u9fff].{10,})',
        ]
        
        split_done = False
        for pat in split_patterns:
            sm = re.match(pat, rest)
            if sm:
                title = sm.group(1)
                content_text = sm.group(2)
                result.append(f"{hashes} {title}")
                result.append("")
                result.append(content_text)
                split_done = True
                break
        
        if not split_done:
            result.append(line)
    
    return '\n'.join(lines)


def wrap_code_blocks(content):
    """将连续的内联代码行合并为一个代码块"""
    lines = content.split('\n')
    result = []
    fm_delimiters = 0
    code_buffer = []
    
    for i, line in enumerate(lines):
        if is_front_matter_delimiter(line):
            fm_delimiters += 1
            result.append(line)
            continue
        
        if fm_delimiters < 2:
            result.append(line)
            continue
        
        stripped = line.strip()
        
        # 不处理已有的代码块标记
        if stripped.startswith('```'):
            if code_buffer:
                result.append('')
                result.append('```java')
                for cl in code_buffer:
                    result.append(cl)
                result.append('```')
                result.append('')
                code_buffer = []
            result.append(line)
            continue
        
        # 在代码块内的行直接添加
        in_existing_fence = False
        fence_count = 0
        for rl in result:
            if rl.strip().startswith('```'):
                fence_count += 1
        in_existing_fence = (fence_count % 2 == 1)
        if in_existing_fence:
            result.append(line)
            continue
        
        # 跳过空行、标题、列表
        if is_blank(line) or is_heading(line) or is_list_item(line):
            if code_buffer:
                result.append('')
                result.append('```java')
                for cl in code_buffer:
                    result.append(cl)
                result.append('```')
                result.append('')
                code_buffer = []
            result.append(line)
            continue
        
        # 检测是否为内联代码
        if looks_like_code(line):
            code_buffer.append(line)
            continue
        
        # 不是代码，刷出缓冲区
        if code_buffer:
            result.append('')
            result.append('```java')
            for cl in code_buffer:
                result.append(cl)
            result.append('```')
            result.append('')
            code_buffer = []
        
        result.append(line)
    
    # 文件末尾
    if code_buffer:
        result.append('')
        result.append('```java')
        for cl in code_buffer:
            result.append(cl)
        result.append('```')
    
    return '\n'.join(result)


def clean_course_metadata(content):
    """删除课程笔记残留元信息行（正文开头的 '主讲老师:...'、'=======' 等）"""
    lines = content.split('\n')
    result = []
    fm_delimiters = 0
    past_fm = False
    
    for line in lines:
        if is_front_matter_delimiter(line):
            fm_delimiters += 1
            result.append(line)
            if fm_delimiters == 2:
                past_fm = True
                # 跳过 front matter 后的第一行如果是元信息
            continue
        
        if fm_delimiters < 2:
            result.append(line)
            continue
        
        stripped = line.strip()
        
        if past_fm:
            # Front Matter 后紧跟着的元信息行
            if stripped.startswith('主讲老师:') or stripped.startswith('主讲老师：'):
                continue
            if re.match(r'^={3,}', stripped):
                continue
            if stripped.startswith('有道笔记'):
                continue
            if stripped.startswith('笔记地址:'):
                continue
        
        result.append(line)
    
    return '\n'.join(result)


def process_file(filepath):
    """处理单个文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 保持原始备份
    original = content
    
    content = fix_heading_merge(content)
    content = wrap_code_blocks(content)
    content = clean_course_metadata(content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    files = sorted([
        f for f in os.listdir(POSTS_DIR) 
        if f.endswith('.md')
    ])
    
    print(f"找到 {len(files)} 个文件")
    fixed_count = 0
    
    for fname in files:
        fpath = os.path.join(POSTS_DIR, fname)
        changed = process_file(fpath)
        status = "已修复" if changed else "无需修改"
        print(f"  {fname}: {status}")
        if changed:
            fixed_count += 1
    
    print(f"\n共修复 {fixed_count}/{len(files)} 个文件")


if __name__ == '__main__':
    main()
