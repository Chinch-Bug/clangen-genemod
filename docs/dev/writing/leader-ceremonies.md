# Chief rabbit ceremonies

## Guidelines
- If using dialogue quotes, put a `\` before the `"` to allow it to work within a json.
- Event text should be 400 character max, with 250 characters preferred (these counts aren't strict, as pronoun tags do artificially inflate them)
- We have two versions of ceremonies! The Inle and the The Lightless.  Which one is used is determined by where the Warren's dead guide is residing.  Focus on the SC ceremonies, as they'll be seen most often, but when possible try to create The Lightless versions of your SC ceremonies.
    - The Lightless ceremonies are held in `lead_ceremony_df.json`
    - Inle ceremonies are held in `lead_ceremony_sc.json`
- Ceremonies are structured as:
    1. Intro
    2. 9 separate life events
        - If 9 dead rabbits are not available, any excess lives are given by an `Unknown Blessing` event
    3. Outro
- Each life giving event must include a virtue that the life represents.  

### Replacement Text:
| abbreviation | use                                                    |
|--------------|--------------------------------------------------------|
| `c_n`        | warren name                                              |
| `m_c`        | chief rabbit's old name                                      |
| `m_c_star`   | chief rabbits new name                                       |
| `r_c`        | life giver's name                                      |
| `[life_num]` | number of un-assigned lives (use in Unknown Blessings) |
| `[virtue]`   | random virtue chosen from given virtue list            |

***
### Format

#### Outro and Intro events
```py
    "unique ID": {
      "tags": [],
      "lead_trait": [],
      "text": []
    }
```

#### Life Giving events

```py
    "unique ID": {
      "tags": [],
      "lead_trait": [],
      "star_trait": [],
      "rank": [],
      "life_giving": [
        {
          "text": "",
          "virtue": []
        }
      ]
    }
```

#### unique ID: str
> This is the ID needs to be a unique string. Try using ctrl+F to check if the ID you want to use is already in use.  Generally this should contain identifying information about the traits or ranks of the rabbits specified within.

***

#### tags: list[str]
> tags available are:

| tag                  | use                                                                                                                                                                      |
|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `"new_clan"`         | Used for intros and outros of newly created Clans. You can pair this with the guide tag to create events in which the guide rabbit meets the chief rabbit for the first time.     |
| `"guide"`            | To specify that the life giver of the event is the guide.  Keep in mind that, upon warren creation, the guide is the only rabbit available to give lives to the first chief rabbit. |
| `"old_leader"`       | To specify that the life giver of the event is the oldest chief rabbit in Inle.                                                                                            |
| `"unknown_blessing"` | To specify that this life giving event is for anonymous spirits to give un-assigned lives to the chief rabbit.  STAR TRAIT AND RANK CANNOT BE USED IN THESE EVENTS.            |
| `"leader_parent"`    | To specify that the life giver is the parent of the new chief rabbit                                                                                                           |
| `"leader_child"`     | To specify that the life giver is the child of the chief rabbit                                                                                                                |
| `"leader_mate"`      | To specify that the life giver is the mate of the chief rabbit                                                                                                                 |

***

#### lead_trait: list[str]
> A list of traits that the new chief rabbit must have for this event to be available

***

#### star_trait: list[str]
> A list of traits that the life giver must have for this event to be available

***

#### rank: list[str]
> A list of ranks that the life giver's rank must be within for this event to be available

***

#### text: list[str]
> A list of possible outro or intro texts for that event. 

***

#### life_giving: list[dict{str[var]}]
> Each dict within this list is a possible text choice for that event, only one will be chosen from this list.  The virtue list holds possible virtues to be randomly chosen from for the replacement text within that event.
```py
        {
          "text": "",
          "virtue": []
        }
```