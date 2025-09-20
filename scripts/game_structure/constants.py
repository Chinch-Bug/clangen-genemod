from pygame import Cursor, image, SYSTEM_CURSOR_ARROW
import ujson
import tomllib
import os
from scripts.game_structure.game.switches import Switch, switch_get_value
from scripts.housekeeping.datadir import get_save_dir

from scripts.screens.enums import GameScreen

# this is just to make referencing main menu screens as a whole easier,
# note that the clan creation screen is included and the clan settings screen is excluded. this is intended.
MENU_SCREENS = [
    GameScreen.SETTINGS,
    GameScreen.START,
    GameScreen.SWITCH_CLAN,
    GameScreen.MAKE_CLAN,
]

BIOME_TYPES = ["Forest", "Plains", "Mountainous", "Beach", "Wetlands", "Desert"]

SEASONS = ["Newleaf", "Greenleaf", "Leaf-fall", "Leaf-bare"]
SEASON_CALENDAR = [
    "Newleaf",
    "Newleaf",
    "Newleaf",
    "Greenleaf",
    "Greenleaf",
    "Greenleaf",
    "Leaf-fall",
    "Leaf-fall",
    "Leaf-fall",
    "Leaf-bare",
    "Leaf-bare",
    "Leaf-bare",
]

TEMPERAMENT_DICT = {
    "low_social": ["cunning", "proud", "bloodthirsty"],
    "mid_social": ["amiable", "stoic", "wary"],
    "high_social": ["gracious", "mellow", "logical"],
}

OUTSIDER_REPS = ("welcoming", "neutral", "hostile")
OTHER_CLAN_REPS = ("ally", "neutral", "hostile")

INJURY_GROUPS = {
    "battle_injury": [
        "claw-wound",
        "mangled leg",
        "mangled tail",
        "torn pelt",
        "cat bite",
    ],
    "minor_injury": ["sprain", "sore", "bruises", "scrapes"],
    "blunt_force_injury": ["broken bone", "broken back", "head damage", "broken jaw"],
    "hot_injury": ["heat exhaustion", "heat stroke", "dehydrated"],
    "cold_injury": ["shivering", "frostbite"],
    "big_bite_injury": [
        "bite-wound",
        "broken bone",
        "torn pelt",
        "mangled leg",
        "mangled tail",
    ],
    "small_bite_injury": ["bite-wound", "torn ear", "torn pelt", "scrapes"],
    "beak_bite": ["beak bite", "torn ear", "scrapes"],
    "rat_bite": ["rat bite", "torn ear", "torn pelt"],
    "sickness": ["greencough", "redcough", "whitecough", "yellowcough"],
}

EVENT_ALLOWED_CONDITIONS = [
    "tick bites",
    "claw-wound",
    "bite-wound",
    "cat bite",
    "beak bite",
    "snake bite",
    "quilled by a porcupine",
    "rat bite",
    "mangled leg",
    "mangled tail",
    "broken jaw",
    "broken bone",
    "sore",
    "bruises",
    "scrapes",
    "cracked pads",
    "small cut",
    "sprain",
    "bee sting",
    "joint pain",
    "dislocated joint",
    "torn pelt",
    "torn ear",
    "water in their lungs",
    "shivering",
    "frostbite",
    "burn",
    "severe burn",
    "shock",
    "dehydrated",
    "head damage",
    "damaged eyes",
    "broken back",
    "poisoned",
    "headache",
    "severe headache",
    "fleas",
    "seizure",
    "diarrhea",
    "running nose",
    "kittencough",
    "whitecough",
    "greencough",
    "yellowcough",
    "redcough",
    "carrionplace disease",
    "heat stroke",
    "heat exhaustion",
    "stomachache",
    "constant nightmares",
]

with open("resources/game_config.toml", "r", encoding="utf-8") as read_file:
    CONFIG = tomllib.loads(read_file.read())

def recursive_merge(dict1, dict2):
    for key, value in dict2.items():
        if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            dict1[key] = recursive_merge(dict1[key], value)
        else:
            # Merge non-dictionary values
            dict1[key] = value
    return dict1

def other_config_refreshes():
    global CONFIG
    from scripts.cat.cats import Cat
    from scripts.cat.enums import CatAge
    from scripts.game_structure import game
    Cat.age_moons = {
        CatAge.NEWBORN: CONFIG["cat_ages"]["newborn"],
        CatAge.KITTEN: CONFIG["cat_ages"]["kitten"],
        CatAge.ADOLESCENT: CONFIG["cat_ages"]["adolescent"],
        CatAge.YOUNG_ADULT: CONFIG["cat_ages"]["young adult"],
        CatAge.ADULT: CONFIG["cat_ages"]["adult"],
        CatAge.SENIOR_ADULT: CONFIG["cat_ages"]["senior adult"],
        CatAge.SENIOR: CONFIG["cat_ages"]["senior"],
    }
    game.prey_config = CONFIG["clan_resources"]["freshkill"]

def load_clan_config():
    global CONFIG
    reset_config()
    if os.path.exists(
        get_save_dir() +
        f"/{switch_get_value(Switch.clan_list)[0]}/game_config.toml"
    ):
        with open(
            get_save_dir()
            + f"/{switch_get_value(Switch.clan_list)[0]}/game_config.toml",
            "r",
            encoding="utf-8",
        ) as read_file:
            config_override = tomllib.loads(read_file.read())
            CONFIG = recursive_merge(CONFIG, config_override)
            other_config_refreshes()

def reset_config():
    global CONFIG
    with open("resources/game_config.toml", "r", encoding="utf-8") as read_file:
        CONFIG = tomllib.loads(read_file.read())
        other_config_refreshes()

with open("resources/placements.json", "r", encoding="utf-8") as read_file:
    LAYOUTS = ujson.loads(read_file.read())

CUSTOM_CURSOR = Cursor((9, 0), image.load("resources/images/cursor.png"))
DEFAULT_CURSOR = Cursor(SYSTEM_CURSOR_ARROW)
