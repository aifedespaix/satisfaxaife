Ouvre une PR : **feat/renderer-and-hud**
But : rendu visuel off-screen + HUD de base.

À faire :
- `app/render/renderer.py` :
  - surface off-screen (1080x1920), arrière-plan sombre, arène (rect à coins arrondis)
  - draw_ball(pos, radius, color, face) avec gloss simple + anneau d’équipe
  - draw_projectile
  - trails dépendants de la vitesse (alpha fade court)
  - draw_eyes(pos, face/gaze, radius) avec blink variable
  - present/capture_frame pour l’enregistreur
- `app/render/hud.py` :
  - draw_title("Qui gagne : Katana ou Shuriken ?")
  - draw_hp_bars(hp_a, hp_b, labels)
  - watermark discret "@battleballs" en bas-gauche
- Intégration dans `app/game/match.py` (ordre : BG -> proj -> balls -> HUD)
- MAJ `app/cli.py` pour qu’un “run” rende des vraies frames (mouvements simples : deux balls se déplacent et rebondissent sans combat pour l’instant)

Critères d’acceptation :
- CI verte.
- La vidéo de test (3–6 s) montre : titre, deux HP bars, deux balls avec yeux/trails.
- Pas d’ouverture de fenêtre en CI (off-screen only).

Commits : feat(render):, feat(hud):, refactor:
