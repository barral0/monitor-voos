"""Leitura e validacao da configuracao. Segredos podem vir do ambiente."""
import json
import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Optional

from .modelos import Voo

CLASSES = ("economy", "premium-economy", "business", "first")
PRECO_MINIMO_KAYAK_PADRAO = 3000


class ConfiguracaoInvalida(ValueError):
    pass


@dataclass(frozen=True)
class Provedores:
    google_flights: bool
    kayak: bool
    kayak_preco_minimo: Optional[int]


@dataclass(frozen=True)
class Telegram:
    ativo: bool
    token: Optional[str]
    chat_id: Optional[str]
    sempre: bool
    ao_encontrar: bool
    ao_baratear: bool


@dataclass(frozen=True)
class Configuracao:
    voo: Voo
    provedores: Provedores
    telegram: Telegram


def _segredo(valor: Any) -> Optional[str]:
    """Vazio e marcadores de exemplo (SEU_..._AQUI) contam como nao configurado."""
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto or "_AQUI" in texto or texto.startswith(("SEU_", "COLE_SEU_")):
        return None
    return texto


def _iata(secao: Mapping, chave: str) -> str:
    valor = secao.get(chave)
    if not isinstance(valor, str) or not re.fullmatch(r"[A-Za-z]{3}", valor.strip()):
        raise ConfiguracaoInvalida(f"flight.{chave} deve ser um c\u00f3digo IATA de 3 letras (ex.: CNF), recebido: {valor!r}.")
    return valor.strip().upper()


def _data(secao: Mapping, chave: str) -> date:
    valor = secao.get(chave)
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        raise ConfiguracaoInvalida(f"flight.{chave} deve estar no formato AAAA-MM-DD, recebido: {valor!r}.") from None


def _booleano(secao: Mapping, chave: str, padrao: bool) -> bool:
    return bool(secao.get(chave, padrao))


def carregar_configuracao(caminho, ambiente: Optional[Mapping[str, str]] = None) -> Configuracao:
    ambiente = os.environ if ambiente is None else ambiente
    caminho = Path(caminho)
    if not caminho.exists():
        raise ConfiguracaoInvalida(f"Arquivo de configura\u00e7\u00e3o n\u00e3o encontrado: {caminho}. "
                                   "Copie config.example.json para config.json e preencha.")
    try:
        bruto = json.loads(caminho.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        raise ConfiguracaoInvalida(f"{caminho} n\u00e3o \u00e9 um JSON v\u00e1lido: {e}.") from None
    if not isinstance(bruto, dict) or not isinstance(bruto.get("flight"), dict):
        raise ConfiguracaoInvalida("A se\u00e7\u00e3o 'flight' \u00e9 obrigat\u00f3ria no config.json.")

    f = bruto["flight"]
    ida, volta = _data(f, "departure_date"), _data(f, "return_date")
    if volta <= ida:
        raise ConfiguracaoInvalida("flight.return_date deve ser posterior a flight.departure_date.")
    max_escalas = f.get("max_stops", 1)
    if isinstance(max_escalas, bool) or not isinstance(max_escalas, int) or not 0 <= max_escalas <= 3:
        raise ConfiguracaoInvalida(f"flight.max_stops deve ser um inteiro de 0 a 3, recebido: {max_escalas!r}.")
    moeda = str(f.get("currency", "BRL")).strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", moeda):
        raise ConfiguracaoInvalida(f"flight.currency deve ter 3 letras (ex.: BRL), recebido: {f.get('currency')!r}.")
    classe = f.get("seat_class", "economy")
    if classe not in CLASSES:
        raise ConfiguracaoInvalida(f"flight.seat_class deve ser um de {', '.join(CLASSES)}, recebido: {classe!r}.")
    if f.get("trip_type", "round-trip") != "round-trip":
        raise ConfiguracaoInvalida("flight.trip_type: apenas 'round-trip' (ida e volta) \u00e9 suportado.")
    alvo = f.get("target_price")
    if alvo is not None:
        if isinstance(alvo, bool) or not isinstance(alvo, (int, float)) or alvo <= 0:
            raise ConfiguracaoInvalida(f"flight.target_price deve ser um n\u00famero positivo, recebido: {alvo!r}.")
        alvo = float(alvo)
    voo = Voo(_iata(f, "origin"), _iata(f, "destination"), ida, volta, moeda, max_escalas, alvo, classe)

    p = bruto.get("providers") or {}
    minimo = p.get("kayak_min_price", PRECO_MINIMO_KAYAK_PADRAO)
    provedores = Provedores(_booleano(p, "google_flights", True), _booleano(p, "kayak", True), None if minimo is None else int(minimo))

    t = bruto.get("telegram") or {}
    telegram = Telegram(
        ativo=_booleano(t, "enabled", True),
        token=_segredo(ambiente.get("TELEGRAM_BOT_TOKEN")) or _segredo(t.get("bot_token")),
        chat_id=_segredo(ambiente.get("TELEGRAM_CHAT_ID")) or _segredo(t.get("chat_id")),
        sempre=_booleano(t, "notify_always", True),
        ao_encontrar=_booleano(t, "notify_when_found", True),
        ao_baratear=_booleano(t, "notify_when_cheaper", True),
    )
    return Configuracao(voo, provedores, telegram)
