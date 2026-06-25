---
# the default layout is 'page'
icon: fas fa-info-circle
order: 6
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

## 👋 你好，我是郝世川

一个 **Java 后端工程师**，正在向 **AI Agent 应用开发** 领域转型。

---

## 🎯 关于我

<div style="display: flex; justify-content: center; align-items: center; gap: 40px; margin: 30px 0; padding: 30px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 12px;">
  <div class="profile-card">
    <img src="/assets/img/avatar/me.jpg" alt="我的照片" class="rounded-circle" style="width: 150px; height: 150px; object-fit: cover; border: 4px solid #6c757d; transition: transform 0.3s ease;">
  </div>
  <div style="display: flex; flex-direction: column; gap: 15px;">
    <div style="background: white; padding: 15px 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: transform 0.3s ease;" onmouseover="this.style.transform='translateX(10px)'" onmouseout="this.style.transform='translateX(0)'">
      <strong style="color: #e67e22; font-size: 16px;">☕ Java 后端工程师</strong>
      <div style="font-size: 13px; color: #666; margin-top: 6px;">Spring Boot / Spring Cloud / MySQL / Redis</div>
    </div>
    <div style="background: white; padding: 15px 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: transform 0.3s ease;" onmouseover="this.style.transform='translateX(10px)'" onmouseout="this.style.transform='translateX(0)'">
      <strong style="color: #9b59b6; font-size: 16px;">🤖 AI Agent 学习中</strong>
      <div style="font-size: 13px; color: #666; margin-top: 6px;">LangChain / RAG / Ollama / 大模型部署</div>
    </div>
  </div>
</div>

---

## 🚀 我的转型路线

> 从后端开发到 AI 应用，每一步都是积累。

| 时间 | 阶段 | 重点 |
|:------|:------|:------|
| 2021 - 2023 | **Java 后端积累** | 深耕 JVM、分布式、微服务，输出 12 篇 JVM 系列文章 |
| 2024 - 2026 | **AI Agent 探索** | 学习大模型部署、RAG、Agent 架构，输出 Ollama / vLLM / LoRA 系列实战文章 |
| 2026 下半年 | **技能深化** | 系统学习 AI Agent 开发，构建完整项目 |
| 2027 春季 | **职业跃迁** 🎯 | 计划通过春季招聘投递 AI Agent 相关岗位 |

---

## 🛠️ 技术栈

### 后端技术
```
Java  •  Spring Boot  •  Spring Cloud  •  MySQL  •  Redis  •  RabbitMQ
```

### AI 相关
```
LangChain  •  RAG  •  Embedding  •  Ollama  •  vLLM  •  Prompt Engineering
```

### 前端 & 工具
```
Vue.js  •  React  •  Linux  •  Docker  •  Git
```

---

## 📝 这个博客写什么

1. **Java 后端** — JVM 原理、分布式架构、性能调优
2. **AI Agent** — 大模型本地部署、RAG 检索增强、Agent 框架实战
3. **转型思考** — 从后端到 AI 的学习路径、面试准备、职业思考
4. **博客运营** — 写作技巧、工具分享、个人品牌建设

---

## 📬 联系我

如果你对以下话题感兴趣，欢迎交流：

- 💻 Java 后端 / JVM 调优
- 🤖 AI Agent 应用开发 / 大模型部署
- 📚 技术转型与学习路径
- ☕ 或者只是单纯想聊聊天

<div style="display: flex; gap: 15px; margin-top: 15px; flex-wrap: wrap;">
  <a href="https://github.com/shichuanhao" style="text-decoration: none;">
    <button style="background: #24292e; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 14px;">📦 GitHub</button>
  </a>
  <a href="mailto:haoshichuan@foxmail.com" style="text-decoration: none;">
    <button style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 14px;">📧 发送邮件</button>
  </a>
  <a href="/resume/" style="text-decoration: none;">
    <button style="background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; border: none; padding: 10px 24px; border-radius: 6px; cursor: pointer; font-size: 14px; box-shadow: 0 2px 8px rgba(37,99,235,0.3);">📄 查看完整简历</button>
  </a>
</div>

---

> 🌟 "技术之路，道阻且长，行则将至。每一步转型，都是新的开始。"
> {: .prompt-info }

感谢你的来访，希望我的分享能对你有所帮助！
