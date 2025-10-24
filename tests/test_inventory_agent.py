"""
Unit Tests for Inventory Agent
Tests all inventory management functionality
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agents.inventory_agent import inventory_agent, query_inventory
from src.dependencies import InventoryDependencies

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def db_path():
    """Return test database path"""
    return "munder_difflin.db"


@pytest.fixture
def deps(db_path):
    """Create dependencies for testing"""
    return InventoryDependencies(db_path=db_path)


# ============================================================================
# TEST: Get All Inventory
# ============================================================================


@pytest.mark.asyncio
async def test_get_all_inventory(db_path):
    """Test retrieving complete inventory list"""

    query = "Show me all products in inventory"
    response = await query_inventory(query, db_path)

    # Assertions
    assert response is not None
    assert "Inventory" in response or "inventory" in response
    assert len(response) > 50  # Should have substantial content

    print("✅ Test passed: Get all inventory")
    print(f"Response length: {len(response)} characters")


# ============================================================================
# TEST: Check Specific Product Stock
# ============================================================================


@pytest.mark.asyncio
async def test_check_specific_product(db_path):
    """Test checking stock for a specific product"""

    query = "Do you have Premium Copy Paper in stock?"
    response = await query_inventory(query, db_path)

    # Assertions
    assert response is not None
    assert "Premium Copy Paper" in response or "premium" in response.lower()
    assert any(status in response for status in ["IN STOCK", "OUT OF STOCK", "LOW STOCK"])

    print("✅ Test passed: Check specific product")


# ============================================================================
# TEST: Search Products (Fuzzy Search)
# ============================================================================


@pytest.mark.asyncio
async def test_search_products(db_path):
    """Test searching products with partial matching"""

    query = "Search for products with 'copy' in the name"
    response = await query_inventory(query, db_path)

    # Assertions
    assert response is not None
    assert "copy" in response.lower() or "Copy" in response

    print("✅ Test passed: Search products")


# ============================================================================
# TEST: Check Availability for Order
# ============================================================================


@pytest.mark.asyncio
async def test_check_availability_for_order(deps):
    """Test checking if product has sufficient stock for order"""

    result = await inventory_agent.run(
        "Check if we can fulfill an order for 50 units of Standard Copy Paper", deps=deps
    )

    response = result.data

    # Assertions
    assert response is not None
    assert any(word in response for word in ["AVAILABLE", "INSUFFICIENT", "OUT OF STOCK"])

    print("✅ Test passed: Check availability for order")


# ============================================================================
# TEST: Get Low Stock Items
# ============================================================================


@pytest.mark.asyncio
async def test_get_low_stock_items(db_path):
    """Test identifying items below minimum stock level"""

    query = "Which items are running low on stock?"
    response = await query_inventory(query, db_path)

    # Assertions
    assert response is not None
    # Should either list low items or confirm all items are stocked
    assert (
        "low" in response.lower()
        or "adequately" in response.lower()
        or "minimum" in response.lower()
    )

    print("✅ Test passed: Get low stock items")


# ============================================================================
# TEST: Product Not Found
# ============================================================================


@pytest.mark.asyncio
async def test_product_not_found(db_path):
    """Test handling of non-existent product"""

    query = "Do you have Unicorn Paper in stock?"
    response = await query_inventory(query, db_path)

    # Assertions
    assert response is not None
    assert "not found" in response.lower() or "❌" in response

    print("✅ Test passed: Product not found handling")


# ============================================================================
# TEST: Stock Level Numbers
# ============================================================================


@pytest.mark.asyncio
async def test_stock_level_contains_numbers(db_path):
    """Test that stock responses include actual numbers"""

    query = "How many units of Recycled Copy Paper do we have?"
    response = await query_inventory(query, db_path)

    # Assertions
    assert response is not None
    # Should contain numbers (digits)
    assert any(char.isdigit() for char in response)

    print("✅ Test passed: Stock level includes numbers")


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 INVENTORY AGENT UNIT TESTS")
    print("=" * 60 + "\n")

    # Run all tests
    pytest.main([__file__, "-v", "-s"])
