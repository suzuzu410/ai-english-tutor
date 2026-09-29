from sqlalchemy.orm import Session
from models import ChatHistory, UserProfile
from openai import OpenAI
import os


class MemoryService:
    def __init__(self, db: Session, client: OpenAI):
        self.db = db
        self.client = client

    # === 短期记忆：获取最近几轮对话 ===
    def get_recent_history(self, user_id: str, limit: int = 10):
        records = self.db.query(ChatHistory).filter(ChatHistory.user_id == user_id).order_by(
            ChatHistory.created_at.desc()).limit(limit).all()
        # 反转为时间正序
        records.reverse()
        return [{"role": r.role, "content": r.content} for r in records]

    # === 持久化：保存单条消息 ===
    def save_message(self, user_id: str, role: str, content: str):
        msg = ChatHistory(user_id=user_id, role=role, content=content)
        self.db.add(msg)
        self.db.commit()

    # === 长期记忆：获取用户画像 ===
    def get_user_profile(self, user_id: str):
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        return profile.profile_summary if profile else ""

    # === 长期记忆：更新用户画像（需要 LLM 辅助提取） ===
    def update_user_profile(self, user_id: str, recent_dialogue: str):
        current_profile = self.get_user_profile(user_id) or "暂无画像信息。"

        prompt = f"""
        你是一个英语教学助手。请根据以下对话，更新用户的英语学习画像。

        当前画像：
        {current_profile}

        最近对话记录：
        {recent_dialogue}

        请总结用户目前的英语水平、易错点、学习偏好。保持简短（不超过150字）。
        """

        response = self.client.chat.completions.create(
            model=os.getenv("LLM_MODEL_ID"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        new_profile = response.choices[0].message.content

        # 更新或创建数据库记录
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if profile:
            profile.profile_summary = new_profile
        else:
            profile = UserProfile(user_id=user_id, profile_summary=new_profile)
            self.db.add(profile)
        self.db.commit()