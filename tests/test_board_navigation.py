import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pygame
from game.board import ALL_KEYS, BoardState, CARD_SIZE, CANVAS, BOARD_SPACE
from game.scenes import Game
from game.savegame import save_progress, load_progress


class BoardNavigationTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.game.scene = "board"

    def tearDown(self):
        pygame.quit()

    def test_every_card_fits_without_overlap_after_pin_and_arrange(self):
        board = self.game.board
        for key in sorted(ALL_KEYS):
            board.pin(key)
        for arrange in (False, True):
            if arrange:
                board.arrange()
            rects = [pygame.Rect(pos, CARD_SIZE) for pos in board.positions.values()]
            for i, rect in enumerate(rects):
                self.assertTrue(pygame.Rect(BOARD_SPACE).contains(rect))
                self.assertFalse(any(rect.colliderect(other) for other in rects[i + 1:]))
        self.game.fit_board()
        for key in self.game.visible_board_keys():
            self.assertTrue(pygame.Rect(CANVAS).contains(self.game.board_card_rect(key)))

    def test_zoom_anchor_drag_and_inverse_transform(self):
        game = self.game
        anchor = (500, 350)
        before = game.screen_to_board(anchor)
        game.zoom_board(1.5, anchor)
        self.assertLess(game.screen_to_board(anchor).distance_to(before), 0.001)
        point = (640, 300)
        self.assertLess(game.screen_to_board(game.board_to_screen(point)).distance_to(point), 0.001)
        key = "person:1"
        start = game.board_card_rect(key).center
        old = pygame.Vector2(game.board.positions[key])
        game.board_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=start, button=1))
        self.assertEqual(game.drag_key, key)
        game.board_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(start[0] + 60, start[1] + 30)))
        self.assertEqual(game.board.positions[key], list(old + (40, 20)))
        game.board_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1))
        self.assertIsNone(game.drag_key)
        for _ in range(30):
            game.zoom_board(2)
        self.assertEqual(game.board.zoom, 1.75)
        game.zoom_board(0.001)
        self.assertEqual(game.board.zoom, 0.35)

    def test_pan_filter_and_locate_preserve_data(self):
        game = self.game
        game.board.pin("item:usb")
        game.board.connect("person:1", "item:usb")
        original = copy.deepcopy(game.board.positions)
        game.board_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=2, pos=(500, 400)))
        game.board_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(550, 430)))
        game.board_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=2))
        self.assertEqual(game.board.pan, [50, 30])
        self.assertFalse(game.board_panning)
        game.board.filter = "item"
        self.assertEqual(game.visible_board_keys(), ["item:usb"])
        self.assertEqual(game.visible_board_links(), [])
        game.board.filter = "linked"
        self.assertEqual(set(game.visible_board_keys()), {"person:1", "item:usb"})
        game.board_selected = "person:6"
        game.locate_board_selection()
        self.assertEqual(game.board.filter, "all")
        self.assertLess(pygame.Vector2(game.board_card_rect("person:6").center).distance_to(pygame.Rect(CANVAS).center), 2)
        self.assertEqual(game.board.positions, original)
        self.assertEqual(game.inventory.ids, set())

    def test_wheel_is_scoped_and_label_click_works_after_zoom(self):
        game = self.game
        with patch("pygame.mouse.get_pos", return_value=(500, 400)):
            game.board_event(pygame.event.Event(pygame.MOUSEWHEEL, y=1))
        self.assertAlmostEqual(game.board.zoom, 1.15)
        with patch("pygame.mouse.get_pos", return_value=(100, 400)):
            game.board_event(pygame.event.Event(pygame.MOUSEWHEEL, y=1))
        self.assertAlmostEqual(game.board.zoom, 1.15)
        game.board.connect("person:0", "person:1")
        game.fit_board()
        game.draw()
        label = game.link_labels()[0]
        game.board_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=label[3].center))
        self.assertEqual(game.scene, "relation")

    def test_view_and_large_positions_survive_save(self):
        game = self.game
        game.board.pin("room:2")
        game.board.move("room:2", (1100, 1200))
        game.board.zoom, game.board.pan, game.board.filter = 0.5, [-100, -200], "room"
        before = game.board.export()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            save_progress(game, path)
            game.reset()
            load_progress(game, path)
        self.assertEqual(game.board.export(), before)
        old = copy.deepcopy(before)
        del old["view"]
        self.assertEqual(BoardState.restore(old, set()).zoom, 1)
        for value in [float("nan"), float("inf"), -1, True, 100]:
            bad = copy.deepcopy(before)
            bad["view"]["zoom"] = value
            with self.assertRaises(ValueError):
                BoardState.restore(bad, set())

    def test_empty_filter_and_all_cards_render(self):
        game = self.game
        game.board.filter = "evidence"
        game.fit_board()
        game.draw()
        for key in ALL_KEYS:
            game.board.pin(key)
        game.board.filter = "all"
        game.arrange_board()
        game.draw()
