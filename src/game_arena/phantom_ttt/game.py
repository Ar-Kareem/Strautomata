from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional, Union

import pyspiel
import numpy as np

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled

@dataclass(frozen=True)
class Move:
    row: int
    col: int
    action: int

def human_to_action(s: Union[str, tuple[int, int]]) -> Move:
    if isinstance(s, tuple):
        row, col = s
        action = row*3+col
        return Move(row, col, action)
    else:
        row1, col1 = [int(x) for x in s.split(',')]
        action = row1*3+col1
        return Move(row1, col1, action)

def action_to_human(action: int) -> str:
    row, col = divmod(action, 3)
    return f"{row},{col}" 

class PhantomTTTGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.reveal_legal_moves: bool = self.config.get("reveal_legal_moves", True)
        self.turn: int = 0

        self._spiel_game = pyspiel.load_game("phantom_ttt")
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("Game expects a 2-player OpenSpiel game.")

        self.move_count: int = 0
        self._is_done: bool = False
    
    def action_to_human(self, action: int) -> str:
        return action_to_human(action)

    def get_observation(self) -> dict[str, np.ndarray]:
        obs = list(self._state.observation_tensor(self.turn))
        board = np.array(obs).reshape(3, 3, 3)
        empty = board[0]
        player_1 = board[1]
        player_2 = board[2]
        legal_moves = self._state.legal_actions()
        if self.turn == 0:
            r = {"board": player_1}
        elif self.turn == 1:
            r = {"board": player_2}
        else:
            raise ValueError(f"Invalid player: {self.turn}")
        if self.reveal_legal_moves:
            r["legal_moves"] = legal_moves
        return r

    def game_step(self, move: Union[Move, int]) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        if isinstance(move, Move):
            action = move.action
        else:
            action = move
        if action not in self._state.legal_actions():
            raise ValueError(f"Expected error, illegal action: {action}")
        self._state.apply_action(action)
        self.move_count += 1
        self.turn = self._state.current_player()
        if self._state.is_terminal():
            self._is_done = True
            return

    def get_move(self, move_str: Union[str, int]) -> Union[Move, int]:
        if isinstance(move_str, int):
            return move_str
        else:
            return human_to_action(move_str)

    def get_legal_moves(self) -> list[int]:
        if self._is_done:
            return []
        return self._state.legal_actions()

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
        reveal_legal_moves = config.get("reveal_legal_moves", True)
        extra_state_info = []
        if reveal_legal_moves:
            extra_state_info += [
                "`legal_moves` is a list of integers in `0-8` representing actions currently allowed by the engine.",
            ]
            signature_block = (
                "```python\n"
                "def policy(board: list[list[int]], legal_moves: list[int]) -> int:\n"
                "    ...\n"
                "```"
            )
        else:
            signature_block = (
                "```python\n"
                "def policy(board: list[list[int]]) -> int:\n"
                "    ...\n"
                "```"
            )
        return render_prompt_pre_filled(
            game_name="Phantom Tic Tac Toe (3x3)",
            signature_block=signature_block,
            state=[
                "`board` is a 3x3 list of lists (or equivalent array-like) of integers.",
                "`1` indicates a cell where **you** have successfully placed a mark.",
                "`0` indicates a cell that is **not confirmed** to be yours (it may be empty or occupied by the opponent).",
                "This is **Phantom Tic Tac Toe** (imperfect information): you do not directly observe the opponent's marks, and failed placement attempts may occur when you pick an occupied cell.",
                "You will be called when it is your turn; you should choose a cell to attempt to mark.",
            ] + extra_state_info,
            action=[
                "Return a tuple of two integers `(row, col)` where each is in `0-2`.",
                "Prefer actions that are consistent with the partial information: avoid cells where `board[row][col] == 1` (already confirmed yours).",
            ],
        )


if __name__ == "__main__":
    config = get_config_file('phantom_ttt', 'world1')
    prompt = PhantomTTTGame.get_prompt(config=config)
    print(prompt)
    (Path(__file__).parent / "prompt_example.txt").write_text(prompt)

