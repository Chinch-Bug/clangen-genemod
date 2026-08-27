import math
from random import choice, randint, random, randrange
from typing import Optional
from copy import deepcopy, copy

import i18n

from scripts.cat.cats import Cat
from scripts.cat.enums import CatAge, CatRank, CatSocial, CatGroup, CatThought, CatCompatibility
from scripts.cat.factories.new_cat_factory import NewCatFactory
from scripts.cat.factories.typed_dicts import StatusDict
from scripts.cat.microservices.add_to_clan import add_to_clan
from scripts.cat.names import Name
from scripts.cat_relations.enums import RelType
from scripts.cat_relations.inheritance2 import inheritance_db
from scripts.cat_relations.relationship import Relationship, create_one_relationship
from scripts.clan_package.settings import get_clan_setting
from scripts.cat.microservices.conditions import add_congenital_condition
from scripts.config import get_config
from scripts.events_module.event_information import EventInformation
from scripts.events_module.consequences import (
    create_new_cat,
    change_relationship_values,
)
from scripts.events_module.event_filters import get_personality_compatibility
from scripts.events_module.pregnancy.build_strings import get_newborn_strings
from scripts.events_module.pregnancy.check_family_size import (
    biggest_family_is_big,
    get_biggest_family,
)
from scripts.events_module.pregnancy.check_parents import no_kits_allowed
from scripts.events_module.short.condition_events import Condition_Events
from scripts.events_module.text_adjust import event_text_adjust, adjust_list_text
from scripts.game_structure import game
from scripts.clan_package.get_clan_cats import get_living_clan_cat_count


def get_kits(
    kits_amount, 
    cat=None, 
    other_cat=None, 
    clan=game.clan, 
    adoptive_parents=None, 
    affair_parents=None,
    backkit=None, 
    surrogate=None):
    """Create some amount of kits
    No parents are specified, it will create a blood parents for all the
    kits to be related to. They may be dead or alive, but will always be outside
    the clan.
    """
    all_kitten = []
    if not adoptive_parents:
        adoptive_parents = []

    # First, just a check: If we have no cat, but an other_cat was provided, swap other_cat to cat:
    # This way, we can ensure that if only one parent is provided, it's cat, not other_cat.
    # And if cat is None, we know that no parents were provided.
    if other_cat and not cat:
        cat = other_cat
        other_cat = None

    blood_parent = None
    blood_parent2 = None

    ##### SELECT BACKSTORY #####
    if not backkit:
        if cat and "pregnant" in cat.injuries and other_cat and other_cat[0].status.get_last_living_group() != cat.status.get_last_living_group():
            backkit = 'halfclan1' if other_cat[0].status.group.is_any_clan_group() else 'outsider_roots1'
        elif cat and other_cat and other_cat[0].status.get_last_living_group() != cat.status.get_last_living_group():
            backkit = 'halfclan2' if other_cat[0].status.group.is_any_clan_group() else 'outsider_roots2'

    if backkit:
        backstory = backkit
    else:  # cat is adopted
        backstory = choice(["abandoned1", "abandoned2",
                            "abandoned3", "abandoned4"])
    ###########################

    ##### ADOPTIVE PARENTS #####
    # First, gather all the mates of the provided bio parents to be added
    # as adoptive parents (if there is  a poly relationship).
    all_adoptive_parents = []

    all_pars = [cat]
    if other_cat:
        all_pars += other_cat
    birth_parents = [i for i in all_pars if i and (
        not surrogate or i not in surrogate)]
    for _par in birth_parents:
        if affair_parents and _par in affair_parents:
            continue
        for _m in _par.mate:
            _mcat = Cat.fetch_cat(_m)
            if _mcat not in birth_parents and _m not in all_adoptive_parents and not _mcat.dead:
                all_adoptive_parents.append(_m)

    # Then, add any additional adoptive parents that were provided passed directly into the
    # function.
    for _m in adoptive_parents:
        if _m not in all_adoptive_parents:
            all_adoptive_parents.append(_m)
    if not cat:
        litter_age = choice([0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5])

        initial_amount = kits_amount
        kits_amount = 0

        stillborn_chance = get_stillborn_chance(
            initial_amount)

        death_chances = get_config("death_related.kit_death_chances")
        for i in range(initial_amount):
            if random() < stillborn_chance:
                continue
            elif litter_age == 0 or not (get_clan_setting("modded_kits")):
                kits_amount += 1
            elif random() < death_chances['0']:
                continue
            elif litter_age == 1:
                kits_amount += 1
            elif random() < death_chances['1']:
                continue
            elif litter_age == 2:
                kits_amount += 1
            elif random() < death_chances['2']:
                continue
            elif litter_age == 3:
                kits_amount += 1
            elif random() < death_chances['3']:
                continue
            elif litter_age == 4:
                kits_amount += 1
            elif random() < death_chances['4']:
                continue
            else:
                kits_amount += 1
        if kits_amount == 0:
            kits_amount = 1

    #############################

    #### GENERATE THE KITS ######
    identical = False
    i = 0
    while i < kits_amount:
        i += 1

        if not cat:
            # No parents provided, create a blood parent - this is an adoption.
            if not blood_parent:
                # Generate a blood parent if we haven't already.
                nr_of_parents = 1
                if get_clan_setting('multisire') and randint(1, get_config("pregnancy.multi-sire_chance")) == 1:
                    nr_of_parents = randint(2, get_config("pregnancy.multi-sire_max_sires"))

                parage = randint(15, 120)
                cat_type = choice(
                    [CatSocial.LONER, CatSocial.ROGUE, CatSocial.KITTYPET])
                blood_parent = create_new_cat(Cat,
                                                original_social=cat_type,
                                                gender='fem' if not get_clan_setting(
                                                        'same sex birth') else None,
                                                alive=choice([True, False]),
                                                moons=parage,
                                                outside=True,
                                                is_parent=True)[0]
                blood_parent2 = []

                for i in range(0, nr_of_parents):
                    blood_par2 = None
                    parage = parage + randint(0, 24) - 12
                    while not blood_par2 or 'sterile' in blood_par2.permanent_condition:
                        if blood_par2 and Cat.all_cats[blood_par2.ID]:
                            del Cat.all_cats[blood_par2.ID]
                        cat_type = choice(
                            [CatSocial.LONER, CatSocial.ROGUE, CatSocial.KITTYPET])
                        blood_par2 = create_new_cat(Cat,
                                                    original_social=cat_type,
                                                    gender='masc' if not get_clan_setting(
                                                        'same sex birth') else None,
                                                    alive=choice(
                                                        [True, False]),
                                                    moons=parage if parage > 14 else 15,
                                                    outside=True,
                                                    is_parent=True)[0]
                    blood_parent2.append(blood_par2)

            sire = choice(blood_parent2)
            chimera_sire = choice(blood_parent2)
            kit_status = {
                "social": blood_parent.status.social,
                "age": CatRank.NEWBORN if litter_age == 0 else CatRank.KITTEN,
                "group_ID": blood_parent.status.get_last_living_group()
            }

            kit = NewCatFactory.create_cat(parent1=blood_parent.ID, parent2=sire.ID, extrapar=chimera_sire if sire.ID !=
                                            chimera_sire.ID else None, status_dict=kit_status, moons=litter_age, backstory=backstory)
        else:
            # Two parents provided
            second_blood = None
            if other_cat:
                second_blood = choice(other_cat)
                chimera_sire = choice(other_cat)
                if second_blood.ID == chimera_sire.ID:
                    chimera_sire = None
            else:
                print("There should be a second parent but there isn't??")

            kit_status = {
                "social": cat.status.social,
                "age": CatRank.NEWBORN,
                "group_ID": cat.status.group_ID
            }

            if backkit:
                kit = NewCatFactory.create_cat(parent1=cat.ID, parent2=second_blood.ID if second_blood else None,
                                                moons=0, backstory=backstory, status_dict=kit_status, extrapar=chimera_sire)
            else:
                kit = NewCatFactory.create_cat(
                    parent1=cat.ID, parent2=second_blood.ID, moons=0, status_dict=kit_status)

        if identical:
            identical = False
            ref_cat = copy(all_kitten[-1])
            kit.permanent_condition = ref_cat.permanent_condition
            kit.phenotype = deepcopy(ref_cat.phenotype)
            kit.phenotype.tortiepattern = None
            kit.phenotype.chimerapattern = None
            kit.phenotype.merlepattern = None
            kit.phenotype.somatic = {}
            kit.phenotype.white_pattern = kit.pelt.generate_white(
                kit.phenotype.white, kit.phenotype.pointgene, kit.phenotype.whitegrade, kit.phenotype.vitiligo, None, kit.phenotype.pax3)
            kit.phenotype.PhenotypeOutput(kit.phenotype.white_pattern)
            kit.phenotype.SpriteInfo(kit.moons)
            kit.pelt.length = ref_cat.pelt.length
            kit.pelt.tint = ref_cat.pelt.tint
            kit.pelt.white_patches_tint = ref_cat.pelt.white_patches_tint
            kit.pelt.scars = ref_cat.pelt.scars

            if ref_cat.chimerapheno:
                kit.chimerapheno = deepcopy(ref_cat.chimerapheno)
                kit.chimerapheno.tortiepattern = None
                kit.chimerapheno.chimerapattern = kit.chimerapheno.ChooseTortiePattern(
                    "chimera")
                kit.chimerapheno.merlepattern = None
                kit.chimerapheno.white_pattern = kit.pelt.generate_white(
                    kit.chimerapheno.white, kit.chimerapheno.pointgene, kit.chimerapheno.whitegrade, kit.chimerapheno.vitiligo, None, kit.chimerapheno.pax3)
                kit.chimerapheno.PhenotypeOutput(
                    kit.chimerapheno.white_pattern)
                kit.chimerapheno.SpriteInfo(kit.moons)

            kit.parent1 = ref_cat.parent1
            kit.parent2 = ref_cat.parent2
            kit.parent3 = ref_cat.parent3
            kit.genderalign = ref_cat.genderalign

        else:
            if kit.chimerapheno:
                kits_amount -= 1
                if i > kits_amount:
                    kit.chimerapheno = None

            if get_config("genetics_config.identical_twins") and randint(1, get_config("genetics_config.identical_twins")) == 1 and kits_amount < 19:
                kits_amount += 1
                identical = True

        kit.assign_thought()

        # make lost status match parent
        if cat and cat.status.is_lost():
            kit.status.make_standing_unknown(cat.status.get_last_living_group())
            kit.status.become_lost(
                cat.status.social, specific_group=cat.status.get_last_living_group()
            )

        # kit.adoptive_parents = all_adoptive_parents  # Add the adoptive parents.
        # Prevent duplicate prefixes in litter
        extant = [
            kitty.name.prefix for kitty in all_kitten if kitty.ID != kit.ID]
        while kit.name.prefix in extant:
            kit.name = Name(kit)

        all_kitten.append(kit)
        # adoptive parents are set at the end, when everything else is decided

        # remove scars
        kit.pelt.scars = tuple()

        # try to give them a permanent condition. 1/90 chance
        # don't delete the game.clan condition, this is needed for a test
        if game.clan and not int(
            random() * get_config("cat_generation.base_permanent_condition")
        ):
            add_congenital_condition(kit)
            for condition in kit.permanent_condition:
                if kit.permanent_condition[condition] == "born without a leg":
                    kit.pelt.scars = (*cat.pelt.scars, "NOPAW")
                elif kit.permanent_condition[condition] == "born without a tail" and kit.phenotype.bobtailnr != 1:
                    kit.pelt.scars = (*cat.pelt.scars, "NOTAIL")
            Condition_Events.handle_already_disabled(kit, clan)

        # create and update relationships
        relationships_to_update = []
        # if kits are in a clan, the whole clan gets to know
        if cat and cat.status.group.is_any_clan_group():
            relationships_to_update = game.clan.clan_cats
        # if they aren't, then they only know parents, sibling rels will be added later
        elif cat:
            relationships_to_update = [cat.ID]
            # other parent only knows if they're in the same group
            if other_cat:
                for o_cat in other_cat:
                    if o_cat.status.group == cat.status.group:
                        relationships_to_update.append(o_cat.ID)

        if relationships_to_update:
            for cat_id in relationships_to_update:
                if cat_id == kit.ID:
                    continue
                the_cat = Cat.all_cats.get(cat_id)
                if not the_cat or the_cat.dead or the_cat.status.group_ID != cat.status.group_ID:
                    continue
                if the_cat.ID in kit.get_parents():
                    parent_to_kit = get_config("new_cat.parent_buff.parent_to_kit")
                    y = randrange(0, 15)
                    start_relation = Relationship(the_cat, kit, family=True)
                    start_relation.like = parent_to_kit[RelType.LIKE] + y
                    start_relation.comfort = parent_to_kit[RelType.COMFORT] + y
                    start_relation.respect = parent_to_kit[RelType.RESPECT] + y
                    start_relation.trust = parent_to_kit[RelType.TRUST] + y
                    the_cat.relationships[kit.ID] = start_relation

                    kit_to_parent = get_config("new_cat.parent_buff.kit_to_parent")
                    y = randrange(0, 15)
                    start_relation = Relationship(kit, the_cat, family=True)
                    start_relation.like += kit_to_parent[RelType.LIKE] + y
                    start_relation.comfort = kit_to_parent[RelType.COMFORT] + y
                    start_relation.respect = kit_to_parent[RelType.RESPECT] + y
                    start_relation.trust = kit_to_parent[RelType.TRUST] + y
                    kit.relationships[the_cat.ID] = start_relation
                else:
                    the_cat.relationships[kit.ID] = Relationship(the_cat, kit)
                    kit.relationships[the_cat.ID] = Relationship(kit, the_cat)

        #### REMOVE ACCESSORY ######
        kit.pelt.accessory = tuple()
        game.clan.add_cat(kit)

        #### GIVE HISTORY ######
        kit.history.add_beginning(clan_born=bool(cat))

    if blood_parent or blood_parent2:
        thought = i18n.t(
            "conditions.pregnancy.half_blood_kitting_thought",
            count=kits_amount,
        )
        blood_parent.thought = event_text_adjust(
            Cat, thought, main_cat=blood_parent, clan=clan)
        for par in range(len(blood_parent2)):
            blood_parent2[par].thought = event_text_adjust(
                Cat, thought, main_cat=blood_parent2[par], clan=clan)

    # check other cats of Clan for siblings
    for kitten in all_kitten:
        # update/buff the relationship towards the siblings
        for second_kitten in all_kitten:
            y = randrange(0, 15)
            if second_kitten.ID == kitten.ID:
                continue
            relationship_value = get_config("new_cat.sib_buff.littermates_to_eachother")
            start_relation = Relationship(kitten, second_kitten, True)
            start_relation.like += relationship_value["like"] + y
            start_relation.comfort += relationship_value["comfort"] + y
            start_relation.trust += relationship_value["trust"] + y
            kitten.relationships[second_kitten.ID] = start_relation

    # check if the possible adoptive cat is not already in the family tree and
    # add them as adoptive parents if not
    final_adoptive_parents = []
    for adoptive_p in all_adoptive_parents:
        if not Cat.fetch_cat(adoptive_p):
            continue
        if adoptive_p not in inheritance_db.get_relatives(all_kitten[0].ID, True):
            final_adoptive_parents.append(adoptive_p)
        if Cat.fetch_cat(adoptive_p).status.group_ID != all_kitten[0].status.group_ID:
            continue
        Cat.fetch_cat(adoptive_p).assign_thought(CatThought.ON_BIRTH)
    if not adoptive_parents:
        cat.assign_thought(CatThought.ON_BIRTH)
        if other_cat:
            for x in other_cat:
                if x.status.group_ID != all_kitten[0].status.group_ID:
                    continue
                x.assign_thought(CatThought.ON_BIRTH)

    # Add the adoptive parents.
    for kit in all_kitten:
        kit.adoptive_parents = final_adoptive_parents.copy()
        if blood_parent2:
            for birth_p in blood_parent2:
                if birth_p.ID not in [kit.parent3, kit.parent2, kit.parent1] and birth_p.ID not in kit.adoptive_parents:
                    kit.adoptive_parents.append(birth_p.ID)
        if other_cat:
            for birth_p in other_cat:
                if birth_p.ID not in [kit.parent3, kit.parent2, kit.parent1] and birth_p.ID not in kit.adoptive_parents:
                    kit.adoptive_parents.append(birth_p.ID)
        if not kit.adoptive_parents:
            continue

        # update relationship for adoptive parents
        for parent_id in final_adoptive_parents:
            parent = Cat.fetch_cat(parent_id)
            if parent:
                kit_to_parent = get_config("new_cat.parent_buff.kit_to_parent")
                parent_to_kit = get_config("new_cat.parent_buff.parent_to_kit")
                change_relationship_values(
                    cats_from=[kit],
                    cats_to=[parent],
                    **kit_to_parent,
                )
                change_relationship_values(
                    cats_from=[parent],
                    cats_to=[kit],
                    **parent_to_kit,
                )
    inheritance_db.load_inheritances(Cat)

    # check for more extended family members to create relationships with
    # we only need this for one kit, since they all share relatives
    all_relatives: list = all_kitten[0].get_relatives()
    parents = all_kitten[0].get_parents()
    # getting the cat objects
    all_relatives = [
        Cat.fetch_cat(c)
        for c in all_relatives
        if c not in list(parents) and c not in [k.ID for k in all_kitten]
    ]
    all_relatives = [c for c in all_relatives if c.status.group_ID == all_kitten[0].status.group_ID]

    for kit in all_kitten:
        for c in all_relatives:
            if c.faded:
                continue
            ext_relative_modifier = get_config("new_cat.ext_relative_modifier")
            rel_reflection = ext_relative_modifier * len(parents)
            variation_range = math.ceil(20 / len(parents))
            y = randrange(-variation_range, variation_range)

            # this finds what the relative's relationship is toward each parent and applies a reflection of that
            # relationship to the kit. reflection values will be divided by 4 by default and then modified
            # by the random y value
            new_relationship = {
                "cats_to": [kit],
                "cats_from": [c],
                "like": 0,
                "comfort": 0,
                "respect": 0,
                "trust": 0,
            }
            for parent_id in parents:
                try:
                    relation_toward_parent: Relationship = c.relationships[parent_id]
                except KeyError:
                    # cat had no relationship toward parent
                    continue

                new_relationship["like"] += (
                    int(relation_toward_parent.like / rel_reflection) + y
                    if relation_toward_parent.like
                    else 5
                )
                new_relationship["comfort"] += (
                    int(relation_toward_parent.comfort / rel_reflection) + y
                    if relation_toward_parent.comfort
                    else 0
                )
                new_relationship["respect"] += (
                    int(relation_toward_parent.respect / rel_reflection) + y
                    if relation_toward_parent.respect
                    else 0
                )
                new_relationship["trust"] += (
                    int(relation_toward_parent.trust / rel_reflection) + y
                    if relation_toward_parent.trust
                    else 0
                )

            # determine what sort of relationship we've ended up with
            rel_amounts = [
                new_relationship["like"],
                new_relationship["comfort"],
                new_relationship["respect"],
                new_relationship["trust"],
            ]
            neg = False
            pos = False
            for digit in rel_amounts:
                if digit < 0:
                    neg = True
                else:
                    pos = True
                if neg and pos:
                    break

            if pos and neg:
                rel_type = "neutral"
            elif pos:
                rel_type = "positive"
            else:
                rel_type = "negative"

            # adds reaction text to type postscript and age postscript
            new_relationship["log"] = i18n.t(
                f"relationships.{rel_type}_postscript",
                text=event_text_adjust(
                    Cat,
                    choice(get_newborn_strings()[f"{rel_type}_log"]),
                    main_cat=c,
                    random_cat=kit,
                    clan=game.clan,
                ),
            )

            change_relationship_values(**new_relationship)

    return all_kitten


def handle_adoption(cat: Cat, other_cat: Optional[Cat] = None, clan=game.clan):
    """Handle if the there is no pregnancy but the pair triggered kits chance."""
    if other_cat:
        for x in other_cat:
            if not x.status.group.is_any_clan_group() or x.birth_cooldown > 0 or no_kits_allowed(x):
                other_cat.remove(x)
    
    if other_cat and len(other_cat) < 1:
        return

    if cat.ID in game.clan.pregnancy_data:
        return

    if other_cat:
        for x in other_cat:
            if x.ID in game.clan.pregnancy_data:
                return
    
    # Gather adoptive parents, to feed into the 
    # get kits function. 
    adoptive_parents = [cat.ID]
    if other_cat:
        for x in other_cat:
            adoptive_parents.append(x.ID)
    
    for _m in cat.mate:
        if _m not in adoptive_parents:
            adoptive_parents.append(_m)

    if other_cat:
        for x in other_cat:
            for _m in x.mate:
                if _m not in adoptive_parents:
                    adoptive_parents.append(_m)
    
    amount = get_amount_of_kits(cat)
    kits = get_kits(amount, None, None, clan, adoptive_parents=adoptive_parents)
    amount = len(kits)

    event = "hardcoded.adoption_kittens_single"
    cats_names = str(cat.name)
    if other_cat:
        event = "hardcoded.adoption_kittens_pair"
        cats_names = adjust_list_text([str(cat.name)] + [str(c.name) for c in other_cat])

    print_event = i18n.t(
        event,
        names=cats_names,
        insert=i18n.t("conditions.pregnancy.kit_amount", count=amount),
        count=amount,
    )
    
    cats_involved = [cat.ID]
    cat.assign_thought(CatThought.ON_BIRTH)
    if other_cat:
        for x in other_cat:
            if x.status.group_ID != kits[0].status.group_ID:
                continue
            cats_involved.append(x.ID)
            x.assign_thought(CatThought.ON_BIRTH)
    for kit in kits:
        kit.assign_thought(CatThought.ON_JOIN)
        cats_involved.append(kit.ID)
        add_to_clan(kit, clan.group_ID)

    # Normally, birth cooldown is only applied to cat who gave birth. However, if we don't apply birth cooldown to
    # adoption, we get too much adoption, since adoptive couples are using the increased two-parent kits chance.
    # We will only apply it to "cat" in this case, which is enough to stop the couple from adopting about within
    # the window.
    cat.birth_cooldown = get_config("pregnancy.birth_cooldown")

    game.cur_events_list.append(
        EventInformation(print_event, ["birth_death"], involved_cats=cats_involved, clan=clan.group_ID)
    )


def get_amount_of_kits(cat, hidden=False):
    """Get the amount of kits which will be born."""

    if (get_clan_setting('modded_kits')):

        one_kit = [1] * get_config(f"pregnancy.one_kit_modded.{cat.age.value}")
        two_kits = [2] * get_config(f"pregnancy.two_kit_modded.{cat.age.value}")
        three_kits = [3] * get_config(f"pregnancy.three_kit_modded.{cat.age.value}")
        four_kits = [4] * get_config(f"pregnancy.four_kit_modded.{cat.age.value}")
        five_kits = [5] * get_config(f"pregnancy.five_kit_modded.{cat.age.value}")
        six_kits = [choice([6, 7, 8])] * get_config(f"pregnancy.six_kit_modded.{cat.age.value}")
        nine_kits = [choice([9, 10, 11, 12])] * get_config(f"pregnancy.nine_kit_modded.{cat.age.value}")
        max_kits = [choice([13, 14, 15, 16, 17, 18, 19])] * get_config(f"pregnancy.max_kit_modded.{cat.age.value}")

        amount = choice(one_kit + two_kits + three_kits + four_kits + five_kits + six_kits + nine_kits + max_kits)

    else:
        min_kits = get_config(f"pregnancy.min_kits")
        min_kit = [min_kits] * get_config(f"pregnancy.one_kit_possibility.{cat.age.value}")
        two_kits = [min_kits + 1] * get_config(f"pregnancy.two_kit_possibility.{cat.age.value}")
        three_kits = [min_kits + 2] * get_config(f"pregnancy.three_kit_possibility.{cat.age.value}")
        four_kits = [min_kits + 3] * get_config(f"pregnancy.four_kit_possibility.{cat.age.value}")
        five_kits = [min_kits + 4] * get_config(f"pregnancy.five_kit_possibility.{cat.age.value}")
        max_kits = [get_config(f"pregnancy.max_kits")] * get_config(f"pregnancy.max_kit_possibility.{cat.age.value}")

        amount = choice(min_kit + two_kits + three_kits + four_kits + five_kits + max_kits)

    if hidden:
        amount = max(1, int(amount/3))

    return amount

def get_stillborn_chance(kits_amount):
    """Fetch chance of stillborn kittens."""

    stillborn_info = get_config("pregnancy.stillborn_chances")
    stillborn_chance = 0
    if kits_amount < 3:
        stillborn_chance = stillborn_info['small']
    elif kits_amount == 3:
        stillborn_chance = stillborn_info['three']
    elif kits_amount < 6:
        stillborn_chance = stillborn_info['mid']
    elif kits_amount < 9:
        stillborn_chance = stillborn_info['big']
    else:
        stillborn_chance = stillborn_info['large']

    if not (get_clan_setting("modded_kits")):
        stillborn_chance = 0

    return stillborn_chance


def get_balanced_kit_chance(first_parent: Cat, second_parent: Cat, is_affair, clan) -> int:
    """Returns the chance for these cats to have kittens together"""
    # Now that the second parent is determined, we can calculate the balanced chance for kits
    # get the chance for pregnancy
    if not (get_clan_setting('modded_kits')):
        inverse_chance = get_config("pregnancy.primary_chance_unmated")
    else:
        inverse_chance = get_config("pregnancy.modded_primary_chance_unmated")
    if first_parent.mate and not is_affair:
        if not (get_clan_setting('modded_kits')):
            inverse_chance = get_config("pregnancy.primary_chance_mated")
        else:
            inverse_chance = get_config("pregnancy.modded_primary_chance_mated")
    
    is_med = False
    if first_parent.status.rank in (CatRank.MEDICINE_CAT, CatRank.MEDICINE_APPRENTICE):
        is_med = True
    elif second_parent:
        for p in second_parent:
            if p != "Surrogate" and p.status.rank in (CatRank.MEDICINE_CAT, CatRank.MEDICINE_APPRENTICE):
                is_med = True

    if is_med:
        inverse_chance += get_config("pregnancy.healer_modifier")

    # SETTINGS
    # - decrease inverse chance if only mated pairs can have kits
    if not get_clan_setting("single parentage") and not get_clan_setting(
        "unmated parentage"
    ):
        inverse_chance = int(inverse_chance * 0.7)

    # - decrease inverse chance if affairs are not allowed
    if not get_clan_setting("affair"):
        inverse_chance = int(inverse_chance * 0.7)

    # CURRENT CAT AMOUNT
    # - increase the inverse chance if the clan is bigger
    living_cats = get_living_clan_cat_count(Cat, clan.group_ID)

    if living_cats < 10:
        inverse_chance = int(inverse_chance * 0.5)
    elif living_cats > 30:
        inverse_chance = int(inverse_chance * (living_cats / 30))

    # POPULATION EQUALIZER
    # - increase chance of new litters if secondary clans smaller than main Clan
    if clan != game.clan:
        main_clan_living_cats = get_living_clan_cat_count(Cat)
        ratio = living_cats / (main_clan_living_cats or 1)
        if ratio < 0.33:
            inverse_chance = int(inverse_chance * ratio / 2)
        if ratio < 0.5:
            inverse_chance = int(inverse_chance * ratio)
        elif ratio < 0.75:
            inverse_chance = int(inverse_chance * ratio * 1.25)


    # COMPATIBILITY
    # - decrease / increase depending on the compatibility
    comp = None
    inv = inverse_chance
    if second_parent:
        for x in second_parent:
            if x == "Surrogate":
                continue
            if comp == True:
                break
            comp = get_personality_compatibility(first_parent, x)
            if comp != CatCompatibility.NEUTRAL:
                buff = 0.85
                if comp == CatCompatibility.NEGATIVE:
                    buff += 0.3
                inverse_chance = int(inverse_chance * buff)


    average_romantic_love = -1000
    average_comfort = -1000
    average_trust = -1000
    # RELATIONSHIP
    # - decrease the inverse chance if the cats are getting along well
    if second_parent:
        # get the needed relationships
        for x in second_parent:
            if x == "Surrogate":
                continue
            if x.ID in first_parent.relationships:
                second_parent_relation = first_parent.relationships[x.ID]
            else:
                second_parent_relation = create_one_relationship(first_parent, x)
            if not second_parent_relation.opposite_relationship:
                second_parent_relation.link_relationship()

            if not second_parent_relation:
                continue

            x_romantic_love = (second_parent_relation.romance +
                                    second_parent_relation.opposite_relationship.romance) / 2
            if x_romantic_love > average_romantic_love:
                average_romantic_love = x_romantic_love
            x_comfort = (second_parent_relation.comfort +
                            second_parent_relation.opposite_relationship.comfort) / 2
            if x_comfort > average_comfort:
                average_comfort = x_comfort
            x_trust = (second_parent_relation.trust +
                            second_parent_relation.opposite_relationship.trust) / 2
            if x_trust > average_trust:
                average_trust = x_trust

        if average_romantic_love >= 85:
            inverse_chance -= int(inverse_chance * 0.3)
        elif average_romantic_love >= 55:
            inverse_chance -= int(inverse_chance * 0.2)
        elif average_romantic_love >= 35:
            inverse_chance -= int(inverse_chance * 0.1)

        if average_comfort >= 85:
            inverse_chance -= int(inverse_chance * 0.3)
        elif average_comfort >= 55:
            inverse_chance -= int(inverse_chance * 0.2)
        elif average_comfort >= 35:
            inverse_chance -= int(inverse_chance * 0.1)

        if average_trust >= 85:
            inverse_chance -= int(inverse_chance * 0.3)
        elif average_trust >= 55:
            inverse_chance -= int(inverse_chance * 0.2)
        elif average_trust >= 35:
            inverse_chance -= int(inverse_chance * 0.1)
    
    # AGE
    # - decrease the inverse chance if the whole clan is really old
    avg_age = int(sum((cat.moons for cat in Cat.all_cats.values() if cat.status.group_ID == clan.group_ID)) / living_cats)
    if avg_age > 80:
        inverse_chance = int(inverse_chance * 0.8)

    # CURRENT KIT COUNT
    # increases inverse chance according to number of existing children (ex. 5 kids will multiply by 1.5)
    inverse_chance += int(inverse_chance * len(first_parent.get_children(True)) * 0.1)

    # 'INBREED' counter
    # - increase inverse chance if one of the current cats belongs in the biggest family
    biggest_family = get_biggest_family(clan)

    in_biggest = False
    if second_parent:
        for x in second_parent:
            if x == "Surrogate":
                continue
            if x.ID in biggest_family:
                in_biggest = True

    if first_parent.ID in biggest_family or second_parent and in_biggest:
        inverse_chance = int(inverse_chance * 1.7)

    # - decrease inverse chance if the current family is small
    if len(first_parent.get_relatives(get_clan_setting("first cousin mates"))) < (
        living_cats / 15
    ):
        inverse_chance = int(inverse_chance * 0.7)

    # - decrease inverse chance single parents if settings allow and biggest family is huge
    settings_allow = not second_parent and not get_clan_setting("single parentage")
    if settings_allow and biggest_family_is_big(clan):
        inverse_chance = int(inverse_chance * 0.9)

    return inverse_chance
