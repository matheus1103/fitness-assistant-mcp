# src/fitness_assistant/tools/user_listing.py
"""
Sistema completo para listar usuários no projeto fitness assistant
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

# Importações do projeto
from fitness_assistant.database.repositories.user_repo import user_repo
from fitness_assistant.tools.profile_manager import ProfileManager
from fitness_assistant.core.database import list_all_users, get_database_stats
from fitness_assistant.models.user import UserProfile, FitnessLevel


class UserListing:
    """Classe principal para listagem de usuários"""
    
    def __init__(self):
        self.profile_manager = ProfileManager()
    
    async def list_all_users_detailed(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Lista todos os usuários com informações detalhadas
        
        Args:
            limit: Número máximo de usuários a retornar
            offset: Offset para paginação
            
        Returns:
            Dict com status, dados dos usuários e metadados
        """
        try:
            usuarios = await user_repo.list_users(limit=limit, offset=offset)
            
            users_data = []
            for user in usuarios:
                user_info = {
                    "user_id": user.user_id,
                    "age": user.age,
                    "weight": user.weight,
                    "height": user.height,
                    "fitness_level": user.fitness_level.value,
                    "bmi": round(user.bmi, 2) if user.bmi else None,
                    "resting_heart_rate": user.resting_heart_rate,
                    "health_conditions": user.health_conditions or [],
                    "goals": user.goals or [],
                    "preferences": user.preferences or {},
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None
                }
                users_data.append(user_info)
            
            return {
                "status": "success",
                "count": len(users_data),
                "limit": limit,
                "offset": offset,
                "users": users_data,
                "message": f"Encontrados {len(users_data)} usuários"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro ao listar usuários detalhados: {str(e)}",
                "users": []
            }
    
    async def list_users_summary(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Lista usuários com informações resumidas
        
        Args:
            limit: Número máximo de usuários
            offset: Offset para paginação
            
        Returns:
            Dict com dados resumidos dos usuários
        """
        try:
            result = await self.profile_manager.list_profiles()
            
            if result["status"] == "success":
                # Aplica paginação manual se necessário
                profiles = result["profiles"]
                if offset > 0 or limit < len(profiles):
                    profiles = profiles[offset:offset + limit]
                
                return {
                    "status": "success",
                    "count": len(profiles),
                    "total_count": result["count"],
                    "limit": limit,
                    "offset": offset,
                    "users": profiles
                }
            else:
                return result
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro ao listar usuários resumidos: {str(e)}",
                "users": []
            }
    
    def list_user_ids_only(self) -> Dict[str, Any]:
        """
        Lista apenas os IDs dos usuários (mais rápido)
        
        Returns:
            Dict com lista de IDs
        """
        try:
            user_ids = list_all_users()
            
            return {
                "status": "success",
                "count": len(user_ids),
                "user_ids": user_ids,
                "message": f"Encontrados {len(user_ids)} usuários"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro ao listar IDs: {str(e)}",
                "user_ids": []
            }
    
    async def list_users_with_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Lista usuários com filtros específicos
        
        Args:
            filters: Dict com filtros (fitness_level, age_min, age_max, active_days)
            
        Returns:
            Dict com usuários filtrados
        """
        try:
            users_data = []
            
            # Filtro por nível de fitness
            if "fitness_level" in filters:
                users = await user_repo.get_users_by_fitness_level(filters["fitness_level"])
                users_data.extend(users)
            
            # Filtro por faixa etária
            elif "age_min" in filters and "age_max" in filters:
                users = await user_repo.get_users_by_age_range(
                    filters["age_min"], 
                    filters["age_max"]
                )
                users_data.extend(users)
            
            # Filtro por usuários ativos
            elif "active_days" in filters:
                users = await user_repo.get_active_users(days=filters["active_days"])
                users_data.extend(users)
            
            # Se nenhum filtro específico, lista todos
            else:
                users = await user_repo.list_users(limit=100)
                users_data.extend(users)
            
            # Formata dados
            formatted_users = []
            for user in users_data:
                user_info = {
                    "user_id": user.user_id,
                    "age": user.age,
                    "fitness_level": user.fitness_level.value,
                    "bmi": round(user.bmi, 2) if user.bmi else None,
                    "created_at": user.created_at.isoformat()
                }
                formatted_users.append(user_info)
            
            return {
                "status": "success",
                "count": len(formatted_users),
                "filters_applied": filters,
                "users": formatted_users
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro ao filtrar usuários: {str(e)}",
                "users": []
            }
    
    async def get_users_statistics(self) -> Dict[str, Any]:
        """
        Gera estatísticas completas dos usuários
        
        Returns:
            Dict com estatísticas detalhadas
        """
        try:
            # Estatísticas do SQLAlchemy
            sql_stats = await user_repo.get_users_summary()
            
            # Estatísticas do sistema em memória
            memory_stats = get_database_stats()
            
            # Combina as estatísticas
            combined_stats = {
                "status": "success",
                "generated_at": datetime.now().isoformat(),
                "database_stats": {
                    "total_users": sql_stats.get("total_users", 0),
                    "active_users_30d": sql_stats.get("active_users_30d", 0),
                    "total_exercises": memory_stats.get("total_exercises", 0),
                    "total_sessions": memory_stats.get("total_sessions", 0)
                },
                "fitness_level_distribution": sql_stats.get("by_fitness_level", {}),
                "age_group_distribution": sql_stats.get("by_age_group", {}),
                "activity_metrics": {
                    "active_users_last_30_days": memory_stats.get("active_users_last_30_days", 0)
                }
            }
            
            return combined_stats
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro ao gerar estatísticas: {str(e)}"
            }
    
    async def search_users(self, search_term: str) -> Dict[str, Any]:
        """
        Busca usuários por termo
        
        Args:
            search_term: Termo de busca (user_id)
            
        Returns:
            Dict com usuários encontrados
        """
        try:
            users = await user_repo.search_users(search_term)
            
            users_data = []
            for user in users:
                user_info = {
                    "user_id": user.user_id,
                    "age": user.age,
                    "fitness_level": user.fitness_level.value,
                    "bmi": round(user.bmi, 2) if user.bmi else None,
                    "created_at": user.created_at.isoformat()
                }
                users_data.append(user_info)
            
            return {
                "status": "success",
                "search_term": search_term,
                "count": len(users_data),
                "users": users_data
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro na busca: {str(e)}",
                "users": []
            }


# Funções de conveniência para uso direto
async def get_all_users(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """Função de conveniência para listar todos os usuários"""
    listing = UserListing()
    return await listing.list_all_users_detailed(limit=limit, offset=offset)


async def get_users_summary(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """Função de conveniência para resumo de usuários"""
    listing = UserListing()
    return await listing.list_users_summary(limit=limit, offset=offset)


def get_user_ids() -> Dict[str, Any]:
    """Função de conveniência para apenas IDs"""
    listing = UserListing()
    return listing.list_user_ids_only()


async def get_users_by_filter(**filters) -> Dict[str, Any]:
    """Função de conveniência para busca com filtros"""
    listing = UserListing()
    return await listing.list_users_with_filters(filters)


async def get_user_statistics() -> Dict[str, Any]:
    """Função de conveniência para estatísticas"""
    listing = UserListing()
    return await listing.get_users_statistics()


# Classe para integração com MCP Server
class MCPUserListingTool:
    """Integração com MCP Server para ferramentas de listagem"""
    
    @staticmethod
    def get_list_users_tool():
        """Retorna a definição da ferramenta MCP para listar usuários"""
        from mcp import Tool
        
        return Tool(
            name="list_users",
            description="Lista todos os usuários cadastrados no sistema com opções de filtro e paginação",
            inputSchema={
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["detailed", "summary", "ids_only", "filtered", "statistics", "search"],
                        "description": "Modo de listagem",
                        "default": "summary"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Número máximo de usuários a retornar",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 500
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Offset para paginação",
                        "default": 0,
                        "minimum": 0
                    },
                    "filters": {
                        "type": "object",
                        "description": "Filtros para aplicar na busca",
                        "properties": {
                            "fitness_level": {
                                "type": "string",
                                "enum": ["beginner", "intermediate", "advanced"]
                            },
                            "age_min": {"type": "integer", "minimum": 13},
                            "age_max": {"type": "integer", "maximum": 120},
                            "active_days": {"type": "integer", "minimum": 1}
                        }
                    },
                    "search_term": {
                        "type": "string",
                        "description": "Termo de busca (para mode=search)"
                    }
                }
            }
        )
    
    @staticmethod
    async def handle_list_users_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handler para a ferramenta MCP de listagem de usuários"""
        mode = arguments.get("mode", "summary")
        limit = arguments.get("limit", 50)
        offset = arguments.get("offset", 0)
        filters = arguments.get("filters", {})
        search_term = arguments.get("search_term", "")
        
        listing = UserListing()
        
        try:
            if mode == "detailed":
                return await listing.list_all_users_detailed(limit=limit, offset=offset)
            
            elif mode == "summary":
                return await listing.list_users_summary(limit=limit, offset=offset)
            
            elif mode == "ids_only":
                return listing.list_user_ids_only()
            
            elif mode == "filtered":
                return await listing.list_users_with_filters(filters)
            
            elif mode == "statistics":
                return await listing.get_users_statistics()
            
            elif mode == "search":
                if not search_term:
                    return {
                        "status": "error",
                        "message": "search_term é obrigatório para mode=search"
                    }
                return await listing.search_users(search_term)
            
            else:
                return {
                    "status": "error",
                    "message": f"Modo '{mode}' não reconhecido"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro na execução: {str(e)}"
            }


# Função principal para demonstração
async def main():
    """Função principal para demonstrar o uso do sistema"""
    print("Sistema de Listagem de Usuários - Fitness Assistant")
    print("=" * 60)
    
    listing = UserListing()
    
    # 1. Lista todos os usuários (resumo)
    print("\n1. Listagem Resumida:")
    result1 = await listing.list_users_summary(limit=10)
    print(f"Status: {result1['status']}")
    print(f"Usuários encontrados: {result1['count']}")
    
    # 2. Lista apenas IDs
    print("\n2. Apenas IDs:")
    result2 = listing.list_user_ids_only()
    print(f"Total de IDs: {result2['count']}")
    print(f"IDs: {result2['user_ids'][:5]}...")  # Primeiros 5
    
    # 3. Estatísticas
    print("\n3. Estatísticas:")
    result3 = await listing.get_users_statistics()
    if result3['status'] == 'success':
        stats = result3['database_stats']
        print(f"Total de usuários: {stats['total_users']}")
        print(f"Usuários ativos (30d): {stats['active_users_30d']}")
    
    # 4. Filtro por nível de fitness
    print("\n4. Filtro por Iniciantes:")
    result4 = await listing.list_users_with_filters({"fitness_level": "beginner"})
    print(f"Iniciantes encontrados: {result4['count']}")
    
    # 5. Listagem detalhada (primeiros 3)
    print("\n5. Listagem Detalhada (3 primeiros):")
    result5 = await listing.list_all_users_detailed(limit=3)
    if result5['status'] == 'success' and result5['users']:
        for user in result5['users']:
            print(f"  - {user['user_id']}: {user['age']}a, {user['fitness_level']}")


# Exportações para uso externo
__all__ = [
    'UserListing',
    'MCPUserListingTool',
    'get_all_users',
    'get_users_summary', 
    'get_user_ids',
    'get_users_by_filter',
    'get_user_statistics'
]


if __name__ == "__main__":
    # Para testar localmente
    asyncio.run(main())