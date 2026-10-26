"""Retratos dos personagens, preservados inteiros e sem distorção."""
from pathlib import Path

import pygame

from game.room_art import RoomArt, load_room_image
from game.map_markers import draw_marker

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

    def draw_marker(self, surface, name, position, color, active=False, investigated=False):
        """Pino compacto no cenário; o retrato completo fica nas telas de consulta."""
        draw_marker(surface, "person", position, color, active, investigated)
