#!/bin/bash
# Script de Setup Automático - Munder Difflin Multi-Agent System
# Uso: ./setup.sh

set -e  # Exit on error

echo "🚀 Munder Difflin Multi-Agent System - Setup"
echo "=============================================="
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para print colorido
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar se está no diretório correto
if [ ! -f "pyproject.toml" ]; then
    print_error "pyproject.toml não encontrado. Execute este script no diretório raiz do projeto."
    exit 1
fi

print_success "Diretório do projeto encontrado"

# Verificar se UV está instalado
if ! command -v uv &> /dev/null; then
    print_warning "UV não encontrado. Instalando..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    print_success "UV instalado"
else
    print_success "UV já instalado: $(uv --version)"
fi

# Verificar se .venv existe
if [ ! -d ".venv" ]; then
    print_warning ".venv não encontrado. Criando ambiente virtual..."
    uv venv
    print_success "Ambiente virtual criado"
else
    print_success "Ambiente virtual já existe"
fi

# Ativar ambiente virtual
print_warning "Ativando ambiente virtual..."
source .venv/bin/activate
print_success "Ambiente virtual ativado"

# Instalar dependências
print_warning "Instalando dependências..."
uv pip install -e ".[dev]"
print_success "Dependências instaladas"

# Criar diretório de logs se não existir
if [ ! -d "logs" ]; then
    mkdir -p logs
    print_success "Diretório logs/ criado"
fi

# Criar .env se não existir
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_warning ".env criado a partir de .env.example - EDITE COM SUAS CHAVES!"
    else
        print_warning ".env não encontrado - crie manualmente"
    fi
else
    print_success ".env já existe"
fi

# Verificar instalação
print_warning "Verificando instalação..."
python -c "from pydantic_ai import Agent; from loguru import logger; import pytest" 2>/dev/null
if [ $? -eq 0 ]; then
    print_success "Todas as dependências principais instaladas corretamente"
else
    print_error "Erro ao importar dependências. Verifique a instalação."
    exit 1
fi

# Mostrar pacotes instalados
echo ""
echo "📦 Pacotes principais instalados:"
uv pip list | grep -E "pydantic-ai|loguru|pytest|ruff|pandas|openai|sqlalchemy" | head -10

echo ""
echo "=============================================="
print_success "Setup concluído com sucesso!"
echo ""
echo "📝 Próximos passos:"
echo "   1. Edite o arquivo .env com suas chaves de API"
echo "   2. Execute: python main.py"
echo "   3. Para testes: pytest"
echo "   4. Para formatar: ruff format ."
echo ""
echo "💡 Dica: Mantenha o ambiente ativado com: source .venv/bin/activate"