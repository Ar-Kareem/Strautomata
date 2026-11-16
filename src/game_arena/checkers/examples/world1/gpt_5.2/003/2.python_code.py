
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Set

Move = Tuple[Tuple[int, int], Tuple[int, int]]  # ((fr,fc),(tr,tc))


@dataclass(frozen=True)
class State:
    bm: frozenset
    bk: frozenset
    wm: frozenset
    wk: frozenset
    side: str  # 'b' or 'w'


# ----------------- Core rules / move generation -----------------

def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def _occupied(state: State) -> Set[Tuple[int, int]]:
    return set(state.bm) | set(state.bk) | set(state.wm) | set(state.wk)


def _my_sets(state: State, side: str):
    if side == 'b':
        return set(state.bm), set(state.bk)
    else:
        return set(state.wm), set(state.wk)


def _opp_sets(state: State, side: str):
    if side == 'b':
        return set(state.wm), set(state.wk)
    else:
        return set(state.bm), set(state.bk)


def _man_forward_dir(side: str) -> int:
    # rows increase bottom-to-top; black moves "down" to lower row values
    return -1 if side == 'b' else 1


def _promotion_row(side: str) -> int:
    return 0 if side == 'b' else 7


def _gen_moves_for_piece(
    state: State,
    side: str,
    pos: Tuple[int, int],
    is_king: bool,
    captures_only: bool
) -> List[Move]:
    r, c = pos
    occ = _occupied(state)
    opp_m, opp_k = _opp_sets(state, side)
    opp = opp_m | opp_k

    moves: List[Move] = []

    if is_king:
        step_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        cap_dirs = step_dirs
    else:
        d = _man_forward_dir(side)
        step_dirs = [(d, -1), (d, 1)]
        cap_dirs = [(2 * d, -2), (2 * d, 2)]

    # captures
    for dr, dc in cap_dirs:
        tr, tc = r + dr, c + dc
        mr, mc = r + dr // 2, c + dc // 2
        if _in_bounds(tr, tc) and (tr, tc) not in occ and (mr, mc) in opp:
            moves.append(((r, c), (tr, tc)))

    if captures_only:
        return moves

    # quiet moves
    for dr, dc in step_dirs:
        tr, tc = r + dr, c + dc
        if _in_bounds(tr, tc) and (tr, tc) not in occ:
            moves.append(((r, c), (tr, tc)))

    return moves


def generate_legal_moves(state: State) -> List[Move]:
    """Generates legal moves for state.side. Enforces mandatory capture."""
    side = state.side
    my_m, my_k = _my_sets(state, side)

    captures: List[Move] = []
    quiets: List[Move] = []

    for p in my_m:
        pm = _gen_moves_for_piece(state, side, p, is_king=False, captures_only=True)
        captures.extend(pm)
    for p in my_k:
        pk = _gen_moves_for_piece(state, side, p, is_king=True, captures_only=True)
        captures.extend(pk)

    if captures:
        return captures

    for p in my_m:
        quiets.extend(_gen_moves_for_piece(state, side, p, is_king=False, captures_only=False))
    for p in my_k:
        quiets.extend(_gen_moves_for_piece(state, side, p, is_king=True, captures_only=False))

    return quiets


def apply_move(state: State, move: Move) -> State:
    """Applies a single-step move (simple or single capture)."""
    (fr, fc), (tr, tc) = move
    side = state.side

    bm, bk, wm, wk = set(state.bm), set(state.bk), set(state.wm), set(state.wk)

    def remove_piece_at(rr, cc):
        if (rr, cc) in bm:
            bm.remove((rr, cc))
        elif (rr, cc) in bk:
            bk.remove((rr, cc))
        elif (rr, cc) in wm:
            wm.remove((rr, cc))
        elif (rr, cc) in wk:
            wk.remove((rr, cc))

    # identify moved piece kind
    if side == 'b':
        moving_is_king = (fr, fc) in bk
        if moving_is_king:
            bk.remove((fr, fc))
        else:
            bm.remove((fr, fc))
    else:
        moving_is_king = (fr, fc) in wk
        if moving_is_king:
            wk.remove((fr, fc))
        else:
            wm.remove((fr, fc))

    # capture?
    if abs(tr - fr) == 2 and abs(tc - fc) == 2:
        mr, mc = (fr + tr) // 2, (fc + tc) // 2
        remove_piece_at(mr, mc)

    # place moved piece, with promotion
    if not moving_is_king:
        if tr == _promotion_row(side):
            moving_is_king = True

    if side == 'b':
        (bk if moving_is_king else bm).add((tr, tc))
    else:
        (wk if moving_is_king else wm).add((tr, tc))

    next_side = 'w' if side == 'b' else 'b'
    return State(frozenset(bm), frozenset(bk), frozenset(wm), frozenset(wk), next_side)


# ----------------- Evaluation -----------------

def _base_eval_black_minus_white(state: State) -> float:
    # Material
    man_w = 100
    king_w = 175
    score = 0.0
    score += man_w * len(state.bm) + king_w * len(state.bk)
    score -= man_w * len(state.wm) + king_w * len(state.wk)

    # Men advancement towards promotion (small but important)
    # black promotes at row 0, so smaller r is better => (7-r)
    for (r, c) in state.bm:
        score += 2.5 * (7 - r)
        score += 0.5 * (3.5 - abs(c - 3.5))  # mild centralization
    for (r, c) in state.wm:
        score -= 2.5 * (r)
        score -= 0.5 * (3.5 - abs(c - 3.5))

    # Kings: centralize a bit
    for (r, c) in state.bk:
        score += 1.5 * (3.5 - abs(r - 3.5)) + 1.5 * (3.5 - abs(c - 3.5))
    for (r, c) in state.wk:
        score -= 1.5 * (3.5 - abs(r - 3.5)) + 1.5 * (3.5 - abs(c - 3.5))

    # Mobility (cheap approximation: difference in legal move counts)
    s_b = State(state.bm, state.bk, state.wm, state.wk, 'b')
    s_w = State(state.bm, state.bk, state.wm, state.wk, 'w')
    mb = len(generate_legal_moves(s_b))
    mw = len(generate_legal_moves(s_w))
    score += 3.0 * (mb - mw)

    # Tactics safety: if opponent has captures, it's dangerous
    # (penalize positions where the side to move next can capture a lot)
    # This helps avoid hanging pieces.
    opp_caps = 0
    if state.side == 'b':
        # after black moved, white to move (state.side), so if white has captures, bad for black
        caps = generate_legal_moves(s_w)
        # mandatory capture: if any capture exists, all moves returned are captures
        # detect capture by delta==2
        if caps and abs(caps[0][1][0] - caps[0][0][0]) == 2:
            opp_caps = len(caps)
        score -= 6.0 * opp_caps
    else:
        caps = generate_legal_moves(s_b)
        if caps and abs(caps[0][1][0] - caps[0][0][0]) == 2:
            opp_caps = len(caps)
        score += 6.0 * opp_caps

    return score


def evaluate_for_player_to_move(state: State) -> float:
    base = _base_eval_black_minus_white(state)
    return base if state.side == 'b' else -base


# ----------------- Search (iterative deepening alpha-beta negamax) -----------------

class Timeout(Exception):
    pass


def _move_heuristic(state: State, move: Move) -> float:
    """Used only for ordering moves before search (higher first)."""
    (fr, fc), (tr, tc) = move
    is_capture = abs(tr - fr) == 2
    h = 0.0
    if is_capture:
        h += 1000.0
        mr, mc = (fr + tr) // 2, (fc + tc) // 2
        # capturing a king is better
        if state.side == 'b':
            if (mr, mc) in state.wk:
                h += 80.0
            else:
                h += 30.0
        else:
            if (mr, mc) in state.bk:
                h += 80.0
            else:
                h += 30.0

    # promotion bonus for men
    if state.side == 'b':
        if (fr, fc) in state.bm and tr == 0:
            h += 120.0
    else:
        if (fr, fc) in state.wm and tr == 7:
            h += 120.0

    # centralization
    h += 2.0 * (3.5 - abs(tr - 3.5)) + 2.0 * (3.5 - abs(tc - 3.5))
    return h


def negamax(
    state: State,
    depth: int,
    alpha: float,
    beta: float,
    tt: Dict,
    deadline: float
) -> float:
    if time.time() >= deadline:
        raise Timeout()

    key = (state.bm, state.bk, state.wm, state.wk, state.side, depth)
    if key in tt:
        return tt[key]

    moves = generate_legal_moves(state)
    if depth == 0 or not moves:
        val = evaluate_for_player_to_move(state)
        tt[key] = val
        return val

    # order moves
    moves.sort(key=lambda m: _move_heuristic(state, m), reverse=True)

    best = -1e18
    for mv in moves:
        child = apply_move(state, mv)
        val = -negamax(child, depth - 1, -beta, -alpha, tt, deadline)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    tt[key] = best
    return best


def choose_best_move(state: State, time_limit: float = 0.92) -> Move:
    moves = generate_legal_moves(state)
    # Assuming non-terminal calls; still guard.
    if not moves:
        # No legal move exists; cannot return a legal move. In typical arenas this won't be called.
        # Fallback to a harmless placeholder (still likely rejected if truly terminal).
        any_piece = next(iter(state.bm or state.bk or state.wm or state.wk))
        return (any_piece, any_piece)

    if len(moves) == 1:
        return moves[0]

    deadline = time.time() + time_limit
    tt: Dict = {}

    # Root move ordering
    moves.sort(key=lambda m: _move_heuristic(state, m), reverse=True)

    best_move = moves[0]
    best_score = -1e18

    # Iterative deepening
    depth = 1
    while True:
        if time.time() >= deadline:
            break
        try:
            current_best_move = best_move
            current_best_score = -1e18
            alpha, beta = -1e18, 1e18

            for mv in moves:
                if time.time() >= deadline:
                    raise Timeout()
                child = apply_move(state, mv)
                val = -negamax(child, depth - 1, -beta, -alpha, tt, deadline)
                if val > current_best_score:
                    current_best_score = val
                    current_best_move = mv
                if val > alpha:
                    alpha = val

            best_move, best_score = current_best_move, current_best_score
            depth += 1
            # Practical cap (keeps TT size stable)
            if depth > 10:
                break
        except Timeout:
            break

    return best_move


# ----------------- Required API -----------------

def policy(my_men, my_kings, opp_men, opp_kings, color) -> Move:
    """
    Returns a legal move ((from_row,from_col),(to_row,to_col)).
    Captures are mandatory and enforced in move generation.
    """
    # Build absolute state by color
    if color == 'b':
        bm = frozenset(tuple(x) for x in my_men)
        bk = frozenset(tuple(x) for x in my_kings)
        wm = frozenset(tuple(x) for x in opp_men)
        wk = frozenset(tuple(x) for x in opp_kings)
        side = 'b'
    else:
        wm = frozenset(tuple(x) for x in my_men)
        wk = frozenset(tuple(x) for x in my_kings)
        bm = frozenset(tuple(x) for x in opp_men)
        bk = frozenset(tuple(x) for x in opp_kings)
        side = 'w'

    state = State(bm=bm, bk=bk, wm=wm, wk=wk, side=side)

    mv = choose_best_move(state)

    # Final safety: ensure we return a legal move; if not, fall back to first legal.
    legals = generate_legal_moves(state)
    if legals:
        if mv not in legals:
            mv = legals[0]
    return mv
