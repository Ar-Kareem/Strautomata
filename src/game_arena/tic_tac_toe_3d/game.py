import re
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass

import numpy as np

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled


@dataclass(frozen=True)
class TicTacToeMove:
    d1: int
    d2: int
    d3: int
    def get_unparsed_str(self) -> str:
        return f"({self.d1}, {self.d2}, {self.d3})"

class TicTacToe3D(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.n = self.config['n']
        self.board: list[list[list[Optional[str]]]] = [[[None for _ in range(self.n)] for _ in range(self.n)] for _ in range(self.n)]
        self._is_done = False
        self.turn = 'o'
        self.moves = 0
        self.legal_moves = [TicTacToeMove(d1, d2, d3) for d1 in range(self.n) for d2 in range(self.n) for d3 in range(self.n)]

        self.winning_lines = get_n_in_a_row(self.n, self.n, self.n, self.n)
        self.max_moves = self.n*self.n*self.n

    def get_observation(self) -> dict[str, list[list[list[int]]]]:
        # im +1 and other player is -1
        me = self.turn
        other = {'o': 'x', 'x': 'o'}[me]
        d = {None: 0, me: 1, other: -1}
        return {'board': [[[d[cell] for cell in row] for row in layer] for layer in self.board]}

    def get_fixed_observation(self) -> dict[str, list[list[list[int]]]]:
        d = {None: 0, 'o': 1, 'x': -1}
        return {'board': [[[d[cell] for cell in row] for row in layer] for layer in self.board]}

    def get_move(self, move_str: str) -> TicTacToeMove:
        if isinstance(move_str, tuple) and len(move_str) == 3 and all(isinstance(x, np.integer) for x in move_str):
            return TicTacToeMove(move_str[0].item(), move_str[1].item(), move_str[2].item())  # type: ignore
        # parse (\d, \d, \d)
        match = re.match(r'\((\d)\s*,\s*(\d)\s*,\s*(\d)\)', str(move_str))
        move = None
        if match:
            move = TicTacToeMove(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        if move is None:
            match = re.match(r'(\d)\s*,\s*(\d)\s*,\s*(\d)', move_str)
            if match:
                move = TicTacToeMove(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        if move is None:
            raise ValueError(f"Invalid move: {move_str}")
        return move

    def get_legal_moves(self) -> list[TicTacToeMove]:
        return self.legal_moves

    def game_step(self, move: TicTacToeMove) -> None:
        if move not in self.legal_moves:
            raise ValueError(f"Not legal move in current state: {move}")
        cell_value = self.board[move.d1][move.d2][move.d3]
        if cell_value is not None:
            raise ValueError("Cell is already occupied")
        self.legal_moves = self.legal_moves.copy()
        self.legal_moves.remove(move)
        self.board[move.d1][move.d2][move.d3] = self.turn
        self.moves += 1
        w = self.check_winner()
        if w is not None:
            self._is_done = True
            return
        if self.moves == self.max_moves:
            self._is_done = True
            return
        self.turn = {'o': 'x', 'x': 'o'}[self.turn]
        return

    def current_player(self) -> int:
        return {'o': 0, 'x': 1}[self.turn]

    def check_winner(self):
        for line in self.winning_lines:
            cells = set([self.board[d1][d2][d3] for d1, d2, d3 in line])
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
        n = config["n"]
        return render_prompt_pre_filled(
            game_name=f"{n}x{n}x{n} 3D Tic Tac Toe game",
            signature_block=(
                "```python\n"
                "def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:\n"
                "    ...\n"
                "```"
            ),
            state=[
                f"`board` is a {n}x{n}x{n} list of lists of lists.",
                "`0` represents an empty cell.",
                "`1` represents your move.",
                "`-1` represents the opponent's move.",
                "Example: `[[[0, 0, 1], ...]]` indicates the first line in the first 2 dimensions has two empty cells, and the last cell occupied by you.",
            ],
            action=[
                f"Return a tuple of three integers `(i, j, k)` where each is in `0-{n-1}`.",
                "The chosen cell must be empty.",
                "The first integer corresponds to the first dimension of the input board, the second to the second dimension, and the third to the third dimension.",
            ],
        )

def get_n_in_a_row(n, size_x, size_y, size_z):
    def in_bounds(x, y, z):
        return 0 <= x < size_x and 0 <= y < size_y and 0 <= z < size_z
    deltas = (-1, 0, 1)
    directions = [(dx, dy, dz) for dx in deltas for dy in deltas for dz in deltas if (dx, dy, dz) != (0, 0, 0)]
    lines = []
    for x in range(size_x):
        for y in range(size_y):
            for z in range(size_z):
                for dx, dy, dz in directions:
                    prev_x = x - dx
                    prev_y = y - dy
                    prev_z = z - dz
                    if in_bounds(prev_x, prev_y, prev_z):
                        continue
                    coords = []
                    cx, cy, cz = x, y, z
                    for _ in range(n):
                        if not in_bounds(cx, cy, cz):
                            break
                        coords.append((cx, cy, cz))
                        cx += dx
                        cy += dy
                        cz += dz
                    if len(coords) == n:
                        lines.append(tuple(coords))
    # remove duplicate lines
    lines = set(frozenset(line) for line in lines)
    lines = sorted([tuple(sorted(line)) for line in lines])
    return lines


if __name__ == "__main__":
    config = get_config_file('tic_tac_toe_3d', 'world1')
    prompt = TicTacToe3D.get_prompt(config=config)
    print(prompt)
    (Path(__file__).parent / "prompt_example.txt").write_text(prompt)

