import argparse
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass

import pyspiel
import numpy as np

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled, render_prompt_for_live_play


@dataclass(frozen=True, order=True)
class ClobberMove:
    start_row: int
    start_col: int
    direction: str
    action: int
    def get_unparsed_str(self) -> str:
        return f"{self.start_row},{self.start_col},{self.direction}"


def action_to_move(action: int) -> ClobberMove:
    # "* Let `(row, col)` be the starting cell of the move (0-indexed, row 0 is the top row).\n"
    # "* Let `d` be the direction:\n"
    # "  - `d=0`: up    (row-1, col)\n"
    # "  - `d=1`: right (row, col+1)\n"
    # "  - `d=2`: down  (row+1, col)\n"
    # "  - `d=3`: left  (row, col-1)\n"
    # "* The action id is `a = ((row * columns) + col) * 4 + d`.\n"
    if not (0 <= action < 288):
        raise ValueError("Action must be in range 0..287")
    row_col = action // 4
    row = row_col // 6
    col = row_col % 6
    direction = action % 4
    direction_str = "U" if direction == 0 else "R" if direction == 1 else "D" if direction == 2 else "L"
    return ClobberMove(row, col, direction_str, action)


def human_to_move(s: str) -> ClobberMove:
    s_list = s.split(':')[0].strip().split(',')
    if len(s_list) != 3:
        raise ValueError(f"Invalid Clobber move string: {s!r} (expected like 'row,col,dir')")
    start_row = int(s_list[0])
    start_col = int(s_list[1])
    direction_str = s_list[2]
    direction = 0 if s_list[2] == "U" else 1 if s_list[2] == "R" else 2 if s_list[2] == "D" else 3
    action = start_row * 6 * 4 + start_col * 4 + direction
    return ClobberMove(start_row, start_col, direction_str, action)


def parse_observation(obs: list[int]) -> dict[str, np.ndarray]:
    expected = 3 * 5 * 6
    if len(obs) != expected:
        raise RuntimeError(f"Unexpected Clobber observation size: {len(obs)} (expected {expected})")
    plane_size = 5 * 6
    p0 = np.array([int(v) for v in obs[0:plane_size]]).reshape(5, 6)
    p1 = np.array([int(v) for v in obs[plane_size : 2 * plane_size]]).reshape(5, 6)
    return {"p0": p0, "p1": p1}

class ClobberGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self._spiel_game = pyspiel.load_game("clobber")
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("ClobberGame expects a 2-player OpenSpiel game.")

        self.turn: int = self._state.current_player()
        self.move_count: int = 0
        self._is_done: bool = False

    def get_observation(self) -> dict[str, np.ndarray]:
        # Player-relative observation tensor planes are: you, opponent, empty.
        # row=0 is the top row and col=0 is the left column.
        parsed = parse_observation(list(self._state.observation_tensor(self.turn)))
        return {"you": parsed["p0"], "opponent": parsed["p1"]}

    def get_fixed_observation(self) -> dict[str, Any]:
        parsed = parse_observation(list(self._state.observation_tensor(0)))
        return {"you": parsed["p0"], "opponent": parsed["p1"], "turn": self.turn}

    def get_move(self, move_str: str) -> ClobberMove:
        return human_to_move(move_str)

    def get_legal_moves(self) -> list[ClobberMove]:
        if self._is_done:
            return []
        legal_actions = self._state.legal_actions()
        return [action_to_move(a) for a in self._state.legal_actions()]

    def game_step(self, move: ClobberMove) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        if move.action not in self._state.legal_actions():
            raise ValueError(f"Invalid or illegal move in Clobber: {move}")

        self._state.apply_action(move.action)
        self.move_count += 1

        if self._state.is_terminal():
            self._is_done = True
            return

        self.turn = self._state.current_player()

    def current_player(self) -> int:
        return self.turn

    def is_done(self) -> bool:
        return self._is_done

    def get_final_stats(self) -> dict[str, Any]:
        if not self.is_done():
            return {"done": False, "winner": None, "move_count": self.move_count}

        returns = self._state.returns()
        if len(returns) != 2:
            raise RuntimeError("Clobber should be a 2-player game.")

        r0, r1 = float(returns[0]), float(returns[1])
        if r0 > r1:
            winner: Optional[int] = 0
        elif r1 > r0:
            winner = 1
        else:
            winner = None  # draw (should be rare / impossible in standard clobber)

        return {
            "done": True,
            "winner": winner,
            "move_count": self.move_count,
            "returns": returns,
        }

    def live_play_is_legal(self, move_str: str) -> bool:
        return move_str in self.live_play_legal_moves()

    def live_play_observation(self) -> dict[str, Any]:
        return {'state': self.get_observation()}

    def live_play_legal_moves(self) -> list[str]:
        return [move.get_unparsed_str() for move in self.get_legal_moves()]

    @staticmethod
    def get_prompt(config: dict[str, Any], live_play: bool = False) -> str:
        game_name="Clobber game on a 5x6 grid"
        signature_block=(
            "```python\n"
            "def policy(you: list[int], opponent: list[int]) -> str:\n"
            "    ...\n"
            "```"
        )
        state=[
            "You are always the player to move.",
            "Board size is 5 rows x 6 columns.",
            "`you` and `opponent` are 5x6 arrays describing the board.",
            "Values are 0 or 1.",
            "`you[row, col] == 1` means you have a piece at cell `(row, col)`.",
            "`opponent[row, col] == 1` means the opponent has a piece at cell `(row, col)`.",
            "For any `(row, col)`, at most one of `you[row, col]` and `opponent[row, col]` is 1.",
        ]
        action=[
            "Return a string move in the format `'row,col,dir'`.",
            "`row` is the row of the starting cell (0-4).",
            "`col` is the column of the starting cell (0-5).",
            "`dir` is the direction of the move: `'U'` (up), `'R'` (right), `'D'` (down), `'L'` (left).",
            "The start cell must contain your piece.",
            "The destination cell must be in bounds and contain an opponent piece.",
            "A legal move must capture an adjacent opponent piece by moving one square orthogonally onto it.",
            "The opponent piece is removed; your piece occupies the destination square; your starting square becomes empty.",
            "The first player to have no legal moves on their turn loses.",
        ]
        if live_play:
            return render_prompt_for_live_play(
                game_name=game_name,
                state=state,
                action=action,
                example_action='"0,0,R"',
            )
        else:
            return render_prompt_pre_filled(
                game_name=game_name,
                signature_block=signature_block,
                state=state,
                action=action,
            )


if __name__ == "__main__":
    config = get_config_file('clobber', 'world1')
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-play", action="store_true")
    args = parser.parse_args()
    if args.live_play:
        prompt = ClobberGame.get_prompt(config=config, live_play=True)
        print(prompt)
        (Path(__file__).parent / "prompt_example_live_play.txt").write_text(prompt)
    else:
        prompt = ClobberGame.get_prompt(config=config)
        print(prompt)
        (Path(__file__).parent / "prompt_example.txt").write_text(prompt)
