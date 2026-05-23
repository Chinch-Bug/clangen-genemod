import random

from typing import TYPE_CHECKING

import i18n

from scripts.cat.enums import CatGroup
from scripts.clan_package.settings import get_clan_setting
from scripts.event_class import Single_Event
from scripts.config import get_config
from scripts.game_structure import game
from scripts.events_module.text_adjust import event_text_adjust
from scripts.game_structure.localization import load_lang_resource

if TYPE_CHECKING:
    from scripts.cat.cats import Cat

# ---------------------------------------------------------------------------- #
#                               New Cat Event Class                              #
# ---------------------------------------------------------------------------- #


class OutsiderEvents:
    """All events with a connection to outsiders."""

    @staticmethod
    def killing_outsiders(cat: "Cat", clan=game.clan):
        if info_dict := get_clan_setting("lead_den_outsider_event"):
            if cat.ID == info_dict["cat_ID"]:
                return

        deaths = load_lang_resource("events/death/outsider_deaths/outsider_deaths.json")

        # killing outside cats
        if cat.status.is_outsider or game.clan.clancount == "singleclan" and cat.status.is_other_clancat:
            age_start = get_config(game.clan, "death_related.old_age_death_start")
            death_curve_setting = get_config(game.clan, "death_related.old_age_death_curve")
            death_curve_value = 0.001 * death_curve_setting
            old_age_death_chance = ((1 + death_curve_value) ** (cat.moons - age_start)) - 1
            if random.getrandbits(int(get_config(game.clan, "outsider_events.outsider_death"))) == 1 or random.random() <= old_age_death_chance and not cat.dead:
                death_history = i18n.t("events.death.outsider_deaths.history.default")
                if cat.status.is_exiled(CatGroup.PLAYER_CLAN_ID if game.clan.clancount == "singleclan" else None):
                    text = random.choice(deaths["exiled"])
                    death_history = i18n.t("events.death.outsider_deaths.history.exiled")
                elif cat.status.is_lost(CatGroup.PLAYER_CLAN_ID if game.clan.clancount == "singleclan" else None):
                    text = random.choice(deaths["lost"])
                    death_history = i18n.t("events.death.outsider_deaths.history.lost")
                elif game.clan.clancount == "singleclan" and cat.status.is_other_clancat or cat.status.is_former_clancat:
                    group_id = cat.status.get_last_valid_group_id()
                    if cat.status.is_exiled(group_id):
                        text = random.choice(deaths["other_clan_exiled"])
                        death_history = i18n.t(
                            "events.death.outsider_deaths.history.other_clan_exiled"
                        )
                    elif cat.status.is_lost(group_id):
                        text = random.choice(deaths["other_clan_lost"])
                        death_history = i18n.t(
                            "events.death.outsider_deaths.history.other_clan_lost"
                        )
                    elif cat.status.is_other_clancat:
                        text = random.choice(deaths["other_clan"])
                        death_history = i18n.t(
                            "events.death.outsider_deaths.history.other_clan"
                        )
                    else:
                        text = random.choice(deaths[cat.status.social.value])
                        death_history = i18n.t(
                            f"events.death.outsider_deaths.history.{cat.status.social.value}"
                        )

                    clanname = [
                        c for c in [game.clan] + game.clan.all_other_clans if c.group_ID == group_id
                    ][0].displayname
                    clanname = i18n.t("general.clan", name=clanname)
                    text = text.replace("o_c_n", clanname)
                    death_history = death_history.replace("o_c_n", clanname)
                elif cat.status.is_outsider:
                    text = random.choice(deaths[cat.status.social.value])
                    death_history = i18n.t(
                        f"events.death.outsider_deaths.history.{cat.status.social.value}"
                    )
                
                cat.history.add_death(death_text=death_history)
                cat.die(grief_allowed=False)
                game.cur_events_list.append(
                    Single_Event(text, "birth_death", cat_dict={"m_c": cat}, clan=cat.status.get_last_living_group())
                )

    @staticmethod
    def outsider_wander(cat: "Cat", clan=game.clan):
        if get_clan_setting("lead_den_outsider_event"):
            info_dict = get_clan_setting("lead_den_outsider_event")
            if cat.ID == info_dict["cat_ID"]:
                return

        wander_events = load_lang_resource("events/death/outsider_deaths/outsider_wander.json")
        return_events = load_lang_resource("events/death/outsider_deaths/outsider_return.json")

        # move outsider cats away from the Clan automatically
        if cat.status.is_outsider:
            if random.getrandbits(int(get_config(game.clan, "outsider_events.outsider_wander_off"))) == 1 and not cat.dead and not cat.age.is_baby() and cat.status.is_near():
                if cat.status.is_exiled(CatGroup.PLAYER_CLAN_ID if game.clan.clancount == "singleclan" else None):
                    text = random.choice(wander_events["exiled"])
                elif cat.status.is_lost(CatGroup.PLAYER_CLAN_ID if game.clan.clancount == "singleclan" else None):
                    text = random.choice(wander_events["lost"])
                elif game.clan.clancount == "singleclan" and cat.status.is_former_clancat:
                    group_id = cat.status.get_last_valid_group_id()
                    if cat.status.is_exiled(group_id):
                        text = random.choice(wander_events["other_clan_exiled"])
                    elif cat.status.is_lost(group_id):
                        text = random.choice(wander_events["other_clan_lost"])
                    else:
                        text = random.choice(wander_events["other_clan"])

                    clanname = [
                        c for c in [game.clan] + game.clan.all_other_clans if c.group_ID == group_id
                    ][0].displayname
                    clanname = i18n.t("general.clan", name=clanname)
                    text = text.replace("o_c_n", clanname)
                else:
                    text = random.choice(wander_events[cat.status.social.value])
                text = event_text_adjust(cat, text, main_cat=cat)
                game.cur_events_list.append(
                    Single_Event(text, "misc", cat_dict={
                                 "m_c": cat}, clan=cat.status.get_last_valid_group_id())
                )
                cat.status.change_group_nearness(clan.group_ID)
            elif random.getrandbits(int(get_config(game.clan, "outsider_events.outsider_return"))) == 1 and not cat.dead and not cat.status.is_near():
                if cat.status.is_exiled(CatGroup.PLAYER_CLAN_ID if game.clan.clancount == "singleclan" else None):
                    text = random.choice(return_events["exiled"])
                elif cat.status.is_lost(CatGroup.PLAYER_CLAN_ID if game.clan.clancount == "singleclan" else None):
                    text = random.choice(return_events["lost"])
                elif game.clan.clancount == "singleclan" and cat.status.is_former_clancat:
                    group_id = cat.status.get_last_valid_group_id()
                    if cat.status.is_exiled(group_id):
                        text = random.choice(return_events["other_clan_exiled"])
                    elif cat.status.is_lost(group_id):
                        text = random.choice(return_events["other_clan_lost"])
                    else:
                        text = random.choice(return_events["other_clan"])

                    clanname = [
                        c for c in [game.clan] + game.clan.all_other_clans if c.group_ID == group_id
                    ][0].displayname
                    clanname = i18n.t("general.clan", name=clanname)
                    text = text.replace("o_c_n", clanname)
                else:
                    text = random.choice(
                        return_events[cat.status.social.value])
                text = event_text_adjust(cat, text, main_cat=cat)
                game.cur_events_list.append(
                    Single_Event(text, "misc", cat_dict={
                                 "m_c": cat}, clan=cat.status.get_last_valid_group_id())
                )
                cat.status.change_group_nearness(clan.group_ID)
