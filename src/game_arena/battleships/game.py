import re
import string
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional, Union

import numpy as np
import pyspiel

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled


@dataclass(frozen=True, order=True)
class BattleshipMove:
    row: int
    col: int
    def get_unparsed_str(self) -> str:
        return f"{self.row},{self.col}"


CAPS = set(string.ascii_uppercase)

def _parse_board_block(block: str) -> list[list[int]]:
    # Extract the |...| rows
    rows = []
    for line in block.splitlines():
        if line.startswith("|") and line.endswith("|"):
            rows.append(line[1:-1])  # strip borders
    h = len(rows)
    w = len(rows[0]) if h else 0
    arr = np.zeros((h, w), dtype=np.int8)

    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == "*":
                arr[r, c] = -1
            elif ch in CAPS:
                arr[r, c] = 1
            else:
                arr[r, c] = 0
    return arr.tolist()

def parse_battleship_state(state_str: str) -> tuple[list[list[int]], list[list[int]]]:
    # Split into the two player boards
    # "Player 0's board:\n... \nPlayer 1's board:\n..."
    m = re.split(r"Player 1's board:\n", state_str)
    p0_block = m[0].split("Player 0's board:\n", 1)[1]
    p1_block = m[1]

    p0_board = _parse_board_block(p0_block)
    p1_board = _parse_board_block(p1_block)

    # These boards show enemy shots on each player’s own board.
    # So: p0_board encodes player 1’s shots on player 0.
    # And: p1_board encodes player 0’s shots on player 1.
    p1_shots_on_p0 = p0_board
    p0_shots_on_p1 = p1_board

    return p0_shots_on_p1, p1_shots_on_p0


def parse_move_from_openspiel_str(move_str: str) -> BattleshipMove:
    m = re.search(r'\((\d+)\s*,\s*(\d+)\)', move_str)
    if not m:
        raise ValueError(f"Invalid move string: {move_str!r}")
    i, j = map(int, m.groups())
    return BattleshipMove(i, j)



def _derive_rng(seed):
    """Generator for the game's own randomness (dice / ship placement).

    When no explicit seed is given, derive one from the global numpy RNG, which the
    tournament runner seeds per match (``utils.set_seed(match_seed)``) before creating
    the game.  That keeps the randomness reproducible from the recorded match seed so
    matches can be replayed move by move later.
    """
    if seed is None:
        seed = int(np.random.randint(0, 2**31 - 1))
    return np.random.default_rng(seed)


class BattleshipGame(Game):
    """
    Two-player Battleship-like game

    Board: n x n grid (config['n'])
    Each player has their own hidden fleet of ships, placed randomly without overlap.
    On your turn, you choose a cell (row, col) on the opponent's board to fire at.
    The game ends when one player has all of their ships sunk, or when both players have
    no legal shots left. In the latter case, the player who has sunk more of the
    opponent's ship cells wins (ties are draws).

    Observation for the current player:
        get_observation() -> list[list[int]]

    The observation is an n x n grid of ints describing your knowledge of the opponent's board:
        0  = unknown (you have not fired at this cell yet)
        -1 = miss (you fired here and it was water)
        1  = hit (you fired here and hit a ship; not distinguished by sunk)
    """

    def __init__(self, config: Optional[dict[str, Any]] = None, seed: Optional[int] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.seed: Optional[int] = seed
        self._rng = _derive_rng(self.seed)

        self.n: int = int(self.config['n'])
        self.ship_lengths: list[int] = self.config['ship_lengths']

        self.turn: int = 0
        self.move_count: int = 0
        self._is_done: bool = False

        _str_sizes = '[' + ';'.join(str(l) for l in self.ship_lengths) + ']'
        _str_values = '[' + ';'.join('1' for _ in self.ship_lengths) + ']'
        self._spiel_game = pyspiel.load_game("battleship", {"board_height": self.n, "board_width": self.n, "ship_sizes": _str_sizes, "ship_values": _str_values})
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("Game expects a 2-player OpenSpiel game.")
        self._init_fleet()
        self._update_legal_moves()

    def _init_fleet(self) -> None:
        for i in range(len(self.ship_lengths)):
            action = self._state.legal_actions()
            action = int(self._rng.choice(action))
            self._state.apply_action(action)
            self._state.apply_action(action)

    def get_observation(self) -> dict[str, Any]:
        """
        Return the current player's observation of the opponent's board as an n x n grid:

            0  = unknown
            -1 = miss
            1  = hit
        """
        player_board = parse_battleship_state(str(self._state))[self.turn]
        return {"board": player_board}


    def get_fixed_observation(self) -> dict[str, Any]:
        white, black = parse_battleship_state(str(self._state))
        return {"white": white, "black": black, "turn": self.turn}


    def _update_legal_moves(self) -> None:
        if self._state.is_terminal():
            self._legal_moves_cache = {}
            return

        legal_actions = self._state.legal_actions()
        self._legal_moves_cache = {parse_move_from_openspiel_str(self._state.action_to_string(a)): a for a in legal_actions}


    def get_move(self, move_str: Union[str, tuple[int, int]]) -> BattleshipMove:
        """Parse a move string "row,col" into a BattleshipMove."""
        if isinstance(move_str, tuple):
            return BattleshipMove(int(move_str[0]), int(move_str[1]))
        match = re.match(r".*?(\d+)\s*,\s*(\d+).*", move_str.strip())
        if match:
            row = int(match.group(1))
            col = int(match.group(2))
            return BattleshipMove(row, col)
        raise ValueError(f"Invalid move string: {move_str!r}")

    def get_legal_moves(self) -> list[BattleshipMove]:
        if self._is_done:
            return []
        return sorted(list(self._legal_moves_cache.keys()))

    def game_step(self, move: BattleshipMove) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")

        if move not in self._legal_moves_cache:
            raise ValueError(f"Invalid or repeated move: {move}")
        
        action = self._legal_moves_cache[move]
        self._state.apply_action(action)
        self._update_legal_moves()
        self.move_count += 1

        if self._state.is_terminal():
            self._is_done = True
            return

        self.turn = self._state.current_player()

    def current_player(self) -> int:
        return self.turn

    def is_done(self) -> bool:
        return self._is_done

    def get_final_stats(self) -> dict[str, Any]:
        if not self.is_done():
            return {"done": False, "winner": None, "move_count": self.move_count}

        returns = self._state.returns()
        r0, r1 = returns[0], returns[1]
        if r0 > r1:
            winner = 0
        elif r1 > r0:
            winner = 1
        else:  # draw
            winner = None

        return {
            "done": True,
            "winner": winner,
            "move_count": self.move_count,
            "returns": returns,
        }

    @staticmethod
    def get_prompt(config: dict[str, Any]) -> str:
        n = config["n"]
        ship_lengths = config["ship_lengths"]
        ships_str = ", ".join(str(s) for s in ship_lengths)

        return render_prompt_pre_filled(
            game_name=f"Battleship-like game on an {n}x{n} grid",
            signature_block=(
                "```python\n"
                "def policy(board: list[list[int]]) -> tuple[int, int]:\n"
                "    ...\n"
                "```"
            ),
            state=[
                f"Each player secretly places ships of lengths {ships_str} on their own {n}x{n} grid (no overlaps, straight lines).",
                "`board` is your current knowledge of the opponent grid based on your past shots.",
                "`0` represents an unknown cell (you have not fired here).",
                "`-1` represents a miss (you fired here and hit water).",
                "`1` represents a hit (you fired here and hit a ship cell).",
            ],
            action=[
                f"Return a tuple `(row, col)` with integers in the range `0-{n-1}`.",
                "You must choose a cell you have not previously fired at (i.e., `board[row][col] == 0`).",
                "Objective: sink all opponent ships before they sink yours (or sink more ship cells if neither fleet is fully destroyed).",
            ],
        )

if __name__ == "__main__":
    config = get_config_file('battleships', 'world1')
    prompt = BattleshipGame.get_prompt(config=config)
    print(prompt)
    (Path(__file__).parent / "prompt_example.txt").write_text(prompt)

