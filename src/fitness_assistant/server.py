#!/usr/bin/env python3
"""
Servidor MCP integrado com PostgreSQL
"""
import sys
import os
from pathlib import Path
from sqlalchemy import select, or_
from sqlalchemy import select, func, and_

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fitness_assistant.database.models import (
    Exercise, WorkoutSession, SessionExercise, 
    ExerciseTypeEnum, IntensityLevelEnum
)
# Adiciona src ao path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Imports do FastMCP
from fastmcp import FastMCP

# Imports do projeto
from fitness_assistant.database.connection import init_database, get_db_session
from fitness_assistant.database.models import UserProfile, FitnessLevelEnum, GenderEnum
from fitness_assistant.database.repositories import UserRepository
from fitness_assistant.config.settings import get_settings

# Cria o servidor
mcp = FastMCP("Fitness Assistant with PostgreSQL")

# Inicializa repositórios
user_repo = UserRepository()
# ADICIONE ESTAS CLASSES no seu server_postgres.py:
class WorkoutRepository:
    """Repositório para salvar treinos no PostgreSQL"""
    
    async def save_workout_session(self, user_id: str, workout_data: Dict[str, Any]) -> bool:
        """Salva sessão de treino no banco"""
        try:
            async with get_db_session() as session:
                # Busca usuário
                user_result = await session.execute(
                    select(UserProfile).where(UserProfile.user_id == user_id)
                )
                user = user_result.scalar_one_or_none()
                
                if not user:
                    return False
                
                # Busca exercícios disponíveis na tabela
                exercises_result = await session.execute(
                    select(Exercise).limit(5)  # Pega alguns exercícios
                )
                available_exercises = exercises_result.scalars().all()
                
                if not available_exercises:
                    logger.error("Nenhum exercício encontrado na tabela exercises")
                    return False
                
                # Cria sessão de treino
                workout_session = WorkoutSession(
                    user_profile_id=user.id,
                    duration_minutes=workout_data.get('duration_minutes', 30),
                    session_type=workout_data.get('workout_type', 'mixed'),
                    avg_heart_rate=workout_data.get('avg_heart_rate'),
                    max_heart_rate=workout_data.get('max_heart_rate'),
                    perceived_exertion=workout_data.get('perceived_exertion'),
                    calories_estimated=workout_data.get('calories_estimated'),
                    notes=workout_data.get('notes', '')
                )
                
                session.add(workout_session)
                await session.flush()  # Para obter o ID
                
                # Adiciona exercícios REAIS da tabela exercises
                exercises_to_add = workout_data.get('exercises', [])
                
                for i, exercise_data in enumerate(exercises_to_add):
                    # Pega um exercício real da tabela (cicla entre os disponíveis)
                    real_exercise = available_exercises[i % len(available_exercises)]
                    
                    session_exercise = SessionExercise(
                        session_id=workout_session.id,
                        exercise_id=real_exercise.id,  # USA ID REAL da tabela exercises
                        duration_minutes=exercise_data.get('duration', 15),
                        sets_performed=exercise_data.get('sets', 1),
                        reps_performed=exercise_data.get('reps'),
                        weight_used=exercise_data.get('weight'),
                        distance_covered=exercise_data.get('distance'),
                        notes=exercise_data.get('notes', exercise_data.get('name', 'Exercício'))
                    )
                    session.add(session_exercise)
                
                await session.commit()
                logger.info(f"Treino salvo para {user_id} com {len(exercises_to_add)} exercícios")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao salvar treino: {e}")
            return False
    
    async def get_random_exercises_by_type(self, workout_type: str, limit: int = 3) -> List[Exercise]:
        """Busca exercícios aleatórios por tipo"""
        try:
            async with get_db_session() as session:
                if workout_type == "mixed":
                    # Para treino misto, pega de vários tipos
                    result = await session.execute(
                        select(Exercise)
                        .where(Exercise.type.in_([ExerciseTypeEnum.CARDIO, ExerciseTypeEnum.STRENGTH]))
                        .limit(limit)
                    )
                elif workout_type == "cardio":
                    result = await session.execute(
                        select(Exercise)
                        .where(Exercise.type == ExerciseTypeEnum.CARDIO)
                        .limit(limit)
                    )
                elif workout_type == "strength":
                    result = await session.execute(
                        select(Exercise)
                        .where(Exercise.type == ExerciseTypeEnum.STRENGTH)
                        .limit(limit)
                    )
                else:
                    # Fallback: pega qualquer exercício
                    result = await session.execute(
                        select(Exercise).limit(limit)
                    )
                
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Erro ao buscar exercícios: {e}")
            return []
    
    async def get_user_workout_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca histórico de treinos do usuário"""
        try:
            async with get_db_session() as session:
                # Busca usuário
                user_result = await session.execute(
                    select(UserProfile).where(UserProfile.user_id == user_id)
                )
                user = user_result.scalar_one_or_none()
                
                if not user:
                    return []
                
                # Busca sessões com exercícios
                result = await session.execute(
                    select(WorkoutSession)
                    .where(WorkoutSession.user_profile_id == user.id)
                    .order_by(WorkoutSession.session_date.desc())
                    .limit(limit)
                )
                
                sessions = result.scalars().all()
                history = []
                
                for session_obj in sessions:
                    # Busca exercícios desta sessão com nomes
                    exercises_result = await session.execute(
                        select(SessionExercise, Exercise)
                        .join(Exercise, SessionExercise.exercise_id == Exercise.id)
                        .where(SessionExercise.session_id == session_obj.id)
                    )
                    exercises = exercises_result.all()
                    
                    exercise_names = [f"{ex.Exercise.name} ({ex.SessionExercise.duration_minutes}min)" 
                                    for ex in exercises]
                    
                    history.append({
                        'date': session_obj.session_date.isoformat(),
                        'duration': session_obj.duration_minutes,
                        'type': session_obj.session_type,
                        'calories': session_obj.calories_estimated,
                        'notes': session_obj.notes,
                        'exercises_count': len(exercises),
                        'exercises': exercise_names
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Erro ao buscar histórico: {e}")
            return []
# 2. INSTANCIA O REPOSITÓRIO
workout_repo = WorkoutRepository()

class ExerciseRepository:
    """Repositório para exercícios"""
    
    async def get_all_exercises(self) -> List[Exercise]:
        """Busca todos os exercícios"""
        async with get_db_session() as session:
            result = await session.execute(select(Exercise))
            return result.scalars().all()

class WorkoutGenerator:
    """Gerador de treinos personalizados"""
    
    def __init__(self):
        self.exercise_repo = ExerciseRepository()
        self.workout_repo = WorkoutRepository()
    
    async def generate_workout(self, user, workout_type="mixed", duration_minutes=45):
        """Gera treino personalizado simples"""
        return {
            "user_id": user.user_id,
            "workout_type": workout_type,
            "total_duration": duration_minutes,
            "phases": [
                {
                    "name": "Treino Principal",
                    "duration": duration_minutes,
                    "exercises": [
                        {"exercise": {"name": "Exercício Exemplo"}, "duration": duration_minutes}
                    ]
                }
            ]
        }

# Instancia o gerador
workout_generator = WorkoutGenerator()
async def initialize_system():
    """Inicializa o sistema e banco de dados"""
    try:
        logger.info("Inicializando conexão com PostgreSQL...")
        await init_database()
        logger.info("Banco inicializado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar banco: {e}")
        return False
# ADICIONE ESTAS FUNÇÕES no seu server_postgres.py:
class StatisticsRepository:
    """Repositório para estatísticas de treino"""
    
    async def get_user_statistics(self, user_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Calcula estatísticas completas do usuário"""
        try:
            async with get_db_session() as session:
                # Busca usuário
                user_result = await session.execute(
                    select(UserProfile).where(UserProfile.user_id == user_id)
                )
                user = user_result.scalar_one_or_none()
                
                if not user:
                    return {"error": "Usuário não encontrado"}
                
                # Data limite
                cutoff_date = datetime.now() - timedelta(days=days_back)
                
                # Estatísticas básicas de sessões
                session_stats = await session.execute(
                    select(
                        func.count(WorkoutSession.id).label('total_sessions'),
                        func.sum(WorkoutSession.duration_minutes).label('total_duration'),
                        func.avg(WorkoutSession.duration_minutes).label('avg_duration'),
                        func.sum(WorkoutSession.calories_estimated).label('total_calories'),
                        func.avg(WorkoutSession.calories_estimated).label('avg_calories'),
                        func.avg(WorkoutSession.avg_heart_rate).label('avg_heart_rate'),
                        func.max(WorkoutSession.session_date).label('last_session'),
                        func.min(WorkoutSession.session_date).label('first_session')
                    ).where(
                        WorkoutSession.user_profile_id == user.id,
                        WorkoutSession.session_date >= cutoff_date
                    )
                )
                
                stats = session_stats.first()
                
                # Estatísticas por tipo de treino
                type_stats = await session.execute(
                    select(
                        WorkoutSession.session_type,
                        func.count(WorkoutSession.id).label('count'),
                        func.avg(WorkoutSession.duration_minutes).label('avg_duration'),
                        func.sum(WorkoutSession.calories_estimated).label('total_calories')
                    ).where(
                        WorkoutSession.user_profile_id == user.id,
                        WorkoutSession.session_date >= cutoff_date
                    ).group_by(WorkoutSession.session_type)
                )
                
                # Exercícios mais realizados
                exercise_stats = await session.execute(
                    select(
                        Exercise.name,
                        func.count(SessionExercise.id).label('times_performed'),
                        func.sum(SessionExercise.duration_minutes).label('total_time')
                    ).select_from(
                        SessionExercise.__table__
                        .join(WorkoutSession.__table__, SessionExercise.session_id == WorkoutSession.id)
                        .join(Exercise.__table__, SessionExercise.exercise_id == Exercise.id)
                    ).where(
                        WorkoutSession.user_profile_id == user.id,
                        WorkoutSession.session_date >= cutoff_date
                    ).group_by(Exercise.name)
                    .order_by(func.count(SessionExercise.id).desc())
                    .limit(5)
                )
                
                # Frequência semanal
                weekly_frequency = await session.execute(
                    select(
                        func.extract('week', WorkoutSession.session_date).label('week'),
                        func.count(WorkoutSession.id).label('sessions')
                    ).where(
                        WorkoutSession.user_profile_id == user.id,
                        WorkoutSession.session_date >= cutoff_date
                    ).group_by(func.extract('week', WorkoutSession.session_date))
                    .order_by(func.extract('week', WorkoutSession.session_date))
                )
                
                # Monta resultado
                type_breakdown = {row.session_type: {
                    'count': row.count,
                    'avg_duration': round(row.avg_duration or 0, 1),
                    'total_calories': row.total_calories or 0
                } for row in type_stats}
                
                top_exercises = [{
                    'name': row.name,
                    'times_performed': row.times_performed,
                    'total_time': row.total_time or 0
                } for row in exercise_stats]
                
                weekly_data = [{
                    'week': int(row.week),
                    'sessions': row.sessions
                } for row in weekly_frequency]
                
                return {
                    'user_info': {
                        'user_id': user.user_id,
                        'age': user.age,
                        'fitness_level': user.fitness_level.value,
                        'bmi': user.bmi,
                        'bmi_category': user.bmi_category
                    },
                    'period': {
                        'days': days_back,
                        'start_date': cutoff_date.isoformat(),
                        'end_date': datetime.now().isoformat()
                    },
                    'summary': {
                        'total_sessions': stats.total_sessions or 0,
                        'total_duration': stats.total_duration or 0,
                        'avg_duration': round(stats.avg_duration or 0, 1),
                        'total_calories': stats.total_calories or 0,
                        'avg_calories': round(stats.avg_calories or 0, 1),
                        'avg_heart_rate': round(stats.avg_heart_rate or 0, 1),
                        'last_session': stats.last_session.isoformat() if stats.last_session else None,
                        'first_session': stats.first_session.isoformat() if stats.first_session else None
                    },
                    'by_type': type_breakdown,
                    'top_exercises': top_exercises,
                    'weekly_frequency': weekly_data,
                    'consistency': self._calculate_consistency(weekly_data),
                    'progress_indicators': self._calculate_progress_indicators(stats, user)
                }
                
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {"error": str(e)}
    
    def _calculate_consistency(self, weekly_data: List[Dict]) -> Dict[str, Any]:
        """Calcula métricas de consistência"""
        if not weekly_data:
            return {'score': 0, 'status': 'Sem dados'}
        
        total_weeks = len(weekly_data)
        weeks_with_sessions = len([w for w in weekly_data if w['sessions'] > 0])
        avg_sessions_per_week = sum(w['sessions'] for w in weekly_data) / total_weeks
        
        consistency_score = (weeks_with_sessions / total_weeks) * 100
        
        if consistency_score >= 80:
            status = 'Excelente'
        elif consistency_score >= 60:
            status = 'Boa'
        elif consistency_score >= 40:
            status = 'Regular'
        else:
            status = 'Precisa melhorar'
        
        return {
            'score': round(consistency_score, 1),
            'status': status,
            'weeks_active': weeks_with_sessions,
            'total_weeks': total_weeks,
            'avg_sessions_per_week': round(avg_sessions_per_week, 1)
        }
    
    def _calculate_progress_indicators(self, stats, user) -> Dict[str, Any]:
        """Calcula indicadores de progresso"""
        total_sessions = stats.total_sessions or 0
        total_duration = stats.total_duration or 0
        
        # Metas baseadas no nível de fitness
        fitness_targets = {
            'beginner': {'sessions_per_week': 3, 'minutes_per_week': 150},
            'intermediate': {'sessions_per_week': 4, 'minutes_per_week': 200},
            'advanced': {'sessions_per_week': 5, 'minutes_per_week': 300}
        }
        
        target = fitness_targets.get(user.fitness_level.value, fitness_targets['intermediate'])
        weeks_in_period = 4  # Aproximadamente 30 dias = 4 semanas
        
        target_sessions = target['sessions_per_week'] * weeks_in_period
        target_minutes = target['minutes_per_week'] * weeks_in_period
        
        sessions_progress = min((total_sessions / target_sessions) * 100, 100) if target_sessions > 0 else 0
        duration_progress = min((total_duration / target_minutes) * 100, 100) if target_minutes > 0 else 0
        
        return {
            'sessions_completed': total_sessions,
            'sessions_target': target_sessions,
            'sessions_progress': round(sessions_progress, 1),
            'duration_completed': total_duration,
            'duration_target': target_minutes,
            'duration_progress': round(duration_progress, 1),
            'overall_progress': round((sessions_progress + duration_progress) / 2, 1)
        }

# Instancia o repositório
stats_repo = StatisticsRepository()

# Adicione estas ferramentas MCP

@mcp.tool
async def get_workout_statistics(
    user_id: str,
    days_back: int = 30
) -> str:
    """Gera estatísticas completas de treino do usuário"""
    
    try:
        user = await user_repo.get_user_by_id(user_id)
        if not user:
            return f"ERRO: Usuário {user_id} não encontrado"
        
        stats = await stats_repo.get_user_statistics(user_id, days_back)
        
        if 'error' in stats:
            return f"ERRO: {stats['error']}"
        
        # Formata estatísticas
        summary = stats['summary']
        progress = stats['progress_indicators']
        consistency = stats['consistency']
        
        result = f"""ESTATÍSTICAS DE TREINO - {user_id}

RESUMO ({days_back} dias):
• Total de sessões: {summary['total_sessions']}
• Duração total: {summary['total_duration']} minutos
• Duração média por sessão: {summary['avg_duration']} min
• Calorias queimadas: {summary['total_calories']} kcal
• FC média: {summary['avg_heart_rate']} bpm
• Última sessão: {summary['last_session'][:10] if summary['last_session'] else 'Nunca'}

PROGRESSO:
• Sessões: {progress['sessions_completed']}/{progress['sessions_target']} ({progress['sessions_progress']}%)
• Duração: {progress['duration_completed']}/{progress['duration_target']} min ({progress['duration_progress']}%)
• Progresso geral: {progress['overall_progress']}%

CONSISTÊNCIA:
• Score: {consistency['score']}% - {consistency['status']}
• Semanas ativas: {consistency['weeks_active']}/{consistency['total_weeks']}
• Média semanal: {consistency['avg_sessions_per_week']} sessões"""

        # Adiciona tipos de treino se houver dados
        if stats['by_type']:
            result += "\n\nPOR TIPO DE TREINO:"
            for workout_type, data in stats['by_type'].items():
                result += f"\n• {workout_type.title()}: {data['count']} sessões, {data['avg_duration']}min média"
        
        # Adiciona exercícios favoritos
        if stats['top_exercises']:
            result += "\n\nTOP EXERCÍCIOS:"
            for i, exercise in enumerate(stats['top_exercises'][:3], 1):
                result += f"\n{i}. {exercise['name']}: {exercise['times_performed']}x ({exercise['total_time']}min)"
        
        return result
        
    except Exception as e:
        return f"ERRO: {str(e)}"

@mcp.tool
async def get_weekly_progress(user_id: str) -> str:
    """Mostra progresso semanal detalhado"""
    
    try:
        stats = await stats_repo.get_user_statistics(user_id, 30)
        
        if 'error' in stats:
            return f"ERRO: {stats['error']}"
        
        weekly_data = stats['weekly_frequency']
        
        if not weekly_data:
            return f"PROGRESSO SEMANAL - {user_id}\n\nNenhum dado encontrado nos últimos 30 dias."
        
        result = f"PROGRESSO SEMANAL - {user_id}\n\n"
        
        for week_data in weekly_data:
            week_num = week_data['week']
            sessions = week_data['sessions']
            result += f"Semana {week_num}: {sessions} sessões\n"
        
        # Adiciona tendência
        if len(weekly_data) >= 2:
            recent_avg = sum(w['sessions'] for w in weekly_data[-2:]) / 2
            older_avg = sum(w['sessions'] for w in weekly_data[:-2]) / max(len(weekly_data) - 2, 1)
            
            if recent_avg > older_avg:
                trend = "Tendência: CRESCENTE"
            elif recent_avg < older_avg:
                trend = "Tendência: DECRESCENTE"
            else:
                trend = "Tendência: ESTÁVEL"
            
            result += f"\n{trend}"
            result += f"\nMédia recente: {recent_avg:.1f} sessões/semana"
        
        return result
        
    except Exception as e:
        return f"ERRO: {str(e)}"

@mcp.tool
async def compare_monthly_progress(user_id: str) -> str:
    """Compara progresso dos últimos 2 meses"""
    
    try:
        # Estatísticas do último mês
        stats_30d = await stats_repo.get_user_statistics(user_id, 30)
        # Estatísticas dos últimos 60 dias
        stats_60d = await stats_repo.get_user_statistics(user_id, 60)
        
        if 'error' in stats_30d or 'error' in stats_60d:
            return f"ERRO: Dados insuficientes para comparação"
        
        current_month = stats_30d['summary']
        total_60d = stats_60d['summary']
        
        # Calcula estatísticas do mês anterior (60-30 dias)
        prev_sessions = (total_60d['total_sessions'] or 0) - (current_month['total_sessions'] or 0)
        prev_duration = (total_60d['total_duration'] or 0) - (current_month['total_duration'] or 0)
        prev_calories = (total_60d['total_calories'] or 0) - (current_month['total_calories'] or 0)
        
        # Calcula variações percentuais
        sessions_change = ((current_month['total_sessions'] or 0) - prev_sessions) / max(prev_sessions, 1) * 100
        duration_change = ((current_month['total_duration'] or 0) - prev_duration) / max(prev_duration, 1) * 100
        calories_change = ((current_month['total_calories'] or 0) - prev_calories) / max(prev_calories, 1) * 100
        
        def format_change(value):
            if value > 0:
                return f"+{value:.1f}%"
            elif value < 0:
                return f"{value:.1f}%"
            else:
                return "0%"
        
        result = f"""COMPARAÇÃO MENSAL - {user_id}

ÚLTIMO MÊS vs MÊS ANTERIOR:

SESSÕES:
• Atual: {current_month['total_sessions']} sessões
• Anterior: {prev_sessions} sessões
• Variação: {format_change(sessions_change)}

DURAÇÃO:
• Atual: {current_month['total_duration']} minutos
• Anterior: {prev_duration} minutos
• Variação: {format_change(duration_change)}

CALORIAS:
• Atual: {current_month['total_calories']} kcal
• Anterior: {prev_calories} kcal
• Variação: {format_change(calories_change)}

PERFORMANCE GERAL:"""
        
        improvements = 0
        if sessions_change > 0: improvements += 1
        if duration_change > 0: improvements += 1
        if calories_change > 0: improvements += 1
        
        if improvements >= 2:
            result += "\nSTATUS: MELHORANDO - Continue assim!"
        elif improvements == 1:
            result += "\nSTATUS: ESTÁVEL - Foco na consistência"
        else:
            result += "\nSTATUS: PRECISA ATENÇÃO - Revise sua rotina"
        
        return result
        
    except Exception as e:
        return f"ERRO: {str(e)}"
@mcp.tool
async def generate_personalized_workout(
    user_id: str,
    workout_type: str = "mixed",
    duration_minutes: int = 45
) -> str:
    """Gera e SALVA treino personalizado baseado em exercícios reais da academia"""
    
    try:
        # Busca usuário
        user = await user_repo.get_user_by_id(user_id)
        if not user:
            return f"ERRO: Usuário {user_id} não encontrado"
        
        # Busca exercícios reais da tabela exercises
        real_exercises = await workout_repo.get_random_exercises_by_type(workout_type, 3)
        
        if not real_exercises:
            return f"ERRO: Nenhum exercício encontrado. Execute 'seed_database_tool' primeiro!"
        
        # Calcula distribuição do tempo
        warm_up_time = 10
        cool_down_time = 10
        main_time = duration_minutes - warm_up_time - cool_down_time
        exercise_time = main_time // len(real_exercises)
        
        # Prepara dados do treino com exercícios reais
        exercises_data = []
        for exercise in real_exercises:
            exercises_data.append({
                'name': exercise.name,
                'duration': exercise_time,
                'sets': 3 if exercise.type == ExerciseTypeEnum.STRENGTH else 1,
                'notes': f"{exercise.type.value} - {exercise.description}"
            })
        
        workout_data = {
            'workout_type': workout_type,
            'duration_minutes': duration_minutes,
            'calories_estimated': duration_minutes * 8,  # Estimativa
            'notes': f'Treino {workout_type} com exercícios de academia',
            'exercises': exercises_data
        }
        
        # SALVA NO BANCO
        saved = await workout_repo.save_workout_session(user_id, workout_data)
        
        if saved:
            exercise_list = "\n".join([f"- {ex['name']} ({ex['duration']}min)" 
                                     for ex in exercises_data])
            
            return f"""TREINO GERADO E SALVO!

Usuário: {user.user_id}
Tipo: {workout_type}
Duração: {duration_minutes} minutos

EXERCÍCIOS SELECIONADOS:
{exercise_list}

TREINO SALVO NO BANCO POSTGRESQL!
Use 'get_workout_history' para ver seu histórico!"""
        else:
            return f"ERRO: Não foi possível salvar o treino no banco"
        
    except Exception as e:
        return f"ERRO: {str(e)}"
@mcp.tool
async def complete_workout_session(
    user_id: str,
    duration: int = 45,
    perceived_exertion: int = 5,
    notes: str = "Treino concluído"
) -> str:
    """Marca treino como concluído e SALVA no banco"""
    
    try:
        # Dados da sessão completa
        workout_data = {
            'workout_type': 'completed',
            'duration_minutes': duration,
            'perceived_exertion': perceived_exertion,
            'calories_estimated': duration * 7,  # Estimativa
            'notes': notes,
            'exercises': [
                {'name': 'Treino Completo', 'duration': duration}
            ]
        }
        
        # SALVA NO BANCO
        saved = await workout_repo.save_workout_session(user_id, workout_data)
        
        if saved:
            return f"""TREINO CONCLUÍDO E SALVO!

Usuário: {user_id}
Duração: {duration} minutos
Esforço Percebido: {perceived_exertion}/10
Observações: {notes}

TREINO SALVO NO BANCO POSTGRESQL!
Parabéns por completar seu treino!"""
        else:
            return f"ERRO: Não foi possível salvar a sessão no banco"
        
    except Exception as e:
        return f"ERRO: {str(e)}"

@mcp.tool
async def get_workout_history(user_id: str) -> str:
    """Mostra histórico REAL de treinos do banco PostgreSQL"""
    
    try:
        user = await user_repo.get_user_by_id(user_id)
        if not user:
            return f"ERRO: Usuário {user_id} não encontrado"
        
        # BUSCA HISTÓRICO REAL DO BANCO
        history = await workout_repo.get_user_workout_history(user_id, limit=10)
        
        if not history:
            return f"""HISTÓRICO DE TREINOS - {user_id}

Nenhum treino encontrado no banco de dados.
Use 'generate_personalized_workout' para criar seu primeiro treino!"""
        
        # Formata histórico
        history_text = f"HISTÓRICO DE TREINOS - {user_id}\n\n"
        
        for i, session in enumerate(history, 1):
            date = session['date'][:10]  # Apenas data
            history_text += f"{i}. {session['type'].title()} - {session['duration']}min"
            if session['calories']:
                history_text += f" ({session['calories']} cal)"
            history_text += f" - {date}\n"
        
        history_text += f"\nTotal de treinos: {len(history)}"
        history_text += "\nUse 'generate_personalized_workout' para criar novo treino!"
        
        return history_text
        
    except Exception as e:
        return f"ERRO: {str(e)}"


@mcp.tool
async def create_user_profile(
    user_id: str,
    age: int,
    weight: float,
    height: float,
    fitness_level: str,
    gender: str = None
) -> str:
    """Cria um novo perfil de usuário no banco PostgreSQL"""
    
    try:
        # Validações
        if age < 13 or age > 120:
            return "ERRO: Idade deve estar entre 13 e 120 anos"
        
        if weight < 30 or weight > 300:
            return "ERRO: Peso deve estar entre 30 e 300 kg"
        
        if height < 1.0 or height > 2.5:
            return "ERRO: Altura deve estar entre 1.0 e 2.5 metros"
        
        if fitness_level not in ["beginner", "intermediate", "advanced"]:
            return "ERRO: Nível deve ser: beginner, intermediate ou advanced"
        
        # Verifica se usuário já existe
        existing_user = await user_repo.get_user_by_id(user_id)
        if existing_user:
            return f"ERRO: Usuário {user_id} já existe"
        
        # Prepara dados
        user_data = {
            "user_id": user_id,
            "age": age,
            "weight": weight,
            "height": height,
            "fitness_level": FitnessLevelEnum(fitness_level)
        }
        
        # Adiciona gênero se fornecido
        if gender:
            gender_map = {"male": GenderEnum.MALE, "female": GenderEnum.FEMALE, "other": GenderEnum.OTHER}
            if gender.lower() in gender_map:
                user_data["gender"] = gender_map[gender.lower()]
        
        # Cria usuário no banco
        user = await user_repo.create_user(user_data)
        
        return f"""PERFIL CRIADO COM SUCESSO!

Usuário: {user.user_id}
ID Interno: {str(user.id)}
Dados Biométricos:
   • Idade: {age} anos
   • Peso: {weight} kg
   • Altura: {height} m
   • Nível: {fitness_level}
   • Gênero: {gender or "não informado"}

Perfil salvo no PostgreSQL!
Criado em: {user.created_at.isoformat()}

Use 'calculate_heart_rate_zones' para calcular suas zonas de FC"""
        
    except Exception as e:
        logger.error(f"Erro ao criar usuário {user_id}: {e}")
        return f"ERRO: {str(e)}"

@mcp.tool
async def get_user_profile(user_id: str) -> str:
    """Busca perfil de usuário no banco PostgreSQL"""
    
    try:
        user = await user_repo.get_user_by_id(user_id)
        if not user:
            return f"ERRO: Usuário {user_id} não encontrado"
        
        return f"""PERFIL DO USUÁRIO

Usuário: {user.user_id}
ID Interno: {str(user.id)}

Dados Biométricos:
   • Idade: {user.age} anos
   • Peso: {user.weight} kg
   • Altura: {user.height} m
   • Nível: {user.fitness_level.value}
   • Gênero: {user.gender.value if user.gender else "não informado"}

Dados Cardíacos:
   • FC Repouso: {user.resting_heart_rate or "não informado"} bpm
   • FC Máxima: {user.max_heart_rate or "não informado"} bpm

Criado em: {user.created_at.isoformat()}
Atualizado em: {user.updated_at.isoformat() if user.updated_at else "nunca"}"""
        
    except Exception as e:
        logger.error(f"Erro ao buscar usuário {user_id}: {e}")
        return f"ERRO: {str(e)}"

@mcp.tool
async def list_all_users(limit: int = 10) -> str:
    """Lista todos os usuários cadastrados no PostgreSQL"""
    
    try:
        users = await user_repo.list_users(limit=limit)
        
        if not users:
            return "Nenhum usuário encontrado no banco de dados."
        
        response = f"USUÁRIOS CADASTRADOS ({len(users)} encontrados)\n\n"
        
        for user in users:
            response += f"""Usuário: {user.user_id}
   • Idade: {user.age} anos
   • Nível: {user.fitness_level.value}
   • Criado: {user.created_at.isoformat()}

"""
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {e}")
        return f"ERRO: {str(e)}"

@mcp.tool
def calculate_heart_rate_zones(age: int, resting_hr: int) -> str:
    """Calcula zonas de frequência cardíaca baseadas na idade e FC de repouso"""
    
    # Validações
    if age < 13 or age > 120:
        return "ERRO: Idade deve estar entre 13 e 120 anos"
    
    if resting_hr < 30 or resting_hr > 120:
        return "ERRO: FC de repouso deve estar entre 30 e 120 bpm"
    
    # Calcula FC máxima
    max_hr = 220 - age
    hr_reserve = max_hr - resting_hr
    
    # Calcula zonas usando fórmula de Karvonen
    zones = {
        "Zona 1 - Recuperação": (resting_hr + int(0.5 * hr_reserve), resting_hr + int(0.6 * hr_reserve)),
        "Zona 2 - Aeróbica": (resting_hr + int(0.6 * hr_reserve), resting_hr + int(0.7 * hr_reserve)),
        "Zona 3 - Tempo": (resting_hr + int(0.7 * hr_reserve), resting_hr + int(0.8 * hr_reserve)),
        "Zona 4 - Anaeróbica": (resting_hr + int(0.8 * hr_reserve), resting_hr + int(0.9 * hr_reserve)),
        "Zona 5 - VO2 Max": (resting_hr + int(0.9 * hr_reserve), max_hr)
    }
    
    response = f"""ZONAS DE FREQUÊNCIA CARDÍACA

Perfil: {age} anos, FC repouso {resting_hr} bpm
FC Máxima Teórica: {max_hr} bpm

Suas Zonas:"""
    
    for zone_name, (min_hr, max_hr_zone) in zones.items():
        response += f"""
{zone_name}: {min_hr}-{max_hr_zone} bpm"""
    
    response += f"""

Recomendações:
   • Zona 1-2: Exercícios de base e recuperação
   • Zona 3: Ritmo de prova e tempo
   • Zona 4-5: Treinos intervalados intensos"""
    
    return response

@mcp.tool
async def import_dataset_users(csv_file_path: str = None) -> str:
    """Importa usuários do dataset CSV para o PostgreSQL"""
    
    if not csv_file_path:
        csv_file_path = "gym_members_exercise_tracking.csv"
    
    try:
        import pandas as pd
        
        # Verifica se arquivo existe
        if not os.path.exists(csv_file_path):
            return f"ERRO: Arquivo {csv_file_path} não encontrado"
        
        # Carrega dataset
        df = pd.read_csv(csv_file_path)
        imported_count = 0
        errors = []
        
        # Importa até 20 usuários do dataset
        for index, row in df.head(20).iterrows():
            try:
                user_data = {
                    "user_id": f"gym_member_{index + 1:04d}",
                    "age": int(row['Age']),
                    "weight": float(row['Weight (kg)']),
                    "height": float(row['Height (m)']),
                    "fitness_level": FitnessLevelEnum.INTERMEDIATE,  # Padrão
                    "resting_heart_rate": int(row['Resting_BPM']),
                    "max_heart_rate": int(row['Max_BPM'])
                }
                
                # Mapeia gênero
                if row['Gender'].lower() == 'male':
                    user_data["gender"] = GenderEnum.MALE
                elif row['Gender'].lower() == 'female':
                    user_data["gender"] = GenderEnum.FEMALE
                
                # Mapeia nível baseado na experiência
                exp_level = int(row.get('Experience_Level', 2))
                if exp_level == 1:
                    user_data["fitness_level"] = FitnessLevelEnum.BEGINNER
                elif exp_level == 3:
                    user_data["fitness_level"] = FitnessLevelEnum.ADVANCED
                
                # Verifica se usuário já existe
                existing = await user_repo.get_user_by_id(user_data["user_id"])
                if not existing:
                    await user_repo.create_user(user_data)
                    imported_count += 1
                
            except Exception as e:
                errors.append(f"Linha {index}: {str(e)}")
        
        response = f"""DATASET IMPORTADO COM SUCESSO!

Dados processados: {min(20, len(df))} registros
Usuários importados: {imported_count}

Dados salvos no PostgreSQL com:
   • Perfis biométricos completos
   • Dados de frequência cardíaca
   • Níveis de experiência mapeados

Use 'list_all_users' para ver os usuários importados"""
        
        if errors:
            response += f"\n\nErros encontrados ({len(errors)}):"
            for error in errors[:5]:  # Mostra apenas os primeiros 5
                response += f"\n   • {error}"
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao importar dataset: {e}")
        return f"ERRO: {str(e)}"

@mcp.tool
async def seed_database_tool() -> str:
    """Popula o banco com exercícios e dados iniciais"""
    
    try:
        from fitness_assistant.database.connection import seed_database
        
        await seed_database()
        
        return """SEED EXECUTADO COM SUCESSO!

Dados iniciais criados:
   • Exercícios básicos por categoria
   • Configurações padrão do sistema
   • Dados de exemplo para testes

O banco agora está pronto para uso completo!

Use 'list_all_users' para verificar dados dos usuários
Use 'create_user_profile' para começar a usar o sistema"""
        
    except Exception as e:
        logger.error(f"Erro no seed: {e}")
        return f"ERRO: {str(e)}"

@mcp.tool
async def reset_database_tool() -> str:
    """Reseta o banco de dados (CUIDADO: apaga todos os dados)"""
    
    try:
        from fitness_assistant.database.connection import reset_database
        
        await reset_database()
        
        return """BANCO RESETADO COM SUCESSO!

ATENÇÃO: Todos os dados foram removidos!

Para recriar dados iniciais, execute:
   • seed_database_tool para criar exercícios
   • import_dataset_users para importar usuários do CSV

O banco está agora completamente limpo."""
        
    except Exception as e:
        logger.error(f"Erro no reset: {e}")
        return f"ERRO: {str(e)}"
    """Função principal"""
    print("Fitness Assistant MCP Server com PostgreSQL")
    print("Ferramentas disponíveis:")
    print("   • create_user_profile - Criar perfil no banco")
    print("   • get_user_profile - Buscar perfil no banco")
    print("   • list_all_users - Listar usuários do banco")
    print("   • calculate_heart_rate_zones - Calcular zonas FC")
    print("   • import_dataset_users - Importar dataset para banco")
    print("\nServidor rodando - teste no Claude Desktop!")
    
    try:
        mcp.run()
    except KeyboardInterrupt:
        print("\nServidor parado")
def main():
    """Função principal"""
    print("Fitness Assistant MCP Server com PostgreSQL")
    print("Ferramentas disponíveis:")
    print("   • create_user_profile - Criar perfil no banco")
    print("   • get_user_profile - Buscar perfil no banco")
    print("   • list_all_users - Listar usuários do banco")
    print("   • calculate_heart_rate_zones - Calcular zonas FC")
    print("   • import_dataset_users - Importar dataset para banco")
    print("   • seed_database_tool - Popular banco com dados iniciais")
    print("   • reset_database_tool - Resetar banco (CUIDADO!)")
    # ADICIONE ESTAS 3 LINHAS:
    print("   • generate_personalized_workout - Gerar treino personalizado")
    print("   • complete_workout_session - Marcar treino como concluído")
    print("   • get_workout_history - Ver histórico de treinos")
    print("\nServidor rodando - teste no Claude Desktop!")
    
    try:
        mcp.run()
    except KeyboardInterrupt:
        print("\nServidor parado")
if __name__ == "__main__":
    main()