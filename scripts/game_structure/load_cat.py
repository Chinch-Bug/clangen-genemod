import logging
import os
import traceback
from math import floor
from random import choice, randint
from copy import deepcopy
from operator import xor

import i18n
import ujson

from scripts.cat.cats import Cat, BACKSTORIES
from scripts.clan import clan_class
from scripts.cat.save_load import load_faded_cat_ids
from scripts.cat_relations.inheritance2 import inheritance_db
from scripts.cat.save_load import get_faded_ids
from ..cat.enums import CatGroup, CatRank
from scripts.cat.pelts import Pelt
from scripts.cat.sprites.load_sprites import sprites
from scripts.cat_relations.inheritance import Inheritance
from scripts.game_structure.game.switches import (
    switch_get_value,
    switch_set_value,
    Switch,
)
from scripts.game_structure.game.settings import game_setting_get
from ..cat.factories.enums import CatType
from ..cat.factories.load_cat_factory import LoadCatFactory
from ..cat.factories.typed_dicts import MentorshipDict, StatusDict
from ..cat.names import Name
from ..cat.pronouns import get_new_pronouns
from scripts.housekeeping.version import SAVE_VERSION_NUMBER
from scripts.config import get_config
from scripts.game_structure import game
from ..cat.personality import Personality
from ..cat.skills import CatSkills
from ..clan_resources.point_of_interest import (
    clear_pois,
    generate_and_add_new_poi,
    PoiType,
)
from ..housekeeping.datadir import get_save_dir

logger = logging.getLogger(__name__)


def load_cats():
    load_faded_cat_ids(switch_get_value(Switch.clan_save_id))
    try:
        json_load()
    except Exception:
        Cat.all_cats.clear()
        Cat.all_cats_list.clear()
        raise

def accurate_porting(cat, info):

    maingame_white = deepcopy(Pelt.maingame_white)

    additional_white = {
        "low": {
            "1": ["RIGHTEAR", "LEFTEAR", "ESTRELLA", "BACKSPOT", "EYEBAGS"],
            "2": ["EXTRA", "BLAZEMASK", "TEARS"],
            "3": ["TOPCOVER", "WINGS", "WOODPECKER", "FADEBELLY", "ROSINA"],
            "4": ["FADESPOTS", "MITAINE", "SKUNK", "BULLSEYE"],
            "5": ["SPARROW"]
        },
        "high": {
            "1": [],
            "2": [],
            "3": [],
            "4": [],
            "5": ["BLACKSTAR", "LOVEBUG", "FULLWHITE"]
        }
    }
    cat.phenotype.lykoi = ["Ly", "Ly"]
    cat.phenotype.pinkdilute = ["Dp", "Dp"]
    cat.phenotype.dilutemd = ["dm", "dm"]
    cat.phenotype.ext = ["E", "E"]
    cat.phenotype.corin = ["N", "N"]
    cat.phenotype.karp = ["k", "k"]
    cat.phenotype.bleach = ["Lb", "Lb"]
    cat.phenotype.ghosting = ["gh", "gh"]
    cat.phenotype.satin = ["St", "St"]
    cat.phenotype.glitter = ["Gl", "Gl"]

    cat.phenotype.curl = ["cu", "cu"]
    cat.phenotype.fold = ["fd", "fd"]
    cat.phenotype.fourear = ["Dup", "Dup"]
    cat.phenotype.manx = ["ab", "ab"]
    cat.phenotype.kab = ["Kab", "Kab"]
    cat.phenotype.toybob = ["tb", "tb"]
    cat.phenotype.jbob = ["Jb", "Jb"]
    cat.phenotype.kub = ["kub", "kub"]
    cat.phenotype.ring = ["Rt", "Rt"]
    cat.phenotype.munch = ["mk", "mk"]
    cat.phenotype.pax3 = ["NoDBE", "NoDBE"]
        
    for i in range(1, 6):
        maingame_white["low"][str(i)] += additional_white["low"][str(i)]
        maingame_white["high"][str(i)] += additional_white["high"][str(i)]

    if cat.phenotype.length == "hairless":
        cat.phenotype.ruhr = ["hrbd", "hrbd"]
        cat.phenotype.sedesp = ["Hr", "Hr"]

    if info["pelt_length"] == "short":
        cat.phenotype.furLength[0] = "L"
    else:
        cat.phenotype.furLength = ["l", "l"]
        cat.phenotype.longtype = info["pelt_length"]
    
    cat.pelt.length = info["pelt_length"]
    cat.phenotype.pointgene[0] = "C"
    cat.phenotype.white = ["w", "w"]
    cat.phenotype.white_pattern = []

    if info["white_patches"]:
        cat.phenotype.white_pattern = info["white_patches"] if isinstance(info["white_patches"], list) else [info["white_patches"]]
    
        white_found = False
        for i in range(1, 6):
            if cat.phenotype.white_pattern[0] in maingame_white["low"][str(i)]:
                if cat.phenotype.white_pattern[0] == "SKUNK":
                    cat.phenotype.white = ["wt", "w"]
                else:
                    cat.phenotype.white = ["ws", "w"]
                cat.phenotype.whitegrade = i
                white_found = True
                break
        if not white_found:
            for i in range(1, 6):
                if cat.phenotype.white_pattern[0] in maingame_white["high"][str(i)]:
                    cat.phenotype.white = ["ws", "ws"]
                    cat.phenotype.whitegrade = i
                    white_found = True
                    break
        if not white_found:
            if cat.phenotype.white_pattern[0] in list(sprites.WHITE_PATCH_COMBOS["little"].keys())+list(chain(*sprites.WHITE_LITTLE_DATA["sprite_list"])):
                cat.phenotype.white = ["ws", "w"]
                cat.phenotype.whitegrade = randint(1, 4)
            if cat.phenotype.white_pattern[0] in list(sprites.WHITE_PATCH_COMBOS["mid"].keys())+list(chain(*sprites.WHITE_MID_DATA["sprite_list"])):
                cat.phenotype.white = ["ws", "w"]
                cat.phenotype.whitegrade = randint(3, 6)
            if cat.phenotype.white_pattern[0] in list(sprites.WHITE_PATCH_COMBOS["high"].keys())+list(chain(*sprites.WHITE_HIGH_DATA["sprite_list"])):
                cat.phenotype.white = ["ws", "ws"]
                cat.phenotype.whitegrade = randint(1, 4)
            if cat.phenotype.white_pattern[0] in list(sprites.WHITE_PATCH_COMBOS["mostly"].keys())+list(chain(*sprites.WHITE_MOSTLY_DATA["sprite_list"])):
                cat.phenotype.white = ["ws", "ws"]
                cat.phenotype.whitegrade = randint(3, 6)
            if cat.phenotype.white_pattern[0] in []:
                cat.phenotype.white[0] = "wt"

    if info["vitiligo"]:
        if info["vitiligo"] == "KARPATI":
            cat.phenotype.karp = ["K", "k"]
        elif isinstance(cat.phenotype.white_pattern, list):
            cat.phenotype.vitiligo = True
            cat.phenotype.white_pattern.insert(0, info["vitiligo"])
        else:
            cat.phenotype.vitiligo = True
            cat.phenotype.white_pattern = [info["vitiligo"]]
    if info["points"]:
        if info["points"] == "SEPIAPOINT":
            cat.phenotype.pointgene = ["cb", "cb"]
        elif info["points"] == "MINKPOINT":
            cat.phenotype.pointgene = ["cb", "cs"]
        else:
            cat.phenotype.pointgene = ["cs", "cs"]
            if info["points"] == "RAGDOLL":
                cat.phenotype.white_pattern.insert(0, "TRIXIE")
                cat.phenotype.white = ["ws", "ws"]
                cat.phenotype.whitegrade = 3
        
    if info["eye_colour"] in ["DUSK"]:
        pigmentation = "albino"
        refraction = choice(range(3, 7))
        cat.phenotype.lefteyetype = f"R{refraction} ; {pigmentation}"
        cat.phenotype.righteyetype = f"R{refraction} ; {pigmentation}"
    elif info["eye_colour"] in ["WALNUT"]:
        pigmentation = 11
        refraction = choice(range(1, 10))
        cat.phenotype.lefteyetype = f"R{refraction} ; {pigmentation}"
        cat.phenotype.righteyetype = f"R{refraction} ; {pigmentation}"
    elif info["eye_colour"] in ["BLUE", "COBALT", "CYAN", "DARKBLUE", "HEATHERBLUE", "PALEBLUE", "SUNLITICE", "SEA", "BLUEBELL", "PERIWINKLE", "STORM"]:
        pigmentation = "blue"
        refraction = choice(range(5, 9))
        if info["eye_colour"] in ["COBALT", "DARKBLUE", "HEATHERBLUE", "SEA", "BLUEBELL", "STORM"]:
            refraction = choice(range(9, 12))
        elif info["eye_colour"] in ["PALEBLUE", "CYAN"]:
            refraction = choice(range(1, 5))
        elif info["eye_colour"] in ["PERIWINKLE"]:
            refraction = choice(range(4, 8))
        cat.phenotype.lefteyetype = f"R{refraction} ; {pigmentation}"
        cat.phenotype.righteyetype = f"R{refraction} ; {pigmentation}"
    elif info["eye_colour"] in ["SAND", "MAPLE"]:
        pigmentation = choice(range(1, 3))
        refraction = choice(range(1, 3))
        if info["eye_colour"] == "MAPLE":
            pigmentation = choice(range(5, 9))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
        cat.phenotype.righteyetype = f"R{refraction} ; P{pigmentation}"
    elif info["eye_colour"] in ["GOLD", "YELLOW", "PALEYELLOW", "GREENYELLOW", "MUSTARD"]:
        pigmentation = choice(range(1, 6))
        refraction = choice(range(1, 4))
        if info["eye_colour"] == "PALEYELLOW":
            pigmentation = 1
        if info["eye_colour"] == "GREENYELLOW":
            refraction = choice(range(3, 6))
        if info["eye_colour"] == "MUSTARD":
            pigmentation = choice(range(4, 7))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
        cat.phenotype.righteyetype = f"R{refraction} ; P{pigmentation}"
    elif info["eye_colour"] in ["AMBER", "COPPER", "BRONZE", "DAWN", "EARTHY", "WILDFIRE"]:
        pigmentation = choice(range(6, 12))
        refraction = choice(range(1, 4))
        if info["eye_colour"] == "AMBER":
            pigmentation = choice(range(5, 8))
        if info["eye_colour"] in ["COPPER", "EARTHY"]:
            pigmentation = choice(range(7, 10))
        if info["eye_colour"] == "BRONZE":
            pigmentation = choice(range(9, 12))
        if info["eye_colour"] in ["DAWN", "WILDFIRE"]:
            pigmentation = choice(range(8, 11))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
        cat.phenotype.righteyetype = f"R{refraction} ; P{pigmentation}"
    elif info["eye_colour"] in ["EMERALD", "GREEN", "PALEGREEN", "SAGE", "OLIVE", "FERN", "MOSSY", "LEAF", "LIME", "SWAMP"]:
        pigmentation = choice(range(3, 7))
        refraction = choice(range(9, 12))
        if info["eye_colour"] == "PALEGREEN":
            pigmentation = choice(range(2, 4))
        elif info["eye_colour"] in ["SAGE", "FERN", "LIME"]:
            pigmentation = choice(range(7, 10))
        elif info["eye_colour"] in ["OLIVE", "MOSSY"]:
            pigmentation = choice(range(9, 11))
        elif info["eye_colour"] in ["SWAMP"]:
            pigmentation = choice(range(9, 12))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
        cat.phenotype.righteyetype = f"R{refraction} ; P{pigmentation}"
    elif info["eye_colour"] in ["HAZEL", "GRASSYGREEN", "CATTAIL", "CACTUS"]:
        pigmentation = choice(range(5, 8))
        refraction = choice(range(5, 8))
        if info["eye_colour"] == "CATTAIL":
            pigmentation = choice(range(10, 12))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
        cat.phenotype.righteyetype = f"R{refraction} ; P{pigmentation}"
    elif info["eye_colour"] in ["AURORA", "AQUAMARINE"]:
        pigmentation = choice(range(1, 3))
        refraction = choice(range(10, 12))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
        cat.phenotype.righteyetype = f"R{refraction} ; P{pigmentation}"
    elif info["eye_colour"] in ["FOREST", "LICHEN", "ALGAE", "PERIDOT"]:
        pigmentation = 1
        refraction = choice(range(5, 9))
        if info["eye_colour"] == "LICHEN":
            pigmentation = choice(range(1, 4))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
        cat.phenotype.righteyetype = f"R{refraction} ; P{pigmentation}"

    if info["eye_colour2"] in ["DUSK"]:
        pigmentation = "albino"
        refraction = choice(range(3, 7))
        cat.phenotype.lefteyetype = f"R{refraction} ; {pigmentation}"
    elif info["eye_colour2"] in ["WALNUT"]:
        pigmentation = 11
        refraction = choice(range(1, 10))
        cat.phenotype.lefteyetype = f"R{refraction} ; {pigmentation}"
    elif info["eye_colour2"] in ["BLUE", "COBALT", "CYAN", "DARKBLUE", "HEATHERBLUE", "PALEBLUE", "SUNLITICE", "SEA", "BLUEBELL", "PERIWINKLE", "STORM"]:
        pigmentation = "blue"
        refraction = choice(range(5, 9))
        if info["eye_colour2"] in ["COBALT", "DARKBLUE", "HEATHERBLUE", "SEA", "BLUEBELL", "STORM"]:
            refraction = choice(range(9, 12))
        elif info["eye_colour2"] in ["PALEBLUE", "CYAN"]:
            refraction = choice(range(1, 5))
        elif info["eye_colour2"] in ["PERIWINKLE"]:
            refraction = choice(range(4, 8))
        cat.phenotype.lefteyetype = f"R{refraction} ; {pigmentation}"
    elif info["eye_colour2"] in ["GOLD", "YELLOW", "PALEYELLOW", "GREENYELLOW", "MUSTARD"]:
        pigmentation = choice(range(1, 6))
        refraction = choice(range(1, 4))
        if info["eye_colour2"] == "PALEYELLOW":
            pigmentation = 1
        if info["eye_colour2"] == "GREENYELLOW":
            refraction = choice(range(3, 6))
        if info["eye_colour2"] == "MUSTARD":
            pigmentation = choice(range(4, 7))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
    elif info["eye_colour2"] in ["AMBER", "COPPER", "BRONZE", "DAWN", "EARTHY"]:
        pigmentation = choice(range(6, 12))
        refraction = choice(range(1, 4))
        if info["eye_colour2"] == "AMBER":
            pigmentation = choice(range(5, 8))
        if info["eye_colour2"] in ["COPPER", "EARTHY"]:
            pigmentation = choice(range(7, 10))
        if info["eye_colour2"] == "BRONZE":
            pigmentation = choice(range(9, 12))
        if info["eye_colour2"] == "DAWN":
            pigmentation = choice(range(8, 11))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
    elif info["eye_colour2"] in ["EMERALD", "GREEN", "PALEGREEN", "SAGE", "OLIVE", "FERN", "MOSSY", "LEAF", "LIME", "SWAMP"]:
        pigmentation = choice(range(3, 7))
        refraction = choice(range(9, 12))
        if info["eye_colour2"] == "PALEGREEN":
            pigmentation = choice(range(2, 4))
        elif info["eye_colour2"] in ["SAGE", "FERN", "LIME"]:
            pigmentation = choice(range(7, 10))
        elif info["eye_colour2"] in ["OLIVE", "MOSSY"]:
            pigmentation = choice(range(9, 11))
        elif info["eye_colour2"] in ["SWAMP"]:
            pigmentation = choice(range(9, 12))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
    elif info["eye_colour2"] in ["HAZEL", "GRASSYGREEN", "CATTAIL", "CACTUS"]:
        pigmentation = choice(range(5, 8))
        refraction = choice(range(5, 8))
        if info["eye_colour2"] == "CATTAIL":
            pigmentation = choice(range(10, 12))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
    elif info["eye_colour2"] in ["AURORA", "AQUAMARINE"]:
        pigmentation = choice(range(1, 3))
        refraction = choice(range(10, 12))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
    elif info["eye_colour2"] in ["FOREST", "LICHEN", "ALGAE", "PERIDOT"]:
        pigmentation = 1
        refraction = choice(range(5, 9))
        if info["eye_colour2"] == "LICHEN":
            pigmentation = choice(range(1, 4))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"

    if "SUNLITICE" in [info["eye_colour"], info["eye_colour2"]]:
        if not info["eye_colour2"]:
            cat.phenotype.extraeye = "sectoral3"
        elif info["eye_colour"] == "SUNLITICE":
            cat.phenotype.extraeye = "sectoral2"
        else:
            cat.phenotype.extraeye = "sectoral1"
        cat.phenotype.extraeyetype = f"R{choice(range(1, 4))} ; P{choice(range(1, 3))}"

    red_bases = ["CREAM", "DARKGINGER", "GINGER", "PALEGINGER", "GOLDEN"]
    tabby_bases = ["CREAM", "DARKGINGER", "GINGER", "PALEGINGER", "GOLDEN", "WHITE"]
    cat.chimerapheno = None
    main_colour = {"pattern": info["pelt_name"].lower(), "colour": info["pelt_color"]}
    patch_colour = {"pattern": "", "colour": ""}
    is_tortie = False

    if info["pelt_name"].lower() in ["tortie", "calico"]:
        if not xor(info["pelt_color"] in red_bases, info["tortie_color"] in red_bases) or (info["tortie_pattern"] != info["tortie_base"] and 
        (info["pelt_color"] not in tabby_bases and info["tortie_base"] not in ["single", "smoke"]) and (info["tortie_color"] not in tabby_bases and info["tortie_pattern"] not in ["single", "smoke"])):
            cat.chimerapheno = deepcopy(cat.phenotype)
            cat.chimerapheno.chimerapattern = [info["tortie_marking"]]
            main_colour = {"pattern": info["tortie_base"], "colour": info["pelt_color"]}
            patch_colour = {"pattern": info["tortie_pattern"], "colour": info["tortie_color"]}
        else:
            if info["tortie_color"] in red_bases:
                main_colour = {
                    "pattern": info["tortie_base"], "colour": info["pelt_color"]}
                patch_colour = {
                    "pattern": info["tortie_pattern"], "colour": info["tortie_color"]}
            else:
                patch_colour = {
                    "pattern": info["tortie_base"], "colour": info["pelt_color"]}
                main_colour = {
                    "pattern": info["tortie_pattern"], "colour": info["tortie_color"]}
            is_tortie = True
    
    cat.phenotype.agouti[0] = "A"

    if main_colour["pattern"] in ["bengal", "rosette", "marbled"] or (not cat.chimerapheno and patch_colour["pattern"] in ["bengal", "rosette", "marbled"]):
        cat.phenotype.bengal = "2222"
    if main_colour["pattern"] in ["bengal", "masked", "marbled"] or (not cat.chimerapheno and patch_colour["pattern"] in ["bengal", "masked", "marbled"]):
        cat.phenotype.agouti = ["Apb", "a"]
    elif (main_colour["pattern"] in ["single", "singlecolour", "twocolour", "smoke"] and main_colour["colour"] not in tabby_bases) or (main_colour["colour"] == "GHOST"):
        cat.phenotype.agouti = ["a", "a"]

    if main_colour["pattern"] in ["ticked", "agouti", "singlestripe", "freckled"] or (not cat.chimerapheno and patch_colour["pattern"] in ["ticked", "agouti", "singlestripe", "freckled"]):
        cat.phenotype.ticked[0] = "Ta"
        if main_colour["pattern"] != "ticked" or (not cat.chimerapheno and patch_colour["pattern"] != "ticked"):
            cat.phenotype.tickgenes = "2222"
        if main_colour["pattern"] == "freckled" or (not cat.chimerapheno and patch_colour["pattern"] == "freckled"):
            cat.phenotype.ticked = ["Ta", "ta"]
            cat.phenotype.breakthrough = True
            cat.phenotype.mack[0] = "Mc"
    elif main_colour["pattern"] in ["classic", "sokoke", "marbled"] or (not cat.chimerapheno and patch_colour["pattern"] in ["classic", "sokoke", "marbled"]):
        cat.phenotype.ticked = ["ta", "ta"]
        cat.phenotype.mack = ["mc", "mc"]
        if main_colour["pattern"] == "sokoke" or (not cat.chimerapheno and patch_colour["pattern"] == "sokoke"):
            cat.phenotype.sokoke = "2222"
    elif main_colour["pattern"] in ["tabby", "mackerel", "speckled", "rosette", "masked", "bengal"] or (not cat.chimerapheno and patch_colour["pattern"] in ["tabby", "mackerel", "speckled", "rosette", "masked", "bengal"]):
        cat.phenotype.ticked = ["ta", "ta"]
        cat.phenotype.mack[0] = "Mc"
        cat.phenotype.spotted = "0000"
    if main_colour["pattern"] in ["speckled", "rosette", "bengal", "freckled"] or (not cat.chimerapheno and patch_colour["pattern"] in ["speckled", "rosette", "bengal", "freckled"]):
        cat.phenotype.spotted = "2222"
    if (main_colour["pattern"] in ["single", "singlecolour", "twocolour", "smoke"] and main_colour["colour"] in tabby_bases):
        cat.phenotype.ticked[0] = "Ta"
    
    if cat.chimerapheno:
        cat.chimerapheno.agouti[0] = "A"
        if patch_colour["pattern"] in ["bengal", "rosette", "marbled"]:
            cat.chimerapheno.bengal = "2222"
            if patch_colour["pattern"] != "rosette":
                cat.chimerapheno.agouti = ["Apb", "a"]

        if patch_colour["pattern"] in ["ticked", "agouti", "singlestripe", "freckled"]:
            cat.chimerapheno.ticked[0] = "Ta"
            if patch_colour["pattern"] != "ticked":
                cat.chimerapheno.tickgenes = "2222"
            if patch_colour["pattern"] == "freckled":
                cat.chimerapheno.ticked = ["Ta", "ta"]
                cat.chimerapheno.breakthrough = True
                cat.chimerapheno.mack[0] = "Mc"
        elif patch_colour["pattern"] in ["classic", "sokoke", "marbled"]:
            cat.chimerapheno.ticked = ["ta", "ta"]
            cat.chimerapheno.mack = ["mc", "mc"]
            if patch_colour["pattern"] == "sokoke":
                cat.chimerapheno.sokoke = "2222"
        elif patch_colour["pattern"] in ["tabby", "mackerel", "speckled", "rosette", "masked", "bengal"]:
            cat.chimerapheno.ticked = ["ta", "ta"]
            cat.chimerapheno.mack[0] = "Mc"
            cat.chimerapheno.spotted = "0000"
        elif (patch_colour["pattern"] in ["single", "singlecolour", "twocolour", "smoke"] and patch_colour["colour"] not in tabby_bases) or (patch_colour["colour"] == "GHOST"):
            cat.chimerapheno.agouti = ["a", "a"]
        elif (patch_colour["pattern"] in ["single", "singlecolour", "twocolour", "smoke"] and patch_colour["colour"] in tabby_bases):
            cat.chimerapheno.ticked[0] = "Ta"
        if patch_colour["pattern"] in ["speckled", "rosette", "bengal", "freckled"]:
            cat.chimerapheno.spotted = "2222"
    
    if not patch_colour["pattern"] and main_colour["pattern"] in ["singlecolour", "twocolour"] and main_colour["colour"] == "WHITE":
        cat.phenotype.white[0] = "W"
        cat.phenotype.white_pattern = "No"
    if "FULLWHITE" in cat.phenotype.white_pattern:
        cat.phenotype.white[0] = "W"
        cat.phenotype.white_pattern = "No"
    
    if main_colour["colour"] in ["WHITE", "PALEGREY", "SILVER", "GREY", "DARKGREY", "CREAM", "PALEGINGER", "LIGHTBROWN", "LILAC"]:
        cat.phenotype.dilute = ["d", "d"]
        cat.phenotype.rufousing = 0
    else:
        cat.phenotype.dilute[0] = "D"
    
    if cat.chimerapheno:
        if patch_colour["colour"] in ["WHITE", "PALEGREY", "SILVER", "GREY", "DARKGREY", "CREAM", "PALEGINGER", "LIGHTBROWN", "LILAC"]:
            cat.chimerapheno.dilute = ["d", "d"]
            cat.chimerapheno.rufousing = 0
        else:
            cat.chimerapheno.dilute[0] = "D"

    if main_colour["colour"] in ["LIGHTBROWN", "GOLDEN-BROWN"]:
        cat.phenotype.eumelanin = ["bl", "bl"]
    elif main_colour["colour"] in ["WHITE", "PALEGREY", "LILAC", "BROWN", "CHOCOLATE", "SIENNA"]:
        cat.phenotype.eumelanin = ["b", "b"]
    else:
        cat.phenotype.eumelanin[0] = "B"

    if cat.chimerapheno:
        if patch_colour["colour"] in ["LIGHTBROWN", "GOLDEN-BROWN"]:
            cat.chimerapheno.eumelanin = ["bl", "bl"]
        elif patch_colour["colour"] in ["WHITE", "PALEGREY", "LILAC", "BROWN", "CHOCOLATE", "SIENNA"]:
            cat.chimerapheno.eumelanin = ["b", "b"]
        else:
            cat.chimerapheno.eumelanin[0] = "B"
    
    if is_tortie:
        cat.phenotype.sexgene = ["O", "o"]
        if cat.phenotype.sex == "tom":
            cat.phenotype.sexgene.append("Y")
            cat.get_permanent_condition('sterile', born_with=True, genetic=True)
        cat.phenotype.tortiepattern = [info["tortie_marking"]]
    elif main_colour["colour"] in red_bases:
        cat.phenotype.sexgene[0] = "O"
        if cat.phenotype.sexgene[1] == "o":
            cat.phenotype.sexgene[1] = "O"
    elif patch_colour["colour"] not in red_bases:
        cat.phenotype.sexgene[0] = "o"
        if cat.phenotype.sexgene[1] == "O":
            cat.phenotype.sexgene[1] = "o"

    if cat.chimerapheno:
        if patch_colour["colour"] in red_bases:
            cat.chimerapheno.sexgene[0] = "O"
            if cat.chimerapheno.sexgene[1] == "o":
                cat.chimerapheno.sexgene[1] = "O"
        elif main_colour["colour"] not in red_bases:
            cat.chimerapheno.sexgene[0] = "o"
            if cat.chimerapheno.sexgene[1] == "O":
                cat.chimerapheno.sexgene[1] = "o"
    
    if main_colour["colour"] in ["WHITE", "SILVER", "GHOST"] and cat.phenotype.agouti != ["Apb", "a"]:
        cat.phenotype.silver[0] = "I"
    else:
        cat.phenotype.silver = ["i", "i"]

    if cat.chimerapheno:
        if patch_colour["colour"] in ["WHITE", "SILVER", "GHOST"]:
            cat.chimerapheno.silver[0] = "I"
        else:
            cat.chimerapheno.silver = ["i", "i"]

    if main_colour["colour"] in ["WHITE", "GOLDEN", "LIGHTBROWN"]:
        cat.phenotype.wideband = 13
        if main_colour["pattern"] in ["single", "singlecolour", "twocolour", "smoke"] and main_colour["colour"] == "GOLDEN":
            cat.phenotype.wideband = 16
    else:
        cat.phenotype.wideband = randint(0, 11)

    if cat.chimerapheno:
        if patch_colour["colour"] in ["WHITE", "GOLDEN", "LIGHTBROWN"]:
            cat.chimerapheno.wideband = 13
            if patch_colour["pattern"] in ["single", "singlecolour", "twocolour", "smoke"] and patch_colour["colour"] == "GOLDEN":
                cat.chimerapheno.wideband = 16
        else:
            cat.chimerapheno.wideband = randint(0, 11)

    if main_colour["colour"] in ["DARKGINGER"]:
        cat.phenotype.rufousing = 8
    if main_colour["colour"] in ["BLACK"]:
        cat.phenotype.rufousing = 0
        cat.phenotype.wideband = 0
    if main_colour["colour"] in ["LILAC", "GREY"] or (main_colour["colour"] in ["SIENNA"] and main_colour["pattern"] in ["single", "singlecolour", "twocolour", "smoke"]):
        cat.phenotype.fur_shade = choice(range(0, 5))
    elif main_colour["colour"] in ["DARKGREY", "PALEGREY", "DARKBROWN", "GHOST"]:
        cat.phenotype.fur_shade = choice(range(5, 7))
    else:
        cat.phenotype.fur_shade = choice(range(2, 5))

    if cat.chimerapheno:
        if patch_colour["colour"] in ["DARKGINGER", "CHOCOLATE"]:
            cat.chimerapheno.rufousing = 8
        if patch_colour["colour"] in ["BLACK"]:
            cat.chimerapheno.rufousing = 0
            cat.chimerapheno.wideband = 0
        if patch_colour["colour"] in ["LILAC", "GREY"] or (main_colour["colour"] in ["SIENNA"] and main_colour["pattern"] in ["single", "singlecolour", "twocolour", "smoke"]):
            cat.chimerapheno.fur_shade = choice(range(0, 5))
        if patch_colour["colour"] in ["DARKGREY", "PALEGREY", "DARKBROWN", "GHOST"]:
            cat.chimerapheno.fur_shade = choice(range(4, 7))
        else:
            cat.chimerapheno.fur_shade = choice(range(2, 5))
            
    cat.phenotype.GeneSort()
    cat.phenotype.PolyEval()
    cat.phenotype.EyeColourName()
    cat.phenotype.PhenotypeOutput(cat.phenotype.white_pattern)
    cat.phenotype.SpriteInfo(cat.moons)
    if cat.chimerapheno:
        cat.chimerapheno.GeneSort()
        cat.chimerapheno.PolyEval()
        cat.chimerapheno.EyeColourName()
        cat.chimerapheno.PhenotypeOutput(cat.chimerapheno.white_pattern)
        cat.chimerapheno.SpriteInfo(cat.moons)

def json_load():
    Cat.all_cats.clear()
    Cat.all_cats_list.clear()
    Inheritance.all_inheritances = {}
    all_cats = []
    clanname = switch_get_value(Switch.clan_list)[0]
    clan_cats_json_path = f"{get_save_dir()}/{clanname}/clan_cats.json"
    with open(
        f"resources/dicts/conversion_dict.json", "r", encoding="utf-8"
    ) as read_file:
        convert = ujson.loads(read_file.read())
    try:
        with open(clan_cats_json_path, "r", encoding="utf-8") as read_file:
            cat_data = ujson.loads(read_file.read())
    except PermissionError as e:
        switch_set_value(Switch.error_message, f"Can\'t open {clan_cats_json_path}!")
        switch_set_value(Switch.traceback, e)
        raise
    except ujson.JSONDecodeError as e:
        switch_set_value(Switch.error_message, f"{clan_cats_json_path} is malformed!")
        switch_set_value(Switch.traceback, e)
        raise

    # create new cat objects
    for i, cat_dict in enumerate(cat_data):
        try:
            if "pattern" in cat_dict:
                cat_dict["tortie_marking"] = cat_dict["pattern"]
                del cat_dict["pattern"]
            cat = LoadCatFactory.create_cat(**cat_dict)
            if not cat_dict.get("genotype", False) and (game_setting_get("accurate_porting") or (not cat.parent1 and not cat.parent2)):
                accurate_porting(cat, cat_dict)
                cat.pelt.init_sprite()
            if cat.favourite == True:
                cat.favourite = 1
            Cat.all_cats[cat.ID] = cat
            all_cats.append(cat)

        except KeyError as e:
            if "ID" in cat_dict:
                key = f" ID #{cat_dict['ID']} "
            else:
                key = f" at index {i} "
            switch_set_value(
                Switch.error_message, f"Cat{key}in clan_cats.json is missing {e}!"
            )
            switch_set_value(Switch.traceback, e)
            raise

    version_info = clan_class.load_clan()
    version_convert(version_info)

    # replace cat ids with cat objects and add other needed variables
    for cat in all_cats:
        if cat.status.rank in (CatRank.LEADER, CatRank.DEPUTY, CatRank.MEDICINE_CAT):
            if cat.status.group == CatGroup.STARCLAN:
                game.starclan.adjust_facets_by_cat(cat)
            elif cat.status.group == CatGroup.DARK_FOREST:
                game.dark_forest.adjust_facets_by_cat(cat)

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
            switch_set_value(
                Switch.error_message,
                f"There was an error loading relationships for cat #{cat}.",
            )
            switch_set_value(Switch.traceback, e)
            raise
        if get_config("save_load.load_integrity_checks"):
            save_check()

    inheritance_db.clear_stored_data()
    inheritance_db.load_inheritances(Cat, get_faded_ids)


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

    # freshkill start for older clans
    if version < 3 and game.clan.freshkill_pile:
        add_prey = game.clan.freshkill_pile.amount_food_needed() * 2
        game.clan.freshkill_pile.add_freshkill(add_prey)

    # death history text revision
    if version < 4:
        for c in Cat.all_cats.values():
            if not c.status.is_leader:
                continue
            for death in c.history.died_by:
                if death["text"] == "multi_lives":
                    # skip these as changing them will break stuff
                    continue
                if death["text"].startswith("m_c lost a life"):
                    # skip these as it duplicates the existing death text
                    continue
                death["text"] = (
                    "m_c lost a life when {PRONOUN/m_c/subject} " + death["text"]
                )
                # check if a period is present and append one if not
                if death["text"][-1] != ".":
                    death["text"] += "."

    # generate points of interest
    if version < 5:
        # remove any already loaded points of interest
        clear_pois()

        generate_and_add_new_poi(biome=game.clan.biome, category=PoiType.GATHERING)
        generate_and_add_new_poi(biome=game.clan.biome, category=PoiType.MOONPLACE)

        for i in range(3):
            generate_and_add_new_poi(biome=game.clan.biome, category=PoiType.TERRAIN, clan="1")
