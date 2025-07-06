#!/usr/bin/env python3
"""
Script para executar o servidor MCP
"""
import asyncio
import sys
import os
from pathlib import Path

# Adiciona o diretório src ao Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

async def main():
    """Executa o servidor MCP"""
    try:
        print("🚀 Iniciando Fitness Assistant...")
        print("📡 Servidor MCP rodando...")
        print("💡 Use Ctrl+C para parar")
        
        # Importa e executa o servidor
        from fitness_assistant.server import main as server_main
        await server_main()
        
    except KeyboardInterrupt:
        print("\n👋 Servidor interrompido pelo usuário")
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("💡 Certifique-se de que as dependências estão instaladas")
        print("   Execute: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)