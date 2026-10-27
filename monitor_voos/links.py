"""Links de pesquisa nos buscadores, com o mesmo filtro de escalas da consulta."""
from datetime import date, datetime
from typing import Dict, Union

Data = Union[date, str]


def _como_data(valor: Data) -> date:
    return valor if isinstance(valor, date) else datetime.strptime(valor, "%Y-%m-%d").date()


def _filtro_google(max_escalas: int) -> str:
    if max_escalas == 0:
        return "%20nonstop"
    return "%20with%20at%20most%201%20stop" if max_escalas == 1 else f"%20with%20at%20most%20{max_escalas}%20stops"


def _filtro_skyscanner(max_escalas: int) -> str:
    return {0: "&stops=direct", 1: "&stops=!two_plus_stops"}.get(max_escalas, "")


def gerar_links(origem: str, destino: str, ida: Data, volta: Data, max_escalas: int = 1, moeda: str = "BRL") -> Dict[str, str]:
    d, r = _como_data(ida), _como_data(volta)
    ida_iso, volta_iso = d.isoformat(), r.isoformat()
    sky_ida, sky_volta = d.strftime("%y%m%d"), r.strftime("%y%m%d")
    return {
        "Google Flights": (f"https://www.google.com/travel/flights?q=Flights%20to%20{destino}%20from%20{origem}"
                           f"%20on%20{ida_iso}%20through%20{volta_iso}{_filtro_google(max_escalas)}"),
        "Skyscanner": (f"https://www.skyscanner.com.br/transporte/passagens-aereas/{origem.lower()}/{destino.lower()}/"
                       f"{sky_ida}/{sky_volta}/?adultsv2=1&cabinclass=economy&rtn=1{_filtro_skyscanner(max_escalas)}"),
        "Kiwi.com": (f"https://www.kiwi.com/deep?from={origem}&to={destino}&departure={ida_iso}&return={volta_iso}"
                     f"&currency={moeda}&lang=pt&max_stopovers={max_escalas}"),
        "Kayak": f"https://www.kayak.com.br/flights/{origem}-{destino}/{ida_iso}/{volta_iso}?sort=price_a&fs=stops=~{max_escalas}",
    }
