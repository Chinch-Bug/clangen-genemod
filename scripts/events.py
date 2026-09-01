# pylint: disable=line-too-long
"""

TODO: Docs


"""
import logging
import random

from scripts.cat.microservices.add_to_clan import add_dependents_to_clan, add_to_clan
from scripts.cat_relations.cat_handle_funcs import create_relationships_new_cat
from scripts.config import get_config

# pylint: enable=line-too-long
import traceback

import i18n

from scripts.cat.cats import Cat, cat_class
from scripts.cat.constants import BACKSTORIES
from scripts.cat.enums import (
    CatAge,
    CatRank,
    CatGroup,
    CatStanding,
    CatSocial,
)
from scripts.cat.names import Name
from scripts.cat.save_load import save_cats, add_cat_to_fade_id
from scripts.clan_package.settings import get_clan_setting, set_clan_setting
from scripts.clan_resources.freshkill import FRESHKILL_EVENT_ACTIVE
from scripts.conditions import (
    medicine_cats_can_cover_clan,
    get_amount_cat_for_one_medic,
)
from scripts.cat.microservices.conditions import get_ill, get_injured, get_permanent_condition
from scripts.events_module.event_information import EventInformation
from scripts.events_module.event_filters import event_for_other_clan
from scripts.events_module.ceremony.perform_ceremony import (
    check_for_ceremony,
    trigger_ceremony,
    check_and_promote_deputy,
)

from scripts.events_module.generate_events import GenerateEvents, generate_events
from scripts.events_module.outsider import outsider_events
from scripts.events_module.patrol.patrol import Patrol
from scripts.events_module.relationship import relation_events
from scripts.events_module.relationship.crossclan_event_generation import handle_crossclan_relationships
from scripts.events_module.pregnancy import pregnancy_events
from scripts.events_module.short.condition_events import Condition_Events
from scripts.events_module.short.short_event_generation import create_short_event
from scripts.events_module.thoughts.generate_thoughts import get_new_thought
from scripts.events_module.transition.generate_transition_event import (
    attempt_coming_out,
)
from scripts.game_structure.game.switches import (
    Switch,
    switch_get_value,
    switch_set_value,
)
from scripts.game_structure import game
from scripts.game_structure.localization import load_lang_resource
from scripts.ui.windows.save_error import SaveErrorWindow
from scripts.events_module.text_adjust import (
    ongoing_event_text_adjust,
    event_text_adjust,
    adjust_list_text,
    history_text_adjust,
)
from scripts.events_module.consequences import unpack_rel_block
from scripts.clan_package.cotc import (
    change_clan_reputation,
    change_clan_relations,
    get_other_clan,
)
from scripts.clan_package.get_clan_cats import (
    find_alive_cats_with_rank,
    get_living_clan_cat_count,
)

logger = logging.getLogger(__name__)


all_events = {}
new_cat_invited = False
WAR_TXT = None
war_lang = None

def one_moon():
    """
    Handles the moon skipping of the whole Clan.
    """
    global new_cat_invited
    game.cur_events_list = []
    game.herb_events_list = []
    game.freshkill_event_list = []
    game.mediated = []
    switch_set_value(Switch.saved_clan, False)
    new_cat_invited = False
    relation_events.clear_trigger_dict()
    Patrol.used_patrols["normal"].clear()
    Patrol.used_patrols["romance"].clear()
    game.patrolled.clear()
    game.just_died.clear()

    if any(
        cat.status.rank.is_active_clan_rank() and cat.status.alive_in_player_clan
        for cat in Cat.all_cats.values()
    ):
        # todo: this links nowhere, can it be removed?
        switch_set_value(Switch.no_able_left, False)

    # age up the clan, set current season
    game.clan.age += 1

    update_afterlife_temper()
    pregnancy_events.increment_pregnancy_age()
    check_war()

    if (
        game.clan.game_mode in ("expanded", "cruel_season")
        and game.clan.freshkill_pile
    ):
        # feed the cats and update the nutrient status
        relevant_cats = list(
            filter(
                lambda _cat: _cat.status.alive_in_player_clan,
                Cat.all_cats.values(),
            )
        )
        game.clan.freshkill_pile.time_skip(relevant_cats, game.freshkill_event_list)
        # get the moonskip freshkill
        get_moon_freshkill()

    # Adding in any potential lead den events that have been saved
    if get_clan_setting("lead_den_interaction"):
        handle_lead_den_event()

    clancount = game.clan.clancount == "multiclan"
    
    # checking if a lost cat returns on their own
    rejoin_upperbound = get_config("lost_cat.rejoin_chance")
    if random.randint(1, rejoin_upperbound) == 1:
        handle_lost_cats_return(clan=game.clan)
    
    handle_tnr_return(clan=game.clan)

    if clancount:
        for clan in game.clan.all_other_clans:
            if random.randint(1, rejoin_upperbound) == 1:
                handle_lost_cats_return(clan=clan)
            handle_tnr_return(clan=clan)

    #Kill kits as needed
    faded_kits = {}
    for clan in [game.clan] + game.clan.all_other_clans:
        if get_clan_setting('modded_kits'):
            faded_kits[clan.prefix] = kit_deaths(Cat.all_cats_list, clan=clan)
        else:
            faded_kits[clan.prefix] = []
        if not clancount:
            break

    trigger_future_events(clan=game.clan)

    if clancount:
        for clan in game.clan.all_other_clans:
            trigger_future_events(clan=clan)

    # Calling of "one_moon" functions.
    for cat in Cat.all_cats_list.copy():
        cat.thought = None
        if not cat.status.group_ID or (cat.status.is_other_clancat and game.clan.clancount == "singleclan"):
            one_moon_outside_cat(cat)
        elif cat.status.group.is_any_clan_group() or cat.status.group.is_afterlife():
            one_moon_cat(cat, cat.status.fetch_clan_object(game.clan))
        cat.pelt.rebuild_sprite = True

    # keeping this commented out till disasters are more polished
    # disaster_events.handle_disasters()

    # Handle grief events.
    if game.clan.grief_strings:
        # Grab all the dead or outside cats, who should not have grief text
        for ID in game.clan.grief_strings.copy():
            check_cat = Cat.all_cats.get(ID)
            if isinstance(check_cat, Cat):
                if check_cat.dead or check_cat.status.is_outsider:
                    game.clan.grief_strings.pop(ID)
            else:
                game.clan.grief_strings.pop(ID)

        # Generate events
        for cat_id, details in game.clan.grief_strings.items():
            for _info in details:
                text = _info[0]
                cats = _info[1]
                grief_type = _info[2]

                if grief_type == "minor":
                    # we get a new thought directly instead of using assign_thought
                    # because we need to include a specific other cat
                    get_new_thought(
                        main_cat=Cat.fetch_cat(cat_id),
                        thought_type=text,
                        other_cat=Cat.fetch_cat(cats[0]),
                    )

                else:
                    game.cur_events_list.append(
                        EventInformation(text, ["birth_death", "relation"], cats, clan=Cat.fetch_cat(cat_id).status.group_ID)
                    )

        game.clan.grief_strings.clear()

    if game.dead_cats_to_grieve:
        ghost_names = {}
        sorted_dead_cats = {}
        shaken_cats = {}
        extra_event = None
        for ghost in game.dead_cats_to_grieve:
            last_living = ghost.status.get_last_living_group()
            if ghost.status.is_exiled(last_living) or ghost.status.has_left(last_living):
                pass
            elif last_living == CatGroup.PLAYER_CLAN_ID:
                if game.clan.prefix not in ghost_names:
                    ghost_names[game.clan.prefix] = []
                    sorted_dead_cats[game.clan.prefix] = []
                ghost_names[game.clan.prefix].append(str(ghost.name))
                sorted_dead_cats[game.clan.prefix].append(ghost)
            elif group := next(filter(lambda c: last_living == c.group_ID, game.clan.all_other_clans), None):
                group = ghost.status.fetch_clan_object()
                if group.prefix not in ghost_names:
                    ghost_names[group.prefix] = []
                    sorted_dead_cats[group.prefix] = []
                ghost_names[group.prefix].append(str(ghost.name))
                sorted_dead_cats[group.prefix].append(ghost)
        for clan in [game.clan] + game.clan.all_other_clans:
            if clan.prefix not in ghost_names:
                continue
            extra_event = None
            insert = adjust_list_text(ghost_names[clan.prefix])

            if len(ghost_names[clan.prefix]) > 1:
                event = i18n.t(
                    "hardcoded.event_deaths", count=len(ghost_names[clan.prefix]), insert=insert
                )

                if len(ghost_names[clan.prefix])-len(faded_kits.get(clan.prefix, [])) > 2:
                    alive_cats = list(
                        filter(
                            lambda kitty: (
                                not kitty.status.is_leader and kitty.status.group_ID == clan.group_ID
                            ),
                            Cat.all_cats.values(),
                        )
                    )
                    # finds a percentage of the living Clan to become shaken

                    if len(alive_cats) == 0:
                        return
                    else:
                        shaken_cats[clan.prefix] = random.sample(
                            alive_cats,
                            k=max(
                                int((len(alive_cats) * random.randint(4, 6)) / 100),
                                1,
                            ),
                        )

                    shaken_cat_names = []
                    for cat in shaken_cats[clan.prefix]:
                        shaken_cat_names.append(str(cat.name))
                        get_injured(
                            cat,
                            "shock",
                            event_triggered=False,
                            lethal=False,
                            severity="minor"
                        )

                    insert = adjust_list_text(shaken_cat_names)

                    extra_event = i18n.t(
                        "hardcoded.event_shaken_grief",
                        count=len(shaken_cat_names),
                        insert=insert,
                    )

            else:
                event = i18n.t("hardcoded.event_deaths", count=1)
                #event = event_text_adjust(Cat, event, main_cat=Cat.dead_cats[0])

            game.cur_events_list.append(
                EventInformation(
                    event_text_adjust(Cat, event, main_cat=sorted_dead_cats[clan.prefix][0], clan=clan),
                    ["birth_death"],
                    [i.ID for i in sorted_dead_cats[clan.prefix]],
                    cat_dict={"m_c": (sorted_dead_cats[clan.prefix])[0]} 
                    if len(sorted_dead_cats[clan.prefix]) == 1 else None,
                    clan=clan.group_ID
                )
            )
            if extra_event:
                game.cur_events_list.append(
                    EventInformation(
                        event_text_adjust(Cat, extra_event, clan=clan), 
                        ["birth_death"], 
                        [i.ID for i in shaken_cats.get(clan.prefix, [])], 
                        clan=clan.group_ID
                    )
                )
            
            if not clancount:
                break
        game.dead_cats_to_grieve.clear()

    if (
        game.clan.game_mode in ("expanded", "cruel_season")
        and game.clan.freshkill_pile
    ):
        # make a notification if the Clan does not have enough prey
        if (
            FRESHKILL_EVENT_ACTIVE
            and not game.clan.freshkill_pile.clan_has_enough_food()
        ):
            event_string = i18n.t("defaults.warn_low_freshkill")
            game.cur_events_list.insert(0, EventInformation(event_string, clan=game.clan.group_ID))
            game.freshkill_event_list.append(event_string)

    handle_focus()

    # handle the herb supply for the moon
    game.clan.herb_supply.handle_moon(
        clan_size=get_living_clan_cat_count(Cat),
        clan_cats=[c for c in Cat.all_cats_list if c.status.alive_in_player_clan],
        med_cats=find_alive_cats_with_rank(
            Cat,
            ranks=[CatRank.MEDICINE_CAT, CatRank.MEDICINE_APPRENTICE],
            working=True,
        ),
    )

    if game.clan.game_mode in ("expanded", "cruel_season"):
        amount_per_med = get_amount_cat_for_one_medic()
        med_fulfilled = medicine_cats_can_cover_clan(
            Cat.all_cats.values(), amount_per_med, clan=CatGroup.PLAYER_CLAN_ID
        )

        if not med_fulfilled:
            string = i18n.t("defaults.warn_low_medcats")
            game.cur_events_list.insert(0, EventInformation(string, ["health"], clan=game.clan.group_ID))
    else:
        has_med = any(
            cat.status.rank.is_any_medicine_rank()
            and cat.status.alive_in_player_clan
            for cat in Cat.all_cats.values()
        )
        if not has_med:
            string = event_text_adjust(Cat, i18n.t("defaults.warn_no_medcats"), clan=game.clan)
            game.cur_events_list.insert(0, EventInformation(string, "health", clan=game.clan.group_ID))
    if clancount:
        for oc in game.clan.all_other_clans:
            has_med = any(
                cat.status.rank.is_any_medicine_rank()
                and cat.status.group_ID == oc.group_ID
                for cat in Cat.all_cats.values()
            )
            if not has_med:
                string = event_text_adjust(Cat, i18n.t("defaults.warn_no_medcats"), clan=oc)
                game.cur_events_list.insert(0, EventInformation(string, "health", clan=oc.group_ID))


    # Clear the list of cats that died this moon.
    game.just_died.clear()

    # Check for mentorless apprentices
    check_missing_mentors()

    # Promote leader and deputy, if needed.
    for clan in [game.clan] + game.clan.all_other_clans:
        check_leader(clan)
        check_and_promote_deputy(clan)
        if not clancount:
            break

    if clancount:
        handle_crossclan_relationships()

    # Resort
    if switch_get_value(Switch.sort_type) != "id":
        Cat.sort_cats()

    # Clear all the loaded event dicts.
    GenerateEvents.clear_loaded_events()

    # autosave
    if get_clan_setting("autosave") and game.clan.age % 5 == 0:
        try:
            save_cats(switch_get_value(Switch.clan_save_id), Cat, game)
            game.clan.save_clan()
            game.clan.save_pregnancy(game.clan)
            game.save_events()
        except:
            SaveErrorWindow(traceback.format_exc())


def update_afterlife_temper():
    """
    Updates the temperaments of the afterlives based off cats who have newly joined an afterlife.
    """
    for c in game.updated_afterlife_cats:
        if not c.status.did_join_group_this_moon:
            continue

        # only high ranks and guides can influence
        if (
            c.status.rank
            not in (
                CatRank.LEADER,
                CatRank.MEDICINE_CAT,
                CatRank.DEPUTY,
            )
            and c not in [game.clan.instructor] + [clan.instructor for clan in game.clan.all_other_clans]
        ):
            continue

        # first change facets of the group they joined
        if (
            c.status.group == CatGroup.STARCLAN
            and c.ID not in game.starclan.influencing_cats
        ):
            game.starclan.adjust_facets_by_cat(c)
            # then remove them from other afterlife, if they were there
            if c.ID in game.dark_forest.influencing_cats:
                game.dark_forest.adjust_facets_by_cat(c, do_removal=True)

        # now do same for DF
        elif (
            c.status.group == CatGroup.DARK_FOREST
            and c.ID not in game.dark_forest.influencing_cats
        ):
            game.dark_forest.adjust_facets_by_cat(c)
            if c.ID in game.starclan.influencing_cats:
                game.starclan.adjust_facets_by_cat(c, do_removal=True)

    game.updated_afterlife_cats.clear()


def trigger_future_events(clan):
    """
    Handles aging and triggering future events.
    """
    removals = []

    for event in game.clan.future_events:
        if event.clan != clan.group_ID:
            continue
        event.moon_delay -= 1
        # we give events a buffer of 12 moons to allow any season-locked events a chance to trigger, then we remove
        if event.moon_delay <= -12:
            removals.append(event)
            continue
        # attempt to trigger event
        if event.moon_delay <= 0:
            create_short_event(
                event_type=event.event_type,
                main_cat=Cat.fetch_cat(event.involved_cats.get("m_c")),
                random_cat=Cat.fetch_cat(event.involved_cats.get("r_c")),
                victim_cat=Cat.fetch_cat(event.involved_cats.get("mur_c")),
                sub_type=event.pool.get("sub_type"),
                future_event=event,
                clan=clan
            )
            if event.triggered:
                removals.append(event)

    for event in removals:
        if event in game.clan.future_events:
            game.clan.future_events.remove(event)

def handle_lead_den_event():
    """
    Handles the events that are chosen in the leaders den the previous moon and resets the relevant clan settings
    """
    if get_clan_setting("lead_den_clan_event"):
        info_dict = get_clan_setting("lead_den_clan_event")
        gathering_cat = Cat.fetch_cat(info_dict["cat_ID"])

        # drop the event if the gathering cat is no longer available
        if not gathering_cat.status.alive_in_player_clan:
            return

        other_clan = get_other_clan(info_dict["other_clan"])

        # get events
        events = generate_events.possible_lead_den_events(
            cat=gathering_cat,
            other_clan_temper=other_clan.temperament,
            player_clan_temper=info_dict["player_clan_temper"],
            event_type="other_clan",
            interaction_type=info_dict["interaction_type"],
            success=info_dict["success"],
        )
        chosen_event = random.choice(events)

        # get text
        event_text = chosen_event["event_text"]

        # change relations and append relation text
        rel_change = chosen_event["rel_change"]
        game.clan.set_relations(game.clan, other_clan, None, rel_change)
        if rel_change > 0:
            event_text += i18n.t("hardcoded.relations_improved")
        elif rel_change == 0:
            event_text += i18n.t("hardcoded.relations_neutral")
        else:
            event_text += i18n.t("hardcoded.relations_worsened")

        # adjust text and add to event list
        event_text = event_text_adjust(
            Cat,
            event_text,
            main_cat=gathering_cat,
            other_clan=other_clan,
            clan=game.clan,
        )
        game.cur_events_list.insert(
            4, EventInformation(event_text, "other_clans", [gathering_cat.ID], clan=game.clan.group_ID)
        )

        set_clan_setting("lead_den_clan_event", {})

    if get_clan_setting("lead_den_outsider_event"):
        info_dict = get_clan_setting("lead_den_outsider_event")
        outsider_cat = Cat.fetch_cat(info_dict["cat_ID"])
        involved_cats = [outsider_cat.ID]
        invited_cats = []

        events = generate_events.possible_lead_den_events(
            cat=outsider_cat,
            event_type="outsider",
            interaction_type=info_dict["interaction_type"],
            success=info_dict["success"],
        )
        chosen_event = random.choice(events)

        # get event text
        event_text = chosen_event["event_text"]
        cat_dict = chosen_event["m_c"]

        # ADJUST REP
        game.clan.reputation += chosen_event["rep_change"]

        additional_kits = None
        # SUCCESS/FAIL
        if info_dict["success"]:
            if info_dict["interaction_type"] == "hunt":
                outsider_cat.history.add_death(
                    death_text=history_text_adjust(
                        i18n.t("hardcoded.lead_den_killed"),
                        other_clan_name=None,
                        clan=game.clan,
                    ),
                )
                outsider_cat.die()

            elif info_dict["interaction_type"] == "drive":
                outsider_cat.status.change_group_nearness(CatGroup.PLAYER_CLAN_ID)

            elif info_dict["interaction_type"] in ("invite", "search"):
                # ADD TO CLAN AND CHECK FOR KITS
                add_to_clan(outsider_cat, game.clan.group_ID)
                additional_kits = add_dependents_to_clan(outsider_cat, game.clan.group_ID)

                if additional_kits:
                    event_text += i18n.t(
                        "hardcoded.event_lost_kits", count=len(additional_kits)
                    )

                    for kit_ID in additional_kits:
                        # add to involved cat list
                        involved_cats.append(kit_ID)

                invited_cats = [outsider_cat.ID]
                invited_cats.extend(additional_kits)

                for cat_ID in invited_cats:
                    invited_cat = Cat.fetch_cat(cat_ID)
                    # some things to handle if the cat has not been in the clan before
                    if (
                        CatStanding.EXILED
                        not in invited_cat.status.get_standing_with_group(
                            CatGroup.PLAYER_CLAN_ID
                        )
                    ):
                        # reset to make sure backstory makes sense
                        if "guided" in invited_cat.backstory:
                            invited_cat.backstory = "outsider1"
                        # if the cat is a healer, give healer rank
                        elif (
                            invited_cat.backstory
                            in BACKSTORIES["backstory_categories"][
                                "healer_backstories"
                            ]
                        ):
                            if invited_cat.age == CatAge.ADOLESCENT:
                                invited_cat.status._change_rank(CatRank.MEDICINE_APPRENTICE)
                            else:
                                invited_cat.status._change_rank(CatRank.MEDICINE_CAT)
                        # if cat is a little baby, check name
                        elif invited_cat.age in (CatAge.NEWBORN, CatAge.KITTEN):
                            if not invited_cat.name.suffix:
                                invited_cat.name = Name(
                                    invited_cat,
                                    invited_cat.name.prefix,
                                    invited_cat.name.suffix,
                                    biome=game.clan.biome,
                                )
                                invited_cat.name.give_suffix(
                                    skills=invited_cat.skills,
                                    personality=invited_cat.personality,
                                    biome=game.clan.biome
                                    if not game.clan.override_biome
                                    else game.clan.override_biome,
                                )
                                invited_cat.specsuffix_hidden = False
                        # if cat is an apprentice, make sure they get a mentor!
                        if invited_cat.status.rank.is_any_apprentice_rank():
                            invited_cat.update_mentor()
                        # if the cat chose to become a mediator but the settings don't allow it, make them a warrior instead
                        if (
                            invited_cat.status.rank == CatRank.MEDIATOR
                            and not get_clan_setting("become_mediator")
                        ):
                            invited_cat.status._change_rank(CatRank.WARRIOR)

                    create_relationships_new_cat(invited_cat)

            # this handles ceremonies for cats coming into the clan
            if invited_cats:
                handle_lost_cats_return(invited_cats)

        # give new thought to cats
        if "new_thought" in cat_dict:
            outsider_cat.thought = event_text_adjust(
                Cat,
                text=cat_dict["new_thought"],
                main_cat=outsider_cat,
                clan=game.clan)

        if "kit_thought" in cat_dict:
            if additional_kits is None:
                additional_kits = outsider_cat.get_children()
            if additional_kits:
                for kit_ID in additional_kits:
                    kit = Cat.fetch_cat(kit_ID)
                    if kit.dead:
                        continue
                    kit.thought = event_text_adjust(
                        Cat,
                        text=cat_dict["kit_thought"],
                        main_cat=kit,
                        clan=game.clan)

        if "relationships" in cat_dict:
            unpack_rel_block(Cat, cat_dict["relationships"], extra_cat=outsider_cat, clan=game.clan)

        # adjust text and add to event list
        event_text = event_text_adjust(
            Cat,
            text=event_text,
            main_cat=outsider_cat,
            clan=game.clan,
        )

        game.cur_events_list.insert(
            4, EventInformation(event_text, ["misc"], involved_cats, clan=game.clan.group_ID)
        )
        set_clan_setting("lead_den_outsider_event", {})

    set_clan_setting("lead_den_interaction", False)

def get_moon_freshkill():
    """Adding auto freshkill for the current moon."""

    prey_amount = game.clan.freshkill_pile.get_moonskip_catch_amount()
    game.freshkill_event_list.append(
        i18n.t("hardcoded.prey_catch_count", count=prey_amount)
    )
    game.clan.freshkill_pile.add_freshkill(prey_amount)

def handle_focus():
    """
    This function should be called late in the 'one_moon' function and handles all focuses which are possible to handle here:
        - business as usual
        - hunting
        - herb gathering
        - threaten outsiders
        - seek outsiders
        - sabotage other clans
        - aid other clans
        - raid other clans
        - hoarding
    Focus which are not able to be handled here:
        rest_and_recover - handled in:
            - 'handle_outbreaks'
            - 'condition_events.handle_injuries'
            - 'condition_events.handle_illnesses'
            - 'cat.moon_skip_illness'
            - 'cat.moon_skip_injury'
    """
    # if no focus is selected, skip all other
    focus_text = i18n.t("defaults.focus_text")
    if get_clan_setting("business_as_usual") or get_clan_setting("rest_and_recover"):
        return
    elif get_clan_setting("hunting"):
        # handle warrior
        healthy_warriors = [
            cat
            for cat in Cat.all_cats.values()
            if cat.status.rank.is_any_adult_warrior_like_rank()
            and cat.status.alive_in_player_clan
            and cat.available_to_work()
        ]

        warrior_amount = len(healthy_warriors) * get_config(f"focus.hunting.{CatRank.WARRIOR}")

        # handle apprentices
        healthy_apprentices = [
            cat
            for cat in Cat.all_cats.values()
            if cat.status.rank == CatRank.APPRENTICE and cat.available_to_work()
            and cat.status.alive_in_player_clan
        ]

        app_amount = len(healthy_apprentices) * get_config(f"focus.hunting.{CatRank.APPRENTICE}")

        if warrior_amount + app_amount == 0:
            healthy_other = list(
                filter(
                    lambda c: c.moons > 3
                    and c.status.alive_in_player_clan
                    and not c.not_working(),
                    Cat.all_cats.values(),
                )
            )
            warrior_amount = (
                len(healthy_other) * get_config("focus.hunting.emergency")
            )

        # finish
        total_amount = warrior_amount + app_amount
        game.clan.freshkill_pile.add_freshkill(total_amount)
        focus_text = i18n.t("hardcoded.focus_prey", count=total_amount)
        game.freshkill_event_list.append(focus_text)

    elif get_clan_setting("herb_gathering"):
        # get medicine cats
        healthy_meds = find_alive_cats_with_rank(
            Cat,
            ranks=[CatRank.MEDICINE_CAT, CatRank.MEDICINE_APPRENTICE],
            working=True,
        )
        # get warriors to help
        healthy_warriors = find_alive_cats_with_rank(
            Cat,
            ranks=[CatRank.WARRIOR, CatRank.DEPUTY, CatRank.LEADER],
            working=True,
        )

        focus_text = game.clan.herb_supply.handle_focus(
            healthy_meds, healthy_warriors
        )

    elif get_clan_setting("threaten_outsiders"):
        amount = get_config("focus.outsiders.reputation")
        change_clan_reputation(-amount, game.clan)
        focus_text = None

    elif get_clan_setting("seek_outsiders"):
        amount = get_config("focus.outsiders.reputation")
        change_clan_reputation(amount, game.clan)
        focus_text = None

    elif get_clan_setting("sabotage_other_clans") or get_clan_setting(
        "aid_other_clans"
    ):
        amount = get_config("focus.other_clans.relation")
        if get_clan_setting("sabotage_other_clans"):
            amount = amount * -1
        for name in game.clan.clans_in_focus:
            clan = [clan for clan in game.clan.all_other_clans if clan.name == name or clan.prefix == name][0]
            change_clan_relations(game.clan, clan, amount)
        focus_text = None

    elif get_clan_setting("hoarding") or get_clan_setting("raid_other_clans"):
        info_dict = get_config("focus.hoarding")
        if get_clan_setting("raid_other_clans"):
            info_dict = get_config("focus.raid_other_clans")

        involved_cats = {"injured": [], "sick": []}
        # handle prey
        healthy_warriors = list(
            filter(
                lambda c: c.status.rank.is_any_adult_warrior_like_rank()
                and c.status.alive_in_player_clan
                and not c.not_working(),
                Cat.all_cats.values(),
            )
        )
        warrior_amount = len(healthy_warriors) * info_dict["prey_warrior"]
        game.clan.freshkill_pile.add_freshkill(warrior_amount)
        game.freshkill_event_list.append(
            i18n.t("hardcoded.focus_raid_prey", count=warrior_amount)
        )

        # handle herbs
        healthy_meds = list(
            filter(
                lambda c: c.status.rank == CatRank.MEDICINE_CAT
                and c.status.alive_in_player_clan
                and not c.not_working(),
                Cat.all_cats.values(),
            )
        )

        herb_focus_text = game.clan.herb_supply.handle_focus(healthy_meds)

        # handle injuries / illness
        relevant_cats = healthy_warriors + healthy_meds
        if get_clan_setting("raid_other_clans"):
            chance = info_dict[f"injury_chance_warrior"]
            # increase the chance of injuries depending on how many clans are raided
            increase = info_dict["chance_increase_per_clan"]
            chance -= increase * len(game.clan.clans_in_focus)
        for cat in relevant_cats:
            # if the raid setting or 50/50 for hoarding to get to the injury part
            if get_clan_setting("raid_other_clans") or random.getrandbits(1):
                status_use = cat.status.rank
                if status_use in (CatRank.DEPUTY, CatRank.LEADER):
                    status_use = CatRank.WARRIOR
                chance = info_dict[f"injury_chance_{status_use}"]
                if get_clan_setting("raid_other_clans"):
                    # increase the chance of injuries depending on how many clans are raided
                    increase = info_dict["chance_increase_per_clan"]
                    chance -= increase * len(game.clan.clans_in_focus)

                if not int(random.random() * chance):  # 1/chance
                    possible_injuries = []
                    injury_dict = info_dict["injuries"]
                    for injury, amount in injury_dict.items():
                        possible_injuries.extend([injury] * amount)
                    chosen_injury = random.choice(possible_injuries)
                    get_injured(cat, chosen_injury)
                    involved_cats["injured"].append(cat.ID)
            else:
                chance = info_dict["illness_chance"]
                if not int(random.random() * chance):  # 1/chance
                    possible_illnesses = []
                    injury_dict = info_dict["illnesses"]
                    for illness, amount in injury_dict.items():
                        possible_illnesses.extend([illness] * amount)
                    chosen_illness = random.choice(possible_illnesses)
                    get_ill(cat, chosen_illness)
                    involved_cats["sick"].append(cat.ID)

        # if it is raiding, lower the relation to other clans
        if get_clan_setting("raid_other_clans"):
            for name in game.clan.clans_in_focus:
                clan = [clan for clan in game.clan.all_other_clans if clan.name == name][0]
                amount = -info_dict["relation"]
                change_clan_relations(game.clan, clan, amount)

        # finish
        text_snippet = "hardcoded.focus_injury_hoarding"
        if get_clan_setting("raid_other_clans"):
            text_snippet = "hardcoded.focus_injury_raiding"
        for condition_type, value in involved_cats.items():
            if len(value) > 0:
                game.cur_events_list.insert(
                    0,
                    EventInformation(
                        i18n.t(text_snippet, condition=condition_type, count=len(value)),
                        ["health"],
                        value,
                        clan=game.clan.group_ID
                    )
                )

        focus_text = i18n.t("hardcoded.focus_prey", count=warrior_amount)

        if herb_focus_text:
            focus_text += f" {herb_focus_text}"

    if focus_text:
        game.cur_events_list.insert(0, EventInformation(focus_text, "misc", clan=game.clan.group_ID))

def handle_tnr_return(clan=game.clan):
    eligible_cats = []
    cat_IDs = []
    for cat in Cat.all_cats.values():
        if not cat.status.is_lost(clan.group_ID) or not cat.status.is_outsider:
            continue
        TNRed = True if ('sterile' in cat.permanent_condition and 'TNR' in cat.pelt.scars and 
        game.clan.age - cat.permanent_condition['sterile']['moon_start'] == 1) else False
        if (cat.status.is_outsider
        and not cat.dead
        and TNRed):
            rejoin_upperbound = get_config("lost_cat.rejoin_tnr_chance")
            if random.randint(1, rejoin_upperbound) == 1 or "recovering from birth" in cat.injuries:
                eligible_cats.append(cat)
                cat_IDs.append(cat.ID)
    
    if len(eligible_cats) == 0:
        return

    names = ', '.join([str(x.name) for x in eligible_cats[:-1]]) + ' and ' + str(eligible_cats[-1].name) if len(eligible_cats) > 1 else eligible_cats[0].name

    text = i18n.t('hardcoded.event_tnr_return', cats=names, count=len(eligible_cats))   
    for cat in eligible_cats:
        add_to_clan(cat, clan.group_ID)
        additional = add_dependents_to_clan(cat, clan.group_ID, False)
        for x in additional:
            if x in Cat.all_cats:
                Cat.all_cats[x].backstory = 'kittypet' + str(random.randint(1, 4))
                Cat.all_cats[x].name.suffix = ''
                get_permanent_condition(Cat.all_cats[x], "sterile", False, custom_reveal=4)
    text = event_text_adjust(Cat, text, main_cat=eligible_cats[0], clan=clan)
    game.cur_events_list.append(EventInformation(text, ["misc"], cat_IDs, clan=clan.group_ID))
    
    handle_lost_cats_return(cat_IDs, clan)

def handle_lost_cats_return(predetermined_cat_IDs: list = None, clan = game.clan):
    """
    TODO: DOCS
    """
    cat_IDs = []
    if predetermined_cat_IDs:
        cat_IDs = predetermined_cat_IDs

    if not predetermined_cat_IDs:
        eligible_cats = []
        for cat in Cat.all_cats.values():
            if cat.dead or not cat.status.is_lost(clan.group_ID) or not cat.status.is_outsider:
                continue

            if "sterile" not in cat.permanent_condition or game.clan.age - cat.permanent_condition["sterile"]["moon_start"] > -1:
                eligible_cats.append(cat)

        if not eligible_cats:
            return

        lost_cat = random.choice(eligible_cats)
        if lost_cat.age in (CatAge.NEWBORN, CatAge.KITTEN):
            return

        cat_IDs.append(lost_cat.ID)

        if lost_cat.status.is_former_clancat or lost_cat.status.is_outsider:
            text = i18n.t(f"hardcoded.event_lost{random.choice(range(1,5))}")
        else:
            # this would be the child of a lost cat, who inherited the lost status from the parent and was never a clancat
            text = i18n.t(
                "hardcoded.event_returning_child_of_lost",
                parent_name=Cat.fetch_cat(lost_cat.parent1).name,
            )

        add_to_clan(lost_cat, clan.group_ID)
        additional_cats = add_dependents_to_clan(lost_cat, clan.group_ID)
        cat_IDs.extend(additional_cats)

        if additional_cats:
            text += i18n.t("hardcoded.event_lost_kits", count=len(additional_cats))

        text = event_text_adjust(Cat, text, main_cat=lost_cat, clan=clan)

        game.cur_events_list.append(EventInformation(text, ["misc"], cat_IDs, clan=clan.group_ID))

    # Perform a ceremony if needed
    for cat_ID in cat_IDs:
        x = Cat.fetch_cat(cat_ID)
        if x.status.rank in [
            CatRank.APPRENTICE,
            CatRank.MEDICINE_APPRENTICE,
            CatRank.MEDIATOR_APPRENTICE,
            CatRank.KITTEN,
            CatRank.NEWBORN,
        ]:
            if x.moons >= 15:
                if x.status.rank == CatRank.MEDICINE_APPRENTICE:
                    trigger_ceremony(x, CatRank.MEDICINE_CAT)
                elif x.status.rank == CatRank.MEDIATOR_APPRENTICE:
                    trigger_ceremony(x, CatRank.MEDIATOR)
                else:
                    trigger_ceremony(x, CatRank.WARRIOR)
            elif not x.status.rank.is_any_apprentice_rank() and x.moons >= 6:
                trigger_ceremony(x, CatRank.APPRENTICE)

def handle_fading(cat, clan, forced=False):
    """
    TODO: DOCS
    """
    if (
        get_clan_setting("fading")
        and not cat.prevent_fading
        and cat.ID not in [clan.instructor.ID for clan in game.clan.all_other_clans if clan.instructor] + [game.clan.instructor.ID]
        and not cat.faded
    ) or forced:
        age_to_fade = get_config("fading.age_to_fade")
        kitten_fade = get_config("fading.kit_fade")
        opacity_at_fade = get_config("fading.opacity_at_fade")
        fading_speed = get_config("fading.visual_fading_speed")
        # Handle opacity
        cat.pelt.opacity = int(
            (100 - opacity_at_fade)
            * (1 - (cat.dead_for / age_to_fade) ** fading_speed)
            + opacity_at_fade
        )

        # Deal with fading the cat if they are old enough.
        if forced or cat.dead_for > age_to_fade or (get_clan_setting('modded_kits') and cat.moons < 6 and cat.dead_for > kitten_fade):
            # If order not to add a cat to the faded list
            # twice, we can't remove them or add them to
            # faded cat list here. Rather, they are added to
            # a list of cats that will be "faded" at the next save.

            # Remove from med cat list, just in case.
            # This should never be triggered, but I've has an issue or
            # two with this, so here it is.
            if cat.ID in clan.med_cat_list:
                clan.med_cat_list.remove(cat.ID)

            # Unset their mate, if they have one
            if len(cat.mate) > 0:
                for mate_id in cat.mate:
                    if Cat.all_cats.get(mate_id):
                        cat.unset_mate(Cat.all_cats.get(mate_id))

            # If the cat is the current med, leader, or deputy, remove them
            if clan.leader:
                if clan.leader.ID == cat.ID:
                    clan.leader = None
            if clan.deputy:
                if clan.deputy.ID == cat.ID:
                    clan.deputy = None
            if clan.medicine_cat:
                if clan.medicine_cat.ID == cat.ID:
                    if clan.med_cat_list:  # If there are other med cats
                        clan.medicine_cat = Cat.fetch_cat(
                            clan.med_cat_list[0]
                        )
                    else:
                        clan.medicine_cat = None

            add_cat_to_fade_id(cat.ID)
            cat.set_faded()

def one_moon_outside_cat(cat):
    """
    exiled cat events
    """
    # aging the cat
    clan = next(filter(lambda c: cat.status.is_lost(c.group_ID) or cat.status.is_exiled(c.group_ID), game.clan.all_other_clans), game.clan)
    # this will also handle increasing dead_for!
    cat.status.increase_current_moons_as()

    cat.one_moon()
    if cat.dead:
        return

    cat.manage_outside_trait()

    handle_outside_EX(cat)

    # handling the rank changes for Other Clan cats
    # this is SUPER rudimentary rn, really just a temp patch to handle our current little edge-cases
    if cat.status.is_other_clancat:
        # kitten to apprentice - for now it's going to be limited to warrior apprentices
        if cat.moons == cat_class.age_moons[CatAge.ADOLESCENT][0]:
            cat.status._change_rank(CatRank.APPRENTICE)
            # we aren't going to worry about sourcing a mentor, we're gonna pretend it's "hidden" from the player
        # apprentice to full
        if cat.moons >= cat_class.age_moons[CatAge.YOUNG_ADULT][0]:
            # warrior
            if cat.status.rank == CatRank.APPRENTICE:
                cat.status._change_rank(CatRank.WARRIOR)
            # med cat
            if cat.status.rank == CatRank.MEDICINE_APPRENTICE:
                cat.status._change_rank(CatRank.MEDICINE_CAT)
            # mediator (just in case)
            if cat.status.rank == CatRank.MEDIATOR_APPRENTICE:
                cat.status._change_rank(CatRank.MEDIATOR)
        # cat to elder
        if cat.moons >= cat_class.age_moons[CatAge.SENIOR][0]:
            # exclude the roles that don't really retire
            if cat.status.rank not in (CatRank.LEADER, CatRank.MEDICINE_CAT):
                cat.status._change_rank(CatRank.ELDER)

    # skill progression needs to be after rank progression
    cat.skills.progress_skill(cat)
    pregnancy_events.handle_having_kits(cat, clan=clan)

    if cat.is_ill() or cat.is_injured():
        if cat.is_ill() and cat.is_injured():
            if random.getrandbits(1):
                triggered_death = Condition_Events.handle_injuries(cat, clan=clan)
                if not triggered_death:
                    Condition_Events.handle_illnesses(cat, clan=clan)
            else:
                triggered_death = Condition_Events.handle_illnesses(cat, clan=clan)
                if not triggered_death:
                    Condition_Events.handle_injuries(cat, clan=clan)
        elif cat.is_ill():
            Condition_Events.handle_illnesses(cat, clan=clan)
        else:
            Condition_Events.handle_injuries(cat, clan=clan)
        switch_get_value(Switch.skip_conditions).clear()
        if cat.dead:
            return

    if not cat.dead:
        outsider_events.killing_outsiders(cat, clan)
        outsider_events.outsider_wander(cat, clan)
    
def kit_deaths(cats, clan=None):
    fading_kits = []
    fading_kit_names = []

    if len(find_alive_cats_with_rank(Cat, [CatRank.KITTEN], clan=clan.group_ID)):
        clan_queens = len(find_alive_cats_with_rank(Cat, [CatRank.QUEEN], working=True, clan=clan.group_ID))*3 + len(find_alive_cats_with_rank(Cat, [CatRank.QUEEN_APPRENTICE], working=True, clan=clan.group_ID))
        clan_queens = min(clan_queens/len(find_alive_cats_with_rank(Cat, [CatRank.KITTEN], clan=clan.group_ID)), 1)
        clan_queens *= get_config("death_related.max_queen_influence")

    death_chances = get_config("death_related.kit_death_chances")
    
    for kit in cats:
        if kit.dead or kit.status.social == CatSocial.KITTYPET:
            continue
        
        multiplier = 1-(clan_queens) if kit.status.group_ID == clan.group_ID and kit.status.rank == CatRank.KITTEN else 1
        multiplier *= 1.25 if kit.phenotype.growth_pattern == "runt" else 1
        if kit.moons < 2 and ((kit.status.is_outsider and clan.group_ID == game.clan.group_ID) or kit.status.group_ID == clan.group_ID):
            if random.random() < death_chances[str(kit.moons)] * multiplier:
                if not kit.status.is_outsider:
                    fading_kits.append(kit.ID)
                    fading_kit_names.append(str(kit.name))
                    kit.die(True)
                else:
                    kit.die(False)
                kit.history.add_death(str(kit.name) + " failed to thrive.")
                kit.moons -= 1
        elif kit.moons < 6 and kit.status.group_ID == clan.group_ID:
            if random.random() < death_chances[str(kit.moons)] * multiplier:
                create_short_event(
                            event_type="birth_death",
                            main_cat=kit,
                            clan=clan)
                if kit.dead:
                    kit.moons -= 1

    if len(fading_kits) > 0:
        event_text = ""
        event_text += ", ".join(fading_kit_names)
        if len(fading_kits) > 1:
            event_text += " were"
        else:
            event_text += " was"
        event_text += " lost this moon."
        game.cur_events_list.append(EventInformation(event_text, ['birth_death'], fading_kits, clan=clan.group_ID))
    
    return fading_kits



def queen_influence(cat):
    """Queens and queen apprentices can influence kits every moon"""

    personality = cat.personality.trait
    queens = find_alive_cats_with_rank(Cat, [CatRank.QUEEN, CatRank.QUEEN_APPRENTICE], clan=cat.status.group_ID)
    has_rel = []
    values = {}
    for c in queens:
        if c.ID in cat.relationships:
            has_rel.append(c)
            values[c.ID] = cat.relationships[c.ID].respect + cat.relationships[c.ID].trust + cat.relationships[c.ID].like + cat.relationships[c.ID].comfort
    if not has_rel:
        return

    negative_influence = False
    has_rel.sort(reverse=True,
        key=lambda c: abs(cat.relationships[c.ID].respect) + abs(cat.relationships[c.ID].trust) + abs(cat.relationships[c.ID].like) + abs(cat.relationships[c.ID].comfort))
    if values[has_rel[0].ID] < 0:
        negative_influence = True
    
    max_influence = random.randint(0, 1)
    i = 0
    while max_influence > i:
        i += 1
        affect_personality = cat.personality.mentor_influence(
            has_rel[0].personality, negative=negative_influence
        )
        affect_skills = None
        if not negative_influence:
            affect_skills = cat.skills.mentor_influence(has_rel[0])
        if affect_personality:
            cat.history.add_facet_queen_influence(
                has_rel[0].ID,
                affect_personality[0],
                affect_personality[1],
            )
            if cat.personality.trait != personality and (not cat.history.prev_pers or cat.personality.trait != cat.history.prev_pers[-1]):
                cat.history.prev_pers.append(personality)
        if affect_skills:
            cat.history.add_skill_queen_influence(
                affect_skills[0], affect_skills[1], affect_skills[2]
            )

def one_moon_cat(cat, clan):
    """
    Triggers various moon events for a cat.
    -If dead, cat is given thought, dead_for count increased, and fading handled (then function is returned)
    -Outbreak chance is handled, death event is attempted, and conditions are handled (if death happens, return)
    -cat.one_moon() is triggered
    -mediator events are triggered (this includes the cat choosing to become a mediator)
    -freshkill pile events are triggered
    -if the cat is injured or ill, they're given their own set of possible events to avoid unrealistic behavior.
    They will handle disability events, coming out, pregnancy, apprentice EXP, ceremonies, relationship events, and
    will generate a new thought. Then the function is returned.
    -if the cat was not injured or ill, then they will do all of the above *and* trigger misc events, acc events,
    and new cat events
    """
    if cat.faded:
        return

    if cat.dead:
        if cat.ID in game.just_died:
            cat.moons += 1
        else:
            cat.status.increase_current_moons_as()
        if cat.moons > 0 and cat.status.rank == CatRank.NEWBORN:
            cat.status._change_rank(CatRank.KITTEN)
        handle_fading(cat, clan)  # Deal with fading.
        return

    if cat.status.rank == CatRank.KITTEN:
        queen_influence(cat)

    cat.status.increase_current_moons_as()

    # all actions, which do not trigger an event display and
    # are connected to cats are located in there
    cat.one_moon()

    if debug_type_override := get_config("event_generation.debug_type_override"):
        if debug_type_override in ["death", "injury"]:
            handle_injuries_or_general_death(cat, clan)
        elif debug_type_override == "misc":
            other_interactions(cat, clan)
        elif debug_type_override == "new_cat":
            invite_new_cats(cat, clan)

    # handle nutrition amount
    # (CARE: the cats have to be fed before this happens - should be handled in "one_moon" function)
    if (
        game.clan.game_mode in ("expanded", "cruel_season")
        and game.clan.freshkill_pile
        and cat.status.alive_in_player_clan
    ):
        Condition_Events.handle_nutrient(
            cat, game.clan.freshkill_pile.nutrition_info
        )

        if cat.dead:
            return

    # prevent injured or sick cats from unrealistic Clan events
    if cat.is_ill() or cat.is_injured():
        if cat.is_ill() and cat.is_injured():
            if random.getrandbits(1):
                triggered_death = Condition_Events.handle_injuries(cat, clan=clan)
                if not triggered_death:
                    Condition_Events.handle_illnesses(cat, clan=clan)
            else:
                triggered_death = Condition_Events.handle_illnesses(cat, clan=clan)
                if not triggered_death:
                    Condition_Events.handle_injuries(cat, clan=clan)
        elif cat.is_ill():
            Condition_Events.handle_illnesses(cat, clan=clan)
        else:
            Condition_Events.handle_injuries(cat, clan=clan)
        switch_set_value(Switch.skip_conditions, [])
        if cat.dead:
            return
        handle_outbreaks(cat, clan)

    # newborns don't do much
    if cat.status.rank == CatRank.NEWBORN:
        return

    handle_timeskip_EX(cat)  # This must be before perform_ceremonies!
    # this HAS TO be before the cat.is_disabled() so that disabled kits can choose a med cat or mediator position
    check_for_ceremony(cat, clan)
    cat.skills.progress_skill(cat)  # This must be done after ceremonies.

    # check for death/reveal/risks/retire caused by permanent conditions
    if cat.is_disabled():
        Condition_Events.handle_already_disabled(cat, clan)
        if cat.dead:
            return

    attempt_coming_out(cat, clan)
    pregnancy_events.handle_having_kits(cat, clan=clan)
    # Stop the timeskip if the cat died in childbirth
    if cat.dead:
        return

    handle_colour_changes(cat, clan)

    # relationships have to be handled separately, because of the ceremony name change
    if cat.status.group.is_any_clan_group():
        relation_events.handle_relationships(cat)

    # now we make sure ill and injured cats don't get interactions they shouldn't
    if cat.is_ill() or cat.is_injured():
        return

    invite_new_cats(cat, clan)
    other_interactions(cat, clan)
    gain_accessories(cat, clan)

    # switches between the two death handles
    if random.getrandbits(1):
        triggered_death = handle_injuries_or_general_death(cat, clan)
        if not triggered_death:
            handle_illnesses_or_illness_deaths(cat, clan)
        else:
            switch_set_value(Switch.skip_conditions, [])
            return
    else:
        triggered_death = handle_illnesses_or_illness_deaths(cat, clan)
        if not triggered_death:
            handle_injuries_or_general_death(cat, clan)
        else:
            switch_set_value(Switch.skip_conditions, [])
            return

    handle_murder(cat, clan)

    switch_set_value(Switch.skip_conditions, [])

def handle_colour_changes(cat, clan):
    involved_cats = [cat.ID]
    event_text = ""

    if cat.phenotype.white[0] == 'W' or (cat.phenotype.white[1] in ['ws', 'wt'] and cat.phenotype.whitegrade > 2) or cat.phenotype.pointgene[0] == 'c' or 'o' not in cat.phenotype.sexgene:
        return
    
    if cat.phenotype.brindledbi:
        red_colour = "white"
    elif cat.phenotype.dilute[0] == 'D' and cat.phenotype.pinkdilute[0] == 'Dp':
        red_colour = "orange"
    elif cat.phenotype.dilute[0] == 'd' and cat.phenotype.pinkdilute[0] == 'Dp':
        red_colour = "cream"
    elif cat.phenotype.dilute[0] == 'D' and cat.phenotype.pinkdilute[0] == 'dp':
        red_colour = "yellow"
    else:
        red_colour = 'creamy white'

    if cat.phenotype.ext[0] == 'ec' and cat.phenotype.agouti[0] == 'a' and cat.moons == 6:
        event_text = "Throughout kittenhood m_c has gotten many comments about their unique coat. Well, it looks by now to have turned completely " + red_colour + "."
    if cat.phenotype.ext[0] == 'ea' and ((cat.moons == 12 and cat.phenotype.agouti[0] != 'a') or (cat.moons == 36 and cat.phenotype.agouti[0] == 'a')):
        event_text = "m_c has gotten used to the odd comment of 'is your fur more "+ red_colour + " today?', having heard it practically since kithood. But by now, nobody can deny it, there's barely a trace of any other coat colour left."
    if cat.phenotype.ext[0] == 'er' and cat.moons == 24:
        event_text = "m_c has gotten used to the odd comment of 'is your fur more "+ red_colour + " today?', having heard it practically since kithood. But by now, nobody can deny it, there's barely a trace of any other coat colour left."

    if event_text:
        event_text = event_text_adjust(Cat, event_text, main_cat=cat)
        types = ["misc"]
        game.cur_events_list.append(EventInformation(event_text, types, involved_cats, clan=clan.group_ID))

def load_war_resources():
    global WAR_TXT, war_lang
    if war_lang == i18n.config.get("locale"):
        return
    WAR_TXT = load_lang_resource("events/war.json")
    war_lang = i18n.config.get("locale")

def check_war():
    """
    interactions with other clans
    """
    global WAR_TXT
    # if there are somehow no other clans, don't proceed
    if not game.clan.all_other_clans:
        return

    # Prevent wars from starting super early in the game.
    if game.clan.age <= 4:
        return
        
    switch_set_value(Switch.war_rel_change_type, {})
    
    for clan in game.clan.war:
        # check if war in progress
        started_war = False
        main_clan = game.clan if clan == game.clan.group_ID else [c for c in game.clan.all_other_clans if c.group_ID == clan][0]
        enemy_clan = None
        victor = None
        for enemy in game.clan.war[clan]:
            war_events: list = []
            enemy_clan = [c for c in game.clan.all_other_clans if c.group_ID == enemy][0]
            enemy_can_fight = game.clan.clancount == "singleclan" or event_for_other_clan(Cat, ["any_warrior_mult"], enemy)
            if game.clan.war[clan][enemy]["at_war"]:
                if not event_for_other_clan(Cat, ["any_warrior_mult"], clan) or not enemy_can_fight:
                    game.clan.war[clan][enemy]["at_war"] = False
                    game.clan.war[clan][enemy]["duration"] = 0
                    war_events = WAR_TXT["loss_events"]
                    victor = clan if not enemy_can_fight else enemy
                else:
                    threshold = 10
                    if enemy_clan.temperament[0] == "bloodthirsty":
                        threshold = 12
                    if enemy_clan.temperament[0] in ["mellow", "amiable", "gracious"]:
                        threshold = 7

                    threshold -= int(game.clan.war[clan][enemy]["duration"])
                    rel_value = game.clan.get_relations(main_clan, enemy_clan)
                    if rel_value < 0:
                        rel_value = 0

                    # check if war should conclude, if not, continue
                    if rel_value >= threshold and game.clan.war[clan][enemy]["duration"] > 1:
                        game.clan.war[clan][enemy]["at_war"] = False
                        game.clan.war[clan][enemy]["duration"] = 0
                        rel_value += 2
                        war_events = WAR_TXT["conclusion_events"]
                    else:  # try to influence the relation with warring clan
                        game.clan.war[clan][enemy]["duration"] += 1
                        choice = random.choice(
                            ["rel_up", "neutral", "rel_down", "rel_down", "rel_down"])
                        current_rels = switch_get_value(Switch.war_rel_change_type)
                        if not current_rels.get(clan):
                            current_rels[clan] = {}
                        current_rels[clan][enemy] = choice
                        switch_set_value(Switch.war_rel_change_type, current_rels)
                        war_events = WAR_TXT["progress_events"][choice]
                        if rel_value < 0:
                            rel_value = 0
                        if choice == "rel_up":
                            rel_value += 2
                        elif choice == "rel_down" and rel_value > 1:
                            rel_value -= 1

                    game.clan.set_relations(main_clan, enemy_clan, rel_value)

            else:  # try to start a war if no war in progress
                if started_war:
                    continue
                if not event_for_other_clan(Cat, ["any_warrior_mult"], clan) or not enemy_can_fight:
                    continue
                active_wars = max(len(game.clan.get_wars(clan)), len(game.clan.get_wars(enemy)))
                if active_wars and random.random() > 0.125:
                    continue
                threshold = 5
                if enemy_clan.temperament[0] == "bloodthirsty":
                    threshold = 10
                if enemy_clan.temperament[0] in ["mellow", "amiable", "gracious"]:
                    threshold = 3

                rel_value = game.clan.get_relations(main_clan, enemy_clan)

                if int(rel_value) <= threshold and not int(
                    random.random() * int(rel_value)
                ):
                    game.clan.war[clan][enemy]["at_war"] = True
                    war_events = WAR_TXT["trigger_events"]
                    current_rels = switch_get_value(Switch.war_rel_change_type)
                    if not current_rels.get(clan):
                        current_rels[clan] = {}
                    current_rels[clan][enemy] = "rel_down"
                    switch_set_value(Switch.war_rel_change_type, current_rels)
                    started_war = True

            # if nothing happened, return
            if not war_events or not enemy_clan or main_clan == enemy_clan:
                continue

            available_med = find_alive_cats_with_rank(Cat, [CatRank.MEDICINE_CAT], working=True, clan=main_clan.group_ID)
            war_events_copy = war_events.copy()
            if not main_clan.leader or not main_clan.deputy or not available_med:
                for event in war_events_copy:
                    if not main_clan.leader and "lead_name" in event:
                        war_events.remove(event)
                        continue
                    if not main_clan.deputy and "dep_name" in event:
                        war_events.remove(event)
                        continue
                    if not available_med and "med_name" in event:
                        war_events.remove(event)


            # grab our war "notice" for this moon
            event = random.choice(war_events)
            if not victor or victor == clan:
                event = ongoing_event_text_adjust(
                    Cat, event, other_clan_name=enemy_clan.name, clan=main_clan
                )
            else:
                event = ongoing_event_text_adjust(
                    Cat, event, other_clan_name=main_clan.name, clan=enemy_clan
                )
            game.cur_events_list.append(EventInformation(event, ["other_clans"], clan=clan))
            if game.clan.clancount == "multiclan":
                game.cur_events_list.append(EventInformation(event, ["other_clans"], clan=enemy))

def gain_accessories(cat, clan):
    """
    accessories
    """

    ceremony_accessory = switch_get_value(Switch.ceremony_accessory)

    if not cat:
        return

    if cat.status.group_ID != clan.group_ID:
        return

    # check if cat already has max acc
    if cat.pelt.accessory and len(cat.pelt.accessory) == 3:
        switch_set_value(Switch.ceremony_accessory, False)
        return

    # chance to gain acc
    acc_chances = get_config("accessory_generation")
    chance = acc_chances["base_acc_chance"]
    if cat.status.rank.is_any_medicine_rank():
        chance += acc_chances["med_modifier"]
    if cat.age in [CatAge.KITTEN, CatAge.ADOLESCENT]:
        chance += acc_chances["baby_modifier"]
    elif cat.age in [CatAge.SENIOR_ADULT, CatAge.SENIOR]:
        chance += acc_chances["elder_modifier"]
    if cat.personality.trait in [
        "adventurous",
        "childish",
        "confident",
        "daring",
        "playful",
        "attention-seeker",
        "sweet",
        "troublesome",
        "impulsive",
        "inquisitive",
        "strange",
        "shameless",
    ]:
        chance += acc_chances["happy_trait_modifier"]
    elif cat.personality.trait in [
        "cold",
        "strict",
        "bossy",
        "bullying",
        "insecure",
        "nervous",
    ]:
        chance += acc_chances["grumpy_trait_modifier"]
    if cat.pelt.accessory and len(cat.pelt.accessory) >= 1:
        chance += acc_chances["multiple_acc_modifier"]
    if ceremony_accessory:
        chance += acc_chances["ceremony_modifier"]

    # increase chance of acc if the cat had a ceremony
    if chance <= 0:
        chance = 1
    if not int(random.random() * chance):
        sub_type = ["accessory"]
        if ceremony_accessory:
            sub_type.append("ceremony")

        create_short_event(
            event_type="misc",
            main_cat=cat,
            sub_type=sub_type,
            clan=clan
        )

    switch_set_value(Switch.ceremony_accessory, False)

    return

# This gives outsiders exp. There may be a better spot for it to go,
# but I put it here to keep the exp functions together
def handle_outside_EX(cat):
    if cat.status.is_outsider or cat.status.is_other_clancat:
        if cat.not_working() and int(random.random() * 3):
            return

        if cat.age == CatAge.KITTEN:
            return

        exp_info = get_config("outsiders.outside_ex")

        if cat.age == CatAge.ADOLESCENT:
            ran = exp_info["base_adolescent_timeskip_ex"]
        elif cat.age == CatAge.SENIOR:
            ran = exp_info["base_senior_timeskip_ex"]
        else:
            ran = exp_info["base_adult_timeskip_ex"]

        role_modifier = 1
        if cat.status.social == CatSocial.KITTYPET:
            # Kittypets will gain exp at 2/3 the rate of loners or exiled cats, as this assumes they are
            # kept indoors at least part of the time and can't hunt/fight as much
            role_modifier = 0.6

        exp = random.choice(
            list(range(ran[0][0], ran[0][1] + 1))
            + list(range(ran[1][0], ran[1][1] + 1))
        )

        if exp > 0:
            cat.experience += max(exp * role_modifier, 1)

def handle_timeskip_EX(cat):
    """
    TODO: DOCS
    """

    if cat.ID in game.patrolled:
        return

    if cat.status.rank in [CatRank.NEWBORN, CatRank.KITTEN]:
        return
        
    if cat.not_working() and int(random.random() * 3):
        return
    
    exp_info = get_config("clancat_ex")

    if cat.status.rank.is_any_apprentice_rank():

        if cat.experience > cat.experience_levels_range["learning"][1]:
            return
    
        exp_info = get_config("clancat_ex")

        if cat.status.rank == CatRank.MEDICINE_APPRENTICE:
            ran = exp_info["base_med_app_timeskip_ex"]
        else:
            ran = exp_info["base_app_timeskip_ex"]

        mentor_modifier = 1
        if not cat.mentor or Cat.fetch_cat(cat.mentor).not_working():
            # Sick mentor debuff
            mentor_modifier = 0.7

        exp = random.choice(
            list(range(ran[0][0], ran[0][1] + 1))
            + list(range(ran[1][0], ran[1][1] + 1))
        )

        if cat.status.group_ID != CatGroup.PLAYER_CLAN_ID:
            exp += random.randint(0, 3)

        cat.add_experience(max(exp * mentor_modifier, 1))

    else:
        if cat.age == CatAge.SENIOR:
            ran = exp_info["base_senior_timeskip_ex"]
        else:
            ran = exp_info["base_adult_timeskip_ex"]

        role_modifier = 1
        if cat.status.rank.is_any_medicine_rank():
            # Healers just gain exp slower because reasons idk
            role_modifier = 0.6

        exp = random.choice(
            list(range(ran[0][0], ran[0][1] + 1))
            + list(range(ran[1][0], ran[1][1] + 1))
        )

        cat.add_experience(max(exp * role_modifier, 1))

def invite_new_cats(cat, clan=game.clan):
    """
    new cats
    """
    global new_cat_invited
    if get_config("event_generation.debug_type_override") == "new_cat":
        create_short_event(
            event_type="new_cat",
            main_cat=cat,
            clan=clan
        )
        return

    chance = 200

    clan_size = get_living_clan_cat_count(Cat, clan.group_ID)

    base_chance = 700
    if clan_size < 10:
        base_chance = 200
    elif clan_size < 30:
        base_chance = 300


    if clan != game.clan:
        # Increase chance if secondary Clan is smaller than main clan

        main_clan_alive_cats = get_living_clan_cat_count(Cat)
        ratio = clan_size / (main_clan_alive_cats or 1)

        if ratio < 0.33:
            base_chance = int(base_chance * ratio / 2)

        if ratio < 0.5:
            base_chance = int(base_chance * ratio)

        if ratio < 0.75:
            base_chance = int(base_chance * ratio * 1.25)

    reputation = 50
    reputation = clan.reputation

    # hostile
    if 1 <= reputation <= 30:
        if clan_size < 10:
            chance = base_chance
        else:
            rep_adjust = int(reputation / 2)
            if rep_adjust == 0:
                rep_adjust = 1
            chance = base_chance + int(300 / rep_adjust)
    # neutral
    elif 31 <= reputation <= 70:
        if clan_size < 10:
            chance = base_chance - reputation
        else:
            chance = base_chance
    # welcoming
    elif 71 <= reputation <= 100:
        chance = base_chance - reputation

    chance = max(chance, 1)

    if (
        not int(random.random() * chance)
        and not cat.age.is_baby()
        and not new_cat_invited
    ):
        new_cat_invited = True

        create_short_event(
            event_type="new_cat",
            main_cat=cat,
            clan=clan
        )

def other_interactions(cat, clan):
    """
    TODO: DOCS
    """
    if get_config("event_generation.debug_type_override") == "misc":
        create_short_event(
            event_type="misc",
            main_cat=cat,
            clan=clan
        )
        return

    hit = int(random.random() * 30)
    if hit:
        return

    create_short_event(
        event_type="misc",
        main_cat=cat,
        clan=clan
    )

def handle_injuries_or_general_death(cat, clan):
    """
    decide if cat dies
    """

    if get_config("event_generation.debug_type_override") == "death":
        create_short_event(
            event_type="birth_death",
            main_cat=cat,
            clan=clan
        )
        return
    elif get_config("event_generation.debug_type_override") == "injury":
        Condition_Events.handle_injuries(cat, clan)
        return

    use_war_modifier = switch_get_value(Switch.war_rel_change_type) != "rel_up" and game.clan.get_wars(clan)

    # chance to kill leader: 1/50 by default
    leader_death_chance = get_config("death_related.leader_death_chance") - (
        get_config("death_related.war_death_modifier_leader") if use_war_modifier else 0
    )

    if (
        not int(random.random() * leader_death_chance)
        and cat.status.is_leader
        and not cat.not_working()
    ):
        create_short_event(
            event_type="birth_death",
            main_cat=cat,
            clan=clan
        )

        return True

    # chance to die of old age
    age_start = get_config("death_related.old_age_death_start")
    death_curve_setting = get_config("death_related.old_age_death_curve")
    death_curve_value = 0.001 * death_curve_setting
    # made old_age_death_chance into a separate value to make testing with print statements easier
    old_age_death_chance = ((1 + death_curve_value) ** (cat.moons - age_start)) - 1
    if random.random() <= old_age_death_chance:
        create_short_event(
            event_type="birth_death",
            main_cat=cat,
            sub_type=["old_age"],
            clan=clan
        )
        return True
    # max age has been indicated to be 300, so if a cat reaches that age, they die of old age
    elif cat.moons >= 300:
        create_short_event(
            event_type="birth_death",
            main_cat=cat,
            sub_type=["old_age"],
            clan=clan
        )
        return True
    
    # disaster death chance
    if get_clan_setting("disasters"):
        if not random.getrandbits(get_config("death_related.mass_death_chance")):  # 1/512
            create_short_event(
                event_type="birth_death",
                main_cat=cat,
                sub_type=["mass_death"],
                clan=clan,
            )
            return True

    # final death chance and then, if not triggered, head to injuries
    path = (
        "death_related.classic_death_chance"
        if game.clan.game_mode == "classic"
        else "death_related.death_chance"
    )
    death_chance = get_config(path) - (
        get_config("death_related.war_death_modifier") if use_war_modifier else 0
    )
    if not cat.age.is_baby():
        death_chance += get_config("death_related.size_modifiers")[cat.phenotype.height_label]
    if not int(random.random() * death_chance) and not cat.not_working():  # 1/400
        create_short_event(
            event_type="birth_death",
            main_cat=cat,
            clan=clan
        )
        return True
    else:
        triggered_death = Condition_Events.handle_injuries(cat, clan)

        return triggered_death

def handle_murder(cat, clan):
    """Handles murder"""

    if cat.age.is_baby():
        return
        
    relationships = cat.relationships.values()
    targets = []

    # if this cat is unstable and aggressive, we lower the random murder chance
    random_murder_chance = int(get_config("death_related.murder.base_random_murder_chance"))

    # Check to see if random murder is triggered.
    # If so, we allow targets to be anyone they have even the smallest amount of negativity for
    if random.getrandbits(max(1, random_murder_chance)) == 1:
        targets = [
            Cat.fetch_cat(i)
            for i in Cat.all_cats
            if Cat.fetch_cat(i).status.group.is_any_clan_group()
            and i != cat.ID
        ]
        if not targets:
            return

        if (
            get_config("death_related.murder.deputy_prefer_leader")
            and cat.status.rank == CatRank.DEPUTY
        ):
            possible_targets = [c for c in targets if c.status.is_leader and c.status.group_ID == cat.status.group_ID]
            if possible_targets:
                targets = possible_targets

        chosen_cat = random.choice(targets)

        create_short_event(
            event_type="birth_death",
            main_cat=chosen_cat,
            random_cat=cat,
            sub_type=["murder"],
            clan=clan,
            second_clan=chosen_cat.status.fetch_clan_object(game.clan) if chosen_cat.status.group_ID != cat.status.group_ID else None
        )

        return

    # will this cat actually murder? this takes into account stability and lawfulness
    murder_capable = 8
    if cat.personality.stability < 6:
        murder_capable -= 3
    if cat.personality.lawfulness < 6:
        murder_capable -= 2
    if cat.personality.aggression > 12:
        murder_capable -= 3
    elif cat.personality.aggression > 10:
        murder_capable -= 1

    murder_capable = max(1, murder_capable)

    if random.getrandbits(murder_capable) != 1:
        return

    # If random murder is not triggered, targets can only be those they have some mid/extreme neg for
    targets = [
        i
        for i in relationships
        if (i.has_mid_negative or i.has_extreme_negative)
        and Cat.fetch_cat(i.cat_to).status.group.is_any_clan_group()
    ]
    # sort by total relationship, this way we know who has the worst relationship
    targets.sort(key=lambda x: x.total_relationship_value)
    if len(targets) > 5:
        targets = targets[:5]

    # if we have some, then we need to decide if this cat will kill
    if targets:
        # chosen target is the cat with the worst relationship (or leader, if a config is set as such)
        if (
            get_config("death_related.murder.deputy_prefer_leader")
            and cat.status.rank == CatRank.DEPUTY
        ):
            possible_targets = [c for c in targets if c.cat_to.status.is_leader and c.cat_to.status.group_ID == cat.status.group_ID]
            if possible_targets:
                targets = possible_targets

        chosen_target = random.choice(targets)
        chosen_cat = Cat.fetch_cat(chosen_target.cat_to)

        kill_chance = get_config("death_related.murder.base_murder_kill_chance")

        if chosen_cat.status.group_ID != cat.status.group_ID:
            kill_chance = get_config("death_related.murder.base_crossclan_murder_kill_chance")

        extreme_neg = len(
            [l for l in chosen_target.get_reltype_tiers() if l.is_extreme_neg]
        )
        mid_neg = len([t for t in chosen_target.get_reltype_tiers() if t.is_mid_neg])

        relation_modifier = (extreme_neg * 8) + (mid_neg * 6)

        kill_chance -= relation_modifier

        if (
            len(chosen_target.log) > 0
            and "(high negative effect)" in chosen_target.log[-1]
        ):
            kill_chance -= 10

        if (
            len(chosen_target.log) > 0
            and "(medium negative effect)" in chosen_target.log[-1]
        ):
            kill_chance -= 5

        # little easter egg just for fun
        if cat.personality.trait in ("ambitious", "arrogant", "rebellious") and (
            chosen_cat.status.is_leader
            or chosen_cat.status.rank == CatRank.DEPUTY
        ):
            kill_chance -= 10
            if cat.status.rank == CatRank.DEPUTY:
                kill_chance -= 15

        if cat.status.rank == CatRank.DEPUTY and chosen_cat.status.is_leader:
            kill_chance -= get_config("death_related.murder.deputy_murder_modifier")

        kill_chance -= cat.personality.aggression
        kill_chance -= 16 - cat.personality.stability
        kill_chance -= 16 - cat.personality.lawfulness
        kill_chance = max(1, int(kill_chance))

        if not int(random.random() * kill_chance):
            # print(
            #     cat.name, "TARGET CHOSEN", Cat.fetch_cat(chosen_target.cat_to).name
            # )
            # print("KILL KILL KILL")

            create_short_event(
                event_type="birth_death",
                main_cat=chosen_cat,
                random_cat=cat,
                sub_type=["murder"],
                clan=clan,
                second_clan=chosen_cat.status.fetch_clan_object(game.clan) if chosen_cat.status.group_ID != cat.status.group_ID else None
            )

        elif kill_chance <= 15:
            create_short_event(
                event_type="misc",
                main_cat=cat,
                random_cat=chosen_cat,
                sub_type=["failed_murder"],
                clan=clan,
                second_clan=chosen_cat.status.fetch_clan_object(game.clan) if chosen_cat.status.group_ID != cat.status.group_ID else None
            )


def handle_illnesses_or_illness_deaths(cat, clan):
    """
    This function will handle:
        - expanded mode: getting a new illness (extra function in own class)
    Returns:
        - boolean if a death event occurred or not
    """
    # ---------------------------------------------------------------------------- #
    #                           decide if cat dies                                 #
    # ---------------------------------------------------------------------------- #
    # if triggered_death is True then the cat will die
    triggered_death = Condition_Events.handle_illnesses(cat, game.clan.current_season, clan=clan)
    if not triggered_death:
        handle_outbreaks(cat, clan)

    return triggered_death

def handle_outbreaks(cat, clan):
    """Try to infect some cats."""
    # check if the cat is ill,
    # or if Clan has sufficient med cats
    if not cat.is_ill():
        return

    # check how many kitties are already ill
    already_sick = list(
        filter(
            lambda kitty: (kitty.status.group_ID == clan.group_ID and kitty.is_ill()),
            Cat.all_cats.values(),
        )
    )
    already_sick_count = len(already_sick)

    # round up the living kitties
    healthy_cats = list(
        filter(
            lambda kitty: (
                kitty.status.group_ID == clan.group_ID and not kitty.is_ill()
            ),
            Cat.all_cats.values(),
        )
    )
    healthy_count = len(healthy_cats)

    # if large amount of the population is already sick, stop spreading
    if already_sick_count >= healthy_count * get_config(
        "condition_related.illness_percentage_max"
    ):
        return

    meds = find_alive_cats_with_rank(
        Cat,
        [CatRank.MEDICINE_CAT, CatRank.MEDICINE_APPRENTICE],
        working=True,
        sort=True,
        clan=clan.group_ID
    )

    for illness in cat.illnesses:
        # check if illness can infect other cats
        if cat.illnesses[illness]["infectiousness"] == 0:
            continue
        chance = cat.illnesses[illness]["infectiousness"]
        chance += len(meds) * get_config("condition_related.med_infection_reduction")
        if not int(random.random() * chance):  # 1/chance to infect
            # fleas are the only condition allowed to spread outside of cold seasons
            if (
                game.clan.current_season
                not in get_config("condition_related.illness_outbreak_season")
                and illness != "fleas"
            ):
                continue

            if get_clan_setting("rest_and_recover") and clan == game.clan:
                stopping_chance = get_config("focus.rest_and_recover.outbreak_prevention")
                if not int(random.random() * stopping_chance):
                    continue

            if illness == "kittencough":
                # adjust alive cats list to only include kittens
                healthy_cats = list(
                    filter(
                        lambda kitty: (
                            kitty.status.rank.is_baby()
                            and kitty.status.group_ID == clan.group_ID
                            and not kitty.is_ill()
                        ),
                        Cat.all_cats.values(),
                    )
                )
                healthy_count = len(healthy_cats)

            max_infected = int(healthy_count / 2)  # 1/2 of alive cats
            # If there are less than two cat to infect,
            # you are allowed to infect all the cats
            if max_infected < 2:
                max_infected = healthy_count
            # If, event with all the cats, there is less
            # than two cats to infect, cancel outbreak.
            if max_infected < 2:
                return

            weights = []
            population = []
            for n in range(2, max_infected + 1):
                population.append(n)
                weight = 1 / (0.75 * n)  # Lower chance for more infected cats
                weights.append(weight)
            infected_count = random.choices(population, weights=weights)[
                0
            ]  # the infected..

            infected_names = []
            involved_cats = []
            infected_cats = random.sample(healthy_cats, infected_count)
            for sick_meowmeow in infected_cats:
                infected_names.append(str(sick_meowmeow.name))
                involved_cats.append(sick_meowmeow.ID)
                get_ill(
                    sick_meowmeow, illness, event_triggered=True
                )  # SPREAD THE GERMS >:)

            # TODO: hardcoded text events, not good, need to consider how to convert
            #  should this be handled in condition_events.py?
            if illness == "kittencough":
                event = i18n.t(
                    "hardcoded.kittencough_spread",
                    kits=adjust_list_text(infected_names),
                    count=len(infected_names),
                )
            elif illness == "fleas":
                event = i18n.t(
                    "hardcoded.flea_spread",
                    cats=adjust_list_text(infected_names),
                    count=len(infected_names)-1,
                )
            else:
                event = i18n.t(
                    "hardcoded.illness_spread",
                    illness=str(illness).capitalize(),
                    cats=adjust_list_text(infected_names),
                    count=len(infected_names),
                )

            game.cur_events_list.append(
                EventInformation(event, ["health"], involved_cats, clan=clan.group_ID)
            )
            # game.health_events_list.append(event)
            break


def check_leader(clan):
    """Checks if leader is missing."""
    # check for leader
    if clan.leader:
        leader_invalid = clan.leader.status.group_ID != clan.group_ID
    else:
        leader_invalid = True

    if leader_invalid:
        game.cur_events_list.insert(
            0,
            EventInformation(
                event_text_adjust(
                    Cat, i18n.t("defaults.warn_no_leader"), clan=clan
                ),
                clan=clan.group_ID
            ),
        )


def check_missing_mentors():
    """
    Checks to see if any apprentices have missing mentors, reminds players of this.
    """

    # Only do the check if mentors aren't being assigned randomly.
    if get_clan_setting("assign_mentors"):
        return

    mentorless = []
    for app in find_alive_cats_with_rank(
        Cat,
        [CatRank.MEDICINE_APPRENTICE, CatRank.APPRENTICE, CatRank.MEDIATOR_APPRENTICE],
        clan=game.clan.group_ID
    ):
        if not app.mentor:
            mentorless.append(app.ID)

    if mentorless:
        game.cur_events_list.insert(
            0,
            EventInformation(
                event_text_adjust(
                    Cat, i18n.t("defaults.warn_missing_mentor", count=len(mentorless))
                ),
                cats_involved=mentorless,
                clan=game.clan.group_ID
            ),
        )


load_war_resources()
