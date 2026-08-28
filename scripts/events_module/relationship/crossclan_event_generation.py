from random import random, choice, shuffle
from typing import Optional

import i18n

from scripts.cat.cats import Cat
from scripts.cat.enums import CatRank
from scripts.events_module.event_filters import (
    check_rel_constraint_groups,
    event_for_cat,
    event_for_clan_relations,
    event_for_poi,
    cat_for_event,
    get_frequency,
    find_new_frequency,
)
from scripts.events_module.text_pool_event.text_pool_event import TextPoolEvent
from scripts.events_module.event_information import EventInformation
from scripts.config import get_config
from scripts.game_structure import game
from scripts.events_module.text_pool_event.event_retrieval import (
    load_text_pool_events,
)
from scripts.events_module.text_pool_event.check_general_constraints import (
    passes_general_constraints,
)
from scripts.events_module.text_pool_event.handle_consequences import execute_outcome

loaded_events = {}
used_events = set()
viable_cats = {}

def get_resource_directory(fallback=False):
    return f"resources/lang/{i18n.config.get('locale') if not fallback else i18n.config.get('fallback')}/events/relationship_events/cross-clan_interactions/"

def handle_crossclan_relationships():
    """
    Triggers relationship events for cats of different Clans in MultiClan
    """
    global used_cats, used_events, viable_cats

    used_events.clear()
    viable_cats = {}

    for c in [game.clan] + game.clan.all_other_clans:
        living = [cat for cat in Cat.all_cats.values() if cat.status.group_ID == c.group_ID and not cat.not_working() and cat.status.rank not in (CatRank.NEWBORN, CatRank.KITTEN)]
        if living:
            viable_cats[c.group_ID] = living
    if not viable_cats:
        return

    event_count = min(get_config("relationship.max_crossclan_interaction"), int(
        sum([len(c) for c in viable_cats.values()])/len(viable_cats.keys())/2))

    for i in range(event_count):
        main_cat = choice(viable_cats[choice(list(viable_cats.keys()))])

        create_rel_event(main_cat, random() < 0.2)


def create_rel_event(
    main_cat: Cat,
    is_group = False
):
    """
    Handles everything involved in finding and executing an appropriate short event for the given args.
    :param main_cat: The cat object that will take the role of m_c.
    """
    # choosing frequency
    frequency = get_frequency()
    used_frequencies = set()

    chosen_event = None
    already_reset = False
    clan = main_cat.status.fetch_clan_object(game.clan)
    while not chosen_event:
        events = find_needed_events(
            is_group,
            clan.biome,
            frequency
        )

        chosen_event, random_cats, involved_cats, other_clans = filter_events(
            possible_events=events,
            main_cat=main_cat,
        )
        if not chosen_event:
            # we'll see if any more common events are available
            used_frequencies.add(frequency)
            frequency = find_new_frequency(used_frequencies)

            # if we've ended up with 4 frequency twice then we're out of events and it's time to reset
            if 4 in used_frequencies and frequency == 4:
                used_events.clear()
                used_frequencies.clear()
                frequency = 4
                # already_reset marks if we've already reset the used_events list while trying to find an event
                if already_reset:
                    break
                already_reset = True

    if chosen_event:
        used_events.add(chosen_event.event_id)

        viable_cats[main_cat.status.group_ID].remove(main_cat)
        for c in random_cats:
            viable_cats[c.status.group_ID].remove(c)
        
        for key in list(viable_cats.keys()).copy():
            if not viable_cats[key]:
                del viable_cats[key]

        # execute the event
        text, results, rel_results = execute_outcome(chosen_event, involved_cats, clan, other_clans)
        types = ["other_clans", "interaction"]
        if chosen_event.condition:
            types = ["other_clans", "health"]
        for clan in [clan]+other_clans:
            game.cur_events_list.append(
                EventInformation(
                    text,
                    types,
                    cat_dict=involved_cats,
                    clan=clan.group_ID
                )
            )


def find_needed_events(is_group, biome, frequency) -> list:
    """
    Handles detecting the biome and collecting all events possible for biome and type
    :param frequency: The event frequency to look for
    :param event_type: The type of event to pull
    """
    event_list = []

    event_list += load_text_pool_events(f"events/relationship_events/cross-clan_interactions/{"group" if is_group else "normal"}_interactions/{biome}.json")
    event_list += load_text_pool_events(f"events/relationship_events/cross-clan_interactions/{"group" if is_group else "normal"}_interactions/general.json")

    event_list = [e for e in event_list if e.frequency == frequency]

    return event_list


def filter_events(
    possible_events,
    main_cat,
) -> (Optional[TextPoolEvent], Optional[Cat]):
    """
    Filters possible events to find an event that fits the given requirements
    :param possible_events: list of possible events
    :param main_cat: main cat for this event
    :param random_cat: random cat for this event
    """
    final_events = []
    clan = main_cat.status.fetch_clan_object()
    involved_cats = {
        "m_c": main_cat
    }

    for event in possible_events:
        # check if event has already been used
        if event.event_id in used_events:
            continue

        # ensure ID and requirements override
        if get_config("event_generation.debug_override_requirements"):
            final_events.append(event)
            continue

        if not passes_general_constraints(
            event,
            involved_cats["m_c"],
            involved_cats,
            clan,
            is_debug_event=event.event_id == get_config("event_generation.debug_ensure_event_id")
        ):
            continue

        if not event_for_poi(event.poi, clan):
            continue

        # check if m_c is allowed this event
        if not event_for_cat(
            cat_info=event.involved_cats["m_c"],
            cat=main_cat,
            event_id=event.event_id,
        ):
            continue

        final_events.extend([event] * event.weight)

    if not final_events:
        return None, None, None, None

    chosen_cats = []
    involved_clans = []
    chosen_event = None

    failed_ids = []
    while final_events and not chosen_event:
        chosen_event = choice(final_events)
        if chosen_event.event_id in failed_ids:
            final_events.remove(chosen_event)
            chosen_event = None
            continue
    
        if chosen_event.nr_involved_clans > len(viable_cats.keys()):
            final_events.remove(chosen_event)
            failed_ids.append(chosen_event.event_id)
            chosen_event = None
            continue

        if (
            get_config("event_generation.debug_ensure_event_id")
            and get_config("event_generation.debug_ensure_event_id")
            != chosen_event.event_id
        ):
            final_events.remove(chosen_event)
            failed_ids.append(chosen_event.event_id)
            chosen_event = None
            continue

        possible_clans = list(viable_cats.keys())

        involved_clans = [main_cat.status.fetch_clan_object()]
        possible_clans.remove(main_cat.status.group_ID)

        clan = game.clan.group_ID_to_clan(main_cat.status.group_ID)

        if chosen_event.required_reputation:
            for other_clan in possible_clans.copy():
                if "other_clan" in chosen_event.required_reputation and not event_for_clan_relations(
                    chosen_event.required_reputation["other_clan"], clan, game.clan.group_ID_to_clan(
                        other_clan)
                ):
                    possible_clans.remove(other_clan)
        
        if "war" in chosen_event.tags:
            enemies = game.clan.get_wars(clan)
            for other_clan in possible_clans.copy():
                if other_clan not in enemies:
                    possible_clans.remove(other_clan)

        if len(possible_clans) < chosen_event.nr_involved_clans-1:
            final_events.remove(chosen_event)
            failed_ids.append(chosen_event.event_id)
            chosen_event = None
            continue

        for i in range(chosen_event.nr_involved_clans-1):
            new_clan = None
            while not new_clan or new_clan in involved_clans:
                new_clan = choice(possible_clans)
            involved_clans.append(game.clan.group_ID_to_clan(new_clan))

        for abbr, cat in chosen_event.involved_cats.items():
            if abbr == "m_c":
                continue
            # gotta gather injuries so we can check if the cat can get them
            possible_injuries = []
            for block in chosen_event.condition:
                possible_injuries.extend(block["condition"] if abbr in block["cats"] else [])

            allowable_cats = []
            if cat.get("clan") == "any":
                for key in viable_cats:
                    allowable_cats += viable_cats[key]
            else:
                allowable_cats = viable_cats[involved_clans[cat["clan"]-1].group_ID] if cat.get("clan") else viable_cats[involved_clans[-1].group_ID]
                allowable_cats = [c for c in allowable_cats if c not in chosen_cats and c.ID != main_cat.ID]

            for c in chosen_cats + [main_cat]:
                if c in allowable_cats:
                    allowable_cats.remove(c)

            chosen_cat = None
            allowable_cats = cat_for_event(
                constraint_dict=cat,
                possible_cats=allowable_cats,
                comparison_cat=main_cat,
                tags=chosen_event.tags,
                injuries=possible_injuries,
                return_list=True,
                return_id=False,
            )
            if allowable_cats:
                shuffle(allowable_cats)
                if chosen_event.relationship_constraint:
                    while not involved_cats.get(abbr):
                        # need a temp cat dict that includes our possible kitty
                        _temp_cats = involved_cats.copy()
                        _temp_cats[abbr] = allowable_cats[0]
                        # now we check each rel constraint to make sure our new cat is valid
                        if not all(
                            check_rel_constraint_groups(block, _temp_cats)
                            for block in chosen_event.relationship_constraint
                        ):
                            # they aren't! so we remove them from the possibilities
                            allowable_cats.remove(_temp_cats[abbr])
                            if not allowable_cats:
                                break
                            else:
                                # still some possibilities, let's try the next!
                                continue
                        # if we got here, then this cat works!
                        involved_cats[abbr] = _temp_cats[abbr]
                        chosen_cat = _temp_cats[abbr]
                else:
                    involved_cats[abbr] = allowable_cats[0]
                    chosen_cat = allowable_cats[0]

            if not chosen_cat:
                failed_ids.append(chosen_event.event_id)
                final_events.remove(chosen_event)
                chosen_event = None
                chosen_cats = []
                break
            else:
                chosen_cats.append(chosen_cat)
                if chosen_cat.status.fetch_clan_object() not in involved_clans:
                    involved_clans.append(chosen_cat.status.fetch_clan_object())

        if chosen_event and chosen_cats and involved_cats.keys() == chosen_event.involved_cats.keys():
           break

    if not final_events:
        return None, None, None, None

    return chosen_event, chosen_cats, involved_cats, involved_clans[1:]
