# src/fitness_assistant/tools/simulation_tools.py
"""
Ferramentas MCP para simulação de usuários baseados em datasets
"""

from typing import Dict, List, Any, Optional
import asyncio
import json
from datetime import datetime

from fitness_assistant.data.dataset_importer import GymDatasetImporter, DatasetSimulator
from fitness_assistant.tools.user_listing import get_all_users


class SimulationMCPTools:
    """Ferramentas MCP para simulação e importação de dados"""
    
    @staticmethod
    def get_import_dataset_tool():
        """Ferramenta para importar dataset de academia"""
        from mcp import Tool
        
        return Tool(
            name="import_gym_dataset",
            description="Importa dataset de membros de academia (formato CSV) e cria perfis de usuários",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_source": {
                        "type": "string",
                        "enum": ["kaggle_sample", "generate_sample", "upload_csv"],
                        "description": "Fonte do dataset",
                        "default": "generate_sample"
                    },
                    "num_users": {
                        "type": "integer",
                        "description": "Número de usuários a gerar/importar",
                        "default": 50,
                        "minimum": 10,
                        "maximum": 1000
                    },
                    "include_history": {
                        "type": "boolean",
                        "description": "Gerar histórico de treinos",
                        "default": True
                    },
                    "history_days": {
                        "type": "integer",
                        "description": "Dias de histórico a gerar",
                        "default": 60,
                        "minimum": 7,
                        "maximum": 365
                    }
                }
            }
        )
    
    @staticmethod
    def get_simulate_user_tool():
        """Ferramenta para simular ser um usuário específico"""
        from mcp import Tool
        
        return Tool(
            name="simulate_user_workout",
            description="Simula ser um usuário específico e gera treino personalizado baseado no seu perfil",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "ID do usuário a simular"
                    },
                    "workout_type": {
                        "type": "string",
                        "enum": ["cardio", "strength", "hiit", "flexibility", "auto"],
                        "description": "Tipo de treino (auto = baseado nas preferências)",
                        "default": "auto"
                    },
                    "save_to_database": {
                        "type": "boolean",
                        "description": "Salvar treino no banco de dados",
                        "default": True
                    },
                    "include_progress_analysis": {
                        "type": "boolean",
                        "description": "Incluir análise de progresso",
                        "default": True
                    }
                },
                "required": ["user_id"]
            }
        )
    
    @staticmethod
    def get_analyze_dataset_tool():
        """Ferramenta para analisar dados importados"""
        from mcp import Tool
        
        return Tool(
            name="analyze_imported_dataset",
            description="Analisa estatísticas e distribuições dos dados importados do dataset",
            inputSchema={
                "type": "object",
                "properties": {
                    "analysis_type": {
                        "type": "string",
                        "enum": ["overview", "demographics", "activity_patterns", "progress_trends"],
                        "description": "Tipo de análise a realizar",
                        "default": "overview"
                    },
                    "include_recommendations": {
                        "type": "boolean",
                        "description": "Incluir recomendações baseadas na análise",
                        "default": True
                    }
                }
            }
        )
    
    @staticmethod
    def get_user_progress_tool():
        """Ferramenta para analisar progresso de usuário específico"""
        from mcp import Tool
        
        return Tool(
            name="analyze_user_progress",
            description="Analisa progresso e evolução de um usuário específico ao longo do tempo",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "ID do usuário para análise"
                    },
                    "period_days": {
                        "type": "integer",
                        "description": "Período de análise em dias",
                        "default": 30,
                        "minimum": 7,
                        "maximum": 365
                    },
                    "metrics": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["frequency", "duration", "intensity", "calories", "progress"]
                        },
                        "description": "Métricas a analisar",
                        "default": ["frequency", "progress"]
                    }
                },
                "required": ["user_id"]
            }
        )
    
    @staticmethod
    async def handle_import_dataset_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handler para importação de dataset"""
        
        try:
            dataset_source = arguments.get("dataset_source", "generate_sample")
            num_users = arguments.get("num_users", 50)
            include_history = arguments.get("include_history", True)
            history_days = arguments.get("history_days", 60)
            
            importer = GymDatasetImporter()
            
            if dataset_source == "generate_sample":
                # Gera dados de exemplo
                import pandas as pd
                import random
                
                sample_data = {
                    'Member_ID': [f'gym_member_{i}' for i in range(1, num_users + 1)],
                    'Age': [random.randint(18, 65) for _ in range(num_users)],
                    'Gender': [random.choice(['Male', 'Female']) for _ in range(num_users)],
                    'Weight': [round(random.normalvariate(70, 15), 1) for _ in range(num_users)],
                    'Height': [round(random.normalvariate(170, 10)) for _ in range(num_users)],
                    'Experience_Level': [random.choice(['Beginner', 'Intermediate', 'Advanced']) for _ in range(num_users)],
                    'Workout_Type': [random.choice(['Cardio', 'Strength', 'HIIT', 'Yoga']) for _ in range(num_users)],
                    'Session_Duration': [random.randint(20, 90) for _ in range(num_users)],
                    'Calories_Burned': [random.randint(150, 600) for _ in range(num_users)],
                    'Heart_Rate': [random.randint(110, 170) for _ in range(num_users)]
                }
                
                df = pd.DataFrame(sample_data)
                
            else:
                return {
                    "status": "error",
                    "message": "Fonte de dataset não implementada. Use 'generate_sample'"
                }
            
            # Processa dataset
            analysis = importer.analyze_dataset_structure(df)
            cleaned_df = importer.clean_and_standardize_data(df, analysis)
            profiles = importer.generate_user_profiles(cleaned_df, analysis, max_users=num_users)
            
            # Importa usuários
            import_result = await importer.import_users_to_database(profiles)
            
            result = {
                "status": "success",
                "dataset_info": {
                    "source": dataset_source,
                    "original_records": len(df),
                    "cleaned_records": len(cleaned_df),
                    "profiles_generated": len(profiles)
                },
                "import_results": import_result,
                "users_created": []
            }
            
            # Adiciona IDs dos usuários criados
            if import_result["successful_imports"] > 0:
                result["users_created"] = [profile["user_id"] for profile in profiles[:5]]  # Primeiros 5
                if len(profiles) > 5:
                    result["users_created"].append(f"... e mais {len(profiles) - 5}")
            
            # Gera histórico se solicitado
            if include_history and import_result["successful_imports"] > 0:
                print("Gerando histórico de treinos...")
                historical_workouts = importer.generate_historical_workouts(profiles, days_back=history_days)
                save_result = await importer.save_workouts_to_database(historical_workouts)
                
                result["workout_history"] = {
                    "total_workouts_generated": save_result["total_workouts"],
                    "workouts_saved": save_result["successful_saves"],
                    "success_rate": save_result["success_rate"]
                }
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro na importação: {str(e)}"
            }
    
    @staticmethod
    async def handle_simulate_user_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handler para simulação de usuário"""
        
        try:
            user_id = arguments["user_id"]
            workout_type = arguments.get("workout_type", "auto")
            save_to_db = arguments.get("save_to_database", True)
            include_progress = arguments.get("include_progress_analysis", True)
            
            # Cria simulador
            simulator = DatasetSimulator(user_id)
            
            # Carrega perfil
            profile_loaded = await simulator.load_user_profile()
            if not profile_loaded:
                return {
                    "status": "error",
                    "message": f"Usuário {user_id} não encontrado"
                }
            
            # Obtém contexto do usuário
            context = simulator.get_user_context()
            
            # Define tipo de treino
            if workout_type == "auto":
                preferences = context.get("preferences", ["cardio"])
                import random
                workout_type = random.choice(preferences)
            
            # Simula treino
            session_result = await simulator.simulate_workout_session(workout_type)
            
            result = {
                "status": "success",
                "user_context": {
                    "user_id": user_id,
                    "age": context.get("age"),
                    "fitness_level": context.get("fitness_level"),
                    "experience_context": context.get("experience_context")
                },
                "workout_simulation": {
                    "type": workout_type,
                    "duration_minutes": session_result["workout_generated"]["duration_minutes"],
                    "calories_estimated": session_result["workout_generated"]["calories_estimated"],
                    "target_heart_rate": session_result["workout_generated"]["target_heart_rate"],
                    "exercises_count": len(session_result["workout_generated"]["exercises"]),
                    "adaptations_made": session_result["workout_generated"].get("adaptations_made", [])
                },
                "recommendations": session_result["recommendations"],
                "saved_to_database": session_result["saved_to_database"]
            }
            
            # Análise de progresso se solicitada
            if include_progress:
                progress_analysis = await SimulationMCPTools._analyze_user_progress_internal(user_id, 30)
                result["progress_analysis"] = progress_analysis
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro na simulação: {str(e)}"
            }
    
    @staticmethod
    async def handle_analyze_dataset_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handler para análise de dataset"""
        
        try:
            analysis_type = arguments.get("analysis_type", "overview")
            include_recommendations = arguments.get("include_recommendations", True)
            
            from fitness_assistant.tools.user_listing import get_user_statistics, get_all_users
            
            # Estatísticas básicas
            stats = await get_user_statistics()
            
            if stats["status"] != "success":
                return {
                    "status": "error", 
                    "message": "Erro ao obter estatísticas"
                }
            
            result = {
                "status": "success",
                "analysis_type": analysis_type,
                "generated_at": datetime.now().isoformat()
            }
            
            if analysis_type == "overview":
                db_stats = stats["database_stats"]
                result["overview"] = {
                    "total_users": db_stats["total_users"],
                    "active_users_30d": db_stats["active_users_30d"],
                    "total_sessions": db_stats["total_sessions"],
                    "total_exercises": db_stats["total_exercises"],
                    "activity_rate": round(
                        (db_stats["active_users_30d"] / max(db_stats["total_users"], 1)) * 100, 1
                    )
                }
            
            elif analysis_type == "demographics":
                result["demographics"] = {
                    "fitness_level_distribution": stats.get("fitness_level_distribution", {}),
                    "age_group_distribution": stats.get("age_group_distribution", {}),
                }
                
                # Adiciona percentuais
                total_users = stats["database_stats"]["total_users"]
                if total_users > 0:
                    for distribution in ["fitness_level_distribution", "age_group_distribution"]:
                        if distribution in result["demographics"]:
                            dist_data = result["demographics"][distribution]
                            result["demographics"][f"{distribution}_percentages"] = {
                                k: round((v / total_users) * 100, 1) 
                                for k, v in dist_data.items()
                            }
            
            elif analysis_type == "activity_patterns":
                # Análise de padrões de atividade
                result["activity_patterns"] = {
                    "average_sessions_per_user": round(
                        stats["database_stats"]["total_sessions"] / max(stats["database_stats"]["total_users"], 1), 1
                    ),
                    "active_user_percentage": round(
                        (stats["database_stats"]["active_users_30d"] / max(stats["database_stats"]["total_users"], 1)) * 100, 1
                    )
                }
            
            # Recomendações baseadas na análise
            if include_recommendations:
                result["recommendations"] = SimulationMCPTools._generate_analysis_recommendations(
                    stats, analysis_type
                )
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro na análise: {str(e)}"
            }
    
    @staticmethod
    async def handle_user_progress_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handler para análise de progresso do usuário"""
        
        try:
            user_id = arguments["user_id"]
            period_days = arguments.get("period_days", 30)
            metrics = arguments.get("metrics", ["frequency", "progress"])
            
            return await SimulationMCPTools._analyze_user_progress_internal(user_id, period_days, metrics)
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro na análise de progresso: {str(e)}"
            }
    
    @staticmethod
    async def _analyze_user_progress_internal(user_id: str, period_days: int, 
                                            metrics: List[str] = None) -> Dict[str, Any]:
        """Análise interna de progresso do usuário"""
        
        from fitness_assistant.core.database import get_user_sessions
        from datetime import datetime, timedelta
        
        if metrics is None:
            metrics = ["frequency", "progress"]
        
        # Busca sessões do usuário
        sessions = get_user_sessions(user_id, limit=None)
        
        if not sessions:
            return {
                "status": "error",
                "message": f"Nenhuma sessão encontrada para usuário {user_id}"
            }
        
        # Filtra sessões do período
        cutoff_date = datetime.now() - timedelta(days=period_days)
        recent_sessions = []
        
        for session in sessions:
            try:
                session_date = datetime.fromisoformat(session["date"])
                if session_date >= cutoff_date:
                    recent_sessions.append(session)
            except:
                continue
        
        if not recent_sessions:
            return {
                "status": "error",
                "message": f"Nenhuma sessão encontrada nos últimos {period_days} dias"
            }
        
        result = {
            "status": "success",
            "user_id": user_id,
            "analysis_period_days": period_days,
            "total_sessions_found": len(recent_sessions),
            "metrics_analyzed": metrics
        }
        
        # Análise de frequência
        if "frequency" in metrics:
            weekly_frequency = len(recent_sessions) / (period_days / 7)
            result["frequency_analysis"] = {
                "sessions_in_period": len(recent_sessions),
                "average_weekly_frequency": round(weekly_frequency, 1),
                "consistency_rating": "Excelente" if weekly_frequency >= 4 else 
                                   "Boa" if weekly_frequency >= 3 else
                                   "Regular" if weekly_frequency >= 2 else "Baixa"
            }
        
        # Análise de duração
        if "duration" in metrics:
            durations = [s.get("duration_minutes", 0) for s in recent_sessions]
            if durations:
                result["duration_analysis"] = {
                    "average_duration": round(sum(durations) / len(durations), 1),
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                    "total_training_time": sum(durations)
                }
        
        # Análise de intensidade
        if "intensity" in metrics:
            heart_rates = [s.get("avg_heart_rate") for s in recent_sessions if s.get("avg_heart_rate")]
            perceived_efforts = [s.get("perceived_exertion") for s in recent_sessions if s.get("perceived_exertion")]
            
            intensity_data = {}
            if heart_rates:
                intensity_data["average_heart_rate"] = round(sum(heart_rates) / len(heart_rates), 1)
                intensity_data["heart_rate_trend"] = "Crescente" if len(heart_rates) > 1 and heart_rates[-1] > heart_rates[0] else "Estável"
            
            if perceived_efforts:
                intensity_data["average_perceived_exertion"] = round(sum(perceived_efforts) / len(perceived_efforts), 1)
            
            result["intensity_analysis"] = intensity_data
        
        # Análise de calorias
        if "calories" in metrics:
            calories = [s.get("calories_estimated", 0) for s in recent_sessions]
            if calories:
                result["calorie_analysis"] = {
                    "total_calories_burned": sum(calories),
                    "average_per_session": round(sum(calories) / len(calories), 1),
                    "daily_average": round(sum(calories) / period_days, 1)
                }
        
        # Análise de progresso geral
        if "progress" in metrics:
            # Divide sessões em duas metades para comparar
            mid_point = len(recent_sessions) // 2
            first_half = recent_sessions[:mid_point] if mid_point > 0 else []
            second_half = recent_sessions[mid_point:]
            
            progress_indicators = {}
            
            if first_half and second_half:
                # Compara duração média
                first_duration = sum(s.get("duration_minutes", 0) for s in first_half) / len(first_half)
                second_duration = sum(s.get("duration_minutes", 0) for s in second_half) / len(second_half)
                duration_change = ((second_duration - first_duration) / first_duration) * 100
                
                progress_indicators["duration_improvement"] = round(duration_change, 1)
                
                # Compara calorias
                first_calories = [s.get("calories_estimated", 0) for s in first_half]
                second_calories = [s.get("calories_estimated", 0) for s in second_half]
                
                if first_calories and second_calories:
                    first_cal_avg = sum(first_calories) / len(first_calories)
                    second_cal_avg = sum(second_calories) / len(second_calories)
                    calorie_change = ((second_cal_avg - first_cal_avg) / first_cal_avg) * 100
                    progress_indicators["calorie_improvement"] = round(calorie_change, 1)
            
            result["progress_analysis"] = progress_indicators
        
        # Gera insights e recomendações
        insights = SimulationMCPTools._generate_progress_insights(result, recent_sessions)
        result["insights"] = insights
        
        return result
    
    @staticmethod
    def _generate_analysis_recommendations(stats: Dict[str, Any], analysis_type: str) -> List[str]:
        """Gera recomendações baseadas na análise"""
        
        recommendations = []
        db_stats = stats.get("database_stats", {})
        
        total_users = db_stats.get("total_users", 0)
        active_users = db_stats.get("active_users_30d", 0)
        activity_rate = (active_users / max(total_users, 1)) * 100
        
        if analysis_type == "overview":
            if activity_rate < 30:
                recommendations.append("Taxa de atividade baixa. Considere campanhas de engajamento")
            elif activity_rate > 70:
                recommendations.append("Excelente taxa de atividade! Continue com as estratégias atuais")
            
            if total_users > 100:
                recommendations.append("Base de usuários robusta. Considere análises segmentadas")
        
        elif analysis_type == "demographics":
            fitness_dist = stats.get("fitness_level_distribution", {})
            beginners = fitness_dist.get("beginner", 0)
            total_fitness = sum(fitness_dist.values()) if fitness_dist else 1
            
            if (beginners / total_fitness) > 0.6:
                recommendations.append("Muitos iniciantes. Foque em programas de retenção e progressão")
            
            age_dist = stats.get("age_group_distribution", {})
            if age_dist.get("65_plus", 0) > 0:
                recommendations.append("Usuários 65+ presentes. Considere programas especializados")
        
        return recommendations
    
    @staticmethod
    def _generate_progress_insights(analysis: Dict[str, Any], sessions: List[Dict[str, Any]]) -> List[str]:
        """Gera insights baseados na análise de progresso"""
        
        insights = []
        
        # Insights de frequência
        if "frequency_analysis" in analysis:
            freq = analysis["frequency_analysis"]
            weekly_freq = freq.get("average_weekly_frequency", 0)
            
            if weekly_freq >= 4:
                insights.append("Frequência excelente! Você está mantendo uma rotina consistente")
            elif weekly_freq >= 3:
                insights.append("Boa frequência de treinos. Tente manter ou aumentar ligeiramente")
            else:
                insights.append("Frequência pode melhorar. Tente adicionar mais sessões por semana")
        
        # Insights de duração
        if "duration_analysis" in analysis:
            duration = analysis["duration_analysis"]
            avg_duration = duration.get("average_duration", 0)
            
            if avg_duration >= 60:
                insights.append("Sessões longas mostram boa dedicação")
            elif avg_duration < 30:
                insights.append("Considere aumentar a duração das sessões gradualmente")
        
        # Insights de progresso
        if "progress_analysis" in analysis:
            progress = analysis["progress_analysis"]
            duration_improvement = progress.get("duration_improvement", 0)
            calorie_improvement = progress.get("calorie_improvement", 0)
            
            if duration_improvement > 10:
                insights.append("Excelente progresso na duração dos treinos!")
            elif duration_improvement < -10:
                insights.append("Duração dos treinos diminuiu. Verifique se precisa de mais recuperação")
            
            if calorie_improvement > 15:
                insights.append("Ótimo aumento na queima de calorias!")
        
        # Insights de variedade
        workout_types = set()
        for session in sessions[-10:]:  # Últimas 10 sessões
            workout_type = session.get("workout_type")
            if workout_type:
                workout_types.add(workout_type)
        
        if len(workout_types) == 1:
            insights.append("Considere variar os tipos de treino para melhor desenvolvimento")
        elif len(workout_types) >= 3:
            insights.append("Boa variedade nos tipos de treino!")
        
        return insights


# Integração com o servidor MCP
def add_simulation_tools_to_server():
    """Adiciona as ferramentas de simulação ao servidor MCP"""
    
    tools_to_add = [
        SimulationMCPTools.get_import_dataset_tool(),
        SimulationMCPTools.get_simulate_user_tool(), 
        SimulationMCPTools.get_analyze_dataset_tool(),
        SimulationMCPTools.get_user_progress_tool()
    ]
    
    handlers = {
        "import_gym_dataset": SimulationMCPTools.handle_import_dataset_tool,
        "simulate_user_workout": SimulationMCPTools.handle_simulate_user_tool,
        "analyze_imported_dataset": SimulationMCPTools.handle_analyze_dataset_tool,
        "analyze_user_progress": SimulationMCPTools.handle_user_progress_tool
    }
    
    return tools_to_add, handlers


# Exemplo de uso das ferramentas
async def example_simulation_workflow():
    """Exemplo completo do fluxo de simulação"""
    
    print("EXEMPLO DE FLUXO DE SIMULAÇÃO")
    print("=" * 40)
    
    # 1. Importa dataset
    print("\n1. Importando dataset...")
    import_args = {
        "dataset_source": "generate_sample",
        "num_users": 20,
        "include_history": True,
        "history_days": 30
    }
    
    import_result = await SimulationMCPTools.handle_import_dataset_tool(import_args)
    print(f"Resultado: {import_result['status']}")
    
    if import_result["status"] == "success":
        users_created = import_result["users_created"]
        print(f"Usuários criados: {users_created[:3]}...")
        
        # 2. Simula treino para um usuário
        if users_created:
            sample_user = users_created[0] if isinstance(users_created[0], str) else "gym_member_1"
            
            print(f"\n2. Simulando treino para {sample_user}...")
            sim_args = {
                "user_id": sample_user,
                "workout_type": "auto",
                "save_to_database": True,
                "include_progress_analysis": True
            }
            
            sim_result = await SimulationMCPTools.handle_simulate_user_tool(sim_args)
            print(f"Resultado: {sim_result['status']}")
            
            if sim_result["status"] == "success":
                workout = sim_result["workout_simulation"]
                print(f"Treino: {workout['type']}, {workout['duration_minutes']}min")
                
                # 3. Analisa progresso
                print(f"\n3. Analisando progresso de {sample_user}...")
                progress_args = {
                    "user_id": sample_user,
                    "period_days": 30,
                    "metrics": ["frequency", "duration", "progress"]
                }
                
                progress_result = await SimulationMCPTools.handle_user_progress_tool(progress_args)
                print(f"Resultado: {progress_result['status']}")
                
                if progress_result["status"] == "success":
                    insights = progress_result.get("insights", [])
                    print(f"Insights: {insights[:2] if insights else 'Nenhum insight disponível'}")
    
    # 4. Análise geral do dataset
    print("\n4. Analisando dataset completo...")
    analysis_args = {
        "analysis_type": "overview",
        "include_recommendations": True
    }
    
    analysis_result = await SimulationMCPTools.handle_analyze_dataset_tool(analysis_args)
    print(f"Resultado: {analysis_result['status']}")
    
    if analysis_result["status"] == "success":
        overview = analysis_result.get("overview", {})
        print(f"Total de usuários: {overview.get('total_users', 0)}")
        print(f"Taxa de atividade: {overview.get('activity_rate', 0)}%")


if __name__ == "__main__":
    # Para testar as ferramentas
    asyncio.run(example_simulation_workflow())