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
        self.correct, explanation = validate_sheet(self.puzzle_index, self.puzzles[self.puzzle_index], self.sheet_answers)
        self.feedback = ("Dedução validada. " if self.correct else "Revise sua dedução. ") + explanation

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
        self.ui_button("Voltar ao mural", (1000, 17, 175, 32), lambda: self.set_scene("board"))
        self.text(sheet["title"], x=25, y=84, width=1000, color=CYAN)
        self.ui_label(f"{self.puzzle_index}/8 resolvidos", 1020, 89, s.MUTED, 170)
        panels = [(24, 133, 334, 438), (374, 133, 468, 438), (858, 133, 318, 438)]
        for rect in panels:
            pygame.draw.rect(self.screen, (15, 24, 36), rect, border_radius=4)
            pygame.draw.rect(self.screen, EDGE, rect, 1, border_radius=4)
        self.ui_label("01 / PREMISSAS", 40, 151, CYAN, 300)
        self.ui_label("02 / COMPLETE O RACIOCÍNIO", 390, 151, CYAN, 435)
        self.ui_label("03 / BASE DA ANÁLISE", 874, 151, CYAN, 285)
        self.text(puzzle["context"], x=40, y=194, width=300, small=True)
        self.ui_label("CONDIÇÕES FORNECIDAS", 40, 442, CYAN, 300)
        if "premises" in puzzle:
            facts = "; ".join(format_expression(premise) for premise in puzzle["premises"])
        elif "values" in puzzle:
            facts = "; ".join(f"{name} = {format_expression(value)}" for name, value in puzzle["values"].items())
        else:
            facts = "Compare todas as valorações possíveis."
        self.ui_label(facts, 40, 478, s.TEXT, 300)
        self.ui_label(sheet["instruction"], 390, 193, s.TEXT, 435)
        count = len(sheet["fields"])
        field_y = 284 if count < 4 else 270
        for index, (label, choices) in enumerate(sheet["fields"]):
            y = field_y + index * 60
            self.ui_label(label, 392, y + 13, s.MUTED, 205)
            selection = self.sheet_answers[index]
            value = choices[selection][0] if selection is not None else "[ preencher ]"
            self.ui_button(value, (597, y, 225, 46), lambda i=index: self.select_sheet_field(i),
                           active=index == self.sheet_field, enabled=not self.feedback)
        if not self.feedback:
            self.ui_button("Verificar dedução [Enter]", (390, 512, 435, 40), self.check_sheet, active=True)
        else:
            self.ui_label("VALIDADO" if self.correct else "REVISÃO NECESSÁRIA", 392, 528,
                          s.GREEN if self.correct else s.RED, 430)
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
            self.ui_label("EXERCÍCIO FORMAL", 874, 200, s.MUTED, 285)
            self.ui_label(sheet["note"], 874, 243, s.TEXT, 285)
            self.ui_label("¬  negação\n∧  conjunção\n∨  disjunção inclusiva\n→  condicional\n↔  bicondicional", 874, 389, CYAN, 285)
        pygame.draw.rect(self.screen, (15, 24, 36), (24, 587, 1152, 189), border_radius=4)
        if self.feedback:
            self.ui_label("RESULTADO DA VERIFICAÇÃO", 42, 603, s.GREEN if self.correct else s.RED, 1080)
            self.ui_label(self.feedback, 42, 637, s.TEXT, 855)
            self.ui_button("Continuar [Enter]" if self.correct else "Revisar campos [Enter]",
                           (922, 710, 235, 44), self.next_puzzle, active=True)
        else:
            self.ui_label("BANCO DE OPÇÕES / " + sheet["fields"][self.sheet_field][0], 42, 606, CYAN, 1100)
            choices = sheet["fields"][self.sheet_field][1]
            for index, (label, _) in enumerate(choices):
                self.ui_button(f"{index + 1}. {label}", (42 + index * 279, 647, 265, 47),
                               lambda i=index: self.choose_sheet_token(i))
            self.ui_label("Clique no campo e depois na opção. Teclas 1–4: escolher / Tab: próximo campo / Enter: verificar.",
                          42, 733, s.MUTED, 1100)

    def open_sheet_source(self, key):
        self.sheet_return = True
        self.board_selected = "evidence:" + key
        self.set_scene("dossier")
