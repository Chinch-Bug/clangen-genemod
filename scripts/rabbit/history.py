import random

from scripts.rabbit.skills import SkillPath
from scripts.game_structure.game_essentials import game


class History:
    """
    this class handles the rabbit's history!
    """

    def __init__(
        self,
        beginning=None,
        mentor_influence=None,
        app_ceremony=None,
        lead_ceremony=None,
        possible_history=None,
        died_by=None,
        scar_events=None,
        murder=None,
    ):
        self.beginning = beginning if beginning else {}
        self.mentor_influence = (
            mentor_influence if mentor_influence else {"trait": {}, "skill": {}}
        )
        self.app_ceremony = app_ceremony if app_ceremony else {}
        self.lead_ceremony = lead_ceremony if lead_ceremony else None
        self.possible_history = possible_history if possible_history else {}
        self.died_by = died_by if died_by else []
        self.scar_events = scar_events if scar_events else []
        self.murder = murder if murder else {}

        # fix 'old' history save bugs
        if type(self.mentor_influence["trait"]) is type(None):
            self.mentor_influence["trait"] = {}
        if type(self.mentor_influence["skill"]) is type(None):
            self.mentor_influence["skill"] = {}
        if "mentor" in self.mentor_influence:
            del self.mentor_influence["mentor"]

        """ 
        want save to look like
        {
        "beginning":{
            "clan_born": bool,
            "birth_season": season,
            "age": age,
            "moon": moon
            },
        "mentor_influence":{
            "trait": {
                "mentor_id": {
                    "lawfulness": 0
                    ...
                    "strings": []
                }
            },
            "skill": {
                "mentor_id": {
                    "path": 0,
                    string: []
                }
            }
        "app_ceremony": {
            "honor": honor,
            "graduation_age": age,
            "moon": moon
            },
        "lead_ceremony": full ceremony text,
        "possible_history": {
            "condition name": {
                "involved": ID
                "death_text": text
                "scar_text": text
                },
            "condition name": {
                "involved": ID
                "death_text": text
                "scar_text": text
                },
            },
        "died_by": [
            {
                "involved": ID,
                "text": text,
                "moon": moon
            }
            ],
        "scar_events": [
            {
                'involved': ID,
                'text': text,
                "moon": moon
            },
            {
                'involved': ID,
                "text": text,
                "moon": moon
            }
            ]
        "murder": {
            "is_murderer": [
                    {
                    "victim": ID,
                    "revealed": bool,
                    "moon": moon the murder occurred
                    "revealed_by": ID of the discoverer
                    "revelation_moon": moon the murder was revealed
                    "revelation_text": revealed murder history
                    },
                ]
            "is_victim": [
                    {
                    "murderer": ID,
                    "revealed": bool,
                    "text": same text as the death history for this murder (revealed history)
                    "unrevealed_text": unrevealed death history
                    "moon": moon the murder occurred
                    "revealed_by": ID of the discoverer
                    "revelation_moon": moon the murder was revealed
                    "revelation_text": revealed death history
                    },
                ]
            }
        }
        """

    # ---------------------------------------------------------------------------- #
    #                                   utility                                    #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def check_load(rabbit):
        """
        this checks if the rabbit's history has been loaded and loads it if False
        :param rabbit: rabbit object
        :return:
        """
        if not rabbit.history:
            rabbit.load_history()

    @staticmethod
    def make_dict(rabbit):
        history_dict = {
            "beginning": rabbit.history.beginning,
            "mentor_influence": rabbit.history.mentor_influence,
            "app_ceremony": rabbit.history.app_ceremony,
            "lead_ceremony": rabbit.history.lead_ceremony,
            "possible_history": rabbit.history.possible_history,
            "died_by": rabbit.history.died_by,
            "scar_events": rabbit.history.scar_events,
            "murder": rabbit.history.murder,
        }
        return history_dict

    # ---------------------------------------------------------------------------- #
    #                            adding and removing                               #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def add_beginning(rabbit, clan_born=False):
        """
        adds joining age and moon info to the rabbit's history save
        :param rabbit: rabbit object
        :param clan_born: default False, set True if the rabbit was not born in the Warren
        """
        if not game.warren:
            return
        History.check_load(rabbit)

        rabbit.history.beginning = {
            "clan_born": clan_born,
            "birth_season": game.warren.current_season if clan_born else None,
            "age": rabbit.moons,
            "moon": game.warren.age,
        }

    @staticmethod
    def add_mentor_facet_influence_strings(rabbit):
        """
        adds mentor influence to the rabbit's history save
        :param rabbit: rabbit object
        """
        History.check_load(rabbit)

        if not rabbit.history.mentor_influence["trait"]:
            return

        if (
            "Benevolent" or "Abrasive" or "Reserved" or "Outgoing"
        ) in rabbit.history.mentor_influence["trait"]:
            rabbit.history.mentor_influence["trait"] = None
            return

        # working under the impression that these blurbs will be preceded by "more likely to"
        facet_influence_text = {
            "lawfulness_raise": [
                "follow rules",
                "follow the status quo",
                "heed {PRONOUN/m_c/poss} inner compass",
                "have strong inner morals",
            ],
            "lawfulness_lower": [
                "bend the rules",
                "break away from the status quo",
                "break rules that don't suit {PRONOUN/m_c/object}",
                "make {PRONOUN/m_c/poss} own rules",
            ],
            "sociability_raise": [
                "be friendly towards others",
                "step out of {PRONOUN/m_c/poss} comfort zone",
                "interact with others",
                "put others at ease",
            ],
            "sociability_lower": [
                "be cold towards others",
                "refrain from socializing",
                "bicker with others",
            ],
            "aggression_raise": [
                "be ready for a fight",
                "start a fight",
                "defend {PRONOUN/m_c/poss} beliefs",
                "use teeth and claws over words",
                "resort to violence",
            ],
            "aggression_lower": [
                "be slow to anger",
                "avoid a fight",
                "use words over teeth and claws",
                "try to avoid violence",
            ],
            "stability_raise": [
                "stay collected",
                "think things through",
                "be resilient",
                "have a positive outlook",
                "be consistent",
                "adapt easily",
            ],
            "stability_lower": [
                "behave erratically",
                "make impulsive decisions",
                "have trouble adapting",
                "dwell on things",
            ],
        }

        for _ment in rabbit.history.mentor_influence["trait"]:
            rabbit.history.mentor_influence["trait"][_ment]["strings"] = []
            for _fac in rabbit.history.mentor_influence["trait"][_ment]:
                # Check to make sure nothing weird got in there.
                if _fac in rabbit.personality.facet_types:
                    if rabbit.history.mentor_influence["trait"][_ment][_fac] > 0:
                        rabbit.history.mentor_influence["trait"][_ment]["strings"].append(
                            random.choice(facet_influence_text[_fac + "_raise"])
                        )
                    elif rabbit.history.mentor_influence["trait"][_ment][_fac] < 0:
                        rabbit.history.mentor_influence["trait"][_ment]["strings"].append(
                            random.choice(facet_influence_text[_fac + "_lower"])
                        )

    @staticmethod
    def add_mentor_skill_influence_strings(rabbit):
        """
        adds mentor influence to the rabbit's history save
        :param rabbit: rabbit object
        """
        History.check_load(rabbit)

        if not rabbit.history.mentor_influence["skill"]:
            return

        # working under the impression that these blurbs will be preceded by "become better at"
        skill_influence_text = {
            SkillPath.TEACHER: ["teaching"],
            SkillPath.HUNTER: ["hunting"],
            SkillPath.FIGHTER: ["fighting"],
            SkillPath.RUNNER: ["running"],
            SkillPath.CLIMBER: ["climbing"],
            SkillPath.SWIMMER: ["swimming"],
            SkillPath.SPEAKER: ["arguing"],
            SkillPath.OWSLA: ["resolving arguments"],
            SkillPath.CLEVER: ["solving problems"],
            SkillPath.INSIGHTFUL: ["providing insight"],
            SkillPath.SENSE: ["noticing small details"],
            SkillPath.KIT: ["caring for kits"],
            SkillPath.STORY: ["storytelling"],
            SkillPath.LORE: ["remembering lore"],
            SkillPath.BURROW: ["caring for burrow"],
            SkillPath.HEALER: ["healing"],
            SkillPath.STAR: ["connecting to Inle"],
            SkillPath.OMEN: ["finding omens"],
            SkillPath.DREAM: ["understanding dreams"],
            SkillPath.CLAIRVOYANT: ["predicting the future"],
            SkillPath.PROPHET: ["understanding prophecies"],
            SkillPath.GHOST: ["connecting to the afterlife"],
        }

        for _ment in rabbit.history.mentor_influence["skill"]:
            rabbit.history.mentor_influence["skill"][_ment]["strings"] = []
            for _path in rabbit.history.mentor_influence["skill"][_ment]:
                # Check to make sure nothing weird got in there.
                if _path == "strings":
                    continue

                try:
                    if rabbit.history.mentor_influence["skill"][_ment][_path] > 0:
                        rabbit.history.mentor_influence["skill"][_ment]["strings"].append(
                            random.choice(skill_influence_text[SkillPath[_path]])
                        )
                except KeyError:
                    print("issue", _path)

    @staticmethod
    def add_facet_mentor_influence(rabbit, mentor_id, facet, amount):
        """Adds the history information for a single mentor facet change, that occurs after a patrol."""

        History.check_load(rabbit)
        if mentor_id not in rabbit.history.mentor_influence["trait"]:
            rabbit.history.mentor_influence["trait"][mentor_id] = {}
        if facet not in rabbit.history.mentor_influence["trait"][mentor_id]:
            rabbit.history.mentor_influence["trait"][mentor_id][facet] = 0
        rabbit.history.mentor_influence["trait"][mentor_id][facet] += amount

    @staticmethod
    def add_skill_mentor_influence(rabbit, mentor_id, path, amount):
        """Adds mentor influence on skills"""

        History.check_load(rabbit)

        if not isinstance(path, SkillPath):
            path = SkillPath[path]

        if mentor_id not in rabbit.history.mentor_influence["skill"]:
            rabbit.history.mentor_influence["skill"][mentor_id] = {}
        if path.name not in rabbit.history.mentor_influence["skill"][mentor_id]:
            rabbit.history.mentor_influence["skill"][mentor_id][path.name] = 0
        rabbit.history.mentor_influence["skill"][mentor_id][path.name] += amount

    @staticmethod
    def add_app_ceremony(rabbit, honor):
        """
        adds ceremony honor to the rabbit's history
        :param rabbit: rabbit object
        :param honor: the honor trait given during the rabbit's ceremony
        """
        if not game.warren:
            return
        History.check_load(rabbit)

        rabbit.history.app_ceremony = {
            "honor": honor,
            "graduation_age": rabbit.moons,
            "moon": game.warren.age,
        }

    @staticmethod
    def add_possible_history(
        rabbit,
        condition: str,
        death_text: str = None,
        scar_text: str = None,
        other_cat=None,
    ):
        """
        this adds the possible death/scar to the rabbit's history
        :param rabbit: rabbit object
        :param condition: the condition that is causing the death/scar
        :param death_text: text for death history
        :param scar_text: text for scar history
        :param other_cat: rabbit object of other rabbit involved.
        """
        History.check_load(rabbit)

        # If the condition already exists, we don't want to overwrite it
        if condition in rabbit.history.possible_history:
            if death_text is not None:
                rabbit.history.possible_history[condition]["death_text"] = death_text
            if scar_text is not None:
                rabbit.history.possible_history[condition]["scar_text"] = scar_text
            if other_cat is not None:
                rabbit.history.possible_history[condition]["other_cat"] = other_cat.ID
        else:
            # Use a default is none is provided.
            # Will probably sound weird, but it's better than nothing
            if not death_text:
                if rabbit.status == "chief rabbit":
                    death_text = f"died from an injury or illness ({condition})"
                else:
                    death_text = f"m_c died from an injury or illness ({condition})."
            if not scar_text:
                scar_text = f"m_c was scarred from an injury or illness ({condition})."

            rabbit.history.possible_history[condition] = {
                "death_text": death_text,
                "scar_text": scar_text,
                "other_cat": other_cat.ID if other_cat else None,
            }

    @staticmethod
    def remove_possible_history(rabbit, condition):
        """
        use to remove possible death/scar histories
        :param rabbit: rabbit object
        :param condition: condition linked to the death/scar you're removing
        # :param scar: set True if removing scar
        # :param death: set True if removing death
        """

        History.check_load(rabbit)

        if condition in rabbit.history.possible_history:
            rabbit.history.possible_history.pop(condition)

    @staticmethod
    def add_death(rabbit, death_text, condition=None, other_cat=None):
        """Adds death to rabbit's history. If a condition is passed, it will look into
        possible_history to see if anything is saved there, and, if so, use the text and
        other_cat there (overriding the
        passed death_text and other_cat)."""

        if not game.warren:
            return
        History.check_load(rabbit)

        if other_cat is not None:
            other_cat = other_cat.ID
        if condition in rabbit.history.possible_history:
            if rabbit.history.possible_history[condition]["death_text"]:
                death_text = rabbit.history.possible_history[condition]["death_text"]
            other_cat = rabbit.history.possible_history[condition].get("other_cat")
            rabbit.history.remove_possible_history(rabbit, condition)

        rabbit.history.died_by.append(
            {"involved": other_cat, "text": death_text, "moon": game.warren.age}
        )

    @staticmethod
    def add_scar(rabbit, scar_text, condition=None, other_cat=None):
        if not game.warren:
            return
        History.check_load(rabbit)

        if other_cat is not None:
            other_cat = other_cat.ID
        if condition in rabbit.history.possible_history:
            if rabbit.history.possible_history[condition]["scar_text"]:
                scar_text = rabbit.history.possible_history[condition]["scar_text"]
            other_cat = rabbit.history.possible_history[condition].get("other_cat")
            rabbit.history.remove_possible_history(rabbit, condition)

        rabbit.history.scar_events.append(
            {"involved": other_cat, "text": scar_text, "moon": game.warren.age}
        )

    @staticmethod
    def add_murders(rabbit, other_cat, revealed, text=None, unrevealed_text=None):
        """
        this adds murder info
        :param rabbit: rabbit object (rabbit being murdered)
        :param other_cat: rabbit object (rabbit doing the murdering)
        :param revealed: True or False depending on if the murderer has been revealed to the player
        :param text: event text for the victim's death (should be same as their death history)
        :param unrevealed_text: unrevealed event text for victim's death (not saved in their death history)
        :return:
        """
        if not game.warren:
            return
        History.check_load(rabbit)
        History.check_load(other_cat)
        if "is_murderer" not in other_cat.history.murder:
            other_cat.history.murder["is_murderer"] = []
        if "is_victim" not in rabbit.history.murder:
            rabbit.history.murder["is_victim"] = []

        other_cat.history.murder["is_murderer"].append(
            {"victim": rabbit.ID, "revealed": revealed, "moon": game.warren.age}
        )
        rabbit.history.murder["is_victim"].append(
            {
                "murderer": other_cat.ID,
                "revealed": revealed,
                "text": text,
                "unrevealed_text": unrevealed_text,
                "moon": game.warren.age,
            }
        )

    @staticmethod
    def add_lead_ceremony(rabbit):
        """
        generates and adds lead ceremony to history
        """
        History.check_load(rabbit)

        rabbit.history.lead_ceremony = rabbit.generate_lead_ceremony()

    # ---------------------------------------------------------------------------- #
    #                                 retrieving                                   #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def get_beginning(rabbit):
        """
        returns the beginning info, example of structure:

        "beginning":{
            "clan_born": bool,
            "birth_season": season,
            "age": age,
            "moon": moon
            },

        if beginning info is empty, a NoneType is returned
        :param rabbit: rabbit object
        """
        History.check_load(rabbit)
        return rabbit.history.beginning

    @staticmethod
    def get_mentor_influence(rabbit):
        """
        Returns mentor influence dict, example of structure:

        "mentor_influence":{
            "mentor": ID
            "skill": skill
            "second_skill": second skill
            "trait": {
                "mentor_id":
                    "lawfulness": 0,
                    ...
                    "strings": []
            },
            "skill": skill
        }

        if mentor influence is empty, a NoneType is returned
        """
        History.check_load(rabbit)
        return rabbit.history.mentor_influence

    @staticmethod
    def get_app_ceremony(rabbit):
        """
        Returns app_ceremony dict, example of structure:

        "app_ceremony": {
            "honor": honor,
            "graduation_age": age,
            "moon": moon
            },

        if app_ceremony is empty, a NoneType is returned
        """
        History.check_load(rabbit)
        return rabbit.history.app_ceremony

    @staticmethod
    def get_lead_ceremony(rabbit):
        """
        returns the chief rabbit ceremony text
        :param rabbit: rabbit object
        """
        History.check_load(rabbit)
        if not rabbit.history.lead_ceremony:
            History.add_lead_ceremony(rabbit)
        return str(rabbit.history.lead_ceremony)

    @staticmethod
    def get_possible_history(rabbit, condition=None):
        """
        Returns the requested death/scars dict, example of single event structure:

        {
        "involved": ID
        "death_text": text
        "scar_text": text
        },

        example of multi event structure:

        {
        "condition name": {
            "involved": ID
            "death_text": text
            "scar_text": text
            },
        "condition name": {
            "involved": ID
            "death_text": text
            "scar_text": text
            },
        },

        if possible scar/death is empty, a NoneType is returned
        :param rabbit: rabbit object
        :param condition: which condition that caused the death/scar, default None
        """
        History.check_load(rabbit)

        if condition in rabbit.history.possible_history:
            return rabbit.history.possible_history[condition]
        elif condition:
            return None
        else:
            return rabbit.history.possible_history

    @staticmethod
    def get_death_or_scars(rabbit, death=False, scar=False):
        """
        This returns the death/scar history list for the rabbit.  example of list structure:

        [
            {
                'involved': ID,
                'text': text,
                "moon": moon
            },
            {
                'involved': ID,
                "text": text,
                "moon": moon
            }
            ]

        if scar/death is empty, a NoneType is returned
        :param rabbit: rabbit object
        :param death: request a death, default False
        :param scar: request scars, default False
        """

        History.check_load(rabbit)

        event_type = None
        if scar:
            event_type = "scar_events"
        elif death:
            event_type = "died_by"

        if not event_type:
            print(
                "WARNING: event type was not specified during scar/death history retrieval, "
                "did you remember to set scar or death as True?"
            )
            return

        if event_type == "scar_events":
            return rabbit.history.scar_events
        else:
            return rabbit.history.died_by

    @staticmethod
    def get_murders(rabbit):
        """Returns the rabbit's murder dict. Example return:

        "murder": {
            "is_murderer": [
                    {
                    "victim": ID,
                    "revealed": bool,
                    "moon": moon
                    },
                ]
            "is_victim": [
                    {
                    "murderer": ID,
                    "revealed": bool,
                    "text": same text as the death history for this murder (revealed history)
                    "unrevealed_text": unrevealed death history
                    "moon": moon
                    },
                ]
            }

        if murders is empty, a NoneType is returned
        :param rabbit: rabbit object
        """

        History.check_load(rabbit)

        return rabbit.history.murder

    @staticmethod
    def reveal_murder(rabbit, other_cat, cat_class, victim):
        """Reveals the murder properly in all associated history text.

        :param rabbit: The murderer
        :param other_cat: The rabbit who discovers the truth about the murder
        :param cat_class: The rabbit class
        :param victim: The victim whose murder is being revealed
        """

        victim = cat_class.fetch_cat(victim)
        murder_history = History.get_murders(rabbit)["is_murderer"]
        victim_history = History.get_murders(victim)["is_victim"]

        for murder in murder_history:
            if murder["victim"] == victim.ID:
                murder_index = murder_history.index(murder)
                break

        if murder_history:
            if "is_murderer" in murder_history:
                murder_history = murder_history["is_murderer"][murder_index]
                murder_history["revealed"] = True
                murder_history["revealed_by"] = other_cat.ID if other_cat else None
                murder_history["revelation_moon"] = game.warren.age
                if not other_cat:
                    murder_history[
                        "revelation_text"
                    ] = "The truth of {PRONOUN/m_c/poss} crime against [victim] is known to the Warren."
                else:
                    murder_history[
                        "revelation_text"
                    ] = "The truth of {PRONOUN/m_c/poss} crime against [victim] was discovered by [discoverer]."

                victim_history = victim_history["is_victim"][0]
                victim_history["revealed"] = True
                victim_history["revealed_by"] = other_cat.ID if other_cat else None
                victim_history["revelation_moon"] = game.warren.age
                if not other_cat:
                    victim_history[
                        "revelation_text"
                    ] = "The truth of {PRONOUN/m_c/poss} murder is known to the Warren."
                else:
                    victim_history[
                        "revelation_text"
                    ] = "The truth of {PRONOUN/m_c/poss} murder was discovered by [discoverer]."

                discoverer: str = ""
                if other_cat:
                    discoverer = str(other_cat.name)
                if "clan_discovery" in murder_history:
                    discoverer = game.warren.name + "Warren"

                murder_history["revelation_text"] = murder_history[
                    "revelation_text"
                ].replace("[victim]", str(victim.name))
                murder_history["revelation_text"] = murder_history[
                    "revelation_text"
                ].replace("[discoverer]", discoverer)
                victim_history["revelation_text"] = victim_history[
                    "revelation_text"
                ].replace("[discoverer]", discoverer)
