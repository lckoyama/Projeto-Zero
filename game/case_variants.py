"""Histórias atuais: acidente, sabotagem, falha interna e espionagem."""
from game.abilities import ABILITIES
from game.case_data import INTRO
from game.legacy_cases import build_case as legacy_case
from game.hypotheses import report_topic

CASE_REVISION = 2


def build_case(case_id="link", revision=CASE_REVISION):
    if type(revision) is not int or revision not in (1, CASE_REVISION):
        raise ValueError("Revisão narrativa desconhecida.")
    if not isinstance(case_id, str) or case_id not in ("link", "usb", "extension", "phishing"):
        raise ValueError("Caso desconhecido no salvamento.")
    case = legacy_case(case_id if revision == 1 else "link")
    case.update(id=case_id, revision=revision, intro=INTRO, timeline_extra=[],
                ability_results={name: ability["result"] for name, ability in ABILITIES.items()})
    if revision == 1:
        return case
    case["intro"] = (
        "Às 21h07, um alerta interrompeu a rotina do banco. Registros e documentos confidenciais "
        "podem ter sido afetados, mas a causa ainda é desconhecida. Sete pessoas estavam no local. "
        "Explore seis salas, reúna oito evidências e descubra o evento inicial. "
        "Um horário suspeito não basta: confronte depoimentos e laudos antes de concluir.")
    if case_id == "link":
        return case
    reports = {item["id"]: item for item in case["evidence"]}
    reports["browser"]["text"] = "O celular de Seu Antônio abriu um link às 20h35. O endereço era legítimo. A perícia excluiu esse celular como origem do incidente."
    reports["credentials"]["title"] = "03 • Laudo do incidente"
    if case_id == "usb":
        case.update(title="O apagamento planejado", answer=[5, 6, 4, 2])
        event = "Jonas executou deliberadamente uma rotina de apagamento pelo pendrive às 20h30"
        consequence = "a rotina apagou registros e interrompeu a auditoria"
        source, item = "usb", "usb"
        reports["usb"]["text"] = (
            "Bianca usou o pendrive às 20h20 com arquivos de teste autorizados e inofensivos. "
            "Às 20h30 houve um segundo uso, por Jonas: sua sessão assinou a execução de uma rotina "
            "de apagamento. O roteiro recuperado manda remover registros e suas cópias para impedir "
            "a auditoria. O conteúdo foi adicionado depois do teste de Bianca.")
        reports["cameras"]["text"] = (
            "As imagens corroboram Arthur na apresentação entre 19h50 e 20h30 e a pausa de Seu Antônio. "
            "Mostram Bianca deixando o pendrive após o teste das 20h20 e Jonas conectando-o "
            "ao terminal de TI às 20h30. As imagens não revelam o conteúdo executado.")
        case["characters"][5]["lines"] = ["Organizei a apresentação de Arthur, de 19h50 a 20h30.",
            "Depois levei o pendrive à TI para organizar os arquivos. Era apenas manutenção."]
        case["ability_results"]["Flávio"] += " As imagens também mostram Jonas com o pendrive na TI às 20h30."
        case["timeline_extra"] = [("usb", "20h30", "Segundo uso do pendrive", "Jonas conectou o dispositivo na TI; consulte a análise do conteúdo.")]
        case["solution"] = (
            "Jonas sabotou a auditoria: às 20h30, usou o pendrive para apagar registros e cópias. "
            "A alegação de manutenção foi desmentida pelo roteiro recuperado e pela execução assinada. "
            "Bianca havia usado o dispositivo dez minutos antes, ainda sem a rotina destrutiva. "
            "O alerta das 21h07 detectou a perda de integridade. Não houve roubo de credenciais.")
    elif case_id == "extension":
        case.update(title="A porta deixada aberta", answer=[4, 1, 1, 4])
        event = "Márcia aplicou um perfil incorreto de permissões pelo computador interno às 20h45"
        consequence = "a configuração expôs os relatórios sem exigir autenticação"
        source, item = "credentials", "computer"
        case["computer"]["text"] = (
            "Às 20h45, Márcia consultou relatórios e aplicou um perfil antigo para corrigir um erro de acesso. "
            "O perfil desativava a autenticação no compartilhamento. O registro de alterações "
            "identifica a sessão e preserva a configuração anterior. Não houve transferência financeira.")
        case["characters"][4]["lines"] = ["Os relatórios não abriam. Às 20h45 apliquei um perfil antigo que já havia funcionado.",
            "Achei que estava restaurando meu acesso. Não sabia que ele liberava o compartilhamento."]
        case["ability_results"]["Márcia"] = (
            "A auditoria confirma a consulta e a aplicação de um perfil antigo às 20h45. "
            "A mudança expôs relatórios sem autenticação; não houve transferência financeira. "
            "O histórico de suporte corrobora a tentativa de corrigir o acesso, sem indício de sabotagem.")
        case["puzzles"][1]["values"]["F"] = True
        case["puzzles"][1]["context"] = "W: há conexão Wi-Fi (V). H: há histórico preservado (V). F: há falha interna (V). Avalie (W & H) | F. A disjunção é inclusiva."
        case["puzzles"][1]["explanation"] = "W & H é V; V | V é V. Os registros confirmam a falha de configuração."
        case["solution"] = (
            "Márcia tentou corrigir o acesso aos relatórios às 20h45, mas aplicou um perfil antigo "
            "que desativava a autenticação. Terceiros consultaram o compartilhamento exposto. "
            "O alerta das 21h07 revelou a falha da rede interna. Não houve link malicioso nem "
            "credencial roubada: foi um erro de configuração, não uma sabotagem.")
    else:
        case.update(title="O transmissor clandestino", answer=[6, 3, 3, 1])
        event = "Carlos ativou deliberadamente um transmissor clandestino nos servidores às 20h20"
        consequence = "o aparelho enviou documentos confidenciais para um receptor externo"
        source, item = "transmitter", "transmitter"
        reports["transmitter"]["text"] = (
            "Encontrado às 21h15, o transmissor tem registro assinado de envio de documentos às 20h20, "
            "com o mesmo número de série dos pacotes recebidos externamente. A configuração recuperada "
            "selecionava pastas confidenciais e ocultava o envio. A ordem de serviço de Carlos não "
            "autorizava equipamentos de rede. Houve extração direta, sem credenciais roubadas.")
        reports["cameras"]["text"] = (
            "As câmeras corroboram a apresentação de Arthur, o teste de Bianca e a pausa de Seu Antônio. "
            "Às 20h20, Carlos instala o aparelho nos servidores e o conecta ao ponto de dados. "
            "As imagens identificam quem instalou; o laudo do transmissor demonstra o envio.")
        reports["laptop"]["text"] += " Se o notebook transmitiu os documentos (T), deixou sua assinatura (A). Essa assinatura está ausente (¬A). A assinatura encontrada pertence ao transmissor."
        case["characters"][6]["lines"] = ["Instalei um aparelho às 20h20 nos servidores. Era apenas um medidor elétrico.",
            "Encontraram o dispositivo às 21h15. A ordem de serviço deve explicar meu trabalho."]
        case["ability_results"]["Carlos"] = (
            "A inspeção identifica um transmissor de dados, não um medidor elétrico. "
            "Seu registro assinado confirma o envio às 20h20. A ordem de serviço não autorizava "
            "essa instalação. Compare o número de série com os pacotes preservados no laudo.")
        case["ability_results"]["Flávio"] += " Carlos aparece instalando o aparelho às 20h20 nos servidores."
        case["puzzles"][6].update(title="07 / Modus Tollens: exclua o notebook",
            context="T: o notebook enviou os documentos do incidente. A: sua assinatura está no registro. O laudo do notebook fornece T → A e ¬A. Qual conclusão é válida?")
        case["sheets"][6].update(title="07 / Examine a hipótese do notebook", sources=["laptop"],
            note="A assinatura do notebook está ausente. Não confunda esse registro com a assinatura presente do transmissor.")
        case["topics"]["transmitter_analysis"] = report_topic("Envio comprovado pelo transmissor", "transmitter",
            ["person:6", "item:transmitter", "evidence:transmitter"],
            "O registro assinado e o número de série comprovam o envio de documentos às 20h20.", True)
        case["timeline_extra"] = [("transmitter", "20h20", "Ativação do transmissor", "Registro assinado do envio; o aparelho foi encontrado mais tarde.")]
        case["solution"] = (
            "Carlos instalou um transmissor clandestino às 20h20 e enviou documentos diretamente "
            "a um receptor externo. Sua alegação de medição elétrica contradiz a função do aparelho "
            "e a configuração que ocultava a extração. O alerta surgiu às 21h07; o dispositivo só foi "
            "encontrado às 21h15. A prova vem dos pacotes assinados, não apenas da presença do aparelho.")
    reports["credentials"]["text"] = (
        f"Registro pericial: {event} (P). Premissa fictícia confirmada pela análise: se P, então {consequence} (Q). "
        "Não houve captura de credenciais neste caso. "
        + ("A causa foi a configuração interna; os equipamentos externos foram excluídos." if case_id == "extension"
           else "A perícia excluiu falha da rede interna e os demais equipamentos como causa."))
    reports["access"]["text"] = "O banco registrou o alerta às 21h07. A auditoria correlaciona esse alerta ao evento descrito no laudo do incidente. Esse é o horário da detecção, não o do evento inicial."
    case["characters"][2]["lines"][0] = "O alerta foi registrado às 21h07. Isso não significa que tudo começou nesse horário."
    case["topics"]["detection"] = report_topic("Detecção do incidente às 21h07", "access",
        ["person:2", "evidence:access"], "O banco detectou o incidente às 21h07.", True, "Flávio")
    case["topics"]["credentials"].update(title="Evento inicial e consequência comprovada",
        keys={f"item:{item}", f"person:{case['answer'][0]}", f"evidence:{source}", "evidence:credentials"},
        requires={source, "credentials"}, definitions={"P": event + ".", "Q": consequence + "."},
        source_note="O registro fornece P; o laudo do incidente fornece P → Q.")
    case["puzzles"][5].update(title="06 / Modus Ponens: reconstrua o incidente",
        context=f"P: {event}. Q: {consequence}. Registro: P. Laudo: P → Q. Qual conclusão decorre dessas premissas?")
    case["sheets"][5].update(title="06 / Do evento à consequência", sources=list(dict.fromkeys([source, "credentials"])),
        note="O registro fornece o evento; a perícia fundamenta sua consequência.")
    case["reasoning"] = [f"Evento inicial: {event}.", f"Consequência comprovada: {consequence}.",
        "P e P → Q permitem Q por Modus Ponens; o vínculo vem da perícia.",
        "O link das 20h35 era legítimo. O horário da detecção, 21h07, não indica o início.",
        ("A assinatura do notebook está ausente; Modus Tollens exclui esse equipamento." if case_id == "phishing"
         else "A assinatura do transmissor está ausente; Modus Tollens exclui esse aparelho."),
        "Depoimentos e laudos devem ser confrontados; profissão não prova culpa."]
    return case
