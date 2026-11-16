import re
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Union

import pyspiel

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled, render_prompt_for_live_play


@dataclass(frozen=True)
class Connect4Move:
    col: int

    def get_unparsed_str(self) -> str:
        return str(self.col)


class Connect4Game(Game):
    """
    Two-player Connect 4 game, backed by OpenSpiel's implementation.

    Board: rows x cols grid (default 6 x 7).
    Players alternately drop discs into columns; discs fall to the lowest empty
    cell in that column. First player to connect four in a row (horiz/vert/diag)
    wins; full board with no connect-four is a draw.

    Observation for the current player:
        get_observation() -> dict[str, list[list[int]]]

    The observation is a rows x cols grid of ints:

        0  = empty cell
        1  = your disc (current player)
        -1 = opponent disc

    Internally, we use OpenSpiel's "connect_four" game for rules, legality,
    and terminal / return computation. We maintain a simple board representation
    purely for observations.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__()
        self.config = config
        self.rows: int = int(self.config["rows"])
        self.cols: int = int(self.config["cols"])
        self._spiel_game = pyspiel.load_game("connect_four")
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("Connect4Game expects a 2-player OpenSpiel game.")
        self.board: list[list[int]] = [
            [0 for _ in range(self.cols)] for _ in range(self.rows)
        ]

        self.turn: int = 0
        self.move_count: int = 0
        self._is_done: bool = False
        self._legal_moves_cache: set[int] = set()
        self._update_legal_moves()

    def _update_legal_moves(self) -> None:
        if self._state.is_terminal():
            self._legal_moves_cache = set()
            self._is_done = True
            return

        legal_actions = self._state.legal_actions()
        self._legal_moves_cache = {a for a in legal_actions}
        self._is_done = False

    def _apply_action_to_board(self, col: int, player: int) -> None:
        if not (0 <= col < self.cols):
            raise ValueError(f"Column out of bounds: {col}")

        mark = 1 if player == 0 else -1
        for r in range(self.rows - 1, -1, -1):
            if self.board[r][col] == 0:
                self.board[r][col] = mark
                return

        raise RuntimeError(f"Column {col} is full; move should have been illegal.")

    def get_observation(self) -> dict[str, Any]:
        if self.turn == 0:
            obs_board = [row.copy() for row in self.board]
        else:
            obs_board = [[-cell for cell in row] for row in self.board]
        return {"board": obs_board}

    def get_fixed_observation(self) -> dict[str, Any]:
        return {
            "board": [row.copy() for row in self.board],
            "turn": self.turn,
            "legal_moves": self.get_legal_moves(),
        }

    def get_move(self, move_str: Union[str, int]) -> Connect4Move:
        if isinstance(move_str, int):
            return Connect4Move(int(move_str))
        s = str(move_str).strip()
        match = re.match(r".*?(-?\d+).*", s)
        if match:
            col = int(match.group(1))
            return Connect4Move(col)
        raise ValueError(f"Invalid move string: {move_str!r}")

    def get_legal_moves(self) -> list[int]:
        if self._is_done:
            return []
        return list(self._legal_moves_cache)

    def game_step(self, move: Connect4Move) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        if move.col not in self._legal_moves_cache:
            raise ValueError(f"Invalid or illegal move: {move}")
        col = move.col
        if not (0 <= col < self.cols):
            raise ValueError(f"Move out of bounds: {move}")

        self._state.apply_action(col)
        self._apply_action_to_board(col, self.turn)
        self.move_count += 1

        if self._state.is_terminal():
            self._is_done = True
            self._legal_moves_cache = set()
            return

        self.turn = 1 - self.turn
        self._update_legal_moves()

    def current_player(self) -> int:
        return self.turn

    def is_done(self) -> bool:
        return self._is_done

    def live_play_is_legal(self, move_str: str) -> bool:
        return move_str in self.live_play_legal_moves()

    def live_play_observation(self) -> dict[str, Any]:
        return {'state': self.get_observation()}

    def live_play_legal_moves(self) -> list[int]:
        return [move for move in self.get_legal_moves()]

    def get_final_stats(self) -> dict[str, Any]:
        if not self.is_done():
            return {"done": False, "winner": None, "move_count": self.move_count}

        returns = self._state.returns()
        r0, r1 = returns[0], returns[1]
        if r0 > r1:
            winner = 0
        elif r1 > r0:
            winner = 1
        else:  # draw
            winner = None

        return {
            "done": True,
            "winner": winner,
            "move_count": self.move_count,
            "returns": returns,
        }

    @staticmethod
    def get_prompt(config: dict[str, Any], live_play: bool = False) -> str:
        rows = int(config.get("rows", 6))
        cols = int(config.get("cols", 7))

        game_name=f"Connect 4 game on a {rows}x{cols} grid"
        signature_block=(
            "```python\n"
            "def policy(board: list[list[int]]) -> int:\n"
            "    ...\n"
            "```"
        )
        state=[
            f"The board is a {rows}x{cols} grid.",
            "You are always the current player when `policy` is called.",
            f"`board` is a {rows}x{cols} grid of ints with the following encoding:",
            "`0` represents an empty cell.",
            "`1` represents your disc (current player).",
            "`-1` represents the opponent's disc.",
            f"Rows are indexed from `0` (top) to `{rows - 1}` (bottom).",
            f"Columns are indexed from `0` to `{cols - 1}`.",
            "When a disc is dropped into a column, it occupies the lowest available empty cell in that column.",
        ]
        action=[
            f"Return an integer column index `col` in the range `0-{cols - 1}`.",
            "The chosen column must not be full (i.e., it must contain at least one `0`).",
            "Your disc will be placed in the lowest available row in that column.",
            "The objective is to form a horizontal, vertical, or diagonal line of four of your discs.",
        ]
        if live_play:
            return render_prompt_for_live_play(
                game_name=game_name,
                state=state,
                action=action,
                example_action='0',
            )
        else:
            return render_prompt_pre_filled(
                game_name=game_name,
                signature_block=signature_block,
                state=state,
                action=action,
            )

if __name__ == "__main__":
    config = get_config_file('connect4', 'world1')
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-play", action="store_true")
    args = parser.parse_args()
    if args.live_play:
        prompt = Connect4Game.get_prompt(config=config, live_play=True)
        print(prompt)
        (Path(__file__).parent / "prompt_example_live_play.txt").write_text(prompt)
    else:
        prompt = Connect4Game.get_prompt(config=config)
        print(prompt)
        (Path(__file__).parent / "prompt_example.txt").write_text(prompt)

