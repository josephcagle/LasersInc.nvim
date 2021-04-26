
import pynvim
from time import sleep

import builtins

@pynvim.plugin
class LasersInc(object):

    def __init__(self, nvim):
        self.nvim = nvim

        self.frame_num = 0
        self.TARGET_FPS = 20

        self.GAME_WIDTH = 80
        self.GAME_HEIGHT = 18
        self.frame_buf = []
        self.EMPTY_BUF = []
        for i in builtins.range(self.GAME_HEIGHT):
            self.EMPTY_BUF.append(" "*self.GAME_WIDTH)

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
        self.nvim.current.buffer[0:(self.GAME_HEIGHT-1)] = self.frame_buf

    def buf_draw(self, x, y, lines):
        x = round(x)
        y = round(y)
        for i in range(len(lines)):
            new_screen_line = self.frame_buf[i][0:x]
            new_screen_line += lines[i]
            new_screen_line += self.frame_buf[i][(x+len(lines[i])):]
            self.frame_buf[y+i] = new_screen_line
            # chars = list(lines[i])
            # for j in range(len(chars)):



    @pynvim.autocmd('User', pattern='GameTick', eval='expand("<afile>")', sync=True)
    def on_game_tick(self, *args):
        self.frame_num += 1
        self.frame_buf = self.EMPTY_BUF.copy()
        self.calc_updates()
        self.draw_objects()
        self.render()


    def calc_updates(self):
        for entity in self.entities:
            entity.x += entity.dx
            entity.y += entity.dy
            if entity.x < 0:
                entity.x = 0
                entity.dx = 0
            elif entity.x + entity.width > self.GAME_WIDTH:
                entity.x = self.GAME_WIDTH - entity.width
                entity.dx = 0
            if entity.y < 0:
                entity.y = 0
                entity.dy = 0
            elif entity.y + entity.height > self.GAME_HEIGHT:
                entity.y = self.GAME_HEIGHT - entity.height
                entity.dy = 0

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


class Entity:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.width = width
        self.height = height

    def sprite(self):
        raise NotImplementedError()


class Spaceship(Entity):
    def __init__(self):
        Entity.__init__(self, 0, 0, 3, 3)

    def sprite(self):
        return [
                ">  ",
                "==>",
                ">  "
                ]



