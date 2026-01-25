import pygame
import pygame_gui
import os
from random import random

from scripts.game_structure import game
from scripts.game_structure.ui_elements import (
    UIImageButton,
    UISurfaceImageButton,
    UITextBoxTweaked,
)
from scripts.screens.enums import GameScreen
from scripts.ui.windows.window_base_class import GameWindow
from scripts.utility import ui_scale

from scripts.cat.cats import Cat
from scripts.cat_relations.inheritance import Inheritance
from scripts.game_structure import game
from scripts.ui.generate_button import ButtonStyles, get_button_dict

from scripts.housekeeping.datadir import (
    get_save_dir,
)

class DeleteCatCheck(GameWindow):
    def __init__(self, reloadscreen, clan_name):
        super().__init__(
            ui_scale(pygame.Rect((250, 200), (300, 275))),
            resizable=False,
        )
        self.set_blocking(True)
        self.clan_name = clan_name
        self.reloadscreen = reloadscreen

        self.delete_check_message = UITextBoxTweaked(
            f"Do you wish to delete your faded cats? This is permanent and cannot be undone. Making a copy of save data is recommended in case any issues arise.",
            ui_scale(pygame.Rect((20, 20), (250, -1))),
            line_spacing=1,
            object_id="#text_box_30_horizcenter",
            container=self,
        )

        self.delete_it_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((71, 160), (153, 30))),
            "Delete it!",
            get_button_dict(ButtonStyles.SQUOVAL, (153, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )
        self.go_back_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((71, 205), (153, 30))),
            "No! Go back!",
            get_button_dict(ButtonStyles.SQUOVAL, (153, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )

        self.go_back_button.enable()
        self.delete_it_button.enable()

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.delete_it_button:
                rempath = get_save_dir() + "/" + self.clan_name + "/faded_cats/"
                rempath_h = get_save_dir() + "/" + self.clan_name + "/history/"
                # get all former mentors (preserve history mentor influence text)
                mentors = []
                history_event_cats = []
                for cat in Cat.all_cats.values():
                    mentors += cat.former_mentor
                # get any other cats relevant to history text
                    if not cat.history:
                        continue
                    if cat.history.died_by:
                        for died in cat.history.died_by:
                            if 'r_c' in died["text"]:
                                history_event_cats.append(died["involved"])
                    if cat.history.scar_events:
                        for scar in cat.history.scar_events:
                            if 'r_c' in scar["text"]:
                                history_event_cats.append(scar["involved"])
                    if cat.history.murder:
                        for killed in cat.history.murder.get("is_murderer", []):
                            history_event_cats.append(killed["victim"])
                        for killed in cat.history.murder.get("is_victim", []):
                            history_event_cats.append(killed["murderer"])
                # get murder cats
                # put together all living cat + family tree data with all that
                safe_ids = Inheritance.get_all_cat_ids() + list(Cat.all_cats.keys()) + \
                    list(set(mentors)) + list(set(history_event_cats))
                if os.path.exists(rempath):
                    for x in os.listdir(rempath):
                        fileName = x.split('.')
                        if fileName[0] not in safe_ids and os.path.exists(rempath + x):
                            os.remove(rempath + x)
                            if os.path.exists(rempath_h + x.replace(".json", "_history.json")):
                                os.remove(
                                    rempath_h + x.replace(".json", "_history.json"))
                self.kill()
                self.reloadscreen(GameScreen.CLAN_SETTINGS)

            elif event.ui_element == self.go_back_button:
                self.kill()
        return super().process_event(event)


class DeleteCatHistoryCheck(GameWindow):
    def __init__(self, reloadscreen, clan_name):
        super().__init__(
            ui_scale(pygame.Rect((250, 200), (300, 180))),
            resizable=False,
        )
        self.set_blocking(True)
        self.reloadscreen = reloadscreen
        self.clan_name = clan_name

        self.delete_check_message = UITextBoxTweaked(
            f"Do you wish to delete your faded cats' history information? This is permanent and cannot be undone.",
            ui_scale(pygame.Rect((20, 20), (260, -1))),
            line_spacing=1,
            object_id="#text_box_30_horizcenter",
            container=self,
        )

        self.delete_it_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((71, 100), (153, 30))),
            "Delete it!",
            get_button_dict(ButtonStyles.SQUOVAL, (153, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )
        self.go_back_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((71, 145), (153, 30))),
            "No! Go back!",
            get_button_dict(ButtonStyles.SQUOVAL, (153, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )

        self.go_back_button.enable()
        self.delete_it_button.enable()

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.delete_it_button:
                rempath = get_save_dir() + "/" + self.clan_name + "/history/"
                safe_ids = list(Cat.all_cats.keys())
                if os.path.exists(rempath):
                    for x in os.listdir(rempath):
                        fileName = x.split('_')
                        if fileName[0] not in safe_ids and os.path.exists(rempath + x):
                            os.remove(rempath + x)
                self.kill()
                self.reloadscreen(GameScreen.CLAN_SETTINGS)

            elif event.ui_element == self.go_back_button:
                self.kill()
        return super().process_event(event)
