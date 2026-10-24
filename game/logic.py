"""Motor lógico independente do Pygame.

Uma expressão é um nome ("P"), um booleano ou uma tupla:
("not", "P"), ("and", "P", "Q"), ("implies", "P", "Q").
"""
from itertools import product

ARITY = {"not": 1, "and": 2, "or": 2, "implies": 2, "iff": 2}


def variables(expression):
    """Retorna as variáveis e rejeita expressões malformadas."""
    if isinstance(expression, bool):
        return set()
    if isinstance(expression, str) and expression:
        return {expression}
    if not isinstance(expression, tuple) or not expression:
        raise ValueError("Expressão lógica inválida")
    operator, *operands = expression
    if operator not in ARITY or len(operands) != ARITY[operator]:
        raise ValueError("Conectivo ou quantidade de operandos inválidos")
    result = set()
    for operand in operands:
        result.update(variables(operand))
    return result


def evaluate(expression, values):
    """Avalia uma expressão com valores estritamente booleanos."""
    variables(expression)
    if isinstance(expression, bool):
        return expression
    if isinstance(expression, str):
        value = values[expression]
        if not isinstance(value, bool):
            raise ValueError("Proposições precisam de valores booleanos")
        return value
    operator, *operands = expression
    results = [evaluate(operand, values) for operand in operands]
    a = results[0]
    if operator == "not":
        return not a
    b = results[1]
    return {"and": a and b, "or": a or b,
            "implies": (not a) or b, "iff": a == b}[operator]


def assignments(names):
    """Gera todas as 2**n combinações em ordem V,V; V,F; F,V; F,F."""
    names = sorted(names)
    for values in product((True, False), repeat=len(names)):
        yield dict(zip(names, values))


def truth_table(expression):
    """Retorna pares (valoração, resultado) para todas as combinações."""
    return [(values, evaluate(expression, values))
            for values in assignments(variables(expression))]


def counterexamples(premises, conclusion):
    """Encontra premissas verdadeiras com conclusão falsa."""
    names = variables(conclusion)
    for premise in premises:
        names.update(variables(premise))
    return [values for values in assignments(names)
            if all(evaluate(premise, values) for premise in premises)
            and not evaluate(conclusion, values)]


def entails(premises, conclusion):
    """Testa consequência semântica por enumeração exaustiva."""
    return not counterexamples(premises, conclusion)


def equivalent(first, second):
    """Duas expressões são equivalentes se coincidem em todas as linhas."""
    return all(evaluate(first, values) == evaluate(second, values)
               for values in assignments(variables(first) | variables(second)))
