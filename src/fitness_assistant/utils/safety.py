# src/fitness_assistant/utils/safety.py
"""
Módulo de segurança e recomendações de saúde
"""
from typing import Dict, List, Any, Optional
from ..models.user import UserProfile, HealthCondition


def generate_health_recommendations(profile: UserProfile) -> List[str]:
    """
    Gera recomendações de saúde baseadas no perfil do usuário
    
    Args:
        profile: Perfil do usuário
        
    Returns:
        List[str]: Lista de recomendações
    """
    recommendations = []
    
    # Recomendações baseadas em condições de saúde
    for condition in profile.health_conditions:
        recommendations.extend(_get_condition_recommendations(condition))
    
    # Recomendações baseadas no IMC
    bmi_recommendations = _get_bmi_recommendations(profile.bmi, profile.bmi_category)
    recommendations.extend(bmi_recommendations)
    
    # Recomendações baseadas na idade
    age_recommendations = _get_age_recommendations(profile.age)
    recommendations.extend(age_recommendations)
    
    # Recomendações baseadas no nível de fitness
    fitness_recommendations = _get_fitness_level_recommendations(profile.fitness_level)
    recommendations.extend(fitness_recommendations)
    
    # Remove duplicatas mantendo a ordem
    seen = set()
    unique_recommendations = []
    for rec in recommendations:
        if rec not in seen:
            seen.add(rec)
            unique_recommendations.append(rec)
    
    return unique_recommendations


def _get_condition_recommendations(condition: HealthCondition) -> List[str]:
    """Recomendações específicas por condição de saúde"""
    recommendations_map = {
        HealthCondition.DIABETES: [
            "Monitore a glicemia antes e após exercícios",
            "Mantenha carboidratos de rápida absorção por perto",
            "Evite exercícios em jejum prolongado",
            "Consulte seu médico sobre ajustes na medicação"
        ],
        HealthCondition.HYPERTENSION: [
            "Evite exercícios de alta intensidade sem supervisão",
            "Monitore a pressão arterial regularmente",
            "Hidrate-se adequadamente durante exercícios",
            "Evite movimentos que envolvam inversão (cabeça para baixo)"
        ],
        HealthCondition.HEART_DISEASE: [
            "Consulte um cardiologista antes de iniciar exercícios",
            "Monitore frequência cardíaca constantemente",
            "Evite exercícios de alta intensidade",
            "Pare imediatamente se sentir dor no peito ou falta de ar"
        ],
        HealthCondition.ASTHMA: [
            "Mantenha o inalador sempre próximo durante exercícios",
            "Faça aquecimento prolongado e gradual",
            "Evite exercícios em ambientes muito frios ou secos",
            "Pare se sentir chiado no peito ou falta de ar"
        ],
        HealthCondition.ARTHRITIS: [
            "Prefira exercícios de baixo impacto",
            "Aqueça bem as articulações antes do exercício",
            "Evite movimentos que causem dor articular",
            "Considere exercícios aquáticos"
        ],
        HealthCondition.PREGNANCY: [
            "Consulte seu obstetra sobre exercícios apropriados",
            "Evite exercícios em posição supina após o primeiro trimestre",
            "Mantenha-se bem hidratada",
            "Pare se sentir tontura, náusea ou falta de ar"
        ]
    }
    
    return recommendations_map.get(condition, [])


def _get_bmi_recommendations(bmi: float, category: str) -> List[str]:
    """Recomendações baseadas no IMC"""
    recommendations = []
    
    if category == "abaixo_do_peso":
        recommendations.extend([
            "Foque em exercícios de fortalecimento muscular",
            "Combine exercícios com alimentação adequada para ganho de peso",
            "Evite exercícios cardiovasculares excessivos"
        ])
    elif category == "sobrepeso":
        recommendations.extend([
            "Combine exercícios cardiovasculares com fortalecimento",
            "Comece com intensidade baixa e aumente gradualmente",
            "Monitore a hidratação durante exercícios"
        ])
    elif category == "obesidade":
        recommendations.extend([
            "Prefira exercícios de baixo impacto para proteger articulações",
            "Comece com caminhadas e exercícios aquáticos",
            "Consulte um profissional de saúde antes de iniciar"
        ])
    
    return recommendations


def _get_age_recommendations(age: int) -> List[str]:
    """Recomendações baseadas na idade"""
    recommendations = []
    
    if age < 18:
        recommendations.extend([
            "Foque no desenvolvimento motor e coordenação",
            "Evite levantamento de peso excessivo",
            "Privilegie atividades lúdicas e esportivas"
        ])
    elif age >= 65:
        recommendations.extend([
            "Inclua exercícios de equilíbrio e coordenação",
            "Aumente gradualmente a intensidade dos exercícios",
            "Considere exercícios de fortalecimento ósseo",
            "Consulte seu médico regularmente"
        ])
    elif age >= 50:
        recommendations.extend([
            "Inclua exercícios de flexibilidade na rotina",
            "Monitore sinais de fadiga e desconforto",
            "Considere suplementação de cálcio e vitamina D"
        ])
    
    return recommendations


def _get_fitness_level_recommendations(fitness_level: str) -> List[str]:
    """Recomendações baseadas no nível de fitness"""
    recommendations_map = {
        "beginner": [
            "Comece com exercícios de baixa intensidade",
            "Aumente gradualmente duração e intensidade",
            "Descanse pelo menos um dia entre treinos intensos",
            "Foque na execução correta dos movimentos"
        ],
        "intermediate": [
            "Varie tipos de exercícios para evitar plateaus",
            "Monitore sinais de overtraining",
            "Inclua periodização no seu treino"
        ],
        "advanced": [
            "Considere treinos de alta intensidade",
            "Monitore métricas avançadas de performance",
            "Planeje períodos de recuperação ativa"
        ]
    }
    
    return recommendations_map.get(fitness_level, [])


def check_exercise_safety(
    user_profile: UserProfile,
    exercise_intensity: str,
    duration: int,
    current_hr: Optional[int] = None
) -> Dict[str, Any]:
    """
    Verifica a segurança de um exercício para o usuário
    
    Args:
        user_profile: Perfil do usuário
        exercise_intensity: Intensidade do exercício
        duration: Duração em minutos
        current_hr: FC atual (opcional)
        
    Returns:
        Dict: Análise de segurança e recomendações
    """
    safety_result = {
        "is_safe": True,
        "warnings": [],
        "recommendations": [],
        "max_duration": duration,
        "target_hr_zone": None
    }
    
    # Verifica contraindicações por condição de saúde
    for condition in user_profile.health_conditions:
        condition_warnings = _check_condition_contraindications(condition, exercise_intensity)
        safety_result["warnings"].extend(condition_warnings)
    
    # Verifica duração baseada no nível de fitness
    max_duration = _calculate_max_safe_duration(user_profile.fitness_level, exercise_intensity)
    if duration > max_duration:
        safety_result["is_safe"] = False
        safety_result["warnings"].append(f"Duração muito longa. Máximo recomendado: {max_duration} minutos")
        safety_result["max_duration"] = max_duration
    
    # Calcula zona de FC alvo
    max_hr = 220 - user_profile.age
    target_zones = _calculate_target_zones(max_hr, exercise_intensity, user_profile.fitness_level)
    safety_result["target_hr_zone"] = target_zones
    
    # Verifica FC atual se fornecida
    if current_hr:
        hr_check = _check_heart_rate_safety(current_hr, target_zones, user_profile.health_conditions)
        safety_result.update(hr_check)
    
    # Se há warnings, exercício não é totalmente seguro
    if safety_result["warnings"]:
        safety_result["is_safe"] = False
    
    return safety_result


def _check_condition_contraindications(condition: HealthCondition, intensity: str) -> List[str]:
    """Verifica contraindicações específicas por condição"""
    warnings = []
    
    contraindications = {
        HealthCondition.HEART_DISEASE: {
            "high": "Exercícios de alta intensidade são contraindicados para problemas cardíacos"
        },
        HealthCondition.HYPERTENSION: {
            "high": "Monitore a pressão arterial - exercícios intensos podem elevá-la perigosamente"
        },
        HealthCondition.PREGNANCY: {
            "high": "Evite exercícios de alta intensidade durante a gravidez"
        },
        HealthCondition.ASTHMA: {
            "high": "Exercícios intensos podem desencadear crises de asma"
        }
    }
    
    if condition in contraindications and intensity in contraindications[condition]:
        warnings.append(contraindications[condition][intensity])
    
    return warnings


def _calculate_max_safe_duration(fitness_level: str, intensity: str) -> int:
    """Calcula duração máxima segura baseada no nível e intensidade"""
    duration_limits = {
        "beginner": {"low": 60, "moderate": 30, "high": 15},
        "intermediate": {"low": 90, "moderate": 60, "high": 30},
        "advanced": {"low": 120, "moderate": 90, "high": 60}
    }
    
    return duration_limits.get(fitness_level, duration_limits["beginner"]).get(intensity, 30)


def _calculate_target_zones(max_hr: int, intensity: str, fitness_level: str) -> Dict[str, int]:
    """Calcula zonas de FC alvo"""
    base_zones = {
        "low": (0.50, 0.60),
        "moderate": (0.60, 0.70),
        "high": (0.70, 0.85)
    }
    
    # Ajusta para nível de fitness
    if fitness_level == "advanced":
        base_zones["high"] = (0.75, 0.90)
    elif fitness_level == "beginner":
        base_zones["high"] = (0.65, 0.80)
    
    lower_pct, upper_pct = base_zones.get(intensity, base_zones["moderate"])
    
    return {
        "lower": int(max_hr * lower_pct),
        "upper": int(max_hr * upper_pct),
        "max_hr": max_hr
    }


def _check_heart_rate_safety(current_hr: int, target_zone: Dict[str, int], conditions: List[HealthCondition]) -> Dict[str, Any]:
    """Verifica segurança da FC atual"""
    result = {
        "hr_status": "normal",
        "hr_warnings": []
    }
    
    # Verifica se está muito alta
    if current_hr > target_zone["upper"]:
        result["hr_status"] = "too_high"
        result["hr_warnings"].append("Frequência cardíaca muito alta - reduza a intensidade")
    
    # Verifica se está muito baixa para a intensidade pretendida
    elif current_hr < target_zone["lower"]:
        result["hr_status"] = "too_low"
        result["hr_warnings"].append("Frequência cardíaca baixa para a intensidade - pode aumentar gradualmente")
    
    # Verificações especiais para condições de saúde
    for condition in conditions:
        if condition == HealthCondition.HEART_DISEASE and current_hr > 0.7 * target_zone["max_hr"]:
            result["hr_warnings"].append("FC alta para problemas cardíacos - consulte seu médico")
        elif condition == HealthCondition.HYPERTENSION and current_hr > 0.8 * target_zone["max_hr"]:
            result["hr_warnings"].append("FC alta para hipertensão - monitore a pressão")
    
    return result


def generate_emergency_protocols() -> Dict[str, List[str]]:
    """Gera protocolos de emergência"""
    return {
        "chest_pain": [
            "Pare o exercício imediatamente",
            "Sente-se e descanse",
            "Se a dor persistir, chame emergência (192)",
            "Não tome medicamentos sem orientação médica"
        ],
        "shortness_of_breath": [
            "Reduza a intensidade ou pare o exercício",
            "Sente-se em posição confortável",
            "Respire lentamente e profundamente",
            "Se não melhorar em 5 minutos, busque ajuda"
        ],
        "dizziness": [
            "Pare o exercício e sente-se",
            "Baixe a cabeça entre os joelhos",
            "Hidrate-se lentamente",
            "Não levante rapidamente"
        ],
        "excessive_fatigue": [
            "Pare o exercício imediatamente",
            "Descanse em local fresco",
            "Hidrate-se gradualmente",
            "Monitore sintomas por 15-30 minutos"
        ]
    }


def assess_overall_risk(profile: UserProfile) -> Dict[str, Any]:
    """Avalia risco geral do usuário para exercícios"""
    risk_factors = []
    risk_level = "low"
    
    # Fatores de risco por idade
    if profile.age > 65:
        risk_factors.append("Idade avançada")
        risk_level = "moderate"
    
    # Fatores de risco por condições de saúde
    high_risk_conditions = [
        HealthCondition.HEART_DISEASE,
        HealthCondition.DIABETES,
        HealthCondition.HYPERTENSION
    ]
    
    for condition in profile.health_conditions:
        if condition in high_risk_conditions:
            risk_factors.append(f"Condição de saúde: {condition.value}")
            risk_level = "high"
    
    # Fatores de risco por IMC
    if profile.bmi_category in ["obesidade"]:
        risk_factors.append("Obesidade")
        if risk_level == "low":
            risk_level = "moderate"
    
    return {
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "recommendations": _get_risk_recommendations(risk_level),
        "medical_clearance_needed": risk_level == "high"
    }


def _get_risk_recommendations(risk_level: str) -> List[str]:
    """Recomendações baseadas no nível de risco"""
    recommendations_map = {
        "low": [
            "Mantenha regularidade nos exercícios",
            "Escute seu corpo e descanse quando necessário"
        ],
        "moderate": [
            "Consulte um profissional de educação física",
            "Monitore sinais vitais durante exercícios",
            "Aumente intensidade gradualmente"
        ],
        "high": [
            "Obtenha liberação médica antes de exercitar-se",
            "Exercite-se sempre com supervisão profissional",
            "Monitore constantemente sinais vitais",
            "Mantenha contato médico regular durante programa de exercícios"
        ]
    }
    
    return recommendations_map.get(risk_level, recommendations_map["low"])


def check_heart_rate_safety(
    current_hr: int,
    age: int,
    fitness_level: str = "intermediate",
    health_conditions: List[HealthCondition] = None
) -> Dict[str, Any]:
    """
    Verifica segurança da frequência cardíaca atual
    
    Args:
        current_hr: FC atual em bpm
        age: Idade do usuário
        fitness_level: Nível de condicionamento físico
        health_conditions: Lista de condições de saúde
        
    Returns:
        Dict com análise de segurança da FC
    """
    if health_conditions is None:
        health_conditions = []
    
    # Calcula FC máxima estimada
    max_hr = 220 - age
    
    # Define limites seguros baseados no nível de fitness
    safety_limits = {
        "beginner": 0.75,      # 75% da FC máxima
        "intermediate": 0.85,   # 85% da FC máxima  
        "advanced": 0.90       # 90% da FC máxima
    }
    
    safe_limit = int(max_hr * safety_limits.get(fitness_level, 0.80))
    
    # Análise básica de segurança
    is_safe = current_hr <= safe_limit
    alerts = []
    recommendations = []
    risk_level = "low"
    
    # Verifica limites críticos
    if current_hr > max_hr * 0.95:
        is_safe = False
        risk_level = "critical"
        alerts.append("FC extremamente alta - PARE o exercício imediatamente")
        recommendations.append("Sente-se e descanse")
        recommendations.append("Busque ajuda médica se não melhorar em 5 minutos")
        
    elif current_hr > safe_limit:
        is_safe = False
        risk_level = "high"
        alerts.append("FC acima do limite seguro - Reduza a intensidade")
        recommendations.append("Diminua o ritmo gradualmente")
        recommendations.append("Monitore constantemente")
        
    elif current_hr > max_hr * 0.60:
        risk_level = "moderate"
        recommendations.append("FC em zona de treino - Continue monitorando")
        
    else:
        recommendations.append("FC em zona segura - Pode aumentar intensidade gradualmente")
    
    # Verificações específicas por condições de saúde
    for condition in health_conditions:
        condition_alerts = _check_hr_condition_specific(current_hr, max_hr, condition)
        alerts.extend(condition_alerts)
        
        if condition_alerts:
            is_safe = False
            risk_level = "high"
    
    # Verifica FC muito baixa durante exercício
    if current_hr < 50:
        alerts.append("FC muito baixa - Verifique se está se exercitando adequadamente")
        recommendations.append("Aumente gradualmente a intensidade")
    
    return {
        "safe": is_safe,
        "risk_level": risk_level,
        "current_hr": current_hr,
        "safe_limit": safe_limit,
        "max_hr": max_hr,
        "percentage_max": round((current_hr / max_hr) * 100, 1),
        "alerts": alerts,
        "recommendations": recommendations,
        "zone_description": _get_hr_zone_description(current_hr, max_hr),
        "next_check_minutes": _suggest_next_hr_check(risk_level)
    }


def _check_hr_condition_specific(current_hr: int, max_hr: int, condition: HealthCondition) -> List[str]:
    """Verifica FC específica por condição de saúde"""
    alerts = []
    hr_percentage = (current_hr / max_hr) * 100
    
    condition_limits = {
        HealthCondition.HEART_DISEASE: {
            "warning_threshold": 70,
            "message": "FC alta para problemas cardíacos - Consulte seu cardiologista"
        },
        HealthCondition.HYPERTENSION: {
            "warning_threshold": 80,
            "message": "FC alta para hipertensão - Monitore pressão arterial"
        },
        HealthCondition.DIABETES: {
            "warning_threshold": 85,
            "message": "Monitore glicemia durante exercício intenso"
        },
        HealthCondition.ASTHMA: {
            "warning_threshold": 80,
            "message": "FC alta pode desencadear sintomas de asma"
        }
    }
    
    if condition in condition_limits:
        limit_info = condition_limits[condition]
        if hr_percentage > limit_info["warning_threshold"]:
            alerts.append(limit_info["message"])
    
    return alerts


def _get_hr_zone_description(current_hr: int, max_hr: int) -> str:
    """Retorna descrição da zona de FC atual"""
    percentage = (current_hr / max_hr) * 100
    
    if percentage < 50:
        return "Zona de Repouso - Muito baixa para exercício"
    elif percentage < 60:
        return "Zona 1 - Recuperação Ativa"
    elif percentage < 70:
        return "Zona 2 - Base Aeróbica"
    elif percentage < 80:
        return "Zona 3 - Aeróbica"
    elif percentage < 90:
        return "Zona 4 - Limiar Anaeróbico" 
    else:
        return "Zona 5 - VO2 Max / Crítica"


def _suggest_next_hr_check(risk_level: str) -> int:
    """Sugere próxima verificação de FC em minutos"""
    intervals = {
        "low": 15,
        "moderate": 10,
        "high": 5,
        "critical": 2
    }
    
    return intervals.get(risk_level, 10)


def generate_exercise_safety_checklist(profile: UserProfile) -> Dict[str, List[str]]:
    """
    Gera checklist de segurança personalizado
    
    Args:
        profile: Perfil do usuário
        
    Returns:
        Dict com checklist categorizado
    """
    checklist = {
        "before_exercise": [
            "Verifique se está bem hidratado",
            "Faça aquecimento de 5-10 minutos",
            "Certifique-se de que tem equipamentos adequados"
        ],
        "during_exercise": [
            "Monitore frequência cardíaca regularmente",
            "Mantenha respiração controlada",
            "Pare se sentir dor ou desconforto anormal"
        ],
        "after_exercise": [
            "Faça resfriamento gradual de 5-10 minutos",
            "Hidrate-se adequadamente",
            "Monitore como se sente nas próximas horas"
        ],
        "emergency_signals": [
            "Dor no peito ou pressão",
            "Falta de ar severa",
            "Tontura ou desmaio",
            "Náusea persistente"
        ]
    }
    
    # Adiciona itens específicos baseados no perfil
    
    # Por idade
    if profile.age > 65:
        checklist["before_exercise"].extend([
            "Verifique medicamentos com médico",
            "Considere exercitar-se com acompanhante"
        ])
        checklist["during_exercise"].append("Monitore equilíbrio constantemente")
    
    if profile.age < 18:
        checklist["before_exercise"].append("Tenha supervisão adulta se necessário")
    
    # Por condições de saúde
    for condition in profile.health_conditions:
        if condition == HealthCondition.DIABETES:
            checklist["before_exercise"].extend([
                "Verifique glicemia",
                "Tenha carboidratos de rápida absorção disponíveis"
            ])
        elif condition == HealthCondition.HYPERTENSION:
            checklist["before_exercise"].append("Verifique pressão arterial")
            checklist["during_exercise"].append("Evite exercícios isométricos prolongados")
        elif condition == HealthCondition.ASTHMA:
            checklist["before_exercise"].append("Tenha inalador próximo")
            checklist["during_exercise"].append("Pare se sentir chiado no peito")
    
    # Por nível de fitness
    if profile.fitness_level == "beginner":
        checklist["during_exercise"].extend([
            "Comece devagar e aumente gradualmente",
            "Descanse sempre que necessário"
        ])
    
    return checklist