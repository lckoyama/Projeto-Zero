"""Salas ilustradas com colisões e portas no corredor central."""
import pygame
from game.room_art import RoomArt

ROOM_NAMES = ["01 / SEGURANÇA", "02 / DIRETOR", "03 / LAZER",
              "04 / TI", "05 / SERVIDORES", "06 / RH"]


class BankMap:
    def __init__(self):
        self.art = RoomArt()
        self.rooms = []
        self.walls = [pygame.Rect(15, 80, 1170, 10), pygame.Rect(15, 655, 1170, 10),
                      pygame.Rect(15, 80, 10, 585), pygame.Rect(1175, 80, 10, 585)]
        for index in range(6):
            x = 30 + (index % 3) * 390
            y = 100 if index < 3 else 395
            rect = pygame.Rect(x, y, 360, 240)
            self.rooms.append(rect)
            door_y = rect.bottom - 8 if index < 3 else y
            closed_y = y if index < 3 else rect.bottom - 8
            self.walls.extend([pygame.Rect(x, y, 8, 240), pygame.Rect(x + 352, y, 8, 240),
                               pygame.Rect(x, closed_y, 360, 8),
                               pygame.Rect(x, door_y, 135, 8), pygame.Rect(x + 225, door_y, 135, 8)])

    def draw(self, surface, font):
        colors = [(27, 41, 57), (36, 40, 55), (29, 48, 53),
                  (25, 43, 65), (24, 36, 57), (40, 43, 53)]
        for index, rect in enumerate(self.rooms):
            pygame.draw.rect(surface, colors[index], rect)
            illustrated = self.art.draw(surface, index, rect.inflate(-16, -16), fill=True)
            label = font.render(ROOM_NAMES[index], True, (195, 221, 240))
            pygame.draw.rect(surface, (12, 18, 29), (rect.x + 12, rect.y + 12, label.get_width() + 12, label.get_height() + 8), border_radius=4)
            surface.blit(label, (rect.x + 18, rect.y + 16))
            if illustrated:
                continue
            # Mobiliário decorativo, sem bloquear portas ou pistas.
            if index == 4:
                for offset in (35, 135, 235):
                    rack = pygame.Rect(rect.x + offset, rect.y + 65, 60, 48)
                    pygame.draw.rect(surface, (47, 63, 84), rack, border_radius=4)
                    for row in range(3):
                        pygame.draw.line(surface, (58, 174, 231), (rack.x + 8, rack.y + 10 + row * 12),
                                         (rack.right - 8, rack.y + 10 + row * 12), 2)
            else:
                pygame.draw.rect(surface, (52, 65, 79), (rect.x + 135, rect.y + 65, 90, 38), border_radius=6)
                if index == 2:
                    pygame.draw.rect(surface, (54, 90, 94), (rect.x + 30, rect.y + 60, 50, 75), border_radius=8)
        for wall in self.walls:
            pygame.draw.rect(surface, (78, 95, 115), wall)
