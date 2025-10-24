# 🧪 Testing Suite - Quick Start Guide

## Overview

This directory contains a comprehensive testing suite for the Munder Difflin Multi-Agent System project.

---

## 🚀 Quick Start (3 Steps)

### Step 1: Check if you're ready

```bash
python check_test_readiness.py
```

This will verify:
- ✅ Python version (3.11+)
- ✅ All packages installed
- ✅ Project structure
- ✅ Database exists
- ✅ Environment variables set

---

### Step 2: Run all tests

```bash
python run_all_tests.py
```

This executes:
1. ✅ Unit tests (Inventory, Quoting, Sales agents)
2. ✅ Integration tests (workflows)
3. ✅ Complete system test (dataset processing)
4. ✅ Generates `test_results.csv` **← PROJECT DELIVERABLE**

**Expected Duration:** ~1-2 minutes

---

### Step 3: Review results

```bash
# View main results
cat test_results.csv

# View rubric evaluation
cat evaluation_results.csv

# View execution log
cat test_execution.log
```

---

## 📂 File Structure

```
.
├── test_complete_system.py       # ⭐ Main test (generates test_results.csv)
├── run_all_tests.py               # Master test runner
├── check_test_readiness.py        # Pre-test validation
│
├── tests/
│   ├── conftest.py                # Pytest configuration
│   ├── test_inventory_agent.py    # Unit tests - Inventory
│   ├── test_quoting_agent.py      # Unit tests - Quoting
│   ├── test_sales_agent.py        # Unit tests - Sales
│   └── test_integration.py        # Integration tests
│
├── TESTING.md                     # Detailed testing guide
├── TEST_SUMMARY.md                # Comprehensive test overview
└── README_TESTS.md                # This file
```

---

## 🎯 What Each Test Does

### 1. **test_complete_system.py** (MAIN)

**Purpose:** Generate required `test_results.csv` file

**Process:**
1. Reads `data/quote_requests_sample.csv`
2. For each request:
   - ✅ Checks inventory
   - ✅ Generates quote
   - ✅ Processes order
   - ✅ Triggers reordering if needed
3. Saves all results to `test_results.csv`
4. Evaluates against project rubric

**Run individually:**
```bash
python test_complete_system.py
```

**Output:**
- `test_results.csv` ← Submit this!
- `evaluation_results.csv`
- `test_execution.log`

---

### 2. **Unit Tests**

**Purpose:** Validate individual agent functionality

**Run all unit tests:**
```bash
pytest tests/test_inventory_agent.py -v
pytest tests/test_quoting_agent.py -v
pytest tests/test_sales_agent.py -v
```

**What they test:**

#### Inventory Agent (7 tests)
- Get all inventory
- Check specific products
- Search products
- Check order availability
- Get low stock items
- Handle invalid products
- Verify stock numbers

#### Quoting Agent (10 tests)
- Discount tier logic (5 tiers)
- Small/medium/large quotes
- Required quote fields
- Price accuracy
- Quote history
- Invalid product handling

#### Sales Agent (10 tests)
- Order processing
- Stock constraints
- Transaction creation
- Inventory updates
- Financial reporting
- Reorder triggers
- Error handling

---

### 3. **Integration Tests**

**Purpose:** Validate complete workflows

**Run integration tests:**
```bash
pytest tests/test_integration.py -v
```

**What they test:**
- Complete purchase workflows
- Orchestrator routing
- Multi-agent coordination
- Reordering triggers
- Bulk discounts
- Multi-product orders
- Error handling

---

## 📊 Understanding Test Results

### test_results.csv Format

```csv
request_id,customer_id,product_name,quantity,
inventory_check,quote_success,quote_id,unit_price,
discount_pct,quoted_total,order_success,transaction_id,
order_total,reorder_triggered,failure_reason
```

**Key Metrics:**
- `quote_success`: TRUE/FALSE for each quote
- `order_success`: TRUE/FALSE for each order
- `discount_pct`: Applied discount percentage
- `reorder_triggered`: TRUE when reordering happens

---

### Success Criteria

Your system passes if:

| Metric | Target | How to Check |
|--------|--------|--------------|
| Quote Success Rate | >90% | Count TRUE in `quote_success` column |
| Order Success Rate | >80% | Count TRUE in `order_success` column |
| Discount Application | >50% | Count rows with `discount_pct` > 0 |
| Reorder Triggers | >0 | Count TRUE in `reorder_triggered` |
| Revenue Generated | >$0 | Sum `order_total` column |

---

## 🔧 Troubleshooting

### Issue: "Module not found"

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

---

### Issue: "Database not found"

**Solution:**
```bash
# Create database
python src/project_starter.py
```

---

### Issue: "quote_requests_sample.csv not found"

**Solution:**
```bash
# Check if file exists
ls data/quote_requests_sample.csv

# If missing, ensure it's in the correct location
mv quote_requests_sample.csv data/
```

---

### Issue: "OPENAI_API_KEY not found"

**Solution:**
```bash
# Create .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

---

### Issue: Tests are slow

**Expected:** 1-2 minutes for all tests

**If slower:**
- Check internet connection (OpenAI API calls)
- Reduce dataset size in `quote_requests_sample.csv`
- Run unit tests only: `pytest tests/ -v`

---

## 📝 Test Execution Order

### Recommended Order:

1. **Pre-check:**
   ```bash
   python check_test_readiness.py
   ```

2. **Unit tests** (optional, for detailed validation):
   ```bash
   pytest tests/ -v
   ```

3. **Complete system test** (required):
   ```bash
   python test_complete_system.py
   ```

4. **Review results:**
   ```bash
   cat test_results.csv
   ```

---

## 🎓 For Project Submission

### Required Deliverable

**File:** `test_results.csv`

**How to generate:**
```bash
python test_complete_system.py
```

**What it contains:**
- All processed quote requests
- Success/failure status
- Generated quotes
- Processed orders
- Reorder triggers
- Performance metrics

---

### Optional (but recommended)

**Additional files to include:**
- `evaluation_results.csv` - Rubric validation
- `test_execution.log` - Execution details
- All test scripts (demonstrates thorough testing)

---

## 📖 Additional Documentation

- **TESTING.md** - Comprehensive testing guide
- **TEST_SUMMARY.md** - Detailed test overview
- **Project code** - All agent implementations

---

## ✅ Final Checklist

Before submission, ensure:

- [ ] `test_results.csv` generated
- [ ] All tests passing (>95% success rate)
- [ ] Quote success rate >90%
- [ ] Order success rate >80%
- [ ] Reordering triggered at least once
- [ ] Revenue generated >$0
- [ ] No critical errors in logs

---

## 🎉 Success Indicators

Your tests are successful if you see:

```
📊 TEST SUMMARY
================================================================
Total Requests Processed: 20
Successful Quotes: 18+      (>90% ✅)
Successful Orders: 16+      (>80% ✅)
Success Rate: 90.00%+

💰 FINANCIAL METRICS:
Total Revenue: $40,000+     (✅)
Reorder Triggers: 2+        (✅)
================================================================

🎯 PROJECT RUBRIC EVALUATION
================================================================
✅ PASS Quote Generation Success Rate: 90%+
✅ PASS Order Processing Success Rate: 80%+
✅ PASS Bulk Discount Application Rate: 50%+
✅ PASS Reorder System Functioning: 2+ triggers
✅ PASS Total Revenue Generated: $40,000+

Overall Score: 100% (5/5 criteria passed)
================================================================
```

---

## 🚀 Quick Commands

```bash
# Check readiness
python check_test_readiness.py

# Run everything
python run_all_tests.py

# Generate deliverable only
python test_complete_system.py

# Unit tests only
pytest tests/ -v

# Integration tests only
pytest tests/test_integration.py -v

# Specific agent
pytest tests/test_inventory_agent.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 📞 Support

If you encounter issues:

1. ✅ Check `test_execution.log`
2. ✅ Run `check_test_readiness.py`
3. ✅ Verify all dependencies installed
4. ✅ Ensure database exists
5. ✅ Check environment variables

---

## 🏆 You're Ready!

If `check_test_readiness.py` passes all checks:

**YOU'RE READY TO RUN TESTS AND SUBMIT YOUR PROJECT! 🎉**

```bash
python run_all_tests.py
```

Good luck! 🚀