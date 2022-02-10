
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
        self.disable_hitbox = False
        self.delete_me = False
        self.children = []
        self.parent = None


    def update(self, delta_multiplier, tick_interval_count):
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

    def texture(self):
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

    def die(self):
        raise NotImplementedError()


