import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional, Union

import pyspiel
import numpy as np

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled, render_prompt_for_live_play

ROWS = 4
COLS = 4

@dataclass(frozen=True, order=True)
class Move:
    row: int
    col: int
    direction: str
    action: int

    def get_unparsed_str(self) -> str:
        return f"{self.row},{self.col},{self.direction}"

def human_to_action(s: str) -> Move:
    r, c, d = s.split(',')
    r = int(r)
    c = int(c)
    maxh = (ROWS + 1) * COLS  # 20
    if d == 'H' or d == 'h':
        action = r * COLS + c  # row in [0..4], col in [0..3]
    elif d == 'V' or d == 'v':
        action = maxh + r * (COLS + 1) + c  # row in [0..3], col in [0..4]
    else:
        raise ValueError("direction must be 'H' or 'V'")
    return Move(r, c, d, action)

def action_to_human(action: int) -> str:
    maxh = (ROWS + 1) * COLS  # 20
    if action < maxh:  # Horizontal
        r = action // COLS
        c = action % COLS
        d = 'H'
    else:  # Vertical
        a = action - maxh
        r = a // (COLS + 1)
        c = a % (COLS + 1)
        d = 'V'
    return f"{r},{c},{d}"

def parse_observation(obs: list[int]) -> dict[str, np.ndarray]:
    b = np.array(obs).reshape(3, -1, 3)
    board_size = b.shape[1]
    assert int(np.sqrt(board_size))**2 == board_size, f"Board size {board_size} is not a square"
    bsz = int(np.sqrt(board_size))
    p1 = b[1]
    p2 = b[2]
    single_horiz = p1[:, 0] - p2[:, 0]
    single_vert = p1[:, 1] - p2[:, 1]
    single_capture = p1[:, 2] - p2[:, 2]
    single_horiz = single_horiz.reshape(bsz, bsz)
    single_vert = single_vert.reshape(bsz, bsz)
    single_capture = single_capture.reshape(bsz, bsz)
    return {"horizontal": single_horiz, "vertical": single_vert, "capture": single_capture}

class DotsAndBoxesGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.turn: int = 0

        self._spiel_game = pyspiel.load_game("dots_and_boxes", {"num_rows": 4, "num_cols": 4})
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("Game expects a 2-player OpenSpiel game.")

        self.move_count: int = 0
        self._is_done: bool = False

    def action_to_human(self, action: int) -> str:
        return action_to_human(action)

    def get_observation(self) -> dict[str, np.ndarray]:
        return parse_observation(list(self._state.observation_tensor(self.turn)))


    def get_fixed_observation(self) -> dict[str, Any]:
        return parse_observation(list(self._state.observation_tensor(0)))



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
            return human_to_action(move_str)

    def get_legal_moves(self) -> list[Move]:
        if self._is_done:
            return []
        actions = self._state.legal_actions()
        string_actions = [self._state.action_to_string(x) for x in actions]
        string_actions = [s.split('(')[1].split(')')[0].split(',') for s in string_actions]
        moves = [Move(int(r), int(c), d, a) for (d, r, c), a in zip(string_actions, actions)]

        return moves

    def current_player(self):
        return self._state.current_player()

    def is_done(self) -> bool:
        return self._is_done

    def live_play_is_legal(self, move_str: str) -> bool:
        return move_str in self.live_play_legal_moves()

    def live_play_observation(self) -> dict[str, Any]:
        return {'state': str(self._state), 'move_count': self.move_count}

    def live_play_legal_moves(self) -> list[str]:
        return [move.get_unparsed_str() for move in self.get_legal_moves()]

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

    def get_viz_board(self) -> np.ndarray:
        obs = self.get_observation()
        single_horiz = obs['horizontal']
        single_vert = obs['vertical']
        single_capture = obs['capture'] * 2
        R, C = single_horiz.shape  # expected 5,5
        board = np.zeros((2*R - 1, 2*C - 1), dtype=int)
        # Horizontal edges: valid for c < C-1
        board[0::2, 1::2] = single_horiz[:, :C-1]
        # Vertical edges: valid for r < R-1
        board[1::2, 0::2] = single_vert[:R-1, :]
        # Box ownership / captures: valid for r < R-1 and c < C-1
        board[1::2, 1::2] = single_capture[:R-1, :C-1]
        return board

    @staticmethod
    def get_prompt(config: dict[str, Any], live_play: bool = False) -> str:
        game_name="Dots and Boxes on a 4x4 box grid"
        if live_play:
            return render_prompt_for_live_play(
                game_name=game_name,
                state=[
                    "You are always the player to move.",
                    "The game is Dots and Boxes on a 4x4 grid of boxes.",
                    "`state` is a string representation of the current state of the game.",
                    "On an empty board, all horizontal and vertical edges are empty and only corners are drawn."
                ],
                action=[
                    "Return a string move in the format `'row,col,dir'`.",
                    "`row` and `col` identify which edge to draw and must be integers in the range 0-4.",
                    "`dir` is the edge orientation: `'h'` for a horizontal edge or `'v'` for a vertical edge.",
                    "A move is legal only if the chosen edge is currently empty.",
                    "When you draw an edge, it becomes occupied by you.",
                    "If drawing the edge completes one or more boxes, those boxes become captured by you.",
                    "If you capture at least one box, you immediately take another turn; otherwise the turn passes to the opponent.",
                    "The game ends when all edges are drawn; the winner is the player who captured more boxes.",
                ],
                example_action='"3,0,v"',
            )
        else:
            return render_prompt_pre_filled(
                game_name=game_name,
                signature_block=(
                    "```python\n"
                    "def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:\n"
                    "    ...\n"
                    "```"
                ),
                state=[
                    "You are always the player to move.",
                    "The game is Dots and Boxes on a 4x4 grid of boxes.",
                    "`horizontal`, `vertical`, and `capture` are 5x5 numpy arrays describing the current state.",
                    "All array elements are integers in {-1, 0, 1}.",
                    "`horizontal[row, col]` encodes whether the horizontal edge at `(row, col)` has been drawn (0 = not drawn; nonzero = drawn).",
                    "`vertical[row, col]` encodes whether the vertical edge at `(row, col)` has been drawn (0 = not drawn; nonzero = drawn).",
                    "`capture[row, col]` encodes who owns the box at `(row, col)` (0 = unclaimed; 1 = claimed by you; -1 = claimed by the opponent).",
                    "A nonzero value in `horizontal` or `vertical` indicates the edge is already occupied and cannot be played again (the sign indicates which player drew it).",
                ],
                action=[
                    "Return a string move in the format `'row,col,dir'`.",
                    "`row` and `col` identify which edge to draw and must be integers in the range 0-4.",
                    "`dir` is the edge orientation: `'H'` for a horizontal edge or `'V'` for a vertical edge.",
                    "A move is legal only if the chosen edge is currently empty (its value is 0 in the corresponding array).",
                    "When you draw an edge, it becomes occupied by you (set to 1 in the corresponding array).",
                    "If drawing the edge completes one or more boxes, those boxes become captured by you (set the corresponding `capture` entries to 1).",
                    "If you capture at least one box, you immediately take another turn; otherwise the turn passes to the opponent.",
                    "The game ends when all edges are drawn; the winner is the player who captured more boxes.",
                    "If you are unsure whether a move completes a box, choose a move that is legal and tends to avoid creating a box with exactly three sides filled (which would allow the opponent to score).",
                ],
            )


if __name__ == "__main__":
    config = get_config_file('dots_and_boxes', 'world1')
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-play", action="store_true")
    args = parser.parse_args()
    if args.live_play:
        prompt = DotsAndBoxesGame.get_prompt(config=config, live_play=True)
        print(prompt)
        (Path(__file__).parent / "prompt_example_live_play.txt").write_text(prompt)
    else:
        prompt = DotsAndBoxesGame.get_prompt(config=config)
        print(prompt)
        (Path(__file__).parent / "prompt_example.txt").write_text(prompt)
