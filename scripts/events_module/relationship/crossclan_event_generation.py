from random import random, choice, randint
from typing import Optional

import i18n
import ujson

from scripts.cat.cats import Cat
from scripts.cat.enums import CatRank
from scripts.cat.skills import SkillPath
from scripts.events_module.event_filters import (
    event_for_location,
    event_for_tags,
    event_for_cat,
    event_for_clan_relations,
    event_for_season,
    cat_for_event,
    get_frequency,
    find_new_frequency,
)
from scripts.events_module.relationship.crossclan_event import CrossClanEvent
from scripts.game_structure import constants, game
from scripts.game_structure.game.switches import switch_get_value, Switch
from scripts.clan_package.cotc import get_warring_clan
from scripts.clan_package.get_clan_cats import (
    get_living_clan_cat_count,
    find_alive_cats_with_rank,
)

loaded_events = {}
used_events = set()
used_cats = set()
viable_cats = {}

def get_resource_directory(fallback=False):
    return f"resources/lang/{i18n.config.get('locale') if not fallback else i18n.config.get('fallback')}/events/relationship_events/cross-clan_interactions/"

def handle_crossclan_relationships():
    """
    Triggers relationship events for cats of different Clans in MultiClan
    """
    global used_cats, used_events, viable_cats

    used_cats.clear()
    used_events.clear()
    viable_cats = {}

    for c in [game.clan] + game.clan.all_other_clans:
        living = [cat for cat in Cat.all_cats.values() if cat.status.group_ID == c.group_ID and not cat.not_working() and cat.status.rank not in (CatRank.NEWBORN, CatRank.KITTEN)]
        if living:
            viable_cats[c.group_ID] = living

    event_count = min(constants.CONFIG["relationship"]["max_crossclan_interaction"], int(sum([len(c) for c in viable_cats.values()])/len(viable_cats.keys())/3))

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
    while not chosen_event:
        events = find_needed_events(
            is_group,
            frequency,
        )

        chosen_event, random_cats = filter_events(
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
        
        # setting event info
        chosen_event.main_cat = main_cat
        chosen_event.random_cat = random_cats

        # execute the event
        chosen_event.execute_event()


def find_needed_events(is_group, frequency) -> list:
    """
    Handles detecting the biome and collecting all events possible for biome and type
    :param frequency: The event frequency to look for
    :param event_type: The type of event to pull
    """
    event_list = []

    # skip the rest of the loading if there is an unrecognised biome
    temp_biome = (
        game.clan.biome if not game.clan.override_biome else game.clan.override_biome
    )
    if temp_biome not in constants.BIOME_TYPES:
        print(
            f"WARNING: unrecognised biome {game.clan.biome} in generate_events. Have you added it to BIOME_TYPES "
            f"in clan.py?"
        )

    biome = temp_biome.lower()

    # biome specific events
    event_list.extend(generate_event_objects(is_group, biome, frequency))

    # any biome events
    event_list.extend(generate_event_objects(is_group, "general", frequency))

    return event_list


def get_event_dicts(file_path) -> list:
    """
    Opens and loads .json for the given file path.
    :param file_path: The file path to open
    """
    try:
        with open(
            get_resource_directory() + file_path, "r", encoding="utf-8"
        ) as read_file:
            events = ujson.loads(read_file.read())
    except ValueError:
        try:
            with open(
                get_resource_directory(fallback=True) + file_path,
                "r",
                encoding="utf-8",
            ) as read_file:
                events = ujson.loads(read_file.read())
        except ValueError:
            print(f"ERROR: Unable to load {file_path}.")
            return []

    return events


def generate_event_objects(is_group, biome, frequency) -> list:
    """
    Gets the event dicts for the given args and creates the short event objects for each entry in the dict.
    :param event_triggered: The type of event triggered
    :param biome: The biome to pull events for
    :param frequency: The frequency to pull events for
    """
    file_path = f"{"group_interactions" if is_group else "normal_interactions"}/{biome}.json"
    load_name = f"{file_path}_{frequency}"

    try:
        if file_path in loaded_events:
            return loaded_events[file_path]
        if load_name in loaded_events:
            return loaded_events[load_name]
        else:
            events_dict = get_event_dicts(file_path)

            event_list = []
            if not events_dict:
                return event_list
            for event in events_dict:
                event_text = event["event_text"] if "event_text" in event else None
                event_frequency = event["frequency"] if "frequency" in event else 4

                if not event_text:
                    event_text = event["death_text"] if "death_text" in event else None

                if not event_text:
                    print(
                        f"WARNING: some events resources which are used in generate_events have no 'event_text'."
                    )
                if frequency != event_frequency:
                    continue

                event = CrossClanEvent(
                    event_id=event["event_id"] if "event_id" in event else "",
                    location=event["location"] if "location" in event else ["any"],
                    season=event["season"] if "season" in event else ["any"],
                    tags=event["tags"] if "tags" in event else [],
                    text=event_text,
                    new_accessory=(
                        event["new_accessory"] if "new_accessory" in event else []
                    ),
                    m_c=event["m_c"] if "m_c" in event else {},
                    r_c=event["r_c"] if "r_c" in event else [],
                    injury=event["injury"] if "injury" in event else [],
                    exclude_involved=(
                        event["exclude_involved"] if "exclude_involved" in event else []
                    ),
                    history=event["history"] if "history" in event else [],
                    relationships=(
                        event["relationships"] if "relationships" in event else []
                    ),
                    other_clan=event["other_clan"] if "other_clan" in event else {},
                    supplies=event["supplies"] if "supplies" in event else [],
                    new_gender=event["new_gender"] if "new_gender" in event else [],
                    future_event=event["future_event"]
                    if "future_event" in event
                    else {},
                    nr_involved_clans=event.get("nr_involved_clans", 2)
                )
                event_list.append(event)

            # Add to loaded events.
            loaded_events[load_name] = event_list
            return event_list

    except ValueError:
        print(f"WARNING: {file_path} was not found, check crossclan event generation")
        return []


def filter_events(
    possible_events,
    main_cat,
    random_cat=None,
) -> (Optional[CrossClanEvent], Optional[Cat]):
    """
    Filters possible events to find an event that fits the given requirements
    :param possible_events: list of possible events
    :param main_cat: main cat for this event
    :param random_cat: random cat for this event
    """
    final_events = []
    incorrect_format = []
    clan = main_cat.status.fetch_clan_object()

    for event in possible_events:
        if event.history:
            if not isinstance(event.history, list) or "cats" not in event.history[0]:
                if (
                    f"{event.event_id} history formatted incorrectly"
                    not in incorrect_format
                ):
                    incorrect_format.append(
                        f"{event.event_id} history formatted incorrectly"
                    )
        if event.injury:
            if not isinstance(event.injury, list) or "cats" not in event.injury[0]:
                if (
                    f"{event.event_id} injury formatted incorrectly"
                    not in incorrect_format
                ):
                    incorrect_format.append(
                        f"{event.event_id} injury formatted incorrectly"
                    )

        # check if event has already been used
        if event.event_id in used_events:
            continue

        # ensure ID and requirements override
        if constants.CONFIG["event_generation"]["debug_override_requirements"]:
            final_events.append(event)
            continue

        if not event_for_location(event.location, clan):
            continue

        if not event_for_season(event.season):
            continue

        # check tags
        if not event_for_tags(event.tags, main_cat, random_cat):
            continue

        # check if already trans
        if "transition" in event.sub_type and main_cat.gender != main_cat.genderalign:
            continue

        m_c_injuries = []
        r_c_injuries = []
        discard = False
        for block in event.injury:
            for injury in block["injuries"]:
                if "m_c" in block["cats"]:
                    m_c_injuries.append(injury)
                if "r_c" in block["cats"]:
                    r_c_injuries.append(injury)
            if discard:
                continue

        # check if m_c is allowed this event
        if event.m_c:
            if not event_for_cat(
                cat_info=event.m_c,
                cat=main_cat,
                cat_group=[main_cat, random_cat] if random_cat else None,
                event_id=event.event_id,
            ):
                continue

        # if a random cat was pre-chosen, then we check if the event will be suitable for them
        if random_cat:
            if not event_for_cat(
                cat_info=event.r_c,
                cat=random_cat,
                cat_group=[random_cat, main_cat],
                event_id=event.event_id,
            ):
                continue

        # other Clan related checks
        if event.other_clan:
            if not other_clan:
                continue

            if "current_rep" in event.other_clan and not event_for_clan_relations(
                event.other_clan["current_rep"], clan, other_clan
            ):
                continue

        elif event.supplies:
            clan_size = get_living_clan_cat_count(Cat)
            # finding cats with the CAMP skill
            camp_cats = [
                c
                for c in Cat.all_cats_list
                if c.status.alive_in_player_clan
                and (
                    (c.skills.primary and c.skills.primary.path == SkillPath.CAMP)
                    or (
                        c.skills.secondary and c.skills.secondary.path == SkillPath.CAMP
                    )
                )
            ]

            discard = False
            for supply in event.supplies:
                trigger = supply["trigger"]
                supply_type = supply["type"]

                if (
                    supply["adjust"] in ["reduce_half", "reduce_full"]
                    and randint(1, reduction_avoidance_chance) != 1
                ):
                    discard = True
                    break

                if supply_type == "freshkill":
                    if not FRESHKILL_EVENT_ACTIVE:
                        continue

                    if not event_for_freshkill_supply(
                        game.clan.freshkill_pile,
                        trigger,
                        FRESHKILL_EVENT_TRIGGER_FACTOR,
                        clan_size,
                    ):
                        discard = True
                        break
                    else:
                        discard = False

                else:  # if supply type wasn't freshkill, then it must be an herb type
                    if not event_for_herb_supply(trigger, supply_type, clan_size):
                        discard = True
                        break
                    else:
                        discard = False

            if discard:
                continue

        final_events.append(event)

    if not final_events:
        return None, random_cat

    chosen_cats = []
    involved_clans = []
    chosen_event = None

    failed_ids = []
    while final_events and not chosen_cats and not chosen_event:
        chosen_event = choice(final_events)
        if chosen_event.event_id in failed_ids:
            final_events.remove(chosen_event)
            chosen_event = None
            continue
    
        if chosen_event.nr_involved_clans > len(viable_cats.keys()):
            final_events.remove(chosen_event)
            chosen_event = None
            continue

        if (
            constants.CONFIG["event_generation"]["debug_ensure_event_id"]
            and constants.CONFIG["event_generation"]["debug_ensure_event_id"]
            != chosen_event.event_id
        ):
            final_events.remove(chosen_event)
            failed_ids.append(chosen_event.event_id)
            chosen_event = None
            continue

        # if we're overriding requirements, don't bother looking for an appropriate cat
        # if constants.CONFIG["event_generation"]["debug_override_requirements"]:
        #     chosen_cat = choice(cat_list)
        #     continue

        involved_clans = [main_cat.status.group_ID]
        for i in range(chosen_event.nr_involved_clans-1):
            new_clan = None
            while not new_clan or new_clan in involved_clans:
                new_clan = choice(list(viable_cats.keys()))
            involved_clans.append(new_clan)

        for i in range(len(chosen_event.r_c)):
            # gotta gather injuries so we can check if the cat can get them
            r_c_injuries = []
            for block in chosen_event.injury:
                r_c_injuries.extend(block["injuries"] if "r_c" in block["cats"] or f"r_c{i+1}" in block["cats"] else [])

            allowable_cats = []
            if chosen_event.r_c[i]["clan"] == "any":
                for key in viable_cats:
                    allowable_cats += viable_cats[key]
                    if key not in involved_clans:
                        involved_clans.append(key)
            else:
                allowable_cats = viable_cats[involved_clans[chosen_event.r_c[i]["clan"]-1]] if chosen_event.r_c[i]["clan"] else viable_cats[involved_clans[-1]]
                allowable_cats = [c for c in allowable_cats if c not in chosen_cats and c.ID != main_cat.ID]
            chosen_cat = cat_for_event(
                constraint_dict=chosen_event.r_c[i].copy(),
                possible_cats=allowable_cats,
                comparison_cat=main_cat,
                comparison_cat_rel_status=chosen_event.m_c.get(
                    "relationship_status", []
                ).copy(),
                injuries=r_c_injuries,
                return_id=False,
            )

            if not chosen_cat:
                failed_ids.append(chosen_event.event_id)
                final_events.remove(chosen_event)
                chosen_event = None
                chosen_cats = []
                break
            else:
                chosen_cats.append(chosen_cat)

        if chosen_event and len(chosen_cats) == len(chosen_event.r_c):
           break 
        

    for notice in incorrect_format:
        print(notice)

    if not final_events:
        return None, None

    chosen_event.involved_clans = involved_clans

    return chosen_event, chosen_cats
