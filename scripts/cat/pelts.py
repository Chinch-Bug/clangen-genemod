import random
from random import choice, random, randint, shuffle
from re import sub

import i18n

from scripts.config import get_config
import scripts.game_structure.screen_settings
from scripts.cat.enums import CatAge
from scripts.cat.sprites.load_sprites import sprites
from scripts.game_structure import constants
from .phenotype import Phenotype
from scripts.game_structure import game
from scripts.game_structure.localization import get_lang_config
from scripts.events_module.text_adjust import adjust_list_text


class Pelt:
    # POSES
    all_poses = sprites.POSE_DATA["poses"]
    newborn_poses = [x for x in all_poses if "newborn" in x]
    kitten_poses = [x for x in all_poses if "kitten" in x and "sick" not in x]
    adolescent_long_poses = [
        x for x in all_poses if "adolescent_long" in x and "sick" not in x
    ]
    adolescent_short_poses = [
        x
        for x in all_poses
        if "adolescent" in x and "long" not in x and "sick" not in x
    ]
    adult_short_poses = [
        x
        for x in all_poses
        if "adult_short" in x and "para" not in x and "sick" not in x
    ]
    adult_long_poses = [
        x
        for x in all_poses
        if "adult_long" in x and "para" not in x and "sick" not in x
    ]
    senior_poses = [x for x in all_poses if "senior" in x and "sick" not in x]

    # PELT LENGTH
    pelt_length = ["short", "medium", "long"]

    # SCARS
    # bite scars by @wood pank on discord
    general_scars = []
    for sprite_list in sprites.SCAR_DATA["sprite_list"]:
        general_scars.extend(sprite_list)

    missing_part_scars = []
    for sprite_list in sprites.SCAR_MISSING_PART_DATA["sprite_list"]:
        missing_part_scars.extend(sprite_list)

    all_scars = general_scars + missing_part_scars

    # ACCESSORIES
    # make sure to add plural and singular forms of new accs to accessories.en.json so that they will display nicely

    # all acc sprites are labeled as occupying a specific part of the cat sprite and then appended into these three lists
    # collar_accessories are presumed to all occupy the neck area and are treated as the fourth of these lists
    tail_accessories = []
    body_accessories = []
    head_accessories = []
    paw_accessories = []

    # here we create the master lists of each accessory type
    plant_accessories = []
    for sprite_list in sprites.PLANT_DATA["sprite_list"]:
        plant_accessories.extend(sprite_list)
        for sprite in sprite_list:
            if sprite_list[sprite] == "tail":
                tail_accessories.append(sprite)
            elif sprite_list[sprite] == "body":
                body_accessories.append(sprite)
            elif sprite_list[sprite] == "head":
                body_accessories.append(sprite)
            elif sprite_list[sprite] == "paw":
                paw_accessories.append(sprite)

    wild_accessories = []
    for sprite_list in sprites.WILD_DATA["sprite_list"]:
        wild_accessories.extend(sprite_list)
        for sprite in sprite_list:
            if sprite_list[sprite] == "tail":
                tail_accessories.append(sprite)
            elif sprite_list[sprite] == "body":
                body_accessories.append(sprite)
            elif sprite_list[sprite] == "head":
                body_accessories.append(sprite)
            elif sprite_list[sprite] == "paw":
                paw_accessories.append(sprite)

    collar_accessories = []
    collar_styles = []
    if sprites.COLLAR_DATA["palette_map"]:
        for style_type in sprites.COLLAR_DATA["style_data"]:
            for style, color_list in style_type.items():
                collar_styles.append(style)
                for colour in color_list:
                    collar_accessories.append(f"{style}_{colour}")
    else:
        for sprite_list in sprites.COLLAR_DATA["sprite_list"]:
            collar_accessories.extend(sprite_list)

    # this is used for acc-giving events, only change if you're adding a new category tag to the event filter
    # adding a category here will automatically update the event editor's options
    acc_categories = {
        "PLANT": plant_accessories,
        "WILD": wild_accessories,
        "COLLAR": collar_accessories,
    }

    maingame_white = {
        'low': {
            '1': [None, 'SCOURGE', 'BLAZE', "BLAZE_MID", "BLAZE_SMALL", "BLAZE_MIN", 'TAILTIP', 'TOES', 'LUNA', 'LOCKET', "CHEST_MIN",
            "LEG_BACK_LEFT_SMALL", "LEG_BACK_LEFT_MIN", "LEG_FRONT_LEFT_SMALL", "LEG_FRONT_LEFT_MIN",
            "LEG_BACK_RIGHT_SMALL", "LEG_BACK_RIGHT_MIN", "LEG_FRONT_RIGHT_SMALL", "LEG_FRONT_RIGHT_MIN"],
            '2': ['LITTLE', 'LIGHTTUXEDO', 'BUZZARDFANG', 'TIP', 'PAWS', 'BROKENBLAZE', 'BEARD', 'BIB', 'VEE', 'HONEY', 'TOESTAIL',
                  'RAVENPAW', 'DAPPLEPAW', 'LILTWO', 'MUSTACHE', 'REVERSEHEART', 'SPARKLE', 'REVERSEEYE', "CHEST_MID", "CHEST_SMALL"],
            '3': ['TUXEDO', 'SAVANNAH', 'FANCY', 'DIVA', 'BEARD', "DAMIEN_REDUCED", 'DAMIEN', 'BELLY', 'SQUEAKS', 'STAR', 'MISS', 'BOWTIE',
                  'FCTWO', 'FCONE', 'MIA', 'PRINCESS', 'DOUGIE', 'STREAMSTRIKE'],
            '4': ['TUXEDO', 'SAVANNAH', 'OWL', 'RINGTAIL', 'UNDERS', 'FAROFA', 'VEST', 'FRONT', 'BLOSSOMSTEP', 'DIGIT',
                  'HAWKBLAZE', "BERRYHEART"],
            '5': ['ANY', 'SHIBAINU', 'FAROFA', 'MISTER', 'PANTS', 'TRIXIE']
        },
        'high': {
            '1': ['ANY', 'SHIBAINU', 'PANTSTWO', 'MAO', 'TRIXIE'],
            '2': ['ANY', 'FRECKLES', 'PANTSTWO', 'MASKMANTLE', 'MAO', 'PAINTED', 'BUB', 'SCAR'],
            '3': ['ANYTWO', 'PEBBLESHINE', 'BROKEN', 'PIEBALD', 'FRECKLES', 'HALFFACE', 'GOATEE', 'PRINCE', 'CAPSADDLE',
                  'REVERSEPANTS', 'GLASS', 'PAINTED', 'COWTWO', 'SAMMY', 'FINN', 'BUSTER', 'CAKE', "FALLEN_LEAVES"],
            '4': ['VAN', 'PEBBLESHINE', 'LIGHTSONG', 'CURVED', 'GOATEE', 'TAIL', 'APRON', 'HALFWHITE', 'APPALOOSA', 'HEART',
                  'MOORISH', 'COW', 'SHOOTINGSTAR', 'PEBBLE', 'TAILTWO', 'BUDDY', 'KROPKA'],
            '5': ['ONEEAR', 'LIGHTSONG', 'PETAL', 'CHESTSPECK', 'HEARTTWO', 'BOOTS', 'SHOOTINGSTAR', 'EYESPOT',
                  'KROPKA']
        }
    }

    """Holds all appearance information for a cat. """

    def __init__(
        self,
        phenotype:Phenotype,
        rusting:str = None,
        accessory:list=None,
        paralyzed:bool=False,
        opacity:int=100,
        scars:list=None,
        tint:str="none",
        white_patches_tint: str = "none",
        newborn_sprite: str = None,
        kitten_sprite: str = None,
        adol_sprite: str = None,
        adult_sprite: str = None,
        senior_sprite: str = None,
        para_adult_sprite: str = None,
        reverse:bool=False,
        ) -> None:
        self.phenotype = phenotype
        if phenotype.length == "longhaired" and phenotype.longtype == 'long' and phenotype.cornish[0] == "R" and phenotype.lykoi[0] == 'Ly' and phenotype.sedesp[0] != "re" and 'brush' not in phenotype.furtype:    
            self.length = "long"
        elif phenotype.length != 'hairless':
            if phenotype.length == "mediumhaired" or phenotype.length == "longhaired":
                self.length = 'medium'
            else:
                self.length = "short"
        else:
            self.length = "hairless"
        self.rebuild_sprite = True
        self._accessory = accessory
        self._paralyzed = paralyzed
        self.opacity = opacity
        self._scars = (
            tuple(scars)
            if isinstance(scars, list)
            else scars
            if isinstance(scars, tuple)
            else tuple()
        )
        self.tint = tint
        self.white_patches_tint = white_patches_tint
        self.rusting = rusting
        self.screen_scale = scripts.game_structure.screen_settings.screen_scale

        # converting old pose numbers into names
        if any(
            isinstance(x, int) or x is None
            for x in [
                newborn_sprite,
                kitten_sprite,
                adol_sprite,
                adult_sprite,
                senior_sprite,
                para_adult_sprite,
            ]
        ):
            # DO NOT CHANGE THIS: this is meant to convert old saves and should not be updated with new pose additions
            self.cat_sprites = {
                "kitten": kitten_sprite if kitten_sprite is not None else 0,
                "adolescent": adol_sprite if adol_sprite is not None else 3,
                "young adult": adult_sprite if adult_sprite is not None else 6,
                "adult": adult_sprite if adult_sprite is not None else 6,
                "senior adult": adult_sprite if adult_sprite is not None else 6,
                "senior": senior_sprite if senior_sprite is not None else 12,
                "para_young": "para_young0",
                "para_adult": para_adult_sprite,
                "newborn": "newborn2",
            }
            for age, pose in self.cat_sprites.items():
                # we only need to convert if it's using the old sprite pose numbers
                if not isinstance(pose, int):
                    continue

                # convert paras
                if age == "para_adult":
                    if self.length == "long":
                        self.cat_sprites[age] = "para_adult_long0"
                    else:
                        self.cat_sprites[age] = "para_adult_short0"
                    continue

                elif age == CatAge.NEWBORN:
                    self.cat_sprites[age] = (
                        "newborn2" if "newborn2" in self.newborn_poses else "newborn0"
                    )
                    continue
                elif age == CatAge.KITTEN:
                    # since these were at the top of the sheet, the pose nums were 0, 1, 2. thus they'll naturally match this fstring
                    self.cat_sprites[age] = f"kitten{pose if pose in (0, 1, 2) else 0}"
                    continue
                elif age == CatAge.ADOLESCENT:
                    if self.length == "long":
                        fur = "long"
                    else:
                        fur = "short"
                    if pose == 3:
                        self.cat_sprites[age] = f"adolescent_{fur}0"
                    elif pose == 4:
                        self.cat_sprites[age] = f"adolescent_{fur}1"
                    elif pose == 5:
                        self.cat_sprites[age] = f"adolescent_{fur}2"
                    else:
                        self.cat_sprites[age] = choice(
                            (
                                f"adolescent_{fur}0",
                                f"adolescent_{fur}1",
                                f"adolescent_{fur}2",
                            )
                        )
                elif age in (CatAge.YOUNG_ADULT, CatAge.ADULT, CatAge.SENIOR_ADULT):
                    if pose in (0, 9):
                        self.cat_sprites[age] = "adult_long0"
                    elif pose in (1, 10):
                        self.cat_sprites[age] = "adult_long1"
                    elif pose in (2, 11):
                        self.cat_sprites[age] = "adult_long2"
                    elif pose == 6:
                        self.cat_sprites[age] = "adult_short0"
                    elif pose == 7:
                        self.cat_sprites[age] = "adult_short1"
                    elif pose == 8:
                        self.cat_sprites[age] = "adult_short2"
                    else:
                        if self.length == "long":
                            self.cat_sprites[age] = choice(
                                ("adult_long0", "adult_long1", "adult_long2")
                            )
                        else:
                            self.cat_sprites[age] = choice(
                                ("adult_short0", "adult_short1", "adult_short2")
                            )

                elif age == CatAge.SENIOR:
                    if pose in (3, 12):
                        self.cat_sprites[age] = "senior0"
                    elif pose in (4, 13):
                        self.cat_sprites[age] = "senior1"
                    elif pose in (5, 14):
                        self.cat_sprites[age] = "senior2"
                    else:
                        self.cat_sprites[age] = choice(
                            ("senior0", "senior1", "senior2")
                        )

        # now for the updating handling of pose name strings
        else:
            adult_sprite = (
                adult_sprite
                if adult_sprite is not None
                and (
                    adult_sprite in self.adult_short_poses
                    or adult_sprite in self.adult_long_poses
                )
                else "adult_short0"
            )

            if adol_sprite in ("adolescent0", "adolescent1", "adolescent2"):
                if self.length == "long":
                    adol_sprite = choice(self.adolescent_long_poses)
                else:
                    adol_sprite = f"adolescent_short{adol_sprite[-1]}"

            self.cat_sprites = {
                "newborn": newborn_sprite
                if newborn_sprite is not None and newborn_sprite in self.newborn_poses
                else "newborn0",
                "kitten": kitten_sprite
                if kitten_sprite is not None and kitten_sprite in self.kitten_poses
                else "kitten0",
                "adolescent": adol_sprite
                if adol_sprite is not None
                and (
                    adol_sprite in self.adolescent_short_poses
                    or adol_sprite in self.adolescent_long_poses
                )
                else "adolescent_short0",
                "young adult": adult_sprite,
                "adult": adult_sprite,
                "senior adult": adult_sprite,
                "senior": senior_sprite
                if senior_sprite is not None and senior_sprite in self.senior_poses
                else "senior0",
                "para_adult": para_adult_sprite
                if para_adult_sprite is not None
                else "para_adult_short0",
                "para_young": "para_young0",
            }

        self.reverse = reverse

        if self.length != "long" and self.cat_sprites["adult"] not in self.adult_short_poses:
            self.cat_sprites["adult"] = choice(self.adult_short_poses)
            self.cat_sprites["young adult"] = self.cat_sprites["adult"]
            self.cat_sprites["senior adult"] = self.cat_sprites["adult"]
            self.cat_sprites["para_adult"] = "para_adult_short0"
        if self.length != "long" and self.cat_sprites["adolescent"] not in self.adolescent_short_poses:
            self.cat_sprites["adolescent"] = choice(self.adolescent_short_poses)
        
        if self.length == "long" and self.adult_long_poses and self.cat_sprites["adult"] not in self.adult_long_poses:
            self.cat_sprites["adult"] = choice(
                self.adult_long_poses
                if self.adult_long_poses
                else self.adult_short_poses
            )
            self.cat_sprites["young adult"] = self.cat_sprites["adult"]
            self.cat_sprites["senior adult"] = self.cat_sprites["adult"]
            self.cat_sprites["para_adult"] = "para_adult_long0"
        if self.length == "long" and self.adolescent_long_poses and self.cat_sprites["adolescent"] not in self.adolescent_long_poses:
            self.cat_sprites["adolescent"] = choice(
                self.adolescent_long_poses
                if self.adolescent_long_poses
                else self.adolescent_short_poses
            )

    @property
    def accessory(self):
        return self._accessory

    @accessory.setter
    def accessory(self, val):
        self.rebuild_sprite = True
        self._accessory = val

    @property
    def scars(self):
        return self._scars

    @scars.setter
    def scars(self, val):
        self.rebuild_sprite = True
        self._scars = val

    @property
    def paralyzed(self):
        return self._paralyzed

    @paralyzed.setter
    def paralyzed(self, val):
        self.rebuild_sprite = True
        self._paralyzed = val

    @staticmethod
    def generate_new_pelt(phenotype, age:str="adult"):
        new_pelt = Pelt(phenotype)

        if random() < get_config("genetics_config.rusting") and sprites.rusting_sprites:
            new_pelt.rusting = {choice(sprites.rusting_sprites): randint(1, 5)*5}
        
        new_pelt.init_sprite()
        new_pelt.init_scars(age)
        new_pelt.init_accessories(age)
        new_pelt.init_tint()

        return new_pelt    
    
    @staticmethod
    def generate_white(KIT, albino, KITgrade, vit, white_pattern, pax3):

        if white_pattern and "break/inverse thai" in white_pattern:
            white_pattern.remove("break/inverse thai")
            white_pattern.append("break/dorsal stripe")
        if white_pattern and "full white" in white_pattern:
            white_pattern.remove("full white")
            white_pattern.append("FULLWHITE")
        if white_pattern and "break/left ear" in white_pattern:
            white_pattern.remove("break/left ear")
            white_pattern.append("break/LEFTEAR")
        if white_pattern and "break/right ear" in white_pattern:
            white_pattern.remove("break/right ear")
            white_pattern.append("break/RIGHTEAR")

        vitiligo = ['MOON', 'PHANTOM', 'POWDER', 'BLEACHED', 'VITILIGO', 'VITILIGOTWO', 'SMOKEY']

        #white patterns
        def clean_white(white_pattern):
            white_pattern = list(set(white_pattern))
            while None in white_pattern:
                white_pattern.remove(None)
            return white_pattern
        has_vitiligo = []
        if (white_pattern is not None and white_pattern != "No"):
            has_vitiligo = [p for p in white_pattern if p in vitiligo]
        if (white_pattern is None and KIT[0] not in ['w', 'wsal']) or ((white_pattern is None or (white_pattern == "No" or (len(white_pattern) == len(has_vitiligo) and len(has_vitiligo) > 0))) and (KIT[0] == 'wg' or 'NoDBE' not in pax3 or KIT[1] in ["ws", "wt"])):
            white_pattern = []
            if 'wt' in KIT:
                if KIT[1] not in ['ws', 'wt'] and KITgrade < 3:
                    white_pattern.append("dorsal1")
                elif KIT[1] not in ['ws', 'wt'] and KITgrade < 5:
                    white_pattern.append(choice(["dorsal1", "dorsal2"]))
                else:
                    white_pattern.append("dorsal2")
                white_pattern.append("thai tail")
            
            if KIT[0] == "wg":
                for mark in ["left front mitten", "left back mitten", "right front mitten", "right back mitten"]:
                    white_pattern.append(mark)
            elif (KIT[0] in ["ws", "wt"] or pax3[0] != 'NoDBE') and KIT[1] not in ["ws", "wt"] and 'NoDBE' in pax3:
                if not KIT[0] in ["ws", "wt"]:
                    if 'DBEre' in pax3[0]:
                        KITgrade = min(KITgrade, 3)
                    else:
                        KITgrade = randint(1, 2)

                if(randint(1, 4) == 1):
                    white_pattern.append(choice(Pelt.maingame_white["low"].get(str(KITgrade))))

                elif KITgrade == 1:
                    if random () < 0.95:
                        white_pattern.append(choice(['chest tuft', 'belly tuft', 'belly tuft', 'belly tuft', "CHEST_MIN", "LOCKET"]))
                    
                elif KITgrade == 2:
                    while len(white_pattern) == 0:
                        #chest
                        if random () < 0.5:
                            white_pattern.append(choice(['chest tuft', 'locket', 'chest tuft', 'locket', 'bib', "BIB_SMALL", "CHEST_MIN", "CHEST_SMALL", "LOCKET"]))
                        #belly
                        elif random () < 0.5:
                            white_pattern.append(choice(['belly tuft', 'belly spot', 'belly tuft', 'belly spot', 'belly', "BELLY_SMALL"]))

                        #toes
                        nropaws = choice([4, 3, 2, 1, 0, 0])
                        order = ['right front', 'left front', 'right back', 'left back']
                        shuffle(order)

                        for i in range(nropaws):
                            white_pattern.append(order[i] + choice([' toes', ' toes', ' toes', ' mitten']))
                        
                        white_pattern = clean_white(white_pattern)
                elif KITgrade == 3:
                    while len(white_pattern) < 4:
                        #chest
                        if random () < 0.8:
                            white_pattern.append(choice(['chest', 'chest', 'beard', 'chest', 'bib', 
                            "BIB", "CHEST_BROKEN", "CHEST_MID", "DAMIEN_REDUCED"]))

                        # belly
                        if random() < 0.8:
                            white_pattern.append(choice(['belly spot', 'belly', 'belly spot', 'belly', 'belly spot', 'BELLY_SMALL']))

                        #paws
                        nropaws = choice([4, 4, 3, 2, 1, 0])
                        order = ['right front', 'left front', 'right back', 'left back']
                        shuffle(order)
                        pawtype = choice(['same', 'mixed'])

                        for i in range(nropaws):
                            if pawtype == 'same':
                                pawtype = choice([' toes', ' mitten', ' mitten', ' mitten', ' low sock'])
                                white_pattern.append(order[i] + pawtype)
                            else:
                                white_pattern.append(order[i] + choice([' toes', ' mitten', ' mitten', ' low sock']))

                        #face
                        if 'beard' in white_pattern:
                            if random() < 0.5:
                                white_pattern.append(choice(['chin', 'mustache', 'chin', 'BEARD_SMALL']))

                        #tail
                        white_pattern.append(choice(['tail tip', None, None, None, None]))
                        white_pattern.append(choice([None, None, None, choice(['break/nose1', 'break/nose2'])]))
                        white_pattern = clean_white(white_pattern)

                elif KITgrade == 4:
                    while len(white_pattern) < 6:
                        #chest
                        white_pattern.append(choice(
                            ['underbelly1', 'underbelly1', 'underbelly1', 
                            'beard', 'chest', 
                            "CHEST_BROKEN", "BELLY", "CHEST_MID"]))

                        #belly
                        if 'underbelly1' not in white_pattern:
                            white_pattern.append('belly')
                        white_pattern.append(choice(['belt', 'belt', 'pants'] + [None] * 7))

                        #paws
                        nropaws = choice([4, 4, 4, 4, 3, 3, 2, 2, 1])
                        order = ['right front', 'left front', 'right back', 'left back']
                        shuffle(order)
                        pawtype = choice(['same', 'mixed'])

                        for i in range(nropaws):
                            if pawtype == 'same':
                                pawtype = choice([' mitten', ' low sock', ' low sock', ' high sock'])
                                white_pattern.append(order[i] + pawtype)
                            else:
                                white_pattern.append(order[i] + choice([' mitten', ' low sock', ' high sock']))

                        if random() < 0.2:
                            nropaws = choice([4, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1])
                            order = ['right front', 'left front', 'right back', 'left back']
                            shuffle(order)
                            for i in range(nropaws):
                                white_pattern.append("break/"+ order[i] + choice([' toes', ' mitten']))
                        
                        for i in range(randint(0, 2)):
                            white_pattern.append(choice(['break/bracelet left', 'break/bracelet right'] + [None] * 5))

                        #face
                        if 'beard' or 'underbelly1' in white_pattern:
                            if random() < 0.75:
                                white_pattern.append(choice(['chin', 'chin', 'muzzle1', 'muzzle1', 'muzzle2', 'blaze']))

                            if random() < 0.25:
                                white_pattern.append(choice(["BEARD_MID", "BEARD_HIGH"]))
                        if random () < 0.1:
                            white_pattern.append(choice(['break/chin', "break/CHIN"]))

                        #tail
                        white_pattern.append(choice(['tail tip', None, None, None, None]))
                        white_pattern.append(choice([None, None, None, choice(['break/nose1', 'break/nose2'])]))
                        white_pattern = clean_white(white_pattern)
                else:
                    while len(white_pattern) < 6:
                        #chest
                        white_pattern.append('underbelly1')
                        white_pattern.append(choice(['belt', 'belt', 'pants'] + [None] * 7))

                        #paws
                        nropaws = 4
                        order = ['right front', 'left front', 'right back', 'left back']
                        shuffle(order)
                        pawtype = choice(['same', 'mixed'])

                        for i in range(nropaws):
                            if pawtype == 'same':
                                pawtype = choice([' high sock', ' bicolour1', ' bicolour1', ' bicolour2'])
                                white_pattern.append(order[i] + pawtype)
                            else:
                                white_pattern.append(order[i] + choice([' high sock', ' bicolour1', ' bicolour1', ' bicolour2']))

                        if random() < 0.2:
                            nropaws = choice([4, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1])
                            order = ['right front', 'left front', 'right back', 'left back']
                            shuffle(order)
                            pawtype = choice(['same', 'mixed'])
                            for i in range(nropaws):
                                white_pattern.append("break/" + order[i] + choice([' toes', ' mitten', ' mitten']))

                        for i in range(randint(0, 2)):
                            white_pattern.append(choice(['break/bracelet left', 'break/bracelet right'] + [None] * 5))
                        #face
                        white_pattern.append(choice(['chin', 'muzzle1', 'muzzle1', 'muzzle1', 'muzzle2', 'blaze']))

                        if random() < 0.25:
                            white_pattern.append(choice(["BEARD_MID", "BEARD_HIGH"]))

                        if random() < 0.1:
                            white_pattern.append(
                                choice(['break/chin', "break/CHIN"]))

                        #tail
                        white_pattern.append(choice(['tail tip', None, None, None, None]))
                        white_pattern.append(choice([None, None, None, choice(['break/nose1', 'break/nose2'])]))
                        white_pattern = clean_white(white_pattern)
            else:
                if "NoDBE" not in pax3 and (random() < 0.75):
                    white_pattern = [choice(["REVERSEPANTS"])]

                if(randint(1, 4) == 1):
                    white_pattern.append(choice(Pelt.maingame_white["high"].get(str(KITgrade))))

                elif KITgrade == 1:
                    while len(white_pattern) < 6:
                        #chest
                        white_pattern.append('underbelly1')
                        white_pattern.append(choice(['belt', 'belt', 'pants'] + [None] * 7))

                        #paws
                        nropaws = 4
                        order = ['right front', 'left front', 'right back', 'left back']
                        shuffle(order)
                        pawtype = choice(['same', 'mixed'])

                        for i in range(nropaws):
                            if pawtype == 'same':
                                pawtype = choice([' bicolour1', ' bicolour2', ' bicolour2'])
                                white_pattern.append(order[i] + pawtype)
                            else:
                                white_pattern.append(order[i] + choice([' bicolour1', ' bicolour2', ' bicolour2']))

                        if random() < 0.2:
                            nropaws = choice([4, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1])
                            order = ['right front', 'left front', 'right back', 'left back']
                            shuffle(order)
                            for i in range(nropaws):
                                white_pattern.append("break/"+ order[i] + choice([' toes', ' mitten', ' mitten', ' low sock']))

                        for i in range(randint(0, 2)):
                            white_pattern.append(choice(['break/bracelet left', 'break/bracelet right'] + [None] * 5))
                        #face
                        white_pattern.append(choice(['chin', 'muzzle1', 'muzzle1', 'muzzle1', 'muzzle2', 'blaze', 'blaze']))
                        white_pattern.append(choice(['break/chin'] + [None] * 5))

                        if random() < 0.25:
                            white_pattern.append(choice(["BEARD_FULL", "BEARD_HIGH", "BEARD_MID"]))

                        #tail
                        white_pattern.append(choice(['tail tip', None, None, None, None]))
                        white_pattern.append(choice([None, None, None, choice(['break/nose1', 'break/nose2'])]))

                elif KITgrade == 2:
                    #body
                    white_pattern.append(choice(['underbelly1', 'mask n mantle']))

                    white_pattern.append(choice(['break/right no', 'break/left no'] + [None] * 14))
                    white_pattern.append(choice(['break/pants'] + [None] * 9))

                    #paws
                    nropaws = 4
                    order = ['right front', 'left front', 'right back', 'left back']
                    shuffle(order)

                    for i in range(nropaws):
                        white_pattern.append(order[i] + ' bicolour2')

                    if random() < 0.15:
                        nropaws = choice([4, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1])
                        order = ['right front', 'left front', 'right back', 'left back']
                        shuffle(order)
                        for i in range(nropaws):
                            white_pattern.append("break/"+ order[i] + choice([' toes', ' mitten', ' mitten', ' low sock']))

                    for i in range(randint(0, 2)):
                        white_pattern.append(choice(['break/bracelet left', 'break/bracelet right'] + [None] * 5))
                    #face
                    white_pattern.append(choice(['muzzle1', 'muzzle1', 'muzzle2', 'blaze', 'blaze']))

                    if random() < 0.25:
                        white_pattern.append(choice(["BEARD_FULL", "BEARD_HIGH", "BEARD_MID"]))

                    if random () < 0.2:
                        white_pattern.append(choice(['break/nose1', 'break/nose2']))
                    if random () < 0.1:
                        white_pattern.append(choice(['break/chin', "BLAZE_FULL", "FOREHEAD_MID", "break/CHIN"]))

                    #tail
                    white_pattern.append(choice(['tail tip', None, None, None, None]))
                elif KITgrade == 3:
                    white_pattern.append(choice(['van1', 'van2', 'van3']))

                    if random() < 0.25:
                        white_pattern.append(choice(['FOREHEAD_STRIPE']))
                    
                    if random() < 0.1:
                        nropaws = choice([4, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1])
                        order = ['right front', 'left front',
                                 'right back', 'left back']
                        shuffle(order)
                        for i in range(nropaws):
                            white_pattern.append("break/" + order[i] + choice(
                                [' toes', ' toes', ' mitten', ' mitten', ' mitten', ' low sock', ' high sock']))
                    for i in range(randint(0, 2)):
                        white_pattern.append(
                            choice(['break/bracelet left', 'break/bracelet right'] + [None] * 9))

                    if random() < 0.25:
                        white_pattern.append(choice(["break/BACKSPOT"]))
                    white_pattern.append(choice(['break/piebald1', 'break/piebald2', 'break/piebald3']))
                    
                    if random() < 0.1:
                        white_pattern.append(choice(['break/pants']))
                    if random() < 0.05:
                        white_pattern.append(choice(['break/right no', 'break/left no']))
                    
                    if random() < 0.9:
                        for i in range(randint(1, 2)):
                            white_pattern.append(choice([
                                choice(['break/LEFTEAR', 'break/LEFTEAR_MID', 'break/LEFTEAR_MOSTLY', 'break/LEFTEAR_TIP']), 
                                choice(['break/RIGHTEAR', 'break/RIGHTEAR_MID', 'break/RIGHTEAR_MOSTLY', 'break/RIGHTEAR_TIP']), 
                                'break/left face', 'break/right face', 'break/bowl cut', 
                                'break/EYESPOT_L', 'break/EYESPOT_R', "break/FOREHEAD_MIN"]))
                    if random() < 0.25:
                        white_pattern.append(choice(['break/nose1', 'break/nose2']))
                    if random() < 0.1:
                        white_pattern.append(choice(['break/chin', "break/CHIN", "break/FOREHEAD_MID"]))
                elif KITgrade == 4:
                    white_pattern.append(choice(['van1', 'van2', 'van3', 'van1', 'van2', 'van3', 'FULLWHITE']))

                    if random() < 0.25:
                        white_pattern.append(choice(["break/BACKSPOT"]))

                    if random() < 0.05:
                        nropaws = choice([4, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1])
                        order = ['right front', 'left front', 'right back', 'left back']
                        shuffle(order)
                        for i in range(nropaws):
                            white_pattern.append("break/"+ order[i] + choice([' toes', ' toes', ' mitten', ' mitten', ' mitten', ' low sock', ' high sock']))

                    for i in range(randint(0, 2)):
                        white_pattern.append(choice(['break/bracelet left', 'break/bracelet right'] + [None] * 9))
                    white_pattern.append(choice(['break/right no', 'break/left no'] + [None] * 14))
                    white_pattern.append(choice(['break/pants'] + [None] * 14))
                    if random() < 0.66:
                        for i in range(randint(1, 2)):
                            white_pattern.append(choice([
                                choice(['break/LEFTEAR', 'break/LEFTEAR_MID', 'break/LEFTEAR_MOSTLY', 'break/LEFTEAR_TIP']), 
                                choice(['break/RIGHTEAR', 'break/RIGHTEAR_MID', 'break/RIGHTEAR_MOSTLY', 'break/RIGHTEAR_TIP']), 
                                'break/left face', 'break/tail tip', 'break/tail band',
                                'break/tail rings', 'break/right face', 'EYESPOT_REVERSE_L', 'EYESPOT_REVERSE_R', 
                                'break/EYESPOT_L', 'break/EYESPOT_R', "break/FOREHEAD_MIN", "break/FOREHEAD_STRIPE"]))
                    if random() < 0.2:
                        white_pattern.append(choice([
                            choice(['break/LEFTEAR', 'break/LEFTEAR_MID', 'break/LEFTEAR_MOSTLY', 'break/LEFTEAR_TIP']), 
                            choice(['break/RIGHTEAR', 'break/RIGHTEAR_MID', 'break/RIGHTEAR_MOSTLY', 'break/RIGHTEAR_TIP']), 
                            'break/left face', 'break/right face', 'break/bowl cut']))
                    white_pattern.append(choice([None, None, None, None, choice(['break/nose1', 'break/nose2'])]))
                    
                    if random () < 0.1:
                        white_pattern.append(choice(['break/chin', "break/CHIN"]))
                else:
                    white_pattern.append(choice(["FULLWHITE", 'van3']))
                    for i in range(randint(0, 2)):
                        white_pattern.append(choice(['break/bracelet left', 'break/bracelet right'] + [None] * 19))
                        

                    if random() < 0.01:
                        nropaws = choice([4, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1])
                        order = ['right front', 'left front', 'right back', 'left back']
                        shuffle(order)
                        for i in range(nropaws):
                            white_pattern.append("break/"+ order[i] + choice([' toes', ' toes', ' mitten', ' mitten', ' mitten', ' low sock', ' high sock']))

                    if random() < 0.25:
                        white_pattern.append(choice(["break/BACKSPOT"]))

                    if random() < 0.05:
                        white_pattern.append(choice(['break/right no', 'break/left no']))
                    
                    if random() < 0.9:
                        for i in range(randint(1, 2)):
                            white_pattern.append(choice([
                            choice(['break/LEFTEAR', 'break/LEFTEAR_MID', 'break/LEFTEAR_MOSTLY', 'break/LEFTEAR_TIP']), 
                            choice(['break/RIGHTEAR', 'break/RIGHTEAR_MID', 'break/RIGHTEAR_MOSTLY', 'break/RIGHTEAR_TIP']), 
                            'break/tail tip', 'break/tail band', 
                            "break/FOREHEAD_MIN", "break/FOREHEAD_STRIPE"]))
                    elif random() < 0.2:
                        white_pattern.append(choice(['break/left face', 'break/right face', 'break/bowl cut', "break/EYESPOT_R", "break/EYESPOT_L", 'break/chin']))

                    if random() < 0.01:
                        white_pattern = ["FULLWHITE", "break/dorsal stripe"]

            if random() < 0.25:
                if "blaze" in white_pattern:
                    white_pattern.append("BLAZE")
                if "muzzle1" in white_pattern:
                    white_pattern.append(choice(["BLAZE_MID", "ESTRELLA"]))
            if random() < 0.2:
                valid_legs = []
                for w in white_pattern:
                    if w and ("bicolour2" in w or "low sock" in w or "toes" in w or "mitten" in w):
                        valid_legs.append(w)
                if valid_legs:
                    count = choice(range(len(valid_legs)))
                    shuffle(valid_legs)
                    for i in range(count):
                        leg = valid_legs[i]
                        white_pattern.remove(leg)
                        split = leg.removeprefix("break/").split(" ", 2)
                        white_pattern.append(f"{"break/" if "break/" in leg else ""}LEG_{split[1].upper()}_{split[0].upper()}_{split[2].replace("bicolour2", "HIGH").replace("low sock", "MID").replace("mitten", "SMALL").replace("toes", "MIN")}")
        
        if vit:
            if white_pattern is None or white_pattern == "No":
                white_pattern = [choice(vitiligo)]
            else:
                if len(has_vitiligo) == 0:
                    white_pattern.append(choice(vitiligo))
        
        if white_pattern == "No" or white_pattern == [] or white_pattern is None or KIT[0] == "W" or albino[0] == "c" or (KIT[0] == "w" and not vit and pax3 == ['NoDBE', 'NoDBE']):
            return "No"
        return clean_white(white_pattern)

    def check_and_convert(self, convert_dict):
        """Checks for old-type properties for the appearance-related properties
        that are stored in Pelt, and converts them. To be run when loading a cat in."""

        if self.length == "long":
            if self.cat_sprites["adult"] not in self.adult_long_poses:
                self.cat_sprites["adult"] = choice(
                    self.adult_long_poses
                    if self.adult_long_poses
                    else self.adult_short_poses
                )
                self.cat_sprites["young adult"] = self.cat_sprites["adult"]
                self.cat_sprites["senior adult"] = self.cat_sprites["adult"]
                self.cat_sprites["para_adult"] = "para_adult_long0"
        else:
            self.cat_sprites["para_adult"] = "para_adult_short0"
        if self.cat_sprites["senior"] not in self.senior_poses:
            self.cat_sprites["senior"] = choice(self.senior_poses)

        if self.accessory is None:
            self.accessory = tuple()
        elif isinstance(self.accessory, str):
            self.accessory = tuple([self.accessory])

        new_acc_list = []
        for acc in self.accessory:
            if acc in convert_dict["collar_map"]:
                new_acc_list.append(convert_dict["collar_map"][acc])
            else:
                new_acc_list.append(acc)
        self.accessory = tuple(new_acc_list)

    def init_sprite(self):
        self.cat_sprites = {
            "newborn": choice(self.newborn_poses),
            "kitten": choice(self.kitten_poses),
            "senior": choice(self.senior_poses),
            "para_young": "para_young0",
        }
        self.reverse = choice([True, False])

        if self.length != "long":
            self.cat_sprites["adolescent"] = choice(self.adolescent_short_poses)
            self.cat_sprites["adult"] = choice(self.adult_short_poses)
            self.cat_sprites["para_adult"] = "para_adult_short0"
        else:
            self.cat_sprites["adolescent"] = choice(
                self.adolescent_long_poses
                if self.adolescent_long_poses
                else self.adolescent_short_poses
            )
            self.cat_sprites["adult"] = choice(
                self.adult_long_poses
                if self.adult_long_poses
                else self.adult_short_poses
            )
            self.cat_sprites["para_adult"] = "para_adult_long0"
        self.cat_sprites["young adult"] = self.cat_sprites["adult"]
        self.cat_sprites["senior adult"] = self.cat_sprites["adult"]

    def init_scars(self, age):
        if age == "newborn":
            return

        if age in ["kitten", "adolescent"]:
            scar_choice = randint(0, 50)  # 2%
        elif age in ["young adult", "adult"]:
            scar_choice = randint(0, 20)  # 5%
        else:
            scar_choice = randint(0, 15)  # 6.67%

        if scar_choice == 1:
            self.scars = (*self.scars, choice(Pelt.general_scars))

        if "NOTAIL" in self.scars and "HALFTAIL" in self.scars:
            self.scars = tuple(scar for scar in self.scars if scar != "HALFTAIL")

    def init_accessories(self, age):
        if age == "newborn":
            self.accessory = tuple()
            return

        acc_display_choice = randint(0, 80)
        if age in ["kitten", "adolescent"]:
            acc_display_choice = randint(0, 180)
        elif age in ["young adult", "adult"]:
            acc_display_choice = randint(0, 100)

        if acc_display_choice == 1:
            self.accessory = tuple(
                [choice([choice(Pelt.plant_accessories), choice(Pelt.wild_accessories)])]
            )
        else:
            self.accessory = tuple()
            return

        if self.phenotype.bobtailnr > 0 and self.phenotype.bobtailnr < 5 and self.accessory[0] in ['RED FEATHERS', 'BLUE FEATHERS', 'JAY FEATHERS']:
            self.accessory = tuple()
        

    def init_tint(self):
        """Sets tint for pelt and white patches"""
        # PELT TINT
        # Basic tints as possible for all colors.
        base_tints = sprites.cat_tints["possible_tints"]["basic"]
        
        colour = ""
        if self.phenotype.white[0] == "W":
            colour = "WHITE"
        elif 'point' in self.phenotype.point or 'silver' in self.phenotype.silvergold or (self.phenotype.dilute[0] == 'd' and self.phenotype.pinkdilute[0] == "dp"):
            colour = "PALE"
        elif 'gold' in self.phenotype.silvergold or 'sunshine' in self.phenotype.silvergold:
            colour = "GOLDEN"
        else:
            if (self.phenotype.dilute[0] == 'd' or self.phenotype.pinkdilute[0] == "dp"):
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
            self.tint = None

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
            self.white_patches_tint = None

    @staticmethod
    def describe_appearance(cat, short=False):
        
        color_name = cat.phenotype.PhenotypeOutput(pattern=cat.phenotype.white_pattern, gender=cat.genderalign)
        
        if not short:

            scar_details = {
                "NOTAIL": "no tail",
                "HALFTAIL": "half a tail",
                "NOPAW": "three legs",
                "NOLEFTEAR": "a missing ear",
                "NORIGHTEAR": "a missing ear",
                "NOEAR": "no ears"
            }

            scarlist = []
            for scar in cat.pelt.scars:
                if scar in scar_details:
                    scarlist.append(i18n.t(f"cat.pelts.{scar}"))
            color_name += ", with " + adjust_list_text(list(set(scarlist))) if len(scarlist) > 0 else "" # note: this doesn't preserve order!
        return color_name
