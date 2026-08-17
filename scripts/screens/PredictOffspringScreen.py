from math import ceil
from random import choice

import i18n
import pygame.transform
import pygame_gui.elements
from operator import xor

from scripts.cat.genotype import Genotype
from scripts.cat.factories.new_cat_factory import NewCatFactory
from scripts.cat.cats import Cat
from ..cat.enums import CatAge, CatRank, CatGroup
from scripts.game_structure import image_cache
from scripts.game_structure import game
from ..game_structure.game.settings import game_setting_get
from ..clan_package.settings import get_clan_setting
from ..clan_package.get_clan_cats import search_cats
from ..game_structure.game.switches import switch_get_value, Switch
from scripts.config import get_config
from pygame_gui.elements import UIDropDownMenu, UITextBox
from pygame import Rect
from ..ui.elements.sprite_button import UISpriteButton
from ..ui.elements.image_button import UIImageButton
from ..ui.elements.checkbox import UICheckbox
from ..ui.elements.surface_image_button import UISurfaceImageButton
from scripts.events_module.text_adjust import shorten_text_to_fit
from scripts.ui.theme import get_text_box_theme
from scripts.ui.scale import ui_scale, ui_scale_dimensions
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

        self.search_bar = None
        self.search_bar_image = None
        self.previous_search_text = ""
        self.search_genotype = False
        self.search_toggle_checkbox = None

        self.outsider_toggle_checkbox = None
        self.include_outsiders = False

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            
            if event.ui_element == self.back_button:
                self.change_screen("profile_screen")
                
            elif event.ui_element == self.predict_button:
                self.predicted_offspring = {}
                for ele in self.predicted_offspring_elements:
                    self.predicted_offspring_elements[ele].kill()
                self.predicted_offspring_elements = {}
                self.generate_offspring()

            if event.ui_element == self.search_toggle_checkbox:
                if event.ui_element.checked:
                    event.ui_element.set_tooltip("screens.list.search_genotypes_tooltip")
                    self.search_genotype = False
                else:
                    event.ui_element.set_tooltip("screens.list.search_names_tooltip")
                    self.search_genotype = True
                event.ui_element.toggle()
                self.search_bar.placeholder_text = "general.genotype_search" if self.search_genotype else "general.name_search"
                self.search_bar.set_text("")
                self.update_potential_mates_container()

            if event.ui_element == self.outsider_toggle_checkbox:
                event.ui_element.toggle()
                self.include_outsiders = event.ui_element.checked
                self.update_potential_mates_container()
            
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
                    self.selected_mate_elements["image"] = UISpriteButton(
                        ui_scale(pygame.Rect((540, 130), (150, 150))),
                        pygame.transform.scale(
                            self.selected_mate.sprite, ui_scale_dimensions((150, 150))
                        ),
                        object_id="#offspring_predict_cat",
                        tool_tip_text=self.selected_mate.create_genelist(),
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
        self.selected_cat = Cat.fetch_cat(switch_get_value(Switch.cat))
        
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

        self.update_potential_mates_container()

        self.selected_cat_elements["selected_image"] = UISpriteButton(
            ui_scale(pygame.Rect((70, 150), (200, 200))),
            pygame.transform.scale(
                self.selected_cat.sprite, ui_scale_dimensions((200, 200))
            ),
            object_id="#offspring_predict_cat",
            tool_tip_text=self.selected_cat.create_genelist(),
        )
        
        self.predict_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((260, 300), (210, 60))),
            "predict offspring",
            get_button_dict(ButtonStyles.SQUOVAL, (160, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
        )
        self.selected_mate = None

        if self.selected_cat.mate:
            selected_option = str(Cat.fetch_cat(self.selected_cat.mate[0]).name).lower()
            try:
                mate_index = self.possible_mates_names.index(selected_option)
                self.selected_mate = self.possible_mates[mate_index-1]
                self.selected_mate_elements["image"] = UISpriteButton(
                    ui_scale(pygame.Rect((540, 130), (150, 150))),
                    pygame.transform.scale(
                        self.selected_mate.sprite, ui_scale_dimensions(
                            (150, 150))
                    ),
                    object_id="#offspring_predict_cat",
                    tool_tip_text=self.selected_mate.create_genelist(),
                )
                self.mate_dropdown.kill()
                self.mate_dropdown = create_dropdown((555, 295), (155, 40), create_options_list(self.possible_mates_names, "upper"),
                                                    get_selected_option(selected_option, "upper"))
            except:
                pass
        
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
            "screens.offspring_predict.second_parent",
            object_id="#text_box_30_horizcenter",
        )

        self.selected_cat_elements["outsider_checkbox_label"] = pygame_gui.elements.UILabel(
            ui_scale(pygame.Rect((350, 163), (130, 30))),
            "screens.offspring_predict.show_outsiders",
            object_id=get_text_box_theme("#text_box_30"),
        )

        self.search_bar_image = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((345, 125), (118, 34))),
            pygame.image.load(
                "resources/images/search_bar.png").convert_alpha(),
            manager=MANAGER,
        )
        self.search_bar = pygame_gui.elements.UITextEntryLine(
            ui_scale(pygame.Rect((350, 129), (115, 27))),
            object_id="#search_entry_box",
            placeholder_text="general.genotype_search" if self.search_genotype else "general.name_search",
            manager=MANAGER,
        )

        self.search_toggle_checkbox = UICheckbox(
            (310, 129),
            check=self.search_genotype,
            tool_tip_text="screens.list.search_names_tooltip"
            if self.search_genotype
            else "screens.list.search_genotypes_tooltip",
            starting_height=1,
            manager=MANAGER,
        )

        self.outsider_toggle_checkbox = UICheckbox(
            (310, 160),
            check=self.include_outsiders,
            starting_height=1,
            manager=MANAGER,
        )
        
    def one_offspring(self):
        gene_config = get_config("genetics_config")
        gene_config.update(get_config("april_fools_genes"))
        par2geno = Genotype(gene_config, game_setting_get("ban problem genes"))
        if 'Y' in self.selected_cat.phenotype.sexgene:
            par2geno.Generator('fem')
        else:
            par2geno.Generator('masc')
        if self.selected_mate:
            new_cat = NewCatFactory.create_cat(parent1=self.selected_cat.ID, parent2=self.selected_mate.ID, status_dict={"rank": CatRank.WARRIOR}, moons=40)
        else:
            new_cat = NewCatFactory.create_cat(parent1 = self.selected_cat.ID, extrapar=par2geno, status = {"rank": CatRank.WARRIOR}, moons = 40)
        return new_cat
        
    def generate_offspring(self):
        
        self.predicted_offspring = []
                
        for i in range(10):
            self.predicted_offspring.append(self.one_offspring())
    
        index = 0
        indey = 0
    
        for offspring in self.predicted_offspring:
            self.predicted_offspring_elements["offspring" + str(index) + str(indey)] = UISpriteButton(
                ui_scale(pygame.Rect((105 + (index*120), 395 + indey), (100, 100))),
                pygame.transform.scale(
                    offspring.sprite, ui_scale_dimensions((100, 100))
                ),
                object_id="#offspring_predict_cat",
                tool_tip_text=offspring.create_genelist(),
            )

            if index < 4:
                index += 1
            else:
                index = 0
                indey = 115
            if offspring in Cat.all_cats_list:
                Cat.all_cats_list.remove(offspring)
            if offspring.ID in Cat.all_cats:
                del Cat.all_cats[offspring.ID]
    
    def exit_screen(self):
        self.back_button.kill()
        del self.back_button
        self.predict_button.kill()
        del self.predict_button

        self.search_bar_image.kill()
        del self.search_bar_image
        self.search_bar.kill()
        del self.search_bar
        self.search_toggle_checkbox.kill()
        del self.search_toggle_checkbox
        self.outsider_toggle_checkbox.kill()
        del self.outsider_toggle_checkbox
        self.previous_search_text = None
        
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

    def update_potential_mates_container(self, search_text = ""):
        self.possible_mates = [
            i
            for i in Cat.all_cats_list
            if i.is_potential_mate(self.selected_cat, for_love_interest=False, age_restriction=False, ignore_no_mates=True, outsider=True)
            and (i.status.group_ID == self.selected_cat.status.group_ID or self.include_outsiders)
            and "sterile" not in i.permanent_condition
            and (get_clan_setting("same sex birth") or xor('Y' in i.phenotype.sexgene, 'Y' in self.selected_cat.phenotype.sexgene))
        ]

        self.possible_mates = search_cats(search_text, self.possible_mates, self.search_genotype)
        self.possible_mates.sort(key=lambda x: str(x.name))

        self.possible_mates_names = ["None"]
        for cat in self.possible_mates:
            self.possible_mates_names.append(str(cat.name).lower())

        if hasattr(self, "mate_dropdown") and self.mate_dropdown:
            self.mate_dropdown.kill()
            del self.mate_dropdown
        self.mate_dropdown = create_dropdown((555, 295), (155, 40), create_options_list(self.possible_mates_names, "upper"),
                                             get_selected_option("None", "upper"))

    def on_use(self):
        super().on_use()
        # Only update the positions if the search text changes
        if self.search_bar.is_focused and self.search_bar.get_text() in ("general.name_search", "general.genotype_search"):
            self.search_bar.set_text("")
        if self.search_bar.get_text() != self.previous_search_text:
            self.update_potential_mates_container(self.search_bar.get_text().strip())
        self.previous_search_text = self.search_bar.get_text()
        
        
        

