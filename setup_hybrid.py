#!/usr/bin/env python3
"""
Setup híbrido: PostgreSQL no Docker + Aplicação local
"""
import subprocess
import sys
import time
import json
import os
from pathlib import Path

def check_docker():
    """Verifica se Docker está disponível"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("Docker encontrado")
            return True
        else:
            print("Docker não está funcionando")
            return False
    except FileNotFoundError:
        print("Docker não encontrado")
        print("Instale Docker Desktop: https://docs.docker.com/get-docker/")
        return False

def start_database():
    """Inicia PostgreSQL via Docker"""
    print("Iniciando PostgreSQL no Docker...")
    
    try:
        # Para qualquer container existente
        subprocess.run(["docker-compose", "down"], capture_output=True)
        
        # Inicia apenas o PostgreSQL
        result = subprocess.run([
            "docker-compose", "up", "-d", "postgres"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Erro ao iniciar Docker: {result.stderr}")
            return False
        
        print("Aguardando PostgreSQL ficar pronto...")
        
        # Aguarda até 60 segundos
        for i in range(30):
            try:
                result = subprocess.run([
                    "docker", "exec", "fitness_assistant_db",
                    "pg_isready", "-U", "fitness_user", "-d", "fitness_assistant"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("PostgreSQL pronto!")
                    return True
            except:
                pass
            
            print(f"Tentativa {i+1}/30...")
            time.sleep(2)
        
        print("Timeout aguardando PostgreSQL")
        return False
        
    except Exception as e:
        print(f"Erro: {e}")
        return False

def install_dependencies():
    """Instala dependências Python"""
    print("Instalando dependências...")
    
    try:
        # Dependências básicas para MCP
        packages = [
            "fastmcp",
            "pydantic",
            "pydantic-settings", 
            "python-dotenv",
            "sqlalchemy[asyncio]",
            "asyncpg",
            "alembic"
        ]
        
        subprocess.check_call([
            sys.executable, "-m", "pip", "install"
        ] + packages)
        
        print("Dependências instaladas")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Erro ao instalar dependências: {e}")
        return False

def create_project_structure():
    """Cria estrutura básica do projeto"""
    print("Criando estrutura do projeto...")
    
    directories = [
        "src/fitness_assistant",
        "src/fitness_assistant/tools",
        "src/fitness_assistant/database", 
        "src/fitness_assistant/models",
        "data",
        "logs",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Cria arquivos __init__.py
    init_files = [
        "src/__init__.py",
        "src/fitness_assistant/__init__.py",
        "src/fitness_assistant/tools/__init__.py",
        "src/fitness_assistant/database/__init__.py",
        "src/fitness_assistant/models/__init__.py"
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
    
    print("Estrutura criada")
    return True

def create_claude_config():
    """Cria configuração para Claude Desktop"""
    print("Criando configuração Claude Desktop...")
    
    project_dir = os.path.abspath(".").replace("\\", "\\\\")
    server_script = os.path.join(project_dir, "src", "fitness_assistant", "server.py").replace("\\", "\\\\")
    
    config = {
        "mcp_servers": {
            "fitness-assistant": {
                "command": "python",
                "args": [server_script],
                "env": {
                    "PYTHONPATH": project_dir,
                    "DATABASE_URL": "postgresql+asyncpg://fitness_user:fitness_dev_2024@localhost:5432/fitness_assistant"
                }
            }
        }
    }
    
    config_file = "config/claude_desktop_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    print(f"Configuração criada: {config_file}")
    print(f"Caminho do script: {server_script}")
    print(f"PYTHONPATH: {project_dir}")
    
    return True

def test_connection():
    """Testa conexão com o banco"""
    print("Testando conexão com banco...")
    
    test_script = '''
import asyncio
import asyncpg

async def test_db():
    try:
        conn = await asyncpg.connect(
            "postgresql://fitness_user:fitness_dev_2024@localhost:5432/fitness_assistant"
        )
        
        result = await conn.fetchval("SELECT version()")
        print("CONEXAO OK: " + str(result)[:50] + "...")
        
        await conn.close()
        return True
    except Exception as e:
        print("ERRO NA CONEXAO: " + str(e))
        return False

if __name__ == "__main__":
    success = asyncio.run(test_db())
    exit(0 if success else 1)
'''
    
    try:
        result = subprocess.run([
            sys.executable, "-c", test_script
        ], capture_output=True, text=True)
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("TESTE DE CONEXAO PASSOU")
            return True
        else:
            print("TESTE FALHOU: " + str(result.stderr))
            return False
            
    except Exception as e:
        print("ERRO NO TESTE: " + str(e))
        return False

def main():
    """Setup principal"""
    print("SETUP HÍBRIDO - FITNESS ASSISTANT")
    print("PostgreSQL no Docker + Aplicação Local")
    print("=" * 50)
    
    steps = [
        ("Verificando Docker", check_docker),
        ("Criando estrutura", create_project_structure), 
        ("Instalando dependências", install_dependencies),
        ("Iniciando PostgreSQL", start_database),
        ("Testando conexão", test_connection),
        ("Criando config Claude", create_claude_config)
    ]
    
    for description, step_function in steps:
        print(f"\n{description}...")
        if not step_function():
            print(f"Falha em: {description}")
            return False
    
    print("\n" + "=" * 50)
    print("SETUP CONCLUÍDO!")
    
    print("\nPróximos passos:")
    print("1. Copie o conteúdo de config/claude_desktop_config.json")
    print("2. Cole em %APPDATA%\\Claude\\claude_desktop_config.json")
    print("3. Reinicie Claude Desktop")
    print("4. Teste: 'Olá! As ferramentas fitness estão disponíveis?'")
    
    print("\nComandos úteis:")
    print("  docker-compose up -d postgres    # Inicia só o PostgreSQL")
    print("  docker-compose down              # Para todos containers")
    print("  docker-compose logs postgres     # Ver logs do banco")
    print("  http://localhost:8080            # Adminer (interface DB)")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n Setup falhou. Verifique os erros acima.")
        sys.exit(1)