from collections import deque
from random import choice, random, randint
from typing import List, Optional

import i18n
import pygame.transform
import pygame_gui.elements
from pygame_gui.core import UIContainer

from scripts.cat.cats import Cat
from scripts.cat_relations.relationship import (
    create_one_relationship
)
from scripts.cat.enums import (
    CatCompatibility,
    CatRank
)
from scripts.config import get_config
from scripts.clan_package.get_clan_cats import search_cats
from scripts.events_module.event_filters import get_personality_compatibility
from scripts.events_module.pregnancy.check_parents import check_if_can_have_kits
from scripts.game_structure import image_cache, game
from ..cat.sprites.load_sprites import sprites
from ..ui.elements.cat_list_display import UICatListDisplay
from ..ui.elements.modified_image import UIModifiedImage
from ..ui.elements.relation_display import UIRelationDisplay
from ..ui.elements.search_bar import UISearchBar
from ..ui.elements.checkbox import UICheckbox
from ..ui.elements.surface_image_button import UISurfaceImageButton
from ..ui.theme import get_text_box_theme
from ..events_module.text_adjust import shorten_text_to_fit
from ..ui.scale import ui_scale, ui_scale_dimensions
from .Screens import Screens
from ..game_structure.game.switches import switch_get_value, Switch
from ..game_structure.screen_settings import MANAGER
from ..ui.generate_box import get_box, BoxStyles
from ..ui.generate_button import get_button_dict, ButtonStyles
from ..ui.icon import Icon
from ..ui.windows.no_queen import NoQueensWindow


class QueenAdviceScreen(Screens):
    def __init__(self, name=None):
        super().__init__(name)
        self.all_cats_list = None
        self.back_button = None
        self.selected_cat0 = None
        self.selected_cat1 = None
        self.queens = deque()
        self.page = 1
        self.selected_cat_elements = {}
        self.previous_search_text = ""
        self.search_genotype = False

        self.elements = {}
        self.queen_elements = {}

    def handle_event(self, event):
        if event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            if (
                self.elements["search_bar"].text_entry.get_text()
                != self.previous_search_text
            ):
                self.update_search_cats(
                    self.elements["search_bar"].text_entry.get_text()
                )
                self.previous_search_text = self.elements[
                    "search_bar"
                ].text_entry.get_text()

        elif event.type == pygame_gui.UI_BUTTON_START_PRESS:
            self.mute_button_pressed(event)

            if event.ui_element == self.back_button:
                self.change_screen(game.last_screen_forupdate)

            elif event.ui_element == self.elements["search_toggle_checkbox"]:
                if event.ui_element.checked:
                    event.ui_element.set_tooltip("screens.list.search_genotypes_tooltip")
                    self.search_genotype = False
                else:
                    event.ui_element.set_tooltip("screens.list.search_names_tooltip")
                    self.search_genotype = True
                event.ui_element.toggle()
                self.elements["search_bar"].text_entry.placeholder_text = "general.genotype_search" if self.search_genotype else "general.name_search"
                self.elements["search_bar"].text_entry.set_text("")
                self.update_search_cats("")
            # QUEEN ARROWS
            elif event.ui_element == self.elements["last_queen"]:
                self.queens.rotate()
                self.update_queen_info()
            elif event.ui_element == self.elements["next_queen"]:
                self.queens.rotate(-1)
                self.update_queen_info()
            # CAT LIST ARROWS
            elif event.ui_element == self.elements["next_page"]:
                self.page += 1
                self.update_list_cats()
            elif event.ui_element == self.elements["prev_page"]:
                self.page -= 1
                self.update_list_cats()
            # REMOVE CAT
            elif event.ui_element == self.elements["remove_cat0"]:
                self.selected_cat0 = None
                self.selected_cat1 = None
                self.update_selected_cats()
            # IMPROVE BUTTON
            elif event.ui_element == self.elements["advise"]:
                game.patrolled.append(self.queens[0].ID)
                output, result = self.influence_cat(
                    self.queens[0],
                    self.selected_cat0,
                )
                game.queen_advice.append(self.selected_cat0.ID)
                game.queen_advice_outcomes.append(str(result))
                self.elements["results"].set_text(output)
                self.update_selected_cats()
                self.update_queen_info()
            # SABOTAGE BUTTON
            elif event.ui_element == self.elements["discourage"]:
                game.patrolled.append(self.queens[0].ID)
                output, result = self.influence_cat(
                    self.queens[0],
                    self.selected_cat0,
                    discourage=True
                )
                game.queen_advice.append(self.selected_cat0.ID)
                game.queen_advice_outcomes.append(str(result))
                self.elements["results"].set_text(output)
                self.update_selected_cats()
                self.update_queen_info()
            # PICK RANDOM CATS
            elif event.ui_element == self.elements["random_cat0"]:
                self.selected_cat0 = self.random_cat()
                self.selected_cat1 = None
                self.update_selected_cats()
            # SELECT A CAT
            elif (
                self.elements.get("cat_list")
                and event.ui_element in self.elements["cat_list"].cat_sprites.values()
            ):
                if event.ui_element.return_cat_object() is not self.selected_cat0:
                    self.selected_cat0 = event.ui_element.return_cat_object()
                    self.selected_cat1 = None
                    self.update_selected_cats()

        super().handle_event(event)

    def screen_switches(self):
        super().screen_switches()
        self.show_mute_buttons()

        # Gather the queens:
        self.queens.clear()
        for cat in Cat.all_cats_list:
            if (
                cat.status.rank.is_any_queen_rank()
                and cat.status.group_ID == (Cat.fetch_cat(switch_get_value(Switch.cat)).status.group_ID if switch_get_value(Switch.cat) and not Cat.fetch_cat(switch_get_value(Switch.cat)).dead else game.selected_clan.group_ID)
            ):
                if cat.ID == switch_get_value(Switch.cat):
                    self.queens.appendleft(cat)
                else:
                    self.queens.append(cat)

        interactable_elements = []

        self.back_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((25, 25), (105, 30))),
            "buttons.back",
            get_button_dict(ButtonStyles.SQUOVAL, (105, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
        )
        self.current_focus = self.back_button
        interactable_elements.append(self.back_button)

        # CONTAINERS
        self.elements["effects_container"] = UIContainer(
            ui_scale(pygame.Rect((0, 300), (270, 170))),
            manager=MANAGER,
            anchors={"centerx": "centerx"},
        )

        self.page = 1
        self.elements["cat_list_container"] = UIContainer(
            ui_scale(pygame.Rect((0, 480), (673, 200))),
            anchors={"centerx": "centerx"},
            manager=MANAGER,
        )

        # SEARCH BAR
        self.elements["search_bar"] = UISearchBar(
            (410, 0),
            container=self.elements["cat_list_container"],
            placeholder_text="general.genotype_search" if self.search_genotype else "general.name_search"
        )
        interactable_elements.append(self.elements["search_bar"].text_entry)

        self.elements["search_toggle_checkbox"] = UICheckbox(
            position=(0, 0),
            manager=MANAGER,
            starting_height=3,
            check=self.search_genotype,
            tool_tip_text="screens.list.search_names_tooltip"
            if self.search_genotype
            else "screens.list.search_genotypes_tooltip",
            container=self.elements["cat_list_container"],
            anchors={"left": "left", "left_target": self.elements["search_bar"].text_entry},
        )
        if not get_config("genetics_config.show_genotype"):
            self.elements["search_toggle_checkbox"].checked = False
            self.elements["search_toggle_checkbox"].disable()
        interactable_elements.append(self.elements["search_toggle_checkbox"])

        # CAT LIST
        self.elements["cat_list_bg"] = UIModifiedImage(
            ui_scale(pygame.Rect((24, 0), (625, 150))),
            get_box(BoxStyles.ROUNDED_BOX, (600, 150)),
            anchors={
                "top_target": self.elements["search_bar"],
            },
            container=self.elements["cat_list_container"],
            manager=MANAGER,
            starting_height=2,
        )

        self.elements["cat_list_bg"].disable()
        # LIST ARROWS
        self.elements["prev_page"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((0, 90), (34, 34))),
            Icon.ARROW_LEFT,
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
            container=self.elements["cat_list_container"],
            manager=MANAGER,
            starting_height=1,
        )
        self.elements["next_page"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((-10, 90), (34, 34))),
            Icon.ARROW_RIGHT,
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
            anchors={"left_target": self.elements["cat_list_bg"]},
            container=self.elements["cat_list_container"],
            manager=MANAGER,
            starting_height=1,
        )
        interactable_elements.extend(
            [self.elements["prev_page"], self.elements["next_page"]]
        )

        # RESULTS
        self.elements["result_frame"] = UIModifiedImage(
            ui_scale(pygame.Rect((0, 8), (270, 125))),
            get_box(BoxStyles.FRAME, (270, 125)),
            container=self.elements["effects_container"],
            manager=MANAGER,
        )

        # EFFECT BUTTONS
        self.elements["advise"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((20, 0), (105, 30))),
            "screens.queen.advise",
            get_button_dict(ButtonStyles.SQUOVAL, (105, 30)),
            object_id="@buttonstyles_squoval",
            container=self.elements["effects_container"],
            manager=MANAGER,
        )
        self.elements["discourage"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((20, 0), (105, 30))),
            "screens.queen.discourage",
            get_button_dict(ButtonStyles.SQUOVAL, (105, 30)),
            object_id="@buttonstyles_squoval",
            container=self.elements["effects_container"],
            anchors={"left_target": self.elements["advise"]},
            manager=MANAGER,
        )
        interactable_elements.extend(
            [self.elements["advise"], self.elements["discourage"]]
        )

        # RESULT TEXT
        self.elements["results"] = pygame_gui.elements.UITextBox(
            "",
            ui_scale(pygame.Rect((20, 40), (229, 80))),
            object_id=get_text_box_theme("#text_box_22_horizcenter_spacing_95"),
            container=self.elements["effects_container"],
            manager=MANAGER,
        )

        # QUEEN ARROWS
        self.elements["last_queen"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((290, 150), (34, 34))),
            Icon.ARROW_LEFT,
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
        )
        self.elements["next_queen"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((476, 150), (34, 34))),
            Icon.ARROW_RIGHT,
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
        )
        interactable_elements.extend(
            [self.elements["last_queen"], self.elements["next_queen"]]
        )

        # INDICATOR TEXT
        self.elements["select_cat0"] = pygame_gui.elements.UITextBox(
            "screens.queen.select_cat0",
            ui_scale(pygame.Rect((68, 385), (165, -1))),
            object_id=get_text_box_theme("#text_box_22_horizcenter_spacing_95"),
            manager=MANAGER,
        )

        # REMOVE AND RANDOM CAT
        self.elements["remove_cat0"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((68, 434), (127, 30))),
            "buttons.remove_cat",
            get_button_dict(ButtonStyles.SQUOVAL, (127, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
        )
        self.elements["remove_cat0"].disable()
        self.elements["random_cat0"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((198, 432), (34, 34))),
            Icon.DICE,
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
            manager=MANAGER,
            sound_id="dice_roll",
        )

        interactable_elements.extend(
            [
                self.elements["remove_cat0"],
                self.elements["random_cat0"],
            ]
        )

        self.add_to_map(interactable_elements)

        # UPDATE
        if self.queens:
            self.update_queen_info()
        else:
            NoQueensWindow()

    def random_cat(self) -> Optional[Cat]:
        """
        Return a random cat to influence
        """
        if self.selected_cat_list:
            random_list = [
                i for i in self.all_cats_list if i not in self.selected_cat_list
            ]
        else:
            random_list = self.all_cats_list

        if not random_list:
            return None

        return choice(random_list)

    def update_queen_info(self):
        """
        Update queen elements and corresponding information
        """
        # kill and reset
        for ele in self.queen_elements:
            self.queen_elements[ele].kill()
        self.queen_elements.clear()

        # grab the queen to use
        queen = self.queens[0]

        # queen can't be one of the selected cats
        if queen == self.selected_cat0:
            self.selected_cat0 = None
            self.update_selected_cats()

        # this is gonna be the "{name} can influence" yada yada above the queen sprite
        self.queen_elements["queen_status"] = pygame_gui.elements.UITextBox(
            "",
            ui_scale(pygame.Rect((0, 37), (229, 57))),
            anchors={"centerx": "centerx"},
            object_id=get_text_box_theme("#text_box_30_horizcenter_spacing_95"),
            manager=MANAGER,
        )

        # container for all the other elements
        self.queen_elements["container"] = UIContainer(
            ui_scale(pygame.Rect((0, 0), (150, 200))),
            anchors={
                "centerx": "centerx",
                "top_target": self.queen_elements["queen_status"],
            },
            manager=MANAGER,
        )
        # cat sprite stuff
        self.queen_elements["platform"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((0, 0), (240, 210))),
            pygame.transform.scale(
                sprites.get_platform(
                    biome=(
                        game.clan.override_biome
                        if game.clan.override_biome
                        else game.clan.biome
                    ),
                    season=game.clan.current_season,
                    show_nest=not queen.can_work(),
                    group=queen.status.group,
                ),
                ui_scale_dimensions((240, 210)),
            ),
            anchors={
                "centerx": "centerx",
                "top_target": self.queen_elements["queen_status"],
            },
            manager=MANAGER,
            starting_height=-1,
        )
        self.queen_elements["queen_image"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((0, 0), (150, 150))),
            pygame.transform.scale(queen.sprite, ui_scale_dimensions((150, 150))),
            container=self.queen_elements["container"],
        )

        # cat description
        text = (
            i18n.t(f"cat.personality.{queen.personality.trait}")
            + "\n"
            + queen.experience_level_string
        )
        self.queen_elements["details"] = pygame_gui.elements.UITextBox(
            text,
            ui_scale(pygame.Rect((0, 0), (150, -1))),
            object_id=get_text_box_theme("#text_box_22_horizcenter_spacing_95"),
            container=self.queen_elements["container"],
            anchors={"top_target": self.queen_elements["queen_image"]},
            manager=MANAGER,
            visible=queen.can_work(),  # doesn't appear if the cat isn't working
        )
        # disable buttons if queen can't work
        if not queen.can_work():
            self.elements["advise"].disable()
            self.elements["discourage"].disable()
        else:
            self.elements["advise"].enable()
            self.elements["discourage"].enable()

        # deactivate arrows if no other queens
        if len(self.queens) <= 1:
            self.elements["last_queen"].disable()
            self.elements["next_queen"].disable()

        self.update_queen_status_and_buttons()
        self.update_list_cats()

    def update_list_cats(self):
        """
        Updates the cat list display according to current selections
        """
        # make sure the list is up to date
        self._set_cat_list()
        if not self.elements.get("cat_list"):  # create the element in the first place
            self.elements["cat_list"] = UICatListDisplay(
                ui_scale(pygame.Rect(((35, 35), (600, 130)))),
                container=self.elements["cat_list_container"],
                starting_height=3,
                cat_list=self.all_cats_list,
                cats_displayed=20,
                x_px_between=5,
                y_px_between=5,
                columns=10,
                rows=2,
                current_page=1,
                next_button=self.elements["next_page"],
                prev_button=self.elements["prev_page"],
                tool_tip_name=True,
                manager=MANAGER,
            )
            self.add_to_map(self.elements["cat_list"].cat_sprites.values())

        self.update_search_cats(self.elements["search_bar"].text_entry.get_text())

    def _set_cat_list(self):
        """
        Updates self.all_cats_list according to chosen tab
        """
        self.all_cats_list = [
            i
            for i in Cat.all_cats_list
            if (i.ID != self.queens[0].ID) and i.status.group_ID == self.queens[0].status.group_ID and check_if_can_have_kits(i)
        ]

    def update_selected_cats(self):
        """
        Updates all elements connected to the selected cats.
        """
        # kill and reset all the elements
        for ele in self.selected_cat_elements:
            self.selected_cat_elements[ele].kill()
        self.selected_cat_elements = {}

        # show both "select a cat" text. these will be hidden later if need be.
        self.elements["select_cat0"].show()

        # check if the neg/pos tabs should be hidden or shown
        if not self.selected_cat0:
            self.elements["remove_cat0"].disable()

        # draw each cat block
        self._draw_cat_block(self.selected_cat0, (50, 80))
        if self.selected_cat1:
            self._draw_cat_block(self.selected_cat1, (550, 80))

        # update the queen info
        self.update_queen_status_and_buttons()

    def _draw_cat_block(self, cat: Cat, starting_pos: tuple):
        """
        Creates all the elements within a selected cat block
        """
        if not cat:
            return

        # first we grab an index for the cat, so that we can create unique elements using it
        selected_cats = self.selected_cat_list
        cat_num = selected_cats.index(cat)
        # we also find the other cat, so that we can get any important info we need from them
        other_cat = (
            [c for c in selected_cats if c != cat][0]
            if len(selected_cats) > 1
            else None
        )

        if cat_num == 0:
            # hide "select cat to influence" text, cus at this point we know a cat has been selected
            self.elements[f"select_cat{cat_num}"].hide()

            # enable random and remove
            self.elements[f"remove_cat{cat_num}"].enable()

        # we love a container
        self.selected_cat_elements[f"cat_container{cat_num}"] = UIContainer(
            ui_scale(pygame.Rect((starting_pos[0], starting_pos[1]), (200, 350))),
            manager=MANAGER,
        )

        # this is the background bubble for the relationship display
        self.selected_cat_elements[f"rel_bg{cat_num}"] = UIModifiedImage(
            ui_scale(pygame.Rect((0, 0), (140, 185))),
            get_box(BoxStyles.ROUNDED_BOX, (140, 185)),
            container=self.selected_cat_elements[f"cat_container{cat_num}"],
            anchors={"centerx": "centerx"},
            manager=MANAGER,
            visible=other_cat,
        )

        # and this is the tail of that bubble
        image = pygame.transform.scale(
            image_cache.load_image(
                "resources/images/thought_bubble_tail.png"
            ).convert_alpha(),
            ui_scale_dimensions((32, 52)),
        )
        if cat == self.queens[0]:  # tail has to flip if this is the right-side cat
            image = pygame.transform.flip(image, True, False)

        self.selected_cat_elements[f"bubble_tail{cat_num}"] = UIModifiedImage(
            ui_scale(pygame.Rect((0, 10), (32, 52))),
            image,
            container=self.selected_cat_elements[f"cat_container{cat_num}"],
            anchors={
                "centerx": "centerx",
                "top_target": self.selected_cat_elements[f"rel_bg{cat_num}"],
            },
            manager=MANAGER,
            visible=other_cat,
        )

        # if we have another cat, then we create the relationship display
        if other_cat:
            the_relationship = cat.relationships[other_cat.ID] if other_cat.ID in cat.relationships else create_one_relationship(cat, other_cat)

            self.selected_cat_elements[
                f"relation_display{cat_num}"
            ] = UIRelationDisplay(
                (2, 10),
                the_relationship,
                romance=True,
                container=self.selected_cat_elements[f"cat_container{cat_num}"],
                anchors={"centerx": "centerx"},
            )

        # cat stuff needs to be drawn differently for each cat due to changes in alignment and anchoring
        if cat == self.selected_cat0:
            self.selected_cat_elements[
                f"cat_image{cat_num}"
            ] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((0, 0), (100, 100))),
                pygame.transform.scale(cat.sprite, ui_scale_dimensions((100, 100))),
                container=self.selected_cat_elements[f"cat_container{cat_num}"],
                anchors={
                    "top_target": self.selected_cat_elements[f"bubble_tail{cat_num}"],
                },
                object_id="#offspring_predict_cat",
                manager=MANAGER,
            )
            self.selected_cat_elements[f"cat_image{cat_num}"].set_tooltip(cat.create_genelist())
            short_name = shorten_text_to_fit(str(cat.name), 45, 7)
            self.selected_cat_elements[
                f"cat_name{cat_num}"
            ] = pygame_gui.elements.UILabel(
                ui_scale(pygame.Rect((0, 0), (100, 30))),
                short_name,
                object_id=get_text_box_theme("#text_box_30_horizleft"),
                container=self.selected_cat_elements[f"cat_container{cat_num}"],
                anchors={
                    "top_target": self.selected_cat_elements[f"bubble_tail{cat_num}"],
                    "left_target": self.selected_cat_elements[f"cat_image{cat_num}"],
                },
                manager=MANAGER,
            )
            self.selected_cat_elements[
                f"cat_details{cat_num}"
            ] = pygame_gui.elements.UITextBox(
                self._get_cat_details(cat, other_cat),
                ui_scale(pygame.Rect((0, 0), (100, -1))),
                object_id=get_text_box_theme("#text_box_22_horizleft_spacing_95"),
                container=self.selected_cat_elements[f"cat_container{cat_num}"],
                anchors={
                    "top_target": self.selected_cat_elements[f"cat_name{cat_num}"],
                    "left_target": self.selected_cat_elements[f"cat_image{cat_num}"],
                },
                manager=MANAGER,
            )

        else:
            short_name = shorten_text_to_fit(str(cat.name), 45, 7)
            self.selected_cat_elements[
                f"cat_name{cat_num}"
            ] = pygame_gui.elements.UILabel(
                ui_scale(pygame.Rect((0, 0), (100, 30))),
                short_name,
                object_id=get_text_box_theme("#text_box_30_horizright"),
                container=self.selected_cat_elements[f"cat_container{cat_num}"],
                anchors={
                    "top_target": self.selected_cat_elements[f"bubble_tail{cat_num}"]
                },
                manager=MANAGER,
            )
            self.selected_cat_elements[
                f"cat_details{cat_num}"
            ] = pygame_gui.elements.UITextBox(
                self._get_cat_details(cat, other_cat),
                ui_scale(pygame.Rect((0, 0), (100, -1))),
                object_id=get_text_box_theme("#text_box_22_horizright_spacing_95"),
                container=self.selected_cat_elements[f"cat_container{cat_num}"],
                anchors={
                    "top_target": self.selected_cat_elements[f"cat_name{cat_num}"]
                },
                manager=MANAGER,
            )
            self.selected_cat_elements[
                f"cat_image{cat_num}"
            ] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((0, 0), (100, 100))),
                pygame.transform.scale(cat.sprite, ui_scale_dimensions((100, 100))),
                container=self.selected_cat_elements[f"cat_container{cat_num}"],
                anchors={
                    "top_target": self.selected_cat_elements[f"bubble_tail{cat_num}"],
                    "left_target": self.selected_cat_elements[f"cat_details{cat_num}"],
                },
                object_id="#offspring_predict_cat",
                manager=MANAGER,
            )
            self.selected_cat_elements[f"cat_image{cat_num}"].set_tooltip(cat.create_genelist())

    @staticmethod
    def _get_cat_details(cat, other_cat) -> str:
        """
        Returns a string with the cat's details: gender, relation to other cat, age, and trait
        """
        output = ""
        output += f"{cat.genderalign}<br>"

        # age
        output += f"{i18n.t('general.moons_age', count=cat.moons)}<br>"

        # trait
        output += f"{i18n.t(f'cat.personality.{cat.personality.trait}')}<br>"

        return output

    @property
    def selected_cat_list(self) -> List[Cat]:
        """Easy way to get a list of both selected cats"""
        output = []
        if self.selected_cat0:
            output.append(self.selected_cat0)
            if self.selected_cat0.mate and not self.selected_cat1:
                mates = [Cat.fetch_cat(m) for m in self.selected_cat0.mate if not Cat.fetch_cat(m).dead]
                if mates:
                    self.selected_cat1 = choice(mates)
        if self.selected_cat1:
            output.append(self.selected_cat1)

        return output

    def update_queen_status_and_buttons(self):
        """
        Updates the queen status text and the states of improve/sabotage buttons
        """
        if not self.queen_elements:
            # early return, sometimes this func is called when no queen elements are made
            # in which case, we should just skip all of it
            return

        # finding queen status string
        invalid_queen = False  # will be True if a queen can't work
        queen_name = self.queens[0].name
        if not self.queens[0].can_work():
            invalid_queen = True
            queen_status = i18n.t(
                "screens.queen.queen_cant_work", name=queen_name
            )
        elif self.queens[0].ID in game.patrolled:
            invalid_queen = True
            queen_status = i18n.t(
                "screens.queen.queen_already_worked", name=queen_name
            )
        else:
            queen_status = i18n.t(
                "screens.queen.queen_ready_to_work", name=queen_name
            )

        # check if influence pair has already been mediated
        invalid_pair = False
        if self.selected_cat0:
            for x in game.queen_advice:
                if self.selected_cat0.ID in x or x in self.selected_cat0.mate:
                    invalid_pair = True
                    queen_status = i18n.t("screens.queen.cat_already_advised")
                    break

        # set status text
        self.queen_elements["queen_status"].set_text(queen_status)

        # disable associated buttons if something is invalid
        if (invalid_queen or invalid_pair) or not (
            self.selected_cat0
        ):
            self.elements["advise"].disable()
            self.elements["discourage"].disable()
        else:
            self.elements["advise"].enable()
            self.elements["discourage"].enable()

    def update_search_cats(self, search_text):
        """Run this function when the search text changes, or when the screen is switched to."""
        current_listed_cats = []
        Cat.sort_cats(self.all_cats_list)

        search_text = search_text.strip()
        if search_text not in (""):
            current_listed_cats = search_cats(search_text, self.all_cats_list, self.search_genotype)
        else:
            current_listed_cats = self.all_cats_list.copy()

        self.remove_from_map(self.elements["cat_list"].cat_sprites.values())
        self.elements["cat_list"].update_display(self.page, current_listed_cats)
        self.add_to_map(self.elements["cat_list"].cat_sprites.values())

    def exit_screen(self):
        self.selected_cat0 = None
        self.selected_cat1 = None
        self.queens.clear()

        for ele in self.queen_elements:
            self.queen_elements[ele].kill()
        self.queen_elements = {}

        for ele in self.elements.values():
            ele.kill()
        self.elements.clear()

        for ele in self.selected_cat_elements:
            self.selected_cat_elements[ele].kill()
        self.selected_cat_elements = {}

        self.back_button.kill()
        del self.back_button

    def influence_cat(self, queen, cat, discourage=False):
        # Output string.
        output = ""

        influence = 0.5

        # Determine the chance of failure.
        if queen.experience_level == "untrained":
            chance = 5
            influence -= 0.4
        elif queen.experience_level == "learning":
            chance = 10
            influence -= 0.3
        elif queen.experience_level == "prepared":
            chance = 20
            influence -= 0.2
        elif queen.experience_level == "proficient":
            chance = 55
        elif queen.experience_level == "adept":
            chance = 70
        elif queen.experience_level == "masterful":
            chance = 100
        else:
            chance = 40
            influence -= 0.1

        # Cat's compatibility with queen also has an effect on success chance.
        if (
            get_personality_compatibility(cat, queen)
            == CatCompatibility.POSITIVE
        ):
            chance += 5
            influence += 0.2
        elif (
            get_personality_compatibility(cat, queen)
            == CatCompatibility.NEGATIVE
        ):
            chance -= 5
            influence -= 0.2

        failed = False
        # Determine chance to fail, turning sabotage into mediate and mediate into sabotage
        if not int(random() * chance):
            failed = True
            influence = min(1 - influence - round(random(), 2), 0)
            if discourage:
                output += i18n.t("screens.queen.discourage_failed")
                discourage = False
            else:
                output += i18n.t("screens.queen.advise_failed")
                discourage = True
        else:
            # EX gain on success
            if queen.status.rank == CatRank.QUEEN:
                exp_gain = randint(10, 24)

                gm_modifier = 1
                if game.clan and game.clan.game_mode == "expanded":
                    gm_modifier = 3

                if queen.experience_level == "proficient":
                    lvl_modifier = 1.25
                elif queen.experience_level == "adept":
                    lvl_modifier = 1.75
                elif queen.experience_level == "masterful":
                    lvl_modifier = 2
                else:
                    lvl_modifier = 1
                queen.add_experience(exp_gain / lvl_modifier / gm_modifier)

        if queen.status.rank == CatRank.QUEEN_APPRENTICE:
            queen.add_experience(max(randint(1, 6), 1))

        if influence > 0:
            output += i18n.t(
                f"screens.queen.output_{'decrease' if discourage else 'increase'}",
                name=cat.name,
            )
        elif not failed:
            if discourage:
                output += i18n.t("screens.queen.discourage_failed")
            else:
                output += i18n.t("screens.queen.advise_failed")
        if discourage:
            influence *= -1

        return output, influence
