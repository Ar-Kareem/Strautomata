from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional, Union

import pyspiel
import numpy as np

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled

@dataclass(frozen=True)
class LinesOfActionMove:
    from_row: int
    from_col: int
    to_row: int
    to_col: int
    action_pair: tuple[str, str]

def _move_from_human(state, turn: int, inp: str) -> LinesOfActionMove:
    def _coord_to_algebraic(row: int, col: int) -> str:
        return f"{chr(ord('a') + col)}{row + 1}"
    a1, a2 = inp.split(':')
    row1, col1 = [int(x) for x in a1.split(',')]
    row2, col2 = [int(x) for x in a2.split(',')]
    sa1, sa2 = _coord_to_algebraic(row1, col1), _coord_to_algebraic(row2, col2)
    return LinesOfActionMove(row1, col1, row2, col2, (sa1, sa2))

def _move_from_openspeil_str(state, turn: int, action: tuple) -> LinesOfActionMove:
    def _algebraic_to_coord(algebraic: str) -> tuple[int, int]:
        col = ord(algebraic[0]) - ord('a')
        row = 8 - int(algebraic[1])
        return row, col
    a1, a2 = action
    row1, col1 = _algebraic_to_coord(a1)
    row2, col2 = _algebraic_to_coord(a2)
    return LinesOfActionMove(row1, col1, row2, col2, (a1, a2))

class LinesOfActionGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.n: int = int(self.config.get("n", 8))

        self._spiel_game = pyspiel.load_game("lines_of_action")
        self._state = self._spiel_game.new_initial_state()
        self.turn = self._state.current_player()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("LinesOfActionGame expects a 2-player OpenSpiel game.")

        self.move_count: int = 0
        self._is_done: bool = False
        self.get_legal_moves()

    def action_to_human(self, action: tuple[str, str]) -> str:
        move = _move_from_openspeil_str(self._state, self.turn, action)
        return f"{move.from_row},{move.from_col}:{move.to_row},{move.to_col}"

    def get_observation(self) -> dict[str, list[list[int]]]:
        turn = self.turn if self.turn >= 0 else 0
        board_np = np.array(self._state.observation_tensor(turn)).reshape(3, 8, 8)
        player1 = board_np[0]
        player2 = board_np[1]
        board = player1 - player2
        if self.turn == 1:
            board = -1 * board
        return {"board": board}

    def get_fixed_observation(self) -> dict[str, Any]:
        board_np = np.array(self._state.observation_tensor(0)).reshape(3, 8, 8)
        player1 = board_np[0]
        player2 = board_np[1]
        board = player1 - player2
        return {"board": board, "turn": self.turn}

    def game_step(self, move: LinesOfActionMove) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        if move.action_pair not in self.legal_strings_dict:
            raise ValueError(f"Invalid or illegal move in Lines of Action: {move}")
        action_str = self.legal_strings_dict[move.action_pair]
        action = self._state.string_to_action(action_str)
        self._state.apply_action(action)
        self.move_count += 1

        if self._state.is_terminal():
            self._is_done = True
            return
        self.turn = self._state.current_player()
        self.get_legal_moves()

    def get_move(self, move_inp: Union[str, tuple[str, str]]) -> LinesOfActionMove:
        if isinstance(move_inp, tuple):
            return _move_from_openspeil_str(self._state, self.turn, move_inp)
        else:
            return _move_from_human(self._state, self.turn, move_inp)

    def get_legal_moves(self) -> list[str]:
        if self._is_done:
            return []
        legal_strings = [self._state.action_to_string(x) for x in self._state.legal_actions()]
        self.legal_strings_dict = {}
        for s in legal_strings:
            k = tuple(s.replace('x', '-').split('-'))
            self.legal_strings_dict[k] = s
        return list(self.legal_strings_dict.keys())
        
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

    @staticmethod
    def get_prompt(config: dict[str, Any]) -> str:
        n = int(config.get("n", 8))
        return render_prompt_pre_filled(
            game_name=f"Lines of Action on an {n}x{n} board",
            signature_block=(
                "```python\n"
                "def policy(board) -> str:\n"
                "    ...\n"
                "```"
            ),
            state=[
                "You are always the player to move when `policy` is called.",
                f"`board` is an {n}x{n} grid of ints with the following encoding:",
                "`0` represents an empty cell.",
                "`1` represents your piece (current player).",
                "`-1` represents the opponent's piece.",
                f"Rows are indexed from `0` (top) to `{n-1}` (bottom).",
                f"Columns are indexed from `0` (left) to `{n-1}` (right).",
                "Rules summary (Lines of Action):",
                "Players alternate moves.",
                "A piece moves horizontally, vertically, or diagonally.",
                "A piece must move exactly as many squares as there are pieces (both players) in the line (row, column, or diagonal) of movement.",
                "A piece may jump over friendly pieces but may not jump over enemy pieces.",
                "A piece may land on and capture an enemy piece (removing it from the board).",
                "Objective: connect all of your pieces into a single contiguous group, where connectivity is counted in 8 directions (horizontal/vertical/diagonal).",
            ],
            action=[
                "Return a single move string formatted exactly as: `\"from_row,from_col:to_row,to_col\"`.",
                f"All coordinates are 0-indexed with `row,col` in `0..{n-1}`.",
                "The move must be legal according to the Lines of Action rules.",
                "Example (syntax only): `\"0,1:2,3\"` moves the piece from `(0,1)` to `(2,3)`.",
            ],
        )


if __name__ == "__main__":
    config = get_config_file('lines_of_action', 'world1')
    prompt = LinesOfActionGame.get_prompt(config=config)
    print(prompt)
    (Path(__file__).parent / "prompt_example.txt").write_text(prompt)

