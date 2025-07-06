# src/fitness_assistant/tools/heart_rate_manager.py
"""
Gerenciador de frequência cardíaca
"""
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from ..database.repositories.user_repo import user_repo
from ..utils.calculations import calculate_heart_rate_zones, determine_heart_rate_zone
from ..utils.safety import check_heart_rate_safety

logger = logging.getLogger(__name__)


class HeartRateManager:
    """Gerencia análises de frequência cardíaca"""
    
    async def calculate_zones(self, age: int, resting_hr: int) -> Dict[str, Any]:
        """Calcula zonas de FC detalhadas"""
        
        try:
            zones_data = calculate_heart_rate_zones(age, resting_hr, method="karvonen")
            
            # Adiciona informações extras para cada zona
            for zone_id, zone_info in zones_data["zones"].items():
                zone_info["recommended_duration"] = self._get_zone_duration(zone_id)
                zone_info["example_activities"] = self._get_zone_activities(zone_id)
                zone_info["training_focus"] = self._get_zone_focus(zone_id)
            
            return {
                "status": "success",
                "age": age,
                "resting_hr": resting_hr,
                "max_hr": zones_data["max_hr"],
                "hr_reserve": zones_data["max_hr"] - resting_hr,
                "zones": zones_data["zones"],
                "recommendations": self._get_general_hr_recommendations(age, resting_hr),
                "calculated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular zonas FC: {e}")
            return {
                "status": "error",
                "message": f"Erro no cálculo: {str(e)}"
            }
    
    async def analyze_current_hr(
        self,
        user_id: str,
        current_hr: int,
        context: str = "exercise"
    ) -> Dict[str, Any]:
        """Analisa FC atual com contexto"""
        
        try:
            # Busca perfil do usuário
            user = await user_repo.get_user_by_id(user_id)
            if not user:
                return {
                    "status": "error",
                    "message": f"Usuário {user_id} não encontrado"
                }
            
            # Calcula zonas
            resting_hr = user.resting_heart_rate or self._estimate_resting_hr(user.age, user.fitness_level.value)
            zones_data = calculate_heart_rate_zones(user.age, resting_hr)
            current_zone = determine_heart_rate_zone(current_hr, zones_data["zones"])
            
            # Verifica segurança
            safety_check = check_heart_rate_safety(
                current_hr, 
                user.age, 
                user.fitness_level.value,
                user.health_conditions
            )
            
            # Análise contextual
            context_analysis = self._analyze_context(current_hr, context, zones_data, user)
            
            # Recomendações dinâmicas
            recommendations = self._get_dynamic_recommendations(
                current_hr, current_zone, context, user, safety_check
            )
            
            return {
                "status": "success",
                "user_id": user_id,
                "current_hr": current_hr,
                "context": context,
                "current_zone": current_zone,
                "safety_status": "safe" if safety_check["safe"] else "warning",
                "safety_alerts": safety_check.get("alerts", []),
                "context_analysis": context_analysis,
                "recommendations": recommendations,
                "next_check_in": self._suggest_next_check(context, current_zone),
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao analisar FC para {user_id}: {e}")
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }
    
    def _get_zone_duration(self, zone_id: str) -> str:
        """Retorna duração recomendada por zona"""
        durations = {
            "zona_1": "20-60 minutos",
            "zona_2": "20-90 minutos", 
            "zona_3": "20-40 minutos",
            "zona_4": "8-40 minutos",
            "zona_5": "30 segundos - 8 minutos"
        }
        return durations.get(zone_id, "10-30 minutos")
    
    def _get_zone_activities(self, zone_id: str) -> list:
        """Retorna atividades típicas por zona"""
        activities = {
            "zona_1": ["Caminhada leve", "Yoga suave", "Alongamento ativo"],
            "zona_2": ["Caminhada rápida", "Ciclismo leve", "Natação tranquila"],
            "zona_3": ["Corrida leve", "Ciclismo moderado", "Aeróbica"],
            "zona_4": ["Corrida intensa", "Ciclismo forte", "Treino intervalado"],
            "zona_5": ["Sprints", "HIIT", "Treino de potência"]
        }
        return activities.get(zone_id, ["Atividade moderada"])
    
    def _get_zone_focus(self, zone_id: str) -> str:
        """Retorna foco de treinamento por zona"""
        focus = {
            "zona_1": "Recuperação ativa e mobilização de gordura",
            "zona_2": "Base aeróbica e resistência fundamental",
            "zona_3": "Eficiência cardiovascular e resistência",
            "zona_4": "Limiar anaeróbico e capacidade lactária",
            "zona_5": "Potência máxima e sistema neuromuscular"
        }
        return focus.get(zone_id, "Condicionamento geral")
    
    def _get_general_hr_recommendations(self, age: int, resting_hr: int) -> list:
        """Gera recomendações gerais baseadas em FC"""
        recommendations = []
        
        # Análise FC repouso
        if resting_hr < 60:
            recommendations.append("Excelente FC de repouso - indica bom condicionamento")
        elif resting_hr > 80:
            recommendations.append("FC de repouso elevada - considere exercícios aeróbicos regulares")
        
        # Análise por idade
        if age > 50:
            recommendations.extend([
                "Priorize zonas 1-2 para segurança cardiovascular",
                "Inclua exercícios de flexibilidade e equilíbrio"
            ])
        elif age < 30:
            recommendations.append("Pode explorar todas as zonas com segurança")
        
        recommendations.extend([
            "Monitore FC durante exercícios intensos",
            "Use as zonas como guia, não regra absoluta",
            "Escute sempre seu corpo acima dos números"
        ])
        
        return recommendations
    
    def _estimate_resting_hr(self, age: int, fitness_level: str) -> int:
        """Estima FC de repouso baseada no perfil"""
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
    
    def _analyze_context(self, current_hr: int, context: str, zones_data: dict, user) -> dict:
        """Analisa FC no contexto da atividade"""
        max_hr = zones_data["max_hr"]
        hr_percentage = (current_hr / max_hr) * 100
        
        context_analysis = {
            "hr_percentage_of_max": round(hr_percentage, 1),
            "context": context,
            "interpretation": ""
        }
        
        if context == "rest":
            if current_hr > user.resting_heart_rate + 20:
                context_analysis["interpretation"] = "FC elevada para repouso - pode indicar stress ou fadiga"
            else:
                context_analysis["interpretation"] = "FC normal para repouso"
                
        elif context == "exercise":
            if hr_percentage < 60:
                context_analysis["interpretation"] = "Intensidade baixa - pode aumentar se confortável"
            elif hr_percentage < 80:
                context_analysis["interpretation"] = "Intensidade moderada - zona de treino efetiva"
            elif hr_percentage < 90:
                context_analysis["interpretation"] = "Intensidade alta - monitorar de perto"
            else:
                context_analysis["interpretation"] = "Intensidade muito alta - reduzir se necessário"
                
        elif context == "recovery":
            if hr_percentage > 70:
                context_analysis["interpretation"] = "FC ainda elevada - continue recuperação ativa"
            else:
                context_analysis["interpretation"] = "FC adequada para recuperação"
        
        return context_analysis
    
    def _get_dynamic_recommendations(
        self, 
        current_hr: int, 
        current_zone: dict, 
        context: str, 
        user, 
        safety_check: dict
    ) -> list:
        """Gera recomendações dinâmicas baseadas na situação atual"""
        
        recommendations = []
        
        # Recomendações de segurança primeiro
        if safety_check.get("alerts"):
            recommendations.extend(safety_check["alerts"])
        
        # Recomendações contextuais
        if context == "exercise":
            zone_id = current_zone.get("zone_id", "unknown")
            
            if zone_id == "zona_1":
                recommendations.append("Pode aumentar a intensidade gradualmente")
            elif zone_id == "zona_2":
                recommendations.append("Ótima zona para queima de gordura e base aeróbica")
            elif zone_id == "zona_3":
                recommendations.append("Zona ideal para melhoria cardiovascular")
            elif zone_id == "zona_4":
                recommendations.append("Intensidade alta - monitore duração")
            elif zone_id == "zona_5":
                recommendations.append("Intensidade máxima - sessões curtas apenas")
        
        # Recomendações baseadas no perfil
        if user.fitness_level.value == "beginner":
            recommendations.append("Como iniciante, foque em zonas 1-2 principalmente")
        elif user.fitness_level.value == "advanced":
            recommendations.append("Pode explorar todas as zonas com segurança")
        
        # Recomendações por condições de saúde
        for condition in user.health_conditions:
            if condition.value == "heart_disease":
                recommendations.append("Mantenha FC abaixo de 70% da máxima")
            elif condition.value == "hypertension":
                recommendations.append("Evite picos súbitos de FC")
        
        return recommendations
    
    def _suggest_next_check(self, context: str, current_zone: dict) -> str:
        """Sugere quando fazer próxima verificação"""
        
        zone_id = current_zone.get("zone_id", "unknown")
        
        if context == "exercise":
            if zone_id in ["zona_4", "zona_5"]:
                return "Verifique em 2-3 minutos"
            elif zone_id == "zona_3":
                return "Verifique em 5-10 minutos"
            else:
                return "Verifique em 10-15 minutos"
        elif context == "recovery":
            return "Verifique em 2-5 minutos"
        else:
            return "Verifique conforme necessário"