# src/fitness_assistant/database/models.py
"""
Modelos SQLAlchemy para PostgreSQL
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid

Base = declarative_base()

class UserProfile(Base):
    """Tabela de perfis de usuários"""
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), unique=True, nullable=False, index=True)
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    fitness_level = Column(String(20), nullable=False)  # beginner, intermediate, advanced
    health_conditions = Column(ARRAY(String), default=[])
    preferences = Column(ARRAY(String), default=[])
    resting_heart_rate = Column(Integer, nullable=True)
    max_heart_rate = Column(Integer, nullable=True)
    goals = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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

class Exercise(Base):
    """Tabela de exercícios"""
    __tablename__ = "exercises"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exercise_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)  # cardio, strength, flexibility, etc.
    description = Column(Text)
    instructions = Column(JSON)  # Lista de instruções
    muscle_groups = Column(ARRAY(String))
    equipment_needed = Column(ARRAY(String))
    difficulty_level = Column(String(20), nullable=False)
    duration_min = Column(Integer)
    duration_max = Column(Integer)
    calories_per_minute = Column(JSON)  # Por nível fitness
    contraindications = Column(ARRAY(String), default=[])
    modifications = Column(ARRAY(String), default=[])
    safety_notes = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    session_exercises = relationship("SessionExercise", back_populates="exercise")

class WorkoutSession(Base):
    """Tabela de sessões de treino"""
    __tablename__ = "workout_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    session_date = Column(DateTime, default=datetime.utcnow)
    duration_minutes = Column(Integer, nullable=False)
    avg_heart_rate = Column(Integer)
    max_heart_rate = Column(Integer)
    perceived_exertion = Column(Integer)  # Escala 1-10
    calories_estimated = Column(Integer)
    notes = Column(Text)
    session_type = Column(String(50))  # cardio, strength, mixed, etc.
    completed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    user = relationship("UserProfile", back_populates="sessions")
    exercises = relationship("SessionExercise", back_populates="session", cascade="all, delete-orphan")

class SessionExercise(Base):
    """Tabela de exercícios dentro de uma sessão"""
    __tablename__ = "session_exercises"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("workout_sessions.id"), nullable=False)
    exercise_id = Column(UUID(as_uuid=True), ForeignKey("exercises.id"), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    sets = Column(Integer)
    reps = Column(Integer)
    weight_kg = Column(Float)
    distance_km = Column(Float)
    target_heart_rate = Column(Integer)
    actual_heart_rate = Column(Integer)
    order_in_session = Column(Integer, default=1)
    notes = Column(Text)
    
    # Relacionamentos
    session = relationship("WorkoutSession", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="session_exercises")

class HeartRateData(Base):
    """Tabela de dados de frequência cardíaca"""
    __tablename__ = "heart_rate_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("workout_sessions.id"), nullable=True)
    heart_rate = Column(Integer, nullable=False)
    context = Column(String(20), default="exercise")  # rest, warmup, exercise, recovery
    timestamp = Column(DateTime, default=datetime.utcnow)
    zone = Column(String(20))  # Zona calculada
    
    # Relacionamentos
    user = relationship("UserProfile", back_populates="heart_rate_data")

class UserGoal(Base):
    """Tabela de objetivos dos usuários"""
    __tablename__ = "user_goals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    goal_type = Column(String(50), nullable=False)  # weight_loss, muscle_gain, endurance
    target_value = Column(Float)
    current_value = Column(Float)
    unit = Column(String(20))
    target_date = Column(DateTime)
    achieved = Column(Boolean, default=False)
    achieved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

