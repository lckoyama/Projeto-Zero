"""Transformação compartilhada entre desenho, arrasto e cliques no mural."""
import pygame
from game.board import CANVAS, BOARD_SPACE, BOARD_FILTERS, CARD_SIZE


class BoardNavigation:
    def visible_board_keys(self):
        kind = self.board.filter
        if kind == "linked":
            linked = {key for pair in self.board.links for key in pair}
            return [key for key in self.board.positions if key in linked]
        return [key for key in self.board.positions if kind == "all" or key.startswith(kind + ":")]

    def visible_board_links(self):
        keys = set(self.visible_board_keys())
        return [pair for pair in sorted(self.board.links) if set(pair) <= keys]

    def board_to_screen(self, point):
        origin = pygame.Vector2(CANVAS[:2])
        return origin + (pygame.Vector2(point) - origin) * self.board.zoom + self.board.pan

    def screen_to_board(self, point):
        origin = pygame.Vector2(CANVAS[:2])
        return origin + (pygame.Vector2(point) - origin - self.board.pan) / self.board.zoom

    def board_card_rect(self, key):
        point = self.board_to_screen(self.board.positions[key])
        return pygame.Rect(round(point.x), round(point.y), round(CARD_SIZE[0] * self.board.zoom), round(CARD_SIZE[1] * self.board.zoom))

    def clamp_board_pan(self):
        for axis in range(2):
            self.board.pan[axis] = max(40 - BOARD_SPACE[axis + 2] * self.board.zoom,
                min(CANVAS[axis + 2] - 40, self.board.pan[axis]))

    def zoom_board(self, factor, anchor=None):
        anchor = pygame.Vector2(anchor or pygame.Rect(CANVAS).center)
        before = self.screen_to_board(anchor)
        self.board.zoom = max(0.35, min(1.75, self.board.zoom * factor))
        self.board.pan = list(anchor - pygame.Vector2(CANVAS[:2]) - (before - pygame.Vector2(CANVAS[:2])) * self.board.zoom)
        self.clamp_board_pan()
        self.drag_key = None

    def fit_board(self):
        keys = self.visible_board_keys()
        if not keys:
            self.board_message = "Nenhuma ficha neste filtro. Troque o filtro ou fixe uma ficha."
            return
        bounds = pygame.Rect(self.board.positions[keys[0]], CARD_SIZE)
        for key in keys[1:]:
            bounds.union_ip(pygame.Rect(self.board.positions[key], CARD_SIZE))
        bounds.inflate_ip(70, 70)
        self.board.zoom = max(0.35, min(1.0, CANVAS[2] / bounds.width, CANVAS[3] / bounds.height))
        self.board.pan = list(pygame.Vector2(pygame.Rect(CANVAS).center) - pygame.Vector2(CANVAS[:2])
            - (pygame.Vector2(bounds.center) - pygame.Vector2(CANVAS[:2])) * self.board.zoom)
        self.clamp_board_pan()
        self.drag_key = None

    def arrange_board(self):
        self.board.arrange()
        self.fit_board()
        self.board_message = "Fichas organizadas sem sobreposição. Ligações e justificativas preservadas."

    def cycle_board_filter(self):
        self.board.filter = BOARD_FILTERS[(BOARD_FILTERS.index(self.board.filter) + 1) % len(BOARD_FILTERS)]
        self.link_start = None
        self.drag_key = None
        self.fit_board()

    def locate_board_selection(self):
        if self.board_selected not in self.board.positions:
            self.board_message = "Fixe a ficha selecionada para localizá-la no mural."
            return
        self.board.filter = "all"
        self.board.zoom = 1.0
        center = pygame.Vector2(self.board.positions[self.board_selected]) + pygame.Vector2(CARD_SIZE) / 2
        self.board.pan = list(pygame.Vector2(pygame.Rect(CANVAS).center) - center)
        self.clamp_board_pan()

    def board_navigation_event(self, event):
        canvas = pygame.Rect(CANVAS)
        if event.type == pygame.MOUSEWHEEL and canvas.collidepoint(pygame.mouse.get_pos()):
            self.zoom_board(1.15 ** max(-10, min(10, event.y)), pygame.mouse.get_pos())
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button in (1, 2):
            self.board_panning = False
        if event.type == pygame.MOUSEMOTION and self.board_panning:
            delta = pygame.Vector2(event.pos) - self.board_pan_last
            self.board.pan = list(pygame.Vector2(self.board.pan) + delta)
            self.board_pan_last = pygame.Vector2(event.pos)
            self.clamp_board_pan()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2 and canvas.collidepoint(event.pos):
            self.start_board_pan(event.pos)
            return True
        return False

    def start_board_pan(self, position):
        self.board_panning = True
        self.board_pan_last = pygame.Vector2(position)
        self.drag_key = None

    def draw_navigation(self):
        names = {"all": "Todas", "person": "Pessoas", "item": "Equipamentos", "room": "Locais", "evidence": "Pistas", "linked": "Com ligações"}
        self.ui_button("−", (238, 700, 34, 30), lambda: self.zoom_board(1 / 1.15))
        self.ui_button("+", (280, 700, 34, 30), lambda: self.zoom_board(1.15))
        self.ui_label(f"{self.board.zoom:.0%}", 326, 706, width=60)
        self.ui_button("Enquadrar", (390, 700, 108, 30), self.fit_board)
        self.ui_button("Filtro: " + names[self.board.filter], (508, 700, 220, 30), self.cycle_board_filter)
        self.ui_button("Localizar ficha", (738, 700, 220, 30), self.locate_board_selection)
