"""Carregamento e desenho proporcional das ilustrações das salas."""
from functools import lru_cache
from pathlib import Path

import pygame

ROOM_FILES = ("seguranca.png", "diretor.png", "lazer.png",
              "ti.png", "servidores.png", "rh.png")
ROOM_ASSETS = Path(__file__).resolve().parent.parent / "assets" / "rooms"


@lru_cache(maxsize=32)
def load_room_image(path):
    """Carrega uma vez; imagem ausente ou inválida permite usar o cenário básico."""
    try:
        return pygame.image.load(str(path)).convert_alpha()
    except (OSError, pygame.error):
        return None


class RoomArt:
    def __init__(self):
        self.images = [load_room_image(ROOM_ASSETS / name) for name in ROOM_FILES]
        self.scaled = {}

    def draw(self, surface, index, area):
        """Encaixa a imagem inteira sem distorção, com versões reduzidas em cache."""
        source = self.images[index]
        if source is None:
            return False
        area = pygame.Rect(area)
        key = (index, area.size)
        if key not in self.scaled:
            ratio = min(area.width / source.get_width(), area.height / source.get_height())
            size = (max(1, round(source.get_width() * ratio)),
                    max(1, round(source.get_height() * ratio)))
            self.scaled[key] = pygame.transform.scale(source, size)
        picture = self.scaled[key]
        surface.blit(picture, picture.get_rect(center=area.center))
        return True
