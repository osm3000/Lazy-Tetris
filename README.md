# LazyBlocks

**LazyBlocks** is a relaxing, "lazy" version of Tetris built with the [Arcade](https://api.arcade.academy/) Python library.  
This game is designed for a chill, stress-free experience—perfect for winding down and enjoying some casual block stacking.

Video demo
<iframe width="560" height="315" src="https://www.youtube.com/embed/ZoQ6w73rbkY?si=18WG6JvQC-cU3TuX" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## Features

- Classic Tetris gameplay (with a relaxing twist 😉 )
- Simple graphics
- Sound effects for moves, drops, rotations, and row clears
- Undo and helper piece mechanics
- Playable on macOS, Linux, and Windows (Python required)

## Installation

```sh
pip install -r requirements.txt
```

Then run the game with 

```sh
python LazyBlocks.py
```

## Controls
- Left/Right Arrow: Move piece left/right
- Down Arrow: Move piece down
- Up Arrow / A: Rotate piece
- Space: Drop piece instantly
- Tab: Swap with helper piece
- Ctrl+R: Reset game
- Ctrl+Z: Undo last move
- X: Clear full rows (if available)
- Esc: Exit game


## Scores
Scores are saved in scores.csv and the top scores are viewable from the main menu.

# Assets
Game sounds are loaded from the blocks_assets directory.
Make sure this folder is present in the same directory as `LazyBlocks.py`