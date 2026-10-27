import unittest
from datetime import date

from fast_flights.exceptions import FlightsNotFound

from monitor_voos.provedores.base import ErroProvedor
from monitor_voos.provedores.google_flights import GoogleFlights, converter_resultados, parametros_consulta
from tests.fabricas import resultado_bruto, voo


class ConversaoTests(unittest.TestCase):
    def test_converte_resultado_com_uma_conexao(self):
        (o,) = converter_resultados([resultado_bruto()], max_escalas=1)
        self.assertEqual((o.provedor, o.preco, o.companhias, o.escalas, o.conexoes, o.duracao_min),
                         ("Google Flights", 4416.0, "COPA", 1, ("PTY",), 704))
        self.assertEqual(o.descricao_escalas(), "escala em PTY")

    def test_voo_direto(self):
        (o,) = converter_resultados([resultado_bruto(trechos=(("CNF", "LAX", 600),))], max_escalas=1)
        self.assertEqual((o.escalas, o.conexoes, o.descricao_escalas()), (0, (), "voo direto"))

    def test_descarta_mais_escalas_que_o_limite(self):
        tres = resultado_bruto(trechos=(("CNF", "PTY", 300), ("PTY", "MIA", 200), ("MIA", "LAX", 300)))
        self.assertEqual(converter_resultados([tres], max_escalas=1), [])
        self.assertEqual(len(converter_resultados([tres], max_escalas=2)), 1)

    def test_varias_companhias_e_nenhuma(self):
        (a,) = converter_resultados([resultado_bruto(companhias=("COPA", "LATAM"))], 1)
        self.assertEqual(a.companhias, "COPA, LATAM")
        (b,) = converter_resultados([resultado_bruto(companhias=())], 1)
        self.assertEqual(b.companhias, "Companhia n\u00e3o informada")


class ConsultaTests(unittest.TestCase):
    def test_parametros_usam_a_configuracao_inclusive_a_classe(self):
        p = parametros_consulta(voo(classe="business", max_escalas=0, moeda="USD"))
        self.assertEqual((p["seat"], p["trip"], p["currency"], p["max_stops"], p["language"]), ("business", "round-trip", "USD", 0, "pt-BR"))
        self.assertEqual(p["trechos"], [(date(2027, 5, 1), "CNF", "LAX"), (date(2027, 5, 31), "LAX", "CNF")])

    def test_sem_voos_nao_e_erro(self):
        def consultar(_):
            raise FlightsNotFound()
        self.assertEqual(GoogleFlights(consultar).buscar(voo()), [])

    def test_falha_inesperada_vira_erro_do_provedor(self):
        def consultar(_):
            raise RuntimeError("timeout")
        with self.assertRaises(ErroProvedor) as ctx:
            GoogleFlights(consultar).buscar(voo())
        self.assertIn("Google Flights", str(ctx.exception)); self.assertIn("timeout", str(ctx.exception))

    def test_busca_devolve_opcoes_convertidas(self):
        p = GoogleFlights(lambda parametros: [resultado_bruto(4000), resultado_bruto(5000)])
        self.assertEqual([o.preco for o in p.buscar(voo())], [4000.0, 5000.0])
        self.assertEqual(p.nome, "Google Flights")


if __name__ == "__main__":
    unittest.main()
