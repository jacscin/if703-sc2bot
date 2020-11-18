import sc2, math
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units

class SC2Bot(sc2.BotAI):
    def __init__(self):
        self.iterbymin = 168

    async def on_step(self, iteration):
        if not self.townhalls:
            all_attack_units: Units = self.units.of_type(
                {UnitTypeId.DRONE, UnitTypeId.QUEEN, UnitTypeId.ZERGLING, UnitTypeId.CORRUPTOR, UnitTypeId.BROODLORD}
            )
            for unit in all_attack_units:
                unit.attack(self.enemy_start_locations[0])
            return
        else:
            hq: Unit = self.townhalls.first

        if self.can_afford(UnitTypeId.SPAWNINGPOOL) and self.already_pending(UnitTypeId.SPAWNINGPOOL) + self.structures.filter(lambda structure: structure.type_id == UnitTypeId.SPAWNINGPOOL and structure.is_ready).amount == 0:
            worker_candidates = self.workers.filter(lambda worker: (worker.is_collecting or worker.is_idle) and worker.tag not in self.unit_tags_received_action)
            # Worker_candidates can be empty
            if worker_candidates:
                map_center = self.game_info.map_center
                position_towards_map_center = self.start_location.towards(map_center, distance=5)
                placement_position = await self.find_placement(UnitTypeId.SPAWNINGPOOL, near=position_towards_map_center, placement_step=1)
                # Placement_position can be None
                if placement_position:
                    build_worker = worker_candidates.closest_to(placement_position)
                    build_worker.build(UnitTypeId.SPAWNINGPOOL, placement_position)

        # Build Extractor
        if self.gas_buildings.amount + self.already_pending(UnitTypeId.EXTRACTOR) < 2:
            if self.can_afford(UnitTypeId.EXTRACTOR):
                drone: Unit = self.workers.random
                target: Unit = self.vespene_geyser.closest_to(drone.position)
                drone.build_gas(target)
        #Create Lair
        if self.structures(UnitTypeId.SPAWNINGPOOL).ready:
            if not self.townhalls(UnitTypeId.LAIR) and not self.townhalls(UnitTypeId.HIVE) and hq.is_idle:
                if self.can_afford(UnitTypeId.LAIR):
                    hq.build(UnitTypeId.LAIR)

        await self.queen(hq)
        await self.baneling()
        await self.larvae()
        await self.roach()
        await self.drone()
    
    async def queen(self, hq):
        if self.structures(UnitTypeId.SPAWNINGPOOL).ready:
            if not self.units(UnitTypeId.QUEEN) and hq.is_idle:
                if self.can_afford(UnitTypeId.QUEEN):
                    hq.train(UnitTypeId.QUEEN)
        
        for queen in self.units(UnitTypeId.QUEEN).idle:
            if queen.energy >= 25:
                queen(AbilityId.EFFECT_INJECTLARVA, hq)

    async def baneling(self):
        pass

    async def larvae(self):
        larvae: Units = self.larva
        for loop_larva in larvae:
            if loop_larva.tag in self.unit_tags_received_action:
                continue
            if self.can_afford(UnitTypeId.DRONE):
                loop_larva.train(UnitTypeId.DRONE)
                break
            else:
                break

        if self.supply_left < 2:
            if larvae and self.can_afford(UnitTypeId.OVERLORD):
                larvae.random.train(UnitTypeId.OVERLORD)
                return

    async def roach(self):
        pass

    async def drone(self):
        pass
            
run_game(
    maps.get("AcropolisLE"),
    [Bot(Race.Zerg, SC2Bot()), Computer(Race.Terran, Difficulty.Hard)],
    realtime=False,
)