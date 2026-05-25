"""
Database session management and base models.
"""

from typing import AsyncGenerator, Optional, Type, TypeVar
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Column, DateTime, func
import uuid

from app.core.config import get_settings

settings = get_settings()

# Type variable for repository pattern
T = TypeVar("T", bound="Base")


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    
    # Common columns for all models
    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True
    )
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


# Engine and session factory
engine: Optional[AsyncEngine] = None
async_session_maker: Optional[async_sessionmaker[AsyncSession]] = None


def init_db(database_url: Optional[str] = None) -> None:
    """Initialize database engine and session factory."""
    global engine, async_session_maker
    
    db_url = database_url or settings.DATABASE_URL
    
    engine = create_async_engine(
        db_url,
        echo=settings.DEBUG,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    if async_session_maker is None:
        init_db()
    
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions."""
    if async_session_maker is None:
        init_db()
    
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all database tables."""
    if engine is None:
        init_db()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop all database tables."""
    if engine is None:
        init_db()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# Repository base class
class BaseRepository:
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: Type[T]):
        self.model = model
    
    async def get(self, db: AsyncSession, id: str) -> Optional[T]:
        """Get a single record by ID."""
        result = await db.get(self.model, id)
        return result
    
    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        desc: bool = False,
    ) -> list[T]:
        """Get all records with pagination."""
        from sqlalchemy import select, desc as desc_func
        
        query = select(self.model)
        
        if order_by and hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            query = query.order_by(desc_func(column) if desc else column)
        
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def create(
        self,
        db: AsyncSession,
        data: dict,
        commit: bool = True,
    ) -> T:
        """Create a new record."""
        obj = self.model(**data)
        db.add(obj)
        
        if commit:
            await db.commit()
            await db.refresh(obj)
        
        return obj
    
    async def update(
        self,
        db: AsyncSession,
        id: str,
        data: dict,
        commit: bool = True,
    ) -> Optional[T]:
        """Update an existing record."""
        obj = await self.get(db, id)
        
        if obj is None:
            return None
        
        for field, value in data.items():
            if hasattr(obj, field):
                setattr(obj, field, value)
        
        if commit:
            await db.commit()
            await db.refresh(obj)
        
        return obj
    
    async def delete(
        self,
        db: AsyncSession,
        id: str,
        commit: bool = True,
    ) -> bool:
        """Delete a record."""
        obj = await self.get(db, id)
        
        if obj is None:
            return False
        
        await db.delete(obj)
        
        if commit:
            await db.commit()
        
        return True
    
    async def count(self, db: AsyncSession) -> int:
        """Count all records."""
        from sqlalchemy import select, func
        
        result = await db.execute(select(func.count()).select_from(self.model))
        return result.scalar() or 0
