
#!/usr/bin/env python3
# Checkers policy for 8x8 board
# Implements:
# def policy(my_men, my_kings, opp_men, opp_kings, color) -> ((r0,c0),(rf,cf))
#
# Notes:
# - Playable squares are dark squares where (row+col)%2 == 1
# - color 'b' moves downwards (to lower row values): forward step is -1
# - color 'w' moves upwards (to higher row values): forward step is +1
# - Men move one square forward for non-captures. For captures, men are allowed to jump in any diagonal direction.
# - Kings move/capture in all diagonal directions.
# - Captures are mandatory; multi-jumps supported.
# - Crowning happens at end of move (man promoted to king after landing on last row).
#
# The policy uses a negamax search with alpha-beta and returns a legal move.

import time
import math
import copy
from typing import List, Tuple, Set

Coord = Tuple[int, int]

# Parameters
MAN_VALUE = 100
KING_VALUE = 175
DEPTH_BASE = 6
TIME_LIMIT = 0.90  # seconds; keep a margin

# Helper utilities
def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def dark_square(r, c):
    return (r + c) % 2 == 1

def make_sets(lst):
    return set(tuple(x) for x in lst)

# Generate all legal moves (start->end) including multi-jump captures.
# Return list of tuples: (start_coord, end_coord, captured_set)
def generate_moves(my_men: Set[Coord], my_kings: Set[Coord],
                   opp_men: Set[Coord], opp_kings: Set[Coord],
                   color: str):
    all_my = my_men | my_kings
    occupied = all_my | opp_men | opp_kings
    dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    forward = -1 if color == 'b' else 1
    captures = []

    # Helper: recursively find jump sequences for a piece
    def jumps_from(pos, is_king, cur_my_men, cur_my_kings, cur_opp_men, cur_opp_kings, visited_capture_positions):
        r, c = pos
        results = []
        found = False
        # men may capture in all 4 diagonal directions (common rules allow backward captures)
        for dr, dc in dirs:
            mid = (r + dr, c + dc)
            land = (r + 2*dr, c + 2*dc)
            if not (in_bounds(mid[0], mid[1]) and in_bounds(land[0], land[1]) and dark_square(land[0], land[1])):
                continue
            # check mid is opponent piece
            if mid in cur_opp_men or mid in cur_opp_kings:
                if land in cur_my_men or land in cur_my_kings or land in cur_opp_men or land in cur_opp_kings:
                    continue
                if mid in visited_capture_positions:
                    # cannot capture same piece twice in sequence
                    continue
                # perform jump
                new_my_men = set(cur_my_men)
                new_my_kings = set(cur_my_kings)
                new_opp_men = set(cur_opp_men)
                new_opp_kings = set(cur_opp_kings)
                # remove captured
                if mid in new_opp_men:
                    new_opp_men.remove(mid)
                else:
                    new_opp_kings.remove(mid)
                # move piece from pos to land
                if is_king:
                    if pos in new_my_kings:
                        new_my_kings.remove(pos)
                    new_my_kings.add(land)
                else:
                    if pos in new_my_men:
                        new_my_men.remove(pos)
                    # if reaches promotion row, per our policy crowning occurs at end of move
                    new_my_men.add(land)
                new_visited = set(visited_capture_positions)
                new_visited.add(mid)
                # recursively search further jumps from landing
                further = jumps_from(land, is_king, new_my_men, new_my_kings, new_opp_men, new_opp_kings, new_visited)
                if further:
                    for (end_pos, caps) in further:
                        results.append((end_pos, {mid} | caps))
                        found = True
                else:
                    results.append((land, {mid}))
                    found = True
        return results

    # For each piece, collect jumps
    for p in my_men:
        j = jumps_from(p, False, my_men, my_kings, opp_men, opp_kings, set())
        for end, caps in j:
            captures.append((p, end, caps))
    for p in my_kings:
        j = jumps_from(p, True, my_men, my_kings, opp_men, opp_kings, set())
        for end, caps in j:
            captures.append((p, end, caps))

    if captures:
        return captures  # only captures are legal when available

    # No captures: generate quiet moves (single-step)
    moves = []
    for p in my_men:
        r, c = p
        for dc in (-1, 1):
            nr = r + forward
            nc = c + dc
            if in_bounds(nr, nc) and dark_square(nr, nc) and (nr, nc) not in occupied:
                moves.append((p, (nr, nc), frozenset()))
    for p in my_kings:
        r, c = p
        for dr, dc in dirs:
            nr = r + dr
            nc = c + dc
            if in_bounds(nr, nc) and dark_square(nr, nc) and (nr, nc) not in occupied:
                moves.append((p, (nr, nc), frozenset()))
    return moves

# Apply a move and return new sets for the player who moved, and opponent sets after move.
def apply_move(my_men, my_kings, opp_men, opp_kings, start, end, captured_set, color):
    new_my_men = set(my_men)
    new_my_kings = set(my_kings)
    new_opp_men = set(opp_men)
    new_opp_kings = set(opp_kings)

    # remove captured pieces
    for cap in captured_set:
        if cap in new_opp_men:
            new_opp_men.remove(cap)
        elif cap in new_opp_kings:
            new_opp_kings.remove(cap)
    # move piece
    if start in new_my_men:
        new_my_men.remove(start)
        # promotion occurs at the end of the move
        if (color == 'w' and end[0] == 7) or (color == 'b' and end[0] == 0):
            new_my_kings.add(end)
        else:
            new_my_men.add(end)
    elif start in new_my_kings:
        new_my_kings.remove(start)
        new_my_kings.add(end)
    else:
        # Should not happen
        pass

    return new_my_men, new_my_kings, new_opp_men, new_opp_kings

# Evaluation function: positive is good for "my side" passed to it.
def evaluate(my_men, my_kings, opp_men, opp_kings, color):
    score = 0.0
    # Material
    score += MAN_VALUE * (len(my_men) - len(opp_men))
    score += KING_VALUE * (len(my_kings) - len(opp_kings))

    # Advancement for men (closer to promotion is better)
    for r, c in my_men:
        if color == 'w':
            score += 4 * r  # higher row better
        else:
            score += 4 * (7 - r)
        # center control
        score += 3 * (3.5 - abs(3.5 - c))  # columns near 3.5 better

    for r, c in opp_men:
        if color == 'w':
            score -= 4 * r
        else:
            score -= 4 * (7 - r)
        score -= 3 * (3.5 - abs(3.5 - c))

    # kings like center
    for r, c in my_kings:
        score += 8 * (3.5 - abs(3.5 - r))
        score += 6 * (3.5 - abs(3.5 - c))
    for r, c in opp_kings:
        score -= 8 * (3.5 - abs(3.5 - r))
        score -= 6 * (3.5 - abs(3.5 - c))

    # Mobility (number of moves)
    my_moves = len(generate_moves(my_men, my_kings, opp_men, opp_kings, color))
    opp_color = 'b' if color == 'w' else 'w'
    opp_moves = len(generate_moves(opp_men, opp_kings, my_men, my_kings, opp_color))
    score += 6 * (my_moves - opp_moves)

    return score

# Negamax with alpha-beta, returns (score, best_move_tuple)
def negamax(my_men, my_kings, opp_men, opp_kings, color, depth, alpha, beta, start_time, time_limit):
    # Terminal/timeout checks
    if time.time() - start_time > time_limit:
        # return a heuristic quickly
        return evaluate(my_men, my_kings, opp_men, opp_kings, color), None

    moves = generate_moves(my_men, my_kings, opp_men, opp_kings, color)
    if not moves:
        # no moves: losing position
        return -1e6, None
    if depth == 0:
        return evaluate(my_men, my_kings, opp_men, opp_kings, color), None

    best_score = -1e9
    best_move = None

    # order moves: captures first, then moves; among captures prefer more captures
    def move_key(m):
        start, end, caps = m
        return (len(caps) > 0, len(caps))  # prefer captures with more pieces

    moves_sorted = sorted(moves, key=move_key, reverse=True)

    opp_color = 'b' if color == 'w' else 'w'

    for mv in moves_sorted:
        start, end, caps = mv
        nm_my_men, nm_my_kings, nm_opp_men, nm_opp_kings = apply_move(
            my_men, my_kings, opp_men, opp_kings, start, end, caps, color)
        # swap sides for recursion
        score, _ = negamax(nm_opp_men, nm_opp_kings, nm_my_men, nm_my_kings,
                           opp_color, depth - 1, -beta, -alpha, start_time, time_limit)
        score = -score
        if score > best_score:
            best_score = score
            best_move = mv
        alpha = max(alpha, score)
        if alpha >= beta:
            break
        # timeout check
        if time.time() - start_time > time_limit:
            break

    return best_score, best_move

# Policy entry point
def policy(my_men: List[Tuple[int,int]], my_kings: List[Tuple[int,int]],
           opp_men: List[Tuple[int,int]], opp_kings: List[Tuple[int,int]],
           color: str) -> Tuple[Coord, Coord]:
    start_time = time.time()
    time_limit = TIME_LIMIT

    my_men_s = make_sets(my_men)
    my_kings_s = make_sets(my_kings)
    opp_men_s = make_sets(opp_men)
    opp_kings_s = make_sets(opp_kings)

    # quick move generation
    moves = generate_moves(my_men_s, my_kings_s, opp_men_s, opp_kings_s, color)
    if not moves:
        # No legal moves; return a dummy legal-looking move (shouldn't happen in normal play)
        # Try to return any piece staying in place (to meet return signature)
        if my_men:
            return tuple(my_men[0]), tuple(my_men[0])
        if my_kings:
            return tuple(my_kings[0]), tuple(my_kings[0])
        # no pieces either
        return (0,1),(0,1)

    # If only one move, return it
    if len(moves) == 1:
        s,e,_ = moves[0]
        return s, e

    # Choose search depth based on piece count to balance speed
    total_pieces = len(my_men) + len(my_kings) + len(opp_men) + len(opp_kings)
    depth = DEPTH_BASE
    if total_pieces > 12:
        depth = max(4, DEPTH_BASE - 2)
    if total_pieces > 18:
        depth = max(3, DEPTH_BASE - 3)

    # iterative deepening
    best_move = None
    best_score = -1e9
    # small safety: cap total search time per call
    tlimit = time_limit
    for d in range(1, depth+1):
        if time.time() - start_time > tlimit:
            break
        score, mv = negamax(my_men_s, my_kings_s, opp_men_s, opp_kings_s, color, d, -1e9, 1e9, start_time, tlimit)
        if mv is not None:
            best_move = mv
            best_score = score
        # small guard for timeout
        if time.time() - start_time > tlimit:
            break

    if best_move is None:
        # fallback: pick a capture if any else pick a quiet move that improves position heuristically
        # choose biggest capture
        captures = [m for m in moves if len(m[2])>0]
        if captures:
            best_move = max(captures, key=lambda m: len(m[2]))
        else:
            # pick quiet move that lands closer to center or promotes
            def quiet_key(m):
                s,e,caps = m
                r,c = e
                center_bonus = -abs(3.5 - r) - abs(3.5 - c)
                promote = 0
                if s in my_men_s:
                    if (color=='w' and r==7) or (color=='b' and r==0):
                        promote = 50
                return (promote, center_bonus)
            best_move = max(moves, key=quiet_key)

    s,e,caps = best_move
    return s, e

# If module run directly, provide a trivial example move
if __name__ == "__main__":
    # Example: simple starting position with a few pieces
    mm = [(2,1),(2,3)]
    mk = []
    om = [(5,2)]
    ok = []
    mv = policy(mm, mk, om, ok, 'w')
    print("Chosen move:", mv)
