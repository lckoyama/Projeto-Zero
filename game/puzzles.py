"""Exercícios cuja correção é calculada pelo motor, não por índice de gabarito."""
from game.logic import evaluate, truth_table, entails, equivalent, counterexamples

PUZZLES = [
    {"title": "01 / Proposição simples e negação", "kind": "value",
     "context": "P: o registro foi preservado. Nesta valoração, P = V. Avalie ¬P. Uma proposição simples recebe um valor; sua negação inverte esse valor.",
     "expression": ("not", "P"), "values": {"P": True},
     "options": [("Verdadeiro", True), ("Falso", False)],
     "explanation": "Como P é verdadeira, ¬P é falsa."},
    {"title": "02 / Conjunção e disjunção", "kind": "value",
     "context": "W: há conexão Wi-Fi (V). H: há histórico preservado (V). F: há falha interna (F). Avalie (W & H) | F. A disjunção é inclusiva.",
     "expression": ("or", ("and", "W", "H"), "F"),
     "values": {"W": True, "H": True, "F": False},
     "options": [("Verdadeiro", True), ("Falso", False)],
     "explanation": "W & H é V; V | F é V. A conjunção exige ambos; a disjunção exige ao menos um."},
    {"title": "03 / Tabela-verdade da condicional", "kind": "table",
     "context": "Calcule P → Q nas quatro linhas, nesta ordem: (P,Q) = (V,V), (V,F), (F,V), (F,F). Preencha o resultado de cada linha. A condicional material não prova, sozinha, causalidade.",
     "expression": ("implies", "P", "Q"),
     "options": [("V, F, V, V", [True, False, True, True]),
                 ("V, V, F, F", [True, True, False, False]),
                 ("V, F, F, V", [True, False, False, True])],
     "explanation": "P → Q só é falsa quando P é verdadeira e Q é falsa."},
    {"title": "04 / Bicondicional", "kind": "value",
     "context": "Em uma linha hipotética da tabela, P = F e Q = F. Qual é o valor de P ↔ Q? Esta linha é um exercício abstrato, não uma nova evidência do caso.",
     "expression": ("iff", "P", "Q"), "values": {"P": False, "Q": False},
     "options": [("Falso", False), ("Verdadeiro", True)],
     "explanation": "P ↔ Q é verdadeira quando os valores são iguais, inclusive quando ambos são falsos."},
    {"title": "05 / Equivalência lógica", "kind": "equivalence",
     "context": "Qual expressão é equivalente a ¬(P & Q) em TODAS as valorações? A verificação compara as tabelas completas.",
     "expression": ("not", ("and", "P", "Q")),
     "options": [("¬P & ¬Q", ("and", ("not", "P"), ("not", "Q"))),
                 ("¬P | ¬Q", ("or", ("not", "P"), ("not", "Q"))),
                 ("P | Q", ("or", "P", "Q"))],
     "explanation": "Lei de De Morgan: negar que ambas sejam verdadeiras equivale a afirmar que ao menos uma é falsa."},
    {"title": "06 / Modus Ponens", "kind": "inference",
     "context": "P: ocorreu o evento do link registrado no celular. Q: esse evento comprometeu credenciais. Histórico: P. Laudo pericial: P → Q. Qual conclusão decorre dessas premissas? O vínculo causal é dado pela perícia fictícia.",
     "premises": ["P", ("implies", "P", "Q")],
     "options": [("¬Q", ("not", "Q")), ("Q", "Q"), ("¬P", ("not", "P"))],
     "explanation": "Modus Ponens: de P e P → Q, segue Q. Nenhuma valoração torna as duas premissas verdadeiras e Q falsa."},
    {"title": "07 / Modus Tollens", "kind": "inference",
     "context": "T: este transmissor enviou os dados do incidente. A: sua assinatura está no registro. Premissas periciais: T → A; ¬A. Qual conclusão é válida?",
     "premises": [("implies", "T", "A"), ("not", "A")],
     "options": [("T", "T"), ("A", "A"), ("¬T", ("not", "T"))],
     "explanation": "Modus Tollens: de T → A e ¬A, segue ¬T. A conclusão depende da premissa pericial sobre a assinatura."},
    {"title": "08 / Evite afirmar o consequente", "kind": "validity",
     "context": "Use APENAS estas premissas abstratas: P → Q e Q. Podemos concluir P? Não use outras pistas. Teste se existe alguma linha em que as premissas sejam verdadeiras e P falsa.",
     "premises": [("implies", "P", "Q"), "Q"], "conclusion": "P",
     "options": [("Sim, P é consequência necessária", True),
                 ("Não, há um contraexemplo", False)],
     "explanation": "Com P = F e Q = V, as premissas são verdadeiras e a conclusão falsa. Afirmar o consequente é inválido; sequência temporal também não prova causa."},
]


def validate(puzzle, choice):
    """Calcula a resposta e produz feedback, incluindo contraexemplos."""
    candidate = puzzle["options"][choice][1]
    kind = puzzle["kind"]
    detail = ""
    if kind == "value":
        correct = candidate == evaluate(puzzle["expression"], puzzle["values"])
    elif kind == "table":
        rows = truth_table(puzzle["expression"])
        correct = candidate == [result for _, result in rows]
        detail = " Tabela calculada: " + "; ".join(
            ", ".join(f"{name}={'V' if value else 'F'}" for name, value in values.items())
            + " => " + ("V" if result else "F") for values, result in rows) + "."
    elif kind == "equivalence":
        correct = equivalent(puzzle["expression"], candidate)
    elif kind == "inference":
        correct = entails(puzzle["premises"], candidate)
        examples = counterexamples(puzzle["premises"], candidate)
        if examples:
            detail = " Contraexemplo: " + ", ".join(
                f"{name}={'V' if value else 'F'}" for name, value in examples[0].items()) + "."
    elif kind == "validity":
        correct = candidate == entails(puzzle["premises"], puzzle["conclusion"])
    else:
        raise ValueError("Tipo de desafio desconhecido")
    return correct, puzzle["explanation"] + detail
