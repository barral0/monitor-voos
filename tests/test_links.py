import unittest
from datetime import date
from monitor_voos.links import gerar_links

IDA, VOLTA = date(2027, 5, 1), date(2027, 5, 31)


class LinksTests(unittest.TestCase):
    def test_um_link_por_buscador_com_os_nomes_originais(self):
        self.assertEqual(list(gerar_links("CNF", "LAX", IDA, VOLTA, 1)), ["Google Flights", "Skyscanner", "Kiwi.com", "Kayak"])

    def test_urls_com_uma_escala_mantem_o_formato_original(self):
        l = gerar_links("CNF", "LAX", IDA, VOLTA, 1)
        self.assertEqual(l["Skyscanner"], "https://www.skyscanner.com.br/transporte/passagens-aereas/cnf/lax/270501/270531/?adultsv2=1&cabinclass=economy&rtn=1&stops=!two_plus_stops")
        self.assertEqual(l["Kiwi.com"], "https://www.kiwi.com/deep?from=CNF&to=LAX&departure=2027-05-01&return=2027-05-31&currency=BRL&lang=pt&max_stopovers=1")
        self.assertEqual(l["Kayak"], "https://www.kayak.com.br/flights/CNF-LAX/2027-05-01/2027-05-31?sort=price_a&fs=stops=~1")

    def test_url_do_google_nao_tem_espacos(self):
        for stops in (0, 1, 2):
            url = gerar_links("CNF", "LAX", IDA, VOLTA, stops)["Google Flights"]
            self.assertNotIn(" ", url)
            self.assertTrue(url.startswith("https://www.google.com/travel/flights?q=Flights%20to%20LAX%20from%20CNF%20on%202027-05-01%20through%202027-05-31"))

    def test_filtro_de_escalas_do_google_acompanha_o_limite(self):
        self.assertTrue(gerar_links("CNF", "LAX", IDA, VOLTA, 0)["Google Flights"].endswith("%20nonstop"))
        self.assertTrue(gerar_links("CNF", "LAX", IDA, VOLTA, 1)["Google Flights"].endswith("%20with%20at%20most%201%20stop"))
        self.assertTrue(gerar_links("CNF", "LAX", IDA, VOLTA, 2)["Google Flights"].endswith("%20with%20at%20most%202%20stops"))

    def test_skyscanner_so_filtra_quando_o_site_suporta(self):
        self.assertIn("stops=direct", gerar_links("CNF", "LAX", IDA, VOLTA, 0)["Skyscanner"])
        self.assertNotIn("stops=", gerar_links("CNF", "LAX", IDA, VOLTA, 2)["Skyscanner"])

    def test_moeda_do_kiwi_nao_e_fixa(self):
        self.assertIn("currency=USD", gerar_links("CNF", "LAX", IDA, VOLTA, 1, moeda="USD")["Kiwi.com"])


if __name__ == "__main__":
    unittest.main()
