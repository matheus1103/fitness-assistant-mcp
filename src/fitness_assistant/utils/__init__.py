# src/fitness_assistant/utils/__init__.py
"""
Utilitários do Fitness Assistant
"""

from .validators import (
    validate_user_data,
    validate_heart_rate,
    validate_exercise_parameters,
    validate_user_id,
    ValidationError
)

from .safety import (
    generate_health_recommendations,
    check_exercise_safety,
    assess_overall_risk,
    generate_emergency_protocols
)

__all__ = [
    'validate_user_data',
    'validate_heart_rate', 
    'validate_exercise_parameters',
    'validate_user_id',
    'ValidationError',
    'generate_health_recommendations',
    'check_exercise_safety',
    'assess_overall_risk',
    'generate_emergency_protocols'
]