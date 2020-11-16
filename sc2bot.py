import sc2, math
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *

class SC2Bot(sc2.BotAI):
    def __init__(self):
        self.iterbymin = 168

    async def on_step(self, iteration):
        self.iteration = iteration
        await self.queen()
        await self.baneling()
        await self.larvae()
        await self.roach()
        await self.drone()
    
    async def queen(self):
        pass

    async def baneling(self):
        pass

    async def larvae(self):
        pass

    async def roach(self):
        pass

    async def drone(self):
        pass
            
run_game(
    maps.get("AcropolisLE"),
    [Bot(Race.Zerg, SC2Bot()), Computer(Race.Terran, Difficulty.Hard)],
    realtime=False,
)