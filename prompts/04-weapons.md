Ouvre une PR : **feat/weapons-and-ai**
But : gameplay minimal 1v1.

À faire :

- `app/weapons/base.py` :
  - classe Weapon(name, cooldown, dmg: Damage) avec timer
  - WorldView Protocol : get_enemy(owner_id), get_position(eid), deal_damage(eid, Damage), apply_impulse(eid, vx, vy), spawn_projectile(...)
- `app/weapons/katana.py` :
  - arc 70°, portée ~140, cooldown 0.6s, dmg 18, knockback 220, enregistre `katana`
- `app/weapons/shuriken.py` :
  - projectile speed 600, ttl 0.8s, dmg 10, knock 120, radius 8, enregistre `shuriken`
- `app/ai/policy.py` :
  - SimplePolicy(style="aggressive"/"kiter") → (accel, face, fire) ; katana colle/orbite, shuriken kite/attaque (seuil d’angle ~18°)
- `app/game/match.py` :
  - intègre IA + armes, gestion dégâts/knockback, morts, gagnant
- `app/render/renderer.py` :
  - impacts : flash court (80 ms), particules radiales (6–10), micro screen-shake léger
  - HP bars : animation ~200 ms à la baisse
  - yeux : blink plus fort sur gros impact

Critères d’acceptation :

- CI verte.
- `uv run python -m app.cli run --weapon-a katana --weapon-b shuriken --seconds 10` produit une vidéo où un gagnant est visible, HP chutent, impacts visibles.
