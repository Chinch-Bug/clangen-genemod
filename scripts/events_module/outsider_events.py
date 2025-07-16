import random

from typing import TYPE_CHECKING

from scripts.cat.enums import CatGroup
from scripts.clan_package.settings import get_clan_setting
from scripts.event_class import Single_Event
from scripts.game_structure.game_essentials import game
from scripts.game_structure import constants

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
            if random.getrandbits(6) == 1 or random.random() <= old_age_death_chance and not cat.dead:
                death_history = "m_c died outside of the Clan."
                if cat.status.is_exiled(CatGroup.PLAYER_CLAN):
                    text = f"Rumors reach your Clan that the exiled {cat.name} has died recently."
                elif cat.status.is_lost(cat.status.get_last_living_group()):
                    text = (
                        f"Will they reach StarClan, even so far away? {cat.name} isn't sure, "
                        f"but as they drift away, they hope to see "
                        f"familiar starry fur on the other side."
                    )
                    death_history = (
                        "m_c died while being lost and trying to get back to the Clan."
                    )
                else:
                    text = (
                        f"Rumors reach your Clan that the {cat.status.social.replace('_', ' ')} "
                        f"{cat.name} has died recently."
                    )
                    death_history = "m_c died while roaming around."

                cat.history.add_death(death_text=death_history)
                cat.die(False)
                game.cur_events_list.append(
                    Single_Event(text, "birth_death", cat_dict={"m_c": cat}, clan=clan.enum)
                )
