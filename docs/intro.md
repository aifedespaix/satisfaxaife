# Intro animation

Ce document décrit l'architecture de l'animation d'introduction avant chaque match.

## IntroManager

- Précharge les assets nécessaires via `IntroAssets.load` : police, logo VS (`assets/vs.png`) et images des armes.
- Machine à états gérant les phases : `LOGO_IN`, `WEAPONS_IN`, `HOLD`, `FADE_OUT`, `DONE`.
- Méthodes `start`, `update(dt, events)`, `draw(surface, labels)` et `is_finished` orchestrent la séquence.
- Permet de passer l'intro via la touche de saut (Échap par défaut) quand `allow_skip=True`.

## IntroRenderer

- Calcule les positions et l'opacité des éléments selon le `progress` fourni par le gestionnaire.
- Utilise les paramètres d'`IntroConfig` pour les dimensions, les positions et les fonctions d'interpolation.
- Affiche le logo VS et les images des armes avec un slide-in et un glow avant un fade final.
- Les éléments restent visibles pendant `hold=1s` puis disparaissent via `fade_out=0.25s`.

## Tween / Easing

- Les transitions reposent sur des fonctions d'interpolation (`ease_out_back`, `ease_out_quad`, `fade`) définies dans `IntroConfig`.
- Le module utilitaire `app/core/tween.py` expose des easings génériques (`linear`, `ease_in_out_cubic`, ...`) réutilisables dans le moteur.
