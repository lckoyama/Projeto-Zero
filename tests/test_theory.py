import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import json
import tempfile
import unittest
from pathlib import Path
import pygame
from game.cases import build_case, CASE_IDS
from game.theory import empty_theory, required_sources, assess_theory
from game.scenes import Game
from game.savegame import save_progress, load_progress
from game.abilities import ABILITIES


class TheoryTests(unittest.TestCase):
    def test_all_cases_need_correct_choices_and_relevant_available_sources(self):
        for revision in (1, 2):
            for case_id in CASE_IDS:
                case = build_case(case_id, revision)
                known = {e["id"] for e in case["evidence"]}
                theory = {"choices": list(case["answer"]),
                    "sources": [sorted(row) for row in required_sources(case)], "submitted": True}
                self.assertTrue(all(s == "supported" for s, _ in assess_theory(case, theory, known, {"computer"})))
                self.assertFalse(any(s == "supported" for s, _ in assess_theory(case, theory, set(), set())))
                for field in range(4):
                    original = theory["sources"][field]
                    theory["sources"][field] = ["access"]
                    self.assertEqual(assess_theory(case, theory, known, {"computer"})[field][0], "unsupported")
                    theory["sources"][field] = original
                    choice = theory["choices"][field]
                    theory["choices"][field] = (choice + 1) % 5
                    self.assertEqual(assess_theory(case, theory, known, {"computer"})[field][0], "unsupported")
                    theory["choices"][field] = choice
                theory["submitted"] = False
                self.assertTrue(all(s == "pending" for s, _ in assess_theory(case, theory, known, {"computer"})))

    def setUp(self):
        self.game = Game()

    def tearDown(self):
        pygame.quit()

    def populate(self):
        game = self.game
        for name, ability in ABILITIES.items():
            game.abilities.inspected.update(ability["requires"])
            choice = 1 if name == "Bianca" else "20h45" if name == "Jonas" else None
            game.abilities.activate(name, ability["room"], True, game.inventory, choice)
        game.inventory.ids.update(e["id"] for e in game.evidence)
        game.theory = {"choices": list(game.case["answer"]),
            "sources": [sorted(row) for row in required_sources(game.case)], "submitted": True}

    def test_transfer_requires_verified_sources_and_completed_challenges(self):
        game = self.game
        game.reset("usb")
        self.populate()
        game.open_theory()
        game.use_theory()
        self.assertEqual(game.scene, "theory")
        game.analysis_done = True
        game.puzzle_index = len(game.puzzles)
        game.use_theory()
        self.assertEqual(game.scene, "conclusion")
        self.assertEqual(game.accusation, game.case["answer"])
        game.open_theory()
        game.cycle_theory_choice(1)
        self.assertFalse(game.theory["submitted"])
        game.use_theory()
        self.assertEqual(game.scene, "theory")

    def test_save_load_legacy_and_invalid_draft(self):
        game = self.game
        game.reset("extension")
        self.populate()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "progress.json"
            save_progress(game, path)
            before = json.loads(path.read_text(encoding="utf-8"))
            game.reset()
            load_progress(game, path)
            self.assertEqual(game.theory, before["theory"])
            self.assertTrue(all(s == "supported" for s, _ in game.theory_results()))
            for bad in [[], {"choices": [999] * 4, "sources": [[]] * 4, "submitted": True},
                        {"choices": [None] * 4, "sources": [["unknown"]] * 4, "submitted": False}]:
                data = dict(before, theory=bad)
                path.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_progress(game, path)
                self.assertEqual(game.theory, before["theory"])
            del before["theory"]
            path.write_text(json.dumps(before), encoding="utf-8")
            load_progress(game, path)
            self.assertEqual(game.theory, empty_theory())

    def test_ui_render_edits_and_return(self):
        game = self.game
        game.open_theory()
        game.draw()
        game.toggle_theory_source("credentials")
        self.assertEqual(game.theory["sources"][0], [])
        for case_id in CASE_IDS:
            game.reset(case_id)
            self.populate()
            game.open_theory()
            for field in range(4):
                game.theory_field = field
                for source in game.comparison_sources():
                    game.theory_reading = source
                    game.draw()
            game.toggle_theory_source("access")
            self.assertFalse(game.theory["submitted"])
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertEqual(game.scene, "board")
        game.draw()
        self.assertTrue(any(action == game.open_theory for _, action in game.buttons))
