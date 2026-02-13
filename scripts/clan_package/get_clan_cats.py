from typing import Union, Type, TYPE_CHECKING, Tuple, List

if TYPE_CHECKING:
    from scripts.cat.cats import Cat
from scripts.cat.enums import CatGroup
import i18n


def get_alive_clan_queens(living_cats, clan: CatGroup = CatGroup.PLAYER_CLAN_ID):
    living_kits = [
        cat
        for cat in living_cats
        if cat.status.group_ID == clan and cat.status.rank.is_baby()
    ]

    queen_dict = {}
    for cat in living_kits.copy():
        parents = cat.get_parents()
        # Fetch parent object, only alive and not outside.
        parents = [
            cat.fetch_cat(i)
            for i in parents
            if cat.fetch_cat(i) and cat.fetch_cat(i).status.group_ID == clan
        ]
        if not parents:
            continue

        if (
            len(parents) == 1
            or len(parents) > 2
            or all('Y' in i.phenotype.sexgene for i in parents)
            or 'Y' not in parents[0].phenotype.sexgene
        ):
            if parents[0].ID in queen_dict:
                queen_dict[parents[0].ID].append(cat)
                living_kits.remove(cat)
            else:
                queen_dict[parents[0].ID] = [cat]
                living_kits.remove(cat)
        elif len(parents) == 2:
            if parents[1].ID in queen_dict:
                queen_dict[parents[1].ID].append(cat)
                living_kits.remove(cat)
            else:
                queen_dict[parents[1].ID] = [cat]
                living_kits.remove(cat)
    return queen_dict, living_kits


def find_alive_cats_with_rank(
    Cat: Union["Cat", Type["Cat"]],
    ranks: list,
    working: bool = False,
    sort: bool = False,
    clan: CatGroup = CatGroup.PLAYER_CLAN_ID
) -> list:
    """
    returns a list of cat objects for all living cats with a listed rank in Clan
    :param Cat Cat: Cat class
    :param list ranks: list of ranks to search for
    :param bool working: default False, set to True if you would like the list to only include working cats
    :param bool sort: default False, set to True if you would like list sorted by descending moon age
    """

    alive_cats = [
        i
        for i in Cat.all_cats.values()
        if i.status.rank in ranks and i.status.group_ID == clan
    ]

    if working:
        alive_cats = [i for i in alive_cats if not i.not_working()]

    if sort:
        alive_cats = sorted(alive_cats, key=lambda cat: cat.moons, reverse=True)

    return alive_cats


def get_living_clan_cat_count(Cat, clan=CatGroup.PLAYER_CLAN_ID):
    """
    Returns the int of all living cats within the Clan
    :param Cat: Cat class
    """
    count = 0
    for the_cat in Cat.all_cats.values():
        if the_cat.status.group_ID != clan:
            continue
        count += 1
    return count


def get_cats_same_age(Cat, cat, age_range=10):
    """
    Look for all cats in the Clan and returns a list of cats which are in the same age range as the given cat.
    :param Cat: Cat class
    :param cat: the given cat
    :param int age_range: The allowed age difference between the two cats, default 10
    """
    cats = []
    for inter_cat in Cat.all_cats.values():
        if inter_cat.status.group_ID != cat.status.group_ID:
            continue
        if inter_cat.ID == cat.ID:
            continue

        if inter_cat.ID not in cat.relationships:
            cat.create_one_relationship(inter_cat)
            if cat.ID not in inter_cat.relationships:
                inter_cat.create_one_relationship(cat)
            continue

        if (
            inter_cat.moons <= cat.moons + age_range
            and inter_cat.moons <= cat.moons - age_range
        ):
            cats.append(inter_cat)

    return cats


def get_possible_mates(cat) -> Tuple[List["Cat"], List["Cat"]]:
    """
    Returns a list of available cats which are possible mates for the given cat,
    and a second list of cats that are possible mates with pre-existing romantic interest.
    :param cat: The cat
    :return: possible mates and possible mates with existing romantic interest
    """
    possible_mates = []
    existing_romance_mates = []
    for inter_cat in cat.all_cats.values():
        if inter_cat.status.group_ID != cat.status.group_ID:
            continue
        if inter_cat.ID == cat.ID:
            continue

        if inter_cat.ID not in cat.relationships:
            cat.create_one_relationship(inter_cat)
            if cat.ID not in inter_cat.relationships:
                inter_cat.create_one_relationship(cat)
            continue

        if inter_cat.is_potential_mate(cat, for_love_interest=True):
            if cat.relationships[inter_cat.ID].romance > 0:
                existing_romance_mates.append(inter_cat)
            possible_mates.append(inter_cat)
    return possible_mates, existing_romance_mates


def search_cats(search_text, cat_list, search_genotype):
    search_text = search_text.strip()
    all_found = cat_list.copy()
    if search_text not in ["", i18n.t("general.name_search"), i18n.t("general.genotype_search")]:
        if search_genotype:
            gene_map = {
                "furLength": ["L", "l"],
                "eumelanin": ["B", "b", "bl"],
                "sexgene": ["O", "o", "Y"],
                "dilute": ["D", "d"],
                "white": ["W", "ws", "w", "wt", "wg", "wsal"],
                "pointgene": ["C", "cb", "cs", "cm", "c"],
                "silver": ["I", "i"],
                "agouti": ["A", "Apb", "a"],
                "mack": ["Mc", "mc"],
                "ticked": ["Ta", "ta"],

                "wirehair": ["Wh", "wh"],
                "laperm": ["Lp", "lp"],
                "cornish": ["R", "r"],
                "urals": ["Ru", "ru"],
                "tenn": ["Tr", "tr"],
                "fleece": ["Fc", "fc"],
                "sedesp": ["Se", "Hr", "Re", "se", "hr", "re"],
                "ruhr": ["Hrbd", "hrbd"],
                "ruhrmod": ["hi", "ha"],
                "lykoi": ["Ly", "ly"],

                "pinkdilute": ["Dp", "dp"],
                "dilutemd": ["Dm", "dm"],
                "ext": ["Eg", "E", "ea", "er", "ec"],
                "corin": ["N", "sh", "sg", "fg"],
                "karp": ["K", "k"],
                "bleach": ["Lb", "lb"],
                "ghosting": ["Gh", "gh"],
                "satin": ["St", "st"],
                "glitter": ["Gl", "gl"],

                "curl": ["Cu", "cu"],
                "fold": ["Fd", "fd"],
                "fourear": ["Dup", "dup"],
                "manx": ["M", "Ab", "m", "ab"],
                "kab": ["Kab", "kab"],
                "toybob": ["Tb", "tb"],
                "jbob": ["Jb", "jb"],
                "kub": ["Kub", "kub"],
                "ring": ["Rt", "rt"],
                "munch": ["Mk", "mk"],
                "poly": ["Pd", "pd"],
                "pax3": ["NoDBE", "DBEre", "DBEalt", "DBEcel"],
            }
            polygenes = {
                "wbsum": ["wideband", "wb"],
                "rufsum": ["rufousing", "ruf"],
                "unders_rufsum": ["underbelly_rufousing", "underbelly_ruf"],
                "bengsum": ["bengal", "bm"],
                "soksum": ["sokoke", "sok"],
                "spotsum": ["spotted", "spot"],
                "ticksum": ["ticked_mod", "tick_md"],
                "saturation": ["saturation", "sat"],
                "refraction": ["refraction", "ref"],
                "pigmentation": ["pigmentation", "pig"],
                "whitegrade": ["whitegrade", "white_grade", "white"]
            }

            orgroups = search_text.split("/")
            all_found = []
            for g in orgroups:
                alleles = g.split("&")
                found_cats = cat_list.copy()
                for a in alleles:
                    a = a.strip()
                    find_poly = [
                        key for key, value in polygenes.items() if a.split(" ")[0].split(">")[0].split("<")[0].split("=")[0] in value]
                    if (">" in a or "<" in a or "=" in a) and find_poly:
                        poly = find_poly[0]
                        operator = None
                        if "<=" in a:
                            operator = "<="
                        elif ">=" in a:
                            operator = ">="
                        elif "<" in a:
                            operator = "<"
                        elif ">" in a:
                            operator = ">"
                        elif ">" in a:
                            operator = ">"
                        elif "=" in a:
                            operator = "="
                        poly_value = a.split(operator, 1)[-1].strip()

                        if poly_value.isdigit():
                            if operator == "<=":
                                found_cats = [
                                    cat
                                    for cat in found_cats
                                    if cat.phenotype[poly] <= int(poly_value) or (cat.chimerapheno and cat.chimerapheno[poly] <= int(poly_value))
                                ]
                            elif operator == ">=":
                                found_cats = [
                                    cat
                                    for cat in found_cats
                                    if cat.phenotype[poly] >= int(poly_value) or (cat.chimerapheno and cat.chimerapheno[poly] >= int(poly_value))
                                ]
                            elif operator == ">":
                                found_cats = [
                                    cat
                                    for cat in found_cats
                                    if cat.phenotype[poly] > int(poly_value) or (cat.chimerapheno and cat.chimerapheno[poly] > int(poly_value))
                                ]
                            elif operator == "<":
                                found_cats = [
                                    cat
                                    for cat in found_cats
                                    if cat.phenotype[poly] < int(poly_value) or (cat.chimerapheno and cat.chimerapheno[poly] < int(poly_value))
                                ]
                            elif operator == "=":
                                found_cats = [
                                    cat
                                    for cat in found_cats
                                    if cat.phenotype[poly] == int(poly_value) or (cat.chimerapheno and cat.chimerapheno[poly] == int(poly_value))
                                ]

                    allele = a.strip().strip("!")
                    find_gene = [
                        key for key, value in gene_map.items() if allele in value]
                    gene = find_gene[0] if len(find_gene) else None
                    if gene:
                        found_cats = [
                            cat
                            for cat in found_cats
                            if '!' not in a and (allele in cat.phenotype[gene] or
                                                 (cat.chimerapheno and allele in cat.chimerapheno[gene]))
                            or ('!' in a and allele not in cat.phenotype[gene] and
                                (not cat.chimerapheno or allele not in cat.chimerapheno[gene]))
                        ]
                all_found += found_cats
            all_found = list(set(all_found))
        else:
            all_found = [
                cat
                for cat in cat_list
                if search_text.lower() in str(cat.name).lower()
            ]
    return all_found
