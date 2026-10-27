"""Tipos de dominio compartilhados. Sem logica de rede nem de formatacao."""
from dataclasses import dataclass
from datetime import date
from typing import Optional, Tuple


@dataclass(frozen=True)
class Voo:
    """Consulta de ida e volta que o monitor acompanha."""
    origem: str
    destino: str
    ida: date
    volta: date
    moeda: str = "BRL"
    max_escalas: int = 1
    preco_alvo: Optional[float] = None
    classe: str = "economy"


@dataclass(frozen=True)
class Janela:
    ida: date
    volta: date


@dataclass(frozen=True)
class Opcao:
    """Uma tarifa encontrada por um buscador. `escalas=None` significa que a fonte nao informou."""
    provedor: str
    preco: float
    companhias: str
    escalas: Optional[int]
    conexoes: Tuple[str, ...] = ()
    duracao_min: Optional[int] = None

    def descricao_escalas(self) -> str:
        if self.escalas == 0:
            return "voo direto"
        if self.conexoes:
            return ("escala em " if len(self.conexoes) == 1 else "escalas em ") + ", ".join(self.conexoes)
        if self.escalas is None:
            return "escalas n\u00e3o informadas"
        return "1 escala" if self.escalas == 1 else f"{self.escalas} escalas"
