import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import json
import tempfile
import unittest
from pathlib import Path
import pygame
from game.scenes import Game
from game.savegame import save_progress, load_progress
from game.notes import NOTE_LIMIT, text_rows


class NotesTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.game.board_selected = "person:0"
        self.game.open_notes()

    def tearDown(self):
        pygame.quit()

    def key(self, key, mod=0):
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, mod=mod))

    def text(self, text):
        self.game.handle_event(pygame.event.Event(pygame.TEXTINPUT, text=text))

    def test_unicode_editing_and_shortcuts_do_not_control_game(self):
        self.text("Antônio: dúvida?")
        self.key(pygame.K_RETURN)
        self.text("Rever o horário.")
        self.assertEqual(self.game.current_note()["text"], "Antônio: dúvida?\nRever o horário.")
        self.key(pygame.K_BACKSPACE)
        self.key(pygame.K_LEFT)
        self.text("!")
        self.assertIn("horári!o", self.game.current_note()["text"])
        self.key(pygame.K_j)
        self.assertEqual(self.game.scene, "notes")
        self.key(pygame.K_a, pygame.KMOD_CTRL)
        self.text("Nova dúvida")
        self.assertEqual(self.game.current_note()["text"], "Nova dúvida")
        self.key(pygame.K_ESCAPE)
        self.assertEqual(self.game.scene, "board")
        self.assertEqual(self.game.board.notes["person:0"]["text"], "Nova dúvida")

    def test_notes_are_not_evidence_and_survive_removing_card(self):
        game = self.game
        original_answer = list(game.case["answer"])
        self.text("Talvez esteja envolvido.")
        game.write_note(mark="discarded")
        game.board.remove("person:0")
        game.board.arrange()
        self.assertEqual(game.board.notes["person:0"]["mark"], "discarded")
        self.assertEqual(game.inventory.ids, set())
        self.assertFalse(game.analysis_done)
        self.assertEqual(game.puzzle_index, 0)
        self.assertEqual(game.case["answer"], original_answer)
        game.board.pin("person:0")
        game.set_scene("board")
        game.draw()
        game.open_notes()
        game.draw()
        game.write_note(text="", mark="none")
        self.assertNotIn("person:0", game.board.notes)

    def test_save_reload_legacy_and_invalid_notes_are_atomic(self):
        game = self.game
        self.text("Conferir câmeras às 20h35.")
        game.write_note(mark="investigate")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            save_progress(game, path)
            data = json.loads(path.read_text(encoding="utf-8"))
            game.reset()
            load_progress(game, path)
            self.assertEqual(game.board.notes, data["board"]["notes"])
            saved = dict(game.board.notes)
            for bad in [[], {"person:0": {"text": "x" * (NOTE_LIMIT + 1), "mark": "none"}},
                        {"person:0": {"text": "x", "mark": "guilty"}},
                        {"evidence:browser": {"text": "hidden", "mark": "none"}}]:
                data["board"]["notes"] = bad
                path.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_progress(game, path)
                self.assertEqual(game.board.notes, saved)
            del data["board"]["notes"]
            path.write_text(json.dumps(data), encoding="utf-8")
            load_progress(game, path)
            self.assertEqual(game.board.notes, {})

    def test_limits_wrapping_and_scroll(self):
        game = self.game
        self.text("a" * (NOTE_LIMIT + 50))
        self.assertEqual(len(game.current_note()["text"]), NOTE_LIMIT)
        rows = text_rows(game.current_note()["text"], game.font, 100)
        self.assertTrue(all(game.font.size(game.current_note()["text"][a:b])[0] <= 100 for a, b in rows))
        self.key(pygame.K_a, pygame.KMOD_CTRL)
        self.text("Dúvida\n" * 80)
        self.assertGreater(game.note_scroll, 0)
        game.draw()
        self.key(pygame.K_HOME, pygame.KMOD_CTRL)
        self.assertEqual(game.note_cursor, 0)
        self.assertEqual(game.note_scroll, 0)
        game.draw()
