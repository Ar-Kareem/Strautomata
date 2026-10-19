
import time

import numpy as np  # noqa: F401  (kept for the required signature)

# ----------------------------------------------------------------------
# Geometry for a 4x4 box grid (5x5 dots).
# Edge indexing:
#   horizontal edge (r, c): idx = r*4 + c        (r in 0..4, c in 0..3)
#   vertical   edge (r, c): idx = 20 + r*5 + c   (r in 0..3, c in 0..4)
# ----------------------------------------------------------------------
BOX_MASKS = []
_edge_boxes = [[] for _ in range(40)]
for _r in range(4):
    for _c in range(4):
        _edges = (
            _r * 4 + _c,            # top horizontal
            (_r + 1) * 4 + _c,      # bottom horizontal
            20 + _r * 5 + _c,       # left vertical
            20 + _r * 5 + _c + 1,   # right vertical
        )
        _m = 0
        for _e in _edges:
            _m |= 1 << _e
            _edge_boxes[_e].append(_r * 4 + _c)
        BOX_MASKS.append(_m)
BOX_MASKS = tuple(BOX_MASKS)
EDGE_BOXES = tuple(tuple(x) for x in _edge_boxes)
FULL = (1 << 40) - 1

_popcount = getattr(int, "bit_count", lambda x: bin(x).count("1"))


class _Timeout(Exception):
    pass


class _Searcher:
    __slots__ = ("deadline", "tt", "nodes")

    def __init__(self, deadline):
        self.deadline = deadline
        self.tt = {}
        self.nodes = 0

    def _order(self, mask, tt_best):
        """Generate ordered moves: TT move, captures, safe moves, unsafe moves."""
        moves = []
        rem = FULL & ~mask
        while rem:
            bit = rem & -rem
            rem ^= bit
            e = bit.bit_length() - 1
            cap = 0
            danger = 0
            twos = 0
            for b in EDGE_BOXES[e]:
                cnt = _popcount(mask & BOX_MASKS[b])
                if cnt == 3:
                    cap += 1
                elif cnt == 2:
                    danger += 1
                elif cnt == 1:
                    twos += 1
            nm = mask | bit
            if e == tt_best:
                key = (0, 0, 0)
            elif cap:
                key = (1, -cap, 0)
            elif danger:
                key = (3, danger, 0)
            else:
                key = (2, twos, 0)
            moves.append((key, cap, e, nm))
        moves.sort(key=lambda t: t[0])
        return moves

    def negamax(self, mask, side, depth, alpha, beta):
        """Future box-difference from the perspective of the player to move."""
        self.nodes += 1
        if (self.nodes & 2047) == 0 and time.perf_counter() > self.deadline:
            raise _Timeout
        if mask == FULL:
            return 0

        a0, b0 = alpha, beta
        tt_best = -1
        key = (mask << 1) | side
        ent = self.tt.get(key)
        if ent is not None:
            ed, ev, ef, eb = ent
            if ed >= depth:
                if ef == 0:
                    return ev
                elif ef == 1:
                    if ev > alpha:
                        alpha = ev
                else:
                    if ev < beta:
                        beta = ev
                if alpha >= beta:
                    return ev
            tt_best = eb

        best = -1000
        beste = -1
        searched = False
        for _, cap, e, nm in self._order(mask, tt_best):
            if cap:
                # Capturing keeps the turn; depth is preserved (chains resolved).
                val = cap + self.negamax(nm, side, depth, alpha, beta)
            else:
                if depth <= 0:
                    continue  # quiescence: only captures beyond the horizon
                val = -self.negamax(nm, side ^ 1, depth - 1, -beta, -alpha)
            searched = True
            if val > best:
                best = val
                beste = e
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        if not searched:
            return 0  # quiet leaf: no immediate captures available

        if best <= a0:
            flag = 2  # upper bound
        elif best >= b0:
            flag = 1  # lower bound
        else:
            flag = 0  # exact
        self.tt[key] = (depth, best, flag, beste)
        return best

    def root(self, mask, depth, prev_best):
        alpha, beta = -1000, 1000
        best = -1000
        beste = prev_best
        for _, cap, e, nm in self._order(mask, prev_best):
            if cap:
                val = cap + self.negamax(nm, 0, depth, alpha, beta)
            else:
                val = -self.negamax(nm, 1, depth - 1, -beta, -alpha)
            if val > best:
                best = val
                beste = e
            if val > alpha:
                alpha = val
        return best, beste


def _edge_str(e):
    if e < 20:
        return "%d,%d,H" % (e // 4, e % 4)
    e -= 20
    return "%d,%d,V" % (e // 5, e % 5)


def _policy_impl(horizontal, vertical, capture):
    deadline = time.perf_counter() + 0.85

    mask = 0
    for r in range(5):
        base = r * 4
        for c in range(4):
            if horizontal[r, c] != 0:
                mask |= 1 << (base + c)
    for r in range(4):
        base = 20 + r * 5
        for c in range(5):
            if vertical[r, c] != 0:
                mask |= 1 << (base + c)

    rem = FULL & ~mask
    if rem == 0:
        return "0,0,H"  # game already over; should never be called

    searcher = _Searcher(deadline)

    # Instant fallback: best ordered move (capture > safe > unsafe).
    moves = searcher._order(mask, -1)
    best_edge = moves[0][2]
    if len(moves) == 1:
        return _edge_str(best_edge)

    # Upper bound on remaining boxes, for early termination on a won position.
    completed = 0
    for bm in BOX_MASKS:
        if (mask & bm) == bm:
            completed += 1
    boxes_left = 16 - completed

    max_depth = _popcount(rem)  # full solve depth bound
    depth = 1
    while depth <= max_depth:
        val, e = searcher.root(mask, depth, best_edge)
        if e is not None and e >= 0:
            best_edge = e
        if val >= boxes_left:
            break  # cannot do better: every remaining box is ours
        if time.perf_counter() > deadline - 0.05:
            break
        depth += 1

    return _edge_str(best_edge)


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    try:
        return _policy_impl(horizontal, vertical, capture)
    except Exception:
        # Emergency fallback: always return some legal move.
        try:
            for r in range(5):
                for c in range(4):
                    if horizontal[r, c] == 0:
                        return "%d,%d,H" % (r, c)
            for r in range(4):
                for c in range(5):
                    if vertical[r, c] == 0:
                        return "%d,%d,V" % (r, c)
        except Exception:
            pass
        return "0,0,H"
