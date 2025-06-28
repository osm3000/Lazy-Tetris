"""LazyBlocks game implementation using Arcade library."""

import math
import random
from dataclasses import dataclass
from typing import Optional
import arcade
from arcade.gui import UIAnchorLayout, UIManager, UITextureButton, UIView
import arcade.gui
import pandas as pd
import atexit
import uuid

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800


PLAY_WIDTH = 300
PLAY_HEIGHT = 600


SCREEN_TITLE = "LazyBlocks Game"
GRID_SIZE = 30
GRID_WIDTH = PLAY_WIDTH // GRID_SIZE
GRID_HEIGHT = PLAY_HEIGHT // GRID_SIZE
SHAPES = [
    [[1, 1, 1, 1]],  # I shape
    [[1, 1], [1, 1]],  # O shape
    [[0, 1, 0], [1, 1, 1]],  # T shape
    [[0, 1, 1], [1, 1, 0]],  # S shape
    [[1, 1, 0], [0, 1, 1]],  # Z shape
    [[1, 0], [1, 0], [1, 1]],  # J shape
    [[0, 1], [0, 1], [1, 1]],  # L shape
]

TINY_GRID_SIZE = 20
NEXT_PIECE_WINDOW_WIDTH = TINY_GRID_SIZE * 4
NEXT_PIECE_WINDOW_HEIGHT = TINY_GRID_SIZE * 4

STATUS_BAR_HEIGHT = GRID_SIZE * 2

FILLED_COLOR = arcade.color.BLACK
BORDER_COLOR = arcade.color.WHITE
BACKGROUND_COLOR = arcade.color.DARK_BLUE_GRAY
EMPTY_CELL_COLOR = arcade.color.GRAY


@dataclass
class CellContent:
    """Class to represent the content of a cell in the grid."""

    value: int
    color: str
    shape_cnt: int
    orig_shape_idx: Optional[int] = (
        None  # Index of the orignal shape, necessary to implement the "undo" feature
    )


def draw_grid(
    grid: list[list[CellContent]],
    grid_height: int,
    grid_width: int,
    offset_x: int = 0,
    offset_y: int = 0,
):
    assert grid_height > 0 and grid_width > 0
    assert isinstance(grid, list) and all(isinstance(row, list) for row in grid)
    assert len(grid) == grid_height
    assert all(len(row) == grid_width for row in grid)

    for y in range(grid_height):
        for x in range(grid_width):
            arcade.draw_lbwh_rectangle_filled(
                x * GRID_SIZE + offset_x,
                y * GRID_SIZE + offset_y,
                GRID_SIZE,
                GRID_SIZE,
                grid[y][x].color,
            )
            arcade.draw_lbwh_rectangle_outline(
                x * GRID_SIZE + offset_x,
                y * GRID_SIZE + offset_y,
                GRID_SIZE,
                GRID_SIZE,
                BORDER_COLOR,
            )


class LazyBlocks(arcade.View):
    def __init__(self):
        # super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        super().__init__()

        self.grid: list[list[CellContent]] = [
            [CellContent(value=0, color=EMPTY_CELL_COLOR, shape_cnt=-1)] * GRID_WIDTH
            for _ in range(GRID_HEIGHT)
        ]
        self.current_shape = None
        self.current_position = (0, 0)
        self.game_over = False
        self.score = 0
        self.current_shape_color = None

        # Initialize Arcade
        self.all_pieces_colors = [
            arcade.color.RED,
            arcade.color.GREEN,
            arcade.color.BLUE,
            arcade.color.YELLOW,
            arcade.color.PURPLE,
            arcade.color.ORANGE,
            arcade.color.CYAN,
        ]

        # Load the game assets
        self.move_piece_sound = arcade.load_sound("./blocks_assets/move_piece.wav")
        self.drop_piece_sound = arcade.load_sound("./blocks_assets/drop_piece.wav")
        self.rotate_piece_sound = arcade.load_sound("./blocks_assets/rotate_piece.wav")
        self.clear_row_sound = arcade.load_sound("./blocks_assets/clear_full_row.wav")
        self.switch_pieces_sound = arcade.load_sound(
            "./blocks_assets/switch_pieces.wav"
        )

        # Setup the background color to yellow
        arcade.set_background_color(BACKGROUND_COLOR)
        self.left_key_pressed = False
        self.right_key_pressed = False
        self.down_key_pressed = False
        self.rot_key_pressed = False
        self.up_key_pressed = False
        self.space_key_pressed = False
        self.swap_pieces_pressed = False
        self.current_shape_color = None
        self.is_there_row_to_clear = False
        self.helper_piece_idx = None
        self.helper_piece_shape = None
        self.shapes_cnt = -1

        self.game_id = None

        self.setup()

    def setup(self):
        """Set up the game and initialize variables."""
        # Reset the game state
        self.grid: list[list[CellContent]] = [
            [CellContent(value=0, color=EMPTY_CELL_COLOR, shape_cnt=-1)] * GRID_WIDTH
            for _ in range(GRID_HEIGHT)
        ]
        self.current_shape = None
        self.current_position = (0, 0)
        self.game_over = False
        self.score = 0
        self.left_key_pressed = False
        self.right_key_pressed = False
        self.down_key_pressed = False
        self.rot_key_pressed = False
        self.up_key_pressed = False
        self.space_key_pressed = False
        self.swap_pieces_pressed = False
        self.current_shape_color = None
        self.next_shape = None
        self.is_there_row_to_clear = False
        self.current_shape_idx = None
        self.next_shape_idx = None
        self.helper_piece_idx = None
        self.shapes_cnt = -1
        # 'Next piece' grid setup
        self.next_piece_grid = [
            [0] * (NEXT_PIECE_WINDOW_WIDTH // GRID_SIZE)
            for _ in range(NEXT_PIECE_WINDOW_HEIGHT // GRID_SIZE)
        ]

        # Spawn the first shape
        self.spawn_new_shape()

        # Score text setup, at the top of the screen
        self.score_text = arcade.Text(
            f"Score: {self.score}",
            x=10,
            y=SCREEN_HEIGHT - (STATUS_BAR_HEIGHT // 2),
            color=arcade.color.WHITE,
            font_size=20,
        )

        # Assign a random game ID (UUID4)
        self.game_id = str(uuid.uuid4())

    def spawn_new_shape(self):
        """Spawn a new shape at the top of the grid."""
        global SHAPES
        self.current_shape_idx = (
            random.randint(0, len(SHAPES) - 1)
            if self.next_shape_idx is None
            else self.next_shape_idx
        )
        self.current_shape = SHAPES[self.current_shape_idx]

        # Generate the helper shape
        self.helper_piece_idx = random.randint(0, len(SHAPES) - 1)
        self.helper_piece_shape = SHAPES[self.helper_piece_idx]

        # Generate the next shape
        self.next_shape_idx = random.randint(0, len(SHAPES) - 1)
        self.next_shape = SHAPES[self.next_shape_idx]

        self.current_position = (
            GRID_WIDTH // 2 - len(self.current_shape[0]) // 2,
            GRID_HEIGHT - 1,
            # GRID_HEIGHT - len(self.current_shape) - 1,
            # GRID_HEIGHT - 2,
        )
        self.current_shape_color = self.all_pieces_colors[self.current_shape_idx]
        if not self.can_be_placed(self.current_shape, self.current_position):
            self.game_over = True
            print(" ---- Game Over! Your score:", self.score)

        assert isinstance(self.current_shape_idx, int)
        assert isinstance(self.next_shape_idx, int)

    def swap_current_and_helper(self):
        """
        Swap the current and the helper shapes
        """
        (
            self.current_shape_idx,
            self.current_shape,
            self.helper_piece_idx,
            self.helper_piece_shape,
        ) = (
            self.helper_piece_idx,
            self.helper_piece_shape,
            self.current_shape_idx,
            self.current_shape,
        )

        # Update the colors
        # TODO: Find a consistent way to do this
        self.current_shape_color = self.all_pieces_colors[self.current_shape_idx]

        # Put the shape in the starting position
        self.current_position = (
            GRID_WIDTH // 2 - len(self.current_shape[0]) // 2,
            GRID_HEIGHT - 1,
        )

    def can_be_placed(self, shape: list[list[int]], position: list[int]):
        """Check if the shape can be placed at the given position."""
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_x = position[0] + x
                    grid_y = position[1] - y
                    if (
                        grid_x < 0
                        or grid_x >= GRID_WIDTH
                        or grid_y < 0
                        or grid_y >= GRID_HEIGHT
                        or self.grid[grid_y][grid_x].value != 0
                    ):
                        return False
        return True

    def on_draw(self):
        # Clear the screen
        self.clear()

        ############################################
        # Draw the main grid
        ############################################
        draw_grid(self.grid, GRID_HEIGHT, GRID_WIDTH, offset_x=0, offset_y=0)
        ############################################
        # Draw the current shape, on the main grid
        ############################################
        if self.current_shape:
            for y, row in enumerate(self.current_shape):
                for x, cell in enumerate(row):
                    if cell:
                        arcade.draw_lbwh_rectangle_filled(
                            (self.current_position[0] + x) * GRID_SIZE,
                            (self.current_position[1] - y) * GRID_SIZE,
                            GRID_SIZE,
                            GRID_SIZE,
                            self.current_shape_color,
                        )

                        # Draw outline for the blocks of the current shape
                        arcade.draw_lbwh_rectangle_outline(
                            (self.current_position[0] + x) * GRID_SIZE,
                            (self.current_position[1] - y) * GRID_SIZE,
                            GRID_SIZE,
                            GRID_SIZE,
                            BORDER_COLOR,
                        )
        ############################################
        # Draw the next piece on the right side of the screen
        ############################################
        if self.next_shape:
            next_piece_x = SCREEN_WIDTH - NEXT_PIECE_WINDOW_WIDTH - 20
            next_piece_y = (
                SCREEN_HEIGHT - NEXT_PIECE_WINDOW_HEIGHT - 20 - STATUS_BAR_HEIGHT
            )
            # Draw the grid for the next piece window (outlined grid)
            for y in range(NEXT_PIECE_WINDOW_HEIGHT // TINY_GRID_SIZE):
                for x in range(NEXT_PIECE_WINDOW_WIDTH // TINY_GRID_SIZE):
                    arcade.draw_lbwh_rectangle_outline(
                        next_piece_x + x * TINY_GRID_SIZE,
                        (next_piece_y + y * TINY_GRID_SIZE),
                        TINY_GRID_SIZE,
                        TINY_GRID_SIZE,
                        arcade.color.BLACK,
                    )

            # Draw the next piece
            for y, row in enumerate(self.next_shape):
                for x, cell in enumerate(row):
                    if cell:
                        arcade.draw_lbwh_rectangle_filled(
                            next_piece_x + x * TINY_GRID_SIZE,
                            next_piece_y
                            + (len(self.next_shape) - 1 - y) * TINY_GRID_SIZE,
                            TINY_GRID_SIZE,
                            TINY_GRID_SIZE,
                            self.all_pieces_colors[self.next_shape_idx],
                        )
                        # Draw outline for the blocks of the next piece
                        arcade.draw_lbwh_rectangle_outline(
                            next_piece_x + x * TINY_GRID_SIZE,
                            next_piece_y
                            + (len(self.next_shape) - 1 - y) * TINY_GRID_SIZE,
                            TINY_GRID_SIZE,
                            TINY_GRID_SIZE,
                            arcade.color.BLACK,
                        )

        ############################################
        # Draw the helper piece on the right side of the screen
        ############################################
        if self.helper_piece_shape:
            helper_piece_x = SCREEN_WIDTH - NEXT_PIECE_WINDOW_WIDTH - 20
            helper_piece_y = SCREEN_HEIGHT - NEXT_PIECE_WINDOW_HEIGHT - 200
            # Draw the grid for the next piece window (outlined grid)
            for y in range(NEXT_PIECE_WINDOW_HEIGHT // TINY_GRID_SIZE):
                for x in range(NEXT_PIECE_WINDOW_WIDTH // TINY_GRID_SIZE):
                    arcade.draw_lbwh_rectangle_outline(
                        helper_piece_x + x * TINY_GRID_SIZE,
                        helper_piece_y + y * TINY_GRID_SIZE,
                        TINY_GRID_SIZE,
                        TINY_GRID_SIZE,
                        arcade.color.BLACK,
                    )

            # Draw the next piece
            for y, row in enumerate(self.helper_piece_shape):
                for x, cell in enumerate(row):
                    if cell:
                        arcade.draw_lbwh_rectangle_filled(
                            helper_piece_x + x * TINY_GRID_SIZE,
                            helper_piece_y
                            + (len(self.helper_piece_shape) - 1 - y) * TINY_GRID_SIZE,
                            TINY_GRID_SIZE,
                            TINY_GRID_SIZE,
                            self.all_pieces_colors[self.helper_piece_idx],
                        )
                        # Draw outline for the blocks of the next piece
                        arcade.draw_lbwh_rectangle_outline(
                            helper_piece_x + x * TINY_GRID_SIZE,
                            helper_piece_y
                            + (len(self.helper_piece_shape) - 1 - y) * TINY_GRID_SIZE,
                            TINY_GRID_SIZE,
                            TINY_GRID_SIZE,
                            arcade.color.BLACK,
                        )

        ############################################
        # Draw the score text at the top of the screen inside a black rectangle
        ############################################
        arcade.draw_lbwh_rectangle_filled(
            0,
            SCREEN_HEIGHT - STATUS_BAR_HEIGHT,
            SCREEN_WIDTH,
            STATUS_BAR_HEIGHT,
            arcade.color.BLACK,
        )
        if self.game_over:
            self.score_text.text = f"Game Over! Final Score: {self.score}"
            self.score_text.color = arcade.color.RED
        else:
            self.score_text.text = f"Score: {self.score}"
            self.score_text.color = arcade.color.WHITE
        self.score_text.draw()

    def on_update(self, delta_time):
        """Update the game state."""
        if self.game_over:
            return

        placement_took_place = False
        piece_rotated = False

        # Handle key presses for moving the shape
        if self.left_key_pressed and self.can_be_placed(
            self.current_shape, (self.current_position[0] - 1, self.current_position[1])
        ):
            self.current_position = (
                self.current_position[0] - 1,
                self.current_position[1],
            )
            placement_took_place = True
        if self.right_key_pressed and self.can_be_placed(
            self.current_shape, (self.current_position[0] + 1, self.current_position[1])
        ):
            self.current_position = (
                self.current_position[0] + 1,
                self.current_position[1],
            )
            placement_took_place = True
        if self.down_key_pressed and self.can_be_placed(
            self.current_shape, (self.current_position[0], self.current_position[1] - 1)
        ):
            self.current_position = (
                self.current_position[0],
                self.current_position[1] - 1,
            )
            placement_took_place = True

        if self.rot_key_pressed:
            # Rotate the shape
            rotated_shape = [list(row) for row in zip(*self.current_shape[::-1])]
            if self.can_be_placed(rotated_shape, self.current_position):
                self.current_shape = rotated_shape
                piece_rotated = True

        if self.space_key_pressed:
            piece_dropped = True

        # Sound effects
        if placement_took_place:
            arcade.play_sound(self.move_piece_sound)
        elif piece_rotated:
            arcade.play_sound(self.rotate_piece_sound)

    def on_key_press(self, key, modifiers):
        """Handle key presses for moving and rotating the shape."""
        # Detect if ctrl + R is pressed to reset the game
        if key == arcade.key.R and modifiers & arcade.key.MOD_CTRL:
            """Reset the game."""
            self.setup()
            print("Game reset!")

        if self.game_over:
            return

        if key == arcade.key.LEFT:
            self.left_key_pressed = True
        elif key == arcade.key.RIGHT:
            self.right_key_pressed = True
        elif key == arcade.key.DOWN:
            self.down_key_pressed = True
            # print("down key pressed")
        elif key == arcade.key.UP:
            # self.up_key_pressed = True
            self.rot_key_pressed = True
        elif key == arcade.key.A:
            self.rot_key_pressed = True
        elif key == arcade.key.SPACE:
            self.space_key_pressed = True
            self.place_piece_on_grid()
            # Spawn a new shape
            self.spawn_new_shape()
        elif key == arcade.key.TAB:
            self.swap_pieces_pressed = True
            self.switch_pieces_sound.play()

        elif key == arcade.key.ESCAPE:
            """Exit the game."""
            arcade.close_window()
        elif key == arcade.key.X:
            # If there is a row to clear, clear it
            self.clear_full_rows()

        elif key == arcade.key.Z and modifiers and arcade.key.MOD_CTRL:
            """Undo the previous move."""
            if self.shapes_cnt > -1:
                self.undo_prev_move()
                # Spawn a new shape
                self.spawn_new_shape()
                print("Undo last move")
            else:
                print("There is nothing I can undo")

    def undo_prev_move(self):
        """
        Starting from the current self.shapes_cnt, keep removing pieces, until either there is no more piece to move, or there is a diff of more than 1 with the last piece
        Then set the next piece to that shape index, and issue a spawn new piece
        """
        # if self.shapes_cnt < 0:
        #     print("No pieces to undo")
        #     return

        for row_idx, row in enumerate(self.grid):
            for col_idx, cell in enumerate(row):
                if cell.shape_cnt == self.shapes_cnt:
                    print("One cell to undo")
                    # Assign the next shape index to the current shape index
                    self.next_shape_idx = cell.orig_shape_idx
                    # Remove the piece from the grid
                    self.grid[row_idx][col_idx] = CellContent(
                        value=0, color=EMPTY_CELL_COLOR, shape_cnt=-1
                    )
        print("-------------------")
        # Decrease the shapes count
        self.shapes_cnt -= 1

    def place_piece_on_grid(self):
        # Drop the shape immediately
        while self.can_be_placed(
            self.current_shape,
            (self.current_position[0], self.current_position[1] - 1),
        ):
            self.current_position = (
                self.current_position[0],
                self.current_position[1] - 1,
            )
        # Play the drop sound
        arcade.play_sound(self.drop_piece_sound)
        # Place the shape on the grid
        self.shapes_cnt += 1
        for y, row in enumerate(self.current_shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_x = self.current_position[0] + x
                    grid_y = self.current_position[1] - y
                    if grid_y >= 0:
                        self.grid[grid_y][grid_x] = CellContent(
                            value=1,
                            color=self.current_shape_color,
                            shape_cnt=self.shapes_cnt,
                            orig_shape_idx=self.current_shape_idx,
                        )

    def clear_full_rows(self):
        """Clear full rows and update the score."""
        all_clear = False
        while not all_clear:
            all_clear = True
            for y in range(GRID_HEIGHT):
                if all([item.value for item in self.grid[y]]):
                    # Clear the row
                    del self.grid[y]
                    self.grid.append(
                        [
                            CellContent(
                                value=0,
                                color=EMPTY_CELL_COLOR,
                                shape_cnt=-1,
                                orig_shape_idx=None,
                            )
                        ]
                        * GRID_WIDTH
                    )
                    self.score += 1
                    all_clear = False
                    # Play the sound for clearing a row
                    arcade.play_sound(self.clear_row_sound)
                    # Store the scores in the CSV file
                    self.store_scores()
                    break
        print("Score:", self.score)

    def on_key_release(self, key, modifiers):
        """Handle key releases."""
        if key == arcade.key.LEFT:
            self.left_key_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_key_pressed = False
        elif key == arcade.key.DOWN:
            self.down_key_pressed = False
        elif key == arcade.key.UP:
            # self.up_key_pressed = False
            self.rot_key_pressed = False
        elif key == arcade.key.A:
            self.rot_key_pressed = False
        elif key == arcade.key.SPACE:
            self.space_key_pressed = False
        elif key == arcade.key.ESCAPE:
            """Exit the game."""
            arcade.close_window()
        elif key == arcade.key.TAB:
            self.swap_current_and_helper()

    def store_scores(self):
        """
        Store the scores in a CSV file in the format:
        Date, Player, GameID, Score.
        """
        scores_file = "scores.csv"
        # Prepare the data to be written
        data = {
            "date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "player": "Player",  # Placeholder for player name
            "gameid": self.game_id,
            "score": self.score,
        }
        # Read the existing scores from the CSV file
        df: pd.DataFrame = pd.DataFrame()
        try:
            df = pd.read_csv(scores_file)
        except FileNotFoundError:
            df = pd.DataFrame(columns=["date", "player", "gameid", "score"])

        # Check if the game ID already exists. If it does, update the score. If it doesn't, append the new score.
        if data["gameid"] in df["gameid"].values:
            df.loc[df["gameid"] == data["gameid"], "score"] = data["score"]
        else:
            df = pd.concat(
                [df, pd.DataFrame([data])],
                ignore_index=True,
            )

        # Store the updated scores back to the CSV file
        df.to_csv(scores_file, index=False)        

class Leaderboard(arcade.View):
    """View to display the leaderboard."""

    def __init__(self):
        super().__init__()
        self.manager = UIManager()
        self.leaderboard_data = self.load_leaderboard_data()

        # Create a button to go back to the main menu
        back_button = arcade.gui.UIFlatButton(text="Back to Menu", width=200)

        @back_button.event("on_click")
        def on_back_button_click(event):
            game_window.show_view(game_settings_view)

        self.anchor = self.manager.add(UIAnchorLayout())
        self.anchor.add(
            child=back_button, anchor_x="center_x", anchor_y="bottom"
        )

    def load_leaderboard_data(self):
        """Load the leaderboard data from the CSV file."""
        try:
            df = pd.read_csv("scores.csv")
            return df.sort_values(by="score", ascending=False).head(10)
        except FileNotFoundError:
            return pd.DataFrame(columns=["date", "player", "gameid", "score"])

    def on_show_view(self):
        """This is run once when we switch to this view"""
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)
        self.manager.enable()

    def on_draw(self):
        """Render the screen."""
        self.clear()
        self.manager.draw()

class GameSettings(arcade.View):
    """Main application class."""

    def __init__(self, game_view):

        super().__init__()

        self.manager = arcade.gui.UIManager()
        self.game_view = game_view

        switch_menu_button = arcade.gui.UIFlatButton(text="Pause", width=250)

        # Make a list of all the buttons
        start_new_game_btn = arcade.gui.UIFlatButton(text="Let's go?", width=150)
        leaderboard_btn = arcade.gui.UIFlatButton(text="Top score so far", width=150)
        credit_btn = arcade.gui.UIFlatButton(text="Credits", width=150)
        exit_btn = arcade.gui.UIFlatButton(text="Only cowards run away...", width=150)
        view_label = arcade.gui.UILabel(
            text="I refuse all of it", align="center", width=300, font_size=30
        )

        @start_new_game_btn.event("on_click")
        def on_start_new_game_btn_click(event):
            """Handle the button click event."""
            self.game_view = LazyBlocks()
            game_window.show_view(self.game_view)

        @leaderboard_btn.event("on_click")
        def on_leaderboard_btn_click(event):
            """Handle the button click event."""
            leaderboard_view = Leaderboard()
            game_window.show_view(leaderboard_view)

        @exit_btn.event("on_click")
        def on_exit_btn_click(event):
            arcade.exit()

        self.main_grid_layout = arcade.gui.UIGridLayout(
            column_count=2, row_count=3, horizontal_spacing=20, vertical_spacing=20
        )
        self.main_grid_layout.add(view_label, row=0, column_span=2)
        self.main_grid_layout.add(start_new_game_btn, column=0, row=1)
        self.main_grid_layout.add(leaderboard_btn, column=1, row=1)
        self.main_grid_layout.add(credit_btn, column=0, row=2)
        self.main_grid_layout.add(exit_btn, column=1, row=2)

        self.anchor = self.manager.add(UIAnchorLayout())

        self.anchor.add(
            child=self.main_grid_layout,
            anchor_x="center_x",
            anchor_y="center_y",
        )

    def on_show_view(self):
        """This is run once when we switch to this view"""

        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)

        # Enable the UIManager when the view is shown.
        self.manager.enable()

    def on_draw(self):
        """Render the screen."""

        # Clear the screen

        self.clear()

        # Draw the manager
        self.manager.draw()

    def on_hide_view(self):
        # Disable the UIManager when the view is hidden.
        self.manager.disable()


if __name__ == "__main__":
    game_window = arcade.Window(
        width=SCREEN_WIDTH, height=SCREEN_HEIGHT, title=SCREEN_TITLE, resizable=True
    )
    game_window.set_update_rate(1 / 10)  # Set the update rate to 10 FPS
    main_game_view = LazyBlocks()
    main_game_view.setup()

    # game_settings_view = GameSettings(game_view=main_game_view)

    # game_window.show_view(game_settings_view)
    game_window.show_view(main_game_view)
    # Register a function to store the scores when the game exits
    atexit.register(main_game_view.store_scores)

    arcade.set_background_color(BACKGROUND_COLOR)
    arcade.run()
