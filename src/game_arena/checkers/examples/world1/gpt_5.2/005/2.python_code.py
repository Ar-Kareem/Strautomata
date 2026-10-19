
"""
Checkers policy for 8x8 American checkers.

Move format returned: ((from_row, from_col), (to_row, to_col))

Assumptions (match typical arena setups with this API):
- Captures are mandatory when available.
- A "move" is a single step or a single jump (single capture). (Multi-jump sequences
  are not representable in the provided API, so this policy plays single-jump captures.)
- Men move forward only; kings move both directions.
- Promotion when a man reaches the farthest rank (black -> row 0, white -> row 7).
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Optional, List, Tuple, Dict

# --- 32-square dark-square mapping utilities ---

def _is_dark(r: int, c: int) -> bool:
    return (r + c) % 2 == 1

def coord_to_idx(r: int, c: int) -> Optional[int]:
    # Dark squares only. Expected by environment.
    if not (0 <= r <= 7 and 0 <= c <= 7):
        return None
    if not _is_dark(r, c):
        return None
    return r * 4 + (c // 2)

def idx_to_coord(idx: int) -> Tuple[int, int]:
    r = idx // 4
    k = idx % 4
    c = 2 * k + (1 if (r % 2 == 0) else 0)
    return r, c

def popcount(x: int) -> int:
    return x.bit_count()

def iter_bits(bb: int):
    while bb:
        lsb = bb & -bb
        i = (lsb.bit_length() - 1)
        yield i
        bb ^= lsb


# Directions in (dr, dc) with row increasing bottom->top.
DIRS = {
    "NE": (1, 1),
    "NW": (1, -1),
    "SE": (-1, 1),
    "SW": (-1, -1),
}

# For men, "forward" depends on color.
MEN_DIRS = {
    "w": ("NE", "NW"),  # white moves upward (to higher row)
    "b": ("SE", "SW"),  # black moves downward (to lower row)
}
KING_DIRS = ("NE", "NW", "SE", "SW")

# Precomputed step/jump tables: [idx][dir_name] -> idx or -1
_STEP = [[-1] * 4 for _ in range(32)]
_JUMP = [[-1] * 4 for _ in range(32)]
_OVER = [[-1] * 4 for _ in range(32)]
_DIR_INDEX = {"NE": 0, "NW": 1, "SE": 2, "SW": 3}

def _precompute():
    for idx in range(32):
        r, c = idx_to_coord(idx)
        for dname, (dr, dc) in DIRS.items():
            di = _DIR_INDEX[dname]
            r1, c1 = r + dr, c + dc
            r2, c2 = r + 2 * dr, c + 2 * dc
            if 0 <= r1 <= 7 and 0 <= c1 <= 7 and _is_dark(r1, c1):
                j = coord_to_idx(r1, c1)
                _STEP[idx][di] = -1 if j is None else j
            if (0 <= r2 <= 7 and 0 <= c2 <= 7 and _is_dark(r2, c2)
                    and 0 <= r1 <= 7 and 0 <= c1 <= 7 and _is_dark(r1, c1)):
                mid = coord_to_idx(r1, c1)
                land = coord_to_idx(r2, c2)
                if mid is not None and land is not None:
                    _OVER[idx][di] = mid
                    _JUMP[idx][di] = land

_precompute()


@dataclass(frozen=True)
class Move:
    frm: int
    to: int
    is_capture: bool
    over: int  # -1 if not capture


@dataclass(frozen=True)
class State:
    bm: int
    bk: int
    wm: int
    wk: int
    turn: str  # 'b' or 'w'

    def key(self):
        return (self.bm, self.bk, self.wm, self.wk, self.turn)


def _side_bits(st: State, side: str) -> Tuple[int, int]:
    if side == "b":
        return st.bm, st.bk
    return st.wm, st.wk

def _opp_bits(st: State, side: str) -> Tuple[int, int]:
    if side == "b":
        return st.wm, st.wk
    return st.bm, st.bk

def _occ(st: State) -> int:
    return st.bm | st.bk | st.wm | st.wk

def _promote_row(side: str) -> int:
    return 0 if side == "b" else 7


def generate_moves(st: State, side: str, mandatory_capture: bool = True) -> List[Move]:
    bm, bk = _side_bits(st, side)
    om, ok = _opp_bits(st, side)
    opp = om | ok
    occ = _occ(st)

    captures: List[Move] = []
    quiets: List[Move] = []

    # Men
    for i in iter_bits(bm):
        for dname in MEN_DIRS[side]:
            di = _DIR_INDEX[dname]
            land = _JUMP[i][di]
            mid = _OVER[i][di]
            if land != -1 and mid != -1:
                if ((opp >> mid) & 1) and not ((occ >> land) & 1):
                    captures.append(Move(i, land, True, mid))
            if not mandatory_capture:
                step = _STEP[i][di]
                if step != -1 and not ((occ >> step) & 1):
                    quiets.append(Move(i, step, False, -1))

    # Kings
    for i in iter_bits(bk):
        for dname in KING_DIRS:
            di = _DIR_INDEX[dname]
            land = _JUMP[i][di]
            mid = _OVER[i][di]
            if land != -1 and mid != -1:
                if ((opp >> mid) & 1) and not ((occ >> land) & 1):
                    captures.append(Move(i, land, True, mid))
            if not mandatory_capture:
                step = _STEP[i][di]
                if step != -1 and not ((occ >> step) & 1):
                    quiets.append(Move(i, step, False, -1))

    if mandatory_capture:
        if captures:
            return captures
        # generate quiets if no captures
        return generate_moves(st, side, mandatory_capture=False)

    return captures + quiets


def apply_move(st: State, side: str, mv: Move) -> State:
    bm, bk, wm, wk = st.bm, st.bk, st.wm, st.wk

    frm_bit = 1 << mv.frm
    to_bit = 1 << mv.to

    is_king = False
    if side == "b":
        if bk & frm_bit:
            is_king = True
            bk ^= frm_bit
        else:
            bm ^= frm_bit
    else:
        if wk & frm_bit:
            is_king = True
            wk ^= frm_bit
        else:
            wm ^= frm_bit

    # capture removal
    if mv.is_capture and mv.over != -1:
        over_bit = 1 << mv.over
        if side == "b":
            if wm & over_bit:
                wm ^= over_bit
            elif wk & over_bit:
                wk ^= over_bit
        else:
            if bm & over_bit:
                bm ^= over_bit
            elif bk & over_bit:
                bk ^= over_bit

    # place moved piece, with possible promotion
    r_to, _ = idx_to_coord(mv.to)
    promote = (not is_king) and (r_to == _promote_row(side))

    if side == "b":
        if is_king or promote:
            bk |= to_bit
        else:
            bm |= to_bit
        turn = "w"
    else:
        if is_king or promote:
            wk |= to_bit
        else:
            wm |= to_bit
        turn = "b"

    return State(bm=bm, bk=bk, wm=wm, wk=wk, turn=turn)


def _immediate_capture_exists(st: State, side: str) -> bool:
    mv = generate_moves(st, side, mandatory_capture=True)
    return bool(mv) and mv[0].is_capture


def evaluate(st: State, my_side: str) -> float:
    """
    Static evaluation from my_side's perspective.
    Positive = good for my_side.
    """
    # Material
    MEN_W = 1.0
    KING_W = 1.75

    bm, bk, wm, wk = st.bm, st.bk, st.wm, st.wk

    mym, myk = (bm, bk) if my_side == "b" else (wm, wk)
    oppm, oppk = (wm, wk) if my_side == "b" else (bm, bk)

    mat = MEN_W * popcount(mym) + KING_W * popcount(myk) - (MEN_W * popcount(oppm) + KING_W * popcount(oppk))

    # Advancement for men (encourage promotion)
    adv = 0.0
    for i in iter_bits(mym):
        r, _ = idx_to_coord(i)
        adv += (7 - r) if my_side == "b" else r
    for i in iter_bits(oppm):
        r, _ = idx_to_coord(i)
        adv -= (7 - r) if (my_side == "w") else r  # subtract opponent progress towards their promotion
        # Explanation: if I'm 'w', opponent is 'b' (promotion at row 0, progress = 7-r)
        # if I'm 'b', opponent is 'w' (promotion at row 7, progress = r)

    adv *= 0.06

    # Center control (rows 2..5, cols 2..5)
    center = 0.0
    def in_center(idx: int) -> bool:
        r, c = idx_to_coord(idx)
        return 2 <= r <= 5 and 2 <= c <= 5

    for i in iter_bits(mym | myk):
        if in_center(i):
            center += 0.05
    for i in iter_bits(oppm | oppk):
        if in_center(i):
            center -= 0.05

    # Mobility (small weight)
    my_moves = len(generate_moves(st, my_side, mandatory_capture=True))  # mandatory model
    opp_side = "w" if my_side == "b" else "b"
    opp_moves = len(generate_moves(st, opp_side, mandatory_capture=True))
    mob = 0.02 * (my_moves - opp_moves)

    # Back row guard (a little) to prevent easy kings
    back = 0.0
    my_home_row = 7 if my_side == "b" else 0
    opp_home_row = 7 if opp_side == "b" else 0
    for i in iter_bits(mym):
        r, _ = idx_to_coord(i)
        if r == my_home_row:
            back += 0.04
    for i in iter_bits(oppm):
        r, _ = idx_to_coord(i)
        if r == opp_home_row:
            back -= 0.04

    # Tactical safety: pieces en prise (can be captured immediately)
    # Approximate by checking whether opponent has any capture in resulting position; handled in move ordering too.
    # Here: small penalty if opponent currently has captures.
    tact = -0.08 if _immediate_capture_exists(st, opp_side) else 0.0

    return mat + adv + center + mob + back + tact


class Searcher:
    def __init__(self, my_side: str, time_limit_s: float = 0.90):
        self.my_side = my_side
        self.t0 = time.perf_counter()
        self.tlimit = time_limit_s
        self.tt: Dict[Tuple[int, int, int, int, str, int], Tuple[float, Optional[Move]]] = {}

    def time_up(self) -> bool:
        return (time.perf_counter() - self.t0) >= self.tlimit

    def order_moves(self, st: State, side: str, moves: List[Move]) -> List[Move]:
        if not moves:
            return moves

        # Heuristic ordering: captures first, then promotions, then center, then "avoid immediate opponent capture".
        occ = _occ(st)
        opp_side = "w" if side == "b" else "b"

        def score(mv: Move) -> float:
            s = 0.0
            if mv.is_capture:
                s += 10.0
                # prefer capturing kings if possible
                over_bit = 1 << mv.over
                if side == "b":
                    if st.wk & over_bit:
                        s += 1.5
                else:
                    if st.bk & over_bit:
                        s += 1.5

            # promotion
            frm_bit = 1 << mv.frm
            is_man = False
            if side == "b":
                is_man = bool(st.bm & frm_bit)
            else:
                is_man = bool(st.wm & frm_bit)
            r_to, c_to = idx_to_coord(mv.to)
            if is_man and r_to == _promote_row(side):
                s += 2.5

            # center preference
            if 2 <= r_to <= 5 and 2 <= c_to <= 5:
                s += 0.25

            # discourage moves that allow immediate opponent capture
            st2 = apply_move(st, side, mv)
            if _immediate_capture_exists(st2, opp_side):
                s -= 0.6

            # small tie-breaker: keep pieces connected / avoid edges slightly
            if c_to in (0, 7):
                s -= 0.05

            return s

        return sorted(moves, key=score, reverse=True)

    def alphabeta(self, st: State, depth: int, alpha: float, beta: float) -> Tuple[float, Optional[Move]]:
        if self.time_up():
            # Return static eval; no move
            return evaluate(st, self.my_side), None

        # Terminal / depth
        legal = generate_moves(st, st.turn, mandatory_capture=True)
        if not legal:
            # Current player has no moves -> loses.
            # If current player is me, very bad; else very good.
            if st.turn == self.my_side:
                return -999.0, None
            else:
                return 999.0, None

        if depth <= 0:
            return evaluate(st, self.my_side), None

        tt_key = (st.bm, st.bk, st.wm, st.wk, st.turn, depth)
        if tt_key in self.tt:
            return self.tt[tt_key]

        side = st.turn
        is_max = (side == self.my_side)

        best_mv: Optional[Move] = None
        if is_max:
            value = -1e9
            moves = self.order_moves(st, side, legal)
            for mv in moves:
                st2 = apply_move(st, side, mv)
                v, _ = self.alphabeta(st2, depth - 1, alpha, beta)
                if v > value:
                    value, best_mv = v, mv
                alpha = max(alpha, value)
                if beta <= alpha or self.time_up():
                    break
        else:
            value = 1e9
            moves = self.order_moves(st, side, legal)
            for mv in moves:
                st2 = apply_move(st, side, mv)
                v, _ = self.alphabeta(st2, depth - 1, alpha, beta)
                if v < value:
                    value, best_mv = v, mv
                beta = min(beta, value)
                if beta <= alpha or self.time_up():
                    break

        self.tt[tt_key] = (value, best_mv)
        return value, best_mv

    def search(self, st: State) -> Move:
        # Always ensure we return something legal.
        root_moves = generate_moves(st, st.turn, mandatory_capture=True)
        if not root_moves:
            # No legal move (shouldn't be called in such positions); pick dummy.
            return Move(0, 0, False, -1)

        best = root_moves[0]
        best_val = -1e9

        # Iterative deepening
        for depth in range(1, 8):
            if self.time_up():
                break
            val, mv = self.alphabeta(st, depth, -1e9, 1e9)
            if self.time_up():
                break
            if mv is not None:
                best = mv
                best_val = val

        return best


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    # Convert lists of (r,c) to bitboards.
    def to_bb(lst) -> int:
        bb = 0
        for (r, c) in lst:
            idx = coord_to_idx(r, c)
            if idx is None:
                continue
            bb |= (1 << idx)
        return bb

    mym = to_bb(my_men)
    myk = to_bb(my_kings)
    oppm = to_bb(opp_men)
    oppk = to_bb(opp_kings)

    if color == "b":
        st = State(bm=mym, bk=myk, wm=oppm, wk=oppk, turn="b")
    else:
        st = State(bm=oppm, bk=oppk, wm=mym, wk=myk, turn="w")

    # Search and pick best legal move.
    searcher = Searcher(my_side=color, time_limit_s=0.90)
    mv = searcher.search(st)

    fr = idx_to_coord(mv.frm)
    to = idx_to_coord(mv.to)
    return fr, to
