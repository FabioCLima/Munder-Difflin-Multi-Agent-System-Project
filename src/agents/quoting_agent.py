"""
Quoting Agent - Manages price quotes, bulk discounts, and pricing history
Generates accurate quotes based on inventory prices and customer requirements
"""

import sqlite3
import sys
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from loguru import logger
from pydantic import BaseModel, Field, field_validator
from pydantic_ai import Agent, RunContext

# ============================================================================
# MODELS - Estruturas de dados
# ============================================================================


class QuoteRequest(BaseModel):
    """Modelo para requisição de cotação"""

    item_name: str
    quantity: int = Field(gt=0, description="Quantity must be positive")
    customer_id: str | None = None

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v


class Quote(BaseModel):
    """Modelo para cotação gerada"""

    request_id: str
    item_name: str
    quantity: int
    unit_price: float
    discount_percentage: float = 0.0
    subtotal: float
    discount_amount: float = 0.0
    total_price: float
    quote_explanation: str
    valid_until: str
    created_at: str

    def to_formatted_string(self) -> str:
        """Retorna cotação formatada para apresentação"""
        lines = [
            f"📋 **Quote #{self.request_id}**",
            "",
            f"Product: {self.item_name}",
            f"Quantity: {self.quantity:,} units",
            f"Unit Price: ${self.unit_price:.2f}",
            "",
            f"Subtotal: ${self.subtotal:,.2f}",
        ]

        if self.discount_percentage > 0:
            lines.extend(
                [
                    f"Discount ({self.discount_percentage:.0f}%): -${self.discount_amount:,.2f}",
                    "",
                ]
            )

        lines.extend(
            [
                f"**TOTAL: ${self.total_price:,.2f}**",
                "",
                f"Valid until: {self.valid_until}",
                f"Generated: {self.created_at}",
            ]
        )

        return "\n".join(lines)


class QuotingDependencies(BaseModel):
    """Dependências para o Quoting Agent"""

    db_path: str = "munder_difflin.db"
    customer_id: str | None = None
    current_date: str = "2025-01-15"
    db_engine: Any = None


# ============================================================================
# BUSINESS RULES - Regras de desconto
# ============================================================================


class DiscountTiers:
    """Definição dos níveis de desconto por volume"""

    TIERS = [
        (1000, 0.15),  # 15% para 1000+ unidades
        (500, 0.10),  # 10% para 500-999 unidades
        (200, 0.05),  # 5% para 200-499 unidades
        (50, 0.02),  # 2% para 50-199 unidades
    ]

    @classmethod
    def get_discount_percentage(cls, quantity: int) -> float:
        """
        Calcula percentual de desconto baseado na quantidade.

        Args:
            quantity: Quantidade de unidades

        Returns:
            Percentual de desconto (0.0 a 0.15)
        """
        for min_qty, discount in cls.TIERS:
            if quantity >= min_qty:
                logger.info(f"💰 Applied {discount * 100:.0f}% discount for {quantity} units")
                return discount

        logger.info(f"💰 No discount applied for {quantity} units")
        return 0.0

    @classmethod
    def get_discount_info(cls) -> str:
        """Retorna informação formatada sobre os níveis de desconto"""
        lines = ["💰 **Bulk Discount Tiers:**"]
        for min_qty, discount in cls.TIERS:
            lines.append(f"• {min_qty:,}+ units: {discount * 100:.0f}% off")
        return "\n".join(lines)


# ============================================================================
# SYSTEM PROMPT - O "cérebro" do Quoting Agent
# ============================================================================

QUOTING_SYSTEM_PROMPT = """You are the Quoting Agent for Munder Difflin Paper Company.

Your responsibilities:
1. Generate accurate price quotes based on product prices and quantities
2. Apply bulk discounts automatically based on quantity tiers
3. Search and provide historical quote information
4. Validate product availability before quoting (coordinate with Inventory Agent)

Discount Structure:
- 1000+ units: 15% discount
- 500-999 units: 10% discount  
- 200-499 units: 5% discount
- 50-199 units: 2% discount
- Below 50 units: No discount

Quote Guidelines:
- Always check product availability first
- Apply appropriate bulk discounts automatically
- Quotes are valid for 30 days from generation
- Provide clear breakdown: unit price, subtotal, discount, total
- Be professional and transparent about pricing

When responding:
- Show complete price breakdown
- Highlight any discounts applied
- Mention validity period
- Offer to save the quote for future reference

Use the provided tools to access pricing data and generate quotes.
"""


# ============================================================================
# QUOTING AGENT
# ============================================================================

# Importar configuração de teste se estivermos em modo de teste
if "pytest" in sys.modules:
    from src.test_config import create_test_agent

    quoting_agent = create_test_agent(QUOTING_SYSTEM_PROMPT, QuotingDependencies)
else:
    quoting_agent = Agent(
        model="openai:gpt-4o-mini",
        system_prompt=QUOTING_SYSTEM_PROMPT,
        deps_type=QuotingDependencies,
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Cria conexão com o banco de dados"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def generate_request_id() -> str:
    """Gera ID único para cotação"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"Q{timestamp}"


def calculate_quote_totals(unit_price: float, quantity: int, discount_pct: float) -> tuple:
    """
    Calcula valores da cotação.

    Returns:
        (subtotal, discount_amount, total)
    """
    subtotal = unit_price * quantity
    discount_amount = subtotal * discount_pct
    total = subtotal - discount_amount

    return subtotal, discount_amount, total


# ============================================================================
# TOOL 1: Get Product Price
# ============================================================================


@quoting_agent.tool
async def get_product_price(ctx: RunContext[QuotingDependencies], item_name: str) -> str:
    """
    Get the unit price for a specific product.

    Args:
        ctx: Context with dependencies
        item_name: Name of the product

    Returns:
        Unit price information
    """
    logger.info(f"💰 Getting price for: {item_name}")

    try:
        conn = get_db_connection(ctx.deps.db_path)
        cursor = conn.cursor()

        query = """
            SELECT item_name, unit_price, current_stock
            FROM inventory
            WHERE LOWER(item_name) = LOWER(?)
        """

        cursor.execute(query, (item_name,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            logger.warning(f"⚠️ Product not found: {item_name}")
            return f"❌ Product '{item_name}' not found in our catalog."

        actual_name = row["item_name"]
        unit_price = row["unit_price"]
        stock = row["current_stock"]

        response = f"""
💰 **Pricing for {actual_name}**

Unit Price: ${unit_price:.2f}
Current Stock: {stock:,} units

{DiscountTiers.get_discount_info()}
"""

        logger.success(f"✅ Price retrieved: ${unit_price:.2f}")
        return response.strip()

    except Exception as e:
        logger.error(f"❌ Error getting price: {e}")
        return f"Error retrieving price: {str(e)}"


# ============================================================================
# TOOL 2: Generate Quote
# ============================================================================


@quoting_agent.tool
async def generate_quote(
    ctx: RunContext[QuotingDependencies], item_name: str, quantity: int
) -> str:
    """
    Generate a complete price quote with bulk discounts.
    Validates availability and saves quote to database.

    Args:
        ctx: Context with dependencies
        item_name: Product to quote
        quantity: Requested quantity

    Returns:
        Formatted quote with pricing breakdown
    """
    logger.info(f"📋 Generating quote: {item_name} x{quantity}")

    try:
        # 1. Verificar se produto existe e pegar preço
        conn = get_db_connection(ctx.deps.db_path)
        cursor = conn.cursor()

        query = """
            SELECT item_name, unit_price, current_stock
            FROM inventory
            WHERE LOWER(item_name) = LOWER(?)
        """

        cursor.execute(query, (item_name,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            logger.warning(f"⚠️ Product not found: {item_name}")
            return f"❌ Product '{item_name}' not found. Please check the product name."

        actual_name = row["item_name"]
        unit_price = row["unit_price"]
        current_stock = row["current_stock"]

        # 2. Validar disponibilidade
        availability_warning = ""
        if current_stock == 0:
            availability_warning = (
                "\n⚠️ **Note:** This product is currently out of stock. Lead time may apply."
            )
        elif current_stock < quantity:
            availability_warning = f"\n⚠️ **Note:** Only {current_stock:,} units currently in stock. Partial delivery or lead time may apply."

        # 3. Calcular desconto
        discount_pct = DiscountTiers.get_discount_percentage(quantity)
        subtotal, discount_amount, total = calculate_quote_totals(
            unit_price, quantity, discount_pct
        )

        # 4. Gerar Quote
        request_id = generate_request_id()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        valid_until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        quote_explanation = f"Quote for {quantity} units of {actual_name} at ${unit_price:.2f} per unit"
        if discount_pct > 0:
            quote_explanation += f" with {discount_pct*100:.0f}% discount"
        
        quote = Quote(
            request_id=request_id,
            item_name=actual_name,
            quantity=quantity,
            unit_price=unit_price,
            discount_percentage=discount_pct * 100,
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_price=total,
            quote_explanation=quote_explanation,
            valid_until=valid_until,
            created_at=created_at,
        )

        # 5. Salvar no banco de dados
        insert_query = """
            INSERT INTO quotes (
                request_id, total_amount, quote_explanation
            ) VALUES (?, ?, ?)
        """

        cursor.execute(
            insert_query,
            (
                quote.request_id,
                quote.total_price,
                quote.quote_explanation,
            ),
        )

        conn.commit()
        conn.close()

        # 6. Formatar resposta
        response = quote.to_formatted_string()

        if availability_warning:
            response += f"\n{availability_warning}"

        response += f"\n\n✅ Quote saved! Reference: #{request_id}"

        logger.success(f"✅ Quote generated: {request_id} - ${total:,.2f}")
        return response

    except Exception as e:
        logger.error(f"❌ Error generating quote: {e}")
        if "conn" in locals():
            conn.close()
        return f"Error generating quote: {str(e)}"


# ============================================================================
# TOOL 3: Search Quote History
# ============================================================================


@quoting_agent.tool
async def search_quote_history(
    ctx: RunContext[QuotingDependencies],
    item_name: str | None = None,
    customer_id: str | None = None,
    limit: int = 10,
) -> str:
    """
    Search historical quotes by product or customer.

    Args:
        ctx: Context with dependencies
        item_name: Optional filter by product
        customer_id: Optional filter by customer
        limit: Maximum number of results (default 10)

    Returns:
        List of matching historical quotes
    """
    logger.info("🔍 Searching quote history...")

    try:
        conn = get_db_connection(ctx.deps.db_path)

        # Construir query dinâmica
        query = """
            SELECT 
                request_id,
                customer_id,
                item_name,
                quantity,
                unit_price,
                discount_percentage,
                total_price,
                status,
                created_at,
                valid_until
            FROM quotes
            WHERE 1=1
        """
        params = []

        if item_name:
            query += " AND LOWER(item_name) LIKE LOWER(?)"
            params.append(f"%{item_name}%")

        if customer_id:
            query += " AND customer_id = ?"
            params.append(customer_id)
        elif ctx.deps.customer_id:
            query += " AND customer_id = ?"
            params.append(ctx.deps.customer_id)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if df.empty:
            return "📋 No quotes found matching your criteria."

        # Formatar resultados
        results = [f"📋 **Found {len(df)} quote(s):**\n"]

        for _, row in df.iterrows():
            discount_info = ""
            if row["discount_percentage"] > 0:
                discount_info = f" ({row['discount_percentage']:.0f}% discount)"

            status_emoji = "✅" if row["status"] == "accepted" else "⏳"

            results.append(
                f"{status_emoji} **Quote #{row['request_id']}**\n"
                f"   • Product: {row['item_name']}\n"
                f"   • Quantity: {row['quantity']:,} units\n"
                f"   • Total: ${row['total_price']:,.2f}{discount_info}\n"
                f"   • Date: {row['created_at']}\n"
                f"   • Status: {row['status'].upper()}\n"
            )

        logger.success(f"✅ Found {len(df)} quotes")
        return "\n".join(results)

    except Exception as e:
        logger.error(f"❌ Error searching quotes: {e}")
        return f"Error searching quote history: {str(e)}"


# ============================================================================
# TOOL 4: Get Quote by ID
# ============================================================================


@quoting_agent.tool
async def get_quote_by_id(ctx: RunContext[QuotingDependencies], request_id: str) -> str:
    """
    Retrieve a specific quote by its ID.

    Args:
        ctx: Context with dependencies
        request_id: Quote ID to retrieve

    Returns:
        Detailed quote information
    """
    logger.info(f"🔍 Retrieving quote: {request_id}")

    try:
        conn = get_db_connection(ctx.deps.db_path)
        cursor = conn.cursor()

        query = """
            SELECT *
            FROM quotes
            WHERE request_id = ?
        """

        cursor.execute(query, (request_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            logger.warning(f"⚠️ Quote not found: {request_id}")
            return f"❌ Quote #{request_id} not found."

        # Reconstruir objeto Quote
        subtotal = row["unit_price"] * row["quantity"]
        discount_amount = subtotal * (row["discount_percentage"] / 100)

        quote = Quote(
            request_id=row["request_id"],
            item_name=row["item_name"],
            quantity=row["quantity"],
            unit_price=row["unit_price"],
            discount_percentage=row["discount_percentage"],
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_price=row["total_price"],
            valid_until=row["valid_until"],
            created_at=row["created_at"],
        )

        response = quote.to_formatted_string()
        response += f"\n\nStatus: {row['status'].upper()}"

        if row["customer_id"]:
            response += f"\nCustomer: {row['customer_id']}"

        logger.success(f"✅ Quote retrieved: {request_id}")
        return response

    except Exception as e:
        logger.error(f"❌ Error retrieving quote: {e}")
        return f"Error retrieving quote: {str(e)}"


# ============================================================================
# TOOL 5: Calculate Custom Quote (with manual discount)
# ============================================================================


@quoting_agent.tool
async def calculate_custom_quote(
    ctx: RunContext[QuotingDependencies],
    item_name: str,
    quantity: int,
    custom_discount_pct: float = 0.0,
) -> str:
    """
    Calculate a quote with custom discount (for special negotiations).
    Does not save to database - for preview only.

    Args:
        ctx: Context with dependencies
        item_name: Product to quote
        quantity: Requested quantity
        custom_discount_pct: Custom discount percentage (0-100)

    Returns:
        Calculated quote preview
    """
    logger.info(
        f"🧮 Calculating custom quote: {item_name} x{quantity} @ {custom_discount_pct}% off"
    )

    try:
        # Validar discount
        if custom_discount_pct < 0 or custom_discount_pct > 100:
            return "❌ Custom discount must be between 0% and 100%"

        # Buscar preço
        conn = get_db_connection(ctx.deps.db_path)
        cursor = conn.cursor()

        query = "SELECT item_name, unit_price FROM inventory WHERE LOWER(item_name) = LOWER(?)"
        cursor.execute(query, (item_name,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return f"❌ Product '{item_name}' not found."

        actual_name = row["item_name"]
        unit_price = row["unit_price"]

        # Calcular
        subtotal = unit_price * quantity
        discount_amount = subtotal * (custom_discount_pct / 100)
        total = subtotal - discount_amount

        # Comparar com desconto padrão
        standard_discount = DiscountTiers.get_discount_percentage(quantity) * 100

        response = f"""
🧮 **Custom Quote Preview** (NOT SAVED)

Product: {actual_name}
Quantity: {quantity:,} units
Unit Price: ${unit_price:.2f}

Subtotal: ${subtotal:,.2f}
Custom Discount ({custom_discount_pct:.1f}%): -${discount_amount:,.2f}
**TOTAL: ${total:,.2f}**

ℹ️ Standard bulk discount for this quantity: {standard_discount:.0f}%
"""

        if custom_discount_pct > standard_discount:
            response += "\n⚠️ Custom discount is higher than standard tier."

        logger.success(f"✅ Custom quote calculated: ${total:,.2f}")
        return response.strip()

    except Exception as e:
        logger.error(f"❌ Error calculating custom quote: {e}")
        return f"Error: {str(e)}"


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================


async def request_quote(
    item_name: str,
    quantity: int,
    customer_id: str | None = None,
    db_path: str = "munder_difflin.db",
) -> str:
    """
    Convenience function to request a quote.

    Args:
        item_name: Product to quote
        quantity: Requested quantity
        customer_id: Optional customer ID
        db_path: Database path

    Returns:
        Generated quote
    """
    logger.info(f"💬 Quote request: {item_name} x{quantity}")

    try:
        query = f"I need a quote for {quantity} units of {item_name}"

        result = await quoting_agent.run(
            query, deps=QuotingDependencies(db_path=db_path, customer_id=customer_id)
        )

        return result.output

    except Exception as e:
        logger.error(f"❌ Error requesting quote: {e}")
        return f"Error: {str(e)}"


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def test_quoting_agent():
        """Test the quoting agent with various scenarios"""

        test_scenarios = [
            # Scenario 1: Small order (no discount)
            ("Standard Copy Paper", 25),
            # Scenario 2: Medium order (2% discount)
            ("Premium Copy Paper", 100),
            # Scenario 3: Large order (10% discount)
            ("Dunder Mifflin Premium Copy Paper", 750),
            # Scenario 4: Bulk order (15% discount)
            ("Recycled Copy Paper", 1500),
        ]

        for product, quantity in test_scenarios:
            print(f"\n{'=' * 60}")
            print(f"Test: {product} x{quantity} units")
            print(f"{'=' * 60}")

            response = await request_quote(
                item_name=product, quantity=quantity, customer_id="TEST_CUSTOMER"
            )
            print(f"\n{response}\n")

            await asyncio.sleep(0.5)  # Rate limiting

    asyncio.run(test_quoting_agent())
