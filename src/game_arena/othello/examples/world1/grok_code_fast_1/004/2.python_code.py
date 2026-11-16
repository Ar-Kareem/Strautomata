
import numpy as np

# Positional weights for 8x8 Othello board: corners are highly valuable, edges decent, center less so
weight = np.array([
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -40, -2, -2, -2, -2, -40, -20],
    [10, -2, 10, -2, -2, 1, -2, 10],
    [5, -2, -2, -1, -1, -2, -2, 5],
    [5, -2, -2, -1, -1, -2, -2, 5],
    [10, -2, 1, -2, -2, 10, -2, 10],
    [-20, -40, -2, -2, -2, -2, -40, -20],
    [100, -20, 10, 5, 5, 10, -20, 100]
])

directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

def is_legal(r, c, player, opp):
    """Check if (r, c) is a legal move for player against opp."""
    if player[r, c] == 1 or opp[r, c] == 1:
        return False
    for dr, dc in directions:
        rr, cc = r + dr, c + dc
        has_opp = False
        while 0 <= rr < 8 and 0 <= cc < 8:
            if opp[rr, cc] == 1:
                has_opp = True
            elif player[rr, cc] == 1:
                if has_opp:
                    return True
                break
            else:
                break
            rr += dr
            cc += dc
    return False

def simulate_move(r, c, you, opponent):
    """Simulate placing a disc at (r, c) for you against opponent, return new_you, new_opponent, flip_count."""
    new_you = you.copy()
    new_opp = opponent.copy()
    new_you[r, c] = 1
    flip_count = 0
    for dr, dc in directions:
        rr, cc = r + dr, c + dc
        to_flip = []
        while 0 <= rr < 8 and 0 <= cc < 8:
            if new_opp[rr, cc] == 1:
                to_flip.append((rr, cc))
            elif new_you[rr, cc] == 1:
                flip_count += len(to_flip)
                for fr, fc in to_flip:
                    new_you[fr, fc] = 1
                    new_opp[fr, fc] = 0
                break
            else:
                break
            rr += dr
            cc += dc
    return new_you, new_opp, flip_count

def count_legal_moves(player, opp):
    """Count the number of legal moves for player against opp."""
    count = 0
    for tr in range(8):
        for tc in range(8):
            if is_legal(tr, tc, player, opp):
                count += 1
    return count

def policy(you, opponent):
    """Return the best move as a string (e.g., 'd3') or 'pass' if no moves."""
    best_score = -float('inf')
    best_move = None
    for r in range(8):
        for c in range(8):
            if is_legal(r, c, you, opponent):
                new_you, new_opp, flips = simulate_move(r, c, you, opponent)
                opp_moves = count_legal_moves(new_opp, new_you)
                score = 10 * flips + weight[r, c] - 2 * opp_moves
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    if best_move is None:
        return "pass"
    r, c = best_move
    file = chr(ord('a') + c)
    rank = str(8 - r)
    return file + rank
