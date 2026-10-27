import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from monitor_voos.config import ConfiguracaoInvalida, carregar_configuracao


def escrever(tmp, dados, bom=False):
    p = Path(tmp) / "config.json"
    texto = json.dumps(dados)
    p.write_bytes((b"\xef\xbb\xbf" if bom else b"") + texto.encode("utf-8"))
    return p


BASE = {"flight": {"origin": "cnf", "destination": "lax", "departure_date": "2027-05-01", "return_date": "2027-05-31"},
        "telegram": {"bot_token": "123:ABC", "chat_id": "42"}}


def com(**mudancas):
    dados = json.loads(json.dumps(BASE))
    for caminho, valor in mudancas.items():
        secao, chave = caminho.split("__")
        dados.setdefault(secao, {})[chave] = valor
    return dados


class ConfigTests(unittest.TestCase):
    def carregar(self, dados, ambiente=None, bom=False):
        with tempfile.TemporaryDirectory() as tmp:
            return carregar_configuracao(escrever(tmp, dados, bom), ambiente if ambiente is not None else {})

    def test_leitura_basica_com_padroes(self):
        c = self.carregar(BASE)
        self.assertEqual((c.voo.origem, c.voo.destino), ("CNF", "LAX"))
        self.assertEqual((c.voo.ida, c.voo.volta), (date(2027, 5, 1), date(2027, 5, 31)))
        self.assertEqual((c.voo.moeda, c.voo.max_escalas, c.voo.classe, c.voo.preco_alvo), ("BRL", 1, "economy", None))
        self.assertTrue(c.provedores.google_flights and c.provedores.kayak)
        self.assertEqual(c.provedores.kayak_preco_minimo, 3000)
        self.assertTrue(c.telegram.ativo and c.telegram.sempre and c.telegram.ao_encontrar and c.telegram.ao_baratear)

    def test_aceita_bom_do_windows(self):
        self.assertEqual(self.carregar(BASE, bom=True).voo.origem, "CNF")

    def test_variaveis_de_ambiente_vencem_o_arquivo(self):
        c = self.carregar(BASE, {"TELEGRAM_BOT_TOKEN": "999:ZZZ", "TELEGRAM_CHAT_ID": "7"})
        self.assertEqual((c.telegram.token, c.telegram.chat_id), ("999:ZZZ", "7"))

    def test_marcadores_de_exemplo_contam_como_nao_configurado(self):
        c = self.carregar(com(telegram__bot_token="SEU_BOT_TOKEN_AQUI", telegram__chat_id="COLE_SEU_CHAT_ID_AQUI"))
        self.assertIsNone(c.telegram.token); self.assertIsNone(c.telegram.chat_id)

    def test_telegram_pode_ficar_sem_credenciais(self):
        c = self.carregar({"flight": BASE["flight"]})
        self.assertIsNone(c.telegram.token)

    def test_opcoes_numericas_e_booleanas(self):
        c = self.carregar(com(flight__max_stops=0, flight__target_price=4500, flight__currency="usd", flight__seat_class="business",
                              providers__kayak=False, providers__kayak_min_price=None, telegram__notify_always=False,
                              telegram__notify_when_found=False, telegram__notify_when_cheaper=False))
        self.assertEqual((c.voo.max_escalas, c.voo.preco_alvo, c.voo.moeda, c.voo.classe), (0, 4500.0, "USD", "business"))
        self.assertFalse(c.provedores.kayak); self.assertIsNone(c.provedores.kayak_preco_minimo)
        self.assertFalse(c.telegram.sempre or c.telegram.ao_encontrar or c.telegram.ao_baratear)

    def assertInvalida(self, dados, trecho):
        with self.assertRaises(ConfiguracaoInvalida) as ctx:
            self.carregar(dados)
        self.assertIn(trecho, str(ctx.exception))

    def test_validacoes_com_mensagens_claras(self):
        self.assertInvalida(com(flight__origin="BELO"), "origin")
        self.assertInvalida(com(flight__destination="L1X"), "destination")
        self.assertInvalida(com(flight__departure_date="01/05/2027"), "departure_date")
        self.assertInvalida(com(flight__return_date="2027-04-30"), "return_date")
        self.assertInvalida(com(flight__max_stops=-1), "max_stops")
        self.assertInvalida(com(flight__max_stops="um"), "max_stops")
        self.assertInvalida(com(flight__currency="REAL"), "currency")
        self.assertInvalida(com(flight__seat_class="vip"), "seat_class")
        self.assertInvalida(com(flight__trip_type="one-way"), "trip_type")
        self.assertInvalida(com(flight__target_price=-5), "target_price")

    def test_arquivo_ausente_ou_invalido(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ConfiguracaoInvalida) as ctx:
                carregar_configuracao(Path(tmp) / "nao-existe.json", {})
            self.assertIn("config.example.json", str(ctx.exception))
            ruim = Path(tmp) / "ruim.json"; ruim.write_text("{nao e json", encoding="utf-8")
            with self.assertRaises(ConfiguracaoInvalida):
                carregar_configuracao(ruim, {})


if __name__ == "__main__":
    unittest.main()
