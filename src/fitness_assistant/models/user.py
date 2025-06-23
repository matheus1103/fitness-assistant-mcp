"""
Modelos Pydantic para dados do usuário
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class FitnessLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class HealthCondition(str, Enum):
    DIABETES = "diabetes"
    HYPERTENSION = "hypertension"
    HEART_DISEASE = "heart_disease"
    ASTHMA = "asthma"
    ARTHRITIS = "arthritis"
    PREGNANCY = "pregnancy"

class ExercisePreference(str, Enum):
    CARDIO = "cardio"
    STRENGTH = "strength"
    FLEXIBILITY = "flexibility"
    SPORTS = "sports"
    YOGA = "yoga"
    SWIMMING = "swimming"
    CYCLING = "cycling"
    RUNNING = "running"

class UserProfile(BaseModel):
    """Modelo do perfil do usuário"""
    user_id: str
    age: int = Field(..., ge=10, le=120, description="Idade do usuário")
    weight: float = Field(..., gt=0, le=500, description="Peso em kg")
    height: float = Field(..., gt=0, le=3.0, description="Altura em metros")
    fitness_level: FitnessLevel
    health_conditions: List[HealthCondition] = Field(default_factory=list)
    preferences: List[ExercisePreference] = Field(default_factory=list)
    resting_heart_rate: Optional[int] = Field(None, ge=30, le=120)
    max_heart_rate: Optional[int] = Field(None, ge=120, le=220)
    goals: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('age')
    def validate_age(cls, v):
        if v < 13:
            raise ValueError('Idade mínima é 13 anos')
        return v
    
    @validator('height')
    def validate_height(cls, v):
        if v < 0.5 or v > 2.5:
            raise ValueError('Altura deve estar entre 0.5m e 2.5m')
        return v
    
    @property
    def bmi(self) -> float:
        """Calcula o IMC"""
        return round(self.weight / (self.height ** 2), 1)
    
    @property
    def bmi_category(self) -> str:
        """Retorna categoria do IMC"""
        bmi = self.bmi
        if bmi < 18.5:
            return "abaixo_do_peso"
        elif bmi < 25:
            return "peso_normal"
        elif bmi < 30:
            return "sobrepeso"
        else:
            return "obesidade"
    
    def update_timestamp(self):
        """Atualiza timestamp de modificação"""
        self.updated_at = datetime.now()

class HeartRateData(BaseModel):
    """Dados de frequência cardíaca"""
    user_id: str
    current_hr: int = Field(..., ge=40, le=250)
    resting_hr: Optional[int] = Field(None, ge=30, le=120)
    max_hr: Optional[int] = Field(None, ge=120, le=220)
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Optional[str] = None  # "rest", "exercise", "recovery"
    
    @validator('current_hr')
    def validate_current_hr(cls, v, values):
        if 'max_hr' in values and values['max_hr']:
            if v > values['max_hr']:
                raise ValueError('FC atual não pode ser maior que FC máxima')
        return v

class UserSettings(BaseModel):
    """Configurações do usuário"""
    user_id: str
    units: str = Field(default="metric", pattern="^(metric|imperial)$")
    language: str = Field(default="pt-BR")
    notifications: bool = True
    safety_alerts: bool = True
    data_sharing: bool = False
    preferred_workout_time: Optional[str] = None  # "morning", "afternoon", "evening"
    workout_reminders: bool = True
    
class UserGoal(BaseModel):
    """Meta do usuário"""
    user_id: str
    goal_type: str  # "weight_loss", "muscle_gain", "endurance", "strength"
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    unit: Optional[str] = None
    target_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    achieved: bool = False
    achieved_at: Optional[datetime] = None