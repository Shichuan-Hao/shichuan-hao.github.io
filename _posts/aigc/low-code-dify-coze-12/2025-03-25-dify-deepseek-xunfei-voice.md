---
title: Dify + DeepSeek + 讯飞语音：打造AI语音客服工作流
description: 使用Dify、DeepSeek和讯飞语音构建语音客服工作流，实现语音输出、定时触发、变量配置和并行模式等高级功能。
author: hsc
date: 2025-03-25 10:00:00 +0800
categories: [AI Agent, 低代码平台, Dify]
tags: [Dify, DeepSeek, 讯飞, 语音客服, 工作流, TTS, 定时触发]
math: true
mermaid: true
---

# 背景
人们更喜欢使用语音留言：

1. **便捷性**  
   语音留言比打字更快，尤其在忙碌或不方便打字时，只需说话即可完成信息传递。在走路、开车或做其他事情时进行沟通，提升了效率。

2. **情感表达**  
   语音能更好地传递语气、情绪和情感，使沟通更生动、真实，减少文字可能带来的误解。

3. **个性化**  
   语音留言更具个人特色，能拉近沟通双方的距离，适合亲密或非正式场合。

4. **技术普及**  
   智能手机和语音识别技术的进步让语音留言变得简单易用，用户无需额外学习即可上手。

# 1.构建语音对话
## 优先构建语音输出
当前输出可以在聊天助手以及对话流中直接设置。(属于独立存在)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220110828243_a967c25b.png)
## 对接微信生态语音输出
修改根目录下/config.json文件
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220110947919_ea02cd9d.png)
```json
{
    "always_reply_voice": false,
    "channel_type": "gewechat",
    "dify_api_base": "http://localhost/v1",
    "dify_api_key": "",
    "dify_app_type": "chatbot",
    "gewechat_app_id": "",
    "gewechat_base_url": "http://192.168.110.25:2531/v2/api",
    "gewechat_callback_url": "http://192.168.110.25:9919/v2/api/callback/collect",
    "gewechat_download_url": "http://192.168.110.25:2532/download",
    "gewechat_token": "",
    "group_chat_prefix": [
        "@bot"
    ],
    "group_name_white_list": [
        "ALL_GROUP"
    ],
    "model": "dify",
    "single_chat_prefix": [
        ""
    ],
      "speech_recognition": true,  # 是否开启语音识别
        "voice_reply_voice": true,   # 是否使用语音回复语音
        "always_reply_voice": false, # 是否一直使用语音回复
        "voice_to_text": "xunfei",     # 语音识别引擎
        "text_to_voice": "dify"      # 语音合成引擎
}
```
此处的配置值无实际意义，程序不会读取此处的配置
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220111333750_0484bfc9.png)
配置相对应的APIkey等信息。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220111839905_363ff86d.png)
当前以讯飞为例
https://www.xfyun.cn/
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220112556928_f25719e8.png)
构建应用
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220112654993_7d2de1e4.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250218231845602_486c6281.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250218231922528_96d0bd49.png)
部分模型是没有免费额度，但是选择直接购买是可以领取一定量免费额度。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220112824254_ca2e98a6.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250218231621434_8277d18a.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250218231730326_a8781a1c.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250218231651486_56126b36.png)
当前使用conda环境进行测试安装，出现少包的错误使用下边命令进行依赖包安装。
```shell
conda install -c conda-forge ffmpeg pilk pysilk pydub
```
效果展示：
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220113118320_269855b3.png)
# 2.定时触发DIFY
当前场景适合想定期触发工作流，例如周期性任务。处理工作流或者信息检索生成等。
使用conda环境进行隔离
conda create -n api_sc2 python=3.11

![image](/assets/img/posts/low-code-dify-coze-12/image-20250220114308981_c33f8156.png)

conda activate api_sc2

![image](/assets/img/posts/low-code-dify-coze-12/image-20250220114435927_862c0a32.png)

 pip install -r requirements.txt

![image](/assets/img/posts/low-code-dify-coze-12/image-20250220114551072_3498287f.png)

python run.py

![image](/assets/img/posts/low-code-dify-coze-12/image-20250220114801570_d9b75d31.png)

获取API信息均在dify中进行获取。
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220114931987_5bc72b2a.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250220115359772_6e3a8985.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250220120150691_63610c70.png)

![image](/assets/img/posts/low-code-dify-coze-12/image-20250220120601697_f2666f7c.png)

## **2.1 整体讲解**
### 一、项目概述

这是一个API定时任务管理系统，主要功能是：
1. 管理定时任务（添加、删除、暂停、启动）
2. 定时调用API接口
3. 记录执行结果
4. 展示执行日志
### 二、核心文件及功能

#### 1. database.py - 数据库管理
```python
class Database:
    def __init__(self, db_path="tasks.db"):
        self.db_path = db_path
        self.init_db()
```
主要职责：
- 创建和管理SQLite数据库
- 提供两个主要表：
  - `tasks`：存储任务信息
  - `task_logs`：存储执行日志
#### 2. models.py - 数据模型
```python
class TaskCreate(BaseModel):
    name: constr(min_length=1, max_length=50)
    url: str
    method: constr(regex='^(GET|POST|PUT|DELETE)$') = 'POST'
    schedule_type: constr(regex='^(interval|fixed_time)$')
```
主要职责：
- 定义数据结构
- 验证数据格式
- 确保数据完整性
#### 3. main.py - 核心业务逻辑
```python
app = FastAPI()
db = Database()

@app.post("/tasks")
async def add_task(task: TaskCreate):
    # 添加任务逻辑
    
@app.get("/logs")
async def get_logs():
    # 获取日志逻辑
```
主要职责：
- 处理HTTP请求
- 执行业务逻辑
- 管理定时任务
- 返回处理结果

### 三、主要功能流程

#### 1. 添加新任务流程
```
A[用户填写表单] --> B[前端发送请求]
B --> C[后端验证数据]
C --> D[保存到数据库]
D --> E[返回结果]
```

#### 2. 执行任务流程
```
A[定时触发] --> B[读取任务信息]
B --> C[发送API请求]
C --> D[解析响应]
D --> E[记录日志]
E --> F[更新状态]
```

#### 3. 查看结果流程
```
A[前端定时请求] --> B[获取最新数据]
B --> C[更新页面显示]
```
### 四、数据结构

#### 1. tasks表（任务信息）
```sql
CREATE TABLE tasks (
    name TEXT PRIMARY KEY,          -- 任务名称
    url TEXT NOT NULL,              -- API地址
    method TEXT NOT NULL,           -- 请求方法
    schedule_type TEXT NOT NULL,    -- 调度类型
    schedule_value TEXT NOT NULL,   -- 调度值
    status TEXT DEFAULT 'pending'   -- 任务状态
    -- 其他字段...
)
```

#### 2. task_logs表（执行日志）
```sql
CREATE TABLE task_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT,                 -- 任务名称
    execution_time TIMESTAMP,       -- 执行时间
    status_code INTEGER,            -- 状态码
    response TEXT                   -- 响应内容
    -- 其他字段...
)
```
### 五、关键功能实现

#### 1. 定时执行
```python
def execute_task(task_name: str):
    # 1. 获取任务信息
    # 2. 发送API请求
    # 3. 处理响应
    # 4. 记录日志
    # 5. 更新状态
```

#### 2. 状态管理
```python
@app.post("/tasks/{task_name}/toggle")
async def toggle_task(task_name: str):
    # 切换任务状态（暂停/启动）
```

#### 3. 日志记录
```python
def log_execution(task_name, response, error=None):
    # 记录执行结果到数据库
```


### 六、使用的技术

1. **后端技术**：
   - Python FastAPI框架   
    一个现代、高性能的 Python Web 框架，用于构建 API。它基于 Python 类型提示，支持异步编程，适合开发高性能的 Web 应用。
   - SQLite数据库   
   轻量级的嵌入式关系型数据库，无需独立的服务器进程，数据存储在单个文件中，适合小型应用或原型开发。
   - Schedule任务调度库   
   轻量级的 Python 库，用于定期执行任务。它允许你以简单的方式安排函数在特定时间或间隔运行，适合需要周期性任务的应用场景。

2. **前端技术**：
   - HTML/CSS/JavaScript
   - AJAX异步请求
   - 定时刷新机制

3. **数据交互**：
   - RESTful API
   - JSON数据格式
   - HTTP基础认证
## **2.2单链路拆解**
以"添加新任务"为例：

### 1. 前端发起请求 (index.html)

```html
<!-- 前端表单 -->
<form id="taskForm" onsubmit="submitTask(event)">
    <input name="name" type="text" placeholder="任务名称">
    <input name="url" type="url" placeholder="API地址">
    <!-- 其他输入字段 -->
</form>

<!-- JavaScript处理提交 -->
<script>
async function submitTask(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    
    // 构造请求数据
    const data = {
        name: formData.get('name'),
        url: formData.get('url'),
        method: formData.get('method'),
        // ... 其他字段
    };

    // 发送POST请求到后端
    const response = await fetch('/tasks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });
    
    if (response.ok) {
        alert('添加任务成功！');
        window.location.reload();
    }
}
</script>
```
### 2. 后端接收请求 (main.py)

```python
@app.post("/tasks")
async def add_task(task: TaskCreate):
    try:
        # 1. 数据验证（通过models.py中的TaskCreate模型）
        # TaskCreate会自动验证数据格式是否正确
        
        # 2. 计算下次执行时间
        next_run = calculate_next_run(task.schedule_type, task.schedule_value)
        
        # 3. 保存到数据库
        with db.get_conn() as conn:
            conn.execute("""
                INSERT INTO tasks (
                    name, url, method, schedule_type, schedule_value,
                    headers, body, timeout, max_retries, next_run,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.name, str(task.url), task.method,
                task.sched.......,
                json.dumps(task......
                task.timeout, .....
                'pending'
            ))
            conn.commit()
        
        # 4. 返回成功响应
        return {"status": "success", "message": "任务添加成功"}
        
    except Exception as e:
        # 5. 如果出错，返回错误信息
        raise HTTPException(status_code=500, detail=str(e))
```
### 3. 数据验证 (models.py)

```python
class TaskCreate(BaseModel):
    name: constr(min_length=1, max_length=50)  # 验证任务名长度
    url: str  # API地址
    method: constr(regex='^(GET|POST|PUT|DELETE)$') = 'POST'
    schedule_type: constr(regex='^(interval|fixed_time)$')
    
    @validator('url')
    def validate_url(cls, v):
        # 验证URL格式
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
```
### 4. 数据库操作 (database.py)

```python
class Database:
    def __init__(self, db_path="tasks.db"):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_conn(self):
        # 获取数据库连接
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
```
### 5. 执行任务并返回结果的流程

当任务执行时：

```python
async def execute_task(task_name: str):
    try:
        # 1. 从数据库获取任务信息
        with db.get_conn() as conn:
            task = conn.execute(
                "SELECT * FROM tasks WHERE name = ?",
                (task_name,)
            ).fetchone()
        
        # 2. 发送API请求
        response = requests.request(
            method=task['method'],
            url=task['url'],
            headers=json.loads(task['headers']),
            json=json.loads(task['body']),
            timeout=task['timeout']
        )
        
        # 3. 解析响应
        parsed_response = parse_response(response.text)
        
        # 4. 保存执行结果到日志
        with db.get_conn() as conn:
            conn.execute("""
                INSERT INTO task_logs (
                    task_name, status_code, response, parsed_response
                ) VALUES (?, ?, ?, ?)
            """, (task_name, response.status_code, response.text, parsed_response))
            conn.commit()
            
        # 5. 更新任务状态
        update_task_status(task_name, 'active', parsed_response)
        
    except Exception as e:
        # 6. 如果出错，记录错误信息
        log_error(task_name, str(e))
```
### 6. 前端自动更新显示结果

```javascript
// 定期获取最新数据
function updateContent() {
    // 1. 获取任务列表
    fetch('/tasks')
        .then(response => response.json())
        .then(data => {
            // 更新任务列表显示
            updateTasksTable(data.tasks);
        });
    
    // 2. 获取执行日志
    fetch('/logs')
        .then(response => response.json())
        .then(data => {
            // 更新日志显示
            updateLogsTable(data.logs);
        });
}

// 每3秒更新一次
setInterval(updateContent, 3000);
```
### 完整流程总结：

1. **数据录入流程**：
   - 用户在前端填写表单
   - JavaScript收集表单数据并发送到后端
   - 后端验证数据格式
   - 数据保存到数据库
   - 返回结果给前端

2. **API访问流程**：
   - 定时器触发任务执行
   - 后端读取任务信息
   - 发送API请求
   - 解析响应结果
   - 保存执行日志
   - 前端自动更新显示最新结果

3. **使用的主要文件和方法**：
   - `index.html`: 前端界面和交互逻辑
   - `main.py`: API路由和业务逻辑处理
   - `models.py`: 数据验证和格式定义
   - `database.py`: 数据库操作封装
# 3.Dify使用技巧
## 变量引入
### 工具与环境变量结合
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220124828954_eecde2ef.png)
变量更新
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220124954534_b8961589.png)
全场景累计变量
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220151025721_f044e57f.png)
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220151122226_e7e988db.png)
### 代码块应用
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220125127408_ed18d25f.png)
## 常用场景
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220151916553_d340c064.png)
## 并行模式
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220152035089_6a7f45d0.png)
# 4.总结
![image](/assets/img/posts/low-code-dify-coze-12/image-20250220164227385_40f578bf.png)