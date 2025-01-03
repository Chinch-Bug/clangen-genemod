from .genotype import *
from .phenotype import *
from random import choice, random
from operator import xor
from copy import deepcopy

class Namer():
    def __init__ (self, used_prefixes=[], mod_prefixes=[], moons=0):
        self.used_prefixes = used_prefixes
        self.all_prefixes = mod_prefixes
        self.moons = moons

    def start(self, genotype, phenotype, chimera_pheno = None):
        self.genotype = genotype
        self.phenotype = phenotype
        self.chimera_pheno = chimera_pheno

        if genotype:
            params = self.parse_chimera() if genotype.chimera else self.get_categories(genotype, phenotype)

            if params[0] in ['white', 'silver shaded'] or (params[3] == 'high' and random() < 0.2):
                return self.white(params[0])
            elif params[0] == 'black':
                return self.black(params)
            elif params[0] == 'blue':
                return self.blue(params)
            elif params[0] == 'ginger':
                return self.ginger(params)
            elif params[0] == 'cream':
                return self.cream(params)
            elif params[0] == 'chocolate':
                return self.chocolate(params)
            elif params[0] == 'lilac':
                return self.lilac(params)
            elif params[0] == 'cinnamon':
                return self.cinnamon(params)
            elif params[0] == 'fawn':
                return self.fawn(params)
            else:
                print('Unknown base:' + params[0])

    def parse_chimera(self):

        base = ""
        tortie = False
        tortie_mimic = False
        tabby = {
            'pattern' : '',
            'type' : 'regular',
            'tortie_red' : ''
        }
        white = 'no'
        point = 'none'

        #compare different chimera halves here
        set_one = self.get_categories(self.genotype, self.phenotype)
        set_two = self.get_categories(self.genotype.chimerageno, self.chimera_pheno)


        #the easy part
        if set_one[1] in ['white', 'silver shaded'] and set_two[1] in ['white', 'silver shaded']:
            base = 'white'
            return [base, tortie, tabby, white, point]
        
        if set_one[1] or set_two[1] or xor(set_one[0] in ['ginger', 'cream'], set_two[0] in ['ginger', 'cream']):
            tortie = True
            tortie_mimic = True
            tabby['tortie_red'] = set_one[2]['pattern'] if set_one[0] in ['ginger', 'cream'] else set_two[2]['pattern']

        if set_one[3] == 'high' or (self.moons == 0 and set_one[4] == 'colourpoint'):
            white = 'high'
        elif set_one[3] == 'mid' or set_two[3] == 'high' or set_one[1] == 'white' or set_two[1] in ['white', 'silver shaded'] or (self.moons == 0 and set_two[4] == 'colourpoint'):
            white = 'mid'
        elif set_one[3] == 'low' or set_two[3] == 'mid':
            white = 'low'

        #mixing solid + tabby or different base-colours changes tabby pattern to blotched
        if set_one[0] != set_two[0] and set_one[0] not in ['ginger', 'cream'] and set_two[0] not in ['ginger', 'cream']:
            tabby['pattern'] = 'blotched'
        
        #mixing different bases

        if (set_one[0] in ['black', 'chocolate', 'cinnamon'] and set_two[0] in ['black', 'chocolate', 'cinnamon']):
            if xor(set_one[2]['type'] == 'silver', set_two[2]['type'] == 'silver'):
                tortie = True
                tabby['type'] = 'silver'
            elif xor(set_one[2]['type'] == 'golden', set_two[2]['type'] == 'golden'):
                tortie = True
                if 'regular' in [set_one[2]['type'], set_two[2]['type']] and '' not in [set_one[2]['pattern'], set_two[2]['pattern']]:
                    tabby['type'] = 'regular'
                else:
                    tabby['type'] = 'dark'
            
            if 'black' in [set_one[0], set_two[0]]:
                base = 'black'
            elif 'chocolate' in [set_one[0], set_two[0]]:
                base = 'chocolate'
            else:
                base = 'cinnamon'
        elif (set_one[0] in ['blue', 'lilac', 'fawn'] and set_two[0] in ['blue', 'lilac', 'fawn']):
            if xor(set_one[2]['type'] == 'silver', set_two[2]['type'] == 'silver'):
                tortie = True
                tabby['type'] = 'silver'
            elif xor(set_one[2]['type'] == 'golden', set_two[2]['type'] == 'golden'):
                tortie = True
                if 'regular' in [set_one[2]['type'], set_two[2]['type']] and '' not in [set_one[2]['pattern'], set_two[2]['pattern']]:
                    tabby['type'] = 'regular'
                else:
                    tabby['type'] = 'dark'
            
            if 'blue' in [set_one[0], set_two[0]]:
                base = 'blue'
            elif 'lilac' in [set_one[0], set_two[0]]:
                base = 'lilac'
            else:
                base = 'fawn'
        else:
            tabby['type'] = 'silver'
            if set_one[4] != 'none':
                tortie = True
            if 'black' in [set_one[0], set_two[0]]:
                base = 'black'
            elif 'chocolate' in [set_one[0], set_two[0]]:
                base = 'chocolate'
            else:
                if 'blue' in [set_one[0], set_two[0]]:
                    base = 'blue'
                elif 'lilac' in [set_one[0], set_two[0]]:
                    base = 'lilac'
                else:
                    base = 'fawn'

        #mixing different types of point

        point = set_one[4]

        return [base, tortie, tabby, white, point, tortie_mimic]

    def get_categories(self, genotype, phenotype):
        
        # Categories are split into: base, tortie?, tabby (pattern, silver, golden), white amount, point
        base = ""
        tortie = False
        tabby = {
            'pattern' : '',
            'type' : 'regular',
            'tortie_red' : ''
        }
        white = 'no'
        point = 'none'

        try:
            phenotype.maincolour
        except:
            phenotype.SpriteInfo(self.moons)

        if (phenotype.colour in ['white', 'albino'] or 
            (phenotype.maincolour == 'white' and not phenotype.patchmain) or
            (genotype.white[1] in ['ws', 'wt'] and genotype.whitegrade == 5) or
            (genotype.tortiepattern == ['revCRYPTIC'] and genotype.brindledbi) or 
            (genotype.dilute[0] == 'd' and genotype.pinkdilute[0] == 'dp' and 
                (('dove' in phenotype.colour and genotype.saturation < 2) or 
                ('platinum' in phenotype.colour and genotype.saturation < 3) or
                ('dove' not in phenotype.colour and 'platinum' not in phenotype.colour)))
            ):
            base = 'white'
            return [base, tortie, tabby, white, point]
        elif ('silver' in phenotype.silvergold and ('shaded' in phenotype.tabby or 'chinchilla' in phenotype.tabby)):
            base = 'silver shaded'
            return [base, tortie, tabby, white, point]
        elif (('o' not in genotype.sexgene or genotype.tortiepattern == ['revCRYPTIC']) or (genotype.ext[0] == 'ea' and ((self.moons > 11 and genotype.agouti[0] != 'a') or (self.moons > 23))) or (genotype.ext[0] == 'er' and self.moons > 23) or (genotype.ext[0] == 'ec' and self.moons > 0 and (genotype.agouti[0] != 'a' or self.moons > 5))) and not (genotype.silver[0] == 'I' and genotype.specialred in ['blue-red', 'cinnamon']):
            if genotype.dilute[0] == 'd' or genotype.pinkdilute[0] == 'dp' or (genotype.silver[0] == 'I' and genotype.specialred in ['cameo', 'merle']):
                base = 'cream'
            else:
                base = 'ginger'
        else:
            if ('O' in genotype.sexgene and not genotype.brindledbi and 'CRYPTIC' not in genotype.tortiepattern[0]) or 'bimetal' in phenotype.silvergold or (genotype.silver[0] == 'I' and genotype.specialred == 'merle'):
                tortie = True
            elif ('O' in genotype.sexgene and genotype.brindledbi):
                white = 'mid'
            
            if (genotype.eumelanin[0] == 'bl') or (phenotype.colour == 'sable' and genotype.pointgene[0] == 'cm') or 'cinnamon' in phenotype.maincolour or 'fawn' in phenotype.spritecolour:
                if 'fawn' in phenotype.spritecolour or genotype.dilute[0] == 'd' or genotype.pinkdilute[0] == 'dp':
                    base = 'fawn'
                else:
                    base = 'cinnamon'
            elif genotype.eumelanin[0] == 'b' or 'lilac' in phenotype.spritecolour:
                if 'lilac' in phenotype.spritecolour or genotype.dilute[0] == 'd' or genotype.pinkdilute[0] == 'dp':
                    base = 'lilac'
                else:
                    base = 'chocolate'
            else:
                if 'blue' in phenotype.spritecolour or genotype.dilute[0] == 'd' or genotype.pinkdilute[0] == 'dp':
                    base = 'blue'
                else:
                    base = 'black'
            
        if base in ['ginger', 'cream'] or (genotype.agouti[0] != "a") or (genotype.ext[0] not in ['Eg', 'E']) or 'light smoke' in phenotype.silvergold:
            sprite = phenotype.GetTabbySprite()
            if 'bar' in sprite or 'ghost' in sprite or 'chinchilla' in phenotype.tabby:
                tabby['pattern'] = 'ticked'
            elif sprite in ['marbled', 'classic']:
                tabby['pattern'] = 'blotched'
            elif 'braid' in sprite or 'mack' in sprite or 'pins' in sprite:
                tabby['pattern'] = 'mackerel'
            else:
                tabby['pattern'] = 'spotted'

            if base not in ['ginger', 'cream'] and ('smoke' in phenotype.silvergold or 'masked' in phenotype.silvergold or genotype.ext[0] == "Eg" or (('charcoal' in phenotype.tabtype or genotype.ruftype == 'low') and genotype.wbtype in ['low', 'medium'])):
                tabby['type'] = 'dark'
            elif 'silver' in phenotype.silvergold or 'cameo' in phenotype.silvergold or 'bimetal' in phenotype.silvergold or genotype.brindledbi:
                tabby['type'] = 'silver'
            elif phenotype.silvergold:
                tabby['type'] = 'golden'

            if tortie:
                tabby['tortie_red'] = tabby['pattern']
        elif tortie:
            sprite = phenotype.GetTabbySprite()
            if 'bar' in sprite or 'ghost' in sprite or 'chinchilla' in phenotype.tabby:
                tabby['tortie_red'] = 'ticked'
            elif sprite in ['marbled', 'classic']:
                tabby['tortie_red'] = 'blotched'
            elif 'braid' in sprite or 'mack' in sprite or 'pins' in sprite:
                tabby['tortie_red'] = 'mackerel'
            else:
                tabby['tortie_red'] = 'spotted'

            

        if (genotype.white[1] in ['ws', 'wt'] and genotype.whitegrade > 2) or (self.moons < 6 and genotype.karp[0] == 'K'):
            white = 'high'
        elif genotype.white[1] in ['ws', 'wt'] or (genotype.white[0] in ['ws', 'wt'] and genotype.whitegrade > 4) or genotype.white[0] == 'wsal' or (self.moons > 12 and genotype.vitiligo) or genotype.karp[0] == 'K':
            white = 'mid'
        elif white != 'mid' and ((genotype.white[0] in ['ws', 'wt'] and genotype.whitegrade > 1) or genotype.white[0] == 'wg' or (genotype.vitiligo and self.moons > 5)) and genotype.white_pattern != "No":
            white = 'low'
        elif white != 'mid' and self.moons > 11 and genotype.vitiligo:
            white = 'low'

        if genotype.pointgene[0] == 'cs' or 'masked' in phenotype.silvergold or (self.moons < 4 and genotype.fevercoat) or (self.moons > 3 and genotype.bleach[0] == 'lb'):
            point = 'colourpoint'
        elif genotype.pointgene == ['cb', 'cb'] or (genotype.pointgene == ['cm', 'cm'] and phenotype.colour != 'sable'):
            point = 'sepia'
            if base in ['ginger', 'cream']:
                point = 'none'
            elif base in ['fawn', 'cinnamon']:
                point = 'colourpoint'
        elif genotype.pointgene[0] == 'cb':
            point = 'mink'
            if base != 'black':
                point = 'colourpoint'

        return [base, tortie, tabby, white, point]

    def filter(self, all, used, filter_out):
        return [x for x in all if x not in used and x not in filter_out]

    def solid(self, base, tortie, tabby, white):
        try:
            possible_prefixes = deepcopy(self.all_prefixes[base]['tortie' if tortie else 'plain']['solid'][white + '_white'])
        except:
            if tabby == 'shaded' and base == 'yellow':
                possible_prefixes = deepcopy(self.all_prefixes[base]['shaded'][white + '_white'])
            else:
                possible_prefixes = deepcopy(self.all_prefixes[base]['solid'][white + '_white'])


        possible_prefixes += self.all_prefixes['general']['any']
        if self.moons < 3:
            possible_prefixes += self.all_prefixes['general']['big']
            possible_prefixes += self.all_prefixes['general']['small']
            possible_prefixes += self.all_prefixes['general']['small']
        else:
            if self.genotype.shoulder_height > 11:
                possible_prefixes += self.all_prefixes['general']['big']
            elif self.genotype.shoulder_height < 9:
                possible_prefixes += self.all_prefixes['general']['small']

        try:
            possible_prefixes += self.all_prefixes['general'][self.phenotype.length.replace('haired', 'hair')]
        except:
            pass
        if white in ['mid', 'high']:
            possible_prefixes += self.all_prefixes['general']['white_patches']
        if tortie:
            possible_prefixes += self.all_prefixes['general']['tortie']
        if tabby and white != 'high':
            possible_prefixes += self.all_prefixes['general'][tabby.replace('shaded', 'ticked')]
        filtered = deepcopy(possible_prefixes)
        try:
            filtered = self.filter(filtered, self.used_prefixes, self.all_prefixes['filter_out'])
        except:
            filtered = self.filter(filtered, self.used_prefixes, [])

        if len(filtered) > 0:
            return choice(filtered)
        else:
            return choice(possible_prefixes)
    def tabby(self, base, tortie, tabby, white):
        try:
            possible_prefixes = deepcopy(self.all_prefixes[base]['tortie' if tortie else 'plain']['tabby'][tabby['pattern']])
        except:
            possible_prefixes = deepcopy(self.all_prefixes[base]['tabby'][tabby['pattern']])

        try:
            possible_prefixes = possible_prefixes[tabby['type']]
            if base in ['ginger', 'cream', 'blue', 'lilac', 'fawn'] and tabby['type'] == 'silver':
                try:
                    possible_prefixes += self.all_prefixes[base]['tortie' if tortie else 'plain']['tabby'][tabby['pattern']]['regular'][white + '_white']
                except:
                    possible_prefixes += self.all_prefixes[base]['tabby'][tabby['pattern']]['regular'][white + '_white']
        except:
            possible_prefixes = possible_prefixes['regular']

        if isinstance(possible_prefixes, dict):
            possible_prefixes = possible_prefixes[white + '_white']
        
        try:
            extra_prefixes = deepcopy(self.all_prefixes[base]['tortie' if tortie else 'plain']['tabby']['general'])
        except:
            extra_prefixes = deepcopy(self.all_prefixes[base]['general'])

        try:
            extra_prefixes = extra_prefixes[tabby['type']]
            if base in ['ginger', 'cream', 'blue', 'lilac', 'fawn'] and tabby['type'] == 'silver':
                try:
                    extra_prefixes += self.all_prefixes[base]['tortie' if tortie else 'plain']['tabby'][tabby['pattern']]['regular'][white + '_white']
                except:
                    extra_prefixes += self.all_prefixes[base]['tabby'][tabby['pattern']]['regular'][white + '_white']
        except:
            try:
                extra_prefixes = extra_prefixes['regular']
            except:
                pass

        if isinstance(extra_prefixes, dict):
            extra_prefixes = extra_prefixes[white + '_white']
        
        possible_prefixes += extra_prefixes
        possible_prefixes += self.all_prefixes['general']['any']
        if self.moons < 3:
            possible_prefixes += self.all_prefixes['general']['big']
            possible_prefixes += self.all_prefixes['general']['small']
            possible_prefixes += self.all_prefixes['general']['small']
        else:
            if self.genotype.shoulder_height > 11:
                possible_prefixes += self.all_prefixes['general']['big']
            elif self.genotype.shoulder_height < 9:
                possible_prefixes += self.all_prefixes['general']['small']

        try:
            possible_prefixes += self.all_prefixes['general'][self.phenotype.length.replace('haired', 'hair')]
        except:
            pass
        if white in ['mid', 'high']:
            possible_prefixes += self.all_prefixes['general']['white_patches']
        if tortie:
            possible_prefixes += self.all_prefixes['general']['tortie']
        if tabby['pattern'] and white != 'high':
            possible_prefixes += self.all_prefixes['general'][tabby['pattern']]
        filtered = deepcopy(possible_prefixes)
        try:
            filtered = self.filter(filtered, self.used_prefixes, self.all_prefixes['filter_out'])
        except:
            filtered = self.filter(filtered, self.used_prefixes, [])

        if len(filtered) > 0:
            return choice(filtered)
        else:
            return choice(possible_prefixes)
    def point(self, base, tortie, point, white):
        if white in ['mid', 'high']:
            if white == 'high' and random() < 0.75:
                if base in ['ginger', 'cream']:
                    return self.tabby(base, tortie, {'pattern': 'ticked', 'type': 'silver'}, 'high')
                else:
                    return self.solid(base, tortie, '', 'high')
            elif random() < 0.5:
                if base in ['ginger', 'cream']:
                    return self.tabby(base, tortie, {'pattern': 'ticked', 'type': 'silver'}, 'high')
                else:
                    return self.solid(base, tortie, '', 'high')

        try:
            possible_prefixes = deepcopy(self.all_prefixes[base]['tortie' if tortie else 'plain']['point'])
        except:
            possible_prefixes = deepcopy(self.all_prefixes[base]['point'])
        
        try:
            possible_prefixes = possible_prefixes[point]
        except:
            possible_prefixes = possible_prefixes['colourpoint']

        try:
            possible_prefixes = possible_prefixes[white + '_white']
        except:
            try:
                possible_prefixes = possible_prefixes['with_white']
            except:
                pass
        
        possible_prefixes += self.all_prefixes['general']['any']
        if self.moons < 3:
            possible_prefixes += self.all_prefixes['general']['big']
            possible_prefixes += self.all_prefixes['general']['small']
            possible_prefixes += self.all_prefixes['general']['small']
        else:
            if self.genotype.shoulder_height > 11:
                possible_prefixes += self.all_prefixes['general']['big']
            elif self.genotype.shoulder_height < 9:
                possible_prefixes += self.all_prefixes['general']['small']

        try:
            possible_prefixes += self.all_prefixes['general'][self.phenotype.length.replace('haired', 'hair')]
        except:
            pass
        if white in ['mid', 'high']:
            possible_prefixes += self.all_prefixes['general']['white_patches']
        if tortie:
            possible_prefixes += self.all_prefixes['general']['tortie']
        
        filtered = deepcopy(possible_prefixes)
        try:
            filtered = self.filter(filtered, self.used_prefixes, self.all_prefixes['filter_out'])
        except:
            filtered = self.filter(filtered, self.used_prefixes, [])

        if len(filtered) > 0:
            return choice(filtered)
        else:
            return choice(possible_prefixes)

    def black(self, params):
        if params[4] != 'none':
            #babies don't have points
            if self.moons == 0 and self.genotype.pointgene[0] == 'cs':
                return self.white('white')
            elif self.moons == 0 and params[4] == 'mink':
                return self.fawn(params)
            elif self.moons == 0 and params[4] == 'sepia':
                return self.cinnamon(params)

            #naming for body colour
            if (params[2]['pattern'] != '' and params[2]['type'] != 'dark') or random() < 0.25:
                if params[2]['pattern'] != '' and params[2]['type'] != 'dark':
                    params[2]['type'] = 'silver'
                if params[4] == 'colourpoint' and (self.genotype.pointgene in ['cm', 'c'] or 'masked' in self.phenotype.silvergold or (self.moons < 4 and self.genotype.fevercoat) or (self.moons > 3 and self.genotype.bleach[0] == 'lb')):
                    if params[2]['pattern'] != '' and params[2]['type'] != 'dark':
                        return self.white('silver shaded')
                    else:
                        return self.white('white')
                elif params[4] == 'colourpoint':
                    return self.fawn(params)
                elif params[4] == 'mink':
                    return self.cinnamon(params)
                else:
                    return self.chocolate(params)

            #naming for point colour

            if random() < 0.1:
                if (self.genotype.tortiepattern or params[5]) and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
                    return self.tabby('ginger', params[1], {'pattern' : params[2]['tortie_red'], 'type' : 'silver'}, params[3])
                elif self.genotype.tortiepattern and random() < 0.33:
                    return self.solid(params[0], False, params[2]['pattern'], params[3])
                else:
                    return self.solid(params[0], params[1], params[2]['pattern'], params[3])

            #overall colourpoint names
            if self.genotype.tortiepattern and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
                if params[4] == 'sepia':
                    return self.tabby('ginger', False, {'pattern' : params[2]['tortie_red'], 'type' : 'silver'}, params[3])
                else:
                    return self.point('ginger', False, 'colourpoint', params[3])
            elif self.genotype.tortiepattern and random() < 0.33:
                return self.point(params[0], False, params[4], params[3])
            else:
                return self.point(params[0], params[1], params[4], params[3])

        if params[2]['type'] == 'golden' and params[2]['pattern'] == 'ticked':
            params[0] = 'golden shaded'
            return self.golden(params)
        
        if self.genotype.tortiepattern and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
            return self.tabby('ginger', params[1], {'pattern' : params[2]['tortie_red'], 'type' : 'silver' if self.genotype.silver[0] == 'I' else 'regular'}, params[3])
            
        if params[2]['type'] == 'dark' or params[2]['pattern'] == '':
            if self.genotype.tortiepattern and random() < 0.33:
                return self.solid(params[0], False, params[2]['pattern'], params[3])
            else:
                return self.solid(params[0], params[1], params[2]['pattern'], params[3])
        if self.genotype.tortiepattern and random() < 0.33:
            return self.tabby(params[0], False, params[2], params[3])
        else:
            return self.tabby(params[0], params[1], params[2], params[3])
        
    def blue(self, params):
        if params[4] != 'none':
            #babies don't have points
            if self.moons == 0 and 'C' not in self.genotype.pointgene and params[4] != 'sepia':
                return self.white('white')
            elif self.moons == 0 and params[4] == 'sepia':
                return self.lilac(params)

            #naming for body colour
            if (params[2]['pattern'] != '' and params[2]['type'] != 'dark') or random() < 0.25:
                if params[2]['pattern'] != '' and params[2]['type'] != 'dark':
                    params[2]['type'] = 'silver'
                if self.genotype.pointgene[0] == 'cs' or 'masked' in self.phenotype.silvergold or (self.moons < 4 and self.genotype.fevercoat) or (self.moons > 3 and self.genotype.bleach[0] == 'lb'):
                    return self.white('white')
                elif params[4] == 'colourpoint':
                    return self.lilac(params)

            #naming for point colour

            elif random() < 0.1:
                if (self.genotype.tortiepattern or params[5]) and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
                    return self.tabby('cream', params[1], {'pattern' : params[2]['tortie_red'], 'type' : 'regular'}, params[3])
                elif self.genotype.tortiepattern and random() < 0.33:
                    return self.solid(params[0], False, params[2]['pattern'], params[3])
                else:
                    return self.solid(params[0], params[1], params[2]['pattern'], params[3])

            #overall colourpoint names
            elif self.genotype.tortiepattern and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
                if params[4] == 'sepia':
                    return self.tabby('cream', False, {'pattern' : params[2]['tortie_red'], 'type' : 'regular'}, params[3])
                else:
                    return self.point('cream', False, 'colourpoint', params[3])
            elif self.genotype.tortiepattern and random() < 0.33:
                return self.point(params[0], False, params[4], params[3])
            else:
                return self.point(params[0], params[1], params[4], params[3])

        if params[2]['type'] == 'golden' and params[2]['pattern'] == 'ticked':
            return self.cream(params)
        
        if self.genotype.tortiepattern and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
            return self.tabby('cream', params[1], {'pattern' : params[2]['tortie_red'], 'type' : 'regular'}, params[3])
            
        if params[2]['type'] == 'dark' or params[2]['pattern'] == '':
            if self.genotype.tortiepattern and random() < 0.33:
                return self.solid(params[0], False, params[2]['pattern'], params[3])
            else:
                return self.solid(params[0], params[1], params[2]['pattern'], params[3])
        if self.genotype.tortiepattern and random() < 0.33:
            return self.tabby(params[0], False, params[2], params[3])
        else:
            return self.tabby(params[0], params[1], params[2], params[3])
        
    def chocolate(self, params):
        if self.genotype.saturation > 4 and random() < 0.2 and params[0] not in ['black', 'cinnamon']:
            params[4] = params[4].replace('sepia', 'mink')
            return self.black(params)

        if params[4] != 'none' and params[0] != 'black':
            #babies don't have points
            if self.moons == 0 and 'C' not in self.genotype.pointgene and params[4] != 'sepia':
                return self.white('white')
            elif self.moons == 0 and params[4] == 'sepia':
                return self.fawn(params)

            #naming for body colour
            if (params[2]['pattern'] != '' and params[2]['type'] != 'dark') or random() < 0.25:
                if params[2]['pattern'] != '' and params[2]['type'] != 'dark':
                    params[2]['type'] = 'silver'
                if self.genotype.pointgene[0] == 'cs' or 'masked' in self.phenotype.silvergold or (self.moons < 4 and self.genotype.fevercoat) or (self.moons > 3 and self.genotype.bleach[0] == 'lb'):
                    return self.white('white')
                elif params[4] == 'colourpoint':
                    return self.fawn(params)
                else:
                    return self.cinnamon(params)

            #naming for point colour

            if random() < 0.1:
                if (self.genotype.tortiepattern or params[5]) and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
                    return self.tabby('ginger', params[1], {'pattern' : params[2]['tortie_red'], 'type' : 'silver'}, params[3])
                elif self.genotype.tortiepattern and random() < 0.33:
                    return self.solid(params[0], False, params[2]['pattern'], params[3])
                else:
                    return self.solid(params[0], params[1], params[2]['pattern'], params[3])

            #overall colourpoint names
            if self.genotype.tortiepattern and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
                if params[4] == 'sepia':
                    return self.tabby('ginger', False, {'pattern' : params[2]['tortie_red'], 'type' : 'silver'}, params[3])
                else:
                    return self.point('ginger', False, 'colourpoint', params[3])
            elif self.genotype.tortiepattern and random() < 0.33:
                return self.point(params[0], False, params[4], params[3])
            else:
                return self.point(params[0], params[1], params[4], params[3])

        if params[2]['type'] == 'golden' and params[2]['pattern'] == 'ticked':
            params[0] = 'golden shaded'
            return self.golden(params)
        
        if self.genotype.tortiepattern and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
            return self.tabby('ginger', params[1], {'pattern' : params[2]['tortie_red'], 'type' : 'silver' if self.genotype.silver[0] == 'I' else 'regular'}, params[3])
            
        if params[2]['type'] == 'dark' or params[2]['pattern'] == '':
            if self.genotype.tortiepattern and random() < 0.33:
                return self.solid(params[0], False, params[2]['pattern'], params[3])
            else:
                return self.solid(params[0], params[1], params[2]['pattern'], params[3])
        if self.genotype.tortiepattern and random() < 0.33:
            return self.tabby(params[0], False, params[2], params[3])
        else:
            return self.tabby(params[0], params[1], params[2], params[3])
        
    def lilac(self, params):
        if random() < 0.1:
            self.purple(params)

        if self.genotype.saturation > 4 and random() < 0.2 and params[0] not in ['blue', 'fawn']:
            params[4] = params[4].replace('sepia', 'mink')
            return self.blue(params)

        if params[4] != 'none' and params[0] not in ['blue']:
            #babies don't have points
            if self.moons == 0 and 'C' not in self.genotype.pointgene and params[4] != 'sepia':
                return self.white('white')
            elif self.moons == 0 and params[4] == 'sepia':
                return self.lilac(params)

            #naming for body colour
            elif (params[2]['pattern'] != '' and params[2]['type'] != 'dark') or random() < 0.25:
                if params[2]['pattern'] != '' and params[2]['type'] != 'dark':
                    params[2]['type'] = 'silver'
                if self.genotype.pointgene[0] == 'cs' or 'masked' in self.phenotype.silvergold or (self.moons < 4 and self.genotype.fevercoat) or (self.moons > 3 and self.genotype.bleach[0] == 'lb'):
                    return self.white('white')

            #naming for point colour

            elif random() < 0.1:
                if (self.genotype.tortiepattern or params[5]) and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
                    return self.tabby('cream', params[1], {'pattern' : params[2]['tortie_red'], 'type' : 'regular'}, params[3])
                elif self.genotype.tortiepattern and random() < 0.33:
                    return self.solid(params[0], False, params[2]['pattern'], params[3])
                else:
                    return self.solid(params[0], params[1], params[2]['pattern'], params[3])

            #overall colourpoint names
            elif self.genotype.tortiepattern and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
                if params[4] == 'sepia':
                    return self.tabby('cream', False, {'pattern' : params[2]['tortie_red'], 'type' : 'regular'}, params[3])
                else:
                    return self.point('cream', False, 'colourpoint', params[3])
            elif self.genotype.tortiepattern and random() < 0.33:
                return self.point(params[0], False, params[4], params[3])
            else:
                return self.point(params[0], params[1], params[4], params[3])

        if params[2]['type'] == 'golden' and params[2]['pattern'] == 'ticked':
            return self.cream(params)
        
        if self.genotype.tortiepattern and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
            return self.tabby('cream', params[1], {'pattern' : params[2]['tortie_red'], 'type' : 'regular'}, params[3])
            
        if params[2]['type'] == 'dark' or params[2]['pattern'] == '':
            if self.genotype.tortiepattern and random() < 0.33:
                return self.solid(params[0], False, params[2]['pattern'], params[3])
            else:
                return self.solid(params[0], params[1], params[2]['pattern'], params[3])
        if self.genotype.tortiepattern and random() < 0.33:
            return self.tabby(params[0], False, params[2], params[3])
        else:
            return self.tabby(params[0], params[1], params[2], params[3])
        
    def cinnamon(self, params):
        if self.genotype.saturation > 4 and random() < 0.2 and params[0] not in ['black', 'chocolate']:
            return self.chocolate(params)
        if random() < 0.1:
            return self.red(params)

        if params[4] != 'none' and params[0] not in ['black', 'chocolate']:
            #babies don't have points
            if self.moons == 0 and 'C' not in self.genotype.pointgene:
                return self.white('white')

            #naming for body colour
            if (params[2]['pattern'] != '' and params[2]['type'] != 'dark') or random() < 0.25:
                if params[2]['pattern'] != '' and params[2]['type'] != 'dark':
                    params[2]['type'] = 'silver'
                if (self.genotype.pointgene[0] != 'C' and self.genotype.pointgene != ['cb', 'cb']) or 'masked' in self.phenotype.silvergold or (self.moons < 4 and self.genotype.fevercoat) or (self.moons > 3 and self.genotype.bleach[0] == 'lb'):
                    return self.white('white')
                else:
                    return self.fawn(params)

            #naming for point colour

            if random() < 0.1:
                if (self.genotype.tortiepattern or params[5]) and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
                    return self.tabby('ginger', params[1], {'pattern' : params[2]['tortie_red'], 'type' : 'silver'}, params[3])
                elif self.genotype.tortiepattern and random() < 0.33:
                    return self.solid(params[0], False, params[2]['pattern'], params[3])
                else:
                    return self.solid(params[0], params[1], params[2]['pattern'], params[3])

            #overall colourpoint names
            if self.genotype.tortiepattern and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
                if not((self.genotype.pointgene[0] != 'C' and self.genotype.pointgene != ['cb', 'cb']) or 'masked' in self.phenotype.silvergold or (self.moons < 4 and self.genotype.fevercoat) or (self.moons > 3 and self.genotype.bleach[0] == 'lb')):
                    return self.tabby('ginger', False, {'pattern' : params[2]['tortie_red'], 'type' : 'silver'}, params[3])
                else:
                    return self.point('ginger', False, 'colourpoint', params[3])
            elif self.genotype.tortiepattern and random() < 0.33:
                return self.point(params[0], False, params[4], params[3])
            else:
                return self.point(params[0], params[1], params[4], params[3])

        if params[2]['type'] == 'golden' and params[2]['pattern'] == 'ticked':
            params[0] = 'golden shaded'
            return self.golden(params)
        
        if self.genotype.tortiepattern and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
            return self.tabby('ginger', params[1], {'pattern' : params[2]['tortie_red'], 'type' : 'silver' if self.genotype.silver[0] == 'I' else 'regular'}, params[3])
            
        if params[2]['type'] == 'dark' or params[2]['pattern'] == '':
            if self.genotype.tortiepattern and random() < 0.33:
                return self.solid(params[0], False, params[2]['pattern'], params[3])
            else:
                return self.solid(params[0], params[1], params[2]['pattern'], params[3])
        if self.genotype.tortiepattern and random() < 0.33:
            return self.tabby(params[0], False, params[2], params[3])
        else:
            return self.tabby(params[0], params[1], params[2], params[3])
        
    def fawn(self, params):
        if self.genotype.saturation > 4 and random() < 0.2 and params[0] not in ['black', 'chocolate', 'cinnamon', 'blue', 'lilac']:
            return self.lilac(params)
        if random() < 0.1:
            return self.pink(params)

        if params[4] != 'none' and params[0] not in ['black', 'chocolate', 'cinnamon', 'blue', 'lilac']:
            #babies don't have points
            if self.moons == 0 and 'C' not in self.genotype.pointgene:
                return self.white('white')

            #naming for body colour
            if (params[2]['pattern'] != '' and params[2]['type'] != 'dark') or random() < 0.25:
                return self.white('white')

            #naming for point colour

            if random() < 0.1:
                if (self.genotype.tortiepattern or params[5]) and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
                    return self.tabby('cream', params[1], {'pattern' : params[2]['tortie_red'], 'type' : 'regular'}, params[3])
                elif self.genotype.tortiepattern and random() < 0.33:
                    return self.solid(params[0], False, params[2]['pattern'], params[3])
                else:
                    return self.solid(params[0], params[1], params[2]['pattern'], params[3])

            #overall colourpoint names
            if self.genotype.tortiepattern and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
                if not((self.genotype.pointgene[0] != 'C' and self.genotype.pointgene != ['cb', 'cb']) or 'masked' in self.phenotype.silvergold or (self.moons < 4 and self.genotype.fevercoat) or (self.moons > 3 and self.genotype.bleach[0] == 'lb')):
                    return self.tabby('cream', False, {'pattern' : params[2]['tortie_red'], 'type' : 'regular'}, params[3])
                else:
                    return self.point('cream', False, 'colourpoint', params[3])
            elif self.genotype.tortiepattern and random() < 0.33:
                return self.point(params[0], False, params[4], params[3])
            else:
                return self.point(params[0], params[1], params[4], params[3])

        if params[2]['type'] == 'golden' and params[2]['pattern'] == 'ticked':
            return self.cream(params)
        
        if self.genotype.tortiepattern and (random() < 0.25 or (len(self.genotype.tortiepattern) > 2 and 'rev' not in self.genotype.tortiepattern[0])):
            return self.tabby('cream', params[1], {'pattern' : params[2]['tortie_red'], 'type' : 'regular'}, params[3])
            
        if params[2]['type'] == 'dark' or params[2]['pattern'] == '':
            if self.genotype.tortiepattern and random() < 0.33:
                return self.solid(params[0], False, params[2]['pattern'], params[3])
            else:
                return self.solid(params[0], params[1], params[2]['pattern'], params[3])
        if self.genotype.tortiepattern and random() < 0.33:
            return self.tabby(params[0], False, params[2], params[3])
        else:
            return self.tabby(params[0], params[1], params[2], params[3])
        
    def red(self, params):
        if params[4]:
            #babies don't have points
            if self.moons == 0 and 'C' not in self.genotype.pointgene:
                return self.white('white')
            
            if random() > 0.9:
                return self.point('red', False, params[4], params[3])
        
        self.solid('red', False, params[2]['pattern'], params[3])

    def ginger(self, params):
        if self.genotype.ruftype == 'rufoused' and random() < 0.2:
            self.red(params)
        if self.genotype.ruftype == 'low' and random() < 0.2:
            self.golden(params)

        if params[4]:
            #babies don't have points
            if self.moons == 0 and 'C' not in self.genotype.pointgene:
                return self.white('white')
            #naming for body colour
            if random() < 0.25:
                return self.white('white')

            #naming for point colour

            if random() < 0.1:
                return self.tabby(params[0], params[1], params[2], params[3])

            #overall colourpoint names
            else:
                return self.point(params[0], params[1], params[4], params[3])
            
        return self.tabby(params[0], params[1], params[2], params[3])

    def golden(self, params):
        if params[4]:
            #babies don't have points
            if self.moons == 0 and 'C' not in self.genotype.pointgene:
                return self.white('white')

            if random() > 0.9:
                return self.point('yellow', False, params[4], params[3])
        
        if params[0] == 'golden shaded':
            return self.solid('yellow', False, 'shaded', params[3])

        self.solid('yellow', False, params[2]['pattern'], params[3])

    def cream(self, params):
        if self.genotype.ruftype == 'rufoused' and random() < 0.2:
            self.golden(params)
        if self.genotype.ruftype != 'rufoused' and random() < 0.1:
            self.pink(params)

        if params[4]:
            #babies don't have points
            if self.moons == 0 and 'C' not in self.genotype.pointgene:
                return self.white('white')
            
            #naming for body colour
            if random() < 0.25:
                return self.white('white')

            #naming for point colour
            if random() < 0.1:
                return self.tabby(params[0], params[1], params[2], params[3])

            #overall colourpoint names
            else:
                return self.point(params[0], params[1], params[4], params[3])
            
        return self.tabby(params[0], params[1], params[2], params[3])

    def purple(self, params):
        if params[4]:
            #babies don't have points
            if self.moons == 0 and 'C' not in self.genotype.pointgene:
                return self.white('white')

            if random() > 0.9:
                return self.point('purple', False, params[4], params[3])
        
        self.solid('purple', False, params[2]['pattern'], params[3])

    def pink(self, params):
        if params[4]:
            #babies don't have points
            if self.moons == 0 and 'C' not in self.genotype.pointgene:
                return self.white('white')
                
            if random() > 0.9:
                return self.point('pink', False, params[4], params[3])
        
        self.solid('pink', False, params[2]['pattern'], params[3])

    def white(self, base):
        if base == 'silver shaded' and random() > 0.33:
            possible_prefixes = self.all_prefixes['white']['shaded']
        else:
            possible_prefixes = self.all_prefixes['white']['solid']
        
        filtered = deepcopy(possible_prefixes)
        try:
            filtered = self.filter(filtered, self.used_prefixes, self.all_prefixes['filter_out'])
        except:
            filtered = self.filter(filtered, self.used_prefixes, [])

        if len(filtered) > 0:
            return choice(filtered)
        else:
            return choice(possible_prefixes)