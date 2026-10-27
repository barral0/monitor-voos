"""Google Flights pela biblioteca fast-flights."""
from typing import Callable, List, Optional, Sequence

from ..modelos import Opcao, Voo
from .base import ErroProvedor

NOME = "Google Flights"
SEM_COMPANHIA = "Companhia n\u00e3o informada"


def parametros_consulta(voo: Voo) -> dict:
    return {
        "trechos": [(voo.ida, voo.origem, voo.destino), (voo.volta, voo.destino, voo.origem)],
        "trip": "round-trip", "seat": voo.classe, "currency": voo.moeda, "max_stops": voo.max_escalas, "language": "pt-BR",
    }


def converter_resultados(brutos: Sequence, max_escalas: int) -> List[Opcao]:
    opcoes = []
    for r in brutos:
        trechos = list(r.flights or [])
        escalas = max(len(trechos) - 1, 0)
        if escalas > max_escalas:
            continue
        opcoes.append(Opcao(
            provedor=NOME,
            preco=float(r.price),
            companhias=", ".join(r.airlines) if r.airlines else SEM_COMPANHIA,
            escalas=escalas,
            conexoes=tuple(t.to_airport.code for t in trechos[:-1]),
            duracao_min=sum(t.duration for t in trechos) or None,
        ))
    return opcoes


def _consulta_real(parametros: dict):
    from fast_flights import FlightQuery, create_query, get_flights
    consulta = create_query(
        flights=[FlightQuery(date=d.isoformat(), from_airport=a, to_airport=b, max_stops=parametros["max_stops"])
                 for d, a, b in parametros["trechos"]],
        trip=parametros["trip"], seat=parametros["seat"], currency=parametros["currency"],
        language=parametros["language"], max_stops=parametros["max_stops"], hide_separate_and_self_transfer=False,
    )
    return get_flights(consulta)


class GoogleFlights:
    nome = NOME

    def __init__(self, consultar: Optional[Callable[[dict], Sequence]] = None):
        self._consultar = consultar or _consulta_real

    def suporta(self, voo: Voo) -> bool:
        return True

    def buscar(self, voo: Voo) -> List[Opcao]:
        from fast_flights.exceptions import FlightsNotFound
        try:
            brutos = self._consultar(parametros_consulta(voo))
        except FlightsNotFound:
            return []
        except Exception as e:
            raise ErroProvedor(f"{NOME}: {e}") from e
        return converter_resultados(brutos or [], voo.max_escalas)
