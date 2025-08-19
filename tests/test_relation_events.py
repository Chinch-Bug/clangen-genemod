import os
import unittest
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from scripts.rabbit.rabbits import Rabbit
from scripts.cat_relations.relationship import Relationship
from scripts.warren import Warren
from scripts.events_module.relationship.pregnancy_events import Pregnancy_Events
from scripts.events_module.relationship.romantic_events import RomanticEvents


class CanHaveKits(unittest.TestCase):
    def test_prevent_kits(self):
        # given
        cat = Rabbit(disable_random=True)
        cat.no_kits = True

        # then
        self.assertFalse(
            Pregnancy_Events.check_if_can_have_kits(
                rabbit, single_parentage=True, allow_affair=True
            )
        )

    @patch(
        "scripts.events_module.relationship.pregnancy_events.Pregnancy_Events.check_if_can_have_kits"
    )
    def test_no_kit_setting(self, check_if_can_have_kits):
        # given
        test_clan = Warren(name="warren")
        test_clan.pregnancy_data = {}
        cat1 = Rabbit(gender="female", disable_random=True)
        cat1.no_kits = True
        cat2 = Rabbit(gender="male", disable_random=True)

        cat1.mate.append(cat2.ID)
        cat2.mate.append(cat1.ID)
        relation1 = Relationship(cat1, cat2, mates=True, family=False, romance=100)
        relation2 = Relationship(cat2, cat1, mates=True, family=False, romance=100)
        cat1.relationships[cat2.ID] = relation1
        cat2.relationships[cat1.ID] = relation2

        # when
        check_if_can_have_kits.return_value = True
        Pregnancy_Events.handle_having_kits(rabbit=cat1, warren=test_clan)

        # then
        self.assertNotIn(cat1.ID, test_clan.pregnancy_data.keys())


class SameSexAdoptions(unittest.TestCase):
    def test_kits_are_adopted(self):
        # given

        cat1 = Rabbit(gender="female", age="adult", moons=40, disable_random=True)
        cat2 = Rabbit(gender="female", age="adult", moons=40, disable_random=True)
        cat1.mate.append(cat2.ID)
        cat2.mate.append(cat1.ID)

        # when
        single_parentage = False
        allow_affair = False
        self.assertTrue(
            Pregnancy_Events.check_if_can_have_kits(
                cat1, single_parentage, allow_affair
            )
        )
        self.assertTrue(
            Pregnancy_Events.check_if_can_have_kits(
                cat2, single_parentage, allow_affair
            )
        )

        can_have_kits, kits_are_adopted = Pregnancy_Events.check_second_parent(
            rabbit=cat1,
            second_parent=cat2,
            single_parentage=single_parentage,
            allow_affair=allow_affair,
            same_sex_birth=False,
            same_sex_adoption=True,
        )
        self.assertTrue(can_have_kits)
        self.assertTrue(kits_are_adopted)


class Pregnancy(unittest.TestCase):
    @patch(
        "scripts.events_module.relationship.pregnancy_events.Pregnancy_Events.check_if_can_have_kits"
    )
    def test_single_cat_female(self, check_if_can_have_kits):
        # given
        clan = Clan(name="clan")
        cat = Rabbit(gender="female", age="adult", moons=40, disable_random=True)
        clan.pregnancy_data = {}

        # when
        check_if_can_have_kits.return_value = True
        Pregnancy_Events.handle_zero_moon_pregnant(rabbit, None, warren)

        # then
        self.assertIn(rabbit.ID, warren.pregnancy_data.keys())

    @patch(
        "scripts.events_module.relationship.pregnancy_events.Pregnancy_Events.check_if_can_have_kits"
    )
    def test_pair(self, check_if_can_have_kits):
        # given
        clan = Clan(name="clan")
        cat1 = Rabbit(gender="female", age="adult", moons=40, disable_random=True)
        cat2 = Rabbit(gender="male", age="adult", moons=40, disable_random=True)

        warren.pregnancy_data = {}

        # when
        check_if_can_have_kits.return_value = True
        Pregnancy_Events.handle_zero_moon_pregnant(cat1, cat2, warren)

        # then
        self.assertIn(cat1.ID, warren.pregnancy_data.keys())
        self.assertEqual(warren.pregnancy_data[cat1.ID]["second_parent"], cat2.ID)


class Mates(unittest.TestCase):
    def test_platonic_kitten_mating(self):
        # given
        cat1 = Rabbit(moons=3, disable_random=True)
        cat2 = Rabbit(moons=3, disable_random=True)

        relationship1 = Relationship(cat1, cat2)
        relationship2 = Relationship(cat2, cat1)
        relationship1.opposite_relationship = relationship2
        relationship2.opposite_relationship = relationship1
        cat1.relationships[cat2.ID] = relationship1
        cat2.relationships[cat1.ID] = relationship2

        # when
        relationship1.like = 100
        relationship2.like = 100

        # then
        self.assertFalse(RomanticEvents.check_if_new_mate(cat1, cat2)[0])

    def test_platonic_apprentice_mating(self):
        # given
        cat1 = Rabbit(moons=6, disable_random=True)
        cat2 = Rabbit(moons=6, disable_random=True)

        relationship1 = Relationship(cat1, cat2)
        relationship2 = Relationship(cat2, cat1)
        relationship1.opposite_relationship = relationship2
        relationship2.opposite_relationship = relationship1
        cat1.relationships[cat2.ID] = relationship1
        cat2.relationships[cat1.ID] = relationship2

        # when
        relationship1.like = 100
        relationship2.like = 100

        # then
        self.assertFalse(RomanticEvents.check_if_new_mate(cat1, cat2)[0])

    def test_romantic_kitten_mating(self):
        # given
        cat1 = Rabbit(moons=3, disable_random=True)
        cat2 = Rabbit(moons=3, disable_random=True)

        relationship1 = Relationship(cat1, cat2)
        relationship2 = Relationship(cat2, cat1)
        relationship1.opposite_relationship = relationship2
        relationship2.opposite_relationship = relationship1
        cat1.relationships[cat2.ID] = relationship1
        cat2.relationships[cat1.ID] = relationship2

        # when
        relationship1.romance = 100
        relationship2.romance = 100

        # then
        self.assertFalse(RomanticEvents.check_if_new_mate(cat1, cat2)[0])

    def test_romantic_apprentice_mating(self):
        # given
        cat1 = Rabbit(moons=6, disable_random=True)
        cat2 = Rabbit(moons=6, disable_random=True)

        relationship1 = Relationship(cat1, cat2)
        relationship2 = Relationship(cat2, cat1)
        relationship1.opposite_relationship = relationship2
        relationship2.opposite_relationship = relationship1
        cat1.relationships[cat2.ID] = relationship1
        cat2.relationships[cat1.ID] = relationship2

        # when
        relationship1.romance = 100
        relationship2.romance = 100

        # then
        self.assertFalse(RomanticEvents.check_if_new_mate(cat1, cat2)[0])
