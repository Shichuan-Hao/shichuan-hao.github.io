"""抽取各专题1-2个PDF的前5页文本，评估内容质量"""
import pdfplumber
import os

samples = [
    # 性能调优
    r"f:\happymaya\web\shichuanhao.github.io\资料\一、性能调优专题\11、JDK17新特性梳理\十一、JDK17新特性梳理.pdf",
    r"f:\happymaya\web\shichuanhao.github.io\资料\一、性能调优专题\1、全面理解JVM虚拟机\1、全面理解JVM虚拟机（更新）.pdf",
    # 框架源码
    r"f:\happymaya\web\shichuanhao.github.io\资料\二、框架源码专题\01-Spring源码整体架构解析及手写SpringIOC-AOP-周瑜\01-spring源码整体架构解析及手写SpringIOC-AOP.pdf",
    # 并发编程
    r"f:\happymaya\web\shichuanhao.github.io\资料\三、并发编程专题\1-从0开始深入理解并发、线程与等待通知机制-fox\1、从0开始深入理解并发、线程与等待通知机制.pdf",
    # 分布式
    r"f:\happymaya\web\shichuanhao.github.io\资料\四、分布式专题\1、Redis核心数据结构与高性能原理-诸葛\1、Redis核心数据结构与高性能原理.pdf",
    # 微服务
    r"f:\happymaya\web\shichuanhao.github.io\资料\五、微服务专题\01-微服务入门&Nacos实战与源码分析-诸葛\01-微服务入门&Nacos实战与源码分析.pdf",
    # 项目实战
    r"f:\happymaya\web\shichuanhao.github.io\资料\六、项目实战专题\01-云课堂项目-页面功能-微服务划分以及环境搭建-诸葛\01-云课堂项目-页面功能-微服务划分以及环境搭建.pdf",
]

output_path = r"f:\happymaya\web\shichuanhao.github.io\temp_course_output.txt"

with open(output_path, "w", encoding="utf-8") as out:
    for pdf_path in samples:
        if not os.path.exists(pdf_path):
            out.write(f"\n{'='*60}\n[跳过] 文件不存在: {pdf_path}\n")
            continue

        out.write(f"\n{'='*60}\n")
        out.write(f"文件: {os.path.basename(pdf_path)}\n")
        out.write(f"路径: {pdf_path}\n")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                total = len(pdf.pages)
                out.write(f"总页数: {total}\n")
                out.write(f"\n--- 前5页内容预览 ---\n")

                for i, page in enumerate(pdf.pages[:5]):
                    text = page.extract_text()
                    out.write(f"\n[第 {i+1} 页]\n")
                    if text:
                        # 只取前1000字符
                        out.write(text[:1000])
                        if len(text) > 1000:
                            out.write("\n...(截断，页内总字符数: {})".format(len(text)))
                    else:
                        out.write("(空白页或无文本)")
                    out.write("\n")
        except Exception as e:
            out.write(f"解析失败: {e}\n")

print(f"样本提取完成，结果写入: {output_path}")
