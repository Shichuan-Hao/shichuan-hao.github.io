# _plugins/response-block.rb
# 1) 把 ```Response 代码块包装成 Chirpy 风格的折叠响应框
# 2) 把所有常规代码块也包装成可折叠的

Jekyll::Hooks.register [:pages, :documents], :post_render do |doc|
  next unless doc.output_ext == '.html' || doc.path.to_s.end_with?('.html')

  # ---- 第一步：处理 ```Response（裸 <pre><code>） ----
  doc.output = doc.output.gsub(
    %r{<pre><code class="language-Response">(.*?)</code></pre>}m
  ) do |_|
      content = $1
      <<~HTML.strip
        <div class="language-response highlighter-rouge">
          <details class="response-collapse">
            <summary class="code-header">
              <i class="fas fa-angle-right fold-toggle"></i>
              <span class="mac-dots"></span>
              <span data-label-text="Response"><i class="fas fa-terminal fa-fw small"></i></span>
              <button aria-label="copy" data-title-succeed="已复制！"><i class="far fa-clipboard"></i></button>
            </summary>
            <div class="highlight"><code><pre>#{content}</pre></code></div>
          </details>
        </div>
      HTML
  end

  # ---- 第二步：把剩余常规代码块也包进 <details> ----
  doc.output = doc.output.gsub(
    %r{<div class="language-(?!response)(\w+) highlighter-rouge"><div class="code-header">(.*?)</div><div class="highlight"><code>(.*?)</code></div></div>}m
  ) do |_|
      lang = $1
      header = $2
      code  = $3
      <<~HTML.strip
        <div class="language-#{lang} highlighter-rouge code-collapse">
          <details>
            <summary class="code-header">
              <i class="fas fa-angle-right fold-toggle"></i>
              <span class="mac-dots"></span>
              #{header}
            </summary>
            <div class="highlight"><code>#{code}</code></div>
          </details>
        </div>
      HTML
  end
end
