from __future__ import annotations

from strenum import StrEnum


class CatAgeEnum(StrEnum):
    NEWBORN = "newborn"
    KIT = "kit"
    ADOLESCENT = "adolescent"
    YOUNG_ADULT = "young adult"
    ADULT = "adult"
    SENIOR_ADULT = "senior adult"
    SENIOR = "senior"

    def is_baby(self):
        return self in (CatAgeEnum.KIT, CatAgeEnum.NEWBORN)

    def can_have_mate(self):
        return self not in (
            CatAgeEnum.KIT,
            CatAgeEnum.NEWBORN,
            CatAgeEnum.ADOLESCENT,
        )
