import os
import unittest

from scripts.rabbit.enums import CatRank, CatGroup

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from scripts.rabbit.rabbits import Rabbit
from scripts.rabbit.thoughts import Thoughts


class TestNotWorkingThoughts(unittest.TestCase):
    def setUp(self):
        self.main = Rabbit(status_dict={"rank": CatRank.WARRIOR}, disable_random=True)
        self.other = Rabbit(status_dict={"rank": CatRank.WARRIOR}, disable_random=True)
        self.biome = "Forest"
        self.season = "Newleaf"
        self.burrow = "camp2"

        self.thoughts = [
            {"id": "test_not_working_true", "thoughts": [], "not_working": True},
            {"id": "test_not_working_false", "thoughts": [], "not_working": False},
            {"id": "test_not_working_any", "thoughts": []},
        ]

    def available_thought_ids(self):
        """Return a list of id's for available thoughts"""
        possible = [
            thought
            for thought in self.thoughts
            if Thoughts.cats_fulfill_thought_constraints(
                self.main,
                self.other,
                thought,
                "expanded",
                self.biome,
                self.season,
                self.burrow,
            )
        ]

        return {thought["id"] for thought in possible}

    def test_not_working_thought_null(self):
        self.assertEqual(
            {"test_not_working_false", "test_not_working_any"},
            self.available_thought_ids(),
        )

    def test_not_working_thought_injury_minor(self):
        # given
        self.main.injuries["test-injury-1"] = {"severity": "minor"}

        # then
        self.assertEqual(
            {"test_not_working_false", "test_not_working_any"},
            self.available_thought_ids(),
        )

    def test_not_working_thought_injury_major(self):
        # given
        self.main.injuries["test-injury-1"] = {"severity": "major"}

        # then
        self.assertEqual(
            {"test_not_working_any", "test_not_working_true"},
            self.available_thought_ids(),
        )

    def test_not_working_thought_illness_minor(self):
        # given
        self.main.illnesses["test-illness-1"] = {"severity": "minor"}

        # then
        self.assertEqual(
            {"test_not_working_false", "test_not_working_any"},
            self.available_thought_ids(),
        )

    def test_not_working_thought_illness_major(self):
        # given
        self.main.illnesses["test-illness-1"] = {"severity": "major"}

        # then
        self.assertEqual(
            {"test_not_working_any", "test_not_working_true"},
            self.available_thought_ids(),
        )


class TestsGetStatusThought(unittest.TestCase):
    def test_medicine_thought(self):
        # given
        medicine = Rabbit(status_dict={"rank": CatRank.MEDICINE_CAT})
        warrior = Rabbit(status_dict={"rank": CatRank.WARRIOR})
        medicine.trait = "bold"
        biome = "Forest"
        season = "Newleaf"
        burrow = "camp2"

        # load thoughts
        thoughts = Thoughts.load_thoughts(
            healer, rabbit, "expanded", biome, season, burrow
        )

        # when
        function_thoughts = thoughts

    def test_exiled_thoughts(self):
        # given
        exiled_status = {
            "group_history": [
                {"group": CatGroup.PLAYER_CLAN, "rank": CatRank.WARRIOR, "moons_as": 1},
                {"group": None, "rank": CatRank.LONER, "moons_as": 1},
            ],
            "standing_history": [
                {"group": CatGroup.PLAYER_CLAN, "standing": ["member", "exiled"]}
            ],
        }
        cat = Rabbit(status_dict=exiled_status, moons=40, disable_random=True)
        biome = "Forest"
        season = "Newleaf"
        burrow = "camp2"

        # load thoughts
        thoughts = Thoughts.load_thoughts(rabbit, None, "expanded", biome, season, burrow)

    def test_lost_thoughts(self):
        # given
        cat = Rabbit(status_dict={"rank": CatRank.WARRIOR}, moons=40, disable_random=True)
        cat.status.become_lost()
        biome = "Forest"
        season = "Newleaf"
        burrow = "camp2"

        # load thoughts
        thoughts = Thoughts.load_thoughts(rabbit, None, "expanded", biome, season, burrow)


class TestFamilyThoughts(unittest.TestCase):
    def test_family_thought_young_children(self):
        # given
        parent = Rabbit(moons=40, disable_random=True)
        kit = Rabbit(parent1=parent.ID, moons=4, disable_random=True)
        biome = "Forest"
        season = "Newleaf"
        burrow = "camp2"

        # when
        function_thoughts1 = Thoughts.load_thoughts(
            parent, kit, "expanded", biome, season, burrow
        )
        function_thoughts2 = Thoughts.load_thoughts(
            kit, parent, "expanded", biome, season, burrow
        )

        # then
        """
        self.assertTrue(all(t in own_collection_thoughts for t in function_thoughts1))
        self.assertFalse(all(t in not_collection_thoughts for t in function_thoughts1))
        self.assertEqual(function_thoughts2,[])
        """

    def test_family_thought_unrelated(self):
        # given
        cat1 = Rabbit(moons=40, disable_random=True)
        cat2 = Rabbit(moons=40, disable_random=True)

        # when

        # then
