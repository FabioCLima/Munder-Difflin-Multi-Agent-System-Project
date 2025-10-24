"""
Pytest Configuration and Fixtures
Shared test fixtures and configurations for all test modules
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


# ============================================================================
# FIXTURES - Database
# ============================================================================


@pytest.fixture(scope="session")
def db_path():
    """
    Provide database path for testing.
    Scope: session - shared across all tests
    """
    return "munder_difflin.db"


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """
    Create a temporary database for isolated testing.
    Scope: session - created once per test session
    """
    db_dir = tmp_path_factory.mktemp("test_db")
    return str(db_dir / "test_munder_difflin.db")


# ============================================================================
# FIXTURES - Customer IDs
# ============================================================================


@pytest.fixture
def test_customer_id():
    """
    Provide a test customer ID.
    Scope: function - new ID for each test
    """
    return "TEST_CUSTOMER_001"


@pytest.fixture
def unique_customer_id():
    """
    Generate unique customer ID for each test.
    Scope: function
    """
    import uuid

    return f"TEST_{uuid.uuid4().hex[:8].upper()}"


# ============================================================================
# FIXTURES - Agent Dependencies
# ============================================================================


@pytest.fixture
def inventory_deps(db_path):
    """Create Inventory Agent dependencies"""
    from src.dependencies import InventoryDependencies

    return InventoryDependencies(db_path=db_path)


@pytest.fixture
def quoting_deps(db_path, test_customer_id):
    """Create Quoting Agent dependencies"""
    from src.dependencies import QuotingDependencies

    return QuotingDependencies(db_path=db_path, customer_id=test_customer_id)


@pytest.fixture
def sales_deps(db_path, test_customer_id):
    """Create Sales Agent dependencies"""
    from src.dependencies import SalesDependencies

    return SalesDependencies(db_path=db_path, customer_id=test_customer_id)


@pytest.fixture
def reordering_deps(db_path):
    """Create Reordering Agent dependencies"""
    from src.dependencies import ReorderingDependencies

    return ReorderingDependencies(
        db_path=db_path,
        auto_approve=False,  # Manual approval for testing
    )


# ============================================================================
# FIXTURES - Test Data
# ============================================================================


@pytest.fixture
def sample_products():
    """Provide sample product names for testing"""
    return [
        "Standard Copy Paper",
        "Premium Copy Paper",
        "Recycled Copy Paper",
        "Dunder Mifflin Premium Copy Paper",
    ]


@pytest.fixture
def sample_quantities():
    """Provide sample quantities for discount testing"""
    return {
        "no_discount": 25,
        "tier_2pct": 100,
        "tier_5pct": 300,
        "tier_10pct": 750,
        "tier_15pct": 1500,
    }


@pytest.fixture
def sample_quote_request():
    """Provide a sample quote request"""
    return {
        "customer_id": "TEST_QUOTE_001",
        "product_name": "Standard Copy Paper",
        "quantity": 100,
    }


# ============================================================================
# FIXTURES - Event Loop (for async tests)
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for async tests.
    Required for pytest-asyncio
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# HOOKS - Test Execution
# ============================================================================


def pytest_runtest_setup(item):
    """
    Hook called before each test.
    Can be used for setup/logging
    """
    if "asyncio" in item.keywords:
        # Ensure asyncio event loop is available
        pass


def pytest_runtest_teardown(item):
    """
    Hook called after each test.
    Can be used for cleanup
    """
    pass


# ============================================================================
# MARKERS - Custom Test Markers
# ============================================================================

# Example usage in tests:
# @pytest.mark.integration
# @pytest.mark.slow
# @pytest.mark.asyncio


# ============================================================================
# HELPER FUNCTIONS (available to all tests)
# ============================================================================


@pytest.fixture
def assert_response_valid():
    """Helper function to validate agent responses"""

    def _validate(response, required_keywords=None):
        """
        Validate that response is not None and contains required keywords

        Args:
            response: Agent response string
            required_keywords: List of keywords that should be in response
        """
        assert response is not None, "Response is None"
        assert len(response) > 0, "Response is empty"

        if required_keywords:
            for keyword in required_keywords:
                assert keyword.lower() in response.lower(), (
                    f"Required keyword '{keyword}' not found in response"
                )

        return True

    return _validate


@pytest.fixture
def extract_price_from_response():
    """Helper to extract price from agent response"""

    def _extract(response):
        """
        Extract dollar amounts from response

        Returns:
            List of float values found in response
        """
        import re

        prices = re.findall(r"\$[\d,]+\.?\d*", response)
        return [float(p.replace("$", "").replace(",", "")) for p in prices]

    return _extract


@pytest.fixture
def extract_quantity_from_response():
    """Helper to extract quantities from agent response"""

    def _extract(response):
        """
        Extract unit quantities from response

        Returns:
            List of integer values found
        """
        import re

        quantities = re.findall(r"(\d+)\s*units?", response, re.IGNORECASE)
        return [int(q) for q in quantities]

    return _extract


# ============================================================================
# PARAMETRIZE FIXTURES
# ============================================================================


@pytest.fixture(
    params=[
        ("Standard Copy Paper", 50),
        ("Premium Copy Paper", 100),
        ("Recycled Copy Paper", 200),
    ]
)
def product_quantity_pair(request):
    """
    Parametrized fixture for testing multiple product/quantity combinations

    Usage:
        def test_something(product_quantity_pair):
            product, quantity = product_quantity_pair
            # test logic
    """
    return request.param


# ============================================================================
# SKIP CONDITIONS
# ============================================================================


@pytest.fixture
def skip_if_no_database(db_path):
    """Skip test if database doesn't exist"""
    import os

    if not os.path.exists(db_path):
        pytest.skip(f"Database not found: {db_path}")


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================


@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    """Configure logging for tests"""
    import sys

    from loguru import logger

    # Remove default handler
    logger.remove()

    # Add test-specific handler
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="WARNING",  # Only show warnings and errors during tests
    )

    # Add file handler for test logs
    logger.add("pytest_execution.log", rotation="1 MB", level="DEBUG")

    yield logger

    # Cleanup after all tests
    logger.info("Test session completed")
