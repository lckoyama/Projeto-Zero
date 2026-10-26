"""Escolha da relação e montagem da justificativa de uma ligação do mural."""
import pygame
from game.board import CANVAS, CARD_SIZE
from game import settings as s
from game.deduction import format_expression
from game.evidence import EVIDENCE
from game.hypotheses import (RELATIONS, RULES, FORMULAS, TOPICS, available_topics,
                             empty_review, assess_review)
from game.investigation_ui import CYAN


class HypothesisUI:
    def link_labels(self):
        labels = []
        occupied = [self.board_card_rect(key).inflate(6, 6) for key in self.visible_board_keys()]
        bounds = pygame.Rect(CANVAS).inflate(-8, -8)
        for pair in self.visible_board_links():
            review = self.board.reviews.get(pair) or {}
            verb = {"time": "Confirma horário", "support": "Confirma", "contradiction": "Contradiz", "used": "Usou"}.get(review.get("relation"), "Justificar")
            status, _ = self.relation_status(pair)
            suffix = {"pending": "pendente", "rejected": "não comprovada", "verified": "verificada"}[status]
            label = verb + " · " + suffix
            width = self.small.size(label)[0] + 20
            a, b = (self.board_to_screen(pygame.Vector2(self.board.positions[key]) + (59, 3)) for key in pair)
            center = (a + b) / 2
            if not bounds.clipline(a, b):
                continue
            rect = pygame.Rect(0, 0, width, 28)
            rect.center = (round(center.x), round(center.y))
            rect.clamp_ip(bounds)
            # Procura espaço perto da linha sem cobrir fichas ou outros rótulos.
            for dy in (0, -32, 32, -64, 64, -96, 96, -128, 128):
                candidate = rect.move(0, dy)
                candidate.clamp_ip(bounds)
                if not any(candidate.colliderect(other) for other in occupied):
                    rect = candidate
                    break
            occupied.append(rect)
            labels.append((pair, label, status, rect, center))
        return labels

    def draw_link_labels(self):
        for pair, label, status, rect, center in self.link_labels():
            color = {"pending": s.MUTED, "rejected": s.RED, "verified": s.GREEN}[status]
            if not rect.collidepoint(center):
                pygame.draw.line(self.screen, color, center, rect.center, 1)
            pygame.draw.rect(self.screen, (12, 19, 32), rect, border_radius=5)
            pygame.draw.rect(self.screen, color, rect, 1, border_radius=5)
            self.screen.blit(self.small.render(label, True, color), (rect.x + 10, rect.y + 4))

    def open_relation(self, first, second):
        if first == second:
            self.board_message = "Escolha duas fichas diferentes."
            self.link_start = None
            return
        pair = tuple(sorted((first, second)))
        if pair not in self.board.links:
            self.board.connect(*pair)
        self.relation_pair = pair
        topics = available_topics(pair, self.inventory.ids, self.topics)
        if pair not in self.board.reviews:
            self.board.reviews[pair] = empty_review(topics[0] if topics else None)
        elif self.board.reviews[pair]["topic"] is None and topics:
            self.board.reviews[pair] = empty_review(topics[0])
        self.link_mode = False
        self.set_scene("relation")

    def cycle_relation_field(self, field, values, index=None):
        if not values:
            return
        review = self.board.reviews[self.relation_pair]
        previous = review[field] if index is None else review[field][index]
        next_value = values[(values.index(previous) + 1) % len(values)] if previous in values else values[0]
        if field == "topic":
            self.board.reviews[self.relation_pair] = empty_review(next_value)
        elif index is None:
            review[field] = next_value
            review["submitted"] = False
        else:
            review[field][index] = next_value
            review["submitted"] = False

    def verify_relation(self):
        self.board.reviews[self.relation_pair]["submitted"] = True

    def read_relation_source(self):
        evidence = self.board.reviews[self.relation_pair]["evidence"]
        if evidence in self.inventory.ids:
            self.relation_return = True
            self.board_selected = "evidence:" + evidence
            self.set_scene("dossier")

    def remove_relation(self):
        self.board.links.discard(self.relation_pair)
        self.board.reviews.pop(self.relation_pair, None)
        self.set_scene("board")

    def relation_status(self, pair):
        return assess_review(pair, self.board.reviews.get(pair), self.inventory.ids, self.talked, self.topics)

    def draw_relation(self):
        pair = self.relation_pair
        review = self.board.reviews[pair]
        self.dossier_header("MURAL / VERIFICAR UMA RELAÇÃO")
        self.ui_button("Voltar ao mural", (1000, 17, 175, 32), lambda: self.set_scene("board"))
        self.entry_art(pair[0], (28, 83, 70, 80))
        self.entry_art(pair[1], (1100, 83, 70, 80))
        self.ui_label(self.entry(pair[0])[0] + "  /  " + self.entry(pair[1])[0], 120, 101, CYAN, 950)
        self.ui_label("Escolha uma afirmação e justifique a relação com uma evidência coletada.", 120, 134, s.MUTED, 950)
        topics = available_topics(pair, self.inventory.ids, self.topics)
        if not topics:
            self.text("Ainda não há uma afirmação verificável disponível para estas fichas.", x=45, y=220, width=1100)
            self.text("Colete os laudos pertinentes ou escolha outra ligação. O jogo só oferece verificações "
                      "para relações modeladas a partir dos registros do caso. A ausência de uma verificação "
                      "não prova que duas fichas não tenham relação.", x=45, y=290, width=1070)
            self.text("Exemplo de uso: após obter o laudo do pendrive, ligue Bianca ao pendrive para avaliar "
                      "o horário registrado. Uma ligação entre personagens, sozinha, não demonstra culpa.",
                      x=45, y=410, width=1070, color=s.MUTED)
            self.ui_button("Retirar ligação", (45, 700, 240, 44), self.remove_relation)
            return
        topic = self.topics[review["topic"]]
        self.ui_button("Afirmação: " + topic["title"] + "  >", (28, 181, 1144, 42),
                       lambda: self.cycle_relation_field("topic", topics))
        self.ui_label("RELAÇÃO E FONTE", 30, 246, CYAN, 350)
        self.ui_label("JUSTIFICATIVA LÓGICA", 416, 246, CYAN, 350)
        self.ui_label("DEFINIÇÕES E PREMISSAS", 814, 246, CYAN, 350)
        self.ui_label("Tipo de relação", 30, 287, s.MUTED, 350)
        self.ui_button(RELATIONS.get(review["relation"], "Selecionar relação") + "  >", (28, 314, 355, 42),
                       lambda: self.cycle_relation_field("relation", list(RELATIONS)))
        self.ui_label("Evidência que fundamenta a relação", 30, 383, s.MUTED, 350)
        evidence = [item for item in self.evidence if self.inventory.contains(item["id"])]
        label = next((item["title"] for item in evidence if item["id"] == review["evidence"]), "Selecionar evidência")
        self.ui_button(label + "  >", (28, 412, 355, 42),
                       lambda: self.cycle_relation_field("evidence", [item["id"] for item in evidence]))
        self.ui_label("Clique nos campos para alternar. Consulte o laudo para conferir as informações usadas na justificativa.",
                      30, 478, s.MUTED, 350)
        self.ui_button("Consultar evidência", (28, 555, 355, 32), self.read_relation_source,
                       enabled=review["evidence"] in self.inventory.ids)
        fields = [("Premissa 1", "premises", 0), ("Premissa 2", "premises", 1),
                  ("Conclusão", "conclusion", None), ("Regra", "rule", None)]
        for row, (label, field, index) in enumerate(fields):
            y = 284 + row * 68
            self.ui_label(label, 416, y, s.MUTED, 350)
            value = review[field] if index is None else review[field][index]
            text = (RULES[value] if field == "rule" else format_expression(FORMULAS[value])) if value is not None else "Selecionar"
            choices = list(RULES) if field == "rule" else list(range(len(FORMULAS)))
            self.ui_button(text + "  >", (414, y + 24, 367, 36),
                           lambda f=field, v=choices, i=index: self.cycle_relation_field(f, v, i))
        y = 287
        for symbol, description in topic["definitions"].items():
            y = self.ui_label(symbol + ": " + description, 814, y, s.TEXT, 350) + 10
        y = self.ui_label("Disponíveis: " + "; ".join(format_expression(p) for p in topic["premises"]),
                          814, y + 5, CYAN, 350)
        self.ui_label(topic["source_note"], 814, y + 15, s.MUTED, 350)
        status, explanation = self.relation_status(pair)
        color = {"verified": s.GREEN, "rejected": s.RED, "pending": s.MUTED}[status]
        self.ui_label({"verified": "VERIFICADA", "rejected": "NÃO COMPROVADA", "pending": "PENDENTE"}[status], 30, 600, color, 1130)
        self.ui_label(explanation, 30, 633, color, 1130)
        self.ui_button("Verificar relação", (30, 733, 260, 44), self.verify_relation, active=True)
        self.ui_button("Retirar ligação", (310, 733, 230, 44), self.remove_relation)
        self.ui_button("Voltar ao mural", (930, 733, 240, 44), lambda: self.set_scene("board"))
