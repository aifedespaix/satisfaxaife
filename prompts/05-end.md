Ouvre une PR : **feat/end-screen-and-loop-config**
But : finition TikTok + config externe.

À faire :

- Fin de match :
  - freeze 120 ms sur dernier hit
  - slow-mo 0.35× ~0.6 s
  - bannière : “VICTOIRE : {team}” + sous-titre “{weapon} remporte le duel !”
  - fade-to-start 400 ms (boucle) ; option pré/post-roll
- `app/render/theme.py` : palette blue/orange + gradients HP
- `app/config.json` : canvas, thème, HUD (titre, watermark), endScreen (textes, slowmo, fade)
- `app/cli.py` : lecture config.json par défaut, flags pour surcharger seed/seconds/out
- README : documenter la boucle & la config

Critères d’acceptation :

- CI verte.
- Vidéo de démo : fin lisible, bannière propre, retour en boucle sans à-coup majeur (ou fade propre).
