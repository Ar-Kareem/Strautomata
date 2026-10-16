
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple
import time
import math

Coord = Tuple[int, int]
MoveTuple = Tuple[Coord, Coord]


def _opp(color: str) -> str:
    return "w" if color == "b" else "b"


def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r <= 7 and 0 <= c <= 7


@dataclass(frozen=True)
class Move:
    fr: Coord
    to: Coord
    cap: Optional[Coord]  # captured square if capture move else None


class _State:
    __slots__ = ("b_men", "b_kings", "w_men", "w_kings", "side")

    def __init__(
        self,
        b_men: Set[Coord],
        b_kings: Set[Coord],
        w_men: Set[Coord],
        w_kings: Set[Coord],
        side: str,
    ) -> None:
        self.b_men = b_men
        self.b_kings = b_kings
        self.w_men = w_men
        self.w_kings = w_kings
        self.side = side

    def clone(self) -> "_State":
        return _State(set(self.b_men), set(self.b_kings), set(self.w_men), set(self.w_kings), self.side)

    def key(self) -> Tuple[str, FrozenSet[Coord], FrozenSet[Coord], FrozenSet[Coord], FrozenSet[Coord]]:
        return (
            self.side,
            frozenset(self.b_men),
            frozenset(self.b_kings),
            frozenset(self.w_men),
            frozenset(self.w_kings),
        )

    def occupied(self) -> Set[Coord]:
        # Used only in move-gen; set() creation is fine at this scale.
        return self.b_men | self.b_kings | self.w_men | self.w_kings


def _pieces_for(st: _State, color: str) -> Tuple[Set[Coord], Set[Coord]]:
    return (st.b_men, st.b_kings) if color == "b" else (st.w_men, st.w_kings)


def _enemy_for(st: _State, color: str) -> Tuple[Set[Coord], Set[Coord]]:
    return (st.w_men, st.w_kings) if color == "b" else (st.b_men, st.b_kings)


def _dirs_for_man(color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Men move (and capture) forward only (English/American checkers style).
    dr = -1 if color == "b" else 1
    return ((dr, -1), (dr, 1))


_KING_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))


def _gen_captures_for_piece(
    st: _State,
    color: str,
    pos: Coord,
    is_king: bool,
    occ: Set[Coord],
    enemy_occ: Set[Coord],
) -> List[Move]:
    r, c = pos
    moves: List[Move] = []
    dirs = _KING_DIRS if is_king else _dirs_for_man(color)
    for dr, dc in dirs:
        mr, mc = r + dr, c + dc
        tr, tc = r + 2 * dr, c + 2 * dc
        if not _in_bounds(tr, tc) or not _in_bounds(mr, mc):
            continue
        mid = (mr, mc)
        to = (tr, tc)
        if mid in enemy_occ and to not in occ:
            moves.append(Move(fr=pos, to=to, cap=mid))
    return moves


def _gen_simple_for_piece(st: _State, color: str, pos: Coord, is_king: bool, occ: Set[Coord]) -> List[Move]:
    r, c = pos
    moves: List[Move] = []
    dirs = _KING_DIRS if is_king else _dirs_for_man(color)
    for dr, dc in dirs:
        tr, tc = r + dr, c + dc
        if not _in_bounds(tr, tc):
            continue
        to = (tr, tc)
        if to not in occ:
            moves.append(Move(fr=pos, to=to, cap=None))
    return moves


def _generate_moves(st: _State, color: str) -> List[Move]:
    my_men, my_kings = _pieces_for(st, color)
    enemy_men, enemy_kings = _enemy_for(st, color)
    occ = st.occupied()
    enemy_occ = enemy_men | enemy_kings

    captures: List[Move] = []
    for p in my_men:
        captures.extend(_gen_captures_for_piece(st, color, p, False, occ, enemy_occ))
    for p in my_kings:
        captures.extend(_gen_captures_for_piece(st, color, p, True, occ, enemy_occ))
    if captures:
        return captures  # mandatory captures

    moves: List[Move] = []
    for p in my_men:
        moves.extend(_gen_simple_for_piece(st, color, p, False, occ))
    for p in my_kings:
        moves.extend(_gen_simple_for_piece(st, color, p, True, occ))
    return moves


def _apply_move(st: _State, mv: Move) -> _State:
    color = st.side
    ns = st.clone()
    my_men, my_kings = _pieces_for(ns, color)
    enemy_men, enemy_kings = _enemy_for(ns, color)

    fr, to = mv.fr, mv.to

    is_king = fr in my_kings
    if is_king:
        my_kings.remove(fr)
    else:
        my_men.remove(fr)

    # capture
    if mv.cap is not None:
        if mv.cap in enemy_men:
            enemy_men.remove(mv.cap)
        elif mv.cap in enemy_kings:
            enemy_kings.remove(mv.cap)

    # promotion
    prom_row = 0 if color == "b" else 7
    if (not is_king) and to[0] == prom_row:
        my_kings.add(to)
    else:
        (my_kings if is_king else my_men).add(to)

    ns.side = _opp(color)
    return ns


def _can_be_captured_next(st: _State, color: str, sq: Coord) -> bool:
    """
    Quick threat check: does opponent have any capture that lands over 'sq'?
    (We only need a boolean, so stop early.)
    """
    opp = _opp(color)
    # If opponent has any capture in their move list that captures sq, it is threatened.
    opp_moves = _generate_moves(st, opp)
    for mv in opp_moves:
        if mv.cap == sq:
            return True
    return False


def _evaluate(st: _State, color: str) -> float:
    """
    Positive is good for 'color'.
    """
    my_men, my_kings = _pieces_for(st, color)
    en_men, en_kings = _enemy_for(st, color)

    # Material
    material = 1.0 * (len(my_men) - len(en_men)) + 1.75 * (len(my_kings) - len(en_kings))

    # Advancement of men (closer to promotion)
    if color == "w":
        adv_my = sum(r for (r, c) in my_men) / 7.0 if my_men else 0.0
        adv_en = sum(7 - r for (r, c) in en_men) / 7.0 if en_men else 0.0
    else:
        adv_my = sum(7 - r for (r, c) in my_men) / 7.0 if my_men else 0.0
        adv_en = sum(r for (r, c) in en_men) / 7.0 if en_men else 0.0
    advancement = 0.20 * (adv_my - adv_en)

    # Center control
    center_sqs = {(3, 2), (3, 4), (4, 3), (4, 5), (2, 3), (2, 5), (5, 2), (5, 4)}
    center = 0.05 * (
        sum(1 for p in (my_men | my_kings) if p in center_sqs) -
        sum(1 for p in (en_men | en_kings) if p in center_sqs)
    )

    # Mobility (small weight; mandatory captures can reduce it)
    st_side_saved = st.side
    st.side = color
    my_moves = _generate_moves(st, color)
    st.side = _opp(color)
    en_moves = _generate_moves(st, _opp(color))
    st.side = st_side_saved
    mobility = 0.02 * (len(my_moves) - len(en_moves))

    # Safety: penalize hanging pieces
    # Keep it light to avoid too much computation.
    safety = 0.0
    for p in my_men | my_kings:
        if _can_be_captured_next(st, color, p):
            safety -= 0.06
    for p in en_men | en_kings:
        if _can_be_captured_next(st, _opp(color), p):
            safety += 0.06

    return material + advancement + center + mobility + safety


class _TTEntry:
    __slots__ = ("depth", "val", "flag", "best")
    # flag: 0 exact, -1 upperbound, +1 lowerbound

    def __init__(self, depth: int, val: float, flag: int, best: Optional[Move]):
        self.depth = depth
        self.val = val
        self.flag = flag
        self.best = best


def _order_moves(st: _State, moves: List[Move]) -> List[Move]:
    color = st.side
    enemy_men, enemy_kings = _enemy_for(st, color)
    enemy_kset = set(enemy_kings)

    def score(mv: Move) -> float:
        s = 0.0
        # Prefer captures
        if mv.cap is not None:
            s += 10.0
            if mv.cap in enemy_kset:
                s += 2.0
        # Prefer promotion
        prom_row = 0 if color == "b" else 7
        if mv.to[0] == prom_row and mv.fr in (_pieces_for(st, color)[0]):  # from a man
            s += 3.0
        # Prefer central squares
        r, c = mv.to
        s += 0.2 * (3.5 - (abs(r - 3.5) + abs(c - 3.5)) / 2.0)
        # Slightly prefer forward progress for men
        if mv.fr in (_pieces_for(st, color)[0]):  # man
            s += 0.15 * (mv.to[0] - mv.fr[0]) if color == "w" else 0.15 * (mv.fr[0] - mv.to[0])
        # Avoid immediate recapture (quick check)
        ns = _apply_move(st, mv)
        if _can_be_captured_next(ns, _opp(ns.side), mv.to):  # after apply, side switched
            s -= 1.0
        return s

    return sorted(moves, key=score, reverse=True)


def _negamax(
    st: _State,
    depth: int,
    alpha: float,
    beta: float,
    root_color: str,
    tt: Dict[Tuple, _TTEntry],
    t_end: float,
) -> Tuple[float, Optional[Move]]:
    if time.perf_counter() >= t_end:
        # Time cutoff: return static evaluation.
        return _evaluate(st, root_color) * (1.0 if st.side == root_color else -1.0), None

    key = st.key()
    if (ent := tt.get(key)) is not None and ent.depth >= depth:
        if ent.flag == 0:
            return ent.val, ent.best
        if ent.flag < 0:  # upper
            beta = min(beta, ent.val)
        else:  # lower
            alpha = max(alpha, ent.val)
        if alpha >= beta:
            return ent.val, ent.best

    moves = _generate_moves(st, st.side)
    if not moves:
        # No legal moves: losing for side to move.
        val = -1e6 + (6 - depth) * 10.0
        return val, None

    if depth == 0:
        val = _evaluate(st, root_color) * (1.0 if st.side == root_color else -1.0)
        return val, None

    best_move: Optional[Move] = None
    moves = _order_moves(st, moves)

    a0 = alpha
    best_val = -math.inf
    for mv in moves:
        ns = _apply_move(st, mv)
        val, _ = _negamax(ns, depth - 1, -beta, -alpha, root_color, tt, t_end)
        val = -val
        if val > best_val:
            best_val = val
            best_move = mv
        if best_val > alpha:
            alpha = best_val
        if alpha >= beta:
            break

    # store TT
    flag = 0
    if best_val <= a0:
        flag = -1
    elif best_val >= beta:
        flag = 1
    tt[key] = _TTEntry(depth, best_val, flag, best_move)
    return best_val, best_move


def policy(
    my_men, my_kings, opp_men, opp_kings, color
) -> tuple[tuple[int, int], tuple[int, int]]:
    # Build full state
    my_men_s = set(map(tuple, my_men))
    my_kings_s = set(map(tuple, my_kings))
    opp_men_s = set(map(tuple, opp_men))
    opp_kings_s = set(map(tuple, opp_kings))

    if color == "b":
        st = _State(my_men_s, my_kings_s, opp_men_s, opp_kings_s, side="b")
    else:
        st = _State(opp_men_s, opp_kings_s, my_men_s, my_kings_s, side="w")
        # Wait: the above would swap incorrectly. Correct mapping:
        # If color == "w", then my pieces are white, opponent are black.
        st = _State(b_men=opp_men_s, b_kings=opp_kings_s, w_men=my_men_s, w_kings=my_kings_s, side="w")

    # Generate legal moves; must return a legal move no matter what.
    legal = _generate_moves(st, st.side)
    if not legal:
        # Should indicate game over; but to avoid disqualification, attempt any pseudo-legal fallback.
        # Choose any piece and any adjacent empty diagonal if exists.
        occ = st.occupied()
        my_men_set, my_kings_set = _pieces_for(st, st.side)
        for p in list(my_men_set) + list(my_kings_set):
            is_king = p in my_kings_set
            for mv in _gen_simple_for_piece(st, st.side, p, is_king, occ):
                return (mv.fr, mv.to)
        # Absolute fallback (should never happen in valid calls)
        anyp = next(iter(my_men_set or my_kings_set))
        return (anyp, anyp)

    # Time-bounded iterative deepening
    t0 = time.perf_counter()
    t_end = t0 + 0.92  # keep margin under 1s
    tt: Dict[Tuple, _TTEntry] = {}

    # If forced capture, search a bit deeper since branching is smaller
    forced_capture = any(mv.cap is not None for mv in legal)
    max_depth = 10 if forced_capture else 8

    best_mv = None
    # Start with a safe heuristic best
    ordered = _order_moves(st, legal)
    best_mv = ordered[0]

    for d in range(1, max_depth + 1):
        if time.perf_counter() >= t_end:
            break
        val, mv = _negamax(st, d, -math.inf, math.inf, root_color=st.side, tt=tt, t_end=t_end)
        if time.perf_counter() >= t_end:
            break
        if mv is not None:
            best_mv = mv

    return (best_mv.fr, best_mv.to)
