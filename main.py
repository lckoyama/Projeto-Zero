"""Entrada do Protocolo Zero: execute com python main.py."""
try:
    import pygame
except ImportError:
    raise SystemExit("Pygame não instalado. Execute: python -m pip install -r requirements.txt")

from game.scenes import Game

if __name__ == "__main__":
    Game().run()
