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
    # UPDATE THIS
    rc: str
    action: int

def human_to_action(s: str) -> Move:
    # UPDATE THIS
    row1, col1 = [int(x) for x in s.split(',')]
    return Move(s, row1*6+col1)

def action_to_human(action: int) -> str:
    # UPDATE THIS
    r1, c1 = divmod(action, 6)
    return f"{r1},{c1}" 

# UPDATE THIS
class AbstractGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.turn: int = 0

        # UPDATE THIS
        self._spiel_game = pyspiel.load_game("tic_tac_toe")
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("Game expects a 2-player OpenSpiel game.")

        self.move_count: int = 0
        self._is_done: bool = False

    def get_observation(self) -> dict[str, np.ndarray]:
        # UPDATE THIS
        me = self.turn
        obs = list(self._state.observation_tensor())
        if len(obs) != 4 * 6 * 6:
            raise RuntimeError(f"Unexpected Amazons observation size: {len(obs)}")
        board = np.array([int(v) for v in obs]).reshape(4, 6, 6)
        return {"board": board}

    def game_step(self, move: Union[Move, int]) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        if isinstance(move, Move):
            action = move.action
            self._state.apply_action(action)
            self.move_count += 1
        else:
            action = move
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


def get_prompt(config: dict[str, Any]) -> str:
    # UPDATE THIS
    return (
        "You are an AI competing in a gaming arena.\n"
    )


if __name__ == "__main__":
    config = get_config_file('tic_tac_toe', 'world1')
    prompt = get_prompt(config=config)
    print(prompt)
    (Path(__file__).parent / "prompt_example.txt").write_text(prompt)

