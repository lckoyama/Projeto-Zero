"""Telas de habilidades e comandos de salvamento usados pelas cenas do jogo."""
import pygame

from game import settings as s
from game.abilities import (ABILITIES, ABILITY_CHALLENGES, DIGITAL_PUZZLE,
                            validate_ability_challenge)
from game.case_data import CHARACTERS
from game.puzzles import validate
from game.savegame import load_progress, save_progress


class AbilityScenes:
    def ability_available(self, name):
        return ABILITIES[name]["requires"] <= self.abilities.inspected

    def ability_puzzle(self, name):
        if name == "Márcia":
            return self.puzzles[5]
        if name == "Carlos":
            return self.puzzles[6]
        return ABILITY_CHALLENGES[name]

    def open_ability(self):
        if self.active_person and self.ability_available(self.active_person):
            self.ability_feedback = ""
            self.scene = "ability"

    def use_ability(self, choice=None):
        person = next((p for p in CHARACTERS if p["name"] == self.active_person), None)
        if person is None:
            return
        if person["name"] not in self.talked:
            self.ability_success = False
            self.ability_feedback = "Converse com a pessoa antes de utilizar esta habilidade."
            return
        legacy_activation = person["name"] != "Bianca" and (
            choice is None or isinstance(choice, str))
        if person["name"] != "Bianca" and person["name"] in ABILITY_CHALLENGES and not legacy_activation:
            puzzle = self.ability_puzzle(person["name"])
            if type(choice) is not int or not 0 <= choice < len(puzzle["options"]):
                self.ability_success = False
                self.ability_feedback = "Selecione uma opção do desafio."
                return
            correct, detail = validate(puzzle, choice)
            if not correct:
                self.ability_success = False
                self.ability_feedback = "Revise a inferência. " + detail
                return
        room = next((i for i, rect in enumerate(self.bank.rooms)
                     if rect.collidepoint(self.player.rect.center)), None)
        nearby = pygame.Vector2(person["pos"]).distance_to(self.player.rect.center) <= 66
        activation_choice = choice if person["name"] == "Bianca" or (
            person["name"] == "Jonas" and isinstance(choice, str)) else None
        success, self.ability_feedback = self.abilities.activate(
            person["name"], room, nearby, self.inventory, activation_choice)
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
        else:
            puzzle = self.ability_puzzle(self.active_person)
            self.text(puzzle["context"], y=185)
            for index, (label, _) in enumerate(puzzle["options"]):
                column = index % 3
                row = index // 3
                self.button(label, (60 + column * 365, 335 + row * 75, 340, 55),
                            lambda i=index: self.use_ability(i))
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
