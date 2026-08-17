from scripts.cat.cats import Cat

biggest_family = {}

def set_biggest_family(clan):
    """Gets the biggest family of the clan."""
    global biggest_family
    big_family = []
    for cat in Cat.all_cats.values():
        if cat.status.group_ID != clan.group_ID:
            continue
        ancestors = list(cat.get_relatives())
        if not ancestors:
            continue
        if not big_family:
            big_family = ancestors
            big_family.append(cat.ID)
        elif len(big_family) < len(ancestors) + 1:
            big_family = ancestors
            big_family.append(cat.ID)
    biggest_family[clan.group_ID] = big_family


def get_biggest_family(clan) -> dict:
    if clan.group_ID not in biggest_family:
        set_biggest_family(clan)

    return biggest_family[clan.group_ID]


def biggest_family_is_big(clan):
    """Returns if the current biggest family is big enough to 'activates' additional inbreeding counters."""

    living_cats = len(
        [i for i in Cat.all_cats.values() if i.status.group_ID == clan.group_ID]
    )
    return len(biggest_family[clan.group_ID]) > (living_cats / 10)
