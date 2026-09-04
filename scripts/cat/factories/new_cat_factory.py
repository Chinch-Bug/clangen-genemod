import random
from operator import xor
from typing import Tuple

from abc import ABC, abstractmethod
from scripts.cat.phenotype import Phenotype
from scripts.cat import save_load
from scripts.cat.cats import Cat
from scripts.cat.constants import BACKSTORIES
from scripts.cat.enums import CatAge, CatRank, CatSocial
from scripts.cat.factories.base_factory import BaseCatFactory
from scripts.cat.factories.typed_dicts import (
    MentorshipDict,
    CatTogglesDict,
    InheritanceDict,
    AfterlifeAffinityDict,
)
from scripts.cat.names import Name
from scripts.cat.pelts import Pelt
from scripts.cat.personality import Personality
from scripts.cat.skills import CatSkills
from scripts.cat.status import Status
from scripts.game_structure import game
from scripts.config import get_config
from scripts.game_structure.game.settings import game_setting_get

BASE_RNG = random.Random


class NewCatFactory(BaseCatFactory, ABC):
    rng = BASE_RNG()

    @classmethod
    def create_cat(cls, **overrides):
        """
        Create a new cat with randomness. Override any elements of the creation with keyword arguments
        :param overrides: Any desired overrides to the random generation
        :return: Cat object
        """
        # remove all values that are empty
        overrides = {k: v for k, v in overrides.items() if v is not None}

        status_dict = overrides.get("status_dict", {})
        if "rank" in overrides:
            status_dict["rank"] = overrides.get("rank")
        if "group_ID" in overrides:
            status_dict["group_ID"] = overrides.get("group_ID")

        # the worst combined dependency ever
        age, moons, status = cls._determine_age_moons_and_status(
            moons=overrides.get("moons"), status_dict=status_dict
        )

        gender_dict = {}
        # if specified, override the randomizer
        gender_dict["sex"] = overrides.get("gender")
        if gender_dict["sex"] == 'female':
            gender_dict["sex"] = 'fem'
        elif gender_dict["sex"] == 'male':
            gender_dict["sex"] = 'masc'

        chimerapheno = None
        phenotype = None
        passes = 1
        parent3 = None
        if pelt := overrides.get("pelt"):
            pelt = Pelt(pelt)
            phenotype = pelt.phenotype
        else:
            pelt, phenotype, chimerapheno, passes, parent3 = cls._get_random_pelt(
                gender_dict["sex"],
                (overrides.get("parent1"), overrides.get("parent2"), overrides.get("extrapar")),
                age,
                moons,
                no_disabling_scars=overrides.get("no_disabling_scars", False),
                use_special=overrides.get("use_special", False)
            )
        gender_dict = cls._get_random_gender_and_genderalign(phenotype, age)
        if overrides.get("genderalign"):
            gender_dict["genderalign"] = overrides.get("genderalign")

        skills = overrides.get(
            "skill_dict", cls._get_random_skills_dict(status.rank, age)
        )
        if not isinstance(skills, CatSkills):
            skills = CatSkills(skill_dict=skills)

        mate = overrides.get("mate", [])
        if isinstance(mate, str):
            mate = [mate]

        cat_params = {
            "ID": cls.get_free_id(),
            "gender_dict": gender_dict,
            "pelt": pelt,
            "phenotype": phenotype,
            "chimerapheno": chimerapheno,
            "passes": passes,
            "moons": moons,
            "status": status,
            "backstory": overrides.get(
                "backstory",
                cls._get_random_backstory_from_status(status, age),
            ),
            "skills": skills,
            "personality": cls._get_random_personality(age),
            "mentorship": MentorshipDict(
                mentor=None,
                former_mentor=[],
                patrol_with_mentor=0,
                apprentice=[],
                former_apprentices=[],
            ),
            "inheritance": InheritanceDict(
                parent1=overrides.get("parent1"),
                parent2=overrides.get("parent2"),
                parent3=parent3,
                adoptive_parents=overrides.get("adoptive_parents", []),
                surrogate_parents=overrides.get("surrogate_parents", []),
                affair_parents=overrides.get("affair_parents", []),
                faded_offspring=[],
                mate=mate,
                previous_mates=[],
            ),
            "affinity": AfterlifeAffinityDict(starclan=0, dark_forest=0),
            "toggles": CatTogglesDict(
                no_kits=False,
                no_mates=False,
                no_retire=False,
                prevent_fading=False,
                favourite=False,
            ),
            "experience": overrides.get(
                "experience", cls._get_random_experience(age, moons)
            ),
            "birth_cooldown": overrides.get("birth_cooldown", 0),
            "faded": False,
            "specsuffix_hidden": False,
        }

        cat = Cat(**cat_params)

        cls._handle_genetic_confitions(cat)

        cat.name = Name(
            prefix=overrides.get("prefix"),
            suffix=overrides.get("suffix"),
            specsuffix_hidden=overrides.get("specsuffix_hidden", False),
            load_existing_name=True,
            cat=cat,
        )

        Cat.all_cats[cat.ID] = cat
        if cat not in Cat.all_cats_list:
            Cat.insert_cat(cat)

        return cat

    @classmethod
    @abstractmethod
    def _get_random_age(cls) -> CatAge:
        return cls.rng.choice([*CatAge])

    @classmethod
    @abstractmethod
    def _get_random_age_from_rank(cls, rank) -> CatAge:
        """
        :param rank: Provided cat's rank
        :return: Random CatAge appropriate for the cat's rank
        """
        if not isinstance(rank, CatRank):
            rank = CatRank(rank)

        if rank == CatRank.NEWBORN:
            return CatAge.NEWBORN
        if rank == CatRank.KITTEN:
            return CatAge.KITTEN
        if rank == CatRank.ELDER:
            return CatAge.SENIOR
        if rank.is_any_apprentice_rank():
            return CatAge.ADOLESCENT

        return cls.rng.choice(
            [
                CatAge.YOUNG_ADULT,
                CatAge.ADULT,
                CatAge.ADULT,
                CatAge.SENIOR_ADULT,
            ]
        )

    @classmethod
    @abstractmethod
    def _get_random_status_from_age(cls, age) -> Status:
        status = Status()
        status.generate_new_status(age)

        return status

    @staticmethod
    @abstractmethod
    def _get_random_backstory_from_status(status: Status, age: CatAge):
        if status.social == CatSocial.CLANCAT:
            return "clanborn"

        social_category = str(status.rank) + "_backstories"

        if age.is_baby():
            social_category = f"baby_{social_category}"
        possible_backstories = BACKSTORIES["backstory_categories"][social_category]

        return random.choice(possible_backstories)

    @classmethod
    @abstractmethod
    def _get_random_moons(cls, age: CatAge) -> int:
        """
        Generate random moons appropriate for the given age
        :param age: CatAge
        :return: Appropriate moons
        """
        return cls.rng.randint(Cat.age_moons[age][0], Cat.age_moons[age][1])

    @classmethod
    def _determine_age_moons_and_status(
        cls, moons, status_dict
    ) -> Tuple[CatAge, int, Status]:
        """
        Figure out the age, moons and status of a cat depending on what's provided

        :param moons: Moons of the cat
        :param status_dict: Status dict describing the cat
        :return: CatAge, moons and Status that all agree with one another
        """
        age = None
        if status_dict and moons is not None:
            return CatAge.get_from_moons(moons), moons, Status(**status_dict)
        if not status_dict and moons is None:
            age = cls._get_random_age()
            status = cls._get_random_status_from_age(age)
            moons = cls._get_random_moons(age)
        elif not status_dict and moons is not None:
            age = CatAge.get_from_moons(moons)
            status = cls._get_random_status_from_age(age)
        elif status_dict and moons is None:
            if "rank" in status_dict:
                age = cls._get_random_age_from_rank(status_dict["rank"])
            elif (
                "group_history" in status_dict
                and "rank" in status_dict["group_history"][-1]
            ):
                age = cls._get_random_age_from_rank(
                    status_dict["group_history"][-1]["rank"]
                )
            else:
                age = cls._get_random_age()
            status = Status(**status_dict)
            moons = cls._get_random_moons(age)
            if moons > 200:
                moons = 200
        else:
            status = None

        if not isinstance(moons, int) or not status or not age:
            raise Exception("Something went wrong generating age, moons or status_dict")

        return age, moons, status

    @classmethod
    @abstractmethod
    def _get_random_gender_and_genderalign(cls, phenotype, age) -> dict:
        gender = {"sex": phenotype.sex}
        gender["genderalign"] = gender["sex"]

        trans_chance = cls.rng.randint(0, 50)
        nb_chance = cls.rng.randint(0, 75)
        agender_chance = cls.rng.randint(0, 100)

        if age.is_baby():
            trans_chance = 0
            nb_chance = 0
            agender_chance = 0

        # GENDER IDENTITY
        gender["genderalign"] = ""
        if (gender["sex"] == 'intersex' or
           (gender["sex"] == "molly" and 'Y' in phenotype.sexgene) or
           (gender["sex"] == "tom" and 'Y' not in phenotype.sexgene) or
           (len(phenotype.sexgene) != 2)):
            gender["genderalign"] = 'intersex '
        if nb_chance == 1:
            gender["genderalign"] += "sam"
        elif agender_chance == 1:
            gender["genderalign"] += "agender"
        elif (gender["sex"] == "molly" or (gender["sex"] == 'intersex' and 'Y' not in phenotype.sexgene)):
            if trans_chance == 1:
                gender["genderalign"] += "trans tom"
            else:
                if (gender["sex"] == 'intersex'):
                    if ('Y' in phenotype.sexgene):
                        gender["genderalign"] += 'tom'
                    else:
                        gender["genderalign"] += 'molly'
                else:
                    gender["genderalign"] += gender["sex"]
        elif (gender["sex"] == "tom" or (gender["sex"] == 'intersex' and 'Y' in phenotype.sexgene)):
            if trans_chance == 1:
                gender["genderalign"] += "trans molly"
            else:
                if (gender["sex"] == 'intersex'):
                    if ('Y' in phenotype.sexgene):
                        gender["genderalign"] += 'tom'
                    else:
                        gender["genderalign"] += 'molly'
                else:
                    gender["genderalign"] += gender["sex"]

        return gender

    @classmethod
    def _get_random_pelt(cls, gender, parents, age, moons, no_disabling_scars: bool, use_special: bool = False):
        gene_config = get_config("genetics_config")
        gene_config.update(get_config("april_fools_genes"))
        phenotype = Phenotype(gene_config, game_setting_get("ban problem genes"))
        chimerapheno = None
        chimera = False
        passes = 1
        parent3 = None
        if cls.rng.randint(1, gene_config["chimera"]) == 1:
            chimerapheno = Phenotype(gene_config, game_setting_get("ban problem genes"))
            chimerapheno.chimerapattern = chimerapheno.ChooseTortiePattern("chimera")
            chimera = True
            if cls.rng.random() < 0.001:
                passes = 0
            elif cls.rng.random() < 0.34:
                passes = 2

        if parents[0] or parents[1]:
            if not parents[0]:
                phenotype.KitGenerator(Cat.all_cats[parents[1]], parents[2], gender=gender)
                if chimera:
                    chimerapheno.KitGenerator(Cat.all_cats[parents[1]], parents[2], chimera=True, gender=gender)
            else:
                phenotype.KitGenerator(Cat.all_cats[parents[0]], Cat.all_cats.get(parents[1], parents[2]), parents[2], gender=gender)
                if chimera:
                    threepars = chimerapheno.KitGenerator(Cat.all_cats[parents[0]], Cat.all_cats.get(
                        parents[1], parents[2]), parents[2], chimera=True, gender=gender)
                    if threepars and isinstance(parents[2], Cat):
                        parent3 = parents[2].ID
        else:
            kittypet_boost = get_config("cat_generation.kittypet_gene_boost")
            if not chimera:
                if use_special and kittypet_boost:
                    phenotype.AltGenerator(special=gender)
                else:
                    phenotype.Generator(special=gender, kittypet=use_special)
            else:
                par1 = Phenotype(gene_config, game_setting_get("ban problem genes"))
                par2 = Phenotype(gene_config, game_setting_get("ban problem genes"))
                if use_special and kittypet_boost:
                    par1.AltGenerator()
                    par2.AltGenerator()
                else:
                    par1.Generator(kittypet=use_special)
                    par2.Generator(kittypet=use_special)

                phenotype.KitGenerator(par1, par2, gender=gender)
                chimerapheno.KitGenerator(par1, par2, gender=gender)

            if phenotype.munch[1] == 'Mk':
                phenotype.munch[1] = "mk"
            if phenotype.manx[1] not in ['m', 'ab']:
                phenotype.manx[1] = phenotype.manx[1].lower()
            if 'NoDBE' not in phenotype.pax3 and 'DBEalt' not in phenotype.pax3 and phenotype.pax3 != ["DBEcel", "DBEcel"]:
                phenotype.pax3[0] = 'DBEalt'

        if (cls.rng.randint(1, gene_config["intersex"]) == 1) or (chimerapheno and xor('Y' in phenotype.sexgene, 'Y' in chimerapheno.sexgene)):
            phenotype.sex = "intersex"
            if (cls.rng.randint(1, 25) == 1 and 'Y' in phenotype.sexgene) or (chimerapheno and xor('Y' in phenotype.sexgene, 'Y' in chimerapheno.sexgene) and cls.rng.randint(1, 10) == 1):
                phenotype.sex = 'molly'
            elif (cls.rng.randint(1, 25) == 1 and 'Y' not in phenotype.sexgene) or (chimerapheno and xor('Y' in phenotype.sexgene, 'Y' in chimerapheno.sexgene) and cls.rng.randint(1, 10) == 1):
                phenotype.sex = 'tom'
        if passes != 1 and (not chimerapheno or xor('Y' in phenotype.sexgene, 'Y' in chimerapheno.sexgene)):
            passes = 1
            if phenotype.sex == "tom" and 'Y' not in phenotype.sexgene:
                passes = 2

        phenotype.white_pattern = Pelt.generate_white(phenotype.white, phenotype.pointgene, phenotype.whitegrade, phenotype.vitiligo, None, phenotype.pax3)
        phenotype.PhenotypeOutput(phenotype.white_pattern)
        phenotype.SpriteInfo(moons if moons else 0)
        if phenotype.maincolour == 'white' and not phenotype.patchmain:
            phenotype.white_pattern = "No"

        if chimerapheno:
            chimerapheno.white_pattern = Pelt.generate_white(chimerapheno.white, chimerapheno.pointgene, chimerapheno.whitegrade, chimerapheno.vitiligo, None, chimerapheno.pax3)
            chimerapheno.PhenotypeOutput(chimerapheno.white_pattern)
            chimerapheno.SpriteInfo(moons if moons else 0)
            if chimerapheno.maincolour == 'white' and not chimerapheno.patchmain:
                chimerapheno.white_pattern = "No"


        pelt = Pelt.generate_new_pelt(
            phenotype,
            age,
        )
        if no_disabling_scars:
            # code copied from removed create_cat function
            # used for generating new cats for a fresh Clan
            not_allowed_scars = (
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
            )

            pelt.scars = tuple(
                scar for scar in pelt.scars if scar not in not_allowed_scars
            )
        
        return [pelt, phenotype, chimerapheno, passes, parent3]

    @classmethod
    def _handle_genetic_confitions(cls, cat):
        cat.genetic_conditions(False)

    @classmethod
    @abstractmethod
    def _get_random_personality(cls, age: CatAge):
        return Personality(kit_trait=age.is_baby())

    @classmethod
    @abstractmethod
    def _get_random_experience(cls, age, moons: int) -> int:
        if age.is_baby():
            return 0

        if age == CatAge.ADOLESCENT:
            experience = 0
            ran = get_config("clancat_ex.base_app_timeskip_ex")
            for i in range(Cat.age_moons[CatAge.ADOLESCENT][0], moons):
                exp = cls.rng.choice(
                    list(range(ran[0][0], ran[0][1] + 1))
                    + list(range(ran[1][0], ran[1][1] + 1))
                )
                experience += exp + 3
            return experience
        elif age in (CatAge.YOUNG_ADULT, CatAge.ADULT):
            return cls.rng.randint(
                Cat.experience_levels_range["prepared"][0],
                Cat.experience_levels_range["proficient"][1],
            )
        elif age == CatAge.SENIOR_ADULT:
            return cls.rng.randint(
                Cat.experience_levels_range["proficient"][0],
                Cat.experience_levels_range["adept"][1],
            )
        elif age == CatAge.SENIOR:
            return cls.rng.randint(
                Cat.experience_levels_range["adept"][0],
                Cat.experience_levels_range["masterful"][1],
            )
        else:
            return 0

    @classmethod
    @abstractmethod
    def _get_random_skills_dict(cls, rank, age):
        skills = CatSkills.generate_new_catskills(rank, age, rng=cls.rng)
        return skills

    @staticmethod
    def get_free_id():
        potential_id = str(next(Cat.id_iter))

        if game.clan:
            faded_cats = save_load.get_faded_ids()
        else:
            faded_cats = []

        while potential_id in Cat.all_cats or potential_id in faded_cats:
            potential_id = str(next(Cat.id_iter))
        return potential_id
