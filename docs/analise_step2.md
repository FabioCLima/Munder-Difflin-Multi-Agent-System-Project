# 📖 STEP 2: ANÁLISE COMPLETA DO STARTER CODE

## 🎯 Objetivo
Revisar cuidadosamente o `project_starter.py` e documentar todas as funções para entender seu propósito e como integrá-las no sistema multi-agente.

---

## 📊 VISÃO GERAL DA ESTRUTURA

### **Banco de Dados: `munder_difflin.db` (SQLite)**

Tabelas criadas por `init_database()`:
```sql
1. inventory         - Catálogo de produtos com preços e níveis mínimos
2. transactions      - Log de todas compras e vendas
3. quote_requests    - Requisições de clientes (histórico)
4. quotes            - Cotações geradas (histórico com metadata)
5. financials        - (implícito) Calculado dinamicamente via transactions
```

### **Dados Iniciais**
- **Cash inicial**: $50,000 (via transação dummy de sales)
- **Inventário**: 40% dos 44 tipos de papel (seed=137)
- **Stock inicial**: 200-800 unidades por item
- **Min stock level**: 50-150 unidades

---

## 🔧 FUNÇÕES DO STARTER CODE

### **1. INICIALIZAÇÃO E SETUP**

#### `generate_sample_inventory(paper_supplies, coverage=0.4, seed=137)`
```python
📝 Propósito:
   Gera inventário aleatório selecionando uma % dos itens da lista paper_supplies

⚙️ Parâmetros:
   - paper_supplies: Lista com 44 tipos de papel
   - coverage: Fração de itens (padrão 40%)
   - seed: Semente para reprodutibilidade

🎯 Retorna:
   DataFrame com: item_name, category, unit_price, current_stock, min_stock_level

🤖 Uso no Multi-Agent:
   - Inventory Agent: Consultar itens disponíveis
   - Reordering Agent: Identificar min_stock_level
```

#### `init_database(db_engine, seed=137)`
```python
📝 Propósito:
   Inicializa TODAS as tabelas do banco de dados e carrega dados iniciais

⚙️ O que faz:
   1. Cria tabela 'transactions' (vazia)
   2. Carrega 'quote_requests.csv' → tabela 'quote_requests'
   3. Carrega 'quotes.csv' → tabela 'quotes' (com parsing de metadata)
   4. Gera inventário via generate_sample_inventory()
   5. Cria transações iniciais:
      - 1 transação de sales = $50,000 (cash inicial)
      - N transações de stock_orders (1 por item no inventário)
   6. Salva inventário na tabela 'inventory'

🔑 Data inicial: 2025-01-01

🎯 Retorna:
   Engine (o mesmo que foi passado)

⚠️ CRÍTICO:
   DEVE ser chamado UMA VEZ no início do programa!
   Se chamar novamente, RESETA todo o banco!

🤖 Uso no Multi-Agent:
   - main.py: Executar ANTES de instanciar os agentes
   - run_test_scenarios(): Primeira linha da função
```

---

### **2. GESTÃO DE TRANSAÇÕES**

#### `create_transaction(item_name, transaction_type, quantity, price, date)`
```python
📝 Propósito:
   Registra uma transação (compra ou venda) no banco de dados

⚙️ Parâmetros:
   - item_name: Nome do item (string exata da tabela inventory)
   - transaction_type: 'stock_orders' OU 'sales'
   - quantity: Número de unidades (int)
   - price: Preço TOTAL da transação (float)
   - date: Data no formato ISO (YYYY-MM-DD) ou datetime

🎯 Retorna:
   int - ID da transação inserida

⚠️ Validações:
   - transaction_type DEVE ser 'stock_orders' ou 'sales'
   - Lança ValueError se tipo inválido

💡 IMPORTANTE:
   - Para stock_orders: quantity > 0, price = cost (negativo no cash)
   - Para sales: quantity > 0, price = revenue (positivo no cash)

🤖 Uso no Multi-Agent:
   - Reordering Agent: create_transaction(..., 'stock_orders', ...)
   - Sales Agent: create_transaction(..., 'sales', ...)
```

---

### **3. CONSULTA DE INVENTÁRIO**

#### `get_all_inventory(as_of_date)`
```python
📝 Propósito:
   Retorna snapshot de TODOS os itens em estoque em uma data específica

⚙️ Parâmetros:
   - as_of_date: Data no formato ISO (YYYY-MM-DD)

🔍 Lógica:
   Calcula: (SUM de stock_orders) - (SUM de sales) até a data
   Retorna apenas itens com stock > 0

🎯 Retorna:
   Dict[str, int] = {item_name: quantidade_em_estoque}
   
   Exemplo:
   {
       "A4 paper": 650,
       "Cardstock": 400,
       "Glossy paper": 200
   }

🤖 Uso no Multi-Agent:
   - Inventory Agent: Listar todos os itens disponíveis
   - Orchestrator: Visão geral do inventário
```

#### `get_stock_level(item_name, as_of_date)`
```python
📝 Propósito:
   Retorna o nível de estoque de UM item específico em uma data

⚙️ Parâmetros:
   - item_name: Nome exato do item (str)
   - as_of_date: Data ISO (str) ou datetime

🔍 Lógica:
   Similar a get_all_inventory, mas filtrado por item_name
   Usa COALESCE para retornar 0 se item não existir

🎯 Retorna:
   DataFrame com colunas: ['item_name', 'current_stock']
   
   Exemplo:
   | item_name    | current_stock |
   |--------------|---------------|
   | A4 paper     | 650           |

🤖 Uso no Multi-Agent:
   - Inventory Agent: Verificar disponibilidade de item específico
   - Quoting Agent: Validar se tem estoque antes de cotar
   - Sales Agent: Confirmar disponibilidade antes de vender
```

---

### **4. LOGÍSTICA E PRAZOS**

#### `get_supplier_delivery_date(input_date_str, quantity)`
```python
📝 Propósito:
   Estima data de entrega do FORNECEDOR baseado na quantidade pedida

⚙️ Parâmetros:
   - input_date_str: Data de pedido (ISO format)
   - quantity: Quantidade de unidades (int)

📅 Regras de Lead Time:
   - ≤ 10 unidades    → Same day (0 dias)
   - 11-100 unidades  → 1 dia
   - 101-1000 unid.   → 4 dias
   - > 1000 unidades  → 7 dias

🎯 Retorna:
   str - Data de entrega estimada (YYYY-MM-DD)

⚠️ Fallback:
   Se data inválida, usa datetime.now() como base

💡 IMPORTANTE:
   Esta função é para REPOSIÇÃO DE ESTOQUE (compra do fornecedor)
   NÃO é para entrega ao cliente!

🤖 Uso no Multi-Agent:
   - Reordering Agent: Calcular quando item estará disponível após reposição
   - Inventory Agent: Informar prazo de chegada de novos itens
```

---

### **5. GESTÃO FINANCEIRA**

#### `get_cash_balance(as_of_date)`
```python
📝 Propósito:
   Calcula saldo de caixa (cash disponível) em uma data específica

⚙️ Parâmetros:
   - as_of_date: Data ISO (str) ou datetime

🔍 Lógica:
   Cash = (SUM de sales.price) - (SUM de stock_orders.price)
   
   Em outras palavras:
   Cash = Revenue - Custo de compras

🎯 Retorna:
   float - Saldo de caixa
   
   Exemplos:
   - Início: $50,000 (transação dummy inicial)
   - Após venda de $100: $50,100
   - Após compra de $50: $50,050

⚠️ CRÍTICO para Reordering:
   Verificar se cash_balance >= custo_da_compra antes de reordenar!

🤖 Uso no Multi-Agent:
   - Reordering Agent: Validar se há dinheiro para comprar
   - Sales Agent: Reportar saldo após venda
   - Financial reporting
```

#### `generate_financial_report(as_of_date)`
```python
📝 Propósito:
   Gera relatório financeiro COMPLETO da empresa

⚙️ Parâmetros:
   - as_of_date: Data do relatório (str ou datetime)

📊 Retorna:
   Dict com estrutura:
   {
       'as_of_date': 'YYYY-MM-DD',
       'cash_balance': float,           # Dinheiro em caixa
       'inventory_value': float,        # Valor total do estoque
       'total_assets': float,           # Cash + Inventory
       'inventory_summary': [           # Lista detalhada por item
           {
               'item_name': str,
               'stock': int,
               'unit_price': float,
               'value': float          # stock × unit_price
           },
           ...
       ],
       'top_selling_products': [        # Top 5 produtos por revenue
           {
               'item_name': str,
               'total_units': int,
               'total_revenue': float
           },
           ...
       ]
   }

💡 Cálculos:
   - inventory_value = SUM(stock × unit_price) para todos os itens
   - total_assets = cash_balance + inventory_value

🤖 Uso no Multi-Agent:
   - main.py: Validar estado do sistema após cada operação
   - run_test_scenarios(): Monitorar saúde financeira
   - Debug: Entender por que algo falhou
```

---

### **6. INTELIGÊNCIA DE COTAÇÕES**

#### `search_quote_history(search_terms, limit=5)`
```python
📝 Propósito:
   Busca cotações históricas similares baseado em keywords

⚙️ Parâmetros:
   - search_terms: List[str] - Lista de termos de busca
   - limit: Máximo de resultados (padrão 5)

🔍 Lógica de Busca:
   Procura nos campos:
   - quote_requests.response (texto do request do cliente)
   - quotes.quote_explanation (explicação da cotação)
   
   Usa LIKE com LOWER() para case-insensitive matching
   Combina múltiplos termos com AND

📊 Retorna:
   List[Dict] com estrutura:
   [
       {
           'original_request': str,      # Request do cliente
           'total_amount': float,        # Valor total cotado
           'quote_explanation': str,     # Justificativa
           'job_type': str,             # Ex: 'office manager'
           'order_size': str,           # 'small', 'medium', 'large'
           'event_type': str,           # Ex: 'ceremony', 'party'
           'order_date': str            # Data ISO
       },
       ...
   ]

🎯 Ordenação:
   Por order_date DESC (mais recentes primeiro)

💡 ESTRATÉGIA DE USO:
   1. Extrair keywords do novo request (ex: ["glossy", "cardstock"])
   2. Buscar quotes similares
   3. Analisar total_amount e descontos aplicados
   4. Usar como referência para pricing strategy

🤖 Uso no Multi-Agent:
   - Quoting Agent: ESSENCIAL para pricing inteligente
   - Analisar padrões de desconto por order_size
   - Referenciar explicações de cotações passadas
```

---

## 🎨 FLUXO DE DADOS ENTRE FUNÇÕES

### **Cenário 1: Processar uma Venda**
```
1. get_stock_level(item, date) 
   → Verifica disponibilidade

2. create_transaction(item, 'sales', qty, price, date)
   → Registra venda
   → Debita do estoque (implicitamente)
   → Adiciona ao cash

3. get_cash_balance(date)
   → Confirma novo saldo

4. (Trigger) Reordering check
   → get_stock_level() novamente
   → Se < min_level, chamar create_transaction('stock_orders')
```

### **Cenário 2: Gerar Cotação Inteligente**
```
1. search_quote_history(keywords)
   → Busca cotações similares

2. Analisar padrões:
   - Order_size 'large' geralmente tem 10-15% desconto
   - Event_type 'conference' tende a ter preços mais altos

3. get_stock_level(item, date)
   → Validar disponibilidade

4. Calcular preço:
   base_price = unit_price × quantity
   bulk_discount = base_price × discount_rate
   final_price = base_price - bulk_discount
   
5. Retornar quote com quote_explanation humanizada
```

### **Cenário 3: Reordenação Automática**
```
1. get_all_inventory(date)
   → Lista todos os itens

2. Para cada item:
   stock = get_stock_level(item, date)
   min_level = inventory.loc[item, 'min_stock_level']
   
   Se stock < min_level:
       3a. Calcular quantidade de reposição
           reorder_qty = (min_level × 2) - stock
       
       3b. get_cash_balance(date)
           → Verificar se há cash disponível
       
       3c. Se cash suficiente:
           cost = reorder_qty × unit_price
           create_transaction(item, 'stock_orders', reorder_qty, cost, date)
       
       3d. get_supplier_delivery_date(date, reorder_qty)
           → Informar quando item estará disponível
```

---

## 🛠️ TOOLS PARA OS AGENTES (ATUALIZAÇÃO DO STEP 1)

### **Tools do Inventory Agent**
```python
1. check_inventory_tool()
   → Wrapper: get_all_inventory(current_date)
   → Retorna: Dict com todos os itens e quantidades

2. check_item_stock_tool(item_name)
   → Wrapper: get_stock_level(item_name, current_date)
   → Retorna: Quantidade específica do item

3. check_low_stock_tool()
   → Lógica custom:
     - get_all_inventory()
     - Comparar com min_stock_level da tabela inventory
     - Retornar lista de itens abaixo do mínimo
```

### **Tools do Quoting Agent**
```python
1. search_similar_quotes_tool(keywords)
   → Wrapper: search_quote_history(keywords, limit=5)
   → Retorna: Histórico de cotações similares

2. get_item_price_tool(item_name)
   → Query: SELECT unit_price FROM inventory WHERE item_name = ?
   → Retorna: Preço unitário

3. validate_availability_tool(items_dict)
   → Para cada item em items_dict:
     - get_stock_level(item, date)
     - Retornar se disponível ou não

4. calculate_bulk_discount_tool(order_size, base_price)
   → Lógica baseada em histórico:
     - 'small': 0-5% desconto
     - 'medium': 5-10% desconto
     - 'large': 10-15% desconto
```

### **Tools do Sales Agent**
```python
1. fulfill_order_tool(items_dict, date)
   → Para cada item:
     - Validar stock via get_stock_level()
     - create_transaction(item, 'sales', qty, price, date)
   → Retornar: Confirmação + novo cash balance

2. check_delivery_timeline_tool(date)
   → Lógica custom (entrega ao CLIENTE, não fornecedor):
     - Padrão: date + 3-5 business days
   → Retorna: Data de entrega estimada

3. get_financial_status_tool(date)
   → Wrapper: get_cash_balance(date)
   → Retorna: Saldo atual
```

### **Tools do Reordering Agent**
```python
1. identify_low_stock_tool(date)
   → get_all_inventory(date)
   → Comparar com min_stock_level
   → Retornar: Lista de itens para reordenar

2. place_stock_order_tool(item, quantity, date)
   → Validações:
     - get_cash_balance(date) ≥ cost
     - Calcular cost = quantity × unit_price
   → create_transaction(item, 'stock_orders', qty, cost, date)
   → get_supplier_delivery_date(date, quantity)
   → Retornar: Confirmação + ETA

3. calculate_reorder_quantity_tool(item, current_stock)
   → Lógica:
     - min_level = inventory['min_stock_level']
     - optimal_stock = min_level × 2
     - reorder_qty = optimal_stock - current_stock
   → Retorna: Quantidade recomendada
```

---

## 📝 PONTOS CRÍTICOS DE ATENÇÃO

### ⚠️ **1. Naming Consistency**
```
PROBLEMA: Request pode pedir "A4 glossy paper"
          Database tem "Glossy paper"

SOLUÇÃO: Implementar fuzzy matching ou normalização de nomes
         Criar mapping table ou usar similarity matching
```

### ⚠️ **2. Date Handling**
```
IMPORTANTE: Todas as funções aceitam dates como str ou datetime
            SEMPRE passar a data correta do request!
            
            Formato: "YYYY-MM-DD" ou datetime object
            
            No run_test_scenarios(), usar:
            request_date = row["request_date"].strftime("%Y-%m-%d")
```

### ⚠️ **3. Transaction Types**
```
APENAS dois tipos válidos:
- 'stock_orders': Compra do fornecedor (debita cash)
- 'sales': Venda ao cliente (credita cash)

NÃO usar: 'purchase', 'buy', 'order', etc.
```

### ⚠️ **4. Cash Management**
```
SEMPRE verificar cash_balance ANTES de reordenar:

cash = get_cash_balance(date)
cost = quantity × unit_price

if cash >= cost:
    create_transaction(..., 'stock_orders', ...)
else:
    logger.warning(f"Insufficient cash: {cash} < {cost}")
```

### ⚠️ **5. Stock Calculation**
```
Stock é calculado DINAMICAMENTE via transactions:
- NÃO há coluna 'current_stock' em transactions
- Stock = SUM(stock_orders) - SUM(sales)

Isso significa:
- Vendas REDUZEM estoque automaticamente
- Compras AUMENTAM estoque automaticamente
- Não precisa "update" manual do inventário
```

---

## ✅ CHECKLIST DE COMPREENSÃO

- [ ] Entendi que init_database() RESETA tudo
- [ ] Sei usar get_stock_level() para verificar disponibilidade
- [ ] Sei usar create_transaction() para registrar vendas e compras
- [ ] Entendi a diferença entre 'stock_orders' e 'sales'
- [ ] Sei usar search_quote_history() para pricing inteligente
- [ ] Entendi que stock é calculado dinamicamente
- [ ] Sei verificar cash_balance antes de reordenar
- [ ] Entendi as regras de delivery do get_supplier_delivery_date()
- [ ] Sei gerar relatórios com generate_financial_report()
- [ ] Revisei TODAS as 9 funções principais

---

## 🎯 PRÓXIMO PASSO

Agora que compreendemos completamente o starter code, vamos:

1. ✅ Atualizar o diagrama de workflow (Step 1) com as tools reais
2. 🔜 Implementar as tools wrapping as funções do starter
3. 🔜 Implementar os agentes usando pydantic-ai
4. 🔜 Criar o orchestrator
5. 🔜 Integrar tudo no main.py

---

**Tempo de revisão**: ✅ Completado (>30 minutos de análise detalhada)
**Documentação**: ✅ Todas as funções documentadas
**Compreensão**: ✅ Pronto para implementação