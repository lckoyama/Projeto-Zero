"""Cenas e loop de eventos. Nenhum diálogo interrompe o loop do Pygame."""
import pygame
from game import settings as s
from game.case_data import CHARACTERS, INTRO, SOLUTION, REASONING
from game.dialogue import draw_text
from game.evidence import EVIDENCE, COMPUTER
from game.inventory import Inventory
from game.map import BankMap, ROOM_NAMES
from game.player import Player
from game.puzzles import PUZZLES, validate
from game.abilities import ABILITIES, AbilitySystem
from game.ability_scenes import AbilityScenes


class Game(AbilityScenes):
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

    def reset(self):
        self.bank = BankMap()
        self.player = Player()
        self.inventory = Inventory()
        self.abilities = AbilitySystem()
        self.active_person = None
        self.record_person = "Seu Antônio"
        self.ability_feedback = ""
        self.ability_success = False
        self.save_message = ""
        self.talked = set()
        self.analysis_done = False
        self.puzzle_index = 0
        self.feedback = ""
        self.correct = False
        self.selection = 0
        self.accusation = [0, 0, 0, 0]
        self.message = "Explore o banco. Aproxime-se dos marcadores e pressione E."

    def start(self):
        self.reset()
        self.has_game = True
        self.scene = "intro"

    def text(self, text, x=60, y=100, width=1080, color=s.TEXT, small=False):
        return draw_text(self.screen, text, self.small if small else self.font, x, y, width, color)

    def title(self, title, subtitle=""):
        self.screen.fill(s.BG)
        pygame.draw.rect(self.screen, s.RED, (30, 40, 4, 36))
        self.screen.blit(self.heading.render(title, True, s.TEXT), (60, 36))
        if subtitle:
            self.text(subtitle, y=82, color=s.MUTED, small=True)

    def button(self, label, rect, action, enabled=True):
        rect = pygame.Rect(rect)
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        color = (39, 80, 111) if hovered and enabled else s.PANEL
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, s.BLUE if enabled else (61, 72, 87), rect, 1, border_radius=8)
        self.text(label, rect.x + 14, rect.y + 12, rect.width - 28,
                  s.TEXT if enabled else s.MUTED)
        if enabled:
            self.buttons.append((rect, action))

    def set_scene(self, scene):
        self.scene = scene

    def show_dialogue(self, title, body):
        self.active_person = None
        self.dialogue_title, self.dialogue_body = title, body
        self.scene = "dialogue"

    def nearest(self):
        targets = [("person", person) for person in CHARACTERS]
        targets += [("evidence", item) for item in EVIDENCE
                    if self.abilities.visible(item["id"])] + [("computer", COMPUTER)]
        nearby = [(pygame.Vector2(item["pos"]).distance_to(self.player.rect.center), kind, item)
                  for kind, item in targets]
        distance, kind, item = min(nearby, key=lambda entry: entry[0])
        return (kind, item) if distance <= 66 else None

    def interact(self):
        target = self.nearest()
        if not target:
            self.message = "Aproxime-se de uma pessoa (círculo) ou objeto (quadrado)."
            return
        kind, item = target
        if kind == "person":
            self.talked.add(item["name"])
            self.show_dialogue(item["name"], item["role"] + "\n" + item["skill"]
                               + "\n\n" + "\n\n".join(item["lines"]))
            self.active_person = item["name"]
        elif kind == "evidence":
            self.abilities.inspected.add(item["id"])
            reason = self.abilities.lock_reason(item["id"])
            if reason:
                self.show_dialogue(item["object"], reason)
                return
            new = self.inventory.collect(item["id"])
            self.show_dialogue(item["title"], item["text"] +
                               ("\n\nEvidência adicionada ao inventário." if new else "\n\nEvidência já coletada."))
        else:
            self.abilities.inspected.add("computer")
            self.show_dialogue(item["object"], item["text"])

    def answer(self, index):
        if self.feedback:
            return
        self.correct, explanation = validate(PUZZLES[self.puzzle_index], index)
        self.feedback = ("Resposta válida. " if self.correct else "Revise seu raciocínio. ") + explanation

    def next_puzzle(self):
        if self.correct:
            self.puzzle_index += 1
        self.feedback = ""
        self.correct = False
        if self.puzzle_index == len(PUZZLES):
            self.scene = "board"

    def change_choice(self, row):
        self.accusation[row] = (self.accusation[row] + 1) % len(self.final_options()[row])

    def final_options(self):
        return [[person["name"] for person in CHARACTERS],
                ["Link malicioso", "Falha na rede interna", "Pendrive", "Dispositivo transmissor"],
                ["Notebook externo", "Computador interno", "Celular conectado ao Wi-Fi", "Dispositivo transmissor", "Pendrive"],
                ["19h50", "20h20", "20h30", "20h35", "20h45", "21h07", "21h15"]]

    def submit(self):
        if self.analysis_done and self.puzzle_index == len(PUZZLES):
            self.scene = "victory" if self.accusation == [0, 0, 2, 3] else "error"

    def handle_event(self, event):
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
                elif self.scene in ("puzzle", "conclusion", "error"):
                    self.scene = "board"
                elif self.scene == "instructions":
                    self.scene = "menu"
                elif self.scene == "intro":
                    self.scene = "world"
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
                self.scene = "world"
            elif self.scene == "puzzle":
                if self.feedback and key == pygame.K_RETURN:
                    self.next_puzzle()
                elif pygame.K_1 <= key <= pygame.K_3:
                    index = key - pygame.K_1
                    if index < len(PUZZLES[self.puzzle_index]["options"]):
                        self.answer(index)

    def draw_world(self):
        self.screen.fill(s.BG)
        pygame.draw.rect(self.screen, s.RED, (16, 24, 4, 22))
        self.bank.draw(self.screen, self.small)
        for person in CHARACTERS:
            color = s.GREEN if person["name"] in self.talked else s.BLUE
            pygame.draw.circle(self.screen, color, person["pos"], 13)
            self.text(person["name"], person["pos"][0] - 42, person["pos"][1] + 19, 145, small=True)
        for item in EVIDENCE + [COMPUTER]:
            if not self.abilities.visible(item.get("id")):
                continue
            collected = self.inventory.contains(item.get("id"))
            color = s.GREEN if collected else (238, 181, 99)
            x, y = item["pos"]
            pygame.draw.rect(self.screen, color, (x - 10, y - 10, 20, 20), border_radius=3)
            if collected:
                pygame.draw.line(self.screen, s.BG, (x - 5, y), (x + 5, y), 2)
        self.player.draw(self.screen)
        self.text("PROTOCOLO ZERO", 30, 20, color=s.BLUE)
        self.text(f"FASE 2 / INVESTIGAÇÃO     Evidências: {len(self.inventory.ids)}/8     Depoimentos: {len(self.talked)}/7",
                  430, 23, 740, small=True)
        target = self.nearest()
        prompt = "E • " + target[1].get("name", target[1].get("object", "")) if target else self.message
        self.text(prompt, 30, 688, 1130, s.GREEN if target else s.TEXT)
        self.text("WASD / setas: mover     E: interagir     I / Tab: evidências     M: mapa     J: painel     Esc: pausa",
                  30, 752, 1140, s.MUTED, small=True)

    def draw_inventory(self):
        self.title("Inventário de evidências", "Selecione uma pista para reler o laudo. Esc: voltar ao banco.")
        found = [item for item in EVIDENCE if self.inventory.contains(item["id"])]
        for index, item in enumerate(found):
            self.button(item["title"], (60, 130 + index * 65, 380, 55),
                        lambda i=index: setattr(self, "selection", i))
        if found:
            item = found[min(self.selection, len(found) - 1)]
            self.text(item["title"], 480, 145, 650, s.BLUE)
            self.text(item["text"], 480, 205, 640)
        else:
            self.text("Nenhuma evidência coletada. Procure os quadrados dourados nas salas.", y=150)
        self.button("Voltar ao banco", (880, 710, 260, 56), lambda: self.set_scene("world"))

    def draw_board(self):
        self.title("Painel de investigação", "FASE 3 / ANÁLISE → FASE 4 / LÓGICA → FASE 5 / CONCLUSÃO")
        self.button(f"Habilidades: {len(self.abilities.used)}/7 • consultar registros", (60, 640, 600, 56),
                    lambda: self.set_scene("ability_records"))
        count = len(self.inventory.ids)
        self.text(f"Evidências reunidas: {count}/8  •  Desafios resolvidos: {self.puzzle_index}/{len(PUZZLES)}", y=130, color=s.BLUE)
        notes = [
            "Equipamentos / confronte pendrive, notebook e transmissor com suas análises técnicas.",
            "Cronologia / separe o horário do evento do horário de identificação do acesso indevido.",
            "Causalidade / só aceite o vínculo entre evento e credenciais sustentado pelo laudo.",
            "Pessoas / depoimentos e fichas ajudam a contextualizar; perfil pessoal não prova culpa.",
        ]
        y = 205
        for note in notes:
            y = self.text(note, y=y) + 22
        if count < 8:
            self.text("Explore o banco para desbloquear a análise. Pistas faltantes:", y=480, color=s.MUTED)
            self.text(", ".join(item["title"] for item in EVIDENCE if not self.inventory.contains(item["id"])), y=525, small=True)
        elif not self.analysis_done:
            self.button("Organizar laudos e iniciar dedução", (60, 560, 510, 60), self.begin_analysis)
        elif self.puzzle_index < len(PUZZLES):
            self.button("Continuar desafios de lógica", (60, 560, 510, 60), lambda: self.set_scene("puzzle"))
        else:
            self.text("Análise lógica concluída. Formule a reconstrução do incidente.", y=490, color=s.GREEN)
            self.button("Apresentar conclusão", (60, 560, 510, 60), lambda: self.set_scene("conclusion"))
        self.button("Voltar ao banco", (880, 710, 260, 56), lambda: self.set_scene("world"))

    def begin_analysis(self):
        if len(self.inventory.ids) == len(EVIDENCE):
            self.analysis_done = True
            self.scene = "puzzle"

    def draw_puzzle(self):
        puzzle = PUZZLES[self.puzzle_index]
        self.title(puzzle["title"], "FASE 4 / DEDUÇÃO   •   Escolha com o mouse ou teclas 1–3. Esc: painel.")
        self.text(puzzle["context"], y=135)
        for index, (label, _) in enumerate(puzzle["options"]):
            self.button(f"{index + 1}. {label}", (60, 300 + index * 65, 1080, 55),
                        lambda i=index: self.answer(i), enabled=not self.feedback)
        if self.feedback:
            self.text(self.feedback, y=515, color=s.GREEN if self.correct else s.RED)
            self.button("Continuar [Enter]" if self.correct else "Tentar novamente [Enter]",
                        (60, 710, 450, 56), self.next_puzzle)

    def draw_conclusion(self):
        self.title("Reconstrução do incidente", "FASE 5 / CONCLUSÃO   •   Clique nas opções para alternar. Esc: painel.")
        self.text("Identifique quem desencadeou o incidente, o método, o equipamento e o horário do evento.", y=140)
        labels = ["Pessoa envolvida", "Método", "Equipamento", "Horário do evento"]
        for row, options in enumerate(self.final_options()):
            self.text(labels[row], 60, 235 + row * 95, 280, s.MUTED)
            self.button(options[self.accusation[row]] + "   ›", (360, 220 + row * 95, 780, 65),
                        lambda r=row: self.change_choice(r))
        self.button("Validar reconstrução", (60, 680, 460, 60), self.submit)

    def draw(self):
        self.buttons = []
        if self.scene == "world":
            self.draw_world()
        elif self.scene == "menu":
            self.title("PROTOCOLO ZERO", "O MISTÉRIO DA INVASÃO BANCÁRIA")
            self.text("Uma invasão. Oito evidências. Uma conclusão que precisa de prova.", y=180, color=s.BLUE)
            self.text("Investigue o banco e use lógica matemática para reconstruir o incidente.", y=230)
            self.button("Começar nova investigação", (60, 340, 480, 60), self.start)
            self.button("Instruções", (60, 420, 480, 60), lambda: self.set_scene("instructions"))
            self.button("Sair", (60, 500, 480, 60), lambda: setattr(self, "running", False))
            if self.has_game:
                self.button("Retomar investigação", (60, 580, 480, 60), lambda: self.set_scene("world"))
            self.button("Carregar partida salva", (620, 340, 520, 60), self.load_game)
            self.text(self.save_message, 620, 430, 520, s.MUTED)
            self.text("Resolução de Problemas com Lógica Matemática • protótipo local", y=735, small=True, color=s.MUTED)
        elif self.scene == "instructions":
            self.title("Como investigar")
            self.text("WASD ou setas: mover. E: interagir quando estiver perto.\n"
                      "Círculos azuis: personagens. Quadrados dourados: objetos. Verde: já consultado.\n"
                      "I ou Tab: inventário. M: mapa. J: painel de investigação. Esc: voltar ou pausar.\n\n"
                      "Entre nas salas pelas portas voltadas ao corredor central. Reúna oito pistas e consulte os depoimentos. "
                      "No painel, organize os laudos e resolva os oito desafios. A conclusão exige todos os desafios corretos.\n\n"
                      "Nos desafios, use 1–3 ou clique. Leia a explicação e pressione Enter. Erros permitem nova tentativa.\n"
                      "Símbolos: ¬ não; ∧ e; ∨ ou inclusivo; → se... então; ↔ se e somente se.\n\n"
                      "Nos diálogos, use H ou o botão para consultar a habilidade. Examine os objetos solicitados antes de ativá-la.\n"
                      "Para salvar, pressione Esc no banco e escolha Salvar progresso. Carregue pelo menu ou pela pausa.", y=140)
            self.button("Voltar ao menu", (60, 710, 300, 56), lambda: self.set_scene("menu"))
        elif self.scene == "intro":
            self.title("Fase 1 / O incidente")
            self.text(INTRO, y=180)
            self.button("Entrar no banco [Enter]", (60, 550, 440, 60), lambda: self.set_scene("world"))
        elif self.scene == "dialogue":
            self.title(self.dialogue_title)
            self.text(self.dialogue_body, y=150)
            if self.active_person:
                ability = ABILITIES[self.active_person]
                self.text(ability["name"] + " — " + ability["description"], y=520, color=s.BLUE)
                self.button("Consultar habilidade [H]", (60, 625, 500, 56), self.open_ability)
            self.button("Continuar [E / Enter]", (60, 710, 430, 56), lambda: self.set_scene("world"))
        elif self.scene == "ability":
            self.draw_ability()
        elif self.scene == "ability_records":
            self.draw_ability_records()
        elif self.scene == "inventory":
            self.draw_inventory()
        elif self.scene == "board":
            self.draw_board()
        elif self.scene == "puzzle":
            self.draw_puzzle()
        elif self.scene == "conclusion":
            self.draw_conclusion()
        elif self.scene == "map":
            self.title("Mapa do banco", "As portas de todas as salas ficam voltadas ao corredor central. Esc: voltar.")
            for index, name in enumerate(ROOM_NAMES):
                x, y = 60 + index % 3 * 365, 150 + index // 3 * 270
                pygame.draw.rect(self.screen, s.PANEL, (x, y, 340, 210), border_radius=8)
                self.text(name, x + 20, y + 20, 300, s.BLUE)
                people = ", ".join(person["name"] for person in CHARACTERS if person["room"] == index)
                self.text(people, x + 20, y + 75, 300, small=True)
                self.text("Porta ↓" if index < 3 else "Porta ↑", x + 20, y + 155, 300, s.MUTED)
            self.text("CORREDOR CENTRAL / posição inicial do investigador", 300, 375, 800, s.GREEN, small=True)
            self.text("Posições para interação neste protótipo; não representam uma grade de álibis.", y=705, small=True, color=s.MUTED)
            self.button("Voltar", (930, 735, 210, 50), lambda: self.set_scene("world"))
        elif self.scene == "pause":
            self.title("Investigação pausada")
            self.button("Continuar", (60, 200, 450, 60), lambda: self.set_scene("world"))
            self.button("Menu inicial", (60, 280, 450, 60), lambda: self.set_scene("menu"))
            self.button("Sair do jogo", (60, 360, 450, 60), lambda: setattr(self, "running", False))
            self.button("Salvar progresso", (60, 440, 450, 60), self.save_game)
            self.button("Carregar partida salva", (60, 520, 450, 60), self.load_game)
            self.text(self.save_message, y=610)
        elif self.scene == "error":
            self.title("Hipótese ainda não sustentada")
            self.text("A combinação escolhida não corresponde ao conjunto dos laudos. Revise as evidências, "
                      "separe o evento inicial da detecção e considere o vínculo causal pericial. "
                      "Seu progresso nos desafios foi preservado.", y=180)
            self.button("Revisar conclusão", (60, 420, 460, 60), lambda: self.set_scene("conclusion"))
            self.button("Voltar às evidências", (60, 500, 460, 60), lambda: self.set_scene("inventory"))
        elif self.scene == "victory":
            self.title("Caso resolvido / raciocínio demonstrado", "PROTOCOLO ZERO • RECONSTRUÇÃO FINAL")
            y = self.text(SOLUTION, y=125, color=s.GREEN) + 20
            for index, step in enumerate(REASONING):
                y = self.text(f"{index + 1}. {step}", y=y, small=True) + 7
            self.button("Menu inicial", (60, 725, 300, 56), lambda: self.set_scene("menu"))

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
