"""Coleção de evidências da partida, sem banco de dados."""
class Inventory:
    def __init__(self, on_collect=None):
        self.ids = set()
        self.on_collect = on_collect

    def collect(self, evidence_id):
        """Coleta uma vez e informa se a evidência era nova."""
        new = evidence_id not in self.ids
        self.ids.add(evidence_id)
        if new and self.on_collect:
            self.on_collect(evidence_id)
        return new

    def contains(self, evidence_id):
        return evidence_id in self.ids
