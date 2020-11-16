import sc2, math
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *

class SC2Bot(sc2.BotAI):
    def __init__(self):
        self.iterbymin = 168

    async def on_step(self, iteration):
        self.iteration = iteration

run_game(
    maps.get("AcropolisLE"),
    [Bot(Race.Zerg, SC2Bot()), Computer(Race.Terran, Difficulty.Hard)],
    realtime=False,
)