"""
Inventory Agent - Manages stock checking and product search
Provides real-time inventory information to customers and other agents
"""

import sqlite3
import sys
from typing import Any

import pandas as pd
from loguru import logger
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

# ============================================================================
# MODELS - Estruturas de dados
# ============================================================================


class InventoryItem(BaseModel):
    """Modelo para um item do inventário"""

    product_name: str
    stock_level: int
    min_stock_level: int
    unit_cost: float
    is_low_stock: bool = False

    @property
    def stock_status(self) -> str:
        """Retorna status legível do estoque"""
        if self.stock_level == 0:
            return "❌ OUT OF STOCK"
        elif self.is_low_stock:
            return f"⚠️ LOW STOCK ({self.stock_level} units left)"
        else:
            return f"✅ IN STOCK ({self.stock_level} units available)"


class InventoryDependencies(BaseModel):
    """Dependências para o Inventory Agent"""

    db_path: str = "munder_difflin.db"
    current_date: str = "2025-01-15"
    db_engine: Any = None


# ============================================================================
# SYSTEM PROMPT - O "cérebro" do Inventory Agent
# ============================================================================

INVENTORY_SYSTEM_PROMPT = """You are the Inventory Agent for Munder Difflin Paper Company.

Your responsibilities:
1. Check stock levels for specific products
2. Search for products in the inventory
3. Provide accurate, real-time inventory information
4. Alert when stock is low or out of stock

Guidelines:
- Always provide exact stock numbers
- Be clear about stock status (in stock, low stock, out of stock)
- If a product is not found, suggest similar products if possible
- Be professional and helpful
- Use the tools available to query the database

When responding:
- ✅ "We have 250 units of Premium Copy Paper in stock"
- ⚠️ "Standard Copy Paper is running low (only 15 units left)"
- ❌ "Unfortunately, Glossy Brochure Paper is currently out of stock"

Always use the provided tools to get accurate data from the database.
"""


# ============================================================================
# INVENTORY AGENT
# ============================================================================

# Importar configuração de teste se estivermos em modo de teste
if "pytest" in sys.modules:
    from src.test_config import create_test_agent

    inventory_agent = create_test_agent(INVENTORY_SYSTEM_PROMPT, InventoryDependencies)
else:
    inventory_agent = Agent(
        model="openai:gpt-4o-mini",  # Mini é suficiente para queries simples
        system_prompt=INVENTORY_SYSTEM_PROMPT,
        deps_type=InventoryDependencies,
    )


# ============================================================================
# HELPER FUNCTIONS - Interação com Database
# ============================================================================


def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Cria conexão com o banco de dados"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
    return conn


def check_low_stock(stock_level: int, min_stock_level: int) -> bool:
    """Verifica se o estoque está baixo"""
    return stock_level < min_stock_level


# ============================================================================
# TOOL 1: Get All Inventory
# ============================================================================


@inventory_agent.tool
async def get_all_inventory(ctx: RunContext[InventoryDependencies]) -> str:
    """
    Get complete inventory list with stock levels.

    Returns:
        Formatted string with all inventory items and their stock status
    """
    logger.info("🔍 Fetching complete inventory...")

    try:
        conn = get_db_connection(ctx.deps.db_path)

        query = """
            SELECT 
                item_name,
                current_stock,
                min_stock_level,
                unit_price
            FROM inventory
            ORDER BY item_name
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            return "❌ No items found in inventory."

        # Formatar resposta
        items = []
        for _, row in df.iterrows():
            item = InventoryItem(
                product_name=row["item_name"],
                stock_level=row["current_stock"],
                min_stock_level=row["min_stock_level"],
                unit_cost=row["unit_price"],
                is_low_stock=check_low_stock(row["current_stock"], row["min_stock_level"]),
            )
            items.append(f"• {item.product_name}: {item.stock_status}")

        result = "📦 **Current Inventory:**\n" + "\n".join(items)
        logger.success(f"✅ Found {len(items)} items in inventory")

        return result

    except Exception as e:
        logger.error(f"❌ Error fetching inventory: {e}")
        return f"Error accessing inventory: {str(e)}"


# ============================================================================
# TOOL 2: Get Stock Level for Specific Product
# ============================================================================


@inventory_agent.tool
async def get_stock_level(ctx: RunContext[InventoryDependencies], product_name: str) -> str:
    """
    Check stock level for a specific product.

    Args:
        ctx: Context with dependencies
        product_name: Name of the product to check

    Returns:
        Stock status and availability information
    """
    logger.info(f"🔍 Checking stock for: {product_name}")

    try:
        conn = get_db_connection(ctx.deps.db_path)
        cursor = conn.cursor()

        # Query case-insensitive
        query = """
            SELECT 
                item_name,
                current_stock,
                min_stock_level,
                unit_price
            FROM inventory
            WHERE LOWER(item_name) = LOWER(?)
        """

        cursor.execute(query, (product_name,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            logger.warning(f"⚠️ Product not found: {product_name}")
            return f"❌ Product '{product_name}' not found in inventory. Please check the spelling or ask for our product catalog."

        # Criar objeto InventoryItem
        item = InventoryItem(
            product_name=row["item_name"],
            stock_level=row["current_stock"],
            min_stock_level=row["min_stock_level"],
            unit_cost=row["unit_price"],
            is_low_stock=check_low_stock(row["current_stock"], row["min_stock_level"]),
        )

        # Formatar resposta detalhada
        response = f"""
📦 **{item.product_name}**
{item.stock_status}

Details:
- Current Stock: {item.stock_level} units
- Minimum Level: {item.min_stock_level} units
- Unit Cost: ${item.unit_cost:.2f}
"""

        if item.stock_level == 0:
            response += "\n⚠️ This item needs to be reordered."
        elif item.is_low_stock:
            response += "\n⚠️ Stock is below minimum level. Reordering recommended."

        logger.success(f"✅ Stock check completed for {product_name}")
        return response.strip()

    except Exception as e:
        logger.error(f"❌ Error checking stock: {e}")
        return f"Error checking stock for '{product_name}': {str(e)}"


# ============================================================================
# TOOL 3: Search Products (Fuzzy search)
# ============================================================================


@inventory_agent.tool
async def search_products(ctx: RunContext[InventoryDependencies], search_term: str) -> str:
    """
    Search for products using partial matching.
    Useful when customer doesn't know exact product name.

    Args:
        ctx: Context with dependencies
        search_term: Partial product name to search

    Returns:
        List of matching products with stock status
    """
    logger.info(f"🔍 Searching products with term: {search_term}")

    try:
        conn = get_db_connection(ctx.deps.db_path)

        # Query com LIKE para busca parcial
        query = """
            SELECT 
                item_name,
                current_stock,
                min_stock_level,
                unit_price
            FROM inventory
            WHERE LOWER(item_name) LIKE LOWER(?)
            ORDER BY item_name
        """

        search_pattern = f"%{search_term}%"
        df = pd.read_sql_query(query, conn, params=(search_pattern,))
        conn.close()

        if df.empty:
            logger.warning(f"⚠️ No products found matching: {search_term}")
            return f"❌ No products found matching '{search_term}'. Try different keywords or ask for our complete catalog."

        # Formatar resultados
        results = [f"🔍 **Found {len(df)} product(s) matching '{search_term}':**\n"]

        for _, row in df.iterrows():
            item = InventoryItem(
                product_name=row["item_name"],
                stock_level=row["current_stock"],
                min_stock_level=row["min_stock_level"],
                unit_cost=row["unit_price"],
                is_low_stock=check_low_stock(row["current_stock"], row["min_stock_level"]),
            )
            results.append(
                f"• {item.product_name}: {item.stock_status} (${item.unit_cost:.2f}/unit)"
            )

        logger.success(f"✅ Found {len(df)} matching products")
        return "\n".join(results)

    except Exception as e:
        logger.error(f"❌ Error searching products: {e}")
        return f"Error searching for products: {str(e)}"


# ============================================================================
# TOOL 4: Check if Product is Available for Order
# ============================================================================


@inventory_agent.tool
async def check_availability_for_order(
    ctx: RunContext[InventoryDependencies], product_name: str, quantity: int
) -> str:
    """
    Verify if sufficient stock is available for a specific order quantity.
    Used by other agents (Quoting, Sales) before processing orders.

    Args:
        ctx: Context with dependencies
        product_name: Product to check
        quantity: Requested quantity

    Returns:
        Availability status (sufficient/insufficient/out of stock)
    """
    logger.info(f"🔍 Checking availability: {product_name} x{quantity}")

    try:
        conn = get_db_connection(ctx.deps.db_path)
        cursor = conn.cursor()

        query = """
            SELECT current_stock, item_name
            FROM inventory
            WHERE LOWER(item_name) = LOWER(?)
        """

        cursor.execute(query, (product_name,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return f"❌ UNAVAILABLE: Product '{product_name}' not found in inventory."

        current_stock = row["current_stock"]
        actual_name = row["item_name"]

        if current_stock == 0:
            return f"❌ OUT OF STOCK: {actual_name} is currently unavailable."

        if current_stock < quantity:
            return f"⚠️ INSUFFICIENT STOCK: {actual_name} has only {current_stock} units available (requested: {quantity})."

        logger.success(f"✅ Sufficient stock available: {current_stock} >= {quantity}")
        return f"✅ AVAILABLE: {actual_name} has sufficient stock ({current_stock} units available for {quantity} requested)."

    except Exception as e:
        logger.error(f"❌ Error checking availability: {e}")
        return f"Error checking availability: {str(e)}"


# ============================================================================
# TOOL 5: Get Low Stock Items (for Reordering Agent)
# ============================================================================


@inventory_agent.tool
async def get_low_stock_items(ctx: RunContext[InventoryDependencies]) -> str:
    """
    Get list of all items that are below minimum stock level.
    Used by Reordering Agent to trigger automatic restocking.

    Returns:
        List of products that need reordering
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
            logger.success("✅ All items are adequately stocked")
            return "✅ All inventory items are at or above minimum stock levels."

        # Formatar lista de items baixos
        low_stock_items = []
        for _, row in df.iterrows():
            deficit = row["min_stock_level"] - row["current_stock"]
            low_stock_items.append(
                f"• {row['item_name']}: {row['current_stock']}/{row['min_stock_level']} units "
                f"(need {deficit} more)"
            )

        result = f"⚠️ **{len(df)} item(s) below minimum stock:**\n" + "\n".join(low_stock_items)
        logger.warning(f"⚠️ Found {len(df)} items needing restock")

        return result

    except Exception as e:
        logger.error(f"❌ Error checking low stock: {e}")
        return f"Error checking low stock items: {str(e)}"


# ============================================================================
# CONVENIENCE FUNCTION - Direct query interface
# ============================================================================


async def query_inventory(question: str, db_path: str = "munder_difflin.db") -> str:
    """
    Convenience function to query inventory with natural language.

    Args:
        question: Natural language question about inventory
        db_path: Path to database

    Returns:
        Answer from Inventory Agent

    Example:
        >>> answer = await query_inventory("Do you have Premium Copy Paper?")
        >>> print(answer)
    """
    logger.info(f"💬 Inventory query: {question}")

    try:
        result = await inventory_agent.run(question, deps=InventoryDependencies(db_path=db_path))
        return result.output

    except Exception as e:
        logger.error(f"❌ Error querying inventory: {e}")
        return f"Error: {str(e)}"


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def test_inventory_agent():
        """Test the inventory agent with various queries"""

        test_queries = [
            "Show me all products in inventory",
            "Do you have Dunder Mifflin Premium Copy Paper?",
            "Search for 'copy' products",
            "Can you fulfill an order for 100 units of Standard Copy Paper?",
            "Which items are running low?",
        ]

        for query in test_queries:
            print(f"\n{'=' * 60}")
            print(f"Query: {query}")
            print(f"{'=' * 60}")

            response = await query_inventory(query)
            print(f"\n{response}\n")

    asyncio.run(test_inventory_agent())
