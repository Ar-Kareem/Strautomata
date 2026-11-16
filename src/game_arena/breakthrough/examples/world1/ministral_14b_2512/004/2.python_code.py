
import sys
from collections import defaultdict

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Precompute opponent's home row (row 0 for white, row 7 for black)
    opp_home_row = 0 if color == 'w' else 7
    my_home_row = 7 if color == 'w' else 0

    # Generate all legal moves for me
    legal_moves = generate_legal_moves(me, opp, color)

    # Check for immediate promotion (win condition)
    for (fr, fc), (tr, tc) in legal_moves:
        if tr == opp_home_row:
            return ((fr, fc), (tr, tc))

    # If no immediate promotion, use minimax with alpha-beta pruning
    best_move = None
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')

    # Sort moves by heuristic value to improve alpha-beta pruning
    sorted_moves = sorted(legal_moves, key=lambda move: evaluate_move(move, me, opp, color, opp_home_row), reverse=True)

    for move in sorted_moves:
        new_me = apply_move(me, opp, move, color)
        new_opp = opp.copy()
        score = minimax(new_me, new_opp, color, alpha, beta, depth=3, is_maximizing=False)
        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, best_score)
        if alpha >= beta:
            break

    return best_move

def generate_legal_moves(me, opp, color):
    moves = []
    opp_set = set(opp)
    for (fr, fc) in me:
        # Forward moves (straight)
        direction = 1 if color == 'w' else -1
        for dr, dc in [(direction, 0), (direction, 1), (direction, -1)]:
            tr, tc = fr + dr, fc + dc
            if 0 <= tr < 8 and 0 <= tc < 8:
                if (tr, tc) not in opp_set:
                    moves.append(((fr, fc), (tr, tc)))
                elif (tr, tc) in opp_set:
                    # Diagonal capture
                    moves.append(((fr, fc), (tr, tc)))
    return moves

def apply_move(me, opp, move, color):
    new_me = me.copy()
    new_opp = opp.copy()
    (fr, fc), (tr, tc) = move
    # Remove from original position
    new_me.remove((fr, fc))
    # Add to new position
    new_me.append((tr, tc))
    # Remove captured opponent piece if any
    if (tr, tc) in opp:
        new_opp.remove((tr, tc))
    return new_me

def evaluate_move(move, me, opp, color, opp_home_row):
    # Simple heuristic: prefer captures, then moves closer to opponent's home row
    (fr, fc), (tr, tc) = move
    score = 0
    # Capture bonus
    if (tr, tc) in opp:
        score += 100
    # Distance to opponent's home row
    direction = 1 if color == 'w' else -1
    distance = abs(tr - opp_home_row)
    score += (8 - distance) * 2  # Higher score for pieces closer to promotion
    # Center control bonus
    center_bonus = 0
    if 3 <= tc <= 4:
        center_bonus += 5
    score += center_bonus
    return score

def minimax(me, opp, color, alpha, beta, depth, is_maximizing):
    if depth == 0:
        return evaluate_position(me, opp, color)

    opp_home_row = 0 if color == 'w' else 7
    legal_moves = generate_legal_moves(me, opp, color)

    if is_maximizing:
        max_eval = -float('inf')
        for move in legal_moves:
            new_me = apply_move(me, opp, move, color)
            new_opp = opp.copy()
            eval = minimax(new_me, new_opp, color, alpha, beta, depth - 1, False)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if alpha >= beta:
                break
        return max_eval
    else:
        # Opponent's turn (minimizing)
        opp_color = 'b' if color == 'w' else 'w'
        opp_legal_moves = generate_legal_moves(opp, me, opp_color)
        min_eval = float('inf')
        for move in opp_legal_moves:
            new_opp = apply_move(opp, me, move, opp_color)
            new_me = me.copy()
            eval = minimax(new_me, new_opp, color, alpha, beta, depth - 1, True)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if alpha >= beta:
                break
        return min_eval

def evaluate_position(me, opp, color):
    score = 0
    opp_home_row = 0 if color == 'w' else 7
    # Material: prefer fewer opponent pieces
    score += len(me) * 10 - len(opp) * 10
    # Mobility: more legal moves = better
    for piece in me:
        moves = generate_legal_moves([piece], opp, color)
        score += len(moves) * 2
    # King potential: pieces closer to opponent's home row
    for (r, c) in me:
        direction = 1 if color == 'w' else -1
        distance = abs(r - opp_home_row)
        score += (8 - distance) * 3
    # Center control
    for (r, c) in me:
        if 3 <= c <= 4:
            score += 5
    return score
