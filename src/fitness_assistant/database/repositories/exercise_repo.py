# src/fitness_assistant/database/repositories/exercise_repo.py
"""
Repository para exercícios usando SQLAlchemy
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select, func, and_, or_

from .base import BaseRepository
from ..models import Exercise, ExerciseTypeEnum, IntensityLevelEnum
from ..connection import get_db_session


class ExerciseRepository(BaseRepository[Exercise]):
    """Repository para operações de exercícios"""
    
    def __init__(self):
        super().__init__(Exercise)
    
    async def get_exercise_by_id(self, exercise_id: str) -> Optional[Exercise]:
        """Busca exercício por exercise_id (string)"""
        return await self.get_by_field("exercise_id", exercise_id)
    
    async def get_exercises_by_type(self, exercise_type: str) -> List[Exercise]:
        """Busca exercícios por tipo"""
        try:
            exercise_enum = ExerciseTypeEnum(exercise_type.lower())
            return await self.filter_by(type=exercise_enum)
        except ValueError:
            return []
    
    async def get_exercises_by_difficulty(self, difficulty: str) -> List[Exercise]:
        """Busca exercícios por dificuldade"""
        try:
            difficulty_enum = IntensityLevelEnum(difficulty.lower())
            return await self.filter_by(difficulty_level=difficulty_enum)
        except ValueError:
            return []
    
    async def get_exercises_by_equipment(self, equipment_list: List[str]) -> List[Exercise]:
        """Busca exercícios que podem ser feitos com equipamentos disponíveis"""
        async with get_db_session() as session:
            # Se não tem equipamento disponível, busca apenas exercícios sem equipamento
            if not equipment_list or equipment_list == ["none"]:
                result = await session.execute(
                    select(Exercise).where(
                        or_(
                            Exercise.equipment_needed == [],
                            Exercise.equipment_needed.is_(None)
                        )
                    )
                )
            else:
                # Busca exercícios onde todos os equipamentos necessários estão disponíveis
                result = await session.execute(
                    select(Exercise).where(
                        Exercise.equipment_needed.contained_by(equipment_list)
                    )
                )
            
            return result.scalars().all()
    
    async def search_exercises(self, name: str) -> List[Exercise]:
        """Busca exercícios por nome (busca parcial)"""
        return await self.search(name, "name", "description")
    
    async def get_exercises_by_muscle_group(self, muscle_group: str) -> List[Exercise]:
        """Busca exercícios por grupo muscular"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Exercise).where(
                    Exercise.muscle_groups.any(muscle_group.lower())
                )
            )
            return result.scalars().all()
    
    async def filter_exercises(self, **criteria) -> List[Exercise]:
        """Filtra exercícios por múltiplos critérios"""
        async with get_db_session() as session:
            query = select(Exercise)
            conditions = []
            
            # Filtro por tipo
            if "type" in criteria:
                try:
                    exercise_type = ExerciseTypeEnum(criteria["type"].lower())
                    conditions.append(Exercise.type == exercise_type)
                except ValueError:
                    pass
            
            # Filtro por dificuldade
            if "difficulty" in criteria:
                try:
                    difficulty = IntensityLevelEnum(criteria["difficulty"].lower())
                    conditions.append(Exercise.difficulty_level == difficulty)
                except ValueError:
                    pass
            
            # Filtro por equipamentos disponíveis
            if "equipment" in criteria:
                equipment_list = criteria["equipment"]
                if not equipment_list or equipment_list == ["none"]:
                    conditions.append(
                        or_(
                            Exercise.equipment_needed == [],
                            Exercise.equipment_needed.is_(None)
                        )
                    )
                else:
                    conditions.append(Exercise.equipment_needed.contained_by(equipment_list))
            
            # Filtro por grupos musculares
            if "muscle_groups" in criteria:
                target_groups = [mg.lower() for mg in criteria["muscle_groups"]]
                muscle_conditions = [
                    Exercise.muscle_groups.any(group) for group in target_groups
                ]
                conditions.append(or_(*muscle_conditions))
            
            # Filtro por duração máxima
            if "max_duration" in criteria:
                max_dur = criteria["max_duration"]
                conditions.append(Exercise.duration_min <= max_dur)
            
            # Filtro por duração mínima
            if "min_duration" in criteria:
                min_dur = criteria["min_duration"]
                conditions.append(Exercise.duration_max >= min_dur)
            
            # Aplica filtros
            if conditions:
                query = query.where(and_(*conditions))
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def get_recommended_exercises(
        self,
        fitness_level: str,
        exercise_types: List[str] = None,
        available_equipment: List[str] = None,
        exclude_conditions: List[str] = None,
        limit: int = 10
    ) -> List[Exercise]:
        """Busca exercícios recomendados baseado em critérios"""
        async with get_db_session() as session:
            query = select(Exercise)
            conditions = []
            
            # Filtro por nível de fitness
            if fitness_level == "beginner":
                conditions.append(
                    Exercise.difficulty_level.in_([
                        IntensityLevelEnum.VERY_LOW,
                        IntensityLevelEnum.LOW
                    ])
                )
            elif fitness_level == "intermediate":
                conditions.append(
                    Exercise.difficulty_level.in_([
                        IntensityLevelEnum.LOW,
                        IntensityLevelEnum.MODERATE
                    ])
                )
            elif fitness_level == "advanced":
                conditions.append(
                    Exercise.difficulty_level.in_([
                        IntensityLevelEnum.MODERATE,
                        IntensityLevelEnum.HIGH,
                        IntensityLevelEnum.VERY_HIGH
                    ])
                )
            
            # Filtro por tipos de exercício
            if exercise_types:
                type_enums = []
                for ex_type in exercise_types:
                    try:
                        type_enums.append(ExerciseTypeEnum(ex_type.lower()))
                    except ValueError:
                        continue
                
                if type_enums:
                    conditions.append(Exercise.type.in_(type_enums))
            
            # Filtro por equipamentos
            if available_equipment:
                if not available_equipment or available_equipment == ["none"]:
                    conditions.append(
                        or_(
                            Exercise.equipment_needed == [],
                            Exercise.equipment_needed.is_(None)
                        )
                    )
                else:
                    conditions.append(Exercise.equipment_needed.contained_by(available_equipment))
            
            # Exclui exercícios com contraindicações
            if exclude_conditions:
                for condition in exclude_conditions:
                    conditions.append(
                        ~Exercise.contraindications.any(condition.lower())
                    )
            
            # Aplica filtros e limita resultados
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.limit(limit)
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def get_exercise_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas dos exercícios"""
        async with get_db_session() as session:
            # Total de exercícios
            total = await session.execute(select(func.count(Exercise.id)))
            
            # Por tipo
            type_stats = await session.execute(
                select(
                    Exercise.type,
                    func.count(Exercise.id).label('count')
                ).group_by(Exercise.type)
            )
            
            # Por dificuldade
            difficulty_stats = await session.execute(
                select(
                    Exercise.difficulty_level,
                    func.count(Exercise.id).label('count')
                ).group_by(Exercise.difficulty_level)
            )
            
            # Exercícios sem equipamento
            no_equipment = await session.execute(
                select(func.count(Exercise.id)).where(
                    or_(
                        Exercise.equipment_needed == [],
                        Exercise.equipment_needed.is_(None)
                    )
                )
            )
            
            return {
                "total_exercises": total.scalar(),
                "by_type": {row.type.value: row.count for row in type_stats},
                "by_difficulty": {row.difficulty_level.value: row.count for row in difficulty_stats},
                "no_equipment_needed": no_equipment.scalar()
            }
    
    async def add_exercise(self, exercise_data: Dict[str, Any]) -> Exercise:
        """Adiciona novo exercício"""
        # Converte strings para enums
        if "type" in exercise_data:
            exercise_data["type"] = ExerciseTypeEnum(exercise_data["type"].lower())
        
        if "difficulty_level" in exercise_data:
            exercise_data["difficulty_level"] = IntensityLevelEnum(exercise_data["difficulty_level"].lower())
        
        return await self.create(**exercise_data)
    
    async def update_exercise(self, exercise_id: str, updates: Dict[str, Any]) -> Optional[Exercise]:
        """Atualiza exercício por exercise_id"""
        async with get_db_session() as session:
            # Busca exercício primeiro
            result = await session.execute(
                select(Exercise).where(Exercise.exercise_id == exercise_id)
            )
            exercise = result.scalar_one_or_none()
            
            if not exercise:
                return None
            
            # Converte enums se necessário
            if "type" in updates:
                updates["type"] = ExerciseTypeEnum(updates["type"].lower())
            
            if "difficulty_level" in updates:
                updates["difficulty_level"] = IntensityLevelEnum(updates["difficulty_level"].lower())
            
            # Atualiza campos
            for field, value in updates.items():
                if hasattr(exercise, field):
                    setattr(exercise, field, value)
            
            await session.flush()
            await session.refresh(exercise)
            return exercise
    
    async def delete_exercise(self, exercise_id: str) -> bool:
        """Remove exercício por exercise_id"""
        async with get_db_session() as session:
            # Busca exercício primeiro
            result = await session.execute(
                select(Exercise).where(Exercise.exercise_id == exercise_id)
            )
            exercise = result.scalar_one_or_none()
            
            if not exercise:
                return False
            
            await session.delete(exercise)
            return True
    
    async def get_exercises_by_duration_range(self, min_duration: int, max_duration: int) -> List[Exercise]:
        """Busca exercícios por faixa de duração"""
        async with get_db_session() as session:
            result = await session.execute(
                select(Exercise).where(
                    and_(
                        Exercise.duration_min >= min_duration,
                        Exercise.duration_max <= max_duration
                    )
                )
            )
            return result.scalars().all()
    
    async def get_exercises_without_contraindications(self, health_conditions: List[str]) -> List[Exercise]:
        """Busca exercícios seguros para condições de saúde específicas"""
        async with get_db_session() as session:
            conditions = []
            
            # Para cada condição de saúde, exclui exercícios com contraindicação
            for condition in health_conditions:
                conditions.append(
                    ~Exercise.contraindications.any(condition.lower())
                )
            
            result = await session.execute(
                select(Exercise).where(and_(*conditions))
            )
            return result.scalars().all()
    
    async def get_popular_exercises(self, limit: int = 10) -> List[Exercise]:
        """Busca exercícios mais populares (baseado em uso em sessões)"""
        async with get_db_session() as session:
            # Nota: Esta query assumiria uma tabela de sessões de exercício
            # Por simplicidade, retorna exercícios por ordem alfabética
            result = await session.execute(
                select(Exercise)
                .order_by(Exercise.name)
                .limit(limit)
            )
            return result.scalars().all()


# Instância global
exercise_repo = ExerciseRepository()