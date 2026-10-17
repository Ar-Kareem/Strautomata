import re
import random
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled


CARD_RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
BASE_CARD_VALUES = {
    "A": 11,  # start as 11, then adjust for softness
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 10,
    "Q": 10,
    "K": 10,
}


@dataclass(frozen=True, order=True)
class BlackjackMove:
    """A move in the blackjack game: either HIT or STAY."""
    action: str

    def get_unparsed_str(self) -> str:
        return self.action


class BlackjackGame(Game):
    """
    Variable-target blackjack-like game with two players.
    - Each player has their own independent 13-card single-suit deck:
        A, 2-10, J, Q, K
    - A target T is chosen uniformly at random from [target_min, target_max].
    - On a turn, the current player chooses HIT or STAY.
        HIT: draw next card from their own deck and add to hand.
        STAY: the player is done and will draw no more cards.
    - Aces are soft:
        Start by counting each "A" as 11.
        If total > T, repeatedly convert an Ace from 11 to 1 (-10) until total <= T or no more soft Aces remain.
    - Game ends when both players are done (STAY or bust).
    - Winner:
        If exactly one player busts, the other player wins.
        If both bust, it's a draw.
        If neither busts, whoever has the higher sum <= T wins.
        If sums are equal, it's a draw.
    """

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.target_min: int = self.config["target_min"]
        self.target_max: int = self.config["target_max"]
        self.max_rounds: int = self.config.get("max_rounds", 40)
        if self.target_min > self.target_max:
            raise ValueError("target_min must be <= target_max")
        self.rng = random.Random(random.getrandbits(64))  # derived from the globally seeded RNG so matches are reproducible
        self.target: int = self.rng.randint(self.target_min, self.target_max)

        self.hands: list[list[str]] = [[], []]
        self.done_flags: list[bool] = [False, False]
        self.busted: list[bool] = [False, False]
        self.round_win_counts: list[int] = [0, 0]

        self._is_done: bool = False
        self.turn: int = 0
        self.move_count: int = 0
        self.round: int = 0
        self._hit_move = BlackjackMove("HIT")
        self._stay_move = BlackjackMove("STAY")

        self._new_round()

    def _get_round_winner(self) -> Optional[int]:
        val0 = self._hand_value(0)
        val1 = self._hand_value(1)
        bust0 = self.busted[0]
        bust1 = self.busted[1]
        winner: Optional[int]
        if bust0 and not bust1:
            winner = 1
        elif bust1 and not bust0:
            winner = 0
        elif bust0 and bust1:  # both bust: draw
            winner = None
        else:  # neither busted
            if val0 > val1:
                winner = 0
            elif val1 > val0:
                winner = 1
            else:
                winner = None
        return winner

    def _new_round(self) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        if self.round == 0:  # first round; ok
            pass
        elif all(self.done_flags):  # all players are done; ok
            pass
        else:  # some player is not done; error
            raise ValueError("Some player is not done")
        self.round += 1
        if self.round > self.max_rounds:
            self._is_done = True
            return
        winner = self._get_round_winner()
        if winner is not None:
            self.round_win_counts[winner] += 1
        deck1 = CARD_RANKS.copy()
        self.rng.shuffle(deck1)
        deck2 = deck1.copy()
        self.decks = [deck1, deck2]
        for player in (0, 1):
            self.done_flags[player] = False
            self.busted[player] = False
            self.hands[player] = []
            self._deal_card(player)
        self.turn = 0

    def _hand_value(self, player: int) -> int:
        """Compute the hand value for a player using soft Aces."""
        cards = self.hands[player]
        total = sum(BASE_CARD_VALUES[card] for card in cards)
        ace_count = cards.count("A")
        while total > self.target and ace_count > 0:
            total -= 10
            ace_count -= 1
        return total

    def _deal_card(self, player: int) -> None:
        """Deal the next card from the player's deck into their hand."""
        assert self.done_flags[player] is False, "Player is done"
        card = self.decks[player].pop()
        self.hands[player].append(card)

    def _advance_turn(self) -> None:
        """Advance turn to the next player who is not done, or mark game done."""
        for _ in range(2):
            self.turn = 1 - self.turn
            if not self.done_flags[self.turn]:
                return
        raise ValueError("All players are done")

    def get_observation(self) -> dict[str, Any]:
        return {'hand': list[str](self.hands[self.turn]), 'target': self.target}

    def get_move(self, move_str: str) -> BlackjackMove:
        s = move_str.strip().lower()
        if re.match(r"\s*hit\s*", s) or re.match(r"\s*h\s*", s):
            return self._hit_move
        if re.match(r"\s*stay\s*", s) or re.match(r"\s*s\s*", s):
            return self._stay_move
        raise ValueError(f"Invalid move: {move_str!r}")

    def get_legal_moves(self) -> list[BlackjackMove]:
        assert self.done_flags[self.turn] is False, "Player is done"
        return [self._hit_move, self._stay_move]

    def game_step(self, move: BlackjackMove) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        assert self.done_flags[self.turn] is False, "Player is done"
        if move.action not in ("HIT", "STAY"):
            raise ValueError(f"Invalid move: {move}")
        player = self.turn
        self.move_count += 1
        if move.action == "STAY":
            self.done_flags[player] = True
        else:  # "HIT"
            if self.decks[player]:
                self._deal_card(player)
                total = self._hand_value(player)
                if total > self.target:  # player busts
                    self.busted[player] = True
                    self.done_flags[player] = True
            else:
                self.done_flags[player] = True
        if all(self.done_flags):
            self._new_round()
            return
        self._advance_turn()

    def current_player(self) -> int:
        return self.turn

    def is_done(self) -> bool:
        return self._is_done

    def get_final_stats(self) -> dict[str, Any]:
        if not self.is_done():
            return {"done": False, "move_count": self.move_count}
        if self.round_win_counts[0] > self.round_win_counts[1]:
            winner = 0
        elif self.round_win_counts[1] > self.round_win_counts[0]:
            winner = 1
        else:
            winner = None
        return {
            "done": True,
            "winner": winner,
            "move_count": self.move_count,
            "target": self.target,
            "round_win_counts": self.round_win_counts,
        }

    @staticmethod
    def get_prompt(config: dict[str, Any]) -> str:
        target_min = config["target_min"]
        target_max = config["target_max"]

        return render_prompt_pre_filled(
            game_name=(
                "a simplified Blackjack-like game "
                f"(target score T is a random integer between {target_min} and {target_max} and is provided as input)"
            ),
            signature_block=(
                "```python\n"
                "def policy(hand: list[str], target: int) -> str:\n"
                "    ...\n"
                "```"
            ),
            state=[
                "The game is played with a single suit of 13 distinct cards: "
                '`"A"`, `"2"`, `"3"`, `"4"`, `"5"`, `"6"`, `"7"`, `"8"`, `"9"`, `"10"`, `"J"`, `"Q"`, `"K"`.',
                "You have your own 13-card deck (one copy of each rank), and your opponent has their own separate 13-card deck.",
                "Card values are defined as:",
                '`"2"`-`"10"` → their face value (2-10).',
                '`"J"`, `"Q"`, `"K"` → 10.',
                '`"A"` → 11 when the hand value is <= `target`, or 1 when the hand value is > `target`.',
                "At the start of a game, a target score `T` is chosen at random and fixed for the entire game.",
                "On each call to `policy` you observe:",
                "`hand`: the list of strings representing the cards you currently hold.",
                "`target`: the integer `T` you are trying to approach.",
            ],
            action=[
                'Return one of the two actions as a string: `"HIT"` or `"STAY"`.',
                '`"HIT"`: draw the next card from your deck.',
                '`"STAY"`: stop drawing cards for the rest of the game.',
                "If at any point the sum of your card values is greater than `target`, you bust and stop drawing cards.",
                "If only you bust, you lose. If only the opponent busts, you win. If both bust, the game is a draw.",
                "If neither busts, the player whose sum is closer to `target` wins.",
            ],
        )

if __name__ == "__main__":
    config = get_config_file('blackjack', 'world1')
    prompt = BlackjackGame.get_prompt(config=config)
    print(prompt)
    (Path(__file__).parent / "prompt_example.txt").write_text(prompt)

