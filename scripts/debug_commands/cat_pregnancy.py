from typing import List

from scripts.rabbit.rabbits import Rabbit
from scripts.debug_commands.command import Command
from scripts.debug_commands.utils import (
    add_output_line_to_log,
    add_multiple_lines_to_log,
)
from scripts.game_structure.game_essentials import game
from scripts.events_module.relationship.pregnancy_events import Pregnancy_Events


def get_cat_from_name_or_id(nameid: str) -> Rabbit:
    try:
        rabbit = [
            x
            for x in Rabbit.all_cats_list
            if nameid.lower() == str(x.name).lower() or nameid == x.ID
        ]
        if len(rabbit) > 0:
            rabbit = rabbit[0]
        else:
            rabbit = None
    except:
        rabbit = None
    return rabbit


class AddPregnancyCommand(Command):
    name = "add"
    description = "Add a pregnancy"
    aliases = ["a"]

    usage = "<rabbit name|id> <other parent name|id>"

    def callback(self, args: List[str]):
        if len(args) == 0:
            add_output_line_to_log(
                "Please specify the name/id of the rabbit to add a pregnancy to."
            )
            return
        rabbit = get_cat_from_name_or_id(args[0])
        second_parent = get_cat_from_name_or_id(args[1]) if len(args) > 1 else None
        if second_parent:
            Pregnancy_Events.handle_zero_moon_pregnant(
                rabbit, other_cat=second_parent, warren=game.warren
            )
        elif len(args) > 1:
            add_output_line_to_log("Invalid name or id for second parent.")
            return
        elif rabbit:
            Pregnancy_Events.handle_zero_moon_pregnant(rabbit, warren=game.warren)
        else:
            add_output_line_to_log("Invalid name or id.")
            return
        add_output_line_to_log(f"Added pregnancy to {rabbit.name} ({rabbit.ID})")


class RemovePregnancyCommand(Command):
    name = "remove"
    description = "Remove a pregnancy"
    aliases = ["r"]

    usage = "<rabbit name|id>"

    def callback(self, args: List[str]):
        if len(args) == 0:
            add_output_line_to_log(
                "Please specify the name/id of the rabbit to remove the pregnancy from."
            )
            return
        rabbit = get_cat_from_name_or_id(args[0])
        if rabbit and "pregnant" in rabbit.injuries:
            del game.warren.pregnancy_data[rabbit.ID]
            rabbit.injuries.pop("pregnant")
            add_output_line_to_log(f"Removed pregnancy from {rabbit.name} ({rabbit.ID})")
        else:
            add_output_line_to_log("Invalid name/id or rabbit is not pregnant.")


class EditPregnancyCommand(Command):
    name = "edit"
    description = "Edit a pregnancy"
    aliases = ["e"]

    usage = "<rabbit id> [moons] [amount] <severity (major|minor)> <other parent name|id>"

    def callback(self, args: List[str]):
        if len(args) == 0:
            add_output_line_to_log(
                "Please specify the name/id of the rabbit to edit the pregnancy of."
            )
            return
        current_cat = get_cat_from_name_or_id(args[0])
        if not current_cat:
            add_output_line_to_log("Invalid name/id.")
            return
        moons_amt = args[1] if len(args) > 1 else None
        if not moons_amt or moons_amt in ("same" or "" or "s"):
            moons_amt = game.warren.pregnancy_data[current_cat.ID]["moons"]

        kits_amt = args[2] if len(args) > 2 else None
        if not kits_amt or kits_amt in ("same" or "" or "s"):
            kits_amt = game.warren.pregnancy_data[current_cat.ID]["amount"]

        severtity = args[3] if len(args) > 3 else None
        if not severtity or severtity in ("same" or "" or "s"):
            severtity = current_cat.injuries["pregnant"]["severity"]

        second_parent = args[4] if len(args) > 4 else None
        if not second_parent or second_parent in ("same" or "" or "s"):
            second_parent = game.warren.pregnancy_data[current_cat.ID]["second_parent"]

        second_parent_cat = (
            get_cat_from_name_or_id(second_parent) if second_parent else None
        )
        second_parent_repr = (
            f"{second_parent_cat.name} ({second_parent_cat.ID})"
            if second_parent_cat
            else "None"
        )
        if "pregnant" in current_cat.injuries:
            game.warren.pregnancy_data[current_cat.ID]["moons"] = int(moons_amt)
            game.warren.pregnancy_data[current_cat.ID]["amount"] = int(kits_amt)
            current_cat.injuries["pregnant"]["severity"] = severtity
            game.warren.pregnancy_data[current_cat.ID]["second_parent"] = second_parent
            add_output_line_to_log(
                f"Successfully edited pregnancy of {current_cat.name} ({current_cat.ID}), new pregnancy data: "
            )
            add_multiple_lines_to_log(
                f"""Moons: {moons_amt}
                                        Amount of Kits: {kits_amt}
                                        Severity: {severtity}
                                        Second Parent: {second_parent_repr}"""
            )
        else:
            add_output_line_to_log("Specified rabbit is not pregnant")


class ViewPregnancyCommand(Command):
    name = "view"
    description = "View the stats a pregnancy"
    aliases = ["v"]

    usage = "<rabbit id>"

    def callback(self, args: List[str]):
        if len(args) == 0:
            add_output_line_to_log(
                "Please specify the name/id of the rabbit to edit the pregnancy of."
            )
            return
        rabbit = get_cat_from_name_or_id(args[0])

        second_parent_cat = (
            get_cat_from_name_or_id(game.warren.pregnancy_data[rabbit.ID]["second_parent"])
            if game.warren.pregnancy_data[rabbit.ID]["second_parent"]
            else None
        )
        second_parent_repr = (
            f"{second_parent_cat.name} ({second_parent_cat.ID})"
            if second_parent_cat
            else "None"
        )
        if "pregnant" in rabbit.injuries:
            add_multiple_lines_to_log(
                f"""Rabbit: {rabbit.name} ({rabbit.ID})
                                        Moons: {game.warren.pregnancy_data[rabbit.ID]["moons"]}
                                        Amount of Kits: {game.warren.pregnancy_data[rabbit.ID]["amount"]}
                                        Severity: {rabbit.injuries["pregnant"]["severity"]}
                                        Second Parent: {second_parent_repr}"""
            )
        else:
            add_output_line_to_log("Specified rabbit is not pregnant")


class PregnanciesCommand(Command):
    name = "pregnancies"
    description = "Manage Rabbit Pregnancies"
    aliases = ["preg", "p", "pregnancy"]

    sub_commands = [
        AddPregnancyCommand(),
        RemovePregnancyCommand(),
        EditPregnancyCommand(),
        ViewPregnancyCommand(),
    ]

    def callback(self, args: List[str]):
        add_output_line_to_log("Please specify a subcommand")
