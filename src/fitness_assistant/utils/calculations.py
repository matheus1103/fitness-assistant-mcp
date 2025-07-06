# src/fitness_assistant/utils/calculations.py
"""
Funções de cálculo para fitness e frequência cardíaca
"""
from typing import Dict, Any, Optional, Tuple
import math


def calculate_heart_rate_zones(
    age: int, 
    resting_hr: int, 
    method: str = "karvonen"
) -> Dict[str, Any]:
    """
    Calcula zonas de frequência cardíaca
    
    Args:
        age: Idade em anos
        resting_hr: FC de repouso
        method: Método de cálculo ("karvonen", "percentage", "tanaka")
        
    Returns:
        Dict com zonas de FC calculadas
    """
    # Calcula FC máxima baseada na idade
    if method == "tanaka":
        # Fórmula de Tanaka: 208 - (0.7 × idade)
        max_hr = int(208 - (0.7 * age))
    else:
        # Fórmula clássica: 220 - idade
        max_hr = 220 - age
    
    # Reserva cardíaca (FC máx - FC repouso)
    hr_reserve = max_hr - resting_hr
    
    if method == "karvonen":
        # Método Karvonen (mais preciso)
        zones = {
            "zona_1": {
                "name": "Recuperação Ativa",
                "percentage": "50-60%",
                "lower": int(resting_hr + (hr_reserve * 0.50)),
                "upper": int(resting_hr + (hr_reserve * 0.60)),
                "description": "Atividade muito leve, recuperação ativa",
                "benefits": ["Recuperação", "Queima de gordura", "Circulação"],
                "intensity": "muito_baixa"
            },
            "zona_2": {
                "name": "Base Aeróbica",
                "percentage": "60-70%",
                "lower": int(resting_hr + (hr_reserve * 0.60)),
                "upper": int(resting_hr + (hr_reserve * 0.70)),
                "description": "Exercício aeróbico confortável",
                "benefits": ["Resistência cardiovascular", "Queima de gordura", "Base aeróbica"],
                "intensity": "baixa"
            },
            "zona_3": {
                "name": "Aeróbica",
                "percentage": "70-80%",
                "lower": int(resting_hr + (hr_reserve * 0.70)),
                "upper": int(resting_hr + (hr_reserve * 0.80)),
                "description": "Exercício moderadamente intenso",
                "benefits": ["Eficiência cardiovascular", "Resistência", "Capacidade aeróbica"],
                "intensity": "moderada"
            },
            "zona_4": {
                "name": "Limiar Anaeróbico",
                "percentage": "80-90%",
                "lower": int(resting_hr + (hr_reserve * 0.80)),
                "upper": int(resting_hr + (hr_reserve * 0.90)),
                "description": "Exercício intenso, próximo ao limiar",
                "benefits": ["Capacidade anaeróbica", "Velocidade", "Potência"],
                "intensity": "alta"
            },
            "zona_5": {
                "name": "VO2 Max",
                "percentage": "90-100%",
                "lower": int(resting_hr + (hr_reserve * 0.90)),
                "upper": max_hr,
                "description": "Exercício máximo, curta duração",
                "benefits": ["Potência máxima", "Sistema neuromuscular", "VO2 máximo"],
                "intensity": "maxima"
            }
        }
    else:
        # Método de porcentagem da FC máxima (mais simples)
        zones = {
            "zona_1": {
                "name": "Recuperação Ativa",
                "percentage": "50-60%",
                "lower": int(max_hr * 0.50),
                "upper": int(max_hr * 0.60),
                "description": "Atividade muito leve, recuperação ativa",
                "benefits": ["Recuperação", "Queima de gordura", "Circulação"],
                "intensity": "muito_baixa"
            },
            "zona_2": {
                "name": "Base Aeróbica", 
                "percentage": "60-70%",
                "lower": int(max_hr * 0.60),
                "upper": int(max_hr * 0.70),
                "description": "Exercício aeróbico confortável",
                "benefits": ["Resistência cardiovascular", "Queima de gordura", "Base aeróbica"],
                "intensity": "baixa"
            },
            "zona_3": {
                "name": "Aeróbica",
                "percentage": "70-80%",
                "lower": int(max_hr * 0.70),
                "upper": int(max_hr * 0.80),
                "description": "Exercício moderadamente intenso",
                "benefits": ["Eficiência cardiovascular", "Resistência", "Capacidade aeróbica"],
                "intensity": "moderada"
            },
            "zona_4": {
                "name": "Limiar Anaeróbico",
                "percentage": "80-90%",
                "lower": int(max_hr * 0.80),
                "upper": int(max_hr * 0.90),
                "description": "Exercício intenso, próximo ao limiar",
                "benefits": ["Capacidade anaeróbica", "Velocidade", "Potência"],
                "intensity": "alta"
            },
            "zona_5": {
                "name": "VO2 Max",
                "percentage": "90-100%", 
                "lower": int(max_hr * 0.90),
                "upper": max_hr,
                "description": "Exercício máximo, curta duração",
                "benefits": ["Potência máxima", "Sistema neuromuscular", "VO2 máximo"],
                "intensity": "maxima"
            }
        }
    
    return {
        "max_hr": max_hr,
        "resting_hr": resting_hr,
        "hr_reserve": hr_reserve,
        "method": method,
        "zones": zones
    }


def determine_heart_rate_zone(current_hr: int, zones: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determina em qual zona de FC a pessoa está
    
    Args:
        current_hr: FC atual
        zones: Zonas de FC calculadas
        
    Returns:
        Dict com informações da zona atual
    """
    for zone_id, zone_info in zones.items():
        if zone_info["lower"] <= current_hr <= zone_info["upper"]:
            return {
                "zone_id": zone_id,
                "zone_name": zone_info["name"],
                "intensity": zone_info["intensity"],
                "percentage_range": zone_info["percentage"],
                "description": zone_info["description"],
                "benefits": zone_info["benefits"],
                "current_hr": current_hr,
                "zone_range": f"{zone_info['lower']}-{zone_info['upper']} bpm"
            }
    
    # Se não está em nenhuma zona definida
    if current_hr < zones["zona_1"]["lower"]:
        return {
            "zone_id": "below_zone_1",
            "zone_name": "Abaixo da Zona 1",
            "intensity": "repouso",
            "description": "Frequência cardíaca muito baixa para exercício",
            "current_hr": current_hr,
            "recommendation": "Aumente a intensidade gradualmente"
        }
    else:
        return {
            "zone_id": "above_zone_5",
            "zone_name": "Acima da Zona 5",
            "intensity": "perigosa",
            "description": "Frequência cardíaca muito alta",
            "current_hr": current_hr,
            "warning": "Reduza a intensidade imediatamente"
        }


def calculate_bmi(weight_kg: float, height_m: float) -> Dict[str, Any]:
    """
    Calcula Índice de Massa Corporal
    
    Args:
        weight_kg: Peso em kg
        height_m: Altura em metros
        
    Returns:
        Dict com IMC e categoria
    """
    bmi = weight_kg / (height_m ** 2)
    
    # Determina categoria
    if bmi < 18.5:
        category = "abaixo_do_peso"
        description = "Abaixo do peso"
        recommendations = [
            "Consulte um nutricionista",
            "Foque em exercícios de fortalecimento",
            "Considere aumentar ingestão calórica saudável"
        ]
    elif bmi < 25:
        category = "peso_normal"
        description = "Peso normal"
        recommendations = [
            "Mantenha estilo de vida ativo",
            "Continue com alimentação balanceada",
            "Varie tipos de exercício"
        ]
    elif bmi < 30:
        category = "sobrepeso"
        description = "Sobrepeso"
        recommendations = [
            "Combine exercícios cardiovasculares e musculação",
            "Monitore alimentação",
            "Estabeleça metas graduais de perda de peso"
        ]
    else:
        category = "obesidade"
        description = "Obesidade"
        recommendations = [
            "Consulte profissionais de saúde",
            "Comece com exercícios de baixo impacto",
            "Planejamento nutricional profissional"
        ]
    
    return {
        "bmi": round(bmi, 1),
        "category": category,
        "description": description,
        "recommendations": recommendations,
        "healthy_weight_range": calculate_healthy_weight_range(height_m)
    }


def calculate_healthy_weight_range(height_m: float) -> Dict[str, float]:
    """Calcula faixa de peso saudável"""
    min_weight = 18.5 * (height_m ** 2)
    max_weight = 24.9 * (height_m ** 2)
    
    return {
        "min_kg": round(min_weight, 1),
        "max_kg": round(max_weight, 1)
    }


def calculate_calories_burned(
    activity_type: str,
    duration_minutes: int,
    weight_kg: float,
    intensity: str = "moderate"
) -> Dict[str, Any]:
    """
    Estima calorias queimadas durante atividade
    
    Args:
        activity_type: Tipo de atividade
        duration_minutes: Duração em minutos
        weight_kg: Peso em kg
        intensity: Intensidade (low, moderate, high)
        
    Returns:
        Dict com estimativa de calorias
    """
    # METs (Equivalente Metabólico) por atividade e intensidade
    met_values = {
        "walking": {"low": 2.5, "moderate": 3.8, "high": 5.0},
        "running": {"low": 6.0, "moderate": 8.0, "high": 11.0},
        "cycling": {"low": 4.0, "moderate": 6.8, "high": 10.0},
        "swimming": {"low": 4.0, "moderate": 6.0, "high": 8.0},
        "strength_training": {"low": 3.0, "moderate": 5.0, "high": 6.0},
        "yoga": {"low": 2.0, "moderate": 3.0, "high": 4.0},
        "dancing": {"low": 3.0, "moderate": 4.8, "high": 6.0},
        "tennis": {"low": 5.0, "moderate": 7.0, "high": 8.0},
        "soccer": {"low": 7.0, "moderate": 8.0, "high": 10.0},
        "basketball": {"low": 6.0, "moderate": 8.0, "high": 10.0}
    }
    
    # Valor MET padrão se atividade não encontrada
    met = met_values.get(activity_type, {"low": 3.0, "moderate": 4.0, "high": 5.0}).get(intensity, 4.0)
    
    # Fórmula: Calorias = MET × peso (kg) × tempo (horas)
    hours = duration_minutes / 60
    calories = met * weight_kg * hours
    
    return {
        "calories_burned": round(calories),
        "activity_type": activity_type,
        "duration_minutes": duration_minutes,
        "intensity": intensity,
        "met_value": met,
        "calories_per_minute": round(calories / duration_minutes, 1)
    }


def calculate_training_load(
    duration_minutes: int,
    avg_heart_rate: int,
    max_heart_rate: int,
    resting_heart_rate: int
) -> Dict[str, Any]:
    """
    Calcula carga de treinamento baseada na sessão
    
    Args:
        duration_minutes: Duração da sessão
        avg_heart_rate: FC média
        max_heart_rate: FC máxima individual
        resting_heart_rate: FC de repouso
        
    Returns:
        Dict com métricas de carga
    """
    # Calcula intensidade relativa
    hr_reserve = max_heart_rate - resting_heart_rate
    relative_intensity = (avg_heart_rate - resting_heart_rate) / hr_reserve
    
    # Calcula TRIMP (Training Impulse)
    # Fórmula simplificada: duração × intensidade relativa
    trimp = duration_minutes * relative_intensity
    
    # Classifica carga
    if trimp < 50:
        load_category = "baixa"
        recovery_recommendation = "Recuperação leve - 12-24 horas"
    elif trimp < 100:
        load_category = "moderada"
        recovery_recommendation = "Recuperação normal - 24-48 horas"
    elif trimp < 150:
        load_category = "alta"
        recovery_recommendation = "Recuperação ativa - 48-72 horas"
    else:
        load_category = "muito_alta"
        recovery_recommendation = "Recuperação completa - 72+ horas"
    
    return {
        "trimp_score": round(trimp, 1),
        "load_category": load_category,
        "relative_intensity": round(relative_intensity * 100, 1),
        "recovery_recommendation": recovery_recommendation,
        "intensity_zone": _get_intensity_zone(relative_intensity)
    }


def _get_intensity_zone(relative_intensity: float) -> str:
    """Determina zona de intensidade"""
    if relative_intensity < 0.5:
        return "Muito Leve"
    elif relative_intensity < 0.6:
        return "Leve"
    elif relative_intensity < 0.7:
        return "Moderada"
    elif relative_intensity < 0.8:
        return "Intensa"
    else:
        return "Muito Intensa"


def calculate_vo2_max_estimate(
    age: int,
    resting_hr: int,
    max_hr: Optional[int] = None,
    fitness_level: str = "intermediate"
) -> Dict[str, Any]:
    """
    Estima VO2 máximo baseado em dados disponíveis
    
    Args:
        age: Idade
        resting_hr: FC de repouso
        max_hr: FC máxima (opcional)
        fitness_level: Nível de condicionamento
        
    Returns:
        Dict com estimativa de VO2 max
    """
    if max_hr is None:
        max_hr = 220 - age
    
    # Fórmula baseada em FC de repouso (estimativa grosseira)
    # VO2 max ≈ 65.3 - (0.1847 × RHR) + (0.1236 × age) - (0.0192 × weight estimado)
    # Simplificada para dados disponíveis
    
    base_vo2 = 50.0  # Valor base
    
    # Ajuste por FC de repouso
    if resting_hr < 50:
        vo2_adjustment = 15
    elif resting_hr < 60:
        vo2_adjustment = 10
    elif resting_hr < 70:
        vo2_adjustment = 5
    elif resting_hr < 80:
        vo2_adjustment = 0
    else:
        vo2_adjustment = -10
    
    # Ajuste por idade
    age_adjustment = max(0, (25 - age) * 0.3)
    
    # Ajuste por nível de fitness
    fitness_adjustments = {
        "beginner": -5,
        "intermediate": 0,
        "advanced": 10
    }
    
    fitness_adjustment = fitness_adjustments.get(fitness_level, 0)
    
    estimated_vo2 = base_vo2 + vo2_adjustment + age_adjustment + fitness_adjustment
    
    # Classifica nível
    if estimated_vo2 < 25:
        classification = "Muito Baixo"
    elif estimated_vo2 < 35:
        classification = "Baixo"
    elif estimated_vo2 < 45:
        classification = "Regular"
    elif estimated_vo2 < 55:
        classification = "Bom"
    elif estimated_vo2 < 65:
        classification = "Muito Bom"
    else:
        classification = "Excelente"
    
    return {
        "estimated_vo2_max": round(estimated_vo2, 1),
        "classification": classification,
        "method": "Estimativa baseada em FC de repouso",
        "accuracy": "Baixa - recomenda-se teste direto",
        "improvement_suggestions": _get_vo2_improvement_tips(classification)
    }


def _get_vo2_improvement_tips(classification: str) -> list:
    """Dicas para melhorar VO2 max"""
    tips_map = {
        "Muito Baixo": [
            "Comece com caminhadas regulares",
            "Aumente gradualmente a duração dos exercícios",
            "Foque em consistência antes de intensidade"
        ],
        "Baixo": [
            "Inclua exercícios cardiovasculares regulares",
            "Combine caminhada rápida com corrida leve",
            "Varie tipos de atividades aeróbicas"
        ],
        "Regular": [
            "Adicione treinos intervalados",
            "Aumente duração dos treinos aeróbicos",
            "Inclua exercícios de diferentes intensidades"
        ],
        "Bom": [
            "Implemente treinos de alta intensidade",
            "Varie entre exercícios contínuos e intervalados",
            "Monitore progressão com testes regulares"
        ],
        "Muito Bom": [
            "Treinos de intervalos específicos",
            "Periodização avançada",
            "Combine diferentes modalidades esportivas"
        ],
        "Excelente": [
            "Mantenha variedade nos treinos",
            "Foque em periodização e recuperação",
            "Considere competições ou desafios específicos"
        ]
    }
    
    return tips_map.get(classification, ["Consulte um profissional de educação física"])


def calculate_recovery_metrics(
    workout_sessions: list,
    time_period_days: int = 7
) -> Dict[str, Any]:
    """
    Calcula métricas de recuperação baseado em sessões recentes
    
    Args:
        workout_sessions: Lista de sessões de treino
        time_period_days: Período para análise
        
    Returns:
        Dict com métricas de recuperação
    """
    if not workout_sessions:
        return {
            "recovery_status": "Sem dados suficientes",
            "recommendations": ["Registre pelo menos 3 sessões para análise"]
        }
    
    # Análise simplificada
    total_sessions = len(workout_sessions)
    avg_sessions_per_week = (total_sessions / time_period_days) * 7
    
    # Calcula distribuição de intensidade
    intensity_distribution = _analyze_intensity_distribution(workout_sessions)
    
    # Determina status de recuperação
    if avg_sessions_per_week > 6:
        recovery_status = "Alto risco de overtraining"
        recommendations = [
            "Reduza frequência de treinos",
            "Inclua mais dias de descanso",
            "Monitore sinais de fadiga"
        ]
    elif avg_sessions_per_week > 4:
        recovery_status = "Carga adequada"
        recommendations = [
            "Mantenha padrão atual",
            "Monitore qualidade do sono",
            "Varie intensidades"
        ]
    else:
        recovery_status = "Pode aumentar volume"
        recommendations = [
            "Considere adicionar 1-2 sessões semanais",
            "Aumente gradualmente duração",
            "Mantenha consistência"
        ]
    
    return {
        "recovery_status": recovery_status,
        "sessions_per_week": round(avg_sessions_per_week, 1),
        "intensity_distribution": intensity_distribution,
        "recommendations": recommendations,
        "next_rest_day": "Recomendado em 24-48 horas"
    }


def _analyze_intensity_distribution(sessions: list) -> Dict[str, float]:
    """Analisa distribuição de intensidade das sessões"""
    # Implementação simplificada
    return {
        "low_intensity": 40.0,    # % de sessões de baixa intensidade
        "moderate_intensity": 40.0,  # % de sessões de intensidade moderada
        "high_intensity": 20.0   # % de sessões de alta intensidade
    }