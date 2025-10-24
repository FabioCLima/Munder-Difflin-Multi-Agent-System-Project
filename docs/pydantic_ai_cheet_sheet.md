# ⚡ PYDANTIC-AI CHEAT SHEET

## 🎯 O QUE É
Framework Python type-safe para criar agents baseados em LLMs com validação automática.

---

## 📦 INSTALAÇÃO
```bash
uv pip install pydantic-ai
```

---

## 🚀 EXEMPLOS RÁPIDOS

### **1. Agent Básico**
```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o')
result = agent.run_sync('Hello!')
print(result.data)  # "Hello! How can I help you?"
```

### **2. Agent com Tool**
```python
agent = Agent('openai:gpt-4o')

@agent.tool
def get_weather(city: str) -> dict:
    """Get weather for a city."""
    return {"temp": 22, "condition": "Sunny"}

result = agent.run_sync("Weather in Paris?")
# LLM chama get_weather() automaticamente
```

### **3. Agent com Resultado Estruturado**
```python
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: float

agent = Agent('openai:gpt-4o', result_type=Product)
result = agent.run_sync("iPhone 15, $999")
print(result.data.name)   # "iPhone 15"
print(result.data.price)  # 999.0
```

### **4. Agent com Dependencies**
```python
from pydantic_ai import RunContext
from dataclasses import dataclass

@dataclass
class DBContext:
    db: str
    user_id: int

agent = Agent('openai:gpt-4o', deps_type=DBContext)

@agent.tool
def get_orders(ctx: RunContext[DBContext]) -> list:
    user_id = ctx.deps.user_id  # Acessa contexto
    return [{"order_id": 1, "total": 100}]

context = DBContext(db="sqlite", user_id=42)
result = agent.run_sync("My orders?", deps=context)
```

---

## 🛠️ CONCEITOS-CHAVE

| Conceito | O que é |
|----------|---------|
| **Agent** | Unidade que conversa com LLM |
| **Tool** | Função Python que agent pode chamar |
| **Dependencies** | Contexto compartilhado (DB, config, etc) |
| **Result Type** | Tipo estruturado de retorno |
| **System Prompt** | Instruções base do agent |

---

## 📝 PATTERNS COMUNS

### **Pattern 1: Orchestrator**
```python
orchestrator = Agent('openai:gpt-4o')

@orchestrator.tool
def delegate_to_inventory(query: str) -> str:
    return inventory_agent.run_sync(query).data
```

### **Pattern 2: Tool com Validação**
```python
@agent.tool
def add_stock(item: str, qty: int) -> dict:
    if qty <= 0:
        return {"error": "Invalid quantity"}
    # Processar...
    return {"success": True}
```

### **Pattern 3: Tool com Logging**
```python
from loguru import logger

@agent.tool
def process_order(order: dict) -> dict:
    logger.info(f"Processing order: {order}")
    # Processar...
    logger.debug("Order processed successfully")
    return {"status": "completed"}
```

---

## 🎯 NOSSA APLICAÇÃO (MUNDER DIFFLIN)

```python
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass

@dataclass
class DatabaseContext:
    db_engine: Engine
    current_date: str

# Inventory Agent
inventory_agent = Agent(
    'openai:gpt-4o',
    deps_type=DatabaseContext,
    system_prompt='You manage paper inventory.'
)

@inventory_agent.tool
def check_stock(ctx: RunContext[DatabaseContext], item: str) -> int:
    return get_stock_level(item, ctx.deps.current_date)

# Quoting Agent
class QuoteResult(BaseModel):
    total_amount: float
    explanation: str

quoting_agent = Agent(
    'openai:gpt-4o',
    result_type=QuoteResult,
    deps_type=DatabaseContext
)

@quoting_agent.tool
def search_quotes(ctx: RunContext[DatabaseContext], keywords: list) -> list:
    return search_quote_history(keywords, limit=5)

# Orchestrator
orchestrator = Agent('openai:gpt-4o', deps_type=DatabaseContext)

@orchestrator.tool
def ask_inventory(ctx: RunContext[DatabaseContext], query: str) -> str:
    return inventory_agent.run_sync(query, deps=ctx.deps).data
```

---

## ✅ VANTAGENS

1. ✅ **Type-safe**: MyPy detecta erros
2. ✅ **Validação automática**: Pydantic valida dados
3. ✅ **Model-agnostic**: Funciona com OpenAI, Anthropic, etc
4. ✅ **Dependency injection**: Fácil compartilhar contexto
5. ✅ **Simples**: Menos código que LangChain

---

## 📚 RECURSOS

- **Docs**: https://ai.pydantic.dev/
- **GitHub**: https://github.com/pydantic/pydantic-ai
- **Guia completo**: [STEP3_PYDANTIC_AI_GUIDE.md](STEP3_PYDANTIC_AI_GUIDE.md)

---

## 🎓 COMANDOS ESSENCIAIS

```python
# Criar agent
agent = Agent('openai:gpt-4o', system_prompt='...')

# Adicionar tool
@agent.tool
def my_tool(param: str) -> str:
    return "result"

# Executar (sync)
result = agent.run_sync('prompt')

# Executar (async)
result = await agent.run('prompt')

# Com dependencies
result = agent.run_sync('prompt', deps=context)

# Ver mensagens
for msg in result.all_messages():
    print(f"{msg.role}: {msg.content}")
```

---

## ⚡ PRONTO PARA IMPLEMENTAR!

Use este cheat sheet + guia completo para referência durante o desenvolvimento.