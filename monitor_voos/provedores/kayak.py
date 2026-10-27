"""Kayak e agencias parceiras, lidos de uma pagina renderizada com Playwright.

A leitura depende do HTML do site e pode quebrar sem aviso: por isso so devolve o que o texto do cartao afirma
(escalas e companhia) e nunca inventa conexoes.
"""
import re
from typing import Callable, List, Optional, Sequence

from ..modelos import Opcao, Voo
from .base import ErroProvedor

NOME = "Kayak / OTAs"
PRECO_MINIMO_PADRAO = 3000
COMPANHIAS = ("Copa", "LATAM", "Gol", "American", "United", "Delta", "Avianca", "Aeromexico")
MAX_CARTOES = 10
ESPERA_MS = 8000


def url_kayak(voo: Voo) -> str:
    return f"https://www.kayak.com.br/flights/{voo.origem}-{voo.destino}/{voo.ida.isoformat()}/{voo.volta.isoformat()}?sort=price_a&fs=stops=~{voo.max_escalas}"


def _escalas_do_texto(texto: str) -> Optional[int]:
    baixo = texto.lower()
    achou = re.search(r"(\d+)\s*(?:escalas?|paradas?)", baixo)
    if achou:
        return int(achou.group(1))
    if "voo direto" in baixo or "sem escala" in baixo or re.search(r"\bdireto\b", baixo):
        return 0
    return None


def interpretar_cartao(texto: str, max_escalas: int, preco_minimo: Optional[int] = PRECO_MINIMO_PADRAO) -> Optional[Opcao]:
    escalas = _escalas_do_texto(texto)
    if escalas is not None and escalas > max_escalas:
        return None
    precos = [int(p.replace(".", "")) for p in re.findall(r"R\$\s?(\d[\d.]*)", texto)]
    validos = [p for p in precos if preco_minimo is None or p >= preco_minimo]
    if not validos:
        return None
    baixo = texto.lower()
    companhia = next((c for c in COMPANHIAS if c.lower() in baixo), "Companhias parceiras")
    return Opcao(NOME, float(min(validos)), companhia, escalas)


def deduplicar_por_preco(opcoes: Sequence[Opcao]) -> List[Opcao]:
    vistos, unicas = set(), []
    for o in opcoes:
        if o.preco not in vistos:
            vistos.add(o.preco)
            unicas.append(o)
    return unicas


def _coletar_com_playwright(url: str) -> List[str]:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        try:
            contexto = navegador.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768}, locale="pt-BR")
            pagina = contexto.new_page()
            pagina.goto(url, wait_until="domcontentloaded", timeout=35000)
            pagina.wait_for_timeout(ESPERA_MS)
            cartoes = pagina.query_selector_all("div[class*='resultWrapper'], div[class*='nrc6']")
            return [c.inner_text() for c in cartoes[:MAX_CARTOES]]
        finally:
            navegador.close()


class Kayak:
    nome = NOME

    def __init__(self, preco_minimo: Optional[int] = PRECO_MINIMO_PADRAO, coletar: Optional[Callable[[str], Sequence[str]]] = None):
        self.preco_minimo = preco_minimo
        self._coletar = coletar or _coletar_com_playwright

    def suporta(self, voo: Voo) -> bool:
        return voo.moeda == "BRL"  # o site e a leitura de precos usam reais

    def buscar(self, voo: Voo) -> List[Opcao]:
        try:
            textos = self._coletar(url_kayak(voo))
        except Exception as e:
            raise ErroProvedor(f"{NOME}: {e}") from e
        opcoes = [interpretar_cartao(t, voo.max_escalas, self.preco_minimo) for t in textos]
        return deduplicar_por_preco([o for o in opcoes if o])
