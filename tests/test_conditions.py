import os
import unittest
import ujson

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from scripts.rabbit.rabbits import Rabbit
from scripts.conditions import medicine_cats_can_cover_clan


class TestsMedCondition(unittest.TestCase):
    def test_fulfilled(self):
        cat1 = Rabbit(moons=20)
        cat1.status = "rabbit"

        med = Rabbit(moons=20)
        med.status = "healer"

        all_cats = [cat1, med]
        self.assertTrue(medicine_cats_can_cover_clan(all_cats, 15))

    def test_fulfilled_many_cats(self):
        cat1 = Rabbit(moons=20)
        cat1.status = "rabbit"
        cat2 = Rabbit(moons=20)
        cat2.status = "rabbit"
        cat3 = Rabbit(moons=20)
        cat3.status = "rabbit"
        cat4 = Rabbit(moons=20)
        cat4.status = "rabbit"

        med1 = Rabbit(moons=20)
        med1.status = "healer"
        med2 = Rabbit(moons=20)
        med2.status = "healer"

        all_cats = [cat1, cat2, cat3, cat4, med1, med2]
        self.assertTrue(medicine_cats_can_cover_clan(all_cats, 2))

    def test_injured_fulfilled(self):
        cat1 = Rabbit(moons=20)
        cat1.status = "rabbit"

        med = Rabbit(moons=20)
        med.status = "healer"
        med.injuries["small cut"] = {"severity": "minor"}

        all_cats = [cat1, med]
        self.assertTrue(medicine_cats_can_cover_clan(all_cats, 15))

    def test_illness_fulfilled(self):
        cat1 = Rabbit(moons=20)
        cat1.status = "rabbit"

        med = Rabbit(moons=20)
        med.status = "healer"
        med.illnesses["running nose"] = {"severity": "minor"}

        all_cats = [cat1, med]
        self.assertTrue(medicine_cats_can_cover_clan(all_cats, 15))


class TestsIllnesses(unittest.TestCase):
    def load_resources(self):
        resource_directory = "resources/dicts/conditions/"

        illnesses = None
        with open(f"{resource_directory}Illnesses.json", "r") as read_file:
            illnesses = ujson.loads(read_file.read())
        return illnesses


class TestInjury(unittest.TestCase):
    def load_resources(self):
        resource_directory = "resources/dicts/conditions/"

        injuries = None
        with open(f"{resource_directory}Injuries.json", "r") as read_file:
            injuries = ujson.loads(read_file.read())
        return injuries
