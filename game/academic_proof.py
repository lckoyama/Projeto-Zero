"""Provas auditáveis: premissas dos laudos, regras e verificação semântica."""
from game.logic import assignments, entails, equivalent, evaluate, variables
from game.deduction import format_expression, rule_applies


def _rename(expression, names):
    if isinstance(expression, str):
        return names.get(expression, expression)
    if isinstance(expression, tuple):
        return (expression[0], *(_rename(term, names) for term in expression[1:]))
    return expression


def proof_inputs(case):
    reports = {item["id"]: item for item in case["evidence"]}
    incident = case["topics"]["credentials"]
    excluded = "laptop" if case["revision"] >= 2 and case["id"] == "phishing" else "transmitter"
    device = "notebook" if excluded == "laptop" else "transmissor"
    definitions = {
        "A": incident["definitions"]["P"],
        "B": incident["definitions"]["Q"],
        "C": f"Este {device} transmitiu os dados do incidente.",
        "D": f"A assinatura deste {device} está no registro do incidente.",
        "E": "O celular de Seu Antônio estava conectado ao Wi-Fi na pausa.",
        "F": "O histórico registra a abertura do link do celular às 20h35.",
        "G": "O banco detectou o incidente às 21h07.",
        "H": "Bianca usou o pendrive em um teste autorizado às 20h20.",
        "I": "Arthur usou o notebook na apresentação de 19h50 a 20h30.",
        "J": "As câmeras corroboram a presença de Arthur na apresentação.",
    }
    # Cada premissa guarda o texto integral das fontes da partida atual.
    def premise(expression, sources, basis):
        return {"expression": expression, "sources": sorted(sources), "basis": basis,
                "quotes": {key: reports[key]["text"] for key in sorted(sources)}}

    premises = [
        premise(_rename(incident["premises"][0], {"P": "A", "Q": "B"}), incident["requires"],
                "Registro do evento, com as definições do tópico pericial do caso."),
        premise(_rename(incident["premises"][1], {"P": "A", "Q": "B"}), {"credentials"},
                "Correlação causal declarada no laudo; não decorre apenas do horário."),
        premise(_rename(case["puzzles"][6]["premises"][0], {"T": "C", "A": "D"}), {excluded},
                "Condição técnica da assinatura fornecida pelo laudo do equipamento."),
        premise(_rename(case["puzzles"][6]["premises"][1], {"T": "C", "A": "D"}), {excluded},
                "Ausência da assinatura no mesmo laudo."),
    ]
    for letter, source in (("E", "wifi"), ("F", "browser"), ("G", "access"),
                           ("H", "usb"), ("I", "laptop"), ("J", "cameras")):
        premises.append(premise(letter, {source}, "Fato registrado; não implica culpa nem causalidade isoladamente."))
    return definitions, premises


def build_proof(case):
    definitions, premises = proof_inputs(case)
    # Referências são índices de linhas: primeiro as dez premissas, depois etapas.
    steps = [
        {"expression": "B", "rule": "Modus Ponens", "refs": [0, 1]},
        {"expression": ("not", "C"), "rule": "Modus Tollens", "refs": [2, 3]},
        {"expression": ("and", "A", "B"), "rule": "Introdução da conjunção", "refs": [0, 10]},
        {"expression": ("not", ("or", ("not", "A"), ("not", "B"))),
         "rule": "De Morgan e dupla negação", "refs": [12]},
        {"expression": ("and", ("and", "A", "B"), ("not", "C")),
         "rule": "Introdução da conjunção", "refs": [12, 11]},
    ]
    return {"case_id": case["id"], "revision": case["revision"], "definitions": definitions,
            "premises": premises, "steps": steps, "conclusion": steps[-1]["expression"]}


def verify_proof(case, proof):
    """Rejeita premissas alteradas, contradições, regras falsas e referências futuras."""
    definitions, premises = proof_inputs(case)
    if (proof.get("case_id") != case["id"] or proof.get("revision") != case["revision"]
            or proof.get("definitions") != definitions or proof.get("premises") != premises):
        return False
    lines = [entry["expression"] for entry in premises]
    names = set().union(*(variables(line) for line in lines))
    if not any(all(evaluate(line, values) for line in lines) for values in assignments(names)):
        return False  # Não aceita prova por explosão a partir de premissas inconsistentes.
    for step in proof.get("steps", []):
        refs = step.get("refs")
        if (not isinstance(refs, list) or not refs
                or any(type(i) is not int or not 0 <= i < len(lines) for i in refs)):
            return False
        inputs = [lines[i] for i in refs]
        result, rule = step["expression"], step["rule"]
        if rule in ("Modus Ponens", "Modus Tollens"):
            valid = rule_applies(inputs, result, "mp" if rule == "Modus Ponens" else "mt")
        elif rule == "Introdução da conjunção":
            valid = len(inputs) == 2 and result == ("and", *inputs)
        elif rule == "De Morgan e dupla negação":
            original = inputs[0]
            valid = (len(inputs) == 1 and isinstance(original, tuple) and original[0] == "and"
                     and result == ("not", ("or", ("not", original[1]), ("not", original[2])))
                     and equivalent(original, result))
        else:
            return False
        if not valid or not entails(inputs, result):
            return False
        lines.append(result)
    return (bool(proof.get("steps")) and proof["conclusion"] == lines[-1]
            and entails([p["expression"] for p in premises], proof["conclusion"]))


def proof_text(case):
    proof = build_proof(case)
    if not verify_proof(case, proof):
        raise ValueError("A prova não passou na verificação lógica.")
    sections = [f"PROVA / {case['title']} / caso {case['id']} / revisão {case['revision']}\n"
                "Os registros são premissas da ficção pedagógica. A verificação testa a dedução, "
                "não autentica laudos reais. A resposta final exige cruzar pessoa, método, equipamento "
                "e horário nas fontes, não apenas descartar suspeitos."]
    definitions = list(proof["definitions"].items())
    for start in (0, 5):
        sections.append("DEZ PROPOSIÇÕES / A–J\n" + "\n".join(f"{k}: {v}" for k, v in definitions[start:start + 5]))
    sections.append("PREMISSAS INICIAIS\n" + "\n".join(
        f"{i + 1}. {format_expression(p['expression'])} / fontes: {', '.join(p['sources'])}"
        for i, p in enumerate(proof["premises"])))
    sections.append("ETAPAS INTERMEDIÁRIAS E CONCLUSÃO\n" + "\n".join(
        f"{i + 11}. {format_expression(step['expression'])} / {step['rule']} / linhas "
        + ", ".join(str(ref + 1) for ref in step["refs"]) for i, step in enumerate(proof["steps"]))
        + "\nVerificação: premissas satisfatíveis; zero contraexemplos para cada passo e para a conclusão.")
    sections.append("INTERPRETAÇÃO DA RECONSTRUÇÃO\n" + case["solution"] + "\n"
                    "A e B descrevem o evento e sua consequência pericial; ¬C exclui somente o equipamento "
                    "alternativo definido neste caso. E–J contextualizam e corroboram os registros. "
                    "Não se infere intenção ou culpa de profissão, presença ou sequência de horários.")
    for start in range(0, len(case["reasoning"]), 3):
        sections.append("LEITURA DAS EVIDÊNCIAS\n" + "\n".join(case["reasoning"][start:start + 3]))
    for i, entry in enumerate(proof["premises"]):
        sections.append(f"FONTE DA PREMISSA {i + 1}: {format_expression(entry['expression'])}\n"
                        + entry["basis"] + "\n" + "\n".join(f"{key}: {quote}" for key, quote in entry["quotes"].items()))
    return "\n\n".join(sections)
