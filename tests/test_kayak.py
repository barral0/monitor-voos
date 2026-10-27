import unittest

from monitor_voos.provedores.kayak import Kayak, deduplicar_por_preco, interpretar_cartao, url_kayak
from tests.fabricas import opcao, voo


class InterpretarCartaoTests(unittest.TestCase):
    def test_cartao_com_uma_escala(self):
        o = interpretar_cartao("Copa Airlines\n1 escala PTY\nR$ 4.416\nVer oferta", max_escalas=1)
        self.assertEqual((o.provedor, o.preco, o.companhias, o.escalas), ("Kayak / OTAs", 4416.0, "Copa", 1))

    def test_voo_direto(self):
        self.assertEqual(interpretar_cartao("Voo direto LATAM R$ 6.800", 1).escalas, 0)
        self.assertEqual(interpretar_cartao("Sem escalas R$ 6.800", 1).escalas, 0)

    def test_descarta_cartao_com_mais_escalas_que_o_limite(self):
        self.assertIsNone(interpretar_cartao("2 escalas R$ 3.900", 1))
        self.assertIsNone(interpretar_cartao("3 paradas R$ 3.900", 1))
        self.assertEqual(interpretar_cartao("2 escalas R$ 3.900", 2).escalas, 2)

    def test_preco_minimo_filtra_valores_que_nao_sao_tarifa(self):
        self.assertIsNone(interpretar_cartao("1 escala R$ 1.200", 1, preco_minimo=3000))
        self.assertEqual(interpretar_cartao("1 escala R$ 1.200", 1, preco_minimo=None).preco, 1200.0)

    def test_usa_o_menor_preco_valido_do_cartao(self):
        self.assertEqual(interpretar_cartao("1 escala R$ 4.900 R$ 4.416 R$ 900", 1).preco, 4416.0)

    def test_sem_preco_nao_gera_opcao(self):
        self.assertIsNone(interpretar_cartao("1 escala Copa", 1))

    def test_escalas_desconhecidas_nao_sao_inventadas(self):
        o = interpretar_cartao("LATAM R$ 4.416", 1)
        self.assertIsNone(o.escalas); self.assertEqual(o.conexoes, ())
        self.assertEqual(o.descricao_escalas(), "escalas n\u00e3o informadas")

    def test_companhia_desconhecida(self):
        self.assertEqual(interpretar_cartao("1 escala R$ 4.416", 1).companhias, "Companhias parceiras")

    def test_deteccao_de_companhia_ignora_maiusculas(self):
        self.assertEqual(interpretar_cartao("1 escala COPA AIRLINES R$ 4.416", 1).companhias, "Copa")


class ProvedorTests(unittest.TestCase):
    def test_deduplica_por_preco_mantendo_a_primeira(self):
        a, b, c = opcao(4000, companhias="A"), opcao(4000, companhias="B"), opcao(4500)
        self.assertEqual(deduplicar_por_preco([a, b, c]), [a, c])

    def test_so_suporta_reais(self):
        k = Kayak(preco_minimo=3000)
        self.assertTrue(k.suporta(voo(moeda="BRL")))
        self.assertFalse(k.suporta(voo(moeda="USD")))

    def test_url_da_busca(self):
        self.assertEqual(url_kayak(voo()), "https://www.kayak.com.br/flights/CNF-LAX/2027-05-01/2027-05-31?sort=price_a&fs=stops=~1")

    def test_usa_coletor_injetado(self):
        k = Kayak(preco_minimo=3000, coletar=lambda url: ["1 escala Copa R$ 4.416", "2 escalas R$ 3.900", "1 escala Copa R$ 4.416"])
        self.assertEqual([o.preco for o in k.buscar(voo())], [4416.0])


if __name__ == "__main__":
    unittest.main()
