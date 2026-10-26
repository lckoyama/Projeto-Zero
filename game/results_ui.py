"""Resultados da reconstrução, preservando a investigação para revisão."""
from game import settings as s


class ResultsUI:
    def draw_result(self, victory):
        self.title("Vitória / caso resolvido" if victory else "Derrota / acusação incorreta")
        self.text(self.case["title"], y=95, small=True, color=s.MUTED)
        self.text(f"Pontuação final: {self.score.points}", y=122, color=s.GREEN if victory else s.RED)
        self.text(f"Acertos: {self.score.correct}     Erros: {self.score.errors}     Dicas: {self.score.hints_used}",
                  y=168, small=True)
        self.text(f"Evidências: {len(self.inventory.ids)}/{len(self.evidence)}     "
                  f"Desafios concluídos: {self.puzzle_index}/{len(self.puzzles)}     "
                  f"Habilidades: {len(self.abilities.used)}/7", y=203, small=True)
        if victory:
            self.text(self.case["solution"], y=252, width=1080, color=s.GREEN)
            self.text("A prova formal e suas fontes estão disponíveis no botão abaixo.", y=505, small=True)
            self.button("Ver prova / slides", (60, 560, 320, 46), lambda: self.set_scene("proof"))
        else:
            self.text("A combinação escolhida não corresponde aos laudos desta investigação. "
                      "Cada nova tentativa incorreta custa 20 pontos. Você pode revisar a conclusão. "
                      "Evidências, habilidades e desafios concluídos foram preservados.", y=265)
            self.button("Revisar conclusão", (60, 430, 340, 48), self.retry_conclusion)
            self.button("Consultar evidências", (420, 430, 340, 48), lambda: self.set_scene("inventory"))
        self.button("Nova partida", (60, 650, 270, 48), self.start)
        self.button("Salvar resultado", (350, 650, 270, 48), self.save_game)
        self.button("Menu inicial", (640, 650, 270, 48), lambda: self.set_scene("menu"))
        self.text(self.save_message, y=720, small=True)

    def draw_proof(self):
        from game.academic_proof import proof_text
        self.title("Prova formal / " + self.case["title"])
        sections = proof_text(self.case).split("\n\n")
        page = min(getattr(self, "proof_page", 0), len(sections) - 1)
        self.text(sections[page], y=125, small=True)
        self.text(f"Página {page + 1}/{len(sections)}", y=670, small=True)
        self.button("Anterior", (60, 720, 190, 44), lambda: setattr(self, "proof_page", max(0, page - 1)))
        self.button("Próxima", (270, 720, 190, 44), lambda: setattr(self, "proof_page", min(len(sections) - 1, page + 1)))
        self.button("Voltar", (900, 720, 240, 44), lambda: self.set_scene("victory" if self.score.won else "board"))
