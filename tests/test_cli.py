import json
import tempfile
import unittest
from pathlib import Path

from monitor_voos.cli import Dependencias, construir_parser, main
from tests.fabricas import AGORA, opcao

CFG = {"flight": {"origin": "CNF", "destination": "LAX", "departure_date": "2027-05-01", "return_date": "2027-05-31"},
       "telegram": {"bot_token": "123:T", "chat_id": "42", "notify_always": False}}


class Provedor:
    nome = "Google Flights"

    def suporta(self, voo):
        return True

    def buscar(self, voo):
        return [opcao(4416)]


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.cfg = self.dir / "config.json"; self.cfg.write_text(json.dumps(CFG), encoding="utf-8")
        self.saida, self.enviadas = [], []
        self.deps = Dependencias(provedores=lambda cfg: [Provedor()], enviador=lambda cfg, saida: (lambda t: self.enviadas.append(t) or True),
                                 agora=lambda: AGORA, historico=self.dir / "h.json")

    def rodar(self, *argv):
        return main(list(argv), deps=self.deps, saida=self.saida.append, ambiente={})

    def test_subcomandos_disponiveis(self):
        acoes = construir_parser()._subparsers._group_actions[0].choices
        self.assertEqual(set(acoes), {"monitorar", "flexivel", "testar-telegram"})

    def test_monitorar_de_ponta_a_ponta(self):
        self.assertEqual(self.rodar("monitorar", "--config", str(self.cfg)), 0)
        self.assertEqual(len(self.enviadas), 1)
        self.assertEqual(json.loads((self.dir / "h.json").read_text(encoding="utf-8"))["versao"], 2)

    def test_segunda_execucao_com_mesmo_preco_nao_reenvia(self):
        self.rodar("monitorar", "--config", str(self.cfg)); self.rodar("monitorar", "--config", str(self.cfg))
        self.assertEqual(len(self.enviadas), 1)

    def test_config_inexistente_retorna_2_com_orientacao(self):
        self.assertEqual(self.rodar("monitorar", "--config", str(self.dir / "nao.json")), 2)
        self.assertIn("config.example.json", "\n".join(self.saida))

    def test_flexivel_sem_telegram_nao_envia(self):
        self.assertEqual(self.rodar("flexivel", "--config", str(self.cfg), "--start", "2027-04-01", "--end", "2027-04-21", "--step-days", "10"), 0)
        self.assertEqual(self.enviadas, []); self.assertIn("R$ 4.416,00", "\n".join(self.saida))

    def test_flexivel_com_telegram_envia_o_ranking(self):
        self.rodar("flexivel", "--config", str(self.cfg), "--start", "2027-04-01", "--end", "2027-04-11", "--step-days", "10", "--telegram")
        self.assertEqual(len(self.enviadas), 1); self.assertIn("R$ 4.416,00", self.enviadas[0])

    def test_flexivel_funciona_sem_config_usando_apenas_argumentos(self):
        self.assertEqual(self.rodar("flexivel", "--config", str(self.dir / "nao.json"), "--origin", "GRU", "--destination", "MIA",
                                    "--start", "2027-04-01", "--end", "2027-04-01"), 0)

    def test_flexivel_valida_argumentos(self):
        self.assertEqual(self.rodar("flexivel", "--config", str(self.cfg), "--start", "2027-05-01", "--end", "2027-04-01"), 2)
        self.assertEqual(self.rodar("flexivel", "--config", str(self.cfg), "--start", "01/05/2027"), 2)
        self.assertEqual(self.rodar("flexivel", "--config", str(self.cfg), "--origin", "BELO"), 2)
        self.assertEqual(self.rodar("flexivel", "--config", str(self.cfg), "--step-days", "0"), 2)

    def test_testar_telegram(self):
        self.assertEqual(self.rodar("testar-telegram", "--config", str(self.cfg)), 0)
        self.assertEqual(len(self.enviadas), 1)

    def test_testar_telegram_sem_credenciais_retorna_1(self):
        sem = self.dir / "sem.json"; sem.write_text(json.dumps({"flight": CFG["flight"]}), encoding="utf-8")
        self.deps = Dependencias(provedores=self.deps.provedores, enviador=lambda cfg, saida: (lambda t: False), agora=self.deps.agora, historico=self.deps.historico)
        self.assertEqual(self.rodar("testar-telegram", "--config", str(sem)), 1)


if __name__ == "__main__":
    unittest.main()
