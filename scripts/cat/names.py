"""
Module that handles the name generation for all cats.
"""
import contextlib
import os
import random

import ujson

from scripts.game_structure import constants
from scripts.cat.enums import CatRank, CatGroup, CatAge
from scripts.housekeeping.datadir import get_save_dir
from .alt_namer import Namer
from scripts.game_structure import game
from scripts.clan_package.settings.clan_settings import get_clan_setting


class Name:
    """
    Stores & handles name generation.
    """

    if os.path.exists('resources/dicts/names/alt_prefixes.json'):
        with open('resources/dicts/names/alt_prefixes.json') as read_file:
            mod_prefixes = ujson.loads(read_file.read())
    mod_suffixes = None
    if os.path.exists('resources/dicts/names/alt_suffixes.json'):
        with open('resources/dicts/names/alt_suffixes.json') as read_file:
            mod_suffixes = ujson.loads(read_file.read())
    if os.path.exists('resources/dicts/names/names.json'):
        with open('resources/dicts/names/names.json') as read_file:
            names_dict = ujson.loads(read_file.read())

        if os.path.exists(get_save_dir() + "/prefixlist.txt"):
            with open(
                str(get_save_dir() + "/prefixlist.txt"), "r", encoding="utf-8"
            ) as read_file:
                name_list = read_file.read()
                if_names = len(name_list)
            if if_names > 0:
                new_names = name_list.split("\n")
                for new_name in new_names:
                    if new_name != "":
                        if new_name.startswith("-"):
                            while new_name[1:] in names_dict["normal_prefixes"]:
                                names_dict["normal_prefixes"].remove(new_name[1:])
                        else:
                            names_dict["normal_prefixes"].append(new_name)

        if os.path.exists(get_save_dir() + "/suffixlist.txt"):
            with open(
                str(get_save_dir() + "/suffixlist.txt"), "r", encoding="utf-8"
            ) as read_file:
                name_list = read_file.read()
                if_names = len(name_list)
            if if_names > 0:
                new_names = name_list.split("\n")
                for new_name in new_names:
                    if new_name != "":
                        if new_name.startswith("-"):
                            while new_name[1:] in names_dict["normal_suffixes"]:
                                names_dict["normal_suffixes"].remove(new_name[1:])
                        else:
                            names_dict["normal_suffixes"].append(new_name)

        if os.path.exists(get_save_dir() + "/specialsuffixes.txt"):
            with open(
                str(get_save_dir() + "/specialsuffixes.txt", "r"), encoding="utf-8"
            ) as read_file:
                name_list = read_file.read()
                if_names = len(name_list)
            if if_names > 0:
                new_names = name_list.split("\n")
                for new_name in new_names:
                    if new_name != "":
                        if new_name.startswith("-"):
                            del names_dict["special_suffixes"][new_name[1:]]
                        elif ":" in new_name:
                            _tmp = new_name.split(":")
                            names_dict["special_suffixes"][_tmp[0]] = _tmp[1]

    def __init__(self,
                 cat=None,
                 prefix=None,
                 suffix=None,
                 honour=None,
                 biome=None,
                 specsuffix_hidden=False,
                 load_existing_name=False
                 ):
        self.prefix = prefix
        self.suffix = suffix
        self.specsuffix_hidden = specsuffix_hidden
        no_suffixes = get_clan_setting("no suffixes") and get_clan_setting("modded names")

        try:
            self.cat = cat
            self.status = cat.status
            self.moons = cat.moons
            self.phenotype = cat.phenotype
            self.chimpheno = cat.chimerapheno if cat.chimerapheno else None
            self.skills = cat.skills if cat.skills else None
            self.personality = cat.personality if cat.personality else None
            self.biome = biome
            self.honour = honour
        except AttributeError:
            self.status = None
            self.moons = None
            self.phenotype = None
            self.chimpheno = None
            self.skills = None
            self.personality = None
            self.biome = None
            self.honour = None

        name_fixpref = False
        # Set prefix
        if prefix is None:
            self.give_prefix(cat, biome, no_suffix=True if (suffix == "" or no_suffixes) else False)
            # needed for random dice when we're changing the Prefix
            name_fixpref = True

        # Set suffix
        if self.suffix is None:
            if no_suffixes and not load_existing_name:
                self.suffix = ""
                self.specsuffix_hidden = True
            else:
                self.give_suffix(self.skills, self.personality, biome, honour)
                if name_fixpref and self.prefix is None:
                    # needed for random dice when we're changing the Prefix
                    name_fixpref = False
    
    def load_clan_names(self, clan):
        if os.path.exists('resources/dicts/names/alt_prefixes.json'):
            with open('resources/dicts/names/alt_prefixes.json') as read_file:
                mod_prefixes = ujson.loads(read_file.read())
        mod_suffixes = None
        if os.path.exists('resources/dicts/names/alt_suffixes.json'):
            with open('resources/dicts/names/alt_suffixes.json') as read_file:
                mod_suffixes = ujson.loads(read_file.read())
        if os.path.exists('resources/dicts/names/names.json'):
            with open('resources/dicts/names/names.json') as read_file:
                names_dict = ujson.loads(read_file.read())

            if os.path.exists(get_save_dir() + "/prefixlist.txt"):
                with open(
                    str(get_save_dir() + "/prefixlist.txt"), "r", encoding="utf-8"
                ) as read_file:
                    name_list = read_file.read()
                    if_names = len(name_list)
                if if_names > 0:
                    new_names = name_list.split("\n")
                    for new_name in new_names:
                        if new_name != "":
                            if new_name.startswith("-"):
                                while new_name[1:] in names_dict["normal_prefixes"]:
                                    names_dict["normal_prefixes"].remove(
                                        new_name[1:])
                            else:
                                names_dict["normal_prefixes"].append(new_name)

            if os.path.exists(get_save_dir() + "/suffixlist.txt"):
                with open(
                    str(get_save_dir() + "/suffixlist.txt"), "r", encoding="utf-8"
                ) as read_file:
                    name_list = read_file.read()
                    if_names = len(name_list)
                if if_names > 0:
                    new_names = name_list.split("\n")
                    for new_name in new_names:
                        if new_name != "":
                            if new_name.startswith("-"):
                                while new_name[1:] in names_dict["normal_suffixes"]:
                                    names_dict["normal_suffixes"].remove(
                                        new_name[1:])
                            else:
                                names_dict["normal_suffixes"].append(new_name)

            if os.path.exists(get_save_dir() + "/specialsuffixes.txt"):
                with open(
                    str(get_save_dir() + "/specialsuffixes.txt", "r"), encoding="utf-8"
                ) as read_file:
                    name_list = read_file.read()
                    if_names = len(name_list)
                if if_names > 0:
                    new_names = name_list.split("\n")
                    for new_name in new_names:
                        if new_name != "":
                            if new_name.startswith("-"):
                                del names_dict["special_suffixes"][new_name[1:]]
                            elif ":" in new_name:
                                _tmp = new_name.split(":")
                                names_dict["special_suffixes"][_tmp[0]] = _tmp[1]


        if not os.path.exists(get_save_dir() + f"/{clan}" + "/names"):
            return
        if os.path.exists(get_save_dir() + f"/{clan}" + "/names" + "/alt_prefixes.json"):
            with open(get_save_dir() + f"/{clan}" + "/names" + "/alt_prefixes.json") as read_file:
                Name.mod_prefixes = ujson.loads(read_file.read())
        if os.path.exists(get_save_dir() + f"/{clan}" + "/names" + '/alt_suffixes.json'):
            with open(get_save_dir() + f"/{clan}" + "/names" + '/alt_suffixes.json') as read_file:
                Name.mod_suffixes = ujson.loads(read_file.read())
        if os.path.exists(get_save_dir() + f"/{clan}" + "/names" + '/names.json'):
            with open(get_save_dir() + f"/{clan}" + "/names" + '/names.json') as read_file:
                Name.names_dict = ujson.loads(read_file.read())
    def check_name(self, cat, name_fixpref):
        if not self.suffix:
            return
        # Prevent triple letter names from joining prefix and suffix from occurring (ex. Beeeye)
        possible_three_letter = (
            (self.prefix[-2:] if len(self.prefix) > 2 else self.prefix) + self.suffix[0],
            self.prefix[-1] + self.suffix[:2],
        )
        triple_letter = all(
            i == possible_three_letter[0][0] for i in possible_three_letter[0]
        ) or all(
            i == possible_three_letter[1][0]
            for i in possible_three_letter[1]
            # Prevent double animal names (ex. Spiderfalcon)
        )
        double_animal = (
            self.prefix in self.names_dict["animal_prefixes"]
            and self.suffix in self.names_dict["animal_suffixes"]
        )
        # Prevent the inappropriate names
        nono_name = self.prefix + self.suffix
        # Prevent double names (ex. Iceice)
        # Prevent suffixes containing the prefix (ex. Butterflyfly)

        i = 0
        while (
            nono_name.lower() in self.names_dict["inappropriate_names"]
            or triple_letter
            or double_animal
            or (
                self.prefix.lower() in self.suffix.lower()
                and str(self.prefix) != ""
            )
            or (
                self.suffix.lower() in self.prefix.lower()
                and str(self.suffix) != ""
            )
            or (
                self.cat and hasattr(self.cat, "pelt") and not self.cat.pelt.scars 
                and self.suffix == "scar"
            )
        ):
            # check if random die was for prefix
            if name_fixpref and not(self.cat and hasattr(self.cat, "pelt") and not self.cat.pelt.scars and self.suffix == "scar"):
                self.give_prefix(cat, self.biome)
            else:
                self.suffix = ""
                self.give_suffix(self.skills, self.personality, self.biome, self.honour)

            nono_name = self.prefix + self.suffix
            possible_three_letter = (
                (self.prefix[-2:] if len(self.prefix) > 2 else self.prefix) + self.suffix[0],
                self.prefix[-1] + self.suffix[:2],
            )
            if any(
                i != possible_three_letter[0][0] for i in possible_three_letter[0]
            ) and any(
                i != possible_three_letter[1][0] for i in possible_three_letter[1]
            ):
                triple_letter = False
            if (
                self.prefix not in self.names_dict["animal_prefixes"]
                or self.suffix not in self.names_dict["animal_suffixes"]
            ):
                double_animal = False
            i += 1

        if self.suffix:
            if get_clan_setting("ancient names") and get_clan_setting("modded names"):
                self.suffix = " " + self.suffix.title()
                self.specsuffix_hidden = True
        elif get_clan_setting("no special suffixes") and get_clan_setting("modded names"):
            self.specsuffix_hidden = True

    def __str__(self):
        return self.__repr__()
    def filter(self, all, used):
        return [x for x in all if x not in used]

    def change_prefix(self, moons, biome, change):
        self.moons = moons

        colour_changed = False

        self.phenotype.SpriteInfo(moons)

        if (self.phenotype.colour in ['white', 'albino'] or 
            (self.phenotype.maincolour == 'white' and not self.phenotype.patchmain) or
            (self.phenotype.white[1] in ['ws', 'wt'] and self.phenotype.whitegrade == 5) or
            (self.phenotype.tortiepattern == ['revCRYPTIC'] and self.phenotype.brindledbi) or 
            (self.phenotype.dilute[0] == 'd' and self.phenotype.pinkdilute[0] == 'dp' and 
                (('dove' in self.phenotype.colour and self.phenotype.saturation < 2) or 
                ('platinum' in self.phenotype.colour and self.phenotype.saturation < 3) or
                ('dove' not in self.phenotype.colour and 'platinum' not in self.phenotype.colour))) or
            ('silver' in self.phenotype.silvergold and ('shaded' in self.phenotype.tabby or 'chinchilla' in self.phenotype.tabby))
            ):
            colour_changed = False
        elif change == "kit-apprentice" and self.phenotype.pointgene[0] in ['cb', 'cs']:
            colour_changed = True
        elif change == "kit-apprentice" and (self.phenotype.fevercoat or self.phenotype.bleach[0] == 'lb'):
            colour_changed = True
        elif change == "kit-apprentice" and self.phenotype.karp[0] == 'K':
            colour_changed = True
        elif self.phenotype.ext[0] == 'ec' and change == "kit-apprentice":
            colour_changed = True
        elif self.phenotype.ext[0] == 'er' and (self.moons > 23 and change == "apprentice-warrior"):
            colour_changed = True
        elif self.phenotype.ext[0] == 'ea' and ((change == "apprentice-warrior" and self.phenotype.agouti[0] != 'a') or (self.moons > 35 and change == "apprentice-warrior")):
            colour_changed = True
        elif change in ["apprentice-warrior", "warrior-elder"] and self.phenotype.vitiligo:
            colour_changed = True
        elif self.prefix in self.mod_prefixes['general']['small'] and self.phenotype.height_label in ['goliath', 'giant', 'large', 'above average', 'average']:
            colour_changed = True
        elif self.prefix in self.mod_prefixes['general']['big'] and self.phenotype.height_label in ['teacup', 'tiny', 'small', 'below average', 'average']:
            colour_changed = True
            
        chance = constants.CONFIG["cat_name_controls"]["prefix_change_chance"][change]
        if colour_changed:
            chance /= constants.CONFIG["cat_name_controls"]["prefix_change_chance"]["pelt_change_modifier"]

        if random.random() < (1/chance):
            self.give_prefix(self.cat, biome)

        self.check_name(self.cat, True)


    # Generate possible prefix
    def give_prefix(self, cat, biome, no_suffix=False):
        if get_clan_setting("modded names") and get_clan_setting('outsider names') and random.random() < 0.5:
            selected_category = random.choices(["silly_names", "human_names", "loner_names",
                                              "normal_prefixes"], constants.CONFIG["cat_name_controls"]["clancat"], k=1)[0]
            self.prefix = random.choice(self.names_dict[selected_category])
            return
        if not self.phenotype:
            self.prefix = random.choice(self.names_dict["normal_prefixes"])
            return

        try:
            used_prefixes = [c.name.prefix for c in cat.all_cats.values() if c.status.group_ID == cat.status.group_ID]
        except:
            used_prefixes = []

        namer = Namer(used_prefixes, self.mod_prefixes, self.moons, self.phenotype, self.chimpheno)
        if get_clan_setting("modded names") and get_clan_setting('new prefixes'):
            self.prefix = namer.start()
            if no_suffix:
                if self.prefix == "Striped":
                    self.prefix = "Stripe"
                elif self.prefix == "Spotted":
                    self.prefix = "Spot"
            if self.prefix:
                return
            

        named_after_appearance = not random.getrandbits(
            2
        )  # Chance for True is '1/4'

        named_after_biome_ = not random.getrandbits(3)  # chance for True is 1/8

        colour_mappings = {
            "black" : ["BLACK"],
            "blue" : ["GREY", "DARKGREY"],
            "chocolate" : ["BROWN", "GOLDEN-BROWN", "DARKBROWN", "CHOCOLATE"],
            "lilac" : ["PALEGREY", "SILVER", "LILAC"],
            "cinnamon" : ["SIENNA", "DARKGINGER", "GOLDEN-BROWN"],
            "fawn" : ["LIGHTBROWN"],
            "ginger" : ["GINGER", "DARKGINGER"],
            "cream" : ["CREAM", "PALEGINGER"],
            "white" : ["WHITE"],
            "silver shaded" : ["WHITE"]
        }
        
        params = namer.parse_chimera() if self.chimpheno else namer.get_categories(self.phenotype)

        colours = colour_mappings[params[0]]
        if params[2]['type'] == 'silver' and params[0] not in ['ginger', 'cream']:
            colours.append('PALEGREY')
            colours.append('SILVER')
        if params[2]['type'] == 'dark' and params[0] == "black":
            colours.append('GHOST')
        if params[2]['type'] == 'golden' and params[0] not in ['ginger', 'cream']:
            colours.append('GOLDEN')
        if self.phenotype.ruftype == 'rufoused' and params[0] == 'ginger':
            colours.append('DARKGINGER')
        if self.phenotype.ruftype == 'low' and params[0] == 'ginger':
            colours.append('PALEGINGER')
        if params[2]['pattern'] != '' and params[2]['type'] == 'regular' and params[0] == "black":
            colours.append('BROWN')
            colours.append('DARKBROWN')

        # Add possible prefix categories to list.
        possible_prefix_categories = []
        possible_prefix_categories.append(self.names_dict["colour_prefixes"][random.choice(colours)])
        if biome is not None and biome in self.names_dict["biome_prefixes"]:
            possible_prefix_categories.append(self.names_dict["biome_prefixes"][biome])

        # Choose appearance-based prefix if possible and named_after_appearance because True.
        if (
            named_after_appearance
            and possible_prefix_categories
            and not named_after_biome_
            or named_after_biome_
            and possible_prefix_categories
        ):
            prefix_category = random.choice(possible_prefix_categories)
            self.prefix = random.choice(prefix_category)
        else:
            self.prefix = random.choice(self.names_dict["normal_prefixes"])

        # This thing prevents any prefix duplications from happening.
        # Try statement stops this form running when initializing.
        with contextlib.suppress(NameError):
            if self.prefix in names.prefix_history:
                # do this recurively until a name that isn't on the history list is chosses.
                self.give_prefix(cat, biome, no_suffix)
                # prevent infinite recursion
                if len(names.prefix_history) > 0:
                    names.prefix_history.pop(0)
            else:
                names.prefix_history.append(self.prefix)
            # Set the maximin length to 8 just to be sure
            if len(names.prefix_history) > 8:
                # removing at zero so the oldest gets removed
                names.prefix_history.pop(0)

    # Generate possible suffix
    def give_suffix(self, skills, personality, biome, honour=None):
        if game.clan and get_clan_setting('modded names') and get_clan_setting('no suffixes'):
            self.suffix = ""
            return
        try:
            if self.mod_suffixes and skills and personality:
                options = []
                suffix_settings = constants.CONFIG["cat_name_controls"]["alt_suffixes"]
                for i in range(suffix_settings["primary_skill"]):
                    try:
                        options.append(self.mod_suffixes['skill'][skills.primary.path.name])
                    except:
                        break

                if skills.secondary:
                    for i in range(suffix_settings["secondary_skill"]):
                        options.append(self.mod_suffixes['skill'].get(skills.secondary.path.name, []))
                
                for i in range(suffix_settings["trait"]):
                    try:
                        options.append(self.mod_suffixes['trait'][personality.trait]['general'])
                    except:
                        options.append(self.mod_suffixes['trait'].get(personality.trait, []))
                if honour:
                    for i in range(suffix_settings["trait_honour"]):
                        try:
                            options.append(self.mod_suffixes['trait'][personality.trait].get(honour, []))
                        except:
                            options.append(self.mod_suffixes['honour'].get(honour, []))
                    for i in range(suffix_settings["general_honour"]):
                        options.append(self.mod_suffixes['honour'].get(honour, []))

                for i in range(suffix_settings["special"]):
                    options.append(self.mod_suffixes['other']['special'])

                appearance = self.mod_suffixes['other']['common']

                if self.phenotype.length == 'longhaired':
                    appearance += self.mod_suffixes['other']['appearance'].get('longhair', [])
                if self.phenotype.tabby != "" and (self.phenotype.white[1] not in ['ws', 'wt'] or self.phenotype.whitegrade < 4):
                    if self.phenotype.ticked[0] == 'Ta' and (not self.phenotype.breakthrough or self.phenotype.mack[0] != 'mc'):
                        appearance += self.mod_suffixes['other']['appearance'].get('ticked', [])
                    if 'spotted' in self.phenotype.tabby or 'servaline' in self.phenotype.tabby:
                        appearance += self.mod_suffixes['other']['appearance'].get('spotted', [])
                    if ('blotched' in self.phenotype.tabby or 'marbled' in self.phenotype.tabby) and "sheeted" not in self.phenotype.tabby:
                        appearance += self.mod_suffixes['other']['appearance'].get('swirled', [])
                    if 'mackerel' in self.phenotype.tabby or 'braided' in self.phenotype.tabby or 'pinstripe' in self.phenotype.tabby:
                        appearance += self.mod_suffixes['other']['appearance'].get('striped', [])
                    if 'rosette' in self.phenotype.tabby:
                        appearance += self.mod_suffixes['other']['appearance'].get('patchy', [])
                if (self.phenotype.tortie and (self.phenotype.white[1] not in ['ws', 'wt'] or self.phenotype.whitegrade < 4)) or\
                    (self.phenotype.white[1] in ['ws', 'wt'] and self.phenotype.whitegrade < 4) or\
                    (self.phenotype.white[0] in ['ws', 'wt'] and self.phenotype.white[1] not in ['ws', 'wt'] and self.phenotype.whitegrade > 2):
                    appearance += self.mod_suffixes['other']['appearance'].get('patchy', [])
                    if (self.phenotype.tortiepattern and self.phenotype.tortiepattern[0].replace('rev', '') in self.phenotype.def_tortie_low_patterns):
                        appearance += self.mod_suffixes['other']['appearance'].get('spotted', [])
                    if ((self.phenotype.white[1] in ['ws', 'wt'] and self.phenotype.whitegrade < 4) or\
                    (self.phenotype.white[0] in ['ws', 'wt'] and self.phenotype.white[1] not in ['ws', 'wt'] and self.phenotype.whitegrade > 2)):
                        appearance += self.mod_suffixes['other']['appearance'].get('white_patchy', [])
                if (self.phenotype.point and (self.phenotype.white[1] not in ['ws', 'wt'] or self.phenotype.whitegrade < 4)):
                    appearance += self.mod_suffixes['other']['appearance'].get('pointed', [])
                if 'curl' in self.phenotype.eartype or 'curl' in self.phenotype.tailtype or 'rexed' in self.phenotype.furtype:
                    appearance += self.mod_suffixes['other']['appearance'].get('curled', [])
                
                size = suffix_settings["common"]
                if self.cat.moons < 11 or (self.cat.status.rank.is_any_medicine_rank() and self.cat.moons < 15):
                    size = suffix_settings["common_early"]
                for i in range(size):
                    options.append(appearance)
                self.suffix = ""

                tries = 0
                while not self.suffix or self.suffix in self.prefix.lower():
                    tries += 1
                    if tries > 20:
                        break
                    try:
                        self.suffix = random.choice(random.choice(options))
                    except:
                        while [] in options:
                            options.remove([])
                        continue
                self.check_name(self.cat, False)
                return
        except:
            pass

        """Generate possible suffix."""
        pelt = []
        if self.phenotype:
            if (self.phenotype.white[1] not in ['ws', 'wt'] or self.phenotype.whitegrade < 4):
                if self.phenotype.tabby != "":
                    if self.phenotype.ticked[0] == 'Ta' and (not self.phenotype.breakthrough or self.phenotype.mack[0] != 'mc'):
                        if self.phenotype.ticktype == "agouti":
                            pelt.append("Agouti")
                        else:
                            pelt.append("Ticked")
                    if 'spotted' in self.phenotype.tabby or 'servaline' in self.phenotype.tabby:
                        pelt.append("Spotted")
                    if ('blotched' in self.phenotype.tabby or 'marbled' in self.phenotype.tabby) and "sheeted" not in self.phenotype.tabby:
                        pelt.append("Classic")
                    if 'mackerel' in self.phenotype.tabby or 'braided' in self.phenotype.tabby or 'pinstripe' in self.phenotype.tabby:
                        pelt.append("Mackerel")
                    if 'rosette' in self.phenotype.tabby:
                        pelt.append("Rosetted")
                    if 'charcoal' in self.phenotype.tabtype:
                        pelt.append("Masked")
                if self.phenotype.tortie:
                    if self.phenotype.white[1] in ['ws', 'wt'] or self.phenotype.whitegrade > 4:
                        pelt.append("Calico")
                    else:
                        pelt.append("Tortie")
                if 'smoke' in self.phenotype.silvergold:
                    pelt.append("Smoke")
            if (self.phenotype.white[1] in ['ws', 'wt'] and self.phenotype.whitegrade < 4) or\
                (self.phenotype.white[0] in ['ws', 'wt'] and self.phenotype.white[1] not in ['ws', 'wt'] and self.phenotype.whitegrade > 2):
                pelt.append("TwoColour")

        tries = 0
        while not self.suffix or self.suffix in self.prefix.lower():
            tries += 1
            if tries > 20:
                break
            named_after_pelt = not random.getrandbits(2)  # Chance for True is '1/8'.
            named_after_biome = not random.getrandbits(3)  # 1/8
            # Pelt name only gets used if there's an associated suffix.
            if named_after_pelt and len(pelt) > 0:
                self.suffix = random.choice(self.names_dict["pelt_suffixes"][random.choice(pelt)])
            elif named_after_biome:
                if biome in self.names_dict["biome_suffixes"]:
                    self.suffix = random.choice(
                        self.names_dict["biome_suffixes"][biome]
                    )
                else:
                    self.suffix = random.choice(self.names_dict["normal_suffixes"])
            else:
                self.suffix = random.choice(self.names_dict["normal_suffixes"])

        self.check_name(self.cat, False)
        
    def get_specsuffix_name(self, rank: CatRank = CatRank.LEADER):
        """
        Return the cat's name with the appropriate special suffix. If no specsuffix is given for that rank, returns
        default prefix + suffix. If specsuffix_hidden is true, return default prefix + suffix.
        :param rank: CatRank matching
        :return: Cat's name string
        """
        if rank in self.names_dict["special_suffixes"] and not self.specsuffix_hidden:
            return self.prefix + self.names_dict["special_suffixes"][rank]

        return self.prefix + self.suffix

    def __repr__(self):
        # Handles predefined suffixes (such as newborns being kit),
        # then suffixes based on ages (fixes #2004, just trust me)

        # Handles suffix assignment with outside cats
        if (
            self.cat.status.is_lost()
            and not self.cat.status.is_former_clancat
            and self.suffix
        ):
            # these are cats who were born to a parent who'd been lost frm their clan, and who's parent decided to keep with traditional naming
            age_to_rank = {
                CatAge.NEWBORN: CatRank.NEWBORN,
                CatAge.KITTEN: CatRank.KITTEN,
                CatAge.ADOLESCENT: CatRank.APPRENTICE,
            }
            if self.cat.age in age_to_rank:
                rank = age_to_rank[self.cat.age]
                return self.prefix + self.names_dict["special_suffixes"][rank]
            else:
                return self.prefix + self.suffix

        if self.cat.status.is_former_clancat:
            old_rank = self.cat.status.find_prior_clan_rank()

            if (
                old_rank in self.names_dict["special_suffixes"]
                and not self.specsuffix_hidden
            ):
                return self.prefix + self.names_dict["special_suffixes"][old_rank]

        if (
            self.cat.status.rank in self.names_dict["special_suffixes"]
            and not self.specsuffix_hidden
        ):
            return (
                self.prefix + self.names_dict["special_suffixes"][self.cat.status.rank]
            )
        return self.prefix + self.suffix


names = Name()
names.prefix_history = []
