---
layout: page
title: 资料
icon: fas fa-bookmark
order: 5
---

<style>
  /* 资料页隐藏右侧面板 */
  #panel-wrapper { display: none !important; }
  #main .row > div:first-child { flex: 0 0 100% !important; max-width: 100% !important; }
</style>

<!-- ============================================================
     资料页 — 楼层式布局
     每层对应 _data/materials/ 下的一个 .yml 文件

     如需添加新楼层，只需在下面复制一个楼层区块，
     修改标题、图标、和数据源路径即可
   ============================================================ -->

<!-- ---------- 楼层 1：外部网站 ---------- -->
<section class="material-floor">
  <header class="floor-header">
    <h2 class="floor-title">
      <i class="fas fa-globe"></i>
      <span>外部网站</span>
    </h2>
    <span class="floor-count">共 {{ site.data.materials.waibuwangzhan.items.size }} 项</span>
  </header>
  <div class="floor-grid">
    {% for item in site.data.materials.waibuwangzhan.items %}
      <a class="floor-card floor-card-website" href="{{ item.url }}" target="_blank" rel="noopener">
        <div class="floor-card-body">
          <div class="floor-card-icon">
            <i class="{{ item.icon | default: 'fas fa-link' }}"></i>
          </div>
          <h3 class="floor-card-title">{{ item.title }}</h3>
          <p class="floor-card-desc">{{ item.description }}</p>
          <div class="floor-card-tags">
            {% for tag in item.tags %}
              <span class="floor-tag">{{ tag }}</span>
            {% endfor %}
          </div>
          <div class="floor-card-foot">
            <i class="fas fa-external-link-alt"></i>
            <span>{{ item.url | remove: 'https://' | remove: 'http://' | truncate: 36 }}</span>
          </div>
        </div>
      </a>
    {% endfor %}
  </div>
</section>

<!-- ---------- 楼层 2：资料 ---------- -->
<section class="material-floor">
  <header class="floor-header">
    <h2 class="floor-title">
      <i class="fas fa-file-alt"></i>
      <span>资料</span>
    </h2>
    <span class="floor-count">共 {{ site.data.materials.ziliao.items.size }} 项</span>
  </header>
  <div class="floor-grid">
    {% for item in site.data.materials.ziliao.items %}
      <a class="floor-card floor-card-article" href="{{ item.url }}" target="_blank" rel="noopener">
        <div class="floor-card-body">
          <div class="floor-card-top">
            <h3 class="floor-card-title">{{ item.title }}</h3>
            {% if item.status == "unread" %}
              <span class="floor-badge badge-unread">待读</span>
            {% elsif item.status == "read" %}
              <span class="floor-badge badge-read">已读</span>
            {% endif %}
          </div>
          <p class="floor-card-desc">{{ item.description }}</p>
          <div class="floor-card-tags">
            {% for tag in item.tags %}
              <span class="floor-tag">{{ tag }}</span>
            {% endfor %}
          </div>
          <div class="floor-card-foot">
            {% if item.date_added %}
              <i class="far fa-calendar-alt"></i>
              <span>{{ item.date_added }}</span>
            {% endif %}
            <span class="floor-url-hint"><i class="fas fa-external-link-alt"></i></span>
          </div>
        </div>
      </a>
    {% endfor %}
  </div>
</section>
