import unittest
from monitor_voos.alertas import decidir


def d(menor, anterior, alvo=None, sempre=False, encontrar=True, baratear=True):
    return decidir(menor, anterior, alvo, sempre, encontrar, baratear)


class AlertasTests(unittest.TestCase):
    def test_primeira_vez_que_encontra(self):
        r = d(4000, None)
        self.assertEqual((r.notificar, r.motivo), (True, "encontrado"))

    def test_novo_menor_preco_com_economia(self):
        r = d(3800, 4000)
        self.assertEqual((r.notificar, r.motivo, r.economia), (True, "novo_menor", 200))
        self.assertAlmostEqual(r.percentual, 5.0)

    def test_preco_igual_ou_maior_nao_notifica(self):
        for atual in (4000, 4500):
            r = d(atual, 4000)
            self.assertEqual((r.notificar, r.motivo), (False, None))

    def test_meta_atingida_quando_nao_ha_outro_motivo(self):
        r = d(4000, 4000, alvo=4500)
        self.assertEqual((r.notificar, r.motivo), (True, "meta"))

    def test_novo_menor_tem_prioridade_sobre_a_meta(self):
        self.assertEqual(d(3000, 4000, alvo=4500).motivo, "novo_menor")

    def test_acima_da_meta_nao_notifica(self):
        self.assertFalse(d(5000, 4000, alvo=4500).notificar)

    def test_notificar_sempre_cobre_os_demais_casos(self):
        r = d(5000, 4000, sempre=True)
        self.assertEqual((r.notificar, r.motivo), (True, "sempre"))

    def test_sem_voos_so_notifica_se_for_sempre(self):
        self.assertEqual((d(None, None).notificar, d(None, 4000).notificar), (False, False))
        r = d(None, 4000, sempre=True)
        self.assertEqual((r.notificar, r.motivo), (True, "sempre"))

    def test_chaves_desligam_cada_tipo_de_aviso(self):
        self.assertFalse(d(4000, None, encontrar=False).notificar)
        self.assertFalse(d(3800, 4000, baratear=False).notificar)

    def test_nao_existe_mais_limite_magico_de_10000(self):
        r = d(5000, 12000)
        self.assertEqual(r.motivo, "novo_menor")


if __name__ == "__main__":
    unittest.main()
