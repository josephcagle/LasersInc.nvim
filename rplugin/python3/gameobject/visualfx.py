
import math

from LasersInc import GAME_HEIGHT, GAME_WIDTH
from base.visualfx import Particle, ParallaxBackground


from random import random
def sometimes(fraction):
    return fraction > random()


class Starfield(ParallaxBackground):
    def __init__(self, parallax_distance):
        self.parallax_distance = parallax_distance
        self.buf = []
        self.scroll_x = 0

        # generate starfield
        for i in range(GAME_HEIGHT):
            line = ""
            for j in range(GAME_WIDTH):
                line += ("." if sometimes(0.002) else " ")
            self.buf.append(line)


    def scroll(self, distance):
        transformed_distance = distance / self.parallax_distance
        scroll_n_pixels = round(self.scroll_x + transformed_distance) - round(self.scroll_x)

        # scroll n characters over
        for i in range(scroll_n_pixels):
            for j in range(len(self.buf)):
                self.buf[j] = self.buf[j][1:] + ("." if sometimes(0.002) else " ")

        self.scroll_x += transformed_distance


    def lines(self):
        return self.buf


class Explosion(Particle):
    def __init__(self, x, y, z_order):
        super().__init__(x, y, 3, 3, z_order)
        self.first_tick_interval_count = -1
        self.disable_hitbox = True

        self.frames = [
            [
                "   ",
                " o ",
                "   ",
            ],
            [
                " - ",
                "(0)",
                " - ",
            ],
            [
                "ooo",
                "oXo",
                "ooo",
            ],
            [
                "...",
                ".x.",
                "...",
            ],
            [
                "   ",
                " x ",
                "   ",
            ],
        ]

    def texture(self):
        if self.first_tick_interval_count < 0: return [""]
        num = self.get_animation_frame_num()
        if 0 <= num < len(self.frames):
            return self.frames[num]
        else:
            return [""]

    def update(self, delta_multiplier, tick_interval_count):
        super().update(delta_multiplier, tick_interval_count)
        if self.first_tick_interval_count < 0:
            self.first_tick_interval_count = tick_interval_count
        if self.get_animation_frame_num() >= len(self.frames) - 1:
            # the last frame has been shown, so
            self.delete_me = True

    def get_animation_frame_num(self):
        return math.floor(
            (self.last_tick_interval_count - self.first_tick_interval_count) / 2
        )

