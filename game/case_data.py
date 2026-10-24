"""Dados narrativos. Posições são escolhas do protótipo, não álibis oficiais."""
CHARACTERS = [
    {"name": "Seu Antônio", "role": "Faxineiro • 56 anos • 10 anos na função",
     "skill": "Pouco conhecimento tecnológico; conhece a rotina de limpeza.",
     "room": 2, "pos": (1090, 180),
     "lines": ["Fiz uma pausa na sala de lazer. Uso o Wi-Fi do banco no meu celular.",
               "Não entendo muito dessas mensagens. Quero ajudar a esclarecer tudo."]},
    {"name": "Bianca", "role": "Estagiária de TI • 20 anos • 2 meses na função",
     "skill": "Cursa Análise de Dados; auxilia testes supervisionados.",
     "room": 3, "pos": (105, 475),
     "lines": ["Usei o pendrive às 20h20, com autorização para arquivos de teste.",
               "A perícia registrou o conteúdo. Ter usado um dispositivo não prova invasão."]},
    {"name": "Flávio", "role": "Segurança • 31 anos • 4 anos na função",
     "skill": "Conhecimento tecnológico mediano; opera câmeras e controle de acesso.",
     "room": 0, "pos": (105, 180),
     "lines": ["O acesso indevido foi identificado às 21h07. Detecção não é início.",
               "As imagens confirmam os eventos registrados, mas não demonstram causa digital."]},
    {"name": "Arthur", "role": "Visitante de outro banco • 43 anos • 9 anos de experiência",
     "skill": "Conhecimento tecnológico mediano; apresenta soluções institucionais.",
     "room": 1, "pos": (490, 180),
     "lines": ["Meu notebook foi usado na apresentação institucional, de 19h50 a 20h30.",
               "O registro da reunião e a análise do equipamento estão no escritório."]},
    {"name": "Márcia", "role": "Líder financeira • 52 anos • 15 anos na função",
     "skill": "Conhecimento tecnológico alto; responsável por relatórios financeiros.",
     "room": 5, "pos": (880, 475),
     "lines": ["Consultei relatórios no computador interno às 20h45.",
               "Meu uso do sistema deve ser confrontado com os registros técnicos."]},
    {"name": "Jonas", "role": "Secretário do diretor • 39 anos • 1 ano na função",
     "skill": "Conhecimento tecnológico alto; organiza reuniões e documentos.",
     "room": 1, "pos": (710, 180),
     "lines": ["Organizei a apresentação de Arthur. O registro confirma a finalidade do notebook.",
               "Experiência tecnológica não é evidência de culpa."]},
    {"name": "Carlos", "role": "Eletricista terceirizado • 47 anos • 20 anos na função",
     "skill": "Conhecimento tecnológico mediano; trabalha com instalações elétricas.",
     "room": 4, "pos": (490, 520),
     "lines": ["O transmissor foi encontrado às 21h15 e encaminhado para análise.",
               "A presença de um aparelho suspeito exige perícia antes de qualquer conclusão."]},
]

INTRO = (
    "Durante a noite, uma invasão comprometeu informações confidenciais do banco. "
    "O acesso não autorizado foi identificado às 21h07. Sete pessoas foram investigadas. "
    "Explore seis salas, ouça os depoimentos e reúna oito evidências. "
    "Depois, use o painel de investigação para testar o que realmente decorre das premissas. "
    "Nenhuma pessoa deve ser acusada apenas por sua profissão, idade ou conhecimento tecnológico."
)

SOLUTION = (
    "Seu Antônio abriu acidentalmente um link malicioso às 20h35, na sala de lazer, "
    "usando um celular conectado ao Wi-Fi da empresa. O evento comprometeu credenciais, "
    "posteriormente utilizadas por criminosos externos. O banco identificou o acesso "
    "indevido às 21h07. Seu Antônio desencadeou o incidente involuntariamente; não foi "
    "o autor intencional do ataque."
)

REASONING = [
    "Wi-Fi e navegador associam o celular ao evento das 20h35; as câmeras corroboram o local.",
    "A perícia vincula o evento ao comprometimento: P e P → Q permitem Q (Modus Ponens).",
    "O registro vincula as credenciais comprometidas ao acesso externo detectado às 21h07.",
    "Pendrive: arquivos de teste autorizados, sem vínculo com o incidente na análise técnica.",
    "Notebook: apresentação de 19h50 a 20h30, corroborada pelo registro e pela perícia.",
    "Transmissor: encontrado às 21h15; a análise o excluiu deste incidente.",
    "Rede interna: a auditoria excluiu a falha proposta; conectar-se ao Wi-Fi não prova falha.",
    "Computador interno: consulta de relatórios às 20h45 sem vínculo técnico com o ataque.",
    "A causalidade vem das premissas periciais fictícias, nunca apenas da ordem dos horários.",
]
