"""A comparação respeita fontes, depoimentos e a revisão narrativa salva."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import unittest
import pygame
from game.cases import build_case, CASE_IDS
from game.comparisons import assess_comparison, comparison_rules
from game.scenes import Game


class ComparisonTests(unittest.TestCase):
    def assess(self, case_id, person, line, source, revision=2):
        case = build_case(case_id, revision)
        return assess_comparison(case, person, line, source,
            {case["characters"][person]["name"]}, {source}, {source})

    def test_deception_needs_the_correct_source(self):
        self.assertEqual(self.assess("usb", 5, 1, "usb")[0], "contradicts")
        self.assertEqual(self.assess("usb", 5, 1, "cameras")[0], "inconclusive")
        self.assertEqual(self.assess("phishing", 6, 0, "transmitter")[0], "contradicts")
        self.assertEqual(self.assess("phishing", 6, 0, "cameras")[0], "inconclusive")
        self.assertEqual(self.assess("usb", 1, 0, "usb")[0], "confirms")
        self.assertEqual(self.assess("usb", 5, 1, "wifi")[0], "inconclusive")

    def test_no_intent_inferred_from_configuration_alone(self):
        self.assertEqual(self.assess("extension", 4, 0, "computer")[0], "confirms")
        self.assertEqual(self.assess("extension", 4, 1, "computer")[0], "inconclusive")

    def test_every_rule_requires_heard_statement_and_obtained_source(self):
        for case_id in CASE_IDS:
            for revision in (1, 2):
                case = build_case(case_id, revision)
                for (person, line, source), expected in comparison_rules(case).items():
                    with self.subTest(case=case_id, revision=revision, person=person, source=source):
                        heard = {case["characters"][person]["name"]}
                        self.assertLess(line, len(case["characters"][person]["lines"]))
                        self.assertEqual(assess_comparison(case, person, line, source, set(), {source}, {source})[0], "locked")
                        self.assertEqual(assess_comparison(case, person, line, source, heard, set(), set())[0], "locked")
                        self.assertEqual(assess_comparison(case, person, line, source, heard, {source}, {source}), expected)
        self.assertEqual(self.assess("phishing", 6, 0, "transmitter", revision=1)[0], "confirms")
        self.assertEqual(self.assess("usb", 5, 1, "usb", revision=1)[0], "inconclusive")

    def test_ui_empty_state_selection_and_navigation(self):
        game = Game()
        try:
            game.reset("phishing")
            game.board_selected = "person:6"
            game.open_comparison()
            game.draw()
            self.assertEqual(game.comparison_person, 6)
            self.assertEqual(game.comparison_sources(), [])
            self.assertIsNone(game.comparison_source)
            game.compare_statement()
            self.assertEqual(game.comparison_result[0], "locked")
            game.talked.add("Carlos")
            game.inventory.collect("transmitter")
            game.open_comparison()
            game.compare_statement()
            game.draw()
            self.assertEqual(game.comparison_result[0], "contradicts")
            game.change_comparison("line", 1)
            self.assertIsNone(game.comparison_result)
            game.compare_statement()
            self.assertEqual(game.comparison_result[0], "inconclusive")
            game.change_comparison("person", 1)
            self.assertEqual(game.comparison_person, 0)
            self.assertEqual(game.comparison_line, 0)
            game.abilities.inspected.add("computer")
            self.assertIn("computer", game.comparison_sources())
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
            self.assertEqual(game.scene, "board")
            game.draw()
            self.assertTrue(any(action == game.open_comparison for _, action in game.buttons))
        finally:
            pygame.quit()

    def test_all_comparisons_render_in_each_case(self):
        game = Game()
        try:
            for case_id in CASE_IDS:
                game.reset(case_id)
                game.talked.update(p["name"] for p in game.characters)
                game.inventory.ids.update(item["id"] for item in game.evidence)
                game.abilities.inspected.add("computer")
                game.open_comparison()
                for person, line, source in comparison_rules(game.case):
                    game.comparison_person, game.comparison_line, game.comparison_source = person, line, source
                    game.compare_statement()
                    game.draw()
        finally:
            pygame.quit()
