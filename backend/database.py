from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 使用 SQLite 数据库，文件名为 lingua_agent.db，生成在当前目录下
SQLALCHEMY_DATABASE_URL = "sqlite:///./lingua_agent.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()