import unittest
from datetime import date

from monitor_voos.busca_flexivel import executar_busca, gerar_janelas
from monitor_voos.modelos import Janela
from monitor_voos.provedores.base import ErroProvedor
from tests.fabricas import opcao


class Provedor:
    nome = "Falso"

    def __init__(self, tabela):
        self.tabela, self.visto = tabela, []

    def buscar(self, voo):
        self.visto.append(voo)
        r = self.tabela.get(voo.ida, [])
        if isinstance(r, Exception):
            raise r
        return r


class JanelasTests(unittest.TestCase):
    def test_gera_janelas_com_estadia_fixa(self):
        j = gerar_janelas(date(2027, 4, 1), date(2027, 4, 21), 30, 10)
        self.assertEqual(j, [Janela(date(2027, 4, 1), date(2027, 5, 1)), Janela(date(2027, 4, 11), date(2027, 5, 11)), Janela(date(2027, 4, 21), date(2027, 5, 21))])

    def test_inicio_igual_ao_fim_gera_uma_janela(self):
        self.assertEqual(len(gerar_janelas(date(2027, 4, 1), date(2027, 4, 1), 30, 10)), 1)

    def test_parametros_invalidos(self):
        with self.assertRaises(ValueError): gerar_janelas(date(2027, 4, 1), date(2027, 4, 21), 30, 0)
        with self.assertRaises(ValueError): gerar_janelas(date(2027, 4, 1), date(2027, 4, 21), 0, 10)
        with self.assertRaises(ValueError): gerar_janelas(date(2027, 5, 1), date(2027, 4, 21), 30, 10)


class ExecucaoTests(unittest.TestCase):
    def rodar(self, tabela, **kw):
        saida = []
        p = Provedor(tabela)
        r = executar_busca("CNF", "LAX", date(2027, 4, 1), date(2027, 4, 21), 30, 10, 1, "BRL", p, saida=saida.append, **kw)
        return r, p, saida

    def test_ranking_ordenado_pelo_menor_preco_e_melhor_opcao_por_janela(self):
        r, p, _ = self.rodar({date(2027, 4, 1): [opcao(5000), opcao(4700)], date(2027, 4, 11): [opcao(4300)], date(2027, 4, 21): [opcao(4900)]})
        self.assertEqual([x.opcao.preco for x in r.ranking], [4300.0, 4700.0, 4900.0])
        self.assertEqual((r.testadas, r.falhas), (3, 0))
        self.assertEqual(len(p.visto), 3)

    def test_janela_sem_voos_nao_entra_no_ranking(self):
        r, _, saida = self.rodar({date(2027, 4, 1): [opcao(5000)]})
        self.assertEqual(len(r.ranking), 1); self.assertEqual(r.falhas, 0)
        self.assertTrue(any("sem voos" in s.lower() for s in saida))

    def test_falha_e_diferente_de_sem_voos(self):
        r, _, saida = self.rodar({date(2027, 4, 1): ErroProvedor("Google Flights: timeout"), date(2027, 4, 11): [opcao(4300)]})
        self.assertEqual((r.falhas, r.testadas, len(r.ranking)), (1, 3, 1))
        self.assertTrue(any("falha" in s.lower() and "timeout" in s for s in saida))

    def test_todas_as_janelas_usam_a_mesma_configuracao_de_voo(self):
        _, p, _ = self.rodar({})
        self.assertTrue(all((v.origem, v.destino, v.max_escalas, v.moeda) == ("CNF", "LAX", 1, "BRL") for v in p.visto))
        self.assertTrue(all((v.volta - v.ida).days == 30 for v in p.visto))

    def test_sem_nenhum_resultado(self):
        r, _, saida = self.rodar({})
        self.assertEqual(r.ranking, []); self.assertTrue(any("nenhuma" in s.lower() for s in saida))


if __name__ == "__main__":
    unittest.main()
