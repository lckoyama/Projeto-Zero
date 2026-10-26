"""Leitura lado a lado de depoimentos e fontes obtidas na investigação."""
import pygame
from game import settings as s
from game.comparisons import assess_comparison


class ComparisonUI:
    def open_comparison(self):
        kind, identifier = self.board_selected.split(":", 1)
        self.comparison_person = int(identifier) if kind == "person" else 0
        self.comparison_line = 0
        sources = self.comparison_sources()
        self.comparison_source = identifier if identifier in sources else (sources[0] if sources else None)
        self.comparison_result = None
        self.set_scene("comparison")

    def comparison_sources(self):
        sources = [item["id"] for item in self.evidence if item["id"] in self.inventory.ids]
        if "computer" in self.abilities.inspected:
            sources.append("computer")
        return sources

    def change_comparison(self, field, delta):
        self.comparison_result = None
        if field == "person":
            self.comparison_person = (self.comparison_person + delta) % len(self.characters)
            self.comparison_line = 0
        elif field == "line":
            person = self.characters[self.comparison_person]
            self.comparison_line = (self.comparison_line + delta) % len(person["lines"])
        else:
            sources = self.comparison_sources()
            if sources:
                current = sources.index(self.comparison_source) if self.comparison_source in sources else 0
                self.comparison_source = sources[(current + delta) % len(sources)]

    def compare_statement(self):
        self.comparison_result = assess_comparison(self.case, self.comparison_person,
            self.comparison_line, self.comparison_source, self.talked, self.inventory.ids,
            self.abilities.inspected)

    def draw_comparison(self):
        self.dossier_header("DEPOIMENTOS / COMPARAR COM EVIDÊNCIAS")
        self.ui_button("Voltar ao mural", (1000, 17, 175, 32), lambda: self.set_scene("board"))
        self.ui_label("Escolha um trecho e uma fonte. A comparação avalia essa afirmação, não a culpa da pessoa.",
                      30, 91, s.MUTED, 1135)
        for rect in [(25, 130, 557, 395), (598, 130, 577, 395)]:
            pygame.draw.rect(self.screen, (15, 24, 36), rect, border_radius=5)
            pygame.draw.rect(self.screen, s.EDGE, rect, 1, border_radius=5)
        person = self.characters[self.comparison_person]
        heard = person["name"] in self.talked
        self.ui_label("01 / DEPOIMENTO", 42, 148, s.CYAN, 500)
        self.ui_button("<", (42, 184, 42, 34), lambda: self.change_comparison("person", -1))
        self.ui_label(person["name"], 100, 192, s.TEXT, 390)
        self.ui_button(">", (520, 184, 42, 34), lambda: self.change_comparison("person", 1))
        if heard:
            self.ui_label(f"Trecho {self.comparison_line + 1} de {len(person['lines'])}", 42, 245, s.MUTED, 500)
            self.text('“' + person["lines"][self.comparison_line] + '”', x=42, y=289, width=510)
            self.ui_button("Trecho anterior", (42, 470, 180, 34), lambda: self.change_comparison("line", -1))
            self.ui_button("Próximo trecho", (235, 470, 180, 34), lambda: self.change_comparison("line", 1))
        else:
            self.text("Depoimento ainda não coletado. Converse com este personagem no banco.",
                      x=42, y=289, width=510, color=s.MUTED)
        self.ui_label("02 / EVIDÊNCIA COLETADA", 615, 148, s.CYAN, 540)
        sources = self.comparison_sources()
        if self.comparison_source in sources:
            source = self.computer if self.comparison_source == "computer" else next(
                item for item in self.evidence if item["id"] == self.comparison_source)
            self.ui_button("<", (615, 184, 42, 34), lambda: self.change_comparison("source", -1))
            self.ui_label(source.get("title", source["object"]), 672, 192, s.TEXT, 420)
            self.ui_button(">", (1115, 184, 42, 34), lambda: self.change_comparison("source", 1))
            self.text(source["text"], x=615, y=245, width=535, small=True)
        else:
            self.text("Nenhuma fonte disponível. Colete pistas ou examine o computador interno no banco.",
                      x=615, y=289, width=535, color=s.MUTED)
        self.ui_button("Comparar trecho e evidência", (30, 545, 360, 42), self.compare_statement,
                       enabled=heard and self.comparison_source in sources, active=True)
        if self.comparison_result:
            status, explanation = self.comparison_result
            label, color = {"confirms": ("CONFIRMA O TRECHO", s.GREEN),
                            "contradicts": ("CONTRADIZ O TRECHO", s.RED),
                            "inconclusive": ("EVIDÊNCIA INSUFICIENTE", s.CYAN),
                            "locked": ("CONSULTA BLOQUEADA", s.MUTED)}[status]
            self.ui_label(label, 30, 612, color, 1100)
            self.text(explanation, x=30, y=647, width=1130, small=True)
        else:
            self.ui_label("O resultado aparece após comparar. Trocar o trecho ou a fonte inicia uma nova análise.",
                          30, 620, s.MUTED, 1130)
        self.ui_button("Explorar banco", (930, 737, 240, 40), lambda: self.set_scene("world"))
