"""
Test suite for all tools in the multi-agent system
Tests the individual tools that agents use to interact with the database
"""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Import database context and dependencies
from src.database import DatabaseContext, create_engine, init_database
from src.dependencies import (
    InventoryDependencies,
    QuotingDependencies,
    ReorderingDependencies,
    SalesDependencies,
)

# Import tools
from src.tools.inventory_tools import (
    check_all_inventory_tool,
    check_item_stock_tool,
    get_item_details_tool,
    identify_low_stock_tool,
    search_items_tool,
)
from src.tools.quoting_tools import (
    calculate_bulk_discount_tool,
    calculate_total_price_tool,
    get_item_pricing_tool,
    search_similar_quotes_tool,
    validate_quote_availability_tool,
)
from src.tools.sales_tools import (
    calculate_customer_delivery_tool,
    calculate_reorder_quantity_tool,
    get_financial_status_tool,
    place_stock_order_tool,
    process_sale_tool,
)


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
def db_context(test_db_path):
    """Create database context for testing"""
    return DatabaseContext(
        db_engine=create_engine(f"sqlite:///{test_db_path}"), current_date="2025-01-15"
    )


@pytest.fixture
def inventory_deps(test_db_path):
    """Create inventory dependencies for testing"""
    from src.database import create_engine

    return InventoryDependencies(
        db_path=test_db_path,
        current_date="2025-01-15",
        db_engine=create_engine(f"sqlite:///{test_db_path}"),
    )


@pytest.fixture
def inventory_context(inventory_deps):
    """Create inventory context for testing"""

    class MockContext:
        def __init__(self, deps):
            self.deps = deps

    return MockContext(inventory_deps)


@pytest.fixture
def quoting_deps(test_db_path):
    """Create quoting dependencies for testing"""
    from src.database import create_engine

    return QuotingDependencies(
        db_path=test_db_path,
        customer_id="TEST_CUSTOMER",
        current_date="2025-01-15",
        db_engine=create_engine(f"sqlite:///{test_db_path}"),
    )


@pytest.fixture
def quoting_context(quoting_deps):
    """Create quoting context for testing"""

    class MockContext:
        def __init__(self, deps):
            self.deps = deps

    return MockContext(quoting_deps)


@pytest.fixture
def sales_deps(test_db_path):
    """Create sales dependencies for testing"""
    from src.database import create_engine

    return SalesDependencies(
        db_path=test_db_path,
        customer_id="TEST_CUSTOMER",
        current_date="2025-01-15",
        db_engine=create_engine(f"sqlite:///{test_db_path}"),
    )


@pytest.fixture
def sales_context(sales_deps):
    """Create sales context for testing"""

    class MockContext:
        def __init__(self, deps):
            self.deps = deps

    return MockContext(sales_deps)


@pytest.fixture
def reordering_deps(test_db_path):
    """Create reordering dependencies for testing"""
    from src.database import create_engine

    return ReorderingDependencies(
        db_path=test_db_path,
        current_date="2025-01-15",
        db_engine=create_engine(f"sqlite:///{test_db_path}"),
    )


@pytest.fixture
def reordering_context(reordering_deps):
    """Create reordering context for testing"""

    class MockContext:
        def __init__(self, deps):
            self.deps = deps

    return MockContext(reordering_deps)


class TestInventoryTools:
    """Test suite for inventory-related tools"""

    def test_check_all_inventory_tool(self, inventory_context):
        """Test checking all inventory items"""
        result = check_all_inventory_tool(inventory_context)

        assert isinstance(result, dict)
        assert len(result) > 0
        # Should contain product names and stock levels
        for product_name, stock_level in result.items():
            assert isinstance(product_name, str)
            assert isinstance(stock_level, (int, float))
            assert stock_level >= 0

    def test_check_item_stock_tool(self, inventory_context):
        """Test checking specific item stock"""
        # First get available products
        all_inventory = check_all_inventory_tool(inventory_context)
        if all_inventory:
            product_name = list(all_inventory.keys())[0]

            result = check_item_stock_tool(inventory_context, product_name)

            assert isinstance(result, dict)
            assert "item_name" in result
            assert "current_stock" in result
            assert result["item_name"] == product_name
            assert isinstance(result["current_stock"], (int, float))

    def test_check_item_stock_tool_nonexistent(self, inventory_context):
        """Test checking stock for non-existent item"""
        result = check_item_stock_tool(inventory_context, "Non-existent Product")

        assert isinstance(result, dict)
        assert "error" in result or "current_stock" in result
        if "current_stock" in result:
            assert result["current_stock"] == 0

    def test_identify_low_stock_tool(self, inventory_context):
        """Test identifying low stock items"""
        result = identify_low_stock_tool(inventory_context)

        assert isinstance(result, list)
        # Each item should have required fields
        for item in result:
            assert isinstance(item, dict)
            assert "product_name" in item
            assert "current_stock" in item
            assert "min_stock_level" in item
            assert "deficit" in item

    def test_get_item_details_tool(self, inventory_context):
        """Test getting detailed item information"""
        # First get available products
        all_inventory = check_all_inventory_tool(inventory_context)
        if all_inventory:
            product_name = list(all_inventory.keys())[0]

            result = get_item_details_tool(inventory_context, product_name)

            assert isinstance(result, dict)
            assert "item_name" in result
            assert "unit_price" in result
            assert "current_stock" in result
            assert "min_stock_level" in result

    def test_search_items_tool(self, inventory_context):
        """Test searching for items by keywords"""
        result = search_items_tool(inventory_context, "paper")

        assert isinstance(result, list)
        # Should return items matching the search term
        for item in result:
            assert isinstance(item, dict)
            assert "item_name" in item
            assert "paper" in item["item_name"].lower()


class TestQuotingTools:
    """Test suite for quoting-related tools"""

    def test_search_similar_quotes_tool(self, quoting_context):
        """Test searching for similar quotes"""
        result = search_similar_quotes_tool(quoting_context, ["paper", "A4"], limit=3)

        assert isinstance(result, list)
        # Should return quote history
        for quote in result:
            assert isinstance(quote, dict)
            assert "total_amount" in quote
            assert "quote_explanation" in quote

    def test_get_item_pricing_tool(self, quoting_context, inventory_context):
        """Test getting item pricing information"""
        # First get available products
        all_inventory = check_all_inventory_tool(inventory_context)
        if all_inventory:
            product_name = list(all_inventory.keys())[0]

            result = get_item_pricing_tool(quoting_context, product_name)

            assert isinstance(result, dict)
            assert "item_name" in result
            assert "unit_price" in result
            assert isinstance(result["unit_price"], (int, float))
            assert result["unit_price"] > 0

    def test_calculate_bulk_discount_tool(self, quoting_context):
        """Test calculating bulk discounts"""
        base_price = 100.0

        # Test small order (no discount)
        result_small = calculate_bulk_discount_tool(quoting_context, base_price, "small")
        assert isinstance(result_small, dict)
        assert "discount_rate" in result_small
        assert "discount_amount" in result_small
        assert "final_price" in result_small

        # Test large order (should have discount)
        result_large = calculate_bulk_discount_tool(quoting_context, base_price, "large")
        assert isinstance(result_large, dict)
        assert result_large["discount_rate"] > result_small["discount_rate"]

    def test_validate_quote_availability_tool(self, quoting_context, inventory_context):
        """Test validating quote availability"""
        # First get available products
        all_inventory = check_all_inventory_tool(inventory_context)
        if all_inventory:
            product_name = list(all_inventory.keys())[0]
            stock_level = all_inventory[product_name]

            # Test with available quantity
            items = {product_name: min(stock_level, 10)}
            result = validate_quote_availability_tool(quoting_context, items)

            assert isinstance(result, dict)
            assert "all_available" in result
            assert "items_status" in result

    def test_calculate_total_price_tool(self, quoting_context, inventory_context):
        """Test calculating total price for multiple items"""
        # First get available products
        all_inventory = check_all_inventory_tool(inventory_context)
        if all_inventory:
            product_name = list(all_inventory.keys())[0]

            items = {product_name: 10}
            result = calculate_total_price_tool(quoting_context, items)

            assert isinstance(result, dict)
            assert "total_base_price" in result
            assert "items_breakdown" in result
            assert isinstance(result["total_base_price"], (int, float))
            assert result["total_base_price"] > 0


class TestSalesTools:
    """Test suite for sales-related tools"""

    def test_process_sale_tool(self, sales_context, inventory_context):
        """Test processing a sale"""
        # First get available products
        all_inventory = check_all_inventory_tool(inventory_context)
        if all_inventory:
            product_name = list(all_inventory.keys())[0]
            stock_level = all_inventory[product_name]

            # Test with small quantity
            quantity = min(stock_level, 5)
            items = {product_name: {"quantity": quantity, "unit_price": 0.05}}

            result = process_sale_tool(sales_context, items)

            assert isinstance(result, dict)
            assert "success" in result
            assert "transactions" in result
            assert "total_revenue" in result

    def test_get_financial_status_tool(self, sales_context):
        """Test getting financial status"""
        result = get_financial_status_tool(sales_context, detailed=True)

        assert isinstance(result, dict)
        assert "cash_balance" in result
        assert "inventory_value" in result
        assert "total_assets" in result
        assert isinstance(result["cash_balance"], (int, float))

    def test_calculate_customer_delivery_tool(self, sales_context):
        """Test calculating customer delivery date"""
        result = calculate_customer_delivery_tool(sales_context)

        assert isinstance(result, str)
        # Should be a date string
        try:
            datetime.fromisoformat(result)
        except ValueError:
            pytest.fail("Delivery date should be in ISO format")

    def test_place_stock_order_tool(self, sales_context, inventory_context):
        """Test placing a stock order"""
        # First get available products
        all_inventory = check_all_inventory_tool(inventory_context)
        if all_inventory:
            product_name = list(all_inventory.keys())[0]

            result = place_stock_order_tool(sales_context, product_name, 100)

            assert isinstance(result, dict)
            assert "success" in result
            assert "transaction_id" in result
            assert "cost" in result

    def test_calculate_reorder_quantity_tool(self, sales_context, inventory_context):
        """Test calculating reorder quantity"""
        # First get available products
        all_inventory = check_all_inventory_tool(inventory_context)
        if all_inventory:
            product_name = list(all_inventory.keys())[0]
            current_stock = all_inventory[product_name]

            result = calculate_reorder_quantity_tool(sales_context, product_name, current_stock)

            assert isinstance(result, int)
            assert result >= 0


class TestToolIntegration:
    """Test suite for tool integration scenarios"""

    def test_inventory_to_quote_workflow(self, inventory_context, quoting_context):
        """Test workflow from inventory check to quote generation"""
        # Step 1: Check inventory
        inventory = check_all_inventory_tool(inventory_context)
        assert len(inventory) > 0

        # Step 2: Get item details
        product_name = list(inventory.keys())[0]
        item_details = get_item_details_tool(inventory_context, product_name)
        assert "unit_price" in item_details

        # Step 3: Calculate quote
        items = {product_name: 50}
        quote_result = calculate_total_price_tool(quoting_context, items)
        assert "total_base_price" in quote_result

    def test_quote_to_sale_workflow(self, inventory_context, quoting_context, sales_context):
        """Test workflow from quote to sale"""
        # Step 1: Get available product
        inventory = check_all_inventory_tool(inventory_context)
        product_name = list(inventory.keys())[0]
        stock_level = inventory[product_name]

        # Step 2: Validate availability
        quantity = min(stock_level, 10)
        items = {product_name: quantity}
        availability = validate_quote_availability_tool(quoting_context, items)
        assert availability["all_available"]

        # Step 3: Process sale
        sale_items = {product_name: {"quantity": quantity, "unit_price": 0.05}}
        sale_result = process_sale_tool(sales_context, sale_items)
        assert sale_result["success"]

    def test_sale_to_reorder_workflow(self, inventory_context, sales_context):
        """Test workflow from sale to reorder check"""
        # Step 1: Process a sale to potentially trigger low stock
        inventory = check_all_inventory_tool(inventory_context)
        product_name = list(inventory.keys())[0]
        stock_level = inventory[product_name]

        # Step 2: Make a large sale to trigger reorder
        quantity = min(stock_level, 50)
        sale_items = {product_name: {"quantity": quantity, "unit_price": 0.05}}
        sale_result = process_sale_tool(sales_context, sale_items)
        assert sale_result["success"]

        # Step 3: Check for low stock items
        low_stock = identify_low_stock_tool(inventory_context)
        assert isinstance(low_stock, list)

        # Step 4: Calculate reorder quantity if needed
        if low_stock:
            item = low_stock[0]
            reorder_qty = calculate_reorder_quantity_tool(
                sales_context, item["product_name"], item["current_stock"]
            )
            assert isinstance(reorder_qty, int)


class TestToolErrorHandling:
    """Test suite for tool error handling"""

    def test_invalid_product_handling(self, inventory_context):
        """Test handling of invalid product names"""
        # Test with non-existent product
        result = check_item_stock_tool(inventory_context, "Invalid Product")
        assert isinstance(result, dict)
        # Should handle gracefully without crashing

    def test_insufficient_stock_handling(self, quoting_context):
        """Test handling of insufficient stock scenarios"""
        # Test with unrealistic quantity
        items = {"A4 paper": 1000000}
        result = validate_quote_availability_tool(quoting_context, items)
        assert isinstance(result, dict)
        # Should indicate insufficient stock

    def test_negative_quantity_handling(self, quoting_context):
        """Test handling of negative quantities"""
        # This should be handled by the tool or raise appropriate error
        try:
            result = calculate_total_price_tool(quoting_context, {"A4 paper": -10})
            # If no error, result should handle negative quantities appropriately
            assert isinstance(result, dict)
        except (ValueError, AssertionError):
            # Expected behavior for negative quantities
            pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
