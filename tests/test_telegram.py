import unittest
from types import SimpleNamespace

from monitor_voos.telegram import LIMITE_MENSAGEM, criar_enviador, enviar_mensagem

TOKEN = "123456:SEGREDO-do-bot"


class Resposta:
    def __init__(self, status=200, corpo=None):
        self.status_code, self._corpo = status, corpo if corpo is not None else {"ok": True}

    def json(self):
        return self._corpo


class Post:
    def __init__(self, resposta=None, erro=None):
        self.resposta, self.erro, self.chamadas = resposta or Resposta(), erro, []

    def __call__(self, url, json=None, timeout=None):
        self.chamadas.append(SimpleNamespace(url=url, json=json, timeout=timeout))
        if self.erro:
            raise self.erro
        return self.resposta


class TelegramTests(unittest.TestCase):
    def setUp(self):
        self.saida = []
        self.log = self.saida.append

    def test_envio_com_sucesso_usa_html(self):
        post = Post()
        self.assertTrue(enviar_mensagem(TOKEN, "42", "ola", post=post, saida=self.log))
        c = post.chamadas[0]
        self.assertEqual(c.url, f"https://api.telegram.org/bot{TOKEN}/sendMessage")
        self.assertEqual((c.json["chat_id"], c.json["text"], c.json["parse_mode"]), ("42", "ola", "HTML"))
        self.assertTrue(c.timeout)

    def test_sem_credenciais_nao_chama_a_rede(self):
        for token, chat in ((None, "1"), ("", "1"), (TOKEN, None), ("SEU_BOT_TOKEN_AQUI", "1"), (TOKEN, "SEU_CHAT_ID_AQUI")):
            post = Post()
            self.assertFalse(enviar_mensagem(token, chat, "x", post=post, saida=self.log))
            self.assertEqual(post.chamadas, [])
        self.assertIn("TELEGRAM_BOT_TOKEN", "\n".join(self.saida))

    def test_erro_da_api_e_informado(self):
        post = Post(Resposta(400, {"ok": False, "description": "chat not found"}))
        self.assertFalse(enviar_mensagem(TOKEN, "42", "x", post=post, saida=self.log))
        self.assertIn("chat not found", "\n".join(self.saida))

    def test_token_nunca_aparece_em_mensagens_de_erro(self):
        post = Post(erro=RuntimeError(f"falha em https://api.telegram.org/bot{TOKEN}/sendMessage"))
        self.assertFalse(enviar_mensagem(TOKEN, "42", "x", post=post, saida=self.log))
        texto = "\n".join(self.saida)
        self.assertNotIn("SEGREDO", texto); self.assertNotIn(TOKEN, texto)
        self.assertIn("***", texto)

    def test_mensagem_longa_e_cortada_no_limite_do_telegram(self):
        post = Post()
        enviar_mensagem(TOKEN, "42", "a" * (LIMITE_MENSAGEM + 500), post=post, saida=self.log)
        self.assertLessEqual(len(post.chamadas[0].json["text"]), LIMITE_MENSAGEM)

    def test_criar_enviador_amarra_credenciais(self):
        post = Post()
        enviar = criar_enviador(TOKEN, "42", post=post, saida=self.log)
        self.assertTrue(enviar("oi"))
        self.assertEqual(post.chamadas[0].json["chat_id"], "42")


if __name__ == "__main__":
    unittest.main()
