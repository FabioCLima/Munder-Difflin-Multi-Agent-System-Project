"""
Configurações centralizadas do sistema Munder Difflin.
Carrega variáveis de ambiente e define constantes do projeto.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Diretórios do projeto
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
DB_PATH = PROJECT_ROOT / "munder_difflin.db"

# Criar diretórios se não existirem
LOGS_DIR.mkdir(exist_ok=True)


@dataclass
class OpenAIConfig:
    """Configurações do OpenAI."""

    api_key: str
    base_url: str
    model: str

    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        """Cria configuração a partir de variáveis de ambiente."""
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url=os.getenv("OPENAI_BASE_URL", "https://openai.vocareum.com/v1"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        )


@dataclass
class LogConfig:
    """Configurações de logging."""

    level: str
    file: str
    rotation: str
    retention: str

    @classmethod
    def from_env(cls) -> "LogConfig":
        """Cria configuração a partir de variáveis de ambiente."""
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file=os.getenv("LOG_FILE", str(LOGS_DIR / "munder_difflin.log")),
            rotation=os.getenv("LOG_ROTATION", "10 MB"),
            retention=os.getenv("LOG_RETENTION", "7 days"),
        )


@dataclass
class DatabaseConfig:
    """Configurações do banco de dados."""

    url: str
    seed: int

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Cria configuração a partir de variáveis de ambiente."""
        return cls(
            url=os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}"),
            seed=int(os.getenv("DATABASE_SEED", "137")),
        )


# Constantes de negócio
class BusinessRules:
    """Regras de negócio do sistema."""

    # Descontos bulk por tamanho de pedido (baseado em análise do histórico)
    BULK_DISCOUNTS = {
        "small": 0.05,  # 5% desconto
        "medium": 0.10,  # 10% desconto
        "large": 0.15,  # 15% desconto
    }

    # Prazo padrão de entrega ao cliente (dias úteis)
    CUSTOMER_DELIVERY_DAYS = 4

    # Multiplicador para cálculo de reordenação (estoque ótimo)
    REORDER_MULTIPLIER = 2

    # Cash inicial do sistema
    INITIAL_CASH = 50000.0

    # Data inicial do sistema
    INITIAL_DATE = "2025-01-01"


# Instâncias globais de configuração
openai_config = OpenAIConfig.from_env()
log_config = LogConfig.from_env()
db_config = DatabaseConfig.from_env()

# Validar configurações críticas (apenas em produção)
import sys

if not openai_config.api_key and "pytest" not in sys.modules:
    raise ValueError(
        "OPENAI_API_KEY não encontrada. Configure no arquivo .env ou variável de ambiente."
    )
