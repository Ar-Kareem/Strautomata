from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional, Union, Literal

import pyspiel
import numpy as np

from game_arena.base import Game
from game_arena.utils import get_config_file
from game_arena.prompt_render import render_prompt_pre_filled

# Canonical fixed notation (no spaces):
#   <ORDER>:<FROM1>,<FROM2>
# ORDER: 'H' (high die first) or 'L' (low die first)
# FROM:  'B' (bar), 'P' (pass), or 'A0'..'A23' (absolute point index)
MOVE_FROM = Union[int, Literal['BAR']]  # '0'..'23'
MOVE_TO = Union[int, Literal['OFF']]  # '0'..'23'
MOVE_FROM_TO = Union[tuple[MOVE_FROM, MOVE_TO], Literal['PASS']]  # (from, to) or 'PASS'
MOVE_PAIR = tuple[MOVE_FROM_TO, MOVE_FROM_TO]  # two pairs of moves, one for each die

@dataclass(frozen=True)
class Move:
    action: int
    action_str: str
    two_moves: MOVE_PAIR


def openspiel_to_move(action_str: str, action: int) -> Move:
    original_action_str = action_str
    if ' - ' in action_str:
        action_str = action_str.split(' - ')[1]
    action_str = action_str.upper()
    action_str = action_str.replace('*', '')  # ignore hit markers
    if action_str.endswith('(2)'):  # double move
        action_str = action_str[:-3]
        action_str = action_str + ' ' + action_str
    if action_str.count('/') == 2 and ' ' not in action_str:  # x/y/z notation -> x/y y/z
        x, y, z = action_str.split('/')
        action_str = f'{x}/{y} {y}/{z}'
    if action_str == 'PASS':
        return Move(action, action_str, ('PASS', 'PASS'))
    assert ' ' in action_str, f"Invalid action string: {action_str}"
    pair1, pair2 = action_str.split(' ')
    return Move(action, original_action_str, (parse_move_from_to(pair1), parse_move_from_to(pair2)))


def parse_move_from_to(pair: str) -> MOVE_FROM_TO:
    if pair == 'PASS':
        return 'PASS'
    m_from, m_to = pair.split('/')
    if m_from != 'BAR':
        m_from = int(m_from)
    if m_to != 'OFF':
        m_to = int(m_to)
    return (m_from, m_to)


def llm_to_move(move_str: str, dice: Optional[list[int]], valid_moves: list[Move], _debug_obs: Any = None) -> Move:
    assert dice is not None, f"Dice is required for LLM move parsing: {move_str}"
    def _parse_from(f: str, order: str) -> MOVE_FROM_TO:
        if f.upper() == 'P':
            return 'PASS'
        elif f.upper() == 'B':
            move_from = 'BAR'
        elif f.upper().startswith('A'):
            move_from = int(f.upper()[1:]) + 1
        elif f.upper().isdigit():
            move_from = int(f.upper()) + 1
        else:
            raise ValueError(f"Invalid from value: {f}. move_str: {move_str}, dice: {dice}")
        move_from_val = int(move_from) if move_from != 'BAR' else 25  # starting index
        val = dice[1] if order == 'H' else dice[0]  # value of the jump
        to_val = move_from_val - val  # ending index
        assert to_val <= 24, f"Invalid to value: {to_val}. move_str: {move_str}, dice: {dice}"
        to: MOVE_TO = int(to_val) if to_val > 0 else 'OFF'
        return (move_from, to)

    assert move_str.count(':') == 1 and move_str.count(',') == 1, f"Invalid move string: {move_str} (should have exactly one ':' and one ',')"
    order, f12 = move_str.split(':')
    f1, f2 = f12.split(',')
    move1 = _parse_from(f1, order)
    move2 = _parse_from(f2, 'L' if order == 'H' else 'H')  # switch order for the second move
    move_pair = (move1, move2)
    matching_moves = [move for move in valid_moves if move.two_moves == move_pair or move.two_moves == move_pair[::-1]]
    if not matching_moves:
        raise ValueError(f"Invalid move: {move_str} with dice {dice} which gives move pair {move_pair} but valid moves are {[move.two_moves for move in valid_moves]} and debug obs: {_debug_obs}")
    # assert len(matching_moves) == 1, f"Ambiguous move: {move_str} with dice {dice} which gives move pair {move_pair} and matches {[move.two_moves for move in matching_moves]}"
    return matching_moves[0]


def parse_observation(obs: np.ndarray) -> dict[str, Any]:
    v = obs.tolist() if hasattr(obs, "tolist") else list(obs)
    assert len(v) == 200, f"Expected 200 floats, got {len(v)}"
    def decode_point(offset: int) -> int:
        """
        Tesauro encoding (per point): [is1, is2, is3, extra]
        - if count == 1 -> [1,0,0,0]
        - if count == 2 -> [0,1,0,0]
        - if count == 3 -> [0,0,1,0]
        - if count > 3  -> [0,0,0,count-3]
        - if count == 0 -> [0,0,0,0]
        """
        a, b, c, d = v[offset:offset + 4]

        # Robust thresholding for float noise.
        if d > 0.5:
            return 3 + int(round(d))
        if a > 0.5:
            return 1
        if b > 0.5:
            return 2
        if c > 0.5:
            return 3
        return 0
    pts0  = [decode_point(i) for i in range(0, 96, 4)]
    pts1 = [decode_point(i) for i in range(96, 192, 4)]
    dice0, dice1 = int(round(v[198])), int(round(v[199]))
    dice = [d for d in (dice0, dice1) if d]
    return {
        "pts0": pts0,
        "pts1": pts1,
        "p0_bar": int(round(v[192])),
        "p0_off": int(round(v[193])),
        "p1_bar": int(round(v[195])),
        "p1_off": int(round(v[196])),
        "dice": dice,
    }

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


class BackgammonGame(Game):
    def __init__(self, config: Optional[dict[str, Any]] = None, seed: Optional[int] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.seed: Optional[int] = seed
        self._rng = _derive_rng(self.seed)
        self.turn: int = 0

        self._spiel_game = pyspiel.load_game("backgammon")
        self._state = self._spiel_game.new_initial_state()
        if self._spiel_game.num_players() != 2:
            raise RuntimeError("Game expects a 2-player OpenSpiel game.")

        self.move_count: int = 0
        self._is_done: bool = False
        self.do_chance_if_needed()
        self.get_legal_moves()

    def openspiel_to_move(self, action_str: str, action: int) -> Move:
        return openspiel_to_move(action_str, action)

    def get_observation(self) -> dict[str, Any]:
        obs = self._state.observation_tensor(1)
        parsed = parse_observation(obs)
        self.dice = parsed['dice']
        my_pts, opp_pts = parsed['pts0'], parsed['pts1']
        my_bar, my_off = parsed['p0_bar'], parsed['p0_off']
        opp_bar, opp_off = parsed['p1_bar'], parsed['p1_off']
        if self.turn == 0:
            my_pts, opp_pts = opp_pts, my_pts
            my_bar, opp_bar = opp_bar, my_bar
            my_off, opp_off = opp_off, my_off
            # flip board
            my_pts = my_pts[::-1]
            opp_pts = opp_pts[::-1]
        self.observation = {'state': {
            "my_pts": my_pts, "opp_pts": opp_pts,
            "my_bar": my_bar, "my_off": my_off,
            "opp_bar": opp_bar, "opp_off": opp_off,
            "dice": self.dice,
        }}
        return self.observation

    def get_fixed_observation(self) -> dict[str, Any]:
        obs = self._state.observation_tensor(0)
        return parse_observation(obs)

    def game_step(self, move: Union[Move, int]) -> None:
        if self._is_done:
            raise ValueError("Game is already finished")
        if isinstance(move, Move):
            action = move.action
        else:
            action = move
        assert action in self._state.legal_actions()
        self._state.apply_action(action)
        self.move_count += 1
        self.dice = None

        self.do_chance_if_needed()
        self.turn = self._state.current_player()
        self.get_legal_moves()
        if self._state.is_terminal():
            self._is_done = True
            return

    def do_chance_if_needed(self) -> None:
        while self._state.is_chance_node():
            outcomes = self._state.chance_outcomes()
            action_list, prob_list = zip(*outcomes)
            action = int(self._rng.choice(action_list, p=prob_list))
            self._state.apply_action(action)

    def get_move(self, move_str: str) -> Union[Move, int]:
        if move_str in self.legal_str_to_actions:
            return self.legal_str_to_actions[move_str]
        if ':' in move_str:  # LLM output
            return llm_to_move(move_str, self.dice, self.legal_moves, self.observation)
        raise ValueError(f"Invalid move: {move_str}")

    def get_legal_moves(self) -> list[str]:
        if self._is_done:
            return []
        self.legal_str_to_actions = {self._state.action_to_string(action): action for action in self._state.legal_actions()}
        self.legal_moves = [openspiel_to_move(k, v) for k, v in self.legal_str_to_actions.items()]
        return list(self.legal_str_to_actions.keys())

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

    @staticmethod
    def get_prompt(config: dict[str, Any]) -> str:
        return render_prompt_pre_filled(
            game_name="Backgammon game",
            signature_block=(
                "```python\n"
                "def policy(state: dict) -> str:\n"
                "    ...\n"
                "```"
            ),
            state=[
                "You are always the player to move.",
                "Your `policy` receives a single Python dict named `state` with the following keys:",
                "- `state['my_pts']`: a length-24 list of nonnegative integers giving how many of your checkers are on each point.",
                "- `state['opp_pts']`: a length-24 list of nonnegative integers giving how many opponent checkers are on each point.",
                "- `state['my_bar']`: number of your checkers on the bar (waiting to re-enter).",
                "- `state['opp_bar']`: number of opponent checkers on the bar.",
                "- `state['my_off']`: number of your checkers borne off (scored).",
                "- `state['opp_off']`: number of opponent checkers borne off (scored).",
                "- `state['dice']`: a list of 0, 1, or 2 integers in `1..6` representing the current roll (e.g., `[5, 6]`).",
                "Point indices are absolute indices `0..23` as used by the engine:",
                "- `0` and `23` are the extreme points (endpoints) of the board; You always move from `23` to `0` while your opponent moves from `0` to `23`, this is handled by the engine.",
                "- You do not need to compute destinations; your action specifies only the starting points for up to two checker moves.",
                "Legal-move constraints are enforced by the engine, including:",
                "- If you have any checkers on the bar, you must move them before moving other checkers.",
                "- You may not move onto a point occupied by 2 or more opposing checkers.",
                "- If only one die can be played, you must play the higher die when possible.",
                "- If both dice can be played, you must play both.",
                "- Bearing off is only allowed when all of your remaining checkers are in your home board (A0..A5).",
            ],
            action=[
                "Return a move string in the fixed compact format: `<ORDER>:<FROM1>,<FROM2>` with no spaces.",
                "`<ORDER>` is one character: `H` or `L`.",
                "- `H` means the first encoded checker move uses the higher die.",
                "- `L` means the first encoded checker move uses the lower die.",
                "`<FROM1>` and `<FROM2>` are the start locations for the first and second checker moves.",
                "Each `<FROM>` token must be one of:",
                "- `A0`..`A23` for an absolute point index (0..23).",
                "- `B` for Bar.",
                "- `P` for Pass (no checker move).",
                "Examples:",
                "- `H:A0,A18` means: apply the higher die from point 0, and the lower die from point 18.",
                "- `L:B,A5` means: apply the lower die from Bar, then the higher die from point 5.",
                "- `H:P,P` means: no legal moves (full pass).",
                "The move string must correspond to a legal action for the current state and dice.",
                "Do not care about hit markers, destinations, or parentheses; hits and end points are computed for you by the engine.",
            ],
        )

if __name__ == "__main__":
    config = get_config_file('backgammon', 'world1')
    prompt = BackgammonGame.get_prompt(config=config)
    print(prompt)
    (Path(__file__).parent / "prompt_example.txt").write_text(prompt)
