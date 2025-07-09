# scripts/setup.py
"""
Script de instalação e configuração inicial
"""
import os
import sys
import json
import shutil
from pathlib import Path

def create_directory_structure():
    """Cria estrutura de diretórios"""
    directories = [
        "data",
        "data/backups", 
        "logs",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Diretório criado: {directory}")

def create_env_file():
    """Cria arquivo .env de exemplo"""
    env_content = """# Configurações do Assistente de Treino Físico

# Ambiente
DEBUG=false
LOG_LEVEL=INFO

# Banco de Dados
DATABASE_TYPE=memory
# DATABASE_URL=postgresql://user:password@localhost/fitness_db

# Diretórios
DATA_DIR=data
BACKUP_DIR=data/backups

# Configurações de Segurança
MAX_HR_WARNING=180
MIN_AGE=13
MAX_AGE=120

# Configurações de Sessão
DEFAULT_SESSION_DURATION=30
MAX_SESSION_DURATION=180

# Analytics
ANALYTICS_RETENTION=365
PROGRESS_WEEKS=4

# Notificações
ENABLE_SAFETY_ALERTS=true
ENABLE_PROGRESS_NOTIFICATIONS=true

# MCP
MCP_SERVER_NAME=fitness-assistant
MCP_DESCRIPTION="Assistente inteligente para recomendações de exercícios"
"""
    
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)
    print("✅ Arquivo .env criado")

def create_claude_config():
    """Cria configuração para Claude Desktop"""
    
    # Detecta o diretório do projeto
    project_dir = os.path.abspath(".")
    main_script = os.path.join(project_dir, "src", "fitness_assistant", "main.py")
    
    config = {
        "mcp_servers": {
            "fitness-assistant": {
                "command": "python",
                "args": [main_script],
                "env": {
                    "PYTHONPATH": project_dir
                }
            }
        }
    }
    
    config_file = "config/claude_desktop_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, indent=2)
    
    print(f"✅ Configuração Claude criada: {config_file}")
    print("\n📋 Para integrar com Claude Desktop:")
    print("1. Localize seu arquivo de configuração Claude:")
    print("   - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json")
    print("   - Windows: %APPDATA%\\Claude\\claude_desktop_config.json")
    print(f"2. Adicione o conteúdo de {config_file} ao seu arquivo Claude")
    print("3. Reinicie o Claude Desktop")

def install_dependencies():
    """Instala dependências do projeto"""
    print("📦 Instalando dependências...")
    
    try:
        import subprocess
        
        # Instala dependências principais
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependências principais instaladas")
        
        # Pergunta sobre dependências de desenvolvimento
        install_dev = input("Instalar dependências de desenvolvimento? (y/N): ").lower().strip()
        if install_dev in ['y', 'yes']:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"])
            print("✅ Dependências de desenvolvimento instaladas")
            
    except subprocess.CalledProcessError as e:
        print(f" Erro ao instalar dependências: {e}")
        return False
    
    return True

def create_sample_data():
    """Cria dados de exemplo para teste"""
    sample_exercises = {
        "walk_light": {
            "id": "walk_light",
            "name": "Caminhada Leve",
            "type": "cardio",
            "description": "Caminhada em ritmo confortável para iniciantes",
            "instructions": [
                "Mantenha postura ereta",
                "Braços relaxados, movimento natural",
                "Respire de forma natural e ritmada"
            ],
            "muscle_groups": ["pernas", "core"],
            "equipment_needed": ["none"],
            "difficulty_level": "low",
            "duration_range": [10, 60],
            "calories_per_minute": {
                "beginner": 3.5,
                "intermediate": 4.0, 
                "advanced": 4.5
            },
            "contraindications": [],
            "modifications": ["Use bastão para apoio se necessário"],
            "safety_notes": ["Hidrate-se adequadamente", "Use calçados apropriados"]
        },
        "squat_bodyweight": {
            "id": "squat_bodyweight",
            "name": "Agachamento Corpo Livre",
            "type": "strength",
            "description": "Agachamento usando apenas o peso corporal",
            "instructions": [
                "Pés na largura dos ombros",
                "Desça até coxas paralelas ao chão",
                "Mantenha joelhos alinhados com os pés"
            ],
            "muscle_groups": ["quadriceps", "glúteos", "core"],
            "equipment_needed": ["none"],
            "difficulty_level": "moderate",
            "duration_range": [5, 20],
            "calories_per_minute": {
                "beginner": 5.0,
                "intermediate": 6.0,
                "advanced": 7.0
            },
            "contraindications": ["lesões no joelho", "problemas na lombar"],
            "modifications": ["Use cadeira para apoio", "Agachamento parcial"],
            "safety_notes": ["Não force além do confortável", "Mantenha core contraído"]
        }
    }
    
    exercises_file = "data/exercises_database.json"
    with open(exercises_file, "w", encoding="utf-8") as f:
        json.dump(sample_exercises, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Banco de exercícios criado: {exercises_file}")

def run_tests():
    """Executa testes básicos"""
    print("🧪 Executando testes básicos...")
    
    try:
        # Testa importação dos módulos principais
        sys.path.insert(0, "src")
        
        from fitness_assistant.models.user import UserProfile
        from fitness_assistant.models.exercise import Exercise
        from fitness_assistant.core.database import init_database
        
        print("✅ Importações básicas funcionando")
        
        # Testa criação de perfil
        profile = UserProfile(
            user_id="test_user",
            age=25,
            weight=70.0,
            height=1.75,
            fitness_level="beginner"
        )
        print(f"✅ Perfil de teste criado: BMI = {profile.bmi}")
        
        # Testa inicialização do banco
        init_database()
        print("✅ Banco de dados inicializado")
        
        return True
        
    except Exception as e:
        print(f" Erro nos testes: {e}")
        return False

def setup_git():
    """Configura Git e cria .gitignore"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
logs/
data/backups/
*.log
.coverage
htmlcov/
.pytest_cache/
.mypy_cache/

# Sensitive data
config/local_settings.py
.env.local
.env.production
"""
    
    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write(gitignore_content)
    print("✅ .gitignore criado")

def main():
    """Executa setup completo"""
    print("🚀 Iniciando setup do Assistente de Treino Físico\n")
    
    steps = [
        ("Criando estrutura de diretórios", create_directory_structure),
        ("Criando arquivo de ambiente", create_env_file),
        ("Configurando Git", setup_git),
        ("Instalando dependências", install_dependencies),
        ("Criando configuração Claude", create_claude_config),
        ("Criando dados de exemplo", create_sample_data),
        ("Executando testes básicos", run_tests)
    ]
    
    failed_steps = []
    
    for description, step_function in steps:
        print(f"\n📌 {description}...")
        try:
            success = step_function()
            if success is False:
                failed_steps.append(description)
        except Exception as e:
            print(f" Erro em '{description}': {e}")
            failed_steps.append(description)
    
    print("\n" + "="*50)
    print("🎉 SETUP CONCLUÍDO!")
    
    if failed_steps:
        print(f"\n⚠️ Algumas etapas falharam:")
        for step in failed_steps:
            print(f"  - {step}")
    else:
        print("\n✅ Todas as etapas foram executadas com sucesso!")
    
    print("\n📋 Próximos passos:")
    print("1. Configure o Claude Desktop com o arquivo em config/")
    print("2. Execute: python src/fitness_assistant/main.py")
    print("3. Teste as ferramentas no Claude Desktop")
    print("4. Consulte a documentação em docs/")

if __name__ == "__main__":
    main()


# scripts/populate_data.py
"""
Script para popular o banco com dados de teste
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import random

# Adiciona o diretório src ao Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def create_test_users():
    """Cria usuários de teste"""
    from fitness_assistant.models.user import UserProfile
    from fitness_assistant.core.database import save_user_profile
    
    test_users = [
        {
            "user_id": "joao_123",
            "age": 28,
            "weight": 75.0,
            "height": 1.75,
            "fitness_level": "intermediate",
            "health_conditions": [],
            "preferences": ["cardio", "strength"],
            "resting_heart_rate": 65,
            "goals": ["perder peso", "ganhar massa muscular"]
        },
        {
            "user_id": "maria_456",
            "age": 35,
            "weight": 62.0,
            "height": 1.65,
            "fitness_level": "beginner",
            "health_conditions": [],
            "preferences": ["yoga", "flexibility"],
            "resting_heart_rate": 70,
            "goals": ["melhorar flexibilidade", "reduzir stress"]
        },
        {
            "user_id": "carlos_789",
            "age": 42,
            "weight": 85.0,
            "height": 1.80,
            "fitness_level": "advanced",
            "health_conditions": ["hypertension"],
            "preferences": ["strength", "cycling"],
            "resting_heart_rate": 58,
            "goals": ["manter forma física", "controlar pressão"]
        }
    ]
    
    for user_data in test_users:
        profile = UserProfile(**user_data)
        save_user_profile(profile)
        print(f"✅ Usuário criado: {user_data['user_id']}")

def create_test_sessions():
    """Cria sessões de teste"""
    from fitness_assistant.core.database import save_workout_session
    
    users = ["joao_123", "maria_456", "carlos_789"]
    
    for user_id in users:
        # Cria 10 sessões dos últimos 30 dias
        for i in range(10):
            date = datetime.now() - timedelta(days=random.randint(1, 30))
            
            session = {
                "date": date.isoformat(),
                "exercises": [
                    {
                        "name": random.choice(["Caminhada", "Corrida", "Agachamento", "Flexão"]),
                        "duration": random.randint(10, 30),
                        "type": random.choice(["cardio", "strength"])
                    }
                ],
                "duration_minutes": random.randint(20, 60),
                "avg_heart_rate": random.randint(120, 160),
                "perceived_exertion": random.randint(4, 8),
                "calories_estimated": random.randint(150, 400)
            }
            
            save_workout_session(user_id, session)
        
        print(f"✅ 10 sessões criadas para {user_id}")

def main():
    """Popula banco com dados de teste"""
    print("📊 Populando banco com dados de teste...")
    
    try:
        from fitness_assistant.core.database import init_database
        
        # Inicializa banco
        init_database()
        
        # Cria dados de teste
        create_test_users()
        create_test_sessions()
        
        print("\n🎉 Dados de teste criados com sucesso!")
        print("💡 Agora você pode testar o assistente com dados reais")
        
    except Exception as e:
        print(f" Erro ao popular dados: {e}")

if __name__ == "__main__":
    main()