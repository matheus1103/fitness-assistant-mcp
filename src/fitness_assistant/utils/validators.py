# src/fitness_assistant/utils/validators.py
"""
Validadores para dados do usuário e parâmetros
"""
from typing import List, Dict, Any, Optional
import re


class ValidationError(Exception):
    """Exceção customizada para erros de validação"""
    pass


def validate_user_data(age: int, weight: float, height: float) -> None:
    """
    Valida dados básicos do usuário
    
    Args:
        age: Idade em anos
        weight: Peso em kg
        height: Altura em metros
        
    Raises:
        ValidationError: Se algum dado for inválido
    """
    # Validar idade
    if not isinstance(age, int) or age < 13 or age > 120:
        raise ValidationError("Idade deve estar entre 13 e 120 anos")
    
    # Validar peso
    if not isinstance(weight, (int, float)) or weight <= 0 or weight > 500:
        raise ValidationError("Peso deve estar entre 0.1 e 500 kg")
    
    # Validar altura
    if not isinstance(height, (int, float)) or height < 0.5 or height > 2.5:
        raise ValidationError("Altura deve estar entre 0.5 e 2.5 metros")


def validate_heart_rate(current_hr: int, max_hr: Optional[int] = None, resting_hr: Optional[int] = None) -> None:
    """
    Valida dados de frequência cardíaca
    
    Args:
        current_hr: FC atual
        max_hr: FC máxima (opcional)
        resting_hr: FC de repouso (opcional)
        
    Raises:
        ValidationError: Se algum dado for inválido
    """
    # FC atual
    if not isinstance(current_hr, int) or current_hr < 40 or current_hr > 250:
        raise ValidationError("Frequência cardíaca atual deve estar entre 40 e 250 bpm")
    
    # FC máxima
    if max_hr is not None:
        if not isinstance(max_hr, int) or max_hr < 120 or max_hr > 220:
            raise ValidationError("Frequência cardíaca máxima deve estar entre 120 e 220 bpm")
        
        if current_hr > max_hr:
            raise ValidationError("FC atual não pode ser maior que FC máxima")
    
    # FC de repouso
    if resting_hr is not None:
        if not isinstance(resting_hr, int) or resting_hr < 30 or resting_hr > 120:
            raise ValidationError("Frequência cardíaca de repouso deve estar entre 30 e 120 bpm")
        
        if resting_hr >= current_hr:
            raise ValidationError("FC de repouso deve ser menor que FC atual")


def validate_exercise_parameters(duration: int, intensity: str, equipment: List[str] = None) -> None:
    """
    Valida parâmetros de exercício
    
    Args:
        duration: Duração em minutos
        intensity: Intensidade (low, moderate, high)
        equipment: Lista de equipamentos (opcional)
        
    Raises:
        ValidationError: Se algum parâmetro for inválido
    """
    # Duração
    if not isinstance(duration, int) or duration < 1 or duration > 300:
        raise ValidationError("Duração deve estar entre 1 e 300 minutos")
    
    # Intensidade
    valid_intensities = ['low', 'moderate', 'high']
    if intensity.lower() not in valid_intensities:
        raise ValidationError(f"Intensidade deve ser uma de: {', '.join(valid_intensities)}")
    
    # Equipamentos
    if equipment is not None:
        if not isinstance(equipment, list):
            raise ValidationError("Equipamentos devem ser fornecidos como lista")
        
        valid_equipment = [
            'none', 'dumbbells', 'barbell', 'resistance_bands', 'kettlebell',
            'medicine_ball', 'yoga_mat', 'pull_up_bar', 'jump_rope', 'treadmill',
            'stationary_bike', 'rowing_machine', 'elliptical'
        ]
        
        for item in equipment:
            if item.lower() not in valid_equipment:
                raise ValidationError(f"Equipamento '{item}' não é válido")


def validate_user_id(user_id: str) -> None:
    """
    Valida formato do ID do usuário
    
    Args:
        user_id: Identificador do usuário
        
    Raises:
        ValidationError: Se o ID for inválido
    """
    if not isinstance(user_id, str):
        raise ValidationError("ID do usuário deve ser uma string")
    
    if len(user_id) < 3 or len(user_id) > 50:
        raise ValidationError("ID do usuário deve ter entre 3 e 50 caracteres")
    
    # Permitir apenas letras, números e alguns caracteres especiais
    if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
        raise ValidationError("ID do usuário pode conter apenas letras, números, _ e -")


def validate_fitness_level(level: str) -> str:
    """
    Valida e normaliza nível de fitness
    
    Args:
        level: Nível de fitness
        
    Returns:
        str: Nível normalizado
        
    Raises:
        ValidationError: Se o nível for inválido
    """
    valid_levels = ['beginner', 'intermediate', 'advanced']
    level_normalized = level.lower().strip()
    
    if level_normalized not in valid_levels:
        raise ValidationError(f"Nível de fitness deve ser um de: {', '.join(valid_levels)}")
    
    return level_normalized


def validate_health_conditions(conditions: List[str]) -> List[str]:
    """
    Valida lista de condições de saúde
    
    Args:
        conditions: Lista de condições
        
    Returns:
        List[str]: Lista de condições normalizadas
        
    Raises:
        ValidationError: Se alguma condição for inválida
    """
    if not isinstance(conditions, list):
        raise ValidationError("Condições de saúde devem ser fornecidas como lista")
    
    valid_conditions = [
        'diabetes', 'hypertension', 'heart_disease', 'asthma', 
        'arthritis', 'pregnancy', 'back_problems', 'knee_problems'
    ]
    
    normalized_conditions = []
    for condition in conditions:
        condition_normalized = condition.lower().strip()
        if condition_normalized not in valid_conditions:
            raise ValidationError(f"Condição de saúde '{condition}' não é válida")
        normalized_conditions.append(condition_normalized)
    
    return normalized_conditions


def validate_exercise_preferences(preferences: List[str]) -> List[str]:
    """
    Valida preferências de exercício
    
    Args:
        preferences: Lista de preferências
        
    Returns:
        List[str]: Lista de preferências normalizadas
        
    Raises:
        ValidationError: Se alguma preferência for inválida
    """
    if not isinstance(preferences, list):
        raise ValidationError("Preferências devem ser fornecidas como lista")
    
    valid_preferences = [
        'cardio', 'strength', 'flexibility', 'sports', 'yoga', 
        'swimming', 'cycling', 'running', 'hiking', 'dancing'
    ]
    
    normalized_preferences = []
    for pref in preferences:
        pref_normalized = pref.lower().strip()
        if pref_normalized not in valid_preferences:
            raise ValidationError(f"Preferência '{pref}' não é válida")
        normalized_preferences.append(pref_normalized)
    
    return normalized_preferences


def validate_goals(goals: List[str]) -> List[str]:
    """
    Valida objetivos do usuário
    
    Args:
        goals: Lista de objetivos
        
    Returns:
        List[str]: Lista de objetivos normalizados
        
    Raises:
        ValidationError: Se algum objetivo for inválido
    """
    if not isinstance(goals, list):
        raise ValidationError("Objetivos devem ser fornecidos como lista")
    
    valid_goals = [
        'perder peso', 'ganhar massa muscular', 'melhorar condicionamento',
        'aumentar flexibilidade', 'reduzir estresse', 'melhorar saúde cardiovascular',
        'aumentar força', 'melhorar postura', 'preparação esportiva'
    ]
    
    normalized_goals = []
    for goal in goals:
        goal_normalized = goal.lower().strip()
        if goal_normalized not in valid_goals:
            raise ValidationError(f"Objetivo '{goal}' não é válido")
        normalized_goals.append(goal_normalized)
    
    return normalized_goals


def validate_session_data(duration: int, exercises_performed: List[str], avg_heart_rate: Optional[int] = None) -> None:
    """
    Valida dados de sessão de treino
    
    Args:
        duration: Duração da sessão em minutos
        exercises_performed: Lista de exercícios realizados
        avg_heart_rate: FC média durante a sessão (opcional)
        
    Raises:
        ValidationError: Se algum dado for inválido
    """
    # Duração
    if not isinstance(duration, int) or duration < 1 or duration > 300:
        raise ValidationError("Duração da sessão deve estar entre 1 e 300 minutos")
    
    # Exercícios
    if not isinstance(exercises_performed, list) or len(exercises_performed) == 0:
        raise ValidationError("Deve haver pelo menos um exercício na sessão")
    
    # FC média
    if avg_heart_rate is not None:
        if not isinstance(avg_heart_rate, int) or avg_heart_rate < 60 or avg_heart_rate > 200:
            raise ValidationError("Frequência cardíaca média deve estar entre 60 e 200 bpm")


def calculate_max_heart_rate(age: int) -> int:
    """
    Calcula FC máxima estimada baseada na idade
    
    Args:
        age: Idade em anos
        
    Returns:
        int: FC máxima estimada
    """
    # Fórmula: 220 - idade (método clássico)
    return 220 - age


def calculate_target_heart_rate_zones(max_hr: int) -> Dict[str, Dict[str, int]]:
    """
    Calcula zonas de FC alvo
    
    Args:
        max_hr: FC máxima
        
    Returns:
        Dict: Zonas de FC com limites inferior e superior
    """
    return {
        "very_light": {
            "lower": int(max_hr * 0.50),
            "upper": int(max_hr * 0.60)
        },
        "light": {
            "lower": int(max_hr * 0.60),
            "upper": int(max_hr * 0.70)
        },
        "moderate": {
            "lower": int(max_hr * 0.70),
            "upper": int(max_hr * 0.80)
        },
        "vigorous": {
            "lower": int(max_hr * 0.80),
            "upper": int(max_hr * 0.90)
        },
        "maximum": {
            "lower": int(max_hr * 0.90),
            "upper": max_hr
        }
    }


def is_safe_heart_rate(current_hr: int, age: int, fitness_level: str = "beginner") -> Dict[str, Any]:
    """
    Verifica se a FC atual está em uma zona segura
    
    Args:
        current_hr: FC atual
        age: Idade
        fitness_level: Nível de fitness
        
    Returns:
        Dict: Status de segurança e recomendações
    """
    max_hr = calculate_max_heart_rate(age)
    zones = calculate_target_heart_rate_zones(max_hr)
    
    # Determina zona atual
    current_zone = "unknown"
    for zone, limits in zones.items():
        if limits["lower"] <= current_hr <= limits["upper"]:
            current_zone = zone
            break
    
    # Determina segurança baseada no nível de fitness
    safety_thresholds = {
        "beginner": 0.75,      # Até 75% da FC máxima
        "intermediate": 0.85,   # Até 85% da FC máxima
        "advanced": 0.90       # Até 90% da FC máxima
    }
    
    threshold_hr = int(max_hr * safety_thresholds.get(fitness_level, 0.75))
    is_safe = current_hr <= threshold_hr
    
    result = {
        "is_safe": is_safe,
        "current_zone": current_zone,
        "current_percentage": round((current_hr / max_hr) * 100, 1),
        "recommended_max": threshold_hr,
        "zones": zones
    }
    
    # Adiciona recomendações
    if not is_safe:
        result["warning"] = "Frequência cardíaca muito alta - reduza a intensidade"
    elif current_hr < zones["light"]["lower"]:
        result["suggestion"] = "Você pode aumentar a intensidade com segurança"
    else:
        result["status"] = "Frequência cardíaca em zona segura e efetiva"
    
    return result