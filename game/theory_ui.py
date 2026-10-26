"""Pessoa → ação → equipamento → horário, com fontes por campo."""
import pygame
from game import settings as s
from game.theory import assess_theory


class TheoryUI:
    def open_theory(self):
        self.theory_field = 0
        self.theory_reading = None
        self.set_scene("theory")

    def theory_results(self):
        return assess_theory(self.case, self.theory, self.inventory.ids, self.abilities.inspected)

    def cycle_theory_choice(self, delta):
        index = self.theory_field
        old = self.theory["choices"][index]
        self.theory["choices"][index] = (0 if delta > 0 else len(self.final_options()[index]) - 1) if old is None else (old + delta) % len(self.final_options()[index])
        self.theory["submitted"] = False

    def toggle_theory_source(self, key):
        if key not in self.comparison_sources():
            return
        row = self.theory["sources"][self.theory_field]
        if key in row:
            row.remove(key)
        else:
            row.append(key)
        self.theory_reading = key
        self.theory["submitted"] = False

    def use_theory(self):
        if (all(status == "supported" for status, _ in self.theory_results())
                and self.analysis_done and self.puzzle_index == len(self.puzzles)):
            self.accusation = list(self.theory["choices"])
            self.set_scene("conclusion")

    def draw_theory(self):
        self.dossier_header("MURAL / RECONSTRUÇÃO")
        self.ui_button("Voltar ao mural", (1000, 17, 175, 32), lambda: self.set_scene("board"))
        self.ui_label("Selecione um campo, escolha sua hipótese e associe uma ou mais provas. Clique em Ler para consultar a fonte.", 25, 89, s.MUTED, 1150)
        labels = ["PESSOA", "AÇÃO", "EQUIPAMENTO", "HORÁRIO INICIAL"]
        results = self.theory_results()
        colors = {"pending": s.MUTED, "unsupported": s.RED, "supported": s.GREEN}
        names = {"pending": "Pendente", "unsupported": "Revisar fontes / escolha", "supported": "Sustentado"}
        for index, label in enumerate(labels):
            x = 25 + index * 295
            active = index == self.theory_field
            pygame.draw.rect(self.screen, (15, 24, 36), (x, 130, 265, 170), border_radius=5)
            pygame.draw.rect(self.screen, s.CYAN if active else s.EDGE, (x, 130, 265, 170), 2, border_radius=5)
            self.ui_button(label, (x + 8, 140, 249, 30), lambda i=index: setattr(self, "theory_field", i), active=active)
            choice = self.theory["choices"][index]
            self.ui_label(self.final_options()[index][choice] if choice is not None else "Escolher…", x + 12, 184, s.TEXT, 240)
            self.ui_label(names[results[index][0]], x + 12, 257, colors[results[index][0]], 240)
            if index < 3:
                self.ui_label("→", x + 273, 195, s.CYAN, 24)
        self.ui_button("< Opção anterior", (25, 315, 205, 36), lambda: self.cycle_theory_choice(-1))
        self.ui_button("Próxima opção >", (245, 315, 205, 36), lambda: self.cycle_theory_choice(1))
        self.ui_label("Editando: " + labels[self.theory_field], 475, 325, s.CYAN, 690)
        self.ui_label("PROVAS PARA ESTE CAMPO", 25, 374, s.CYAN, 510)
        sources = self.comparison_sources()
        for index, key in enumerate(sources):
            source = self.computer if key == "computer" else next(e for e in self.evidence if e["id"] == key)
            chosen = key in self.theory["sources"][self.theory_field]
            self.ui_button(("[x] " if chosen else "[ ] ") + source.get("title", source["object"]),
                (25, 405 + index * 30, 410, 27), lambda k=key: self.toggle_theory_source(k), active=chosen)
            self.ui_button("Ler", (445, 405 + index * 30, 65, 27), lambda k=key: setattr(self, "theory_reading", k))
        if not sources:
            self.text("Colete evidências no banco para fundamentar sua hipótese.", x=25, y=415, width=490, color=s.MUTED)
        if self.theory_reading in sources:
            source = self.computer if self.theory_reading == "computer" else next(e for e in self.evidence if e["id"] == self.theory_reading)
            self.ui_label(source.get("title", source["object"]), 545, 374, s.CYAN, 620)
            self.text(source["text"], x=545, y=410, width=620, small=True)
        else:
            self.ui_label("LEITURA DA FONTE", 545, 374, s.CYAN, 620)
            self.text("Escolha uma prova para consultar seu texto. Você pode usar a mesma fonte em vários campos e combinar fontes diferentes.", x=545, y=410, width=620, small=True)
        status, explanation = results[self.theory_field]
        self.ui_label(explanation, 545, 620, colors[status], 620)
        ready = all(status == "supported" for status, _ in results)
        finished = self.analysis_done and self.puzzle_index == len(self.puzzles)
        self.ui_button("Salvar", (265, 721, 105, 42), self.save_game)
        self.ui_button("Levar à conclusão", (895, 721, 280, 42), self.use_theory, enabled=ready and finished)
        self.ui_label(self.save_message or "A conclusão final exige as oito pistas e os oito desafios resolvidos.", 390, 733, s.MUTED, 485)
