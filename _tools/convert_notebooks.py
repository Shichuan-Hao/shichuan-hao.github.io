#!/usr/bin/env python3
"""Convert 6 Dify/DeepSeek iPynb files to Jekyll markdown blog posts."""

import json
import os

NOTEBOOKS = [
    {
        "src": r"f:\happymaya\web\shichuanhao.github.io\_posts\aigc\1. window&Dify&xinference环境部署与安装.ipynb",
        "dst": r"f:\happymaya\web\shichuanhao.github.io\_posts\aigc\low-code-dify-coze-12\2025-01-01-dify-xinference-setup.md",
        "title": "Ch1 Window & Dify & Xinference 环境部署与安装",
        "description": "低代码平台发展介绍、Dify安装部署（Docker方式）、Xinference介绍与部署、Dify与Xinference全链路打通，构建第一个聊天机器人。",
        "date": "2025-01-01",
        "tags": ["Dify", "Xinference", "低代码", "环境部署"]
    },
    {
        "src": r"f:\happymaya\web\shichuanhao.github.io\_posts\aigc\Ch2 源码部署Dify构建RAG_补充版 .ipynb",
        "dst": r"f:\happymaya\web\shichuanhao.github.io\_posts\aigc\low-code-dify-coze-12\2025-01-08-dify-source-deploy-rag.md",
        "title": "Ch2 源码部署Dify构建RAG",
        "description": "服务器租赁、CUDA安装、Docker安装、源码部署Dify、Xinference细化安装、知识库构建与RAG应用实战。",
        "date": "2025-01-08",
        "tags": ["Dify", "RAG", "源码部署", "Xinference", "知识库"]
    },
    {
        "src": r"f:\happymaya\web\shichuanhao.github.io\_posts\aigc\3. window环境deepseek+Dify本地部署.ipynb",
        "dst": r"f:\happymaya\web\shichuanhao.github.io\_posts\aigc\low-code-dify-coze-12\2025-02-11-deepseek-dify-local-deploy.md",
        "title": "Ch3 Window环境 DeepSeek + Dify 本地部署",
        "description": "Ollama安装与使用、DeepSeek模型下载、Dify Docker部署、Xinference安装、模型横向对比、Postman API调用测试。",
        "date": "2025-02-11",
        "tags": ["DeepSeek", "Dify", "Ollama", "Xinference", "API"]
    },
    {
        "src": r"f:\happymaya\web\shichuanhao.github.io\_posts\aigc\4. Dify+deepseek构建微信客服工作流.ipynb",
        "dst": r"f:\happymaya\web\shichuanhao.github.io\_posts\aigc\low-code-dify-coze-12\2025-02-17-dify-wechat-workflow.md",
        "title": "Ch4 Dify + DeepSeek 构建微信客服工作流",
        "description": "聊天助手/Agent/工作流概念详解、Dify节点介绍、Agent构建、知识库+RAG对话流、dify-on-wechat微信对接实战。",
        "date": "2025-02-17",
        "tags": ["Dify", "DeepSeek", "工作流", "微信", "Agent"]
    },
    {
        "src": r"f:\happymaya\web\shichuanhao.github.io\_posts\aigc\5. Dify+deepseek+xunfei构建语音客服工作流.ipynb",
        "dst": r"f:\happymaya\web\shichuanhao.github.io\_posts\aigc\low-code-dify-coze-12\2025-02-20-dify-voice-workflow.md",
        "title": "Ch5 Dify + DeepSeek + 讯飞 构建语音客服工作流",
        "description": "语音对话构建、讯飞语音对接、定时触发Dify工作流（FastAPI+Schedule）、Dify使用技巧（变量/代码块/并行模式）。",
        "date": "2025-02-20",
        "tags": ["Dify", "DeepSeek", "讯飞", "语音客服", "定时任务"]
    },
    {
        "src": r"f:\happymaya\web\shichuanhao.github.io\_posts\aigc\6. Dify企业微信对话与人工客服转接.ipynb",
        "dst": r"f:\happymaya\web\shichuanhao.github.io\_posts\aigc\low-code-dify-coze-12\2025-02-25-dify-wecom-human-transfer.md",
        "title": "Ch6 Dify企业微信对话与人工客服转接",
        "description": "人工客服转接工作流、企业微信配置（corpid/secret/access_token）、域名备案与SSL、企微/个微双通道部署测试。",
        "date": "2025-02-25",
        "tags": ["Dify", "企业微信", "人工客服", "access_token"]
    },
]


def extract_markdown_from_notebook(notebook_path: str) -> str:
    """Extract all markdown cells from a Jupyter notebook and concatenate them."""
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    lines = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue
        source = cell.get("source", [])
        if isinstance(source, list):
            text = "".join(source)
        else:
            text = str(source)

        # Remove the centered title like "<center>...</center>" from first cell
        # We'll use front matter for the title instead
        text = text.strip()
        if text.startswith("# <center>") and text.endswith("</center>"):
            # Skip the centered title - use front matter title
            continue

        if text:
            lines.append(text)

    return "\n\n".join(lines)


def clean_content(content: str) -> str:
    """Minimal cleanup of markdown content."""
    # Fix any oddly broken HTML image tags from the notebook
    content = content.replace('" width=100%></div>', '" width="100%"></div>')
    # Replace the broken json block in notebook 6
    content = content.replace(
        '"# 从阿里云镜像仓库拉取(国内" width=100%></div>',
        '-header  Content-Type:application/json'
    )
    return content


def build_front_matter(cfg: dict) -> str:
    """Build YAML front matter string."""
    tags_str = "[" + ", ".join(cfg["tags"]) + "]"
    return f"""---
title: {cfg['title']}
description: {cfg['description']}
author: hsc
date: {cfg['date']} 23:27:00 +0800
categories: [AI Agent, 低代码平台 coze & dify]
tags: {tags_str}
math: true
mermaid: true
---

"""


def main():
    for cfg in NOTEBOOKS:
        print(f"Processing: {cfg['title']}")
        md_content = extract_markdown_from_notebook(cfg["src"])
        md_content = clean_content(md_content)
        fm = build_front_matter(cfg)
        full_content = fm + md_content + "\n"

        os.makedirs(os.path.dirname(cfg["dst"]), exist_ok=True)
        with open(cfg["dst"], "w", encoding="utf-8") as f:
            f.write(full_content)

        # Count lines and chars
        lines = full_content.count("\n")
        print(f"  -> {cfg['dst'].split(chr(92))[-1]} ({lines} lines, {len(full_content)} chars)")

    print("\nAll 6 notebooks converted successfully!")


if __name__ == "__main__":
    main()
