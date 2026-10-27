import json
import tempfile
import unittest
from pathlib import Path

from monitor_voos.historico import LIMITE_VERIFICACOES, Historico, chave_rota
from tests.fabricas import voo


class HistoricoTests(unittest.TestCase):
    def test_chave_identifica_rota_datas_moeda_e_escalas(self):
        self.assertEqual(chave_rota(voo()), "CNF-LAX|2027-05-01|2027-05-31|BRL|1")
        self.assertNotEqual(chave_rota(voo()), chave_rota(voo(max_escalas=0)))

    def test_arquivo_ausente_comeca_vazio(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Historico.carregar(Path(tmp) / "h.json")
            self.assertIsNone(h.menor_preco("x"))

    def test_registrar_salvar_e_recarregar(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / "h.json"
            h = Historico.carregar(caminho)
            h.registrar("A", {"timestamp": "t1", "menor_preco": 100.0}, 100.0)
            h.salvar()
            h2 = Historico.carregar(caminho)
            self.assertEqual(h2.menor_preco("A"), 100.0)
            self.assertEqual(h2.verificacoes("A")[0]["timestamp"], "t1")
            self.assertEqual(json.loads(caminho.read_text(encoding="utf-8"))["versao"], 2)

    def test_menor_preco_so_desce(self):
        h = Historico()
        h.registrar("A", {"timestamp": "1"}, 100.0)
        h.registrar("A", {"timestamp": "2"}, 150.0)
        self.assertEqual(h.menor_preco("A"), 100.0)
        h.registrar("A", {"timestamp": "3"}, 90.0)
        self.assertEqual(h.menor_preco("A"), 90.0)

    def test_registrar_sem_preco_nao_altera_o_menor(self):
        h = Historico(); h.registrar("A", {"timestamp": "1"}, 100.0); h.registrar("A", {"timestamp": "2"}, None)
        self.assertEqual(h.menor_preco("A"), 100.0); self.assertEqual(len(h.verificacoes("A")), 2)

    def test_rotas_sao_independentes(self):
        h = Historico(); h.registrar("A", {}, 100.0); h.registrar("B", {}, 500.0)
        self.assertEqual((h.menor_preco("A"), h.menor_preco("B")), (100.0, 500.0))

    def test_limite_de_verificacoes_guardadas(self):
        h = Historico()
        for i in range(LIMITE_VERIFICACOES + 20): h.registrar("A", {"n": i}, None)
        v = h.verificacoes("A")
        self.assertEqual((len(v), v[-1]["n"]), (LIMITE_VERIFICACOES, LIMITE_VERIFICACOES + 19))

    def test_formato_antigo_e_migrado_para_a_rota_atual(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / "h.json"
            caminho.write_text(json.dumps({"checks": [{"timestamp": "antigo", "lowest_price": 4000}], "lowest_recorded_price": 4000}), encoding="utf-8")
            h = Historico.carregar(caminho, chave_legado="CNF-LAX|2027-05-01|2027-05-31|BRL|1")
            self.assertEqual(h.menor_preco("CNF-LAX|2027-05-01|2027-05-31|BRL|1"), 4000)
            self.assertIsNone(h.menor_preco("OUTRA"))

    def test_arquivo_corrompido_e_preservado_nao_apagado(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / "h.json"; caminho.write_text("{quebrado", encoding="utf-8")
            h = Historico.carregar(caminho)
            self.assertIsNone(h.menor_preco("A"))
            self.assertTrue((Path(tmp) / "h.json.corrompido").exists())


if __name__ == "__main__":
    unittest.main()
