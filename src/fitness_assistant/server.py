# src/fitness_assistant/server.py (Servidor MCP CLI)
"""
Servidor MCP usando mcp[cli] 1.6.0
"""
import asyncio
from typing import Any, Dict, List, Optional, Sequence
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
import mcp.server.stdio
import mcp.types

from .core.database import init_database, backup_database
from .tools.profile_manager import ProfileManager
from .tools.exercise_manager import ExerciseManager
from .tools.analytics_manager import AnalyticsManager
from .tools.heart_rate_manager import HeartRateManager
from .config.settings import get_settings

# Configurações
settings = get_settings()

# Gerenciadores
profile_manager = ProfileManager()
exercise_manager = ExerciseManager()
analytics_manager = AnalyticsManager()
heart_rate_manager = HeartRateManager()

# Servidor MCP
server = Server("fitness-assistant")

@server.list_tools()
async def list_tools() -> List[Tool]:
    """Lista todas as ferramentas disponíveis"""
    tools = []
    
    # Tools de perfil
    tools.extend([
        Tool(
            name="create_user_profile",
            description="Cria um novo perfil de usuário com validação completa",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID único do usuário"},
                    "age": {"type": "integer", "minimum": 13, "maximum": 120, "description": "Idade em anos"},
                    "weight": {"type": "number", "minimum": 0, "description": "Peso em kg"},
                    "height": {"type": "number", "minimum": 0, "description": "Altura em metros"},
                    "fitness_level": {
                        "type": "string", 
                        "enum": ["beginner", "intermediate", "advanced"],
                        "description": "Nível de condicionamento físico"
                    },
                    "health_conditions": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["diabetes", "hypertension", "heart_disease", "asthma", "arthritis", "pregnancy"]
                        },
                        "description": "Condições de saúde relevantes"
                    },
                    "preferences": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["cardio", "strength", "flexibility", "sports", "yoga", "swimming", "cycling", "running"]
                        },
                        "description": "Preferências de exercício"
                    },
                    "resting_heart_rate": {"type": "integer", "minimum": 30, "maximum": 120, "description": "FC de repouso (opcional)"},
                    "goals": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Objetivos fitness"
                    }
                },
                "required": ["user_id", "age", "weight", "height", "fitness_level"]
            }
        ),
        
        Tool(
            name="get_user_profile",
            description="Recupera informações completas do perfil do usuário",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID do usuário"}
                },
                "required": ["user_id"]
            }
        ),
        
        Tool(
            name="update_user_profile",
            description="Atualiza campos específicos do perfil do usuário",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID do usuário"},
                    "updates": {
                        "type": "object",
                        "description": "Campos a serem atualizados",
                        "additionalProperties": True
                    }
                },
                "required": ["user_id", "updates"]
            }
        )
    ])
    
    # Tools de frequência cardíaca
    tools.extend([
        Tool(
            name="calculate_heart_rate_zones",
            description="Calcula as 5 zonas de frequência cardíaca baseadas na idade e FC de repouso",
            inputSchema={
                "type": "object",
                "properties": {
                    "age": {"type": "integer", "minimum": 13, "maximum": 120, "description": "Idade em anos"},
                    "resting_hr": {"type": "integer", "minimum": 30, "maximum": 120, "description": "FC de repouso"}
                },
                "required": ["age", "resting_hr"]
            }
        ),
        
        Tool(
            name="analyze_current_heart_rate",
            description="Analisa a frequência cardíaca atual e determina zona de treinamento",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID do usuário"},
                    "current_hr": {"type": "integer", "minimum": 40, "maximum": 250, "description": "FC atual"},
                    "context": {"type": "string", "enum": ["rest", "warmup", "exercise", "recovery"], "description": "Contexto da medição"}
                },
                "required": ["user_id", "current_hr"]
            }
        )
    ])
    
    # Tools de exercícios
    tools.extend([
        Tool(
            name="recommend_exercises",
            description="Recomenda exercícios personalizados baseados no perfil e FC atual",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID do usuário"},
                    "current_hr": {"type": "integer", "minimum": 40, "maximum": 250, "description": "FC atual"},
                    "session_duration": {"type": "integer", "minimum": 5, "maximum": 180, "description": "Duração desejada em minutos"},
                    "workout_type": {
                        "type": "string",
                        "enum": ["cardio", "strength", "flexibility", "mixed", "hiit"],
                        "description": "Tipo de treino preferido"
                    },
                    "available_equipment": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["none", "dumbbells", "resistance_bands", "kettlebell", "barbell", "treadmill", "bike"]
                        },
                        "description": "Equipamentos disponíveis"
                    }
                },
                "required": ["user_id", "current_hr", "session_duration"]
            }
        ),
        
        Tool(
            name="get_exercise_variations",
            description="Obtém variações de um exercício baseadas no nível de fitness",
            inputSchema={
                "type": "object",
                "properties": {
                    "exercise_name": {"type": "string", "description": "Nome do exercício"},
                    "fitness_level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"], "description": "Nível de fitness"},
                    "modifications_needed": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Modificações necessárias (lesões, limitações)"
                    }
                },
                "required": ["exercise_name", "fitness_level"]
            }
        )
    ])
    
    # Tools de analytics
    tools.extend([
        Tool(
            name="log_workout_session",
            description="Registra uma sessão de treino completa",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID do usuário"},
                    "exercises": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "duration": {"type": "integer"},
                                "sets": {"type": "integer"},
                                "reps": {"type": "integer"},
                                "weight": {"type": "number"}
                            },
                            "required": ["name", "duration"]
                        },
                        "description": "Lista de exercícios realizados"
                    },
                    "duration_minutes": {"type": "integer", "minimum": 1, "description": "Duração total em minutos"},
                    "avg_heart_rate": {"type": "integer", "minimum": 40, "maximum": 250, "description": "FC média durante sessão"},
                    "max_heart_rate": {"type": "integer", "minimum": 40, "maximum": 250, "description": "FC máxima atingida"},
                    "perceived_exertion": {"type": "integer", "minimum": 1, "maximum": 10, "description": "Esforço percebido (escala 1-10)"},
                    "notes": {"type": "string", "description": "Observações sobre a sessão"}
                },
                "required": ["user_id", "exercises", "duration_minutes", "avg_heart_rate", "perceived_exertion"]
            }
        ),
        
        Tool(
            name="get_workout_analytics",
            description="Fornece análise detalhada dos treinos realizados",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID do usuário"},
                    "period_days": {"type": "integer", "minimum": 1, "maximum": 365, "description": "Período de análise em dias"},
                    "analysis_type": {
                        "type": "string",
                        "enum": ["summary", "progress", "trends", "recommendations"],
                        "description": "Tipo de análise desejada"
                    }
                },
                "required": ["user_id", "period_days"]
            }
        ),
        
        Tool(
            name="generate_progress_report",
            description="Gera relatório detalhado de progresso com insights",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID do usuário"},
                    "report_type": {
                        "type": "string",
                        "enum": ["weekly", "monthly", "quarterly"],
                        "description": "Tipo de relatório"
                    },
                    "include_comparisons": {"type": "boolean", "description": "Incluir comparações com períodos anteriores"},
                    "include_goals": {"type": "boolean", "description": "Incluir análise de objetivos"}
                },
                "required": ["user_id", "report_type"]
            }
        )
    ])
    
    return tools

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Executa uma ferramenta"""
    
    try:
        if name == "create_user_profile":
            result = await profile_manager.create_profile(**arguments)
        
        elif name == "get_user_profile":
            result = await profile_manager.get_profile(arguments["user_id"])
        
        elif name == "update_user_profile":
            result = await profile_manager.update_profile(arguments["user_id"], arguments["updates"])
        
        elif name == "calculate_heart_rate_zones":
            result = await heart_rate_manager.calculate_zones(arguments["age"], arguments["resting_hr"])
        
        elif name == "analyze_current_heart_rate":
            result = await heart_rate_manager.analyze_current_hr(
                arguments["user_id"], 
                arguments["current_hr"],
                arguments.get("context", "exercise")
            )
        
        elif name == "recommend_exercises":
            result = await exercise_manager.recommend_exercises(
                arguments["user_id"],
                arguments["current_hr"],
                arguments["session_duration"],
                arguments.get("workout_type", "mixed"),
                arguments.get("available_equipment", ["none"])
            )
        
        elif name == "get_exercise_variations":
            result = await exercise_manager.get_variations(
                arguments["exercise_name"],
                arguments["fitness_level"],
                arguments.get("modifications_needed", [])
            )
        
        elif name == "log_workout_session":
            result = await analytics_manager.log_session(
                arguments["user_id"],
                arguments["exercises"],
                arguments["duration_minutes"],
                arguments["avg_heart_rate"],
                arguments.get("max_heart_rate"),
                arguments["perceived_exertion"],
                arguments.get("notes", "")
            )
        
        elif name == "get_workout_analytics":
            result = await analytics_manager.get_analytics(
                arguments["user_id"],
                arguments["period_days"],
                arguments.get("analysis_type", "summary")
            )
        
        elif name == "generate_progress_report":
            result = await analytics_manager.generate_report(
                arguments["user_id"],
                arguments["report_type"],
                arguments.get("include_comparisons", True),
                arguments.get("include_goals", True)
            )
        
        else:
            result = {"error": f"Ferramenta desconhecida: {name}"}
        
        # Converte resultado para TextContent
        if isinstance(result, dict):
            import json
            content = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            content = str(result)
        
        return [TextContent(type="text", text=content)]
    
    except Exception as e:
        error_content = f"Erro ao executar {name}: {str(e)}"
        return [TextContent(type="text", text=error_content)]

@server.list_resources()
async def list_resources() -> List[Resource]:
    """Lista recursos disponíveis"""
    return [
        Resource(
            uri="fitness://user-guide",
            name="Guia do Usuário - Fitness Assistant",
            description="Guia completo de uso do assistente de treino",
            mimeType="text/markdown"
        ),
        Resource(
            uri="fitness://exercise-database", 
            name="Base de Dados de Exercícios",
            description="Catálogo completo de exercícios disponíveis",
            mimeType="application/json"
        ),
        Resource(
            uri="fitness://safety-guidelines",
            name="Diretrizes de Segurança",
            description="Recomendações de segurança para exercícios",
            mimeType="text/markdown"
        )
    ]

@server.read_resource()
async def read_resource(uri: str) -> str:
    """Lê conteúdo de um recurso"""
    
    if uri == "fitness://user-guide":
        return """# Guia do Fitness Assistant

## Como usar
1. Crie seu perfil com dados pessoais
2. Configure suas preferências de exercício
3. Informe sua FC atual para recomendações personalizadas
4. Registre suas sessões para acompanhar progresso

## Dicas de Segurança
- Sempre aqueça antes dos exercícios
- Monitore sua frequência cardíaca
- Pare se sentir dor ou desconforto
- Consulte um médico antes de iniciar novos programas
"""
    
    elif uri == "fitness://exercise-database":
        # Retorna catálogo de exercícios
        exercises = await exercise_manager.get_all_exercises()
        import json
        return json.dumps(exercises, indent=2, ensure_ascii=False)
    
    elif uri == "fitness://safety-guidelines":
        return """# Diretrizes de Segurança

## Antes do Exercício
- Verifique condições de saúde
- Faça aquecimento adequado
- Configure equipamentos corretamente

## Durante o Exercício
- Monitore sinais vitais
- Mantenha hidratação
- Respeite limites do corpo

## Alertas
- FC > 180 bpm: Reduza intensidade
- Dor aguda: Pare imediatamente
- Tontura/náusea: Descanse
"""
    
    return f"Recurso não encontrado: {uri}"

async def main():
    """Função principal do servidor"""
    
    # Inicializa banco de dados
    print("📊 Inicializando banco de dados...")
    init_database()
    
    print("🚀 Iniciando Fitness Assistant MCP Server...")
    print("💡 Aguardando conexões do Claude...")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())