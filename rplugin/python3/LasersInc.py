
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

        self.player_lives = 3
        self.game_over = False


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
            self.background_layers.append(Starfield(1+i))

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

        # guarantee at least part of the sprite is on-screen
        if y > GAME_HEIGHT or x > GAME_WIDTH:
            return
        if y + len(lines) < 0 or x + len(max(lines, key=len)) < 0:
            return

        for i in range(len(lines)):
            if y+i < 0:
                continue
            if y+i >= GAME_HEIGHT:
                break

            # as the system is currently implemented, some lines are longer
            # than others, so check and make sure this particular line
            # isn't completely off-screen
            if x + len(lines[i]) < 0:
                continue

            old_screen_line = self.frame_buf[y+i]

            new_screen_line = ""
            if x > 0:
                new_screen_line += old_screen_line[0:x]

            for j in range(len(lines[i])):
                if x+j < 0:
                    continue
                if x+j >= GAME_WIDTH:
                    break

                if transparent and lines[i][j] == " ":
                    new_screen_line += old_screen_line[x+j]
                else:
                    new_screen_line += lines[i][j]

            if x + len(lines[i]) < GAME_WIDTH:
                new_screen_line += old_screen_line[(x+len(lines[i])):]

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
            self.background_layers[i].scroll(1.4 * delta_multiplier)

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

        if sometimes(1 / (TARGET_FPS * 20)):
            self.entities.append(AlienMinion(GAME_WIDTH - 2, int(random()*GAME_HEIGHT)))

        self.update_statusline()


    def draw_objects(self):
        for i in range(len(self.background_layers)):
            self.buf_draw(0, 0, self.background_layers[i].lines(), transparent=True)

        # self.buf_draw(0, 0, ['frame %s' % self.frame_num], transparent=True)
        for entity in self.entities:
            self.buf_draw(entity.x,
                          entity.y,
                          entity.sprite(),
                          transparent=entity.transparent)


    @pynvim.autocmd('User', pattern="h_Pressed")
    def accelerate_spaceship_left(self):
        self.spaceship.dx -= 0.8
    @pynvim.autocmd('User', pattern="j_Pressed")
    def accelerate_spaceship_down(self):
        self.spaceship.dy += 0.8
    @pynvim.autocmd('User', pattern="k_Pressed")
    def accelerate_spaceship_up(self):
        self.spaceship.dy -= 0.8
    @pynvim.autocmd('User', pattern="l_Pressed")
    def accelerate_spaceship_right(self):
        self.spaceship.dx += 0.8

    @pynvim.autocmd('User', pattern="Space_Pressed")
    def shoot_player_bullet(self):
        self.entities.append(self.spaceship.shoot_bullet())

    @pynvim.autocmd('User', pattern="Shift_o_Pressed")
    def toggle_player_top_laser(self):
        self.spaceship.toggle_top_laser()
    @pynvim.autocmd('User', pattern="o_Pressed")
    def toggle_player_bottom_laser(self):
        self.spaceship.toggle_bottom_laser()


    def update_statusline(self):
        if self.game_over:
            self.nvim.command("set statusline=%#StatusLine#\\ %#StatusLineRed#\\ Game\\ Over\\ %#StatusLine#")
        else:
            new_statusline = "\\ %#StatusLine#\\ %#StatusLineTitle#\\ Lives:\\ %#StatusLineRed#"
            new_statusline += "\\ ".join(["♥︎"] * self.player_lives) + ("\\ " * (3-self.player_lives)*2)
            new_statusline += "\\ %#StatusLine#"
            new_statusline += "%="
            new_statusline += "%#StatusLineTitle#\\ Capacitor\\ Charge\\ %#StatusLineGreen#"
            new_statusline += "\\ " * (8 - max(int(self.spaceship.capacitor_charge), 0))
            new_statusline += "]" * int(self.spaceship.capacitor_charge)
            new_statusline += "\\ %#StatusLine#\\ "

            # self.nvim.command("echom " + new_statusline)
            self.nvim.command("set statusline=" + new_statusline)



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
        # if self.x < 0:
        #     self.x = 0
        #     self.dx = 0
        # elif self.x + self.width > GAME_WIDTH:
        #     self.x = GAME_WIDTH - self.width
        #     self.dx = 0
        # if self.y < 0:
        #     self.y = 0
        #     self.dy = 0
        # elif self.y + self.height > GAME_HEIGHT:
        #     self.y = GAME_HEIGHT - self.height
        #     self.dy = 0

    def sprite(self):
        raise NotImplementedError()


    def is_intersecting_with(self, other):
        # check whether one is to the left of another
        if (self.x + self.width < other.x) or (other.x + other.width < self.x):
            return False
        # check whether one is above another
        if (self.y + self.height < other.y) or (other.y + other.height < self.y):
            return False

        return True


class Spaceship(Entity):
    def __init__(self):
        Entity.__init__(self, 0, 0, 3, 3)
        self.bullets = []
        self.top_laser = False
        self.bottom_laser = False
        self.capacitor_charge = 8.0

    def sprite(self):
        return_val = [
                "\\>",
                "==>",
                "/>"
                ]

        if self.top_laser:
            return_val[0] += "X" + ("=" * (GAME_WIDTH - (int(self.x)+3)))
        if self.bottom_laser:
            return_val[2] += "X" + ("=" * (GAME_WIDTH - (int(self.x)+3)))

        return return_val

    def update(self, delta_multiplier):
        self.dx *= 1 - (0.05 * delta_multiplier)
        self.dy *= 1 - (0.15 * delta_multiplier)
        Entity.update(self, delta_multiplier)

        if self.top_laser:
            self.capacitor_charge -= 0.2
        if self.bottom_laser:
            self.capacitor_charge -= 0.2

        if self.capacitor_charge <= 0:
            self.top_laser = False
            self.bottom_laser = False

        if self.capacitor_charge <= 8.0:
            self.capacitor_charge += 0.02

    def shoot_bullet(self):
        bullet = Bullet(self.x+3, self.y+1,  self.dx+4, self.dy)
        self.bullets.append(bullet)
        return bullet

    def toggle_top_laser(self):
        self.top_laser = not self.top_laser
    def toggle_bottom_laser(self):
        self.bottom_laser = not self.bottom_laser



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


class Enemy(Entity):
    def __init__(self, x, y, width, height):
        Entity.__init__(self, x, y, width, height)

class AlienMinion(Enemy):
    def __init__(self, x, y):
        Enemy.__init__(self, x, y, 2, 2)
        self.update_count = 0.0

    def update(self, delta_multiplier):
        self.update_count += delta_multiplier
        if int(self.update_count) % int(TARGET_FPS * 1.5) == 0:
            self.y += 1
        elif (int(self.update_count) - int(TARGET_FPS * 1.0)) \
            % int(TARGET_FPS * 1.5) == 0:
            self.y -= 1

    def sprite(self):
        return [
                "oo",
                "''"
                ]



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

from random import random
def sometimes(fraction):
    return fraction > random()


