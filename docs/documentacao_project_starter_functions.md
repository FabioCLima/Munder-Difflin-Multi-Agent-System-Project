# 📚 DOCUMENTAÇÃO COMPLETA - project_starter.py Functions

## 🎯 OVERVIEW

O `project_starter.py` fornece **8 funções principais** para gerenciar o sistema de inventário e vendas da Munder Difflin Paper Company.

---

## 📊 CATEGORIAS DE FUNÇÕES

### 🏗️ **SETUP & INITIALIZATION** (1 função)
### 📦 **INVENTORY MANAGEMENT** (3 funções)
### 💰 **FINANCIAL TRACKING** (2 funções)
### 📝 **TRANSACTION MANAGEMENT** (1 função)
### 📚 **HISTORICAL DATA** (1 função)
### 🚚 **LOGISTICS** (1 função)

---

## 🔍 ANÁLISE DETALHADA DAS FUNÇÕES

---

### 1️⃣ `generate_sample_inventory(paper_supplies, coverage=0.4, seed=137)`

**Categoria:** 🏗️ Setup & Initialization

**Propósito:**
Gera um inventário inicial aleatório selecionando uma porcentagem dos itens disponíveis da lista `paper_supplies`.

**Parâmetros:**
- `paper_supplies` (list): Lista de dicionários com items (item_name, category, unit_price)
- `coverage` (float): Fração de itens a incluir (default: 0.4 = 40%)
- `seed` (int): Seed para reprodutibilidade (default: 137)

**Retorno:**
- `pd.DataFrame`: DataFrame com colunas:
  - `item_name`: Nome do item
  - `category`: Categoria (paper, product, large_format, specialty)
  - `unit_price`: Preço por unidade
  - `current_stock`: Estoque inicial (200-800 units)
  - `min_stock_level`: Nível mínimo antes de reordenar (50-150 units)

**Exemplo de Uso:**
```python
inventory = generate_sample_inventory(paper_supplies, coverage=0.4, seed=137)
# Retorna DataFrame com ~18 items (40% de 44 itens)
```

**Quando Usar:**
- Uma vez no início do sistema (chamada por `init_database()`)
- Não usar diretamente nos agentes

---

### 2️⃣ `init_database(db_engine, seed=137)`

**Categoria:** 🏗️ Setup & Initialization

**Propósito:**
Inicializa TODO o banco de dados do zero:
- Cria tabelas (transactions, quote_requests, quotes, inventory)
- Carrega dados dos CSVs
- Gera inventário inicial
- Cria transações iniciais (cash seed + stock inicial)

**Parâmetros:**
- `db_engine` (Engine): SQLAlchemy engine conectado ao SQLite
- `seed` (int): Seed para reprodutibilidade (default: 137)

**Retorno:**
- `Engine`: O mesmo engine após setup completo

**Tabelas Criadas:**

| Tabela | Propósito | Colunas Principais |
|--------|-----------|-------------------|
| `transactions` | Registra todas as transações | id, item_name, transaction_type, units, price, transaction_date |
| `quote_requests` | Requisições originais dos clientes | id, job, need_size, event, request |
| `quotes` | Cotações históricas | request_id, total_amount, quote_explanation, job_type, order_size, event_type |
| `inventory` | Catálogo de produtos | item_name, category, unit_price, current_stock, min_stock_level |

**Estado Inicial:**
- Cash Balance: $50,000 (via transação dummy de sales)
- Inventory: ~18 itens com 200-800 units cada
- Data inicial: 2025-01-01

**Exemplo de Uso:**
```python
db_engine = create_engine("sqlite:///munder_difflin.db")
init_database(db_engine, seed=137)
```

**Quando Usar:**
- **UMA VEZ** no início do programa (linha 616 do starter code)
- **NUNCA** durante operação normal dos agentes

---

### 3️⃣ `get_all_inventory(as_of_date)`

**Categoria:** 📦 Inventory Management

**Propósito:**
Retorna um snapshot de TODOS os itens em estoque em uma data específica.
Calcula o estoque líquido: `stock_orders - sales` até a data.

**Parâmetros:**
- `as_of_date` (str): Data no formato ISO "YYYY-MM-DD"

**Retorno:**
- `Dict[str, int]`: Dicionário mapeando `{item_name: stock_quantity}`
- **Apenas itens com stock > 0 são incluídos**

**Lógica Interna:**
```sql
SELECT item_name,
       SUM(CASE 
           WHEN transaction_type = 'stock_orders' THEN units
           WHEN transaction_type = 'sales' THEN -units
       END) as stock
FROM transactions
WHERE transaction_date <= as_of_date
GROUP BY item_name
HAVING stock > 0
```

**Exemplo de Uso:**
```python
inventory = get_all_inventory("2025-04-10")
# Returns: {"A4 paper": 450, "Cardstock": 320, ...}
```

**Casos de Uso:**
- **Inventory Agent**: Responder "What do you have in stock?"
- **Quoting Agent**: Validar disponibilidade antes de cotar
- **Reordering Agent**: Verificar itens com estoque baixo

**⚠️ Nota Importante:**
Retorna snapshot histórico! Se `as_of_date = "2025-04-01"`, não inclui transações após 01/04.

---

### 4️⃣ `get_stock_level(item_name, as_of_date)`

**Categoria:** 📦 Inventory Management

**Propósito:**
Retorna o estoque de UM item específico em uma data.

**Parâmetros:**
- `item_name` (str): Nome exato do item (case-sensitive!)
- `as_of_date` (str | datetime): Data de consulta

**Retorno:**
- `pd.DataFrame`: Single-row DataFrame com colunas:
  - `item_name`: Nome do item
  - `current_stock`: Quantidade em estoque (pode ser 0 se item não existe ou esgotado)

**Exemplo de Uso:**
```python
stock_df = get_stock_level("A4 paper", "2025-04-10")
stock_qty = stock_df["current_stock"].iloc[0]
# Returns: 450
```

**Casos de Uso:**
- **Inventory Agent**: "How much A4 paper do we have?"
- **Sales Agent**: Validar quantidade disponível antes de venda
- **Reordering Agent**: Checar se item está abaixo do mínimo

**⚠️ CRITICAL:**
Nome do item deve ser **EXATAMENTE** como está no banco!
- ✅ "A4 paper" → Funciona
- ❌ "a4 paper" → Retorna 0
- ❌ "A4" → Retorna 0

**Solução:** Implementar fuzzy matching nas tools!

---

### 5️⃣ `create_transaction(item_name, transaction_type, quantity, price, date)`

**Categoria:** 📝 Transaction Management

**Propósito:**
Registra uma transação no banco de dados (compra de estoque OU venda).

**Parâmetros:**
- `item_name` (str): Nome do item
- `transaction_type` (str): **"stock_orders"** (compra) OU **"sales"** (venda)
- `quantity` (int): Número de unidades
- `price` (float): Preço TOTAL da transação (não unitário!)
- `date` (str | datetime): Data da transação

**Retorno:**
- `int`: ID da transação inserida

**Validações:**
```python
if transaction_type not in {"stock_orders", "sales"}:
    raise ValueError("Transaction type must be 'stock_orders' or 'sales'")
```

**Exemplo de Uso:**
```python
# Venda de 500 sheets de A4 paper por $25 total
transaction_id = create_transaction(
    item_name="A4 paper",
    transaction_type="sales",
    quantity=500,
    price=25.0,
    date="2025-04-10"
)

# Compra de 1000 sheets de fornecedor por $50
transaction_id = create_transaction(
    item_name="A4 paper",
    transaction_type="stock_orders",
    quantity=1000,
    price=50.0,
    date="2025-04-10"
)
```

**Casos de Uso:**
- **Sales Agent**: Registrar vendas para clientes
- **Reordering Agent**: Registrar compras de fornecedor

**⚠️ IMPORTANTE:**
- `price` é o valor TOTAL, não unitário!
- Se vender 500 units a $0.05 cada → `price=25.0`
- Se comprar 1000 units a $0.05 cada → `price=50.0`

---

### 6️⃣ `get_cash_balance(as_of_date)`

**Categoria:** 💰 Financial Tracking

**Propósito:**
Calcula o saldo de caixa atual baseado em todas as transações até uma data.

**Fórmula:**
```
Cash Balance = Σ(sales) - Σ(stock_orders)
```

**Parâmetros:**
- `as_of_date` (str | datetime): Data de corte

**Retorno:**
- `float`: Saldo em dólares (pode ser negativo se gastos > receitas)

**Lógica Interna:**
```python
total_sales = SUM(price WHERE transaction_type = "sales")
total_purchases = SUM(price WHERE transaction_type = "stock_orders")
return total_sales - total_purchases
```

**Exemplo de Uso:**
```python
cash = get_cash_balance("2025-04-10")
# Returns: 49875.50 (se vendas=50000, compras=124.50)
```

**Casos de Uso:**
- **Financial Reporting**: Monitorar saúde financeira
- **Reordering Agent**: Verificar se há dinheiro para comprar estoque
- **Validation**: Garantir que sistema não fique sem capital

**Estado Inicial:**
- $50,000 (via transação seed no `init_database()`)
- Menos o custo do inventário inicial (~$2,000-5,000)
- Cash inicial real ≈ $45,000-48,000

---

### 7️⃣ `generate_financial_report(as_of_date)`

**Categoria:** 💰 Financial Tracking

**Propósito:**
Gera um relatório financeiro COMPLETO do negócio em uma data.

**Parâmetros:**
- `as_of_date` (str | datetime): Data do relatório

**Retorno:**
- `Dict` com as seguintes chaves:

```python
{
    "as_of_date": "2025-04-10",
    "cash_balance": 48500.00,           # Dinheiro em caixa
    "inventory_value": 3200.00,         # Valor total do estoque
    "total_assets": 51700.00,           # Cash + Inventory
    "inventory_summary": [              # Detalhes por item
        {
            "item_name": "A4 paper",
            "stock": 450,
            "unit_price": 0.05,
            "value": 22.50
        },
        # ... mais itens
    ],
    "top_selling_products": [           # Top 5 produtos
        {
            "item_name": "A4 paper",
            "total_units": 5000,
            "total_revenue": 250.00
        },
        # ... mais produtos
    ]
}
```

**Exemplo de Uso:**
```python
report = generate_financial_report("2025-04-15")
print(f"Cash: ${report['cash_balance']:.2f}")
print(f"Inventory: ${report['inventory_value']:.2f}")
print(f"Total Assets: ${report['total_assets']:.2f}")
```

**Casos de Uso:**
- **Testing**: Validar estado do sistema após cada request
- **Monitoring**: Acompanhar saúde financeira
- **Debugging**: Verificar se vendas/compras estão corretas

**⚠️ Performance:**
Esta função é **CUSTOSA** - faz múltiplas queries ao banco.
Use apenas quando necessário (não em cada iteração do agente).

---

### 8️⃣ `get_supplier_delivery_date(input_date_str, quantity)`

**Categoria:** 🚚 Logistics

**Propósito:**
Estima a data de entrega do fornecedor baseada na quantidade do pedido.

**Parâmetros:**
- `input_date_str` (str): Data do pedido em formato ISO "YYYY-MM-DD"
- `quantity` (int): Número de unidades pedidas

**Retorno:**
- `str`: Data de entrega estimada "YYYY-MM-DD"

**Regras de Lead Time:**
```
Quantity         Lead Time    Exemplo
≤ 10 units    →  0 days      Hoje mesmo
11-100        →  1 day       Amanhã
101-1000      →  4 days      Daqui 4 dias
> 1000        →  7 days      Semana que vem
```

**Exemplo de Uso:**
```python
# Pedido de 50 units feito em 10/04
delivery = get_supplier_delivery_date("2025-04-10", 50)
# Returns: "2025-04-11" (1 dia depois)

# Pedido de 2000 units
delivery = get_supplier_delivery_date("2025-04-10", 2000)
# Returns: "2025-04-17" (7 dias depois)
```

**Casos de Uso:**
- **Reordering Agent**: Informar ao cliente quando o estoque estará disponível
- **Sales Agent**: Validar se consegue cumprir prazo de entrega
- **Planning**: Antecipar necessidades futuras

**⚠️ Nota:**
Se `input_date_str` inválido, usa data atual como fallback.

---

### 9️⃣ `search_quote_history(search_terms, limit=5)`

**Categoria:** 📚 Historical Data

**Propósito:**
Busca cotações históricas similares para usar como referência de pricing.

**Parâmetros:**
- `search_terms` (List[str]): Lista de keywords para buscar
- `limit` (int): Número máximo de resultados (default: 5)

**Retorno:**
- `List[Dict]`: Lista de cotações que matcham, ordenadas por data (mais recente primeiro)

```python
[
    {
        "original_request": "I need 500 sheets of glossy paper...",
        "total_amount": 120.0,
        "quote_explanation": "Thank you for your order! ...",
        "job_type": "event manager",
        "order_size": "small",
        "event_type": "ceremony",
        "order_date": "2025-01-01"
    },
    # ... mais quotes
]
```

**Lógica de Busca:**
Busca os termos (case-insensitive) em:
1. `quote_requests.response` (request original do cliente)
2. `quotes.quote_explanation` (explicação da cotação)

**Exemplo de Uso:**
```python
# Cliente pede "glossy paper"
similar_quotes = search_quote_history(["glossy", "paper"], limit=5)

# Analisar preços históricos
for quote in similar_quotes:
    print(f"{quote['order_size']}: ${quote['total_amount']}")
```

**Casos de Uso:**
- **Quoting Agent**: ESSENCIAL! Usar para determinar pricing strategy
- **Analysis**: Entender padrões de descontos bulk
- **Consistency**: Manter preços alinhados com histórico

**⚠️ CRITICAL:**
O README diz: **"Ensure every quote includes bulk discounts and uses past data"**
Esta função é OBRIGATÓRIA no Quoting Agent!

**Estratégia de Keywords:**
```python
# Request: "I need 500 glossy paper for a wedding"
keywords = ["glossy", "paper", "wedding", "ceremony"]
quotes = search_quote_history(keywords, limit=5)
```

---

## 🗺️ MAPEAMENTO: FUNÇÕES → TOOLS → AGENTES

### **INVENTORY AGENT Tools**

| Tool Name | Função Base | Propósito |
|-----------|-------------|-----------|
| `check_inventory_tool` | `get_all_inventory()` | Listar todos os itens disponíveis |
| `check_item_stock_tool` | `get_stock_level()` | Verificar estoque de item específico |
| `search_item_by_name_tool` | Custom (fuzzy matching) | Encontrar item mesmo com nome aproximado |

**Funções que o Inventory Agent NÃO usa:**
- ❌ `create_transaction()` (não faz vendas)
- ❌ `search_quote_history()` (não precisa de histórico)

---

### **QUOTING AGENT Tools**

| Tool Name | Função Base | Propósito |
|-----------|-------------|-----------|
| `get_quote_history_tool` | `search_quote_history()` | Buscar cotações similares |
| `check_availability_tool` | `get_stock_level()` | Validar se tem estoque |
| `calculate_pricing_tool` | Custom logic + inventory | Calcular preço com desconto bulk |

**Lógica de Pricing:**
1. Buscar quotes similares com `search_quote_history()`
2. Analisar descontos aplicados (10-15% típico)
3. Calcular: `base_price = sum(quantity × unit_price)`
4. Aplicar bulk discount baseado em `order_size` e histórico
5. Arredondar para valor "amigável"

**Funções que o Quoting Agent NÃO usa:**
- ❌ `create_transaction()` (não finaliza vendas)
- ❌ `get_supplier_delivery_date()` (não compra estoque)

---

### **SALES AGENT Tools**

| Tool Name | Função Base | Propósito |
|-----------|-------------|-----------|
| `finalize_sale_tool` | `create_transaction()` type="sales" | Registrar venda |
| `validate_stock_tool` | `get_stock_level()` | Confirmar disponibilidade |
| `estimate_delivery_tool` | Custom logic | Informar prazo ao cliente |

**Workflow de Venda:**
1. Validar disponibilidade com `get_stock_level()`
2. Criar transação de venda com `create_transaction()`
3. Retornar confirmação com prazo de entrega

**Funções que o Sales Agent NÃO usa:**
- ❌ `search_quote_history()` (cotação já foi feita)
- ❌ `get_supplier_delivery_date()` (entrega ao cliente, não do fornecedor)

---

### **REORDERING AGENT Tools**

| Tool Name | Função Base | Propósito |
|-----------|-------------|-----------|
| `check_low_stock_tool` | `get_all_inventory()` + inventory table | Identificar itens abaixo do mínimo |
| `reorder_stock_tool` | `create_transaction()` type="stock_orders" | Comprar do fornecedor |
| `get_delivery_estimate_tool` | `get_supplier_delivery_date()` | Informar quando chega |
| `check_cash_tool` | `get_cash_balance()` | Validar se há dinheiro |

**Workflow de Reordenação:**
1. Após cada venda, chamar `get_all_inventory()`
2. Comparar com `min_stock_level` da tabela `inventory`
3. Se `current_stock < min_stock_level`:
   - Verificar `get_cash_balance()` (tem dinheiro?)
   - Calcular quantidade (ex: restock até 500 units)
   - Calcular custo: `quantity × unit_price`
   - Chamar `create_transaction(type="stock_orders")`
   - Usar `get_supplier_delivery_date()` para logging

**Quantidade de Reordenação:**
```python
# Strategy: reordenar para ter 500 units
reorder_quantity = 500 - current_stock
```

---

## 🚨 PONTOS CRÍTICOS DE ATENÇÃO

### ⚠️ **1. Case-Sensitive Item Names**
```python
# ❌ ERRADO
get_stock_level("a4 paper", date)  # Retorna 0

# ✅ CERTO
get_stock_level("A4 paper", date)  # Retorna estoque correto
```

**Solução:** Criar tool de fuzzy matching ou normalização.

---

### ⚠️ **2. Price vs Unit Price**
```python
# create_transaction() usa PREÇO TOTAL, não unitário!

# ❌ ERRADO
create_transaction("A4 paper", "sales", 500, 0.05, date)
# Isso registra venda de $0.05 TOTAL (perdeu $24.95!)

# ✅ CERTO
unit_price = 0.05
quantity = 500
total_price = unit_price * quantity  # = 25.0
create_transaction("A4 paper", "sales", 500, 25.0, date)
```

---

### ⚠️ **3. Transaction Types**
```python
# Apenas dois valores válidos:
"stock_orders"  # Compra de fornecedor (adiciona estoque, reduz cash)
"sales"         # Venda para cliente (reduz estoque, adiciona cash)

# ❌ Qualquer outro valor causa ValueError
```

---

### ⚠️ **4. Date Format**
```python
# Sempre usar ISO format: "YYYY-MM-DD"
"2025-04-10"  # ✅ Correto
"04/10/2025"  # ❌ Pode causar erros
"2025-4-10"   # ❌ Inconsistente
```

---

### ⚠️ **5. Stock Calculation é Histórico**
```python
# get_all_inventory("2025-04-01")
# Retorna estoque EM 01/04, não inclui transações posteriores!

# Se você tem:
# 01/04: 500 units
# 05/04: venda de 100 units
# 10/04: compra de 200 units

get_all_inventory("2025-04-03")  # Returns: 500
get_all_inventory("2025-04-06")  # Returns: 400
get_all_inventory("2025-04-15")  # Returns: 600
```

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### **Para cada Tool, você deve:**

- [ ] Usar a função correta do `project_starter.py`
- [ ] Adicionar validações (ex: item existe? quantidade positiva?)
- [ ] Implementar error handling (try/except)
- [ ] Adicionar logging com loguru
- [ ] Retornar resultado em formato estruturado (Pydantic model?)
- [ ] Documentar parâmetros e retorno

### **Para cada Agent, você deve:**

- [ ] Definir quais tools ele pode usar
- [ ] Implementar prompt do sistema (role definition)
- [ ] Testar isoladamente antes de integrar
- [ ] Adicionar logging de cada ação
- [ ] Validar inputs antes de chamar tools

---

## 🎯 PRÓXIMOS PASSOS

Agora que você entende todas as funções:

1. ✅ **Revisitar diagrama do Step 1**
   - Substituir tools hipotéticas pelas funções reais
   - Confirmar que cada agente tem as tools corretas

2. ✅ **Criar wrappers (Tools)**
   - `src/tools/inventory_tools.py`
   - `src/tools/quoting_tools.py`
   - `src/tools/sales_tools.py`

3. ✅ **Implementar Agentes**
   - Usar as tools criadas
   - Seguir o workflow do diagrama

4. ✅ **Testar com sample requests**
   - Processar os 20 casos
   - Validar com `generate_financial_report()`

---

**FIM DA DOCUMENTAÇÃO**

Tempo estimado de revisão: ✅ 30+ minutos concluídos