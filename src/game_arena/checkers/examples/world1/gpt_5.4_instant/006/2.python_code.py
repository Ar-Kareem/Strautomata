
from __future__ import annotations

from typing import List, Tuple, Dict, Set, Optional
import math
import time

Square = Tuple[int, int]
Move = Tuple[Square, Square]


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.perf_counter()
    time_limit = 0.92

    # Normalize to tuples/sets
    my_men = set(map(tuple, my_men))
    my_kings = set(map(tuple, my_kings))
    opp_men = set(map(tuple, opp_men))
    opp_kings = set(map(tuple, opp_kings))

    root = State(my_men, my_kings, opp_men, opp_kings, color)

    legal = generate_legal_moves(root)
    if not legal:
        # Should not happen in valid arena states, but must return something.
        # Return any placeholder legal-looking move from own pieces if possible.
        for s in list(my_men) + list(my_kings):
            return (s, s)
        return ((0, 1), (0, 1))

    # Move ordering at root
    legal = order_moves(root, legal)

    best_move = legal[0]
    best_score = -INF

    # Iterative deepening
    depth = 1
    try:
        while depth <= 8:
            if time.perf_counter() - start_time > time_limit:
                break

            score, move = alphabeta_root(root, depth, start_time, time_limit)
            if move is not None:
                best_move = move
                best_score = score
            depth += 1
    except TimeoutError:
        pass

    # Safety: ensure returned move is legal
    if best_move not in legal:
        best_move = legal[0]
    return best_move


INF = 10**9


class State:
    __slots__ = ("my_men", "my_kings", "opp_men", "opp_kings", "color")

    def __init__(self, my_men: Set[Square], my_kings: Set[Square],
                 opp_men: Set[Square], opp_kings: Set[Square], color: str):
        self.my_men = my_men
        self.my_kings = my_kings
        self.opp_men = opp_men
        self.opp_kings = opp_kings
        self.color = color  # side to move: 'b' or 'w'

    def key(self):
        return (
            tuple(sorted(self.my_men)),
            tuple(sorted(self.my_kings)),
            tuple(sorted(self.opp_men)),
            tuple(sorted(self.opp_kings)),
            self.color,
        )


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def playable(r: int, c: int) -> bool:
    return (r + c) % 2 == 1


def forward_dirs(color: str):
    # black moves downward (lower row), white upward (higher row)
    return [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]


def all_dirs():
    return [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def promotion_row(color: str) -> int:
    return 0 if color == 'b' else 7


def occupied(state: State) -> Set[Square]:
    return state.my_men | state.my_kings | state.opp_men | state.opp_kings


def generate_legal_moves(state: State) -> List[Move]:
    caps = generate_captures(state)
    if caps:
        return caps
    return generate_quiet_moves(state)


def generate_captures(state: State) -> List[Move]:
    occ = occupied(state)
    enemy = state.opp_men | state.opp_kings
    moves = []

    for r, c in state.my_men:
        for dr, dc in forward_dirs(state.color):
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if in_bounds(tr, tc) and playable(tr, tc):
                if (mr, mc) in enemy and (tr, tc) not in occ:
                    moves.append(((r, c), (tr, tc)))

    for r, c in state.my_kings:
        for dr, dc in all_dirs():
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if in_bounds(tr, tc) and playable(tr, tc):
                if (mr, mc) in enemy and (tr, tc) not in occ:
                    moves.append(((r, c), (tr, tc)))

    return moves


def generate_quiet_moves(state: State) -> List[Move]:
    occ = occupied(state)
    moves = []

    for r, c in state.my_men:
        for dr, dc in forward_dirs(state.color):
            tr, tc = r + dr, c + dc
            if in_bounds(tr, tc) and playable(tr, tc) and (tr, tc) not in occ:
                moves.append(((r, c), (tr, tc)))

    for r, c in state.my_kings:
        for dr, dc in all_dirs():
            tr, tc = r + dr, c + dc
            if in_bounds(tr, tc) and playable(tr, tc) and (tr, tc) not in occ:
                moves.append(((r, c), (tr, tc)))

    return moves


def apply_move(state: State, move: Move) -> State:
    (fr, fc), (tr, tc) = move

    my_men = set(state.my_men)
    my_kings = set(state.my_kings)
    opp_men = set(state.opp_men)
    opp_kings = set(state.opp_kings)

    was_king = (fr, fc) in my_kings
    was_man = (fr, fc) in my_men

    if was_king:
        my_kings.remove((fr, fc))
    elif was_man:
        my_men.remove((fr, fc))
    else:
        # Invalid source; keep state but swap perspective to avoid crash.
        return State(opp_men, opp_kings, my_men, my_kings, 'w' if state.color == 'b' else 'b')

    # Capture
    if abs(tr - fr) == 2 and abs(tc - fc) == 2:
        mr, mc = (fr + tr) // 2, (fc + tc) // 2
        if (mr, mc) in opp_men:
            opp_men.remove((mr, mc))
        elif (mr, mc) in opp_kings:
            opp_kings.remove((mr, mc))

    # Place moved piece, promoting if applicable
    if was_king:
        my_kings.add((tr, tc))
    else:
        if tr == promotion_row(state.color):
            my_kings.add((tr, tc))
        else:
            my_men.add((tr, tc))

    # Swap side to move / perspective
    next_color = 'w' if state.color == 'b' else 'b'
    return State(opp_men, opp_kings, my_men, my_kings, next_color)


def order_moves(state: State, moves: List[Move]) -> List[Move]:
    enemy_attack_squares = set()
    # Approximate opponent capture landing squares after our move not known here,
    # so use static heuristics only.
    scored = []
    for mv in moves:
        score = 0
        (fr, fc), (tr, tc) = mv
        is_cap = abs(tr - fr) == 2
        if is_cap:
            score += 100
            mr, mc = (fr + tr) // 2, (fc + tc) // 2
            if (mr, mc) in state.opp_kings:
                score += 25
            else:
                score += 15
        if (fr, fc) in state.my_men and tr == promotion_row(state.color):
            score += 80
        # centrality
        score += 6 - (abs(3.5 - tr) + abs(3.5 - tc))
        # advancement for men
        if (fr, fc) in state.my_men:
            score += (7 - tr) if state.color == 'b' else tr
        scored.append((score, mv))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [mv for _, mv in scored]


TT: Dict[Tuple, Tuple[int, int]] = {}


def alphabeta_root(state: State, depth: int, start_time: float, time_limit: float):
    legal = order_moves(state, generate_legal_moves(state))
    if not legal:
        return -INF + 1, None

    alpha = -INF
    beta = INF
    best_move = legal[0]
    best_score = -INF

    for mv in legal:
        if time.perf_counter() - start_time > time_limit:
            raise TimeoutError
        child = apply_move(state, mv)
        score = -alphabeta(child, depth - 1, -beta, -alpha, start_time, time_limit)
        if score > best_score:
            best_score = score
            best_move = mv
        if score > alpha:
            alpha = score

    return best_score, best_move


def alphabeta(state: State, depth: int, alpha: int, beta: int, start_time: float, time_limit: float) -> int:
    if time.perf_counter() - start_time > time_limit:
        raise TimeoutError

    key = state.key()
    tt = TT.get((key, depth))
    if tt is not None:
        return tt[1]

    legal = generate_legal_moves(state)
    if not legal:
        # No legal move = loss for side to move
        return -200000

    if depth <= 0:
        val = evaluate(state, legal)
        TT[(key, depth)] = (depth, val)
        return val

    legal = order_moves(state, legal)
    best = -INF

    for mv in legal:
        child = apply_move(state, mv)
        score = -alphabeta(child, depth - 1, -beta, -alpha, start_time, time_limit)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    TT[(key, depth)] = (depth, best)
    return best


def evaluate(state: State, legal_moves: Optional[List[Move]] = None) -> int:
    my_men = state.my_men
    my_kings = state.my_kings
    opp_men = state.opp_men
    opp_kings = state.opp_kings

    # Terminal-like
    if not my_men and not my_kings:
        return -200000
    if not opp_men and not opp_kings:
        return 200000

    score = 0

    # Material
    score += 100 * len(my_men)
    score += 175 * len(my_kings)
    score -= 100 * len(opp_men)
    score -= 175 * len(opp_kings)

    # Advancement for men
    for r, c in my_men:
        score += (7 - r) * 7 if state.color == 'b' else r * 7
        # edge pieces are often a bit safer
        if c == 0 or c == 7:
            score += 4
        # center
        if 2 <= r <= 5 and 2 <= c <= 5:
            score += 5

    opp_color = 'w' if state.color == 'b' else 'b'
    for r, c in opp_men:
        score -= ((7 - r) * 7 if opp_color == 'b' else r * 7)
        if c == 0 or c == 7:
            score -= 4
        if 2 <= r <= 5 and 2 <= c <= 5:
            score -= 5

    # Kings prefer center/mobility
    for r, c in my_kings:
        score += 8
        if 2 <= r <= 5 and 2 <= c <= 5:
            score += 8
    for r, c in opp_kings:
        score -= 8
        if 2 <= r <= 5 and 2 <= c <= 5:
            score -= 8

    # Back-rank guard for men
    home_row = 7 if state.color == 'b' else 0
    opp_home_row = 7 if opp_color == 'b' else 0
    score += 6 * sum(1 for r, _ in my_men if r == home_row)
    score -= 6 * sum(1 for r, _ in opp_men if r == opp_home_row)

    # Mobility
    if legal_moves is None:
        legal_moves = generate_legal_moves(state)
    score += 3 * len(legal_moves)

    opp_state = State(set(opp_men), set(opp_kings), set(my_men), set(my_kings), opp_color)
    opp_legal = generate_legal_moves(opp_state)
    score -= 3 * len(opp_legal)

    # Immediate tactical pressure
    my_caps = sum(1 for mv in legal_moves if abs(mv[0][0] - mv[1][0]) == 2)
    opp_caps = sum(1 for mv in opp_legal if abs(mv[0][0] - mv[1][0]) == 2)
    score += 20 * my_caps
    score -= 20 * opp_caps

    # Promotion threats
    for r, c in my_men:
        dist = r if state.color == 'b' else (7 - r)
        score += max(0, 6 - dist) * 3
    for r, c in opp_men:
        dist = r if opp_color == 'b' else (7 - r)
        score -= max(0, 6 - dist) * 3

    return int(score)
