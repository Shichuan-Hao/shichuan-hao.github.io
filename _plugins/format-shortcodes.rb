# frozen_string_literal: true

# ============================================================
#  Markdown 格式化短标签插件
#  为 Markdown 提供简洁的格式化标签，自动转换为 HTML
#
#  用法：
#    <b>加粗文字</b>
#    <i>斜体文字</i>
#    <u>下划线</u>
#    <s>删除线</s>
#    <color=red>红色文字</color>
#    <color=#3498db>蓝色文字（十六进制）</color>
#    <bg=yellow>黄色背景</bg>
#    <hl=red>高亮文字（加粗+颜色）</hl>
#    <mark>高亮标记（黄色底）</mark>
#    <code>行内代码</code>
#    <tip>提示框</tip>
#    <warn>警告框</warn>
#    <info>信息框</info>
#    <center>居中文字</center>
#    <right>右对齐文字</right>
#    <size=20px>指定字号</size>
# ============================================================

# --------------------------------------------------
#  核心转换函数（用 gsub 而非 gsub! 避免 FrozenError）
# --------------------------------------------------
def convert_shortcodes(input)
  text = input.dup   # 复制一份，避免操作 frozen string

  # <b>...</b> 加粗
  text = text.gsub(%r{<b>(.*?)</b>}m, '<b>\1</b>')

  # <i>...</i> 斜体
  text = text.gsub(%r{<i>(.*?)</i>}m, '<i>\1</i>')

  # <u>...</u> 下划线
  text = text.gsub(%r{<u>(.*?)</u>}m, '<u>\1</u>')

  # <s>...</s> 删除线
  text = text.gsub(%r{<s>(.*?)</s>}m, '<s>\1</s>')

  # <color=COLOR>...</color> 文字颜色
  text = text.gsub(%r{<color=([^>]+)>(.*?)</color>}m) do
    color = ::Regexp.last_match(1).strip
    inner = ::Regexp.last_match(2)
    "<span style=\"color:#{color};\">#{inner}</span>"
  end

  # <bg=COLOR>...</bg> 背景颜色
  text = text.gsub(%r{<bg=([^>]+)>(.*?)</bg>}m) do
    color = ::Regexp.last_match(1).strip
    inner = ::Regexp.last_match(2)
    "<span style=\"background-color:#{color};padding:0 4px;\">#{inner}</span>"
  end

  # <hl=COLOR>...</hl> 高亮（加粗 + 颜色）
  text = text.gsub(%r{<hl=([^>]+)>(.*?)</hl>}m) do
    color = ::Regexp.last_match(1).strip
    inner = ::Regexp.last_match(2)
    "<span style=\"color:#{color};font-weight:bold;\">#{inner}</span>"
  end

  # <mark>...</mark> 荧光笔高亮
  text = text.gsub(%r{<mark>(.*?)</mark>}m,
                   '<mark style="background-color:#fff59d;padding:0 2px;">\1</mark>')

  # <code>...</code> 行内代码
  text = text.gsub(%r{<code>(.*?)</code>}m,
                   '<code style="background:#f4f4f4;color:#e74c3c;padding:1px 5px;border-radius:3px;">\1</code>')

  # <size=N>...</size> 指定字号
  text = text.gsub(%r{<size=([^>]+)>(.*?)</size>}m) do
    sz    = ::Regexp.last_match(1).strip
    inner = ::Regexp.last_match(2)
    "<span style=\"font-size:#{sz};\">#{inner}</span>"
  end

  # <center>...</center> 居中
  text = text.gsub(%r{<center>(.*?)</center>}m,
                   '<div style="text-align:center;">\1</div>')

  # <right>...</right> 右对齐
  text = text.gsub(%r{<right>(.*?)</right>}m,
                   '<div style="text-align:right;">\1</div>')

  # <tip>...</tip> 提示框
  text = text.gsub(%r{<tip>(.*?)</tip>}m) do
    inner = ::Regexp.last_match(1)
    <<~HTML
      <blockquote style="background:#e8f5e9;border-left:4px solid #4caf50;padding:10px 16px;margin:12px 0;border-radius:4px;">
      💡 <b>提示：</b>#{inner}
      </blockquote>
    HTML
  end

  # <warn>...</warn> 警告框
  text = text.gsub(%r{<warn>(.*?)</warn>}m) do
    inner = ::Regexp.last_match(1)
    <<~HTML
      <blockquote style="background:#fff3e0;border-left:4px solid #ff9800;padding:10px 16px;margin:12px 0;border-radius:4px;">
      ⚠️ <b>警告：</b>#{inner}
      </blockquote>
    HTML
  end

  # <info>...</info> 信息框
  text = text.gsub(%r{<info>(.*?)</info>}m) do
    inner = ::Regexp.last_match(1)
    <<~HTML
      <blockquote style="background:#e3f2fd;border-left:4px solid #2196f3;padding:10px 16px;margin:12px 0;border-radius:4px;">
      ℹ️ <b>信息：</b>#{inner}
      </blockquote>
    HTML
  end

  text
end

# --------------------------------------------------
#  注册 Hook：处理 posts / documents
# --------------------------------------------------
Jekyll::Hooks.register :documents, :pre_render do |doc|
  next unless doc.respond_to?(:content) && doc.content.is_a?(String)
  doc.content = convert_shortcodes(doc.content)
end

# --------------------------------------------------
#  注册 Hook：处理 pages
# --------------------------------------------------
Jekyll::Hooks.register :pages, :pre_render do |page|
  next unless page.respond_to?(:content) && page.content.is_a?(String)
  page.content = convert_shortcodes(page.content)
end
