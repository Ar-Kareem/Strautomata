from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional

import pyspiel

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled


@dataclass(frozen=True)
class MancalaMove:
    action: int

    def get_unparsed_str(self) -> str:
        return str(self.action)


class MancalaGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.turn: int = 0

        self._spiel_game = pyspiel.load_game("mancala")
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("MancalaGame expects a 2-player OpenSpiel game.")

        self.move_count: int = 0
        self._is_done: bool = False
        self._last_stores = None

    def get_observation(self) -> dict[str, list[int]]:
        l1, l2, l3 = str(self._state).splitlines()
        top_houses = [int(x) for x in l1.split('-') if x]
        bottom_houses = [int(x) for x in l3.split('-') if x]
        store_left, store_right = [int(x) for x in l2.split('-') if x]
        # if self._last_stores is not None:
        #     if abs(store_left - self._last_stores[0]) > 1 or abs(store_right - self._last_stores[1]) > 1:
        #         print('CAPTURED!\nCAPTURED!\nCAPTURED!')
        self._last_stores = (store_left, store_right)
        left_player = top_houses[::-1] + [store_left]
        right_player = bottom_houses + [store_right]
        you = right_player if self.turn == 0 else left_player
        other = left_player if self.turn == 0 else right_player
        observation = {"you": you, "opponent": other}
        return observation

    def get_fixed_observation(self) -> dict[str, Any]:
        l1, l2, l3 = str(self._state).splitlines()
        top_houses = [int(x) for x in l1.split('-') if x]
        bottom_houses = [int(x) for x in l3.split('-') if x]
        store_left, store_right = [int(x) for x in l2.split('-') if x]
        if self._is_done:
            # OpenSpiel scores the remaining seeds without sweeping them; show the end-of-game sweep.
            store_left += sum(top_houses)
            store_right += sum(bottom_houses)
            top_houses = [0] * len(top_houses)
            bottom_houses = [0] * len(bottom_houses)
        left_player = top_houses[::-1] + [store_left]
        right_player = bottom_houses + [store_right]
        return {"left_player": left_player, "right_player": right_player}

    def get_move(self, move_str: str) -> MancalaMove:
        move = int(move_str)
        return MancalaMove(move) if move <= 6 else MancalaMove(move - 6)

    def get_legal_moves(self) -> list[MancalaMove]:
        if self._is_done:
            return []
        legal_moves = self._state.legal_actions()
        if self.turn == 0:
            return [MancalaMove(a-1) for a in legal_moves]
        else:
            return [MancalaMove(a-8) for a in legal_moves]

    def game_step(self, move: MancalaMove) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        if move not in self.get_legal_moves():
            raise ValueError(f"Invalid or illegal move in Mancala: {move}")
        action = move.action
        if self.turn == 1:
            action = action + 8
        else:
            action = action + 1

        self._state.apply_action(action)
        self.move_count += 1

        if self._state.is_terminal():
            self._is_done = True
            return
        # if self.turn == self._state.current_player():
        #     print('EXTRA TURN\nEXTRA TURN\nEXTRA TURN\n')
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
            raise RuntimeError("Mancala should be a 2-player game.")

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
            game_name="Kalah on a standard board",
            signature_block=(
                "```python\n"
                "def policy(you: list[int], opponent: list[int]) -> int:\n"
                "    ...\n"
                "```"
            ),
            state=[
                "You are always the player to move.",
                "The game uses 6 houses per side plus 1 store per side.",
                "The state is given as two lists of length 7:",
                "`you = [h0, h1, h2, h3, h4, h5, store]`",
                "`opponent = [h0, h1, h2, h3, h4, h5, store]`",
                "Indices `0..5` are houses; index `6` is that player's store.",
                "All entries are non-negative integers (seed counts).",
                "Game ends when one player has no seeds in all houses (`0..5` all zero).",
                "When the game ends, the other player moves all remaining seeds into their store; higher store total wins (draws possible).",
                "You may assume `policy` is never called when you have no legal move.",
            ],
            action=[
                "Choose an integer move `i` where `0 <= i <= 5` and `you[i] > 0`.",
                "Sow by removing all seeds from `you[i]` and placing them one-by-one in order:",
                "`you[i+1]` through `you[5]`, then `you[6]` (your store), then `opponent[0]` through `opponent[5]`, then `you[0]` through `you[5]`, repeating as needed.",
                "Skip `opponent[6]` (the opponent's store) when sowing.",
                "Extra move: if the last seed lands in `you[6]`, you immediately get another move.",
                "Capture: if the last seed lands in your house `you[i]` (`0..5`) and that house was empty before the drop, and the opposite house `opponent[5 - i]` has seeds, capture the seed in `you[i]` and all seeds in `opponent[5 - i]` into `you[6]`.",
                "You must always return a legal move integer `i` with `you[i] > 0`.",
            ],
        )

if __name__ == "__main__":
    config = get_config_file('mancala', 'world1')
    prompt = MancalaGame.get_prompt(config=config)
    print(prompt)
    (Path(__file__).parent / "prompt_example.txt").write_text(prompt)

