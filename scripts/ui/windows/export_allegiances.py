import os

import pygame
import pygame_gui

from scripts.game_structure.ui_elements import (
    UISurfaceImageButton,
)
from scripts.housekeeping.datadir import get_saved_allegiances_dir, open_data_dir
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from scripts.ui.windows.window_base_class import GameWindow
from scripts.ui.scale import ui_scale


class ExportAllegiancesWindow(GameWindow):
    def __init__(self, allegiances_data, file_name):
        super().__init__(
            ui_scale(pygame.Rect((200, 175), (400, 150))),
        )

        self.allegiances_data = allegiances_data
        self.file_name = file_name

        self.save_as_txt = UISurfaceImageButton(
            ui_scale(pygame.Rect((0, 20), (135, 30))),
            "screens.allegiances.save_as_txt",
            get_button_dict(ButtonStyles.SQUOVAL, (135, 30)),
            object_id="@buttonstyles_squoval",
            sound_id="save",
            container=self,
            anchors={"centerx": "centerx"},
        )

        self.open_data_directory_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((0, 105), (178, 30))),
            "buttons.open_data_directory",
            get_button_dict(ButtonStyles.SQUOVAL, (178, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
            starting_height=2,
            tool_tip_text="buttons.open_data_directory_tooltip",
            anchors={"centerx": "centerx"},
        )

        self.confirm_text = pygame_gui.elements.UITextBox(
            "",
            ui_scale(pygame.Rect((0, 55), (390, -1))),
            object_id="#text_box_26_horizcenter_vertcenter_spacing_95",
            container=self,
            starting_height=2,
            anchors={"centerx": "centerx"},
        )

    def save_text(self):
        file_name = self.file_name
        file_number = ""
        i = 0
        while True:
            if os.path.isfile(
                f"{get_saved_allegiances_dir()}/{file_name + file_number}.txt"
            ):
                i += 1
                file_number = f"_{i}"
            else:
                break
        
        full_text = ""
        for row in self.allegiances_data:
            rank_box = row[0].replace("<u>", "").replace("<b>", "").replace("</b>", "").replace("</u>", "")
            if len(rank_box) < 8:
                rank_box += "\t"
            full_text += f"{rank_box}\t{row[-1].replace("<i>", "").replace("</i>", "").replace("\n", "\n\t")}\n"

        with open(f"{get_saved_allegiances_dir()}/{file_name + file_number}.txt", "w") as f:
            f.write(full_text)
        
        return f"{file_name + file_number}.txt"

    def process_event(self, event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.open_data_directory_button:
                open_data_dir()
                return True
            elif event.ui_element == self.save_as_txt:
                file_name = self.save_text()
                self.confirm_text.set_text(
                    "windows.confirm_saved_allegiances", text_kwargs={"file_name": file_name}
                )

        return super().process_event(event)
