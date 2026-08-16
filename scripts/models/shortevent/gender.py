from enum import Enum


class NewGenderEnum(Enum):
    nonbinary = "nonbinary"
    trans_male = "trans male"
    trans_female = "trans female"
    agender = "agender"


class GenderEnum(Enum):
    male = "male"
    female = "female"
