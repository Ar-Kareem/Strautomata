
from __future__ import annotations

from typing import List, Tuple, Dict, Optional

Coord = Tuple[int, int]
Move = Tuple[Coord, Coord]


# ---------------------------
# Core board / state helpers
# ---------------------------

DARK_SQUARES = {(r, c) for r in range(8) for c in range(8) if (r + c) % 2 == 1}


class State:
    __slots__ = ("my_men", "my_kings", "opp_men", "opp_kings", "color")

    def __init__(self, my_men, my_kings, opp_men, opp_kings, color):
        self.my_men = set(my_men)
        self.my_kings = set(my_kings)
        self.opp_men = set(opp_men)
        self.opp_kings = set(opp_kings)
        self.color = color  # side to move: 'b' or 'w'

    def clone(self) -> "State":
        return State(
            list(self.my_men),
            list(self.my_kings),
            list(self.opp_men),
            list(self.opp_kings),
            self.color,
        )

    def key(self):
        return (
            tuple(sorted(self.my_men)),
            tuple(sorted(self.my_kings)),
            tuple(sorted(self.opp_men)),
            tuple(sorted(self.opp_kings)),
            self.color,
        )


def inside(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def promotion_row(color: str) -> int:
    return 0 if color == "b" else 7


def man_dirs(color: str):
    # black moves downward in row value, white upward
    return [(-1, -1), (-1, 1)] if color == "b" else [(1, -1), (1, 1)]


def king_dirs():
    return [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def occupied_map(state: State) -> Dict[Coord, int]:
    occ = {}
    for p in state.my_men:
        occ[p] = 1
    for p in state.my_kings:
        occ[p] = 2
    for p in state.opp_men:
        occ[p] = -1
    for p in state.opp_kings:
        occ[p] = -2
    return occ


# ---------------------------
# Move generation
# ---------------------------

def simple_moves_for_piece(state: State, pos: Coord, is_king: bool) -> List[Move]:
    occ = occupied_map(state)
    r, c = pos
    dirs = king_dirs() if is_king else man_dirs(state.color)
    moves = []
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        if inside(nr, nc) and (nr, nc) in DARK_SQUARES and (nr, nc) not in occ:
            moves.append((pos, (nr, nc)))
    return moves


def capture_sequences_from_piece(state: State, pos: Coord, is_king: bool):
    """
    Returns list of tuples:
      (final_pos, captured_count, resulting_state_after_full_sequence)
    We only need final destination for API, but internally search over full resulting states.
    """
    results = []
    occ = occupied_map(state)

    def rec(cur_state: State, cur_pos: Coord, cur_is_king: bool, captured: int):
        nonlocal results
        cur_occ = occupied_map(cur_state)
        found = False
        dirs = king_dirs() if cur_is_king else man_dirs(cur_state.color)
        for dr, dc in dirs:
            mid = (cur_pos[0] + dr, cur_pos[1] + dc)
            land = (cur_pos[0] + 2 * dr, cur_pos[1] + 2 * dc)
            if not (inside(*mid) and inside(*land)):
                continue
            if land not in DARK_SQUARES:
                continue
            if land in cur_occ:
                continue

            enemy_at_mid = mid in cur_state.opp_men or mid in cur_state.opp_kings
            if not enemy_at_mid:
                continue

            found = True
            ns = cur_state.clone()

            # remove moving piece
            if cur_pos in ns.my_men:
                ns.my_men.remove(cur_pos)
                moving_was_king = False
            else:
                ns.my_kings.remove(cur_pos)
                moving_was_king = True

            # remove captured enemy
            if mid in ns.opp_men:
                ns.opp_men.remove(mid)
            else:
                ns.opp_kings.remove(mid)

            # place moved piece, with promotion if applicable
            became_king = moving_was_king
            if not moving_was_king and land[0] == promotion_row(ns.color):
                became_king = True

            if became_king:
                ns.my_kings.add(land)
            else:
                ns.my_men.add(land)

            # Continue multi-capture if possible.
            rec(ns, land, became_king, captured + 1)

        if not found and captured > 0:
            results.append((cur_pos, captured, cur_state))

    rec(state, pos, is_king, 0)
    return results


def legal_moves_with_states(state: State):
    capture_moves = []
    all_capture_lines = []

    for p in state.my_men:
        seqs = capture_sequences_from_piece(state, p, False)
        for final_pos, cap_count, res_state in seqs:
            all_capture_lines.append(((p, final_pos), cap_count, res_state))

    for p in state.my_kings:
        seqs = capture_sequences_from_piece(state, p, True)
        for final_pos, cap_count, res_state in seqs:
            all_capture_lines.append(((p, final_pos), cap_count, res_state))

    if all_capture_lines:
        max_caps = max(x[1] for x in all_capture_lines)
        # Prefer maximum captures if multiple are available.
        capture_moves = [(mv, st) for mv, cc, st in all_capture_lines if cc == max_caps]
        return capture_moves, True

    simple = []
    for p in state.my_men:
        for mv in simple_moves_for_piece(state, p, False):
            ns = apply_simple_move(state, mv)
            simple.append((mv, ns))
    for p in state.my_kings:
        for mv in simple_moves_for_piece(state, p, True):
            ns = apply_simple_move(state, mv)
            simple.append((mv, ns))
    return simple, False


def apply_simple_move(state: State, move: Move) -> State:
    (fr, fc), (tr, tc) = move
    ns = state.clone()
    src = (fr, fc)
    dst = (tr, tc)
    if src in ns.my_men:
        ns.my_men.remove(src)
        if tr == promotion_row(ns.color):
            ns.my_kings.add(dst)
        else:
            ns.my_men.add(dst)
    else:
        ns.my_kings.remove(src)
        ns.my_kings.add(dst)
    return ns


def switch_perspective(state: State) -> State:
    # Next player becomes "my" side.
    return State(
        list(state.opp_men),
        list(state.opp_kings),
        list(state.my_men),
        list(state.my_kings),
        "w" if state.color == "b" else "b",
    )


# ---------------------------
# Evaluation
# ---------------------------

def piece_advancement_bonus(pos: Coord, color: str) -> float:
    r, _ = pos
    return (7 - r) if color == "b" else r


def center_bonus(pos: Coord) -> float:
    r, c = pos
    return 3.5 - (abs(r - 3.5) + abs(c - 3.5)) / 2.0


def is_edge(pos: Coord) -> bool:
    r, c = pos
    return r == 0 or r == 7 or c == 0 or c == 7


def defended_by_friend(state: State, pos: Coord) -> bool:
    # Approximate: a piece is defended if a friendly piece is on a backward adjacent square.
    r, c = pos
    occ = occupied_map(state)
    # For our side, enemy would need to approach from "forward" relative to them,
    # so friendly support from behind is useful.
    back_dirs = [(1, -1), (1, 1)] if state.color == "b" else [(-1, -1), (-1, 1)]
    for dr, dc in back_dirs:
        sq = (r + dr, c + dc)
        if inside(*sq) and sq in occ and occ[sq] > 0:
            return True
    return False


def vulnerable_piece(state: State, pos: Coord, is_king_piece: bool) -> bool:
    # Approximate immediate capturability by opponent after side switch.
    # Check if opponent has adjacent piece with empty landing square over this piece.
    occ = occupied_map(state)
    r, c = pos
    for dr, dc in king_dirs():
        er, ec = r - dr, c - dc
        lr, lc = r + dr, c + dc
        if not (inside(er, ec) and inside(lr, lc)):
            continue
        if (lr, lc) not in DARK_SQUARES:
            continue
        if (lr, lc) in occ:
            continue
        if (er, ec) in state.opp_kings:
            return True
        if (er, ec) in state.opp_men:
            # Opponent men can only capture in their movement direction.
            # Opponent color is opposite of state.color.
            opp_color = "w" if state.color == "b" else "b"
            dirs = man_dirs(opp_color)
            if (dr, dc) in dirs:
                return True
    return False


def evaluate(state: State) -> float:
    my_men = len(state.my_men)
    my_kings = len(state.my_kings)
    opp_men = len(state.opp_men)
    opp_kings = len(state.opp_kings)

    score = 0.0
    score += 100.0 * (my_men - opp_men)
    score += 180.0 * (my_kings - opp_kings)

    for p in state.my_men:
        score += 7.0 * piece_advancement_bonus(p, state.color)
        score += 4.0 * center_bonus(p)
        if is_edge(p):
            score += 2.0
        if defended_by_friend(state, p):
            score += 5.0
        if vulnerable_piece(state, p, False):
            score -= 12.0

    for p in state.my_kings:
        score += 10.0 * center_bonus(p)
        if defended_by_friend(state, p):
            score += 4.0
        if vulnerable_piece(state, p, True):
            score -= 14.0

    for p in state.opp_men:
        opp_color = "w" if state.color == "b" else "b"
        score -= 7.0 * piece_advancement_bonus(p, opp_color)
        score -= 4.0 * center_bonus(p)
        if is_edge(p):
            score -= 2.0

    for p in state.opp_kings:
        score -= 10.0 * center_bonus(p)

    # Mobility
    my_moves, my_caps = legal_moves_with_states(state)
    if not my_moves:
        return -100000.0
    score += 1.5 * len(my_moves)
    if my_caps:
        score += 8.0

    opp_state = switch_perspective(state)
    opp_moves, opp_caps = legal_moves_with_states(opp_state)
    if not opp_moves:
        return 100000.0
    score -= 1.2 * len(opp_moves)
    if opp_caps:
        score -= 8.0

    return score


# ---------------------------
# Search
# ---------------------------

TT = {}

def order_moves(moves_with_states, maximizing=True):
    scored = []
    for mv, st in moves_with_states:
        v = evaluate(st)
        scored.append((v, mv, st))
    scored.sort(reverse=maximizing, key=lambda x: x[0])
    return [(mv, st) for v, mv, st in scored]


def alphabeta(state: State, depth: int, alpha: float, beta: float) -> float:
    key = (state.key(), depth, alpha, beta)
    if key in TT:
        return TT[key]

    moves, _ = legal_moves_with_states(state)
    if depth == 0 or not moves:
        val = evaluate(state)
        TT[key] = val
        return val

    moves = order_moves(moves, maximizing=True)

    best = -10**18
    for mv, child_same_perspective in moves:
        nxt = switch_perspective(child_same_perspective)
        val = -alphabeta(nxt, depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    TT[key] = best
    return best


def choose_move(state: State) -> Move:
    moves, is_capture = legal_moves_with_states(state)
    if not moves:
        # Should not happen in valid ongoing games, but keep a robust fallback.
        all_pieces = list(state.my_men) + list(state.my_kings)
        if all_pieces:
            p = all_pieces[0]
            return (p, p)
        return ((0, 1), (0, 1))

    # If only one legal move, return it.
    if len(moves) == 1:
        return moves[0][0]

    # Dynamic depth: deeper in smaller positions.
    total_pieces = len(state.my_men) + len(state.my_kings) + len(state.opp_men) + len(state.opp_kings)
    if total_pieces >= 18:
        depth = 5
    elif total_pieces >= 10:
        depth = 7
    else:
        depth = 9

    # Capturing positions are tactically sharper; search a bit deeper if branching is low.
    if is_capture and len(moves) <= 4:
        depth += 1

    ordered = order_moves(moves, maximizing=True)
    best_move = ordered[0][0]
    best_val = -10**18
    alpha = -10**18
    beta = 10**18

    for mv, child in ordered:
        nxt = switch_perspective(child)
        val = -alphabeta(nxt, depth - 1, -beta, -alpha)
        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val

    return best_move


# ---------------------------
# Public API
# ---------------------------

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Return a legal move ((from_row, from_col), (to_row, to_col)).
    Captures are mandatory; generator enforces that.
    """
    # Sanitize inputs to playable dark squares only where possible.
    my_men = [tuple(x) for x in my_men if tuple(x) in DARK_SQUARES]
    my_kings = [tuple(x) for x in my_kings if tuple(x) in DARK_SQUARES]
    opp_men = [tuple(x) for x in opp_men if tuple(x) in DARK_SQUARES]
    opp_kings = [tuple(x) for x in opp_kings if tuple(x) in DARK_SQUARES]

    state = State(my_men, my_kings, opp_men, opp_kings, color)
    move = choose_move(state)

    # Final legality fallback
    legal, _ = legal_moves_with_states(state)
    legal_moves = [mv for mv, st in legal]
    if move in legal_moves:
        return move
    return legal_moves[0] if legal_moves else move
