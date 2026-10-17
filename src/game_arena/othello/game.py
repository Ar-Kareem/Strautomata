from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional

import pyspiel
import numpy as np

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled


@dataclass(frozen=True, order=True)
class OthelloMove:
    move_str: str

    def get_unparsed_str(self) -> str:
        return self.move_str


def parse_observation(obs: list[int]) -> dict[str, np.ndarray]:
    if len(obs) != 3 * 8 * 8:
        raise RuntimeError(f"Unexpected Pentago observation size: {len(obs)}")
    p0 = np.array([int(v) for v in obs[8 * 8 : 2 * 8 * 8]]).reshape(8, 8)
    p1 = np.array([int(v) for v in obs[2 * 8 * 8 : 3 * 8 * 8]]).reshape(8, 8)
    return {"p0": p0, "p1": p1}


class OthelloGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.turn: int = 0

        self._spiel_game = pyspiel.load_game("othello")
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("OthelloGame expects a 2-player OpenSpiel game.")

        self.move_count: int = 0
        self._is_done: bool = False
        self._last_stores = None
        self._update_legal_moves()

    def get_observation(self) -> dict[str, np.ndarray]:
        obs = list(self._state.observation_tensor(self.turn))
        parsed = parse_observation(obs)
        return {"you": parsed["p0"], "opponent": parsed["p1"]}

    def get_fixed_observation(self) -> dict[str, Any]:
        obs = list(self._state.observation_tensor(0))
        return parse_observation(obs)

    def _update_legal_moves(self) -> None:
        if self._state.is_terminal():
            self._legal_moves_cache = {}
            return

        legal_actions = self._state.legal_actions()
        self._legal_moves_cache = {self._state.action_to_string(a): a for a in legal_actions}

    def get_move(self, move_str: str) -> OthelloMove:
        return OthelloMove(move_str)

    def get_legal_moves(self) -> list[OthelloMove]:
        if self._is_done:
            return []
        return sorted(list(self._legal_moves_cache.keys()))

    def game_step(self, move: OthelloMove) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        if move.move_str not in self._legal_moves_cache:
            raise ValueError(f"Invalid or illegal move in Othello: {move}")
        self._state.apply_action(self._legal_moves_cache[move.move_str])
        self.move_count += 1

        if self._state.is_terminal():
            self._is_done = True
            return
        self.turn = self._state.current_player()
        self._update_legal_moves()

    def current_player(self) -> int:
        return self.turn

    def is_done(self) -> bool:
        return self._is_done

    def get_final_stats(self) -> dict[str, Any]:
        if not self.is_done():
            return {"done": False, "winner": None, "move_count": self.move_count}

        returns = self._state.returns()
        if len(returns) != 2:
            raise RuntimeError("Othello should be a 2-player game.")

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
        return render_prompt_pre_filled(
            game_name="Othello (Reversi) on an 8x8 board",
            signature_block=(
                "```python\n"
                "def policy(you: np.ndarray, opponent: np.ndarray) -> str:\n"
                "    ...\n"
                "```"
            ),
            state=[
                "You are always the player to move when `policy` is called.",
                "`you` and `opponent` are 8x8 numpy arrays containing only 0/1 integers.",
                "`you[r][c] == 1` means your disc is at row `r`, col `c`.",
                "`opponent[r][c] == 1` means the opponent disc is at row `r`, col `c`.",
                "An empty cell means `you[r][c] == 0` and `opponent[r][c] == 0`.",
                "Positions are valid: never `you[r][c] == opponent[r][c] == 1`.",
                "Move coordinates use algebraic notation: columns `a..h` map to `c = 0..7`, rows `1..8` map to `r = 0..7`. For example, `a4` maps to you[3][0]",
                "The game ends when neither player has a legal move (or the board is full).",
                "Objective: finish with more discs than the opponent; ties are draws.",
            ],
            action=[
                "Return a move string like `\"d3\"` (file letter `a..h` + rank `1..8`).",
                "A legal move must place a disc on an empty cell that flips at least one opponent disc in any direction.",
                "Flips occur along any of the 8 directions where the new disc brackets a contiguous line of opponent discs ending in your disc.",
                "If you have no legal moves, return `\"pass\"`. You may not return `\"pass\"` if you have legal moves.",
            ],
        )

if __name__ == "__main__":
    config = get_config_file('othello', 'world1')
    prompt = OthelloGame.get_prompt(config=config)
    print(prompt)
    (Path(__file__).parent / "prompt_example.txt").write_text(prompt)
