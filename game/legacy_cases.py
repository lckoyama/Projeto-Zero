"""Variantes narrativas isoladas por partida; o sorteio ocorre ao começar."""
from copy import deepcopy
import random

from game.case_data import CHARACTERS, SOLUTION, REASONING
from game.evidence import EVIDENCE, COMPUTER
from game.puzzles import PUZZLES
from game.deduction import SHEETS
from game.hypotheses import TOPICS

CASE_IDS = ("link", "usb", "extension", "phishing")


def choose_case():
    return random.choice(CASE_IDS)


def build_case(case_id="link"):
    if not isinstance(case_id, str) or case_id not in CASE_IDS:
        raise ValueError("Caso desconhecido no salvamento.")
    case = dict(id=case_id, characters=deepcopy(CHARACTERS), evidence=deepcopy(EVIDENCE),
                computer=deepcopy(COMPUTER), puzzles=deepcopy(PUZZLES),
                sheets=deepcopy(SHEETS), topics=deepcopy(TOPICS),
                solution=SOLUTION, reasoning=list(REASONING), answer=[0, 0, 2, 3],
                title="O link na sala de lazer")
    if case_id == "link":
        return case
    reports = {item["id"]: item for item in case["evidence"]}
    reports["browser"]["text"] = (
        "O celular de Seu Antônio registra a abertura de um link às 20h35. "
        "Nesta investigação, o endereço é legítimo e a perícia excluiu o celular como vetor do incidente.")
    if case_id == "usb":
        title, answer, source, item = "O arquivo de teste adulterado", [1, 4, 4, 1], "usb", "usb"
        event = "Bianca executou um arquivo de teste adulterado do pendrive às 20h20"
        reports["usb"]["text"] = (
            "Bianca usou o pendrive às 20h20 em um teste autorizado. O registro confirma a execução "
            "de um arquivo adulterado por terceiros. A perícia encontrou o capturador de credenciais "
            "nesse arquivo; a autorização não garantia a segurança do conteúdo.")
    elif case_id == "extension":
        title, answer, source, item = "A extensão comprometida", [3, 5, 0, 0], "laptop", "laptop"
        event = "Arthur iniciou a apresentação no notebook com uma extensão maliciosa ativa às 19h50"
        reports["laptop"]["text"] = (
            "Arthur usou o notebook de 19h50 a 20h30 na apresentação institucional. Às 19h50, "
            "uma extensão maliciosa ativa capturou credenciais. O documento era legítimo; "
            "a análise identificou a extensão comprometida por terceiros como vetor do incidente.")
    else:
        title, answer, source, item = "A falsa autenticação", [4, 0, 1, 4], "credentials", "computer"
        event = "Márcia abriu um link malicioso e preencheu uma autenticação falsa no computador interno às 20h45"
        case["computer"]["text"] = (
            "Márcia consultou relatórios às 20h45. Durante a consulta, abriu um link e preencheu "
            "uma página falsa de autenticação. O terminal pericial preserva o registro desse evento. "
            "Não houve transferência financeira nem falha da rede interna.")
    reports["credentials"]["text"] = (
        f"Registro pericial: {event} (P). A correlação técnica identifica esse evento como a origem "
        "das credenciais capturadas. Premissa fictícia: se P, então esse evento comprometeu "
        "credenciais (Q). A auditoria exclui falha da rede interna e os demais equipamentos "
        "como vetores deste incidente.")
    person = case["characters"][answer[0]]["name"]
    case["characters"][answer[0]]["lines"].append(
        "Não percebi nada suspeito naquele momento. Os registros técnicos podem esclarecer o ocorrido.")
    case["title"], case["answer"] = title, answer
    case["solution"] = (
        f"{event}. A perícia vinculou esse evento à captura de credenciais, usadas por criminosos "
        f"externos no acesso identificado às 21h07. {person} desencadeou o incidente "
        "involuntariamente; não foi o autor intencional do ataque.")
    case["reasoning"] = [
        f"Evento inicial comprovado: {event}.",
        "O laudo correlaciona o evento à captura: P e P → Q permitem Q por Modus Ponens.",
        "O alerta vincula as credenciais capturadas ao acesso externo identificado às 21h07.",
        "O link do celular às 20h35 era legítimo; a perícia excluiu esse vetor.",
        "A assinatura do transmissor está ausente; Modus Tollens exclui esse aparelho.",
        "A auditoria excluiu falha interna e os demais equipamentos como vetores.",
        "Autorização, finalidade legítima e coincidência de horários não substituem perícia.",
    ]
    case["puzzles"][5]["context"] = (
        f"P: {event}. Q: esse evento comprometeu credenciais. Registro: P. "
        "Laudo: P → Q. Qual conclusão decorre dessas premissas?")
    case["sheets"][5]["sources"] = list(dict.fromkeys([source, "credentials"]))
    case["sheets"][5]["note"] = "O registro fornece P; a correlação pericial fornece P → Q."
    topic = case["topics"]["credentials"]
    topic["keys"] = {f"item:{item}", f"person:{answer[0]}", f"evidence:{source}", "evidence:credentials"}
    topic["requires"] = {source, "credentials"}
    topic["definitions"]["P"] = event + "."
    topic["source_note"] = "O registro do evento fornece P; a correlação técnica do laudo fornece P → Q."
    return case
