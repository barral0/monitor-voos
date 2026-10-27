import json
import re
import unittest
from pathlib import Path

from monitor_voos.cli import construir_parser
from monitor_voos.config import carregar_configuracao

RAIZ = Path(__file__).resolve().parent.parent
SKILL = RAIZ / ".agents" / "skills" / "monitor-voos" / "SKILL.md"


def sem_icones(texto):
    """Letras latinas, pontuacao comum e simbolos ASCII; nenhum emoji ou pictograma."""
    return [c for c in texto if ord(c) > 0x24F and c not in "\u2013\u2014\u2018\u2019\u201c\u201d\u2022\u2026\u00d7"]


class SkillTests(unittest.TestCase):
    def setUp(self):
        self.texto = SKILL.read_text(encoding="utf-8")

    def test_frontmatter_valido(self):
        m = re.match(r"^---\n(.*?)\n---\n", self.texto, re.S)
        self.assertIsNotNone(m, "SKILL.md precisa comecar com frontmatter")
        corpo = m.group(1)
        self.assertRegex(corpo, r"(?m)^name: monitor-voos$")
        desc = re.search(r"(?ms)^description: >-?\n(.*?)(?=^\w+:|\Z)", corpo + "\n")
        self.assertIsNotNone(desc)
        d = " ".join(desc.group(1).split())
        self.assertTrue(80 <= len(d) <= 1024, len(d))
        self.assertIn("Use", d)

    def test_comandos_citados_existem_na_cli(self):
        validos = set(construir_parser()._subparsers._group_actions[0].choices)
        citados = set(re.findall(r"python -m monitor_voos ([a-z-]+)", self.texto))
        self.assertTrue(citados)
        self.assertLessEqual(citados, validos)
        self.assertEqual(citados, validos, "todo subcomando deve estar documentado na skill")

    def test_skill_nao_duplica_codigo(self):
        self.assertEqual(list((RAIZ / ".agents").rglob("*.py")), [])

    def test_regras_de_seguranca_estao_na_skill(self):
        t = self.texto.lower()
        self.assertIn("token", t); self.assertIn("confirm", t)

    def test_sem_icones(self):
        self.assertEqual(sem_icones(self.texto), [])


class RepositorioTests(unittest.TestCase):
    def test_readme_sem_icones_nem_emojis(self):
        self.assertEqual(sem_icones((RAIZ / "README.md").read_text(encoding="utf-8")), [])

    def test_exemplo_de_configuracao_e_valido_e_sem_segredo(self):
        c = carregar_configuracao(RAIZ / "config.example.json", {})
        self.assertIsNone(c.telegram.token); self.assertIsNone(c.telegram.chat_id)
        chaves = json.loads((RAIZ / "config.example.json").read_text(encoding="utf-8-sig"))
        self.assertNotIn("kiwi", chaves["providers"])

    def test_gitignore_protege_credenciais_e_historico(self):
        g = (RAIZ / ".gitignore").read_text(encoding="utf-8-sig")
        for item in ("config.json", ".env", "price_history.json"):
            self.assertIn(item, g)

    def test_atalho_do_windows_usa_a_cli_unica(self):
        self.assertIn("python -m monitor_voos monitorar", (RAIZ / "run_monitor.bat").read_text(encoding="utf-8"))

    def test_dependencias_sem_pacotes_nao_usados(self):
        r = (RAIZ / "requirements.txt").read_text(encoding="utf-8-sig").lower()
        for pacote in ("fast-flights", "requests", "playwright"):
            self.assertIn(pacote, r)
        self.assertNotIn("dotenv", r); self.assertNotIn("typing_extensions", r)

    def test_nao_ha_codigo_duplicado_na_raiz(self):
        for antigo in ("flexible_search.py", "telegram_notifier.py", "monitor.py", "test_telegram.py"):
            self.assertFalse((RAIZ / antigo).exists(), antigo)


if __name__ == "__main__":
    unittest.main()
