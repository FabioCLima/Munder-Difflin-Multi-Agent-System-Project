"""
Teste apenas das dependências sem importar agentes
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from src.database import create_engine, init_database


def test_database_creation():
    """Test database creation and initialization"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"

    try:
        # Create engine
        engine = create_engine(f"sqlite:///{db_path}")
        assert engine is not None

        # Initialize database
        init_database(engine, seed=137)

        print("✅ Database created and initialized successfully")

    finally:
        shutil.rmtree(temp_dir)


def test_engine_creation():
    """Test engine creation"""
    engine = create_engine("sqlite:///:memory:")
    assert engine is not None
    print("✅ Engine created successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
