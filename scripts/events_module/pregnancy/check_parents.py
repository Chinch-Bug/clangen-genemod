from random import choice, random, randint
from typing import Optional
from operator import xor

from scripts.cat.cats import Cat, BACKSTORIES
from scripts.cat.enums import (
    CatAge,
    CatRank,
    CatSocial,
    CatThought,
)
from scripts.cat_relations.relationship import Relationship
from scripts.clan_package.settings import get_clan_setting
from scripts.game_structure import game
from scripts.events_module.consequences import (
    create_new_cat,
)
from scripts.events_module.pregnancy.check_family_size import (
    biggest_family_is_big,
    get_biggest_family,
)
from scripts.events_module.event_filters import (
    get_highest_romantic_relation,
)
from scripts.events_module.thoughts.generate_thoughts import get_new_thought
from scripts.config import get_config

def cat_is_amab(cat):
    return (('Y' in cat.phenotype.sexgene and cat.phenotype.sex != "molly") or cat.phenotype.sex == "tom")

def no_kits_allowed(cat):
    kit_blocked_ranks = set()
    if get_clan_setting("block_litters_by_rank"):
        for rank in CatRank:
            rank_str = rank
            if rank == CatRank.APPRENTICE:
                rank_str = CatRank.WARRIOR
            elif "apprentice" in rank:
                rank_str = rank.replace(" apprentice", "")
            if get_clan_setting(f"block_litters_{rank_str}"):
                kit_blocked_ranks.add(rank)
    return cat.no_kits or cat.status.rank in kit_blocked_ranks


def check_if_can_have_kits(cat, for_surrogate=False):
    """Check if the given cat can have kits, see for age, birth-cooldown and so on."""
    if not cat:
        return False

    if cat.birth_cooldown:
        return False

    if "recovering from birth" in cat.injuries or "pregnant" in cat.injuries:
        return False

    # decide chances of having kits, and if it's possible at all.
    # Including - age, dead status, having kits turned off.
    not_correct_age = (
        cat.age in [CatAge.NEWBORN, CatAge.KITTEN, CatAge.ADOLESCENT]
        or cat.moons < 15
    )
    if not_correct_age or no_kits_allowed(cat) or cat.dead:
        return False

    # check for mate
    if cat.mate:
        for mate_id in cat.mate:
            if mate_id not in cat.all_cats:
                print(
                    f"WARNING: {cat.name}  has an invalid mate # {mate_id}. This has been unset."
                )
                cat.mate.remove(mate_id)
    else:
        # if the cat has no mate, and we don't allow single parents, unmated parents, or affairs
        # then they can't have kits
        if (
            not get_clan_setting("single parentage")
            and not get_clan_setting("unmated parentage")
            and not for_surrogate
        ):
            return False

    # if function reaches this point, having kits is possible
    return True


def check_second_parent(cat: Cat, second_parent: Cat) -> tuple[bool, bool]:
    """
    This checks to see if the chosen second parent can have kits. It assumes CAT can have kits.
    returns:
    parent can have kits, kits are adopted
    """

    surrogates = get_clan_setting("surrogates")
    same_sex_birth = get_clan_setting("same sex birth")
    same_sex_adoption = get_clan_setting("same sex adoption")

    if not second_parent:
        if get_clan_setting("single_parentage"):
            return True, False, second_parent
        else:
            return False, False, second_parent
    elif len(second_parent) == 1:
        # Checks for second parent alone:
        if not check_if_can_have_kits(second_parent[0]):
            return False, False, second_parent

        # Check to see if the pair can have kits.
        if not xor(cat_is_amab(cat), cat_is_amab(second_parent[0])) or ("sterile" in cat.permanent_condition or "sterile" in second_parent[0].permanent_condition):
            if same_sex_birth and not "sterile" in second_parent[0].permanent_condition and not "sterile" in cat.permanent_condition:
                return True, False, second_parent
            elif (surrogates and second_parent[0].ID in cat.mate and random() < get_config("pregnancy.surrogate_rate")) and not ("sterile" in second_parent[0].permanent_condition and "sterile" in cat.permanent_condition):
                return True, False, ["Surrogate"] + second_parent
            elif not same_sex_adoption:
                return False, False, second_parent
            else:
                return True, True, second_parent

        return True, False, second_parent
    else:
        second_parent_copy = []
        for x in second_parent:
            if check_if_can_have_kits(x) or x == None:
                second_parent_copy.append(x)

        second_parent = second_parent_copy
        if len(second_parent) < 1:
            return False, False, second_parent

        second_parent_copy = []

        for x in second_parent:
            if (xor(cat_is_amab(cat), cat_is_amab(x)) or same_sex_birth) and not "sterile" in x.permanent_condition:
                second_parent_copy.append(x)

        if len(second_parent_copy) < 1:
            if surrogates and second_parent[0].ID in cat.mate and random() < get_config("pregnancy.surrogate_rate"):
                return True, False, ["Surrogate"] + second_parent
            elif same_sex_adoption:
                return True, True, second_parent
            else:
                return False, False, second_parent
        if "sterile" in cat.permanent_condition:
            if surrogates and second_parent[0].ID in cat.mate and random() < get_config("pregnancy.surrogate_rate"):
                return True, False, ["Surrogate"] + second_parent
            elif same_sex_adoption:
                return True, True, second_parent
            else:
                return False, False, second_parent

        return True, False, second_parent_copy


def get_second_parent(cat, clan):
    """
    Return the second parent of a cat, which will have kits.
    Also returns a bool that is true if an affair was triggered.
    """
    # randomly select a mate of given cat
    samesex = get_clan_setting("same sex birth")

    mate = None
    if len(cat.mate) > 0:
        mate = []
        if get_clan_setting('multisire'):
            mate_copy = cat.mate
            for x in mate_copy:
                mate.append(cat.fetch_cat(x))
        else:
            mate.append(cat.fetch_cat(choice(cat.mate)))

    # if the sex does matter, choose the best solution to allow kits
    if not samesex and mate and not cat_is_amab(cat):
        opposite_mate = [cat.fetch_cat(mate_id) for mate_id in cat.mate if xor(cat_is_amab(cat.fetch_cat(
            mate_id)), cat_is_amab(cat)) and "sterile" not in cat.fetch_cat(mate_id).permanent_condition]
        if len(opposite_mate) > 0:
            mate = opposite_mate
            if not get_clan_setting('multisire'):
                mate = [choice(opposite_mate)]
    elif not samesex and mate and cat_is_amab(cat):
        opposite_mate = [cat.fetch_cat(mate_id) for mate_id in cat.mate if xor(cat_is_amab(cat.fetch_cat(
            mate_id)), cat_is_amab(cat)) and "sterile" not in cat.fetch_cat(mate_id).permanent_condition]
        if len(opposite_mate) > 0:
            mate = [choice(opposite_mate)]

    if not cat.mate and not get_clan_setting('unmated parentage'):
        return mate, False

    affair_allowed = get_clan_setting("affair")
    if mate and not affair_allowed:
        # if affairs setting is OFF, mate will always be the second parent
        return mate, False

    # get relationships to influence the affair chance
    relationship_toward_mate = None
    if mate:
        for x in mate:
            rel = None
            if x.ID in cat.relationships:
                rel = cat.relationships[x.ID]
            else:
                continue

            if not relationship_toward_mate:
                relationship_toward_mate = rel
            elif relationship_toward_mate.romance < rel.romance:
                relationship_toward_mate = rel

    # LOVE AFFAIR & COPARENTING
    # Handle love affair chance.
    new_partner = _determine_highest_romantic_relation(
        cat, mate if mate else None, relationship_toward_mate if mate else None, samesex)
    if new_partner:
        if mate and get_clan_setting('multisire') and not cat_is_amab(cat):
            mate.append(new_partner)
        else:
            mate = [new_partner]
        return mate, True

    # RANDOM AFFAIR & COPARENTING
    if not cat.mate:
        # is there's no mate to cheat on then this isn't an affair, rather it's coparenting
        coparenting = True
    else:
        coparenting = False

    if coparenting:
        chance = get_config("pregnancy.unmated_random_affair_chance")
    else:
        chance = get_config("pregnancy.random_affair_chance")

    # 'buff' affairs if the current biggest family is big + this cat doesn't belong there
    biggest_family = get_biggest_family(clan)

    if (
        biggest_family_is_big(clan)
        and cat.ID not in biggest_family
    ):
        chance = int(chance * 0.8)

    # "regular" random fling
    if not int(random() * chance):
        possible_partners = [
            i
            for i in Cat.all_cats_list
            if i.is_potential_mate(cat, for_love_interest=True)
            and i.status.group_ID in [cat.status.group_ID, None]
            and (samesex or xor(cat_is_amab(i), cat_is_amab(cat)))
            and "sterile" not in i.permanent_condition
            and i.ID not in cat.mate
        ]

        # even it is a random affair, the cats should not hate each other or something like that
        p_affairs = []
        if len(possible_partners) > 0:
            for p_affair in possible_partners:
                if p_affair.ID in cat.relationships:
                    p_rel = cat.relationships[p_affair.ID]
                    if not p_rel.opposite_relationship:
                        p_rel.link_relationship()
                    p_rel_opp = p_rel.opposite_relationship
                    if p_rel_opp.like > -20 and p_rel.like > -20:
                        p_affairs.append(p_affair)
        possible_partners = p_affairs

        if len(possible_partners) > 0:
            chosen_affair = [choice(possible_partners)]
            return chosen_affair, True

    # no affair/coparent was found
    return mate, False

def handle_surrogate(cat, other_cats, clan):
    """
    Return the surrogate for a pregnancy
    """
    only_outside = get_clan_setting("only outside surrogates")
    only_clancat = get_clan_setting("only clan surrogates") and game.clan.clancount == "multiclan"
    only_clanmate = get_clan_setting("only inclan surrogates")
    mate = []

    # gather up mates to participate in the *selection* ig
    if len(cat.mate) > 0:
        mate_copy = cat.mate
        for x in mate_copy:
            mate.append(cat.fetch_cat(x))

    all_cats = [cat] + mate
    if other_cats[1:]:
        all_cats += other_cats[1:]

    all_cats = list(set(all_cats))

    backstories = {
        CatSocial.LONER : 'loner_backstories',
        CatSocial.ROGUE : 'rogue_backstories',
        CatSocial.KITTYPET: 'kittypet_backstories'
    }
    
    all_candidates = []
    for cand_cat in Cat.all_cats:
        cand_cat = Cat.all_cats.get(cand_cat)
        if (not cand_cat.dead and not cand_cat.status.is_lost() and not cand_cat.status.is_exiled(clan.group_ID) and
        not cand_cat in all_cats and "sterile" not in cand_cat.permanent_condition 
        and check_if_can_have_kits(cand_cat, True)
        and (get_clan_setting('same sex birth') or xor(cat_is_amab(cand_cat), cat_is_amab(cat)))):
            all_candidates.append(cand_cat)

    if (only_clanmate or randint(1, get_config("pregnancy.clanmate_surrogate_chance")) == 1) and not only_outside:
        candidates = []
        for cand in all_candidates:
            if cand.status.group_ID != cat.status.group_ID:
                continue
            possible = True
            for couple in all_cats:
                if not couple.is_potential_mate(cand, ignore_no_mates=True):
                    possible = False
                    break
                if x := couple.relationships.get(cand.ID):
                    if (x.romance + x.like + x.respect + x.trust + x.comfort) < 15:
                        possible = False
                        break
            if possible:
                candidates.append(cand)
        if candidates:
            return choice(candidates)
        elif only_clanmate:
            return None

    if only_clancat or random() < get_config("pregnancy.half-clan_chance"):
        candidates = []
        for cand in all_candidates:
            if not cand.status.group.is_any_clan_group() or cand.status.group_ID == cat.status.group_ID:
                continue
            possible = True
            for couple in all_cats:
                if not cand.is_potential_mate(couple, ignore_no_mates=True, outsider=True):
                    possible = False
                    break
            if possible:
                candidates.append(cand)

        if candidates:
            return choice(candidates)
        elif only_clancat:
            return None
    
    if random() < 0.25:
        candidates = []
        for cand in all_candidates:
            if cand.status.group.is_any_clan_group():
                continue
            possible = True
            for couple in all_cats:
                if not cand.is_potential_mate(couple, ignore_no_mates=True, outsider=True):
                    possible = False
                    break
            if possible:
                candidates.append(cand)

        if candidates:
            return choice(candidates)

    cat_type = choice(
        [CatSocial.LONER, CatSocial.ROGUE, CatSocial.KITTYPET])
    mate_age = cat.moons + randint(0, 24)-12
    outside_parent = None
    while not outside_parent or 'sterile' in outside_parent.permanent_condition:
        if outside_parent and Cat.all_cats[outside_parent.ID]:
            del Cat.all_cats[outside_parent.ID]
        outside_parent = create_new_cat(Cat,
                                        original_social=cat_type,
                                        backstory=BACKSTORIES["backstory_categories"][backstories[cat_type]],
                                        alive=True,
                                        moons=mate_age if mate_age > 14 else 15,
                                        gender=('fem' if cat_is_amab(cat) else 'masc') if not get_clan_setting('same sex birth') else None,
                                        outside=True,
                                        is_parent=True)[0]
        outside_parent.assign_thought(CatThought.OUTSIDE_SURROGATE)
    return outside_parent
    
def handle_outside_parent(cat, clan, amount=0, background_category= "1"):
    unknowns = []
    for outcat in Cat.all_cats:
        outcat = Cat.all_cats.get(outcat)
        if not outcat.dead and not outcat.status.is_lost(clan.group_ID) and (not outcat.status.is_exiled(clan.group_ID) or random() < 0.25):
            unknowns.append(outcat)

    possible_affair_partners = [i for i in unknowns if
                            i.is_potential_mate(cat, for_love_interest=True, outsider=True)
                            and check_if_can_have_kits(i)
                            and 'sterile' not in i.permanent_condition
                            and (get_clan_setting('same sex birth') or cat_is_amab(i) != cat_is_amab(cat))
                                and len(i.mate) == 0 and not i.birth_cooldown
                                and i.ID not in game.clan.pregnancy_data
                                and i.status.group_ID != cat.status.group_ID]
    outsider_affair_partners = [
        i for i in possible_affair_partners if not i.status.group.is_any_clan_group() and i.status.is_near()]
    other_clan_affair_partners = [
        i for i in possible_affair_partners if i.status.group.is_any_clan_group()]

    if (random() < get_config("pregnancy.half-clan_chance") or get_clan_setting("halfclan single")) and not get_clan_setting("outsiders single") and (game.clan.clancount == "singleclan" or len(other_clan_affair_partners)):
        backkit = f'halfclan{background_category}'
        outside_parent = None
        if other_clan_affair_partners and (random() < 0.25 or game.clan.clancount == "multiclan"):
            outside_parent = [choice(other_clan_affair_partners)]
        else:
            mate_age = cat.moons + randint(0, 24)-12
            outside_parent = create_new_cat(Cat,
                                            original_social=CatSocial.CLANCAT,
                                            backstory=BACKSTORIES["backstory_categories"].get(f"former_clancat_backstories", ["outsider1"]),
                                            alive=True,
                                            moons=mate_age if mate_age > 14 else 15,
                                            gender=('fem' if cat_is_amab(cat) else 'masc') if not get_clan_setting('same sex birth') else None,
                                            outside=True,
                                            is_parent=True)
        get_new_thought(outside_parent[0], CatThought.OUTSIDE_DAM if background_category == "2" else CatThought.OUTSIDE_SIRE, other_cat=cat)
        if random() < get_config("mates.crossclan_litter_mates_chance") and get_config("mates.allow_mating"):
            outside_parent[0].set_mate(cat)
            cat.set_mate(outside_parent[0])
    else:
        if get_clan_setting("halfclan single"):
            print("No possible half-clan single parents found")
            if background_category == "2":
                return None, None
        nr_of_parents = 1
        if background_category == "1" and get_clan_setting('multisire') and randint(1, get_config("pregnancy.multi-sire_chance")) == 1:
            nr_of_parents = randint(2, get_config("pregnancy.multi-sire_max_sires"))
        outside_parents = []
        for i in range(nr_of_parents):
            if (random() < 0.75 or (random() < 0.5 and i) or not outsider_affair_partners):
                cat_type = choice(
                    [CatSocial.LONER, CatSocial.ROGUE, CatSocial.KITTYPET])
                backstories = {
                    CatSocial.LONER: 'loner_backstories',
                    CatSocial.ROGUE: 'rogue_backstories',
                    CatSocial.KITTYPET: 'kittypet_backstories'
                }
                mate_age = cat.moons + randint(0, 24)-12
                outside_parent = None
                
                while not outside_parent or 'sterile' in outside_parent.permanent_condition:
                    if outside_parent and Cat.all_cats[outside_parent.ID]:
                        del Cat.all_cats[outside_parent.ID]
                    outside_parent = create_new_cat(Cat,
                                                    original_social=cat_type,
                                                    backstory=BACKSTORIES["backstory_categories"][backstories[cat_type]],
                                                    alive=True,
                                                    moons=mate_age if mate_age > 14 else 15,
                                                    gender=('fem' if cat_is_amab(cat) else 'masc') if not get_clan_setting('same sex birth') else None,
                                                    outside=True,
                                                    is_parent=True)[0]
                get_new_thought(outside_parent, CatThought.OUTSIDE_DAM if background_category == "2" else CatThought.OUTSIDE_SIRE, other_cat=cat)
                outside_parent.birth_cooldown = get_config("pregnancy.birth_cooldown")
                if random() < get_config("mates.outsider_litter_mates_chance") and get_config("mates.allow_mating"):
                    outside_parent.set_mate(cat)
                    cat.set_mate(outside_parent)

                outside_parents.append(outside_parent)

            else:
                par = choice(outsider_affair_partners)
                outside_parents.append(par)
                outsider_affair_partners.remove(par)
        backkit = f'outsider_roots{background_category}'
        outside_parent = outside_parents

    return [outside_parent, backkit]


def _determine_highest_romantic_relation(
    cat: Cat,
    mate: Optional[list[Cat]],
    relationship_with_mate: Optional[Relationship],
    same_sex_birth_allowed: bool,
) -> Optional[Cat]:
    """
    Function to handle everything around unmated affairs.
    Will return a second parent if triggerd, and none otherwise.
    """

    highest_romantic_relation = get_highest_romantic_relation(
        cat.relationships.values(), exclude_mate=True, potential_mate=True
    )

    # AFFAIR
    if mate and highest_romantic_relation:
        # Love affair calculation when the cat has a mate
        love_affair_chance = _get_love_affair_chance(
            relationship_with_mate, highest_romantic_relation
        )
        if not love_affair_chance or not int(random() * love_affair_chance):
            if (
                same_sex_birth_allowed
                or xor(cat_is_amab(cat), cat_is_amab(highest_romantic_relation.cat_to))
            ):
                return highest_romantic_relation.cat_to
    # COPARENTING
    elif highest_romantic_relation:
        # Love affair chance if the cat doesn't have a mate:
        coparenting_chance = _get_unmated_coparenting_chance(highest_romantic_relation)
        if not coparenting_chance or not int(random() * coparenting_chance):
            if (
                same_sex_birth_allowed
                or xor(cat_is_amab(cat), cat_is_amab(highest_romantic_relation.cat_to))
            ):
                return highest_romantic_relation.cat_to

    return None


def _get_love_affair_chance(mate_relation: Relationship, affair_relation: Relationship):
    """Looks into the current values and calculate the chance of having kits with the affair cat.
    The lower, the more likely they will have affairs. This function should only be called when mate
    and affair_cat are not the same.

    Returns:
        integer (number)
    """
    if not mate_relation.opposite_relationship:
        mate_relation.link_relationship()

    if not affair_relation.opposite_relationship:
        affair_relation.link_relationship()

    average_mate_love = (
        mate_relation.romance + mate_relation.opposite_relationship.romance
    ) / 2
    average_affair_love = (
        affair_relation.romance + affair_relation.opposite_relationship.romance
    ) / 2

    difference = average_mate_love - average_affair_love

    if difference < 0:
        # If the average love between affair partner is greater than the average love between the mate
        affair_chance = 10
        difference = -difference

        if difference > 30:
            affair_chance -= 7
        elif difference > 20:
            affair_chance -= 6
        elif difference > 15:
            affair_chance -= 5
        elif difference > 10:
            affair_chance -= 4

    elif difference > 0:
        # If the average love between the mate is greater than the average relationship between the affair
        affair_chance = 30

        if difference > 30:
            affair_chance += 8
        elif difference > 20:
            affair_chance += 5
        elif difference > 15:
            affair_chance += 3
        elif difference > 10:
            affair_chance += 5

    else:
        # For difference = 0 or some other weird stuff
        affair_chance = 15

    return affair_chance


def _get_unmated_coparenting_chance(relation: Relationship) -> int:
    """
    Calculates the chance of coparenting when neither the cat
    nor highest romantic relation have mates.
    """

    if not relation.opposite_relationship:
        relation.link_relationship()

    coparenting_chance = 15
    average_romantic_love = (
        relation.romance + relation.opposite_relationship.romance
    ) / 2

    if average_romantic_love > 50:
        coparenting_chance -= 12
    elif average_romantic_love > 40:
        coparenting_chance -= 10
    elif average_romantic_love > 30:
        coparenting_chance -= 7
    elif average_romantic_love > 10:
        coparenting_chance -= 5

    return coparenting_chance
