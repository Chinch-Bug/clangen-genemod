from random import Random
from typing import Dict, Tuple, Optional, Union, List

import ujson

from scripts.cat.phenotype import Phenotype
from scripts.cat.cats import Cat
from scripts.cat.constants import BACKSTORIES
from scripts.cat.enums import CatAge, CatGroup, CatSocial
from scripts.cat.factories.base_factory import BaseCatFactory
from scripts.cat.factories.typed_dicts import (
    MentorshipDict,
    CatTogglesDict,
    GenderDict,
    InheritanceDict,
    AfterlifeAffinityDict,
)
from scripts.cat.history import History
from scripts.cat.names import Name
from scripts.cat.pelts import Pelt
from scripts.cat.personality import Personality
from scripts.cat.skills import CatSkills
from scripts.cat.status import Status
from scripts.config import get_config
from scripts.game_structure.game.settings import game_setting_get


class LoadCatFactory(BaseCatFactory):
    cat_id = None
    rng = Random()

    with open(
        f"resources/dicts/conversion_dict.json", "r", encoding="utf-8"
    ) as read_file:
        CONVERT = ujson.loads(read_file.read())

    @classmethod
    def create_cat(cls, **kwargs) -> Cat:
        """
        Takes a dict from save data & constructs the cat
        :param kwargs: save file dict
        :return:
        """
        if "ID" not in kwargs:
            raise KeyError("Cat ID missing!")
        cls.cat_id = kwargs["ID"]

        mate = kwargs.get("mate", [])
        inheritance = InheritanceDict(
            parent1=kwargs["parent1"],
            parent2=kwargs["parent2"],
            parent3=kwargs.get("parent3"),
            adoptive_parents=kwargs.get("adoptive_parents", []),
            surrogate_parents=kwargs.get("surrogate_parents", []),
            affair_parents=kwargs.get("affair_parents", []),
            faded_offspring=kwargs.get("faded_offspring", []),
            mate=mate if isinstance(mate, list) else [mate],
            previous_mates=kwargs.get("previous_mates", []),
        )

        mentorship = MentorshipDict(
            mentor=kwargs["mentor"],
            former_mentor=kwargs.get("former_mentor", []),
            patrol_with_mentor=kwargs.get("patrol_with_mentor", 0),
            apprentice=kwargs["current_apprentice"],
            former_apprentices=kwargs["former_apprentices"],
        )

        toggles = CatTogglesDict(
            no_kits=kwargs.get("no_kits", False),
            no_mates=kwargs.get("no_mates", False),
            no_retire=kwargs.get("no_retire", False),
            prevent_fading=kwargs.get("prevent_fading", False),
            favourite=kwargs.get("favourite", False),
        )

        status = cls._convert_status(
            kwargs.get("status"),
            kwargs.get("moons"),
            old_bools=[
                kwargs.get("dead"),
                kwargs.get("df"),
                kwargs.get("driven_out"),
                kwargs.get("exiled"),
                kwargs.get("outside"),
            ],
        )

        if kwargs.get("gender"):
            if kwargs["gender"] == 'female':
                kwargs["gender"] = 'fem'
            elif kwargs["gender"] == 'male':
                kwargs["gender"] = 'masc'
        phenotype, chimerapheno = cls._build_pheno(use_special=(status.social == CatSocial.KITTYPET), kwargs=kwargs)
        pelt = cls._build_pelt(phenotype=phenotype, kwargs=kwargs)

        gender = GenderDict(
            sex=phenotype.sex,
            genderalign=kwargs.get("gender_align"),
            pronouns=kwargs.get("pronouns")
        )
        

        backstory = cls._convert_backstory(kwargs.get("backstory"))
        skills, backstory = cls._convert_skill_and_backstory(
            kwargs.get("skill_dict"),
            kwargs.get("skill"),
            backstory,
            status.rank,
            CatAge.get_from_moons(kwargs["moons"]),
        )

        affinity = AfterlifeAffinityDict(
            starclan=kwargs.get("starclan_affinity", 0),
            dark_forest=kwargs.get("dark_forest_affinity", 0),
        )

        cat_params = {
            "ID": cls.cat_id,
            "gender_dict": gender,
            "phenotype": phenotype,
            "chimerapheno": chimerapheno,
            "passes": kwargs.get("passes", 1),
            "pelt": pelt,
            "moons": kwargs["moons"],
            "status": status,
            "backstory": backstory,
            "skills": skills,
            "personality": cls._build_personality(
                kwargs.get("facets"),
                kwargs["trait"],
                CatAge.get_from_moons(kwargs["moons"]).is_baby(),
            ),
            "mentorship": mentorship,
            "inheritance": inheritance,
            "affinity": affinity,
            "toggles": toggles,
            "experience": kwargs.get("experience"),
            "birth_cooldown": kwargs.get("birth_cooldown", 0),
            "specsuffix_hidden": kwargs.get("specsuffix_hidden", False),
        }

        cat = Cat(**cat_params)

        cat.genetic_conditions(True)

        # Unfortunately, these two have to be handled *after* the creation of the cat
        # because of the horrible nested cat. fixme.
        if "died_by" in kwargs or "scar_event" in kwargs:
            cat.history = cls._convert_history(
                kwargs.get("died_by", []), kwargs.get("scar_event", []), cat=cat
            )
        cat.name = Name(
            prefix=kwargs["name_prefix"],
            suffix=kwargs["name_suffix"],
            specsuffix_hidden=kwargs.get("specsuffix_hidden", False),
            load_existing_name=True,
            cat=cat,
        )
        return cat

    @classmethod
    def _convert_status(
        cls,
        status_dict: Optional[Union[Dict, str]],
        moons: int,
        old_bools: List[Optional[bool]],
    ) -> Status:
        """
        Check & convert status to new Status
        :param status_dict: Possible status_dict
        :param moons: age in moons
        :param old_bools: old-style status bools in a list
        :return: valid status
        """
        if status_dict is None:
            raise TypeError(f"Status is None for cat ID: {cls.cat_id}")
        if moons is None:
            raise TypeError(f"Moons is None for cat ID: {cls.cat_id}")

        if isinstance(status_dict, str):
            age = CatAge.get_from_moons(moons)
            status = Status(rank=status_dict, age=age)
        else:
            status = Status(**status_dict)

        if not any(old_bools):
            # either they're not present or all False
            return status

        dead, df, driven_out, exiled, outside = old_bools

        if dead and not status.group.is_afterlife():
            if df:
                status.send_to_afterlife(target_ID=CatGroup.DARK_FOREST_ID)
            elif outside:
                status.send_to_afterlife(target_ID=CatGroup.UNKNOWN_RESIDENCE_ID)
            else:
                status.send_to_afterlife(target_ID=CatGroup.STARCLAN_ID)
        elif exiled:
            status.exile_from_group()
        elif outside and not status.is_outsider:
            status.become_lost()

        if driven_out:
            status.change_group_nearness(CatGroup.PLAYER_CLAN_ID)

        return status

    @classmethod
    def _build_pheno(cls, use_special, kwargs) -> list[Phenotype]:
        gene_config = get_config("genetics_config")
        gene_config.update(get_config("april_fools_genes"))
        phenotype = Phenotype(gene_config, game_setting_get("ban problem genes"))
        chimerapheno = None
        chimera = False
        if kwargs.get("chimerageno"):
            chimerapheno = Phenotype(gene_config, game_setting_get("ban problem genes"))
            chimerapheno.fromJSON(kwargs["chimerageno"])
            chimerapheno.chimerapattern = kwargs["chimera_pattern"] if kwargs["chimera_pattern"] else chimerapheno.ChooseTortiePattern("chimera")
            chimera = True

        if kwargs.get("genotype"):
            phenotype.fromJSON(kwargs["genotype"])
        elif kwargs["parent1"] or kwargs["parent2"]:
            if not kwargs["parent1"]:
                phenotype.KitGenerator(Cat.all_cats[kwargs["parent2"]], gender=kwargs.get("gender"))
                if chimera:
                    chimerapheno.KitGenerator(Cat.all_cats[kwargs["parent2"]], chimera=True, gender=kwargs.get("gender"))
            else:
                phenotype.KitGenerator(Cat.all_cats[kwargs["parent1"]], Cat.all_cats.get(kwargs["parent2"]), gender=kwargs.get("gender"))
                if chimera:
                    threepars = chimerapheno.KitGenerator(Cat.all_cats[kwargs["parent1"]], Cat.all_cats.get(
                        kwargs["parent2"]), chimera=True, gender=kwargs.get("gender"))
        else:
            kittypet_boost = get_config("cat_generation.kittypet_gene_boost")
            if not chimera:
                if use_special and kittypet_boost:
                    phenotype.AltGenerator(special=kwargs.get("gender"))
                else:
                    phenotype.Generator(special=kwargs.get("gender"), kittypet=use_special)
            else:
                par1 = Phenotype(
                    gene_config, game_setting_get("ban problem genes"))
                par2 = Phenotype(
                    gene_config, game_setting_get("ban problem genes"))
                if use_special and kittypet_boost:
                    par1.AltGenerator()
                    par2.AltGenerator()
                else:
                    par1.Generator(kittypet=use_special)
                    par2.Generator(kittypet=use_special)

                phenotype.KitGenerator(par1, par2, gender=kwargs.get("gender"))
                chimerapheno.KitGenerator(par1, par2, gender=kwargs.get("gender"))

            if phenotype.munch[1] == 'Mk':
                phenotype.munch[1] = "mk"
            if phenotype.manx[1] not in ['m', 'ab']:
                phenotype.manx[1] = phenotype.manx[1].lower()
            if 'NoDBE' not in phenotype.pax3 and 'DBEalt' not in phenotype.pax3:
                phenotype.pax3[0] = 'DBEalt'

        phenotype.PhenotypeOutput(phenotype.white_pattern)
        phenotype.SpriteInfo(kwargs.get("moons", 0))
        if chimera:
            chimerapheno.PhenotypeOutput(chimerapheno.white_pattern)
            chimerapheno.SpriteInfo(kwargs.get("moons", 0))

        phenotype.white_pattern = Pelt.generate_white(phenotype.white, phenotype.pointgene, phenotype.whitegrade, phenotype.vitiligo, kwargs.get("white_pattern"), phenotype.pax3)
        if phenotype.maincolour == 'white' and not phenotype.patchmain:
            phenotype.white_pattern = "No"

        if chimerapheno:
            chimerapheno.white_pattern = Pelt.generate_white(chimerapheno.white, chimerapheno.pointgene, chimerapheno.whitegrade, chimerapheno.vitiligo, kwargs.get("chim_white"), chimerapheno.pax3)
            if chimerapheno.maincolour == 'white' and not chimerapheno.patchmain:
                chimerapheno.white_pattern = "No"

        return [phenotype, chimerapheno]

    @classmethod
    def _build_pelt(cls, phenotype, kwargs) -> Pelt:
        """
        Handles some check & convert functionality for pelts
        :param kwargs: Everything we've ever passed into the factory
        :return: A dict of the keys needed to build the pelt
        """
        if isinstance(kwargs.get("tint"), str) and kwargs.get("tint").lower() == "none":
            kwargs["tint"] = None
        if (
            isinstance(kwargs.get("white_patches_tint"), str)
            and kwargs.get("white_patches_tint").lower() == "none"
        ):
            kwargs["white_patches_tint"] = None
            # this then gets set to "offwhite" later

        for specialty in ("specialty", "specialty2"):
            if old_scars := kwargs.get(specialty):
                kwargs["scars"] = tuple([*kwargs["scars"], old_scars])

        pelt = Pelt(
            **{
                "phenotype": phenotype,
                "rusting": kwargs.get("rusting"),
                "paralyzed": kwargs["paralyzed"],
                "newborn_sprite": kwargs.get("sprite_newborn"),
                "kitten_sprite": kwargs.get(
                    "sprite_kitten", kwargs.get("spirit_kitten")
                ),
                "adol_sprite": kwargs.get(
                    "sprite_adolescent", kwargs.get("spirit_adolescent")
                ),
                "adult_sprite": kwargs.get("sprite_adult", kwargs.get("spirit_adult")),
                "senior_sprite": kwargs.get(
                    "sprite_senior", kwargs.get("spirit_senior")
                ),
                "para_adult_sprite": kwargs.get("sprite_para_adult"),
                "reverse": kwargs["reverse"],
                "white_patches_tint": kwargs.get("white_patches_tint", "offwhite"),
                "tint": kwargs.get("tint"),
                "scars": kwargs["scars"],
                "accessory": kwargs.get("accessory", []),
                "opacity": kwargs.get("opacity", 100),
            }
        )
        pelt.check_and_convert(convert_dict=cls.CONVERT)

        return pelt

    @staticmethod
    def _convert_backstory(backstory) -> str:
        """
        Convert an old-style backstory to the new version
        :param backstory:
        :return: the new-style backstory
        """
        # if the key isn't found, return it as the value (no need to convert)
        return BACKSTORIES["conversion"].get(backstory, backstory)

    @classmethod
    def _build_personality(
        cls, facets: str, trait: str, is_kit_trait: bool
    ) -> Personality:
        """
        Builds the personality object from the inputs provided
        :param facets: Cat's facet string
        :param trait: Provided trait
        :param is_kit_trait: True if the cat is kit-aged, False otherwise
        :return: Personality object
        """
        if facets is not None:
            facets = [int(i) for i in facets.split(",")]
            return Personality(
                trait=trait,
                kit_trait=is_kit_trait,
                lawful=facets[0],
                social=facets[1],
                aggress=facets[2],
                stable=facets[3],
            )
        else:
            print(f"WARNING: no facets found for cat ID: {cls.cat_id}")
            return Personality(trait=trait, kit_trait=is_kit_trait)

    @classmethod
    def _convert_skill_and_backstory(
        cls, skill_dict, skill, backstory, rank, age
    ) -> Tuple[CatSkills, str]:
        """
        Handle conversion of some *very old* skills & backstories
        :param skill_dict: modern skill dict
        :param skill: skill string
        :param backstory: backstory string
        :param rank: needed to generate new skills
        :param age: needed to generate new skills
        :return:
        """
        if skill_dict:
            return CatSkills(skill_dict), backstory
        if skill:
            if backstory is not None:
                if skill == "formerly a loner":
                    backstory = cls.rng.choice(BACKSTORIES["loner_backstories"])
                elif skill == "formerly a kittypet":
                    backstory = cls.rng.choice(BACKSTORIES["kittypet_backstories"])
                else:
                    backstory = "clanborn"
            return CatSkills.get_skills_from_old(skill, rank, age), backstory
        else:
            raise Exception(f"No skill data provided for cat ID: {cls.cat_id}")

    @staticmethod
    def _convert_history(died_by, scar_events, cat) -> History:
        """
        Converts some very, very old saves to modern ClanGen
        :param died_by: What killed this cat
        :param scar_events: What happened when they got scarred
        :param cat: The cat in question
        :return: A new History object that describes the cat
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
        return History(died_by=deaths, scar_events=scars, cat=cat)
