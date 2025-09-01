import i18n
import pygame
import pygame_gui
from pygame_gui.core import ObjectID

from scripts.cat.cats import Cat
from scripts.game_structure import game
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from scripts.game_structure.screen_settings import MANAGER
from scripts.utility import (
    get_text_box_theme,
    ui_scale,
    get_alive_clan_queens,
    ui_scale_offset,
    adjust_list_text,
    event_text_adjust,
)
from scripts.game_structure.game.switches import (
    switch_set_value,
    Switch,
)
from .Screens import Screens
from ..cat.enums import CatRank
from scripts.game_structure.ui_elements import (
    AllegiancesCat,
    UIDropDownContainer,
    UISurfaceImageButton,
    UIModifiedScrollingContainer
)


class AllegiancesScreen(Screens):
    allegiance_list = []

    def __init__(self, name=None):
        super().__init__(name)
        self.names_boxes = None
        self.ranks_boxes = None
        self.scroll_container = None
        self.heading = None

        self.event_screen_container = None
        self.current_clan = None
        self.choose_group_button = None
        self.living_groups_container = None
        self.choose_group_buttons = {}
        self.choose_living_dropdown = None

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element in self.names_buttons:
                switch_set_value(Switch.cat, event.ui_element.return_cat_id())
                self.change_screen('profile screen')
            elif event.ui_element in self.choose_group_buttons.values():
                self.choose_living_dropdown.close()
                self.current_clan = event.ui_element.text.replace("Clan", "")
                self.current_clan = [c for c in game.clan.all_other_clans if c.displayname == self.current_clan]
                if self.current_clan:
                    self.current_clan = self.current_clan[0]
                else:
                    self.current_clan = game.clan
                
                self.fill_allegiances()
            else:
                self.menu_button_pressed(event)
                self.mute_button_pressed(event)

    def on_use(self):
        super().on_use()

    def screen_switches(self):
        super().screen_switches()

        # Set Menu Buttons.
        self.show_menu_buttons()
        self.show_mute_buttons()
        self.set_disabled_menu_buttons(["allegiances"])
        self.update_heading_text(f"{game.clan.displayname}Clan")

        if not self.current_clan:
            self.current_clan = game.clan
        if game.clan.clancount == 'multiclan':

            self.event_screen_container = pygame_gui.core.UIContainer(
                ui_scale(pygame.Rect((0, 100), (800, 300))),
                starting_height=1,
                manager=MANAGER,
            )
            self.choose_group_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((510, 0), (190, 34))),
                "screens.list.choose_group",
                get_button_dict(ButtonStyles.DROPDOWN, (190, 34)),
                object_id="@buttonstyles_dropdown",
                manager=MANAGER,
                starting_height=1,
                container=self.event_screen_container,
            )

            self.living_groups_container = pygame_gui.elements.UIAutoResizingContainer(
                ui_scale(pygame.Rect((510, 32), (0, 0))),
                object_id="#choose_group_container",
                manager=MANAGER,
                starting_height=1,
                container=self.event_screen_container,
            )
            self.living_groups_container.change_layer(10)
            self.choose_group_buttons[game.clan.displayname] = UISurfaceImageButton(
                ui_scale(pygame.Rect((0, 0), (190, 34))),
                game.clan.displayname + "Clan",
                get_button_dict(ButtonStyles.DROPDOWN, (190, 34)),
                container=self.living_groups_container,
                object_id=ObjectID(
                    class_id="@buttonstyles_dropdown", object_id=None),
                starting_height=2,
                manager=MANAGER,
            )
            y_pos = 32
            for clan in game.clan.all_other_clans:
                self.choose_group_buttons[clan.displayname] = UISurfaceImageButton(
                    ui_scale(pygame.Rect((0, y_pos), (190, 34))),
                    clan.displayname + "Clan",
                    get_button_dict(ButtonStyles.DROPDOWN, (190, 34)),
                    container=self.living_groups_container,
                    object_id=ObjectID(
                        class_id="@buttonstyles_dropdown", object_id=None),
                    starting_height=2,
                    manager=MANAGER,
                )
                y_pos += 32

            self.choose_living_dropdown = UIDropDownContainer(
                self.living_groups_container.relative_rect,
                container=self.event_screen_container,
                object_id="#choose_living_dropdown",
                starting_height=1,
                parent_button=self.choose_group_button,
                child_button_container=self.living_groups_container,
                manager=MANAGER,
            )

            self.choose_living_dropdown.close()
            self.choose_living_dropdown.show()

        self.fill_allegiances()

    def exit_screen(self):
        for x in self.ranks_boxes:
            x.kill()
        del self.ranks_boxes
        for x in self.names_boxes:
            x.kill()
        del self.names_boxes
        for x in self.names_buttons:
            x.kill()
        del self.names_buttons
        self.scroll_container.kill()
        del self.scroll_container
        self.heading.kill()
        del self.heading

        if game.clan.clancount == 'multiclan':
            self.event_screen_container.kill()
            self.choose_group_button.kill()
            self.living_groups_container.kill()
            for x in self.choose_group_buttons.values():
                x.kill()
            self.choose_living_dropdown.kill()
            del self.event_screen_container
            del self.choose_group_button
            del self.living_groups_container
            self.choose_group_buttons = {}
            del self.choose_living_dropdown

    def fill_allegiances(self):
        # Heading
        if hasattr(self, "heading") and self.heading:
            self.heading.kill()
        self.heading = pygame_gui.elements.UITextBox(
            "screens.allegiances.heading",
            ui_scale(pygame.Rect((0, 115), (400, 40))),
            text_kwargs={"clan_name": self.current_clan.displayname},
            object_id=get_text_box_theme(
                "#text_box_34_horizcenter_vertcenter"),
            manager=MANAGER,
            anchors={"centerx": "centerx"},
        )
        allegiance_list = self.get_allegiances_text()

        if hasattr(self, "scroll_container") and self.scroll_container:
            self.scroll_container.kill()
        self.scroll_container = UIModifiedScrollingContainer(
            ui_scale(pygame.Rect((50, 165), (715, 470))),
            allow_scroll_x=False,
            allow_scroll_y=True,
            manager=MANAGER,
        )

        self.ranks_boxes = []
        self.names_boxes = []
        self.names_buttons = []
        y_pos = 0
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
            offset = 7
            self.names_buttons.append(AllegiancesCat(
                pygame.Rect(
                    (offset, -
                     self.ranks_boxes[-1].get_relative_rect()[3]+offset),
                    ui_scale_offset((565, -1))),
                x[1],
                object_id=get_text_box_theme("#allegiance"),
                container=self.scroll_container, manager=MANAGER,
                anchors={
                    "top_target": self.ranks_boxes[-1],
                    "left_target": self.ranks_boxes[-1],
                    "left": "left",
                    "right": "right",
                }))
            self.names_buttons[-1].set_cat_id(x[2])
            self.names_boxes.append(
                pygame_gui.elements.UITextBox(
                    x[3],
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

    @staticmethod
    def generate_one_entry(cat, extra_details=""):
        """Extra Details will be placed after the cat description, but before the apprentice (if they have one)."""
        output = f"{str(cat.name).upper()} - {cat.describe_cat()} {extra_details}"

        if len(cat.apprentice) == 0:
            return [str(cat.name).upper(), cat.ID, event_text_adjust(Cat, output, main_cat=cat)]

        output += f"\n      {i18n.t('general.apprentice', count=len(cat.apprentice)).upper()}: "
        output += adjust_list_text(
            [
                str(Cat.fetch_cat(i).name).upper()
                for i in cat.apprentice
                if Cat.fetch_cat(i)
            ]
        ).upper()

        return [str(cat.name).upper(), cat.ID, event_text_adjust(Cat, output, main_cat=cat)]

    def get_allegiances_text(self):
        """Determine Text. Ouputs list of tuples."""

        living_cats = [
            i for i in Cat.all_cats.values() if i.status.fetch_clan_object() == self.current_clan
        ]
        living_meds = []
        living_mediators = []
        living_warriors = []
        living_apprentices = []
        living_kits = []
        living_elders = []
        for cat in living_cats:
            if cat.status.rank == CatRank.MEDICINE_CAT:
                living_meds.append(cat)
            elif cat.status.rank == CatRank.WARRIOR:
                living_warriors.append(cat)
            elif cat.status.rank == CatRank.MEDIATOR:
                living_mediators.append(cat)
            elif cat.status.rank.is_any_apprentice_rank():
                living_apprentices.append(cat)
            elif cat.status.rank.is_baby():
                living_kits.append(cat)
            elif cat.status.rank == CatRank.ELDER:
                living_elders.append(cat)
        if not len(living_meds):
            for cat in living_apprentices:
                if cat.status.rank == CatRank.MEDICINE_APPRENTICE:
                    living_meds.append(cat)
                    living_apprentices.remove(cat)
        if not len(living_mediators):
            for cat in living_apprentices:
                if cat.status.rank == CatRank.MEDIATOR_APPRENTICE:
                    living_mediators.append(cat)
                    living_apprentices.remove(cat)


        living_meds = sorted(living_meds, key=lambda x: x.moons, reverse=True)
        living_mediators = sorted(living_mediators, key=lambda x: x.moons, reverse=True)
        living_warriors = sorted(living_warriors, key=lambda x: x.moons, reverse=True)
        living_apprentices = sorted(living_apprentices, key=lambda x: x.moons, reverse=True)
        living_kits = sorted(living_kits, key=lambda x: x.moons, reverse=True)
        living_elders = sorted(living_elders, key=lambda x: x.moons, reverse=True)

        # Find Queens:
        queen_dict, living_kits = get_alive_clan_queens(living_cats, self.current_clan.group_ID)

        # Remove queens from warrior or elder lists, if they are there.  Let them stay on any other lists.
        for q in queen_dict:
            queen = Cat.fetch_cat(q)
            if not queen:
                continue
            if queen in living_warriors:
                living_warriors.remove(queen)
            elif queen in living_elders:
                living_elders.remove(queen)

        # Clan Leader Box:
        # Pull the Clan leaders
        outputs = []
        if self.current_clan.leader and not (self.current_clan.leader.dead or self.current_clan.leader.status.is_outsider):
            x = self.generate_one_entry(self.current_clan.leader)
            outputs.append(
                [
                    f"<b><u>{i18n.t('general.leader', count=1).upper()}</u></b>",
                    x[0],
                    x[1],
                    x[2]
                ]
            )

        # Deputy Box:
        if self.current_clan.deputy and not (self.current_clan.deputy.dead or self.current_clan.deputy.status.is_outsider):
            x = self.generate_one_entry(self.current_clan.deputy)
            outputs.append(
                [
                    f"<b><u>{i18n.t('general.deputy', count=1).upper()}</u></b>",
                    x[0],
                    x[1],
                    x[2]
                ]
            )

        # Healer Box:
        if living_meds:
            for i in range(len(living_meds)):    
                _box = ["", "", "", ""]
                if i == 0:    
                    _box[0] = f"<b><u>{i18n.t('general.healer', count=len(living_meds)).upper()}</u></b>"
                else:
                    _box[0] = ""
                x = self.generate_one_entry(living_meds[i])
                _box[1] = x[0]
                _box[2] = x[1]
                _box[3] = x[2]
            
                #_box[1] = "\n".join([self.generate_one_entry(i) for i in living_meds])
                outputs.append(_box)
        
        # Mediator Box:
        if living_mediators:
            for i in range(len(living_mediators)): 
                _box = ["", "", "", ""]   
                if i == 0:    
                    _box[0] = f"<b><u>{i18n.t('general.mediator', count=len(living_mediators)).upper()}</u></b>"
                else:
                    _box[0] = ""
                x = self.generate_one_entry(living_mediators[i])
                _box[1] = x[0]
                _box[2] = x[1]
                _box[3] = x[2]
            
                #_box[1] = "\n".join([self.generate_one_entry(i) for i in living_mediators])
                outputs.append(_box)

        # Warrior Box:
        if living_warriors:
            for i in range(len(living_warriors)):   
                box = ["", "", "", ""]
                if i == 0:    
                    box[0] = f"<b><u>{i18n.t('general.warrior', count=len(living_warriors)).upper()}</u></b>"
                else:
                    box[0] = ""
                x = self.generate_one_entry(living_warriors[i])
                box[1] = x[0]
                box[2] = x[1]
                box[3] = x[2]
                outputs.append(box)
         # Apprentice Box:
        if living_apprentices:
            for i in range(len(living_apprentices)):   
                _box = ["", "", "", ""] 
                if i == 0:    
                    _box[0] = f"<b><u>{i18n.t('general.apprentice', count=len(living_apprentices)).upper()}</u></b>"
                else:
                    _box[0] = ""
                x = self.generate_one_entry(living_apprentices[i])
                _box[1] = x[0]
                _box[2] = x[1]
                _box[3] = x[2]
                outputs.append(_box)
        
         # Queens and Kits Box:
        if queen_dict or living_kits:
            # This one is a bit different.  First all the queens, and the kits they are caring for. 
            all_entries = []
            for q in queen_dict:
                queen = Cat.fetch_cat(q)
                if not queen:
                    continue
                kittens = []
                for k in queen_dict[q]:
                    kittens += [
                        event_text_adjust(
                            Cat, f"{k.name} - {k.describe_cat(short=True)}", main_cat=k
                        )
                    ]
                if len(kittens) == 1:
                    kittens = i18n.t(
                        "screens.allegiances.caring_for",
                        kitten=kittens[0],
                        count=len(kittens),
                    )
                else:
                    kittens = i18n.t(
                        "screens.allegiances.caring_for",
                        kitten_list=", ".join(kittens[:-1]),
                        last_kitten=kittens[-1],
                        count=len(kittens),
                    )
                all_entries.append(self.generate_one_entry(queen, kittens))

            # Now kittens without carers
            for k in living_kits:
                all_entries.append([str(k.name).upper(), k.ID, event_text_adjust(
                        Cat,
                        f"{str(k.name).upper()} - {k.describe_cat(short=True)}",
                        main_cat=k,
                    )])
            
            if all_entries:
                for i in range(len(all_entries)):
                    _box = ["", "", "", ""]
                    if i == 0:
                        _box[0] = f"<b><u>{i18n.t('general.queen', count=len(queen_dict)).upper()} AND {i18n.t('general.kit', count=2).upper()}</u></b>"
                    else:
                        _box[0] = ''
                    
                    _box[1] = all_entries[i][0]
                    _box[2] = all_entries[i][1]
                    _box[3] = all_entries[i][2]
                    outputs.append(_box)

        # Elder Box:
        if living_elders:
            for i in range(len(living_elders)):    
                _box = ["", "", "", ""]
                if i == 0:    
                    _box[0] = f"<b><u>{i18n.t('general.elder', count=len(living_elders)).upper()}</u></b>"
                else:
                    _box[0] = ""
                x = self.generate_one_entry(living_elders[i])
                _box[1] = x[0]
                _box[2] = x[1]
                _box[3] = x[2]
                outputs.append(_box)

        return outputs
