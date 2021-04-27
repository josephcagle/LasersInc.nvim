
import pynvim
from time import sleep
from numpy import inf

import builtins

GAME_WIDTH = 80
GAME_HEIGHT = 18

TARGET_FPS = 30

@pynvim.plugin
class LasersInc(object):

    def __init__(self, nvim):
        self.nvim = nvim

        self.frame_num = 0

        self.frame_buf = []
        self.EMPTY_BUF = []
        for i in builtins.range(GAME_HEIGHT):
            self.EMPTY_BUF.append(" "*GAME_WIDTH)

        self.running = False

        self.entities = []
        self.spaceship = None
        self.background_layers = []


    @pynvim.command('LasersInc', nargs='*', range='', sync=False)
    def start(self, args, range):
        if self.running:
            raise RuntimeError("LasersInc is already running")

        # create screen
        self.frame_buf = self.EMPTY_BUF.copy()
        screen = self.nvim.current.buffer
        screen[:] = None
        for lineNum in builtins.range(len(self.frame_buf)):
            screen.append(self.frame_buf[lineNum])
        del screen[0]  # get rid of first line

        # reset state
        self.entities = []
        self.spaceship = Spaceship()
        self.entities.append(self.spaceship)

        self.background_layers = []
        for i in builtins.range(4):
            self.background_layers.append(Starfield(1 + i*1.2))

        self.running = True
        while self.running:
            self.nvim.command('doautocmd User GameTick')
            sleep(1 / TARGET_FPS)


    @pynvim.command('LasersIncStop')
    def stop(self):
        self.running = False


    def render(self):
        self.nvim.current.buffer[0:GAME_HEIGHT] = self.frame_buf

    def buf_draw(self, x, y, lines, transparent=False):
        x = int(x)
        y = int(y)

        if y + len(lines) > GAME_HEIGHT or \
           x + len(max(lines, key=len)) > GAME_WIDTH:
            raise Exception("cannot draw offscreen")

        for i in range(len(lines)):
            new_screen_line = self.frame_buf[y+i][0:x]

            if transparent:
                old_screen_line = self.frame_buf[y+i]
                for j in range(len(lines[i])):
                    if lines[i][j] == " ":
                        new_screen_line += old_screen_line[x+j]
                    else:
                        new_screen_line += lines[i][j]
            else:
                new_screen_line += lines[i]

            new_screen_line += self.frame_buf[y+i][(x+len(lines[i])):]
            self.frame_buf[y+i] = new_screen_line


    @pynvim.autocmd('User', pattern='GameTick', sync=True)
    def on_game_tick(self, *args):
        self.frame_num += 1
        self.frame_buf = self.EMPTY_BUF.copy()
        self.draw_objects()
        self.render()
        self.calc_updates()


    def calc_updates(self):
        delta_multiplier = 1.0  # TODO: calculate based on real UPS

        for i in range(len(self.background_layers)):
            self.background_layers[i].scroll(delta_multiplier)

        for entity in self.entities:
            if entity.ttl < 0:
                self.entities.remove(entity)
                continue

            entity.update(delta_multiplier)

            if isinstance(entity, Bullet):
                if (entity.x < 0           or
                    entity.y < 0           or
                    entity.x > GAME_WIDTH  or
                    entity.y > GAME_HEIGHT   ):
                    self.entities.remove(entity)
                    continue


    def draw_objects(self):
        for i in range(len(self.background_layers)):
            self.buf_draw(0, 0, self.background_layers[i].lines(), transparent=True)

        self.buf_draw(0, 0, ['frame %s' % self.frame_num])
        for entity in self.entities:
            self.buf_draw(entity.x,
                          entity.y,
                          entity.sprite(),
                          transparent=entity.transparent)


    @pynvim.autocmd('User', pattern="h_Pressed")
    def accelerate_spaceship_left(self):
        self.spaceship.dx -= 1
    @pynvim.autocmd('User', pattern="j_Pressed")
    def accelerate_spaceship_down(self):
        self.spaceship.dy += 1
    @pynvim.autocmd('User', pattern="k_Pressed")
    def accelerate_spaceship_up(self):
        self.spaceship.dy -= 1
    @pynvim.autocmd('User', pattern="l_Pressed")
    def accelerate_spaceship_right(self):
        self.spaceship.dx += 1

    @pynvim.autocmd('User', pattern="Space_Pressed")
    def shoot_player_bullet(self):
        self.entities.append(self.spaceship.shoot_bullet())


class Entity:
    def __init__(self, x, y, width, height, transparent=True, ttl=inf):
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.width = width
        self.height = height
        self.transparent = transparent
        self.ttl = ttl


    def update(self, delta_multiplier):
        self.x += self.dx * delta_multiplier
        self.y += self.dy * delta_multiplier
        if self.x < 0:
            self.x = 0
            self.dx = 0
        elif self.x + self.width > GAME_WIDTH:
            self.x = GAME_WIDTH - self.width
            self.dx = 0
        if self.y < 0:
            self.y = 0
            self.dy = 0
        elif self.y + self.height > GAME_HEIGHT:
            self.y = GAME_HEIGHT - self.height
            self.dy = 0

    def sprite(self):
        raise NotImplementedError()

class Spaceship(Entity):
    def __init__(self):
        Entity.__init__(self, 0, 0, 3, 3)
        self.bullets = []

    def sprite(self):
        return [
                "\\>",
                "==>",
                "/>"
                ]

    def update(self, delta_multiplier):
        self.dx *= 1 - (0.05 * delta_multiplier)
        self.dy *= 1 - (0.15 * delta_multiplier)
        Entity.update(self, delta_multiplier)

    def shoot_bullet(self):
        bullet = Bullet(self.x+3, self.y+1,  self.dx+4, self.dy)
        self.bullets.append(bullet)
        return bullet


class Bullet(Entity):
    def __init__(self, x, y, dx, dy):
        Entity.__init__(self, x, y, 1, 1, ttl = TARGET_FPS * 4)
        self.dx = dx
        self.dy = dy

    def sprite(self):
        return ["-"]

    def update(self, delta_multiplier):
        self.dx *= 1 - (0.02 * delta_multiplier)
        self.dy *= 1 - (0.2 * delta_multiplier)
        self.x += self.dx * delta_multiplier
        self.y += self.dy * delta_multiplier

        self.ttl -= 1 * delta_multiplier



class Background:
    def lines(self):
        raise NotImplementedError()

class ParallaxBackground(Background):
    def __init__(self, parallax_distance):
        self.parallax_distance = parallax_distance

    # this method handles parallax_distance calculations
    def moveCameraRight(self):
        raise NotImplementedError()

from math import sqrt
class Starfield(ParallaxBackground):
    def __init__(self, parallax_distance):
        self.parallax_distance = parallax_distance
        self.buf = []
        self.scroll_x = 0

        # generate starfield
        for i in range(GAME_HEIGHT):
            line = ""
            for j in range(GAME_WIDTH):
                line += ("." if sometimes(0.002 * sqrt(self.parallax_distance)) else " ")
            self.buf.append(line)


    def scroll(self, distance):
        transformed_distance = distance / self.parallax_distance
        scroll_n_pixels = round(self.scroll_x + transformed_distance) - round(self.scroll_x)

        # scroll n characters over
        for i in range(scroll_n_pixels):
            for j in range(len(self.buf)):
                self.buf[j] = self.buf[j][1:] + ("." if sometimes(0.002 * sqrt(self.parallax_distance)) else " ")

        self.scroll_x += transformed_distance


    def lines(self):
        return self.buf

from random import random
def sometimes(fraction):
    return fraction > random()


