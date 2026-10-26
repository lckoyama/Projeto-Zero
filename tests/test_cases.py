"""Cada variante deve ser solucionável e persistir sem contaminar outra partida."""
import json
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame
from game.cases import CASE_IDS, build_case, choose_case
from game.scenes import Game
from game.savegame import save_progress, load_progress
from game.hypotheses import available_topics, assess_review, empty_review
import test_game


class CaseTests(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def test_each_case_complete_playthrough(self):
        for case_id in CASE_IDS:
            with self.subTest(case=case_id), patch("game.scenes.choose_case", return_value=case_id):
                run = test_game.GameTests("test_progression_and_scenes")
                run.setUp()
                try:
                    run.test_progression_and_scenes()
                    self.assertEqual(run.game.case_id, case_id)
                finally:
                    run.tearDown()

    def test_random_choice_and_start(self):
        with patch("game.cases.random.choice", return_value="extension") as choice:
            self.assertEqual(choose_case(), "extension")
            choice.assert_called_once_with(CASE_IDS)
        game = Game()
        with patch("game.scenes.choose_case", side_effect=CASE_IDS):
            for case_id in CASE_IDS:
                game.start()
                self.assertEqual(game.case_id, case_id)
                self.assertFalse(game.inventory.ids)

    def test_save_preserves_case_and_old_save_uses_original(self):
        game = Game()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            for case_id in CASE_IDS:
                game.reset(case_id)
                game.has_game = True
                save_progress(game, path)
                game.reset()
                with patch("game.scenes.choose_case", side_effect=AssertionError("No reroll")):
                    load_progress(game, path)
                self.assertEqual(game.case, build_case(case_id))
            data = json.loads(path.read_text(encoding="utf-8"))
            data["case_id"] = "unknown"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_progress(game, path)
            self.assertEqual(game.case_id, "phishing")
            del data["case_id"]
            path.write_text(json.dumps(data), encoding="utf-8")
            load_progress(game, path)
            self.assertEqual(game.case_id, "link")

    def test_case_sources_and_unique_solutions(self):
        answers = set()
        for case_id in CASE_IDS:
            case = build_case(case_id)
            answers.add(tuple(case["answer"]))
            topic = case["topics"]["credentials"]
            pair = tuple(sorted(topic["keys"])[:2])
            sources = topic["requires"]
            self.assertIn("credentials", available_topics(pair, sources, case["topics"]))
            self.assertNotIn("credentials", available_topics(pair, set(), case["topics"]))
            review = empty_review("credentials")
            review.update(relation="support", evidence="credentials", premises=[0, 1],
                          conclusion=2, rule="mp", submitted=True)
            self.assertEqual(assess_review(pair, review, sources, set(), case["topics"])[0], "verified")
            self.assertEqual(set(case["sheets"][5]["sources"]), sources)
        self.assertEqual(len(answers), len(CASE_IDS))
        changed = build_case("usb")
        changed["evidence"][0]["text"] = "changed"
        self.assertNotEqual(build_case("usb")["evidence"][0]["text"], "changed")

    def test_other_case_answers_do_not_win(self):
        game = Game()
        for case_id in CASE_IDS:
            game.reset(case_id)
            game.analysis_done = True
            game.puzzle_index = len(game.puzzles)
            for other in CASE_IDS:
                game.accusation = build_case(other)["answer"]
                game.submit()
                self.assertEqual(game.scene, "victory" if other == case_id else "error")

    def test_old_saved_stories_keep_their_revision(self):
        game = Game()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            for case_id in CASE_IDS:
                game.reset(case_id, revision=1)
                original = game.case
                save_progress(game, path)
                data = json.loads(path.read_text(encoding="utf-8"))
                del data["case_revision"]
                path.write_text(json.dumps(data), encoding="utf-8")
                game.reset(case_id)
                load_progress(game, path)
                self.assertEqual(game.case, original)
                save_progress(game, path)
                self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["case_revision"], 1)
            data["case_revision"] = 999
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_progress(game, path)
            self.assertEqual(game.case, original)

    def test_transmitter_is_supported_and_not_excluded(self):
        game = Game()
        game.reset("phishing")
        topic = game.topics["transmitter_analysis"]
        review = empty_review("transmitter_analysis")
        review.update(relation="support", evidence="transmitter", premises=[0, 1],
                      conclusion=2, rule="mp", submitted=True)
        pair = ("person:6", "item:transmitter")
        self.assertEqual(assess_review(pair, review, {"transmitter"}, set(), game.topics)[0], "verified")
        review.update(premises=[1, 4], conclusion=3, rule="mt")
        self.assertEqual(assess_review(pair, review, {"transmitter"}, set(), game.topics)[0], "rejected")
        self.assertEqual(game.sheets[6]["sources"], ["laptop"])
        self.assertIn("notebook", game.ability_puzzle("Carlos")["context"])
        game.abilities.inspected.add("transmitter")
        ok, result = game.abilities.activate("Carlos", 4, True, game.inventory)
        self.assertTrue(ok)
        self.assertIn("envio às 20h20", result)
        self.assertNotIn("assinatura não foi encontrada", result)

    def test_case_specific_dialogues_records_and_timeline_render(self):
        game = Game()
        intros = set()
        for case_id in CASE_IDS:
            game.reset(case_id)
            intros.add(game.case["intro"])
            for name, ability in game.abilities.results.items():
                self.assertEqual(ability, game.case["ability_results"][name])
            for item in game.evidence:
                game.inventory.collect(item["id"])
                game.board_selected = "evidence:" + item["id"]
                self.assertIn(item["text"], game.entry(game.board_selected)[2])
            game.abilities.inspected.add("computer")
            game.scene = "timeline"
            game.draw()
        self.assertEqual(len(intros), 1)
        failure = build_case("extension")
        self.assertTrue(failure["puzzles"][1]["values"]["F"])
        self.assertIn("sem autenticação", failure["ability_results"]["Márcia"])
