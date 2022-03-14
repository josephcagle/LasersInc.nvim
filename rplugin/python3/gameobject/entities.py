
import math

from LasersInc import GAME_WIDTH, GAME_HEIGHT, TARGET_FPS
from base.entities import Entity, HealthyEntity
from base.visualfx import Particle
from gameobject.visualfx import Explosion

class Spaceship(HealthyEntity):
    def __init__(self):
        super().__init__(5, 8, 3, 3, 100)
        self.texture_offset_x = -1
        self.last_tick_interval_count = 0.0
        self.z_order = 1000
        self.bullets = []
        self.top_laser = SpaceshipLaser(self, 3, 0)
        self.bottom_laser = SpaceshipLaser(self, 3, 2)
        self.children.append(self.top_laser)
        self.children.append(self.bottom_laser)
        self.capacitor_charge = 8.0
        self.dying = False
        self.animation_progress = 0.0
        self.on_death = None

    def texture(self):
        frames = [ [
           r" \>",
            " ==>",
            " />"
        ],
        [
           r"-\>",
            " ==>",
            "-/>"
        ],
        [
           r"=\>",
            " ==>",
            "=/>"
        ],
        [
           r"-\>",
            " ==>",
            "-/>"
        ]]
        return_val = frames[math.floor(self.last_tick_interval_count) % 4]

        if self.dying:
            if math.floor(self.animation_progress * 100) % 30 < 15:
                return [""]
            else:
                return return_val

        return return_val

    def update(self, delta_multiplier, tick_interval_count):
        self.last_tick_interval_count = tick_interval_count

        self.dx *= 1 - (0.05 * delta_multiplier)
        self.dy *= 1 - (0.15 * delta_multiplier)
        super().update(delta_multiplier, tick_interval_count)

        if self.dying:
            if self.animation_progress >= 1:
                if self.top_laser.on:
                    self.top_laser.toggle()
                if self.bottom_laser.on:
                    self.bottom_laser.toggle()
                self.delete_me = True
                self.on_death()
                return
            self.animation_progress += 1/10 * delta_multiplier

        if self.top_laser.on:
            self.capacitor_charge -= 0.2
        if self.bottom_laser.on:
            self.capacitor_charge -= 0.2

        if self.capacitor_charge <= 0:
            self.top_laser.on = False
            self.top_laser.disable_hitbox = True
            self.bottom_laser.on = False
            self.bottom_laser.disable_hitbox = True

        if self.capacitor_charge <= 8.0:
            self.capacitor_charge += 0.02

    def shoot_bullet(self):
        bullet = Bullet(self.x+3, self.y+1,  self.dx+4, self.dy, 10)
        bullet.parent = self
        self.bullets.append(bullet)
        self.children.append(bullet)

    def toggle_top_laser(self):
        self.top_laser.toggle()
    def toggle_bottom_laser(self):
        self.bottom_laser.toggle()

    def die(self):
        self.dying = True
        expl = Explosion(self.x, self.y, self.z_order+1)
        expl.parent = self
        self.children.append(expl)

    def on_event(self, event_type, *data):
        if event_type == "intersection" and isinstance(data[0], Enemy):
            self.die()


class Bullet(Entity):
    def __init__(self, x, y, dx, dy, damage_value):
        super().__init__(x, y, 1, 1)
        self.ttl = TARGET_FPS * 4
        self.dx = dx
        self.dy = dy
        self.base_damage_value = damage_value / math.hypot(dx, dy)

    def texture(self):
        return ["-"]

    def update(self, delta_multiplier, tick_interval_count):
        self.dx *= 1 - (0.02 * delta_multiplier)
        self.dy *= 1 - (0.2 * delta_multiplier)
        self.x += self.dx * delta_multiplier
        self.y += self.dy * delta_multiplier

        if ( self.x < 0 and self.dx < 0           or
             self.y < 0 and self.dy < 0           or
             self.x > GAME_WIDTH  and self.dx > 0 or
             self.y > GAME_HEIGHT and self.dx > 0 ):
            self.delete_me = True
            return

        self.ttl -= 1 * delta_multiplier
        if self.ttl <= 0:
            self.delete_me = True

    def get_damage_value(self):
        return self.base_damage_value * math.hypot(self.dx, self.dy)

    def on_event(self, event_type, *data):
        if event_type == "intersection" and not isinstance(data[0], Bullet):
            expl = Explosion(self.x-1, self.y-1, self.z_order+1)
            expl.parent = self
            self.children.append(expl)

            self.delete_me = True


class SpaceshipLaser(Entity):
    def __init__(self, parent_spaceship, offset_x, offset_y):

        super().__init__(
            parent_spaceship.x + offset_x, parent_spaceship.y + offset_y,
            int(GAME_WIDTH - parent_spaceship.x - offset_x), 1
        )
        self.base_damage_value = 100
        self.parent = parent_spaceship
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.on = False
        self.disable_hitbox = True

    def toggle(self):
        self.on = not self.on
        self.disable_hitbox = not self.disable_hitbox

    def texture(self):
        if self.on:
            return [f"X{'='*int(self.width-1)}"]
        return [""]

    def update(self, delta_multiplier, tick_interval_count):
        self.x = self.parent.x + self.offset_x
        self.y = self.parent.y + self.offset_y
        self.width = GAME_WIDTH - self.x

    def on_event(self, event_type, *data):
        if event_type == "intersection" and isinstance(data[0], Enemy):
            data[0].health -= self.base_damage_value
            expl = Explosion(data[0].x, self.y-1, self.z_order+1)
            expl.parent = self
            self.children.append(expl)


class Enemy(HealthyEntity):
    def __init__(self, x, y, width, height, health):
        super().__init__(x, y, width, height, health)


class AlienMinion(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 2, 2, 10)
        self.direction = math.pi
        self.speed = 0.4

    def update(self, delta_multiplier, tick_interval_count):
        self.direction += math.pi/TARGET_FPS
        self.dx = self.speed * math.cos(self.direction) * 1.25 # attempt to correct for
        self.dy = self.speed * math.sin(self.direction) * 0.8  # char aspect ratio
        self.x += self.dx
        self.y += self.dy


    def texture(self):
        return [
                "oo",
                "''"
                ]

    def on_event(self, event_type, *data):
        if event_type == "intersection":
            other_entity = data[0]

            if isinstance(other_entity, Bullet):
                self.health -= other_entity.get_damage_value()
            if self.health <= 0: self.delete_me = True

            if isinstance(other_entity, Spaceship):
                self.delete_me = True




