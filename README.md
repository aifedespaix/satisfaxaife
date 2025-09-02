# 🎥 Battle Balls — Générateur automatique de vidéos satisfaction TikTok

**Battle Balls** est un moteur Python permettant de **générer automatiquement des vidéos "satisfaction" pour TikTok** 🎬  
Le concept : des **boules armées** (katana, shuriken, etc.) s’affrontent dans une arène, et le moteur **simule physiquement** le combat en temps réel, puis **exporte la vidéo** en haute qualité, prête à être postée sur TikTok.

Le code est **modulaire**, **extensible** et **typé**, pensé pour créer **des centaines de vidéos uniques** automatiquement.

## 👀 Aperçu

Image de prévisualisation à venir.

---

## ✨ Fonctionnalités principales

- 🏟 **Simulations physiques** réalistes via [Pymunk](https://www.pymunk.org/).
- ⚔️ **Boules armées** avec armes variées : katana, shuriken, etc.
- 🧠 **IA configurable** : agressive, kite, support… ou comportements personnalisés.
- 🎨 **Rendu vertical 1080×1920** optimisé pour TikTok.
- 🎥 **Export vidéo automatique** en `.mp4` via [imageio-ffmpeg](https://imageio.readthedocs.io/).
- 🖥️ **Mode affichage** sans enregistrement grâce à l'option `--display`.
 - 🔄 **Reproductibilité totale** grâce aux seeds (mêmes combats → mêmes résultats).
 - 🛡️ **Esquives dépendantes de la seed** : chaque seed produit un biais d'évitement unique mais reproductible.
- 🌀 **Dash** d'esquive infligeant des dégâts proportionnels à la vitesse,
  coup critique si une attaque touche pendant l'action et 3 s de recharge.
- 🧩 **Architecture plug-in** : ajout d'armes, IA ou effets visuels sans toucher au moteur.
- 🔊 **Effets sonores** intégrés dans la piste audio.
- 📦 **Batch mode** : génération de **N vidéos** en une seule commande.
- 🚀 Prêt pour la scalabilité : 1v1, 2v2, FFA, replay slow-mo, highlights TikTok.
- 🎞️ **Ralentit automatique** du coup fatal ajouté à la fin de la vidéo.

---

## 🧠 Concept des vidéos TikTok

Les vidéos générées sont pensées pour **maximiser le watch-time** :

- 🔁 **Boucles parfaites** : la fin peut relancer automatiquement le match.
- 🎯 **Suspense** : combats courts (20–40 sec) → les viewers restent jusqu'au KO.
- 🌈 **Satisfying vibes** : couleurs pop, mouvements fluides, bruitages ASMR.
- 🧩 **Variabilité infinie** : armes, seeds, couleurs → des milliers de vidéos uniques.
- 🔮 **Prédictions TikTok** (optionnel) :  
  _"L’arme qui gagne choisira ton destin ✨"_ → fort potentiel viral.

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

### Clean Images

## `magick mogrify -strip ./assets/*.png`

## 🎮 Lancer un match simple

Exemple : **Katana VS Shuriken**, seed = 42 :

````bash
v```

Pendant le match, pressez `Maj gauche` pour déclencher un *dash* offrant une
impulsion rapide. Les collisions et dégâts restent actifs pendant toute sa
durée, mais une traînée de clones évanescents rend l'action spectaculaire. L'IA
utilise le dash automatiquement lorsqu'un projectile est prévu à moins de `0,3 s`.

📌 **Résultat :**
Une vidéo **1080×1920, 60 FPS, .mp4**, prête pour TikTok, enregistrée dans
`./generated` sous la forme
`YYYY_MM_DD_HH_MM_SS-katana-VS-shuriken-<arme_vainqueur>_win.mp4`.

⏱️ _La durée du match dépend de la dynamique du jeu._
Si aucun vainqueur n’est déterminé après **2 minutes**, le moteur interrompt
automatiquement la simulation et renvoie un **message d’erreur**.

Pour afficher la simulation sans enregistrer de vidéo, ajoutez `--display`.
La fenêtre s'ouvre alors à la moitié de la résolution configurée et s'arrête
après l'animation de fin **sans** rejouer le ralenti :

```bash
uv run python -m app.cli run --display
````

---

## 📦 Générer un batch de vidéos

Génère plusieurs combats en série avec seeds et armes aléatoires. Les fichiers
sont nommés `YYYY_MM_DD_HH_MM_SS-<armeA>-VS-<armeB>-<arme_vainqueur>_win.mp4` et
enregistrés dans `./generated` par défaut.

Exemple pour créer **10 vidéos TikTok** :

```bash
uv run python -m app.cli batch \
  --count 10
```

---

## ⚙️ Configuration personnalisée

- **Armes** disponibles : `app/weapons/`
- Chaque arme expose un attribut `speed` (float) indiquant la vitesse de son projectile ou de son effet. Par exemple, la `Shuriken` voyage à `600.0` unités par seconde, tandis que la `Katana` reste à `0.0`.
- **IA** : agressive, kite, support, teamplay.
- **Équipes** : passer de 1v1 → 2v2 → FFA → Battle Royale.
- **Rendu** : couleurs, arènes, effets visuels.
- **Yeux** : définir `"show_eyes": false` dans `app/config.json` pour les masquer.
- **Boucle & fin de match** : animation de victoire puis segment ralenti configurable, démarrant au plus tôt après l'intro.
- **Configuration externe** : `app/config.json` regroupe canvas, palette (bleu/orange), HUD (titre, watermark) et paramètres d'**end screen** (textes, slow-mo, fade...).
- **FPS / résolution** : ajuster `canvas` dans `app/config.json`.

## 🎬 Intro animation

Avant chaque match, une courte séquence présente les armes en jeu.

- **Configuration** : `IntroConfig` permet d'ajuster les durées, les fonctions d'interpolation et la touche de saut. Utilisez `allow_skip=False` pour imposer l'animation.
- **Assets** : le logo et les images d'armes sont chargés depuis `assets/`. L'option CLI `--intro-weapons` permet de remplacer les visuels par défaut.
- **Skip** : appuyez sur `Échap` pour passer l'animation.

### Développer une nouvelle arme

1. **Skin** : placer l'image dans `assets/` puis la charger via `load_sprite`.
2. **Paramètres** : définir vitesse, rayon et dégâts directement dans la classe de l'arme.
3. **Attache à une boule** : instancier l'arme et l'enregistrer auprès d'un joueur dans `run_match`.

---

## 🧪 Lancer les tests

```bash
uv run pytest
```

---

## 📱 Conseils TikTok

- Utiliser une musique tendance et des hashtags pertinents.
- Préparer une miniature accrocheuse.
- Publier régulièrement pour alimenter l’algorithme.

## 🛠️ Troubleshooting

- **Aucune fenêtre** : forcer `SDL_VIDEODRIVER=dummy` pour l’exécution headless.
- **Pas de vidéo générée** : vérifier l’installation de `imageio-ffmpeg`.
- **Erreur SDL** : installer les bibliothèques systèmes `SDL2`.

---

## 📌 Roadmap

- [ ] ⚔️ Plus d’armes : lance, masse, bouclier.
- [ ] 🧠 IA avancée : esquives, focus multiple, comportements dynamiques.
- [ ] 🏟 Arènes procédurales pour varier les vidéos.
- [ ] 🎥 Slow-mo automatique sur le dernier hit.
- [ ] 🔁 Boucles TikTok parfaites (match → replay → restart).
- [ ] 🔊 Effets sonores & ASMR optimisés.
- [ ] 🌈 FX visuels : particules, traînées, éclats.
- [ ] 🤖 Mode _full batch_ : générer **100+ vidéos par nuit**.

---

## 📜 Licence

[MIT](LICENSE)
