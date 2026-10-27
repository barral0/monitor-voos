import unittest

from monitor_voos.config import Configuracao, Provedores, Telegram
from monitor_voos.historico import Historico, chave_rota
from monitor_voos.monitor import executar_monitor
from monitor_voos.provedores.base import ErroProvedor
from tests.fabricas import AGORA, opcao, voo


class Falso:
    def __init__(self, nome, opcoes=None, erro=None, aceita=True):
        self.nome, self.opcoes, self.erro, self.aceita, self.chamadas = nome, opcoes or [], erro, aceita, 0

    def suporta(self, v):
        return self.aceita

    def buscar(self, v):
        self.chamadas += 1
        if self.erro:
            raise ErroProvedor(self.erro)
        return list(self.opcoes)


def configuracao(v=None, sempre=False, ativo=True, encontrar=True, baratear=True):
    return Configuracao(v or voo(), Provedores(True, True, 3000), Telegram(ativo, "123:T", "42", sempre, encontrar, baratear))


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.saida, self.enviadas, self.historico = [], [], Historico()

    def enviar(self, texto):
        self.enviadas.append(texto)
        return True

    def rodar(self, cfg, provedores):
        return executar_monitor(cfg, provedores, self.historico, self.enviar, AGORA, self.saida.append)

    def test_primeira_consulta_com_voos_notifica_e_grava_o_menor_preco(self):
        cfg = configuracao()
        r = self.rodar(cfg, [Falso("G", [opcao(4900), opcao(4416)])])
        self.assertEqual((r.menor_preco, r.decisao.motivo, r.enviado), (4416.0, "encontrado", True))
        self.assertEqual([o.preco for o in r.opcoes], [4416.0, 4900.0])
        self.assertEqual(self.historico.menor_preco(chave_rota(cfg.voo)), 4416.0)
        self.assertEqual(len(self.enviadas), 1); self.assertIn("R$ 4.416,00", self.enviadas[0])

    def test_preco_menor_que_o_historico_avisa_com_economia(self):
        cfg = configuracao()
        self.historico.registrar(chave_rota(cfg.voo), {}, 5000.0)
        r = self.rodar(cfg, [Falso("G", [opcao(4500)])])
        self.assertEqual((r.decisao.motivo, r.decisao.economia), ("novo_menor", 500.0))
        self.assertEqual(self.historico.menor_preco(chave_rota(cfg.voo)), 4500.0)

    def test_preco_igual_nao_notifica_mas_registra_a_verificacao(self):
        cfg = configuracao()
        self.historico.registrar(chave_rota(cfg.voo), {}, 4416.0)
        r = self.rodar(cfg, [Falso("G", [opcao(4416)])])
        self.assertFalse(r.enviado); self.assertEqual(self.enviadas, [])
        self.assertEqual(len(self.historico.verificacoes(chave_rota(cfg.voo))), 2)

    def test_sem_voos_e_notificar_sempre(self):
        r = self.rodar(configuracao(sempre=True), [Falso("G", [])])
        self.assertEqual((r.menor_preco, r.enviado), (None, True)); self.assertIn("Nenhum voo", self.enviadas[0])

    def test_telegram_desativado_nao_envia(self):
        r = self.rodar(configuracao(ativo=False), [Falso("G", [opcao()])])
        self.assertFalse(r.enviado); self.assertEqual(self.enviadas, [])

    def test_meta_de_preco(self):
        cfg = configuracao(voo(preco_alvo=4500))
        self.historico.registrar(chave_rota(cfg.voo), {}, 4416.0)
        self.assertEqual(self.rodar(cfg, [Falso("G", [opcao(4416)])]).decisao.motivo, "meta")

    def test_falha_de_um_provedor_nao_derruba_os_outros(self):
        r = self.rodar(configuracao(), [Falso("Google", erro="Google Flights: timeout"), Falso("Kayak", [opcao(4800, provedor="Kayak / OTAs")])])
        self.assertEqual(r.menor_preco, 4800.0)
        self.assertEqual(len(r.falhas), 1); self.assertIn("timeout", r.falhas[0])
        self.assertTrue(any("falha" in s.lower() for s in self.saida))

    def test_provedor_que_nao_suporta_a_moeda_e_ignorado_sem_ser_chamado(self):
        k = Falso("Kayak", [opcao()], aceita=False)
        r = self.rodar(configuracao(voo(moeda="USD")), [Falso("Google", [opcao(900)]), k])
        self.assertEqual(k.chamadas, 0); self.assertEqual(len(r.ignorados), 1)

    def test_provedor_desligado_na_configuracao_nao_e_chamado(self):
        cfg = Configuracao(voo(), Provedores(True, False, 3000), Telegram(False, None, None, False, True, True))
        g, k = Falso("Google Flights", [opcao()]), Falso("Kayak / OTAs", [opcao(1)])
        executar_monitor(cfg, [g, k], self.historico, self.enviar, AGORA, self.saida.append)
        self.assertEqual((g.chamadas, k.chamadas), (1, 0))

    def test_historico_e_separado_por_rota_e_datas(self):
        a = configuracao(); b = configuracao(voo(destino="MIA"))
        self.rodar(a, [Falso("G", [opcao(4000)])])
        r = self.rodar(b, [Falso("G", [opcao(9000)])])
        self.assertEqual(r.decisao.motivo, "encontrado")

    def test_falha_no_envio_e_reportada_sem_quebrar(self):
        r = executar_monitor(configuracao(), [Falso("G", [opcao()])], self.historico, lambda t: False, AGORA, self.saida.append)
        self.assertFalse(r.enviado); self.assertTrue(r.opcoes)

    def test_saida_do_console_nao_usa_icones(self):
        self.rodar(configuracao(), [Falso("G", [opcao()])])
        self.assertTrue(all(ord(c) < 0x250 for linha in self.saida for c in linha))


if __name__ == "__main__":
    unittest.main()
