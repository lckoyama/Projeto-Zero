import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import tempfile
import unittest
from pathlib import Path
import pygame
from game.cases import build_case
from game.hypotheses import assess_review, empty_review
from game.scenes import Game
from game.savegame import save_progress, load_progress


def review(topic, relation, source, premises=(0, 1), conclusion=2):
    value = empty_review(topic)
    value.update(relation=relation, evidence=source, premises=list(premises),
                 conclusion=conclusion, rule="mp", submitted=True)
    return value


class LinkLabelTests(unittest.TestCase):
    def test_used_requires_usage_and_correct_pair(self):
        topics = build_case("link")["topics"]
        value = review("usb_time", "used", "usb")
        self.assertEqual(assess_review(("person:1", "item:usb"), value, {"usb"}, set(), topics)[0], "verified")
        self.assertEqual(assess_review(("person:1", "evidence:usb"), value, {"usb"}, set(), topics)[0], "rejected")
        value = review("transmitter_found", "used", "transmitter")
        self.assertEqual(assess_review(("person:6", "item:transmitter"), value, {"transmitter"}, set(), topics)[0], "rejected")

    def test_contradictions_need_testimony_and_correct_inference(self):
        for case_id, person, source, name in [("usb", 5, "usb", "Jonas"), ("phishing", 6, "transmitter", "Carlos")]:
            topics = build_case(case_id)["topics"]
            pair = (f"person:{person}", f"item:{source}")
            value = review("incident_contradiction", "contradiction", source, (0, 6), 4)
            self.assertEqual(assess_review(pair, value, {source}, {name}, topics)[0], "verified")
            self.assertEqual(assess_review(pair, value, {source}, set(), topics)[0], "rejected")
            value["relation"] = "support"
            self.assertEqual(assess_review(pair, value, {source}, {name}, topics)[0], "rejected")

    def test_label_click_edit_and_save_reload(self):
        game = Game()
        try:
            game.reset("usb")
            game.abilities.inspected.add("usb")
            game.abilities.activate("Bianca", 3, True, game.inventory, 1)
            game.inventory.collect("usb")
            game.talked.add("Jonas")
            game.board.pin("item:usb")
            pair = tuple(sorted(("person:5", "item:usb")))
            game.board.connect(*pair)
            game.board.reviews[pair] = review("incident_contradiction", "contradiction", "usb", (0, 6), 4)
            game.scene = "board"
            game.draw()
            label = game.link_labels()[0]
            self.assertIn("Contradiz", label[1])
            self.assertEqual(label[2], "verified")
            game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=label[3].center))
            self.assertEqual(game.scene, "relation")
            self.assertEqual(game.relation_pair, pair)
            game.draw()
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "save.json"
                save_progress(game, path)
                game.reset()
                load_progress(game, path)
            self.assertEqual(game.relation_status(pair)[0], "verified")
            game.open_relation(*pair)
            game.cycle_relation_field("rule", ["mp", "mt"])
            self.assertEqual(game.link_labels()[0][2], "pending")
            game.verify_relation()
            self.assertEqual(game.link_labels()[0][2], "rejected")
            game.remove_relation()
            self.assertEqual(game.link_labels(), [])
        finally:
            pygame.quit()
