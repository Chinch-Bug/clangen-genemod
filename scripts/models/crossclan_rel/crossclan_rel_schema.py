from __future__ import annotations

from typing import List

from pydantic import Field, RootModel

from scripts.models.crossclan_rel.crossclan_rel_schema_item import CrossClanRelSchemaItem


class CrossClanRelSchema(RootModel):
    root: List[CrossClanRelSchemaItem] = Field(
        ...,
        description="Crossclan Rel Events in Genemod.",
        title="Genemod Crossclan Rel Schema",
    )
