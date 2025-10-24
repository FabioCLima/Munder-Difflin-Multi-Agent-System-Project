"""
Orchestrator Agent - Central coordinator for the multi-agent system
Routes customer requests to specialized agents
"""

import sys
from typing import Literal

from loguru import logger
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

# ============================================================================
# MODELS - Estruturas de dados
# ============================================================================


class CustomerRequest(BaseModel):
    """Modelo para requisições de clientes"""

    text: str = Field(..., description="Customer's request in natural language")
    customer_id: str | None = Field(default=None, description="Customer identifier")


class AgentResponse(BaseModel):
    """Modelo para respostas dos agentes"""

    agent_type: Literal["inventory", "quoting", "sales", "reordering"]
    response: str
    success: bool
    data: dict | None = None


class OrchestratorDependencies(BaseModel):
    """Dependências compartilhadas entre agentes"""

    db_path: str = "munder_difflin.db"
    customer_id: str | None = None


# ============================================================================
# SYSTEM PROMPT - O "cérebro" do Orchestrator
# ============================================================================

ORCHESTRATOR_SYSTEM_PROMPT = """You are the Orchestrator Agent for Munder Difflin Paper Company.

Your role is to:
1. Understand customer requests in natural language
2. Determine which specialized agent should handle the request
3. Coordinate between agents when needed
4. Provide clear, professional responses

Available specialized agents:
- **InventoryAgent**: Check stock levels, search for products, get inventory information
- **QuotingAgent**: Generate price quotes, calculate discounts, provide pricing history
- **SalesAgent**: Process orders, finalize transactions, generate reports
- **ReorderingAgent**: (Background process - automatically triggered when stock is low)

Decision Logic:
- If customer asks about "availability", "stock", "in stock", "do you have" → InventoryAgent
- If customer asks for "price", "quote", "how much", "cost" → QuotingAgent  
- If customer wants to "buy", "order", "purchase", "place order" → SalesAgent
- If request is complex, you may need to coordinate multiple agents

Always be professional, clear, and helpful. Think step-by-step before deciding.
"""


# ============================================================================
# ORCHESTRATOR AGENT
# ============================================================================

# Importar configuração de teste se estivermos em modo de teste
if "pytest" in sys.modules:
    from src.test_config import create_test_agent

    orchestrator_agent = create_test_agent(ORCHESTRATOR_SYSTEM_PROMPT, OrchestratorDependencies)
else:
    orchestrator_agent = Agent(
        model="openai:gpt-4o",  # Modelo mais inteligente para coordenação
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        deps_type=OrchestratorDependencies,
    )


# ============================================================================
# TOOL: Delegate to Inventory Agent
# ============================================================================


@orchestrator_agent.tool
async def delegate_to_inventory(ctx: RunContext[OrchestratorDependencies], query: str) -> str:
    """
    Delegate request to Inventory Agent for stock checking and product search.

    Args:
        ctx: Context with dependencies
        query: Customer's inventory-related question

    Returns:
        Response from Inventory Agent
    """
    logger.info(f"🔄 Orchestrator delegating to InventoryAgent: {query}")

    # Import aqui para evitar circular imports
    from .inventory_agent import InventoryDependencies, inventory_agent

    try:
        result = await inventory_agent.run(
            query, deps=InventoryDependencies(db_path=ctx.deps.db_path)
        )

        logger.success("✅ InventoryAgent responded successfully")
        return result.output

    except Exception as e:
        logger.error(f"❌ Error delegating to InventoryAgent: {e}")
        return f"Error checking inventory: {str(e)}"


# ============================================================================
# TOOL: Delegate to Quoting Agent
# ============================================================================


@orchestrator_agent.tool
async def delegate_to_quoting(
    ctx: RunContext[OrchestratorDependencies], product_name: str, quantity: int
) -> str:
    """
    Delegate request to Quoting Agent for price quotes.

    Args:
        ctx: Context with dependencies
        product_name: Name of the product to quote
        quantity: Quantity requested

    Returns:
        Price quote from Quoting Agent
    """
    logger.info(f"🔄 Orchestrator delegating to QuotingAgent: {product_name} x{quantity}")

    from .quoting_agent import QuotingDependencies, quoting_agent

    try:
        query = f"Generate quote for {quantity} units of {product_name}"
        result = await quoting_agent.run(
            query,
            deps=QuotingDependencies(db_path=ctx.deps.db_path, customer_id=ctx.deps.customer_id),
        )

        logger.success("✅ QuotingAgent responded successfully")
        return result.output

    except Exception as e:
        logger.error(f"❌ Error delegating to QuotingAgent: {e}")
        return f"Error generating quote: {str(e)}"


# ============================================================================
# TOOL: Delegate to Sales Agent
# ============================================================================


@orchestrator_agent.tool
async def delegate_to_sales(
    ctx: RunContext[OrchestratorDependencies], product_name: str, quantity: int, quoted_price: float
) -> str:
    """
    Delegate request to Sales Agent for order processing.

    Args:
        ctx: Context with dependencies
        product_name: Product to purchase
        quantity: Quantity to purchase
        quoted_price: Price per unit (from quote)

    Returns:
        Order confirmation from Sales Agent
    """
    logger.info(
        f"🔄 Orchestrator delegating to SalesAgent: {product_name} x{quantity} @ ${quoted_price}"
    )

    from .sales_agent import SalesDependencies, sales_agent

    try:
        query = f"Process order: {quantity} units of {product_name} at ${quoted_price} per unit"
        result = await sales_agent.run(
            query,
            deps=SalesDependencies(db_path=ctx.deps.db_path, customer_id=ctx.deps.customer_id),
        )

        logger.success("✅ SalesAgent responded successfully")
        return result.output

    except Exception as e:
        logger.error(f"❌ Error delegating to SalesAgent: {e}")
        return f"Error processing order: {str(e)}"


# ============================================================================
# MAIN FUNCTION - Entry point for customer requests
# ============================================================================


async def handle_customer_request(
    request_text: str, customer_id: str | None = None, db_path: str = "munder_difflin.db"
) -> str:
    """
    Main entry point for handling customer requests.

    Args:
        request_text: Customer's request in natural language
        customer_id: Optional customer identifier
        db_path: Path to SQLite database

    Returns:
        Response from the orchestrator or specialized agent

    Example:
        >>> response = await handle_customer_request(
        ...     "Do you have Dunder Mifflin Premium Copy Paper in stock?"
        ... )
        >>> print(response)
    """
    logger.info(f"📨 New customer request: {request_text}")

    try:
        result = await orchestrator_agent.run(
            request_text, deps=OrchestratorDependencies(db_path=db_path, customer_id=customer_id)
        )

        logger.success("✅ Request handled successfully")
        return result.output

    except Exception as e:
        logger.error(f"❌ Error handling request: {e}")
        return f"Sorry, I encountered an error processing your request: {str(e)}"


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def test_orchestrator():
        """Test the orchestrator with sample requests"""

        requests = [
            "Do you have Dunder Mifflin Premium Copy Paper in stock?",
            "How much does Standard Copy Paper cost for 500 reams?",
            "I want to buy 100 reams of Premium Copy Paper",
        ]

        for req in requests:
            print(f"\n{'=' * 60}")
            print(f"Request: {req}")
            print(f"{'=' * 60}")

            response = await handle_customer_request(req, customer_id="CUST001")
            print(f"\nResponse:\n{response}\n")

    asyncio.run(test_orchestrator())
