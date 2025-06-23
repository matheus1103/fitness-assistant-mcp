
# src/fitness_assistant/database/repositories.py
"""
Repositórios para acesso aos dados
"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

from .models import UserProfile, Exercise, WorkoutSession, SessionExercise, HeartRateData
from .connection import get_db_session

class UserRepository:
    """Repositório para usuários"""
    
    async def create_user(self, user_data: Dict[str, Any]) -> UserProfile:
        """Cria novo usuário"""
        async with get_db_session() as session:
            user = UserProfile(**user_data)
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserProfile]:
        """Busca usuário por ID"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            return result.scalar_one_or_none()
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[UserProfile]:
        """Atualiza usuário"""
        async with get_db_session() as session:
            updates['updated_at'] = datetime.utcnow()
            
            await session.execute(
                update(UserProfile)
                .where(UserProfile.user_id == user_id)
                .values(**updates)
            )
            
            return await self.get_user_by_id(user_id)
    
    async def delete_user(self, user_id: str) -> bool:
        """Remove usuário"""
        async with get_db_session() as session:
            result = await session.execute(
                delete(UserProfile).where(UserProfile.user_id == user_id)
            )
            return result.rowcount > 0
    
    async def list_users(self, limit: int = 100, offset: int = 0) -> List[UserProfile]:
        """Lista usuários"""
        async with get_db_session() as session:
            result = await session.execute(
                select(UserProfile)
                .offset(offset)
                .limit(limit)
                .order_by(UserProfile.created_at.desc())
            )
            return result.scalars().all()

class SessionRepository:
    """Repositório para sessões de treino"""
    
    async def create_session(self, session_data: Dict[str, Any]) -> WorkoutSession:
        """Cria nova sessão"""
        async with get_db_session() as session:
            workout = WorkoutSession(**session_data)
            session.add(workout)
            await session.flush()
            await session.refresh(workout)
            return workout
    
    async def get_user_sessions(
        self, 
        user_id: str, 
        limit: int = 50,
        days_back: int = 30
    ) -> List[WorkoutSession]:
        """Busca sessões do usuário"""
        async with get_db_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            result = await session.execute(
                select(WorkoutSession)
                .join(UserProfile)
                .where(
                    UserProfile.user_id == user_id,
                    WorkoutSession.session_date >= cutoff_date
                )
                .options(selectinload(WorkoutSession.exercises))
                .order_by(WorkoutSession.session_date.desc())
                .limit(limit)
            )
            return result.scalars().all()
    
    async def get_session_analytics(self, user_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Calcula analytics das sessões"""
        async with get_db_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            result = await session.execute(
                select(
                    func.count(WorkoutSession.id).label('total_sessions'),
                    func.sum(WorkoutSession.duration_minutes).label('total_duration'),
                    func.avg(WorkoutSession.avg_heart_rate).label('avg_hr'),
                    func.sum(WorkoutSession.calories_estimated).label('total_calories')
                )
                .join(UserProfile)
                .where(
                    UserProfile.user_id == user_id,
                    WorkoutSession.session_date >= cutoff_date
                )
            )
            
            row = result.first()
            
            return {
                "total_sessions": row.total_sessions or 0,
                "total_duration": row.total_duration or 0,
                "avg_duration": (row.total_duration or 0) / max(row.total_sessions or 1, 1),
                "avg_heart_rate": int(row.avg_hr or 0),
                "total_calories": row.total_calories or 0,
                "period_days": days_back
            }

class ExerciseRepository:
    """Repositório para exercícios"""
    
    async def get_exercises_by_type(self, exercise_type: str) -> List[Exercise]:
        """Busca exercícios por tipo"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Exercise).where(Exercise.type == exercise_type)
            )
            return result.scalars().all()
    
    async def search_exercises(self, query: str) -> List[Exercise]:
        """Busca exercícios por nome"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Exercise).where(Exercise.name.ilike(f"%{query}%"))
            )
            return result.scalars().all()
    
    async def create_exercise(self, exercise_data: Dict[str, Any]) -> Exercise:
        """Cria novo exercício"""
        async with get_db_session() as session:
            exercise = Exercise(**exercise_data)
            session.add(exercise)
            await session.flush()
            await session.refresh(exercise)
            return exercise

# Instâncias globais dos repositórios
user_repo = UserRepository()
session_repo = SessionRepository()
exercise_repo = ExerciseRepository()