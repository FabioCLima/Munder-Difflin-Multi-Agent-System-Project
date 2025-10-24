"""
Tools para o Inventory Agent.
Fornece funções para consultar e gerenciar estoque.
"""

import pandas as pd
from pydantic_ai import RunContext

from src.database import DatabaseContext, get_all_inventory, get_stock_level
from src.utils.logging_config import logger

# ============================================================================
# TOOL 1: CHECK ALL INVENTORY
# ============================================================================


def check_all_inventory_tool(ctx: RunContext[DatabaseContext]) -> dict[str, int]:
    """
    Lista TODOS os itens em estoque e suas quantidades.

    Esta tool é usada quando o usuário pergunta:
    - "What do you have in stock?"
    - "Show me all available items"
    - "List your inventory"

    Args:
        ctx: Contexto com db_engine e current_date

    Returns:
        Dict[item_name, quantity] - Ex: {"A4 paper": 650, "Cardstock": 400}

    Example:
        >>> inventory = check_all_inventory_tool(ctx)
        >>> print(inventory)
        {"A4 paper": 650, "Cardstock": 400, "Glossy paper": 200}
    """
    logger.info(f"[TOOL] check_all_inventory em {ctx.deps.current_date}")

    try:
        inventory = get_all_inventory(as_of_date=ctx.deps.current_date, engine=ctx.deps.db_engine)

        logger.debug(f"Inventário completo: {len(inventory)} itens")
        return inventory

    except Exception as e:
        logger.error(f"Erro ao consultar inventário completo: {e}")
        return {"error": f"Failed to fetch inventory: {str(e)}"}


# ============================================================================
# TOOL 2: CHECK SPECIFIC ITEM STOCK
# ============================================================================


def check_item_stock_tool(ctx: RunContext[DatabaseContext], item_name: str) -> dict[str, any]:
    """
    Verifica a quantidade disponível de um item específico.

    Esta tool é usada quando o usuário pergunta:
    - "Do you have A4 paper?"
    - "How much cardstock is available?"
    - "Check stock for glossy paper"

    Args:
        ctx: Contexto com db_engine e current_date
        item_name: Nome EXATO do item (case-sensitive)

    Returns:
        Dict com: {
            "item_name": str,
            "current_stock": int,
            "available": bool
        }

    Example:
        >>> result = check_item_stock_tool(ctx, "A4 paper")
        >>> print(result)
        {"item_name": "A4 paper", "current_stock": 650, "available": True}
    """
    logger.info(f"[TOOL] check_item_stock: '{item_name}' em {ctx.deps.current_date}")

    try:
        stock_df = get_stock_level(
            item_name=item_name, as_of_date=ctx.deps.current_date, engine=ctx.deps.db_engine
        )

        if stock_df.empty or stock_df["current_stock"].iloc[0] == 0:
            logger.warning(f"Item '{item_name}' não encontrado ou sem estoque")
            return {
                "item_name": item_name,
                "current_stock": 0,
                "available": False,
                "message": f"Item '{item_name}' is not available or out of stock",
            }

        current_stock = int(stock_df["current_stock"].iloc[0])

        logger.debug(f"Stock de '{item_name}': {current_stock} unidades")

        return {
            "item_name": item_name,
            "current_stock": current_stock,
            "available": current_stock > 0,
        }

    except Exception as e:
        logger.error(f"Erro ao consultar stock de '{item_name}': {e}")
        return {"item_name": item_name, "error": str(e), "available": False}


# ============================================================================
# TOOL 3: IDENTIFY LOW STOCK ITEMS
# ============================================================================


def identify_low_stock_tool(ctx: RunContext[DatabaseContext]) -> list[dict]:
    """
    Identifica itens com estoque abaixo do nível mínimo.

    Esta tool é usada para:
    - Alertar sobre itens que precisam de reposição
    - Reordering Agent usa para decidir o que comprar
    - Relatórios de status de inventário

    Args:
        ctx: Contexto com db_engine e current_date

    Returns:
        Lista de dicts com itens críticos:
        [
            {
                "item_name": str,
                "current_stock": int,
                "min_stock_level": int,
                "shortage": int,  # Quanto falta para atingir mínimo
                "status": "critical"
            },
            ...
        ]

    Example:
        >>> low_stock = identify_low_stock_tool(ctx)
        >>> print(low_stock)
        [
            {
                "item_name": "A4 paper",
                "current_stock": 45,
                "min_stock_level": 50,
                "shortage": 5,
                "status": "critical"
            }
        ]
    """
    logger.info(f"[TOOL] identify_low_stock em {ctx.deps.current_date}")

    try:
        # Buscar estoque atual de todos os itens
        current_inventory = get_all_inventory(
            as_of_date=ctx.deps.current_date, engine=ctx.deps.db_engine
        )

        # Buscar min_stock_level da tabela inventory
        inventory_df = pd.read_sql(
            "SELECT item_name, min_stock_level, unit_price FROM inventory", ctx.deps.db_engine
        )

        low_stock_items = []

        for _, row in inventory_df.iterrows():
            item_name = row["item_name"]
            min_level = int(row["min_stock_level"])
            current = current_inventory.get(item_name, 0)

            # Se estoque está abaixo do mínimo
            if current < min_level:
                shortage = min_level - current

                low_stock_items.append(
                    {
                        "item_name": item_name,
                        "current_stock": current,
                        "min_stock_level": min_level,
                        "shortage": shortage,
                        "unit_price": float(row["unit_price"]),
                        "status": "critical",
                    }
                )

        if low_stock_items:
            logger.warning(f"Itens com estoque baixo: {len(low_stock_items)}")
            for item in low_stock_items:
                logger.debug(
                    f"  - {item['item_name']}: {item['current_stock']}/{item['min_stock_level']}"
                )
        else:
            logger.info("Nenhum item com estoque baixo")

        return low_stock_items

    except Exception as e:
        logger.error(f"Erro ao identificar low stock: {e}")
        return []


# ============================================================================
# TOOL 4: GET ITEM DETAILS
# ============================================================================


def get_item_details_tool(ctx: RunContext[DatabaseContext], item_name: str) -> dict[str, any]:
    """
    Retorna detalhes completos de um item (preço, categoria, estoque, etc).

    Args:
        ctx: Contexto com db_engine e current_date
        item_name: Nome do item

    Returns:
        Dict com todos os detalhes do item

    Example:
        >>> details = get_item_details_tool(ctx, "A4 paper")
        >>> print(details)
        {
            "item_name": "A4 paper",
            "category": "paper",
            "unit_price": 0.05,
            "current_stock": 650,
            "min_stock_level": 50
        }
    """
    logger.info(f"[TOOL] get_item_details: '{item_name}'")

    try:
        # Buscar info da tabela inventory
        query = """
            SELECT item_name, category, unit_price, min_stock_level
            FROM inventory
            WHERE item_name = ?
        """
        item_df = pd.read_sql(query, ctx.deps.db_engine, params=(item_name,))

        if item_df.empty:
            logger.warning(f"Item '{item_name}' não encontrado no inventário")
            return {"error": f"Item '{item_name}' not found in inventory catalog"}

        # Buscar estoque atual
        stock_df = get_stock_level(
            item_name=item_name, as_of_date=ctx.deps.current_date, engine=ctx.deps.db_engine
        )

        current_stock = int(stock_df["current_stock"].iloc[0])

        details = {
            "item_name": item_df["item_name"].iloc[0],
            "category": item_df["category"].iloc[0],
            "unit_price": float(item_df["unit_price"].iloc[0]),
            "min_stock_level": int(item_df["min_stock_level"].iloc[0]),
            "current_stock": current_stock,
            "status": "available" if current_stock > 0 else "out_of_stock",
        }

        logger.debug(f"Detalhes do item: {details}")
        return details

    except Exception as e:
        logger.error(f"Erro ao buscar detalhes de '{item_name}': {e}")
        return {"error": str(e)}


# ============================================================================
# TOOL 5: SEARCH ITEMS BY KEYWORDS
# ============================================================================


def search_items_tool(ctx: RunContext[DatabaseContext], keywords: str) -> list[dict]:
    """
    Busca itens no inventário por palavras-chave (fuzzy search).

    Útil para quando o usuário não sabe o nome exato do item:
    - "Do you have glossy something?"
    - "Show me all paper items"
    - "What cardstock do you have?"

    Args:
        ctx: Contexto com db_engine e current_date
        keywords: Palavras-chave para busca (case-insensitive)

    Returns:
        Lista de items que fazem match

    Example:
        >>> results = search_items_tool(ctx, "glossy")
        >>> print(results)
        [
            {
                "item_name": "Glossy paper",
                "category": "paper",
                "unit_price": 0.20,
                "current_stock": 200
            }
        ]
    """
    logger.info(f"[TOOL] search_items: keywords='{keywords}'")

    try:
        # Buscar todos os itens que contenham a keyword
        query = """
            SELECT item_name, category, unit_price
            FROM inventory
            WHERE LOWER(item_name) LIKE ?
        """

        keyword_pattern = f"%{keywords.lower()}%"
        items_df = pd.read_sql(query, ctx.deps.db_engine, params=(keyword_pattern,))

        if items_df.empty:
            logger.info(f"Nenhum item encontrado com keywords '{keywords}'")
            return []

        # Buscar estoque atual de cada item
        current_inventory = get_all_inventory(
            as_of_date=ctx.deps.current_date, engine=ctx.deps.db_engine
        )

        results = []
        for _, row in items_df.iterrows():
            item_name = row["item_name"]
            current_stock = current_inventory.get(item_name, 0)

            results.append(
                {
                    "item_name": item_name,
                    "category": row["category"],
                    "unit_price": float(row["unit_price"]),
                    "current_stock": current_stock,
                    "available": current_stock > 0,
                }
            )

        logger.debug(f"Encontrados {len(results)} itens com keywords '{keywords}'")
        return results

    except Exception as e:
        logger.error(f"Erro ao buscar itens com keywords '{keywords}': {e}")
        return []


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "check_all_inventory_tool",
    "check_item_stock_tool",
    "identify_low_stock_tool",
    "get_item_details_tool",
    "search_items_tool",
]
