# Content adding

## Burrow Backgrounds
To make the burrow backgrounds themselves, go to [this page](https://github.com/ClanGenOfficial/clangen/wiki/%5BArt%5D-%E2%80%90-Basic#burrow-bgs). Style guide for burrow backgrounds can be found [here](https://github.com/ClanGenOfficial/clangen/wiki/%5BArt%5D-%E2%80%90-Style-Guides#burrow-bgs-style-guide).

The steps for adding a new burrow background to the game go as following:

1. **Add the burrow image files to the correct folders with the correct names**
2. **Creating and coding in a button to select said burrow in warren creation screen**
3. **Adjusting rabbit sprite & label placements inside the burrow, if needed**

Done! Let's go over those steps now.

### 1. Adding the images

If you've followed the previous guides for burrow background making, you'll know how to name your image files for them. What's left is simply adding them to their correct folders.

Navigate to "resources/images/camp_bg", where each biome has their own folder. Go to whichever biome's folder that you have decided for your burrow.
Then, simply add all of your burrow image files to that folder.

**Note!** Be careful to not replace any existing camps with your own files. You can see what number your burrow should have by looking at the file names in the folder.

![image](https://github.com/ClanGenOfficial/clangen/assets/54122046/36d58d49-ee01-493f-882c-f2af743aff60)

_In the image above, the highest number given for the existing camps is 3, so the number given for your burrow would be 4._

### 2. Adding the Buttons

How to create the button images themselves will be touched up in the burrow backgrounds guide linked above. You can add the completed button images to "resources/images/buttons". They should be named like this:

`[burrow name]_camp.png`

`[burrow name]_camp_hover.png`

`[burrow name]_camp_unavailable.png`

Next, the button will be added into the code in two locations.

In "resources/theme/image_buttons.json", you can find the other biome & burrow buttons by using Ctrl + F and looking for "biome". The burrow buttons code will look something like this;

![image](https://github.com/ClanGenOfficial/clangen/assets/54122046/d5be8704-9d4a-4140-9371-504408b52c5d)

Find the last burrow/biome button code like this and add your own after it.
Format:

```json
"#[your burrow name]_tab": {
    "prototype": "#image_button",
    "images": {
        "normal_image": {
            "path": "resources/images/buttons/[your burrow name]_camp.png"
        },
        "hovered_image": {
            "path": "resources/images/buttons/[your burrow name]_hover.png"
        },
        "selected_image": {
            "path": "resources/images/buttons/[your burrow name]_hover.png"
        },
        "disabled_image": {
            "path": "resources/images/buttons/[your burrow name]_unavailable.png"
        }
    }
},
```

After that, we can go and add the button to the Make Warren Screen. Navigate to "scripts/screens/MakeClanScreen.py". You'll be editing the "refresh_selected_camp", "handle_choose_background_key" and "handle_choose_background" functions. Let's find "refresh_selected_camp" with Ctrl + F by searching for one of the existing burrow names + "_tab". Like: `wasteland_tab`.

Each biome will have an if-statement like this:

![image](https://github.com/ClanGenOfficial/clangen/assets/54122046/7fc5a1f1-7b7a-4da5-a9ee-9569c5c2e8be)

Find which biome your burrow belongs to, and add a new self.tab line of code below the last one. Format:

```py
self.tabs["tab#"] = UIImageButton(scale(pygame.Rect([position], [size])), "", object_id="#[your burrow name]_tab", manager=MANAGER)
```

The [position] and [size] should be replaced with (x,y) coordinates. **Size** is almost always the same: `(308, 60)`. The **position** has a couple of rules however. The x-position is usually a number near 170, but varies depending on how long the name of your burrow is. For example, the "Grasslands" burrow has a long name, so its x-position is 128. The "Cliff" burrow however has a very short name, so the x-position is 222. Test out different lengths and see what fits for your burrow. The y-position meanwhile should always be 70 pixels more than the last burrow tab in your biome. If the last burrow tab y-position is at 500, your y-position should be 570.

Let's next find the "handle_choose_background_event" function. You can find it by tapping Ctrl + F and searching "def handle_choose_background_event". How the next edits will look will depend on the amount of camps in each biome. At the bottom of the function, there is an elif -statement that looks something like this:

![image](https://github.com/ClanGenOfficial/clangen/assets/54122046/1af89cd6-2694-4e60-ae53-e75235e44240)

This is how the "randomize background" button works. It accounts for the number of available camps in each biome, which at the time of taking this screenshot, was 3 camps in each biome except forest, which had 4. Therefore every other biome uses the parameters (1, 4) for the randrange function, while the Forest biome uses (1, 5). Use if-else statements to adjust the number for the number available camps in each biome. Example:

```py
            if self.biome_selected == 'Biome1':
                self.selected_camp_tab = randrange (1, [number of camps in Biome1] + 1)
            elif self.biome_selected == 'Biome2':
                self.selected_camp_tab = randrange (1, [number of camps in Biome2] + 1)
            else:
                self.selected_camp_tab = randrange(1, [number, if the other biomes have the same number of camps] + 1)
```

With that, the buttons for selecting the new burrow should be successfully coded into the game.

### 3. Adjusting Sprite & Label Placements inside Burrow
This step is not mandatory; if the placements are not edited for the burrow, they will be found in their default locations. You probably won't want that for a unique burrow design, though.

Navigate to "resources/placements.json", where each burrow has their rabbit and den label placements written. The default looks like this;

```json
    "default": {
        "chief rabbit den": [688, 200],
        "healer den": [210, 400],
        "nursery": [1240, 400],
        "clearing": [635, 570],
        "rusasi den": [140, 820],
        "rabbit den": [1230, 880],
        "elder den": [696, 980],
        "chief rabbit place": [[[750, 390], "xy"], [[920, 205], "xy"],
                         [[950, 538], "xy"]],
        "healer place": [[[160, 540], "xy"], [[254, 570], "xy"],
                           [[416, 546], "xy"], [[330, 660], "xy"],
                           [[80, 368], "xy"]],
        "nursery place": [[[1170, 600], "xy"], [[1200, 500], "xy"],
                          [[1300, 500], "xy"], [[1070, 600], "xy"],
                          [[1970, 600], "xy"], [[1270, 600], "xy"],
                          [[1370, 600], "xy"], [[1060, 700], "xy"],
                          [[1160, 700], "xy"], [[1260, 700], "xy"],
                          [[1360, 700], "xy"]],
        "clearing place": [[[710, 640], "xy"], [[590, 700], "xy"],
                           [[750, 740], "xy"], [[870, 720], "xy"],
                           [[650, 810], "xy"], [[800, 840], "xy"],
                           [[950, 820], "xy"]],
        "rusasi place": [[[140, 920], "xy"], [[250, 940], "xy"],
                             [[330, 920], "xy"], [[240, 1040], "xy"],
                             [[300, 1020], "xy"], [[70, 990], "xy"]],
        "rabbit place": [[[1260, 980], "xy"], [[1378, 1000], "xy"],
                          [[1480, 1052], "xy"], [[1214, 1050], "xy"],
                          [[1415, 1162], "xy"], [[1310, 1150], "xy"],
                          [[1254, 1100], "xy"], [[1340, 1070], "xy"]],
        "elder place": [[[890, 1140], "xy"], [[700, 1040], "xy"],
                        [[800, 1040], "xy"], [[690, 1140], "xy"],
                        [[790, 1140], "xy"]]
    },
```

Under the default are listed all camps, named in this format: `Biome+burrow#`. You should make a new list like this under the others for your new burrow - be sure to name it using that same format. It's a good idea to copy one of the pre-existing ones to save the effort of rewriting all of that.

The editing process is quite straightforward and simple, although tedious; it involves a lot of testing to see what looks right. You edit the numbers after the "dens" to change the placements of the den labels. To edit the rabbit sprite placements, you edit the numbers in the lists after each "place". You are also able to add (or reduce) rabbit sprite placements by adding `[[number, number], "xy"]` in any of the lists - just be mindful of the right amount of square brackets and correct comma placements.

Few numbers to keep in mind:

- A single rabbit sprite on the burrow screen counts for 100x100 pixels
- Burrow screen length is 1600 pixels. This means that to not have rabbit sprites go behind the screens, their x-coordinate should not be placed beyond 1500 pixels.
- Burrow screen height is 1400 pixels. Like before, the rabbit sprite y-coordinates shouldn't be placed beyond 1300 pixels.

Photo-editing/painting programs may help you figure out the right placements, if they have measuring tools available.

Once this is all finished - your new burrow should now be fully added into the game!

## Accessories

## Attributes