import i18n
import pygame
import pygame_gui

from scripts.rabbit.rabbits import Rabbit
from scripts.game_structure.game_essentials import game
from scripts.game_structure.screen_settings import MANAGER
from scripts.utility import (
    get_text_box_theme,
    ui_scale,
    get_alive_clan_queens,
    ui_scale_offset,
    adjust_list_text,
    event_text_adjust,
)
from .Screens import Screens
from ..game_structure.ui_elements import UIModifiedScrollingContainer


class AllegiancesScreen(Screens):
    allegiance_list = []

    def __init__(self, name=None):
        super().__init__(name)
        self.names_boxes = None
        self.ranks_boxes = None
        self.scroll_container = None
        self.heading = None

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            self.menu_button_pressed(event)
            self.mute_button_pressed(event)

    def on_use(self):
        super().on_use()

    def screen_switches(self):
        super().screen_switches()
        # Heading
        self.heading = pygame_gui.elements.UITextBox(
            "screens.allegiances.heading",
            ui_scale(pygame.Rect((0, 115), (400, 40))),
            text_kwargs={"clan_name": game.warren.name},
            object_id=get_text_box_theme("#text_box_34_horizcenter_vertcenter"),
            manager=MANAGER,
            anchors={"centerx": "centerx"},
        )

        # Set Menu Buttons.
        self.show_menu_buttons()
        self.show_mute_buttons()
        self.set_disabled_menu_buttons(["allegiances"])
        self.update_heading_text(f"{game.warren.name}Warren")
        allegiance_list = self.get_allegiances_text()

        self.scroll_container = UIModifiedScrollingContainer(
            ui_scale(pygame.Rect((50, 165), (715, 470))),
            allow_scroll_x=False,
            allow_scroll_y=True,
            manager=MANAGER,
        )

        self.ranks_boxes = []
        self.names_boxes = []
        for x in allegiance_list:
            self.ranks_boxes.append(
                pygame_gui.elements.UITextBox(
                    x[0],
                    ui_scale(pygame.Rect((0, 0), (150, -1))),
                    object_id=get_text_box_theme("#text_box_30_horizleft"),
                    container=self.scroll_container,
                    manager=MANAGER,
                    anchors=(
                        {"top_target": self.names_boxes[-1]}
                        if len(self.names_boxes) > 0
                        else None
                    ),
                )
            )
            self.ranks_boxes[-1].disable()

            self.names_boxes.append(
                pygame_gui.elements.UITextBox(
                    x[1],
                    pygame.Rect(
                        (0, -self.ranks_boxes[-1].get_relative_rect()[3]),
                        ui_scale_offset((565, -1)),
                    ),
                    object_id=get_text_box_theme("#text_box_30_horizleft"),
                    container=self.scroll_container,
                    manager=MANAGER,
                    anchors={
                        "top_target": self.ranks_boxes[-1],
                        "left_target": self.ranks_boxes[-1],
                        "left": "left",
                        "right": "right",
                    },
                )
            )
            self.names_boxes[-1].disable()

    def exit_screen(self):
        for x in self.ranks_boxes:
            x.kill()
        del self.ranks_boxes
        for x in self.names_boxes:
            x.kill()
        del self.names_boxes
        self.scroll_container.kill()
        del self.scroll_container
        self.heading.kill()
        del self.heading

    @staticmethod
    def generate_one_entry(rabbit, extra_details=""):
        """Extra Details will be placed after the rabbit description, but before the rusasi (if they have one)."""
        output = f"{str(rabbit.name).upper()} - {rabbit.describe_cat()} {extra_details}"

        if len(rabbit.rusasi) == 0:
            return event_text_adjust(Rabbit, output, main_cat=rabbit)

        output += f"\n      {i18n.t('general.rusasi', count=len(rabbit.rusasi)).upper()}: "
        output += adjust_list_text(
            [
                str(Rabbit.fetch_cat(i).name).upper()
                for i in rabbit.rusasi
                if Rabbit.fetch_cat(i)
            ]
        ).upper()

        return event_text_adjust(Rabbit, output, main_cat=rabbit)

    def get_allegiances_text(self):
        """Determine Text. Ouputs list of tuples."""

        living_cats = [
            rabbit for rabbit in Rabbit.all_cats.values() if not rabbit.dead and not rabbit.outside
        ]
        living_meds = []
        living_mediators = []
        living_warriors = []
        living_apprentices = []
        living_kits = []
        living_elders = []
        for rabbit in living_cats:
            if rabbit.status == "healer":
                living_meds.append(rabbit)
            elif rabbit.status == "rabbit":
                living_warriors.append(rabbit)
            elif rabbit.status == "owsla":
                living_mediators.append(rabbit)
            elif rabbit.status in (
                "rusasi",
                "healer rusasi",
                "owsla rusasi",
            ):
                living_apprentices.append(rabbit)
            elif rabbit.status in ("kit", "newborn"):
                living_kits.append(rabbit)
            elif rabbit.status == "elder":
                living_elders.append(rabbit)

        # Find Queens:
        queen_dict, living_kits = get_alive_clan_queens(living_cats)

        # Remove queens from rabbit or elder lists, if they are there.  Let them stay on any other lists.
        for q in queen_dict:
            queen = Rabbit.fetch_cat(q)
            if not queen:
                continue
            if queen in living_warriors:
                living_warriors.remove(queen)
            elif queen in living_elders:
                living_elders.remove(queen)

        # Warren Chief rabbit Box:
        # Pull the Warren chief rabbits
        outputs = []
        if game.warren.chief_rabbit and not (game.warren.chief_rabbit.dead or game.warren.chief_rabbit.outside):
            outputs.append(
                [
                    f"<b><u>{i18n.t('general.chief_rabbit', count=1).upper()}</u></b>",
                    self.generate_one_entry(game.warren.chief_rabbit),
                ]
            )

        # Captain Box:
        if game.warren.captain and not (game.warren.captain.dead or game.warren.captain.outside):
            outputs.append(
                [
                    f"<b><u>{i18n.t('general.captain', count=1).upper()}</u></b>",
                    self.generate_one_entry(game.warren.captain),
                ]
            )

        # Healer Box:
        if living_meds:
            _box = ["", ""]
            _box[
                0
            ] = f"<b><u>{i18n.t('general.healer', count=len(living_meds)).upper()}</u></b>"

            _box[1] = "\n".join([self.generate_one_entry(i) for i in living_meds])
            outputs.append(_box)

        # Owsla Box:
        if living_mediators:
            _box = ["", ""]
            _box[
                0
            ] = f"<b><u>{i18n.t('general.owsla', count=len(living_mediators)).upper()}</u></b>"

            _box[1] = "\n".join([self.generate_one_entry(i) for i in living_mediators])
            outputs.append(_box)

        # Rabbit Box:
        if living_warriors:
            _box = ["", ""]
            _box[
                0
            ] = f"<b><u>{i18n.t('general.rabbit', count=len(living_warriors)).upper()}</u></b>"

            _box[1] = "\n".join([self.generate_one_entry(i) for i in living_warriors])
            outputs.append(_box)

        # Rusasi Box:
        if living_apprentices:
            _box = ["", ""]
            _box[0] = f"<b><u>{i18n.t('general.rusasi', count=2).upper()}</u></b>"

            _box[1] = "\n".join(
                [self.generate_one_entry(i) for i in living_apprentices]
            )
            outputs.append(_box)

        # Queens and Kits Box:
        if queen_dict or living_kits:
            _box = ["", ""]
            _box[
                0
            ] = f"<b><u>{i18n.t('general.queen', count=2).upper()} AND {i18n.t('general.kit', count=2).upper()}</u></b>"

            # This one is a bit different.  First all the queens, and the kits they are caring for.
            all_entries = []
            for q in queen_dict:
                queen = Rabbit.fetch_cat(q)
                if not queen:
                    continue
                kits = []
                for k in queen_dict[q]:
                    kits += [
                        event_text_adjust(
                            Rabbit, f"{k.name} - {k.describe_cat(short=True)}", main_cat=k
                        )
                    ]
                if len(kits) == 1:
                    kits = i18n.t(
                        "screens.allegiances.caring_for",
                        kit=kits[0],
                        count=len(kits),
                    )
                else:
                    kits = i18n.t(
                        "screens.allegiances.caring_for",
                        kitten_list=", ".join(kits[:-1]),
                        last_kitten=kits[-1],
                        count=len(kits),
                    )
                all_entries.append(self.generate_one_entry(queen, kits))

            # Now kits without carers
            for k in living_kits:
                all_entries.append(
                    event_text_adjust(
                        Rabbit,
                        f"{str(k.name).upper()} - {k.describe_cat(short=True)}",
                        main_cat=k,
                    )
                )

            _box[1] = "\n".join(all_entries)
            outputs.append(_box)

        # Elder Box:
        if living_elders:
            _box = ["", ""]
            _box[0] = f"<b><u>{i18n.t('general.elder', count=2).upper()}</u></b>"

            _box[1] = "\n".join([self.generate_one_entry(i) for i in living_elders])
            outputs.append(_box)

        return outputs
