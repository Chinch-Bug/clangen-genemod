from random import randrange, choice

import pygame
import pygame_gui

from scripts.cat.cats import create_cat, create_example_cats
from scripts.cat.enums import CatRank
from scripts.cat.sprites.load_sprites import sprites
from scripts.clan_package.settings.clan_settings import reset_loaded_clan_settings
from scripts.config import reset_config
from scripts.game_structure import image_cache
from scripts.game_structure.game import Switch
from scripts.game_structure.game.settings import game_setting_set
from scripts.game_structure.game.switches import switch_set_value
from scripts.game_structure.screen_settings import MANAGER
from scripts.screens.enums import GameScreen
from scripts.screens.make_clan_screens.MakeClanScreenBase import MakeClanScreenBase
from scripts.ui.elements.checkbox import UICheckbox
from scripts.ui.elements.image_button import UIImageButton
from scripts.ui.elements.surface_image_button import UISurfaceImageButton
from scripts.ui.elements.text_box_tweaked import UITextBoxTweaked
from scripts.ui.generate_button import ButtonStyles, get_button_dict
from scripts.ui.scale import ui_scale, ui_scale_dimensions
from scripts.ui.theme import get_text_box_theme


class ChooseClancountScreen(MakeClanScreenBase):
    def __init__(self, name="choose_clancount_screen"):
        super().__init__(name)

        self.clan_count_mode = "singleclan"

    def screen_switches(self):
        # Reset variables
        reset_loaded_clan_settings()
        reset_config()
        switch_set_value(Switch.possible_cats, create_example_cats())

        super().screen_switches()
        self.elements["previous_step"].disable()
        self.elements["next_step"].enable()

        self.set_mute_button_position("topright")
        self.show_mute_buttons()
        self.set_bg("default", "mainmenu_bg")

        # MODE DESCRIPTION
        text_box = image_cache.load_image(
            "resources/images/game_mode_text_box.png"
        ).convert_alpha()
        self.elements["game_mode_background"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((325, 130), (399, 461))),
            pygame.transform.scale(text_box, ui_scale_dimensions((399, 461))),
            manager=MANAGER,
        )

        # Create all the elements.
        self.elements["singleclan_mode_button"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((109, 240), (132, 30))),
            "screens.make_clan.singleclan_label",
            get_button_dict(ButtonStyles.SQUOVAL, (132, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
        )
        self.elements["multiclan_mode_button"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((94, 320), (162, 34))),
            "screens.make_clan.multiclan_label",
            get_button_dict(ButtonStyles.SQUOVAL, (132, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
        )

        self.elements["game_mode_warning"] = pygame_gui.elements.UITextBox(
            "screens.make_clan.game_mode_warning",
            ui_scale(pygame.Rect((100, 581), (600, 40))),
            object_id=get_text_box_theme("#text_box_30_horizcenter"),
            manager=MANAGER,
        )

        self.elements["mode_details"] = UITextBoxTweaked(
            "",
            ui_scale(pygame.Rect((345, 180), (365, 360))),
            object_id="#text_box_30_horizleft",
            manager=MANAGER,
        )

        self.elements["mode_name"] = pygame_gui.elements.UITextBox(
            "",
            ui_scale(pygame.Rect((425, 135), (200, 27))),
            object_id="#text_box_30_horizcenter_light",
            manager=MANAGER,
        )

        self.refresh_text_and_buttons()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.elements['singleclan_mode_button']:
                self.clan_count_mode = 'singleclan'
                self.refresh_text_and_buttons()
            elif event.ui_element == self.elements['multiclan_mode_button']:
                self.clan_count_mode = 'multiclan'
                self.refresh_text_and_buttons()

            elif event.ui_element == self.elements["next_step"]:
                self.clan_info.clan_count_mode = self.clan_count_mode
                self.change_screen(GameScreen.MAKE_CLAN_CHOOSE_MODE)

        return super().handle_event(event)

    def refresh_text_and_buttons(self):
        """Refreshes the button states and text boxes"""
        # Set the mode explanation text
        if self.clan_count_mode == "singleclan":
            display_text = "screens.make_clan.singleclan_info"
            display_name = "screens.make_clan.singleclan_label"
        elif self.clan_count_mode == "multiclan":
            display_text = "screens.make_clan.multiclan_info"
            display_name = "screens.make_clan.multiclan_label"
        else:
            display_text = ""
            display_name = "ERROR"

        self.elements["mode_details"].set_text(display_text)
        self.elements["mode_name"].set_text(display_name)

        # Update the enabled buttons for the game selection
        if self.clan_count_mode == "singleclan":
            self.elements["singleclan_mode_button"].disable()
            self.elements["multiclan_mode_button"].enable()
        elif self.clan_count_mode == "multiclan":
            self.elements["singleclan_mode_button"].enable()
            self.elements["multiclan_mode_button"].disable()
        else:
            self.elements["singleclan_mode_button"].enable()
            self.elements["multiclan_mode_button"].enable()
