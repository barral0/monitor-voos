"""Busca por varias datas de partida mantendo a duracao da viagem."""
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Callable, List, NamedTuple

from .formatacao import formatar_data, formatar_preco
from .modelos import Janela, Opcao, Voo
from .provedores.base import ErroProvedor


class Entrada(NamedTuple):
    janela: Janela
    opcao: Opcao


@dataclass
class Resultado:
    ranking: List[Entrada] = field(default_factory=list)
    testadas: int = 0
    falhas: int = 0


def gerar_janelas(inicio: date, fim: date, estadia_dias: int, passo_dias: int) -> List[Janela]:
    if passo_dias < 1:
        raise ValueError("O intervalo entre datas (step-days) deve ser de pelo menos 1 dia.")
    if estadia_dias < 1:
        raise ValueError("A estadia (stay-days) deve ser de pelo menos 1 dia.")
    if fim < inicio:
        raise ValueError("A data final deve ser igual ou posterior \u00e0 inicial.")
    janelas, dia = [], inicio
    while dia <= fim:
        janelas.append(Janela(dia, dia + timedelta(days=estadia_dias)))
        dia += timedelta(days=passo_dias)
    return janelas


def executar_busca(origem: str, destino: str, inicio: date, fim: date, estadia_dias: int, passo_dias: int, max_escalas: int,
                   moeda: str, provedor, saida: Callable[[str], None] = print, classe: str = "economy",
                   pausa_s: float = 0, dormir: Callable[[float], None] = time.sleep) -> Resultado:
    janelas = gerar_janelas(inicio, fim, estadia_dias, passo_dias)
    resultado = Resultado(testadas=len(janelas))
    for i, j in enumerate(janelas):
        if i and pausa_s:
            dormir(pausa_s)
        rotulo = f"{formatar_data(j.ida)} a {formatar_data(j.volta)}"
        voo = Voo(origem, destino, j.ida, j.volta, moeda, max_escalas, None, classe)
        try:
            opcoes = provedor.buscar(voo)
        except ErroProvedor as e:
            resultado.falhas += 1
            saida(f"[{i + 1}/{len(janelas)}] {rotulo}: falha na consulta ({e})")
            continue
        if not opcoes:
            saida(f"[{i + 1}/{len(janelas)}] {rotulo}: sem voos dentro do limite de escalas")
            continue
        melhor = min(opcoes, key=lambda o: o.preco)
        resultado.ranking.append(Entrada(j, melhor))
        saida(f"[{i + 1}/{len(janelas)}] {rotulo}: {formatar_preco(melhor.preco, moeda)} ({melhor.companhias})")
    resultado.ranking.sort(key=lambda e: e.opcao.preco)
    if not resultado.ranking:
        saida("Nenhuma op\u00e7\u00e3o encontrada no per\u00edodo." + (" Houve falhas de consulta; tente novamente." if resultado.falhas else ""))
    return resultado
