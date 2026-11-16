
"""
Breakthrough 8x8 policy (smart, always-legal move chooser)

Implements:
    def policy(me, opp, color) -> ((from_r, from_c), (to_r, to_c))
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import List, Tuple, Optional, Dict

# --- Bitboard helpers ---

def rc_to_i(r: int, c: int) -> int:
    return (r << 3) | c

def i_to_rc(i: int) -> Tuple[int, int]:
    return (i >> 3), (i & 7)

def list_to_bitboard(pieces: List[Tuple[int, int]]) -> int:
    bb = 0
    for r, c in pieces:
        bb |= 1 << rc_to_i(r, c)
    return bb

def iter_bits(bb: int):
    while bb:
        lsb = bb & -bb
        i = lsb.bit_length() - 1
        yield i
        bb ^= lsb

def popcount(bb: int) -> int:
    return bb.bit_count()

# --- Precomputation ---

FILE_MASK = [0] * 8
RANK_MASK = [0] * 8
for c in range(8):
    m = 0
    for r in range(8):
        m |= 1 << rc_to_i(r, c)
    FILE_MASK[c] = m

for r in range(8):
    m = 0
    for c in range(8):
        m |= 1 << rc_to_i(r, c)
    RANK_MASK[r] = m

ABOVE_MASK_W = [0] * 8  # squares strictly above rank r (for white moving up)
BELOW_MASK_B = [0] * 8  # squares strictly below rank r (for black moving down)
for r in range(8):
    above = 0
    for rr in range(r + 1, 8):
        above |= RANK_MASK[rr]
    ABOVE_MASK_W[r] = above

    below = 0
    for rr in range(0, r):
        below |= RANK_MASK[rr]
    BELOW_MASK_B[r] = below

GOAL_MASK = {
    "w": RANK_MASK[7],  # white wins by reaching row 7
    "b": RANK_MASK[0],  # black wins by reaching row 0
}

OPP_COLOR = {"w": "b", "b": "w"}

# Move target tables: for each square index, forward target and diagonal targets (up to 2)
FWD = {"w": [-1] * 64, "b": [-1] * 64}
DIAG = {"w": [[] for _ in range(64)], "b": [[] for _ in range(64)]}
PROGRESS = {"w": [0] * 64, "b": [0] * 64}  # higher is closer to goal

CENTER_BONUS = [0.0] * 64
for i in range(64):
    r, c = i_to_rc(i)
    # small preference for central files
    CENTER_BONUS[i] = -abs(c - 3.5)

for i in range(64):
    r, c = i_to_rc(i)
    # White forward: (r+1, c)
    if r < 7:
        FWD["w"][i] = rc_to_i(r + 1, c)
        if c > 0:
            DIAG["w"][i].append(rc_to_i(r + 1, c - 1))
        if c < 7:
            DIAG["w"][i].append(rc_to_i(r + 1, c + 1))
    # Black forward: (r-1, c)
    if r > 0:
        FWD["b"][i] = rc_to_i(r - 1, c)
        if c > 0:
            DIAG["b"][i].append(rc_to_i(r - 1, c - 1))
        if c < 7:
            DIAG["b"][i].append(rc_to_i(r - 1, c + 1))

    # progress to goal
    PROGRESS["w"][i] = r
    PROGRESS["b"][i] = 7 - r


@dataclass(frozen=True)
class Move:
    frm: int
    to: int
    is_capture: bool
    is_win: bool
    adv_gain: int  # progress gain


INF = 10**9


def has_goal(bits: int, color: str) -> bool:
    return (bits & GOAL_MASK[color]) != 0


def generate_moves(my_bits: int, opp_bits: int, color: str) -> List[Move]:
    occ = my_bits | opp_bits
    moves: List[Move] = []
    goal = GOAL_MASK[color]

    for frm in iter_bits(my_bits):
        # Forward move (must be empty)
        f = FWD[color][frm]
        if f != -1 and ((occ >> f) & 1) == 0:
            to = f
            is_win = ((1 << to) & goal) != 0
            moves.append(Move(frm, to, False, is_win, PROGRESS[color][to] - PROGRESS[color][frm]))

        # Diagonals (empty or capture)
        for to in DIAG[color][frm]:
            if ((my_bits >> to) & 1) != 0:
                continue  # own piece blocks
            cap = ((opp_bits >> to) & 1) != 0
            # diagonal into empty is allowed
            is_win = ((1 << to) & goal) != 0
            moves.append(Move(frm, to, cap, is_win, PROGRESS[color][to] - PROGRESS[color][frm]))

    return moves


def apply_move(my_bits: int, opp_bits: int, mv: Move) -> Tuple[int, int]:
    frm_mask = 1 << mv.frm
    to_mask = 1 << mv.to
    my_bits2 = (my_bits ^ frm_mask) | to_mask
    opp_bits2 = opp_bits & ~to_mask  # remove if captured
    return my_bits2, opp_bits2


def count_capture_moves(my_bits: int, opp_bits: int, color: str) -> int:
    cnt = 0
    for frm in iter_bits(my_bits):
        for to in DIAG[color][frm]:
            if ((opp_bits >> to) & 1) and not ((my_bits >> to) & 1):
                cnt += 1
    return cnt


def any_immediate_win(my_bits: int, opp_bits: int, color: str) -> bool:
    for mv in generate_moves(my_bits, opp_bits, color):
        if mv.is_win:
            return True
    return False


def evaluate(my_bits: int, opp_bits: int, color: str) -> int:
    """
    Static eval from perspective of side-to-move 'color':
    positive is good for side to move.
    """
    opp_color = OPP_COLOR[color]

    # Terminal checks
    if my_bits == 0:
        return -INF
    if opp_bits == 0:
        return INF
    if has_goal(my_bits, color):
        return INF
    if has_goal(opp_bits, opp_color):
        return -INF

    my_n = popcount(my_bits)
    opp_n = popcount(opp_bits)

    score = 0

    # Material
    score += 120 * (my_n - opp_n)

    # Advancement / progress
    my_prog = 0
    for i in iter_bits(my_bits):
        my_prog += PROGRESS[color][i]
    opp_prog = 0
    for i in iter_bits(opp_bits):
        opp_prog += PROGRESS[opp_color][i]
    score += 6 * (my_prog - opp_prog)

    # Center preference (small)
    cscore = 0.0
    for i in iter_bits(my_bits):
        cscore += CENTER_BONUS[i]
    for i in iter_bits(opp_bits):
        cscore -= CENTER_BONUS[i]
    score += int(3 * cscore)

    # Passed pawn potential (simple file/adjacent-file scan ahead)
    passed_bonus = 0
    for i in iter_bits(my_bits):
        r, c = i_to_rc(i)
        files = FILE_MASK[c]
        if c > 0:
            files |= FILE_MASK[c - 1]
        if c < 7:
            files |= FILE_MASK[c + 1]
        ahead = ABOVE_MASK_W[r] if color == "w" else BELOW_MASK_B[r]
        if (opp_bits & files & ahead) == 0:
            # extra value for more advanced passed pawns
            passed_bonus += 12 + 2 * PROGRESS[color][i]
    for i in iter_bits(opp_bits):
        r, c = i_to_rc(i)
        files = FILE_MASK[c]
        if c > 0:
            files |= FILE_MASK[c - 1]
        if c < 7:
            files |= FILE_MASK[c + 1]
        ahead = ABOVE_MASK_W[r] if opp_color == "w" else BELOW_MASK_B[r]
        if (my_bits & files & ahead) == 0:
            passed_bonus -= 12 + 2 * PROGRESS[opp_color][i]
    score += passed_bonus

    # Mobility (cheap-ish)
    my_moves = generate_moves(my_bits, opp_bits, color)
    opp_moves = generate_moves(opp_bits, my_bits, opp_color)
    score += 2 * (len(my_moves) - len(opp_moves))

    # Capture threats
    my_caps = sum(1 for mv in my_moves if mv.is_capture)
    opp_caps = sum(1 for mv in opp_moves if mv.is_capture)
    score += 10 * (my_caps - opp_caps)

    # Must-stop: if opponent can win in one on their next move, huge penalty
    if any(mv.is_win for mv in opp_moves):
        score -= 600

    return score


def order_moves(moves: List[Move]) -> List[Move]:
    # Strong ordering: win > capture > advancement > center
    # (Center is implicitly in eval; here we just use a tiny bias)
    def key(mv: Move):
        return (
            1 if mv.is_win else 0,
            1 if mv.is_capture else 0,
            mv.adv_gain,
            CENTER_BONUS[mv.to],
        )
    return sorted(moves, key=key, reverse=True)


class Searcher:
    __slots__ = ("t0", "t_limit", "tt")

    def __init__(self, time_limit_s: float):
        self.t0 = perf_counter()
        self.t_limit = time_limit_s
        self.tt: Dict[Tuple[int, int, str, int], Tuple[int, Optional[Move]]] = {}

    def time_up(self) -> bool:
        return (perf_counter() - self.t0) >= self.t_limit

    def negamax(self, my_bits: int, opp_bits: int, color: str, depth: int, alpha: int, beta: int) -> Tuple[int, Optional[Move]]:
        if self.time_up():
            # Caller will handle partial results; return a static eval
            return evaluate(my_bits, opp_bits, color), None

        opp_color = OPP_COLOR[color]

        # Terminal checks
        if my_bits == 0:
            return -INF + (0 if depth == 0 else depth), None
        if opp_bits == 0:
            return INF - (0 if depth == 0 else depth), None
        if has_goal(my_bits, color):
            return INF - (0 if depth == 0 else depth), None
        if has_goal(opp_bits, opp_color):
            return -INF + (0 if depth == 0 else depth), None

        if depth <= 0:
            return evaluate(my_bits, opp_bits, color), None

        tt_key = (my_bits, opp_bits, color, depth)
        if tt_key in self.tt:
            return self.tt[tt_key]

        moves = generate_moves(my_bits, opp_bits, color)
        if not moves:
            # No legal moves: treat as losing state (standard Breakthrough rule).
            return -INF + depth, None

        moves = order_moves(moves)

        best_move: Optional[Move] = None
        best_score = -INF

        for mv in moves:
            my2, opp2 = apply_move(my_bits, opp_bits, mv)

            # After we move, opponent is to play; swap roles
            score_child, _ = self.negamax(opp2, my2, opp_color, depth - 1, -beta, -alpha)
            score = -score_child

            if score > best_score:
                best_score = score
                best_move = mv

            if best_score > alpha:
                alpha = best_score
            if alpha >= beta:
                break

        self.tt[tt_key] = (best_score, best_move)
        return best_score, best_move


def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    my_bits = list_to_bitboard(me)
    opp_bits = list_to_bitboard(opp)

    # Generate legal moves up-front; ensure we always return a legal move if one exists.
    root_moves = generate_moves(my_bits, opp_bits, color)
    if not root_moves:
        # If no legal moves exist, the position is losing; arena positions are expected to allow a move.
        # Return a placeholder "best effort" to avoid crashing (may be illegal in true stalemate).
        if me:
            return (me[0], me[0])
        return ((0, 0), (0, 0))

    # Immediate win
    for mv in root_moves:
        if mv.is_win:
            return i_to_rc(mv.frm), i_to_rc(mv.to)

    # Time-bounded iterative deepening
    # Slightly adapt depth to material: fewer pieces => deeper.
    total_pieces = len(me) + len(opp)
    max_depth = 5 if total_pieces >= 18 else 6

    searcher = Searcher(time_limit_s=0.85)
    best_mv = order_moves(root_moves)[0]  # safe fallback: legal move

    alpha, beta = -INF, INF
    for depth in range(1, max_depth + 1):
        if searcher.time_up():
            break
        score, mv = searcher.negamax(my_bits, opp_bits, color, depth, alpha, beta)
        if searcher.time_up():
            break
        if mv is not None:
            best_mv = mv
        # If we found a forced win, stop early.
        if score >= INF // 2:
            break

    return i_to_rc(best_mv.frm), i_to_rc(best_mv.to)
