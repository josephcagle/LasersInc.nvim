
from base.entities import Entity

class Particle(Entity):
    def __init__(self, x, y, width, height, z_order):
        super().__init__(x, y, width, height)
        self.last_tick_interval_count = 0.0
        self.z_order = z_order

    def texture(self):
        raise NotImplementedError()

    def update(self, delta_multiplier, tick_interval_count):
        self.last_tick_interval_count = tick_interval_count


class Background:
    def lines(self):
        raise NotImplementedError()

class ParallaxBackground(Background):
    def __init__(self, parallax_distance):
        self.parallax_distance = parallax_distance

    # this method handles parallax_distance calculations
    def moveCameraRight(self):
        raise NotImplementedError()

