"""Habilidades e requisitos de investigação, independentes da interface."""
from game.puzzles import validate

ABILITIES = {
    "Seu Antônio": {
        "name": "Acesso Discreto", "room": 2,
        "description": "Revela pistas ocultas em áreas comuns durante a limpeza.",
        "requires": set(), "evidence": set(),
        "result": "Uma anotação de preservação indica um laudo do navegador entre os objetos da sala de lazer. O marcador oculto agora está visível. Localizar um registro não demonstra a causa do incidente.",
    },
    "Bianca": {
        "name": "Análise Digital", "room": 3,
        "description": "Libera a leitura de registros digitais após um desafio proposicional.",
        "requires": {"usb"}, "evidence": set(),
        "result": "Acesso de análise liberado para pendrive, navegador e terminal pericial. Volte aos equipamentos para coletar os laudos. A validação de acesso não determina quem iniciou o incidente.",
    },
    "Flávio": {
        "name": "Visão de Segurança", "room": 0,
        "description": "Consulta imagens para corroborar a localização e o horário de um registro.",
        "requires": {"cameras"}, "evidence": {"cameras"},
        "result": "Câmeras: Arthur está na reunião no escritório do diretor durante a apresentação de 19h50 a 20h30. Esse registro corrobora a reunião; não demonstra o conteúdo transmitido pelo notebook nem exclui sozinho outras hipóteses.",
    },
    "Arthur": {
        "name": "Conhecimento Bancário", "room": 1,
        "description": "Interpreta documentos e distingue apresentação institucional de atividade financeira.",
        "requires": {"laptop"}, "evidence": {"laptop"},
        "result": "O documento do notebook é uma apresentação institucional, não uma ordem de movimentação financeira. Regra de triagem: inconsistência documental ∨ divergência de finalidade exige revisão. A apresentação, por si só, não prova nem afasta um ataque; confronte-a com o laudo técnico.",
    },
    "Márcia": {
        "name": "Auditoria Financeira", "room": 5,
        "description": "Examina o registro financeiro e verifica inconsistências na interpretação da atividade.",
        "requires": {"computer"}, "evidence": set(),
        "result": "Registro auditado: consulta de relatórios no computador interno às 20h45. A anotação 'transferência financeira às 20h45' é incompatível com esse registro e deve ser rejeitada. Consulta não equivale a transferência. Os dados disponíveis não autorizam inventar valores ou transações.",
    },
    "Jonas": {
        "name": "Controle de Agenda", "room": 1,
        "description": "Compara uma hipótese de horário com o intervalo registrado da reunião.",
        "requires": {"laptop"}, "evidence": set(),
        "result": "Agenda: apresentação de Arthur entre 19h50 e 20h30. Compatibilidade de horário ↔ (horário ≥ 19h50 ∧ horário ≤ 20h30). Uma contradição com esse intervalo invalida a hipótese sobre a reunião, mas não estabelece culpa.",
    },
    "Carlos": {
        "name": "Inspeção Técnica", "room": 4,
        "description": "Examina o transmissor e fornece premissas técnicas para avaliar seu possível uso.",
        "requires": {"transmitter"}, "evidence": {"transmitter"},
        "result": "Inspeção do aparelho encontrado às 21h15: se transmitiu os dados do incidente (T), deixou a assinatura A. A assinatura não foi encontrada (¬A). Use T → A e ¬A para avaliar a hipótese. O horário da descoberta, sozinho, não exclui o equipamento.",
    },
}

DIGITAL_PUZZLE = {
    "title": "Análise Digital / autorização de leitura", "kind": "inference",
    "context": "R: o registro está preservado. A: a análise está autorizada. L: a leitura pode ser liberada. Premissas do procedimento: R, A e (R ∧ A) → L. Qual conclusão decorre dessas premissas?",
    "premises": ["R", "A", ("implies", ("and", "R", "A"), "L")],
    "options": [("¬L", ("not", "L")), ("L", "L"), ("¬R", ("not", "R"))],
    "explanation": "R e A permitem R ∧ A; com (R ∧ A) → L, Modus Ponens permite L. Isso libera a análise, não uma conclusão sobre a invasão.",
}

REQUIREMENT_NAMES = {
    "usb": "examinar o pendrive na sala de TI",
    "cameras": "examinar o arquivo de câmeras na segurança",
    "laptop": "examinar o notebook no escritório do diretor",
    "computer": "examinar o computador interno no RH",
    "transmitter": "examinar o transmissor na sala dos servidores",
}


class AbilitySystem:
    def __init__(self):
        self.inspected = set()
        self.used = set()
        self.records = {}

    def visible(self, evidence_id):
        """O laudo oculto só aparece após a busca na área comum."""
        return evidence_id != "browser" or "Seu Antônio" in self.used

    def lock_reason(self, evidence_id):
        if evidence_id in {"browser", "credentials", "usb"} and "Bianca" not in self.used:
            return "Leitura protegida. Examine o pendrive e peça a Análise Digital de Bianca na sala de TI."
        owner = {"cameras": "Flávio", "laptop": "Arthur", "transmitter": "Carlos"}.get(evidence_id)
        if owner and owner not in self.used:
            return f"Objeto examinado. Converse com {owner} e utilize {ABILITIES[owner]['name']} para obter o laudo."
        return ""

    def activate(self, name, room, nearby, inventory, choice=None):
        """Valida contexto, aplica a habilidade e registra um resultado único."""
        if name not in ABILITIES:
            return False, "Personagem sem habilidade cadastrada."
        ability = ABILITIES[name]
        if not nearby or room != ability["room"]:
            return False, "Aproxime-se do personagem na sala indicada para utilizar sua habilidade."
        missing = ability["requires"] - self.inspected
        if missing:
            return False, "Antes, você precisa " + "; ".join(REQUIREMENT_NAMES[key] for key in sorted(missing)) + "."
        if name in self.used:
            return False, "Habilidade já registrada no painel. " + self.records[name]
        detail = ""
        if name == "Bianca":
            if type(choice) is not int or not 0 <= choice < len(DIGITAL_PUZZLE["options"]):
                return False, "Escolha uma conclusão no desafio para liberar a análise."
            correct, detail = validate(DIGITAL_PUZZLE, choice)
            if not correct:
                return False, "Revise a inferência. " + detail
        if name == "Jonas":
            if choice not in ("20h20", "20h45"):
                return False, "Selecione uma hipótese de horário para comparar com a agenda."
            hour, minute = map(int, choice.split("h"))
            compatible = 19 * 60 + 50 <= hour * 60 + minute <= 20 * 60 + 30
            detail = (f"Hipótese examinada: apresentação às {choice}. "
                      + ("Compatível com o intervalo." if compatible else "Contradição com o intervalo.")
                      + " É uma hipótese de análise, não um novo depoimento.")
        self.used.add(name)
        self.records[name] = ability["result"] + (" " + detail if detail else "")
        for evidence_id in ability["evidence"]:
            inventory.collect(evidence_id)
        return True, self.records[name]
