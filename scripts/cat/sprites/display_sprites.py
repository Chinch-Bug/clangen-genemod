import logging
import traceback

import pygame

from scripts.cat.enums import CatAge, CatGroup
from scripts.cat.phenotype import Phenotype
from scripts.cat.sprites.load_sprites import sprites
from scripts.clan_package.settings import get_clan_setting
from scripts.config import get_config
from scripts.game_structure import image_cache
from scripts.game_structure.game import game_setting_get
from scripts.ui.scale import ui_scale_dimensions
from copy import deepcopy
from scripts.game_structure import game
from scripts.special_dates import SpecialDate, is_today
from random import randint

logger = logging.getLogger(__name__)

def get_current_season(season_override=None):
    if season_override:
        return season_override

    if game.clan:
        return game.clan.current_season

    return "Newleaf"

def generate_sprite(
    cat,
    life_state=None,
    scars_hidden=False,
    acc_hidden=False,
    always_living=False,
    disable_sick_sprite=False,
    hide_white=False,
    season_override=None,
) -> pygame.Surface:
    """
    Generates the sprite for a cat, with optional arguments that will override certain things.

    :param life_state: sets the age life_stage of the cat, overriding the one set by its age. Set to string.
    :param scars_hidden: If True, doesn't display the cat's scars. If False, display cat scars.
    :param acc_hidden: If True, hide the accessory. If false, show the accessory.
    :param always_living: If True, always show the cat with living lineart
    :param disable_sick_sprite: If true, never use the not_working lineart.
                    If false, use the cat.not_working() to determine the no_working art.
    """
    poses: list = sprites.POSE_DATA["poses"]
    sprite_poses = {x: str(poses.index(x)) for x in poses}

    if life_state is not None:
        age = life_state
    else:
        if game_setting_get("ageup dead") and cat.dead and cat.age in [CatAge.NEWBORN, CatAge.KITTEN, CatAge.ADOLESCENT]:
            age = CatAge.ADULT
        elif game_setting_get("youthful dead") and cat.dead and cat.age == CatAge.SENIOR:
            age = CatAge.ADULT
        else:
            age = cat.age


    if always_living:
        dead = False
    else:
        dead = cat.dead

    # setting the cat_sprite (bc this makes things much easier)
    cat_sprite = ""
    # sick sprites
    if (
        not disable_sick_sprite
        and cat.not_working()
        and age != CatAge.NEWBORN
        and get_config("cat_sprites.sick_sprites")
    ):
        if age in (CatAge.KITTEN, CatAge.ADOLESCENT):
            if age == CatAge.KITTEN:
                cat_sprite = sprite_poses["sick_kitten0"]
            elif age == CatAge.ADOLESCENT:
                cat_sprite = sprite_poses["sick_adolescent0"]
        elif age == CatAge.SENIOR:
            cat_sprite = sprite_poses["sick_senior0"]
        else:
            cat_sprite = sprite_poses["sick_adult0"]

    # paralyzed sprites
    elif cat.pelt.paralyzed and age != CatAge.NEWBORN:
        if age in (CatAge.KITTEN, CatAge.ADOLESCENT):
            cat_sprite = sprite_poses["para_young0"]
        else:
            if cat.pelt.length == 'long' or (cat.pelt.length == 'medium' and get_current_season(season_override) == 'Leaf-bare'):
                cat_sprite = sprite_poses["para_adult_long0"]
            else:
                cat_sprite = sprite_poses["para_adult_short0"]

    # default sprites
    else:
        if get_config("fun.all_cats_are_newborn"):
            cat_sprite = sprite_poses[cat.pelt.cat_sprites["newborn"]]
        else:
            if cat.pelt.length == 'medium' and get_current_season(season_override) == 'Leaf-bare':
                cat_sprite = sprite_poses[cat.pelt.cat_sprites[age].replace("short", "long")]
            else:
                cat_sprite = sprite_poses[cat.pelt.cat_sprites[age]]

    new_sprite = pygame.Surface(
        (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA
    )

    def draw_sprite(phenotype, cat_sprite, somatic = False):

        new_sprite = pygame.Surface(
            (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA
        )

        vitiligo = ['MOON', 'PHANTOM', 'POWDER', 'BLEACHED', 'VITILIGO', 'VITILIGOTWO', 'SMOKEY']
        
        if somatic:
            phenotype[phenotype.somatic["gene"]][0] = phenotype.somatic["allele"]
            phenotype.GeneSort()
            if phenotype.somatic["gene"] == 'sexgene' and len(phenotype.sexgene) > 1:
                phenotype.sexgene[1] = 'Y'
            phenotype.PhenotypeOutput(phenotype.white_pattern)

        stripecolourdict = {
                'rufousedapricot' : 'lowred',
                'mediumapricot' : 'rufousedcream',
                'lowapricot' : 'mediumcream',

                'rufousedivory-apricot' : 'lowhoney',
                'mediumivory-apricot' : 'rufousedivory',
                'lowivory-apricot' : 'mediumivory'
            }
        gensprite = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                
        def gen_sprite(phenotype, sprite_age, merle=False):
            phenotype.SpriteInfo(sprite_age)
            if(phenotype.merlepattern != None and not merle and 'rev' in phenotype.merlepattern[0]):
                old_silver = phenotype.silver
                phenotype.silver = ['i', 'i']
                phenotype.SpriteInfo(sprite_age)
                phenotype.silver = old_silver

            def create_coloursurface(basecolour, is_tabby=False):
                is_red = ('red' in basecolour or 'cream' in basecolour or 'honey' in basecolour or 'ivory' in basecolour or 'apricot' in basecolour)
                coloursurface = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                pointbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                if is_tabby:
                    pointbase.blit(sprites.sprites[stripecolourdict.get(basecolour[:-1], basecolour[:-1])+basecolour[-1]], (0, 0))
                    if phenotype.caramel == 'caramel' and not is_red:    
                        pointbase.blit(sprites.sprites['caramel0'], (0, 0))
                    
                    if "cm" in phenotype.pointgene or phenotype.pointgene[0] in ["cb", "cm"]:
                        pointbase.set_alpha(102) 
                    elif phenotype.pointgene == ["cb", "cb"] and sprite_age > 0:
                        pointbase.set_alpha(204)
                    elif phenotype.eumelanin[0] == "bl":
                        pointbase.set_alpha(25)
                    else:
                        pointbase.set_alpha(102)
                    
                    coloursurface.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                    coloursurface.blit(pointbase, (0, 0))
                else:
                    pointbase.blit(sprites.sprites[basecolour], (0, 0))
                    if phenotype.caramel == 'caramel' and not is_red:    
                        pointbase.blit(sprites.sprites['caramel0'], (0, 0))
        
                    if "cm" in phenotype.pointgene or phenotype.pointgene[0] in ["cb", "cm"]:
                        pointbase.set_alpha(102)
                        if 'fawn' in basecolour:
                            pointbase.set_alpha(0)

                        if 'blue' in basecolour:
                            if phenotype.pointgene[0] == "cm":
                                coloursurface.blit(sprites.sprites[basecolour.replace('blue', 'fawn')], (0, 0))
                                coloursurface.blit(pointbase, (0, 0))
                                pointbase.blit(sprites.sprites['lightbasecolours2'], (0, 0))
                                pointbase.set_alpha(50)
                            else:
                                coloursurface.blit(sprites.sprites['lightbasecolours1'], (0, 0))
                        else:
                            coloursurface.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                    elif phenotype.pointgene == ["cb", "cb"] and sprite_age > 0:
                        pointbase.set_alpha(204)
                        if 'lilac' in basecolour:
                            pointbase.set_alpha(140)
                        if 'fawn' in basecolour:
                            pointbase.set_alpha(50)
                        
                        if 'blue' in basecolour:
                            coloursurface.blit(sprites.sprites['lightbasecolours1'], (0, 0))
                        else:
                            coloursurface.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                    else: # mink or newborn sepia
                        if(phenotype.eumelanin[0] == "bl"):
                            pointbase.set_alpha(25)
                        else:
                            pointbase.set_alpha(102)
                        
                        if 'blue' in basecolour:
                            coloursurface.blit(sprites.sprites['lightbasecolours1'], (0, 0))
                        else:
                            coloursurface.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                    coloursurface.blit(pointbase, (0, 0))
                
                return coloursurface
                
            def create_stripes(stripecolour, whichbase, coloursurface=None, preset_pattern=None, special=None):
                stripebase = pygame.Surface(
                    (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                shading = pygame.Surface(
                    (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                
                if whichbase == "solid" and phenotype.ghosting[0] == 'Gh' and not (phenotype.silver[0] == 'I' and cat.pelt.length == 'long'):
                    return stripebase

                not_red = (
                    'red' not in stripecolour and 'cream' not in stripecolour and 'honey' not in stripecolour and 'ivory' not in stripecolour and 'apricot' not in stripecolour)
                is_dark_sunshine = (phenotype.wbtype not in [
                    "shaded", "chinchilla"] and phenotype.corin[0] == "sh" and not_red and phenotype.agouti[1] == "a"
                    and not (('ec' in phenotype.ext or (phenotype.ext[0] == 'ea' and ((sprite_age > 3 and phenotype.agouti[0] != "a") or sprite_age > 6))) and 'Eg' not in phenotype.ext))
                
                is_amber = not_red and phenotype.ext[0] == 'ea' and ((sprite_age > 11 and phenotype.agouti[0] != 'a') or (sprite_age > 35))
                is_older_amber = is_amber and ((sprite_age > 35 and phenotype.agouti[0] != 'a') or (sprite_age > 59))
                is_baby_amber = not_red and not is_amber and phenotype.ext[0] == 'ea' and ((sprite_age > 3 and phenotype.agouti[0] != "a") or sprite_age > 6)
                
                is_chinchilla = whichbase.rsplit("_", 1)[-1].isdigit() and int(whichbase.rsplit("_", 1)[-1]) > 14
                is_shaded = whichbase.rsplit("_", 1)[-1].isdigit() and not is_chinchilla and int(whichbase.rsplit("_", 1)[-1]) > 11

                pattern = []
                if preset_pattern:
                    for pat in preset_pattern:
                        pattern_sprite = pygame.Surface(
                            (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        pattern_sprite.blit(
                            sprites.sprites[pat + cat_sprite], (0, 0))
                        if pat != "agouti" and is_chinchilla or is_amber:
                            if phenotype.wbtype == "chinchilla" or is_older_amber:
                                pattern_sprite.set_alpha(15)
                            else:
                                pattern_sprite.set_alpha(125)
                        stripebase.blit(pattern_sprite, (0, 0))
                elif 'ghost' in phenotype.tabby:
                    ghoststripes = pygame.Surface(
                        (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    ghoststripes.blit(
                        sprites.sprites[phenotype.GetTabbySprite()[0] + cat_sprite], (0, 0))
                    ghoststripes.set_alpha(25)
                    stripebase.blit(ghoststripes, (0, 0))
                    pattern = phenotype.GetTabbySprite(special='ghost')
                    for pat in pattern:
                        stripebase.blit(
                            sprites.sprites[pat + cat_sprite], (0, 0))
                else:
                    pattern = phenotype.GetTabbySprite()
                    for pat in pattern:
                        pattern_sprite = pygame.Surface(
                            (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        pattern_sprite.blit(
                            sprites.sprites[pat + cat_sprite], (0, 0))
                        if (phenotype.bengtype == "mild bengal") and pat in ["braided", "brokenbraid"]:
                            stripebase2 = pygame.Surface(
                                (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            stripebase2.blit(
                                sprites.sprites[pat + cat_sprite], (0, 0))
                            stripebase2.set_alpha(127)
                            pattern_sprite.blit(stripebase2, (0, 0))
                        if pat != "agouti" and is_chinchilla or is_amber:
                            if phenotype.wbtype == "chinchilla" or is_older_amber:
                                pattern_sprite.set_alpha(15)
                            else:
                                pattern_sprite.set_alpha(125)
                        stripebase.blit(pattern_sprite, (0, 0))
                if (preset_pattern and preset_pattern[0] in ["marbled", "blotched"] or pattern and pattern[0] in ["marbled", "blotched"]) and phenotype.sheeted:
                    pattern_sprite = pygame.Surface(
                        (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    pattern_sprite.blit(
                        sprites.sprites["sheeted" + cat_sprite], (0, 0))
                    if is_chinchilla or is_amber:
                        if phenotype.wbtype == "chinchilla" or is_older_amber:
                            pattern_sprite.set_alpha(15)
                        else:
                            pattern_sprite.set_alpha(125)
                    stripebase.blit(pattern_sprite, (0, 0))

                if not_red and special != "no_shading" and not is_amber:
                    stripebase.blit(
                        sprites.sprites["tabbypads" + cat_sprite], (0, 0))

                charc = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                charc_shading = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                if (phenotype.agouti[0] == "Apb" and not_red and not is_amber):
                    if special != "no_shading":
                        charc_shading.blit(
                            sprites.sprites['lightbasecolours0'], (0, 0))
                        modifiers = {
                            "chinchilla": 2,
                            "shaded": 4,
                            "high": 8,
                            "medium": 8,
                            "low": 9
                        }
                        unders = sprites.sprites["Tabby_unders" + cat_sprite].copy()
                        unders.fill((255, 255, 255, 180), special_flags=pygame.BLEND_RGBA_MULT)
                        charc_shading.blit(unders, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
                        opacity = int(25 * modifiers.get(phenotype.banding, 5))
                        charc_shading.set_alpha(opacity)
                        charc.blit(charc_shading, (0, 0))
                    charc.blit(sprites.sprites['charcoal' + cat_sprite], (0, 0))
                    if not preset_pattern and pattern[0] not in ["normal barring", "ticked", "reduced barring", "reduced ticked"]:
                        charc.blit(sprites.sprites[pattern[0] + cat_sprite], (0, 0))

                    if (phenotype.agouti == ["Apb", "Apb"]):
                        charc.set_alpha(191)
                stripebase.blit(charc, (0, 0))

                if (is_chinchilla or is_shaded or is_amber or is_baby_amber):
                    golden_gradient = pygame.Surface(
                        (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    golden_gradient2 = pygame.Surface(
                        (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    golden_gradient2.blit(
                        sprites.sprites["goldengradient" + cat_sprite], (0, 0))

                    golden_gradient.blit(golden_gradient2, (0, 0))
                    if is_chinchilla and phenotype.wbtype != "chinchilla" and not is_dark_sunshine and not is_amber and not is_baby_amber:
                        golden_gradient2.set_alpha(100)
                        golden_gradient.blit(golden_gradient2, (0, 0))
                        golden_gradient2.set_alpha(255)
                    if is_shaded and not is_amber or is_baby_amber:
                        golden_gradient.blit(golden_gradient2, (0, 0))
                        if phenotype.corin[0] == "N":
                            golden_gradient2.set_alpha(100)
                            golden_gradient.blit(golden_gradient2, (0, 0))
                            golden_gradient2.set_alpha(255)
                        elif is_dark_sunshine:
                            golden_gradient2.set_alpha(255)
                            golden_gradient.blit(golden_gradient2, (0, 0))
                            golden_gradient.blit(golden_gradient2, (0, 0))

                    stripebase.blit(golden_gradient, (0, 0),
                                    special_flags=pygame.BLEND_RGBA_MIN)
                    golden_gradient = pygame.Surface(
                        (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    golden_gradient.fill((255, 255, 255))
                    stripebase.blit(golden_gradient, (0, 0),
                                    special_flags=pygame.BLEND_RGB_MAX)

                if not preset_pattern and len(pattern) > 2:
                    if phenotype.soktype == "full sokoke":
                        stripebase = create_stripes(
                            stripecolour, whichbase, coloursurface, preset_pattern=pattern[1:])
                        middle = create_stripes(
                            stripecolour, whichbase, coloursurface, special="no_shading", preset_pattern=pattern[:1])
                        middle.set_alpha(150)
                        stripebase.blit(middle, (0, 0))
                    elif phenotype.soktype == "mild fading":
                        stripebase = create_stripes(
                            stripecolour, whichbase, coloursurface, preset_pattern=pattern[1:])
                        middle = create_stripes(
                            stripecolour, whichbase, coloursurface, special="no_shading", preset_pattern=pattern[:1])
                        middle.set_alpha(204)
                        stripebase.blit(middle, (0, 0))
                elif preset_pattern and (len(preset_pattern) > 1 or special == "no_shading"):
                    return stripebase

                if not special and 'solid' not in whichbase:
                    if is_chinchilla or is_amber:
                        shading.blit(
                            sprites.sprites['chinchillashading' + cat_sprite], (0, 0))
                    elif is_shaded and not is_dark_sunshine or is_baby_amber:
                        shading.blit(
                            sprites.sprites['shadedshading' + cat_sprite], (0, 0))
                    else:
                        shading.blit(
                            sprites.sprites[phenotype.wbtype + 'shading' + cat_sprite], (0, 0))
                    if "silver" in whichbase:
                        shading.set_alpha(150)

                    stripebase.blit(shading, (0, 0))

                if coloursurface:
                    stripebase.blit(coloursurface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    stripebase.blit(coloursurface, (0, 0), special_flags=pygame.BLEND_RGB_MAX)
                elif 'basecolours' in stripecolour:
                    stripebase.blit(sprites.sprites[stripecolour], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    stripebase.blit(sprites.sprites[stripecolour], (0, 0), special_flags=pygame.BLEND_RGB_MAX)
                else:
                    surf = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    surf.blit(sprites.sprites[stripecolourdict.get(stripecolour[:-1], stripecolour[:-1])+stripecolour[-1]], (0, 0))
                    if phenotype.caramel == 'caramel' and not_red:
                        surf.blit(sprites.sprites['caramel0'], (0, 0))

                    stripebase.blit(surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    stripebase.blit(surf, (0, 0), special_flags=pygame.BLEND_RGB_MAX)

                return stripebase

            def get_tabby_base(base_string):
                basecolour, rufousing, wideband = base_string.rsplit("_", 2)
                rufousing = int(rufousing) if rufousing != "silver" else rufousing
                wideband = int(wideband)
                wb_blocks = ["low", "medium", "high", "shaded", "chinchilla"]
                wb_steps = [0, 5, 10, 13, 16]
                main_wb_block = next((n for n in range(4, -1, -1) if wideband >= wb_steps[n]))
                next_wb_block = next((n for n in range(5) if wideband <= wb_steps[n]))

                main_ruf_block = 3
                next_ruf_block = 3
                ruf_blocks = ["low", "medium", "rufoused", "silver"]
                ruf_steps = [0, 4, 8]
                if rufousing == "silver":
                    pass
                else:
                    main_ruf_block = next((n for n in range(2, -1, -1) if rufousing >= ruf_steps[n]))
                    next_ruf_block = next((n for n in range(3) if rufousing <= ruf_steps[n]))
                
                main_colour = sprites.sprites[basecolour + ruf_blocks[main_ruf_block] + wb_blocks[main_wb_block]+"0"].get_at((0, 0))
                final_colour = main_colour

                if main_ruf_block != next_ruf_block:
                    comparison_colour = sprites.sprites[basecolour + ruf_blocks[next_ruf_block] + wb_blocks[main_wb_block]+"0"].get_at((0, 0))
                    for i in range(3):
                        final_colour[i] += int((comparison_colour[i]-main_colour[i])/(ruf_steps[next_ruf_block]-ruf_steps[main_ruf_block])*(rufousing-ruf_steps[main_ruf_block]))

                if main_wb_block != next_wb_block:
                    comparison_colour = sprites.sprites[basecolour + ruf_blocks[main_ruf_block] + wb_blocks[next_wb_block]+"0"].get_at((0, 0))
                    for i in range(3):
                        final_colour[i] += int((comparison_colour[i]-main_colour[i])/(wb_steps[next_wb_block]-wb_steps[main_wb_block])*(wideband-wb_steps[main_wb_block]))
                
                layer = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                layer.fill(final_colour)
                return layer

            def tabby_base(whichcolour, whichbase, cat_unders, special=None):
                is_red = ('red' in whichcolour or 'cream' in whichcolour or 'honey' in whichcolour or 'ivory' in whichcolour or 'apricot' in whichcolour)
                whichmain = get_tabby_base(whichbase)
                if special !='copper' and sprite_age > 12 and (phenotype.silver[0] == 'I' and phenotype.corin[0] == 'fg' and (get_current_season(season_override) in ['Leaf-fall', 'Leaf-bare'] or 'sterile' in cat.permanent_condition)):
                    sunshine = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    
                    colours = phenotype.FindRed(phenotype, sprite_age, special='low')
                    sunshine = make_cat(sunshine, colours[0], colours[1], [colours[2], colours[3]], special='copper')

                    sunshine.set_alpha(150)
                    whichmain.blit(sunshine, (0, 0))

                unders = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                unders.blit(sprites.sprites["Tabby_unders" + cat_sprite], (0, 0))
                if phenotype.corin[0] != "N":
                    for p in ["left front", "right front", "left back", "right back"]:
                        unders.blit(sprites.sprites[p + " toes" + cat_sprite], (0, 0))
                unders.blit(sprites.sprites[cat_unders[0]], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                unders.set_alpha(int(cat_unders[1] * 2.55))
                whichmain.blit(unders, (0, 0))
                    
                
                if phenotype.caramel == 'caramel' and not is_red:    
                    whichmain.blit(sprites.sprites['caramel0'], (0, 0))

                if phenotype.pangere:
                    modifiers = {
                        "chinchilla" : 9,
                        "shaded" : 8,
                        "high" : 7,
                        "medium" : 6,
                        "low" : 5
                    }
                    opacity = int(25 * (modifiers.get(phenotype.banding, 5)))
                    pangere = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    pangere.blit(sprites.sprites[phenotype.pangere + cat_sprite], (0, 0))
                    pangere.set_alpha(opacity)
                    whichmain.blit(pangere, (0, 0))
                
                if phenotype.rednose and not phenotype.tabtype:
                    modifiers = {
                        "chinchilla" : 1,
                        "shaded" : 3,
                        "high" : 7,
                        "medium" : 7,
                        "low" : 7
                    }
                    opacity = int(12 * (modifiers.get(phenotype.banding, 5)))
                    rednose = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    rednose.blit(sprites.sprites["rednose" + cat_sprite], (0, 0))
                    nose_colour = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    stripecolour = phenotype.FindRed(phenotype, sprite_age, "red")[0]
                    nose_colour.blit(sprites.sprites[stripecolourdict.get(stripecolour[:-1], stripecolour[:-1])+stripecolour[-1]], (0, 0))
                    rednose.blit(nose_colour, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    rednose.set_alpha(opacity)
                    whichmain.blit(rednose, (0, 0))
                
                return whichmain
        
            def add_stripes(main_layer, stripe_colour, whichbase, coloursurface=None):
                stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                is_red = ('red' in stripe_colour or 'cream' in stripe_colour or 'honey' in stripe_colour or 'ivory' in stripe_colour or 'apricot' in stripe_colour)
                if not is_red and (phenotype.ext[0] == 'ea' and ((sprite_age > 11 and phenotype.agouti[0] != "a") or (sprite_age > 35 and phenotype.agouti[0] == "a"))):
                    if phenotype.pointgene[0] != "C" and phenotype.pointgene[0] in ["cm", "cb"] and (phenotype.pointgene[1] != "cs" or sprite_age > 0):
                        base_c = phenotype.FindRed(phenotype, sprite_age)[0]
                        stripebase = create_stripes(base_c, whichbase, coloursurface=create_coloursurface(base_c, True))
                    elif "lightbasecolours" not in stripe_colour:
                        stripebase = create_stripes(phenotype.FindRed(phenotype, sprite_age)[0], whichbase)
                    stripebase.blit(create_stripes(stripe_colour, whichbase, coloursurface=coloursurface), (0, 0))
                elif 'ec' in phenotype.ext and 'Eg' not in phenotype.ext and not is_red:
                    stripebase = create_stripes(stripe_colour, whichbase, coloursurface=coloursurface)
                    stripebase.set_alpha(200)
                    main_layer.blit(stripebase, (0, 0))
                    stripebase = create_stripes(
                        stripe_colour, whichbase, coloursurface=coloursurface, preset_pattern=['agouti'])
                else:
                    stripebase.blit(create_stripes(
                        stripe_colour, whichbase, coloursurface=coloursurface), (0, 0))

                main_layer.blit(stripebase, (0, 0))

                return main_layer

            def apply_smoke_effects(whichmain):
                white = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                white.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                smokeUnders = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                smokeUnders.blit(sprites.sprites["ghost" + cat_sprite], (0, 0))
                white.set_alpha(10)
                smokeLayer = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                smokeLayer.blit(white, (0, 0))
                if(phenotype.ext[0] == 'Eg' and phenotype.agouti[0] != 'a'):
                    grizzle = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    grizzle.blit(sprites.sprites['satin0'], (0, 0))
                    grizzle.blit(sprites.sprites['grizzle' + cat_sprite], (0, 0))
                    grizzle.set_alpha(175)
                    whichmain.blit(grizzle, (0, 0))
                if phenotype.ghosting[0] == 'Gh' and not (phenotype.silver[0] == 'I' and cat.pelt.length == 'long'):
                    if(sprite_age < 4):
                        smokeUnders.set_alpha(150)
                    
                    whichmain.blit(smokeUnders, (0, 0))
                smokeUnders.set_alpha(255)
                if (phenotype.silver[0] == 'I' or phenotype.karp[1] == "K"):
                    if cat.pelt.length != 'long':
                        smokeUnders.set_alpha(100)
                    elif phenotype.wbtype == 'low':
                        smokeUnders.set_alpha(150)
                    
                    whichmain.blit(smokeUnders, (0, 0))
                    if phenotype.wbtype == 'low' and cat.pelt.length == 'long':
                        smokeLayer.set_alpha(75)
                    elif phenotype.wbtype == 'low' or cat.pelt.length == 'long':
                        smokeLayer.set_alpha(150)
                    else:
                        smokeLayer.set_alpha(200)
                    whichmain.blit(smokeLayer, (0, 0))
                smokeUnders.set_alpha(20)
                if ('smoke' in phenotype.silvergold and 14 > phenotype.wideband > 9):
                    smokeLayer.set_alpha(255)
                    if cat.pelt.length != 'long':
                        smokeLayer.blit(smokeUnders, (0, 0))
                    if phenotype.wbtype == 'high':
                        smokeLayer.set_alpha(100)
                    elif cat.pelt.length == 'long':
                        smokeLayer.set_alpha(200)                    
                    whichmain.blit(smokeLayer, (0, 0))
                
                return whichmain

            def add_pads(sprite, whichcolour, is_red=False):
                pads = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                pads.blit(sprites.sprites['pads' + cat_sprite], (0, 0))

                pad_dict = {
                    'red' : 0,
                    'whit' : 1,
                    'black' : 3,
                    'chocolate' : 4,
                    'cinnamon' : 5,
                    'blue' : 6,
                    'lilac' : 7,
                    'fawn' : 8,
                    'dove' : 9,
                    'champagne' : 10,
                    'buff' : 11,
                    'platinum' : 12,
                    'lavender' : 13,
                    'beige' : 14
                }

                if(phenotype.white[0] == 'W' or phenotype.pointgene[0] == 'c' or phenotype.white_pattern == ['full white'] or whichcolour == "white"):
                    pads.blit(sprites.sprites['padcolours1'], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                elif ('amber' not in phenotype.colour or phenotype.agouti[0] != 'a') and ('russet' in phenotype.colour or 'carnelian' in phenotype.colour or is_red):
                    pads.blit(sprites.sprites['padcolours0'], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                elif 'amber' in phenotype.colour:
                    phenotype.SpriteInfo(10)
                    whichcolour = phenotype.maincolour
                    pads.blit(sprites.sprites['padcolours' + str(pad_dict.get(whichcolour[:-1], 0))], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    phenotype.SpriteInfo(sprite_age)
                else:
                    pads.blit(sprites.sprites['padcolours' + str(pad_dict.get(whichcolour[:-1]))], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                sprite.blit(pads, (0, 0))

                return sprite

            def add_nose(sprite, maincolour, spritecolour, isred):
                nose = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                nose.blit(sprites.sprites['nose' + cat_sprite], (0, 0))

                nose_dict = {
                    'red' : 0,
                    'whit' : 1,
                    'tabby' : 2,
                    'black' : 3,
                    'chocolate' : 4,
                    'cinnamon' : 5,
                    'blue' : 6,
                    'lilac' : 7,
                    'fawn' : 8,
                    'dove' : 9,
                    'champagne' : 10,
                    'buff' : 11,
                    'platinum' : 12,
                    'lavender' : 13,
                    'beige' : 14
                }

                if maincolour == "white":
                    nose.blit(sprites.sprites['nosecolours1'], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                elif ('amber' in phenotype.colour and phenotype.agouti[0] != 'a' and sprite_age > 11) or isred:
                    nose.blit(sprites.sprites['nosecolours0'], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                elif 'amber' in phenotype.colour:
                    phenotype.SpriteInfo(10)
                    nose.blit(sprites.sprites['nosecolours' + str(nose_dict.get(phenotype.maincolour[:-1]))], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    phenotype.SpriteInfo(sprite_age)
                elif maincolour != spritecolour and "masked" not in phenotype.silvergold and "charcoal" not in phenotype.tabtype and not phenotype.blacknose:
                    if phenotype.corin[0] != "N" and not (phenotype.corin[0] == "sh" and phenotype.agouti[1] == "a"):
                        nose.blit(sprites.sprites['nosecolours0'], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    else:
                        nose.blit(sprites.sprites['nosecolours2'], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    nose.set_alpha(200)
                else:
                    nose.blit(sprites.sprites['nosecolours' + str(nose_dict.get(maincolour[:-1]))], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                sprite.blit(nose, (0, 0))
                return sprite

            def make_cat(whichmain, whichcolour, whichbase, cat_unders, special=None):
                is_red = ('red' in whichcolour or 'cream' in whichcolour or 'honey' in whichcolour or 'ivory' in whichcolour or 'apricot' in whichcolour)
                is_white = (phenotype.white[0] == 'W' or phenotype.pointgene[0] == 'c' or whichbase == 'white' or phenotype.white_pattern == ['full white'])

                if is_white:
                    if phenotype.white[0] == "W" and phenotype.colour == "black":
                        whichmain.blit(sprites.sprites[f'black{phenotype.fur_shade}'], (0, 0))
                    else:
                        whichmain.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                elif(whichcolour != whichbase and special != 'masked silver'):
                    if(phenotype.pointgene[0] == "C"):
                        whichmain = tabby_base(whichcolour, whichbase, cat_unders, special)

                        whichmain = add_stripes(whichmain, whichcolour, whichbase)
                    else:
                        #create base
                        colourbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        if("black" in whichcolour and phenotype.pointgene[0] == "cm"):
                            colourbase.blit(get_tabby_base(whichbase.replace("black", "cinnamon")), (0, 0))
                        else:
                            colourbase = tabby_base(whichcolour, whichbase, cat_unders, special)

                            if((phenotype.pointgene == ["cb", "cb"] and 'cinnamon' not in whichcolour and sprite_age > 0) or (((("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm") and sprite_age > 0) or phenotype.pointgene == ["cb", "cb"]) and get_current_season(season_override) == 'Leaf-bare')):
                                colourbase.set_alpha(100)
                            elif((("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm") and sprite_age > 0) or phenotype.pointgene == ["cb", "cb"] or ((sprite_age > 0 or ("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm")) and get_current_season(season_override) == 'Leaf-bare')):
                                colourbase.set_alpha(50)
                            elif(("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm")):
                                colourbase.set_alpha(15)
                            else:
                                colourbase.set_alpha(0)
                        
                        whichmain.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                        whichmain.blit(colourbase, (0, 0))

                        #add base stripes
                        if("cm" in phenotype.pointgene):
                            if("black" in whichcolour and phenotype.pointgene[0] == "cm"):
                                whichmain = add_stripes(whichmain, 'lightbasecolours2', whichbase)
                            else:
                                if(phenotype.pointgene[0] in ["cb", "cm"]):
                                    if("black" in whichcolour and sprite_age > 0):
                                        whichmain = add_stripes(whichmain, 'lightbasecolours2', whichbase)
                                    elif((("chocolate" in whichcolour or "cinnamon" in whichcolour) and sprite_age > 0) or "black" in whichcolour):
                                        whichmain = add_stripes(whichmain, 'lightbasecolours1', whichbase)
                                    elif("cinnamon" in whichcolour or "chocolate" in whichcolour):
                                        whichmain = add_stripes(whichmain, 'lightbasecolours0', whichbase)
                                    else:
                                        whichmain = add_stripes(whichmain, whichcolour, whichbase, coloursurface=create_coloursurface(whichcolour, True))
                                elif("black" in whichcolour and sprite_age > 0):
                                    stripecolour = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                                    stripecolour = add_stripes(stripecolour, 'lightbasecolours1', whichbase)
                                    stripecolour.set_alpha(102)
                                    whichmain.blit(stripecolour, (0, 0))
                        
                        else:
                            if("black" in whichcolour and phenotype.pointgene == ["cb", "cb"] and sprite_age > 0):
                                whichmain = add_stripes(whichmain, 'lightbasecolours3', whichbase)
                            elif((("chocolate" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("black" in whichcolour and "cb" in phenotype.pointgene)) and sprite_age > 0 or ("black" in whichcolour and phenotype.pointgene == ["cb", "cb"])):
                                whichmain = add_stripes(whichmain, 'lightbasecolours2', whichbase)
                            elif((("cinnamon" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("chocolate" in whichcolour and "cb" in phenotype.pointgene) or ("black" in whichbase and phenotype.pointgene == ["cs", "cs"])) and sprite_age > 0 or (("chocolate" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("black" in whichcolour and "cb" in phenotype.pointgene))):
                                whichmain = add_stripes(whichmain, 'lightbasecolours1', whichbase)

                            elif phenotype.pointgene == ["cb", "cb"] or ("cb" in phenotype.pointgene and sprite_age > 0):
                                whichmain = add_stripes(whichmain, whichcolour, whichbase, coloursurface=create_coloursurface(whichcolour, True))

                        #mask base
                        colourbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        if("black" in whichcolour and phenotype.pointgene[0] == "cm"):
                            colourbase2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            colourbase.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                            colourbase2.blit(get_tabby_base(whichbase.replace("black", "cinnamon")), (0, 0))
                            colourbase2.set_alpha(150)
                            colourbase.blit(colourbase2, (0, 0))
                        else:
                            colourbase = tabby_base(whichcolour, whichbase, cat_unders, special)
                        pointbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        pointbase2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        pointbase2.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                        if("cm" in phenotype.pointgene):
                            if("black" in whichcolour and phenotype.pointgene[0] == "cm"):
                                pointbase.blit(colourbase, (0, 0))
                            else:
                                if((("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm") and sprite_age > 0) or ((sprite_age > 0 or ("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm")) and get_current_season(season_override) == "Leaf-bare")):
                                    colourbase.set_alpha(180)
                                elif(sprite_age > 0 or ("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm")):
                                    colourbase.set_alpha(50)
                                else:
                                    colourbase.set_alpha(0)

                                pointbase2.blit(colourbase, (0, 0))
                                
                                if phenotype.pointgene[0] == "cm":
                                    if(get_current_season(season_override) == "Greenleaf"):
                                        pointbase.blit(sprites.sprites['mochal' + cat_sprite], (0, 0))
                                        pointbase.blit(pointbase2, (0, 0), 
                                                    special_flags=pygame.BLEND_RGBA_MULT)
                                    elif(get_current_season(season_override) == "Leaf-bare"):
                                        pointbase.blit(sprites.sprites['mochad' + cat_sprite], (0, 0))
                                        pointbase.blit(pointbase2, (0, 0), 
                                                    special_flags=pygame.BLEND_RGBA_MULT)
                                    else:
                                        pointbase.blit(sprites.sprites['mocham' + cat_sprite], (0, 0))
                                        pointbase.blit(pointbase2, (0, 0), 
                                                    special_flags=pygame.BLEND_RGBA_MULT)
                                else:                 
                                    if(get_current_season(season_override) == "Greenleaf"):
                                        pointbase.blit(sprites.sprites['pointsl' + cat_sprite], (0, 0))
                                        pointbase.blit(pointbase2, (0, 0), 
                                                    special_flags=pygame.BLEND_RGBA_MULT)
                                    elif(get_current_season(season_override) == "Leaf-bare"):
                                        pointbase.blit(sprites.sprites['pointsd' + cat_sprite], (0, 0))
                                        pointbase.blit(pointbase2, (0, 0), 
                                                    special_flags=pygame.BLEND_RGBA_MULT)
                                    else:
                                        pointbase.blit(sprites.sprites['pointsm' + cat_sprite], (0, 0))
                                        pointbase.blit(pointbase2, (0, 0), 
                                                    special_flags=pygame.BLEND_RGBA_MULT)   
                                
                        else:
                            if((phenotype.pointgene == ["cb", "cb"] and sprite_age > 0) or ("cb" in phenotype.pointgene and sprite_age > 0 and get_current_season(season_override) == 'Leaf-bare')):
                                colourbase.set_alpha(180)
                            elif(("cb" in phenotype.pointgene and sprite_age > 0) or phenotype.pointgene == ["cb", "cb"] or ((sprite_age > 0 or "cb" in phenotype.pointgene) and get_current_season(season_override) == 'Leaf-bare')):
                                colourbase.set_alpha(120)
                            elif(sprite_age > 0 or "cb" in phenotype.pointgene):
                                colourbase.set_alpha(50)
                            else:
                                colourbase.set_alpha(15)
                            
                            pointbase2.blit(colourbase, (0, 0))

                            if(get_current_season(season_override) == "Greenleaf"):
                                pointbase.blit(sprites.sprites['pointsl' + cat_sprite], (0, 0))
                                pointbase.blit(pointbase2, (0, 0), 
                                            special_flags=pygame.BLEND_RGBA_MULT)
                            elif(get_current_season(season_override) == "Leaf-bare"):
                                pointbase.blit(sprites.sprites['pointsd' + cat_sprite], (0, 0))
                                pointbase.blit(pointbase2, (0, 0), 
                                            special_flags=pygame.BLEND_RGBA_MULT)
                            else:
                                pointbase.blit(sprites.sprites['pointsm' + cat_sprite], (0, 0))
                                pointbase.blit(pointbase2, (0, 0), 
                                            special_flags=pygame.BLEND_RGBA_MULT)
                        
                            
                        #add mask stripes
                    
                        stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        stripebase2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)

                        if("black" in whichcolour and phenotype.pointgene[0] == "cm"):
                            colour = whichcolour.replace("black", "cinnamon")
                        else:
                            colour = whichcolour
                
                        stripebase = add_stripes(stripebase, colour, whichbase)

                        
                        if phenotype.pointgene[0] == "cm":
                            if(get_current_season(season_override) == "Greenleaf"):
                                stripebase2.blit(sprites.sprites['mochal' + cat_sprite], (0, 0))
                                stripebase2.blit(stripebase, (0, 0), 
                                            special_flags=pygame.BLEND_RGBA_MULT)
                            elif(get_current_season(season_override) == "Leaf-bare"):
                                stripebase2.blit(sprites.sprites['mochad' + cat_sprite], (0, 0))
                                stripebase2.blit(stripebase, (0, 0), 
                                            special_flags=pygame.BLEND_RGBA_MULT)
                            else:
                                stripebase2.blit(sprites.sprites['mocham' + cat_sprite], (0, 0))
                                stripebase2.blit(stripebase, (0, 0), 
                                            special_flags=pygame.BLEND_RGBA_MULT)
                        else:
                            if(get_current_season(season_override) == "Greenleaf"):
                                stripebase2.blit(sprites.sprites['pointsl' + cat_sprite], (0, 0))
                                stripebase2.blit(stripebase, (0, 0), 
                                            special_flags=pygame.BLEND_RGBA_MULT)
                            elif(get_current_season(season_override) == "Leaf-bare"):
                                stripebase2.blit(sprites.sprites['pointsd' + cat_sprite], (0, 0))
                                stripebase2.blit(stripebase, (0, 0), 
                                            special_flags=pygame.BLEND_RGBA_MULT)
                            else:
                                stripebase2.blit(sprites.sprites['pointsm' + cat_sprite], (0, 0))
                                stripebase2.blit(stripebase, (0, 0), 
                                            special_flags=pygame.BLEND_RGBA_MULT)

                        pointbase.blit(stripebase2, (0, 0))

                        whichmain.blit(pointbase, (0, 0))

                else:
                    if(phenotype.pointgene[0] == "C"):
                        whichmain.blit(sprites.sprites[stripecolourdict.get(whichcolour[:-1], whichcolour[:-1])+whichcolour[-1]], (0, 0))
                        if phenotype.caramel == 'caramel' and not is_red:    
                            whichmain.blit(sprites.sprites['caramel0'], (0, 0))
                            
                        whichmain = apply_smoke_effects(whichmain)

                        stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        stripebase.blit(create_stripes(whichcolour, "solid", special="no_shading"), (0, 0))
                        whichmain.blit(stripebase, (0, 0))
                    elif("cm" in phenotype.pointgene):
                        colour = None
                        coloursurface = None
                        if("black" in whichcolour and phenotype.pointgene[0] == "cm"):
                            whichmain.blit(sprites.sprites['lightbasecolours2'], (0, 0)) 
                            overlay = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            overlay.blit(sprites.sprites['cinnamon3'], (0, 0)) 
                            overlay.set_alpha(10)
                            whichmain.blit(overlay, (0, 0))
                            whichmain = apply_smoke_effects(whichmain)

                            stripebase = create_stripes("cinnamon2", 'solid', special="no_shading")
                            stripebase.set_alpha(10)

                            whichmain.blit(stripebase, (0, 0))
                        else:
                            stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                                
                            if("cb" in phenotype.pointgene or phenotype.pointgene[0] == "cm"):
                                if("black" in whichcolour and sprite_age > 0):
                                    whichmain.blit(sprites.sprites['lightbasecolours2'], (0, 0))
                                    colour = 'lightbasecolours2'
                                    whichmain = apply_smoke_effects(whichmain)

                                elif(("chocolate" in whichcolour and sprite_age > 0) or "black" in whichcolour):
                                    whichmain.blit(sprites.sprites['lightbasecolours1'], (0, 0))
                                    colour = 'lightbasecolours1'
                                    whichmain = apply_smoke_effects(whichmain)
                                elif("cinnamon" in whichcolour or "chocolate" in whichcolour):
                                    whichmain.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                                    colour = 'lightbasecolours0'
                                else:
                                    coloursurface = create_coloursurface(whichcolour, False)
                                    whichmain.blit(coloursurface, (0, 0))
                                    colour = whichcolour
                                    
                                    whichmain = apply_smoke_effects(whichmain)
                            else:
                                if("black" in whichcolour and sprite_age > 0):
                                    whichmain.blit(sprites.sprites['lightbasecolours1'], (0, 0))
                                    colour = 'lightbasecolours1'
                                    whichmain = apply_smoke_effects(whichmain)
                                else:
                                    whichmain.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                                    colour = 'lightbasecolours0'
                            
                            
                            stripebase = create_stripes(colour, 'solid', special="no_shading", coloursurface=coloursurface)
                            whichmain.blit(stripebase, (0, 0))

                            pointbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            pointbase2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            
                            pointbase2.blit(sprites.sprites[whichcolour], (0, 0))
                            if phenotype.caramel == 'caramel' and not is_red:    
                                pointbase2.blit(sprites.sprites['caramel0'], (0, 0))
                        
                            whichmain = apply_smoke_effects(whichmain)

                            
                            stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            stripebase.blit(create_stripes(whichcolour, 'solid', special="no_shading"), (0, 0))

                            pointbase2.blit(stripebase, (0, 0))

                            if phenotype.pointgene[0] == "cm":
                                if (get_current_season(season_override) == "Greenleaf"):
                                    pointbase.blit(
                                        sprites.sprites['mochal' + cat_sprite], (0, 0))
                                    pointbase.blit(pointbase2, (0, 0),
                                                special_flags=pygame.BLEND_RGBA_MULT)
                                elif (get_current_season(season_override) == "Leaf-bare"):
                                    pointbase.blit(
                                        sprites.sprites['mochad' + cat_sprite], (0, 0))
                                    pointbase.blit(pointbase2, (0, 0),
                                                special_flags=pygame.BLEND_RGBA_MULT)
                                else:
                                    pointbase.blit(
                                        sprites.sprites['mocham' + cat_sprite], (0, 0))
                                    pointbase.blit(pointbase2, (0, 0),
                                                special_flags=pygame.BLEND_RGBA_MULT)
                            else:                 
                                if(get_current_season(season_override) == "Greenleaf"):
                                    pointbase.blit(sprites.sprites['pointsl' + cat_sprite], (0, 0))
                                    pointbase.blit(pointbase2, (0, 0), 
                                                special_flags=pygame.BLEND_RGBA_MULT)
                                elif(get_current_season(season_override) == "Leaf-bare"):
                                    pointbase.blit(sprites.sprites['pointsd' + cat_sprite], (0, 0))
                                    pointbase.blit(pointbase2, (0, 0), 
                                                special_flags=pygame.BLEND_RGBA_MULT)
                                else:
                                    pointbase.blit(sprites.sprites['pointsm' + cat_sprite], (0, 0))
                                    pointbase.blit(pointbase2, (0, 0), 
                                                special_flags=pygame.BLEND_RGBA_MULT)   
                        
                            # if phenotype.pointgene[0] == "cm" and 'blue' in whichcolour:
                            #     pointbase.set_alpha(102)

                            whichmain.blit(pointbase, (0, 0))        
                            
                    else:
                        colour = whichcolour
                        coloursurface = None
                        stripebase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        if("black" in whichcolour and phenotype.pointgene == ["cb", "cb"] and sprite_age > 0):
                            whichmain.blit(sprites.sprites['lightbasecolours3'], (0, 0)) 
                            colour = 'lightbasecolours3'
                            whichmain = apply_smoke_effects(whichmain)
                        elif((("chocolate" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("black" in whichcolour and "cb" in phenotype.pointgene)) and sprite_age > 0) or ("black" in whichcolour and phenotype.pointgene == ["cb", "cb"]):
                            whichmain.blit(sprites.sprites['lightbasecolours2'], (0, 0)) 
                            colour = 'lightbasecolours2'
                            whichmain = apply_smoke_effects(whichmain)
                        elif((("cinnamon" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("chocolate" in whichcolour and "cb" in phenotype.pointgene) or ("black" in whichcolour and phenotype.pointgene == ["cs", "cs"])) and sprite_age > 0) or (("chocolate" in whichcolour and phenotype.pointgene == ["cb", "cb"]) or ("black" in whichcolour and "cb" in phenotype.pointgene)):
                            whichmain.blit(sprites.sprites['lightbasecolours1'], (0, 0))  
                            colour = 'lightbasecolours1'
                            whichmain = apply_smoke_effects(whichmain)
                        elif phenotype.pointgene == ["cb", "cb"] or ("cb" in phenotype.pointgene and sprite_age > 0):
                            coloursurface = create_coloursurface(whichcolour, False)
                            whichmain.blit(coloursurface, (0, 0))
                            whichmain = apply_smoke_effects(whichmain)
                        else:
                            whichmain.blit(sprites.sprites['lightbasecolours0'], (0, 0))
                            colour = 'lightbasecolours0'

                        stripebase = create_stripes(colour, 'solid', special="no_shading", coloursurface=coloursurface)

                        whichmain.blit(stripebase, (0, 0))

                        pointbase = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        pointbase2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                            
                        pointbase2.blit(sprites.sprites[whichcolour], (0, 0))
                        if phenotype.caramel == 'caramel' and not is_red:    
                                pointbase2.blit(sprites.sprites['caramel0'], (0, 0))
                        pointbase2 = apply_smoke_effects(pointbase2)

                        
                        stripebase = create_stripes(whichcolour, "solid", special="no_shading")
                    
                        pointbase2.blit(stripebase, (0, 0))

                        if(get_current_season(season_override) == "Greenleaf"):
                            pointbase.blit(sprites.sprites['pointsl' + cat_sprite], (0, 0))
                            pointbase.blit(pointbase2, (0, 0), 
                                        special_flags=pygame.BLEND_RGBA_MULT)
                        elif(get_current_season(season_override) == "Leaf-bare"):
                            pointbase.blit(sprites.sprites['pointsd' + cat_sprite], (0, 0))
                            pointbase.blit(pointbase2, (0, 0), 
                                        special_flags=pygame.BLEND_RGBA_MULT)
                        else:
                            pointbase.blit(sprites.sprites['pointsm' + cat_sprite], (0, 0))
                            pointbase.blit(pointbase2, (0, 0), 
                                        special_flags=pygame.BLEND_RGBA_MULT)
                    
                        whichmain.blit(pointbase, (0, 0))

                if is_today(SpecialDate.APRIL_FOOLS) and phenotype.peacock and not is_red:
                    blue = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    if phenotype.eumelanin[0] == "B":
                        blue.fill((0, 100, 255))
                    elif phenotype.eumelanin[0] == "b":
                        blue.fill((50, 0, 255))
                    else:
                        blue.fill((255, 0, 150))
                    blue.set_alpha(100)
                    blue.blit(whichmain, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
                    whichmain.blit(blue, (0, 0))

                if is_red and phenotype.specialred == "blue-tipped" and special != "blue-tipped":
                    mask = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    mask.blit(sprites.sprites['BLUE-TIPPED' + cat_sprite], (0, 0))
                    colours = phenotype.FindRed(phenotype, sprite_age, 'blue-tipped')
                    mask.blit(make_cat(pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA), colours[0], colours[1], [colours[2], colours[3]], "blue-tipped"), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    whichmain.blit(mask, (0, 0))

                if not is_red and not is_white and cat.pelt.rusting:
                    for rust, opacity in cat.pelt.rusting.items():
                        rusting = sprites.sprites[rust + cat_sprite].copy()
                        rusting.fill((255, 255, 255, int((255/100)*opacity)), special_flags=pygame.BLEND_RGBA_MULT)
                        whichmain.blit(rusting.premul_alpha(), (0, 0), special_flags=pygame.BLEND_RGB_ADD)
                    
                seasondict = {
                    'Greenleaf': 'summer',
                    'Leaf-bare': 'winter'
                }

                if(phenotype.karp[0] == 'K'):
                    if(phenotype.karp[1] == 'K'):
                        whichmain.blit(sprites.sprites['homokarpati'+ seasondict.get(get_current_season(season_override), "spring") + cat_sprite], (0, 0))
                    else:
                        whichmain.blit(sprites.sprites['hetkarpati'+ seasondict.get(get_current_season(season_override), "spring") + cat_sprite], (0, 0))
                if(phenotype.white[0] == 'wsal'):
                    whichmain.blit(sprites.sprites['salmiak' + cat_sprite], (0, 0))

                whichmain = add_pads(whichmain, whichcolour, is_red)
                whichmain = add_nose(whichmain, whichcolour, whichbase, is_red)
                
                return whichmain

            gensprite = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)

            def apply_patch_effects(sprite):
                if('masked' in phenotype.silvergold):
                    masked = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    masked = make_cat(masked, phenotype.maincolour, phenotype.spritecolour, phenotype.mainunders, special="masked silver")
                    masked2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    masked2.blit(sprites.sprites["BLUE-TIPPED" + cat_sprite], (0, 0))
                    masked2.blit(masked, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    masked2.set_alpha(120)
                    sprite.blit(masked2, (0, 0))

                if (phenotype.glitter[0] == 'gl' or phenotype.ghosting[0] == 'Gh') and (phenotype.agouti[0] != 'a' or ('red' in phenotype.maincolour or 'cream' in phenotype.maincolour or 'honey' in phenotype.maincolour or 'ivory' in phenotype.maincolour or 'apricot' in phenotype.maincolour)):    
                    if phenotype.glitter[0] == 'gl':
                        sprite.blit(sprites.sprites['satin0'], (0, 0))
                    if (phenotype.ghosting[0] == 'Gh'):
                        fading = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        fading.blit(sprites.sprites['bleach'+cat_sprite], (0, 0))
                        fading.blit(sprites.sprites['satin0'], (0, 0))
                        fading.blit(sprites.sprites['satin0'], (0, 0))
                        fading.blit(sprites.sprites['satin0'], (0, 0))
                        fading.blit(sprites.sprites['satin0'], (0, 0))
                        fading.set_alpha(50)
                        sprite.blit(fading, (0, 0))
                if not phenotype.brindledbi and not ('red' in phenotype.maincolour or 'cream' in phenotype.maincolour or 'honey' in phenotype.maincolour or 'ivory' in phenotype.maincolour or 'apricot' in phenotype.maincolour) and phenotype.ext[0] != "Eg" and (phenotype.agouti[0] != 'a' and (phenotype.corin[0] == 'sg' or phenotype.corin[0] == 'sh' or (phenotype.silver[0] == 'i' and phenotype.corin[0] == 'fg') or (phenotype.ext[0] == 'ea' and sprite_age > 6) or 'ec' in phenotype.ext) or (phenotype.ext[0] == 'ea' and sprite_age > 12)):
                    sunshine = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    sunshine.blit(sprites.sprites['Tabby_unders' + cat_sprite], (0, 0))

                    colours = phenotype.FindRed(phenotype, sprite_age, special='nosilver')
                    underbelly = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    underbelly = make_cat(underbelly, colours[0], colours[1], [colours[2], colours[3]], special='nounders')
                    sunshine.blit(underbelly, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                    sunshine.set_alpha(75)
                    sprite.blit(sunshine, (0, 0))
                return sprite

            is_white = 'W' in phenotype.white or phenotype.pointgene[0] == 'c' or phenotype.white_pattern == ['full white']
            
            if(phenotype.patchmain != "" and 'rev' in phenotype.tortiepattern[0]):
                gensprite = make_cat(gensprite, phenotype.patchmain, phenotype.patchcolour, phenotype.patchunders)
            else:
                gensprite = make_cat(gensprite, phenotype.maincolour, phenotype.spritecolour, phenotype.mainunders)
            
            if not is_white:
                gensprite = apply_patch_effects(gensprite)
            
                if(phenotype.patchmain != ""):
                    for pattern in phenotype.tortiepattern:
                        tortpatches = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        if 'rev' in pattern:
                            isred = ('red' in phenotype.maincolour or 'cream' in phenotype.maincolour or 'honey' in phenotype.maincolour or 'ivory' in phenotype.maincolour or 'apricot' in phenotype.maincolour or 'white' in phenotype.maincolour)
                            tortpatches = make_cat(tortpatches, phenotype.maincolour, phenotype.spritecolour, phenotype.mainunders)
                        else:
                            isred = ('red' in phenotype.patchmain or 'cream' in phenotype.patchmain or 'honey' in phenotype.patchmain or 'ivory' in phenotype.patchmain or 'apricot' in phenotype.patchmain or 'white' in phenotype.patchmain)
                            tortpatches = make_cat(tortpatches, phenotype.patchmain, phenotype.patchcolour, phenotype.patchunders)
                        if phenotype.caramel == 'caramel' and not isred: 
                            tortpatches.blit(sprites.sprites['caramel0'], (0, 0))
                        tortpatches = apply_patch_effects(tortpatches)
                        
                        tortpatches2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        tortpatches2.blit(sprites.sprites[pattern.replace('rev', "") + cat_sprite], (0, 0))
                        tortpatches2.blit(tortpatches, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        gensprite.blit(tortpatches2, (0, 0))

                if(phenotype.merlepattern != None and not merle):
                    for pattern in phenotype.merlepattern:
                        if 'rev' in pattern:
                            phenotype.SpriteInfo(sprite_age)
                            merlepatches = gen_sprite(phenotype, sprite_age, merle=True)
                        else:
                            old_silver = phenotype.silver
                            phenotype.silver = ['i', 'i']
                            phenotype.SpriteInfo(sprite_age)
                            merlepatches = gen_sprite(phenotype, sprite_age, merle=True)
                            phenotype.silver = old_silver
                            phenotype.SpriteInfo(sprite_age)
                        
                        merlepatches2 = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                        merlepatches2.blit(sprites.sprites[pattern.replace('rev', "") + cat_sprite], (0, 0))
                        merlepatches2.blit(merlepatches, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        gensprite.blit(merlepatches2, (0, 0))

                if phenotype.satin[0] == "st" or phenotype.tenn[0] == 'tr':
                    gensprite.blit(sprites.sprites['satin0'], (0, 0))

                if (phenotype.fevercoat and sprite_age < 5):
                    fevercoat = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                    fevercoat.blit(sprites.sprites['bleach' + cat_sprite], (0, 0))
                    fevercoat.blit(sprites.sprites['bleach' + cat_sprite], (0, 0))
                    fevercoat.blit(sprites.sprites['bleach' + cat_sprite], (0, 0))
                    if (sprite_age > 2):
                        fevercoat.set_alpha(150)
                    gensprite.blit(fevercoat, (0, 0))
                
                elif (phenotype.bleach[0] == "lb" and sprite_age > 3) or (phenotype.wbtype == "shaded" and 'smoke' in phenotype.silvergold):
                    gensprite.blit(sprites.sprites['bleach' + cat_sprite], (0, 0))
                elif ('masked' in phenotype.silvergold and phenotype.wideband < 16):
                    gensprite.blit(sprites.sprites['bleach' + cat_sprite], (0, 0))
                    gensprite.blit(sprites.sprites['bleach' + cat_sprite], (0, 0))

            
            if (
                game_setting_get('tints')
                and cat.pelt.tint in sprites.cat_tints["tint_colours"]
            ):
                tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                tint.fill(tuple(sprites.cat_tints["tint_colours"][cat.pelt.tint]))
                gensprite.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            if (
                game_setting_get('tints')
                and cat.pelt.tint in sprites.cat_tints["dilute_tint_colours"]
            ):
                tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                tint.fill(tuple(sprites.cat_tints["dilute_tint_colours"][cat.pelt.tint]))
                gensprite.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

            if is_today(SpecialDate.APRIL_FOOLS) and "Dg" in phenotype.april_fools.get("danish_green", []):
                green = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                green.fill((0, 255, 0))
                green.set_alpha(100)
                green.blit(gensprite, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
                gensprite.blit(green, (0, 0))

            whitesprite = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
            tintedwhitesprite = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)

            if(phenotype.white_pattern != 'No' and phenotype.white_pattern):
                for x in phenotype.white_pattern:
                    if('dorsal' not in x and 'break/' not in x and x not in vitiligo):
                        whitesprite.blit(sprites.sprites[x + cat_sprite], (0, 0))
            if(phenotype.white_pattern != 'No' and phenotype.white_pattern):
                for x in phenotype.white_pattern:
                    if('break/' in x):
                        whitesprite.blit(sprites.sprites[x + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            tintedwhitesprite.blit(whitesprite, (0, 0))

            leathers = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
            leathers = add_pads(leathers, "white")
            leathers = add_nose(leathers, "white", "white", False)
            white_leathers = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
            white_leathers.blit(whitesprite, (0, 0))

            if(phenotype.vitiligo):
                for x in vitiligo:
                    if x in phenotype.white_pattern:
                        white_leathers.blit(sprites.sprites[x + cat_sprite], (0, 0))
                        tintedwhitesprite.blit(sprites.sprites[x + cat_sprite], (0, 0))
            white_leathers.blit(leathers, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

            if phenotype.white_pattern:
                if 'dorsal1' in phenotype.white_pattern:
                    tintedwhitesprite.blit(sprites.sprites['dorsal1' + cat_sprite], (0, 0))
                elif 'dorsal2' in phenotype.white_pattern:
                    tintedwhitesprite.blit(sprites.sprites['dorsal2' + cat_sprite], (0, 0))

            
            if is_today(SpecialDate.APRIL_FOOLS) and "Bs" in phenotype.april_fools.get("black_spotting", []):
                tintedwhitesprite.blit(sprites.sprites[f'black{phenotype.fur_shade}'], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            if (
                game_setting_get('tints')
                and cat.pelt.white_patches_tint != "none"
                and cat.pelt.white_patches_tint
                in sprites.white_patches_tints["tint_colours"]
            ):
                tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                tint.fill(
                    tuple(
                        sprites.white_patches_tints["tint_colours"][
                            cat.pelt.white_patches_tint
                        ]
                    )
                )
                tintedwhitesprite.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            gensprite.blit(tintedwhitesprite, (0, 0))

            hairless = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
            if cat.phenotype.sedesp == ['hr', 're'] or (cat.phenotype.sedesp[0] == 're' and sprite_age < 12):
                hairless.blit(sprites.sprites['furpoint' + cat_sprite], (0, 0))
                hairless.blit(sprites.sprites['furpoint' + cat_sprite], (0, 0))
            elif(cat.pelt.length == 'hairless' and (cat.phenotype.sedesp[0] == "hr" or cat.phenotype.ruhr[1] == "Hrbd" or sprite_age > 11)):
                hairless.blit(sprites.sprites['hairless' + cat_sprite], (0, 0))
                hairless.blit(sprites.sprites['break/nose1' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
                hairless.blit(sprites.sprites['furpoint' + cat_sprite], (0, 0))
                if get_current_season(season_override) == "Leaf-bare":
                    hairless.set_alpha(200)
            elif cat.phenotype.laperm[0] == 'Lp' and sprite_age < 4:
                hairless.blit(sprites.sprites['furpoint' + cat_sprite], (0, 0))
                hairless.blit(sprites.sprites['furpoint' + cat_sprite], (0, 0))
                hairless.set_alpha(120)
            elif ('patchy ' in cat.phenotype.furtype) or (cat.pelt.length == 'hairless' and cat.phenotype.sedesp[0] != "hr" and cat.phenotype.ruhr[1] != "Hrbd" and sprite_age > 5):
                hairless.blit(sprites.sprites['donskoy' + cat_sprite], (0, 0))
            
            if('sparse' in cat.phenotype.furtype):
                hairless.blit(sprites.sprites['satin0'], (0, 0))
                hairless.blit(sprites.sprites['lykoi' + cat_sprite], (0, 0))
            
            hairless.blit(sprites.sprites['nose' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            gensprite.blit(hairless, (0, 0))

            gensprite.blit(white_leathers, (0, 0))
            

            if(phenotype.fold[0] == 'Fd' and phenotype.curl[0] == 'Cu'):
                gensprite.blit(sprites.sprites['fold_curl_ears' + cat_sprite], (0, 0))
            elif(phenotype.fold[0] != 'Fd' or phenotype.curl[0] == 'Cu'):
                gensprite.blit(sprites.sprites['ears' + cat_sprite], (0, 0))


            def construct_eye_colour(eyetype):
                split = eyetype.split(" ; ")
                data = sprites.EYE_DATA[split[1]][split[0]].copy()
                eyes = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                
                if is_today(SpecialDate.APRIL_FOOLS):
                    if phenotype.april_fools.get("rainbow_eyes", ["NoDRE"])[0] == "DREfull":
                        data["inner"] = [randint(0, 255), randint(0, 255), randint(0, 255)] 
                        data["outer"] = [randint(127, 255), randint(127, 255), randint(127, 255)] 
                        data["pupil"] = [randint(0, 127), randint(0, 127), randint(0, 127)] 
                    elif phenotype.april_fools.get("rainbow_eyes", ["NoDRE"])[0] == "DREmin":
                        rgb = [randint(0, 255), randint(0, 255), randint(0, 255)]
                        data["inner"] = rgb 
                        pupils = [0, 0, 0]
                        pupils1 = [v*0.5 for v in rgb]
                        rgb = [round(rgb[0]*0.625), round(rgb[1]*0.7), round(rgb[2]*0.50)]
                        data["outer"] = rgb
                        pupils2 = [v*0.5 for v in rgb]
                        for i in range(3):
                            pupils[i] = round((pupils1[i] + pupils2[i])/2)
                        data["pupil"] = pupils
                
                colour = pygame.Color(data["inner"])
                eye_section = sprites.sprites['eyeinner' + cat_sprite].copy()
                pixel_array = pygame.PixelArray(eye_section)
                pixel_array.replace((255, 255, 255, 255), colour, distance=0)
                del pixel_array
                eyes.blit(eye_section, (0, 0))
                
                colour = pygame.Color(data["outer"])
                eye_section = sprites.sprites['eyeouter' + cat_sprite].copy()
                pixel_array = pygame.PixelArray(eye_section)
                pixel_array.replace((255, 255, 255, 255), colour, distance=0)
                del pixel_array
                eyes.blit(eye_section, (0, 0))
                
                colour = pygame.Color(data["pupil"] if phenotype.pinkdilute[0] != 'dp' and not game_setting_get('black_pupils') else ([0, 0, 0] if phenotype.pinkdilute[0] != 'dp' and (phenotype.pointgene[1] != "c" or phenotype.pointgene[0] == "C") else [80, 20, 29]))
                eye_section = sprites.sprites['eyepupil' + cat_sprite].copy()
                pixel_array = pygame.PixelArray(eye_section)
                pixel_array.replace((255, 255, 255, 255), colour, distance=0)
                del pixel_array
                eyes.blit(eye_section, (0, 0))
                return eyes

            if(int(cat_sprite) % 4 != 3 and int(cat_sprite) > 3):
                lefteye = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                righteye = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                special = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)

                lefteye.blit(sprites.sprites['left' + cat_sprite], (0, 0))
                righteye.blit(sprites.sprites['right' + cat_sprite], (0, 0))

                lefteye.blit(construct_eye_colour(phenotype.lefteyetype), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                righteye.blit(construct_eye_colour(phenotype.righteyetype), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

                gensprite.blit(lefteye, (0, 0))
                gensprite.blit(righteye, (0, 0))

                if sprite_age == 1:
                    lefteye.blit(sprites.sprites['left' + cat_sprite], (0, 0))
                    righteye.blit(sprites.sprites['right' + cat_sprite], (0, 0))
                    lefteye.blit(construct_eye_colour(phenotype.lefteyetype.split(' ; ')[0] + ' ; blue'), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    righteye.blit(construct_eye_colour(phenotype.righteyetype.split(' ; ')[0] + ' ; blue'), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    lefteye.set_alpha(200)
                    righteye.set_alpha(200)
                    gensprite.blit(lefteye, (0, 0))
                    gensprite.blit(righteye, (0, 0))


                if(phenotype.extraeye):
                    special.blit(sprites.sprites[phenotype.extraeye + cat_sprite], (0, 0))
                    special.blit(construct_eye_colour(phenotype.extraeyetype), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    gensprite.blit(special, (0, 0))
                    if sprite_age == 1:
                        special.blit(sprites.sprites[phenotype.extraeye + cat_sprite], (0, 0))
                        special.blit(construct_eye_colour(phenotype.extraeyetype.split(' ; ')[0] + ' ; blue'), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        special.set_alpha(150)
                        gensprite.blit(special, (0, 0))
            
            return gensprite

        age = cat.moons

        if int(cat_sprite) < 4:
            age = 0
        elif 3 < int(cat_sprite) < 8 and (5 < cat.moons or cat.moons < 1):
            age = 4
        elif 7 < int(cat_sprite) < 16 and (11 < cat.moons or cat.moons < 6):
            age = 10
        elif cat_sprite in ['30'] and (12 < cat.moons or cat.moons < 1):
            age = 6
        elif 15 < int(cat_sprite) < 24 and cat.moons > 120:
            age = 30
        elif 23 < int(cat_sprite) < 28 and cat.moons < 120:
            age = 120
        elif int(cat_sprite) > 15 and cat_sprite not in ['28', '29'] and cat.moons < 12:
            age = 60
        gensprite.blit(gen_sprite(phenotype, age), (0, 0))

        if(cat.chimerapheno):
            geno = deepcopy(cat.chimerapheno)
            if hide_white:
                geno.white = ["w", "w"]
                geno.white_pattern = "No"
                geno.PhenotypeOutput()
            chimerapatches = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
            for pattern in cat.chimerapheno.chimerapattern:
                chimerapatches.blit(sprites.sprites[pattern + cat_sprite], (0, 0))
            chimerapatches.blit(gen_sprite(geno, age), (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            gensprite.blit(chimerapatches, (0, 0))

        if not scars_hidden:
            for scar in cat.pelt.scars:
                if scar in cat.pelt.general_scars:
                    sprite_name = (
                        f"{sprites.SCAR_DATA['spritesheet']}{scar}{cat_sprite}"
                    )
                    gensprite.blit(sprites.sprites[sprite_name], (0, 0))

        # setting the lineart color to override on accessories & missing bits
        lineart_color = (
            pygame.Color(
                get_config("cat_sprites")["lineart_color_sc"]
                if cat.status.group == CatGroup.STARCLAN
                else get_config("cat_sprites")["lineart_color_df"]
            )
            if cat.status.group != CatGroup.UNKNOWN_RESIDENCE
            else None
        )

        gradient_surface = (
            sprites.sprites["line_ur_gradient" + cat_sprite]
            if dead and cat.status.group == CatGroup.UNKNOWN_RESIDENCE
            else None
        )

        def _recolor_lineart(
            sprite, color=None, source: pygame.Surface = None
        ) -> pygame.Surface:
            """
            Helper function to set the appropriate lineart color for the living status of the cat
            :param sprite: lineart to recolor
            :param color: color to apply to all pixels
            :param source: source surface of same size as sprite to use instead of color
            :return:
            """
            if not dead:
                return sprite

            if color is None and source is None:
                raise ValueError(
                    "Must provide either `color` or `source` for _recolor_lineart"
                )

            out = sprite.copy()
            if color:
                pixel_array = pygame.PixelArray(out)
                pixel_array.replace((0, 0, 0), color, distance=0)
                del pixel_array
                return out

            width, height = sprite.get_size()
            for x in range(width):
                for y in range(height):
                    if sprite.get_at((x, y)) == (pygame.Color(0, 0, 0)):
                        color = source.get_at((x, y))
                        out.set_at((x, y), color)
            return out

        # draw line art
        if game_setting_get('shaders') and not dead:
            gensprite.blit(sprites.sprites['shader_mask' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            gensprite.blit(
                sprites.sprites['shader_lighting' + cat_sprite], (0, 0))

        # make sure colours are in the lines
        if('rexed' in phenotype.furtype or 'wiry' in phenotype.furtype):
            gensprite.blit(sprites.sprites['rexbord'+ cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            gensprite.blit(sprites.sprites['rexbord'+ cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        else:
            gensprite.blit(sprites.sprites['normbord'+ cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            gensprite.blit(sprites.sprites['normbord'+ cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        if(cat.phenotype.fold[0] == 'Fd'):
            gensprite.blit(sprites.sprites['foldbord'+ cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            gensprite.blit(sprites.sprites['foldbord'+ cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        elif(cat.phenotype.curl[0] == 'Cu'):
            gensprite.blit(sprites.sprites['curlbord'+ cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            gensprite.blit(sprites.sprites['curlbord'+ cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        new_sprite.blit(gensprite, (0, 0))

        lineart = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
        earlines = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
        bodylines = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)

        # if not dead:
        if(cat.phenotype.fold[0] != 'Fd'):
            if(cat.phenotype.curl[0] == 'Cu'):
                earlines.blit(sprites.sprites['curllines' + cat_sprite], (0, 0))
            else:
                earlines.blit(sprites.sprites['lineart' + cat_sprite], (0, 0))
            if phenotype.fourear[0] == "dup":
                earlines.blit(sprites.sprites['fourears' + cat_sprite], (0, 0))
        elif(cat.phenotype.curl[0] == 'Cu'):
            earlines.blit(sprites.sprites['fold_curllines' + cat_sprite], (0, 0))
        else:
            earlines.blit(sprites.sprites['foldlines' + cat_sprite], (0, 0))

        if('rexed' in phenotype.furtype or 'wiry' in phenotype.furtype):
            if not dead or cat.status.group != CatGroup.DARK_FOREST:
                bodylines.blit(sprites.sprites['rexlineart' + cat_sprite], (0, 0))
            elif cat.status.group == CatGroup.DARK_FOREST:
                bodylines.blit(sprites.sprites['rexlineartdf' + cat_sprite], (0, 0))
        else:
            if not dead:
                bodylines.blit(sprites.sprites['lineart' + cat_sprite], (0, 0))
            elif cat.status.group == CatGroup.UNKNOWN_RESIDENCE:
                bodylines.blit(sprites.sprites['lineart_ur' + cat_sprite], (0, 0))
            elif cat.status.group == CatGroup.DARK_FOREST:
                bodylines.blit(sprites.sprites['lineart_df' + cat_sprite], (0, 0))
            else:
                bodylines.blit(sprites.sprites['lineart_sc' + cat_sprite], (0, 0))
            
        if int(cat_sprite) > 2:
            earlines.blit(sprites.sprites['isolateears' + cat_sprite],
                      (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            lineart.blit(earlines, (0, 0))
            bodylines.blit(sprites.sprites['noears' + cat_sprite], (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        lineart.blit(bodylines, (0, 0))
        new_sprite.blit(_recolor_lineart(
                            lineart,
                            lineart_color,
                            gradient_surface,
                        ), (0, 0))

        # draw skin and scars2
        blendmode = pygame.BLEND_RGBA_MIN

        gensprite = new_sprite
        if cat.phenotype.bobtailnr > 0:
            gensprite.blit(_recolor_lineart(
                sprites.sprites['bobtail' +
                                str(cat.phenotype.bobtailnr) + cat_sprite],
                lineart_color,
                gradient_surface,
            ), (0, 0))
        gensprite.set_colorkey((0, 0, 255))
        new_sprite = pygame.Surface(
            (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
        new_sprite.blit(gensprite, (0, 0))

        if is_today(SpecialDate.APRIL_FOOLS):
            if cat.phenotype.bobtailnr != 1 and "Pc" in phenotype.april_fools.get("polycaudal", []):
                tail = pygame.Surface(
                    (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                tail.blit(sprites.sprites['bobtail1' + cat_sprite], (0, 0))
                white = pygame.Surface(
                    (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
                white.fill((255, 255, 255))
                tail.blit(white, (0, 0), special_flags=pygame.BLEND_RGB_MAX)
                tail.blit(new_sprite, (0, 0),
                          special_flags=pygame.BLEND_RGBA_MIN)
                offset = 2
                if cat_sprite in ["2", "11", "16", "17", "18", "19", "21", "24"]:
                    new_sprite.blit(tail, (offset, 1))
                elif cat_sprite in ["5", "8", "9", "10", "12", "13", "14", "20", "25", "26", "27"]:
                    new_sprite.blit(tail, (-offset, -1))
                elif cat_sprite in ["1", "6", "7"]:
                    new_sprite.blit(tail, (0, -2))

            if get_config("fun.april_fools_hats"):
                if not dead:
                    new_sprite.blit(
                        sprites.sprites['aprilfoolslines' + cat_sprite], (0, 0))
                elif cat.status.group == CatGroup.DARK_FOREST:
                    new_sprite.blit(
                        sprites.sprites['aprilfoolslineartdf' + cat_sprite], (0, 0))
                elif cat.status.group == CatGroup.UNKNOWN_RESIDENCE:
                    new_sprite.blit(
                        sprites.sprites['aprilfoolslineartur' + cat_sprite], (0, 0))
                else:
                    new_sprite.blit(
                        sprites.sprites['aprilfoolslineartdead' + cat_sprite], (0, 0))

        if not scars_hidden:
            for scar in cat.pelt.scars:
                if scar in cat.pelt.missing_part_scars:
                    sprite_name = f"{sprites.SCAR_MISSING_PART_DATA['spritesheet']}{scar}{cat_sprite}"
                    new_sprite.blit(
                        _recolor_lineart(
                            sprites.sprites[sprite_name],
                            lineart_color,
                            gradient_surface,
                        ),
                        (0, 0),
                        special_flags=blendmode,
                    )

        # draw accessories
        from scripts.cat.pelts import Pelt

        if not acc_hidden and cat.pelt.accessory:
            cat_accessories = cat.pelt.accessory
            categories = [
                "collar_accessories",
                "tail_accessories",
                "body_accessories",
                "head_accessories",
            ]
            for category in categories:
                for accessory in cat_accessories:
                    if accessory in getattr(Pelt, category):
                        if accessory in cat.pelt.plant_accessories:
                            sprite_name = f"{sprites.PLANT_DATA['spritesheet']}{accessory}{cat_sprite}"
                            new_sprite.blit(
                                _recolor_lineart(
                                    sprites.sprites[sprite_name],
                                    lineart_color,
                                    gradient_surface,
                                ),
                                (0, 0),
                            )
                        elif accessory in cat.pelt.wild_accessories:
                            sprite_name = f"{sprites.WILD_DATA['spritesheet']}{accessory}{cat_sprite}"
                            new_sprite.blit(
                                _recolor_lineart(
                                    sprites.sprites[sprite_name],
                                    lineart_color,
                                    gradient_surface,
                                ),
                                (0, 0),
                            )
                        elif accessory in cat.pelt.collar_accessories:
                            sprite_name = f"{sprites.COLLAR_DATA['spritesheet']}{accessory}{cat_sprite}"
                            new_sprite.blit(
                                _recolor_lineart(
                                    sprites.sprites[sprite_name],
                                    lineart_color,
                                    gradient_surface,
                                ),
                                (0, 0),
                            )

        # Apply fading fog
        if (
            cat.pelt.opacity <= 97
            and not cat.prevent_fading
            and get_clan_setting("fading")
            and dead
        ):
            stage = "0"
            if 80 >= cat.pelt.opacity > 45:
                # Stage 1
                stage = "1"
            elif cat.pelt.opacity <= 45:
                # Stage 2
                stage = "2"

            new_sprite.blit(
                sprites.sprites["fademask" + stage + cat_sprite],
                (0, 0),
                special_flags=pygame.BLEND_RGBA_MULT,
            )

            if cat.status.group == CatGroup.STARCLAN:
                temp = sprites.sprites["fadestarclan" + stage + cat_sprite].copy()
                temp.blit(new_sprite, (0, 0))
                new_sprite = temp
            elif cat.status.group == CatGroup.UNKNOWN_RESIDENCE:
                temp = sprites.sprites["fadeur" + stage + cat_sprite].copy()
                temp.blit(new_sprite, (0, 0))
                new_sprite = temp
            else:
                temp = sprites.sprites["fadedf" + stage + cat_sprite].copy()
                temp.blit(new_sprite, (0, 0))
                new_sprite = temp

        # ok! we have the sprite! now, do some layer things if the cat's already dead
        if dead:
            temp_sprite = pygame.Surface(
                (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA
            )

            if cat.status.group == CatGroup.STARCLAN:
                # no underlay

                # cat sprite
                temp_sprite.blit(new_sprite, (0, 0))

                # overlay
                temp_sprite.blit(
                    sprites.sprites["line_sc_overlay" + cat_sprite],
                    (0, 0),
                )
            elif cat.status.group == CatGroup.UNKNOWN_RESIDENCE:
                # underlay
                temp_sprite.blit(
                    sprites.sprites["line_ur_underlay" + cat_sprite],
                    (0, 0),
                )

                # cat sprite
                temp_sprite.blit(new_sprite, (0, 0))

                # overlay
                temp_sprite.blit(
                    sprites.sprites["line_ur_overlay" + cat_sprite],
                    (0, 0),
                )
            elif cat.status.group == CatGroup.DARK_FOREST:
                # no underlay

                # cat sprite
                temp_sprite.blit(new_sprite, (0, 0))

                # no overlay

            new_sprite = temp_sprite

        return new_sprite

    try:
        geno = deepcopy(cat.phenotype)
        if hide_white:
            geno.white = ["w", "w"]
            geno.white_pattern = "No"
            geno.PhenotypeOutput()
        new_sprite = draw_sprite(geno, cat_sprite)
        if cat.phenotype.somatic.get('base', False):
            som_sprite = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)
            som_sprite.blit(sprites.sprites[geno.somatic["base"] + cat_sprite], (0, 0))
            som_sprite.blit(draw_sprite(geno, cat_sprite, somatic=True), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            new_sprite.blit(som_sprite, (0, 0))

    except (TypeError, KeyError):
        traceback.print_exc()
        logger.exception("Failed to load sprite")

        # Placeholder image
        new_sprite = image_cache.load_image(
            f"sprites/error_placeholder.png"
        ).convert_alpha()
    
    # reverse, if assigned so
    if cat.pelt.reverse:
        new_sprite = pygame.transform.flip(new_sprite, True, False)

    return new_sprite


def update_sprite(cat):
    # First, check if the cat is faded.
    if cat.faded:
        # Don't update the sprite if the cat is faded.
        return

    # apply
    cat.sprite = generate_sprite(cat)
    # update class dictionary
    cat.all_cats[cat.ID] = cat


def update_mask(cat):
    if cat.faded or cat.dead:
        # should never need a mask since they can't appear on the Clan screen
        cat.sprite_mask = None
        return

    val = pygame.mask.from_surface(
        pygame.transform.scale(cat.sprite, ui_scale_dimensions((50, 50))), threshold=250
    )

    inflated_mask = pygame.Mask(
        (
            val.get_size()[0] + 10,
            val.get_size()[1] + 10,
        )
    )
    inflated_mask.draw(val, (5, 5))
    for _ in range(3):
        outline = inflated_mask.outline()
        for point in outline:
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    try:
                        inflated_mask.set_at((point[0] + dx, point[1] + dy), 1)
                    except IndexError:
                        continue
    cat.sprite_mask = inflated_mask


def calculate_size(cat):
    if cat.age in [CatAge.NEWBORN, CatAge.KITTEN]:
        size = "average"
        if cat.phenotype.growth_pattern == "big-kitten":
            size = "big"
        elif cat.phenotype.growth_pattern == "small-kitten":
            size = "small"
        elif cat.phenotype.growth_pattern == "runt":
            size = "runt"
        return size
    elif (cat.age == CatAge.ADOLESCENT or (cat.moons < 24 and cat.phenotype.growth_pattern == "slow")):
        start_point = cat.phenotype.shoulder_height * 0.66 if cat.phenotype.growth_pattern == "slow" else cat.phenotype.shoulder_height * 0.75
        period = 18 if cat.phenotype.growth_pattern == "slow" else 6
        difference = 24-cat.moons if cat.phenotype.growth_pattern == "slow" else 12-cat.moons
        difference = max(0, difference)
        step = (cat.phenotype.shoulder_height - start_point) / period

        height = round(cat.phenotype.shoulder_height - (difference * step), 2)
        return height

    return cat.phenotype.shoulder_height