from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional, Union

import pyspiel
import numpy as np

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled

@dataclass(frozen=True, order=True)
class Move:
    pile: int
    take: int
    action: int
    def get_unparsed_str(self) -> str:
        return f"{self.pile},{self.take}"

def human_to_action(s: str, num_piles: int) -> Move:
    pile, take = s.split(",")
    pile = int(pile)
    take = int(take)
    action = (take - 1) * num_piles + pile
    return Move(pile, take, action)


def action_to_human(action: int, num_piles: int) -> str:
    pile = action % num_piles
    take = (action // num_piles) + 1
    return f"{pile},{take}"

class NimGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.turn: int = 0

        self._spiel_game = pyspiel.load_game("nim")
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("Game expects a 2-player OpenSpiel game.")

        self.move_count: int = 0
        self._is_done: bool = False

    def action_to_human(self, action: int) -> str:
        return action_to_human(action, self.num_piles)

    def get_observation(self) -> dict[str, Any]:
        tol = 0.5
        board = np.array(self._state.observation_tensor(0))
        L = len(board)
        # Layout: 2 (player) + 1 (terminal) + n (num_piles one-hot) + n*(m+1) (piles)
        # So: L = 3 + n*(m+2), where m = max_num_per_pile
        if L < 6:
            raise ValueError(f"Observation tensor too short: len={L}")

        inferred = None
        for n in range(1, L):  # candidate num_piles
            if (L - 3) % n != 0:
                continue
            m_plus_2 = (L - 3) // n
            m = m_plus_2 - 2
            if m < 0:
                continue
            # num_piles block is length n and, per C++:
            # values[offset + num_piles_ - 1] = 1  ==> the '1' must be at index n-1
            block = board[3 : 3 + n]
            if len(block) != n:
                continue
            if int(block.argmax()) != (n - 1):
                continue
            if block[n - 1] <= tol:
                continue
            # ensure it's effectively one-hot
            if (block > tol).sum() != 1:
                continue
            inferred = (n, m)
            break
        if inferred is None:
            raise ValueError("Could not infer (num_piles, max_num_per_pile) from observation tensor.")
        self.num_piles, self.max_num_per_pile = inferred
        # 2) decode piles
        idx = 3 + self.num_piles
        stride = self.max_num_per_pile + 1
        piles = [int(board[idx + i * stride : idx + (i + 1) * stride].argmax())
                for i in range(self.num_piles)]
        return {"piles": piles}
    
    def get_fixed_observation(self) -> dict[str, Any]:
        return {"piles": self.get_observation()["piles"], "turn": self.turn}

    def game_step(self, move: Union[Move, int]) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        if isinstance(move, Move):
            action = move.action
        else:
            action = move
        if action not in self._state.legal_actions():
            raise ValueError(f"Invalid or illegal move: {action}")
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
            return human_to_action(move_str, self.num_piles)

    def get_legal_moves(self) -> list[int]:
        if self._is_done:
            return []
        actions = self._state.legal_actions()
        string_actions = [self._state.action_to_string(s).rstrip(";") for s in actions]
        moves = []
        for a, s in zip(actions, string_actions):
            pile, take = s.split(", ")
            pile = int(pile.split(":")[1]) - 1
            take = int(take.split(":")[1])
            moves.append(Move(pile, take, a))
        return moves

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
            game_name="Nim (4 piles) with action format 'pile,take'",
            signature_block=(
                "```python\n"
                "def policy(piles: list[int]) -> str:\n"
                "    ...\n"
                "```"
            ),
            state=[
                "You are always the player to move.",
                "`piles`: list[int] of length 4. Each entry is the number of objects remaining in that pile.",
                "Example: `piles = [1, 3, 5, 7]`.",
            ],
            action=[
                "Return a move as a string in the format `'pile,take'` (both are integers, comma-separated, no extra text).",
                "`pile` is the 0-based pile index (0-3).",
                "`take` is how many objects to remove from that pile (must be >= 1).",
                "The move is legal iff `1 <= take <= state['piles'][pile]`.",
                "The game ends when all piles are zero. The player who takes the last object loses.",
                "Your goal is to choose an optimal move (perfect play).",
            ],
        )

if __name__ == "__main__":
    config = get_config_file('nim', 'world1')
    prompt = NimGame.get_prompt(config=config)
    print(prompt)
    (Path(__file__).parent / "prompt_example.txt").write_text(prompt)

