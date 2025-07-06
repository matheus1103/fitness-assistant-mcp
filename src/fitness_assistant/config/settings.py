# src/fitness_assistant/config/settings.py
"""
Configurações do Fitness Assistant
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configurações principais da aplicação"""
    
    # Aplicação
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Banco de dados
    database_type: str = Field(default="memory", env="DATABASE_TYPE")
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # Diretórios
    data_dir: str = Field(default="data", env="DATA_DIR")
    backup_dir: str = Field(default="data/backups", env="BACKUP_DIR")
    logs_dir: str = Field(default="logs", env="LOGS_DIR")
    
    # Segurança
    max_hr_warning: int = Field(default=180, env="MAX_HR_WARNING")
    min_age: int = Field(default=13, env="MIN_AGE")
    max_age: int = Field(default=120, env="MAX_AGE")
    
    # Sessões
    default_session_duration: int = Field(default=30, env="DEFAULT_SESSION_DURATION")
    max_session_duration: int = Field(default=180, env="MAX_SESSION_DURATION")
    
    # Analytics - ADICIONADOS
    analytics_retention: int = Field(default=365, env="ANALYTICS_RETENTION")
    progress_weeks: int = Field(default=4, env="PROGRESS_WEEKS")
    
    # Notificações - ADICIONADAS
    enable_safety_alerts: bool = Field(default=True, env="ENABLE_SAFETY_ALERTS")
    enable_progress_notifications: bool = Field(default=True, env="ENABLE_PROGRESS_NOTIFICATIONS")
    
    # MCP
    mcp_server_name: str = Field(default="fitness-assistant", env="MCP_SERVER_NAME")
    mcp_description: str = Field(
        default="Assistente inteligente para recomendações de exercícios",
        env="MCP_DESCRIPTION"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instância global
_settings = None

def get_settings() -> Settings:
    """Retorna instância singleton das configurações"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def reload_settings():
    """Recarrega as configurações"""
    global _settings
    _settings = None