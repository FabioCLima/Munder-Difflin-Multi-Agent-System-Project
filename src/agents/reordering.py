"""
Reordering Agent - Automated stock replenishment system
Monitors inventory levels and places supplier orders when stock is low
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from loguru import logger
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

# ============================================================================
# MODELS
# ============================================================================


class ReorderItem(BaseModel):
    """Item que precisa ser reordenado"""

    item_name: str
    current_stock: int
    min_stock_level: int
    deficit: int  # Quanto falta
    reorder_quantity: int  # Quanto pedir
    unit_price: float
    total_cost: float


class SupplierOrder(BaseModel):
    """Ordem de compra ao fornecedor"""

    order_id: str
    item_name: str
    quantity: int
    unit_price: float
    total_cost: float
    expected_delivery: str
    status: str

    def to_formatted_string(self) -> str:
        return f"""
📦 **Supplier Order #{self.order_id}**

Product: {self.item_name}
Quantity: {self.quantity:,} units
Unit Cost: ${self.unit_price:.2f}
**Total Cost: ${self.total_cost:,.2f}**

Expected Delivery: {self.expected_delivery}
Status: {self.status.upper()}
"""


class ReorderingDependencies(BaseModel):
    """Dependências para o Reordering Agent"""

    db_path: str = "munder_difflin.db"
    auto_approve: bool = True  # Auto-aprovar pedidos
    current_date: str = "2025-01-15"
    db_engine: Any = None
    safety_stock_multiplier: float = 1.5  # 50% acima do mínimo


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

REORDERING_SYSTEM_PROMPT = """You are the Reordering Agent for Munder Difflin Paper Company.

Your responsibilities:
1. Monitor inventory levels continuously
2. Identify products below minimum stock level
3. Calculate optimal reorder quantities
4. Place supplier orders automatically
5. Track delivery timelines
6. Update inventory upon delivery

Reordering Logic:
- Trigger: When current_stock < min_stock_level
- Reorder Quantity: (min_stock_level × 1.5) - current_stock
- Delivery Time: 5-7 business days (simulated)
- Auto-approval: Orders are placed automatically unless flagged

Guidelines:
- Always check for low stock items first
- Calculate reorder quantities to restore safety stock
- Consider lead times and demand patterns
- Log all reorder activities
- Update inventory when supplier delivers
- Be proactive but cost-conscious

This is a background process that runs periodically or when triggered by Sales Agent.
"""


# ============================================================================
# REORDERING AGENT
# ============================================================================

# Importar configuração de teste se estivermos em modo de teste
import sys

if "pytest" in sys.modules:
    from src.test_config import create_test_agent

    reordering_agent = create_test_agent(REORDERING_SYSTEM_PROMPT, ReorderingDependencies)
else:
    reordering_agent = Agent(
        model="openai:gpt-4o-mini",
        system_prompt=REORDERING_SYSTEM_PROMPT,
        deps_type=ReorderingDependencies,
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Cria conexão com o banco de dados"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def generate_order_id() -> str:
    """Gera ID único para ordem de compra"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"PO{timestamp}"


def calculate_delivery_date(days: int = 6) -> str:
    """Calcula data estimada de entrega"""
    delivery = datetime.now() + timedelta(days=days)
    return delivery.strftime("%Y-%m-%d")


# ============================================================================
# TOOL 1: Check Low Stock Items
# ============================================================================


@reordering_agent.tool
async def check_low_stock_items(ctx: RunContext[ReorderingDependencies]) -> str:
    """
    Identify all products that are below minimum stock level.

    Returns:
        List of items needing reorder with recommendations
    """
    logger.info("🔍 Checking for low stock items...")

    try:
        conn = get_db_connection(ctx.deps.db_path)

        query = """
            SELECT 
                item_name,
                current_stock,
                min_stock_level,
                unit_price
            FROM inventory
            WHERE current_stock < min_stock_level
            ORDER BY (min_stock_level - current_stock) DESC
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            logger.success("✅ All items adequately stocked")
            return (
                "✅ All inventory items are at or above minimum stock levels. No reordering needed."
            )

        # Calcular reorder quantities
        reorder_items = []
        total_cost = 0.0

        for _, row in df.iterrows():
            deficit = row["min_stock_level"] - row["current_stock"]
            # Reorder para 50% acima do mínimo
            reorder_qty = int(
                (row["min_stock_level"] * ctx.deps.safety_stock_multiplier) - row["current_stock"]
            )
            item_cost = reorder_qty * row["unit_price"]
            total_cost += item_cost

            reorder_items.append(
                ReorderItem(
                    item_name=row["item_name"],
                    current_stock=row["current_stock"],
                    min_stock_level=row["min_stock_level"],
                    deficit=deficit,
                    reorder_quantity=reorder_qty,
                    unit_price=row["unit_price"],
                    total_cost=item_cost,
                )
            )

        # Formatar relatório
        lines = [f"⚠️ **{len(reorder_items)} Product(s) Need Reordering**\n"]

        for item in reorder_items:
            lines.append(
                f"📦 **{item.item_name}**\n"
                f"   • Current: {item.current_stock} units (Minimum: {item.min_stock_level})\n"
                f"   • Deficit: {item.deficit} units\n"
                f"   • Recommended Order: {item.reorder_quantity} units\n"
                f"   • Cost: ${item.total_cost:,.2f}\n"
            )

        lines.append(f"\n**Total Reorder Cost: ${total_cost:,.2f}**")

        logger.warning(f"⚠️ {len(reorder_items)} items need reordering (${total_cost:,.2f})")
        return "\n".join(lines)

    except Exception as e:
        logger.error(f"❌ Error checking low stock: {e}")
        return f"Error checking low stock: {str(e)}"


# ============================================================================
# TOOL 2: Place Supplier Order
# ============================================================================


@reordering_agent.tool
async def place_supplier_order(
    ctx: RunContext[ReorderingDependencies], item_name: str, quantity: int
) -> str:
    """
    Place an order with supplier to restock inventory.
    Creates a purchase transaction and schedules delivery.

    Args:
        ctx: Context with dependencies
        item_name: Product to reorder
        quantity: Quantity to order

    Returns:
        Order confirmation
    """
    logger.info(f"📦 Placing supplier order: {item_name} x{quantity}")

    conn = None
    try:
        conn = get_db_connection(ctx.deps.db_path)
        cursor = conn.cursor()

        # 1. Validar produto
        cursor.execute(
            "SELECT item_name, unit_price, current_stock FROM inventory WHERE LOWER(item_name) = LOWER(?)",
            (item_name,),
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return f"❌ Product '{item_name}' not found."

        actual_name = row["item_name"]
        unit_price = row["unit_price"]
        current_stock = row["current_stock"]
        total_cost = unit_price * quantity

        # 2. Criar ordem de compra
        order_id = generate_order_id()
        delivery_date = calculate_delivery_date()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 3. Registrar transação
        cursor.execute(
            """
            INSERT INTO transactions (
                id, transaction_type, item_name,
                units, price, transaction_date
            ) VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                order_id,
                "stock_orders",
                actual_name,
                quantity,
                total_cost,
                created_at,
            ),
        )

        # 4. Atualizar inventário (simular entrega imediata)
        # Em produção real, isso seria feito após a entrega
        new_stock = current_stock + quantity
        cursor.execute(
            "UPDATE inventory SET current_stock = ? WHERE item_name = ?", (new_stock, actual_name)
        )

        conn.commit()
        conn.close()

        # 5. Criar resposta
        order = SupplierOrder(
            order_id=order_id,
            item_name=actual_name,
            quantity=quantity,
            unit_price=unit_price,
            total_cost=total_cost,
            expected_delivery=delivery_date,
            status="completed",
        )

        response = f"""
✅ **SUPPLIER ORDER PLACED**

{order.to_formatted_string()}

Inventory Updated:
- Before: {current_stock:,} units
- After: {new_stock:,} units (+{quantity:,})

💰 Total Cost: ${total_cost:,.2f}

Note: In production, this would be a pending order awaiting delivery.
For simulation purposes, inventory is updated immediately.
"""

        logger.success(f"✅ Order placed: {order_id} - {quantity} units of {actual_name}")
        return response.strip()

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        logger.error(f"❌ Error placing order: {e}")
        return f"Error placing supplier order: {str(e)}"


# ============================================================================
# TOOL 3: Auto-Reorder All Low Stock
# ============================================================================


@reordering_agent.tool
async def auto_reorder_all_low_stock(ctx: RunContext[ReorderingDependencies]) -> str:
    """
    Automatically reorder ALL products that are below minimum stock.
    This is the main tool for automated replenishment.

    Returns:
        Summary of all orders placed
    """
    logger.info("🤖 Starting automatic reordering process...")

    try:
        conn = get_db_connection(ctx.deps.db_path)

        # Buscar todos os items baixos
        query = """
            SELECT 
                item_name,
                current_stock,
                min_stock_level,
                unit_price
            FROM inventory
            WHERE current_stock < min_stock_level
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            return "✅ No reordering needed. All inventory levels are adequate."

        # Processar cada item
        orders_placed = []
        total_cost = 0.0

        for _, row in df.iterrows():
            reorder_qty = int(
                (row["min_stock_level"] * ctx.deps.safety_stock_multiplier) - row["current_stock"]
            )

            # Chamar place_supplier_order para cada item
            await place_supplier_order(ctx, item_name=row["item_name"], quantity=reorder_qty)

            item_cost = reorder_qty * row["unit_price"]
            total_cost += item_cost

            orders_placed.append(
                {"product": row["item_name"], "quantity": reorder_qty, "cost": item_cost}
            )

            logger.info(f"✅ Reordered: {row['item_name']} x{reorder_qty}")

        # Resumo
        summary = [
            "🤖 **Automatic Reordering Complete**\n",
            f"Orders Placed: {len(orders_placed)}\n",
        ]

        for order in orders_placed:
            summary.append(
                f"✅ {order['product']}: {order['quantity']:,} units (${order['cost']:,.2f})"
            )

        summary.append(f"\n**Total Investment: ${total_cost:,.2f}**")
        summary.append("\n✅ All inventory levels restored to safety stock.")

        logger.success(f"🤖 Auto-reorder complete: {len(orders_placed)} orders, ${total_cost:,.2f}")
        return "\n".join(summary)

    except Exception as e:
        logger.error(f"❌ Error in auto-reorder: {e}")
        return f"Error in automatic reordering: {str(e)}"


# ============================================================================
# TOOL 4: Get Supplier Delivery Schedule
# ============================================================================


@reordering_agent.tool
async def get_supplier_delivery_schedule(ctx: RunContext[ReorderingDependencies]) -> str:
    """
    Get schedule of pending supplier deliveries.

    Returns:
        List of pending orders and delivery dates
    """
    logger.info("📅 Fetching supplier delivery schedule...")

    try:
        conn = get_db_connection(ctx.deps.db_path)

        query = """
            SELECT 
                id as order_id,
                item_name,
                quantity,
                total_amount,
                created_at,
                status
            FROM transactions
            WHERE transaction_type = 'stock_orders'
            ORDER BY created_at DESC
            LIMIT 20
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            return "📅 No supplier orders found."

        lines = [f"📅 **Supplier Order History** (last {len(df)} orders):\n"]

        for _, row in df.iterrows():
            status_emoji = "✅" if row["status"] == "completed" else "⏳"

            lines.append(
                f"{status_emoji} **Order #{row['order_id']}**\n"
                f"   • Product: {row['item_name']}\n"
                f"   • Quantity: {row['quantity']:,} units\n"
                f"   • Cost: ${row['total_amount']:,.2f}\n"
                f"   • Date: {row['created_at']}\n"
                f"   • Status: {row['status'].upper()}\n"
            )

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"❌ Error fetching schedule: {e}")
        return f"Error retrieving delivery schedule: {str(e)}"


# ============================================================================
# CONVENIENCE FUNCTION - Trigger Reorder Check
# ============================================================================


async def trigger_reorder_check(
    auto_approve: bool = True, db_path: str = "munder_difflin.db"
) -> str:
    """
    Trigger the reordering process.
    This is called by Sales Agent when stock drops below minimum.

    Args:
        auto_approve: Whether to automatically place orders
        db_path: Database path

    Returns:
        Reordering summary
    """
    logger.info("🔔 Reorder check triggered...")

    try:
        if auto_approve:
            # Auto-reorder tudo
            result = await reordering_agent.run(
                "Check low stock and automatically reorder all items below minimum",
                deps=ReorderingDependencies(db_path=db_path, auto_approve=True),
            )
        else:
            # Apenas reportar
            result = await reordering_agent.run(
                "Check which items are low on stock and need reordering",
                deps=ReorderingDependencies(db_path=db_path, auto_approve=False),
            )

        return result.output

    except Exception as e:
        logger.error(f"❌ Error in reorder check: {e}")
        return f"Error: {str(e)}"


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def test_reordering_agent():
        """Test the reordering agent"""

        print("=" * 60)
        print("TEST 1: Check Low Stock Items")
        print("=" * 60)

        result = await reordering_agent.run(
            "Check which products need reordering", deps=ReorderingDependencies()
        )
        print(result.output)

        print("\n" + "=" * 60)
        print("TEST 2: Trigger Auto-Reorder")
        print("=" * 60)

        response = await trigger_reorder_check(auto_approve=True)
        print(response)

        print("\n" + "=" * 60)
        print("TEST 3: Delivery Schedule")
        print("=" * 60)

        result = await reordering_agent.run(
            "Show me the supplier delivery schedule", deps=ReorderingDependencies()
        )
        print(result.output)

    asyncio.run(test_reordering_agent())
