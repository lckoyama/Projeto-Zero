"""Pontuação e estatísticas, independentes do Pygame e reconstituídas por eventos."""
from copy import deepcopy


class Score:
    def __init__(self, evidence=(), solved=()):
        self.baseline = {"evidence": sorted(evidence), "solved": sorted(solved)}
        self.events = []
        self.points = 100
        self.evidence = set(evidence)
        self.solved = set(solved)
        self.attempts = {}
        self.hints = set()
        self.last_accusation = None
        self.correct = 0
        self.errors = 0
        self.hints_used = 0
        self.won = False
        self.outcome = None

    def find_evidence(self, key):
        if key in self.evidence:
            return False
        self.evidence.add(key)
        self.points += 10
        self.events.append(["evidence", key])
        return True

    def answer(self, key, correct):
        if key in self.solved:
            return False
        attempts = self.attempts.get(key, 0)
        self.attempts[key] = attempts + 1
        if correct:
            self.correct += 1
            self.solved.add(key)
            if attempts == 0:
                self.points += 20
        else:
            self.errors += 1
            self.points -= 10
        self.events.append(["answer", key, correct])
        return True

    def hint(self, key):
        # Uma dica por desafio; reler a mesma dica não cobra novamente.
        if key in self.hints or key in self.solved:
            return False
        self.hints.add(key)
        self.hints_used += 1
        self.points -= 5
        self.events.append(["hint", key])
        return True

    def accuse(self, choices, correct):
        signature = tuple(choices)
        self.outcome = "victory" if correct else "error"
        self.last_accusation = signature
        if correct:
            if not self.won:
                self.points += 50
                self.correct += 1
                self.won = True
        else:
            self.points -= 20
            self.errors += 1
        self.events.append(["accusation", list(choices), correct])
        return True

    def export(self):
        return {"baseline": deepcopy(self.baseline), "events": deepcopy(self.events), "outcome": self.outcome,
                "summary": {"points": self.points, "correct": self.correct,
                            "errors": self.errors, "hints_used": self.hints_used}}

    @classmethod
    def restore(cls, data, evidence_ids, challenge_ids, option_sizes, answer):
        if not isinstance(data, dict) or set(data) != {"baseline", "events", "outcome", "summary"}:
            raise ValueError("Estatísticas inválidas.")
        baseline = data["baseline"]
        if not isinstance(baseline, dict) or set(baseline) != {"evidence", "solved"}:
            raise ValueError("Progresso anterior inválido.")
        for field, allowed in (("evidence", evidence_ids), ("solved", challenge_ids)):
            values = baseline[field]
            if (not isinstance(values, list) or any(not isinstance(v, str) or v not in allowed for v in values)
                    or len(values) != len(set(values))):
                raise ValueError("Progresso anterior inválido.")
        events = data["events"]
        if not isinstance(events, list) or len(events) > 100000:
            raise ValueError("Histórico de pontuação inválido.")
        score = cls(baseline["evidence"], baseline["solved"])
        for event in events:
            if not isinstance(event, list) or not event:
                raise ValueError("Evento inválido.")
            kind = event[0]
            if kind == "evidence" and len(event) == 2 and isinstance(event[1], str) and event[1] in evidence_ids:
                accepted = score.find_evidence(event[1])
            elif kind in ("answer", "hint") and isinstance(event[1] if len(event) > 1 else None, str) and event[1] in challenge_ids:
                if kind == "answer" and len(event) == 3 and type(event[2]) is bool:
                    accepted = score.answer(event[1], event[2])
                elif kind == "hint" and len(event) == 2:
                    accepted = score.hint(event[1])
                else:
                    raise ValueError("Tentativa inválida.")
            elif kind == "accusation" and len(event) == 3:
                choices, correct = event[1:]
                if (not isinstance(choices, list) or len(choices) != len(option_sizes)
                        or any(type(n) is not int or not 0 <= n < size for n, size in zip(choices, option_sizes))
                        or type(correct) is not bool or correct != (choices == answer)):
                    raise ValueError("Acusação inválida.")
                accepted = score.accuse(choices, correct)
            else:
                raise ValueError("Evento de pontuação desconhecido.")
            if not accepted:
                raise ValueError("Evento de pontuação repetido.")
        if data["outcome"] not in (None, "victory", "error"):
            raise ValueError("Resultado inválido.")
        if data["outcome"] is not None and data["outcome"] != score.outcome:
            raise ValueError("Resultado sem acusação correspondente.")
        score.outcome = data["outcome"]
        summary = data["summary"]
        if (not isinstance(summary, dict) or any(type(value) is not int for value in summary.values())
                or summary != score.export()["summary"]):
            raise ValueError("Totais incompatíveis com o histórico de pontuação.")
        return score
