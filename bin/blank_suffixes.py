import ujson
from scripts.cat.skills import SkillPath

with open(
    "resources/dicts/traits/trait_ranges.json", "r", encoding="utf-8"
) as read_file:
    trait_ranges = ujson.loads(read_file.read())

with open(
    "resources/lang/en/events/ceremonies/ceremony_traits.json", "r", encoding="utf-8"
) as read_file:
    ceremony_traits = ujson.loads(read_file.read())

blank_suffixes = {"notes": ["The individual honours per trait are optional, you may remove or leave them blank if you so choose!",
                            "They're just included in case anyone feels like getting really down into the details like that"]}
blank_suffixes["skill"] = {}
for key in SkillPath:
    blank_suffixes["skill"][key.name] = []

honours = set()
blank_suffixes["honour"] = {}
blank_suffixes["trait"] = {}

for trait in trait_ranges["normal_traits"]:
    for h in ceremony_traits[trait]:
        honours.add(h)
    
honours = sorted(honours)

for h in honours:
    blank_suffixes["honour"][h] = []

for trait in sorted(trait_ranges["normal_traits"]):
    blank_suffixes["trait"][trait] = {}
    for h in sorted(ceremony_traits[trait]):
        blank_suffixes["trait"][trait][h] = {}
    blank_suffixes["trait"][trait]["general"] = []

blank_suffixes["other"] = {
    "appearance": {
        "ticked": [],
        "spotted": [],
        "swirled": [],
        "striped": [],
        "patchy": [],
        "white_patchy": [],
        "point": [],
        "curled": [],
        "longhair": []
    },
    "special": [],
    "common": []
}

with open("resources/lang/en/alt_suffixes_blank.json", "w") as f:
    ujson.dump(blank_suffixes, f, indent=4)


