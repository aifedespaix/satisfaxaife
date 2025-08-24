# app/cli.py
import typer
from app.core.config import FPS
from app.runner import run_match, run_batch  # à créer léger

app = typer.Typer(help="Génération de vidéos satisfaction (TikTok).")

@app.command()
def run(weapon_a: str = "katana", weapon_b: str = "shuriken",
        seed: int = 42, seconds: int = 22, out: str = "battle.mp4"):
    """Lance un match unique et exporte la vidéo."""
    run_match(weapon_a, weapon_b, seed, seconds, out)

@app.command()
def batch(count: int = 10, out_dir: str = "out"):
    """Génère N vidéos (armes/seeds variées)."""
    run_batch(count, out_dir)

if __name__ == "__main__":
    app()
