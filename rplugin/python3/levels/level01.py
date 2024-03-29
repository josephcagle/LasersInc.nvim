
from random import random

from gameobject.entities import AlienMinion, BeefyMinion
from LasersInc import GAME_HEIGHT, GAME_WIDTH, BASE_UPS

from levels.base_level import Level


class Level01(Level):
    def __init__(self, entities, debug):
        super().__init__()
        self.cycle_progression = 0.0
        self.entities = entities
        self.debug = debug
        self.cycle_length = BASE_UPS * 3

    def update(self, delta_multiplier, tick_interval_count):
        self.cycle_progression += delta_multiplier
        if self.cycle_progression > self.cycle_length:
            self.cycle_progression -= self.cycle_length
            if random() > 0.5:
                self.entities.add_entity(BeefyMinion(GAME_WIDTH + 10, int(random()*GAME_HEIGHT)))
            else:
                self.entities.add_entity(AlienMinion(GAME_WIDTH + 10, int(random()*GAME_HEIGHT)))
            # self.debug(f"entities: {list(map(lambda x: str(x), self.entities))}")
            if self.cycle_length > 1 * BASE_UPS:
                self.cycle_length *= 0.9

