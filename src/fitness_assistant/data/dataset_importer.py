# src/fitness_assistant/data/dataset_importer.py
"""
Sistema para importar e processar datasets de academia do Kaggle
Foco no "Gym Members Exercise Dataset" e datasets similares
"""

import pandas as pd
import numpy as np
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import random
import json
import os
from pathlib import Path

# Importações do projeto
from fitness_assistant.models.user import UserProfile, FitnessLevel
from fitness_assistant.database.repositories.user_repo import user_repo
from fitness_assistant.core.database import save_workout_session
from fitness_assistant.tools.profile_manager import ProfileManager


class GymDatasetImporter:
    """Importador para datasets de academia do Kaggle"""
    
    def __init__(self, dataset_path: str = None):
        self.dataset_path = dataset_path
        self.profile_manager = ProfileManager()
        
        # Mapeamentos para padronizar dados
        self.fitness_level_mapping = {
            'Beginner': 'beginner',
            'Intermediate': 'intermediate', 
            'Advanced': 'advanced',
            'Expert': 'advanced',
            1: 'beginner',
            2: 'intermediate',
            3: 'advanced',
            4: 'advanced',
            '1': 'beginner',
            '2': 'intermediate',
            '3': 'advanced',
            '4': 'advanced'
        }
        
        self.workout_type_mapping = {
            'Cardio': 'cardio',
            'Strength': 'strength',
            'HIIT': 'hiit',
            'Yoga': 'flexibility',
            'Flexibility': 'flexibility',
            'CrossTraining': 'strength'
        }
        
        self.gender_mapping = {
            'Male': 'M',
            'Female': 'F',
            'M': 'M',
            'F': 'F',
            1: 'M',
            0: 'F'
        }
    def _get_fitness_level(self, row, fields):
        if "fitness_level" in fields and pd.notna(row[fields["fitness_level"]]):
            value = row[fields["fitness_level"]]
            
            # Se for número
            try:
                num_value = int(value)
                if num_value == 1:
                    return "beginner"
                elif num_value == 2:
                    return "intermediate" 
                else:
                    return "advanced"
            except:
                # Se for string, usa mapeamento
                return self.fitness_level_mapping.get(value, 'beginner')
        
        return "beginner"
        if "fitness_level" in fields and pd.notna(row[fields["fitness_level"]]):
            value = row[fields["fitness_level"]]
            if value == 1:
                return "beginner"
            elif value == 2:
                return "intermediate" 
            elif value >= 3:
                return "advanced"
            else:
                return self.fitness_level_mapping.get(value, 'beginner')
        return "beginner"
    def load_dataset(self, file_path: str) -> pd.DataFrame:
        """Carrega dataset do arquivo CSV"""
        try:
            # Tenta diferentes encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    print(f"Dataset carregado com {len(df)} registros (encoding: {encoding})")
                    return df
                except UnicodeDecodeError:
                    continue
            
            raise ValueError("Não foi possível carregar o arquivo com nenhum encoding")
            
        except Exception as e:
            print(f"Erro ao carregar dataset: {e}")
            return pd.DataFrame()
    
    def analyze_dataset_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analisa a estrutura do dataset e identifica colunas relevantes"""
        
        analysis = {
            "total_records": len(df),
            "columns": list(df.columns),
            "column_types": df.dtypes.to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "sample_data": df.head().to_dict('records'),
            "identified_fields": {}
        }
        
        # Identifica colunas relevantes por nome/padrão
        column_patterns = {
            "user_id": ["id", "user_id", "member_id", "customer_id"],
            "age": ["age", "Age"],
            "gender": ["gender", "Gender", "sex", "Sex"],
            "weight": ["weight", "Weight", "Weight (kg)", "body_weight", "kg"],
            "height": ["height", "Height", "Height (m)", "cm"],
            "fitness_level": ["fitness_level", "experience", "level", "Experience_Level"],
            "workout_type": ["workout_type", "exercise_type", "activity", "Workout_Type"],
            "workout_frequency": ["frequency", "sessions_per_week", "weekly_sessions", "Workout_Frequency (days/week)"],
            "duration": ["duration", "session_duration", "workout_duration", "Session_Duration (hours)"],
            "calories": ["calories", "calories_burned", "cal_burn", "Calories_Burned"],
            "heart_rate": ["heart_rate", "avg_heart_rate", "hr", "bpm", "Avg_BPM"],
            "max_heart_rate": ["max_heart_rate", "max_bpm", "Max_BPM"],
            "resting_heart_rate": ["resting_heart_rate", "resting_bpm", "Resting_BPM"],
            "body_fat": ["body_fat", "fat_percentage", "bf_percent", "Fat_Percentage"],
            "bmi": ["bmi", "BMI", "body_mass_index"],
            "water_intake": ["water_intake", "Water_Intake (liters)", "hydration"],
            "experience_years": ["experience", "years_training", "training_years", "Experience_Level"]
        }
        
        for field, patterns in column_patterns.items():
            for col in df.columns:
                if any(pattern.lower() in col.lower() for pattern in patterns):
                    analysis["identified_fields"][field] = col
                    break
        
        print(f"Campos identificados: {analysis['identified_fields']}")
        return analysis
    
    def clean_and_standardize_data(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> pd.DataFrame:
        """Limpa e padroniza os dados do dataset"""
        
        cleaned_df = df.copy()
        fields = analysis["identified_fields"]
        
        # Remove registros com dados essenciais faltando
        essential_fields = ["age", "gender"]
        for field in essential_fields:
            if field in fields:
                col = fields[field]
                cleaned_df = cleaned_df.dropna(subset=[col])
        
        # Padroniza valores categóricos
        if "fitness_level" in fields:
            col = fields["fitness_level"]
            cleaned_df[col] = cleaned_df[col].map(
                lambda x: self.fitness_level_mapping.get(x, 'beginner')
            )
        
        if "gender" in fields:
            col = fields["gender"]
            cleaned_df[col] = cleaned_df[col].map(
                lambda x: self.gender_mapping.get(x, 'M')
            )
        
        # Converte tipos de dados
        numeric_fields = ["age", "weight", "height", "duration", "calories", "heart_rate"]
        for field in numeric_fields:
            if field in fields:
                col = fields[field]
                cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
        
        # Remove outliers óbvios
        if "age" in fields:
            col = fields["age"]
            cleaned_df = cleaned_df[
                (cleaned_df[col] >= 13) & (cleaned_df[col] <= 100)
            ]
        
        if "weight" in fields:
            col = fields["weight"]
            cleaned_df = cleaned_df[
                (cleaned_df[col] >= 30) & (cleaned_df[col] <= 300)
            ]
        
        if "height" in fields:
            col = fields["height"]
            # Converte altura para metros se estiver em cm
            if cleaned_df[col].mean() > 10:  # Provavelmente em cm
                cleaned_df[col] = cleaned_df[col] / 100
            
            cleaned_df = cleaned_df[
                (cleaned_df[col] >= 1.2) & (cleaned_df[col] <= 2.5)
            ]
        
        print(f"Dataset limpo: {len(cleaned_df)} registros (removidos {len(df) - len(cleaned_df)})")
        return cleaned_df
    
    def generate_user_profiles(self, df: pd.DataFrame, analysis: Dict[str, Any], 
                        max_users: int = 1000) -> List[Dict[str, Any]]:
       """Gera perfis de usuários baseados no dataset"""
       
       fields = analysis["identified_fields"]
       profiles = []
       
       # Limita número de usuários se necessário
       if len(df) > max_users:
           df = df.sample(n=max_users, random_state=42)
       
       for idx, row in df.iterrows():
           try:
               # Dados básicos
               profile = {
                   "user_id": f"gym_member_{idx}",
                   "age": int(row[fields["age"]]) if "age" in fields else random.randint(18, 65),
                   "weight": float(row[fields["weight"]]) if "weight" in fields and pd.notna(row[fields["weight"]]) else self._generate_realistic_weight(),
                   "height": float(row[fields["height"]]) if "height" in fields and pd.notna(row[fields["height"]]) else self._generate_realistic_height(),
"fitness_level": self._get_fitness_level(row, fields)               }
               
               # Corrige gender
               if "gender" in fields and pd.notna(row[fields["gender"]]):
                   gender_value = str(row[fields["gender"]]).strip()
                   if gender_value == "Male":
                       profile["gender"] = "M"
                   elif gender_value == "Female":
                       profile["gender"] = "F"
                   else:
                       profile["gender"] = "M"
               
               # Gera dados adicionais baseados no perfil
               additional_data = self._generate_additional_profile_data(profile, row, fields)
               profile.update(additional_data)
               
               # FILTRA APENAS CAMPOS ACEITOS
               allowed_fields = ["user_id", "age", "weight", "height", "fitness_level", 
                               "gender", "resting_heart_rate", "health_conditions", 
                               "preferences", "goals"]
               
               filtered_profile = {k: v for k, v in profile.items() if k in allowed_fields}
               profiles.append(filtered_profile)
               
           except Exception as e:
               print(f"Erro ao processar registro {idx}: {e}")
               continue
       
       print(f"Gerados {len(profiles)} perfis de usuários")
       return profiles
    
    def _generate_realistic_weight(self) -> float:
        """Gera peso realista baseado em distribuição normal"""
        return round(random.normalvariate(70, 15), 1)
    
    def _generate_realistic_height(self) -> float:
        """Gera altura realista em metros"""
        return round(random.normalvariate(1.70, 0.1), 2)
    
    def _generate_additional_profile_data(self, profile: Dict[str, Any], 
                                        row: pd.Series, fields: Dict[str, str]) -> Dict[str, Any]:
        """Gera dados adicionais para o perfil baseado nos dados disponíveis"""
        
        additional_data = {}
        
        # Frequência cardíaca de repouso baseada na idade e fitness
        age = profile["age"]
        fitness_level = profile["fitness_level"]
        
        base_rhr = 60 if fitness_level == "advanced" else 65 if fitness_level == "intermediate" else 70
        age_factor = (age - 25) * 0.1
        rhr = max(50, min(90, int(base_rhr + age_factor + random.randint(-5, 5))))
        additional_data["resting_heart_rate"] = rhr
        
        # Objetivos baseados no fitness level e dados do dataset
        goals_by_level = {
            "beginner": ["perder peso", "melhorar condicionamento", "criar hábito"],
            "intermediate": ["ganhar massa muscular", "melhorar performance", "tonificar"],
            "advanced": ["competir", "manter forma", "especializar técnica"]
        }
        additional_data["goals"] = random.sample(goals_by_level[fitness_level], 2)
        
        # Preferências de exercício
        workout_preferences = ["cardio", "strength", "hiit", "flexibility"]
        if "workout_type" in fields and pd.notna(row[fields["workout_type"]]):
            pref_type = self.workout_type_mapping.get(row[fields["workout_type"]], "cardio")
            additional_data["preferences"] = [pref_type, random.choice(workout_preferences)]
        else:
            additional_data["preferences"] = random.sample(workout_preferences, 2)
        
        # Condições de saúde baseadas na idade
        health_conditions = []
        if age > 40:
            if random.random() < 0.2:  # 20% chance
                health_conditions.append(random.choice(["hypertension", "diabetes", "arthritis"]))
        if age > 60:
            if random.random() < 0.3:  # 30% chance adicional
                health_conditions.append("osteoporosis")
        
        additional_data["health_conditions"] = health_conditions
        
        return additional_data
    
    async def import_users_to_database(self, profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Importa perfis de usuários para o banco de dados"""
        
        successful_imports = 0
        failed_imports = 0
        errors = []
        
        for profile in profiles:
            try:
                result = await self.profile_manager.create_profile(**profile)
                
                if result["status"] == "success":
                    successful_imports += 1
                else:
                    failed_imports += 1
                    errors.append(f"User {profile['user_id']}: {result['message']}")
                    
            except Exception as e:
                failed_imports += 1
                errors.append(f"User {profile['user_id']}: {str(e)}")
        
        return {
            "status": "completed",
            "successful_imports": successful_imports,
            "failed_imports": failed_imports,
            "total_processed": len(profiles),
            "errors": errors[:10]  # Primeiros 10 erros
        }
    
    def generate_historical_workouts(self, user_profiles: List[Dict[str, Any]], 
                                   days_back: int = 90) -> Dict[str, List[Dict[str, Any]]]:
        """Gera histórico de treinos para os usuários"""
        
        all_workouts = {}
        
        for profile in user_profiles:
            user_id = profile["user_id"]
            fitness_level = profile["fitness_level"]
            preferences = profile.get("preferences", ["cardio", "strength"])
            
            # Frequência de treino baseada no nível
            weekly_frequency = {
                "beginner": 3,
                "intermediate": 4,
                "advanced": 5
            }[fitness_level]
            
            user_workouts = self._generate_user_workout_history(
                user_id, fitness_level, preferences, weekly_frequency, days_back
            )
            
            all_workouts[user_id] = user_workouts
        
        print(f"Gerado histórico para {len(all_workouts)} usuários")
        return all_workouts
    
    def _generate_user_workout_history(self, user_id: str, fitness_level: str, 
                                     preferences: List[str], weekly_freq: int, 
                                     days_back: int) -> List[Dict[str, Any]]:
        """Gera histórico de treinos para um usuário específico"""
        
        workouts = []
        current_date = datetime.now()
        
        # Calcula número total de treinos
        total_weeks = days_back // 7
        total_workouts = total_weeks * weekly_freq
        
        # Distribui treinos ao longo do período
        workout_dates = []
        for week in range(total_weeks):
            week_start = current_date - timedelta(days=(week + 1) * 7)
            
            # Gera dias de treino da semana
            workout_days = random.sample(range(7), min(weekly_freq, 7))
            for day in workout_days:
                workout_date = week_start + timedelta(days=day)
                workout_dates.append(workout_date)
        
        # Gera dados dos treinos
        for workout_date in workout_dates:
            workout = self._generate_single_workout(
                user_id, fitness_level, preferences, workout_date
            )
            workouts.append(workout)
        
        return sorted(workouts, key=lambda x: x["date"])
    
    def _generate_single_workout(self, user_id: str, fitness_level: str, 
                               preferences: List[str], workout_date: datetime) -> Dict[str, Any]:
        """Gera dados de um treino específico"""
        
        # Escolhe tipo de treino baseado nas preferências
        workout_type = random.choice(preferences)
        
        # Parâmetros baseados no nível de fitness
        duration_ranges = {
            "beginner": (20, 45),
            "intermediate": (30, 60),
            "advanced": (45, 90)
        }
        
        hr_ranges = {
            "beginner": (110, 140),
            "intermediate": (120, 160),
            "advanced": (130, 175)
        }
        
        duration = random.randint(*duration_ranges[fitness_level])
        avg_hr = random.randint(*hr_ranges[fitness_level])
        
        # Exercícios baseados no tipo de treino
        exercises = self._generate_workout_exercises(workout_type, fitness_level, duration)
        
        # Calorias estimadas
        calories_per_min = {
            "beginner": 7,
            "intermediate": 8,
            "advanced": 10
        }[fitness_level]
        
        calories = duration * calories_per_min + random.randint(-50, 50)
        
        # Esforço percebido
        perceived_exertion = random.randint(4, 9)
        
        return {
            "date": workout_date.isoformat(),
            "workout_type": workout_type,
            "duration_minutes": duration,
            "exercises": exercises,
            "avg_heart_rate": avg_hr,
            "max_heart_rate": avg_hr + random.randint(10, 25),
            "calories_estimated": calories,
            "perceived_exertion": perceived_exertion,
            "notes": self._generate_workout_notes(perceived_exertion, workout_type)
        }
    
    def _generate_workout_exercises(self, workout_type: str, fitness_level: str, 
                                  duration: int) -> List[Dict[str, Any]]:
        """Gera lista de exercícios para o treino"""
        
        exercise_database = {
            "cardio": [
                {"name": "Esteira", "equipment": "treadmill"},
                {"name": "Bicicleta Ergométrica", "equipment": "bike"},
                {"name": "Elíptico", "equipment": "elliptical"},
                {"name": "Caminhada", "equipment": "none"},
                {"name": "Corrida", "equipment": "none"}
            ],
            "strength": [
                {"name": "Supino", "equipment": "barbell"},
                {"name": "Agachamento", "equipment": "barbell"},
                {"name": "Levantamento Terra", "equipment": "barbell"},
                {"name": "Desenvolvimento", "equipment": "dumbbell"},
                {"name": "Rosca Bíceps", "equipment": "dumbbell"},
                {"name": "Tríceps Pulley", "equipment": "machine"}
            ],
            "hiit": [
                {"name": "Burpees", "equipment": "none"},
                {"name": "Jump Squats", "equipment": "none"},
                {"name": "Mountain Climbers", "equipment": "none"},
                {"name": "Kettlebell Swings", "equipment": "kettlebell"}
            ],
            "flexibility": [
                {"name": "Alongamento Geral", "equipment": "none"},
                {"name": "Yoga Flow", "equipment": "mat"},
                {"name": "Pilates", "equipment": "mat"}
            ]
        }
        
        available_exercises = exercise_database.get(workout_type, exercise_database["cardio"])
        
        # Número de exercícios baseado na duração
        num_exercises = min(len(available_exercises), max(1, duration // 15))
        selected_exercises = random.sample(available_exercises, num_exercises)
        
        exercises = []
        for exercise in selected_exercises:
            exercise_duration = duration // num_exercises + random.randint(-5, 5)
            exercises.append({
                "name": exercise["name"],
                "equipment": exercise["equipment"],
                "duration_minutes": max(5, exercise_duration),
                "sets": random.randint(2, 4) if workout_type == "strength" else None,
                "reps": random.randint(8, 15) if workout_type == "strength" else None
            })
        
        return exercises
    
    def _generate_workout_notes(self, perceived_exertion: int, workout_type: str) -> str:
        """Gera notas do treino baseadas no esforço percebido"""
        
        notes_templates = {
            "low": [
                "Treino tranquilo, me senti bem durante toda a sessão",
                "Boa recuperação ativa, sem muito esforço",
                "Dia de treino leve, focando na técnica"
            ],
            "medium": [
                "Treino moderado, suei um pouco mais hoje", 
                "Boa sessão, me senti desafiado mas controlado",
                "Intensidade adequada, consegui manter o ritmo"
            ],
            "high": [
                "Treino intenso, me esforcei bastante hoje",
                "Sessão puxada, mas consegui completar todos os exercícios",
                "Treino desafiador, vou precisar de uma boa recuperação"
            ]
        }
        
        intensity = "low" if perceived_exertion <= 5 else "medium" if perceived_exertion <= 7 else "high"
        return random.choice(notes_templates[intensity])
    
    async def save_workouts_to_database(self, all_workouts: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Salva histórico de treinos no banco de dados"""
        
        total_workouts = 0
        successful_saves = 0
        failed_saves = 0
        
        for user_id, workouts in all_workouts.items():
            for workout in workouts:
                total_workouts += 1
                try:
                    success = save_workout_session(user_id, workout)
                    if success:
                        successful_saves += 1
                    else:
                        failed_saves += 1
                except Exception as e:
                    failed_saves += 1
                    print(f"Erro ao salvar treino para {user_id}: {e}")
        
        return {
            "status": "completed",
            "total_workouts": total_workouts,
            "successful_saves": successful_saves,
            "failed_saves": failed_saves,
            "success_rate": round(successful_saves / total_workouts * 100, 2) if total_workouts > 0 else 0
        }


class DatasetSimulator:
    """Simula ser um usuário específico do dataset e gera treinos personalizados"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.profile_manager = ProfileManager()
        self.current_user_profile = None
    
    async def load_user_profile(self) -> bool:
        """Carrega perfil do usuário para simulação"""
        try:
            result = await self.profile_manager.get_profile(self.user_id)
            if result["status"] == "success":
                self.current_user_profile = result["profile"]
                print(f"Perfil carregado para usuário: {self.user_id}")
                return True
            else:
                print(f"Erro ao carregar perfil: {result['message']}")
                return False
        except Exception as e:
            print(f"Erro ao carregar perfil: {e}")
            return False
    
    def get_user_context(self) -> Dict[str, Any]:
        """Retorna contexto completo do usuário para personalização de treinos"""
        if not self.current_user_profile:
            return {}
        
        profile = self.current_user_profile
        
        return {
            "user_id": self.user_id,
            "age": profile.get("age"),
            "fitness_level": profile.get("fitness_level"),
            "bmi": profile.get("bmi"),
            "resting_heart_rate": profile.get("resting_heart_rate"),
            "health_conditions": profile.get("health_conditions", []),
            "goals": profile.get("goals", []),
            "preferences": profile.get("preferences", []),
            "experience_context": f"Usuário {profile.get('fitness_level', 'iniciante')} de {profile.get('age')} anos"
        }
    
    async def simulate_workout_session(self, workout_type: Optional[str] = None) -> Dict[str, Any]:
        """Simula uma sessão de treino personalizada para o usuário"""
        
        if not self.current_user_profile:
            await self.load_user_profile()
        
        context = self.get_user_context()
        
        # Escolhe tipo de treino baseado nas preferências ou parâmetro
        if not workout_type:
            preferences = context.get("preferences", ["cardio"])
            workout_type = random.choice(preferences)
        
        # Gera treino personalizado
        workout = self._generate_personalized_workout(context, workout_type)
        
        # Salva no banco de dados
        success = save_workout_session(self.user_id, workout)
        
        return {
            "status": "success" if success else "error",
            "user_context": context,
            "workout_generated": workout,
            "saved_to_database": success,
            "recommendations": self._generate_post_workout_recommendations(context, workout)
        }
    
    def _generate_personalized_workout(self, context: Dict[str, Any], workout_type: str) -> Dict[str, Any]:
        """Gera treino personalizado baseado no contexto do usuário"""
        
        # Ajusta intensidade baseada no nível de fitness
        fitness_level = context.get("fitness_level", "beginner")
        age = context.get("age", 30)
        health_conditions = context.get("health_conditions", [])
        
        # Duração baseada no perfil
        duration_map = {
            "beginner": random.randint(20, 40),
            "intermediate": random.randint(30, 60),
            "advanced": random.randint(45, 75)
        }
        duration = duration_map[fitness_level]
        
        # Ajustes para idade
        if age > 50:
            duration = int(duration * 0.8)  # Reduz 20%
        if age > 65:
            duration = int(duration * 0.7)  # Reduz mais 10%
        
        # Ajustes para condições de saúde
        if "hypertension" in health_conditions:
            duration = min(duration, 45)  # Limita duração
        
        # Frequência cardíaca alvo
        max_hr = 220 - age
        resting_hr = context.get("resting_heart_rate", 70)
        
        if fitness_level == "beginner":
            target_hr = int(resting_hr + (max_hr - resting_hr) * 0.6)
        elif fitness_level == "intermediate":
            target_hr = int(resting_hr + (max_hr - resting_hr) * 0.7)
        else:
            target_hr = int(resting_hr + (max_hr - resting_hr) * 0.8)
        
        # Gera exercícios específicos
        exercises = self._select_personalized_exercises(workout_type, fitness_level, health_conditions, duration)
        
        return {
            "date": datetime.now().isoformat(),
            "workout_type": workout_type,
            "duration_minutes": duration,
            "exercises": exercises,
            "target_heart_rate": target_hr,
            "avg_heart_rate": target_hr + random.randint(-10, 10),
            "max_heart_rate": target_hr + random.randint(5, 20),
            "calories_estimated": self._estimate_calories(duration, fitness_level, workout_type),
            "perceived_exertion": random.randint(5, 8),
            "personalization_notes": f"Treino personalizado para {fitness_level}, idade {age}",
            "adaptations_made": self._list_adaptations_made(health_conditions, age)
        }
    
    def _select_personalized_exercises(self, workout_type: str, fitness_level: str, 
                                     health_conditions: List[str], duration: int) -> List[Dict[str, Any]]:
        """Seleciona exercícios personalizados baseados no perfil"""
        
        # Base de exercícios com adaptações
        exercise_library = {
            "cardio": {
                "beginner": [
                    {"name": "Caminhada na esteira", "intensity": "low", "duration": 15},
                    {"name": "Bicicleta ergométrica", "intensity": "low", "duration": 20},
                    {"name": "Elíptico suave", "intensity": "medium", "duration": 12}
                ],
                "intermediate": [
                    {"name": "Corrida intervalada", "intensity": "medium", "duration": 25},
                    {"name": "Spinning", "intensity": "high", "duration": 30},
                    {"name": "Escada/step", "intensity": "medium", "duration": 20}
                ],
                "advanced": [
                    {"name": "HIIT na esteira", "intensity": "high", "duration": 20},
                    {"name": "Corrida de resistência", "intensity": "high", "duration": 40},
                    {"name": "Circuito cardio", "intensity": "high", "duration": 30}
                ]
            },
            "strength": {
                "beginner": [
                    {"name": "Agachamento com peso corporal", "sets": 3, "reps": 12},
                    {"name": "Flexão modificada", "sets": 2, "reps": 8},
                    {"name": "Prancha", "sets": 3, "duration": 30}
                ],
                "intermediate": [
                    {"name": "Supino com halteres", "sets": 3, "reps": 10},
                    {"name": "Agachamento com barra", "sets": 4, "reps": 12},
                    {"name": "Remada curvada", "sets": 3, "reps": 10}
                ],
                "advanced": [
                    {"name": "Levantamento terra", "sets": 4, "reps": 8},
                    {"name": "Supino inclinado", "sets": 4, "reps": 10},
                    {"name": "Agachamento búlgaro", "sets": 3, "reps": 12}
                ]
            }
        }
        
        base_exercises = exercise_library.get(workout_type, {}).get(fitness_level, [])
        
        # Aplica adaptações para condições de saúde
        adapted_exercises = []
        for exercise in base_exercises:
            adapted_exercise = exercise.copy()
            
            # Adaptações para hipertensão
            if "hypertension" in health_conditions:
                if "intensity" in adapted_exercise and adapted_exercise["intensity"] == "high":
                    adapted_exercise["intensity"] = "medium"
                    adapted_exercise["adaptation_note"] = "Intensidade reduzida devido à hipertensão"
                
                # Evita exercícios isométricos prolongados
                if "Prancha" in adapted_exercise["name"]:
                    adapted_exercise["duration"] = min(adapted_exercise.get("duration", 30), 20)
            
            # Adaptações para diabetes
            if "diabetes" in health_conditions:
                adapted_exercise["monitoring_note"] = "Monitorar glicemia antes e após exercício"
            
            # Adaptações para artrite/problemas articulares
            if "arthritis" in health_conditions:
                if "Agachamento" in adapted_exercise["name"]:
                    adapted_exercise["name"] = "Agachamento parcial"
                    adapted_exercise["adaptation_note"] = "Amplitude reduzida para proteger articulações"
            
            adapted_exercises.append(adapted_exercise)
        
        return adapted_exercises
    
    def _estimate_calories(self, duration: int, fitness_level: str, workout_type: str) -> int:
        """Estima calorias queimadas baseado nos parâmetros"""
        
        base_calories_per_minute = {
            "cardio": {"beginner": 8, "intermediate": 10, "advanced": 12},
            "strength": {"beginner": 6, "intermediate": 8, "advanced": 10},
            "hiit": {"beginner": 12, "intermediate": 15, "advanced": 18},
            "flexibility": {"beginner": 3, "intermediate": 4, "advanced": 5}
        }
        
        rate = base_calories_per_minute.get(workout_type, {}).get(fitness_level, 8)
        calories = duration * rate + random.randint(-20, 20)
        
        return max(50, calories)  # Mínimo de 50 calorias
    
    def _list_adaptations_made(self, health_conditions: List[str], age: int) -> List[str]:
        """Lista adaptações feitas no treino"""
        
        adaptations = []
        
        if age > 50:
            adaptations.append("Duração ajustada para idade")
        if age > 65:
            adaptations.append("Aquecimento prolongado recomendado")
        
        if "hypertension" in health_conditions:
            adaptations.append("Intensidade moderada devido à hipertensão")
        if "diabetes" in health_conditions:
            adaptations.append("Monitoramento de glicemia recomendado")
        if "arthritis" in health_conditions:
            adaptations.append("Exercícios de baixo impacto priorizados")
        
        return adaptations
    
    def _generate_post_workout_recommendations(self, context: Dict[str, Any], 
                                             workout: Dict[str, Any]) -> List[str]:
        """Gera recomendações pós-treino personalizadas"""
        
        recommendations = []
        
        # Recomendações baseadas na intensidade
        perceived_exertion = workout.get("perceived_exertion", 5)
        if perceived_exertion >= 7:
            recommendations.append("Hidratação adequada é essencial após treino intenso")
            recommendations.append("Considere alongamento ou relaxamento")
        
        # Recomendações baseadas no tipo de treino
        workout_type = workout.get("workout_type")
        if workout_type == "strength":
            recommendations.append("Consumo de proteína nas próximas 2 horas")
            recommendations.append("Descanso de 48h para os músculos trabalhados")
        elif workout_type == "cardio":
            recommendations.append("Reposição de eletrólitos se duração > 60min")
        
        # Recomendações baseadas na idade
        age = context.get("age", 30)
        if age > 50:
            recommendations.append("Recuperação pode levar mais tempo - ouça seu corpo")
        
        # Recomendações baseadas em condições de saúde
        health_conditions = context.get("health_conditions", [])
        if "diabetes" in health_conditions:
            recommendations.append("Verifique glicemia pós-exercício")
        if "hypertension" in health_conditions:
            recommendations.append("Monitore pressão arterial se sentir tontura")
        
        return recommendations


# Função principal de importação e simulação
async def main_import_and_simulate():
    """Função principal para demonstrar o sistema completo"""
    
    print("SISTEMA DE IMPORTAÇÃO E SIMULAÇÃO - GYM DATASET")
    print("=" * 60)
    
    # 1. Configuração do importador
    importer = GymDatasetImporter()
    
    # 2. Exemplo de uso com dataset
    print("\n1. CARREGANDO DATASET...")
    
    # Exemplo com dados simulados (substitua pelo caminho real do CSV)
    sample_data = {
        'Member_ID': [f'M_{i}' for i in range(1, 101)],
        'Age': [random.randint(18, 65) for _ in range(100)],
        'Gender': [random.choice(['Male', 'Female']) for _ in range(100)],
        'Weight': [random.normalvariate(70, 15) for _ in range(100)],
        'Height': [random.normalvariate(170, 10) for _ in range(100)],
        'Experience_Level': [random.choice(['Beginner', 'Intermediate', 'Advanced']) for _ in range(100)],
        'Workout_Type': [random.choice(['Cardio', 'Strength', 'HIIT', 'Yoga']) for _ in range(100)],
        'Session_Duration': [random.randint(20, 90) for _ in range(100)],
        'Calories_Burned': [random.randint(150, 600) for _ in range(100)],
        'Heart_Rate': [random.randint(110, 170) for _ in range(100)]
    }
    
    df = pd.DataFrame(sample_data)
    print(f"Dataset simulado criado com {len(df)} registros")
    
    # 3. Análise da estrutura
    print("\n2. ANALISANDO ESTRUTURA DO DATASET...")
    analysis = importer.analyze_dataset_structure(df)
    print(f"Campos identificados: {len(analysis['identified_fields'])}")
    
    # 4. Limpeza e padronização
    print("\n3. LIMPANDO E PADRONIZANDO DADOS...")
    cleaned_df = importer.clean_and_standardize_data(df, analysis)
    
    # 5. Geração de perfis
    print("\n4. GERANDO PERFIS DE USUÁRIOS...")
    profiles = importer.generate_user_profiles(cleaned_df, analysis, max_users=20)
    
    # 6. Importação para banco
    print("\n5. IMPORTANDO USUÁRIOS PARA BANCO...")
    import_result = await importer.import_users_to_database(profiles)
    print(f"Importados: {import_result['successful_imports']}/{import_result['total_processed']}")
    
    # 7. Geração de histórico de treinos
    print("\n6. GERANDO HISTÓRICO DE TREINOS...")
    historical_workouts = importer.generate_historical_workouts(profiles, days_back=60)
    
    # 8. Salvamento do histórico
    print("\n7. SALVANDO HISTÓRICO NO BANCO...")
    save_result = await importer.save_workouts_to_database(historical_workouts)
    print(f"Treinos salvos: {save_result['successful_saves']}/{save_result['total_workouts']}")
    
    # 9. Simulação como usuário específico
    print("\n8. SIMULANDO COMO USUÁRIO ESPECÍFICO...")
    
    # Escolhe um usuário aleatório para simular
    sample_user_id = profiles[0]["user_id"]
    simulator = DatasetSimulator(sample_user_id)
    
    # Carrega perfil do usuário
    profile_loaded = await simulator.load_user_profile()
    
    if profile_loaded:
        print(f"Simulando como usuário: {sample_user_id}")
        
        # Contexto do usuário
        context = simulator.get_user_context()
        print(f"Contexto: {context['experience_context']}")
        
        # Simula 3 treinos diferentes
        workout_types = ["cardio", "strength", "flexibility"]
        
        for workout_type in workout_types:
            print(f"\n   Simulando treino de {workout_type}...")
            
            session_result = await simulator.simulate_workout_session(workout_type)
            
            if session_result["status"] == "success":
                workout = session_result["workout_generated"]
                print(f"   ✅ {workout_type.title()}: {workout['duration_minutes']}min, "
                      f"{workout['calories_estimated']} cal")
                
                # Mostra recomendações
                recommendations = session_result["recommendations"]
                if recommendations:
                    print(f"   💡 Recomendações: {recommendations[0]}")
    
    print("\n" + "=" * 60)
    print("IMPORTAÇÃO E SIMULAÇÃO CONCLUÍDAS!")
    print("=" * 60)


# Utilitários para análise de dados importados
class DatasetAnalyzer:
    """Analisador para datasets importados"""
    
    @staticmethod
    async def analyze_imported_data():
        """Analisa dados que foram importados"""
        
        from fitness_assistant.tools.user_listing import get_user_statistics, get_all_users
        
        print("ANÁLISE DOS DADOS IMPORTADOS")
        print("=" * 40)
        
        # Estatísticas gerais
        stats = await get_user_statistics()
        if stats['status'] == 'success':
            db_stats = stats['database_stats']
            print(f"Total de usuários: {db_stats['total_users']}")
            print(f"Usuários ativos: {db_stats['active_users_30d']}")
            print(f"Total de sessões: {db_stats['total_sessions']}")
            
            # Distribuições
            if 'fitness_level_distribution' in stats:
                print("\nDistribuição por nível:")
                for level, count in stats['fitness_level_distribution'].items():
                    print(f"  {level}: {count}")
        
        # Amostra de usuários
        users = await get_all_users(limit=5)
        if users['status'] == 'success':
            print(f"\nAmostra de usuários importados:")
            for user in users['users']:
                print(f"  {user['user_id']}: {user['age']}a, {user['fitness_level']}")
    
    @staticmethod
    def export_user_data_csv(filename: str = "exported_users.csv"):
        """Exporta dados dos usuários para CSV"""
        
        import asyncio
        from fitness_assistant.tools.user_listing import get_all_users
        
        async def export():
            users = await get_all_users(limit=1000)
            if users['status'] == 'success':
                df = pd.DataFrame(users['users'])
                df.to_csv(filename, index=False)
                print(f"Dados exportados para: {filename}")
                return len(df)
            return 0
        
        return asyncio.run(export())


# Script de linha de comando
def create_import_script():
    """Cria script standalone para importação"""
    
    script_content = '''#!/usr/bin/env python3
"""
Script para importar dataset de academia do Kaggle
Uso: python import_gym_dataset.py [caminho_para_csv]
"""

import sys
import asyncio
from pathlib import Path

# Adiciona src ao path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from fitness_assistant.data.dataset_importer import GymDatasetImporter, DatasetSimulator

async def main():
    if len(sys.argv) < 2:
        print("Uso: python import_gym_dataset.py [caminho_para_csv]")
        sys.exit(1)
    
    dataset_path = sys.argv[1]
    
    if not Path(dataset_path).exists():
        print(f"Arquivo não encontrado: {dataset_path}")
        sys.exit(1)
    
    print(f"Importando dataset: {dataset_path}")
    
    # Importa dataset
    importer = GymDatasetImporter()
    df = importer.load_dataset(dataset_path)
    
    if df.empty:
        print("Erro ao carregar dataset")
        sys.exit(1)
    
    # Processa dados
    analysis = importer.analyze_dataset_structure(df)
    cleaned_df = importer.clean_and_standardize_data(df, analysis)
    profiles = importer.generate_user_profiles(cleaned_df, analysis)
    
    # Importa para banco
    result = await importer.import_users_to_database(profiles)
    print(f"Usuários importados: {result['successful_imports']}")
    
    # Gera histórico
    workouts = importer.generate_historical_workouts(profiles)
    save_result = await importer.save_workouts_to_database(workouts)
    print(f"Treinos salvos: {save_result['successful_saves']}")
    
    print("Importação concluída!")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open("import_gym_dataset.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("Script de importação criado: import_gym_dataset.py")


if __name__ == "__main__":
    # Para testar localmente
    asyncio.run(main_import_and_simulate())