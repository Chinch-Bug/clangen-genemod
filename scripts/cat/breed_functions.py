
from random import choice, randint, random
import math

class Breed_generator:
    @staticmethod
    def AllColours(genoclass, special):
        # FUR LENGTH
        
        for i in range(2):
            if genoclass.odds["longhair"] > 0 and randint(1, genoclass.odds["longhair"]) == 1:
                genoclass.furLength[i] = "l"
            else:
                genoclass.furLength[i] = "L"

        # EUMELANIN

            if genoclass.odds["cinnamon"] > 0 and (randint(1, round(genoclass.odds["cinnamon"]/2)) == 1 or genoclass.odds["cinnamon"] == 1):
                genoclass.eumelanin[i] = "bl"
            elif genoclass.odds["chocolate"] > 0 and (randint(1, round(genoclass.odds["chocolate"]/2)) == 1 or genoclass.odds["chocolate"] == 1):
                genoclass.eumelanin[i] = "b"
            else:
                genoclass.eumelanin[i] = "B"

        # RED GENE
        if genoclass.odds['XXX/XXY'] > 0 and randint(1, genoclass.odds['XXX/XXY']) == 1:
            genoclass.sexgene = ["", "", ""]
        else:
            genoclass.sexgene = ["", ""]
        
        for i in range(len(genoclass.sexgene)):
            if genoclass.odds["red"] > 0 and randint(1, genoclass.odds["red"]) == 1:
                genoclass.sexgene[i] = "O"
            else:
                genoclass.sexgene[i] = "o"

        if (random() < 0.5 and special != "fem") or special == "masc":
            genoclass.sexgene[-1] = "Y"
            genoclass.sex = "tom"
        else:
            genoclass.sex = "molly"

        if(random() < 0.05):
            genoclass.specialred = choice(['cameo', 'cameo', 'cameo', 'cameo', 'cameo', 'cameo', 'cameo', 'cameo', 'merle', 'merle', 'merle', 'merle'])

        # DILUTE

        for i in range(2):
            if genoclass.odds["dilute"] > 0 and randint(1, genoclass.odds["dilute"]) == 1:
                genoclass.dilute[i] = "d"
            else:
                genoclass.dilute[i] = "D"

        # WHITE

            if genoclass.odds["dominant white"] > 0 and randint(1, genoclass.odds["dominant white"]) == 1:
                genoclass.white[i] = "W"
            elif genoclass.odds["white spotting"] > 0 and randint(1, genoclass.odds["white spotting"]) == 1:
                genoclass.white[i] = "ws"
            else:
                genoclass.white[i] = "w"

        # ALBINO

            if genoclass.odds["sepia"] > 0 and (randint(1, round(genoclass.odds["sepia"]/2)) == 1 or genoclass.odds["sepia"] == 1):
                genoclass.pointgene[i] = "cb"
            elif genoclass.odds["colourpoint"] > 0 and (randint(1, round(genoclass.odds["colourpoint"]/2)) == 1 or genoclass.odds["colourpoint"] == 1):
                genoclass.pointgene[i] = "cs"
            else:
                genoclass.pointgene[i] = "C"

        # SILVER

            if genoclass.odds["silver"] > 0 and randint(1, genoclass.odds["silver"]) == 1:
                genoclass.silver[i] = "I"
            else:
                genoclass.silver[i] = "i"

        # AGOUTI

            if genoclass.odds["solid"] > 0 and randint(1, genoclass.odds["solid"]) == 1:
                genoclass.agouti[i] = "a"
            else:
                genoclass.agouti[i] = "A"

        # MACKEREL
            if genoclass.odds["blotched"] > 0 and randint(1, genoclass.odds["blotched"]) == 1:
                genoclass.mack[i] = "mc"
            else:
                genoclass.mack[i] = "Mc"

        # TICKED
            if genoclass.odds["ticked"] > 0 and randint(1, genoclass.odds["ticked"]) == 1:
                genoclass.ticked[i] = "Ta"
            else:
                genoclass.ticked[i] = "ta"

        if genoclass.odds["breakthrough"] > 0 and randint(1, genoclass.odds["breakthrough"]) == 1:
            genoclass.breakthrough = True

        a = randint(1, 4)

        if a == 1:
            genoclass.ruhrmod = ["hi", "hi"]
        elif a == 4:
            genoclass.ruhrmod = ["ha", "ha"]
        else:
            genoclass.ruhrmod = ["hi", "ha"]

        genoclass.wideband = ''
        genoclass.rufousing = ''
        genoclass.spotted = ''
        genoclass.tickgenes = ''
        genoclass.bengal = ''
        genoclass.sokoke = ''
        
        for i in range(0, 8):
            genoclass.wideband += choice(genoclass.odds["wideband_kittypet"])
            genoclass.wbsum += int(genoclass.wideband[i])

        for i in range(0, 4):
            genoclass.rufousing += choice(genoclass.odds["rufousing_kittypet"])
            genoclass.rufsum += int(genoclass.rufousing[i])

        for i in range(0, 4):
            genoclass.spotted += choice(genoclass.odds["spotted_kittypet"])
            genoclass.spotsum += int(genoclass.spotted[i])

        for i in range(0, 4):
            genoclass.tickgenes += choice(genoclass.odds["tickmod_kittypet"])
            genoclass.ticksum += int(genoclass.tickgenes[i])

        for i in range(0, 4):
            genoclass.bengal += choice(genoclass.odds["bengal_kittypet"])
            genoclass.bengsum += int(genoclass.bengal[i])

        for i in range(0, 4):
            genoclass.sokoke += choice(genoclass.odds["sokoke_kittypet"])
            genoclass.soksum += int(genoclass.sokoke[i])
            
        genoclass.body_value = randint(genoclass.body_indexes[2]+1, genoclass.body_indexes[3])
        genoclass.height_value = randint(genoclass.height_indexes[3]+1, genoclass.height_indexes[4])

        return genoclass
    
    @staticmethod
    def Aby(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH

        genoclass.longtype = 'long'
        
        if random() < 0.01:
            genoclass.furLength = ["L", "l"]
        elif random() < 0.25:
            genoclass.furLength = ["l", "l"]
        else:
            genoclass.furLength = ["L", "L"]

        # EUMELANIN

        for i in range(2):
            if randint(1, 3) == 1:
                genoclass.eumelanin[i] = "bl"
            elif randint(1, 6) == 1:
                genoclass.eumelanin[i] = "b"
            else:
                genoclass.eumelanin[i] = "B"

        # RED GENE
        if genoclass.odds['XXX/XXY'] > 0 and randint(1, genoclass.odds['XXX/XXY']) == 1:
            genoclass.sexgene = ["", "", ""]
        else:
            genoclass.sexgene = ["", ""]
        
        for i in range(len(genoclass.sexgene)):
            if randint(1, 10) == 1:
                genoclass.sexgene[i] = "O"
            else:
                genoclass.sexgene[i] = "o"

        if (random() < 0.5 and special != "fem") or special == "masc":
            genoclass.sexgene[-1] = "Y"
            genoclass.sex = "tom"
        else:
            genoclass.sex = "molly"

        # WHITE

        genoclass.white = ["w", "w"]

        # ALBINO

        genoclass.pointgene = ["C", "C"]

        # SILVER

        a = randint(1, 36)

        if a == 1:
            genoclass.silver = ["I", "I"]
        elif a < 8:
            genoclass.silver = ["I", "i"]
        else:
            genoclass.silver = ["i", "i"]

        # AGOUTI

        genoclass.agouti = ["A", "A"]

        # MACKEREL

        genoclass.mack = ["Mc", "Mc"]

        # TICKED

        genoclass.ticked = ["Ta", "Ta"]

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]

        genoclass.rufousing = ''
        genoclass.tickgenes = ''
        genoclass.bengal = ''
        genoclass.sokoke = ''
        
        while genoclass.wbsum > 11 or genoclass.wbsum < 6:
            genoclass.wideband = ""
            genoclass.wbsum = 0
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])

        for i in range(0, 4):
            genoclass.rufousing += '2'

        for i in range(0, 4):
            genoclass.tickgenes += '2'

        for i in range(0, 4):
            genoclass.bengal += '0'

        for i in range(0, 4):
            genoclass.sokoke += '0'

        genoclass.body_value = randint(genoclass.body_indexes[3]+1, genoclass.body_indexes[4])

        genoclass.breeds["Abyssinian"] = 100
        return genoclass
    
    @staticmethod
    def AmBob(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        #  manx + kab + toybob + jbob + kub + ring

        genoclass.manx = ["Ab", "ab"]

        genoclass.breeds["American Bobtail"] = 100
        
        return genoclass
    
    @staticmethod
    def AmCurl(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        for i in range(2):
            if randint(1, 50) == 1:
                genoclass.dilutemd[i] = "Dm"

        # curl + fold
        genoclass.curl = ["Cu", "Cu"]
        
        genoclass.breeds["American Curl"] = 100
        return genoclass
    
    @staticmethod
    def AmSH(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)

        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        if(random() < 0.5):
            genoclass.wirehair = ["Wh", "Wh"]
        # EUMELANIN

        for i in range(2):
            if randint(1, 20) == 1:
                genoclass.eumelanin[i] = "bl"
            elif randint(1, 15) == 1:
                genoclass.eumelanin[i] = "b"
            else:
                genoclass.eumelanin[i] = "B"

        # ALBINO

        genoclass.pointgene = ["C", "C"]

        genoclass.body_value = randint(genoclass.body_indexes[0]+1, genoclass.body_indexes[1])
        
        genoclass.breeds["American Shorthair"] = 100
        return genoclass
    
    @staticmethod
    def AmBurm(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]
        
        # EUMELANIN

        for i in range(2):
            if randint(1, 3) == 1:
                genoclass.eumelanin[i] = "b"
            else:
                genoclass.eumelanin[i] = "B"

        # RED GENE

        for i in range(len(genoclass.sexgene)):
            if genoclass.sexgene[i] == 'O':
                genoclass.sexgene[i] = 'o'

        # WHITE

        genoclass.white = ["w", "w"]

        # ALBINO

        genoclass.pointgene = ["cb", "cb"]
        if random() < 0.2:
            genoclass.pointgene = ["C", "C"]
            genoclass.dilute = ["D", "D"]
            genoclass.eumelanin = ["B", "B"]

        # SILVER

        genoclass.silver = ["i", "i"]

        # AGOUTI

        genoclass.agouti = ["a", "a"]

        # TICKED

        genoclass.ticked = ["Ta", "Ta"]

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]

        genoclass.tickgenes = ''
        genoclass.bengal = ''
        genoclass.sokoke = ''
        
        genesmild = ["2", "2", "1", "1", "1", "1", "1", "0", "0", "0", "0", "0", "0"]

        for i in range(0, 4):
            genoclass.tickgenes += choice(genesmild)
            genoclass.ticksum += int(genoclass.tickgenes[i])

        for i in range(0, 4):
            genoclass.bengal += '0'

        for i in range(0, 4):
            genoclass.sokoke += '0'

        genoclass.body_value = randint(genoclass.body_indexes[0]+1, genoclass.body_indexes[1])
        
        genoclass.breeds["American Burmese/Bombay"] = 100
        return genoclass
    
    @staticmethod
    def Aphrodite(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        # ALBINO

        genoclass.pointgene = ["C", "C"]

        genoclass.height_value = randint(genoclass.height_indexes[4]+1, genoclass.height_indexes[8])
        
        genoclass.breeds["Aphrodite"] = 100
        return genoclass
    
    @staticmethod
    def Arab(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # EUMELANIN

        genoclass.eumelanin = ["B", "B"]

        # ALBINO

        genoclass.pointgene = ["C", "C"]

        # SILVER

        genoclass.silver = ["i", "i"]

        # TABBY

        genoclass.mack = ["Mc", "Mc"]

        genoclass.ticked = ["ta", "ta"]

        #ruhr + ruhrmod + lykoi

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]
        
        while genoclass.wbsum > 11 or genoclass.wideband == "":
            genoclass.wideband = ""
            genoclass.wbsum = 0
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])

        genoclass.tickgenes = ''
        genoclass.bengal = ''
        genoclass.sokoke = ''
        for i in range(0, 4):
            genoclass.tickgenes += '0'
            genoclass.ticksum += int(genoclass.tickgenes[i])

        for i in range(0, 4):
            genoclass.bengal += '0'
            genoclass.bengsum += int(genoclass.bengal[i])

        for i in range(0, 4):
            genoclass.sokoke += '0'
            genoclass.soksum += int(genoclass.sokoke[i])
        
        genoclass.breeds["Arabian Mau"] = 100
        return genoclass
    
    @staticmethod
    def Asian(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        genoclass.white = ["w", "w"]

        for i in range(2):
            if randint(1, 50) == 1:
                genoclass.dilutemd[i] = "Dm"

        # ALBINO

        for i in range(2):
            if random() < 0.75:
                genoclass.pointgene[i] = "cb"
            else:
                genoclass.pointgene[i] = "C"

        # MACKEREL

        genoclass.mack = ["Mc", "Mc"]

        genoclass.ticked = ["Ta", "Ta"]

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]
        
        if random() < 0.25:
            while genoclass.wbsum < 14:
                genoclass.wideband = ""
                genoclass.wbsum = 0
                for i in range(0, 8):
                    genoclass.wideband += choice(genes)
                    genoclass.wbsum += int(genoclass.wideband[i])
        
        genoclass.tickgenes = ''
        genoclass.ticksum = 0
        genesmild = ["2", "2", "1", "1", "1", "1", "1", "0", "0", "0", "0", "0", "0"]

        for i in range(0, 4):
            genoclass.tickgenes += choice(genesmild)
            genoclass.ticksum += int(genoclass.tickgenes[i])

        genoclass.body_value = randint(genoclass.body_indexes[1]+1, genoclass.body_indexes[2])
        
        genoclass.breeds["Asian/Burmese"] = 100
        return genoclass
    
    @staticmethod
    def AusMist(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)

        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # EUMELANIN

        for i in range(2):
            if randint(1, 5) == 1:
                genoclass.eumelanin[i] = "bl"
            elif randint(1, 3) == 1:
                genoclass.eumelanin[i] = "b"
            else:
                genoclass.eumelanin[i] = "B"

        # RED GENE

        for i in range(len(genoclass.sexgene)):
            if genoclass.sexgene[i] == 'O':
                genoclass.sexgene[i] = 'o'
        
        # WHITE

        genoclass.white = ["w", "w"]

        # ALBINO

        genoclass.pointgene = ["cb", "cb"]

        # SILVER

        genoclass.silver = ["i", "i"]

        # AGOUTI

        genoclass.agouti = ["A", "A"]

        genoclass.ticked = ["ta", "ta"]

        for i in range(2):
            if randint(1, 50) == 1:
                genoclass.dilutemd[i] = "Dm"

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]
        
        while genoclass.wbsum > 11 or genoclass.wideband == "":
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])

        genoclass.spotted = ''
        for i in range(0, 4):
            genoclass.spotted += '2'
        
        genoclass.breeds["Australian Mist"] = 100
        return genoclass
    
    @staticmethod
    def Bengal(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        a = randint(1, 10)

        if a < 7:
            genoclass.furLength = ["L", "L"]
        elif a == 10:
            genoclass.furLength = ["l", "l"]
        else:
            genoclass.furLength = ["L", "l"]

        # EUMELANIN

        for i in range(2):
            if randint(1, 30) == 1:
                genoclass.eumelanin[i] = "bl"
            elif randint(1, 25) == 1:
                genoclass.eumelanin[i] = "b"
            else:
                genoclass.eumelanin[i] = "B"

        # RED GENE
        if genoclass.odds['XXX/XXY'] > 0 and randint(1, genoclass.odds['XXX/XXY']) == 1:
            genoclass.sexgene = ["", "", ""]
        else:
            genoclass.sexgene = ["", ""]
        
        for i in range(len(genoclass.sexgene)):
            if randint(1, 25) == 1:
                genoclass.sexgene[i] = "O"
            else:
                genoclass.sexgene[i] = "o"

        if (random() < 0.5 and special != "fem") or special == "masc":
            genoclass.sexgene[-1] = "Y"
            genoclass.sex = "tom"
        else:
            genoclass.sex = "molly"
        
        # DILUTE

        a = randint(1, 10)

        if a < 7:
            genoclass.dilute = ["D", "D"]
        elif a == 10:
            genoclass.dilute = ["d", "d"]
        else:
            genoclass.dilute = ["D", "d"]

        # WHITE

        genoclass.white = ["w", "w"]

        # ALBINO

        for i in range(2):
            if randint(1, 5) == 1:
                genoclass.pointgene[i] = "cb"
            elif randint(1, 5) == 1:
                genoclass.pointgene[i] = "cs"
            else:
                genoclass.pointgene[i] = "C"

        # AGOUTI

        for i in range(2):
            if randint(1, 5) == 1:
                genoclass.agouti[i] = "Apb"
            elif randint(1, 3) == 1:
                genoclass.agouti[i] = "a"
            else:
                genoclass.agouti[i] = "A"

        if genoclass.agouti == ['a', 'a'] and random() > 0.25:
            genoclass.agouti = ['A', 'a']

        genoclass.ticked = ["ta", "ta"]

        # karp + bleach + ghosting + satin + glitter

        if random() < 0.2:
            genoclass.glitter = ["gl", "gl"]
        elif random() < 0.25:
            genoclass.glitter[1] = "gl"

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]

        genoclass.rufousing = ''
        genoclass.rufsum = 0
        genoclass.spotted = ''
        genoclass.spotsum = 0
        genoclass.bengal = ''
        genoclass.bengsum = 0
        
        while genoclass.wbsum > 11 or genoclass.wideband == "":
            genoclass.wideband = ""
            genoclass.wbsum = 0
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])

        for i in range(0, 4):
            genoclass.rufousing += '2'
            genoclass.rufsum += int(genoclass.rufousing[i])

        for i in range(0, 4):
            genoclass.spotted += '2'
            genoclass.spotsum += int(genoclass.spotted[i])

        for i in range(0, 4):
            genoclass.bengal += '2'
            genoclass.bengsum += int(genoclass.bengal[i])

        genoclass.height_value = randint(genoclass.height_indexes[3]+1, genoclass.height_indexes[5])
        
        genoclass.breeds["Bengal"] = 100
        return genoclass
    
    @staticmethod
    def Birman(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.longtype = 'long'
        if random() < 0.125:
            genoclass.furLength = ["L", choice(["L", "l"])]
        else:
            genoclass.furLength = ["l", "l"]

        # WHITE

        for i in range(2):
            genoclass.white[i] = "wg"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "cs"

        for i in range(2):
            if randint(1, 50) == 1:
                genoclass.dilutemd[i] = "Dm"

        genoclass.breeds["Birman"] = 100
        return genoclass
    
    @staticmethod
    def Brazil(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # ALBINO

        genoclass.pointgene = ["C", "C"]
        
        genoclass.breeds["Brazilian Shorthair"] = 100
        return genoclass
    
    @staticmethod
    def British(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        for i in range(2):
            if randint(1, 50) == 1:
                genoclass.dilutemd[i] = "Dm"

        #sunshine

        for i in range(2):
            if randint(1, 40) == 1:
                genoclass.corin[i] = "fg" #Flaxen Gold
            else:
                genoclass.corin[i] = "N" #No

        # curl + fold

        if random() < 0.2 and not genoclass.ban_genes:
            genoclass.fold[0] = "Fd"

        if genoclass.fold[0] == 'fd' and random() < 0.1:
            genoclass.pax3[0] = 'DBEcel'
            genoclass.pointgene = ['C', 'C']
            genoclass.white = ['w', 'w']

        genoclass.body_value = randint(genoclass.body_indexes[0]+1, genoclass.body_indexes[1])
        genoclass.height_value = randint(genoclass.height_indexes[3]+1, genoclass.height_indexes[6])
        
        genoclass.breeds["British"] = 100
        return genoclass
    
    @staticmethod
    def Ceylon(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # EUMELANIN

        for i in range(2):
            genoclass.eumelanin[i] = "B"

        # WHITE

            genoclass.white[i] = "w"

        # ALBINO

            genoclass.pointgene[i] = "C"

        # SILVER

        genoclass.silver = ["i", "i"]

        # AGOUTI

        for i in range(2):
            genoclass.agouti[i] = "A"

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]

        while genoclass.wbsum > 11 or genoclass.wideband == "":
            genoclass.wideband = ""
            genoclass.wbsum = 0
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])

        genoclass.bengal = ''
        genoclass.sokoke = ''
        for i in range(0, 4):
            genoclass.bengal += '0'
            genoclass.bengsum += int(genoclass.bengal[i])

        for i in range(0, 4):
            genoclass.sokoke += '0'
            genoclass.soksum += int(genoclass.sokoke[i])
        
        genoclass.breeds["Ceylon"] = 100
        return genoclass
    
    @staticmethod
    def Chartreux(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)
        
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # EUMELANIN

        for i in range(2):
            genoclass.eumelanin[i] = "B"

        # RED GENE

        for i in range(len(genoclass.sexgene)):
            if genoclass.sexgene[i] == 'O':
                genoclass.sexgene[i] = 'o'
        
        # DILUTE

        genoclass.dilute = ["d", "d"]

        # WHITE

        for i in range(2):
            genoclass.white[i] = "w"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "C"

        # SILVER

        genoclass.silver = ["i", "i"]

        # AGOUTI

        for i in range(2):
            genoclass.agouti[i] = "a"

        genoclass.tickgenes = ''
        genoclass.bengal = ''
        genoclass.sokoke = ''

        for i in range(0, 4):
            genoclass.tickgenes += '0'
            genoclass.ticksum += int(genoclass.tickgenes[i])

        for i in range(0, 4):
            genoclass.bengal += '0'
            genoclass.bengsum += int(genoclass.bengal[i])

        for i in range(0, 4):
            genoclass.sokoke += '0'
            genoclass.soksum += int(genoclass.sokoke[i])
        
        genoclass.breeds[choice(["Korat", "Chartreux"])] = 100
        if genoclass.breeds.get("Korat", False):
            genoclass.body_value = randint(genoclass.body_indexes[3]+1, genoclass.body_indexes[4])
        return genoclass
    
    @staticmethod
    def Chausie(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)
        
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # EUMELANIN

        for i in range(2):
            genoclass.eumelanin[i] = "B"

        # RED GENE

        for i in range(len(genoclass.sexgene)):
            if genoclass.sexgene[i] == 'O':
                genoclass.sexgene[i] = 'o'
        
        # DILUTE

        genoclass.dilute = ["D", "D"]

        # WHITE

        for i in range(2):

            genoclass.white[i] = "w"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "C"

        # SILVER

        genoclass.silver = ["i", "i"]

        # AGOUTI

        for i in range(2):
            if randint(1, 3) == 1:
                genoclass.agouti[i] = "a"
            else:
                genoclass.agouti[i] = "A"

        # TICKED

        genoclass.ticked = ["Ta", "Ta"]

        # ext

        for i in range(2):
            a = randint(1, 8)

            if a == 1:
                genoclass.ext[i] = "Eg"

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]

        genoclass.bengal = ''
        genoclass.sokoke = ''

        while genoclass.wbsum > 11 or genoclass.wideband == "":  
            genoclass.wideband = ''
            genoclass.wbsum = 0    
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])

        for i in range(0, 4):
            genoclass.bengal += '0'
            genoclass.bengsum += int(genoclass.bengal[i])

        for i in range(0, 4):
            genoclass.sokoke += '0'
            genoclass.soksum += int(genoclass.sokoke[i])

        genoclass.height_value = randint(genoclass.height_indexes[3]+1, genoclass.height_indexes[9])
        
        genoclass.breeds["Chausie"] = 100
        return genoclass
    
    @staticmethod
    def Clippercat(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        # ALBINO

        for i in range(2):
            d = randint(1, 5)

            if d == 1:
                genoclass.pointgene[i] = "cs"
            else:
                genoclass.pointgene[i] = "C"

        # munch + poly + altai

        genoclass.poly = ["Pd", "Pd"]

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]
        
        while genoclass.wbsum > 11 or genoclass.wideband == "":  
            genoclass.wideband = ''
            genoclass.wbsum = 0    
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])
        
        genoclass.breeds["Clippercat"] = 100
        return genoclass
    
    @staticmethod
    def Cornish(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]


        # YORK, WIREHAIR, LAPERM, CORNISH, URAL, TENN, FLEECE

        genoclass.cornish = ["r", "r"]

        genoclass.breeds[choice(["Cornish Rex", "German Rex"])] = 100
        
        if genoclass.breeds.get("Cornish Rex", False):
            for i in range(2):
                if randint(1, 50) == 1:
                    genoclass.dilutemd[i] = "Dm"
            genoclass.body_value = randint(genoclass.body_indexes[3]+1, genoclass.body_indexes[4])
        return genoclass
    
    @staticmethod
    def Devon(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        if random() < 0.95:
            genoclass.furLength = ["L", "L"]
        else:
            genoclass.furLength = ["l", "l"]

        # YORK, WIREHAIR, LAPERM, CORNISH, URAL, TENN, FLEECE

        genoclass.sedesp = ["re", "re"]

        for i in range(2):
            if randint(1, 50) == 1:
                genoclass.dilutemd[i] = "Dm"

        genoclass.body_value = randint(genoclass.body_indexes[1]+1, genoclass.body_indexes[2])
        
        genoclass.breeds["Devon Rex"] = 100
        return genoclass
    
    @staticmethod
    def Donskoy(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        #ruhr + ruhrmod + lykoi

        a = randint(1, 4)

        if random() < 0.5:
            genoclass.ruhr = ["Hrbd", "Hrbd"]
        elif random() < 0.75:
            genoclass.ruhr = ["Hrbd", "hrbd"]

        # pinkdilute + dilutemd

        a = randint(1, 2500)

        if a == 1:
            genoclass.pinkdilute = ["dp", "dp"]
        elif a <= 51:
            genoclass.pinkdilute[1] = "dp"

        genoclass.body_value = randint(genoclass.body_indexes[3]+1, genoclass.body_indexes[4])
        
        genoclass.breeds["Donskoy"] = 100
        return genoclass
    
    @staticmethod
    def Egyptian(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # EUMELANIN

        for i in range(2):
            genoclass.eumelanin[i] = "B"

        # RED GENE

        for i in range(len(genoclass.sexgene)):
            if genoclass.sexgene[i] == 'O':
                genoclass.sexgene[i] = 'o'
        
        # DILUTE

        genoclass.dilute = ["D", "D"]

        # WHITE

        for i in range(2):

            genoclass.white[i] = "w"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "C"

        # SILVER

        if random() < 0.25:
            genoclass.silver = ["I", "I"]
        elif random() < 0.25:
            genoclass.silver = ["I", "i"]
        else:
            genoclass.silver = ["i", "i"]

        # MACKEREL

        genoclass.mack = ["Mc", "Mc"]
        genoclass.ticked = ["ta", "ta"]

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]

        genoclass.spotted = ''
        genoclass.tickgenes = ''
        genoclass.bengal = ''
        genoclass.sokoke = ''
        
        while genoclass.wbsum > 11 or genoclass.wbsum < 6:
            genoclass.wideband = ""
            genoclass.wbsum = 0
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])

        while genoclass.rufsum < 3 or genoclass.rufsum > 5:
            genoclass.rufousing = ""
            genoclass.rufsum = 0
            for i in range(0, 4):
                genoclass.rufousing += choice(genes)
                genoclass.rufsum += int(genoclass.rufousing[i])

        for i in range(0, 4):
            genoclass.spotted += '2'
            genoclass.spotsum += int(genoclass.spotted[i])

        for i in range(0, 4):
            genoclass.tickgenes += '0'
            genoclass.ticksum += int(genoclass.tickgenes[i])

        for i in range(0, 4):
            genoclass.bengal += '0'
            genoclass.bengsum += int(genoclass.bengal[i])

        for i in range(0, 4):
            genoclass.sokoke += '0'
            genoclass.soksum += int(genoclass.sokoke[i])
        
        genoclass.breeds[choice(["Egyptian Mau", "Savannah"])] = 100

        if genoclass.breeds.get('Savannah', False):
            genoclass.height_value = randint(genoclass.height_indexes[4]+1, genoclass.height_indexes[9])

        return genoclass
    
    @staticmethod
    def European(genoclass, special):
        # FUR LENGTH

        genoclass = Breed_generator.AllColours(genoclass, special)
        
        genoclass.furLength = ["L", "L"]

        # EUMELANIN

        for i in range(2):
            genoclass.eumelanin[i] = "B"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "C"
        
        genoclass.breeds["European Shorthair"] = 100
        return genoclass
    
    @staticmethod
    def GermanLH(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH

        genoclass.furLength = ["l", "l"]
        
        if random() < 0.95:
            genoclass.karp = ["K", "K"]
        elif random() < 0.80:
            genoclass.karp = ["K", 'k']
        
        genoclass.breeds["German Longhair"] = 100
        return genoclass
    
    @staticmethod
    def Havana(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # EUMELANIN

        for i in range(2):
            genoclass.eumelanin[i] = "b"

        # RED GENE

        for i in range(len(genoclass.sexgene)):
            if genoclass.sexgene[i] == 'O':
                genoclass.sexgene[i] = 'o'
        
        # DILUTE

        if random() < 0.80:
            genoclass.dilute = ["D", "D"]
        elif random() < 0.25:
            genoclass.dilute = ["d", "d"]
        else:
            genoclass.dilute = ["D", "d"]

        # WHITE

        for i in range(2):

            genoclass.white[i] = "w"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "C"

        # SILVER

        genoclass.silver = ["i", "i"]

        # AGOUTI

        for i in range(2):
            genoclass.agouti[i] = "a"

        genoclass.tickgenes = ''
        genoclass.bengal = ''
        genoclass.sokoke = ''

        for i in range(0, 4):
            genoclass.tickgenes += '0'
            genoclass.ticksum += int(genoclass.tickgenes[i])

        for i in range(0, 4):
            genoclass.bengal += '0'
            genoclass.bengsum += int(genoclass.bengal[i])

        for i in range(0, 4):
            genoclass.sokoke += '0'
            genoclass.soksum += int(genoclass.sokoke[i])

        genoclass.body_value = randint(genoclass.body_indexes[3]+1, genoclass.body_indexes[4])
        
        genoclass.breeds["Havana"] = 100
        return genoclass
    
    @staticmethod
    def Highlander(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        # curl + fold

        genoclass.curl = ["Cu", "Cu"]
        #  manx + kab + toybob + jbob + kub + ring

        genoclass.manx = ["Ab", "ab"]
        
        # munch + poly + altai

        if random() < 0.25:
            genoclass.poly = ["Pd", "Pd"]
        elif random() < 0.25:
            genoclass.poly[0] = "Pd"

        genoclass.height_value = randint(genoclass.height_indexes[3]+1, genoclass.height_indexes[5])
        
        genoclass.breeds["Highlander"] = 100
        return genoclass
    
    @staticmethod
    def JapBob(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        # ALBINO

        for i in range(2):
            c = randint(1, 20)
            d = randint(1, 5)

            if c == 1:
                genoclass.pointgene[i] = "cb"
            elif d == 1:
                genoclass.pointgene[i] = "cs"
            else:
                genoclass.pointgene[i] = "C"

        #  manx + kab + toybob + jbob + kub + ring

        genoclass.jbob = ["jb", "jb"]
        
        genoclass.breeds["Japanese Bobtail"] = 100
        return genoclass
    
    @staticmethod
    def Kanaani(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # RED GENE

        for i in range(len(genoclass.sexgene)):
            if genoclass.sexgene[i] == 'O':
                genoclass.sexgene[i] = 'o'
        
        # DILUTE

        genoclass.dilute = ["D", "D"]

        # WHITE

        for i in range(2):

            genoclass.white[i] = "w"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "C"

        # SILVER

        genoclass.silver = ["i", "i"]

        # AGOUTI

        for i in range(2):
            genoclass.agouti[i] = "A"

        genoclass.ticked = ["ta", "ta"]

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]
        
        genoclass.spotted = ''
        genoclass.spotsum = 0
        
        while genoclass.wbsum > 11 or genoclass.wideband == "":  
            genoclass.wideband = ''
            genoclass.wbsum = 0    
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])

        for i in range(0, 4):
            genoclass.spotted += '2'
            genoclass.spotsum += int(genoclass.spotted[i])

        genoclass.body_value = randint(genoclass.body_indexes[3]+1, genoclass.body_indexes[4])
        
        genoclass.breeds["Kanaani"] = 100
        return genoclass
    
    @staticmethod
    def Karel(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        # EUMELANIN

        for i in range(2):
            genoclass.eumelanin[i] = "B"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "C"

        genoclass.kab = ["kab", 'kab']
        
        genoclass.breeds["Karelian Bobtail"] = 100
        return genoclass
    
    @staticmethod
    def Khao(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # EUMELANIN

        for i in range(2):
            if randint(1, 5) == 1:
                genoclass.eumelanin[i] = "b"
            else:
                genoclass.eumelanin[i] = "B"

        # WHITE

        for i in range(2):

            genoclass.white[i] = "W"

        # SILVER

        genoclass.silver = ["i", "i"]

        genoclass.tickgenes = ''
        genoclass.bengal = ''
        genoclass.sokoke = ''

        for i in range(0, 4):
            genoclass.tickgenes += '0'

        for i in range(0, 4):
            genoclass.bengal += '0'

        for i in range(0, 4):
            genoclass.sokoke += '0'
        
        genoclass.body_value = randint(genoclass.body_indexes[3]+1, genoclass.body_indexes[4])
        
        genoclass.breeds["Khao Manee"] = 100
        return genoclass
    
    @staticmethod
    def Kuril(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        # EUMELANIN

        for i in range(2):
            genoclass.eumelanin[i] = "B"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "C"

        # ext

        for i in range(2):
            if randint(1, 15) == 1:
                genoclass.ext[i] = "ec"

        #  manx + kab + toybob + jbob + kub + ring

        genoclass.kub = ["Kub", "Kub"]
        
        genoclass.breeds["Kurilian Bobtail"] = 100
        return genoclass
    
    @staticmethod
    def LaPerm(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        genoclass.laperm = ["Lp", "Lp"]
        
        for i in range(2):
            if randint(1, 50) == 1:
                genoclass.dilutemd[i] = "Dm"

        # karp + bleach + ghosting + satin + glitter

        if random() < 0.1:
            genoclass.karp = ["K", "K"]
        elif random() < 0.1:
            genoclass.karp[0] = "K"

        if random() < 0.01:
            genoclass.bleach = ["lb", "lb"]
        elif random() < 0.1:
            genoclass.bleach[1] = "lb"

        genoclass.breeds["LaPerm"] = 100
        return genoclass
    
    @staticmethod
    def Lin(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        # FUR LENGTH
        
        genoclass.furLength = ["l", "l"]

        # EUMELANIN

        for i in range(2):
            genoclass.eumelanin[i] = "B"

        # RED GENE

        for i in range(len(genoclass.sexgene)):
            if genoclass.sexgene[i] == 'O':
                genoclass.sexgene[i] = 'o'
        
        # DILUTE

        genoclass.dilute = ["D", "D"]

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "C"

        # SILVER

        genoclass.silver = ["i", "i"]

        # AGOUTI

        for i in range(2):
            genoclass.agouti[i] = "a"

        genoclass.tickgenes = ''
        genoclass.bengal = ''
        genoclass.sokoke = ''

        for i in range(0, 4):
            genoclass.tickgenes += '0'
            genoclass.ticksum += int(genoclass.tickgenes[i])

        for i in range(0, 4):
            genoclass.bengal += '0'
            genoclass.bengsum += int(genoclass.bengal[i])

        for i in range(0, 4):
            genoclass.sokoke += '0'
            genoclass.soksum += int(genoclass.sokoke[i])
        
        genoclass.breeds["Lin-Qing Lion cat"] = 100
        return genoclass
    
    @staticmethod
    def Lykoi(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        # RED GENE
        if genoclass.odds['XXX/XXY'] > 0 and randint(1, genoclass.odds['XXX/XXY']) == 1:
            genoclass.sexgene = ["", "", ""]
        else:
            genoclass.sexgene = ["", ""]
        
        for i in range(len(genoclass.sexgene)):
            if randint(1, 10) == 1:
                genoclass.sexgene[i] = "O"
            else:
                genoclass.sexgene[i] = "o"

        if (random() < 0.5 and special != "fem") or special == "masc":
            genoclass.sexgene[-1] = "Y"
            genoclass.sex = "tom"
        else:
            genoclass.sex = "molly"
        
        # AGOUTI

        for i in range(2):
            if randint(1, 5) == 1:
                genoclass.agouti[i] = "A"
            else:
                genoclass.agouti[i] = "a"

        genoclass.lykoi = ["ly", "ly"]
        
        genoclass.breeds["Lykoi"] = 100
        return genoclass
    
    @staticmethod
    def Mandalay(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        
        a = randint(1, 10)

        if a < 7:
            genoclass.furLength = ["L", "L"]
        elif a == 10:
            genoclass.furLength = ["l", "l"]
        else:
            genoclass.furLength = ["L", "l"]

        genoclass.white = ['w', 'w']

        # ALBINO

        for i in range(2):

            if random() < 0.25:
                genoclass.pointgene[i] = "cb"
            else:
                genoclass.pointgene[i] = "C"
        
        if random() < 0.5:
            genoclass.pointgene = ["cb", "cb"]

        # MACKEREL

        genoclass.mack = ["Mc", "Mc"]

        # TICKED

        genoclass.ticked = ["Ta", "Ta"]

        for i in range(2):
            if randint(1, 50) == 1:
                genoclass.dilutemd[i] = "Dm"

        # ext

        for i in range(2):
            if random() < 0.15:
                genoclass.ext[i] = "er"

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]
        genoclass.tickgenes = ''
        genoclass.ticksum = 0

        for i in range(0, 4):
            genoclass.tickgenes += choice(genes)
            genoclass.ticksum += int(genoclass.tickgenes[i])
        
        genoclass.breeds["Mandalay/Burmese"] = 100
        return genoclass
    
    @staticmethod
    def Maine(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["l", "l"]

        # EUMELANIN

        for i in range(2):
            if randint(1, 20) == 1:
                genoclass.eumelanin[i] = "bl"
            elif randint(1, 15) == 1:
                genoclass.eumelanin[i] = "b"
            else:
                genoclass.eumelanin[i] = "B"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "C"

        if random() < 0.0625:
            genoclass.poly = ["Pd", "Pd"]
        elif random() < 0.0625:
            genoclass.poly[0] = "Pd"

        genoclass.height_value = randint(genoclass.height_indexes[3]+1, genoclass.height_indexes[9])
        
        genoclass.breeds["Maine Coon"] = 100
        genoclass.longtype = 'long'
        return genoclass
    
    @staticmethod
    def Manx(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        if random() < 0.125:
            genoclass.cornish = ["r", "r"]
            
        for i in range(2):
            if randint(1, 50) == 1:
                genoclass.dilutemd[i] = "Dm"


        #  manx + kab + toybob + jbob + kub + ring

        genoclass.manx = ["M", "m"]

        genoclass.body_value = randint(genoclass.body_indexes[1]+1, genoclass.body_indexes[3])
        
        genoclass.breeds["Manx"] = 100
        return genoclass
    
    @staticmethod
    def Mekong(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # WHITE

        for i in range(2):

            genoclass.white[i] = "w"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "cs"

        #  manx + kab + toybob + jbob + kub + ring

        genoclass.jbob = ["jb", "jb"]
        
        genoclass.breeds["Mekong Bobtail"] = 100
        return genoclass
    
    @staticmethod
    def Munchkin(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        if random() < 0.05:
            genoclass.karp = ["K", "K"]
        elif random() < 0.05:
            genoclass.karp[0] = "K"

        # munch + poly + altai

        genoclass.munch[0] = "Mk"
        
        genoclass.breeds["Munchkin"] = 100
        return genoclass
    
    @staticmethod
    def NewZeal(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        # EUMELANIN

        for i in range(2):
            genoclass.eumelanin[i] = "B"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "C"
        
        genoclass.breeds["New Zealand"] = 100
        return genoclass
    
    @staticmethod
    def NFC(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["l", "l"]
        genoclass.longtype = "long"


        # EUMELANIN

        for i in range(2):
            if randint(1, 20) == 1:
                genoclass.eumelanin[i] = "bl"
            elif randint(1, 15) == 1:
                genoclass.eumelanin[i] = "b"
            else:
                genoclass.eumelanin[i] = "B"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "C"

        # ext

        for i in range(2):
            if random() < 0.125:
                genoclass.ext[i] = "ea"

        genoclass.height_value = randint(genoclass.height_indexes[3]+1, genoclass.height_indexes[6])
        
        genoclass.breeds["Norwegian Forest cat"] = 100
        return genoclass
    
    @staticmethod
    def Ocicat(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]


        # RED GENE

        for i in range(len(genoclass.sexgene)):
            if genoclass.sexgene[i] == 'O':
                genoclass.sexgene[i] = 'o'
        
        # WHITE

        for i in range(2):

            genoclass.white[i] = "w"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "C"

        # AGOUTI

        for i in range(2):
            b = randint(1, 4)
            if b == 1:
                genoclass.agouti[i] = "a"
            else:
                genoclass.agouti[i] = "A"

        genoclass.ticked = ["ta", "ta"]

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]

        genoclass.spotted = ''
        genoclass.spotsum = 0
        
        while genoclass.wbsum > 11 or genoclass.wideband == "":
            genoclass.wideband = ""
            genoclass.wbsum = 0
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])

        for i in range(0, 4):
            genoclass.spotted += '2'
            genoclass.spotsum += int(genoclass.spotted[i])
        
        genoclass.breeds["Ocicat"] = 100
        return genoclass
    
    @staticmethod
    def Oriental(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)
        genoclass.longtype = "medium"

        # ALBINO

        for i in range(2):
            if random() < 0.125:
                genoclass.pointgene[i] = "cs"
            else:
                genoclass.pointgene[i] = "C"
        
        if random() < 0.5:
            genoclass.pointgene = ["cs", "cs"]

        # pinkdilute + dilutemd

        a = randint(1, 2500)

        if a == 1:
            genoclass.dilutemd = ["Dm", "Dm"]
        elif a <= 51:
            genoclass.dilutemd[0] = "Dm"

        genoclass.body_value = randint(genoclass.body_indexes[4]+1, genoclass.body_indexes[6])
        
        genoclass.breeds["Oriental/Siamese"] = 100
        return genoclass
    
    @staticmethod
    def Persian(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH

        genoclass.longtype = "long"
        
        if random() < 0.33:
            genoclass.furLength = ["L", "L"]
        else:
            genoclass.furLength = ["l", "l"]


        # EUMELANIN

        for i in range(2):
            if randint(1, 25) == 1:
                genoclass.eumelanin[i] = "bl"
            elif randint(1, 5) == 1:
                genoclass.eumelanin[i] = "b"
            else:
                genoclass.eumelanin[i] = "B"

        # ALBINO

        for i in range(2):
            c = randint(1, 10)
            d = randint(1, 5)

            if d == 1:
                genoclass.pointgene[i] = "cs"
            else:
                genoclass.pointgene[i] = "C"
        
        if random() < 0.33:
            genoclass.pointgene = ["cs", "cs"]
            
        if genoclass.pointgene == ["cs", "cs"]:
            if random() < 0.0625:
                genoclass.poly = ["Pd", "Pd"]
            elif random() < 0.0625:
                genoclass.poly[0] = "Pd"

        # TICKED

        genoclass.ticked = ["ta", "ta"]

        # pinkdilute + dilutemd

        a = randint(1, 2500)

        if a == 1:
            genoclass.dilutemd = ["Dm", "Dm"]
        elif a <= 51:
            genoclass.dilutemd[0] = "Dm"

        genoclass.body_value = randint(genoclass.body_indexes[0], genoclass.body_indexes[1])
        
        genoclass.breeds["Persian/Exotic"] = 100
        return genoclass
    
    @staticmethod
    def Pixiebob(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        
        # EUMELANIN

        for i in range(2):
            genoclass.eumelanin[i] = "B"

        # RED GENE

        for i in range(len(genoclass.sexgene)):
            if genoclass.sexgene[i] == 'O':
                genoclass.sexgene[i] = 'o'
        
        # DILUTE

        genoclass.dilute = ["D", "D"]

        # WHITE

        for i in range(2):

            genoclass.white[i] = "w"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "C"

        # SILVER

        genoclass.silver = ["i", "i"]

        # AGOUTI

        for i in range(2):
            genoclass.agouti[i] = "A"

        # MACKEREL

        genoclass.mack = ["Mc", "Mc"]

        genoclass.ticked = ["ta", "ta"]

        #  manx + kab + toybob + jbob + kub + ring

        genoclass.manx = ["Ab", "ab"]
        
        if random() < 0.125:
            genoclass.poly = ["Pd", "Pd"]
        elif random() < 0.25:
            genoclass.poly[0] = "Pd"

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]

        genoclass.spotted = ''
        genoclass.tickgenes = ''
        genoclass.bengal = ''
        genoclass.sokoke = ''
        
        while genoclass.wbsum < 6 or genoclass.wbsum > 9:
            genoclass.wideband = ''
            genoclass.wbsum = 0
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])

        while genoclass.rufsum < 3 or genoclass.rufsum > 5:
            genoclass.rufousing = ''
            genoclass.rufsum = 0
            for i in range(0, 4):
                genoclass.rufousing += choice(genes)
                genoclass.rufsum += int(genoclass.rufousing[i])

        for i in range(0, 4):
            genoclass.spotted += '2'

        for i in range(0, 4):
            genoclass.tickgenes += '0'


        for i in range(0, 4):
            genoclass.bengal += '0'

        for i in range(0, 4):
            genoclass.sokoke += '0'
        
        genoclass.breeds["Pixie-Bob"] = 100
        return genoclass
    
    @staticmethod
    def Ragamuffin(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["l", "l"]
        genoclass.longtype = "long"


        genoclass.body_value = randint(genoclass.body_indexes[1]+1, genoclass.body_indexes[2])
        
        genoclass.breeds["Ragamuffin"] = 100
        return genoclass
    
    @staticmethod
    def Ragdoll(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["l", "l"]
        genoclass.longtype = "long"


        # EUMELANIN

        for i in range(2):
            if randint(1, 20) == 1:
                genoclass.eumelanin[i] = "bl"
            elif randint(1, 5) == 1:
                genoclass.eumelanin[i] = "b"
            else:
                genoclass.eumelanin[i] = "B"

        # WHITE

        for i in range(2):

            if randint(1, 2) == 1:
                genoclass.white[i] = "ws"
            else:
                genoclass.white[i] = "w"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "cs"

        # pinkdilute + dilutemd

        a = randint(1, 2500)

        if a == 1:
            genoclass.dilutemd = ["Dm", "Dm"]
        elif a <= 51:
            genoclass.dilutemd[0] = "Dm"

        genoclass.body_value = randint(genoclass.body_indexes[1]+1, genoclass.body_indexes[2])
        
        genoclass.breeds["Ragdoll"] = 100
        return genoclass
    
    @staticmethod
    def Russian(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        if random() < 0.75:
            genoclass.furLength = ["L", "L"]
        else:
            genoclass.furLength = ["l", "l"]

        # EUMELANIN

        for i in range(2):
            genoclass.eumelanin[i] = "B"

        # RED GENE

        for i in range(len(genoclass.sexgene)):
            if genoclass.sexgene[i] == 'O':
                genoclass.sexgene[i] = 'o'
        
        # DILUTE

        if random() < 0.25 and genoclass.furLength[0] == "L":
            genoclass.dilute = ["D", "D"]
        else:
            genoclass.dilute = ["d", "d"]
            genoclass.saturation = randint(0, 2)

        # WHITE

        for i in range(2):

            if random() < 0.25 and genoclass.furLength[0] == "L":
                genoclass.white[i] = "W"
            else:
                genoclass.white[i] = "w"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "C"

        # SILVER

        genoclass.silver = ["i", "i"]

        # AGOUTI

        for i in range(2):
            genoclass.agouti[i] = "a"

        # karp + bleach + ghosting + satin + glitter

        genoclass.satin = ["st", "st"]

        genoclass.tickgenes = ''
        genoclass.bengal = ''
        genoclass.sokoke = ''

        for i in range(0, 4):
            genoclass.tickgenes += '0'

        for i in range(0, 4):
            genoclass.bengal += '0'

        for i in range(0, 4):
            genoclass.sokoke += '0'

        genoclass.body_value = randint(genoclass.body_indexes[2]+1, genoclass.body_indexes[4])
        
        genoclass.breeds["Russian"] = 100
        return genoclass
    
    @staticmethod
    def Selkirk(genoclass, special):
        
        genoclass = Breed_generator.AllColours(genoclass, special)

        #SELKIRK/DEVON/HAIRLESS
    
        for i in range(2):
            if random() > 0.25:
                genoclass.sedesp[i] = "Se"

        # pinkdilute + dilutemd

        a = randint(1, 2500)

        if a == 1:
            genoclass.dilutemd = ["Dm", "Dm"]
        elif a <= 51:
            genoclass.dilutemd[0] = "Dm"

        #sunshine

        for i in range(2):
            if randint(1, 40) == 1:
                genoclass.corin[i] = "fg" #Flaxen Gold
            else:
                genoclass.corin[i] = "N" #No

        genoclass.body_value = randint(genoclass.body_indexes[0]+1, genoclass.body_indexes[1])
        
        genoclass.breeds["Selkirk Rex"] = 100
        return genoclass
    
    @staticmethod
    def Siberian(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["l", "l"]
        genoclass.longtype = "long"


        # EUMELANIN

        for i in range(2):
            if randint(1, 20) == 1:
                genoclass.eumelanin[i] = "bl"
            elif randint(1, 15) == 1:
                genoclass.eumelanin[i] = "b"
            else:
                genoclass.eumelanin[i] = "B"

        # ALBINO

        for i in range(2):
            if randint(1, 3) == 1:
                genoclass.pointgene[i] = "cs"
            else:
                genoclass.pointgene[i] = "C"

        #sunshine

        for i in range(2):
            if random() < 0.125:
                genoclass.corin[i] = "sh" #sunSHine
            elif random() < 0.0625:
                genoclass.corin[i] = "sg" #Siberian Gold / extreme sunshine

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]
        
        while genoclass.wbsum > 11 or genoclass.wideband == "":
            genoclass.wideband = ''
            genoclass.wbsum = 0
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])

        genoclass.height_value = randint(genoclass.height_indexes[4]+1, genoclass.height_indexes[6])
        
        genoclass.breeds["Siberian"] = 100
        return genoclass
    
    @staticmethod
    def Singapura(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # EUMELANIN

        for i in range(2):
            genoclass.eumelanin[i] = "B"

        # RED GENE

        for i in range(len(genoclass.sexgene)):
            if genoclass.sexgene[i] == 'O':
                genoclass.sexgene[i] = 'o'
        
        # DILUTE

        genoclass.dilute = ["D", "D"]

        # WHITE

        for i in range(2):

            genoclass.white[i] = "w"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "cb"

        # SILVER

        genoclass.silver = ["i", "i"]

        # AGOUTI

        for i in range(2):
            genoclass.agouti[i] = "A"

        # TICKED

        genoclass.ticked = ["Ta", "Ta"]

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]

        genoclass.tickgenes = ''
        genoclass.bengal = ''
        genoclass.sokoke = ''
        
        while genoclass.wbsum > 11 or genoclass.wbsum < 6:
            genoclass.wideband = ""
            genoclass.wbsum = 0
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])

        for i in range(0, 4):
            genoclass.tickgenes += '2'

        for i in range(0, 4):
            genoclass.bengal += '0'

        for i in range(0, 4):
            genoclass.sokoke += '0'

        genoclass.body_value = randint(genoclass.body_indexes[3]+1, genoclass.body_indexes[4])
        
        genoclass.breeds["Singapura"] = 100
        return genoclass
    
    @staticmethod
    def Snowshoe(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # WHITE

        genoclass.white = ["ws", "w"]
        genoclass.whitegrade = randint(3, 5)

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "cs"

        # pinkdilute + dilutemd

        a = randint(1, 2500)

        if a == 1:
            genoclass.dilutemd = ["Dm", "Dm"]
        elif a <= 51:
            genoclass.dilutemd[0] = "Dm"
        
        genoclass.breeds["Snowshoe"] = 100
        return genoclass
    
    @staticmethod
    def Sokoke(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # EUMELANIN

        for i in range(2):
            genoclass.eumelanin[i] = "B"

        # RED GENE

        for i in range(len(genoclass.sexgene)):
            if genoclass.sexgene[i] == 'O':
                genoclass.sexgene[i] = 'o'
        
        # DILUTE

        genoclass.dilute = ["D", "D"]

        # WHITE

        for i in range(2):

            genoclass.white[i] = "w"

        # ALBINO

        for i in range(2):
            if randint(1, 5) == 1:
                genoclass.pointgene[i] = "cs"
            else:
                genoclass.pointgene[i] = "C"

        # SILVER

        genoclass.silver = ["i", "i"]

        # AGOUTI

        for i in range(2):
            genoclass.agouti[i] = "A"

        # MACKEREL

        genoclass.mack = ["mc", "mc"]

        genoclass.ticked = ["ta", "ta"]

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]

        genoclass.tickgenes = ''
        genoclass.bengal = ''
        genoclass.sokoke = ''

        while genoclass.wbsum > 11 or genoclass.wbsum < 6:
            genoclass.wideband = ""
            genoclass.wbsum = 0
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])

        while genoclass.rufsum < 3 or genoclass.rufsum > 5:
            genoclass.rufousing = ""
            genoclass.rufsum = 0
            for i in range(0, 4):
                genoclass.rufousing += choice(genes)
                genoclass.rufsum += int(genoclass.rufousing[i])

        for i in range(0, 4):
            genoclass.tickgenes += '0'

        for i in range(0, 4):
            genoclass.bengal += '0'

        for i in range(0, 4):
            genoclass.sokoke += '2'
            
        genoclass.body_value = randint(genoclass.body_indexes[3]+1, genoclass.body_indexes[4])
        
        genoclass.breeds["Sokoke"] = 100
        return genoclass
    
    @staticmethod
    def Sphynx(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        #SELKIRK/DEVON/HAIRLESS
    
        for i in range(2):
            genoclass.sedesp[i] = "hr"

        # curl

        if random() < 0.125:
            genoclass.curl = ["Cu", "Cu"]
        elif random() < 0.25:
            genoclass.curl[0] = "Cu"
            
        genoclass.body_value = randint(genoclass.body_indexes[3]+1, genoclass.body_indexes[4])
        
        genoclass.breeds["Sphynx"] = 100
        return genoclass
    
    @staticmethod
    def Tenn(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)

        # YORK, WIREHAIR, LAPERM, CORNISH, URAL, TENN, FLEECE

        genoclass.tenn = ["tr", "tr"]
            
        genoclass.body_value = randint(genoclass.body_indexes[1]+1, genoclass.body_indexes[3])
            
        genoclass.breeds["Tennessee Rex"] = 100
        return genoclass
    
    @staticmethod
    def Thai(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # EUMELANIN

        for i in range(2):
            if randint(1, 20) == 1:
                genoclass.eumelanin[i] = "bl"
            elif randint(1, 5) == 1:
                genoclass.eumelanin[i] = "b"
            else:
                genoclass.eumelanin[i] = "B"

        # WHITE

        for i in range(2):

            genoclass.white[i] = "w"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "cs"

        # AGOUTI

        for i in range(2):
            if randint(1, 3) == 1:
                genoclass.agouti[i] = "A"
            else:
                genoclass.agouti[i] = "a"
        
        genoclass.breeds["Thai"] = 100
        return genoclass
    
    @staticmethod
    def Tonk(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # WHITE
        for i in range(2):
            genoclass.white[i] = "w"

        # ALBINO

        for i in range(2):
            if random() < 0.5:
                genoclass.pointgene[i] = "cb"
            else:
                genoclass.pointgene[i] = "cs"

        # AGOUTI

        for i in range(2):
            b = randint(1, 7)
            if b == 1:
                genoclass.agouti[i] = "A"
            else:
                genoclass.agouti[i] = "a"

        # pinkdilute + dilutemd

        a = randint(1, 2500)

        if a == 1:
            genoclass.dilutemd = ["Dm", "Dm"]
        elif a <= 51:
            genoclass.dilutemd[0] = "Dm"

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]

        genoclass.tickgenes = ''
        
        while genoclass.wbsum > 11 or genoclass.wideband == "":  
            genoclass.wideband = ''
            genoclass.wbsum = 0    
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])
            
        genoclass.body_value = randint(genoclass.body_indexes[1]+1, genoclass.body_indexes[4])
        
        genoclass.breeds["Tonkinese"] = 100
        return genoclass
    
    @staticmethod
    def Toybob(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        #  manx + kab + toybob + jbob + kub + ring

        genoclass.toybob = ["Tb", "Tb"]

        genoclass.height_value = randint(genoclass.height_indexes[0], genoclass.height_indexes[1])
        
        genoclass.breeds["Toybob"] = 100
        return genoclass
    
    @staticmethod
    def Toyger(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # EUMELANIN

        for i in range(2):
            genoclass.eumelanin[i] = "B"

        # RED GENE

        for i in range(len(genoclass.sexgene)):
            if genoclass.sexgene[i] == 'O':
                genoclass.sexgene[i] = 'o'
        
        # DILUTE

        genoclass.dilute = ["D", "D"]

        # WHITE

        for i in range(2):

            genoclass.white[i] = "w"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "C"

        # SILVER

        genoclass.silver = ["i", "i"]

        # AGOUTI

        for i in range(2):
            genoclass.agouti[i] = "A"

        # MACKEREL

        genoclass.mack = ["Mc", "Mc"]

        genoclass.ticked = ["ta", "ta"]

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]

        genoclass.rufousing = ''
        genoclass.spotted = ''
        genoclass.tickgenes = ''
        genoclass.bengal = ''
        genoclass.sokoke = ''
        
        while genoclass.wbsum > 11 or genoclass.wbsum < 6:
            genoclass.wideband = ""
            genoclass.wbsum = 0
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])

        for i in range(0, 4):
            genoclass.rufousing += '2'

        genesspot = ["1", "1", "1", "1", "1", "0", "0", "0", "0", "0", "0", "0", "0"]

        for i in range(0, 4):
            genoclass.spotted += choice(genesspot)

        for i in range(0, 4):
            genoclass.tickgenes += '0'

        for i in range(0, 4):
            genoclass.bengal += '2'

        for i in range(0, 4):
            genoclass.sokoke += '0'
        
        genoclass.breeds["Toyger"] = 100
        return genoclass
    
    @staticmethod
    def Turkish(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        if random() < 0.125:
            genoclass.furLength = ["L", "L"]
        else:
            genoclass.furLength = ["l", "l"]

        # EUMELANIN

        genoclass.eumelanin = ["B", "B"]
        
        if random() < 0.5:
            genoclass.white = ["ws", "ws"]
            genoclass.whitegrade = 4

        # ALBINO

        genoclass.pointgene = ["C", "C"]
            
        genoclass.body_value = randint(genoclass.body_indexes[3]+1, genoclass.body_indexes[4])
        
        genoclass.breeds["Turkish"] = 100
        return genoclass
    
    @staticmethod
    def Ural(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        # EUMELANIN

        for i in range(2):
            genoclass.eumelanin[i] = "B"

        # ALBINO

        for i in range(2):
            if randint(1, 5) == 1:
                genoclass.pointgene[i] = "cs"
            else:
                genoclass.pointgene[i] = "C"

        genoclass.ticked = ["ta", "ta"]

        # YORK, WIREHAIR, LAPERM, CORNISH, URAL, TENN, FLEECE

        genoclass.urals = ["ru", "ru"]
            
        genoclass.body_value = randint(genoclass.body_indexes[1]+1, genoclass.body_indexes[2])
        
        genoclass.breeds["Ural Rex"] = 100
        return genoclass
    
    @staticmethod
    def Bambino(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]


        #SELKIRK/DEVON/HAIRLESS
    
        for i in range(2):
            genoclass.sedesp[i] = "hr"


        # munch + poly + altai

        genoclass.munch[0] = "Mk"
            
        genoclass.body_value = randint(genoclass.body_indexes[3]+1, genoclass.body_indexes[4])
        
        genoclass.breeds["Sphynx"] = 75
        genoclass.breeds["Munchkin"] = 25
        return genoclass
    
    @staticmethod
    def Cheetoh(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # EUMELANIN

        for i in range(2):
            if randint(1, 10) == 1:
                genoclass.eumelanin[i] = "bl"
            elif randint(1, 5) == 1:
                genoclass.eumelanin[i] = "b"
            else:
                genoclass.eumelanin[i] = "B"

        # RED GENE

        for i in range(len(genoclass.sexgene)):
            if genoclass.sexgene[i] == 'O':
                genoclass.sexgene[i] = 'o'
        
        # DILUTE

        if random() < 0.33 or genoclass.eumelanin[0] != "B":
            genoclass.dilute = ["D", "D"]
        elif random() < 0.33:
            genoclass.dilute = ["d", "d"]
        else:
            genoclass.dilute = ["D", "d"]

        # WHITE

        for i in range(2):

            genoclass.white[i] = "w"

        # ALBINO

        for i in range(2):
            if random() < 0.2 and genoclass.eumelanin[0] == "B" and genoclass.dilute[0] == "D":
                genoclass.pointgene[i] = "cs"
            else:
                genoclass.pointgene[i] = "C"

        # SILVER

        if random() < 0.125 or genoclass.eumelanin[0] != "B" or genoclass.dilute[0] == "d":
            genoclass.silver = ["I", "I"]
        elif random() < 0.33:
            genoclass.silver = ["I", "i"]
        else:
            genoclass.silver = ["i", "i"]

        # AGOUTI

        for i in range(2):
            if randint(1, 3) == 1 and genoclass.eumelanin[0] != "bl" and genoclass.dilute[0] == "D" and genoclass.silver[0] == "I" and genoclass.pointgene[0] == "C":
                genoclass.agouti[i] = "a"
            else:
                genoclass.agouti[i] = "A"

        # MACKEREL

        if random() < 0.25 and genoclass.eumelanin[0] == "B" and genoclass.dilute[0] == "D" and genoclass.silver[0] == 'i':
            genoclass.mack = ["mc", "mc"]
        else:
            genoclass.mack = ["Mc", "Mc"]

        genoclass.ticked = ["ta", "ta"]

        # karp + bleach + ghosting + satin + glitter

        if random() < 0.125:
            genoclass.glitter = ["gl", "gl"]
        elif random() < 0.25:
            genoclass.glitter[1] = "gl"


        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]

        genoclass.spotted = ''
        genoclass.tickgenes = ''
        genoclass.bengal = ''
        genoclass.sokoke = ''
        
        while genoclass.wbsum > 11 or genoclass.wideband == "":
            genoclass.wideband = ""
            genoclass.wbsum = 0
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])

        for i in range(0, 4):
            genoclass.spotted += '2'
        
        genesmild = ["2", "2", "1", "1", "1", "1", "1", "0", "0", "0", "0", "0", "0", "0", "0"]

        for i in range(0, 4):
            genoclass.tickgenes += '0'

        for i in range(0, 4):
            genoclass.bengal += choice(genesmild)

        for i in range(0, 4):
            genoclass.sokoke += '0'
        
        genoclass.breeds["Ocicat"] = 75
        genoclass.breeds["Bengal"] = 25
        return genoclass
    
    @staticmethod
    def Foldex(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        
        # EUMELANIN

        for i in range(2):
            if randint(1, 5) == 1:
                genoclass.eumelanin[i] = "b"
            else:
                genoclass.eumelanin[i] = "B"

        # ALBINO

        for i in range(2):
            if randint(1, 5) == 1:
                genoclass.pointgene[i] = "cs"
            else:
                genoclass.pointgene[i] = "C"

        # curl + fold

        genoclass.fold[0] = "Fd"

        genoclass.tickgenes = ''
        genoclass.bengal = ''
        genoclass.sokoke = ''

        for i in range(0, 4):
            genoclass.tickgenes += '0'

        for i in range(0, 4):
            genoclass.bengal += '0'

        for i in range(0, 4):
            genoclass.sokoke += '0'
            
        genoclass.body_value = randint(genoclass.body_indexes[0], genoclass.body_indexes[1])
        
        genoclass.breeds["Persian/Exotic"] = 50
        genoclass.breeds["British"] = 50
        return genoclass
    
    @staticmethod
    def Gaelic(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        # curl + fold

        genoclass.fold[0] = "Fd"
        
        # munch + poly + altai

        genoclass.munch[0] = "Mk"
            
        genoclass.body_value = randint(genoclass.body_indexes[0]+1, genoclass.body_indexes[1])
        
        genoclass.breeds["British"] = 50
        genoclass.breeds["Munchkin"] = 25
        genoclass.breeds["Persian/Exotic"] = 25
        return genoclass
    
    @staticmethod
    def Kinkalow(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        # curl + fold

        genoclass.curl = ["Cu", "Cu"]


        # munch + poly + altai

        genoclass.munch[0] = "Mk"
        
        genoclass.breeds["American Curl"] = 50
        genoclass.breeds["Munchkin"] = 50
        return genoclass
    
    @staticmethod
    def Lambkin(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        #SELKIRK/DEVON/HAIRLESS
    
        for i in range(2):
            genoclass.sedesp[i] = "Se"
        
        genoclass.munch[0] = "Mk"
        
        genoclass.breeds["Selkirk Rex"] = 50
        genoclass.breeds["Munchkin"] = 50
        return genoclass
    
    @staticmethod
    def Napoleon(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)
        
        # munch + poly + altai

        genoclass.munch[0] = "Mk"
            
        genoclass.body_value = randint(genoclass.body_indexes[0], genoclass.body_indexes[1])
        
        genoclass.breeds["Persian/Exotic"] = 75
        genoclass.breeds["Munchkin"] = 25
        return genoclass
    
    @staticmethod
    def Peterbald(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]


        #ruhr + ruhrmod + lykoi

        if random() < 0.75:
            genoclass.ruhr = ["Hrbd", "Hrbd"]
        elif random() < 0.75:
            genoclass.ruhr = ["Hrbd", "hrbd"]

        # pinkdilute + dilutemd
        
        a = randint(1, 2500)

        if a == 1:
            genoclass.dilutemd = ["Dm", "Dm"]
        elif a <= 51:
            genoclass.dilutemd[0] = "Dm"
            
        genoclass.body_value = randint(genoclass.body_indexes[4]+1, genoclass.body_indexes[5])
        
        genoclass.breeds["Oriental/Siamese"] = 75
        genoclass.breeds["Donskoy"] = 25
        return genoclass
    
    @staticmethod
    def Serengeti(genoclass, special):
        genoclass = Breed_generator.AllColours(genoclass, special)
        # FUR LENGTH
        
        genoclass.furLength = ["L", "L"]

        # EUMELANIN

        for i in range(2):
            genoclass.eumelanin[i] = "B"

        # RED GENE

        for i in range(len(genoclass.sexgene)):
            if genoclass.sexgene[i] == 'O':
                genoclass.sexgene[i] = 'o'
        
        # DILUTE

        genoclass.dilute = ["D", "D"]

        # WHITE

        for i in range(2):

            genoclass.white[i] = "w"

        # ALBINO

        for i in range(2):
            genoclass.pointgene[i] = "C"

        # SILVER

        if random() < 0.25:
            genoclass.silver = ["I", "I"]
        elif random() < 0.25:
            genoclass.silver = ["I", "i"]
        else:
            genoclass.silver = ["i", "i"]

        # AGOUTI

        for i in range(2):
            if random() < 0.5:
                genoclass.agouti[i] = "A"
            else:
                genoclass.agouti[i] = "a"

        # MACKEREL

        genoclass.mack = ["Mc", "Mc"]
        genoclass.ticked = ["ta", "ta"]

        genes = ["2", "2", "1", "1", "1", "1", "1", "1", "0", "0"]

        genoclass.spotted = ''
        genoclass.tickgenes = ''
        genoclass.bengal = ''
        genoclass.sokoke = ''
        
        while genoclass.wbsum > 11 or genoclass.wbsum < 6:
            genoclass.wideband = ""
            genoclass.wbsum = 0
            for i in range(0, 8):
                genoclass.wideband += choice(genes)
                genoclass.wbsum += int(genoclass.wideband[i])

        while genoclass.rufsum < 3 or genoclass.rufsum > 5:
            genoclass.rufousing = ""
            genoclass.rufsum = 0
            for i in range(0, 4):
                genoclass.rufousing += choice(genes)
                genoclass.rufsum += int(genoclass.rufousing[i])

        for i in range(0, 4):
            genoclass.spotted += '2'

        for i in range(0, 4):
            genoclass.tickgenes += '0'

        for i in range(0, 4):
            genoclass.bengal += '0'

        for i in range(0, 4):
            genoclass.sokoke += '0'
            
        genoclass.body_value = randint(genoclass.body_indexes[4]+1, genoclass.body_indexes[5])
        
        genoclass.breeds["Oriental/Siamese"] = 50
        genoclass.breeds["Bengal"] = 50
        return genoclass
    
    @staticmethod
    def Skookum(genoclass, special):

        genoclass = Breed_generator.AllColours(genoclass, special)

        # YORK, WIREHAIR, LAPERM, CORNISH, URAL, TENN, FLEECE

        genoclass.laperm = ["Lp", "Lp"]
        
        # munch + poly + altai

        genoclass.munch[0] = "Mk"
        
        genoclass.breeds["Munchkin"] = 50
        genoclass.breeds["LaPerm"] = 50
        return genoclass

class Breed_checker:
    @staticmethod
    def Cheetoh(genotype, phenotype):
        if genotype.ext[0] != "E" or genotype.corin[0] != "N" or phenotype.length != "shorthaired" or 'O' in genotype.sexgene:
            return False
        if genotype.white[0] != "w" or genotype.ticked[0] != "ta" or phenotype.furtype != [""] or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.karp[0] != "k" or genotype.bleach[0] != "Lb" or genotype.ghosting[0] != "gh" or genotype.satin[0] == "st":
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        if genotype.dilute[0] == "d" and (genotype.eumelanin[0] != "B" or genotype.dilutemd[0] != "dm"):
            return False
        if genotype.pointgene[0] != "C" and (genotype.eumelanin[0] != "B" or genotype.dilute[0] == "d" or genotype.agouti[0] != "A"):
            return False
        if genotype.silver[0] == "I" and genotype.agouti[0] == "a" and (genotype.eumelanin == "bl" or genotype.dilute[0] == "d"):
            return False
        if genotype.mack[0] == "mc" and (genotype.eumelanin[0] != "B" or genotype.dilute[0] == "d"):
            return False
        if genotype.eumelanin[0] != "B" and genotype.silver[0] != "I":
            return False
        if genotype.wbsum > 11 or genotype.soksum > 3:
            return False
        return True
    @staticmethod
    def Serengeti(genotype, phenotype):
        
        if phenotype.length != "shorthaired" or (phenotype.furtype != [""] and phenotype.furtype != [" shiny", " fur"]):
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        
        if 'O' in genotype.sexgene:
            return False
        if genotype.white[0] != "w" or genotype.ticked[0] != "ta":
            return False
        if genotype.dilute[0] == "d" or genotype.pointgene[0] != "C" or genotype.eumelanin[0] != "B" or genotype.mack[0] == "mc":
            return False
        if genotype.wbsum > 11 or genotype.soksum > 3 or genotype.spotsum < 6:
            return False
        return True

    @staticmethod
    def Aby(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False

        if genotype.white[0] != "w" or genotype.pointgene[0] != "C" or genotype.agouti[0] != "A":
            return False
        if genotype.ticked[0] == "ta" or genotype.ticksum < 6:
            return False
    
        if genotype.furLength[0] == "l":
            return "Somali"
        return "Abyssinian"

    @staticmethod
    def AmBob(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or genotype.manx[0] != "Ab" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False
    
        return "American Bobtail"

    @staticmethod
    def AmCurl(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if genotype.curl[0] != "Cu" or genotype.fold[0] == "Fd" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False
        
        return "American Curl"

    @staticmethod
    def AmSH(genotype, phenotype):
        if phenotype.length == "hairless" or (phenotype.furtype != [""] and phenotype.furtype != ["wiry", " fur"]):
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False

        if genotype.pointgene[0] != "C" or genotype.furLength[0] != "L":
            return False
    
        if genotype.wirehair[0] == "Wh":
            return "American Wirehair"
        return "American Shorthair"

    @staticmethod
    def AmBurm(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False

        if genotype.white[0] != "w" or genotype.agouti[0] != "a" or genotype.eumelanin[0] == "bl":
            return False
        if genotype.silver[0] == "I" or genotype.furLength[0] == "l" or 'O' in genotype.sexgene:
            return False

        if genotype.pointgene != ["cb", "cb"]:
            if genotype.pointgene[0] == "C" and genotype.dilute[0] == "D" and genotype.eumelanin[0] == "B":
                return "American Bombay"
            return False
    
        return "American Burmese"

    @staticmethod
    def Aphrodite(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False

        if genotype.pointgene[0] != "C":
            return False
        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
    
        return "Aphrodite's Giant"

    @staticmethod
    def Arab(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""] or genotype.furLength[0] != "L":
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False

        if genotype.pointgene[0] != "C" or (genotype.eumelanin[0] != "B" and 'o' in genotype.sexgene) or genotype.silver[0] != "i":
            return False
        if genotype.white[0] in ["W", "wg"]:
            return False
        if genotype.agouti[0] == "A" and (genotype.ticked[0] != "ta" or genotype.mack[0] == "mc" or genotype.wbsum > 11 or\
                                            genotype.ticksum > 3 or genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if 'o' not in genotype.sexgene and genotype.dilute[0] == "d":
            return False

        return "Arabian Mau"

    @staticmethod
    def Asian(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] == "Apb":
            return False
        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
    
        if genotype.white[0] != "w" or genotype.pointgene[0] not in ["C", "cb"] or (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False
    
        if genotype.agouti[0] != "a" and genotype.wbsum > 11:
            return "Burmilla"
        if genotype.agouti[0] == "a" and genotype.pointgene[0] == "cb":
            return "European Burmese"
        if genotype.furLength[0] == "l":
            return "Asian Longhair"
        return "Asian Shorthair"

    @staticmethod
    def AusMist(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] != "A" or 'O' in genotype.sexgene or genotype.silver[0] == "I" or genotype.white[0] != "w":
            return False
        if genotype.bengsum > 3 or genotype.soksum > 3:
            return False

        if genotype.pointgene[0] != "cb" or genotype.ticked[0] != "ta" or (genotype.mack[0] != "mc" and genotype.spotsum < 6):
            return False
        
        return "Australian Mist"

    @staticmethod
    def Bengal(genotype, phenotype):
        if phenotype.length == "hairless" or (phenotype.furtype != [""] and phenotype.furtype != [" shiny", " fur"]):
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False

        if genotype.white[0] != "w" or (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False
        if genotype.ticked[0] == 'Ta' or (genotype.mack[0] == "Mc" and genotype.spotsum < 6):
            return False
        
        if genotype.furLength[0] == "l":
            return "Cashmere"
        return "Bengal"

    @staticmethod
    def Birman(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] == "Apb":
            return False
        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False

        if genotype.pointgene[0] != "cs" or genotype.white[0] != 'wg':
            return False
    
        if genotype.furLength[0] == "L":
            return "Templecat"
        return "Birman"

    @staticmethod
    def Brazil(genotype, phenotype):
        if phenotype.length != "shorthaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False

        if genotype.pointgene[0] != "C":
            return False
        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
    
        return "Brazilian Shorthair"

    @staticmethod
    def British(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if genotype.curl[0] != "cu" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E":
            return False
        if genotype.pinkdilute[0] == "dp":
            return False

        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False
        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
    
        if genotype.fold[0] == "Fd":
            return "Scottish Fold"
        if genotype.white[0] == 'w' and genotype.pointgene[0] == 'C' and genotype.pax3[0] == 'DBEcel':
            if genotype.furLength[0] == "l":
                return "Celestial Longhair"
            return "Celestial Shorthair"
        if genotype.furLength[0] == "l":
            return "British Longhair"
        return "British Shorthair"

    @staticmethod
    def Ceylon(genotype, phenotype):
        if phenotype.length != "shorthaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] != "A" or (genotype.wbsum > 11 or genotype.bengsum > 3 or genotype.soksum > 3):
            return False

        if genotype.eumelanin[0] != "B" or genotype.white[0] != 'w':
            return False
        if genotype.silver[0] == 'I' or genotype.pointgene[0] != "C":
            return False
        
        return "Ceylon"

    @staticmethod
    def Chartreux(genotype, phenotype):
        if phenotype.length != "shorthaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] != "a":
            return False

        if genotype.eumelanin[0] != "B" or 'O' in genotype.sexgene or genotype.dilute[0] != 'd' or genotype.white[0] != 'w':
            return False
        if genotype.silver[0] == 'I' or genotype.pointgene[0] != "C":
            return False
        
        if genotype.breeds.get("Chartreux", 0) >= 75:
            return "Chartreux"
        if genotype.breeds.get("Korat", 0) >= 75:
            return "Korat"

        return "Huh????"

    @staticmethod
    def Chausie(genotype, phenotype):
        if phenotype.length != "shorthaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] not in ["E", "Eg"] or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] == "Apb":
            return False

        if genotype.eumelanin[0] != "B" or 'O' in genotype.sexgene or genotype.dilute[0] != 'D' or genotype.white[0] != 'w':
            return False
        if genotype.silver[0] == 'I' or genotype.pointgene[0] != "C" or genotype.ticked[0] != "Ta" or genotype.wbsum > 11:
            return False
        
        return "Chausie"

    @staticmethod
    def Clippercat(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or genotype.munch[0] == "Mk" or genotype.poly[0] != "Pd":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene or 'cb' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3 or genotype.wbsum > 11):
            return False
        if genotype.agouti[0] == "Apb":
            return False
    
        return "Clippercat"

    @staticmethod
    def Cornish(genotype, phenotype):
        if phenotype.length == "hairless" or (phenotype.furtype != ["rexed", " fur"] and genotype.cornish[0] != "r"):
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False
    
        if genotype.breeds.get("Cornish Rex", 0) >= 75:
            if genotype.furLength[0] == "l":
                return "Californian Rex"
            return "Cornish Rex"
        if genotype.breeds.get("German Rex", 0) >= 75:
            if genotype.furLength[0] == "l":
                return False
            return "German Rex"

    @staticmethod
    def Devon(genotype, phenotype):
        if phenotype.length == "hairless" or (phenotype.furtype != ["rexed", " fur"] and genotype.sedesp[0] != "re"):
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False
    
        return "Devon Rex"

    @staticmethod
    def Donskoy(genotype, phenotype):
        if 'sparse' in phenotype.furtype or 'wiry' in phenotype.furtype or 'rexed' in phenotype.furtype or 'no undercoat' in phenotype.furtype or 'satin' in phenotype.furtype or 'shiny' in phenotype.furtype:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] == "Dm":
            return False
        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False
    
        return "Donskoy"

    @staticmethod
    def Egyptian(genotype, phenotype):
        if phenotype.length != "shorthaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene or 'cb' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3 or genotype.wbsum > 11):
            return False
        if genotype.agouti[0] == "Apb":
            return False

        if genotype.eumelanin[0] != "B" or 'O' in genotype.sexgene or genotype.dilute[0] != "D" or genotype.white[0] != "w" or genotype.pointgene[0] != "C":
            return False
        if genotype.ticked[0] != "ta" or genotype.mack[0] != "Mc" or genotype.spotsum < 6:
            return False
    
        
        if genotype.breeds.get("Egyptian Mau", 0) >= 75:
            return "Egyptian Mau"
        if genotype.breeds.get("Savannah", 0) >= 75:
            return "Savannah"

        return "Huh????"

    @staticmethod
    def European(genotype, phenotype):
        if phenotype.length != "shorthaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False

        if genotype.eumelanin[0] != "B" or genotype.pointgene[0] != "C":
            return False
        
        return "European Shorthair"

    @staticmethod
    def GermanLH(genotype, phenotype):
        if phenotype.length != "longhaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene or 'cb' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        
        return "German Longhair"

    @staticmethod
    def Havana(genotype, phenotype):
        if phenotype.length != "shorthaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] != "a":
            return False

        if genotype.eumelanin[0] != "b" or 'O' in genotype.sexgene or genotype.white[0] != 'w':
            return False
        if genotype.silver[0] == 'I' or genotype.pointgene[0] != "C":
            return False
        
        return "Havana"

    @staticmethod
    def Highlander(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if genotype.curl[0] != "Cu" or genotype.fold[0] == "Fd" or (phenotype.tailtype != "" and genotype.manx[0] != "Ab") or genotype.munch[0] == "Mk":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
    
        return "Highlander"

    @staticmethod
    def JapBob(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or (phenotype.tailtype.find("pom-pom") == -1 or genotype.jbob[0] != "jb") or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        
        return "Japanese Bobtail"

    @staticmethod
    def Kanaani(genotype, phenotype):
        if phenotype.length != "shorthaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] != "A" or (genotype.wbsum > 11 or genotype.bengsum > 3 or genotype.soksum > 3):
            return False

        if 'O' in genotype.sexgene or genotype.dilute[0] == 'd' or genotype.white[0] != 'w':
            return False
        if genotype.silver[0] == 'I' or genotype.pointgene[0] != "C" or genotype.agouti[0] != "A":
            return False
        if genotype.ticked[0] != "ta" or (genotype.mack[0] == "Mc" and genotype.spotsum < 6):
            return False
        
        return "Kanaani"

    @staticmethod
    def Karel(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or (phenotype.tailtype.find("pom-pom") == -1 or genotype.kab[0] != "kab") or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False

        if genotype.eumelanin[0] != "B" or genotype.pointgene[0] != "C":
            return False
        
        return "Karelian Bobtail"

    @staticmethod
    def Khao(genotype, phenotype):
        if phenotype.length != "shorthaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False

        if genotype.white[0] != "W":
            return False
        
        return "Khao Manee"

    @staticmethod
    def Kuril(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or (phenotype.tailtype.find("pom-pom") == -1 or genotype.kub[0] != "Kub") or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] not in ["E", 'ec'] or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False

        if genotype.eumelanin[0] != "B" or genotype.pointgene[0] != "C":
            return False
        
        return "Kurilian Bobtail"

    @staticmethod
    def LaPerm(genotype, phenotype):
        if phenotype.length == "hairless" or (phenotype.furtype != ["rexed", " fur"] and genotype.laperm[0] != "Lp"):
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if genotype.ghosting[0] == "Gh":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False
    
        return "LaPerm"

    @staticmethod
    def Lin(genotype, phenotype):
        if phenotype.length != "longhaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] != "a":
            return False

        if genotype.eumelanin[0] != "B" or 'O' in genotype.sexgene or 'wt' in genotype.white:
            return False
        if genotype.silver[0] == 'I' or genotype.pointgene[0] != "C" or genotype.dilute[0] != "D":
            return False
        
        return "Lin-Qing Lion cat"

    @staticmethod
    def Lykoi(genotype, phenotype):
        if phenotype.length == "hairless" or (phenotype.furtype != ["sparse", " fur"]):
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False
    
        return "Lykoi"

    @staticmethod
    def Mandalay(genotype, phenotype):
        if phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] not in ["E", "er"] or genotype.corin[0] != "N":
            return False
        if genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene or 'cs' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3 or genotype.ticked[0] != "Ta"):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        
        if genotype.furLength[0] == 'l':
            return "Tiffany"
        if genotype.pointgene[0] == "cb":
            return "Burmese"
        return "Mandalay"

    @staticmethod
    def Maine(genotype, phenotype):
        if phenotype.length != "longhaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or genotype.munch[0] != "mk":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False

        if genotype.pointgene[0] != "C":
            return False
        genotype.longtype = "long"

        return "Maine Coon"

    @staticmethod
    def Manx(genotype, phenotype):
        if phenotype.length == "hairless" or (phenotype.furtype != [""] and (phenotype.furtype != ["rexed", " fur"] and genotype.cornish[0] != "r")):
            return False
        if phenotype.eartype != "" or (phenotype.tailtype != "" and genotype.manx[0] != "M") or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] not in ["E", 'ec'] or genotype.corin[0] != "N":
            return False
        if genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        
        if genotype.cornish[0] == "r":
            if genotype.furLength[0] == "l":
                return "Tasman Cymric"
            return "Tasman Manx"
        if genotype.furLength[0] == "l":
            return "Cymric"
        return "Manx"

    @staticmethod
    def Mekong(genotype, phenotype):
        if phenotype.length != "shorthaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or (phenotype.tailtype.find("pom-pom") == -1 or genotype.jbob[0] != "jb") or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
    
        if genotype.white[0] != "w" or genotype.pointgene[0] != "cs":
            return False
        
        return "Mekong Bobtail"

    @staticmethod
    def Munchkin(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or genotype.poly[0] == "Pd":
            return False
        
        if phenotype.fade != "":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        
        return "Munchkin"

    @staticmethod
    def NewZeal(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False

        if genotype.eumelanin[0] != "B" or genotype.pointgene[0] != "C":
            return False
        
        if genotype.furLength[0] == "l":
            return "New Zealand Longhair"
        return "New Zealand Shorthair"

    @staticmethod
    def NFC(genotype, phenotype):
        if phenotype.length != "longhaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or genotype.munch[0] != "mk":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] not in ["E", 'ea'] or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False

        if genotype.pointgene[0] != "C":
            return False
        genotype.longtype = "long"

        return "Norwegian Forest cat"

    @staticmethod
    def Ocicat(genotype, phenotype):
        if phenotype.length != "shorthaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False

        if 'O' in genotype.sexgene or genotype.white[0] != 'w' or genotype.pointgene[0] != "C":
            return False
        if genotype.agouti[0] == "A" and (genotype.mack[0] == "Mc" and genotype.spotsum < 6 or genotype.ticked[0] == "Ta"):
            return False
        
        if genotype.mack[0] == "mc":
            return "Jungala"
        return "Ocicat"

    @staticmethod
    def Oriental(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.pinkdilute[0] == "dp":
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False

        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene or 'cb' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False
        
        genotype.longtype = "medium"
        if genotype.pointgene[0] == "cs" and genotype.white[0] != 'W':
            if genotype.furLength[0] == "l":
                return "Balinese"
            return "Siamese"
        if genotype.furLength[0] == "l":
            return "Oriental Longhair"
        return "Oriental Shorthair"

    @staticmethod
    def Persian(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or genotype.munch[0] != "mk":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene or 'cb' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3 or genotype.ticked[0] == "Ta"):
            return False
        if genotype.agouti[0] == "Apb":
            return False

        genotype.longtype = "long"

        if genotype.furLength[0] == "l":
            if genotype.pointgene[0] == "cs":
                if genotype.poly[0] == "Pd":
                    return "Nepalayan"
                return "Himalayan"
            if genotype.poly[0] == "Pd":
                return False
            return "Persian"
        return "Exotic"

    @staticmethod
    def Pixiebob(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or (phenotype.tailtype != "" and genotype.manx[0] != "Ab") or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] != "A" or (genotype.bengsum > 3 or genotype.soksum > 3):
            return False

        if genotype.eumelanin[0] != "B" or 'O' in genotype.sexgene or genotype.dilute[0] != 'D' or genotype.white[0] != 'w':
            return False
        if genotype.silver[0] == 'I' or genotype.pointgene[0] != "C" or genotype.ticked[0] == "Ta" or genotype.wbsum > 11:
            return False
        
        if genotype.mack[0] == "mc" or genotype.spotsum < 6:
            return False
        
        return "Pixie-Bob"

    @staticmethod
    def Ragamuffin(genotype, phenotype):
        if phenotype.length != "longhaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        genotype.longtype = "long"

        return "Ragamuffin"

    @staticmethod
    def Ragdoll(genotype, phenotype):
        if phenotype.length != "longhaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.pinkdilute[0] == "dp":
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        genotype.longtype = "long"

        if genotype.pointgene[0] != "cs" or genotype.white[0] not in ["ws", "w"] or genotype.white[1] not in ["ws", "w"]:
            return False

        return "Ragdoll"

    @staticmethod
    def Russian(genotype, phenotype):
        if phenotype.length == "hairless" or (phenotype.furtype != [""] and phenotype.furtype != [" satin", " fur"]):
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] != "a" and genotype.white[0] != "W":
            return False

        if genotype.eumelanin[0] != "B" or 'O' in genotype.sexgene or genotype.white[0] not in ["W", "w"]:
            return False
        if genotype.silver[0] == 'I' or genotype.pointgene[0] != "C":
            return False
        if genotype.furLength[0] == "l" and (genotype.dilute[0] != "d" or genotype.white[0] != "w"):
            return False
        
        if genotype.furLength[0] == "L":
            if genotype.white[0] == "W":
                return "Russian White"
            if genotype.dilute[0] == "D":
                return "Russian Black"
            return "Russian Blue"
        return "Nebelung"
    
    @staticmethod
    def Selkirk(genotype, phenotype):
        if phenotype.length == "hairless" or ((phenotype.furtype != [""] and phenotype.furtype != ["rexed", " fur"]) or (phenotype.furtype == ["rexed", " fur"] and genotype.sedesp[0] != "Se")):
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.sedesp[0] != "Se":
            return "Selkirk Rex variant"
        return "Selkirk Rex"

    @staticmethod
    def Siberian(genotype, phenotype):
        if phenotype.length != "longhaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] == "fg":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene or 'cb' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        genotype.longtype = "long"

        if genotype.pointgene[0] == "cs":
            return "Neva Masquerade"
        return "Siberian"

    @staticmethod
    def Singapura(genotype, phenotype):
        if phenotype.length != "shorthaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] != "A":
            return False

        if genotype.eumelanin[0] != "B" or 'O' in genotype.sexgene or genotype.dilute[0] != 'D' or genotype.white[0] != 'w':
            return False
        if genotype.silver[0] == 'I' or genotype.pointgene != ["cb", "cb"] or genotype.ticked[0] != "Ta" or genotype.wbsum > 11:
            return False
        
        return "Singapura"

    @staticmethod
    def Snowshoe(genotype, phenotype):
        if phenotype.length != "shorthaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.pinkdilute[0] == "dp":
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False

        if genotype.pointgene[0] != "cs" or genotype.white[0] not in ["ws", "w"] or genotype.white[1] not in ["ws", "w"] or 'ws' not in genotype.white:
            return False

        return "Snowshoe"

    @staticmethod
    def Sokoke(genotype, phenotype):
        if phenotype.length != "shorthaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] != "A":
            return False

        if genotype.eumelanin[0] != "B" or 'O' in genotype.sexgene or genotype.dilute[0] != 'D' or genotype.white[0] != 'w':
            return False
        if genotype.silver[0] == 'I' or genotype.pointgene[0] not in ["C", "cs"] or genotype.ticked[0] == "Ta" or genotype.wbsum > 11:
            return False
        if genotype.soksum < 6 or genotype.mack[0] != "mc" or genotype.bengsum > 3:
            return False
        
        return "Sokoke"

    @staticmethod
    def Sphynx(genotype, phenotype):
        if genotype.sedesp != ["hr", "hr"]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] == "Dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False
    
        return "Sphynx"

    @staticmethod
    def Tenn(genotype, phenotype):
        if phenotype.length == "hairless" or (phenotype.furtype != ["rexed", " satin", " fur"] or genotype.tenn[0] != "tr"):
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] == "Dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False
    
        return "Tennessee Rex"

    @staticmethod
    def Thai(genotype, phenotype):
        if phenotype.length != "shorthaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] == "Dm" or genotype.pinkdilute[0] == "dp":
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False

        if genotype.pointgene[0] != "cs" or genotype.white[0] != "w":
            return False

        return "Thai"

    @staticmethod
    def Tonk(genotype, phenotype):
        if phenotype.length != "shorthaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.pinkdilute[0] == "dp":
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3 or genotype.wbsum > 11):
            return False
        if genotype.agouti[0] == "Apb":
            return False

        if genotype.pointgene[0] not in ["cb", "cs"] or genotype.pointgene[1] not in ["cb", "cs"] or genotype.white[0] != "w":
            return False

        return "Tonkinese"

    @staticmethod
    def Toybob(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or (phenotype.tailtype.find("pom-pom") == -1 or genotype.toybob[0] != "Tb") or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        
        return "Toybob"

    @staticmethod
    def Toyger(genotype, phenotype):
        if phenotype.length != "shorthaired" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] != "A":
            return False

        if genotype.eumelanin[0] != "B" or 'O' in genotype.sexgene or genotype.dilute[0] != 'D' or genotype.white[0] != 'w':
            return False
        if genotype.silver[0] == 'I' or genotype.pointgene[0] != "C" or genotype.ticked[0] == "Ta" or genotype.wbsum > 11:
            return False
        if genotype.bengsum < 6 or genotype.mack[0] != "Mc" or genotype.soksum > 3:
            return False
        
        return "Toyger"

    @staticmethod
    def Turkish(genotype, phenotype):
        if phenotype.length == "hairless" or phenotype.furtype != [""]:
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False

        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3):
            return False
        if genotype.agouti[0] == "Apb":
            return False

        if genotype.eumelanin[0] != "B" or genotype.pointgene[0] != "C":
            return False
        
        if genotype.furLength[0] == "L":
            return "Anatoli"
        if genotype.white_pattern == ["full white"]:
            return "Turkish Vankedisi"
        if genotype.white == ["ws", "ws"] and genotype.whitegrade == 4:
            return "Turkish Van"
        return "Turkish Angora"

    @staticmethod
    def Ural(genotype, phenotype):
        if phenotype.length == "hairless" or (phenotype.furtype != ["rexed", " fur"] or genotype.urals[0] != "ru"):
            return False
        if phenotype.eartype != "" or phenotype.tailtype != "" or phenotype.pawtype != "":
            return False
        
        if phenotype.fade != "" or genotype.karp[0] == "K":
            return False
        if genotype.ext[0] != "E" or genotype.corin[0] != "N":
            return False
        if genotype.dilutemd[0] != "dm" or genotype.pinkdilute[0] == "dp":
            return False
        if genotype.agouti[0] == "A" and (genotype.bengsum > 3 or genotype.soksum > 3 or genotype.ticked[0] == "Ta"):
            return False
        if genotype.agouti[0] == "Apb":
            return False
        if (('cm' in genotype.pointgene or 'c' in genotype.pointgene or 'cb' in genotype.pointgene) and genotype.pointgene[0] != "C"):
            return False
    
        if genotype.eumelanin[0] != "B":
            return False
    
        return "Ural Rex"


def find_my_breed(genotype, phenotype, config):
    purebred_range = 75
    mix_range = 12.5

    hybrids = {
        "Bambino" : genotype.breeds.get("Munchkin", 0) + genotype.breeds.get("Sphynx", 0), 
        "Cheetoh" : genotype.breeds.get("Ocicat", 0) + genotype.breeds.get("Bengal", 0), 
        "Elf" : genotype.breeds.get("American Curl", 0) + genotype.breeds.get("Sphynx", 0), 
        "Foldex" : genotype.breeds.get("Persian/Exotic", 0) + genotype.breeds.get("British", 0), 
        "Gaelic Fold" : genotype.breeds.get("Munchkin", 0) + genotype.breeds.get("Persian/Exotic", 0) + genotype.breeds.get("British", 0), 
        "Kinkalow" : genotype.breeds.get("American Curl", 0) + genotype.breeds.get("Munchkin", 0), 
        "Lambkin" : genotype.breeds.get("Selkirk Rex", 0) + genotype.breeds.get("Munchkin", 0), 
        "Napoleon" : genotype.breeds.get("Munchkin", 0) + genotype.breeds.get("Persian/Exotic", 0),
        "Peterbald" : genotype.breeds.get("Oriental/Siamese", 0) + genotype.breeds.get("Donskoy", 0), 
        "Serengeti" : genotype.breeds.get("Oriental/Siamese", 0) + genotype.breeds.get("Bengal", 0), 
        "Skookum" : genotype.breeds.get("LaPerm", 0) + genotype.breeds.get("Munchkin", 0)
    }

    if not genotype.breeds.get("Munchkin", False) or not genotype.breeds.get("Sphynx", False):
        hybrids["Bambino"] = 0
    if not genotype.breeds.get("Ocicat", False) or not genotype.breeds.get("Bengal", False):
        hybrids["Cheetoh"] = 0
    if not genotype.breeds.get("Sphynx", False):
        hybrids["Elf"] = 0
    if not genotype.breeds.get("Persian/Exotic", False) or not genotype.breeds.get("British", False) or genotype.breeds.get("Munchkin", False):
        hybrids["Foldex"] = 0
    if not genotype.breeds.get("Munchkin", False) or not genotype.breeds.get("Persian/Exotic", False) or not genotype.breeds.get("British", False):
        hybrids["Gaelic Fold"] = 0
    if not genotype.breeds.get("American Curl", False) or not genotype.breeds.get("Munchkin", False):
        hybrids["Kinkalow"] = 0
    if not genotype.breeds.get("Selkirk Rex", False) or not genotype.breeds.get("Munchkin", False):
        hybrids["Lambkin"] = 0
    if not genotype.breeds.get("Persian/Exotic", False) or not genotype.breeds.get("Munchkin", False) or genotype.breeds.get("British", False):
        hybrids["Napoleon"] = 0
    if not genotype.breeds.get("Oriental/Siamese", False) or not genotype.breeds.get("Donskoy", False):
        hybrids["Peterbald"] = 0
    if not genotype.breeds.get("Oriental/Siamese", False) or not genotype.breeds.get("Bengal", False):
        hybrids["Serengeti"] = 0
    if not genotype.breeds.get("LaPerm", False) or not genotype.breeds.get("Munchkin", False):
        hybrids["Skookum"] = 0

    sorted_hybrids = dict(sorted(hybrids.items(), key=lambda item: item[1], reverse=True))
    sorted_breeds = dict(sorted(genotype.breeds.items(), key=lambda item: item[1], reverse=True))
    
    for breed in sorted_hybrids:
        if sorted_hybrids[breed] < purebred_range:
            break
        if breed == "Bambino" and genotype.sedesp[0] == "hr" and genotype.breeds.get("Munchkin", 0) and genotype.breeds.get("Sphynx", 0):
            return "Bambino"
        elif breed == "Cheetoh" and Breed_checker.Cheetoh(genotype, phenotype) and genotype.breeds.get("Ocicat", 0) and genotype.breeds.get("Bengal", 0):
            return "Cheetoh"
        elif breed == "Elf" and genotype.sedesp[0] == "hr" and genotype.curl[0] == "Cu" and genotype.breeds.get("Sphynx", 0):
            return "Elf"
        elif breed == "Foldex" and phenotype.length != "hairless" and genotype.lykoi[0] == "Ly" and genotype.eumelanin[0] != "bl" and genotype.breeds.get("Persian/Exotic", 0) and genotype.breeds.get("British", 0):
            return "Foldex"
        elif breed == "Gaelic Fold" and phenotype.length != "hairless" and genotype.lykoi[0] == "Ly" and genotype.breeds.get("Munchkin", 0) and genotype.breeds.get("Persian/Exotic", 0) and genotype.breeds.get("British", 0):
            return "Gaelic Fold"
        elif breed == "Kinkalow" and phenotype.length != "hairless" and genotype.lykoi[0] == "Ly" and genotype.curl[0] == "Cu" and genotype.breeds.get("American Curl", 0) and genotype.breeds.get("Munchkin", 0):
            return "Kinkalow"
        elif breed == "Lambkin" and phenotype.length != "hairless" and genotype.lykoi[0] == "Ly" and genotype.sedesp[0] == "Se" and genotype.breeds.get("Selkirk Rex", 0) and genotype.breeds.get("Munchkin", 0):
            return "Lambkin"
        elif breed == "Napoleon" and phenotype.length != "hairless" and genotype.lykoi[0] == "Ly" and genotype.breeds.get("Persian/Exotic", 0) and genotype.breeds.get("Munchkin", 0):
            return "Napoleon"
        elif breed == "Peterbald" and genotype.breeds.get("Oriental/Siamese", 0) and genotype.breeds.get("Donskoy", 0):
            return "Peterbald"
        elif breed == "Serengeti" and Breed_checker.Serengeti(genotype, phenotype) and genotype.breeds.get("Oriental/Siamese", 0) and genotype.breeds.get("Bengal", 0):
            return "Serengeti"
        elif breed == "Skookum" and phenotype.length != "hairless" and genotype.lykoi[0] == "Ly" and genotype.laperm[0] == "Lp" and genotype.breeds.get("LaPerm", 0) and genotype.breeds.get("Munchkin", 0):
            return "Skookum"

    for breed in sorted_breeds:
        if sorted_breeds[breed] < purebred_range:
            break
        if breed_functions["checker"][breed](genotype, phenotype):
            return breed_functions["checker"][breed](genotype, phenotype)

    sorted_breeds.update(sorted_hybrids)
    sorted_breeds = dict(sorted(sorted_breeds.items(), key=lambda item: item[1], reverse=True))

    top = 0
    breed_mix = ""
    for breed in sorted_breeds:
        if sorted_breeds[breed] < mix_range:
            if breed_mix == "":
                break
            return breed_mix + " mix"
        elif sorted_breeds[breed] > top:
            top = sorted_breeds[breed]
            breed_mix = breed
        elif sorted_breeds[breed] == top:
            breed_mix += ", " + breed
            

    return ""

breed_functions = {
    "generator" : {
        "Abyssinian" : Breed_generator.Aby,
        "American Bobtail" : Breed_generator.AmBob,
        "American Curl" : Breed_generator.AmCurl,
        "American Shorthair" : Breed_generator.AmSH,
        "American Burmese/Bombay" : Breed_generator.AmBurm,
        "Aphrodite" : Breed_generator.Aphrodite,
        "Arabian Mau" : Breed_generator.Arab,
        "Asian/Burmese" : Breed_generator.Asian,
        "Australian Mist" : Breed_generator.AusMist,
        "Bengal" : Breed_generator.Bengal,
        "Birman" : Breed_generator.Birman,
        "Brazilian Shorthair" : Breed_generator.Brazil,
        "British" : Breed_generator.British,
        "Ceylon" : Breed_generator.Ceylon,
        "Chartreux" : Breed_generator.Chartreux,
        "Korat" : Breed_generator.Chartreux,
        "Chausie" : Breed_generator.Chausie,
        "Clippercat" : Breed_generator.Clippercat,
        "Cornish Rex" : Breed_generator.Cornish,
        "German Rex" : Breed_generator.Cornish,
        "Devon Rex" : Breed_generator.Devon,
        "Donskoy" : Breed_generator.Donskoy,
        "Egyptian Mau" : Breed_generator.Egyptian,
        "European Shorthair" : Breed_generator.European,
        "German Longhair" : Breed_generator.GermanLH,
        "Havana" : Breed_generator.Havana,
        "Highlander" : Breed_generator.Highlander,
        "Japanese Bobtail" : Breed_generator.JapBob,
        "Kanaani" : Breed_generator.Kanaani,
        "Karelian Bobtail" : Breed_generator.Karel,
        "Khao Manee" : Breed_generator.Khao,
        "Kurilian Bobtail" : Breed_generator.Kuril,
        "LaPerm" : Breed_generator.LaPerm,
        "Lin-Qing Lion cat" : Breed_generator.Lin,
        "Lykoi" : Breed_generator.Lykoi,
        "Mandalay/Burmese" : Breed_generator.Mandalay,
        "Maine Coon" : Breed_generator.Maine,
        "Manx" : Breed_generator.Manx,
        "Mekong Bobtail" : Breed_generator.Mekong,
        "Munchkin" : Breed_generator.Munchkin,
        "New Zealand" : Breed_generator.NewZeal,
        "Norwegian Forest cat" : Breed_generator.NFC,
        "Ocicat" : Breed_generator.Ocicat,
        "Oriental/Siamese" : Breed_generator.Oriental,
        "Persian/Exotic" : Breed_generator.Persian,
        "Pixie-Bob" : Breed_generator.Pixiebob,
        "Ragamuffin" : Breed_generator.Ragamuffin,
        "Ragdoll" : Breed_generator.Ragdoll,
        "Russian" : Breed_generator.Russian,
        "Savannah" : Breed_generator.Egyptian,
        "Selkirk Rex" : Breed_generator.Selkirk,
        "Siberian" : Breed_generator.Siberian,
        "Singapura" : Breed_generator.Singapura,
        "Snowshoe" : Breed_generator.Snowshoe,
        "Sokoke" : Breed_generator.Sokoke,
        "Sphynx" : Breed_generator.Sphynx,
        "Tennessee Rex" : Breed_generator.Tenn,
        "Thai" : Breed_generator.Thai,
        "Tonkinese" : Breed_generator.Tonk,
        "Toybob" : Breed_generator.Toybob,
        "Toyger" : Breed_generator.Toyger,
        "Turkish" : Breed_generator.Turkish,
        "Ural Rex" : Breed_generator.Ural,
        "Bambino" : Breed_generator.Bambino,
        "Cheetoh" : Breed_generator.Cheetoh,
        "Foldex" : Breed_generator.Foldex,
        "Gaelic Fold" : Breed_generator.Gaelic,
        "Kinkalow" : Breed_generator.Kinkalow,
        "Lambkin" : Breed_generator.Lambkin,
        "Napoleon" : Breed_generator.Napoleon,
        "Peterbald" : Breed_generator.Peterbald,
        "Serengeti" : Breed_generator.Serengeti,
        "Skookum" : Breed_generator.Skookum
    },
    "checker": {
        "Abyssinian" : Breed_checker.Aby,
        "American Bobtail" : Breed_checker.AmBob,
        "American Curl" : Breed_checker.AmCurl,
        "American Shorthair" : Breed_checker.AmSH,
        "American Burmese/Bombay" : Breed_checker.AmBurm,
        "Aphrodite" : Breed_checker.Aphrodite,
        "Arabian Mau" : Breed_checker.Arab,
        "Asian/Burmese" : Breed_checker.Asian,
        "Australian Mist" : Breed_checker.AusMist,
        "Bengal" : Breed_checker.Bengal,
        "Birman" : Breed_checker.Birman,
        "Brazilian Shorthair" : Breed_checker.Brazil,
        "British" : Breed_checker.British,
        "Ceylon" : Breed_checker.Ceylon,
        "Chartreux" : Breed_checker.Chartreux,
        "Korat" : Breed_checker.Chartreux,
        "Chausie" : Breed_checker.Chausie,
        "Clippercat" : Breed_checker.Clippercat,
        "Cornish Rex" : Breed_checker.Cornish,
        "German Rex" : Breed_checker.Cornish,
        "Devon Rex" : Breed_checker.Devon,
        "Donskoy" : Breed_checker.Donskoy,
        "Egyptian Mau" : Breed_checker.Egyptian,
        "Savannah" : Breed_checker.Egyptian,
        "European Shorthair" : Breed_checker.European,
        "German Longhair" : Breed_checker.GermanLH,
        "Havana" : Breed_checker.Havana,
        "Highlander" : Breed_checker.Highlander,
        "Japanese Bobtail" : Breed_checker.JapBob,
        "Kanaani" : Breed_checker.Kanaani,
        "Karelian Bobtail" : Breed_checker.Karel,
        "Khao Manee" : Breed_checker.Khao,
        "Kurilian Bobtail" : Breed_checker.Kuril,
        "LaPerm" : Breed_checker.LaPerm,
        "Lin-Qing Lion cat" : Breed_checker.Lin,
        "Lykoi" : Breed_checker.Lykoi,
        "Mandalay/Burmese" : Breed_checker.Mandalay,
        "Maine Coon" : Breed_checker.Maine,
        "Manx" : Breed_checker.Manx,
        "Mekong Bobtail" : Breed_checker.Mekong,
        "Munchkin" : Breed_checker.Munchkin,
        "New Zealand" : Breed_checker.NewZeal,
        "Norwegian Forest cat" : Breed_checker.NFC,
        "Ocicat" : Breed_checker.Ocicat,
        "Oriental/Siamese" : Breed_checker.Oriental,
        "Persian/Exotic" : Breed_checker.Persian,
        "Pixie-Bob" : Breed_checker.Pixiebob,
        "Ragamuffin" : Breed_checker.Ragamuffin,
        "Ragdoll" : Breed_checker.Ragdoll,
        "Russian" : Breed_checker.Russian,
        "Selkirk Rex" : Breed_checker.Selkirk,
        "Siberian" : Breed_checker.Siberian,
        "Singapura" : Breed_checker.Singapura,
        "Snowshoe" : Breed_checker.Snowshoe,
        "Sokoke" : Breed_checker.Sokoke,
        "Sphynx" : Breed_checker.Sphynx,
        "Tennessee Rex" : Breed_checker.Tenn,
        "Thai" : Breed_checker.Thai,
        "Tonkinese" : Breed_checker.Tonk,
        "Toybob" : Breed_checker.Toybob,
        "Toyger" : Breed_checker.Toyger,
        "Turkish" : Breed_checker.Turkish,
        "Ural Rex" : Breed_checker.Ural
    }
}