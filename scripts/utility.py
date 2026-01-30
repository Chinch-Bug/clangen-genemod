# pylint: disable=line-too-long
"""

TODO: Docs


"""  # pylint: enable=line-too-long

import logging
import os
import re
import traceback
from itertools import combinations
from math import floor
from random import choice, choices, randint, random, sample, randrange, getrandbits
from sys import exit as sys_exit
from copy import deepcopy
from typing import List, Tuple, TYPE_CHECKING, Type, Union, Optional

import i18n
import pygame

from scripts.cat.phenotype import Phenotype
from scripts.cat.phenotype import Genotype

import ujson
from pygame_gui.core import ObjectID

from scripts.cat_relations.enums import RelType, RelTier, rel_type_tiers
from scripts.clan_package.settings import get_clan_setting
from scripts.game_structure.game.settings import game_settings_save, game_setting_get
from scripts.game_structure.game.switches import switch_get_value, Switch
from scripts.game_structure.localization import (
    load_lang_resource,
    determine_plural_pronouns,
    get_lang_config,
)

logger = logging.getLogger(__name__)
from scripts.special_dates import SpecialDate, is_today
from scripts.game_structure import image_cache, localization, constants
from scripts.cat.status import Status
from scripts.cat.enums import CatAge, CatRank, CatSocial, CatGroup, CatStanding, CatCompatibility
from scripts.cat.names import names
from scripts.cat.sprites import sprites
from scripts.game_structure import game
import scripts.game_structure.screen_settings  # must be done like this to get updates when we change screen size etc

if TYPE_CHECKING:
    from scripts.cat.cats import Cat


# ---------------------------------------------------------------------------- #
#                               Getting Cats                                   #
# ---------------------------------------------------------------------------- #


def get_alive_clan_queens(living_cats, clan:CatGroup=CatGroup.PLAYER_CLAN_ID):
    living_kits = [
        cat
        for cat in living_cats
        if cat.status.group_ID == clan and cat.status.rank.is_baby()
    ]

    queen_dict = {}
    for cat in living_kits.copy():
        parents = cat.get_parents()
        # Fetch parent object, only alive and not outside.
        parents = [
            cat.fetch_cat(i)
            for i in parents
            if cat.fetch_cat(i) and cat.fetch_cat(i).status.group_ID == clan
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


def find_alive_cats_with_rank(
    Cat: Union["Cat", Type["Cat"]],
    ranks: list,
    working: bool = False,
    sort: bool = False,
    clan: CatGroup = CatGroup.PLAYER_CLAN_ID
) -> list:
    """
    returns a list of cat objects for all living cats with a listed rank in Clan
    :param Cat Cat: Cat class
    :param list ranks: list of ranks to search for
    :param bool working: default False, set to True if you would like the list to only include working cats
    :param bool sort: default False, set to True if you would like list sorted by descending moon age
    """

    alive_cats = [
        i
        for i in Cat.all_cats.values()
        if i.status.rank in ranks and i.status.group_ID == clan
    ]

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


def get_living_clan_cat_count(Cat, clan=CatGroup.PLAYER_CLAN_ID):
    """
    Returns the int of all living cats within the Clan
    :param Cat: Cat class
    """
    count = 0
    for the_cat in Cat.all_cats.values():
        if the_cat.status.group_ID != clan:
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
        if inter_cat.status.group_ID != cat.status.group_ID:
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
        if inter_cat.status.group_ID != cat.status.group_ID:
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

def search_cats(search_text, cat_list, search_genotype):
    search_text = search_text.strip()
    all_found = cat_list.copy()
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
                "fourear": ["Dup", "dup"],
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
            polygenes = {
                "wbsum": ["wideband", "wb"],
                "rufsum": ["rufousing", "ruf"],
                "unders_rufsum": ["underbelly_rufousing", "underbelly_ruf"],
                "bengsum": ["bengal", "bm"],
                "soksum": ["sokoke", "sok"],
                "spotsum": ["spotted", "spot"],
                "ticksum": ["ticked_mod", "tick_md"],
                "saturation": ["saturation", "sat"],
                "refraction": ["refraction", "ref"],
                "pigmentation": ["pigmentation", "pig"],
                "whitegrade": ["whitegrade", "white_grade", "white"]
            }
            
            orgroups = search_text.split("/")
            all_found = []
            for g in orgroups:
                alleles = g.split("&")
                found_cats = cat_list.copy()
                for a in alleles:
                    find_poly = [
                        key for key, value in polygenes.items() if a.split(" ")[0].split(">")[0].split("<")[0].split("=")[0] in value]
                    if ">" in a or "<" in a or "=" in a and find_poly:
                        poly = find_poly[0]
                        operator = None
                        if "<=" in a:
                            operator = "<="
                        elif ">=" in a:
                            operator = ">="
                        elif "<" in a:
                            operator = "<"
                        elif ">" in a:
                            operator = ">"
                        elif ">" in a:
                            operator = ">"
                        elif "=" in a:
                            operator = "="
                        poly_value = a.split(operator, 1)[-1]

                        if poly_value.isdigit():
                            if operator == "<=":
                                found_cats = [
                                    cat
                                    for cat in found_cats
                                    if cat.phenotype[poly] <= int(poly_value) or (cat.chimerapheno and cat.chimerapheno[poly] <= int(poly_value))
                                ]
                            elif operator == ">=":
                                found_cats = [
                                    cat
                                    for cat in found_cats
                                    if cat.phenotype[poly] >= int(poly_value) or (cat.chimerapheno and cat.chimerapheno[poly] >= int(poly_value))
                                ]
                            elif operator == ">":
                                found_cats = [
                                    cat
                                    for cat in found_cats
                                    if cat.phenotype[poly] > int(poly_value) or (cat.chimerapheno and cat.chimerapheno[poly] > int(poly_value))
                                ]
                            elif operator == "<":
                                found_cats = [
                                    cat
                                    for cat in found_cats
                                    if cat.phenotype[poly] < int(poly_value) or (cat.chimerapheno and cat.chimerapheno[poly] < int(poly_value))
                                ]
                            elif operator == "=":
                                found_cats = [
                                    cat
                                    for cat in found_cats
                                    if cat.phenotype[poly] == int(poly_value) or (cat.chimerapheno and cat.chimerapheno[poly] == int(poly_value))
                                ]
                        
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
    if not game.clan:
        return "Newleaf"

    if constants.CONFIG["lock_season"]:
        game.clan.current_season = game.clan.starting_season
        return game.clan.starting_season

    modifiers = {
        "Newleaf": 0,
        "Greenleaf": 3,
        "Leaf-fall": 6,
        "Leaf-bare": 9
    }
    index = game.clan.age % 12 + modifiers[game.clan.starting_season]

    if index > 11:
        index = index - 12

    game.clan.current_season = constants.SEASON_CALENDAR[index]

    return game.clan.current_season


def change_clan_reputation(difference, clan):
    """
    will change the Clan's reputation with outsider cats according to the difference parameter.
    """
    clan.reputation += difference
    if clan.reputation < 0:
        clan.reputation = 0  # clamp to 0
    elif clan.reputation > 100:
        clan.reputation = 100  # clamp to 100


def change_clan_relations(clan, other_clan, difference):
    """
    will change the Clan's relation with other clans according to the difference parameter.
    """
    # grab the relation value for that clan
    clan_relations = game.clan.get_relations(clan, other_clan)
    # change the value
    clan_relations += difference
    # making sure it doesn't exceed the bounds
    if clan_relations > 30:
        clan_relations = 30
    elif clan_relations < 0:
        clan_relations = 0
    # setting it in the Clan save
    game.clan.set_relations(clan, other_clan, clan_relations)

def create_bio_parents(Cat, flip=False, second_parent=True, clan=None):
    ages = [randint(15,120), 0]
    ages[1] = ages[0] + randint(0, 24) - 12
    original_social = choice([CatSocial.KITTYPET, CatSocial.LONER, CatSocial.ROGUE])
    thought = None
    if clan:
        original_social = CatSocial.CLANCAT
        thought = i18n.t("hardcoded.thought_kit_dead")
    
    blood_parent2 = None
    par2geno = None
    blood_parent = create_new_cat(Cat,
                                    original_social=original_social,
                                    original_group=clan,
                                    alive=choice([True, True, True, False]) if clan else choice([True, False]),
                                    moons=ages[0],
                                    gender='fem' if flip else 'masc',
                                    outside=True,
                                    is_parent=True)[0]
    while 'sterile' in blood_parent.permanent_condition:
        if(blood_parent):
            del Cat.all_cats[blood_parent.ID]
        blood_parent = create_new_cat(Cat,
                                    original_social=original_social,
                                    original_group=clan,
                                    alive=choice([True, True, True, False]) if clan else choice([True, False]),
                                    moons=ages[0],
                                    gender='fem' if flip else 'masc',
                                    outside=True,
                                    is_parent=True)[0]
    if second_parent:
        original_social = choice([CatSocial.KITTYPET, CatSocial.LONER, CatSocial.ROGUE])
        if clan:
            original_social = CatSocial.CLANCAT
        blood_parent2 = create_new_cat(Cat,
                                    original_social=original_social,
                                    original_group=clan,
                                    alive=choice([True, True, True, False]) if clan else choice([True, False]),
                                    moons=ages[1] if ages[1] > 14 else 15,
                                    gender='masc' if flip else 'fem',
                                    outside=True,
                                    is_parent=True)[0]
        while 'sterile' in blood_parent2.permanent_condition:
            if blood_parent2 and Cat.all_cats[blood_parent2.ID]:
                del Cat.all_cats[blood_parent2.ID]
            blood_parent2 = create_new_cat(Cat,
                                           original_social=original_social,
                                           original_group=clan,
                                           alive=choice(
                                               [True, True, True, False]) if clan else choice([True, False]),
                                            moons=ages[0],
                                            gender='masc' if flip else 'fem',
                                            outside=True,
                                            is_parent=True)[0]
    else:
        par2geno = Genotype(constants.CONFIG['genetics_config'], game_setting_get("ban problem genes"))
        par2geno.Generator('masc' if flip else 'fem')

    if thought:
        if blood_parent:
            blood_parent.thought = event_text_adjust(Cat, thought, main_cat = blood_parent)
            
            if blood_parent.status.rank == CatRank.MEDICINE_CAT:
                blood_parent.backstory = choice(["medicine_cat", "disgraced1"])
            else:
                blood_parent.backstory = choice(
                    BACKSTORIES["backstory_categories"].get(f"former_clancat_backstories", ["outsider1"])
                )
        if blood_parent2:
            blood_parent2.thought = event_text_adjust(Cat, thought, main_cat = blood_parent2)
            if blood_parent2.status.rank == CatRank.MEDICINE_CAT:
                blood_parent2.backstory = choice(["medicine_cat", "disgraced1"])
            else:
                blood_parent2.backstory = choice(
                    BACKSTORIES["backstory_categories"].get(f"former_clancat_backstories", ["outsider1"])
                )

    return [blood_parent, blood_parent2, par2geno]

def create_new_cat_block(
    Cat: Optional["Cat"],
    Relationship,
    event,
    in_event_cats: dict,
    i: int,
    attribute_list: List[str], 
    clan=None,
    other_clan=None,
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
                if in_event_cats[index].status.rank.is_any_apprentice_rank():
                    print("Can't give apprentices mates")
                    continue

                give_mates.append(in_event_cats[index])

    # determine gender
    if "male" in attribute_list:
        gender = "male"
    elif "female" in attribute_list:
        gender = "female"
    elif "can_birth" in attribute_list and not get_clan_setting("same sex birth"):
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

    # RANK - must be handled before backstories
    rank = None
    for _tag in attribute_list:
        match = re.match(r"status:\s?(.+)", _tag)
        if not match:
            continue

        elif match.group(1) in (
            CatRank.DEPUTY,
            CatRank.LEADER
        ):
            rank = CatRank.WARRIOR
            break
        elif match.group(1) in [
            CatRank.NEWBORN,
            CatRank.KITTEN,
            CatRank.ELDER,
            CatRank.APPRENTICE,
            CatRank.WARRIOR,
            CatRank.MEDIATOR_APPRENTICE,
            CatRank.MEDIATOR,
            CatRank.MEDICINE_APPRENTICE,
            CatRank.MEDICINE_CAT,
        ]:
            rank = match.group(1)
            break

    # SET AGE
    age = None
    for _tag in attribute_list:
        match = re.match(r"age:\s?(.+)", _tag)
        if not match:
            continue

        if match.group(1) in Cat.age_moons:
            min_age, max_age = Cat.age_moons[CatAge(match.group(1))]
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

    if not rank and not age and "meeting" not in attribute_list:
        rank = choice([CatRank.WARRIOR, CatRank.WARRIOR, CatRank.WARRIOR, CatRank.APPRENTICE])
    if rank and not age:
        if rank in [
            CatRank.APPRENTICE,
            CatRank.MEDIATOR_APPRENTICE,
            CatRank.MEDICINE_APPRENTICE,
        ]:
            age = randint(
                Cat.age_moons[CatAge.ADOLESCENT][0],
                Cat.age_moons[CatAge.ADOLESCENT][1],
            )
        elif rank in [CatRank.WARRIOR, CatRank.MEDIATOR, CatRank.MEDICINE_CAT]:
            age = randint(
                Cat.age_moons["young adult"][0], Cat.age_moons["senior adult"][1]
            )
        elif rank == CatRank.ELDER:
            age = randint(Cat.age_moons["senior"][0], Cat.age_moons["senior"][1])

    cat_group = None

    if "kittypet" in attribute_list:
        cat_social = CatSocial.KITTYPET
    elif "rogue" in attribute_list:
        cat_social = CatSocial.ROGUE
    elif "loner" in attribute_list:
        cat_social = CatSocial.LONER
    elif "clancat" in attribute_list or "former Clancat" in attribute_list:
        cat_social = CatSocial.CLANCAT
        if other_clan:
            cat_group = other_clan.group_ID
        else:
            cat_group = choice([x.group_ID for x in game.clan.all_other_clans])
    else:
        if game.clan.clancount == "multiclan":
            cat_social = choice([CatSocial.KITTYPET, CatSocial.LONER])
        else:
            cat_social = choice([CatSocial.KITTYPET, CatSocial.LONER, CatSocial.CLANCAT])

    # LITTER
    litter = False
    if "litter" in attribute_list:
        litter = True
        if rank not in (CatRank.KITTEN, CatRank.NEWBORN):
            rank = CatRank.KITTEN
        if rank == CatRank.NEWBORN:
            age = 0
        else:
            age = randint(
                Cat.age_moons[CatAge.KITTEN][0],
                Cat.age_moons[CatAge.KITTEN][1],
            )

    # CHOOSE DEFAULT BACKSTORY BASED ON CAT TYPE, STATUS
    if rank in (CatRank.KITTEN, CatRank.NEWBORN):
        chosen_backstory = choice(
            BACKSTORIES["backstory_categories"]["abandoned_backstories"]
        )
    elif rank == CatRank.MEDICINE_CAT and cat_social == CatSocial.CLANCAT:
        chosen_backstory = choice(["medicine_cat", "disgraced1"])
    elif rank == CatRank.MEDICINE_CAT:
        chosen_backstory = choice(["wandering_healer1", "wandering_healer2"])
    else:
        if cat_social == CatSocial.CLANCAT:
            x = "former_clancat"
        else:
            x = cat_social
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

        if (
            chosen_backstory
            in BACKSTORIES["backstory_categories"]["baby_clancat_backstories"] + 
            BACKSTORIES["backstory_categories"]["former_clancat_backstories"]
            or (game.clan.clancount == "multiclan" and "clancat" in attribute_list)
        ):
            cat_social = CatSocial.CLANCAT
        elif chosen_backstory in (
            BACKSTORIES["backstory_categories"]["baby_loner_backstories"]
            + BACKSTORIES["backstory_categories"]["loner_backstories"]
        ):
            cat_social = CatSocial.LONER
        elif chosen_backstory in (
            BACKSTORIES["backstory_categories"]["baby_kittypet_backstories"]
            + BACKSTORIES["backstory_categories"]["kittypet_backstories"]
        ):
            cat_social = CatSocial.KITTYPET
        elif (
            chosen_backstory in BACKSTORIES["backstory_categories"]["rogue_backstories"]
        ):
            cat_social = CatSocial.ROGUE

    # KITTEN THOUGHT
    if rank in (CatRank.KITTEN, CatRank.NEWBORN):
        thought = i18n.t("hardcoded.thought_new_kitten")

    # MEETING - DETERMINE IF THIS IS AN OUTSIDE CAT
    outside = False
    if "meeting" in attribute_list:
        outside = True
        if game.clan.clancount != "multiclan" or "clancat" not in attribute_list:
            new_name = False
            rank = None
            thought = i18n.t("hardcoded.thought_meeting")
            if age is not None and age <= 6 and not bs_override:
                chosen_backstory = "outsider1"

    # IS THE CAT DEAD?
    alive = True
    if "dead" in attribute_list:
        alive = False
        thought = i18n.t("hardcoded.thought_new_dead")

    # check if we can use an existing cat here
    chosen_cat: Optional["Cat"] = None
    if "exists" in attribute_list:
        existing_outsiders = [
            i for i in Cat.all_cats.values() if i.status.is_outsider and not i.dead and i.status.is_near() and not i.status.is_lost()
        ]
        possible_outsiders = []
        for cat in existing_outsiders:
            if stor and cat.backstory not in stor:
                continue
            if cat_social != cat.status.social:
                continue
            if gender and gender != cat.gender:
                continue
            if age and age not in Cat.age_moons[cat.age]:
                continue
            already_picked = False
            for picked_cats in event.new_cats:
                if cat in picked_cats:
                    already_picked = True
                    break
            if already_picked:
                continue
            possible_outsiders.append(cat)

        if possible_outsiders:
            chosen_cat = choice(possible_outsiders)
            if not alive:
                chosen_cat.die()
            elif not outside:
                if not rank:
                    rank = chosen_cat.status.get_rank_from_age(chosen_cat.age)
                chosen_cat.add_to_clan(clan.group_ID)
                if chosen_cat.status.rank != rank:
                    chosen_cat.rank_change(new_rank=CatRank(rank), resort=True)
            elif outside:
                # updates so that the clan is marked as knowing of this cat
                current_standing = chosen_cat.status.get_standing_with_group(
                    clan.group_ID
                )
                if (
                    CatStanding.KNOWN not in current_standing
                    and CatStanding.EXILED not in current_standing
                ):
                    chosen_cat.status.change_standing(CatStanding.KNOWN)

            if new_name:
                name = f"{chosen_cat.name.prefix}"

                chosen_cat.history.prev_names.append(str(chosen_cat.name))
                spaces = name.count(" ")
                if bool(getrandbits(1)):
                    if spaces > 0:  # adding suffix to OG name
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
        if rank in (CatRank.KITTEN, CatRank.NEWBORN) or age in range(Cat.age_moons[CatAge.KITTEN][0], Cat.age_moons[CatAge.KITTEN][1]+1) or parent1:
            generated_parents = create_bio_parents(Cat, flip=True if parent1 and 'Y' in parent1.phenotype.sexgene else False, second_parent=not parent1, clan=cat_group)
            if not parent1:
                parent1 = generated_parents[1]
            if not parent2:
                parent2 = generated_parents[0]
        new_cats = create_new_cat(
            Cat,
            new_name=new_name,
            kit=False if litter else rank in (CatRank.KITTEN, CatRank.NEWBORN) or age in range(
                Cat.age_moons[CatAge.KITTEN][0], Cat.age_moons[CatAge.KITTEN][1]+1),
            # this is for singular kits, litters need this to be false
            litter=litter,
            backstory=chosen_backstory,
            rank=rank,
            original_social=cat_social,
            original_group=cat_group,
            moons=age,
            gender=gender,
            thought=thought,
            alive=alive,
            outside=outside,
            group=clan.group_ID,
            parent1=parent1.ID if parent1 else None,
            parent2=parent2.ID if parent2 else None,
            extrapar=generated_parents[2] if not parent2 and generated_parents else None,
            is_parent= "age:has_kits" in attribute_list,
            adoptive_parents=adoptive_parents if adoptive_parents else None
            )
        while "age:has_kits" in attribute_list and "sterile" in new_cats[0].permanent_condition:
            del Cat.all_cats[new_cats[0].ID]
            new_cats[0] = create_new_cat(
                Cat,
                new_name=new_name,
                kit=False if litter else rank in (CatRank.KITTEN, CatRank.NEWBORN),
                litter=litter,
                backstory=chosen_backstory,
                rank=rank,
                original_social=cat_social,
                original_group=cat_group,
                moons=age,
                gender=gender,
                thought=thought,
                alive=alive,
                outside=outside,
                group=clan.group_ID,
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
                start_relation.like += 40 + y
                start_relation.comfort = 40 + y
                start_relation.respect = 10 + y
                start_relation.trust = 30 + y
                n_c.relationships[inter_cat.ID] = start_relation

            # BIO PARENTS
            for par in (parent1, parent2):
                if not par:
                    continue

                y = randrange(0, 20)
                start_relation = Relationship(par, n_c, False, True)
                start_relation.like += 60 + y
                start_relation.comfort = 40 + y
                start_relation.respect = 30 + y
                start_relation.trust = 30 + y
                par.relationships[n_c.ID] = start_relation

                y = randrange(0, 20)
                start_relation = Relationship(n_c, par, False, True)
                start_relation.like += 40 + y
                start_relation.comfort = 70 + y
                start_relation.respect = 30 + y
                start_relation.trust = 60 + y
                n_c.relationships[par.ID] = start_relation

            # ADOPTIVE PARENTS
            for par in adoptive_parents:
                if not par:
                    continue

                par = Cat.fetch_cat(par)

                y = randrange(0, 20)
                start_relation = Relationship(par, n_c, False, True)
                start_relation.like += 60 + y
                start_relation.comfort = 40 + y
                start_relation.respect = 30 + y
                start_relation.trust = 30 + y
                par.relationships[n_c.ID] = start_relation

                y = randrange(0, 20)
                start_relation = Relationship(n_c, par, False, True)
                start_relation.like += 40 + y
                start_relation.comfort = 70 + y
                start_relation.respect = 30 + y
                start_relation.trust = 60 + y
                n_c.relationships[par.ID] = start_relation

            # UPDATE INHERITANCE
            n_c.create_inheritance_new_cat()

    return new_cats


def find_clan_cats(Cat, Relationship, event, in_event_cats: dict, i: int, attribute_list: List[str], clan=None, other_clan=None):
    status = None
    age = None
    adoptive_parents = []
    blood_parent = None
    give_mates = []
    picked_cats = []
    chosen_backstory = None
    
    all_clan_cats = []
    if "exiled" in attribute_list:
        all_clan_cats = [i for i in Cat.all_cats.values() if i.status.is_exiled() and i.status.is_exiled() != clan.group_ID]
    if not all_clan_cats:
        all_clan_cats = [i for i in Cat.all_cats.values() if i.status.group_ID == other_clan.group_ID]

    for a in attribute_list:
        match = re.match(r'status:\s?(.+)', a)
        if match:
            status = match.group(1)
        match = re.match(r'age:\s?(.+)', a)
        if match:
            age = match.group(1)
        match = re.match(r"parent:\s?(.+)", a)
        if match:
            blood_parent = in_event_cats[match.group(1)]
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
                if in_event_cats[index].status.rank.is_any_apprentice_rank():
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
        (parents, orphans) = get_alive_clan_queens(all_clan_cats, clan=other_clan.group_ID)
        if blood_parent:
            picked_cats = parents[blood_parent.ID]
        elif parents:
            litter = parents[choice(list(parents.keys()))]
            picked_cats = litter
        else:
            picked_cats = [choice(orphans)]
    else:
        if status == "any_apprentice":
            all_clan_cats = [cat for cat in all_clan_cats if cat.status.rank.is_any_apprentice_rank()]
        elif status == "any_healer":
            all_clan_cats = [cat for cat in all_clan_cats if cat.status.rank.is_any_medicine_rank()]
        elif status:
            all_clan_cats = [cat for cat in all_clan_cats if cat.status.rank.value == status]
        
        if age == "match":
            all_clan_cats_age = [cat for cat in all_clan_cats if cat.age == in_event_cats["m_c"].age]
            if all_clan_cats_age:
                all_clan_cats = all_clan_cats_age
        elif age == "mate":
            all_clan_cats = [cat for cat in all_clan_cats if give_mates[0].is_potential_mate(cat, for_love_interest=True, outsider=True)]
            if not all_clan_cats:
                print("No possible mates found")
                all_clan_cats = create_new_cat_block(Cat, Relationship, event, in_event_cats, i, attribute_list, other_clan = other_clan)
        elif age == "has_kits":
            (parents, orphans) = get_alive_clan_queens(all_clan_cats, clan=other_clan.group_ID)
            for par_id in parents.keys():
                if Cat.fetch_cat(par_id) not in all_clan_cats:
                    del parents[par_id]
            all_clan_cats = [Cat.fetch_cat(par_id) for par_id in parents.keys()]
        elif age:
            all_clan_cats_age = [cat for cat in all_clan_cats if cat.age.value == age]
            if all_clan_cats_age:
                all_clan_cats = all_clan_cats_age
        if not all_clan_cats:
            all_clan_cats = [i for i in Cat.all_cats.values() if i.status.group_ID == other_clan.group_ID]
        picked_cats = [choice(all_clan_cats)]

    if "change_clan" in attribute_list:
        for cat in picked_cats:
            other = cat.status.fetch_clan_object()
            if cat.status.rank == CatRank.LEADER:
                other.leader = None
                other.leader_lives = 0
            if cat.status.rank == CatRank.DEPUTY:
                other.deputy = None
            if cat.status.rank == CatRank.MEDICINE_CAT:
                other.remove_med_cat(cat)
            if cat.status.rank in [CatRank.LEADER, CatRank.DEPUTY]:
                cat.status._change_rank(CatRank.WARRIOR)

            if "rogue" in attribute_list:
                cat.become_lost(CatSocial.ROGUE)
            else:
                cat.status.add_to_group(clan.group_ID, standing_with_past_group=CatStanding.LEFT)
            for app in cat.apprentice.copy():
                app_ob = Cat.fetch_cat(app)
                if app_ob:
                    app_ob.update_mentor()

            cat.update_mentor()
    elif "change_clan_rev" in attribute_list:
        other = give_mates[0].status.fetch_clan_object()
        give_mates[0].status.add_to_group(other_clan.group_ID, standing_with_past_group=CatStanding.LEFT)
        if give_mates[0].status.rank == CatRank.LEADER:
            other.leader = None
            other.leader_lives = 0
        if give_mates[0].status.rank == CatRank.DEPUTY:
            other.deputy = None
        if give_mates[0].rank == CatRank.MEDICINE_CAT:
            other.remove_med_cat(cat)
        if give_mates[0].status.rank in [CatRank.LEADER, CatRank.DEPUTY]:
            give_mates[0].status._change_rank(CatRank.WARRIOR)
    
    if "dead" in attribute_list:
        for cat in picked_cats:
            cat.die()

    for cat in picked_cats:
        if chosen_backstory:
            cat.backstory = chosen_backstory
            cat.history.add_beginning()
        
        # SET MATES
        for inter_cat in give_mates:
            if cat == inter_cat or cat.ID in inter_cat.mate:
                continue

            # this is some duplicate work, since this triggers inheritance re-calcs
            # TODO: optimize
            cat.set_mate(inter_cat)

        # ADOPTIVE PARENTS
        for par in adoptive_parents:
            if not par:
                continue

            cat.adoptive_parents.append(par)
            par = Cat.fetch_cat(par)

            y = randrange(0, 20)
            start_relation = Relationship(par, cat, False, True)
            start_relation.like += 30 + y
            start_relation.comfortable = 10 + y
            start_relation.respect = 15 + y
            start_relation.trust = 10 + y
            par.relationships[cat.ID] = start_relation

            y = randrange(0, 20)
            start_relation = Relationship(cat, par, False, True)
            start_relation.like += 30 + y
            start_relation.comfortable = 10 + y
            start_relation.respect = 15 + y
            start_relation.trust = 10 + y
            cat.relationships[par.ID] = start_relation

        if adoptive_parents:
            cat.create_inheritance_new_cat()

    return picked_cats


def get_other_clan(clan_name):
    """
    returns the clan object of given clan name
    """
    for clan in game.clan.all_other_clans:
        if clan.displayname == clan_name:
            return clan


def create_new_cat(
    Cat: Union["Cat", Type["Cat"]],
    new_name: bool = False,
    kit: bool = False,
    litter: bool = False,
    backstory: bool = None,
    rank: Optional[CatRank] = None,
    original_social: CatSocial = CatSocial.CLANCAT,
    original_group: CatGroup = None,
    moons: int = None,
    gender: str = None,
    thought: str = None,
    alive: bool = True,
    outside: bool = False,
    group:CatGroup = None,
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
    :param bool kit: set True if the cat is a lone kitten - default: False
    :param bool litter: set True if a litter of kittens needs to be generated - default: False
    :param bool backstory: a list of possible backstories.json for the new cat(s) - default: None
    :param rank: set as the rank you want the new cat to have - default: None (will cause a random status to be picked)
    :param original_social: set as the cat's old social - default: None (cat will not be given any past social, it will
    appear that they have always been a clancat)
    :param original_group: set as the cat's old group - default: None (cat will not be given any past group)
    :param bool outside: set this as True to generate the cat as an outsider instead of as part of the Clan - default: False (Clan cat)
    :param int moons: set the age of the new cat(s) - default: None (will be random or if kit/litter is true, will be kitten.
    :param str gender: set the gender (BIRTH SEX) of the cat - default: None (will be random)
    :param str thought: if you need to give a custom "welcome" thought, set it here
    :param bool alive: set this as False to generate the cat as already dead - default: True (alive)
    :param str parent1: Cat ID to set as the biological parent1
    :param str parent2: Cat ID to set as the biological parent2
    :param list adoptive_parents: Cat IDs to set as adoptive parents
    """

    if thought is None:
        thought = i18n.t("hardcoded.thought_new_cat")

    if backstory is None:
        if original_social == CatSocial.KITTYPET:
            backstory = BACKSTORIES["backstory_categories"]["kittypet_backstories"]
        if original_social == CatSocial.ROGUE:
            backstory = BACKSTORIES["backstory_categories"]["rogue_backstories"]
        if original_social == CatSocial.LONER:
            backstory = BACKSTORIES["backstory_categories"]["loner_backstories"]
    if isinstance(backstory, list):
        backstory = choice(backstory)

    if (
        backstory
        in (
            BACKSTORIES["backstory_categories"]["former_clancat_backstories"]
            + BACKSTORIES["backstory_categories"]["baby_clancat_backstories"]
        ) 
        and original_social == CatSocial.CLANCAT
        and not original_group
    ):
        original_group = choice([x.group_ID for x in game.clan.all_other_clans])

    created_cats = []

    if not litter:
        number_of_cats = 1
    else:
        number_of_cats = choices([2, 3, 4, 5], [5, 4, 1, 1], k=1)[0]

    if (litter or kit):
        parent_thought = i18n.t("conditions.pregnancy.half_blood_kitting_thought", count=number_of_cats)
        if Cat.all_cats[parent1].status.is_outsider:
            Cat.all_cats[parent1].thought = event_text_adjust(Cat, parent_thought, main_cat=Cat.all_cats[parent1])
        if Cat.all_cats[parent2].status.is_outsider:
            Cat.all_cats[parent2].thought = event_text_adjust(Cat, parent_thought, main_cat=Cat.all_cats[parent2])
    

    if not isinstance(moons, int):
        if rank == CatRank.NEWBORN:
            moons = 0
        elif litter or kit:
            moons = randint(1, 5)
        elif rank in (
            CatRank.APPRENTICE,
            CatRank.MEDICINE_APPRENTICE,
            CatRank.MEDIATOR_APPRENTICE,
        ):
            moons = randint(6, 11)
        elif rank == CatRank.WARRIOR:
            moons = randint(23, 120)
        elif rank == CatRank.MEDICINE_CAT:
            moons = randint(23, 140)
        elif rank == CatRank.ELDER:
            moons = randint(120, 130)
        else:
            moons = randint(6, 120)

    # setting rank
    if not rank and not outside:
        if moons == 0:
            rank = CatRank.NEWBORN
        elif moons < 6:
            rank = CatRank.KITTEN
        elif 6 <= moons <= 11:
            rank = CatRank.APPRENTICE
        elif moons >= 120:
            rank = CatRank.ELDER
        else:
            rank = CatRank.WARRIOR

    # need to get actual age enum
    age = CatAge.SENIOR
    for key_age in Cat.age_moons.keys():
        if moons in range(Cat.age_moons[key_age][0], Cat.age_moons[key_age][1] + 1):
            age: CatAge = key_age
            break

    # cat creation and naming time
    for index in range(number_of_cats):
        # setting gender
        if not gender:
            _gender = choice(['fem', 'masc'])
        else:
            _gender = gender

        # first we generate the cat as though they are not part of the clan yet
        new_cat = Cat(
            moons=moons,
            status_dict={
                "social": original_social,
                "age": age,
                "group_ID": original_group,
            },
            gender=_gender,
            backstory=backstory,
            parent1=parent1,
            parent2=parent2,
            extrapar=extrapar,
            adoptive_parents=adoptive_parents if adoptive_parents else [],
        )
        

        if new_cat.phenotype.manx[1] == "Ab" or new_cat.phenotype.sexgene[0] == "Y" or new_cat.phenotype.manx[1] == "M" or new_cat.phenotype.munch[1] == "Mk" or ('NoDBE' not in new_cat.phenotype.pax3 and 'DBEalt' not in new_cat.phenotype.pax3):
            if len(created_cats) == 0:
                while new_cat.phenotype.manx[1] == "Ab" or new_cat.phenotype.sexgene[0] == "Y" or new_cat.phenotype.manx[1] == "M" or new_cat.phenotype.munch[1] == "Mk" or ('NoDBE' not in new_cat.phenotype.pax3 and 'DBEalt' not in new_cat.phenotype.pax3):
                    del Cat.all_cats[new_cat.ID]
                    new_cat = Cat(
                        moons=moons,
                        status_dict={
                            "social": original_social,
                            "age": age,
                            "group_ID": original_group,
                        },
                        gender=_gender,
                        backstory=backstory,
                        parent1=parent1,
                        parent2=parent2,
                        extrapar=extrapar,
                        adoptive_parents=adoptive_parents if adoptive_parents else [],
                    )
            else:
                new_cat.moons = 0
                new_cat.status = Status(**{"group_ID": new_cat.status.group_ID,
                                "rank": CatRank.NEWBORN, "age": CatAge.NEWBORN})
                new_cat.dead = True
                new_cat.thoughts(just_died=True)
                new_cat.history.add_death(str(new_cat.name) + " was stillborn.")
        # this simulates a "history" as whomever they used to be
        new_cat.status.change_current_moons_as(moons)

        # now we actually add them to the clan, if they should be joining
        if not outside and alive:
            new_cat.add_to_clan(group)
            # check if cat is the correct rank
            if new_cat.status.rank != rank:
                new_cat.status._change_rank(CatRank(rank))
            # give apprentice aged cat a mentor
            if new_cat.status.rank.is_any_apprentice_rank():
                new_cat.update_mentor()
                # ensuring that any cats joining as an apprentice will display the correct skills
                new_cat.skills.primary.interest_only = True
                if new_cat.skills.secondary:
                    new_cat.skills.secondary.interest_only = True

        # NAMES and accs
        # clancat adults should have already generated with a clan-ish name, thus they skip all of this re-naming
        # little babies will take a clancat name, we love indoctrination
        if not outside and (kit or litter or moons < 12) and (not original_group or not game.used_group_IDs[original_group].is_any_clan_group()):
            # babies change name, in case their initial name isn't clan-ish
            new_cat.change_name()
        elif not original_group or not game.used_group_IDs[original_group].is_any_clan_group():
            # give kittypets a kittypet name
            overwrite_prefix = False
            if original_social == CatSocial.KITTYPET:
                name = choice(names.names_dict["loner_names"])
                # check if the kittypets come with a pretty acc
                if bool(getrandbits(1)):
                    # TODO: refactor this entire function to remove this call amongst other things
                    from scripts.cat.pelts import Pelt

                    new_cat.pelt.accessory.append(choice(Pelt.collar_accessories))

            # try to give name from full loner name list
            elif original_social in (CatSocial.LONER, CatSocial.ROGUE) and bool(
                getrandbits(1)
            ):
                name = choice(names.names_dict["loner_names"])
            # otherwise give name from prefix list (more nature-y names)
            else:
                name = choice(names.names_dict["normal_prefixes"])
                if get_clan_setting("modded names") and get_clan_setting('new prefixes') and random() < 0.9:
                    overwrite_prefix = True

                # now, if this cat should take a new clan name, we give them such
            if new_name:
                # check if adding suffix to OG name
                if bool(getrandbits(1)):
                    spaces = name.count(" ")
                    if spaces > 0:
                        # make a list of the words within the name, then add the OG name back in the list
                        words = name.split(" ")
                        words.append(name)
                        new_prefix = choice(words)  # pick new prefix from that list
                        new_cat.change_name(new_prefix=new_prefix)
                # else, take a whole new name
                else:
                    new_cat.change_name()
            # else, let them keep their old name
            else:
                new_cat.change_name(new_prefix=name, new_suffix="")
                if overwrite_prefix:
                    new_cat.name.give_prefix(Cat, game.clan.biome, no_suffix=True)

        # Remove disabling scars, if they generated.
        # these are removed bc the cat won't have the associated perm condition
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
                constants.CONFIG["cat_generation"]["base_permanent_condition"] / 11.25
            )
        else:
            chance = constants.CONFIG["cat_generation"]["base_permanent_condition"]
        
        if not is_parent and get_clan_setting('tnr_mode') and moons > 5:
            kittypet_n = constants.CONFIG['tnr_mode']['kittypet_neuter']
            loner_n = constants.CONFIG['tnr_mode']['loner_tnr']
            if original_social == CatSocial.KITTYPET and random() < kittypet_n:
                new_cat.get_permanent_condition("sterile", False)
            if original_social in (CatSocial.LONER, CatSocial.ROGUE) and random() < loner_n:
                new_cat.get_permanent_condition("sterile", False)
                new_cat.pelt.scars.append("TNR")
                new_cat.pelt.rebuild_sprite = True
        if not int(random() * chance):
            possible_conditions = []
            for condition in PERMANENT:
                if (kit or litter) and PERMANENT[condition]["congenital"] not in [
                    "always",
                    "sometimes",
                ]:
                    continue
                if condition in ['manx syndrome', "flat nose", 'ocular albinism', 'albinism', 'rabbit gait', 'fully hairless', 'partially hairless', "bad back", "narrowed chest", "bumpy skin"]:
                    continue
                # next part ensures that a kit won't get a condition that takes too long to reveal
                moons = new_cat.moons
                leeway = 5 - (PERMANENT[condition]["moons_until"] + 1)
                if moons > leeway:
                    continue
                possible_conditions.append(condition)

            if possible_conditions:
                chosen_condition = choice(possible_conditions)
                if PERMANENT[chosen_condition]["congenital"] in [
                    "always",
                    "sometimes",
                ]:
                    new_cat.get_permanent_condition(chosen_condition, True)
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
            if new_cat.status.social is not CatSocial.CLANCAT:
                new_cat.name.suffix = ""
        if not alive:
            new_cat.die()

        # newbie thought
        new_cat.thought = thought

        # and they exist now
        created_cats.append(new_cat)
        game.clan.add_cat(new_cat)
        new_cat.history.add_beginning()

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
        if rel.romance < 0:
            continue
        if exclude_mate and rel.cat_from.ID in rel.cat_to.mate:
            continue
        if potential_mate and not rel.cat_to.is_potential_mate(
            rel.cat_from, for_love_interest=True
        ):
            continue
        if rel.romance > max_love_value:
            current_max_relationship = rel
            max_love_value = rel.romance

    return current_max_relationship


def check_relationship_value(cat_from, cat_to, rel_value=None):
    """
    returns the value of the rel_value param given
    :param cat_from: the cat who is having the feelings
    :param cat_to: the cat that the feelings are directed towards
    :param rel_value: the relationship value that you're looking for,
    options are: romance, like, respect, comfort, trust
    """
    if cat_to.ID in cat_from.relationships:
        relationship = cat_from.relationships[cat_to.ID]
    else:
        return 0

    if rel_value == RelType.ROMANCE:
        return relationship.romance
    elif rel_value == RelType.LIKE:
        return relationship.like
    elif rel_value == RelType.RESPECT:
        return relationship.respect
    elif rel_value == RelType.COMFORT:
        return relationship.comfort
    elif rel_value == RelType.TRUST:
        return relationship.trust

    return None


def get_personality_compatibility(cat1, cat2):
    """
    Returns matching CatCompatibility enum according to personalitiesof given cat objects.
    :param cat1: Cat object of first cat
    :param cat2: Cat object of second cat
    """
    personality1 = cat1.personality.trait
    personality2 = cat2.personality.trait

    if personality1 == personality2:
        if personality1 is None:
            return CatCompatibility.NEUTRAL
        return CatCompatibility.POSITIVE

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
        return CatCompatibility.POSITIVE
    if running_total <= -2:
        return CatCompatibility.NEGATIVE

    return CatCompatibility.NEUTRAL


def get_cats_of_romantic_interest(cat):
    """Returns a list of cats, those cats are love interest of the given cat"""
    cats = []
    for inter_cat in cat.all_cats.values():
        if inter_cat.status.group_ID != cat.status.group_ID:
            continue
        if inter_cat.ID == cat.ID:
            continue

        if inter_cat.ID not in cat.relationships:
            continue

        # Extra check to ensure they are potential mates
        if (
            inter_cat.is_potential_mate(cat, for_love_interest=True)
            and cat.relationships[inter_cat.ID].romance > 0
        ):
            cats.append(inter_cat)
    return cats


def get_num_of_cats_with_relation_amount_towards(cat, amount, all_cats):
    """
    Looks how many cats have the certain value
    :param cat: cat in question
    :param amount: amount of relationship value which has to be reached
    :param all_cats: list of cats which has to be checked
    """

    # collect all true or false if the value is reached for the cat or not
    # later count or sum can be used to get the amount of cats
    # this will be handled like this, because it is easier / shorter to check

    relation_dict = {v: [] for v in [*RelType]}

    for inter_cat in all_cats:
        if cat.ID in inter_cat.relationships:
            relation = inter_cat.relationships[cat.ID]
        else:
            continue

        for value in [*RelType]:
            if amount > 0:
                relation_dict[value].append(
                    relation.get_amount_of_type(value) >= amount
                )
            elif amount < 0:
                relation_dict[value].append(
                    relation.get_amount_of_type(value) <= amount
                )

    return_dict = {v: sum(relation_dict[v]) for v in [*RelType]}

    return return_dict


def filter_relationship_type(
    group: list, filter_types: List[str], event_id: str = None, patrol_leader=None
):
    """
    filters for specific types of relationships between groups of cat objects, returns bool
    :param group: the group of cats to be tested (make sure they're in the correct order (i.e. if testing for
    parent/child, the cat being tested as parent must be index 0)
    :param filter_types: the relationship types to check for.
    :param event_id: if the event has an ID, include it here
    :param patrol_leader: if you are testing a patrol, ensure you include the self.patrol_leader here
    """
    if not filter_types:
        return True

    filter_list = filter_types.copy()

    # keeping this list here just for quick reference of what tags are handled here
    all_possible_tags = [
        "siblings",
        "not_siblings",
        "littermates",
        "not_littermates",
        "mates",
        "mates_with_pl",
        "not_mates",
        "parent/child",
        "not_parent",
        "child/parent",
        "not_child",
        "mentor/app",
        "not_mentor",
        "app/mentor",
        "not_app",
    ]
    for tier_list in rel_type_tiers.values():
        all_possible_tags.extend(tier_list)
        all_possible_tags.extend([f"{l}_only" for l in tier_list])
    if not set(filter_list).issubset(set(all_possible_tags)):
        print(
            f"WARNING: {[tag for tag in filter_list if tag not in all_possible_tags]} is not a valid relationship_status tag!"
        )

    if patrol_leader:
        if patrol_leader in group:
            group.remove(patrol_leader)
        group.insert(0, patrol_leader)

    if "siblings" in filter_list:
        test_cat = group[0]
        testing_cats = [cat for cat in group if cat.ID != test_cat.ID]

        if not all([test_cat.is_sibling(inter_cat) for inter_cat in testing_cats]):
            return False
        filter_list.remove("siblings")

    if "not_siblings" in filter_list:
        test_cat = group[0]
        testing_cats = [cat for cat in group if cat.ID != test_cat.ID]

        if any([test_cat.is_sibling(inter_cat) for inter_cat in testing_cats]):
            return False
        filter_list.remove("not_siblings")

    if "littermates" in filter_list:
        test_cat = group[0]
        testing_cats = [cat for cat in group if cat.ID != test_cat.ID]

        if not all([test_cat.is_littermate(inter_cat) for inter_cat in testing_cats]):
            return False
        filter_list.remove("littermates")

    if "not_littermates" in filter_list:
        test_cat = group[0]
        testing_cats = [cat for cat in group if cat.ID != test_cat.ID]

        if any([test_cat.is_littermate(inter_cat) for inter_cat in testing_cats]):
            return False

        filter_list.remove("not_littermates")

    if "mates" in filter_list:
        # first test if more than one cat
        if len(group) == 1:
            return False

        # then if cats don't have the needed number of mates
        if not all(len(i.mate) >= (len(group) - 1) for i in group):
            return False

        # Now the expensive test.  We have to see if everyone is mates with each other
        # Hopefully the cheaper tests mean this is only needed on events with a small number of cats
        for x in combinations(group, 2):
            if x[0].ID not in x[1].mate:
                return False
        filter_list.remove("mates")

    # check if all cats are mates with p_l (they do not have to be mates with each other)
    if "mates_with_pl" in filter_list:
        # First test if there is more than one cat
        if len(group) == 1:
            return False

        # Check each cat to see if it is mates with the patrol leader
        for cat in group:
            if cat.ID == patrol_leader.ID:
                continue
            if cat.ID not in patrol_leader.mate:
                return False
        filter_list.remove("mates_with_pl")

    # Check if all cats are not mates
    if "not_mates" in filter_list:
        # opposite of mate check
        for x in combinations(group, 2):
            if x[0].ID in x[1].mate:
                return False
        filter_list.remove("not_mates")

    # Check if the cats are in a parent/child relationship
    if "parent/child" in filter_list:
        # It should be exactly two cats for a "parent/child" event
        if len(group) != 2:
            return False
        # test for parentage
        if not group[0].is_parent(group[1]):
            return False
        filter_list.remove("parent/child")

    if "not_parent" in filter_list:
        test_cat = group[0]
        testing_cats = [cat for cat in group if cat.ID != test_cat.ID]

        if any([test_cat.is_parent(inter_cat) for inter_cat in testing_cats]):
            return False
        filter_list.remove("not_parent")

    if "child/parent" in filter_list:
        # It should be exactly two cats for a "child/parent" event
        if len(group) != 2:
            return False
        # test for parentage
        if not group[1].is_parent(group[0]):
            return False
        filter_list.remove("child/parent")

    if "not_child" in filter_list:
        test_cat = group[0]
        testing_cats = [cat for cat in group if cat.ID != test_cat.ID]

        if any([inter_cat.is_parent(test_cat) for inter_cat in testing_cats]):
            return False
        filter_list.remove("not_child")

    if "mentor/app" in filter_list:
        # It should be exactly two cats for a "mentor/app" event
        if len(group) != 2:
            return False
        # test for parentage
        if group[1].ID not in group[0].apprentice:
            return False
        filter_list.remove("mentor/app")

    if "not_mentor" in filter_list:
        test_cat = group[0]
        testing_cats = [cat for cat in group if cat.ID != test_cat.ID]

        if any([inter_cat in test_cat.apprentice for inter_cat in testing_cats]):
            return False
        filter_list.remove("not_mentor")

    if "app/mentor" in filter_list:
        # It should be exactly two cats for a "app/mentor" event
        if len(group) != 2:
            return False
        # test for parentage
        if group[0].ID not in group[1].apprentice:
            return False
        filter_list.remove("app/mentor")

    if "not_app" in filter_list:
        test_cat = group[0]
        testing_cats = [cat for cat in group if cat.ID != test_cat.ID]

        if any([inter_cat in test_cat.mentor for inter_cat in testing_cats]):
            return False
        filter_list.remove("not_app")

    # Filtering relationship values
    # each cat has to have relationships toward each other matching every level tag
    for tier in filter_list:
        for inter_cat in group:
            if len(group) == 2 and inter_cat == group[1]:
                # if this is a two cat group, then we only look for the first cat's rel toward the second cat.
                # groups > 2 will require that all cats feel the same way toward each other.
                continue
            group_ids = [cat.ID for cat in group]

            relevant_relationships = [
                rel
                for rel in inter_cat.relationships.values()
                if rel.cat_to.ID in group_ids and rel.cat_to.ID != inter_cat.ID
            ]

            # list of every cat's tier list
            group_lists: list[RelTier] = [
                rel.get_reltype_tiers() for rel in relevant_relationships
            ]

            # now test each list to see if the required tag is inside
            for tier_list in group_lists:
                # just a quick check to see if we can avoid all the extra hullabaloo
                if tier in tier_list:
                    continue

                # if it's limited to *just* the given tier
                if "_only" in tier:
                    tier.replace("_only", "")
                    if tier not in tier_list:
                        return False
                # otherwise we allow both the given tier and any greater tiers
                else:
                    # finding the matching tier enum
                    rel_tier: RelTier = RelTier(tier)

                    # find the matching rel_type enum
                    rel_type: Optional[RelType] = None
                    for rel_type in rel_type_tiers:
                        if rel_tier in rel_type_tiers[rel_type]:
                            rel_type = rel_type
                            break
                    if not rel_type:
                        continue

                    # get the tier's index within the rel_types's list
                    index = rel_type_tiers[rel_type].index(rel_tier)
                    allowed_levels = []
                    # if it's a pos tier, we allow that index and higher
                    if rel_tier.is_any_pos:
                        allowed_levels = rel_type_tiers[rel_type][index:]
                    # if it's a neg tier, we allow that index and lower
                    elif rel_tier.is_any_neg:
                        allowed_levels = rel_type_tiers[rel_type][0 : index + 1]

                    discard = True
                    for l in tier_list:
                        if l in allowed_levels:
                            discard = False
                            break
                    if discard:
                        return False

    return True


def gather_cat_objects(
    Cat, abbr_list: List[str], event, stat_cat=None, extra_cat=None, clan=game.clan
) -> list:
    """
    gathers cat objects from list of abbreviations used within an event format block
    :param Cat Cat: Cat class
    :param list[str] abbr_list: The list of abbreviations
    :param event: the controlling class of the event (e.g. Patrol, HandleShortEvents), default None
    :param Cat stat_cat: if passing the Patrol class, must include stat_cat separately
    :param Cat extra_cat: if not passing an event class, include the single affected cat object here. If you are not
    passing a full event class, then be aware that you can only include "m_c" as a cat abbreviation in your rel block.
    The other cat abbreviations will not work.
    :return: list of cat objects
    """

    clan_cats = [x for x in Cat.all_cats_list if x.status.group_ID == clan.group_ID]
    out_set = set()

    for abbr in abbr_list:
        if abbr == "m_c":
            if extra_cat:
                out_set.add(extra_cat)
            else:
                out_set.add(event.main_cat)
        elif abbr == "r_c":
            out_set.add(event.random_cat)
        elif re.match(r"n_c:[0-9]+", abbr):
            index = re.match(r"n_c:([0-9]+)", abbr).group(1)
            index = int(index)
            if index < len(event.new_cats):
                out_set.update(event.new_cats[index])
        # PATROL SPECIFIC
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
        elif abbr == "patrol":
            out_set.update(event.patrol_cats)
        elif abbr == "multi":
            cat_num = randint(1, max(1, len(event.patrol_cats) - 1))
            out_set.update(sample(event.patrol_cats, cat_num))
        # OVERALL CLAN CATS
        elif abbr == "clan":
            out_set.update(clan_cats)
        elif abbr == "some_clan":  # 1 / 8 of clan cats are affected
            out_set.update(
                sample(clan_cats, randint(1, max(1, round(len(clan_cats) / 8))))
            )
        # FACET CATS IN CLAN
        elif abbr == "high_social":
            out_set = {c for c in out_set if c.personality.sociability > 8}
        elif abbr == "low_social":
            out_set = {c for c in out_set if c.personality.sociability <= 8}
        elif abbr == "high_lawful":
            out_set = {c for c in out_set if c.personality.lawfulness > 8}
        elif abbr == "low_lawful":
            out_set = {c for c in out_set if c.personality.lawfulness <= 8}
        elif abbr == "high_stable":
            out_set = {c for c in out_set if c.personality.stability > 8}
        elif abbr == "low_stable":
            out_set = {c for c in out_set if c.personality.stability <= 8}
        elif abbr == "high_aggress":
            out_set = {c for c in out_set if c.personality.aggression > 8}
        elif abbr == "low_aggress":
            out_set = {c for c in out_set if c.personality.aggression <= 8}

        else:
            print(f"WARNING: Unsupported abbreviation {abbr}")

    return list(out_set)


def unpack_rel_block(
    Cat, relationship_effects: List[dict], event=None, stat_cat=None, extra_cat=None, clan=game.clan
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
    possible_values = [*RelType]

    for block in relationship_effects:
        cats_from = block.get("cats_from", [])
        cats_to = block.get("cats_to", [])
        amount = block.get("amount")
        values = [x for x in block.get("values", ()) if x in possible_values]

        # Gather actual cat objects:
        cats_from_ob = gather_cat_objects(Cat, cats_from, event, stat_cat, extra_cat, clan=clan)
        cats_to_ob = gather_cat_objects(Cat, cats_to, event, stat_cat, extra_cat, clan=clan)

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
        value_changes = {}

        for val in [*RelType]:
            if val in values:
                value_changes[val] = amount
                if amount > 0:
                    positive = True

        if positive:
            effect = i18n.t("relationships.positive_postscript")
        else:
            effect = i18n.t("relationships.negative_postscript")

        # Get log
        to_log = None
        from_log = None
        if "log" in block:
            to_log = (
                block["log"].get("cats_to", "") + effect
                if "cats_to" in block["log"]
                else None
            )
            from_log = (
                block["log"].get("cats_from", "") + effect
                if "cats_from" in block["log"]
                else None
            )
            if not to_log and not from_log:
                print(f"something is wrong with relationship log: {block['log']}")

        change_relationship_values(
            cats_to_ob,
            cats_from_ob,
            **value_changes,
            log=from_log,
        )

        if block.get("mutual"):
            # we'll default to the other log if no unique log was written
            change_relationship_values(
                cats_from_ob,
                cats_to_ob,
                **value_changes,
                log=to_log if to_log else from_log,
            )


def change_relationship_values(
    cats_to: list,
    cats_from: list,
    romance: int = 0,
    like: int = 0,
    respect: int = 0,
    comfort: int = 0,
    trust: int = 0,
    log: str = None,
):
    """
    changes relationship values according to the parameters.

    :param list[Cat] cats_from: list of cat objects whose rel values will be affected
    (e.g. cat_from loses trust in cat_to)
    :param list[Cat] cats_to: list of cats objects who are the target of that rel value
    (e.g. cat_from loses trust in cat_to)
    :param int romance: amount to change romantic, default 0
    :param int like: amount to change platonic, default 0
    :param int respect: amount to change admiration (respect), default 0
    :param int comfort: amount to change comfort, default 0
    :param int trust: amount to change trust, default 0
    :param str log: the string to append to the relationship log of cats involved
    """

    # This is just for test prints - DON'T DELETE - you can use this to test if relationships are changing
    """changed = False
    if romance == 0 and like == 0 and respect == 0 and \
            comfort == 0 and trust == 0:
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
                # now gain the romance
                rel.romance += romance

            # gain other rel values
            rel.like += like
            rel.respect += respect
            rel.comfort += comfort
            rel.trust += trust

            # for testing purposes - DON'T DELETE - you can use this to test if relationships are changing
            """
            print(str(single_cat_from.name) + " gained relationship with " + str(rel.cat_to.name) + ": " +
                  "Romance: " + str(romance) +
                  " /Like: " + str(like) +
                  " /Respect: " + str(respect) +
                  " /Comfort: " + str(comfort) +
                  " /Trust: " + str(trust)) if changed else print("No relationship change")"""
            if not log:
                log = i18n.t("relationships.relationship_log")
            if log and isinstance(log, str):
                replace_dict = {}
                if "from_cat" in log:
                    replace_dict["from_cat"] = (
                        str(single_cat_from.name),
                        choice(single_cat_from.pronouns),
                    )
                if "to_cat" in log:
                    replace_dict["to_cat"] = (
                        str(single_cat_to.name),
                        choice(single_cat_to.pronouns),
                    )
                if replace_dict:
                    processed_log = process_text(log, replace_dict)
                else:
                    processed_log = log

                log_text = processed_log + i18n.t(
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
    if clan.instructor.status.group_ID == CatGroup.DARK_FOREST_ID:
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
    """
    Helper function for add_pronouns.
    :param m: Snippet to pronounify
    :param cat_pronouns_dict: Cats to pronounify
    :param raise_exception: If True, will raise an exception if a mistake is found. Necessary for tests!
    :return: Appropriate pronoun/verb/adjective
    :raises KeyError: if cat doesn't have requested pronoun
    :raises IndexError: if cat doesn't have requested pronoun
    """

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
                except KeyError as e:
                    print(f"Missing pronouns for {cat}")
                    if raise_exception:
                        raise e
                    continue
            d = determine_plural_pronouns(catlist)
        else:
            try:
                d = cat_pronouns_dict[inner_details[1]][1]
            except KeyError as e:
                if raise_exception:
                    raise e

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
    biome = (
        game.clan.biome if not game.clan.override_biome else game.clan.override_biome
    ).casefold()
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
        text = text.replace("c_n", clan.displayname + "Clan")
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
            text = text[:index] + replacement + text[index + len(pattern) :]
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
        cat_dict["lead_name"] = (str(clan.leader.name), choice(clan.leader.pronouns))
    if "dep_name" in text:
        cat_dict["dep_name"] = (str(clan.deputy.name), choice(clan.deputy.pronouns))
    if "med_name" in text:
        meds = find_alive_cats_with_rank(Cat, [CatRank.MEDICINE_CAT], working=True, clan=clan.group_ID)
        kitty = choice(
            meds if meds else find_alive_cats_with_rank(Cat, [CatRank.MEDICINE_CAT], clan=clan.group_ID)
        )
        cat_dict["med_name"] = (str(kitty.name), choice(kitty.pronouns))

    if cat_dict:
        text = process_text(text, cat_dict)

    if other_clan_name:
        text = text.replace("o_c_n", other_clan_name)
    if clan:
        clan_name = str(clan.displayname)
    else:
        if game.clan is None:
            # todo can this be Switch.clan_name ?
            clan_name = switch_get_value(Switch.clan_list)[0]
        else:
            clan_name = str(game.clan.displayname)

    text = text.replace("c_n", clan_name + "Clan")

    text = text.replace("medicine cat", "healer").replace("medicine den", "healer den")

    return text


def event_text_adjust(
    Cat: Type["Cat"],
    text: str,
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
    clan = None,
    other_clan = None,
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
    vowels = ["A", "E", "I", "O", "U"]
    if not patrol_apprentices:
        patrol_apprentices = []
    if not new_cats:
        new_cats = []

    if clan is None:
        clan = game.clan

    if not text:
        text = "This should not appear, report as a bug please! Tried to adjust the text, but no text was provided."
        print("WARNING: Tried to adjust text, but no text was provided.")

    # this check is really just here to catch odd bug edge-cases from old saves, specifically in death history
    # otherwise we should really *never* have lists being passed as the text
    if isinstance(text, list):
        text = text[0]

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
    if "n_c" in text:
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
        try:
            med = choice(
                find_alive_cats_with_rank(
                    Cat, [CatRank.MEDICINE_CAT, CatRank.MEDICINE_APPRENTICE], working=True, clan=clan.group_ID)
            )
        except:
            med = choice(
                find_alive_cats_with_rank(Cat, [CatRank.MEDICINE_CAT], clan=clan.group_ID)
            )
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
    if "o_c_n" in text and other_clan:
        other_clan_name = other_clan.displayname
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
            clan_name = clan.displayname
        except AttributeError:
            # todo can this be Switch.clan_name ?
            clan_name = switch_get_value(Switch.clan_list)[0]

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
    if main_cat:
        if "acc_plural" in text:
            text = text.replace(
                "acc_plural",
                i18n.t(f"cat.accessories.{main_cat.pelt.accessory[-1]}", count=2),
            )

        # acc_singular (only works for main_cat's acc)
        if "acc_singular" in text:
            accessory_name = main_cat.pelt.accessory[-1]
            if sprites.COLLAR_DATA["palette_map"]:
                potential_collar = "".join(
                    [x for x in accessory_name if not x.islower()]
                ).strip("_")
                for style in main_cat.pelt.collar_styles:
                    if style == potential_collar:
                        accessory_name = potential_collar
                        break
            text = text.replace(
                "acc_singular",
                i18n.t(f"cat.accessories.{accessory_name}", count=1),
            )

        if "given_herb" in text:
            text = text.replace(
                "given_herb", i18n.t(f"conditions.herbs.{chosen_herb}", count=2)
            )

    text = text.replace("medicine cat", "healer").replace("medicine den", "healer den")

    return text


def leader_ceremony_text_adjust(
    Cat,
    text,
    leader,
    life_giver=None,
    virtue=None,
    extra_lives=None,
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

    clan = leader.status.fetch_clan_object()
    text = text.replace("c_n", str(clan.displayname) + "Clan")

    text = text.replace("medicine cat", "healer").replace("medicine den", "healer den")

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
    clanname = str(clan.displayname + "Clan")

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

    adjust_text = adjust_text.replace("medicine cat", "healer").replace("medicine den", "healer den")

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
        (
            floor(dim[0] * scripts.game_structure.screen_settings.screen_scale)
            if dim[0] > 0
            else dim[0]
        ),
        (
            floor(dim[1] * scripts.game_structure.screen_settings.screen_scale)
            if dim[1] > 0
            else dim[1]
        ),
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


def update_mask(cat):
    if cat.faded or cat.dead:
        # should never need a mask since they can't appear on the Clan screen
        cat.sprite_mask = None
        return

    val = pygame.mask.from_surface(
        pygame.transform.scale(cat.sprite, ui_scale_dimensions((50, 50))), threshold=250
    )

    inflated_mask = pygame.Mask(
        (
            val.get_size()[0] + 10,
            val.get_size()[1] + 10,
        )
    )
    inflated_mask.draw(val, (5, 5))
    for _ in range(3):
        outline = inflated_mask.outline()
        for point in outline:
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    try:
                        inflated_mask.set_at((point[0] + dx, point[1] + dy), 1)
                    except IndexError:
                        continue
    cat.sprite_mask = inflated_mask


def clan_symbol_sprite(clan, return_string=False, force_light=False, force_dark=False):
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
            if f"symbol{clan.displayname.upper()}" == name:
                possible_sprites.append(sprite)
        if possible_sprites:
            clan.chosen_symbol = choice(possible_sprites)
        else:
            # give random symbol if no matching symbol exists
            print(
                f"WARNING: attempted to return symbol, but there's no clan symbol for {clan.displayname.upper()}. "
                f"Random chosen."
            )
            clan.chosen_symbol = choice(sprites.clan_symbols)

    if return_string:
        return clan.chosen_symbol
    else:
        return sprites.get_symbol(clan.chosen_symbol, force_light=force_light, force_dark=force_dark)


def generate_sprite(
    cat,
    life_state=None,
    scars_hidden=False,
    acc_hidden=False,
    always_living=False,
    disable_sick_sprite=False,
    hide_white=False
) -> pygame.Surface:
    """
    Generates the sprite for a cat, with optional arguments that will override certain things.

    :param life_state: sets the age life_stage of the cat, overriding the one set by its age. Set to string.
    :param scars_hidden: If True, doesn't display the cat's scars. If False, display cat scars.
    :param acc_hidden: If True, hide the accessory. If false, show the accessory.
    :param always_living: If True, always show the cat with living lineart
    :param disable_sick_sprite: If true, never use the not_working lineart.
                    If false, use the cat.not_working() to determine the no_working art.
    """
    sprite_poses = sprites.POSE_DATA["poses"]

    if life_state is not None:
        age = life_state
    else:
        if game_setting_get("ageup dead") and cat.dead and cat.age in [CatAge.NEWBORN, CatAge.KITTEN, CatAge.ADOLESCENT]:
            age = CatAge.ADULT
        elif game_setting_get("youthful dead") and cat.dead and cat.age == CatAge.SENIOR:
            age = CatAge.ADULT
        else:
            age = cat.age


    if always_living:
        dead = False
    else:
        dead = cat.dead

    # setting the cat_sprite (bc this makes things much easier)

    # sick sprites
    if (
        not disable_sick_sprite
        and cat.not_working()
        and age != CatAge.NEWBORN
        and constants.CONFIG["cat_sprites"]["sick_sprites"]
    ):
        if age in (CatAge.KITTEN, CatAge.ADOLESCENT):
            cat_sprite = sprite_poses["sick_young0"]
        else:
            cat_sprite = sprite_poses["sick_adult0"]

    # paralyzed sprites
    elif cat.pelt.paralyzed and age != CatAge.NEWBORN:
        if age in (CatAge.KITTEN, CatAge.ADOLESCENT):
            cat_sprite = sprite_poses["para_young0"]
        else:
            if cat.pelt.length == 'long' or (cat.pelt.length == 'medium' and get_current_season() == 'Leaf-bare'):
                cat_sprite = sprite_poses["para_adult_long0"]
            else:
                cat_sprite = sprite_poses["para_adult_short0"]

    # default sprites
    else:
        if constants.CONFIG["fun"]["all_cats_are_newborn"]:
            cat_sprite = sprite_poses[cat.pelt.cat_sprites["newborn"]]
        else:
            if cat.pelt.length == 'medium' and get_current_season() == 'Leaf-bare':
                cat_sprite = sprite_poses[cat.pelt.cat_sprites[age].replace("short", "long")]
            else:
                cat_sprite = sprite_poses[cat.pelt.cat_sprites[age]]

    alt_cat_sprite = str(int(cat_sprite)-3)

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
            if phenotype.somatic["gene"] == 'sexgene' and len(phenotype.sexgene) > 1:
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
                
            def CreateStripes(stripecolour, whichbase, coloursurface=None, preset_pattern=None, special=None):
                stripebase = pygame.Surface(
                    (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                shading = pygame.Surface(
                    (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)

                if whichbase == "solid" and phenotype.ghosting[0] == 'Gh' and not (phenotype.silver[0] == 'I' and cat.pelt.length == 'long'):
                    return stripebase

                not_red = (
                    'red' not in stripecolour and 'cream' not in stripecolour and 'honey' not in stripecolour and 'ivory' not in stripecolour and 'apricot' not in stripecolour)
                is_dark_sunshine = (phenotype.wbtype not in [
                    "shaded", "chinchilla"] and phenotype.corin[0] == "sh" and not_red and phenotype.agouti[1] == "a"
                    and not (('ec' in phenotype.ext or (phenotype.ext[0] == 'ea' and ((sprite_age > 7 and phenotype.ext[0] != "a") or sprite_age > 19))) and 'Eg' not in phenotype.ext))

                if not special and 'solid' not in whichbase:
                    if ('chinchilla' in whichbase):
                        shading.blit(
                            sprites.sprites['chinchillashading' + cat_sprite], (0, 0))
                    elif ('shaded' in whichbase) and not is_dark_sunshine:
                        shading.blit(
                            sprites.sprites['shadedshading' + cat_sprite], (0, 0))
                    else:
                        shading.blit(
                            sprites.sprites[phenotype.wbtype + 'shading' + cat_sprite], (0, 0))
                if "silver" in whichbase:
                    shading.set_alpha(150)
                
                stripebase.blit(shading, (0, 0))

                
                if preset_pattern:
                    for pat in preset_pattern:
                        stripebase.blit(
                            sprites.sprites[pat + cat_sprite], (0, 0))
                elif 'ghost' in phenotype.tabby:
                    ghoststripes = pygame.Surface(
                        (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    ghoststripes.blit(
                        sprites.sprites[phenotype.GetTabbySprite()[0] + cat_sprite], (0, 0))
                    ghoststripes.set_alpha(25)
                    stripebase.blit(ghoststripes, (0, 0))
                    pattern = phenotype.GetTabbySprite(special='ghost')
                    for pat in pattern:
                        stripebase.blit(
                            sprites.sprites[pat + cat_sprite], (0, 0))
                else:
                    pattern = phenotype.GetTabbySprite()
                    for pat in pattern:
                        stripebase.blit(
                            sprites.sprites[pat + cat_sprite], (0, 0))
                        if (phenotype.bengtype == "mild bengal") and pat in ["braided", "brokenbraid"]:
                            stripebase2 = pygame.Surface(
                                (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            stripebase2.blit(
                                sprites.sprites[pat + cat_sprite], (0, 0))
                            stripebase2.set_alpha(127)
                            stripebase.blit(stripebase2, (0, 0))
                    if pattern[0] in ["marbled", "blotched"] and phenotype.sheeted:
                        stripebase.blit(
                            sprites.sprites["sheeted" + cat_sprite], (0, 0))

                if not_red:
                    stripebase.blit(
                        sprites.sprites["tabbypads" + cat_sprite], (0, 0))

                charc = pygame.Surface(
                    (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                charc_shading = pygame.Surface(
                    (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                if (phenotype.agouti[0] == "Apb" and not_red):
                    if special != "no_shading":
                        charc_shading.blit(
                            sprites.sprites['lightbasecolours0'], (0, 0))
                        modifiers = {
                            "chinchilla": 2,
                            "shaded": 3,
                            "high": 5,
                            "medium": 6,
                            "low": 7
                        }
                        opacity = int(
                            25 * (modifiers.get(phenotype.banding, 5) / (1 * (int("silver" in whichbase) + 1))))
                        charc_shading.set_alpha(opacity)
                        charc.blit(charc_shading, (0, 0))
                    charc.blit(
                        sprites.sprites['charcoal' + cat_sprite], (0, 0))
                    if not preset_pattern and "fullbar" not in pattern[0] and "redbar" not in pattern[0]:
                        charc.blit(
                            sprites.sprites[pattern[0] + cat_sprite], (0, 0))

                    if (phenotype.agouti == ["Apb", "Apb"]):
                        charc.set_alpha(191)
                stripebase.blit(charc, (0, 0))

                if ('chinchilla' in whichbase or 'shaded' in whichbase) and not is_dark_sunshine:
                    golden_gradient = pygame.Surface(
                        (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    golden_gradient2 = pygame.Surface(
                        (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    golden_gradient2.blit(
                        sprites.sprites["goldengradient" + cat_sprite], (0, 0))

                    if 'chinchilla' in whichbase:
                        golden_gradient2.set_alpha(150)
                    if 'shaded' in whichbase:
                        if phenotype.corin[0] == "N":
                            golden_gradient2.set_alpha(100)
                            golden_gradient.blit(golden_gradient2, (0, 0))
                            golden_gradient2.set_alpha(255)
                    golden_gradient.blit(golden_gradient2, (0, 0))

                    stripebase.blit(golden_gradient, (0, 0),
                                    special_flags=pygame.BLEND_RGBA_MIN)
                    golden_gradient = pygame.Surface(
                        (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    golden_gradient.fill((255, 255, 255))
                    stripebase.blit(golden_gradient, (0, 0),
                                    special_flags=pygame.BLEND_RGB_MAX)

                if coloursurface:
                    stripebase.blit(coloursurface, (0, 0),
                                    special_flags=pygame.BLEND_RGBA_MULT)
                elif 'basecolours' in stripecolour:
                    stripebase.blit(
                        sprites.sprites[stripecolour], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                else:
                    surf = pygame.Surface(
                        (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    surf.blit(sprites.sprites[stripecolourdict.get(
                        stripecolour[:-1], stripecolour[:-1])+stripecolour[-1]], (0, 0))
                    if phenotype.caramel == 'caramel' and not ('red' in stripecolour or 'cream' in stripecolour or 'honey' in stripecolour or 'ivory' in stripecolour or 'apricot' in stripecolour):
                        surf.blit(sprites.sprites['caramel0'], (0, 0))

                    stripebase.blit(
                        surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                if not preset_pattern and len(pattern) > 2:
                    if phenotype.soktype == "full sokoke":
                        stripebase = CreateStripes(
                            stripecolour, whichbase, coloursurface, preset_pattern=pattern[1:])
                        middle = CreateStripes(
                            stripecolour, whichbase, coloursurface, special="no_shading", preset_pattern=pattern[:1])
                        middle.set_alpha(150)
                        stripebase.blit(middle, (0, 0))
                    elif phenotype.soktype == "mild fading":
                        stripebase = CreateStripes(
                            stripecolour, whichbase, coloursurface, preset_pattern=pattern[1:])
                        middle = CreateStripes(
                            stripecolour, whichbase, coloursurface, special="no_shading", preset_pattern=pattern[:1])
                        middle.set_alpha(204)
                        stripebase.blit(middle, (0, 0))

                return stripebase

            def TabbyBase(whichcolour, whichbase, cat_unders, special=None):
                is_red = ('red' in whichcolour or 'cream' in whichcolour or 'honey' in whichcolour or 'ivory' in whichcolour or 'apricot' in whichcolour)
                whichmain = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                whichmain.blit(sprites.sprites[whichbase], (0, 0))
                if special !='copper' and sprite_age > 12 and (phenotype.silver[0] == 'I' and phenotype.corin[0] == 'fg' and (get_current_season() == 'Leaf-fall' or get_current_season() == 'Leaf-bare' or 'sterile' in cat.permanent_condition)):
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

                if phenotype.pangere:
                    modifiers = {
                        "chinchilla" : 9,
                        "shaded" : 8,
                        "high" : 7,
                        "medium" : 6,
                        "low" : 5
                    }
                    opacity = int(25 * (modifiers.get(phenotype.banding, 5)))
                    pangere = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    pangere.blit(sprites.sprites[phenotype.pangere + cat_sprite], (0, 0))
                    pangere.set_alpha(opacity)
                    whichmain.blit(pangere, (0, 0))
                
                if phenotype.rednose and not phenotype.tabtype:
                    modifiers = {
                        "chinchilla" : 1,
                        "shaded" : 3,
                        "high" : 7,
                        "medium" : 7,
                        "low" : 7
                    }
                    opacity = int(12 * (modifiers.get(phenotype.banding, 5)))
                    rednose = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    rednose.blit(sprites.sprites["rednose" + cat_sprite], (0, 0))
                    nose_colour = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    stripecolour = phenotype.FindRed(phenotype, sprite_age, "red")[0]
                    nose_colour.blit(sprites.sprites[stripecolourdict.get(stripecolour[:-1], stripecolour[:-1])+stripecolour[-1]], (0, 0))
                    rednose.blit(nose_colour, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    rednose.set_alpha(opacity)
                    whichmain.blit(rednose, (0, 0))
                
                return whichmain
        
            def AddStripes(whichmain, whichcolour, whichbase, coloursurface=None):
                stripebase = pygame.Surface(
                    (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                if (('ec' in phenotype.ext or (phenotype.ext[0] == 'ea' and ((sprite_age > 7 and phenotype.ext[0] != "a") or sprite_age > 19))) and 'Eg' not in phenotype.ext and not ('red' in whichcolour or 'cream' in whichcolour or 'honey' in whichcolour or 'ivory' in whichcolour or 'apricot' in whichcolour)):
                    stripebase = CreateStripes(
                        whichcolour, whichbase, coloursurface=coloursurface)
                    stripebase.set_alpha(200)
                    whichmain.blit(stripebase, (0, 0))
                    stripebase = CreateStripes(
                        whichcolour, whichbase, coloursurface=coloursurface, preset_pattern=['agouti'])
                else:
                    stripebase.blit(CreateStripes(
                        whichcolour, whichbase, coloursurface=coloursurface), (0, 0))

                whichmain.blit(stripebase, (0, 0))

                return whichmain

            def ApplySmokeEffects(whichmain):
                white = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                white.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                smokeUnders = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                smokeUnders.blit(sprites.sprites["ghost" + cat_sprite], (0, 0))
                white.set_alpha(10)
                smokeLayer = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                smokeLayer.blit(white, (0, 0))
                if(phenotype.ext[0] == 'Eg' and phenotype.agouti[0] != 'a'):
                    grizzle = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    grizzle.blit(sprites.sprites['satin0'], (0, 0))
                    grizzle.blit(sprites.sprites['grizzle' + cat_sprite], (0, 0))
                    grizzle.set_alpha(175)
                    whichmain.blit(grizzle, (0, 0))
                if phenotype.ghosting[0] == 'Gh' and not (phenotype.silver[0] == 'I' and cat.pelt.length == 'long'):
                    if(sprite_age < 4):
                        smokeUnders.set_alpha(150)
                    
                    whichmain.blit(smokeUnders, (0, 0))
                smokeUnders.set_alpha(255)
                if (phenotype.silver[0] == 'I' or phenotype.karp[1] == "K"):
                    if cat.pelt.length != 'long':
                        smokeUnders.set_alpha(100)
                    elif phenotype.wbtype == 'low':
                        smokeUnders.set_alpha(150)
                    
                    whichmain.blit(smokeUnders, (0, 0))
                    if phenotype.wbtype == 'low' and cat.pelt.length == 'long':
                        smokeLayer.set_alpha(75)
                    elif phenotype.wbtype == 'low' or cat.pelt.length == 'long':
                        smokeLayer.set_alpha(150)
                    else:
                        smokeLayer.set_alpha(200)
                    whichmain.blit(smokeLayer, (0, 0))
                smokeUnders.set_alpha(20)
                if ('smoke' in phenotype.silvergold and 14 > phenotype.wbsum > 9):
                    smokeLayer.set_alpha(255)
                    if cat.pelt.length != 'long':
                        smokeLayer.blit(smokeUnders, (0, 0))
                    if phenotype.wbtype == 'high':
                        smokeLayer.set_alpha(100)
                    elif cat.pelt.length == 'long':
                        smokeLayer.set_alpha(200)                    
                    whichmain.blit(smokeLayer, (0, 0))
                
                return whichmain

            def AddPads(sprite, whichcolour, is_red=False):
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

                if(phenotype.white[0] == 'W' or phenotype.pointgene[0] == 'c' or phenotype.white_pattern == ['full white'] or whichcolour == "white"):
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

            def AddNose(sprite, maincolour, spritecolour, isred):
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

                if maincolour == "white":
                    nose.blit(sprites.sprites['nosecolours1'], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                elif ('amber' not in phenotype.colour or phenotype.agouti[0] != 'a') and isred:
                    nose.blit(sprites.sprites['nosecolours0'], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                elif 'amber' in phenotype.colour:
                    phenotype.SpriteInfo(10)
                    nose.blit(sprites.sprites['nosecolours' + str(nose_dict.get(phenotype.maincolour[:-1]))], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    phenotype.SpriteInfo(sprite_age)
                elif maincolour != spritecolour and "masked" not in phenotype.silvergold and "charcoal" not in phenotype.tabtype and not phenotype.blacknose:
                    if phenotype.corin[0] != "N" and not (phenotype.corin[0] == "sh" and phenotype.agouti[1] == "a"):
                        nose.blit(sprites.sprites['nosecolours0'], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    else:
                        nose.blit(sprites.sprites['nosecolours2'], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    nose.set_alpha(200)
                else:
                    nose.blit(sprites.sprites['nosecolours' + str(nose_dict.get(maincolour[:-1]))], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                sprite.blit(nose, (0, 0))
                return sprite

            def MakeCat(whichmain, whichcolour, whichbase, cat_unders, special=None):
                is_red = ('red' in whichcolour or 'cream' in whichcolour or 'honey' in whichcolour or 'ivory' in whichcolour or 'apricot' in whichcolour)
                
                if (phenotype.white[0] == 'W' or phenotype.pointgene[0] == 'c' or whichbase == 'white' or phenotype.white_pattern == ['full white']):
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

                            if((phenotype.pointgene == ["cb", "cb"] and 'cinnamon' not in whichcolour and sprite_age > 0) or (((("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm") and sprite_age > 0) or phenotype.pointgene == ["cb", "cb"]) and get_current_season() == 'Leaf-bare')):
                                colourbase.set_alpha(100)
                            elif((("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm") and sprite_age > 0) or phenotype.pointgene == ["cb", "cb"] or ((sprite_age > 0 or ("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm")) and get_current_season() == 'Leaf-bare')):
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
                                    if("black" in whichcolour and sprite_age > 0):
                                        whichmain = AddStripes(whichmain, 'lightbasecolours2', whichbase)
                                    elif((("chocolate" in whichcolour or "cinnamon" in whichcolour) and sprite_age > 0) or "black" in whichcolour):
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
                                    if("black" in whichcolour and sprite_age > 0):
                                        stripecolour = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                                        stripecolour = AddStripes(stripecolour, 'lightbasecolours1', whichbase)
                                        stripecolour.set_alpha(102)
                                        whichmain.blit(stripecolour, (0, 0))
                                    else:
                                        whichmain = AddStripes(whichmain, 'lightbasecolours0', whichbase)
                        
                        else:
                            if("black" in whichcolour and phenotype.pointgene == ["cb", "cb"] and sprite_age > 0):
                                whichmain = AddStripes(whichmain, 'lightbasecolours3', whichbase)
                            elif((("chocolate" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("black" in whichcolour and "cb" in phenotype.pointgene)) and sprite_age > 0 or ("black" in whichcolour and phenotype.pointgene == ["cb", "cb"])):
                                whichmain = AddStripes(whichmain, 'lightbasecolours2', whichbase)
                            elif((("cinnamon" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("chocolate" in whichcolour and "cb" in phenotype.pointgene) or ("black" in whichcolour and phenotype.pointgene == ["cs", "cs"])) and sprite_age > 0 or (("chocolate" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("black" in whichcolour and "cb" in phenotype.pointgene))):
                                whichmain = AddStripes(whichmain, 'lightbasecolours1', whichbase)

                            elif(phenotype.pointgene == ["cb", "cb"]) and sprite_age > 0:
                                pointbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                                pointbase.blit(sprites.sprites[stripecolourdict.get(whichcolour[:-1], whichcolour[:-1])+whichcolour[-1]], (0, 0))
                                if phenotype.caramel == 'caramel' and not is_red:    
                                    pointbase.blit(sprites.sprites['caramel0'], (0, 0))
                                pointbase.set_alpha(204)
                                pointbase2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                                pointbase2.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                                pointbase2.blit(pointbase, (0, 0))
                                whichmain = AddStripes(whichmain, whichcolour, whichbase, coloursurface=pointbase2)
                            elif("cb" in phenotype.pointgene) and (sprite_age > 0 or phenotype.pointgene == ["cb", "cb"]):
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
                            # else:
                            #     whichmain = AddStripes(whichmain, 'lightbasecolours0', whichbase)

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
                                if((("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm") and sprite_age > 0) or ((sprite_age > 0 or ("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm")) and get_current_season() == "Leaf-bare")):
                                    colourbase.set_alpha(180)
                                elif(sprite_age > 0 or ("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm")):
                                    colourbase.set_alpha(50)
                                else:
                                    colourbase.set_alpha(0)

                                pointbase2.blit(colourbase, (0, 0))
                                
                                if phenotype.pointgene[0] == "cm":
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
                                
                        else:
                            if((phenotype.pointgene == ["cb", "cb"] and sprite_age > 0) or ("cb" in phenotype.pointgene and sprite_age > 0 and get_current_season() == 'Leaf-bare')):
                                colourbase.set_alpha(180)
                            elif(("cb" in phenotype.pointgene and sprite_age > 0) or phenotype.pointgene == ["cb", "cb"] or ((sprite_age > 0 or "cb" in phenotype.pointgene) and get_current_season() == 'Leaf-bare')):
                                colourbase.set_alpha(120)
                            elif(sprite_age > 0 or "cb" in phenotype.pointgene):
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

                        
                        if phenotype.pointgene[0] == "cm":
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
                        else:
                            if(get_current_season() == "Greenleaf"):
                                stripebase2.blit(sprites.sprites['pointsl' + cat_sprite], (0, 0))
                                stripebase2.blit(stripebase, (0, 0), 
                                            special_flags=pygame.BLEND_RGBA_MULT)
                            elif(get_current_season() == "Leaf-bare"):
                                stripebase2.blit(sprites.sprites['pointsd' + cat_sprite], (0, 0))
                                stripebase2.blit(stripebase, (0, 0), 
                                            special_flags=pygame.BLEND_RGBA_MULT)
                            else:
                                stripebase2.blit(sprites.sprites['pointsm' + cat_sprite], (0, 0))
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

                        stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        stripebase.blit(CreateStripes(whichcolour, "solid", special="no_shading"), (0, 0))
                        whichmain.blit(stripebase, (0, 0))
                    elif("cm" in phenotype.pointgene):
                        colour = None
                        coloursurface = None
                        if("black" in whichcolour and phenotype.pointgene[0] == "cm"):
                            whichmain.blit(sprites.sprites['lightbasecolours2'], (0, 0)) 
                            overlay = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            overlay.blit(sprites.sprites['cinnamon3'], (0, 0)) 
                            overlay.set_alpha(10)
                            whichmain.blit(overlay, (0, 0))
                            whichmain = ApplySmokeEffects(whichmain)

                            stripebase = CreateStripes("cinnamon2", 'solid', special="no_shading")
                            stripebase.set_alpha(10)

                            whichmain.blit(stripebase, (0, 0))
                        else:
                            stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                                
                            if("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm"):
                                if("black" in whichcolour and sprite_age > 0):
                                    whichmain.blit(sprites.sprites['lightbasecolours2'], (0, 0))
                                    colour = 'lightbasecolours2'
                                    whichmain = ApplySmokeEffects(whichmain)

                                elif(("chocolate" in whichcolour and sprite_age > 0) or "black" in whichcolour):
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
                                if("black" in whichcolour and sprite_age > 0):
                                    whichmain.blit(sprites.sprites['lightbasecolours1'], (0, 0))
                                    colour = 'lightbasecolours1'
                                    whichmain = ApplySmokeEffects(whichmain)
                                else:
                                    whichmain.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                                    colour = 'lightbasecolours0'
                            
                            
                            stripebase = CreateStripes(colour, 'solid', special="no_shading", coloursurface=coloursurface)
                            whichmain.blit(stripebase, (0, 0))

                            pointbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            pointbase2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            
                            pointbase2.blit(sprites.sprites[whichcolour], (0, 0))
                            if phenotype.caramel == 'caramel' and not is_red:    
                                pointbase2.blit(sprites.sprites['caramel0'], (0, 0))
                        
                            whichmain = ApplySmokeEffects(whichmain)

                            
                            stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            stripebase.blit(CreateStripes(whichcolour, 'solid', special="no_shading"), (0, 0))

                            pointbase2.blit(stripebase, (0, 0))

                            if phenotype.pointgene[0] == "cm":
                                if (get_current_season() == "Greenleaf"):
                                    pointbase.blit(
                                        sprites.sprites['mochal' + cat_sprite], (0, 0))
                                    pointbase.blit(pointbase2, (0, 0),
                                                special_flags=pygame.BLEND_RGBA_MULT)
                                elif (get_current_season() == "Leaf-bare"):
                                    pointbase.blit(
                                        sprites.sprites['mochad' + cat_sprite], (0, 0))
                                    pointbase.blit(pointbase2, (0, 0),
                                                special_flags=pygame.BLEND_RGBA_MULT)
                                else:
                                    pointbase.blit(
                                        sprites.sprites['mocham' + cat_sprite], (0, 0))
                                    pointbase.blit(pointbase2, (0, 0),
                                                special_flags=pygame.BLEND_RGBA_MULT)
                            else:                 
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
                        
                            # if phenotype.pointgene[0] == "cm" and 'blue' in whichcolour:
                            #     pointbase.set_alpha(102)

                            whichmain.blit(pointbase, (0, 0))        
                            
                    else:
                        colour = whichcolour
                        coloursurface = None
                        stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        if("black" in whichcolour and phenotype.pointgene == ["cb", "cb"] and sprite_age > 0):
                            whichmain.blit(sprites.sprites['lightbasecolours3'], (0, 0)) 
                            colour = 'lightbasecolours3'
                            whichmain = ApplySmokeEffects(whichmain)
                        elif((("chocolate" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("black" in whichcolour and "cb" in phenotype.pointgene)) and sprite_age > 0) or ("black" in whichcolour and phenotype.pointgene == ["cb", "cb"]):
                            whichmain.blit(sprites.sprites['lightbasecolours2'], (0, 0)) 
                            colour = 'lightbasecolours2'
                            whichmain = ApplySmokeEffects(whichmain)
                        elif((("cinnamon" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("chocolate" in whichcolour and "cb" in phenotype.pointgene) or ("black" in whichcolour and phenotype.pointgene == ["cs", "cs"])) and sprite_age > 0) or (("chocolate" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("black" in whichcolour and "cb" in phenotype.pointgene)):
                            whichmain.blit(sprites.sprites['lightbasecolours1'], (0, 0))  
                            colour = 'lightbasecolours1'
                            whichmain = ApplySmokeEffects(whichmain)
                        elif(phenotype.pointgene == ["cb", "cb"]) and sprite_age > 0:
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
                        elif("cb" in phenotype.pointgene) and (sprite_age > 0 or phenotype.pointgene == ["cb", "cb"]):
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

                        stripebase = CreateStripes(colour, 'solid', special="no_shading", coloursurface=coloursurface)

                        whichmain.blit(stripebase, (0, 0))

                        pointbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        pointbase2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            
                        pointbase2.blit(sprites.sprites[whichcolour], (0, 0))
                        if phenotype.caramel == 'caramel' and not is_red:    
                                pointbase2.blit(sprites.sprites['caramel0'], (0, 0))
                        pointbase2 = ApplySmokeEffects(pointbase2)

                        
                        stripebase = CreateStripes(whichcolour, "solid", special="no_shading")
                    
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
                whichmain = AddNose(whichmain, whichcolour, whichbase, is_red)
                
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

                if (phenotype.glitter[0] == 'gl' or phenotype.ghosting[0] == 'Gh') and (phenotype.agouti[0] != 'a' or ('red' in phenotype.maincolour or 'cream' in phenotype.maincolour or 'honey' in phenotype.maincolour or 'ivory' in phenotype.maincolour or 'apricot' in phenotype.maincolour)):    
                    if phenotype.glitter[0] == 'gl':
                        sprite.blit(sprites.sprites['satin0'], (0, 0))
                    if (phenotype.ghosting[0] == 'Gh'):
                        fading = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        fading.blit(sprites.sprites['bleach'+cat_sprite], (0, 0))
                        fading.blit(sprites.sprites['satin0'], (0, 0))
                        fading.blit(sprites.sprites['satin0'], (0, 0))
                        fading.blit(sprites.sprites['satin0'], (0, 0))
                        fading.blit(sprites.sprites['satin0'], (0, 0))
                        fading.set_alpha(50)
                        sprite.blit(fading, (0, 0))
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
                            isred = ('red' in phenotype.maincolour or 'cream' in phenotype.maincolour or 'honey' in phenotype.maincolour or 'ivory' in phenotype.maincolour or 'apricot' in phenotype.maincolour or 'white' in phenotype.maincolour)
                            tortpatches = MakeCat(tortpatches, phenotype.maincolour, phenotype.spritecolour, phenotype.mainunders)
                        else:
                            isred = ('red' in phenotype.patchmain or 'cream' in phenotype.patchmain or 'honey' in phenotype.patchmain or 'ivory' in phenotype.patchmain or 'apricot' in phenotype.patchmain or 'white' in phenotype.patchmain)
                            tortpatches = MakeCat(tortpatches, phenotype.patchmain, phenotype.patchcolour, phenotype.patchunders)
                        if phenotype.caramel == 'caramel' and not isred: 
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
                    if (sprite_age > 2):
                        fevercoat.set_alpha(150)
                    gensprite.blit(fevercoat, (0, 0))
                
                elif (phenotype.bleach[0] == "lb" and sprite_age > 3) or (phenotype.wbtype == "shaded" and 'smoke' in phenotype.silvergold):
                    gensprite.blit(sprites.sprites['bleach' + cat_sprite], (0, 0))
                elif ('masked' in phenotype.silvergold and phenotype.wbsum < 16):
                    gensprite.blit(sprites.sprites['bleach' + cat_sprite], (0, 0))
                    gensprite.blit(sprites.sprites['bleach' + cat_sprite], (0, 0))

            
            if (
                game_setting_get('tints')
                and cat.pelt.tint in sprites.cat_tints["tint_colours"]
            ):
                tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                tint.fill(tuple(sprites.cat_tints["tint_colours"][cat.pelt.tint]))
                gensprite.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            if (
                game_setting_get('tints')
                and cat.pelt.tint in sprites.cat_tints["dilute_tint_colours"]
            ):
                tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                tint.fill(tuple(sprites.cat_tints["dilute_tint_colours"][cat.pelt.tint]))
                gensprite.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

            if is_today(SpecialDate.APRIL_FOOLS) and "Dg" in phenotype.april_fools.get("danish_green", []):
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
            leathers = AddPads(leathers, "white")
            leathers = AddNose(leathers, "white", "white", False)
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
                game_setting_get('tints')
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
            elif(cat.pelt.length == 'hairless' and (cat.phenotype.sedesp[0] == "hr" or cat.phenotype.ruhr[1] == "Hrbd" or sprite_age > 11)):
                gensprite.blit(sprites.sprites['hairless' + cat_sprite], (0, 0))
                gensprite.blit(sprites.sprites['furpoint' + cat_sprite], (0, 0))
            elif ('patchy ' in cat.phenotype.furtype) or (cat.pelt.length == 'hairless' and cat.phenotype.sedesp[0] != "hr" and cat.phenotype.ruhr[1] != "Hrbd" and sprite_age > 5):
                gensprite.blit(sprites.sprites['donskoy' + cat_sprite], (0, 0))
            
            if('sparse' in cat.phenotype.furtype):
                gensprite.blit(sprites.sprites['satin0'], (0, 0))
                gensprite.blit(sprites.sprites['satin0'], (0, 0))
                gensprite.blit(sprites.sprites['lykoi' + cat_sprite], (0, 0))

            gensprite.blit(white_leathers, (0, 0))
            

            if(phenotype.fold[0] != 'Fd' or phenotype.curl[0] == 'Cu'):
                gensprite.blit(sprites.sprites['ears' + cat_sprite], (0, 0))


            def construct_eye_colour(eyetype):
                split = eyetype.split(" ; ")
                data = sprites.EYE_DATA[split[1]][split[0]].copy()
                eyes = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                
                if is_today(SpecialDate.APRIL_FOOLS):
                    if phenotype.april_fools.get("rainbow_eyes", ["NoDRE"])[0] == "DREfull":
                        data["inner"] = [randint(0, 255), randint(0, 255), randint(0, 255)] 
                        data["outer"] = [randint(127, 255), randint(127, 255), randint(127, 255)] 
                        data["pupil"] = [randint(0, 127), randint(0, 127), randint(0, 127)] 
                    elif phenotype.april_fools.get("rainbow_eyes", ["NoDRE"])[0] == "DREmin":
                        rgb = [randint(0, 255), randint(0, 255), randint(0, 255)]
                        data["inner"] = rgb 
                        pupils = [0, 0, 0]
                        pupils1 = [v*0.5 for v in rgb]
                        rgb = [round(rgb[0]*0.625), round(rgb[1]*0.7), round(rgb[2]*0.50)]
                        data["outer"] = rgb
                        pupils2 = [v*0.5 for v in rgb]
                        for i in range(3):
                            pupils[i] = round((pupils1[i] + pupils2[i])/2)
                        data["pupil"] = pupils
                
                colour = pygame.Color(data["inner"])
                eye_section = sprites.sprites['eyeinner' + alt_cat_sprite].copy()
                pixel_array = pygame.PixelArray(eye_section)
                pixel_array.replace((255, 255, 255, 255), colour, distance=0)
                del pixel_array
                eyes.blit(eye_section, (0, 0))
                
                colour = pygame.Color(data["outer"])
                eye_section = sprites.sprites['eyeouter' + alt_cat_sprite].copy()
                eyes.blit(eye_section, (0, 0))
                pixel_array = pygame.PixelArray(eye_section)
                pixel_array.replace((255, 255, 255, 255), colour, distance=0)
                del pixel_array
                eyes.blit(eye_section, (0, 0))
                
                colour = pygame.Color(data["pupil"] if phenotype.pinkdilute[0] != 'dp' and not game_setting_get('black_pupils') else ([0, 0, 0] if phenotype.pinkdilute[0] != 'dp' and (phenotype.pointgene[1] != "c" or phenotype.pointgene[0] == "C") else [80, 20, 29]))
                eye_section = sprites.sprites['eyepupil' + alt_cat_sprite].copy()
                pixel_array = pygame.PixelArray(eye_section)
                pixel_array.replace((255, 255, 255, 255), colour, distance=0)
                del pixel_array
                eyes.blit(eye_section, (0, 0))
                return eyes

            if(int(cat_sprite) < 21 and int(cat_sprite) > 2):
                lefteye = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                righteye = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                special = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)

                lefteye.blit(sprites.sprites['left' + alt_cat_sprite], (0, 0))
                righteye.blit(sprites.sprites['right' + alt_cat_sprite], (0, 0))

                lefteye.blit(construct_eye_colour(phenotype.lefteyetype), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                righteye.blit(construct_eye_colour(phenotype.righteyetype), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                gensprite.blit(lefteye, (0, 0))
                gensprite.blit(righteye, (0, 0))

                if sprite_age == 1:
                    lefteye.blit(sprites.sprites['left' + alt_cat_sprite], (0, 0))
                    righteye.blit(sprites.sprites['right' + alt_cat_sprite], (0, 0))
                    lefteye.blit(construct_eye_colour(phenotype.lefteyetype.split(' ; ')[0] + ' ; blue'), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    righteye.blit(construct_eye_colour(phenotype.righteyetype.split(' ; ')[0] + ' ; blue'), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    lefteye.set_alpha(200)
                    righteye.set_alpha(200)
                    gensprite.blit(lefteye, (0, 0))
                    gensprite.blit(righteye, (0, 0))


                if(phenotype.extraeye):
                    special.blit(sprites.sprites[phenotype.extraeye + alt_cat_sprite], (0, 0))
                    special.blit(construct_eye_colour(phenotype.extraeyetype), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    gensprite.blit(special, (0, 0))
                    if sprite_age == 1:
                        special.blit(sprites.sprites[phenotype.extraeye + alt_cat_sprite], (0, 0))
                        special.blit(construct_eye_colour(phenotype.extraeyetype.split(' ; ')[0] + ' ; blue'), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        special.set_alpha(150)
                        gensprite.blit(special, (0, 0))
            
            return gensprite

        age = cat.moons

        if int(cat_sprite) < 3:
            age = 0
        elif 2 < int(cat_sprite) < 6 and (5 < cat.moons or cat.moons < 1):
            age = 4
        elif 5 < int(cat_sprite) < 9 and (11 < cat.moons or cat.moons < 6):
            age = 10
        elif cat_sprite in ['20', '22'] and (12 < cat.moons or cat.moons < 6):
            age = 6
        elif int(cat_sprite) > 8 and cat_sprite not in ['20', '22'] and cat.moons < 12:
            age = 60
        gensprite.blit(GenSprite(phenotype, age), (0, 0))

        if(cat.chimerapheno):
            geno = deepcopy(cat.chimerapheno)
            if hide_white:
                geno.white = ["w", "w"]
                geno.white_pattern = "No"
                geno.PhenotypeOutput()
            chimerapatches = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
            for pattern in cat.chimerapheno.chimerapattern:
                chimerapatches.blit(sprites.sprites[pattern + cat_sprite], (0, 0))
            chimerapatches.blit(GenSprite(geno, age), (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            gensprite.blit(chimerapatches, (0, 0))

        if not scars_hidden:
            for scar in cat.pelt.scars:
                if scar in cat.pelt.general_scars:
                    sprite_name = (
                        f"{sprites.SCAR_DATA['spritesheet']}{scar}{cat_sprite}"
                    )
                    gensprite.blit(sprites.sprites[sprite_name], (0, 0))

        # setting the lineart color to override on accessories & missing bits
        lineart_color = (
            pygame.Color(
                constants.CONFIG["cat_sprites"]["lineart_color_sc"]
                if cat.status.group == CatGroup.STARCLAN
                else constants.CONFIG["cat_sprites"]["lineart_color_df"]
            )
            if cat.status.group != CatGroup.UNKNOWN_RESIDENCE
            else None
        )

        gradient_surface = (
            sprites.sprites["line_ur_gradient" + cat_sprite]
            if dead and cat.status.group == CatGroup.UNKNOWN_RESIDENCE
            else None
        )

        def _recolor_lineart(
            sprite, color=None, source: pygame.Surface = None
        ) -> pygame.Surface:
            """
            Helper function to set the appropriate lineart color for the living status of the cat
            :param sprite: lineart to recolor
            :param color: color to apply to all pixels
            :param source: source surface of same size as sprite to use instead of color
            :return:
            """
            if not dead:
                return sprite

            if color is None and source is None:
                raise ValueError(
                    "Must provide either `color` or `source` for _recolor_lineart"
                )

            out = sprite.copy()
            if color:
                pixel_array = pygame.PixelArray(out)
                pixel_array.replace((0, 0, 0), color, distance=0)
                del pixel_array
                return out

            width, height = sprite.get_size()
            for x in range(width):
                for y in range(height):
                    if sprite.get_at((x, y)) == (pygame.Color(0, 0, 0)):
                        color = source.get_at((x, y))
                        out.set_at((x, y), color)
            return out

        # draw line art
        if game_setting_get('shaders') and not dead:
            gensprite.blit(sprites.sprites['shader_mask' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            gensprite.blit(
                sprites.sprites['shader_lighting' + cat_sprite], (0, 0))

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

        # if not dead:
        if(cat.phenotype.fold[0] != 'Fd'):
            if(cat.phenotype.curl[0] == 'Cu'):
                earlines.blit(sprites.sprites['curllines' + cat_sprite], (0, 0))
            else:
                earlines.blit(sprites.sprites['lineart' + cat_sprite], (0, 0))
            if phenotype.fourear[0] == "dup":
                earlines.blit(sprites.sprites['fourears' + cat_sprite], (0, 0))
        elif(cat.phenotype.curl[0] == 'Cu'):
            earlines.blit(sprites.sprites['fold_curllines' + cat_sprite], (0, 0))
        else:
            earlines.blit(sprites.sprites['foldlines' + cat_sprite], (0, 0))

        if('rexed' in phenotype.furtype or 'wiry' in phenotype.furtype):
            if not dead or cat.status.group == CatGroup.UNKNOWN_RESIDENCE:
                bodylines.blit(sprites.sprites['rexlineart' + cat_sprite], (0, 0))
            elif cat.status.group == CatGroup.DARK_FOREST:
                bodylines.blit(sprites.sprites['rexlineartdf' + cat_sprite], (0, 0))
            else:
                bodylines.blit(sprites.sprites['rexlineartdead' + cat_sprite], (0, 0))
        else:
            if not dead:
                bodylines.blit(sprites.sprites['lineart' + cat_sprite], (0, 0))
            elif cat.status.group == CatGroup.UNKNOWN_RESIDENCE:
                bodylines.blit(sprites.sprites['lineart_ur' + cat_sprite], (0, 0))
            elif cat.status.group == CatGroup.DARK_FOREST:
                bodylines.blit(sprites.sprites['lineart_df' + cat_sprite], (0, 0))
            else:
                bodylines.blit(sprites.sprites['lineart_sc' + cat_sprite], (0, 0))
            
        if int(cat_sprite) > 2:
            earlines.blit(sprites.sprites['isolateears' + alt_cat_sprite],
                      (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            lineart.blit(earlines, (0, 0))
            bodylines.blit(sprites.sprites['noears' + alt_cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        lineart.blit(bodylines, (0, 0))
        new_sprite.blit(_recolor_lineart(
                            lineart,
                            lineart_color,
                            gradient_surface,
                        ), (0, 0))

        # draw skin and scars2
        blendmode = pygame.BLEND_RGBA_MIN

        gensprite = new_sprite
        if cat.phenotype.bobtailnr > 0:
            gensprite.blit(_recolor_lineart(
                sprites.sprites['bobtail' +
                                str(cat.phenotype.bobtailnr) + cat_sprite],
                            lineart_color,
                            gradient_surface,
                        ), (0, 0))
        gensprite.set_colorkey((0, 0, 255))
        new_sprite = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
        new_sprite.blit(gensprite, (0, 0))

        if not scars_hidden:
            for scar in cat.pelt.scars:
                if scar in cat.pelt.missing_part_scars:
                    sprite_name = f"{sprites.SCAR_MISSING_PART_DATA['spritesheet']}{scar}{cat_sprite}"
                    new_sprite.blit(
                        _recolor_lineart(
                            sprites.sprites[sprite_name],
                            lineart_color,
                            gradient_surface,
                        ),
                        (0, 0),
                        special_flags=blendmode,
                    )

        if is_today(SpecialDate.APRIL_FOOLS):
            if cat.phenotype.bobtailnr != 1 and "Pc" in phenotype.april_fools.get("polycaudal", []):
                tail = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                tail.blit(sprites.sprites['bobtail1' + cat_sprite], (0, 0))
                white = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                white.fill((255, 255, 255))
                tail.blit(white, (0, 0), special_flags=pygame.BLEND_RGB_MAX)
                tail.blit(new_sprite, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                offset = 2
                if cat_sprite in ["2", "12", "13", "14", "16", "18"]:
                    new_sprite.blit(tail, (offset, 1))
                elif cat_sprite in ["4", "6", "7", "8", "9", "10", "11", "15", "19", "20"]:
                    new_sprite.blit(tail, (-offset, -1))
                elif cat_sprite in ["1", "5"]:
                    new_sprite.blit(tail, (0, -2))
            
            if constants.CONFIG["fun"]["april_fools_hats"]:
                if not dead:
                    new_sprite.blit(sprites.sprites['aprilfoolslines' + cat_sprite], (0, 0))
                elif cat.status.group == CatGroup.DARK_FOREST:
                    new_sprite.blit(sprites.sprites['aprilfoolslineartdf' + cat_sprite], (0, 0))
                else:
                    new_sprite.blit(sprites.sprites['aprilfoolslineartdead' + cat_sprite], (0, 0))

        # draw accessories
        from scripts.cat.pelts import Pelt

        if not acc_hidden and cat.pelt.accessory:
            cat_accessories = cat.pelt.accessory
            categories = [
                "collar_accessories",
                "tail_accessories",
                "body_accessories",
                "head_accessories",
            ]
            for category in categories:
                for accessory in cat_accessories:
                    if accessory in getattr(Pelt, category):
                        if accessory in cat.pelt.plant_accessories:
                            sprite_name = f"{sprites.PLANT_DATA['spritesheet']}{accessory}{cat_sprite}"
                            new_sprite.blit(
                                _recolor_lineart(
                                    sprites.sprites[sprite_name],
                                    lineart_color,
                                    gradient_surface,
                                ),
                                (0, 0),
                            )
                        elif accessory in cat.pelt.wild_accessories:
                            sprite_name = f"{sprites.WILD_DATA['spritesheet']}{accessory}{cat_sprite}"
                            new_sprite.blit(
                                _recolor_lineart(
                                    sprites.sprites[sprite_name],
                                    lineart_color,
                                    gradient_surface,
                                ),
                                (0, 0),
                            )
                        elif accessory in cat.pelt.collar_accessories:
                            sprite_name = f"{sprites.COLLAR_DATA['spritesheet']}{accessory}{cat_sprite}"
                            new_sprite.blit(
                                _recolor_lineart(
                                    sprites.sprites[sprite_name],
                                    lineart_color,
                                    gradient_surface,
                                ),
                                (0, 0),
                            )

        # Apply fading fog
        if (
            cat.pelt.opacity <= 97
            and not cat.prevent_fading
            and get_clan_setting("fading")
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

            if cat.status.group == CatGroup.STARCLAN:
                temp = sprites.sprites["fadestarclan" + stage + cat_sprite].copy()
                temp.blit(new_sprite, (0, 0))
                new_sprite = temp
            elif cat.status.group == CatGroup.UNKNOWN_RESIDENCE:
                temp = sprites.sprites["fadeur" + stage + cat_sprite].copy()
                temp.blit(new_sprite, (0, 0))
                new_sprite = temp
            else:
                temp = sprites.sprites["fadedf" + stage + cat_sprite].copy()
                temp.blit(new_sprite, (0, 0))
                new_sprite = temp

        # ok! we have the sprite! now, do some layer things if the cat's already dead
        if dead:
            temp_sprite = pygame.Surface(
                (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA
            )

            if cat.status.group == CatGroup.STARCLAN:
                # no underlay

                # cat sprite
                temp_sprite.blit(new_sprite, (0, 0))

                # overlay
                temp_sprite.blit(
                    sprites.sprites["line_sc_overlay" + cat_sprite],
                    (0, 0),
                )
            elif cat.status.group == CatGroup.UNKNOWN_RESIDENCE:
                # underlay
                temp_sprite.blit(
                    sprites.sprites["line_ur_overlay" + cat_sprite],
                    (0, 0),
                )

                # cat sprite
                temp_sprite.blit(new_sprite, (0, 0))

                # overlay
                temp_sprite.blit(
                    sprites.sprites["line_ur_overlay" + cat_sprite],
                    (0, 0),
                )
            elif cat.status.group == CatGroup.DARK_FOREST:
                # no underlay

                # cat sprite
                temp_sprite.blit(new_sprite, (0, 0))

                # no overlay

            new_sprite = temp_sprite

        return new_sprite

    try:
        geno = deepcopy(cat.phenotype)
        if hide_white:
            geno.white = ["w", "w"]
            geno.white_pattern = "No"
            geno.PhenotypeOutput()
        new_sprite = draw_sprite(geno, cat_sprite)
        if cat.phenotype.somatic.get('base', False):
            som_sprite = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
            som_sprite.blit(sprites.sprites[geno.somatic["base"] + cat_sprite], (0, 0))
            som_sprite.blit(draw_sprite(geno, cat_sprite, somatic=True), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            new_sprite.blit(som_sprite, (0, 0))

    except (TypeError, KeyError):
        traceback.print_exc()
        logger.exception("Failed to load sprite")

        # Placeholder image
        new_sprite = image_cache.load_image(
            f"sprites/error_placeholder.png"
        ).convert_alpha()
    
    # reverse, if assigned so
    if cat.pelt.reverse:
        new_sprite = pygame.transform.flip(new_sprite, True, False)

    return new_sprite


# ---------------------------------------------------------------------------- #
#                                     OTHER                                    #
# ---------------------------------------------------------------------------- #


def chunks(L, n):
    return [L[x : x + n] for x in range(0, len(L), n)]


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
    if game_setting_get("dark mode"):
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
        game_settings_save(None)
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
with open(
    os.path.normpath(f"{resource_directory}illnesses.json"), "r", encoding="utf-8"
) as read_file:
    ILLNESSES = ujson.loads(read_file.read())

with open(
    os.path.normpath(f"{resource_directory}injuries.json"), "r", encoding="utf-8"
) as read_file:
    INJURIES = ujson.loads(read_file.read())

with open(
    os.path.normpath(f"{resource_directory}permanent_conditions.json"),
    "r",
    encoding="utf-8",
) as read_file:
    PERMANENT = ujson.loads(read_file.read())

langs = {"snippet": None, "prey": None}

SNIPPETS = None
PREY_LISTS = None

with open(
    os.path.normpath("resources/dicts/backstories.json"), "r", encoding="utf-8"
) as read_file:
    BACKSTORIES = ujson.loads(read_file.read())
