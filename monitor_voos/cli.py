"""Interface de linha de comando: python -m monitor_voos <comando>."""
import argparse
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, List, Mapping, Optional

from .busca_flexivel import executar_busca
from .config import Configuracao, ConfiguracaoInvalida, Provedores, Telegram, carregar_configuracao
from .formatacao import formatar_data, formatar_preco
from .historico import Historico, chave_rota
from .mensagens import mensagem_busca_flexivel, mensagem_teste
from .modelos import Voo
from .monitor import executar_monitor
from .provedores.google_flights import GoogleFlights
from .provedores.kayak import Kayak
from .telegram import criar_enviador

CONFIG_PADRAO = "config.json"


def _provedores_reais(cfg: Configuracao) -> list:
    return [GoogleFlights(), Kayak(preco_minimo=cfg.provedores.kayak_preco_minimo)]


def _enviador_real(cfg: Configuracao, saida: Callable[[str], None]) -> Callable[[str], bool]:
    return criar_enviador(cfg.telegram.token, cfg.telegram.chat_id, saida=saida)


@dataclass
class Dependencias:
    provedores: Callable[[Configuracao], list] = _provedores_reais
    enviador: Callable[[Configuracao, Callable], Callable[[str], bool]] = _enviador_real
    agora: Callable[[], datetime] = datetime.now
    historico: Optional[Path] = None  # padrao: price_history.json ao lado do config


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="monitor_voos", description="Monitor de tarifas a\u00e9reas com alertas no Telegram.")
    sub = p.add_subparsers(dest="comando", required=True)

    m = sub.add_parser("monitorar", help="Consulta as datas fixas do config.json e avisa no Telegram.")
    m.add_argument("--config", default=CONFIG_PADRAO)

    f = sub.add_parser("flexivel", help="Varre v\u00e1rias datas de partida mantendo a dura\u00e7\u00e3o da viagem.")
    f.add_argument("--config", default=CONFIG_PADRAO)
    f.add_argument("--origin"); f.add_argument("--destination")
    f.add_argument("--start", help="Primeira partida (AAAA-MM-DD). Padr\u00e3o: daqui a 30 dias.")
    f.add_argument("--end", help="\u00daltima partida (AAAA-MM-DD). Padr\u00e3o: 180 dias ap\u00f3s o in\u00edcio.")
    f.add_argument("--stay-days", type=int, default=30)
    f.add_argument("--step-days", type=int, default=15)
    f.add_argument("--max-stops", type=int)
    f.add_argument("--telegram", action="store_true", help="Envia o ranking ao Telegram.")

    t = sub.add_parser("testar-telegram", help="Envia uma mensagem de teste.")
    t.add_argument("--config", default=CONFIG_PADRAO)
    return p


def _data_arg(valor: Optional[str], nome: str, padrao: date) -> date:
    if valor is None:
        return padrao
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise ConfiguracaoInvalida(f"{nome} deve estar no formato AAAA-MM-DD, recebido: {valor!r}.") from None


def _iata(valor: str, nome: str) -> str:
    if len(valor) != 3 or not valor.isalpha():
        raise ConfiguracaoInvalida(f"{nome} deve ser um c\u00f3digo IATA de 3 letras, recebido: {valor!r}.")
    return valor.upper()


def _comando_monitorar(args, deps: Dependencias, saida, ambiente) -> int:
    cfg = carregar_configuracao(args.config, ambiente)
    caminho = deps.historico or Path(args.config).resolve().parent / "price_history.json"
    historico = Historico.carregar(caminho, chave_legado=chave_rota(cfg.voo))
    if historico.aviso:
        saida(historico.aviso)
    r = executar_monitor(cfg, deps.provedores(cfg), historico, deps.enviador(cfg, saida), deps.agora(), saida)
    historico.salvar()
    return 1 if r.todas_falharam else 0


def _comando_flexivel(args, deps: Dependencias, saida, ambiente) -> int:
    existe = Path(args.config).exists()
    if existe:
        cfg = carregar_configuracao(args.config, ambiente)
    elif args.origin and args.destination:
        base = Voo(_iata(args.origin, "--origin"), _iata(args.destination, "--destination"), date.today(), date.today() + timedelta(days=1))
        cfg = Configuracao(base, Provedores(True, False, None), Telegram(False, None, None, False, False, False))
    else:
        raise ConfiguracaoInvalida(f"Arquivo de configura\u00e7\u00e3o n\u00e3o encontrado: {args.config}. Copie config.example.json "
                                   "para config.json ou informe --origin e --destination.")
    origem = _iata(args.origin, "--origin") if args.origin else cfg.voo.origem
    destino = _iata(args.destination, "--destination") if args.destination else cfg.voo.destino
    escalas = cfg.voo.max_escalas if args.max_stops is None else args.max_stops
    if not 0 <= escalas <= 3:
        raise ConfiguracaoInvalida("--max-stops deve ser de 0 a 3.")
    hoje = deps.agora().date()
    inicio = _data_arg(args.start, "--start", hoje + timedelta(days=30))
    fim = _data_arg(args.end, "--end", inicio + timedelta(days=180))

    provedores = [p for p in deps.provedores(cfg) if p.nome == "Google Flights"]
    if not provedores:
        raise ConfiguracaoInvalida("Nenhum buscador compat\u00edvel dispon\u00edvel para a busca flex\u00edvel.")
    try:
        r = executar_busca(origem, destino, inicio, fim, args.stay_days, args.step_days, escalas, cfg.voo.moeda, provedores[0],
                           saida=saida, classe=cfg.voo.classe, pausa_s=0 if deps.agora is not datetime.now else 1.0)
    except ValueError as e:
        raise ConfiguracaoInvalida(str(e)) from None

    if r.ranking:
        saida("")
        saida("Melhores op\u00e7\u00f5es:")
        for i, (j, o) in enumerate(r.ranking[:5], 1):
            saida(f"  {i}. {formatar_preco(o.preco, cfg.voo.moeda)} - {formatar_data(j.ida)} a {formatar_data(j.volta)} - {o.companhias} ({o.descricao_escalas()})")
    if args.telegram and r.ranking:
        texto = mensagem_busca_flexivel(origem, destino, escalas, inicio, fim, args.stay_days, r.ranking, cfg.voo.moeda)
        saida("Ranking enviado ao Telegram." if deps.enviador(cfg, saida)(texto) else "N\u00e3o foi poss\u00edvel enviar ao Telegram.")
    return 0


def _comando_testar_telegram(args, deps: Dependencias, saida, ambiente) -> int:
    cfg = carregar_configuracao(args.config, ambiente)
    ok = deps.enviador(cfg, saida)(mensagem_teste(cfg.voo.origem, cfg.voo.destino))
    saida("Mensagem de teste enviada." if ok else "Falha no envio da mensagem de teste.")
    return 0 if ok else 1


COMANDOS = {"monitorar": _comando_monitorar, "flexivel": _comando_flexivel, "testar-telegram": _comando_testar_telegram}


def main(argv: Optional[List[str]] = None, deps: Optional[Dependencias] = None, saida: Callable[[str], None] = print,
         ambiente: Optional[Mapping[str, str]] = None) -> int:
    try:
        args = construir_parser().parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        return COMANDOS[args.comando](args, deps or Dependencias(), saida, os.environ if ambiente is None else ambiente)
    except ConfiguracaoInvalida as e:
        saida(f"Erro: {e}")
        return 2
