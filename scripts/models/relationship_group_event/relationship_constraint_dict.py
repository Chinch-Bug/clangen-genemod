from typing import List

from pydantic import Field

from scripts.models.relationship_group_event.cat_enums import GroupEventCatEnum
from scripts.models.text_pool_event.relationship_constraint_dict import (
    RelationshipConstraint,
)


class GroupEventRelationshipConstraint(RelationshipConstraint):
    cats_from: List[GroupEventCatEnum] = Field(
        ...,
        description="The cat from whom the relationship originates.",
    )
    cats_to: List[GroupEventCatEnum] = Field(
        ...,
        description="The target of the relationship.",
    )
