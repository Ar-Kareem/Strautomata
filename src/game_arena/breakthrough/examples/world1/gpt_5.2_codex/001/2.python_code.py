
import math
import random
from typing import List, Tuple

Move = Tuple[Tuple[int, int], Tuple[int, int]]

WIN_SCORE = 10**6

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Move:
    me = list(me)
    opp = list(opp)
    root_color = color
    max_depth = 3

    def goal_row(col):
        return 7 if col == 'w' else 0

    def advancement_score(pieces, col):
        if col == 'w':
            return sum(r for r, _ in pieces)
        else:
            return sum(7 - r for r, _ in pieces)

    def has_won(pieces, col, opp_pieces):
        if not opp_pieces:
            return True
        gr = goal_row(col)
        return any(r == gr for r, _ in pieces)

    def evaluate(my_p, opp_p, my_col):
        if has_won(my_p, my_col, opp_p):
            return WIN_SCORE
        if has_won(opp_p, 'b' if my_col == 'w' else 'w', my_p):
            return -WIN_SCORE
        mat = 10 * (len(my_p) - len(opp_p))
        adv = advancement_score(my_p, my_col) - advancement_score(opp_p, 'b' if my_col == 'w' else 'w')
        # encourage reaching last row
        gr = goal_row(my_col)
        bonus = sum(50 for r, _ in my_p if r == gr)
        return mat + adv + bonus

    def generate_moves(pieces, opp_pieces, col) -> List[Move]:
        moves = []
        my_set = set(pieces)
        opp_set = set(opp_pieces)
        dr = 1 if col == 'w' else -1
        for r, c in pieces:
            nr = r + dr
            if 0 <= nr < 8:
                # forward
                if (nr, c) not in my_set and (nr, c) not in opp_set:
                    moves.append(((r, c), (nr, c)))
                # diag left
                nc = c - 1
                if 0 <= nc < 8:
                    if (nr, nc) not in my_set:
                        # empty or capture
                        moves.append(((r, c), (nr, nc)))
                # diag right
                nc = c + 1
                if 0 <= nc < 8:
                    if (nr, nc) not in my_set:
                        moves.append(((r, c), (nr, nc)))
        # filter illegal diagonal onto own piece already handled
        # legality for forward already ensured empty
        # diagonal onto opponent or empty are both legal
        # but forward onto opponent is not generated
        return moves

    def apply_move(pieces, opp_pieces, move: Move):
        (fr, fc), (tr, tc) = move
        new_p = [p for p in pieces if p != (fr, fc)]
        new_p.append((tr, tc))
        new_o = [p for p in opp_pieces if p != (tr, tc)]
        return new_p, new_o

    def alphabeta(pieces, opp_pieces, to_move, depth, alpha, beta):
        if depth == 0 or has_won(pieces, to_move, opp_pieces) or has_won(opp_pieces, 'b' if to_move == 'w' else 'w', pieces):
            return evaluate(pieces if to_move == root_color else opp_pieces,
                            opp_pieces if to_move == root_color else pieces,
                            root_color)
        moves = generate_moves(pieces, opp_pieces, to_move)
        if not moves:
            # no legal moves -> lose
            return -WIN_SCORE if to_move == root_color else WIN_SCORE
        if to_move == root_color:
            value = -math.inf
            for mv in moves:
                np, no = apply_move(pieces, opp_pieces, mv)
                val = alphabeta(no, np, 'b' if to_move == 'w' else 'w', depth-1, alpha, beta)
                value = max(value, val)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = math.inf
            for mv in moves:
                np, no = apply_move(pieces, opp_pieces, mv)
                val = alphabeta(no, np, 'b' if to_move == 'w' else 'w', depth-1, alpha, beta)
                value = min(value, val)
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    # Root move selection
    moves = generate_moves(me, opp, color)
    if not moves:
        # no legal moves, though shouldn't happen; return dummy safe
        return ((me[0][0], me[0][1]), (me[0][0], me[0][1]))

    best_val = -math.inf
    best_move = moves[0]
    for mv in moves:
        np, no = apply_move(me, opp, mv)
        val = alphabeta(no, np, 'b' if color == 'w' else 'w', max_depth-1, -math.inf, math.inf)
        if val > best_val:
            best_val = val
            best_move = mv

    return best_move
