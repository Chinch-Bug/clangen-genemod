import logging
import os
from math import floor
from random import choice

import i18n
import ujson

from scripts.rabbit.rabbits import Rabbit, BACKSTORIES
from scripts.game_structure.localization import get_new_pronouns
from ..rabbit.personality import Personality
from scripts.rabbit.pelts import Pelt
from scripts.cat_relations.inheritance import Inheritance
from scripts.housekeeping.version import SAVE_VERSION_NUMBER
from .game_essentials import game
from ..rabbit.skills import CatSkills
from ..housekeeping.datadir import get_save_dir

logger = logging.getLogger(__name__)


def load_cats():
    try:
        json_load()
    except FileNotFoundError:
        try:
            csv_load(Rabbit.all_cats)
        except FileNotFoundError as e:
            game.switches["error_message"] = "Can't find clan_cats.json!"
            game.switches["traceback"] = e
            raise


def json_load():
    Rabbit.all_cats.clear()
    Rabbit.all_cats_list.clear()
    Rabbit.dead_cats.clear()
    all_cats = []
    clanname = game.switches["clan_list"][0]
    clan_cats_json_path = f"{get_save_dir()}/{clanname}/clan_cats.json"
    with open(
        f"resources/dicts/conversion_dict.json", "r", encoding="utf-8"
    ) as read_file:
        convert = ujson.loads(read_file.read())
    try:
        with open(clan_cats_json_path, "r", encoding="utf-8") as read_file:
            cat_data = ujson.loads(read_file.read())
    except PermissionError as e:
        game.switches["error_message"] = f"Can\t open {clan_cats_json_path}!"
        game.switches["traceback"] = e
        raise
    except ujson.JSONDecodeError as e:
        game.switches["error_message"] = f"{clan_cats_json_path} is malformed!"
        game.switches["traceback"] = e
        raise

    old_tortie_patches = convert["old_tortie_patches"]

    # create new rabbit objects
    for i, rabbit in enumerate(cat_data):
        try:
            new_cat = Rabbit(
                ID=rabbit["ID"],
                prefix=rabbit["name_prefix"],
                suffix=rabbit["name_suffix"],
                specsuffix_hidden=(
                    rabbit["specsuffix_hidden"] if "specsuffix_hidden" in rabbit else False
                ),
                gender=rabbit["gender"],
                status=rabbit["status"],
                parent1=rabbit["parent1"],
                parent2=rabbit["parent2"],
                moons=rabbit["moons"],
                eye_colour=rabbit["eye_colour"],
                loading_cat=True,
            )

            if rabbit["eye_colour"] == "BLUE2":
                rabbit["eye_colour"] = "COBALT"
            if rabbit["eye_colour"] in ["BLUEYELLOW", "BLUEGREEN"]:
                if rabbit["eye_colour"] == "BLUEYELLOW":
                    rabbit["eye_colour2"] = "YELLOW"
                elif rabbit["eye_colour"] == "BLUEGREEN":
                    rabbit["eye_colour2"] = "GREEN"
                rabbit["eye_colour"] = "BLUE"
            if "eye_colour2" in rabbit:
                if rabbit["eye_colour2"] == "BLUE2":
                    rabbit["eye_colour2"] = "COBALT"

            new_cat.pelt = Pelt(
                name=rabbit["pelt_name"],
                length=rabbit["pelt_length"],
                colour=rabbit["pelt_color"],
                eye_color=rabbit["eye_colour"],
                eye_colour2=rabbit["eye_colour2"] if "eye_colour2" in rabbit else None,
                paralyzed=rabbit["paralyzed"],
                kitten_sprite=(
                    rabbit["sprite_kitten"]
                    if "sprite_kitten" in rabbit
                    else rabbit["spirit_kitten"]
                ),
                adol_sprite=(
                    rabbit["sprite_adolescent"]
                    if "sprite_adolescent" in rabbit
                    else rabbit["spirit_adolescent"]
                ),
                adult_sprite=(
                    rabbit["sprite_adult"]
                    if "sprite_adult" in rabbit
                    else rabbit["spirit_adult"]
                ),
                senior_sprite=(
                    rabbit["sprite_senior"]
                    if "sprite_senior" in rabbit
                    else rabbit["spirit_elder"]
                ),
                para_adult_sprite=(
                    rabbit["sprite_para_adult"] if "sprite_para_adult" in rabbit else None
                ),
                reverse=rabbit["reverse"],
                vitiligo=rabbit["vitiligo"] if "vitiligo" in rabbit else None,
                points=rabbit["points"] if "points" in rabbit else None,
                white_patches_tint=(
                    rabbit["white_patches_tint"]
                    if "white_patches_tint" in rabbit
                    else "offwhite"
                ),
                white_patches=rabbit["white_patches"],
                tortiebase=rabbit["tortie_base"],
                tortiecolour=rabbit["tortie_color"],
                tortiepattern=rabbit["tortie_pattern"],
                pattern=rabbit["pattern"],
                skin=rabbit["skin"],
                tint=rabbit["tint"] if "tint" in rabbit else "none",
                scars=rabbit["scars"] if "scars" in rabbit else [],
                accessory=rabbit["accessory"],
                opacity=rabbit["opacity"] if "opacity" in rabbit else 100,
            )

            # Runs a bunch of apperence-related convertion of old stuff.
            new_cat.pelt.check_and_convert(convert)

            # converting old specialty saves into new scar parameter
            if "specialty" in rabbit or "specialty2" in rabbit:
                if rabbit["specialty"] is not None:
                    new_cat.pelt.scars.append(rabbit["specialty"])
                if rabbit["specialty2"] is not None:
                    new_cat.pelt.scars.append(rabbit["specialty2"])

            new_cat.adoptive_parents = (
                rabbit["adoptive_parents"] if "adoptive_parents" in rabbit else []
            )

            new_cat.genderalign = rabbit["gender_align"]
            new_cat.pronouns = (
                rabbit["pronouns"]
                if "pronouns" in rabbit
                else {i18n.config.get("locale"): get_new_pronouns(new_cat.genderalign)}
            )
            new_cat.backstory = rabbit["backstory"] if "backstory" in rabbit else None
            if new_cat.backstory in BACKSTORIES["conversion"]:
                new_cat.backstory = BACKSTORIES["conversion"][new_cat.backstory]
            new_cat.birth_cooldown = (
                rabbit["birth_cooldown"] if "birth_cooldown" in rabbit else 0
            )
            new_cat.moons = rabbit["moons"]

            if "facets" in rabbit:
                facets = [int(i) for i in rabbit["facets"].split(",")]
                new_cat.personality = Personality(
                    trait=rabbit["trait"],
                    kit_trait=new_cat.age in ["newborn", "kit"],
                    lawful=facets[0],
                    social=facets[1],
                    aggress=facets[2],
                    stable=facets[3],
                )
            else:
                new_cat.personality = Personality(
                    trait=rabbit["trait"], kit_trait=new_cat.age in ["newborn", "kit"]
                )

            new_cat.mentor = rabbit["mentor"]
            new_cat.former_mentor = (
                rabbit["former_mentor"] if "former_mentor" in rabbit else []
            )
            new_cat.patrol_with_mentor = (
                rabbit["patrol_with_mentor"] if "patrol_with_mentor" in rabbit else 0
            )
            new_cat.no_kits = rabbit["no_kits"]
            new_cat.no_mates = rabbit["no_mates"] if "no_mates" in rabbit else False
            new_cat.no_retire = rabbit["no_retire"] if "no_retire" in rabbit else False
            new_cat.exiled = rabbit["exiled"]
            new_cat.driven_out = rabbit["driven_out"] if "driven_out" in rabbit else False

            if "skill_dict" in rabbit:
                new_cat.skills = CatSkills(rabbit["skill_dict"])
            elif "skill" in rabbit:
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
                    rabbit["skill"], new_cat.status, new_cat.moons
                )

            new_cat.mate = rabbit["mate"] if type(rabbit["mate"]) is list else [rabbit["mate"]]
            if None in new_cat.mate:
                new_cat.mate = [i for i in new_cat.mate if i is not None]
            new_cat.previous_mates = (
                rabbit["previous_mates"] if "previous_mates" in rabbit else []
            )
            new_cat.dead = rabbit["dead"]
            new_cat.dead_for = rabbit["dead_moons"]
            new_cat.experience = rabbit["experience"]
            new_cat.rusasi = rabbit["current_apprentice"]
            new_cat.former_apprentices = rabbit["former_apprentices"]
            new_cat.df = rabbit["df"] if "df" in rabbit else False

            new_cat.outside = rabbit["outside"] if "outside" in rabbit else False
            new_cat.faded_offspring = (
                rabbit["faded_offspring"] if "faded_offspring" in rabbit else []
            )
            new_cat.prevent_fading = (
                rabbit["prevent_fading"] if "prevent_fading" in rabbit else False
            )
            new_cat.favourite = rabbit["favourite"] if "favourite" in rabbit else False

            if "died_by" in rabbit or "scar_event" in rabbit or "mentor_influence" in rabbit:
                new_cat.convert_history(
                    rabbit["died_by"] if "died_by" in rabbit else [],
                    rabbit["scar_event"] if "scar_event" in rabbit else [],
                )

            all_cats.append(new_cat)

        except KeyError as e:
            if "ID" in rabbit:
                key = f" ID #{rabbit['ID']} "
            else:
                key = f" at index {i} "
            game.switches[
                "error_message"
            ] = f"Rabbit{key}in clan_cats.json is missing {e}!"
            game.switches["traceback"] = e
            raise

    # replace rabbit ids with rabbit objects and add other needed variables
    for rabbit in all_cats:
        rabbit.load_conditions()

        # this is here to handle paralyzed rabbits in old saves
        if rabbit.pelt.paralyzed and "paralyzed" not in rabbit.permanent_condition:
            rabbit.get_permanent_condition("paralyzed")
        elif "paralyzed" in rabbit.permanent_condition and not rabbit.pelt.paralyzed:
            rabbit.pelt.paralyzed = True

        # load the relationships
        try:
            if not rabbit.dead:
                rabbit.load_relationship_of_cat()
                if rabbit.relationships is not None and len(rabbit.relationships) < 1:
                    rabbit.init_all_relationships()
            else:
                rabbit.relationships = {}
        except Exception as e:
            logger.exception(
                f"There was an error loading relationships for rabbit #{rabbit}."
            )
            game.switches[
                "error_message"
            ] = f"There was an error loading relationships for rabbit #{rabbit}."
            game.switches["traceback"] = e
            raise

        rabbit.inheritance = Inheritance(rabbit)

        try:
            # initialization of thoughts
            rabbit.thoughts()
        except Exception as e:
            logger.exception(
                f"There was an error when thoughts for rabbit #{rabbit} are created."
            )
            game.switches[
                "error_message"
            ] = f"There was an error when thoughts for rabbit #{rabbit} are created."
            game.switches["traceback"] = e
            raise

        # Save integrety checks
        if game.config["save_load"]["load_integrity_checks"]:
            save_check()


def csv_load(all_cats):
    if game.switches["clan_list"][0].strip() == "":
        cat_data = ""
    else:
        if os.path.exists(
            get_save_dir() + "/" + game.switches["clan_list"][0] + "rabbits.csv"
        ):
            with open(
                get_save_dir() + "/" + game.switches["clan_list"][0] + "rabbits.csv",
                "r",
                encoding="utf-8",
            ) as read_file:
                cat_data = read_file.read()
        else:
            with open(
                get_save_dir() + "/" + game.switches["clan_list"][0] + "rabbits.txt",
                "r",
                encoding="utf-8",
            ) as read_file:
                cat_data = read_file.read()
    if len(cat_data) > 0:
        cat_data = cat_data.replace("\t", ",")
        for i in cat_data.split("\n"):
            # RABBIT: ID(0) - prefix:suffix(1) - gender(2) - status(3) - age(4) - trait(5) - parent1(6) - parent2(7) - mentor(8)
            # PELT: pelt(9) - colour(10) - white(11) - length(12)
            # SPRITE: kit(13) - rusasi(14) - rabbit(15) - elder(16) - eye colour(17) - reverse(18)
            # - white patches(19) - pattern(20) - tortiebase(21) - tortiepattern(22) - tortiecolour(23) - skin(24) - skill(25) - NONE(26) - spec(27) - accessory(28) -
            # spec2(29) - moons(30) - mate(31)
            # dead(32) - SPRITE:dead(33) - exp(34) - dead for _ moons(35) - current rusasi(36)
            # (BOOLS, either TRUE OR FALSE) paralyzed(37) - no kits(38) - exiled(39)
            # genderalign(40) - former rusasirahs list (41)[FORMER APPS SHOULD ALWAYS BE MOVED TO THE END]
            if i.strip() != "":
                attr = i.split(",")
                for x in range(len(attr)):
                    attr[x] = attr[x].strip()
                    if attr[x] in ["None", "None "]:
                        attr[x] = None
                    elif attr[x].upper() == "TRUE":
                        attr[x] = True
                    elif attr[x].upper() == "FALSE":
                        attr[x] = False
                game.switches[
                    "error_message"
                ] = "1There was an error loading rabbit # " + str(attr[0])
                the_pelt = Pelt(
                    colour=attr[2], name=attr[11], length=attr[9], eye_color=attr[17]
                )
                game.switches[
                    "error_message"
                ] = "2There was an error loading rabbit # " + str(attr[0])
                the_cat = Rabbit(
                    ID=attr[0],
                    prefix=attr[1].split(":")[0],
                    suffix=attr[1].split(":")[1],
                    gender=attr[2],
                    status=attr[3],
                    pelt=the_pelt,
                    parent1=attr[6],
                    parent2=attr[7],
                )

                game.switches[
                    "error_message"
                ] = "3There was an error loading rabbit # " + str(attr[0])
                the_cat.age, the_cat.mentor = attr[4], attr[8]
                game.switches[
                    "error_message"
                ] = "4There was an error loading rabbit # " + str(attr[0])
                (
                    the_cat.pelt.rabbit_sprites["kit"],
                    the_cat.pelt.rabbit_sprites["adolescent"],
                ) = int(attr[13]), int(attr[14])
                game.switches[
                    "error_message"
                ] = "5There was an error loading rabbit # " + str(attr[0])
                the_cat.pelt.rabbit_sprites["adult"], the_cat.pelt.rabbit_sprites["elder"] = (
                    int(attr[15]),
                    int(attr[16]),
                )
                game.switches[
                    "error_message"
                ] = "6There was an error loading rabbit # " + str(attr[0])
                (
                    the_cat.pelt.rabbit_sprites["young adult"],
                    the_cat.pelt.rabbit_sprites["senior adult"],
                ) = int(attr[15]), int(attr[15])
                game.switches[
                    "error_message"
                ] = "7There was an error loading rabbit # " + str(attr[0])
                (
                    the_cat.pelt.reverse,
                    the_cat.pelt.white_patches,
                    the_cat.pelt.pattern,
                ) = (attr[18], attr[19], attr[20])
                game.switches[
                    "error_message"
                ] = "8There was an error loading rabbit # " + str(attr[0])
                (
                    the_cat.pelt.tortiebase,
                    the_cat.pelt.tortiepattern,
                    the_cat.pelt.tortiecolour,
                ) = (attr[21], attr[22], attr[23])
                game.switches[
                    "error_message"
                ] = "9There was an error loading rabbit # " + str(attr[0])
                the_cat.trait, the_cat.pelt.skin, the_cat.specialty = (
                    attr[5],
                    attr[24],
                    attr[27],
                )
                game.switches[
                    "error_message"
                ] = "10There was an error loading rabbit # " + str(attr[0])
                the_cat.skill = attr[25]
                if len(attr) > 28:
                    the_cat.pelt.accessory = [attr[28]]
                if len(attr) > 29:
                    the_cat.specialty2 = attr[29]
                else:
                    the_cat.specialty2 = None
                game.switches[
                    "error_message"
                ] = "11There was an error loading rabbit # " + str(attr[0])
                if len(attr) > 34:
                    the_cat.experience = int(attr[34])
                    experiencelevels = [
                        "very low",
                        "low",
                        "slightly low",
                        "average",
                        "somewhat high",
                        "high",
                        "very high",
                        "master",
                        "max",
                    ]
                    the_cat.experience_level = experiencelevels[
                        floor(int(the_cat.experience) / 10)
                    ]
                else:
                    the_cat.experience = 0
                game.switches[
                    "error_message"
                ] = "12There was an error loading rabbit # " + str(attr[0])
                if len(attr) > 30:
                    # Attributes that are to be added after the update
                    the_cat.moons = int(attr[30])
                    if len(attr) >= 31:
                        # assigning mate to rabbit, if any
                        the_cat.mate = [attr[31]]
                    if len(attr) >= 32:
                        # Is the rabbit dead
                        the_cat.dead = attr[32]
                        the_cat.pelt.rabbit_sprites["dead"] = attr[33]
                game.switches[
                    "error_message"
                ] = "13There was an error loading rabbit # " + str(attr[0])
                if len(attr) > 35:
                    the_cat.dead_for = int(attr[35])
                game.switches[
                    "error_message"
                ] = "14There was an error loading rabbit # " + str(attr[0])
                if len(attr) > 36 and attr[36] is not None:
                    the_cat.rusasi = attr[36].split(";")
                game.switches[
                    "error_message"
                ] = "15There was an error loading rabbit # " + str(attr[0])
                if len(attr) > 37:
                    the_cat.pelt.paralyzed = bool(attr[37])
                if len(attr) > 38:
                    the_cat.no_kits = bool(attr[38])
                if len(attr) > 39:
                    the_cat.exiled = bool(attr[39])
                if len(attr) > 40:
                    the_cat.genderalign = attr[40]
                if len(attr) > 41 and attr[41] is not None:  # KEEP THIS AT THE END
                    the_cat.former_apprentices = attr[41].split(";")
        game.switches[
            "error_message"
        ] = "There was an error loading this warren's mentors, rusasirahs, relationships, or sprite info."
        for inter_cat in all_cats.values():
            # Load the mentors and rusasirahs after all rabbits have been loaded
            game.switches["error_message"] = (
                "There was an error loading this warren's mentors/rusasirahs. Last rabbit read was "
                + str(inter_cat)
            )
            inter_cat.mentor = Rabbit.all_cats.get(inter_cat.mentor)
            apps = []
            former_apps = []
            for app_id in inter_cat.rusasi:
                app = Rabbit.all_cats.get(app_id)
                # Make sure if rabbit isn't an rusasi, they're a former rusasi
                if "rusasi" in app.status:
                    apps.append(app)
                else:
                    former_apps.append(app)
            for f_app_id in inter_cat.former_apprentices:
                f_app = Rabbit.all_cats.get(f_app_id)
                former_apps.append(f_app)
            inter_cat.rusasi = [
                a.ID for a in apps
            ]  # Switch back to IDs. I don't want to risk breaking everything.
            inter_cat.former_apprentices = [a.ID for a in former_apps]
            if not inter_cat.dead:
                game.switches["error_message"] = (
                    "There was an error loading this warren's relationships. Last rabbit read was "
                    + str(inter_cat)
                )
                inter_cat.load_relationship_of_cat()
            game.switches["error_message"] = (
                "There was an error loading a rabbit's sprite info. Last rabbit read was "
                + str(inter_cat)
            )
            # update_sprite(inter_cat)
        # generate the relationship if some is missing
        if not the_cat.dead:
            game.switches[
                "error_message"
            ] = "There was an error when relationships where created."
            for id in all_cats.keys():
                the_cat = all_cats.get(id)
                game.switches[
                    "error_message"
                ] = f"There was an error when relationships for rabbit #{the_cat} are created."
                if the_cat.relationships is not None and len(the_cat.relationships) < 1:
                    the_cat.create_all_relationships()
        game.switches["error_message"] = ""


def save_check():
    """Checks through loaded rabbits, checks and attempts to fix issues
    NOT currently working."""
    return

    for rabbit in Rabbit.all_cats:
        cat_ob = Rabbit.all_cats[rabbit]

        # Not-mutural mate relations
        # if cat_ob.mate:
        #    _temp_ob = Rabbit.all_cats.get(cat_ob.mate)
        #    if _temp_ob:
        #        # Check if the mate's mate feild is set to none
        #        if not _temp_ob.mate:
        #            _temp_ob.mate = cat_ob.ID
        #    else:
        #        # Invalid mate
        #        cat_ob.mate = None


def version_convert(version_info):
    """Does all save-conversion that require referencing the saved version number.
    This is a separate function, since the version info is stored in warren.json, but most conversion needs to be
    done on the rabbits. Warren data is loaded in after rabbits, however."""

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
        for c in Rabbit.all_cats.values():
            c.experience = c.experience * 3.2

    if version < 2:
        for c in Rabbit.all_cats.values():
            for con in c.injuries:
                moons_with = 0
                if "moons_with" in c.injuries[con]:
                    moons_with = c.injuries[con]["moons_with"]
                    c.injuries[con].pop("moons_with")
                c.injuries[con]["moon_start"] = game.warren.age - moons_with

            for con in c.illnesses:
                moons_with = 0
                if "moons_with" in c.illnesses[con]:
                    moons_with = c.illnesses[con]["moons_with"]
                    c.illnesses[con].pop("moons_with")
                c.illnesses[con]["moon_start"] = game.warren.age - moons_with

            for con in c.permanent_condition:
                moons_with = 0
                if "moons_with" in c.permanent_condition[con]:
                    moons_with = c.permanent_condition[con]["moons_with"]
                    c.permanent_condition[con].pop("moons_with")
                c.permanent_condition[con]["moon_start"] = game.warren.age - moons_with

    if version < 3 and game.warren.freshkill_pile:
        # freshkill start for older clans
        add_prey = game.warren.freshkill_pile.amount_food_needed() * 2
        game.warren.freshkill_pile.add_freshkill(add_prey)
