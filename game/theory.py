"""Hipótese completa e fontes necessárias para sustentar cada escolha."""


def empty_theory():
    return {"choices": [None] * 4, "sources": [[] for _ in range(4)], "submitted": False}


def restore_theory(value, options, collected, inspected):
    if value is None:
        return empty_theory()
    if not isinstance(value, dict) or set(value) != {"choices", "sources", "submitted"}:
        raise ValueError("Hipótese inválida.")
    if type(value["submitted"]) is not bool:
        raise ValueError("Estado da hipótese inválido.")
    choices, sources = value["choices"], value["sources"]
    if not isinstance(choices, list) or len(choices) != 4 or not isinstance(sources, list) or len(sources) != 4:
        raise ValueError("Campos da hipótese inválidos.")
    allowed = set(collected) | ({"computer"} if "computer" in inspected else set())
    for choice, row, pool in zip(choices, sources, options):
        if choice is not None and (type(choice) is not int or not 0 <= choice < len(pool)):
            raise ValueError("Escolha da hipótese inválida.")
        if not isinstance(row, list) or any(not isinstance(key, str) or key not in allowed for key in row):
            raise ValueError("Fonte da hipótese indisponível.")
        if len(row) != len(set(row)):
            raise ValueError("Fonte repetida na hipótese.")
    return {"choices": list(choices), "sources": [list(row) for row in sources], "submitted": value["submitted"]}


def required_sources(case):
    if case["id"] == "link":
        return [{"wifi", "browser"}, {"browser", "credentials"}, {"browser", "credentials"}, {"browser"}]
    if case["revision"] == 1:
        source = {"usb": "usb", "extension": "laptop", "phishing": "credentials"}[case["id"]]
        return [{source, "credentials"}, {source, "credentials"}, {source, "credentials"}, {source}]
    if case["id"] == "usb":
        return [{"usb", "cameras"}, {"usb", "credentials"}, {"usb"}, {"usb"}]
    if case["id"] == "extension":
        return [{"computer", "credentials"}, {"computer", "credentials"}, {"computer"}, {"computer"}]
    return [{"cameras", "transmitter"}, {"transmitter", "credentials"}, {"transmitter"}, {"transmitter"}]


def assess_theory(case, theory, collected, inspected):
    known = set(collected) | ({"computer"} if "computer" in inspected else set())
    results = []
    for index, required in enumerate(required_sources(case)):
        choice, sources = theory["choices"][index], set(theory["sources"][index])
        if choice is None or not sources:
            results.append(("pending", "Escolha uma opção e associe as fontes que a sustentam."))
        elif not sources <= known:
            results.append(("pending", "Uma fonte selecionada ainda não está disponível."))
        elif not required <= sources:
            results.append(("unsupported", "As fontes associadas não bastam para demonstrar este campo. Cruze os registros do evento com os laudos pertinentes."))
        elif choice != case["answer"][index]:
            results.append(("unsupported", "A escolha não corresponde ao que as fontes demonstram. Releia os registros e revise este campo."))
        else:
            results.append(("supported", "Escolha sustentada pelo conjunto de fontes associado. Isso não substitui a resolução dos desafios."))
    return results
