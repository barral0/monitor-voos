import unittest
from datetime import date

from monitor_voos.alertas import Decisao
from monitor_voos.links import gerar_links
from monitor_voos.mensagens import mensagem_busca_flexivel, mensagem_monitor, mensagem_teste
from monitor_voos.modelos import Janela
from tests.fabricas import AGORA, opcao, voo


def decisao(motivo="encontrado", economia=None, percentual=None):
    return Decisao(True, motivo, economia, percentual)


def links_de(v):
    return gerar_links(v.origem, v.destino, v.ida, v.volta, v.max_escalas, v.moeda)


class MensagensTests(unittest.TestCase):
    def test_mensagem_com_voos_traz_precos_no_padrao_brasileiro_e_links(self):
        v = voo()
        t = mensagem_monitor(v, [opcao(4416), opcao(4900, provedor="Kayak / OTAs", companhias="LATAM")], decisao(), links_de(v), AGORA)
        self.assertIn("R$ 4.416,00", t); self.assertIn("R$ 4.900,00", t)
        self.assertIn("CNF", t); self.assertIn("LAX", t); self.assertIn("27/10/2026", t)
        for nome in ("Google Flights", "Skyscanner", "Kiwi.com", "Kayak"):
            self.assertIn(nome, t)
        self.assertIn("<a href=", t)

    def test_texto_acompanha_o_limite_de_escalas_configurado(self):
        v = voo(max_escalas=2)
        t = mensagem_monitor(v, [opcao()], decisao(), links_de(v), AGORA)
        self.assertIn("m\u00e1ximo de 2 escalas", t)
        self.assertNotIn("1 ESCALA", t.upper().replace("M\u00c1XIMO DE 1 ESCALA", ""))

    def test_voos_diretos(self):
        v = voo(max_escalas=0)
        self.assertIn("somente voos diretos", mensagem_monitor(v, [opcao(escalas=0, conexoes=())], decisao(), links_de(v), AGORA))

    def test_conteudo_externo_e_escapado_para_html(self):
        v = voo()
        t = mensagem_monitor(v, [opcao(companhias="A&B <b>x</b> _y_ *z*")], decisao(), links_de(v), AGORA)
        self.assertIn("A&amp;B &lt;b&gt;x&lt;/b&gt; _y_ *z*", t)
        self.assertNotIn("<b>x</b>", t)

    def test_motivos_aparecem_no_titulo(self):
        v = voo(preco_alvo=4500)
        casos = {"encontrado": "ENCONTRADOS", "meta": "META", "sempre": "Monitor de Voos"}
        for motivo, trecho in casos.items():
            self.assertIn(trecho, mensagem_monitor(v, [opcao()], decisao(motivo), links_de(v), AGORA))
        t = mensagem_monitor(v, [opcao(3800)], decisao("novo_menor", 200.0, 5.0), links_de(v), AGORA)
        self.assertIn("NOVO MENOR", t); self.assertIn("R$ 200,00", t); self.assertIn("5,0%", t)

    def test_sem_voos(self):
        v = voo()
        t = mensagem_monitor(v, [], decisao("sempre"), links_de(v), AGORA)
        self.assertIn("Nenhum voo", t); self.assertIn("m\u00e1ximo de 1 escala", t); self.assertIn("Skyscanner", t)

    def test_nao_inventa_conexoes(self):
        v = voo()
        t = mensagem_monitor(v, [opcao(escalas=None, conexoes=(), provedor="Kayak / OTAs")], decisao(), links_de(v), AGORA)
        self.assertNotIn("Panam", t); self.assertNotIn("PTY", t)

    def test_busca_flexivel_lista_o_ranking_com_links(self):
        ranking = [(Janela(date(2027, 5, 1), date(2027, 5, 31)), opcao(4416)), (Janela(date(2027, 6, 1), date(2027, 7, 1)), opcao(4800))]
        t = mensagem_busca_flexivel("CNF", "LAX", 1, date(2027, 4, 1), date(2027, 8, 1), 30, ranking, "BRL")
        self.assertIn("R$ 4.416,00", t); self.assertIn("01/05/27", t); self.assertIn("31/05/27", t)
        self.assertIn("30 dias", t); self.assertIn("<a href=", t)

    def test_busca_flexivel_mostra_so_os_cinco_melhores(self):
        ranking = [(Janela(date(2027, 5, i + 1), date(2027, 6, i + 1)), opcao(4000 + i)) for i in range(8)]
        t = mensagem_busca_flexivel("CNF", "LAX", 1, date(2027, 5, 1), date(2027, 5, 8), 30, ranking, "BRL")
        self.assertIn("R$ 4.004,00", t); self.assertNotIn("R$ 4.005,00", t)

    def test_mensagem_de_teste(self):
        self.assertIn("Teste", mensagem_teste("CNF", "LAX"))


if __name__ == "__main__":
    unittest.main()
