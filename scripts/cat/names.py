"""
Module that handles the name generation for all cats.
"""
import contextlib
import os
import random

import ujson

from scripts.game_structure.game_essentials import game
from scripts.housekeeping.datadir import get_save_dir
from .alt_namer import Namer


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
            self.give_prefix(cat, biome, no_suffix=True if suffix == "" else False)
            # needed for random dice when we're changing the Prefix
            name_fixpref = True

        # Set suffix
        if self.suffix is None:
            self.give_suffix(self.skills, self.personality, biome, honour)
            if name_fixpref and self.prefix is None:
                # needed for random dice when we're changing the Prefix
                name_fixpref = False

        if self.suffix and not load_existing_name:
            self.check_name(cat, name_fixpref)
    
    def check_name(self, cat, name_fixpref):
        if not self.suffix:
            return
        # Prevent triple letter names from joining prefix and suffix from occurring (ex. Beeeye)
        possible_three_letter = (
            self.prefix[-2:] + self.suffix[0],
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
                self.suffix = None
                self.give_suffix(self.skills, self.personality, self.biome, self.honour)

            nono_name = self.prefix + self.suffix
            possible_three_letter = (
                self.prefix[-2:] + self.suffix[0],
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

    def __str__(self):
        return self.__repr__()
    def filter(self, all, used):
        return [x for x in all if x not in used]

    def change_prefix(self, cat, moons, biome, change):
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
        elif self.phenotype.ext[0] == 'ea' and ((change == "apprentice-warrior" and self.phenotype.agouti[0] != 'a') or (self.moons > 23 and change == "apprentice-warrior")):
            colour_changed = True
        elif change == "apprentice-warrior" and self.phenotype.vitiligo:
            colour_changed = True
        elif self.prefix in self.mod_prefixes['general']['small'] and self.phenotype.height_label in ['goliath', 'giant', 'large', 'above average', 'average']:
            colour_changed = True
        elif self.prefix in self.mod_prefixes['general']['big'] and self.phenotype.height_label in ['teacup', 'tiny', 'small', 'below average', 'average']:
            colour_changed = True
            
        chance = game.config["cat_name_controls"]["prefix_change_chance"][change]
        if colour_changed:
            chance /= game.config["cat_name_controls"]["prefix_change_chance"]["pelt-change-modifier"]

        if random.random() < (1/chance):
            self.give_prefix(cat, biome)

        self.check_name(cat, True)


    # Generate possible prefix
    def give_prefix(self, cat, biome, no_suffix=False):
        if not self.phenotype:
            self.prefix = random.choice(self.names_dict["normal_prefixes"])
            return

        try:
            used_prefixes = [c.name.prefix for c in cat.all_cats.values() if not c.dead and c.group == cat.group and c.group]
        except:
            used_prefixes = []

        namer = Namer(used_prefixes, self.mod_prefixes, self.moons, self.phenotype, self.chimpheno)
        if not game.clan or (game.clan.clan_settings["modded names"] and game.clan.clan_settings['new prefixes']):
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
        try:
            if self.mod_suffixes and (not game.clan or (game.clan.clan_settings["modded names"] and game.clan.clan_settings['new suffixes'])) and skills and personality:
                options = []
                for i in range(4):
                    try:
                        options.append(self.mod_suffixes['skill'][skills.primary.path.name])
                    except:
                        break

                if skills.secondary:
                    for i in range(2):
                        options.append(self.mod_suffixes['skill'].get(skills.secondary.path.name, []))
                
                
                for i in range(2):
                    try:
                        options.append(self.mod_suffixes['trait'][personality.trait]['general'])
                    except:
                        options.append(self.mod_suffixes['trait'].get(personality.trait, []))
                    if honour:
                        try:
                            options.append(self.mod_suffixes['trait'][personality.trait].get(honour, []))
                        except:
                            pass
                        options.append(self.mod_suffixes['honour'].get(honour, []))

                for i in range(1):
                    options.append(self.mod_suffixes['other']['special'])
                for i in range(3):
                    options.append(self.mod_suffixes['other']['common'])

                appearance = []

                if self.phenotype.length == 'longhaired':
                    appearance += self.mod_suffixes['other']['appearance'].get('longhair', [])
                if self.phenotype.tabby != "" and (self.phenotype.white[1] not in ['ws', 'wt'] or self.phenotype.whitegrade < 4):
                    if self.phenotype.ticked[0] == 'Ta' and (not self.phenotype.breakthrough or self.phenotype.mack[0] != 'mc'):
                        appearance += self.mod_suffixes['other']['appearance'].get('ticked', [])
                    if 'spotted' in self.phenotype.tabby or 'servaline' in self.phenotype.tabby:
                        appearance += self.mod_suffixes['other']['appearance'].get('spotted', [])
                    if 'classic' in self.phenotype.tabby or 'marbled' in self.phenotype.tabby:
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
                options.append(appearance)
                self.suffix = None

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
                    if 'classic' in self.phenotype.tabby or 'marbled' in self.phenotype.tabby:
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

    def __repr__(self):
        # Handles predefined suffixes (such as newborns being kit),
        # then suffixes based on ages (fixes #2004, just trust me)

        # Handles suffix assignment with outside cats
        if self.cat.status not in ("rogue", "loner", "kittypet") and self.cat.outside:
            adjusted_status: str = ""
            if self.cat.moons >= 15:
                adjusted_status = "warrior"
            elif self.cat.moons >= 6:
                adjusted_status = "apprentice"
            if self.cat.moons == 0:
                adjusted_status = "newborn"
            elif self.cat.moons < 6:
                adjusted_status = "kitten"
            elif self.cat.moons < 12:
                adjusted_status = "apprentice"
            else:
                adjusted_status = "warrior"

            if adjusted_status != "warrior" and not self.specsuffix_hidden:
                return (
                    self.prefix + self.names_dict["special_suffixes"][adjusted_status]
                )
        if (
            self.cat.status in self.names_dict["special_suffixes"]
            and not self.specsuffix_hidden
        ):
            return self.prefix + self.names_dict["special_suffixes"][self.cat.status]
        return self.prefix + self.suffix


names = Name()
names.prefix_history = []
