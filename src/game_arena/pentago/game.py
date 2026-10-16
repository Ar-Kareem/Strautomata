from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional

import pyspiel
import numpy as np

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled


@dataclass(frozen=True, order=True)
class PentagoMove:
    act_str: str
    action: int

    def get_unparsed_str(self) -> str:
        return self.act_str

def llm_to_action_str(move_str: str) -> str:
    row, col, quad, d = move_str.split(',')
    row = int(row)
    col = chr(ord('a') + int(col) - 1)
    quad = int(quad)
    # swap quad 2 and 3
    quad = {0: 0, 1: 1, 2: 3, 3: 2}[quad]
    d = 1 if d == 'R' else 0
    quad_d = chr(ord('s') + quad * 2 + d)
    return f"{col}{row}{quad_d}"

def parse_observation(obs: list[int]) -> dict[str, np.ndarray]:
    if len(obs) != 3 * 6 * 6:
        raise RuntimeError(f"Unexpected Pentago observation size: {len(obs)}")
    p0 = np.array([int(v) for v in obs[0 : 6 * 6]]).reshape(6, 6)
    p1 = np.array([int(v) for v in obs[6 * 6 : 2 * 6 * 6]]).reshape(6, 6)
    return {"p0": p0, "p1": p1}


class PentagoGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.turn: int = 0

        self._spiel_game = pyspiel.load_game("pentago")
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("PentagoGame expects a 2-player OpenSpiel game.")

        self.move_count: int = 0
        self._is_done: bool = False
        self._last_stores = None
        self.get_legal_moves()

    def get_observation(self) -> dict[str, np.ndarray]:
        obs = list(self._state.observation_tensor(self.turn))
        parsed = parse_observation(obs)
        return {"you": parsed["p0"], "opponent": parsed["p1"]}

    def get_fixed_observation(self) -> dict[str, Any]:
        obs = list(self._state.observation_tensor(0))
        return parse_observation(obs)

    def get_move(self, move_str: str) -> PentagoMove:
        if ',' in move_str:  # LLM format
            move_str = llm_to_action_str(move_str)
        assert move_str in self.legal_moves_str, f"Invalid or illegal move: {move_str}. Legal moves: {self.legal_moves_str}."
        return self.legal_moves_str[move_str]

    def get_legal_moves(self) -> list[str]:
        if self._is_done:
            return []
        self.legal_moves = set(self._state.legal_actions())
        legal_moves = [PentagoMove(self._state.action_to_string(a), a) for a in self.legal_moves]
        self.legal_moves_str = {m.act_str: m for m in legal_moves}
        return list(self.legal_moves_str.keys())

    def game_step(self, move: PentagoMove) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        if move.action not in self.legal_moves:
            raise ValueError(f"Invalid or illegal move in Pentago: {move}")
        action = move.action
        self._state.apply_action(action)
        self.move_count += 1
        self.get_legal_moves()

        if self._state.is_terminal():
            self._is_done = True
            return

    def current_player(self):
        return self._state.current_player()

    def is_done(self) -> bool:
        return self._is_done

    def get_final_stats(self) -> dict[str, Any]:
        if not self.is_done():
            return {"done": False, "winner": None, "move_count": self.move_count}

        returns = self._state.returns()
        if len(returns) != 2:
            raise RuntimeError("Pentago should be a 2-player game.")

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
            game_name="Pentago on a standard 6x6 board",
            signature_block=(
                "```python\n"
                "def policy(you, opponent) -> str:\n"
                "    ...\n"
                "```"
            ),
            state=[
                "You are always the player to move.",
                "The board is 6x6.",
                "You are given two 6x6 arrays (or array-like objects) containing only 0/1 integers.",
                "`you[r][c] == 1` means your marble is at row `r`, col `c`.",
                "`opponent[r][c] == 1` means the opponent marble is at row `r`, col `c`.",
                "An empty cell means `you[r][c] == 0` and `opponent[r][c] == 0`.",
                "Positions are valid (no overlaps): never `you[r][c] == opponent[r][c] == 1`.",
                "Quadrants are 3x3 sub-boards indexed as:",
                "`quad = 0`: rows 1..3, cols 1..3 (top-left).",
                "`quad = 1`: rows 1..3, cols 4..6 (top-right).",
                "`quad = 2`: rows 4..6, cols 1..3 (bottom-left).",
                "`quad = 3`: rows 4..6, cols 4..6 (bottom-right).",
                "A quadrant rotation rotates the chosen 3x3 sub-board in place and affects BOTH players' marbles in that quadrant.",
                "`L` is 90 degrees anticlockwise; `R` is 90 degrees clockwise.",
                "After placement and rotation, a player wins if they have 5 (or more) marbles in a row in any straight line: horizontal, vertical, or diagonal (either diagonal direction).",
                "If both players have a 5-in-a-row after your move is applied, the result is a draw.",
                "If neither player has a 5-in-a-row and the board is full, the result is a draw.",
            ],
            action=[
                "Return a single string move formatted exactly as: `\"row,col,quad,dir\"`.",
                "`row` is 1..6 (1-indexed).",
                "`col` is 1..6 (1-indexed).",
                "`quad` is 0..3.",
                "`dir` is `L` or `R`.",
                "A legal move must place exactly one of your marbles on an empty cell, then rotate exactly one quadrant 90 degrees in the chosen direction.",
                "Example syntax: `\"6,5,2,L\"` means place at row 6 col 5, then rotate quadrant 2 left.",
                "You may assume at least one empty cell exists (i.e., `policy` is not called when no legal move exists).",
            ],
        )

if __name__ == "__main__":
    config = get_config_file('pentago', 'world1')
    prompt = PentagoGame.get_prompt(config=config)
    print(prompt)
    (Path(__file__).parent / "prompt_example.txt").write_text(prompt)

