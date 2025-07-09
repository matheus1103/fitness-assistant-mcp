# src/fitness_assistant/database/repositories/user_repo.py
"""
Repository para usuários usando SQLAlchemy
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..models import UserProfile, WorkoutSession, HeartRateData
from ..connection import get_db_session


class UserRepository(BaseRepository[UserProfile]):
    """Repository para operações de usuário"""
    async def list_users(self, limit: int = 100, offset: int = 0) -> List[UserProfile]:
        """Lista usuários com paginação"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserProfile)
                .order_by(UserProfile.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
    def __init__(self):
        super().__init__(UserProfile)
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserProfile]:
        """Busca usuário por user_id (string)"""
        return await self.get_by_field("user_id", user_id)
    
    async def create_user(self, user_data: Dict[str, Any]) -> UserProfile:
        """Cria novo usuário"""
        return await self.create(**user_data)
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[UserProfile]:
        """Atualiza usuário por user_id"""
        async with get_db_session() as session:
            # Busca usuário primeiro
            result = await session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Atualiza campos
            for field, value in updates.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            
            await session.flush()
            await session.refresh(user)
            return user
    
    async def delete_user(self, user_id: str) -> bool:
        """Remove usuário por user_id"""
        async with get_db_session() as session:
            # Busca usuário primeiro
            result = await session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            await session.delete(user)
            return True
    
    async def user_exists(self, user_id: str) -> bool:
        """Verifica se usuário existe"""
        return await self.exists(user_id=user_id)
    
    async def get_users_by_fitness_level(self, fitness_level: str) -> List[UserProfile]:
        """Busca usuários por nível de fitness"""
        return await self.filter_by(fitness_level=fitness_level)
    
    async def get_users_by_age_range(self, min_age: int, max_age: int) -> List[UserProfile]:
        """Busca usuários por faixa etária"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserProfile).where(
                    and_(
                        UserProfile.age >= min_age,
                        UserProfile.age <= max_age
                    )
                )
            )
            return result.scalars().all()
    
    async def get_users_with_health_condition(self, condition: str) -> List[UserProfile]:
        """Busca usuários com condição de saúde específica"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserProfile).where(
                    UserProfile.health_conditions.any(condition)
                )
            )
            return result.scalars().all()
    
    async def get_user_with_sessions(self, user_id: str, limit_sessions: int = 10) -> Optional[UserProfile]:
        """Busca usuário com sessões recentes"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserProfile)
                .options(selectinload(UserProfile.sessions).limit(limit_sessions))
                .where(UserProfile.user_id == user_id)
            )
            return result.scalar_one_or_none()
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Calcula estatísticas do usuário"""
        async with get_db_session() as session:
            # Busca usuário
            user_result = await session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return {}
            
            # Estatísticas de sessões
            session_stats = await session.execute(
                select(
                    func.count(WorkoutSession.id).label('total_sessions'),
                    func.sum(WorkoutSession.duration_minutes).label('total_minutes'),
                    func.avg(WorkoutSession.avg_heart_rate).label('avg_heart_rate'),
                    func.sum(WorkoutSession.calories_estimated).label('total_calories'),
                    func.max(WorkoutSession.session_date).label('last_session')
                ).where(WorkoutSession.user_profile_id == user.id)
            )
            
            stats = session_stats.first()
            
            # Dados de FC recentes
            hr_stats = await session.execute(
                select(
                    func.avg(HeartRateData.current_hr).label('avg_current_hr'),
                    func.count(HeartRateData.id).label('hr_readings')
                ).where(
                    and_(
                        HeartRateData.user_profile_id == user.id,
                        HeartRateData.timestamp >= func.now() - func.interval('30 days')
                    )
                )
            )
            
            hr_data = hr_stats.first()
            
            return {
                "user_id": user_id,
                "total_sessions": stats.total_sessions or 0,
                "total_minutes": stats.total_minutes or 0,
                "total_calories": stats.total_calories or 0,
                "avg_heart_rate": round(stats.avg_heart_rate or 0, 1),
                "last_session": stats.last_session,
                "avg_current_hr": round(hr_data.avg_current_hr or 0, 1),
                "hr_readings_30d": hr_data.hr_readings or 0,
                "bmi": user.bmi,
                "bmi_category": user.bmi_category
            }
    
    async def get_active_users(self, days: int = 30) -> List[UserProfile]:
        """Busca usuários ativos nos últimos X dias"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserProfile)
                .join(WorkoutSession)
                .where(
                    WorkoutSession.session_date >= func.now() - func.interval(f'{days} days')
                )
                .distinct()
            )
            return result.scalars().all()
    
    async def search_users(self, search_term: str) -> List[UserProfile]:
        """Busca usuários por termo (user_id)"""
        return await self.search(search_term, "user_id")
    
    async def get_users_summary(self) -> Dict[str, Any]:
        """Retorna resumo estatístico dos usuários"""
        async with get_db_session() as session:
            # Contagem total
            total_users = await session.execute(
                select(func.count(UserProfile.id))
            )
            
            # Por nível de fitness
            fitness_stats = await session.execute(
                select(
                    UserProfile.fitness_level,
                    func.count(UserProfile.id).label('count')
                ).group_by(UserProfile.fitness_level)
            )
            
            # Por faixa etária
            age_stats = await session.execute(
                select(
                    func.case(
                        (UserProfile.age < 25, 'under_25'),
                        (UserProfile.age < 35, '25_34'),
                        (UserProfile.age < 50, '35_49'),
                        (UserProfile.age < 65, '50_64'),
                        else_='65_plus'
                    ).label('age_group'),
                    func.count(UserProfile.id).label('count')
                ).group_by('age_group')
            )
            
            # Usuários ativos
            active_users = await session.execute(
                select(func.count(func.distinct(WorkoutSession.user_profile_id)))
                .where(
                    WorkoutSession.session_date >= func.now() - func.interval('30 days')
                )
            )
            
            return {
                "total_users": total_users.scalar(),
                "active_users_30d": active_users.scalar(),
                "by_fitness_level": {row.fitness_level: row.count for row in fitness_stats},
                "by_age_group": {row.age_group: row.count for row in age_stats}
            }


# Instância global
user_repo = UserRepository()