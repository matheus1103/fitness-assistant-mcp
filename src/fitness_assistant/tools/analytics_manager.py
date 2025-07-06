# src/fitness_assistant/tools/analytics_manager.py
"""
Gerenciador de analytics e progresso
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AnalyticsManager:
    """Gerencia analytics e dados de progresso"""
    
    def __init__(self):
        # Simulação de dados em memória
        self._workout_sessions: Dict[str, List[Dict]] = {}
        self._user_metrics: Dict[str, Dict] = {}
    
    async def log_session(
        self,
        user_id: str,
        exercises: List[str],
        duration_minutes: int,
        avg_heart_rate: Optional[int] = None,
        max_heart_rate: Optional[int] = None,
        perceived_exertion: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Registra uma sessão de treino"""
        
        try:
            session_data = {
                "session_id": f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "user_id": user_id,
                "date": datetime.now().isoformat(),
                "exercises": exercises,
                "duration_minutes": duration_minutes,
                "avg_heart_rate": avg_heart_rate,
                "max_heart_rate": max_heart_rate,
                "perceived_exertion": perceived_exertion,
                "notes": notes,
                "calories_estimated": self._estimate_calories(exercises, duration_minutes, avg_heart_rate)
            }
            
            # Adiciona à lista de sessões do usuário
            if user_id not in self._workout_sessions:
                self._workout_sessions[user_id] = []
            
            self._workout_sessions[user_id].append(session_data)
            
            # Atualiza métricas do usuário
            await self._update_user_metrics(user_id)
            
            logger.info(f"Sessão registrada para usuário {user_id}")
            
            return {
                "status": "success",
                "message": "Sessão registrada com sucesso",
                "session": session_data,
                "total_sessions": len(self._workout_sessions[user_id])
            }
            
        except Exception as e:
            logger.error(f"Erro ao registrar sessão para {user_id}: {e}")
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }
    
    async def get_user_analytics(
        self,
        user_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Obtém analytics do usuário"""
        
        try:
            if user_id not in self._workout_sessions:
                return {
                    "status": "error",
                    "message": f"Nenhuma sessão encontrada para usuário {user_id}"
                }
            
            sessions = self._workout_sessions[user_id]
            
            # Filtra por período
            cutoff_date = datetime.now() - timedelta(days=period_days)
            recent_sessions = [
                s for s in sessions 
                if datetime.fromisoformat(s['date']) > cutoff_date
            ]
            
            if not recent_sessions:
                return {
                    "status": "warning",
                    "message": f"Nenhuma sessão encontrada nos últimos {period_days} dias",
                    "analytics": self._get_empty_analytics()
                }
            
            # Calcula métricas
            analytics = self._calculate_analytics(recent_sessions, period_days)
            
            return {
                "status": "success",
                "user_id": user_id,
                "period_days": period_days,
                "analytics": analytics
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular analytics para {user_id}: {e}")
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }
    
    async def get_progress_report(
        self,
        user_id: str,
        report_type: str = "monthly"
    ) -> Dict[str, Any]:
        """Gera relatório de progresso"""
        
        try:
            if user_id not in self._workout_sessions:
                return {
                    "status": "error",
                    "message": f"Nenhuma sessão encontrada para usuário {user_id}"
                }
            
            sessions = self._workout_sessions[user_id]
            
            # Define período
            if report_type == "weekly":
                period_days = 7
            elif report_type == "monthly":
                period_days = 30
            elif report_type == "quarterly":
                period_days = 90
            else:
                period_days = 30
            
            # Gera relatório
            report = self._generate_progress_report(sessions, period_days, report_type)
            
            return {
                "status": "success",
                "user_id": user_id,
                "report_type": report_type,
                "generated_at": datetime.now().isoformat(),
                "report": report
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório para {user_id}: {e}")
            return {
                "status": "error",
                "message": f"Erro interno: {str(e)}"
            }
    
    def _estimate_calories(
        self,
        exercises: List[str],
        duration_minutes: int,
        avg_heart_rate: Optional[int] = None
    ) -> int:
        """Estima calorias queimadas"""
        
        # Estimativa básica: 5-8 calorias por minuto dependendo da intensidade
        base_calories_per_minute = 6
        
        # Ajusta baseado na FC se disponível
        if avg_heart_rate:
            if avg_heart_rate > 150:
                base_calories_per_minute = 8
            elif avg_heart_rate > 120:
                base_calories_per_minute = 7
            elif avg_heart_rate < 100:
                base_calories_per_minute = 4
        
        # Ajusta baseado nos tipos de exercício
        exercise_multiplier = 1.0
        exercise_types = [ex.lower() for ex in exercises]
        
        if any("corrida" in ex or "running" in ex for ex in exercise_types):
            exercise_multiplier = 1.3
        elif any("musculação" in ex or "strength" in ex for ex in exercise_types):
            exercise_multiplier = 1.1
        elif any("caminhada" in ex or "walk" in ex for ex in exercise_types):
            exercise_multiplier = 0.8
        
        total_calories = int(base_calories_per_minute * duration_minutes * exercise_multiplier)
        return max(total_calories, duration_minutes * 2)  # Mínimo de 2 cal/min
    
    async def _update_user_metrics(self, user_id: str):
        """Atualiza métricas calculadas do usuário"""
        
        sessions = self._workout_sessions.get(user_id, [])
        if not sessions:
            return
        
        # Calcula métricas básicas
        total_sessions = len(sessions)
        total_minutes = sum(s['duration_minutes'] for s in sessions)
        total_calories = sum(s.get('calories_estimated', 0) for s in sessions)
        
        # Última sessão
        last_session = max(sessions, key=lambda x: x['date'])
        
        # Frequência semanal (últimas 4 semanas)
        four_weeks_ago = datetime.now() - timedelta(weeks=4)
        recent_sessions = [
            s for s in sessions 
            if datetime.fromisoformat(s['date']) > four_weeks_ago
        ]
        weekly_frequency = len(recent_sessions) / 4
        
        self._user_metrics[user_id] = {
            "total_sessions": total_sessions,
            "total_minutes": total_minutes,
            "total_calories": total_calories,
            "last_session_date": last_session['date'],
            "weekly_frequency": round(weekly_frequency, 1),
            "updated_at": datetime.now().isoformat()
        }
    
    def _calculate_analytics(self, sessions: List[Dict], period_days: int) -> Dict[str, Any]:
        """Calcula métricas detalhadas"""
        
        total_sessions = len(sessions)
        total_minutes = sum(s['duration_minutes'] for s in sessions)
        total_calories = sum(s.get('calories_estimated', 0) for s in sessions)
        
        # Médias
        avg_duration = total_minutes / total_sessions if total_sessions > 0 else 0
        avg_calories_per_session = total_calories / total_sessions if total_sessions > 0 else 0
        
        # Frequência
        sessions_per_week = (total_sessions / period_days) * 7
        
        # Tendências de FC
        hr_sessions = [s for s in sessions if s.get('avg_heart_rate')]
        avg_heart_rate = sum(s['avg_heart_rate'] for s in hr_sessions) / len(hr_sessions) if hr_sessions else None
        
        # Exercícios mais frequentes
        exercise_counts = {}
        for session in sessions:
            for exercise in session.get('exercises', []):
                exercise_counts[exercise] = exercise_counts.get(exercise, 0) + 1
        
        favorite_exercises = sorted(exercise_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Consistency score (baseado na regularidade)
        consistency_score = min(sessions_per_week / 3 * 100, 100)  # 3 sessões/semana = 100%
        
        return {
            "summary": {
                "total_sessions": total_sessions,
                "total_minutes": total_minutes,
                "total_calories": total_calories,
                "sessions_per_week": round(sessions_per_week, 1),
                "avg_duration": round(avg_duration, 1),
                "avg_calories_per_session": round(avg_calories_per_session),
                "consistency_score": round(consistency_score, 1)
            },
            "heart_rate": {
                "avg_heart_rate": round(avg_heart_rate) if avg_heart_rate else None,
                "sessions_with_hr": len(hr_sessions),
                "hr_data_coverage": round(len(hr_sessions) / total_sessions * 100, 1) if total_sessions > 0 else 0
            },
            "favorites": {
                "exercises": [{"name": ex, "count": count} for ex, count in favorite_exercises]
            },
            "trends": {
                "activity_level": "High" if sessions_per_week >= 4 else "Moderate" if sessions_per_week >= 2 else "Low",
                "progression": "Improving" if consistency_score > 70 else "Stable" if consistency_score > 40 else "Needs Improvement"
            }
        }
    
    def _generate_progress_report(self, sessions: List[Dict], period_days: int, report_type: str) -> Dict[str, Any]:
        """Gera relatório detalhado de progresso"""
        
        # Filtra sessões do período
        cutoff_date = datetime.now() - timedelta(days=period_days)
        period_sessions = [
            s for s in sessions 
            if datetime.fromisoformat(s['date']) > cutoff_date
        ]
        
        if not period_sessions:
            return {
                "message": f"Nenhuma atividade nos últimos {period_days} dias",
                "recommendations": ["Retome os exercícios gradualmente", "Defina metas pequenas e alcançáveis"]
            }
        
        # Compara com período anterior
        previous_cutoff = cutoff_date - timedelta(days=period_days)
        previous_sessions = [
            s for s in sessions 
            if previous_cutoff < datetime.fromisoformat(s['date']) <= cutoff_date
        ]
        
        current_metrics = self._calculate_analytics(period_sessions, period_days)
        previous_metrics = self._calculate_analytics(previous_sessions, period_days) if previous_sessions else None
        
        # Calcula mudanças
        changes = {}
        if previous_metrics:
            for key in ['total_sessions', 'total_minutes', 'sessions_per_week']:
                current_val = current_metrics['summary'][key]
                previous_val = previous_metrics['summary'][key]
                
                if previous_val > 0:
                    change_pct = ((current_val - previous_val) / previous_val) * 100
                    changes[key] = round(change_pct, 1)
        
        # Gera insights
        insights = self._generate_insights(current_metrics, changes)
        recommendations = self._generate_recommendations(current_metrics, changes)
        
        return {
            "period": {
                "type": report_type,
                "days": period_days,
                "start_date": cutoff_date.strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d")
            },
            "current_metrics": current_metrics,
            "changes_from_previous": changes,
            "insights": insights,
            "recommendations": recommendations,
            "goals_status": self._assess_goals_progress(current_metrics)
        }
    
    def _generate_insights(self, metrics: Dict[str, Any], changes: Dict[str, float]) -> List[str]:
        """Gera insights baseados nas métricas"""
        
        insights = []
        summary = metrics['summary']
        
        # Insights sobre frequência
        if summary['sessions_per_week'] >= 4:
            insights.append("Excelente consistência nos treinos!")
        elif summary['sessions_per_week'] >= 2:
            insights.append("Boa frequência de treinos mantida")
        else:
            insights.append("Frequência de treinos abaixo do ideal")
        
        # Insights sobre mudanças
        if changes.get('sessions_per_week', 0) > 10:
            insights.append("Aumento significativo na frequência de treinos")
        elif changes.get('sessions_per_week', 0) < -10:
            insights.append("Redução na frequência de treinos")
        
        # Insights sobre duração
        if summary['avg_duration'] > 45:
            insights.append("Sessões longas indicam boa dedicação")
        elif summary['avg_duration'] < 20:
            insights.append("Sessões curtas - considere aumentar gradualmente")
        
        return insights
    
    def _generate_recommendations(self, metrics: Dict[str, Any], changes: Dict[str, float]) -> List[str]:
        """Gera recomendações personalizadas"""
        
        recommendations = []
        summary = metrics['summary']
        
        # Recomendações sobre frequência
        if summary['sessions_per_week'] < 2:
            recommendations.append("Tente se exercitar pelo menos 2-3 vezes por semana")
        elif summary['sessions_per_week'] > 6:
            recommendations.append("Considere incluir dias de descanso para recuperação")
        
        # Recomendações sobre variedade
        favorite_count = len(metrics['favorites']['exercises'])
        if favorite_count < 3:
            recommendations.append("Experimente variar mais os tipos de exercício")
        
        # Recomendações sobre FC
        hr_coverage = metrics['heart_rate']['hr_data_coverage']
        if hr_coverage < 50:
            recommendations.append("Monitore sua frequência cardíaca para otimizar treinos")
        
        return recommendations
    
    def _assess_goals_progress(self, metrics: Dict[str, Any]) -> Dict[str, str]:
        """Avalia progresso em relação aos objetivos"""
        
        summary = metrics['summary']
        
        goals_status = {}
        
        # Meta de frequência
        if summary['sessions_per_week'] >= 3:
            goals_status['frequency'] = "Atingido"
        elif summary['sessions_per_week'] >= 2:
            goals_status['frequency'] = "Em progresso"
        else:
            goals_status['frequency'] = "Abaixo do esperado"
        
        # Meta de consistência
        if summary['consistency_score'] >= 80:
            goals_status['consistency'] = "Excelente"
        elif summary['consistency_score'] >= 60:
            goals_status['consistency'] = "Bom"
        else:
            goals_status['consistency'] = "Precisa melhorar"
        
        return goals_status
    
    def _get_empty_analytics(self) -> Dict[str, Any]:
        """Retorna analytics vazios"""
        
        return {
            "summary": {
                "total_sessions": 0,
                "total_minutes": 0,
                "total_calories": 0,
                "sessions_per_week": 0,
                "avg_duration": 0,
                "avg_calories_per_session": 0,
                "consistency_score": 0
            },
            "heart_rate": {
                "avg_heart_rate": None,
                "sessions_with_hr": 0,
                "hr_data_coverage": 0
            },
            "favorites": {
                "exercises": []
            },
            "trends": {
                "activity_level": "None",
                "progression": "No data"
            }
        }