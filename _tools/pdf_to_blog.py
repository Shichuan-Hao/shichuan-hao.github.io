"""批量将PDF课程笔记转换为Jekyll博客文章"""
import pdfplumber
import os
import re
import unicodedata
from datetime import datetime, timedelta

# ============ 配置 ============
PDF_ROOT = r"f:\happymaya\web\shichuanhao.github.io\资料"
POSTS_ROOT = r"f:\happymaya\web\shichuanhao.github.io\_posts"
AUTHOR = "hsc"

# 专题目录到分类和标签的映射
CATEGORY_MAP = {
    "一、性能调优专题": {
        "categories": ["Java 后端", "性能调优"],
        "tags": ["性能调优", "JVM", "MySQL", "Tomcat", "GC"],
        "slug_dir": "performance-tuning"
    },
    "二、框架源码专题": {
        "categories": ["Java 后端", "框架源码"],
        "tags": ["Spring", "MyBatis", "源码分析", "框架"],
        "slug_dir": "framework-source"
    },
    "三、并发编程专题": {
        "categories": ["Java 后端", "并发编程"],
        "tags": ["并发编程", "多线程", "JUC", "AQS", "线程池"],
        "slug_dir": "concurrency"
    },
    "四、分布式专题": {
        "categories": ["Java 后端", "分布式"],
        "tags": ["分布式", "Redis", "Kafka", "RocketMQ", "Netty", "ElasticSearch", "ShardingSphere"],
        "slug_dir": "distributed"
    },
    "五、微服务专题": {
        "categories": ["Java 后端", "微服务"],
        "tags": ["微服务", "SpringCloud", "Nacos", "Sentinel", "Docker", "K8s"],
        "slug_dir": "microservices"
    },
    "六、项目实战专题": {
        "categories": ["Java 后端", "项目实战"],
        "tags": ["项目实战", "云课堂", "电商"],
        "slug_dir": "project-practice"
    }
}

# 起始日期，文章将按顺序分配日期
START_DATE = datetime(2026, 6, 1)


def sanitize_filename(text, max_len=60):
    """生成安全的文件名（英文slug）"""
    text = text.strip()
    # 保留中文、字母、数字、空格、连字符
    text = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', text)
    text = re.sub(r'\s+', '-', text)
    if len(text) > max_len:
        text = text[:max_len].rsplit('-', 1)[0]
    return text.strip('-') or "untitled"


def generate_slug(name, topic_name):
    """根据文件名和专题生成英文slug"""
    # 提取数字前缀
    num_match = re.match(r'(\d+)', name)
    num_prefix = f"{int(num_match.group(1)):02d}-" if num_match else ""

    # 提取核心标题
    clean = re.sub(r'[\d、\s]+', ' ', name)
    clean = re.sub(r'[《》""""]', '', clean)
    clean = re.sub(r'（[^）]*）', '', clean)
    clean = re.sub(r'\([^)]*\)', '', clean)

    # 简化中文标题
    slug_map = CATEGORY_MAP.get(topic_name, {}).get("slug_dir", "other")
    return f"{num_prefix}{slug_map}-{sanitize_filename(clean, 50)}"


def extract_title_from_pdf(pdf_path):
    """从PDF路径和内容提取标题"""
    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    # 清理文件名中的编号前缀
    title = re.sub(r'^\d+[、.]?\s*', '', filename)
    return title


def clean_text(text):
    """清理提取的文本"""
    if not text:
        return ""
    # 规范化Unicode
    text = unicodedata.normalize('NFKC', text)
    # 移除多余空行
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    # 移除行尾空格
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
    return text.strip()


def get_topic_name(pdf_path):
    """从PDF路径提取专题名"""
    rel = os.path.relpath(pdf_path, PDF_ROOT)
    parts = rel.split(os.sep)
    for part in parts:
        if part in CATEGORY_MAP:
            return part
    return "其他"


def generate_tags(topic_name, pdf_filename):
    """根据专题和文件名生成标签"""
    config = CATEGORY_MAP.get(topic_name, {})
    base_tags = list(config.get("tags", []))

    # 从文件名提取关键词作为额外标签
    title_lower = pdf_filename.lower()
    keyword_map = {
        "jvm": ["JVM"],
        "gc": ["GC"],
        "mysql": ["MySQL"],
        "redis": ["Redis"],
        "spring": ["Spring"],
        "mybatis": ["MyBatis"],
        "netty": ["Netty"],
        "kafka": ["Kafka"],
        "rocketmq": ["RocketMQ"],
        "elasticsearch": ["ElasticSearch", "ES"],
        "docker": ["Docker"],
        "nacos": ["Nacos"],
        "tomcat": ["Tomcat"],
        "sharding": ["ShardingSphere"],
        "sentinel": ["Sentinel"],
        "并发": ["并发编程"],
        "线程": ["多线程"],
        "锁": ["锁"],
        "源码": ["源码分析"],
        "调优": ["性能调优"],
        "实战": ["实战"],
        "分布式": ["分布式"],
        "集群": ["集群"],
        "架构": ["架构"],
        "微服务": ["微服务"],
    }
    extra_tags = set()
    for key, tags in keyword_map.items():
        if key in title_lower:
            extra_tags.update(tags)

    # 合并去重，保持base_tags顺序
    all_tags = list(base_tags)
    for t in extra_tags:
        if t not in all_tags:
            all_tags.append(t)
    return all_tags


def convert_pdf_to_post(pdf_path, date, post_index):
    """将单个PDF转换为博客文章"""
    topic_name = get_topic_name(pdf_path)
    if topic_name not in CATEGORY_MAP:
        print(f"  [跳过] 未识别的专题: {topic_name}")
        return None

    config = CATEGORY_MAP[topic_name]
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    title = extract_title_from_pdf(pdf_path)
    slug = generate_slug(pdf_name, topic_name)
    date_str = date.strftime("%Y-%m-%d %H:%M:%S +0800")
    filename_date = date.strftime("%Y-%m-%d")
    tags = generate_tags(topic_name, pdf_name)

    # 提取PDF全文
    full_text = ""
    page_count = 0
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n\n"
    except Exception as e:
        print(f"  [错误] 提取失败: {e}")
        return None

    if not full_text.strip():
        print(f"  [警告] PDF内容为空")
        return None

    full_text = clean_text(full_text)

    # 生成描述（取前200字符）
    description = full_text[:200].replace('\n', ' ').strip()
    if len(description) >= 200:
        description = description[:197] + "..."

    # 生成Markdown内容
    md_content = f"""---
title: "{title}"
description: "{description}"
author: {AUTHOR}
date: {date_str}
categories: {config['categories']}
tags: {tags}
toc: true
---

> 本文整理自《{topic_name}》课程笔记，共 {page_count} 页。

{full_text}
"""

    # 确定输出路径
    output_dir = os.path.join(POSTS_ROOT, config["slug_dir"])
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{filename_date}-{slug}.md"
    output_path = os.path.join(output_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return output_path


def main():
    print("=" * 60)
    print("PDF → 博客 批量转换工具")
    print("=" * 60)

    # 收集所有PDF文件
    all_pdfs = []
    for root, dirs, files in os.walk(PDF_ROOT):
        for f in files:
            if f.lower().endswith('.pdf'):
                all_pdfs.append(os.path.join(root, f))

    # 按路径排序（保证编号顺序）
    all_pdfs.sort()

    print(f"\n找到 {len(all_pdfs)} 个PDF文件\n")

    # 按专题分组统计
    topic_counts = {}
    for p in all_pdfs:
        tn = get_topic_name(p)
        topic_counts[tn] = topic_counts.get(tn, 0) + 1

    print("各专题文件数：")
    for tn, count in topic_counts.items():
        print(f"  {tn}: {count} 个")
    print()

    # 逐个转换
    success_count = 0
    fail_count = 0
    current_date = START_DATE

    for i, pdf_path in enumerate(all_pdfs):
        rel_path = os.path.relpath(pdf_path, PDF_ROOT)
        print(f"[{i+1}/{len(all_pdfs)}] {rel_path[:80]}")

        result = convert_pdf_to_post(pdf_path, current_date, i)
        if result:
            print(f"  → {os.path.relpath(result, POSTS_ROOT)}")
            success_count += 1
        else:
            fail_count += 1

        # 每篇文章间隔1天
        current_date += timedelta(days=1)

    print(f"\n{'=' * 60}")
    print(f"转换完成！成功: {success_count}，失败: {fail_count}")
    print(f"文章已保存到: {POSTS_ROOT}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
