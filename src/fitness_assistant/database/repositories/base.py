# src/fitness_assistant/database/repositories/base.py
"""
Repository base com operações comuns
"""
from typing import TypeVar, Generic, Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

from ..connection import get_db_session

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Repository base com operações CRUD comuns"""
    
    def __init__(self, model_class: type[T]):
        self.model_class = model_class
    
    async def create(self, **data) -> T:
        """Cria novo registro"""
        async with get_db_session() as session:
            instance = self.model_class(**data)
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
            return instance
    
    async def get_by_id(self, id_value: UUID) -> Optional[T]:
        """Busca por ID (UUID)"""
        async with get_db_session() as session:
            result = await session.execute(
                select(self.model_class).where(self.model_class.id == id_value)
            )
            return result.scalar_one_or_none()
    
    async def get_by_field(self, field_name: str, value: Any) -> Optional[T]:
        """Busca por campo específico"""
        async with get_db_session() as session:
            field = getattr(self.model_class, field_name)
            result = await session.execute(
                select(self.model_class).where(field == value)
            )
            return result.scalar_one_or_none()
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Busca todos os registros com paginação"""
        async with get_db_session() as session:
            result = await session.execute(
                select(self.model_class)
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
    
    async def update_by_id(self, id_value: UUID, **updates) -> Optional[T]:
        """Atualiza registro por ID"""
        async with get_db_session() as session:
            # Executa update
            result = await session.execute(
                update(self.model_class)
                .where(self.model_class.id == id_value)
                .values(**updates)
                .returning(self.model_class)
            )
            updated_instance = result.scalar_one_or_none()
            
            if updated_instance:
                await session.refresh(updated_instance)
            
            return updated_instance
    
    async def delete_by_id(self, id_value: UUID) -> bool:
        """Remove registro por ID"""
        async with get_db_session() as session:
            result = await session.execute(
                delete(self.model_class).where(self.model_class.id == id_value)
            )
            return result.rowcount > 0
    
    async def count(self) -> int:
        """Conta total de registros"""
        async with get_db_session() as session:
            result = await session.execute(
                select(func.count(self.model_class.id))
            )
            return result.scalar()
    
    async def exists(self, **conditions) -> bool:
        """Verifica se registro existe"""
        async with get_db_session() as session:
            conditions_list = [
                getattr(self.model_class, field) == value 
                for field, value in conditions.items()
            ]
            
            result = await session.execute(
                select(func.count(self.model_class.id))
                .where(*conditions_list)
            )
            return result.scalar() > 0
    
    async def filter_by(self, **conditions) -> List[T]:
        """Filtra registros por condições"""
        async with get_db_session() as session:
            conditions_list = [
                getattr(self.model_class, field) == value 
                for field, value in conditions.items()
            ]
            
            result = await session.execute(
                select(self.model_class).where(*conditions_list)
            )
            return result.scalars().all()
    
    async def get_with_relations(self, id_value: UUID, *relations) -> Optional[T]:
        """Busca com relacionamentos carregados"""
        async with get_db_session() as session:
            query = select(self.model_class).where(self.model_class.id == id_value)
            
            # Adiciona carregamento de relacionamentos
            for relation in relations:
                query = query.options(selectinload(getattr(self.model_class, relation)))
            
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    async def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[T]:
        """Cria múltiplos registros em lote"""
        async with get_db_session() as session:
            instances = [self.model_class(**data) for data in data_list]
            session.add_all(instances)
            await session.flush()
            
            # Refresh all instances
            for instance in instances:
                await session.refresh(instance)
            
            return instances
    
    async def search(self, search_term: str, *fields) -> List[T]:
        """Busca textual em campos especificados"""
        async with get_db_session() as session:
            from sqlalchemy import or_, func
            
            # Cria condições de busca para cada campo
            search_conditions = []
            for field_name in fields:
                field = getattr(self.model_class, field_name)
                search_conditions.append(
                    func.lower(field).contains(search_term.lower())
                )
            
            result = await session.execute(
                select(self.model_class).where(or_(*search_conditions))
            )
            return result.scalars().all()