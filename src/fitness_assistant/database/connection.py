# src/fitness_assistant/database/connection.py
"""
Conexão com PostgreSQL usando SQLAlchemy async
"""
import asyncio
import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from ..config.settings import get_settings
from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gerenciador de conexão com PostgreSQL"""
    
    def __init__(self):
        self.settings = get_settings()
        self.engine = None
        self.session_factory = None
        self._initialized = False
        
    async def initialize(self):
        """Inicializa conexão com banco"""
        if self._initialized:
            return
            
        try:
            # URL de conexão
            database_url = self.settings.database_url
            if not database_url:
                # URL padrão para desenvolvimento
                database_url = "postgresql+asyncpg://fitness_user:fitness_dev_2024@localhost:5432/fitness_assistant"
                logger.warning("DATABASE_URL não configurada, usando padrão de desenvolvimento")
            
            # Garante que está usando asyncpg
            if not database_url.startswith("postgresql+asyncpg://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
            
            # Cria engine assíncrono
            if self.settings.debug:
                # Para desenvolvimento, usa configuração mais simples
                self.engine = create_async_engine(
                    database_url,
                    echo=True,
                    poolclass=NullPool,  # Sem pool para desenvolvimento
                )
            else:
                # Para produção, usa pool normal
                self.engine = create_async_engine(
                    database_url,
                    echo=False,
                    pool_size=20,
                    max_overflow=30,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                )
            
            # Cria factory de sessões
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            # Testa conexão
            await self._test_connection()
            
            self._initialized = True
            logger.info("✅ Conexão com PostgreSQL estabelecida")
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar PostgreSQL: {e}")
            logger.error("💡 Certifique-se de que:")
            logger.error("   - PostgreSQL está rodando")
            logger.error("   - DATABASE_URL está correta")
            logger.error("   - Usuario/senha estão corretos")
            raise
    
    async def _test_connection(self):
        """Testa conexão com banco"""
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(f"🔗 Conectado ao PostgreSQL: {version}")
        except Exception as e:
            logger.error(f"❌ Erro no teste de conexão: {e}")
            raise
    
    async def close(self):
        """Fecha conexão com banco"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("🔌 Conexão PostgreSQL fechada")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager para sessões de banco"""
        if not self._initialized:
            await self.initialize()
        
        if not self.session_factory:
            raise RuntimeError("Database não inicializado")
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Erro na sessão de banco: {e}")
                raise
            finally:
                await session.close()
    
    async def create_tables(self):
        """Cria todas as tabelas"""
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("📊 Tabelas criadas/atualizadas no PostgreSQL")
        except Exception as e:
            logger.error(f"❌ Erro ao criar tabelas: {e}")
            raise
    
    async def drop_tables(self):
        """Remove todas as tabelas (CUIDADO!)"""
        if not self._initialized:
            await self.initialize()
            
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.warning("🗑️ Todas as tabelas foram removidas!")
        except Exception as e:
            logger.error(f"❌ Erro ao remover tabelas: {e}")
            raise
    
    async def reset_database(self):
        """Reseta banco (drop + create)"""
        logger.warning("⚠️ Resetando banco de dados...")
        await self.drop_tables()
        await self.create_tables()
        logger.info("🔄 Banco de dados resetado")
    
    async def get_database_info(self) -> dict:
        """Retorna informações do banco"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.get_session() as session:
                # Versão do PostgreSQL
                result = await session.execute(text("SELECT version()"))
                version = result.scalar()
                
                # Número de tabelas
                result = await session.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                table_count = result.scalar()
                
                # Tamanho do banco
                result = await session.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """))
                db_size = result.scalar()
                
                return {
                    "version": version,
                    "table_count": table_count,
                    "database_size": db_size,
                    "connection_url": self.settings.database_url or "default",
                    "initialized": self._initialized
                }
        except Exception as e:
            logger.error(f"❌ Erro ao obter informações do banco: {e}")
            return {"error": str(e)}


# Instância global
db_manager = DatabaseManager()


# Funções de conveniência
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


async def reset_database():
    """Reseta banco de dados (desenvolvimento)"""
    await db_manager.reset_database()


async def get_db_info() -> dict:
    """Obtém informações do banco"""
    return await db_manager.get_database_info()


# Função para criar dados iniciais
async def seed_database():
    """Cria dados iniciais no banco"""
    logger.info("🌱 Criando dados iniciais...")
    
    try:
        async with get_db_session() as session:
            from .models import Exercise, ExerciseTypeEnum, IntensityLevelEnum
            
            # Verifica se já existem exercícios
            result = await session.execute(text("SELECT COUNT(*) FROM exercises"))
            exercise_count = result.scalar()
            
            if exercise_count > 0:
                logger.info(f"ℹ️ Banco já possui {exercise_count} exercícios")
                return
            
            # Exercícios iniciais
            initial_exercises = [
                {
                    "exercise_id": "walk_light",
                    "name": "Caminhada Leve",
                    "type": ExerciseTypeEnum.CARDIO,
                    "description": "Caminhada em ritmo confortável para iniciantes",
                    "instructions": ["Mantenha postura ereta", "Braços relaxados", "Respire naturalmente"],
                    "muscle_groups": ["pernas", "core"],
                    "equipment_needed": [],
                    "difficulty_level": IntensityLevelEnum.LOW,
                    "duration_min": 10,
                    "duration_max": 60,
                    "calories_per_minute": {"beginner": 3.5, "intermediate": 4.0, "advanced": 4.5},
                    "contraindications": [],
                    "modifications": ["Use bastão para apoio se necessário"],
                    "safety_notes": ["Hidrate-se adequadamente", "Use calçados apropriados"]
                },
                {
                    "exercise_id": "squat_bodyweight",
                    "name": "Agachamento Corpo Livre",
                    "type": ExerciseTypeEnum.STRENGTH,
                    "description": "Agachamento usando apenas o peso corporal",
                    "instructions": ["Pés na largura dos ombros", "Desça até coxas paralelas", "Mantenha joelhos alinhados"],
                    "muscle_groups": ["quadriceps", "glúteos", "core"],
                    "equipment_needed": [],
                    "difficulty_level": IntensityLevelEnum.MODERATE,
                    "duration_min": 5,
                    "duration_max": 20,
                    "calories_per_minute": {"beginner": 5.0, "intermediate": 6.0, "advanced": 7.0},
                    "contraindications": ["lesões no joelho", "problemas na lombar"],
                    "modifications": ["Use cadeira para apoio", "Agachamento parcial"],
                    "safety_notes": ["Não force além do confortável", "Mantenha core contraído"]
                },
                {
                    "exercise_id": "push_up",
                    "name": "Flexão de Braço",
                    "type": ExerciseTypeEnum.STRENGTH,
                    "description": "Flexão tradicional para força do tronco superior",
                    "instructions": ["Posição de prancha", "Desça o corpo controladamente", "Empurre de volta"],
                    "muscle_groups": ["peito", "triceps", "ombros", "core"],
                    "equipment_needed": [],
                    "difficulty_level": IntensityLevelEnum.MODERATE,
                    "duration_min": 5,
                    "duration_max": 15,
                    "calories_per_minute": {"beginner": 6.0, "intermediate": 7.0, "advanced": 8.0},
                    "contraindications": ["lesões no punho", "problemas no ombro"],
                    "modifications": ["Flexão com joelhos", "Flexão inclinada"],
                    "safety_notes": ["Mantenha core ativado", "Não force se sentir dor"]
                },
                {
                    "exercise_id": "plank",
                    "name": "Prancha",
                    "type": ExerciseTypeEnum.STRENGTH,
                    "description": "Exercício isométrico para fortalecimento do core",
                    "instructions": ["Posição de flexão com antebraços", "Mantenha corpo alinhado", "Respire normalmente"],
                    "muscle_groups": ["core", "ombros", "costas"],
                    "equipment_needed": [],
                    "difficulty_level": IntensityLevelEnum.MODERATE,
                    "duration_min": 1,
                    "duration_max": 5,
                    "calories_per_minute": {"beginner": 4.0, "intermediate": 5.0, "advanced": 6.0},
                    "contraindications": ["lesões na lombar", "problemas no ombro"],
                    "modifications": ["Prancha com joelhos", "Prancha inclinada"],
                    "safety_notes": ["Não prenda a respiração", "Pare se sentir dor lombar"]
                }
            ]
            
            # Adiciona exercícios ao banco
            for ex_data in initial_exercises:
                exercise = Exercise(**ex_data)
                session.add(exercise)
            
            await session.commit()
            logger.info(f"✅ {len(initial_exercises)} exercícios iniciais criados")
            
    except Exception as e:
        logger.error(f"❌ Erro ao criar dados iniciais: {e}")
        raise