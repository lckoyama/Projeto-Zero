"""Validação das sete habilidades e de suas restrições."""
import unittest

from game.abilities import ABILITIES, AbilitySystem, DIGITAL_PUZZLE
from game.case_data import SOLUTION
from game.inventory import Inventory
from game.puzzles import validate


class AbilityTests(unittest.TestCase):
    def setUp(self):
        self.system = AbilitySystem()
        self.inventory = Inventory()

    def activate(self, name, choice=None):
        return self.system.activate(name, ABILITIES[name]["room"], True, self.inventory, choice)

    def test_unique_abilities(self):
        self.assertEqual(len(ABILITIES), 7)
        self.assertEqual(len({item["name"] for item in ABILITIES.values()}), 7)

    def test_hidden_clue(self):
        self.assertFalse(self.system.visible("browser"))
        self.assertTrue(self.activate("Seu Antônio")[0])
        self.assertTrue(self.system.visible("browser"))
        self.assertNotIn("browser", self.inventory.ids)
        self.assertTrue(self.system.lock_reason("browser"))

    def test_digital_challenge_required(self):
        self.assertFalse(self.activate("Bianca", 1)[0])
        self.system.inspected.add("usb")
        self.assertFalse(self.activate("Bianca", 0)[0])
        self.assertNotIn("Bianca", self.system.used)
        self.assertTrue(self.activate("Bianca", 1)[0])
        for key in ("browser", "usb", "credentials"):
            self.assertFalse(self.system.lock_reason(key))
        self.assertEqual(sum(validate(DIGITAL_PUZZLE, i)[0] for i in range(3)), 1)

    def test_all_context_guards_and_duplicates(self):
        for name, ability in ABILITIES.items():
            with self.subTest(name=name):
                self.assertFalse(self.system.activate(name, -1, True, self.inventory)[0])
                self.assertFalse(self.system.activate(name, ability["room"], False, self.inventory)[0])
                if ability["requires"]:
                    self.assertFalse(self.activate(name)[0])
                self.system.inspected.update(ability["requires"])
                choice = 1 if name == "Bianca" else "20h45" if name == "Jonas" else None
                self.assertTrue(self.activate(name, choice)[0])
                evidence_before = self.inventory.ids.copy()
                records_before = self.system.records.copy()
                self.assertFalse(self.activate(name, choice)[0])
                self.assertEqual(evidence_before, self.inventory.ids)
                self.assertEqual(records_before, self.system.records)
                self.assertNotIn(SOLUTION, self.system.records[name])

    def test_agenda_comparison(self):
        for time, expected in [("20h20", "Compatível"), ("20h45", "Contradição")]:
            self.system = AbilitySystem()
            self.system.inspected.add("laptop")
            success, result = self.activate("Jonas", time)
            self.assertTrue(success)
            self.assertIn(expected, result)
            self.assertIn("não um novo depoimento", result)


if __name__ == "__main__":
    unittest.main()
