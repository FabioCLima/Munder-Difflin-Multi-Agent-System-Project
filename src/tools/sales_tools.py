"""
Tools para Sales Agent e Reordering Agent.
Fornece funções para processar vendas e gerenciar reordenação automática.
"""

from datetime import datetime, timedelta

import pandas as pd
from pydantic_ai import RunContext

from src.config import BusinessRules
from src.database import (
    DatabaseContext,
    create_transaction,
    generate_financial_report,
    get_cash_balance,
    get_stock_level,
    get_supplier_delivery_date,
)
from src.utils.logging_config import logger

# ============================================================================
# TOOL 1: PROCESS SALE
# ============================================================================


def process_sale_tool(
    ctx: RunContext[DatabaseContext], items: dict[str, dict[str, any]]
) -> dict[str, any]:
    """
    Processa uma venda completa (múltiplos itens).

    Esta é a tool CRÍTICA do Sales Agent!

    Args:
        ctx: Contexto com db_engine e current_date
        items: Dict de itens para vender:
               {
                   "A4 paper": {"quantity": 500, "unit_price": 0.05},
                   "Cardstock": {"quantity": 300, "unit_price": 0.15}
               }

    Returns:
        Dict com resultado da venda:
        {
            "success": bool,
            "transactions": [lista de IDs criados],
            "total_revenue": float,
            "items_sold": int,
            "date": str,
            "new_cash_balance": float
        }

    Example:
        >>> items = {
        ...     "A4 paper": {"quantity": 500, "unit_price": 0.05},
        ...     "Cardstock": {"quantity": 300, "unit_price": 0.15}
        ... }
        >>> result = process_sale_tool(ctx, items)
        >>> print(result)
        {
            "success": True,
            "total_revenue": 70.0,
            "items_sold": 2,
            "transactions": [123, 124]
        }
    """
    logger.info(f"[TOOL] process_sale: {len(items)} itens em {ctx.deps.current_date}")

    try:
        # Fase 1: Validar disponibilidade de TODOS os itens
        logger.debug("Fase 1: Validando disponibilidade...")
        for item_name, details in items.items():
            quantity = details["quantity"]

            stock_df = get_stock_level(
                item_name=item_name, as_of_date=ctx.deps.current_date, engine=ctx.deps.db_engine
            )

            if stock_df.empty:
                available = 0
            else:
                available = int(stock_df["current_stock"].iloc[0])

            if available < quantity:
                error_msg = (
                    f"Insufficient stock for '{item_name}': "
                    f"requested {quantity}, available {available}"
                )
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "item_name": item_name,
                    "requested": quantity,
                    "available": available,
                }

        # Fase 2: Processar vendas
        logger.debug("Fase 2: Processando transações...")
        transactions = []
        total_revenue = 0.0

        for item_name, details in items.items():
            quantity = details["quantity"]
            unit_price = details["unit_price"]
            total_price = quantity * unit_price

            # Criar transação de venda
            tx_id = create_transaction(
                item_name=item_name,
                transaction_type="sales",
                quantity=quantity,
                price=total_price,
                date=ctx.deps.current_date,
                engine=ctx.deps.db_engine,
            )

            transactions.append(
                {
                    "transaction_id": tx_id,
                    "item_name": item_name,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_price": round(total_price, 2),
                }
            )

            total_revenue += total_price

            logger.debug(f"  Venda registrada: {item_name} × {quantity} = ${total_price:.2f}")

        # Fase 3: Calcular novo saldo de caixa
        new_cash_balance = get_cash_balance(
            as_of_date=ctx.deps.current_date, engine=ctx.deps.db_engine
        )

        result = {
            "success": True,
            "transactions": transactions,
            "total_revenue": round(total_revenue, 2),
            "items_sold": len(items),
            "date": ctx.deps.current_date,
            "new_cash_balance": round(new_cash_balance, 2),
        }

        logger.success(
            f"Venda processada com sucesso: ${total_revenue:.2f} | "
            f"Novo saldo: ${new_cash_balance:.2f}"
        )

        return result

    except Exception as e:
        logger.error(f"Erro ao processar venda: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# TOOL 2: GET FINANCIAL STATUS
# ============================================================================


def get_financial_status_tool(
    ctx: RunContext[DatabaseContext], detailed: bool = False
) -> dict[str, any]:
    """
    Retorna status financeiro atual da empresa.

    Args:
        ctx: Contexto com db_engine e current_date
        detailed: Se True, retorna relatório completo

    Returns:
        Dict com status financeiro

    Example (basic):
        >>> status = get_financial_status_tool(ctx, detailed=False)
        >>> print(status)
        {"cash_balance": 50000.0, "date": "2025-04-01"}

    Example (detailed):
        >>> status = get_financial_status_tool(ctx, detailed=True)
        >>> print(status.keys())
        dict_keys(['as_of_date', 'cash_balance', 'inventory_value',
                   'total_assets', 'inventory_summary', 'top_selling_products'])
    """
    logger.info(f"[TOOL] get_financial_status (detailed={detailed}) em {ctx.deps.current_date}")

    try:
        if detailed:
            # Relatório completo
            report = generate_financial_report(
                as_of_date=ctx.deps.current_date, engine=ctx.deps.db_engine
            )
            logger.debug("Relatório detalhado gerado")
            return report
        else:
            # Status rápido (apenas cash)
            cash = get_cash_balance(as_of_date=ctx.deps.current_date, engine=ctx.deps.db_engine)
            return {"cash_balance": round(cash, 2), "date": ctx.deps.current_date}

    except Exception as e:
        logger.error(f"Erro ao buscar status financeiro: {e}")
        return {"error": str(e)}


# ============================================================================
# TOOL 3: CALCULATE CUSTOMER DELIVERY DATE
# ============================================================================


def calculate_customer_delivery_tool(ctx: RunContext[DatabaseContext]) -> str:
    """
    Calcula data estimada de entrega ao CLIENTE.

    IMPORTANTE: Diferente de get_supplier_delivery_date()!
    Esta função é para entrega ao cliente final, não do fornecedor.

    Regra: current_date + CUSTOMER_DELIVERY_DAYS (padrão: 4 dias úteis)

    Args:
        ctx: Contexto com current_date

    Returns:
        Data de entrega no formato ISO (YYYY-MM-DD)

    Example:
        >>> delivery = calculate_customer_delivery_tool(ctx)
        >>> print(delivery)
        "2025-04-05"  # Se current_date = 2025-04-01
    """
    logger.info(f"[TOOL] calculate_customer_delivery em {ctx.deps.current_date}")

    try:
        order_date = datetime.fromisoformat(ctx.deps.current_date)
        delivery_date = order_date + timedelta(days=BusinessRules.CUSTOMER_DELIVERY_DAYS)
        delivery_str = delivery_date.strftime("%Y-%m-%d")

        logger.debug(f"Delivery date: {delivery_str}")
        return delivery_str

    except Exception as e:
        logger.error(f"Erro ao calcular delivery date: {e}")
        # Fallback
        return ctx.deps.current_date


# ============================================================================
# TOOL 4: PLACE STOCK ORDER (Reordering)
# ============================================================================


def place_stock_order_tool(
    ctx: RunContext[DatabaseContext], item_name: str, quantity: int
) -> dict[str, any]:
    """
    Faz pedido de reposição de estoque ao fornecedor.

    Esta tool é usada pelo Reordering Agent!

    Validações:
    1. Verificar se há cash suficiente
    2. Calcular custo total
    3. Criar transação de stock_orders
    4. Calcular ETA de entrega

    Args:
        ctx: Contexto com db_engine e current_date
        item_name: Nome do item a reordenar
        quantity: Quantidade a comprar

    Returns:
        Dict com resultado do pedido:
        {
            "success": bool,
            "transaction_id": int,
            "item_name": str,
            "quantity": int,
            "cost": float,
            "order_date": str,
            "estimated_delivery": str,
            "remaining_cash": float
        }

    Example:
        >>> result = place_stock_order_tool(ctx, "A4 paper", 500)
        >>> print(result)
        {
            "success": True,
            "cost": 25.0,
            "estimated_delivery": "2025-04-05"
        }
    """
    logger.info(f"[TOOL] place_stock_order: '{item_name}' × {quantity} em {ctx.deps.current_date}")

    try:
        # Fase 1: Buscar unit_price
        query = "SELECT unit_price FROM inventory WHERE item_name = ?"
        result = pd.read_sql(query, ctx.deps.db_engine, params=(item_name,))

        if result.empty:
            error_msg = f"Item '{item_name}' not found in inventory catalog"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        unit_price = float(result["unit_price"].iloc[0])
        total_cost = quantity * unit_price

        logger.debug(f"Custo calculado: {quantity} × ${unit_price} = ${total_cost:.2f}")

        # Fase 2: Verificar cash disponível
        current_cash = get_cash_balance(as_of_date=ctx.deps.current_date, engine=ctx.deps.db_engine)

        if current_cash < total_cost:
            error_msg = (
                f"Insufficient cash: required ${total_cost:.2f}, available ${current_cash:.2f}"
            )
            logger.warning(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "required": round(total_cost, 2),
                "available": round(current_cash, 2),
                "shortage": round(total_cost - current_cash, 2),
            }

        # Fase 3: Criar transação de compra
        tx_id = create_transaction(
            item_name=item_name,
            transaction_type="stock_orders",
            quantity=quantity,
            price=total_cost,
            date=ctx.deps.current_date,
            engine=ctx.deps.db_engine,
        )

        # Fase 4: Calcular ETA de entrega do fornecedor
        eta = get_supplier_delivery_date(ctx.deps.current_date, quantity)

        # Fase 5: Calcular novo saldo
        remaining_cash = current_cash - total_cost

        result = {
            "success": True,
            "transaction_id": tx_id,
            "item_name": item_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "cost": round(total_cost, 2),
            "order_date": ctx.deps.current_date,
            "estimated_delivery": eta,
            "remaining_cash": round(remaining_cash, 2),
        }

        logger.success(
            f"Pedido de reposição criado: {item_name} × {quantity} | "
            f"Custo: ${total_cost:.2f} | ETA: {eta}"
        )

        return result

    except Exception as e:
        logger.error(f"Erro ao criar pedido de reposição: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# TOOL 5: CALCULATE REORDER QUANTITY
# ============================================================================


def calculate_reorder_quantity_tool(
    ctx: RunContext[DatabaseContext], item_name: str, current_stock: int
) -> int:
    """
    Calcula quantidade ideal de reposição.

    Lógica:
    1. Buscar min_stock_level do item
    2. Optimal stock = min_stock_level × REORDER_MULTIPLIER (padrão 2)
    3. Reorder qty = optimal - current_stock

    Args:
        ctx: Contexto com db_engine
        item_name: Nome do item
        current_stock: Estoque atual

    Returns:
        Quantidade recomendada para reordenar

    Example:
        >>> qty = calculate_reorder_quantity_tool(ctx, "A4 paper", 45)
        >>> print(qty)
        105  # Se min_level=50, optimal=100, current=45 → reorder=55
    """
    logger.info(f"[TOOL] calculate_reorder_quantity: '{item_name}'")

    try:
        query = "SELECT min_stock_level FROM inventory WHERE item_name = ?"
        result = pd.read_sql(query, ctx.deps.db_engine, params=(item_name,))

        if result.empty:
            logger.error(f"Item '{item_name}' não encontrado")
            return 0

        min_level = int(result["min_stock_level"].iloc[0])
        optimal_stock = min_level * BusinessRules.REORDER_MULTIPLIER
        reorder_qty = max(optimal_stock - current_stock, 0)

        logger.debug(
            f"Reorder calculation: min={min_level}, optimal={optimal_stock}, "
            f"current={current_stock}, reorder={reorder_qty}"
        )

        return reorder_qty

    except Exception as e:
        logger.error(f"Erro ao calcular reorder quantity: {e}")
        return 0


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "process_sale_tool",
    "get_financial_status_tool",
    "calculate_customer_delivery_tool",
    "place_stock_order_tool",
    "calculate_reorder_quantity_tool",
]
