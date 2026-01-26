import pygame
import pygame_gui

from scripts.game_structure import game
from scripts.game_structure.ui_elements import (
    UIImageButton,
    UISurfaceImageButton,
)
from scripts.screens.enums import GameScreen
from scripts.ui.windows.window_base_class import GameWindow
from scripts.utility import ui_scale

from scripts.cat.cats import Cat, BACKSTORIES
from scripts.cat.enums import CatStanding, CatRank, CatAge
from scripts.game_structure import game
from scripts.ui.generate_button import ButtonStyles, get_button_dict


class ChangeCatClanWindow(GameWindow):
    """This window allows the user to select a clan to switch a living clan cat to."""

    def __init__(self, focus_cat):
        super().__init__(
            ui_scale(pygame.Rect((250, 120), (300, 225))),
            resizable=False,
        )
        self.set_blocking(True)
        self.the_cat = focus_cat
        self.selected = None
        self.save_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((80, 180), (139, 30))),
            "windows.change_clan",
            get_button_dict(ButtonStyles.SQUOVAL, (139, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )
        self.save_button.disable()

        self.checkboxes = {}
        self.refresh_checkboxes()

        # Text
        self.texts = {}
        self.texts["prompt"] = pygame_gui.elements.UITextBox(
            "windows.change_clan_prompt",
            ui_scale(pygame.Rect((25, 5), (250, 30))),
            object_id="#text_box_30_horizcenter",
            container=self,
        )
        n = 0
        for clan in [game.clan] + game.clan.all_other_clans:
            if self.the_cat.status.group_ID == clan.group_ID:
                continue
            self.texts[clan.displayname] = pygame_gui.elements.UITextBox(
                clan.displayname + "clan",
                ui_scale(pygame.Rect(107, n * 27 + 38, -1, 25)),
                object_id="#text_box_30_horizleft_pad_0_8",
                container=self,
            )
            n += 1

    def refresh_checkboxes(self):
        for x in self.checkboxes.values():
            x.kill()
        self.checkboxes = {}

        n = 0
        for clan in [game.clan] + game.clan.all_other_clans:
            if self.the_cat.status.group_ID == clan.group_ID:
                continue
            box_type = "@checked_checkbox" if self.selected == clan else "@unchecked_checkbox"

            self.checkboxes[clan.displayname] = UIImageButton(
                ui_scale(pygame.Rect((75, n * 27 + 35), (34, 34))),
                "",
                container=self,
                object_id=box_type,
            )
            n += 1

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.save_button:
                if self.the_cat.status.group:
                    self.the_cat.backstory = "otherclan1"
                    if self.the_cat.status.rank == CatRank.LEADER:
                        self.the_cat.status.fetch_clan_object().leader = None
                    elif self.the_cat.status.rank == CatRank.DEPUTY:
                        self.the_cat.status.fetch_clan_object().deputy = None
                    elif self.the_cat.status.rank == CatRank.LEADER:
                        self.the_cat.status.fetch_clan_object().remove_med_cat(self.the_cat)
                    self.the_cat.history.add_beginning(False)
                    self.the_cat.status._modify_group(
                        CatRank.WARRIOR if self.the_cat.status.rank in (CatRank.LEADER, CatRank.DEPUTY) else self.the_cat.status.rank, 
                        CatStanding.LEFT, self.selected.group_ID)
                    for app in self.the_cat.apprentice.copy():
                        app_ob = Cat.fetch_cat(app)
                        if app_ob:
                            app_ob.update_mentor()
                else:
                    self.the_cat.add_to_clan(self.selected.group_ID)
                    if (
                        self.the_cat.backstory
                        in BACKSTORIES["backstory_categories"][
                            "healer_backstories"
                        ]
                    ):
                        if self.the_cat.age == CatAge.ADOLESCENT:
                            self.the_cat.status._change_rank(CatRank.MEDICINE_APPRENTICE)
                        else:
                            self.the_cat.status._change_rank(CatRank.MEDICINE_CAT)
                self.the_cat.update_mentor()
                self.the_cat.thoughts()
                game.all_screens["profile_screen"].exit_screen()
                game.all_screens["profile_screen"].screen_switches()
                self.kill()
            if event.ui_element in self.checkboxes.values():
                for clan_name, value in self.checkboxes.items():
                    if value == event.ui_element:
                        if value.object_ids[1] == "@unchecked_checkbox":
                            self.save_button.enable()
                            self.selected = next(filter(lambda c: c.displayname == clan_name, game.clan.all_other_clans), game.clan)
                        if value.object_ids[1] == "@checked_checkbox":
                            self.save_button.disable()
                            self.selected = None
                        self.refresh_checkboxes()

        return super().process_event(event)