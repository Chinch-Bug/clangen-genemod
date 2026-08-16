import pygame
screen = pygame.display.set_mode((200, 400))
import ujson

spritesheet_list = ["sprites/patches_white_mostly.png",
                "sprites/patches_white_high.png",
                "sprites/patches_white_mid.png",
                "sprites/patches_white_little.png"]

lineart = pygame.image.load("sprites/lineart.png").convert_alpha()

def has_adjacent_pixels(surface, x, y):
    return (surface.get_at((x, y+1))[3] > 0 or surface.get_at((x, y-1))[3] or surface.get_at((x+1, y))[3] or surface.get_at((x-1, y))[3])

for sheet in spritesheet_list:
    current_sheet = pygame.image.load(sheet).convert_alpha()
    sheet_x = int(current_sheet.get_width()/200)
    sheet_y = int(current_sheet.get_height()/400)
    for spritey in range(sheet_y):
        for spritex in range(sheet_x):
            for y in range(400):
                for x in range(200):
                    if lineart.get_at((x, y))[3] > 0 and has_adjacent_pixels(current_sheet, int(spritex*200)+x, int(spritey*400)+y):
                        current_sheet.set_at((int(spritex*200)+x, int(spritey*400)+y), (255, 255, 255, 255))
    pygame.image.save(current_sheet, sheet)