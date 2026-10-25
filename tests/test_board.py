"""Interações do mural, proteção das pistas e persistência das hipóteses."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import tempfile
import unittest
from pathlib import Path

import pygame

from game.board import BoardState, CANVAS, CARD_SIZE
from game.savegame import load_progress, save_progress
from game.scenes import Game


class BoardTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.game.start()
        self.game.scene = "board"

    def tearDown(self):
        pygame.quit()

    def click(self, position):
        self.game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position))
        self.game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=position))

    def test_drag_is_bounded_and_preserves_evidence(self):
        game = self.game
        x, y = game.board.positions["person:0"]
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(x + 10, y + 10)))
        game.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(-999, 9999)))
        self.assertEqual(game.board.positions["person:0"],
                         [CANVAS[0] + 8, CANVAS[1] + CANVAS[3] - CARD_SIZE[1] - 8])
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(0, 0)))
        self.assertIsNone(game.drag_key)
        self.assertEqual(game.inventory.ids, set())

    def test_link_toggle_and_remove(self):
        game = self.game
        game.toggle_links()
        for key in ("person:0", "person:1"):
            x, y = game.board.positions[key]
            self.click((x + 15, y + 15))
        self.assertEqual(game.board.links, {("person:0", "person:1")})
        self.assertEqual(game.puzzle_index, 0)
        game.submit()
        self.assertNotEqual(game.scene, "victory")
        game.remove_selected()
        self.assertNotIn("person:1", game.board.positions)
        self.assertFalse(game.board.links)
        game.pin_selected()
        self.assertIn("person:1", game.board.positions)

    def test_catalog_does_not_reveal_uncollected_evidence(self):
        game = self.game
        game.choose_catalog("evidence")
        self.assertEqual(game.catalog_keys(), [])
        self.assertFalse(game.entry("item:usb")[3])
        self.assertIn("ainda não disponível", game.entry("item:usb")[2])
        game.inventory.collect("wifi")
        self.assertEqual(game.catalog_keys(), ["evidence:wifi"])
        self.assertTrue(game.entry("evidence:wifi")[3])
        game.choose_catalog("person")
        game.page_catalog(1)
        self.assertEqual(game.catalog_page, 1)
        game.choose_catalog("room")
        self.assertEqual(game.catalog_page, 0)

    def test_board_survives_save_and_old_files(self):
        game = self.game
        game.board.pin("room:2")
        game.board.move("room:2", (600, 400))
        game.board.connect("room:2", "person:3")
        before = game.board.export()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "progress.json"
            save_progress(game, path)
            game.reset()
            load_progress(game, path)
            self.assertEqual(game.board.export(), before)
        self.assertEqual(len(BoardState.restore(None, set()).positions), 7)
        with self.assertRaises(ValueError):
            BoardState.restore({"positions": {"evidence:browser": [250, 180]}, "links": []}, set())

    def test_navigation_and_rendering(self):
        game = self.game
        game.draw()
        self.click((920, 32))
        self.assertEqual(game.scene, "world")
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j))
        self.assertEqual(game.scene, "board")
        for scene in ("menu", "board", "dossier", "timeline", "conclusion"):
            game.scene = scene
            game.draw()
        game.scene = "board"
        game.draw()
        self.click((1060, 425))
        self.assertEqual(game.scene, "dossier")
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertEqual(game.scene, "board")


if __name__ == "__main__":
    unittest.main()
