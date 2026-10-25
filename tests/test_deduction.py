"""Correção das lacunas, equivalências alternativas e interação da mesa."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import unittest
from itertools import product

import pygame

from game.deduction import SHEETS, rule_applies, validate_sheet
from game.puzzles import PUZZLES
from game.scenes import Game


class DeductionTests(unittest.TestCase):
    def check(self, index, choices):
        return validate_sheet(index, PUZZLES[index], choices)[0]

    def test_incomplete_and_invalid_fields(self):
        for index, sheet in enumerate(SHEETS):
            self.assertFalse(self.check(index, [None] * len(sheet["fields"])))
            self.assertFalse(self.check(index, [99] * len(sheet["fields"])))
            self.assertFalse(self.check(index, []))

    def test_all_truth_table_combinations(self):
        accepted = [values for values in product(range(2), repeat=4) if self.check(2, values)]
        self.assertEqual(accepted, [(0, 1, 0, 0)])

    def test_equivalent_alternatives(self):
        self.assertTrue(self.check(4, [1, 1, 3]))  # ¬P ∨ ¬Q
        self.assertTrue(self.check(4, [3, 1, 1]))  # ¬Q ∨ ¬P
        self.assertTrue(self.check(4, [0, 2, 3]))  # P → ¬Q
        self.assertFalse(self.check(4, [1, 0, 3]))  # ¬P ∧ ¬Q

    def test_inference_requires_conclusion_and_rule(self):
        self.assertTrue(self.check(5, [2, 0]))
        self.assertFalse(self.check(5, [2, 1]))
        self.assertFalse(self.check(5, [0, 0]))
        self.assertTrue(self.check(6, [1, 1]))
        self.assertFalse(rule_applies([("implies", "P", "Q"), "Q"], "P", "ac"))

    def test_counterexample(self):
        accepted = [values for values in product(range(2), repeat=2) if self.check(7, values)]
        self.assertEqual(accepted, [(1, 0)])

    def test_each_sheet_has_a_solution_and_a_wrong_answer(self):
        for index, sheet in enumerate(SHEETS):
            results = [self.check(index, values) for values in product(*(range(len(choices)) for _, choices in sheet["fields"]))]
            self.assertIn(True, results)
            self.assertIn(False, results)

    def test_keyboard_review_and_source_return(self):
        game = Game()
        try:
            game.scene = "puzzle"
            game.sheet_keyboard(pygame.K_RETURN)
            self.assertFalse(game.correct)
            game.sheet_keyboard(pygame.K_RETURN)
            game.sheet_keyboard(pygame.K_2)
            self.assertEqual(game.sheet_answers, [1])
            self.assertEqual(game.puzzle_index, 0)
            game.sheet_keyboard(pygame.K_RETURN)
            self.assertTrue(game.correct)
            game.sheet_keyboard(pygame.K_RETURN)
            self.assertEqual(game.puzzle_index, 1)
            self.assertEqual(game.sheet_answers, [None, None])
            game.choose_sheet_token(0)
            before = game.sheet_answers.copy()
            game.inventory.collect("wifi")
            game.open_sheet_source("wifi")
            game.draw()
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
            self.assertEqual(game.scene, "puzzle")
            self.assertEqual(game.sheet_answers, before)
            self.assertFalse(game.sheet_return)
            game.draw()
        finally:
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
