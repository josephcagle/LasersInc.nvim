
import pynvim
from time import sleep
from numpy import inf
import math

import builtins

GAME_WIDTH = 80
GAME_HEIGHT = 18

TARGET_FPS = 30

@pynvim.plugin
class LasersInc(object):

    def __init__(self, nvim):
        self.nvim = nvim

        self.prefs = {}
        self.prefs["controls"] = {}

        self.frame_num = 0

        self.frame_buf = []
        self.EMPTY_BUF = []
        for i in builtins.range(GAME_HEIGHT):
            self.EMPTY_BUF.append(" "*GAME_WIDTH)

        self.running = False

        self.entities = EntityList()
        self.spaceship = None
        self.background_layers = []

        self.player_lives = 3
        self.game_over = False

        self.game_paused = False

        self.menu = Menu(
            self.nvim,
            30,
            5,
            "Welcome, Adventurer!",
            ["LASERS INC"],
            ["Start Game"],
            lambda x: self.menu.hide()
        )


    def print_message(self, message):
        self.nvim.command('echom "%s"\n' % message.replace('"', '\\"'))
    ## test
    # self.printMessage('"ain\'t it workin\' yet?"')

    def load_controls(self):
        prefs_file = open("data/game_controls.properties", "r")
        lines = prefs_file.readlines()

        self.nvim.command("source disable.vim")

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
        self.spaceship = Spaceship()
        self.entities.add_entity(self.spaceship)

        self.background_layers = []
        for i in builtins.range(4):
            self.background_layers.append(Starfield(1+i))

        self.menu.show()

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


    # recursive helper function for calc_updates
    def update_entity(self, entity, delta_multiplier):
        if entity.delete_me:
            if entity.parent:
                entity.parent.children.remove(entity)
            elif entity in self.entities:
                self.entities.remove_entity(entity)
            else: raise RuntimeError("can't find parent for entity")
            return

        entity.update(delta_multiplier)

        if entity.delete_me:
            if entity.parent:
                entity.parent.children.remove(entity)
            elif entity in self.entities:
                self.entities.remove_entity(entity)
            else: raise RuntimeError("can't find parent for entity")
            return

        for other_entity in self.entities.get_all_in_tree():
            if entity is other_entity: continue
            if entity.is_intersecting_with(other_entity):
                # call the event listener
                # (TODO: maybe rename the method later)
                entity.on_event("intersection", other_entity)

        if isinstance(entity, Spaceship):
            if entity.top_laser or entity.bottom_laser:

                for other_entity in self.entities.get_all_in_tree():
                    if other_entity is entity:
                        continue

                    if ( other_entity.y
                            <=
                         entity.y + (0 if entity.top_laser else 2)
                            <=
                         other_entity.y + other_entity.height-1
                       ) \
                    and \
                       ( entity.x + 2
                            <=
                         other_entity.x + other_entity.width-1
                       ):

                        other_entity.delete_me = True

        if len(entity.children) > 0:
            for child in entity.children:
                self.update_entity(child, delta_multiplier)


    def calc_updates(self):
        if self.game_paused:
            return

        delta_multiplier = 1.0  # TODO: calculate based on real UPS

        for i in range(len(self.background_layers)):
            self.background_layers[i].scroll(1.4 * delta_multiplier)

        for entity in self.entities:
            self.update_entity(entity, delta_multiplier)

        if sometimes(1 / (TARGET_FPS * 20)) and not (self.menu and self.menu.shown):
            self.entities.add_entity(AlienMinion(GAME_WIDTH - 2, int(random()*GAME_HEIGHT)))

        self.update_statusline()


    def draw_objects(self):
        for i in range(len(self.background_layers)):
            self.buf_draw(0, 0, self.background_layers[i].lines(), transparent=True)

        # self.buf_draw(0, 0, ['frame %s' % self.frame_num], transparent=True)

        for entity in \
            sorted(
                self.entities.get_all_in_tree(),
                key = lambda entity: entity.z_order
            ):
            self.buf_draw(entity.x,
                          entity.y,
                          entity.sprite(),
                          transparent=entity.transparent)


    @pynvim.autocmd('User', pattern="LeftPressed")
    def on_left_pressed(self):
        self.accelerate_spaceship_left()

    @pynvim.autocmd('User', pattern="DownPressed")
    def on_down_pressed(self):
        if self.menu and self.menu.shown:
            self.menu.select_next_option()
            return
        self.accelerate_spaceship_down()

    @pynvim.autocmd('User', pattern="UpPressed")
    def on_up_pressed(self):
        if self.menu and self.menu.shown:
            self.menu.select_previous_option()
            return
        self.accelerate_spaceship_up()

    @pynvim.autocmd('User', pattern="RightPressed")
    def on_right_pressed(self):
        self.accelerate_spaceship_right()

    @pynvim.autocmd('User', pattern="EnterPressed")
    def on_enter_pressed(self):
        if self.menu and self.menu.shown:
            self.menu.confirm_option()


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

    @pynvim.autocmd('User', pattern="MainCannonTriggered")
    def shoot_player_bullet(self):
        self.spaceship.shoot_bullet()

    @pynvim.autocmd('User', pattern="TopLaserTriggered")
    def toggle_player_top_laser(self):
        self.spaceship.toggle_top_laser()
    @pynvim.autocmd('User', pattern="BottomLaserTriggered")
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



class EntityList:
    def __init__(self):
        self.list = []

    def add_entity(self, entity):
        self.list.append(entity)

    def remove_entity(self, entity):
        # TODO: validation
        self.list.remove(entity)

    def __iter__(self):
        return self.list.__iter__()

    def get_all_in_tree(self):
        # copy-pasted from the internet somewhere lol
        flat_map = lambda f, xs: [y for ys in xs for y in f(ys)]

        return flat_map(lambda entity: entity.get_all_descendants_plus_self(), self)


class Entity:
    def __init__(self, x, y, width, height, transparent=True):
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.width = width
        self.height = height
        self.transparent = transparent
        self.z_order = 0
        self.delete_me = False
        self.children = []
        self.parent = None


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

    def on_event(self, event_type, *data):
        pass

    def sprite(self):
        raise NotImplementedError()


    def get_all_descendants(self):
        current_list = []
        current_list.extend(self.children)
        for child in self.children:
            current_list.extend(child.get_all_descendants())
        return current_list

    def get_all_descendants_plus_self(self):
        list = self.get_all_descendants()
        list.append(self)
        return list


    def is_intersecting_with(self, other):
        # check whether one is to the left of another
        if (self.x + self.width < other.x) or (other.x + other.width < self.x):
            return False
        # check whether one is above another
        if (self.y + self.height < other.y) or (other.y + other.height < self.y):
            return False

        return True


class HealthyEntity(Entity):
    def __init__(self, x, y, width, height, health):
        super().__init__(x, y, width, height)
        self.max_health = health
        self.health = health


class Spaceship(HealthyEntity):
    def __init__(self):
        super().__init__(4, 8, 3, 3, 100)
        # spaceship should always be on top
        self.z_order = inf
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
        bullet = Bullet(self.x+3, self.y+1,  self.dx+4, self.dy, 10)
        bullet.parent = self
        self.bullets.append(bullet)
        self.children.append(bullet)

    def toggle_top_laser(self):
        self.top_laser = not self.top_laser
    def toggle_bottom_laser(self):
        self.bottom_laser = not self.bottom_laser



class Bullet(Entity):
    def __init__(self, x, y, dx, dy, damage_value):
        super().__init__(x, y, 1, 1)
        self.ttl = TARGET_FPS * 4
        self.dx = dx
        self.dy = dy
        self.base_damage_value = damage_value / math.hypot(dx, dy)

    def sprite(self):
        return ["-"]

    def update(self, delta_multiplier):
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
            self.delete_me = True


class Enemy(HealthyEntity):
    def __init__(self, x, y, width, height, health):
        super().__init__(x, y, width, height, health)

class AlienMinion(HealthyEntity):
    def __init__(self, x, y):
        super().__init__(x, y, 2, 2, 10)
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

    def on_event(self, event_type, *data):
        if event_type == "intersection":
            other_entity = data[0]
            if isinstance(other_entity, Bullet):
                self.health -= other_entity.get_damage_value()
            if self.health <= 0: self.delete_me = True



class Background:
    def lines(self):
        raise NotImplementedError()

class ParallaxBackground(Background):
    def __init__(self, parallax_distance):
        self.parallax_distance = parallax_distance

    # this method handles parallax_distance calculations
    def moveCameraRight(self):
        raise NotImplementedError()

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

    import math
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

