import sc2, math
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sc2.data import ActionResult, Attribute, Race
import random
from contextlib import suppress

class SC2Bot(sc2.BotAI):
    def __init__(self):
        self.iterbymin = 168
        self.assigned_queens = {}
        self.scouts = {}
        self.last_scout = 0
        self.enemy_count = 0
        self.army_command = 0 #0: idle, 1: attack, 2: defend

    def select_target(self) -> Point2:
        if self.enemy_structures:
            return random.choice(self.enemy_structures).position
        return self.enemy_start_locations[0]

    async def on_step(self, iteration):
        self.iteration = iteration
        await self.worker_manager()
        await self.production_manager()
        await self.combat_manager()

    async def worker_manager(self):
        await self.distribute_workers()
        
        if (
            self.can_afford(UnitTypeId.ZERGLING)
            and self.larva
            and self.supply_army + self.supply_workers > 20
            and self.units(UnitTypeId.ZERGLING).amount < (12 * self.townhalls.amount)):
                self.larva.random.train(UnitTypeId.ZERGLING)

        if (
            self.can_afford(UnitTypeId.ROACH)
            and self.larva
            and self.supply_army + self.supply_workers > 27
            and self.units(UnitTypeId.ROACH).amount < (6 * self.townhalls.amount)):
                self.larva.random.train(UnitTypeId.ROACH)
        
        if self.larva and self.can_afford(UnitTypeId.HYDRALISK) and self.structures(UnitTypeId.HYDRALISKDEN).ready:
            self.larva.random.train(UnitTypeId.HYDRALISK)

        await self.queen_manager()
        
        if (
            self.supply_left < 2
            and not self.already_pending(UnitTypeId.OVERLORD)
            and self.can_afford(UnitTypeId.OVERLORD)
        ):
            self.train(UnitTypeId.OVERLORD)

        if self.can_afford(UnitTypeId.DRONE) and self.supply_workers < min(80, (16 * self.townhalls.amount) + 3):
            self.train(UnitTypeId.DRONE)

    async def queen_manager(self):
        if (
            self.can_afford(UnitTypeId.QUEEN)
            and self.units(UnitTypeId.QUEEN).amount < self.townhalls.amount * 5
            and self.townhalls.first.is_idle
        ):
            self.townhalls.first.train(UnitTypeId.QUEEN)
        for queen in self.units(UnitTypeId.QUEEN).idle:
            if queen.energy >= 25:
                queen(AbilityId.EFFECT_INJECTLARVA, self.townhalls.first)

    async def production_manager(self):
        await self.building_manager()

    async def combat_manager(self):
        await self.strategy_manager()
        await self.upgrade_manager()

        # Attack
        if(self.army_command == 1):
            for unit in self.units:
                if ((unit.type_id != UnitTypeId.OVERLORD)
                    and (unit.type_id != UnitTypeId.DRONE)
                ):
                    if self.enemy_units.amount > 0:
                        unit.attack(self.enemy_units.closest_to(unit))
                    elif self.enemy_structures.amount > 0:
                        unit.attack(self.enemy_structures.closest_to(unit))
                    else:
                        unit.attack(self.enemy_start_locations[0])

        # Defend
        if(self.army_command == 2):
            for unit in self.units:
                if ((unit.type_id != UnitTypeId.OVERLORD)
                    and (unit.type_id != UnitTypeId.DRONE)
                ):
                    closest_enemies = self.enemy_units.closer_than(5, unit)
                    if len(closest_enemies) > 0:
                        target = random.choice(closest_enemies)
                        closest_units = self.units(UnitTypeId.ZERGLING).n_closest_to_distance(target.position, 5,
                                                                                        round(len(closest_enemies) * 1.25))
                        for backup_unit in closest_units:
                            backup_unit.attack(target)

            for idle_unit in self.units(UnitTypeId.ZERGLING).idle:
                idle_unit.move(self.townhalls[0].position)

    async def strategy_manager(self):
        # Scouting
        if (self.iteration / self.iterbymin) > self.last_scout:
            self.last_scout += 1
            self.enemy_count = self.enemy_count * 0.9
            to_be_removed = []
            for scout in self.scouts:
                if scout not in [unit.tag for unit in self.units]:
                    to_be_removed.append(scout)

            for scout in to_be_removed:
                del self.scouts[scout]

        if self.townhalls(UnitTypeId.LAIR).exists:
            for scout in self.units.tags_in(self.scouts.keys()).idle:
                scout(AbilityId.BEHAVIOR_GENERATECREEPON)
            
        if self.units(UnitTypeId.OVERLORD).idle.amount > 0:
            enemy_locations = sorted(self.expansion_locations_list, key=lambda el: el.distance_to(self.enemy_start_locations[0]))
            for location in enemy_locations[:5]:
                for scout in self.units(UnitTypeId.OVERLORD).idle:
                    if location not in self.scouts.values():
                        if scout.tag not in self.scouts:
                            self.do(scout.move(location))
                            self.scouts[scout.tag] = location
        self.army_command = 0

        # Attacking
        self.enemy_count = max(self.enemy_count, self.enemy_units.amount)
        print(self.units({UnitTypeId.ZERGLING, UnitTypeId.ROACH, UnitTypeId.QUEEN}).amount, self.enemy_count)
        if(self.units({UnitTypeId.ZERGLING, UnitTypeId.ROACH, UnitTypeId.QUEEN}).amount
            > (self.enemy_count + 10)
        ):
            self.army_command = 1

        # Defending
        for building in self.structures():
            if (self.enemy_units.closer_than(30, building).amount > 0
                and (self.units.amount - self.units({UnitTypeId.OVERLORD, UnitTypeId.DRONE}).amount) > 10
            ):
                self.army_command = 2

        print(self.army_command)

    async def upgrade_manager(self):
        if self.structures(UnitTypeId.HATCHERY).ready:
            if self.can_afford(AbilityId.RESEARCH_PNEUMATIZEDCARAPACE):
                if not self.already_pending_upgrade(UpgradeId.OVERLORDSPEED):
                    hatchery = self.structures(UnitTypeId.HATCHERY).ready.first
                    hatchery.research(UpgradeId.OVERLORDSPEED)

        if self.structures(UnitTypeId.HATCHERY).ready:
            if self.can_afford(AbilityId.RESEARCH_BURROW):
                if not self.already_pending_upgrade(UpgradeId.BURROW):
                    hatchery = self.structures(UnitTypeId.HATCHERY).ready.first
                    hatchery.research(UpgradeId.BURROW)

        if (self.structures(UnitTypeId.HATCHERY).ready
            and self.structures(UnitTypeId.SPAWNINGPOOL).ready
            and self.structures(UnitTypeId.LAIR).amount + self.structures(UnitTypeId.HIVE).amount + self.already_pending(UnitTypeId.LAIR) == 0
            and self.can_afford(UnitTypeId.LAIR)
        ):
            hatchery = self.structures(UnitTypeId.HATCHERY).ready.first
            hatchery.build(UnitTypeId.LAIR)

        if (self.structures(UnitTypeId.LAIR).ready
            and self.supply_used > 130
            and self.units(UnitTypeId.INFESTATIONPIT).amount + self.already_pending(UnitTypeId.INFESTATIONPIT) == 0
            and self.can_afford(UnitTypeId.INFESTATIONPIT)
            and self.townhalls.amount >= 2
        ):
            await self.build (
                    UnitTypeId.INFESTATIONPIT,
                    near=self.townhalls.first.position.towards(self.game_info.map_center, 7)
                    )

        hydra_dens = self.structures(UnitTypeId.HYDRALISKDEN)
        if hydra_dens:
            for hydra_den in hydra_dens.ready.idle:
                if self.already_pending_upgrade(UpgradeId.EVOLVEGROOVEDSPINES) == 0 and self.can_afford(
                    UpgradeId.EVOLVEGROOVEDSPINES
                ):
                    hydra_den.research(UpgradeId.EVOLVEGROOVEDSPINES)
                elif self.already_pending_upgrade(UpgradeId.EVOLVEMUSCULARAUGMENTS) == 0 and self.can_afford(
                    UpgradeId.EVOLVEMUSCULARAUGMENTS
                ):
                    hydra_den.research(UpgradeId.EVOLVEMUSCULARAUGMENTS)

    async def building_manager(self):
        if (
            self.gas_buildings.amount + self.already_pending(UnitTypeId.EXTRACTOR) == 0
            and self.can_afford(UnitTypeId.EXTRACTOR)
            and self.workers
        ):
            drone: Unit = self.workers.random
            target: Unit = self.vespene_geyser.closest_to(drone)
            drone.build_gas(target)

        th = {UnitTypeId.NEXUS, UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE, UnitTypeId.COMMANDCENTER, UnitTypeId.ORBITALCOMMAND, UnitTypeId.PLANETARYFORTRESS}
        if (
            self.townhalls.amount <= self.enemy_structures(th).amount
            and self.can_afford(UnitTypeId.HATCHERY)
            and not self.already_pending(UnitTypeId.HATCHERY)
        ):
            await self.expand_now()
        
        if (
            self.can_afford(UnitTypeId.SPAWNINGPOOL)
            and self.structures(UnitTypeId.SPAWNINGPOOL).amount + self.already_pending(UnitTypeId.SPAWNINGPOOL) == 0
            and self.townhalls.amount >= 2
        ):
            await self.build (
                UnitTypeId.SPAWNINGPOOL,
                near=self.townhalls.first.position.towards(self.game_info.map_center, 5)
            )
        
        if (
            self.units(UnitTypeId.SPAWNINGPOOL).ready.exists
            and self.can_afford(UnitTypeId.ROACHWARREN)
            and not self.already_pending(UnitTypeId.ROACHWARREN)
        ):
            await self.build (
                UnitTypeId.ROACHWARREN,
                near=self.townhalls.first.position.towards(self.game_info.map_center, 5)
            )

        if self.townhalls(UnitTypeId.LAIR).ready:
            if self.structures(UnitTypeId.HYDRALISKDEN).amount + self.already_pending(UnitTypeId.HYDRALISKDEN) == 0:
                if self.can_afford(UnitTypeId.HYDRALISKDEN):
                    await self.build(UnitTypeId.HYDRALISKDEN,  near=self.townhalls.first.position.towards(self.game_info.map_center, 5))

run_game(
    maps.get("AcropolisLE"),
    [Bot(Race.Zerg, SC2Bot()), Computer(Race.Terran, Difficulty.Hard)],
    realtime=False,
)