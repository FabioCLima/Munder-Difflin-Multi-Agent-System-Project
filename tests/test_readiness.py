"""
Test Readiness Checker
Validates that all prerequisites are met before running tests
"""

import subprocess
import sys
from pathlib import Path


def print_header(text, char="="):
    """Print formatted header"""
    print(f"\n{char * 70}")
    print(f"  {text}")
    print(f"{char * 70}\n")


def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")

    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} (Need Python 3.11+)")
        return False


def check_required_packages():
    """Check if required packages are installed"""
    print("\n📦 Checking required packages...")

    required = [
        "pydantic_ai",
        "pydantic",
        "loguru",
        "pandas",
        "openai",
        "sqlalchemy",
        "pytest",
        "pytest_asyncio",
    ]

    all_installed = True

    for package in required:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (MISSING)")
            all_installed = False

    return all_installed


def check_project_structure():
    """Check if project structure is correct"""
    print("\n📁 Checking project structure...")

    required_paths = [
        "src/agents/orchestrator.py",
        "src/agents/inventory_agent.py",
        "src/agents/quoting_agent.py",
        "src/agents/sales_agent.py",
        "src/agents/reordering_agent.py",
        "tests/test_inventory_agent.py",
        "tests/test_quoting_agent.py",
        "tests/test_sales_agent.py",
        "tests/test_integration.py",
        "tests/conftest.py",
        "test_complete_system.py",
        "run_all_tests.py",
    ]

    all_exist = True

    for path in required_paths:
        if Path(path).exists():
            print(f"   ✅ {path}")
        else:
            print(f"   ❌ {path} (MISSING)")
            all_exist = False

    return all_exist


def check_data_files():
    """Check if data files exist"""
    print("\n📊 Checking data files...")

    data_files = [
        "data/quote_requests_sample.csv",
        "data/quotes.csv",
        "data/quote_requests.csv",
    ]

    all_exist = True

    for file in data_files:
        if Path(file).exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ⚠️  {file} (NOT FOUND)")
            # Not critical for some files
            if "sample" in file:
                all_exist = False

    return all_exist


def check_database():
    """Check if database exists and is accessible"""
    print("\n🗄️  Checking database...")

    db_path = Path("munder_difflin.db")

    if db_path.exists():
        print("   ✅ munder_difflin.db exists")

        # Try to connect
        try:
            import sqlite3

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            required_tables = ["inventory", "transactions", "quotes"]
            found_tables = [t[0] for t in tables]

            for table in required_tables:
                if table in found_tables:
                    print(f"   ✅ Table '{table}' exists")
                else:
                    print(f"   ❌ Table '{table}' missing")

            conn.close()
            return all(t in found_tables for t in required_tables)

        except Exception as e:
            print(f"   ❌ Database error: {e}")
            return False
    else:
        print("   ❌ munder_difflin.db not found")
        print("   ℹ️  Run 'python src/project_starter.py' to create it")
        return False


def check_environment_variables():
    """Check for required environment variables"""
    print("\n🔑 Checking environment variables...")

    import os

    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")

    if api_key:
        masked_key = api_key[:8] + "..." + api_key[-4:]
        print(f"   ✅ OPENAI_API_KEY: {masked_key}")
        return True
    else:
        print("   ❌ OPENAI_API_KEY not found")
        print("   ℹ️  Create a .env file with: OPENAI_API_KEY=your-key-here")
        return False


def check_pytest_executable():
    """Check if pytest can run"""
    print("\n🧪 Checking pytest...")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--version"], capture_output=True, text=True
        )

        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"   ✅ {version}")
            return True
        else:
            print("   ❌ pytest not working")
            return False
    except Exception as e:
        print(f"   ❌ pytest error: {e}")
        return False


def provide_recommendations(results):
    """Provide recommendations based on check results"""
    print_header("📋 RECOMMENDATIONS", "=")

    if all(results.values()):
        print("🎉 All checks passed! You're ready to run tests.\n")
        print("Next steps:")
        print("  1. Run all tests:  python run_all_tests.py")
        print("  2. Or run system test:  python test_complete_system.py")
        print("  3. Or run unit tests:  pytest tests/ -v")
        return True
    else:
        print("⚠️  Some checks failed. Please fix the issues above.\n")
        print("Common fixes:")

        if not results["packages"]:
            print('  • Install packages: pip install -e ".[dev]"')

        if not results["database"]:
            print("  • Create database: python src/project_starter.py")

        if not results["data_files"]:
            print("  • Ensure data files are in data/ directory")

        if not results["env_vars"]:
            print("  • Create .env file with OPENAI_API_KEY")

        print("\nAfter fixing, run this script again:")
        print("  python check_test_readiness.py")

        return False


def main():
    """Run all checks"""
    print_header("🔍 TEST READINESS CHECK", "=")
    print("Validating system prerequisites...\n")

    results = {
        "python": check_python_version(),
        "packages": check_required_packages(),
        "structure": check_project_structure(),
        "data_files": check_data_files(),
        "database": check_database(),
        "env_vars": check_environment_variables(),
        "pytest": check_pytest_executable(),
    }

    # Summary
    print_header("📊 SUMMARY", "=")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    print(f"Checks passed: {passed}/{total}\n")

    for check, status in results.items():
        emoji = "✅" if status else "❌"
        print(f"  {emoji} {check.replace('_', ' ').title()}")

    # Recommendations
    ready = provide_recommendations(results)

    # Exit code
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
