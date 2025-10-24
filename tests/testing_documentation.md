# 🧪 Testing Documentation - Munder Difflin Multi-Agent System

## Overview

This document describes the comprehensive testing suite for the Munder Difflin Multi-Agent System project.

---

## Test Structure

```
tests/
├── test_inventory_agent.py     # Unit tests for Inventory Agent
├── test_quoting_agent.py        # Unit tests for Quoting Agent  
├── test_sales_agent.py          # Unit tests for Sales Agent
├── test_integration.py          # Integration tests (end-to-end workflows)
└── conftest.py                  # Pytest configuration

Root level:
├── test_complete_system.py      # Main test: processes quote_requests_sample.csv
├── run_all_tests.py             # Master script to run all tests
└── test_results.csv             # Generated output with all test results
```

---

## Running Tests

### Option 1: Run All Tests at Once (Recommended)

```bash
python run_all_tests.py
```

This will:
1. ✅ Run all unit tests for each agent
2. ✅ Run integration tests
3. ✅ Process the complete dataset (`quote_requests_sample.csv`)
4. ✅ Generate `test_results.csv`
5. ✅ Display comprehensive summary

---

### Option 2: Run Individual Test Suites

#### Inventory Agent Tests
```bash
pytest tests/test_inventory_agent.py -v
```

Tests covered:
- ✅ Get all inventory
- ✅ Check specific product stock
- ✅ Search products (fuzzy matching)
- ✅ Check availability for orders
- ✅ Get low stock items
- ✅ Handle non-existent products

---

#### Quoting Agent Tests
```bash
pytest tests/test_quoting_agent.py -v
```

Tests covered:
- ✅ Discount tier logic (0%, 2%, 5%, 10%, 15%)
- ✅ Generate quotes with correct discounts
- ✅ Quote contains all required fields
- ✅ Get product pricing
- ✅ Search quote history
- ✅ Handle invalid products
- ✅ Price calculation accuracy

---

#### Sales Agent Tests
```bash
pytest tests/test_sales_agent.py -v
```

Tests covered:
- ✅ Successful order processing
- ✅ Handle insufficient stock
- ✅ Create transaction records
- ✅ Update inventory after orders
- ✅ Get cash balance
- ✅ Generate financial reports
- ✅ Transaction history
- ✅ Trigger reordering when low stock
- ✅ Order total calculations

---

#### Integration Tests
```bash
pytest tests/test_integration.py -v
```

Tests covered:
- ✅ Complete purchase workflow (Inventory → Quote → Order)
- ✅ Orchestrator routing to correct agents
- ✅ Inventory depletion triggers reordering
- ✅ Quote to order conversion
- ✅ Bulk discount application
- ✅ Multi-product orders
- ✅ Error handling

---

### Option 3: Run Complete System Test (Dataset Processing)

```bash
python test_complete_system.py
```

This processes `data/quote_requests_sample.csv` and:
1. ✅ Checks inventory for each product
2. ✅ Generates quotes with appropriate discounts
3. ✅ Processes orders
4. ✅ Triggers reordering when needed
5. ✅ Generates `test_results.csv` with all transactions
6. ✅ Evaluates against project rubric criteria

**Output Files:**
- `test_results.csv` - Detailed results for each request
- `evaluation_results.csv` - Rubric evaluation scores
- `test_execution.log` - Complete execution log

---

## Test Results Analysis

### Metrics Tracked

1. **Success Rates:**
   - Quote generation success rate
   - Order processing success rate
   - Overall success rate

2. **Financial Metrics:**
   - Total revenue generated
   - Total units sold
   - Average revenue per order

3. **Inventory Metrics:**
   - Inventory warnings (low/out of stock)
   - Reorder triggers
   - Stock level updates

4. **Pricing Metrics:**
   - Discount application rate
   - Average discount percentage
   - Pricing accuracy

---

## Expected Test Output

### ✅ Successful Test Run

```
📊 TEST SUMMARY
================================================================
Total Requests Processed: 20
Successful Quotes: 20
Successful Orders: 18
Failed Requests: 2
Success Rate: 90.00%

💰 FINANCIAL METRICS:
Total Revenue: $45,230.50
Total Units Sold: 12,450
Avg Revenue/Order: $2,512.81

📦 INVENTORY METRICS:
Inventory Warnings: 3
Reorder Triggers: 2
================================================================
```

---

## Project Rubric Evaluation

The system is evaluated against the following criteria:

### 1. Quote Generation Success Rate (Target: >90%)
- System should successfully generate quotes for most requests
- Includes price calculation and discount application

### 2. Order Processing Success Rate (Target: >80%)
- Orders should be processed when stock is available
- Proper handling of insufficient stock scenarios

### 3. Competitive Pricing (Target: >50% discount rate)
- Bulk discounts applied automatically
- Correct discount tiers (2%, 5%, 10%, 15%)

### 4. Inventory Management
- Automatic reordering when stock drops below minimum
- Proper stock level tracking

### 5. Revenue Generation
- Successful transactions generate revenue
- Financial reporting is accurate

---

## Troubleshooting

### Issue: Tests fail with "Module not found"

**Solution:**
```bash
# Ensure you're in the project root directory
cd ~/Workdir/udacity_projects/Munder-Difflin-Multi-Agent-System-Project

# Activate virtual environment
source .venv/bin/activate

# Verify installation
pip list | grep pydantic-ai
```

---

### Issue: Database not found

**Solution:**
```bash
# Run the project_starter.py to initialize database
python src/project_starter.py
```

---

### Issue: quote_requests_sample.csv not found

**Solution:**
```bash
# Ensure data file exists
ls data/quote_requests_sample.csv

# If missing, check original location
ls quote_requests_sample.csv
```

---

## Continuous Integration

For CI/CD pipelines:

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Run complete system test
python test_complete_system.py

# Check results
test $? -eq 0 && echo "Tests passed" || echo "Tests failed"
```

---

## Test Data

### Sample Quote Requests

The `quote_requests_sample.csv` should contain:

```csv
customer_id,product_name,quantity
CUST001,Dunder Mifflin Premium Copy Paper,500
CUST002,Standard Copy Paper,100
CUST003,Recycled Copy Paper,1000
...
```

---

## Performance Benchmarks

Expected execution times:
- Unit tests (per agent): 2-5 seconds
- Integration tests: 10-15 seconds
- Complete system test: 30-60 seconds
- All tests combined: 1-2 minutes

---

## Coverage Goals

Target code coverage: **>80%**

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html

# View report
open htmlcov/index.html
```

---

## Next Steps

After running tests:

1. ✅ Review `test_results.csv` for detailed results
2. ✅ Check `evaluation_results.csv` for rubric scores
3. ✅ Analyze `test_execution.log` for any warnings
4. ✅ Ensure all criteria are met
5. ✅ Submit project with confidence!

---

## Support

For issues or questions:
- Check logs in `test_execution.log`
- Review error messages in terminal output
- Verify database integrity
- Ensure all dependencies are installed

---

**Last Updated:** 2025-10-24
**Version:** 1.0.0