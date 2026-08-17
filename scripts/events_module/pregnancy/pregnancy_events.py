from random import random, choice

from scripts.config import get_config
from scripts.cat.cats import Cat
from scripts.clan_package.settings import get_clan_setting
from scripts.event_class import Single_Event
from scripts.events_module.pregnancy.check_parents import (
    check_if_can_have_kits,
    get_second_parent,
    check_second_parent,
    handle_surrogate,
)
from scripts.events_module.pregnancy.create_kits import (
    handle_adoption,
    get_balanced_kit_chance,
)
from scripts.events_module.pregnancy.handle_already_pregnant import (
    handle_one_moon_pregnant,
    handle_two_moon_pregnant,
)
from scripts.events_module.pregnancy.handle_become_pregnant import (
    handle_zero_moon_pregnant,
    _create_pregnancy_announcement
)
from scripts.game_structure import game


def increment_pregnancy_age():
    """Increase the moon for each pregnancy in the pregnancy dictionary"""
    for pregnancy_key in game.clan.pregnancy_data.keys():
        game.clan.pregnancy_data[pregnancy_key]["moons"] += 1


def handle_having_kits(cat: Cat, clan):
    """
    Handles existing pregnancies and creates new pregnancies. If cats cannot get pregnant, this might have them adopt or
     bring back 'secret' kittens.
    """
    if not game.clan:
        return

    # Handles if a cat is already pregnant
    if cat.ID in game.clan.pregnancy_data:
        moons = game.clan.pregnancy_data[cat.ID]["moons"]
        if moons == 1:
            handle_one_moon_pregnant(cat, clan)
            return
        if moons >= 2:
            handle_two_moon_pregnant(cat, clan)
            return

    if cat.status.is_outsider or get_clan_setting("no_litters") or (game.clan.clancount == "singleclan" and cat.status.is_other_clancat) or cat.not_working():
        return

    # Handle birth cooldown outside the check_if_can_have_kits function, so it only happens once
    # for each cat.
    if cat.birth_cooldown:
        cat.birth_cooldown -= 1

    # Check if they can have kits.
    if not check_if_can_have_kits(cat):
        return

    # DETERMINE THE SECOND PARENT
    # check if there is a cat in the clan for the second parent
    second_parent, is_affair = get_second_parent(cat, clan)

    if not second_parent and not get_clan_setting("single parentage"):
        return

    # check if the second_parent is not none and if they also can have kits
    can_have_kits, kits_are_adopted, second_parent = check_second_parent(cat, second_parent)
    if not can_have_kits:
        return
    elif not second_parent and not get_clan_setting("single parentage"):
        return

    chance = get_balanced_kit_chance(cat, second_parent, is_affair, clan)
    
    all_infertile = True
    if 'sterile' not in cat.permanent_condition:
        all_infertile = False
    elif second_parent:
        for x in second_parent:
            if x != "Surrogate" and 'sterile' not in x.permanent_condition:
                all_infertile = False

    if not int(random() * chance):
        # If you've reached here - congrats, kits!
        if kits_are_adopted or ('sterile' in cat.permanent_condition and (not second_parent or second_parent[0] != "Surrogate")) or (second_parent and all_infertile):
            handle_adoption(cat, second_parent, clan)
        else:
            surrogate = False
            if second_parent and second_parent[0] == "Surrogate":
                x = 1
                while 'sterile' in cat.permanent_condition:
                    cat = second_parent[x]
                    x += 1
                if cat in second_parent:
                    second_parent.remove(cat)
                second_parent[0] = handle_surrogate(cat, second_parent, clan)
                if not second_parent[0]:
                    return
                else:
                    surrogate = True
            handle_zero_moon_pregnant(cat, second_parent, surrogate, clan)

    elif second_parent and second_parent[0] != "Surrogate" and not kits_are_adopted and get_config("pregnancy.false_pregnancy_chance") and not int(random() * (get_config("pregnancy.false_pregnancy_chance")-1)):
        if ('Y' in cat.phenotype.sexgene and not cat.phenotype.sex == "molly") and not get_clan_setting("same sex birth"):
            return

        if cat.status.group_ID != clan.group_ID:
            clan = cat.status.fetch_clan_object(game.clan)
        
        text, involved_cats = _create_pregnancy_announcement(cat, "announcement", clan, choice(second_parent), force_minor=True)
        
        cat.injuries["pregnant"]["duration"] = 1
        game.cur_events_list.append(
            Single_Event(
                text, "birth_death", involved_cats, clan=clan.group_ID
            )
        )
