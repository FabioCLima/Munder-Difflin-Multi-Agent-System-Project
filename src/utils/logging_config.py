"""
Configuração de logging usando Loguru.
Fornece logging estruturado para todo o sistema com rotação automática.
"""

import sys
from pathlib import Path

from loguru import logger

from src.config import log_config


def setup_logging() -> None:
    """
    Configura o sistema de logging usando Loguru.

    Features:
    - Console output colorido
    - Arquivo com rotação automática
    - Diferentes níveis de log para console e arquivo
    - Thread-safe
    - Traceback formatados
    """
    # Remove handler padrão do loguru
    logger.remove()

    # ====== CONSOLE HANDLER (colorido e conciso) ======
    logger.add(
        sys.stdout,
        level=log_config.level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # ====== FILE HANDLER (completo e persistente) ======
    log_path = Path(log_config.file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_config.file,
        level="DEBUG",  # Log tudo no arquivo
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"
        ),
        rotation=log_config.rotation,
        retention=log_config.retention,
        compression="zip",
        enqueue=True,  # Thread-safe
        backtrace=True,
        diagnose=True,
    )

    logger.info(f"Logging configurado: console={log_config.level}, file={log_config.file}")


# Função auxiliar para criar loggers de módulo
def get_logger(name: str):
    """
    Retorna um logger bound ao nome do módulo.

    Uso:
        from src.utils.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Mensagem")
    """
    return logger.bind(name=name)


# Exportar logger principal
__all__ = ["logger", "setup_logging", "get_logger"]
