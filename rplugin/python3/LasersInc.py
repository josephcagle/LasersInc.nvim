
GAME_WIDTH = 80
GAME_HEIGHT = 18

# Everything in the game will assume the game is running at BASE_UPS ups,
# and then we will scale everything up or down using delta_multiplier.
# DON'T change this from 60 without redoing all the code to adjust
BASE_UPS = 60

TARGET_FPS = 60
UPDATES_PER_FRAME = 3
TARGET_UPS = TARGET_FPS * UPDATES_PER_FRAME

import pynvim
from time import sleep, time_ns
import math
import builtins

import sys, os
sys.path.append(f"{os.getcwd()}/rplugin/python3")

from sound.sound import SoundManager, SOUND_SUPPORTED

from gameobject.entities import Spaceship, AlienMinion
from gameobject.visualfx import Starfield

from levels.level01 import Level01


from random import random
def sometimes(fraction):
    return fraction > random()


@pynvim.plugin
class LasersInc(object):

    def __init__(self, nvim):
        self.nvim = nvim

        self.prefs = {}
        self.prefs["controls"] = {}

        self.frame_num = 0
        self.tick_interval_count = 0.0

        # placeholder values so things don't break before the first frame
        self.last_frame_timestamp = time_ns()
        self.time_since_last_frame = 1
        self.current_real_fps = 60

        self.frame_buf = []
        self.EMPTY_BUF = []
        for i in builtins.range(GAME_HEIGHT):
            self.EMPTY_BUF.append(" "*GAME_WIDTH)
        self.highlight_namespace_id = self.nvim.api.create_namespace("LasersInc")

        self.running = False

        self.entities = None
        self.spaceship = None
        self.background_layers = []

        self.player_lives = 3
        self.game_over = False

        self.game_paused = False

        self.sound_manager = SoundManager() if SOUND_SUPPORTED else None

        self.menu = Menu(
            self.nvim,
            30,
            5,
            "Welcome, Adventurer!",
            ["LASERS INC"],
            ["Start Game"],
            lambda x: self.menu_selection_handler()
        )

        self.level = None

        self.debug_text = [""]

    def menu_selection_handler(self):
        self.menu.hide()
        if SOUND_SUPPORTED:
            self.sound_manager.fade_out_music(1000)


    def print_message(self, message):
        if '\n' in message:
            message_lines = message.split('\n')
            for line in message_lines:
                self.nvim.command('echom "%s"\n' % line.replace('"', '\\"'))
        self.nvim.command('echom "%s"\n' % message.replace('"', '\\"'))
    ## test
    # self.printMessage('"ain\'t it workin\' yet?"')

    def load_controls(self):
        prefs_file = open("data/game_controls.properties", "r")
        lines = prefs_file.readlines()

        # self.nvim.command("source disable.vim")

        for line in lines:
            if line.startswith("#") or len(line.strip()) == 0:
                continue
            parts = line.split("=")
            key = parts[0]
            value = "=".join(parts[1:]).strip()
            self.prefs["controls"][key] = value
            self.nvim.command(f"nnoremap <silent> {value} :doautocmd User {key}<CR>")
        # self.print_message(str(self.prefs))

        self.nvim.command("nnoremap <silent> <CR> :doautocmd User EnterPressed<CR>")


    @pynvim.command('LasersInc', nargs='*', range='', sync=False)
    def start(self, args, range):
        if self.running:
            raise RuntimeError("LasersInc is already running")

        self.load_controls()

        # create screen
        self.frame_buf = self.EMPTY_BUF.copy()
        screen = self.nvim.current.buffer
        screen[:] = None
        for lineNum in builtins.range(len(self.frame_buf)):
            screen.append(self.frame_buf[lineNum])
        del screen[0]  # get rid of first line

        # reset state
        self.entities = EntityList()

        def spawn_new_spaceship():
            self.spaceship = Spaceship()
            self.spaceship.on_death = spawn_new_spaceship
            self.entities.add_entity(self.spaceship)
            self.player_lives -= 1
            if self.player_lives < 0:
                # TODO: game over
                self.player_lives = 0

        spawn_new_spaceship()
        self.player_lives += 1

        self.background_layers = []
        for i in builtins.range(4):
            self.background_layers.append(Starfield(1+i))

        self.level = Level01(self.entities, self.print_message)

        self.menu.show()

        if SOUND_SUPPORTED:
            self.sound_manager.load_music("main_menu")
            self.sound_manager.set_music_volume(0.5)
            self.sound_manager.play_music(loop=True)

        self.running = True
        while self.running:
            self.nvim.command('doautocmd User GameTick')
            sleep(1 / TARGET_FPS)



    @pynvim.command('LasersIncStop')
    def stop(self):
        self.running = False


    def render(self):
        self.nvim.api.buf_clear_namespace(0, self.highlight_namespace_id, 0,-1)

        self.nvim.current.buffer[0:GAME_HEIGHT] = self.frame_buf

        for entity in \
            sorted(
                self.entities.get_all_in_tree(),
                key = lambda entity: entity.z_order
            ):
            for highlight in entity.highlights():
                highlight_line_num = highlight.line_num \
                    + math.floor(entity.y) \
                    + entity.texture_offset_y
                if highlight_line_num < 0 or highlight_line_num >= GAME_HEIGHT:
                    continue

                highlight_col_start = highlight.col_start \
                    + math.floor(entity.x) \
                    + entity.texture_offset_x
                if highlight_col_start < 0:
                    highlight_col_start = 0
                if highlight_col_start > GAME_WIDTH:
                    continue

                highlight_col_end = highlight.col_end \
                    + math.floor(entity.x) \
                    + entity.texture_offset_x
                if highlight_col_end < 0:
                    continue
                if highlight_col_end > GAME_WIDTH:
                    highlight_col_end = GAME_WIDTH

                self.nvim.api.buf_add_highlight(0,
                    self.highlight_namespace_id,
                    highlight.highlight_group,
                    highlight_line_num,
                    highlight_col_start,
                    highlight_col_end
                )

    def buf_draw(self, x, y, lines, transparent=False):
        x = math.floor(x)
        y = math.floor(y)

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
        now = time_ns()
        self.time_since_last_frame = now - self.last_frame_timestamp
        self.last_frame_timestamp = now
        self.current_real_fps = 1e9 / self.time_since_last_frame

        self.frame_num += 1
        self.frame_buf = self.EMPTY_BUF.copy()
        self.draw_objects()
        self.render()
        for i in range(UPDATES_PER_FRAME):
            self.calc_updates()

    def delete_if_requested(self, entity):
        if entity.delete_me:
            if entity.parent:
                entity.parent.children.remove(entity)
            elif entity in self.entities:
                self.entities.remove_entity(entity)
            else: raise RuntimeError(f"can't find parent for entity: {entity}")

            # save orphans
            self.entities.extend(entity.children)
            entity.parent = None

            return True

        return False


    # recursive helper function for calc_updates
    def update_entity(self, entity, delta_multiplier, tick_interval_count):
        if self.delete_if_requested(entity): return

        entity.update(delta_multiplier, tick_interval_count)

        if self.delete_if_requested(entity): return

        for other_entity in self.entities.get_all_in_tree():
            if entity is other_entity: continue
            if entity.disable_hitbox or other_entity.disable_hitbox: continue
            if entity.is_intersecting_with(other_entity):
                # call the event listener
                # (TODO: maybe rename the method later)
                entity.on_event("intersection", other_entity)

        for child in entity.children:
            self.update_entity(child, delta_multiplier, tick_interval_count)


    def calc_updates(self):
        if self.game_paused:
            return

        scale_factor = TARGET_FPS/self.current_real_fps
        self.debug_text[0] = "{0:.3}".format(scale_factor)

        # scale everything to BASE_FPS ups, then apply scale_factor
        delta_multiplier = BASE_UPS/TARGET_UPS * scale_factor

        self.tick_interval_count += delta_multiplier

        for i in range(len(self.background_layers)):
            self.background_layers[i].scroll(1.2 * delta_multiplier)

        for entity in self.entities:
            self.update_entity(entity, delta_multiplier, self.tick_interval_count)

        if not self.menu or not self.menu.shown:
            self.level.update(delta_multiplier, self.tick_interval_count)

        self.update_statusline()


    def draw_objects(self):
        for background_layer in self.background_layers:
            self.buf_draw(0, 0, background_layer.lines(), transparent=True)

        # self.buf_draw(0, 0, ['frame %s' % self.frame_num], transparent=True)

        for entity in \
            sorted(
                self.entities.get_all_in_tree(),
                key = lambda entity: entity.z_order
            ):
            self.buf_draw(entity.x + entity.texture_offset_x,
                          entity.y + entity.texture_offset_y,
                          entity.texture(),
                          transparent=entity.transparent)

        self.buf_draw(0, 0, [f"{'{0:.3}'.format(self.current_real_fps)} FPS"])
        self.buf_draw(0, 1, self.debug_text)


    @pynvim.autocmd('User', pattern="LeftPressed")
    def on_left_pressed(self):
        self.process_input("LeftPressed")

    @pynvim.autocmd('User', pattern="DownPressed")
    def on_down_pressed(self):
        self.process_input("DownPressed")

    @pynvim.autocmd('User', pattern="UpPressed")
    def on_up_pressed(self):
        self.process_input("UpPressed")

    @pynvim.autocmd('User', pattern="RightPressed")
    def on_right_pressed(self):
        self.process_input("RightPressed")

    @pynvim.autocmd('User', pattern="EnterPressed")
    def on_enter_pressed(self):
        self.process_input("EnterPressed")

    @pynvim.autocmd('User', pattern="MainCannonTriggered")
    def on_main_cannon_triggered(self):
        self.process_input("MainCannonTriggered")

    @pynvim.autocmd('User', pattern="TopLaserTriggered")
    def on_top_laser_triggered(self):
        self.process_input("TopLaserTriggered")

    @pynvim.autocmd('User', pattern="BottomLaserTriggered")
    def on_bottom_laser_triggered(self):
        self.process_input("BottomLaserTriggered")


    def process_input(self, event_type):
        if self.menu and self.menu.shown:
            if event_type == "EnterPressed":
                self.menu.confirm_option()
            elif event_type == "DownPressed":
                self.menu.select_next_option()
            elif event_type == "UpPressed":
                self.menu.select_previous_option()
            return

        if event_type == "LeftPressed":
            self.accelerate_spaceship_left()
        elif event_type == "DownPressed":
            self.accelerate_spaceship_down()
        elif event_type == "UpPressed":
            self.accelerate_spaceship_up()
        elif event_type == "RightPressed":
            self.accelerate_spaceship_right()
        elif event_type == "MainCannonTriggered":
            self.spaceship.shoot_bullet()
        elif event_type == "TopLaserTriggered":
            self.spaceship.toggle_top_laser()
        elif event_type == "BottomLaserTriggered":
            self.spaceship.toggle_bottom_laser()



    def accelerate_spaceship_left(self):
        self.spaceship.dx -= \
            math.hypot(self.spaceship.dx, self.spaceship.dy) * 0.1 + 0.35
    def accelerate_spaceship_down(self):
        self.spaceship.dy += \
            math.hypot(self.spaceship.dx, self.spaceship.dy) * 0.1 + 0.35
    def accelerate_spaceship_up(self):
        self.spaceship.dy -= \
            math.hypot(self.spaceship.dx, self.spaceship.dy) * 0.1 + 0.35
    def accelerate_spaceship_right(self):
        self.spaceship.dx += \
            math.hypot(self.spaceship.dx, self.spaceship.dy) * 0.1 + 0.35


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


class EntityList:
    def __init__(self):
        self.list = []

    def add_entity(self, entity):
        self.list.append(entity)

    def extend(self, list):
        self.list.extend(list)

    def remove_entity(self, entity):
        # TODO: validation
        self.list.remove(entity)

    def __iter__(self):
        return self.list.__iter__()

    def get_all_in_tree(self):
        # copy-pasted from the internet somewhere lol
        flat_map = lambda f, xs: [y for ys in xs for y in f(ys)]

        return flat_map(lambda entity: entity.get_all_descendants_plus_self(), self)





class Menu:
    def __init__(self, nvim, width, height, title, display_lines, options, callback):
        self.nvim = nvim
        self.width = width
        self.height = height
        self.title = title.strip()
        self.display_lines = display_lines
        self.options = list(map(lambda line: line.strip(), options))
        self.callback = callback

        self.shown = False
        self.current_selected_option = 0
        self.win = None
        self.buf = nvim.api.create_buf(False, False)

        self.draw()


    def show(self):
        if self.shown: return
        self.shown = True

        self.win = self.nvim.api.open_win(self.buf, False, {
            "relative": "editor",
            "width": self.width,
            "height": self.height,
            "row": round(GAME_HEIGHT / 2 - (self.height / 2)),
            "col": round(GAME_WIDTH / 2 - (self.width / 2)),
            "border": "rounded"
        })

    def hide(self):
        self.nvim.api.win_close(self.win, True)
        self.shown = False

    def draw(self):
        self.nvim.api.buf_set_lines(self.buf, 0, -1, False, self._build_menu())

    def select_next_option(self):
        self.current_selected_option += 1
        if self.current_selected_option == len(self.options):
            self.current_selected_option = 0
        self.draw()

    def select_previous_option(self):
        self.current_selected_option -= 1
        if self.current_selected_option == -1:
            self.current_selected_option = len(self.options)-1
        self.draw()

    def confirm_option(self):
        self.callback(self.current_selected_option)
        pass

    def _build_menu(self):
        def pad(s):
            num_spaces = self.width - len(s)
            return (" " * math.floor(num_spaces/2)) + s + (" " * math.ceil(num_spaces/2))

        lines = []

        title = self.title.strip()
        if len(title) > 0:
            lines.append(pad(title))
            lines.append("")

        for line_to_display in self.display_lines:
            lines.append(pad(line_to_display))
        lines.append("")

        for i, option in enumerate(self.options):
            selected = i == self.current_selected_option
            lines.append(pad(f"{'>' if selected else ' '} {option}"))

        return lines

