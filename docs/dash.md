# Dash

Le _dash_ est une impulsion latérale brève. Les collisions et dégâts
continuent de s'appliquer normalement pendant toute sa durée.

## Paramètres par défaut

- **Vitesse** : `800` unités/s
- **Durée** : `0,2` s
- **Recharge** : `3` s

## Utilisation

- **Joueur** : pressez `Maj gauche` pour déclencher un dash.
- **IA** : déclenche automatiquement le dash lorsqu'un projectile est prévu à
  moins de `0,3` s et que la recharge est terminée.
- **Audio** : un bref son `dash.ogg` est joué avec des variations de hauteur pour
  éviter la monotonie.

## Effet visuel

Pendant un dash, la balle génère une animation de traînée explosive : des
clones semi-transparents ("ghosts") suivent sa trajectoire et
disparaissent en quelques images, rendant l'action nette et éphémère.
