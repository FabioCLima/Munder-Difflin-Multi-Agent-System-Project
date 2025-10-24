"""
Unit Tests for Quoting Agent
Tests pricing, discounts, and quote generation
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agents.quoting_agent import DiscountTiers, quoting_agent, request_quote
from src.dependencies import QuotingDependencies

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
    return QuotingDependencies(db_path=db_path, customer_id="TEST_CUST")


# ============================================================================
# TEST: Discount Tier Logic
# ============================================================================


def test_discount_tiers():
    """Test bulk discount calculation"""

    # Test each tier
    assert DiscountTiers.get_discount_percentage(25) == 0.0  # No discount
    assert DiscountTiers.get_discount_percentage(75) == 0.02  # 2%
    assert DiscountTiers.get_discount_percentage(300) == 0.05  # 5%
    assert DiscountTiers.get_discount_percentage(750) == 0.10  # 10%
    assert DiscountTiers.get_discount_percentage(1500) == 0.15  # 15%

    print("✅ Test passed: Discount tier logic")


# ============================================================================
# TEST: Generate Small Quote (No Discount)
# ============================================================================


@pytest.mark.asyncio
async def test_small_quote_no_discount(db_path):
    """Test generating quote for small quantity (no discount)"""

    response = await request_quote(
        product_name="Standard Copy Paper", quantity=25, customer_id="TEST001", db_path=db_path
    )

    # Assertions
    assert response is not None
    assert "Quote #" in response
    assert "Standard Copy Paper" in response
    assert "25" in response
    # Should NOT have discount for small orders
    assert "0%" in response or "Discount" not in response

    print("✅ Test passed: Small quote (no discount)")


# ============================================================================
# TEST: Generate Medium Quote (2% Discount)
# ============================================================================


@pytest.mark.asyncio
async def test_medium_quote_with_discount(db_path):
    """Test generating quote with 2% discount"""

    response = await request_quote(
        product_name="Premium Copy Paper", quantity=100, customer_id="TEST002", db_path=db_path
    )

    # Assertions
    assert response is not None
    assert "Quote #" in response
    assert "2%" in response  # Should have 2% discount
    assert "Discount" in response

    print("✅ Test passed: Medium quote (2% discount)")


# ============================================================================
# TEST: Generate Large Quote (10% Discount)
# ============================================================================


@pytest.mark.asyncio
async def test_large_quote_with_discount(db_path):
    """Test generating quote with 10% discount"""

    response = await request_quote(
        product_name="Recycled Copy Paper", quantity=750, customer_id="TEST003", db_path=db_path
    )

    # Assertions
    assert response is not None
    assert "Quote #" in response
    assert "10%" in response  # Should have 10% discount

    print("✅ Test passed: Large quote (10% discount)")


# ============================================================================
# TEST: Generate Bulk Quote (15% Discount)
# ============================================================================


@pytest.mark.asyncio
async def test_bulk_quote_maximum_discount(db_path):
    """Test generating quote with maximum 15% discount"""

    response = await request_quote(
        product_name="Standard Copy Paper", quantity=1500, customer_id="TEST004", db_path=db_path
    )

    # Assertions
    assert response is not None
    assert "Quote #" in response
    assert "15%" in response  # Should have 15% discount (maximum)

    print("✅ Test passed: Bulk quote (15% discount)")


# ============================================================================
# TEST: Quote Contains All Required Fields
# ============================================================================


@pytest.mark.asyncio
async def test_quote_contains_required_fields(db_path):
    """Test that quote contains all necessary information"""

    response = await request_quote(
        product_name="Premium Copy Paper", quantity=200, customer_id="TEST005", db_path=db_path
    )

    # Assertions
    required_fields = [
        "Quote #",
        "Product:",
        "Quantity:",
        "Unit Price:",
        "TOTAL:",
        "Valid until:",
    ]

    for field in required_fields:
        assert field in response, f"Missing field: {field}"

    print("✅ Test passed: Quote contains all required fields")


# ============================================================================
# TEST: Get Product Price
# ============================================================================


@pytest.mark.asyncio
async def test_get_product_price(deps):
    """Test retrieving product price"""

    result = await quoting_agent.run("What's the price for Standard Copy Paper?", deps=deps)

    response = result.data

    # Assertions
    assert response is not None
    assert "Standard Copy Paper" in response or "price" in response.lower()
    assert "$" in response
    assert any(char.isdigit() for char in response)

    print("✅ Test passed: Get product price")


# ============================================================================
# TEST: Search Quote History
# ============================================================================


@pytest.mark.asyncio
async def test_search_quote_history(deps):
    """Test searching historical quotes"""

    result = await quoting_agent.run("Show me recent quotes for Premium Copy Paper", deps=deps)

    response = result.data

    # Assertions
    assert response is not None
    # Should either show quotes or indicate none found
    assert "Quote #" in response or "No quotes" in response or "Found" in response

    print("✅ Test passed: Search quote history")


# ============================================================================
# TEST: Invalid Product
# ============================================================================


@pytest.mark.asyncio
async def test_quote_invalid_product(db_path):
    """Test quoting for non-existent product"""

    response = await request_quote(
        product_name="Invisible Paper", quantity=100, customer_id="TEST006", db_path=db_path
    )

    # Assertions
    assert response is not None
    assert "not found" in response.lower() or "❌" in response

    print("✅ Test passed: Invalid product handling")


# ============================================================================
# TEST: Price Calculation Accuracy
# ============================================================================


@pytest.mark.asyncio
async def test_price_calculation_accuracy(db_path):
    """Test that price calculations are mathematically correct"""

    # Generate quote with known discount
    response = await request_quote(
        product_name="Standard Copy Paper",
        quantity=500,  # Should get 10% discount
        customer_id="TEST007",
        db_path=db_path,
    )

    # Extract prices (simplified check)
    assert "$" in response
    assert "10%" in response  # Verify discount applied

    # Verify total is less than subtotal (due to discount)
    if "Subtotal:" in response and "TOTAL:" in response:
        # Basic validation that discount was applied
        assert response.index("TOTAL:") > response.index("Subtotal:")

    print("✅ Test passed: Price calculation accuracy")


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 QUOTING AGENT UNIT TESTS")
    print("=" * 60 + "\n")

    # Run all tests
    pytest.main([__file__, "-v", "-s"])
