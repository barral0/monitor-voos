"""Textos das notificacoes (HTML do Telegram). Todo conteudo externo e escapado."""
from datetime import date, datetime
from html import escape
from typing import Dict, Iterable, Sequence, Tuple

from .alertas import Decisao
from .formatacao import formatar_data, formatar_duracao, formatar_preco, texto_escalas
from .links import gerar_links
from .modelos import Janela, Opcao, Voo

TOP_MONITOR = 5
TOP_FLEXIVEL = 5


def _e(texto) -> str:
    return escape(str(texto), quote=False)


def _links(links: Dict[str, str]) -> str:
    return " | ".join(f'<a href="{escape(url, quote=True)}">{_e(nome)}</a>' for nome, url in links.items())


def _linha_opcao(o: Opcao, moeda: str) -> str:
    duracao = formatar_duracao(o.duracao_min)
    return (f"\u2022 <b>{_e(formatar_preco(o.preco, moeda))}</b> - {_e(o.companhias)} "
            f"({_e(o.descricao_escalas())}){' ' + duracao if duracao else ''} [{_e(o.provedor)}]")


def _percentual(valor: float) -> str:
    return f"{valor:.1f}".replace(".", ",") + "%"


def _titulo(voo: Voo, decisao: Decisao) -> str:
    if decisao.motivo == "novo_menor":
        return (f"<b>NOVO MENOR PRE\u00c7O!</b> Economia de {_e(formatar_preco(decisao.economia, voo.moeda))} "
                f"({_e(_percentual(decisao.percentual))})")
    if decisao.motivo == "meta":
        return f"<b>META DE PRE\u00c7O ATINGIDA</b> (at\u00e9 {_e(formatar_preco(voo.preco_alvo, voo.moeda))})"
    if decisao.motivo == "encontrado":
        return "<b>VOOS ENCONTRADOS</b>"
    return ""


def mensagem_monitor(voo: Voo, opcoes: Sequence[Opcao], decisao: Decisao, links: Dict[str, str], agora: datetime) -> str:
    linhas = ["<b>Monitor de Voos</b>"]
    titulo = _titulo(voo, decisao)
    if titulo:
        linhas.append(titulo)
    linhas += [
        f"<b>{_e(voo.origem)} - {_e(voo.destino)}</b>",
        f"Ida {formatar_data(voo.ida)} | Volta {formatar_data(voo.volta)} | {texto_escalas(voo.max_escalas)}",
        f"Verificado em {agora.strftime('%d/%m/%Y %H:%M')}",
        "",
    ]
    if opcoes:
        linhas.append(f"Melhor tarifa: <b>{_e(formatar_preco(opcoes[0].preco, voo.moeda))}</b> [{_e(opcoes[0].provedor)}]")
        linhas += [_linha_opcao(o, voo.moeda) for o in opcoes[:TOP_MONITOR]]
    else:
        linhas.append(f"Nenhum voo encontrado com {texto_escalas(voo.max_escalas)} nesta verifica\u00e7\u00e3o.")
    linhas += ["", "Pesquisar e reservar:", _links(links)]
    return "\n".join(linhas)


def mensagem_busca_flexivel(origem: str, destino: str, max_escalas: int, inicio: date, fim: date, estadia: int,
                            ranking: Iterable[Tuple[Janela, Opcao]], moeda: str) -> str:
    linhas = [
        "<b>Busca flex\u00edvel de datas</b>",
        f"<b>{_e(origem)} - {_e(destino)}</b> | {texto_escalas(max_escalas)} | estadia de {estadia} dias",
        f"Partidas de {formatar_data(inicio, '%d/%m/%y')} a {formatar_data(fim, '%d/%m/%y')}",
        "",
    ]
    for posicao, (janela, opcao) in enumerate(list(ranking)[:TOP_FLEXIVEL], start=1):
        links = gerar_links(origem, destino, janela.ida, janela.volta, max_escalas, moeda)
        link = f'<a href="{escape(links["Google Flights"], quote=True)}">Google Flights</a>'
        linhas.append(f"{posicao}. <b>{_e(formatar_preco(opcao.preco, moeda))}</b> - "
                      f"{formatar_data(janela.ida, '%d/%m/%y')} a {formatar_data(janela.volta, '%d/%m/%y')} - "
                      f"{_e(opcao.companhias)} ({_e(opcao.descricao_escalas())}) {link}")
    return "\n".join(linhas)


def mensagem_teste(origem: str, destino: str) -> str:
    return f"<b>Teste do Monitor de Voos</b>\nConex\u00e3o com o Telegram funcionando. Rota configurada: {_e(origem)} - {_e(destino)}."
