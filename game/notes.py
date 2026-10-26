"""Notas do jogador; nunca são tratadas como evidências ou veredictos."""
NOTE_LIMIT = 1000
NOTE_MARKS = {"none": "Sem marcação", "investigate": "Investigar", "suspect": "Suspeita", "discarded": "Descartada por mim"}


def restore_notes(value, allowed, collected):
    if not isinstance(value, dict):
        raise ValueError("Anotações inválidas.")
    restored = {}
    for key, note in value.items():
        if key not in allowed or (key.startswith("evidence:") and key.split(":", 1)[1] not in collected):
            raise ValueError("Anotação de ficha indisponível.")
        if not isinstance(note, dict) or set(note) != {"text", "mark"}:
            raise ValueError("Anotação inválida.")
        text, mark = note["text"], note["mark"]
        if (not isinstance(text, str) or len(text) > NOTE_LIMIT
                or any(ord(c) < 32 and c != "\n" for c in text)
                or not isinstance(mark, str) or mark not in NOTE_MARKS):
            raise ValueError("Conteúdo de anotação inválido.")
        restored[key] = dict(note)
    return restored


def text_rows(text, font, width):
    """Retorna intervalos do texto, preservando espaços, quebras e posição do cursor."""
    rows = []
    start = 0
    for index, char in enumerate(text):
        if char == "\n":
            rows.append((start, index))
            start = index + 1
        elif font.size(text[start:index + 1])[0] > width and index > start:
            rows.append((start, index))
            start = index
    rows.append((start, len(text)))
    return rows
