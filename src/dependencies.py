"""
Dependências dos agentes para testes
"""

from typing import Any

from pydantic import BaseModel


class InventoryDependencies(BaseModel):
    """Dependências para o Inventory Agent"""

    db_path: str = "munder_difflin.db"
    current_date: str = "2025-01-15"
    db_engine: Any = None


class QuotingDependencies(BaseModel):
    """Dependências para o Quoting Agent"""

    db_path: str = "munder_difflin.db"
    customer_id: str | None = None
    current_date: str = "2025-01-15"
    db_engine: Any = None


class SalesDependencies(BaseModel):
    """Dependências para o Sales Agent"""

    db_path: str = "munder_difflin.db"
    customer_id: str | None = None
    current_date: str = "2025-01-15"
    db_engine: Any = None


class ReorderingDependencies(BaseModel):
    """Dependências para o Reordering Agent"""

    db_path: str = "munder_difflin.db"
    auto_approve: bool = True  # Auto-aprovar pedidos
    current_date: str = "2025-01-15"
    db_engine: Any = None
    safety_stock_multiplier: float = 1.5  # 50% acima do mínimo
