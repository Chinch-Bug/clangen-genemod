from random import choice, randrange, random, randint, choices, sample
from typing import List, Optional

import i18n
import re

from scripts.cat import pronouns
from scripts.cat.cats import Cat
from scripts.cat.enums import CatGroup
from scripts.cat.pelts import Pelt
from scripts.cat_relations.relationship import Relationship
from scripts.clan_package.settings import get_clan_setting
from scripts.event_class import Single_Event
from scripts.events_module.future.prep_and_trigger import prep_future_event
from scripts.events_module.short.short_event import ShortEvent
from scripts.events_module.relationship.relation_events import Relation_Events
from scripts.game_structure import localization, game
from scripts.events_module.text_adjust import (
    event_text_adjust,
    get_leader_life_notice,
    adjust_list_text,
    history_text_adjust,
    process_text,
)
from scripts.events_module.consequences import (
    create_new_cat_block,
    unpack_rel_block,
    change_relationship_values, 
    find_clan_cats,
)
from scripts.clan_package.cotc import change_clan_reputation, change_clan_relations
from scripts.clan_package.get_clan_cats import find_alive_cats_with_rank

from scripts.cat.enums import CatAge, CatRank, CatSocial, CatStanding
from scripts.cat.personality import Personality
from scripts.cat.skills import SkillPath
from scripts.game_structure import constants


class CrossClanEvent(ShortEvent):
    """
    A moon event that only affects the moon it was triggered on.  Can involve two cats directly and be restricted by various constraints.
    - full documentation available on GitHub wiki
    """

    NUM_OF_TRAITS = len(Personality.trait_ranges["normal_traits"].keys()) + len(
        Personality.trait_ranges["kit_traits"].keys()
    )
    NUM_OF_SKILLS = len(SkillPath)

    NUM_OF_AGES = len(CatAge)

    NUM_OF_RANKS = CatRank.get_num_of_clan_ranks()

    def __init__(
        self,
        event_id: str = "",
        location: List[str] = None,
        season: List[str] = None,
        sub_type: List[str] = None,
        poi: Optional[Dict[str, List]] = None,
        text: List[str] = [],
        new_accessory: List[str] = None,
        m_c = None,
        r_c: List[list] = None,
        injury: list = None,
        exclude_involved: list = None,
        history: list = None,
        relationships: list = None,
        other_clan: dict = None,
        supplies: list = None,
        new_gender: List[str] = None,
        future_event: dict = None,
        nr_involved_clans: int = None
    ):
        super().__init__(
            event_id, 
            location, 
            season, 
            poi=poi,
            sub_type=sub_type,
            text=text, 
            new_accessory=new_accessory, 
            m_c=m_c, 
            injury=injury, 
            exclude_involved=exclude_involved, 
            history=history, 
            relationships=relationships, 
            other_clan=other_clan,
            supplies=supplies,
            new_gender=new_gender, 
            future_event=future_event)
        self.r_c = r_c
        self.nr_involved_clans = nr_involved_clans
        self.involved_clans = []
        self.random_cats = []
        self.custom_mapping = {}

    def execute_event(self):
        """
        Handles the execution of this event.
        :param other_clan: the object for the other clan involved in this event
        """
        self.additional_event_text = ""
        self.text = choice(self.text_template)
        self.all_involved_cat_ids.clear()

        self.types = ["other_clans", "interaction"]

        self.all_involved_cat_ids.append(self.main_cat.ID)

        if not self.random_cats:
            print(f"{self.event_id} event did not get any cats?")
            return

        for c in self.random_cats:
            self.all_involved_cat_ids.append(c.ID)

        # remove cats from involved_cats if they're supposed to be
        if self.r_c and "r_c" in self.exclude_involved:
            self.all_involved_cat_ids.remove(self.random_cats[0].ID)
        for i in range(len(self.r_c)):
            if f"r_c{i+1}" in self.exclude_involved:
                self.all_involved_cat_ids.remove(self.random_cats[i].ID)
        if "m_c" in self.exclude_involved:
            self.all_involved_cat_ids.remove(self.main_cat.ID)

        # give accessory
        if self.new_accessory:
            if self.handle_accessories() is False:
                return

        # update gender
        if self.new_gender:
            self.handle_transition()

        custom_mapping = {}
        for i in range(len(self.r_c)):
            custom_mapping[f"r_c{i+1}"] = (
                str(self.random_cats[i].name),
                choice(self.random_cats[i].pronouns),
            )
        clan = game.clan.group_ID_to_clan(self.involved_clans[0])
        self.custom_mapping["c_n"] = (i18n.t("general.clan", name=clan.displayname), {})
        for i, o_clan in enumerate(self.involved_clans[1:], start=1):
            o_clan = game.clan.group_ID_to_clan(o_clan)
            custom_mapping[f"o_c_n{i}"] = (i18n.t("general.clan", name=o_clan.displayname), {})
            if i == 1:
                custom_mapping[f"o_c_n"] = (i18n.t("general.clan", name=o_clan.displayname), {})

        self.text = process_text(self.text, custom_mapping)

        # change relationships before killing anyone
        if self.relationships:
            # we're doing this here to make sure rel logs get adjusted text
            self.text = event_text_adjust(
                Cat,
                self.text,
                main_cat=self.main_cat,
                clan=clan,
                random_cat=self.random_cats[0]
            )
            for change in self.relationships:
                for group in change.get("log", []):
                    change["log"][group] = process_text(change["log"][group], custom_mapping)

            unpack_rel_block(Cat, self.relationships, self, clan=clan)

        # handle injuries and injury history
        self.handle_injury()

        # change other_clan rep
        if self.other_clan:
            for other_clan in self.involved_clans[1:]:
                change_clan_relations(clan, game.clan.group_ID_to_clan(other_clan), self.other_clan["changed"])

        # change supplies
        # if self.supplies:
        #     for block in self.supplies:
        #         if "misc" not in self.types:
        #             self.types.append("misc")
        #         if block["type"] == "freshkill":
        #             self.handle_freshkill_supply(block)
        #         else:  # if freshkill isn't being adjusted, then it must be an herb supply
        #             self.handle_herb_supply(block)

        # adjust text again to account for info that wasn't available when we do rel changes
        self.text = event_text_adjust(
            Cat,
            self.text,
            main_cat=self.main_cat,
            clan=clan,
            random_cat=self.random_cats[0],
        )

        for clan_id in self.involved_clans:
            game.cur_events_list.append(
                Single_Event(
                    self.text + " " + self.additional_event_text,
                    self.types,
                    self.all_involved_cat_ids,
                    clan=clan_id
                )
            )
        self.involved_clans.clear()
        self.random_cats.clear()
        self.custom_mapping = {}
        self.main_cat = None

    def handle_injury(self):
        """
        assigns an injury to involved cats and then assigns possible histories
        """

        # if no injury block, then no injury gets assigned
        if not self.injury:
            return

        if "health" not in self.types:
            self.types.append("health")
            self.types.remove("interaction")

        # now go through each injury block
        for block in self.injury:
            cats_affected = block["cats"]
            potential_scars = block.get("scars", ())

            # find all possible injuries
            possible_injuries = []
            for injury in block["injuries"]:
                if injury in constants.INJURY_GROUPS:
                    possible_injuries.extend(constants.INJURY_GROUPS[injury])
                else:
                    possible_injuries.append(injury)

            # give the injury
            for abbr in cats_affected:
                # MAIN CAT
                if abbr == "m_c":
                    injury = choice(possible_injuries)
                    self.main_cat.get_injured(injury, potential_scars=potential_scars)
                    self.handle_injury_history(self.main_cat, "m_c", injury)

                # RANDOM CAT
                elif abbr == "r_c":
                    injury = choice(possible_injuries)
                    for random_cat in self.random_cats:
                        random_cat.get_injured(injury, potential_scars=potential_scars)
                        self.handle_injury_history(random_cat, "r_c", injury)

                # NEW CATS
                elif "r_c" in abbr:
                    injury = choice(possible_injuries)
                    random_cat = self.random_cats[int(abbr.strip("r_c"))-1]
                    random_cat.get_injured(
                        injury, potential_scars=potential_scars
                    )
                    self.handle_injury_history(random_cat, abbr, injury)

    def handle_injury_history(self, cat, cat_abbr, injury=None):
        """
        handle injury histories
        :param cat: the cat object for cat being injured
        :param cat_abbr: the abbreviation used for this cat within the event format (i.e. m_c, r_c, ect)
        :param injury: the injury being given, if in classic then leave this as the default None
        """
        # TODO: problematic as we currently cannot mark who is the r_c and who is the m_c
        #  should consider if we can have history text be converted to use the cat's ID number in place of abbrs

        # if injury is false then this is classic, and they just need scar history

        for block in self.history:
            if "scar" not in block:
                return
            elif cat_abbr in block["cats"]:
                possible_scar = history_text_adjust(
                    block["scar"], 
                    self.custom_mapping["o_c_n"][0], 
                    cat.status.fetch_clan_object(game.clan), 
                    self.random_cats[0] if cat_abbr == "m_c" else self.main_cat
                )
                possible_death = history_text_adjust(
                    block["death"],
                    self.custom_mapping["o_c_n"][0],
                    cat.status.fetch_clan_object(game.clan),
                    self.random_cats[0] if cat_abbr == "m_c" else self.main_cat,
                )
                if possible_scar or possible_death:
                    cat.history.add_possible_history(
                        injury,
                        scar_text=possible_scar,
                        death_text=possible_death,
                        other_cat=self.random_cats[0] if cat_abbr == "m_c" else self.main_cat,
                    )
