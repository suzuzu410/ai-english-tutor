# 🎓 LinguaAgent - 全栈 AI 英语私教

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)
![Vue3](https://img.shields.io/badge/Vue-3.0+-4FC08D.svg)
![RAG](https://img.shields.io/badge/RAG-ChromaDB-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

一个基于 **RAG（检索增强生成）、长短期记忆（Memory）与 Function Calling（技能调用）** 的全栈 AI 英语学习系统。用户可以上传英文文档进行基于语料的问答，系统会记住用户的学习画像，并能自动调用词典、语法纠错等工具。

## 📸 项目演示

<img width="1223" height="577" alt="屏幕截图 2026-09-29 144429" src="https://github.com/user-attachments/assets/9c2f7492-d13b-408f-bea4-0b09ca7b0e35" />

## ✨ 核心功能

- **📚 RAG 知识库问答**：支持上传 PDF/TXT 文档。针对中英文混合场景优化了切片策略，支持持久化存储与多文档追加检索。
- **🧠 双层级记忆系统**：
  - *短期记忆*：保留最近 6 轮对话上下文。
  - *长期记忆*：通过异步后台任务（Background Tasks）调用 LLM 提取用户水平与薄弱点（用户画像），存入 SQLite，实现“因人而异”的个性化教学。
- **🛠️ Agent 技能工具箱（Function Calling）**：
  - `lookup_word`：查词典（带网络异常静默降级）。
  - `check_grammar`：语法纠错与原因分析。
  - `roleplay`：沉浸式英语角色扮演。
  - *前端支持工具调用状态实时提示（自定义 `[STATUS]` SSE 事件）。*
- **⚡ 流式输出与极致 UX**：前后端基于 SSE 实现打字机效果，前端利用占位符与无痕替换技术，完美解决大模型首字延迟带来的体验问题。

## 🛠️ 技术栈

| 层级 | 技术 | 选型/版本 | 选择理由 |
|---|---|---|---|
| **前端** | Vue 3 + Vite | 3.x | 组合式 API 便于逻辑复用，Vite 启动极快 |
| | TailwindCSS | 3.x | 原子化 CSS，快速构建响应式界面 |
| | `@microsoft/fetch-event-source` | 2.x | 支持 POST 请求的 SSE 流式解析 |
| **后端** | Python + FastAPI | 3.10+ | 异步性能优异，自动生成 Swagger 文档 |
| | OpenAI SDK (兼容 DeepSeek) | 1.x | 标准的 Function Calling 接口 |
| **AI / RAG** | LangChain | 0.3.x | 文档加载、切片、向量库集成 |
| | ChromaDB | 0.5.x | 轻量级本地向量库，支持持久化 |
| | HuggingFace Embeddings | `all-MiniLM-L6-v2` | 本地推理、零成本、英文语义理解佳 |
| **数据库** | SQLite + SQLAlchemy | 2.x | 零配置存储对话历史与用户画像 |
| **部署/工具** | Uvicorn, python-dotenv | - | ASGI 服务器与环境变量管理 |

## 🏗️ 系统架构

```text
👤 用户（浏览器）
   ↓ HTTP / SSE
[ Vue3 前端 ] (App.vue, TailwindCSS, EventSource)
   ↓ POST /api/chat, POST /api/upload
[ FastAPI 后端 ] (main.py)
   ├── 🧠 Memory Service (SQLAlchemy + SQLite) -> 历史对话 & 用户画像
   ├── 📚 RAG Service (LangChain + ChromaDB) -> 文档切片 & 向量检索
   └── 🛠️ Tools Service (OpenAI Function Calling) -> 词典 / 语法 / 角色扮演
   ↓
[ 大语言模型 / 向量化模型 ] (DeepSeek API, HuggingFace Embeddings)

```

## 🧰 环境要求

``` Python 3.10+

    Node.js 18+

    Git

    DeepSeek API Key（获取地址）
```

## 🚀 快速开始
1. 克隆项目
```
bash

git clone https://github.com/suzuzu410/ai-english-tutor.git
cd ai-english-tutor
```
2. 启动后端
```
bash

cd backend
```
创建并激活虚拟环境
```
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
```
安装依赖
```
pip install -r requirements.txt
```
# 配置环境变量
```
复制 .env.example 为 .env，并填入你的 DeepSeek API Key：
LLM_MODEL_ID=deepseek-flash
LLM_API_KEY=sk-你的密钥
LLM_BASE_URL=https://api.deepseek.com
```
# 启动服务
```
python -m uvicorn main:app --reload

后端运行在 http://127.0.0.1:8000。首次启动会自动下载向量化模型（约 100MB）。
```
# 3. 启动前端
```
bash

cd ../frontend
```
# 安装依赖
```
npm install
```
# 启动开发服务器
```
npm run dev

前端运行在 http://localhost:5173。打开浏览器即可开始对话。
```
# 📂 项目结构
```
text

ai-english-tutor/
├── backend/                 # Python FastAPI 后端
│   ├── main.py              # 主入口，包含路由与核心 SSE 流式逻辑
│   ├── database.py          # 数据库连接
│   ├── models.py            # SQLAlchemy ORM 模型 (ChatHistory, UserProfile)
│   ├── services/            # 业务逻辑层
│   │   ├── memory_service.py# 记忆管理（短期+长期）
│   │   └── tools.py         # Function Calling 工具集
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # Vue3 前端
│   ├── src/
│   │   ├── App.vue          # 主聊天界面，包含 SSE 解析与 Markdown 渲染
│   │   └── style.css
│   ├── package.json
│   └── vite.config.js
└── README.md
方法	路径	用途	请求体示例
POST	/api/chat	流式对话（含工具调用）	{"user_id": "student_01", "message": "Hello"}
POST	/api/upload	上传 PDF/TXT 文档	multipart/form-data (key: file)
GET	/health	健康检查	-
```
