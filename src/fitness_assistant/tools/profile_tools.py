"""
Ferramentas MCP para gestão de perfis de usuário
"""
from typing import List, Dict, Any
from ..models.user import UserProfile, FitnessLevel, HealthCondition, ExercisePreference
from ..core.database import get_user_profile, save_user_profile, delete_user_profile
from ..utils.validators import validate_user_data
from ..utils.safety import generate_health_recommendations

def register_profile_tools(mcp):
    """Registra todas as ferramentas de perfil no servidor MCP"""
    
    @mcp.tool()
    def create_user_profile(
        user_id: str,
        age: int,
        weight: float,
        height: float,
        fitness_level: str,
        health_conditions: List[str] = [],
        preferences: List[str] = [],
        resting_heart_rate: int = None,
        goals: List[str] = []
    ) -> Dict[str, Any]:
        """
        Cria um novo perfil de usuário com validação completa
        
        Args:
            user_id: Identificador único do usuário
            age: Idade em anos (13-120)
            weight: Peso em kg
            height: Altura em metros
            fitness_level: beginner, intermediate ou advanced
            health_conditions: Lista de condições médicas
            preferences: Lista de preferências de exercício
            resting_heart_rate: FC de repouso (opcional)
            goals: Lista de objetivos fitness
        """
        try:
            # Valida dados de entrada
            validate_user_data(age, weight, height)
            
            # Converte strings para enums
            fitness_enum = FitnessLevel(fitness_level.lower())
            health_enums = [HealthCondition(cond.lower()) for cond in health_conditions]
            pref_enums = [ExercisePreference(pref.lower()) for pref in preferences]
            
            # Cria perfil
            profile = UserProfile(
                user_id=user_id,
                age=age,
                weight=weight,
                height=height,
                fitness_level=fitness_enum,
                health_conditions=health_enums,
                preferences=pref_enums,
                resting_heart_rate=resting_heart_rate,
                goals=goals
            )
            
            # Salva no banco
            save_user_profile(profile)
            
            # Gera recomendações de saúde
            health_recommendations = generate_health_recommendations(profile)
            
            return {
                "status": "success",
                "message": f"Perfil criado com sucesso para {user_id}",
                "profile": profile.dict(),
                "bmi": profile.bmi,
                "bmi_category": profile.bmi_category,
                "health_recommendations": health_recommendations
            }
            
        except ValueError as e:
            return {
                "status": "error",
                "message": f"Erro de validação: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Erro interno: {str(e)}"
            }
    
    @mcp.tool()
    def get_user_profile_info(user_id: str) -> Dict[str, Any]:
        """
        Recupera informações completas do perfil do usuário
        """
        try:
            profile = get_user_profile(user_id)
            if not profile:
                return {
                    "status": "error",
                    "message": f"Usuário {user_id} não encontrado"
                }
            
            return {
                "status": "success",
                "profile": profile.dict(),
                "bmi": profile.bmi,
                "bmi_category": profile.bmi_category,
                "profile_completeness": calculate_profile_completeness(profile)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro ao recuperar perfil: {str(e)}"
            }
    
    @mcp.tool()
    def update_user_profile(
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Atualiza campos específicos do perfil do usuário
        
        Args:
            user_id: ID do usuário
            updates: Dicionário com campos a serem atualizados
        """
        try:
            profile = get_user_profile(user_id)
            if not profile:
                return {
                    "status": "error",
                    "message": f"Usuário {user_id} não encontrado"
                }
            
            # Atualiza campos permitidos
            allowed_fields = [
                'weight', 'height', 'fitness_level', 'health_conditions',
                'preferences', 'resting_heart_rate', 'goals'
            ]
            
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(profile, field, value)
            
            # Atualiza timestamp
            profile.update_timestamp()
            
            # Salva alterações
            save_user_profile(profile)
            
            return {
                "status": "success",
                "message": "Perfil atualizado com sucesso",
                "updated_fields": list(updates.keys()),
                "profile": profile.dict()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro ao atualizar perfil: {str(e)}"
            }
    
    @mcp.tool()
    def delete_user_profile_tool(user_id: str) -> Dict[str, Any]:
        """
        Remove completamente o perfil do usuário
        """
        try:
            success = delete_user_profile(user_id)
            if success:
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
            return {
                "status": "error",
                "message": f"Erro ao remover perfil: {str(e)}"
            }
    
    @mcp.tool()
    def validate_profile_completeness(user_id: str) -> Dict[str, Any]:
        """
        Verifica completude do perfil e sugere melhorias
        """
        try:
            profile = get_user_profile(user_id)
            if not profile:
                return {
                    "status": "error",
                    "message": f"Usuário {user_id} não encontrado"
                }
            
            completeness = calculate_profile_completeness(profile)
            suggestions = generate_profile_suggestions(profile)
            
            return {
                "status": "success",
                "completeness_score": completeness["score"],
                "missing_fields": completeness["missing"],
                "recommendations": suggestions,
                "profile_strength": get_profile_strength(completeness["score"])
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro na validação: {str(e)}"
            }

def calculate_profile_completeness(profile: UserProfile) -> Dict[str, Any]:
    """Calcula completude do perfil"""
    required_fields = ['age', 'weight', 'height', 'fitness_level']
    optional_fields = ['resting_heart_rate', 'health_conditions', 'preferences', 'goals']
    
    filled_required = sum(1 for field in required_fields if getattr(profile, field) is not None)
    filled_optional = sum(1 for field in optional_fields 
                         if getattr(profile, field) and 
                         (not isinstance(getattr(profile, field), list) or len(getattr(profile, field)) > 0))
    
    total_possible = len(required_fields) + len(optional_fields)
    total_filled = filled_required + filled_optional
    
    score = (total_filled / total_possible) * 100
    
    missing = []
    if not profile.resting_heart_rate:
        missing.append("resting_heart_rate")
    if not profile.health_conditions:
        missing.append("health_conditions")
    if not profile.preferences:
        missing.append("preferences")
    if not profile.goals:
        missing.append("goals")
    
    return {
        "score": round(score, 1),
        "missing": missing,
        "filled_required": filled_required,
        "filled_optional": filled_optional
    }

def generate_profile_suggestions(profile: UserProfile) -> List[str]:
    """Gera sugestões para melhorar o perfil"""
    suggestions = []
    
    if not profile.resting_heart_rate:
        suggestions.append("Adicione sua FC de repouso para recomendações mais precisas")
    
    if not profile.health_conditions:
        suggestions.append("Informe condições de saúde relevantes para exercícios mais seguros")
    
    if len(profile.preferences) < 2:
        suggestions.append("Adicione mais preferências de exercício para recomendações variadas")
    
    if not profile.goals:
        suggestions.append("Defina objetivos específicos para acompanhar seu progresso")
    
    if profile.bmi_category in ["sobrepeso", "obesidade"]:
        suggestions.append("Considere consultar um profissional de saúde antes de iniciar exercícios intensos")
    
    return suggestions

def get_profile_strength(score: float) -> str:
    """Determina força do perfil baseado na completude"""
    if score >= 90:
        return "Excelente"
    elif score >= 75:
        return "Bom"
    elif score >= 60:
        return "Regular"
    else:
        return "Incompleto"