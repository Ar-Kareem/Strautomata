import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional, Union

import pyspiel
import numpy as np

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled, render_prompt_for_live_play


# OpenSpiel Breakthrough observation planes (absolute):
# 0: player 0 pieces, 1: player 1 pieces, 2: empty.
BREAKTHROUGH_PLANE_MAP = {
    "p0": 0,
    "p1": 1,
    "empty": 2,
}


def _algebraic_to_coord(algebraic: str) -> tuple[tuple[int, int], tuple[int, int]]:
    from_col_str = algebraic[0]
    from_row = int(algebraic[1]) - 1
    to_col_str = algebraic[2]
    to_row = int(algebraic[3]) - 1
    from_col = ord(from_col_str) - ord('a')
    to_col = ord(to_col_str) - ord('a')
    return ((from_row, from_col), (to_row, to_col))


@dataclass(frozen=True)
class Move:
    from_row: int
    from_col: int
    to_row: int
    to_col: int
    action_str: str


def move_from_llm(move_inp: tuple[tuple[int, int], tuple[int, int]]) -> Move:
    from_coord, to_coord = move_inp
    from_row, from_col = from_coord
    to_row, to_col = to_coord
    # convert to algebraic notation
    from_col_str = chr(ord('a') + from_col)
    to_col_str = chr(ord('a') + to_col)
    action_str = f"{from_col_str}{from_row+1}{to_col_str}{to_row+1}"
    return Move(from_row, from_col, to_row, to_col, action_str)


def move_from_openspiel_str(move_str: str) -> Move:
    from_coord, to_coord = _algebraic_to_coord(move_str)
    from_row, from_col = from_coord
    to_row, to_col = to_coord
    return Move(from_row, from_col, to_row, to_col, move_str)


def parse_board(obs: list[int], board_size: int = 8) -> dict[str, Any]:
    arr = np.asarray(obs, dtype=np.float32)
    n = arr.size // (board_size * board_size)
    planes = arr.reshape(n, board_size, board_size)
    if planes.shape[0] != 3:
        raise ValueError(f"Need == 3 planes, got {planes.shape[0]}")

    black: list[tuple[int, int]] = []
    white: list[tuple[int, int]] = []
    for row, col in np.argwhere(planes[BREAKTHROUGH_PLANE_MAP["p0"]] > 0.5):
        black.append((7-int(row), int(col)))
    for row, col in np.argwhere(planes[BREAKTHROUGH_PLANE_MAP["p1"]] > 0.5):
        white.append((7-int(row), int(col)))
    return {
        "black": black,
        "white": white,
    }


class BreakthroughGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.turn: int = 0

        self._spiel_game = pyspiel.load_game("breakthrough")
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("Game expects a 2-player OpenSpiel game.")

        self.move_count: int = 0
        self._is_done: bool = False
        self.get_legal_moves()

    def get_observation(self, board_size: int = 8) -> dict[str, Any]:
        """
        Parse OpenSpiel Breakthrough observation into a simple piece map.

        Returns: {"pieces": {"a1":"b", ...}, "to_play": "black"/"white", "board_size": 8}
        """
        turn = self.turn if self.turn >= 0 else 0
        obs = list(self._state.observation_tensor(turn))
        current_player = self.turn
        pieces = parse_board(obs, board_size=board_size)
        black = pieces["black"]
        white = pieces["white"]
        return {
            "me": black if current_player == 0 else white,
            "opp": white if current_player == 0 else black,
            "color": 'b' if current_player == 0 else 'w',
        }
    
    def get_fixed_observation(self, board_size: int = 8) -> dict[str, Any]:
        obs = list(self._state.observation_tensor(0))
        pieces = parse_board(obs, board_size=board_size)
        return {
            "black": pieces["black"],
            "white": pieces["white"],
            "turn": self.turn,
        }
    

    def game_step(self, move: Move) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        action_str = move.action_str
        if action_str not in self.legal_moves:
            if action_str + '*' not in self.legal_moves:
                raise ValueError(f"Invalid or illegal move: '{action_str}'. Legal moves: {self.legal_moves}. At move count {self.move_count}, current player is {self.turn}.")
            action_str = action_str + '*'
        action = self._state.string_to_action(action_str)
        self._state.apply_action(action)
        self.move_count += 1
        self.turn = self._state.current_player()
        self.get_legal_moves()
        if self._state.is_terminal():
            self._is_done = True
            return

    def get_move(self, move_inp: Union[tuple[tuple[int, int], tuple[int, int]], str]) -> Move:
        if isinstance(move_inp, (tuple, list)):
            return move_from_llm(move_inp)
        elif isinstance(move_inp, str):
            return move_from_openspiel_str(move_inp)
        else:
            raise ValueError(f"Invalid move input: {move_inp}")

    def get_legal_moves(self) -> list[str]:
        if self._is_done:
            return []
        self.legal_moves = [self._state.action_to_string(action) for action in self._state.legal_actions()]
        return self.legal_moves

    def current_player(self):
        return self._state.current_player()

    def is_done(self) -> bool:
        return self._is_done

    def live_play_is_legal(self, move_str: str) -> bool:
        return move_str in self.legal_moves

    def live_play_observation(self) -> dict[str, Any]:
        return {'state': self.visualize(return_str=True), 'your_character': 'b' if self.turn == 0 else 'w', 'move_count': self.move_count}
    
    def live_play_legal_moves(self) -> list[str]:
        return self.legal_moves

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

    def visualize(self, return_str: bool = False) -> Optional[str]:
        state = self.get_observation()
        me = state.get("me", []) or []
        opp = state.get("opp", []) or []
        size = int(state.get("board_size", 8))
        me_color = "b" if self.turn == 0 else "w"
        opp_color = "w" if self.turn == 0 else "b"

        def token(row: int, col: int) -> str:
            if (row, col) in me:
                return me_color
            if (row, col) in opp:
                return opp_color
            return "."

        files = "".join(chr(ord("a") + i) for i in range(size))
        s = "  +" + "--" * size + "+" + "\n"
        for rank in range(size, 0, -1):
            row = [token(rank-1, col) for col in range(size)]
            s += f"{rank:2d} | " + " ".join(row) + " |" + "\n"
        s += "  +" + "--" * size + "+" + "\n"
        s += "    " + " ".join(files) + "\n"
        if state.get("to_play"):
            s += f"To play: {state['to_play']}" + "\n"
        if return_str:
            return s
        else:
            print(s)

    @staticmethod
    def get_prompt(config: dict[str, Any], live_play: bool = False) -> str:
        board_size = int(config.get("board_size", 8))
        game_name=f"Breakthrough on an {board_size}x{board_size} board"
        if live_play:
            return render_prompt_for_live_play(
                game_name=game_name,
                state=[
                    "You are always the player to move.",
                ],
                action=[
                    "Return a move as a string in algebraic notation: `a3b4`.",
                    "Movement rules:",
                    "- A piece may move one space straight forward if the target square is empty.",
                    "- A piece may move one space diagonally forward if the target square is empty.",
                    "- A piece may capture only by moving one space diagonally forward onto an opponent piece; the opponent piece is removed.",
                    "- Capturing is not compulsory and is never chained; you can capture at most one piece per turn.",
                    "Win conditions:",
                    "- A piece may not move one space straight forward if the target square is not empty (capturing by going forward is not allowed).",
                    "- You win immediately if any of your pieces reaches the opponent's home row (furthest row from you).",
                    "- You win if all opponent pieces are captured.",
                    "- Draws do not occur in Breakthrough.",
                    "Your move must be legal.",
                ],
                example_action='"a3b4"',
            )
        else:
            return render_prompt_pre_filled(
                game_name=game_name,
                signature_block=(
                    "```python\n"
                    "def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:\n"
                    "    ...\n"
                    "```"
                ),
                state=[
                    "You are always the player to move.",
                    "`me` is a list of (row, col) tuples containing your pieces.",
                    "`opp` is a list of (row, col) tuples containing the opponent's pieces.",
                    "`color` is `'b'` for black which moves downwards (to lower row values) and `'w'` for white which moves upwards (to higher row values).",
                    f"Rows and columns are 0-indexed in `0..{board_size - 1}`.",
                    "Row 0 is the bottom (home row for white); row 7 is the top (home row for black).",
                ],
                action=[
                    "Return a move as a tuple: `((from_row, from_col), (to_row, to_col))`.",
                    "Movement rules:",
                    "- A piece may move one space straight forward if the target square is empty.",
                    "- A piece may move one space diagonally forward if the target square is empty.",
                    "- A piece may capture only by moving one space diagonally forward onto an opponent piece; the opponent piece is removed.",
                    "- Capturing is not compulsory and is never chained; you can capture at most one piece per turn.",
                    "Win conditions:",
                    "- A piece may not move one space straight forward if the target square is not empty (capturing by going forward is not allowed).",
                    "- You win immediately if any of your pieces reaches the opponent's home row (furthest row from you).",
                    "- You win if all opponent pieces are captured.",
                    "- Draws do not occur in Breakthrough.",
                    "Your move must be legal.",
                ],
            )


if __name__ == "__main__":
    config = get_config_file('breakthrough', 'world1')
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-play", action="store_true")
    args = parser.parse_args()
    if args.live_play:
        prompt = BreakthroughGame.get_prompt(config=config, live_play=True)
        print(prompt)
        (Path(__file__).parent / "prompt_example_live_play.txt").write_text(prompt)
    else:
        prompt = BreakthroughGame.get_prompt(config=config)
        print(prompt)
        (Path(__file__).parent / "prompt_example.txt").write_text(prompt)
