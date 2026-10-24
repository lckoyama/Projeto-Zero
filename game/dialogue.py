"""Quebra de texto e desenho de painéis compartilhados pela interface."""
import pygame
from game.settings import TEXT


def wrap_text(text, font, width):
    lines = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = (line + " " + word).strip()
            if font.size(candidate)[0] > width and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return lines


def draw_text(surface, text, font, x, y, width=1000, color=TEXT, spacing=5):
    """Desenha texto com quebra automática e retorna o próximo y."""
    for line in wrap_text(text, font, width):
        surface.blit(font.render(line, True, color), (x, y))
        y += font.get_linesize() + spacing
    return y
