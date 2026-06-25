---
layout: page
title: 项目
icon: fas fa-rocket
order: 2
---

<style>
  /* 项目页隐藏右侧面板 */
  #panel-wrapper { display: none !important; }
  #main .row > div:first-child { flex: 0 0 100% !important; max-width: 100% !important; }
</style>

<!-- ============================================================
     项目页
     数据源：_data/projects.yml
   ============================================================ -->

<section class="material-floor">
  <header class="floor-header">
    <h2 class="floor-title">
      <i class="fas fa-rocket"></i>
      <span>项目列表</span>
    </h2>
    <span class="floor-count">共 {{ site.data.projects.items.size }} 项</span>
  </header>

  <div class="floor-grid">
    {% for item in site.data.projects.items %}
      <div class="floor-card floor-card-article">
        <div class="floor-card-body">
          <div class="floor-card-top">
            <h3 class="floor-card-title">{{ item.title }}</h3>
            {% if item.status == "开发中" %}
              <span class="floor-badge" style="background: #fef3c7; color: #b45309;">🛠 开发中</span>
            {% elsif item.status == "已完成" %}
              <span class="floor-badge" style="background: #d1fae5; color: #065f46;">✅ 已完成</span>
            {% elsif item.status == "规划中" %}
              <span class="floor-badge" style="background: #e0e7ff; color: #3730a3;">📋 规划中</span>
            {% endif %}
          </div>
          <p class="floor-card-desc">{{ item.description }}</p>
          <div class="floor-card-tags">
            {% for tag in item.tech %}
              <span class="floor-tag">{{ tag }}</span>
            {% endfor %}
          </div>
          <div class="floor-card-foot">
            {% if item.url and item.url != "#" %}
              <a href="{{ item.url }}" target="_blank" rel="noopener">
                <i class="fas fa-external-link-alt"></i> 查看项目
              </a>
            {% else %}
              <span style="color: #999;"><i class="fas fa-hourglass-half"></i> 即将上线</span>
            {% endif %}
          </div>
        </div>
      </div>
    {% endfor %}
  </div>
</section>
