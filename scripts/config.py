import tomllib
import os

from scripts.game_structure.game.switches import switch_get_value, Switch
from scripts.housekeeping.datadir import get_save_dir
from scripts.game_structure import constants, game

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
    from scripts.cat.cats import Cat
    from scripts.cat.enums import CatAge
    Cat.age_moons = {
        CatAge.NEWBORN: CONFIG["cat_ages"]["newborn"],
        CatAge.KITTEN: CONFIG["cat_ages"]["kitten"],
        CatAge.ADOLESCENT: CONFIG["cat_ages"]["adolescent"],
        CatAge.YOUNG_ADULT: CONFIG["cat_ages"]["young adult"],
        CatAge.ADULT: CONFIG["cat_ages"]["adult"],
        CatAge.SENIOR_ADULT: CONFIG["cat_ages"]["senior adult"],
        CatAge.SENIOR: CONFIG["cat_ages"]["senior"],
    }

def load_clan_config():
    global CONFIG
    reset_config()
    if switch_get_value(Switch.clan_list) and os.path.exists(
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


# config_path passed as a string using dot notation - ex "graduation.min_graduating_age"
def get_config(config_path):
    config_value = CONFIG
    config_keys = tuple(config_path.split("."))

    # checking cards first
    if hasattr(game.clan, "cruel_cards"):
        for card in game.clan.cruel_cards:
            card_info = constants.CRUEL_CARDS_ALL[card]
            if config_path in card_info["modifiers"]:
                config_value = card_info["modifiers"][config_path]

    # then checking game_config
    if config_value == CONFIG:
        for key in config_keys:
            config_value = config_value[key]

    return config_value
