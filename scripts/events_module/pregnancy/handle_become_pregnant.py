from random import randint, choice, choices, random
from typing import Optional, List
from copy import copy

import i18n

from scripts.config import get_config
from scripts.cat.cats import Cat
from scripts.clan_package.settings import get_clan_setting
from scripts.cat.microservices.conditions import get_injured
from scripts.event_class import Single_Event
from scripts.events_module.pregnancy.build_strings import (
    get_pregnancy_strings,
)
from scripts.events_module.pregnancy.create_kits import get_amount_of_kits, get_stillborn_chance, get_kits
from scripts.events_module.pregnancy.check_parents import cat_is_amab, handle_surrogate, handle_outside_parent, no_kits_allowed
from scripts.events_module.text_adjust import event_text_adjust
from scripts.game_structure import game


def handle_zero_moon_pregnant(cat: Cat, other_cat=None, surrogate=False, clan=game.clan):
    """Handles if the cat is zero moons pregnant."""

    if other_cat:
        other_cat_copy = []
        for x in other_cat:
            if not (x.dead or x.status.is_lost() or x.status.is_exiled(clan.group_ID) or x.birth_cooldown > 0 or no_kits_allowed(x) or "sterile" in x.permanent_condition):
                other_cat_copy.append(x)
        other_cat = other_cat_copy

    if other_cat != None and not other_cat:
        return

    if cat.ID in game.clan.pregnancy_data:
        return

    if other_cat:
        for x in other_cat:
            if x.ID in game.clan.pregnancy_data:
                return

    hidden = get_config("pregnancy.hidden_pregnancy_chance") and not (random() * (get_config("pregnancy.hidden_pregnancy_chance")-1))
    birth_cooldown = get_config("pregnancy.birth_cooldown")

    if get_clan_setting("same sex birth") and not (not other_cat and randint(0, 1)):
        # same sex birth enables all cats to get pregnant,
        # therefore the main cat will be used, regarding of gender
        _handle_pregnancy_notice(cat, other_cat, surrogate, hidden, clan)
    else:
        if (not other_cat or surrogate) and cat_is_amab(cat):
            _retrieve_secret_kittens(cat, other_cat, surrogate, clan)
            return

        # if the other cat is afab and the current cat is amab, make the afab cat pregnant
        pregnant_cat = cat
        second_parent = other_cat
        second_parent_copy = copy(second_parent)
        if second_parent:
            for x in second_parent_copy:
                if cat_is_amab(pregnant_cat) and not cat_is_amab(x):
                    second_parent.append(pregnant_cat)
                    second_parent.remove(x)
                    pregnant_cat = x
                    break

        _handle_pregnancy_notice(pregnant_cat, second_parent, surrogate, hidden, clan)


def _handle_pregnancy_notice(cat, other_cat, surrogate, hidden, clan):
    allow_affair = get_clan_setting("affair")
    allow_coparenting = get_clan_setting("unmated parentage")

    ids = []
    affair_partner = []
    surrogates = []
    if other_cat:
        if surrogate:
            surrogates.append(other_cat[0].ID)
        for x in other_cat:
            if cat.mate and x.ID not in cat.mate:
                affair_partner.append(x.ID)
            else:
                ids.append(x.ID)
    if surrogate:
        affair_partner = []

    mate = []
    afab_mate = []
    amab_mate = []
    # afab/amab only matters if same sex setting is off
    if get_clan_setting("same sex birth"):
        mate = [
            Cat.fetch_cat(mate_id)
            for mate_id in cat.mate
            if Cat.fetch_cat(mate_id)
        ]
    else:
        for mate_id in cat.mate:
            mate_cat = Cat.fetch_cat(mate_id)
            mate.append(mate_cat)

            if not cat_is_amab(mate_cat):
                afab_mate.append(mate_cat)
            else:
                amab_mate.append(mate_cat)
    if cat.status.group_ID != clan.group_ID:
        clan = cat.status.fetch_clan_object(game.clan)

    _create_pregnancy_data(cat, ids, affair_partner, surrogates, hidden)

    if not hidden:
        # if both cats are faithful to each other and aren't cheaters,
        # the pregnancy will be announced as normal
        if not affair_partner and mate:
            text, involved_cats = _create_pregnancy_announcement(
                cat, "announcement", clan, random_cat=choice(mate)
            )
        # if the pregnant cat is single and had a fling with a random cat, let them
        # announce their surprise pregnancy and leave the Clan and player pointing
        # fingers on who the second parent may be
        elif not mate:
            text, involved_cats = _create_pregnancy_announcement(
                cat, "announcement_surprise", clan
            )
        # if the pregnant cat is in a same-sex relationship and they get knocked-up
        # by another cat, let there be some drama for that!
        elif (
            affair_partner
            and not amab_mate and not get_clan_setting("same sex birth")
        ):
            random_cat = choice(afab_mate) if afab_mate else None
            text, involved_cats = _create_pregnancy_announcement(
                cat,
                "announcement_affair_samesex",
                clan,
                random_cat=random_cat,
            )
        # and lastly, if the pregnant cat got knocked up by another cat who ISN'T their mate,
        # let the player guess whether it's an affair or not, sometimes the events will tell you,
        # sometimes they won't...
        elif (
            affair_partner
            and amab_mate
        ):
            announcement_key = choice(["announcement_affair", "announcement"])
            _set_affair_visibility(cat, announcement_key == "announcement_affair")
            random_cat = choice(amab_mate) if amab_mate else None
            text, involved_cats = _create_pregnancy_announcement(cat, announcement_key, clan, random_cat=random_cat)
        # if all else fails, just a regular announcement happens
        else:
            text, involved_cats = _create_pregnancy_announcement(cat, "announcement", clan, random_cat=choice(other_cat))
        game.cur_events_list.append(
            Single_Event(
                text, "birth_death", involved_cats, clan=clan.group_ID
            )
        )
    else:
        get_injured(cat, "pregnant", severity="minor")


def _create_pregnancy_data(pregnant_cat: Cat, second_parent: Optional[Cat], affair_partner: Optional[list[Cat]], surrogate: Optional[list[Cat]], hidden=False):
    """Creates the pregnancy data entry for a new pregnancy."""
    fever = False
    if len(pregnant_cat.illnesses) > 0:
        for illness in pregnant_cat.illnesses:
            if illness in ["greencough", "redcough", "yellowcough", "whitecough",
                            "an infected wound", "a festering wound", "ear infection",
                            "carrionplace disease", "heat stroke", "heat exhaustion", "tick fever"] and random() < 0.25:
                fever = True

    game.clan.pregnancy_data[pregnant_cat.ID] = {
        "second_parent": second_parent if second_parent else None,
        "affair_partner": affair_partner if affair_partner else None,
        "surrogate": surrogate if surrogate else None,
        "moons": 0,
        "amount": 0,
        "fever_coat": fever,
        "hidden": hidden
    }


def _retrieve_secret_kittens(cat, other_cat, surrogate, clan):
    amount = get_amount_of_kits(cat)
    stillborn_chance = get_stillborn_chance(amount)
    birth_cooldown = get_config("pregnancy.birth_cooldown")

    if surrogate:
        other_cat[0].birth_cooldown = birth_cooldown
        backkit = None
    else:
        outside_parent, backkit = handle_outside_parent(cat, clan, amount, "2")
        if outside_parent is None:
            return

    pregnant_cat = None
    if surrogate:
        pregnant_cat = other_cat[0]
    if surrogate and pregnant_cat.status.group_ID == cat.status.group_ID:
        text, involved_cats = _create_pregnancy_announcement(
            pregnant_cat, "announcement_surrogate", clan, random_cat=cat
        )
        game.cur_events_list.append(Single_Event(text, "birth_death", cats_involved=involved_cats, clan=clan.group_ID))
        
        ids = [cat.ID]
        if get_clan_setting('multisire'):
            for c in other_cat:
                if c != pregnant_cat:
                    ids.append(c.ID)
        
        _create_pregnancy_data(pregnant_cat, ids, None, [pregnant_cat.ID], False)
        return

    kits = get_kits(amount, cat, outside_parent if not surrogate else [pregnant_cat], clan, backkit=backkit, surrogate=[pregnant_cat] if surrogate else None)

    for kit in kits:
        if surrogate:
            kit.surrogate_parents.append(pregnant_cat.ID)
        if cat.mate and other_cat:
            for x in other_cat:
                if x.ID not in cat.mate and x.ID not in kit.surrogate_parents:
                    kit.affair_parents.append(x.ID)
        if random() < stillborn_chance or kit.phenotype.sexgene[0] == "Y" or kit.phenotype.manx[1] == "Ab" or kit.phenotype.manx[1] == "M" or kit.phenotype.munch[1] == "Mk" or ('NoDBE' not in kit.phenotype.pax3 and 'DBEalt' not in kit.phenotype.pax3):
            if not kit.dead:
                kit.dead = True
            kit.moons = 0
            kit.history.add_death(i18n.t(
                "cat.history.stillbirth",
                name=(kit.name),
            ))
            kits.remove(kit)

    if len(kits) > 0:
        cats_involved = [cat.ID]
        cat.birth_cooldown = birth_cooldown
        if surrogate:
            cats_involved.append(pregnant_cat.ID)
            
            get_injured(pregnant_cat, "recovering from birth", event_triggered=True)
            pregnant_cat.injuries["recovering from birth"]["risks"] = []
            print_event = i18n.t(
                "conditions.pregnancy.outside_surrogate_dam",
                name=cat.name,
                insert=i18n.t("conditions.pregnancy.kit_amount", count=len(kits)),
            )
            for p in cat.mate:
                par = Cat.fetch_cat(p)
                par.birth_cooldown = birth_cooldown
        else:
            print_event = i18n.t(
                "conditions.pregnancy.pregnant_secret",
                name=cat.name,
                insert=i18n.t("conditions.pregnancy.kit_amount", count=len(kits)),
            )
            if outside_parent:
                for par in outside_parent:
                    if par:
                        cats_involved.append(par.ID)
                        par.birth_cooldown = birth_cooldown
                        get_injured(par, "recovering from birth", event_triggered=True)
                        par.injuries["recovering from birth"]["risks"] = []
                        if par.status.group_ID != cat.status.group_ID and not par.status.is_outsider:
                            events = get_pregnancy_strings()
                            secondary_event = choice(events["birth"]["otherclan_mother"])
                            secondary_event = event_text_adjust(Cat, secondary_event, main_cat=par)
                            game.cur_events_list.append(Single_Event(secondary_event, "birth_death", cats_involved=cats_involved, clan=par.status.group_ID))
        for kit in kits:
            cats_involved.append(kit.ID)
        game.cur_events_list.append(Single_Event(print_event, "birth_death", cats_involved=cats_involved, clan=clan.group_ID))


def _create_pregnancy_announcement(
    pregnant_cat: Cat,
    announcement_key: str,
    clan,
    random_cat: Optional[Cat] = None,
    mentioned_cat: Optional[Cat] = None,
    force_minor=False,
):
    """Creates announcement text, applies pregnancy injury, and returns involved cats."""
    text = choice(get_pregnancy_strings()[announcement_key])
    event_text = text
    severity = choices(["minor", "major"], [3, 1], k=1)[0] if not force_minor else "minor"
    get_injured(pregnant_cat, "pregnant", severity=severity)
    text += choice(get_pregnancy_strings()[f"{severity}_severity"])
    text = event_text_adjust(
        Cat,
        text,
        main_cat=pregnant_cat,
        random_cat=random_cat,
        clan=clan,
    )
    involved_cats = [pregnant_cat.ID]
    involved_cats = _append_second_parent_if_mentioned(
        involved_cats, event_text, mentioned_cat or random_cat
    )
    return text, involved_cats


def _append_second_parent_if_mentioned(
    involved_cats: List[str], event_text: str, mentioned_cat: Optional[Cat]
) -> List[str]:
    """
    Appends the second parent/mate ID only if the event text mentions r_c.
    :param involved_cats: the cats involved in the invent, usually the first and second parent

    :return: involved_cats dict with mentioned_cat included if needed
    """
    if mentioned_cat and "r_c" in event_text and mentioned_cat.ID not in involved_cats:
        involved_cats.append(mentioned_cat.ID)
    return involved_cats


def _set_affair_visibility(
    cat: Optional[Cat] = False,
    is_affair_known: Optional[bool] = False,
    pregnant_cat: Optional[Cat] = False,
):
    """Store whether an affair was explicitly announced in pregnancy data."""
    target_cat = cat or pregnant_cat
    if not target_cat or not game.clan:
        return
    pregnancy = game.clan.pregnancy_data.get(target_cat.ID)
    if pregnancy is None:
        return
    pregnancy["affair_known"] = is_affair_known
