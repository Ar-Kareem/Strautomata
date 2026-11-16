import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional, Union

import pyspiel
import numpy as np

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled, render_prompt_for_live_play


@dataclass(frozen=True)
class Move:
    row: int
    col: int
    action_str: str


def move_from_llm(move_inp: tuple[int, int]) -> Move:
    row, col = move_inp
    return Move(row, col, f"{chr(ord('a') + col)}{row+1}")


def move_from_openspiel_str(move_str: str) -> Move:
    row = int(move_str[1:]) - 1
    col = ord(move_str[0]) - ord('a')
    return Move(row, col, move_str)


def parse_observation(obs: Any, board_size: int = 11) -> dict[str, Any]:
    """
    Parse OpenSpiel Hex observation_tensor into a compact, human-readable dict,
    using the plane semantics implied by the user's hint:

    0: (rare) terminal/win-marker plane (usually all 0 unless terminal)
    1: white edge-connected (side A)
    2: white edge-connected (side B)
    3: white normal
    4: empty
    5: black normal
    6: black edge-connected (side A)
    7: black edge-connected (side B)
    8: (rare) terminal/win-marker plane (usually all 0 unless terminal)

    Returns only what is typically required to choose the next move:
    - empties (legal placement actions)
    - owners per cell (None/'black'/'white')
    - grid for readable logging
    - edge_connected sets (still readable, often useful for heuristics)
    """
    obs = np.array(obs).reshape(-1, board_size, board_size)
    shp = obs.shape
    if len(shp) != 3 or shp[0] != 9:
        raise ValueError(f"Expected observation shaped (9, rows, cols). Got shape={shp}.")
    planes = obs
    _, R, C = shp
    CH_EMPTY = 4
    # planes 0/8 hold the winning stone(s) once the game is terminal
    CH_WHITE = (0, 1, 2, 3)
    CH_BLACK = (5, 6, 7, 8)
    white: list[tuple[int, int]] = []
    black: list[tuple[int, int]] = []
    for r in range(R):
        for c in range(C):
            ch = max(range(9), key=lambda k: float(planes[k][r][c]))
            if ch in CH_WHITE:
                white.append((r, c))
            elif ch in CH_BLACK:
                black.append((r, c))
    return {
        "black": black,
        "white": white,
    }

class HexGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.turn: int = 0

        self._spiel_game = pyspiel.load_game("hex")
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("Game expects a 2-player OpenSpiel game.")

        self.move_count: int = 0
        self._is_done: bool = False
        self.get_legal_moves()

    def get_observation(self) -> dict[str, Any]:
        turn = self.turn if self.turn >= 0 else 0
        obs = list(self._state.observation_tensor(turn))
        parsed = parse_observation(obs)
        return {
            "me": parsed["black"] if turn == 0 else parsed["white"],
            "opp": parsed["white"] if turn == 0 else parsed["black"],
            "color": "b" if turn == 0 else "w",
        }
    
    def get_fixed_observation(self) -> dict[str, Any]:
        obs = list(self._state.observation_tensor(0))
        parsed = parse_observation(obs, board_size=11)
        return {
            "black": parsed["black"],
            "white": parsed["white"],
            "turn": self.turn,
            "board_size": (11, 11),
            "legal_moves": self.get_legal_moves(),
        }

    def game_step(self, move: Move) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        if move.action_str not in self.legal_moves:
            raise ValueError(f"Invalid or illegal move: '{move.action_str}'. Legal moves: {self.legal_moves}. At move count {self.move_count}, current player is {self.turn}.")
        action = self._state.string_to_action(move.action_str)
        self._state.apply_action(action)
        self.move_count += 1
        self.turn = self._state.current_player()
        self.get_legal_moves()
        if self._state.is_terminal():
            self._is_done = True
            return

    def get_move(self, move_inp: Union[tuple[tuple[int, int], tuple[int, int]], str]) -> Move:
        if isinstance(move_inp, (tuple, list)):
            return move_from_llm(move_inp)
        elif isinstance(move_inp, str):
            return move_from_openspiel_str(move_inp)
        else:
            raise ValueError(f"Invalid move input: {move_inp}")

    def get_legal_moves(self) -> list[str]:
        if self._is_done:
            return []
        self.legal_moves = [self._state.action_to_string(action) for action in self._state.legal_actions()]
        return self.legal_moves

    def current_player(self):
        return self._state.current_player()

    def is_done(self) -> bool:
        return self._is_done

    def live_play_is_legal(self, move_str: str) -> bool:
        return move_str in self.live_play_legal_moves()

    def live_play_observation(self) -> dict[str, Any]:
        return {'state': str(self._state), 'your_character': 'x' if self.turn == 0 else 'o'}

    def live_play_legal_moves(self) -> list[str]:
        return self.legal_moves

    def get_final_stats(self) -> dict[str, Any]:
        if not self.is_done():
            return {"done": False, "winner": None, "move_count": self.move_count}

        returns = self._state.returns()
        if len(returns) != 2:
            raise RuntimeError("should be a 2-player game.")

        r0, r1 = float(returns[0]), float(returns[1])
        if r0 > r1:
            winner: Optional[int] = 0
        elif r1 > r0:
            winner = 1
        else:
            winner = None  # draw

        return {
            "done": True,
            "winner": winner,
            "move_count": self.move_count,
            "returns": returns,
        }

    def visualize(self) -> None:
        state = self.get_observation()
        me = state.get("me", []) or []
        opp = state.get("opp", []) or []
        size = int(state.get("board_size", 11))
        me_color = "b" if self.turn == 0 else "w"
        opp_color = "w" if self.turn == 0 else "b"

        def token(row: int, col: int) -> str:
            if (row, col) in me:
                return me_color
            if (row, col) in opp:
                return opp_color
            return "."

        files = "".join(chr(ord("a") + i) for i in range(size))
        print("  +" + "--" * size + "+")
        for rank in range(size, 0, -1):
            row = [token(rank-1, col) for col in range(size)]
            print(f"{rank:2d} | " + " ".join(row) + " |")
        print("  +" + "--" * size + "+")
        print("    " + " ".join(files))
        if state.get("to_play"):
            print(f"To play: {state['to_play']}")

    @staticmethod
    def get_prompt(config: dict[str, Any], live_play: bool = False) -> str:
        board_size = int(config.get("board_size", 11))
        game_name = f"Hex on a {board_size}x{board_size} board"
        if live_play:
            return render_prompt_for_live_play(
                game_name=game_name,
                state=[
                    "You are always the player to move.",
                    "`your_character` is either `'x'` which tries to connect the top and bottom sides, or `'o'` which tries to connect the left and right sides.",
                    f"Rows 1-indexed in from the top to the bottom.",
                    f"Columns start with 'a' from the left to the right.",
                    "Your goal is to connect your two opposing sides; the opponent tries to connect their two opposing sides.",
                    "Note that the board is a grid each individual cell is a hexagonal shape. Thus to know which cell is touching which other cell requires spatial reasoning to determine the winning lines.",
                    "Every stone not on the edge of the board is touching exactly 6 other stones (since they are hexagonal).",
                    "Two of those 6 stones are in the same row, two are in the top row, and two are in the bottom row.",
                    "Example: The stone located at j8 is touching i8 and k8",
                    "   and to its bottom is touching i9 and j9",
                    "   and to its top is touching j7 and k7",
                    "An easy way to determine the touching cells of cell (i, j) is all it's 8 neighbors except for (i-1, j-1) and (i+1, j+1)",
                ],
                action=[
                    "Return a single move as a string in the format `a1`.",
                    "The chosen cell must be empty and within the board bounds.",
                    "There is no pass; always place a stone.",
                ],
                example_action='d3',
            )
        else:
            return render_prompt_pre_filled(
                game_name=game_name,
                signature_block=(
                        "```python\n"
                        "def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:\n"
                        "    ...\n"
                        "```"
                ),
                state=[
                    "You are always the player to move.",
                    "`me` is a list of (row, col) tuples containing your stones.",
                    "`opp` is a list of (row, col) tuples containing the opponent's stones.",
                    "`color` is your color: `'b'` for black which tries to connect the top and bottom sides, and `'w'` for white which tries to connect the left and right sides.",
                    f"Rows and columns are 0-indexed in `0..{board_size - 1}`.",
                    "An empty cell is any coordinate not in `me` or `opp`.",
                    "Your goal is to connect your two opposing sides; the opponent tries to connect their two opposing sides.",
                    "Note that the board is a grid each individual cell is a hexagonal shape. Thus to know which cell is touching which other cell requires spatial reasoning to determine the winning lines.",
                    "Every stone not on the edge of the board is touching exactly 6 other stones (since they are hexagonal).",
                    "Two of those 6 stones are in the same row, two are in the top row, and two are in the bottom row.",
                    "Example: The stone located at (4, 1) is touching (4, 0) and (4, 2)",
                    "   and to its bottom is touching (5, 1) and (5, 0)",
                    "   and to its top is touching (3, 1) and (3, 2)",
                    "An easy way to determine the touching cells of cell (i, j) is all it's 8 neighbors except for (i-1, j-1) and (i+1, j+1)",
                ],
                action=[
                    "Return a single move as a tuple `(row, col)`.",
                    "The chosen cell must be empty and within the board bounds.",
                    "There is no pass; always place a stone.",
                ],
            )

if __name__ == "__main__":
    config = get_config_file('hex', 'world1')
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-play", action="store_true")
    args = parser.parse_args()
    if args.live_play:
        prompt = HexGame.get_prompt(config=config, live_play=True)
        print(prompt)
        (Path(__file__).parent / "prompt_example_live_play.txt").write_text(prompt)
    else:
        prompt = HexGame.get_prompt(config=config)
        print(prompt)
        (Path(__file__).parent / "prompt_example.txt").write_text(prompt)
