# src/fitness_assistant/tools/profile_manager.py (atualizado para PostgreSQL)
"""
Gerenciador de perfis com PostgreSQL
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from ..database.repositories import user_repo
from ..models.user import FitnessLevel, HealthCondition, ExercisePreference
from ..utils.validators import validate_user_data
from ..utils.safety import generate_health_recommendations

logger = logging.getLogger(__name__)

class ProfileManager:
    """Gerencia operações de perfil com PostgreSQL"""
    
    async def create_profile(
        self,
        user_id: str,
        age: int,
        weight: float,
        height: float,
        fitness_level: str,
        health_conditions: List[str] = None,
        preferences: List[str] = None,
        resting_heart_rate: Optional[int] = None,
        goals: List[str] = None
    ) -> Dict[str, Any]:
        """Cria novo perfil de usuário no PostgreSQL"""
        
        try:
            # Validações
            validate_user_data(age, weight, height)
            
            # Verifica se usuário já existe
            existing_user = await user_repo.get_user_by_id(user_id)
            if existing_user:
                return {
                    "status": "error",
                    "message": f"Usuário {user_id} já existe"
                }
            
            # Valida enums
            try:
                fitness_enum = FitnessLevel(fitness_level.lower())
                health_enums = [HealthCondition(cond.lower()).value for cond in (health_conditions or [])]
                pref_enums = [ExercisePreference(pref.lower()).value for pref in (preferences or [])]
            except ValueError as e:
                return {
                    "status": "error",
                    "message": f"Valor inválido: {str(e)}"
                }
            
            # Dados para criação
            user_data = {
                "user_id": user_id,
                "age": age,
                "weight": weight,
                "height": height,
                "fitness_level": fitness_enum.value,
                "health_conditions": health_enums,
                "preferences": pref_enums,
                "resting_heart_rate": resting_heart_rate,
                "goals": goals or []
            }
            
            # Cria no banco
            profile = await user_repo.create_user(user_data)
            
            # Gera recomendações
            health_recs = generate_health_recommendations_from_data(user_data)
            
            logger.info(f"Perfil criado para usuário {user_id}")
            
            return {
                "status": "success",
                "message": f"Perfil criado para {user_id}",
                "profile": {
                    "user_id": profile.user_id,
                    "age": profile.age,
                    "weight": profile.weight,
                    "height": profile.height,
                    "fitness_level": profile.fitness_level,
                    "health_conditions": profile.health_conditions,
                    "preferences": profile.preferences,
                    "resting_heart_rate": profile.resting_heart_rate,
                    "goals": profile.goals,
                    "created_at": profile.created_at.isoformat()
                },
                "bmi": profile.bmi,
                "bmi_category": profile.bmi_category,
                "health_recommendations": health_recs,
                "completeness_score": self._calculate_completeness_from_db(profile)
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar perfil para {user_id}: {e}")
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }
    
    async def get_profile(self, user_id: str) -> Dict[str, Any]:
        """Recupera perfil do usuário do PostgreSQL"""
        
        try:
            profile = await user_repo.get_user_by_id(user_id)
            if not profile:
                return {
                    "status": "error",
                    "message": f"Usuário {user_id} não encontrado"
                }
            
            return {
                "status": "success",
                "profile": {
                    "user_id": profile.user_id,
                    "age": profile.age,
                    "weight": profile.weight,
                    "height": profile.height,
                    "fitness_level": profile.fitness_level,
                    "health_conditions": profile.health_conditions,
                    "preferences": profile.preferences,
                    "resting_heart_rate": profile.resting_heart_rate,
                    "goals": profile.goals,
                    "created_at": profile.created_at.isoformat(),
                    "updated_at": profile.updated_at.isoformat()
                },
                "bmi": profile.bmi,
                "bmi_category": profile.bmi_category,
                "completeness_score": self._calculate_completeness_from_db(profile),
                "recommendations": self._get_profile_suggestions_from_db(profile)
            }
            
        except Exception as e:
            logger.error(f"Erro ao recuperar perfil {user_id}: {e}")
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }
    
    async def update_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza perfil do usuário no PostgreSQL"""
        
        try:
            # Verifica se usuário existe
            existing_profile = await user_repo.get_user_by_id(user_id)
            if not existing_profile:
                return {
                    "status": "error",
                    "message": f"Usuário {user_id} não encontrado"
                }
            
            # Campos permitidos para atualização
            allowed_fields = [
                'weight', 'height', 'fitness_level', 'health_conditions',
                'preferences', 'resting_heart_rate', 'goals'
            ]
            
            # Filtra apenas campos permitidos
            filtered_updates = {
                field: value for field, value in updates.items() 
                if field in allowed_fields
            }
            
            if not filtered_updates:
                return {
                    "status": "error",
                    "message": "Nenhum campo válido para atualização"
                }
            
            # Validações específicas
            if 'weight' in filtered_updates or 'height' in filtered_updates:
                weight = filtered_updates.get('weight', existing_profile.weight)
                height = filtered_updates.get('height', existing_profile.height)
                validate_user_data(existing_profile.age, weight, height)
            
            # Valida enums se presentes
            if 'fitness_level' in filtered_updates:
                try:
                    fitness_enum = FitnessLevel(filtered_updates['fitness_level'].lower())
                    filtered_updates['fitness_level'] = fitness_enum.value
                except ValueError:
                    return {
                        "status": "error",
                        "message": f"Nível de fitness inválido: {filtered_updates['fitness_level']}"
                    }
            
            if 'health_conditions' in filtered_updates:
                try:
                    health_enums = [HealthCondition(cond.lower()).value for cond in filtered_updates['health_conditions']]
                    filtered_updates['health_conditions'] = health_enums
                except ValueError as e:
                    return {
                        "status": "error",
                        "message": f"Condição de saúde inválida: {str(e)}"
                    }
            
            if 'preferences' in filtered_updates:
                try:
                    pref_enums = [ExercisePreference(pref.lower()).value for pref in filtered_updates['preferences']]
                    filtered_updates['preferences'] = pref_enums
                except ValueError as e:
                    return {
                        "status": "error",
                        "message": f"Preferência inválida: {str(e)}"
                    }
            
            # Atualiza no banco
            updated_profile = await user_repo.update_user(user_id, filtered_updates)
            
            if not updated_profile:
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
                    "user_id": updated_profile.user_id,
                    "age": updated_profile.age,
                    "weight": updated_profile.weight,
                    "height": updated_profile.height,
                    "fitness_level": updated_profile.fitness_level,
                    "health_conditions": updated_profile.health_conditions,
                    "preferences": updated_profile.preferences,
                    "resting_heart_rate": updated_profile.resting_heart_rate,
                    "goals": updated_profile.goals,
                    "updated_at": updated_profile.updated_at.isoformat()
                },
                "new_completeness_score": self._calculate_completeness_from_db(updated_profile)
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
    
    async def list_profiles(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Lista perfis de usuários"""
        
        try:
            profiles = await user_repo.list_users(limit, offset)
            
            profiles_data = []
            for profile in profiles:
                profiles_data.append({
                    "user_id": profile.user_id,
                    "age": profile.age,
                    "fitness_level": profile.fitness_level,
                    "bmi": profile.bmi,
                    "created_at": profile.created_at.isoformat(),
                    "completeness": self._calculate_completeness_from_db(profile)
                })
            
            return {
                "status": "success",
                "profiles": profiles_data,
                "total": len(profiles_data),
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar perfis: {e}")
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }
    
    def _calculate_completeness_from_db(self, profile) -> float:
        """Calcula completude do perfil do banco"""
        required_fields = 4  # age, weight, height, fitness_level
        optional_fields = 0
        
        if profile.resting_heart_rate:
            optional_fields += 1
        if profile.health_conditions:
            optional_fields += 1
        if profile.preferences:
            optional_fields += 1
        if profile.goals:
            optional_fields += 1
        
        total_possible = required_fields + 4  # 4 campos opcionais
        total_filled = required_fields + optional_fields
        
        return round((total_filled / total_possible) * 100, 1)
    
    def _get_profile_suggestions_from_db(self, profile) -> List[str]:
        """Gera sugestões baseadas no perfil do banco"""
        suggestions = []
        
        if not profile.resting_heart_rate:
            suggestions.append("Adicione FC de repouso para recomendações precisas")
        
        if not profile.health_conditions:
            suggestions.append("Informe condições de saúde para exercícios seguros")
        
        if not profile.preferences or len(profile.preferences) < 2:
            suggestions.append("Adicione mais preferências para variedade")
        
        if not profile.goals:
            suggestions.append("Defina objetivos para acompanhar progresso")
        
        return suggestions

def generate_health_recommendations_from_data(user_data: Dict[str, Any]) -> List[str]:
    """Gera recomendações de saúde a partir dos dados"""
    recommendations = []
    
    # Verificações por condição de saúde
    for condition in user_data.get('health_conditions', []):
        if condition == "diabetes":
            recommendations.extend([
                "Monitore glicemia antes e após exercícios",
                "Tenha carboidratos disponíveis durante exercícios",
                "Evite exercícios em jejum prolongado"
            ])
        elif condition == "hypertension":
            recommendations.extend([
                "Evite exercícios isométricos prolongados",
                "Monitore pressão arterial regularmente",
                "Hidrate-se adequadamente"
            ])
        elif condition == "heart_disease":
            recommendations.extend([
                "Necessária liberação médica para exercícios",
                "Monitore frequência cardíaca constantemente",
                "Evite exercícios de alta intensidade"
            ])
    
    # Verificações por idade
    age = user_data.get('age', 30)
    if age > 65:
        recommendations.extend([
            "Inclua aquecimento prolongado (10-15 minutos)",
            "Priorize exercícios de equilíbrio",
            "Considere exercícios supervisionados"
        ])
    elif age < 18:
        recommendations.extend([
            "Foque em diversão e variedade",
            "Evite treinamento de força muito intenso",
            "Supervisão adulta recomendada"
        ])
    
    # Verificações por IMC
    weight = user_data.get('weight', 70)
    height = user_data.get('height', 1.7)
    if weight and height:
        bmi = weight / (height ** 2)
        if bmi > 30:
            recommendations.extend([
                "Inicie com exercícios de baixo impacto",
                "Priorize atividades aquáticas se disponível",
                "Aumente intensidade gradualmente"
            ])
        elif bmi < 18.5:
            recommendations.extend([
                "Combine exercícios com orientação nutricional",
                "Evite exercícios muito intensos inicialmente",
                "Foque em ganho de massa muscular"
            ])
    
    # Recomendações gerais se lista vazia
    if not recommendations:
        recommendations = [
            "Mantenha hidratação adequada",
            "Faça aquecimento antes dos exercícios",
            "Escute seu corpo e descanse quando necessário"
        ]
    
    return recommendations
