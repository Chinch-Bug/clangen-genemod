from random import choice, choices, randint, random
import json
from scripts.cat.breed_functions import breed_functions
from scripts.clan_package.settings import get_clan_setting
from scripts.special_dates import SpecialDate, is_today
from operator import xor
import math


class Genotype:
    def __init__(self, odds, ban_genes=True, spec=None):
        self.odds = odds
        self.ban_genes = ban_genes
        self.chimerapattern = None

        self.fevercoat = False

        self.april_fools = {}
        
        self.furLength = ["", ""]
        self.longtype = choice(self.odds["longtype"])
        self.eumelanin = ["", ""]
        self.sexgene = ["", ""]
        self.specialred = None
        self.tortiepattern = None
        self.pseudomerle = False
        self.merlepattern = None
        self.brindledbi = False
        self.sex = ""
        self.dilute = ["", ""]
        self.white = ["", ""]
        self.whitegrade = randint(1, 5)
        self.white_pattern = []
        self.vitiligo = False
        self.deaf = False
        self.pointgene = ["", ""]
        self.silver = ["", ""]
        self.agouti = ["", ""]
        self.pangere = None
        self.blacknose = False
        self.rednose = False
        self.mack = ["", ""]
        self.ticked = ["", ""]
        self.breakthrough = False
        self.sheeted = False

        self.wirehair = ["wh", "wh"]
        self.laperm = ["lp", "lp"]
        self.cornish = ["R", "R"]
        self.urals = ["Ru", "Ru"]
        self.tenn = ["Tr", "Tr"]
        self.fleece = ["Fc", "Fc"]
        self.sedesp = ["Hr", "Hr"]
        self.ruhr = ["hrbd", "hrbd"]
        self.ruhrmod = ""
        self.lykoi = ["Ly", "Ly"]

        self.pinkdilute = ["Dp", "Dp"]
        self.dilutemd = ["dm", "dm"]
        self.ext = ["E", "E"]
        self.corin = ["N", "N"]
        self.karp = ["k", "k"]
        self.bleach = ["Lb", "Lb"]
        self.ghosting = ["gh", "gh"]
        self.satin = ["St", "St"]
        self.glitter = ["Gl", "Gl"]

        self.curl = ["cu", "cu"]
        self.fold = ["fd", "fd"]
        self.fourear = ["Dup", "Dup"]
        self.manx = ["ab", "ab"]
        self.manxtype = choice(["long", "most", "most", "stubby", "stubby", "stubby", "stubby", "stubby", "stubby", "stumpy", "stumpy", "stumpy", "stumpy", "stumpy", "stumpy", "stumpy", "stumpy", "riser", "riser", "riser", "riser", "riser", "riser", "riser", "riser", "riser", "rumpy", "rumpy", "rumpy", "rumpy", "rumpy", "rumpy", "rumpy", "rumpy", "rumpy", "rumpy"])
        self.kab = ["Kab", "Kab"]
        self.toybob = ["tb", "tb"]
        self.jbob = ["Jb", "Jb"]
        self.kub = ["kub", "kub"]
        self.ring = ["Rt", "Rt"]
        self.munch = ["mk", "mk"]
        self.poly = ["pd", "pd"]
        self.pax3 = ["NoDBE", "NoDBE"]

        self.wideband = ""
        self.wbtype = ""
        self.wbsum = 0

        self.saturation = choice(odds['saturation'])

        self.rufousing = ""
        self.ruftype = ""
        self.rufsum = 0

        self.unders_ruf = ""
        self.unders_ruftype = ""
        self.unders_rufsum = 0

        self.bengal = ""
        self.bengtype = ""
        self.bengsum = 0

        self.sokoke = ""
        self.soktype = ""
        self.soksum = 0

        self.spotted = ""
        self.spottype = ""
        self.spotsum = 0

        self.tickgenes = ""
        self.ticktype = ""
        self.ticksum = 0

        self.body_ranges = odds['body_ranges']
        self.height_ranges = odds['height_ranges']

        def getindexes(m, size):
            inds = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
            
            for i in range(0, size):
                for j in range(0, i+1):
                    inds[i] += m[j]
            
            return inds
        self.body_indexes = getindexes(self.body_ranges, 7)
        self.height_indexes = getindexes(self.height_ranges, 10)

        self.body_value = 0
        self.height_value = 0
        self.shoulder_height = 0
        self.body_label = ""
        self.height_label = ""
        self.growth_pattern = ""

        self.refraction = False
        self.pigmentation = False

        self.lefteye = ""
        self.righteye = ""
        self.lefteyetype = "Error"
        self.righteyetype = "Error"

        self.extraeye = None
        self.extraeyetype = ""
        self.extraeyecolour = ""

        self.breeds = {}
        self.somatic = {}

    def __getitem__(self, name):
        return getattr(self, name)
    
    def fromJSON(self, jsonstring):
        self.april_fools = jsonstring.get("april_fools", {})
        self.fevercoat = jsonstring.get("fevercoat", False)
        self.furLength = jsonstring["furLength"]
        self.eumelanin = jsonstring["eumelanin"]
        self.sexgene = jsonstring["sexgene"]
        self.tortiepattern = jsonstring.get("tortiepattern", None)
        if self.tortiepattern and not isinstance(self.tortiepattern, list):
            self.tortiepattern = [self.tortiepattern]
        self.brindledbi = jsonstring["brindledbi"]

        self.specialred = jsonstring['specialred']
        self.merlepattern = jsonstring.get('merlepattern', None)
        self.pseudomerle = jsonstring.get('pseudomerle')
        self.longtype = jsonstring["longtype"]

        try:
            self.sex = jsonstring['sex']
        except:
            self.sex = jsonstring['gender']
        self.dilute = jsonstring["dilute"]
        self.white = jsonstring["white"]
        self.whitegrade = jsonstring["whitegrade"]
        self.vitiligo = jsonstring["vitiligo"]
        self.pointgene = jsonstring["pointgene"]
        self.silver = jsonstring["silver"]
        self.agouti = jsonstring["agouti"]
        self.pangere = jsonstring.get("pangere")
        self.blacknose = jsonstring.get("blacknose", False)
        self.rednose = jsonstring.get("rednose", False)
        self.mack = jsonstring["mack"]
        self.ticked = jsonstring["ticked"]
        self.breakthrough = jsonstring["breakthrough"]
        self.sheeted = jsonstring.get("sheeted", False)

        self.wirehair = jsonstring["wirehair"]
        self.laperm = jsonstring["laperm"]
        self.cornish = jsonstring["cornish"]
        self.urals = jsonstring["urals"]
        self.tenn = jsonstring["tenn"]
        self.fleece = jsonstring["fleece"]
        self.sedesp = jsonstring["sedesp"]
        self.ruhr = jsonstring["ruhr"]
        self.ruhrmod = jsonstring["ruhrmod"]
        self.lykoi = jsonstring["lykoi"]
    
        self.pinkdilute = jsonstring["pinkdilute"]
        self.dilutemd = jsonstring["dilutemd"]
        self.ext = jsonstring["ext"]
        self.corin = jsonstring.get("corin", ['N', 'N'])
        self.karp = jsonstring["karp"]
        self.bleach = jsonstring["bleach"]
        self.ghosting = jsonstring["ghosting"]
        self.satin = jsonstring["satin"]
        self.glitter = jsonstring["glitter"]
    
        self.curl = jsonstring["curl"]
        self.fold = jsonstring["fold"]
        self.fourear = jsonstring.get("fourear", ["Dup", "Dup"])
        self.manx = jsonstring["manx"]
        self.manxtype = jsonstring["manxtype"]
        self.kab = jsonstring["kab"]
        self.toybob = jsonstring["toybob"]
        self.jbob = jsonstring["jbob"]
        self.kub = jsonstring["kub"]
        self.ring = jsonstring["ring"]
        self.munch = jsonstring["munch"]
        self.poly = jsonstring["poly"]
        self.pax3 = jsonstring.get("pax3", ['NoDBE', 'NoDBE'])

        self.wideband = jsonstring["wideband"]
        self.saturation = jsonstring.get("saturation", 3)
        self.rufousing = jsonstring["rufousing"]
        self.unders_ruf = jsonstring.get("unders_ruf", "")
        self.bengal = jsonstring["bengal"]
        self.sokoke = jsonstring["sokoke"]
        self.spotted = jsonstring["spotted"]
        self.tickgenes = jsonstring["tickgenes"]

        if isinstance(jsonstring["refraction"], int):
            self.refraction = jsonstring["refraction"]
            self.pigmentation = jsonstring["pigmentation"]

        self.lefteye = jsonstring["lefteye"]
        self.righteye = jsonstring["righteye"]
        self.lefteyetype = jsonstring["lefteyetype"]
        self.righteyetype = jsonstring["righteyetype"]
        
        self.extraeye = jsonstring["extraeye"]
        self.extraeyetype = jsonstring["extraeyetype"]
        self.extraeyecolour = jsonstring["extraeyecolour"]

        self.breeds = json.loads(jsonstring.get("breeds", "{}")) if isinstance(jsonstring.get("breeds", "{}"), str) else jsonstring.get("breeds", {})
        self.somatic = json.loads(jsonstring.get("somatic", "{}")) if isinstance(jsonstring.get("somatic", "{}"), str) else jsonstring.get("somatic", {})
        self.body_value = jsonstring.get("body_type", randint(1, sum(self.body_ranges)))
        self.height_value = jsonstring.get("height", randint(1, sum(self.height_ranges)))
        self.shoulder_height = jsonstring.get("shoulder_height", 0)
        self.body_label = jsonstring.get("body_type_label", '')
        self.growth_pattern = jsonstring.get("growth_pattern", "average")

        self.GeneSort()
        self.PolyEval()
        self.EyeColourName()

    def toJSON(self):
        return {
            "fevercoat" : self.fevercoat,
            "furLength": self.furLength,
            "longtype": self.longtype,
            "eumelanin": self.eumelanin,
            "sexgene" : self.sexgene,
            "specialred" : self.specialred,
            "tortiepattern" : self.tortiepattern,
            "brindledbi" : self.brindledbi,

            "pseudomerle" : self.pseudomerle,
            "merlepattern" : self.merlepattern,

            "sex": self.sex,
            "dilute": self.dilute,
            "white" : self.white,
            "whitegrade" : self.whitegrade,
            "vitiligo" : self.vitiligo,
            "pointgene" : self.pointgene,
            "silver" : self.silver,
            "agouti" : self.agouti,
            "pangere" : self.pangere,
            "blacknose" : self.blacknose,
            "rednose" : self.rednose,
            "mack" : self.mack,
            "ticked" : self.ticked,
            "breakthrough" : self.breakthrough,
            "sheeted" : self.sheeted,

            "wirehair" : self.wirehair,
            "laperm" : self.laperm,
            "cornish" : self.cornish,
            "urals" : self.urals,
            "tenn" : self.tenn,
            "fleece" : self.fleece,
            "sedesp" : self.sedesp,
            "ruhr" : self.ruhr,
            "ruhrmod" : self.ruhrmod,
            "lykoi" : self.lykoi,

            "pinkdilute" : self.pinkdilute,
            "dilutemd" : self.dilutemd,
            "ext" : self.ext,
            "corin" : self.corin,
            "karp" : self.karp,
            "bleach" : self.bleach,
            "ghosting" : self.ghosting,
            "satin" : self.satin,
            "glitter" : self.glitter,

            "curl" : self.curl,
            "fold" : self.fold,
            "fourear": self.fourear,
            "manx" : self.manx,
            "manxtype" : self.manxtype,
            "kab" : self.kab,
            "toybob" : self.toybob,
            "jbob" : self.jbob,
            "kub" : self.kub,
            "ring" : self.ring,
            "munch" : self.munch,
            "poly" : self.poly,
            "pax3" : self.pax3,

            "wideband" : self.wideband,
            "saturation" : self.saturation,
            "rufousing" : self.rufousing,
            "unders_ruf": self.unders_ruf,
            "bengal" : self.bengal,
            "sokoke" : self.sokoke,
            "spotted" : self.spotted,
            "tickgenes" : self.tickgenes,
            "refraction" :self.refraction,
            "pigmentation" : self.pigmentation,
            
            "lefteye" : self.lefteye,
            "righteye" : self.righteye,
            "lefteyetype" :self.lefteyetype,
            "righteyetype" : self.righteyetype,
            
            "extraeye" : self.extraeye,
            "extraeyetype" :self.extraeyetype,
            "extraeyecolour" : self.extraeyecolour,

            "body_type" : self.body_value,
            "body_type_label" : self.body_label,
            "height" : self.height_value,
            "shoulder_height" : self.shoulder_height,
            "growth_pattern": self.growth_pattern,

            "breeds" : self.breeds,
            "somatic" : self.somatic,
            "april_fools" : self.april_fools
        }
    
    def AprilFools(self):
        if is_today(SpecialDate.APRIL_FOOLS):
            self.april_fools = {
                "danish_green" : ["dg", "dg"],
                "polycaudal" : ["pc", "pc"],
                "rainbow_eyes" : ["NoDRE", "NoDRE"],
                "black_spotting" : ["bs", "bs"],
                "peacock_blue" : ["pb", "pb"],
            }
            for i in range(2):
                if self.odds["green"] > 0 and random() < (1/self.odds["green"]):
                    self.april_fools["danish_green"][i] = "Dg"
                if self.odds["polycaudal"] > 0 and random() < (1/self.odds["polycaudal"]):
                    self.april_fools["polycaudal"][i] = "Pc"
                if self.odds["rainbow_eyes"] > 0 and random() < (1/self.odds["rainbow_eyes"]):
                    self.april_fools["rainbow_eyes"][i] = choice(["DREmin", "DREfull"])
                if self.odds["black_spotting"] > 0 and random() < (1/self.odds["black_spotting"]):
                    self.april_fools["black_spotting"][i] = "Bs"
                if self.odds["peacock_blue"] > 0 and random() < (1/self.odds["peacock_blue"]):
                    self.april_fools["peacock_blue"][i] = "Pb"
            for key in ["danish_green", "polycaudal", "black_spotting", "peacock_blue"]:
                if self.april_fools[key][0].islower() and self.april_fools[key][1].islower():
                    del self.april_fools[key]
            if self.april_fools["rainbow_eyes"][0] == "NoDRE" and self.april_fools["rainbow_eyes"][1] == "NoDRE":
                del self.april_fools["rainbow_eyes"]

    def CommonGen(self, special=None):

        if self.odds["vitiligo"] > 0 and randint(1, self.odds["vitiligo"]) == 1:
            self.vitiligo = True

        self.GenerateBody()

        self.AprilFools()

        a = randint(1, 4)

        if a == 1:
            self.ruhrmod = ["hi", "hi"]
        elif a == 4:
            self.ruhrmod = ["ha", "ha"]
        else:
            self.ruhrmod = ["hi", "ha"]

        # FUR LENGTH

        for i in range(2):
            if self.odds["longhair"] > 0 and randint(1, self.odds["longhair"]) == 1:
                self.furLength[i] = "l"
            else:
                self.furLength[i] = "L"
        
        # RED GENE

        if self.odds['X monosomy'] > 0 and randint(1, self.odds['X monosomy']) == 1:
            self.sexgene = [""]
        elif self.odds['XXX/XXY'] > 0 and randint(1, self.odds['XXX/XXY']) == 1:
            self.sexgene = ["", "", ""]
        else:
            self.sexgene = ["", ""]

        for i in range(len(self.sexgene)):
            if self.odds["red"] > 0 and randint(1, self.odds["red"]) == 1:
                self.sexgene[i] = "O"
            else:
                self.sexgene[i] = "o"

        if (random() < 0.5 and special != "fem" and len(self.sexgene) > 1) or special == "masc":
            self.sexgene[-1] = "Y"
            self.sex = "tom"
        else:
            self.sex = "molly"

        if self.odds['brindled_bicolour'] > 0 and randint(1, self.odds['brindled_bicolour']) == 1:
            self.brindledbi = True
        if self.odds['pseudo_merle'] > 0 and randint(1, self.odds['pseudo_merle']) == 1:
            self.pseudomerle = True

        if (random() < 0.05):
            self.specialred = choice(['cameo', 'cameo', 'cameo', 'cameo', 'cameo', 'cameo', 'cameo', 'cameo',
                                     'cameo', 'cameo', 'blue-red', 'blue-tipped', 'blue-tipped', 'blue-tipped', 'cinnamon'])

        # DILUTE

        for i in range(2):
            if self.odds["dilute"] > 0 and randint(1, self.odds["dilute"]) == 1:
                self.dilute[i] = "d"
            else:
                self.dilute[i] = "D"

        # SILVER

            if self.odds["silver"] > 0 and randint(1, self.odds["silver"]) == 1:
                self.silver[i] = "I"
            else:
                self.silver[i] = "i"

        # MACKEREL
            if self.odds["blotched"] > 0 and randint(1, self.odds["blotched"]) == 1:
                self.mack[i] = "mc"
            else:
                self.mack[i] = "Mc"

        # TICKED
            if self.odds["ticked"] > 0 and randint(1, self.odds["ticked"]) == 1:
                self.ticked[i] = "Ta"
            else:
                self.ticked[i] = "ta"

        # DOUBLE EARS
            if self.odds["four_ears"] > 0 and randint(1, self.odds["four_ears"]) == 1:
                self.fourear[i] = "dup"

        if self.odds["breakthrough"] > 0 and randint(1, self.odds["breakthrough"]) == 1:
            self.breakthrough = True

        if self.odds["dense_blotched"] > 0 and randint(1, self.odds["dense_blotched"]) == 1:
            self.sheeted = True

        self.pangere = choice([None, None,
                              "pangere small 1", "pangere small 1", "pangere small 1",
                               "pangere small 2", "pangere small 2", "pangere small 2",
                               "pangere medium 1", "pangere medium 2", "pangere medium 1 + tail"])

        self.rednose = random() < 0.25
        self.blacknose = random() < 0.005

        self.unders_ruf = ''
        self.unders_rufsum = 0

        for i in range(0, 4):
            self.unders_ruf += choice(self.odds["rufousing"])
            self.unders_rufsum += int(self.unders_ruf[i])

    def Generator(self, special=None, kittypet=False):
        if kittypet and self.odds["kittypet_breed"] > 0 and randint(1, self.odds["kittypet_breed"]) == 1:
            return self.BreedGenerator(special)
        elif self.odds["other_breed"] > 0 and randint(1, self.odds["other_breed"]) == 1:
            return self.BreedGenerator(special)

        self.CommonGen(special)
        
        # EUMELANIN

        for i in range(2):
            if self.odds["cinnamon"] > 0 and randint(1, self.odds["cinnamon"]) == 1:
                self.eumelanin[i] = "bl"
            elif self.odds["chocolate"] > 0 and randint(1, self.odds["chocolate"]) == 1:
                self.eumelanin[i] = "b"
            else:
                self.eumelanin[i] = "B"

        # WHITE   
            if self.odds["birman gloving"] > 0 and randint(1, self.odds["birman gloving"]) == 1:
                self.white[i] = "wg"
            elif self.odds["thai white"] > 0 and randint(1, self.odds["thai white"]) == 1:
                self.white[i] = "wt"
            elif self.odds["salmiak"] > 0 and randint(1, self.odds["salmiak"]) == 1:
                self.white[i] = "wsal"
            elif self.odds["dominant white"] > 0 and randint(1, self.odds["dominant white"]) == 1:
                self.white[i] = "W"
            elif self.odds["white spotting"] > 0 and randint(1, self.odds["white spotting"]) == 1:
                self.white[i] = "ws"
            else:
                self.white[i] = "w"

        # ALBINO

            if self.odds["albino"] > 0 and randint(1, self.odds["albino"]) == 1 and not self.ban_genes:
                self.pointgene[i] = "c"
            elif self.odds["mocha"] > 0 and randint(1, self.odds["mocha"]) == 1:
                self.pointgene[i] = "cm"
            elif self.odds["sepia"] > 0 and randint(1, self.odds["sepia"]) == 1:
                self.pointgene[i] = "cb"
            elif self.odds["colourpoint"] > 0 and randint(1, self.odds["colourpoint"]) == 1:
                self.pointgene[i] = "cs"
            else:
                self.pointgene[i] = "C"

        # AGOUTI

            if self.odds["charcoal"] > 0 and randint(1, self.odds["charcoal"]) == 1:
                self.agouti[i] = "Apb"
            elif self.odds["solid"] > 0 and randint(1, self.odds["solid"]) == 1:
                self.agouti[i] = "a"
            else:
                self.agouti[i] = "A"

        # YORK, WIREHAIR, LAPERM, CORNISH, URAL, TENN, FLEECE

        for i in range(2):
            if self.odds["wirehair"] > 0 and randint(1, self.odds["wirehair"]) == 1:
                self.wirehair[i] = "Wh"
            if self.odds["laperm"] > 0 and randint(1, self.odds["laperm"]) == 1:
                self.laperm[i] = "Lp"
            if self.odds["cornish"] > 0 and randint(1, self.odds["cornish"]) == 1:
                self.cornish[i] = "r"
            if self.odds["urals"] > 0 and randint(1, self.odds["urals"]) == 1:
                self.urals[i] = "ru"
            if self.odds["tenn"] > 0 and randint(1, self.odds["tenn"]) == 1:
                self.tenn[i] = "tr"
            if self.odds["fleece"] > 0 and randint(1, self.odds["fleece"]) == 1:
                self.fleece[i] = "fc"
            
        
        #SELKIRK/DEVON/HAIRLESS
    
            if self.odds["canadian hairless"] > 0 and randint(1, self.odds["canadian hairless"]) == 1:
                self.sedesp[i] = "hr"
            elif self.odds["devon"] > 0 and randint(1, self.odds["devon"]) == 1:
                self.sedesp[i] = "re"
            elif self.odds["selkirk"] > 0 and randint(1, self.odds["selkirk"]) == 1:
                self.sedesp[i] = "Se"


        #ruhr + ruhrmod + lykoi
            if self.odds["russian hairless"] > 0 and randint(1, self.odds["russian hairless"]) == 1 and not self.ban_genes:
                self.ruhr[i] = "Hrbd"
            if self.odds["lykoi"] > 0 and randint(1, self.odds["lykoi"]) == 1 and not self.ban_genes:
                self.lykoi[i] = "ly"

        # pinkdilute + dilutemd

        for i in range(2):
            if self.odds["pink-eyed dilute"] > 0 and randint(1, self.odds["pink-eyed dilute"]) == 1 and not self.ban_genes:
                self.pinkdilute[i] = "dp"
            if self.odds["dilute modifier"] > 0 and randint(1, self.odds["dilute modifier"]) == 1:
                self.dilutemd[i] = "Dm"

        # ext

            if self.odds["grizzle"] > 0 and randint(1, self.odds["grizzle"]) == 1:
                self.ext[i] = "Eg"
            elif self.odds["carnelian"] > 0 and randint(1, self.odds["carnelian"]) == 1:
                self.ext[i] = "ec"
            elif self.odds["russet"] > 0 and randint(1, self.odds["russet"]) == 1:
                self.ext[i] = "er"
            elif self.odds["amber"] > 0 and randint(1, self.odds["amber"]) == 1:
                self.ext[i] = "ea"

        #sunshine

            if self.odds["sunshine"] > 0 and randint(1, self.odds["sunshine"]) == 1:
                self.corin[i] = "sh" #sunSHine
            elif self.odds["extreme sunshine"] > 0 and randint(1, self.odds["extreme sunshine"]) == 1:
                self.corin[i] = "sg" #Siberian Gold / extreme sunshine
            elif self.odds["copper"] > 0 and randint(1, self.odds["copper"]) == 1:
                self.corin[i] = "fg" #Flaxen Gold
            else:
                self.corin[i] = "N" #No

        # karp + bleach + ghosting + satin + glitter

            if self.odds["karpati"] > 0 and randint(1, self.odds["karpati"]) == 1:
                self.karp[i] = "K"
            if self.odds["bleaching"] > 0 and randint(1, self.odds["bleaching"]) == 1:
                self.bleach[i] = "lb"
            if self.odds["ghosting"] > 0 and randint(1, self.odds["ghosting"]) == 1:
                self.ghosting[i] = "Gh"
            if self.odds["satin"] > 0 and randint(1, self.odds["satin"]) == 1:
                self.satin[i] = "st"
            if self.odds["glitter"] > 0 and randint(1, self.odds["glitter"]) == 1:
                self.glitter[i] = "gl"

        # curl + fold

            if self.odds["curl"] > 0 and randint(1, self.odds["curl"]) == 1:
                self.curl[i] = "Cu"

        if self.odds["fold"] > 0 and randint(1, self.odds["fold"]) == 1 and not self.ban_genes:
            self.fold[0] = "Fd"

        #  manx + kab + toybob + jbob + kub + ring

        if self.odds["american bobtail"] > 0 and randint(1, self.odds["american bobtail"]) == 1:
            self.manx = ["Ab", "ab"]
        elif self.odds["manx"] > 0 and randint(1, self.odds["manx"]) == 1 and not self.ban_genes:
            self.manx = ["M", "m"]
        
        for i in range(2):
            if self.odds["karelian bobtail"] > 0 and randint(1, self.odds["karelian bobtail"]) == 1:
                self.kab[i] = "kab"
            if self.odds["toybob"] > 0 and randint(1, self.odds["toybob"]) == 1:
                self.toybob[i] = "Tb"
            if self.odds["kurilian bobtail"] > 0 and randint(1, self.odds["kurilian bobtail"]) == 1:
                self.kub[i] = "Kub"
            if self.odds["japanese bobtail"] > 0 and randint(1, self.odds["japanese bobtail"]) == 1:
                self.jbob[i] = "jb"
            if self.odds["ringtail"] > 0 and randint(1, self.odds["ringtail"]) == 1:
                self.ring[i] = "rt"
        
        # munch + poly + altai

        if self.odds["munchkin"] > 0 and randint(1, self.odds["munchkin"]) == 1 and not self.ban_genes:
            self.munch[0] = "Mk"

        for i in range(2):
            if self.odds["polydactyl"] > 0 and randint(1, self.odds["polydactyl"]) == 1:
                self.poly[i] = "Pd"
        
        if self.odds["DBE"] > 0 and randint(1, self.odds["DBE"] ** 2) == 1 and not self.ban_genes:
            self.pax3 = ['DBEalt', choice(['DBEcel', 'DBEcel', 'DBEre', 'DBEalt', 'DBEalt'])]
        elif self.odds["DBE"] > 0 and randint(1, self.odds["DBE"]) == 1 and not self.ban_genes:
            self.pax3[0] = choice(['DBEcel', 'DBEcel', 'DBEre', 'DBEalt', 'DBEalt'])

        self.wideband = ''
        self.rufousing = ''
        self.spotted = ''
        self.tickgenes = ''
        self.bengal = ''
        self.sokoke = ''
        
        for i in range(0, 8):
            self.wideband += choice(self.odds["wideband"])
            self.wbsum += int(self.wideband[i])

        for i in range(0, 4):
            self.rufousing += choice(self.odds["rufousing"])
            self.rufsum += int(self.rufousing[i])

        for i in range(0, 4):
            self.spotted += choice(self.odds["spotted"])
            self.spotsum += int(self.spotted[i])

        for i in range(0, 4):
            self.tickgenes += choice(self.odds["tickmod"])
            self.ticksum += int(self.tickgenes[i])

        for i in range(0, 4):
            self.bengal += choice(self.odds["bengal"])
            self.bengsum += int(self.bengal[i])

        for i in range(0, 4):
            self.sokoke += choice(self.odds["sokoke"])
            self.soksum += int(self.sokoke[i])

        self.GeneSort()
        self.PolyEval()

        if randint(1, self.odds['somatic_mutation']) > 0 and randint(1, self.odds['somatic_mutation']) == 1:
            self.GenerateSomatic()

        self.EyeColourFinder()

    def AltGenerator(self, special=None):
        if self.odds["kittypet_breed"] > 0 and randint(1, self.odds["kittypet_breed"]) == 1:
            return self.BreedGenerator(special)

        self.CommonGen(special)

        modifier = self.odds["boost_value"]

        # EUMELANIN

        for i in range(2):
            if self.odds["cinnamon"] > 1 and randint(1, math.ceil(self.odds["cinnamon"]/modifier)) == 1:
                self.eumelanin[i] = "bl"
            elif self.odds["chocolate"] > 1 and randint(1, math.ceil(self.odds["chocolate"]/modifier)) == 1:
                self.eumelanin[i] = "b"
            else:
                self.eumelanin[i] = "B"

        # WHITE
        
            if self.odds["birman gloving"] > 1 and randint(1, math.ceil(self.odds["birman gloving"]/modifier)) == 1:
                self.white[i] = "wg"
            elif self.odds["thai white"] > 1 and randint(1, math.ceil(self.odds["thai white"]/modifier)) == 1:
                self.white[i] = "wt"
            elif self.odds["salmiak"] > 1 and randint(1, math.ceil(self.odds["salmiak"]/modifier)) == 1:
                self.white[i] = "wsal"
            elif self.odds["dominant white"] > 0 and randint(1, self.odds["dominant white"]) == 1:
                self.white[i] = "W"
            elif self.odds["white spotting"] > 0 and randint(1, self.odds["white spotting"]) == 1:
                self.white[i] = "ws"
            else:
                self.white[i] = "w"

        # ALBINO

            if self.odds["albino"] > 1 and randint(1, math.ceil(self.odds["albino"]/modifier)) == 1 and not self.ban_genes:
                self.pointgene[i] = "c"
            elif self.odds["mocha"] > 1 and randint(1, math.ceil(self.odds["mocha"]/modifier)) == 1:
                self.pointgene[i] = "cm"
            elif self.odds["sepia"] > 1 and randint(1, math.ceil(self.odds["sepia"]/modifier)) == 1:
                self.pointgene[i] = "cb"
            elif self.odds["colourpoint"] > 1 and randint(1, math.ceil(self.odds["colourpoint"]/modifier)) == 1:
                self.pointgene[i] = "cs"
            else:
                self.pointgene[i] = "C"

        # AGOUTI

            if self.odds["charcoal"] > 1 and randint(1, math.ceil(self.odds["charcoal"]/modifier)) == 1:
                self.agouti[i] = "Apb"
            elif self.odds["solid"] > 0 and randint(1, self.odds["solid"]) == 1:
                self.agouti[i] = "a"
            else:
                self.agouti[i] = "A"

        # YORK, WIREHAIR, LAPERM, CORNISH, URAL, TENN, FLEECE

        for i in range(2):
            if self.odds["wirehair"] > 1 and randint(1, math.ceil(self.odds["wirehair"]/modifier)) == 1:
                self.wirehair[i] = "Wh"
            if self.odds["laperm"] > 1 and randint(1, math.ceil(self.odds["laperm"]/modifier)) == 1:
                self.laperm[i] = "Lp"
            if self.odds["cornish"] > 1 and randint(1, math.ceil(self.odds["cornish"]/modifier)) == 1:
                self.cornish[i] = "r"
            if self.odds["urals"] > 1 and randint(1, math.ceil(self.odds["urals"]/modifier)) == 1:
                self.urals[i] = "ru"
            if self.odds["tenn"] > 1 and randint(1, math.ceil(self.odds["tenn"]/modifier)) == 1:
                self.tenn[i] = "tr"
            if self.odds["fleece"] > 1 and randint(1, math.ceil(self.odds["fleece"]/modifier)) == 1:
                self.fleece[i] = "fc"
            
        
        #SELKIRK/DEVON/HAIRLESS
    
            if self.odds["canadian hairless"] > 1 and randint(1, math.ceil(self.odds["canadian hairless"]/modifier)) == 1 and not self.ban_genes:
                self.sedesp[i] = "hr"
            elif self.odds["devon"] > 1 and randint(1, math.ceil(self.odds["devon"]/modifier)) == 1:
                self.sedesp[i] = "re"
            elif self.odds["selkirk"] > 1 and randint(1, math.ceil(self.odds["selkirk"]/modifier)) == 1:
                self.sedesp[i] = "Se"


        #ruhr + ruhrmod + lykoi
            if self.odds["russian hairless"] > 1 and randint(1, math.ceil(self.odds["russian hairless"]/modifier)) == 1 and not self.ban_genes:
                self.ruhr[i] = "Hrbd"
            if self.odds["lykoi"] > 1 and randint(1, math.ceil(self.odds["lykoi"]/modifier)) == 1 and not self.ban_genes:
                self.lykoi[i] = "ly"

        # pinkdilute + dilutemd

        for i in range(2):
            if self.odds["pink-eyed dilute"] > 1 and randint(1, math.ceil(self.odds["pink-eyed dilute"]/modifier)) == 1 and not self.ban_genes:
                self.pinkdilute[i] = "dp"
            if self.odds["dilute modifier"] > 1 and randint(1, math.ceil(self.odds["dilute modifier"]/modifier)) == 1:
                self.dilutemd[i] = "Dm"

        # ext

            if self.odds["grizzle"] > 1 and randint(1, math.ceil(self.odds["grizzle"]/modifier)) == 1:
                self.ext[i] = "Eg"
            elif self.odds["carnelian"] > 1 and randint(1, math.ceil(self.odds["carnelian"]/modifier)) == 1:
                self.ext[i] = "ec"
            elif self.odds["russet"] > 1 and randint(1, math.ceil(self.odds["russet"]/modifier)) == 1:
                self.ext[i] = "er"
            elif self.odds["amber"] > 1 and randint(1, math.ceil(self.odds["amber"]/modifier)) == 1:
                self.ext[i] = "ea"

        #sunshine

            if self.odds["sunshine"] > 1 and randint(1, math.ceil(self.odds["sunshine"]/modifier)) == 1:
                self.corin[i] = "sh" #sunSHine
            elif self.odds["extreme sunshine"] > 1 and randint(1, math.ceil(self.odds["extreme sunshine"]/modifier)) == 1:
                self.corin[i] = "sg" #Siberian Gold / extreme sunshine
            elif self.odds["copper"] > 1 and randint(1, math.ceil(self.odds["copper"]/modifier)) == 1:
                self.corin[i] = "fg" #Flaxen Gold
            else:
                self.corin[i] = "N" #No

        # karp + bleach + ghosting + satin + glitter

            if self.odds["karpati"] > 1 and randint(1, math.ceil(self.odds["karpati"]/modifier)) == 1:
                self.karp[i] = "K"
            if self.odds["bleaching"] > 1 and randint(1, math.ceil(self.odds["bleaching"]/modifier)) == 1:
                self.bleach[i] = "lb"
            if self.odds["ghosting"] > 1 and randint(1, math.ceil(self.odds["ghosting"]/modifier)) == 1:
                self.ghosting[i] = "Gh"
            if self.odds["satin"] > 1 and randint(1, math.ceil(self.odds["satin"]/modifier)) == 1:
                self.satin[i] = "st"
            if self.odds["glitter"] > 1 and randint(1, math.ceil(self.odds["glitter"]/modifier)) == 1:
                self.glitter[i] = "gl"

        # curl + fold

            if self.odds["curl"] > 1 and randint(1, math.ceil(self.odds["curl"]/modifier)) == 1:
                self.curl[i] = "Cu"

        if self.odds["fold"] > 1 and randint(1, math.ceil(self.odds["fold"]/modifier)) == 1 and not self.ban_genes:
            self.fold[0] = "Fd"

        #  manx + kab + toybob + jbob + kub + ring

        if self.odds["american bobtail"] > 1 and randint(1, math.ceil(self.odds["american bobtail"]/modifier)) == 1:
            self.manx = ["Ab", "ab"]
        elif self.odds["manx"] > 1 and randint(1, math.ceil(self.odds["manx"]/modifier)) == 1 and not self.ban_genes:
            self.manx = ["M", "m"]
        
        for i in range(2):
            if self.odds["karelian bobtail"] > 1 and randint(1, math.ceil(self.odds["karelian bobtail"]/modifier)) == 1:
                self.kab[i] = "kab"
            if self.odds["toybob"] > 1 and randint(1, math.ceil(self.odds["toybob"]/modifier)) == 1:
                self.toybob[i] = "Tb"
            if self.odds["kurilian bobtail"] > 1 and randint(1, math.ceil(self.odds["kurilian bobtail"]/modifier)) == 1:
                self.kub[i] = "Kub"
            if self.odds["japanese bobtail"] > 1 and randint(1, math.ceil(self.odds["japanese bobtail"]/modifier)) == 1:
                self.jbob[i] = "jb"
            if self.odds["ringtail"] > 1 and randint(1, math.ceil(self.odds["ringtail"]/modifier)) == 1:
                self.ring[i] = "rt"
        
        # munch + poly + altai

        if self.odds["munchkin"] > 1 and randint(1, math.ceil(self.odds["munchkin"]/modifier)) == 1 and not self.ban_genes:
            self.munch[0] = "Mk"

        for i in range(2):
            if self.odds["polydactyl"] > 1 and randint(1, math.ceil(self.odds["polydactyl"]/modifier)) == 1:
                self.poly[i] = "Pd"
        
        if self.odds["DBE"] > 1 and randint(1, math.ceil((self.odds["DBE"] ** 2)/modifier)) == 1 and not self.ban_genes:
            self.pax3 = ['DBEalt', choice(['DBEcel', 'DBEcel', 'DBEre', 'DBEalt', 'DBEalt'])]
        elif self.odds["DBE"] > 1 and randint(1, math.ceil(self.odds["DBE"]/modifier)) == 1  and not self.ban_genes:
            self.pax3[0] = choice(['DBEcel', 'DBEcel', 'DBEre', 'DBEalt', 'DBEalt'])

        self.wideband = ''
        self.rufousing = ''
        self.spotted = ''
        self.tickgenes = ''
        self.bengal = ''
        self.sokoke = ''

        for i in range(0, 8):
            self.wideband += choice(self.odds["wideband_kittypet"])
            self.wbsum += int(self.wideband[i])

        for i in range(0, 4):
            self.rufousing += choice(self.odds["rufousing_kittypet"])
            self.rufsum += int(self.rufousing[i])

        for i in range(0, 4):
            self.spotted += choice(self.odds["spotted_kittypet"])
            self.spotsum += int(self.spotted[i])

        for i in range(0, 4):
            self.tickgenes += choice(self.odds["tickmod_kittypet"])
            self.ticksum += int(self.tickgenes[i])

        for i in range(0, 4):
            self.bengal += choice(self.odds["bengal_kittypet"])
            self.bengsum += int(self.bengal[i])

        for i in range(0, 4):
            self.sokoke += choice(self.odds["sokoke_kittypet"])
            self.soksum += int(self.sokoke[i])

        self.GeneSort()

        self.PolyEval()

        if randint(1, self.odds['somatic_mutation']) == 1:
            self.GenerateSomatic()

        self.EyeColourFinder()

    def BreedGenerator(self, special=None):

        common_breeds = [
            "Abyssinian", "American Burmese/Bombay", "American Curl", "American Shorthair", "Asian/Burmese", 
            "Bengal", "Birman", "British", "Chartreux", "Cornish Rex", "Devon Rex", "Egyptian Mau", 
            "Havana", "Japanese Bobtail", "Korat", "LaPerm", "Lykoi", "Maine Coon", "Manx", "Norwegian Forest cat", 
            "Ocicat", "Oriental/Siamese", "Persian/Exotic", "Ragdoll", "Russian", "Selkirk Rex", "Siberian", 
            "Singapura", "Sphynx", "Tonkinese", "Turkish"
        ]
        medium_breeds = [
            "American Bobtail", "Australian Mist", "Bambino", "Chausie", "Donskoy", "European Shorthair", "German Rex",
            "Highlander", "Khao Manee", "Kurilian Bobtail", "Mandalay/Burmese", "Munchkin", "Peterbald", "Pixie-Bob",
            "Ragamuffin", "Savannah", "Snowshoe", "Sokoke", "Thai", "Toybob", "Toyger"
        ]
        rare_breeds = [
            "Aphrodite", "Arabian Mau", "Brazilian Shorthair", "Cheetoh", "Ceylon", "Foldex", "Gaelic Fold", 
            "German Longhair", "Kanaani", "Karelian Bobtail", "Kinkalow", "Lambkin", "Lin-Qing Lion cat", "Mekong Bobtail", 
            "Napoleon", "New Zealand", "Serengeti", "Skookum", "Tennessee Rex", "Ural Rex"
        ]

        selected_breed = choice(choice([rare_breeds, medium_breeds, medium_breeds, medium_breeds, medium_breeds, common_breeds, common_breeds, common_breeds, common_breeds, common_breeds, common_breeds, common_breeds, common_breeds]))

        if self.ban_genes:
            while selected_breed in ["Lykoi", "Manx", "Sphynx", "Bambino", "Donskoy", "Munchkin", "Peterbald", "Foldex", "Gaelic Fold",
            "Kinkalow", "Lambkin", "Napoleon", "Skookum"]:
                selected_breed = choice(choice([rare_breeds, medium_breeds, medium_breeds, medium_breeds, medium_breeds, common_breeds, common_breeds, common_breeds, common_breeds, common_breeds, common_breeds, common_breeds, common_breeds]))
        
        gen = breed_functions["generator"][selected_breed]

        self = gen(self, special)

        self.GeneSort()

        if self.odds['somatic_mutation'] > 0 and randint(1, self.odds['somatic_mutation']) == 1:
            self.GenerateSomatic()

        self.PolyEval()
        self.EyeColourFinder()

    def KitGenerator(self, par1, par2=None, par3=None, chimera=False, gender=None):
        try:
            if par1.passes == 1 or not par1.chimerapheno:
                par1 = par1.phenotype
            elif not par1.passes:
                par1 = choice([par1.phenotype, par1.chimerapheno])
            else:
                par1 = par1.chimerapheno
        except:
            par1 = par1
        try:
            if par2.passes == 1 or not par2.chimerapheno:
                par2 = par2.phenotype
            elif not par2.passes:
                par2 = choice([par2.phenotype, par2.chimerapheno])
            else:
                par2 = par2.chimerapheno
        except:
            par2 = par2
        if not par2:
            print("No second parent genotype given")
            par2 = Genotype(self.odds, self.ban_genes, 'no chimeras')
            par2.Generator()
        if not par1:
            print("No first parent genotype given")
            par1 = Genotype(self.odds, self.ban_genes)
            par1.Generator()

        threepars = False
        try:
            if par3.passes == 1 or not par3.chimerapheno:
                par3 = par3.phenotype
            elif not par3.passes:
                par3 = choice([par3.phenotype, par3.chimerapheno])
            else:
                par3 = par3.chimerapheno
        except:
            par3 = par3
            if par2 == par3:
                par3 = None
        
        
        for breed in par1.breeds:
            if par1.breeds[breed] >= 0.1:
                self.breeds[breed] = par1.breeds[breed] / 2 
        for breed in par2.breeds:
            if par2.breeds[breed] >= 0.1:
                if self.breeds.get(breed, False):
                    self.breeds[breed] += par2.breeds[breed] / 2
                else:
                    self.breeds[breed] = par2.breeds[breed] / 2 
        
        self.KitEyes(par1, par2)

        if chimera:
            if isinstance(par3, Genotype) and random() < 0.33:
                self.KitGenerator(par1, par3)
                threepars = True
    
        if randint(1, 3) != 1:
            self.whitegrade = choice([par1.whitegrade, par2.whitegrade])

        if self.odds["vitiligo"] <= 0:
            a = 0
        elif (par1.vitiligo and par2.vitiligo):
            a = randint(1, math.ceil((self.odds["vitiligo"]/4)))
        elif(par1.vitiligo or par2.vitiligo):
            a = randint(1, math.ceil((self.odds['vitiligo']/2)))
        else:
            a = randint(1, self.odds['vitiligo'])

        if(a == 1):
            self.vitiligo = True    

        if self.odds['pseudo_merle'] > 0 and randint(1, self.odds['pseudo_merle'])==1:
            self.pseudomerle = True 
        
        for gene in ["danish_green", "polycaudal", "rainbow_eyes", "black_spotting", "peacock_blue"]:
            self.april_fools[gene] = ["", ""]
            if gene in par1.april_fools.keys():
                self.april_fools[gene][0] = choice(par1.april_fools[gene])
            if gene in par2.april_fools.keys():
                self.april_fools[gene][1] = choice(par2.april_fools[gene])
            
            if self.april_fools[gene] == ["", ""]:
                del self.april_fools[gene]
            elif not self.april_fools[gene][0]:
                self.april_fools[gene][0] = self.april_fools[gene][1].lower() if gene != "rainbow_eyes" else "NoDRE"
            elif not self.april_fools[gene][1]:
                self.april_fools[gene][1] = self.april_fools[gene][0].lower() if gene != "rainbow_eyes" else "NoDRE"

        self.furLength = [choice(par1.furLength), choice(par2.furLength)]
        
        self.eumelanin = [choice(par1.eumelanin), choice(par2.eumelanin)]

        mum = ["o", "o"]
        pap = ["o", "Y"]
        if (not get_clan_setting('modded_kits') or get_clan_setting('same sex birth')) and not xor('Y' in par1.sexgene, 'Y' in par2.sexgene):
            if ('Y' in par1.sexgene):
                if (randint(1, 2) == 1):
                    mum[0] = par1.sexgene[0]
                    if len(par1.sexgene) > 2:
                        mum[1] = par1.sexgene[1]
                    else:
                        mum[1] = mum[0]
                    pap = par2.sexgene
                else:
                    mum[0] = par2.sexgene[0]
                    if len(par2.sexgene) > 2:
                        mum[1] = par2.sexgene[1]
                    else:
                        mum[1] = mum[0]
                    pap = par1.sexgene
            else:
                if ('O' in par1.sexgene and 'o' in par1.sexgene):
                    mum = par1.sexgene
                    pap[0] = par2.sexgene[0]
                elif ('O' in par2.sexgene and 'o' in par2.sexgene):
                    mum = par2.sexgene
                    pap[0] = par1.sexgene[0]
                else:
                    if (random() < 0.5):
                        mum = par2.sexgene
                        pap[0] = par1.sexgene[0]
                    else:
                        mum = par1.sexgene
                        pap[0] = par2.sexgene[0]
        elif 'Y' in par1.sexgene or (par1.sex == "tom" and 'Y' not in par2.sexgene):
            mum = par2.sexgene
            pap = par1.sexgene
        else:
            mum = par1.sexgene
            pap = par2.sexgene
        

        while not self.sexgene[0] or (gender == "masc" and self.sex != "tom") or (gender == "fem" and self.sex != "molly"):
            if self.odds['X monosomy'] > 0 and randint(1, self.odds['X monosomy']) == 1:
                self.sexgene = [choice(mum)]
                self.sex = "molly"
            elif self.odds['XXX/XXY'] > 0 and randint(1, self.odds['XXX/XXY']) == 1 and (len(mum) > 1 or len(pap) > 1):
                self.sexgene = ["", "", ""]
                if random() < 0.5 and len(pap) > 1:
                    self.sexgene[0] = choice(mum)
                    if len(pap) < 3:
                        self.sexgene[1] = pap[0]
                        self.sexgene[2] = pap[1]
                    else:
                        a = randint(0, len(pap))
                        b = randint(0, len(pap))
                        while b == a:
                            b = randint(0, len(pap))
                        self.sexgene[1] = pap[a]
                        self.sexgene[2] = pap[b]
                else:
                    if len(mum) < 3:
                        self.sexgene[0] = mum[0]
                        self.sexgene[1] = mum[1]
                    else:
                        a = randint(0, 2)
                        b = randint(0, 2)
                        while b == a:
                            b = randint(0, 2)
                        
                        self.sexgene[0] = mum[a]
                        self.sexgene[1] = mum[b]
                    self.sexgene[2] = choice(pap)
            else:
                self.sexgene = [choice(mum), choice(pap)]
            
            if gender == "masc" and len(self.sexgene) > 1:
                self.sexgene[-1] = "Y"

            self.sex = "tom" if "Y" in self.sexgene else "molly"
        
        if self.odds['brindled_bicolour'] > 0 and randint(1, self.odds['brindled_bicolour'])==1:
            self.brindledbi = True 
        
        if(par1.specialred and random() < 0.1):
            self.specialred = par1.specialred
        elif(par2.specialred and random() < 0.1):
            self.specialred = par2.specialred
        elif(random() < 0.05):
            self.specialred = choice(['cameo', 'cameo', 'cameo', 'cameo', 'cameo', 'cameo', 'cameo', 'cameo', 'cameo', 'cameo', 'blue-red', 'blue-tipped', 'blue-tipped', 'blue-tipped', 'cinnamon'])

        self.dilute = [choice(par1.dilute), choice(par2.dilute)]
        self.white = [choice(par1.white), choice(par2.white)]
        self.pointgene = [choice(par1.pointgene), choice(par2.pointgene)]

        self.silver = [choice(par1.silver), choice(par2.silver)]
        self.agouti = [choice(par1.agouti), choice(par2.agouti)]
        self.mack = [choice(par1.mack), choice(par2.mack)]
        self.ticked = [choice(par1.ticked), choice(par2.ticked)]


        if self.odds["breakthrough"] <= 0:
            pass
        elif (par1.breakthrough and par2.breakthrough):
            self.breakthrough = randint(1, math.ceil((self.odds["breakthrough"]/4))) == 1
        elif(par1.breakthrough or par2.breakthrough):
            self.breakthrough = randint(1, math.ceil((self.odds['breakthrough']/2))) == 1
        else:
            self.breakthrough = randint(1, self.odds['breakthrough']) == 1

        if self.odds["dense_blotched"] <= 0:
            pass
        elif (par1.sheeted and par2.sheeted):
            self.sheeted = randint(1, math.ceil((self.odds["dense_blotched"]/4))) == 1
        elif (par1.sheeted or par2.sheeted):
            self.sheeted = randint(1, math.ceil((self.odds['dense_blotched']/2))) == 1
        else:
            self.sheeted = randint(1, self.odds['dense_blotched']) == 1

        self.wirehair = [choice(par1.wirehair), choice(par2.wirehair)]
        self.laperm = [choice(par1.laperm), choice(par2.laperm)]
        self.cornish = [choice(par1.cornish), choice(par2.cornish)]
        self.urals = [choice(par1.urals), choice(par2.urals)]
        self.tenn = [choice(par1.tenn), choice(par2.tenn)]
        self.fleece = [choice(par1.fleece), choice(par2.fleece)]
        self.sedesp = [choice(par1.sedesp), choice(par2.sedesp)]
        self.ruhr = [choice(par1.ruhr), choice(par2.ruhr)]
        self.ruhrmod = [choice(par1.ruhrmod), choice(par2.ruhrmod)]

        if(self.ruhrmod[0] == "ha"):
            x = self.ruhrmod[1]
            self.ruhrmod[1] = self.ruhrmod[0]
            self.ruhrmod[0] = x

        self.lykoi = [choice(par1.lykoi), choice(par2.lykoi)]

        self.pinkdilute = [choice(par1.pinkdilute), choice(par2.pinkdilute)]
        self.dilutemd = [choice(par1.dilutemd), choice(par2.dilutemd)]
        self.ext = [choice(par1.ext), choice(par2.ext)]
        self.corin = [choice(par1.corin), choice(par2.corin)]
        
        self.karp = [choice(par1.karp), choice(par2.karp)]
        self.bleach = [choice(par1.bleach), choice(par2.bleach)]
        self.ghosting = [choice(par1.ghosting), choice(par2.ghosting)]
        self.satin = [choice(par1.satin), choice(par2.satin)]
        self.glitter = [choice(par1.glitter), choice(par2.glitter)]

        self.curl = [choice(par1.curl), choice(par2.curl)]
        self.fold = [choice(par1.fold), choice(par2.fold)]
        self.fourear = [choice(par1.fourear), choice(par2.fourear)]
        
        self.manx = [choice(par1.manx), choice(par2.manx)]
        self.kab = [choice(par1.kab), choice(par2.kab)]
        self.toybob = [choice(par1.toybob), choice(par2.toybob)]
        self.jbob = [choice(par1.jbob), choice(par2.jbob)]
        self.kub = [choice(par1.kub), choice(par2.kub)]
        self.ring = [choice(par1.ring), choice(par2.ring)]
        self.munch = [choice(par1.munch), choice(par2.munch)]
        self.poly = [choice(par1.poly), choice(par2.poly)]
        self.pax3 = [choice(par1.pax3), choice(par2.pax3)]

        if random() < 0.25:
            self.saturation = par1.saturation
        elif random() < 0.25:
            self.saturation = par2.saturation
        

        self.wideband = ""
        for i in range(8):
            tempwb = 0
            if par1.wideband[i] == "2" or (par1.wideband[i] == "1" and randint(1, 2) == 1):
                tempwb = tempwb+1
            if par2.wideband[i] == "2" or (par2.wideband[i] == "1" and randint(1, 2) == 1):
                tempwb = tempwb+1
            self.wideband += str(tempwb)
        
        self.rufousing = ""
        for i in range(4):
            tempruf = 0
            if par1.rufousing[i] == "2" or (par1.rufousing[i] == "1" and randint(1, 2) == 1):
                tempruf = tempruf+1
            if par2.rufousing[i] == "2" or (par2.rufousing[i] == "1" and randint(1, 2) == 1):
                tempruf = tempruf+1
            self.rufousing += str(tempruf)
        
        self.unders_ruf = ""
        for i in range(4):
            tempruf = 0
            if par1.unders_ruf[i] == "2" or (par1.unders_ruf[i] == "1" and randint(1, 2) == 1):
                tempruf = tempruf+1
            if par2.unders_ruf[i] == "2" or (par2.unders_ruf[i] == "1" and randint(1, 2) == 1):
                tempruf = tempruf+1
            self.unders_ruf += str(tempruf)
        
        self.bengal = ""
        for i in range(4):
            tempbeng = 0
            if par1.bengal[i] == "2" or (par1.bengal[i] == "1" and randint(1, 2) == 1):
                tempbeng = tempbeng+1
            if par2.bengal[i] == "2" or (par2.bengal[i] == "1" and randint(1, 2) == 1):
                tempbeng = tempbeng+1
            self.bengal += str(tempbeng)
        
        self.sokoke = ""
        for i in range(4):
            tempsok = 0
            if par1.sokoke[i] == "2" or (par1.sokoke[i] == "1" and randint(1, 2) == 1):
                tempsok = tempsok+1
            if par2.sokoke[i] == "2" or (par2.sokoke[i] == "1" and randint(1, 2) == 1):
                tempsok = tempsok+1
            self.sokoke += str(tempsok)
        
        self.spotted = ""
        for i in range(4):
            tempspot = 0
            if par1.spotted[i] == "2" or (par1.spotted[i] == "1" and randint(1, 2) == 1):
                tempspot = tempspot+1
            if par2.spotted[i] == "2" or (par2.spotted[i] == "1" and randint(1, 2) == 1):
                tempspot = tempspot+1
            self.spotted += str(tempspot)
        
        self.tickgenes = ""
        for i in range(4):
            temptick = 0
            if par1.tickgenes[i] == "2" or (par1.tickgenes[i] == "1" and randint(1, 2) == 1):
                temptick = temptick+1
            if par2.tickgenes[i] == "2" or (par2.tickgenes[i] == "1" and randint(1, 2) == 1):
                temptick = temptick+1
            self.tickgenes += str(temptick)

        wobble = randint(1, int(sum(self.body_ranges) / 25))
        self.body_value = randint(min(par1.body_value-wobble, par2.body_value-wobble), max(par1.body_value+wobble, par2.body_value+wobble))
        
        wobble = randint(1, int(sum(self.height_ranges) / 25))
        self.height_value = randint(min(par1.height_value-wobble, par2.height_value-wobble), max(par1.height_value+wobble, par2.height_value+wobble))

        if self.body_value < 1:
            self.body_value = 1
        if self.body_value > sum(self.body_ranges):
            self.body_value = sum(self.body_ranges)
        
        if self.height_value < 1:
            self.height_value = 1
        if self.height_value > sum(self.height_ranges):
            self.height_value = sum(self.height_ranges)

        self.GeneSort()

        if self.odds['random_mutation'] > 0 and randint(1, self.odds['random_mutation']) == 1:
            print("MUTATION!")
            self.Mutate()
            self.GeneSort()

        if self.odds['somatic_mutation'] > 0 and randint(1, self.odds['somatic_mutation']) == 1:
            self.GenerateSomatic()
        
        self.PolyEval()
        self.EyeColourFinder()

        return threepars

    def KitEyes(self, par1, par2):
        multipliers = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        multipliers2 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    
        def maths(par, m):
            m[par-1] += 10
            for i in range(0, par-1):
                m[i] += 10 / 5 ** (par-i-1)
            
            for i in range(par, 11):
                m[i] += 10 / 5 ** (i-par+1)
            return m
    
        multipliers = maths(par1.refraction, multipliers)
        multipliers = maths(par2.refraction, multipliers)
        multipliers = maths(math.floor((int(par1.refraction) + int(par2.refraction))/2), multipliers)
        multipliers2 = maths(par1.pigmentation, multipliers2)
        multipliers2 = maths(par2.pigmentation, multipliers2)
        multipliers2 = maths(math.floor((int(par1.pigmentation) + int(par2.pigmentation))/2), multipliers2)

        x = sum(multipliers)
        x2 = sum(multipliers2)

        def getindexes(m):
            inds = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
            
            for i in range(0, 11):
                for j in range(0, i+1):
                    inds[i] += m[j]
            
            return inds
        indexes = getindexes(multipliers)
        indexes2 = getindexes(multipliers2)

        num = random() * x
        self.refraction = next((n for n in range(len(indexes)) if num < indexes[n])) + 1
        num = random() * x2
        self.pigmentation = next((n for n in range(len(indexes2)) if num < indexes2[n])) + 1

    def GenerateBody(self):
        self.body_value = randint(1, sum(self.body_ranges))

        self.height_value = randint(1, sum(self.height_ranges))
    
    def VerifyBody(self, body_types):
        for i in range(7):
            if i == 0:
                if self.body_label == body_types[0] and self.body_value >= self.body_indexes[0]:
                    self.body_value = randint(0, self.body_indexes[0]-1)
            else:
                if self.body_label == body_types[i] and (self.body_value >= self.body_indexes[i] or self.body_value < self.body_indexes[i-1]):
                    self.body_value = randint(self.body_indexes[i-1], self.body_indexes[i]-1)
    
    def VerifyHeight(self):
        height = self.shoulder_height
        if self.growth_pattern == "runt":
            height /= 0.85
        if self.munch[0] == 'Mk':
            height *= 1.5
        if 'Y' in self.sexgene[0]:
            height /= 1.075
        height = round(height, 2)

        if height <= 5.00:
            self.shoulder_height = 5.00

            if self.munch[0] == 'Mk':
                self.shoulder_height /= 1.5
            if 'Y' in self.sexgene:
                self.shoulder_height *= 1.1
            self.shoulder_height = round(self.shoulder_height, 2)

            if self.height_value >= self.height_indexes[0]:
                self.height_value = randint(0, self.height_indexes[0]-1)
            return
        elif height >= 15.00:
            self.shoulder_height = 15.00

            if self.growth_pattern == "runt":
                self.shoulder_height *= 0.85
            if self.munch[0] == 'Mk':
                self.shoulder_height /= 1.5
            if 'Y' in self.sexgene:
                self.shoulder_height *= 1.1
            self.shoulder_height = round(self.shoulder_height, 2)
            
            if self.height_value < self.height_indexes[8]:
                self.height_value = randint(self.height_indexes[8], self.height_indexes[9]-1)
            return
        elif 6.01 > height > 5.00:
            if self.height_indexes[0] > self.height_value or self.height_value >= self.height_indexes[1]:
                self.height_value = randint(self.height_indexes[0], self.height_indexes[1]-1)
            return
        elif 7.51 > height > 6.00:
            if self.height_indexes[1] > self.height_value or self.height_value >= self.height_indexes[2]:
                self.height_value = randint(self.height_indexes[1], self.height_indexes[2]-1)
            return
        elif 9 > height > 7.50:
            if self.height_indexes[2] > self.height_value or self.height_value >= self.height_indexes[3]:
                self.height_value = randint(self.height_indexes[2], self.height_indexes[3]-1)
            return
        elif 11.01 > height > 8.99:
            if self.height_indexes[3] > self.height_value or self.height_value >= self.height_indexes[4]:
                self.height_value = randint(self.height_indexes[3], self.height_indexes[4]-1)
            return
        elif 12.50 > height > 11.00:
            if self.height_indexes[4] > self.height_value or self.height_value >= self.height_indexes[5]:
                self.height_value = randint(self.height_indexes[4], self.height_indexes[5]-1)
            return
        elif 13.50 > height > 12.49:
            if self.height_indexes[5] > self.height_value or self.height_value >= self.height_indexes[6]:
                self.height_value = randint(self.height_indexes[5], self.height_indexes[6]-1)
            return
        elif 14.50 > height > 13.49:
            if self.height_indexes[6] > self.height_value or self.height_value >= self.height_indexes[7]:
                self.height_value = randint(self.height_indexes[6], self.height_indexes[7]-1)
            return
        elif 15.00 > height > 14.49:
            if self.height_indexes[7] > self.height_value or self.height_value >= self.height_indexes[8]:
                self.height_value = randint(self.height_indexes[7], self.height_indexes[8]-1)
            return

    def PolyEval(self):
        wbtypes = ["low", "medium", "high", "shaded", "chinchilla"]
        ruftypes = ["low", "medium", "rufoused"]

        self.wbsum = 0
        self.rufsum = 0
        self.unders_rufsum = 0
        self.bengsum = 0
        self.soksum = 0
        self.spotsum = 0
        self.ticksum = 0
        
        if len(self.wideband) < 8:
            while len(self.wideband) < 8:
                self.wideband += '1'
        if len(self.rufousing) < 4:
            while len(self.rufousing) < 4:
                self.rufousing += '1'
        if len(self.unders_ruf) < 4:
            while len(self.unders_ruf) < 4:
                self.unders_ruf += '1'
        if len(self.bengal) < 4:
            while len(self.bengal) < 4:
                self.bengal += '1'
        if len(self.sokoke) < 4:
            while len(self.sokoke) < 4:
                self.sokoke += '1'
        if len(self.spotted) < 4:
            while len(self.spotted) < 4:
                self.spotted += '1'
        if len(self.tickgenes) < 4:
            while len(self.tickgenes) < 4:
                self.tickgenes += '1'

        for i in self.wideband:
            self.wbsum += int(i)
        for i in self.rufousing:
            self.rufsum += int(i)
        for i in self.unders_ruf:
            self.unders_rufsum += int(i)
        for i in self.bengal:
            self.bengsum += int(i)
        for i in self.sokoke:
            self.soksum += int(i)
        for i in self.spotted:
            self.spotsum += int(i)
        for i in self.tickgenes:
            self.ticksum += int(i)
        
        if self.wbsum < 6:
            self.wbtype = wbtypes[0]
        elif self.wbsum < 10:
            self.wbtype = wbtypes[1]
        elif self.wbsum < 12: 
            self.wbtype = wbtypes[2]
        elif self.wbsum < 14: 
            self.wbtype = wbtypes[3]
        else: 
            self.wbtype = wbtypes[4]

        if self.rufsum < 3: 
            self.ruftype = ruftypes[0]
        elif self.rufsum < 6: 
            self.ruftype = ruftypes[1]
        else:
            self.ruftype = ruftypes[2]

        if self.unders_rufsum < 3: 
            self.unders_ruftype = ruftypes[0]
        elif self.unders_rufsum < 6: 
            self.unders_ruftype = ruftypes[1]
        else:
            self.unders_ruftype = ruftypes[2]

        spottypes = ["fully striped", "slightly broken", "broken stripes", "mostly broken", "spotted"]

        if self.spotsum < 1: 
            self.spottype = spottypes[0]
        elif self.spotsum < 3:
            self.spottype = spottypes[1]
        elif self.spotsum < 6:
            self.spottype = spottypes[2]
        elif self.spotsum < 8: 
            self.spottype = spottypes[3]
        else:
            self.spottype = spottypes[4]
        
        ticktypes = ["full barring", "reduced barring", "agouti"]

        if self.ticksum < 4: 
            self.ticktype = ticktypes[0]
        elif self.ticksum < 6:
            self.ticktype = ticktypes[1]
        else:
            self.ticktype = ticktypes[2]

        bengtypes = ["normal markings", "mild bengal", "full bengal"]

        if self.bengsum < 4: 
            self.bengtype = bengtypes[0]
        elif self.bengsum < 6:
            self.bengtype = bengtypes[1]
        else:
            self.bengtype = bengtypes[2]

        soktypes = ["normal markings", "mild fading", "full sokoke"]

        if self.soksum < 4: 
            self.soktype = soktypes[0]
        elif self.soksum < 6:
            self.soktype = soktypes[1]
        else:
            self.soktype = soktypes[2]

        body_types = ['snub-nosed cobby', 'cobby', 'semi-cobby', 'intermediate', 'semi-oriental', 'oriental', 'wedge-faced oriental']
        height_types = ['teacup', 'tiny', 'small', 'below average', 'average', 'above average', 'large', 'massive', 'giant', 'goliath']

        if self.body_label != '':
            self.VerifyBody(body_types)
        else:
            index = next((n for n in range(7) if self.body_value <= self.body_indexes[n]))
            self.body_label = body_types[index]

        if self.shoulder_height > 0:
            self.VerifyHeight()
        index = next((n for n in range(10) if self.height_value <= self.height_indexes[n]))
        self.height_label = height_types[index]

        if self.shoulder_height > 0:
            return

        if index == 0:
            self.shoulder_height = 5.00
        elif index == 1:
            value = self.height_value - self.height_indexes[index-1]-1
            step = (6-5.01) / self.height_ranges[index]
            self.shoulder_height = 5.01 + value * step + (random() * step)
        elif index == 2:
            value = self.height_value - self.height_indexes[index-1]-1
            step = (7.5-6.01) / self.height_ranges[index]
            self.shoulder_height = 6.01 + value * step + (random() * step)
        elif index == 3:
            value = self.height_value - self.height_indexes[index-1]-1
            step = (8.99-7.51) / self.height_ranges[index]
            self.shoulder_height = 7.51 + value * step + (random() * step)
        elif index == 4:
            value = self.height_value - self.height_indexes[index-1]-1
            step = (11-9) / self.height_ranges[index]
            self.shoulder_height = 9 + value * step + (random() * step)
        elif index == 5:
            value = self.height_value - self.height_indexes[index-1]-1
            step = (12.49-11.01) / self.height_ranges[index]
            self.shoulder_height = 11.01 + value * step + (random() * step)
        elif index == 6:
            value = self.height_value - self.height_indexes[index-1]-1
            step = (13.49-12.50) / self.height_ranges[index]
            self.shoulder_height = 12.50 + value * step + (random() * step)
        elif index == 7:
            value = self.height_value - self.height_indexes[index-1]-1
            step = (14.49-13.50) / self.height_ranges[index]
            self.shoulder_height = 13.50 + value * step + (random() * step)
        elif index == 8:
            value = self.height_value - self.height_indexes[index-1]-1
            step = (14.99-14.50) / self.height_ranges[index]
            self.shoulder_height = 14.50 + value * step + (random() * step)
        elif index == 9:
            self.shoulder_height = 15.00
        
        if 'Y' in self.sexgene:
            self.shoulder_height *= 1.075
        elif len(self.sexgene) == 1:
            self.shoulder_height *= 0.9
        if self.munch[0] == 'Mk':
            self.shoulder_height /= 1.5

        weights = [1, 5, 12, 5, 3] if height_types.index(self.height_label) > 5 else [1, 1, 12, 4, 4]
        self.growth_pattern = choices(["runt", "slow", "average", "big-kitten", "small-kitten"], weights)[0]
        index = next((n for n in range(10) if self.height_value <= self.height_indexes[n]))
        self.height_label = height_types[index]

        if self.growth_pattern == "runt":
            self.shoulder_height *= 0.85
            if self.shoulder_height <= 5:
                self.shoulder_height = 5
        self.shoulder_height = round(self.shoulder_height, 2)
    
    def GeneSort(self):

        for gene in ["furLength", "dilute", 'silver', 'mack', 'ticked',
                     'wirehair', 'laperm', 'cornish', 'urals', 'tenn', 'fleece', 'ruhr', 'lykoi',
                     'pinkdilute', 'dilutemd', 'karp', 'bleach', 'ghosting', 'satin', 'glitter',
                     'curl', 'fold', "fourear", 'kab', 'toybob', 'jbob', 'kub', 'ring', 'munch', 'poly']:
            self[gene].sort()
        for gene in self.april_fools.keys():
            self.april_fools[gene].sort()

        if self.eumelanin[0] == "bl":
            self.eumelanin[0] = self.eumelanin[1]
            self.eumelanin[1] = "bl"
        elif self.eumelanin[0] == "b" and self.eumelanin[1] == "B":
            self.eumelanin[0] = "B"
            self.eumelanin[1] = "b"

        self.sexgene.sort(key=lambda s: (s.lower(), s))

        if self.white[0] == "wsal":
            self.white[0] = self.white[1]
            self.white[1] = "wsal"
        elif self.white[0] == "wg" and self.white[1] != "wsal":
            self.white[0] = self.white[1]
            self.white[1] = "wg"
        elif self.white[0] == "w" and self.white[1] not in ["wsal", "wg"]:
            self.white[0] = self.white[1]
            self.white[1] = "w"
        elif self.white[0] == "wt" and self.white[1] not in ["wsal", "wg", "w"]:
            self.white[0] = self.white[1]
            self.white[1] = "wt"
        elif self.white[1] == "W":
            self.white[1] = self.white[0]
            self.white[0] = "W"

        if self.pointgene[0] == "c":
            self.pointgene[0] = self.pointgene[1]
            self.pointgene[1] = "c"
        elif self.pointgene[0] == "cm" and self.pointgene[1] != "c":
            self.pointgene[0] = self.pointgene[1]
            self.pointgene[1] = "cm"
        elif self.pointgene[0] == "cs" and self.pointgene[1] not in ["c", "cm"]:
            self.pointgene[0] = self.pointgene[1]
            self.pointgene[1] = "cs"
        elif self.pointgene[1] == "C":
            self.pointgene[1] = self.pointgene[0]
            self.pointgene[0] = "C"

        if self.agouti[0] == "a":
            self.agouti[0] = self.agouti[1]
            self.agouti[1] = "a"
        elif self.agouti[0] == "Apb" and self.agouti[1] != "a":
            self.agouti[0] = self.agouti[1]
            self.agouti[1] = "Apb"

        if self.sedesp[0] == "re":
            self.sedesp[0] = self.sedesp[1]
            self.sedesp[1] = "re"
        elif self.sedesp[0] == "hr" and self.sedesp[1] != "re":
            self.sedesp[0] = self.sedesp[1]
            self.sedesp[1] = "hr"
        elif self.sedesp[1] == "Se":
            self.sedesp[1] = self.sedesp[0]
            self.sedesp[0] = "Se"

        if self.ext[0] == "ec":
            self.ext[0] = self.ext[1]
            self.ext[1] = "ec"
        elif self.ext[0] == "er" and self.ext[1] != "ec":
            self.ext[0] = self.ext[1]
            self.ext[1] = "er"
        elif self.ext[1] == "Eg":
            self.ext[1] = self.ext[0]
            self.ext[0] = "Eg"
        elif self.ext[1] == "E" and self.ext[0] != "Eg":
            self.ext[1] = self.ext[0]
            self.ext[0] = "E"

        if self.corin[0] == "fg":
            self.corin[0] = self.corin[1]
            self.corin[1] = "fg"
        elif self.corin[0] == "sh" and self.corin[1] != "fg":
            self.corin[0] = self.corin[1]
            self.corin[1] = "sh"
        elif self.corin[0] == "sg" and self.corin[1] not in ["sh", "fg"]:
            self.corin[0] = self.corin[1]
            self.corin[1] = "sg"

        if self.manx[1] == "M":
            self.manx[1] = self.manx[0]
            self.manx[0] = "M"
        elif self.manx[1] == "Ab":
            self.manx[1] = self.manx[0]
            self.manx[0] = "Ab"

        if self.pax3[0] == 'NoDBE':
            self.pax3[0] = self.pax3[1]
            self.pax3[1] = 'NoDBE'

    def find_unused_rand_value(self, used_value, max):
        rand = None
        while not rand or rand == used_value:
            rand = randint(1, max)
        return rand

    def EyeColourFinder(self):
        eyecolours = {
        "R1" : ["Citrine", "Golden Beryl", "Yellow", "Pale Golden", "Golden", "Amber", "Light Orange", "Orange", "Cinnabar", "Auburn", "Copper", "Ice Blue", "Pink"],
        "R2" : ["Pale Citrine", "Pale Yellow", "Lemon", "Deep Yellow", "Dull Golden", "Honey", "Pale Orange", "Burnt Orange", "Dark Orange", "Russet", "Dark Topaz", "Aquamarine", "Rose"],
        "R3" : ["Lemonade Yellow", "Straw Yellow", "Dandelion Yellow", "Banana Yellow", "Sunglow Yellow", "Copal", "Dull Orange", "Rust Orange", "Topaz", "Chocolate", "Burgundy", "Sky Blue", "Magenta"],
        "R4" : ["Light Celadon", "Pale Chartreuse", "Pear Green", "Brass Yellow", "Golden Green", "Butterscotch", "Dusty Orange", "Tawny", "Jasper", "Light Brown", "Earth", "Cyan", "Periwinkle"],
        "R5" : ["Light Jade", "Pale Lime", "Spring Bud", "Chartreuse", "Pale Hazel", "Yellow Hazel", "Golden Fluorite", "Beaver Brown", "Sienna", "Chestnut", "Umber", "Baby Blue", "Violet"],
        "R6" : ["Light Fluorite", "Mantis Green", "Spring Green", "Lime", "Green Tea", "Hazel", "Green Hazel", "Dark Copal", "Cinnamon", "Raw Umber", "Sepia", "Aqua", "Glass"],
        "R7" : ["Pale Emerald", "Apple Green", "Shamrock", "Lemon-Lime", "Peridot", "Antique Brass", "Dark Hazel", "Brown-Green", "Hazel Brown", "Bronze", "Bistre Brown", "Cerulean", "Moonstone"],
        "R8" : ["Malachite", "Olivine", "Pastel Green", "Bright Green", "Pistachio", "Dull Olive", "Murky Green", "Jungle Green", "Hemlock Green", "Thatch Green", "Muddy", "Ocean Blue", "Albino Ice Blue"],
        "R9" : ["Pale Turquoise", "Mint", "Snake Green", "Dark Lime", "Fern Green", "Dull Green", "Dark Fern Green", "Olive", "Tumbleweed Green", "Bronze Olive", "Deep Bronze", "Teal", "Albino Aquamarine"],
        "R10" : ["Turquoise", "Viridian", "Green Onion", "Leaf Green", "Green", "Sap Green", "Dark Leaf Green", "Forest Green", "Dark Peridot", "Seaweed Green", "Dark Olive", "Sapphire", "Albino Sky Blue"],
        "R11" : ["Deep Turquoise", "Amazonite", "Pine Green", "Deep Leaf Green", "Jade", "Emerald", "Deep Green", "Deep Forest Green", "Dark Green", "Dark Moss Green", "Black Olive", "Azure", "Albino Azure"]
        }
        sectoralindex = randint(0, self.odds["sectoral_heterochromia"]-1) if self.odds["sectoral_heterochromia"] > 1 else 0
        het2index = randint(0, self.odds["random_heterochromia"]-1) if self.odds["random_heterochromia"] > 1 else 0
        blueindex = 1
        hetindex = 1

        if not self.refraction:
            refgrade = choice([1, 2, 2, 3, 3, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 9, 9, 10, 10, 11])
            piggrade = choice([1, 2, 2, 3, 3, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 9, 9, 10, 10, 11])
            self.refraction = refgrade
            self.pigmentation = piggrade
        else:
            refgrade = self.refraction
            piggrade = self.pigmentation

        if self.dilute[0] == "d" or self.pointgene == ["cb", "cb"] or self.pointgene == ["cb", "c"] or self.pointgene == ["cb", "cm"]:
            if randint(1, 5) == 1:
                piggrade = piggrade - 1

        if self.pinkdilute[0] == 'dp' or self.pointgene == ["cb", "cs"] or self.pointgene[0] == "cm":
            piggrade = math.ceil(piggrade / 2)
        
        if piggrade == 0 or ((self.pointgene == ["cb", "cs"] or self.pointgene == ["cb", "cm"] or self.pointgene == ["cm", "cm"] or self.pointgene == ["cm", "c"]) and randint(1, 5) == 1):
            piggrade = 1

        def RefTypeFind(x, piggrade):
            y = eyecolours['R' + str(x)][piggrade-1]

            return y
        
        def SecondaryRefTypeFind(x, piggrade):
            y = ""

            piggrade = "P" + str(piggrade)
            if piggrade == "P12":
                piggrade = "blue"
            elif piggrade == "P13":
                piggrade = "albino"
                    
            y += "R" + str(x) + " ; " + str(piggrade) + ""
            return y
        
        


        if self.pointgene == ["cb","cs"]:
            blueindex = randint(0, 10)
        if self.pointgene == ["cb","cs"] or self.pointgene == ["cb","cm"] or self.pointgene == ["cm","cm"] or self.pointgene == ["cm","c"]:
            blueindex = randint(0, 4)
        if self.white[0] in ['w', 'wg', 'wsal'] or blueindex == 0:
            pass
        elif self.white[0] in ['ws', 'wt'] and self.white[1] not in ['ws', 'wt']:
            if self.whitegrade < 3:
                blueindex = randint(0, self.odds["no-low_white_blue_eyes"]-1) if self.odds["no-low_white_blue_eyes"] > 1 else 0
            elif self.whitegrade < 5:
                blueindex = randint(0, self.odds["low_white_blue_eyes"]-1) if self.odds["low_white_blue_eyes"] > 1 else 0
            else:
                blueindex = randint(0, self.odds["mid_white_blue_eyes"]-1) if self.odds["mid_white_blue_eyes"] > 1 else 0
        elif self.white[0] in ['ws', 'wt']:
            if self.whitegrade < 3:
                blueindex = randint(0, self.odds["mid_white_blue_eyes"]-1) if self.odds["mid_white_blue_eyes"] > 1 else 0
            else:
                blueindex = randint(0, self.odds["high_white_blue_eyes"]-1) if self.odds["high_white_blue_eyes"] > 1 else 0
        elif self.white[0] == "W":
            blueindex = randint(0, self.odds["het_dom_white_blue_eyes"]-1) if self.odds["het_dom_white_blue_eyes"] > 1 else 0
            if randint(1, 4) == 1 and blueindex == 0:
                self.deaf = True
        if self.white == ["W","W"]:
            blueindex = randint(0, self.odds["homo_dom_white_blue_eyes"]-1) if self.odds["homo_dom_white_blue_eyes"] > 1 else 0
            if randint(1, 4) < 4 and blueindex == 0:
                self.deaf = True
        
        if self.pointgene[0] == "cs":
            blueindex = 0
        

        if self.white[0] in ['w', 'wg', 'wsal']:
            pass
        elif self.white[0] in ['ws', 'wt'] and self.white[1] not in ['ws', 'wt']:
            if self.whitegrade < 3:
                hetindex = randint(0, self.odds["no-low_white_one_blue_eye"]-1) if self.odds["no-low_white_one_blue_eye"] > 1 else 0
            elif self.whitegrade < 5:
                hetindex = randint(0, self.odds["low_white_one_blue_eye"]-1) if self.odds["low_white_one_blue_eye"] > 1 else 0
            else:
                hetindex = randint(0, self.odds["mid_white_one_blue_eye"]-1) if self.odds["mid_white_one_blue_eye"] > 1 else 0
        elif self.white[0] in ['ws', 'wt']:
            if self.whitegrade < 3:
                hetindex = randint(0, self.odds["mid_white_one_blue_eye"]-1) if self.odds["mid_white_one_blue_eye"] > 1 else 0
            else:
                hetindex = randint(0, self.odds["high_white_one_blue_eye"]-1) if self.odds["high_white_one_blue_eye"] > 1 else 0
        elif self.white[0] == "W":
            hetindex = randint(0, self.odds["het_dom_white_one_blue_eye"]-1) if self.odds["het_dom_white_one_blue_eye"] > 1 else 0
            if randint(1, 10) == 1 and hetindex == 0:
                self.deaf = True
            elif randint(1, 20) == 1:
                self.deaf = True
        if self.white == ["W","W"]:
            hetindex = randint(0, self.odds["homo_dom_white_one_blue_eye"]-1) if self.odds["homo_dom_white_one_blue_eye"] > 1 else 0
            if randint(1, 8) == 1 and hetindex == 0:
                self.deaf = True

        if self.pax3[0] != 'NoDBE':
            if 'NoDBE' not in self.pax3:
                blueindex = 0
                if (self.pax3 == ['DBEalt', 'DBEalt'] and random() < 0.5) or self.pax3 != ['DBEalt', 'DBEalt']:
                    self.deaf = True
            elif 'DBEre' not in self.pax3 and random() >= 0.1:
                if random() < 0.33:
                    blueindex = 0
                else:
                    hetindex = 0
            elif 'DBEre' in self.pax3:
                blueindex = 0 if random() < 0.70 else 1
                if random() < 0.33:
                    self.deaf = True

        tempref = self.find_unused_rand_value(refgrade, 11)
        temppig = 12 if not blueindex else self.find_unused_rand_value(piggrade, 12)
        tempvals = [self.find_unused_rand_value(refgrade, 11), 12 if not blueindex else self.find_unused_rand_value(piggrade, 12)]
        
        if not blueindex:
            piggrade = 12
        if ("c" in self.pointgene and self.pointgene[0] != "C"):
            piggrade = 13
            temppig = 13
            tempvals[1] = 13
        
        self.righteye = RefTypeFind(refgrade, piggrade)
        self.lefteye = RefTypeFind(refgrade, piggrade)

        self.lefteyetype = SecondaryRefTypeFind(refgrade, piggrade)
        self.righteyetype = SecondaryRefTypeFind(refgrade, piggrade)
        
        self.extraeyecolour = RefTypeFind(tempvals[0], tempvals[1])
        self.extraeyetype = SecondaryRefTypeFind(tempvals[0], tempvals[1])

        if het2index == 0:
            if randint(1, 2)==1:
                self.lefteye = RefTypeFind(tempref, temppig)
                self.lefteyetype = SecondaryRefTypeFind(tempref, temppig)
            else:
                self.righteye = RefTypeFind(tempref, temppig)
                self.righteyetype = SecondaryRefTypeFind(tempref, temppig)

        if(sectoralindex == 0):
            self.extraeye = 'sectoral' + str(randint(1, 6))
                
        elif hetindex == 0 and piggrade != 13:
            if random() < 0.5:
                self.lefteye = RefTypeFind(refgrade, 12)
                self.lefteyetype = SecondaryRefTypeFind(refgrade, 12)
            else:
                self.righteye = RefTypeFind(refgrade, 12)
                self.righteyetype = SecondaryRefTypeFind(refgrade, 12)

    def EyeColourName(self):
    
        eyecolours = {
        "R1" : ["Citrine", "Golden Beryl", "Yellow", "Pale Golden", "Golden", "Amber", "Light Orange", "Orange", "Cinnabar", "Auburn", "Copper", "Ice Blue", "Pink"],
        "R2" : ["Pale Citrine", "Pale Yellow", "Lemon", "Deep Yellow", "Dull Golden", "Honey", "Pale Orange", "Burnt Orange", "Dark Orange", "Russet", "Dark Topaz", "Aquamarine", "Rose"],
        "R3" : ["Lemonade Yellow", "Straw Yellow", "Dandelion Yellow", "Banana Yellow", "Sunglow Yellow", "Copal", "Dull Orange", "Rust Orange", "Topaz", "Chocolate", "Burgundy", "Sky Blue", "Magenta"],
        "R4" : ["Light Celadon", "Pale Chartreuse", "Pear Green", "Brass Yellow", "Golden Green", "Butterscotch", "Dusty Orange", "Tawny", "Jasper", "Light Brown", "Earth", "Cyan", "Periwinkle"],
        "R5" : ["Light Jade", "Pale Lime", "Spring Bud", "Chartreuse", "Pale Hazel", "Yellow Hazel", "Golden Fluorite", "Beaver Brown", "Sienna", "Chestnut", "Umber", "Baby Blue", "Violet"],
        "R6" : ["Light Fluorite", "Mantis Green", "Spring Green", "Lime", "Green Tea", "Hazel", "Green Hazel", "Dark Copal", "Cinnamon", "Raw Umber", "Sepia", "Aqua", "Glass"],
        "R7" : ["Pale Emerald", "Apple Green", "Shamrock", "Lemon-Lime", "Peridot", "Antique Brass", "Dark Hazel", "Brown-Green", "Hazel Brown", "Bronze", "Bistre Brown", "Cerulean", "Moonstone"],
        "R8" : ["Malachite", "Olivine", "Pastel Green", "Bright Green", "Pistachio", "Dull Olive", "Murky Green", "Jungle Green", "Hemlock Green", "Thatch Green", "Muddy", "Ocean Blue", "Albino Ice Blue"],
        "R9" : ["Pale Turquoise", "Mint", "Snake Green", "Dark Lime", "Fern Green", "Dull Green", "Dark Fern Green", "Olive", "Tumbleweed Green", "Bronze Olive", "Deep Bronze", "Teal", "Albino Aquamarine"],
        "R10" : ["Turquoise", "Viridian", "Green Onion", "Leaf Green", "Green", "Sap Green", "Dark Leaf Green", "Forest Green", "Dark Peridot", "Seaweed Green", "Dark Olive", "Sapphire", "Albino Sky Blue"],
        "R11" : ["Deep Turquoise", "Amazonite", "Pine Green", "Deep Leaf Green", "Jade", "Emerald", "Deep Green", "Deep Forest Green", "Dark Green", "Dark Moss Green", "Black Olive", "Azure", "Albino Azure"]
        }

        def setup(eyestring):
            eye = eyestring.split(' ; ')
            ref = eye[0]
            pig = int(eye[1].replace("albino", '13').replace('blue', '12').replace('P', ''))
            return eyecolours[ref][pig-1]
        self.lefteye = setup(self.lefteyetype)
        self.righteye = setup(self.righteyetype)
        if self.extraeyecolour != '':
            self.extraeyecolour = setup(self.extraeyetype)

    def EyeConvert(self):
        refsum = 0
        pigsum = 0
        refgrade = 1
        piggrade = 1

        for i in self.refraction:
            refsum += int(i)
        for i in self.pigmentation:
            pigsum += int(i)
            
        if refsum == 0:
            refgrade = 1
        elif refsum <= 1:
            refgrade = 2
        elif refsum <= 3:
            refgrade = 3
        elif refsum <= 5:
            refgrade = 4
        elif refsum <= 7:
            refgrade = 5
        elif refsum <= 10:
            refgrade = 6
        elif refsum <= 12:
            refgrade = 7
        elif refsum <= 14:
            refgrade = 8
        elif refsum <= 16:
            refgrade = 9
        elif refsum < 18:
            refgrade = 10
        else:
            refgrade = 11

        if pigsum == 0:
            piggrade = 1
        elif pigsum <= 1:
            piggrade = 2
        elif pigsum <= 3:
            piggrade = 3
        elif pigsum <= 5:
            piggrade = 4
        elif pigsum <= 7:
            piggrade = 5
        elif pigsum <= 10:
            piggrade = 6
        elif pigsum <= 12:
            piggrade = 7
        elif pigsum <= 14:
            piggrade = 8
        elif pigsum <= 16:
            piggrade = 9
        elif pigsum < 18:
            piggrade = 10
        else:
            piggrade = 11

        self.refraction = refgrade
        self.pigmentation = piggrade

    def ShowGenes(self, filter=True):
        self.PolyEval()
        self.Cat_Genes = [self.furLength, self.eumelanin, self.sexgene, self.dilute, self.white, self.pointgene, self.silver,
                     self.agouti, self.mack, self.ticked]
        april_fools_output = []
        if filter:
            self.Fur_Genes = []
            self.Other_Colour = []
            self.Body_Genes = []
            for x in [self.wirehair, self.laperm, self.cornish, self.urals, self.tenn, self.fleece, self.sedesp, self.ruhr, self.ruhrmod, self.lykoi]:
                if x == self.ruhrmod:
                    self.Fur_Genes.append(x)
                elif x[0] != x[1] or x[0] not in ['wh', 'lp', 'R', 'Ru', 'Tr', 'Fc', 'Hr', 'hrbd', 'Ly']:
                    self.Fur_Genes.append(x)
            for x in [self.pinkdilute, self.dilutemd, self.ext, self.corin, self.karp, self.bleach, self.ghosting, self.satin, self.glitter]:
                if x[0] != x[1] or x[0] not in ['Dp', 'dm', 'E', 'N', 'k', 'Lb', 'gh', 'St', 'Gl']:
                    self.Other_Colour.append(x)
            for x in [self.curl, self.fold, self.fourear, self.manx, self.kab, self.toybob, self.jbob, self.kub, self.ring, self.munch, self.poly, self.pax3]:
                if x == self.manx:
                    if x[0] == 'M' or x[0] == 'Ab':
                        self.Body_Genes.append(x)
                elif x[0] != x[1] or x[0] not in ['cu', 'fd', 'Dup', 'm', 'ab', 'Kab', 'tb', 'Jb', 'kub', 'Rt', 'mk', 'pd', 'NoDBE']:
                    self.Body_Genes.append(x)
            for x in self.april_fools.values():
                if x[0] != x[1] or not (x[0].islower() or x[0] == "NoDRE"):
                    april_fools_output.append(x)
        else:
            self.Fur_Genes = [self.wirehair, self.laperm, self.cornish, self.urals, self.tenn, self.fleece, self.sedesp, self.ruhr, self.ruhrmod, self.lykoi]
            self.Other_Colour = [self.pinkdilute, self.dilutemd, self.ext, self.corin, self.karp, self.bleach, self.ghosting, self.satin, self.glitter]
            self.Body_Genes = [self.curl, self.fold, self.fourear, self.manx, self.kab, self.toybob, self.jbob, self.kub, self.ring, self.munch, self.poly, self.pax3]
            april_fools_output = [self.april_fools.values()]
        self.Polygenes = ["Wideband:", self.wideband, self.wbtype, "Rufousing:", self.rufousing, self.ruftype, "Underbelly rufousing:", self.unders_ruf, self.unders_ruftype, "Saturation:", self.saturation, "Bengal:", self.bengal, self.bengtype, "Sokoke:", self.sokoke, self.soktype, "Spotted:", self.spotted, self.spottype, "Ticked:", self.tickgenes, self.ticktype, "White Grade:", self.whitegrade, "Refraction:", self.refraction, "Pigmentation:", self.pigmentation]

        if is_today(SpecialDate.APRIL_FOOLS):
            return self.Cat_Genes, "Other Fur Genes: ", self.Fur_Genes, "Other Colour Genes: ", self.Other_Colour, "Body Mutations: ", self.Body_Genes, "Polygenes: ", self.Polygenes, "April Fools:", april_fools_output
        return self.Cat_Genes, "Other Fur Genes: ", self.Fur_Genes, "Other Colour Genes: ", self.Other_Colour, "Body Mutations: ", self.Body_Genes, "Polygenes: ", self.Polygenes
    
    def Mutate(self):
        wheremutation = ["body", "furtype", "furtype", "othercoat", "othercoat", "othercoat", "maincoat", "maincoat", "maincoat", "maincoat", "maincoat", "maincoat"]
        where = choice(wheremutation)

        if where == 'body':
            self.Bodymutation()
        elif where == 'furtype':
            self.FurTypemutation()
        elif where == 'othercoat':
            self.OtherCoatmutation()
        else:
            self.MainCoatmutation()

    def Bodymutation(self):
        whichgene = ["curl", "fold", "fourear", "manx", "kab", "kub", "toybob", "jbob", "ring", "munch", "poly", "poly", "poly", "poly"]
        
        name_map = {
            "curl": "curled ears",
            "fold": "folded ears",
            "fourear": "duplicated pinnae",
            "manx": "manx/american bobtail",
            "kab": "karel bobtail",
            "kub": "kurilian bobtail",
            "toybob": "toybob bobtail",
            "jbob": "japanese bobtail",
            "ring": "ringtail",
            "munch": "munchkin",
            "poly": "polydactyly"
        }

        if self.ban_genes:
            whichgene.remove("fold")
            whichgene.remove("munch")
        
        which = choice(whichgene)

        if which in ["curl", "fold", "kub", "toybob", "munch", "poly"]:
            if self[which][-1].islower():
                self[which][-1] = self[which][-1].title()
            else:
                return self.Mutate()
        elif which in ["fourear", "jbob", "kab", "ring"]:
            if not self[which][0].islower():
                self[which][0] = self[which][0].lower()
            else:
                return self.Mutate()
        elif which == 'manx':
            if self.manx[0] in ["m", 'ab']:
                if(random() < 0.34) and not self.ban_genes:
                    self.manx[0] = 'M'
                else:
                    self.manx[0] = 'Ab'
            elif self.manx[1] in ["m", 'ab']:
                if(random() < 0.34) and not self.ban_genes:
                    self.manx[1] = 'M'
                else:
                    self.manx[1] = 'Ab'
            else:
                return self.Mutate()
        
        print(name_map[which])
    
    def FurTypemutation(self):
        whichgene = ["wirehair", "laperm", "cornish", "urals", "tenn", "fleece", "sedesp", "sedesp", "sedesp", "lykoi", "ruhr"]
        
        name_map = {
            "wirehair": "wirehair",
            "laperm": "laperm",
            "cornish": "cornish rex",
            "urals": "urals rex",
            "tenn": "tennessee rex",
            "fleece": "fleecy cloud rexing",
            "sedesp": "selkirk/devon rex or canadian hairless",
            "lykoi": "lykoi",
            "ruhr": "russian hairless"
        }

        if self.ban_genes:
            whichgene.remove("lykoi")
            whichgene.remove("ruhr")

        which = choice(whichgene)

        if which in ["wirehair", "laperm", "ruhr"]:
            if self[which][-1].islower():
                self[which][-1] = self[which][-1].title()
            else:
                return self.Mutate()
        elif which in ["cornish", "urals", "tenn", "fleece", "lykoi"]:
            if not self[which][0].islower():
                self[which][0] = self[which][0].lower()
            else:
                return self.Mutate()

        elif which == 'sedesp':
            if 'Hr' not in self.sedesp:
                return self.Mutate()
            i = self.sedesp.index("Hr")
            self.sedesp[i] = "hr" if random() < 0.25 and not self.ban_genes else choice(["re", "re", "Se"])
            
        print(name_map[which])

    def OtherCoatmutation(self):
        whichgene = ["dilutemd", "pinkdilute", "ext", "corin", "karp", "bleach", "ghosting", "satin", "glitter"]

        name_map = {
            "dilutemd": "dilute modifier",
            "pinkdilute": "ukrainian chocolate (pink-eyed dilute)",
            "ext": "amber/russet/carnelian",
            "corin": "sunshine/extreme sunshine/flaxen gold (copper)",
            "karp": "karpati",
            "bleach": "laperm bleaching",
            "ghosting": "ghosting",
            "satin": "satin",
            "glitter": "glitter"
        }

        if self.ban_genes:
            whichgene.remove("pinkdilute")

        which = choice(whichgene)

        if which in ["dilutemd", "karp", "ghosting"]:
            if self[which][-1].islower():
                self[which][-1] = self[which][-1].title()
            else:
                return self.Mutate()
        elif which in ["pinkdilute", "bleach", "satin", "glitter"]:
            if not self[which][0].islower():
                self[which][0] = self[which][0].lower()
            else:
                return self.Mutate()

        elif which == 'ext':
            if 'E' not in self.ext:
                return self.Mutate()
                
            i = self.ext.index("E")
            self.ext[i] = choice(['ea', 'er', 'ec'])
        elif which == 'corin':
            if 'N' not in self.corin:
                return self.Mutate()
                
            i = self.corin.index("N")
            self.corin[i] = choice(['sh', 'sg', 'fg'])

        print(name_map[which])
    
    def MainCoatmutation(self):
        whichgene = ["furLength", "eumelanin", "sexgene", "dilute", "white", "pointgene", "silver", "agouti", "mack", "ticked", 'pax3']
        which = choice(whichgene)

        name_map = {
            "furLength": "longhair",
            "eumelanin": "chocolate/cinnamon",
            "sexgene": "red/black",
            "dilute": "dilute",
            "white": "KIT locus",
            "pointgene": "colour restriction/mocha/albino",
            "silver": "silver",
            "agouti": "solid",
            "mack": "blotched",
            "ticked": "ticked",
            "pax3": "PAX3 dominant blue eyes"
        }

        if which in ["silver", "ticked"]:
            if self[which][-1].islower():
                self[which][-1] = self[which][-1].title()
            else:
                return self.Mutate()
        elif which in ["furLength", "dilute", "mack"]:
            if not self[which][0].islower():
                self[which][0] = self[which][0].lower()
            else:
                return self.Mutate()

        elif which == 'eumelanin':
            if self.eumelanin[0] == 'bl':
                return self.Mutate()

            if "B" in self.eumelanin and "b" in self.eumelanin:
                al = choice(["B", "b"])
                i = self.eumelanin.index(al)
                self.eumelanin[i] = "bl" if al == "b" else "b"
            elif "B" in self.eumelanin:
                i = self.eumelanin.index("B")
                self.eumelanin[i] = "b"
            else:
                i = self.eumelanin.index("b")
                self.eumelanin[i] = "bl"
        elif which == 'sexgene':
            i = 0
            while self.sexgene[i] == 'Y':
                randint(0, len(self.sexgene))

            if(self.sexgene[i] == 'o'):
                self.sexgene[i] = 'O'
            else:
                self.sexgene[i] = 'o'
        elif which == 'white':
            if 'w' not in self.white:
                return self.Mutate()
            i = self.white.index("w")
            if random() < 0.1:
                self.white[i] = choice(['wt', 'wsal'])
            elif random() < 0.2:
                self.white[i] = "W"
            else:
                self.white[i] = choice(['wg', 'ws', 'ws', 'ws', 'ws'])
        elif which == 'pointgene':
            if 'C' not in self.pointgene:
                return self.Mutate()
            i = self.pointgene.index("C")
            self.pointgene[i] = choice([choice(['c', 'cm']), choice(['cs', 'cb']), choice(['cs', 'cb']), choice(['cs', 'cb']), choice(['cs', 'cb'])])
            if self.ban_genes:
                self.pointgene[i] = choice(['cm', choice(['cs', 'cb']), choice(['cs', 'cb']), choice(['cs', 'cb']), choice(['cs', 'cb'])])
        elif which == 'agouti':
            if "A" not in self.agouti:
                return self.Mutate()
            i = self.agouti.index("A")
            self.agouti[i] = "a"
        else:
            if "NoDBE" not in self.pax3:
                return self.Mutate()
            i = self.pax3.index("NoDBE")
            self.pax3[i] = choice(['DBEcel', 'DBEre', 'DBEalt'])

        print(name_map[which])
    
    def GenerateSomatic(self):
        self.somatic["base"] = choice(['Somatic/leftface', 'Somatic/rightface', 'Somatic/tail', 
                                    'underbelly1', "BEARD", "BELLY", "BIB",
                                    'right front bicolour2', 'left front bicolour2', 
                                    'right back bicolour2', 'left back bicolour2', 
                                    'right front bicolour1', 'left front bicolour1', 
                                    'right back bicolour1', 'left back bicolour1', 
                                    "LEFTEAR", "RIGHTEAR", "BACKSPOT", "TAILTIP"])

        possible_mutes = {
        "furtype" : ["wirehair", "laperm", "cornish", "urals", "tenn", "fleece", "sedesp"],
        "other" : ["pinkdilute", "ext", "corin", "karp"],
        "main" : ["eumelanin", "sexgene", "dilute", "white", "pointgene", "silver", "agouti"]
        }
        filtered_mutes = {
        "furtype" : ["wirehair", "laperm", "cornish", "urals", "tenn", "fleece", "sedesp"],
        "other" : ["pinkdilute", "ext", "corin", "karp"],
        "main" : ["eumelanin", "sexgene", "dilute", "white", "pointgene", "silver", "agouti"]
        }

        for gene in possible_mutes["furtype"]:
            if gene in ['wirehair', 'laperm', 'sedesp']:
                if self[gene][0] in ['Wh', 'Lp', 'Se', 'hr', 're']:
                    filtered_mutes["furtype"].remove(gene)
            try:
                if self[gene][0] in ['r', 'ru', 'tr', 'fc']:
                    filtered_mutes["furtype"].remove(gene)
                elif self[gene][1] in ['R', 'Ru', 'Tr', 'Fc']:
                    filtered_mutes["furtype"].remove(gene)
            except:
                continue
        for gene in possible_mutes["other"]:
            if gene == 'corin' and (self.agouti[0] == 'a' or self.ext[0] == 'Eg'):
                filtered_mutes["other"].remove(gene)
                continue
            elif gene in ['ext', 'karp', 'ghosting']:
                if self[gene][0] in ['Eg', 'K', 'Gh']:
                    filtered_mutes["other"].remove(gene)
                    continue
            if self[gene][0] in ['dp', 'ec', 'ea', 'er', 'sh', 'sg', 'fg', 'lb', 'st', 'gl']:
                filtered_mutes["other"].remove(gene)
            elif self[gene][1] in ['Dp', 'E', 'N', 'Lb', 'St', 'Gl']:
                filtered_mutes["other"].remove(gene)
        for gene in possible_mutes["main"]:
            if gene in ['mack', 'ticked', 'silver'] and (self.agouti[0] == 'a' or self.ext[0] == 'Eg'):
                filtered_mutes["main"].remove(gene)
                continue
            elif gene == 'agouti' and (self.ext[0] == 'Eg' or 'o' not in self.sexgene):
                filtered_mutes["main"].remove(gene)
                continue
            elif gene in ['white']:
                if self[gene][0] in ['W', 'ws', 'wt']:
                    filtered_mutes["main"].remove(gene)
                    continue
            if self[gene][0] in ['I', 'b', 'bl', 'd', 'wg', 'wsal', 'cs', 'cb', 'cm', 'c', 'Apb', 'a']:
                filtered_mutes["main"].remove(gene)
            elif len(self[gene]) > 1 and self[gene][1] in ['B', 'D', 'w', 'C', 'A']:
                filtered_mutes["main"].remove(gene)
            
        if "eumelanin" in filtered_mutes["main"] and self.sexgene[0] != "o":
            filtered_mutes["main"].remove("eumelanin")
        
        whichgene = ['furtype', 'other', 'main', 'other', 'main', 'main']
        if self.white[0] == 'W' or (self.white[1] in ['ws', 'wt'] and self.whitegrade == 5):
            whichgene = ['furtype']
        for cate in ['furtype', 'other', 'main']:
            if len(filtered_mutes[cate]) == 0:
                while cate in whichgene:
                    whichgene.remove(cate)
        if len(whichgene) > 0:
            self.somatic["gene"] = choice(filtered_mutes[choice(whichgene)])
        else:
            self.somatic = {}
            return

        
        if self.white[1] in ['ws', 'wt'] and self.somatic["base"] not in ['Somatic/leftface', 'Somatic/rightface', 'Somatic/tail', "LEFTEAR", "RIGHTEAR", "BACKSPOT"]:
            self.somatic["base"] = choice(['Somatic/leftface', 'Somatic/rightface', 'Somatic/tail', "LEFTEAR", "RIGHTEAR", "BACKSPOT"])
        
        if self.somatic["gene"] in possible_mutes["furtype"]:
            self.somatic["base"] = "Somatic/tail"

        
        alleles = {
            "wirehair" : ['Wh'],
            "laperm" : ['Lp'],
            "cornish" : ['r'],
            "urals" : ['ru'],
            "tenn" : ['tr'],
            "fleece" : ['fc'],
            "sedesp" : ['Se'],

            'pinkdilute' : ['dp'],
            "ext" : ['ec', 'er', 'ea'],
            "corin" : ['sh', 'sg', 'fg'],
            "karp" : ['K'],
            "bleach" : ['lb'],
            "ghosting" : ['Gh'],

            'eumelanin' : ['b', 'bl'],
            'sexgene' : ['O'],
            "dilute" : ['d'],
            "white" : ['W', 'wsal'],
            "pointgene" : ['cb', 'cs', 'cm', 'c'],
            "silver" : ['I'],
            "agouti" : ['a']
        }

        self.somatic["allele"] = choice(alleles[self.somatic['gene']])
        if self.somatic['gene'] == 'sexgene' and self.sexgene[0] == 'O':
            self.somatic["allele"] = 'o'

    def FormatSomatic(self):
        body = {
            "Somatic/leftface" : "face",
            "Somatic/rightface" : "face",
            "Somatic/tail" : 'tail',
            "underbelly1" : 'underbelly',
            'right front bicolour2' : 'front leg', 
            'left front bicolour2' : 'front leg', 
            'right back bicolour2' : 'back leg', 
            'left back bicolour2' : 'back leg',
            'right front bicolour1' : 'front leg', 
            'left front bicolour1' : 'front leg', 
            'right back bicolour1' : 'back leg', 
            'left back bicolour1' : 'back leg',
            'LEFTEAR' : 'ear', 
            'RIGHTEAR' : 'ear', 
            "BACKSPOT": "back",
            "TAILTIP": "tail tip",
            "BEARD": "chin",
            "BELLY": "belly",
            "BIB": "chest"
        }
        if not self.somatic.get('gene', False):
            return ""

        alleles = {
            "wirehair" : "Wirehair",
            "laperm" : "LaPerm",
            "cornish" : "Cornish rex",
            "urals" : "Urals rex",
            "tenn" : "Tennessee rex",
            "fleece" : "Fleecy cloud rexing",
            "sedesp" : "Selkirk rexing",

            'pinkdilute' : "Pink-eyed dilute",
            "ext" : {
                'ec': 'Carnelian', 
                'er' : 'Russet', 
                'ea' : 'Amber'
            },
            "corin" : {
                'sh' : 'Sunshine', 
                'sg' : 'Extreme sunshine', 
                'fg' : 'Flaxen gold'},
            "karp" : 'Karpati',
            "bleach" : 'Bleaching',
            "ghosting" : 'Ghosting',

            'eumelanin' : {'b' : 'Chocolate', 'bl' : 'Cinnamon'},
            'sexgene' : {
                'O': 'Red',
                'o' : 'Black'
            },
            "dilute" : 'Dilute',
            "white" : {'W' : 'Dominant white', 'wsal' : 'Salmiak'},
            "pointgene" : {'cb' : 'Sepia', 'cs' : 'Colourpoint', 'cm' : 'Mocha', 'c' : 'Albino'},
            "silver" : "Silver",
            "agouti" : "Solid"
        }
        try:
            return "Mutated " + alleles[self.somatic['gene']].get(self.somatic['allele']) + " on " + body[self.somatic['base']]
        except:
            try:
                return "Mutated " + alleles[self.somatic['gene']] + " on " + body[self.somatic['base']]
            except:
                return self.somatic['gene'] + " mutated on " + body[self.somatic['base']]






