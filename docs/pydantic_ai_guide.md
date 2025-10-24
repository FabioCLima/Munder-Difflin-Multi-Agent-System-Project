# 📘 PYDANTIC-AI: GUIA COMPLETO E REFERÊNCIA

## 🎯 O QUE É PYDANTIC-AI?

**Pydantic-AI** é um framework Python moderno para construir **agents baseados em LLMs** (Large Language Models) com **type safety** e validação automática de dados.

### **Criado por**: Samuel Colvin (mesmo criador do Pydantic)
### **Versão atual**: 0.0.14+
### **Lançamento**: 2024
### **Documentação**: https://ai.pydantic.dev/

---

## 🌟 PRINCIPAIS CARACTERÍSTICAS

### **1. Type-Safe por Design**
```python
# Pydantic-AI valida AUTOMATICAMENTE tipos
agent_result: str = agent.run_sync("Hello")  # ✅ Type-checked
agent_result: int = agent.run_sync("Hello")  # ❌ MyPy error
```

### **2. Integração Nativa com Pydantic**
```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

# Agent retorna objetos Pydantic validados
user = agent.run_sync("Create user John, 30 years old")
# user é automaticamente um objeto User validado!
```

### **3. Model-Agnostic**
```python
# Suporta múltiplos LLM providers:
- OpenAI (GPT-3.5, GPT-4, GPT-4o)
- Anthropic (Claude)
- Gemini (Google)
- Groq
- Ollama (local)
```

### **4. Tools (Function Calling)**
```python
# Agents podem chamar funções Python
@agent.tool
def get_weather(city: str) -> dict:
    return {"city": city, "temp": 22}

# LLM decide QUANDO e COMO chamar a função
```

### **5. Dependency Injection**
```python
# Compartilhar contexto entre tools
@agent.tool
def process_order(ctx: RunContext[OrderContext]):
    # ctx.deps tem acesso ao contexto compartilhado
    db = ctx.deps.database
    return db.save_order()
```

---

## 🏗️ CONCEITOS FUNDAMENTAIS

### **1. Agent (Agente)**
```
Um Agent é a unidade principal que:
- Recebe um prompt (input do usuário)
- Conversa com um LLM
- Pode chamar tools (funções Python)
- Retorna uma resposta estruturada
```

### **2. Tools (Ferramentas)**
```
Tools são funções Python que o agent pode chamar:
- Decoradas com @agent.tool
- O LLM decide quando chamá-las
- Podem acessar databases, APIs, etc.
```

### **3. Dependencies (Contexto)**
```
Dependências compartilhadas entre tools:
- Database connections
- API clients
- Configuration
- State compartilhado
```

### **4. Result Types**
```
Agents podem retornar tipos validados:
- str, int, bool (primitivos)
- Pydantic Models (estruturados)
- List[Model] (listas)
```

---

## 📝 EXEMPLO 1: AGENT BÁSICO (Hello World)

### **Código Completo:**
```python
from pydantic_ai import Agent

# 1. Criar um agent simples
agent = Agent(
    'openai:gpt-4o',  # Model a usar
    system_prompt='You are a helpful assistant.'  # Instruções base
)

# 2. Executar agent (sync)
result = agent.run_sync('What is the capital of France?')
print(result.data)  # Output: "Paris"

# 3. Ver histórico da conversa
print(result.all_messages())
```

### **Explicação:**
```python
Agent('openai:gpt-4o')
# └─ Cria agent conectado ao GPT-4o

.run_sync('prompt')
# └─ Executa de forma síncrona (bloqueia até resposta)

result.data
# └─ Contém a resposta do LLM (string por padrão)

result.all_messages()
# └─ Histórico completo: [user_message, assistant_response]
```

---

## 📝 EXEMPLO 2: AGENT COM TOOL (Função)

### **Código Completo:**
```python
from pydantic_ai import Agent, RunContext

# 1. Criar agent
agent = Agent(
    'openai:gpt-4o',
    system_prompt='You are a weather assistant.'
)

# 2. Definir uma tool
@agent.tool
def get_weather(city: str) -> dict:
    """Get current weather for a city."""
    # Em produção, isso chamaria uma API real
    weather_db = {
        'Paris': {'temp': 18, 'condition': 'Cloudy'},
        'London': {'temp': 15, 'condition': 'Rainy'},
        'Tokyo': {'temp': 25, 'condition': 'Sunny'}
    }
    return weather_db.get(city, {'temp': 20, 'condition': 'Unknown'})

# 3. Agent decide AUTOMATICAMENTE quando chamar a tool
result = agent.run_sync("What's the weather in Paris?")
print(result.data)
# Output: "The weather in Paris is currently 18°C and cloudy."
```

### **O que acontece internamente:**
```
1. User: "What's the weather in Paris?"
2. LLM pensa: "Preciso de dados! Vou chamar get_weather()"
3. LLM chama: get_weather(city="Paris")
4. Tool retorna: {'temp': 18, 'condition': 'Cloudy'}
5. LLM gera resposta: "The weather in Paris is 18°C and cloudy"
6. Usuário recebe resposta humanizada
```

---

## 📝 EXEMPLO 3: AGENT COM RESULTADO ESTRUTURADO

### **Código Completo:**
```python
from pydantic import BaseModel
from pydantic_ai import Agent

# 1. Definir estrutura de dados desejada
class Product(BaseModel):
    name: str
    price: float
    category: str
    in_stock: bool

# 2. Criar agent que retorna Product
agent = Agent(
    'openai:gpt-4o',
    result_type=Product,  # ← Tipo de retorno
    system_prompt='Extract product information from text.'
)

# 3. Agent retorna objeto validado automaticamente
result = agent.run_sync(
    "I want to buy the Samsung Galaxy S24 for $899, it's in Electronics and available"
)

product = result.data  # product é um objeto Product validado!
print(product.name)     # "Samsung Galaxy S24"
print(product.price)    # 899.0
print(product.category) # "Electronics"
print(product.in_stock) # True

# 4. Validação automática!
# Se LLM retornar dados inválidos, Pydantic levanta erro
```

### **Por que isso é poderoso?**
```
✅ Type safety: Garantia de tipos em tempo de desenvolvimento
✅ Validação automática: Pydantic valida os dados
✅ Auto-completion: IDEs sugerem campos automaticamente
✅ Documentação: Estrutura clara dos dados
```

---

## 📝 EXEMPLO 4: AGENT COM DEPENDENCIES (Contexto)

### **Código Completo:**
```python
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass

# 1. Definir contexto compartilhado
@dataclass
class DatabaseContext:
    connection: str  # Simulando uma conexão
    user_id: int

# 2. Criar agent com dependencies
agent = Agent(
    'openai:gpt-4o',
    deps_type=DatabaseContext,  # ← Tipo de dependências
)

# 3. Tools que usam o contexto
@agent.tool
def get_user_orders(ctx: RunContext[DatabaseContext]) -> list:
    """Get orders for the current user."""
    user_id = ctx.deps.user_id  # Acessa contexto!
    db = ctx.deps.connection
    
    # Simular query
    return [
        {'order_id': 1, 'product': 'Laptop', 'total': 1200},
        {'order_id': 2, 'product': 'Mouse', 'total': 25}
    ]

@agent.tool
def get_user_profile(ctx: RunContext[DatabaseContext]) -> dict:
    """Get user profile information."""
    user_id = ctx.deps.user_id
    return {'user_id': user_id, 'name': 'John Doe', 'email': 'john@example.com'}

# 4. Executar com contexto
db_context = DatabaseContext(
    connection='sqlite:///database.db',
    user_id=42
)

result = agent.run_sync(
    'Show me my recent orders and profile',
    deps=db_context  # ← Passa contexto
)
print(result.data)
```

### **Vantagens de Dependencies:**
```
✅ Compartilhar estado entre tools
✅ Injetar databases, APIs, configs
✅ Testar facilmente (mock dependencies)
✅ Type-safe access ao contexto
```

---

## 📝 EXEMPLO 5: MULTI-AGENT COM ORCHESTRATOR

### **Código Completo:**
```python
from pydantic_ai import Agent

# 1. Criar agentes especializados
inventory_agent = Agent(
    'openai:gpt-4o',
    system_prompt='You manage inventory. Answer questions about stock levels.'
)

pricing_agent = Agent(
    'openai:gpt-4o',
    system_prompt='You handle pricing. Calculate quotes and discounts.'
)

# 2. Criar orchestrator
orchestrator = Agent(
    'openai:gpt-4o',
    system_prompt="""
    You are a coordinator. When user asks:
    - About inventory/stock → delegate to inventory_agent
    - About prices/quotes → delegate to pricing_agent
    - General questions → answer directly
    """
)

# 3. Tools para delegar aos agentes
@orchestrator.tool
def check_inventory(query: str) -> str:
    """Check inventory levels."""
    result = inventory_agent.run_sync(query)
    return result.data

@orchestrator.tool
def get_quote(query: str) -> str:
    """Get price quote."""
    result = pricing_agent.run_sync(query)
    return result.data

# 4. Uso
result = orchestrator.run_sync("Do you have A4 paper and how much for 500 sheets?")
print(result.data)
# Orchestrator decide chamar check_inventory() e get_quote() automaticamente!
```

---

## 🎯 APLICAÇÃO NO MUNDER DIFFLIN PROJECT

### **Nossa Arquitetura com Pydantic-AI:**

```python
# 1. INVENTORY AGENT
inventory_agent = Agent(
    'openai:gpt-4o',
    deps_type=DatabaseContext,
    system_prompt='You manage paper inventory for Munder Difflin.'
)

@inventory_agent.tool
def check_stock(ctx: RunContext[DatabaseContext], item: str, date: str) -> dict:
    """Check stock level for an item."""
    return get_stock_level(item, date)  # Função do starter code

@inventory_agent.tool
def list_all_inventory(ctx: RunContext[DatabaseContext], date: str) -> dict:
    """List all items in inventory."""
    return get_all_inventory(date)

# 2. QUOTING AGENT
class QuoteResult(BaseModel):
    total_amount: float
    items: list[dict]
    discount_applied: float
    explanation: str

quoting_agent = Agent(
    'openai:gpt-4o',
    result_type=QuoteResult,  # Retorna cotação estruturada
    deps_type=DatabaseContext,
    system_prompt='You generate quotes with bulk discounts.'
)

@quoting_agent.tool
def search_past_quotes(ctx: RunContext[DatabaseContext], keywords: list) -> list:
    """Search historical quotes."""
    return search_quote_history(keywords, limit=5)

# 3. SALES AGENT
sales_agent = Agent(
    'openai:gpt-4o',
    deps_type=DatabaseContext,
    system_prompt='You process sales orders.'
)

@sales_agent.tool
def process_order(ctx: RunContext[DatabaseContext], items: dict, date: str) -> dict:
    """Process a sales order."""
    # Validar stock
    # create_transaction(..., 'sales', ...)
    # Retornar confirmação
    pass

# 4. ORCHESTRATOR
orchestrator = Agent(
    'openai:gpt-4o',
    deps_type=DatabaseContext,
    system_prompt="""
    You coordinate between:
    - Inventory Agent (stock queries)
    - Quoting Agent (price quotes)
    - Sales Agent (process orders)
    """
)

@orchestrator.tool
def delegate_to_inventory(ctx: RunContext[DatabaseContext], query: str) -> str:
    return inventory_agent.run_sync(query, deps=ctx.deps).data

@orchestrator.tool
def delegate_to_quoting(ctx: RunContext[DatabaseContext], query: str) -> QuoteResult:
    return quoting_agent.run_sync(query, deps=ctx.deps).data

@orchestrator.tool
def delegate_to_sales(ctx: RunContext[DatabaseContext], query: str) -> str:
    return sales_agent.run_sync(query, deps=ctx.deps).data
```

---

## 🎨 PADRÕES COMUNS

### **Padrão 1: Tool com Validação**
```python
@agent.tool
def add_stock(ctx: RunContext[DatabaseContext], item: str, quantity: int) -> dict:
    """Add stock to inventory."""
    # Validações
    if quantity <= 0:
        return {"error": "Quantity must be positive"}
    
    # Verificar cash
    cash = get_cash_balance(ctx.deps.current_date)
    cost = quantity * get_item_price(item)
    
    if cash < cost:
        return {"error": "Insufficient cash", "required": cost, "available": cash}
    
    # Executar
    tx_id = create_transaction(item, 'stock_orders', quantity, cost, ctx.deps.current_date)
    return {"success": True, "transaction_id": tx_id}
```

### **Padrão 2: Tool com Logging**
```python
from loguru import logger

@agent.tool
def get_stock_level_logged(ctx: RunContext[DatabaseContext], item: str) -> int:
    """Check stock with logging."""
    logger.info(f"Checking stock for: {item}")
    
    try:
        stock = get_stock_level(item, ctx.deps.current_date)
        quantity = int(stock['current_stock'].iloc[0])
        logger.debug(f"Stock found: {quantity}")
        return quantity
    except Exception as e:
        logger.error(f"Error checking stock: {e}")
        raise
```

### **Padrão 3: Tool com Cache**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def _get_item_price_cached(item: str) -> float:
    """Cached price lookup."""
    return get_item_pricing_tool(item)

@agent.tool
def get_item_price(item: str) -> float:
    """Get item price (cached)."""
    return _get_item_price_cached(item)
```

---

## 🚀 COMANDOS ESSENCIAIS

### **Executar Agent (Sync)**
```python
result = agent.run_sync('Your prompt here')
print(result.data)
```

### **Executar Agent (Async)**
```python
result = await agent.run('Your prompt here')
print(result.data)
```

### **Executar com Dependencies**
```python
result = agent.run_sync('Prompt', deps=my_context)
```

### **Streaming (Respostas em tempo real)**
```python
async with agent.run_stream('Long prompt') as response:
    async for chunk in response.stream_text():
        print(chunk, end='')
```

### **Ver histórico de mensagens**
```python
result = agent.run_sync('Hello')
for msg in result.all_messages():
    print(f"{msg.role}: {msg.content}")
```

---

## 📊 COMPARAÇÃO: PYDANTIC-AI vs OUTROS

| Característica | Pydantic-AI | LangChain | AutoGen |
|----------------|-------------|-----------|---------|
| Type Safety | ✅ Forte | ⚠️ Parcial | ❌ Fraca |
| Validação automática | ✅ Sim | ❌ Manual | ❌ Manual |
| Curva de aprendizado | 🟢 Baixa | 🟡 Média | 🔴 Alta |
| Model-agnostic | ✅ Sim | ✅ Sim | ⚠️ Limitado |
| Dependency Injection | ✅ Built-in | ❌ Manual | ❌ Manual |
| Documentação | 🟢 Excelente | 🟡 Boa | 🟡 Boa |

---

## ✅ VANTAGENS PARA O NOSSO PROJETO

### **1. Type Safety**
```python
# MyPy detecta erros antes de rodar:
result: QuoteResult = quoting_agent.run_sync(...)  # ✅
result: str = quoting_agent.run_sync(...)  # ❌ Type error
```

### **2. Validação Automática**
```python
class Quote(BaseModel):
    total_amount: float
    items: list[dict]
    
# Se LLM retornar dados inválidos, erro automático!
# Sem necessidade de validação manual
```

### **3. Dependency Injection**
```python
# Compartilhar database, date, config entre todos os agents/tools
db_context = DatabaseContext(
    db_engine=db_engine,
    current_date="2025-04-01"
)

result = orchestrator.run_sync(query, deps=db_context)
# Todas as tools acessam o mesmo contexto!
```

### **4. Testabilidade**
```python
# Fácil mockar dependencies para testes
mock_db = MockDatabase()
test_context = DatabaseContext(db_engine=mock_db, current_date="2025-01-01")

result = agent.run_sync("test query", deps=test_context)
assert result.data == expected_value
```

### **5. Logging Integrado**
```python
# Pydantic-AI já loga todas as chamadas de LLM e tools
# Perfeito para debug e auditoria
```

---

## 📚 RECURSOS E DOCUMENTAÇÃO

### **Oficial:**
- **Docs**: https://ai.pydantic.dev/
- **GitHub**: https://github.com/pydantic/pydantic-ai
- **Examples**: https://ai.pydantic.dev/examples/

### **Tutoriais:**
- Getting Started: https://ai.pydantic.dev/getting-started/
- Agents: https://ai.pydantic.dev/agents/
- Tools: https://ai.pydantic.dev/tools/
- Dependencies: https://ai.pydantic.dev/dependencies/

### **API Reference:**
- Agent: https://ai.pydantic.dev/api/agent/
- RunContext: https://ai.pydantic.dev/api/run-context/
- Models: https://ai.pydantic.dev/api/models/

---

## 🎓 BOAS PRÁTICAS

### **1. System Prompts Claros**
```python
agent = Agent(
    'openai:gpt-4o',
    system_prompt="""
    You are a paper inventory specialist.
    
    Your responsibilities:
    - Check stock levels accurately
    - Identify low stock situations
    - Use exact item names from database
    
    Always be precise and use the tools provided.
    """
)
```

### **2. Tools com Docstrings**
```python
@agent.tool
def check_stock(item_name: str, date: str) -> int:
    """
    Check current stock level for a specific item.
    
    Args:
        item_name: Exact name of the item (e.g., "A4 paper")
        date: Date in ISO format (YYYY-MM-DD)
    
    Returns:
        Current stock quantity as integer
    """
    # LLM lê a docstring para entender quando usar a tool!
```

### **3. Error Handling**
```python
@agent.tool
def process_order(items: dict, date: str) -> dict:
    """Process a sales order."""
    try:
        # Processamento
        return {"success": True, "order_id": 123}
    except InsufficientStockError as e:
        return {"error": "insufficient_stock", "message": str(e)}
    except Exception as e:
        logger.error(f"Order processing failed: {e}")
        return {"error": "system_error", "message": "Please try again"}
```

### **4. Result Types Estruturados**
```python
# ❌ Evitar:
agent = Agent('openai:gpt-4o')  # Retorna string genérica

# ✅ Preferir:
class OrderResult(BaseModel):
    success: bool
    order_id: int
    total_amount: float
    items: list[dict]

agent = Agent('openai:gpt-4o', result_type=OrderResult)
```

---

## ⚡ QUICK REFERENCE

```python
# Criar agent
agent = Agent('openai:gpt-4o', system_prompt='...')

# Adicionar tool
@agent.tool
def my_tool(param: str) -> str:
    return "result"

# Executar
result = agent.run_sync('prompt')
print(result.data)

# Com dependencies
result = agent.run_sync('prompt', deps=context)

# Com tipo estruturado
agent = Agent('openai:gpt-4o', result_type=MyModel)

# Tool com contexto
@agent.tool
def my_tool(ctx: RunContext[MyContext]) -> str:
    data = ctx.deps.database.query()
    return data
```

---

## ✅ RESUMO

**Pydantic-AI é ideal para o Munder Difflin porque:**
- ✅ Type-safe: Menos bugs
- ✅ Validação automática: Dados sempre corretos
- ✅ Dependency injection: Fácil compartilhar database
- ✅ Model-agnostic: Funciona com OpenAI
- ✅ Simples de usar: Curva de aprendizado baixa
- ✅ Testável: Fácil mockar dependencies

**Pronto para implementar!** 🚀