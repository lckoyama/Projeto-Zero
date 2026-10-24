# Protocolo Zero — O Mistério da Invasão Bancária

Jogo local de investigação top-down, feito apenas com Python e Pygame para a disciplina de Resolução de Problemas com Lógica Matemática. Gráficos geométricos, sem imagens externas, web ou banco de dados.

## Referência visual do projeto

![Referência visual de Protocolo Zero, com os sete personagens, os itens de investigação e as seis salas do banco](assets/reference/protocolo-zero.png)

Referência para a identidade visual, os personagens e os ambientes. A versão jogável atual utiliza formas geométricas.

## Executar no VS Code

Abra esta pasta no VS Code. Use Python 3.10 ou superior e execute no terminal:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

Ou, com seu ambiente Python já selecionado/ativado:

```powershell
python -m pip install -r requirements.txt
python main.py
```

No VS Code, selecione `.venv` em **Python: Select Interpreter**. Uma sessão gráfica local é necessária para jogar. Sem Pygame, a entrada mostra o comando de instalação em vez de um traceback.

## Controles e progressão

- WASD ou setas: mover; E: interagir perto de um marcador.
- I ou Tab: inventário; M: mapa; J: painel; Esc: voltar/pausar.
- Mouse: botões; 1–3: respostas dos desafios; Enter: continuar após o feedback.
- Círculos: sete personagens com fichas e depoimentos. Quadrados: objetos. Marcadores consultados ficam verdes.

As portas das seis salas ficam voltadas ao corredor central. Explore, reúna oito evidências, organize a análise no painel e resolva oito desafios. Só então a reconstrução final fica disponível. Ela pede pessoa, método, equipamento e horário. Erros não apagam o progresso. A solução e a exclusão das hipóteses são apresentadas após acertar a reconstrução.

O menu permite retomar a partida em memória. **Não há salvamento em disco**: fechar o aplicativo ou iniciar uma nova investigação reinicia a partida. O loop limita a atualização a 60 FPS, inclusive em diálogos.

## Lógica matemática

`game/logic.py` não importa Pygame. Expressões são nomes de variáveis, booleanos ou tuplas: `("implies", "P", "Q")`. O motor avalia negação, conjunção, disjunção inclusiva, condicional e bicondicional; gera todas as valorações; verifica equivalência e consequência semântica; produz contraexemplos.

Os desafios abordam proposições simples e compostas, tabelas-verdade, De Morgan, Modus Ponens, Modus Tollens e afirmação indevida do consequente. Cada resposta é validada pelo motor, sem gabarito por índice. Todos os desafios são obrigatórios para vencer. O motor usa lógica proposicional clássica: premissas inconsistentes acarretam qualquer conclusão; os exercícios de inferência do jogo usam premissas consistentes.

Coincidência temporal não demonstra causalidade. As relações causais usadas são premissas explícitas de laudos fictícios. A condicional material sozinha também não demonstra uma causa real.

## Escopo dos dados narrativos

Foram usados os personagens, objetos, oito pistas e horários fornecidos no pedido. **O documento oficial com a grade completa de movimentações não estava na pasta.** As posições dos NPCs são escolhas de jogabilidade, não álibis adicionais. Não foram inventados horários de deslocamento. Substitua/complemente `game/case_data.py` e `game/evidence.py` quando o documento estiver disponível.

Diálogos e detalhes dos laudos (assinatura do transmissor, correlação do evento, exclusão técnica dos equipamentos e da falha interna) são complementos pedagógicos fictícios do protótipo, coerentes com a solução fornecida, e devem ser revisados pelo grupo. Não constituem nova documentação oficial. As evidências revelam fatos gradualmente; a reconstrução completa aparece apenas na vitória.

## Testes

Para verificar apenas o motor lógico, sem depender do Pygame:

```powershell
python -B -m unittest discover -s tests -p test_logic.py -v
```

Para executar todos os testes no ambiente virtual:

```powershell
.venv\Scripts\python -B -m unittest discover -s tests -v
```

Os testes verificam conectivos, tabelas-verdade, equivalências, inferências, acesso aos objetos, colisões e progressão até a vitória. Os testes gráficos usam uma tela virtual do SDL, sem abrir janela. A opção `-B` evita gerar arquivos de cache Python; os testes não salvam capturas nem relatórios em disco.

## Organização

- `main.py`: entrada e diagnóstico de dependência ausente.
- `game/settings.py`: dimensões, cores e FPS.
- `game/player.py`, `game/map.py`: movimento, colisões e salas.
- `game/scenes.py`, `game/dialogue.py`: cenas, eventos e texto.
- `game/inventory.py`, `game/evidence.py`, `game/case_data.py`: coleta e narrativa.
- `game/logic.py`, `game/puzzles.py`: motor independente e exercícios.
- `tests/`: testes automatizados do motor lógico e da integração do jogo.
- `assets/`: locais reservados para arte e áudio opcionais.

Para adicionar sprites depois, substitua os desenhos em `Player.draw`, `BankMap.draw` e `Game.draw_world`. Mantenha os retângulos de colisão e posições separados da arte. O protótipo não carrega arquivos de assets, portanto imagens/fontes/áudios externos ausentes não impedem sua execução. As fontes usam resolução do sistema com fallback do Pygame.
