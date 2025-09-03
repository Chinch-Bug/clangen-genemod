import random

from typing import TYPE_CHECKING

import i18n

from scripts.cat.enums import CatGroup, CatSocial
from scripts.clan_package.settings import get_clan_setting
from scripts.event_class import Single_Event
from scripts.game_structure import constants
from scripts.game_structure import game
from scripts.utility import (
    event_text_adjust,
)

if TYPE_CHECKING:
    from scripts.cat.cats import Cat

# ---------------------------------------------------------------------------- #
#                               New Cat Event Class                              #
# ---------------------------------------------------------------------------- #


class OutsiderEvents:
    """All events with a connection to outsiders."""

    @staticmethod
    def killing_outsiders(cat: "Cat", clan=game.clan):
        if get_clan_setting("lead_den_outsider_event"):
            info_dict = get_clan_setting("lead_den_outsider_event")
            if cat.ID == info_dict["cat_ID"]:
                return

        # killing outside cats
        if cat.status.is_outsider:
            age_start = constants.CONFIG["death_related"]["old_age_death_start"]
            death_curve_setting = constants.CONFIG["death_related"]["old_age_death_curve"]
            death_curve_value = 0.001 * death_curve_setting
            old_age_death_chance = ((1 + death_curve_value) ** (cat.moons - age_start)) - 1
            if random.getrandbits(int(constants.CONFIG["outsider_events"]["outsider_death"])) == 1 or random.random() <= old_age_death_chance and not cat.dead:
                death_history = "m_c died outside of the Clan."
                if cat.status.is_exiled():
                    text = f"Rumors reach your Clan that the exiled {cat.name} has died recently."
                elif cat.status.is_lost():
                    text = (
                        f"Will they reach StarClan, even so far away? {cat.name} isn't sure, "
                        f"but as they drift away, they hope to see "
                        f"familiar starry fur on the other side."
                    )
                    death_history = (
                        "m_c died while being lost and trying to get back to the Clan."
                    )

                else:
                    social = i18n.t(f"general.{cat.status.social}", count=1)
                    text = (
                        f"Rumors reach your Clan that the {social}, "
                        f"{cat.name}, has died recently."
                    )
                    death_history = "m_c died while roaming around."
                cat.history.add_death(death_text=death_history)
                cat.die()
                game.cur_events_list.append(
                    Single_Event(text, "birth_death", cat_dict={"m_c": cat}, clan=clan.group_ID)
                )

    @staticmethod
    def outsider_wander(cat: "Cat", clan=game.clan):
        if get_clan_setting("lead_den_outsider_event"):
            info_dict = get_clan_setting("lead_den_outsider_event")
            if cat.ID == info_dict["cat_ID"]:
                return

        # move outsider cats away from the Clan automatically
        if cat.status.is_outsider:
            if random.getrandbits(int(constants.CONFIG["outsider_events"]["outsider_wander_off"])) == 1 and not cat.dead and not cat.age.is_baby() and cat.status.is_near():
                if cat.status.is_exiled():
                    text = f"The Clan hasn't scented the exiled {cat.name} nearby in a while."
                elif cat.status.is_lost():
                    text = (
                        f"Time away from the Clan has given {cat.name} a lot of room to think. "
                        "Following a call to adventure, {PRONOUN/m_c/subject/CAP} {VERB/m_c/wander/wanders} even farther afield."
                    )

                else:
                    social = i18n.t(f"general.{cat.status.social}", count=1)
                    text = (
                        f"Sightings of the {social}, {cat.name}, have stopped as of recent."
                    )
                text = event_text_adjust(cat, text, main_cat=cat)
                game.cur_events_list.append(
                    Single_Event(text, "misc", cat_dict={
                                 "m_c": cat}, clan=clan.group_ID)
                )
                cat.status.change_group_nearness(clan.group_ID)
