import sc2, math
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sc2.data import ActionResult, Attribute, Race
import random
from contextlib import suppress

class SC2Bot(sc2.BotAI):
    def __init__(self):
        self.iterbymin = 168
        self.reservedWorkers = []

    def select_target(self) -> Point2:
        if self.enemy_structures:
            return random.choice(self.enemy_structures).position
        return self.enemy_start_locations[0]

    async def on_step(self, iteration):
        await self.worker_manager()
        await self.production_manager()

    async def worker_manager(self):
        await self.distribute_workers()
        if (
            len(self.units(UnitTypeId.DRONE)) > 13
            and self.supply_left < 2
            and self.already_pending(UnitTypeId.OVERLORD) < 2
            and self.can_afford(UnitTypeId.OVERLORD)
        ):
            self.train(UnitTypeId.OVERLORD)
        if self.can_afford(UnitTypeId.DRONE) and self.supply_workers < 20:
            self.train(UnitTypeId.DRONE)

    async def information_manager(self):
        pass

    async def production_manager(self):
        await self.building_manager()

    async def strategy_manager(self):
        pass
    
    async def map_grid(self):
        pass

    async def combat_manager(self):
        pass

    async def building_manager(self):
        if (
            self.gas_buildings.amount + self.already_pending(UnitTypeId.EXTRACTOR) == 0
            and self.can_afford(UnitTypeId.EXTRACTOR)
            and self.workers
        ):
            drone: Unit = self.workers.random
            target: Unit = self.vespene_geyser.closest_to(drone)
            drone.build_gas(target)

        with suppress(AssertionError):
            if self.townhalls.amount < 2 and (self.can_afford(UnitTypeId.HATCHERY) and self.units(UnitTypeId.DRONE).amount > 5) and self.already_pending(UnitTypeId.HATCHERY) < 1:
                    planned_hatch_locations: Set[Point2] = {placeholder.position for placeholder in self.placeholders}
                    my_structure_locations: Set[Point2] = {structure.position for structure in self.structures}
                    enemy_structure_locations: Set[Point2] = {structure.position for structure in self.enemy_structures}
                    blocked_locations: Set[
                        Point2
                    ] = my_structure_locations | planned_hatch_locations | enemy_structure_locations
                    expansions = self.expansion_locations_list
                    for exp_pos in expansions:
                        if exp_pos in blocked_locations:
                            continue
                        for drone in self.workers.collecting:
                            drone: Unit
                            drone.build(UnitTypeId.HATCHERY, exp_pos)
                            break
            
run_game(
    maps.get("AcropolisLE"),
    [Bot(Race.Zerg, SC2Bot()), Computer(Race.Terran, Difficulty.Hard)],
    realtime=False,
)