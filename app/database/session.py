"""
session.py — Async session factory.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.database import engine

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
