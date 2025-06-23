# scripts/setup_postgres.py
"""
Setup completo do Fitness Assistant com PostgreSQL
"""
import os
import sys
import json
import subprocess
import asyncio
from pathlib import Path
from typing import Optional

def check_prerequisites():
    """Verifica todos os pré-requisitos"""
    print("🔍 Verificando pré-requisitos...")
    
    missing = []
    
    # Python 3.9+
    if sys.version_info < (3, 9):
        missing.append("Python 3.9+")
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # uv
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ uv: {result.stdout.strip()}")
        else:
            missing.append("uv")
    except FileNotFoundError:
        missing.append("uv")
    
    # PostgreSQL
    try:
        result = subprocess.run(["psql", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PostgreSQL client: {result.stdout.strip()}")
        else:
            missing.append("PostgreSQL client")
    except FileNotFoundError:
        missing.append("PostgreSQL client")
    
    if missing:
        print("❌ Pré-requisitos faltando:")
        for item in missing:
            print(f"  - {item}")
        
        print("\n📦 Comandos de instalação:")
        if "uv" in missing:
            print("  curl -LsSf https://astral.sh/uv/install.sh | sh")
        if "PostgreSQL client" in missing:
            print("  # Ubuntu/Debian: apt install postgresql-client")
            print("  # macOS: brew install postgresql")
            print("  # Windows: https://www.postgresql.org/download/")
        
        return False
    
    return True

def create_project_structure():
    """Cria estrutura completa do projeto"""
    print("📁 Criando estrutura do projeto...")
    
    directories = [
        "src/fitness_assistant",
        "src/fitness_assistant/models",
        "src/fitness_assistant/tools", 
        "src/fitness_assistant/core",
        "src/fitness_assistant/config",
        "src/fitness_assistant/utils",
        "src/fitness_assistant/database",
        "tests",
        "tests/fixtures",
        "migrations",
        "data",
        "config",
        "logs",
        "scripts/database"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Cria __init__.py files
    init_files = [
        "src/fitness_assistant/__init__.py",
        "src/fitness_assistant/models/__init__.py",
        "src/fitness_assistant/tools/__init__.py",
        "src/fitness_assistant/core/__init__.py",
        "src/fitness_assistant/config/__init__.py",
        "src/fitness_assistant/utils/__init__.py",
        "src/fitness_assistant/database/__init__.py",
        "tests/__init__.py"
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
    
    print("✅ Estrutura do projeto criada")

def setup_database_environment():
    """Configura ambiente de banco de dados"""
    print("🐘 Configurando ambiente PostgreSQL...")
    
    # Verifica se há PostgreSQL rodando
    try:
        result = subprocess.run([
            "pg_isready", "-h", "localhost", "-p", "5432"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PostgreSQL detectado rodando")
            return True
        else:
            print("⚠️ PostgreSQL não detectado")
    except FileNotFoundError:
        print("⚠️ pg_isready não encontrado")
    
    # Oferece opções
    print("\n📋 Opções para PostgreSQL:")
    print("1. Docker (recomendado para desenvolvimento)")
    print("2. Instalação local")
    print("3. Usar banco existente")
    
    choice = input("Escolha uma opção (1-3): ").strip()
    
    if choice == "1":
        return setup_docker_postgres()
    elif choice == "2":
        return setup_local_postgres()
    elif choice == "3":
        return configure_existing_postgres()
    else:
        print("❌ Opção inválida")
        return False

def setup_docker_postgres():
    """Configura PostgreSQL via Docker"""
    print("🐳 Configurando PostgreSQL com Docker...")
    
    # Verifica se Docker está disponível
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        print("✅ Docker encontrado")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ Docker não encontrado")
        print("📦 Instale Docker: https://docs.docker.com/get-docker/")
        return False
    
    # Cria docker-compose.yml
    docker_compose = """version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: fitness_assistant_db
    environment:
      POSTGRES_DB: fitness_assistant
      POSTGRES_USER: fitness_user
      POSTGRES_PASSWORD: fitness_dev_2024
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8"
    ports:
      - "5432:5432"
    volumes:
      - fitness_postgres_data:/var/lib/postgresql/data
      - ./scripts/database/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U fitness_user -d fitness_assistant"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: fitness_assistant_redis
    ports:
      - "6379:6379"
    volumes:
      - fitness_redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

volumes:
  fitness_postgres_data:
  fitness_redis_data:
"""
    
    with open("docker-compose.yml", "w") as f:
        f.write(docker_compose)
    
    # Cria script de inicialização
    init_sql = """-- Fitness Assistant Database Initialization
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Configurações de performance
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET pg_stat_statements.track = 'all';

-- Timezone
ALTER DATABASE fitness_assistant SET timezone TO 'UTC';

-- Schema para testes
CREATE SCHEMA IF NOT EXISTS test_data;

-- Função de limpeza automática
CREATE OR REPLACE FUNCTION cleanup_old_heart_rate_data()
RETURNS void AS $
BEGIN
    DELETE FROM heart_rate_data 
    WHERE timestamp < NOW() - INTERVAL '1 year';
    
    RAISE NOTICE 'Limpeza de dados antigos executada';
END;
$ LANGUAGE plpgsql;
"""
    
    Path("scripts/database").mkdir(parents=True, exist_ok=True)
    with open("scripts/database/init.sql", "w") as f:
        f.write(init_sql)
    
    # Inicia containers
    try:
        print("🚀 Iniciando containers...")
        result = subprocess.run([
            "docker-compose", "up", "-d"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PostgreSQL e Redis iniciados via Docker")
            
            # Aguarda banco ficar pronto
            print("⏳ Aguardando banco ficar pronto...")
            for i in range(30):
                try:
                    result = subprocess.run([
                        "docker-compose", "exec", "-T", "postgres",
                        "pg_isready", "-U", "fitness_user", "-d", "fitness_assistant"
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print("✅ Banco de dados pronto!")
                        break
                except:
                    pass
                
                import time
                time.sleep(2)
            else:
                print("⚠️ Timeout aguardando banco")
                return False
            
            # Atualiza .env
            update_env_file({
                "DATABASE_URL": "postgresql+asyncpg://fitness_user:fitness_dev_2024@localhost:5432/fitness_assistant",
                "REDIS_URL": "redis://localhost:6379/0"
            })
            
            return True
        else:
            print(f"❌ Erro ao iniciar Docker: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro com Docker: {e}")
        return False

def setup_local_postgres():
    """Configura PostgreSQL local"""
    print("🏠 Configuração para PostgreSQL local...")
    
    # Solicita credenciais
    print("📝 Configure as credenciais do banco:")
    host = input("Host (localhost): ").strip() or "localhost"
    port = input("Porta (5432): ").strip() or "5432"
    database = input("Nome do banco (fitness_assistant): ").strip() or "fitness_assistant"
    username = input("Usuário (postgres): ").strip() or "postgres"
    password = input("Senha: ").strip()
    
    # Testa conexão
    database_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    if test_database_connection(database_url):
        # Atualiza .env
        update_env_file({
            "DATABASE_URL": database_url.replace("postgresql://", "postgresql+asyncpg://"),
            "DB_HOST": host,
            "DB_PORT": port,
            "DB_NAME": database,
            "DB_USER": username,
            "DB_PASSWORD": password
        })
        return True
    else:
        return False

def configure_existing_postgres():
    """Configura para usar banco existente"""
    print("🔗 Configuração para banco existente...")
    
    database_url = input("URL completa do banco: ").strip()
    
    if not database_url:
        print("❌ URL do banco é obrigatória")
        return False
    
    if test_database_connection(database_url):
        update_env_file({
            "DATABASE_URL": database_url.replace("postgresql://", "postgresql+asyncpg://")
        })
        return True
    else:
        return False

def test_database_connection(database_url: str) -> bool:
    """Testa conexão com banco de dados"""
    print("🔍 Testando conexão com banco...")
    
    try:
        # Remove asyncpg para teste com psycopg2
        test_url = database_url.replace("+asyncpg", "")
        
        # Tenta conectar usando psql
        from urllib.parse import urlparse
        parsed = urlparse(test_url)
        
        env = os.environ.copy()
        if parsed.password:
            env["PGPASSWORD"] = parsed.password
        
        result = subprocess.run([
            "psql", 
            "-h", parsed.hostname or "localhost",
            "-p", str(parsed.port or 5432),
            "-U", parsed.username or "postgres",
            "-d", parsed.path.lstrip("/") or "postgres",
            "-c", "SELECT version();"
        ], capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            print("✅ Conexão com banco bem-sucedida")
            return True
        else:
            print(f"❌ Erro de conexão: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar conexão: {e}")
        return False

def update_env_file(config: dict):
    """Atualiza arquivo .env"""
    env_content = """# Fitness Assistant MCP - Configurações

# === APLICAÇÃO ===
DEBUG=true
LOG_LEVEL=INFO
APP_NAME="Fitness Assistant MCP"
APP_VERSION="1.0.0"

# === BANCO DE DADOS ===
"""
    
    for key, value in config.items():
        env_content += f'{key}={value}\n'
    
    env_content += """
# === CONFIGURAÇÕES DE SAÚDE ===
MAX_HR_WARNING=180
MIN_AGE=13
MAX_AGE=120

# === CONFIGURAÇÕES DE SESSÃO ===
DEFAULT_SESSION_DURATION=30
MAX_SESSION_DURATION=180

# === ANALYTICS ===
ANALYTICS_RETENTION=365
PROGRESS_WEEKS=4

# === MCP ===
MCP_SERVER_NAME=fitness-assistant
MCP_DESCRIPTION="Assistente de treino com PostgreSQL"

# === CONFIGURAÇÕES AVANÇADAS DO BANCO ===
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_QUERY_LOGGING=false
DB_CONNECTION_TIMEOUT=30
DB_COMMAND_TIMEOUT=60

# === BACKUP ===
DB_BACKUP_ENABLED=true
DB_BACKUP_RETENTION=30

# === MONITORAMENTO ===
DB_ENABLE_METRICS=true
DB_SLOW_QUERY_THRESHOLD=1.0
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✅ Arquivo .env atualizado")

def setup_uv_project():
    """Configura projeto com uv"""
    print("📦 Configurando projeto uv...")
    
    try:
        # Sincroniza dependências
        result = subprocess.run(["uv", "sync", "--dev"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Dependências instaladas via uv")
        else:
            print(f"⚠️ Warning uv sync: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro uv sync: {e}")
        return False

def setup_database_migrations():
    """Configura sistema de migrações"""
    print("🔄 Configurando migrações...")
    
    try:
        # Inicializa Alembic
        result = subprocess.run([
            "uv", "run", "alembic", "init", "migrations"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Alembic inicializado")
        else:
            print("ℹ️ Alembic já inicializado")
        
        # Cria primeira migração
        result = subprocess.run([
            "uv", "run", "alembic", "revision", 
            "--autogenerate", "-m", "Initial tables"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migração inicial criada")
        else:
            print(f"⚠️ Erro na migração: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nas migrações: {e}")
        return False

def run_database_migrations():
    """Executa migrações do banco"""
    print("⬆️ Executando migrações...")
    
    try:
        result = subprocess.run([
            "uv", "run", "alembic", "upgrade", "head"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migrações aplicadas")
            return True
        else:
            print(f"❌ Erro nas migrações: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro executando migrações: {e}")
        return False

def test_mcp_integration():
    """Testa integração MCP"""
    print("🧪 Testando integração...")
    
    test_script = '''
import asyncio
import sys
sys.path.insert(0, "src")

async def test_basic_functionality():
    try:
        # Testa imports
        from fitness_assistant.database.connection import init_database
        from fitness_assistant.tools.profile_manager import ProfileManager
        
        print("✅ Imports básicos OK")
        
        # Testa conexão com banco
        await init_database()
        print("✅ Conexão com banco OK")
        
        # Testa criação de perfil
        manager = ProfileManager()
        result = await manager.create_profile(
            user_id="test_setup",
            age=25,
            weight=70.0,
            height=1.75,
            fitness_level="beginner"
        )
        
        if result["status"] == "success":
            print("✅ Criação de perfil OK")
        else:
            print(f"⚠️ Perfil: {result}")
        
        print("🎉 Todos os testes básicos passaram!")
        
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
'''
    
    try:
        result = subprocess.run([
            "uv", "run", "python", "-c", test_script
        ], capture_output=True, text=True)
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("✅ Testes de integração passaram")
            return True
        else:
            print(f"❌ Falha nos testes: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")
        return False

def create_claude_config():
    """Cria configuração para Claude Desktop"""
    print("🤖 Criando configuração Claude Desktop...")
    
    project_dir = os.path.abspath(".")
    
    config = {
        "mcpServers": {
            "fitness-assistant": {
                "command": "uv",
                "args": [
                    "run", "python", 
                    f"{project_dir}/src/fitness_assistant/server.py"
                ],
                "cwd": project_dir,
                "env": {
                    "PYTHONPATH": project_dir
                }
            }
        }
    }
    
    config_file = "config/claude_desktop_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Configuração criada: {config_file}")
    
    # Instruções
    print("\n📋 Para configurar Claude Desktop:")
    print("1. Localize seu arquivo de configuração:")
    print("   - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json")
    print("   - Windows: %APPDATA%\\Claude\\claude_desktop_config.json")
    print(f"2. Adicione o conteúdo de {config_file}")
    print("3. Reinicie Claude Desktop")

def create_helpful_scripts():
    """Cria scripts úteis"""
    print("📜 Criando scripts úteis...")
    
    scripts = {
        "run_server.py": '''#!/usr/bin/env python3
"""Executa o servidor MCP"""
import subprocess
import sys

def main():
    try:
        subprocess.run([
            "uv", "run", "python", "src/fitness_assistant/server.py"
        ])
    except KeyboardInterrupt:
        print("\\n👋 Servidor parado")

if __name__ == "__main__":
    main()
''',
        
        "run_migrations.py": '''#!/usr/bin/env python3
"""Executa migrações do banco"""
import subprocess
import sys

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "upgrade"
    
    if action == "create":
        message = input("Mensagem da migração: ")
        subprocess.run([
            "uv", "run", "alembic", "revision", 
            "--autogenerate", "-m", message
        ])
    elif action == "upgrade":
        subprocess.run(["uv", "run", "alembic", "upgrade", "head"])
    elif action == "downgrade":
        revision = input("Revision para downgrade (-1 para anterior): ")
        subprocess.run(["uv", "run", "alembic", "downgrade", revision])
    elif action == "current":
        subprocess.run(["uv", "run", "alembic", "current"])
    else:
        print("Uso: python run_migrations.py [create|upgrade|downgrade|current]")

if __name__ == "__main__":
    main()
''',
        
        "dev.sh": '''#!/bin/bash
# Script de desenvolvimento

echo "🛠️ Modo desenvolvimento"

# Verificar banco
echo "🔍 Verificando banco..."
uv run python -c "
import asyncio
from src.fitness_assistant.database.connection import init_database
asyncio.run(init_database())
print('✅ Banco OK')
"

# Executar testes
echo "🧪 Executando testes..."
uv run pytest -x

# Executar servidor
echo "🚀 Iniciando servidor..."
uv run python src/fitness_assistant/server.py
'''
    }
    
    for script_name, content in scripts.items():
        with open(script_name, "w") as f:
            f.write(content)
        
        # Torna executável
        if script_name.endswith('.sh'):
            try:
                os.chmod(script_name, 0o755)
            except:
                pass
    
    print("✅ Scripts criados")

def main():
    """Execução principal do setup"""
    print("🚀 SETUP COMPLETO FITNESS ASSISTANT MCP + POSTGRESQL")
    print("="*60)
    
    steps = [
        ("Verificando pré-requisitos", check_prerequisites),
        ("Criando estrutura do projeto", create_project_structure),
        ("Configurando PostgreSQL", setup_database_environment),
        ("Configurando projeto uv", setup_uv_project),
        ("Configurando migrações", setup_database_migrations),
        ("Executando migrações", run_database_migrations),
        ("Testando integração", test_mcp_integration),
        ("Criando configuração Claude", create_claude_config),
        ("Criando scripts úteis", create_helpful_scripts)
    ]
    
    failed_steps = []
    
    for description, step_function in steps:
        print(f"\n📌 {description}...")
        try:
            success = step_function()
            if success is False:
                failed_steps.append(description)
                
                # Pergunta se quer continuar
                continue_setup = input(f"❌ '{description}' falhou. Continuar? (y/N): ").lower()
                if continue_setup != 'y':
                    break
                    
        except Exception as e:
            print(f"❌ Erro em '{description}': {e}")
            failed_steps.append(description)
            
            continue_setup = input("Continuar mesmo assim? (y/N): ").lower()
            if continue_setup != 'y':
                break
    
    print("\n" + "="*60)
    
    if failed_steps:
        print("⚠️ SETUP PARCIALMENTE CONCLUÍDO")
        print("Etapas que falharam:")
        for step in failed_steps:
            print(f"  - {step}")
    else:
        print("🎉 SETUP CONCLUÍDO COM SUCESSO!")
    
    print("\n📋 Próximos passos:")
    print("1. Configure Claude Desktop com config/claude_desktop_config.json")
    print("2. Execute: python run_server.py")
    print("3. Teste no Claude: 'Crie um perfil de usuário teste'")
    
    print("\n💡 Comandos úteis:")
    print("  python run_server.py          # Executa servidor MCP")
    print("  python run_migrations.py      # Gerencia migrações")
    print("  ./dev.sh                      # Modo desenvolvimento")
    print("  uv run pytest                 # Executa testes")
    print("  docker-compose up -d          # Inicia PostgreSQL (se Docker)")
    print("  docker-compose down           # Para PostgreSQL (se Docker)")

if __name__ == "__main__":
    main()