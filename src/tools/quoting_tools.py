"""
Tools para o Quoting Agent.
Fornece funções para gerar cotações inteligentes com descontos bulk.
"""

import pandas as pd
from pydantic_ai import RunContext

from src.config import BusinessRules
from src.database import DatabaseContext, get_stock_level, search_quote_history
from src.utils.logging_config import logger

# ============================================================================
# TOOL 1: SEARCH SIMILAR QUOTES
# ============================================================================


def search_similar_quotes_tool(
    ctx: RunContext[DatabaseContext], keywords: list[str], limit: int = 5
) -> list[dict]:
    """
    Busca cotações históricas similares para referência de preços.

    Esta tool é ESSENCIAL para pricing inteligente!
    O LLM usa cotações passadas para:
    - Identificar padrões de desconto
    - Consistência de preços
    - Justificar valores

    Args:
        ctx: Contexto com db_engine
        keywords: Lista de palavras-chave (ex: ["glossy", "cardstock"])
        limit: Máximo de resultados (padrão 5)

    Returns:
        Lista de cotações similares com metadata

    Example:
        >>> quotes = search_similar_quotes_tool(ctx, ["glossy", "cardstock"])
        >>> print(quotes[0])
        {
            "original_request": "500 sheets glossy paper...",
            "total_amount": 95.0,
            "quote_explanation": "10% bulk discount applied...",
            "job_type": "office manager",
            "order_size": "small",
            "event_type": "ceremony"
        }
    """
    logger.info(f"[TOOL] search_similar_quotes: keywords={keywords}")

    try:
        quotes = search_quote_history(search_terms=keywords, limit=limit, engine=ctx.deps.db_engine)

        if not quotes:
            logger.warning(f"Nenhuma cotação encontrada com keywords {keywords}")
            return []

        logger.debug(f"Encontradas {len(quotes)} cotações similares")

        # Adicionar análise de descontos
        for quote in quotes:
            # Extrair insights úteis
            if quote.get("order_size"):
                discount_rate = BusinessRules.BULK_DISCOUNTS.get(quote["order_size"].lower(), 0.05)
                quote["typical_discount_rate"] = discount_rate

        return quotes

    except Exception as e:
        logger.error(f"Erro ao buscar cotações similares: {e}")
        return []


# ============================================================================
# TOOL 2: GET ITEM PRICING
# ============================================================================


def get_item_pricing_tool(ctx: RunContext[DatabaseContext], item_name: str) -> dict[str, any]:
    """
    Retorna o preço unitário de um item do catálogo.

    Args:
        ctx: Contexto com db_engine
        item_name: Nome exato do item

    Returns:
        Dict com: {
            "item_name": str,
            "unit_price": float,
            "category": str
        }

    Example:
        >>> pricing = get_item_pricing_tool(ctx, "A4 paper")
        >>> print(pricing)
        {"item_name": "A4 paper", "unit_price": 0.05, "category": "paper"}
    """
    logger.info(f"[TOOL] get_item_pricing: '{item_name}'")

    try:
        query = """
            SELECT item_name, unit_price, category
            FROM inventory
            WHERE item_name = ?
        """
        result = pd.read_sql(query, ctx.deps.db_engine, params=(item_name,))

        if result.empty:
            logger.warning(f"Preço não encontrado para '{item_name}'")
            return {"error": f"Item '{item_name}' not found in catalog"}

        pricing = {
            "item_name": result["item_name"].iloc[0],
            "unit_price": float(result["unit_price"].iloc[0]),
            "category": result["category"].iloc[0],
        }

        logger.debug(f"Preço de '{item_name}': ${pricing['unit_price']}")
        return pricing

    except Exception as e:
        logger.error(f"Erro ao buscar preço de '{item_name}': {e}")
        return {"error": str(e)}


# ============================================================================
# TOOL 3: CALCULATE BULK DISCOUNT
# ============================================================================


def calculate_bulk_discount_tool(
    ctx: RunContext[DatabaseContext], base_price: float, order_size: str
) -> dict[str, any]:
    """
    Aplica desconto bulk baseado no tamanho do pedido.

    Regras (baseadas em análise do histórico):
    - small: 5% desconto
    - medium: 10% desconto
    - large: 15% desconto

    Args:
        ctx: Contexto (não usado, mas necessário para pydantic-ai)
        base_price: Preço base total
        order_size: 'small', 'medium', ou 'large'

    Returns:
        Dict com breakdown completo do desconto

    Example:
        >>> discount = calculate_bulk_discount_tool(ctx, 100.0, "medium")
        >>> print(discount)
        {
            "base_price": 100.0,
            "order_size": "medium",
            "discount_rate": 0.10,
            "discount_amount": 10.0,
            "final_price": 90.0,
            "rounded_price": 90.0
        }
    """
    logger.info(f"[TOOL] calculate_bulk_discount: base=${base_price:.2f}, size={order_size}")

    try:
        # Normalizar order_size
        order_size_lower = order_size.lower().strip()

        # Buscar taxa de desconto
        discount_rate = BusinessRules.BULK_DISCOUNTS.get(order_size_lower, 0.05)

        # Calcular desconto
        discount_amount = base_price * discount_rate
        final_price = base_price - discount_amount

        # Arredondar para valor "amigável" (múltiplo de 5)
        rounded_price = round(final_price / 5) * 5

        result = {
            "base_price": round(base_price, 2),
            "order_size": order_size_lower,
            "discount_rate": discount_rate,
            "discount_amount": round(discount_amount, 2),
            "final_price": round(final_price, 2),
            "rounded_price": round(rounded_price, 2),
        }

        logger.debug(
            f"Desconto calculado: ${base_price:.2f} → "
            f"${rounded_price:.2f} ({discount_rate * 100:.0f}% off)"
        )

        return result

    except Exception as e:
        logger.error(f"Erro ao calcular desconto: {e}")
        return {"error": str(e), "base_price": base_price, "final_price": base_price}


# ============================================================================
# TOOL 4: VALIDATE QUOTE AVAILABILITY
# ============================================================================


def validate_quote_availability_tool(
    ctx: RunContext[DatabaseContext], items: dict[str, int]
) -> dict[str, any]:
    """
    Valida se há estoque disponível para todos os itens da cotação.

    Verifica ANTES de gerar a cotação se podemos cumprir o pedido.

    Args:
        ctx: Contexto com db_engine e current_date
        items: Dict[item_name, quantidade_solicitada]
               Ex: {"A4 paper": 500, "Cardstock": 300}

    Returns:
        Dict com status de disponibilidade:
        {
            "all_available": bool,
            "items_status": {
                "A4 paper": {
                    "requested": 500,
                    "available": 650,
                    "sufficient": True
                },
                "Cardstock": {
                    "requested": 300,
                    "available": 150,
                    "sufficient": False
                }
            },
            "unavailable_items": ["Cardstock"]
        }
    """
    logger.info(f"[TOOL] validate_quote_availability: {len(items)} itens")

    try:
        items_status = {}
        unavailable_items = []
        all_available = True

        for item_name, requested_qty in items.items():
            # Buscar estoque atual
            stock_df = get_stock_level(
                item_name=item_name, as_of_date=ctx.deps.current_date, engine=ctx.deps.db_engine
            )

            if stock_df.empty:
                available_qty = 0
            else:
                available_qty = int(stock_df["current_stock"].iloc[0])

            is_sufficient = available_qty >= requested_qty

            if not is_sufficient:
                all_available = False
                unavailable_items.append(item_name)

            items_status[item_name] = {
                "requested": requested_qty,
                "available": available_qty,
                "sufficient": is_sufficient,
            }

            logger.debug(
                f"  {item_name}: requested={requested_qty}, "
                f"available={available_qty}, OK={is_sufficient}"
            )

        result = {
            "all_available": all_available,
            "items_status": items_status,
            "unavailable_items": unavailable_items,
        }

        if not all_available:
            logger.warning(f"Itens insuficientes: {unavailable_items}")
        else:
            logger.info("Todos os itens estão disponíveis")

        return result

    except Exception as e:
        logger.error(f"Erro ao validar disponibilidade: {e}")
        return {"error": str(e), "all_available": False}


# ============================================================================
# TOOL 5: CALCULATE TOTAL PRICE
# ============================================================================


def calculate_total_price_tool(
    ctx: RunContext[DatabaseContext], items: dict[str, int]
) -> dict[str, any]:
    """
    Calcula preço base total para uma lista de itens.

    Args:
        ctx: Contexto com db_engine
        items: Dict[item_name, quantidade]
               Ex: {"A4 paper": 500, "Cardstock": 300}

    Returns:
        Dict com breakdown de preços:
        {
            "items_breakdown": [
                {
                    "item_name": "A4 paper",
                    "quantity": 500,
                    "unit_price": 0.05,
                    "subtotal": 25.0
                },
                ...
            ],
            "total_base_price": 70.0,
            "total_items": 2,
            "total_units": 800
        }
    """
    logger.info(f"[TOOL] calculate_total_price: {len(items)} itens")

    try:
        items_breakdown = []
        total_base_price = 0.0
        total_units = 0

        for item_name, quantity in items.items():
            # Buscar preço unitário
            pricing = get_item_pricing_tool(ctx, item_name)

            if "error" in pricing:
                logger.warning(f"Item '{item_name}' não encontrado no catálogo")
                continue

            unit_price = pricing["unit_price"]
            subtotal = quantity * unit_price

            items_breakdown.append(
                {
                    "item_name": item_name,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "subtotal": round(subtotal, 2),
                }
            )

            total_base_price += subtotal
            total_units += quantity

            logger.debug(f"  {item_name}: {quantity} × ${unit_price} = ${subtotal:.2f}")

        result = {
            "items_breakdown": items_breakdown,
            "total_base_price": round(total_base_price, 2),
            "total_items": len(items_breakdown),
            "total_units": total_units,
        }

        logger.info(f"Preço base total: ${total_base_price:.2f}")
        return result

    except Exception as e:
        logger.error(f"Erro ao calcular preço total: {e}")
        return {"error": str(e), "total_base_price": 0.0}


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "search_similar_quotes_tool",
    "get_item_pricing_tool",
    "calculate_bulk_discount_tool",
    "validate_quote_availability_tool",
    "calculate_total_price_tool",
]
