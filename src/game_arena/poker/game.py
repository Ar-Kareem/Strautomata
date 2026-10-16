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
    name: str
    action: int

def human_to_action(s: str) -> Move:
    # 0 → Fold
    # 1 → Call
    # 2 → Raise
    # 3 → All-in
    if s.lower() == 'fold':
        return Move(s, 0)
    elif s.lower() == 'call' or s.lower() == 'check':
        return Move(s, 1)
    elif s.lower() == 'raise':
        return Move(s, 2)
    elif s.lower().replace('-', '') == 'allin':
        return Move(s, 3)
    else:
        raise ValueError(f"Invalid poker move: {s}")

def action_to_human(action: int) -> str:
    return {0: 'fold', 1: 'call', 2: 'raise', 3: 'all-in'}[action]

class PokerGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.turn: int = 0
        self.chips = [6_000, 6_000]

        self._spiel_game = pyspiel.load_game("universal_poker")
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("Game expects a 2-player OpenSpiel game.")

        self.move_count: int = 0
        self._is_done: bool = False
        self.do_chance_if_needed()

    def action_to_human(self, action: int) -> str:
        return action_to_human(action)

    def get_observation(self) -> dict[str, Any]:
        """
        Parse OpenSpiel Universal Poker observation_tensor into a minimal, human-readable dict.

        Observation layout (from open_spiel/games/universal_poker/universal_poker.cc):
        [0 : P)                  -> one-hot "who I am" / observer player id
        [P : P + C)              -> my private cards (one-hot over deck cards)
        [P + C : P + 2C)         -> public/board cards (one-hot over deck cards)
        [P + 2C : P + 2C + P)    -> each player's current contribution/spent (numeric)

        Returns only what is typically required to act well on the next decision:
        - player_id (the observing player)
        - private_cards, public_cards (decoded as {rank, suit})
        - contributions, pot, to_call (derived from contributions)
        - max_spent (table max contribution so far)
        """
        b = list(self._state.observation_tensor())
        n = len(b)
        def _is01(x: float, eps: float = 1e-6) -> bool:
            return abs(x - 0.0) < eps or abs(x - 1.0) < eps
        # Infer num_players P (OpenSpiel poker max is 10, min is 2).
        P = None
        for p in range(2, 11):
            if n - 2 * p <= 0 or (n - 2 * p) % 2 != 0:
                continue
            head = b[:p]
            if all(_is01(x) for x in head) and abs(sum(head) - 1.0) < 1e-6:
                P = p
                break
        assert P is not None, "Could not infer num_players from tensor prefix. Expected a one-hot prefix of length 2..10."
        C = (n - 2 * P) // 2  # total_cards = num_suits * num_ranks
        assert C > 0, "Invalid deck size inferred from observation tensor."
        # Infer num_suits/num_ranks (default games are almost always 4 suits).
        num_suits = next((s for s in (4, 5, 6, 8, 2, 3, 7, 9, 10) if C % s == 0), 1)
        num_ranks = C // num_suits

        def decode_card(idx: int) -> dict[str, int]:
            # Card indexing in this codebase is rank-major: idx = rank * num_suits + suit.
            return {"rank": idx // num_suits, "suit": idx % num_suits}

        player_id = int(max(range(P), key=lambda i: b[i]))

        priv = b[P : P + C]
        pub = b[P + C : P + 2 * C]
        contributions = [float(x) for x in b[P + 2 * C : P + 2 * C + P]]

        private_cards = [decode_card(i) for i, v in enumerate(priv) if v > 0.5]
        public_cards = [decode_card(i) for i, v in enumerate(pub) if v > 0.5]

        max_spent = max(contributions) if contributions else 0.0
        my_spent = contributions[player_id] if 0 <= player_id < len(contributions) else 0.0
        to_call = max(0.0, max_spent - my_spent)
        pot = sum(contributions)
        opponent_spent = pot - my_spent

        return {'state': {
            # "deck": {"num_suits": num_suits, "num_ranks": num_ranks, "num_cards": C},
            "private_cards": private_cards,   # list[{"rank": r, "suit": s}]
            "public_cards": public_cards,     # list[{"rank": r, "suit": s}]
            "pot": pot,
            "my_spent": my_spent,
            "opponent_spent": opponent_spent,
            "to_call": to_call,
            "allowed_actions": [action_to_human(a) for a in self._state.legal_actions()],
        }}

    def game_step(self, move: Union[Move, int]) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        if isinstance(move, Move):
            action = move.action
        else:
            action = move
        if action not in self._state.legal_actions():
            raise ValueError(f"Invalid or illegal move in Poker: {action_to_human(action)}. Current observation: {self.get_observation()}")
        self._state.apply_action(action)
        self.move_count += 1

        self.do_chance_if_needed()
        if self._state.is_terminal():
            # print('new game. Current chips:', self.chips)
            returns = self._state.returns()
            self.chips[0] += returns[0]
            self.chips[1] += returns[1]
            self._state = self._spiel_game.new_initial_state()
            self.do_chance_if_needed()
        self.turn = self._state.current_player()
        if any([c <= 0 for c in self.chips]):
            self._is_done = True
            return

    def do_chance_if_needed(self) -> None:
        while self._state.is_chance_node():
            outcomes = self._state.chance_outcomes()
            action_list, prob_list = zip(*outcomes)
            action = np.random.choice(action_list, p=prob_list)
            self._state.apply_action(action)

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

        returns = self.chips
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
            game_name="Poker (Hold 'em) game",
            signature_block=(
                "```python\n"
                "def policy(state: dict) -> str:\n"
                "    ...\n"
                "```"
            ),
            state=[
                "You are always the player to move.",
                "This is a two-player poker game.",
                "The game state is given as a dictionary called `state` with the following fields:",
                "`state['private_cards']`: a list of your hole cards. Each card is a dict: {'rank': int, 'suit': int}. Currently always exactly one card.",
                "`state['public_cards']`: a list of board cards (same card format). Possibly empty.",
                "`state['pot']`: total number of chips in the pot.",
                "`state['my_spent']`: how many chips you have committed to the pot so far.",
                "`state['opponent_spent']`: how many chips the opponent has committed to the pot so far.",
                "`state['to_call']`: how many chips you must add to match the current bet. If 0, you may check.",
                "`state['allowed_actions']`: a list of legal actions you can take. Possible values: 'fold', 'call', 'raise', 'all-in'. This informs you if its legal to fold or raise for example.",
                "Ranks and suits are integers only; you must reason about hand strength yourself.",
                "The game ends automatically when all betting is complete or when a player folds.",
                "Your goal is to maximize your final chip return (zero-sum).",
            ],
            action=[
                "You must return exactly one of the following strings: 'fold', 'call', 'raise', or 'all-in'.",
                "'fold': concede the hand and lose any chips you have already committed. You are not allowed to fold in the very first round when both players only have 100 chips in the pot.",
                "'call': if `to_call` > 0, match the opponent's bet; if `to_call` == 0, this is a check.",
                "'raise': increase the current bet by the system-defined amount. The system calculates the current pot after you call then raises by one pot. (raise_to = current_max_bet + pot_after_call)",
                "'all-in': commit your entire remaining stack to the pot.",
                "You may assume the policy is only called when at least one legal action exists.",
                "Always return a single action string and nothing else.",
            ],
        )

if __name__ == "__main__":
    config = get_config_file('poker', 'world1')
    prompt = PokerGame.get_prompt(config=config)
    print(prompt)
    (Path(__file__).parent / "prompt_example.txt").write_text(prompt)

