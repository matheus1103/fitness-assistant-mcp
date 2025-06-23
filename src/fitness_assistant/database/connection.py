# src/fitness_assistant/database/connection.py
"""
Conexão com PostgreSQL
"""
import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
import logging

from ..config.settings import get_settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gerenciador de conexão com PostgreSQL"""
    
    def __init__(self):
        self.settings = get_settings()
        self.engine = None
        self.session_factory = None
        
    async def initialize(self):
        """Inicializa conexão com banco"""
        try:
            database_url = self.settings.database_url
            if not database_url:
                raise ValueError("DATABASE_URL não configurada")
            
            # Cria engine assíncrono
            self.engine = create_async_engine(
                database_url,
                echo=self.settings.debug,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            
            # Cria factory de sessões
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("✅ Conexão com PostgreSQL estabelecida")
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar PostgreSQL: {e}")
            raise
    
    async def close(self):
        """Fecha conexão com banco"""
        if self.engine:
            await self.engine.dispose()
            logger.info("🔌 Conexão PostgreSQL fechada")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager para sessões de banco"""
        if not self.session_factory:
            raise RuntimeError("Database não inicializado")
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def create_tables(self):
        """Cria todas as tabelas"""
        from .models import Base
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("📊 Tabelas criadas no PostgreSQL")
    
    async def drop_tables(self):
        """Remove todas as tabelas (cuidado!)"""
        from .models import Base
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("🗑️ Tabelas removidas do PostgreSQL")

# Instância global
db_manager = DatabaseManager()

async def init_database():
    """Inicializa banco de dados"""
    await db_manager.initialize()
    await db_manager.create_tables()

async def close_database():
    """Fecha conexão com banco"""
    await db_manager.close()

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Obtém sessão de banco de dados"""
    async with db_manager.get_session() as session:
        yield session
