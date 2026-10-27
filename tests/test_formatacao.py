import unittest
from monitor_voos.formatacao import formatar_duracao, formatar_preco, texto_escalas


class FormatacaoTests(unittest.TestCase):
    def test_preco_no_padrao_brasileiro(self):
        self.assertEqual(formatar_preco(4416, "BRL"), "R$ 4.416,00")
        self.assertEqual(formatar_preco(1234567.5, "BRL"), "R$ 1.234.567,50")
        self.assertEqual(formatar_preco(0.5, "BRL"), "R$ 0,50")

    def test_outras_moedas(self):
        self.assertEqual(formatar_preco(1200, "USD"), "US$ 1.200,00")
        self.assertEqual(formatar_preco(99.9, "EUR"), "\u20ac 99,90")
        self.assertEqual(formatar_preco(10, "CHF"), "CHF 10,00")

    def test_duracao(self):
        self.assertEqual(formatar_duracao(404), "6h44m")
        self.assertEqual(formatar_duracao(65), "1h05m")
        self.assertEqual(formatar_duracao(0), "")
        self.assertEqual(formatar_duracao(None), "")

    def test_texto_de_escalas_acompanha_o_limite_configurado(self):
        self.assertEqual(texto_escalas(0), "somente voos diretos")
        self.assertEqual(texto_escalas(1), "m\u00e1ximo de 1 escala")
        self.assertEqual(texto_escalas(2), "m\u00e1ximo de 2 escalas")


if __name__ == "__main__":
    unittest.main()
