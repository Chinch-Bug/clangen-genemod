"""
Contains the Cat and Personality classes
"""

from __future__ import annotations

import bisect
import itertools
import os.path
import sys
import traceback
from random import choice, randint, sample, random, getrandbits, randrange
from operator import xor
from typing import Dict, List, Any, Optional, Union, Callable, TYPE_CHECKING

import i18n
import ujson  # type: ignore

import scripts.game_structure.localization as pronouns
from scripts.cat import save_load
from scripts.cat.enums import CatAge, CatRank, CatSocial, CatGroup, CatStanding
from scripts.cat.history import History
from scripts.cat.names import Name
from scripts.cat.pelts import Pelt
from scripts.cat.phenotype import Genotype
from scripts.cat.phenotype import Phenotype
from scripts.cat.personality import Personality
from scripts.cat.skills import CatSkills
from scripts.cat.status import Status, StatusDict
from scripts.cat.thoughts import Thoughts
from scripts.cat_relations.inheritance import Inheritance
from scripts.cat_relations.relationship import Relationship
from scripts.cat_relations.enums import RelType, RelTier, rel_type_tiers
from scripts.clan_package.settings import get_clan_setting
from scripts.conditions import (
    Illness,
    Injury,
    PermanentCondition,
    get_amount_cat_for_one_medic,
    medicine_cats_can_cover_clan,
)
from scripts.event_class import Single_Event
from scripts.events_module.generate_events import GenerateEvents
from scripts.game_structure import image_cache, constants, game
from scripts.game_structure.game.save_load import safe_save
from scripts.game_structure.game.settings import game_setting_get
from scripts.game_structure.game.switches import switch_get_value, Switch
from scripts.game_structure.localization import load_lang_resource
from scripts.game_structure.screen_settings import screen
from scripts.housekeeping.datadir import get_save_dir
from scripts.utility import (
    clamp,
    find_alive_cats_with_rank,
    get_personality_compatibility,
    event_text_adjust,
    update_sprite,
    leader_ceremony_text_adjust,
    update_mask,
)

import scripts.game_structure.screen_settings

if TYPE_CHECKING:
    import pygame


class Cat:
    """The cat class."""

    dead_cats = []
    used_screen = screen
    current_pronoun_lang = None

    age_moons = {
        CatAge.NEWBORN: constants.CONFIG["cat_ages"]["newborn"],
        CatAge.KITTEN: constants.CONFIG["cat_ages"]["kitten"],
        CatAge.ADOLESCENT: constants.CONFIG["cat_ages"]["adolescent"],
        CatAge.YOUNG_ADULT: constants.CONFIG["cat_ages"]["young adult"],
        CatAge.ADULT: constants.CONFIG["cat_ages"]["adult"],
        CatAge.SENIOR_ADULT: constants.CONFIG["cat_ages"]["senior adult"],
        CatAge.SENIOR: constants.CONFIG["cat_ages"]["senior"],
    }

    # This in is in reverse order: top of the list at the bottom
    rank_sort_order = [
        CatRank.NEWBORN,
        CatRank.KITTEN,
        CatRank.APPRENTICE,
        CatRank.WARRIOR,
        CatRank.ELDER,
        CatRank.MEDIATOR_APPRENTICE,
        CatRank.MEDIATOR,
        CatRank.MEDICINE_APPRENTICE,
        CatRank.MEDICINE_CAT,
        CatRank.DEPUTY,
        CatRank.LEADER,
    ]

    gender_tags = {'molly': 'F', 'tom': 'M', 'intersex': 'I'}

    # EX levels and ranges.
    # Ranges are inclusive to both bounds
    experience_levels_range = {
        "untrained": (0, 0),
        "trainee": (1, 50),
        "prepared": (51, 110),
        "competent": (110, 170),
        "proficient": (171, 240),
        "expert": (241, 320),
        "master": (321, 321),
    }

    all_cats: Dict[str, Cat] = {}  # ID: object
    outside_cats: Dict[str, Cat] = {}  # cats outside the clan
    id_iter = itertools.count()

    all_cats_list: List[Cat] = []
    ordered_cat_list: List[Cat] = []

    grief_strings = {}

    def __init__(
        self,
        prefix=None,
        gender=None,
        status_dict: StatusDict = None,
        backstory="clanborn",
        parent1=None,
        parent2=None,
        extrapar=None,
        kittypet=False,
        adoptive_parents=None,
        suffix=None,
        specsuffix_hidden=False,
        ID=None,
        moons=None,
        example=False,
        faded=False,
        skill_dict=None,
        pelt:Pelt=None,
        genotype:Genotype=None,
        chimerageno:Genotype=None,
        passes=1,
        white_patterns=None,
        chim_white=None,
        chim_pattern=None,
        loading_cat=False,  # Set to true if you are loading a cat at start-up.
        disable_random=False,
        **kwargs,
    ):
        """Initialise the cat.

        :param prefix: Cat's prefix (e.g. Fire- for Fireheart)
        :param gender: Cat's gender, default None
        :param status_dict: Dict containing information for Cat's status, default None
        :param backstory: Cat's origin, default "clanborn"
        :param parent1: ID of parent 1, default None
        :param parent2: ID of parent 2, default None
        :param parent3: ID of parent 3 (second parent of 2nd chimera genotype), default None
        :param suffix: Cat's suffix (e.g. -heart for Fireheart)
        :param specsuffix_hidden: Whether cat has a special suffix (-kit, -paw, etc.), default False
        :param ID: Cat's unique ID, default None
        :param moons: Cat's age, default None
        :param example: If cat is an example cat, default False
        :param faded: If cat is faded, default False
        :param skill_dict: TODO find a good definition for this
        :param genotype: Main genotype, default None
        :param chimerageno: Chimera half genotype, default None
        :param white_patterns: Main white pattern list, default None
        :param chim_white: Chimera white pattern list, default None
        :param chim_pattern: Chimera distribution pattern, default None
        :param loading_cat: If loading a cat rather than generating a new one, default False
        :param disable_random: If True, disables as much random generation junk as possible
        :param kwargs: TODO what are the possible args here? ["biome", ]
        """

        self._history = None

        if (
            faded
        ):  # This must be at the top. It's a smaller list of things to init, which is only for faded cats
            self.init_faded(ID, status_dict, prefix, suffix, moons, **kwargs)
            return

        self.generate_events = GenerateEvents()

        # Private attributes
        self._mentor = None  # plz
        self._experience = None
        self._moons = None

        # Public attributes
        self.gender = gender
        if self.gender == 'female':
            self.gender = 'fem'
        elif self.gender == 'male':
            self.gender = 'masc'
        self.status: Status = Status(**status_dict) if status_dict else Status()
        self.backstory = backstory
        self.age: Optional[CatAge] = None
        self.skills = CatSkills(skill_dict=skill_dict)
        self.personality = Personality(
            trait="troublesome", lawful=0, aggress=0, stable=0, social=0
        )
        self.parent1 = parent1
        self.parent2 = parent2
        self.parent3 = None

        self.passes = passes

        self.adoptive_parents = adoptive_parents.copy() if adoptive_parents else []
        gene_config = constants.CONFIG['genetics_config']
        gene_config.update(constants.CONFIG['april_fools_genes'])
        self.phenotype = Phenotype(gene_config, game_setting_get("ban problem genes"))
        self.chimerapheno = None
        chimera = False
        if chimerageno:
            self.chimerapheno = Phenotype(gene_config, game_setting_get("ban problem genes"))
            self.chimerapheno.fromJSON(chimerageno)
            self.chimerapheno.chimerapattern = chim_pattern if chim_pattern else self.chimerapheno.ChooseTortiePattern("chimera")
            chimera = True
        elif not loading_cat and randint(1, constants.CONFIG['genetics_config']["chimera"]) == 1:
            self.chimerapheno = Phenotype(gene_config, game_setting_get("ban problem genes"))
            self.chimerapheno.chimerapattern = chim_pattern if chim_pattern else self.chimerapheno.ChooseTortiePattern("chimera")
            chimera = True
            if random() < 0.001:
                self.passes = 0
            elif random() < 0.34:
                self.passes = 2

        if genotype:
            self.phenotype.fromJSON(genotype)
        elif parent1 or parent2:
            if not parent1:
                self.phenotype.KitGenerator(Cat.all_cats[parent2], extrapar)
                if chimera:
                    self.chimerapheno.KitGenerator(Cat.all_cats[parent2], extrapar, chimera=True)
            else:
                try:    
                    self.phenotype.KitGenerator(Cat.all_cats[parent1], Cat.all_cats.get(parent2, extrapar), extrapar)
                    if chimera:
                        threepars = self.chimerapheno.KitGenerator(Cat.all_cats[parent1], Cat.all_cats.get(parent2, extrapar), extrapar, chimera=True)
                        if threepars and isinstance(extrapar, Cat):
                            self.parent3 = extrapar.ID
                except:
                    traceback.print_exc()
                    self.phenotype.Generator(kittypet=kittypet)
        else:
            if not chimera:
                if (kittypet or self.status.social == CatSocial.KITTYPET) and constants.CONFIG["cat_generation"]["kittypet_gene_boost"]:
                    self.phenotype.AltGenerator(special=self.gender)
                else:
                    self.phenotype.Generator(special=self.gender, kittypet=kittypet)
            else:
                par1 = Phenotype(gene_config, game_setting_get("ban problem genes"))
                par2 = Phenotype(gene_config, game_setting_get("ban problem genes"))
                if (kittypet or self.status.social == CatSocial.KITTYPET) and constants.CONFIG["cat_generation"]["kittypet_gene_boost"]:
                    par1.AltGenerator()
                    par2.AltGenerator()
                else:
                    par1.Generator(kittypet=kittypet)
                    par2.Generator(kittypet=kittypet)

                self.phenotype.KitGenerator(par1, par2)
                self.chimerapheno.KitGenerator(par1, par2)
            
            if self.phenotype.munch[1] == 'Mk':
                self.phenotype.munch[1] = "mk"
            if self.phenotype.manx[1] not in ['m', 'ab']:
                self.phenotype.manx[1] = self.phenotype.manx[1].lower()
            if 'NoDBE' not in self.phenotype.pax3 and 'DBEalt' not in self.phenotype.pax3:
                self.phenotype.pax3[0] = 'DBEalt'
        
        if not loading_cat:
            if(randint(1, constants.CONFIG['genetics_config']['intersex']) == 1) or (self.chimerapheno and xor('Y' in self.phenotype.sexgene, 'Y' in self.chimerapheno.sexgene) and randint(1, round(constants.CONFIG['genetics_config']['intersex']/4)) == 1):
                self.phenotype.sex = "intersex"
                if(randint(1, 25) == 1 and 'Y' in self.phenotype.sexgene):
                    self.phenotype.sex = 'molly'
                elif(randint(1, 25) == 1 and 'Y' not in self.phenotype.sexgene):
                    self.phenotype.sex = 'tom'
        if self.passes != 1 and (not self.chimerapheno or xor('Y' in self.phenotype.sexgene, 'Y' in self.chimerapheno.sexgene)):
            self.passes = 1

        self.phenotype.PhenotypeOutput(self.phenotype.white_pattern)
        self.phenotype.SpriteInfo(moons if moons else 0)
        if chimera:
            self.chimerapheno.PhenotypeOutput(self.chimerapheno.white_pattern)
            self.chimerapheno.SpriteInfo(moons if moons else 0)

        self.gender = self.phenotype.sex

        self.pelt = pelt if pelt else Pelt(self.phenotype)

        self.former_mentor = []
        self.patrol_with_mentor = 0
        self.apprentice = []
        self.former_apprentices = []
        self.relationships = {}
        self.blank_relations = []
        self.mate = []
        self.previous_mates = []
        self._pronouns: Dict[str, List[Dict[str, Union[str, int]]]] = {}
        self.placement = None
        self.example = example
        self.thought = ""
        self.genderalign = None
        self.birth_cooldown = 0
        self.illnesses = {}
        self.injuries = {}
        self.healed_condition = None
        self.leader_death_heal = None
        self.also_got = False
        self.permanent_condition = {}
        self.experience_level = None
        self.dark_forest_affinity = 0
        self.starclan_affinity = 0

        white_pattern = white_patterns

        self.phenotype.white_pattern = Pelt.generate_white(self.phenotype.white, self.phenotype.pointgene, self.phenotype.whitegrade, self.phenotype.vitiligo, white_pattern, self.phenotype.pax3)
        if self.phenotype.maincolour == 'white' and not self.phenotype.patchmain:
            self.phenotype.white_pattern = "No"

        white_pattern = chim_white
        if self.chimerapheno:    
            self.chimerapheno.white_pattern = Pelt.generate_white(self.chimerapheno.white, self.chimerapheno.pointgene, self.chimerapheno.whitegrade, self.chimerapheno.vitiligo, white_pattern, self.chimerapheno.pax3)
            if self.chimerapheno.maincolour == 'white' and not self.chimerapheno.patchmain:
                self.chimerapheno.white_pattern = "No"

        # Various behavior toggles
        self.no_kits = False
        self.no_mates = False
        self.no_retire = False

        self.prevent_fading = False  # Prevents a cat from fading

        self.faded_offspring = (
            []
        )  # Stores of a list of faded offspring, for relation tracking purposes

        self.faded = faded  # This is only used to flag cats that are faded, but won't be added to the faded list until
        # the next save.

        self.favourite = 0

        self.specsuffix_hidden = specsuffix_hidden
        self.inheritance = None

        # setting ID
        if ID is None:
            potential_id = str(next(Cat.id_iter))

            if game.clan:
                faded_cats = save_load.get_faded_ids()
            else:
                faded_cats = []

            while potential_id in self.all_cats or potential_id in faded_cats:
                potential_id = str(next(Cat.id_iter))
            self.ID = potential_id
        else:
            self.ID = ID

        # age and status
        if status_dict is None and moons is None:
            self.age = CatAge.NEWBORN if disable_random else choice([*CatAge])
            self.status.generate_new_status(age=self.age, disable_random=disable_random)
        elif moons is not None:
            self.moons = moons
            if moons > 300:
                # Out of range, always elder
                self.age = CatAge.SENIOR
            elif moons == 0:
                self.age = CatAge.NEWBORN
            else:
                # In range
                for key_age in self.age_moons.keys():
                    if moons in range(
                        self.age_moons[key_age][0], self.age_moons[key_age][1] + 1
                    ):
                        self.age = key_age
            if status_dict is None:
                self.status.generate_new_status(
                    age=self.age, disable_random=disable_random
                )
        else:
            if disable_random or self.status.rank == CatRank.NEWBORN:
                self.age = CatAge.NEWBORN
            elif self.status.rank == CatRank.KITTEN:
                self.age = CatAge.KITTEN
            elif self.status.rank == CatRank.ELDER:
                self.age = CatAge.SENIOR
            elif self.status.rank.is_any_apprentice_rank():
                self.age = CatAge.ADOLESCENT
            else:
                self.age = choice(
                    [
                        CatAge.YOUNG_ADULT,
                        CatAge.ADULT,
                        CatAge.ADULT,
                        CatAge.SENIOR_ADULT,
                    ]
                )
        if moons is None:
            if disable_random:
                self.moons = 0
            else:
                self.moons = randint(
                    self.age_moons[self.age][0], self.age_moons[self.age][1]
                )


        # backstory
        if self.backstory is None:
            self.backstory = "clanborn"
        else:
            self.backstory = self.backstory  # fixme why does this exist

        # sex!?!??!?!?!??!?!?!?!??
        # if self.gender is None:
        #     self.gender = choice(["female", "male"])

        """if self.genderalign == "":
            self.genderalign = self.gender"""

        # These things should only run when generating a new cat, rather than loading one in.
        if not loading_cat:
            self.init_generate_cat(skill_dict, disable_random)
        
        if self.phenotype.munch[1] == "Mk" or (self.phenotype.manx[1] == "Ab" or self.phenotype.manx[1] == "M") or ('NoDBE' not in self.phenotype.pax3 and 'DBEalt' not in self.phenotype.pax3):
            if not self.dead:
                self.dead = True

        # In camp status
        self.in_camp = 1
        if "biome" in kwargs:
            biome = kwargs["biome"]
        elif game.clan is not None:
            biome = (
                game.clan.biome
                if not game.clan.override_biome
                else game.clan.override_biome
            )
        else:
            biome = None
            
        # NAME
        # load_existing_name is needed so existing cats don't get their names changed/fixed for no reason
        if biome:
            self.name = Name(
                self,
                prefix,
                suffix,
                biome=biome,
                specsuffix_hidden=self.specsuffix_hidden,
                load_existing_name=loading_cat
            )
        else:
            self.name = Name(
                self,
                prefix,
                suffix,
                specsuffix_hidden=self.specsuffix_hidden,
                load_existing_name = loading_cat)
        
        # Private Sprite
        self._sprite: Optional["pygame.Surface"] = None
        self._sprite_mask: Optional["pygame.Mask"] = None
        self._sprite_working: bool = self.not_working()
        """used to store whether we should be displaying sick sprite or not"""

        # SAVE CAT INTO ALL_CATS DICTIONARY IN CATS-CLASS
        self.all_cats[self.ID] = self

        if self.ID is not None and self.ID != "0":
            Cat.insert_cat(self)

    def init_faded(self, ID, status, prefix, suffix, moons, **kwargs):
        """Perform faded-specific initialization

        :param ID: Cat ID
        :param status: Cat status
        :param prefix: Cat's prefix
        :param suffix: Cat's suffix
        :param moons: Age in moons
        :param kwargs:

        :return: None
        """
        self.ID = ID
        self.name = Name(self, prefix=prefix, suffix=suffix, load_existing_name=True)
        self.parent1 = None
        self.parent2 = None
        self.parent3 = None
        self.adoptive_parents = []
        self.mate = []
        self.status = Status(**status) if status else Status()
        self._pronouns = {}  # Needs to be set as a dict
        self.moons = moons
        self.inheritance = None  # This should never be used, but just for safety

        self.init_moons_age(moons)

        self.set_faded()  # Sets the faded sprite and faded tag (self.faded = True)
        return True

    def init_moons_age(self, moons):
        """
        Gets the correct life stage for associated moons

        :param moons: Age in moons
        :return: None
        """
        if moons > 300:
            # Out of range, always elder
            self.age = CatAge.SENIOR
        elif moons == 0:
            self.age = CatAge.NEWBORN
        else:
            # In range
            for key_age in self.age_moons.keys():
                if moons in range(
                    self.age_moons[key_age][0], self.age_moons[key_age][1] + 1
                ):
                    self.age = key_age

    def init_generate_cat(self, skill_dict, disable_random):
        """
        Used to roll a new cat
        :param skill_dict: TODO what is a skill dict exactly
        :param disable_random: If true, disable randomisation code
        :return: None
        """
        # trans cat chances
        self.genderalign = self.gender
        trans_chance = randint(0, 50)
        nb_chance = randint(0, 75)

        # GENDER IDENTITY
        if self.age.is_baby() or disable_random:
            # newborns can't be trans, sorry babies
            nb_chance = 0
            trans_chance = 0
        self.genderalign = ""
        if (self.gender == 'intersex' or 
           (self.gender == "molly" and 'Y' in self.phenotype.sexgene) or 
           (self.gender == "tom" and 'Y' not in self.phenotype.sexgene)):
            self.genderalign = 'intersex '
        if nb_chance == 1:
            self.genderalign += "sam"
        elif (self.gender == "molly" or (self.gender == 'intersex' and 'Y' not in self.phenotype.sexgene)):
            if trans_chance == 1:
                self.genderalign += "trans tom"
            else:
                if(self.gender == 'intersex'):
                    if('Y' in self.phenotype.sexgene):
                        self.genderalign += 'tom'
                    else:
                        self.genderalign += 'molly'
                else:
                    self.genderalign += self.gender
        elif (self.gender == "tom" or (self.gender == 'intersex' and 'Y' in self.phenotype.sexgene)):
            if trans_chance == 1:
                self.genderalign += "trans molly"
            else:
                if(self.gender == 'intersex'):
                    if('Y' in self.phenotype.sexgene):
                        self.genderalign += 'tom'
                    else:
                        self.genderalign += 'molly'
                else:
                    self.genderalign += self.gender

        # PRONOUNS AUTO-GENERATE WHEN REQUIRED

        # APPEARANCE
        self.pelt = Pelt.generate_new_pelt(self.phenotype, self.age)
    
        #Personality
        self.personality = Personality(kit_trait=self.age.is_baby())

        # experience and current patrol status
        if self.age.is_baby() or disable_random:
            self.experience = 0
        elif self.age == CatAge.ADOLESCENT:
            m = self.moons
            self.experience = 0
            while m > Cat.age_moons[CatAge.ADOLESCENT][0]:
                ran = constants.CONFIG["clancat_ex"]["base_app_timeskip_ex"]
                exp = choice(
                    list(range(ran[0][0], ran[0][1] + 1)) + list(range(ran[1][0], ran[1][1] + 1)))
                self.experience += exp + 3
                m -= 1
        elif self.age in (CatAge.YOUNG_ADULT, CatAge.ADULT):
            self.experience = randint(
                Cat.experience_levels_range["prepared"][0],
                Cat.experience_levels_range["proficient"][1],
            )
        elif self.age == CatAge.SENIOR_ADULT:
            self.experience = randint(
                Cat.experience_levels_range["competent"][0],
                Cat.experience_levels_range["expert"][1],
            )
        elif self.age == CatAge.SENIOR:
            self.experience = randint(
                Cat.experience_levels_range["competent"][0],
                Cat.experience_levels_range["master"][1],
            )
        else:
            self.experience = 0
                
        if not skill_dict:
            self.skills = CatSkills.generate_new_catskills(self.status.rank, self.age)
        
        self.genetic_conditions()

    def __repr__(self):
        return "CAT OBJECT:" + self.ID

    def __eq__(self, other):
        return False if not isinstance(other, Cat) else self.ID == other.ID

    def __hash__(self):
        return hash(self.ID)

    def genetic_conditions(self):
        if self.phenotype.deaf:
            if 'blue' in self.phenotype.lefteyetype and 'blue' in self.phenotype.righteyetype:
                if 'DBEre' in self.phenotype.pax3:
                    self.get_permanent_condition(choice(['deaf in one ear', 'deaf in one ear', 'partial hearing loss in one ear', 'deaf', 'deaf', 'partial hearing loss']), born_with=True, genetic=True)
                else:
                    self.get_permanent_condition(choice(['deaf', 'deaf', 'partial hearing loss']), born_with=True, genetic=True)
            elif 'blue' not in self.phenotype.lefteyetype or 'blue' not in self.phenotype.righteyetype:
                self.get_permanent_condition(choice(['deaf in one ear', 'deaf in one ear', 'partial hearing loss in one ear']), born_with=True, genetic=True)
        if ('M' in self.phenotype.manx and self.phenotype.bobtailnr):
            manx_c = 0.95
            if self.phenotype.bobtailnr > 3:
                manx_c = 0.995
            elif self.phenotype.bobtailnr > 1:
                manx_c = 0.98
            if(random() > manx_c):
                self.get_permanent_condition('manx syndrome', born_with=True, genetic=True)
        if self.phenotype.body_label == "snub-nosed cobby":
            self.get_permanent_condition('flat nose', born_with=True, genetic=True)

        if self.phenotype.manx[0] == 'M' and (self.phenotype.manxtype in ['rumpy', 'riser']):
            self.get_permanent_condition('born without a tail', born_with=True, genetic=True)
        
        if ((len(self.phenotype.sexgene) > 2 and 'Y' in self.phenotype.sexgene and random() > 0.001) 
            or len(self.phenotype.sexgene) == 1
            or (self.gender == 'intersex' and random() < 0.2) 
            or (self.gender == 'molly' and 'Y' in self.phenotype.sexgene) 
            or (self.gender == 'tom' and 'Y' not in self.phenotype.sexgene)):
            self.get_permanent_condition('sterile', born_with=True, genetic=True)
        
        if self.phenotype.fold[0] == 'Fd' or ('manx syndrome' in self.permanent_condition and self.phenotype.bobtailnr < 4 and self.phenotype.bobtailnr > 1 and random() < 0.05):
            if not self.phenotype.fold[1] == 'Fd':
                self.get_permanent_condition('constant joint pain', born_with=True, genetic=True, custom_reveal=randint(3, 60))
            else:
                self.get_permanent_condition('constant joint pain', born_with=True, genetic=True)
        if 'manx syndrome' in self.permanent_condition and ((self.phenotype.bobtailnr < 2 and random() > 0.5) or (self.phenotype.bobtailnr > 1 and random() > ((self.phenotype.bobtailnr) * 0.24))):
            self.get_permanent_condition('incontinence', born_with=True, genetic=True)
        if 'manx syndrome' in self.permanent_condition and ((self.phenotype.bobtailnr < 2 and random() > 0.2) or (self.phenotype.bobtailnr > 1 and random() > ((self.phenotype.bobtailnr) * 0.3))):
            self.get_permanent_condition('rabbit gait', born_with=True, genetic=True)
        
        if(self.phenotype.pointgene[0] == 'c'):
            self.get_permanent_condition('albinism', born_with=True, genetic=True)
        elif('albino' in self.phenotype.lefteyetype):
            self.get_permanent_condition('ocular albinism', born_with=True, genetic=True)
        
        if self.phenotype.length == 'hairless':
            self.get_permanent_condition('fully hairless', born_with=True, genetic=True)
        if self.phenotype.length == 'fur-pointed' or 'patchy ' in self.phenotype.furtype:
            self.get_permanent_condition('partially hairless', born_with=True, genetic=True)
        
        if self.phenotype.munch[0] == 'Mk':
            if random() < 0.33:
                self.get_permanent_condition('constant joint pain', born_with=True, genetic=True, custom_reveal=randint(24, 120))
            if random() < 0.2:
                self.get_permanent_condition('bad back', born_with=True, genetic=True)
            if random() < 0.05:
                self.get_permanent_condition('narrowed chest', born_with=True, genetic=True)

        if self.phenotype.lykoi[0] == 'ly':
            self.get_permanent_condition('bumpy skin', born_with=True, genetic=True, custom_reveal=randint(36, 60))

    @property
    def dead(self) -> bool:
        return bool(self.status.group.is_afterlife())

    @dead.setter
    def dead(self, die: bool):
        if die:
            if self.status.group.is_afterlife():
                print(
                    f"WARNING: Tried to kill {self.name} ID: {self.ID} but this cat is already dead!"
                )
                return
            
            instructor = self.status.fetch_clan_object(game.clan).instructor
            if not instructor:
                instructor = game.clan.instructor

            if self.status.get_last_living_group():
            # kits are auto-accepted
                if self.age in (CatAge.KITTEN, CatAge.NEWBORN):
                    self.history.add_afterlife_acceptance(
                        instructor.status.group,
                        is_kit=True,
                    )
                else:
                    if instructor.status.group == CatGroup.STARCLAN:
                        affinity = self.starclan_affinity
                        afterlife_group = CatGroup.STARCLAN
                        rejected_ID = CatGroup.DARK_FOREST_ID
                    else:
                        affinity = self.dark_forest_affinity
                        afterlife_group = CatGroup.DARK_FOREST
                        rejected_ID = CatGroup.STARCLAN_ID

                    # afterlife does not like this cat
                    if affinity < 0:
                        # might send them to the opposite afterlife instead
                        if random() < abs(affinity / 100):
                            self.history.add_afterlife_acceptance(
                                afterlife_group, rejected=True
                            )
                            self.status.send_to_afterlife(rejected_ID)
                            return
                        # fine, they can go to afterlife, but some cats don't like it
                        self.history.add_afterlife_acceptance(
                            afterlife_group, contentious=True
                        )
                    # afterlife thinks this cat is ok
                    else:
                        self.history.add_afterlife_acceptance(afterlife_group)
            self.status.send_to_afterlife()

    @property
    def dead_for(self) -> int:
        return sum(
            entry.get("moons_as")
            for entry in self.status.group_history
            if entry.get("group")
            in (
                CatGroup.STARCLAN_ID,
                CatGroup.UNKNOWN_RESIDENCE_ID,
                CatGroup.DARK_FOREST_ID,
            )
        )

    @dead_for.setter
    def dead_for(self, moons: int):
        self.status.change_current_moons_as(moons)

    @property
    def mentor(self):
        """Return managed attribute '_mentor', which is the ID of the cat's mentor."""
        return self._mentor

    @mentor.setter
    def mentor(self, mentor_id: Any):
        """Makes sure `Cat.mentor` can only be None (no mentor) or a string (mentor ID)."""
        if mentor_id is None or isinstance(mentor_id, str):
            self._mentor = mentor_id
        else:
            print(
                f"Mentor ID {mentor_id} of type {type(mentor_id)} isn't valid :("
                "\nCat.mentor has to be either None (no mentor) or the mentor's ID as a string."
            )

    @property
    def pronouns(self) -> List[Dict[str, Union[str, int]]]:
        """
        Loads the correct pronouns for the loaded language.
        :return: List of dicts for the cat's pronouns
        """
        if self.faded:
            value = pronouns.get_default_pronouns()["0"]
            return [value]

        locale = i18n.config.get("locale")
        value = self._pronouns.get(locale)
        if value is None:
            try:
                self._pronouns[locale] = pronouns.get_new_pronouns(self.genderalign)
            except:
                self._pronouns[locale] = pronouns.get_new_pronouns('sam')
            value = self._pronouns[locale]
        return value

    @pronouns.setter
    def pronouns(
        self,
        val: Union[
            Dict[str, List[Dict[str, Union[str, int]]]],
            List[Dict[str, Union[str, int]]],
        ],
    ):
        """
        Sets the pronouns for the cat. Contains protection for "old-style" pronouns
        :param val:
        :return:
        """
        if isinstance(val, dict):
            self._pronouns = val
            return
        elif isinstance(val, list):
            # possibly old-style pronouns
            self._pronouns[i18n.config.get("locale")] = val
            return

    @property
    def history(self) -> History:
        """load history if it is None"""
        if self._history is None:
            self.load_history()
        return self._history

    @history.setter
    def history(self, val: History):
        self._history = val

    def get_genderalign_string(self):
        # translate it if it's default
        if self.genderalign.replace('intersex ', '') in (
            "molly",
            "tom",
            "trans molly",
            "trans tom",
            "sam",
        ):
            return i18n.t(f"general.{self.genderalign}")
        # otherwise, it's custom - just return it directly
        return self.genderalign

    def get_gender_string(self):
        return i18n.t(f"general.{self.gender}")

    def is_alive(self):
        """Check if this cat is alive

        :return: True if alive, False if dead
        """
        return not self.dead

    def die(self, body: bool = True):
        """Kills cat.

        body - defaults to True, use this to mark if the body was recovered so
        that grief messages will align with body status
        - if it is None, a lost cat died and therefore not trigger grief, since the clan does not know
        """
        clan = self.status.fetch_clan_object() if self.status.is_leader else None
        if (
            self.status.is_leader
            and "pregnant" in self.injuries
            and clan.leader_lives > 0
        ):
            self.illnesses.clear()

            self.injuries = {
                key: value
                for (key, value) in self.injuries.items()
                if key == "pregnant"
            }
        else:
            self.injuries.clear()
            self.illnesses.clear()

        # Deal with leader death
        if self.status.is_leader:
            if clan.leader_lives > 0:
                lives_left = clan.leader_lives
                self.thoughts(just_died=True, lives_left=lives_left)
                return
            elif clan.leader_lives <= 0:
                self.dead = True
                game.just_died.append(self.ID)
                clan.leader_lives = 0
                self.thoughts(just_died=True, lives_left=0)
        else:
            self.dead = True
            game.just_died.append(self.ID)
            self.thoughts(just_died=True)

        for app in self.apprentice.copy():
            fetched_cat = Cat.fetch_cat(app)
            if fetched_cat:
                fetched_cat.update_mentor()
        self.update_mentor()

        if group := self.status.get_last_living_group():
            if self.moons > 1 and not self.status.is_lost(group) and not self.status.is_exiled(group):
                self.grief(body)
            Cat.dead_cats.append(self)

        # mark the sprite as outdated
        self.pelt.rebuild_sprite = True

    def exile(self):
        """This is used to send a cat into exile."""

        self.status.exile_from_group()

        if self.personality.trait == "vengeful":
            self.thought = "Swears their revenge for being exiled"
        else:
            self.thought = "Is shocked that they have been exiled"
        for app in self.apprentice:
            fetched_cat = Cat.fetch_cat(app)
            if fetched_cat:
                fetched_cat.update_mentor()
        self.update_mentor()

    def grief(self, body: bool):
        """
        compiles grief moon event text
        """
        if body:
            body_status = "body"
        else:
            body_status = "no_body"

        # Keep track is the body was treated with rosemary.
        body_treated = False
        text = None

        load_grief_reactions()

        # apply grief to cats with high positive relationships to dead cat
        for cat in Cat.all_cats.values():
            if cat.dead or cat.status.is_outsider or cat.moons < 1 or cat.status.group_ID != self.status.get_last_living_group():
                continue

            rel_with_dead = cat.relationships.get(self.ID)
            if not isinstance(rel_with_dead, Relationship):
                continue

            family_relation = self.familial_grief(living_cat=cat)
            very_high_types = []
            high_types = []
            very_low_types = []

            # find what tier of rel they had for each type
            tiers: list[RelTier] = rel_with_dead.get_reltype_tiers()
            for tier in tiers:
                rel_type = [k for k in rel_type_tiers if tier in rel_type_tiers[k]]
                if tier.is_extreme_pos:
                    very_high_types.extend(rel_type)
                elif tier.is_mid_pos:
                    # 50/50 if this will cause major grief
                    if randint(1, 2) == 1:
                        very_high_types.extend(rel_type)
                    else:
                        high_types.extend(rel_type)
                elif tier.is_low_pos:
                    high_types.extend(rel_type)
                elif tier.is_extreme_neg or tier.is_mid_neg:
                    very_low_types.extend(rel_type)
                continue

            major_chance = 0
            if very_high_types:
                # major grief eligible cats.

                major_chance = 3
                if cat.personality.stability < 5:
                    major_chance -= 1

                # decrease major grief chance if grave herbs are used
                if body and not body_treated and ("rosemary" in game.clan.herb_supply.entire_supply or self.status.get_last_living_group() != CatGroup.PLAYER_CLAN_ID):
                    body_treated = True
                    if self.status.get_last_living_group() == CatGroup.PLAYER_CLAN_ID:
                        game.clan.herb_supply.remove_herb("rosemary", -1)
                        game.herb_events_list.append(
                            f"Rosemary was used for {self.name}'s body."
                        )

                if body_treated:
                    major_chance += 1

            # If major_chance is not 0, there is a chance for major grief
            grief_type = None
            if major_chance and not int(random() * major_chance):
                grief_type = "major"

                possible_strings = []
                for x in very_high_types:
                    possible_strings.extend(
                        self.generate_events.possible_death_reactions(
                            family_relation, x, cat.personality.trait, body_status
                        )
                    )

                if not possible_strings:
                    print("No grief strings")
                    continue

                text = choice(possible_strings)
                text += " " + choice(MINOR_MAJOR_REACTION["major"])
                text = event_text_adjust(Cat, text=text, main_cat=self, random_cat=cat, clan=cat.status.fetch_clan_object(game.clan))

                cat.get_ill("grief stricken", event_triggered=True, severity="major")

            # If major grief fails, but there are still very_high or high values,
            # it can fail to to minor grief. If they have a family relation, bypass the roll.
            elif (very_high_types or high_types) and (
                family_relation != "general" or not int(random() * 5)
            ):
                grief_type = "minor"

                # These minor grief message will be applied as thoughts.
                minor_grief_messages = (
                    "Told a fond story at r_c's vigil",
                    "Bargains with StarClan, begging them to send r_c back",
                    "Sat all night at r_c's vigil",
                    "Will never forget r_c",
                    "Prays that r_c is safe in StarClan",
                    "Misses the warmth that r_c brought to {PRONOUN/m_c/poss} life",
                    "Is mourning r_c",
                    "Can't stop coming to tears each time r_c is mentioned",
                    "Stayed the longest at r_c's vigil",
                    "Left r_c's vigil early due to grief",
                    "Lashes out at any cat who checks on {PRONOUN/m_c/object} after r_c's death",
                    "Took a long walk on {PRONOUN/m_c/poss} own to mourn r_c in private",
                    "Is busying {PRONOUN/m_c/self} with too much work to forget about r_c's death",
                    "Does {PRONOUN/m_c/poss} best to console {PRONOUN/m_c/poss} clanmates about r_c's death",
                    "Takes a part of r_c's nest to put with {PRONOUN/m_c/poss} own, clinging to the fading scent",
                    "Sleeps in r_c's nest tonight",
                    "Defensively states that {PRONOUN/m_c/subject} {VERB/m_c/don't/doesn't} need any comfort about r_c's death",
                    "Wonders why StarClan had to take r_c so soon",
                    "Still needs r_c even though they're gone",
                    "Doesn't think {PRONOUN/m_c/subject} will ever be the same without r_c",
                    "Was seen crying in {PRONOUN/m_c/poss} nest after r_c's vigil",
                    "Is hiding {PRONOUN/m_c/poss} tears as {PRONOUN/m_c/subject} {VERB/m_c/comfort/comforts} the others about r_c's passing",
                )

                if body:
                    minor_grief_messages += (
                        "Helped bury r_c, leaving {PRONOUN/r_c/poss} favorite prey at the grave",
                        "Slips out of camp to visit r_c's grave",
                        "Clung so desperately to r_c's body that {PRONOUN/m_c/subject} had to be dragged away",
                        "Hides a scrap of r_c's fur under {PRONOUN/m_c/poss} nest to cling to",
                        "Can't stand the sight of r_c's body in camp",
                        "Hissed at anyone who got too close to r_c's body, refusing to let go",
                        "Spent a long time grooming r_c's fur for their vigil",
                        "Arranged the flowers for r_c's vigil",
                        "Picked the best spot in the burial grounds for r_c",
                        "Keeps thinking that r_c is only sleeping",
                        "Is in denial of r_c's death, despite the ongoing vigil",
                        "Insists that r_c isn't gone",
                        "Begs r_c not to leave them all",
                        "Sleeps next to r_c for the entire vigil one last time",
                        "Ran out of camp the moment {PRONOUN/m_c/subject} saw r_c's body",
                        "Sang a song in memory of r_c at the vigil",
                        "Stares at r_c's vigil longingly, but doesn't feel the right to join in",
                    )

                text = choice(minor_grief_messages)

            if grief_type:
                # Generate the event:
                if cat.ID not in Cat.grief_strings:
                    Cat.grief_strings[cat.ID] = []

                Cat.grief_strings[cat.ID].append((text, (self.ID, cat.ID), grief_type))
                continue

            # Negative "grief" messages are just for flavor.
            elif very_low_types:
                # Generate the event:
                possible_strings = []
                for x in very_low_types:
                    value = f"neg_{x}"
                    possible_strings.extend(
                        self.generate_events.possible_death_reactions(
                            family_relation, value, cat.personality.trait, body_status
                        )
                    )

                text = event_text_adjust(
                    Cat, choice(possible_strings), main_cat=self, random_cat=cat, clan=self.status.fetch_clan_object(game.clan)
                )
                if cat.ID not in Cat.grief_strings:
                    Cat.grief_strings[cat.ID] = []

                Cat.grief_strings[cat.ID].append((text, (self.ID, cat.ID), "negative"))

    def familial_grief(self, living_cat: Cat):
        """
        returns relevant grief strings for family members, if no relevant strings then returns None
        """
        dead_cat = self

        if dead_cat.is_parent(living_cat):
            return "child"
        elif living_cat.is_parent(dead_cat):
            return "parent"
        elif dead_cat.is_sibling(living_cat):
            return "sibling"
        else:
            return "general"

    def become_lost(self, status = None, standing = CatStanding.LOST):
        """Makes a Clan cat a lost cat. Makes status changes and removes apprentices."""

        if self.status.is_leader:
            self.status.fetch_clan_object().leader = None
        if self.status.rank == CatRank.DEPUTY:
            self.status.fetch_clan_object().deputy = None
        if self.status.rank.is_any_medicine_rank():
            self.status.fetch_clan_object().remove_med_cat(self)

        self.status.become_lost(
            new_social_status=choice([CatSocial.KITTYPET, CatSocial.LONER]) if not status else status,
            override_standing=standing
        )

        for app in self.apprentice.copy():
            app_ob = Cat.fetch_cat(app)
            if app_ob:
                app_ob.update_mentor()

        self.update_mentor()

        for x in self.apprentice:
            Cat.fetch_cat(x).update_mentor()

    def add_to_clan(self, clan: CatGroup = CatGroup.PLAYER_CLAN_ID, add_kits=True) -> list:
        """Makes an "outside cat" a Clan cat. Returns a list of IDs for any additional cats that
        are coming with them."""

        if not self.status.is_exiled(clan):
            self.history.add_beginning()

        self.status.add_to_group(new_group_ID=clan, age=self.age)

        game.clan.add_to_clan(self)

        # check if there are kits under 12 moons with this cat and also add them to the clan
        children = self.get_children()
        ids = []
        for child_id in children:
            child = Cat.fetch_cat(child_id)
            if (
                child and
                not child.dead
                and child.status.is_outsider
                and not child.status.is_exiled(clan)
                and child.moons < 12
            ):
                if add_kits:
                    # child.status.add_to_group(new_group=clan, age=self.age)
                    child.add_to_clan(clan)
                else:
                    game.clan.add_to_clan(self)
                child.history.add_beginning()
                ids.append(child_id)

        return ids

    def rank_change(self, new_rank: CatRank, resort=False):
        """Changes the status of a cat. Additional functions are needed if you want to make a cat a leader or deputy.
        :param new_rank: CatRank that the cat is becoming
        :param resort: If sorting type is 'rank', and resort is True, it will resort the cat list. This should
                only be true for non-timeskip status changes."""

        clan = self.status.fetch_clan_object(game.clan)
        old_rank = self.status.rank

        # this is a private function, but it's meant to be used here.
        self.status._change_rank(new_rank)  # pylint: disable=protected-access

        self.name.status = new_rank

        self.update_mentor()
        for app in self.apprentice.copy():
            fetched_cat = Cat.fetch_cat(app)
            if isinstance(fetched_cat, Cat):
                fetched_cat.update_mentor()

        # If they have any apprentices, make sure they are still valid:
        if old_rank == CatRank.MEDICINE_CAT:
            clan.remove_med_cat(self)

        # updates mentors
        if self.status.rank in [
            CatRank.APPRENTICE,
            CatRank.MEDICINE_APPRENTICE,
            CatRank.MEDIATOR_APPRENTICE,
            CatRank.MEDIATOR,
        ]:
            pass

        elif self.status.rank == CatRank.WARRIOR:
            if old_rank == CatRank.LEADER and (
                clan.leader and clan.leader.ID == self.ID
            ):
                clan.leader = None
                clan.leader_predecessors += 1
            if clan and clan.deputy and clan.deputy.ID == self.ID:
                clan.deputy = None
                clan.deputy_predecessors += 1

        elif self.status.rank == CatRank.MEDICINE_CAT:
            if clan is not None:
                clan.new_medicine_cat(self)

        elif self.status.rank == CatRank.ELDER:
            if (
                old_rank == CatRank.LEADER
                and clan.leader
                and clan.leader.ID == self.ID
            ):
                clan.leader = None
                clan.leader_predecessors += 1

            if clan.deputy and clan.deputy.ID == self.ID:
                clan.deputy = None
                clan.deputy_predecessors += 1

        # update class dictionary
        self.all_cats[self.ID] = self

        # If we have it sorted by rank, we also need to re-sort
        if switch_get_value(Switch.sort_type) == "rank" and resort:
            Cat.sort_cats()

    def rank_change_traits_skill(self, mentor):
        """Updates trait and skill upon ceremony"""

        if self.status.rank in (
            CatRank.WARRIOR,
            CatRank.MEDICINE_CAT,
            CatRank.MEDIATOR,
        ):
            # Give a couple doses of mentor influence:
            if mentor:
                max_influence = randint(0, 2)
                i = 0
                while max_influence > i:
                    i += 1
                    affect_personality = self.personality.mentor_influence(
                        Cat.fetch_cat(mentor).personality
                    )
                    affect_skills = self.skills.mentor_influence(Cat.fetch_cat(mentor))
                    if affect_personality:
                        self.history.add_facet_mentor_influence(
                            mentor.ID,
                            affect_personality[0],
                            affect_personality[1],
                        )
                    if affect_skills:
                        self.history.add_skill_mentor_influence(
                            affect_skills[0], affect_skills[1], affect_skills[2]
                        )

            self.history.add_mentor_skill_influence_strings()
            self.history.add_mentor_facet_influence_strings()
        return

    def change_name(self, new_prefix=None, new_suffix=None):
        self.name = Name(
            cat=self,
            prefix=new_prefix,
            suffix=new_suffix,
            biome=game.clan.biome,
            specsuffix_hidden=self.specsuffix_hidden,
        )

    def manage_outside_trait(self):
        """To be run every moon on outside cats
        to keep trait and skills making sense."""
        if not self.status.is_outsider and not self.status.is_other_clancat:
            return

        self.personality.set_kit(self.age.is_baby())  # Update kit trait stuff

    def describe_cat(self, short=False):
        """ Generates a string describing the cat's appearance and gender. Mainly used for generating
        the allegiances. If short is true, it will generate a very short one, with the minimal amount of information. """
        return Pelt.describe_appearance(self, short)

    def create_genelist(self):
        genelist = str(self.phenotype.PhenotypeOutput(self.phenotype.white_pattern, chimera=self.chimerapheno)) + \
            "\n" + str(self.phenotype.ShowGenes(True)) + "\n" + self.phenotype.FormatSomatic()
        if (self.chimerapheno):
            genelist += "\n\n" + str(self.chimerapheno.PhenotypeOutput(self.chimerapheno.white_pattern, chimera=self.chimerapheno))

        return genelist

    def describe_eyes(self):
        if(self.phenotype.lefteye == self.phenotype.righteye):
            colour = self.phenotype.lefteye.lower()
        else:
            colour = self.phenotype.righteye.lower() + " & " + self.phenotype.lefteye.lower()
        
        return colour

    def convert_history(self, died_by, scar_events):
        """
        Handle old history save conversions
        """
        deaths = []
        if died_by:
            deaths.extend(
                {"involved": None, "text": death, "moon": "?"} for death in died_by
            )
        scars = []
        if scar_events:
            scars.extend(
                {"involved": None, "text": scar, "moon": "?"} for scar in scar_events
            )
        self.history = History(died_by=deaths, scar_events=scars, cat=self)

    def load_history(self):
        """Load this cat's history"""
        if self._history:
            return

        try:
            if switch_get_value(Switch.clan_name) != "":
                clanname = switch_get_value(Switch.clan_name)
            else:
                clanname = switch_get_value(Switch.clan_list)[0]
        except IndexError:
            print("WARNING: History failed to load, no Clan in switches?")
            return

        history_directory = f"{get_save_dir()}/{clanname}/history/"
        cat_history_directory = history_directory + self.ID + "_history.json"

        if not os.path.exists(cat_history_directory):
            self._history = History(
                prev_names = [],
                beginning={},
                mentor_influence={},
                app_ceremony={},
                lead_ceremony=None,
                possible_history={},
                died_by=[],
                scar_events=[],
                murder={},
                cat=self,
            )
            return
        try:
            with open(cat_history_directory, "r", encoding="utf-8") as read_file:
                history_data = ujson.loads(read_file.read())

                self._history = History(
                    prev_names = history_data["prev_names"] if "prev_names" in history_data else [],
                    beginning=(
                        history_data["beginning"] if "beginning" in history_data else {}
                    ),
                    mentor_influence=(
                        history_data["mentor_influence"]
                        if "mentor_influence" in history_data
                        else {}
                    ),
                    app_ceremony=(
                        history_data["app_ceremony"]
                        if "app_ceremony" in history_data
                        else {}
                    ),
                    lead_ceremony=(
                        history_data["lead_ceremony"]
                        if "lead_ceremony" in history_data
                        else None
                    ),
                    possible_history=(
                        history_data["possible_history"]
                        if "possible_history" in history_data
                        else {}
                    ),
                    died_by=(
                        history_data["died_by"] if "died_by" in history_data else []
                    ),
                    scar_events=(
                        history_data["scar_events"]
                        if "scar_events" in history_data
                        else []
                    ),
                    murder=history_data["murder"] if "murder" in history_data else {},
                    afterlife_acceptance=(
                        history_data["afterlife_acceptance"]
                        if "afterlife_acceptance" in history_data
                        else None
                    ),
                    cat=self,
                )
        except Exception:
            self._history = None
            print(
                f"WARNING: There was an error reading the history file of cat #{self} or their history file was "
                f"empty. Default history info was given. Close game without saving if you have save information "
                f"you'd like to preserve!"
            )

    def save_history(self, history_dir):
        """Save this cat's history.

        :param history_dir: Directory to save cat's history to
        :type history_dir: str
        """
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)

        history_dict = self.history.make_dict()
        try:
            safe_save(f"{history_dir}/{self.ID}_history.json", history_dict)
        except:
            self.history = History(
                prev_names=[],
                beginning={},
                mentor_influence={},
                app_ceremony={},
                lead_ceremony=None,
                possible_history={},
                died_by=[],
                scar_events=[],
                murder={},
                cat=self,
            )

            print(f"WARNING: saving history of cat #{self.ID} didn't work")

    def generate_lead_ceremony(self):
        """Create a leader ceremony and add it to the history"""

        load_leader_ceremonies()

        # determine which dict we're pulling from
        if self.status.fetch_clan_object(game.clan).instructor.status.group == CatGroup.DARK_FOREST:
            starclan = False
            ceremony_dict: Dict = LEAD_CEREMONY_DF
        else:
            starclan = True
            ceremony_dict: Dict = LEAD_CEREMONY_SC

        # ---------------------------------------------------------------------------- #
        #                                    INTRO                                     #
        # ---------------------------------------------------------------------------- #
        all_intros = ceremony_dict["intros"]

        # filter the intros
        possible_intros = []
        for intro in all_intros:
            tags = all_intros[intro]["tags"]

            if game.clan.age != 0 and "new_clan" in tags:
                continue
            elif game.clan.age == 0 and "new_clan" not in tags:
                continue

            if (
                all_intros[intro]["lead_trait"]
                and self.personality.trait not in all_intros[intro]["lead_trait"]
            ):
                continue
            possible_intros.append(all_intros[intro])

        if chosen_intro := choice(possible_intros):
            intro = choice(chosen_intro["text"])
            intro = leader_ceremony_text_adjust(
                Cat,
                intro,
                self
            )
        else:
            intro = "this should not appear"

        # ---------------------------------------------------------------------------- #
        #                                 LIFE GIVING                                  #
        # ---------------------------------------------------------------------------- #
        life_givers = []
        dead_relations = []
        life_giving_leader = None

        # grab life givers that the cat actually knew in life and sort by amount of relationship!
        relationships = self.relationships.values()

        for rel in relationships:
            kitty = self.fetch_cat(rel.cat_to)
            if kitty and kitty.dead and kitty.status.rank != CatRank.NEWBORN:
                # check where they reside
                if starclan:
                    if kitty.status.group != CatGroup.STARCLAN:
                        continue
                else:
                    if kitty.status.group != CatGroup.DARK_FOREST:
                        continue
                # guides aren't allowed here
                if kitty in [game.clan.instructor] + [clan.instructor for clan in game.clan.all_other_clans if clan.instructor]:
                    continue
                else:
                    dead_relations.append(rel)

        # sort relations by the strength of their relationship
        dead_relations.sort(
            key=lambda rel: rel.romance
            + rel.like
            + rel.respect
            + rel.comfort
            + rel.trust,
            reverse=True,
        )

        # if we have relations, then make sure we only take the top 8
        if dead_relations:
            for i, rel in enumerate(dead_relations):
                if rel.cat_to.faded:
                    continue
                if i == 8:
                    break
                if rel.cat_to.status.is_leader:
                    life_giving_leader = rel.cat_to
                    continue
                life_givers.append(rel.cat_to.ID)

        cats_in_afterlife = [
            self.fetch_cat(i)
            for i in game.clan.clan_cats
            if self.fetch_cat(i)
            and i not in life_givers
            and self.fetch_cat(i).status.group
            == (CatGroup.STARCLAN if starclan else CatGroup.DARK_FOREST)
        ]

        # check amount of life givers, if we need more, then grab from the other dead cats
        if len(life_givers) < 8:
            amount = 8 - len(life_givers)

            possible_dead_cats = [
                i
                for i in cats_in_afterlife
                if i.status.rank not in (CatRank.LEADER, CatRank.NEWBORN)
            ]
            # this part just checks how many cats are available, if there aren't enough to fill all the slots,
            # then we just take however many are available

            if len(possible_dead_cats) - 1 < amount:
                extra_givers = possible_dead_cats
            else:
                extra_givers = sample(possible_dead_cats, k=amount)

            life_givers.extend(extra_givers)

        # making sure we have a leader at the end
        ancient_leader = False
        leaders = [x for x in cats_in_afterlife if x.status.is_leader and (x.status.get_last_living_group() == self.status.group_ID or x.dead_for > 300)]
        if not life_giving_leader and leaders:
            # choosing if the life giving leader will be the oldest leader or previous leader
            coin_flip = randint(1, 2)
            if coin_flip == 1:
                # pick the oldest leader
                leaders.sort(key=lambda x: -1 * int(x.dead_for))
                ancient_leader = True
                life_giving_leader = leaders[0] if leaders else None
            else:
                # pick previous leader
                leaders.sort(key=lambda x: int(Cat.fetch_cat(x).dead_for))
                life_giving_leader = leaders[0] if leaders else None

        if life_giving_leader:
            life_givers.append(life_giving_leader)

        # check amount again, if more are needed then we'll add the ghost-y cats at the end
        if len(life_givers) < 9:
            unknown_blessing = True
        else:
            unknown_blessing = False
        extra_lives = str(9 - len(life_givers))
        possible_lives = ceremony_dict["lives"]
        lives = []
        used_lives = []
        used_virtues = []
        for giver in life_givers:
            giver_cat = self.fetch_cat(giver)
            if not giver_cat:
                continue
            life_list = []
            for life in possible_lives:
                tags = possible_lives[life]["tags"]
                rank = giver_cat.status.rank

                if "unknown_blessing" in tags:
                    continue

                if "guide" in tags and giver_cat not in [game.clan.instructor] + [clan.instructor for clan in game.clan.all_other_clans if clan.instructor]:
                    continue
                if game.clan.age != 0 and "new_clan" in tags:
                    continue
                elif game.clan.age == 0 and "new_clan" not in tags:
                    continue
                if "old_leader" in tags and not ancient_leader:
                    continue
                if "leader_parent" in tags and giver_cat.ID not in self.get_parents():
                    continue
                elif "leader_child" in tags and giver_cat.ID not in self.get_children():
                    continue
                elif (
                    "leader_sibling" in tags and giver_cat.ID not in self.get_siblings()
                ):
                    continue
                elif "leader_mate" in tags and giver_cat.ID not in self.mate:
                    continue
                elif (
                    "leader_former_mate" in tags
                    and giver_cat.ID not in self.previous_mates
                ):
                    continue
                if "leader_mentor" in tags and giver_cat.ID not in self.former_mentor:
                    continue
                if (
                    "leader_apprentice" in tags
                    and giver_cat.ID not in self.former_apprentices
                ):
                    continue
                if (
                    possible_lives[life]["rank"]
                    and rank not in possible_lives[life]["rank"]
                ):
                    continue
                if (
                    possible_lives[life]["lead_trait"]
                    and self.personality.trait not in possible_lives[life]["lead_trait"]
                ):
                    continue
                if possible_lives[life]["star_trait"] and (
                    giver_cat.personality.trait
                    not in possible_lives[life]["star_trait"]
                ):
                    continue
                life_list.extend(list(possible_lives[life]["life_giving"]))

            i = 0
            chosen_life = {}
            while i < 10:
                attempted = []
                if life_list:
                    chosen_life = choice(life_list)
                    if chosen_life not in used_lives and chosen_life not in attempted:
                        break
                    attempted.append(chosen_life)
                    i += 1
                else:
                    print(
                        f"WARNING: life list had no items for giver #{giver_cat.ID}. Using default life. "
                        f"If you are a beta tester, please report and ping scribble along with "
                        f"all the info you can about the giver cat mentioned in this warning."
                    )
                    chosen_life = ceremony_dict["default_life"]
                    break

            used_lives.append(chosen_life)
            if "virtue" in chosen_life:
                poss_virtues = [
                    i for i in chosen_life["virtue"] if i not in used_virtues
                ] or ["faith", "friendship", "love", "strength"]
                virtue = choice(poss_virtues)
                used_virtues.append(virtue)
            else:
                virtue = None

            lives.append(
                leader_ceremony_text_adjust(
                    Cat,
                    chosen_life["text"],
                    leader=self,
                    life_giver=giver,
                    virtue=virtue
                )
            )
        if unknown_blessing:
            possible_blessing = []
            for life in possible_lives:
                tags = possible_lives[life]["tags"]

                if "unknown_blessing" not in tags:
                    continue

                if (
                    possible_lives[life]["lead_trait"]
                    and self.personality.trait not in possible_lives[life]["lead_trait"]
                ):
                    continue
                possible_blessing.append(possible_lives[life])
            chosen_blessing = choice(possible_blessing)
            chosen_text = choice(chosen_blessing["life_giving"])
            lives.append(
                leader_ceremony_text_adjust(
                    Cat,
                    chosen_text["text"],
                    leader=self,
                    virtue=chosen_text["virtue"],
                    extra_lives=extra_lives
                )
            )
        all_lives = "<br><br>".join(lives)

        # ---------------------------------------------------------------------------- #
        #                                    OUTRO                                     #
        # ---------------------------------------------------------------------------- #

        # get the outro
        all_outros = ceremony_dict["outros"]

        possible_outros = []
        for outro in all_outros:
            tags = all_outros[outro]["tags"]

            if game.clan.age != 0 and "new_clan" in tags:
                continue
            elif game.clan.age == 0 and "new_clan" not in tags:
                continue

            if (
                all_outros[outro]["lead_trait"]
                and self.personality.trait not in all_outros[outro]["lead_trait"]
            ):
                continue
            possible_outros.append(all_outros[outro])

        chosen_outro = choice(possible_outros)

        if chosen_outro:
            if life_givers:
                giver = life_givers[-1]
            else:
                giver = None
            outro = choice(chosen_outro["text"])
            outro = leader_ceremony_text_adjust(
                Cat,
                outro,
                leader=self,
                life_giver=giver
            )
        else:
            outro = "this should not appear"

        full_ceremony = "<br><br>".join([intro, all_lives, outro])
        self.history.lead_ceremony = full_ceremony

    # ---------------------------------------------------------------------------- #
    #                              moon skip functions                             #
    # ---------------------------------------------------------------------------- #

    def one_moon(self, other_clan_cats: list = None):
        """Handles a moon skip for an alive cat."""
        old_age = self.age

        if self.dead and not self.faded:
            self.thoughts()
            return

        self.moons += 1
        if self.moons == 1 and self.status.rank == CatRank.NEWBORN:
            self.status._change_rank(CatRank.KITTEN)
        self.in_camp = 1

        if not self.status.is_clancat:
            # this is handled in events.py
            self.personality.set_kit(self.age.is_baby())
            self.thoughts(other_clan_cats=other_clan_cats)
            return

        if old_age != self.age:
            # Things to do if the age changes
            self.personality.facet_wobble(facet_max=2)

        # Set personality to correct type
        self.personality.set_kit(self.age.is_baby())
        # Upon age-change

        if self.status.rank.is_any_apprentice_rank():
            self.update_mentor()

    def thoughts(
        self, just_died=False, lives_left: int = 0, other_clan_cats: list = None
    ):
        """
        Generates a thought for the cat, which displays on their profile.
        :param just_died: Set True if the cat is generating a death thought
        :param lives_left: If a leader is generating a death thought, include their lives left here
        """
        if self.status.is_other_clancat:
            if not other_clan_cats:
                all_cats = []
            else:
                all_cats = other_clan_cats.copy()
                all_cats.remove(self)
        else:
            all_cats = self.all_cats_list.copy()
            all_cats.remove(self)

        game_mode = switch_get_value(Switch.game_mode)
        biome = switch_get_value(Switch.biome)
        camp = switch_get_value(Switch.camp_bg)
        try:
            season = game.clan.current_season
        except Exception:
            season = None

        # get other cat
        i = 0
        other_cat = None
        if all_cats:
            other_cat = choice(all_cats)
            # for cats inside the clan
            if self.status.is_clancat:
                # we want to limit how often dead cats are thought about
                thinking_of_dead_cat = getrandbits(4) == 1
                while all_cats and (
                    (other_cat.dead and not thinking_of_dead_cat)
                    or other_cat.ID not in self.relationships
                    or other_cat.status.group_ID != self.status.group_ID
                ):
                    all_cats.remove(other_cat)

                    if not all_cats or i > 100:
                        other_cat = None
                        break

                    other_cat = choice(all_cats)

                    i += 1

            # for dead cats, they can think about whoever they want
            elif self.status.group.is_afterlife():
                other_cat = choice(all_cats)

            # for cats currently outside
            # it appears as for now, kittypets and loners can only think about outsider cats
            elif self.status.is_outsider:
                while all_cats and (other_cat not in self.relationships):
                    all_cats.remove(other_cat)
                    if not all_cats:
                        other_cat = None
                        break

                    other_cat = choice(all_cats)

                    i += 1
                    if i > 100:
                        other_cat = None
                        break

        if self.status.is_clancat:
            clan = self.status.fetch_clan_object()
        elif other_cat and other_cat.status.is_clancat:
            clan = other_cat.status.fetch_clan_object()
        else:
            clan = game.clan

        # get chosen thought
        if just_died:
            afterlife = (
                self.status.group
                if self.status.group.is_afterlife()
                else clan.instructor.status.group
            )
            chosen_thought = Thoughts.new_death_thought(
                self, other_cat, game_mode, biome, season, camp, afterlife, lives_left
            )
        else:
            chosen_thought = Thoughts.get_chosen_thought(
                self, other_cat, game_mode, biome, season, camp, game_setting_get("ageup dead")
            )

        chosen_thought = event_text_adjust(
            self.__class__,
            chosen_thought,
            main_cat=self,
            random_cat=other_cat,
            clan=clan,
        )

        # insert thought
        self.thought = str(chosen_thought)

    def relationship_interaction(self):
        """Randomly choose a cat of the Clan and have an interaction with them."""
        cats_to_choose = [
            iter_cat
            for iter_cat in Cat.all_cats.values()
            if iter_cat.ID != self.ID and iter_cat.status.group_ID == self.status.group_ID
        ]
        # if there are no cats to interact, stop
        if not cats_to_choose:
            return

        chosen_cat = choice(cats_to_choose)
        if chosen_cat.ID not in self.relationships:
            self.create_one_relationship(chosen_cat)
        relevant_relationship = self.relationships[chosen_cat.ID]
        relevant_relationship.start_interaction()

        # handle contact with ill cat if
        if self.is_ill():
            relevant_relationship.cat_to.contact_with_ill_cat(self)
        if relevant_relationship.cat_to.is_ill():
            self.contact_with_ill_cat(relevant_relationship.cat_to)

    def moon_skip_illness(self, illness):
        """handles the moon skip for illness"""
        if not self.is_ill():
            return True

        if self.illnesses[illness]["event_triggered"]:
            self.illnesses[illness]["event_triggered"] = False
            return True

        mortality = self.illnesses[illness]["mortality"]

        # leader should have a higher chance of death
        if self.status.is_leader and mortality != 0:
            mortality = int(mortality * 0.7)
            if mortality == 0:
                mortality = 1

        if mortality and not int(random() * mortality):
            if self.status.is_leader:
                self.leader_death_heal = True
                self.status.fetch_clan_object().leader_lives -= 1

            self.die()
            return False

        moons_with = game.clan.age - self.illnesses[illness]["moon_start"]

        # focus buff
        moons_prior = constants.CONFIG["focus"]["rest and recover"][
            "moons_earlier_healed"
        ]

        if self.illnesses[illness]["duration"] - moons_with <= 0:
            self.healed_condition = True
            return False

        # CLAN FOCUS! - if the focus 'rest and recover' is selected
        elif (
            get_clan_setting("rest and recover") and self.status.group_ID == CatGroup.PLAYER_CLAN_ID
            and self.illnesses[illness]["duration"] + moons_prior - moons_with <= 0
        ):
            self.healed_condition = True
            return False

    def moon_skip_injury(self, injury):
        """handles the moon skip for injury"""
        if not self.is_injured():
            return True

        if self.injuries[injury]["event_triggered"] is True:
            self.injuries[injury]["event_triggered"] = False
            return True

        mortality = self.injuries[injury]["mortality"]

        # leader should have a higher chance of death
        if self.status.is_leader and mortality != 0:
            mortality = int(mortality * 0.7)
            if mortality == 0:
                mortality = 1

        if mortality and not int(random() * mortality):
            if self.status.is_leader:
                self.status.fetch_clan_object().leader_lives -= 1
            self.die()
            return False

        moons_with = game.clan.age - self.injuries[injury]["moon_start"]

        # focus buff
        moons_prior = constants.CONFIG["focus"]["rest and recover"][
            "moons_earlier_healed"
        ]

        # if the cat has an infected wound, the wound shouldn't heal till the illness is cured
        if (
            not self.injuries[injury]["complication"]
            and self.injuries[injury]["duration"] - moons_with <= 0
        ):
            self.healed_condition = True
            return False

        # CLAN FOCUS! - if the focus 'rest and recover' is selected
        elif (
            not self.injuries[injury]["complication"]
            and get_clan_setting("rest and recover")
            and self.status.group_ID == CatGroup.PLAYER_CLAN_ID
            and self.injuries[injury]["duration"] + moons_prior - moons_with <= 0
        ):
            self.healed_condition = True
            return False

    def moon_skip_permanent_condition(self, condition):
        """handles the moon skip for permanent conditions"""
        if not self.is_disabled():
            return "skip"

        if self.permanent_condition[condition]["event_triggered"]:
            self.permanent_condition[condition]["event_triggered"] = False
            return "skip"

        mortality = self.permanent_condition[condition]["mortality"]
        moons_until = self.permanent_condition[condition]["moons_until"]
        born_with = self.permanent_condition[condition]["born_with"]

        # handling the countdown till a congenital condition is revealed
        if moons_until is not None and moons_until >= 0 and born_with is True:
            self.permanent_condition[condition]["moons_until"] = int(moons_until - 1)
            self.permanent_condition[condition]["moons_with"] = 0
            if self.permanent_condition[condition]["moons_until"] != -1:
                return "skip"
        if (
            self.permanent_condition[condition]["moons_until"] == -1
            and self.permanent_condition[condition]["born_with"] is True
        ):
            self.permanent_condition[condition]["moons_until"] = -2
            return "reveal"

        clan = self.status.fetch_clan_object()
        # leader should have a higher chance of death
        if self.status.is_leader and mortality != 0:
            mortality = int(mortality * 0.7)
            if mortality == 0:
                mortality = 1

        if mortality and not int(random() * mortality):
            if self.status.is_leader:
                clan.leader_lives -= 1
            self.die()
            return "died"
    
        if not mortality:
            return "continue"

    # ---------------------------------------------------------------------------- #
    #                                   relative                                   #
    # ---------------------------------------------------------------------------- #
    def get_parents(self):
        """Returns list containing parents of cat(id)."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        return self.inheritance.parents.keys()

    def get_siblings(self):
        """Returns list of the siblings(id)."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        return self.inheritance.siblings.keys()

    def get_children(self):
        """Returns list of the children (ids)."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        return self.inheritance.kits.keys()

    def is_grandparent(self, other_cat: Cat):
        """Check if the cat is the grandparent of the other cat."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        return other_cat.ID in self.inheritance.grand_kits.keys()

    def is_parent(self, other_cat: Cat):
        """Check if the cat is the parent of the other cat."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        return other_cat.ID in self.inheritance.kits.keys()

    def is_sibling(self, other_cat: Cat):
        """Check if the cats are siblings."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        return other_cat.ID in self.inheritance.siblings.keys()

    def is_littermate(self, other_cat: Cat):
        """Check if the cats are littermates."""
        if other_cat.ID not in self.inheritance.siblings.keys():
            return False
        litter_mates = [
            key
            for key, value in self.inheritance.siblings.items()
            if "litter mates" in value["additional"]
        ]
        return other_cat.ID in litter_mates

    def is_uncle_aunt(self, other_cat: Cat):
        """Check if the cats are related as uncle/aunt and niece/nephew."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        return other_cat.ID in self.inheritance.siblings_kits.keys()

    def is_cousin(self, other_cat: Cat):
        """Check if this cat and other_cat are cousins."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        return other_cat.ID in self.inheritance.cousins.keys()

    def is_related(self, other_cat, cousin_allowed):
        """Checks if the given cat is related to the current cat, according to the inheritance."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        if other_cat.ID in [self.parent1, self.parent2, self.parent3] + self.adoptive_parents and other_cat.ID not in self.inheritance.all_involved:
            print(f"Parent not in family tree all_involved list??? Current involved list: {self.inheritance.all_involved}")
        if cousin_allowed:
            return other_cat.ID in self.inheritance.all_but_cousins
        return other_cat.ID in self.inheritance.all_involved

    def get_relatives(self, cousin_allowed=True) -> list:
        """Returns a list of ids of all nearly related ancestors."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        if cousin_allowed:
            return self.inheritance.all_involved
        return self.inheritance.all_but_cousins

    # ---------------------------------------------------------------------------- #
    #                                  conditions                                  #
    # ---------------------------------------------------------------------------- #

    def get_ill(self, name, event_triggered=False, lethal=True, severity="default"):
        """Add an illness to this cat.

        :param name: name of the illness (str)
        :param event_triggered: Whether to have this illness skip `moon_skip_illness` for 1 moon, default `False` (bool)
        :param lethal: Allow lethality, default `True` (bool)
        :param severity: Override severity, default `'default'` (str, accepted values `'minor'`, `'major'`, `'severe'`)
        """
        if self.dead:
            return
        if name not in ILLNESSES:
            print(f"WARNING: {name} is not in the illnesses collection.")
            return
        if name == "kittencough" and self.status.rank != CatRank.KITTEN:
            return

        illness = ILLNESSES[name]
        mortality = illness["mortality"][self.age.value]
        med_mortality = illness["medicine_mortality"][self.age.value]
        illness_severity = illness["severity"] if severity == "default" else severity
        duration = illness["duration"]
        med_duration = illness["medicine_duration"]

        amount_per_med = get_amount_cat_for_one_medic()

        if medicine_cats_can_cover_clan(Cat.all_cats.values(), amount_per_med, self.status.group_ID):
            duration = med_duration
        if severity != "minor":
            duration += randrange(-1, 1)
        if duration == 0:
            duration = 1

        if game.clan and game.clan.game_mode == "cruel season" and mortality != 0:
            mortality = int(mortality * 0.5)
            med_mortality = int(med_mortality * 0.5)

            # to prevent an illness gets no mortality, check and set it to 1 if needed
            if mortality == 0 or med_mortality == 0:
                mortality = 1
                med_mortality = 1
        if lethal is False:
            mortality = 0

        new_illness = Illness(
            name=name,
            severity=illness_severity,
            mortality=mortality,
            infectiousness=illness["infectiousness"],
            duration=duration,
            medicine_duration=illness["medicine_duration"],
            medicine_mortality=med_mortality,
            risks=illness["risks"],
            event_triggered=event_triggered,
            clan=self.status.group_ID
        )

        if new_illness.name not in self.illnesses:
            self.illnesses[new_illness.name] = {
                "severity": new_illness.severity,
                "mortality": new_illness.current_mortality,
                "infectiousness": new_illness.infectiousness,
                "duration": new_illness.duration,
                "moon_start": game.clan.age if game.clan else 0,
                "risks": new_illness.risks,
                "event_triggered": new_illness.new,
            }
            self.pelt.rebuild_sprite = True

    def get_injured(self, name, event_triggered=False, lethal=True, severity="default"):
        """Add an injury to this cat.

        :param name: The injury to add
        :type name: str
        :param event_triggered: Whether to process healing immediately, defaults to False
        :type event_triggered: bool, optional
        :param lethal: _description_, defaults to True
        :type lethal: bool, optional
        :param severity: _description_, defaults to 'default'
        :type severity: str, optional
        """
        if self.dead:
            return

        if name not in INJURIES:
            print(f"WARNING: {name} is not in the injuries collection.")
            return

        if name == "mangled tail" and "NOTAIL" in self.pelt.scars:
            return
        if name == "torn ear" and "NOEAR" in self.pelt.scars:
            return

        injury = INJURIES[name]
        mortality = injury["mortality"][self.age.value]
        duration = injury["duration"]
        med_duration = injury["medicine_duration"]

        injury_severity = injury["severity"] if severity == "default" else severity
        if medicine_cats_can_cover_clan(
            Cat.all_cats.values(), get_amount_cat_for_one_medic(), self.status.group_ID
        ):
            duration = med_duration
        if severity != "minor":
            duration += randrange(-1, 1)
        if duration == 0:
            duration = 1

        if mortality != 0 and (game.clan and game.clan.game_mode == "cruel season"):
            mortality = int(mortality * 0.5)

            if mortality == 0:
                mortality = 1
        if lethal is False:
            mortality = 0

        new_injury = Injury(
            name=name,
            severity=injury_severity,
            duration=injury["duration"],
            medicine_duration=duration,
            mortality=mortality,
            risks=injury["risks"],
            illness_infectiousness=injury["illness_infectiousness"],
            also_got=injury["also_got"],
            cause_permanent=injury["cause_permanent"],
            event_triggered=event_triggered,
            clan=self.status.group_ID
        )

        if new_injury.name not in self.injuries:
            self.injuries[new_injury.name] = {
                "severity": new_injury.severity,
                "mortality": new_injury.current_mortality,
                "duration": new_injury.duration,
                "moon_start": game.clan.age if game.clan else 0,
                "illness_infectiousness": new_injury.illness_infectiousness,
                "risks": new_injury.risks,
                "complication": None,
                "cause_permanent": new_injury.cause_permanent,
                "event_triggered": new_injury.new,
            }
            
            self.pelt.rebuild_sprite = True

        if len(new_injury.also_got) > 0 and not int(random() * 5):
            avoided = False
            if (
                "blood loss" in new_injury.also_got
                and len(
                    find_alive_cats_with_rank(Cat, [CatRank.MEDICINE_CAT], working=True, clan=self.status.group_ID)
                )
                != 0
            ):
                clan_herbs = set(game.clan.herb_supply.entire_supply.keys())
                needed_herbs = {"horsetail", "raspberry", "marigold", "cobwebs"}
                usable_herbs = list(needed_herbs.intersection(clan_herbs))

                if usable_herbs and self.status.group_ID == CatGroup.PLAYER_CLAN_ID:
                    # deplete the herb
                    herb_used = choice(usable_herbs)
                    game.clan.herb_supply.remove_herb(herb_used, -1)
                    avoided = True
                    text = i18n.t("screens.med_den.blood_loss", name=self.name)
                    game.herb_events_list.append(text)

            if not avoided:
                self.also_got = True
                additional_injury = choice(new_injury.also_got)
                if additional_injury in INJURIES:
                    self.additional_injury(additional_injury)
                else:
                    self.get_ill(additional_injury, event_triggered=True)
        else:
            self.also_got = False

    def additional_injury(self, injury):
        self.get_injured(injury, event_triggered=True)

    def congenital_condition(self, cat):
        possible_conditions = []

        for condition in PERMANENT:
            possible = PERMANENT[condition]
            if possible["congenital"] in ('always', 'sometimes') and condition not in ('albinism', 'ocular albinism', "flat nose", 'manx syndrome', 'rabbit gait', "fully hairless", "partially hairless", "bad back", "narrowed chest", "bumpy skin"):
                possible_conditions.append(condition)

        new_condition = choice(possible_conditions)

        if new_condition == "born without a leg":
            cat.pelt.scars.append("NOPAW")
        elif new_condition == "born without a tail":
            cat.pelt.scars.append("NOTAIL")

        self.get_permanent_condition(new_condition, born_with=True)

    def get_permanent_condition(self, name, born_with=False, event_triggered=False, genetic=False, custom_reveal=None):
        if self.dead:
            return
        with open(f"resources/dicts/conditions/permanent_conditions.json", 'r') as read_file:
            PERMANENT = ujson.loads(read_file.read())
        if name not in PERMANENT:
            print(
                self.name if self.name else "[new cat]",
                f"WARNING: {name} is not in the permanent conditions collection.",
            )
            return
        
        if not genetic and name in ["manx syndrome", "flat nose", "rabbit gait", "albinism", "ocular albinism", 'fully hairless', 'partially hairless', "bad back", "narrowed chest", "bumpy skin"]:
            return
        if "blind" in self.permanent_condition and name == "failing eyesight":
            return
        if "deaf" in self.permanent_condition and name in ["partial hearing loss", "partial hearing loss in one ear", "deaf in one ear"]:
            return
        if "partial hearing loss" in self.permanent_condition and name in ["partial hearing loss in one ear"]:
            return
        if "deaf in one ear" in self.permanent_condition and name in ["partial hearing loss in one ear"]:
            return

        # remove accessories if need be
        if "NOTAIL" in self.pelt.scars or "HALFTAIL" in self.pelt.scars or (self.phenotype.bobtailnr > 0 and self.phenotype.bobtailnr < 5):
            self.pelt.accessory = [
                acc
                for acc in self.pelt.accessory
                if acc
                not in (
                    "RED FEATHERS",
                    "BLUE FEATHERS",
                    "JAY FEATHERS",
                    "GULL FEATHERS",
                    "SPARROW FEATHERS",
                    "CLOVER",
                    "DAISY",
                    "WISTERIA",
                    "GOLDEN CREEPING JENNY",
                )
            ]

        condition = PERMANENT[name]
        new_condition = False
        mortality = condition["mortality"][self.age.value]
        if mortality != 0 and (game.clan and game.clan.game_mode == "cruel season"):
            mortality = int(mortality * 0.65)

        if condition["congenital"] == "always":
            born_with = True
        moons_until = condition["moons_until"]
        if born_with and moons_until != 0:
            moons_until = randint(
                moons_until - 1, moons_until + 1
            )  # creating a range in which a condition can present
            moons_until = max(moons_until, 0)

        if born_with and not self.status.rank.is_baby():
            moons_until = -2
        elif born_with is False:
            moons_until = 0

        if name == 'partially hairless' and self.phenotype.length != 'fur-pointed':
            moons_until = 11 - self.moons
        if custom_reveal:
            moons_until = custom_reveal - self.moons
        if moons_until < -2:
            moons_until = -2

        if name == "paralyzed":
            self.pelt.paralyzed = True

        new_perm_condition = PermanentCondition(
            name=name,
            severity=condition["severity"],
            congenital=condition["congenital"],
            moons_until=moons_until,
            mortality=mortality,
            risks=condition["risks"],
            illness_infectiousness=condition["illness_infectiousness"],
            event_triggered=event_triggered,
        )

        if new_perm_condition.name not in self.permanent_condition:
            self.permanent_condition[new_perm_condition.name] = {
                "severity": new_perm_condition.severity,
                "born_with": born_with,
                "moons_until": new_perm_condition.moons_until,
                "moon_start": game.clan.age if game.clan else 0,
                "mortality": new_perm_condition.current_mortality,
                "illness_infectiousness": new_perm_condition.illness_infectiousness,
                "risks": new_perm_condition.risks,
                "complication": None,
                "event_triggered": new_perm_condition.new,
            }
            new_condition = True
        return new_condition

    def not_working(self):
        """returns True if the cat cannot work, False if the cat can work"""
        for illness in self.illnesses:
            if self.illnesses[illness]["severity"] != "minor":
                return True
        return any(
            self.injuries[injury]["severity"] != "minor" for injury in self.injuries
        )

    def not_work_because_hunger(self):
        """returns True if the only condition, why the cat cannot work is because of starvation"""
        non_minor_injuries = [
            injury
            for injury in self.injuries
            if self.injuries[injury]["severity"] != "minor"
        ]
        if len(non_minor_injuries) > 0:
            return False
        non_minor_illnesses = [
            illness
            for illness in self.illnesses
            if self.illnesses[illness]["severity"] != "minor"
        ]
        return "starving" in non_minor_illnesses and len(non_minor_illnesses) == 1

    def retire_cat(self):
        """This is only for cats that retire due to health condition"""
        # There are some special tasks we need to do for apprentice
        # Note that although you can un-retire cats, they will be a full warrior/med_cat/mediator
        if self.moons > 6 and self.status.rank.is_any_apprentice_rank():
            _ment = Cat.fetch_cat(self.mentor) if self.mentor else None
            self.rank_change(
                CatRank.WARRIOR
            )  # Temp switch them to warrior, so the following step will work
            self.rank_change_traits_skill(_ment)

        self.rank_change(CatRank.ELDER)
        return

    def is_ill(self):
        """Returns true if the cat is ill."""
        return len(self.illnesses) > 0

    def is_injured(self):
        """Returns true if the cat is injured."""
        return len(self.injuries) > 0

    def is_disabled(self):
        """Returns true if the cat have permanent condition"""
        return len(self.permanent_condition) > 0

    def available_to_work(self):
        return self.status.alive_in_player_clan and not self.not_working()

    def contact_with_ill_cat(self, cat: Cat):
        """handles if one cat had contact with an ill cat"""

        infectious_illnesses = []
        if self.is_ill() or cat is None or not cat.is_ill():
            return
        elif cat.is_ill():
            for illness in cat.illnesses:
                if cat.illnesses[illness]["infectiousness"] != 0:
                    infectious_illnesses.append(illness)
            if len(infectious_illnesses) == 0:
                return

        for illness in infectious_illnesses:
            illness_name = illness
            rate = cat.illnesses[illness]["infectiousness"]
            if self.is_injured():
                for y in self.injuries:
                    illness_infect = list(
                        filter(
                            lambda ill: ill["name"] == illness_name,
                            self.injuries[y]["illness_infectiousness"],
                        )
                    )
                    if illness_infect is not None and len(illness_infect) > 0:
                        illness_infect = illness_infect[0]
                        rate -= illness_infect["lower_by"]

                    # prevent rate lower 0 and print warning message
                    if rate < 0:
                        print(
                            f"WARNING: injury {self.injuries[y]['name']} has lowered \
                            chance of {illness_name} infection to {rate}"
                        )
                        rate = 1

            if not random() * rate:
                text = f"{self.name} had contact with {cat.name} and now has {illness_name}."
                # game.health_events_list.append(text)
                game.cur_events_list.append(
                    Single_Event(text, "health", cat_dict={"m_c": self}, clan=game.clan.group_ID)
                )
                self.get_ill(illness_name)

    def save_condition(self):
        # save conditions for each cat
        clanname = None
        if switch_get_value(Switch.clan_name) != "":
            clanname = switch_get_value(Switch.clan_name)
        elif len(switch_get_value(Switch.clan_list)) > 0:
            clanname = switch_get_value(Switch.clan_list)[0]
        elif game.clan is not None:
            clanname = game.clan.displayname

        condition_directory = get_save_dir() + "/" + clanname + "/conditions"
        condition_file_path = condition_directory + "/" + self.ID + "_conditions.json"

        if (
            (not self.is_ill() and not self.is_injured() and not self.is_disabled())
            or self.dead
        ):
            if os.path.exists(condition_file_path):
                os.remove(condition_file_path)
            return

        conditions = {}

        if self.is_ill():
            conditions["illnesses"] = self.illnesses

        if self.is_injured():
            conditions["injuries"] = self.injuries

        if self.is_disabled():
            conditions["permanent conditions"] = self.permanent_condition

        safe_save(condition_file_path, conditions)

    def load_conditions(self):
        if switch_get_value(Switch.clan_name) != "":
            clanname = switch_get_value(Switch.clan_name)
        else:
            clanname = switch_get_value(Switch.clan_list)[0]

        condition_directory = get_save_dir() + "/" + clanname + "/conditions/"
        condition_cat_directory = condition_directory + self.ID + "_conditions.json"
        if not os.path.exists(condition_cat_directory):
            return

        try:
            with open(condition_cat_directory, "r", encoding="utf-8") as read_file:
                rel_data = ujson.loads(read_file.read())
                self.illnesses = rel_data.get("illnesses", {})
                self.injuries = rel_data.get("injuries", {})
                self.permanent_condition = rel_data.get("permanent conditions", {})

            if "paralyzed" in self.permanent_condition and not self.pelt.paralyzed:
                self.pelt.paralyzed = True
            if "infertility" in self.permanent_condition:
                self.permanent_condition["sterile"] = self.permanent_condition["infertility"]
                del self.permanent_condition["infertility"]

        except Exception as e:
            print(
                f"WARNING: There was an error reading the condition file of cat #{self}.\n",
                e,
            )

    # ---------------------------------------------------------------------------- #
    #                                    mentor                                    #
    # ---------------------------------------------------------------------------- #

    def is_valid_mentor(self, potential_mentor: Cat):
        # If not an app, don't need a mentor
        if not self.status.rank.is_any_apprentice_rank():
            return False

        # App and mentor must be members of the same clan
        if self.status.group_ID != potential_mentor.status.group_ID:
            return False

        # Match jobs
        if (
            self.status.rank == CatRank.MEDICINE_APPRENTICE
            and potential_mentor.status.rank != CatRank.MEDICINE_CAT
        ):
            return False
        if (
            self.status.rank == CatRank.APPRENTICE
            and potential_mentor.status.rank
            not in [CatRank.LEADER, CatRank.DEPUTY, CatRank.WARRIOR]
        ):
            return False
        if (
            self.status.rank == CatRank.MEDIATOR_APPRENTICE
            and potential_mentor.status.rank != CatRank.MEDIATOR
        ):
            return False

        return True

    def __remove_mentor(self):
        """Should only be called by update_mentor, also sets fields on mentor."""
        if not self.mentor:
            return
        mentor_cat = Cat.fetch_cat(self.mentor)
        if not mentor_cat:
            return
        if self.ID in mentor_cat.apprentice:
            mentor_cat.apprentice.remove(self.ID)
        if self.moons > 5:
            if self.ID not in mentor_cat.former_apprentices:
                mentor_cat.former_apprentices.append(self.ID)
            if mentor_cat.ID not in self.former_mentor:
                self.former_mentor.append(mentor_cat.ID)
        self.mentor = None

    def __add_mentor(self, new_mentor_id: str):
        """Should only be called by update_mentor, also sets fields on mentor."""
        # reset patrol number
        self.patrol_with_mentor = 0
        self.mentor = new_mentor_id
        mentor_cat = Cat.fetch_cat(self.mentor)
        if not mentor_cat:
            return
        if self.ID not in mentor_cat.apprentice:
            mentor_cat.apprentice.append(self.ID)

    def update_mentor(self, new_mentor: Any = None):
        """Takes mentor's ID as argument, mentor could just be set via this function."""
        # No !!
        if isinstance(new_mentor, Cat):
            print("Everything is terrible!! (new_mentor {new_mentor} is a Cat D:)")
            return

        # Check if cat can have a mentor
        if (
            self.dead
            or self.status.is_outsider
            or not self.status.rank.is_any_apprentice_rank()
        ):
            self.__remove_mentor()
            return

        # If eligible, cat should get a mentor.
        if new_mentor:
            self.__remove_mentor()
            self.__add_mentor(new_mentor)

        # Check if current mentor is valid
        if self.mentor:
            mentor_cat = Cat.fetch_cat(
                self.mentor
            )  # This will return None if there is no current mentor
            if mentor_cat and not self.is_valid_mentor(mentor_cat):
                self.__remove_mentor()

        # Need to pick a random mentor if not specified
        if not self.mentor:
            potential_mentors = []
            priority_mentors = []
            for cat in self.all_cats.values():
                if self.is_valid_mentor(cat):
                    potential_mentors.append(cat)
                    if not cat.apprentice and not cat.not_working() and not cat.moons < 24:
                        priority_mentors.append(cat)
            # First try for a cat who currently has no apprentices and is working
            if priority_mentors:  # length of list > 0
                new_mentor = choice(priority_mentors)
            elif potential_mentors:  # length of list > 0
                new_mentor = choice(potential_mentors)
            if new_mentor:
                self.__add_mentor(new_mentor.ID)

    # ---------------------------------------------------------------------------- #
    #                                 relationships                                #
    # ---------------------------------------------------------------------------- #
    def is_potential_mate(
        self,
        other_cat: Cat,
        for_love_interest: bool = False,
        age_restriction: bool = True,
        first_cousin_mates: bool = False,
        ignore_no_mates: bool = False,
        outsider= False,
    ):
        """
        Checks if this cat is potential mate for the other cat.
        There are no restrictions if the current cat already has a mate or not (this allows poly-mates).
        """

        try:
            first_cousin_mates = get_clan_setting("first cousin mates")
        except:
            if "unittest" not in sys.modules:
                raise

        # just to be sure, check if it is not the same cat
        if self.ID == other_cat.ID:
            return False

        # check exiled, outside, and dead cats
        if (self.status.is_outsider and not outsider) or other_cat.status.is_outsider:
            return False

        # No Mates Check
        if not ignore_no_mates and (self.no_mates or other_cat.no_mates):
            return False

        # Inheritance check
        if self.is_related(other_cat, first_cousin_mates):
            return False

        # check dead cats
        if self.dead != other_cat.dead:
            return False

        # check for age
        if age_restriction:
            if (self.moons < 14 or other_cat.moons < 14) and not for_love_interest:
                return False

            # the +1 is necessary because both might not already be aged up
            # if only one is aged up at this point, later they are more moons apart than the setting defined
            # constants.CONFIG boolean "override_same_age_group" disables the same-age group check.
            if (
                constants.CONFIG["mates"].get("override_same_age_group", False)
                or self.age != other_cat.age
            ) and (
                abs(self.moons - other_cat.moons)
                > constants.CONFIG["mates"]["age_range"] + 1
            ):
                return False

        if (
            not self.age.can_have_mate() or not other_cat.age.can_have_mate()
        ) and self.age != other_cat.age:
            return False

        # check for mentor

        # Current mentor
        if other_cat.ID in self.apprentice or self.ID in other_cat.apprentice:
            return False

        # Former mentor
        is_former_mentor = (
            other_cat.ID in self.former_apprentices
            or self.ID in other_cat.former_apprentices
        )
        return bool(
            not is_former_mentor or get_clan_setting("romantic with former mentor")
        )

    def unset_mate(self, other_cat: Cat, breakup: bool = False, fight: bool = False):
        """Unset the mate from both self and other_cat"""
        if not other_cat:
            return

        # Both cats must have mates for this to work
        if len(self.mate) < 1 or len(other_cat.mate) < 1:
            return

        # AND they must be mates with each other.
        if self.ID not in other_cat.mate or other_cat.ID not in self.mate:
            print(
                f"Unsetting mates: These {self.name} and {other_cat.name} are not mates!"
            )
            return

        # If only deal with relationships if this is a breakup.
        if breakup:
            self_relationship = None
            if not self.dead:
                if other_cat.ID not in self.relationships:
                    self.create_one_relationship(other_cat)
                    self.relationships[other_cat.ID].mates = True
                self_relationship = self.relationships[other_cat.ID]
                self_relationship.romance -= randint(20, 60)
                self_relationship.comfort -= randint(10, 30)
                self_relationship.trust -= randint(5, 15)
                self_relationship.mates = False
                if fight:
                    self_relationship.romance -= randint(10, 30)
                    self_relationship.like -= randint(15, 45)

            if not other_cat.dead:
                if self.ID not in other_cat.relationships:
                    other_cat.create_one_relationship(self)
                    other_cat.relationships[self.ID].mates = True
                other_relationship = other_cat.relationships[self.ID]
                other_relationship.romance -= 40
                other_relationship.comfort -= 20
                other_relationship.trust -= 10
                other_relationship.mates = False
                if fight:
                    self_relationship.romance -= 20
                    other_relationship.like -= 30

        self.mate.remove(other_cat.ID)
        other_cat.mate.remove(self.ID)

        # Handle previous mates:
        if other_cat.ID not in self.previous_mates:
            self.previous_mates.append(other_cat.ID)
        if self.ID not in other_cat.previous_mates:
            other_cat.previous_mates.append(self.ID)

        if other_cat.inheritance:
            other_cat.inheritance.update_all_mates()
        if self.inheritance:
            self.inheritance.update_all_mates()

    def set_mate(self, other_cat: Cat):
        """Sets up a mate relationship between self and other_cat."""
        if other_cat.ID not in self.mate:
            self.mate.append(other_cat.ID)
        if self.ID not in other_cat.mate:
            other_cat.mate.append(self.ID)

        # If the current mate was in the previous mate list, remove them.
        if other_cat.ID in self.previous_mates:
            self.previous_mates.remove(other_cat.ID)
        if self.ID in other_cat.previous_mates:
            other_cat.previous_mates.remove(self.ID)

        if other_cat.inheritance:
            other_cat.inheritance.update_all_mates()
        if self.inheritance:
            self.inheritance.update_all_mates()

        # Set starting relationship values
        if not self.dead:
            if other_cat.ID not in self.relationships:
                self.create_one_relationship(other_cat)
                self.relationships[other_cat.ID].mates = True
            self_relationship = self.relationships[other_cat.ID]
            self_relationship.romance += 20
            self_relationship.comfort += 20
            self_relationship.trust += 10
            self_relationship.mates = True

        if not other_cat.dead:
            if self.ID not in other_cat.relationships:
                other_cat.create_one_relationship(self)
                other_cat.relationships[self.ID].mates = True
            other_relationship = other_cat.relationships[self.ID]
            other_relationship.romance += 20
            other_relationship.comfort += 20
            other_relationship.trust += 10
            other_relationship.mates = True

    def unset_adoptive_parent(self, other_cat: Cat):
        """Unset the adoptive parent from self"""
        self.adoptive_parents.remove(other_cat.ID)
        self.create_inheritance_new_cat()
        other_cat.create_inheritance_new_cat()
        if not self.dead:
            if other_cat.ID not in self.relationships:
                self.create_one_relationship(other_cat)
            self_relationship = self.relationships[other_cat.ID]
            self_relationship.like -= randint(10, 30)
            self_relationship.comfort -= randint(10, 30)
            self_relationship.trust -= randint(5, 15)

        if not other_cat.dead:
            if self.ID not in other_cat.relationships:
                other_cat.create_one_relationship(self)
            other_relationship = other_cat.relationships[self.ID]
            other_relationship.like -= 20
            other_relationship.comfort -= 20
            other_relationship.trust -= 10

    def set_adoptive_parent(self, other_cat: Cat):
        """Sets up a parent-child relationship between self and other_cat."""
        self.adoptive_parents.append(other_cat.ID)
        self.create_inheritance_new_cat()

        # Set starting relationship values
        if not self.dead:
            if other_cat.ID not in self.relationships:
                self.create_one_relationship(other_cat)
            self_relationship = self.relationships[other_cat.ID]
            self_relationship.like += 20
            self_relationship.comfort += 20
            self_relationship.trust += 10

        if not other_cat.dead:
            if self.ID not in other_cat.relationships:
                other_cat.create_one_relationship(self)
            other_relationship = other_cat.relationships[self.ID]
            other_relationship.like += 20
            other_relationship.comfort += 20
            other_relationship.trust += 10

    def create_inheritance_new_cat(self):
        """Creates the inheritance class for a new cat."""
        # set the born status to true, just for safety
        self.inheritance = Inheritance(self, True)

    def create_one_relationship(self, other_cat: Cat):
        """Create a new relationship between current cat and other cat. Returns: Relationship"""
        try:
            if not self.relationships:
                self.relationships = {}
        except:
            self.relationships = {}
        if other_cat.ID in self.relationships:
            return self.relationships[other_cat.ID]

        if other_cat.ID == self.ID:
            print(
                f"Attempted to create a relationship with self: {self.name}. Please report as a bug!"
            )
            return None

        self.relationships[other_cat.ID] = Relationship(self, other_cat)
        return self.relationships[other_cat.ID]

    def create_relationships_new_cat(self):
        """Create relationships for a new generated cat."""
        for inter_cat in Cat.all_cats.values():
            # the inter_cat is the same as the current cat
            if inter_cat.ID == self.ID:
                continue
            # if the cat already has (somehow) a relationship with the inter cat
            if inter_cat.ID in self.relationships or inter_cat.ID in self.blank_relations:
                continue
            # if they dead (dead cats have no relationships)
            if self.dead or inter_cat.dead:
                continue
            # if they are not within the same group
            if self.status.group_ID != inter_cat.status.group_ID:
                continue
            inter_cat.blank_relations.append(self.ID)
            self.blank_relations.append(inter_cat.ID)

    def init_all_relationships(self):
        """Create Relationships to all current Clancats."""
        blanks = []
        for ID in self.all_cats:
            the_cat = self.all_cats.get(ID)
            if the_cat.ID is not self.ID:
                mates = the_cat.ID in self.mate
                are_parents = False
                parents = False
                siblings = False

                if (
                    self.parent1 is not None
                    and self.parent2 is not None
                    and the_cat.parent1 is not None
                    and the_cat.parent2 is not None
                ):
                    are_parents = the_cat.ID in (self.parent1, self.parent2)
                    parents = are_parents or self.ID in (
                        the_cat.parent1,
                        the_cat.parent2,
                    )
                    siblings = self.parent1 in (
                        the_cat.parent1,
                        the_cat.parent2,
                    ) or self.parent2 in (the_cat.parent1, the_cat.parent2)

                related = parents or siblings

                # set the different stats
                romance = 0
                like = 0
                respect = 0
                comfort = 0
                trust = 0
                if game_setting_get("random relation"):
                    if (
                        game.clan
                        and the_cat in [game.clan.instructor] + [clan.instructor for clan in game.clan.all_other_clans if clan.instructor]
                        and the_cat.dead_for >= self.moons
                    ):
                        pass
                    elif (
                        game.clan
                        and the_cat in [game.clan.instructor] + [clan.instructor for clan in game.clan.all_other_clans if clan.instructor]
                        and the_cat.status.get_last_living_group() != self.status.group_ID
                    ):
                        pass
                    elif (randint(1, 20) == 1 or (self.status.group_ID != the_cat.status.group_ID and random() < 0.8)) and romance < 1:
                        like += randint(-25, 5)
                        respect += randint(-10, 15)
                        trust += randint(-15, 5)
                        comfort += randint(-15, 10)
                    else:
                        like += randint(-10, 35)
                        respect += randint(-10, 25)
                        trust += randint(-5, 15)
                        comfort += randint(-5, 15)
                        if (
                            randint(1, 100 - like) == 1
                            and self.moons > 11
                            and the_cat.moons > 11
                            and self.age == the_cat.age
                        ):
                            romance += randint(15, 30)
                            comfort = int(comfort * 1.3)
                            trust = int(trust * 1.2)

                if are_parents and like < 60:
                    like = 60
                if siblings and like < 30:
                    like = 30

                rel = Relationship(
                    cat_from=self,
                    cat_to=the_cat,
                    mates=mates,
                    family=related,
                    romance=romance,
                    like=like,
                    respect=respect,
                    comfort=comfort,
                    trust=trust,
                )
                if not (not mates and not related and romance == 0 and like == 0 and respect == 0 and comfort == 0 and trust == 0):
                    self.relationships[the_cat.ID] = rel
                else:
                    blanks.append(the_cat.ID)
        
        self.blank_relations = list(set(blanks))

    def save_relationship_of_cat(self, relationship_dir):
        # save relationships for each cat

        rel = []
        for r in self.relationships.values():
            rel.append(r.to_dict())

        safe_save(f"{relationship_dir}/{self.ID}_relations.json", rel)

    def load_relationship_of_cat(self):
        if switch_get_value(Switch.clan_name) != "":
            clanname = switch_get_value(Switch.clan_name)
        else:
            clanname = switch_get_value(Switch.clan_list)[0]

        relation_directory = get_save_dir() + "/" + clanname + "/relationships/"
        relation_cat_directory = relation_directory + self.ID + "_relations.json"

        self.relationships = {}
        if os.path.exists(relation_directory):
            if not os.path.exists(relation_cat_directory):
                self.init_all_relationships()
                return
            try:
                with open(relation_cat_directory, "r", encoding="utf-8") as read_file:
                    rel_data = ujson.loads(read_file.read())

                    for rel in rel_data:
                        if isinstance(rel.get('blanks', False), list):
                            self.blank_relations = rel['blanks']
                            continue
                        cat_to = self.all_cats.get(rel["cat_to_id"])
                        if cat_to is None or rel["cat_to_id"] == self.ID:
                            continue

                        # converting old saves
                        if "platonic_like" in rel:
                            # romance
                            rel["romance"] = rel["romantic_love"]
                            rel.pop("romantic_love")
                            # like
                            rel["like"] = rel["platonic_like"] - rel["dislike"]
                            rel.pop("platonic_like")
                            rel.pop("dislike")
                            # respect
                            rel["respect"] = rel["admiration"] - rel["jealousy"]
                            rel.pop("admiration")
                            rel.pop("jealousy")
                            # comfort
                            rel["comfort"] = rel["comfortable"]
                            rel.pop("comfortable")

                        # create relationship
                        new_rel = Relationship(
                            cat_from=self,
                            cat_to=cat_to,
                            mates=rel["mates"] or False,
                            family=rel["family"] or False,
                            romance=(rel["romance"] or 0),
                            like=(rel["like"] or 0),
                            respect=rel["respect"] or 0,
                            comfort=rel["comfort"] or 0,
                            trust=rel["trust"] or 0,
                            log=rel["log"],
                        )
                        if not (not new_rel.mates and not new_rel.family and new_rel.romance == 0 and new_rel.like == 0 
                        and new_rel.respect == 0 and new_rel.comfort == 0 and new_rel.trust == 0 and len(new_rel.log) == 0):
                            self.relationships[rel["cat_to_id"]] = new_rel
                        else:
                            self.blank_relations.append(rel["cat_to_id"])
            except Exception as e:
                print(e)
                print(
                    f"WARNING: There was an error reading the relationship file of cat #{self}."
                )

    @staticmethod
    def mediate_relationship(mediator, cat1, cat2, allow_romantic, sabotage=False):
        # Gather some important info

        # Gathering the relationships.
        if cat2.ID in cat1.relationships:
            rel1 = cat1.relationships[cat2.ID]
        else:
            rel1 = cat1.create_one_relationship(cat2)

        if cat1.ID in cat2.relationships:
            rel2 = cat2.relationships[cat1.ID]
        else:
            rel2 = cat2.create_one_relationship(cat1)

        # Output string.
        output = ""

        # Determine the chance of failure.
        if mediator.experience_level == "untrained":
            chance = 15
        elif mediator.experience_level == "trainee":
            # Negative bonus for very low.
            chance = 20
        elif mediator.experience_level == "prepared":
            chance = 35
        elif mediator.experience_level == "proficient":
            chance = 55
        elif mediator.experience_level == "expert":
            chance = 70
        elif mediator.experience_level == "master":
            chance = 100
        else:
            chance = 40

        compat = get_personality_compatibility(cat1, cat2)
        if compat is True:
            chance += 10
        elif compat is False:
            chance -= 5

        # Cat's compatibility with mediator also has an effect on success chance.
        for cat in (cat1, cat2):
            if get_personality_compatibility(cat, mediator) is True:
                chance += 5
            elif get_personality_compatibility(cat, mediator) is False:
                chance -= 5

        # Determine chance to fail, turning sabotage into mediate and mediate into sabotage
        if not int(random() * chance):
            apply_bonus = False
            if sabotage:
                output += "Sabotage Failed!\n"
                sabotage = False
            else:
                output += "Mediate Failed!\n"
                sabotage = True
        else:
            apply_bonus = True
            # EX gain on success
            if mediator.status.rank == CatRank.MEDIATOR:
                exp_gain = randint(10, 24)

                gm_modifier = 1
                if game.clan and game.clan.game_mode == "expanded":
                    gm_modifier = 3
                elif game.clan and game.clan.game_mode == "cruel season":
                    gm_modifier = 6

                if mediator.experience_level == "proficient":
                    lvl_modifier = 1.25
                elif mediator.experience_level == "expert":
                    lvl_modifier = 1.75
                elif mediator.experience_level == "master":
                    lvl_modifier = 2
                else:
                    lvl_modifier = 1
                mediator.experience += exp_gain / lvl_modifier / gm_modifier

        if mediator.status.rank == CatRank.MEDIATOR_APPRENTICE:
            mediator.experience += max(randint(1, 6), 1)

        # determine the traits to effect
        # Are they mates?
        mates = rel1.cat_from.ID in rel1.cat_to.mate

        rel_values = [v for v in [*RelType] if v != RelType.ROMANCE]
        if allow_romantic and (mates or cat1.is_potential_mate(cat2)):
            rel_values.append(RelType.ROMANCE)

        # Determine the number of traits to effect, and choose the traits
        chosen_rel = sample(rel_values, k=randint(2, len(rel_values)))

        if compat is True:
            personality_bonus = 2
        elif compat is False:
            personality_bonus = -2
        else:
            personality_bonus = 0

        # Effects on traits
        for rel_type in chosen_rel:
            # The EX bonus in not applied upon a fail.
            if apply_bonus:
                if mediator.experience_level == "very low":
                    # Negative bonus for very low.
                    bonus = randint(-2, -1)
                elif mediator.experience_level == "low":
                    bonus = randint(-2, 0)
                elif mediator.experience_level == "high":
                    bonus = randint(1, 3)
                elif mediator.experience_level == "master":
                    bonus = randint(3, 4)
                elif mediator.experience_level == "max":
                    bonus = randint(4, 5)
                else:
                    bonus = 0  # Average gets no bonus.
            else:
                bonus = 0

            ran = (5, 10) if rel_type == RelType.ROMANCE and mates else (4, 6)

            amount = ((randint(ran[0], ran[1]) + bonus) + personality_bonus) * (
                -1 if sabotage else 1
            )

            setattr(rel1, rel_type, getattr(rel1, rel_type) + amount)
            setattr(rel2, rel_type, getattr(rel2, rel_type) + amount)

            output += i18n.t(
                f"screens.mediation.output_{'decrease' if sabotage else 'increase'}",
                trait=i18n.t(f"screens.mediation.{rel_type}"),
            )

        return output

    def set_faded(self):
        """This function is for cats that are faded. It will set the sprite and the faded tag"""
        self.faded = True

        # Silhouette sprite
        if self.age == CatAge.NEWBORN:
            file_name = "faded_newborn"
        elif self.age == CatAge.KITTEN:
            file_name = "faded_kitten"
        elif self.age in [
            CatAge.ADULT,
            CatAge.YOUNG_ADULT,
            CatAge.SENIOR_ADULT,
        ]:
            file_name = "faded_adult"
        elif self.age == CatAge.ADOLESCENT:
            file_name = "faded_adol"
        else:
            file_name = "faded_senior"

        if self.status.group == CatGroup.DARK_FOREST:
            file_name += "_df"
        elif self.status.group == CatGroup.UNKNOWN_RESIDENCE:
            file_name += "_ur"

        file_name += ".png"

        self.sprite = image_cache.load_image(
            f"sprites/faded/{file_name}"
        ).convert_alpha()

    @staticmethod
    def fetch_cat(ID: str):
        """Fetches a cat object. Works for both faded and non-faded cats. Returns none if no cat was found."""
        if not ID or isinstance(ID, Cat):  # Check if argument is None or Cat.
            return ID
        elif not isinstance(ID, str):  # Invalid type
            return None
        if ID in Cat.all_cats:
            cat = Cat.all_cats[ID]
            return cat
        else:
            return ob if (ob := Cat.load_faded_cat(ID)) else None

    @staticmethod
    def load_faded_cat(cat: str):
        """Loads a faded cat, returning the cat object. This object is saved nowhere else."""

        # just preventing any attempts to load something that isn't a cat ID
        if not cat.isdigit():
            return

        try:
            # todo: why can't this be `get_switch(Switch.clan_name)`?
            clan = (
                switch_get_value(Switch.clan_list)[0]
                if game.clan is None
                else game.clan.displayname
            )

            with open(
                get_save_dir() + "/" + game.clan.displayname + "/faded_cats/" + cat + ".json",
                "r",
                encoding="utf-8",
            ) as read_file:
                cat_info = ujson.loads(read_file.read())
                # If loading cats is attempted before the Clan is loaded, we would need to use this.

        except (
            AttributeError
        ):  # NOPE, cats are always loaded before the Clan, so doesn't make sense to throw an error
            with open(
                get_save_dir()
                + "/"
                + switch_get_value(Switch.clan_list)[0]
                + "/faded_cats/"
                + cat
                + ".json",
                "r",
                encoding="utf-8",
            ) as read_file:
                cat_info = ujson.loads(read_file.read())
        except:
            print("ERROR: in loading faded cat")
            return False

        if isinstance(cat_info["status"], str):
            status_dict = {"rank": cat_info["status"]}
        else:
            status_dict = cat_info["status"]

        cat_ob = Cat(
            ID=cat_info["ID"],
            prefix=cat_info["name_prefix"],
            suffix=cat_info["name_suffix"],
            status_dict=status_dict,
            moons=cat_info["moons"],
            faded=True,
        )
        if cat_info["parent1"]:
            cat_ob.parent1 = cat_info["parent1"]
        if cat_info["parent2"]:
            cat_ob.parent2 = cat_info["parent2"]
        if cat_info.get("parent3"):
            cat_ob.parent3 = cat_info["parent3"]
        cat_ob.faded_offspring = cat_info["faded_offspring"]
        cat_ob.adoptive_parents = (
            cat_info["adoptive_parents"] if "adoptive_parents" in cat_info else []
        )
        cat_ob.faded = True

        if cat_info.get("df"):
            cat_ob.status.send_to_afterlife(target_ID=CatGroup.DARK_FOREST_ID)
        elif isinstance(cat_info["status"], str):
            cat_ob.status.send_to_afterlife(target_ID=CatGroup.STARCLAN_ID)

        cat_ob.dead_for = cat_info["dead_for"] if "dead_for" in cat_info else 1
        return cat_ob

    # ---------------------------------------------------------------------------- #
    #                                  Sorting                                     #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def sort_cats(given_list=None):
        # disable unnecessary lambda in this function
        # pylint: disable=unnecessary-lambda
        if given_list is None:
            given_list = []
        if not given_list:
            given_list = Cat.all_cats_list
        sort_type = switch_get_value(Switch.sort_type)
        if sort_type == "age":
            given_list.sort(key=lambda x: Cat.get_adjusted_age(x))
        elif sort_type == "reverse_age":
            given_list.sort(key=lambda x: Cat.get_adjusted_age(x), reverse=True)
        elif sort_type == "id":
            given_list.sort(key=lambda x: int(x.ID))
        elif sort_type == "reverse_id":
            given_list.sort(key=lambda x: int(x.ID), reverse=True)
        elif sort_type == "rank":
            given_list.sort(
                key=lambda x: (Cat.rank_order(x), Cat.get_adjusted_age(x)), reverse=True
            )
        elif sort_type == "exp":
            given_list.sort(key=lambda x: x.experience, reverse=True)
        elif sort_type == "death":
            given_list.sort(key=lambda x: -1 * int(x.dead_for))
        elif sort_type == "clan":
            given_list.sort(key=lambda x: (int(x.status.get_last_living_group())*-1 if x.status.get_last_living_group() else 0, 
                                            Cat.rank_order(x), Cat.get_adjusted_age(x)), reverse=True)

        return

    @staticmethod
    def insert_cat(c: Cat):
        sort_type = switch_get_value(Switch.sort_type)
        try:
            if sort_type == "age":
                bisect.insort(
                    Cat.all_cats_list, c, key=lambda x: Cat.get_adjusted_age(x)
                )
            elif sort_type == "reverse_age":
                bisect.insort(
                    Cat.all_cats_list, c, key=lambda x: -1 * Cat.get_adjusted_age(x)
                )
            elif sort_type == "rank":
                bisect.insort(
                    Cat.all_cats_list,
                    c,
                    key=lambda x: (
                        -1 * Cat.rank_order(x),
                        -1 * Cat.get_adjusted_age(x),
                    ),
                )
            elif sort_type == "exp":
                bisect.insort(Cat.all_cats_list, c, key=lambda x: x.experience)
            elif sort_type == "id":
                bisect.insort(Cat.all_cats_list, c, key=lambda x: int(x.ID))
            elif sort_type == "reverse_id":
                bisect.insort(Cat.all_cats_list, c, key=lambda x: -1 * int(x.ID))
            elif sort_type == "death":
                bisect.insort(Cat.all_cats_list, c, key=lambda x: -1 * int(x.dead_for))
        except (TypeError, NameError):
            # If you are using python 3.8, key is not a supported parameter into insort. Therefore, we'll need to
            # do the slower option of adding the cat, then resorting
            Cat.all_cats_list.append(c)
            Cat.sort_cats()

    @staticmethod
    def rank_order(cat: Cat):
        if cat.status.rank in Cat.rank_sort_order:
            return Cat.rank_sort_order.index(cat.status.rank)
        else:
            return 0

    @staticmethod
    def get_adjusted_age(cat: Cat):
        """Returns the moons + dead_for moons rather than the moons at death for dead cats, so dead cats are sorted by
        total age, rather than age at death"""
        if cat.dead:
            if constants.CONFIG["sorting"]["sort_rank_by_death"]:
                if switch_get_value(Switch.sort_type) == "rank":
                    return cat.dead_for
                else:
                    if constants.CONFIG["sorting"]["sort_dead_by_total_age"]:
                        return cat.dead_for + cat.moons
                    else:
                        return cat.moons
            else:
                if constants.CONFIG["sorting"]["sort_dead_by_total_age"]:
                    return cat.dead_for + cat.moons
                else:
                    return cat.moons
        else:
            return cat.moons

    # ---------------------------------------------------------------------------- #
    #                                  properties                                  #
    # ---------------------------------------------------------------------------- #

    @property
    def experience(self):
        return self._experience

    @experience.setter
    def experience(self, exp: int):
        exp = min(exp, self.experience_levels_range["master"][1])
        self._experience = int(exp)

        for x in self.experience_levels_range:
            if (
                self.experience_levels_range[x][0]
                <= exp
                <= self.experience_levels_range[x][1]
            ):
                self.experience_level = x
                break

    @property
    def moons(self):
        return self._moons

    @moons.setter
    def moons(self, value: int):
        self._moons = value

        updated_age = False
        for key_age in self.age_moons.keys():            
            if key_age == "senior" and value > self.age_moons[key_age][1] + 1:
                self.age = "senior"
            if self._moons in range(
                self.age_moons[key_age][0], self.age_moons[key_age][1] + 1
            ):
                updated_age = True
                self.age = key_age
        try:
            if not updated_age and self.age is not None:
                self.age = CatAge.SENIOR
        except AttributeError:
            print(f"ERROR: cat has no age attribute! Cat ID: {self.ID}")

    @property
    def sprite(self):
        if self.faded:
            return self._sprite

        # Update the sprite
        if hasattr(self, "pelt") and self.pelt.rebuild_sprite:
            self.pelt.rebuild_sprite = False
            self._sprite_working = self.not_working()
            update_sprite(self)
            update_mask(self)
        return self._sprite

    @sprite.setter
    def sprite(self, new_sprite):
        self._sprite = new_sprite

    @property
    def sprite_mask(self):
        if (
            scripts.game_structure.screen_settings.screen_scale
            != self.pelt.screen_scale
        ):
            self.pelt.screen_scale = scripts.game_structure.screen_settings.screen_scale
            update_mask(self)
        return self._sprite_mask

    @sprite_mask.setter
    def sprite_mask(self, val):
        self._sprite_mask = val

    # ---------------------------------------------------------------------------- #
    #                                  other                                       #
    # ---------------------------------------------------------------------------- #

    def get_info_block(self, *, make_clan=False, patrol=False, relationship=False):
        if make_clan:
            return "\n".join(
                [
                    self.genderalign,
                    i18n.t(
                        (
                            f"general.{self.age}"
                            if self.age != "kitten"
                            else "general.kitten_profile"
                        ),
                        count=1,
                    ),
                    i18n.t(f"cat.personality.{self.personality.trait}"),
                    self.skills.skill_string(),
                ]
            )
        elif patrol:
            return "<br>".join(
                [
                    i18n.t(f"general.{self.status.rank.lower()}", count=1),
                    i18n.t(f"cat.personality.{self.personality.trait}"),
                    self.skills.skill_string(short=True),
                    i18n.t(f"cat.skills.{self.experience_level}")
                    + (
                        f" ({str(self.experience)})\n"
                        if get_clan_setting("showxp")
                        else "\n"
                    ),
                ]
            )
        elif relationship:
            return " - ".join(
                [
                    i18n.t("general.moons_age", count=self.moons),
                    self.genderalign,
                    i18n.t(f"cat.personality.{self.personality.trait}"),
                ]
            )

        return "\n".join(
            [
                i18n.t("general.moons_age", count=self.moons),
                i18n.t(f"general.{self.status.rank.lower()}", count=1),
                self.genderalign,
                i18n.t(f"cat.personality.{self.personality.trait}"),
                self.skills.skill_string(short=True),
            ]
        )

    def get_save_dict(self, faded=False):
        if faded:
            if self.inheritance:
                self.inheritance.save_inheritance(True)
            return {
                "ID": self.ID,
                "name_prefix": self.name.prefix,
                "name_suffix": self.name.suffix,
                "status": self.status.get_status_dict(),
                "moons": self.moons,
                "dead_for": self.dead_for,
                "parent1": self.parent1,
                "parent2": self.parent2,
                "parent3": self.parent3 if self.parent3 else None,
                "adoptive_parents": self.adoptive_parents,
                "faded_offspring": self.faded_offspring,
            }
        else:
            if self.inheritance:
                self.inheritance.save_inheritance()
            return {
                "ID": self.ID,
                "name_prefix": self.name.prefix,
                "name_suffix": self.name.suffix,
                "specsuffix_hidden": self.name.specsuffix_hidden,
                "gender_align": self.genderalign,
                "pronouns": (
                    self._pronouns
                    if self._pronouns is not None
                    else {i18n.config.get("locale"): self.pronouns}
                ),
                "birth_cooldown": self.birth_cooldown,
                "status": self.status.get_status_dict(),
                "dark_forest_affinity": self.dark_forest_affinity,
                "starclan_affinity": self.starclan_affinity,
                "backstory": self.backstory or None,
                "moons": self.moons,
                "trait": self.personality.trait,
                "facets": self.personality.get_facet_string(),
                "parent1": self.parent1,
                "parent2": self.parent2,
                "parent3": self.parent3 if self.parent3 else None,
                "adoptive_parents": self.adoptive_parents,
                "mentor": self.mentor or None,
                "former_mentor": (
                    list(self.former_mentor) if self.former_mentor else []
                ),
                "patrol_with_mentor": (self.patrol_with_mentor or 0),
                "mate": self.mate,
                "previous_mates": self.previous_mates,
                "paralyzed": self.pelt.paralyzed,
                "no_kits": self.no_kits,
                "no_retire": self.no_retire,
                "no_mates": self.no_mates,
                "genotype": self.phenotype.toJSON(),
                "chimerageno": self.chimerapheno.toJSON() if self.chimerapheno else None,
                "chimera_pattern": self.chimerapheno.chimerapattern if self.chimerapheno else None,
                "passes_genotype" : self.passes,
                "white_pattern" : self.phenotype.white_pattern,
                "chim_white" : self.chimerapheno.white_pattern if self.chimerapheno else "No",
                "sprite_kitten": self.pelt.cat_sprites['kitten'],
                "sprite_adolescent": self.pelt.cat_sprites['adolescent'],
                "sprite_adult": self.pelt.cat_sprites['adult'],
                "sprite_senior": self.pelt.cat_sprites['senior'],
                "sprite_para_adult": self.pelt.cat_sprites['para_adult'],
                "reverse": self.pelt.reverse,
                "tint": self.pelt.tint,
                "white_tint": self.pelt.white_patches_tint,
                "skill_dict": self.skills.get_skill_dict(),
                "scars": self.pelt.scars or [],
                "accessory": self.pelt.accessory,
                "experience": self.experience,
                "dead_moons": self.dead_for,
                "current_apprentice": list(self.apprentice),
                "former_apprentices": list(self.former_apprentices),
                "faded_offspring": self.faded_offspring,
                "opacity": self.pelt.opacity,
                "prevent_fading": self.prevent_fading,
                "favourite": self.favourite,
            }

    def determine_next_and_previous_cats(
        self, filter_func: Callable[[Cat], bool] = None
    ):
        """Determines where the next and previous buttons point to, relative to this cat.

        :param filter_func: Allows you to constrain the list by any attribute of
            the Cat object. Takes a function which takes in a Cat instance and
            returns a boolean.
        """

        sorted_specific_list = [
            check_cat
            for check_cat in Cat.all_cats_list
            if check_cat.dead == self.dead
            and ( (game.clan.clancount == "singleclan" and check_cat.status.alive_in_player_clan == self.status.alive_in_player_clan)
                or (game.clan.clancount == "multiclan" and check_cat.status.is_outsider == self.status.is_outsider
                and (self.status.is_outsider or check_cat.status.group_ID == self.status.group_ID)))
            and not check_cat.faded
            and check_cat.status.is_near() == self.status.is_near()
        ]

        # we're doing this separately so that we don't fuck up other clan cats and cats with no group
        if self.dead:
            sorted_specific_list = [
                check_cat
                for check_cat in sorted_specific_list
                if check_cat.status.group_ID == self.status.group_ID
            ]

        if filter_func is not None:
            sorted_specific_list = [
                check_cat
                for check_cat in sorted_specific_list
                if filter_func(check_cat)
            ]

        all_instructors = [game.clan.instructor] + [clan.instructor for clan in game.clan.all_other_clans if clan.instructor]

        for ins in all_instructors[::-1]:
            if ins in sorted_specific_list:
                sorted_specific_list.remove(ins)
                sorted_specific_list.insert(0, ins)

        idx = sorted_specific_list.index(self)

        return (
            (
                sorted_specific_list[idx + 1].ID
                if len(sorted_specific_list) > idx + 1
                else 0
            ),
            sorted_specific_list[idx - 1].ID if idx - 1 >= 0 else 0,
        )


# ---------------------------------------------------------------------------- #
#                               END OF CAT CLASS                               #
# ---------------------------------------------------------------------------- #


# Creates a random cat
def create_cat(rank, moons=None, biome=None, kittypet=False):
    status_dict = {"rank": rank}

    new_cat = Cat(status_dict=status_dict, biome=biome, kittypet=kittypet)

    if moons is not None:
        new_cat.moons = moons
    elif new_cat.moons >= 160:
        new_cat.moons = randint(120, 155)
    elif new_cat.moons == 0:
        new_cat.moons = randint(1, 5)

    not_allowed_scars = [
        "NOPAW",
        "NOTAIL",
        "HALFTAIL",
        "NOEAR",
        "BOTHBLIND",
        "RIGHTBLIND",
        "LEFTBLIND",
        "BRIGHTHEART",
        "NOLEFTEAR",
        "NORIGHTEAR",
        "MANLEG",
    ]

    for scar in new_cat.pelt.scars:
        if scar in not_allowed_scars:
            new_cat.pelt.scars.remove(scar)

    return new_cat


# Twelve example cats
def create_example_cats():
    warrior_indices = sample(range(12), 3)

    for cat_index in range(12):
        if cat_index in warrior_indices:
            game.choose_cats[cat_index] = create_cat(rank=CatRank.WARRIOR, kittypet=constants.CONFIG["clan_creation"]["use_special_roller"])
        else:
            random_rank = choice(
                [
                    CatRank.KITTEN,
                    CatRank.APPRENTICE,
                    CatRank.WARRIOR,
                    CatRank.WARRIOR,
                    CatRank.ELDER,
                ]
            )
            game.choose_cats[cat_index] = create_cat(rank=random_rank, kittypet=constants.CONFIG["clan_creation"]["use_special_roller"])


def create_option_preview_cat(scar: str = None, acc: str = None):
    """
    Creates a cat with the specified scar
    """
    gene_config = constants.CONFIG['genetics_config']
    gene_config.update(constants.CONFIG['april_fools_genes'])
    pheno = Phenotype(gene_config, game_setting_get("ban problem genes"))
    pheno.Generator()
    new_cat = Cat(
        loading_cat=True,
        pelt=Pelt(
            phenotype=pheno.toJSON(),
            reverse=False,
            tint="gray",
            scars=[scar] if scar else [],
            adult_sprite=8,
            accessory=[acc] if acc else [],
        ),
    )
    new_cat.age = CatAge.ADULT

    return new_cat


# CAT CLASS ITEMS
cat_class = Cat(example=True)
game.cat_class = cat_class

# ---------------------------------------------------------------------------- #
#                                load json files                               #
# ---------------------------------------------------------------------------- #

resource_directory = "resources/dicts/conditions/"
with open(f"{resource_directory}illnesses.json", "r", encoding="utf-8") as read_file:
    ILLNESSES = ujson.loads(read_file.read())

with open(f"{resource_directory}injuries.json", "r", encoding="utf-8") as read_file:
    INJURIES = ujson.loads(read_file.read())

with open(
    f"{resource_directory}permanent_conditions.json", "r", encoding="utf-8"
) as read_file:
    PERMANENT = ujson.loads(read_file.read())

MINOR_MAJOR_REACTION: Optional[Dict] = None
grief_lang: Optional[str] = None


def load_grief_reactions():
    global MINOR_MAJOR_REACTION, grief_lang
    if grief_lang == i18n.config.get("locale"):
        return
    MINOR_MAJOR_REACTION = load_lang_resource(
        "events/death/death_reactions/minor_major.json"
    )
    grief_lang = i18n.config.get("locale")


load_grief_reactions()

LEAD_CEREMONY_SC: Optional[Dict] = None
LEAD_CEREMONY_DF: Optional[Dict] = None
lead_ceremony_lang = None


def load_leader_ceremonies():
    global LEAD_CEREMONY_SC, LEAD_CEREMONY_DF, lead_ceremony_lang
    if lead_ceremony_lang == i18n.config.get("locale"):
        return
    LEAD_CEREMONY_SC = load_lang_resource("events/lead_ceremony_sc.json")
    LEAD_CEREMONY_DF = load_lang_resource("events/lead_ceremony_df.json")
    lead_ceremony_lang = i18n.config.get("locale")


load_leader_ceremonies()

with open("resources/dicts/backstories.json", "r", encoding="utf-8") as read_file:
    BACKSTORIES = ujson.loads(read_file.read())
