import pygame
import pygame_gui

from scripts.game_structure import game
from scripts.ui.elements.image_button import UIImageButton
from scripts.ui.elements.checkbox import UICheckbox
from scripts.screens.enums import GameScreen
from scripts.ui.windows.window_base_class import GameWindow
from scripts.ui.scale import ui_scale


class CatToggleWindow(GameWindow):
    """This window allows the user to edit various cat behavior toggles"""

    cat_toggles = [
        "prevent_fading",
        "prevent_kits",
        "prevent_retirement",
        "prevent_romance",
    ]

    def __init__(self, cat):
        super().__init__(
            ui_scale(pygame.Rect((300, 215), (400, 185))),
        )
        self.the_cat = cat

        self.checkboxes = {}
        self.textbox = {}
        self.refresh_checkboxes()

        prev_element = None
        for text in self.cat_toggles:
            self.textbox[text] = pygame_gui.elements.UITextBox(
                f"windows.{text}",
                ui_scale(pygame.Rect(55, 0 if prev_element else 26, -1, 34)),
                object_id="#text_box_30_horizleft_pad_0_8",
                container=self,
                anchors={"top_target": prev_element} if prev_element else None,
            )
            prev_element = self.textbox[text]

    def refresh_checkboxes(self):
        for ele in self.checkboxes:
            self.checkboxes[ele].kill()
        self.checkboxes = {}

        self.checkboxes["prevent_fading"] = UICheckbox(
            (22, 25),
            container=self,
            tool_tip_text=f"windows.prevent_fading_tooltip",
            check=self.the_cat.prevent_fading,
        )
        self.checkboxes["prevent_kits"] = UICheckbox(
            (22, 0),
            container=self,
            anchors={
                "top_target": self.checkboxes["prevent_fading"],
            },
            tool_tip_text=f"windows.prevent_kits_tooltip",
            check=self.the_cat.no_kits,
        )

        self.checkboxes["prevent_retirement"] = UICheckbox(
            (22, 0),
            container=self,
            anchors={
                "top_target": self.checkboxes["prevent_kits"],
            },
            tool_tip_text=f"windows.prevent_retirement_tooltip",
            check=self.the_cat.no_retire,
        )

        self.checkboxes["prevent_romance"] = UICheckbox(
            (22, 0),
            container=self,
            anchors={
                "top_target": self.checkboxes["prevent_retirement"],
            },
            tool_tip_text=f"windows.prevent_romance_tooltip",
            check=self.the_cat.no_mates,
        )

        if self.the_cat in [game.clan.instructor] + [clan.instructor for clan in game.clan.all_other_clans if clan.instructor]:
            self.checkboxes["prevent_fading"].set_tooltip(
                "windows.prevent_fading_tooltip_guide"
            )
            self.checkboxes["prevent_fading"].disable()

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.back_button:
                game.all_screens[GameScreen.PROFILE].exit_screen()
                game.all_screens[GameScreen.PROFILE].screen_switches()
            elif event.ui_element == self.checkboxes["prevent_fading"]:
                self.checkboxes["prevent_fading"].toggle()
                self.the_cat.prevent_fading = self.checkboxes["prevent_fading"].checked
            elif event.ui_element == self.checkboxes["prevent_kits"]:
                self.checkboxes["prevent_kits"].toggle()
                self.the_cat.no_kits = self.checkboxes["prevent_kits"].checked
            elif event.ui_element == self.checkboxes["prevent_retirement"]:
                self.checkboxes["prevent_retirement"].toggle()
                self.the_cat.no_retire = self.checkboxes["prevent_retirement"].checked
            elif event.ui_element == self.checkboxes["prevent_romance"]:
                self.checkboxes["prevent_romance"].toggle()
                self.the_cat.no_mates = self.checkboxes["prevent_romance"].checked

        return super().process_event(event)
