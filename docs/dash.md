# Dash

Le _dash_ est une impulsion latérale brève. Les collisions infligent des
dégâts proportionnels à la vitesse au moment de l'impact et une attaque
portée pendant un dash devient un **coup critique**.

## Paramètres par défaut

- **Vitesse** : `800` unités/s
- **Durée** : `0,2` s
- **Recharge** : `3` s pour les armes de contact, `6` s pour les armes à distance

## Orientation

- **Mêlée offensive** : le dash cherche à réduire la distance jusqu'à
  l'adversaire. La trajectoire pointe directement vers lui.
- **Mêlée défensive** : le dash s'oriente latéralement afin d'esquiver les
  projectiles tout en restant à portée de frappe.
- **Armes de contact** : les dashs en arrière sont évités pour conserver la
  pression sur l'adversaire.

```text
Offensif :  [Vous] ───▶ [Ennemi]
Défensif : projectile ─▶ (dash latéral)
```

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
