
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional

Square = Tuple[int, int]
Move = Tuple[Square, Square]


@dataclass(frozen=True)
class State:
    my_men: frozenset
    my_kings: frozenset
    opp_men: frozenset
    opp_kings: frozenset
    color: str  # side to move: 'b' or 'w'


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def is_dark(r: int, c: int) -> bool:
    return (r + c) % 2 == 1


def forward_dirs(color: str):
    # black moves downward (toward lower row values), white upward
    return [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]


def king_dirs():
    return [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def promotion_row(color: str) -> int:
    return 0 if color == 'b' else 7


def make_state(my_men, my_kings, opp_men, opp_kings, color) -> State:
    return State(frozenset(my_men), frozenset(my_kings), frozenset(opp_men), frozenset(opp_kings), color)


def occupied(state: State):
    return state.my_men | state.my_kings | state.opp_men | state.opp_kings


def swap_perspective(state: State) -> State:
    return State(state.opp_men, state.opp_kings, state.my_men, state.my_kings, 'w' if state.color == 'b' else 'b')


def simple_moves_for_piece(state: State, pos: Square, is_king_piece: bool) -> List[Move]:
    r, c = pos
    dirs = king_dirs() if is_king_piece else forward_dirs(state.color)
    occ = occupied(state)
    moves = []
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc) and is_dark(nr, nc) and (nr, nc) not in occ:
            moves.append((pos, (nr, nc)))
    return moves


def jump_dirs(is_king_piece: bool, color: str):
    return king_dirs() if is_king_piece else forward_dirs(color)


def capture_sequences_for_piece(state: State, pos: Square, is_king_piece: bool):
    """
    Returns list of sequences, each as:
      {
        'path': [start, ..., final],
        'state': resulting State with same side-to-move perspective,
        'captures': int
      }
    """
    results = []
    occ = occupied(state)

    def dfs(cur_pos: Square, my_men, my_kings, opp_men, opp_kings, king_now: bool, path: List[Square], capcount: int):
        found = False
        r, c = cur_pos
        dirs = jump_dirs(king_now, state.color)
        local_occ = my_men | my_kings | opp_men | opp_kings

        for dr, dc in dirs:
            mr, mc = r + dr, c + dc
            lr, lc = r + 2 * dr, c + 2 * dc
            if not (in_bounds(mr, mc) and in_bounds(lr, lc)):
                continue
            if not is_dark(lr, lc):
                continue
            if (lr, lc) in local_occ:
                continue
            if (mr, mc) in opp_men or (mr, mc) in opp_kings:
                found = True

                n_my_men = set(my_men)
                n_my_kings = set(my_kings)
                n_opp_men = set(opp_men)
                n_opp_kings = set(opp_kings)

                if king_now:
                    n_my_kings.remove(cur_pos)
                else:
                    n_my_men.remove(cur_pos)

                if (mr, mc) in n_opp_men:
                    n_opp_men.remove((mr, mc))
                else:
                    n_opp_kings.remove((mr, mc))

                landed = (lr, lc)
                promoted = False
                if not king_now and lr == promotion_row(state.color):
                    n_my_kings.add(landed)
                    promoted = True
                else:
                    if king_now:
                        n_my_kings.add(landed)
                    else:
                        n_my_men.add(landed)

                # If promoted during jump, in standard American checkers the move ends.
                if promoted:
                    results.append({
                        'path': path + [landed],
                        'state': State(frozenset(n_my_men), frozenset(n_my_kings),
                                       frozenset(n_opp_men), frozenset(n_opp_kings), state.color),
                        'captures': capcount + 1
                    })
                else:
                    dfs(landed, frozenset(n_my_men), frozenset(n_my_kings),
                        frozenset(n_opp_men), frozenset(n_opp_kings),
                        king_now, path + [landed], capcount + 1)

        if not found and capcount > 0:
            results.append({
                'path': path,
                'state': State(frozenset(my_men), frozenset(my_kings),
                               frozenset(opp_men), frozenset(opp_kings), state.color),
                'captures': capcount
            })

    dfs(pos, state.my_men, state.my_kings, state.opp_men, state.opp_kings, is_king_piece, [pos], 0)
    return results


def all_legal_actions(state: State):
    """
    Returns:
      ('capture', [seqdicts]) if any capture exists, else ('simple', [Move])
    """
    captures = []
    for p in state.my_men:
        captures.extend(capture_sequences_for_piece(state, p, False))
    for p in state.my_kings:
        captures.extend(capture_sequences_for_piece(state, p, True))

    if captures:
        max_caps = max(x['captures'] for x in captures)
        best_caps = [x for x in captures if x['captures'] == max_caps]
        return 'capture', best_caps

    moves = []
    for p in state.my_men:
        moves.extend(simple_moves_for_piece(state, p, False))
    for p in state.my_kings:
        moves.extend(simple_moves_for_piece(state, p, True))
    return 'simple', moves


def apply_simple_move(state: State, move: Move) -> State:
    (r1, c1), (r2, c2) = move
    src = (r1, c1)
    dst = (r2, c2)
    my_men = set(state.my_men)
    my_kings = set(state.my_kings)

    if src in my_men:
        my_men.remove(src)
        if r2 == promotion_row(state.color):
            my_kings.add(dst)
        else:
            my_men.add(dst)
    else:
        my_kings.remove(src)
        my_kings.add(dst)

    next_same_perspective = State(frozenset(my_men), frozenset(my_kings), state.opp_men, state.opp_kings, state.color)
    return swap_perspective(next_same_perspective)


def apply_capture_sequence_result(seqdict) -> State:
    # sequence result is still in same perspective; after move, swap side to move
    return swap_perspective(seqdict['state'])


def has_any_move(state: State) -> bool:
    kind, acts = all_legal_actions(state)
    return len(acts) > 0


def edge_bonus(pos: Square) -> float:
    r, c = pos
    return 0.25 if r in (0, 7) or c in (0, 7) else 0.0


def center_bonus(pos: Square) -> float:
    r, c = pos
    return 0.35 if 2 <= r <= 5 and 2 <= c <= 5 else 0.0


def advancement_score(pos: Square, color: str) -> float:
    r, _ = pos
    return (7 - r) * 0.12 if color == 'b' else r * 0.12


def evaluate(state: State) -> float:
    # Current perspective is side to move = "my"
    my_men = len(state.my_men)
    my_kings = len(state.my_kings)
    opp_men = len(state.opp_men)
    opp_kings = len(state.opp_kings)

    if my_men + my_kings == 0:
        return -10000.0
    if opp_men + opp_kings == 0:
        return 10000.0

    kind, acts = all_legal_actions(state)
    my_mob = len(acts)
    if my_mob == 0:
        return -9000.0

    opp_state = swap_perspective(state)
    okind, oacts = all_legal_actions(opp_state)
    opp_mob = len(oacts)
    if opp_mob == 0:
        return 9000.0

    score = 0.0
    score += 100.0 * (my_men - opp_men)
    score += 175.0 * (my_kings - opp_kings)
    score += 4.0 * (my_mob - opp_mob)

    for p in state.my_men:
        score += advancement_score(p, state.color)
        score += center_bonus(p)
        score += edge_bonus(p) * 0.6

    opp_color = 'w' if state.color == 'b' else 'b'
    for p in state.opp_men:
        score -= advancement_score(p, opp_color)
        score -= center_bonus(p)
        score -= edge_bonus(p) * 0.6

    for p in state.my_kings:
        score += center_bonus(p) * 1.2
    for p in state.opp_kings:
        score -= center_bonus(p) * 1.2

    # Tempo toward promotion lanes being open
    occ = occupied(state)
    for r, c in state.my_men:
        dr = -1 if state.color == 'b' else 1
        for dc in (-1, 1):
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and (nr, nc) not in occ:
                score += 0.4

    # Slight preference if captures available now
    if kind == 'capture':
        score += 2.0 * max((x['captures'] for x in acts), default=0)

    return score


def ordered_children(state: State):
    kind, acts = all_legal_actions(state)
    children = []
    if kind == 'capture':
        for seq in acts:
            child = apply_capture_sequence_result(seq)
            first = (seq['path'][0], seq['path'][1])
            heuristic = 500 + 50 * seq['captures']
            final_sq = seq['path'][-1]
            heuristic += center_bonus(final_sq)
            children.append((heuristic, first, child))
    else:
        for mv in acts:
            child = apply_simple_move(state, mv)
            heuristic = 0.0
            _, dst = mv
            src = mv[0]
            if src in state.my_men and dst[0] == promotion_row(state.color):
                heuristic += 120.0
            heuristic += center_bonus(dst)
            heuristic += edge_bonus(dst) * 0.2
            children.append((heuristic, mv, child))

    children.sort(key=lambda x: x[0], reverse=True)
    return children


def negamax(state: State, depth: int, alpha: float, beta: float) -> float:
    if depth == 0:
        return evaluate(state)

    children = ordered_children(state)
    if not children:
        return -9000.0

    best = -10**18
    for _, _, child in children:
        val = -negamax(child, depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def choose_move(state: State) -> Move:
    children = ordered_children(state)
    if not children:
        # Should not happen in valid arena states, but guard anyway.
        for p in list(state.my_men) + list(state.my_kings):
            return (p, p)

    piece_count = len(state.my_men) + len(state.my_kings) + len(state.opp_men) + len(state.opp_kings)
    if piece_count >= 18:
        depth = 4
    elif piece_count >= 10:
        depth = 6
    else:
        depth = 8

    best_move = children[0][1]
    best_val = -10**18
    alpha = -10**18
    beta = 10**18

    for _, mv, child in children:
        val = -negamax(child, depth - 1, -beta, -alpha)
        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val

    return best_move


def legal_fallback(state: State) -> Move:
    kind, acts = all_legal_actions(state)
    if kind == 'capture' and acts:
        path = acts[0]['path']
        return (path[0], path[1])
    if kind == 'simple' and acts:
        return acts[0]
    # Emergency invalid-state fallback: attempt to find any pseudo-legal destination.
    for p in state.my_men:
        for mv in simple_moves_for_piece(state, p, False):
            return mv
    for p in state.my_kings:
        for mv in simple_moves_for_piece(state, p, True):
            return mv
    # Absolute emergency; should never occur if a move exists.
    if state.my_men:
        p = next(iter(state.my_men))
        return (p, p)
    if state.my_kings:
        p = next(iter(state.my_kings))
        return (p, p)
    return ((0, 1), (0, 1))


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    state = make_state(my_men, my_kings, opp_men, opp_kings, color)
    try:
        mv = choose_move(state)
        kind, acts = all_legal_actions(state)
        if kind == 'capture':
            legal_first_steps = {(a['path'][0], a['path'][1]) for a in acts if len(a['path']) >= 2}
            if mv in legal_first_steps:
                return mv
        else:
            legal_moves = set(acts)
            if mv in legal_moves:
                return mv
        return legal_fallback(state)
    except Exception:
        return legal_fallback(state)
