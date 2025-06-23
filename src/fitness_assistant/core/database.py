"""
Simulação de banco de dados em memória para desenvolvimento
Em produção, substituir por banco real (PostgreSQL, MongoDB, etc.)
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os
from ..models.user import UserProfile
from ..models.exercise import Exercise, ExerciseRecommendation

# Armazenamento em memória
_user_profiles: Dict[str, UserProfile] = {}
_workout_sessions: Dict[str, List[Dict]] = {}
_exercises_database: Dict[str, Exercise] = {}
_user_analytics: Dict[str, Dict] = {}

# Caminhos para persistência (desenvolvimento)
DATA_DIR = os.path.join(os.path.dirname(__file__), "../../../data")
PROFILES_FILE = os.path.join(DATA_DIR, "user_profiles.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "workout_sessions.json")
EXERCISES_FILE = os.path.join(DATA_DIR, "exercises_database.json")

def init_database():
    """Inicializa o banco de dados e carrega dados existentes"""
    global _user_profiles, _workout_sessions, _exercises_database
    
    # Cria diretório de dados se não existir
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Carrega dados existentes
    _load_user_profiles()
    _load_workout_sessions()
    _load_exercises_database()
    
    print("✅ Database inicializado com sucesso")

def _load_user_profiles():
    """Carrega perfis de usuários do arquivo"""
    global _user_profiles
    try:
        if os.path.exists(PROFILES_FILE):
            with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _user_profiles = {
                    user_id: UserProfile(**profile_data) 
                    for user_id, profile_data in data.items()
                }
            print(f"📊 Carregados {len(_user_profiles)} perfis de usuários")
    except Exception as e:
        print(f"⚠️ Erro ao carregar perfis: {e}")
        _user_profiles = {}

def _save_user_profiles():
    """Salva perfis de usuários no arquivo"""
    try:
        data = {
            user_id: profile.dict() 
            for user_id, profile in _user_profiles.items()
        }
        with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    except Exception as e:
        print(f"⚠️ Erro ao salvar perfis: {e}")

def _load_workout_sessions():
    """Carrega sessões de treino do arquivo"""
    global _workout_sessions
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
                _workout_sessions = json.load(f)
            total_sessions = sum(len(sessions) for sessions in _workout_sessions.values())
            print(f"📊 Carregadas {total_sessions} sessões de treino")
    except Exception as e:
        print(f"⚠️ Erro ao carregar sessões: {e}")
        _workout_sessions = {}

def _save_workout_sessions():
    """Salva sessões de treino no arquivo"""
    try:
        with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(_workout_sessions, f, indent=2, ensure_ascii=False, default=str)
    except Exception as e:
        print(f"⚠️ Erro ao salvar sessões: {e}")

def _load_exercises_database():
    """Carrega base de exercícios do arquivo"""
    global _exercises_database
    try:
        if os.path.exists(EXERCISES_FILE):
            with open(EXERCISES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _exercises_database = {
                    ex_id: Exercise(**ex_data) 
                    for ex_id, ex_data in data.items()
                }
            print(f"📊 Carregados {len(_exercises_database)} exercícios")
        else:
            # Cria base inicial se não existir
            _create_initial_exercises()
    except Exception as e:
        print(f"⚠️ Erro ao carregar exercícios: {e}")
        _exercises_database = {}

# === FUNÇÕES CRUD PARA USUÁRIOS ===

def get_user_profile(user_id: str) -> Optional[UserProfile]:
    """Recupera perfil do usuário"""
    return _user_profiles.get(user_id)

def save_user_profile(profile: UserProfile) -> bool:
    """Salva ou atualiza perfil do usuário"""
    try:
        _user_profiles[profile.user_id] = profile
        _save_user_profiles()
        return True
    except Exception as e:
        print(f"Erro ao salvar perfil {profile.user_id}: {e}")
        return False

def delete_user_profile(user_id: str) -> bool:
    """Remove perfil do usuário"""
    try:
        if user_id in _user_profiles:
            del _user_profiles[user_id]
            _save_user_profiles()
            return True
        return False
    except Exception as e:
        print(f"Erro ao deletar perfil {user_id}: {e}")
        return False

def list_all_users() -> List[str]:
    """Lista todos os IDs de usuários"""
    return list(_user_profiles.keys())

# === FUNÇÕES CRUD PARA SESSÕES DE TREINO ===

def save_workout_session(user_id: str, session_data: Dict[str, Any]) -> bool:
    """Salva uma sessão de treino"""
    try:
        if user_id not in _workout_sessions:
            _workout_sessions[user_id] = []
        
        session_data['id'] = f"{user_id}_{datetime.now().isoformat()}"
        _workout_sessions[user_id].append(session_data)
        _save_workout_sessions()
        return True
    except Exception as e:
        print(f"Erro ao salvar sessão para {user_id}: {e}")
        return False

def get_user_sessions(user_id: str, limit: int = None) -> List[Dict[str, Any]]:
    """Recupera sessões de treino do usuário"""
    sessions = _workout_sessions.get(user_id, [])
    if limit:
        return sessions[-limit:]  # Últimas N sessões
    return sessions

def get_sessions_by_date_range(user_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
    """Recupera sessões em um período específico"""
    sessions = _workout_sessions.get(user_id, [])
    filtered = []
    
    for session in sessions:
        session_date = datetime.fromisoformat(session['date'])
        if start_date <= session_date <= end_date:
            filtered.append(session)
    
    return filtered

# === FUNÇÕES CRUD PARA EXERCÍCIOS ===

def get_exercise(exercise_id: str) -> Optional[Exercise]:
    """Recupera um exercício específico"""
    return _exercises_database.get(exercise_id)

def get_exercises_by_type(exercise_type: str) -> List[Exercise]:
    """Recupera exercícios por tipo"""
    return [
        exercise for exercise in _exercises_database.values()
        if exercise.type == exercise_type
    ]

def get_exercises_by_muscle_group(muscle_group: str) -> List[Exercise]:
    """Recupera exercícios que trabalham um grupo muscular"""
    return [
        exercise for exercise in _exercises_database.values()
        if muscle_group.lower() in [mg.lower() for mg in exercise.muscle_groups]
    ]

def search_exercises(query: str) -> List[Exercise]:
    """Busca exercícios por nome ou descrição"""
    query = query.lower()
    return [
        exercise for exercise in _exercises_database.values()
        if query in exercise.name.lower() or query in exercise.description.lower()
    ]

def add_exercise(exercise: Exercise) -> bool:
    """Adiciona um novo exercício à base"""
    try:
        _exercises_database[exercise.id] = exercise
        _save_exercises_database()
        return True
    except Exception as e:
        print(f"Erro ao adicionar exercício {exercise.id}: {e}")
        return False

def _save_exercises_database():
    """Salva base de exercícios no arquivo"""
    try:
        data = {
            ex_id: exercise.dict() 
            for ex_id, exercise in _exercises_database.items()
        }
        with open(EXERCISES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    except Exception as e:
        print(f"⚠️ Erro ao salvar exercícios: {e}")

# === ANÁLISES E ESTATÍSTICAS ===

def get_user_analytics(user_id: str) -> Dict[str, Any]:
    """Calcula estatísticas do usuário"""
    if user_id not in _user_analytics:
        _calculate_user_analytics(user_id)
    return _user_analytics.get(user_id, {})

def _calculate_user_analytics(user_id: str):
    """Calcula e armazena analytics do usuário"""
    sessions = get_user_sessions(user_id)
    profile = get_user_profile(user_id)
    
    if not sessions:
        _user_analytics[user_id] = {
            "total_sessions": 0,
            "total_duration": 0,
            "avg_duration": 0,
            "total_calories": 0,
            "last_workout": None
        }
        return
    
    total_sessions = len(sessions)
    total_duration = sum(s.get('duration_minutes', 0) for s in sessions)
    total_calories = sum(s.get('calories_estimated', 0) for s in sessions)
    
    _user_analytics[user_id] = {
        "total_sessions": total_sessions,
        "total_duration": total_duration,
        "avg_duration": total_duration / total_sessions if total_sessions > 0 else 0,
        "total_calories": total_calories,
        "avg_calories": total_calories / total_sessions if total_sessions > 0 else 0,
        "last_workout": sessions[-1]['date'] if sessions else None,
        "streak_days": _calculate_workout_streak(sessions),
        "favorite_exercises": _get_favorite_exercises(sessions),
        "progress_trend": _calculate_progress_trend(sessions)
    }

def _calculate_workout_streak(sessions: List[Dict[str, Any]]) -> int:
    """Calcula sequência de dias com treino"""
    if not sessions:
        return 0
    
    # Ordena sessões por data
    sorted_sessions = sorted(sessions, key=lambda x: x['date'], reverse=True)
    
    streak = 0
    current_date = datetime.now().date()
    
    for session in sorted_sessions:
        session_date = datetime.fromisoformat(session['date']).date()
        
        # Se é hoje ou ontem, continua a sequência
        if (current_date - session_date).days <= streak + 1:
            streak += 1
            current_date = session_date
        else:
            break
    
    return streak

def _get_favorite_exercises(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identifica exercícios favoritos baseado na frequência"""
    exercise_count = {}
    
    for session in sessions:
        for exercise in session.get('exercises', []):
            name = exercise.get('name', 'Unknown')
            exercise_count[name] = exercise_count.get(name, 0) + 1
    
    # Ordena por frequência
    sorted_exercises = sorted(exercise_count.items(), key=lambda x: x[1], reverse=True)
    
    return [
        {"name": name, "count": count} 
        for name, count in sorted_exercises[:5]  # Top 5
    ]

def _calculate_progress_trend(sessions: List[Dict[str, Any]]) -> str:
    """Calcula tendência de progresso"""
    if len(sessions) < 2:
        return "insufficient_data"
    
    # Analisa últimas 4 semanas vs 4 semanas anteriores
    recent_sessions = sessions[-8:] if len(sessions) >= 8 else sessions
    
    if len(recent_sessions) <= len(sessions) // 2:
        return "improving"
    elif len(recent_sessions) >= len(sessions) * 0.8:
        return "stable"
    else:
        return "declining"

# === INICIALIZAÇÃO DE DADOS ===

def _create_initial_exercises():
    """Cria base inicial de exercícios"""
    from ..models.exercise import Exercise, ExerciseType, IntensityLevel, Equipment
    
    initial_exercises = [
        {
            "id": "walk_light",
            "name": "Caminhada Leve",
            "type": ExerciseType.CARDIO,
            "description": "Caminhada em ritmo confortável",
            "instructions": [
                "Mantenha postura ereta",
                "Braços relaxados, movimento natural",
                "Respire de forma natural e ritmada"
            ],
            "muscle_groups": ["pernas", "core"],
            "equipment_needed": [Equipment.NONE],
            "difficulty_level": IntensityLevel.LOW,
            "duration_range": (10, 60),
            "calories_per_minute": {"beginner": 3.5, "intermediate": 4.0, "advanced": 4.5},
            "contraindications": [],
            "modifications": ["Use bastão para apoio se necessário"],
            "safety_notes": ["Hidrate-se adequadamente", "Use calçados apropriados"]
        },
        {
            "id": "squat_bodyweight",
            "name": "Agachamento Corpo Livre",
            "type": ExerciseType.STRENGTH,
            "description": "Agachamento usando apenas o peso corporal",
            "instructions": [
                "Pés na largura dos ombros",
                "Desça até coxas paralelas ao chão",
                "Mantenha joelhos alinhados com os pés"
            ],
            "muscle_groups": ["quadriceps", "glúteos", "core"],
            "equipment_needed": [Equipment.NONE],
            "difficulty_level": IntensityLevel.MODERATE,
            "duration_range": (5, 20),
            "calories_per_minute": {"beginner": 5.0, "intermediate": 6.0, "advanced": 7.0},
            "contraindications": ["lesões no joelho", "problemas na lombar"],
            "modifications": ["Use cadeira para apoio", "Agachamento parcial"],
            "safety_notes": ["Não force além do confortável", "Mantenha core contraído"]
        },
        {
            "id": "plank",
            "name": "Prancha",
            "type": ExerciseType.STRENGTH,
            "description": "Exercício isométrico para fortalecimento do core",
            "instructions": [
                "Apoie-se nos antebraços e pontas dos pés",
                "Mantenha corpo em linha reta",
                "Respire normalmente durante o exercício"
            ],
            "muscle_groups": ["core", "ombros", "braços"],
            "equipment_needed": [Equipment.NONE],
            "difficulty_level": IntensityLevel.MODERATE,
            "duration_range": (1, 10),
            "calories_per_minute": {"beginner": 4.0, "intermediate": 5.0, "advanced": 6.0},
            "contraindications": ["lesões no ombro", "problemas na lombar"],
            "modifications": ["Prancha nos joelhos", "Prancha inclinada"],
            "safety_notes": ["Não deixe quadril cair", "Pare se sentir dor"]
        }
    ]
    
    for ex_data in initial_exercises:
        exercise = Exercise(**ex_data)
        _exercises_database[exercise.id] = exercise
    
    _save_exercises_database()
    print(f"✅ Criados {len(initial_exercises)} exercícios iniciais")

# === UTILITÁRIOS ===

def get_database_stats() -> Dict[str, Any]:
    """Retorna estatísticas gerais do banco"""
    total_sessions = sum(len(sessions) for sessions in _workout_sessions.values())
    
    return {
        "total_users": len(_user_profiles),
        "total_exercises": len(_exercises_database),
        "total_sessions": total_sessions,
        "active_users_last_30_days": _count_active_users(30)
    }

def _count_active_users(days: int) -> int:
    """Conta usuários ativos nos últimos N dias"""
    cutoff_date = datetime.now() - timedelta(days=days)
    active_users = 0
    
    for user_id, sessions in _workout_sessions.items():
        for session in sessions:
            session_date = datetime.fromisoformat(session['date'])
            if session_date > cutoff_date:
                active_users += 1
                break
    
    return active_users

def backup_database() -> bool:
    """Cria backup dos dados"""
    try:
        import shutil
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(DATA_DIR, f"backup_{timestamp}")
        
        os.makedirs(backup_dir, exist_ok=True)
        
        if os.path.exists(PROFILES_FILE):
            shutil.copy2(PROFILES_FILE, backup_dir)
        if os.path.exists(SESSIONS_FILE):
            shutil.copy2(SESSIONS_FILE, backup_dir)
        if os.path.exists(EXERCISES_FILE):
            shutil.copy2(EXERCISES_FILE, backup_dir)
        
        print(f"✅ Backup criado em {backup_dir}")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        return False