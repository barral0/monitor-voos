"""Uma verificacao completa: consulta os buscadores, decide se avisa e atualiza o historico."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, List, Optional, Sequence

from .alertas import Decisao, decidir
from .config import Configuracao
from .formatacao import formatar_duracao, formatar_preco
from .historico import Historico, chave_rota
from .links import gerar_links
from .mensagens import mensagem_monitor
from .modelos import Opcao
from .provedores.base import ErroProvedor

NOME_GOOGLE = "Google Flights"
NOME_KAYAK = "Kayak / OTAs"


@dataclass
class Resultado:
    menor_preco: Optional[float]
    decisao: Decisao
    enviado: bool
    opcoes: List[Opcao] = field(default_factory=list)
    falhas: List[str] = field(default_factory=list)
    ignorados: List[str] = field(default_factory=list)
    consultados: int = 0

    @property
    def todas_falharam(self) -> bool:
        return self.consultados > 0 and len(self.falhas) == self.consultados


def _habilitado(provedor, cfg: Configuracao) -> bool:
    if provedor.nome == NOME_GOOGLE:
        return cfg.provedores.google_flights
    if provedor.nome == NOME_KAYAK:
        return cfg.provedores.kayak
    return True


def executar_monitor(cfg: Configuracao, provedores: Sequence, historico: Historico, enviar: Callable[[str], bool],
                     agora: datetime, saida: Callable[[str], None] = print) -> Resultado:
    voo = cfg.voo
    saida(f"Monitorando {voo.origem} - {voo.destino} ({voo.ida:%d/%m/%Y} a {voo.volta:%d/%m/%Y}, at\u00e9 {voo.max_escalas} escala(s))")
    opcoes: List[Opcao] = []
    falhas: List[str] = []
    ignorados: List[str] = []
    consultados = 0
    for p in provedores:
        if not _habilitado(p, cfg):
            continue
        if not p.suporta(voo):
            ignorados.append(f"{p.nome}: n\u00e3o suporta a moeda {voo.moeda}")
            saida(f"{p.nome}: ignorado (n\u00e3o suporta a moeda {voo.moeda})")
            continue
        consultados += 1
        try:
            achadas = p.buscar(voo)
        except ErroProvedor as e:
            falhas.append(str(e))
            saida(f"Falha na consulta: {e}")
            continue
        saida(f"{p.nome}: {len(achadas)} op\u00e7\u00e3o(\u00f5es)")
        opcoes += achadas
    opcoes.sort(key=lambda o: o.preco)
    for i, o in enumerate(opcoes[:5], 1):
        duracao = formatar_duracao(o.duracao_min)
        saida(f"  {i}. {formatar_preco(o.preco, voo.moeda)} [{o.provedor}] {o.companhias} ({o.descricao_escalas()}){' ' + duracao if duracao else ''}")

    chave = chave_rota(voo)
    menor = opcoes[0].preco if opcoes else None
    anterior = historico.menor_preco(chave)
    t = cfg.telegram
    decisao = decidir(menor, anterior, voo.preco_alvo, t.sempre, t.ao_encontrar, t.ao_baratear)
    historico.registrar(chave, {"timestamp": agora.isoformat(timespec="seconds"), "menor_preco": menor, "opcoes": len(opcoes),
                                "falhas": len(falhas)}, menor)
    if anterior is not None and menor is not None:
        saida(f"Menor pre\u00e7o anterior: {formatar_preco(anterior, voo.moeda)}")

    enviado = False
    if decisao.notificar and t.ativo:
        links = gerar_links(voo.origem, voo.destino, voo.ida, voo.volta, voo.max_escalas, voo.moeda)
        enviado = bool(enviar(mensagem_monitor(voo, opcoes, decisao, links, agora)))
        saida("Notifica\u00e7\u00e3o enviada." if enviado else "Notifica\u00e7\u00e3o n\u00e3o enviada.")
    else:
        saida("Sem novidades para avisar." if not decisao.notificar else "Telegram desativado na configura\u00e7\u00e3o.")
    return Resultado(menor, decisao, enviado, opcoes, falhas, ignorados, consultados)
