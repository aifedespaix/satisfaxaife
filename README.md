# 🎥 Battle Balls — Générateur automatique de vidéos satisfaction TikTok

![Banner](docs/banner.png)

**Battle Balls** est un moteur Python permettant de **générer automatiquement des vidéos "satisfaction" pour TikTok** 🎬  
Le concept : des **boules armées** (katana, shuriken, etc.) s’affrontent dans une arène, et le moteur **simule physiquement** le combat en temps réel, puis **exporte la vidéo** en haute qualité, prête à être postée sur TikTok.

Le code est **modulaire**, **extensible** et **typé**, pensé pour créer **des centaines de vidéos uniques** automatiquement.

---

## ✨ Fonctionnalités principales

- 🏟 **Simulations physiques** réalistes via [Pymunk](https://www.pymunk.org/).
- ⚔️ **Boules armées** avec armes variées : katana, shuriken, etc.
- 🧠 **IA configurable** : agressive, kite, support… ou comportements personnalisés.
- 🎨 **Rendu vertical 1080×1920** optimisé pour TikTok.
- 🎥 **Export vidéo automatique** en `.mp4` via [imageio-ffmpeg](https://imageio.readthedocs.io/).
- 🔄 **Reproductibilité totale** grâce aux seeds (mêmes combats → mêmes résultats).
- 🧩 **Architecture plug-in** : ajout d'armes, IA ou effets visuels sans toucher au moteur.
- 🔊 **Effets sonores & particules** (prévu pour la v2).
- 📦 **Batch mode** : génération de **N vidéos** en une seule commande.
- 🚀 Prêt pour la scalabilité : 1v1, 2v2, FFA, replay slow-mo, highlights TikTok.

---

## 🧠 Concept des vidéos TikTok

Les vidéos générées sont pensées pour **maximiser le watch-time** :

- 🔁 **Boucles parfaites** : la fin peut relancer automatiquement le match.
- 🎯 **Suspense** : combats courts (20–40 sec) → les viewers restent jusqu'au KO.
- 🌈 **Satisfying vibes** : couleurs pop, mouvements fluides, bruitages ASMR.
- 🧩 **Variabilité infinie** : armes, seeds, couleurs → des milliers de vidéos uniques.
- 🔮 **Prédictions TikTok** (optionnel) :  
  *"L’arme qui gagne choisira ton destin ✨"* → fort potentiel viral.

---

## 🏗️ Architecture du projet

```
battle-balls/
│
├── app/
│   ├── core/        # Types, config, utils, registry (plugins)
│   ├── world/       # Physique, entités, projectiles
│   ├── weapons/     # Katana, Shuriken, Lance, Bouclier... (1 arme = 1 fichier)
│   ├── ai/          # Politiques IA (agressive, kiter, teamplay, prédictions)
│   ├── render/      # Rendu Pygame + HUD, FX, shaders
│   ├── video/       # Enregistreur vidéo (imageio)
│   ├── game/        # Gestion de match, équipes, règles, replay, scoring
│   ├── cli.py       # Interface CLI Typer (lancer un match ou plusieurs)
│   └── __init__.py
│
├── tests/           # Tests unitaires et d'intégration
├── docs/            # Images, schémas, bannières
├── out/             # Vidéos générées
├── .gitignore
├── AGENTS.md
├── pyproject.toml
├── Makefile
└── README.md
```

---

## 🚀 Installation

### 1. Cloner le projet

```bash
git clone https://github.com/username/battle-balls.git
cd battle-balls
```

### 2. Créer l’environnement virtuel (recommandé : **uv**)

```bash
uv sync --all-extras --dev
```

### 3. Activer l’environnement

```bash
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate   # Windows
```

### 4. Vérifier l’installation

```bash
uv run python -m app.cli --help
```

---

## 🎮 Lancer un match simple

Exemple : **Katana VS Shuriken**, durée 22s, seed = 42 :

```bash
uv run python -m app.cli run \
  --weapon-a katana \
  --weapon-b shuriken \
  --seconds 22 \
  --seed 42 \
  --out out/katana_vs_shuriken.mp4
```

📌 **Résultat :**  
Une vidéo **1080×1920, 60 FPS, .mp4**, prête pour TikTok.

---

## 📦 Générer un batch de vidéos

Générer **10 vidéos TikTok** aléatoires automatiquement :

```bash
uv run python -m app.cli batch \
  --count 10 \
  --out-dir out
```

---

## ⚙️ Configuration personnalisée

- **Armes** disponibles : `app/weapons/`
- **IA** : agressive, kite, support, teamplay.
- **Équipes** : passer de 1v1 → 2v2 → FFA → Battle Royale.
- **Rendu** : couleurs, arènes, effets visuels.
- **Boucle & fin de match** : freeze 120 ms, ralenti ×0.35, bannière « VICTOIRE » puis fondu vers le début (400 ms).
- **Configuration externe** : `app/config.json` regroupe canvas, palette (bleu/orange), HUD (titre, watermark) et paramètres d'**end screen** (textes, slow-mo, fade...).
- **FPS / résolution** : ajuster `canvas` dans `app/config.json`.

---

## 🧪 Lancer les tests

```bash
uv run pytest
```

---

## 📌 Roadmap

- [ ] ⚔️ Plus d’armes : lance, masse, bouclier.
- [ ] 🧠 IA avancée : esquives, focus multiple, comportements dynamiques.
- [ ] 🏟 Arènes procédurales pour varier les vidéos.
- [ ] 🎥 Slow-mo automatique sur le dernier hit.
- [ ] 🔁 Boucles TikTok parfaites (match → replay → restart).
- [ ] 🔊 Effets sonores & ASMR optimisés.
- [ ] 🌈 FX visuels : particules, traînées, éclats.
- [ ] 🤖 Mode *full batch* : générer **100+ vidéos par nuit**.

---

## 📜 Licence

[MIT](LICENSE)
