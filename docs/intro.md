# Intro animation

Ce document décrit l'architecture de l'animation d'introduction avant chaque match.

## IntroManager

- Précharge les assets nécessaires via `IntroAssets.load` : police, logo VS (`assets/vs.png`) et images des armes.
- Machine à états gérant les phases : `LOGO_IN`, `WEAPONS_IN`, `HOLD`, `FADE_OUT`, `DONE`.
- Méthodes `start`, `update(dt, events)`, `draw(surface, labels)` et `is_finished` orchestrent la séquence.
- Permet de passer l'intro via la touche de saut (Échap par défaut) quand `allow_skip=True`.
- Joue `versus.ogg` au lancement et `fight.ogg` lors du passage à la phase `FADE_OUT`.

## IntroRenderer

- Calcule les positions et l'opacité des éléments selon le `progress` fourni par le gestionnaire.
- Utilise les paramètres d'`IntroConfig` pour les dimensions, les positions et les fonctions d'interpolation.
- Affiche le logo VS centré au-dessus des noms des armes, à 50 % de sa taille d'origine.
- Les images des armes (40 % de la largeur de l'écran) apparaissent juste au-dessus de leur nom,
  tous deux alignés horizontalement légèrement sous le milieu de l'écran.
- Les noms sont rendus avec la police `assets/fonts/FightKickDemoRegular.ttf`.
- Les éléments apparaissent instantanément (`logo_in=0s`, `weapons_in=0s`), restent visibles pendant `hold=1s` puis disparaissent via `fade_out=0.25s`.

## Tween / Easing

- Les transitions reposent sur des fonctions d'interpolation (`ease_out_back`, `ease_out_quad`, `fade`) définies dans `IntroConfig`.
- Le module utilitaire `app/core/tween.py` expose des easings génériques (`linear`, `ease_in_out_cubic`, ...`) réutilisables dans le moteur.
