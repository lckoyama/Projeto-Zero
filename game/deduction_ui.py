"""Mesa de dedução com premissas, lacunas e fichas de evidência."""
import pygame

from game import settings as s
from game.deduction import SHEETS, format_expression, validate_sheet
from game.evidence import EVIDENCE
from game.investigation_ui import CYAN, EDGE
from game.puzzles import PUZZLES


class DeductionUI:
    def reset_sheet(self):
        self.sheet_answers = [None] * len(self.sheets[min(self.puzzle_index, len(self.sheets) - 1)]["fields"])
        self.sheet_field = 0
        self.sheet_source = 0
        self.sheet_drag_choice = None
        self.sheet_drag_pos = None

    def sheet_drag_event(self, event):
        if self.scene != "puzzle" or self.feedback:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, choice in getattr(self, "sheet_option_rects", []):
                if rect.collidepoint(event.pos):
                    self.sheet_drag_choice = choice
                    self.sheet_drag_pos = event.pos
                    return True
        elif event.type == pygame.MOUSEMOTION and self.sheet_drag_choice is not None:
            self.sheet_drag_pos = event.pos
            return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.sheet_drag_choice is not None:
                choice = self.sheet_drag_choice
                position = event.pos
                self.sheet_drag_choice = None
                self.sheet_drag_pos = None
                if any(rect.collidepoint(position) and option == choice
                       for rect, option in getattr(self, "sheet_option_rects", [])):
                    self.choose_sheet_token(choice)
                    return True
                for rect, field in getattr(self, "sheet_field_rects", []):
                    if rect.collidepoint(position):
                        self.select_sheet_field(field)
                        self.choose_sheet_token(choice)
                        break
                return True
        return False

    def select_sheet_field(self, index):
        if not self.feedback:
            self.sheet_field = index

    def choose_sheet_token(self, choice):
        if self.feedback:
            return
        sheet = self.sheets[self.puzzle_index]
        choices = sheet["fields"][self.sheet_field][1]
        if not 0 <= choice < len(choices):
            return
        self.sheet_answers[self.sheet_field] = choice
        # Avança à próxima lacuna; clicar num campo permite revisar a escolha.
        for index in range(self.sheet_field + 1, len(self.sheet_answers)):
            if self.sheet_answers[index] is None:
                self.sheet_field = index
                break

    def check_sheet(self):
        if self.feedback:
            return
        if None in self.sheet_answers:
            return
        self.correct, explanation = validate_sheet(self.puzzle_index, self.puzzles[self.puzzle_index], self.sheet_answers)
        self.score.answer(f"sheet:{self.puzzle_index}", self.correct)
        self.feedback = ("Dedução validada. " if self.correct else "Revise sua dedução. ") + explanation

    def request_hint(self):
        if self.feedback or self.puzzle_index >= len(self.puzzles):
            return
        self.score.hint(f"sheet:{self.puzzle_index}")

    def sheet_keyboard(self, key):
        if key == pygame.K_RETURN:
            if self.feedback:
                self.next_puzzle()
            else:
                self.check_sheet()
        elif pygame.K_1 <= key <= pygame.K_4:
            self.choose_sheet_token(key - pygame.K_1)
        elif key == pygame.K_TAB and not self.feedback:
            self.sheet_field = (self.sheet_field + 1) % len(self.sheet_answers)

    def draw_puzzle(self):
        puzzle, sheet = self.puzzles[self.puzzle_index], self.sheets[self.puzzle_index]
        self.dossier_header("MESA DE DEDUÇÃO / LÓGICA MATEMÁTICA")
        self.ui_button("Voltar ao banco", (1000, 17, 175, 32), lambda: self.set_scene("world"))
        self.text(sheet["title"], x=25, y=84, width=1000, color=CYAN)
        self.ui_label(f"DESAFIO {self.puzzle_index + 1} DE 8", 845, 87, CYAN, 150)
        self.ui_label(f"{self.score.points} PONTOS", 1030, 87, s.MUTED, 140)
        filled = len(self.sheet_answers) - self.sheet_answers.count(None)
        remaining = len(self.sheet_answers) - filled
        objective = ("OBJETIVO: revise o resultado e avance para o próximo desafio."
                     if self.feedback else
                     f"OBJETIVO: preencha {remaining} lacuna(s) e verifique a dedução.")
        objective_color = s.GREEN if self.feedback else s.GOLD
        pygame.draw.rect(self.screen, (48, 36, 22) if not self.feedback else (22, 52, 43),
                         (25, 119, 1150, 28), border_radius=5)
        pygame.draw.rect(self.screen, objective_color, (25, 119, 5, 28), border_radius=3)
        self.ui_label(objective, 42, 124, objective_color, 1100)
        panels = [(24, 151, 334, 430), (374, 151, 468, 430), (858, 151, 318, 430)]
        for rect in panels:
            pygame.draw.rect(self.screen, (15, 24, 36), rect, border_radius=4)
            pygame.draw.rect(self.screen, EDGE, rect, 1, border_radius=4)
        headers = (
            (24, 151, 334, "01 / PREMISSAS"),
            (374, 151, 468, "02 / COMPLETE O RACIOCÍNIO"),
            (858, 151, 318, "03 / BASE DA ANÁLISE"),
        )
        for x, y, width, label in headers:
            pygame.draw.rect(self.screen, (19, 53, 66), (x + 1, y + 1, width - 2, 39),
                             border_radius=4)
            pygame.draw.rect(self.screen, CYAN, (x + 1, y + 1, 4, 39), border_radius=2)
            self.ui_label(label, x + 16, y + 12, CYAN, width - 32)
        self.text(puzzle["context"], x=40, y=194, width=300, small=True)
        self.ui_label("CONDIÇÕES FORNECIDAS", 40, 442, CYAN, 300)
        if "premises" in puzzle:
            facts = "; ".join(format_expression(premise) for premise in puzzle["premises"])
        elif "values" in puzzle:
            facts = "; ".join(f"{name} = {format_expression(value)}" for name, value in puzzle["values"].items())
        else:
            facts = "Compare todas as valorações possíveis."
        self.ui_label(facts, 40, 478, s.TEXT, 300)
        self.ui_label("PREENCHA O RACIOCÍNIO", 390, 193, CYAN, 435)
        self.ui_label("Selecione uma lacuna e escolha uma resposta.",
                      390, 220, s.TEXT, 435)
        instruction_end = self.ui_label(sheet["instruction"], 390, 263, s.MUTED, 435)
        count = len(sheet["fields"])
        field_y = max(300, instruction_end + 8) if count < 4 else 286
        self.sheet_field_rects = []
        for index, (label, choices) in enumerate(sheet["fields"]):
            y = field_y + index * 60
            self.ui_label(label, 392, y + 13, s.MUTED, 205)
            selection = self.sheet_answers[index]
            value = choices[selection][0] if selection is not None else "[ preencher ]"
            field_rect = pygame.Rect(597, y, 225, 46)
            self.sheet_field_rects.append((field_rect, index))
            self.ui_button(value, (597, y, 225, 46), lambda i=index: self.select_sheet_field(i),
                           active=index == self.sheet_field, enabled=not self.feedback)
        ready = filled == len(self.sheet_answers)
        verify_y = min(512, field_y + count * 60 + 20)
        if not self.feedback:
            self.ui_button("Verificar dedução [Enter]" if ready else "Preencha todas as lacunas",
                           (390, verify_y, 435, 40), self.check_sheet, active=ready, enabled=ready)
        else:
            status_color = s.GREEN if self.correct else s.RED
            pygame.draw.rect(self.screen, (22, 52, 43) if self.correct else (58, 28, 35),
                             (390, verify_y - 10, 435, 62), border_radius=6)
            pygame.draw.rect(self.screen, status_color, (390, verify_y - 10, 5, 62), border_radius=2)
            self.ui_label("VALIDADO" if self.correct else "REVISÃO NECESSÁRIA", 408, verify_y + 2,
                          status_color, 400)
            self.ui_label("Leia o resultado abaixo para seguir.", 408, verify_y + 25, s.TEXT, 400)
        sources = sheet["sources"]
        if sources:
            for index in range(len(sources)):
                self.ui_button(str(index + 1), (875 + index * 50, 191, 40, 27),
                               lambda i=index: setattr(self, "sheet_source", i), active=index == self.sheet_source)
            key = sources[self.sheet_source]
            evidence = next(item for item in self.evidence if item["id"] == key)
            available = self.inventory.contains(key)
            if available:
                self.entry_art("evidence:" + key, (947, 230, 130, 105))
                self.ui_label(evidence["title"], 874, 352, CYAN, 285)
                self.ui_label(sheet["note"], 874, 395, s.TEXT, 285)
                self.ui_button("Ler laudo", (875, 519, 283, 33),
                               lambda: self.open_sheet_source(key))
            else:
                self.ui_label("Evidência ainda não coletada.", 875, 249, s.MUTED, 280)
        else:
            self.ui_label("APOIO", 874, 200, s.MUTED, 285)
            self.ui_label(sheet["note"], 874, 243, s.TEXT, 285)
            self.ui_label("¬  negação\n&  conjunção\n|  disjunção inclusiva\n→  condicional\n↔  bicondicional", 874, 389, CYAN, 285)
        hint_key = f"sheet:{self.puzzle_index}"
        if not self.feedback:
            self.ui_button("DICA  (-5 PTS)" if hint_key not in self.score.hints else "DICA CONSULTADA",
                           (40, 535, 300, 34), self.request_hint,
                           enabled=hint_key not in self.score.hints,
                           active=hint_key not in self.score.hints)
        pygame.draw.rect(self.screen, (15, 24, 36), (24, 587, 1152, 189), border_radius=4)
        pygame.draw.rect(self.screen, EDGE, (24, 587, 1152, 189), 1, border_radius=4)
        pygame.draw.rect(self.screen, (19, 53, 66), (25, 588, 1150, 38), border_radius=4)
        pygame.draw.rect(self.screen, CYAN, (25, 588, 5, 38), border_radius=2)
        if self.feedback:
            self.ui_label("RESULTADO DA VERIFICAÇÃO", 42, 600, s.GREEN if self.correct else s.RED, 1080)
            self.ui_label(self.feedback, 42, 637, s.TEXT, 855)
            self.ui_button("Continuar [Enter]" if self.correct else "Revisar campos [Enter]",
                           (922, 710, 235, 44), self.next_puzzle, active=True)
        else:
            self.ui_label(f"RESPOSTAS  •  {filled}/{len(self.sheet_answers)} LACUNAS PREENCHIDAS",
                          42, 600, CYAN, 1100)
            choices = sheet["fields"][self.sheet_field][1]
            columns = min(4, len(choices))
            gap = 12
            button_width = (1100 - gap * (columns - 1)) // columns
            for index, (label, _) in enumerate(choices):
                x = 42 + (index % columns) * (button_width + gap)
                y = 647 + (index // columns) * 47
                if index == 0:
                    self.sheet_option_rects = []
                self.sheet_option_rects.append((pygame.Rect(x, y, button_width, 47), index))
                self.ui_button(f"{index + 1}. {label}", (x, y, button_width, 47),
                               lambda i=index: self.choose_sheet_token(i))
            instruction = "Clique ou arraste uma resposta para a lacuna. Depois, verifique a dedução."
            if hint_key in self.score.hints:
                instruction = self.puzzles[self.puzzle_index].get(
                    "hint", "Revise as premissas e a regra indicada.")
            pygame.draw.rect(self.screen, (26, 34, 48), (42, 704, 1115, 43), border_radius=5)
            pygame.draw.rect(self.screen, s.GOLD if hint_key in self.score.hints else EDGE,
                             (42, 704, 1115, 43), 1, border_radius=5)
            self.ui_label(instruction, 58, 716, s.TEXT, 1080)
            if self.sheet_drag_choice is not None and self.sheet_drag_pos is not None:
                label = choices[self.sheet_drag_choice][0]
                ghost = self.small.render(label, True, s.TEXT)
                ghost_rect = ghost.get_rect(center=self.sheet_drag_pos)
                background = ghost_rect.inflate(24, 14)
                pygame.draw.rect(self.screen, s.PANEL_ALT, background, border_radius=5)
                pygame.draw.rect(self.screen, s.GOLD, background, 2, border_radius=5)
                self.screen.blit(ghost, ghost_rect)

    def open_sheet_source(self, key):
        self.sheet_return = True
        self.board_selected = "evidence:" + key
        self.set_scene("dossier")
