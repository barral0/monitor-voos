"""Regra pura de quando avisar. Nao conhece rede, arquivo nem texto."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Decisao:
    notificar: bool
    motivo: Optional[str] = None  # encontrado | novo_menor | meta | sempre
    economia: Optional[float] = None
    percentual: Optional[float] = None


def decidir(menor_preco: Optional[float], menor_anterior: Optional[float], preco_alvo: Optional[float],
            notificar_sempre: bool, ao_encontrar: bool, ao_baratear: bool) -> Decisao:
    motivo, economia, percentual = None, None, None
    if menor_preco is not None:
        if menor_anterior is None:
            if ao_encontrar:
                motivo = "encontrado"
        elif menor_preco < menor_anterior:
            if ao_baratear:
                motivo, economia = "novo_menor", menor_anterior - menor_preco
                percentual = economia / menor_anterior * 100
        if motivo is None and preco_alvo is not None and menor_preco <= preco_alvo:
            motivo = "meta"
    if motivo is None and notificar_sempre:
        motivo = "sempre"
    return Decisao(motivo is not None, motivo, economia, percentual)
