from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .config import get_config, DefaultConfig

Base = declarative_base()
engine = None
AsyncSessionLocal = None

def init_db(config: DefaultConfig) -> None:
    global engine, AsyncSessionLocal

    postgres_endpoint = config.postgresql_endpoint
    postgres_port = config.postgresql_port
    postgres_table = config.postgresql_table
    postgres_user = config.postgresql_user
    postgres_password = config.postgresql_password

    db_url = (
        f"postgresql+asyncpg://{postgres_user}:{postgres_password}"
        f"@{postgres_endpoint}:{postgres_port}/{postgres_table}"
    )

    try:
        engine = create_async_engine(db_url, echo=True)
        AsyncSessionLocal = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        print("Database connection successful.")
    except Exception as e:
        print(f"Database connection failed. Reason: {str(e)}")
        print(f"Failed URL: {db_url}")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Initialize the database
init_db(get_config())