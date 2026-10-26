"""Regras de pontuação e integração com os fluxos reais da investigação."""
import json
import os
import tempfile
import unittest
from copy import deepcopy
from itertools import product
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from game.abilities import ABILITIES
from game.cases import CASE_IDS, build_case
from game.deduction import validate_sheet
from game.scenes import Game
from game.puzzles import validate
from game.scoring import Score
from game.savegame import save_progress, load_progress


def solution(game, index, correct=True):
    sheet = game.sheets[index]
    return list(next(values for values in product(*(range(len(choices)) for _, choices in sheet["fields"]))
                     if validate_sheet(index, game.puzzles[index], values)[0] == correct))


def gather(game):
    for name, ability in ABILITIES.items():
        game.abilities.inspected.update(ability["requires"])
        choice = 1 if name == "Bianca" else "20h45" if name == "Jonas" else None
        assert game.abilities.activate(name, ability["room"], True, game.inventory, choice)[0]
    for evidence in game.evidence:
        game.inventory.collect(evidence["id"])


class ScoreTests(unittest.TestCase):
    def test_rules_and_first_attempt_bonus(self):
        score = Score()
        self.assertEqual(score.points, 100)
        self.assertTrue(score.find_evidence("wifi"))
        self.assertFalse(score.find_evidence("wifi"))
        score.answer("sheet:0", True)
        self.assertFalse(score.answer("sheet:0", True))
        self.assertEqual(score.points, 130)
        score.answer("sheet:1", False)
        score.answer("sheet:1", True)
        self.assertEqual(score.points, 120)  # Acertar depois de errar não rende +20.
        self.assertEqual((score.correct, score.errors), (2, 1))
        score.hint("sheet:2")
        self.assertFalse(score.hint("sheet:2"))
        self.assertEqual((score.points, score.hints_used), (115, 1))
        score.accuse([0, 0, 0, 0], False)
        score.accuse([0, 0, 0, 0], False)
        self.assertEqual(score.points, 75)
        score.accuse([0, 0, 2, 3], True)
        score.accuse([0, 0, 2, 3], True)
        self.assertEqual(score.points, 125)
        self.assertEqual((score.correct, score.errors), (3, 3))

    def test_negative_score_is_not_a_progress_reset(self):
        score = Score()
        for _ in range(11):
            score.answer("sheet:0", False)
        self.assertEqual(score.points, -10)
        self.assertEqual(score.outcome, None)


class ScoreGameTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    def tearDown(self):
        pygame.quit()

    def test_collect_interaction_and_automatic_ability(self):
        game = self.game
        item = next(item for item in game.evidence if item["id"] == "wifi")
        game.player.rect.center = item["pos"]
        game.interact()
        game.interact()
        self.assertEqual(game.score.points, 110)
        game.abilities.inspected.add("cameras")
        game.abilities.activate("Flávio", 0, True, game.inventory)
        self.assertEqual(game.score.points, 120)
        game.inventory.collect("cameras")
        self.assertEqual(game.score.points, 120)

    def test_hint_wrong_retry_and_no_duplicate_checks(self):
        game = self.game
        game.request_hint()
        game.request_hint()
        self.assertEqual((game.score.points, game.score.hints_used), (95, 1))
        game.check_sheet()  # Campo vazio não é uma resposta incorreta.
        self.assertEqual(game.score.errors, 0)
        game.sheet_answers = solution(game, 0, False)
        game.check_sheet()
        game.check_sheet()  # Mesmo resultado continua aberto.
        self.assertEqual((game.score.points, game.score.errors), (85, 1))
        game.next_puzzle()
        self.assertEqual(game.puzzle_index, 0)
        game.sheet_answers = solution(game, 0)
        game.check_sheet()
        self.assertEqual(game.score.points, 85)
        game.next_puzzle()
        self.assertEqual(game.puzzle_index, 1)
        game.sheet_answers = solution(game, 1)
        game.check_sheet()
        self.assertEqual(game.score.points, 105)

    def test_all_four_stories_scores_and_end_screens(self):
        game = self.game
        for case_id in CASE_IDS:
            with self.subTest(case=case_id):
                game.reset(case_id)
                gather(game)
                self.assertEqual(game.score.points, 180)
                game.begin_analysis()
                for index in range(8):
                    game.sheet_answers = solution(game, index)
                    game.check_sheet()
                    game.next_puzzle()
                self.assertEqual(game.score.points, 340)
                before = game.inventory.ids.copy()
                game.accusation = [0, 0, 0, 0]
                game.submit()
                game.draw()
                self.assertEqual((game.scene, game.score.points), ("error", 320))
                self.assertEqual(game.inventory.ids, before)
                self.assertEqual(game.puzzle_index, 8)
                game.retry_conclusion()
                game.accusation = list(game.case["answer"])
                game.submit()
                game.draw()
                game.submit()
                self.assertEqual((game.scene, game.score.points), ("victory", 370))
                self.assertEqual((game.score.correct, game.score.errors), (9, 1))
                game.start_demo()
                self.assertEqual((game.case_id, game.score.points), ("link", 100))
                self.assertFalse(game.inventory.ids)

    def test_ability_ui_penalties_hints_and_jonas_completion(self):
        game = self.game
        person = next(p for p in game.characters if p["name"] == "Jonas")
        game.player.rect.center = person["pos"]
        game.active_person = "Jonas"
        game.talked.add("Jonas")
        game.abilities.inspected.add("laptop")
        game.request_ability_hint()
        game.request_ability_hint()
        game.use_ability(0)
        self.assertFalse(game.ability_success)
        self.assertEqual(game.score.points, 85)
        game.use_ability(1)
        self.assertTrue(game.ability_success)
        self.assertIn("Jonas", game.abilities.used)
        self.assertEqual(game.score.points, 85)
        game.use_ability(1)
        self.assertEqual(game.score.points, 85)

    def test_all_ability_buttons_complete_in_every_story(self):
        game = self.game
        for case_id in CASE_IDS:
            game.reset(case_id)
            for person in game.characters:
                with self.subTest(case=case_id, person=person["name"]):
                    name = person["name"]
                    game.player.rect.center = person["pos"]
                    game.active_person = name
                    game.talked.add(name)
                    game.abilities.inspected.update(ABILITIES[name]["requires"])
                    puzzle = game.ability_puzzle(name)
                    choice = next(i for i in range(len(puzzle["options"])) if validate(puzzle, i)[0])
                    game.use_ability(choice)
                    self.assertTrue(game.ability_success, game.ability_feedback)
                    game.scene = "ability"
                    game.draw()
                    points = game.score.points
                    game.use_ability(choice)
                    self.assertEqual(game.score.points, points)
            self.assertEqual(game.score.correct, 7)
            for item in game.evidence:
                game.inventory.collect(item["id"])
            self.assertEqual(game.score.points, 320)

    def test_final_error_charges_once_per_intentional_retry(self):
        game = self.game
        game.analysis_done = True
        game.puzzle_index = 8
        game.submit()
        game.submit()
        self.assertEqual((game.score.points, game.score.errors), (80, 1))
        game.retry_conclusion()
        game.submit()
        self.assertEqual((game.score.points, game.score.errors), (60, 2))

    def test_save_stats_and_prevent_rewards_after_load(self):
        game = self.game
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            for case_id in CASE_IDS:
                with self.subTest(case=case_id):
                    game.reset(case_id)
                    gather(game)
                    game.begin_analysis()
                    game.request_hint()
                    game.sheet_answers = solution(game, 0, False)
                    game.check_sheet()
                    game.next_puzzle()
                    game.sheet_answers = solution(game, 0)
                    game.check_sheet()  # Salvar antes de clicar em Continuar.
                    expected = game.score.export()
                    points = game.score.points
                    save_progress(game, path)
                    game.reset()
                    load_progress(game, path)
                    self.assertEqual(game.score.export(), expected)
                    self.assertEqual(game.score.points, points)
                    game.inventory.collect("wifi")
                    game.request_hint()
                    game.sheet_answers = solution(game, 0)
                    game.check_sheet()
                    self.assertEqual(game.score.points, points)

    def test_save_terminal_result_and_migration(self):
        game = self.game
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            gather(game)
            game.begin_analysis()
            for index in range(8):
                game.sheet_answers = solution(game, index)
                game.check_sheet()
                game.next_puzzle()
            for correct in (False, True):
                game.accusation = list(game.case["answer"]) if correct else [0, 0, 0, 0]
                game.submit()
                expected = game.score.export()
                save_progress(game, path)
                game.reset()
                load_progress(game, path)
                self.assertEqual(game.score.export(), expected)
                self.assertEqual(game.scene, "victory" if correct else "error")
            data = json.loads(path.read_text())
            del data["scoring"]
            path.write_text(json.dumps(data))
            load_progress(game, path)
            self.assertEqual(game.score.points, 100)
            self.assertFalse(game.score.find_evidence("wifi"))
            self.assertFalse(game.score.answer("sheet:0", True))
            save_progress(game, path)
            load_progress(game, path)
            self.assertEqual(game.score.points, 100)

    def test_corrupt_statistics_preserve_game(self):
        game = self.game
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            game.inventory.collect("wifi")
            save_progress(game, path)
            original = json.loads(path.read_text())
            invalid = [None, {}, {"baseline": {}, "events": [], "outcome": None}]
            duplicate = deepcopy(original["scoring"])
            duplicate["events"] *= 2
            invalid.append(duplicate)
            wrong_total = deepcopy(original["scoring"])
            wrong_total["summary"]["points"] = 9999
            invalid.append(wrong_total)
            for value in invalid:
                data = deepcopy(original)
                data["scoring"] = value
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    load_progress(game, path)
                self.assertEqual(game.score.points, 110)
                self.assertEqual(game.inventory.ids, {"wifi"})
