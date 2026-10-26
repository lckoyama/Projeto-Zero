"""Interface do dossiê e mural de hipóteses, desenhada inteiramente em Pygame."""
import pygame

from game import settings as s
from game.abilities import ABILITIES
from game.board import CANVAS, CARD_SIZE, ITEM_IDS
from game.case_data import CHARACTERS, INTRO
from game.dialogue import draw_text, wrap_text
from game.evidence import COMPUTER, EVIDENCE
from game.map import ROOM_NAMES
from game.puzzles import PUZZLES

INK = (9, 13, 22)
EDGE = (39, 54, 72)
PAPER = (219, 226, 232)
CYAN = (63, 193, 216)


class InvestigationUI:
    def setup_board_ui(self):
        self.board_selected = "person:0"
        self.catalog = "person"
        self.catalog_page = 0
        self.link_mode = False
        self.link_start = None
        self.drag_key = None
        self.drag_offset = (0, 0)
        self.board_panning = False
        self.board_pan_last = pygame.Vector2()
        self.board_message = "Arraste as fichas para organizar sua investigação."

    def ui_label(self, text, x, y, color=s.TEXT, width=220):
        return draw_text(self.screen, text, self.small, x, y, width, color, spacing=4)

    def ui_button(self, label, rect, action, active=False, enabled=True):
        rect = pygame.Rect(rect)
        hover = rect.collidepoint(pygame.mouse.get_pos()) and enabled
        pygame.draw.rect(self.screen, (7, 12, 20), rect.move(0, 3), border_radius=5)
        pygame.draw.rect(self.screen, (23, 56, 69) if active or hover else (17, 26, 40),
                         rect, border_radius=5)
        pygame.draw.rect(self.screen, CYAN if active or hover else EDGE, rect, 1, border_radius=5)
        rendered = self.small.render(label, True, s.TEXT if enabled else (94, 111, 130))
        self.screen.blit(rendered, rendered.get_rect(center=rect.center))
        if enabled:
            self.buttons.append((rect, action))

    def dossier_header(self, subtitle):
        self.screen.fill(INK)
        pygame.draw.rect(self.screen, (12, 19, 32), (0, 0, 1200, 66))
        pygame.draw.line(self.screen, EDGE, (0, 66), (1200, 66))
        pygame.draw.rect(self.screen, CYAN, (22, 20, 5, 25))
        self.ui_label("PROTOCOLO ZERO", 40, 22, width=210)
        pygame.draw.line(self.screen, EDGE, (235, 18), (235, 48))
        self.ui_label("INVESTIGAÇÃO / " + subtitle, 255, 23, CYAN, 510)

    def entry(self, key):
        kind, identifier = key.split(":", 1)
        if kind == "person":
            person = self.characters[int(identifier)]
            heard = person["name"] in self.talked
            body = person["role"] + "\n\n" + person["skill"]
            body += "\n\n" + ABILITIES[person["name"]]["name"] + ": " + ABILITIES[person["name"]]["description"]
            body += "\n\n" + ("\n".join(person["lines"]) if heard else "Depoimento ainda não coletado. Encontre este personagem no banco.")
            if person["name"] in self.abilities.records:
                body += "\n\n" + self.abilities.records[person["name"]]
            return person["name"], person["role"].split(" • ")[0], body, heard
        if kind == "room":
            index = int(identifier)
            people = ", ".join(p["name"] for p in self.characters if p["room"] == index)
            return ROOM_NAMES[index].split(" / ")[1], "LOCAL DE INVESTIGAÇÃO", (
                "Personagens disponíveis: " + people + ".\n\nEntre pela porta voltada ao corredor central. "
                "Examine objetos com E e consulte as habilidades dos personagens.\n\n"
                "A posição atual no mapa não é um álibi histórico. Os horários devem ser verificados nos registros."), False
        item = self.computer if identifier == "computer" else next(e for e in self.evidence if e["id"] == identifier)
        known = ("computer" in self.abilities.inspected if identifier == "computer"
                 else self.inventory.contains(identifier))
        text = item["text"] if known else "Registro ainda não disponível. Examine o equipamento no banco e cumpra os requisitos de análise para consultar suas evidências."
        return (item["title"] if kind == "evidence" else item["object"]), ("EVIDÊNCIA" if kind == "evidence" else "EQUIPAMENTO"), text, known

    def entry_art(self, key, rect):
        kind, identifier = key.split(":", 1)
        if kind == "person":
            return self.character_art.draw(self.screen, self.characters[int(identifier)]["name"], rect)
        if kind == "room":
            return self.bank.art.draw(self.screen, int(identifier), rect)
        if self.item_art.draw(self.screen, identifier, rect):
            return True
        # Registros textuais usam uma ficha de documento, sem uma fotografia inventada.
        rect = pygame.Rect(rect)
        pygame.draw.rect(self.screen, (27, 41, 55), rect)
        self.ui_label("REGISTRO", rect.x + 8, rect.y + 12, CYAN, rect.width - 16)
        for offset in (40, 53, 66):
            pygame.draw.line(self.screen, EDGE, (rect.x + 8, rect.y + offset), (rect.right - 8, rect.y + offset), 2)
        return True

    def catalog_keys(self):
        if self.catalog == "person":
            return [f"person:{i}" for i in range(7)]
        if self.catalog == "room":
            return [f"room:{i}" for i in range(6)]
        if self.catalog == "item":
            return [f"item:{key}" for key in ITEM_IDS]
        return [f"evidence:{item['id']}" for item in self.evidence if self.inventory.contains(item["id"])]

    def choose_catalog(self, category):
        self.catalog, self.catalog_page = category, 0

    def page_catalog(self, direction):
        pages = max(1, (len(self.catalog_keys()) + 5) // 6)
        self.catalog_page = (self.catalog_page + direction) % pages

    def toggle_links(self):
        self.link_mode = not self.link_mode
        self.link_start = None
        self.drag_key = None
        self.board_message = "Clique em duas fichas para escolher e justificar a relação." if self.link_mode else "Arraste fichas. Clique numa linha para revisar sua justificativa."

    def pin_selected(self):
        added = self.board.pin(self.board_selected)
        if added:
            self.locate_board_selection()
        self.board_message = "Ficha fixada. Você pode arrastá-la no mural." if added else "Essa ficha já está no mural."

    def remove_selected(self):
        self.board.remove(self.board_selected)
        self.link_start = None
        self.board_message = "Ficha retirada do mural. O registro continua no catálogo."

    def board_event(self, event):
        """Arrastar e ligar fichas só altera hipóteses, nunca as evidências."""
        if self.board_navigation_event(event):
            return True
        if event.type == pygame.MOUSEWHEEL:
            if pygame.mouse.get_pos()[0] < CANVAS[0]:
                self.page_catalog(-event.y)
                return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.drag_key = None
        if event.type == pygame.MOUSEMOTION and self.drag_key:
            point = self.screen_to_board(event.pos) - self.drag_offset
            self.board.move(self.drag_key, point)
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
            if not pygame.Rect(CANVAS).collidepoint(event.pos):
                return False
            if event.button == 1 and not self.link_mode:
                for pair, _, _, rect, _ in reversed(self.link_labels()):
                    if rect.collidepoint(event.pos):
                        self.open_relation(*pair)
                        return True
            for key in reversed(self.visible_board_keys()):
                position = self.board.positions[key]
                if self.board_card_rect(key).collidepoint(event.pos):
                    self.board_selected = key
                    if event.button == 3:
                        self.remove_selected()
                    elif self.link_mode:
                        if self.link_start is None:
                            self.link_start = key
                            self.board_message = "Selecione a segunda ficha."
                        else:
                            self.open_relation(self.link_start, key)
                    else:
                        # A ficha selecionada passa à frente das demais.
                        self.board.positions.pop(key)
                        self.board.positions[key] = position
                        self.drag_key = key
                        self.drag_offset = self.screen_to_board(event.pos) - position
                    return True
            if event.button == 1 and pygame.Rect(CANVAS).collidepoint(event.pos):
                point = pygame.Vector2(event.pos)
                for pair in self.visible_board_links():
                    first, second = (self.board_to_screen(pygame.Vector2(self.board.positions[key]) + (59, 3)) for key in pair)
                    vector = second - first
                    if vector.length_squared():
                        ratio = max(0, min(1, (point - first).dot(vector) / vector.length_squared()))
                        if point.distance_to(first + vector * ratio) <= 6:
                            self.open_relation(*pair)
                            return True
                if not self.link_mode:
                    self.start_board_pan(event.pos)
                    return True
        return False

    def draw_board_card(self, key, position):
        target = self.screen
        card = pygame.Surface((CARD_SIZE[0] + 16, CARD_SIZE[1] + 16), pygame.SRCALPHA)
        try:
            self.screen = card
            self.draw_board_card_content(key, (6, 6))
        finally:
            self.screen = target
        size = (round(card.get_width() * self.board.zoom), round(card.get_height() * self.board.zoom))
        rendered = pygame.transform.smoothscale(card, size) if self.board.zoom != 1 else card
        point = self.board_to_screen(position) - pygame.Vector2(6, 6) * self.board.zoom
        self.screen.blit(rendered, point)

    def draw_board_card_content(self, key, position):
        rect = pygame.Rect(position, CARD_SIZE)
        pygame.draw.rect(self.screen, (3, 6, 10), rect.move(5, 7), border_radius=2)
        pygame.draw.rect(self.screen, PAPER, rect)
        image_rect = pygame.Rect(rect.x + 5, rect.y + 6, rect.width - 10, 105)
        pygame.draw.rect(self.screen, (15, 22, 31), image_rect)
        self.entry_art(key, image_rect)
        note = self.board.notes.get(key)
        if note:
            label = {"none": "Nota pessoal", "investigate": "Investigar", "suspect": "Suspeita", "discarded": "Descartada*"}[note["mark"]]
            pygame.draw.rect(self.screen, (42, 35, 24), (rect.x + 5, rect.y + 87, rect.width - 10, 23))
            self.ui_label(label, rect.x + 8, rect.y + 89, (240, 203, 124), rect.width - 14)
        title, category, _, known = self.entry(key)
        lines = wrap_text(title, self.small, rect.width - 12)
        for index, line in enumerate(lines[:2]):
            self.ui_label(line, rect.x + 6, rect.y + 113 + index * 18, (20, 30, 42), rect.width - 12)
        pin_color = s.RED if key == self.link_start else CYAN if known else (143, 155, 171)
        pygame.draw.circle(self.screen, pin_color, (rect.centerx, rect.top + 3), 4)
        if key == self.board_selected:
            pygame.draw.rect(self.screen, CYAN, rect.inflate(4, 4), 2)

    def draw_board(self):
        self.dossier_header("O MISTÉRIO DA INVASÃO BANCÁRIA")
        self.ui_button("Explorar banco", (855, 17, 145, 32), lambda: self.set_scene("world"))
        self.ui_button("Salvar", (1010, 17, 75, 32), self.save_game)
        self.ui_button("Menu", (1095, 17, 80, 32), lambda: self.set_scene("menu"))
        # Arquivo do caso, à esquerda.
        pygame.draw.rect(self.screen, (13, 20, 33), (0, 67, 218, 733))
        pygame.draw.line(self.screen, EDGE, (218, 67), (218, 800))
        self.ui_label("ARQUIVO DO CASO / 001", 18, 88, CYAN, 185)
        self.ui_label("Invasão bancária", 18, 130, width=185)
        self.ui_label("Informações confidenciais comprometidas. Acesso indevido identificado às 21h07. Reconstrua o incidente com evidências.", 18, 161, s.MUTED, 185)
        self.ui_label("CONSULTAR DOSSIÊS", 18, 294, CYAN, 185)
        for index, (kind, label) in enumerate([("person", "Pessoas"), ("item", "Itens"), ("room", "Locais"), ("evidence", "Pistas")]):
            self.ui_button(label, (16 + index % 2 * 96, 324 + index // 2 * 38, 90, 31),
                           lambda value=kind: self.choose_catalog(value), active=self.catalog == kind)
        keys = self.catalog_keys()
        for index, key in enumerate(keys[self.catalog_page * 6:self.catalog_page * 6 + 6]):
            name = self.entry(key)[0]
            if len(name) > 22:
                name = name[:21] + "…"
            self.ui_button(name, (16, 414 + index * 39, 186, 33),
                           lambda value=key: setattr(self, "board_selected", value), active=key == self.board_selected)
        if not keys:
            self.ui_label("As pistas aparecem aqui após a coleta no banco.", 18, 425, s.MUTED, 180)
        if len(keys) > 6:
            self.ui_button("Anterior", (16, 655, 89, 30), lambda: self.page_catalog(-1))
            self.ui_button("Próxima", (112, 655, 90, 30), lambda: self.page_catalog(1))
        self.ui_button("Comparar depoimentos", (16, 693, 186, 30), self.open_comparison)
        self.ui_button("Registros / habilidades", (16, 726, 186, 25), lambda: self.set_scene("ability_records"))
        self.ui_button("Linha do tempo", (16, 753, 186, 30), lambda: self.set_scene("timeline"))
        # Mural central.
        pygame.draw.rect(self.screen, (12, 18, 23), CANVAS)
        for x in range(238, 970, 16):
            for y in range(141, 690, 16):
                self.screen.set_at((x, y), (25, 33, 39))
        self.ui_label("MURAL DE HIPÓTESES", 238, 89, width=210)
        self.ui_button("Ligar fichas", (453, 84, 125, 32), self.toggle_links, active=self.link_mode)
        self.ui_button("Organizar", (588, 84, 112, 32), self.arrange_board)
        self.ui_button("Limpar ligações", (710, 84, 145, 32), self.board.clear_links)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(CANVAS)
        for first, second in self.visible_board_links():
            a, b = (self.board_to_screen(pygame.Vector2(self.board.positions[key]) + (59, 3)) for key in (first, second))
            status, _ = self.relation_status((first, second))
            color = {"pending": s.MUTED, "verified": s.GREEN, "rejected": s.RED}[status]
            pygame.draw.line(self.screen, color, a, b, 2)
        for key in self.visible_board_keys():
            if self.board_card_rect(key).inflate(16, 16).colliderect(CANVAS):
                self.draw_board_card(key, self.board.positions[key])
        self.draw_link_labels()
        if not self.visible_board_keys():
            self.ui_label("Nenhuma ficha neste filtro. Clique em Filtro para trocar.", 300, 400, s.MUTED, 600)
        self.screen.set_clip(old_clip)
        self.draw_navigation()
        self.ui_label(self.board_message, 238, 739, CYAN, 720)
        self.ui_label("Roda: zoom • Arraste o fundo ou use o botão do meio para mover o mural.", 238, 779, s.MUTED, 720)
        # Inspeção e progressão, à direita.
        pygame.draw.rect(self.screen, (13, 20, 33), (982, 67, 218, 733))
        pygame.draw.line(self.screen, EDGE, (982, 67), (982, 800))
        self.ui_label("FICHA SELECIONADA", 998, 88, CYAN, 190)
        title, category, body, known = self.entry(self.board_selected)
        self.entry_art(self.board_selected, (1025, 124, 132, 150))
        self.ui_label(title, 998, 289, width=185)
        self.ui_label(category, 998, 338, CYAN, 185)
        self.ui_label("Registro disponível" if known else "A investigar", 998, 367, s.GREEN if known else s.MUTED, 185)
        self.ui_button("Abrir ficha", (998, 409, 184, 35), lambda: self.set_scene("dossier"))
        self.ui_button("Fixar no mural", (998, 453, 184, 35), self.pin_selected)
        self.ui_button("Montar hipótese", (998, 497, 184, 35), self.open_theory)
        self.ui_label(f"EVIDÊNCIAS  {len(self.inventory.ids):02}/08", 998, 566, CYAN, 185)
        self.ui_label(f"DEDUÇÕES    {self.puzzle_index:02}/08", 998, 594, s.MUTED, 185)
        count = len(self.inventory.ids)
        for index in range(8):
            pygame.draw.rect(self.screen, CYAN if index < count else EDGE, (998 + index * 23, 631, 18, 4))
        ready = count == 8
        finished = self.puzzle_index == len(self.puzzles)
        label = "Apresentar conclusão" if finished else "Resolver lógica" if ready else "Reúna as 8 pistas"
        def progress():
            if finished:
                self.set_scene("conclusion")
            elif self.analysis_done:
                self.set_scene("puzzle")
            else:
                self.begin_analysis()
        self.ui_button(label, (998, 665, 184, 42), progress, enabled=ready, active=ready)
        self.ui_button("Anotações pessoais", (998, 713, 184, 32), self.open_notes)
        if self.save_message:
            self.ui_label(self.save_message, 998, 750, s.MUTED, 185)

    def draw_dossier(self):
        title, category, body, _ = self.entry(self.board_selected)
        self.dossier_header("DOSSIÊ / " + category)
        self.entry_art(self.board_selected, (50, 150, 300, 420))
        self.screen.blit(self.heading.render(title, True, s.TEXT), (390, 110))
        self.text(body, x=390, y=178, width=755, small=True)
        destination = "relation" if self.relation_return else "puzzle" if self.sheet_return else "board"
        label = "Voltar à relação" if self.relation_return else "Voltar à dedução" if self.sheet_return else "Voltar ao mural"
        self.ui_button(label, (390, 713, 220, 44),
                       lambda: self.set_scene(destination))
        self.ui_button("Explorar banco", (630, 713, 220, 44), lambda: self.set_scene("world"))

    def draw_timeline(self):
        self.dossier_header("CRONOLOGIA / REGISTROS DESCOBERTOS")
        self.text("Linha do tempo", x=60, y=100, color=CYAN)
        self.ui_label("A ordem dos acontecimentos não prova causalidade. Consulte os laudos e teste as premissas.", 60, 145, s.MUTED, 1080)
        events = [
            ("laptop", "19h50–20h30", "Apresentação institucional", "Uso do notebook de Arthur durante a reunião."),
            ("usb", "20h20", "Teste autorizado", "Uso do pendrive de Bianca conforme autorização e análise."),
            ("browser", "20h35", "Evento do navegador", "Horário preservado no histórico. Consulte o laudo para relacionar o evento."),
            ("computer", "20h45", "Consulta de relatórios", "Atividade de Márcia no computador interno."),
            ("access", "21h07", "Identificação do acesso indevido", "Horário da detecção pelo banco, não necessariamente do início do incidente."),
            ("transmitter", "21h15", "Transmissor encontrado", "Horário da descoberta; a análise técnica é necessária para avaliar seu uso."),
        ]
        if self.case["revision"] >= 2 and self.case_id != "link":
            events[4] = ("access", "21h07", "Detecção do incidente", "O alerta surgiu depois do evento inicial. Consulte o laudo do incidente.")
            if self.case_id == "extension":
                events[3] = ("computer", "20h45", "Alteração de permissões", "Márcia aplicou um perfil antigo durante a consulta de relatórios.")
        events += self.case["timeline_extra"]
        events.sort(key=lambda event: event[1])
        for index, (key, time, title, description) in enumerate(events):
            y = 185 + index * 72
            known = key in self.inventory.ids or (key == "computer" and key in self.abilities.inspected)
            pygame.draw.rect(self.screen, (16, 25, 38), (60, y, 1080, 65), border_radius=4)
            self.ui_label(time if known else "--:--", 80, y + 21, CYAN if known else s.MUTED, 150)
            self.ui_label(title if known else "Registro ainda não descoberto", 250, y + 9, s.TEXT, 840)
            self.ui_label(description if known else "Explore o banco e obtenha o registro correspondente.", 250, y + 34, s.MUTED, 840)
        self.ui_button("Voltar ao mural", (60, 713, 230, 44), lambda: self.set_scene("board"))

    def draw_case_conclusion(self):
        self.dossier_header("RECONSTRUÇÃO / CONCLUSÃO DO CASO")
        self.ui_label("FORMULE SUA CONCLUSÃO", 60, 110, CYAN, 600)
        self.text("Confronte sua hipótese com as evidências.", x=60, y=150, width=1080)
        self.ui_label("Escolha cada campo clicando para alternar. O horário deve corresponder ao evento inicial.", 60, 198, s.MUTED, 1080)
        person_key = f"person:{self.accusation[0]}"
        self.entry_art(person_key, (60, 270, 260, 330))
        labels = ("PESSOA ENVOLVIDA", "MÉTODO", "EQUIPAMENTO", "HORÁRIO DO EVENTO")
        for row, options in enumerate(self.final_options()):
            y = 265 + row * 93
            self.ui_label(labels[row], 385, y, CYAN, 740)
            self.ui_button(options[self.accusation[row]] + "   >", (385, y + 27, 745, 43),
                           lambda value=row: self.change_choice(value))
        self.ui_button("Voltar ao mural", (60, 707, 260, 46), lambda: self.set_scene("board"))
        self.ui_button("Validar reconstrução", (385, 707, 350, 46), self.submit,
                       active=True, enabled=self.analysis_done and self.puzzle_index == len(self.puzzles))

    def draw_case_menu(self):
        self.dossier_header("DOSSIÊ 001 / ACESSO RESTRITO")
        self.ui_label("BANCO / INVESTIGAÇÃO EM ABERTO", 54, 123, CYAN, 500)
        self.screen.blit(self.heading.render("PROTOCOLO ZERO", True, s.TEXT), (50, 169))
        self.text("O Mistério da Invasão Bancária", x=54, y=220, width=500, color=s.MUTED)
        self.text("Um incidente. Oito evidências.\nUma conclusão que precisa de prova.", x=54, y=292, width=450)
        self.text("Explore o banco, consulte os depoimentos e conecte suas hipóteses no mural. Use lógica matemática para reconstruir o incidente.", x=54, y=393, width=435, small=True, color=s.MUTED)
        self.ui_button("INICIAR INVESTIGAÇÃO", (54, 520, 400, 48), self.start, active=True)
        self.ui_button("Retomar", (54, 583, 194, 40),
                       lambda: self.set_scene("board"), enabled=self.has_game)
        self.ui_button("Carregar partida", (260, 583, 194, 40), self.load_game)
        self.ui_button("Instruções", (54, 637, 194, 36), lambda: self.set_scene("instructions"))
        self.ui_button("Sair", (260, 637, 194, 36), lambda: setattr(self, "running", False))
        self.ui_label(self.save_message, 54, 698, s.MUTED, 440)
        # Composição editorial com os próprios assets, sem relações pré-julgadas.
        pygame.draw.rect(self.screen, (14, 22, 32), (520, 100, 638, 611), border_radius=8)
        self.bank.art.draw(self.screen, 0, (560, 130, 550, 300))
        self.ui_label("O CENÁRIO", 554, 120, CYAN, 200)
        for index, key in enumerate(("person:1", "item:usb", "person:2")):
            self.draw_board_card(key, (575 + index * 180, 468))
        self.ui_label("INVESTIGAR  /  RELACIONAR  /  DEDUZIR", 580, 656, CYAN, 540)
        self.ui_label("RESOLUÇÃO DE PROBLEMAS COM LÓGICA MATEMÁTICA", 54, 757, s.MUTED, 850)
