
# src/fitness_assistant/tools/heart_rate_manager.py (completando)
"""
Gerenciador de frequência cardíaca - versão completa
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from ..database.repositories import user_repo
from ..utils.calculations import calculate_heart_rate_zones, determine_heart_rate_zone
from ..utils.safety import check_heart_rate_safety

logger = logging.getLogger(__name__)

class HeartRateManager:
    """Gerencia análises de frequência cardíaca"""
    
    async def calculate_zones(self, age: int, resting_hr: int) -> Dict[str, Any]:
        """Calcula zonas de FC detalhadas"""
        
        try:
            zones_data = calculate_heart_rate_zones(age, resting_hr, method="karvonen")
            
            # Adiciona informações extras
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
            resting_hr = user.resting_heart_rate or self._estimate_resting_hr(user.age, user.fitness_level)
            zones_data = calculate_heart_rate_zones(user.age, resting_hr)
            current_zone = determine_heart_rate_zone(current_hr, zones_data["zones"])
            
            # Verifica segurança
            safety_check = check_heart_rate_safety(current_hr, user.age, user.fitness_level)
            
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
    
    async def get_heart_rate_trends(
        self,
        user_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Analisa tendências de FC ao longo do tempo"""
        
        try:
            # Busca dados históricos (implementação futura com banco)
            # Por agora, retorna análise simulada
            
            trends = {
                "status": "success",
                "user_id": user_id,
                "period_days": period_days,
                "trends": {
                    "resting_hr_trend": "stable",  # improving, stable, declining
                    "max_hr_trend": "stable",
                    "recovery_trend": "improving",
                    "zone_distribution": {
                        "zona_1": 20,  # % tempo em cada zona
                        "zona_2": 40,
                        "zona_3": 25,
                        "zona_4": 10,
                        "zona_5": 5
                    }
                },
                "insights": [
                    "FC de repouso mantida estável",
                    "Boa distribuição entre zonas aeróbicas",
                    "Recuperação pós-exercício melhorando"
                ],
                "recommendations": [
                    "Continue o bom trabalho nas zonas 2-3",
                    "Considere incluir mais treinos na zona 1 para recuperação"
                ]
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Erro ao analisar tendências FC para {user_id}: {e}")
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
    
    def _get_zone_activities(self, zone_id: str) -> List[str]:
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
    
    def _get_general_hr_recommendations(self, age: int, resting_hr: int) -> List[str]:
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
    
    def _analyze_context(self, current_hr: int, context: str, zones_data: Dict, user) -> Dict[str, Any]:
        """Analisa FC no contexto atual"""
        
        max_hr = zones_data["max_hr"]
        percentage = (current_hr / max_hr) * 100
        
        analysis = {
            "hr_percentage_of_max": round(percentage, 1),
            "context_appropriate": True,
            "context_feedback": ""
        }
        
        if context == "rest":
            if current_hr > 100:
                analysis["context_appropriate"] = False
                analysis["context_feedback"] = "FC elevada para repouso - considere relaxar"
            else:
                analysis["context_feedback"] = "FC adequada para repouso"
                
        elif context == "warmup":
            if percentage < 50:
                analysis["context_feedback"] = "Bom aquecimento gradual"
            elif percentage > 70:
                analysis["context_feedback"] = "Aquecimento muito intenso - reduza ritmo"
            else:
                analysis["context_feedback"] = "Aquecimento adequado"
                
        elif context == "exercise":
            if percentage < 60:
                analysis["context_feedback"] = "Intensidade leve - pode aumentar se desejar"
            elif percentage < 85:
                analysis["context_feedback"] = "Intensidade adequada para exercício"
            else:
                analysis["context_feedback"] = "Alta intensidade - monitore cuidadosamente"
                
        elif context == "recovery":
            if percentage > 70:
                analysis["context_appropriate"] = False
                analysis["context_feedback"] = "FC ainda alta - continue recuperação ativa"
            else:
                analysis["context_feedback"] = "Boa recuperação pós-exercício"
        
        return analysis
    
    def _get_dynamic_recommendations(
        self,
        current_hr: int,
        current_zone: Dict,
        context: str,
        user,
        safety_check: Dict
    ) -> List[str]:
        """Gera recomendações dinâmicas baseadas no estado atual"""
        
        recommendations = []
        
        # Recomendações de segurança prioritárias
        if not safety_check["safe"]:
            recommendations.extend(safety_check.get("alerts", []))
            return recommendations
        
        zone_name = current_zone.get("zone_name", "").lower()
        
        # Recomendações por zona atual
        if "recuperação" in zone_name:
            recommendations.extend([
                "Ótima zona para exercícios prolongados",
                "Ideal para queima de gordura",
                "Mantenha respiração confortável"
            ])
        elif "aeróbica" in zone_name:
            recommendations.extend([
                "Zona excelente para resistência",
                "Mantenha este ritmo por 20-40 minutos",
                "Hidrate-se regularmente"
            ])
        elif "limiar" in zone_name or "potência" in zone_name:
            recommendations.extend([
                "Alta intensidade - monitore cuidadosamente",
                "Limite tempo nesta zona (5-15 min)",
                "Prepare recuperação ativa depois"
            ])
        
        # Recomendações por contexto
        if context == "exercise":
            recommendations.append("Ajuste intensidade conforme seu objetivo")
        elif context == "recovery":
            recommendations.append("Continue movimentação leve até FC normalizar")
        
        # Recomendações personalizadas
        if user.fitness_level == "beginner":
            recommendations.append("Como iniciante, priorize consistência sobre intensidade")
        elif user.fitness_level == "advanced":
            recommendations.append("Pode explorar zonas mais altas com segurança")
        
        return recommendations
    
    def _suggest_next_check(self, context: str, current_zone: Dict) -> str:
        """Sugere quando verificar FC novamente"""
        
        if context == "exercise":
            zone_name = current_zone.get("zone_name", "").lower()
            if "potência" in zone_name or "limiar" in zone_name:
                return "Verifique em 2-3 minutos"
            else:
                return "Verifique em 5-10 minutos"
        elif context == "recovery":
            return "Verifique em 2-3 minutos até normalizar"
        else:
            return "Verifique conforme necessário"