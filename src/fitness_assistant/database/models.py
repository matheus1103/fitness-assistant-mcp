# src/fitness_assistant/database/models.py
"""
Modelos SQLAlchemy para PostgreSQL
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

Base = declarative_base()


class FitnessLevelEnum(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ExerciseTypeEnum(str, enum.Enum):
    CARDIO = "cardio"
    STRENGTH = "strength"
    FLEXIBILITY = "flexibility"
    BALANCE = "balance"
    HIIT = "hiit"
    SPORT = "sport"


class IntensityLevelEnum(str, enum.Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class UserProfile(Base):
    """Tabela de perfis de usuários"""
    __tablename__ = "user_profiles"
    
    # Chave primária
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Dados básicos
    user_id = Column(String(100), unique=True, nullable=False, index=True)
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    
    # Fitness
    fitness_level = Column(SQLEnum(FitnessLevelEnum), nullable=False)
    resting_heart_rate = Column(Integer, nullable=True)
    max_heart_rate = Column(Integer, nullable=True)
    
    # Arrays PostgreSQL
    health_conditions = Column(ARRAY(String), default=[], server_default='{}')
    preferences = Column(ARRAY(String), default=[], server_default='{}')
    goals = Column(ARRAY(String), default=[], server_default='{}')
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    sessions = relationship("WorkoutSession", back_populates="user", cascade="all, delete-orphan")
    heart_rate_data = relationship("HeartRateData", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def bmi(self) -> float:
        """Calcula BMI"""
        return round(self.weight / (self.height ** 2), 1)
    
    @property
    def bmi_category(self) -> str:
        """Categoria do BMI"""
        bmi = self.bmi
        if bmi < 18.5:
            return "abaixo_do_peso"
        elif bmi < 25:
            return "peso_normal"
        elif bmi < 30:
            return "sobrepeso"
        else:
            return "obesidade"

    def __repr__(self):
        return f"<UserProfile(user_id='{self.user_id}', age={self.age}, fitness_level='{self.fitness_level}')>"


class Exercise(Base):
    """Tabela de exercícios"""
    __tablename__ = "exercises"
    
    # Chave primária
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Dados básicos
    exercise_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    type = Column(SQLEnum(ExerciseTypeEnum), nullable=False)
    description = Column(Text)
    
    # Instruções e dados estruturados (JSON)
    instructions = Column(JSON)  # Lista de instruções
    muscle_groups = Column(ARRAY(String))
    equipment_needed = Column(ARRAY(String))
    
    # Dificuldade e duração
    difficulty_level = Column(SQLEnum(IntensityLevelEnum), nullable=False)
    duration_min = Column(Integer)  # Duração mínima em minutos
    duration_max = Column(Integer)  # Duração máxima em minutos
    
    # Calorias por nível de fitness (JSON)
    calories_per_minute = Column(JSON)  # {"beginner": 5.0, "intermediate": 6.0, "advanced": 7.0}
    
    # Segurança
    contraindications = Column(ARRAY(String), default=[], server_default='{}')
    modifications = Column(ARRAY(String), default=[], server_default='{}')
    safety_notes = Column(ARRAY(String), default=[], server_default='{}')
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    session_exercises = relationship("SessionExercise", back_populates="exercise")

    def __repr__(self):
        return f"<Exercise(name='{self.name}', type='{self.type}', difficulty='{self.difficulty_level}')>"


class WorkoutSession(Base):
    """Tabela de sessões de treino"""
    __tablename__ = "workout_sessions"
    
    # Chave primária
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relacionamento com usuário
    user_profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    
    # Dados da sessão
    session_date = Column(DateTime(timezone=True), server_default=func.now())
    duration_minutes = Column(Integer, nullable=False)
    session_type = Column(String(50))  # cardio, strength, mixed, etc.
    
    # Métricas de FC
    avg_heart_rate = Column(Integer)
    max_heart_rate = Column(Integer)
    
    # Avaliação subjetiva
    perceived_exertion = Column(Integer)  # Escala 1-10 (RPE)
    
    # Estimativas
    calories_estimated = Column(Integer)
    
    # Notas
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos
    user = relationship("UserProfile", back_populates="sessions")
    exercises = relationship("SessionExercise", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WorkoutSession(user_id='{self.user.user_id}', date='{self.session_date}', duration={self.duration_minutes})>"


class SessionExercise(Base):
    """Tabela de exercícios realizados em uma sessão"""
    __tablename__ = "session_exercises"
    
    # Chave primária
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relacionamentos
    session_id = Column(UUID(as_uuid=True), ForeignKey("workout_sessions.id"), nullable=False)
    exercise_id = Column(UUID(as_uuid=True), ForeignKey("exercises.id"), nullable=False)
    
    # Dados específicos da execução
    duration_minutes = Column(Integer)
    sets_performed = Column(Integer)
    reps_performed = Column(Integer)
    weight_used = Column(Float)  # Em kg
    distance_covered = Column(Float)  # Em km
    
    # Métricas
    calories_burned = Column(Integer)
    avg_heart_rate = Column(Integer)
    max_heart_rate = Column(Integer)
    
    # Avaliação
    difficulty_rating = Column(Integer)  # 1-10
    completion_percentage = Column(Float)  # 0-100%
    
    # Notas específicas
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos
    session = relationship("WorkoutSession", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="session_exercises")

    def __repr__(self):
        return f"<SessionExercise(exercise='{self.exercise.name}', duration={self.duration_minutes})>"


class HeartRateData(Base):
    """Tabela de dados de frequência cardíaca"""
    __tablename__ = "heart_rate_data"
    
    # Chave primária
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relacionamento com usuário
    user_profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    
    # Dados de FC
    current_hr = Column(Integer, nullable=False)
    resting_hr = Column(Integer)
    max_hr = Column(Integer)
    
    # Contexto
    context = Column(String(50))  # "rest", "exercise", "recovery", "sleep"
    activity_type = Column(String(100))  # Tipo de atividade se em exercício
    
    # Localização/Ambiente
    location = Column(String(100))
    temperature = Column(Float)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamento
    user = relationship("UserProfile", back_populates="heart_rate_data")

    def __repr__(self):
        return f"<HeartRateData(user_id='{self.user.user_id}', hr={self.current_hr}, context='{self.context}')>"


class UserGoal(Base):
    """Tabela de objetivos do usuário"""
    __tablename__ = "user_goals"
    
    # Chave primária
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relacionamento com usuário
    user_profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    
    # Dados do objetivo
    goal_type = Column(String(50), nullable=False)  # "weight_loss", "muscle_gain", "endurance", etc.
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Valores
    target_value = Column(Float)
    current_value = Column(Float)
    unit = Column(String(20))  # kg, minutes, reps, etc.
    
    # Datas
    target_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    achieved_at = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_achieved = Column(Boolean, default=False)
    
    # Relacionamento
    user = relationship("UserProfile")

    def __repr__(self):
        return f"<UserGoal(user_id='{self.user.user_id}', title='{self.title}', achieved={self.is_achieved})>"


class UserSettings(Base):
    """Tabela de configurações do usuário"""
    __tablename__ = "user_settings"
    
    # Chave primária
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relacionamento com usuário (1:1)
    user_profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False, unique=True)
    
    # Configurações gerais
    units = Column(String(20), default="metric")  # metric, imperial
    language = Column(String(10), default="pt-BR")
    timezone = Column(String(50), default="America/Sao_Paulo")
    
    # Notificações
    notifications_enabled = Column(Boolean, default=True)
    safety_alerts_enabled = Column(Boolean, default=True)
    progress_reminders_enabled = Column(Boolean, default=True)
    workout_reminders_enabled = Column(Boolean, default=True)
    
    # Preferências de treino
    preferred_workout_time = Column(String(20))  # "morning", "afternoon", "evening"
    preferred_session_duration = Column(Integer, default=30)
    
    # Privacidade
    data_sharing_enabled = Column(Boolean, default=False)
    public_profile = Column(Boolean, default=False)
    
    # Configurações avançadas (JSON)
    advanced_settings = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relacionamento
    user = relationship("UserProfile")

    def __repr__(self):
        return f"<UserSettings(user_id='{self.user.user_id}', units='{self.units}')>"