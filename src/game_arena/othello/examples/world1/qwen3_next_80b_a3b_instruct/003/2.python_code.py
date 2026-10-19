
import numpy as np
import heapq
from typing import List, Tuple, Dict, Optional

# Define directions for 8 neighbors
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

def is_valid_pos(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def get_legal_moves(you: np.ndarray, opponent: np.ndarray) -> List[Tuple[int, int]]:
    """Returns a list of (row, col) tuples representing all legal moves."""
    moves = []
    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0:  # empty cell
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    found_opponent = False
                    while is_valid_pos(nr, nc):
                        if opponent[nr][nc] == 1:
                            found_opponent = True
                        elif you[nr][nc] == 1 and found_opponent:
                            moves.append((r, c))
                            break
                        else:
                            break
                        nr, nc = nr + dr, nc + dc
                    if (r, c) in moves:
                        break
    return moves

def make_move(board_you: np.ndarray, board_opponent: np.ndarray, r: int, c: int) -> Tuple[np.ndarray, np.ndarray]:
    """Returns new (you, opponent) arrays after making move at (r, c)."""
    new_you = board_you.copy()
    new_opponent = board_opponent.copy()
    
    new_you[r][c] = 1
    for dr, dc in DIRECTIONS:
        flips = []
        nr, nc = r + dr, c + dc
        while is_valid_pos(nr, nc):
            if new_opponent[nr][nc] == 1:
                flips.append((nr, nc))
            elif new_you[nr][nc] == 1:
                for fr, fc in flips:
                    new_you[fr][fc] = 1
                    new_opponent[fr][fc] = 0
                break
            else:
                break
            nr, nc = nr + dr, nc + dc
    return new_you, new_opponent

def count_discs(you: np.ndarray, opponent: np.ndarray) -> Tuple[int, int]:
    """Returns (your discs, opponent discs) count."""
    return int(np.sum(you)), int(np.sum(opponent))

def evaluate_board(you: np.ndarray, opponent: np.ndarray) -> float:
    """
    Evaluation function that returns a score from your perspective.
    Higher is better.
    """
    your_discs, opp_discs = count_discs(you, opponent)
    
    # Corner control (very valuable)
    corners = [(0,0), (0,7), (7,0), (7,7)]
    your_corners = sum(1 for r, c in corners if you[r][c] == 1)
    opp_corners = sum(1 for r, c in corners if opponent[r][c] == 1)
    
    # Edge control (moderately valuable)
    edges = []
    for r in [0, 7]:
        for c in range(1, 7):
            edges.append((r, c))
    for c in [0, 7]:
        for r in range(1, 7):
            edges.append((r, c))
    your_edges = sum(1 for r, c in edges if you[r][c] == 1)
    opp_edges = sum(1 for r, c in edges if opponent[r][c] == 1)
    
    # Mobility (number of legal moves)
    your_moves = len(get_legal_moves(you, opponent))
    opp_moves = len(get_legal_moves(opponent, you))
    
    # Frontier discs (discs adjacent to empty squares - want to minimize)
    def count_frontier(board):
        frontier = 0
        for r in range(8):
            for c in range(8):
                if board[r][c] == 1:
                    for dr, dc in DIRECTIONS:
                        nr, nc = r + dr, c + dc
                        if is_valid_pos(nr, nc) and you[nr][nc] == 0 and opponent[nr][nc] == 0:
                            frontier += 1
                            break
        return frontier
    
    your_frontier = count_frontier(you)
    opp_frontier = count_frontier(opponent)
    
    # Stability - count discs that cannot be flipped (heuristic)
    def count_stable(you, opponent):
        # Simple stability: count corner-adjacent discs that are in stable lines
        # This is a simplified version - full stability is complex
        stable = 0
        for r in range(8):
            for c in range(8):
                if you[r][c] == 1:
                    # Check if the disc is in a stable row/col
                    def stable_in_line(dr, dc):
                        # check if this disc is part of a stable line toward edge
                        current_r, current_c = r, c
                        while is_valid_pos(current_r, current_c):
                            if you[current_r][current_c] == 0:
                                return False
                            current_r += dr
                            current_c += dc
                        return True
                    
                    if any(stable_in_line(dr, dc) for dr, dc in DIRECTIONS):
                        stable += 1
        return stable
    
    your_stability = count_stable(you, opponent)
    opp_stability = count_stable(opponent, you)
    
    # Board parity: favor being ahead in disc count late-game
    total_discs = your_discs + opp_discs
    if total_discs > 50:  # Endgame
        disc_score = (your_discs - opp_discs) * 10.0
    else:
        disc_score = (your_discs - opp_discs) * 0.5
    
    # Combine scores with weights
    score = (
        25.0 * (your_corners - opp_corners) +      # Corners are very valuable
        5.0 * (your_edges - opp_edges) +           # Edges are valuable
        3.0 * (your_moves - opp_moves) +           # Mobility
        -2.0 * (your_frontier - opp_frontier) +    # Minimize frontier
        1.5 * (your_stability - opp_stability) +   # Stability
        disc_score                                 # Disc count
    )
    
    return score

def minimax(you: np.ndarray, opponent: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
    """Minimax with alpha-beta pruning."""
    if depth == 0:
        return evaluate_board(you, opponent)
    
    legal_moves = get_legal_moves(you, opponent)
    if not legal_moves:
        # No moves: check if opponent has moves
        opp_moves = get_legal_moves(opponent, you)
        if not opp_moves:
            # Game over
            your_discs, opp_discs = count_discs(you, opponent)
            return 1000.0 if your_discs > opp_discs else (-1000.0 if your_discs < opp_discs else 0)
        else:
            # Pass; opponent plays next
            return minimax(opponent, you, depth - 1, alpha, beta, not maximizing)
    
    if maximizing:
        max_eval = float('-inf')
        for r, c in legal_moves:
            new_you, new_opponent = make_move(you, opponent, r, c)
            eval_score = minimax(new_you, new_opponent, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Beta cutoff
        return max_eval
    else:
        min_eval = float('inf')
        for r, c in legal_moves:
            new_you, new_opponent = make_move(you, opponent, r, c)
            eval_score = minimax(new_you, new_opponent, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha cutoff
        return min_eval

def get_best_move(you: np.ndarray, opponent: np.ndarray) -> Optional[Tuple[int, int]]:
    """Returns the best move using iterative deepening and move ordering."""
    legal_moves = get_legal_moves(you, opponent)
    if not legal_moves:
        return None
    
    # Order moves: corners first, then edges, then mobility
    def move_priority(move):
        r, c = move
        # Corners (highest priority)
        if (r, c) in [(0,0), (0,7), (7,0), (7,7)]:
            return 3
        # Edges (high priority)
        if r in [0,7] or c in [0,7]:
            return 2
        # Otherwise, prioritize moves that give high mobility to opponent after
        # We'll use a secondary sort by expected evaluation (cheap estimate)
        return 1
    
    legal_moves.sort(key=move_priority, reverse=True)
    
    # Count total discs to estimate depth
    total_discs = int(np.sum(you) + np.sum(opponent))
    
    # Set depth dynamically
    if total_discs < 20:
        max_depth = 6
    elif total_discs < 40:
        max_depth = 7
    else:
        max_depth = 5  # Save time for endgame; too many nodes otherwise
    
    best_move = None
    best_score = float('-inf')
    
    # Iterative deepening
    for depth in range(1, max_depth + 1):
        current_best = None
        current_best_score = float('-inf')
        
        for r, c in legal_moves:
            new_you, new_opponent = make_move(you, opponent, r, c)
            score = minimax(new_you, new_opponent, depth, float('-inf'), float('inf'), False)
            
            if score > current_best_score:
                current_best_score = score
                current_best = (r, c)
                
            # Early termination? Maybe not, since we want to explore all at given depth
        
        # Update best move only if we got a better one
        if current_best_score > best_score:
            best_score = current_best_score
            best_move = current_best
    
    return best_move

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Main policy function that returns the best move in algebraic notation.
    Returns "pass" if no legal moves exist.
    """
    legal_moves = get_legal_moves(you, opponent)
    if not legal_moves:
        return "pass"
    
    best_move = get_best_move(you, opponent)
    if best_move is None:
        return "pass"
    
    r, c = best_move
    # Convert (r, c) to algebraic notation: c -> 'a'..'h', r -> '1'..'8' (r=0 is row 1)
    file = chr(ord('a') + c)
    rank = str(r + 1)
    return file + rank
