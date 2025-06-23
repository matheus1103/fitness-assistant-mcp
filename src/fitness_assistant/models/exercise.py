"""
Modelos para exercícios e recomendações
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ExerciseType(str, Enum):
    CARDIO = "cardio"
    STRENGTH = "strength"
    FLEXIBILITY = "flexibility"
    BALANCE = "balance"
    HIIT = "hiit"
    SPORT = "sport"

class IntensityLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

class Equipment(str, Enum):
    NONE = "none"
    DUMBBELLS = "dumbbells"
    RESISTANCE_BANDS = "resistance_bands"
    KETTLEBELL = "kettlebell"
    BARBELL = "barbell"
    TREADMILL = "treadmill"
    BIKE = "bike"
    POOL = "pool"

class Exercise(BaseModel):
    """Modelo base de um exercício"""
    id: str
    name: str
    type: ExerciseType
    description: str
    instructions: List[str]
    muscle_groups: List[str]
    equipment_needed: List[Equipment]
    difficulty_level: IntensityLevel
    duration_range: tuple[int, int]  # min, max em minutos
    calories_per_minute: Dict[str, float]  # por nível fitness
    contraindications: List[str] = Field(default_factory=list)
    modifications: List[str] = Field(default_factory=list)
    safety_notes: List[str] = Field(default_factory=list)
    
class ExerciseRecommendation(BaseModel):
    """Recomendação personalizada de exercício"""
    user_id: str
    exercise: Exercise
    recommended_duration: int  # minutos
    recommended_intensity: IntensityLevel
    target_heart_rate_zone: Dict[str, Any]
    personalized_instructions: List[str]
    safety_modifications: List[str] = Field(default_factory=list)
    reason: str  # Por que foi recomendado
    confidence_score: float = Field(..., ge=0, le=1)
    generated_at: datetime = Field(default_factory=datetime.now)

class WorkoutPlan(BaseModel):
    """Plano de treino completo"""
    user_id: str
    name: str
    exercises: List[ExerciseRecommendation]
    total_duration: int
    estimated_calories: int
    target_zones: Dict[str, Any]
    warm_up: List[Exercise] = Field(default_factory=list)
    cool_down: List[Exercise] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    
class ExerciseVariation(BaseModel):
    """Variação de um exercício"""
    base_exercise_id: str
    name: str
    difficulty_modifier: int  # -2 (muito mais fácil) a +2 (muito mais difícil)
    description: str
    modifications: List[str]
    when_to_use: str

class MuscleGroup(BaseModel):
    """Grupo muscular"""
    name: str
    primary_muscles: List[str]
    secondary_muscles: List[str]
    common_exercises: List[str]
    
class ExerciseCategory(BaseModel):
    """Categoria de exercícios"""
    name: str
    description: str
    benefits: List[str]
    recommended_frequency: str
    exercises: List[str]  # IDs dos exercícios