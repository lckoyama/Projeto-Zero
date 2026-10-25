"""Folhas de dedução: campos preenchíveis e correção sem depender do Pygame."""
from game.logic import evaluate, truth_table, equivalent, entails, counterexamples

BOOL_CHOICES = [("Verdadeiro (V)", True), ("Falso (F)", False)]
TERMS = [("P", "P"), ("¬P", ("not", "P")), ("Q", "Q"), ("¬Q", ("not", "Q"))]
RULES = [("Modus Ponens", "mp"), ("Modus Tollens", "mt"),
         ("Afirmação do consequente", "ac")]

SHEETS = [
    {"title": "01 / Negação de uma proposição", "mode": "values",
     "instruction": "Complete o valor lógico da expressão.",
     "fields": [("¬P =", BOOL_CHOICES)], "expressions": [("not", "P")],
     "sources": [], "note": "Exercício de valoração. P é verdadeira nesta situação; isso não acrescenta um fato à história."},
    {"title": "02 / Combine os registros", "mode": "values",
     "instruction": "Resolva primeiro a conjunção e depois a expressão completa.",
     "fields": [("W ∧ H =", BOOL_CHOICES), ("(W ∧ H) ∨ F =", BOOL_CHOICES)],
     "expressions": [("and", "W", "H"), ("or", ("and", "W", "H"), "F")],
     "sources": ["wifi", "browser", "credentials"], "note": "A conexão e o histórico são informações distintas. A conclusão causal exige o laudo pericial."},
    {"title": "03 / Construa a tabela-verdade", "mode": "table",
     "instruction": "Preencha todas as células de P → Q. Não escolha uma coluna pronta.",
     "fields": [("P = V, Q = V", BOOL_CHOICES), ("P = V, Q = F", BOOL_CHOICES),
                ("P = F, Q = V", BOOL_CHOICES), ("P = F, Q = F", BOOL_CHOICES)],
     "sources": [], "note": "As quatro linhas são valorações possíveis. A condicional material não demonstra uma causa real."},
    {"title": "04 / Compare os valores", "mode": "values",
     "instruction": "Complete o resultado da bicondicional na valoração fornecida.",
     "fields": [("P ↔ Q =", BOOL_CHOICES)], "expressions": [("iff", "P", "Q")],
     "sources": [], "note": "Esta linha hipotética não é uma nova evidência. Avalie apenas os valores fornecidos."},
    {"title": "05 / Monte uma expressão equivalente", "mode": "equivalence",
     "instruction": "Preencha termo, conectivo e termo para obter uma expressão equivalente a ¬(P ∧ Q).",
     "fields": [("Primeiro termo", TERMS),
                ("Conectivo", [("∧", "and"), ("∨", "or"), ("→", "implies"), ("↔", "iff")]),
                ("Segundo termo", TERMS)],
     "sources": [], "note": "A expressão será comparada com ¬(P ∧ Q) em todas as quatro valorações. Mais de uma escrita equivalente pode ser aceita."},
    {"title": "06 / Do evento às credenciais", "mode": "inference",
     "instruction": "Complete a conclusão e identifique a regra que justifica esta passagem.",
     "fields": [("Logo, concluo", TERMS), ("Pela regra", RULES)],
     "sources": ["browser", "credentials"], "note": "O histórico fornece uma ocorrência. O vínculo entre evento e comprometimento é uma premissa do laudo."},
    {"title": "07 / Examine a hipótese do transmissor", "mode": "inference",
     "instruction": "Use a condição técnica e a ausência da assinatura para completar a inferência.",
     "fields": [("Logo, concluo", [("T", "T"), ("¬T", ("not", "T")), ("A", "A"), ("¬A", ("not", "A"))]),
                ("Pela regra", RULES)],
     "sources": ["transmitter"], "note": "A data da descoberta não exclui um aparelho. A análise depende das premissas técnicas sobre sua assinatura."},
    {"title": "08 / Encontre um contraexemplo", "mode": "counterexample",
     "instruction": "Preencha P e Q para tornar P → Q e Q verdadeiras, mas a conclusão P falsa.",
     "fields": [("Valor de P", BOOL_CHOICES), ("Valor de Q", BOOL_CHOICES)],
     "sources": [], "note": "Um único contraexemplo basta para refutar a validade de uma inferência. Não use outros fatos do caso nesta tarefa."},
]


def format_expression(expression):
    if type(expression) is bool:
        return "V" if expression else "F"
    if isinstance(expression, str):
        return expression
    operator, *terms = expression
    if operator == "not":
        return "¬" + format_expression(terms[0])
    symbol = {"and": "∧", "or": "∨", "implies": "→", "iff": "↔"}[operator]
    return f"({format_expression(terms[0])} {symbol} {format_expression(terms[1])})"


def rule_applies(premises, conclusion, rule):
    """Verifica a estrutura da regra, além da consequência semântica."""
    for premise in premises:
        if not isinstance(premise, tuple) or premise[0] != "implies":
            continue
        _, antecedent, consequent = premise
        if rule == "mp" and antecedent in premises and conclusion == consequent:
            return entails(premises, conclusion)
        if rule == "mt" and ("not", consequent) in premises and conclusion == ("not", antecedent):
            return entails(premises, conclusion)
    return False


def validate_sheet(index, puzzle, selections):
    """Corrige valores, expressões, regras e contraexemplos usando o motor."""
    sheet = SHEETS[index]
    if len(selections) != len(sheet["fields"]) or any(value is None for value in selections):
        return False, "Preencha todos os campos antes de verificar a dedução."
    answers = []
    for selected, (_, choices) in zip(selections, sheet["fields"]):
        if type(selected) is not int or not 0 <= selected < len(choices):
            return False, "Selecione uma das opções disponíveis para cada campo."
        answers.append(choices[selected][1])
    mode = sheet["mode"]
    detail = ""
    if mode == "values":
        expected = [evaluate(expression, puzzle["values"]) for expression in sheet["expressions"]]
        correct = answers == expected
        detail = " Resultados calculados: " + "; ".join(
            format_expression(expression) + " = " + format_expression(value)
            for expression, value in zip(sheet["expressions"], expected)) + "."
    elif mode == "table":
        expected = [value for _, value in truth_table(puzzle["expression"])]
        correct = answers == expected
        detail = " Coluna calculada, na ordem apresentada: " + ", ".join(format_expression(value) for value in expected) + "."
    elif mode == "equivalence":
        expression = (answers[1], answers[0], answers[2])
        correct = equivalent(puzzle["expression"], expression)
        detail = " Expressão montada: " + format_expression(expression) + "."
    elif mode == "inference":
        conclusion, rule = answers
        follows = entails(puzzle["premises"], conclusion)
        correct = follows and rule_applies(puzzle["premises"], conclusion, rule)
        if follows and not correct:
            detail = " A conclusão decorre das premissas, mas a regra escolhida não justifica essa passagem."
        examples = counterexamples(puzzle["premises"], conclusion)
        if examples:
            detail = " Contraexemplo: " + ", ".join(f"{name} = {format_expression(value)}" for name, value in examples[0].items()) + "."
    else:
        values = dict(zip(("P", "Q"), answers))
        premises_true = all(evaluate(premise, values) for premise in puzzle["premises"])
        conclusion_false = not evaluate(puzzle["conclusion"], values)
        correct = premises_true and conclusion_false
        detail = " Sua valoração: premissas " + ("todas verdadeiras" if premises_true else "não são todas verdadeiras")
        detail += "; conclusão " + ("falsa" if conclusion_false else "verdadeira") + "."
    return correct, puzzle["explanation"] + detail
