"""Verificação contextual e lógica das ligações, incluindo persistência."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

from game.board import BoardState
from game.hypotheses import TOPICS, available_topics, assess_review, empty_review
from game.savegame import save_progress, load_progress
from game.scenes import Game


def justification(topic="usb_time", relation="time", evidence="usb", premises=None, conclusion=2, rule="mp"):
    review = empty_review(topic)
    review.update(relation=relation, evidence=evidence, premises=premises or [0, 1],
                  conclusion=conclusion, rule=rule, submitted=True)
    return review


class HypothesisLogicTests(unittest.TestCase):
    pair = ("item:usb", "person:1")

    def test_verified_time_requires_real_source_and_rule(self):
        status, _ = assess_review(self.pair, justification(), {"usb"}, {"Bianca"})
        self.assertEqual(status, "verified")
        for change in [{"evidence": "laptop"}, {"rule": "mt"}, {"conclusion": 4}, {"premises": [2, 1]}]:
            review = justification()
            review.update(change)
            self.assertEqual(assess_review(self.pair, review, {"usb", "laptop"}, {"Bianca"})[0], "rejected")

    def test_no_automatic_verification(self):
        review = justification()
        review["submitted"] = False
        self.assertEqual(assess_review(self.pair, review, {"usb"}, set())[0], "pending")
        review["premises"] = [None, None]
        review["submitted"] = True
        self.assertEqual(assess_review(self.pair, review, {"usb"}, set())[0], "pending")

    def test_duplicate_premises_do_not_prove_conclusion(self):
        status, explanation = assess_review(self.pair, justification(premises=[0, 0]), {"usb"}, set())
        self.assertEqual(status, "rejected")
        self.assertIn("Contraexemplo", explanation)

    def test_irrelevant_pairs_and_temporal_coincidence(self):
        self.assertEqual(available_topics(("person:0", "person:1"), {"usb"}), [])
        self.assertEqual(available_topics(("evidence:browser", "evidence:access"), {"browser", "access"}), [])
        self.assertEqual(assess_review(("person:0", "person:1"), justification(), {"usb"}, set())[0], "rejected")
        self.assertEqual(available_topics(self.pair, set()), [])

    def test_causal_premise_requires_both_reports(self):
        pair = ("evidence:browser", "evidence:credentials")
        review = justification("credentials", "support", "credentials")
        self.assertEqual(assess_review(pair, review, {"credentials"}, set())[0], "rejected")
        self.assertEqual(assess_review(pair, review, {"credentials", "browser"}, set())[0], "verified")
        review["relation"] = "time"
        self.assertEqual(assess_review(pair, review, {"credentials", "browser"}, set())[0], "rejected")

    def test_modus_tollens(self):
        pair = ("item:transmitter", "evidence:transmitter")
        review = justification("transmitter_analysis", "support", "transmitter", [1, 4], 3, "mt")
        self.assertEqual(assess_review(pair, review, {"transmitter"}, set())[0], "verified")
        review["rule"] = "mp"
        self.assertEqual(assess_review(pair, review, {"transmitter"}, set())[0], "rejected")

    def test_official_testimony_is_not_falsely_contradicted(self):
        review = justification(relation="contradiction", conclusion=4)
        self.assertEqual(assess_review(self.pair, review, {"usb"}, set())[0], "rejected")
        status, explanation = assess_review(self.pair, review, {"usb"}, {"Bianca"})
        self.assertEqual(status, "rejected")
        self.assertIn("não há contradição", explanation.lower())

    def test_contradiction_is_a_real_negation_check(self):
        # Cenário isolado do teste; não adiciona depoimentos à história do jogo.
        topic = copy.deepcopy(TOPICS["transmitter_analysis"])
        topic.update(claim="P", witness="Carlos")
        review = justification("transmitter_analysis", "contradiction", "transmitter", [1, 4], 3, "mt")
        with patch.dict(TOPICS, {"transmitter_analysis": topic}):
            status, _ = assess_review(("person:6", "item:transmitter"), review, {"transmitter"}, {"Carlos"})
            self.assertEqual(status, "verified")


class HypothesisIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.game.start()
        self.game.abilities.inspected.add("usb")
        self.game.abilities.activate("Bianca", 3, True, self.game.inventory, 1)
        self.game.inventory.collect("usb")
        self.game.board.pin("item:usb")
        self.game.open_relation("person:1", "item:usb")

    def tearDown(self):
        pygame.quit()

    def test_ui_fields_verify_and_revise(self):
        game = self.game
        self.assertEqual(game.scene, "relation")
        game.draw()
        game.cycle_relation_field("relation", ["time", "contradiction", "support"])
        game.cycle_relation_field("evidence", ["usb"])
        game.cycle_relation_field("premises", list(range(6)), 0)
        game.cycle_relation_field("premises", list(range(6)), 1)
        game.cycle_relation_field("premises", list(range(6)), 1)
        for _ in range(3):
            game.cycle_relation_field("conclusion", list(range(6)))
        game.cycle_relation_field("rule", ["mp", "mt", "ac"])
        self.assertEqual(game.relation_status(game.relation_pair)[0], "pending")
        game.verify_relation()
        self.assertEqual(game.relation_status(game.relation_pair)[0], "verified")
        game.draw()
        game.read_relation_source()
        self.assertEqual(game.scene, "dossier")
        game.draw()
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertEqual(game.scene, "relation")
        self.assertEqual(game.relation_status(game.relation_pair)[0], "verified")
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertEqual(game.scene, "board")
        game.draw()
        game.open_relation(*game.relation_pair)
        self.assertEqual(game.relation_status(game.relation_pair)[0], "verified")
        game.cycle_relation_field("rule", ["mp", "mt", "ac"])
        self.assertEqual(game.relation_status(game.relation_pair)[0], "pending")
        game.verify_relation()
        self.assertEqual(game.relation_status(game.relation_pair)[0], "rejected")
        self.assertEqual(game.puzzle_index, 0)

    def test_save_reload_recomputes_and_preserves_review(self):
        game = self.game
        game.board.reviews[game.relation_pair] = justification()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "progress.json"
            save_progress(game, path)
            pair = game.relation_pair
            load_progress(game, path)
            self.assertEqual(game.relation_status(pair)[0], "verified")
            data = json.loads(path.read_text(encoding="utf-8"))
            data["board"]["reviews"][0]["review"]["rule"] = "mt"
            path.write_text(json.dumps(data), encoding="utf-8")
            load_progress(game, path)
            self.assertEqual(game.relation_status(pair)[0], "rejected")
        game.board.clear_links()
        self.assertEqual(game.board.reviews, {})

    def test_invalid_and_old_save_data(self):
        game = self.game
        game.board.reviews[game.relation_pair] = justification()
        data = game.board.export()
        data["reviews"][0]["review"]["conclusion"] = 999
        with self.assertRaises(ValueError):
            BoardState.restore(data, {"usb"})
        data.pop("reviews")
        restored = BoardState.restore(data, {"usb"})
        self.assertEqual(restored.reviews, {})
        self.assertTrue(restored.links)

    def test_removal_cleans_reviews(self):
        self.game.board.remove("item:usb")
        self.assertFalse(self.game.board.links)
        self.assertFalse(self.game.board.reviews)


if __name__ == "__main__":
    unittest.main()
