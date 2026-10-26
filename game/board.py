"""Estado do mural: fichas, posições e ligações de hipóteses."""
from game.case_data import CHARACTERS
from game.evidence import EVIDENCE
from game.hypotheses import validate_review_shape, available_topics
import math
from game.notes import restore_notes

CANVAS = (230, 135, 740, 555)
BOARD_SPACE = (230, 135, 1200, 1400)
BOARD_FILTERS = ("all", "person", "item", "room", "evidence", "linked")
CARD_SIZE = (118, 155)
ITEM_IDS = ("wifi", "usb", "transmitter", "laptop", "computer")
ALL_KEYS = ({f"person:{i}" for i in range(len(CHARACTERS))}
            | {f"room:{i}" for i in range(6)}
            | {f"item:{key}" for key in ITEM_IDS}
            | {f"evidence:{item['id']}" for item in EVIDENCE})


class BoardState:
    def __init__(self):
        self.positions = {}
        self.links = set()
        self.reviews = {}
        self.notes = {}
        self.zoom = 1.0
        self.pan = [0.0, 0.0]
        self.filter = "all"
        for index in range(7):
            self.pin(f"person:{index}")
        self.arrange()

    def pin(self, key):
        """Uma ficha é fixada no máximo uma vez."""
        if key not in ALL_KEYS or key in self.positions:
            return False
        # Procura uma célula livre, inclusive após remoções ou arrastos manuais.
        for index in range(56):
            candidate = [250 + (index % 6) * 174, 174 + (index // 6) * 172]
            if candidate[1] + CARD_SIZE[1] > BOARD_SPACE[1] + BOARD_SPACE[3] - 8:
                break
            if all(candidate[0] + CARD_SIZE[0] + 8 <= x or x + CARD_SIZE[0] + 8 <= candidate[0]
                   or candidate[1] + CARD_SIZE[1] + 8 <= y or y + CARD_SIZE[1] + 8 <= candidate[1]
                   for x, y in self.positions.values()):
                self.positions[key] = candidate
                return True
        self.positions[key] = [250, 174]
        self.arrange()
        return True

    def move(self, key, position):
        if key in self.positions:
            x, y, width, height = BOARD_SPACE
            self.positions[key] = [max(x + 8, min(int(position[0]), x + width - CARD_SIZE[0] - 8)),
                                   max(y + 8, min(int(position[1]), y + height - CARD_SIZE[1] - 8))]

    def connect(self, first, second):
        """Alterna uma hipótese não direcionada; não afirma causalidade."""
        if first == second or first not in self.positions or second not in self.positions:
            return False
        pair = tuple(sorted((first, second)))
        if pair in self.links:
            self.links.remove(pair)
            self.reviews.pop(pair, None)
        else:
            self.links.add(pair)
        return True

    def remove(self, key):
        self.positions.pop(key, None)
        self.links = {pair for pair in self.links if key not in pair}
        self.reviews = {pair: review for pair, review in self.reviews.items() if pair in self.links}

    def clear_links(self):
        self.links.clear()
        self.reviews.clear()

    def arrange(self):
        keys = sorted(self.positions)
        columns = min(6, max(1, math.ceil(math.sqrt(len(keys) * 1.3))))
        for index, key in enumerate(keys):
            self.positions[key] = [250 + index % columns * 174, 174 + index // columns * 200]

    def export(self):
        return {"positions": {key: list(pos) for key, pos in self.positions.items()},
                "notes": {key: dict(note) for key, note in self.notes.items()},
                "view": {"zoom": self.zoom, "pan": list(self.pan), "filter": self.filter},
                "links": [list(pair) for pair in sorted(self.links)],
                "reviews": [{"pair": list(pair), "review": review} for pair, review in sorted(self.reviews.items())]}

    @classmethod
    def restore(cls, data, evidence, topics=None):
        """Valida o mural salvo; arquivos antigos recebem o mural inicial."""
        board = cls()
        if data is None:
            return board
        if not isinstance(data, dict) or not isinstance(data.get("positions"), dict):
            raise ValueError("Mural inválido.")
        board.notes = restore_notes(data.get("notes", {}), ALL_KEYS, evidence)
        view = data.get("view", {"zoom": 1.0, "pan": [0.0, 0.0], "filter": "all"})
        if not isinstance(view, dict) or set(view) != {"zoom", "pan", "filter"}:
            raise ValueError("Visualização do mural inválida.")
        zoom, pan = view["zoom"], view["pan"]
        if (type(zoom) not in (int, float) or not math.isfinite(zoom) or not 0.35 <= zoom <= 1.75
                or not isinstance(pan, list) or len(pan) != 2
                or any(type(n) not in (int, float) or not math.isfinite(n) or abs(n) > 5000 for n in pan)
                or view["filter"] not in BOARD_FILTERS):
            raise ValueError("Visualização do mural inválida.")
        board.zoom, board.pan, board.filter = zoom, list(pan), view["filter"]
        board.positions.clear()
        for key, position in data["positions"].items():
            if key not in ALL_KEYS or (key.startswith("evidence:") and key.split(":")[1] not in evidence):
                raise ValueError("Ficha desconhecida ou evidência não descoberta.")
            if not isinstance(position, list) or len(position) != 2 or any(type(n) is not int for n in position):
                raise ValueError("Posição de ficha inválida.")
            board.pin(key)
            board.move(key, position)
        links = data.get("links")
        if not isinstance(links, list) or len(links) > len(ALL_KEYS) ** 2:
            raise ValueError("Ligações inválidas.")
        for pair in links:
            if (not isinstance(pair, list) or len(pair) != 2
                    or any(not isinstance(key, str) or key not in board.positions for key in pair)
                    or pair[0] == pair[1]):
                raise ValueError("Ligação sem fichas correspondentes.")
            board.links.add(tuple(sorted(pair)))
        reviews = data.get("reviews", [])
        if not isinstance(reviews, list) or len(reviews) > len(board.links):
            raise ValueError("Justificativas inválidas.")
        for entry in reviews:
            if not isinstance(entry, dict) or set(entry) != {"pair", "review"}:
                raise ValueError("Justificativa inválida.")
            pair = entry["pair"]
            if not isinstance(pair, list) or len(pair) != 2 or any(not isinstance(key, str) for key in pair):
                raise ValueError("Ligação inválida na justificativa.")
            pair = tuple(sorted(pair))
            if pair not in board.links or pair in board.reviews:
                raise ValueError("Justificativa duplicada ou sem ligação.")
            review = entry["review"]
            validate_review_shape(review, topics)
            if review["evidence"] is not None and review["evidence"] not in evidence:
                raise ValueError("Justificativa usa evidência não coletada.")
            if review["topic"] is not None and review["topic"] not in available_topics(pair, evidence, topics):
                raise ValueError("Afirmação sem fontes disponíveis.")
            board.reviews[pair] = review
        return board
