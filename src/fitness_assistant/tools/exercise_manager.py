# src/fitness_assistant/tools/exercise_manager.py
"""
Gerenciador de exercícios e recomendações
"""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ..database.repositories.user_repo import user_repo
from ..database.repositories.exercise_repo import exercise_repo
from ..utils.calculations import calculate_heart_rate_zones, determine_heart_rate_zone
from ..utils.safety import check_heart_rate_safety

logger = logging.getLogger(__name__)


class ExerciseManager:
    """Gerencia exercícios e recomendações"""
    
    async def recommend_exercises(
        self,
        user_id: str,
        current_hr: int,
        session_duration: int,
        workout_type: str = "mixed",
        available_equipment: List[str] = None
    ) -> Dict[str, Any]:
        """Recomenda exercícios personalizados"""
        
        try:
            # Busca perfil do usuário
            user = await user_repo.get_user_by_id(user_id)
            if not user:
                return {
                    "status": "error",
                    "message": f"Usuário {user_id} não encontrado"
                }
            
            # Verifica segurança da FC
            safety_check = check_heart_rate_safety(
                current_hr, 
                user.age, 
                user.fitness_level.value,
                user.health_conditions
            )
            
            if not safety_check["safe"]:
                return {
                    "status": "warning",
                    "message": "FC fora da zona segura",
                    "safety_alerts": safety_check["alerts"],
                    "recommendations": ["Reduza a intensidade", "Descanse antes de continuar"]
                }
            
            # Calcula zonas de FC
            resting_hr = user.resting_heart_rate or self._estimate_resting_hr(user.age, user.fitness_level.value)
            hr_zones = calculate_heart_rate_zones(user.age, resting_hr)
            current_zone = determine_heart_rate_zone(current_hr, hr_zones["zones"])
            
            # Filtra exercícios por equipamentos disponíveis
            if available_equipment is None:
                available_equipment = ["none"]
            
            # Busca exercícios adequados
            recommendations = await self._generate_exercise_recommendations(
                user, current_zone, session_duration, workout_type, available_equipment
            )
            
            return {
                "status": "success",
                "user_id": user_id,
                "current_hr": current_hr,
                "current_zone": current_zone.get("zone_name", "Unknown"),
                "session_duration": session_duration,
                "workout_type": workout_type,
                "recommendations": recommendations,
                "safety_notes": self._get_safety_notes(user, current_zone),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao recomendar exercícios para {user_id}: {e}")
            return {
                "status": "error", 
                "message": f"Erro interno: {str(e)}"
            }
    
    async def get_variations(
        self,
        exercise_name: str,
        fitness_level: str,
        modifications_needed: List[str] = None
    ) -> Dict[str, Any]:
        """Obtém variações de um exercício"""
        
        try:
            # Busca exercício base
            exercises = await exercise_repo.search_exercises(exercise_name)
            
            if not exercises:
                return {
                    "status": "error",
                    "message": f"Exercício '{exercise_name}' não encontrado"
                }
            
            base_exercise = exercises[0]
            variations = []
            
            # Variações por nível de fitness
            if fitness_level == "beginner":
                variations.append({
                    "name": f"{base_exercise.name} - Versão Iniciante",
                    "description": "Versão simplificada com menor intensidade",
                    "modifications": [
                        "Reduza amplitude de movimento",
                        "Use menos peso ou resistência",
                        "Faça mais pausas entre repetições",
                        "Reduza número de repetições"
                    ]
                })
            elif fitness_level == "advanced":
                variations.append({
                    "name": f"{base_exercise.name} - Versão Avançada",
                    "description": "Versão mais desafiadora",
                    "modifications": [
                        "Aumente amplitude de movimento",
                        "Adicione peso ou resistência",
                        "Combine com outros movimentos",
                        "Aumente tempo sob tensão"
                    ]
                })
            
            # Modificações específicas por necessidades
            if modifications_needed:
                for modification in modifications_needed:
                    if "joelho" in modification.lower():
                        variations.append({
                            "name": f"{base_exercise.name} - Proteção Joelho",
                            "description": "Adaptado para problemas no joelho",
                            "modifications": [
                                "Evite flexão profunda",
                                "Use suporte se necessário",
                                "Movimento controlado e lento",
                                "Fortaleça músculos ao redor do joelho"
                            ]
                        })
                    elif "lombar" in modification.lower():
                        variations.append({
                            "name": f"{base_exercise.name} - Proteção Lombar",
                            "description": "Adaptado para problemas lombares",
                            "modifications": [
                                "Mantenha coluna neutra",
                                "Evite flexão excessiva",
                                "Use apoio lombar se necessário",
                                "Fortaleça core antes de progredir"
                            ]
                        })
                    elif "ombro" in modification.lower():
                        variations.append({
                            "name": f"{base_exercise.name} - Proteção Ombro",
                            "description": "Adaptado para problemas no ombro",
                            "modifications": [
                                "Evite movimentos acima da cabeça",
                                "Reduza amplitude se houver dor",
                                "Fortaleça rotadores do ombro",
                                "Use movimentos controlados"
                            ]
                        })
            
            return {
                "status": "success",
                "base_exercise": base_exercise.name,
                "fitness_level": fitness_level,
                "variations": variations,
                "general_tips": [
                    "Sempre aqueça antes de começar",
                    "Pare se sentir dor",
                    "Progrida gradualmente",
                    "Mantenha boa forma durante todo o movimento"
                ]
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar variações de {exercise_name}: {e}")
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }
    
    async def get_all_exercises(self) -> List[Dict[str, Any]]:
        """Retorna catálogo completo de exercícios"""
        
        try:
            exercises = await exercise_repo.get_all_exercises()
            
            catalog = []
            for exercise in exercises:
                catalog.append({
                    "id": exercise.id,
                    "name": exercise.name,
                    "type": exercise.type.value,
                    "difficulty": exercise.difficulty_level.value,
                    "equipment": [eq.value for eq in exercise.equipment_needed],
                    "duration_range": exercise.duration_range,
                    "muscle_groups": exercise.muscle_groups,
                    "description": exercise.description
                })
            
            return catalog
            
        except Exception as e:
            logger.error(f"Erro ao buscar catálogo de exercícios: {e}")
            return []
    
    async def _generate_exercise_recommendations(
        self,
        user,
        current_zone: dict,
        session_duration: int,
        workout_type: str,
        available_equipment: List[str]
    ) -> List[Dict[str, Any]]:
        """Gera recomendações de exercícios personalizadas"""
        
        recommendations = []
        remaining_duration = session_duration
        
        # Determina tipos de exercício baseado no workout_type
        if workout_type == "mixed":
            exercise_types = ["cardio", "strength"]
            cardio_ratio = 0.6  # 60% cardio, 40% força
        elif workout_type == "cardio":
            exercise_types = ["cardio"]
            cardio_ratio = 1.0
        elif workout_type == "strength":
            exercise_types = ["strength"]
            cardio_ratio = 0.0
        else:
            exercise_types = ["cardio", "strength"]
            cardio_ratio = 0.5
        
        # Busca exercícios por tipo
        for ex_type in exercise_types:
            exercises = await exercise_repo.get_exercises_by_type(ex_type)
            
            # Filtra por equipamentos disponíveis
            filtered_exercises = await exercise_repo.get_exercises_by_equipment(available_equipment)
            
            # Filtra por dificuldade apropriada
            suitable_exercises = []
            for exercise in filtered_exercises:
                if exercise.type.value == ex_type:
                    # Verifica se dificuldade é apropriada
                    if self._is_suitable_difficulty(exercise, user.fitness_level.value):
                        suitable_exercises.append(exercise)
            
            if suitable_exercises:
                # Calcula duração para este tipo
                if ex_type == "cardio":
                    type_duration = int(remaining_duration * cardio_ratio) if workout_type == "mixed" else remaining_duration
                else:
                    type_duration = remaining_duration - int(session_duration * cardio_ratio) if workout_type == "mixed" else remaining_duration
                
                # Seleciona exercícios
                selected_exercises = self._select_exercises(
                    suitable_exercises, 
                    type_duration, 
                    user,
                    current_zone
                )
                
                recommendations.extend(selected_exercises)
                remaining_duration -= sum(ex['recommended_duration'] for ex in selected_exercises)
        
        return recommendations
    
    def _is_suitable_difficulty(self, exercise, fitness_level: str) -> bool:
        """Verifica se dificuldade do exercício é adequada"""
        
        exercise_difficulty = exercise.difficulty_level.value
        
        difficulty_mapping = {
            "beginner": ["very_low", "low"],
            "intermediate": ["low", "moderate"],
            "advanced": ["moderate", "high", "very_high"]
        }
        
        suitable_levels = difficulty_mapping.get(fitness_level, ["low", "moderate"])
        return exercise_difficulty in suitable_levels
    
    def _select_exercises(
        self, 
        exercises: List, 
        total_duration: int, 
        user,
        current_zone: dict
    ) -> List[Dict[str, Any]]:
        """Seleciona exercícios adequados para a sessão"""
        
        selected = []
        used_duration = 0
        
        # Prioriza exercícios baseado nas preferências do usuário
        user_preferences = [pref.value for pref in user.preferences] if user.preferences else []
        
        # Ordena exercícios por relevância
        scored_exercises = []
        for exercise in exercises:
            score = 0
            
            # Pontuação por preferência
            if exercise.type.value in user_preferences:
                score += 10
            
            # Pontuação por grupo muscular (varia para balanceamento)
            for muscle in exercise.muscle_groups:
                if muscle in ["core", "legs"]:  # Grupos importantes
                    score += 5
            
            scored_exercises.append((score, exercise))
        
        # Ordena por pontuação
        scored_exercises.sort(key=lambda x: x[0], reverse=True)
        
        # Seleciona exercícios até preencher a duração
        for score, exercise in scored_exercises:
            if used_duration >= total_duration:
                break
            
            # Calcula duração recomendada para este exercício
            min_duration, max_duration = exercise.duration_range
            
            # Ajusta baseado no tempo restante e zona de FC
            remaining_time = total_duration - used_duration
            
            if current_zone.get("intensity") == "alta":
                recommended_duration = min(min_duration, remaining_time, 15)  # Máximo 15min em alta intensidade
            else:
                recommended_duration = min(max_duration, remaining_time, 30)  # Máximo 30min
            
            if recommended_duration >= min_duration:
                selected.append({
                    "exercise_id": exercise.id,
                    "name": exercise.name,
                    "type": exercise.type.value,
                    "description": exercise.description,
                    "recommended_duration": recommended_duration,
                    "instructions": exercise.instructions,
                    "muscle_groups": exercise.muscle_groups,
                    "safety_notes": exercise.safety_notes,
                    "estimated_calories": self._estimate_calories(exercise, recommended_duration, user)
                })
                
                used_duration += recommended_duration
        
        return selected
    
    def _estimate_calories(self, exercise, duration: int, user) -> int:
        """Estima calorias para um exercício"""
        
        fitness_level = user.fitness_level.value
        calories_per_minute = exercise.calories_per_minute.get(fitness_level, 5.0)
        
        # Ajusta baseado no peso (estimativa grosseira)
        weight_factor = user.weight / 70.0  # 70kg como base
        
        total_calories = int(calories_per_minute * duration * weight_factor)
        return max(total_calories, duration)  # Mínimo 1 cal/min
    
    def _estimate_resting_hr(self, age: int, fitness_level: str) -> int:
        """Estima FC de repouso"""
        base_values = {
            "beginner": 75,
            "intermediate": 65,
            "advanced": 55
        }
        
        base = base_values.get(fitness_level, 70)
        
        # Ajuste por idade
        if age > 60:
            base += 8
        elif age > 40:
            base += 5
        elif age < 25:
            base -= 5
        
        return base
    
    def _get_safety_notes(self, user, current_zone: dict) -> List[str]:
        """Gera notas de segurança personalizadas"""
        
        safety_notes = [
            "Monitore sua frequência cardíaca regularmente",
            "Pare se sentir dor ou desconforto",
            "Mantenha-se hidratado durante o exercício"
        ]
        
        # Notas específicas por zona de FC
        zone_id = current_zone.get("zone_id", "")
        if zone_id in ["zona_4", "zona_5"]:
            safety_notes.append("Intensidade alta - sessões mais curtas")
            safety_notes.append("Tenha períodos de recuperação entre exercícios")
        
        # Notas por condições de saúde
        for condition in user.health_conditions:
            if condition.value == "diabetes":
                safety_notes.append("Monitore glicemia antes e após exercícios")
            elif condition.value == "hypertension":
                safety_notes.append("Evite exercícios isométricos prolongados")
            elif condition.value == "heart_disease":
                safety_notes.append("Mantenha FC abaixo dos limites recomendados pelo médico")
        
        # Notas por idade
        if user.age > 65:
            safety_notes.append("Inclua exercícios de equilíbrio e coordenação")
            safety_notes.append("Aqueça por mais tempo antes dos exercícios")
        
        return safety_notes