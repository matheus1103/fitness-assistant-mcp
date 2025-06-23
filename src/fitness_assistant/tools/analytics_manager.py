
# src/fitness_assistant/tools/analytics_manager.py (para PostgreSQL)
"""
Gerenciador de analytics com PostgreSQL
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from ..database.repositories import session_repo, user_repo
from ..utils.calculations import estimate_calories, calculate_workout_intensity

logger = logging.getLogger(__name__)

class AnalyticsManager:
    """Gerencia analytics e relatórios com PostgreSQL"""
    
    async def log_session(
        self,
        user_id: str,
        exercises: List[Dict[str, Any]],
        duration_minutes: int,
        avg_heart_rate: int,
        max_heart_rate: Optional[int] = None,
        perceived_exertion: int = 5,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Registra sessão de treino no PostgreSQL"""
        
        try:
            # Verifica se usuário existe
            user = await user_repo.get_user_by_id(user_id)
            if not user:
                return {
                    "status": "error",
                    "message": f"Usuário {user_id} não encontrado"
                }
            
            # Estima calorias baseado no perfil
            calories = estimate_calories(
                weight=user.weight,
                duration_minutes=duration_minutes,
                avg_heart_rate=avg_heart_rate,
                age=user.age
            )
            
            # Determina tipo da sessão baseado nos exercícios
            session_type = self._determine_session_type(exercises)
            
            # Dados da sessão
            session_data = {
                "user_profile_id": user.id,
                "duration_minutes": duration_minutes,
                "avg_heart_rate": avg_heart_rate,
                "max_heart_rate": max_heart_rate or avg_heart_rate,
                "perceived_exertion": perceived_exertion,
                "calories_estimated": calories,
                "notes": notes,
                "session_type": session_type,
                "session_date": datetime.utcnow()
            }
            
            # Cria sessão no banco
            session = await session_repo.create_session(session_data)
            
            logger.info(f"Sessão registrada para usuário {user_id}: {duration_minutes}min, {calories}cal")
            
            return {
                "status": "success",
                "message": "Sessão registrada com sucesso",
                "session": {
                    "id": str(session.id),
                    "user_id": user_id,
                    "date": session.session_date.isoformat(),
                    "duration_minutes": session.duration_minutes,
                    "avg_heart_rate": session.avg_heart_rate,
                    "max_heart_rate": session.max_heart_rate,
                    "perceived_exertion": session.perceived_exertion,
                    "calories_estimated": session.calories_estimated,
                    "session_type": session.session_type,
                    "exercises_count": len(exercises)
                },
                "insights": self._generate_session_insights(session, user)
            }
            
        except Exception as e:
            logger.error(f"Erro ao registrar sessão para {user_id}: {e}")
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }
    
    async def get_analytics(
        self,
        user_id: str,
        period_days: int = 30,
        analysis_type: str = "summary"
    ) -> Dict[str, Any]:
        """Obtém analytics detalhados do usuário"""
        
        try:
            # Verifica se usuário existe
            user = await user_repo.get_user_by_id(user_id)
            if not user:
                return {
                    "status": "error",
                    "message": f"Usuário {user_id} não encontrado"
                }
            
            # Busca dados do período
            analytics_data = await session_repo.get_session_analytics(user_id, period_days)
            sessions = await session_repo.get_user_sessions(user_id, limit=100, days_back=period_days)
            
            # Calcula métricas adicionais
            if sessions:
                weekly_frequency = self._calculate_weekly_frequency(sessions, period_days)
                progress_trend = self._calculate_progress_trend(sessions)
                favorite_activities = self._analyze_favorite_activities(sessions)
                performance_zones = self._analyze_performance_zones(sessions, user)
            else:
                weekly_frequency = 0
                progress_trend = "insufficient_data"
                favorite_activities = []
                performance_zones = {}
            
            result = {
                "status": "success",
                "user_id": user_id,
                "period_days": period_days,
                "analysis_type": analysis_type,
                "summary": {
                    "total_sessions": analytics_data["total_sessions"],
                    "total_duration_minutes": analytics_data["total_duration"],
                    "avg_duration_per_session": analytics_data["avg_duration"],
                    "avg_heart_rate": analytics_data["avg_heart_rate"],
                    "total_calories": analytics_data["total_calories"],
                    "weekly_frequency": weekly_frequency,
                    "progress_trend": progress_trend
                },
                "detailed_insights": {
                    "favorite_activities": favorite_activities,
                    "performance_zones": performance_zones,
                    "consistency_score": self._calculate_consistency_score(sessions, period_days),
                    "improvement_areas": self._identify_improvement_areas(sessions, user)
                }
            }
            
            # Adiciona análises específicas por tipo
            if analysis_type == "progress":
                result["progress_analysis"] = await self._generate_progress_analysis(user_id, sessions)
            elif analysis_type == "trends":
                result["trend_analysis"] = self._generate_trend_analysis(sessions)
            elif analysis_type == "recommendations":
                result["recommendations"] = await self._generate_personalized_recommendations(user, sessions)
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao gerar analytics para {user_id}: {e}")
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }
    
    async def generate_report(
        self,
        user_id: str,
        report_type: str = "monthly",
        include_comparisons: bool = True,
        include_goals: bool = True
    ) -> Dict[str, Any]:
        """Gera relatório detalhado de progresso"""
        
        try:
            # Define período baseado no tipo de relatório
            period_mapping = {
                "weekly": 7,
                "monthly": 30,
                "quarterly": 90
            }
            
            days_back = period_mapping.get(report_type, 30)
            
            # Busca dados
            user = await user_repo.get_user_by_id(user_id)
            if not user:
                return {
                    "status": "error",
                    "message": f"Usuário {user_id} não encontrado"
                }
            
            current_sessions = await session_repo.get_user_sessions(user_id, days_back=days_back)
            
            # Dados de comparação se solicitado
            comparison_data = None
            if include_comparisons and len(current_sessions) > 0:
                previous_sessions = await session_repo.get_user_sessions(
                    user_id, 
                    days_back=days_back * 2
                )
                # Filtra sessões do período anterior
                cutoff_date = datetime.utcnow() - timedelta(days=days_back)
                previous_sessions = [
                    s for s in previous_sessions 
                    if s.session_date < cutoff_date
                ][:len(current_sessions)]
                
                if previous_sessions:
                    comparison_data = self._generate_comparison_analysis(current_sessions, previous_sessions)
            
            # Gera relatório
            report = {
                "status": "success",
                "report_type": report_type,
                "user_id": user_id,
                "generated_at": datetime.utcnow().isoformat(),
                "period": {
                    "days": days_back,
                    "start_date": (datetime.utcnow() - timedelta(days=days_back)).isoformat(),
                    "end_date": datetime.utcnow().isoformat()
                },
                "executive_summary": self._generate_executive_summary(current_sessions, user),
                "detailed_metrics": await self._generate_detailed_metrics(user_id, current_sessions),
                "achievements": self._identify_achievements(current_sessions, user),
                "recommendations": await self._generate_actionable_recommendations(user, current_sessions)
            }
            
            if comparison_data:
                report["comparison_analysis"] = comparison_data
            
            if include_goals:
                report["goal_progress"] = await self._analyze_goal_progress(user_id, current_sessions)
            
            return report
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório para {user_id}: {e}")
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }
    
    def _determine_session_type(self, exercises: List[Dict[str, Any]]) -> str:
        """Determina tipo da sessão baseado nos exercícios"""
        if not exercises:
            return "unknown"
        
        cardio_count = sum(1 for ex in exercises if ex.get("type", "").lower() == "cardio")
        strength_count = sum(1 for ex in exercises if ex.get("type", "").lower() == "strength")
        flexibility_count = sum(1 for ex in exercises if ex.get("type", "").lower() == "flexibility")
        
        total_exercises = len(exercises)
        
        if cardio_count / total_exercises > 0.7:
            return "cardio"
        elif strength_count / total_exercises > 0.7:
            return "strength"
        elif flexibility_count / total_exercises > 0.7:
            return "flexibility"
        else:
            return "mixed"
    
    def _generate_session_insights(self, session, user) -> List[str]:
        """Gera insights sobre a sessão"""
        insights = []
        
        # Análise de intensidade
        intensity = calculate_workout_intensity(session.avg_heart_rate, user.age)
        insights.append(f"Intensidade do treino: {intensity}")
        
        # Análise de duração
        if session.duration_minutes >= 45:
            insights.append("Excelente duração de treino!")
        elif session.duration_minutes >= 30:
            insights.append("Boa duração de treino")
        else:
            insights.append("Considere aumentar a duração gradualmente")
        
        # Análise de esforço percebido
        if session.perceived_exertion >= 8:
            insights.append("Treino de alta intensidade - lembre-se de descansar")
        elif session.perceived_exertion >= 6:
            insights.append("Boa intensidade de treino")
        else:
            insights.append("Pode aumentar a intensidade gradualmente")
        
        return insights
    
    def _calculate_weekly_frequency(self, sessions: List, period_days: int) -> float:
        """Calcula frequência semanal de treinos"""
        if not sessions or period_days == 0:
            return 0.0
        
        weeks = period_days / 7
        return round(len(sessions) / weeks, 1)
    
    def _calculate_progress_trend(self, sessions: List) -> str:
        """Calcula tendência de progresso"""
        if len(sessions) < 4:
            return "insufficient_data"
        
        # Analisa últimas 4 vs 4 anteriores
        recent = sessions[:len(sessions)//2]
        older = sessions[len(sessions)//2:]
        
        recent_avg_duration = sum(s.duration_minutes for s in recent) / len(recent)
        older_avg_duration = sum(s.duration_minutes for s in older) / len(older)
        
        if recent_avg_duration > older_avg_duration * 1.1:
            return "improving"
        elif recent_avg_duration < older_avg_duration * 0.9:
            return "declining"
        else:
            return "stable"
    
    def _analyze_favorite_activities(self, sessions: List) -> List[Dict[str, Any]]:
        """Analisa atividades favoritas"""
        activity_count = {}
        
        for session in sessions:
            session_type = session.session_type or "unknown"
            activity_count[session_type] = activity_count.get(session_type, 0) + 1
        
        # Ordena por frequência
        sorted_activities = sorted(activity_count.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {"activity": activity, "sessions": count, "percentage": round(count/len(sessions)*100, 1)}
            for activity, count in sorted_activities[:5]
        ]
    
    def _analyze_performance_zones(self, sessions: List, user) -> Dict[str, Any]:
        """Analisa zonas de performance"""
        if not sessions:
            return {}
        
        max_hr = 220 - user.age
        zone_counts = {"low": 0, "moderate": 0, "high": 0, "very_high": 0}
        
        for session in sessions:
            hr_percentage = (session.avg_heart_rate / max_hr) * 100
            
            if hr_percentage < 60:
                zone_counts["low"] += 1
            elif hr_percentage < 70:
                zone_counts["moderate"] += 1
            elif hr_percentage < 85:
                zone_counts["high"] += 1
            else:
                zone_counts["very_high"] += 1
        
        total = len(sessions)
        return {
            zone: {"count": count, "percentage": round(count/total*100, 1)}
            for zone, count in zone_counts.items()
        }
    
    def _calculate_consistency_score(self, sessions: List, period_days: int) -> float:
        """Calcula score de consistência (0-100)"""
        if not sessions or period_days == 0:
            return 0.0
        
        # Score baseado em frequência e distribuição
        expected_sessions = period_days / 7 * 3  # 3x por semana ideal
        frequency_score = min(len(sessions) / expected_sessions, 1.0) * 60
        
        # Score de distribuição (evita concentração em poucos dias)
        if len(sessions) > 1:
            dates = [s.session_date.date() for s in sessions]
            unique_days = len(set(dates))
            distribution_score = min(unique_days / len(sessions), 1.0) * 40
        else:
            distribution_score = 20 if len(sessions) == 1 else 0
        
        return round(frequency_score + distribution_score, 1)
    
    def _identify_improvement_areas(self, sessions: List, user) -> List[str]:
        """Identifica áreas para melhoria"""
        areas = []
        
        if not sessions:
            return ["Inicie uma rotina regular de exercícios"]
        
        # Analisa duração média
        avg_duration = sum(s.duration_minutes for s in sessions) / len(sessions)
        if avg_duration < 30:
            areas.append("Aumente a duração dos treinos gradualmente")
        
        # Analisa frequência
        if len(sessions) < 8:  # menos de 2x por semana
            areas.append("Aumente a frequência dos treinos")
        
        # Analisa variedade
        session_types = set(s.session_type for s in sessions)
        if len(session_types) < 2:
            areas.append("Inclua mais variedade nos tipos de exercício")
        
        # Analisa intensidade
        avg_exertion = sum(s.perceived_exertion for s in sessions if s.perceived_exertion) / len(sessions)
        if avg_exertion < 5:
            areas.append("Considere aumentar gradualmente a intensidade")
        
        return areas[:3]  # Máximo 3 áreas
    
    async def _generate_progress_analysis(self, user_id: str, sessions: List) -> Dict[str, Any]:
        """Gera análise detalhada de progresso"""
        # Implementação específica para análise de progresso
        return {
            "trend": self._calculate_progress_trend(sessions),
            "improvements": self._identify_improvements(sessions),
            "milestones": self._identify_milestones(sessions)
        }
    
    def _generate_trend_analysis(self, sessions: List) -> Dict[str, Any]:
        """Gera análise de tendências"""
        # Implementação para análise de tendências
        return {
            "duration_trend": "increasing",
            "intensity_trend": "stable",
            "frequency_trend": "improving"
        }
    
    async def _generate_personalized_recommendations(self, user, sessions: List) -> List[str]:
        """Gera recomendações personalizadas"""
        recommendations = []
        
        # Baseado no nível fitness
        if user.fitness_level == "beginner":
            recommendations.append("Foque na consistência antes da intensidade")
        elif user.fitness_level == "advanced":
            recommendations.append("Considere periodização nos treinos")
        
        # Baseado na frequência
        weekly_freq = self._calculate_weekly_frequency(sessions, 30)
        if weekly_freq < 2:
            recommendations.append("Tente treinar pelo menos 2-3 vezes por semana")
        elif weekly_freq > 6:
            recommendations.append("Inclua dias de descanso para recuperação")
        
        return recommendations
    
    def _generate_executive_summary(self, sessions: List, user) -> Dict[str, Any]:
        """Gera resumo executivo"""
        if not sessions:
            return {
                "status": "inactive",
                "message": "Nenhuma atividade registrada no período"
            }
        
        total_duration = sum(s.duration_minutes for s in sessions)
        avg_duration = total_duration / len(sessions)
        
        return {
            "status": "active",
            "total_sessions": len(sessions),
            "total_hours": round(total_duration / 60, 1),
            "avg_session_duration": round(avg_duration, 1),
            "consistency_rating": "excellent" if len(sessions) >= 12 else "good" if len(sessions) >= 8 else "needs_improvement"
        }
    
    async def _generate_detailed_metrics(self, user_id: str, sessions: List) -> Dict[str, Any]:
        """Gera métricas detalhadas"""
        analytics = await session_repo.get_session_analytics(user_id, 30)
        
        return {
            "performance": analytics,
            "distribution": self._analyze_favorite_activities(sessions),
            "intensity": self._analyze_intensity_distribution(sessions)
        }
    
    def _analyze_intensity_distribution(self, sessions: List) -> Dict[str, Any]:
        """Analisa distribuição de intensidade"""
        if not sessions:
            return {}
        
        low_intensity = sum(1 for s in sessions if (s.perceived_exertion or 5) <= 4)
        moderate_intensity = sum(1 for s in sessions if 5 <= (s.perceived_exertion or 5) <= 7)
        high_intensity = sum(1 for s in sessions if (s.perceived_exertion or 5) >= 8)
        
        total = len(sessions)
        
        return {
            "low": {"count": low_intensity, "percentage": round(low_intensity/total*100, 1)},
            "moderate": {"count": moderate_intensity, "percentage": round(moderate_intensity/total*100, 1)},
            "high": {"count": high_intensity, "percentage": round(high_intensity/total*100, 1)}
        }
    
    def _identify_achievements(self, sessions: List, user) -> List[Dict[str, Any]]:
        """Identifica conquistas do usuário"""
        achievements = []
        
        if len(sessions) >= 10:
            achievements.append({
                "title": "Consistência",
                "description": f"Completou {len(sessions)} sessões no período",
                "type": "consistency"
            })
        
        total_duration = sum(s.duration_minutes for s in sessions)
        if total_duration >= 600:  # 10 horas
            achievements.append({
                "title": "Dedicação",
                "description": f"Treinou por {total_duration//60}h {total_duration%60}min",
                "type": "duration"
            })
        
        return achievements
    
    async def _generate_actionable_recommendations(self, user, sessions: List) -> List[Dict[str, str]]:
        """Gera recomendações acionáveis"""
        recommendations = []
        
        # Análise de frequência
        weekly_freq = self._calculate_weekly_frequency(sessions, 30)
        if weekly_freq < 3:
            recommendations.append({
                "category": "Frequência",
                "recommendation": "Aumente para 3-4 treinos por semana",
                "priority": "high"
            })
        
        # Análise de variedade
        session_types = set(s.session_type for s in sessions if s.session_type)
        if len(session_types) < 2:
            recommendations.append({
                "category": "Variedade",
                "recommendation": "Inclua diferentes tipos de exercício",
                "priority": "medium"
            })
        
        return recommendations
    
    def _generate_comparison_analysis(self, current: List, previous: List) -> Dict[str, Any]:
        """Gera análise comparativa entre períodos"""
        current_duration = sum(s.duration_minutes for s in current)
        previous_duration = sum(s.duration_minutes for s in previous)
        
        duration_change = ((current_duration - previous_duration) / max(previous_duration, 1)) * 100
        session_change = ((len(current) - len(previous)) / max(len(previous), 1)) * 100
        
        return {
            "sessions": {
                "current": len(current),
                "previous": len(previous),
                "change_percentage": round(session_change, 1)
            },
            "duration": {
                "current": current_duration,
                "previous": previous_duration,
                "change_percentage": round(duration_change, 1)
            },
            "trend": "improving" if duration_change > 10 else "declining" if duration_change < -10 else "stable"
        }
    
    async def _analyze_goal_progress(self, user_id: str, sessions: List) -> Dict[str, Any]:
        """Analisa progresso em relação às metas"""
        # Implementação futura: integração com tabela de goals
        return {
            "goals_analyzed": 0,
            "message": "Sistema de metas será implementado em breve"
        }
    
    def _identify_improvements(self, sessions: List) -> List[str]:
        """Identifica melhorias detectadas"""
        improvements = []
        
        if len(sessions) >= 4:
            recent_avg = sum(s.duration_minutes for s in sessions[:len(sessions)//2]) / (len(sessions)//2)
            older_avg = sum(s.duration_minutes for s in sessions[len(sessions)//2:]) / (len(sessions) - len(sessions)//2)
            
            if recent_avg > older_avg * 1.1:
                improvements.append("Aumento na duração dos treinos")
        
        return improvements
    
    def _identify_milestones(self, sessions: List) -> List[Dict[str, Any]]:
        """Identifica marcos importantes"""
        milestones = []
        
        if len(sessions) >= 10:
            milestones.append({
                "milestone": "10 treinos completados",
                "achieved_at": sessions[9].session_date.isoformat() if len(sessions) > 9 else None
            })
        
        return milestones