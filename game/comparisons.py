"""Comparações explícitas: uma fonte só avalia a afirmação que ela sustenta."""


def comparison_rules(case):
    # (Pessoa, trecho do depoimento, fonte) -> resultado e justificativa.
    rules = {
        (0, 0, "wifi"): ("confirms", "O registro associa o celular de Seu Antônio ao Wi-Fi durante a pausa na sala de lazer."),
        (1, 0, "usb"): ("confirms", "O laudo confirma o teste autorizado de Bianca às 20h20. Isso não atribui a ela outros usos do pendrive."),
        (2, 0, "access"): ("confirms", "O alerta registra 21h07 como horário da detecção. O início do incidente precisa de outra fonte."),
        (3, 0, "laptop"): ("confirms", "O registro confirma o uso do notebook na apresentação entre 19h50 e 20h30. A finalidade da reunião não exclui, sozinha, outros eventos."),
        (3, 0, "cameras"): ("confirms", "As câmeras corroboram a presença de Arthur na apresentação. Não revelam o conteúdo da tela."),
        (4, 0, "computer"): ("confirms", "O registro do computador confirma a consulta de relatórios às 20h45."),
        (5, 0, "laptop"): ("inconclusive", "O registro confirma a apresentação de Arthur, mas não comprova quem a organizou. A afirmação completa permanece sem confirmação."),
        (6, 0, "transmitter"): ("confirms", "O laudo registra a descoberta do aparelho às 21h15. Descoberta e início de operação são eventos diferentes."),
    }
    if case["revision"] >= 2:
        if case["id"] == "usb":
            rules[(5, 1, "usb")] = ("contradicts", "Jonas alega que era apenas manutenção. O roteiro recuperado manda apagar registros e cópias para impedir a auditoria, e sua sessão assinou a execução. Isso contradiz a finalidade declarada.")
            rules[(5, 1, "cameras")] = ("inconclusive", "As câmeras confirmam Jonas conectando o pendrive na TI às 20h30, mas não demonstram que era apenas manutenção. Compare com a análise do pendrive.")
        elif case["id"] == "extension":
            rules[(4, 0, "computer")] = ("confirms", "O registro de alterações confirma que Márcia aplicou um perfil antigo durante a consulta das 20h45 para corrigir o acesso.")
            rules[(4, 1, "computer")] = ("inconclusive", "O registro mostra a mudança de permissões, mas não demonstra, sozinho, o que Márcia sabia ou pretendia naquele momento.")
        elif case["id"] == "phishing":
            rules[(6, 0, "transmitter")] = ("contradicts", "Carlos diz que instalou apenas um medidor elétrico. A inspeção identifica transmissão de documentos e uma configuração para ocultar o envio. O horário coincide, mas a função declarada é contradita.")
            rules[(6, 0, "cameras")] = ("inconclusive", "As câmeras mostram Carlos instalando o aparelho às 20h20. Isso confirma a instalação, mas não sua alegação de que era um medidor elétrico.")
            rules[(6, 1, "transmitter")] = ("inconclusive", "A descoberta às 21h15 é confirmada, mas a ordem de serviço não autorizava o aparelho. A descoberta não justifica sua instalação.")
    return rules


def assess_comparison(case, person_index, line_index, source, talked, collected, inspected):
    """Não revela texto ou resultado de depoimentos e fontes ainda bloqueados."""
    person = case["characters"][person_index]
    if person["name"] not in talked:
        return "locked", "Converse com este personagem no banco para obter o depoimento."
    known = "computer" in inspected if source == "computer" else source in collected
    if not known:
        return "locked", "Obtenha a evidência ou examine o computador antes de comparar."
    if not 0 <= line_index < len(person["lines"]):
        return "inconclusive", "Selecione um trecho do depoimento."
    return comparison_rules(case).get((person_index, line_index, source),
        ("inconclusive", "Esta fonte não confirma nem contradiz este trecho. Isso não prova que o depoimento seja verdadeiro ou falso; procure uma evidência pertinente."))
