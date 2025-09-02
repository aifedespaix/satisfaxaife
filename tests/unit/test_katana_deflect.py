from dataclasses import dataclass, field

import pygame

from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.weapons.base import WeaponEffect, WorldView
from app.weapons.effects import OrbitingSprite
from app.world.physics import PhysicsWorld
from app.world.projectiles import Projectile


@dataclass
class DummyView(WorldView):
    positions: dict[EntityId, Vec2]
    enemies: dict[EntityId, EntityId]
    damage: dict[EntityId, float] = field(default_factory=dict)

    def get_enemy(self, owner: EntityId) -> EntityId | None:
        return self.enemies.get(owner)

    def get_position(self, eid: EntityId) -> Vec2:
        return self.positions[eid]

    def get_velocity(self, eid: EntityId) -> Vec2:
        return (0.0, 0.0)

    def get_health_ratio(self, eid: EntityId) -> float:
        return 1.0

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:
        self.damage[eid] = self.damage.get(eid, 0.0) + damage.amount

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:
        return None

    def spawn_effect(self, effect: WeaponEffect) -> None:
        return None

    def add_speed_bonus(self, eid: EntityId, bonus: float) -> None:  # noqa: D401
        return None

    def spawn_projectile(
        self,
        owner: EntityId,
        position: Vec2,
        velocity: Vec2,
        radius: float,
        damage: Damage,
        knockback: float,
        ttl: float,
        sprite: pygame.Surface | None = None,
        spin: float = 0.0,
        trail_color: tuple[int, int, int] | None = None,
        acceleration: float = 0.0,
    ) -> WeaponEffect:
        raise NotImplementedError

    def iter_projectiles(self, excluding: EntityId | None = None) -> list[ProjectileInfo]:  # noqa: D401
        return []


def test_katana_deflects_projectile() -> None:
    pygame.init()
    world = PhysicsWorld()
    owner = EntityId(1)
    enemy = EntityId(2)
    positions = {owner: (0.0, 0.0), enemy: (30.0, 0.0)}
    enemies = {owner: enemy, enemy: owner}
    view = DummyView(positions, enemies)
    sprite = pygame.Surface((20, 20))
    katana = OrbitingSprite(
        owner=owner,
        damage=Damage(0),
        sprite=sprite,
        radius=10.0,
        angle=0.0,
        speed=0.0,
    )
    projectile = Projectile.spawn(
        world,
        owner=enemy,
        position=(10.0, 0.0),
        velocity=(-100.0, 0.0),
        radius=1.0,
        damage=Damage(5),
        knockback=0.0,
        ttl=1.0,
    )
    projectile.ttl = 0.1
    pos = (float(projectile.body.position.x), float(projectile.body.position.y))
    assert katana.collides(view, pos, float(projectile.shape.radius))

    katana.deflect_projectile(view, projectile, timestamp=0.0)

    assert projectile.owner == owner
    assert projectile.body.velocity.x == 100.0
    assert projectile.ttl == projectile.max_ttl
    assert view.damage == {}

    projectile.on_hit(view, enemy, timestamp=0.1)
    assert view.damage[enemy] == 5


def test_katana_does_not_deflect_body_hit() -> None:
    pygame.init()
    world = PhysicsWorld()
    owner = EntityId(1)
    enemy = EntityId(2)
    positions = {owner: (0.0, 0.0), enemy: (30.0, 0.0)}
    enemies = {owner: enemy, enemy: owner}
    view = DummyView(positions, enemies)
    sprite = pygame.Surface((20, 20))
    katana = OrbitingSprite(
        owner=owner,
        damage=Damage(0),
        sprite=sprite,
        radius=10.0,
        angle=0.0,
        speed=0.0,
    )
    projectile = Projectile.spawn(
        world,
        owner=enemy,
        position=(0.0, 0.0),
        velocity=(-100.0, 0.0),
        radius=1.0,
        damage=Damage(5),
        knockback=0.0,
        ttl=1.0,
    )
    projectile.ttl = 0.1
    pos = (float(projectile.body.position.x), float(projectile.body.position.y))
    assert not katana.collides(view, pos, float(projectile.shape.radius))

    projectile.on_hit(view, owner, timestamp=0.0)
    assert view.damage[owner] == 5
