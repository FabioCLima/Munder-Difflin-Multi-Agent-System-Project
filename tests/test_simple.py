"""
Teste simples para verificar se as dependências funcionam
"""

import shutil
import tempfile
from pathlib import Path

from src.agents.inventory_agent import InventoryDependencies
from src.database import create_engine, init_database


def test_inventory_dependencies():
    """Test creating inventory dependencies"""
    # Create temporary database
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"

    try:
        # Initialize database
        engine = create_engine(f"sqlite:///{db_path}")
        init_database(engine, seed=137)

        # Create dependencies
        deps = InventoryDependencies(
            db_path=str(db_path), current_date="2025-01-15", db_engine=engine
        )

        # Test that dependencies have required attributes
        assert deps.db_path == str(db_path)
        assert deps.current_date == "2025-01-15"
        assert deps.db_engine is not None

        print("✅ InventoryDependencies created successfully")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    test_inventory_dependencies()
