
import numpy as np
from typing import List, Tuple

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Returns the next move for the current player (you) in Othello using a heuristic-based minimax search.
    - Corners are prioritized.
    - Mobility (legal moves) is considered.
    - Disc parity is used as a tiebreaker.
    - Stability (unflippable discs) is approximated.
    - Alpha-beta pruning is used to limit search depth.
    """

    # Directions for flipping: 8 possible directions (horizontal, vertical, diagonal)
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]

    # Get all legal moves for the current player
    legal_moves = get_legal_moves(you, opponent)

    if not legal_moves:
        return "pass"

    # Evaluate each legal move using minimax with alpha-beta pruning
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        # Simulate the move
        new_you = you.copy()
        new_opponent = opponent.copy()
        new_you[move[0]][move[1]] = 1
        new_opponent = flip_discs(new_you, new_opponent, move)

        # Get opponent's legal moves after this move
        opponent_legal_moves = get_legal_moves(new_opponent, new_you)

        # If opponent has no moves, this is a forced win (evaluate as +infinity)
        if not opponent_legal_moves:
            score = float('inf')
        else:
            # Evaluate the move using minimax with depth limit
            score = minimax(new_opponent, new_you, 3, -float('inf'), float('inf'), False)

        # Update best move
        if score > best_score:
            best_score = score
            best_move = move

    # Return the best move in algebraic notation
    return f"{chr(ord('a') + best_move[1])}{best_move[0] + 1}" if best_move else "pass"

def get_legal_moves(you: np.ndarray, opponent: np.ndarray) -> List[Tuple[int, int]]:
    """Returns all legal moves for the current player."""
    legal_moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]

    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0:
                # Check if placing a disc here flips any opponent discs
                for dr, dc in directions:
                    if is_legal_flip(you, opponent, r, c, dr, dc):
                        legal_moves.append((r, c))
                        break
    return legal_moves

def is_legal_flip(you: np.ndarray, opponent: np.ndarray, r: int, c: int, dr: int, dc: int) -> bool:
    """Checks if placing a disc at (r, c) flips opponent discs in direction (dr, dc)."""
    nr, nc = r + dr, c + dc
    if opponent[nr][nc] == 1:
        nr += dr
        nc += dc
        while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc] == 1:
            nr += dr
            nc += dc
        return 0 <= nr < 8 and 0 <= nc < 8 and you[nr][nc] == 1
    return False

def flip_discs(you: np.ndarray, opponent: np.ndarray, move: Tuple[int, int]) -> np.ndarray:
    """Flips opponent discs after placing a disc at `move`."""
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]

    flipped_opponent = opponent.copy()
    r, c = move

    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if opponent[nr][nc] == 1:
            nr += dr
            nc += dc
            while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc] == 1:
                flipped_opponent[nr][nc] = 0
                nr += dr
                nc += dc
            if 0 <= nr < 8 and 0 <= nc < 8 and you[nr][nc] == 1:
                flipped_opponent[r][c] = 1

    return flipped_opponent

def minimax(you: np.ndarray, opponent: np.ndarray, depth: int, alpha: float, beta: float, maximizing_player: bool) -> float:
    """
    Minimax search with alpha-beta pruning.
    - `you`: Current player's board (opponent's perspective if not maximizing).
    - `opponent`: Opponent's board.
    - `depth`: Remaining depth.
    - `alpha`: Best value for maximizing player so far.
    - `beta`: Best value for minimizing player so far.
    - `maximizing_player`: Whether the current player is maximizing or minimizing.
    """
    if depth == 0 or (not get_legal_moves(you, opponent)) and (not get_legal_moves(opponent, you)):
        return evaluate_board(you, opponent)

    if maximizing_player:
        legal_moves = get_legal_moves(you, opponent)
        if not legal_moves:
            return evaluate_board(you, opponent)  # No moves left (pass)

        best_score = -float('inf')
        for move in legal_moves:
            new_you = you.copy()
            new_opponent = opponent.copy()
            new_you[move[0]][move[1]] = 1
            new_opponent = flip_discs(new_you, new_opponent, move)

            score = minimax(new_opponent, new_you, depth - 1, alpha, beta, False)
            best_score = max(score, best_score)
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break  # Beta cutoff
        return best_score
    else:
        legal_moves = get_legal_moves(opponent, you)
        if not legal_moves:
            return evaluate_board(you, opponent)  # Opponent passes

        best_score = float('inf')
        for move in legal_moves:
            new_you = you.copy()
            new_opponent = opponent.copy()
            new_opponent[move[0]][move[1]] = 1
            new_you = flip_discs(new_opponent, new_you, move)

            score = minimax(new_you, new_opponent, depth - 1, alpha, beta, True)
            best_score = min(score, best_score)
            beta = min(beta, best_score)
            if beta <= alpha:
                break  # Alpha cutoff
        return best_score

def evaluate_board(you: np.ndarray, opponent: np.ndarray) -> float:
    """
    Heuristic evaluation of the board.
    - Corners are highly valued.
    - Mobility (legal moves) is considered.
    - Disc parity is used as a tiebreaker.
    - Stability is approximated by checking unflippable discs.
    """
    # Corners (a1, a8, h1, h8) are highly valuable
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    corner_score = 0
    for r, c in corners:
        if you[r][c] == 1:
            corner_score += 50
        elif opponent[r][c] == 1:
            corner_score -= 50

    # Edge positions (next to corners)
    edges = [(0, 1), (0, 6), (1, 0), (1, 7), (6, 0), (6, 7), (7, 1), (7, 6),
            (1, 1), (1, 6), (6, 1), (6, 6)]
    edge_score = 0
    for r, c in edges:
        if you[r][c] == 1:
            edge_score += 15
        elif opponent[r][c] == 1:
            edge_score -= 15

    # Disc parity (difference in disc counts)
    your_discs = np.sum(you)
    opponent_discs = np.sum(opponent)
    parity = your_discs - opponent_discs

    # Mobility (number of legal moves)
    your_mobility = len(get_legal_moves(you, opponent))
    opponent_mobility = len(get_legal_moves(opponent, you))
    mobility_score = your_mobility - opponent_mobility

    # Stability (approximate: discs that cannot be flipped)
    stability_score = 0
    for r in range(8):
        for c in range(8):
            if you[r][c] == 1:
                # Check if this disc can be flipped by opponent
                if not can_flip(you, opponent, r, c):
                    stability_score += 1
            elif opponent[r][c] == 1:
                if not can_flip(opponent, you, r, c):
                    stability_score -= 1

    # Combine scores with weights (tuned for balance)
    total_score = (
        corner_score * 1.0 +
        edge_score * 0.5 +
        parity * 10.0 +
        mobility_score * 5.0 +
        stability_score * 2.0
    )

    return total_score

def can_flip(you: np.ndarray, opponent: np.ndarray, r: int, c: int) -> bool:
    """Checks if the disc at (r, c) can be flipped by the opponent."""
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]

    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if opponent[nr][nc] == 1:
            nr += dr
            nc += dc
            while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc] == 1:
                nr += dr
                nc += dc
            if 0 <= nr < 8 and 0 <= nc < 8 and you[nr][nc] == 0:
                return True
    return False
