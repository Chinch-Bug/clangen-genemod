import random

from scripts.cat.cats import Cat
from scripts.cat.history import History
from scripts.event_class import Single_Event
from scripts.game_structure.game_essentials import game


# ---------------------------------------------------------------------------- #
#                               New Cat Event Class                              #
# ---------------------------------------------------------------------------- #


class OutsiderEvents:
    """All events with a connection to outsiders."""

    @staticmethod
    def killing_outsiders(cat: Cat):
        if "lead_den_outsider_event" in game.clan.clan_settings:
            if game.clan.clan_settings["lead_den_outsider_event"]:
                info_dict = game.clan.clan_settings["lead_den_outsider_event"]
                if cat.ID == info_dict["cat_ID"]:
                    return

        # killing outside cats
        if cat.outside:
            age_start = game.config["death_related"]["old_age_death_start"]
            death_curve_setting = game.config["death_related"]["old_age_death_curve"]
            death_curve_value = 0.001 * death_curve_setting
            old_age_death_chance = ((1 + death_curve_value) ** (cat.moons - age_start)) - 1
            if random.getrandbits(6) == 1 or random.random() <= old_age_death_chance and not cat.dead:
                death_history = "m_c died outside of the Clan."
                if cat.exiled:
                    text = f"Rumors reach your Clan that the exiled {cat.name} has died recently."
                elif cat.group == "outsider cat":
                    text = (
                        f"Rumors reach your Clan that the {cat.status} "
                        f"{cat.name} has died recently."
                    )
                    death_history = "m_c died while roaming around."
                else:  # only lost cats are left
                    cat.outside = False
                    text = (
                        f"Will they reach StarClan, even so far away? {cat.name} isn't sure, "
                        f"but as they drift away, they hope to see "
                        f"familiar starry fur on the other side."
                    )
                    death_history = (
                        "m_c died while being lost and trying to get back to the Clan."
                    )

                History.add_death(cat, death_text=death_history)
                cat.die(False, clan=game.clan)
                game.cur_events_list.append(
                    Single_Event(text, "birth_death", cat_dict={"m_c": cat}, clan=None if cat.group in [" ", "outsider cat"] else cat.group)
                )

    @staticmethod
    def lost_cat_become_outsider(cat: Cat):
        """
        this will be for lost cats becoming kittypets/loners/etc
        TODO: need to make a unique backstory for these cats so they still have thoughts related to their clan
        """
        if random.getrandbits(7) == 1 and not cat.dead:
            OutsiderEvents.become_kittypet(cat)

    @staticmethod
    def become_kittypet(cat: Cat):
        # TODO: Make backstory for all of these + for exiled cats
        cat.status = "kittypet"

    @staticmethod
    def become_loner(cat: Cat):
        cat.status = "loner"

    @staticmethod
    def become_rogue(cat: Cat):
        """Cats will probably only become rogues if they were exiled formerly"""
        cat.status = "rogue"
