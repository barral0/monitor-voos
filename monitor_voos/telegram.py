"""Envio de mensagens pelo Telegram. O token nunca aparece em saidas ou erros."""
from typing import Callable, Optional

LIMITE_MENSAGEM = 4096
TIMEOUT_S = 15


def _ausente(valor: Optional[str]) -> bool:
    return not valor or "_AQUI" in valor or valor.startswith(("SEU_", "COLE_SEU_"))


def _mascarar(texto: str, token: str) -> str:
    return texto.replace(token, "***")


def enviar_mensagem(token: Optional[str], chat_id: Optional[str], texto: str, post: Optional[Callable] = None,
                    saida: Callable[[str], None] = print) -> bool:
    if _ausente(token) or _ausente(chat_id):
        saida("Telegram n\u00e3o configurado: defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID (ou preencha o config.json).")
        return False
    if post is None:
        import requests
        post = requests.post
    corpo = {"chat_id": chat_id, "text": texto[:LIMITE_MENSAGEM], "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        resposta = post(f"https://api.telegram.org/bot{token}/sendMessage", json=corpo, timeout=TIMEOUT_S)
        dados = resposta.json()
    except Exception as e:
        saida(_mascarar(f"Falha ao enviar para o Telegram: {e}", token))
        return False
    if resposta.status_code == 200 and dados.get("ok"):
        return True
    saida(_mascarar(f"Telegram recusou a mensagem (HTTP {resposta.status_code}): {dados.get('description', 'sem detalhes')}", token))
    return False


def criar_enviador(token: Optional[str], chat_id: Optional[str], post: Optional[Callable] = None,
                   saida: Callable[[str], None] = print) -> Callable[[str], bool]:
    return lambda texto: enviar_mensagem(token, chat_id, texto, post=post, saida=saida)
