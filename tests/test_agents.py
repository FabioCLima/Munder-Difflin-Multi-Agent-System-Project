"""
Test suite for all agents in the multi-agent system
Tests the core functionality of each agent individually
"""

import shutil
import tempfile
from pathlib import Path

import pytest

# Import all agents
from src.agents.inventory_agent import query_inventory
from src.agents.orchestrator import handle_customer_request
from src.agents.quoting_agent import request_quote
from src.agents.reordering import trigger_reorder_check
from src.agents.sales_agent import process_order

# Import database functions
from src.database import create_engine, init_database


@pytest.fixture(scope="session")
def test_db_path():
    """Create a temporary database for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_munder_difflin.db"

    # Initialize test database
    engine = create_engine(f"sqlite:///{db_path}")
    init_database(engine, seed=137)

    yield str(db_path)

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_customer_id():
    """Generate a test customer ID"""
    return "test_customer_001"


class TestInventoryAgent:
    """Test suite for Inventory Agent"""

    @pytest.mark.asyncio
    async def test_inventory_agent_basic_query(self, test_db_path):
        """Test basic inventory query functionality"""
        response = await query_inventory("What products do we have in stock?", db_path=test_db_path)

        assert isinstance(response, str)
        assert len(response) > 0
        # Should contain inventory information
        assert any(
            keyword in response.lower()
            for keyword in ["stock", "inventory", "available", "product"]
        )

    @pytest.mark.asyncio
    async def test_inventory_agent_specific_product(self, test_db_path):
        """Test querying specific product information"""
        response = await query_inventory("Do we have A4 paper in stock?", db_path=test_db_path)

        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_inventory_agent_low_stock_check(self, test_db_path):
        """Test low stock identification"""
        response = await query_inventory(
            "Which products are running low on stock?", db_path=test_db_path
        )

        assert isinstance(response, str)
        assert len(response) > 0


class TestQuotingAgent:
    """Test suite for Quoting Agent"""

    @pytest.mark.asyncio
    async def test_quoting_agent_small_order(self, test_db_path, test_customer_id):
        """Test quote generation for small order"""
        response = await request_quote(
            product_name="A4 paper", quantity=10, customer_id=test_customer_id, db_path=test_db_path
        )

        assert isinstance(response, str)
        assert len(response) > 0
        # Should contain pricing information
        assert any(
            keyword in response.lower() for keyword in ["quote", "price", "total", "discount"]
        )

    @pytest.mark.asyncio
    async def test_quoting_agent_large_order(self, test_db_path, test_customer_id):
        """Test quote generation for large order with bulk discount"""
        response = await request_quote(
            product_name="A4 paper",
            quantity=1000,
            customer_id=test_customer_id,
            db_path=test_db_path,
        )

        assert isinstance(response, str)
        assert len(response) > 0
        # Should mention bulk discount for large orders
        assert any(
            keyword in response.lower() for keyword in ["bulk", "discount", "large", "order"]
        )

    @pytest.mark.asyncio
    async def test_quoting_agent_invalid_product(self, test_db_path, test_customer_id):
        """Test quote generation for non-existent product"""
        response = await request_quote(
            product_name="Non-existent Product",
            quantity=10,
            customer_id=test_customer_id,
            db_path=test_db_path,
        )

        assert isinstance(response, str)
        assert len(response) > 0
        # Should indicate product not found
        assert any(
            keyword in response.lower() for keyword in ["not found", "unavailable", "doesn't exist"]
        )


class TestSalesAgent:
    """Test suite for Sales Agent"""

    @pytest.mark.asyncio
    async def test_sales_agent_process_order(self, test_db_path, test_customer_id):
        """Test order processing functionality"""
        response = await process_order(
            product_name="A4 paper",
            quantity=5,
            unit_price=0.05,
            customer_id=test_customer_id,
            db_path=test_db_path,
        )

        assert isinstance(response, str)
        assert len(response) > 0
        # Should contain transaction information
        assert any(
            keyword in response.lower()
            for keyword in ["transaction", "order", "completed", "processed"]
        )

    @pytest.mark.asyncio
    async def test_sales_agent_insufficient_stock(self, test_db_path, test_customer_id):
        """Test order processing with insufficient stock"""
        # Try to order more than available
        response = await process_order(
            product_name="A4 paper",
            quantity=100000,  # Unrealistically large quantity
            unit_price=0.05,
            customer_id=test_customer_id,
            db_path=test_db_path,
        )

        assert isinstance(response, str)
        assert len(response) > 0
        # Should indicate insufficient stock
        assert any(
            keyword in response.lower()
            for keyword in ["insufficient", "not enough", "stock", "available"]
        )


class TestReorderingAgent:
    """Test suite for Reordering Agent"""

    @pytest.mark.asyncio
    async def test_reordering_agent_check(self, test_db_path):
        """Test reorder check functionality"""
        response = await trigger_reorder_check(auto_approve=True, db_path=test_db_path)

        assert isinstance(response, str)
        assert len(response) > 0
        # Should contain reorder information
        assert any(
            keyword in response.lower() for keyword in ["reorder", "stock", "supplier", "order"]
        )

    @pytest.mark.asyncio
    async def test_reordering_agent_manual_mode(self, test_db_path):
        """Test reorder check in manual approval mode"""
        response = await trigger_reorder_check(auto_approve=False, db_path=test_db_path)

        assert isinstance(response, str)
        assert len(response) > 0


class TestOrchestratorAgent:
    """Test suite for Orchestrator Agent"""

    @pytest.mark.asyncio
    async def test_orchestrator_inventory_query(self, test_db_path, test_customer_id):
        """Test orchestrator routing inventory queries"""
        response = await handle_customer_request(
            request_text="What products do you have available?",
            customer_id=test_customer_id,
            db_path=test_db_path,
        )

        assert isinstance(response, str)
        assert len(response) > 0
        # Should route to inventory agent
        assert any(
            keyword in response.lower()
            for keyword in ["inventory", "stock", "available", "product"]
        )

    @pytest.mark.asyncio
    async def test_orchestrator_quote_request(self, test_db_path, test_customer_id):
        """Test orchestrator routing quote requests"""
        response = await handle_customer_request(
            request_text="I need a quote for 100 sheets of A4 paper",
            customer_id=test_customer_id,
            db_path=test_db_path,
        )

        assert isinstance(response, str)
        assert len(response) > 0
        # Should route to quoting agent
        assert any(
            keyword in response.lower() for keyword in ["quote", "price", "total", "discount"]
        )

    @pytest.mark.asyncio
    async def test_orchestrator_order_request(self, test_db_path, test_customer_id):
        """Test orchestrator routing order requests"""
        response = await handle_customer_request(
            request_text="I want to place an order for 50 sheets of A4 paper",
            customer_id=test_customer_id,
            db_path=test_db_path,
        )

        assert isinstance(response, str)
        assert len(response) > 0
        # Should route to sales agent
        assert any(
            keyword in response.lower() for keyword in ["order", "transaction", "purchase", "buy"]
        )

    @pytest.mark.asyncio
    async def test_orchestrator_complex_request(self, test_db_path, test_customer_id):
        """Test orchestrator handling complex multi-step requests"""
        response = await handle_customer_request(
            request_text="I need to check if you have A4 paper, get a quote for 200 sheets, and then place an order",
            customer_id=test_customer_id,
            db_path=test_db_path,
        )

        assert isinstance(response, str)
        assert len(response) > 0
        # Should coordinate multiple agents
        assert len(response) > 100  # Complex response should be longer


class TestAgentIntegration:
    """Test suite for agent integration scenarios"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self, test_db_path, test_customer_id):
        """Test complete workflow from quote to order"""
        # Step 1: Get quote
        quote_response = await request_quote(
            product_name="A4 paper", quantity=25, customer_id=test_customer_id, db_path=test_db_path
        )

        assert isinstance(quote_response, str)
        assert len(quote_response) > 0

        # Step 2: Process order
        order_response = await process_order(
            product_name="A4 paper",
            quantity=25,
            unit_price=0.05,
            customer_id=test_customer_id,
            db_path=test_db_path,
        )

        assert isinstance(order_response, str)
        assert len(order_response) > 0

        # Step 3: Check if reorder was triggered
        reorder_response = await trigger_reorder_check(auto_approve=True, db_path=test_db_path)

        assert isinstance(reorder_response, str)
        assert len(reorder_response) > 0

    @pytest.mark.asyncio
    async def test_error_handling(self, test_db_path, test_customer_id):
        """Test error handling across agents"""
        # Test with invalid product
        response = await handle_customer_request(
            request_text="I want to buy 100 units of 'Invalid Product Name'",
            customer_id=test_customer_id,
            db_path=test_db_path,
        )

        assert isinstance(response, str)
        assert len(response) > 0
        # Should handle error gracefully
        assert any(
            keyword in response.lower()
            for keyword in ["error", "not found", "unavailable", "sorry"]
        )


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
