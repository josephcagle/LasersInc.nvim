
from random import random

from gameobject.entities import AlienMinion
from LasersInc import TARGET_FPS, GAME_HEIGHT, GAME_WIDTH

from levels.base_level import Level


class Level01(Level):
    def __init__(self, entities, debug):
        self.cycle_progression = 0.0
        self.entities = entities
        self.debug = debug

    def update(self, delta_multiplier, tick_interval_count):
        self.cycle_progression += delta_multiplier
        if self.cycle_progression > TARGET_FPS * 3:
            self.cycle_progression -= TARGET_FPS * 3
            self.entities.add_entity(AlienMinion(GAME_WIDTH - 10, int(random()*GAME_HEIGHT)))
            # self.debug(f"entities: {list(map(lambda x: str(x), self.entities))}")

