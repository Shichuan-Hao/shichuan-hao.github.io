---
# the default layout is 'page'
icon: fas fa-info-circle
order: 4
---

<style>
.profile-card:hover img {
  transform: scale(1.1);
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.8);
}
.profile-card {
  position: relative;
}
.profile-card::after {
  content: '✨';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 0;
  transition: all 0.3s ease;
  pointer-events: none;
}
.profile-card:hover::after {
  font-size: 40px;
  animation: sparkle 1s ease-in-out infinite;
}
@keyframes sparkle {
  0%, 100% { opacity: 0; transform: translate(-50%, -50%) scale(0.5); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.2); }
}
</style>

## 👋 你好

欢迎来到 **字节漫步**！很高兴认识你~

---

## 🎯 关于我

<div style="display: flex; justify-content: center; align-items: center; gap: 40px; margin: 30px 0; padding: 30px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 12px;">
  <div class="profile-card">
    <img src="/assets/img/avatar/me.jpg" alt="我的照片" class="rounded-circle" style="width: 150px; height: 150px; object-fit: cover; border: 4px solid #6c757d; transition: transform 0.3s ease;">
    <div class="stars"></div>
  </div>
  <div style="display: flex; flex-direction: column; gap: 15px;">
    <div style="background: white; padding: 15px 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: transform 0.3s ease;" onmouseover="this.style.transform='translateX(10px)'" onmouseout="this.style.transform='translateX(0)'">
      <strong style="color: #e67e22; font-size: 16px;">☕ Java 后端工程师</strong>
      <div style="font-size: 13px; color: #666; margin-top: 6px;">Spring Boot / Spring Cloud / MySQL / Redis</div>
    </div>
    <div style="background: white; padding: 15px 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: transform 0.3s ease;" onmouseover="this.style.transform='translateX(10px)'" onmouseout="this.style.transform='translateX(0)'">
      <strong style="color: #9b59b6; font-size: 16px;">🤖 AI Agent 全栈开发者</strong>
      <div style="font-size: 13px; color: #666; margin-top: 6px;">LangChain / RAG / 大模型 API / Vue/React</div>
    </div>
  </div>
</div>

### 技术历程

> 🚀 从传统后端开发到 AI Agent 赛道，持续探索技术的边界

- 🔭 **后端开发**：深耕 Java 技术栈，熟悉微服务架构、分布式系统
- 🌱 **AI 转型**：正在学习大模型应用、Agent 架构设计、RAG 检索增强
- 💡 **全栈探索**：结合后端能力与 AI 前沿，构建智能化应用

---

## 🛠️ 技术栈

### 后端技术
```
Java  •  Spring Boot  •  Spring Cloud  •  MySQL  •  Redis  •  RabbitMQ
```

### AI 相关
```
LangChain  •  RAG  •  Embedding  •  Vector DB  •  Prompt Engineering
```

### 前端技术
```
Vue.js  •  React  •  HTML/CSS/JavaScript
```

---

## 📬 联系我

如果你对以下话题感兴趣，欢迎来找我交流：

- 💻 Java 后端开发经验
- 🤖 AI Agent 应用开发
- 📚 技术学习与成长
- ☕ 或者只是单纯想聊聊天

<div style="display: flex; gap: 15px; margin-top: 15px;">
  <a href="https://github.com/shichuanhao" style="text-decoration: none;">
    <button style="background: #24292e; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 14px;">📦 GitHub</button>
  </a>
  <a href="mailto:haoshichuan@foxmail.com" style="text-decoration: none;">
    <button style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 14px;">📧 发送邮件</button>
  </a>
</div>

---

## 📝 博客内容

这个博客记录我的技术学习和成长历程：

1. **Java 后端** - Spring Boot 实战、数据库优化、架构设计
2. **AI Agent** - 大模型应用、RAG 实践、Agent 开发心得
3. **问题解决** - 开发中遇到的问题及解决方案
4. **学习笔记** - 新技术的学习记录与总结

---

> 🌟 "技术之路，道阻且长，行则将至。" 
> {: .prompt-info }

感谢你的来访，希望我的分享能对你有所帮助！
