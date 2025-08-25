Ouvre une PR : **feat/batch-tests-and-docs**
But : production en série + qualité.

À faire :

- `app/cli.py` : commande `batch --count N --out-dir out` (varie seeds/armes, nommage explicite ex: battle_seed42_katana_vs_shuriken.mp4)
- `tests/unit/` : tests pour cooldown armes, dégâts, policy (angles), utils
- `tests/integration/` : mini-match 2 s headless → vérifie fichier vidéo écrit et états cohérents
- CI :
  - upload coverage (artifact)
  - upload 1–2 courts extraits vidéo (ou quelques frames) pour inspection
- Docs :
  - README enrichi (usage batch, conseils TikTok, troubleshooting)
  - `.gitignore` : out/, frames/, logs/ confirmés
  - (optionnel) `docs/banner.png` placeholder et section “Aperçu”

Critères d’acceptation :

- CI verte (lint, mypy, tests).
- Artefacts de test dispos dans la run CI.
- README prêt GitHub.
