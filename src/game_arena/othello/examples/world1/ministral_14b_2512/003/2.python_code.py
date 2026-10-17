
import numpy as np
from typing import List, Tuple

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Othello policy using minimax with alpha-beta pruning and heuristic evaluation.
    Returns a legal move in algebraic notation (e.g., "d3") or "pass" if no moves.
    """
    # Get legal moves
    legal_moves = get_legal_moves(you, opponent)
    if not legal_moves:
        return "pass"

    # If no legal moves, return pass (shouldn't happen due to check above)
    best_move = None
    best_score = -float('inf')

    # Iterative deepening with time control (simplified for 1-second constraint)
    max_depth = 4  # Start with depth 4, reduce if needed
    for depth in range(1, max_depth + 1):
        try:
            # Perform minimax search with alpha-beta pruning
            score, move = minimax(you, opponent, depth, -float('inf'), float('inf'), True)
            if score > best_score:
                best_score = score
                best_move = move
            break  # Use best depth found
        except TimeoutError:
            # If search takes too long, reduce depth and try again
            max_depth = depth - 1
            continue

    return best_move

def minimax(you: np.ndarray, opponent: np.ndarray, depth: int, alpha: float, beta: float, maximizing_player: bool) -> Tuple[float, str]:
    """
    Minimax with alpha-beta pruning.
    Returns (best_score, best_move) for the current player.
    """
    if depth == 0 or no_legal_moves(you, opponent) and no_legal_moves(opponent, you):
        return evaluate_board(you, opponent), "pass"

    legal_moves = get_legal_moves(you, opponent)
    if not legal_moves:
        return evaluate_board(you, opponent), "pass"

    best_score = -float('inf') if maximizing_player else float('inf')
    best_move = None

    for move in legal_moves:
        new_you, new_opponent = simulate_move(you, opponent, move, maximizing_player)
        score, _ = minimax(new_you, new_opponent, depth - 1, alpha, beta, not maximizing_player)

        if maximizing_player and score > best_score:
            best_score = score
            best_move = move
            alpha = max(alpha, score)
        elif not maximizing_player and score < best_score:
            best_score = score
            best_move = move
            beta = min(beta, score)

        if beta <= alpha:
            break  # Alpha-beta pruning

    return best_score, best_move

def evaluate_board(you: np.ndarray, opponent: np.ndarray) -> float:
    """
    Heuristic evaluation of the board.
    Higher score = better for the current player.
    """
    # Disc parity (difference in disc count)
    your_discs = np.sum(you)
    opp_discs = np.sum(opponent)
    parity = your_discs - opp_discs

    # Positional advantage (corners, edges, center)
    score = 0
    for r in range(8):
        for c in range(8):
            if you[r][c] == 1:
                score += positional_value(r, c)
            elif opponent[r][c] == 1:
                score -= positional_value(r, c)

    # Mobility (number of legal moves)
    your_mobility = len(get_legal_moves(you, opponent))
    opp_mobility = len(get_legal_moves(opponent, you))
    mobility = your_mobility - opp_mobility

    # Combine heuristics (weights tuned for balance)
    return parity * 100 + score * 0.1 + mobility * 10

def positional_value(r: int, c: int) -> float:
    """
    Assigns a positional value to a cell (r, c).
    Corners > edges > center > others.
    """
    # Corner bonus (~1000)
    if (r == 0 or r == 7) and (c == 0 or c == 7):
        return 1000

    # Edge bonus (~100)
    if r == 0 or r == 7 or c == 0 or c == 7:
        return 100

    # Center bonus (~50)
    if (r >= 3 and r <= 4) and (c >= 3 and c <= 4):
        return 50

    # Other cells (~1)
    return 1

def get_legal_moves(you: np.ndarray, opponent: np.ndarray) -> List[str]:
    """
    Returns all legal moves for the current player.
    """
    legal_moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]

    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0:
                for dr, dc in directions:
                    if is_valid_flip(you, opponent, r, c, dr, dc):
                        legal_moves.append(f"{chr(ord('a') + c)}{r + 1}")
                        break
    return legal_moves

def is_valid_flip(you: np.ndarray, opponent: np.ndarray, r: int, c: int, dr: int, dc: int) -> bool:
    """
    Checks if placing a disc at (r, c) flips at least one opponent disc in direction (dr, dc).
    """
    nr, nc = r + dr, c + dc
    if nr < 0 or nr >= 8 or nc < 0 or nc >= 8:
        return False

    # Must be opponent's disc, and there must be at least one of my discs beyond it
    if opponent[nr][nc] == 1:
        nr += dr
        nc += dc
        while 0 <= nr < 8 and 0 <= nc < 8:
            if you[nr][nc] == 1:
                return True
            if you[nr][nc] == 0 and opponent[nr][nc] == 0:
                break  # No more discs in this direction
            nr += dr
            nc += dc
    return False

def simulate_move(you: np.ndarray, opponent: np.ndarray, move: str, maximizing_player: bool) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulates placing a disc at `move` and flipping opponent discs.
    Returns (new_you, new_opponent) after the move.
    """
    c = ord(move[0]) - ord('a')
    r = int(move[1]) - 1
    new_you = you.copy()
    new_opponent = opponent.copy()
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]

    # Place my disc
    new_you[r][c] = 1

    # Flip opponent discs in all 8 directions
    for dr, dc in directions:
        flip_discs(new_you, new_opponent, r, c, dr, dc, maximizing_player)

    return new_you, new_opponent

def flip_discs(you: np.ndarray, opponent: np.ndarray, r: int, c: int, dr: int, dc: int, maximizing_player: bool) -> None:
    """
    Flips opponent discs in direction (dr, dc) if the move is valid.
    """
    nr, nc = r + dr, c + dc
    if nr < 0 or nr >= 8 or nc < 0 or nc >= 8:
        return

    # Must be opponent's disc, and there must be at least one of my discs beyond it
    if opponent[nr][nc] == 1:
        nr += dr
        nc += dc
        while 0 <= nr < 8 and 0 <= nc < 8:
            if you[nr][nc] == 1:
                # Flip all opponent discs in this direction
                nr, nc = r + dr, c + dc
                while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc] == 1:
                    opponent[nr][nc] = 0
                    you[nr][nc] = 1 if maximizing_player else 0
                    nr += dr
                    nc += dc
                break
            if you[nr][nc] == 0 and opponent[nr][nc] == 0:
                break  # No more discs in this direction
            nr += dr
            nc += dc

def no_legal_moves(you: np.ndarray, opponent: np.ndarray) -> bool:
    """
    Checks if the current player has no legal moves.
    """
    return len(get_legal_moves(you, opponent)) == 0
