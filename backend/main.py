import os
import json
import asyncio
from typing import AsyncGenerator, Optional

# 1. 环境与网络配置
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import tempfile

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from database import Base, engine, get_db
from services.memory_service import MemoryService
from services.tools import TOOLS_SCHEMA, execute_tool

# 初始化数据库表
Base.metadata.create_all(bind=engine)

# 加载环境变量
load_dotenv()

app = FastAPI(title="LinguaAgent API", description="AI 英语私教后端接口")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL")
)

# RAG 组件
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
PERSIST_DIR = "./chroma_db"
vector_store: Optional[Chroma] = None


class ChatRequest(BaseModel):
    user_id: str
    message: str


# ================= 接口部分 =================

@app.post("/api/chat")
async def chat_endpoint(
        request: ChatRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    if not request.message:
        raise HTTPException(status_code=400, detail="消息不能为空")

    memory_service = MemoryService(db, client)
    history = memory_service.get_recent_history(request.user_id, limit=6)
    user_profile = memory_service.get_user_profile(request.user_id)

    # RAG 检索
    context = ""
    if vector_store is not None:
        try:
            retriever = vector_store.as_retriever(search_kwargs={"k": 3})
            docs = retriever.invoke(request.message)
            context = "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"⚠️ RAG 检索失败: {str(e)}")

    system_prompt = "You are a helpful and patient English tutor. Always reply in English. Keep your responses concise and encouraging."
    system_prompt += "\n【重要规则】：如果调用的工具未返回有效结果，请直接使用你自己的知识回答，不要向用户解释工具出错了。"
    if user_profile:
        system_prompt += f"\n\n【用户画像】：\n{user_profile}"
    if context:
        system_prompt += f"\n\n【文档参考】：\n{context}"

    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": request.message}
    ]

    # 🚀 升级：stream_and_save 接收 status_message，用于在调用工具前通知前端
    async def stream_and_save(messages_input: list, status_message: str = "") -> AsyncGenerator[str, None]:
        full_response = ""
        try:
            # 如果存在工具调用状态，先推送状态提示
            if status_message:
                yield f"data: [STATUS] {status_message}\n\n"

            response = client.chat.completions.create(
                model=os.getenv("LLM_MODEL_ID"),
                messages=messages_input,
                stream=True,
                temperature=0.7
            )
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    yield f"data: {content}\n\n"

            # 保存记忆到数据库
            memory_service.save_message(request.user_id, "user", request.message)
            memory_service.save_message(request.user_id, "assistant", full_response)
            recent_dialogue = f"User: {request.message}\nAssistant: {full_response}"

            # 异步更新画像
            background_tasks.add_task(memory_service.update_user_profile, request.user_id, recent_dialogue)

        except Exception as e:
            yield f"data: [Error] {str(e)}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    # 第一次请求：判断是否需要调用工具
    try:
        first_response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL_ID"),
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
            temperature=0.7
        )
        response_message = first_response.choices[0].message
        tool_calls = response_message.tool_calls
    except Exception as e:
        print(f"⚠️ 第一次 LLM 请求失败，降级为普通对话: {str(e)}")
        tool_calls = None

    if tool_calls:
        # 提取工具名称用于提示
        tool_names = [tc.function.name for tc in tool_calls]
        status_msg = f"正在使用工具: {', '.join(tool_names)}..."

        print(f"🛠️ 检测到工具调用: {tool_names}")
        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            tool_result = execute_tool(function_name, function_args)
            print(f"✅ 工具执行结果: {tool_result[:50]}...")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

        return StreamingResponse(stream_and_save(messages, status_msg), media_type="text/event-stream")

    return StreamingResponse(stream_and_save(messages), media_type="text/event-stream")


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    global vector_store

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".pdf", ".txt"]:
        raise HTTPException(status_code=400, detail="目前仅支持上传 PDF 或 TXT 文件")

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        def process_and_vectorize():
            documents = []
            if file_ext == ".pdf":
                loader = PyPDFLoader(tmp_path)
                documents = loader.load()
            elif file_ext == ".txt":
                with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                documents = [Document(page_content=text)]

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=300, chunk_overlap=50, separators=["\n\n", "\n", "。", "！", "？", " ", ""]
            )
            chunks = text_splitter.split_documents(documents)

            if vector_store is None:
                store = Chroma.from_documents(
                    documents=chunks,
                    embedding=embedding_model,
                    persist_directory=PERSIST_DIR
                )
            else:
                vector_store.add_documents(chunks)
                store = vector_store

            return store, len(chunks)

        new_store, chunk_count = await asyncio.to_thread(process_and_vectorize)
        vector_store = new_store

        return {"message": "上传成功", "file_type": file_ext, "chunks_count": chunk_count}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "LinguaAgent is running!"}