"""Objetos de teste. Dados sinteticos, sem rede."""
from datetime import date, datetime
from types import SimpleNamespace

from monitor_voos.modelos import Opcao, Voo


def voo(**kw):
    base = dict(origem="CNF", destino="LAX", ida=date(2027, 5, 1), volta=date(2027, 5, 31), moeda="BRL",
                max_escalas=1, preco_alvo=None, classe="economy")
    base.update(kw)
    return Voo(**base)


def opcao(preco=4416.0, provedor="Google Flights", companhias="COPA", escalas=1, conexoes=("PTY",), duracao_min=404):
    return Opcao(provedor=provedor, preco=preco, companhias=companhias, escalas=escalas,
                 conexoes=tuple(conexoes), duracao_min=duracao_min)


AGORA = datetime(2026, 10, 27, 13, 15)


def resultado_bruto(preco=4416, companhias=("COPA",), trechos=(("CNF", "PTY", 404), ("PTY", "LAX", 300))):
    """Imita o objeto devolvido pela biblioteca fast_flights (somente atributos usados)."""
    voos = [SimpleNamespace(duration=d, from_airport=SimpleNamespace(code=a), to_airport=SimpleNamespace(code=b))
            for a, b, d in trechos]
    return SimpleNamespace(price=preco, airlines=list(companhias), flights=voos)
