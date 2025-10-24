"""
Teste das ferramentas usando dependências separadas
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from src.database import create_engine, init_database
from src.dependencies import (
    InventoryDependencies,
    QuotingDependencies,
    ReorderingDependencies,
    SalesDependencies,
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
def inventory_deps(test_db_path):
    """Create inventory dependencies for testing"""
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


def test_inventory_dependencies_creation(inventory_deps):
    """Test that inventory dependencies are created correctly"""
    assert inventory_deps.db_path is not None
    assert inventory_deps.current_date == "2025-01-15"
    assert inventory_deps.db_engine is not None
    print("✅ InventoryDependencies created successfully")


def test_inventory_context_creation(inventory_context):
    """Test that inventory context is created correctly"""
    assert inventory_context.deps is not None
    assert inventory_context.deps.current_date == "2025-01-15"
    assert inventory_context.deps.db_engine is not None
    print("✅ InventoryContext created successfully")


def test_quoting_dependencies_creation(test_db_path):
    """Test that quoting dependencies are created correctly"""
    deps = QuotingDependencies(
        db_path=test_db_path,
        customer_id="TEST_CUSTOMER",
        current_date="2025-01-15",
        db_engine=create_engine(f"sqlite:///{test_db_path}"),
    )

    assert deps.db_path is not None
    assert deps.customer_id == "TEST_CUSTOMER"
    assert deps.current_date == "2025-01-15"
    assert deps.db_engine is not None
    print("✅ QuotingDependencies created successfully")


def test_sales_dependencies_creation(test_db_path):
    """Test that sales dependencies are created correctly"""
    deps = SalesDependencies(
        db_path=test_db_path,
        customer_id="TEST_CUSTOMER",
        current_date="2025-01-15",
        db_engine=create_engine(f"sqlite:///{test_db_path}"),
    )

    assert deps.db_path is not None
    assert deps.customer_id == "TEST_CUSTOMER"
    assert deps.current_date == "2025-01-15"
    assert deps.db_engine is not None
    print("✅ SalesDependencies created successfully")


def test_reordering_dependencies_creation(test_db_path):
    """Test that reordering dependencies are created correctly"""
    deps = ReorderingDependencies(
        db_path=test_db_path,
        current_date="2025-01-15",
        db_engine=create_engine(f"sqlite:///{test_db_path}"),
    )

    assert deps.db_path is not None
    assert deps.current_date == "2025-01-15"
    assert deps.db_engine is not None
    print("✅ ReorderingDependencies created successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
