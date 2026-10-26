"""Editor local de anotações por ficha, com entrada Unicode e rolagem."""
import pygame
from game import settings as s
from game.notes import NOTE_LIMIT, NOTE_MARKS, text_rows

EDITOR = pygame.Rect(40, 280, 1120, 310)
LINE_HEIGHT = 27


class NotesUI:
    def open_notes(self):
        self.note_key = self.board_selected
        self.note_cursor = len(self.board.notes.get(self.note_key, {}).get("text", ""))
        self.note_scroll = 0
        self.note_select_all = False
        self.save_message = ""
        self.set_scene("notes")
        pygame.key.start_text_input()
        pygame.key.set_text_input_rect(EDITOR)
        self.follow_note_cursor()

    def current_note(self):
        return self.board.notes.get(self.note_key, {"text": "", "mark": "none"})

    def write_note(self, text=None, mark=None):
        note = dict(self.current_note())
        if text is not None:
            note["text"] = text
        if mark is not None:
            note["mark"] = mark
        if note["text"] or note["mark"] != "none":
            self.board.notes[self.note_key] = note
        else:
            self.board.notes.pop(self.note_key, None)
        self.save_message = "Alterações na partida. Use Salvar para gravar em disco."

    def note_layout(self):
        return text_rows(self.current_note()["text"], self.font, EDITOR.width - 32)

    def note_cursor_row(self):
        rows = self.note_layout()
        return max(i for i, (start, end) in enumerate(rows) if start <= self.note_cursor)

    def follow_note_cursor(self):
        row = self.note_cursor_row()
        visible = (EDITOR.height - 24) // LINE_HEIGHT
        self.note_scroll = max(0, min(self.note_scroll, row))
        if row >= self.note_scroll + visible:
            self.note_scroll = row - visible + 1

    def insert_note_text(self, text):
        text = "".join(c for c in text if ord(c) >= 32 or c == "\n")
        old = self.current_note()["text"]
        if self.note_select_all:
            old, self.note_cursor = "", 0
        text = text[:NOTE_LIMIT - len(old)]
        self.write_note(old[:self.note_cursor] + text + old[self.note_cursor:])
        self.note_cursor += len(text)
        self.note_select_all = False
        self.follow_note_cursor()

    def notes_event(self, event):
        if event.type == pygame.TEXTINPUT:
            self.insert_note_text(event.text)
            return True
        if event.type == pygame.MOUSEWHEEL:
            self.note_scroll = max(0, min(max(0, len(self.note_layout()) - 10), self.note_scroll - event.y))
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and EDITOR.collidepoint(event.pos):
            text = self.current_note()["text"]
            rows = self.note_layout()
            row = min(len(rows) - 1, self.note_scroll + max(0, (event.pos[1] - EDITOR.y - 12) // LINE_HEIGHT))
            start, end = rows[row]
            self.note_cursor = min(range(start, end + 1), key=lambda n: abs(self.font.size(text[start:n])[0] - (event.pos[0] - EDITOR.x - 16)))
            self.note_select_all = False
            return True
        if event.type != pygame.KEYDOWN:
            return False
        key = event.key
        ctrl = getattr(event, "mod", 0) & pygame.KMOD_CTRL
        text = self.current_note()["text"]
        if key == pygame.K_ESCAPE:
            self.set_scene("board")
        elif ctrl and key == pygame.K_s:
            self.save_game()
        elif ctrl and key == pygame.K_a:
            self.note_select_all = True
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.insert_note_text("\n")
        elif key in (pygame.K_BACKSPACE, pygame.K_DELETE):
            if self.note_select_all:
                self.write_note("")
                self.note_cursor = 0
            elif key == pygame.K_BACKSPACE and self.note_cursor:
                self.write_note(text[:self.note_cursor - 1] + text[self.note_cursor:])
                self.note_cursor -= 1
            elif key == pygame.K_DELETE:
                self.write_note(text[:self.note_cursor] + text[self.note_cursor + 1:])
            self.note_select_all = False
        elif key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_HOME, pygame.K_END, pygame.K_UP, pygame.K_DOWN):
            rows = self.note_layout()
            row = self.note_cursor_row()
            if key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.note_cursor = max(0, min(len(text), self.note_cursor + (1 if key == pygame.K_RIGHT else -1)))
            elif key == pygame.K_HOME:
                self.note_cursor = 0 if ctrl else rows[row][0]
            elif key == pygame.K_END:
                self.note_cursor = len(text) if ctrl else rows[row][1]
            else:
                target = max(0, min(len(rows) - 1, row + (1 if key == pygame.K_DOWN else -1)))
                self.note_cursor = min(rows[target][1], rows[target][0] + self.note_cursor - rows[row][0])
            self.note_select_all = False
        self.follow_note_cursor()
        return True

    def draw_notes(self):
        self.dossier_header("MURAL / ANOTAÇÕES PESSOAIS")
        self.ui_button("Voltar ao mural", (1000, 17, 175, 32), lambda: self.set_scene("board"))
        self.text(self.entry(self.note_key)[0], x=40, y=100, width=1120, color=s.CYAN)
        self.ui_label("Suas dúvidas e interpretações. Estas marcações não são provas nem avaliações automáticas do jogo.", 40, 150, s.MUTED, 1120)
        note = self.current_note()
        for index, (mark, label) in enumerate(NOTE_MARKS.items()):
            self.ui_button(label, (40 + index * 282, 202, 265, 40), lambda m=mark: self.write_note(mark=m), active=note["mark"] == mark)
        pygame.draw.rect(self.screen, (15, 24, 36), EDITOR, border_radius=5)
        pygame.draw.rect(self.screen, s.CYAN, EDITOR, 1, border_radius=5)
        rows = self.note_layout()
        clip = self.screen.get_clip()
        self.screen.set_clip(EDITOR.inflate(-20, -16))
        for index in range(self.note_scroll, min(len(rows), self.note_scroll + 10)):
            start, end = rows[index]
            y = EDITOR.y + 12 + (index - self.note_scroll) * LINE_HEIGHT
            line = note["text"][start:end]
            if self.note_select_all:
                pygame.draw.rect(self.screen, (35, 71, 91), (EDITOR.x + 16, y, max(5, self.font.size(line)[0]), LINE_HEIGHT))
            self.screen.blit(self.font.render(line, True, s.TEXT), (EDITOR.x + 16, y))
            if index == self.note_cursor_row() and pygame.time.get_ticks() % 1000 < 600:
                x = EDITOR.x + 16 + self.font.size(note["text"][start:self.note_cursor])[0]
                pygame.draw.line(self.screen, s.CYAN, (x, y), (x, y + 23), 2)
        self.screen.set_clip(clip)
        self.ui_label(f"{len(note['text'])}/{NOTE_LIMIT} caracteres • Enter: nova linha • Ctrl+A: selecionar tudo • Ctrl+S: salvar • Roda: rolar", 40, 610, s.MUTED, 1120)
        self.ui_label(self.save_message or "As notas permanecem ao voltar ao mural. O salvamento em disco é manual.", 40, 660, s.CYAN, 1120)
        self.ui_button("Salvar partida e notas", (40, 725, 300, 44), self.save_game, active=True)
