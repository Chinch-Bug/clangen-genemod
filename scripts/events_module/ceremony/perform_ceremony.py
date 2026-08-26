import logging
import random
from math import floor

import i18n

from scripts.cat.cats import cat_class, Cat
from scripts.cat.enums import CatRank, CatAge
from scripts.cat.skills import SkillPath
from scripts.clan_package.settings import get_clan_setting
from scripts.conditions import (
    medicine_cats_can_cover_clan,
    get_amount_cat_for_one_medic,
)
from scripts.config import get_config
from scripts.events_module.ceremony.generate_normal_ceremony import create_ceremony
from scripts.events_module.event_information import EventInformation
from scripts.game_structure import game, constants
from scripts.game_structure.game import Switch
from scripts.game_structure.game.switches import switch_set_value
from scripts.game_structure.localization import load_lang_resource
from scripts.events_module.text_adjust import (
    event_text_adjust,
)

logger = logging.getLogger(__name__)
disable_random = False


def trigger_ceremony(
    main_cat: Cat, new_rank: CatRank, involved_cats: dict[str, Cat] = None
):
    """
    Triggers the ceremony to occur and initiates the cat's rank change.
    :param main_cat: The cat object receiving the ceremony
    :param new_rank: The CatRank that main_cat is becoming
    :param involved_cats: Dict of cats who are already involved, main_cat does not need to be included here. This is
    just for any specific extra cats. Key is abbreviation and value is cat object.
    """
    # allows cat to receive a congratulatory accessory
    switch_set_value(Switch.ceremony_accessory, True)

    # need the cats name from before they change rank!
    old_name = str(main_cat.name)

    clan = main_cat.status.fetch_clan_object(game.clan)

    # Changing prefix if needed
    if get_clan_setting('modded names') and get_clan_setting('dynamic prefixes'):
        cer_type = 'warrior-elder'
        if new_rank.is_any_apprentice_rank():
            cer_type = 'kit-apprentice'
        elif main_cat.status.rank.is_any_apprentice_rank():
            cer_type = 'apprentice-warrior'
        
        main_cat.name.change_prefix(main_cat.moons, clan.biome, cer_type)

    random_honor = None
    if new_rank in (CatRank.WARRIOR, CatRank.MEDIATOR, CatRank.MEDICINE_CAT, CatRank.QUEEN) and main_cat.status.rank.is_any_apprentice_rank():
        traits = load_lang_resource("events/ceremonies/ceremony_traits.json")
        try:
            random_honor = random.choice(traits[main_cat.personality.trait])
        except KeyError:
            random_honor = i18n.t("defaults.ceremony_honor")

        if get_clan_setting('modded names') and get_clan_setting('new suffixes') and not main_cat.name.specsuffix_hidden:
            main_cat.name.give_suffix(main_cat.skills, main_cat.personality, clan.biome, random_honor)

        main_cat.history.add_app_ceremony(random_honor)

    # applies actual rank change
    current_mentor = Cat.fetch_cat(main_cat.mentor) if main_cat.mentor else None
    lead_retire = main_cat.status.rank == CatRank.LEADER and new_rank == CatRank.ELDER
    main_cat.rank_change(new_rank)
    main_cat.rank_change_traits_skill(current_mentor)

    # now we create the ceremony event for the player to view
    create_ceremony(main_cat=main_cat, old_name=old_name, involved_cats=involved_cats, random_honor=random_honor, lead_retire=lead_retire)


def check_for_ceremony(main_cat: Cat, clan):
    """
    Checks if a cat needs to undergo a ceremony, then handles everything pertaining to that ceremony.
    :param main_cat: The cat object that must be checked for a potential ceremony
    """

    # Protection check, to ensure "None" cats won't cause a crash.
    if not main_cat or main_cat.dead:
        return

    # reset this value so that a cat doesn't get a congratulatory acc event if they don't receive a ceremony
    switch_set_value(Switch.ceremony_accessory, False)

    # game.clan.rank check
    if main_cat.status.rank == CatRank.DEPUTY and clan.deputy is None:
        clan.deputy = main_cat
    if main_cat.status.rank == CatRank.MEDICINE_CAT and clan.medicine_cat is None:
        clan.medicine_cat = main_cat

    # PROMOTE DEPUTY TO LEADER
    if main_cat.status.rank == CatRank.DEPUTY:
        # If a Clan deputy exists, and the leader is dead, outside, or doesn't exist, make the deputy leader.
        if not clan.leader or clan.leader.status.group_ID != clan.group_ID:
            _handle_leader_ceremony(main_cat, clan)
            return

    # CHECK IF A CAT WANTS TO CHANGE INTO A MEDIATOR
    if not disable_random and _adult_becomes_mediator(main_cat):
        return
    elif not disable_random and _adult_becomes_queen(main_cat):
        return
    elif not disable_random and _cat_becomes_healer(main_cat):
        return

    special_can_retire = False
    role_info = get_config("roles")
    retirement_info = get_config("retirement")
    if main_cat.status.rank == CatRank.LEADER:
        special_can_retire = get_clan_setting("leader_retirement") and random.random() < (1/retirement_info["max_leader_retire_chance"])
    if main_cat.status.rank == CatRank.MEDICINE_CAT:
        special_can_retire = get_clan_setting("healer_retirement") and medicine_cats_can_cover_clan(
            Cat.all_cats.values(), get_amount_cat_for_one_medic(), clan=clan.group_ID, exclude=main_cat
        ) and random.random() < (1/retirement_info["max_healer_retire_chance"])
    if main_cat.status.rank == CatRank.MEDIATOR:
        special_can_retire = get_clan_setting("mediator_retirement") and random.random() < (1/retirement_info["max_mediator_retire_chance"])
    if main_cat.status.rank == CatRank.QUEEN:
        special_can_retire = random.random() < (1/retirement_info["max_queen_retire_chance"])
        
    # OLD CAT RETIRE
    if (
        not main_cat.no_retire
        and (main_cat.status.rank in (CatRank.WARRIOR, CatRank.DEPUTY) or special_can_retire)
        and not main_cat.apprentice
        and main_cat.moons >= retirement_info["min_retirement_age"]
    ):
        # There is some variation in the age.
        if main_cat.moons > retirement_info["min_retirement_age"]+25 or not int(
            random.random() * (-0.7 * (main_cat.moons-retirement_info["min_retirement_age"]+115) + 100)
        ):
            if main_cat.status.rank == CatRank.DEPUTY:
                clan.deputy = None
            if main_cat.status.rank == CatRank.LEADER:
                clan.leader = None
            if main_cat.status.rank == CatRank.MEDICINE_CAT:
                clan.remove_med_cat(main_cat)

            trigger_ceremony(main_cat, CatRank.ELDER)
            return

    # BECOME APPRENTICE
    if main_cat.moons == cat_class.age_moons[CatAge.ADOLESCENT][0]:
        if main_cat.status.rank == CatRank.KITTEN:
            # BECOME MEDICINE APPRENTICE
            if _is_suitable_medcat_app(main_cat, clan):
                trigger_ceremony(main_cat, CatRank.MEDICINE_APPRENTICE)
                return
            elif _is_suitable_mediator_app(main_cat, clan):
                trigger_ceremony(main_cat, CatRank.MEDIATOR_APPRENTICE)
                return
            elif _is_suitable_queen_app(main_cat, clan):
                trigger_ceremony(main_cat, CatRank.QUEEN_APPRENTICE)
                return
            else:
                trigger_ceremony(main_cat, CatRank.APPRENTICE)
                return

    # APPRENTICE GRADUATE
    if main_cat.status.rank.is_any_apprentice_rank():
        if get_clan_setting("12_moon_graduation"):
            _ready = main_cat.moons >= 12
        else:
            _ready = (
                main_cat.experience_level not in ["untrained", "learning"]
                and main_cat.moons >= get_config("graduation.min_graduating_age")
            ) or main_cat.moons >= get_config(
                f"graduation.max_apprentice_age.{main_cat.status.rank}"
            )

        if _ready:
            if main_cat.status.rank == CatRank.APPRENTICE:
                trigger_ceremony(main_cat, CatRank.WARRIOR)

            # promote to med cat
            elif main_cat.status.rank == CatRank.MEDICINE_APPRENTICE:
                trigger_ceremony(main_cat, CatRank.MEDICINE_CAT)

            elif main_cat.status.rank == CatRank.MEDIATOR_APPRENTICE:
                trigger_ceremony(main_cat, CatRank.MEDIATOR)

            elif main_cat.status.rank == CatRank.QUEEN_APPRENTICE:
                trigger_ceremony(main_cat, CatRank.QUEEN)


def _rel_deputy_filter(cat_list, leader):
    has_rel = []
    values = {}
    for c in cat_list:
        if c.ID in leader.relationships:
            has_rel.append(c)
            values[c.ID] = leader.relationships[c.ID].respect * 3 + leader.relationships[c.ID].trust * 2 + leader.relationships[c.ID].like + leader.relationships[c.ID].comfort
    if not has_rel:
        return cat_list

    has_rel.sort( reverse=True,
        key=lambda c: leader.relationships[c.ID].respect * 3 + leader.relationships[c.ID].trust * 2 + leader.relationships[c.ID].like + leader.relationships[c.ID].comfort)

    if values[has_rel[0].ID] < 0:
        return cat_list
    for i, c in enumerate(has_rel):
        if i > 5:
            break
        if i <= 5 and values[c.ID] < 0:
            has_rel = has_rel[:i]
            break

    return has_rel[:min(5, len(has_rel))]

def check_and_promote_deputy(clan):
    """
    Checks if a new deputy needs to be appointed, and appoints them if necessary.
    """
    if (
        clan.deputy
        and clan.deputy.status.group_ID == clan.group_ID
        and clan.deputy.status.rank != CatRank.ELDER
    ):
        # don't need a new deputy
        return

    if not get_clan_setting("deputy") and clan == game.clan:
        # player doesn't want us to pick a dep for them
        game.cur_events_list.insert(0, EventInformation(event_text_adjust(Cat, "defaults.warn_no_deputy", clan=clan), clan=clan.group_ID))
        return

    # This determines all the cats who are eligible to be deputy.
    possible_deputies = list(
        filter(
            lambda x: x.status.group_ID == clan.group_ID
            and x.status.rank == CatRank.WARRIOR
            and ([i for i in x.former_apprentices if Cat.all_cats.get(i) and not Cat.all_cats.get(i).status.rank.is_any_apprentice_rank()]),
            Cat.all_cats_list,
        )
    )

    if not possible_deputies:
        possible_deputies = list(
            filter(
                lambda x: x.status.group_ID == clan.group_ID
                and x.status.rank == CatRank.WARRIOR
                and (x.apprentice or x.former_apprentices),
                Cat.all_cats_list))
    if get_clan_setting("rel_deputy") and clan.leader:
        possible_deputies = _rel_deputy_filter(possible_deputies, clan.leader)

    if possible_deputies:
        # from here we must have appropriate deputy choices
        main_cat = random.choice(possible_deputies)
    else:
        # If there are no possible deputies, choose someone else, with special text.
        all_warriors = list(
            filter(
                lambda x: x.status.group_ID == clan.group_ID
                and x.status.rank == CatRank.WARRIOR,
                Cat.all_cats_list,
            )
        )
        if all_warriors:
            if get_clan_setting("rel_deputy") and clan.leader:
                all_warriors = _rel_deputy_filter(all_warriors, clan.leader)
            main_cat = random.choice(all_warriors)
        else:
            # If there are no warriors at all, no one is named deputy.
            game.cur_events_list.append(
                EventInformation(i18n.t("hardcoded.ceremony_deputy_none"), "ceremony", clan=clan.group_ID)
            )
            return

    prev_dep = {"past_deputy": clan.deputy}
    clan.deputy = main_cat
    trigger_ceremony(main_cat, CatRank.DEPUTY, prev_dep)


def _adult_becomes_mediator(cat) -> bool:
    """
    Check if a cat wants to switch from their current role into the role of a mediator
    """
    if get_clan_setting("become_mediator"):
        # Note: These chances are large since it triggers every moon.
        # Checking every moon has the effect giving older cats more chances to become a mediator
        change_chance_per_role = get_config("roles.become_mediator_chances")
        if cat.status.rank in change_chance_per_role and not int(
            random.random() * change_chance_per_role[cat.status.rank]
        ):
            trigger_ceremony(cat, CatRank.MEDIATOR)
            cat.experience = int(cat.experience * 0.75)
            return True

    return False


def _adult_becomes_queen(cat) -> bool:
    """
    Check if a cat wants to switch from their current role into the role of a mediator
    """
    if get_clan_setting("become_queen"):
        # Note: These chances are large since it triggers every moon.
        # Checking every moon has the effect giving older cats more chances to become a mediator
        change_chance_per_role = get_config("roles.become_queen_chances")
        if cat.status.rank in change_chance_per_role and not int(
            random.random() * change_chance_per_role[cat.status.rank]
        ):
            trigger_ceremony(cat, CatRank.QUEEN)
            cat.experience = int(cat.experience * 0.75)
            return True

    return False


def _cat_becomes_healer(cat) -> bool:
    """
    Check if a cat wants to switch from their current role into the role of a mediator
    """
    if get_clan_setting("become_healer"):
        # Note: These chances are large since it triggers every moon.
        # Checking every moon has the effect giving older cats more chances to become a mediator
        change_chance_per_role = get_config("roles.become_healer_chances")
        if cat.status.rank in change_chance_per_role and not int(
            random.random() * change_chance_per_role[cat.status.rank]
        ):
            trigger_ceremony(cat, CatRank.MEDICINE_CAT)
            cat.experience = int(cat.experience * 0.75)
            return True

    return False


def _handle_leader_ceremony(main_cat, clan):
    """
    Handles everything pertaining to a leader ceremony.
    """
    trigger_ceremony(main_cat, CatRank.LEADER)
    main_cat.generate_lead_ceremony()
    clan.deputy = None
    clan.leader = main_cat


def _is_suitable_mediator_app(main_cat: Cat, clan) -> bool:
    """
    Determines whether this cat will become a mediator
    :param main_cat: A kitten preparing for apprenticeship ceremony
    :return: True if the kitten should be a mediator, False otherwise
    """
    # Chance for mediator apprentice
    mediator_list = list(
        filter(
            lambda x: x.status.rank == CatRank.MEDIATOR
            and x.status.group_ID == clan.group_ID,
            Cat.all_cats_list,
        )
    )
    # This checks if at least one mediator already has an apprentice.
    has_mediator_apprentice = False
    for c in mediator_list:
        if c.apprentice:
            has_mediator_apprentice = True
            break
    chance = get_config("roles.mediator_app_chance")
    if main_cat.personality.trait in [
        "charismatic",
        "loving",
        "responsible",
        "wise",
        "thoughtful",
    ]:
        chance = int(chance / 1.5)
    if main_cat.skills.primary.path == SkillPath.MEDIATOR or main_cat.skills.secondary and main_cat.skills.secondary.path == SkillPath.MEDIATOR:
        chance = int(chance / 2)
    if main_cat.is_disabled():
        chance = int(chance / 1.5)
    if chance == 0:
        chance = 1
    # Only become a mediator if there is already one in the clan.
    if (
        mediator_list
        and not has_mediator_apprentice
        and not int(random.random() * chance)
    ):
        return True
    if (
        not mediator_list
        and not int(random.random() * chance * 3)
    ):
        return True
    return False


def _is_suitable_queen_app(main_cat: Cat, clan) -> bool:
    """
    Determines whether this cat will become a queen
    :param main_cat: A kitten preparing for apprenticeship ceremony
    :return: True if the kitten should be a queen, False otherwise
    """
    # Chance for mediator apprentice
    queen_list = list(
        filter(
            lambda x: x.status.rank == CatRank.QUEEN
            and x.status.group_ID == clan.group_ID,
            Cat.all_cats_list,
        )
    )
    # This checks if at least one mediator already has an apprentice.
    has_queen_apprentice = False
    for c in queen_list:
        if c.apprentice:
            has_queen_apprentice = True
            break
    chance = get_config("roles.queen_app_chance")
    if main_cat.personality.trait in [
        "childish",
        "playful",
        "compassionate",
        "thoughtful",
        "calm",
        "responsible",
    ]:
        chance = int(chance / 1.5)
    if main_cat.skills.primary.path == SkillPath.KIT or main_cat.skills.secondary and main_cat.skills.secondary.path == SkillPath.KIT:
        chance = int(chance / 2)
    if main_cat.is_disabled():
        chance = int(chance / 1.5)
    if chance == 0:
        chance = 1
    # Only become a queen if there is already one in the clan.
    if (
        queen_list
        and not has_queen_apprentice
        and not int(random.random() * chance)
    ):
        return True
    if (
        not queen_list
        and not int(random.random() * chance * 3)
    ):
        return True
    return False


def _is_suitable_medcat_app(cat, clan) -> bool:
    """
    Determines whether this cat will become a medicine cat
    :param cat: A kitten preparing for apprenticeship ceremony
    :return: True if the kitten should be a medcat, False otherwise
    """
    # assign chance to become med app depending on current med cat and traits
    chance = get_config("roles.base_medicine_app_chance")  # 41
    logger.info("Medcat app %s starting chance: %d", str(cat.name), chance)

    med_cat_list = [
        i
        for i in Cat.all_cats_list
        if i.status.rank.is_any_medicine_rank() and i.status.group_ID == clan.group_ID
    ]

    num_medcats = len(med_cat_list)

    # get number of medcat apps
    num_med_apps = len(
        [cat.status.rank == CatRank.MEDICINE_APPRENTICE for cat in med_cat_list]
    )
    logger.debug("Current number of medcats: %d", num_medcats - num_med_apps)
    logger.debug("Current number of medcat apps: %d", num_med_apps)

    # check if the Clan has sufficient med cats
    enough_working_meds = medicine_cats_can_cover_clan(
        Cat.all_cats.values(),
        amount_per_med=get_amount_cat_for_one_medic(), 
        clan=clan.group_ID,
    )

    med_info = get_config("roles.medicine cat apprentice")
    if (
        floor(num_med_apps / max(1, (len(med_cat_list) - num_med_apps)))
        > med_info["max_medcats_to_apps"]
    ):
        if enough_working_meds:
            # early return if the ratio of apps would be too high
            logger.info("Too many apprentices for medcat population. Aborting.")
            return False
        logger.debug(
            "Too many apprentices for medcat population, but not enough medicine cats for Clan! Continuing."
        )

    # check if the medicine cats are old
    senior_meds = [
        c
        for c in med_cat_list
        if c.age == "senior" and c.status.rank == CatRank.MEDICINE_CAT
    ]

    ancient_meds = [
        c
        for c in senior_meds
        if c.moons
        >= med_info["threshold_moons_ancient"]
    ]

    senior_med_ratio = (len(senior_meds) / num_medcats) if num_medcats != 0 else 0

    ancient_med_ratio = (len(ancient_meds) / num_medcats) if num_medcats != 0 else 0

    if (
        ancient_med_ratio > med_info["threshold_percentage_ancient"] / 100
    ):
        # These chances apply if enough medicine cats are very old.
        if enough_working_meds:
            chance = chance / 3
        else:
            logger.info("Not enough healthy medicine cats")
            chance = chance / 14

        logger.info("Ancient medicine cats, chance updated to %d", round(chance))
    elif (
        senior_med_ratio > med_info["threshold_percentage_seniors"] / 100
    ):
        # These chances apply if enough medicine cats are elders.
        if enough_working_meds:
            chance = chance / 2.22
        else:
            logger.info("Not enough healthy medicine cats")
            chance = chance / 14

        logger.info("Senior medicine cats, chance updated to %d", round(chance))
    else:
        # These chances will only be reached if the
        # Clan has at least one non-elder medicine cat.
        if not enough_working_meds:
            chance = chance / 7.125
            logger.info(
                "Not enough healthy medicine cats, chance updated to %d", chance
            )
        else:
            chance = chance * 2.22
            logger.info(
                "Enough healthy young medicine cats, chance updated to %d", chance
            )

    if cat.personality.trait in [
        "careful",
        "compassionate",
        "loving",
        "wise",
        "faithful",
    ]:
        chance = chance / 1.3
        logger.info("Suitable trait, chance updated to %d", round(chance))

    elif cat.personality.trait in [
        "adventurous",
        "arrogant",
        "bold",
        "bloodthirsty",
        "cold",
        "fierce",
        "rebellious",
        "troublesome",
        "vengeful",
    ]:
        chance = chance * 2
        logger.info("Unsuitable trait, chance updated to %d", round(chance))

    beneficial_skills = [
        SkillPath.OMEN,
        SkillPath.PROPHET,
        SkillPath.HEALER,
        SkillPath.STAR,
        SkillPath.DREAM,
        SkillPath.CLAIRVOYANT,
        SkillPath.GHOST,
        SkillPath.CAMP,
    ]

    if cat.skills.primary.path in beneficial_skills:
        chance = chance / 2
        logger.info("beneficial primary skill, chance updated to %d", round(chance))

    if cat.skills.secondary and cat.skills.secondary.path in beneficial_skills:
        chance = chance / 2
        logger.info("beneficial secondary skill, chance updated to %d", round(chance))

    if cat.is_disabled():
        chance = chance / 1.5

    if num_med_apps == 0:
        # if there are no apprentices at all, make it slightly easier to get one
        logger.info("No apprentices at all")
        chance = chance / 1.8
        logger.info("No medcat apprentices at all, chance updated to %d", chance)
    if num_med_apps > 1:
        # if there's already at least one medcat app, make it harder to get another
        chance = chance * (1 + (0.2 * (num_med_apps - 1)))
        logger.info("%d medcat apps, chance updated to %d", num_med_apps, chance)

    chance = max(1, int(chance))

    success = not int(random.random() * chance)
    logger.info("%s final chance: %d | SUCCESS: %s", cat.name, chance, success)
    return success
