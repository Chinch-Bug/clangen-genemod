# clangen (now with 100% more cat genetics)

### [Discord Server](https://discord.gg/rnFQqyPZ7K) || [Itch.io Page](https://sablesteel.itch.io/clan-gen-fan-edit)
### [Genemod Server](https://discord.gg/t6XqgQ46Jx)

A mod of the Clan-gen fan edit featuring cat genetics that get passed down from cat to cat, among a few little bonuses here and there!

## Description
Fan-edit of the warrior cat clangen game built using Python and Pygame.

## Credits
Original creator: just-some-cat.tumblr.com

Fan-edit creator: SableSteel, and many others

## Downloads
Note: These are developer builds and are not guaranteed to work!
- [Nightly Link](https://nightly.link/Chinch-Bug/clangen-genemod/workflows/build/modded)

## Running from source
> [!WARNING]
> Running the game via poetry is no longer supported. Please use uv instead.

ClanGen uses uv to manage virtual environments. Therefore it is required to install the dependencies and run the game from source without manual tweaking.

### Installing python
> [!NOTE] 
> You no longer need to install Python on your system. uv will automatically install the correct version for you.

### Installing uv
Follow the instructions for installing uv from the official website: https://docs.astral.sh/uv/getting-started/installation/

#### Linux, macOS, WSL
Open a terminal and paste this:
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Then restart your terminal and check if uv is installed by running `uv --version`

#### Windows (Powershell)
Open a PowerShell window (Windows key and then enter `PowerShell`) and paste this:
```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
Then restart your terminal and check if uv is installed by running `uv --version`

### Running the game via the helper scripts
#### Linux, macOS
Double click the `run.sh` script or open it in the terminal via `./run.sh` with the current working directory set to the game's root directory.

#### Windows
Double click the `run.bat` script.

### Running the game via Visual Studio Code
> [!NOTE] 
> uv automatically creates the .venv folder in the root directory of the game, unlike poetry.

First, you need to let uv install the dependencies. To do so, run the following command in the terminal:
```
uv sync
```

After that, ensure that you have the Python extension installed in Visual Studio Code. You can install it from the Extensions tab on the left sidebar. [(or click here)
](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

Then, open the Command Palette (Ctrl+Shift+P) and search for `Python: Select Interpreter`. Select the virtual environment created by uv (it should mention a `.venv` somewhere).

Finally, open the `main.py` file and click the play button in the top right corner to run the game.


## Bug Reporting
We have migrated to GitHub Issues for bug reporting and tracking. We no longer review bug reports from the retired Google Form.

## Contributing
If you'd like to contribute to Clangen, please read our [Contributing guide](https://github.com/ClanGenOfficial/clangen/blob/development/CONTRIBUTING.md).
