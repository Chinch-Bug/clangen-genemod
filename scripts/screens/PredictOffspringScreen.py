from math import ceil
from random import choice

import i18n
import pygame.transform
import pygame_gui.elements

from scripts.cat.cats import Cat
from scripts.game_structure import image_cache
from scripts.game_structure.game_essentials import game
from pygame_gui.elements import UIDropDownMenu, UITextBox
from pygame import Rect
from scripts.game_structure.ui_elements import (
    UIImageButton,
    UISpriteButton,
    UIRelationStatusBar,
    UISurfaceImageButton,
)
from scripts.utility import (
    get_text_box_theme,
    ui_scale,
    shorten_text_to_fit,
    ui_scale_dimensions,
)
from .Screens import Screens
from ..game_structure.screen_settings import MANAGER
from ..ui.generate_box import get_box, BoxStyles
from ..ui.generate_button import get_button_dict, ButtonStyles
from ..ui.icon import Icon


def create_dropdown(pos, size, options, selected_option, style=None):
    return UIDropDownMenu(
        options,
        selected_option,
        ui_scale(Rect(pos, size)),
        object_id=f"#{style}",
        manager=MANAGER
    )

def get_selected_option(attribute, case):
    if isinstance(attribute, list):
        if len(attribute) > 0:  # selects an option in scar dropdowns for any existing scars
            return attribute[0].capitalize(), attribute[0].upper()
        else:
            return "None", "NONE"
    if attribute:
        if case == "upper":
            return attribute.capitalize(), attribute.upper()
        elif case == "lower":
            return attribute.capitalize(), attribute.lower()
        else:
            return attribute.capitalize(), attribute
    else:
        if case == "upper":
            return "None", "NONE"
        elif case == "lower":
            return "None", "none"
        else:
            return "None", "None"
        
def create_options_list(attribute, case):
    if case == "upper":
        return [(option.capitalize(), option.upper()) for option in attribute]
    elif case == "lower":
        return [(option.capitalize(), option.lower()) for option in attribute]
    else:
        return [(option.capitalize(), option) for option in attribute]
    

class PredictOffspringScreen(Screens):
    def __init__(self, name=None):
        super().__init__(name)
        self.back_button = None
        
        self.selected_cat = None
        self.selected_cat_elements = {}
        
        self.predict_button = None
        self.display_box = None
        self.predicted_offspring_elements = {}
        self.predicted_offspring = []
        
        self.possible_mates = []
        self.possible_mates_names = []
        self.possible_mates_box = None
        self.mate_dropdown = None
        
        self.selected_mate = None
        self.selected_mate_elements = {}
        

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            
            if event.ui_element == self.back_button:
                self.change_screen("profile screen")
                
            elif event.ui_element == self.predict_button:
                self.predicted_offspring = {}
                for ele in self.predicted_offspring_elements:
                    self.predicted_offspring_elements[ele].kill()
                self.predicted_offspring_elements = {}
                self.generate_offspring()
            
        elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            
            if event.ui_element == self.mate_dropdown:
                for ele in self.selected_mate_elements:
                        self.selected_mate_elements[ele].kill()
                self.selected_mate_elements = {}
                selected_option = self.mate_dropdown.selected_option[1]
                if selected_option =="NONE":
                    self.selected_mate = None
                else:
                    selected_option = selected_option.lower()
                    
                    mate_index = self.possible_mates_names.index(selected_option)
                    self.selected_mate = self.possible_mates[mate_index-1]
                    self.selected_mate_elements["image"] = pygame_gui.elements.UIImage(
                            ui_scale(pygame.Rect((540, 130), (150, 150))),
                            pygame.transform.scale(
                                self.selected_mate.sprite, ui_scale_dimensions((150, 150))
                            ),
                    )
                
                    
        
    def screen_switches(self):
        super().screen_switches()
        self.back_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((25, 25), (105, 30))),
            "buttons.back",
            get_button_dict(ButtonStyles.SQUOVAL, (105, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
        )
        self.selected_cat = Cat.fetch_cat(game.switches["cat"])
        
        self.possible_mates_box = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((490, 100), (275, 250))),
            get_box(BoxStyles.ROUNDED_BOX, (200, 250)),
        )
        self.possible_mates_box.disable()
        
        self.display_box = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((80, 380), (640, 250))),
            get_box(BoxStyles.ROUNDED_BOX, (640, 250)),
        )
        self.display_box.disable()
        
        self.possible_mates = [
            i
            for i in Cat.all_cats_list
            if i.is_potential_mate(self.selected_cat, for_love_interest=False, age_restriction=False, ignore_no_mates=True)
            and not (i.dead or i.outside)
        ]
        
        self.possible_mates_names = ["None"]
        for cat in self.possible_mates:
            self.possible_mates_names.append(str(cat.name).lower())
        
        self.mate_dropdown = create_dropdown((555, 295), (155, 40), create_options_list(self.possible_mates_names, "upper"),
                                                get_selected_option("None", "upper"))
        
        self.selected_cat_elements["selected_image"] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((70, 150), (200, 200))),
                pygame.transform.scale(
                    self.selected_cat.sprite, ui_scale_dimensions((200, 200))
                ),
        )
        
        self.predict_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((260, 300), (210, 60))),
            "predict offspring",
            get_button_dict(ButtonStyles.SQUOVAL, (160, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
        )
        self.selected_mate = None
        
        heading_rect = ui_scale(pygame.Rect((0, 20), (400, -1)))
        self.selected_cat_elements["heading"] = pygame_gui.elements.UITextBox(
            "Predict " + str(self.selected_cat.name) + "'s offspring",
            heading_rect,
            object_id=get_text_box_theme("#text_box_34_horizcenter"),
            anchors={
                "centerx": "centerx",
            }
        )
        
        self.selected_cat_elements["label"] = pygame_gui.elements.UILabel(
            ui_scale(pygame.Rect((530, 110), (200, 30))),
            "Second Parent",
            object_id="#text_box_30_horizcenter",
        )
        
    def one_offspring(self):
        if self.selected_mate:
            new_cat = Cat(parent1 = self.selected_cat.ID, parent2 = self.selected_mate.ID, status = "warrior", moons = 12, example = True)
        else:
            new_cat = Cat(parent1 = self.selected_cat.ID, status = "warrior", moons = 12, example = True)
        return new_cat
        
    def generate_offspring(self):
        
        self.predicted_offspring = []
                
        for i in range(10):
            self.predicted_offspring.append(self.one_offspring())
    
        index = 0
        indey = 0
        for offspring in self.predicted_offspring:
            self.predicted_offspring_elements["offspring" + str(index) + str(indey)] = pygame_gui.elements.UIImage(
                    ui_scale(pygame.Rect((105 + (index*120), 395 + indey), (100, 100))),
                    pygame.transform.scale(
                        offspring.sprite, ui_scale_dimensions((100, 100))
                    ),
            )
            if index < 4:
                index += 1
            else:
                index = 0
                indey = 115
            Cat.all_cats_list.remove(offspring)
            del Cat.all_cats[offspring.ID]
    
    def exit_screen(self):
        self.back_button.kill()
        del self.back_button
        self.predict_button.kill()
        del self.predict_button
        
        self.possible_mates_box.kill()
        del self.possible_mates_box
        self.mate_dropdown.kill()
        del self.mate_dropdown
        self.display_box.kill()
        del self.display_box
        
        for ele in self.selected_cat_elements:
            self.selected_cat_elements[ele].kill()
        self.selected_cat_elements = {}
        
        for ele in self.selected_mate_elements:
            self.selected_mate_elements[ele].kill()
        self.selected_mate_elements = {}
        
        for ele in self.predicted_offspring_elements:
            self.predicted_offspring_elements[ele].kill()
        self.predicted_offspring_elements = {}
        
        self.selected_mate = None
        self.predicted_offspring = []
        
        
        

