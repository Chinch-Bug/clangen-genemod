from __future__ import annotations

from typing import Union

from pydantic import Field, ConfigDict
from pydantic_core import MISSING

from scripts.models.crossclan_rel.involved_cats import InvolvedCatsCrossClanRelEvent
from scripts.models.common.points_of_interest import PointsOfInterestGroup
from scripts.models.text_pool_event.base_text_pool_event import BaseTextPoolEvent


class CrossClanRelSchemaItem(BaseTextPoolEvent):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(
        ...,
        description="Separates the events into their blocks. Generally, the ID is descriptive of the cats included in the event or the general themes of the event.",
    )
    poi: Union[PointsOfInterestGroup, MISSING] = Field(
        MISSING,
        description="The relevant points of interest. Points of Interest never affect outcome.",
    )
    frequency: int = Field(
        ...,
        description="Controls how common an event is. 4 is the most common, 1 is the least.",
        json_schema_extra={
            "default": 4
        },  # Necessary so that JSON Schema still shows a default without making the field optional
    )
    nr_involved_clans: int | MISSING = Field(
        2,
        description="Required number of Clans for the event",
    )
    involved_cats: InvolvedCatsCrossClanRelEvent | MISSING = Field(
        MISSING,
        description="Used to add constraints for the various involved cats.",
    )
