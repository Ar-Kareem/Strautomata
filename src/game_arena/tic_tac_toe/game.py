import re
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass

import pyspiel
import numpy as np

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled

@dataclass(frozen=True, order=True)
class TicTacToeMove:
    row: int
    col: int
    def get_unparsed_str(self) -> str:
        return f"{self.row},{self.col}"

class TicTacToeGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.n = self.config['n']
        self.board: list[list[Optional[str]]] = [[None for _ in range(self.n)] for _ in range(self.n)]
        self._spiel_game = pyspiel.load_game("mnk", {"m": self.n, "n": self.n, "k": self.n})
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("TicTacToeGame expects a 2-player OpenSpiel game.")
        self._is_done = False
        self.turn = 'o'
        self.moves = 0
        self.legal_moves: list[TicTacToeMove] = []
        self._legal_actions: set[int] = set()
        self.winning_lines = get_n_in_a_row(self.n, self.n, self.n)
        self.max_moves = self.n*self.n
        self._update_legal_moves()

    def _action_to_move(self, action: int) -> TicTacToeMove:
        row = action // self.n
        col = action % self.n
        return TicTacToeMove(row, col)

    def _move_to_action(self, move: TicTacToeMove) -> int:
        return move.row * self.n + move.col

    def _update_legal_moves(self) -> None:
        if self._state.is_terminal():
            self._legal_actions = set()
            self.legal_moves = []
            self._is_done = True
            return
        actions = self._state.legal_actions()
        self._legal_actions = set(actions)
        self.legal_moves = [self._action_to_move(a) for a in actions]

    def get_observation(self) -> dict[str, Any]:
        # im +1 and other player is -1
        me = self.turn
        other = {'o': 'x', 'x': 'o'}[me]
        d = {None: 0, me: 1, other: -1}
        return {'board': [[d[cell] for cell in row] for row in self.board]}
    
    def get_fixed_observation(self) -> dict[str, Any]:
        return {'board': [[cell for cell in row] for row in self.board], 'turn': self.turn}

    def get_move(self, move_str: str) -> TicTacToeMove:
        if isinstance(move_str, tuple) and len(move_str) == 2 and isinstance(move_str[0], (np.integer, int)) and isinstance(move_str[1], (np.integer, int)):
            if isinstance(move_str[0], np.integer):
                move0 = move_str[0].item()
            else:
                move0 = int(move_str[0])
            if isinstance(move_str[1], np.integer):
                move1 = move_str[1].item()
            else:
                move1 = int(move_str[1])
            return TicTacToeMove(move0, move1)
        s = str(move_str).strip()
        if s.isdigit():
            s = int(s)-1
            s = f"{s//3},{s%3}"
        match = re.match(r'.*(\d)\s*,\s*(\d).*', s)
        if match:
            return TicTacToeMove(int(match.group(1)), int(match.group(2)))
        raise ValueError(f"Invalid move: {move_str}")

    def get_legal_moves(self) -> list[TicTacToeMove]:
        return self.legal_moves

    def game_step(self, move: TicTacToeMove) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        if move not in self.legal_moves:
            raise ValueError(f"Invalid move: {move}")
        cell_value = self.board[move.row][move.col]
        if cell_value is not None:
            raise ValueError("Cell is already occupied")
        action = self._move_to_action(move)
        if action not in self._legal_actions:
            raise ValueError(f"Invalid or illegal move: {move}")
        self._state.apply_action(action)
        self.legal_moves = self.legal_moves.copy()
        self.legal_moves.remove(move)
        self.board[move.row][move.col] = self.turn
        self.moves += 1
        if self._state.is_terminal():
            self._is_done = True
            return
        self.turn = 'o' if self._state.current_player() == 0 else 'x'
        self._update_legal_moves()
        return

    def current_player(self) -> int:
        return {'o': 0, 'x': 1}[self.turn]

    def check_winner(self):
        for line in self.winning_lines:
            cells = set([self.board[x][y] for x, y in line])
            if len(cells) == 1 and cells != {None}:
                w = cells.pop()
                return {'o': 0, 'x': 1}[w]
        return None
    
    def is_done(self) -> bool:
        return self._is_done

    def get_final_stats(self) -> dict[str, Any]:
        if not self.is_done():
            return {"done": False, "move_count": self.moves}
        winner = self.check_winner()
        return {"done": True, "winner": winner, "move_count": self.moves}

    @staticmethod
    def get_prompt(config: dict[str, Any]) -> str:
        n = config['n']
        return render_prompt_pre_filled(
            game_name=f'{n}x{n} Tic Tac Toe game',
            signature_block=(
                "```python\n"
                "def policy(board: list[list[int]]) -> tuple[int, int]:\n"
                "    ...\n"
                "```"
            ),
            state=[
                f"`board` is a {n}x{n} list of lists.",
                "`0` represents an empty cell.",
                "`1` represents your move.",
                "`-1` represents the opponent's move.",
            ],
            action=[
                f"Return a tuple of two integers `(row, col)` where each is in `0-{n-1}`.",
                "The chosen cell must be empty.",
            ],
        )

def get_n_in_a_row(n, size_x, size_y):
    def in_bounds(x, y):
        return 0 <= x < size_x and 0 <= y < size_y
    deltas = (-1, 0, 1)
    directions = [(dx, dy) for dx in deltas for dy in deltas if (dx, dy) != (0, 0)]
    lines = []
    for x in range(size_x):
        for y in range(size_y):
            for dx, dy in directions:
                prev_x = x - dx
                prev_y = y - dy
                if in_bounds(prev_x, prev_y):
                    continue
                coords = []
                cx, cy = x, y
                for _ in range(n):
                    if not in_bounds(cx, cy):
                        break
                    coords.append((cx, cy))
                    cx += dx
                    cy += dy
                if len(coords) == n:
                    lines.append(tuple(coords))
    # remove duplicate lines
    lines = set(frozenset(line) for line in lines)
    lines = sorted([tuple(sorted(line)) for line in lines])
    return lines




if __name__ == "__main__":
    config = get_config_file('tic_tac_toe', 'world2')
    prompt = TicTacToeGame.get_prompt(config=config)
    print(prompt)
    (Path(__file__).parent / "prompt_example.txt").write_text(prompt)
