import logging
import threading
from multiprocessing.dummy import Pool as ThreadPool
import os
import traceback
from math import floor, ceil
from random import choice

import ujson

from scripts.cat.cats import Cat, Personality, BACKSTORIES
from scripts.cat.pelts import Pelt
from scripts.cat_relations.inheritance import Inheritance
from scripts.housekeeping.version import SAVE_VERSION_NUMBER
from .game_essentials import game
from ..cat.skills import CatSkills
from ..housekeeping.datadir import get_save_dir

logger = logging.getLogger(__name__)


def load_cats():
    try:
        json_load()
    except FileNotFoundError as e:
        game.switches["error_message"] = "Can't find clan_cats.json!"
        game.switches["traceback"] = e
        raise

def some_cats(all_cats, start, end):
    for i in range(start, end):
        if i > len(all_cats)-1:
            break
        # all_cats[i].load_conditions()

        # # this is here to handle paralyzed cats in old saves
        # if all_cats[i].pelt.paralyzed and "paralyzed" not in all_cats[i].permanent_condition:
        #     all_cats[i].get_permanent_condition("paralyzed")
        # elif "paralyzed" in all_cats[i].permanent_condition and not all_cats[i].pelt.paralyzed:
        #     all_cats[i].pelt.paralyzed = True

        # # load the relationships
        # try:
        #     if not all_cats[i].dead:
        #         all_cats[i].load_relationship_of_cat()
        #     else:
        #         all_cats[i].relationships = {}
        # except Exception as e:
        #     logger.exception(
        #         f"There was an error loading relationships for cat #{all_cats[i]}."
        #     )
        #     game.switches["error_message"] = (
        #         f"There was an error loading relationships for cat #{all_cats[i]}."
        #     )
        #     game.switches["traceback"] = e
        #     raise

        all_cats[i].inheritance = Inheritance(all_cats[i])

        # try:
        #     # initialization of thoughts
        #     all_cats[i].thoughts()
        # except Exception as e:
        #     logger.exception(
        #         f"There was an error when thoughts for cat #{all_cats[i]} are created."
        #     )
        #     game.switches["error_message"] = (
        #         f"There was an error when thoughts for cat #{all_cats[i]} are created."
        #     )
        #     game.switches["traceback"] = e
        #     raise

        # # Save integrety checks
        # if game.config["save_load"]["load_integrity_checks"]:
        #     save_check()

def json_load():
    all_cats = []
    cat_data = None
    clanname = game.switches["clan_list"][0]
    clan_cats_json_path = f"{get_save_dir()}/{clanname}/clan_cats.json"
    with open(f"resources/dicts/conversion_dict.json", "r") as read_file:
        convert = ujson.loads(read_file.read())
    try:
        with open(clan_cats_json_path, "r") as read_file:
            cat_data = ujson.loads(read_file.read())
    except PermissionError as e:
        game.switches["error_message"] = f"Can\t open {clan_cats_json_path}!"
        game.switches["traceback"] = e
        raise
    except ujson.JSONDecodeError as e:
        game.switches["error_message"] = f"{clan_cats_json_path} is malformed!"
        game.switches["traceback"] = e
        raise

    # create new cat objects
    for i, cat in enumerate(cat_data):
        try:
            try:
                new_cat = Cat(ID=cat["ID"],
                        prefix=cat["name_prefix"],
                        suffix=cat["name_suffix"],
                        specsuffix_hidden=(cat["specsuffix_hidden"] if 'specsuffix_hidden' in cat else False),
                        status=cat["status"],
                        parent1=cat["parent1"],
                        parent2=cat["parent2"],
                        parent3=cat.get("parent3"),
                        moons=cat["moons"],
                        genotype=cat["genotype"],
                        white_patterns=cat["white_pattern"],
                        chim_white=cat["chim_white"] if 'chim_white' in cat else None,
                        loading_cat=True)
            except:
                if cat.get("genotype", False):
                    traceback.print_exc()
                    try:
                        cat['gender'] = cat['genotype']['sex']
                    except:
                        cat['gender'] = cat['genotype']['gender']
                new_cat = Cat(ID=cat["ID"],
                        prefix=cat["name_prefix"],
                        suffix=cat["name_suffix"],
                        specsuffix_hidden=(cat["specsuffix_hidden"] if 'specsuffix_hidden' in cat else False),
                        gender=cat['gender'],
                        status=cat["status"],
                        parent1=cat["parent1"],
                        parent3=cat.get("parent3"),
                        moons=cat["moons"],
                        loading_cat=True)
                
            new_cat.pelt = Pelt(
                new_cat.genotype,
                new_cat.phenotype,
                tint=cat.get('tint', 'none'),
                white_patches_tint=cat.get('white_tint', 'none'),
                paralyzed=cat["paralyzed"],
                kitten_sprite=(
                    cat["sprite_kitten"]
                    if "sprite_kitten" in cat
                    else cat["spirit_kitten"]
                ),
                adol_sprite=(
                    cat["sprite_adolescent"]
                    if "sprite_adolescent" in cat
                    else cat["spirit_adolescent"]
                ),
                adult_sprite=(
                    cat["sprite_adult"]
                    if "sprite_adult" in cat
                    else cat["spirit_adult"]
                ),
                senior_sprite=(
                    cat["sprite_senior"]
                    if "sprite_senior" in cat
                    else cat["spirit_elder"]
                ),
                para_adult_sprite=(
                    cat["sprite_para_adult"] if "sprite_para_adult" in cat else None
                ),
                reverse=cat["reverse"],
                scars=cat["scars"] if "scars" in cat else [],
                accessory=cat["accessory"],
                opacity=cat["opacity"] if "opacity" in cat else 100,
            )

            # Runs a bunch of apperence-related convertion of old stuff.
            new_cat.pelt.check_and_convert(convert)

            # converting old specialty saves into new scar parameter
            if "specialty" in cat or "specialty2" in cat:
                if cat["specialty"] is not None:
                    new_cat.pelt.scars.append(cat["specialty"])
                if cat["specialty2"] is not None:
                    new_cat.pelt.scars.append(cat["specialty2"])

            new_cat.adoptive_parents = (
                cat["adoptive_parents"] if "adoptive_parents" in cat else []
            )

            new_cat.genderalign = cat["gender_align"]
            # new_cat.pronouns = cat["pronouns"]
            new_cat.pronouns = (
                cat["pronouns"]
                if "pronouns" in cat
                else [new_cat.default_pronouns[0].copy()]
            )
            new_cat.backstory = cat["backstory"] if "backstory" in cat else None
            if new_cat.backstory in BACKSTORIES["conversion"]:
                new_cat.backstory = BACKSTORIES["conversion"][new_cat.backstory]
            new_cat.birth_cooldown = (
                cat["birth_cooldown"] if "birth_cooldown" in cat else 0
            )
            new_cat.moons = cat["moons"]

            if "facets" in cat:
                facets = [int(i) for i in cat["facets"].split(",")]
                new_cat.personality = Personality(
                    trait=cat["trait"],
                    kit_trait=new_cat.age in ["newborn", "kitten"],
                    lawful=facets[0],
                    social=facets[1],
                    aggress=facets[2],
                    stable=facets[3],
                )
            else:
                new_cat.personality = Personality(
                    trait=cat["trait"], kit_trait=new_cat.age in ["newborn", "kitten"]
                )

            new_cat.mentor = cat["mentor"]
            new_cat.former_mentor = (
                cat["former_mentor"] if "former_mentor" in cat else []
            )
            new_cat.patrol_with_mentor = (
                cat["patrol_with_mentor"] if "patrol_with_mentor" in cat else 0
            )
            new_cat.no_kits = cat["no_kits"]
            new_cat.no_mates = cat["no_mates"] if "no_mates" in cat else False
            new_cat.no_retire = cat["no_retire"] if "no_retire" in cat else False
            new_cat.exiled = cat["exiled"]
            new_cat.driven_out = cat["driven_out"] if "driven_out" in cat else False

            if "skill_dict" in cat:
                new_cat.skills = CatSkills(cat["skill_dict"])
            elif "skill" in cat:
                if new_cat.backstory is None:
                    if "skill" == "formerly a loner":
                        backstory = choice(["loner1", "loner2", "rogue1", "rogue2"])
                        new_cat.backstory = backstory
                    elif "skill" == "formerly a kittypet":
                        backstory = choice(["kittypet1", "kittypet2"])
                        new_cat.backstory = backstory
                    else:
                        new_cat.backstory = "clanborn"
                new_cat.skills = CatSkills.get_skills_from_old(
                    cat["skill"], new_cat.status, new_cat.moons
                )

            new_cat.mate = cat["mate"] if type(cat["mate"]) is list else [cat["mate"]]
            if None in new_cat.mate:
                new_cat.mate = [i for i in new_cat.mate if i is not None]
            new_cat.previous_mates = (
                cat["previous_mates"] if "previous_mates" in cat else []
            )
            new_cat.dead = cat["dead"]
            new_cat.dead_for = cat["dead_moons"]
            new_cat.experience = cat["experience"]
            new_cat.apprentice = cat["current_apprentice"]
            new_cat.former_apprentices = cat["former_apprentices"]
            new_cat.df = cat["df"] if "df" in cat else False

            new_cat.outside = cat["outside"] if "outside" in cat else False
            new_cat.faded_offspring = (
                cat["faded_offspring"] if "faded_offspring" in cat else []
            )
            new_cat.prevent_fading = (
                cat["prevent_fading"] if "prevent_fading" in cat else False
            )
            new_cat.favourite = cat["favourite"] if "favourite" in cat else False

            if "died_by" in cat or "scar_event" in cat or "mentor_influence" in cat:
                new_cat.convert_history(
                    cat["died_by"] if "died_by" in cat else [],
                    cat["scar_event"] if "scar_event" in cat else [],
                )

            all_cats.append(new_cat)

        except KeyError as e:
            if "ID" in cat:
                key = f" ID #{cat['ID']} "
            else:
                key = f" at index {i} "
            game.switches["error_message"] = (
                f"Cat{key}in clan_cats.json is missing {e}!"
            )
            game.switches["traceback"] = e
            raise

    portion = floor(len(all_cats)/4)
    length = ceil(len(all_cats)/portion)
    # args = [(all_cats, i*portion, i*portion+portion) for i in range(length)]
    # pool = ThreadPool(4)
    # pool.starmap(some_cats, args)

    # cat_threads = []

    # for i in range(length):
    #     cat_threads.append(threading.Thread(target=some_cats, args=(all_cats,(i*portion), (i*portion)+portion,)))
    #     cat_threads[-1].start()
    
    #replace cat ids with cat objects and add other needed variables
    for cat in all_cats:
        cat.load_conditions()

        # this is here to handle paralyzed cats in old saves
        if cat.pelt.paralyzed and "paralyzed" not in cat.permanent_condition:
            cat.get_permanent_condition("paralyzed")
        elif "paralyzed" in cat.permanent_condition and not cat.pelt.paralyzed:
            cat.pelt.paralyzed = True

        # load the relationships
        try:
            if not cat.dead:
                cat.load_relationship_of_cat()
            else:
                cat.relationships = {}
        except Exception as e:
            logger.exception(
                f"There was an error loading relationships for cat #{cat}."
            )
            game.switches["error_message"] = (
                f"There was an error loading relationships for cat #{cat}."
            )
            game.switches["traceback"] = e
            raise

        #cat.inheritance = Inheritance(cat)

        try:
            # initialization of thoughts
            cat.thoughts()
        except Exception as e:
            logger.exception(
                f"There was an error when thoughts for cat #{cat} are created."
            )
            game.switches["error_message"] = (
                f"There was an error when thoughts for cat #{cat} are created."
            )
            game.switches["traceback"] = e
            raise

        # Save integrety checks
        if game.config["save_load"]["load_integrity_checks"]:
            save_check()

    # for t in cat_threads:
    #     t.join()


def save_check():
    """Checks through loaded cats, checks and attempts to fix issues
    NOT currently working."""
    return

    for cat in Cat.all_cats:
        cat_ob = Cat.all_cats[cat]

        # Not-mutural mate relations
        # if cat_ob.mate:
        #    _temp_ob = Cat.all_cats.get(cat_ob.mate)
        #    if _temp_ob:
        #        # Check if the mate's mate feild is set to none
        #        if not _temp_ob.mate:
        #            _temp_ob.mate = cat_ob.ID
        #    else:
        #        # Invalid mate
        #        cat_ob.mate = None


def version_convert(version_info):
    """Does all save-conversion that require referencing the saved version number.
    This is a separate function, since the version info is stored in clan.json, but most conversion needs to be
    done on the cats. Clan data is loaded in after cats, however."""

    if version_info is None:
        return

    if version_info["version_name"] == SAVE_VERSION_NUMBER:
        # Save was made on current version
        return

    if version_info["version_name"] is None:
        version = 0
    else:
        version = version_info["version_name"]

    if version < 1:
        # Save was made before version number storage was implemented.
        # (ie, save file version 0)
        # This means the EXP must be adjusted.
        for c in Cat.all_cats.values():
            c.experience = c.experience * 3.2

    if version < 2:
        for c in Cat.all_cats.values():
            for con in c.injuries:
                moons_with = 0
                if "moons_with" in c.injuries[con]:
                    moons_with = c.injuries[con]["moons_with"]
                    c.injuries[con].pop("moons_with")
                c.injuries[con]["moon_start"] = game.clan.age - moons_with

            for con in c.illnesses:
                moons_with = 0
                if "moons_with" in c.illnesses[con]:
                    moons_with = c.illnesses[con]["moons_with"]
                    c.illnesses[con].pop("moons_with")
                c.illnesses[con]["moon_start"] = game.clan.age - moons_with

            for con in c.permanent_condition:
                moons_with = 0
                if "moons_with" in c.permanent_condition[con]:
                    moons_with = c.permanent_condition[con]["moons_with"]
                    c.permanent_condition[con].pop("moons_with")
                c.permanent_condition[con]["moon_start"] = game.clan.age - moons_with

    if version < 3 and game.clan.freshkill_pile:
        # freshkill start for older clans
        add_prey = game.clan.freshkill_pile.amount_food_needed() * 2
        game.clan.freshkill_pile.add_freshkill(add_prey)
