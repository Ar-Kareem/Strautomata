from pathlib import Path
import argparse
from dataclasses import dataclass
from typing import Any, Optional, Union

import pyspiel
import numpy as np

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_for_live_play, render_prompt_pre_filled
from game_arena.chess.san import san_to_uci

# Plane indices for OpenSpiel chess (first 12 planes).
# Order is by piece type with black then white: K, Q, R, B, N, P.
CHESS_PLANE_MAP = [
    ("w", "K"),
    ("b", "K"),
    ("w", "Q"),
    ("b", "Q"),
    ("w", "R"),
    ("b", "R"),
    ("w", "B"),
    ("b", "B"),
    ("w", "N"),
    ("b", "N"),
    ("w", "P"),
    ("b", "P"),
]

@dataclass(frozen=True)
class Move:
    action: str

def _reshape_to_planes(obs: Any, board_size: int = 8) -> np.ndarray:
    arr = np.asarray(obs, dtype=np.float32)
    if arr.ndim == 1:
        n = arr.size // (board_size * board_size)
        return arr.reshape(n, board_size, board_size)
    if arr.ndim == 3:
        # accept (H,W,C) or (C,H,W)
        if arr.shape[0] == board_size and arr.shape[1] == board_size:
            return np.transpose(arr, (2, 0, 1))
        return arr
    raise ValueError(f"Unexpected obs shape: {arr.shape}")

def parse_board(obs: np.ndarray, board_size: int = 8) -> dict[str, Any]:
    if obs.shape[0] < 12:
        raise ValueError(f"Need >=12 obs, got {obs.shape[0]}")

    # Convert square coords to human square names with white-at-bottom convention.
    # OpenSpiel chess observations are indexed from the top-left (rank 8, file a).
    def to_sq(col: int, row: int) -> str:
        rank = board_size - row
        return f"{chr(ord('a') + col)}{rank}"

    pieces: dict[str, str] = {}

    for idx, (color, piece) in enumerate(CHESS_PLANE_MAP):
        rows, cols = np.where(obs[idx] > 0.5)
        for row, col in zip(rows.tolist(), cols.tolist()):
            pieces[to_sq(int(col), 7-int(row))] = f"{color}{piece}"

    return pieces

class ChessGame(Game):
    LIVE_SEAT_SWAPPER: type["ChessGame"]  # for frontend; player 0 is white not black

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}

        self._spiel_game = pyspiel.load_game("chess")
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("Game expects a 2-player OpenSpiel game.")

        self.turn: int = self._state.current_player()
        self.move_count: int = 0
        self._is_done: bool = False
        self.legal_moves: list[str] = []
        self.san_to_dict: dict[str, dict] = {}
        self.get_observation(with_legal_moves=False)
        self.get_legal_moves()

    def get_observation(self, board_size: int = 8, fixed_observation: bool = False, with_legal_moves: bool = False) -> dict[str, Any]:
        """
        Robust OpenSpiel chess observation parser:
        - planes 0..5: current player pieces
        - planes 6..11: opponent pieces
        - piece-type plane order inferred by occupancy patterns

        Returns: {"pieces": {"e4":"wP", ...}, "to_play": "white"/"black"}
        """
        planes = _reshape_to_planes(self._state.observation_tensor(0), board_size=board_size)
        to_play = {0: "black", 1: "white"}.get(self.turn, None)
        pieces = parse_board(planes)
        if with_legal_moves:
            legal_moves_dict = {"legal_moves": self.get_legal_moves()}
        else:
            legal_moves_dict = {}
        return {
            "pieces": pieces,
            "to_play": to_play,
            **legal_moves_dict,
        }

    def get_fixed_observation(self, board_size: int = 8) -> dict[str, Any]:
        planes = _reshape_to_planes(self._state.observation_tensor(0), board_size=board_size)
        pieces = parse_board(planes, board_size=board_size)
        return {
            "pieces": pieces,
            "turn": self.turn,
            "legal_moves": self.get_legal_moves(),
        }

    def game_step(self, move: Union[Move, int, str]) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        if isinstance(move, Move):
            action = move.action
        else:
            action = move
            
        self._state.apply_action(action)
        self.move_count += 1
        self.turn = self._state.current_player()
        if self._state.is_terminal():
            self._is_done = True
            return
        self.get_legal_moves()

    def get_move(self, move_str: Union[str, int]) -> Union[Move, int]:
        if isinstance(move_str, int):
            return move_str
        elif move_str in self.legal_moves:
            return self._state.string_to_action(move_str)
        elif move_str in self.uci_to_san:
            return self._state.string_to_action(self.uci_to_san[move_str])
        else:
            raise ValueError(f"Invalid move_str: {move_str}. legal move_strs: {self.legal_moves}. uci_to_san: {self.uci_to_san}")

    def get_legal_moves(self) -> list[str]:
        if self._is_done:
            return []
        obs = self.get_observation(with_legal_moves=False)
        pieces = obs['pieces']
        self.legal_moves = [self._state.action_to_string(i) for i in self._state.legal_actions()]
        uci_list = [san_to_uci(move, pieces, ['b', 'w'][self.turn]) for move in self.legal_moves]
        self.uci_to_san = {uci: move for uci, move in zip(uci_list, self.legal_moves)}
        return list(self.uci_to_san.keys())

    def live_play_is_legal(self, move_str: str) -> bool:
        return move_str in self.legal_moves or move_str in self.uci_to_san

    def live_play_observation(self) -> dict[str, Any]:
        return {'state': str(self._state)}
    
    def live_play_legal_moves(self) -> list[str]:
        return list(self.uci_to_san.keys())

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

    def print_board_ascii(self) -> None:
        state = self.get_observation()
        pieces = state.get("pieces", {}) or {}

        def token(v: str) -> str:
            if not v or len(v) < 2:
                return "."
            c, p = v[0], v[1]
            return p.upper() if c == "w" else p.lower()

        files = "abcdefgh"
        print("  +-----------------+")
        for rank in range(8, 0, -1):
            row = [token(pieces.get(f"{f}{rank}", "")) for f in files]
            print(f"{rank} | " + " ".join(row) + " |")
        print("  +-----------------+")
        print("    a b c d e f g h")
        if state.get("to_play"):
            print(f"To play: {state['to_play']}")

    def visualize(self) -> None:
        self.print_board_ascii()

    @staticmethod
    def get_prompt(config: dict[str, Any], live_play: bool = False) -> str:
        memory = config.get("memory", False)
        assert not memory or not live_play, 'Cant have both memory and live play.'
        game_name="Chess (move selection from provided legal moves)"

        if memory:  # with memory
            mem_parameter = ', memory: dict'
            mem_state = [
                "`memory` is an empty dictionary that you may use however you want to store information between calls.",
                "You may use and store anything in `memory` and store any keys and values you want (even leave it empty).",
            ]
            ret_type = 'tuple[str, dict]'
            return_actions = [
                "Return a tuple `(action, memory)` where `memory` is a dictionary that you will receive next call.",
                "`action` is a move string that is an element of `legal_moves`.",
            ]
        else:  # without memory
            mem_parameter = ''
            mem_state = []
            ret_type = 'str'
            return_actions = [
                "Return exactly ONE move string that is an element of `legal_moves`.",
            ]

        signature_block=(
            "```python\n"
            f"def policy(pieces: dict[str, str], to_play: str{mem_parameter}) -> {ret_type}:\n"
            "    ...\n"
            "```"
        )
        state=[
            *mem_state,
            "You are always the player whose turn it is (given by `to_play`).",
            "`pieces` is a dictionary mapping squares to piece codes, e.g. `{'e1': 'bK', 'f3': 'wR'}`.",
            "Squares are in algebraic coordinates: file `a`-`h` and rank `1`-`8` (e.g. `'e4'`).",
            "Piece codes are two characters: color + piece type.",
            "Colors: `'w'` = White, `'b'` = Black.",
            "Piece types: `K` King, `Q` Queen, `R` Rook, `B` Bishop, `N` Knight, `P` Pawn.",
            "`to_play` is either `'white'` or `'black'`.",
            "For example: pieces: {'f1': 'wK', 'd1': 'bK', 'a4': 'wN', 'h3': 'wP', 'a5': 'wP', 'h4': 'bP'}, to_play = 'white'",
            "You are not allowed to import the `chess` module. You are allowed to import other python modules or numpy."
        ]
        action=[
            *return_actions,
            "Do not return any extra text, commentary, or formatting—only the move string.",
            "The move strings is a UCI move string and almost always 4 characters long. Examples: `'b4b5', 'g3e1', etc. Castling is simply represented as a king move (e1g1, e1c1, e8g8, e8c8)",
            "The only time the move strings is longer than 4 characters is when a pawn promotion is involved. Examples: 'a2a1r', 'a2a1b', 'a2a1n', 'a2a1q' moves the pawn from a2 to a1 and promotes it to one of four piece types."
            "The move strings does not include any extra characters for captures, checks, or disambiguation.",
            "Example format of `legal_moves` you might receive:",
            " `['f5e4', 'f5f4', 'g3d6', 'g3e1', 'g3e5', 'g3f2', 'g3f4', 'g3h2', ...]`",
            "Your goal is to choose the strongest move under standard chess objectives: prioritize checkmate if available; otherwise prioritize winning material, improving king safety, and preventing immediate threats.",
        ]
        if live_play:
            return render_prompt_for_live_play(
                game_name=game_name,
                state=state,
                action=action,
                example_action='"Be4"',
            )
        else:
            return render_prompt_pre_filled(
                game_name=game_name,
                signature_block=signature_block,
                state=state,
                action=action,
            )


class ChessGameSeatSwapped(ChessGame):
    """Live website matches only: player indices are seats (0 = automaton A = white) instead of
    OpenSpiel's (0 = black). Bot observations are unchanged; replays and offline tournaments use ChessGame."""

    @staticmethod
    def _seat(player: Any) -> Any:
        return 1 - player if player in (0, 1) else player

    def current_player(self):
        return self._seat(super().current_player())

    def get_fixed_observation(self, board_size: int = 8) -> dict[str, Any]:
        obs = super().get_fixed_observation(board_size)
        return {**obs, "turn": self._seat(obs["turn"])}

    def get_final_stats(self) -> dict[str, Any]:
        stats = super().get_final_stats()
        if stats.get("winner") is not None:
            stats = {**stats, "winner": self._seat(stats["winner"])}
        if "returns" in stats:
            stats = {**stats, "returns": list(stats["returns"])[::-1]}
        return stats


ChessGame.LIVE_SEAT_SWAPPER = ChessGameSeatSwapped


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-play", action="store_true")
    parser.add_argument("--memory", action="store_true")
    args = parser.parse_args()
    assert not args.live_play or not args.memory, 'Cant have both live play and memory.'
    config = get_config_file('chess', 'world1' if not args.memory else 'worldmem1')
    if args.live_play:
        prompt = ChessGame.get_prompt(config=config, live_play=True)
        print(prompt)
        (Path(__file__).parent / "prompt_example_live_play.txt").write_text(prompt)
    elif args.memory:
        prompt = ChessGame.get_prompt(config=config)
        print(prompt)
        (Path(__file__).parent / "prompt_example_memory.txt").write_text(prompt)
    else:
        prompt = ChessGame.get_prompt(config=config)
        print(prompt)
        (Path(__file__).parent / "prompt_example.txt").write_text(prompt)
