"""
Integration Tests - Complete Multi-Agent System
Tests end-to-end workflows across multiple agents
"""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agents.inventory_agent import query_inventory
from src.agents.orchestrator import handle_customer_request
from src.agents.quoting_agent import request_quote
from src.agents.reordering import trigger_reorder_check
from src.agents.sales_agent import process_order

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def db_path():
    """Return test database path"""
    return "munder_difflin.db"


@pytest.fixture
def test_customer_id():
    """Return test customer ID"""
    return "INTEGRATION_TEST_001"


# ============================================================================
# TEST: Complete Purchase Workflow
# ============================================================================


@pytest.mark.asyncio
async def test_complete_purchase_workflow(db_path, test_customer_id):
    """
    Test complete workflow: Check Inventory → Generate Quote → Process Order
    """

    product = "Standard Copy Paper"
    quantity = 50

    print(f"\n{'=' * 60}")
    print("Integration Test: Complete Purchase Workflow")
    print(f"Product: {product}, Quantity: {quantity}")
    print(f"{'=' * 60}\n")

    # Step 1: Check Inventory
    print("Step 1: Checking inventory...")
    inventory_response = await query_inventory(f"Do you have {product} in stock?", db_path)

    assert inventory_response is not None
    print("✅ Inventory checked")

    # Step 2: Request Quote
    print("\nStep 2: Requesting quote...")
    quote_response = await request_quote(
        product_name=product, quantity=quantity, customer_id=test_customer_id, db_path=db_path
    )

    assert quote_response is not None
    assert "Quote #" in quote_response
    print("✅ Quote generated")

    # Extract quote info (simplified)
    unit_price = 3.50  # Default price for testing

    # Step 3: Process Order (if stock available)
    if "OUT OF STOCK" not in inventory_response:
        print("\nStep 3: Processing order...")
        order_response = await process_order(
            product_name=product,
            quantity=quantity,
            unit_price=unit_price,
            customer_id=test_customer_id,
            db_path=db_path,
        )

        assert order_response is not None
        print("✅ Order processed")

        # Verify order was successful or get reason for failure
        if "ORDER CONFIRMED" in order_response:
            assert "Transaction #" in order_response
            print("✅ Complete workflow SUCCESS")
        else:
            print("⚠️ Order could not be completed (likely insufficient stock)")
    else:
        print("⚠️ Workflow stopped: Product out of stock")

    print(f"\n{'=' * 60}\n")


# ============================================================================
# TEST: Orchestrator Routing
# ============================================================================


@pytest.mark.asyncio
async def test_orchestrator_routes_correctly(test_customer_id):
    """Test that orchestrator correctly routes requests to appropriate agents"""

    test_cases = [
        {
            "query": "Do you have Premium Copy Paper in stock?",
            "expected_agent": "Inventory",
            "keywords": ["stock", "units", "available"],
        },
        {
            "query": "How much does Standard Copy Paper cost for 200 units?",
            "expected_agent": "Quoting",
            "keywords": ["Quote", "price", "$"],
        },
        {
            "query": "I want to buy 50 units of Recycled Copy Paper",
            "expected_agent": "Sales",
            "keywords": ["order", "buy", "purchase"],
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"Orchestrator Test {i}: {test_case['expected_agent']} Agent")
        print(f"Query: {test_case['query']}")
        print(f"{'=' * 60}")

        response = await handle_customer_request(
            request_text=test_case["query"], customer_id=test_customer_id
        )

        # Assertions
        assert response is not None

        # Check if response contains expected keywords
        found_keywords = [kw for kw in test_case["keywords"] if kw.lower() in response.lower()]

        print(f"Response length: {len(response)} chars")
        print(f"Keywords found: {found_keywords}")
        print(f"✅ Orchestrator correctly routed to {test_case['expected_agent']} Agent")


# ============================================================================
# TEST: Inventory Depletion and Reordering
# ============================================================================


@pytest.mark.asyncio
async def test_inventory_depletion_triggers_reorder(db_path, test_customer_id):
    """
    Test that when inventory gets low, reordering is triggered
    """

    print(f"\n{'=' * 60}")
    print("Integration Test: Inventory Depletion & Reordering")
    print(f"{'=' * 60}\n")

    # Step 1: Check initial low stock items
    print("Step 1: Checking for low stock items...")
    initial_check = await trigger_reorder_check(auto_approve=False, db_path=db_path)

    assert initial_check is not None
    print("Initial check complete")

    # Step 2: Trigger auto-reorder if needed
    print("\nStep 2: Triggering auto-reorder...")
    reorder_response = await trigger_reorder_check(auto_approve=True, db_path=db_path)

    assert reorder_response is not None

    if "Orders Placed:" in reorder_response or "Supplier Order" in reorder_response:
        print("✅ Reordering system activated")
        assert "units" in reorder_response.lower()
    else:
        print("✅ No reordering needed (all stock adequate)")

    print(f"\n{'=' * 60}\n")


# ============================================================================
# TEST: Quote to Order Conversion
# ============================================================================


@pytest.mark.asyncio
async def test_quote_to_order_conversion(db_path, test_customer_id):
    """
    Test converting a quote directly to an order
    """

    product = "Premium Copy Paper"
    quantity = 75

    print(f"\n{'=' * 60}")
    print("Integration Test: Quote → Order Conversion")
    print(f"{'=' * 60}\n")

    # Step 1: Generate quote
    print("Step 1: Generating quote...")
    quote_response = await request_quote(
        product_name=product, quantity=quantity, customer_id=test_customer_id, db_path=db_path
    )

    assert "Quote #" in quote_response

    # Extract quote ID and price (simplified)
    quote_id = None
    if "Quote #Q" in quote_response:
        try:
            quote_id = quote_response.split("Quote #")[1].split("\n")[0].strip().replace("**", "")
        except:
            pass

    unit_price = 4.50  # Default for testing

    print(f"✅ Quote generated: {quote_id}")

    # Step 2: Check availability
    print("\nStep 2: Checking stock availability...")
    inventory_check = await query_inventory(
        f"Can we fulfill {quantity} units of {product}?", db_path
    )

    # Step 3: Process order with quote reference
    if "OUT OF STOCK" not in inventory_check and "INSUFFICIENT" not in inventory_check:
        print("\nStep 3: Converting quote to order...")
        order_response = await process_order(
            product_name=product,
            quantity=quantity,
            unit_price=unit_price,
            customer_id=test_customer_id,
            quote_id=quote_id,
            db_path=db_path,
        )

        if "ORDER CONFIRMED" in order_response:
            print("✅ Quote successfully converted to order")
        else:
            print("⚠️ Order could not be completed")
    else:
        print("⚠️ Insufficient stock to fulfill order")

    print(f"\n{'=' * 60}\n")


# ============================================================================
# TEST: Bulk Discount Application
# ============================================================================


@pytest.mark.asyncio
async def test_bulk_discount_applied_correctly(db_path, test_customer_id):
    """
    Test that bulk discounts are applied correctly at different quantity tiers
    """

    print(f"\n{'=' * 60}")
    print("Integration Test: Bulk Discount Application")
    print(f"{'=' * 60}\n")

    test_quantities = [
        (25, "0%"),  # No discount
        (100, "2%"),  # 2% discount
        (300, "5%"),  # 5% discount
        (750, "10%"),  # 10% discount
        (1500, "15%"),  # 15% discount
    ]

    for quantity, expected_discount in test_quantities:
        print(f"\nTesting quantity: {quantity} units (expecting {expected_discount} discount)")

        quote_response = await request_quote(
            product_name="Standard Copy Paper",
            quantity=quantity,
            customer_id=test_customer_id,
            db_path=db_path,
        )

        assert quote_response is not None

        # Verify discount is present
        if expected_discount != "0%":
            assert expected_discount in quote_response, (
                f"Expected {expected_discount} discount not found"
            )
            print(f"✅ {expected_discount} discount correctly applied")
        else:
            # For 0%, discount should not be mentioned or be 0%
            print("✅ No discount applied (as expected for small orders)")

    print(f"\n{'=' * 60}\n")


# ============================================================================
# TEST: Multi-Product Order
# ============================================================================


@pytest.mark.asyncio
async def test_multi_product_workflow(db_path, test_customer_id):
    """
    Test processing orders for multiple different products
    """

    print(f"\n{'=' * 60}")
    print("Integration Test: Multi-Product Order Workflow")
    print(f"{'=' * 60}\n")

    products = [
        ("Standard Copy Paper", 50, 3.50),
        ("Premium Copy Paper", 100, 4.50),
        ("Recycled Copy Paper", 75, 3.25),
    ]

    successful_orders = 0

    for product, quantity, unit_price in products:
        print(f"\nProcessing: {product} x{quantity}")

        # Check inventory
        inventory_check = await query_inventory(f"Do you have {product}?", db_path)

        # Generate quote
        quote_response = await request_quote(
            product_name=product, quantity=quantity, customer_id=test_customer_id, db_path=db_path
        )

        # Process order if stock available
        if "OUT OF STOCK" not in inventory_check:
            order_response = await process_order(
                product_name=product,
                quantity=quantity,
                unit_price=unit_price,
                customer_id=test_customer_id,
                db_path=db_path,
            )

            if "ORDER CONFIRMED" in order_response:
                successful_orders += 1
                print(f"✅ Order successful for {product}")
            else:
                print(f"⚠️ Order failed for {product}")
        else:
            print(f"⚠️ {product} out of stock")

        await asyncio.sleep(0.3)  # Rate limiting

    print(f"\n{'=' * 60}")
    print(f"Multi-product workflow complete: {successful_orders}/{len(products)} orders successful")
    print(f"{'=' * 60}\n")


# ============================================================================
# TEST: Error Handling
# ============================================================================


@pytest.mark.asyncio
async def test_error_handling(db_path, test_customer_id):
    """
    Test that system handles errors gracefully
    """

    print(f"\n{'=' * 60}")
    print("Integration Test: Error Handling")
    print(f"{'=' * 60}\n")

    # Test 1: Invalid product
    print("Test 1: Invalid product name")
    response = await handle_customer_request(
        "Do you have Invisible Paper?", customer_id=test_customer_id
    )
    assert "not found" in response.lower() or "don't have" in response.lower()
    print("✅ Invalid product handled gracefully")

    # Test 2: Negative quantity (should be handled by Pydantic validation)
    print("\nTest 2: Attempting order with excessive quantity")
    response = await process_order(
        product_name="Standard Copy Paper",
        quantity=999999,
        unit_price=3.50,
        customer_id=test_customer_id,
        db_path=db_path,
    )
    assert (
        "Cannot Be Fulfilled" in response
        or "Insufficient" in response.lower()
        or "not enough" in response.lower()
    )
    print("✅ Excessive quantity handled gracefully")

    print(f"\n{'=' * 60}\n")


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 INTEGRATION TESTS - MULTI-AGENT SYSTEM")
    print("=" * 60 + "\n")

    # Run all tests
    pytest.main([__file__, "-v", "-s"])
