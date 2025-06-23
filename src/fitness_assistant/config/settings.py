"""
Configurações do sistema
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    """Configurações principais do sistema"""
    
    # Informações da aplicação
    app_name: str = "Assistente de Treino Físico"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Configurações de banco de dados
    database_type: str = Field(default="memory", env="DATABASE_TYPE")  # memory, postgresql, mongodb
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # Caminhos de arquivos
    data_directory: str = Field(default="data", env="DATA_DIR")
    backup_directory: str = Field(default="backups", env="BACKUP_DIR")
    
    # Configurações de saúde e segurança
    max_heart_rate_warning: int = Field(default=180, env="MAX_HR_WARNING")
    min_age_requirement: int = Field(default=13, env="MIN_AGE")
    max_age_limit: int = Field(default=120, env="MAX_AGE")
    
    # Configurações de exercícios
    default_session_duration: int = Field(default=30, env="DEFAULT_SESSION_DURATION")
    max_session_duration: int = Field(default=180, env="MAX_SESSION_DURATION")
    calories_calculation_method: str = Field(default="mets", env="CALORIES_METHOD")
    
    # Configurações de analytics
    analytics_retention_days: int = Field(default=365, env="ANALYTICS_RETENTION")
    progress_analysis_weeks: int = Field(default=4, env="PROGRESS_WEEKS")
    
    # Configurações de notificações
    enable_safety_alerts: bool = Field(default=True, env="ENABLE_SAFETY_ALERTS")
    enable_progress_notifications: bool = Field(default=True, env="ENABLE_PROGRESS_NOTIFICATIONS")
    
    # Configurações MCP
    mcp_server_name: str = Field(default="fitness-assistant", env="MCP_SERVER_NAME")
    mcp_server_description: str = Field(default="Assistente inteligente para recomendações de exercícios", env="MCP_DESCRIPTION")
    
    # Configurações de logs
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

class HeartRateZones(BaseSettings):
    """Configurações específicas para zonas de FC"""
    
    # Percentuais para cálculo das zonas (método Karvonen)
    zone_1_min: float = 0.5  # 50% FC Reserve
    zone_1_max: float = 0.6  # 60% FC Reserve
    
    zone_2_min: float = 0.6  # 60% FC Reserve
    zone_2_max: float = 0.7  # 70% FC Reserve
    
    zone_3_min: float = 0.7  # 70% FC Reserve
    zone_3_max: float = 0.8  # 80% FC Reserve
    
    zone_4_min: float = 0.8  # 80% FC Reserve
    zone_4_max: float = 0.9  # 90% FC Reserve
    
    zone_5_min: float = 0.9  # 90% FC Reserve
    zone_5_max: float = 1.0  # 100% FC Reserve
    
    # FC máxima padrão por idade (Fox formula)
    max_hr_formula: str = "220-age"  # Alternativas: "208-0.7*age", "211-0.64*age"
    
    # FC de repouso padrão por idade/fitness
    default_resting_hr: dict = {
        "beginner": {"young": 70, "middle": 75, "senior": 80},
        "intermediate": {"young": 65, "middle": 68, "senior": 72},
        "advanced": {"young": 55, "middle": 60, "senior": 65}
    }

class ExerciseSettings(BaseSettings):
    """Configurações para recomendações de exercícios"""
    
    # Durações recomendadas por tipo de exercício (minutos)
    cardio_duration_range: tuple = (10, 60)
    strength_duration_range: tuple = (15, 45)
    flexibility_duration_range: tuple = (5, 30)
    hiit_duration_range: tuple = (10, 30)
    
    # Progressões por nível de fitness
    beginner_max_intensity: str = "moderate"
    intermediate_max_intensity: str = "high"
    advanced_max_intensity: str = "very_high"
    
    # Frequência semanal recomendada
    weekly_frequency: dict = {
        "cardio": {"min": 3, "max": 6},
        "strength": {"min": 2, "max": 4},
        "flexibility": {"min": 2, "max": 7}
    }
    
    # METs (Metabolic Equivalents) para cálculo de calorias
    mets_values: dict = {
        "walking_slow": 2.5,
        "walking_moderate": 3.5,
        "walking_fast": 4.5,
        "running_slow": 6.0,
        "running_moderate": 8.0,
        "running_fast": 10.0,
        "cycling_leisure": 4.0,
        "cycling_moderate": 6.0,
        "cycling_vigorous": 8.0,
        "strength_light": 3.0,
        "strength_moderate": 5.0,
        "strength_vigorous": 6.0,
        "yoga": 2.5,
        "pilates": 3.0,
        "swimming_leisure": 5.0,
        "swimming_vigorous": 8.0
    }

class SafetySettings(BaseSettings):
    """Configurações de segurança"""
    
    # Limites de FC por idade
    max_safe_hr_percentage: float = 0.95  # 95% da FC máxima
    
    # Condições que requerem cuidados especiais
    high_risk_conditions: list = [
        "heart_disease",
        "diabetes",
        "hypertension",
        "pregnancy"
    ]
    
    # Modificações automáticas por condição
    condition_modifications: dict = {
        "diabetes": {
            "pre_exercise_checks": ["Verificar glicemia"],
            "avoid_exercises": [],
            "intensity_limit": "moderate"
        },
        "hypertension": {
            "pre_exercise_checks": ["Verificar pressão arterial"],
            "avoid_exercises": ["exercícios isométricos prolongados"],
            "intensity_limit": "moderate"
        },
        "pregnancy": {
            "pre_exercise_checks": ["Liberação médica"],
            "avoid_exercises": ["exercícios supinos após 1º trimestre", "esportes de contato"],
            "intensity_limit": "low"
        },
        "heart_disease": {
            "pre_exercise_checks": ["Liberação cardiológica"],
            "avoid_exercises": ["exercícios de alta intensidade"],
            "intensity_limit": "low"
        }
    }
    
    # Alertas automáticos
    auto_alerts: dict = {
        "high_hr": "FC muito alta - Reduza a intensidade",
        "duration_exceeded": "Duração recomendada excedida",
        "intensity_too_high": "Intensidade muito alta para seu nível"
    }

# Instância global das configurações
_settings = None
_hr_zones = None
_exercise_settings = None
_safety_settings = None

def get_settings() -> Settings:
    """Retorna instância das configurações principais"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def get_hr_zones() -> HeartRateZones:
    """Retorna configurações de zonas de FC"""
    global _hr_zones
    if _hr_zones is None:
        _hr_zones = HeartRateZones()
    return _hr_zones

def get_exercise_settings() -> ExerciseSettings:
    """Retorna configurações de exercícios"""
    global _exercise_settings
    if _exercise_settings is None:
        _exercise_settings = ExerciseSettings()
    return _exercise_settings

def get_safety_settings() -> SafetySettings:
    """Retorna configurações de segurança"""
    global _safety_settings
    if _safety_settings is None:
        _safety_settings = SafetySettings()
    return _safety_settings

def reload_settings():
    """Recarrega todas as configurações"""
    global _settings, _hr_zones, _exercise_settings, _safety_settings
    _settings = None
    _hr_zones = None
    _exercise_settings = None
    _safety_settings = None

def get_all_settings() -> dict:
    """Retorna todas as configurações em um dicionário"""
    return {
        "main": get_settings().dict(),
        "heart_rate_zones": get_hr_zones().dict(),
        "exercise": get_exercise_settings().dict(),
        "safety": get_safety_settings().dict()
    }