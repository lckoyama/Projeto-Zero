"""Marcadores suaves e legíveis para os alvos da investigação."""
from functools import lru_cache

import pygame


@lru_cache(maxsize=64)
def marker_image(kind, color, active, collected):
    scale = 3
    image = pygame.Surface((46 * scale, 46 * scale), pygame.SRCALPHA)

    def point(x, y):
        return (round(x * scale), round(y * scale))

    def line(points, ink, width=2):
        pygame.draw.lines(image, ink, False, [point(*p) for p in points], width * scale)

    background = (38, 154, 99) if collected else (36, 113, 199)
    ink = (255, 255, 255)
    if active:
        pygame.draw.circle(image, (*background, 75), point(23, 23), 22 * scale)
    pygame.draw.circle(image, (0, 0, 0, 65), point(23, 25), 17 * scale)
    pygame.draw.circle(image, background, point(23, 23), 16 * scale)
    pygame.draw.circle(image, ink, point(23, 23), 16 * scale, scale)
    if kind == "person":
        pygame.draw.circle(image, ink, point(23, 18), 4 * scale)
        pygame.draw.rect(image, ink, (16 * scale, 24 * scale, 14 * scale, 9 * scale),
                         border_radius=4 * scale)
    else:
        outline = [(23, 14), (31, 18), (31, 28), (23, 32), (15, 28), (15, 18), (23, 14)]
        line(outline, ink)
        line([(15, 18), (23, 22), (31, 18)], ink)
        line([(23, 22), (23, 32)], ink)
    if collected:
        pygame.draw.circle(image, background, point(35, 12), 6 * scale)
        pygame.draw.circle(image, ink, point(35, 12), 5 * scale)
        line([(32, 12), (34, 14), (38, 10)], background, 1)
    return pygame.transform.smoothscale(image, (46, 46))


def draw_marker(surface, kind, position, color, active=False, collected=False):
    image = marker_image(kind, tuple(color), active, collected)
    surface.blit(image, image.get_rect(center=position))
