"""Persistência em diretórios temporários removidos ao terminar os testes."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import json
import tempfile
import unittest
from pathlib import Path

import pygame

from game.abilities import ABILITIES
from game.evidence import EVIDENCE
from game.savegame import load_progress, save_progress
from game.scenes import Game


class SaveTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "progress.json"

    def tearDown(self):
        self.directory.cleanup()
        pygame.quit()

    def test_all_abilities_survive_reload(self):
        game = self.game
        game.start()
        for name, ability in ABILITIES.items():
            game.abilities.inspected.update(ability["requires"])
            choice = 1 if name == "Bianca" else "20h45" if name == "Jonas" else None
            self.assertTrue(game.abilities.activate(name, ability["room"], True, game.inventory, choice)[0])
        for item in EVIDENCE:
            game.inventory.collect(item["id"])
        game.talked = set(ABILITIES)
        game.analysis_done, game.puzzle_index = True, 3
        records = game.abilities.records.copy()
        save_progress(game, self.path)
        game.reset()
        load_progress(game, self.path)
        self.assertEqual(game.abilities.records, records)
        self.assertEqual(game.abilities.used, set(ABILITIES))
        self.assertEqual(len(game.inventory.ids), 8)
        self.assertEqual(game.puzzle_index, 3)
        self.assertEqual(game.talked, set(ABILITIES))
        self.assertTrue(game.abilities.visible("browser"))
        self.assertFalse(game.abilities.lock_reason("credentials"))
        for name, ability in ABILITIES.items():
            self.assertFalse(game.abilities.activate(name, ability["room"], True, game.inventory)[0])
        self.assertFalse(self.path.with_suffix(".tmp").exists())

    def test_partial_progress_can_continue(self):
        game = self.game
        game.abilities.inspected.add("usb")
        save_progress(game, self.path)
        game.reset()
        load_progress(game, self.path)
        self.assertTrue(game.abilities.activate("Bianca", 3, True, game.inventory, 1)[0])
        self.assertEqual(game.puzzle_index, 0)

    def test_bad_files_preserve_current_game(self):
        game = self.game
        game.talked.add("Flávio")
        with self.assertRaises(FileNotFoundError):
            load_progress(game, self.path)
        for contents in ["{", "[]", '{"version": 999}']:
            self.path.write_text(contents, encoding="utf-8")
            with self.assertRaises(ValueError):
                load_progress(game, self.path)
            self.assertEqual(game.talked, {"Flávio"})
        save_progress(game, self.path)
        data = json.loads(self.path.read_text(encoding="utf-8"))
        for field, value in [("position", [0, 0]), ("puzzle_index", 99),
                             ("evidence", ["credentials"]), ("accusation", [-1, 0, 0, 0])]:
            invalid = dict(data)
            invalid[field] = value
            self.path.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_progress(game, self.path)
            self.assertEqual(game.talked, {"Flávio"})


if __name__ == "__main__":
    unittest.main()
