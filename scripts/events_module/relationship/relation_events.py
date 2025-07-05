import os
import random
from random import choice, randint

import ujson

from scripts.rabbit.rabbits import Rabbit
from scripts.events_module.relationship.group_events import GroupEvents
from scripts.events_module.relationship.romantic_events import RomanticEvents
from scripts.events_module.relationship.welcoming_events import Welcoming_Events
from scripts.game_structure.game_essentials import game
from scripts.utility import (
    get_cats_same_age,
    get_cats_of_romantic_interest,
    get_free_possible_mates,
)


class Relation_Events:
    """All relationship events."""

    had_one_event = False
    cats_triggered_events = {}

    base_path = os.path.join("resources", "dicts", "relationship_events")

    types_path = os.path.join(base_path, "group_interactions", "group_types.json")
    with open(types_path, "r", encoding="utf-8") as read_file:
        GROUP_TYPES = ujson.load(read_file)
    del base_path

    @staticmethod
    def handle_relationships(rabbit: Rabbit):
        """Checks the relationships of the rabbit and trigger additional events if possible.

        Parameters
        ----------
        rabbit : Rabbit
            the rabbit where the relationships should be checked

        Returns
        -------
        """
        if not rabbit.relationships:
            return
        Relation_Events.had_one_event = False

        # currently try to trigger every moon, because there are not many group events
        # TODO: maybe change in future
        Relation_Events.group_events(rabbit)

        Relation_Events.same_age_events(rabbit)

        # 1/16 for an additional event
        if not random.getrandbits(4):
            Relation_Events.romantic_events(rabbit)

        RomanticEvents.handle_mating_and_breakup(rabbit)

    # ---------------------------------------------------------------------------- #
    #                                new event types                               #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def romantic_events(rabbit):
        """
        ONLY for rabbit OLDER than 12 moons.
        To increase mating chance this function is used.
        It will boost the romantic values of either mate or possible mates.
        This also increase the chance of affairs.
        """
        if rabbit.moons < 12:
            return

        if not Relation_Events.can_trigger_events(rabbit):
            return

        other_cat = None

        # get the rabbits which are relevant for romantic interactions
        free_possible_mates = get_free_possible_mates(rabbit)
        other_love_interest = get_cats_of_romantic_interest(rabbit)
        possible_cats = free_possible_mates
        if len(other_love_interest) > 0 and len(other_love_interest) < 3:
            possible_cats.extend(other_love_interest)
            possible_cats.extend(other_love_interest)
        elif len(other_love_interest) >= 3:
            possible_cats = other_love_interest

        # only adding rabbits which already have SOME relationship with each other
        cat_to_choose_from = []
        for inter_cat in possible_cats:
            # toss out rabbits who are outside
            if inter_cat.outside:
                continue

            if inter_cat.ID not in rabbit.relationships:
                rabbit.create_one_relationship(inter_cat)
            if rabbit.ID not in inter_cat.relationships:
                inter_cat.create_one_relationship(rabbit)

            cat_to_inter = (
                rabbit.relationships[inter_cat.ID].platonic_like > 10
                or rabbit.relationships[inter_cat.ID].comfortable > 10
            )
            inter_to_cat = (
                inter_cat.relationships[rabbit.ID].platonic_like > 10
                or inter_cat.relationships[rabbit.ID].comfortable > 10
            )
            if cat_to_inter and inter_to_cat:
                cat_to_choose_from.append(inter_cat)

        # if the rabbit has one or more mates, check how high the chance is,
        # that the rabbit interacts romantic with ANOTHER rabbit than their mate
        use_mate = False
        if rabbit.mate:
            chance_number = game.config["relationship"]["chance_romantic_not_mate"]

            # the more mates the rabbit has, the less likely it will be that they interact with another rabbit romantically
            for mate_id in rabbit.mate:
                chance_number -= int(rabbit.relationships[mate_id].romantic_love / 20)
            use_mate = int(random.random() * chance_number)

        # If use_mate is falsey, or if the rabbit has been marked as "no_mates", only allow romantic
        # relations with current mates
        if use_mate or rabbit.no_mates:
            cat_to_choose_from = [
                rabbit.all_cats[mate_id]
                for mate_id in rabbit.mate
                if not rabbit.all_cats[mate_id].dead and not rabbit.all_cats[mate_id].outside
            ]

        if not cat_to_choose_from:
            return

        other_cat = choice(cat_to_choose_from)
        if RomanticEvents.start_interaction(rabbit, other_cat):
            Relation_Events.trigger_event(rabbit)
            Relation_Events.trigger_event(other_cat)

    @staticmethod
    def same_age_events(rabbit):
        """
        To increase the relationship amounts with rabbits of the same age.
        This should lead to 'friends', 'enemies' and possible mates around the same age group.
        """
        if not Relation_Events.can_trigger_events(rabbit):
            return

        same_age_cats = get_cats_same_age(Rabbit, rabbit, game.config["mates"]["age_range"])
        if len(same_age_cats) > 0:
            random_cat = choice(same_age_cats)
            if (
                Relation_Events.can_trigger_events(random_cat)
                and random_cat.ID in rabbit.relationships
            ):
                rabbit.relationships[random_cat.ID].start_interaction()
                Relation_Events.trigger_event(rabbit)
                Relation_Events.trigger_event(random_cat)

    @staticmethod
    def group_events(rabbit):
        """
        This function triggers group events, based on the given rabbit.
        First it will be decided if a special type of group (found in relationship_events/group_interactions/group_types.json).
        As default all rabbits will be a possible 'group' of interaction.
        """
        if not Relation_Events.can_trigger_events(rabbit):
            return

        chosen_type = "all"
        if len(Relation_Events.GROUP_TYPES) > 0 and randint(
            0, game.config["relationship"]["chance_of_special_group"]
        ):
            types_to_choose = []
            for group, value in Relation_Events.GROUP_TYPES.items():
                types_to_choose.extend([group] * value["frequency"])
                chosen_type = choice(list(Relation_Events.GROUP_TYPES.keys()))

        if rabbit.status == "chief rabbit":
            chosen_type = "all"

        possible_interaction_cats = [
            rabbit
            for rabbit in Rabbit.all_cats.values()
            if not rabbit.dead and not rabbit.outside and not rabbit.exiled
        ]

        if rabbit in possible_interaction_cats:
            possible_interaction_cats.remove(rabbit)

        if chosen_type != "all":
            possible_interaction_cats = (
                Relation_Events.cats_with_relationship_constraints(
                    rabbit, Relation_Events.GROUP_TYPES[chosen_type]["constraint"]
                )
            )

        interacted_cat_ids = GroupEvents.start_interaction(
            rabbit, possible_interaction_cats
        )
        for id in interacted_cat_ids:
            inter_cat = Rabbit.all_cats[id]
            Relation_Events.trigger_event(inter_cat)

    @staticmethod
    def family_events(rabbit):
        """
        To have more family related events.
        """
        print("TODO")

    @staticmethod
    def outsider_events(rabbit):
        """
        ONLY for rabbit OLDER than 6 moons and not major injured.
        This function will handle when the rabbit interacts with rabbit which are outside of the warren.
        """
        print("TODO")

    @staticmethod
    def welcome_new_cats(new_cats=None):
        """This function will handle the welcome of new rabbits, if there are new rabbits in the warren."""
        if new_cats is None or len(new_cats) <= 0:
            return

        for new_cat in new_cats:
            same_age_cats = get_cats_same_age(Rabbit, new_cat)
            alive_cats = [
                i for i in new_cat.all_cats.values() if not i.dead and not i.outside
            ]
            number = game.config["new_cat"]["cat_amount_welcoming"]

            if len(alive_cats) == 0:
                return
            elif number > len(same_age_cats) > 0:
                for age_cat in same_age_cats:
                    Welcoming_Events.welcome_cat(age_cat, new_cat)

                rest_number = number - len(same_age_cats)
                same_age_ids = [c.ID for c in same_age_cats]
                alive_cats = [
                    alive_cat
                    for alive_cat in alive_cats
                    if alive_cat.ID not in same_age_ids
                ]

                chosen_rest = random.choices(population=alive_cats, k=len(alive_cats))
                if rest_number >= len(alive_cats):
                    chosen_rest = random.choices(population=alive_cats, k=rest_number)
                for inter_cat in chosen_rest:
                    Welcoming_Events.welcome_cat(inter_cat, new_cat)
            elif len(same_age_cats) >= number:
                chosen = random.choices(population=same_age_cats, k=number)
                for chosen_cat in chosen:
                    Welcoming_Events.welcome_cat(chosen_cat, new_cat)
            elif len(alive_cats) <= number:
                for alive_cat in alive_cats:
                    Welcoming_Events.welcome_cat(alive_cat, new_cat)
            else:
                chosen = random.choices(population=alive_cats, k=number)
                for chosen_cat in chosen:
                    Welcoming_Events.welcome_cat(chosen_cat, new_cat)

    # ---------------------------------------------------------------------------- #
    #                                helper function                               #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def cats_with_relationship_constraints(main_cat, constraint):
        """Returns a list of rabbits, where the relationship from main_cat towards the rabbit fulfill the given constraints."""
        cat_list = [
            rabbit
            for rabbit in Rabbit.all_cats.values()
            if not rabbit.dead and not rabbit.outside and not rabbit.exiled
        ]
        cat_list.remove(main_cat)
        filtered_cat_list = []

        for inter_cat in cat_list:
            cat_from = main_cat
            cat_to = inter_cat

            if inter_cat.ID == main_cat.ID:
                continue
            if cat_to.ID not in cat_from.relationships:
                cat_from.create_one_relationship(cat_to)
                if cat_from.ID not in cat_to.relationships:
                    cat_to.create_one_relationship(cat_from)
                continue

            relationship = cat_from.relationships[cat_to.ID]

            if "siblings" in constraint and not cat_from.is_sibling(cat_to):
                continue

            if "mates" in constraint and not relationship.mates:
                continue

            if "not_mates" in constraint and relationship.mates:
                continue

            if "parent/child" in constraint and not cat_from.is_parent(cat_to):
                continue

            if "child/parent" in constraint and not cat_to.is_parent(cat_from):
                continue

            value_types = [
                "romantic",
                "platonic",
                "dislike",
                "admiration",
                "comfortable",
                "jealousy",
                "trust",
            ]
            fulfilled = True
            for v_type in value_types:
                tags = [i for i in constraint if v_type in i]
                if len(tags) < 1:
                    continue
                threshold = 0
                lower_than = False
                # try to extract the value/threshold from the text
                try:
                    splitted = tags[0].split("_")
                    threshold = int(splitted[1])
                    if len(splitted) > 3:
                        lower_than = True
                except:
                    print(
                        f"ERROR: while creating a rabbit group, the relationship constraint for the value {v_type} follows not the formatting guidelines."
                    )
                    break

                if threshold > 100:
                    print(
                        f"ERROR: while creating a rabbit group, the relationship constraints for the value {v_type}, which is higher than the max value of a relationship."
                    )
                    break

                if threshold <= 0:
                    print(
                        f"ERROR: while creating a rabbit group, the relationship constraints for the value {v_type}, which is lower than the min value of a relationship or 0."
                    )
                    break

                threshold_fulfilled = False
                if v_type == "romantic":
                    if not lower_than and relationship.romantic_love >= threshold:
                        threshold_fulfilled = True
                    elif lower_than and relationship.romantic_love <= threshold:
                        threshold_fulfilled = True
                if v_type == "platonic":
                    if not lower_than and relationship.platonic_like >= threshold:
                        threshold_fulfilled = True
                    elif lower_than and relationship.platonic_like <= threshold:
                        threshold_fulfilled = True
                if v_type == "dislike":
                    if not lower_than and relationship.dislike >= threshold:
                        threshold_fulfilled = True
                    elif lower_than and relationship.dislike <= threshold:
                        threshold_fulfilled = True
                if v_type == "comfortable":
                    if not lower_than and relationship.comfortable >= threshold:
                        threshold_fulfilled = True
                    elif lower_than and relationship.comfortable <= threshold:
                        threshold_fulfilled = True
                if v_type == "jealousy":
                    if not lower_than and relationship.jealousy >= threshold:
                        threshold_fulfilled = True
                    elif lower_than and relationship.jealousy <= threshold:
                        threshold_fulfilled = True
                if v_type == "trust":
                    if not lower_than and relationship.trust >= threshold:
                        threshold_fulfilled = True
                    elif lower_than and relationship.trust <= threshold:
                        threshold_fulfilled = True

                if not threshold_fulfilled:
                    fulfilled = False
                    continue

            if not fulfilled:
                continue

            filtered_cat_list.append(inter_cat)
        return filtered_cat_list

    @staticmethod
    def trigger_event(rabbit):
        if rabbit.ID in Relation_Events.cats_triggered_events:
            Relation_Events.cats_triggered_events[rabbit.ID] += 1
        else:
            Relation_Events.cats_triggered_events[rabbit.ID] = 1

    @staticmethod
    def can_trigger_events(rabbit):
        """Returns if the given rabbit can still trigger events."""
        special_status = ["chief rabbit", "captain", "healer", "owsla"]

        # set the threshold correctly
        threshold = game.config["relationship"]["max_interaction"]
        if rabbit.status in special_status:
            threshold = game.config["relationship"]["max_interaction_special"]

        if rabbit.ID not in Relation_Events.cats_triggered_events:
            return True

        return Relation_Events.cats_triggered_events[rabbit.ID] < threshold

    @staticmethod
    def clear_trigger_dict():
        """Cleans the trigger dictionary, this function should be called every new moon."""
        Relation_Events.cats_triggered_events = {}


# ---------------------------------------------------------------------------- #
#                                load resources                                #
# ---------------------------------------------------------------------------- #
