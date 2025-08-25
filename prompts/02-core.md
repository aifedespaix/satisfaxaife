Ouvre une PR : **feat/core-engine**
But : base exécutable minimale (sans HUD avancé).

À faire (fichiers courts, typés) :

- `app/core/config.py` : W=1080, H=1920, FPS=60, DT, couleurs de base, épaisseur murs
- `app/core/types.py` : dataclasses (Stats, Damage, EntityId), alias de types (Vec2, Color)
- `app/core/utils.py` : clamp, easing simple, to_screen helper
- `app/core/registry.py` : registre armes (register/create/names)
- `app/world/physics.py` : Pymunk Space (gravité 0), murs (boîte), step(dt)
- `app/world/entities.py` : Ball.spawn(), take_damage(), cap_speed()
- `app/world/projectiles.py` : Projectile.spawn(), step(dt)
- `app/game/match.py` : boucle de match, gestion entités/projectiles, horloge
- `app/video/recorder.py` : writer MP4 via imageio-ffmpeg, fallback GIF si indispo
- `app/cli.py` :
  - `run`: paramètres `--seconds`, `--seed`, `--out` (stub rendu pour l’instant)
  - `batch`: placeholder (juste parse args)

Critères d’acceptation :

- CI verte.
- `uv run python -m app.cli run --seconds 3` écrit un fichier vidéo/gif “stub” (fond uni + frame counter).
- Code typé, petits fichiers, imports ordonnés.

Commits : feat:, refactor:, chore:
