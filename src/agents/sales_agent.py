"""
Sales Agent - Processes purchase orders, creates transactions, and manages sales
Coordinates with Inventory and Quoting agents to fulfill customer orders
"""

import sqlite3
from datetime import datetime
from typing import Any, Literal

import pandas as pd
from loguru import logger
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

# ============================================================================
# MODELS - Estruturas de dados
# ============================================================================


class OrderRequest(BaseModel):
    """Modelo para requisição de pedido"""

    item_name: str
    quantity: int = Field(gt=0)
    quoted_price: float | None = None
    quote_id: str | None = None


class Transaction(BaseModel):
    """Modelo para transação"""

    id: str
    transaction_type: Literal["sales", "stock_orders"]
    item_name: str
    quantity: int
    unit_price: float
    price: float
    customer_id: str | None = None
    transaction_date: str
    status: Literal["completed", "pending", "failed"]

    def to_formatted_string(self) -> str:
        """Retorna transação formatada"""
        type_emoji = "💰" if self.transaction_type == "sales" else "📦"
        status_emoji = "✅" if self.status == "completed" else "⏳"

        lines = [
            f"{type_emoji} **Transaction #{self.id}** {status_emoji}",
            "",
            f"Type: {self.transaction_type.upper()}",
            f"Product: {self.item_name}",
            f"Quantity: {self.quantity:,} units",
            f"Unit Price: ${self.unit_price:.2f}",
            f"**Total Amount: ${self.price:,.2f}**",
            "",
            f"Date: {self.transaction_date}",
            f"Status: {self.status.upper()}",
        ]

        if self.customer_id:
            lines.insert(-2, f"Customer: {self.customer_id}")

        return "\n".join(lines)


class SalesDependencies(BaseModel):
    """Dependências para o Sales Agent"""

    db_path: str = "munder_difflin.db"
    customer_id: str | None = None
    current_date: str = "2025-01-15"
    db_engine: Any = None


# ============================================================================
# SYSTEM PROMPT - O "cérebro" do Sales Agent
# ============================================================================

SALES_SYSTEM_PROMPT = """You are the Sales Agent for Munder Difflin Paper Company.

Your responsibilities:
1. Process customer purchase orders
2. Create sales transactions in the database
3. Update inventory levels after successful sales
4. Validate order feasibility (stock availability, pricing)
5. Generate sales reports and financial summaries
6. Trigger reordering process when stock becomes low

Order Processing Flow:
1. Validate product and quantity
2. Check inventory availability (coordinate with Inventory Agent)
3. Verify pricing (coordinate with Quoting Agent if needed)
4. Create transaction record
5. Update inventory (deduct stock)
6. Check if reordering is needed
7. Confirm order to customer

Guidelines:
- Always validate stock availability before processing
- Ensure quoted prices match current pricing
- Provide clear order confirmations with transaction IDs
- Alert about any stock issues or delays
- Be professional and reassuring
- Trigger reordering if stock drops below minimum level

When an order cannot be fulfilled:
- Explain the reason clearly (out of stock, insufficient quantity)
- Suggest alternatives or partial fulfillment
- Offer to place a backorder

Use the provided tools to process orders safely and accurately.
"""


# ============================================================================
# SALES AGENT
# ============================================================================

# Importar configuração de teste se estivermos em modo de teste
import sys

if "pytest" in sys.modules:
    from src.test_config import create_test_agent

    sales_agent = create_test_agent(SALES_SYSTEM_PROMPT, SalesDependencies)
else:
    sales_agent = Agent(
        model="openai:gpt-4o-mini",
        system_prompt=SALES_SYSTEM_PROMPT,
        deps_type=SalesDependencies,
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Cria conexão com o banco de dados"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def generate_id(transaction_type: str) -> str:
    """Gera ID único para transação"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    prefix = "S" if transaction_type == "sales" else "P"
    return f"{prefix}{timestamp}"


# ============================================================================
# TOOL 1: Create Sales Transaction
# ============================================================================


@sales_agent.tool
async def create_sales_transaction(
    ctx: RunContext[SalesDependencies],
    item_name: str,
    quantity: int,
    unit_price: float,
    quote_id: str | None = None,
) -> str:
    """
    Create a sales transaction and update inventory.
    This is the main tool for processing customer orders.

    Args:
        ctx: Context with dependencies
        item_name: Product being purchased
        quantity: Quantity to purchase
        unit_price: Price per unit (from quote)
        quote_id: Optional reference to quote

    Returns:
        Transaction confirmation or error message
    """
    logger.info(f"💰 Processing sales transaction: {item_name} x{quantity} @ ${unit_price}")

    conn = None
    try:
        conn = get_db_connection(ctx.deps.db_path)
        cursor = conn.cursor()

        # 1. Validar produto e estoque
        cursor.execute(
            "SELECT item_name, current_stock, unit_price FROM inventory WHERE LOWER(item_name) = LOWER(?)",
            (item_name,),
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            logger.warning(f"⚠️ Product not found: {item_name}")
            return f"❌ Product '{item_name}' not found in inventory."

        actual_name = row["item_name"]
        current_stock = row["current_stock"]
        catalog_price = row["unit_price"]

        # 2. Verificar disponibilidade
        if current_stock < quantity:
            conn.close()
            logger.warning(f"⚠️ Insufficient stock: {current_stock} < {quantity}")
            return f"""
❌ **Order Cannot Be Fulfilled**

Product: {actual_name}
Requested: {quantity:,} units
Available: {current_stock:,} units

We don't have enough stock to fulfill this order. 

Options:
- Reduce quantity to {current_stock:,} units
- Place a backorder (delivery in 5-7 business days)
- Choose a different product
"""

        if current_stock == 0:
            conn.close()
            return f"❌ {actual_name} is currently out of stock."

        # 3. Validar preço (warning se diferente do catálogo)
        price_warning = ""
        if abs(unit_price - catalog_price) > 0.01:
            price_diff_pct = ((unit_price - catalog_price) / catalog_price) * 100
            logger.info(f"💰 Price variance: {price_diff_pct:.1f}% (quoted vs catalog)")
            if unit_price > catalog_price:
                price_warning = f"\n⚠️ Note: Quoted price (${unit_price:.2f}) is higher than current catalog price (${catalog_price:.2f})"

        # 4. Criar transação
        id = generate_id("sales")
        price = unit_price * quantity
        transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            INSERT INTO transactions (
                id, transaction_type, item_name,
                units, price, transaction_date
            ) VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                id,
                "sales",
                actual_name,
                quantity,
                price,
                transaction_date,
            ),
        )

        # 5. Atualizar inventário (deduzir estoque)
        new_stock = current_stock - quantity
        cursor.execute(
            "UPDATE inventory SET current_stock = ? WHERE item_name = ?", (new_stock, actual_name)
        )

        # 6. Atualizar quote se fornecido
        if quote_id:
            cursor.execute("UPDATE quotes SET status = 'accepted' WHERE quote_id = ?", (quote_id,))

        conn.commit()

        # 7. Verificar se precisa reordenar
        cursor.execute(
            "SELECT min_stock_level FROM inventory WHERE item_name = ?", (actual_name,)
        )
        min_stock = cursor.fetchone()["min_stock_level"]

        reorder_alert = ""
        if new_stock < min_stock:
            logger.warning(f"⚠️ Stock below minimum: {new_stock} < {min_stock}")
            reorder_alert = f"\n\n🔔 **Auto-reordering triggered**: Stock dropped to {new_stock} units (minimum: {min_stock})"

        conn.close()

        # 8. Criar resposta
        transaction = Transaction(
            id=id,
            transaction_type="sales",
            item_name=actual_name,
            quantity=quantity,
            unit_price=unit_price,
            price=price,
            customer_id=ctx.deps.customer_id,
            transaction_date=transaction_date,
            status="completed",
        )

        response = f"""
✅ **ORDER CONFIRMED**

{transaction.to_formatted_string()}

Updated Stock Level: {new_stock:,} units (was {current_stock:,})
{price_warning}
{reorder_alert}

Thank you for your purchase! Your order will be processed immediately.
"""

        logger.success(f"✅ Transaction completed: {id} - ${price:,.2f}")
        return response.strip()

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        logger.error(f"❌ Error creating transaction: {e}")
        return f"❌ Error processing order: {str(e)}"


# ============================================================================
# TOOL 2: Get Cash Balance (Company financials)
# ============================================================================


@sales_agent.tool
async def get_cash_balance(ctx: RunContext[SalesDependencies]) -> str:
    """
    Get current cash balance from sales and purchases.

    Returns:
        Financial summary with cash balance
    """
    logger.info("💰 Calculating cash balance...")

    try:
        conn = get_db_connection(ctx.deps.db_path)

        # Sales (money IN)
        sales_df = pd.read_sql_query(
            """
            SELECT SUM(price) as total_sales
            FROM transactions
            WHERE transaction_type = 'sales'
        """,
            conn,
        )

        # Purchases (money OUT)
        purchases_df = pd.read_sql_query(
            """
            SELECT SUM(price) as total_purchases
            FROM transactions
            WHERE transaction_type = 'stock_orders'
        """,
            conn,
        )

        conn.close()

        total_sales = sales_df["total_sales"].iloc[0] or 0.0
        total_purchases = purchases_df["total_purchases"].iloc[0] or 0.0
        cash_balance = total_sales - total_purchases

        response = f"""
💰 **Financial Summary**

Revenue (Sales): ${total_sales:,.2f}
Expenses (Purchases): ${total_purchases:,.2f}
━━━━━━━━━━━━━━━━━━━━━━━
**Cash Balance: ${cash_balance:,.2f}**

{"✅ Positive cash flow" if cash_balance > 0 else "⚠️ Negative cash flow"}
"""

        logger.success(f"✅ Cash balance: ${cash_balance:,.2f}")
        return response.strip()

    except Exception as e:
        logger.error(f"❌ Error calculating balance: {e}")
        return f"Error retrieving cash balance: {str(e)}"


# ============================================================================
# TOOL 3: Generate Financial Report
# ============================================================================


@sales_agent.tool
async def generate_financial_report(
    ctx: RunContext[SalesDependencies], period: Literal["today", "week", "month", "all"] = "all"
) -> str:
    """
    Generate comprehensive financial report.

    Args:
        ctx: Context with dependencies
        period: Time period for report (today/week/month/all)

    Returns:
        Detailed financial report
    """
    logger.info(f"📊 Generating {period} financial report...")

    try:
        conn = get_db_connection(ctx.deps.db_path)

        # Construir filtro de data
        date_filter = ""
        if period == "today":
            date_filter = "AND DATE(transaction_date) = DATE('now')"
        elif period == "week":
            date_filter = "AND DATE(transaction_date) >= DATE('now', '-7 days')"
        elif period == "month":
            date_filter = "AND DATE(transaction_date) >= DATE('now', '-30 days')"

        # Sales
        sales_query = f"""
            SELECT 
                COUNT(*) as num_sales,
                SUM(quantity) as total_units_sold,
                SUM(price) as total_revenue
            FROM transactions
            WHERE transaction_type = 'sales'
            {date_filter}
        """
        sales_df = pd.read_sql_query(sales_query, conn)

        # Top products
        top_products_query = f"""
            SELECT 
                item_name,
                SUM(quantity) as units_sold,
                SUM(price) as revenue
            FROM transactions
            WHERE transaction_type = 'sales'
            {date_filter}
            GROUP BY item_name
            ORDER BY revenue DESC
            LIMIT 5
        """
        top_df = pd.read_sql_query(top_products_query, conn)

        # Purchases
        purchases_query = f"""
            SELECT 
                COUNT(*) as num_purchases,
                SUM(price) as total_spent
            FROM transactions
            WHERE transaction_type = 'stock_orders'
            {date_filter}
        """
        purchases_df = pd.read_sql_query(purchases_query, conn)

        conn.close()

        # Formatar relatório
        num_sales = int(sales_df["num_sales"].iloc[0] or 0)
        total_units = int(sales_df["total_units_sold"].iloc[0] or 0)
        revenue = float(sales_df["total_revenue"].iloc[0] or 0.0)

        num_purchases = int(purchases_df["num_purchases"].iloc[0] or 0)
        spent = float(purchases_df["total_spent"].iloc[0] or 0.0)

        profit = revenue - spent

        period_label = {
            "today": "Today",
            "week": "Last 7 Days",
            "month": "Last 30 Days",
            "all": "All Time",
        }[period]

        lines = [
            f"📊 **Financial Report - {period_label}**",
            "",
            "**SALES:**",
            f"• Number of Transactions: {num_sales:,}",
            f"• Total Units Sold: {total_units:,}",
            f"• Total Revenue: ${revenue:,.2f}",
            "",
            "**PURCHASES:**",
            f"• Number of Orders: {num_purchases:,}",
            f"• Total Spent: ${spent:,.2f}",
            "",
            "**PROFIT:**",
            f"• Net Profit/Loss: ${profit:,.2f}",
            f"• Profit Margin: {(profit / revenue * 100) if revenue > 0 else 0:.1f}%",
        ]

        if not top_df.empty:
            lines.extend(["", "**TOP PRODUCTS:**"])
            for i, row in top_df.iterrows():
                lines.append(
                    f"{i + 1}. {row['item_name']}: {row['units_sold']:,.0f} units (${row['revenue']:,.2f})"
                )

        logger.success(f"✅ Report generated: {period}")
        return "\n".join(lines)

    except Exception as e:
        logger.error(f"❌ Error generating report: {e}")
        return f"Error generating report: {str(e)}"


# ============================================================================
# TOOL 4: Get Transaction History
# ============================================================================


@sales_agent.tool
async def get_transaction_history(
    ctx: RunContext[SalesDependencies],
    transaction_type: Literal["sales", "stock_orders"] | None = None,
    limit: int = 10,
) -> str:
    """
    Retrieve recent transaction history.

    Args:
        ctx: Context with dependencies
        transaction_type: Filter by type (sales/stock_orders/all)
        limit: Maximum number of results

    Returns:
        List of recent transactions
    """
    logger.info(f"📜 Fetching transaction history (type: {transaction_type})...")

    try:
        conn = get_db_connection(ctx.deps.db_path)

        query = """
            SELECT *
            FROM transactions
            WHERE 1=1
        """
        params = []

        if transaction_type:
            query += " AND transaction_type = ?"
            params.append(transaction_type)

        if ctx.deps.customer_id:
            query += " AND customer_id = ?"
            params.append(ctx.deps.customer_id)

        query += " ORDER BY transaction_date DESC LIMIT ?"
        params.append(limit)

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if df.empty:
            return "📜 No transactions found."

        # Formatar lista
        type_label = {"sales": "Sales", "stock_orders": "Stock Orders", None: "All"}[
            transaction_type
        ]

        lines = [f"📜 **Recent {type_label} Transactions** (last {len(df)}):\n"]

        for _, row in df.iterrows():
            type_emoji = "💰" if row["transaction_type"] == "sales" else "📦"
            status_emoji = "✅"  # Assume completed since no status field

            lines.append(
                f"{type_emoji} **#{row['id']}** {status_emoji}\n"
                f"   • Product: {row['item_name']}\n"
                f"   • Quantity: {row['units']:,} units\n"
                f"   • Amount: ${row['price']:,.2f}\n"
                f"   • Date: {row['transaction_date']}\n"
            )

        logger.success(f"✅ Found {len(df)} transactions")
        return "\n".join(lines)

    except Exception as e:
        logger.error(f"❌ Error fetching history: {e}")
        return f"Error retrieving transactions: {str(e)}"


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================


async def process_order(
    item_name: str,
    quantity: int,
    unit_price: float,
    customer_id: str | None = None,
    quote_id: str | None = None,
    db_path: str = "munder_difflin.db",
) -> str:
    """
    Convenience function to process an order.

    Args:
        item_name: Product to purchase
        quantity: Quantity to buy
        unit_price: Price per unit
        customer_id: Optional customer ID
        quote_id: Optional quote reference
        db_path: Database path

    Returns:
        Order confirmation or error
    """
    logger.info(f"🛒 Processing order: {item_name} x{quantity}")

    try:
        query = f"Process order for {quantity} units of {item_name} at ${unit_price} per unit"

        result = await sales_agent.run(
            query, deps=SalesDependencies(db_path=db_path, customer_id=customer_id)
        )

        return result.output

    except Exception as e:
        logger.error(f"❌ Error processing order: {e}")
        return f"Error: {str(e)}"


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def test_sales_agent():
        """Test the sales agent with order processing"""

        print("=" * 60)
        print("TEST 1: Process Order")
        print("=" * 60)

        response = await process_order(
            item_name="Premium Copy Paper", quantity=100, unit_price=4.50, customer_id="TEST001"
        )
        print(response)

        print("\n" + "=" * 60)
        print("TEST 2: Financial Report")
        print("=" * 60)

        from src.agents.sales_agent import SalesDependencies, sales_agent

        result = await sales_agent.run(
            "Generate a financial report for all time", deps=SalesDependencies()
        )
        print(result.output)

        print("\n" + "=" * 60)
        print("TEST 3: Cash Balance")
        print("=" * 60)

        result = await sales_agent.run("What's our current cash balance?", deps=SalesDependencies())
        print(result.output)

    asyncio.run(test_sales_agent())
