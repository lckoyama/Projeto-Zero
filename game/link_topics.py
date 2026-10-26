"""Afirmações de uso e contradições apoiadas nos registros de cada história."""
from game.hypotheses import report_topic


def add_link_topics(case):
    topics = case["topics"]
    for key, person, item in [("usb_time", 1, "usb"), ("meeting", 3, "laptop"), ("wifi_connection", 0, "wifi")]:
        topics[key]["usage_pair"] = [f"person:{person}", f"item:{item}"]
    if case["revision"] < 2:
        return
    if case["id"] == "usb":
        person, item, source, name = 5, "usb", "usb", "Jonas"
        claim = "Jonas usou o pendrive na TI às 20h30."
        testimony = "O uso do pendrive por Jonas era apenas manutenção."
        fact = "O roteiro executado por Jonas apagava registros e cópias para impedir a auditoria."
    elif case["id"] == "phishing":
        person, item, source, name = 6, "transmitter", "transmitter", "Carlos"
        claim = "Carlos instalou e ativou o transmissor às 20h20."
        testimony = "O aparelho instalado por Carlos era apenas um medidor elétrico."
        fact = "A perícia identifica extração de documentos e configuração para ocultar o envio."
    elif case["id"] == "extension":
        topic = report_topic("Uso do computador às 20h45", "credentials",
            ["person:4", "item:computer", "evidence:credentials"],
            "Márcia aplicou um perfil de permissões pelo computador interno às 20h45.", True, "Márcia")
        topic["usage_pair"] = ["person:4", "item:computer"]
        topics["computer_use"] = topic
        return
    else:
        return
    pair = [f"person:{person}", f"item:{item}"]
    topic = report_topic("Uso registrado / " + name, source, pair + [f"evidence:{source}"], claim, True, name)
    topic["usage_pair"] = pair
    if case["id"] == "phishing":
        topic["requires"].add("cameras")
    topics["incident_use"] = topic
    topics["incident_contradiction"] = {
        "title": "Confronte a explicação de " + name, "primary": source,
        "keys": set(pair + [f"evidence:{source}"]), "requires": {source},
        "timed": False, "witness": name, "claim": "Q",
        "definitions": {"P": fact, "Q": testimony},
        "premises": ["P", ("implies", "P", ("not", "Q"))],
        "source_note": "O laudo fornece P e P → ¬Q. Por Modus Ponens, ¬Q contradiz a explicação dada no depoimento.",
    }
