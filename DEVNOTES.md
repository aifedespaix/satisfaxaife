# Dev Notes

## Armes basées sur un sprite

- Ajouter l'image dans `assets/`.
- Charger l'asset avec `load_sprite` et passer la surface au projectile ou à `OrbitingSprite`.
- Les vitesses, rayons et dégâts sont des attributs définis dans la classe de l'arme.
- Pour lier une arme à une boule : créer l'instance et l'enregistrer dans le `weapon_registry`, puis associer l'arme au joueur dans `run_match`.
