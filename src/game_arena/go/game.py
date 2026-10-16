import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional, Union

import pyspiel
import numpy as np

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled

# OpenSpiel Go observation planes (absolute):
# 0: black stones, 1: white stones, 2: empty, 3: to-play indicator.
GO_PLANE_MAP = {
    "black": 0,
    "white": 1,
    "empty": 2,
    "to_play": 3,
}


def _reshape_to_planes(obs: Any, board_size: int = 19) -> np.ndarray:
    arr = np.asarray(obs, dtype=np.float32)
    if arr.ndim == 1:
        n = arr.size // (board_size * board_size)
        return arr.reshape(n, board_size, board_size)
    if arr.ndim == 3:
        if arr.shape[0] == board_size and arr.shape[1] == board_size:
            return np.transpose(arr, (2, 0, 1))
        return arr
    raise ValueError(f"Unexpected obs shape: {arr.shape}")


def _go_columns(size: int) -> list[str]:
    letters = []
    for i in range(size):
        code = ord("a") + i
        if code >= ord("i"):
            code += 1
        letters.append(chr(code))
    return letters


def _sq_to_coord(sq: str, board_size: int) -> tuple[int, int]:
    sq = sq.strip()
    if sq.lower() == "pass":
        return (0, 0)
    cols = _go_columns(board_size)
    col_letter = sq[0]
    if col_letter not in cols:
        raise ValueError(f"Invalid column letter: {col_letter}")
    row = cols.index(col_letter) + 1
    try:
        col = int(sq[1:])
    except ValueError:
        raise ValueError(f"Invalid coordinate: {sq}") from None
    if not (1 <= col <= board_size):
        raise ValueError(f"Invalid row number: {col}")
    return row, col


def parse_board(obs: Any, board_size: int = 19) -> dict[str, Any]:
    planes = _reshape_to_planes(obs, board_size=board_size)
    if planes.shape[0] < 3:
        raise ValueError(f"Need >=3 planes, got {planes.shape[0]}")
    cols = _go_columns(board_size)
    def to_sq(col: int, row: int) -> str:
        rank = row + 1
        return f"{cols[col]}{rank}"
    pieces: dict[str, str] = {}
    for row, col in np.argwhere(planes[GO_PLANE_MAP["black"]] > 0.5):
        pieces[to_sq(int(col), int(row))] = "b"
    for row, col in np.argwhere(planes[GO_PLANE_MAP["white"]] > 0.5):
        pieces[to_sq(int(col), int(row))] = "w"
    return pieces


@dataclass(frozen=True, order=True)
class GoMove:
    llm_output: tuple[int, int]
    action: int

    def get_unparsed_str(self) -> tuple[int, int]:
        return self.llm_output


class GoGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.board_size: int = int(self.config.get("board_size", 19))

        try:
            self._spiel_game = pyspiel.load_game("go", {"board_size": self.board_size})
        except Exception:
            self._spiel_game = pyspiel.load_game("go")
        self._state = self._spiel_game.new_initial_state()
        self.turn = self._state.current_player()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("GoGame expects a 2-player OpenSpiel game.")

        self.move_count: int = 0
        self._is_done: bool = False
        self.get_legal_moves()

    def get_observation(self) -> dict[str, Any]:
        turn = self.turn if self.turn >= 0 else 0
        pieces = parse_board(self._state.observation_tensor(turn), board_size=self.board_size)
        my_color = "b" if self.turn == 0 else "w"
        opp_color = "w" if self.turn == 0 else "b"
        return {
            "me": sorted([_sq_to_coord(sq, self.board_size) for sq, v in pieces.items() if v == my_color]),
            "opponent": sorted([_sq_to_coord(sq, self.board_size) for sq, v in pieces.items() if v == opp_color]),
        }

    def get_fixed_observation(self) -> dict[str, Any]:
        pieces = parse_board(self._state.observation_tensor(0), board_size=self.board_size)
        return {
            "black": sorted([_sq_to_coord(sq, self.board_size) for sq, v in pieces.items() if v == "b"]),
            "white": sorted([_sq_to_coord(sq, self.board_size) for sq, v in pieces.items() if v == "w"]),
            "turn": self.turn,
        }

    def game_step(self, move: Union[GoMove, int]) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        action = move.action if isinstance(move, GoMove) else move
        if action not in self._state.legal_actions():
            raise ValueError(f"Invalid or illegal move in Go: {move}")
        self._state.apply_action(action)
        self.move_count += 1
        self.turn = self._state.current_player()
        if self._state.is_terminal():
            self._is_done = True
            return
        self.get_legal_moves()

    def get_move(self, move_inp: Union[GoMove, tuple[int, int]]) -> Union[GoMove, int]:
        if isinstance(move_inp, GoMove):
            return move_inp
        if isinstance(move_inp, (tuple, list)) and len(move_inp) == 2:
            turn_char = 'B ' if self.turn == 0 else 'W '
            row = int(move_inp[0])
            col = int(move_inp[1])
            if (row, col) not in self.legal:
                raise ValueError(f"Invalid move: {move_inp}. in move_count {self.move_count}, current board: {self.get_observation()}")
            if row == 0 and col == 0:
                action = self._state.string_to_action(turn_char + "PASS")
                return GoMove(action=action, llm_output=(0, 0))
            cols = _go_columns(self.board_size)
            action_body = f"{cols[row - 1]}{col}"
            action_str = turn_char + action_body
            action = self._state.string_to_action(action_str)
            return GoMove(action=action, llm_output=(row, col))
        elif isinstance(move_inp, str):
            return self.get_move(eval(move_inp))
        raise ValueError(f"Invalid move: {move_inp}")

    def get_legal_moves(self) -> list[tuple[int, int]]:
        if self._is_done:
            return []
        self.legal = []
        for action in self._state.legal_actions():
            action_str = self._state.action_to_string(action)
            if " " in action_str:
                action_str = action_str.split(" ", 1)[1]
            self.legal.append(_sq_to_coord(action_str, self.board_size))
        return self.legal

    def current_player(self):
        return self._state.current_player()

    def is_done(self) -> bool:
        return self._is_done

    def get_final_stats(self) -> dict[str, Any]:
        if not self.is_done():
            return {"done": False, "winner": None, "move_count": self.move_count}

        returns = self._state.returns()
        if len(returns) != 2:
            raise RuntimeError("Go should be a 2-player game.")

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


    @staticmethod
    def get_prompt(config: dict[str, Any]) -> str:
        board_size = int(config.get("board_size", 19))
        memory = config.get("memory", False)
        if memory:  # with memory
            mem_parameter = ', memory: dict'
            mem_state = [
                "`memory` is an empty dictionary that you may use however you want to store information between calls.",
                "You may use and store anything in `memory` and store any keys and values you want (even leave it empty).",
            ]
            ret_type = 'tuple[tuple[int, int], dict]'
            actions = [
                "Return a tuple `(action, memory)` where `memory` is a dictionary that you will receive next call (You may return an empty dictionary if you don't want to store anything).",
                "`action` is a single move as a tuple `(row, col)`.",
                "Use `(0, 0)` to pass.",
            ]
        else:  # without memory
            mem_parameter = ''
            mem_state = []
            ret_type = 'tuple[int, int]'
            actions = [
                "Return exactly ONE move as a tuple `(row, col)`.",
                "Use `(0, 0)` to pass.",
            ]
        return render_prompt_pre_filled(
            game_name=f"game of Go on a {board_size}x{board_size} board",
            signature_block=(
                "```python\n"
                f"def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]{mem_parameter}) -> {ret_type}:\n"
                "    ...\n"
                "```"
            ),
            state=[
                "You are always the player to move.",
                "`me` is a list of (row, col) tuples containing your stones.",
                "`opponent` is a list of (row, col) tuples containing the opponent's stones.",
                f"Rows are indexed from 1 (top) to {board_size} (bottom).",
                f"Columns are indexed from 1 (left) to {board_size} (right).",
                *mem_state,
            ],
            action=actions,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--memory", action="store_true")
    args = parser.parse_args()
    if not args.memory:
        config = get_config_file("go", "world1")
        prompt = GoGame.get_prompt(config=config)
        print(prompt)
        (Path(__file__).parent / "prompt_example.txt").write_text(prompt)
    else:
        config = get_config_file("go", "worldmem1")
        prompt = GoGame.get_prompt(config=config)
        print(prompt)
        (Path(__file__).parent / "prompt_example_memory.txt").write_text(prompt)
