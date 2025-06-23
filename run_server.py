# scripts/run_server.py
"""
Script para executar o servidor MCP
"""
import sys
import os
from pathlib import Path

# Adiciona o diretório src ao Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def main():
    """Executa o servidor MCP"""
    try:
        from fitness_assistant.server import server
        print("🚀 Iniciando Assistente de Treino Físico...")
        print("📡 Servidor MCP rodando...")
        print("💡 Use Ctrl+C para parar")
        
        server.run()
        
    except KeyboardInterrupt:
        print("\n👋 Servidor interrompido pelo usuário")
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("💡 Certifique-se de que as dependências estão instaladas")
        print("   Execute: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    main()
