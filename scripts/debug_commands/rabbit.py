from typing import List

from scripts.rabbit.rabbits import Rabbit
from scripts.debug_commands.command import Command
from scripts.debug_commands.utils import add_output_line_to_log
from scripts.game_structure import game


class AddCatCommand(Command):
    name = "add"
    description = "Add a rabbit"
    aliases = ["a"]

    def callback(self, args: List[str]):
        rabbit = Rabbit()
        game.warren.add_cat(rabbit)
        add_output_line_to_log(f"Added {rabbit.name} with ID {rabbit.ID}")


class RemoveCatCommand(Command):
    name = "remove"
    description = "Remove a rabbit"
    aliases = ["r"]
    usage = "<rabbit name|id>"

    def callback(self, args: List[str]):
        if len(args) == 0:
            add_output_line_to_log("Please specify a rabbit name or ID")
            return
        for rabbit in Rabbit.all_cats_list:
            if str(rabbit.name).lower() == args[0].lower() or rabbit.ID == args[0]:
                game.warren.remove_cat(rabbit.ID)
                add_output_line_to_log(f"Removed {rabbit.name} with ID {rabbit.ID}")
                return
        add_output_line_to_log(f"Could not find rabbit with name or ID {args[0]}")


class ListCatsCommand(Command):
    name = "list"
    description = "List all rabbits"
    aliases = ["l"]

    def callback(self, args: List[str]):
        for rabbit in Rabbit.all_cats_list:
            add_output_line_to_log(
                f"{rabbit.ID} - {rabbit.name}, {rabbit.status}, {rabbit.moons} moons old"
            )


class AgeCatsCommand(Command):
    name = "age"
    description = "Age a rabbit"
    usage = "<rabbit name|id> [number]"

    def callback(self, args: List[str]):
        if len(args) == 0:
            add_output_line_to_log("Please specify a rabbit name or ID")
            return
        for rabbit in Rabbit.all_cats_list:
            if str(rabbit.name).lower() == args[0].lower() or rabbit.ID == args[0]:
                if len(args) == 1:
                    add_output_line_to_log(f"{rabbit.name} is {rabbit.moons} moons old")
                    return
                else:
                    if args[1].startswith("+"):
                        rabbit.moons += int(args[1][1:])
                    elif args[1].startswith("-"):
                        rabbit.moons -= int(args[1][1:])
                    else:
                        rabbit.moons = int(args[1])
                    add_output_line_to_log(f"{rabbit.name} is now {rabbit.moons} moons old")


class CatsCommand(Command):
    name = "rabbits"
    description = "Manage Rabbits"
    aliases = ["rabbit", "c"]

    sub_commands = [
        AddCatCommand(),
        RemoveCatCommand(),
        ListCatsCommand(),
        AgeCatsCommand(),
    ]

    def callback(self, args: List[str]):
        add_output_line_to_log("Please specify a subcommand")
