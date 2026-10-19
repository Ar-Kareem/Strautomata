
import math
from typing import List, Tuple

Move = Tuple[Tuple[int, int], Tuple[int, int]]

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Move:
    """
    Choose a move for Breakthrough.
    """
    # If no moves exist (should be rare), fall back safely
    moves = generate_moves(me, opp, color)
    if not moves:
        # Fallback: just return something (should never happen in normal play)
        return (me[0], me[0])

    total_pieces = len(me) + len(opp)
    depth = 4 if total_pieces <= 8 else 3

    best_score = -math.inf
    best_move = moves[0]
    for mv in order_moves(moves, me, opp, color):
        new_me, new_opp = apply_move(me, opp, mv)
        score = -negamax(new_opp, new_me, opposite(color), depth - 1, -math.inf, math.inf, color)
        if score > best_score:
            best_score = score
            best_move = mv

    return best_move

def negamax(me, opp, color, depth, alpha, beta, root_color):
    winner = check_winner(me, opp, color)
    if winner is not None:
        return 100000 if winner == root_color else -100000
    if depth == 0:
        return evaluate(me, opp, root_color)

    moves = generate_moves(me, opp, color)
    if not moves:
        # no moves = lose
        return -100000 if color == root_color else 100000

    max_score = -math.inf
    for mv in order_moves(moves, me, opp, color):
        new_me, new_opp = apply_move(me, opp, mv)
        score = -negamax(new_opp, new_me, opposite(color), depth - 1, -beta, -alpha, root_color)
        if score > max_score:
            max_score = score
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    return max_score

def check_winner(me, opp, color):
    if not opp:
        return color
    goal = 7 if color == 'w' else 0
    for r, c in me:
        if r == goal:
            return color
    # Check if opponent already on goal row
    opp_goal = 7 if color == 'b' else 0
    for r, c in opp:
        if r == opp_goal:
            return opposite(color)
    return None

def evaluate(me, opp, root_color):
    # material
    mat = 100 * (len(me) - len(opp))

    # advancement
    if root_color == 'w':
        adv_me = sum(r for r, c in me)
        adv_opp = sum(7 - r for r, c in opp)
    else:
        adv_me = sum(7 - r for r, c in me)
        adv_opp = sum(r for r, c in opp)
    adv = 10 * (adv_me - adv_opp)

    # capture threats
    threats_me = count_captures(me, opp, root_color)
    threats_opp = count_captures(opp, me, opposite(root_color))
    threat_score = 5 * (threats_me - threats_opp)

    return mat + adv + threat_score

def count_captures(me, opp, color):
    opp_set = set(opp)
    d = 1 if color == 'w' else -1
    count = 0
    for r, c in me:
        for dc in (-1, 1):
            nr, nc = r + d, c + dc
            if 0 <= nr <= 7 and 0 <= nc <= 7 and (nr, nc) in opp_set:
                count += 1
    return count

def generate_moves(me, opp, color):
    me_set = set(me)
    opp_set = set(opp)
    moves = []
    d = 1 if color == 'w' else -1

    for r, c in me:
        # forward
        nr, nc = r + d, c
        if 0 <= nr <= 7 and (nr, nc) not in me_set and (nr, nc) not in opp_set:
            moves.append(((r, c), (nr, nc)))
        # diagonals
        for dc in (-1, 1):
            nr, nc = r + d, c + dc
            if 0 <= nr <= 7 and 0 <= nc <= 7:
                if (nr, nc) not in me_set:
                    moves.append(((r, c), (nr, nc)))
    return moves

def apply_move(me, opp, move):
    me_set = set(me)
    opp_set = set(opp)
    frm, to = move
    me_set.remove(frm)
    if to in opp_set:
        opp_set.remove(to)
    me_set.add(to)
    return list(me_set), list(opp_set)

def order_moves(moves, me, opp, color):
    """Order moves to improve alpha-beta: prefer winning moves, captures, goal advances."""
    opp_set = set(opp)
    goal = 7 if color == 'w' else 0
    def score(m):
        frm, to = m
        s = 0
        if to in opp_set:
            s += 50
        if to[0] == goal:
            s += 100
        # prefer forward progress
        s += (to[0] - frm[0]) * (1 if color == 'w' else -1)
        return -s  # negative for ascending sort
    return sorted(moves, key=score)

def opposite(color):
    return 'b' if color == 'w' else 'w'
