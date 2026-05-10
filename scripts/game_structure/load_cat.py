import logging
import os
import traceback
from math import floor
from random import choice
from copy import deepcopy
from operator import xor

import i18n
import ujson

from scripts.cat.cats import Cat, BACKSTORIES
from scripts.clan import clan_class
from ..cat.enums import CatGroup, CatRank
from scripts.cat.pelts import Pelt
from scripts.cat_relations.inheritance import Inheritance
from scripts.game_structure.game.switches import (
    switch_get_value,
    switch_set_value,
    Switch,
)
from scripts.game_structure.game.settings import game_setting_get
from ..cat.pronouns import get_new_pronouns
from scripts.housekeeping.version import SAVE_VERSION_NUMBER
from scripts.game_structure import constants
from scripts.game_structure import game
from ..cat.personality import Personality
from ..cat.skills import CatSkills
from ..cat.status import StatusDict
from ..housekeeping.datadir import get_save_dir

logger = logging.getLogger(__name__)


def load_cats():
    switch_set_value(
        Switch.error_message, ""
    )
    try:
        json_load()
    except FileNotFoundError as e:
        switch_set_value(Switch.error_message, "Can't find clan_cats.json!")
        switch_set_value(Switch.traceback, e)

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
        
    if info["eye_colour"] in ["BLUE", "COBALT", "CYAN", "DARKBLUE", "HEATHERBLUE", "PALEBLUE", "SUNLITICE"]:
        pigmentation = "blue"
        refraction = choice(range(5, 9))
        if info["eye_colour"] in ["COBALT", "DARKBLUE", "HEATHERBLUE"]:
            refraction = choice(range(9, 12))
        elif info["eye_colour"] in ["PALEBLUE", "CYAN"]:
            refraction = choice(range(1, 5))
        cat.phenotype.lefteyetype = f"R{refraction} ; {pigmentation}"
        cat.phenotype.righteyetype = f"R{refraction} ; {pigmentation}"
    elif info["eye_colour"] in ["GOLD", "YELLOW", "PALEYELLOW", "GREENYELLOW"]:
        pigmentation = choice(range(1, 6))
        refraction = choice(range(1, 4))
        if info["eye_colour"] == "PALEYELLOW":
            pigmentation = 1
        if info["eye_colour"] == "GREENYELLOW":
            refraction = choice(range(3, 6))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
        cat.phenotype.righteyetype = f"R{refraction} ; P{pigmentation}"
    elif info["eye_colour"] in ["AMBER", "COPPER", "BRONZE"]:
        pigmentation = choice(range(6, 12))
        refraction = choice(range(1, 4))
        if info["eye_colour"] == "AMBER":
            pigmentation = choice(range(5, 8))
        if info["eye_colour"] == "COPPER":
            pigmentation = choice(range(7, 10))
        if info["eye_colour"] == "BRONZE":
            pigmentation = choice(range(9, 12))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
        cat.phenotype.righteyetype = f"R{refraction} ; P{pigmentation}"
    elif info["eye_colour"] in ["EMERALD", "GREEN", "PALEGREEN", "SAGE"]:
        pigmentation = choice(range(2, 12))
        refraction = choice(range(9, 12))
        if info["eye_colour"] == "PALEGREEN":
            pigmentation = choice(range(2, 4))
        elif info["eye_colour"] == "SAGE":
            pigmentation = choice(range(7, 10))
        else:
            pigmentation = choice(range(3, 7))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
        cat.phenotype.righteyetype = f"R{refraction} ; P{pigmentation}"
    elif info["eye_colour"] in ["HAZEL"]:
        pigmentation = choice(range(5, 8))
        refraction = choice(range(5, 8))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
        cat.phenotype.righteyetype = f"R{refraction} ; P{pigmentation}"

    if info["eye_colour2"] in ["BLUE", "COBALT", "CYAN", "DARKBLUE", "HEATHERBLUE", "PALEBLUE", "SUNLITICE"]:
        pigmentation = "blue"
        refraction = choice(range(5, 9))
        if info["eye_colour"] in ["COBALT", "DARKBLUE", "HEATHERBLUE"]:
            refraction = choice(range(9, 12))
        elif info["eye_colour"] in ["PALEBLUE", "CYAN"]:
            refraction = choice(range(1, 5))
        cat.phenotype.lefteyetype = f"R{refraction} ; {pigmentation}"
    elif info["eye_colour2"] in ["GOLD", "YELLOW", "PALEYELLOW", "GREENYELLOW"]:
        pigmentation = choice(range(1, 6))
        refraction = choice(range(1, 4))
        if info["eye_colour"] == "PALEYELLOW":
            pigmentation = 1
        if info["eye_colour"] == "GREENYELLOW":
            refraction = choice(range(3, 6))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
    elif info["eye_colour2"] in ["AMBER", "COPPER", "BRONZE"]:
        pigmentation = choice(range(6, 12))
        refraction = choice(range(1, 4))
        if info["eye_colour"] == "AMBER":
            pigmentation = choice(range(5, 8))
        if info["eye_colour"] == "COPPER":
            pigmentation = choice(range(7, 10))
        if info["eye_colour"] == "BRONZE":
            pigmentation = choice(range(9, 12))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
    elif info["eye_colour2"] in ["EMERALD", "GREEN", "PALEGREEN", "SAGE"]:
        pigmentation = choice(range(2, 12))
        refraction = choice(range(9, 12))
        if info["eye_colour"] == "PALEGREEN":
            pigmentation = choice(range(2, 4))
        elif info["eye_colour"] == "SAGE":
            pigmentation = choice(range(7, 10))
        else:
            pigmentation = choice(range(3, 7))
        cat.phenotype.lefteyetype = f"R{refraction} ; P{pigmentation}"
    elif info["eye_colour2"] in ["HAZEL"]:
        pigmentation = choice(range(5, 8))
        refraction = choice(range(5, 8))
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

    if main_colour["pattern"] in ["ticked", "agouti", "singlestripe"] or (not cat.chimerapheno and patch_colour["pattern"] in ["ticked", "agouti", "singlestripe"]):
        cat.phenotype.ticked[0] = "Ta"
        if main_colour["pattern"] != "ticked" or (not cat.chimerapheno and patch_colour["pattern"] != "ticked"):
            cat.phenotype.tickgenes = "2222"
    elif main_colour["pattern"] in ["classic", "sokoke", "marbled"] or (not cat.chimerapheno and patch_colour["pattern"] in ["classic", "sokoke", "marbled"]):
        cat.phenotype.ticked = ["ta", "ta"]
        cat.phenotype.mack = ["mc", "mc"]
        if main_colour["pattern"] == "sokoke" or (not cat.chimerapheno and patch_colour["pattern"] == "sokoke"):
            cat.phenotype.sokoke = "2222"
    elif main_colour["pattern"] in ["tabby", "mackerel", "speckled", "rosette", "masked", "bengal"] or (not cat.chimerapheno and patch_colour["pattern"] in ["tabby", "mackerel", "speckled", "rosette", "masked", "bengal"]):
        cat.phenotype.ticked = ["ta", "ta"]
        cat.phenotype.mack[0] = "Mc"
        cat.phenotype.spotted = "0000"
        if main_colour["pattern"] in ["speckled", "rosette", "bengal"] or (not cat.chimerapheno and patch_colour["pattern"] in ["speckled", "rosette", "bengal"]):
            cat.phenotype.spotted = "2222"
    if (main_colour["pattern"] in ["single", "singlecolour", "twocolour", "smoke"] and main_colour["colour"] in tabby_bases):
        cat.phenotype.ticked[0] = "Ta"
    
    if cat.chimerapheno:
        cat.chimerapheno.agouti[0] = "A"
        if patch_colour["pattern"] in ["bengal", "rosette", "marbled"]:
            cat.chimerapheno.bengal = "2222"
            if patch_colour["pattern"] != "rosette":
                cat.chimerapheno.agouti = ["Apb", "a"]

        if patch_colour["pattern"] in ["ticked", "agouti", "singlestripe"]:
            cat.chimerapheno.ticked[0] = "Ta"
            if patch_colour["pattern"] != "ticked":
                cat.chimerapheno.tickgenes = "2222"
        elif patch_colour["pattern"] in ["classic", "sokoke", "marbled"]:
            cat.chimerapheno.ticked = ["ta", "ta"]
            cat.chimerapheno.mack = ["mc", "mc"]
            if patch_colour["pattern"] == "sokoke":
                cat.chimerapheno.sokoke = "2222"
        elif patch_colour["pattern"] in ["tabby", "mackerel", "speckled", "rosette", "masked", "bengal"]:
            cat.chimerapheno.ticked = ["ta", "ta"]
            cat.chimerapheno.mack[0] = "Mc"
            cat.chimerapheno.spotted = "0000"
            if patch_colour["pattern"] in ["speckled", "rosette", "bengal"]:
                cat.chimerapheno.spotted = "2222"
        elif (patch_colour["pattern"] in ["single", "singlecolour", "twocolour", "smoke"] and patch_colour["colour"] not in tabby_bases) or (patch_colour["colour"] == "GHOST"):
            cat.chimerapheno.agouti = ["a", "a"]
        elif (patch_colour["pattern"] in ["single", "singlecolour", "twocolour", "smoke"] and patch_colour["colour"] in tabby_bases):
            cat.chimerapheno.ticked[0] = "Ta"
    
    if not patch_colour["pattern"] and main_colour["pattern"] in ["singlecolour", "twocolour"] and main_colour["colour"] == "WHITE":
        cat.phenotype.white[0] = ["W"]
    
    if main_colour["colour"] in ["WHITE", "PALEGREY", "SILVER", "GREY", "DARKGREY", "CREAM", "PALEGINGER", "LIGHTBROWN", "LILAC"]:
        cat.phenotype.dilute = ["d", "d"]
        cat.phenotype.rufousing = "0000"
    else:
        cat.phenotype.dilute[0] = "D"
    
    if cat.chimerapheno:
        if patch_colour["colour"] in ["WHITE", "PALEGREY", "SILVER", "GREY", "DARKGREY", "CREAM", "PALEGINGER", "LIGHTBROWN", "LILAC"]:
            cat.chimerapheno.dilute = ["d", "d"]
            cat.chimerapheno.rufousing = "0000"
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
        wbsum = 0
        while 12 > wbsum < 14:
            cat.phenotype.wideband = ""
            wbsum = 0
            for i in range(0, 8):
                cat.phenotype.wideband += choice(["1", "1", "2"])
                wbsum += int(cat.phenotype.wideband[i])
        if main_colour["pattern"] in ["single", "singlecolour", "twocolour", "smoke"] and main_colour["colour"] == "GOLDEN":
            cat.phenotype.wideband = "22222222"
    else:
        wbsum = 0
        while wbsum > 11:
            cat.phenotype.wideband = ""
            wbsum = 0
            for i in range(0, 8):
                cat.phenotype.wideband += choice(["1", "0", "0", "2"])
                wbsum += int(cat.phenotype.wideband[i])

    if cat.chimerapheno:
        if patch_colour["colour"] in ["WHITE", "GOLDEN", "LIGHTBROWN"]:
            wbsum = 0
            while 12 > wbsum < 14:
                cat.chimerapheno.wideband = ""
                wbsum = 0
                for i in range(0, 8):
                    cat.chimerapheno.wideband += choice(["1", "1", "2"])
                    wbsum += int(cat.chimerapheno.wideband[i])
            if patch_colour["pattern"] in ["single", "singlecolour", "twocolour", "smoke"] and patch_colour["colour"] == "GOLDEN":
                cat.chimerapheno.wideband = "22222222"
        else:
            wbsum = 0
            while wbsum > 11:
                cat.chimerapheno.wideband = ""
                wbsum = 0
                for i in range(0, 8):
                    cat.chimerapheno.wideband += choice(["1", "0", "0", "2"])
                    wbsum += int(cat.chimerapheno.wideband[i])

    if main_colour["colour"] in ["DARKGINGER"]:
        cat.phenotype.rufousing = "2222"
    if main_colour["colour"] in ["BLACK"]:
        cat.phenotype.rufousing = "0000"
        cat.phenotype.wideband = "00000000"
    if main_colour["colour"] in ["LILAC", "GREY"] or (main_colour["colour"] in ["SIENNA"] and main_colour["pattern"] in ["single", "singlecolour", "twocolour", "smoke"]):
        cat.phenotype.saturation = choice(range(0, 5))
    elif main_colour["colour"] in ["DARKGREY", "PALEGREY", "DARKBROWN", "GHOST"]:
        cat.phenotype.saturation = choice(range(5, 7))
    else:
        cat.phenotype.saturation = choice(range(2, 5))

    if cat.chimerapheno:
        if patch_colour["colour"] in ["DARKGINGER", "CHOCOLATE"]:
            cat.chimerapheno.rufousing = "2222"
        if patch_colour["colour"] in ["BLACK"]:
            cat.chimerapheno.rufousing = "0000"
            cat.chimerapheno.wideband = "00000000"
        if patch_colour["colour"] in ["LILAC", "GREY"] or (main_colour["colour"] in ["SIENNA"] and main_colour["pattern"] in ["single", "singlecolour", "twocolour", "smoke"]):
            cat.chimerapheno.saturation = choice(range(0, 5))
        if patch_colour["colour"] in ["DARKGREY", "PALEGREY", "DARKBROWN", "GHOST"]:
            cat.chimerapheno.saturation = choice(range(4, 7))
        else:
            cat.chimerapheno.saturation = choice(range(2, 5))
            
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
    for i, cat in enumerate(cat_data):
        try:
            if isinstance(cat["status"], str):
                # this sucks, but we need to get the actual str age to make sure nothing goes wonky
                age = None
                for key_age in Cat.age_moons.keys():
                    if cat["moons"] in range(
                        Cat.age_moons[key_age][0], Cat.age_moons[key_age][1] + 1
                    ):
                        age = key_age
                status_dict = {"rank": cat["status"], "age": age}
            else:
                status_dict = cat["status"]

            if "pattern" in cat:
                cat["tortie_marking"] = cat["pattern"]
                del cat["pattern"]
            try:
                new_cat = Cat(ID=cat["ID"],
                        prefix=cat["name_prefix"],
                        suffix=cat["name_suffix"],
                        specsuffix_hidden=(cat["specsuffix_hidden"] if 'specsuffix_hidden' in cat else False),
                        status_dict=status_dict,
                        backstory=cat["backstory"],
                        parent1=cat["parent1"],
                        parent2=cat["parent2"],
                        parent3=cat.get("parent3"),
                        moons=cat["moons"],
                        genotype=cat["genotype"],
                        chimerageno=cat["chimerageno"] if "chimerageno" in cat else cat["genotype"]["chimerageno"],
                        passes=cat["passes_genotype"] if "passes_genotype" in cat else 1,
                        white_patterns=cat["white_pattern"],
                        chim_white=cat["chim_white"] if 'chim_white' in cat else None,
                        chim_pattern=cat["chimera_pattern"] if "chimera_pattern" in cat else cat["genotype"]["chimerapattern"],
                        loading_cat=True)
                if cat.get("group"):
                    new_cat.group = cat.get("group")
            except Exception as e:
                if cat.get("genotype", False):
                    raise e
                new_cat = Cat(ID=cat["ID"],
                        prefix=cat["name_prefix"],
                        suffix=cat["name_suffix"],
                        specsuffix_hidden=(cat["specsuffix_hidden"] if 'specsuffix_hidden' in cat else False),
                        gender=cat['gender'],
                        status_dict=status_dict,
                        parent1=cat["parent1"],
                        parent2=cat["parent2"],
                        parent3=cat.get("parent3"),
                        moons=cat["moons"],
                        loading_cat=True)
                if not cat.get("genotype", False) and (game_setting_get("accurate_porting") or (not new_cat.parent1 and not new_cat.parent2)):
                    accurate_porting(new_cat, cat)

            if "tint" in cat:
                if cat["tint"] == "none":
                    cat["tint"] = None
            if "white_patches_tint" in cat:
                if cat["white_patches_tint"] == "none":
                    cat["white_patches_tint"] = None

            new_cat.pelt = Pelt(
                new_cat.phenotype,
                tint=cat.get('tint', 'none'),
                white_patches_tint=cat.get('white_tint', 'none'),
                paralyzed=cat["paralyzed"],
                newborn_sprite=cat.get("sprite_newborn"),
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

            # Runs a bunch of appearance-related conversion of old stuff.
            new_cat.pelt.check_and_convert(convert)

            # converting old specialty saves into new scar parameter
            if "specialty" in cat or "specialty2" in cat:
                if cat["specialty"] is not None:
                    new_cat.pelt.scars = (*new_cat.pelt.scars, cat["specialty"])
                if cat["specialty2"] is not None:
                    new_cat.pelt.scars = (*new_cat.pelt.scars, cat["specialty2"])

            new_cat.adoptive_parents = (
                cat["adoptive_parents"] if "adoptive_parents" in cat else []
            )

            new_cat.surrogate_parents = (
                cat["surrogate_parents"] if "surrogate_parents" in cat else []
            )

            new_cat.affair_parents = (
                cat["affair_parents"] if "affair_parents" in cat else []
            )

            new_cat.genderalign = cat["gender_align"]
            new_cat.pronouns = (
                cat["pronouns"]
                if "pronouns" in cat
                else {i18n.config.get("locale"): get_new_pronouns(new_cat.genderalign)}
            )
            new_cat.backstory = cat["backstory"] if "backstory" in cat else None
            if new_cat.backstory in BACKSTORIES["conversion"]:
                new_cat.backstory = BACKSTORIES["conversion"][new_cat.backstory]
            new_cat.birth_cooldown = (
                cat["birth_cooldown"] if "birth_cooldown" in cat else 0
            )
            new_cat.moons = cat["moons"]

            if "facets" in cat and cat["facets"] is not None:
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
                    cat["skill"], new_cat.status.rank, new_cat.age
                )

            new_cat.mate = cat["mate"] if type(cat["mate"]) is list else [cat["mate"]]
            if None in new_cat.mate:
                new_cat.mate = [i for i in new_cat.mate if i is not None]
            new_cat.previous_mates = (
                cat["previous_mates"] if "previous_mates" in cat else []
            )

            # checking for old dead
            if (
                cat.get("dead")
                or cat.get("df")
                or cat.get("driven_out")
                or cat.get("exiled")
                or cat.get("outside")
            ):
                if cat.get("dead") and not new_cat.status.group.is_afterlife():
                    if cat.get("df"):
                        new_cat.status.send_to_afterlife(
                            target_ID=CatGroup.DARK_FOREST_ID
                        )
                    elif cat.get("outside"):
                        new_cat.status.send_to_afterlife(
                            target_ID=CatGroup.UNKNOWN_RESIDENCE_ID
                        )
                    else:
                        new_cat.status.send_to_afterlife(target_ID=CatGroup.STARCLAN_ID)

                else:
                    # these should properly change the cat's status to align with old bool info
                    if cat.get("exiled"):
                        new_cat.status.exile_from_group()
                    elif cat.get("outside") and not new_cat.status.is_outsider:
                        new_cat.status.become_lost()

                    if cat.get("driven_out"):
                        new_cat.status.change_group_nearness(CatGroup.PLAYER_CLAN_ID)

            if cat.get("dead_moons"):
                new_cat.dead_for = cat["dead_moons"]
            new_cat.experience = cat["experience"]
            new_cat.apprentice = cat["current_apprentice"]
            new_cat.former_apprentices = cat["former_apprentices"]

            new_cat.faded_offspring = (
                cat["faded_offspring"] if "faded_offspring" in cat else []
            )
            new_cat.prevent_fading = (
                cat["prevent_fading"] if "prevent_fading" in cat else False
            )
            new_cat.favourite = cat["favourite"] if "favourite" in cat else 0
            if new_cat.favourite == True:
                new_cat.favourite = 1

            if "died_by" in cat or "scar_event" in cat or "mentor_influence" in cat:
                new_cat.convert_history(
                    cat["died_by"] if "died_by" in cat else [],
                    cat["scar_event"] if "scar_event" in cat else [],
                )

            new_cat.starclan_affinity = cat.get("starclan_affinity", 0)
            new_cat.dark_forest_affinity = cat.get("dark_forest_affinity", 0)

            all_cats.append(new_cat)

        except KeyError as e:
            if "ID" in cat:
                key = f" ID #{cat['ID']} "
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
    other_clan_cats = [c for c in Cat.all_cats_list if c.status.is_other_clancat]
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

        cat.inheritance = Inheritance(cat)

        try:
            # initialization of thoughts
            cat.get_new_thought(other_clan_cats=other_clan_cats)
        except Exception as e:
            logger.exception(
                f"There was an error when thoughts for cat #{cat} are created."
            )
            switch_set_value(
                Switch.error_message,
                f"There was an error when thoughts for cat #{cat} are created.",
            )
            switch_set_value(Switch.traceback, e)
            raise

        # Save integrety checks
        if constants.CONFIG["save_load"]["load_integrity_checks"]:
            save_check()


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

    if version < 4:
        for c in Cat.all_cats.values():
            if not c.status.is_leader:
                continue
            for death in c.history.died_by:
                if death["text"] == "multi_lives":
                    # skip these as changing them will break stuff
                    continue
                death["text"] = (
                    "m_c lost a life when {PRONOUN/m_c/subject} " + death["text"]
                )
                # check if a period is present and append one if not
                if death["text"][-1] != ".":
                    death["text"] += "."
