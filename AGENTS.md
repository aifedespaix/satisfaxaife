# AGENTS

## Objectif

Générer automatiquement des **vidéos satisfaction** (format TikTok 1080×1920, 60 fps) via un **moteur de jeu 2D** (physique) en Python, avec un code **modulaire, typé, testable**, et des **assets cohérents**.

## Principes non-négociables

- **Qualité**: typage strict (mypy), lint (ruff), tests (pytest), docstrings.
- **Évolutivité**: petits fichiers, registres/plug-ins, couches découplées.
- **Reproductibilité**: seeds contrôlés, versions de libs **dernières stables**.
- **Automatisation**: pre-commit, CI, Makefile/Justfile, CLI (Typer).
- **Sécurité**: audit deps (pip-audit), bandit, pinning versions.

## Stack & Versions

- Python ≥ 3.11
- Dépendances principales (toujours **dernières versions stables** au moment de l’installation) :
  - `pygame` (rendu 2D), `pymunk` (physique), `imageio` + `imageio-ffmpeg` (export vidéo),
  - `typer` (CLI), `pydantic-settings` (config),
  - Dev: `ruff`, `mypy`, `pytest`, `pytest-cov`, `pre-commit`, `pip-audit`, `bandit`.
- Gestion : **uv** (install, lock, run). Un seul outil de gestion.

## Rôles

- **Owner (humain)** : priorise, valide les décisions, tranche les ADR.
- **Codegen Agent** : propose du code **Python typé** conforme (ruff/mypy), petits fichiers, tests inclus.
- **QA Agent** : écrit/améliore les tests (unitaires/intégration), impose couverture, vérifie seeds et déterminisme.
- **Lint/Style Agent** : applique ruff/format, revoit imports, docstrings, conventions.
- **Doc Agent** : maintient README, AGENTS.md, ADR/ et doc d’API interne.
- **Release Agent** : versioning (SemVer), CHANGELOG (Keep a Changelog), tag, build artefacts.
- **Security Agent** : pip-audit, bandit, dépendances obsolètes.

## Dossier & Découpage

- `app/core`: types, config, utils, registry (plugins)
- `app/world`: physics (Pymunk), entities (Ball), projectiles
- `app/weapons`: base + 1 fichier/arme (katana, shuriken, ...)
- `app/ai`: policies d’IA (simple, kiter, agressive, teamplay)
- `app/game`: match loop, rules, replay/events, team
- `app/render`: renderer pygame, HUD, FX
- `app/video`: recorder (imageio)
- `app/cli.py`: CLI Typer (run, batch, bench, export)
- `tests/`: unit/ & integration/

## Qualité de code (checklist)

- Typage **obligatoire** (aucun `Any` caché).
- Fonctions ≤ 50–60 lignes si possible, modules ≤ 300 lignes.
- Pas d’état global; passer par objets ou paramètres.
- Exceptions spécifiques; pas de `print` (utiliser `logging`).
- Imports triés; dead code interdit.
- Docstrings avec paramètres, returns, exceptions.
- Tests: un test par unité logique. Intégration: scénario complet 1v1 + 2v2.

## CI (pipeline minimal)

1. Lint & format (ruff)
2. Type-check (mypy)
3. Tests + couverture
4. Audit sécurité (pip-audit, bandit)
5. Build (si tag) + publication des artefacts

## CLI (Typer)

- `run`: lance un match (armes, seed, durée, export vidéo).
- `batch`: génère N vidéos avec presets (armes, seeds).
- `bench`: petit profil de perf.

## Config

- `Settings` via `pydantic-settings`: fps, dt, taille, couleurs, chemin export, seed.
- Override par env/CLI (ex: `--seed 123 --seconds 22`).

## Reproductibilité

- Seed obligatoire pour chaque run; estampiller les vidéos avec métadonnées (weaponA, weaponB, seed).
- Lockfile des deps commit.

## Évolutions prévues

- Équipes (n>1), modes (FFA, 2v2…), armes avancées (lance, masse, bouclier/parry).
- FX (traînées, particules), replays & highlights, boucle parfaite (montage automatique).

## ADR (Architecture Decision Records)

- Un fichier par décision : `adr/0001-nom_snake.md`, `adr/0002-...`.
- Contenu minimal : Contexte, Décision, Alternatives, Conséquences, Liens.
- Règle : toute décision structurelle passe par un ADR.

## Convention de commits

- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `build:`, `chore:`.
- Releases **SemVer**; changelog tenu à jour.

## Définition du “Done”

- Lint OK, format OK, mypy OK, tests OK, couverture OK, doc mise à jour, ADR si changement d’archi.
