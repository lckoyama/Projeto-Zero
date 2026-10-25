"""Telas de habilidades e comandos de salvamento usados pelas cenas do jogo."""
import pygame

from game import settings as s
from game.abilities import ABILITIES, DIGITAL_PUZZLE
from game.case_data import CHARACTERS
from game.savegame import load_progress, save_progress


class AbilityScenes:
    def open_ability(self):
        if self.active_person:
            self.ability_feedback = ""
            self.scene = "ability"

    def use_ability(self, choice=None):
        person = next((p for p in CHARACTERS if p["name"] == self.active_person), None)
        if person is None:
            return
        room = next((i for i, rect in enumerate(self.bank.rooms)
                     if rect.collidepoint(self.player.rect.center)), None)
        nearby = pygame.Vector2(person["pos"]).distance_to(self.player.rect.center) <= 66
        success, self.ability_feedback = self.abilities.activate(
            person["name"], room, nearby, self.inventory, choice)
        self.ability_success = success

    def draw_ability(self):
        ability = ABILITIES[self.active_person]
        self.title(self.active_person + " / " + ability["name"], "HABILIDADE DE INVESTIGAÇÃO • Esc: voltar ao banco")
        self.text(ability["description"], y=125, color=s.BLUE)
        used = self.active_person in self.abilities.used
        if used:
            self.text("Resultado registrado no painel:", y=195, color=s.GREEN)
            self.text(self.abilities.records[self.active_person], y=245)
        elif self.active_person == "Bianca":
            self.text(DIGITAL_PUZZLE["context"], y=185)
            for index, (label, _) in enumerate(DIGITAL_PUZZLE["options"]):
                self.button(label, (60 + index * 365, 335, 340, 55),
                            lambda i=index: self.use_ability(i))
        elif self.active_person == "Jonas":
            self.text("Compare uma hipótese sobre o horário da apresentação de Arthur com a agenda. As opções abaixo não são novos depoimentos.", y=190)
            for index, time in enumerate(("20h20", "20h45")):
                self.button("Comparar " + time, (60 + index * 450, 335, 420, 55),
                            lambda value=time: self.use_ability(value))
        else:
            self.button("Utilizar habilidade", (60, 260, 450, 60), self.use_ability)
        if self.ability_feedback and not used:
            self.text(self.ability_feedback, y=435, color=s.GREEN if self.ability_success else s.RED)
        self.button("Voltar ao banco", (60, 710, 350, 56), lambda: self.set_scene("world"))

    def draw_ability_records(self):
        self.title("Registros das habilidades", "Selecione um personagem para consultar suas descobertas. Esc: banco.")
        for index, (name, ability) in enumerate(ABILITIES.items()):
            done = name in self.abilities.used
            self.button(name + (" • registrado" if done else " • pendente"),
                        (60, 125 + index * 75, 350, 62),
                        lambda value=name: setattr(self, "record_person", value))
        ability = ABILITIES[self.record_person]
        self.text(ability["name"], 455, 135, 680, s.BLUE)
        self.text(ability["description"], 455, 185, 680)
        self.text(self.abilities.records.get(self.record_person,
                  "Converse com este personagem e utilize sua habilidade para registrar o resultado."),
                  455, 290, 680)
        self.button("Voltar ao painel", (815, 710, 325, 56), lambda: self.set_scene("board"))

    def save_game(self):
        try:
            save_progress(self)
            self.save_message = "Progresso salvo."
        except OSError:
            self.save_message = "Não foi possível salvar. Verifique a permissão de escrita na pasta do jogo."

    def load_game(self):
        try:
            load_progress(self)
            self.set_scene("board")
            self.message = "Progresso carregado. Evidências e habilidades restauradas."
        except FileNotFoundError:
            self.save_message = "Nenhuma partida salva foi encontrada."
        except (OSError, ValueError, TypeError, OverflowError):
            self.save_message = "Não foi possível carregar: arquivo inválido, incompatível ou sem acesso. A partida atual foi preservada."
