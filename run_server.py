#!/usr/bin/env python3
"""
Script para executar o servidor MCP do projeto
"""
import sys
import os
import logging
from pathlib import Path

# Configura logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adiciona o diretório src ao Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def main():
    """Executa o servidor MCP"""
    try:
        logger.info("Iniciando Fitness Assistant")
        logger.info("Conectando com FastMCP 2.0")
        logger.info("Use Ctrl+C para parar")
        
        # Importa e executa o servidor diretamente
        from fitness_assistant.server import main as server_main
        server_main()  # Não usa await aqui
        
    except KeyboardInterrupt:
        logger.info("Servidor interrompido pelo usuario")
    except ImportError as e:
        logger.error("ERRO DE IMPORTACAO: %s", e)
        logger.error("Verifique se todas as dependencias estao instaladas:")
        logger.error("pip install fastmcp pydantic numpy")
        return 1
    except Exception as e:
        logger.error("ERRO: %s", e)
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()  # Remove asyncio.run
    sys.exit(exit_code)