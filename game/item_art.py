"""Ilustrações dos cinco equipamentos investigáveis."""
from pathlib import Path

import pygame

from game.room_art import RoomArt, load_room_image
from game.map_markers import draw_marker

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
        draw_marker(surface, "item", position, color, active, collected)
