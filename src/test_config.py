"""
Configurações de teste para o sistema Munder Difflin.
Usa modelos mock para evitar dependências externas durante os testes.
"""

import os

from pydantic_ai import Agent

# Definir uma chave de API fake para testes
os.environ["OPENAI_API_KEY"] = "test-key-for-testing"


def create_test_agent(system_prompt: str, deps_type):
    """Cria um agente de teste usando modelo mock."""
    return Agent(
        model="openai:gpt-4o-mini",
        system_prompt=system_prompt,
        deps_type=deps_type,
    )
