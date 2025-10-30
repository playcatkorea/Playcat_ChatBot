from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from database.models import Base
import os

# 데이터베이스 파일 경로
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "playcat.db")
ASYNC_DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
SYNC_DATABASE_URL = f"sqlite:///{DB_PATH}"

# 비동기 엔진
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,
    future=True
)

# 동기 엔진 (테이블 생성용)
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=True
)

# 세션 팩토리
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    """데이터베이스 세션 의존성"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def init_db():
    """데이터베이스 테이블 생성"""
    Base.metadata.create_all(bind=sync_engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()
