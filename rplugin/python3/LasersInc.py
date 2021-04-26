
import pynvim
from time import sleep

import builtins

GAME_WIDTH = 80
GAME_HEIGHT = 18

@pynvim.plugin
class LasersInc(object):

    def __init__(self, nvim):
        self.nvim = nvim

        self.frame_num = 0
        self.TARGET_FPS = 20

        self.frame_buf = []
        self.EMPTY_BUF = []
        for i in builtins.range(GAME_HEIGHT):
            self.EMPTY_BUF.append(" "*GAME_WIDTH)

        self.running = False

        self.entities = []
        self.spaceship = None


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

        self.running = True
        while self.running:
            self.nvim.command('doautocmd User GameTick')
            sleep(1 / self.TARGET_FPS)


    @pynvim.command('LasersIncStop')
    def stop(self):
        self.running = False


    def render(self):
        self.nvim.current.buffer[0:GAME_HEIGHT] = self.frame_buf

    def buf_draw(self, x, y, lines):
        x = round(x)
        y = round(y)
        for i in range(len(lines)):
            new_screen_line = self.frame_buf[y+i][0:x]
            new_screen_line += lines[i]
            new_screen_line += self.frame_buf[y+i][(x+len(lines[i])):]
            self.frame_buf[y+i] = new_screen_line
            # chars = list(lines[i])
            # for j in range(len(chars)):



    @pynvim.autocmd('User', pattern='GameTick', sync=True)
    def on_game_tick(self, *args):
        self.frame_num += 1
        self.frame_buf = self.EMPTY_BUF.copy()
        self.calc_updates()
        self.draw_objects()
        self.render()


    def calc_updates(self):
        for entity in self.entities:

            if isinstance(entity, Bullet):
                if (entity.x + entity.dx < 0           or
                    entity.y + entity.dy < 0           or
                    entity.x + entity.dx > GAME_WIDTH  or
                    entity.y + entity.dy > GAME_HEIGHT   ):
                    self.entities.remove(entity)
                    continue

            entity.update()

    def draw_objects(self):
        self.buf_draw(0, 0, ['frame %s' % self.frame_num])
        for entity in self.entities:
            self.buf_draw(entity.x, entity.y, entity.sprite())


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
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.width = width
        self.height = height


    def update(self):
        self.x += self.dx
        self.y += self.dy
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
                ">  ",
                "==>",
                ">  "
                ]

    def update(self):
        self.dx *= 0.95
        self.dy *= 0.85
        Entity.update(self)

    def shoot_bullet(self):
        bullet = Bullet(self.x+3, self.y+1,  self.dx+4, self.dy)
        self.bullets.append(bullet)
        return bullet


class Bullet(Entity):
    def __init__(self, x, y, dx, dy):
        Entity.__init__(self, x, y, 1, 1)
        self.dx = dx
        self.dy = dy

    def sprite(self):
        return ["-"]

    def update(self):
        self.dx *= 0.98
        self.dy *= 0.8
        self.x += self.dx
        self.y += self.dy

