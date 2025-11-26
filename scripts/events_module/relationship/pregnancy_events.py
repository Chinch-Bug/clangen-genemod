import random
from operator import xor
from random import choice, choices, randint, random, randrange
from copy import copy, deepcopy
from typing import Dict, List, Union, Optional

import i18n

from scripts.cat.cats import Cat
from scripts.cat.enums import CatAge, CatGroup, CatRank, CatSocial
from scripts.cat.genotype import Genotype
from scripts.cat.names import names, Name
from scripts.cat_relations.relationship import Relationship, RelType
from scripts.clan_package.settings import get_clan_setting
from scripts.event_class import Single_Event
from scripts.events_module.short.condition_events import Condition_Events
from scripts.game_structure import constants
from scripts.game_structure import game
from scripts.game_structure.localization import load_lang_resource
from scripts.game_structure.game.settings import game_setting_get
from scripts.utility import (
    create_new_cat,
    get_highest_romantic_relation,
    event_text_adjust,
    get_personality_compatibility,
    BACKSTORIES,
    change_relationship_values,
    find_alive_cats_with_rank,
    adjust_list_text,
    get_living_clan_cat_count,
)


class Pregnancy_Events:
    """All events which are related to pregnancy such as kitting and defining who are the parents."""

    biggest_family = {}
    PREGNANT_STRINGS: Optional[Dict[str, Union[List, Dict[str, List]]]] = {}
    currently_loaded_lang: str = None

    @staticmethod
    def rebuild_strings():
        if Pregnancy_Events.currently_loaded_lang == i18n.config.get("locale"):
            return
        Pregnancy_Events.PREGNANT_STRINGS = load_lang_resource(
            "conditions/pregnancy.json"
        )
        Pregnancy_Events.currently_loaded_lang = i18n.config.get("locale")

    @staticmethod
    def set_biggest_family(clan):
        """Gets the biggest family of the clan."""
        biggest_family = None
        for cat in Cat.all_cats.values():
            if cat.status.group_ID != clan.group_ID:
                continue
            ancestors = cat.get_relatives()
            if not biggest_family:
                biggest_family = ancestors
                biggest_family.append(cat.ID)
            elif len(biggest_family) < len(ancestors) + 1:
                biggest_family = ancestors
                biggest_family.append(cat.ID)
        Pregnancy_Events.biggest_family[clan.displayname] = biggest_family

    @staticmethod
    def biggest_family_is_big(clan):
        """Returns if the current biggest family is big enough to 'activates' additional inbreeding counters."""

        living_cats = len(
            [i for i in Cat.all_cats.values() if i.status.group_ID == clan.group_ID]
        )
        return len(Pregnancy_Events.biggest_family[clan.displayname]) > (living_cats / 10)

    @staticmethod
    def handle_pregnancy_age(clan):
        """Increase the moon for each pregnancy in the pregnancy dictionary"""
        for pregnancy_key in clan.pregnancy_data.keys():
            clan.pregnancy_data[pregnancy_key]["moons"] += 1

    @staticmethod
    def handle_having_kits(cat, clan):
        """Handles pregnancy of a cat."""
        if not clan:
            return

        if not Pregnancy_Events.biggest_family.get(clan.displayname):
            Pregnancy_Events.set_biggest_family(clan)

        # Handles if a cat is already pregnant
        if cat.ID in game.clan.pregnancy_data:
            moons = game.clan.pregnancy_data[cat.ID]["moons"]
            if moons == 1:
                Pregnancy_Events.handle_one_moon_pregnant(cat, clan)
                return
            if moons >= 2:
                Pregnancy_Events.handle_two_moon_pregnant(cat, clan)
                # events.ceremony_accessory = True
                return

        if cat.status.is_outsider or get_clan_setting("no_litters") or (game.clan.clancount == "singleclan" and cat.status.is_other_clancat):
            return

        # Handle birth cooldown outside of the check_if_can_have_kits function, so it only happens once
        # for each cat.
        if cat.birth_cooldown > 0:
            cat.birth_cooldown -= 1

        # Check if they can have kits.
        can_have_kits = Pregnancy_Events.check_if_can_have_kits(
            cat, get_clan_setting("single parentage"), get_clan_setting("affair")
        )
        if not can_have_kits:
            return

        # DETERMINE THE SECOND PARENT
        # check if there is a cat in the clan for the second parent
        second_parent, is_affair = Pregnancy_Events.get_second_parent(cat, game.clan)

        # check if the second_parent is not none and if they also can have kits
        can_have_kits, kits_are_adopted, second_parent = Pregnancy_Events.check_second_parent(
            cat,
            second_parent,
            get_clan_setting("single parentage"),
            get_clan_setting("affair"),
            get_clan_setting("same sex birth"),
            get_clan_setting("same sex adoption"),
            get_clan_setting("surrogates"),
        )
        if not can_have_kits:
            return
        elif not second_parent and not get_clan_setting("single parentage"):
            return

        chance = Pregnancy_Events.get_balanced_kit_chance(cat, second_parent if second_parent else None, is_affair, clan)
        
        All_Infertile = True
        if 'sterile' not in cat.permanent_condition:
            All_Infertile = False
        elif second_parent:
            for x in second_parent:
                if x != "Surrogate" and 'sterile' not in x.permanent_condition:
                    All_Infertile = False

        if not int(random() * chance):
            # If you've reached here - congrats, kits!
            if kits_are_adopted or ('sterile' in cat.permanent_condition and (not second_parent or second_parent[0] != "Surrogate")) or (second_parent and All_Infertile):
                Pregnancy_Events.handle_adoption(cat, second_parent, clan)
            else:
                surrogate = False
                if second_parent and second_parent[0] == "Surrogate":
                    x = 1
                    while 'sterile' in cat.permanent_condition:
                        cat = second_parent[x]
                        x += 1
                    if cat in second_parent:
                        second_parent.remove(cat)
                    second_parent[0] = Pregnancy_Events.handle_surrogate(cat, clan)
                    if not second_parent[0]:
                        return
                    else:
                        surrogate = True
                Pregnancy_Events.handle_zero_moon_pregnant(cat, second_parent, surrogate, clan)

        elif second_parent and second_parent[0] != "Surrogate" and not kits_are_adopted and constants.CONFIG["pregnancy"]["false_pregnancy_chance"] and not int(random() * (constants.CONFIG["pregnancy"]["false_pregnancy_chance"]-1)):
            Pregnancy_Events.rebuild_strings()
            if 'Y' in cat.phenotype.sexgene and not get_clan_setting("same sex birth"):
                return

            if cat.status.group_ID != clan.group_ID:
                clan = cat.status.fetch_clan_object(game.clan)
            
            text = choice(Pregnancy_Events.PREGNANT_STRINGS["announcement"])
            cat.get_injured("pregnant", severity="minor")
            cat.injuries["pregnant"]["duration"] = 1
            text += choice(Pregnancy_Events.PREGNANT_STRINGS[f"minor_severity"])
            text = event_text_adjust(Cat, text, main_cat=cat, clan=clan)
            game.cur_events_list.append(
                Single_Event(
                    text, "birth_death", cat.ID, clan=clan.group_ID
                )
            )

    # ---------------------------------------------------------------------------- #
    #                                 handle events                                #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def handle_adoption(cat: Cat, other_cat=None, clan=game.clan):
        """Handle if the there is no pregnancy but the pair triggered kits chance."""
        if other_cat:
            for x in other_cat:
                if not x.status.group.is_any_clan_group() or x.birth_cooldown > 0 or x.no_kits:
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
        
        amount = Pregnancy_Events.get_amount_of_kits(cat, game.clan)
        kits = Pregnancy_Events.get_kits(amount, None, None, clan, adoptive_parents=adoptive_parents)
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
        if other_cat:
            for x in other_cat:
                cats_involved.append(x.ID)
        for kit in kits:
            kit.thought = i18n.t("hardcoded.new_kit_thought", name=str(cat.name))
            cats_involved.append(kit.ID)

        # Normally, birth cooldown is only applied to cat who gave birth
        # However, if we don't apply birth cooldown to adoption, we get
        # too much adoption, since adoptive couples are using the increased two-parent
        # kits chance. We will only apply it to "cat" in this case
        # which is enough to stop the couple from adopting about within
        # the window.
        cat.birth_cooldown = constants.CONFIG["pregnancy"]["birth_cooldown"]

        game.cur_events_list.append(
            Single_Event(print_event, "birth_death", cats_involved=cats_involved, clan=clan.group_ID)
        )

    @staticmethod
    def handle_zero_moon_pregnant(cat: Cat, other_cat=None, surrogate=False, clan=game.clan):
        """Handles if the cat is zero moons pregnant."""

        if other_cat:
            other_cat_copy = []
            for x in other_cat:
                if not (x.dead or x.status.is_lost() or x.status.is_exiled(clan.group_ID) or x.birth_cooldown > 0 or x.no_kits):
                    other_cat_copy.append(x)
            other_cat = other_cat_copy
        
        if other_cat != None and len(other_cat) < 1:
            return

        if cat.ID in game.clan.pregnancy_data:
            return

        if other_cat:
            for x in other_cat:
                if x.ID in game.clan.pregnancy_data:
                    return
        
        # additional save for no kit setting
        if (cat and cat.no_kits):
            return

            
        hidden = constants.CONFIG["pregnancy"]["hidden_pregnancy_chance"] and not (random() * (constants.CONFIG["pregnancy"]["hidden_pregnancy_chance"]-1))

        Pregnancy_Events.rebuild_strings()

        if get_clan_setting("same sex birth") and not (not other_cat and randint(0,1)):
            # same sex birth enables all cats to get pregnant,
            # therefore the main cat will be used, regarding of gender
            ids = []
            affair_partner = []
            surrogates = []
            if other_cat:
                if surrogate:
                    surrogates.append(other_cat[0].ID)
                for x in other_cat:
                    if x.ID not in cat.mate:
                        affair_partner.append(x.ID) 
                    else:
                        ids.append(x.ID)
            if surrogate:
                affair_partner = []
            
            fever = False
            if len(cat.illnesses) > 0:
                for illness in cat.illnesses:
                    if illness in ["greencough", "redcough", "yellowcough", "whitecough", 
                    "an infected wound", "a festering wound", "ear infection",
                    "carrionplace disease", "heat stroke", "heat exhaustion", "tick fever"] and random() < 0.25:
                        fever = True

            game.clan.pregnancy_data[cat.ID] = {
                "second_parent": ids if other_cat else None,
                "affair_partner" : affair_partner if affair_partner else None,
                "surrogate" : surrogates if surrogate else None,
                "moons": 0,
                "amount": 0,
                "fever_coat": fever,
                "hidden": hidden
            }

            if not hidden:
                text = choice(Pregnancy_Events.PREGNANT_STRINGS["announcement"])
                severity = choices(["minor", "major"], [3, 1], k=1)
                cat.get_injured("pregnant", severity=severity[0])
                text += choice(Pregnancy_Events.PREGNANT_STRINGS[f"{severity[0]}_severity"])
                text = event_text_adjust(Cat, text, main_cat=cat, clan=clan)
                game.cur_events_list.append(
                    Single_Event(text, "birth_death", cat.ID, clan=clan.group_ID)
                )
            else:
                cat.get_injured("pregnant", severity="minor")
        else:
            if (not other_cat or surrogate) and 'Y' in cat.phenotype.sexgene:
        
                amount = Pregnancy_Events.get_amount_of_kits(cat, game.clan)
                stillborn_chance = 0

                if amount < 3:
                    stillborn_chance = constants.CONFIG['pregnancy']['stillborn_chances']['small']
                elif amount == 3:
                    stillborn_chance = constants.CONFIG['pregnancy']['stillborn_chances']['three']
                elif amount < 6:
                    stillborn_chance = constants.CONFIG['pregnancy']['stillborn_chances']['mid']
                elif amount < 9:
                    stillborn_chance = constants.CONFIG['pregnancy']['stillborn_chances']['big']
                else:
                    stillborn_chance = constants.CONFIG['pregnancy']['stillborn_chances']['large']

                if not (get_clan_setting("modded_kits")):
                    stillborn_chance = 0
                
                if surrogate:
                    other_cat[0].birth_cooldown = constants.CONFIG["pregnancy"]["birth_cooldown"]
                    backkit = None
                else:
                    outside_parent, backkit = Pregnancy_Events.handle_outside_parent(cat, clan, amount, "2")
                    if outside_parent is None:
                        return

                pregnant_cat = None
                if surrogate:
                    pregnant_cat = other_cat[0]
                if surrogate and pregnant_cat.status.group_ID == cat.status.group_ID:
                    cats_involved = [cat.ID, pregnant_cat.ID]
                    text = choice(Pregnancy_Events.PREGNANT_STRINGS["announcement"])
                    severity = choices(["minor", "major"], [3, 1], k=1)
                    text += choice(Pregnancy_Events.PREGNANT_STRINGS[f"{severity[0]}_severity"])
                    text = event_text_adjust(Cat, text, main_cat=pregnant_cat, clan=clan)
                    text += " " + i18n.t(
                            "conditions.pregnancy.inclan_surrogate_dam",
                            name=cat.name,
                            insert=pregnant_cat.name)
                    game.cur_events_list.append(Single_Event(text, "birth_death", cats_involved=cats_involved, clan=clan.group_ID))
                    
                    fever = False
                    ids = [cat.ID]
                    if get_clan_setting('multisire'):
                        for c in other_cat:
                            if c != pregnant_cat:
                                cats_involved.append(c.ID)
                                ids.append(c.ID)
                    if len(pregnant_cat.illnesses) > 0:
                        for illness in pregnant_cat.illnesses:
                            if illness in ["greencough", "redcough", "yellowcough", "whitecough", 
                            "an infected wound", "a festering wound", "ear infection",
                            "carrionplace disease", "heat stroke", "heat exhaustion", "tick fever"] and random() < 0.25:
                                fever = True

                    game.clan.pregnancy_data[pregnant_cat.ID] = {
                        "second_parent": ids,
                        "affair_partner" : None,
                        "surrogate" : [pregnant_cat.ID],
                        "moons": 0,
                        "amount": 0,
                        "fever_coat": fever
                    }
                    severity = choices(["minor", "major"], [3, 1], k=1)
                    pregnant_cat.get_injured("pregnant", severity=severity[0])
                    return

                kits = Pregnancy_Events.get_kits(amount, cat, outside_parent if not surrogate else [pregnant_cat], clan, backkit=backkit)

                for kit in kits:
                    if random() < stillborn_chance or kit.phenotype.manx[1] == "Ab" or kit.phenotype.manx[1] == "M" or kit.phenotype.munch[1] == "Mk" or ('NoDBE' not in kit.phenotype.pax3 and 'DBEalt' not in kit.phenotype.pax3):
                        kit.dead = True
                        kit.moons = 0
                        kit.history.add_death(i18n.t(
                            "cat.history.stillbirth",
                            name=(kit.name),
                        ))
                        kits.remove(kit)

                if len(kits) > 0:
                    cats_involved = [cat.ID]
                    cat.birth_cooldown = constants.CONFIG["pregnancy"]["birth_cooldown"]
                    if surrogate:
                        cats_involved.append(pregnant_cat.ID)
                        
                        pregnant_cat.get_injured("recovering from birth", event_triggered=True)
                        print_event = i18n.t(
                            "conditions.pregnancy.outside_surrogate_dam",
                            name=cat.name,
                            insert=i18n.t("conditions.pregnancy.kit_amount", count=len(kits)),
                        )
                        for p in cat.mate:
                            par = Cat.fetch_cat(p)
                            par.birth_cooldown = constants.CONFIG["pregnancy"]["birth_cooldown"]
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
                                    par.birth_cooldown = constants.CONFIG["pregnancy"]["birth_cooldown"]
                                    par.get_injured("recovering from birth", event_triggered=True)
                                    if par.status.group_ID != cat.status.group_ID and not par.status.is_outsider:
                                        Pregnancy_Events.rebuild_strings()
                                        events = Pregnancy_Events.PREGNANT_STRINGS
                                        secondary_event = choice(events["birth"]["otherclan_mother"])
                                        secondary_event = event_text_adjust(Cat, secondary_event, main_cat=par)
                                        game.cur_events_list.append(Single_Event(secondary_event, "birth_death", cats_involved=cats_involved, clan=par.status.group_ID))
                    for kit in kits:
                        cats_involved.append(kit.ID)
                    game.cur_events_list.append(Single_Event(print_event, "birth_death", cats_involved=cats_involved, clan=clan.group_ID))
                return

            # if the other cat is afab and the current cat is amab, make the afab cat pregnant
            pregnant_cat = cat
            second_parent = other_cat
            affair_partner = []
            surrogates = []
            second_parent_copy = copy(second_parent)
            if second_parent:
                for x in second_parent_copy:
                    if 'Y' in pregnant_cat.phenotype.sexgene and 'Y' not in x.phenotype.sexgene:
                        second_parent.append(pregnant_cat)
                        second_parent.remove(x)
                        pregnant_cat = x
                        break

                ids = []
                if surrogate:
                    surrogates.append(second_parent[0].ID)
                for x in second_parent:
                    if x.ID not in pregnant_cat.mate:
                        affair_partner.append(x.ID) 
                    else:
                        ids.append(x.ID)
                if surrogate:
                    affair_partner = []

            if pregnant_cat.status.group_ID != clan.group_ID:
                clan = pregnant_cat.status.fetch_clan_object(game.clan)

            fever = False
            if len(pregnant_cat.illnesses) > 0:
                for illness in pregnant_cat.illnesses:
                    if illness in ["greencough", "redcough", "yellowcough", "whitecough", 
                    "an infected wound", "a festering wound", "ear infection",
                    "carrionplace disease", "heat stroke", "heat exhaustion", "tick fever"] and random() < 0.25:
                        fever = True

            game.clan.pregnancy_data[pregnant_cat.ID] = {
                "second_parent": ids if second_parent else None,
                "affair_partner" : affair_partner if affair_partner else None,
                "surrogate" : surrogates if surrogate else None,
                "moons": 0,
                "amount": 0,
                "fever_coat": fever,
                "hidden": hidden
            }

            if not hidden:
                text = choice(Pregnancy_Events.PREGNANT_STRINGS["announcement"])
                severity = choices(["minor", "major"], [3, 1], k=1)
                pregnant_cat.get_injured("pregnant", severity=severity[0])
                text += choice(Pregnancy_Events.PREGNANT_STRINGS[f"{severity[0]}_severity"])
                text = event_text_adjust(Cat, text, main_cat=pregnant_cat, clan=clan)
                game.cur_events_list.append(
                    Single_Event(
                        text, "birth_death", pregnant_cat.ID, clan=clan.group_ID
                    )
                )
            else:
                pregnant_cat.get_injured("pregnant", severity="minor")
    

    @staticmethod
    def handle_one_moon_pregnant(cat: Cat, clan=game.clan):
        """Handles if the cat is one moon pregnant."""
        if cat.ID not in game.clan.pregnancy_data.keys():
            return

        # if the pregnant cat killed meanwhile, delete it from the dictionary
        if cat.dead:
            del game.clan.pregnancy_data[cat.ID]
            return

        amount = Pregnancy_Events.get_amount_of_kits(cat, game.clan, game.clan.pregnancy_data[cat.ID].get("hidden"))
        
        text = 'This should not appear (pregnancy_events.py)'

        # add the amount to the pregnancy dict
        game.clan.pregnancy_data[cat.ID]["amount"] = amount

        fever = game.clan.pregnancy_data[cat.ID].get('fever_coat', False)

        if len(cat.illnesses) > 0 and not fever:
            for illness in cat.illnesses:
                if illness in ["greencough", "redcough", "yellowcough", "whitecough", 
                "an infected wound", "a festering wound", "ear infection",
                "carrionplace disease", "heat stroke", "heat exhaustion"] and random() < 0.33:
                    game.clan.pregnancy_data[cat.ID]["fever_coat"] = True

        # if the cat is outside of the clan (or doesn't know about the pregnancy), they won't guess how many kits they will have
        if cat.status.is_outsider or game.clan.pregnancy_data[cat.ID].get("hidden"):
            return

        thinking_amount = choices(
            ["correct", "incorrect", "unsure"], [4, 1, 1], k=1
        )
        if amount <= 6:
            correct_guess = "small"
        else:
            correct_guess = "large"

        Pregnancy_Events.rebuild_strings()

        if thinking_amount[0] == "correct":
            if correct_guess == "small":
                text = Pregnancy_Events.PREGNANT_STRINGS["litter_guess"][0]
            else:
                text = Pregnancy_Events.PREGNANT_STRINGS["litter_guess"][1]
        elif thinking_amount[0] == "incorrect":
            if correct_guess == "small":
                text = Pregnancy_Events.PREGNANT_STRINGS["litter_guess"][1]
            else:
                text = Pregnancy_Events.PREGNANT_STRINGS["litter_guess"][0]
        else:
            text = Pregnancy_Events.PREGNANT_STRINGS["litter_guess"][2]

        try:
            if cat.injuries["pregnant"]["severity"] == "minor":
                cat.injuries["pregnant"]["severity"] = "major"
                text += choice(Pregnancy_Events.PREGNANT_STRINGS["major_severity"])
        except:
            print("Is this an old save? Cat does not have the pregnant condition")

        text = event_text_adjust(Cat, text, main_cat=cat, clan=cat.status.fetch_clan_object(game.clan))
        game.cur_events_list.append(
            Single_Event(text, "birth_death", cat_dict={"m_c": cat}, clan=clan.group_ID)
        )

    @staticmethod
    def handle_two_moon_pregnant(cat: Cat, clan=game.clan):
        """Handles if the cat is two moons pregnant."""
        if cat.ID not in game.clan.pregnancy_data.keys():
            return

        # if the pregnant cat is killed meanwhile, delete it from the dictionary
        if cat.dead:
            del game.clan.pregnancy_data[cat.ID]
            return

        involved_cats = [cat.ID]
        hidden = game.clan.pregnancy_data[cat.ID].get("hidden")

        kits_amount = game.clan.pregnancy_data[cat.ID]["amount"]
        FeverCoat = game.clan.pregnancy_data[cat.ID].get("fever_coat", False)
        stillborn_chance = 0
        if kits_amount == 0:  # safety check, sometimes pregnancies were ending up with 0 due to save rollbacks
            kits_amount = 1

        if kits_amount < 3:
            stillborn_chance = constants.CONFIG['pregnancy']['stillborn_chances']['small']
        elif kits_amount == 3:
            stillborn_chance = constants.CONFIG['pregnancy']['stillborn_chances']['three']
        elif kits_amount < 6:
            stillborn_chance = constants.CONFIG['pregnancy']['stillborn_chances']['mid']
        elif kits_amount < 9:
            stillborn_chance = constants.CONFIG['pregnancy']['stillborn_chances']['big']
        else:
            stillborn_chance = constants.CONFIG['pregnancy']['stillborn_chances']['large']
        
        if not (get_clan_setting('modded_kits')):
            stillborn_chance = 0

        other_cat_id = game.clan.pregnancy_data[cat.ID]["second_parent"]
        affair_partner_id = []
        affair_partners = []
        surrogate = []
        RandomAffair = None
        try:
            affair_partner_id = game.clan.pregnancy_data[cat.ID]["affair_partner"]
        except:
            affair_partner_id = []
        try:
            surrogate_id = game.clan.pregnancy_data[cat.ID]["surrogate"]
        except:
            surrogate_id = []

        # delete the cat out of the pregnancy dictionary
        del game.clan.pregnancy_data[cat.ID]

        pregnant_cat = cat

        other_cat = []
        if other_cat_id and isinstance(other_cat_id, list): 
            for id in other_cat_id:
                other_cat.append(Cat.all_cats.get(id))
        elif other_cat_id:
            other_cat.append(Cat.all_cats.get(other_cat_id))
            if other_cat == [None]:
                print("SECOND PARENT NOT FOUND! If you edited the pregnancy in, double check the ID, please")
                other_cat = None
        else:
            other_cat = None

        if surrogate_id:
            if not isinstance(surrogate_id, list):
                surrogate_id = [surrogate_id]
            for sur in surrogate_id:
                surrogate.append(Cat.all_cats.get(sur))

        if affair_partner_id:
            if not isinstance(affair_partner_id, list):
                affair_partner_id = [affair_partner_id]
            if not other_cat:
                other_cat = []
            for id in affair_partner_id:
                other_cat.append(Cat.all_cats.get(id))
                affair_partners.append(Cat.all_cats.get(id))
            if affair_partners:
                RandomAffair = choice(affair_partners)
        
        if (other_cat and None in other_cat) or (surrogate and None in surrogate) or (affair_partners and None in affair_partners):
            print("PARENT NOT FOUND! If you edited the pregnancy in, double check the IDs, please")
            other_cat = [c for c in other_cat if c] if other_cat else None
            affair_partners = [c for c in affair_partners if c] if affair_partners else None
            surrogate = [c for c in surrogate if c] if surrogate else None

        backkit = None
        
        if not other_cat:
            other_cat, backkit = Pregnancy_Events.handle_outside_parent(
                cat, clan, "1")
                
        kits = Pregnancy_Events.get_kits(kits_amount, pregnant_cat, other_cat if not surrogate or pregnant_cat in surrogate else surrogate, clan, backkit=backkit)
        kits_amount = len(kits)
        for kit in kits:
            if FeverCoat:
                kit.phenotype.fevercoat = True
                if kit.chimerapheno:
                    kit.chimerapheno.fevercoat = True
            if random() < stillborn_chance or kit.phenotype.manx[1] == "Ab" or kit.phenotype.manx[1] == "M" or kit.phenotype.munch[1] == "Mk" or ('NoDBE' not in kit.phenotype.pax3 and 'DBEalt' not in kit.phenotype.pax3):
                kit.moons = 0
                kit.dead = True
                kit.thoughts(just_died=True)
                kit.history.add_death(str(kit.name) + " was stillborn.")
        Pregnancy_Events.set_biggest_family(clan)
        
        if pregnant_cat.status.is_outsider:
            for kit in kits:
                kit.status.generate_new_status(
                    age=kit.age, social=cat.status.social, group_ID=cat.status.group_ID
                )
                kit.backstory = "outsider1"

                if pregnant_cat.status.is_exiled():
                    name = choice(names.names_dict["normal_prefixes"])
                    kit.name = Name(prefix=name, suffix="", cat=kit)

                    if get_clan_setting("modded names") and get_clan_setting("new prefixes") and random() > 0.25:
                        kit.name.give_prefix(kit, game.clan.biome, True)

                if other_cat and not other_cat[0].status.is_outsider:
                    kit.backstory = "outsider2"

                if pregnant_cat.status.is_outsider and not pregnant_cat.status.is_exiled(
                    clan.group_ID
                ):
                    kit.backstory = "outsider3"
                kit.relationships = {}
                kit.create_one_relationship(cat)

        insert = i18n.t("conditions.pregnancy.kit_amount", count=kits_amount)

        # Since cat has given birth, apply the birth cooldown.
        cat.birth_cooldown = constants.CONFIG["pregnancy"]["birth_cooldown"]
        if other_cat:
            for c in other_cat:
                c.birth_cooldown = constants.CONFIG["pregnancy"]["birth_cooldown"]
        if surrogate:
            for c in surrogate:
                c.birth_cooldown = constants.CONFIG["pregnancy"]["birth_cooldown"]

        Dead_Mate = False
        WhoDied = 0
        All_Mates_Outside = True
        Both_Unmated = True
        RandomChoice = None
        SurrogateBirth = False

        if other_cat:
            RandomChoice = choice(other_cat)
            while RandomChoice.ID == cat.ID:
                RandomChoice = choice(other_cat)
            for x in other_cat:
                if x.dead:
                    Dead_Mate = True
                    WhoDied = x
                if x.status.group_ID == cat.status.group_ID or not (x.status.is_lost() or x.status.is_exiled()):
                    All_Mates_Outside = False
                if len(x.mate) > 0:
                    Both_Unmated = False
        
        # choose event string
        # TODO: currently they don't choose which 'mate' is the 'blood' parent or not
        # change or leaf as it is?
        Pregnancy_Events.rebuild_strings()
        events = Pregnancy_Events.PREGNANT_STRINGS
        event_list = []

        if surrogate and cat in other_cat:
            if pregnant_cat.ID not in involved_cats:
                involved_cats.append(pregnant_cat.ID)
            involved_cats.append(RandomChoice.ID)
            if random() < 0.5:
                event_list.append(choice(events["birth"]["surrogate_birth"]))
            else:
                SurrogateBirth = True
                event_list.append(choice(events["birth"]["two_parents_surrogate"]))
        elif hidden:
            event_list.append(choice(events["birth"]["hidden_pregnancy"]))
        elif not cat.status.is_outsider and backkit:
            event_list.append(choice(events["birth"]["unmated_parent"]))
        elif cat.status.is_outsider:
            adding_text = choice(events["birth"]["outside_alone"])
            if other_cat and not All_Mates_Outside:
                adding_text = choice(events["birth"]["outside_in_clan"])
            event_list.append(adding_text)
        elif not Both_Unmated and not affair_partners and not Dead_Mate and not All_Mates_Outside:
            involved_cats.append(RandomChoice.ID)
            if surrogate:
                involved_cats.append(surrogate[0].ID)
            event_list.append(choice(events["birth"]["two_parents"]))
        elif not affair_partners and Dead_Mate or All_Mates_Outside:
            if WhoDied != 0:
                involved_cats.append(WhoDied.ID)
                RandomChoice = WhoDied
            event_list.append(choice(events["birth"]["dead_mate"]))
        elif len(cat.mate) < 1 and Both_Unmated and not Dead_Mate:
            involved_cats.append(RandomChoice.ID)
            event_list.append(choice(events["birth"]["both_unmated"]))
        elif (len(cat.mate) > 0 and affair_partners) or\
            (affair_partners and len(RandomAffair.mate) > 0 and cat.ID not in RandomAffair.mate and not RandomAffair.dead):
            involved_cats.append(RandomAffair.ID)
            RandomChoice = RandomAffair
            if len(cat.mate) > 0:
                event_list.append(choice(events["birth"]["affair_mated"]))
            else:
                event_list.append(choice(events["birth"]["affair"]))
        else:
            event_list.append(choice(events["birth"]["unmated_parent"]))

        involved_cats += [k.ID for k in kits]

        if game.clan.game_mode != "classic":
            try:
                death_chance = cat.injuries["pregnant"]["mortality"]
            except:
                death_chance = 40
        else:
            death_chance = 40
        if not int(
            random() * death_chance
        ):  # chance for a cat to die during childbirth
            possible_events = events["birth"]["death"]
            # just makin sure meds aren't mentioned if they aren't around or if they are a parent
            meds = find_alive_cats_with_rank(
                Cat, [CatRank.MEDICINE_CAT, CatRank.MEDICINE_APPRENTICE], sort=True, clan=clan.group_ID
            )
            mate_is_med = [mate_id for mate_id in cat.mate if mate_id in meds]
            if not meds or cat in meds or len(mate_is_med) > 0:
                for event in possible_events:
                    if CatRank.MEDICINE_CAT in event:
                        possible_events.remove(event)

            if cat.status.is_outsider:
                possible_events = events["birth"]["outside_death"]
            if clan.leader_lives > 1 and cat.status.is_leader:
                possible_events = events["birth"]["lead_death"]
            event_list.append(choice(possible_events))

            if cat.status.is_leader:
                clan.leader_lives -= 1
                cat.die()
                death_event = i18n.t("conditions.pregnancy.leader_kitting_death")
            else:
                cat.die()
                death_event = i18n.t(
                    "conditions.pregnancy.kitting_death", name=cat.name
                )
            cat.history.add_death(death_text=death_event)
        else:  # if cat doesn't die, give recovering from birth
            cat.get_injured("recovering from birth", event_triggered=True)
            if "blood loss" in cat.injuries:
                if cat.status.is_leader:
                    death_event = i18n.t(
                        "conditions.pregnancy.leader_kitting_death_severe"
                    )
                else:
                    death_event = i18n.t(
                        "conditions.pregnancy.kitting_death_harsh", name=cat.name
                    )
                cat.history.add_possible_history("blood loss", death_text=death_event)
                possible_events = events["birth"]["difficult_birth"]
                # just makin sure meds aren't mentioned if they aren't around or if they are a parent
                meds = find_alive_cats_with_rank(
                    Cat, [CatRank.MEDICINE_CAT, CatRank.MEDICINE_APPRENTICE], clan=clan.group_ID
                )
                mate_is_med = [mate_id for mate_id in cat.mate if mate_id in meds]
                if not meds or cat in meds or len(mate_is_med) > 0:
                    for event in possible_events:
                        if CatRank.MEDICINE_CAT in event:
                            possible_events.remove(event)

                event_list.append(choice(possible_events))
        if not cat.dead:
            # If they are dead in childbirth above, all condition are cleared anyway.
            try:
                cat.injuries.pop("pregnant")
            except:
                print(
                    "Is this an old save? Your cat didn't have the pregnant condition!"
                )
        if SurrogateBirth:
            cat = other_cat[0]
            event_list[0] = event_list[0].replace("{surrogate}", f"{pregnant_cat.name}")
            if len(event_list) > 1:
                event_list[0] = event_text_adjust(Cat, event_list[0], main_cat=cat, random_cat=RandomChoice, clan=clan)
                cat = pregnant_cat
        print_event = " ".join(event_list)
        print_event = print_event.replace("{insert}", insert)

        print_event = event_text_adjust(Cat, print_event, main_cat=cat, random_cat=RandomChoice, clan=clan)

        # display event
        game.cur_events_list.append(
            Single_Event(
                print_event, ["health", "birth_death"], involved_cats, clan=clan.group_ID
            )
        )

    # ---------------------------------------------------------------------------- #
    #                          check if event is triggered                         #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def check_if_can_have_kits(cat, single_parentage, allow_affair):
        """Check if the given cat can have kits, see for age, birth-cooldown and so on."""
        if not cat:
            return False

        if cat.birth_cooldown > 0:
            return False

        if "recovering from birth" in cat.injuries or "pregnant" in cat.injuries:
            return False

        # decide chances of having kits, and if it's possible at all.
        # Including - age, dead statis, having kits turned off.
        not_correct_age = (
            cat.age in [CatAge.NEWBORN, CatAge.KITTEN, CatAge.ADOLESCENT]
            or cat.moons < 15
        )
        if not_correct_age or cat.no_kits or cat.dead:
            return False

        # check for mate
        if len(cat.mate) > 0:
            for mate_id in cat.mate:
                if mate_id not in cat.all_cats:
                    print(
                        f"WARNING: {cat.name}  has an invalid mate # {mate_id}. This has been unset."
                    )
                    cat.mate.remove(mate_id)

        # If the "single parentage setting in on, we should only allow cats that have mates to have kits.
        if not single_parentage and len(cat.mate) < 1 and not allow_affair:
            return False

        # if function reaches this point, having kits is possible
        return True

    @staticmethod
    def check_second_parent(
        cat: Cat,
        second_parent: Cat,
        single_parentage: bool,
        allow_affair: bool,
        same_sex_birth: bool,
        same_sex_adoption: bool,
        surrogates: bool=False,
    ):
        """
        This checks to see if the chosen second parent and CAT can have kits. It assumes CAT can have kits.
        returns:
        parent can have kits, kits are adopted
        """

        if not second_parent:
            if single_parentage:
                return True, False, second_parent
            else:
                return False, False, second_parent
        elif len(second_parent) == 1:
        # Checks for second parent alone:
            if not Pregnancy_Events.check_if_can_have_kits(second_parent[0] if second_parent else None, single_parentage, allow_affair):
                return False, False, second_parent

            # Check to see if the pair can have kits.
            if not xor('Y' in cat.phenotype.sexgene, 'Y' in second_parent[0].phenotype.sexgene) or ("sterile" in cat.permanent_condition or "sterile" in second_parent[0].permanent_condition):
                if same_sex_birth and not "sterile" in second_parent[0].permanent_condition and not "sterile" in cat.permanent_condition:
                    return True, False, second_parent
                elif surrogates and not ("sterile" in second_parent[0].permanent_condition and "sterile" in cat.permanent_condition):
                    return True, False, ["Surrogate"] + second_parent
                elif not same_sex_adoption:
                    return False, False, second_parent
                else:
                    return True, True, second_parent
                    
            return True, False, second_parent
        else:
            second_parent_copy = []
            for x in second_parent:
                if Pregnancy_Events.check_if_can_have_kits(x, single_parentage, allow_affair) or x == None:
                    second_parent_copy.append(x)
            
            second_parent = second_parent_copy
            if len(second_parent) < 1:
                return False, False, second_parent

            second_parent_copy = []

            for x in second_parent:
                if (xor('Y' in cat.phenotype.sexgene, 'Y' in x.phenotype.sexgene) or same_sex_birth) and not "sterile" in x.permanent_condition:
                    second_parent_copy.append(x)
            
            if len(second_parent_copy) < 1:
                if surrogates:
                    return True, False, ["Surrogate"] + second_parent
                elif same_sex_adoption:
                    return True, True, second_parent
                else:
                    return False, False, second_parent
            if "sterile" in cat.permanent_condition:
                if surrogates:
                    return True, False, ["Surrogate"] + second_parent
                elif same_sex_adoption:
                    return True, True, second_parent
                else:
                    return False, False, second_parent
                
            return True, False, second_parent_copy



    # ---------------------------------------------------------------------------- #
    #                               getter functions                               #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def get_second_parent(cat, clan):
        """
        Return the second parent of a cat, which will have kits.
        Also returns a bool that is true if an affair was triggered.
        """
        samesex = get_clan_setting("same sex birth")
        allow_affair = get_clan_setting("affair")
        mate = None
    
        # randomly select a mate of given cat
        if len(cat.mate) > 0:
            mate = []
            if get_clan_setting('multisire'):
                mate_copy = cat.mate
                for x in mate_copy:
                    mate.append(cat.fetch_cat(x))
            else:
                mate.append(cat.fetch_cat(choice(cat.mate)))

        # if the sex does matter, choose the best solution to allow kits
        if not samesex and mate and 'Y' not in cat.phenotype.sexgene:
            opposite_mate = [cat.fetch_cat(mate_id) for mate_id in cat.mate if xor('Y' in cat.fetch_cat(mate_id).phenotype.sexgene, 'Y' in cat.phenotype.sexgene)]
            if len(opposite_mate) > 0:
                mate = opposite_mate
                if not get_clan_setting('multisire'):
                    mate = [choice(opposite_mate)]
        elif not samesex and mate and 'Y' in cat.phenotype.sexgene:
            opposite_mate = [cat.fetch_cat(mate_id) for mate_id in cat.mate if xor('Y' in cat.fetch_cat(mate_id).phenotype.sexgene, 'Y' in cat.phenotype.sexgene)]
            if len(opposite_mate) > 0:
                mate = [choice(opposite_mate)]
        

        if not allow_affair:
            # if affairs setting is OFF, second parent (mate) will be returned
            return mate, False

        # get relationships to influence the affair chance
        mate_relation = None
        if mate:
            for x in mate:
                rel = None
                if x.ID in cat.relationships:
                    rel = cat.relationships[x.ID]
                else:
                    continue

                if not mate_relation:
                    mate_relation = rel
                elif mate_relation.romance < rel.romance:
                    mate_relation = rel

        # LOVE AFFAIR
        # Handle love affair chance.
        affair_partner = Pregnancy_Events.determine_love_affair(cat, mate if mate else None, mate_relation if mate else None, samesex)
        if affair_partner:
            if mate and not get_clan_setting('multisire'):
                mate.append(affair_partner)
            else:
                mate = [affair_partner]
            return mate, True

        # RANDOM AFFAIR
        chance = constants.CONFIG["pregnancy"]["random_affair_chance"]
        special_affair = False
        if len(cat.mate) <= 0:
            # Special random affair check only for unmated cats. For this check, only
            # other unmated cats can be the affair partner.
            chance = constants.CONFIG["pregnancy"]["unmated_random_affair_chance"]
            special_affair = True

        # 'buff' affairs if the current biggest family is big + this cat doesn't belong there
        if not Pregnancy_Events.biggest_family.get(clan.displayname):
            Pregnancy_Events.set_biggest_family(clan)

        if (
            Pregnancy_Events.biggest_family_is_big(clan)
            and cat.ID not in Pregnancy_Events.biggest_family[clan.displayname]
        ):
            chance = int(chance * 0.8)

        # "regular" random affair
        if not int(random() * chance):
            possible_affair_partners = [
                i
                for i in Cat.all_cats_list
                if i.is_potential_mate(cat, for_love_interest=True)
                and i.status.group_ID in [cat.status.group_ID, None]
                and (samesex or xor('Y' in i.phenotype.sexgene, 'Y' in cat.phenotype.sexgene))
                and "sterile" not in i.permanent_condition
                and i.ID not in cat.mate
            ]
            if special_affair:
                possible_affair_partners = [
                    c for c in possible_affair_partners if len(c.mate) < 1
                ]

            # even it is a random affair, the cats should not hate each other or something like that
            p_affairs = []
            if len(possible_affair_partners) > 0:
                for p_affair in possible_affair_partners:
                    if p_affair.ID in cat.relationships:
                        p_rel = cat.relationships[p_affair.ID]
                        if not p_rel.opposite_relationship:
                            p_rel.link_relationship()
                        p_rel_opp = p_rel.opposite_relationship
                        if p_rel_opp.like > -20 and p_rel.like > -20:
                            p_affairs.append(p_affair)
            possible_affair_partners = p_affairs

            if len(possible_affair_partners) > 0:
                chosen_affair = [choice(possible_affair_partners)]
                return chosen_affair, True

        return mate, False

    @staticmethod
    def handle_surrogate(cat, clan):
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
            and Pregnancy_Events.check_if_can_have_kits(cand_cat, True, True)
            and (get_clan_setting('same sex birth') or xor('Y' in cand_cat.phenotype.sexgene, 'Y' in cat.phenotype.sexgene))):
                all_candidates.append(cand_cat)

        if (only_clanmate or randint(1, constants.CONFIG['pregnancy']['clanmate_surrogate_chance']) == 1) and not only_outside:
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
                        if (x.romance + x.like + x.respect + x.trust + x.comfort) < 5:
                            possible = False
                            break
                if possible:
                    candidates.append(cand)
            if candidates:
                return choice(candidates)
            elif only_clanmate:
                return None

        if only_clancat or random() < constants.CONFIG['pregnancy']['half-clan_chance']:
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
                                            gender='fem' if 'Y' in cat.phenotype.sexgene else 'masc',
                                            outside=True,
                                            is_parent=True)[0]
            outside_parent.thought = i18n.t("hardcoded.thought_outside_surrogate")
        return outside_parent
        
    @staticmethod
    def handle_outside_parent(cat, clan, amount=0, background_category= "1"):
        unknowns = []
        for outcat in Cat.all_cats:
            outcat = Cat.all_cats.get(outcat)
            if not outcat.dead and not outcat.status.is_lost(clan.group_ID) and not outcat.status.is_exiled(clan.group_ID):
                unknowns.append(outcat)

        possible_affair_partners = [i for i in unknowns if
                                i.is_potential_mate(cat, for_love_interest=True, outsider=True)
                                and Pregnancy_Events.check_if_can_have_kits(i, True, True)
                                and 'sterile' not in i.permanent_condition
                                and (get_clan_setting('same sex birth') or xor('Y' in i.phenotype.sexgene, 'Y' in cat.phenotype.sexgene))
                                    and len(i.mate) == 0 and not i.birth_cooldown
                                    and i.ID not in game.clan.pregnancy_data
                                    and i.status.group_ID != cat.status.group_ID]
        outsider_affair_partners = [
            i for i in possible_affair_partners if not i.status.group.is_any_clan_group() and i.status.is_near()]
        other_clan_affair_partners = [
            i for i in possible_affair_partners if i.status.group.is_any_clan_group()]

        if (random() < constants.CONFIG["pregnancy"]["half-clan_chance"] or get_clan_setting("halfclan single")) and not get_clan_setting("outsiders single") and (game.clan.clancount == "singleclan" or len(other_clan_affair_partners)):
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
                                                gender='fem' if 'Y' in cat.phenotype.sexgene else 'masc',
                                                outside=True,
                                                is_parent=True)
                outside_parent[0].thought = event_text_adjust(Cat, i18n.t(
                    "hardcoded.thought_outside_dam" if background_category == "2" else "hardcoded.thought_outside_sire", count=amount, name=str(cat.name)), main_cat=outside_parent[0])
            if random() < 0.2:
                outside_parent[0].set_mate(cat)
                cat.set_mate(outside_parent[0])
        else:
            if get_clan_setting("halfclan single"):
                print("No possible half-clan single parents found")
                if background_category == "2":
                    return None, None
            nr_of_parents = 1
            if background_category == "1" and get_clan_setting('multisire') and randint(1, constants.CONFIG['pregnancy']["multi-sire_chance"]) == 1:
                nr_of_parents = randint(2, constants.CONFIG['pregnancy']["multi-sire_max_sires"])
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
                                                        gender='fem' if 'Y' in cat.phenotype.sexgene else 'masc',
                                                        outside=True,
                                                        is_parent=True)[0]
                    outside_parent.thought = event_text_adjust(Cat, i18n.t(
                        "hardcoded.thought_outside_dam" if background_category == "2" else "hardcoded.thought_outside_sire", count=amount, name=str(cat.name)), main_cat=outside_parent)
                    outside_parent.birth_cooldown = constants.CONFIG["pregnancy"]["birth_cooldown"]
                    if random() < 0.1:
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

    @staticmethod
    def determine_love_affair(cat, mate, mate_relation, samesex):
        """
        Function to handle everything around love affairs.
        Will return a second parent if a love affair is triggerd, and none otherwise.
        """

        highest_romantic_relation = get_highest_romantic_relation(
            cat.relationships.values(), exclude_mate=True, potential_mate=True
        )

        if mate and mate_relation and highest_romantic_relation:
            # Love affair calculation when the cat has a mate
            chance_love_affair = Pregnancy_Events.get_love_affair_chance(
                mate_relation, highest_romantic_relation
            )
            if not chance_love_affair or not int(random() * chance_love_affair):
                if samesex or 'Y' in cat.phenotype.sexgene != 'Y' in highest_romantic_relation.cat_to.phenotype.sexgene:
                    return highest_romantic_relation.cat_to
        elif highest_romantic_relation:
            # Love affair change if the cat doesn't have a mate:
            chance_love_affair = Pregnancy_Events.get_unmated_love_affair_chance(
                highest_romantic_relation
            )
            if not chance_love_affair or not int(random() * chance_love_affair):
                if samesex or 'Y' in cat.phenotype.sexgene != highest_romantic_relation.cat_to.phenotype.sexgene:
                    return highest_romantic_relation.cat_to

        return None

    @staticmethod
    def get_kits(kits_amount, cat=None, other_cat=None, clan=game.clan, adoptive_parents=None, backkit=None):
        """Create some amount of kits
        No parents are specified, it will create a blood parents for all the
        kits to be related to. They may be dead or alive, but will always be outside
        the clan."""
        all_kitten = []
        if not adoptive_parents:
            adoptive_parents = []

        # First, just a check: If we have no cat, but an other_cat was provided,
        # swap other_cat to cat:
        # This way, we can ensure that if only one parent is provided,
        # it's cat, not other_cat.
        # And if cat is None, we know that no parents were provided.
        if other_cat and not cat:
            cat = other_cat
            other_cat = None

        blood_parent = None
        blood_parent2 = None
         
        par2geno = Genotype(constants.CONFIG['genetics_config'], game_setting_get("ban problem genes"))
        if cat and 'Y' in cat.phenotype.sexgene:
            par2geno.Generator('fem')
        elif cat:
            par2geno.Generator('masc')
        ##### SELECT BACKSTORY #####
        if cat and "pregnant" in cat.injuries and other_cat and other_cat[0].status.get_last_living_group() != cat.status.group_ID:
            backkit = 'halfclan1' if other_cat[0].status.group.is_any_clan_group() else 'outsider_roots1'
        elif cat and other_cat and other_cat[0].status.get_last_living_group() != cat.status.group_ID:
            backkit = 'halfclan2' if other_cat[0].status.group.is_any_clan_group() else 'outsider_roots2'
        if backkit:
            backstory = backkit
        else:  # cat is adopted
            backstory = choice(["abandoned1", "abandoned2", "abandoned3", "abandoned4"])
        ###########################

        ##### ADOPTIVE PARENTS #####
        # First, gather all the mates of the provided bio parents to be added
        # as adoptive parents.
        all_adoptive_parents = []
        
        all_pars = [cat]
        if other_cat:
            all_pars += other_cat
        birth_parents = [i.ID for i in all_pars if i]
        for _par in all_pars:
            if not _par:
                continue
            for _m in _par.mate:
                if _m not in birth_parents and _m not in all_adoptive_parents:
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
            if initial_amount < 3:
                stillborn_chance = constants.CONFIG['pregnancy']['stillborn_chances']['small']
            elif initial_amount == 3:
                stillborn_chance = constants.CONFIG['pregnancy']['stillborn_chances']['three']
            elif initial_amount < 6:
                stillborn_chance = constants.CONFIG['pregnancy']['stillborn_chances']['mid']
            elif initial_amount < 9:
                stillborn_chance = constants.CONFIG['pregnancy']['stillborn_chances']['big']
            else:
                stillborn_chance = constants.CONFIG['pregnancy']['stillborn_chances']['large']

            if not (get_clan_setting("modded_kits")):
                stillborn_chance = 0

            death_chances = constants.CONFIG['death_related']['kit_death_chances']
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
                # No parents provided, give a blood parent - this is an adoption.
                if not blood_parent:
                    # Generate a blood parent if we haven't already. 
                    nr_of_parents = 1
                    if get_clan_setting('multisire') and randint(1, constants.CONFIG['pregnancy']["multi-sire_chance"]) == 1:
                        nr_of_parents = randint(2, constants.CONFIG['pregnancy']["multi-sire_max_sires"])
                    
                    parage = randint(15,120)
                    cat_type = choice([CatSocial.LONER, CatSocial.ROGUE, CatSocial.KITTYPET])
                    blood_parent = create_new_cat(Cat,
                                                original_social=cat_type,
                                                gender='fem',
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
                            cat_type = choice([CatSocial.LONER, CatSocial.ROGUE, CatSocial.KITTYPET])
                            blood_par2 = create_new_cat(Cat,
                                                        original_social=cat_type,
                                                        gender='masc',
                                                        alive=choice([True, False]),
                                                        moons=parage if parage > 14 else 15,
                                                        outside=True,
                                                        is_parent=True)[0]
                        blood_parent2.append(blood_par2)

                sire = choice(blood_parent2)
                chimera_sire = choice(blood_parent2)
                kit_status = {"group_ID": clan.group_ID}
                kit_status["rank"] = CatRank.NEWBORN if litter_age == 0 else CatRank.KITTEN
                kit = Cat(parent1=blood_parent.ID, parent2=sire.ID, extrapar=chimera_sire if sire.ID != chimera_sire.ID else None, status_dict=kit_status, moons=litter_age, backstory=backstory)
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

                if backkit:    
                    kit = Cat(parent1=cat.ID, parent2=second_blood.ID if second_blood else None, moons=0, backstory=backstory, status_dict={"rank": CatRank.NEWBORN, "group_ID": clan.group_ID}, extrapar = chimera_sire)
                else:
                    kit = Cat(parent1=cat.ID, parent2=second_blood.ID, moons=0, status_dict={"rank": CatRank.NEWBORN, "group_ID": clan.group_ID})
                
                if 'Y' not in cat.phenotype.sexgene or not second_blood or second_blood.status.is_outsider:
                    kit.thought = i18n.t("hardcoded.new_kit_thought", name=str(cat.name))
                elif 'Y' in cat.phenotype.sexgene and 'Y' in cat.phenotype.sexgene:
                    kit.thought = i18n.t("hardcoded.new_kit_thought", name=str(cat.name))
                else:
                    kit.thought = i18n.t("hardcoded.new_kit_thought", name=str(second_blood.name))

            if identical:
                identical = False
                ref_cat = copy(all_kitten[-1])
                kit.permanent_condition = ref_cat.permanent_condition
                kit.phenotype = deepcopy(ref_cat.phenotype)    
                kit.phenotype.tortiepattern = None
                kit.phenotype.chimerapattern = None
                kit.phenotype.merlepattern = None
                kit.phenotype.white_pattern = kit.pelt.generate_white(kit.phenotype.white, kit.phenotype.pointgene, kit.phenotype.whitegrade, kit.phenotype.vitiligo, None, kit.phenotype.pax3)
                kit.phenotype.PhenotypeOutput(kit.phenotype.white_pattern)
                kit.phenotype.SpriteInfo(kit.moons)
                kit.pelt.length = ref_cat.pelt.length
                kit.pelt.tint = ref_cat.pelt.tint
                kit.pelt.white_patches_tint = ref_cat.pelt.white_patches_tint
                
                if ref_cat.chimerapheno:
                    kit.chimerapheno = deepcopy(ref_cat.chimerapheno)   
                    kit.chimerapheno.tortiepattern = None
                    kit.chimerapheno.chimerapattern = kit.chimerapheno.ChooseTortiePattern("chimera")
                    kit.chimerapheno.merlepattern = None
                    kit.chimerapheno.white_pattern = kit.pelt.generate_white(kit.chimerapheno.white, kit.chimerapheno.pointgene, kit.chimerapheno.whitegrade, kit.chimerapheno.vitiligo, None, kit.chimerapheno.pax3)
                    kit.chimerapheno.PhenotypeOutput(kit.chimerapheno.white_pattern)
                    kit.chimerapheno.SpriteInfo(kit.moons)

                kit.parent1 = ref_cat.parent1    
                kit.parent2 = ref_cat.parent2   
                kit.parent3 = ref_cat.parent3  
                kit.genderalign = ref_cat.genderalign

            else:
                if kit.chimerapheno:
                    kits_amount -= 1
                    if i > kits_amount:
                        kit.phenotype.chimera = False
                        kit.chimerapheno = None
                
                if constants.CONFIG["genetics_config"]["identical_twins"] and randint(1, constants.CONFIG["genetics_config"]["identical_twins"]) == 1 and kits_amount < 19:
                    kits_amount += 1
                    identical = True
                
            #kit.adoptive_parents = all_adoptive_parents  # Add the adoptive parents. 
            # Prevent duplicate prefixes in litter
            extant = [kitty.name.prefix for kitty in all_kitten if kitty.ID != kit.ID]
            while kit.name.prefix in extant:
                kit.name = Name(kit)

            all_kitten.append(kit)
            # adoptive parents are set at the end, when everything else is decided

            # remove scars
            kit.pelt.scars.clear()

            # try to give them a permanent condition. 1/90 chance
            # don't delete the game.clan condition, this is needed for a test
            if game.clan and not int(
                random()
                * constants.CONFIG["cat_generation"]["base_permanent_condition"]
            ):
                kit.congenital_condition(kit)
                for condition in kit.permanent_condition:
                    if kit.permanent_condition[condition] == 'born without a leg':
                        kit.pelt.scars.append('NOPAW')
                    elif kit.permanent_condition[condition] == 'born without a tail' and kit.phenotype.bobtailnr != 1:
                        kit.pelt.scars.append('NOTAIL')
                Condition_Events.handle_already_disabled(kit, clan)

            # create and update relationships
            for cat_id in game.clan.clan_cats:
                if cat_id == kit.ID:
                    continue
                the_cat = Cat.all_cats.get(cat_id)
                if not the_cat or the_cat.dead or the_cat.status.is_outsider:
                    continue
                if the_cat.ID in kit.get_parents():
                    parent_to_kit = constants.CONFIG["new_cat"]["parent_buff"][
                        "parent_to_kit"
                    ]
                    y = randrange(0, 15)
                    start_relation = Relationship(the_cat, kit, False, True)
                    start_relation.like = parent_to_kit[RelType.LIKE] + y
                    start_relation.comfort = parent_to_kit[RelType.COMFORT] + y
                    start_relation.respect = parent_to_kit[RelType.RESPECT] + y
                    start_relation.trust = parent_to_kit[RelType.TRUST] + y
                    the_cat.relationships[kit.ID] = start_relation

                    kit_to_parent = constants.CONFIG["new_cat"]["parent_buff"][
                        "kit_to_parent"
                    ]
                    y = randrange(0, 15)
                    start_relation = Relationship(kit, the_cat, False, True)
                    start_relation.like += kit_to_parent[RelType.LIKE] + y
                    start_relation.comfort = kit_to_parent[RelType.COMFORT] + y
                    start_relation.respect = kit_to_parent[RelType.RESPECT] + y
                    start_relation.trust = kit_to_parent[RelType.TRUST] + y
                    kit.relationships[the_cat.ID] = start_relation

            #### REMOVE ACCESSORY ######
            kit.pelt.accessory = []
            game.clan.add_cat(kit)

            #### GIVE HISTORY ######
            kit.history.add_beginning(clan_born=bool(cat))

        if blood_parent or blood_parent2:
            thought = i18n.t(
                "conditions.pregnancy.half_blood_kitting_thought",
                count=kits_amount,
            )
            blood_parent.thought = event_text_adjust(Cat, thought, main_cat = blood_parent, clan=clan)
            for par in range(len(blood_parent2)):
                blood_parent2[par].thought = event_text_adjust(Cat, thought, main_cat = blood_parent2[par], clan=clan)

        # check other cats of Clan for siblings
        for kitten in all_kitten:
            # update/buff the relationship towards the siblings
            for second_kitten in all_kitten:
                y = randrange(0, 10)
                if second_kitten.ID == kitten.ID:
                    continue
                try:
                    kitten.relationships[second_kitten.ID].like += 20 + y
                    kitten.relationships[second_kitten.ID].comfortable += 10 + y
                    kitten.relationships[second_kitten.ID].trust += 10 + y
                except:
                    start_relation = Relationship(kitten, second_kitten, False, True)
                    kitten.relationships[second_kitten.ID] = start_relation
                    kitten.relationships[second_kitten.ID].like = 20 + y
                    kitten.relationships[second_kitten.ID].comfortable = 10 + y
                    kitten.relationships[second_kitten.ID].trust = 10 + y
            
            kitten.create_inheritance_new_cat() # Calculate inheritance. 
            kitten.create_relationships_new_cat()

        # check if the possible adoptive cat is not already in the family tree and
        # add them as adoptive parents if not
        final_adoptive_parents = []
        for adoptive_p in all_adoptive_parents:
            if adoptive_p not in all_kitten[0].inheritance.all_involved:
                final_adoptive_parents.append(adoptive_p)
        
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
            kit.inheritance.update_inheritance()
            kit.inheritance.update_all_related_inheritance()

            # update relationship for adoptive parents
            for parent_id in kit.adoptive_parents:
                parent = Cat.fetch_cat(parent_id)
                if parent:
                    kit_to_parent = constants.CONFIG["new_cat"]["parent_buff"][
                        "kit_to_parent"
                    ]
                    parent_to_kit = constants.CONFIG["new_cat"]["parent_buff"][
                        "parent_to_kit"
                    ]
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

        return all_kitten

    @staticmethod
    def get_amount_of_kits(cat, clan, hidden=False):
        """Get the amount of kits which will be born."""
        
        if(get_clan_setting('modded_kits')):

            one_kit = [1] * constants.CONFIG["pregnancy"]["one_kit_modded"][cat.age.value]
            two_kits = [2] * constants.CONFIG["pregnancy"]["two_kit_modded"][cat.age.value]
            three_kits = [3] * constants.CONFIG["pregnancy"]["three_kit_modded"][cat.age.value]
            four_kits = [4] * constants.CONFIG["pregnancy"]["four_kit_modded"][cat.age.value]
            five_kits = [5] * constants.CONFIG["pregnancy"]["five_kit_modded"][cat.age.value]
            six_kits = [choice([6, 7, 8])] * constants.CONFIG["pregnancy"]["six_kit_modded"][cat.age.value]
            nine_kits = [choice([9, 10, 11, 12])] * constants.CONFIG["pregnancy"]["nine_kit_modded"][cat.age.value]
            max_kits = [choice([13, 14, 15, 16, 17, 18, 19])] * constants.CONFIG["pregnancy"]["max_kit_modded"][cat.age.value]

            amount = choice(one_kit + two_kits + three_kits + four_kits + five_kits + six_kits + nine_kits + max_kits)

        else:
            min_kits = constants.CONFIG["pregnancy"]["min_kits"]
            min_kit = [min_kits] * constants.CONFIG["pregnancy"]["one_kit_possibility"][cat.age.value]
            two_kits = [min_kits + 1] * constants.CONFIG["pregnancy"]["two_kit_possibility"][cat.age.value]
            three_kits = [min_kits + 2] * constants.CONFIG["pregnancy"]["three_kit_possibility"][cat.age.value]
            four_kits = [min_kits + 3] * constants.CONFIG["pregnancy"]["four_kit_possibility"][cat.age.value]
            five_kits = [min_kits + 4] * constants.CONFIG["pregnancy"]["five_kit_possibility"][cat.age.value]
            max_kits = [constants.CONFIG["pregnancy"]["max_kits"]] * constants.CONFIG["pregnancy"]["max_kit_possibility"][cat.age.value]

            amount = choice(min_kit + two_kits + three_kits + four_kits + five_kits + max_kits)
        
        if hidden:
            amount = max(1, int(amount/3))

        return amount

    # ---------------------------------------------------------------------------- #
    #                                  get chances                                 #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def get_love_affair_chance(
        mate_relation: Relationship, affair_relation: Relationship
    ):
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

    @staticmethod
    def get_unmated_love_affair_chance(relation: Relationship):
        """Get the "love affair" change when neither the cat nor the highest romantic relation have a mate"""

        if not relation.opposite_relationship:
            relation.link_relationship()

        affair_chance = 15
        average_romantic_love = (
            relation.romance + relation.opposite_relationship.romance
        ) / 2

        if average_romantic_love > 50:
            affair_chance -= 12
        elif average_romantic_love > 40:
            affair_chance -= 10
        elif average_romantic_love > 30:
            affair_chance -= 7
        elif average_romantic_love > 10:
            affair_chance -= 5

        return affair_chance

    @staticmethod
    def get_balanced_kit_chance(
        first_parent: Cat, second_parent: Cat, affair, clan
    ) -> int:
        """Returns a chance based on different values."""
        # Now that the second parent is determined, we can calculate the balanced chance for kits
        # get the chance for pregnancy
        if not (get_clan_setting('modded_kits')):
            inverse_chance = constants.CONFIG["pregnancy"]["primary_chance_unmated"]
        else:
            inverse_chance = constants.CONFIG["pregnancy"]["modded_primary_chance_unmated"]
        if len(first_parent.mate) > 0:
            if not (get_clan_setting('modded_kits')):
                inverse_chance = constants.CONFIG["pregnancy"]["primary_chance_mated"]
            else:
                inverse_chance = constants.CONFIG["pregnancy"]["modded_primary_chance_mated"]

        # SETTINGS
        # - decrease inverse chance if only mated pairs can have kits
        if not get_clan_setting("single parentage"):
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
                if comp is not None:
                    buff = 0.85
                    if not comp:
                        buff += 0.3
                    inverse_chance = int(inv * buff)


        average_romantic_love = -1000
        average_comfort = -1000
        average_trust = -1000
        # RELATIONSHIP
        # - decrease the inverse chance if the cats are going along well
        if second_parent:
            # get the needed relationships
            for x in second_parent:
                if x == "Surrogate":
                    continue
                if x.ID in first_parent.relationships:
                    second_parent_relation = first_parent.relationships[x.ID]
                else:
                    second_parent_relation = first_parent.create_one_relationship(x)
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

        # 'INBREED' counter
        # - increase inverse chance if one of the current cats belongs in the biggest family
        if not Pregnancy_Events.biggest_family.get(clan.displayname):  # set the family if not already
            Pregnancy_Events.set_biggest_family(clan)

        InBiggest = False
        if second_parent:
            for x in second_parent:
                if x == "Surrogate":
                    continue
                if x.ID in Pregnancy_Events.biggest_family[clan.displayname]:
                    InBiggest = True

        if first_parent.ID in Pregnancy_Events.biggest_family[clan.displayname] or second_parent and InBiggest:
            inverse_chance = int(inverse_chance * 1.7)

        # - decrease inverse chance if the current family is small
        if len(first_parent.get_relatives(get_clan_setting("first cousin mates"))) < (
            living_cats / 15
        ):
            inverse_chance = int(inverse_chance * 0.7)

        # - decrease inverse chance single parents if settings allow an biggest family is huge
        settings_allow = not second_parent and get_clan_setting("single parentage")
        if settings_allow and Pregnancy_Events.biggest_family_is_big(clan):
            inverse_chance = int(inverse_chance * 0.9)

        if first_parent.name.prefix == "Choupique":
            inverse_chance = int(inverse_chance/4)

        return inverse_chance
