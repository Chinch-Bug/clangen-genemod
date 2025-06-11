# pylint: disable=line-too-long
"""

TODO: Docs


"""  # pylint: enable=line-too-long

import logging
import os
import re
from itertools import combinations
from math import floor
from random import choice, choices, randint, random, sample, randrange, getrandbits
from sys import exit as sys_exit
from copy import deepcopy
from typing import List, Tuple, TYPE_CHECKING, Type, Union

import i18n
import pygame

from scripts.cat.phenotype import Phenotype
from scripts.cat.phenotype import Genotype

import ujson
from pygame_gui.core import ObjectID

from scripts.game_structure.localization import (
    load_lang_resource,
    determine_plural_pronouns,
    get_lang_config,
)

logger = logging.getLogger(__name__)
from scripts.special_dates import SpecialDate, is_today
from scripts.game_structure import image_cache, localization
from scripts.cat.enums import CatAgeEnum
from scripts.cat.history import History
from scripts.cat.names import names
from scripts.cat.sprites import sprites
from scripts.game_structure.game_essentials import game
import scripts.game_structure.screen_settings  # must be done like this to get updates when we change screen size etc

if TYPE_CHECKING:
    from scripts.cat.cats import Cat


# ---------------------------------------------------------------------------- #
#                               Getting Cats                                   #
# ---------------------------------------------------------------------------- #


def get_alive_clan_queens(living_cats, clan=game.clan):
    living_kits = [
        cat
        for cat in living_cats
        if not (cat.dead or cat.outside) and cat.status in ("kitten", "newborn")
        and cat.group == clan
    ]

    queen_dict = {}
    for cat in living_kits.copy():
        parents = cat.get_parents()
        # Fetch parent object, only alive and not outside.
        parents = [
            cat.fetch_cat(i)
            for i in parents
            if cat.fetch_cat(i)
            and not (cat.fetch_cat(i).dead or cat.fetch_cat(i).outside)
            and cat.fetch_cat(i).group == clan
        ]
        if not parents:
            continue

        if (
            len(parents) == 1
            or len(parents) > 2
            or all('Y' in i.phenotype.sexgene for i in parents)
            or 'Y' not in parents[0].phenotype.sexgene
        ):
            if parents[0].ID in queen_dict:
                queen_dict[parents[0].ID].append(cat)
                living_kits.remove(cat)
            else:
                queen_dict[parents[0].ID] = [cat]
                living_kits.remove(cat)
        elif len(parents) == 2:
            if parents[1].ID in queen_dict:
                queen_dict[parents[1].ID].append(cat)
                living_kits.remove(cat)
            else:
                queen_dict[parents[1].ID] = [cat]
                living_kits.remove(cat)
    return queen_dict, living_kits


def get_alive_status_cats(
        Cat: Union["Cat", Type["Cat"]],
        get_status: list,
        working: bool = False,
        sort: bool = False,
        clan = None
) -> list:
    """
    returns a list of cat objects for all living cats of get_status in Clan
    :param Cat Cat: Cat class
    :param list get_status: list of statuses searching for
    :param bool working: default False, set to True if you would like the list to only include working cats
    :param bool sort: default False, set to True if you would like list sorted by descending moon age
    """

    alive_cats = [
        i
        for i in Cat.all_cats.values()
        if i.status in get_status and not i.dead and not i.outside
    ]

    if clan:
        for c in alive_cats:
            if not c.group:
                pass
        alive_cats = [i for i in alive_cats if i.group and i.group.name == clan]

    if working:
        alive_cats = [i for i in alive_cats if not i.not_working()]

    if sort:
        alive_cats = sorted(alive_cats, key=lambda cat: cat.moons, reverse=True)

    return alive_cats


def get_living_cat_count(Cat):
    """
    Returns the int of all living cats, both in and out of the Clan
    :param Cat: Cat class
    """
    count = 0
    for the_cat in Cat.all_cats.values():
        if the_cat.dead:
            continue
        count += 1
    return count


def get_living_clan_cat_count(Cat, clan=None):
    """
    Returns the int of all living cats within the Clan
    :param Cat: Cat class
    """
    count = 0
    for the_cat in Cat.all_cats.values():
        if the_cat.dead or the_cat.exiled or the_cat.outside or (clan and the_cat.group != clan):
            continue
        count += 1
    return count


def get_cats_same_age(Cat, cat, age_range=10):
    """
    Look for all cats in the Clan and returns a list of cats which are in the same age range as the given cat.
    :param Cat: Cat class
    :param cat: the given cat
    :param int age_range: The allowed age difference between the two cats, default 10
    """
    cats = []
    for inter_cat in Cat.all_cats.values():
        if inter_cat.dead or inter_cat.outside or inter_cat.exiled or inter_cat.group != cat.group:
            continue
        if inter_cat.ID == cat.ID:
            continue

        if inter_cat.ID not in cat.relationships:
            cat.create_one_relationship(inter_cat)
            if cat.ID not in inter_cat.relationships:
                inter_cat.create_one_relationship(cat)
            continue

        if (
                inter_cat.moons <= cat.moons + age_range
                and inter_cat.moons <= cat.moons - age_range
        ):
            cats.append(inter_cat)

    return cats


def get_free_possible_mates(cat):
    """Returns a list of available cats, which are possible mates for the given cat."""
    cats = []
    for inter_cat in cat.all_cats.values():
        if inter_cat.dead or inter_cat.outside or inter_cat.exiled or inter_cat.group != cat.group:
            continue
        if inter_cat.ID == cat.ID:
            continue

        if inter_cat.ID not in cat.relationships:
            cat.create_one_relationship(inter_cat)
            if cat.ID not in inter_cat.relationships:
                inter_cat.create_one_relationship(cat)
            continue

        if inter_cat.is_potential_mate(cat, for_love_interest=True):
            cats.append(inter_cat)
    return cats


def get_random_moon_cat(
        Cat, main_cat, parent_child_modifier=True, mentor_app_modifier=True, clan=None
):
    """
    returns a random cat for use in moon events
    :param Cat: Cat class
    :param main_cat: cat object of main cat in event
    :param parent_child_modifier: increase the chance of the random cat being a
    parent of the main cat. Default True
    :param mentor_app_modifier: increase the chance of the random cat being a mentor or
    app of the main cat. Default True
    """
    random_cat = None

    # grab list of possible random cats
    possible_r_c = [
        cat for cat in Cat.all_cats.values()
        if not cat.dead
        and not cat.exiled
        and not cat.outside
        and (not clan or cat.group == clan)
        and (cat.ID != main_cat.ID)
    ]

    if possible_r_c:
        random_cat = choice(possible_r_c)
        if parent_child_modifier and not int(random() * 3):
            possible_parents = []
            if main_cat.parent1:
                if Cat.fetch_cat(main_cat.parent1) in possible_r_c:
                    possible_parents.append(main_cat.parent1)
            if main_cat.parent2:
                if Cat.fetch_cat(main_cat.parent2) in possible_r_c:
                    possible_parents.append(main_cat.parent2)
            if main_cat.parent3:
                if Cat.fetch_cat(main_cat.parent3) in possible_r_c:
                    possible_parents.append(main_cat.parent3)
            if main_cat.adoptive_parents:
                for parent in main_cat.adoptive_parents:
                    if Cat.fetch_cat(parent) in possible_r_c:
                        possible_parents.append(parent)
            if possible_parents:
                random_cat = Cat.fetch_cat(choice(possible_parents))
        if mentor_app_modifier:
            if (
                main_cat.status
                in ["apprentice", "mediator apprentice", "healer apprentice"]
                and main_cat.mentor
                and not int(random() * 3)
            ):
                random_cat = Cat.fetch_cat(main_cat.mentor)
            elif main_cat.apprentice and not int(random() * 3):
                random_cat = Cat.fetch_cat(choice(main_cat.apprentice))

    if isinstance(random_cat, str):
        print(f"WARNING: random cat was {random_cat} instead of cat object")
        random_cat = Cat.fetch_cat(random_cat)
    return random_cat


def get_warring_clan():
    """
    returns enemy clan if a war is currently ongoing
    """
    enemy_clan = None
    if game.clan.war.get("at_war", False):
        for other_clan in game.clan.all_clans:
            if other_clan.name == game.clan.war["enemy"]:
                enemy_clan = other_clan

    return enemy_clan

def search_cats(search_text, cat_list, search_genotype):
    search_text = search_text.strip()
    all_found = cat_list
    if search_text not in ["", i18n.t("general.name_search"), i18n.t("general.genotype_search")]:
        if search_genotype:
            gene_map = {
                "furLength": ["L", "l"],
                "eumelanin": ["B", "b", "bl"],
                "sexgene": ["O", "o", "Y"],
                "dilute": ["D", "d"],
                "white": ["W", "ws", "w", "wt", "wg", "wsal"],
                "pointgene": ["C", "cb", "cs", "cm", "c"],
                "silver": ["I", "i"],
                "agouti": ["A", "Apb", "a"],
                "mack": ["Mc", "mc"],
                "ticked": ["Ta", "ta"],

                "wirehair": ["Wh", "wh"],
                "laperm": ["Lp", "lp"],
                "cornish": ["R", "r"],
                "urals": ["Ru", "ru"],
                "tenn": ["Tr", "tr"],
                "fleece": ["Fc", "fc"],
                "sedesp": ["Se", "Hr", "Re", "se", "hr", "re"],
                "ruhr": ["Hrbd", "hrbd"],
                "ruhrmod": ["hi", "ha"],
                "lykoi": ["Ly", "ly"],

                "pinkdilute": ["Dp", "dp"],
                "dilutemd": ["Dm", "dm"],
                "ext": ["Eg", "E", "ea", "er", "ec"],
                "corin": ["N", "sh", "sg", "fg"],
                "karp": ["K", "k"],
                "bleach": ["Lb", "lb"],
                "ghosting": ["Gh", "gh"],
                "satin": ["St", "st"],
                "glitter": ["Gl", "gl"],

                "curl": ["Cu", "cu"],
                "fold": ["Fd", "fd"],
                "manx": ["M", "Ab", "m", "ab"],
                "kab": ["Kab", "kab"],
                "toybob": ["Tb", "tb"],
                "jbob": ["Jb", "jb"],
                "kub": ["Kub", "kub"],
                "ring": ["Rt", "rt"],
                "munch": ["Mk", "mk"],
                "poly": ["Pd", "pd"],
                "pax3": ["NoDBE", "DBEre", "DBEalt", "DBEcel"],
            }
            orgroups = search_text.split("/")
            all_found = []
            for g in orgroups:
                alleles = g.split("&")
                found_cats = cat_list.copy()
                for a in alleles:
                    allele = a.strip().strip("!")
                    find_gene = [
                        key for key, value in gene_map.items() if allele in value]
                    gene = find_gene[0] if len(find_gene) else None
                    if gene:
                        found_cats = [
                            cat
                            for cat in found_cats
                            if '!' not in a and (allele in cat.phenotype[gene] or
                                                    (cat.chimerapheno and allele in cat.chimerapheno[gene]))
                            or ('!' in a and allele not in cat.phenotype[gene] and
                                (not cat.chimerapheno or allele not in cat.chimerapheno[gene]))
                        ]
                all_found += found_cats
            all_found = list(set(all_found))
        else:
            all_found = [
                cat
                for cat in cat_list
                if search_text.lower() in str(cat.name).lower()
            ]
    return all_found


# ---------------------------------------------------------------------------- #
#                          Handling Outside Factors                            #
# ---------------------------------------------------------------------------- #


def get_current_season():
    """
    function to handle the math for finding the Clan's current season
    :return: the Clan's current season
    """

    if game.config["lock_season"]:
        game.clan.current_season = game.clan.starting_season
        return game.clan.starting_season

    modifiers = {
        "Newleaf": 0,
        "Greenleaf": 3,
        "Leaf-fall": 6,
        "Leaf-bare": 9
    }
    if(not game.clan):
        return "Newleaf"
    else: 
        index = game.clan.age % 12 + modifiers[game.clan.starting_season]

        if index > 11:
            index = index - 12

        game.clan.current_season = game.clan.seasons[index]

        return game.clan.current_season


def change_clan_reputation(difference):
    """
    will change the Clan's reputation with outsider cats according to the difference parameter.
    """
    game.clan.reputation += difference
    if game.clan.reputation < 0:
        game.clan.reputation = 0 # clamp to 0
    elif game.clan.reputation > 100:
        game.clan.reputation = 100 # clamp to 100

def change_clan_relations(other_clan, difference):
    """
    will change the Clan's relation with other clans according to the difference parameter.
    """
    # grab the clan that has been indicated
    other_clan = other_clan
    # grab the relation value for that clan
    y = game.clan.all_clans.index(other_clan)
    clan_relations = int(game.clan.all_clans[y].relations)
    # change the value
    clan_relations += difference
    # making sure it doesn't exceed the bounds
    if clan_relations > 30:
        clan_relations = 30
    elif clan_relations < 0:
        clan_relations = 0
    # setting it in the Clan save
    game.clan.all_clans[y].relations = clan_relations

def create_bio_parents(Cat, cat_type, flip=False, second_parent=True):
    ages = [randint(15,120), 0]
    ages[1] = ages[0] + randint(0, 24) - 12
    
    blood_parent2 = None
    par2geno = None
    blood_parent = create_new_cat(Cat,
                                    loner=cat_type in ["loner", "rogue"],
                                    kittypet=cat_type == "kittypet",
                                    other_clan=cat_type == 'former Clancat',
                                    status=cat_type,
                                    alive=choice([True, True, True, False]),
                                    age=ages[0],
                                    gender='fem' if flip else 'masc',
                                    outside=True,
                                    is_parent=True)[0]
    while 'infertility' in blood_parent.permanent_condition:
        if(blood_parent):
            del Cat.all_cats[blood_parent.ID]
        blood_parent = create_new_cat(Cat,
                                    loner=cat_type in ["loner", "rogue"],
                                    kittypet=cat_type == "kittypet",
                                    other_clan=cat_type == 'former Clancat',
                                    status=cat_type,
                                    alive=choice([True, True, True, False]),
                                    age=ages[0],
                                    gender='fem' if flip else 'masc',
                                    outside=True,
                                    is_parent=True)[0]
    if second_parent:
        cat_type = choice(["loner", "rogue", "kittypet"])
        blood_parent2 = create_new_cat(Cat,
                                    loner=cat_type in ["loner", "rogue"],
                                    kittypet=cat_type == "kittypet",
                                    other_clan=cat_type == 'former Clancat',
                                    status=cat_type,
                                    alive=choice([True, True, True, False]),
                                    age=ages[1] if ages[1] > 14 else 15,
                                    gender='masc' if flip else 'fem',
                                    outside=True,
                                    is_parent=True)[0]
        while 'infertility' in blood_parent2.permanent_condition:
            if blood_parent2 and Cat.all_cats[blood_parent2.ID]:
                del Cat.all_cats[blood_parent2.ID]
            blood_parent2 = create_new_cat(Cat,
                                    loner=cat_type in ["loner", "rogue"],
                                    kittypet=cat_type == "kittypet",
                                    other_clan=cat_type == 'former Clancat',
                                    status=cat_type,
                                    alive=choice([True, True, True, False]),
                                    age=ages[0],
                                    gender='masc' if flip else 'fem',
                                    outside=True,
                                    is_parent=True)[0]
    else:
        par2geno = Genotype(game.config['genetics_config'], game.settings["ban problem genes"])
        par2geno.Generator('masc' if flip else 'fem')

    return [blood_parent, blood_parent2, par2geno]

def create_new_cat_block(
        Cat, Relationship, event, in_event_cats: dict, i: int, attribute_list: List[str], clan=None
) -> list:
    """
    Creates a single new_cat block and then generates and returns the cats within the block
    :param Cat Cat: always pass Cat class
    :param Relationship Relationship: always pass Relationship class
    :param event: always pass the event class
    :param dict in_event_cats: dict containing involved cats' abbreviations as keys and cat objects as values
    :param int i: index of the cat block
    :param list[str] attribute_list: attribute list contained within the block
    """

    thought = i18n.t("hardcoded.thought_new_cat")
    new_cats = None

    # gather parents
    parent1 = None
    parent2 = None
    adoptive_parents = []
    for tag in attribute_list:
        parent_match = re.match(r"parent:\s?([,0-9]+)", tag)
        sibling_match = re.match(r"sibling:\s?([,0-9]+)", tag)
        adoptive_match = re.match(r"adoptive:\s?(.+)", tag)
        if not parent_match and not adoptive_match and not sibling_match:
            continue

        parent_indexes = parent_match.group(1).split(",") if parent_match else []
        sibling_indexes = sibling_match.group(1).split(",") if sibling_match else []
        adoptive_indexes = adoptive_match.group(1).split(",") if adoptive_match else []
        if not parent_indexes and not adoptive_indexes and not sibling_indexes:
            continue

        parent_indexes = [int(index) for index in parent_indexes]
        sibling_indexes = [int(index) for index in sibling_indexes]
        for index in parent_indexes:
            if index >= i:
                continue

            if parent1 is None:
                parent1 = event.new_cats[index][0]
            else:
                parent2 = event.new_cats[index][0]
        for index in sibling_indexes:
            if index >= i:
                continue

            sibling = event.new_cats[index][0]
            if not parent2:
                parent2 = Cat.fetch_cat(sibling.parent2)

        adoptive_indexes = [
            int(index) if index.isdigit() else index for index in adoptive_indexes
        ]
        for index in adoptive_indexes:
            if in_event_cats[index].ID not in adoptive_parents:
                adoptive_parents.append(in_event_cats[index].ID)
                adoptive_parents.extend(in_event_cats[index].mate)

    # gather mates
    give_mates = []
    for tag in attribute_list:
        match = re.match(r"mate:\s?([_,0-9a-zA-Z]+)", tag)
        if not match:
            continue

        mate_indexes = match.group(1).split(",")

        # TODO: make this less ugly
        for index in mate_indexes:
            if index in in_event_cats:
                if in_event_cats[index] in (
                    "apprentice",
                    "healer apprentice",
                    "mediator apprentice",
                ):
                    print("Can't give apprentices mates")
                    continue

                give_mates.append(in_event_cats[index])

            try:
                index = int(index)
            except ValueError:
                print(f"mate-index not correct: {index}")
                continue

            if index >= i:
                continue

            give_mates.extend(event.new_cats[index])

    # determine gender
    if "male" in attribute_list:
        gender = "male"
    elif "female" in attribute_list:
        gender = "female"
    elif (
            "can_birth" in attribute_list and not game.clan.clan_settings["same sex birth"]
    ):
        gender = "female"
    else:
        gender = None

    # will the cat get a new name?
    if "new_name" in attribute_list:
        new_name = True
    elif "old_name" in attribute_list:
        new_name = False
    else:
        new_name = bool(getrandbits(1))

    # STATUS - must be handled before backstories
    status = None
    for _tag in attribute_list:
        match = re.match(r"status:\s?(.+)", _tag)
        if not match:
            continue

        elif match.group(1) in (
            "deputy",
            "leader"
        ):
            status = "warrior"
            break
        elif match.group(1) in (
            "newborn",
            "kitten",
            "elder",
            "apprentice",
            "warrior",
            "mediator apprentice",
            "mediator",
            "healer apprentice",
            "healer",
        ):
            status = match.group(1)
            break

    # SET AGE
    age = None
    for _tag in attribute_list:
        match = re.match(r"age:\s?(.+)", _tag)
        if not match:
            continue

        if match.group(1) in Cat.age_moons:
            min_age, max_age = Cat.age_moons[CatAgeEnum(match.group(1))]
            age = randint(min_age, max_age)
            break

        # Set same as first mate
        if match.group(1) == "mate" and give_mates:
            min_age, max_age = Cat.age_moons[give_mates[0].age]
            age = randint(min_age, max_age)
            break

        if match.group(1) == "has_kits":
            age = randint(19, 120)
            break

    if status and not age:
        if status in ("apprentice", "mediator apprentice", "healer apprentice"):
            age = randint(
                Cat.age_moons[CatAgeEnum.ADOLESCENT][0],
                Cat.age_moons[CatAgeEnum.ADOLESCENT][1],
            )
        elif status in ("warrior", "mediator", "healer"):
            age = randint(
                Cat.age_moons["young adult"][0], Cat.age_moons["senior adult"][1]
            )
        elif status == "elder":
            age = randint(Cat.age_moons["senior"][0], Cat.age_moons["senior"][1])

    if "kittypet" in attribute_list:
        cat_type = "kittypet"
    elif "rogue" in attribute_list:
        cat_type = "rogue"
    elif "loner" in attribute_list:
        cat_type = "loner"
    elif "clancat" in attribute_list:
        cat_type = "former Clancat"
    else:
        if game.clan.clancount == "multiclan":
            cat_type = choice(['kittypet', 'kittypet', 'loner', 'loner'])
        else:
            cat_type = choice(['kittypet', 'kittypet', 'loner', 'loner', 'former Clancat'])

    # LITTER
    litter = False
    if "litter" in attribute_list:
        litter = True
        if status not in ("kitten", "newborn"):
            status = "kitten"

    # CHOOSE DEFAULT BACKSTORY BASED ON CAT TYPE, STATUS
    if status in ("kitten", "newborn"):
        chosen_backstory = choice(
            BACKSTORIES["backstory_categories"]["abandoned_backstories"]
        )
    elif status == "healer" and cat_type == "former Clancat":
        chosen_backstory = choice(["medicine_cat", "disgraced1"])
    elif status == "healer":
        chosen_backstory = choice(["wandering_healer1", "wandering_healer2"])
    else:
        if cat_type == "former Clancat":
            x = "former_clancat"
        else:
            x = cat_type
        chosen_backstory = choice(
            BACKSTORIES["backstory_categories"].get(f"{x}_backstories", ["outsider1"])
        )

    # OPTION TO OVERRIDE DEFAULT BACKSTORY
    bs_override = False
    stor = []
    for _tag in attribute_list:
        match = re.match(r"backstory:\s?(.+)", _tag)
        if match:
            bs_list = [x for x in re.split(r", ?", match.group(1))]
            stor = []
            for story in bs_list:
                if story in set(
                        [
                            backstory
                            for backstory_block in BACKSTORIES[
                            "backstory_categories"
                        ].values()
                            for backstory in backstory_block
                        ]
                ):
                    stor.append(story)
                elif story in BACKSTORIES["backstory_categories"]:
                    stor.extend(BACKSTORIES["backstory_categories"][story])
            bs_override = True
            break
    if bs_override and stor:
        chosen_backstory = choice(stor)

    # KITTEN THOUGHT
    if status in ("kitten", "newborn"):
        thought = i18n.t("hardcoded.thought_new_kitten")

    # MEETING - DETERMINE IF THIS IS AN OUTSIDE CAT
    outside = False
    if "meeting" in attribute_list:
        outside = True
        status = cat_type
        new_name = False
        thought = i18n.t("hardcoded.thought_meeting")
        if age is not None and age <= 6 and not bs_override:
            chosen_backstory = "outsider1"

    # IS THE CAT DEAD?
    alive = True
    if "dead" in attribute_list:
        alive = False
        thought = i18n.t("hardcoded.thought_new_dead")

    # check if we can use an existing cat here
    chosen_cat = None
    if "exists" in attribute_list:
        existing_outsiders = [
            i for i in Cat.all_cats.values() if i.outside and not i.dead
        ]
        possible_outsiders = []
        for cat in existing_outsiders:
            if stor and cat.backstory not in stor:
                continue
            if cat_type != cat.status:
                continue
            if gender and gender != cat.gender:
                continue
            if age and age not in Cat.age_moons[cat.age]:
                continue
            possible_outsiders.append(cat)

        if possible_outsiders:
            chosen_cat = choice(possible_outsiders)
            game.clan.add_to_clan(chosen_cat, clan=clan)
            if not status:
                if chosen_cat.moons == 0:
                    status = "newborn"
                elif chosen_cat.moons < 6:
                    status = "kitten"
                elif 6 <= chosen_cat.moons <= 11:
                    status = "apprentice"
                elif chosen_cat.moons >= 120:
                    status = "elder"
                elif chosen_cat.moons >= 12:
                    status = "warrior"
            chosen_cat.outside = outside
            if not outside:
                chosen_cat.status = status
                chosen_cat.group = clan
            if not alive:
                chosen_cat.die()

            if new_name:
                name = f"{chosen_cat.name.prefix}"

                if chosen_cat.history:
                    chosen_cat.history.prev_names.append(str(chosen_cat.name))
                else:
                    chosen_cat.history = History(prev_names=[str(chosen_cat.name)])
                spaces = name.count(" ")
                if bool(getrandbits(1)) and spaces > 0:  # adding suffix to OG name
                    # make a list of the words within the name, then add the OG name back in the list
                    words = name.split(" ")
                    words.append(name)
                    new_prefix = choice(words)  # pick new prefix from that list
                    name = new_prefix
                    chosen_cat.name.prefix = name
                    chosen_cat.name.give_suffix(
                        skills=chosen_cat.skills,
                        personality=chosen_cat.personality,
                        biome=game.clan.biome
                    )
                else:  # completely new name
                    chosen_cat.name.give_prefix(
                        Cat, 
                        biome=game.clan.biome
                    )
                    chosen_cat.name.give_suffix(
                        skills=chosen_cat.skills,
                        personality=chosen_cat.personality,
                        biome=game.clan.biome
                    )

            new_cats = [chosen_cat]

    # Now we generate the new cat
    if not chosen_cat:
        generated_parents = []
        if status in ["kitten", "newborn"]:
            generated_parents = create_bio_parents(Cat, cat_type, flip=True if parent1 and 'Y' in parent1.phenotype.sexgene else False, second_parent=not parent1)
            if not parent1:
                parent1 = generated_parents[1]
            if not parent2:
                parent2 = generated_parents[0]
        new_cats = create_new_cat(
            Cat,
            new_name=new_name,
            loner=cat_type in ("loner", "rogue"),
            kittypet=cat_type == "kittypet",
            other_clan=cat_type == "former Clancat",
            kit=(not litter) and status in ("kitten", "newborn"),
            # this is for singular kits, litters need this to be false
            litter=litter,
            backstory=chosen_backstory,
            status=status,
            age=age,
            gender=gender,
            thought=thought,
            alive=alive,
            outside=outside,
            group=clan,
            parent1=parent1.ID if parent1 else None,
            parent2=parent2.ID if parent2 else None,
            extrapar=generated_parents[2] if not parent2 and generated_parents else None,
            is_parent= "age:has_kits" in attribute_list,
            adoptive_parents=adoptive_parents if adoptive_parents else None
            )
        while "age:has_kits" in attribute_list and "infertility" in new_cats[0].permanent_condition:
            del Cat.all_cats[new_cats[0].ID]
            new_cats[0] = create_new_cat(
                Cat,
                new_name=new_name,
                loner=cat_type in ["loner", "rogue"],
                kittypet=cat_type == "kittypet",
                other_clan=cat_type == 'former Clancat',
                kit=False if litter else status in ["kitten", "newborn"],
                litter=litter,
                backstory=chosen_backstory,
                status=status,
                age=age,
                gender=gender,
                thought=thought,
                alive=alive,
                outside=outside,
                parent1=parent1.ID if parent1 else None,
                parent2=parent2.ID if parent2 else None,
                extrapar=generated_parents[2] if not parent2 and generated_parents else None,
                is_parent= "age:has_kits" in attribute_list,
                adoptive_parents=adoptive_parents if adoptive_parents else None
                )[0]

        # NEXT
        # add relations to bio parents, if needed
        # add relations to cats generated within the same block, as they are littermates
        # add mates
        # THIS DOES NOT ADD RELATIONS TO CATS IN THE EVENT, those are added within the relationships block of the event

        fevercoat = False
        if random() < 0.01:
            fevercoat = True

        for n_c in new_cats:

            if n_c.phenotype.manx[1] == "Ab" or n_c.phenotype.manx[1] == "M" or n_c.phenotype.munch[1] == "Mk" or ('NoDBE' not in n_c.phenotype.pax3 and 'DBEalt' not in n_c.phenotype.pax3):
                n_c.moons = 0
                n_c.status = "newborn"
                n_c.dead = True
                History.add_death(n_c, str(n_c.name) + " was stillborn.")
                new_cats.remove(n_c)
                continue

            if fevercoat:
                n_c.phenotype.fevercoat = True
                if n_c.chimerapheno:
                    n_c.chimerapheno.fevercoat = True

            # SET MATES
            for inter_cat in give_mates:
                if n_c == inter_cat or n_c.ID in inter_cat.mate:
                    continue

                # this is some duplicate work, since this triggers inheritance re-calcs
                # TODO: optimize
                n_c.set_mate(inter_cat)

            # LITTERMATES
            for inter_cat in new_cats:
                if n_c == inter_cat:
                    continue

                y = randrange(0, 20)
                start_relation = Relationship(n_c, inter_cat, False, True)
                start_relation.platonic_like += 30 + y
                start_relation.comfortable = 10 + y
                start_relation.admiration = 15 + y
                start_relation.trust = 10 + y
                n_c.relationships[inter_cat.ID] = start_relation

            # BIO PARENTS
            for par in (parent1, parent2):
                if not par:
                    continue

                y = randrange(0, 20)
                start_relation = Relationship(par, n_c, False, True)
                start_relation.platonic_like += 30 + y
                start_relation.comfortable = 10 + y
                start_relation.admiration = 15 + y
                start_relation.trust = 10 + y
                par.relationships[n_c.ID] = start_relation

                y = randrange(0, 20)
                start_relation = Relationship(n_c, par, False, True)
                start_relation.platonic_like += 30 + y
                start_relation.comfortable = 10 + y
                start_relation.admiration = 15 + y
                start_relation.trust = 10 + y
                n_c.relationships[par.ID] = start_relation

            # ADOPTIVE PARENTS
            for par in adoptive_parents:
                if not par:
                    continue

                par = Cat.fetch_cat(par)

                y = randrange(0, 20)
                start_relation = Relationship(par, n_c, False, True)
                start_relation.platonic_like += 30 + y
                start_relation.comfortable = 10 + y
                start_relation.admiration = 15 + y
                start_relation.trust = 10 + y
                par.relationships[n_c.ID] = start_relation

                y = randrange(0, 20)
                start_relation = Relationship(n_c, par, False, True)
                start_relation.platonic_like += 30 + y
                start_relation.comfortable = 10 + y
                start_relation.admiration = 15 + y
                start_relation.trust = 10 + y
                n_c.relationships[par.ID] = start_relation

            # UPDATE INHERITANCE
            n_c.create_inheritance_new_cat()

    return new_cats


def find_clan_cats(Cat, Relationship, event, in_event_cats: dict, i: int, attribute_list: List[str], clan=None, other_clan=None):
    status = None
    age = None
    adoptive_parents = []
    give_mates = []
    picked_cats = []
    
    all_clan_cats = [i for i in Cat.all_cats.values() if i.group == other_clan and not i.outside and not i.dead]
    for a in attribute_list:
        match = re.match(r'status:\s?(.+)', a)
        if match:
            status = match.group(1)
        match = re.match(r'age:\s?(.+)', a)
        if match:
            age = match.group(1)
        match = re.match(r"adoptive:\s?(.+)", a)
        if match:
            adoptive_indexes = match.group(1).split(",") if match else []
            if not adoptive_indexes:
                continue

            adoptive_indexes = [
                int(index) if index.isdigit() else index for index in adoptive_indexes
            ]
            for index in adoptive_indexes:
                if in_event_cats[index].ID not in adoptive_parents:
                    adoptive_parents.append(in_event_cats[index].ID)
                    adoptive_parents.extend(in_event_cats[index].mate)

    # OPTION TO OVERRIDE DEFAULT BACKSTORY
    bs_override = False
    stor = []
    for _tag in attribute_list:
        match = re.match(r"backstory:\s?(.+)", _tag)
        if match:
            bs_list = [x for x in re.split(r", ?", match.group(1))]
            stor = []
            for story in bs_list:
                if story in set(
                        [
                            backstory
                            for backstory_block in BACKSTORIES[
                                "backstory_categories"
                            ].values()
                            for backstory in backstory_block
                        ]
                ):
                    stor.append(story)
                elif story in BACKSTORIES["backstory_categories"]:
                    stor.extend(BACKSTORIES["backstory_categories"][story])
            bs_override = True
            break
    if bs_override and stor:
        chosen_backstory = choice(stor)

    for tag in attribute_list:
        match = re.match(r"mate:\s?([_,0-9a-zA-Z]+)", tag)
        if not match:
            continue

        mate_indexes = match.group(1).split(",")

        # TODO: make this less ugly
        for index in mate_indexes:
            if index in in_event_cats:
                if in_event_cats[index] in (
                    "apprentice",
                    "healer apprentice",
                    "mediator apprentice",
                ):
                    print("Can't give apprentices mates")
                    continue

                give_mates.append(in_event_cats[index])

            try:
                index = int(index)
            except ValueError:
                print(f"mate-index not correct: {index}")
                continue

            if index >= i:
                continue

            give_mates.extend(event.new_cats[index])


        
    if "litter" in attribute_list:
        (parents, orphans) = get_alive_clan_queens(all_clan_cats, clan=other_clan)[0]
        if parents:
            litter = parents[choice(list(parents.keys()))]
            picked_cats = litter
        else:
            picked_cats = [choice(orphans)]
    else:
        if status == "any_apprentice":
            all_clan_cats = [cat for cat in all_clan_cats if "apprentice" in cat.status]
        elif status:
            all_clan_cats = [cat for cat in all_clan_cats if cat.status == status]
        
        if age == "mate":
            all_clan_cats = [cat for cat in all_clan_cats if give_mates[0].is_potential_mate(cat, for_love_interest=True, outsider=True)]
            if not all_clan_cats:
                print("No possible mates found")
                all_clan_cats = create_new_cat_block(Cat, Relationship, event, in_event_cats, i, attribute_list, other_clan)
        elif age:
            all_clan_cats_age = [cat for cat in all_clan_cats if cat.age == age]
            if all_clan_cats_age:
                all_clan_cats = all_clan_cats_age
        picked_cats = [choice(all_clan_cats)]

    if "change_clan" in attribute_list:
        for cat in picked_cats:
            cat.group = clan
            if cat.status == "leader":
                other_clan.leader = None
                other_clan.leader_lives = 0
            if cat.status == "deputy":
                other_clan.deputy = None
            if cat.status == "healer":
                other_clan.remove_med_cat(cat)
            if cat.status in ["leader", "deputy"]:
                cat.status = "warrior"

        # ADOPTIVE PARENTS
        for par in adoptive_parents:
            if not par:
                continue

            par = Cat.fetch_cat(par)

            y = randrange(0, 20)
            start_relation = Relationship(par, cat, False, True)
            start_relation.platonic_like += 30 + y
            start_relation.comfortable = 10 + y
            start_relation.admiration = 15 + y
            start_relation.trust = 10 + y
            par.relationships[cat.ID] = start_relation

            y = randrange(0, 20)
            start_relation = Relationship(cat, par, False, True)
            start_relation.platonic_like += 30 + y
            start_relation.comfortable = 10 + y
            start_relation.admiration = 15 + y
            start_relation.trust = 10 + y
            cat.relationships[par.ID] = start_relation

        # UPDATE INHERITANCE
        cat.create_inheritance_new_cat()
    elif "change_clan_rev" in attribute_list:
        give_mates[0].group = other_clan
        if give_mates[0].status == "leader":
            clan.leader = None
            clan.leader_lives = 0
        if give_mates[0].status == "deputy":
            clan.deputy = None
        if give_mates[0].status == "healer":
            clan.remove_med_cat(cat)
        if give_mates[0].status in ["leader", "deputy"]:
            cat.status = "warrior"
    
    if "dead" in attribute_list:
        for cat in picked_cats:
            cat.die(True)

    for cat in picked_cats:
        cat.backstory = chosen_backstory
        
        # SET MATES
        for inter_cat in give_mates:
            if cat == inter_cat or cat.ID in inter_cat.mate:
                continue

            # this is some duplicate work, since this triggers inheritance re-calcs
            # TODO: optimize
            cat.set_mate(inter_cat)

    return picked_cats


def get_other_clan(clan_name):
    """
    returns the clan object of given clan name
    """
    for clan in game.clan.all_clans:
        if clan.name == clan_name:
            return clan


def create_new_cat(
    Cat: Union["Cat", Type["Cat"]],
    new_name: bool = False,
    loner: bool = False,
    kittypet: bool = False,
    kit: bool = False,
    litter: bool = False,
    other_clan: bool = None,
    backstory: bool = None,
    status: str = None,
    age: int = None,
    gender: str = None,
    thought: str = None,
    alive: bool = True,
    outside: bool = False,
    group = None,
    parent1: str = None,
    parent2: str = None,
    extrapar: Genotype = None,
    adoptive_parents: list = None,
    is_parent: bool = False
) -> list:
    """
    This function creates new cats and then returns a list of those cats
    :param Cat Cat: pass the Cat class
    :params Relationship Relationship: pass the Relationship class
    :param bool new_name: set True if cat(s) is a loner/rogue receiving a new Clan name - default: False
    :param bool loner: set True if cat(s) is a loner or rogue - default: False
    :param bool kittypet: set True if cat(s) is a kittypet - default: False
    :param bool kit: set True if the cat is a lone kitten - default: False
    :param bool litter: set True if a litter of kittens needs to be generated - default: False
    :param bool other_clan: if new cat(s) are from a neighboring clan, set true
    :param bool backstory: a list of possible backstories.json for the new cat(s) - default: None
    :param str status: set as the rank you want the new cat to have - default: None (will cause a random status to be picked)
    :param int age: set the age of the new cat(s) - default: None (will be random or if kit/litter is true, will be kitten.
    :param str gender: set the gender (BIRTH SEX) of the cat - default: None (will be random)
    :param str thought: if you need to give a custom "welcome" thought, set it here
    :param bool alive: set this as False to generate the cat as already dead - default: True (alive)
    :param bool outside: set this as True to generate the cat as an outsider instead of as part of the Clan - default: False (Clan cat)
    :param str parent1: Cat ID to set as the biological parent1
    :param str parent2: Cat ID to set as the biological parent2
    :param list adoptive_parents: Cat IDs to set as adoptive parents
    """

    if thought is None:
        thought = i18n.t("hardcoded.thought_new_cat")

    # TODO: it would be nice to rewrite this to be less bool-centric
    accessory = None
    if isinstance(backstory, list):
        backstory = choice(backstory)

    if backstory in (
            BACKSTORIES["backstory_categories"]["former_clancat_backstories"]
            or BACKSTORIES["backstory_categories"]["otherclan_categories"]
    ):
        other_clan = True

    created_cats = []

    if not litter:
        number_of_cats = 1
    else:
        number_of_cats = choices([2, 3, 4, 5], [5, 4, 1, 1], k=1)[0]

    if (litter or kit):
        parent_thought = i18n.t("conditions.pregnancy.half_blood_kitting_thought", count=number_of_cats)
        Cat.all_cats[parent1].thought = event_text_adjust(Cat, parent_thought, main_cat=Cat.all_cats[parent1])
        Cat.all_cats[parent2].thought = event_text_adjust(Cat, parent_thought, main_cat=Cat.all_cats[parent2])
    

    if not isinstance(age, int):
        if status == "newborn":
            age = 0
        elif litter or kit:
            age = randint(1, 5)
        elif status in ('apprentice', 'healer apprentice', 'mediator apprentice'):
            age = randint(6, 11)
        elif status == "warrior":
            age = randint(23, 120)
        elif status == 'healer':
            age = randint(23, 140)
        elif status == "elder":
            age = randint(120, 130)
        else:
            age = randint(6, 120)

    # setting status
    if not status:
        if age == 0:
            status = "newborn"
        elif age < 6:
            status = "kitten"
        elif 6 <= age <= 11:
            status = "apprentice"
        elif age >= 120:
            status = "elder"
        elif age >= 12:
            status = "warrior"

    # cat creation and naming time
    for index in range(number_of_cats):
        # setting gender
        if not gender:
            _gender = choice(['fem', 'masc'])
        else:
            _gender = gender

        # other Clan cats, apps, and kittens (kittens and apps get indoctrinated lmao no old names for them)
        if other_clan or kit or litter or age < 12 and not (loner or kittypet):
            new_cat = Cat(
                moons=age,
                status=status,
                group=group if group and status not in ["kittypet", "loner", "rogue", "former Clancat"] else None,
                gender=_gender,
                backstory=backstory,
                parent1=parent1,
                parent2=parent2,
                extrapar=extrapar,
                adoptive_parents=adoptive_parents if adoptive_parents else []
            )
        else:
            # grab starting names and accs for loners/kittypets
            overwrite_prefix = False
            if kittypet:
                name = choice(names.names_dict["loner_names"])
            elif loner and bool(
                    getrandbits(1)
            ):  # try to give name from full loner name list
                name = choice(names.names_dict["loner_names"])
            else:
                name = choice(
                    names.names_dict["normal_prefixes"]
                )  # otherwise give name from prefix list (more nature-y names)
                if game.clan.clan_settings["modded names"] and game.clan.clan_settings['new prefixes'] and random() < 0.9:
                    overwrite_prefix = True

            # now we make the cats
            if new_name:  # these cats get new names
                if bool(getrandbits(1)):  # adding suffix to OG name
                    spaces = name.count(" ")
                    if spaces > 0:
                        # make a list of the words within the name, then add the OG name back in the list
                        words = name.split(" ")
                        words.append(name)
                        new_prefix = choice(words)  # pick new prefix from that list
                        name = new_prefix
                    new_cat = Cat(
                        moons=age,
                        prefix=name,
                        status=status,
                        group=group if group and status not in ["kittypet", "loner", "rogue", "former Clancat"] else None,
                        gender=_gender,
                        backstory=backstory,
                        parent1=parent1,
                        parent2=parent2,
                        kittypet=kittypet,
                        adoptive_parents=adoptive_parents if adoptive_parents else []
                    )
                    if overwrite_prefix:
                        new_cat.name.give_prefix(Cat, game.clan.biome)
                else:  # completely new name
                    new_cat = Cat(
                        moons=age,
                        status=status,
                        group=group if group and status not in ["kittypet", "loner", "rogue", "former Clancat"] else None,
                        gender=_gender,
                        backstory=backstory,
                        parent1=parent1,
                        parent2=parent2,
                        kittypet=kittypet,
                        adoptive_parents=adoptive_parents if adoptive_parents else []
                    )
            # these cats keep their old names
            else:
                new_cat = Cat(
                    moons=age,
                    prefix=name,
                    suffix="",
                    status=status,
                    group=group if group and status not in ["kittypet", "loner", "rogue", "former Clancat"] else None,
                    gender=_gender,
                    backstory=backstory,
                    parent1=parent1,
                    parent2=parent2,
                    kittypet=kittypet,
                    adoptive_parents=adoptive_parents if adoptive_parents else []
                )
                if overwrite_prefix:
                    new_cat.name.give_prefix(Cat, game.clan.biome, no_suffix=True)

            if kittypet:
                if bool(getrandbits(1)):
                    accessory = choice(new_cat.pelt.collars)

        # give em a collar if they got one
        if accessory:
            new_cat.pelt.accessory = [accessory]

        # give apprentice aged cat a mentor
        if new_cat.age == "adolescent":
            new_cat.update_mentor()

        # Remove disabling scars, if they generated.
        not_allowed = [
            "NOPAW",
            "NOTAIL",
            "HALFTAIL",
            "NOEAR",
            "BOTHBLIND",
            "RIGHTBLIND",
            "LEFTBLIND",
            "BRIGHTHEART",
            "NOLEFTEAR",
            "NORIGHTEAR",
            "MANLEG",
        ]
        for scar in new_cat.pelt.scars:
            if scar in not_allowed:
                new_cat.pelt.scars.remove(scar)

        # chance to give the new cat a permanent condition, higher chance for found kits and litters
        if kit or litter:
            chance = int(
                game.config["cat_generation"]["base_permanent_condition"] / 11.25
            )
        else:
            chance = game.config["cat_generation"]["base_permanent_condition"] + 10
        
        if not is_parent and game.clan.clan_settings['tnr_mode'] and age > 5:
            kittypet_n = game.config['tnr_mode']['kittypet_neuter']
            loner_n = game.config['tnr_mode']['loner_tnr']
            if kittypet and random() < kittypet_n:
                new_cat.get_permanent_condition("infertility", False)
            if loner and random() < loner_n:
                new_cat.get_permanent_condition("infertility", False)
                new_cat.pelt.scars.append("TNR")
        if not int(random() * chance):
            possible_conditions = []
            for condition in PERMANENT:
                if (kit or litter) and PERMANENT[condition]["congenital"] not in (
                    "always",
                    "sometimes",
                ):
                    continue
                if condition in ['manx syndrome', "flat nose", 'ocular albinism', 'albinism', 'rabbit gait', 'fully hairless', 'partially hairless', "bad back", "narrowed chest", "bumpy skin"]:
                    continue
                # next part ensures that a kit won't get a condition that takes too long to reveal
                age = new_cat.moons
                leeway = 5 - (PERMANENT[condition]["moons_until"] + 1)
                if age > leeway:
                    continue
                possible_conditions.append(condition)

            if possible_conditions:
                chosen_condition = choice(possible_conditions)
                born_with = False
                if PERMANENT[chosen_condition]["congenital"] in (
                    "always",
                    "sometimes",
                ):
                    born_with = True

                    new_cat.get_permanent_condition(chosen_condition, born_with)
                    if (
                            new_cat.permanent_condition[chosen_condition]["moons_until"]
                            == 0
                    ):
                        new_cat.permanent_condition[chosen_condition][
                            "moons_until"
                        ] = -2

                # assign scars
                if chosen_condition in ("lost a leg", "born without a leg"):
                    new_cat.pelt.scars.append("NOPAW")
                elif chosen_condition in ("lost their tail", "born without a tail"):
                    new_cat.pelt.scars.append("NOTAIL")

        if outside:
            new_cat.outside = True
            if new_cat.status in ["kittypet", "rogue", "loner"]:
                new_cat.name.suffix = ""
        if not alive:
            new_cat.die()

        # newbie thought
        new_cat.thought = thought

        # and they exist now
        created_cats.append(new_cat)
        game.clan.add_cat(new_cat)
        history = History()
        history.add_beginning(new_cat)

        # create relationships
        new_cat.create_relationships_new_cat()
        # Note - we always update inheritance after the cats are generated, to
        # allow us to add parents.
        # new_cat.create_inheritance_new_cat()

    return created_cats


# ---------------------------------------------------------------------------- #
#                             Cat Relationships                                #
# ---------------------------------------------------------------------------- #


def get_highest_romantic_relation(
        relationships, exclude_mate=False, potential_mate=False
):
    """Returns the relationship with the highest romantic value."""
    max_love_value = 0
    current_max_relationship = None
    for rel in relationships:
        if rel.romantic_love < 0:
            continue
        if exclude_mate and rel.cat_from.ID in rel.cat_to.mate:
            continue
        if potential_mate and not rel.cat_to.is_potential_mate(
                rel.cat_from, for_love_interest=True
        ):
            continue
        if rel.romantic_love > max_love_value:
            current_max_relationship = rel
            max_love_value = rel.romantic_love

    return current_max_relationship


def check_relationship_value(cat_from, cat_to, rel_value=None):
    """
    returns the value of the rel_value param given
    :param cat_from: the cat who is having the feelings
    :param cat_to: the cat that the feelings are directed towards
    :param rel_value: the relationship value that you're looking for,
    options are: romantic, platonic, dislike, admiration, comfortable, jealousy, trust
    """
    if cat_to.ID in cat_from.relationships:
        relationship = cat_from.relationships[cat_to.ID]
    else:
        return 0

    if rel_value == "romantic":
        return relationship.romantic_love
    elif rel_value == "platonic":
        return relationship.platonic_like
    elif rel_value == "dislike":
        return relationship.dislike
    elif rel_value == "admiration":
        return relationship.admiration
    elif rel_value == "comfortable":
        return relationship.comfortable
    elif rel_value == "jealousy":
        return relationship.jealousy
    elif rel_value == "trust":
        return relationship.trust


def get_personality_compatibility(cat1, cat2):
    """Returns:
    True - if personalities have a positive compatibility
    False - if personalities have a negative compatibility
    None - if personalities have a neutral compatibility
    """
    personality1 = cat1.personality.trait
    personality2 = cat2.personality.trait

    if personality1 == personality2:
        if personality1 is None:
            return None
        return True

    lawfulness_diff = abs(cat1.personality.lawfulness - cat2.personality.lawfulness)
    sociability_diff = abs(cat1.personality.sociability - cat2.personality.sociability)
    aggression_diff = abs(cat1.personality.aggression - cat2.personality.aggression)
    stability_diff = abs(cat1.personality.stability - cat2.personality.stability)
    list_of_differences = [
        lawfulness_diff,
        sociability_diff,
        aggression_diff,
        stability_diff,
    ]

    running_total = 0
    for x in list_of_differences:
        if x <= 4:
            running_total += 1
        elif x >= 6:
            running_total -= 1

    if running_total >= 2:
        return True
    if running_total <= -2:
        return False

    return None


def get_cats_of_romantic_interest(cat):
    """Returns a list of cats, those cats are love interest of the given cat"""
    cats = []
    for inter_cat in cat.all_cats.values():
        if inter_cat.dead or inter_cat.outside or inter_cat.exiled or inter_cat.group != cat.group:
            continue
        if inter_cat.ID == cat.ID:
            continue

        if inter_cat.ID not in cat.relationships:
            continue

        # Extra check to ensure they are potential mates
        if (
                inter_cat.is_potential_mate(cat, for_love_interest=True)
                and cat.relationships[inter_cat.ID].romantic_love > 0
        ):
            cats.append(inter_cat)
    return cats


def get_amount_of_cats_with_relation_value_towards(cat, value, all_cats):
    """
    Looks how many cats have the certain value
    :param cat: cat in question
    :param value: value which has to be reached
    :param all_cats: list of cats which has to be checked
    """

    # collect all true or false if the value is reached for the cat or not
    # later count or sum can be used to get the amount of cats
    # this will be handled like this, because it is easier / shorter to check
    relation_dict = {
        "romantic_love": [],
        "platonic_like": [],
        "dislike": [],
        "admiration": [],
        "comfortable": [],
        "jealousy": [],
        "trust": [],
    }

    for inter_cat in all_cats:
        if cat.ID in inter_cat.relationships:
            relation = inter_cat.relationships[cat.ID]
        else:
            continue

        relation_dict["romantic_love"].append(relation.romantic_love >= value)
        relation_dict["platonic_like"].append(relation.platonic_like >= value)
        relation_dict["dislike"].append(relation.dislike >= value)
        relation_dict["admiration"].append(relation.admiration >= value)
        relation_dict["comfortable"].append(relation.comfortable >= value)
        relation_dict["jealousy"].append(relation.jealousy >= value)
        relation_dict["trust"].append(relation.trust >= value)

    return_dict = {
        "romantic_love": sum(relation_dict["romantic_love"]),
        "platonic_like": sum(relation_dict["platonic_like"]),
        "dislike": sum(relation_dict["dislike"]),
        "admiration": sum(relation_dict["admiration"]),
        "comfortable": sum(relation_dict["comfortable"]),
        "jealousy": sum(relation_dict["jealousy"]),
        "trust": sum(relation_dict["trust"]),
    }

    return return_dict


def filter_relationship_type(
        group: list, filter_types: List[str], event_id: str = None, patrol_leader=None
):
    """
    filters for specific types of relationships between groups of cat objects, returns bool
    :param list[Cat] group: the group of cats to be tested (make sure they're in the correct order (i.e. if testing for
    parent/child, the cat being tested as parent must be index 0)
    :param list[str] filter_types: the relationship types to check for. possible types: "siblings", "mates",
    "mates_with_pl" (PATROL ONLY), "not_mates", "parent/child", "child/parent", "mentor/app", "app/mentor",
    (following tags check if value is over given int) "romantic_int", "platonic_int", "dislike_int", "comfortable_int",
    "jealousy_int", "trust_int"
    :param str event_id: if the event has an ID, include it here
    :param Cat patrol_leader: if you are testing a patrol, ensure you include the self.patrol_leader here
    """
    if not filter_types:
        return True

    # keeping this list here just for quick reference of what tags are handled here
    possible_rel_types = [
        "siblings",
        "mates",
        "mates_with_pl",
        "not_mates",
        "parent/child",
        "child/parent",
        "mentor/app",
        "app/mentor",
    ]

    possible_value_types = [
        "romantic",
        "platonic",
        "dislike",
        "comfortable",
        "jealousy",
        "trust",
        "admiration",
    ]

    if "siblings" in filter_types:
        test_cat = group[0]
        testing_cats = [cat for cat in group if cat.ID != test_cat.ID]

        siblings = [test_cat.is_sibling(inter_cat) for inter_cat in testing_cats]
        if not all(siblings):
            return False

    if "mates" in filter_types:
        # first test if more than one cat
        if len(group) == 1:
            return False

        # then if cats don't have the needed number of mates
        if not all(len(i.mate) >= (len(group) - 1) for i in group):
            return False

        # Now the expensive test.  We have to see if everone is mates with each other
        # Hopefully the cheaper tests mean this is only needed on events with a small number of cats
        for x in combinations(group, 2):
            if x[0].ID not in x[1].mate:
                return False

    # check if all cats are mates with p_l (they do not have to be mates with each other)
    if "mates_with_pl" in filter_types:
        # First test if there is more than one cat
        if len(group) == 1:
            return False

        # Check each cat to see if it is mates with the patrol leader
        for cat in group:
            if cat.ID == patrol_leader.ID:
                continue
            if cat.ID not in patrol_leader.mate:
                return False

    # Check if all cats are not mates
    if "not_mates" in filter_types:
        # opposite of mate check
        for x in combinations(group, 2):
            if x[0].ID in x[1].mate:
                return False

    # Check if the cats are in a parent/child relationship
    if "parent/child" in filter_types:
        if patrol_leader:
            if patrol_leader in group:
                group.remove(patrol_leader)
            group.insert(0, patrol_leader)
        # It should be exactly two cats for a "parent/child" event
        if len(group) != 2:
            return False
        # test for parentage
        if not group[0].is_parent(group[1]):
            return False

    if "child/parent" in filter_types:
        if patrol_leader:
            if patrol_leader in group:
                group.remove(patrol_leader)
            group.insert(0, patrol_leader)
        # It should be exactly two cats for a "parent/child" event
        if len(group) != 2:
            return False
        # test for parentage
        if not group[1].is_parent(group[0]):
            return False

    if "mentor/app" in filter_types:
        if patrol_leader:
            if patrol_leader in group:
                group.remove(patrol_leader)
            group.insert(0, patrol_leader)
        # It should be exactly two cats for a "parent/child" event
        if len(group) != 2:
            return False
        # test for parentage
        if not group[1].ID in group[0].apprentice:
            return False

    if "app/mentor" in filter_types:
        if patrol_leader:
            if patrol_leader in group:
                group.remove(patrol_leader)
            group.insert(0, patrol_leader)
        # It should be exactly two cats for a "parent/child" event
        if len(group) != 2:
            return False
        # test for parentage
        if not group[0].ID in group[1].apprentice:
            return False

    # Filtering relationship values
    break_loop = False
    for v_type in possible_value_types:
        # first get all tags for current value types
        tags = [constraint for constraint in filter_types if v_type in constraint]

        # If there is not a tag for the current value type, check next one
        if len(tags) == 0:
            continue

            # there should be only one value constraint for each value type
        elif len(tags) > 1:
            print(
                f"ERROR: event {event_id} has multiple relationship constraints for the value {v_type}."
            )
            break_loop = True
            break

        # try to extract the value/threshold from the text
        try:
            threshold = int(tags[0].split("_")[1])
        except:
            print(
                f"ERROR: event {event_id} with the relationship constraint for the value does not {v_type} follow the formatting guidelines."
            )
            break_loop = True
            break

        if threshold > 100:
            print(
                f"ERROR: event {event_id} has a relationship constraint for the value {v_type}, which is higher than the max value of a relationship."
            )
            break_loop = True
            break

        if threshold <= 0:
            print(
                f"ERROR: event {event_id} has a relationship constraint for the value {v_type}, which is lower than the min value of a relationship or 0."
            )
            break_loop = True
            break

        # each cat has to have relationships with this relationship value above the threshold
        fulfilled = True
        for inter_cat in group:
            rel_above_threshold = []
            group_ids = [cat.ID for cat in group]
            relevant_relationships = list(
                filter(
                    lambda rel: rel.cat_to.ID in group_ids
                                and rel.cat_to.ID != inter_cat.ID,
                    list(inter_cat.relationships.values()),
                )
            )

            # get the relationships depending on the current value type + threshold
            if v_type == "romantic":
                rel_above_threshold = [
                    i for i in relevant_relationships if i.romantic_love >= threshold
                ]
            elif v_type == "platonic":
                rel_above_threshold = [
                    i for i in relevant_relationships if i.platonic_like >= threshold
                ]
            elif v_type == "dislike":
                rel_above_threshold = [
                    i for i in relevant_relationships if i.dislike >= threshold
                ]
            elif v_type == "comfortable":
                rel_above_threshold = [
                    i for i in relevant_relationships if i.comfortable >= threshold
                ]
            elif v_type == "jealousy":
                rel_above_threshold = [
                    i for i in relevant_relationships if i.jealousy >= threshold
                ]
            elif v_type == "trust":
                rel_above_threshold = [
                    i for i in relevant_relationships if i.trust >= threshold
                ]
            elif v_type == "admiration":
                rel_above_threshold = [
                    i for i in relevant_relationships if i.admiration >= threshold
                ]

            # if the lengths are not equal, one cat has not the relationship value which is needed to another cat of
            # the event
            if len(rel_above_threshold) + 1 != len(group):
                fulfilled = False
                break

        if not fulfilled:
            break_loop = True
            break

    # if break is used in the loop, the condition are not fulfilled
    # and this event should not be added to the filtered list
    if break_loop:
        return False

    return True


def gather_cat_objects(
        Cat, abbr_list: List[str], event, stat_cat=None, extra_cat=None
) -> list:
    """
    gathers cat objects from list of abbreviations used within an event format block
    :param Cat Cat: Cat class
    :param list[str] abbr_list: The list of abbreviations, supports "m_c", "r_c", "p_l", "s_c", "app1" through "app6",
    "clan", "some_clan", "patrol", "multi", "n_c{index}"
    :param event: the controlling class of the event (e.g. Patrol, HandleShortEvents), default None
    :param Cat stat_cat: if passing the Patrol class, must include stat_cat separately
    :param Cat extra_cat: if not passing an event class, include the single affected cat object here. If you are not
    passing a full event class, then be aware that you can only include "m_c" as a cat abbreviation in your rel block.
    The other cat abbreviations will not work.
    :return: list of cat objects
    """
    out_set = set()

    for abbr in abbr_list:
        if abbr == "m_c":
            if extra_cat:
                out_set.add(extra_cat)
            else:
                out_set.add(event.main_cat)
        elif abbr == "r_c":
            out_set.add(event.random_cat)
        elif abbr == "p_l":
            out_set.add(event.patrol_leader)
        elif abbr == "s_c":
            out_set.add(stat_cat)
        elif abbr == "app1" and len(event.patrol_apprentices) >= 1:
            out_set.add(event.patrol_apprentices[0])
        elif abbr == "app2" and len(event.patrol_apprentices) >= 2:
            out_set.add(event.patrol_apprentices[1])
        elif abbr == "app3" and len(event.patrol_apprentices) >= 3:
            out_set.add(event.patrol_apprentices[2])
        elif abbr == "app4" and len(event.patrol_apprentices) >= 4:
            out_set.add(event.patrol_apprentices[3])
        elif abbr == "app5" and len(event.patrol_apprentices) >= 5:
            out_set.add(event.patrol_apprentices[4])
        elif abbr == "app6" and len(event.patrol_apprentices) >= 6:
            out_set.add(event.patrol_apprentices[5])
        elif abbr == "clan":
            out_set.update(
                [x for x in Cat.all_cats_list if not (x.dead or x.outside or x.exiled)]
            )
        elif abbr == "some_clan":  # 1 / 8 of clan cats are affected
            clan_cats = [
                x for x in Cat.all_cats_list if not (x.dead or x.outside or x.exiled)
            ]
            out_set.update(
                sample(clan_cats, randint(1, max(1, round(len(clan_cats) / 8))))
            )
        elif abbr == "patrol":
            out_set.update(event.patrol_cats)
        elif abbr == "multi":
            cat_num = randint(1, max(1, len(event.patrol_cats) - 1))
            out_set.update(sample(event.patrol_cats, cat_num))
        elif re.match(r"n_c:[0-9]+", abbr):
            index = re.match(r"n_c:([0-9]+)", abbr).group(1)
            index = int(index)
            if index < len(event.new_cats):
                out_set.update(event.new_cats[index])
        else:
            print(f"WARNING: Unsupported abbreviation {abbr}")

    return list(out_set)


def unpack_rel_block(
        Cat, relationship_effects: List[dict], event=None, stat_cat=None, extra_cat=None
):
    """
    Unpacks the info from the relationship effect block used in patrol and moon events, then adjusts rel values
    accordingly.

    :param Cat Cat: Cat class
    :param list[dict] relationship_effects: the relationship effect block
    :param event: the controlling class of the event (e.g. Patrol, HandleShortEvents), default None
    :param Cat stat_cat: if passing the Patrol class, must include stat_cat separately
    :param Cat extra_cat: if not passing an event class, include the single affected cat object here. If you are not passing a full event class, then be aware that you can only include "m_c" as a cat abbreviation in your rel block.  The other cat abbreviations will not work.
    """
    possible_values = (
        "romantic",
        "platonic",
        "dislike",
        "comfort",
        "jealous",
        "trust",
        "respect",
    )

    for block in relationship_effects:
        cats_from = block.get("cats_from", [])
        cats_to = block.get("cats_to", [])
        amount = block.get("amount")
        values = [x for x in block.get("values", ()) if x in possible_values]

        # Gather actual cat objects:
        cats_from_ob = gather_cat_objects(Cat, cats_from, event, stat_cat, extra_cat)
        cats_to_ob = gather_cat_objects(Cat, cats_to, event, stat_cat, extra_cat)

        # Remove any "None" that might have snuck in
        if None in cats_from_ob:
            cats_from_ob.remove(None)
        if None in cats_to_ob:
            cats_to_ob.remove(None)

        # Check to see if value block
        if not (cats_to_ob and cats_from_ob and values and isinstance(amount, int)):
            print(f"Relationship block incorrectly formatted: {block}")
            continue

        positive = False

        # grabbing values
        romantic_love = 0
        platonic_like = 0
        dislike = 0
        comfortable = 0
        jealousy = 0
        admiration = 0
        trust = 0
        if "romantic" in values:
            romantic_love = amount
            if amount > 0:
                positive = True
        if "platonic" in values:
            platonic_like = amount
            if amount > 0:
                positive = True
        if "dislike" in values:
            dislike = amount
            if amount < 0:
                positive = True
        if "comfort" in values:
            comfortable = amount
            if amount > 0:
                positive = True
        if "jealous" in values:
            jealousy = amount
            if amount < 0:
                positive = True
        if "trust" in values:
            trust = amount
            if amount > 0:
                positive = True
        if "respect" in values:
            admiration = amount
            if amount > 0:
                positive = True

        if positive:
            effect = i18n.t("relationships.positive_postscript")
        else:
            effect = i18n.t("relationships.negative_postscript")

        # Get log
        log1 = None
        log2 = None
        if block.get("log"):
            log = block.get("log")
            if isinstance(log, str):
                log1 = log
            elif isinstance(log, list):
                if len(log) >= 2:
                    log1 = log[0]
                    log2 = log[1]
                elif len(log) == 1:
                    log1 = log[0]
            else:
                print(f"something is wrong with relationship log: {log}")

        if not log1:
            if hasattr(event, "text"):
                try:
                    log1 = event.text + effect
                except AttributeError:
                    print(
                        f"WARNING: event changed relationships but did not create a relationship log"
                    )
            else:
                log1 = i18n.t("defaults.relationship_log") + effect
        if not log2:
            if hasattr(event, "text"):
                try:
                    log2 = event.text + effect
                except AttributeError:
                    print(
                        f"WARNING: event changed relationships but did not create a relationship log"
                    )
            else:
                log2 = i18n.t("defaults.relationship_log") + effect

        change_relationship_values(
            cats_to_ob,
            cats_from_ob,
            romantic_love,
            platonic_like,
            dislike,
            admiration,
            comfortable,
            jealousy,
            trust,
            log=log1,
        )

        if block.get("mutual"):
            change_relationship_values(
                cats_from_ob,
                cats_to_ob,
                romantic_love,
                platonic_like,
                dislike,
                admiration,
                comfortable,
                jealousy,
                trust,
                log=log2,
            )


def change_relationship_values(
        cats_to: list,
        cats_from: list,
        romantic_love: int = 0,
        platonic_like: int = 0,
        dislike: int = 0,
        admiration: int = 0,
        comfortable: int = 0,
        jealousy: int = 0,
        trust: int = 0,
        auto_romance: bool = False,
        log: str = None,
):
    """
    changes relationship values according to the parameters.

    :param list[Cat] cats_from: list of cat objects whose rel values will be affected
    (e.g. cat_from loses trust in cat_to)
    :param list[Cat] cats_to: list of cats objects who are the target of that rel value
    (e.g. cat_from loses trust in cat_to)
    :param int romantic_love: amount to change romantic, default 0
    :param int platonic_like: amount to change platonic, default 0
    :param int dislike: amount to change dislike, default 0
    :param int admiration: amount to change admiration (respect), default 0
    :param int comfortable: amount to change comfort, default 0
    :param int jealousy: amount to change jealousy, default 0
    :param int trust: amount to change trust, default 0
    :param bool auto_romance: if the cat_from already has romantic value with cat_to, then the platonic_like param value
    will also be applied to romantic, default False
    :param str log: the string to append to the relationship log of cats involved
    """

    # This is just for test prints - DON'T DELETE - you can use this to test if relationships are changing
    """changed = False
    if romantic_love == 0 and platonic_like == 0 and dislike == 0 and admiration == 0 and \
            comfortable == 0 and jealousy == 0 and trust == 0:
        changed = False
    else:
        changed = True"""

    # pick out the correct cats
    for single_cat_from in cats_from:
        for single_cat_to in cats_to:
            # make sure we aren't trying to change a cat's relationship with themself
            if single_cat_from == single_cat_to:
                continue

            # if the cats don't know each other, start a new relationship
            if single_cat_to.ID not in single_cat_from.relationships:
                single_cat_from.create_one_relationship(single_cat_to)

            rel = single_cat_from.relationships[single_cat_to.ID]

            # here we just double-check that the cats are allowed to be romantic with each other
            if (
                    single_cat_from.is_potential_mate(single_cat_to, for_love_interest=True)
                    or single_cat_to.ID in single_cat_from.mate
            ):
                # if cat already has romantic feelings then automatically increase romantic feelings
                # when platonic feelings would increase
                if rel.romantic_love > 0 and auto_romance:
                    romantic_love = platonic_like

                # now gain the romance
                rel.romantic_love += romantic_love

            # gain other rel values
            rel.platonic_like += platonic_like
            rel.dislike += dislike
            rel.admiration += admiration
            rel.comfortable += comfortable
            rel.jealousy += jealousy
            rel.trust += trust

            # for testing purposes - DON'T DELETE - you can use this to test if relationships are changing
            """
            print(str(single_cat_from.name) + " gained relationship with " + str(rel.cat_to.name) + ": " +
                  "Romantic: " + str(romantic_love) +
                  " /Platonic: " + str(platonic_like) +
                  " /Dislike: " + str(dislike) +
                  " /Respect: " + str(admiration) +
                  " /Comfort: " + str(comfortable) +
                  " /Jealousy: " + str(jealousy) +
                  " /Trust: " + str(trust)) if changed else print("No relationship change")"""

            if log and isinstance(log, str):
                log_text = log + i18n.t(
                    "relationships.age_postscript",
                    name=str(single_cat_to.name),
                    count=single_cat_to.moons,
                )
                if log_text not in rel.log:
                    rel.log.append(log_text)


# ---------------------------------------------------------------------------- #
#                               Text Adjust                                    #
# ---------------------------------------------------------------------------- #


def get_leader_life_notice(clan) -> str:
    """
    Returns a string specifying how many lives the leader has left or notifying of the leader's full death
    """
    if game.clan.instructor.df:
        return i18n.t("cat.history.leader_lives_left_df", count=clan.leader_lives)
    return i18n.t("cat.history.leader_lives_left_sc", count=clan.leader_lives)


def get_other_clan_relation(relation):
    """
    converts int value into string relation and returns string: "hostile", "neutral", or "ally"
    :param relation: the other_clan.relations value
    """

    if int(relation) >= 17:
        return "ally"
    elif 7 < int(relation) < 17:
        return "neutral"
    elif int(relation) <= 7:
        return "hostile"


def pronoun_repl(m, cat_pronouns_dict, raise_exception=False):
    """Helper function for add_pronouns. If raise_exception is
    False, any error in pronoun formatting will not raise an
    exception, and will use a simple replacement "error" """

    # Add protection about the "insert" sometimes used
    if m.group(0) in ["{insert}", "{surrogate}"]:
        return m.group(0)

    inner_details = m.group(1).split("/")
    out = None

    try:
        if inner_details[1].upper() == "PLURAL":
            inner_details.pop(1)  # remove plural tag so it can be processed as normal
            catlist = []
            for cat in inner_details[1].split("+"):
                try:
                    catlist.append(cat_pronouns_dict[cat][1])
                except KeyError:
                    print(f"Missing pronouns for {cat}")
                    continue
            d = determine_plural_pronouns(catlist)
        else:
            try:
                d = cat_pronouns_dict[inner_details[1]][1]
            except KeyError:
                if inner_details[0].upper() == "ADJ":
                    # find the default - this is a semi-expected behaviour for the adj tag as it may be called when
                    # there is no relevant cat
                    return inner_details[localization.get_default_adj()]
                else:
                    logger.warning(
                        f"Could not get pronouns for {inner_details[1]}. Using default."
                    )
                    print(
                        f"Could not get pronouns for {inner_details[1]}. Using default."
                    )
                    d = choice(localization.get_new_pronouns("default"))

        if inner_details[0].upper() == "PRONOUN":
            out = d[inner_details[2]]
        elif inner_details[0].upper() == "VERB":
            out = inner_details[d["conju"] + 1]
        elif inner_details[0].upper() == "ADJ":
            out = inner_details[(d["gender"] + 2) if "gender" in d else 2]

        if out is not None:
            if inner_details[-1] == "CAP":
                out = out.capitalize()
            return out

        if raise_exception:
            raise KeyError(
                f"Pronoun tag: {m.group(1)} is not properly"
                "indicated as a PRONOUN or VERB tag."
            )

        print("Failed to find pronoun:", m.group(1))
        return "error1"
    except (KeyError, IndexError) as e:
        if raise_exception:
            raise

        logger.exception("Failed to find pronoun: " + m.group(1))
        print("Failed to find pronoun:", m.group(1))
        return "error2"


def name_repl(m, cat_dict):
    """Name replacement"""
    return cat_dict[m.group(0)][0]


def process_text(text, cat_dict, raise_exception=False):
    """Add the correct name and pronouns into a string."""
    adjust_text = re.sub(
        r"(?<!%)\{(.*?)}", lambda x: pronoun_repl(x, cat_dict, raise_exception), text
    )

    name_patterns = [r"(?<!\{)" + re.escape(l) + r"(?!\})" for l in cat_dict]
    adjust_text = re.sub(
        "|".join(name_patterns), lambda x: name_repl(x, cat_dict), adjust_text
    )

    adjust_text.replace("medicine cat", "healer").replace("medicine den", "healer den")

    return adjust_text


def adjust_list_text(list_of_items: List) -> str:
    """
    returns the list in correct grammar format (i.e. item1, item2, item3 and item4)
    this works with any number of items
    :param list_of_items: the list of items you want converted
    :return: the new string
    """

    if not isinstance(list_of_items, list):
        logger.warning("non-list object was passed to adjust_list_text")
        list_of_items = list(list_of_items)

    if len(list_of_items) == 0:
        item1 = ""
        item2 = ""
    elif len(list_of_items) == 1:
        item1 = list_of_items[0]
        item2 = ""
    elif len(list_of_items) == 2:
        item1 = list_of_items[0]
        item2 = list_of_items[1]
    else:
        item1 = ", ".join(list_of_items[:-1])
        if get_lang_config().get("oxford_comma"):
            item1 += ","
        item2 = list_of_items[-1]

    return i18n.t("utility.items", count=len(list_of_items), item1=item1, item2=item2)


def adjust_prey_abbr(patrol_text):
    """
    checks for prey abbreviations and returns adjusted text
    """
    global PREY_LISTS
    if langs["prey"] != i18n.config.get("locale"):
        langs["prey"] = i18n.config.get("locale")
        PREY_LISTS = load_lang_resource("patrols/prey_text_replacements.json")

    for abbr in PREY_LISTS["abbreviations"]:
        if abbr in patrol_text:
            chosen_list = PREY_LISTS["abbreviations"].get(abbr)
            chosen_list = PREY_LISTS[chosen_list]
            prey = choice(chosen_list)
            patrol_text = patrol_text.replace(abbr, prey)

    return patrol_text


def get_special_snippet_list(
        chosen_list, amount, sense_groups=None, return_string=True
):
    """
    function to grab items from various lists in snippet_collections.json
    list options are:
    -prophecy_list - sense_groups = sight, sound, smell, emotional, touch
    -omen_list - sense_groups = sight, sound, smell, emotional, touch
    -clair_list  - sense_groups = sound, smell, emotional, touch, taste
    -dream_list (this list doesn't have sense_groups)
    -story_list (this list doesn't have sense_groups)
    :param chosen_list: pick which list you want to grab from
    :param amount: the amount of items you want the returned list to contain
    :param sense_groups: list which senses you want the snippets to correspond with:
     "touch", "sight", "emotional", "sound", "smell" are the options. Default is None, if left as this then all senses
     will be included (if the list doesn't have sense categories, then leave as None)
    :param return_string: if True then the function will format the snippet list with appropriate commas and 'ands'.
    This will work with any number of items. If set to True, then the function will return a string instead of a list.
    (i.e. ["hate", "fear", "dread"] becomes "hate, fear, and dread") - Default is True
    :return: a list of the chosen items from chosen_list or a formatted string if format is True
    """
    biome = game.clan.biome.casefold()
    global SNIPPETS
    if langs["snippet"] != i18n.config.get("locale"):
        langs["snippet"] = i18n.config.get("locale")
        SNIPPETS = load_lang_resource("snippet_collections.json")

    # these lists don't get sense specific snippets, so is handled first
    if chosen_list in ["dream_list", "story_list"]:
        if (
                chosen_list == "story_list"
        ):  # story list has some biome specific things to collect
            snippets = SNIPPETS[chosen_list]["general"]
            snippets.extend(SNIPPETS[chosen_list][biome])
        elif (
                chosen_list == "clair_list"
        ):  # the clair list also pulls from the dream list
            snippets = SNIPPETS[chosen_list]
            snippets.extend(SNIPPETS["dream_list"])
        else:  # the dream list just gets the one
            snippets = SNIPPETS[chosen_list]

    else:
        # if no sense groups were specified, use all of them
        if not sense_groups:
            if chosen_list == "clair_list":
                sense_groups = ["taste", "sound", "smell", "emotional", "touch"]
            else:
                sense_groups = ["sight", "sound", "smell", "emotional", "touch"]

        # find the correct lists and compile them
        snippets = []
        for sense in sense_groups:
            snippet_group = SNIPPETS[chosen_list][sense]
            snippets.extend(snippet_group["general"])
            snippets.extend(snippet_group[biome])

    # now choose a unique snippet from each snip list
    unique_snippets = []
    for snip_list in snippets:
        unique_snippets.append(choice(snip_list))

    # pick out our final snippets
    final_snippets = sample(unique_snippets, k=amount)

    if return_string:
        text = adjust_list_text(final_snippets)
        return text
    else:
        return final_snippets


def find_special_list_types(text):
    """
    purely to identify which senses are being called for by a snippet abbreviation
    returns adjusted text, sense list, list type, and cat_tag
    """
    senses = []
    list_text = None
    list_type = None
    words = text.split(" ")
    for bit in words:
        if "_list" in bit:
            list_text = bit
            # just getting rid of pesky punctuation
            list_text = list_text.replace(".", "")
            list_text = list_text.replace(",", "")
            break

    if not list_text:
        return text, None, None, None

    parts_of_tag = list_text.split("/")

    try:
        cat_tag = parts_of_tag[1]
    except IndexError:
        cat_tag = None

    if "omen_list" in list_text:
        list_type = "omen_list"
    elif "prophecy_list" in list_text:
        list_type = "prophecy_list"
    elif "dream_list" in list_text:
        list_type = "dream_list"
    elif "clair_list" in list_text:
        list_type = "clair_list"
    elif "story_list" in list_text:
        list_type = "story_list"
    else:
        logger.error("WARNING: no list type found for %s", list_text)
        return text, None, None, None

    if "_sight" in list_text:
        senses.append("sight")
    if "_sound" in list_text:
        senses.append("sound")
    if "_smell" in list_text:
        senses.append("smell")
    if "_emotional" in list_text:
        senses.append("emotional")
    if "_touch" in list_text:
        senses.append("touch")
    if "_taste" in list_text:
        senses.append("taste")

    text = text.replace(list_text, list_type)

    return text, senses, list_type, cat_tag


def history_text_adjust(text, other_clan_name, clan, other_cat_rc=None):
    """
    we want to handle history text on its own because it needs to preserve the pronoun tags and cat abbreviations.
    this is so that future pronoun changes or name changes will continue to be reflected in history
    """
    vowels = ["A", "E", "I", "O", "U"]

    if "o_c_n" in text:
        pos = 0
        for x in range(text.count("o_c_n")):
            if "o_c_n" in text:
                for y in vowels:
                    if str(other_clan_name).startswith(y):
                        modify = text.split()
                        if "o_c_n" in modify:
                            pos = modify.index("o_c_n")
                        if "o_c_n's" in modify:
                            pos = modify.index("o_c_n's")
                        if "o_c_n." in modify:
                            pos = modify.index("o_c_n.")
                        if modify[pos - 1] == "a":
                            modify.remove("a")
                            modify.insert(pos - 1, "an")
                        text = " ".join(modify)
                        break

        text = text.replace("o_c_n", str(other_clan_name))

    if "c_n" in text:
        text = text.replace("c_n", clan.name)
    if "r_c" in text and other_cat_rc:
        text = selective_replace(text, "r_c", str(other_cat_rc.name))
    return text


def selective_replace(text, pattern, replacement):
    i = 0
    while i < len(text):
        index = text.find(pattern, i)
        if index == -1:
            break
        start_brace = text.rfind("{", 0, index)
        end_brace = text.find("}", index)
        if start_brace != -1 and end_brace != -1 and start_brace < index < end_brace:
            i = index + len(pattern)
        else:
            text = text[:index] + replacement + text[index + len(pattern):]
            i = index + len(replacement)

    return text


def ongoing_event_text_adjust(Cat, text, clan=None, other_clan_name=None):
    """
    This function is for adjusting the text of ongoing events
    :param Cat: the cat class
    :param text: the text to be adjusted
    :param clan: the name of the clan
    :param other_clan_name: the other Clan's name if another Clan is involved
    """
    cat_dict = {}
    if "lead_name" in text:
        kitty = Cat.fetch_cat(game.clan.leader)
        cat_dict["lead_name"] = (str(kitty.name), choice(kitty.pronouns))
    if "dep_name" in text:
        kitty = Cat.fetch_cat(game.clan.deputy)
        cat_dict["dep_name"] = (str(kitty.name), choice(kitty.pronouns))
    if "med_name" in text:
        kitty = choice(get_alive_status_cats(Cat, ["healer"], working=True))
        cat_dict["med_name"] = (str(kitty.name), choice(kitty.pronouns))

    if cat_dict:
        text = process_text(text, cat_dict)

    if other_clan_name:
        text = text.replace("o_c_n", other_clan_name)
    if clan:
        clan_name = str(clan.name)
    else:
        if game.clan is None:
            clan_name = game.switches["clan_list"][0]
        else:
            clan_name = str(game.clan.name)

    text = text.replace("c_n", clan_name + "Clan")

    return text


def event_text_adjust(
        Cat: Type["Cat"],
        text,
        *,
        patrol_leader=None,
        main_cat=None,
        random_cat=None,
        stat_cat=None,
        victim_cat=None,
        patrol_cats: list = None,
        patrol_apprentices: list = None,
        new_cats: list = None,
        multi_cats: list = None,
        clan=None,
        other_clan=None,
        chosen_herb: str = None,
):
    """
    handles finding abbreviations in the text and replacing them appropriately, returns the adjusted text
    :param Cat Cat: always pass the Cat class
    :param str text: the text being adjusted
    :param Cat patrol_leader: Cat object for patrol_leader (p_l), if present
    :param Cat main_cat: Cat object for main_cat (m_c), if present
    :param Cat random_cat: Cat object for random_cat (r_c), if present
    :param Cat stat_cat: Cat object for stat_cat (s_c), if present
    :param Cat victim_cat: Cat object for victim_cat (mur_c), if present
    :param list[Cat] patrol_cats: List of Cat objects for cats in patrol, if present
    :param list[Cat] patrol_apprentices: List of Cat objects for patrol_apprentices (app#), if present
    :param list[Cat] new_cats: List of Cat objects for new_cats (n_c:index), if present
    :param list[Cat] multi_cats: List of Cat objects for multi_cat (multi_cat), if present
    :param Clan clan: pass game.clan
    :param OtherClan other_clan: OtherClan object for other_clan (o_c_n), if present
    :param str chosen_herb: string of chosen_herb (chosen_herb), if present
    """
    from scripts.clan import OtherClan
    vowels = ["A", "E", "I", "O", "U"]

    if not text:
        text = "This should not appear, report as a bug please! Tried to adjust the text, but no text was provided."
        print("WARNING: Tried to adjust text, but no text was provided.")

    # this check is really just here to catch odd bug edge-cases from old saves, specifically in death history
    # otherwise we should really *never* have lists being passed as the text
    if isinstance(text, list):
        text = text[0]

    if isinstance(clan, str):
        if "Clan" not in clan and game.clan:
            clan = game.clan if clan in [" ", game.clan.name, "outsider cat"] else [c for c in game.clan.all_clans if c.name == clan][0]
        elif clan == main_cat.group:
            clan = OtherClan(clan)

    replace_dict = {}

    # special lists - this needs to happen first for pronoun tag reasons
    text, senses, list_type, cat_tag = find_special_list_types(text)
    if list_type:
        sign_list = get_special_snippet_list(
            list_type, amount=randint(1, 3), sense_groups=senses
        )
        text = text.replace(list_type, str(sign_list))
        if cat_tag:
            text = text.replace("cat_tag", cat_tag)

    # main_cat
    if "m_c" in text:
        if main_cat:
            replace_dict["m_c"] = (str(main_cat.name), choice(main_cat.pronouns))

    # patrol_lead
    if "p_l" in text:
        if patrol_leader:
            replace_dict["p_l"] = (
                str(patrol_leader.name),
                choice(patrol_leader.pronouns),
            )

    # random_cat
    if "r_c" in text:
        if random_cat:
            replace_dict["r_c"] = (str(random_cat.name), get_pronouns(random_cat))

    # stat cat
    if "s_c" in text:
        if stat_cat:
            replace_dict["s_c"] = (str(stat_cat.name), get_pronouns(stat_cat))

    # other_cats
    if patrol_cats:
        other_cats = [
            i
            for i in patrol_cats
            if i not in [patrol_leader, random_cat, patrol_apprentices]
        ]
        other_cat_abbr = ["o_c1", "o_c2", "o_c3", "o_c4"]
        for i, abbr in enumerate(other_cat_abbr):
            if abbr not in text:
                continue
            if len(other_cats) > i:
                replace_dict[abbr] = (
                    str(other_cats[i].name),
                    choice(other_cats[i].pronouns),
                )

    # patrol_apprentices
    app_abbr = ["app1", "app2", "app3", "app4", "app5", "app6"]
    for i, abbr in enumerate(app_abbr):
        if abbr not in text:
            continue
        if len(patrol_apprentices) > i:
            replace_dict[abbr] = (
                str(patrol_apprentices[i].name),
                choice(patrol_apprentices[i].pronouns),
            )

    # new_cats (include pre version)
    if "n_c" in text and new_cats:
        for i, cat_list in enumerate(new_cats):
            if len(new_cats) > 1:
                pronoun = localization.get_new_pronouns("default plural")[0]
            else:
                pronoun = choice(cat_list[0].pronouns)

            replace_dict[f"n_c:{i}"] = (str(cat_list[0].name), pronoun)
            replace_dict[f"n_c_pre:{i}"] = (str(cat_list[0].name.prefix), pronoun)

    # mur_c (murdered cat for reveals)
    if "mur_c" in text:
        replace_dict["mur_c"] = (str(victim_cat.name), get_pronouns(victim_cat))

    # lead_name
    if "lead_name" in text:
        leader = Cat.fetch_cat(clan.leader if clan else game.clan.leader)
        replace_dict["lead_name"] = (str(leader.name), choice(leader.pronouns))

    # dep_name
    if "dep_name" in text:
        deputy = Cat.fetch_cat(clan.deputy if clan else game.clan.deputy)
        replace_dict["dep_name"] = (str(deputy.name), choice(deputy.pronouns))

    # med_name
    if "med_name" in text:
        med = choice(get_alive_status_cats(Cat, ["healer", "healer apprentice"], clan=clan.name if clan else game.clan.name))
        replace_dict["med_name"] = (str(med.name), choice(med.pronouns))

    # assign all names and pronouns
    if replace_dict:
        text = process_text(text, replace_dict)

    # multi_cat
    if "multi_cat" in text:
        name_list = []
        for _cat in multi_cats:
            name_list.append(str(_cat.name))
        list_text = adjust_list_text(name_list)
        text = text.replace("multi_cat", list_text)

    # other_clan_name
    if "o_c_n" in text:
        other_clan_name = other_clan.name
        pos = 0
        for x in range(text.count("o_c_n")):
            if "o_c_n" in text:
                for y in vowels:
                    if str(other_clan_name).startswith(y):
                        modify = text.split()
                        if "o_c_n" in modify:
                            pos = modify.index("o_c_n")
                        if "o_c_n's" in modify:
                            pos = modify.index("o_c_n's")
                        if "o_c_n." in modify:
                            pos = modify.index("o_c_n.")
                        if modify[pos - 1] == "a":
                            modify.remove("a")
                            modify.insert(pos - 1, "an")
                        text = " ".join(modify)
                        break

        text = text.replace("o_c_n", str(other_clan_name) + "Clan")

    # clan_name
    if "c_n" in text:
        try:
            clan_name = clan.name
        except AttributeError:
            clan_name = game.switches["clan_list"][0]

        pos = 0
        for x in range(text.count("c_n")):
            if "c_n" in text:
                for y in vowels:
                    if str(clan_name).startswith(y):
                        modify = text.split()
                        if "c_n" in modify:
                            pos = modify.index("c_n")
                        if "c_n's" in modify:
                            pos = modify.index("c_n's")
                        if "c_n." in modify:
                            pos = modify.index("c_n.")
                        if modify[pos - 1] == "a":
                            modify.remove("a")
                            modify.insert(pos - 1, "an")
                        text = " ".join(modify)
                        break

        text = text.replace("c_n", str(clan_name) + "Clan")

    # prey lists
    text = adjust_prey_abbr(text)

    # acc_plural (only works for main_cat's acc)
    if "acc_plural" in text:
        text = text.replace(
            "acc_plural", i18n.t(f"cat.accessories.{main_cat.pelt.accessory[-1]}", count=2)
        )

    # acc_singular (only works for main_cat's acc)
    if "acc_singular" in text:
        text = text.replace(
            "acc_singular",
            i18n.t(f"cat.accessories.{main_cat.pelt.accessory[-1]}", count=1),
        )

    if "given_herb" in text:
        text = text.replace(
            "given_herb", i18n.t(f"conditions.herbs.{chosen_herb}", count=2)
        )

    return text


def leader_ceremony_text_adjust(
        Cat,
        text,
        leader,
        life_giver=None,
        virtue=None,
        extra_lives=None
):
    """
    used to adjust the text for leader ceremonies
    """
    replace_dict = {
        "m_c_star": (str(leader.name.prefix + "star"), choice(leader.pronouns)),
        "m_c": (str(leader.name.prefix + leader.name.suffix), choice(leader.pronouns)),
    }

    if life_giver:
        replace_dict["r_c"] = (
            str(Cat.fetch_cat(life_giver).name),
            choice(Cat.fetch_cat(life_giver).pronouns),
        )

    text = process_text(text, replace_dict)

    if virtue:
        virtue = process_text(virtue, replace_dict)
        text = text.replace("[virtue]", virtue)

    if extra_lives:
        text = text.replace("[life_num]", str(extra_lives))

    text = text.replace("c_n", str(leader.group.name) + "Clan")

    return text


def ceremony_text_adjust(
        Cat,
        text,
        cat,
        old_name=None,
        dead_mentor=None,
        mentor=None,
        previous_alive_mentor=None,
        random_honor=None,
        living_parents=(),
        dead_parents=(),
        clan=game.clan
):
    clanname = str(clan.name + "Clan")

    random_honor = random_honor
    random_living_parent = None
    random_dead_parent = None

    adjust_text = text

    cat_dict = {
        "m_c": (
            (str(cat.name), choice(cat.pronouns)) if cat else ("cat_placeholder", None)
        ),
        "(mentor)": (
            (str(mentor.name), choice(mentor.pronouns))
            if mentor
            else ("mentor_placeholder", None)
        ),
        "(deadmentor)": (
            (str(dead_mentor.name), get_pronouns(dead_mentor))
            if dead_mentor
            else ("dead_mentor_name", None)
        ),
        "(previous_mentor)": (
            (str(previous_alive_mentor.name), choice(previous_alive_mentor.pronouns))
            if previous_alive_mentor
            else ("previous_mentor_name", None)
        ),
        "l_n": (
            (str(clan.leader.name), choice(clan.leader.pronouns))
            if clan.leader
            else ("leader_name", None)
        ),
        "c_n": (clanname, None),
    }

    if old_name:
        cat_dict["(old_name)"] = (old_name, None)

    if random_honor:
        cat_dict["r_h"] = (random_honor, None)

    if "p1" in adjust_text and "p2" in adjust_text and len(living_parents) >= 2:
        cat_dict["p1"] = (
            str(living_parents[0].name),
            choice(living_parents[0].pronouns),
        )
        cat_dict["p2"] = (
            str(living_parents[1].name),
            choice(living_parents[1].pronouns),
        )
    elif living_parents:
        random_living_parent = choice(living_parents)
        cat_dict["p1"] = (
            str(random_living_parent.name),
            choice(random_living_parent.pronouns),
        )
        cat_dict["p2"] = (
            str(random_living_parent.name),
            choice(random_living_parent.pronouns),
        )

    if (
            "dead_par1" in adjust_text
            and "dead_par2" in adjust_text
            and len(dead_parents) >= 2
    ):
        cat_dict["dead_par1"] = (
            str(dead_parents[0].name),
            get_pronouns(dead_parents[0]),
        )
        cat_dict["dead_par2"] = (
            str(dead_parents[1].name),
            get_pronouns(dead_parents[1]),
        )
    elif dead_parents:
        random_dead_parent = choice(dead_parents)
        cat_dict["dead_par1"] = (
            str(random_dead_parent.name),
            get_pronouns(random_dead_parent),
        )
        cat_dict["dead_par2"] = (
            str(random_dead_parent.name),
            get_pronouns(random_dead_parent),
        )

    adjust_text = process_text(adjust_text, cat_dict)

    return adjust_text, random_living_parent, random_dead_parent


def get_pronouns(cat: "Cat"):
    """Get a cat's pronoun even if the cat has faded to prevent crashes (use gender-neutral pronouns when the cat has faded)"""
    if not cat.pronouns:
        # since get_new_pronouns returns a list with length 1
        return localization.get_new_pronouns("default")[0]
    else:
        return choice(cat.pronouns)


def shorten_text_to_fit(
        name, length_limit, font_size=None, font_type="resources/fonts/NotoSans-Medium.ttf"
):
    length_limit = length_limit * scripts.game_structure.screen_settings.screen_scale
    if font_size is None:
        font_size = 15
    font_size = floor(font_size * scripts.game_structure.screen_settings.screen_scale)

    if font_type == "clangen":
        font_type = "resources/fonts/clangen.ttf"
    # Create the font object
    font = pygame.font.Font(font_type, font_size)

    # Add dynamic name lengths by checking the actual width of the text
    total_width = 0
    short_name = ""
    ellipsis_width = font.size("...")[0]
    for index, character in enumerate(name):
        char_width = font.size(character)[0]

        # Check if the current character is the last one and its width is less than or equal to ellipsis_width
        if index == len(name) - 1 and char_width <= ellipsis_width:
            short_name += character
        else:
            total_width += char_width
            if total_width + ellipsis_width > length_limit:
                break
            short_name += character

    # If the name was truncated, add "..."
    if len(short_name) < len(name):
        short_name += "..."

    return short_name


# ---------------------------------------------------------------------------- #
#                                    Sprites                                   #
# ---------------------------------------------------------------------------- #


def ui_scale(rect: pygame.Rect):
    """
    Scales a pygame.Rect appropriately for the UI scaling currently in use.
    :param rect: a pygame.Rect
    :return: the same pygame.Rect, scaled for the current UI.
    """
    # offset can be negative to allow for correct anchoring
    rect[0] = floor(rect[0] * scripts.game_structure.screen_settings.screen_scale)
    rect[1] = floor(rect[1] * scripts.game_structure.screen_settings.screen_scale)
    # if the dimensions are negative, it's dynamically scaled, ignore
    rect[2] = (
        floor(rect[2] * scripts.game_structure.screen_settings.screen_scale)
        if rect[2] > 0
        else rect[2]
    )
    rect[3] = (
        floor(rect[3] * scripts.game_structure.screen_settings.screen_scale)
        if rect[3] > 0
        else rect[3]
    )

    return rect


def ui_scale_dimensions(dim: Tuple[int, int]):
    """
    Use to scale the dimensions of an item - WILL IGNORE NEGATIVE VALUES
    :param dim: The dimensions to scale
    :return: The scaled dimensions
    """
    return (
        floor(dim[0] * scripts.game_structure.screen_settings.screen_scale)
        if dim[0] > 0
        else dim[0],
        floor(dim[1] * scripts.game_structure.screen_settings.screen_scale)
        if dim[1] > 0
        else dim[1],
    )


def ui_scale_offset(coords: Tuple[int, int]):
    """
    Use to scale the offset of an item (i.e. the first 2 values of a pygame.Rect).
    Not to be confused with ui_scale_blit.
    :param coords: The coordinates to scale
    :return: The scaled coordinates
    """
    return (
        floor(coords[0] * scripts.game_structure.screen_settings.screen_scale),
        floor(coords[1] * scripts.game_structure.screen_settings.screen_scale),
    )


def ui_scale_value(val: int):
    """
    Use to scale a single value according to the UI scale. If you need this one,
    you're probably doing something unusual. Try to avoid where possible.
    :param val: The value to scale
    :return: The scaled value
    """
    return floor(val * scripts.game_structure.screen_settings.screen_scale)


def ui_scale_blit(coords: Tuple[int, int]):
    """
    Use to scale WHERE to blit an item, not the SIZE of it. (0, 0) is the top left corner of the pygame_gui managed window,
    this adds the offset from fullscreen etc. to make it blit in the right place. Not to be confused with ui_scale_offset.
    :param coords: The coordinates to blit to
    :return: The scaled, correctly offset coordinates to blit to.
    """
    return floor(
        coords[0] * scripts.game_structure.screen_settings.screen_scale
        + scripts.game_structure.screen_settings.offset[0]
    ), floor(
        coords[1] * scripts.game_structure.screen_settings.screen_scale
        + scripts.game_structure.screen_settings.offset[1]
    )


def update_sprite(cat):
    # First, check if the cat is faded.
    if cat.faded:
        # Don't update the sprite if the cat is faded.
        return

    # apply
    cat.sprite = generate_sprite(cat)
    # update class dictionary
    cat.all_cats[cat.ID] = cat


def clan_symbol_sprite(clan, return_string=False, force_light=False):
    """
    returns the clan symbol for the given clan_name, if no symbol exists then random symbol is chosen
    :param clan: the clan object
    :param return_string: default False, set True if the sprite name string is required rather than the sprite image
    :param force_light: Set true if you want this sprite to override the dark/light mode changes with the light sprite
    """
    if not clan.chosen_symbol:
        possible_sprites = []
        for sprite in sprites.clan_symbols:
            name = sprite.strip("1234567890")
            if f"symbol{clan.name.upper()}" == name:
                possible_sprites.append(sprite)
        if possible_sprites:
            clan.chosen_symbol = choice(possible_sprites)
        else:
            # give random symbol if no matching symbol exists
            print(
                f"WARNING: attempted to return symbol, but there's no clan symbol for {clan.name.upper()}. "
                f"Random chosen."
            )
            clan.chosen_symbol = choice(sprites.clan_symbols)

    if return_string:
        return clan.chosen_symbol
    else:
        return sprites.get_symbol(clan.chosen_symbol, force_light=force_light)


def generate_sprite(
        cat,
        life_state=None,
        scars_hidden=False,
        acc_hidden=False,
        always_living=False,
        no_not_working=False,
) -> pygame.Surface:
    """
    Generates the sprite for a cat, with optional arguments that will override certain things.

    :param life_state: sets the age life_stage of the cat, overriding the one set by its age. Set to string.
    :param scars_hidden: If True, doesn't display the cat's scars. If False, display cat scars.
    :param acc_hidden: If True, hide the accessory. If false, show the accessory.
    :param always_living: If True, always show the cat with living lineart
    :param no_not_working: If true, never use the not_working lineart.
                    If false, use the cat.not_working() to determine the no_working art.
    """

    if life_state is not None:
        age = life_state
    else:
        if game.settings["ageup dead"] and cat.dead and cat.age in ["newborn", "kitten", "adolescent"]:
            age = "adult"
        else:
            age = cat.age.value


    if always_living:
        dead = False
    else:
        dead = cat.dead

    # setting the cat_sprite (bc this makes things much easier)
    if (
            not no_not_working
            and cat.not_working()
            and age != "newborn"
            and game.config["cat_sprites"]["sick_sprites"]
    ):
        if age in ["kitten", "adolescent"]:
            cat_sprite = str(19)
        else:
            cat_sprite = str(18)
    elif cat.pelt.paralyzed and age != "newborn":
        if age in ["kitten", "adolescent"]:
            cat_sprite = str(17)
        else:
            if cat.pelt.length == 'long' or (cat.pelt.length == 'medium' and get_current_season() == 'Leaf-bare'):
                cat_sprite = str(16)
            else:
                cat_sprite = str(15)
    else:
        if age == "elder" and not game.config["fun"]["all_cats_are_newborn"]:
            age = "senior"

        if game.config["fun"]["all_cats_are_newborn"]:
            cat_sprite = str(cat.pelt.cat_sprites["newborn"])
        else:
            if cat.pelt.cat_sprites[age] < 9 and cat.pelt.cat_sprites[age] > 5 and (cat.pelt.length == 'medium' and get_current_season() == 'Leaf-bare'):
                cat_sprite = str(cat.pelt.cat_sprites[age]+3)
            else:
                cat_sprite = str(cat.pelt.cat_sprites[age])

    new_sprite = pygame.Surface(
        (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA
    )

    def draw_sprite(phenotype, cat_sprite, somatic = False):

        new_sprite = pygame.Surface(
            (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA
        )

        vitiligo = ['MOON', 'PHANTOM', 'POWDER', 'BLEACHED', 'VITILIGO', 'VITILIGOTWO', 'SMOKEY']
        
        if somatic:
            phenotype[phenotype.somatic["gene"]][0] = phenotype.somatic["allele"]
            phenotype.GeneSort()
            if phenotype.somatic["gene"] == 'sexgene':
                phenotype.sexgene[1] = 'Y'
            phenotype.PhenotypeOutput(phenotype.white_pattern)

        stripecolourdict = {
                'rufousedapricot' : 'lowred',
                'mediumapricot' : 'rufousedcream',
                'lowapricot' : 'mediumcream',

                'rufousedhoney-apricot' : 'lowred',
                'mediumhoney-apricot' : 'rufousedhoney',
                'lowhoney-apricot' : 'mediumhoney',

                'rufousedivory-apricot' : 'lowhoney',
                'mediumivory-apricot' : 'rufousedivory',
                'lowivory-apricot' : 'mediumivory'
            }
        gensprite = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                
        def GenSprite(phenotype, sprite_age, merle=False):
            phenotype.SpriteInfo(sprite_age)
            if(phenotype.merlepattern != None and not merle and 'rev' in phenotype.merlepattern[0]):
                old_silver = phenotype.silver
                phenotype.silver = ['i', 'i']
                phenotype.SpriteInfo(sprite_age)
                phenotype.silver = old_silver
                
            def CreateStripes(stripecolour, whichbase, coloursurface=None, pattern=None, special = None):
                notred = ('red' not in stripecolour and 'cream' not in stripecolour and 'honey' not in stripecolour and 'ivory' not in stripecolour and 'apricot' not in stripecolour)
                stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                
                if not pattern and not special and 'solid' not in whichbase:
                    if('chinchilla' in whichbase):
                        stripebase.blit(sprites.sprites['chinchillashading' + cat_sprite], (0, 0))   
                    elif('shaded' in whichbase):
                        stripebase.blit(sprites.sprites['shadedshading' + cat_sprite], (0, 0))       
                    else:           
                        stripebase.blit(sprites.sprites[phenotype.wbtype + 'shading' + cat_sprite], (0, 0))      

                if pattern:
                    stripebase.blit(sprites.sprites[pattern + cat_sprite], (0, 0))
                elif 'ghost' in phenotype.tabby:
                    ghoststripes = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    ghoststripes.blit(sprites.sprites[phenotype.GetTabbySprite() + cat_sprite], (0, 0))
                    ghoststripes.set_alpha(25)
                    stripebase.blit(ghoststripes, (0, 0))
                    stripebase.blit(sprites.sprites[phenotype.GetTabbySprite(special='ghost') + cat_sprite], (0, 0))
                else:    
                    stripebase.blit(sprites.sprites[phenotype.GetTabbySprite() + cat_sprite], (0, 0))

                charc = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                charc_shading = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                if(phenotype.agouti[0] == "Apb" and notred and hasattr(phenotype, "banding")):
                    charc_shading.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                    modifiers = {
                        "chinchilla" : 2,
                        "shaded" : 3,
                        "high" : 5,
                        "medium" : 6,
                        "low" : 7
                    }
                    opacity = int(25 * (modifiers.get(phenotype.banding, 5) / (1 * (int("silver" in whichbase) + 1))))
                    charc_shading.set_alpha(opacity)
                    charc.blit(charc_shading, (0, 0))
                    charc.blit(sprites.sprites['charcoal' + cat_sprite], (0, 0))
                
                if(phenotype.agouti == ["Apb", "Apb"]):
                    charc.set_alpha(125)
                stripebase.blit(charc, (0, 0))

                if coloursurface:
                    stripebase.blit(coloursurface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                elif 'basecolours' in stripecolour:
                    stripebase.blit(sprites.sprites[stripecolour], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                else:
                    surf = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    surf.blit(sprites.sprites[stripecolourdict.get(stripecolour[:-1], stripecolour[:-1])+stripecolour[-1]], (0, 0))
                    if phenotype.caramel == 'caramel' and not ('red' in stripecolour or 'cream' in stripecolour or 'honey' in stripecolour or 'ivory' in stripecolour or 'apricot' in stripecolour):    
                        surf.blit(sprites.sprites['caramel0'], (0, 0))

                    stripebase.blit(surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
                middle = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                if(phenotype.soktype == "full sokoke" and not pattern and 'agouti' not in phenotype.tabby):
                    middle.blit(stripebase, (0, 0))
                    stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    middle.set_alpha(150)
                    stripebase.blit(middle, (0, 0))
                    middle = CreateStripes(stripecolour, whichbase, coloursurface, pattern=phenotype.GetTabbySprite(special='redbar'))
                    stripebase.blit(middle, (0, 0))
                elif(phenotype.soktype == "mild fading" and not pattern and 'agouti' not in phenotype.tabby):
                    middle.blit(stripebase, (0, 0))
                    stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    middle.set_alpha(204)
                    stripebase.blit(middle, (0, 0))
                    middle = CreateStripes(stripecolour, whichbase, coloursurface, pattern=phenotype.GetTabbySprite(special='redbar'))
                    stripebase.blit(middle, (0, 0))

                # if cat.phenotype.furLength[0] == 'l':
                #     stripebase = pygame.transform.box_blur(stripebase, 1)

                return stripebase

            def TabbyBase(whichcolour, whichbase, cat_unders, special = None):
                is_red = ('red' in whichcolour or 'cream' in whichcolour or 'honey' in whichcolour or 'ivory' in whichcolour or 'apricot' in whichcolour)
                whichmain = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                whichmain.blit(sprites.sprites[whichbase], (0, 0))
                if special !='copper' and sprite_age > 12 and (phenotype.silver[0] == 'I' and phenotype.corin[0] == 'fg' and (get_current_season() == 'Leaf-fall' or get_current_season() == 'Leaf-bare' or 'infertility' in cat.permanent_condition)):
                    sunshine = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    
                    colours = phenotype.FindRed(phenotype, sprite_age, special='low')
                    sunshine = MakeCat(sunshine, colours[0], colours[1], [colours[2], colours[3]], special='copper')

                    sunshine.set_alpha(150)
                    whichmain.blit(sunshine, (0, 0))

                unders = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                unders.blit(sprites.sprites["Tabby_unders" + cat_sprite], (0, 0))
                unders.blit(sprites.sprites[cat_unders[0]], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                unders.set_alpha(int(cat_unders[1] * 2.55))
                whichmain.blit(unders, (0, 0))
                    
                
                if phenotype.caramel == 'caramel' and not is_red:    
                    whichmain.blit(sprites.sprites['caramel0'], (0, 0))
                
                return whichmain
        
            def AddStripes(whichmain, whichcolour, whichbase, coloursurface=None):
                stripebase = pygame.Surface(
                    (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                if ((phenotype.corin[0] != 'N' and phenotype.wbtype == "shaded") or phenotype.wbtype == 'chinchilla'):
                    stripebase = CreateStripes(
                        whichcolour, whichbase, coloursurface=coloursurface)
                    stripebase.set_alpha(100)
                elif (phenotype.wbtype == "shaded" or phenotype.corin[0] != 'N'):
                    stripebase = CreateStripes(
                        phenotype.FindRed(phenotype, sprite_age, special='red')[0], phenotype.FindRed(phenotype, sprite_age, special='red')[1], coloursurface=coloursurface)
                    stripebase.set_alpha(50)
                    whichmain.blit(stripebase, (0, 0))
                    stripebase = CreateStripes(
                        whichcolour, whichbase, coloursurface=coloursurface)
                    stripebase.set_alpha(100)
                    whichmain.blit(stripebase, (0, 0))
                    stripebase = CreateStripes(
                        whichcolour, whichbase, pattern="agouti", coloursurface=coloursurface)
                    stripebase.set_alpha(200)
                elif ('ec' in phenotype.ext and 'Eg' not in phenotype.ext and not ('red' in whichcolour or 'cream' in whichcolour or 'honey' in whichcolour or 'ivory' in whichcolour or 'apricot' in whichcolour)):
                    stripebase = CreateStripes(
                        whichcolour, whichbase, coloursurface=coloursurface)
                    stripebase.set_alpha(200)
                    whichmain.blit(stripebase, (0, 0))
                    stripebase = CreateStripes(
                        whichcolour, whichbase, coloursurface=coloursurface, pattern='agouti')
                else:
                    stripebase.blit(CreateStripes(
                        whichcolour, whichbase, coloursurface=coloursurface), (0, 0))

                whichmain.blit(stripebase, (0, 0))

                return whichmain

            def ApplySmokeEffects(whichmain):
                white = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                white.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                smokeUnders = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                smokeUnders.blit(sprites.sprites["Tabby_unders" + cat_sprite], (0, 0))
                smokeUnders.blit(white, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                smokeUnders.set_alpha(10)
                white.set_alpha(10)
                smokeLayer = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                smokeLayer.blit(white, (0, 0))
                if(phenotype.ext[0] == 'Eg' and phenotype.agouti[0] != 'a'):
                    whichmain.blit(sprites.sprites['grizzle' + cat_sprite], (0, 0))
                if phenotype.ghosting[0] == 'Gh' and not (phenotype.silver[0] == 'I' and cat.pelt.length == 'long'):
                    ghostingbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    ghostingbase.blit(sprites.sprites['ghost' + cat_sprite], (0, 0))
                    if(sprite_age < 4):
                        ghostingbase.set_alpha(150)
                    
                    whichmain.blit(ghostingbase, (0, 0))
                if (phenotype.silver[0] == 'I'):
                    ghostingbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    ghostingbase.blit(sprites.sprites['ghost' + cat_sprite], (0, 0))
                    if cat.pelt.length != 'long':
                        ghostingbase.set_alpha(100)
                    elif phenotype.wbtype == 'low':
                        ghostingbase.set_alpha(150)
                    
                    whichmain.blit(ghostingbase, (0, 0))
                if (phenotype.silver[0] == 'I'):
                    smokeLayer.set_alpha(255)
                    if cat.pelt.length != 'long':
                        smokeLayer.blit(smokeUnders, (0, 0))
                    if phenotype.wbtype == 'low' and cat.pelt.length == 'long':
                        smokeLayer.set_alpha(75)
                    elif phenotype.wbtype == 'low' or cat.pelt.length == 'long':
                        smokeLayer.set_alpha(150)
                    else:
                        smokeLayer.set_alpha(200)
                    whichmain.blit(smokeLayer, (0, 0))
                if('smoke' in phenotype.silvergold and 14 > phenotype.wbsum > 9):
                    smokeLayer.set_alpha(255)
                    if cat.pelt.length != 'long':
                        smokeLayer.blit(smokeUnders, (0, 0))
                    if phenotype.wbtype == 'high':
                        smokeLayer.set_alpha(100)
                    elif cat.pelt.length == 'long':
                        smokeLayer.set_alpha(200)                    
                    whichmain.blit(smokeLayer, (0, 0))
                
                return whichmain

            def AddPads(sprite, whichcolour, is_red=False, override=None):
                pads = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                pads.blit(sprites.sprites['pads' + cat_sprite], (0, 0))

                pad_dict = {
                    'red' : 0,
                    'whit' : 1,
                    'tabby' : 2,
                    'black' : 3,
                    'chocolate' : 4,
                    'cinnamon' : 5,
                    'blue' : 6,
                    'lilac' : 7,
                    'fawn' : 8,
                    'dove' : 9,
                    'champagne' : 10,
                    'buff' : 11,
                    'platinum' : 12,
                    'lavender' : 13,
                    'beige' : 14
                }

                if(phenotype.white[0] == 'W' or phenotype.pointgene[0] == 'c' or phenotype.white_pattern == ['full white'] or override == "white"):
                    pads.blit(sprites.sprites['nosecolours1'], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                elif ('amber' not in phenotype.colour or phenotype.agouti[0] != 'a') and ('russet' in phenotype.colour or 'carnelian' in phenotype.colour or is_red):
                    pads.blit(sprites.sprites['nosecolours0'], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                elif 'amber' in phenotype.colour:
                    phenotype.SpriteInfo(10)
                    whichcolour = phenotype.maincolour
                    pads.blit(sprites.sprites['nosecolours' + str(pad_dict.get(whichcolour[:-1], 0))], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    phenotype.SpriteInfo(sprite_age)
                else:
                    pads.blit(sprites.sprites['nosecolours' + str(pad_dict.get(whichcolour[:-1]))], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                sprite.blit(pads, (0, 0))

                return sprite

            def AddNose(sprite, override = None):
                nose = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                nose.blit(sprites.sprites['nose' + cat_sprite], (0, 0))

                nose_dict = {
                    'red' : 0,
                    'whit' : 1,
                    'tabby' : 2,
                    'black' : 3,
                    'chocolate' : 4,
                    'cinnamon' : 5,
                    'blue' : 6,
                    'lilac' : 7,
                    'fawn' : 8,
                    'dove' : 9,
                    'champagne' : 10,
                    'buff' : 11,
                    'platinum' : 12,
                    'lavender' : 13,
                    'beige' : 14
                }

                if phenotype.maincolour == "white" or override == 'white':
                    nose.blit(sprites.sprites['nosecolours1'], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                elif ('amber' not in phenotype.colour or phenotype.agouti[0] != 'a') and ('red' in phenotype.maincolour or 'cream' in phenotype.maincolour or 'honey' in phenotype.maincolour or 'ivory' in phenotype.maincolour or 'apricot' in phenotype.maincolour):
                    nose.blit(sprites.sprites['nosecolours0'], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                elif 'amber' in phenotype.colour:
                    phenotype.SpriteInfo(10)
                    nose.blit(sprites.sprites['nosecolours' + str(nose_dict.get(phenotype.maincolour[:-1]))], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    phenotype.SpriteInfo(sprite_age)
                elif phenotype.maincolour != phenotype.spritecolour:
                    nose.blit(sprites.sprites['nosecolours2'], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    nose.set_alpha(200)
                else:
                    nose.blit(sprites.sprites['nosecolours' + str(nose_dict.get(phenotype.maincolour[:-1]))], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                sprite.blit(nose, (0, 0))
                return sprite

            def MakeCat(whichmain, whichcolour, whichbase, cat_unders, special=None):
                is_red = ('red' in whichcolour or 'cream' in whichcolour or 'honey' in whichcolour or 'ivory' in whichcolour or 'apricot' in whichcolour)
                
                if (phenotype.white[0] == 'W' or phenotype.pointgene[0] == 'c' or whichcolour == 'white' or phenotype.white_pattern == ['full white']):
                    whichmain.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                elif(whichcolour != whichbase and special != 'masked silver'):
                    if(phenotype.pointgene[0] == "C"):
                        whichmain = TabbyBase(whichcolour, whichbase, cat_unders, special)

                        whichmain = AddStripes(whichmain, whichcolour, whichbase)
                    else:
                        #create base
                        colourbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        if("black" in whichcolour and phenotype.pointgene[0] == "cm"):
                            colourbase.blit(sprites.sprites[whichbase.replace("black", "cinnamon")], (0, 0))
                        else:
                            colourbase = TabbyBase(whichcolour, whichbase, cat_unders, special)

                            if((phenotype.pointgene == ["cb", "cb"] and 'cinnamon' not in whichcolour and cat_sprite != "20") or (((("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm") and cat_sprite != "20") or phenotype.pointgene == ["cb", "cb"]) and get_current_season() == 'Leaf-bare')):
                                colourbase.set_alpha(100)
                            elif((("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm") and cat_sprite != "20") or phenotype.pointgene == ["cb", "cb"] or ((cat_sprite != "20" or ("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm")) and get_current_season() == 'Leaf-bare')):
                                colourbase.set_alpha(50)
                            elif(("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm")):
                                colourbase.set_alpha(15)
                            else:
                                colourbase.set_alpha(0)
                        
                        whichmain.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                        whichmain.blit(colourbase, (0, 0))

                        #add base stripes
                        if("cm" in phenotype.pointgene):
                            if("black" in whichcolour and phenotype.pointgene[0] == "cm"):
                                whichmain = AddStripes(whichmain, 'lightbasecolours2', whichbase)
                            else:
                                if("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm"):
                                    if("black" in whichcolour and cat_sprite != "20"):
                                        whichmain = AddStripes(whichmain, 'lightbasecolours2', whichbase)
                                    elif((("chocolate" in whichcolour or "cinnamon" in whichcolour) and cat_sprite != "20") or "black" in whichcolour):
                                        whichmain = AddStripes(whichmain, 'lightbasecolours1', whichbase)
                                    elif("cinnamon" in whichcolour or "chocolate" in whichcolour):
                                        whichmain = AddStripes(whichmain, 'lightbasecolours0', whichbase)
                                    else:
                                        pointbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                                        pointbase.blit(sprites.sprites[stripecolourdict.get(whichcolour[:-1], whichcolour[:-1])+whichcolour[-1]], (0, 0))
                                        if phenotype.caramel == 'caramel' and not is_red:    
                                            pointbase.blit(sprites.sprites['caramel0'], (0, 0))
                                        pointbase.set_alpha(102)
                                        pointbase2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                                        pointbase2.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                                        pointbase2.blit(pointbase, (0, 0))
                                        whichmain = AddStripes(whichmain, whichcolour, whichbase, coloursurface=pointbase2)
                                else:
                                    if("black" in whichcolour and cat_sprite != "20"):
                                        stripecolour = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                                        stripecolour = AddStripes(stripecolour, 'lightbasecolours1', whichbase)
                                        stripecolour.set_alpha(102)
                                        whichmain.blit(stripecolour, (0, 0))
                                    else:
                                        whichmain = AddStripes(whichmain, 'lightbasecolours0', whichbase)
                        
                        else:
                            if("black" in whichcolour and phenotype.pointgene == ["cb", "cb"] and cat_sprite != "20"):
                                whichmain = AddStripes(whichmain, 'lightbasecolours3', whichbase)
                            elif((("chocolate" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("black" in whichcolour and "cb" in phenotype.pointgene)) and cat_sprite != "20" or ("black" in whichcolour and phenotype.pointgene == ["cb", "cb"])):
                                whichmain = AddStripes(whichmain, 'lightbasecolours2', whichbase)
                            elif((("cinnamon" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("chocolate" in whichcolour and "cb" in phenotype.pointgene) or ("black" in whichcolour and phenotype.pointgene == ["cs", "cs"])) and cat_sprite != "20" or (("chocolate" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("black" in whichcolour and "cb" in phenotype.pointgene))):
                                whichmain = AddStripes(whichmain, 'lightbasecolours1', whichbase)

                            elif(phenotype.pointgene == ["cb", "cb"]) and cat_sprite != "20":
                                pointbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                                pointbase.blit(sprites.sprites[stripecolourdict.get(whichcolour[:-1], whichcolour[:-1])+whichcolour[-1]], (0, 0))
                                if phenotype.caramel == 'caramel' and not is_red:    
                                    pointbase.blit(sprites.sprites['caramel0'], (0, 0))
                                pointbase.set_alpha(204)
                                pointbase2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                                pointbase2.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                                pointbase2.blit(pointbase, (0, 0))
                                whichmain = AddStripes(whichmain, whichcolour, whichbase, coloursurface=pointbase2)
                            elif("cb" in phenotype.pointgene) and (cat_sprite != "20" or phenotype.pointgene == ["cb", "cb"]):
                                pointbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                                pointbase.blit(sprites.sprites[stripecolourdict.get(whichcolour[:-1], whichcolour[:-1])+whichcolour[-1]], (0, 0))
                                if phenotype.caramel == 'caramel' and not is_red:    
                                    pointbase.blit(sprites.sprites['caramel0'], (0, 0))
                                if(phenotype.eumelanin[0] == "bl"):
                                    pointbase.set_alpha(25)
                                else:
                                    pointbase.set_alpha(102)
                                pointbase2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                                pointbase2.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                                pointbase2.blit(pointbase, (0, 0))
                                whichmain = AddStripes(whichmain, whichcolour, whichbase, coloursurface=pointbase2)
                            else:
                                whichmain = AddStripes(whichmain, 'lightbasecolours0', whichbase)

                        #mask base
                        colourbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        if("black" in whichcolour and phenotype.pointgene[0] == "cm"):
                            colourbase2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            colourbase.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                            colourbase2.blit(sprites.sprites[whichbase.replace("black", "cinnamon")], (0, 0))
                            colourbase2.set_alpha(150)
                            colourbase.blit(colourbase2, (0, 0))
                        else:
                            colourbase = TabbyBase(whichcolour, whichbase, cat_unders, special)
                        pointbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        pointbase2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        pointbase2.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                        if("cm" in phenotype.pointgene):
                            if("black" in whichcolour and phenotype.pointgene[0] == "cm"):
                                pointbase.blit(colourbase, (0, 0))
                            else:
                                if((("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm") and cat_sprite != "20") or ((cat_sprite != "20" or ("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm")) and get_current_season() == "Leaf-bare")):
                                    colourbase.set_alpha(180)
                                elif(cat_sprite != "20" or ("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm")):
                                    colourbase.set_alpha(50)
                                else:
                                    colourbase.set_alpha(0)

                                pointbase2.blit(colourbase, (0, 0))

                                if(get_current_season() == "Greenleaf"):
                                    pointbase.blit(sprites.sprites['mochal' + cat_sprite], (0, 0))
                                    pointbase.blit(pointbase2, (0, 0), 
                                                special_flags=pygame.BLEND_RGBA_MULT)
                                elif(get_current_season() == "Leaf-bare"):
                                    pointbase.blit(sprites.sprites['mochad' + cat_sprite], (0, 0))
                                    pointbase.blit(pointbase2, (0, 0), 
                                                special_flags=pygame.BLEND_RGBA_MULT)
                                else:
                                    pointbase.blit(sprites.sprites['mocham' + cat_sprite], (0, 0))
                                    pointbase.blit(pointbase2, (0, 0), 
                                                special_flags=pygame.BLEND_RGBA_MULT)
                            
                                
                        else:
                            if((phenotype.pointgene == ["cb", "cb"] and cat_sprite != "20") or ("cb" in phenotype.pointgene and cat_sprite != "20" and get_current_season() == 'Leaf-bare')):
                                colourbase.set_alpha(180)
                            elif(("cb" in phenotype.pointgene and cat_sprite != "20") or phenotype.pointgene == ["cb", "cb"] or ((cat_sprite != "20" or "cb" in phenotype.pointgene) and get_current_season() == 'Leaf-bare')):
                                colourbase.set_alpha(120)
                            elif(cat_sprite != "20" or "cb" in phenotype.pointgene):
                                colourbase.set_alpha(50)
                            else:
                                colourbase.set_alpha(15)
                            
                            pointbase2.blit(colourbase, (0, 0))

                            if(get_current_season() == "Greenleaf"):
                                pointbase.blit(sprites.sprites['pointsl' + cat_sprite], (0, 0))
                                pointbase.blit(pointbase2, (0, 0), 
                                            special_flags=pygame.BLEND_RGBA_MULT)
                            elif(get_current_season() == "Leaf-bare"):
                                pointbase.blit(sprites.sprites['pointsd' + cat_sprite], (0, 0))
                                pointbase.blit(pointbase2, (0, 0), 
                                            special_flags=pygame.BLEND_RGBA_MULT)
                            else:
                                pointbase.blit(sprites.sprites['pointsm' + cat_sprite], (0, 0))
                                pointbase.blit(pointbase2, (0, 0), 
                                            special_flags=pygame.BLEND_RGBA_MULT)
                        
                            
                        #add mask stripes
                    
                        stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        stripebase2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)

                        if("black" in whichcolour and phenotype.pointgene[0] == "cm"):
                            colour = whichcolour.replace("black", "cinnamon")
                        else:
                            colour = whichcolour
                
                        stripebase.blit(CreateStripes(colour, whichbase), (0, 0))

                        
                        if(get_current_season() == "Greenleaf"):
                            stripebase2.blit(sprites.sprites['mochal' + cat_sprite], (0, 0))
                            stripebase2.blit(stripebase, (0, 0), 
                                        special_flags=pygame.BLEND_RGBA_MULT)
                        elif(get_current_season() == "Leaf-bare"):
                            stripebase2.blit(sprites.sprites['mochad' + cat_sprite], (0, 0))
                            stripebase2.blit(stripebase, (0, 0), 
                                        special_flags=pygame.BLEND_RGBA_MULT)
                        else:
                            stripebase2.blit(sprites.sprites['mocham' + cat_sprite], (0, 0))
                            stripebase2.blit(stripebase, (0, 0), 
                                        special_flags=pygame.BLEND_RGBA_MULT)

                        pointbase.blit(stripebase2, (0, 0))

                        whichmain.blit(pointbase, (0, 0))

                else:
                    if(phenotype.pointgene[0] == "C"):
                        whichmain.blit(sprites.sprites[stripecolourdict.get(whichcolour[:-1], whichcolour[:-1])+whichcolour[-1]], (0, 0))
                        if phenotype.caramel == 'caramel' and not is_red:    
                            whichmain.blit(sprites.sprites['caramel0'], (0, 0))
                            
                        whichmain = ApplySmokeEffects(whichmain)

                        if phenotype.length != "longhaired":
                            stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            stripebase.blit(CreateStripes(whichcolour, "solid"), (0, 0))
                            whichmain.blit(stripebase, (0, 0))
                    elif("cm" in phenotype.pointgene):
                        colour = None
                        coloursurface = None
                        if("black" in whichcolour and phenotype.pointgene[0] == "cm"):
                            whichmain.blit(sprites.sprites['lightbasecolours2'], (0, 0)) 
                            overlay = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            overlay.blit(sprites.sprites['cinnamon3'], (0, 0)) 
                            overlay.set_alpha(150)
                            whichmain.blit(overlay, (0, 0))
                            whichmain = ApplySmokeEffects(whichmain)

                            if phenotype.length != "longhaired":
                                stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            
                                stripebase.blit(CreateStripes(whichcolour.replace("black", "cinnamon"), 'solid', pattern="fullbar"), (0, 0))
                                stripebase.set_alpha(150)

                                whichmain.blit(stripebase, (0, 0))
                        else:
                            stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                                
                            if("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm"):
                                if("black" in whichcolour and cat_sprite != "20"):
                                    whichmain.blit(sprites.sprites['lightbasecolours2'], (0, 0))
                                    colour = 'lightbasecolours2'
                                    whichmain = ApplySmokeEffects(whichmain)

                                elif(("chocolate" in whichcolour and cat_sprite != "20") or "black" in whichcolour):
                                    whichmain.blit(sprites.sprites['lightbasecolours1'], (0, 0))
                                    colour = 'lightbasecolours1'
                                    whichmain = ApplySmokeEffects(whichmain)
                                elif("cinnamon" in whichcolour or "chocolate" in whichcolour):
                                    whichmain.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                                    colour = 'lightbasecolours0'
                                else:
                                    pointbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                                    pointbase.blit(sprites.sprites[whichcolour], (0, 0))
                                    if phenotype.caramel == 'caramel' and not is_red:    
                                        pointbase.blit(sprites.sprites['caramel0'], (0, 0))
                        
                                    pointbase.set_alpha(102)
                                    if 'fawn' in whichcolour:
                                        pointbase.set_alpha(0)

                                    if 'blue' in whichcolour:
                                        if phenotype.pointgene[0] == "cm":
                                            whichmain.blit(sprites.sprites[whichcolour.replace('blue', 'fawn')], (0, 0))
                                            whichmain.blit(pointbase, (0, 0))
                                            pointbase.blit(sprites.sprites['lightbasecolours2'], (0, 0))
                                            pointbase.set_alpha(50)
                                        else:
                                            whichmain.blit(sprites.sprites['lightbasecolours1'], (0, 0))
                                    else:
                                        whichmain.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                                    whichmain.blit(pointbase, (0, 0))
                                    pointbase.blit(whichmain, (0, 0))
                                    coloursurface = pointbase
                                    colour = whichcolour
                                    
                                    whichmain = ApplySmokeEffects(whichmain)
                            else:
                                if("black" in whichcolour and cat_sprite != "20"):
                                    whichmain.blit(sprites.sprites['lightbasecolours1'], (0, 0))
                                    colour = 'lightbasecolours1'
                                    whichmain = ApplySmokeEffects(whichmain)
                                else:
                                    whichmain.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                                    colour = 'lightbasecolours0'
                            
                            
                            if phenotype.length != "longhaired":
                                stripebase = CreateStripes(colour, 'solid', coloursurface=coloursurface)
                                whichmain.blit(stripebase, (0, 0))

                            pointbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            pointbase2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            
                            pointbase2.blit(sprites.sprites[whichcolour], (0, 0))
                            if phenotype.caramel == 'caramel' and not is_red:    
                                pointbase2.blit(sprites.sprites['caramel0'], (0, 0))
                        
                            whichmain = ApplySmokeEffects(whichmain)

                            
                            if phenotype.length != "longhaired":
                                stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                                stripebase.blit(CreateStripes(whichcolour, 'solid'), (0, 0))

                            pointbase2.blit(stripebase, (0, 0))

                            if(get_current_season() == "Greenleaf"):
                                pointbase.blit(sprites.sprites['mochal' + cat_sprite], (0, 0))
                                pointbase.blit(pointbase2, (0, 0), 
                                            special_flags=pygame.BLEND_RGBA_MULT)
                            elif(get_current_season() == "Leaf-bare"):
                                pointbase.blit(sprites.sprites['mochad' + cat_sprite], (0, 0))
                                pointbase.blit(pointbase2, (0, 0), 
                                            special_flags=pygame.BLEND_RGBA_MULT)
                            else:
                                pointbase.blit(sprites.sprites['mocham' + cat_sprite], (0, 0))
                                pointbase.blit(pointbase2, (0, 0), 
                                            special_flags=pygame.BLEND_RGBA_MULT)
                        
                            if phenotype.pointgene[0] == "cm" and 'blue' in whichcolour:
                                pointbase.set_alpha(102)

                            whichmain.blit(pointbase, (0, 0))        
                            
                    else:
                        colour = whichcolour
                        coloursurface = None
                        stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        if("black" in whichcolour and phenotype.pointgene == ["cb", "cb"] and cat_sprite != "20"):
                            whichmain.blit(sprites.sprites['lightbasecolours3'], (0, 0)) 
                            colour = 'lightbasecolours3'
                            whichmain = ApplySmokeEffects(whichmain)
                        elif((("chocolate" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("black" in whichcolour and "cb" in phenotype.pointgene)) and cat_sprite != "20") or ("black" in whichcolour and phenotype.pointgene == ["cb", "cb"]):
                            whichmain.blit(sprites.sprites['lightbasecolours2'], (0, 0)) 
                            colour = 'lightbasecolours2'
                            whichmain = ApplySmokeEffects(whichmain)
                        elif((("chocolate" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("chocolate" in whichcolour and "cb" in phenotype.pointgene) or ("black" in whichcolour and phenotype.pointgene == ["cs", "cs"])) and cat_sprite != "20") or (("chocolate" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("black" in whichcolour and "cb" in phenotype.pointgene)):
                            whichmain.blit(sprites.sprites['lightbasecolours1'], (0, 0))  
                            colour = 'lightbasecolours1'
                            whichmain = ApplySmokeEffects(whichmain)
                        elif(phenotype.pointgene == ["cb", "cb"]) and cat_sprite != "20":
                            pointbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            pointbase.blit(sprites.sprites[whichcolour], (0, 0))
                            if phenotype.caramel == 'caramel' and not is_red:    
                                pointbase.blit(sprites.sprites['caramel0'], (0, 0))
                        
                            pointbase.set_alpha(204)
                            if 'lilac' in whichcolour:
                                pointbase.set_alpha(140)
                            if 'fawn' in whichcolour:
                                pointbase.set_alpha(50)
                            
                            if 'blue' in whichcolour:
                                whichmain.blit(sprites.sprites['lightbasecolours1'], (0, 0))
                            else:
                                whichmain.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                            whichmain.blit(pointbase, (0, 0))
                            pointbase.blit(whichmain, (0, 0)) 
                            coloursurface = pointbase
                            whichmain = ApplySmokeEffects(whichmain)
                        elif("cb" in phenotype.pointgene) and (cat_sprite != "20" or phenotype.pointgene == ["cb", "cb"]):
                            pointbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            pointbase.blit(sprites.sprites[whichcolour], (0, 0))
                            if phenotype.caramel == 'caramel' and not is_red:    
                                pointbase.blit(sprites.sprites['caramel0'], (0, 0))
                        
                            if(phenotype.eumelanin[0] == "bl"):
                                pointbase.set_alpha(25)
                            else:
                                pointbase.set_alpha(102)
                            
                            if 'blue' in whichcolour:
                                whichmain.blit(sprites.sprites['lightbasecolours1'], (0, 0))
                            else:
                                whichmain.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                            whichmain.blit(pointbase, (0, 0))
                            coloursurface = whichmain
                            whichmain = ApplySmokeEffects(whichmain)
                            colour = whichcolour

                        else:
                            whichmain.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                            colour = 'lightbasecolours0'

                        stripebase = CreateStripes(colour, 'solid', coloursurface=coloursurface)

                        whichmain.blit(stripebase, (0, 0))

                        pointbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        pointbase2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            
                        pointbase2.blit(sprites.sprites[whichcolour], (0, 0))
                        if phenotype.caramel == 'caramel' and not is_red:    
                                pointbase2.blit(sprites.sprites['caramel0'], (0, 0))
                        pointbase2 = ApplySmokeEffects(pointbase2)

                        
                        if phenotype.length != "longhaired":
                            stripebase = CreateStripes(whichcolour, "solid")
                        
                            pointbase2.blit(stripebase, (0, 0))

                        if(get_current_season() == "Greenleaf"):
                            pointbase.blit(sprites.sprites['pointsl' + cat_sprite], (0, 0))
                            pointbase.blit(pointbase2, (0, 0), 
                                        special_flags=pygame.BLEND_RGBA_MULT)
                        elif(get_current_season() == "Leaf-bare"):
                            pointbase.blit(sprites.sprites['pointsd' + cat_sprite], (0, 0))
                            pointbase.blit(pointbase2, (0, 0), 
                                        special_flags=pygame.BLEND_RGBA_MULT)
                        else:
                            pointbase.blit(sprites.sprites['pointsm' + cat_sprite], (0, 0))
                            pointbase.blit(pointbase2, (0, 0), 
                                        special_flags=pygame.BLEND_RGBA_MULT)
                    
                        whichmain.blit(pointbase, (0, 0))


                seasondict = {
                    'Greenleaf': 'summer',
                    'Leaf-bare': 'winter'
                }

                if(phenotype.karp[0] == 'K'):
                    if(phenotype.karp[1] == 'K'):
                        whichmain.blit(sprites.sprites['homokarpati'+ seasondict.get(get_current_season(), "spring") + cat_sprite], (0, 0))
                    else:
                        whichmain.blit(sprites.sprites['hetkarpati'+ seasondict.get(get_current_season(), "spring") + cat_sprite], (0, 0))
                if(phenotype.white[0] == 'wsal'):
                    whichmain.blit(sprites.sprites['salmiak' + cat_sprite], (0, 0))

                whichmain = AddPads(whichmain, whichcolour, is_red)
                
                return whichmain

            gensprite = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)

            def ApplyPatchEffects(sprite):
                if('masked' in phenotype.silvergold):
                    masked = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    masked = MakeCat(masked, phenotype.maincolour, phenotype.spritecolour, phenotype.mainunders, special="masked silver")
                    masked2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    masked2.blit(sprites.sprites["BLUE-TIPPED" + cat_sprite], (0, 0))
                    masked2.blit(masked, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    masked2.set_alpha(120)
                    sprite.blit(masked2, (0, 0))

                if (phenotype.ext[0] == 'Eg' and phenotype.agouti[0] != 'a') and phenotype.satin[0] != "st" and phenotype.tenn[0] != 'tr' and not ('red' in phenotype.maincolour or 'cream' in phenotype.maincolour or 'honey' in phenotype.maincolour or 'ivory' in phenotype.maincolour or 'apricot' in phenotype.maincolour):    
                    sprite.blit(sprites.sprites['satin0'], (0, 0))
                elif (phenotype.glitter[0] == 'gl' or phenotype.ghosting[0] == 'Gh') and (phenotype.agouti[0] != 'a' or ('red' in phenotype.maincolour or 'cream' in phenotype.maincolour or 'honey' in phenotype.maincolour or 'ivory' in phenotype.maincolour or 'apricot' in phenotype.maincolour)):    
                    if phenotype.satin[0] != "st" and phenotype.tenn[0] != 'tr':    
                        sprite.blit(sprites.sprites['satin0'], (0, 0))
                    if(phenotype.ghosting[0] == 'Gh'):
                        fading = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        fading.blit(sprites.sprites['tabbyghost'+cat_sprite], (0, 0))
                        fading.set_alpha(50)
                        sprite.blit(fading, (0, 0))
                        sprite.blit(sprites.sprites['satin0'], (0, 0))
                if not phenotype.brindledbi and not ('red' in phenotype.maincolour or 'cream' in phenotype.maincolour or 'honey' in phenotype.maincolour or 'ivory' in phenotype.maincolour or 'apricot' in phenotype.maincolour) and (phenotype.ext[0] != "Eg" and phenotype.agouti[0] !='a' and (phenotype.corin[0] == 'sg' or phenotype.corin[0] == 'sh' or ('ec' in phenotype.ext and phenotype.ext[0] != "Eg") or (phenotype.ext[0] == 'ea' and sprite_age > 6) or (phenotype.silver[0] == 'i' and phenotype.corin[0] == 'fg'))):
                    sunshine = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    sunshine.blit(sprites.sprites['bimetal' + cat_sprite], (0, 0))

                    colours = phenotype.FindRed(phenotype, sprite_age, special='nosilver')
                    underbelly = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    underbelly = MakeCat(underbelly, colours[0], colours[1], [colours[2], colours[3]], special='nounders')
                    sunshine.blit(underbelly, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                    sunshine.set_alpha(75)
                    sprite.blit(sunshine, (0, 0))
                return sprite

            is_white = 'W' in phenotype.white or phenotype.pointgene[0] == 'c' or phenotype.white_pattern == ['full white']
            
            if(phenotype.patchmain != "" and 'rev' in phenotype.tortiepattern[0]):
                gensprite = MakeCat(gensprite, phenotype.patchmain, phenotype.patchcolour, phenotype.patchunders)
            else:
                gensprite = MakeCat(gensprite, phenotype.maincolour, phenotype.spritecolour, phenotype.mainunders)
            
            if not is_white:
                gensprite = ApplyPatchEffects(gensprite)
            
                if(phenotype.patchmain != ""):
                    for pattern in phenotype.tortiepattern:
                        tortpatches = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        if 'rev' in pattern:
                            isred = not ('red' in phenotype.maincolour or 'cream' in phenotype.maincolour or 'honey' in phenotype.maincolour or 'ivory' in phenotype.maincolour or 'apricot' in phenotype.maincolour)
                            tortpatches = MakeCat(tortpatches, phenotype.maincolour, phenotype.spritecolour, phenotype.mainunders)
                        else:
                            isred = not ('red' in phenotype.patchmain or 'cream' in phenotype.patchmain or 'honey' in phenotype.patchmain or 'ivory' in phenotype.patchmain or 'apricot' in phenotype.patchmain)
                            tortpatches = MakeCat(tortpatches, phenotype.patchmain, phenotype.patchcolour, phenotype.patchunders)
                        if phenotype.caramel == 'caramel' and isred: 
                            tortpatches.blit(sprites.sprites['caramel0'], (0, 0))
                        tortpatches = ApplyPatchEffects(tortpatches)
                        
                        tortpatches2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        tortpatches2.blit(sprites.sprites[pattern.replace('rev', "") + cat_sprite], (0, 0))
                        tortpatches2.blit(tortpatches, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        gensprite.blit(tortpatches2, (0, 0))

                if(phenotype.merlepattern != None and not merle):
                    for pattern in phenotype.merlepattern:
                        if 'rev' in pattern:
                            phenotype.SpriteInfo(sprite_age)
                            merlepatches = GenSprite(phenotype, sprite_age, merle=True)
                        else:
                            old_silver = phenotype.silver
                            phenotype.silver = ['i', 'i']
                            phenotype.SpriteInfo(sprite_age)
                            merlepatches = GenSprite(phenotype, sprite_age, merle=True)
                            phenotype.silver = old_silver
                            phenotype.SpriteInfo(sprite_age)
                        
                        merlepatches2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        merlepatches2.blit(sprites.sprites[pattern.replace('rev', "") + cat_sprite], (0, 0))
                        merlepatches2.blit(merlepatches, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        gensprite.blit(merlepatches2, (0, 0))

                if phenotype.satin[0] == "st" or phenotype.tenn[0] == 'tr':
                    gensprite.blit(sprites.sprites['satin0'], (0, 0))

                if (phenotype.fevercoat and sprite_age < 5):
                    fevercoat = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    fevercoat.blit(sprites.sprites['bleach' + cat_sprite], (0, 0))
                    fevercoat.blit(sprites.sprites['bleach' + cat_sprite], (0, 0))
                    fevercoat.blit(sprites.sprites['bleach' + cat_sprite], (0, 0))
                    fevercoat.blit(sprites.sprites['bleach' + cat_sprite], (0, 0))
                    fevercoat.blit(sprites.sprites['bleach' + cat_sprite], (0, 0))
                    fevercoat.blit(sprites.sprites['lightbasecolours0'], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    if (sprite_age > 2):
                        fevercoat.set_alpha(150)
                    gensprite.blit(fevercoat, (0, 0))
                
                elif (phenotype.bleach[0] == "lb" and sprite_age > 3) or (phenotype.wbtype == "shaded" and 'smoke' in phenotype.silvergold):
                    gensprite.blit(sprites.sprites['bleach' + cat_sprite], (0, 0))

            
            if (
                game.settings['tints']
                and cat.pelt.tint != "none" 
                and cat.pelt.tint in sprites.cat_tints["tint_colours"]
            ):
                tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                tint.fill(tuple(sprites.cat_tints["tint_colours"][cat.pelt.tint]))
                gensprite.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            if (
                game.settings['tints']
                and cat.pelt.tint != "none"
                and cat.pelt.tint in sprites.cat_tints["dilute_tint_colours"]
            ):
                tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                tint.fill(tuple(sprites.cat_tints["dilute_tint_colours"][cat.pelt.tint]))
                gensprite.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

            gensprite = AddNose(gensprite)

            if (game.config["fun"]["april_fools"] or is_today(SpecialDate.APRIL_FOOLS)) and "Dg" in phenotype.april_fools.get("danish_green", []):
                green = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                green.fill((0, 255, 0))
                green.set_alpha(100)
                green.blit(gensprite, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
                gensprite.blit(green, (0, 0))

            whitesprite = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
            tintedwhitesprite = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)

            if(phenotype.white_pattern != 'No' and phenotype.white_pattern):
                for x in phenotype.white_pattern:
                    if('dorsal' not in x and 'break/' not in x and x not in vitiligo):
                        whitesprite.blit(sprites.sprites[x + cat_sprite], (0, 0))
            if(phenotype.white_pattern != 'No' and phenotype.white_pattern):
                for x in phenotype.white_pattern:
                    if('break/' in x):
                        whitesprite.blit(sprites.sprites[x + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            tintedwhitesprite.blit(whitesprite, (0, 0))

            leathers = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
            leathers = AddPads(leathers, "white", override="white")
            leathers = AddNose(leathers, "white")
            white_leathers = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
            white_leathers.blit(whitesprite, (0, 0))

            if(phenotype.vitiligo):
                for x in vitiligo:
                    if x in phenotype.white_pattern:
                        white_leathers.blit(sprites.sprites[x + cat_sprite], (0, 0))
                        tintedwhitesprite.blit(sprites.sprites[x + cat_sprite], (0, 0))
            white_leathers.blit(leathers, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

            if phenotype.white_pattern:
                if 'dorsal1' in phenotype.white_pattern:
                    tintedwhitesprite.blit(sprites.sprites['dorsal1' + cat_sprite], (0, 0))
                elif 'dorsal2' in phenotype.white_pattern:
                    tintedwhitesprite.blit(sprites.sprites['dorsal2' + cat_sprite], (0, 0))

            
            if (
                game.settings['tints']
                and cat.pelt.white_patches_tint != "none"
                and cat.pelt.white_patches_tint
                in sprites.white_patches_tints["tint_colours"]
            ):
                tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                tint.fill(
                    tuple(
                        sprites.white_patches_tints["tint_colours"][
                            cat.pelt.white_patches_tint
                        ]
                    )
                )
                tintedwhitesprite.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            gensprite.blit(tintedwhitesprite, (0, 0))


            if cat.phenotype.sedesp == ['hr', 're'] or (cat.phenotype.sedesp[0] == 're' and sprite_age < 12) or (cat.phenotype.laperm[0] == 'Lp' and sprite_age < 4):
                gensprite.blit(sprites.sprites['furpoint' + cat_sprite], (0, 0))
                gensprite.blit(sprites.sprites['furpoint' + cat_sprite], (0, 0))
            elif(cat.pelt.length == 'hairless'):
                gensprite.blit(sprites.sprites['hairless' + cat_sprite], (0, 0))
                gensprite.blit(sprites.sprites['furpoint' + cat_sprite], (0, 0))
            elif('patchy ' in cat.phenotype.furtype):
                gensprite.blit(sprites.sprites['donskoy' + cat_sprite], (0, 0))
            
            if('sparse' in cat.phenotype.furtype):
                gensprite.blit(sprites.sprites['satin0'], (0, 0))
                gensprite.blit(sprites.sprites['satin0'], (0, 0))
                gensprite.blit(sprites.sprites['lykoi' + cat_sprite], (0, 0))

            gensprite.blit(white_leathers, (0, 0))
            

            if(phenotype.fold[0] != 'Fd' or phenotype.curl[0] == 'Cu'):
                gensprite.blit(sprites.sprites['ears' + cat_sprite], (0, 0))

            if(int(cat_sprite) < 18):
                lefteye = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                righteye = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                special = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)

                lefteye.blit(sprites.sprites['left' + cat_sprite], (0, 0))
                righteye.blit(sprites.sprites['right' + cat_sprite], (0, 0))

                lefteye.blit(sprites.sprites[phenotype.lefteyetype + "/" + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                righteye.blit(sprites.sprites[phenotype.righteyetype + "/" + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                gensprite.blit(lefteye, (0, 0))
                gensprite.blit(righteye, (0, 0))


                if sprite_age == 1:
                    lefteye.blit(sprites.sprites['left' + cat_sprite], (0, 0))
                    righteye.blit(sprites.sprites['right' + cat_sprite], (0, 0))
                    lefteye.blit(sprites.sprites[phenotype.lefteyetype.split(' ; ')[0] + ' ; blue' + "/" + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    righteye.blit(sprites.sprites[phenotype.righteyetype.split(' ; ')[0] + ' ; blue' + "/" + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    lefteye.set_alpha(200)
                    righteye.set_alpha(200)
                    gensprite.blit(lefteye, (0, 0))
                    gensprite.blit(righteye, (0, 0))


                if(phenotype.extraeye):
                    special.blit(sprites.sprites[phenotype.extraeye + cat_sprite], (0, 0))
                    special.blit(sprites.sprites[phenotype.extraeyetype + "/" + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    gensprite.blit(special, (0, 0))
                    if sprite_age == 1:
                        special.blit(sprites.sprites[phenotype.extraeye + cat_sprite], (0, 0))
                        special.blit(sprites.sprites[phenotype.extraeyetype.split(' ; ')[0] + ' ; blue' + "/" + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        special.set_alpha(150)
                        gensprite.blit(special, (0, 0))

                if(phenotype.pinkdilute[0] == 'dp'):
                    pupils = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    pupils.blit(sprites.sprites['redpupils' + cat_sprite], (0, 0))
                    pupils.set_alpha(100)
                    gensprite.blit(pupils, (0, 0))
            
            return gensprite

        age = cat.moons

        if int(cat_sprite) == 20:
            age = 0
        elif int(cat_sprite) < 3 and 5 < cat.moons < 1:
            age = 4
        elif int(cat_sprite) < 6 and 11 < cat.moons < 6:
            age = 10
        elif (int(cat_sprite == 19) or int(cat_sprite) == 17) and 12 < cat.moons < 6:
            age = 6
        elif int(cat_sprite) > 5 and cat_sprite not in ['17', '19'] and cat.moons < 12:
            age = 60
        gensprite.blit(GenSprite(phenotype, age), (0, 0))

        if(cat.chimerapheno):
            chimerapatches = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
            for pattern in cat.chimerapheno.chimerapattern:
                chimerapatches.blit(sprites.sprites[pattern + cat_sprite], (0, 0))
            chimerapatches.blit(GenSprite(cat.chimerapheno, age), (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            gensprite.blit(chimerapatches, (0, 0))

        if not scars_hidden:
            for scar in cat.pelt.scars:
                if scar in cat.pelt.scars1:
                    gensprite.blit(sprites.sprites['scars' + scar + cat_sprite], (0, 0))
                if scar in cat.pelt.scars3:
                    gensprite.blit(sprites.sprites['scars' + scar + cat_sprite], (0, 0))

        # draw line art
        if game.settings['shaders'] and not dead:
            gensprite.blit(sprites.sprites['shaders' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            gensprite.blit(sprites.sprites['lighting' + cat_sprite], (0, 0))

        # make sure colours are in the lines
        if('rexed' in cat.phenotype.furtype or 'wiry' in cat.phenotype.furtype):
            gensprite.blit(sprites.sprites['rexbord'+ cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            gensprite.blit(sprites.sprites['rexbord'+ cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        else:
            gensprite.blit(sprites.sprites['normbord'+ cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            gensprite.blit(sprites.sprites['normbord'+ cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        if(cat.phenotype.fold[0] == 'Fd'):
            gensprite.blit(sprites.sprites['foldbord'+ cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            gensprite.blit(sprites.sprites['foldbord'+ cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        elif(cat.phenotype.curl[0] == 'Cu'):
            gensprite.blit(sprites.sprites['curlbord'+ cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            gensprite.blit(sprites.sprites['curlbord'+ cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        new_sprite.blit(gensprite, (0, 0))

        lineart = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
        earlines = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
        bodylines = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)

        if not dead:
            if(cat.phenotype.fold[0] != 'Fd'):
                if(cat.phenotype.curl[0] == 'Cu'):
                    earlines.blit(sprites.sprites['curllines' + cat_sprite], (0, 0))
                else:
                    earlines.blit(sprites.sprites['lines' + cat_sprite], (0, 0))
            elif(cat.phenotype.curl[0] == 'Cu'):
                earlines.blit(sprites.sprites['fold_curllines' + cat_sprite], (0, 0))
            else:
                earlines.blit(sprites.sprites['foldlines' + cat_sprite], (0, 0))
        elif cat.df:
            if(cat.phenotype.fold[0] != 'Fd'):
                if(cat.phenotype.curl[0] == 'Cu'):
                    earlines.blit(sprites.sprites['curllineartdf' + cat_sprite], (0, 0))
                else:
                    earlines.blit(sprites.sprites['lineartdf' + cat_sprite], (0, 0))
            elif(cat.phenotype.curl[0] == 'Cu'):
                earlines.blit(sprites.sprites['fold_curllineartdf' + cat_sprite], (0, 0))
            else:
                earlines.blit(sprites.sprites['foldlineartdf' + cat_sprite], (0, 0))
        elif dead:
            if(cat.phenotype.fold[0] != 'Fd'):
                if(cat.phenotype.curl[0] == 'Cu'):
                    earlines.blit(sprites.sprites['curllineartdead' + cat_sprite], (0, 0))
                else:
                    earlines.blit(sprites.sprites['lineartdead' + cat_sprite], (0, 0))
            elif(cat.phenotype.curl[0] == 'Cu'):
                earlines.blit(sprites.sprites['fold_curllineartdead' + cat_sprite], (0, 0))
            else:
                earlines.blit(sprites.sprites['foldlineartdead' + cat_sprite], (0, 0))

        earlines.blit(sprites.sprites['isolateears' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        lineart.blit(earlines, (0, 0))
        if('rexed' in phenotype.furtype or 'wiry' in phenotype.furtype):
            if not dead:
                bodylines.blit(sprites.sprites['rexlineart' + cat_sprite], (0, 0))
            elif cat.df:
                bodylines.blit(sprites.sprites['rexlineartdf' + cat_sprite], (0, 0))
            else:
                bodylines.blit(sprites.sprites['rexlineartdead' + cat_sprite], (0, 0))
        else:
            if not dead:
                bodylines.blit(sprites.sprites['lines' + cat_sprite], (0, 0))
            elif cat.df:
                bodylines.blit(sprites.sprites['lineartdf' + cat_sprite], (0, 0))
            else:
                bodylines.blit(sprites.sprites['lineartdead' + cat_sprite], (0, 0))
            
        bodylines.blit(sprites.sprites['noears' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        if cat_sprite != '20':
            lineart.blit(bodylines, (0, 0))
        new_sprite.blit(lineart, (0, 0))

        # draw skin and scars2
        blendmode = pygame.BLEND_RGBA_MIN

        gensprite = new_sprite
        if cat.phenotype.bobtailnr > 0:
            gensprite.blit(sprites.sprites['bobtail' + str(cat.phenotype.bobtailnr) + cat_sprite], (0, 0))
        gensprite.set_colorkey((0, 0, 255))
        new_sprite = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
        new_sprite.blit(gensprite, (0, 0))

        if not scars_hidden:
            for scar in cat.pelt.scars:
                if scar in cat.pelt.scars2:
                    new_sprite.blit(
                        sprites.sprites["scars" + scar + cat_sprite],
                        (0, 0),
                        special_flags=blendmode,
                    )

        if game.config["fun"]["april_fools"] or is_today(SpecialDate.APRIL_FOOLS):
            if cat.phenotype.bobtailnr != 1 and "Pc" in phenotype.april_fools.get("polycaudal", []):
                tail = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                tail.blit(sprites.sprites['bobtail1' + cat_sprite], (0, 0))
                white = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                white.fill((255, 255, 255))
                tail.blit(white, (0, 0), special_flags=pygame.BLEND_RGB_MAX)
                tail.blit(new_sprite, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                offset = 2
                if cat_sprite in ["0", "9", "10", "11", "13", "15", "20"]:
                    new_sprite.blit(tail, (offset, 1))
                elif cat_sprite in ["1", "3", "4", "5", "6", "7", "8", "12", "16", "17"]:
                    new_sprite.blit(tail, (-offset, -1))
                elif cat_sprite in ["2"]:
                    new_sprite.blit(tail, (0, -2))
            
            if game.config["fun"]["april_fools_hats"]:
                if not dead:
                    new_sprite.blit(sprites.sprites['aprilfoolslines' + cat_sprite], (0, 0))
                elif cat.df:
                    new_sprite.blit(sprites.sprites['aprilfoolslineartdf' + cat_sprite], (0, 0))
                else:
                    new_sprite.blit(sprites.sprites['aprilfoolslineartdead' + cat_sprite], (0, 0))

        # draw accessories
        from scripts.cat.pelts import Pelt
        if not acc_hidden and cat.pelt.accessory:
            cat_accessories = cat.pelt.accessory
            categories = ["collars", "tail_accessories", "body_accessories", "head_accessories"]
            for category in categories:
                for accessory in cat_accessories:
                    if accessory in getattr(Pelt, category):
                        if accessory in cat.pelt.plant_accessories:
                            new_sprite.blit(
                                sprites.sprites["acc_herbs" + accessory + cat_sprite],
                                (0, 0),
                            )
                        elif accessory in cat.pelt.wild_accessories:
                            new_sprite.blit(
                                sprites.sprites["acc_wild" + accessory + cat_sprite],
                                (0, 0),
                            )
                        elif accessory in cat.pelt.collars:
                            new_sprite.blit(
                                sprites.sprites["collars" + accessory + cat_sprite], (0, 0)
                            )

        # Apply fading fog
        if (
                cat.pelt.opacity <= 97
                and not cat.prevent_fading
                and game.clan.clan_settings["fading"]
                and dead
        ):
            stage = "0"
            if 80 >= cat.pelt.opacity > 45:
                # Stage 1
                stage = "1"
            elif cat.pelt.opacity <= 45:
                # Stage 2
                stage = "2"

            new_sprite.blit(
                sprites.sprites["fademask" + stage + cat_sprite],
                (0, 0),
                special_flags=pygame.BLEND_RGBA_MULT,
            )

            if cat.df:
                temp = sprites.sprites["fadedf" + stage + cat_sprite].copy()
                temp.blit(new_sprite, (0, 0))
                new_sprite = temp
            else:
                temp = sprites.sprites["fadestarclan" + stage + cat_sprite].copy()
                temp.blit(new_sprite, (0, 0))
                new_sprite = temp
        
        return new_sprite

    try:
        geno = deepcopy(cat.phenotype)
        new_sprite = draw_sprite(geno, cat_sprite)
        if cat.phenotype.somatic.get('base', False):
            som_sprite = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
            som_sprite.blit(sprites.sprites[geno.somatic["base"] + cat_sprite], (0, 0))
            som_sprite.blit(draw_sprite(geno, cat_sprite, somatic=True), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            new_sprite.blit(som_sprite, (0, 0))

    except (TypeError, KeyError):
        logger.exception("Failed to load sprite")

        # Placeholder image
        new_sprite = image_cache.load_image(
            f"sprites/error_placeholder.png"
        ).convert_alpha()
    
    # reverse, if assigned so
    if cat.pelt.reverse:
        new_sprite = pygame.transform.flip(new_sprite, True, False)

    return new_sprite


def apply_opacity(surface, opacity):
    for x in range(surface.get_width()):
        for y in range(surface.get_height()):
            pixel = list(surface.get_at((x, y)))
            pixel[3] = int(pixel[3] * opacity / 100)
            surface.set_at((x, y), tuple(pixel))
    return surface


# ---------------------------------------------------------------------------- #
#                                     OTHER                                    #
# ---------------------------------------------------------------------------- #


def chunks(L, n):
    return [L[x: x + n] for x in range(0, len(L), n)]


def clamp(value: float, minimum_value: float, maximum_value: float) -> float:
    """
    Takes a value and returns it constrained to a certain range
    :param value: The input value
    :param minimum_value: Lower bound
    :param maximum_value: Upper bound
    :return: Clamped float.
    """
    if value < minimum_value:
        return minimum_value
    elif value > maximum_value:
        return maximum_value
    return value


def is_iterable(y):
    try:
        0 in y
    except TypeError:
        return False


def get_text_box_theme(theme_name=None):
    """Updates the name of the theme based on dark or light mode"""
    if game.settings["dark mode"]:
        if theme_name == "#allegiance":
            return '#allegiance_dark'
        return ObjectID("#dark", theme_name)
    else:
        return theme_name


def quit(savesettings=False, clearevents=False):
    """
    Quits the game, avoids a bunch of repeated lines
    """
    if savesettings:
        game.save_settings(None)
    if clearevents:
        game.cur_events_list.clear()
    game.rpc.close_rpc.set()
    game.rpc.update_rpc.set()
    pygame.display.quit()
    pygame.quit()
    if game.rpc.is_alive():
        game.rpc.join(1)
    sys_exit()


resource_directory = "resources/dicts/conditions/"
with open(os.path.normpath(f"{resource_directory}illnesses.json"), "r", encoding="utf-8") as read_file:
    ILLNESSES = ujson.loads(read_file.read())

with open(os.path.normpath(f"{resource_directory}injuries.json"), "r", encoding="utf-8") as read_file:
    INJURIES = ujson.loads(read_file.read())

with open(
        os.path.normpath(f"{resource_directory}permanent_conditions.json"), "r", encoding="utf-8"
) as read_file:
    PERMANENT = ujson.loads(read_file.read())

langs = {"snippet": None, "prey": None}

SNIPPETS = None
PREY_LISTS = None

with open(
        os.path.normpath("resources/dicts/backstories.json"), "r", encoding="utf-8"
) as read_file:
    BACKSTORIES = ujson.loads(read_file.read())
