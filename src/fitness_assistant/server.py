# src/fitness_assistant/server.py
"""
Servidor MCP para Fitness Assistant
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Imports do projeto
from .config.settings import get_settings
from .database.connection import init_database

# Configurações
settings = get_settings()
logger = logging.getLogger(__name__)

# Servidor MCP
server = Server("fitness-assistant")

@server.list_tools()
async def list_tools() -> List[Tool]:
    """Lista todas as ferramentas disponíveis"""
    tools = []
    
    # Tool básica de teste
    tools.append(
        Tool(
            name="create_user_profile",
            description="Cria um novo perfil de usuário",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID único do usuário"},
                    "age": {"type": "integer", "minimum": 13, "maximum": 120},
                    "weight": {"type": "number", "minimum": 0},
                    "height": {"type": "number", "minimum": 0},
                    "fitness_level": {
                        "type": "string", 
                        "enum": ["beginner", "intermediate", "advanced"]
                    }
                },
                "required": ["user_id", "age", "weight", "height", "fitness_level"]
            }
        )
    )
    
    tools.append(
        Tool(
            name="get_user_profile",
            description="Obtém perfil do usuário",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID do usuário"}
                },
                "required": ["user_id"]
            }
        )
    )
    
    tools.append(
        Tool(
            name="calculate_heart_rate_zones",
            description="Calcula zonas de frequência cardíaca",
            inputSchema={
                "type": "object",
                "properties": {
                    "age": {"type": "integer", "minimum": 13, "maximum": 120},
                    "resting_hr": {"type": "integer", "minimum": 30, "maximum": 120}
                },
                "required": ["age", "resting_hr"]
            }
        )
    )
    
    return tools

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Executa uma ferramenta"""
    
    try:
        if name == "create_user_profile":
            # Importa e usa o manager apenas quando necessário
            from .tools.profile_manager import ProfileManager
            manager = ProfileManager()
            
            result = await manager.create_profile(
                user_id=arguments["user_id"],
                age=arguments["age"],
                weight=arguments["weight"],
                height=arguments["height"],
                fitness_level=arguments["fitness_level"]
            )
            
            return [TextContent(
                type="text",
                text=f"Resultado: {result}"
            )]
        
        elif name == "get_user_profile":
            from .tools.profile_manager import ProfileManager
            manager = ProfileManager()
            
            result = await manager.get_profile(arguments["user_id"])
            
            return [TextContent(
                type="text",
                text=f"Perfil: {result}"
            )]
        
        elif name == "calculate_heart_rate_zones":
            from .tools.heart_rate_manager import HeartRateManager
            manager = HeartRateManager()
            
            result = await manager.calculate_zones(
                age=arguments["age"],
                resting_hr=arguments["resting_hr"]
            )
            
            return [TextContent(
                type="text",
                text=f"Zonas de FC: {result}"
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Ferramenta '{name}' não encontrada"
            )]
            
    except Exception as e:
        logger.error(f"Erro ao executar ferramenta {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Erro: {str(e)}"
        )]

@server.list_resources()
async def list_resources() -> List[Resource]:
    """Lista recursos disponíveis"""
    return [
        Resource(
            uri="fitness://guide",
            name="Guia do Fitness Assistant",
            description="Guia de uso do assistente",
            mimeType="text/markdown"
        ),
        Resource(
            uri="fitness://safety",
            name="Diretrizes de Segurança",
            description="Diretrizes de segurança para exercícios",
            mimeType="text/markdown"
        )
    ]

@server.read_resource()
async def read_resource(uri: str) -> str:
    """Lê conteúdo de um recurso"""
    
    if uri == "fitness://guide":
        return """# Guia do Fitness Assistant

## Como usar:
1. Crie seu perfil com dados pessoais
2. Configure suas preferências de exercício
3. Calcule suas zonas de frequência cardíaca
4. Receba recomendações personalizadas

## Ferramentas disponíveis:
- `create_user_profile`: Criar perfil
- `get_user_profile`: Visualizar perfil  
- `calculate_heart_rate_zones`: Calcular zonas de FC
"""
    
    elif uri == "fitness://safety":
        return """# Diretrizes de Segurança

## Antes do Exercício
- Consulte um médico se tiver condições de saúde
- Faça aquecimento adequado
- Verifique equipamentos

## Durante o Exercício
- Monitore frequência cardíaca
- Pare se sentir dor ou desconforto
- Mantenha hidratação

## Alertas
- FC > 180 bpm: Reduza intensidade
- Dor aguda: Pare imediatamente
- Tontura/náusea: Descanse
"""
    
    return f"Recurso não encontrado: {uri}"

async def main():
    """Função principal do servidor"""
    
    try:
        # Inicializa banco de dados
        print("📊 Inicializando banco de dados...")
        await init_database()
        print("✅ Banco inicializado")
        
        print("🚀 Iniciando Fitness Assistant MCP Server...")
        print("💡 Aguardando conexões do Claude...")
        
        # Inicia servidor MCP
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
            
    except Exception as e:
        logger.error(f"Erro no servidor: {e}")
        print(f"❌ Erro no servidor: {e}")
        raise

if __name__ == "__main__":
    # Configura logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Servidor interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        exit(1)