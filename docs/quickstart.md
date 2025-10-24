# 🚀 QUICKSTART - Comandos Essenciais

## 📦 INSTALAÇÃO (ESCOLHA UMA OPÇÃO)

### Opção 1: Script Automático (Recomendado)
```bash
chmod +x setup.sh
./setup.sh
```

### Opção 2: Manual com UV
```bash
# 1. Ativar ambiente
source .venv/bin/activate

# 2. Substituir pyproject.toml (copie o arquivo fornecido)
cp /caminho/outputs/pyproject.toml ./

# 3. Instalar dependências
uv pip install -e ".[dev]"

# 4. Verificar
python -c "from pydantic_ai import Agent; print('✅ OK')"
```

### Opção 3: Fallback com pip tradicional
```bash
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-cov ruff ipython
```

## 🎯 COMANDOS DO DIA-A-DIA

```bash
# Ativar ambiente
source .venv/bin/activate

# Rodar projeto
python main.py

# Rodar testes
pytest

# Formatar código
ruff format .

# Checar qualidade
ruff check .

# Ver logs
tail -f logs/munder_difflin.log
```

## 🐛 SE DER ERRO

### Erro: "No module named 'src'"
```bash
uv pip install -e . --reinstall
```

### Erro: "pydantic_ai not found"
```bash
uv pip install pydantic-ai pydantic --upgrade
```

### Erro: Build failed
```bash
# Use o pyproject.toml fornecido nos outputs
cp /caminho/outputs/pyproject.toml ./
uv pip install -e .
```

## ✅ CHECKLIST DE VERIFICAÇÃO

- [ ] .venv ativado
- [ ] pyproject.toml atualizado
- [ ] Dependências instaladas
- [ ] .env configurado com API keys
- [ ] `python -c "from pydantic_ai import Agent; print('OK')"` funciona
- [ ] `pytest` roda sem erros
- [ ] `python main.py` executa

## 📁 ESTRUTURA DE IMPORTS

```python
# main.py
from src.agents.orchestrator import OrchestratorAgent
from src.database import init_database
from src.utils.logging_config import setup_logging, logger

# src/agents/inventory_agent.py
from src.tools.inventory_tools import check_inventory_tool
from src.utils.logging_config import logger
```

## 🎓 LEMBRE-SE

1. **Sempre ative o .venv**: `source .venv/bin/activate`
2. **Formate antes de commitar**: `ruff format .`
3. **Rode testes frequentemente**: `pytest`
4. **Veja os logs**: `tail -f logs/munder_difflin.log`
5. **Use o logger**: `from src.utils.logging_config import logger`