import random
from operator import xor
from random import choice, randint

import ujson

from scripts.cat.cats import Cat
from scripts.cat.history import History
from scripts.cat.genotype import Genotype
from scripts.cat.names import names, Name
from scripts.cat_relations.relationship import Relationship
from scripts.event_class import Single_Event
from scripts.events_module.condition_events import Condition_Events
from scripts.game_structure.game_essentials import game
from scripts.utility import (
    create_new_cat,
    get_highest_romantic_relation,
    event_text_adjust,
    get_personality_compatibility,
    BACKSTORIES,
    change_relationship_values,
    get_alive_status_cats,
)


class Pregnancy_Events:
    """All events which are related to pregnancy such as kitting and defining who are the parents."""

    biggest_family = {}

    PREGNANT_STRINGS = None
    with open(f"resources/dicts/conditions/pregnancy.json", "r") as read_file:
        PREGNANT_STRINGS = ujson.loads(read_file.read())

    @staticmethod
    def set_biggest_family():
        """Gets the biggest family of the clan."""
        biggest_family = None
        for cat in Cat.all_cats.values():
            ancestors = cat.get_relatives()
            if not biggest_family:
                biggest_family = ancestors
                biggest_family.append(cat.ID)
            elif len(biggest_family) < len(ancestors) + 1:
                biggest_family = ancestors
                biggest_family.append(cat.ID)
        Pregnancy_Events.biggest_family = biggest_family

    @staticmethod
    def biggest_family_is_big():
        """Returns if the current biggest family is big enough to 'activates' additional inbreeding counters."""

        living_cats = len(
            [i for i in Cat.all_cats.values() if not (i.dead or i.outside or i.exiled)]
        )
        return len(Pregnancy_Events.biggest_family) > (living_cats / 10)

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

        if not Pregnancy_Events.biggest_family:
            Pregnancy_Events.set_biggest_family()

        # Handles if a cat is already pregnant
        if cat.ID in clan.pregnancy_data:
            moons = clan.pregnancy_data[cat.ID]["moons"]
            if moons == 1:
                Pregnancy_Events.handle_one_moon_pregnant(cat, clan)
                return
            if moons >= 2:
                Pregnancy_Events.handle_two_moon_pregnant(cat, clan)
                # events.ceremony_accessory = True
                return

        if cat.outside:
            return

        # Handle birth cooldown outside of the check_if_can_have_kits function, so it only happens once
        # for each cat.
        if cat.birth_cooldown > 0:
            cat.birth_cooldown -= 1

        # Check if they can have kits.
        can_have_kits = Pregnancy_Events.check_if_can_have_kits(
            cat, clan.clan_settings["single parentage"], clan.clan_settings["affair"]
        )
        if not can_have_kits:
            return

        # DETERMINE THE SECOND PARENT
        # check if there is a cat in the clan for the second parent
        second_parent, is_affair = Pregnancy_Events.get_second_parent(cat, clan)

        # check if the second_parent is not none and if they also can have kits
        can_have_kits, kits_are_adopted, second_parent = Pregnancy_Events.check_second_parent(
            cat,
            second_parent,
            clan.clan_settings["single parentage"],
            clan.clan_settings["affair"],
            clan.clan_settings["same sex birth"],
            clan.clan_settings["same sex adoption"],
            clan.clan_settings["surrogates"],
        )
        if second_parent:
            if not can_have_kits:
                return
        else:
            if not game.clan.clan_settings["single parentage"]:
                return

        chance = Pregnancy_Events.get_balanced_kit_chance(cat, second_parent if second_parent else None, is_affair, clan)
        
        All_Infertile = True
        if second_parent and second_parent[0] == "Surrogate" and 'infertility' not in cat.permanent_condition:
            All_Infertile = False
        elif second_parent and second_parent[0] == "Surrogate":
            second_parent = None
            if not game.clan.clan_settings["single parentage"]:
                return
        elif second_parent:
            for x in second_parent:
                if 'infertility' not in x.permanent_condition:
                    All_Infertile = False

        if not int(random.random() * chance):
            # If you've reached here - congrats, kits!
            if kits_are_adopted or 'infertility' in cat.permanent_condition or (second_parent and All_Infertile):
                Pregnancy_Events.handle_adoption(cat, second_parent, clan)
            else:
                surrogate = False
                if second_parent and second_parent[0] == "Surrogate":
                    second_parent[0] = Pregnancy_Events.handle_surrogate(cat, clan)
                    if not second_parent[0]:
                        second_parent = None
                        return
                    else:
                        surrogate = True
                Pregnancy_Events.handle_zero_moon_pregnant(cat, second_parent, surrogate, clan)

    # ---------------------------------------------------------------------------- #
    #                                 handle events                                #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def handle_adoption(cat: Cat, other_cat=None, clan=game.clan):
        """Handle if the there is no pregnancy but the pair triggered kits chance."""
        if other_cat:
            for x in other_cat:
                if x.dead or x.outside or x.birth_cooldown > 0 or x.no_kits:
                    other_cat.remove(x)
        
        if other_cat and len(other_cat) < 1:
            return

        if cat.ID in clan.pregnancy_data:
            return

        if other_cat:
            for x in other_cat:
                if x.ID in clan.pregnancy_data:
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
        
        amount = Pregnancy_Events.get_amount_of_kits(cat, clan)
        kits = Pregnancy_Events.get_kits(amount, None, None, clan, adoptive_parents=adoptive_parents)
        
        insert = 'this should not display'
        insert2 = 'this should not display'
        if amount == 1:
            insert = "a single kitten"
            insert2 = "it"
        if amount > 1:
            insert = f"a litter of {len(kits)} kits"
            insert2 = "them"

        print_event = f"{cat.name} found {insert} and decides to adopt {insert2}."
        if other_cat:
            if len(other_cat) == 1:
                print_event = f"{cat.name} and {other_cat[0].name} found {insert} and decided to adopt {insert2}."
            else:
                names = ""
                for x in other_cat[:-1]:
                    names += ", " + str(x.name)
                names += " and " + other_cat[len(other_cat)-1]
                print_event = f"{cat.name} {names} found {insert} and decided to adopt {insert2}."
        
        cats_involved = [cat.ID]
        if other_cat:
            for x in other_cat:
                cats_involved.append(x.ID)
        for kit in kits:
            kit.thought = f"Snuggles up to the belly of {cat.name}"
            cats_involved.append(kit.ID)

        # Normally, birth cooldown is only applied to cat who gave birth
        # However, if we don't apply birth cooldown to adoption, we get
        # too much adoption, since adoptive couples are using the increased two-parent
        # kits chance. We will only apply it to "cat" in this case
        # which is enough to stop the couple from adopting about within
        # the window.
        cat.birth_cooldown = game.config["pregnancy"]["birth_cooldown"]

        game.cur_events_list.append(
            Single_Event(print_event, "birth_death", cats_involved)
        )

    @staticmethod
    def handle_zero_moon_pregnant(cat: Cat, other_cat=None, surrogate=False, clan=game.clan):
        """Handles if the cat is zero moons pregnant."""

        if other_cat:
            other_cat_copy = []
            for x in other_cat:
                if not(x.dead or (x.outside and x.status not in ['kittypet', 'loner', 'rogue']) or x.birth_cooldown > 0 or x.no_kits):
                    other_cat_copy.append(x)
            other_cat = other_cat_copy
        
        if other_cat != None and len(other_cat) < 1:
            return

        if cat.ID in clan.pregnancy_data:
            return

        if other_cat:
            for x in other_cat:
                if x.ID in clan.pregnancy_data:
                    return
        
        # additional save for no kit setting
        if (cat and cat.no_kits):
            return

        if clan.clan_settings['same sex birth'] and not (not other_cat and random.randint(0,1)):
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
                    "carrionplace disease", "heat stroke", "heat exhaustion"] and random.random() < 0.25:
                        fever = True

            clan.pregnancy_data[cat.ID] = {
                "second_parent": ids if other_cat else None,
                "affair_partner" : affair_partner if affair_partner else None,
                "surrogate" : surrogates if surrogate else None,
                "moons": 0,
                "amount": 0,
                "fever_coat": fever
            }

            text = choice(Pregnancy_Events.PREGNANT_STRINGS["announcement"])
            severity = random.choices(["minor", "major"], [3, 1], k=1)
            cat.get_injured("pregnant", severity=severity[0])
            text += choice(Pregnancy_Events.PREGNANT_STRINGS[f"{severity[0]}_severity"])
            text = event_text_adjust(Cat, text, main_cat=cat, clan=clan)
            game.cur_events_list.append(Single_Event(text, "birth_death", cat.ID))
        else:
            if (not other_cat or surrogate) and 'Y' in cat.genotype.sexgene:
        
                amount = Pregnancy_Events.get_amount_of_kits(cat, clan)
                stillborn_chance = 0

                if amount < 3:
                    stillborn_chance = game.config['pregnancy']['stillborn_chances']['small']
                elif amount == 3:
                    stillborn_chance = game.config['pregnancy']['stillborn_chances']['three']
                elif amount < 6:
                    stillborn_chance = game.config['pregnancy']['stillborn_chances']['mid']
                elif amount < 9:
                    stillborn_chance = game.config['pregnancy']['stillborn_chances']['big']
                else:
                    stillborn_chance = game.config['pregnancy']['stillborn_chances']['large']

                if not (clan.clan_settings['modded_kits']):
                    stillborn_chance = 0
                
                unknowns = []
                for outcat in Cat.all_cats:
                    outcat = Cat.all_cats.get(outcat)
                    if not outcat.dead and outcat.status in ['kittypet', 'loner', 'rogue']:    
                        unknowns.append(outcat)

                possible_affair_partners = [i for i in unknowns if
                                        i.is_potential_mate(cat, for_love_interest=True, outsider=True) 
                                        and Pregnancy_Events.check_if_can_have_kits(i, True, True) 
                                        and 'infertility' not in i.permanent_condition 
                                        and (clan.clan_settings['same sex birth'] or xor('Y' in i.genotype.sexgene, 'Y' in cat.genotype.sexgene)) 
                                        and len(i.mate) == 0 and not i.birth_cooldown]
                if surrogate:
                    outside_parent = other_cat
                    outside_parent[0].birth_cooldown = game.config["pregnancy"]["birth_cooldown"]
                    backkit = None
                elif(random.random() < 0.75 or len(possible_affair_partners) < 1):
                    if(randint(1, 4) > 1):
                        cat_type = choice(['loner', 'rogue', 'kittypet'])
                        backstories = {
                            'loner' : 'loner_backstories',
                            'rogue' : 'rogue_backstories',
                            'kittypet' : 'kittypet_backstories'
                        }
                        backkit = 'outsider_roots2'
                    else:
                        cat_type = 'Clancat'
                        backkit = 'halfclan2'
                    mate_age = cat.moons + randint(0, 24)-12
                    outside_parent = None
                    if cat_type != 'Clancat':
                        while not outside_parent or 'infertility' in outside_parent.permanent_condition:
                            if outside_parent and Cat.all_cats[outside_parent.ID]:
                                del Cat.all_cats[outside_parent.ID]
                            outside_parent = create_new_cat(Cat,
                                                loner=cat_type in ["loner", "rogue"],
                                                kittypet=cat_type == "kittypet",
                                                other_clan=cat_type == 'former Clancat',
                                                status=cat_type,
                                                backstory=BACKSTORIES["backstory_categories"][backstories[cat_type]],
                                                alive=True,
                                                age=mate_age if mate_age > 14 else 15,
                                                gender='fem' if 'Y' in cat.genotype.sexgene else 'masc',
                                                outside=True,
                                                is_parent=True)[0]
                        outside_parent.thought = "Is wondering what their kits are doing"
                        outside_parent.birth_cooldown = game.config["pregnancy"]["birth_cooldown"]
                        if random.random() < 0.2:
                            outside_parent.set_mate(cat)
                            cat.set_mate(outside_parent)
                    
                    outside_parent = [outside_parent]

                else:
                    outside_parent = [choice(possible_affair_partners)]
                    backkit = 'outsider_roots2'

                if surrogate and not outside_parent[0].outside:
                    cats_involved = [cat.ID]
                    for par in outside_parent:
                        cats_involved.append(par.ID)
                    
                    pregnant_cat = outside_parent[0]
                    text = choice(Pregnancy_Events.PREGNANT_STRINGS["announcement"])
                    severity = random.choices(["minor", "major"], [3, 1], k=1)
                    text += choice(Pregnancy_Events.PREGNANT_STRINGS[f"{severity[0]}_severity"])
                    text = event_text_adjust(Cat, text, main_cat=pregnant_cat, clan=clan)
                    text += f" {cat.name} thanks {outside_parent[0].name} for being a surrogate."
                    game.cur_events_list.append(Single_Event(text, "birth_death", cats_involved))
                    
                    fever = False
                    ids = [cat.ID]
                    if clan.clan_settings['multisire']:
                        for c in other_cat:
                            ids.append(c.ID)
                    if len(pregnant_cat.illnesses) > 0:
                        for illness in pregnant_cat.illnesses:
                            if illness in ["greencough", "redcough", "yellowcough", "whitecough", 
                            "an infected wound", "a festering wound", "ear infection",
                            "carrionplace disease", "heat stroke", "heat exhaustion"] and random.random() < 0.25:
                                fever = True

                    clan.pregnancy_data[pregnant_cat.ID] = {
                        "second_parent": ids,
                        "affair_partner" : None,
                        "surrogate" : pregnant_cat.ID,
                        "moons": 0,
                        "amount": 0,
                        "fever_coat": fever
                    }
                    severity = random.choices(["minor", "major"], [3, 1], k=1)
                    pregnant_cat.get_injured("pregnant", severity=severity[0])
                    return

                kits = Pregnancy_Events.get_kits(amount, cat, outside_parent, clan, backkit=backkit)

                for kit in kits:
                    if random.random() < stillborn_chance or kit.genotype.manx[1] == "Ab" or kit.genotype.manx[1] == "M" or kit.genotype.fold[1] == "Fd" or kit.genotype.munch[1] == "Mk" or ('NoDBE' not in kit.genotype.pax3 and 'DBEalt' not in kit.genotype.pax3):
                        kit.dead = True
                        kit.moons = 0
                        History.add_death(kit, str(kit.name) + " was stillborn.")
                        kits.remove(kit)

                insert = 'this should not display'
                if len(kits) == 1:
                    insert = 'a single kitten'
                if len(kits) > 1:
                    insert = f'a litter of {len(kits)} kits'
                if len(kits) > 0:
                    print_event = f"{cat.name} brought {insert} back to camp, but refused to talk about their origin."
                    if surrogate:
                        if outside_parent[0].outside:
                            print_event = f"{cat.name} brought {insert} back to camp, telling the Clan of having found a surrogate."
                            cat.birth_cooldown = game.config["pregnancy"]["birth_cooldown"]
                            for p in cat.mate:
                                par = Cat.fetch_cat(p)
                                par.birth_cooldown = game.config["pregnancy"]["birth_cooldown"]
                        else:
                            print_event = f"{cat.name} thanks {outside_parent[0].name} for being a surrogate to a litter."
                            outside_parent[0].get_injured("recovering from birth", event_triggered=True)
                    cats_involved = [cat.ID]
                    for par in outside_parent:
                        if par:
                            cats_involved.append(par.ID)
                    for kit in kits:
                        cats_involved.append(kit.ID)
                    game.cur_events_list.append(Single_Event(print_event, "birth_death", cats_involved))
                return

            # if the other cat is afab and the current cat is amab, make the afab cat pregnant
            pregnant_cat = cat
            second_parent = other_cat
            affair_partner = []
            surrogates = []
            if second_parent:
                for x in second_parent:
                    if 'Y' in cat.genotype.sexgene and 'Y' not in x.genotype.sexgene:
                        pregnant_cat = x
                        second_parent.remove(x)
                        second_parent.append(cat)
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

            fever = False
            if len(pregnant_cat.illnesses) > 0:
                for illness in pregnant_cat.illnesses:
                    if illness in ["greencough", "redcough", "yellowcough", "whitecough", 
                    "an infected wound", "a festering wound", "ear infection",
                    "carrionplace disease", "heat stroke", "heat exhaustion"] and random.random() < 0.25:
                        fever = True

            clan.pregnancy_data[pregnant_cat.ID] = {
                "second_parent": ids if second_parent else None,
                "affair_partner" : affair_partner if affair_partner else None,
                "surrogate" : surrogates if surrogate else None,
                "moons": 0,
                "amount": 0,
                "fever_coat": fever
            }

            text = choice(Pregnancy_Events.PREGNANT_STRINGS["announcement"])
            severity = random.choices(["minor", "major"], [3, 1], k=1)
            pregnant_cat.get_injured("pregnant", severity=severity[0])
            text += choice(Pregnancy_Events.PREGNANT_STRINGS[f"{severity[0]}_severity"])
            text = event_text_adjust(Cat, text, main_cat=pregnant_cat, clan=clan)
            game.cur_events_list.append(
                Single_Event(text, "birth_death", pregnant_cat.ID)
            )

    @staticmethod
    def handle_one_moon_pregnant(cat: Cat, clan=game.clan):
        """Handles if the cat is one moon pregnant."""
        if cat.ID not in clan.pregnancy_data.keys():
            return

        # if the pregnant cat killed meanwhile, delete it from the dictionary
        if cat.dead:
            del clan.pregnancy_data[cat.ID]
            return

        amount = Pregnancy_Events.get_amount_of_kits(cat, clan)
        
        text = 'This should not appear (pregnancy_events.py)'

        # add the amount to the pregnancy dict
        clan.pregnancy_data[cat.ID]["amount"] = amount

        fever = clan.pregnancy_data[cat.ID].get('fever_coat', False)

        if len(cat.illnesses) > 0 and not fever:
            for illness in cat.illnesses:
                if illness in ["greencough", "redcough", "yellowcough", "whitecough", 
                "an infected wound", "a festering wound", "ear infection",
                "carrionplace disease", "heat stroke", "heat exhaustion"] and random.random() < 0.33:
                    clan.pregnancy_data[cat.ID]["fever_coat"] = True

        # if the cat is outside of the clan, they won't guess how many kits they will have
        if cat.outside:
            return

        thinking_amount = random.choices(
            ["correct", "incorrect", "unsure"], [4, 1, 1], k=1
        )
        if amount <= 6:
            correct_guess = "small"
        else:
            correct_guess = "large"

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

        text = event_text_adjust(Cat, text, main_cat=cat, clan=game.clan)
        game.cur_events_list.append(Single_Event(text, "birth_death", cat.ID))

    @staticmethod
    def handle_two_moon_pregnant(cat: Cat, clan=game.clan):
        """Handles if the cat is two moons pregnant."""
        if cat.ID not in clan.pregnancy_data.keys():
            return

        # if the pregnant cat is killed meanwhile, delete it from the dictionary
        if cat.dead:
            del clan.pregnancy_data[cat.ID]
            return

        involved_cats = [cat.ID]

        kits_amount = clan.pregnancy_data[cat.ID]["amount"]
        FeverCoat = clan.pregnancy_data[cat.ID].get("fever_coat", False)
        stillborn_chance = 0
        if kits_amount == 0:  # safety check, sometimes pregnancies were ending up with 0 due to save rollbacks
            kits_amount = 1

        if kits_amount < 3:
            stillborn_chance = game.config['pregnancy']['stillborn_chances']['small']
        elif kits_amount == 3:
            stillborn_chance = game.config['pregnancy']['stillborn_chances']['three']
        elif kits_amount < 6:
            stillborn_chance = game.config['pregnancy']['stillborn_chances']['mid']
        elif kits_amount < 9:
            stillborn_chance = game.config['pregnancy']['stillborn_chances']['big']
        else:
            stillborn_chance = game.config['pregnancy']['stillborn_chances']['large']
        
        if not (clan.clan_settings['modded_kits']):
            stillborn_chance = 0

        other_cat_id = clan.pregnancy_data[cat.ID]["second_parent"]
        affair_partner_id = []
        affair_partners = []
        surrogate = []
        RandomAffair = None
        try:
            affair_partner_id = clan.pregnancy_data[cat.ID]["affair_partner"]
        except:
            affair_partner_id = []
        try:
            surrogate_id = clan.pregnancy_data[cat.ID]["surrogate"]
        except:
            surrogate_id = []

        # delete the cat out of the pregnancy dictionary
        del clan.pregnancy_data[cat.ID]

        pregnant_cat = cat

        other_cat = []
        if other_cat_id and type(other_cat_id) == list: 
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
            if surrogate_id[0] == cat.ID:
                cat = other_cat[0]
            surrogate.append(Cat.all_cats.get(surrogate_id[0]))

        if affair_partner_id:
            if not other_cat:
                other_cat = []
            for id in affair_partner_id:
                other_cat.append(Cat.all_cats.get(id))
                affair_partners.append(Cat.all_cats.get(id))
            if affair_partners:
                RandomAffair = choice(affair_partners)

        backkit = None
        if not other_cat:
            
            unknowns = []
            for outcat in Cat.all_cats:
                outcat = Cat.all_cats.get(outcat)
                if not outcat.dead and outcat.status in ['kittypet', 'loner', 'rogue']:    
                    unknowns.append(outcat)

            possible_affair_partners = [i for i in unknowns if
                                    i.is_potential_mate(cat, for_love_interest=True, outsider=True) 
                                    and Pregnancy_Events.check_if_can_have_kits(i, True, True) 
                                    and 'infertility' not in i.permanent_condition 
                                    and (clan.clan_settings['same sex birth'] or xor('Y' in i.genotype.sexgene, 'Y' in cat.genotype.sexgene)) 
                                    and len(i.mate) == 0]
            if(random.random() < 0.75 or len(possible_affair_partners) < 1):
                if(randint(1, 4) > 1):
                    cat_type = choice(['loner', 'rogue', 'kittypet'])
                    
                    backstories = {
                        'loner' : 'loner_backstories',
                        'rogue' : 'rogue_backstories',
                        'kittypet' : 'kittypet_backstories'
                    }
                    backkit = 'outsider_roots1'
                else:
                    cat_type = 'Clancat'
                    backkit = 'halfclan1'
                
                nr_of_parents = 1
                if clan.clan_settings['multisire'] and randint(1, game.config['pregnancy']["multi-sire_chance"]) == 1 and cat_type != 'Clancat':
                    nr_of_parents = randint(2, game.config['pregnancy']["multi-sire_max_sires"])
                other_cat = []
                for i in range(0, nr_of_parents):

                    mate_age = cat.moons + randint(0, 24)-12
                    if cat_type != 'Clancat':
                        out_par = None
                        while not out_par or 'infertility' in out_par.permanent_condition:
                            if out_par and Cat.all_cats[out_par.ID]:
                                del Cat.all_cats[out_par.ID]
                            out_par = create_new_cat(Cat,
                                                    loner=cat_type in ["loner", "rogue"],
                                                    kittypet=cat_type == "kittypet",
                                                    other_clan=cat_type == 'former Clancat',
                                                    status=cat_type,
                                                    backstory=BACKSTORIES["backstory_categories"][backstories[cat_type]],
                                                    alive=True,
                                                    age=mate_age if mate_age > 14 else 15,
                                                    gender='masc',
                                                    outside=True,
                                                    is_parent=True)[0]
                            out_par.thought = f"Is wondering how {cat.name} is doing"
                        
                        if random.random() < 0.2:
                            out_par.set_mate(cat)
                            cat.set_mate(out_par)

                        other_cat.append(out_par)

            else:
                backkit = 'outsider_roots1'
                other_cat = []
                nr_of_parents = 1
                if clan.clan_settings['multisire'] and randint(1, game.config['pregnancy']["multi-sire_chance"]) == 1:
                    nr_of_parents = randint(2, game.config['pregnancy']["multi-sire_max_sires"])
                
                if nr_of_parents > len(possible_affair_partners):
                    nr_of_parents = len(possible_affair_partners)

                for i in range(0, nr_of_parents):
                    other_cat.append(choice(possible_affair_partners))
                    possible_affair_partners.remove(other_cat[i])
                


        kits = Pregnancy_Events.get_kits(kits_amount, pregnant_cat, other_cat if not surrogate or cat in other_cat else surrogate, clan, backkit=backkit)
        kits_amount = len(kits)
        for kit in kits:
            if FeverCoat:
                kit.genotype.fevercoat = True
                if kit.genotype.chimera:
                    kit.genotype.chimerageno.fevercoat = True
            if random.random() < stillborn_chance or kit.genotype.manx[1] == "Ab" or kit.genotype.manx[1] == "M" or kit.genotype.fold[1] == "Fd" or kit.genotype.munch[1] == "Mk" or ('NoDBE' not in kit.genotype.pax3 and 'DBEalt' not in kit.genotype.pax3):
                kit.moons = 0
                kit.dead = True
                History.add_death(kit, str(kit.name) + " was stillborn.")
        Pregnancy_Events.set_biggest_family()
        
        if pregnant_cat.outside:
            for kit in kits:
                kit.outside = True
                game.clan.add_to_outside(kit)
                kit.backstory = "outsider1"
                if pregnant_cat.exiled:
                    kit.status = "loner"
                    name = choice(names.names_dict["normal_prefixes"])
                    kit.name = Name('loner', prefix=name, suffix="")
                if other_cat and not other_cat[0].outside:
                    kit.backstory = "outsider2"
                if pregnant_cat.outside and not pregnant_cat.exiled:
                    kit.backstory = "outsider3"
                kit.relationships = {}
                kit.create_one_relationship(cat)

        if kits_amount == 1:
            insert = "single kitten"
        else:
            insert = f"litter of {kits_amount} kits"

        # Since cat has given birth, apply the birth cooldown.
        cat.birth_cooldown = game.config["pregnancy"]["birth_cooldown"]
        if other_cat:
            for c in other_cat:
                c.birth_cooldown = game.config["pregnancy"]["birth_cooldown"]
        if surrogate:
            for c in surrogate:
                c.birth_cooldown = game.config["pregnancy"]["birth_cooldown"]

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
                if not x.outside:
                    All_Mates_Outside = False
                if len(x.mate) > 0:
                    Both_Unmated = False
        
        # choose event string
        # TODO: currently they don't choose which 'mate' is the 'blood' parent or not
        # change or leaf as it is?
        events = Pregnancy_Events.PREGNANT_STRINGS
        event_list = []


        if surrogate and cat in other_cat:
            involved_cats.append(cat.ID)
            involved_cats.append(RandomChoice.ID)
            cat = pregnant_cat
            if random.random() < 0.5:
                event_list.append(choice(events["birth"]["surrogate_birth"]))
            else:
                SurrogateBirth = True
                event_list.append(choice(events["birth"]["two_parents_surrogate"]))
        elif not cat.outside and backkit:
            event_list.append(choice(events["birth"]["unmated_parent"]))
        elif cat.outside:
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
            event_list.append(choice(events["birth"]["affair"]))
        else:
            event_list.append(choice(events["birth"]["unmated_parent"]))

        if clan.game_mode != "classic":
            try:
                death_chance = cat.injuries["pregnant"]["mortality"]
            except:
                death_chance = 40
        else:
            death_chance = 40
        if not int(
            random.random() * death_chance
        ):  # chance for a cat to die during childbirth
            possible_events = events["birth"]["death"]
            # just makin sure meds aren't mentioned if they aren't around or if they are a parent
            meds = get_alive_status_cats(Cat, ["healer", "healer apprentice"], sort=True)
            mate_is_med = [mate_id for mate_id in cat.mate if mate_id in meds]
            if not meds or cat in meds or len(mate_is_med) > 0:
                for event in possible_events:
                    if "healer" in event:
                        possible_events.remove(event)

            if cat.outside:
                possible_events = events["birth"]["outside_death"]
            if game.clan.leader_lives > 1 and cat.status == "leader":
                possible_events = events["birth"]["lead_death"]
            event_list.append(choice(possible_events))

            if cat.status == "leader":
                clan.leader_lives -= 1
                cat.die()
                death_event = "died shortly after kitting"
            else:
                cat.die()
                death_event = f"{cat.name} died while kitting."
            History.add_death(cat, death_text=death_event)
        elif not cat.outside:  # if cat doesn't die, give recovering from birth
            cat.get_injured("recovering from birth", event_triggered=True)
            if "blood loss" in cat.injuries:
                if cat.status == "leader":
                    death_event = "died after a harsh kitting"
                else:
                    death_event = f"{cat.name} died after a harsh kitting."
                History.add_possible_history(cat, "blood loss", death_text=death_event)
                possible_events = events["birth"]["difficult_birth"]
                # just makin sure meds aren't mentioned if they aren't around or if they are a parent
                meds = get_alive_status_cats(Cat, ["healer", "healer apprentice"])
                mate_is_med = [mate_id for mate_id in cat.mate if mate_id in meds]
                if not meds or cat in meds or len(mate_is_med) > 0:
                    for event in possible_events:
                        if "healer" in event:
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
                event_list[0] = event_text_adjust(Cat, event_list[0], main_cat=cat, random_cat=RandomChoice, clan=game.clan)
                cat = pregnant_cat
        print_event = " ".join(event_list)
        print_event = print_event.replace("{insert}", insert)

        for kit in kits:
            involved_cats.append(kit.ID)

        print_event = event_text_adjust(Cat, print_event, main_cat=cat, random_cat=RandomChoice, clan=game.clan)

        # display event
        game.cur_events_list.append(
            Single_Event(print_event, ["health", "birth_death"], involved_cats)
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

        if "recovering from birth" in cat.injuries:
            return False

        # decide chances of having kits, and if it's possible at all.
        # Including - age, dead statis, having kits turned off.
        not_correct_age = (
            cat.age in ["newborn", "kitten", "adolescent"] or cat.moons < 15
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

        if not second_parent or len(second_parent) == 1:
        # Checks for second parent alone:
            if not Pregnancy_Events.check_if_can_have_kits(second_parent[0] if second_parent else None, single_parentage, allow_affair):
                return False, False, second_parent

            # Check to see if the pair can have kits.
            if not xor('Y' in cat.genotype.sexgene, 'Y' in second_parent[0].genotype.sexgene):
                if same_sex_birth:
                    return True, False, second_parent
                elif surrogates:
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
                if xor('Y' in cat.genotype.sexgene, 'Y' in x.genotype.sexgene) or same_sex_birth:
                    second_parent_copy.append(x)
            
            if len(second_parent_copy) < 1:
                if surrogates:
                    return True, False, ["Surrogate"] + second_parent
                elif same_sex_adoption:
                    return True, True, second_parent
                else:
                    return False, False, second_parent
            
            return True, False, second_parent



    # ---------------------------------------------------------------------------- #
    #                               getter functions                               #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def get_second_parent(cat, clan):
        """
        Return the second parent of a cat, which will have kits.
        Also returns a bool that is true if an affair was triggered.
        """
        samesex = clan.clan_settings["same sex birth"]
        allow_affair = clan.clan_settings["affair"]
        mate = None
        need_surrogate = False

        # randomly select a mate of given cat
        if len(cat.mate) > 0:
            if clan.clan_settings['multisire']:
                mate_copy = cat.mate
                mate = []
                for x in mate_copy:
                    mate.append(cat.fetch_cat(x))
            else:
                mate = choice(cat.mate)
                mate = [cat.fetch_cat(mate)]

        # if the sex does matter, choose the best solution to allow kits
        if not samesex and mate and 'Y' not in cat.genotype.sexgene:
            opposite_mate = [cat.fetch_cat(mate_id) for mate_id in cat.mate if xor('Y' in cat.fetch_cat(mate_id).genotype.sexgene, 'Y' in cat.genotype.sexgene)]
            if len(opposite_mate) > 0:
                mate = opposite_mate
                if not clan.clan_settings['multisire']:
                    mate = [choice(opposite_mate)]
        elif not samesex and mate and 'Y' in cat.genotype.sexgene:
            opposite_mate = [cat.fetch_cat(mate_id) for mate_id in cat.mate if xor('Y' in cat.fetch_cat(mate_id).genotype.sexgene, 'Y' in cat.genotype.sexgene)]
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
                elif mate_relation.romantic_love < rel.romantic_love:
                    mate_relation = rel

        # LOVE AFFAIR
        # Handle love affair chance.
        affair_partner = Pregnancy_Events.determine_love_affair(cat, mate if mate else None, mate_relation if mate else None, samesex)
        if affair_partner:
            if mate:
                mate.append(affair_partner)
            else:
                mate = [affair_partner]
            return mate, True

        # RANDOM AFFAIR
        chance = game.config["pregnancy"]["random_affair_chance"]
        special_affair = False
        if len(cat.mate) <= 0:
            # Special random affair check only for unmated cats. For this check, only
            # other unmated cats can be the affair partner.
            chance = game.config["pregnancy"]["unmated_random_affair_chance"]
            special_affair = True

        # 'buff' affairs if the current biggest family is big + this cat doesn't belong there
        if not Pregnancy_Events.biggest_family:
            Pregnancy_Events.set_biggest_family()

        if (
            Pregnancy_Events.biggest_family_is_big()
            and cat.ID not in Pregnancy_Events.biggest_family
        ):
            chance = int(chance * 0.8)

            # "regular" random affair
        if not int(random.random() * chance):
            possible_affair_partners = [
                i
                for i in Cat.all_cats_list
                if i.is_potential_mate(cat, for_love_interest=True)
                and (samesex or xor('Y' in i.genotype.sexgene, 'Y' in cat.genotype.sexgene))
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
                        if p_rel.dislike < 20 and p_rel_opp.dislike < 20:
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
        only_outside = clan.clan_settings["only outside surrogates"]
        only_clanmate = clan.clan_settings["only inclan surrogates"]
        mate = []
        
        unknowns = []
        for outcat in Cat.all_cats:
            outcat = Cat.all_cats.get(outcat)
            if not outcat.dead and outcat.status in ['kittypet', 'loner', 'rogue']:    
                unknowns.append(outcat)
        outsiders = [i for i in unknowns if
                    i.is_potential_mate(cat, for_love_interest=True, outsider=True)
                    and Pregnancy_Events.check_if_can_have_kits(i, True, True) 
                    and 'infertility' not in i.permanent_condition 
                    and (clan.clan_settings['same sex birth'] or xor('Y' in i.genotype.sexgene, 'Y' in cat.genotype.sexgene)) 
                    and len(i.mate) == 0]
        backstories = {
            'loner' : 'loner_backstories',
            'rogue' : 'rogue_backstories',
            'kittypet' : 'kittypet_backstories'
        }

        if not only_clanmate and (only_outside or randint(1, game.config['pregnancy']['clanmate_surrogate_chance']) != 1):
            if len(outsiders) > 0 and random.random() < 0.25:
                return choice(outsiders)
            else:
                cat_type = choice(['loner', 'rogue', 'kittypet'])
                mate_age = cat.moons + randint(0, 24)-12
                outside_parent = None
                while not outside_parent or 'infertility' in outside_parent.permanent_condition:
                    if outside_parent and Cat.all_cats[outside_parent.ID]:
                        del Cat.all_cats[outside_parent.ID]
                    outside_parent = create_new_cat(Cat,
                            loner=cat_type in ["loner", "rogue"],
                            kittypet=cat_type == "kittypet",
                            other_clan=False,
                            status=cat_type,
                            backstory=BACKSTORIES["backstory_categories"][backstories[cat_type]],
                            alive=True,
                            age=mate_age if mate_age > 14 else 15,
                            gender='fem' if 'Y' in cat.genotype.sexgene else 'masc',
                            outside=True,
                            is_parent=True)[0]
                    outside_parent.thought = "Wonders about those oddly named cats"
                return outside_parent
        
        # gather up mates to participate in the *selection* ig
        if len(cat.mate) > 0:
            mate_copy = cat.mate
            for x in mate_copy:
                mate.append(cat.fetch_cat(x))
        
        all_cats = [cat] + mate

        candidates = []

        for check_cat in all_cats:
            for x in check_cat.relationships.values():
                check_cand = Cat.fetch_cat(x.cat_to)
                if check_cand.dead or (check_cand.outside and not only_clanmate and check_cand.status not in ['kittypet', 'loner', 'rogue', 'former Clancat']):
                    continue
                if (x.romantic_love + x.platonic_like + x.admiration + x.trust + x.comfortable) > 20:
                    if Pregnancy_Events.check_if_can_have_kits(check_cand, True, True) and not check_cand.mate and xor('Y' in check_cand.genotype.sexgene, 'Y' in cat.genotype.sexgene) and 'infertility' not in check_cat.permanent_condition:
                        possible = True
                        for couple in all_cats:
                            if not couple.is_potential_mate(check_cand):
                                possible = False
                                break
                        if possible:
                            candidates.append(check_cand)

            candidates = list(set(candidates))
        
        if len(candidates) > 0:
            return choice(candidates)
        elif not only_clanmate:
            if len(outsiders) > 0 and random.random() < 0.25:
                return choice(outsiders)
            else:
                cat_type = choice(['loner', 'rogue', 'kittypet'])
                mate_age = cat.moons + randint(0, 24)-12
                outside_parent = None
                while not outside_parent or 'infertility' in outside_parent.permanent_condition:
                    if outside_parent and Cat.all_cats[outside_parent.ID]:
                        del Cat.all_cats[outside_parent.ID]
                    outside_parent = create_new_cat(Cat,
                            loner=cat_type in ["loner", "rogue"],
                            kittypet=cat_type == "kittypet",
                            other_clan=False,
                            status=cat_type,
                            backstory=BACKSTORIES["backstory_categories"][backstories[cat_type]],
                            alive=True,
                            age=mate_age if mate_age > 14 else 15,
                            gender='fem' if 'Y' in cat.genotype.sexgene else 'masc',
                            outside=True,
                            is_parent=True)[0]
                    outside_parent.thought = "Wonders about those oddly named cats"
                return outside_parent
        else:
            return None
        

    @staticmethod
    def determine_love_affair(cat, mate, mate_relation, samesex):
        """
        Function to handle everything around love affairs.
        Will return a second parent if a love affair is triggerd, and none otherwise.
        """

        highest_romantic_relation = get_highest_romantic_relation(
            cat.relationships.values(), exclude_mate=True, potential_mate=True
        )

        if mate and highest_romantic_relation:
            # Love affair calculation when the cat has a mate
            chance_love_affair = Pregnancy_Events.get_love_affair_chance(
                mate_relation, highest_romantic_relation
            )
            if not chance_love_affair or not int(random.random() * chance_love_affair):
                if samesex or 'Y' in cat.genotype.sexgene != 'Y' in highest_romantic_relation.cat_to.genotype.sexgene:
                    return highest_romantic_relation.cat_to
        elif highest_romantic_relation:
            # Love affair change if the cat doesn't have a mate:
            chance_love_affair = Pregnancy_Events.get_unmated_love_affair_chance(
                highest_romantic_relation
            )
            if not chance_love_affair or not int(random.random() * chance_love_affair):
                if samesex or 'Y' in cat.genotype.sexgene != highest_romantic_relation.cat_to.genotype.sexgene:
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
         
        par2geno = Genotype(game.config['genetics_config'], game.settings["ban problem genes"])
        if cat and 'Y' in cat.genotype.sexgene:
            par2geno.Generator('fem')
        elif cat:
            par2geno.Generator('masc')
        ##### SELECT BACKSTORY #####
        if backkit:
            backstory = backkit
            if 'halfclan' in backkit:
                other_cat = None
        elif cat and 'Y' not in cat.genotype.sexgene:
            backstory = choice(['halfclan1', 'outsider_roots1'])
        elif cat:
            backstory = choice(["halfclan2", "outsider_roots2"])
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
                stillborn_chance = game.config['pregnancy']['stillborn_chances']['small']
            elif initial_amount == 3:
                stillborn_chance = game.config['pregnancy']['stillborn_chances']['three']
            elif initial_amount < 6:
                stillborn_chance = game.config['pregnancy']['stillborn_chances']['mid']
            elif initial_amount < 9:
                stillborn_chance = game.config['pregnancy']['stillborn_chances']['big']
            else:
                stillborn_chance = game.config['pregnancy']['stillborn_chances']['large']

            if not (clan.clan_settings['modded_kits']):
                stillborn_chance = 0

            death_chances = game.config['death_related']['kit_death_chances']
            for i in range(initial_amount):
                if random.random() < stillborn_chance:
                   continue
                elif litter_age == 0 or not (clan.clan_settings['modded_kits']):
                    kits_amount += 1
                elif random.random() < death_chances['0']:
                    continue
                elif litter_age == 1:
                    kits_amount += 1
                elif random.random() < death_chances['1']:
                    continue
                elif litter_age == 2:
                    kits_amount += 1
                elif random.random() < death_chances['2']:
                    continue
                elif litter_age == 3:
                    kits_amount += 1
                elif random.random() < death_chances['3']:
                    continue
                elif litter_age == 4:
                    kits_amount += 1
                elif random.random() < death_chances['4']:
                    continue
                else:
                    kits_amount += 1
            if kits_amount == 0:
                kits_amount = 1
                
        #############################

        #### GENERATE THE KITS ######
        for kit in range(kits_amount):
            kit = None
            if not cat:
                # No parents provided, give a blood parent - this is an adoption.
                if not blood_parent:
                    # Generate a blood parent if we haven't already. 
                    nr_of_parents = 1
                    if clan.clan_settings['multisire'] and randint(1, game.config['pregnancy']["multi-sire_chance"]) == 1:
                        nr_of_parents = randint(2, game.config['pregnancy']["multi-sire_max_sires"])
                    
                    insert = "their kits are"
                    if kits_amount == 1:
                        insert = "their kit is"
                    thought = f"Is glad that {insert} safe"
                    parage = randint(15,120)
                    cat_type = random.choice(["loner", "kittypet"])
                    blood_parent = create_new_cat(Cat,
                                                loner=cat_type in ["loner", "rogue"],
                                                kittypet=cat_type == "kittypet",
                                                other_clan=cat_type == 'former Clancat',
                                                status=cat_type,
                                                gender='fem',
                                                alive=choice([True, False]),
                                                thought=thought,
                                                age=parage,
                                                outside=True,
                                                is_parent=True)[0]
                    blood_parent2 = []
                    
                    for i in range(0, nr_of_parents):
                        blood_par2 = None
                        parage = parage + randint(0, 24) - 12
                        while not blood_par2 or 'infertility' in blood_par2.permanent_condition:
                            if blood_par2 and Cat.all_cats[blood_par2.ID]:
                                del Cat.all_cats[blood_par2.ID]
                            cat_type = random.choice(["loner", "kittypet"])
                            blood_par2 = create_new_cat(Cat,
                                                        loner=cat_type in ["loner", "rogue"],
                                                        kittypet=cat_type == "kittypet",
                                                        other_clan=cat_type == 'former Clancat',
                                                        status=cat_type,
                                                        gender='masc',
                                                        alive=choice([True, False]),
                                                        thought=thought,
                                                        age=parage if parage > 14 else 15,
                                                        outside=True,
                                                        is_parent=True)[0]
                        blood_par2.thought = thought

                        blood_parent2.append(blood_par2)

                    blood_parent.thought = thought
                sire = choice(blood_parent2)
                chimera_sire = choice(blood_parent2)
                kit = Cat(parent1=blood_parent.ID, parent2=sire.ID, extrapar=chimera_sire if sire.ID != chimera_sire.ID else None,moons=litter_age, backstory=backstory, status='newborn' if litter_age == 0 else 'kitten')
            else:
                # Two parents provided
                second_blood = None
                if other_cat:
                    second_blood = choice(other_cat)
                    chimera_sire = choice(other_cat)
                    if second_blood.ID == chimera_sire.ID:
                        chimera_sire = None

                if backkit:    
                    kit = Cat(parent1=cat.ID, parent2=second_blood.ID if second_blood else None, moons=0, backstory=backstory, status='newborn', extrapar = par2geno if not second_blood else chimera_sire)
                else:
                    kit = Cat(parent1=cat.ID, parent2=second_blood.ID, moons=0, status='newborn')
                
                if 'Y' not in cat.genotype.sexgene or not second_blood or second_blood.outside:
                    kit.thought = f"Snuggles up to the belly of {cat.name}"
                elif 'Y' in cat.genotype.sexgene and 'Y' in cat.genotype.sexgene:
                    kit.thought = f"Snuggles up to the belly of {cat.name}"
                else:
                    kit.thought = f"Snuggles up to the belly of {second_blood.name}"
                
            #kit.adoptive_parents = all_adoptive_parents  # Add the adoptive parents. 
            # Prevent duplicate prefixes in Clan
            tries = 0
            extant = [kitty.name.prefix for kitty in Cat.all_cats.values() if not kitty.dead and not kitty.outside and kitty.ID != kit.ID]
            while tries < 20 and kit.name.prefix in extant:
                kit.name = Name("newborn")
                tries += 1

            all_kitten.append(kit)
            # adoptive parents are set at the end, when everything else is decided

            # remove scars
            kit.pelt.scars.clear()

            # try to give them a permanent condition. 1/90 chance
            # don't delete the game.clan condition, this is needed for a test
            if game.clan and not int(
                random.random()
                * game.config["cat_generation"]["base_permanent_condition"]
            ):
                kit.congenital_condition(kit)
                for condition in kit.permanent_condition:
                    if kit.permanent_condition[condition] == 'born without a leg':
                        kit.pelt.scars.append('NOPAW')
                    elif kit.permanent_condition[condition] == 'born without a tail' and kit.phenotype.bobtailnr != 1:
                        kit.pelt.scars.append('NOTAIL')
                Condition_Events.handle_already_disabled(kit)

            # create and update relationships
            for cat_id in clan.clan_cats:
                if cat_id == kit.ID:
                    continue
                the_cat = Cat.all_cats.get(cat_id)
                if not the_cat or the_cat.dead or the_cat.outside:
                    continue
                if the_cat.ID in kit.get_parents():
                    parent_to_kit = game.config["new_cat"]["parent_buff"][
                        "parent_to_kit"
                    ]
                    y = random.randrange(0, 15)
                    start_relation = Relationship(the_cat, kit, False, True)
                    start_relation.platonic_like += parent_to_kit["platonic"] + y
                    start_relation.comfortable = parent_to_kit["comfortable"] + y
                    start_relation.admiration = parent_to_kit["admiration"] + y
                    start_relation.trust = parent_to_kit["trust"] + y
                    the_cat.relationships[kit.ID] = start_relation

                    kit_to_parent = game.config["new_cat"]["parent_buff"][
                        "kit_to_parent"
                    ]
                    y = random.randrange(0, 15)
                    start_relation = Relationship(kit, the_cat, False, True)
                    start_relation.platonic_like += kit_to_parent["platonic"] + y
                    start_relation.comfortable = kit_to_parent["comfortable"] + y
                    start_relation.admiration = kit_to_parent["admiration"] + y
                    start_relation.trust = kit_to_parent["trust"] + y
                    kit.relationships[the_cat.ID] = start_relation

            #### REMOVE ACCESSORY ######
            kit.pelt.accessory = None
            clan.add_cat(kit)

            #### GIVE HISTORY ######
            History.add_beginning(kit, clan_born=bool(cat))

        # check other cats of Clan for siblings
        for kitten in all_kitten:
            # update/buff the relationship towards the siblings
            for second_kitten in all_kitten:
                y = random.randrange(0, 10)
                if second_kitten.ID == kitten.ID:
                    continue
                try:
                    kitten.relationships[second_kitten.ID].platonic_like += 20 + y
                    kitten.relationships[second_kitten.ID].comfortable += 10 + y
                    kitten.relationships[second_kitten.ID].trust += 10 + y
                except:
                    start_relation = Relationship(kitten, second_kitten, False, True)
                    kitten.relationships[second_kitten.ID] = start_relation
                    kitten.relationships[second_kitten.ID].platonic_like = 20 + y
                    kitten.relationships[second_kitten.ID].comfortable = 10 + y
                    kitten.relationships[second_kitten.ID].trust = 10 + y
            
            kitten.create_inheritance_new_cat() # Calculate inheritance. 

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
                    kit_to_parent = game.config["new_cat"]["parent_buff"][
                        "kit_to_parent"
                    ]
                    parent_to_kit = game.config["new_cat"]["parent_buff"][
                        "parent_to_kit"
                    ]
                    change_relationship_values(
                        cats_from=[kit],
                        cats_to=[parent],
                        platonic_like=kit_to_parent["platonic"],
                        dislike=kit_to_parent["dislike"],
                        admiration=kit_to_parent["admiration"],
                        comfortable=kit_to_parent["comfortable"],
                        jealousy=kit_to_parent["jealousy"],
                        trust=kit_to_parent["trust"],
                    )
                    change_relationship_values(
                        cats_from=[parent],
                        cats_to=[kit],
                        platonic_like=parent_to_kit["platonic"],
                        dislike=parent_to_kit["dislike"],
                        admiration=parent_to_kit["admiration"],
                        comfortable=parent_to_kit["comfortable"],
                        jealousy=parent_to_kit["jealousy"],
                        trust=parent_to_kit["trust"],
                    )

        if blood_parent:
            blood_parent.outside = True
            if blood_parent.dead:
                clan.unknown_cats.append(blood_parent.ID)
        if blood_parent2:
            for x in blood_parent2:
                x.outside = True
                if x.dead:
                    clan.unknown_cats.append(x.ID)

        return all_kitten

    @staticmethod
    def get_amount_of_kits(cat, clan):
        """Get the amount of kits which will be born."""
        
        if(clan.clan_settings['modded_kits']):

            one_kit = [1] * game.config["pregnancy"]["one_kit_modded"][cat.age]
            two_kits = [2] * game.config["pregnancy"]["two_kit_modded"][cat.age]
            three_kits = [3] * game.config["pregnancy"]["three_kit_modded"][cat.age]
            four_kits = [4] * game.config["pregnancy"]["four_kit_modded"][cat.age]
            five_kits = [5] * game.config["pregnancy"]["five_kit_modded"][cat.age]
            six_kits = [choice([6, 7, 8])] * game.config["pregnancy"]["six_kit_modded"][cat.age]
            nine_kits = [choice([9, 10, 11, 12])] * game.config["pregnancy"]["nine_kit_modded"][cat.age]
            max_kits = [choice([13, 14, 15, 16, 17, 18, 19])] * game.config["pregnancy"]["max_kit_modded"][cat.age]

            amount = choice(one_kit + two_kits + three_kits + four_kits + five_kits + six_kits + nine_kits + max_kits)

        else:
            min_kits = game.config["pregnancy"]["min_kits"]
            min_kit = [min_kits] * game.config["pregnancy"]["one_kit_possibility"][cat.age]
            two_kits = [min_kits + 1] * game.config["pregnancy"]["two_kit_possibility"][cat.age]
            three_kits = [min_kits + 2] * game.config["pregnancy"]["three_kit_possibility"][cat.age]
            four_kits = [min_kits + 3] * game.config["pregnancy"]["four_kit_possibility"][cat.age]
            five_kits = [min_kits + 4] * game.config["pregnancy"]["five_kit_possibility"][cat.age]
            max_kits = [game.config["pregnancy"]["max_kits"]] * game.config["pregnancy"]["max_kit_possibility"][cat.age]

            amount = choice(min_kit + two_kits + three_kits + four_kits + five_kits + max_kits)
        

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
            mate_relation.romantic_love
            + mate_relation.opposite_relationship.romantic_love
        ) / 2
        average_affair_love = (
            affair_relation.romantic_love
            + affair_relation.opposite_relationship.romantic_love
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
            relation.romantic_love + relation.opposite_relationship.romantic_love
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
        if not (clan.clan_settings['modded_kits']):
            inverse_chance = game.config["pregnancy"]["primary_chance_unmated"]
        else:
            inverse_chance = game.config["pregnancy"]["modded_primary_chance_unmated"]
        if len(first_parent.mate) > 0:
            if not (clan.clan_settings['modded_kits']):
                inverse_chance = game.config["pregnancy"]["primary_chance_mated"]
            else:
                inverse_chance = game.config["pregnancy"]["modded_primary_chance_mated"]

        # SETTINGS
        # - decrease inverse chance if only mated pairs can have kits
        if not clan.clan_settings["single parentage"]:
            inverse_chance = int(inverse_chance * 0.7)

        # - decrease inverse chance if affairs are not allowed
        if not clan.clan_settings["affair"]:
            inverse_chance = int(inverse_chance * 0.7)

        # CURRENT CAT AMOUNT
        # - increase the inverse chance if the clan is bigger
        living_cats = len(
            [i for i in Cat.all_cats.values() if not (i.dead or i.outside or i.exiled)]
        )
        if living_cats < 10:
            inverse_chance = int(inverse_chance * 0.5)
        elif living_cats > 30:
            inverse_chance = int(inverse_chance * (living_cats / 30))

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
                    if not second_parent_relation.opposite_relationship:
                        second_parent_relation.link_relationship()
                else:
                    second_parent_relation = first_parent.create_one_relationship(x)

                x_romantic_love = (second_parent_relation.romantic_love +
                                        second_parent_relation.opposite_relationship.romantic_love) / 2
                if x_romantic_love > average_romantic_love:
                    average_romantic_love = x_romantic_love
                x_comfort = (second_parent_relation.comfortable +
                                second_parent_relation.opposite_relationship.comfortable) / 2
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
        avg_age = int(sum([cat.moons for cat in Cat.all_cats.values()]) / living_cats)
        if avg_age > 80:
            inverse_chance = int(inverse_chance * 0.8)

        # 'INBREED' counter
        # - increase inverse chance if one of the current cats belongs in the biggest family
        if not Pregnancy_Events.biggest_family:  # set the family if not already
            Pregnancy_Events.set_biggest_family()

        InBiggest = False
        if second_parent:
            for x in second_parent:
                if x == "Surrogate":
                    continue
                if x.ID in Pregnancy_Events.biggest_family:
                    InBiggest = True

        if first_parent.ID in Pregnancy_Events.biggest_family or second_parent and InBiggest:
            inverse_chance = int(inverse_chance * 1.7)

        # - decrease inverse chance if the current family is small
        if len(first_parent.get_relatives(clan.clan_settings["first cousin mates"])) < (
            living_cats / 15
        ):
            inverse_chance = int(inverse_chance * 0.7)

        # - decrease inverse chance single parents if settings allow an biggest family is huge
        settings_allow = (
            not second_parent and not clan.clan_settings["single parentage"]
        )
        if settings_allow and Pregnancy_Events.biggest_family_is_big():
            inverse_chance = int(inverse_chance * 0.9)

        return inverse_chance
