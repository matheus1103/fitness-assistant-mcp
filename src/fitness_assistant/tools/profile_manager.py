# src/fitness_assistant/tools/profile_manager.py
"""
Gerenciador de perfis de usuário
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from ..database.repositories import user_repo
from ..models.user import FitnessLevel, HealthCondition, ExercisePreference
from ..utils.validators import validate_user_data, ValidationError
from ..utils.safety import generate_health_recommendations

logger = logging.getLogger(__name__)


class ProfileManager:
    """Gerencia operações de perfil de usuário"""
    
    async def create_profile(
        self,
        user_id: str,
        age: int,
        weight: float,
        height: float,
        fitness_level: str,
        gender: Optional[str] = None,
        health_conditions: List[str] = None,
        preferences: List[str] = None,
        resting_heart_rate: Optional[int] = None,
        goals: List[str] = None
    ) -> Dict[str, Any]:
        """Cria novo perfil de usuário"""
        
        try:
            # Validações básicas
            validate_user_data(age, weight, height)
            
            # Verifica se usuário já existe
            existing_user = await user_repo.get_user_by_id(user_id)
            if existing_user:
                return {
                    "status": "error",
                    "message": f"Usuário {user_id} já existe"
                }
            
            # Remove usuário de teste se já existir
            if user_id.startswith("test_") or user_id.startswith("gym_member_"):
                await user_repo.delete_user(user_id)
            
            # Normaliza dados
            health_conditions = health_conditions or []
            preferences = preferences or []
            goals = goals or []
            
            # Valida enums
            try:
                fitness_enum = FitnessLevel(fitness_level.lower())
                
                # Valida condições de saúde
                valid_health_conditions = []
                for condition in health_conditions:
                    try:
                        health_enum = HealthCondition(condition.lower())
                        valid_health_conditions.append(health_enum)
                    except ValueError:
                        logger.warning(f"Condição de saúde inválida ignorada: {condition}")
                
                # Valida preferências
                valid_preferences = []
                for pref in preferences:
                    try:
                        pref_enum = ExercisePreference(pref.lower())
                        valid_preferences.append(pref_enum)
                    except ValueError:
                        logger.warning(f"Preferência inválida ignorada: {pref}")
                
            except ValueError as e:
                return {
                    "status": "error",
                    "message": f"Nível de fitness inválido: {fitness_level}"
                }
            
            # Dados para criação
            user_data = {
                "user_id": user_id,
                "age": age,
                "weight": weight,
                "height": height,
                "fitness_level": fitness_enum,
                "health_conditions": valid_health_conditions,
                "preferences": valid_preferences,
                "resting_heart_rate": resting_heart_rate,
                "goals": goals
            }
            
            # Cria usuário
            user = await user_repo.create_user(user_data)
            
            # Gera recomendações de saúde
            health_recommendations = generate_health_recommendations(user)
            
            logger.info(f"Perfil criado para usuário {user_id}")
            
            return {
                "status": "success",
                "message": "Perfil criado com sucesso",
                "profile": {
                    "user_id": user.user_id,
                    "age": user.age,
                    "weight": user.weight,
                    "height": user.height,
                    "bmi": getattr(user, 'bmi', None),
                    "bmi_category": getattr(user, 'bmi_category', None),
                    "fitness_level": getattr(getattr(user, 'fitness_level', None), 'value', getattr(user, 'fitness_level', None)),
                    "gender": getattr(getattr(user, 'gender', None), 'value', getattr(user, 'gender', None)),
                    "health_conditions": [getattr(hc, 'value', hc) for hc in getattr(user, 'health_conditions', [])],
                    "preferences": [getattr(p, 'value', p) for p in getattr(user, 'preferences', [])],
                    "goals": getattr(user, 'goals', None),
                    "created_at": getattr(user, 'created_at', None).isoformat() if getattr(user, 'created_at', None) else None
                },
                "health_recommendations": health_recommendations
            }
            
        except ValidationError as e:
            return {
                "status": "error",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Erro ao criar perfil para {user_id}: {e}")
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }
    
    async def get_profile(self, user_id: str) -> Dict[str, Any]:
        """Obtém perfil do usuário"""
        
        try:
            user = await user_repo.get_user_by_id(user_id)
            
            if not user:
                return {
                    "status": "error",
                    "message": f"Usuário {user_id} não encontrado"
                }
            
            return {
                "status": "success",
                "profile": {
                    "user_id": user.user_id,
                    "age": user.age,
                    "weight": user.weight,
                    "height": user.height,
                    "bmi": user.bmi,
                    "bmi_category": user.bmi_category,
                    "fitness_level": getattr(user.fitness_level, 'value', user.fitness_level) if user.fitness_level else None,
                    "gender": getattr(user.gender, 'value', user.gender) if user.gender else None,
                    "health_conditions": [hc.value for hc in user.health_conditions],
                    "preferences": [p.value for p in user.preferences],
                    "resting_heart_rate": user.resting_heart_rate,
                    "goals": user.goals,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar perfil {user_id}: {e}")
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }
    
    async def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza perfil do usuário"""
        
        try:
            # Verifica se usuário existe
            existing_user = await user_repo.get_user_by_id(user_id)
            if not existing_user:
                return {
                    "status": "error",
                    "message": f"Usuário {user_id} não encontrado"
                }
            
            # Remove campos que não devem ser atualizados diretamente
            filtered_updates = {k: v for k, v in updates.items() 
                              if k not in ['user_id', 'created_at', 'updated_at']}
            
            # Validações específicas
            if 'age' in filtered_updates or 'weight' in filtered_updates or 'height' in filtered_updates:
                age = filtered_updates.get('age', existing_user.age)
                weight = filtered_updates.get('weight', existing_user.weight)
                height = filtered_updates.get('height', existing_user.height)
                
                validate_user_data(age, weight, height)
            
            # Valida e converte enums se presentes
            if 'fitness_level' in filtered_updates:
                try:
                    fitness_enum = FitnessLevel(filtered_updates['fitness_level'].lower())
                    filtered_updates['fitness_level'] = fitness_enum
                except ValueError:
                    return {
                        "status": "error",
                        "message": f"Nível de fitness inválido: {filtered_updates['fitness_level']}"
                    }
            
            if 'health_conditions' in filtered_updates:
                try:
                    health_enums = []
                    for cond in filtered_updates['health_conditions']:
                        health_enums.append(HealthCondition(cond.lower()))
                    filtered_updates['health_conditions'] = health_enums
                except ValueError as e:
                    return {
                        "status": "error",
                        "message": f"Condição de saúde inválida: {str(e)}"
                    }
            
            if 'preferences' in filtered_updates:
                try:
                    pref_enums = []
                    for pref in filtered_updates['preferences']:
                        pref_enums.append(ExercisePreference(pref.lower()))
                    filtered_updates['preferences'] = pref_enums
                except ValueError as e:
                    return {
                        "status": "error",
                        "message": f"Preferência inválida: {str(e)}"
                    }
            
            # Atualiza usuário
            updated_user = await user_repo.update_user(user_id, filtered_updates)
            
            if not updated_user:
                return {
                    "status": "error",
                    "message": "Erro ao atualizar perfil"
                }
            
            logger.info(f"Perfil atualizado para usuário {user_id}")
            
            return {
                "status": "success",
                "message": "Perfil atualizado com sucesso",
                "updated_fields": list(filtered_updates.keys()),
                "profile": {
                    "user_id": updated_user.user_id,
                    "age": updated_user.age,
                    "weight": updated_user.weight,
                    "height": updated_user.height,
                    "bmi": updated_user.bmi,
                    "bmi_category": updated_user.bmi_category,
                    "fitness_level": updated_user.fitness_level.value,
                    "health_conditions": [hc.value for hc in updated_user.health_conditions],
                    "preferences": [p.value for p in updated_user.preferences],
                    "updated_at": updated_user.updated_at.isoformat()
                }
            }
            
        except ValidationError as e:
            return {
                "status": "error",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Erro ao atualizar perfil {user_id}: {e}")
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }
    
    async def delete_profile(self, user_id: str) -> Dict[str, Any]:
        """Remove perfil do usuário"""
        
        try:
            success = await user_repo.delete_user(user_id)
            
            if success:
                logger.info(f"Perfil removido para usuário {user_id}")
                return {
                    "status": "success",
                    "message": f"Perfil de {user_id} removido com sucesso"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Usuário {user_id} não encontrado"
                }
                
        except Exception as e:
            logger.error(f"Erro ao remover perfil {user_id}: {e}")
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }
    
    async def list_profiles(self) -> Dict[str, Any]:
        """Lista todos os perfis"""
        
        try:
            users = await user_repo.get_all_users()
            
            profiles = []
            for user in users:
                profiles.append({
                    "user_id": user.user_id,
                    "age": user.age,
                    "fitness_level": getattr(user.fitness_level, 'value', user.fitness_level) if user.fitness_level else None,
                    "gender": getattr(user.gender, 'value', user.gender) if user.gender else None,
                    "bmi": user.bmi,
                    "created_at": user.created_at.isoformat()
                })
            
            return {
                "status": "success",
                "count": len(profiles),
                "profiles": profiles
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar perfis: {e}")
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }
    
    async def validate_profile_completeness(self, user_id: str) -> Dict[str, Any]:
        """Verifica completude do perfil e sugere melhorias"""
        
        try:
            user = await user_repo.get_user_by_id(user_id)
            if not user:
                return {
                    "status": "error",
                    "message": f"Usuário {user_id} não encontrado"
                }
            
            # Calcula completude
            required_fields = ['age', 'weight', 'height', 'fitness_level']
            optional_fields = ['resting_heart_rate', 'health_conditions', 'preferences', 'goals']
            
            filled_required = sum(1 for field in required_fields 
                                if getattr(user, field) is not None)
            filled_optional = sum(1 for field in optional_fields 
                                if getattr(user, field) and len(getattr(user, field)) > 0)
            
            total_fields = len(required_fields) + len(optional_fields)
            completeness_score = ((filled_required * 2) + filled_optional) / (len(required_fields) * 2 + len(optional_fields)) * 100
            
            # Identifica campos faltando
            missing_fields = []
            for field in required_fields:
                if getattr(user, field) is None:
                    missing_fields.append(field)
            
            suggestions = []
            if not user.resting_heart_rate:
                suggestions.append("Adicione sua frequência cardíaca de repouso para recomendações mais precisas")
            if not user.health_conditions:
                suggestions.append("Informe condições de saúde relevantes para exercícios mais seguros")
            if not user.preferences:
                suggestions.append("Adicione suas preferências de exercício para recomendações personalizadas")
            if not user.goals:
                suggestions.append("Defina seus objetivos fitness para planos mais direcionados")
            
            # Determina força do perfil
            if completeness_score >= 90:
                profile_strength = "Excelente"
            elif completeness_score >= 75:
                profile_strength = "Bom"
            elif completeness_score >= 50:
                profile_strength = "Regular"
            else:
                profile_strength = "Incompleto"
            
            return {
                "status": "success",
                "user_id": user_id,
                "completeness_score": round(completeness_score, 1),
                "profile_strength": profile_strength,
                "missing_required_fields": missing_fields,
                "suggestions": suggestions,
                "health_recommendations": generate_health_recommendations(user)
            }
            
        except Exception as e:
            logger.error(f"Erro ao validar completude do perfil {user_id}: {e}")
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }