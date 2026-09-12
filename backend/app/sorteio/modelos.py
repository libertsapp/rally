"""Estruturas de dados puras usadas pelo módulo de sorteio.

Sem qualquer dependência de banco (SQLAlchemy) ou de API (FastAPI/Pydantic) —
o sorteio recebe e devolve só isto, o que permite testá-lo isoladamente.
"""

from dataclasses import dataclass


@dataclass
class JogadorSorteio:
    id: str
    nome: str
    estrelas: float = 0
    sexo: str = ""  # "F" | "M" | ""
    porte: str = ""  # "P" | "M" | "G" | ""
