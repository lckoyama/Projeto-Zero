"""Entrada do Protocolo Zero: execute com python main.py."""
try:
    import pygame
except ImportError:
    raise SystemExit("Pygame não instalado. Execute: python -m pip install -r requirements.txt")

from game.scenes import Game

if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Protocolo Zero")
    parser.add_argument("--demo", action="store_true", help="Iniciar o caso fixo de Seu Antônio.")
    parser.add_argument("--export-proofs", metavar="PASTA", help="Exportar as quatro provas em texto, sem abrir a janela.")
    args = parser.parse_args()
    if args.export_proofs:
        from game.academic_proof import proof_text
        from game.cases import CASE_IDS, build_case
        destination = Path(args.export_proofs)
        destination.mkdir(parents=True, exist_ok=True)
        for case_id in CASE_IDS:
            (destination / f"{case_id}.txt").write_text(proof_text(build_case(case_id)), encoding="utf-8")
        print(f"Quatro provas verificadas exportadas para {destination}.")
    else:
        game = Game()
        if args.demo:
            game.start_demo()
        game.run()
