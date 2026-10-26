"""Relações do mural sustentadas pelos laudos e pelo motor proposicional."""
from game.logic import entails, counterexamples
from game.deduction import format_expression, rule_applies

RELATIONS = {"time": "Confirma o horário", "contradiction": "Contradiz o depoimento",
             "support": "Confirma a afirmação", "used": "Usou o equipamento"}
FORMULAS = ["P", ("implies", "P", "Q"), "Q", ("not", "P"),
            ("not", "Q"), ("implies", "Q", "P"), ("implies", "P", ("not", "Q"))]
RULES = {"mp": "Modus Ponens", "mt": "Modus Tollens", "ac": "Afirmação do consequente"}


def report_topic(title, primary, keys, claim, timed=False, witness=None, requires=None):
    """Formaliza o uso de um registro pericial aceito no universo fictício do caso."""
    return {"title": title, "primary": primary, "keys": set(keys),
            "requires": set(requires or [primary]), "timed": timed, "witness": witness,
            "definitions": {"P": "O laudo indicado registra e corrobora a afirmação Q.", "Q": claim},
            "premises": ["P", ("implies", "P", "Q")], "claim": "Q",
            "source_note": "P → Q é a regra de aceitação deste registro pericial fictício. Ela não estabelece a causa da invasão."}


TOPICS = {
    "usb_time": report_topic("Uso autorizado do pendrive às 20h20", "usb",
        ["person:1", "item:usb", "evidence:usb"],
        "Bianca usou o pendrive em testes autorizados às 20h20.", True, "Bianca"),
    "meeting": report_topic("Notebook na apresentação de 19h50 a 20h30", "laptop",
        ["person:3", "item:laptop", "room:1", "evidence:laptop"],
        "Arthur usou o notebook na apresentação de 19h50 a 20h30.", True, "Arthur"),
    "camera_meeting": report_topic("Câmeras corroboram o registro da reunião", "cameras",
        ["person:3", "item:laptop", "room:1", "evidence:cameras", "evidence:laptop"],
        "Arthur estava na reunião durante a apresentação de 19h50 a 20h30.", True, "Arthur", ["cameras", "laptop"]),
    "wifi_connection": report_topic("Conexão do celular ao Wi-Fi", "wifi",
        ["person:0", "item:wifi", "room:2", "evidence:wifi"],
        "O celular de Seu Antônio estava conectado ao Wi-Fi durante a pausa na sala de lazer.", witness="Seu Antônio"),
    "browser_time": report_topic("Horário registrado no navegador", "browser",
        ["item:wifi", "evidence:browser"],
        "O histórico do celular registra a abertura do link às 20h35.", True),
    "detection": report_topic("Identificação do acesso indevido às 21h07", "access",
        ["person:2", "evidence:access"],
        "O banco identificou o acesso indevido às 21h07.", True, "Flávio"),
    "transmitter_found": report_topic("Descoberta do transmissor às 21h15", "transmitter",
        ["person:6", "item:transmitter", "evidence:transmitter"],
        "O transmissor foi encontrado às 21h15.", True, "Carlos"),
    "credentials": {
        "title": "Evento digital e comprometimento das credenciais", "primary": "credentials",
        "keys": {"item:wifi", "evidence:browser", "evidence:credentials"},
        "requires": {"browser", "credentials"}, "timed": False, "witness": None,
        "definitions": {"P": "Ocorreu o evento do link preservado no histórico.",
                        "Q": "Esse evento comprometeu credenciais."},
        "premises": ["P", ("implies", "P", "Q")], "claim": "Q",
        "source_note": "P vem do histórico; P → Q vem da correlação técnica do laudo. A proximidade de horários não é uma dessas premissas."},
    "transmitter_analysis": {
        "title": "Possível uso do transmissor neste incidente", "primary": "transmitter",
        "keys": {"person:6", "item:transmitter", "evidence:transmitter"},
        "requires": {"transmitter"}, "timed": False, "witness": None,
        "definitions": {"P": "Este transmissor enviou os dados do incidente.",
                        "Q": "A assinatura técnica deste aparelho está no registro."},
        "premises": [("implies", "P", "Q"), ("not", "Q")], "claim": ("not", "P"),
        "source_note": "O laudo fornece P → Q e ¬Q. A conclusão limita-se a este aparelho e a este incidente."},
}


def available_topics(pair, collected, topics=None):
    """Só apresenta afirmações cujas fontes já foram coletadas."""
    return [key for key, topic in (TOPICS if topics is None else topics).items()
            if set(pair) <= topic["keys"] and topic["requires"] <= set(collected)]


def empty_review(topic=None):
    return {"topic": topic, "relation": None, "evidence": None,
            "premises": [None, None], "conclusion": None, "rule": None, "submitted": False}


def validate_review_shape(review, topics=None):
    """Valida entradas salvas sem confiar em um selo de aprovação no arquivo."""
    if not isinstance(review, dict) or set(review) != set(empty_review()):
        raise ValueError("Estrutura de justificativa inválida.")
    if type(review["submitted"]) is not bool:
        raise ValueError("Estado de verificação inválido.")
    for name, allowed in [("topic", TOPICS if topics is None else topics), ("relation", RELATIONS), ("rule", RULES)]:
        value = review[name]
        if value is not None and (not isinstance(value, str) or value not in allowed):
            raise ValueError("Opção de justificativa desconhecida.")
    if review["evidence"] is not None and not isinstance(review["evidence"], str):
        raise ValueError("Evidência inválida.")
    if not isinstance(review["premises"], list) or len(review["premises"]) != 2:
        raise ValueError("Premissas inválidas.")
    for index in review["premises"] + [review["conclusion"]]:
        if index is not None and (type(index) is not int or not 0 <= index < len(FORMULAS)):
            raise ValueError("Fórmula desconhecida.")


def assess_review(pair, review, collected, talked, topics=None):
    """Verifica contexto, fontes, premissas, consequência e regra da relação."""
    if review is None:
        return "pending", "Escolha a relação, a evidência e a justificativa lógica."
    validate_review_shape(review, topics)
    if any(review[key] is None for key in ("topic", "relation", "evidence", "conclusion", "rule")) or None in review["premises"]:
        return "pending", "Preencha a relação, a evidência, duas premissas, a conclusão e a regra."
    if not review["submitted"]:
        return "pending", "Justificativa preenchida. Clique em Verificar relação para avaliá-la."
    topic = (TOPICS if topics is None else topics)[review["topic"]]
    if review["topic"] not in available_topics(pair, collected, topics):
        return "rejected", "As fichas ou as fontes disponíveis não sustentam esta afirmação."
    if review["evidence"] not in collected:
        return "rejected", "A evidência indicada ainda não foi coletada."
    if review["evidence"] != topic["primary"]:
        return "rejected", "A evidência escolhida não é o laudo que fundamenta esta relação."
    relation = review["relation"]
    if relation == "used" and (not topic.get("usage_pair") or set(pair) != set(topic["usage_pair"])):
        return "rejected", "Usou exige uma pessoa, um equipamento e um registro que comprove esse uso. Presença ou descoberta não bastam."
    if relation == "time" and not topic["timed"]:
        return "rejected", "Esta afirmação não confirma um horário. Conexão ou causalidade não equivalem a uma confirmação temporal."
    expected = topic["claim"]
    if relation == "contradiction":
        if not topic["witness"]:
            return "rejected", "Esta afirmação não corresponde a um depoimento que possa ser contradito."
        if topic["witness"] not in talked:
            return "rejected", "Ouça o depoimento antes de alegar uma contradição."
        expected = ("not", expected)
        if not entails(topic["premises"], expected):
            return "rejected", "O registro corrobora a declaração, não sua negação. Não há contradição demonstrada neste depoimento; diferenças entre horários de eventos distintos não bastam."
    premises = [FORMULAS[index] for index in review["premises"]]
    conclusion = FORMULAS[review["conclusion"]]
    if any(premise not in topic["premises"] for premise in premises):
        return "rejected", "Uma premissa escolhida não foi fornecida pela evidência. Uma dedução válida não autoriza inventar premissas."
    if conclusion != expected:
        return "rejected", "A conclusão escolhida não expressa a relação proposta. Use as definições de P e Q para reconstruí-la."
    examples = counterexamples(premises, conclusion)
    if examples:
        example = ", ".join(f"{key} = {format_expression(value)}" for key, value in examples[0].items())
        return "rejected", "As premissas não implicam a conclusão. Contraexemplo: " + example + "."
    if not rule_applies(premises, conclusion, review["rule"]):
        return "rejected", "A regra escolhida não justifica a passagem dessas premissas para a conclusão."
    return "verified", ("Relação verificada: " + RELATIONS[relation].lower() + ". "
        + "; ".join(format_expression(p) for p in premises) + " permitem " + format_expression(conclusion)
        + " por " + RULES[review["rule"]] + ". A verificação vale apenas para esta afirmação, não para a solução completa do mistério.")
