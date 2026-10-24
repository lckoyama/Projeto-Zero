"""Testes de integração com uma tela virtual do SDL."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import unittest
from collections import deque

import pygame

from game.case_data import CHARACTERS
from game.evidence import COMPUTER, EVIDENCE
from game.puzzles import PUZZLES, validate
from game.scenes import Game


class GameTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    def tearDown(self):
        pygame.quit()

    def test_objects_reachable(self):
        """Busca caminhos considerando o tamanho do jogador e as paredes."""
        start = self.game.player.rect.center
        visited, queue = {start}, deque([start])
        while queue:
            x, y = queue.popleft()
            for point in [(x - 5, y), (x + 5, y), (x, y - 5), (x, y + 5)]:
                if point in visited or not (15 < point[0] < 1185 and 80 < point[1] < 665):
                    continue
                rect = self.game.player.rect.copy()
                rect.center = point
                if any(rect.colliderect(wall) for wall in self.game.bank.walls):
                    continue
                visited.add(point)
                queue.append(point)
        for item in EVIDENCE + CHARACTERS + [COMPUTER]:
            with self.subTest(target=item.get("object", item.get("name"))):
                self.assertTrue(any(
                    pygame.Vector2(point).distance_to(item["pos"]) < 30
                    for point in visited
                ))

    def test_progression_and_scenes(self):
        game = self.game
        game.start()
        game.begin_analysis()
        self.assertFalse(game.analysis_done)
        game.submit()
        self.assertNotEqual(game.scene, "victory")
        for item in EVIDENCE:
            game.player.rect.center = item["pos"]
            game.interact()
            self.assertEqual(game.scene, "dialogue")
        self.assertEqual(len(game.inventory.ids), 8)
        game.begin_analysis()
        self.assertTrue(game.analysis_done)
        for puzzle in PUZZLES:
            wrong = next(index for index in range(len(puzzle["options"]))
                         if not validate(puzzle, index)[0])
            before = game.puzzle_index
            game.answer(wrong)
            game.draw()
            game.next_puzzle()
            self.assertEqual(game.puzzle_index, before)
            right = next(index for index in range(len(puzzle["options"]))
                         if validate(puzzle, index)[0])
            game.answer(right)
            game.draw()
            game.next_puzzle()
        game.submit()
        self.assertEqual(game.scene, "error")
        game.accusation = [0, 0, 2, 3]
        game.submit()
        self.assertEqual(game.scene, "victory")
        for scene in ["menu", "instructions", "intro", "world", "dialogue", "inventory",
                      "board", "map", "pause", "conclusion", "error", "victory"]:
            with self.subTest(scene=scene):
                game.scene = scene
                game.draw()
        game.handle_event(pygame.event.Event(pygame.QUIT))
        self.assertFalse(game.running)

    def test_collision_and_dialogue(self):
        class RightKeys:
            def __getitem__(self, key):
                return key == pygame.K_d

        game = self.game
        game.player.rect.topleft = (1145, 350)
        game.player.position.update(game.player.rect.topleft)
        for _ in range(60):
            game.player.update(RightKeys(), 1 / 60, game.bank.walls)
        self.assertLessEqual(game.player.rect.right, 1175)
        game.show_dialogue("Depoimento", "Conversa com o investigador.")
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        self.assertEqual(game.scene, "world")


if __name__ == "__main__":
    unittest.main()
