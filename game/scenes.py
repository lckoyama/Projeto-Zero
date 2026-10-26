"""Cenas e loop de eventos. Nenhum diálogo interrompe o loop do Pygame."""
import pygame
from game.cases import CASE_REVISION, build_case, choose_case
from game import settings as s
from game.case_data import CHARACTERS, INTRO, SOLUTION, REASONING
from game.dialogue import draw_text
from game.evidence import EVIDENCE, COMPUTER
from game.inventory import Inventory
from game.map import BankMap, ROOM_NAMES
from game.player import Player
from game.puzzles import PUZZLES
from game.abilities import ABILITIES, AbilitySystem
from game.ability_scenes import AbilityScenes
from game.character_art import CharacterArt
from game.item_art import ItemArt
from game.board import BoardState
from game.investigation_ui import CYAN, InvestigationUI
from game.deduction_ui import DeductionUI
from game.hypothesis_ui import HypothesisUI
from game.comparison_ui import ComparisonUI
from game.theory_ui import TheoryUI
from game.theory import empty_theory
from game.board_navigation import BoardNavigation
from game.notes_ui import NotesUI
from game.scoring import Score
from game.results_ui import ResultsUI


class Game(ResultsUI, NotesUI, BoardNavigation, TheoryUI, ComparisonUI, HypothesisUI, DeductionUI, InvestigationUI, AbilityScenes):
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((s.WIDTH, s.HEIGHT))
        pygame.display.set_caption(s.TITLE)
        self.clock = pygame.time.Clock()
        # Fonte do sistema com suporte a símbolos; fallback do próprio Pygame.
        self.font = pygame.font.SysFont("segoeuisymbol,dejavusans,cambria,arial", 21)
        self.small = pygame.font.SysFont("segoeuisymbol,dejavusans,cambria,arial", 16)
        self.heading = pygame.font.SysFont("segoeui,dejavusans,arial", 34, bold=True)
        self.buttons = []
        self.running = True
        self.scene = "menu"
        self.has_game = False
        self.reset()

    def reset(self, case_id="link", revision=CASE_REVISION):
        pygame.key.stop_text_input()
        self.case = build_case(case_id, revision)
        self.case_id = self.case["id"]
        self.demo_mode = False
        for field in ("characters", "evidence", "computer", "puzzles", "sheets", "topics"):
            setattr(self, field, self.case[field])
        self.bank = BankMap()
        self.character_art = CharacterArt()
        self.item_art = ItemArt()
        self.board = BoardState()
        self.setup_board_ui()
        self.active_item = None
        self.player = Player()
        self.proof_page = 0
        self.score = Score()
        self.inventory = Inventory(self.score.find_evidence)
        self.abilities = AbilitySystem(self.case["ability_results"])
        self.active_person = None
        self.record_person = "Seu Antônio"
        self.ability_feedback = ""
        self.ability_success = False
        self.save_message = ""
        self.talked = set()
        self.analysis_done = False
        self.puzzle_index = 0
        self.reset_sheet()
        self.sheet_return = False
        self.relation_return = False
        self.feedback = ""
        self.correct = False
        self.selection = 0
        self.accusation = [0, 0, 0, 0]
        self.final_choice_open = None
        self.theory = empty_theory()
        self.theory_field = 0
        self.theory_reading = None
        self.message = "Explore o banco. Aproxime-se dos marcadores e pressione E."

    def start(self):
        self.reset(choose_case())
        self.has_game = True
        self.scene = "intro"

    def start_demo(self):
        self.reset("link")
        self.demo_mode = True
        self.has_game = True
        self.scene = "intro"

    def retry_conclusion(self):
        self.score.outcome = None
        self.set_scene("conclusion")

    def text(self, text, x=60, y=100, width=1080, color=s.TEXT, small=False):
        return draw_text(self.screen, text, self.small if small else self.font, x, y, width, color)

    def title(self, title, subtitle=""):
        self.screen.fill(s.BG)
        pygame.draw.rect(self.screen, s.RED, (30, 36, 5, 42), border_radius=2)
        self.screen.blit(self.heading.render(title, True, s.TEXT), (60, 36))
        pygame.draw.line(self.screen, s.EDGE, (60, 88), (1140, 88), 1)
        if subtitle:
            self.text(subtitle, y=82, color=s.MUTED, small=True)

    def button(self, label, rect, action, enabled=True):
        rect = pygame.Rect(rect)
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        color = s.PANEL_ALT if hovered and enabled else s.PANEL
        shadow = rect.move(0, 3)
        pygame.draw.rect(self.screen, s.PANEL_DARK, shadow, border_radius=8)
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, s.CYAN if hovered and enabled else
                         (s.BLUE if enabled else s.EDGE), rect, 1, border_radius=8)
        label_surface = self.small.render(label, True, s.TEXT if enabled else s.MUTED)
        self.screen.blit(label_surface, label_surface.get_rect(center=rect.center))
        if enabled:
            self.buttons.append((rect, action))

    def set_scene(self, scene):
        if self.scene == "notes" and scene != "notes":
            pygame.key.stop_text_input()
        if scene != "conclusion":
            self.final_choice_open = None
        self.board_panning = False
        if scene != "dossier":
            self.sheet_return = False
            self.relation_return = False
        self.drag_key = None
        self.link_start = None
        self.scene = scene

    def show_dialogue(self, title, body, item_id=None):
        self.active_person = None
        self.active_item = item_id
        self.dialogue_title, self.dialogue_body = title, body
        self.scene = "dialogue"

    def nearest(self):
        targets = [("person", person) for person in self.characters]
        targets += [("evidence", item) for item in self.evidence
                    if self.abilities.visible(item["id"])] + [("computer", self.computer)]
        nearby = [(pygame.Vector2(item["pos"]).distance_to(self.player.rect.center), kind, item)
                  for kind, item in targets]
        distance, kind, item = min(nearby, key=lambda entry: entry[0])
        return (kind, item) if distance <= 66 else None

    def interact(self):
        target = self.nearest()
        if not target:
            self.message = "Aproxime-se de um personagem ou objeto com marcação dourada."
            return
        kind, item = target
        if kind == "person":
            self.talked.add(item["name"])
            self.show_dialogue(item["name"], item["role"] + "\n" + item["skill"]
                               + "\n\n" + "\n\n".join(item["lines"]))
            self.active_person = item["name"]
        elif kind == "evidence":
            # Examinar o objeto registra o pré-requisito da perícia; só a
            # coleta abaixo torna a evidência parte do inventário.
            self.abilities.inspected.add(item["id"])
            reason = self.abilities.lock_reason(item["id"])
            if reason:
                self.show_dialogue(item["object"], reason, item["id"])
                return
            new = self.inventory.collect(item["id"])
            self.show_dialogue(item["title"], item["text"] +
                               ("\n\nEvidência adicionada ao inventário." if new else "\n\nEvidência já coletada."), item["id"])
        else:
            self.abilities.inspected.add("computer")
            self.show_dialogue(item["object"], item["text"], "computer")

    def next_puzzle(self):
        if self.correct:
            self.puzzle_index += 1
            self.reset_sheet()
        self.feedback = ""
        self.correct = False
        if self.puzzle_index == len(self.puzzles):
            self.scene = "board"

    def change_choice(self, row):
        self.accusation[row] = (self.accusation[row] + 1) % len(self.final_options()[row])

    def toggle_final_choice(self, row):
        self.final_choice_open = None if self.final_choice_open == row else row

    def select_final_choice(self, row, choice):
        self.accusation[row] = choice
        self.final_choice_open = None

    def final_options(self):
        return [[person["name"] for person in self.characters],
                ["Link malicioso", "Falha na rede interna", "Pendrive", "Dispositivo transmissor", "Arquivo adulterado", "Extensão maliciosa", "Sabotagem de registros"],
                ["Notebook externo", "Computador interno", "Celular conectado ao Wi-Fi", "Dispositivo transmissor", "Pendrive"],
                ["19h50", "20h20", "20h30", "20h35", "20h45", "21h07", "21h15"]]

    def submit(self):
        if self.analysis_done and self.puzzle_index == len(self.puzzles):
            if (self.scene in ("victory", "error") and self.score.outcome is not None
                    and tuple(self.accusation) == self.score.last_accusation):
                self.set_scene(self.score.outcome)
                return
            correct = self.accusation == self.case["answer"]
            self.score.accuse(self.accusation, correct)
            self.set_scene("victory" if correct else "error")

    def handle_event(self, event):
        if self.scene == "notes" and self.notes_event(event):
            return
        if event.type == pygame.MOUSEBUTTONUP or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            self.drag_key = None
        if self.scene == "board" and self.board_event(event):
            return
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action in self.buttons:
                if rect.collidepoint(event.pos):
                    action()
                    break
        elif event.type == pygame.KEYDOWN:
            key = event.key
            if key == pygame.K_ESCAPE:
                if self.scene == "world":
                    self.scene = "pause"
                elif self.scene in ("dialogue", "inventory", "map", "board", "pause", "ability", "ability_records"):
                    self.scene = "world"
                elif self.scene == "dossier" and self.relation_return:
                    self.relation_return = False
                    self.scene = "relation"
                elif self.scene == "dossier" and self.sheet_return:
                    self.sheet_return = False
                    self.scene = "puzzle"
                elif self.scene in ("puzzle", "conclusion", "error", "dossier", "timeline", "relation", "comparison", "theory", "proof"):
                    self.scene = "board"
                elif self.scene == "instructions":
                    self.scene = "menu"
                elif self.scene == "intro":
                    self.scene = "board"
            elif self.scene == "world":
                if key == pygame.K_e:
                    self.interact()
                elif key in (pygame.K_i, pygame.K_TAB):
                    self.selection = 0
                    self.scene = "inventory"
                elif key == pygame.K_m:
                    self.scene = "map"
                elif key == pygame.K_j:
                    self.scene = "board"
            elif self.scene == "dialogue":
                if key == pygame.K_h:
                    self.open_ability()
                elif key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                    self.scene = "world"
            elif self.scene == "intro" and key == pygame.K_RETURN:
                self.scene = "board"
            elif self.scene == "puzzle":
                self.sheet_keyboard(key)

    def draw_world(self):
        self.screen.fill(s.BG)
        pygame.draw.rect(self.screen, s.PANEL_DARK, (0, 0, 1200, 76))
        pygame.draw.line(self.screen, s.EDGE, (0, 76), (1200, 76), 1)
        pygame.draw.rect(self.screen, s.RED, (25, 22, 5, 31), border_radius=2)
        self.bank.draw(self.screen, self.small)
        target = self.nearest()
        for person in self.characters:
            color = s.GREEN if person["name"] in self.talked else s.BLUE
            active = target and target[0] == "person" and target[1] is person
            self.character_art.draw_marker(self.screen, person["name"], person["pos"], color, active,
                                           investigated=person["name"] in self.talked)
            if active:
                self.draw_target_label(person["name"], person["pos"], color)
        for item in self.evidence + [self.computer]:
            if not self.abilities.visible(item.get("id")):
                continue
            item_id = item.get("id", "computer")
            collected = ("computer" in self.abilities.inspected if item_id == "computer"
                         else self.inventory.contains(item_id))
            active = target and target[0] in ("evidence", "computer") and target[1] is item
            self.item_art.draw_marker(self.screen, item_id, item["pos"], collected, active)
            if active:
                self.draw_target_label(item.get("object", "Registro"), item["pos"], s.GREEN if collected else s.GOLD)
        self.player.draw(self.screen)
        self.text("PROTOCOLO ZERO", 46, 19, 300, color=s.CYAN)
        self.text(f"INVESTIGAÇÃO / {self.score.points} PONTOS", 390, 28, 300, s.TEXT, small=True)
        progress = pygame.Rect(700, 18, 465, 38)
        pygame.draw.rect(self.screen, s.PANEL, progress, border_radius=7)
        pygame.draw.rect(self.screen, s.EDGE, progress, 1, border_radius=7)
        self.text(f"EVIDÊNCIAS  {len(self.inventory.ids)}/8", 718, 28, 150, s.GOLD, small=True)
        self.text(f"DEPOIMENTOS  {len(self.talked)}/7", 915, 28, 170, s.GREEN, small=True)
        prompt = "E • " + target[1].get("name", target[1].get("object", "")) if target else self.message
        pygame.draw.rect(self.screen, s.PANEL_DARK, (20, 678, 1160, 95), border_radius=10)
        pygame.draw.rect(self.screen, s.EDGE, (20, 678, 1160, 95), 1, border_radius=10)
        prompt_color = s.GREEN if target else s.TEXT
        self.text(prompt, 42, 694, 1115, prompt_color)
        self.text("WASD / setas  mover     E  interagir     I / Tab  evidências     M  mapa     J  mural     Esc  pausa",
                  42, 743, 1115, s.MUTED, small=True)

    def draw_target_label(self, label, position, color):
        text = self.small.render(label, True, s.TEXT)
        rect = text.get_rect(midbottom=(position[0], position[1] - 25))
        rect.inflate_ip(14, 8)
        rect.x = max(28, min(rect.x, self.screen.get_width() - rect.width - 28))
        pygame.draw.rect(self.screen, s.PANEL_DARK, rect, border_radius=5)
        pygame.draw.rect(self.screen, color, rect, 1, border_radius=5)
        self.screen.blit(text, text.get_rect(center=rect.center))

    def draw_inventory(self):
        self.title("Inventário de evidências", "Selecione uma pista para reler o laudo. Esc: voltar ao banco.")
        found = [item for item in self.evidence if self.inventory.contains(item["id"])]
        for index, item in enumerate(found):
            self.button(item["title"], (60, 130 + index * 65, 380, 55),
                        lambda i=index: setattr(self, "selection", i))
        if found:
            item = found[min(self.selection, len(found) - 1)]
            self.text(item["title"], 480, 145, 650, s.BLUE)
            end_y = self.text(item["text"], 480, 205, 640)
            self.item_art.draw(self.screen, item["id"], (690, end_y + 15, 180, 180))
        else:
            self.text("Nenhuma evidência coletada. Procure objetos e registros com marcação dourada nas salas.", y=150)
        self.button("Voltar ao banco", (880, 710, 260, 56), lambda: self.set_scene("world"))

    def begin_analysis(self):
        if len(self.inventory.ids) == len(self.evidence):
            self.analysis_done = True
            self.scene = "puzzle"

    def draw_map(self):
        """Exibe a planta visual do banco sem confundir localização com álibi."""
        self.screen.fill(s.BG)
        pygame.draw.rect(self.screen, s.PANEL, (0, 0, 1200, 92))
        pygame.draw.rect(self.screen, s.RED, (30, 29, 5, 35))
        self.text("MAPA OPERACIONAL", 52, 25, 430, s.TEXT)
        self.text("PROTOCOLO ZERO / PLANTA DE INVESTIGAÇÃO", 52, 61, 500, s.MUTED, small=True)
        self.button("Voltar ao banco", (990, 25, 170, 42), lambda: self.set_scene("world"))

        corridor = pygame.Rect(28, 354, 1144, 44)
        pygame.draw.rect(self.screen, (18, 47, 62), corridor, border_radius=8)
        pygame.draw.line(self.screen, (63, 193, 216), corridor.midleft, corridor.midright, 2)
        self.text("CORREDOR CENTRAL", 475, 365, 250, CYAN, small=True)

        current_room = None
        for index, room in enumerate(self.bank.rooms):
            if self.player.rect.colliderect(room):
                current_room = index

        for index, name in enumerate(ROOM_NAMES):
            column, row = index % 3, index // 3
            card = pygame.Rect(30 + column * 390, 112 + row * 285, 370, 252)
            current = index == current_room
            fill = (24, 47, 61) if current else (19, 29, 43)
            border = s.GREEN if current else (55, 76, 96)
            pygame.draw.rect(self.screen, fill, card, border_radius=8)
            art_rect = card.inflate(-4, -4)
            self.bank.art.draw(self.screen, index, art_rect, fill=True)
            pygame.draw.rect(self.screen, border, card, 2, border_radius=8)

            title = self.small.render(name, True, s.GREEN if current else s.TEXT)
            pygame.draw.rect(self.screen, (10, 18, 29),
                             (card.x + 12, card.y + 12, title.get_width() + 18, 27),
                             border_radius=4)
            self.screen.blit(title, (card.x + 20, card.y + 17))
            if current:
                self.ui_label("VOCÊ ESTÁ AQUI", card.right - 126, card.y + 18, s.GREEN, 112)

            people = [person["name"] for person in self.characters if person["room"] == index]
            room_evidence = []
            for item in self.evidence:
                item_room = min(range(len(self.bank.rooms)),
                                key=lambda room_index: pygame.Vector2(self.bank.rooms[room_index].center)
                                .distance_to(item["pos"]))
                if item_room == index and self.abilities.visible(item["id"]):
                    room_evidence.append(item)
            if index == min(range(len(self.bank.rooms)),
                            key=lambda room_index: pygame.Vector2(self.bank.rooms[room_index].center)
                            .distance_to(self.computer["pos"])):
                if self.abilities.visible("computer"):
                    room_evidence.append(self.computer)

            self.ui_label("PESSOAS", card.x + 220, card.y + 59, CYAN, 135)
            self.ui_label(", ".join(people) or "Nenhuma registrada", card.x + 220, card.y + 83, s.TEXT, 135)
            self.ui_label("REGISTROS", card.x + 220, card.y + 137, CYAN, 135)
            found = sum(1 for item in room_evidence
                        if item.get("id", "computer") in self.inventory.ids
                        or item.get("id", "computer") == "computer"
                        and "computer" in self.abilities.inspected)
            self.ui_label(f"{found}/{len(room_evidence)} consultados", card.x + 220, card.y + 161, s.GREEN if found else s.MUTED, 135)
            self.ui_label("Porta para o corredor " + ("abaixo" if index < 3 else "acima"),
                          card.x + 220, card.y + 202, s.MUTED, 135)

        self.ui_label("Legenda:", 36, 688, s.MUTED, 70)
        pygame.draw.rect(self.screen, s.GREEN, (112, 693, 12, 12), border_radius=3)
        self.ui_label("sala atual", 132, 687, s.TEXT, 100)
        pygame.draw.rect(self.screen, CYAN, (246, 693, 12, 12), border_radius=3)
        self.ui_label("sala e registros disponíveis", 266, 687, s.TEXT, 260)
        self.ui_label("A posição no mapa orienta a exploração; os horários e álibis devem ser verificados nos registros.",
                      36, 716, s.MUTED, 820)

    def draw(self):
        self.buttons = []
        if self.scene == "world":
            self.draw_world()
        elif self.scene == "menu":
            self.draw_case_menu()
        elif self.scene == "instructions":
            self.title("Como investigar")
            self.text("WASD ou setas: mover. E: interagir quando estiver perto.\n"
                      "Retratos azuis: personagens. Ícones e quadrados dourados: objetos e registros. Verde: já consultado.\n"
                      "I ou Tab: inventário. M: mapa. J: painel de investigação. Esc: voltar ou pausar.\n\n"
                      "No mural, arraste fichas e use Ligar fichas para conectar duas hipóteses. Use o catálogo lateral para consultar pessoas, itens, locais e pistas.\n"
                      "Clique em Explorar banco para entrar nas salas pelas portas do corredor. Reúna oito pistas e volte com J para resolver os desafios.\n\n"
                      "Na mesa de dedução, clique numa lacuna e escolha uma opção (1–4). Tab muda de campo; Enter verifica e continua após o resultado.\n"
                      "Símbolos: ¬ não; & e; | ou inclusivo; → se... então; ↔ se e somente se.\n\n"
                      "Nos diálogos, use H ou o botão para consultar a habilidade. Examine os objetos solicitados antes de ativá-la.\n"
                      "Salve pelo botão Salvar no mural ou pela pausa no banco. Carregue pelo menu ou pela pausa.", y=140)
            self.button("Voltar ao menu", (60, 710, 300, 56), lambda: self.set_scene("menu"))
        elif self.scene == "intro":
            self.title("Fase 1 / O incidente")
            mode = ("Demonstração acadêmica: caso fixo de Seu Antônio."
                    if self.demo_mode else "A solução é sorteada a cada nova investigação.")
            self.text(self.case["intro"] + "\n\n" + mode + " Leia os laudos desta partida; carregar preserva o mesmo caso.", y=180)
            self.button("Abrir investigação [Enter]", (60, 550, 440, 60), lambda: self.set_scene("board"))
        elif self.scene == "dialogue":
            self.title(self.dialogue_title)
            portrait = self.active_person and self.character_art.draw(
                self.screen, self.active_person, (60, 140, 280, 420))
            if not portrait and self.active_item:
                portrait = self.item_art.draw(self.screen, self.active_item, (60, 170, 280, 280))
            text_x = 380 if portrait else 60
            text_width = 760 if portrait else 1080
            self.text(self.dialogue_body, x=text_x, y=150, width=text_width)
            if self.active_person:
                ability = ABILITIES[self.active_person]
                self.text(ability["name"] + " — " + ability["description"],
                          x=text_x, y=520, width=text_width, color=s.BLUE)
                self.button("Consultar habilidade [H]", (60, 625, 500, 56), self.open_ability,
                            enabled=self.ability_available(self.active_person))
            self.button("Continuar [E / Enter]", (60, 710, 430, 56), lambda: self.set_scene("world"))
        elif self.scene == "ability":
            self.draw_ability()
        elif self.scene == "ability_records":
            self.draw_ability_records()
        elif self.scene == "inventory":
            self.draw_inventory()
        elif self.scene == "board":
            self.draw_board()
        elif self.scene == "relation":
            self.draw_relation()
        elif self.scene == "comparison":
            self.draw_comparison()
        elif self.scene == "theory":
            self.draw_theory()
        elif self.scene == "notes":
            self.draw_notes()
        elif self.scene == "dossier":
            self.draw_dossier()
        elif self.scene == "timeline":
            self.draw_timeline()
        elif self.scene == "puzzle":
            self.draw_puzzle()
        elif self.scene == "conclusion":
            self.draw_case_conclusion()
        elif self.scene == "map":
            self.draw_map()
        elif self.scene == "pause":
            self.title("Investigação pausada")
            self.button("Continuar", (60, 200, 450, 60), lambda: self.set_scene("world"))
            self.button("Menu inicial", (60, 280, 450, 60), lambda: self.set_scene("menu"))
            self.button("Sair do jogo", (60, 360, 450, 60), lambda: setattr(self, "running", False))
            self.button("Salvar progresso", (60, 440, 450, 60), self.save_game)
            self.button("Carregar partida salva", (60, 520, 450, 60), self.load_game)
            self.text(self.save_message, y=610)
        elif self.scene in ("error", "victory"):
            self.draw_result(self.scene == "victory")
        elif self.scene == "proof":
            self.draw_proof()

    def run(self):
        """Processa eventos continuamente, inclusive em diálogos, a até 60 FPS."""
        try:
            while self.running:
                dt = self.clock.tick(s.FPS) / 1000
                # Atualiza áreas clicáveis antes de processar eventos da cena atual.
                self.draw()
                for event in pygame.event.get():
                    previous_scene = self.scene
                    self.handle_event(event)
                    if self.scene != previous_scene:
                        self.draw()
                if self.scene == "world":
                    self.player.update(pygame.key.get_pressed(), dt, self.bank.walls)
                self.draw()
                pygame.display.flip()
        finally:
            pygame.quit()
