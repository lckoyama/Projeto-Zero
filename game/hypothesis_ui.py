"""Escolha da relação e montagem da justificativa de uma ligação do mural."""
from game import settings as s
from game.deduction import format_expression
from game.evidence import EVIDENCE
from game.hypotheses import (RELATIONS, RULES, FORMULAS, TOPICS, available_topics,
                             empty_review, assess_review)
from game.investigation_ui import CYAN


class HypothesisUI:
    def open_relation(self, first, second):
        if first == second:
            self.board_message = "Escolha duas fichas diferentes."
            self.link_start = None
            return
        pair = tuple(sorted((first, second)))
        if pair not in self.board.links:
            self.board.connect(*pair)
        self.relation_pair = pair
        topics = available_topics(pair, self.inventory.ids)
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
        return assess_review(pair, self.board.reviews.get(pair), self.inventory.ids, self.talked)

    def draw_relation(self):
        pair = self.relation_pair
        review = self.board.reviews[pair]
        self.dossier_header("MURAL / VERIFICAR UMA RELAÇÃO")
        self.ui_button("Voltar ao mural", (1000, 17, 175, 32), lambda: self.set_scene("board"))
        self.entry_art(pair[0], (28, 83, 70, 80))
        self.entry_art(pair[1], (1100, 83, 70, 80))
        self.ui_label(self.entry(pair[0])[0] + "  /  " + self.entry(pair[1])[0], 120, 101, CYAN, 950)
        self.ui_label("Escolha uma afirmação e justifique a relação com uma evidência coletada.", 120, 134, s.MUTED, 950)
        topics = available_topics(pair, self.inventory.ids)
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
        topic = TOPICS[review["topic"]]
        self.ui_button("Afirmação: " + topic["title"] + "  >", (28, 181, 1144, 42),
                       lambda: self.cycle_relation_field("topic", topics))
        self.ui_label("RELAÇÃO E FONTE", 30, 246, CYAN, 350)
        self.ui_label("JUSTIFICATIVA LÓGICA", 416, 246, CYAN, 350)
        self.ui_label("DEFINIÇÕES E PREMISSAS", 814, 246, CYAN, 350)
        self.ui_label("Tipo de relação", 30, 287, s.MUTED, 350)
        self.ui_button(RELATIONS.get(review["relation"], "Selecionar relação") + "  >", (28, 314, 355, 42),
                       lambda: self.cycle_relation_field("relation", list(RELATIONS)))
        self.ui_label("Evidência que fundamenta a relação", 30, 383, s.MUTED, 350)
        evidence = [item for item in EVIDENCE if self.inventory.contains(item["id"])]
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
