from __future__ import annotations

from random import sample, choices
from typing import TYPE_CHECKING

from scripts.cat.phenotype import Phenotype
from scripts.cat.enums import CatRank
from scripts.cat.factories.new_cat_factory import NewCatFactory
from scripts.cat.factories.test_cat_factory import TestCatFactory
from scripts.cat.pelts import Pelt
from scripts.config import get_config
from scripts.clan_package.settings import get_clan_setting

if TYPE_CHECKING:
    from scripts.cat.cats import Cat


def create_example_cats(majority_rank: CatRank, rank_weights: dict) -> list[Cat]:
    majority_rank_cats = sample(range(12), 3)
    use_special = get_config("clan_creation.use_special_roller")

    chosen_cats = []
    for cat_index in range(12):
        if cat_index in majority_rank_cats:
            chosen_cats.append(NewCatFactory.create_cat(rank=majority_rank, use_special=use_special))
        else:
            random_rank = choices(
                list(rank_weights.keys()), list(rank_weights.values())
            )[0]
            chosen_cats.append(NewCatFactory.create_cat(rank=random_rank, use_special=use_special))

    return chosen_cats


def create_option_preview_cat(scar: str = None, acc: str = None):
    """
    Creates a cat with the specified scar
    """
    gene_config = get_config("genetics_config")
    gene_config.update(get_config("april_fools_genes"))
    pheno = Phenotype(gene_config, game_setting_get("ban problem genes"))
    pheno.Generator()
    new_cat = TestCatFactory.create_cat(
        loading_cat=True,
        pelt=Pelt(
            phenotype=pheno,
            reverse=False,
            tint="gray",
            scars=[scar] if scar else [],
            adult_sprite=8,
            accessory=[acc] if acc else [],
        ),
    )
    new_cat.age = CatAge.ADULT

    return new_cat
