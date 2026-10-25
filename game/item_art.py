"""Ilustrações dos cinco equipamentos investigáveis."""
from pathlib import Path

import pygame

from game.room_art import RoomArt, load_room_image

ITEM_FILES = {
    "wifi": "celular.png", "computer": "computador.png",
    "transmitter": "transmissor.png", "laptop": "notebook.png",
    "usb": "pendrive.png",
}
ITEM_ASSETS = Path(__file__).resolve().parent.parent / "assets" / "items"


class ItemArt(RoomArt):
    def __init__(self):
        self.images = {key: load_room_image(ITEM_ASSETS / filename)
                       for key, filename in ITEM_FILES.items()}
        self.scaled = {}

    def draw(self, surface, key, area):
        """Registros sem ilustração própria continuam usando marcadores simples."""
        if key not in self.images:
            return False
        return super().draw(surface, key, area)

    def draw_marker(self, surface, key, position, collected, active=False):
        """Pino geométrico discreto; o equipamento é exibido ao inspecionar."""
        color = (102, 216, 167) if collected else (238, 181, 99)
        center = pygame.Vector2(position)
        if active:
            pygame.draw.circle(surface, (8, 16, 26), center, 19)
            pygame.draw.circle(surface, color, center, 16, 2)
        points = [(center.x, center.y - 9), (center.x + 9, center.y),
                  (center.x, center.y + 9), (center.x - 9, center.y)]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.circle(surface, (255, 245, 214), center, 3)
        if collected:
            pygame.draw.circle(surface, color, (center.x + 11, center.y - 11), 4)
