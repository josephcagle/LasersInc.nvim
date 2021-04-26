
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

        self.running = False


    @pynvim.command('LasersInc', nargs='*', range='', sync=False)
    def start(self, args, range):
        if self.running:
            raise RuntimeError("LasersInc is already running")

        # create screen
        self.frame_buf = []
        for i in builtins.range(self.GAME_HEIGHT):
            self.frame_buf.append(" "*self.GAME_WIDTH)
        screen = self.nvim.current.buffer
        screen[:] = None
        for lineNum in builtins.range(len(self.frame_buf)):
            screen.append(self.frame_buf[lineNum])
        del screen[0]  # get rid of first line

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
        self.calc_updates()
        self.draw_objects()
        self.render()


    def calc_updates(self):
        pass

    def draw_objects(self):
        self.buf_draw(0, 0, ['frame %s' % self.frame_num])





