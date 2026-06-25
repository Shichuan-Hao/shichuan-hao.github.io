# frozen_string_literal: true

module Jekyll
  # 为 blog-list 布局自动生成第 2 页起的分页页面
  class BlogPaginator < Generator
    safe true
    priority :low

    def generate(site)
      # 从 tabs 集合中找到使用 blog-list 布局的页面
      blog_page = site.collections['tabs']&.docs&.find { |doc| doc.data['layout'] == 'blog-list' }
      return unless blog_page

      per_page = 10
      all_posts = site.posts.docs.sort_by(&:date).reverse
      total_pages = (all_posts.size + per_page - 1) / per_page
      return if total_pages <= 1

      # 去掉开头的 / 得到相对路径，如 /blog/ -> blog
      blog_dir = blog_page.url.chomp('/').sub(%r{/index\.html$}, '').sub(%r{^/}, '')

      (2..total_pages).each do |page_num|
        dir = File.join(blog_dir, 'page', page_num.to_s)
        p = PageWithoutAFile.new(site, site.source, dir, 'index.html')
        p.data.merge!(
          'layout'           => 'blog-list',
          'blog_page_num'    => page_num,
          'blog_total_pages' => total_pages,
          'per_page'         => per_page,
          'title'            => "文章 - 第 #{page_num} 页",
          'sitemap'          => false
        )
        p.content = ''
        site.pages << p
      end
    end
  end
end
