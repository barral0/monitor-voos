"""Contrato dos buscadores de tarifas."""
from typing import List, Protocol

from ..modelos import Opcao, Voo


class ErroProvedor(Exception):
    """Falha ao consultar um buscador. Diferente de 'nenhum voo encontrado', que devolve lista vazia."""


class Provedor(Protocol):
    nome: str

    def suporta(self, voo: Voo) -> bool: ...

    def buscar(self, voo: Voo) -> List[Opcao]: ...
