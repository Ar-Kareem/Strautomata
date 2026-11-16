from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional, Union

import pyspiel
import numpy as np

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled


# OpenSpiel checkers observation planes (player-relative):
# 0: current player men, 1: current player kings, 2: opponent kings,
# 3: opponent men, 4: empty.
CHECKERS_PLANE_MAP = {
    "cur_men": 0,
    "cur_kings": 1,
    "opp_men": 3,
    "opp_kings": 2,
    "empty": 4,
}

def _reshape_to_planes(obs: Any, board_size: int = 8) -> np.ndarray:
    arr = np.asarray(obs, dtype=np.float32)
    if arr.ndim == 1:
        n = arr.size // (board_size * board_size)
        return arr.reshape(n, board_size, board_size)
    if arr.ndim == 3:
        if arr.shape[0] == board_size and arr.shape[1] == board_size:
            return np.transpose(arr, (2, 0, 1))
        return arr
    raise ValueError(f"Unexpected obs shape: {arr.shape}")

def parse_board(obs: Any, current_player: int, board_size: int = 8) -> dict[str, Any]:
    """
    Parse OpenSpiel checkers observation into a simple piece map.

    Returns: {"my_men": ["a1", ...], "my_kings": [...], "opp_men": [...], "opp_kings": [...]}
    """
    planes = _reshape_to_planes(obs, board_size=board_size)
    if planes.shape[0] < 5:
        raise ValueError(f"Need >=5 planes, got {planes.shape[0]}")

    if current_player not in (0, 1):
        raise ValueError(f"Unexpected current_player: {current_player}")

    my_men: list[tuple[int, int]] = []
    my_kings: list[tuple[int, int]] = []
    opp_men: list[tuple[int, int]] = []
    opp_kings: list[tuple[int, int]] = []

    for row, col in np.argwhere(planes[CHECKERS_PLANE_MAP["cur_men"]] > 0.5):
        my_men.append((7-int(row), int(col)))
    for row, col in np.argwhere(planes[CHECKERS_PLANE_MAP["cur_kings"]] > 0.5):
        my_kings.append((7-int(row), int(col)))
    for row, col in np.argwhere(planes[CHECKERS_PLANE_MAP["opp_men"]] > 0.5):
        opp_men.append((7-int(row), int(col)))
    for row, col in np.argwhere(planes[CHECKERS_PLANE_MAP["opp_kings"]] > 0.5):
        opp_kings.append((7-int(row), int(col)))

    return {
        "my_men": sorted(my_men),
        "my_kings": sorted(my_kings),
        "opp_men": sorted(opp_men),
        "opp_kings": sorted(opp_kings),
        "color": "w" if current_player == 0 else "b",
    }


@dataclass(frozen=True)
class Move:
    llm_output: tuple[tuple[int, int], tuple[int, int]]
    action_str: str


def move_from_llm(move_inp: tuple[tuple[int, int], tuple[int, int]]) -> Move:
    from_coord, to_coord = move_inp
    from_row, from_col = from_coord
    to_row, to_col = to_coord
    # convert to algebraic notation
    from_col_str = chr(ord('a') + from_col)
    to_col_str = chr(ord('a') + to_col)
    action_str = f"{from_col_str}{from_row+1}{to_col_str}{to_row+1}"
    return Move(move_inp, action_str)


def move_from_openspiel_str(move_str: str) -> Move:
    from_col_str = move_str[0]
    from_row = int(move_str[1]) - 1
    to_col_str = move_str[2]
    to_row = int(move_str[3]) - 1
    from_col = ord(from_col_str) - ord('a')
    to_col = ord(to_col_str) - ord('a')
    return Move(((from_row, from_col), (to_row, to_col)), move_str)


class CheckersGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.turn: int = 0

        self._spiel_game = pyspiel.load_game("checkers")
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("Game expects a 2-player OpenSpiel game.")

        self.move_count: int = 0
        self._is_done: bool = False
        self.get_legal_moves()

    def get_observation(self) -> dict[str, np.ndarray]:
        return parse_board(self._state.observation_tensor(self.turn), self.turn)
    
    def get_fixed_observation(self, board_size: int = 8) -> dict[str, Any]:
        board = parse_board(self._state.observation_tensor(0), 0)
        return {
            "white_men": sorted(board["my_men"]),
            "white_kings": sorted(board["my_kings"]),
            "black_men": sorted(board["opp_men"]),
            "black_kings": sorted(board["opp_kings"]),
            "turn": self.turn,
            "legal_moves": self.get_legal_moves(),
        }
    
    def game_step(self, move: Move) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        if move.action_str not in self.legal_moves:
            raise ValueError(f"Invalid or illegal move: '{move}'. Legal moves: {self.legal_moves}. At move count {self.move_count}, state {self.get_observation()}.")
        action = self._state.string_to_action(move.action_str)
        self._state.apply_action(action)
        self.move_count += 1
        self.turn = self._state.current_player()
        self.get_legal_moves()
        if self._state.is_terminal():
            self._is_done = True
            return

    def get_move(self, move_inp: Union[tuple[tuple[int, int], tuple[int, int]], str]) -> Move:
        if isinstance(move_inp, tuple):
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
        return move_str in self.live_play_legal_moves()

    def live_play_observation(self) -> dict[str, Any]:
        return {
            "state": str(self._state),
            "your_character": "w" if self.turn == 0 else "b",
        }

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

    def visualize(self) -> None:
        state = self.get_observation()
        my_color = "w" if self.turn == 0 else "b"
        opp_color = "b" if self.turn == 0 else "w"
        pieces = {}
        for row, col in state["my_men"]:
            pieces[f"{chr(ord('a') + col)}{row+1}"] = f"{my_color}M"
        for row, col in state["my_kings"]:
            pieces[f"{chr(ord('a') + col)}{row+1}"] = f"{my_color}K"
        for row, col in state["opp_men"]:
            pieces[f"{chr(ord('a') + col)}{row+1}"] = f"{opp_color}M"
        for row, col in state["opp_kings"]:
            pieces[f"{chr(ord('a') + col)}{row+1}"] = f"{opp_color}K"
        size = int(state.get("board_size", 8))

        def token(v: str) -> str:
            if not v or len(v) < 2:
                return "."
            color, kind = v[0], v[1]
            if kind == "K":
                return "B" if color == "b" else "W"
            return "b" if color == "b" else "w"

        files = "".join(chr(ord("a") + i) for i in range(size))
        print("   +" + "--" * size + "-+")
        for rank in range(size, 0, -1):
            row = [token(pieces.get(f"{f}{rank}", "")) for f in files]
            print(f"{rank:2d} | " + " ".join(row) + " |")
        print("   +" + "--" * size + "-+")
        print("     " + " ".join(files))
        if state.get("to_play"):
            print(f"To play: {state['to_play']}")

    @staticmethod
    def get_prompt(config: dict[str, Any]) -> str:
        board_size = int(config.get("board_size", 8))
        return render_prompt_pre_filled(
            game_name=f"Checkers on an {board_size}x{board_size} board",
            signature_block=(
                "```python\n"
                "def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:\n"
                "    ...\n"
                "```"
            ),
            state=[
                "You are always the player to move.",
                "`my_men` is a list of squares containing your regular pieces.",
                "`my_kings` is a list of squares containing your kings.",
                "`opp_men` is a list of squares containing opponent regular pieces.",
                "`opp_kings` is a list of squares containing opponent kings.",
                "`color` is your color: `'b'` for black which moves downwards (to lower row values) and `'w'` for white which moves upwards (to higher row values).",
                f"Squares use coordinates: row `0`-`{board_size - 1}`, column `0`-`{board_size - 1}`.",
                "`(0, 0)` is the bottom-left corner; rows increase bottom-to-top and columns increase left-to-right.",
                "Only dark squares are playable.",
            ],
            action=[
                "Return a move as a tuple: `((from_row, from_col), (to_row, to_col))`.",
                f"`from_row`, `to_row`, `from_col`, `to_col` are coordinates `0..{board_size - 1}`.",
                "(`from_row`, `from_col`) has to be a coordinate of a piece that is yours and (`to_row`, `to_col`) has to be the destination square."
                "Return a legal move; captures are mandatory when available.",
            ],
        )


if __name__ == "__main__":
    config = get_config_file('checkers', 'world1')
    prompt = CheckersGame.get_prompt(config=config)
    print(prompt)
    (Path(__file__).parent / "prompt_example.txt").write_text(prompt)
