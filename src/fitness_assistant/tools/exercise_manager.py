# src/fitness_assistant/tools/exercise_manager.py
"""
Gerenciador de exercícios e recomendações
"""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ..database.repositories import exercise_repo, user_repo
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
            safety_check = check_heart_rate_safety(current_hr, user.age, user.fitness_level)
            if not safety_check["safe"]:
                return {
                    "status": "warning",
                    "message": "FC fora da zona segura",
                    "safety_alerts": safety_check["alerts"],
                    "recommendations": ["Reduza a intensidade", "Consulte um profissional"]
                }
            
            # Calcula zonas de FC
            resting_hr = user.resting_heart_rate or self._estimate_resting_hr(user.age, user.fitness_level)
            hr_zones = calculate_heart_rate_zones(user.age, resting_hr)
            current_zone = determine_heart_rate_zone(current_hr, hr_zones["zones"])
            
            # Busca exercícios por tipo
            if workout_type == "mixed":
                exercise_types = ["cardio", "strength"]
            else:
                exercise_types = [workout_type]
            
            recommendations = []
            remaining_duration = session_duration
            
            for ex_type in exercise_types:
                exercises = await exercise_repo.get_exercises_by_type(ex_type)
                
                if exercises:
                    # Filtra por nível e equipamento
                    suitable_exercises = self._filter_exercises(
                        exercises, 
                        user.fitness_level, 
                        available_equipment or ["none"],
                        user.health_conditions
                    )
                    
                    if suitable_exercises:
                        duration_for_type = remaining_duration // len(exercise_types)
                        exercise = self._select_best_exercise(suitable_exercises, current_zone, user)
                        
                        recommendation = {
                            "exercise": {
                                "name": exercise.name,
                                "type": exercise.type,
                                "description": exercise.description,
                                "instructions": exercise.instructions
                            },
                            "duration_minutes": min(duration_for_type, exercise.duration_max),
                            "target_zone": current_zone,
                            "intensity_guidance": self._get_intensity_guidance(current_zone, user.fitness_level),
                            "safety_notes": exercise.safety_notes,
                            "modifications": self._get_personalized_modifications(exercise, user)
                        }
                        
                        recommendations.append(recommendation)
                        remaining_duration -= duration_for_type
            
            # Adiciona aquecimento e alongamento
            warm_up, cool_down = self._get_warm_up_cool_down(user.fitness_level, session_duration)
            
            return {
                "status": "success",
                "user_id": user_id,
                "current_hr": current_hr,
                "current_zone": current_zone,
                "session_plan": {
                    "warm_up": warm_up,
                    "main_exercises": recommendations,
                    "cool_down": cool_down,
                    "total_duration": session_duration
                },
                "safety_notes": safety_check.get("warnings", []),
                "hydration_reminder": "Mantenha-se hidratado durante o exercício"
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
            
            # Variações por nível
            if fitness_level == "beginner":
                variations.extend([
                    {
                        "name": f"{base_exercise.name} - Versão Iniciante",
                        "description": "Versão simplificada com menor intensidade",
                        "modifications": [
                            "Reduza amplitude de movimento",
                            "Use menos peso ou resistência",
                            "Faça mais pausas entre séries"
                        ]
                    }
                ])
            elif fitness_level == "advanced":
                variations.extend([
                    {
                        "name": f"{base_exercise.name} - Versão Avançada",
                        "description": "Versão mais desafiadora",
                        "modifications": [
                            "Aumente amplitude de movimento",
                            "Adicione peso ou resistência",
                            "Combine com outros movimentos"
                        ]
                    }
                ])
            
            # Modificações específicas
            if modifications_needed:
                for modification in modifications_needed:
                    if "joelho" in modification.lower():
                        variations.append({
                            "name": f"{base_exercise.name} - Proteção Joelho",
                            "description": "Adaptado para problemas no joelho",
                            "modifications": [
                                "Evite flexão profunda",
                                "Use suporte se necessário",
                                "Movimento controlado"
                            ]
                        })
                    elif "lombar" in modification.lower():
                        variations.append({
                            "name": f"{base_exercise.name} - Proteção Lombar",
                            "description": "Adaptado para problemas lombares",
                            "modifications": [
                                "Mantenha coluna neutra",
                                "Evite flexão excessiva",
                                "Use apoio se necessário"
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
                    "Progrida gradualmente"
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
            # Implementação simplificada - em produção viria do banco
            exercises_catalog = [
                {
                    "id": "walk_light",
                    "name": "Caminhada Leve",
                    "type": "cardio",
                    "difficulty": "beginner",
                    "equipment": ["none"],
                    "duration_range": [10, 60],
                    "muscle_groups": ["pernas", "core"]
                },
                {
                    "id": "squat_bodyweight", 
                    "name": "Agachamento Livre",
                    "type": "strength",
                    "difficulty": "beginner",
                    "equipment": ["none"],
                    "duration_range": [5, 20],
                    "muscle_groups": ["quadriceps", "glúteos"]
                },
                {
                    "id": "plank",
                    "name": "Prancha",
                    "type": "strength",
                    "difficulty": "intermediate",
                    "equipment": ["none"], 
                    "duration_range": [1, 10],
                    "muscle_groups": ["core", "ombros"]
                },
                {
                    "id": "push_ups",
                    "name": "Flexões",
                    "type": "strength",
                    "difficulty": "intermediate",
                    "equipment": ["none"],
                    "duration_range": [5, 15],
                    "muscle_groups": ["peito", "tríceps", "ombros"]
                }
            ]
            
            return exercises_catalog
            
        except Exception as e:
            logger.error(f"Erro ao buscar catálogo: {e}")
            return []
    
    def _estimate_resting_hr(self, age: int, fitness_level: str) -> int:
        """Estima FC de repouso baseada na idade e nível"""
        
        base_resting = {
            "beginner": 75,
            "intermediate": 65,
            "advanced": 55
        }
        
        base = base_resting.get(fitness_level, 70)
        
        # Ajusta por idade
        if age > 50:
            base += 5
        elif age < 25:
            base -= 5
        
        return base
    
    def _filter_exercises(
        self,
        exercises: List,
        fitness_level: str,
        available_equipment: List[str],
        health_conditions: List[str]
    ) -> List:
        """Filtra exercícios por critérios"""
        
        suitable = []
        
        for exercise in exercises:
            # Verifica equipamento
            exercise_equipment = getattr(exercise, 'equipment_needed', ['none'])
            if not any(eq in available_equipment for eq in exercise_equipment):
                continue
            
            # Verifica contraindicações
            contraindications = getattr(exercise, 'contraindications', [])
            if any(condition in contraindications for condition in health_conditions):
                continue
            
            # Verifica nível de dificuldade
            difficulty = getattr(exercise, 'difficulty_level', 'moderate')
            if fitness_level == "beginner" and difficulty in ["high", "very_high"]:
                continue
            
            suitable.append(exercise)
        
        return suitable
    
    def _select_best_exercise(self, exercises: List, current_zone: Dict, user) -> Any:
        """Seleciona melhor exercício baseado no contexto"""
        
        # Lógica simplificada - seleciona primeiro adequado
        # Em produção, usaria algoritmo mais sofisticado
        
        # Prioriza exercícios que combinam com a zona atual
        zone_name = current_zone.get("zone_name", "").lower()
        
        for exercise in exercises:
            # Se está em zona aeróbica, prioriza cardio
            if "aeróbica" in zone_name and exercise.type == "cardio":
                return exercise
            # Se está em zona baixa, prioriza força
            elif "recuperação" in zone_name and exercise.type == "strength":
                return exercise
        
        # Retorna primeiro disponível
        return exercises[0] if exercises else None
    
    def _get_intensity_guidance(self, current_zone: Dict, fitness_level: str) -> List[str]:
        """Gera orientações de intensidade"""
        
        guidance = []
        zone_name = current_zone.get("zone_name", "").lower()
        
        if "recuperação" in zone_name:
            guidance.extend([
                "Mantenha ritmo leve e confortável",
                "Você deve conseguir conversar normalmente",
                "Foque na técnica dos movimentos"
            ])
        elif "aeróbica" in zone_name:
            guidance.extend([
                "Mantenha ritmo moderado e sustentável",
                "Respiração ligeiramente acelerada",
                "Deve conseguir falar frases curtas"
            ])
        elif "limiar" in zone_name or "potência" in zone_name:
            guidance.extend([
                "Intensidade alta, monitore FC",
                "Períodos curtos nesta intensidade",
                "Inclua intervalos de recuperação"
            ])
        
        # Ajustes por nível fitness
        if fitness_level == "beginner":
            guidance.append("Comece devagar e aumente gradualmente")
        elif fitness_level == "advanced":
            guidance.append("Pode explorar intensidades mais altas")
        
        return guidance
    
    def _get_personalized_modifications(self, exercise, user) -> List[str]:
        """Gera modificações personalizadas"""
        
        modifications = []
        
        # Baseado na idade
        if user.age > 65:
            modifications.extend([
                "Movimento mais lento e controlado",
                "Use apoio se necessário",
                "Foque no equilíbrio"
            ])
        elif user.age < 25:
            modifications.append("Pode explorar maior amplitude de movimento")
        
        # Baseado no nível fitness
        if user.fitness_level == "beginner":
            modifications.extend([
                "Comece com menos repetições",
                "Priorize forma sobre intensidade",
                "Descanse mais entre séries"
            ])
        
        # Baseado em condições de saúde
        for condition in user.health_conditions:
            if condition == "diabetes":
                modifications.append("Monitore glicemia se sessão longa")
            elif condition == "hypertension":
                modifications.append("Evite prender respiração")
            elif condition == "arthritis":
                modifications.append("Amplitude de movimento confortável")
        
        return modifications
    
    def _get_warm_up_cool_down(self, fitness_level: str, session_duration: int) -> tuple:
        """Retorna aquecimento e alongamento apropriados"""
        
        # Duração do aquecimento baseada na sessão
        warm_up_duration = max(5, session_duration // 6)  # 5-10 min
        cool_down_duration = max(5, session_duration // 8)  # 5-8 min
        
        warm_up = {
            "duration_minutes": warm_up_duration,
            "exercises": [
                "Movimentação articular (2-3 min)",
                "Caminhada leve (2-3 min)",
                "Alongamento dinâmico (2-4 min)"
            ],
            "intensity": "Muito leve, gradual"
        }
        
        cool_down = {
            "duration_minutes": cool_down_duration,
            "exercises": [
                "Caminhada lenta (2-3 min)",
                "Alongamento estático (3-5 min)",
                "Respiração profunda (1-2 min)"
            ],
            "intensity": "Muito leve, relaxante"
        }
        
        # Ajustes por nível
        if fitness_level == "beginner":
            warm_up["exercises"].append("Movimentos extras de mobilidade")
            cool_down["exercises"].append("Alongamento prolongado")
        
        return warm_up, cool_down
