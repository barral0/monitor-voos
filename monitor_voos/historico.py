"""Historico de precos por rota (origem, destino, datas, moeda e limite de escalas)."""
import json
from pathlib import Path
from typing import Dict, List, Optional

from .modelos import Voo

LIMITE_VERIFICACOES = 500
VERSAO = 2


def chave_rota(voo: Voo) -> str:
    return f"{voo.origem}-{voo.destino}|{voo.ida.isoformat()}|{voo.volta.isoformat()}|{voo.moeda}|{voo.max_escalas}"


class Historico:
    def __init__(self, caminho: Optional[Path] = None, rotas: Optional[Dict[str, dict]] = None):
        self.caminho = Path(caminho) if caminho else None
        self.rotas: Dict[str, dict] = rotas or {}
        self.aviso: Optional[str] = None

    @classmethod
    def carregar(cls, caminho, chave_legado: Optional[str] = None) -> "Historico":
        caminho = Path(caminho)
        h = cls(caminho)
        if not caminho.exists():
            return h
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8-sig"))
            if not isinstance(dados, dict):
                raise ValueError("formato inesperado")
        except (ValueError, OSError):
            destino = caminho.with_name(caminho.name + ".corrompido")
            caminho.replace(destino)
            h.aviso = f"Hist\u00f3rico ileg\u00edvel; preservado em {destino.name} e reiniciado."
            return h
        if dados.get("versao") == VERSAO:
            h.rotas = dados.get("rotas", {})
        elif "checks" in dados and chave_legado:
            h.rotas[chave_legado] = {"menor_preco": dados.get("lowest_recorded_price"), "verificacoes": list(dados["checks"])}
            h.aviso = "Hist\u00f3rico no formato antigo migrado para a rota atual."
        return h

    def menor_preco(self, chave: str) -> Optional[float]:
        return self.rotas.get(chave, {}).get("menor_preco")

    def verificacoes(self, chave: str) -> List[dict]:
        return self.rotas.get(chave, {}).get("verificacoes", [])

    def registrar(self, chave: str, verificacao: dict, preco: Optional[float]) -> None:
        rota = self.rotas.setdefault(chave, {"menor_preco": None, "verificacoes": []})
        rota["verificacoes"].append(verificacao)
        del rota["verificacoes"][:-LIMITE_VERIFICACOES]
        if preco is not None and (rota["menor_preco"] is None or preco < rota["menor_preco"]):
            rota["menor_preco"] = preco

    def salvar(self) -> None:
        if not self.caminho:
            return
        temporario = self.caminho.with_name(self.caminho.name + ".tmp")
        temporario.write_text(json.dumps({"versao": VERSAO, "rotas": self.rotas}, indent=2, ensure_ascii=False), encoding="utf-8")
        temporario.replace(self.caminho)
