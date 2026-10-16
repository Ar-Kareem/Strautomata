from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional, Union

import pyspiel
import numpy as np

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled


# OpenSpiel havannah observation planes (absolute):
# 0: player 0 stones, 1: player 1 stones, 2: empty/valid mask.
HAVANNAH_PLANE_MAP = {
    "p0": 0,
    "p1": 1,
    "empty": 2,
}

def _reshape_to_planes(obs: Any, board_size: int = 15) -> np.ndarray:
    arr = np.asarray(obs, dtype=np.float32)
    if arr.ndim == 1:
        n = arr.size // (board_size * board_size)
        return arr.reshape(n, board_size, board_size)
    if arr.ndim == 3:
        if arr.shape[0] == board_size and arr.shape[1] == board_size:
            return np.transpose(arr, (2, 0, 1))
        return arr
    raise ValueError(f"Unexpected obs shape: {arr.shape}")

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

class HavannahGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.turn: int = 0

        self._spiel_game = pyspiel.load_game("havannah")
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("Game expects a 2-player OpenSpiel game.")

        self.move_count: int = 0
        self._is_done: bool = False
        self.get_legal_moves()

    def get_observation(self, board_size: int = 15) -> dict[str, Any]:
        """
        Parse OpenSpiel Havannah observation into a simple piece map.

        Returns: {"pieces": {"a1":"b", ...}, "to_play": "black"/"white", "board_size": 15}
        """
        planes = _reshape_to_planes(self._state.observation_tensor(self.turn), board_size=board_size)
        if planes.shape[0] != 3:
            raise ValueError(f"Need == 3 planes, got {planes.shape[0]}")

        me = []
        opp = []
        for row, col in np.argwhere(planes[HAVANNAH_PLANE_MAP["p0"]] > 0.5):
            me.append((int(row), int(col)))
        for row, col in np.argwhere(planes[HAVANNAH_PLANE_MAP["p1"]] > 0.5):
            opp.append((int(row), int(col)))

        valid_mask = (
            (planes[HAVANNAH_PLANE_MAP["empty"]] > 0.5)
            | (planes[HAVANNAH_PLANE_MAP["p0"]] > 0.5)
            | (planes[HAVANNAH_PLANE_MAP["p1"]] > 0.5)
        )

        return {
            "me": me,
            "opp": opp,
            "valid_mask": valid_mask,
        }

    def get_fixed_observation(self, board_size: int = 15) -> dict[str, Any]:
        planes = _reshape_to_planes(self._state.observation_tensor(0), board_size=board_size)
        if planes.shape[0] != 3:
            raise ValueError(f"Need == 3 planes, got {planes.shape[0]}")

        me = []
        opp = []
        for row, col in np.argwhere(planes[HAVANNAH_PLANE_MAP["p0"]] > 0.5):
            me.append((int(row), int(col)))
        for row, col in np.argwhere(planes[HAVANNAH_PLANE_MAP["p1"]] > 0.5):
            opp.append((int(row), int(col)))

        valid_mask = (
            (planes[HAVANNAH_PLANE_MAP["empty"]] > 0.5)
            | (planes[HAVANNAH_PLANE_MAP["p0"]] > 0.5)
            | (planes[HAVANNAH_PLANE_MAP["p1"]] > 0.5)
        )

        return {
            "black": me,
            "white": opp,
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

    def get_move(self, move_inp: Union[tuple[int, int], str]) -> Move:
        if isinstance(move_inp, tuple):
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
        size = 15
        state = self.get_observation()
        me = state.get("me", []) or []
        opp = state.get("opp", []) or []
        valid_mask = state.get("valid_mask")
        my_color = "w" if self.turn == 0 else "b"
        opp_color = "b" if self.turn == 0 else "w"

        def token(row: int, col: int) -> str:
            if valid_mask is not None and not bool(valid_mask[row, col]):
                return " "
            sq = f"{chr(ord('a') + col)}{size - row}"
            if (row, col) in me:
                return my_color
            if (row, col) in opp:
                return opp_color
            return "."

        files = "".join(chr(ord("a") + i) for i in range(size))
        print("  +" + "--" * size + "+")
        for rank in range(1, size + 1):
            spaces_to_add = np.abs(size//2 - rank + 1)
            spaces = " " * spaces_to_add
            row = [token(rank-1, c) for c in range(size)]
            print(f"{rank:2d} | " + spaces + " ".join(row).rstrip().lstrip() + spaces + " |")
        print("  +" + "--" * size + "+")
        print("    " + " ".join(files))
        print(f"To play: {'white' if self.turn == 0 else 'black'}")


    @staticmethod
    def get_prompt(config: dict[str, Any]) -> str:
        board_size = int(config.get("board_size", 15))
        return render_prompt_pre_filled(
            game_name=f"Havannah on a {board_size}x{board_size} board",
            signature_block=(
                "```python\n"
                "def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:\n"
                "    ...\n"
                "```"
            ),
            state=[
                "You are always the player to move.",
                "`me` is a list of (row, col) tuples for player-0 stones.",
                "`opp` is a list of (row, col) tuples for player-1 stones.",
                "`valid_mask` is a 2D array (shape NxN) where True marks playable cells on the Havannah board.",
                f"Rows and columns are 0-indexed in `0..{board_size - 1}`, matching `valid_mask` indices.",
                "A player wins when they complete one of three different structures from unbroken lines, or paths, of connected stones, all of their colour:"
                "- A ring is a loop around one or more cells (no matter whether the encircled cells are occupied by any player or empty[3])",
                "- A bridge, which connects any two of the six corner cells of the board",
                "- A fork, which connects any three edges of the board; corner points are not considered parts of an edge",
                "Note that the board is represented as a 2D array however internally it is a hexagonal grid. This requires extra spatial reasoning to determine the winning structures."
                "Every stone not on the edge of the board is touching exactly 6 other stones (since they are hexagonal).",
                "Two of those 6 stones are in the same column, two are in the left column, and two are in the right column.",
                "Example: The store located at (4, 1) [i.e. b5] is touching b6 (5, 1) and b4 (3, 1)",
                "   and to its left is touching a4 (3, 0) and a5 (4, 0)",
                "   and to its right is touching c5 (4, 2) and c4 (3, 2)",
            ],
            action=[
                "Return a single move as a tuple `(row, col)`.",
                "The chosen coordinate must satisfy `valid_mask[row][col] == True` and be unoccupied.",
                "There is no pass move; always place a stone.",
            ],
        )


if __name__ == "__main__":
    config = get_config_file('havannah', 'world1')
    prompt = HavannahGame.get_prompt(config=config)
    print(prompt)
    (Path(__file__).parent / "prompt_example.txt").write_text(prompt)
