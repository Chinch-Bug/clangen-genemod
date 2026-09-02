import random

from scripts.cat import pronouns
from scripts.cat.cats import Cat
from scripts.cat.enums import CatAge
from scripts.config import get_config
from scripts.events_module.event_information import EventInformation
from scripts.events_module.text_pool_event.event_retrieval import (
    load_text_pool_events,
    get_valid_event,
)
from scripts.events_module.text_pool_event.handle_consequences import execute_outcome
from scripts.events_module.text_pool_event.text_pool_event import TextPoolEvent
from scripts.game_structure import game


def attempt_coming_out(main_cat: Cat, clan):
    """Check if main_cat wants to transition (turnin' the kitties trans...)"""

    if main_cat.moons < 3 or main_cat.gender != main_cat.genderalign:
        return

    transing_chance = get_config("transition_related")
    chance = transing_chance["base_trans_chance"]
    if main_cat.age in (CatAge.ADOLESCENT, CatAge.KITTEN):
        chance += transing_chance["adolescent_modifier"]
    elif main_cat.age in (CatAge.ADULT, CatAge.SENIOR_ADULT, CatAge.SENIOR):
        chance += transing_chance["older_modifier"]

    if not int(random.random() * chance):
        _generate_transition_event(main_cat=main_cat, clan=clan)

    return


def _generate_transition_event(main_cat: Cat, clan):
    """
    Actually generate and execute transition event
    """
    possible_events = load_text_pool_events("events/transition.json")
    involved_cats = {"m_c": main_cat}

    other_clan = (
        random.choice([c for c in game.clan.all_other_clans+[game.clan] if c.group_ID != main_cat.status.group_ID]) if game.clan.all_other_clans else None
    )

    chosen_event, involved_cats = get_valid_event(
        primary_cat=main_cat,
        involved_cats=involved_cats,
        interactable_cats=Cat.all_cats_list,
        possible_events=possible_events,
        other_clan=other_clan,
        clan=clan,
        frequency_active=False,
    )

    processed_text = _handle_event(chosen_event, involved_cats, main_cat, clan, other_clan)

    game.cur_events_list.append(
        EventInformation(
            processed_text,
            ["misc"],
            [c.ID for c in involved_cats.values()],
            clan=clan.group_ID
        )
    )


def _handle_event(
    chosen_event: TextPoolEvent,
    involved_cats: dict,
    main_cat: Cat,
    clan,
    other_clan,
):
    """
    Changes the cat's genderalign and handles any other changes made by the event. Needs to be its own function for testing purposes.
    """
    # DO the transing before we execute_outcome, this ensures that we don't misgender

    new_gender = random.choice(chosen_event.new_gender)

    main_cat.genderalign = "intersex " if (main_cat.gender == 'intersex' or 
    (main_cat.gender == "molly" and 'Y' in main_cat.phenotype.sexgene) or 
    (main_cat.gender == "tom" and 'Y' not in main_cat.phenotype.sexgene) or
    (len(main_cat.phenotype.sexgene) != 2)) else "" 
    main_cat.genderalign += new_gender.replace("female", "molly").replace("male", "tom").replace("nonbinary", "sam")

    main_cat.pronouns = pronouns.get_new_pronouns(main_cat.genderalign)
    # we won't use results and rel_results here
    processed_text, results, rel_results = execute_outcome(
        event=chosen_event,
        event_involved_cats=involved_cats,
        clan=clan,
        other_clan=other_clan,
    )
    return processed_text
