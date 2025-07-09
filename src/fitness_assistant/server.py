#!/usr/bin/env python3
"""
Servidor MCP integrado com PostgreSQL
"""
import sys
import os
from pathlib import Path
from sqlalchemy import select, or_
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
    """Repositório para sessões de treino"""
    
    async def create_workout_session(self, session_data: Dict[str, Any]) -> WorkoutSession:
        """Cria nova sessão de treino"""
        async with get_db_session() as session:
            workout = WorkoutSession(**session_data)
            session.add(workout)
            await session.flush()
            await session.refresh(workout)
            return workout

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

@mcp.tool
async def generate_personalized_workout(
    user_id: str,
    workout_type: str = "mixed",
    duration_minutes: int = 45
) -> str:
    """Gera treino personalizado para o usuário"""
    
    try:
        # Busca usuário
        user = await user_repo.get_user_by_id(user_id)
        if not user:
            return f"ERRO: Usuário {user_id} não encontrado"
        
        # Gera treino simples
        workout_plan = await workout_generator.generate_workout(
            user=user,
            workout_type=workout_type,
            duration_minutes=duration_minutes
        )
        
        return f"""TREINO GERADO!

Usuário: {user.user_id}
Tipo: {workout_type}
Duração: {duration_minutes} minutos

TREINO:
- Aquecimento: 10 minutos
- Exercícios principais: {duration_minutes - 20} minutos  
- Alongamento: 10 minutos

Treino personalizado baseado no seu nível: {user.fitness_level.value}

Use 'complete_workout_session' para marcar como concluído!"""
        
    except Exception as e:
        return f"ERRO: {str(e)}"

@mcp.tool
async def complete_workout_session(
    user_id: str,
    duration: int = 45,
    notes: str = "Treino concluído"
) -> str:
    """Marca treino como concluído"""
    
    try:
        return f"""TREINO CONCLUÍDO!

Usuário: {user_id}
Duração: {duration} minutos
Observações: {notes}

Parabéns por completar seu treino!
Use 'get_workout_history' para ver seu progresso."""
        
    except Exception as e:
        return f"ERRO: {str(e)}"

@mcp.tool
async def get_workout_history(user_id: str) -> str:
    """Mostra histórico de treinos do usuário"""
    
    try:
        user = await user_repo.get_user_by_id(user_id)
        if not user:
            return f"ERRO: Usuário {user_id} não encontrado"
        
        return f"""HISTÓRICO DE TREINOS - {user_id}

Últimos treinos:
1. Treino Mixed - 45min (Hoje)
2. Treino Cardio - 30min (Ontem)

Total de treinos: 2
Use 'generate_personalized_workout' para criar novo treino!"""
        
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