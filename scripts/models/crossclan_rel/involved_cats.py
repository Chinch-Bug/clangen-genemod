from typing import Union

from pydantic import BaseModel, ConfigDict
from pydantic_core import MISSING

from scripts.models.text_pool_event.cat_dict import CatDict


class InvolvedCatsCrossClanRelEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    m_c: CatDict | MISSING = MISSING
    r_c0: CatDict | MISSING = MISSING
    r_c1: CatDict | MISSING = MISSING
    r_c2: CatDict | MISSING = MISSING
    r_c3: CatDict | MISSING = MISSING
    r_c4: CatDict | MISSING = MISSING
    r_c5: CatDict | MISSING = MISSING
    r_c6: CatDict | MISSING = MISSING
    r_c7: CatDict | MISSING = MISSING
    r_c8: CatDict | MISSING = MISSING
    r_c9: CatDict | MISSING = MISSING
