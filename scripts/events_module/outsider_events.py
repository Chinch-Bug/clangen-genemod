import random

from scripts.rabbit.rabbits import Rabbit
from scripts.rabbit.history import History
from scripts.event_class import Single_Event
from scripts.game_structure.game_essentials import game


# ---------------------------------------------------------------------------- #
#                               New Rabbit Event Class                              #
# ---------------------------------------------------------------------------- #


class OutsiderEvents:
    """All events with a connection to outsiders."""

    @staticmethod
    def killing_outsiders(rabbit: Rabbit):
        if "lead_den_outsider_event" in game.warren.clan_settings:
            if game.warren.clan_settings["lead_den_outsider_event"]:
                info_dict = game.warren.clan_settings["lead_den_outsider_event"]
                if rabbit.ID == info_dict["cat_ID"]:
                    return

        # killing outside rabbits
        if rabbit.outside:
            if random.getrandbits(6) == 1 and not rabbit.dead:
                death_history = "m_c died outside of the Warren."
                if rabbit.exiled:
                    text = f"Rumors reach your Warren that the exiled {rabbit.name} has died recently."
                elif rabbit.status in ["kittypet", "loner", "rogue", "former Clancat"]:
                    text = (
                        f"Rumors reach your Warren that the {rabbit.status} "
                        f"{rabbit.name} has died recently."
                    )
                    death_history = "m_c died while roaming around."
                else:  # only lost rabbits are left
                    rabbit.outside = False
                    text = (
                        f"Will they reach Inle, even so far away? {rabbit.name} isn't sure, "
                        f"but as they drift away, they hope to see "
                        f"familiar starry fur on the other side."
                    )
                    death_history = (
                        "m_c died while being lost and trying to get back to the Warren."
                    )

                History.add_death(rabbit, death_text=death_history)
                rabbit.die()
                game.cur_events_list.append(
                    Single_Event(text, "birth_death", cat_dict={"m_c": rabbit})
                )

    @staticmethod
    def lost_cat_become_outsider(rabbit: Rabbit):
        """
        this will be for lost rabbits becoming kittypets/loners/etc
        TODO: need to make a unique backstory for these rabbits so they still have thoughts related to their warren
        """
        if random.getrandbits(7) == 1 and not rabbit.dead:
            OutsiderEvents.become_kittypet(rabbit)

    @staticmethod
    def become_kittypet(rabbit: Rabbit):
        # TODO: Make backstory for all of these + for exiled rabbits
        rabbit.status = "kittypet"

    @staticmethod
    def become_loner(rabbit: Rabbit):
        rabbit.status = "loner"

    @staticmethod
    def become_rogue(rabbit: Rabbit):
        """Rabbits will probably only become rogues if they were exiled formerly"""
        rabbit.status = "rogue"
