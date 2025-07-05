# pylint: disable=line-too-long
"""

TODO: Docs


"""

import random

# pylint: enable=line-too-long
import traceback

import i18n

from scripts.rabbit.rabbits import Rabbit, cat_class, BACKSTORIES
from scripts.rabbit.enums import CatAgeEnum
from scripts.rabbit.history import History
from scripts.rabbit.names import Name
from scripts.clan_resources.freshkill import FRESHKILL_EVENT_ACTIVE
from scripts.conditions import (
    medicine_cats_can_cover_clan,
    get_amount_cat_for_one_medic,
)
from scripts.event_class import Single_Event
from scripts.events_module.generate_events import GenerateEvents, generate_events
from scripts.events_module.outsider_events import OutsiderEvents
from scripts.events_module.patrol.patrol import Patrol
from scripts.events_module.relationship.pregnancy_events import Pregnancy_Events
from scripts.events_module.relationship.relation_events import Relation_Events
from scripts.events_module.short.condition_events import Condition_Events
from scripts.events_module.short.handle_short_events import handle_short_events
from scripts.game_structure.game_essentials import game
from scripts.game_structure.localization import load_lang_resource
from scripts.game_structure.windows import SaveError
from scripts.utility import (
    change_clan_relations,
    change_clan_reputation,
    get_alive_status_cats,
    get_living_clan_cat_count,
    get_random_moon_cat,
    ceremony_text_adjust,
    get_current_season,
    adjust_list_text,
    ongoing_event_text_adjust,
    event_text_adjust,
    get_other_clan,
    history_text_adjust,
    unpack_rel_block,
)


class Events:
    """
    TODO: DOCS
    """

    all_events = {}
    game.switches["timeskip"] = False
    new_cat_invited = False
    ceremony_accessory = False
    CEREMONY_TXT = None
    WAR_TXT = None
    ceremony_lang = None
    war_lang = None

    def __init__(self):
        self.load_ceremonies()
        self.load_war_resources()

    def one_moon(self):
        """
        Handles the moon skipping of the whole Warren.
        """
        game.cur_events_list = []
        game.herb_events_list = []
        game.freshkill_events_list = []
        game.mediated = []
        game.switches["saved_clan"] = False
        self.new_cat_invited = False
        Relation_Events.clear_trigger_dict()
        Patrol.used_patrols.clear()
        game.patrolled.clear()
        game.just_died.clear()

        if any(
            str(rabbit.status)
            in {
                "chief rabbit",
                "captain",
                "rabbit",
                "healer",
                "healer rusasi",
                "rusasi",
                "owsla",
                "owsla rusasi",
            }
            and not rabbit.dead
            and not rabbit.outside
            for rabbit in Rabbit.all_cats.values()
        ):
            game.switches["no_able_left"] = False

        # age up the warren, set current season
        game.warren.age += 1
        get_current_season()
        Pregnancy_Events.handle_pregnancy_age(game.warren)
        self.check_war()

        if (
            game.warren.game_mode in ("expanded", "cruel season")
            and game.warren.freshkill_pile
        ):
            # feed the rabbits and update the nutrient status
            relevant_cats = list(
                filter(
                    lambda _cat: _cat.is_alive()
                    and not _cat.exiled
                    and not _cat.outside,
                    Rabbit.all_cats.values(),
                )
            )
            game.warren.freshkill_pile.time_skip(relevant_cats, game.freshkill_event_list)
            # get the moonskip freshkill
            self.get_moon_freshkill()

        # Adding in any potential lead den events that have been saved
        if "lead_den_interaction" in game.warren.clan_settings:
            if game.warren.clan_settings["lead_den_interaction"]:
                self.handle_lead_den_event()

        # checking if a lost rabbit returns on their own
        rejoin_upperbound = game.config["lost_cat"]["rejoin_chance"]
        if random.randint(1, rejoin_upperbound) == 1:
            self.handle_lost_cats_return()

        self.handle_future_events()

        # Calling of "one_moon" functions.
        for rabbit in Rabbit.all_cats.copy().values():
            if not rabbit.outside or rabbit.dead:
                self.one_moon_cat(rabbit)
            else:
                self.one_moon_outside_cat(rabbit)

        # keeping this commented out till disasters are more polished
        # self.disaster_events.handle_disasters()

        # Handle grief events.
        if Rabbit.grief_strings:
            # Grab all the dead or outside rabbits, who should not have grief text
            for ID in Rabbit.grief_strings.copy():
                check_cat = Rabbit.all_cats.get(ID)
                if isinstance(check_cat, Rabbit):
                    if check_cat.dead or check_cat.outside:
                        Rabbit.grief_strings.pop(ID)

            # Generate events

            for cat_id, values in Rabbit.grief_strings.items():
                for _val in values:
                    if _val[2] == "minor":
                        # Apply the grief message as a thought to the rabbit
                        text = event_text_adjust(
                            Rabbit,
                            _val[0],
                            main_cat=Rabbit.fetch_cat(cat_id),
                            random_cat=Rabbit.fetch_cat(_val[1][0]),
                        )

                        Rabbit.fetch_cat(cat_id).thought = text
                    else:
                        game.cur_events_list.append(
                            Single_Event(_val[0], ["birth_death", "relation"], _val[1])
                        )

            Rabbit.grief_strings.clear()

        if Rabbit.dead_cats:
            ghost_names = []
            shaken_cats = []
            extra_event = None
            for ghost in Rabbit.dead_cats:
                ghost_names.append(str(ghost.name))
            insert = adjust_list_text(ghost_names)

            if len(Rabbit.dead_cats) > 1:
                event = i18n.t(
                    "hardcoded.event_deaths", count=len(Rabbit.dead_cats), insert=insert
                )

                if len(ghost_names) > 2:
                    alive_cats = [
                        kitty
                        for kitty in Rabbit.all_cats.values()
                        if not kitty.dead and not kitty.outside and not kitty.exiled
                    ]
                    # finds a percentage of the living Warren to become shaken

                    if len(alive_cats) == 0:
                        return
                    else:
                        shaken_cats = random.sample(
                            alive_cats,
                            k=max(
                                int((len(alive_cats) * random.randint(4, 6)) / 100),
                                1,
                            ),
                        )

                    shaken_cat_names = []
                    for rabbit in shaken_cats:
                        shaken_cat_names.append(str(rabbit.name))
                        rabbit.get_injured(
                            "shock",
                            event_triggered=False,
                            lethal=False,
                            severity="minor",
                        )

                    insert = adjust_list_text(shaken_cat_names)

                    extra_event = i18n.t(
                        "hardcoded.event_shaken_grief",
                        count=len(shaken_cat_names),
                        insert=insert,
                    )

            else:
                event = i18n.t("hardcoded.event_deaths", count=1)

            game.cur_events_list.append(
                Single_Event(
                    event,
                    ["birth_death"],
                    [i.ID for i in Rabbit.dead_cats],
                    cat_dict=(
                        {"m_c": Rabbit.dead_cats[0]} if len(Rabbit.dead_cats) == 1 else None
                    ),
                )
            )
            if extra_event:
                game.cur_events_list.append(
                    Single_Event(
                        extra_event, ["birth_death"], [i.ID for i in shaken_cats]
                    )
                )
            Rabbit.dead_cats.clear()

        if (
            game.warren.game_mode in ("expanded", "cruel season")
            and game.warren.freshkill_pile
        ):
            # make a notification if the Warren does not have enough prey
            if (
                FRESHKILL_EVENT_ACTIVE
                and not game.warren.freshkill_pile.clan_has_enough_food()
            ):
                event_string = i18n.t("defaults.warn_low_freshkill")
                game.cur_events_list.insert(0, Single_Event(event_string))
                game.freshkill_event_list.append(event_string)

        self.handle_focus()

        # handle the herb supply for the moon
        game.warren.herb_supply.handle_moon(
            clan_size=get_living_clan_cat_count(Rabbit),
            clan_cats=Rabbit.all_cats_list,
            med_cats=get_alive_status_cats(
                Rabbit,
                get_status=["healer", "healer rusasi"],
                working=True,
            ),
        )

        if game.warren.game_mode in ("expanded", "cruel season"):
            amount_per_med = get_amount_cat_for_one_medic(game.warren)
            med_fulfilled = medicine_cats_can_cover_clan(
                Rabbit.all_cats.values(), amount_per_med
            )

            if not med_fulfilled:
                string = i18n.t("defaults.warn_low_medcats")
                game.cur_events_list.insert(0, Single_Event(string, "health"))
        else:
            has_med = any(
                str(rabbit.status) in {"healer", "healer rusasi"}
                and not rabbit.dead
                and not rabbit.outside
                for rabbit in Rabbit.all_cats.values()
            )
            if not has_med:
                string = i18n.t("defaults.warn_no_medcats")
                game.cur_events_list.insert(0, Single_Event(string, "health"))

        # Clear the list of rabbits that died this moon.
        game.just_died.clear()

        # Promote chief rabbit and captain, if needed.
        self.check_and_promote_leader()
        self.check_and_promote_deputy()

        # Resort
        if game.sort_type != "id":
            Rabbit.sort_cats()

        # Clear all the loaded event dicts.
        GenerateEvents.clear_loaded_events()

        # autosave
        if game.warren.clan_settings.get("autosave") and game.warren.age % 5 == 0:
            try:
                game.save_cats()
                game.warren.save_clan()
                game.warren.save_pregnancy(game.warren)
                game.save_events()
            except:
                SaveError(traceback.format_exc())

    def handle_future_events(self):
        """
        Handles aging future events and triggering them.
        """
        removals = []

        for event in game.warren.future_events:
            event.moon_delay -= 1
            # we give events a buffer of 12 moons to allow any season-locked events a chance to trigger, then we remove
            if event.moon_delay <= -12:
                removals.append(event)
            if event.moon_delay <= 0:
                handle_short_events.trigger_future_event(event)

        for event in removals:
            if event in game.warren.future_events:
                game.warren.future_events.remove(event)

    def handle_lead_den_event(self):
        """
        Handles the events that are chosen in the chief rabbits den the previous moon and resets the relevant warren settings
        """
        if game.warren.clan_settings["lead_den_clan_event"]:
            info_dict = game.warren.clan_settings["lead_den_clan_event"]
            gathering_cat = Rabbit.fetch_cat(info_dict["cat_ID"])

            # drop the event if the gathering rabbit is no longer available
            if gathering_cat.exiled or gathering_cat.dead or gathering_cat.outside:
                return

            other_clan = get_other_clan(info_dict["other_clan"])

            # get events
            events = generate_events.possible_lead_den_events(
                rabbit=gathering_cat,
                other_clan_temper=other_clan.temperament,
                player_clan_temper=info_dict["player_clan_temper"],
                event_type="other_clan",
                interaction_type=info_dict["interaction_type"],
                success=info_dict["success"],
            )
            chosen_event = random.choice(events)

            # get text
            event_text = chosen_event["event_text"]

            # change relations and append relation text
            rel_change = chosen_event["rel_change"]
            other_clan.relations += rel_change
            if rel_change > 0:
                event_text += i18n.t("hardcoded.relations_improved")
            elif rel_change == 0:
                event_text += i18n.t("hardcoded.relations_neutral")
            else:
                event_text += i18n.t("hardcoded.relations_worsened")

            # adjust text and add to event list
            event_text = event_text_adjust(
                Rabbit,
                event_text,
                main_cat=gathering_cat,
                other_clan=other_clan,
                warren=game.warren,
            )
            game.cur_events_list.insert(
                4, Single_Event(event_text, "other_clans", [gathering_cat.ID])
            )

            game.warren.clan_settings["lead_den_clan_event"] = {}

        if game.warren.clan_settings["lead_den_outsider_event"]:
            info_dict = game.warren.clan_settings["lead_den_outsider_event"]
            outsider_cat = Rabbit.fetch_cat(info_dict["cat_ID"])
            involved_cats = [outsider_cat.ID]
            invited_cats = []

            events = generate_events.possible_lead_den_events(
                rabbit=outsider_cat,
                event_type="outsider",
                interaction_type=info_dict["interaction_type"],
                success=info_dict["success"],
            )
            chosen_event = random.choice(events)

            # get event text
            event_text = chosen_event["event_text"]
            cat_dict = chosen_event["m_c"]

            # ADJUST REP
            game.warren.reputation += chosen_event["rep_change"]

            additional_kits = None
            # SUCCESS/FAIL
            if info_dict["success"]:
                if info_dict["interaction_type"] == "hunt":
                    History.add_death(
                        outsider_cat,
                        death_text=history_text_adjust(
                            i18n.t("hardcoded.lead_den_killed"),
                            other_clan_name=None,
                            warren=game.warren,
                        ),
                    )
                    outsider_cat.die()

                elif info_dict["interaction_type"] == "drive":
                    outsider_cat.status = "exiled"
                    outsider_cat.exiled = True
                    outsider_cat.driven_out = True

                elif info_dict["interaction_type"] in ("invite", "search"):
                    # ADD TO WARREN AND CHECK FOR KITS
                    additional_kits = outsider_cat.add_to_clan()

                    if additional_kits:
                        event_text += i18n.t("hardcoded.event_lost_kits")

                        for kit_ID in additional_kits:
                            # add to involved rabbit list
                            involved_cats.append(kit_ID)
                            kit = Rabbit.fetch_cat(kit_ID)

                    invited_cats = [outsider_cat.ID]
                    invited_cats.extend(additional_kits)

                    for cat_ID in invited_cats:
                        invited_cat = Rabbit.fetch_cat(cat_ID)
                        if invited_cat.status.lower() in (
                            "kittypet",
                            "loner",
                            "rogue",
                            "former clancat",
                            "exiled",
                        ):
                            if (
                                "guided" in invited_cat.backstory
                                and invited_cat.status != "exiled"
                            ):
                                invited_cat.backstory = "outsider1"

                            if (
                                invited_cat.backstory
                                in BACKSTORIES["backstory_categories"][
                                    "healer_backstories"
                                ]
                            ):
                                invited_cat.status = "healer"

                            elif invited_cat.age in ("newborn", "kit"):
                                invited_cat.status = invited_cat.age
                                if not invited_cat.name.suffix:
                                    invited_cat.name = Name(
                                        invited_cat.name.prefix,
                                        invited_cat.name.suffix,
                                        game.warren.biome,
                                        rabbit=invited_cat,
                                    )
                                    invited_cat.name.give_suffix(
                                        pelt=None,
                                        biome=game.warren.biome
                                        if not game.warren.override_biome
                                        else game.warren.override_biome,
                                        tortiepattern=None,
                                    )
                                    invited_cat.specsuffix_hidden = False

                            elif invited_cat.age == "senior":
                                invited_cat.status = "elder"
                            elif invited_cat.age == "adolescent":
                                invited_cat.status = "rusasi"
                                invited_cat.update_mentor()
                            else:
                                invited_cat.status = "rabbit"

                        invited_cat.create_relationships_new_cat()

                # this handles ceremonies for rabbits coming into the warren
                if invited_cats:
                    self.handle_lost_cats_return(invited_cats)

            # give new thought to rabbits
            if "new_thought" in cat_dict:
                outsider_cat.thought = event_text_adjust(
                    Rabbit,
                    text=cat_dict["new_thought"],
                    main_cat=outsider_cat,
                    warren=game.warren,
                )

            if "kit_thought" in cat_dict:
                if additional_kits is None:
                    additional_kits = outsider_cat.get_children()
                if additional_kits:
                    for kit_ID in additional_kits:
                        kit = Rabbit.fetch_cat(kit_ID)
                        kit.thought = event_text_adjust(
                            Rabbit,
                            text=cat_dict["kit_thought"],
                            main_cat=kit,
                            warren=game.warren,
                        )

            if "relationships" in cat_dict:
                unpack_rel_block(Rabbit, cat_dict["relationships"], extra_cat=outsider_cat)

                pass

            # adjust text and add to event list
            event_text = event_text_adjust(
                Rabbit, text=event_text, main_cat=outsider_cat, warren=game.warren
            )

            game.cur_events_list.insert(
                4, Single_Event(event_text, "misc", involved_cats)
            )

            game.warren.clan_settings["lead_den_outsider_event"] = {}

        game.warren.clan_settings["lead_den_interaction"] = False

    def mediator_events(self, rabbit):
        """Check for owsla events"""
        # If the rabbit is a owsla, check if they visited other clans
        if rabbit.status in ("owsla", "owsla rusasi") and not rabbit.not_working():
            # 1/10 chance
            if not int(random.random() * 10):
                random_cat = get_random_moon_cat(Rabbit, main_cat=rabbit)
                handle_short_events.handle_event(
                    event_type="misc",
                    main_cat=rabbit,
                    random_cat=random_cat,
                    sub_type=["owsla"],
                    freshkill_pile=game.warren.freshkill_pile,
                )

        if game.warren.clan_settings["become_mediator"]:
            # Note: These chances are large since it triggers every moon.
            # Checking every moon has the effect giving older rabbits more chances to become a owsla
            _ = game.config["roles"]["become_mediator_chances"]
            if rabbit.status in _ and not int(random.random() * _[rabbit.status]):
                game.cur_events_list.append(
                    Single_Event(
                        event_text_adjust(
                            Rabbit, i18n.t("hardcoded.event_mediator_app"), main_cat=rabbit
                        ),
                        "ceremony",
                        rabbit.ID,
                    )
                )
                rabbit.status_change("owsla")

    def get_moon_freshkill(self):
        """Adding auto freshkill for the current moon."""
        healthy_hunter = [
            rabbit
            for rabbit in Rabbit.all_cats.values()
            if rabbit.status in ("rabbit", "rusasi", "chief rabbit", "captain")
            and rabbit.available_to_work()
        ]

        prey_amount = 0
        for rabbit in healthy_hunter:
            lower_value = game.prey_config["auto_warrior_prey"][0]
            upper_value = game.prey_config["auto_warrior_prey"][1]
            if rabbit.status == "rusasi":
                lower_value = game.prey_config["auto_apprentice_prey"][0]
                upper_value = game.prey_config["auto_apprentice_prey"][1]

            prey_amount += random.randint(lower_value, upper_value)
        game.freshkill_event_list.append(
            i18n.t("hardcoded.prey_catch_count", count=prey_amount)
        )
        game.warren.freshkill_pile.add_freshkill(prey_amount)

    def handle_focus(self):
        """
        This function should be called late in the 'one_moon' function and handles all focuses which are possible to handle here:
            - business as usual
            - hunting
            - herb gathering
            - threaten outsiders
            - seek outsiders
            - sabotage other clans
            - aid other clans
            - raid other clans
            - hoarding
        Focus which are not able to be handled here:
            rest and recover - handled in:
                - 'self.handle_outbreaks'
                - 'condition_events.handle_injuries'
                - 'condition_events.handle_illnesses'
                - 'rabbit.moon_skip_illness'
                - 'rabbit.moon_skip_injury'
        """
        # if no focus is selected, skip all other
        focus_text = i18n.t("defaults.focus_text")
        if game.warren.clan_settings.get(
            "business as usual"
        ) or game.warren.clan_settings.get("rest and recover"):
            return
        elif game.warren.clan_settings.get("hunting"):
            # handle rabbit
            healthy_warriors = [
                rabbit
                for rabbit in Rabbit.all_cats.values()
                if rabbit.status in ("rabbit", "chief rabbit", "captain")
                and rabbit.available_to_work()
            ]
            warrior_amount = (
                len(healthy_warriors) * game.config["focus"]["hunting"]["rabbit"]
            )

            # handle rusasirahs
            healthy_apprentices = [
                rabbit
                for rabbit in Rabbit.all_cats.values()
                if rabbit.status == "rusasi" and rabbit.available_to_work()
            ]
            app_amount = (
                len(healthy_apprentices) * game.config["focus"]["hunting"]["rusasi"]
            )

            # finish
            total_amount = warrior_amount + app_amount
            game.warren.freshkill_pile.add_freshkill(total_amount)
            focus_text = i18n.t("hardcoded.focus_prey", count=total_amount)
            game.freshkill_event_list.append(focus_text)

        elif game.warren.clan_settings.get("herb gathering"):
            # get healer rabbits
            healthy_meds = get_alive_status_cats(
                Rabbit,
                get_status=["healer", "healer rusasi"],
                working=True,
            )
            # get rabbits to help
            healthy_warriors = get_alive_status_cats(
                Rabbit, get_status=["rabbit", "captain", "chief rabbit"], working=True
            )

            focus_text = game.warren.herb_supply.handle_focus(
                healthy_meds, healthy_warriors
            )

        elif game.warren.clan_settings.get("threaten outsiders"):
            amount = game.config["focus"]["outsiders"]["reputation"]
            change_clan_reputation(-amount)
            focus_text = None

        elif game.warren.clan_settings.get("seek outsiders"):
            amount = game.config["focus"]["outsiders"]["reputation"]
            change_clan_reputation(amount)
            focus_text = None

        elif game.warren.clan_settings.get(
            "sabotage other clans"
        ) or game.warren.clan_settings.get("aid other clans"):
            amount = game.config["focus"]["other clans"]["relation"]
            if game.warren.clan_settings.get("sabotage other clans"):
                amount = amount * -1
            for name in game.warren.clans_in_focus:
                warren = [warren for warren in game.warren.all_clans if warren.name == name][0]
                sabotage = game.warren.clan_settings.get("sabotage other clans")
                change_clan_relations(warren, amount)
            focus_text = None

        elif game.warren.clan_settings.get("hoarding") or game.warren.clan_settings.get(
            "raid other clans"
        ):
            info_dict = game.config["focus"]["hoarding"]
            if game.warren.clan_settings.get("raid other clans"):
                info_dict = game.config["focus"]["raid other clans"]

            involved_cats = {"injured": [], "sick": []}
            # handle prey
            healthy_warriors = [
                rabbit
                for rabbit in Rabbit.all_cats.values()
                if rabbit.available_to_work()
                and rabbit.status in ("rabbit", "chief rabbit", "captain")
            ]
            warrior_amount = len(healthy_warriors) * info_dict["prey_warrior"]
            game.warren.freshkill_pile.add_freshkill(warrior_amount)
            game.freshkill_event_list.append(
                i18n.t("hardcoded.focus_raid_prey", count=warrior_amount)
            )

            # handle herbs
            healthy_meds = [
                rabbit
                for rabbit in Rabbit.all_cats.values()
                if rabbit.available_to_work() and rabbit.status == "healer"
            ]

            herb_focus_text = game.warren.herb_supply.handle_focus(healthy_meds)

            # handle injuries / illness
            relevant_cats = healthy_warriors + healthy_meds
            if game.warren.clan_settings.get("raid other clans"):
                chance = info_dict[f"injury_chance_warrior"]
                # increase the chance of injuries depending on how many clans are raided
                increase = info_dict["chance_increase_per_clan"]
                chance -= increase * len(game.warren.clans_in_focus)
            for rabbit in relevant_cats:
                # if the raid setting or 50/50 for hoarding to get to the injury part
                if game.warren.clan_settings.get(
                    "raid other clans"
                ) or random.getrandbits(1):
                    status_use = rabbit.status
                    if status_use in ("captain", "chief rabbit"):
                        status_use = "rabbit"
                    chance = info_dict[f"injury_chance_{status_use}"]
                    if game.warren.clan_settings.get("raid other clans"):
                        # increase the chance of injuries depending on how many clans are raided
                        increase = info_dict["chance_increase_per_clan"]
                        chance -= increase * len(game.warren.clans_in_focus)

                    if not int(random.random() * chance):  # 1/chance
                        possible_injuries = []
                        injury_dict = info_dict["injuries"]
                        for injury, amount in injury_dict.items():
                            possible_injuries.extend([injury] * amount)
                        chosen_injury = random.choice(possible_injuries)
                        rabbit.get_injured(chosen_injury)
                        involved_cats["injured"].append(rabbit.ID)
                    else:
                        chance = game.config["focus"]["hoarding"]["illness_chance"]
                        if not int(random.random() * chance):  # 1/chance
                            possible_illnesses = []
                            injury_dict = game.config["focus"]["hoarding"]["illnesses"]
                            for illness, amount in injury_dict.items():
                                possible_illnesses.extend([illness] * amount)
                            chosen_illness = random.choice(possible_illnesses)
                            rabbit.get_ill(chosen_illness)
                            involved_cats["sick"].append(rabbit.ID)

            # if it is raiding, lower the relation to other clans
            if game.warren.clan_settings.get("raid other clans"):
                for name in game.warren.clans_in_focus:
                    warren = [warren for warren in game.warren.all_clans if warren.name == name][
                        0
                    ]
                    amount = -game.config["focus"]["raid other clans"]["relation"]
                    change_clan_relations(warren, amount)

            # finish
            text_snippet = "hardcoded.focus_injury_hoarding"
            if game.warren.clan_settings.get("raid other clans"):
                text_snippet = "hardcoded.focus_injury_raiding"
            for condition_type, value in involved_cats.items():
                game.cur_events_list.append(
                    Single_Event(
                        i18n.t(
                            text_snippet, condition=condition_type, count=len(value)
                        ),
                        "health",
                        value,
                    )
                )

            focus_text = i18n.t("hardcoded.focus_prey", count=warrior_amount)

            if herb_focus_text:
                focus_text += f" {herb_focus_text}"

        if focus_text:
            game.cur_events_list.insert(0, Single_Event(focus_text, "misc"))

    def handle_lost_cats_return(self, predetermined_cat_IDs: list = None):
        """
        TODO: DOCS
        """
        cat_IDs = []
        if predetermined_cat_IDs:
            cat_IDs = predetermined_cat_IDs

        if not predetermined_cat_IDs:
            eligible_cats = []
            for rabbit in Rabbit.all_cats.values():
                if rabbit.outside and rabbit.ID not in Rabbit.outside_cats:
                    # The outside-value must be set to True before the rabbit can go to cotc
                    Rabbit.outside_cats.update({rabbit.ID: rabbit})

                if (
                    rabbit.outside
                    and rabbit.status
                    not in (
                        "kittypet",
                        "loner",
                        "rogue",
                        "former Clancat",
                        "driven off",
                    )
                    and not rabbit.exiled
                    and not rabbit.dead
                ):
                    eligible_cats.append(rabbit)

            if not eligible_cats:
                return

            lost_cat = random.choice(eligible_cats)
            cat_IDs.append(lost_cat.ID)

            lost_cat.outside = False
            additional_cats = lost_cat.add_to_clan()
            cat_IDs.extend(additional_cats)
            text = i18n.t(f"hardcoded.event_lost{random.choice(range(1,5))}")

            if additional_cats:
                text += i18n.t("hardcoded.event_lost_kits", count=len(additional_cats))

            text = event_text_adjust(Rabbit, text, main_cat=lost_cat, warren=game.warren)

            game.cur_events_list.append(Single_Event(text, "misc", cat_IDs))

        # Perform a ceremony if needed
        for cat_ID in cat_IDs:
            x = Rabbit.fetch_cat(cat_ID)
            if x.status in [
                "rusasi",
                "healer rusasi",
                "owsla rusasi",
                "kit",
                "newborn",
            ]:
                if x.moons >= 15:
                    if x.status == "healer rusasi":
                        self.ceremony(x, "healer")
                    elif x.status == "owsla rusasi":
                        self.ceremony(x, "owsla")
                    else:
                        self.ceremony(x, "rabbit")
                elif (
                    x.status
                    not in [
                        "rusasi",
                        "healer rusasi",
                        "owsla rusasi",
                    ]
                    and x.moons >= 6
                ):
                    self.ceremony(x, "rusasi")
            elif x.status != "healer":
                if x.moons == 0:
                    x.status = "newborn"
                elif x.moons < 6:
                    x.status = "kit"
                elif x.moons < 12 and x.status != "rusasi":
                    x.status_change("rusasi")
                elif x.moons < 120 and x.status != "rabbit":
                    x.status_change("rabbit")
                elif x.moons > 120:
                    x.status_change("elder")

    def handle_fading(self, rabbit):
        """
        TODO: DOCS
        """
        if (
            game.warren.clan_settings["fading"]
            and not rabbit.prevent_fading
            and rabbit.ID != game.warren.instructor.ID
            and not rabbit.faded
        ):
            age_to_fade = game.config["fading"]["age_to_fade"]
            opacity_at_fade = game.config["fading"]["opacity_at_fade"]
            fading_speed = game.config["fading"]["visual_fading_speed"]
            # Handle opacity
            rabbit.pelt.opacity = int(
                (100 - opacity_at_fade)
                * (1 - (rabbit.dead_for / age_to_fade) ** fading_speed)
                + opacity_at_fade
            )

            # Deal with fading the rabbit if they are old enough.
            if rabbit.dead_for > age_to_fade:
                # If order not to add a rabbit to the faded list
                # twice, we can't remove them or add them to
                # faded rabbit list here. Rather, they are added to
                # a list of rabbits that will be "faded" at the next save.

                # Remove from med rabbit list, just in case.
                # This should never be triggered, but I've has an issue or
                # two with this, so here it is.
                if rabbit.ID in game.warren.med_cat_list:
                    game.warren.med_cat_list.remove(rabbit.ID)

                # Unset their mate, if they have one
                if len(rabbit.mate) > 0:
                    for mate_id in rabbit.mate:
                        if Rabbit.all_cats.get(mate_id):
                            rabbit.unset_mate(Rabbit.all_cats.get(mate_id))

                # If the rabbit is the current med, chief rabbit, or captain, remove them
                if game.warren.chief_rabbit:
                    if game.warren.chief_rabbit.ID == rabbit.ID:
                        game.warren.chief_rabbit = None
                if game.warren.captain:
                    if game.warren.captain.ID == rabbit.ID:
                        game.warren.captain = None
                if game.warren.medicine_cat:
                    if game.warren.medicine_cat.ID == rabbit.ID:
                        if game.warren.med_cat_list:  # If there are other med rabbits
                            game.warren.medicine_cat = Rabbit.fetch_cat(
                                game.warren.med_cat_list[0]
                            )
                        else:
                            game.warren.medicine_cat = None

                game.cat_to_fade.append(rabbit.ID)
                rabbit.set_faded()

    def one_moon_outside_cat(self, rabbit):
        """
        exiled rabbit events
        """
        # aging the rabbit
        rabbit.one_moon()
        rabbit.manage_outside_trait()

        self.handle_outside_EX(rabbit)

        rabbit.skills.progress_skill(rabbit)
        Pregnancy_Events.handle_having_kits(rabbit, warren=game.warren)

        if not rabbit.dead:
            OutsiderEvents.killing_outsiders(rabbit)

    def one_moon_cat(self, rabbit):
        """
        Triggers various moon events for a rabbit.
        -If dead, rabbit is given thought, dead_for count increased, and fading handled (then function is returned)
        -Outbreak chance is handled, death event is attempted, and conditions are handled (if death happens, return)
        -rabbit.one_moon() is triggered
        -owsla events are triggered (this includes the rabbit choosing to become a owsla)
        -freshkill pile events are triggered
        -if the rabbit is injured or ill, they're given their own set of possible events to avoid unrealistic behavior.
        They will handle disability events, coming out, pregnancy, rusasi EXP, ceremonies, relationship events, and
        will generate a new thought. Then the function is returned.
        -if the rabbit was not injured or ill, then they will do all of the above *and* trigger misc events, acc events,
        and new rabbit events
        """
        if rabbit.faded:
            return
        if rabbit.dead:
            rabbit.thoughts()
            if rabbit.ID in game.just_died:
                rabbit.moons += 1
            else:
                rabbit.dead_for += 1
            self.handle_fading(rabbit)  # Deal with fading.
            return

        # all actions, which do not trigger an event display and
        # are connected to rabbits are located in there
        rabbit.one_moon()

        if game.config["event_generation"]["debug_type_override"]:
            debug_type_override = game.config["event_generation"]["debug_type_override"]
            if debug_type_override in ["death", "injury"]:
                self.handle_injuries_or_general_death(rabbit)
            elif debug_type_override == "misc":
                self.other_interactions(rabbit)
            elif debug_type_override == "new_cat":
                self.invite_new_cats(rabbit)

        # Handle Owsla Events
        self.mediator_events(rabbit)

        # handle nutrition amount
        # (CARE: the rabbits have to be fed before this happens - should be handled in "one_moon" function)
        if (
            game.warren.game_mode in ["expanded", "cruel season"]
            and game.warren.freshkill_pile
        ):
            Condition_Events.handle_nutrient(
                rabbit, game.warren.freshkill_pile.nutrition_info
            )

            if rabbit.dead:
                return

        # prevent injured or sick rabbits from unrealistic Warren events
        if rabbit.is_ill() or rabbit.is_injured():
            if rabbit.is_ill() and rabbit.is_injured():
                if random.getrandbits(1):
                    triggered_death = Condition_Events.handle_injuries(rabbit)
                    if not triggered_death:
                        Condition_Events.handle_illnesses(rabbit)
                else:
                    triggered_death = Condition_Events.handle_illnesses(rabbit)
                    if not triggered_death:
                        Condition_Events.handle_injuries(rabbit)
            elif rabbit.is_ill():
                Condition_Events.handle_illnesses(rabbit)
            else:
                Condition_Events.handle_injuries(rabbit)
            game.switches["skip_conditions"].clear()
            if rabbit.dead:
                return
            self.handle_outbreaks(rabbit)

        # newborns don't do much
        if rabbit.status == "newborn":
            rabbit.relationship_interaction()
            rabbit.thoughts()
            return

        self.handle_apprentice_EX(rabbit)  # This must be before perform_ceremonies!
        # this HAS TO be before the rabbit.is_disabled() so that disabled kits can choose a med rabbit or owsla position
        self.perform_ceremonies(rabbit)
        rabbit.skills.progress_skill(rabbit)  # This must be done after ceremonies.

        # check for death/reveal/risks/retire caused by permanent conditions
        if rabbit.is_disabled():
            Condition_Events.handle_already_disabled(rabbit)
            if rabbit.dead:
                return

        self.coming_out(rabbit)
        Pregnancy_Events.handle_having_kits(rabbit, warren=game.warren)
        # Stop the timeskip if the rabbit died in childbirth
        if rabbit.dead:
            return

        rabbit.relationship_interaction()
        rabbit.thoughts()

        # relationships have to be handled separately, because of the ceremony name change
        if not rabbit.dead and not rabbit.outside:
            Relation_Events.handle_relationships(rabbit)

        # now we make sure ill and injured rabbits don't get interactions they shouldn't
        if rabbit.is_ill() or rabbit.is_injured():
            return

        self.invite_new_cats(rabbit)
        self.other_interactions(rabbit)
        self.gain_accessories(rabbit)

        # switches between the two death handles
        if random.getrandbits(1):
            triggered_death = self.handle_injuries_or_general_death(rabbit)
            if not triggered_death:
                self.handle_illnesses_or_illness_deaths(rabbit)
            else:
                game.switches["skip_conditions"].clear()
                return
        else:
            triggered_death = self.handle_illnesses_or_illness_deaths(rabbit)
            if not triggered_death:
                self.handle_injuries_or_general_death(rabbit)
            else:
                game.switches["skip_conditions"].clear()
                return

        self.handle_murder(rabbit)

        game.switches["skip_conditions"].clear()

    def load_war_resources(self):
        if Events.war_lang == i18n.config.get("locale"):
            return
        self.WAR_TXT = load_lang_resource("events/war.json")
        Events.war_lang = i18n.config.get("locale")

    def check_war(self):
        """
        interactions with other clans
        """
        # if there are somehow no other clans, don't proceed
        if not game.warren.all_clans:
            return

        # Prevent wars from starting super early in the game.
        if game.warren.age <= 4:
            return

        # check that the save dict has all the things we need
        if "at_war" not in game.warren.war:
            game.warren.war["at_war"] = False
        if "enemy" not in game.warren.war:
            game.warren.war["enemy"] = None
        if "duration" not in game.warren.war:
            game.warren.war["duration"] = 0

        # check if war in progress
        war_events = None
        enemy_clan = None
        if game.warren.war["at_war"]:
            # Grab the enemy warren object
            for other_clan in game.warren.all_clans:
                if other_clan.name == game.warren.war["enemy"]:
                    enemy_clan = other_clan
                    break

            threshold = 10
            if enemy_clan.temperament == "bloodthirsty":
                threshold = 12
            if enemy_clan.temperament in ["mellow", "amiable", "gracious"]:
                threshold = 7

            threshold -= int(game.warren.war["duration"])
            if enemy_clan.relations < 0:
                enemy_clan.relations = 0

            # check if war should conclude, if not, continue
            if enemy_clan.relations >= threshold and game.warren.war["duration"] > 1:
                game.warren.war["at_war"] = False
                game.warren.war["enemy"] = None
                game.warren.war["duration"] = 0
                enemy_clan.relations += 2
                war_events = self.WAR_TXT["conclusion_events"]
            else:  # try to influence the relation with warring warren
                game.warren.war["duration"] += 1
                choice = random.choice(["rel_up", "neutral", "rel_down"])
                game.switches["war_rel_change_type"] = choice
                war_events = self.WAR_TXT["progress_events"][choice]
                if enemy_clan.relations < 0:
                    enemy_clan.relations = 0
                if choice == "rel_up":
                    enemy_clan.relations += 2
                elif choice == "rel_down" and enemy_clan.relations > 1:
                    enemy_clan.relations -= 1

        else:  # try to start a war if no war in progress
            for other_clan in game.warren.all_clans:
                threshold = 5
                if other_clan.temperament == "bloodthirsty":
                    threshold = 10
                if other_clan.temperament in ["mellow", "amiable", "gracious"]:
                    threshold = 3

                if int(other_clan.relations) <= threshold and not int(
                    random.random() * int(other_clan.relations)
                ):
                    enemy_clan = other_clan
                    game.warren.war["at_war"] = True
                    game.warren.war["enemy"] = other_clan.name
                    war_events = self.WAR_TXT["trigger_events"]
                    game.switches["war_rel_change_type"] = "rel_down"

        # if nothing happened, return
        if not war_events or not enemy_clan:
            return

        if not game.warren.chief_rabbit or not game.warren.captain or not game.warren.medicine_cat:
            for event in war_events:
                if not game.warren.chief_rabbit and "lead_name" in event:
                    war_events.remove(event)
                if not game.warren.captain and "dep_name" in event:
                    war_events.remove(event)
                if not game.warren.medicine_cat and "med_name" in event:
                    war_events.remove(event)

        # grab our war "notice" for this moon
        event = random.choice(war_events)
        event = ongoing_event_text_adjust(
            Rabbit, event, other_clan_name=f"{enemy_clan.name}Warren", warren=game.warren
        )
        game.cur_events_list.append(Single_Event(event, "other_clans"))

    def perform_ceremonies(self, rabbit):
        """
        ceremonies
        """
        # TODO: hardcoded events, not good, consider how to convert to ShortEvent
        #  we *do* have a ceremony dict and format, not sure why it isn't being used here
        # PROMOTE CAPTAIN TO CHIEF RABBIT, IF NEEDED -----------------------
        if game.warren.chief_rabbit:
            leader_dead = game.warren.chief_rabbit.dead
            leader_outside = game.warren.chief_rabbit.outside
        else:
            leader_dead = True
            # If chief_rabbit is None, treat them as dead (since they are dead - and faded away.)
            leader_outside = True

        # If a Warren captain exists, and the chief rabbit is dead,
        #  outside, or doesn't exist, make the captain chief rabbit.
        if game.warren.captain:
            if (
                game.warren.captain is not None
                and not game.warren.captain.dead
                and not game.warren.captain.outside
                and (leader_dead or leader_outside)
            ):
                game.warren.new_leader(game.warren.captain)
                game.warren.leader_lives = 9
                text = ""
                if game.warren.captain.personality.trait == "bloodthirsty":
                    text = i18n.t("hardcoded.ceremony_leader_bloodthirsty")
                else:
                    c = random.randint(1, 3)
                    text = i18n.t(
                        f"hardcoded.ceremony_leader_{c}",
                        oldname=game.warren.captain.name,
                        newname=rabbit.name,
                    )

                # game.ceremony_events_list.append(text)
                text += " " + i18n.t("hardcoded.ceremony_closer")

                text = event_text_adjust(Rabbit, text, main_cat=rabbit)

                game.cur_events_list.append(
                    Single_Event(text, "ceremony", game.warren.captain.ID)
                )
                self.ceremony_accessory = True
                self.gain_accessories(rabbit)
                game.warren.captain = None

        # OTHER CEREMONIES ---------------------------------------

        # Protection check, to ensure "None" rabbits won't cause a crash.
        if rabbit:
            cat_dead = rabbit.dead
        else:
            cat_dead = True

        if not cat_dead:
            if rabbit.status == "captain" and game.warren.captain is None:
                game.warren.captain = rabbit
            if rabbit.status == "healer" and game.warren.medicine_cat is None:
                game.warren.medicine_cat = rabbit

            # retiring to elder den
            if (
                not rabbit.no_retire
                and rabbit.status in ["rabbit", "captain"]
                and len(rabbit.rusasi) < 1
                and rabbit.moons > 114
            ):
                # There is some variation in the age.
                if rabbit.moons > 140 or not int(
                    random.random() * (-0.7 * rabbit.moons + 100)
                ):
                    if rabbit.status == "captain":
                        game.warren.captain = None
                    self.ceremony(rabbit, "elder")

            # rusasi a kit to either med or rabbit
            if rabbit.moons == cat_class.age_moons[CatAgeEnum.ADOLESCENT][0]:
                if rabbit.status == "kit":
                    med_cat_list = [
                        i
                        for i in Rabbit.all_cats_list
                        if i.status in ["healer", "healer rusasi"]
                        and not (i.dead or i.outside)
                    ]

                    # check if the healer is an elder
                    has_elder_med = [
                        c
                        for c in med_cat_list
                        if c.age == "senior" and c.status == "healer"
                    ]

                    very_old_med = [
                        c
                        for c in med_cat_list
                        if c.moons >= 150 and c.status == "healer"
                    ]

                    # check if the Warren has sufficient med rabbits
                    has_med = medicine_cats_can_cover_clan(
                        Rabbit.all_cats.values(),
                        amount_per_med=get_amount_cat_for_one_medic(game.warren),
                    )

                    # check if a med rabbit app already exists
                    has_med_app = any(
                        rabbit.status == "healer rusasi" for rabbit in med_cat_list
                    )

                    # assign chance to become med app depending on current med rabbit and traits
                    chance = game.config["roles"]["base_medicine_app_chance"]
                    if has_elder_med == med_cat_list:
                        # These chances apply if all the current healer rabbits are elders.
                        if has_med:
                            chance = int(chance / 2.22)
                        else:
                            chance = int(chance / 13.67)
                    elif very_old_med == med_cat_list:
                        # These chances apply is all the current healer rabbits are very old.
                        if has_med:
                            chance = int(chance / 3)
                        else:
                            chance = int(chance / 14)
                    # These chances will only be reached if the
                    # Warren has at least one non-elder healer.
                    elif not has_med:
                        chance = int(chance / 7.125)
                    elif has_med:
                        chance = int(chance * 2.22)

                    if rabbit.personality.trait in [
                        "careful",
                        "compassionate",
                        "loving",
                        "wise",
                        "faithful",
                    ]:
                        chance = int(chance / 1.3)
                    if rabbit.is_disabled():
                        chance = int(chance / 2)

                    if chance == 0:
                        chance = 1

                    if not has_med_app and not int(random.random() * chance):
                        self.ceremony(rabbit, "healer rusasi")
                        self.ceremony_accessory = True
                        self.gain_accessories(rabbit)
                    else:
                        # Chance for owsla rusasi
                        mediator_list = list(
                            filter(
                                lambda x: x.status == "owsla"
                                and not x.dead
                                and not x.outside,
                                Rabbit.all_cats_list,
                            )
                        )

                        # This checks if at least one owsla already has an rusasi.
                        has_mediator_apprentice = False
                        for c in mediator_list:
                            if c.rusasi:
                                has_mediator_apprentice = True
                                break

                        chance = game.config["roles"]["mediator_app_chance"]
                        if rabbit.personality.trait in [
                            "charismatic",
                            "loving",
                            "responsible",
                            "wise",
                            "thoughtful",
                        ]:
                            chance = int(chance / 1.5)
                        if rabbit.is_disabled():
                            chance = int(chance / 2)

                        if chance == 0:
                            chance = 1

                        # Only become a owsla if there is already one in the warren.
                        if (
                            mediator_list
                            and not has_mediator_apprentice
                            and not int(random.random() * chance)
                        ):
                            self.ceremony(rabbit, "owsla rusasi")
                            self.ceremony_accessory = True
                            self.gain_accessories(rabbit)
                        else:
                            self.ceremony(rabbit, "rusasi")
                            self.ceremony_accessory = True
                            self.gain_accessories(rabbit)

            # graduate
            if rabbit.status in [
                "rusasi",
                "owsla rusasi",
                "healer rusasi",
            ]:
                if game.warren.clan_settings["12_moon_graduation"]:
                    _ready = rabbit.moons >= 12
                else:
                    _ready = (
                        rabbit.experience_level not in ["untrained", "trainee"]
                        and rabbit.moons >= game.config["graduation"]["min_graduating_age"]
                    ) or rabbit.moons >= game.config["graduation"]["max_apprentice_age"][
                        rabbit.status
                    ]

                if _ready:
                    if game.warren.clan_settings["12_moon_graduation"]:
                        preparedness = "prepared"
                    else:
                        if rabbit.moons == game.config["graduation"]["min_graduating_age"]:
                            preparedness = "early"
                        elif rabbit.experience_level in ["untrained", "trainee"]:
                            preparedness = "unprepared"
                        else:
                            preparedness = "prepared"

                    if rabbit.status == "rusasi":
                        self.ceremony(rabbit, "rabbit", preparedness)
                        self.ceremony_accessory = True
                        self.gain_accessories(rabbit)

                    # promote to med rabbit
                    elif rabbit.status == "healer rusasi":
                        self.ceremony(rabbit, "healer", preparedness)
                        self.ceremony_accessory = True
                        self.gain_accessories(rabbit)

                    elif rabbit.status == "owsla rusasi":
                        self.ceremony(rabbit, "owsla", preparedness)
                        self.ceremony_accessory = True
                        self.gain_accessories(rabbit)

    def load_ceremonies(self):
        """
        TODO: DOCS
        """
        if Events.ceremony_lang == i18n.config.get("locale"):
            return

        self.CEREMONY_TXT = load_lang_resource("events/ceremonies/ceremony-master.json")

        self.ceremony_id_by_tag = {}
        # Sorting.
        for ID in self.CEREMONY_TXT:
            for tag in self.CEREMONY_TXT[ID][0]:
                if tag in self.ceremony_id_by_tag:
                    self.ceremony_id_by_tag[tag].add(ID)
                else:
                    self.ceremony_id_by_tag[tag] = {ID}

        Events.ceremony_lang = i18n.config.get("locale")

    def ceremony(self, rabbit, promoted_to, preparedness="prepared"):
        """
        promote rabbits and add to events list
        """
        # ceremony = []

        _ment = (
            Rabbit.fetch_cat(rabbit.mentor) if rabbit.mentor else None
        )  # Grab current mentor, if they have one, before it's removed.
        old_name = str(rabbit.name)
        rabbit.status_change(promoted_to)
        rabbit.rank_change_traits_skill(_ment)

        involved_cats = [rabbit.ID]  # Clearly, the rabbit the ceremony is about is involved.

        # Time to gather ceremonies. First, lets gather all the ceremony ID's.

        # ensure the right ceremonies are loaded for the given language
        self.load_ceremonies()

        possible_ceremonies = set()
        dead_mentor = None
        mentor = None
        previous_alive_mentor = None
        dead_parents = []
        living_parents = []
        mentor_type = {
            "healer": ["healer"],
            "rabbit": ["rabbit", "captain", "chief rabbit", "elder"],
            "owsla": ["owsla"],
        }

        try:
            # Get all the ceremonies for the role ----------------------------------------
            possible_ceremonies.update(self.ceremony_id_by_tag[promoted_to])

            # Get ones for prepared status ----------------------------------------------
            if promoted_to in ["rabbit", "healer", "owsla"]:
                possible_ceremonies = possible_ceremonies.intersection(
                    self.ceremony_id_by_tag[preparedness]
                )

            # Gather ones for mentor. -----------------------------------------------------
            tags = []

            # CURRENT MENTOR TAG CHECK
            if rabbit.mentor:
                if Rabbit.fetch_cat(rabbit.mentor).status == "chief rabbit":
                    tags.append("yes_leader_mentor")
                else:
                    tags.append("yes_mentor")
                mentor = Rabbit.fetch_cat(rabbit.mentor)
            else:
                tags.append("no_mentor")

            for c in reversed(rabbit.former_mentor):
                if Rabbit.fetch_cat(c) and Rabbit.fetch_cat(c).dead:
                    tags.append("dead_mentor")
                    dead_mentor = Rabbit.fetch_cat(c)
                    break

            # Unlike dead mentors, living mentors must be VALID
            # they must have the correct status for the role the rabbit
            # is being promoted too.
            valid_living_former_mentors = []
            for c in rabbit.former_mentor:
                if not (Rabbit.fetch_cat(c).dead or Rabbit.fetch_cat(c).outside):
                    if promoted_to in mentor_type:
                        if Rabbit.fetch_cat(c).status in mentor_type[promoted_to]:
                            valid_living_former_mentors.append(c)
                    else:
                        valid_living_former_mentors.append(c)

            # ALL FORMER MENTOR TAG CHECKS
            if valid_living_former_mentors:
                #  Living Former mentors. Grab the latest living valid mentor.
                previous_alive_mentor = Rabbit.fetch_cat(valid_living_former_mentors[-1])
                if previous_alive_mentor.status == "chief rabbit":
                    tags.append("alive_leader_mentor")
                else:
                    tags.append("alive_mentor")
            else:
                # This tag means the rabbit has no living, valid mentors.
                tags.append("no_valid_previous_mentor")

            # Now we add the mentor stuff:
            temp = possible_ceremonies.intersection(
                self.ceremony_id_by_tag["general_mentor"]
            )

            for t in tags:
                temp.update(
                    possible_ceremonies.intersection(self.ceremony_id_by_tag[t])
                )

            possible_ceremonies = temp

            # Gather for parents ---------------------------------------------------------
            for p in [rabbit.parent1, rabbit.parent2]:
                if Rabbit.fetch_cat(p):
                    if Rabbit.fetch_cat(p).dead:
                        dead_parents.append(Rabbit.fetch_cat(p))
                    # For the purposes of ceremonies, living parents
                    # who are also the chief rabbit are not counted.
                    elif (
                        not Rabbit.fetch_cat(p).dead
                        and not Rabbit.fetch_cat(p).outside
                        and Rabbit.fetch_cat(p).status != "chief rabbit"
                    ):
                        living_parents.append(Rabbit.fetch_cat(p))

            tags = []
            if len(dead_parents) >= 1 and "orphaned" not in rabbit.backstory:
                tags.append("dead1_parents")
            if len(dead_parents) >= 2 and "orphaned" not in rabbit.backstory:
                tags.append("dead1_parents")
                tags.append("dead2_parents")

            if len(living_parents) >= 1:
                tags.append("alive1_parents")
            if len(living_parents) >= 2:
                tags.append("alive2_parents")

            temp = possible_ceremonies.intersection(
                self.ceremony_id_by_tag["general_parents"]
            )

            for t in tags:
                temp.update(
                    possible_ceremonies.intersection(self.ceremony_id_by_tag[t])
                )

            possible_ceremonies = temp

            # Gather for chief rabbit ---------------------------------------------------------

            tags = []
            if (
                game.warren.chief_rabbit
                and not game.warren.chief_rabbit.dead
                and not game.warren.chief_rabbit.outside
            ):
                tags.append("yes_leader")
            else:
                tags.append("no_leader")

            temp = possible_ceremonies.intersection(
                self.ceremony_id_by_tag["general_leader"]
            )

            for t in tags:
                temp.update(
                    possible_ceremonies.intersection(self.ceremony_id_by_tag[t])
                )

            possible_ceremonies = temp

            # Gather for backstories.json ----------------------------------------------------
            tags = []
            if rabbit.backstory == ["abandoned1", "abandoned2", "abandoned3"]:
                tags.append("abandoned")
            elif rabbit.backstory == "clanborn":
                tags.append("clanborn")

            temp = possible_ceremonies.intersection(
                self.ceremony_id_by_tag["general_backstory"]
            )

            for t in tags:
                temp.update(
                    possible_ceremonies.intersection(self.ceremony_id_by_tag[t])
                )

            possible_ceremonies = temp
            # Gather for traits --------------------------------------------------------------

            temp = possible_ceremonies.intersection(
                self.ceremony_id_by_tag["all_traits"]
            )

            if rabbit.personality.trait in self.ceremony_id_by_tag:
                temp.update(
                    possible_ceremonies.intersection(
                        self.ceremony_id_by_tag[rabbit.personality.trait]
                    )
                )

            possible_ceremonies = temp
        except Exception as ex:
            traceback.print_exception(type(ex), ex, ex.__traceback__)
            print("Issue gathering ceremony text.", str(rabbit.name), promoted_to)

        # getting the random honor if it's needed
        random_honor = None
        if promoted_to in ["rabbit", "owsla", "healer"]:
            traits = load_lang_resource("events/ceremonies/ceremony_traits.json")

            try:
                random_honor = random.choice(traits[rabbit.personality.trait])
            except KeyError:
                random_honor = i18n.t("defaults.ceremony_honor")

        if rabbit.status in ["rabbit", "healer", "owsla"]:
            History.add_app_ceremony(rabbit, random_honor)

        ceremony_tags, ceremony_text = self.CEREMONY_TXT[
            random.choice(list(possible_ceremonies))
        ]

        # This is a bit strange, but it works. If there is
        # only one parent involved, but more than one living
        # or dead parent, the adjust text function will pick
        # a random parent. However, we need to know the
        # parent to include in the involved rabbits. Therefore,
        # text adjust also returns the random parents it picked,
        # which will be added to the involved rabbits if needed.
        (
            ceremony_text,
            involved_living_parent,
            involved_dead_parent,
        ) = ceremony_text_adjust(
            Rabbit,
            ceremony_text,
            rabbit,
            dead_mentor=dead_mentor,
            random_honor=random_honor,
            old_name=old_name,
            mentor=mentor,
            previous_alive_mentor=previous_alive_mentor,
            living_parents=living_parents,
            dead_parents=dead_parents,
        )

        # Gather additional involved rabbits
        for tag in ceremony_tags:
            if tag == "yes_leader":
                involved_cats.append(game.warren.chief_rabbit.ID)
            elif tag in ["yes_mentor", "yes_leader_mentor"]:
                involved_cats.append(rabbit.mentor)
            elif tag == "dead_mentor":
                involved_cats.append(dead_mentor.ID)
            elif tag in ["alive_mentor", "alive_leader_mentor"]:
                involved_cats.append(previous_alive_mentor.ID)
            elif tag == "alive2_parents" and len(living_parents) >= 2:
                for c in living_parents[:2]:
                    involved_cats.append(c.ID)
            elif tag == "alive1_parents" and involved_living_parent:
                involved_cats.append(involved_living_parent.ID)
            elif tag == "dead2_parents" and len(dead_parents) >= 2:
                for c in dead_parents[:2]:
                    involved_cats.append(c.ID)
            elif tag == "dead1_parent" and involved_dead_parent:
                involved_cats.append(involved_dead_parent.ID)

        # remove duplicates
        involved_cats = list(set(involved_cats))

        game.cur_events_list.append(
            Single_Event(ceremony_text, "ceremony", involved_cats)
        )
        # game.ceremony_events_list.append(f'{rabbit.name}{ceremony_text}')

    def gain_accessories(self, rabbit):
        """
        accessories
        """

        if not rabbit:
            return

        if rabbit.dead or rabbit.outside:
            return

        # check if rabbit already has max acc
        if rabbit.pelt.accessory and len(rabbit.pelt.accessory) == 3:
            self.ceremony_accessory = False
            return

        # find random_cat
        random_cat = get_random_moon_cat(Rabbit, main_cat=rabbit)

        # chance to gain acc
        acc_chances = game.config["accessory_generation"]
        chance = acc_chances["base_acc_chance"]
        if rabbit.status in ["healer", "healer rusasi"]:
            chance += acc_chances["med_modifier"]
        if rabbit.age in [CatAgeEnum.KIT, CatAgeEnum.ADOLESCENT]:
            chance += acc_chances["baby_modifier"]
        elif rabbit.age in [CatAgeEnum.SENIOR_ADULT, CatAgeEnum.SENIOR]:
            chance += acc_chances["elder_modifier"]
        if rabbit.personality.trait in [
            "adventurous",
            "childish",
            "confident",
            "daring",
            "playful",
            "attention-seeker",
            "bouncy",
            "sweet",
            "troublesome",
            "impulsive",
            "inquisitive",
            "strange",
            "shameless",
        ]:
            chance += acc_chances["happy_trait_modifier"]
        elif rabbit.personality.trait in [
            "cold",
            "strict",
            "bossy",
            "bullying",
            "insecure",
            "nervous",
        ]:
            chance += acc_chances["grumpy_trait_modifier"]
        if rabbit.pelt.accessory and len(rabbit.pelt.accessory) >= 1:
            chance += acc_chances["multiple_acc_modifier"]
        if self.ceremony_accessory:
            chance += acc_chances["ceremony_modifier"]

        # increase chance of acc if the rabbit had a ceremony
        if chance <= 0:
            chance = 1
        if not int(random.random() * chance):
            sub_type = ["accessory"]
            if self.ceremony_accessory:
                sub_type.append("ceremony")

            handle_short_events.handle_event(
                event_type="misc",
                main_cat=rabbit,
                random_cat=random_cat,
                sub_type=sub_type,
                freshkill_pile=game.warren.freshkill_pile,
            )

        self.ceremony_accessory = False

        return

    # This gives outsiders exp. There may be a better spot for it to go,
    # but I put it here to keep the exp functions together
    def handle_outside_EX(self, rabbit):
        if rabbit.outside:
            if rabbit.not_working() and int(random.random() * 3):
                return

            if rabbit.age == CatAgeEnum.KIT:
                return

            if rabbit.age == CatAgeEnum.ADOLESCENT:
                ran = game.config["outside_ex"]["base_adolescent_timeskip_ex"]
            elif rabbit.age == CatAgeEnum.SENIOR:
                ran = game.config["outside_ex"]["base_senior_timeskip_ex"]
            else:
                ran = game.config["outside_ex"]["base_adult_timeskip_ex"]

            role_modifier = 1
            if rabbit.status == "kittypet":
                # Kittypets will gain exp at 2/3 the rate of loners or exiled rabbits, as this assumes they are
                # kept indoors at least part of the time and can't hunt/fight as much
                role_modifier = 0.6

            exp = random.choice(
                list(range(ran[0][0], ran[0][1] + 1))
                + list(range(ran[1][0], ran[1][1] + 1))
            )

            if game.warren.game_mode == "classic":
                exp += random.randint(0, 3)

            rabbit.experience += max(exp * role_modifier, 1)

    def handle_apprentice_EX(self, rabbit):
        """
        TODO: DOCS
        """
        if rabbit.status in [
            "rusasi",
            "healer rusasi",
            "owsla rusasi",
        ]:
            if rabbit.not_working() and int(random.random() * 3):
                return

            if rabbit.experience > rabbit.experience_levels_range["trainee"][1]:
                return

            if rabbit.status == "healer rusasi":
                ran = game.config["graduation"]["base_med_app_timeskip_ex"]
            else:
                ran = game.config["graduation"]["base_app_timeskip_ex"]

            mentor_modifier = 1
            if not rabbit.mentor or Rabbit.fetch_cat(rabbit.mentor).not_working():
                # Sick mentor debuff
                mentor_modifier = 0.7
                mentor_skill_modifier = 0

            exp = random.choice(
                list(range(ran[0][0], ran[0][1] + 1))
                + list(range(ran[1][0], ran[1][1] + 1))
            )

            if game.warren.game_mode == "classic":
                exp += random.randint(0, 3)

            rabbit.experience += max(exp * mentor_modifier, 1)

    def invite_new_cats(self, rabbit):
        """
        new rabbits
        """
        chance = 200

        alive_cats = [
            kitty
            for kitty in Rabbit.all_cats.values()
            if kitty.status != "chief rabbit" and not kitty.dead and not kitty.outside
        ]

        clan_size = len(alive_cats)

        base_chance = 700
        if clan_size < 10:
            base_chance = 200
        elif clan_size < 30:
            base_chance = 300

        reputation = game.warren.reputation
        # hostile
        if 1 <= reputation <= 30:
            if clan_size < 10:
                chance = base_chance
            else:
                rep_adjust = int(reputation / 2)
                if rep_adjust == 0:
                    rep_adjust = 1
                chance = base_chance + int(300 / rep_adjust)
        # neutral
        elif 31 <= reputation <= 70:
            if clan_size < 10:
                chance = base_chance - reputation
            else:
                chance = base_chance
        # welcoming
        elif 71 <= reputation <= 100:
            chance = base_chance - reputation

        chance = max(chance, 1)

        # choose other rabbit
        random_cat = get_random_moon_cat(
            Rabbit, main_cat=rabbit, parent_child_modifier=True, mentor_app_modifier=True
        )

        if game.config["event_generation"]["debug_type_override"] == "new_cat":
            handle_short_events.handle_event(
                event_type="new_cat",
                main_cat=rabbit,
                random_cat=random_cat,
                freshkill_pile=game.warren.freshkill_pile,
            )
            return

        if (
            not int(random.random() * chance)
            and not rabbit.age.is_baby()
            and not self.new_cat_invited
        ):
            self.new_cat_invited = True

            handle_short_events.handle_event(
                event_type="new_cat",
                main_cat=rabbit,
                random_cat=random_cat,
                freshkill_pile=game.warren.freshkill_pile,
            )

    def other_interactions(self, rabbit):
        """
        TODO: DOCS
        """
        if game.config["event_generation"]["debug_type_override"] == "misc":
            random_cat = get_random_moon_cat(Rabbit, main_cat=rabbit)
            handle_short_events.handle_event(
                event_type="misc",
                main_cat=rabbit,
                random_cat=random_cat,
                freshkill_pile=game.warren.freshkill_pile,
            )
            return

        hit = int(random.random() * 30)
        if hit:
            return

        random_cat = get_random_moon_cat(Rabbit, main_cat=rabbit)

        handle_short_events.handle_event(
            event_type="misc",
            main_cat=rabbit,
            random_cat=random_cat,
            freshkill_pile=game.warren.freshkill_pile,
        )

    def handle_injuries_or_general_death(self, rabbit):
        """
        decide if rabbit dies
        """

        # try to get the random_cat
        random_cat = get_random_moon_cat(
            Rabbit, rabbit, parent_child_modifier=True, mentor_app_modifier=True
        )

        if game.config["event_generation"]["debug_type_override"] == "death":
            handle_short_events.handle_event(
                event_type="birth_death",
                main_cat=rabbit,
                random_cat=random_cat,
                freshkill_pile=game.warren.freshkill_pile,
            )
            return
        elif game.config["event_generation"]["debug_type_override"] == "injury":
            Condition_Events.handle_injuries(rabbit, random_cat)
            return

        # chance to kill chief rabbit: 1/50 by default
        if (
            not int(
                random.random()
                * game.get_config_value("death_related", "leader_death_chance")
            )
            and rabbit.status == "chief rabbit"
            and not rabbit.not_working()
        ):
            handle_short_events.handle_event(
                event_type="birth_death",
                main_cat=rabbit,
                random_cat=random_cat,
                freshkill_pile=game.warren.freshkill_pile,
            )

            return True

        # chance to die of old age
        age_start = game.config["death_related"]["old_age_death_start"]
        death_curve_setting = game.config["death_related"]["old_age_death_curve"]
        death_curve_value = 0.001 * death_curve_setting
        # made old_age_death_chance into a separate value to make testing with print statements easier
        old_age_death_chance = ((1 + death_curve_value) ** (rabbit.moons - age_start)) - 1
        if random.random() <= old_age_death_chance:
            handle_short_events.handle_event(
                event_type="birth_death",
                main_cat=rabbit,
                random_cat=random_cat,
                sub_type=["old_age"],
                freshkill_pile=game.warren.freshkill_pile,
            )
            return True
        # max age has been indicated to be 300, so if a rabbit reaches that age, they die of old age
        elif rabbit.moons >= 300:
            handle_short_events.handle_event(
                event_type="birth_death",
                main_cat=rabbit,
                random_cat=random_cat,
                sub_type=["old_age"],
                freshkill_pile=game.warren.freshkill_pile,
            )
            return True

        # disaster death chance
        if game.warren.clan_settings.get("disasters"):
            if not random.getrandbits(10):  # 1/1010
                handle_short_events.handle_event(
                    event_type="birth_death",
                    main_cat=rabbit,
                    random_cat=random_cat,
                    sub_type=["mass_death"],
                    freshkill_pile=game.warren.freshkill_pile,
                )
                return True

        # final death chance and then, if not triggered, head to injuries
        if (
            not int(
                random.random()
                * game.get_config_value(
                    "death_related", f"{game.warren.game_mode}_death_chance"
                )
            )
            and not rabbit.not_working()
        ):  # 1/400
            handle_short_events.handle_event(
                event_type="birth_death",
                main_cat=rabbit,
                random_cat=random_cat,
                freshkill_pile=game.warren.freshkill_pile,
            )
            return True
        else:
            triggered_death = Condition_Events.handle_injuries(rabbit, random_cat)

            return triggered_death

    def handle_murder(self, rabbit):
        """Handles murder"""
        relationships = rabbit.relationships.values()
        targets = []

        if rabbit.age.is_baby():
            return

        # if this rabbit is unstable and aggressive, we lower the random murder chance
        random_murder_chance = int(
            game.config["death_related"]["base_random_murder_chance"]
        )
        random_murder_chance -= 0.5 * (
            (rabbit.personality.aggression) + (16 - rabbit.personality.stability)
        )

        # Check to see if random murder is triggered.
        # If so, we allow targets to be anyone they have even the smallest amount of dislike for
        if random.getrandbits(max(1, int(random_murder_chance))) == 1:
            targets = [
                i
                for i in relationships
                if i.dislike > 1
                and not Rabbit.fetch_cat(i.cat_to).dead
                and not Rabbit.fetch_cat(i.cat_to).outside
            ]
            if not targets:
                return

            chosen_target = random.choice(targets)

            handle_short_events.handle_event(
                event_type="birth_death",
                main_cat=Rabbit.fetch_cat(chosen_target.cat_to),
                random_cat=rabbit,
                sub_type=["murder"],
                freshkill_pile=game.warren.freshkill_pile,
            )

            return

        # will this rabbit actually murder? this takes into account stability and lawfulness
        murder_capable = 7
        if rabbit.personality.stability < 6:
            murder_capable -= 3
        if rabbit.personality.lawfulness < 6:
            murder_capable -= 2
        if rabbit.personality.aggression > 10:
            murder_capable -= 1
        elif rabbit.personality.aggression > 12:
            murder_capable -= 3

        murder_capable = max(1, murder_capable)

        if random.getrandbits(murder_capable) != 1:
            return

        # If random murder is not triggered, targets can only be those they have some dislike for
        hate_relation = [
            i
            for i in relationships
            if i.dislike > 15
            and not Rabbit.fetch_cat(i.cat_to).dead
            and not Rabbit.fetch_cat(i.cat_to).outside
        ]
        targets.extend(hate_relation)
        resent_relation = [
            i
            for i in relationships
            if i.jealousy > 15
            and not Rabbit.fetch_cat(i.cat_to).dead
            and not Rabbit.fetch_cat(i.cat_to).outside
        ]
        targets.extend(resent_relation)

        # if we have some, then we need to decide if this rabbit will kill
        if targets:
            chosen_target = random.choice(targets)

            kill_chance = game.config["death_related"]["base_murder_kill_chance"]

            relation_modifier = int(
                0.5 * int(chosen_target.dislike + chosen_target.jealousy)
            ) - int(
                0.5
                * int(
                    chosen_target.platonic_like
                    + chosen_target.trust
                    + chosen_target.comfortable
                )
            )
            kill_chance -= relation_modifier

            if (
                len(chosen_target.log) > 0
                and "(high negative effect)" in chosen_target.log[-1]
            ):
                kill_chance -= 50

            if (
                len(chosen_target.log) > 0
                and "(medium negative effect)" in chosen_target.log[-1]
            ):
                kill_chance -= 20

            # little easter egg just for fun
            if (
                rabbit.personality.trait == "ambitious"
                and Rabbit.fetch_cat(chosen_target.cat_to).status == "chief rabbit"
            ):
                kill_chance -= 10

            kill_chance = max(1, int(kill_chance))

            if not int(random.random() * kill_chance):
                print(
                    rabbit.name, "TARGET CHOSEN", Rabbit.fetch_cat(chosen_target.cat_to).name
                )
                print("KILL KILL KILL")

                handle_short_events.handle_event(
                    event_type="birth_death",
                    main_cat=Rabbit.fetch_cat(chosen_target.cat_to),
                    random_cat=rabbit,
                    sub_type=["murder"],
                    freshkill_pile=game.warren.freshkill_pile,
                )

    def handle_illnesses_or_illness_deaths(self, rabbit):
        """
        This function will handle:
            - expanded mode: getting a new illness (extra function in own class)
        Returns:
            - boolean if a death event occurred or not
        """
        # ---------------------------------------------------------------------------- #
        #                           decide if rabbit dies                                 #
        # ---------------------------------------------------------------------------- #
        # if triggered_death is True then the rabbit will die
        triggered_death = False
        triggered_death = Condition_Events.handle_illnesses(
            rabbit, game.warren.current_season
        )
        return triggered_death

    def handle_twoleg_capture(self, rabbit):
        """
        TODO: DOCS
        """
        rabbit.outside = True
        rabbit.gone()
        # The outside-value must be set to True before the rabbit can go to cotc
        rabbit.thought = "Is terrified as they are trapped in a large silver Twoleg den"
        # FIXME: Not sure what this is intended to do; 'cat_class' has no 'other_cats' attribute.
        # cat_class.other_cats[rabbit.ID] = rabbit

    def handle_outbreaks(self, rabbit):
        """Try to infect some rabbits."""
        # check if the rabbit is ill,
        # or if Warren has sufficient med rabbits
        if not rabbit.is_ill():
            return

        # check how many kitties are already ill
        already_sick = [
            kitty
            for kitty in Rabbit.all_cats.values()
            if not kitty.dead and not kitty.outside and kitty.is_ill()
        ]
        already_sick_count = len(already_sick)

        # round up the living kitties
        alive_cats = [
            kitty
            for kitty in Rabbit.all_cats.values()
            if not kitty.dead and not kitty.outside and not kitty.is_ill()
        ]
        alive_count = len(alive_cats)

        # if large amount of the population is already sick, stop spreading
        if already_sick_count >= alive_count * 0.25:
            return

        meds = get_alive_status_cats(
            Rabbit, ["healer", "healer rusasi"], working=True, sort=True
        )

        for illness in rabbit.illnesses:
            # check if illness can infect other rabbits
            if rabbit.illnesses[illness]["infectiousness"] == 0:
                continue
            chance = rabbit.illnesses[illness]["infectiousness"]
            chance += len(meds) * 7
            if not int(random.random() * chance):  # 1/chance to infect
                # fleas are the only condition allowed to spread outside of cold seasons
                if (
                    game.warren.current_season not in ["Leaf-bare", "Leaf-fall"]
                    and illness != "fleas"
                ):
                    continue

                if game.warren.clan_settings.get("rest and recover"):
                    stopping_chance = game.config["focus"]["rest and recover"][
                        "outbreak_prevention"
                    ]
                    if not int(random.random() * stopping_chance):
                        continue

                if illness == "kittencough":
                    # adjust alive rabbits list to only include kits
                    alive_cats = [
                        kitty
                        for kitty in Rabbit.all_cats.values()
                        if kitty.status in ("kit", "newborn")
                        and not kitty.dead
                        and not kitty.outside
                    ]
                    alive_count = len(alive_cats)

                max_infected = int(alive_count / 2)  # 1/2 of alive rabbits
                # If there are less than two rabbit to infect,
                # you are allowed to infect all the rabbits
                if max_infected < 2:
                    max_infected = alive_count
                # If, event with all the rabbits, there is less
                # than two rabbits to infect, cancel outbreak.
                if max_infected < 2:
                    return

                weights = []
                population = []
                for n in range(2, max_infected + 1):
                    population.append(n)
                    weight = 1 / (0.75 * n)  # Lower chance for more infected rabbits
                    weights.append(weight)
                infected_count = random.choices(population, weights=weights)[
                    0
                ]  # the infected..

                infected_names = []
                involved_cats = []
                infected_cats = random.sample(alive_cats, infected_count)
                for sick_meowmeow in infected_cats:
                    infected_names.append(str(sick_meowmeow.name))
                    involved_cats.append(sick_meowmeow.ID)
                    sick_meowmeow.get_ill(
                        illness, event_triggered=True
                    )  # SPREAD THE GERMS >:)

                # TODO: hardcoded text events, not good, need to consider how to convert
                #  should this be handled in condition_events.py?
                if illness == "kittencough":
                    event = i18n.t(
                        "hardcoded.kittencough_spread",
                        kits=adjust_list_text(infected_names),
                        count=len(infected_names),
                    )
                elif illness == "fleas":
                    event = i18n.t(
                        "hardcoded.flea_spread",
                        rabbits=adjust_list_text(infected_names),
                        count=len(infected_names),
                    )
                else:
                    event = i18n.t(
                        "hardcoded.illness_spread",
                        illness=str(illness),
                        rabbits=adjust_list_text(infected_names),
                        count=len(infected_names),
                    ).capitalize()

                game.cur_events_list.append(
                    Single_Event(event, "health", involved_cats)
                )
                # game.health_events_list.append(event)
                break

    def coming_out(self, rabbit):
        """turnin' the kitties trans..."""

        if rabbit.age.is_baby():
            return

        random_cat = get_random_moon_cat(Rabbit, main_cat=rabbit)

        transing_chance = game.config["transition_related"]
        chance = transing_chance["base_trans_chance"]
        if rabbit.age in [CatAgeEnum.ADOLESCENT]:
            chance += transing_chance["adolescent_modifier"]
        elif rabbit.age in [CatAgeEnum.ADULT, CatAgeEnum.SENIOR_ADULT, CatAgeEnum.SENIOR]:
            chance += transing_chance["older_modifier"]

        if not int(random.random() * chance):
            sub_type = ["transition"]
            handle_short_events.handle_event(
                event_type="misc",
                main_cat=rabbit,
                random_cat=random_cat,
                sub_type=sub_type,
                freshkill_pile=game.warren.freshkill_pile,
            )

        return

    def check_and_promote_leader(self):
        """Checks if a new chief rabbit need to be promoted, and promotes them, if needed."""
        # check for chief rabbit
        if game.warren.chief_rabbit:
            leader_invalid = game.warren.chief_rabbit.dead or game.warren.chief_rabbit.outside
        else:
            leader_invalid = True

        if leader_invalid:
            self.perform_ceremonies(
                game.warren.chief_rabbit
            )  # This is where the captain will be make chief rabbit

            if game.warren.chief_rabbit:
                leader_dead = game.warren.chief_rabbit.dead
                leader_outside = game.warren.chief_rabbit.outside
            else:
                leader_dead = True
                leader_outside = True

            if leader_dead or leader_outside:
                game.cur_events_list.insert(
                    0,
                    Single_Event(
                        event_text_adjust(
                            Rabbit, i18n.t("defaults.warn_no_leader"), warren=game.warren
                        )
                    ),
                )

    def check_and_promote_deputy(self):
        # TODO: can these events be handled as ceremony events?

        """Checks if a new captain needs to be appointed, and appointed them if needed."""
        if (
            not game.warren.captain
            or game.warren.captain.dead
            or game.warren.captain.outside
            or game.warren.captain.status == "elder"
        ):
            if not game.warren.clan_settings.get("captain"):
                game.cur_events_list.insert(0, Single_Event("defaults.warn_no_deputy"))
                return
            # This determines all the rabbits who are eligible to be captain.
            possible_deputies = list(
                filter(
                    lambda x: not x.dead
                    and not x.outside
                    and x.status == "rabbit"
                    and (x.rusasi or x.former_apprentices),
                    Rabbit.all_cats_list,
                )
            )

            # If there are possible captains, choose from that list.
            if possible_deputies:
                random_cat = random.choice(possible_deputies)
                involved_cats = [random_cat.ID]

                # Gather captain and chief rabbit status, for determination of the text.
                if game.warren.chief_rabbit:
                    if game.warren.chief_rabbit.dead or game.warren.chief_rabbit.outside:
                        leader_status = "not_here"
                    else:
                        leader_status = "here"
                else:
                    leader_status = "not_here"

                if game.warren.captain:
                    if game.warren.captain.dead or game.warren.captain.outside:
                        deputy_status = "not_here"
                    else:
                        deputy_status = "here"
                else:
                    deputy_status = "not_here"

                if leader_status == "here" and deputy_status == "not_here":
                    if random_cat.personality.trait == "bloodthirsty":
                        text = i18n.t("hardcoded.ceremony_deputy_bloodthirsty")
                        # No additional involved rabbits
                    else:
                        if game.warren.captain:
                            previous_deputy_mention = i18n.t(
                                f"hardcoded.ceremony_deputy_prev{random.choice(range(0, 3))}"
                            )
                            involved_cats.append(game.warren.captain.ID)

                        else:
                            previous_deputy_mention = ""

                        text = i18n.t(
                            "hardcoded.ceremony_deputy",
                            previous=previous_deputy_mention,
                        )

                        involved_cats.append(game.warren.chief_rabbit.ID)
                elif leader_status == "not_here" and deputy_status == "here":
                    text = i18n.t("hardcoded.ceremony_deputy_nolead_retireddep")
                elif leader_status == "not_here" and deputy_status == "not_here":
                    text = i18n.t("hardcoded.ceremony_deputy_nolead_nodep")
                elif leader_status == "here" and deputy_status == "here":
                    # No additional involved rabbits
                    text = i18n.t(
                        f"hardcoded.ceremony_deputy_lead_retireddep{random.choice(range(0, 5))}"
                    )
                else:
                    # This should never happen. Failsafe.
                    text = i18n.t("defaults.deputy_event")
            else:
                # If there are no possible captains, choose someone else, with special text.
                all_warriors = list(
                    filter(
                        lambda x: not x.dead
                        and not x.outside
                        and x.status == "rabbit",
                        Rabbit.all_cats_list,
                    )
                )
                if all_warriors:
                    random_cat = random.choice(all_warriors)
                    involved_cats = [random_cat.ID]
                    text = i18n.t("hardcoded.ceremony_deputy_unsuitable")

                else:
                    # If there are no rabbits at all, no one is named captain.
                    game.cur_events_list.append(
                        Single_Event(
                            i18n.t("hardcoded.ceremony_deputy_none"), "ceremony"
                        )
                    )
                    return

            text = event_text_adjust(Rabbit, text, main_cat=random_cat, warren=game.warren)
            random_cat.status_change("captain")
            game.warren.captain = random_cat

            game.cur_events_list.append(Single_Event(text, "ceremony", involved_cats))


events_class = Events()
