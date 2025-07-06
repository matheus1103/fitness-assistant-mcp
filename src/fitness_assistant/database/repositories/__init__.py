# src/fitness_assistant/database/repositories/__init__.py
"""
Repositories para acesso a dados com SQLAlchemy
"""

from .base import BaseRepository
from .user_repo import UserRepository, user_repo
from .exercise_repo import ExerciseRepository, exercise_repo

__all__ = [
    'BaseRepository',
    'UserRepository', 'user_repo',
    'ExerciseRepository', 'exercise_repo'
]