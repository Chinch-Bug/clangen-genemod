import random
from random import choice
from re import sub

from scripts.cat.sprites import sprites
from scripts.game_structure.game_essentials import game
from .genotype import Genotype
from .phenotype import Phenotype

class Pelt:
    # bite scars by @wood pank on discord

    # scars from other cats, other animals
    scars1 = ["ONE", "TWO", "THREE", "TAILSCAR", "SNOUT", "CHEEK", "SIDE", "THROAT", "TAILBASE", "BELLY",
              "LEGBITE", "NECKBITE", "FACE", "MANLEG", "BRIGHTHEART", "MANTAIL", "BRIDGE", "RIGHTBLIND", "LEFTBLIND",
              "BOTHBLIND", "BEAKCHEEK", "BEAKLOWER", "CATBITE", "RATBITE", "QUILLCHUNK", "QUILLSCRATCH", "HINDLEG",
              "BACK", "QUILLSIDE", "SCRATCHSIDE", "BEAKSIDE", "CATBITETWO", "FOUR"]

    # missing parts
    scars2 = ["LEFTEAR", "RIGHTEAR", "NOTAIL", "HALFTAIL", "NOPAW", "NOLEFTEAR", "NORIGHTEAR", "NOEAR", "TNR"]

    # "special" scars that could only happen in a special event
    scars3 = ["SNAKE", "TOETRAP", "BURNPAWS", "BURNTAIL", "BURNBELLY", "BURNRUMP", "FROSTFACE", "FROSTTAIL",
              "FROSTMITT", "FROSTSOCK", "TOE", "SNAKETWO"]

    # make sure to add plural and singular forms of new accs to acc_display.json so that they will display nicely
    plant_accessories = ["MAPLE LEAF", "HOLLY", "BLUE BERRIES", "FORGET ME NOTS", "RYE STALK", "CATTAIL", "POPPY", "ORANGE POPPY", "CYAN POPPY", "WHITE POPPY", "PINK POPPY",
                        "BLUEBELLS", "LILY OF THE VALLEY", "SNAPDRAGON", "HERBS", "PETALS", "NETTLE", "HEATHER", "GORSE", "JUNIPER", "RASPBERRY", "LAVENDER",
                        "OAK LEAVES", "CATMINT", "MAPLE SEED", "LAUREL", "BULB WHITE", "BULB YELLOW", "BULB ORANGE", "BULB PINK", "BULB BLUE", "CLOVER", "DAISY",
                        "CLOVER", "DAISY", "LILY OF THE VALLEY", "HEATHER", "SNAPDRAGON", "GORSE", "BULB WHITE", "BULB YELLOW",
                        "DRY HERBS", "DRY CATMINT", "DRY NETTLES", "DRY LAURELS"
                        ]
    wild_accessories = ["RED FEATHERS", "BLUE FEATHERS", "JAY FEATHERS", "GULL FEATHERS", "SPARROW FEATHERS", "MOTH WINGS", "ROSY MOTH WINGS", "MORPHO BUTTERFLY", "MONARCH BUTTERFLY", "CICADA WINGS", "BLACK CICADA"]
  
    tail_accessories = ["RED FEATHERS", "BLUE FEATHERS", "JAY FEATHERS", "GULL FEATHERS", "SPARROW FEATHERS", "CLOVER", "DAISY"]
    collars = [
        "CRIMSON", "BLUE", "YELLOW", "CYAN", "RED", "LIME", "GREEN", "RAINBOW",
        "BLACK", "SPIKES", "WHITE", "PINK", "PURPLE", "MULTI", "INDIGO", "CRIMSONBELL", "BLUEBELL",
        "YELLOWBELL", "CYANBELL", "REDBELL", "LIMEBELL", "GREENBELL",
        "RAINBOWBELL", "BLACKBELL", "SPIKESBELL", "WHITEBELL", "PINKBELL", "PURPLEBELL",
        "MULTIBELL", "INDIGOBELL", "CRIMSONBOW", "BLUEBOW", "YELLOWBOW", "CYANBOW", "REDBOW",
        "LIMEBOW", "GREENBOW", "RAINBOWBOW", "BLACKBOW", "SPIKESBOW", "WHITEBOW", "PINKBOW",
        "PURPLEBOW", "MULTIBOW", "INDIGOBOW", "CRIMSONNYLON", "BLUENYLON", "YELLOWNYLON", "CYANNYLON",
        "REDNYLON", "LIMENYLON", "GREENNYLON", "RAINBOWNYLON",
        "BLACKNYLON", "SPIKESNYLON", "WHITENYLON", "PINKNYLON", "PURPLENYLON", "MULTINYLON", "INDIGONYLON",
    ]

    """Holds all appearance information for a cat. """

    def __init__(
        self,
        genotype:Genotype,
        phenotype:Phenotype,
        accessory:str=None,
        paralyzed:bool=False,
        opacity:int=100,
        scars:list=None,
        tint:str="none",
        white_patches_tint:str="none",
        kitten_sprite:int=None,
        adol_sprite:int=None,
        adult_sprite:int=None,
        senior_sprite:int=None,
        para_adult_sprite:int=None,
        reverse:bool=False,
        ) -> None:
        self.genotype = genotype
        self.phenotype = phenotype
        self.cat_sprites =  {
            "kitten": kitten_sprite if kitten_sprite is not None else 0,
            "adolescent": adol_sprite if adol_sprite is not None else 0,
            "young adult": adult_sprite if adult_sprite is not None else 0,
            "adult": adult_sprite if adult_sprite is not None else 0,
            "senior adult": adult_sprite if adult_sprite is not None else 0,
            "senior": senior_sprite if senior_sprite is not None else 0,
            "para_adult": para_adult_sprite if para_adult_sprite is not None else 0,
        }        
        self.cat_sprites['newborn'] = 20
        self.cat_sprites['para_young'] = 17
        self.cat_sprites["sick_adult"] = 18
        self.cat_sprites["sick_young"] = 19
        if phenotype.length == "longhaired" and genotype.longtype == 'long' and genotype.cornish[0] == "R" and genotype.lykoi[0] == 'Ly' and genotype.sedesp[0] != "re" and 'brush' not in phenotype.furtype:    
            self.length="long"
            if self.cat_sprites['adult'] < 9:
                self.cat_sprites['adult'] += 3
                self.cat_sprites['young adult'] += 3
                self.cat_sprites['senior adult'] += 3
        elif phenotype.length != 'hairless':
            if phenotype.length == "mediumhaired":
                self.length = 'medium'
            else:
                self.length="short"
            if self.cat_sprites['adult'] > 8:
                self.cat_sprites['adult'] -= 3
                self.cat_sprites['young adult'] -= 3
                self.cat_sprites['senior adult'] -= 3
        else:
            self.length="hairless"
            if self.cat_sprites['adult'] > 8:
                self.cat_sprites['adult'] -= 3
                self.cat_sprites['young adult'] -= 3
                self.cat_sprites['senior adult'] -= 3
        self.accessory = accessory
        self.paralyzed = paralyzed
        self.opacity = opacity
        self.scars = scars if isinstance(scars, list) else []
        self.tint = tint
        self.white_patches_tint = white_patches_tint
        
        self.reverse = reverse

    @staticmethod
    def generate_new_pelt(genotype, phenotype, gender:str, parents:tuple=(), age:str="adult"):
        new_pelt = Pelt(genotype, phenotype)
        
        new_pelt.init_sprite()
        new_pelt.init_scars(age)
        new_pelt.init_accessories(age)
        new_pelt.init_tint()

        return new_pelt

    def init_sprite(self):
        self.cat_sprites = {
            'newborn': 20,
            'kitten': random.randint(0, 2),
            'adolescent': random.randint(3, 5),
            'senior': random.randint(12, 14),
            'sick_young': 19,
            'sick_adult': 18
        }
        self.reverse = choice([True, False])

        if self.length != 'long':
            self.cat_sprites['adult'] = random.randint(6, 8)
            self.cat_sprites['para_adult'] = 16
        else:
            self.cat_sprites['adult'] = random.randint(9, 11)
            self.cat_sprites['para_adult'] = 15
        self.cat_sprites['young adult'] = self.cat_sprites['adult']
        self.cat_sprites['senior adult'] = self.cat_sprites['adult']

    def init_scars(self, age):
        if age == "newborn":
            return

        if age in ['kitten', 'adolescent']:
            scar_choice = random.randint(0, 50)  # 2%
        elif age in ['young adult', 'adult']:
            scar_choice = random.randint(0, 20)  # 5%
        else:
            scar_choice = random.randint(0, 15)  # 6.67%

        if scar_choice == 1:
            self.scars.append(choice([
                choice(Pelt.scars1),
                choice(Pelt.scars3)
            ]))

        if 'NOTAIL' in self.scars and 'HALFTAIL' in self.scars:
            self.scars.remove('HALFTAIL')

    def init_accessories(self, age):
        if age == "newborn":
            self.accessory = None
            return

        acc_display_choice = random.randint(0, 80)
        if age in ['kitten', 'adolescent']:
            acc_display_choice = random.randint(0, 180)
        elif age in ['young adult', 'adult']:
            acc_display_choice = random.randint(0, 100)

        if acc_display_choice == 1:
            self.accessory = choice([
                choice(Pelt.plant_accessories),
                choice(Pelt.wild_accessories)
            ])
        else:
            self.accessory = None

        if self.phenotype.bobtailnr > 0 and self.phenotype.bobtailnr < 5 and self.accessory in ['RED FEATHERS', 'BLUE FEATHERS', 'JAY FEATHERS']:
            self.accessory = None
        

    def init_tint(self):
        """Sets tint for pelt and white patches"""

        # PELT TINT
        # Basic tints as possible for all colors.
        base_tints = sprites.cat_tints["possible_tints"]["basic"]
        
        colour = ""
        if self.phenotype.genotype.white[0] == "W":
            colour = "WHITE"
        elif 'point' in self.phenotype.point or 'silver' in self.phenotype.silvergold or (self.phenotype.genotype.dilute[0] == 'd' and self.phenotype.genotype.pinkdilute[0] == "dp"):
            colour = "PALE"
        elif 'gold' in self.phenotype.silvergold or 'sunshine' in self.phenotype.silvergold:
            colour = "GOLDEN"
        else:
            if (self.phenotype.genotype.dilute[0] == 'd' or self.phenotype.genotype.pinkdilute[0] == "dp"):
                if self.phenotype.colour in ['cream', 'cream apricot', 'honey']:
                    colour = "CREAM"
                elif self.phenotype.colour in ['fawn', 'fawn caramel', 'buff']:
                    colour = "FAWN"
                elif self.phenotype.colour in ['lilac', 'lilac caramel', 'champagne']:
                    colour = "LILAC"
                else:
                    colour = "BLUE"
            else:
                if self.phenotype.colour in ['flame', 'red']:
                    colour = "RED"
                elif self.phenotype.colour == "cinnamon":
                    colour = "CINNAMON"
                elif self.phenotype.colour == "chocolate":
                    colour = "CHOCOLATE"
                else:
                    colour = "BLACK"
        color_group = sprites.cat_tints["colour_groups"].get(colour, "warm")
        color_tints = sprites.cat_tints["possible_tints"][color_group]

        if base_tints or color_tints:
            self.tint = choice(base_tints + color_tints)
        else:
            self.tint = "none"

        # WHITE PATCHES TINT
        # Now for white patches
        base_tints = sprites.white_patches_tints["possible_tints"]["basic"]
        if colour in sprites.cat_tints["colour_groups"]:
            color_group = sprites.white_patches_tints["colour_groups"].get(colour, "white")
            color_tints = sprites.white_patches_tints["possible_tints"][color_group]
        else:
            color_tints = []

        if base_tints or color_tints:
            self.white_patches_tint = choice(base_tints + color_tints)
        else:
            self.white_patches_tint = "none"

    @staticmethod
    def describe_appearance(cat, short=False):
        
        color_name = cat.phenotype.PhenotypeOutput(pattern=cat.genotype.white_pattern, gender=cat.genderalign)
        
        if not short:

            scar_details = {
                "NOTAIL": "no tail",
                "HALFTAIL": "half a tail",
                "NOPAW": "three legs",
                "NOLEFTEAR": "a missing ear",
                "NORIGHTEAR": "a missing ear",
                "NOEAR": "no ears"
            }

            additional_details = []
            for scar in cat.pelt.scars:
                if scar in scar_details and scar_details[scar] not in additional_details:
                    additional_details.append(scar_details[scar])

            if len(additional_details) > 2:
                color_name = f"{color_name} with {', '.join(additional_details[:-1])}, and {additional_details[-1]}"
            elif len(additional_details) == 2:
                color_name = f"{color_name} with {' and '.join(additional_details)}"
            elif additional_details:
                color_name = f"{color_name} with {additional_details[0]}"
        
            if len(cat.pelt.scars) >= 3:
                color_name = f"scarred {color_name}"

        return color_name