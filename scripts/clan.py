# pylint: disable=line-too-long
"""

TODO: Docs


"""

# pylint: enable=line-too-long

import os
import statistics
from random import choice, choices, randint, random, getrandbits
from typing import Literal

import i18n
import ujson

from scripts.cat.cats import Cat, create_cat, cat_class, BACKSTORIES
from scripts.cat.enums import CatRank, CatGroup, CatSocial
from scripts.cat.names import names
from scripts.cat.save_load import (
    save_cats,
    get_faded_ids,
)
from scripts.clan_package.clan_names import get_possible_clan_names
from scripts.clan_package.settings import save_clan_settings, load_clan_settings
from scripts.clan_package.settings.clan_settings import (
    reset_loaded_clan_settings,
    set_clan_setting,
)
from scripts.clan_resources.freshkill import FreshkillPile, Nutrition
from scripts.clan_resources.herb.herb_supply import HerbSupply
from scripts.clan_resources.point_of_interest import (
    load_pois,
    get_poi_save_dict,
    generate_and_add_new_poi,
    PoiType,
    get_poi_names_set,
    clear_pois,
)
from scripts.config import get_config
from scripts.events_module.future.future_event import FutureEvent
from scripts.events_module.generate_events import OngoingEvent
from scripts.game_structure import constants
from scripts.game_structure.game.save_load import safe_save, save_clanlist, read_clans
from scripts.game_structure.game.switches import (
    switch_set_value,
    switch_get_value,
    Switch,
)
from scripts.game_structure import game
from scripts.housekeeping.datadir import get_save_dir
from scripts.housekeeping.version import get_version_info, SAVE_VERSION_NUMBER
from scripts.clan_package.clan_symbols import clan_symbol_sprite
from scripts.events_module.consequences import create_new_cat
from scripts.clan_package.get_clan_cats import (
    get_living_clan_cat_count,
    find_alive_cats_with_rank,
)
from scripts.screens.screens_core.screens_core import rebuild_top_menu_buttons


class Clan:
    """

    TODO: Docs

    """

    clan_cats = []

    age = 0
    all_other_clans = []

    grief_strings = {}

    def __init__(
        self,
        save_id="",
        display_name=None,
        leader=None,
        deputy=None,
        medicine_cat=None,
        biome="Forest",
        camp_bg=None,
        symbol=None,
        game_mode="classic",
        cruel_cards: list[str] = None,
        starting_members=None,
        starting_season="Newleaf",
        relations={CatGroup.PLAYER_CLAN_ID: {}},
        self_run_init_functions=True,
        clan_count_mode=""
    ):
        """
        :param save_id: The save file name for the Clan, this should not be used for player-facing text beyond the save file screen
        :param display_name: The display name for the Clan, this is what should appear while the playing the game.
        """
        if save_id == "":
            return

        if starting_members is None:
            starting_members = []

        self.group_ID = CatGroup.PLAYER_CLAN_ID
        self.save_id = save_id
        self.name = display_name if display_name else save_id
        self.clancount = clan_count_mode

        # needs to happen immediately so that any config retrievals will be accurate
        self.cruel_cards: list[str] = cruel_cards if cruel_cards else []
        game.clan = self

        self.leader = leader
        self._leader_lives = 9
        self.leader_predecessors = 0
        self.deputy = deputy
        self.deputy_predecessors = 0
        self.medicine_cat = medicine_cat
        self.med_cat_list = []
        self.med_cat_predecessors = 0

        self.med_cat_number = len(
            self.med_cat_list
        )  # Must do this after the healer is added to the list.
        self.age = 0
        self.starting_season = starting_season
        self.instructor = None
        # This is the first cat in starclan, to "guide" the other dead cats there.
        self.clan_cats = []
        self.biome = biome
        self.override_biome = None
        self.camp_bg = camp_bg
        self.chosen_symbol = symbol
        self.game_mode = game_mode
        self.pregnancy_data = {}
        self.inheritance = {}
        self.custom_pronouns = {}

        switch_set_value(Switch.biome, biome)
        switch_set_value(Switch.camp_bg, camp_bg)
        switch_set_value(Switch.game_mode, game_mode)

        # Reputation is for loners/kittypets/outsiders in general that wish to join the clan.
        # it's a range from 1-100, with 30-70 being neutral, 71-100 being "welcoming",
        # and 1-29 being "hostile". if you're hostile to outsiders, they will VERY RARELY show up.
        self._reputation = get_config(
            "outsiders.starting_reputation",
            creating_clan=True,
            card_list_override=self.cruel_cards,
        )
        self.relations = relations if relations.get(self.group_ID) else {CatGroup.PLAYER_CLAN_ID: {}}

        self.all_other_clans: list[OtherClan] = []
        self.other_clan_IDs = []

        self.starting_members = starting_members
        if game_mode in ("expanded", "cruel_season"):
            self.freshkill_pile = FreshkillPile()
        else:
            self.freshkill_pile = None
        self.herb_supply = HerbSupply()
        self.primary_disaster = None
        self.secondary_disaster = None
        self.war = {CatGroup.PLAYER_CLAN_ID: {}}
        self.future_events = []
        self.last_focus_change = None
        self.clans_in_focus = []

        if self_run_init_functions:
            self.post_initialization_functions()

        rebuild_top_menu_buttons()

    @property
    def current_season(self):
        season_length = get_config("seasons.length")
        calendar = get_config("seasons.calendar")
        modifiers = {
            season: i * season_length
            for i, season in enumerate(calendar)
        }
        return (
            self.starting_season
            if get_config("seasons.lock_season")
            else constants.SEASON_CALENDAR[
                (self.age + modifiers[self.starting_season]) % (season_length * len(calendar))
            ]
        )

    @property
    def name(self):
        return i18n.t("general.clan", name=self.prefix)

    @name.setter
    def name(self, value):
        self.prefix = value

    @property
    def leader_lives(self):
        return min(self._leader_lives, get_config("death_related.max_leader_lives"))

    @leader_lives.setter
    def leader_lives(self, value):
        self._leader_lives = min(value, get_config("death_related.max_leader_lives"))

    # The clan couldn't save itself in time due to issues arising, for example, from this function: "if deputy is not
    # None: self.deputy.status_change('deputy') -> game.clan.remove_med_cat(self)"
    def post_initialization_functions(self):
        if self.deputy and self.deputy.status.alive_in_player_clan:
            self.deputy.rank_change(CatRank.DEPUTY, new_thought=False)
            self.clan_cats.append(self.deputy.ID)

        if self.leader and self.leader.status.alive_in_player_clan:
            self.leader.rank_change(CatRank.LEADER, new_thought=False)
            self.clan_cats.append(self.leader.ID)

        if self.medicine_cat and self.medicine_cat.status.alive_in_player_clan:
            self.clan_cats.append(self.medicine_cat.ID)
            self.med_cat_list.append(self.medicine_cat.ID)
            if self.medicine_cat.status.rank != CatRank.MEDICINE_CAT:
                Cat.all_cats[self.medicine_cat.ID].rank_change(
                    CatRank.MEDICINE_CAT, new_thought=False
                )

    def create_clan(self, clancount="singleclan"):
        """
        This function is only called once a new clan is
        created in the 'clan created' screen, not every time
        the program starts
        """
        game.reset_used_group_IDs()
        switch_set_value(Switch.clan_save_id, self.save_id)
        reset_loaded_clan_settings()
        game.reset_group_IDs()
        game.starclan = Afterlife()
        game.dark_forest = Afterlife()
        game.just_died.clear()
        game.dead_cats_to_grieve.clear()
        instructor_rank = choice(
            (
                CatRank.APPRENTICE,
                CatRank.MEDIATOR_APPRENTICE,
                CatRank.MEDICINE_APPRENTICE,
                CatRank.WARRIOR,
                CatRank.MEDICINE_CAT,
                CatRank.LEADER,
                CatRank.MEDIATOR,
                CatRank.DEPUTY,
                CatRank.ELDER,
            )
        )

        self.instructor = Cat(
            status_dict={"rank": instructor_rank, "group_ID": CatGroup.STARCLAN_ID},
            backstory=choice(
                BACKSTORIES["backstory_categories"]["clan_guide_backstories"]
            ),
        )

        self.clancount = clancount
        self.instructor.status.group_history.insert(0, {"rank": instructor_rank, "group": CatGroup.PLAYER_CLAN_ID, "moons_as": self.instructor.moons})
        self.instructor.dead_for = randint(20, 200)
        self.add_cat(self.instructor)
        self.all_other_clans = []

        key_copy = tuple(Cat.all_cats.keys())
        for i in key_copy:  # Going through all currently existing cats
            # cat_class is a Cat-object
            not_found = True

            for x in self.starting_members:
                if Cat.all_cats[i] == x:
                    self.add_cat(Cat.all_cats[i])
                    not_found = False
            if (
                Cat.all_cats[i] != self.leader
                and Cat.all_cats[i] != self.medicine_cat
                and Cat.all_cats[i] != self.deputy
                and Cat.all_cats[i] != self.instructor
                and not_found
            ):
                Cat.all_cats[i].example = True
                self.remove_cat(Cat.all_cats[i].ID)

        allowed_range = get_config("clan_creation.other_clans_range")
        number_other_clans = randint(allowed_range[0], allowed_range[1])
        for _ in range(number_other_clans):
            other_clan = OtherClan(clancount=self.clancount)
            game.clan.relations[CatGroup.PLAYER_CLAN_ID][other_clan.group_ID] = randint(
                get_config("clan_creation.starting_clan_relation")[0],
                get_config("clan_creation.starting_clan_relation")[1],
            )
            game.clan.war[CatGroup.PLAYER_CLAN_ID][other_clan.group_ID] = {"at_war": False, "duration": 0}

        if self.clancount == "multiclan":
            for i, clan in enumerate(game.clan.all_other_clans[:-1]):
                game.clan.war[clan.group_ID] = {}
                game.clan.relations[clan.group_ID] = {}
                for o_clan in game.clan.all_other_clans[i+1:]:
                    game.clan.relations[clan.group_ID][o_clan.group_ID] = randint(
                        get_config("clan_creation.starting_clan_relation")[0],
                        get_config("clan_creation.starting_clan_relation")[1],
                    )
                    game.clan.war[clan.group_ID][o_clan.group_ID] = {"at_war": False, "duration": 0}

        allowed_range = get_config("clan_creation.starting_outsiders")
        number_outsiders = randint(allowed_range[0], allowed_range[1])
        for i in range(number_outsiders):
            create_new_cat(
                Cat,
                original_social=choice([CatSocial.KITTYPET, CatSocial.LONER, CatSocial.LONER, CatSocial.ROGUE, CatSocial.ROGUE]),
                outside=True
            )

        for cat_id in Cat.all_cats:
            if cat_id not in self.clan_cats:
                self.clan_cats.append(cat_id)
            the_cat = Cat.all_cats.get(cat_id)

        # give thoughts,actions and relationships to cats
            the_cat.init_all_relationships()
            if not the_cat.dead:
                the_cat.backstory = "clan_founder"
            if the_cat.status.rank == CatRank.APPRENTICE:
                the_cat.rank_change(CatRank.APPRENTICE)
            the_cat.pelt.rebuild_sprite = True 

        # find non-selected cats from the 12 generated starters
        for c in switch_get_value(Switch.possible_cats):
            if c.ID not in Cat.all_cats:
                # change non-selected cats to outsiders
                random_social = choice(
                    [
                        CatSocial.ROGUE,
                        CatSocial.LONER,
                        CatSocial.KITTYPET,
                    ]
                )
                c.status.generate_new_status(self, social=random_social)
                # re-assign backstory once cat has new status
                c.assign_backstory()
                # random chance for cat to generate as dead
                if randint(1, 3) == 1:
                    c.die()
                    c.status.change_current_moons_as(new_moons_as=randint(1, 10))

                # renaming to fit outsider status
                name_categories = [
                    "silly_names",
                    "human_names",
                    "loner_names",
                    "normal_prefixes",
                ]
                # defaults in case of error
                weights = [1, 1, 1, 1]
                # give kittypets a kittypet name
                if random_social == CatSocial.KITTYPET:
                    weights = get_config("cat_name_controls.kittypet")
                    # check if the kittypets come with a pretty acc
                    if bool(getrandbits(1)):
                        c.pelt.accessory = (
                            *c.pelt.accessory,
                            choice(c.pelt.collar_accessories),
                        )
                if random_social == CatSocial.LONER:
                    weights = get_config("cat_name_controls.loner")

                if random_social == CatSocial.ROGUE:
                    weights = get_config("cat_name_controls.rogue")

                selected_category = choices(name_categories, weights, k=1)[0]
                name = choice(names.names_dict[selected_category])
                c.change_name(new_prefix=name, new_suffix="")

                # add back to all_cats, cus they get removed during `create_clan()`
                Cat.all_cats[c.ID] = c
                Cat.all_cats_list.append(c)
                self.clan_cats.append(c.ID)

        save_cats(game.clan.save_id, Cat, game)

        # remove any already loaded points of interest
        clear_pois()

        generate_and_add_new_poi(game.clan.biome, PoiType.GATHERING)
        generate_and_add_new_poi(game.clan.biome, PoiType.MOONPLACE)
        for i in range(3):
            generate_and_add_new_poi(game.clan.biome, PoiType.TERRAIN, clan=self.group_ID)

        # create leader's ceremony and give lives
        if self.leader:
            self.leader.generate_lead_ceremony()
        if self.clancount == "multiclan":
            for clan in self.all_other_clans:
                clan.leader.generate_lead_ceremony()

        self.save_clan()
        save_clanlist(self.save_id)
        switch_set_value(Switch.clan_list, read_clans())

        # CHECK IF CAMP BG IS SET -fail-safe in case it gets set to None-
        if switch_get_value(Switch.camp_bg) is None:
            random_camp_options = ["camp1", "camp2"]
            random_camp = choice(random_camp_options)
            switch_set_value(Switch.camp_bg, random_camp)

        # if no game mode chosen, set to Classic
        if switch_get_value(Switch.game_mode) == "":
            switch_set_value(Switch.game_mode, "classic")
            self.game_mode = "classic"

        rebuild_top_menu_buttons()
        # makes sure all the settings are at their starting positions
        self._adjust_settings()

    @staticmethod
    def _adjust_settings():
        """
        Make sure settings are at their starting positions as dictated in the game_config
        """
        # deputy
        if get_config("settings.force_enable.deputy"):
            set_clan_setting("deputy", True)
            save_clan_settings()

        # disasters
        if get_config("settings.force_enable.disasters"):
            set_clan_setting("disasters", True)
            save_clan_settings()

        # modded_kits
        if get_config("settings.force_enable.modded_kits"):
            set_clan_setting("modded_kits", True)
            save_clan_settings()
        if get_config("settings.force_disable.modded_kits"):
            set_clan_setting("modded_kits", False)
            save_clan_settings()

        # feeding order
        starting_order = get_config("prey.feeding.starting_order")
        for setting in [
            "low_rank",
            "high_rank",
            "youngest_first",
            "oldest_first",
            "hungriest_first",
            "experience_first",
        ]:
            set_clan_setting(setting, True if starting_order == setting else False)

        # feeding priority
        starting_priority = get_config("prey.feeding.starting_priority")
        for setting in ["hunter_first", "sick_injured_first"]:
            set_clan_setting(setting, True if starting_priority == setting else False)

    def add_cat(self, cat):  # cat is a 'Cat' object
        """Adds cat into the list of clan cats"""
        if cat.ID in Cat.all_cats and cat.ID not in self.clan_cats:
            self.clan_cats.append(cat.ID)

    def remove_cat(self, ID):  # ID is cat.ID
        """
        This function is for completely removing the cat from the game,
        it's not meant for a cat that's simply dead
        """

        if Cat.all_cats[ID] in Cat.all_cats_list:
            Cat.all_cats_list.remove(Cat.all_cats[ID])

        if ID in Cat.all_cats:
            Cat.all_cats.pop(ID)

        if ID in self.clan_cats:
            self.clan_cats.remove(ID)

    def __repr__(self):
        if self.save_id is not None:
            _ = (
                f"{self.save_id}: led by {self.leader.name}"
                f"with {self.medicine_cat.name} as med. cat"
            )
            return _

        else:
            return "No Clan"

    def new_leader(self, leader):
        """
        TODO: DOCS
        """

        if leader:
            leader.history.add_lead_ceremony()
            self.leader = leader
            if leader.status.rank != CatRank.LEADER:
                Cat.all_cats[leader.ID].rank_change(CatRank.LEADER)
            self.leader_predecessors += 1

    def new_deputy(self, deputy):
        """
        TODO: DOCS
        """
        if deputy:
            self.deputy = deputy
            Cat.all_cats[deputy.ID].rank_change(CatRank.DEPUTY)
            self.deputy_predecessors += 1

    def new_medicine_cat(self, medicine_cat):
        """
        TODO: DOCS
        """
        if medicine_cat:
            if medicine_cat.status.rank != CatRank.MEDICINE_CAT:
                Cat.all_cats[medicine_cat.ID].rank_change(CatRank.MEDICINE_CAT)
            if medicine_cat.ID not in self.med_cat_list:
                self.med_cat_list.append(medicine_cat.ID)
            medicine_cat = self.med_cat_list[0]
            self.medicine_cat = Cat.all_cats[medicine_cat]
            self.med_cat_number = len(self.med_cat_list)

    def remove_med_cat(self, medicine_cat):
        """
        Removes a med cat. Use when retiring, or switching to warrior
        """
        if medicine_cat:
            if medicine_cat.ID in game.clan.med_cat_list:
                game.clan.med_cat_list.remove(medicine_cat.ID)
                game.clan.med_cat_number = len(game.clan.med_cat_list)
            if self.medicine_cat:
                if medicine_cat.ID == self.medicine_cat.ID:
                    if game.clan.med_cat_list:
                        game.clan.medicine_cat = Cat.fetch_cat(
                            game.clan.med_cat_list[0]
                        )
                        game.clan.med_cat_number = len(game.clan.med_cat_list)
                    else:
                        game.clan.medicine_cat = None

    @staticmethod
    def switch_clans(clan, save=True):
        """
        TODO: DOCS
        """
        if save:
            save_clanlist(clan, True)
        else:
            save_clanlist(clan)
        switch_set_value(Switch.switch_clan, True)

    def save_clan(self):
        """
        TODO: DOCS
        """

        clan_data = {
            "clancount_mode": self.clancount,
            "save_id": self.save_id,
            "displayname": self.prefix,
            "clanage": self.age,
            "biome": self.biome,
            "camp_bg": self.camp_bg,
            "clan_symbol": self.chosen_symbol,
            "gamemode": self.game_mode,
            "cruel_cards": self.cruel_cards,
            "used_group_IDs": game.used_group_IDs,
            "last_focus_change": self.last_focus_change,
            "clans_in_focus": self.clans_in_focus,
            "instructor": self.instructor.ID,
            "reputation": self.reputation,
            "mediated": game.mediated,
            "starting_season": self.starting_season,
            "temperament": self.temperament,
            "relations": self.relations,
            "just_died": game.just_died,
            "dead_cats_to_grieve": [x.ID for x in game.dead_cats_to_grieve if x],
            "grief_to_assign": game.clan.grief_strings,
            "version_name": SAVE_VERSION_NUMBER,
            "version_commit": get_version_info().version_number,
            "source_build": get_version_info().is_source_build,
            "custom_pronouns": self.custom_pronouns,
        }

        # LEADER DATA
        if self.leader:
            clan_data["leader"] = self.leader.ID
            clan_data["leader_lives"] = self.leader_lives
        else:
            clan_data["leader"] = None

        clan_data["leader_predecessors"] = self.leader_predecessors

        # DEPUTY DATA
        if self.deputy:
            clan_data["deputy"] = self.deputy.ID
        else:
            clan_data["deputy"] = None

        clan_data["deputy_predecessors"] = self.deputy_predecessors

        # MED CAT DATA
        if self.medicine_cat:
            clan_data["med_cat"] = self.medicine_cat.ID
        else:
            clan_data["med_cat"] = None
        clan_data["med_cat_number"] = self.med_cat_number
        clan_data["med_cat_predecessors"] = self.med_cat_predecessors

        # LIST OF CLAN CATS
        clan_data["clan_cats"] = ",".join([str(i) for i in self.clan_cats])

        clan_data["faded_cats"] = ",".join([str(i) for i in get_faded_ids()])

        # Patrolled cats
        clan_data["patrolled_cats"] = [str(i) for i in game.patrolled]

        # OTHER CLANS
        clan_data["other_clans"] = [i.get_save_data() for i in self.all_other_clans]

        clan_data["war"] = self.war

        clan_data["poi"] = get_poi_save_dict()

        self.save_herb_supply(game.clan)
        self.save_disaster(game.clan)
        self.save_future_events(game.clan)
        self.save_pregnancy(game.clan)

        save_clan_settings()
        if game.clan.game_mode in ("expanded", "cruel_season"):
            self.save_freshkill_pile(game.clan)

        safe_save(f"{get_save_dir()}/{self.save_id}/clan.json", clan_data)

        if os.path.exists(f"{get_save_dir()}/{self.save_id}clan.json"):
            os.remove(f"{get_save_dir()}/{self.save_id}clan.json")
        elif os.path.exists(get_save_dir() + f"/{self.save_id}clan.txt") & (
            self.save_id != "current"
        ):
            os.remove(get_save_dir() + f"/{self.save_id}clan.txt")

    def load_clan(self):
        """
        TODO: DOCS
        """

        version_info = None
        game.reset_used_group_IDs()
        if os.path.exists(
            get_save_dir() + "/" + switch_get_value(Switch.clan_list)[0] + "clan.json"
        ) or os.path.exists(
            get_save_dir() + "/" + switch_get_value(Switch.clan_list)[0] + "/clan.json"
        ):
            version_info = self.load_clan_json()
        else:
            switch_set_value(
                Switch.error_message, "There was an error loading the clan.json"
            )

        # can't put this in post initialization bc guide isn't made before that func
        self.add_guide_influence()
        load_clan_settings()

        return version_info

    @staticmethod
    def add_guide_influence():
        """
        Adds guide's facet influences to their current afterlife
        """
        if game.clan.instructor.status.group == CatGroup.STARCLAN:
            game.starclan.adjust_facets_by_cat(game.clan.instructor)
        elif game.clan.instructor.status.group == CatGroup.DARK_FOREST:
            game.dark_forest.adjust_facets_by_cat(game.clan.instructor)

        if game.clan.clancount == "multiclan":
            for clan in game.clan.all_other_clans:
                if clan.instructor.status.group == CatGroup.STARCLAN:
                    game.starclan.adjust_facets_by_cat(clan.instructor)
                elif clan.instructor.status.group == CatGroup.DARK_FOREST:
                    game.dark_forest.adjust_facets_by_cat(clan.instructor)

    def load_clan_json(self):
        """
        TODO: DOCS
        """
        if not switch_get_value(Switch.clan_list):
            number_other_clans = randint(3, 5)
            for _ in range(number_other_clans):
                OtherClan()
            return
        elif switch_get_value(Switch.clan_list)[0].strip() == "":
            number_other_clans = randint(3, 5)
            for _ in range(number_other_clans):
                OtherClan()
            return

        switch_set_value(
            Switch.error_message, "There was an error loading the clan.json"
        )
        filename = (
            get_save_dir() + "/" + switch_get_value(Switch.clan_list)[0] + "/clan.json"
        )
        if not os.path.exists(filename):
            # legacy
            filename = (
                get_save_dir()
                + "/"
                + switch_get_value(Switch.clan_list)[0]
                + "clan.json"
            )
        with open(
            filename,
            "r",
            encoding="utf-8",
        ) as read_file:  # pylint: disable=redefined-outer-name
            clan_data = ujson.loads(read_file.read())

        if clan_data["leader"]:
            leader = Cat.all_cats[clan_data["leader"]]
            leader_lives = clan_data["leader_lives"]
        else:
            leader = None
            leader_lives = 0

        if clan_data["deputy"]:
            deputy = Cat.all_cats[clan_data["deputy"]]
        else:
            deputy = None

        if clan_data["med_cat"]:
            med_cat = Cat.all_cats[clan_data["med_cat"]]
        else:
            med_cat = None

        # just checking if old param name is being used
        save_id = (
            clan_data.get("clanname")
            if clan_data.get("clanname")
            else clan_data.get("save_id")
        )

        # remove any already loaded points of interest
        clear_pois()

        load_pois(clan_data.get("poi", {"empty": []}))

        game.clan = Clan(
            save_id=save_id,
            display_name=clan_data.get(
                "displayname", None
            ),  # if no displayname is found, clan init just uses save_id
            leader=leader,
            deputy=deputy,
            medicine_cat=med_cat,
            biome=clan_data["biome"],
            camp_bg=clan_data["camp_bg"],
            game_mode=clan_data["gamemode"],
            relations=clan_data.get("relations", {CatGroup.PLAYER_CLAN_ID:{}}),
            cruel_cards=[
                c
                for c in clan_data.get("cruel_cards", [])
                if c in constants.CRUEL_CARDS_ALL
            ],
            self_run_init_functions=False,
        )
        game.clan.post_initialization_functions()

        if clan_data.get("used_group_IDs"):
            game.used_group_IDs = clan_data["used_group_IDs"]
            for ID in game.used_group_IDs:
                game.used_group_IDs[ID] = CatGroup(game.used_group_IDs[ID])

        game.clan.reputation = clan_data["reputation"]

        game.clan.clancount = clan_data.get("clancount_mode", "singleclan")
        game.clan.age = clan_data["clanage"]
        game.clan.starting_season = (
            clan_data["starting_season"]
            if "starting_season" in clan_data
            else "Newleaf"
        )
        game.clan.leader_lives = leader_lives
        game.clan.leader_predecessors = clan_data["leader_predecessors"]

        game.clan.deputy_predecessors = clan_data["deputy_predecessors"]
        game.clan.med_cat_predecessors = clan_data["med_cat_predecessors"]
        game.clan.med_cat_number = clan_data["med_cat_number"]
        # Allows for the custom pronouns to show up in the add pronoun list after the game has closed and reopened.
        if "custom_pronouns" in clan_data.keys():
            if clan_data["custom_pronouns"]:
                if isinstance(clan_data["custom_pronouns"], list):
                    # english-only pronouns from an old version
                    game.clan.custom_pronouns["en"] = clan_data["custom_pronouns"]
                else:
                    game.clan.custom_pronouns = clan_data["custom_pronouns"]

        # Instructor Info
        if clan_data["instructor"] in Cat.all_cats:
            game.clan.instructor = Cat.all_cats[clan_data["instructor"]]
            if not game.clan.instructor.status.get_last_living_group():
                game.clan.instructor.status.group_history.insert(0, {"rank": game.clan.instructor.status.rank, "group": CatGroup.PLAYER_CLAN_ID, "moons_as": game.clan.instructor.moons})
            elif game.clan.instructor.status.get_last_living_group() != CatGroup.PLAYER_CLAN_ID:
                game.clan.instructor.status.group_history[0]["group"] = CatGroup.PLAYER_CLAN_ID
            game.clan.add_cat(game.clan.instructor)
        else:
            game.clan.instructor = Cat(
                status_dict={
                    "rank": choice((CatRank.WARRIOR, CatRank.WARRIOR, CatRank.ELDER)),
                    "group_ID": CatGroup.STARCLAN_ID,
                },
                backstory=choice(
                    BACKSTORIES["backstory_categories"]["clan_guide_backstories"]
                ),
            )
            game.clan.instructor.status.group_history.insert(0, {"rank": game.clan.instructor.status.rank, "group": CatGroup.PLAYER_CLAN_ID, "moons_as": self.instructor.moons})
            # update_sprite(game.clan.instructor)
            game.clan.add_cat(game.clan.instructor)

        # check for symbol
        if "clan_symbol" in clan_data:
            game.clan.chosen_symbol = clan_data["clan_symbol"]
        else:
            game.clan.chosen_symbol = clan_symbol_sprite(game.clan, return_string=True)

        if "other_clans" in clan_data:
            for other_clan in clan_data["other_clans"]:
                if not other_clan.get("group_ID"):
                    ID = game.get_free_group_ID(CatGroup.OTHER_CLAN)
                else:
                    ID = other_clan["group_ID"]
                OtherClan(
                    other_clan.get("prefix", other_clan.get("name")),
                    temperament=other_clan["temperament"],
                    reputation=other_clan.get("reputation"),
                    chosen_symbol=other_clan["chosen_symbol"],
                    biome=other_clan.get("biome"),
                    camp_bg=other_clan.get("camp_bg"),
                    instructor=other_clan.get("instructor"),
                    leader=other_clan.get("leader"),
                    leader_lives=other_clan.get("leader_lives"),
                    leader_predecessors=other_clan.get("leader_predecessors", 0),
                    deputy=other_clan.get("deputy"),
                    deputy_predecessors=other_clan.get("deputy_predecessors", 0),
                    medicine_cat=other_clan.get("medicine_cat"),
                    med_cat_predecessors=other_clan.get("med_cat_predecessors", 0),
                    ID=ID,
                )
                if "relations" in other_clan:
                    game.clan.relations[CatGroup.PLAYER_CLAN_ID][ID] = int(other_clan["relations"])
                else:
                    if not clan_data["relations"].get(CatGroup.PLAYER_CLAN_ID):
                        game.clan.relations[CatGroup.PLAYER_CLAN_ID][ID] = clan_data["relations"]["player_clan"]["other_clan"+str(len(game.clan.all_other_clans))]
        else:
            ID = game.get_free_group_ID(CatGroup.OTHER_CLAN)
            if "other_clan_chosen_symbol" not in clan_data:
                for name, relation, temper in zip(
                    clan_data["other_clans_names"].split(","),
                    clan_data["other_clans_relations"].split(","),
                    clan_data["other_clan_temperament"].split(","),
                ):
                    OtherClan(name, temperament=temper, ID=ID)
                    game.clan.relations[CatGroup.PLAYER_CLAN_ID][ID] = int(relation)
            else:
                for name, relation, temper, symbol in zip(
                    clan_data["other_clans_names"].split(","),
                    clan_data["other_clans_relations"].split(","),
                    clan_data["other_clan_temperament"].split(","),
                    clan_data["other_clan_chosen_symbol"].split(","),
                ):
                    OtherClan(name, temperament=temper, chosen_symbol=symbol, ID=ID)
                    game.clan.relations[CatGroup.PLAYER_CLAN_ID][ID] = int(relation)
        if game.clan.clancount == "multiclan":
            if "relations" not in clan_data or not clan_data["relations"].get(game.clan.group_ID) or len(clan_data["relations"]) < len(game.clan.all_other_clans):
                for i, clan in enumerate(game.clan.all_other_clans[:-1]):
                    game.clan.relations[clan.group_ID] = {}
                    for j, o_clan in enumerate(game.clan.all_other_clans[i+1:]):
                        if "relations" in clan_data:
                            if rel := clan_data["relations"].get("other_clan" + (str(i+1)), {}).get("other_clan" + (str(j+1))):
                                game.clan.relations[clan.group_ID][o_clan.group_ID] = rel
                                continue
                        game.clan.relations[clan.group_ID][o_clan.group_ID] = randint(
                            get_config("clan_creation.starting_clan_relation")[0],
                            get_config("clan_creation.starting_clan_relation")[1],
                        )

        for cat in clan_data["clan_cats"].split(","):
            if cat in Cat.all_cats:
                game.clan.add_cat(Cat.all_cats[cat])
                if hasattr(Cat.all_cats[cat], "group"):
                    if Cat.all_cats[cat].group == game.clan.prefix:
                        pass
                    else:
                        is_neighbour = next(
                            filter(lambda c: c.prefix == Cat.all_cats[cat].group, game.clan.all_other_clans), None)
                        if is_neighbour:
                            Cat.all_cats[cat].status.group_history[0]["group"] = is_neighbour.group_ID
                            Cat.all_cats[cat].status.standing_history[0]["group"] = is_neighbour.group_ID

            else:
                print("WARNING: Cat not found:", cat)
        if "war" in clan_data:
            if clan_data["war"].get("at_war") is not None:
                for c in game.clan.all_other_clans:
                    if c.prefix == clan_data["war"]["enemy"]:
                        game.clan.war[CatGroup.PLAYER_CLAN_ID][c.group_ID] = {"at_war": True, "duration": clan_data["war"]["duration"]}
                    else:
                        game.clan.war[CatGroup.PLAYER_CLAN_ID][c.group_ID] = {"at_war": False, "duration": 0}
                if game.clan.clancount == "multiclan":
                    for i, clan in enumerate(game.clan.all_other_clans[:-1]):
                        game.clan.war[clan.group_ID] = {}
                        for o_clan in game.clan.all_other_clans[i+1:]:
                            game.clan.war[clan.group_ID][o_clan.group_ID] = {"at_war": False, "duration": 0}
            else:
                if clan_data["war"].get(CatGroup.PLAYER_CLAN_ID):
                    game.clan.war = clan_data["war"]
                else:
                    for key in clan_data["war"]:
                        clan_id = key
                        if len(key) > 2:
                            clan_id = CatGroup.PLAYER_CLAN_ID if key == "player_clan" else game.clan.all_other_clans[int(key[-1])-1].group_ID
                        game.clan.war[clan_id] = {}
                        for other_key in clan_data["war"][key]:
                            other_clan_id = other_key
                            if len(other_key) > 2:
                                other_clan_id = game.clan.all_other_clans[int(other_key[-1])-1].group_ID
                            game.clan.war[clan_id][other_clan_id] = clan_data["war"][key][other_key]
                

        game.clan.last_focus_change = clan_data.get("last_focus_change")
        game.clan.clans_in_focus = clan_data.get("clans_in_focus", [])

        # Patrolled cats
        if "patrolled_cats" in clan_data:
            game.patrolled = clan_data["patrolled_cats"]

        # Mediated flag
        if "mediated" in clan_data:
            if not isinstance(clan_data["mediated"], list):
                game.mediated = []
            else:
                game.mediated = clan_data["mediated"]

        game.just_died.clear()
        # Cat who had just died
        if "just_died" in clan_data:
            game.just_died = clan_data["just_died"]

        game.dead_cats_to_grieve.clear()
        # Cats who need to be grieved
        if "dead_cats_to_grieve" in clan_data:
            game.dead_cats_to_grieve = [
                Cat.fetch_cat(x) for x in clan_data["dead_cats_to_grieve"] if Cat.fetch_cat(x)
            ]

        # Cats who are gonna grieve
        if "grief_to_assign" in clan_data:
            game.clan.grief_strings = clan_data["grief_to_assign"]

        self.load_pregnancy(game.clan)
        self.load_herb_supply(game.clan)
        self.load_future_events(game.clan)
        self.load_disaster(game.clan)
        if game.clan.game_mode != "classic":
            self.load_freshkill_pile(game.clan)
        switch_set_value(Switch.error_message, "")

        # Return Version Info.
        return {
            "version_name": clan_data.get("version_name"),
            "version_commit": clan_data.get("version_commit"),
            "source_build": clan_data.get("source_build"),
        }

    def load_pregnancy(self, clan):
        """
        Load the information about what cat is pregnant and in what 'state' they are in the pregnancy.
        """
        if not game.clan.save_id:
            return
        file_path = get_save_dir() + f"/{game.clan.save_id}/pregnancy.json"
        if os.path.exists(file_path):
            with open(
                file_path, "r", encoding="utf-8"
            ) as read_file:  # pylint: disable=redefined-outer-name
                clan.pregnancy_data = ujson.load(read_file)
        else:
            clan.pregnancy_data = {}

    def save_pregnancy(self, clan):
        """
        Save the information about what cat is pregnant and in what 'state' they are in the pregnancy.
        """
        if not game.clan.save_id:
            return

        keys_to_delete = []
        for key in clan.pregnancy_data:
            if key not in Cat.all_cats:
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del clan.pregnancy_data[key]

        safe_save(
            f"{get_save_dir()}/{game.clan.save_id}/pregnancy.json", clan.pregnancy_data
        )

    def load_disaster(self, clan):
        """
        TODO: DOCS
        """
        if not game.clan.save_id:
            return

        file_path = get_save_dir() + f"/{game.clan.save_id}/disasters/primary.json"
        try:
            if os.path.exists(file_path):
                with open(
                    file_path, "r", encoding="utf-8"
                ) as read_file:  # pylint: disable=redefined-outer-name
                    disaster = ujson.load(read_file)
                    if disaster:
                        clan.primary_disaster = OngoingEvent(
                            event=disaster["event"],
                            tags=disaster["tags"],
                            duration=disaster["duration"],
                            current_duration=(
                                disaster["current_duration"]
                                if "current_duration"
                                else disaster["duration"]
                            ),  # pylint: disable=using-constant-test
                            trigger_events=disaster["trigger_events"],
                            progress_events=disaster["progress_events"],
                            conclusion_events=disaster["conclusion_events"],
                            secondary_disasters=disaster["secondary_disasters"],
                            collateral_damage=disaster["collateral_damage"],
                        )
                    else:
                        clan.primary_disaster = {}
            else:
                os.makedirs(get_save_dir() + f"/{game.clan.save_id}/disasters")
                clan.primary_disaster = None
                with open(file_path, "w", encoding="utf-8") as rel_file:
                    json_string = ujson.dumps(clan.primary_disaster, indent=4)
                    rel_file.write(json_string)
        except:
            clan.primary_disaster = None

        file_path = get_save_dir() + f"/{game.clan.save_id}/disasters/secondary.json"
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as read_file:
                    disaster = ujson.load(read_file)
                    if disaster:
                        clan.secondary_disaster = OngoingEvent(
                            event=disaster["event"],
                            tags=disaster["tags"],
                            duration=disaster["duration"],
                            current_duration=(
                                disaster["current_duration"]
                                if "current_duration"
                                else disaster["duration"]
                            ),  # pylint: disable=using-constant-test
                            progress_events=disaster["progress_events"],
                            conclusion_events=disaster["conclusion_events"],
                            collateral_damage=disaster["collateral_damage"],
                        )
                    else:
                        clan.secondary_disaster = {}
            else:
                os.makedirs(get_save_dir() + f"/{game.clan.save_id}/disasters")
                clan.secondary_disaster = None
                with open(file_path, "w", encoding="utf-8") as rel_file:
                    json_string = ujson.dumps(clan.secondary_disaster, indent=4)
                    rel_file.write(json_string)

        except:
            clan.secondary_disaster = None

    def save_disaster(self, clan=game.clan):
        """
        TODO: DOCS
        """
        if not clan.save_id:
            return
        file_path = get_save_dir() + f"/{clan.save_id}/disasters/primary.json"
        if not os.path.isdir(f"{get_save_dir()}/{clan.save_id}/disasters"):
            os.mkdir(f"{get_save_dir()}/{clan.save_id}/disasters")
        if clan.primary_disaster:
            disaster = {
                "event": clan.primary_disaster.event,
                "tags": clan.primary_disaster.tags,
                "duration": clan.primary_disaster.duration,
                "current_duration": clan.primary_disaster.current_duration,
                "trigger_events": clan.primary_disaster.trigger_events,
                "progress_events": clan.primary_disaster.progress_events,
                "conclusion_events": clan.primary_disaster.conclusion_events,
                "secondary_disasters": clan.primary_disaster.secondary_disasters,
                "collateral_damage": clan.primary_disaster.collateral_damage,
            }
        else:
            disaster = {}

        safe_save(f"{get_save_dir()}/{clan.save_id}/disasters/primary.json", disaster)

        if clan.secondary_disaster:
            disaster = {
                "event": clan.secondary_disaster.event,
                "tags": clan.secondary_disaster.tags,
                "duration": clan.secondary_disaster.duration,
                "current_duration": clan.secondary_disaster.current_duration,
                "trigger_events": clan.secondary_disaster.trigger_events,
                "progress_events": clan.secondary_disaster.progress_events,
                "conclusion_events": clan.secondary_disaster.conclusion_events,
                "secondary_disasters": clan.secondary_disaster.secondary_disasters,
                "collateral_damage": clan.secondary_disaster.collateral_damage,
            }
        else:
            disaster = {}

        safe_save(f"{get_save_dir()}/{clan.save_id}/disasters/secondary.json", disaster)

    def load_future_events(self, clan):
        """
        Loads the Clan's saved future events
        """
        if not clan.save_id:
            return

        # load the current file path, if it exists in save
        file_path = f"{get_save_dir()}/{clan.save_id}/future_events.json"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as save_file:
                save_list = ujson.load(save_file)
                for event in save_list:
                    try:
                        event_obj = FutureEvent(
                                parent_event=event["parent_event"],
                                event_type=event["event_type"],
                                pool=event["pool"],
                                moon_delay=event["moon_delay"],
                                involved_cats=event["involved_cats"],
                                clan=event["clan"],
                            )
                        if not event_obj.clan or event_obj.clan in [clan.prefix, CatGroup.PLAYER_CLAN.value]:
                            event_obj.clan = CatGroup.PLAYER_CLAN_ID
                        elif len(event_obj.clan) > 2:
                            if match := [c for c in clan.all_other_clans if c.prefix == event_obj.clan]:
                                event_obj.clan = match[0].group_ID
                            else:
                                event_obj.clan = clan.all_other_clans[int(event_obj.clan[-1])-1].group_ID

                        game.clan.future_events.append(event_obj)
                    except KeyError:
                        print(
                            f"WARNING: A saved future event was missing information and was not loaded. event: {event}"
                        )
                        continue

    def save_future_events(self, clan):
        """
        saves the Clan's current future events
        """
        save_list = []

        for event in game.clan.future_events:
            if e := event.to_dict():
                save_list.append(e)

        safe_save(f"{get_save_dir()}/{game.clan.save_id}/future_events.json", save_list)

    def load_herb_supply(self, clan):
        """
        Loads the Clan's saved herb supply info
        """
        if not game.clan.save_id:
            return

        save_dir = get_save_dir()

        current_file_path = save_dir + f"/{game.clan.save_id}/herb_supply.json"
        old_file_path = save_dir + f"/{game.clan.save_id}/herbs.json"

        try:
            # load the old file path and convert the save data into current format
            if os.path.exists(old_file_path):
                with open(old_file_path, "r", encoding="utf-8") as save_file:
                    herbs = ujson.load(save_file)
                    clan.herb_supply = HerbSupply()
                    clan.herb_supply.convert_old_save(herbs)

            # load the current file path, if it exists in save
            elif os.path.exists(current_file_path):
                with open(current_file_path, "r", encoding="utf-8") as save_file:
                    herbs = ujson.load(save_file)
                    clan.herb_supply = HerbSupply(herb_supply=herbs["storage"])
                    clan.herb_supply.collected = herbs["collected"]

            # else just start us with an empty herb supply
            else:
                clan.herb_supply = HerbSupply()

            clan.herb_supply.set_required_herb_count(get_living_clan_cat_count(Cat))
        except:
            clan.herb_supply = HerbSupply()

    def save_herb_supply(self, clan):
        """
        saves the Clan's current herb supply
        """
        if not clan.herb_supply:
            return

        combined_supply_dict = clan.herb_supply.combined_supply_dict
        combined_supply_dict = {
            "storage": {
                herb: [int(i) for i in amounts]
                for herb, amounts in combined_supply_dict["storage"].items()
            },
            "collected": {
                herb: int(amount)
                for herb, amount in combined_supply_dict["collected"].items()
            },
        }

        safe_save(
            f"{get_save_dir()}/{game.clan.save_id}/herb_supply.json",
            combined_supply_dict,
        )

        # delete old herb save file if it exists
        if os.path.exists(get_save_dir() + f"/{game.clan.save_id}/herbs.json"):
            os.remove(get_save_dir() + f"/{game.clan.save_id}/herbs.json")

    def load_freshkill_pile(self, clan):
        """
        TODO: DOCS
        """
        if not game.clan.save_id or clan.game_mode == "classic":
            return

        file_path = get_save_dir() + f"/{game.clan.save_id}/freshkill_pile.json"
        try:
            if os.path.exists(file_path):
                with open(
                    file_path, "r", encoding="utf-8"
                ) as read_file:  # pylint: disable=redefined-outer-name
                    pile = ujson.load(read_file)
                    clan.freshkill_pile = FreshkillPile(pile)

                file_path = get_save_dir() + f"/{game.clan.save_id}/nutrition_info.json"
                if os.path.exists(file_path) and clan.freshkill_pile:
                    with open(file_path, "r", encoding="utf-8") as read_file:
                        nutritions = ujson.load(read_file)
                        for k, nutr in nutritions.items():
                            nutrition = Nutrition()
                            nutrition.max_score = nutr["max_score"]
                            nutrition.current_score = nutr["current_score"]
                            clan.freshkill_pile.nutrition_info[k] = nutrition
                        if len(nutritions) <= 0:
                            for cat in Cat.all_cats_list:
                                clan.freshkill_pile.add_cat_to_nutrition(cat)
            else:
                clan.freshkill_pile = FreshkillPile()
        except:
            clan.freshkill_pile = FreshkillPile()

    def save_freshkill_pile(self, clan):
        """
        TODO: DOCS
        """
        if clan.game_mode == "classic" or not clan.freshkill_pile:
            return

        safe_save(
            f"{get_save_dir()}/{game.clan.save_id}/freshkill_pile.json",
            clan.freshkill_pile.pile,
        )

        data = {}
        for k, nutr in clan.freshkill_pile.nutrition_info.items():
            data[k] = {
                "max_score": nutr.max_score,
                "current_score": nutr.current_score,
                "percentage": nutr.percentage,
            }

        safe_save(f"{get_save_dir()}/{game.clan.save_id}/nutrition_info.json", data)

    ## Properties

    @property
    def reputation(self):
        return self._reputation

    @reputation.setter
    def reputation(self, a: int):
        rep = min(int(a), get_config("outsiders.max_reputation"))
        self._reputation = max(rep, get_config("outsiders.min_reputation"))

    @property
    def temperament(self) -> tuple[str, str]:
        """Temperament is determined whenever it's accessed. This makes sure it's always accurate to the
        current cats in the Clan. However, determining Clan temperament is slow!
        Clan temperament should be used as sparsely as possible, since
        it's pretty resource-intensive to determine it."""

        leader = (
            Cat.fetch_cat(self.leader)
            if isinstance(Cat.fetch_cat(self.leader), Cat)
            else None
        )
        deputy = (
            Cat.fetch_cat(self.deputy)
            if isinstance(Cat.fetch_cat(self.deputy), Cat)
            else None
        )
        medicine_cats = find_alive_cats_with_rank(Cat, [CatRank.MEDICINE_CAT])

        all_other_cats = [
            i
            for i in Cat.all_cats_list
            if i.status.rank
            not in (CatRank.LEADER, CatRank.DEPUTY, CatRank.MEDICINE_CAT)
            and i.status.alive_in_player_clan
        ]

        sociability_list = []
        aggression_list = []
        lawfulness_list = []
        stability_list = []

        # 3x influence
        if leader:
            sociability_list += [leader.personality.sociability] * 3
            aggression_list += [leader.personality.aggression] * 3
            lawfulness_list += [leader.personality.lawfulness] * 3
            stability_list += [leader.personality.stability] * 3

        # 2x influence
        if deputy:
            sociability_list += [deputy.personality.sociability] * 2
            aggression_list += [deputy.personality.aggression] * 2
            lawfulness_list += [deputy.personality.lawfulness] * 2
            stability_list += [deputy.personality.stability] * 2

        # collective influence
        if medicine_cats:
            sociability_list.append(
                statistics.median([i.personality.sociability for i in medicine_cats])
            )
            aggression_list.append(
                statistics.median([i.personality.aggression for i in medicine_cats])
            )
            lawfulness_list.append(
                statistics.median([i.personality.lawfulness for i in medicine_cats])
            )
            stability_list.append(
                statistics.median([i.personality.stability for i in medicine_cats])
            )

        # collective influence
        if all_other_cats:
            sociability_list.append(
                statistics.median([i.personality.sociability for i in all_other_cats])
            )
            aggression_list.append(
                statistics.median([i.personality.aggression for i in all_other_cats])
            )
            lawfulness_list.append(
                statistics.median([i.personality.lawfulness for i in all_other_cats])
            )
            stability_list.append(
                statistics.median([i.personality.stability for i in all_other_cats])
            )

        # mean of [leader, leader, leader, deputy, deputy, medicine_cats, all_other_cats]
        clan_sociability = round(statistics.mean(sociability_list))
        clan_aggression = round(statistics.mean(aggression_list))
        clan_lawfulness = round(statistics.mean(lawfulness_list))
        clan_stability = round(statistics.mean(stability_list))

        if not leader and not deputy and not all_other_cats:
            print("returned default temper: stoic, observant")
            return "stoic", "observant"

        return get_temper_alignment(
            clan_sociability, clan_aggression, clan_lawfulness, clan_stability
        )

    @temperament.setter
    def temperament(self, val):
        return

    def group_ID_to_clan(self, group_ID):
        return next(filter(lambda c: c.group_ID == group_ID, game.clan.all_other_clans), game.clan)

    def get_relations(self, clan, other_clan, get_label=False):
        main_enum = clan.group_ID
        other_enum = other_clan.group_ID

        if game.clan.relations.get(other_enum, {}).get(main_enum):
            main_enum = other_clan.group_ID
            other_enum = clan.group_ID

        if get_label:
            if game.clan.relations[main_enum][other_enum] > get_config("reputation.other_clans.neutral"):
                return "ally"
            elif game.clan.relations[main_enum][other_enum] <= get_config("reputation.other_clans.hostile"):
                return "hostile"
            return "neutral"
        
        return game.clan.relations[main_enum][other_enum]

    def set_relations(self, clan, other_clan, value = None, offset=0):
        main_enum = clan.group_ID
        other_enum = other_clan.group_ID

        if game.clan.relations.get(other_enum, {}).get(main_enum):
            main_enum = other_clan.group_ID
            other_enum = clan.group_ID

        value = value or game.clan.relations[main_enum][other_enum]
        
        game.clan.relations[main_enum][other_enum] = max(0, min(int(value + offset), get_config("reputation.other_clans.relation_cap")))

    def get_wars(self, clan):
        enemies = []
        for key in game.clan.war:
            if key == clan:
                for o_key in game.clan.war[key]:
                    if game.clan.war[key][o_key]["at_war"]:
                        enemies.append(o_key)
            elif game.clan.war[key].get(clan, {"at_war": False})["at_war"]:
                enemies.append(key)
        return enemies

    def check_war(self, clan, other_clan):
        if match := game.clan.war.get(clan):
            return match[other_clan]["at_war"]
        return game.clan.war[other_clan][clan]["at_war"]



class OtherClan:
    """
    TODO: DOCS
    """

    interaction_dict = {
        "ally": ["offend", "praise"],
        "neutral": ["provoke", "befriend"],
        "hostile": ["antagonize", "appease", "declare"],
    }

    first_temper_list = []
    second_temper_list = []
    for _l in constants.TEMPERAMENT_DICTS[0].values():
        first_temper_list.extend(_l)
    for _l in constants.TEMPERAMENT_DICTS[1].values():
        second_temper_list.extend(_l)

    # Notes to self:
    # Friendly to joiners: gracious, amiable   
    # Neutral to joiners: cunning, logical, stoic, mellow, bloodthirsty
    # Hostile to joiners: wary, proud

    def __init__(
        self, 
        name: str = "",
        clancount="singleclan", 
        biome=None, 
        camp_bg=None, 
        reputation=None, 
        temperament: tuple[str, str] = None,
        chosen_symbol: str = "", 
        instructor=None, 
        leader=None, 
        leader_lives=9, 
        leader_predecessors=0, 
        deputy=None, 
        deputy_predecessors=0, 
        medicine_cat=None, 
        med_cat_predecessors=0, 
        ID: str = 0
    ):
        self.group_ID = ID
        if not self.group_ID:
            self.group_ID = game.get_free_group_ID(CatGroup.OTHER_CLAN)
        game.clan.other_clan_IDs.append(self.group_ID)

        self.name = name
        if not self.prefix:  # find name if clan has no name yet
            used_names = [str(i.name) for i in game.clan.all_other_clans] + [
                game.clan.name
            ]
            clan_names = get_possible_clan_names()
            self.name = choice(clan_names)  # name property will set self.prefix
            while self.name in used_names:  # making sure we don't repeat a name
                self.name = choice(clan_names)
        if biome:
            self.biome = biome
        else:
            self.biome = game.clan.biome if random() < 0.75 else choice(constants.BIOME_TYPES)
            while self.biome in ["Wetlands", "Desert", None]:
                self.biome = choice(constants.BIOME_TYPES)
        if camp_bg:
            self.camp_bg = camp_bg
        else:
            self.camp_bg = f"camp{randint(1, 4)}"

        self.temperament: tuple[str, str]

        # detect old saves and convert
        if isinstance(temperament, str):
            used_tempers = []
            for clan in game.clan.all_other_clans:
                used_tempers.extend(clan.temperament)

            self.temperament = (
                temperament,
                choice([x for x in self.second_temper_list if x not in used_tempers]),
            )
        # assign if a saved temper exists
        elif temperament:
            self.temperament = temperament
        # find temperament
        else:
            used_tempers = []
            for clan in game.clan.all_other_clans:
                used_tempers.extend(clan.temperament)

            self.temperament = (
                choice([x for x in self.first_temper_list if x not in used_tempers]),
                choice([x for x in self.second_temper_list if x not in used_tempers]),
            )
        if reputation is None:
            if self.temperament[0] in ["gracious", "amiable"]:
                self.reputation = choice([randint(71, 100), randint(71, 100), randint(71, 100), randint(50, 70)])
            elif self.temperament[0] in ["wary", "proud"]:
                self.reputation = choice([randint(1, 30), randint(1, 30), randint(1, 30), randint(31, 50)])
            else:
                self.reputation = choice([randint(1, 30), randint(31, 70), randint(31, 70), randint(71, 100)])
        else:
            self.reputation = reputation

        self.chosen_symbol = (
            None  # have to establish None first so that clan_symbol_sprite works
        )
        self.chosen_symbol = (
            chosen_symbol
            if chosen_symbol
            else clan_symbol_sprite(self, return_string=True)
        )

        self.instructor = Cat.all_cats.get(instructor)
        self.leader = Cat.all_cats.get(leader)
        self.leader_lives = leader_lives if leader else 0
        self.leader_predecessors = leader_predecessors
        self.deputy = Cat.all_cats.get(deputy)
        self.deputy_predecessors = deputy_predecessors
        self.medicine_cat = Cat.all_cats.get(medicine_cat)
        self.med_cat_predecessors = med_cat_predecessors
        self.med_cat_list = []
        self.med_cat_number = len(self.med_cat_list)

        if self.leader and not self.instructor:
            instructor_rank = choice((
                CatRank.APPRENTICE,
                CatRank.MEDIATOR_APPRENTICE,
                CatRank.MEDICINE_APPRENTICE,
                CatRank.WARRIOR,
                CatRank.MEDICINE_CAT,
                CatRank.LEADER,
                CatRank.MEDIATOR,
                CatRank.DEPUTY,
                CatRank.ELDER,
            ))
            self.instructor = Cat(
                status_dict={
                    "rank": instructor_rank,
                    "group_ID": CatGroup.STARCLAN_ID,
                },
                backstory=choice(
                    BACKSTORIES["backstory_categories"]["clan_guide_backstories"]
                ),
            )
            self.instructor.dead_for = randint(20, 200)
            self.instructor.status.group_history.insert(0, {"rank": instructor_rank, "group": self.group_ID, "moons_as": self.instructor.moons})
            game.clan.add_cat(self.instructor)

        game.clan.all_other_clans.append(self)

        rank_weights = get_config("clan_creation.rank_weights")
        if clancount == "multiclan":
            for i in range(3):
                generate_and_add_new_poi(game.clan.biome, PoiType.TERRAIN, clan=self.group_ID)

            instructor_rank = choice(
                (
                    CatRank.APPRENTICE,
                    CatRank.MEDIATOR_APPRENTICE,
                    CatRank.MEDICINE_APPRENTICE,
                    CatRank.WARRIOR,
                    CatRank.MEDICINE_CAT,
                    CatRank.LEADER,
                    CatRank.MEDIATOR,
                    CatRank.DEPUTY,
                    CatRank.ELDER,
                )
            )
            self.instructor = Cat(
                status_dict={"rank": instructor_rank, "group_ID": CatGroup.STARCLAN_ID},
                backstory=choice(
                BACKSTORIES["backstory_categories"]["clan_guide_backstories"]
                ),
            )
            self.instructor.dead_for = randint(20, 200)
            self.instructor.status.group_history.insert(0, {"rank": instructor_rank, "group": self.group_ID, "moons_as": self.instructor.moons})

            use_special = get_config("clan_creation.use_special_roller")
            cat_range = get_config("clan_creation.neighbourclan_cats")
            self.new_leader(create_cat(CatRank.LEADER, biome=self.biome, kittypet=use_special, clan=self.group_ID))
            self.new_deputy(create_cat(CatRank.DEPUTY, biome=self.biome, kittypet=use_special, clan=self.group_ID))
            self.new_medicine_cat(create_cat(CatRank.MEDICINE_CAT, biome=self.biome, kittypet=use_special, clan=self.group_ID))
            for i in range(randint(cat_range[0], cat_range[1])):
                create_cat(choices(list(rank_weights.keys()), list(rank_weights.values()))[0], biome=self.biome, kittypet = use_special, clan=self.group_ID)
    @property
    def name(self):
        return i18n.t("general.clan", name=self.prefix)

    @name.setter
    def name(self, value):
        self.prefix = value

    def __repr__(self):
        # has indicators that this is unlocalized, just in case
        return f"!!{self.name}Clan!!"
    
    def get_save_data(self):
        return {
            "group_ID": self.group_ID,
            "name": self.prefix,
            "reputation" : self.reputation,
            "temperament" : self.temperament,
            "chosen_symbol": self.chosen_symbol,
            "biome": self.biome,
            "camp_bg": self.camp_bg,
            "instructor": self.instructor.ID if self.instructor else None,
            "leader" : self.leader.ID if self.leader else None,
            "leader_lives" : self.leader_lives,
            "leader_predecessors" : self.leader_predecessors,
            "deputy" : self.deputy.ID if self.deputy else None,
            "deputy_predecessors": self.deputy_predecessors,
            "medicine_cat": self.medicine_cat.ID if self.medicine_cat else None,
            "med_cat_predecessors": self.med_cat_predecessors,
        }

    def new_leader(self, leader):
        """
        TODO: DOCS
        """

        if leader:
            leader.history.add_lead_ceremony()
            self.leader = leader
            if leader.status.rank != CatRank.LEADER:
                Cat.all_cats[leader.ID].rank_change(CatRank.LEADER)
            self.leader_predecessors += 1

    def new_deputy(self, deputy):
        """
        TODO: DOCS
        """
        if deputy:
            self.deputy = deputy
            Cat.all_cats[deputy.ID].rank_change(CatRank.DEPUTY)
            self.deputy_predecessors += 1

    def new_medicine_cat(self, medicine_cat):
        """
        TODO: DOCS
        """
        if medicine_cat:
            if medicine_cat.status.rank != CatRank.MEDICINE_CAT:
                Cat.all_cats[medicine_cat.ID].rank_change(CatRank.MEDICINE_CAT)
            if medicine_cat.ID not in self.med_cat_list:
                self.med_cat_list.append(medicine_cat.ID)
            medicine_cat = self.med_cat_list[0]
            self.medicine_cat = Cat.all_cats[medicine_cat]
            self.med_cat_number = len(self.med_cat_list)

    def remove_med_cat(self, medicine_cat):
        """
        Removes a med cat. Use when retiring, or switching to warrior
        """
        if medicine_cat:
            if medicine_cat.ID in self.med_cat_list:
                self.med_cat_list.remove(medicine_cat.ID)
                self.med_cat_number = len(self.med_cat_list)
            if self.medicine_cat:
                if medicine_cat.ID == self.medicine_cat.ID:
                    if self.med_cat_list:
                        self.medicine_cat = Cat.fetch_cat(
                            self.med_cat_list[0]
                        )
                        self.med_cat_number = len(self.med_cat_list)
                    else:
                        self.medicine_cat = None

    @property
    def reputation(self):
        return self._reputation

    @reputation.setter
    def reputation(self, a: int):
        self._reputation = int(a)
        if self._reputation > 100:
            self._reputation = 100
        elif self._reputation < 0:
            self._reputation = 0

class Afterlife:
    """
    Currently just used for tracking temperament & facets. All facets default to 8 if influencing_cats is empty.
    """

    def __init__(self):
        self.influencing_cats: set[str] = set()

        self._law: int = 0
        self._social: int = 0
        self._aggress: int = 0
        self._stable: int = 0

        self._total_aggression: int = 0
        self._total_lawfulness: int = 0
        self._total_sociability: int = 0
        self._total_stability: int = 0

    @property
    def aggression(self) -> int:
        if not self.influencing_cats:
            return 8
        else:
            return self._aggress

    @aggression.setter
    def aggression(self, value):
        raise Exception(
            "ERROR: Afterlife aggression cannot be set manually as it is meant to be calculated from the currently dead cats."
        )

    @property
    def sociability(self) -> int:
        if not self.influencing_cats:
            return 8
        else:
            return self._social

    @sociability.setter
    def sociability(self, value):
        raise Exception(
            "ERROR: Afterlife sociability cannot be set manually as it is meant to be calculated from the currently dead cats."
        )

    @property
    def lawfulness(self) -> int:
        if not self.influencing_cats:
            return 8
        else:
            return self._law

    @lawfulness.setter
    def lawfulness(self, value):
        raise Exception(
            "ERROR: Afterlife lawfulness cannot be set manually as it is meant to be calculated from the currently dead cats."
        )

    @property
    def stability(self) -> int:
        if not self.influencing_cats:
            return 8
        else:
            return self._stable

    @stability.setter
    def stability(self, value):
        raise Exception(
            "ERROR: Afterlife stability cannot be set manually as it is meant to be calculated from the currently dead cats."
        )

    @property
    def temperament(self) -> (str, str):
        return get_temper_alignment(
            self.sociability, self.aggression, self.lawfulness, self.stability
        )

    def adjust_facets_by_cat(self, cat: Cat, do_removal: bool = False):
        """
        Adjusts the afterlife's facet averages according to the facets of the given cat
        :param cat: The cat object adjust facets by
        :param do_removal: Set True if the cat's facets are being removed from the afterlife's
        """
        if do_removal:
            self.influencing_cats.remove(cat.ID)
        else:
            self.influencing_cats.add(cat.ID)

        num_of_influencers = len(self.influencing_cats)

        if do_removal:
            self._total_lawfulness -= cat.personality.lawfulness
            self._total_sociability -= cat.personality.sociability
            self._total_aggression -= cat.personality.aggression
            self._total_stability -= cat.personality.stability
        else:
            self._total_lawfulness += cat.personality.lawfulness
            self._total_sociability += cat.personality.sociability
            self._total_aggression += cat.personality.aggression
            self._total_stability += cat.personality.stability

        self._law = self._get_adjusted_facet_average(
            self._total_lawfulness,
            num_of_influencers,
        )

        self._social = self._get_adjusted_facet_average(
            self._total_sociability,
            num_of_influencers,
        )

        self._aggress = self._get_adjusted_facet_average(
            self._total_aggression,
            num_of_influencers,
        )

        self._stable = self._get_adjusted_facet_average(
            self._total_stability,
            num_of_influencers,
        )

    @staticmethod
    def _get_adjusted_facet_average(
        total: int,
        num_of_influencers: int,
    ) -> int:
        """
        Handles the math for adjust average facets.
        :param total: The facet's total value derived from all influencing cats
        :param num_of_influencers: The number of cats influencing the average
        :return: The adjusted average
        """
        if not num_of_influencers:
            return 0
        return total // num_of_influencers


def get_temper_alignment(
    sociability: int, aggression: int, lawfulness: int, stability: int
) -> tuple[str, str]:
    """
    Returns the temperament strings associated with given values
    """
    first_temper = _find_alignment(
        constants.TEMPERAMENT_DICTS[0], sociability, aggression
    )
    second_temper = _find_alignment(
        constants.TEMPERAMENT_DICTS[1], lawfulness, stability
    )

    return first_temper, second_temper


def _find_alignment(temper_dict: dict, first_value: int, second_value: int) -> str:
    """
    Helper function that returns the string on a temper alignment chart for the first and second values.
    :param temper_dict: The temper alignment chart dictionary.
    :param first_value: The first value to find the alignment for. This is the chart's "y_value", or when viewing it as a dictionary: its keys.
    :param second_value: The second value to find the alignment for. This is the chart's "x-value", or when viewing it as a dictionary: its values.
    """
    if 11 <= first_value:
        temper = list(temper_dict.values())[2]
    elif 7 <= first_value:
        temper = list(temper_dict.values())[1]
    else:
        temper = list(temper_dict.values())[0]

    if 11 <= second_value:
        temper = temper[2]
    elif 7 <= second_value:
        temper = temper[1]
    else:
        temper = temper[0]

    return temper


clan_class = Clan()
clan_class.remove_cat(cat_class.ID)
