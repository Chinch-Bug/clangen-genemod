import pygame_gui

class AllegiancesCat(pygame_gui.elements.UIButton):
    def set_cat_id(self, id):
        self.cat_id = id
    def return_cat_id(self):
        return self.cat_id