"""Retratos dos personagens, preservados inteiros e sem distorção."""
from pathlib import Path

import pygame

from game.room_art import RoomArt, load_room_image

CHARACTER_FILES = {
    "Seu Antônio": "antonio.png", "Bianca": "bianca.png",
    "Flávio": "flavio.png", "Arthur": "arthur.png",
    "Márcia": "marcia.png", "Jonas": "jonas.png", "Carlos": "carlos.png",
}
CHARACTER_ASSETS = Path(__file__).resolve().parent.parent / "assets" / "characters"


class CharacterArt(RoomArt):
    """Reutiliza o desenho proporcional e o cache das ilustrações das salas."""
    def __init__(self):
        self.images = {name: load_room_image(CHARACTER_ASSETS / filename)
                       for name, filename in CHARACTER_FILES.items()}
        self.scaled = {}

    def draw_marker(self, surface, name, position, color, active=False):
        """Pino compacto no cenário; o retrato completo fica nas telas de consulta."""
        center = pygame.Vector2(position)
        pygame.draw.circle(surface, (7, 14, 24), center, 16)
        pygame.draw.circle(surface, color, center, 14, 2)
        if active:
            pygame.draw.circle(surface, color, center, 21, 2)
        pygame.draw.circle(surface, color, center, 10)
        pygame.draw.circle(surface, (245, 255, 255), center, 5)
        pygame.draw.circle(surface, (32, 110, 121), center, 2)
