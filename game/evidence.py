"""Oito evidências; textos periciais complementares são ficção pedagógica."""
EVIDENCE = [
    {"id": "wifi", "title": "01 • Registro Wi-Fi", "object": "Celular conectado", "pos": (920, 245),
     "text": "O registro associa o celular de Seu Antônio ao Wi-Fi da empresa durante sua pausa na sala de lazer. A conexão isolada não demonstra uma invasão."},
    {"id": "browser", "title": "02 • Histórico do navegador", "object": "Laudo do navegador", "pos": (1090, 265),
     "text": "O histórico preservado do celular registra a abertura de um link às 20h35. O endereço foi classificado como malicioso pela perícia. É preciso relacionar o evento ao laudo de credenciais."},
    {"id": "credentials", "title": "03 • Laudo de credenciais", "object": "Terminal pericial", "pos": (680, 560),
     "text": "Premissa pericial fictícia: se o evento do link registrado no celular ocorreu (P), então ele comprometeu credenciais (Q). A perícia correlacionou o identificador do evento à captura das credenciais. A auditoria excluiu a hipótese de falha na rede interna neste caso."},
    {"id": "access", "title": "04 • Alerta das 21h07", "object": "Console de alertas", "pos": (280, 240),
     "text": "O banco identificou o acesso indevido às 21h07. O registro pericial vincula esse acesso de criminosos externos às credenciais comprometidas. Esse horário é o da identificação, não o da abertura do link."},
    {"id": "usb", "title": "05 • Análise do pendrive", "object": "Pendrive", "pos": (280, 550),
     "text": "Bianca utilizou o pendrive às 20h20. A autorização e a perícia confirmam arquivos de teste autorizados e ausência de vínculo com este incidente. A autorização sozinha não seria prova de inocuidade."},
    {"id": "laptop", "title": "06 • Registro da reunião", "object": "Notebook externo", "pos": (600, 255),
     "text": "Arthur utilizou o notebook de 19h50 a 20h30 numa apresentação institucional. Registro da reunião e perícia do equipamento excluem seu uso como vetor deste incidente."},
    {"id": "transmitter", "title": "07 • Análise do transmissor", "object": "Dispositivo transmissor", "pos": (510, 570),
     "text": "Encontrado às 21h15. Premissas da perícia: se este aparelho transmitiu os dados do incidente (T), deixou a assinatura A (T → A). A assinatura está ausente (¬A). A análise excluiu este aparelho, não todo transmissor possível."},
    {"id": "cameras", "title": "08 • Registro das câmeras", "object": "Arquivo de câmeras", "pos": (110, 265),
     "text": "As câmeras corroboram os eventos fornecidos no caso: notebook na reunião, pendrive autorizado e pausa de Seu Antônio na sala de lazer. Não revelam o conteúdo de uma tela nem demonstram causalidade. A grade completa de movimentações do grupo ainda não foi fornecida."},
]

COMPUTER = {"object": "Computador interno", "pos": (1060, 550),
            "text": "Márcia consultou relatórios às 20h45. A análise técnica fictícia não encontrou vínculo dessa consulta com o ataque. Este é um objeto de contexto; as oito evidências estão distribuídas pelo banco."}
