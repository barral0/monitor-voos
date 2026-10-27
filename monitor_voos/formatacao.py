"""Formatacao de valores para exibicao em portugues do Brasil."""
from datetime import date
from typing import Optional

SIMBOLOS = {"BRL": "R$", "USD": "US$", "EUR": "\u20ac"}


def formatar_preco(valor: float, moeda: str = "BRL") -> str:
    numero = f"{valor:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    return f"{SIMBOLOS.get(moeda, moeda)} {numero}"


def formatar_duracao(minutos: Optional[int]) -> str:
    if not minutos:
        return ""
    return f"{minutos // 60}h{minutos % 60:02d}m"


def formatar_data(dia: date, formato: str = "%d/%m/%Y") -> str:
    return dia.strftime(formato)


def texto_escalas(max_escalas: int) -> str:
    if max_escalas == 0:
        return "somente voos diretos"
    return "m\u00e1ximo de 1 escala" if max_escalas == 1 else f"m\u00e1ximo de {max_escalas} escalas"
