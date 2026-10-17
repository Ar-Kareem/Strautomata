
import numpy as np
from typing import List, Tuple

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Hybrid Othello policy combining:
    - Corner/edge prioritization (heuristics)
    - Disc count optimization
    - Limited lookahead (minimax with alpha-beta pruning)
    - Fallback to greedy mobility if no strong move is found.
    """
    # Get empty cells
    empty = np.where(you == 0)
    empty_cells = list(zip(empty[0], empty[1]))

    # If no legal moves, return "pass" (though problem says this won't happen)
    if not empty_cells:
        return "pass"

    # Evaluate all possible moves using a combination of heuristics and minimax
    best_move = None
    best_score = -float('inf')

    # Heuristic weights (tuned for balance)
    HEURISTIC_WEIGHTS = {
        'corner': 10000,
        'semi_corner': 5000,
        'edge': 2000,
        'disc_flipped': 10,
        'mobility': 1,
        'stability': 500,
    }

    # Precompute board features (corners, edges, etc.)
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    semi_corners = [(0, 1), (0, 6), (1, 0), (1, 7), (6, 0), (6, 7), (7, 1), (7, 6)]
    edges = [(0, c) for c in range(8)] + [(7, c) for c in range(8)] + \
            [(r, 0) for r in range(1, 7)] + [(r, 7) for r in range(1, 7)]

    # For each empty cell, compute heuristic score
    for r, c in empty_cells:
        # Check if it's a corner, semi-corner, or edge
        score = 0
        if (r, c) in corners:
            score += HEURISTIC_WEIGHTS['corner']
        elif (r, c) in semi_corners:
            score += HEURISTIC_WEIGHTS['semi_corner']
        elif (r, c) in edges:
            score += HEURISTIC_WEIGHTS['edge']

        # Compute disc flips (greedy)
        flipped = count_flips(you, opponent, r, c)
        score += flipped * HEURISTIC_WEIGHTS['disc_flipped']

        # Compute mobility (number of legal moves for both players)
        mobility_you = count_legal_moves(you, opponent)
        mobility_opponent = count_legal_moves(opponent, you)
        mobility_diff = mobility_you - mobility_opponent
        score += mobility_diff * HEURISTIC_WEIGHTS['mobility']

        # Compute stability (discs adjacent to mine or edge)
        stability = count_stable(you, opponent, r, c)
        score += stability * HEURISTIC_WEIGHTS['stability']

        # Update best move if this is better
        if score > best_score:
            best_score = score
            best_move = (r, c)

    # If no move found (shouldn't happen), pick a random one
    if best_move is None:
        return random.choice([f"{chr(97+c)}{r+1}" for r, c in empty_cells])

    # Decide whether to use minimax in endgame
    if (you.sum() + opponent.sum()) < 30:  # Endgame threshold
        best_move, _ = minimax(you, opponent, empty_cells, depth=2)

    # Return the move in algebraic notation
    r, c = best_move
    return f"{chr(97+c)}{r+1}"

def count_flips(you: np.ndarray, opponent: np.ndarray, r: int, c: int) -> int:
    """Count the number of opponent discs flipped if a move is made at (r, c)."""
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]
    you_copy = you.copy()
    you_copy[r, c] = 1
    flips = 0

    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8:
            if you_copy[nr, nc] == 1:
                break
            if opponent[nr, nc] == 1:
                flips += 1
                nr += dr
                nc += dc
            else:
                break
    return flips

def count_legal_moves(you: np.ndarray, opponent: np.ndarray) -> int:
    """Count the number of legal moves for 'you'."""
    empty = np.where(you == 0)
    empty_cells = list(zip(empty[0], empty[1]))
    legal_moves = []

    for r, c in empty_cells:
        if count_flips(you, opponent, r, c) > 0:
            legal_moves.append((r, c))
    return len(legal_moves)

def count_stable(you: np.ndarray, opponent: np.ndarray, r: int, c: int) -> int:
    """Count how many of my discs are stable after placing at (r, c)."""
    # Simulate the move and count flips
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]
    you_copy = you.copy()
    you_copy[r, c] = 1
    flipped = 0

    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8:
            if you_copy[nr, nc] == 1:
                break
            if opponent[nr, nc] == 1:
                flipped += 1
                nr += dr
                nc += dc
            else:
                break

    # Stability = discs adjacent to mine or edge (after flipping)
    stability = 0
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr, nc] == 0:
            stability += 1

    # Also count edge adjacency
    if r == 0 or r == 7 or c == 0 or c == 7:
        stability += 4  # Edge bonus
    else:
        stability += 2  # Center bonus (less stable)

    return stability

def minimax(you: np.ndarray, opponent: np.ndarray, empty_cells: List[Tuple[int, int]], depth: int = 2) -> Tuple[Tuple[int, int], int]:
    """Perform a minimax search with alpha-beta pruning for endgame decisions."""
    best_move = None
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')

    for r, c in empty_cells:
        # Simulate the move
        new_you = you.copy()
        new_you[r, c] = 1
        new_opponent = opponent.copy()

        # Flip opponent discs
        flipped = count_flips(you, opponent, r, c)
        for dr, dc in [(-1, -1), (-1, 0), (-1, 1),
                       (0, -1),          (0, 1),
                       (1, -1),  (1, 0), (1, 1)]:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                if you[nr, nc] == 1:
                    break
                if opponent[nr, nc] == 1:
                    new_opponent[nr, nc] = 0
                    new_you[nr, nc] = 1
                    nr += dr
                    nc += dc
                else:
                    break

        # Evaluate the position
        score = evaluate(new_you, new_opponent)

        # If not at max depth, recurse
        if depth > 0:
            opponent_legal = count_legal_moves(new_opponent, new_you)
            if opponent_legal == 0:
                # Opponent has no moves; this is a forced win
                score = new_you.sum() - new_opponent.sum()
            else:
                # Opponent's turn: minimize
                opponent_empty = np.where(new_opponent == 0)
                opponent_cells = list(zip(opponent_empty[0], opponent_empty[1]))
                _, opponent_score = minimax(new_opponent, new_you, opponent_cells, depth-1)
                score = opponent_score

        # Update best move
        if score > best_score:
            best_score = score
            best_move = (r, c)
        alpha = max(alpha, score)
        if beta <= alpha:
            break  # Alpha-beta pruning

    return best_move, best_score

def evaluate(you: np.ndarray, opponent: np.ndarray) -> int:
    """Evaluate the board position using weighted heuristics."""
    # Disc difference
    disc_diff = you.sum() - opponent.sum()

    # Mobility difference
    mobility_you = count_legal_moves(you, opponent)
    mobility_opponent = count_legal_moves(opponent, you)
    mobility_diff = mobility_you - mobility_opponent

    # Corner control
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    corner_score = sum(you[r, c] * 10000 for r, c in corners)

    # Edge control
    edges = [(0, c) for c in range(8)] + [(7, c) for c in range(8)] + \
            [(r, 0) for r in range(1, 7)] + [(r, 7) for r in range(1, 7)]
    edge_score = sum(you[r, c] * 2000 for r, c in edges)

    # Stability (discs adjacent to mine or edge)
    stability = 0
    for r in range(8):
        for c in range(8):
            if you[r, c] == 1:
                for dr, dc in [(-1, -1), (-1, 0), (-1, 1),
                               (0, -1),          (0, 1),
                               (1, -1),  (1, 0), (1, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr, nc] == 0:
                        stability += 1
    # Edge adjacency bonus
    for r in range(8):
        for c in range(8):
            if you[r, c] == 1 and (r == 0 or r == 7 or c == 0 or c == 7):
                stability += 4

    # Total score
    total_score = disc_diff + mobility_diff + corner_score + edge_score + stability
    return total_score
