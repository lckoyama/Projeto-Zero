"""Persistência local em JSON, com validação antes de alterar a partida."""
import json
from pathlib import Path

from game.abilities import ABILITIES
from game.cases import build_case
from game.evidence import EVIDENCE
from game.puzzles import PUZZLES
from game.board import BoardState
from game.theory import restore_theory

SAVE_PATH = Path(__file__).resolve().parent.parent / "saves" / "progress.json"


def save_progress(game, path=SAVE_PATH):
    """Grava primeiro um temporário e substitui o arquivo apenas ao concluir."""
    path = Path(path)
    data = {
        "version": 1, "case_id": game.case_id, "case_revision": game.case["revision"], "evidence": sorted(game.inventory.ids),
        "talked": sorted(game.talked), "inspected": sorted(game.abilities.inspected),
        "used": sorted(game.abilities.used), "records": game.abilities.records,
        "analysis_done": game.analysis_done, "puzzle_index": game.puzzle_index,
        "position": list(game.player.rect.topleft), "accusation": game.accusation,
        "board": game.board.export(),
        "theory": game.theory,
    }
    temporary = path.with_suffix(".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _string_set(value, allowed):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError("Lista de progresso inválida.")
    if not set(value) <= allowed:
        raise ValueError("O arquivo contém registros desconhecidos.")
    return set(value)


def load_progress(game, path=SAVE_PATH):
    """Arquivos ausentes, inválidos ou incompatíveis preservam a partida atual."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("Versão de salvamento incompatível.")
    case = build_case(data.get("case_id", "link"), data.get("case_revision", 1))
    evidence_ids = {item["id"] for item in EVIDENCE}
    evidence = _string_set(data.get("evidence"), evidence_ids)
    talked = _string_set(data.get("talked"), set(ABILITIES))
    inspected = _string_set(data.get("inspected"), evidence_ids | {"computer"})
    used = _string_set(data.get("used"), set(ABILITIES))
    records = data.get("records")
    if not isinstance(records, dict) or set(records) != used or any(
            not isinstance(value, str) or len(value) > 2500 for value in records.values()):
        raise ValueError("Registros de habilidades inválidos.")
    for name in used:
        if not ABILITIES[name]["requires"] <= inspected or not ABILITIES[name]["evidence"] <= evidence:
            raise ValueError("Requisitos de habilidade inconsistentes.")
    if evidence & {"browser", "credentials", "usb"} and "Bianca" not in used:
        raise ValueError("Evidências digitais sem análise.")
    if "browser" in evidence and "Seu Antônio" not in used:
        raise ValueError("Pista oculta ainda não descoberta.")
    for item, name in [("cameras", "Flávio"), ("laptop", "Arthur"), ("transmitter", "Carlos")]:
        if item in evidence and name not in used:
            raise ValueError("Laudo sem habilidade correspondente.")
    index, analysis = data.get("puzzle_index"), data.get("analysis_done")
    if type(index) is not int or not 0 <= index <= len(PUZZLES) or type(analysis) is not bool:
        raise ValueError("Progressão inválida.")
    if (analysis and evidence != evidence_ids) or (index and not analysis):
        raise ValueError("Etapas de investigação inconsistentes.")
    position, accusation = data.get("position"), data.get("accusation")
    if not isinstance(position, list) or len(position) != 2 or any(type(n) is not int for n in position):
        raise ValueError("Posição inválida.")
    rect = game.player.rect.copy()
    rect.topleft = position
    if not (25 <= rect.left and rect.right <= 1175 and 90 <= rect.top and rect.bottom <= 655) or any(
            rect.colliderect(wall) for wall in game.bank.walls):
        raise ValueError("Posição fora da área acessível.")
    if not isinstance(accusation, list) or len(accusation) != 4 or any(
            type(n) is not int or not 0 <= n < len(options)
            for n, options in zip(accusation, game.final_options())):
        raise ValueError("Seleção de conclusão inválida.")
    board = BoardState.restore(data.get("board"), evidence, case["topics"])
    theory = restore_theory(data.get("theory"), game.final_options(), evidence, inspected)
    # Só modifica o jogo depois de validar todos os campos.
    game.reset(case["id"], case["revision"])
    game.inventory.ids, game.talked = evidence, talked
    game.abilities.inspected, game.abilities.used = inspected, used
    game.abilities.records = records
    game.analysis_done, game.puzzle_index = analysis, index
    game.reset_sheet()
    game.player.rect.topleft = position
    game.player.position.update(position)
    game.accusation = accusation
    game.board = board
    game.theory = theory
    game.has_game = True
    game.scene = "world"
