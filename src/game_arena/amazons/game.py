from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional, Union

import pyspiel
import numpy as np

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled

@dataclass(frozen=True)
class AmazonsMove:
    r1: int
    c1: int
    r2: int
    c2: int
    r3: int
    c3: int
    action: tuple[int, int, int]
    def get_unparsed_str(self) -> str:
        return action_to_human(self.action)

def human_to_action(s: str) -> AmazonsMove:
    assert s.count(':') == 2
    a1, a2, a3 = s.split(':')
    row1, col1 = [int(x) for x in a1.split(',')]
    row2, col2 = [int(x) for x in a2.split(',')]
    row3, col3 = [int(x) for x in a3.split(',')]
    action = (row1*6+col1, row2*6+col2, row3*6+col3)
    return AmazonsMove(row1, col1, row2, col2, row3, col3, action)

def action_to_human(action: tuple[int, int, int]) -> str:
    a1, a2, a3 = action
    r1, c1 = divmod(a1, 6)
    r2, c2 = divmod(a2, 6)
    r3, c3 = divmod(a3, 6)
    return f"{r1},{c1}:{r2},{c2}:{r3},{c3}" 

def get_observation(obs: list[int], me: int) -> dict[str, np.ndarray]:
    if len(obs) != 4 * 6 * 6:
        raise RuntimeError(f"Unexpected Amazons observation size: {len(obs)}")
    board = np.array([int(v) for v in obs]).reshape(4, 6, 6)
    empty = board[0]
    player1 = board[1]
    player2 = board[2]
    if me == 0:
        pass
    elif me == 1:
        player1, player2 = player2, player1
    else:
        raise ValueError(f"Invalid player: {me}")
    arrows = board[3]
    single_board = 2*player1 + player2 - arrows
    return {"board": single_board}

class AmazonsGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.turn: int = 0

        self._spiel_game = pyspiel.load_game("amazons")
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("AmazonsGame expects a 2-player OpenSpiel game.")

        self.move_count: int = 0
        self._is_done: bool = False

    def get_observation(self) -> dict[str, np.ndarray]:
        obs = list(self._state.observation_tensor())
        return get_observation(obs, self.turn)

    def get_fixed_observation(self) -> dict[str, Any]:
        obs = list(self._state.observation_tensor(0))
        return get_observation(obs, 0)

    def game_step(self, move: Union[AmazonsMove, int]) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        if isinstance(move, AmazonsMove):
            actions = move.action
            player = self.turn
            for i in range(3):
                assert self._state.current_player() == player, f"Current player is {self._state.current_player()} but expected {player}"
                assert actions[i] in self._state.legal_actions(), f"Action {actions[i]} is not legal"
                self._state.apply_action(actions[i])
            assert self._state.current_player() != player, f"Current player is {self._state.current_player()} but expected not {player}"
            self.move_count += 3
        else:
            action = move
            self._state.apply_action(action)
            self.move_count += 1
        self.turn = self._state.current_player()
        if self._state.is_terminal():
            self._is_done = True
            return

    def get_move(self, move_str: str) -> AmazonsMove:
        if isinstance(move_str, int):
            return move_str
        else:
            return human_to_action(move_str)

    def get_legal_moves(self) -> list[str]:
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
        return render_prompt_pre_filled(
            game_name="Amazons on a 6x6 board",
            signature_block=(
                "```python\n"
                "def policy(board) -> str:\n"
                "    ...\n"
                "```"
            ),
            state=[
                "`board` is a 6x6 numpy array (dtype can be int).",
                "Cell values:",
                "  - `0` = empty square",
                "  - `1` = your amazon",
                "  - `2` = opponent amazon",
                "  - `-1` = arrow / blocked square",
                "You may assume the board is valid.",
            ],
            action=[
                "Return a single move string formatted exactly as: "
                "`\"from_row,from_col:to_row,to_col:arrow_row,arrow_col\"`.",
                "All coordinates are 0-indexed with `row,col` in `0..5`.",
                "Example (syntax only): `\"0,1:2,3:3,3\"` moves from (0,1) to (2,3) then shoots an arrow to (3,3).",
                "Your move must be legal and consists of two parts:",
                "  - Move one of your amazons (`board == 1`) from `from` to `to`.",
                "  - From the landing square `to`, shoot an arrow to `arrow`.",
                "Movement rules (queen-like) for both the amazon move and arrow shot:",
                "  - Any positive number of squares in a straight line, orthogonally or diagonally.",
                "  - The path must be unobstructed and may not cross or land on any non-empty square.",
                "    Blockers are: your amazons (`1`), opponent amazons (`2`), and arrows (`-1`).",
                "Additional legality constraints:",
                "  - `from` must contain your amazon (`board[from] == 1`).",
                "  - `to` must be empty in the original position (`board[to] == 0`).",
                "  - For the arrow shot, treat the amazon as having moved to `to` and vacated `from`.",
                "  - `arrow` must be empty after the move; it may pass through the vacated `from` square if unobstructed.",
                "Terminal condition:",
                "  - The last player who can make any legal move wins.",
                "  - The environment should not call `policy` when you have no legal move, but your policy must still be robust.",
            ],
        )

if __name__ == "__main__":
    config = get_config_file('amazons', 'world1')
    prompt = AmazonsGame.get_prompt(config=config)
    print(prompt)
    (Path(__file__).parent / "prompt_example.txt").write_text(prompt)

