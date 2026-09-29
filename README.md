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
