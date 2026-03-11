import re
from random import getrandbits, randint, choice, randrange, choices, random, sample
from typing import Optional, List, Union, Type

import i18n

from scripts.cat.cats import Cat
from scripts.cat.genotype import Genotype
from scripts.cat.status import Status
from scripts.cat.enums import (
    CatRank,
    CatAge,
    CatSocial,
    CatGroup,
    CatStanding,
    CatThought,
)
from scripts.cat.names import names
from scripts.cat_relations.enums import RelType
from scripts.clan_package.settings import get_clan_setting
from scripts.game_structure import game, constants
from scripts.cat.constants import BACKSTORIES, PERMANENT
from scripts.events_module.text_adjust import process_text, event_text_adjust, adjust_list_text
from scripts.game_structure.game import game_setting_get
from scripts.clan_package.get_clan_cats import get_alive_clan_queens


def create_bio_parents(Cat, flip=False, second_parent=True, clan=None):
    ages = [randint(15, 120), 0]
    ages[1] = ages[0] + randint(0, 24) - 12
    original_social = choice(
        [CatSocial.KITTYPET, CatSocial.LONER, CatSocial.ROGUE])
    thought = None
    if clan:
        original_social = CatSocial.CLANCAT
        thought = CatThought.OUTSIDE_KIT_DEATH

    blood_parent2 = None
    par2geno = None
    blood_parent = create_new_cat(Cat,
                                  original_social=original_social,
                                  original_group=clan,
                                  alive=choice([True, True, True, False]) if clan else choice(
                                      [True, False]),
                                  moons=ages[0],
                                  gender='fem' if flip else 'masc',
                                  outside=True,
                                  is_parent=True)[0]
    while 'sterile' in blood_parent.permanent_condition:
        if (blood_parent):
            del Cat.all_cats[blood_parent.ID]
        blood_parent = create_new_cat(Cat,
                                      original_social=original_social,
                                      original_group=clan,
                                      alive=choice([True, True, True, False]) if clan else choice(
                                          [True, False]),
                                      moons=ages[0],
                                      gender='fem' if flip else 'masc',
                                      outside=True,
                                      is_parent=True)[0]
    if second_parent:
        original_social = choice(
            [CatSocial.KITTYPET, CatSocial.LONER, CatSocial.ROGUE])
        if clan:
            original_social = CatSocial.CLANCAT
        blood_parent2 = create_new_cat(Cat,
                                       original_social=original_social,
                                       original_group=clan,
                                       alive=choice([True, True, True, False]) if clan else choice(
                                           [True, False]),
                                       moons=ages[1] if ages[1] > 14 else 15,
                                       gender='masc' if flip else 'fem',
                                       outside=True,
                                       is_parent=True)[0]
        while 'sterile' in blood_parent2.permanent_condition:
            if blood_parent2 and Cat.all_cats[blood_parent2.ID]:
                del Cat.all_cats[blood_parent2.ID]
            blood_parent2 = create_new_cat(Cat,
                                           original_social=original_social,
                                           original_group=clan,
                                           alive=choice(
                                               [True, True, True, False]) if clan else choice([True, False]),
                                           moons=ages[0],
                                           gender='masc' if flip else 'fem',
                                           outside=True,
                                           is_parent=True)[0]
    else:
        par2geno = Genotype(
            constants.CONFIG['genetics_config'], game_setting_get("ban problem genes"))
        par2geno.Generator('masc' if flip else 'fem')

    if thought:
        if blood_parent:
            blood_parent.get_new_thought(thought)

            if blood_parent.status.rank == CatRank.MEDICINE_CAT:
                blood_parent.backstory = choice(["medicine_cat", "disgraced1"])
            else:
                blood_parent.backstory = choice(
                    BACKSTORIES["backstory_categories"].get(
                        f"former_clancat_backstories", ["outsider1"])
                )
        if blood_parent2:
            blood_parent2.get_new_thought(thought)
            if blood_parent2.status.rank == CatRank.MEDICINE_CAT:
                blood_parent2.backstory = choice(
                    ["medicine_cat", "disgraced1"])
            else:
                blood_parent2.backstory = choice(
                    BACKSTORIES["backstory_categories"].get(
                        f"former_clancat_backstories", ["outsider1"])
                )

    return [blood_parent, blood_parent2, par2geno]


def create_new_cat_block(
    Cat: Optional["Cat"],
    Relationship,
    event,
    in_event_cats: dict,
    i: int,
    attribute_list: List[str],
    clan=None,
    other_clan=None,
) -> list:
    """
    Creates a single new_cat block and then generates and returns the cats within the block
    :param Cat Cat: always pass Cat class
    :param Relationship Relationship: always pass Relationship class
    :param event: always pass the event class
    :param dict in_event_cats: dict containing involved cats' abbreviations as keys and cat objects as values
    :param int i: index of the cat block
    :param list[str] attribute_list: attribute list contained within the block
    """

    new_cats = None

    # gather parents
    parent1 = None
    parent2 = None
    adoptive_parents = []
    for tag in attribute_list:
        parent_match = re.match(r"parent:\s?([,0-9]+)", tag)
        sibling_match = re.match(r"sibling:\s?([,0-9]+)", tag)
        adoptive_match = re.match(r"adoptive:\s?(.+)", tag)
        if not parent_match and not adoptive_match and not sibling_match:
            continue

        parent_indexes = parent_match.group(
            1).split(",") if parent_match else []
        sibling_indexes = sibling_match.group(
            1).split(",") if sibling_match else []
        adoptive_indexes = adoptive_match.group(
            1).split(",") if adoptive_match else []
        if not parent_indexes and not adoptive_indexes and not sibling_indexes:
            continue

        parent_indexes = [int(index) for index in parent_indexes]
        sibling_indexes = [int(index) for index in sibling_indexes]
        for index in parent_indexes:
            if index >= i:
                continue

            if parent1 is None:
                parent1 = event.new_cats[index][0]
            else:
                parent2 = event.new_cats[index][0]
        for index in sibling_indexes:
            if index >= i:
                continue

            sibling = event.new_cats[index][0]
            if not parent2:
                parent2 = Cat.fetch_cat(sibling.parent2)

        adoptive_indexes = [
            int(index) if index.isdigit() else index for index in adoptive_indexes
        ]
        for index in adoptive_indexes:
            if in_event_cats[index].ID not in adoptive_parents:
                adoptive_parents.append(in_event_cats[index].ID)
                adoptive_parents.extend(in_event_cats[index].mate)

    # gather mates
    give_mates = []
    for tag in attribute_list:
        match = re.match(r"mate:\s?([_,0-9a-zA-Z]+)", tag)
        if not match:
            continue

        mate_indexes = match.group(1).split(",")

        # TODO: make this less ugly
        for index in mate_indexes:
            if index in in_event_cats:
                if in_event_cats[index].status.rank.is_any_apprentice_rank():
                    print("Can't give apprentices mates")
                    continue

                give_mates.append(in_event_cats[index])

    # determine gender
    if "male" in attribute_list:
        gender = "male"
    elif "female" in attribute_list:
        gender = "female"
    elif "can_birth" in attribute_list and not get_clan_setting("same sex birth"):
        gender = "female"
    else:
        gender = None

    # will the cat get a new name?
    if "new_name" in attribute_list:
        new_name = True
    elif "old_name" in attribute_list:
        new_name = False
    else:
        new_name = bool(getrandbits(1))

    # RANK - must be handled before backstories
    rank = None
    for _tag in attribute_list:
        match = re.match(r"status:\s?(.+)", _tag)
        if not match:
            continue

        elif match.group(1) in (
            CatRank.DEPUTY,
            CatRank.LEADER
        ):
            rank = CatRank.WARRIOR
            break
        elif match.group(1) in [
            CatRank.NEWBORN,
            CatRank.KITTEN,
            CatRank.ELDER,
            CatRank.APPRENTICE,
            CatRank.WARRIOR,
            CatRank.MEDIATOR_APPRENTICE,
            CatRank.MEDIATOR,
            CatRank.MEDICINE_APPRENTICE,
            CatRank.MEDICINE_CAT,
        ]:
            rank = match.group(1)
            break

    # SET AGE
    age = None
    for _tag in attribute_list:
        match = re.match(r"age:\s?(.+)", _tag)
        if not match:
            continue

        if match.group(1) in Cat.age_moons:
            min_age, max_age = Cat.age_moons[CatAge(match.group(1))]
            age = randint(min_age, max_age)
            break

        # Set same as first mate
        if match.group(1) == "mate" and give_mates:
            min_age, max_age = Cat.age_moons[give_mates[0].age]
            age = randint(min_age, max_age)
            break

        if match.group(1) == "has_kits":
            age = randint(19, 120)
            break

    if not rank and not age and "meeting" not in attribute_list:
        rank = choice([CatRank.WARRIOR, CatRank.WARRIOR,
                      CatRank.WARRIOR, CatRank.APPRENTICE])
    if rank and not age:
        if rank in [
            CatRank.APPRENTICE,
            CatRank.MEDIATOR_APPRENTICE,
            CatRank.MEDICINE_APPRENTICE,
        ]:
            age = randint(
                Cat.age_moons[CatAge.ADOLESCENT][0],
                Cat.age_moons[CatAge.ADOLESCENT][1],
            )
        elif rank in [CatRank.WARRIOR, CatRank.MEDIATOR, CatRank.MEDICINE_CAT]:
            age = randint(
                Cat.age_moons["young adult"][0], Cat.age_moons["senior adult"][1]
            )
        elif rank == CatRank.ELDER:
            age = randint(Cat.age_moons["senior"][0],
                          Cat.age_moons["senior"][1])

    cat_group = None

    if "kittypet" in attribute_list:
        cat_social = CatSocial.KITTYPET
    elif "rogue" in attribute_list:
        cat_social = CatSocial.ROGUE
    elif "loner" in attribute_list:
        cat_social = CatSocial.LONER
    elif "clancat" in attribute_list or "former clancat" in attribute_list:
        cat_social = CatSocial.CLANCAT
        if "former clancat" in attribute_list:
            cat_social = "former clancat"
        if other_clan:
            cat_group = other_clan.group_ID
        else:
            cat_group = choice([x.group_ID for x in game.clan.all_other_clans])
    else:
        if parent1:
            cat_social = parent1.status.social
        elif game.clan.clancount == "multiclan":
            cat_social = choice([CatSocial.KITTYPET, CatSocial.LONER])
        else:
            cat_social = choice(
                [CatSocial.KITTYPET, CatSocial.LONER, "former clancat"])

    # LITTER
    litter = False
    if "litter" in attribute_list:
        litter = True
        if rank not in (CatRank.KITTEN, CatRank.NEWBORN):
            rank = CatRank.KITTEN
        if rank == CatRank.NEWBORN:
            age = 0
        else:
            age = randint(
                Cat.age_moons[CatAge.KITTEN][0],
                Cat.age_moons[CatAge.KITTEN][1],
            )

    # CHOOSE DEFAULT BACKSTORY BASED ON CAT TYPE, STATUS
    if rank in (CatRank.KITTEN, CatRank.NEWBORN):
        chosen_backstory = choice(
            BACKSTORIES["backstory_categories"]["abandoned_backstories"]
        )
    elif rank == CatRank.MEDICINE_CAT and cat_social == CatSocial.CLANCAT:
        chosen_backstory = choice(["medicine_cat", "disgraced1"])
    elif rank == CatRank.MEDICINE_CAT:
        chosen_backstory = choice(["wandering_healer1", "wandering_healer2"])
    else:
        if cat_social == CatSocial.CLANCAT:
            x = "former_clancat"
        else:
            x = cat_social
        chosen_backstory = choice(
            BACKSTORIES["backstory_categories"].get(
                f"{x}_backstories", ["outsider1"])
        )

    # OPTION TO OVERRIDE DEFAULT BACKSTORY
    bs_override = False
    stor = []
    for _tag in attribute_list:
        match = re.match(r"backstory:\s?(.+)", _tag)
        if match:
            bs_list = [x for x in re.split(r", ?", match.group(1))]
            stor = []
            for story in bs_list:
                if story in set(
                    [
                        backstory
                        for backstory_block in BACKSTORIES[
                            "backstory_categories"
                        ].values()
                        for backstory in backstory_block
                    ]
                ):
                    stor.append(story)
                elif story in BACKSTORIES["backstory_categories"]:
                    stor.extend(BACKSTORIES["backstory_categories"][story])
            bs_override = True
            break
    if bs_override and stor:
        chosen_backstory = choice(stor)

        if (
            chosen_backstory
            in BACKSTORIES["backstory_categories"]["baby_clancat_backstories"] +
            BACKSTORIES["backstory_categories"]["former_clancat_backstories"]
            or (game.clan.clancount == "multiclan" and "clancat" in attribute_list)
        ):
            cat_social = CatSocial.CLANCAT
        elif chosen_backstory in (
            BACKSTORIES["backstory_categories"]["baby_loner_backstories"]
            + BACKSTORIES["backstory_categories"]["loner_backstories"]
        ):
            cat_social = CatSocial.LONER
        elif chosen_backstory in (
            BACKSTORIES["backstory_categories"]["baby_kittypet_backstories"]
            + BACKSTORIES["backstory_categories"]["kittypet_backstories"]
        ):
            cat_social = CatSocial.KITTYPET
        elif (
            chosen_backstory in BACKSTORIES["backstory_categories"]["rogue_backstories"]
        ):
            cat_social = CatSocial.ROGUE

    thought = None
    # KITTEN THOUGHT
    if rank in (CatRank.KITTEN, CatRank.NEWBORN):
        thought = CatThought.ON_JOIN

    # MEETING - DETERMINE IF THIS IS AN OUTSIDE CAT
    outside = False
    if "meeting" in attribute_list:
        outside = True
        if game.clan.clancount != "multiclan" or "clancat" not in attribute_list:
            new_name = False
            rank = None
            thought = CatThought.ON_MEETING
            if age is not None and age <= 6 and not bs_override:
                chosen_backstory = "outsider1"

    # IS THE CAT DEAD?
    alive = True
    if "dead" in attribute_list:
        thought = CatThought.ON_DEATH
        alive = False

    # check if we can use an existing cat here
    chosen_cat: Optional["Cat"] = None
    if "exists" in attribute_list:
        existing_outsiders = [
            i for i in Cat.all_cats.values() 
            if i.status.is_outsider and 
            not i.dead and i.status.is_near() and 
            not i.status.is_lost() and not i.status.is_exiled(clan.group_ID) and i not in in_event_cats.values()
        ]
        possible_outsiders = []
        for cat in existing_outsiders:
            if stor and cat.backstory not in stor:
                continue
            if cat_social != cat.status.social or (
                cat_social == "former clancat" and not cat.status.is_former_clancat
            ):
                continue
            if gender and gender != cat.gender:
                continue
            if age and age not in Cat.age_moons[cat.age]:
                continue
            already_picked = False
            for picked_cats in event.new_cats:
                if cat in picked_cats:
                    already_picked = True
                    break
            if already_picked:
                continue
            possible_outsiders.append(cat)

        if possible_outsiders:
            chosen_cat = choice(possible_outsiders)
            if not alive:
                chosen_cat.die()
            elif not outside:
                if not rank:
                    rank = chosen_cat.status.get_rank_from_age(chosen_cat.age)
                chosen_cat.add_to_clan(clan.group_ID)
                if chosen_cat.status.rank != rank:
                    chosen_cat.rank_change(
                        new_rank=CatRank(rank), resort=True, new_thought=False
                    )
                
                if chosen_cat.status.rank in [CatRank.NEWBORN, CatRank.KITTEN]:
                    rank = chosen_cat.status.get_rank_from_age(chosen_cat.age)
                    if chosen_cat.status.rank != rank:
                        chosen_cat.rank_change(new_rank=CatRank(rank), resort=True)
            elif outside:
                # updates so that the clan is marked as knowing of this cat
                current_standing = chosen_cat.status.get_standing_with_group(
                    clan.group_ID
                )
                if (
                    CatStanding.KNOWN not in current_standing
                    and CatStanding.EXILED not in current_standing
                ):
                    chosen_cat.status.change_standing(CatStanding.KNOWN)

            if new_name:
                name = f"{chosen_cat.name.prefix}"

                chosen_cat.history.prev_names.append(str(chosen_cat.name))
                spaces = name.count(" ")
                if bool(getrandbits(1)):
                    if spaces > 0:  # adding suffix to OG name
                        # make a list of the words within the name, then add the OG name back in the list
                        words = name.split(" ")
                        words.append(name)
                        # pick new prefix from that list
                        new_prefix = choice(words)
                        name = new_prefix
                    chosen_cat.name.prefix = name
                    chosen_cat.name.give_suffix(
                        skills=chosen_cat.skills,
                        personality=chosen_cat.personality,
                        biome=clan.biome
                    )
                else:  # completely new name
                    chosen_cat.name.give_prefix(
                        Cat,
                        biome=clan.biome
                    )
                    chosen_cat.name.give_suffix(
                        skills=chosen_cat.skills,
                        personality=chosen_cat.personality,
                        biome=clan.biome
                    )

            new_cats = [chosen_cat]

    # Now we generate the new cat
    if not chosen_cat:
        generated_parents = []
        if rank in (CatRank.KITTEN, CatRank.NEWBORN) or age in range(Cat.age_moons[CatAge.KITTEN][0], Cat.age_moons[CatAge.KITTEN][1]+1) or parent1:
            generated_parents = create_bio_parents(
                Cat, flip=True if parent1 and 'Y' in parent1.phenotype.sexgene else False, second_parent=not parent1, clan=cat_group if cat_social == CatSocial.CLANCAT else None)
            if not parent1:
                parent1 = generated_parents[1]
            if not parent2:
                parent2 = generated_parents[0]
        new_cats = create_new_cat(
            Cat,
            new_name=new_name,
            kit=False if litter else rank in (CatRank.KITTEN, CatRank.NEWBORN) or age in range(
                Cat.age_moons[CatAge.KITTEN][0], Cat.age_moons[CatAge.KITTEN][1]+1),
            # this is for singular kits, litters need this to be false
            litter=litter,
            backstory=chosen_backstory,
            rank=rank,
            thought=thought,
            original_social=cat_social,
            original_group=cat_group,
            moons=age,
            gender=gender,
            alive=alive,
            outside=outside,
            group=clan.group_ID,
            parent1=parent1.ID if parent1 else None,
            parent2=parent2.ID if parent2 else None,
            extrapar=generated_parents[2] if not parent2 and generated_parents else None,
            is_parent="age:has_kits" in attribute_list,
            adoptive_parents=adoptive_parents if adoptive_parents else None
        )
        while "age:has_kits" in attribute_list and "sterile" in new_cats[0].permanent_condition:
            del Cat.all_cats[new_cats[0].ID]
            new_cats[0] = create_new_cat(
                Cat,
                new_name=new_name,
                kit=False if litter else rank in (
                    CatRank.KITTEN, CatRank.NEWBORN),
                litter=litter,
                backstory=chosen_backstory,
                rank=rank,
                original_social=cat_social,
                original_group=cat_group,
                moons=age,
                gender=gender,
                thought=thought,
                alive=alive,
                outside=outside,
                group=clan.group_ID,
                parent1=parent1.ID if parent1 else None,
                parent2=parent2.ID if parent2 else None,
                extrapar=generated_parents[2] if not parent2 and generated_parents else None,
                is_parent="age:has_kits" in attribute_list,
                adoptive_parents=adoptive_parents if adoptive_parents else None
            )[0]

        # NEXT
        # add relations to bio parents, if needed
        # add relations to cats generated within the same block, as they are littermates
        # add mates
        # THIS DOES NOT ADD RELATIONS TO CATS IN THE EVENT, those are added within the relationships block of the event

        fevercoat = False
        if random() < 0.01:
            fevercoat = True

        for n_c in new_cats:
            if fevercoat:
                n_c.phenotype.fevercoat = True
                if n_c.chimerapheno:
                    n_c.chimerapheno.fevercoat = True

            # SET MATES
            for inter_cat in give_mates:
                if n_c == inter_cat or n_c.ID in inter_cat.mate:
                    continue

                # this is some duplicate work, since this triggers inheritance re-calcs
                # TODO: optimize
                n_c.set_mate(inter_cat)

            # LITTERMATES
            for inter_cat in new_cats:
                if n_c == inter_cat:
                    continue

                y = randrange(0, 20)
                start_relation = Relationship(n_c, inter_cat, False, True)
                start_relation.like += 40 + y
                start_relation.comfort = 40 + y
                start_relation.respect = 10 + y
                start_relation.trust = 30 + y
                n_c.relationships[inter_cat.ID] = start_relation

            # BIO PARENTS
            for par in (parent1, parent2):
                if not par:
                    continue

                y = randrange(0, 20)
                start_relation = Relationship(par, n_c, False, True)
                start_relation.like += 60 + y
                start_relation.comfort = 40 + y
                start_relation.respect = 30 + y
                start_relation.trust = 30 + y
                par.relationships[n_c.ID] = start_relation

                y = randrange(0, 20)
                start_relation = Relationship(n_c, par, False, True)
                start_relation.like += 40 + y
                start_relation.comfort = 70 + y
                start_relation.respect = 30 + y
                start_relation.trust = 60 + y
                n_c.relationships[par.ID] = start_relation

            # ADOPTIVE PARENTS
            for par in adoptive_parents:
                if not par:
                    continue

                par = Cat.fetch_cat(par)

                y = randrange(0, 20)
                start_relation = Relationship(par, n_c, False, True)
                start_relation.like += 60 + y
                start_relation.comfort = 40 + y
                start_relation.respect = 30 + y
                start_relation.trust = 30 + y
                par.relationships[n_c.ID] = start_relation

                y = randrange(0, 20)
                start_relation = Relationship(n_c, par, False, True)
                start_relation.like += 40 + y
                start_relation.comfort = 70 + y
                start_relation.respect = 30 + y
                start_relation.trust = 60 + y
                n_c.relationships[par.ID] = start_relation

            # UPDATE INHERITANCE
            n_c.create_inheritance_new_cat()

    return new_cats

def find_clan_cats(Cat, Relationship, event, in_event_cats: dict, i: int, attribute_list: List[str], clan=None, other_clan=None):
    status = None
    age = None
    adoptive_parents = []
    blood_parent = None
    sibling = None
    parent_match = None
    give_mates = []
    picked_cats = []
    chosen_backstory = None

    all_clan_cats = []
    if "exiled" in attribute_list:
        all_clan_cats = [i for i in Cat.all_cats.values(
        ) if i.status.is_exiled() and i.status.is_exiled() != clan.group_ID and not i.dead]
    if not all_clan_cats:
        all_clan_cats = [i for i in Cat.all_cats.values(
        ) if i.status.group_ID == other_clan.group_ID]

    for a in attribute_list:
        match = re.match(r'status:\s?(.+)', a)
        if match:
            status = match.group(1)
        match = re.match(r'age:\s?(.+)', a)
        if match:
            age = match.group(1)
        match = re.match(r"parent:\s?(.+)", a)
        if match:
            parent_match = "n_c:" + match.group(1)
            blood_parent = in_event_cats[parent_match]
        match = re.match(r"sibling:\s?(.+)", a)
        if match:
            sibling = in_event_cats["n_c:" + match.group(1)]
        match = re.match(r"adoptive:\s?(.+)", a)
        if match:
            adoptive_indexes = match.group(1).split(",") if match else []
            if not adoptive_indexes:
                continue

            adoptive_indexes = [
                int(index) if index.isdigit() else index for index in adoptive_indexes
            ]
            for index in adoptive_indexes:
                if in_event_cats[index].ID not in adoptive_parents:
                    adoptive_parents.append(in_event_cats[index].ID)
                    adoptive_parents.extend(in_event_cats[index].mate)

    # OPTION TO OVERRIDE DEFAULT BACKSTORY
    bs_override = False
    stor = []
    for _tag in attribute_list:
        match = re.match(r"backstory:\s?(.+)", _tag)
        if match:
            bs_list = [x for x in re.split(r", ?", match.group(1))]
            stor = []
            for story in bs_list:
                if story in set(
                        [
                            backstory
                            for backstory_block in BACKSTORIES[
                                "backstory_categories"
                            ].values()
                            for backstory in backstory_block
                        ]
                ):
                    stor.append(story)
                elif story in BACKSTORIES["backstory_categories"]:
                    stor.extend(BACKSTORIES["backstory_categories"][story])
            bs_override = True
            break
    if bs_override and stor:
        chosen_backstory = choice(stor)

    for tag in attribute_list:
        match = re.match(r"mate:\s?([_,0-9a-zA-Z]+)", tag)
        if not match:
            continue

        mate_indexes = match.group(1).split(",")

        # TODO: make this less ugly
        for index in mate_indexes:
            if index in in_event_cats:
                if in_event_cats[index].status.rank.is_any_apprentice_rank():
                    print("Can't give apprentices mates")
                    continue

                give_mates.append(in_event_cats[index])

            try:
                index = int(index)
            except ValueError:
                print(f"mate-index not correct: {index}")
                continue

            if index >= i:
                continue

            give_mates.extend(event.new_cats[index])

    if "litter" in attribute_list:
        (parents, orphans) = get_alive_clan_queens(
            all_clan_cats, clan=other_clan.group_ID)
        if blood_parent:
            picked_cats = parents[blood_parent.ID]
        elif parents:
            litter = parents[choice(list(parents.keys()))]
            picked_cats = litter
        else:
            picked_cats = [choice(orphans)]
    else:
        if blood_parent and not sibling:
            all_clan_cats = [cat for cat in all_clan_cats if cat.parent1]
        elif sibling:
            all_clan_cats = [cat for cat in all_clan_cats if sibling.ID in cat.inheritance.siblings]
        if status == "any_apprentice":
            all_clan_cats = [
                cat for cat in all_clan_cats if cat.status.rank.is_any_apprentice_rank()]
        elif status == "any_healer":
            all_clan_cats = [
                cat for cat in all_clan_cats if cat.status.rank.is_any_medicine_rank()]
        elif status:
            all_clan_cats = [
                cat for cat in all_clan_cats if cat.status.rank.value == status]

        if age == "match":
            all_clan_cats_age = [
                cat for cat in all_clan_cats if cat.age == in_event_cats["m_c"].age]
            if all_clan_cats_age:
                all_clan_cats = all_clan_cats_age
        elif age == "mate":
            all_clan_cats = [cat for cat in all_clan_cats if give_mates[0].is_potential_mate(
                cat, for_love_interest=True, outsider=True)]
            if not all_clan_cats:
                print("No possible mates found")
                all_clan_cats = create_new_cat_block(
                    Cat, Relationship, event, in_event_cats, i, attribute_list, clan=clan, other_clan=other_clan)
        elif age == "has_kits":
            (parents, orphans) = get_alive_clan_queens(
                all_clan_cats, clan=other_clan.group_ID)
            for par_id in parents.keys():
                if Cat.fetch_cat(par_id) not in all_clan_cats:
                    del parents[par_id]
            all_clan_cats = [Cat.fetch_cat(par_id)
                             for par_id in parents.keys()]
        elif age:
            all_clan_cats_age = [
                cat for cat in all_clan_cats if cat.age.value == age]
            if all_clan_cats_age:
                all_clan_cats = all_clan_cats_age
        if not all_clan_cats:
            all_clan_cats = [i for i in Cat.all_cats.values(
            ) if i.status.group_ID == other_clan.group_ID]

        all_clan_cats_healthy = [i for i in all_clan_cats if not i.not_working()]
        picked_cats = [choice(all_clan_cats_healthy if all_clan_cats_healthy else all_clan_cats)]
        if blood_parent and not sibling:
            picked_parents = [picked_cats[0].parent1, picked_cats[0].parent2]
            in_event_cats[parent_match] = Cat.fetch_cat(choice([p for p in picked_parents if p])) if [p for p in picked_parents if p] else None

    if "change_clan" in attribute_list:
        for cat in picked_cats:
            other = cat.status.fetch_clan_object()
            if cat.status.rank == CatRank.LEADER:
                other.leader = None
                other.leader_lives = 0
            if cat.status.rank == CatRank.DEPUTY:
                other.deputy = None
            if cat.status.rank == CatRank.MEDICINE_CAT:
                other.remove_med_cat(cat)
            if cat.status.rank in [CatRank.LEADER, CatRank.DEPUTY]:
                cat.status._change_rank(CatRank.WARRIOR)

            if "rogue" in attribute_list:
                cat.leave_clan(CatSocial.ROGUE)
            elif "former clancat" in attribute_list:
                cat.leave_clan(CatSocial.LONER)
            else:
                cat.status.add_to_group(
                    clan.group_ID, standing_with_past_group=CatStanding.LEFT)
            for app in cat.apprentice.copy():
                app_ob = Cat.fetch_cat(app)
                if app_ob:
                    app_ob.update_mentor()

            cat.update_mentor()
    elif "change_clan_rev" in attribute_list:
        other = give_mates[0].status.fetch_clan_object()
        give_mates[0].status.add_to_group(
            other_clan.group_ID, standing_with_past_group=CatStanding.LEFT)
        if give_mates[0].status.rank == CatRank.LEADER:
            other.leader = None
            other.leader_lives = 0
        if give_mates[0].status.rank == CatRank.DEPUTY:
            other.deputy = None
        if give_mates[0].rank == CatRank.MEDICINE_CAT:
            other.remove_med_cat(cat)
        if give_mates[0].status.rank in [CatRank.LEADER, CatRank.DEPUTY]:
            give_mates[0].status._change_rank(CatRank.WARRIOR)

    if "dead" in attribute_list:
        for cat in picked_cats:
            cat.die()

    for cat in picked_cats:
        if chosen_backstory:
            cat.backstory = chosen_backstory
            cat.history.add_beginning()

        # SET MATES
        for inter_cat in give_mates:
            if cat == inter_cat or cat.ID in inter_cat.mate:
                continue

            # this is some duplicate work, since this triggers inheritance re-calcs
            # TODO: optimize
            cat.set_mate(inter_cat)

        # ADOPTIVE PARENTS
        for par in adoptive_parents:
            if not par:
                continue

            cat.adoptive_parents.append(par)
            par = Cat.fetch_cat(par)

            y = randrange(0, 20)
            start_relation = Relationship(par, cat, False, True)
            start_relation.like += 30 + y
            start_relation.comfortable = 10 + y
            start_relation.respect = 15 + y
            start_relation.trust = 10 + y
            par.relationships[cat.ID] = start_relation

            y = randrange(0, 20)
            start_relation = Relationship(cat, par, False, True)
            start_relation.like += 30 + y
            start_relation.comfortable = 10 + y
            start_relation.respect = 15 + y
            start_relation.trust = 10 + y
            cat.relationships[par.ID] = start_relation

        if adoptive_parents:
            cat.create_inheritance_new_cat()

    return picked_cats


def get_other_clan(clan_name):
    """
    returns the clan object of given clan name
    """
    for clan in game.clan.all_other_clans:
        if clan.name == clan_name:
            return clan


def create_new_cat(
    Cat: Union["Cat", Type["Cat"]],
    new_name: bool = False,
    kit: bool = False,
    litter: bool = False,
    backstory: bool = None,
    rank: Optional[CatRank] = None,
    original_social: CatSocial = CatSocial.CLANCAT,
    original_group: CatGroup = None,
    thought: Optional[CatThought] = None,
    moons: int = None,
    gender: str = None,
    alive: bool = True,
    outside: bool = False,
    group: CatGroup = None,
    parent1: str = None,
    parent2: str = None,
    extrapar: Genotype = None,
    adoptive_parents: list = None,
    is_parent: bool = False
) -> list:
    """
    This function creates new cats and then returns a list of those cats
    :param Cat Cat: pass the Cat class
    :params Relationship Relationship: pass the Relationship class
    :param bool new_name: set True if cat(s) is a loner/rogue receiving a new Clan name - default: False
    :param bool kit: set True if the cat is a lone kitten - default: False
    :param bool litter: set True if a litter of kittens needs to be generated - default: False
    :param bool backstory: a list of possible backstories.json for the new cat(s) - default: None
    :param rank: set as the rank you want the new cat to have - default: None (will cause a random status to be picked)
    :param original_social: set as the cat's old social - default: None (cat will not be given any past social, it will
    appear that they have always been a clancat)
    :param original_group: set as the cat's old group - default: None (cat will not be given any past group)
    :param str thought: if you need to give a custom thought, set it here
    :param bool outside: set this as True to generate the cat as an outsider instead of as part of the Clan - default: False (Clan cat)
    :param int moons: set the age of the new cat(s) - default: None (will be random or if kit/litter is true, will be kitten.
    :param str gender: set the gender (BIRTH SEX) of the cat - default: None (will be random)
    :param bool alive: set this as False to generate the cat as already dead - default: True (alive)
    :param str parent1: Cat ID to set as the biological parent1
    :param str parent2: Cat ID to set as the biological parent2
    :param list adoptive_parents: Cat IDs to set as adoptive parents
    """
    if not thought:
        thought = CatThought.ON_JOIN

    if backstory is None:
        if original_social == CatSocial.KITTYPET:
            backstory = BACKSTORIES["backstory_categories"]["kittypet_backstories"]
        if original_social == CatSocial.ROGUE:
            backstory = BACKSTORIES["backstory_categories"]["rogue_backstories"]
        if original_social == CatSocial.LONER:
            backstory = BACKSTORIES["backstory_categories"]["loner_backstories"]
    if isinstance(backstory, list):
        backstory = choice(backstory)

    if (
        backstory
        in (
            BACKSTORIES["backstory_categories"]["former_clancat_backstories"]
            + BACKSTORIES["backstory_categories"]["baby_clancat_backstories"]
        )
        or original_social == "former clancat"
    ) and not original_group:
        original_group = choice([x.group_ID for x in game.clan.all_other_clans])

    created_cats = []

    if not litter:
        number_of_cats = 1
    else:
        number_of_cats = choices([2, 3, 4, 5], [5, 4, 1, 1], k=1)[0]

    if (litter or kit):
        parent_thought = i18n.t(
            "conditions.pregnancy.half_blood_kitting_thought", count=number_of_cats)
        if Cat.all_cats[parent1].status.is_outsider:
            Cat.all_cats[parent1].thought = event_text_adjust(
                Cat, parent_thought, main_cat=Cat.all_cats[parent1])
        if Cat.all_cats[parent2].status.is_outsider:
            Cat.all_cats[parent2].thought = event_text_adjust(
                Cat, parent_thought, main_cat=Cat.all_cats[parent2])

    if not isinstance(moons, int):
        if rank == CatRank.NEWBORN:
            moons = 0
        elif litter or kit:
            moons = randint(1, 5)
        elif rank in (
            CatRank.APPRENTICE,
            CatRank.MEDICINE_APPRENTICE,
            CatRank.MEDIATOR_APPRENTICE,
        ):
            moons = randint(6, 11)
        elif rank == CatRank.WARRIOR:
            moons = randint(23, 120)
        elif rank == CatRank.MEDICINE_CAT:
            moons = randint(23, 140)
        elif rank == CatRank.ELDER:
            moons = randint(120, 130)
        else:
            moons = randint(6, 120)

    # setting rank
    if not rank and not outside:
        if moons == 0:
            rank = CatRank.NEWBORN
        elif moons < 6:
            rank = CatRank.KITTEN
        elif 6 <= moons <= 11:
            rank = CatRank.APPRENTICE
        elif moons >= 120:
            rank = CatRank.ELDER
        else:
            rank = CatRank.WARRIOR

    # need to get actual age enum
    age = CatAge.SENIOR
    for key_age in Cat.age_moons.keys():
        if moons in range(Cat.age_moons[key_age][0], Cat.age_moons[key_age][1] + 1):
            age: CatAge = key_age
            break

    # cat creation and naming time
    for index in range(number_of_cats):
        # setting gender
        if not gender:
            _gender = choice(['fem', 'masc'])
        else:
            _gender = gender

        # first we generate the cat as though they are not part of the clan yet
        new_cat = Cat(
            moons=moons,
            status_dict={
                "social": original_social,
                "age": age,
                "group_ID": original_group,
            },
            gender=_gender,
            backstory=backstory,
            parent1=parent1,
            parent2=parent2,
            extrapar=extrapar,
            adoptive_parents=adoptive_parents if adoptive_parents else [],
        )

        if new_cat.phenotype.manx[1] == "Ab" or new_cat.phenotype.sexgene[0] == "Y" or new_cat.phenotype.manx[1] == "M" or new_cat.phenotype.munch[1] == "Mk" or ('NoDBE' not in new_cat.phenotype.pax3 and 'DBEalt' not in new_cat.phenotype.pax3):
            if len(created_cats) == 0:
                while new_cat.phenotype.manx[1] == "Ab" or new_cat.phenotype.sexgene[0] == "Y" or new_cat.phenotype.manx[1] == "M" or new_cat.phenotype.munch[1] == "Mk" or ('NoDBE' not in new_cat.phenotype.pax3 and 'DBEalt' not in new_cat.phenotype.pax3):
                    del Cat.all_cats[new_cat.ID]
                    new_cat = Cat(
                        moons=moons,
                        status_dict={
                            "social": original_social,
                            "age": age,
                            "group_ID": original_group,
                        },
                        gender=_gender,
                        backstory=backstory,
                        parent1=parent1,
                        parent2=parent2,
                        extrapar=extrapar,
                        adoptive_parents=adoptive_parents if adoptive_parents else [],
                    )
            else:
                new_cat.moons = 0
                new_cat.status = Status(**{"group_ID": new_cat.status.group_ID,
                                           "rank": CatRank.NEWBORN, "age": CatAge.NEWBORN})
                new_cat.dead = True
                new_cat.get_new_thought(CatThought.ON_DEATH)
                new_cat.history.add_death(
                    str(new_cat.name) + " was stillborn.")
        # this simulates a "history" as whomever they used to be
        new_cat.status.change_current_moons_as(moons)

        if original_social == "former clancat":
            new_cat.status.leave_group(
                choice([CatSocial.KITTYPET, CatSocial.LONER, CatSocial.ROGUE])
            )
        # now we actually add them to the clan, if they should be joining
        if not outside and alive:
            new_cat.add_to_clan(group)
            # check if cat is the correct rank
            if new_cat.status.rank != rank:
                new_cat.status._change_rank(CatRank(rank))
            # give apprentice aged cat a mentor
            if new_cat.status.rank.is_any_apprentice_rank():
                new_cat.update_mentor()
                # ensuring that any cats joining as an apprentice will display the correct skills
                new_cat.skills.primary.interest_only = True
                if new_cat.skills.secondary:
                    new_cat.skills.secondary.interest_only = True

        # NAMES and accs
        # clancat adults should have already generated with a clan-ish name, thus they skip all of this re-naming
        # little babies will take a clancat name, we love indoctrination
        if not outside and (kit or litter or moons < 12) and (not original_group or not game.used_group_IDs[original_group].is_any_clan_group()):
            # babies change name, in case their initial name isn't clan-ish
            new_cat.change_name()
        elif not original_group or not game.used_group_IDs[original_group].is_any_clan_group():
            name_categories = [
                "silly_names",
                "human_names",
                "loner_names",
                "normal_prefixes",
            ]
            # defaults in case of error
            weights = [1, 1, 1, 1]
            # give kittypets a kittypet name
            overwrite_prefix = False
            if original_social == CatSocial.KITTYPET:
                weights = constants.CONFIG["cat_name_controls"]["kittypet"]
                # check if the kittypets come with a pretty acc
                if bool(getrandbits(1)):
                    new_cat.pelt.accessory = (
                        *new_cat.pelt.accessory,
                        choice(new_cat.pelt.collar_accessories),
                    )
            if original_social == CatSocial.LONER:
                weights = constants.CONFIG["cat_name_controls"]["loner"]

            if original_social == CatSocial.ROGUE:
                weights = constants.CONFIG["cat_name_controls"]["rogue"]

            selected_category = choices(name_categories, weights, k=1)[0]
            name = choice(names.names_dict[selected_category])
                
            if selected_category == "normal prefixes" and get_clan_setting("modded names") and get_clan_setting('new prefixes') and random() < 0.9:
                overwrite_prefix = True

            # now, if this cat should take a new clan name, we give them such
            if new_name:
                # check if adding suffix to OG name
                if bool(getrandbits(1)):
                    spaces = name.count(" ")
                    if spaces > 0:
                        # make a list of the words within the name, then add the OG name back in the list
                        words = name.split(" ")
                        words.append(name)
                        # pick new prefix from that list
                        new_prefix = choice(words)
                        new_cat.change_name(new_prefix=new_prefix)
                # else, take a whole new name
                else:
                    new_cat.change_name()
            # else, let them keep their old name
            else:
                new_cat.change_name(new_prefix=name, new_suffix="")
                if overwrite_prefix:
                    new_cat.name.give_prefix(
                        Cat, new_cat.status.fetch_clan_object(game.clan).biome, no_suffix=True)

        # Remove disabling scars, if they generated.
        # these are removed bc the cat won't have the associated perm condition
        not_allowed = [
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

        new_cat.pelt.scars = tuple(
            scar for scar in new_cat.pelt.scars if scar not in not_allowed
        )

        # chance to give the new cat a permanent condition, higher chance for found kits and litters
        if kit or litter:
            chance = int(
                constants.CONFIG["cat_generation"]["base_permanent_condition"] / 11.25
            )
        else:
            chance = constants.CONFIG["cat_generation"]["base_permanent_condition"]

        if not is_parent and get_clan_setting('tnr_mode') and moons > 5:
            kittypet_n = constants.CONFIG['tnr_mode']['kittypet_neuter']
            loner_n = constants.CONFIG['tnr_mode']['loner_tnr']
            if original_social == CatSocial.KITTYPET and random() < kittypet_n:
                new_cat.get_permanent_condition("sterile", False)
            if original_social in (CatSocial.LONER, CatSocial.ROGUE) and random() < loner_n:
                new_cat.get_permanent_condition("sterile", False)
                new_cat.pelt.scars = (*new_cat.pelt.scars, "TNR")
                new_cat.pelt.rebuild_sprite = True
        if not int(random() * chance):
            possible_conditions = []
            for condition in PERMANENT:
                if (kit or litter) and PERMANENT[condition]["congenital"] not in [
                    "always",
                    "sometimes",
                ]:
                    continue
                if condition in ['manx syndrome', "flat nose", 'ocular albinism', 'albinism', 'rabbit gait', 'fully hairless', 'partially hairless', "bad back", "narrowed chest", "bumpy skin"]:
                    continue
                # next part ensures that a kit won't get a condition that takes too long to reveal
                moons = new_cat.moons
                leeway = 5 - (PERMANENT[condition]["moons_until"] + 1)
                if moons > leeway:
                    continue
                possible_conditions.append(condition)

            if possible_conditions:
                chosen_condition = choice(possible_conditions)
                if PERMANENT[chosen_condition]["congenital"] in [
                    "always",
                    "sometimes",
                ]:
                    new_cat.get_permanent_condition(chosen_condition, True)
                    if (
                        new_cat.permanent_condition[chosen_condition]["moons_until"]
                        == 0
                    ):
                        new_cat.permanent_condition[chosen_condition][
                            "moons_until"
                        ] = -2

                # assign scars

                if chosen_condition in ("lost a leg", "born without a leg"):
                    new_cat.pelt.scars = (*new_cat.pelt.scars, "NOPAW")
                elif chosen_condition in ("lost their tail", "born without a tail"):
                    new_cat.pelt.scars = (*new_cat.pelt.scars, "NOTAIL")

        if outside:
            if new_cat.status.social is not CatSocial.CLANCAT:
                new_cat.name.suffix = ""
        if not alive:
            new_cat.die()

        # newbie thought
        new_cat.get_new_thought(thought)

        # and they exist now
        created_cats.append(new_cat)
        game.clan.add_cat(new_cat)
        new_cat.history.add_beginning()

        # create relationships
        new_cat.create_relationships_new_cat()
        # Note - we always update inheritance after the cats are generated, to
        # allow us to add parents.
        # new_cat.create_inheritance_new_cat()

    return created_cats


def gather_cat_objects(
    Cat, abbr_list: List[str], event, stat_cat=None, extra_cat=None, clan=game.clan
) -> list:
    """
    gathers cat objects from list of abbreviations used within an event format block
    :param Cat Cat: Cat class
    :param list[str] abbr_list: The list of abbreviations
    :param event: the controlling class of the event (e.g. Patrol, HandleShortEvents), default None
    :param Cat stat_cat: if passing the Patrol class, must include stat_cat separately
    :param Cat extra_cat: if not passing an event class, include the single affected cat object here. If you are not
    passing a full event class, then be aware that you can only include "m_c" as a cat abbreviation in your rel block.
    The other cat abbreviations will not work.
    :return: list of cat objects
    """

    clan_cats = [x for x in Cat.all_cats_list if x.status.group_ID == clan.group_ID and x.age != CatAge.NEWBORN]
    out_set = set()

    for abbr in abbr_list:
        is_exclusionary = False
        if "-" in abbr:
            is_exclusionary = True
            abbr = abbr.replace("-", "")

        found_cat = None
        if abbr == "m_c":
            found_cat = extra_cat if extra_cat else event.main_cat
        elif abbr == "r_c":
            found_cat = event.random_cats[0] if hasattr(event, "random_cats") else event.random_cat
        elif re.match(r"r_c[0-9]+", abbr):
            index = re.match(r"r_c([0-9]+)", abbr).group(1)
            index = int(index)-1
            if index < len(event.random_cats):
                found_cat = event.random_cats[index]
        # PATROL SPECIFIC
        elif abbr == "p_l":
            found_cat = event.patrol_leader
        elif abbr == "s_c":
            found_cat = stat_cat
        elif abbr == "app1" and len(event.patrol_apprentices) >= 1:
            found_cat = event.patrol_apprentices[0]
        elif abbr == "app2" and len(event.patrol_apprentices) >= 2:
            found_cat = event.patrol_apprentices[1]
        elif abbr == "app3" and len(event.patrol_apprentices) >= 3:
            found_cat = event.patrol_apprentices[2]
        elif abbr == "app4" and len(event.patrol_apprentices) >= 4:
            found_cat = event.patrol_apprentices[3]
        elif abbr == "app5" and len(event.patrol_apprentices) >= 5:
            found_cat = event.patrol_apprentices[4]
        elif abbr == "app6" and len(event.patrol_apprentices) >= 6:
            found_cat = event.patrol_apprentices[5]

        # add/remove cat if found and then continue for loop
        if is_exclusionary and found_cat:
            if found_cat not in out_set:
                # continue to avoid KeyError
                continue
            out_set.remove(found_cat)
            continue
        if not is_exclusionary and found_cat:
            out_set.add(found_cat)
            continue

        # SMALL CAT GROUPS
        found_cat_list = set()
        if abbr == "patrol":
            found_cat_list.update(event.patrol_cats)
        elif re.match(r"n_c:[0-9]+", abbr):  # new_cats
            index = re.match(r"n_c:([0-9]+)", abbr).group(1)
            index = int(index)
            if index < len(event.new_cats):
                found_cat_list.update(event.new_cats[index])
        elif abbr == "multi":
            cat_num = randint(1, max(1, len(event.patrol_cats) - 1))
            found_cat_list.update(sample(event.patrol_cats, cat_num))
        # OVERALL CLAN CATS
        elif abbr == "clan":
            found_cat_list.update(clan_cats)
        elif abbr == "some_clan":  # 1 / 8 of clan cats are affected
            found_cat_list.update(
                sample(clan_cats, randint(1, max(1, round(len(clan_cats) / 8))))
            )

        # add/remove cats if found and then continue for loop
        if is_exclusionary and found_cat_list:
            # removes found_cat_list items from out_set if they are present in out_set
            out_set -= found_cat_list
            continue
        if not is_exclusionary and found_cat_list:
            out_set.update(found_cat_list)
            continue

        # FACET CATS IN CLAN
        if abbr == "high_social":
            found_cat_list = {c for c in out_set if c.personality.sociability > 8}
        elif abbr == "low_social":
            found_cat_list = {c for c in out_set if c.personality.sociability <= 8}
        elif abbr == "high_lawful":
            found_cat_list = {c for c in out_set if c.personality.lawfulness > 8}
        elif abbr == "low_lawful":
            found_cat_list = {c for c in out_set if c.personality.lawfulness <= 8}
        elif abbr == "high_stable":
            found_cat_list = {c for c in out_set if c.personality.stability > 8}
        elif abbr == "low_stable":
            found_cat_list = {c for c in out_set if c.personality.stability <= 8}
        elif abbr == "high_aggress":
            found_cat_list = {c for c in out_set if c.personality.aggression > 8}
        elif abbr == "low_aggress":
            found_cat_list = {c for c in out_set if c.personality.aggression <= 8}

        # add/remove cats if found and then continue for loop
        if is_exclusionary and found_cat_list:
            # removes found_cat_list items from out_set if they are present in out_set
            out_set -= found_cat_list
            continue
        if not is_exclusionary and found_cat_list:
            # found_cat_list includes all qualifying cats!
            out_set = found_cat_list
            continue

        else:
            print(f"WARNING: Unsupported abbreviation {abbr}")

    return list(out_set)


def unpack_rel_block(
    Cat, relationship_effects: List[dict], event=None, stat_cat=None, extra_cat=None, clan=game.clan
) -> dict:
    """
    Unpacks the info from the relationship effect block used in patrol and moon events, then adjusts rel values
    accordingly.

    :param Cat Cat: Cat class
    :param list[dict] relationship_effects: the relationship effect block
    :param event: the controlling class of the event (e.g. Patrol, HandleShortEvents), default None
    :param Cat stat_cat: if passing the Patrol class, must include stat_cat separately
    :param Cat extra_cat: if not passing an event class, include the single affected cat object here. If you are not passing a full event class, then be aware that you can only include "m_c" as a cat abbreviation in your rel block.  The other cat abbreviations will not work.
    :returns: List of all created rel logs for this rel block.
    """
    possible_values = [*RelType]

    created_rel_logs: dict = {}

    is_clan_reaction: bool = False

    for block in relationship_effects:
        cats_from = block.get("cats_from", [])
        cats_to = block.get("cats_to", [])
        amount = block.get("amount")
        values = [x for x in block.get("values", ()) if x in possible_values]

        # if this is a reaction from the entire clan, we need to know for later
        if cats_from == ["clan"] or (
            len(cats_from) == 2 and "clan" in cats_from and "patrol" in cats_from
        ):
            is_clan_reaction = True

        # Gather actual cat objects:
        cats_from_ob = gather_cat_objects(
            Cat, cats_from, event, stat_cat, extra_cat, clan=clan)
        cats_to_ob = gather_cat_objects(
            Cat, cats_to, event, stat_cat, extra_cat, clan=clan)

        # Remove any "None" that might have snuck in
        if None in cats_from_ob:
            cats_from_ob.remove(None)
        if None in cats_to_ob:
            cats_to_ob.remove(None)

        positive = False
        if amount > 0:
            amount = int(amount * constants.CONFIG["relationship"]["pos_rel_change_multiplier"])
            positive = True
        else:
            amount = int(amount * constants.CONFIG["relationship"]["neg_rel_change_multiplier"])

        # grabbing values
        value_changes = {}

        for val in [*RelType]:
            if val in values:
                value_changes[val] = amount

        if positive:
            effect = i18n.t("relationships.positive_postscript")
        else:
            effect = i18n.t("relationships.negative_postscript")

        # Get log
        to_log = None
        from_log = None
        if "log" in block:
            to_log = (
                block["log"].get("cats_to", "") + effect
                if "cats_to" in block["log"]
                else None
            )
            from_log = (
                block["log"].get("cats_from", "") + effect
                if "cats_from" in block["log"]
                else None
            )
            if not to_log and not from_log:
                print(
                    f"something is wrong with relationship log: {block['log']}")

        if is_clan_reaction:
            value_list = adjust_list_text(
                [i18n.t(f"relationships.{x}_word") for x in values]
            )
            name_list = adjust_list_text([str(x.name) for x in cats_to_ob])
            if positive:
                effect = "pos"
            else:
                effect = "neg"
            created_rel_logs["clan"] = i18n.t(
                f"windows.{effect}_clan_rel_log",
                value_list=value_list,
                name_list=name_list,
            )
            change_relationship_values(
                cats_to_ob,
                cats_from_ob,
                **value_changes,
                log=from_log,
            )
        else:
            created_rel_logs.update(
                change_relationship_values(
                    cats_to_ob,
                    cats_from_ob,
                    **value_changes,
                    log=from_log,
                )
            )

        if block.get("mutual"):
            # we'll default to the other log if no unique log was written
            created_rel_logs.update(
                change_relationship_values(
                    cats_from_ob,
                    cats_to_ob,
                    **value_changes,
                    log=to_log if to_log else (from_log.replace("to_cat", "[placeholder]").replace("from_cat", "to_cat").replace("[placeholder]", "from_cat") if from_log else None),
                )
            )

    return created_rel_logs


def change_relationship_values(
    cats_to: list,
    cats_from: list,
    romance: int = 0,
    like: int = 0,
    respect: int = 0,
    comfort: int = 0,
    trust: int = 0,
    log: str = None,
) -> dict:
    """
    changes relationship values according to the parameters.

    :param list[Cat] cats_from: list of cat objects whose rel values will be affected
    (e.g. cat_from loses trust in cat_to)
    :param list[Cat] cats_to: list of cats objects who are the target of that rel value
    (e.g. cat_from loses trust in cat_to)
    :param int romance: amount to change romantic, default 0
    :param int like: amount to change platonic, default 0
    :param int respect: amount to change admiration (respect), default 0
    :param int comfort: amount to change comfort, default 0
    :param int trust: amount to change trust, default 0
    :param str log: the string to append to the relationship log of cats involved
    """

    # This is just for test prints - DON'T DELETE - you can use this to test if relationships are changing
    """changed = False
    if romance == 0 and like == 0 and respect == 0 and \
            comfort == 0 and trust == 0:
        changed = False
    else:
        changed = True"""

    created_rel_logs = {}
    # pick out the correct cats
    for single_cat_from in cats_from:
        for single_cat_to in cats_to:
            # make sure we aren't trying to change a cat's relationship with themself
            if single_cat_from == single_cat_to:
                continue

            # if the cats don't know each other, start a new relationship
            if single_cat_to.ID not in single_cat_from.relationships:
                single_cat_from.create_one_relationship(single_cat_to)

            rel = single_cat_from.relationships[single_cat_to.ID]

            # here we just double-check that the cats are allowed to be romantic with each other
            if (
                single_cat_from.is_potential_mate(single_cat_to, for_love_interest=True)
                or single_cat_to.ID in single_cat_from.mate
            ):
                # now gain the romance
                rel.romance += romance

            # gain other rel values
            rel.like += like
            rel.respect += respect
            rel.comfort += comfort
            rel.trust += trust

            # for testing purposes - DON'T DELETE - you can use this to test if relationships are changing
            """
            print(str(single_cat_from.name) + " gained relationship with " + str(rel.cat_to.name) + ": " +
                  "Romance: " + str(romance) +
                  " /Like: " + str(like) +
                  " /Respect: " + str(respect) +
                  " /Comfort: " + str(comfort) +
                  " /Trust: " + str(trust)) if changed else print("No relationship change")"""
            if not log:
                log = i18n.t("relationships.relationship_log")
            if log and isinstance(log, str):
                replace_dict = {}
                if "from_cat" in log:
                    replace_dict["from_cat"] = (
                        str(single_cat_from.name),
                        choice(single_cat_from.pronouns),
                    )
                if "to_cat" in log:
                    replace_dict["to_cat"] = (
                        str(single_cat_to.name),
                        choice(single_cat_to.pronouns),
                    )
                if replace_dict:
                    processed_log = process_text(log, replace_dict)
                else:
                    processed_log = log

                if single_cat_from in created_rel_logs:
                    created_rel_logs[single_cat_from] = "<br><br>".join(
                        [created_rel_logs[single_cat_from], processed_log]
                    )
                else:
                    created_rel_logs.update({single_cat_from: processed_log})

                log_text = processed_log + i18n.t(
                    "relationships.age_postscript",
                    name=str(single_cat_to.name),
                    count=single_cat_to.moons,
                )
                if log_text not in rel.log:
                    rel.log.append(log_text)

    return created_rel_logs
