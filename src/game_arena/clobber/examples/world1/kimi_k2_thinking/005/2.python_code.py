
import numpy as np
import time
import random
import sys

# Directions: (row delta, column delta, character)
DIRS = [(-1, 0, 'U'), (1, 0, 'D'), (0, 1, 'R'), (0, -1, 'L')]

def generate_moves(you, opponent, player):
    """Return list of legal moves for player ('you' or 'opponent')."""
    moves = []
    rows, cols = you.shape
    for r in range(rows):
        for c in range(cols):
            if player == 'you' and you[r, c]:
                for dr, dc, dchar in DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and opponent[nr, nc]:
                        moves.append((r, c, dchar))
            elif player == 'opponent' and opponent[r, c]:
                for dr, dc, dchar in DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and you[nr, nc]:
                        moves.append((r, c, dchar))
    return moves

def apply_move(you, opponent, move, player):
    """Return new board arrays after executing move for player."""
    you_new = you.copy()
    opp_new = opponent.copy()
    r, c, dchar = move
    dr, dc = {
        'U': (-1, 0),
        'D': (1, 0),
        'L': (0, -1),
        'R': (0, 1)
    }[dchar]
    nr, nc = r + dr, c + dc
    if player == 'you':
        you_new[r, c] = 0
        opp_new[nr, nc] = 0
        you_new[nr, nc] = 1
    else:  # opponent
        opp_new[r, c] = 0
        you_new[nr, nc] = 0
        opp_new[nr, nc] = 1
    return you_new, opp_new

def compute_mobility(you, opponent, player):
    """Count number of legal moves for player."""
    rows, cols = you.shape
    count = 0
    for r in range(rows):
        for c in range(cols):
            if player == 'you' and you[r, c]:
                for dr, dc, _ in DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and opponent[nr, nc]:
                        count += 1
            elif player == 'opponent' and opponent[r, c]:
                for dr, dc, _ in DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and you[nr, nc]:
                        count += 1
    return count

def evaluate(you, opponent, player):
    """Heuristic: mobility difference + small material bias."""
    if player == 'you':
        my_mob = compute_mobility(you, opponent, 'you')
        opp_mob = compute_mobility(you, opponent, 'opponent')
        my_mat = you.sum()
        opp_mat = opponent.sum()
    else:
        my_mob = compute_mobility(you, opponent, 'opponent')
        opp_mob = compute_mobility(you, opponent, 'you')
        my_mat = opponent.sum()
        opp_mat = you.sum()
    return (my_mob - opp_mob) + 0.1 * (my_mat - opp_mat)

def minimax(you, opponent, depth, alpha, beta, maximizing):
    """Alpha‑beta minimax."""
    player = 'you' if maximizing else 'opponent'
    moves = generate_moves(you, opponent, player)
    if not moves:
        # Player to move loses.
        return -1e9 if maximizing else 1e9
    if depth == 0:
        return evaluate(you, opponent, player)
    if maximizing:
        value = -1e9
        for move in moves:
            you_new, opp_new = apply_move(you, opponent, move, player)
            child_val = minimax(you_new, opp_new, depth - 1, alpha, beta, False)
            value = max(value, child_val)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = 1e9
        for move in moves:
            you_new, opp_new = apply_move(you, opponent, move, player)
            child_val = minimax(you_new, opp_new, depth - 1, alpha, beta, True)
            value = min(value, child_val)
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value

def policy(you, opponent):
    """Return a legal move string."""
    you_arr = np.array(you, dtype=np.int8)
    opp_arr = np.array(opponent, dtype=np.int8)

    # All legal moves for the current player.
    moves = generate_moves(you_arr, opp_arr, 'you')
    if not moves:
        # Should not happen, but avoid disqualification.
        return "0,0,U"

    # Immediate win?
    winning_moves = []
    for move in moves:
        you_new, opp_new = apply_move(you_arr, opp_arr, move, 'you')
        if not generate_moves(you_new, opp_new, 'opponent'):
            winning_moves.append(move)
    if winning_moves:
        move = random.choice(winning_moves)
        return f"{move[0]},{move[1]},{move[2]}"

    # Order moves by opponent mobility after the move (ascending).
    move_scores = []
    for move in moves:
        you_new, opp_new = apply_move(you_arr, opp_arr, move, 'you')
        opp_mob = compute_mobility(you_new, opp_new, 'opponent')
        move_scores.append((opp_mob, move))
    move_scores.sort(key=lambda x: x[0])
    sorted_moves = [m for _, m in move_scores]

    start = time.time()
    best_move = None
    best_score = -1e9

    # Iterative deepening, start with depth 2.
    depth = 2
    while time.time() - start < 0.95:
        current_best = None
        current_best_score = -1e9
        alpha = -1e9
        beta = 1e9
        for move in sorted_moves:
            you_new, opp_new = apply_move(you_arr, opp_arr, move, 'you')
            # Opponent's turn (minimising)
            score = minimax(you_new, opp_new, depth, alpha, beta, False)
            if score > current_best_score:
                current_best_score = score
                current_best = move
            alpha = max(alpha, current_best_score)
            # Stop early if a forced win is found.
            if current_best_score >= 1e8:
                break
        # Keep result from the deepest finished search.
        best_move = current_best
        best_score = current_best_score
        # No need to search deeper if we already have a forced win.
        if best_score >= 1e8:
            break
        depth += 1

    # Fallback to the first move if something went wrong.
    if best_move is None:
        best_move = sorted_moves[0]

    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
