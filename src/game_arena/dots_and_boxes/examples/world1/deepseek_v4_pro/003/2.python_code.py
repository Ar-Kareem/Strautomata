
import numpy as np
from typing import List, Tuple, Optional
import time

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Dots and Boxes policy using minimax with alpha-beta pruning.
    """
    start_time = time.time()
    time_limit = 0.95  # Leave some margin
    
    # Find all legal moves
    legal_moves = get_legal_moves(horizontal, vertical)
    
    if not legal_moves:
        # No legal moves, return a dummy move (shouldn't happen in practice)
        return "0,0,H"
    
    # First, check for immediate captures (moves that complete at least one box)
    for move in legal_moves:
        row, col, dir = move
        if completes_box(row, col, dir, horizontal, vertical, capture):
            return f"{row},{col},{dir}"
    
    # If no immediate captures, use minimax search
    best_move = None
    best_score = float('-inf')
    
    # Try different depths based on remaining moves
    num_legal = len(legal_moves)
    max_depth = 3 if num_legal > 20 else 4
    if num_legal < 10:
        max_depth = 6
    
    # Iterative deepening
    for depth in range(1, max_depth + 1):
        if time.time() - start_time > time_limit * 0.5:
            break
            
        current_best_move = None
        current_best_score = float('-inf')
        alpha = float('-inf')
        beta = float('inf')
        
        # Sort moves to improve pruning (try safer moves first)
        scored_moves = []
        for move in legal_moves:
            score = evaluate_move_safety(move, horizontal, vertical, capture)
            scored_moves.append((score, move))
        scored_moves.sort(reverse=True)  # Try safer moves first
        
        for _, move in scored_moves:
            if time.time() - start_time > time_limit:
                break
                
            new_h, new_v, new_c = apply_move(move, horizontal, vertical, capture, 1)
            
            if completes_box(move[0], move[1], move[2], horizontal, vertical, capture):
                # If we complete a box, we get another turn
                score = minimax(new_h, new_v, new_c, depth - 1, True, alpha, beta, start_time, time_limit)
            else:
                score = minimax(new_h, new_v, new_c, depth - 1, False, alpha, beta, start_time, time_limit)
            
            if score > current_best_score:
                current_best_score = score
                current_best_move = move
                alpha = max(alpha, score)
        
        if current_best_move is not None:
            best_move = current_best_move
            best_score = current_best_score
    
    if best_move is None:
        # Fallback: choose the safest move
        best_move = select_safest_move(legal_moves, horizontal, vertical, capture)
    
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"


def get_legal_moves(horizontal: np.ndarray, vertical: np.ndarray) -> List[Tuple[int, int, str]]:
    """Get all legal moves (empty edges)."""
    moves = []
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                moves.append((row, col, 'H'))
            if vertical[row, col] == 0:
                moves.append((row, col, 'V'))
    return moves


def completes_box(row: int, col: int, dir: str, 
                  horizontal: np.ndarray, vertical: np.ndarray, 
                  capture: np.ndarray) -> bool:
    """Check if a move completes at least one box."""
    if dir == 'H':
        # A horizontal edge can complete boxes above and below it
        # Box above: (row-1, col) - check if all 4 edges are now filled
        if row > 0:
            if (horizontal[row-1, col] != 0 and 
                vertical[row-1, col] != 0 and 
                vertical[row-1, col+1] != 0 and 
                capture[row-1, col] == 0):
                return True
        # Box below: (row, col)
        if row < 4:
            if (horizontal[row+1, col] != 0 and 
                vertical[row, col] != 0 and 
                vertical[row, col+1] != 0 and 
                capture[row, col] == 0):
                return True
    else:  # dir == 'V'
        # A vertical edge can complete boxes to its left and right
        # Box to the left: (row, col-1)
        if col > 0:
            if (vertical[row, col-1] != 0 and 
                horizontal[row, col-1] != 0 and 
                horizontal[row+1, col-1] != 0 and 
                capture[row, col-1] == 0):
                return True
        # Box to the right: (row, col)
        if col < 4:
            if (vertical[row, col+1] != 0 and 
                horizontal[row, col] != 0 and 
                horizontal[row+1, col] != 0 and 
                capture[row, col] == 0):
                return True
    return False


def count_completed_boxes(row: int, col: int, dir: str,
                          horizontal: np.ndarray, vertical: np.ndarray,
                          capture: np.ndarray) -> int:
    """Count how many boxes a move completes."""
    count = 0
    if dir == 'H':
        if row > 0:
            if (horizontal[row-1, col] != 0 and 
                vertical[row-1, col] != 0 and 
                vertical[row-1, col+1] != 0 and 
                capture[row-1, col] == 0):
                count += 1
        if row < 4:
            if (horizontal[row+1, col] != 0 and 
                vertical[row, col] != 0 and 
                vertical[row, col+1] != 0 and 
                capture[row, col] == 0):
                count += 1
    else:
        if col > 0:
            if (vertical[row, col-1] != 0 and 
                horizontal[row, col-1] != 0 and 
                horizontal[row+1, col-1] != 0 and 
                capture[row, col-1] == 0):
                count += 1
        if col < 4:
            if (vertical[row, col+1] != 0 and 
                horizontal[row, col] != 0 and 
                horizontal[row+1, col] != 0 and 
                capture[row, col] == 0):
                count += 1
    return count


def apply_move(move: Tuple[int, int, str], 
               horizontal: np.ndarray, vertical: np.ndarray, 
               capture: np.ndarray, player: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Apply a move and return new state."""
    row, col, dir = move
    new_h = horizontal.copy()
    new_v = vertical.copy()
    new_c = capture.copy()
    
    if dir == 'H':
        new_h[row, col] = player
    else:
        new_v[row, col] = player
    
    # Check for completed boxes
    if dir == 'H':
        if row > 0:
            if (new_h[row-1, col] != 0 and 
                new_v[row-1, col] != 0 and 
                new_v[row-1, col+1] != 0 and 
                new_c[row-1, col] == 0):
                new_c[row-1, col] = player
        if row < 4:
            if (new_h[row+1, col] != 0 and 
                new_v[row, col] != 0 and 
                new_v[row, col+1] != 0 and 
                new_c[row, col] == 0):
                new_c[row, col] = player
    else:
        if col > 0:
            if (new_v[row, col-1] != 0 and 
                new_h[row, col-1] != 0 and 
                new_h[row+1, col-1] != 0 and 
                new_c[row, col-1] == 0):
                new_c[row, col-1] = player
        if col < 4:
            if (new_v[row, col+1] != 0 and 
                new_h[row, col] != 0 and 
                new_h[row+1, col] != 0 and 
                new_c[row, col] == 0):
                new_c[row, col] = player
    
    return new_h, new_v, new_c


def evaluate_move_safety(move: Tuple[int, int, str],
                         horizontal: np.ndarray, vertical: np.ndarray,
                         capture: np.ndarray) -> float:
    """Evaluate how safe a move is (higher = safer)."""
    row, col, dir = move
    
    # Check if this move creates a three-sided box
    score = 0.0
    
    if dir == 'H':
        # Check box above
        if row > 0 and capture[row-1, col] == 0:
            filled_edges = 0
            if horizontal[row-1, col] != 0:
                filled_edges += 1
            if vertical[row-1, col] != 0:
                filled_edges += 1
            if vertical[row-1, col+1] != 0:
                filled_edges += 1
            if filled_edges == 2:
                score -= 10  # This would create a three-sided box
                
        # Check box below
        if row < 4 and capture[row, col] == 0:
            filled_edges = 0
            if horizontal[row+1, col] != 0:
                filled_edges += 1
            if vertical[row, col] != 0:
                filled_edges += 1
            if vertical[row, col+1] != 0:
                filled_edges += 1
            if filled_edges == 2:
                score -= 10
    else:
        # Check box to the left
        if col > 0 and capture[row, col-1] == 0:
            filled_edges = 0
            if vertical[row, col-1] != 0:
                filled_edges += 1
            if horizontal[row, col-1] != 0:
                filled_edges += 1
            if horizontal[row+1, col-1] != 0:
                filled_edges += 1
            if filled_edges == 2:
                score -= 10
                
        # Check box to the right
        if col < 4 and capture[row, col] == 0:
            filled_edges = 0
            if vertical[row, col+1] != 0:
                filled_edges += 1
            if horizontal[row, col] != 0:
                filled_edges += 1
            if horizontal[row+1, col] != 0:
                filled_edges += 1
            if filled_edges == 2:
                score -= 10
    
    return score


def select_safest_move(legal_moves: List[Tuple[int, int, str]],
                       horizontal: np.ndarray, vertical: np.ndarray,
                       capture: np.ndarray) -> Tuple[int, int, str]:
    """Select the safest move among legal moves."""
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        score = evaluate_move_safety(move, horizontal, vertical, capture)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move


def evaluate_state(horizontal: np.ndarray, vertical: np.ndarray, 
                   capture: np.ndarray) -> float:
    """Evaluate the current state from our perspective."""
    # Count captured boxes
    our_boxes = np.sum(capture == 1)
    opp_boxes = np.sum(capture == -1)
    
    score = (our_boxes - opp_boxes) * 100
    
    # Penalize moves that create three-sided boxes
    for row in range(4):
        for col in range(4):
            if capture[row, col] == 0:
                filled_edges = 0
                if horizontal[row, col] != 0:
                    filled_edges += 1
                if horizontal[row+1, col] != 0:
                    filled_edges += 1
                if vertical[row, col] != 0:
                    filled_edges += 1
                if vertical[row, col+1] != 0:
                    filled_edges += 1
                
                if filled_edges == 3:
                    # This box is about to be captured
                    # Determine who will capture it based on whose turn it is
                    # This is a heuristic - we can't know for sure
                    score -= 5
                elif filled_edges == 2:
                    # Potential danger
                    score -= 1
    
    return score


def minimax(horizontal: np.ndarray, vertical: np.ndarray, 
            capture: np.ndarray, depth: int, is_maximizing: bool,
            alpha: float, beta: float, start_time: float, 
            time_limit: float) -> float:
    """Minimax with alpha-beta pruning."""
    
    if time.time() - start_time > time_limit:
        return evaluate_state(horizontal, vertical, capture)
    
    if depth == 0:
        return evaluate_state(horizontal, vertical, capture)
    
    legal_moves = get_legal_moves(horizontal, vertical)
    
    if not legal_moves:
        return evaluate_state(horizontal, vertical, capture)
    
    if is_maximizing:
        max_eval = float('-inf')
        
        # Check for immediate captures first
        capture_moves = []
        safe_moves = []
        
        for move in legal_moves:
            if completes_box(move[0], move[1], move[2], horizontal, vertical, capture):
                capture_moves.append(move)
            else:
                safe_moves.append(move)
        
        # Prioritize capture moves
        moves_to_check = capture_moves + safe_moves
        
        for move in moves_to_check:
            if time.time() - start_time > time_limit:
                break
                
            new_h, new_v, new_c = apply_move(move, horizontal, vertical, capture, 1)
            
            if completes_box(move[0], move[1], move[2], horizontal, vertical, capture):
                # We get another turn
                eval_score = minimax(new_h, new_v, new_c, depth - 1, True, alpha, beta, start_time, time_limit)
            else:
                eval_score = minimax(new_h, new_v, new_c, depth - 1, False, alpha, beta, start_time, time_limit)
            
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        
        return max_eval if max_eval != float('-inf') else evaluate_state(horizontal, vertical, capture)
    else:
        min_eval = float('inf')
        
        # Check for immediate captures for opponent
        capture_moves = []
        safe_moves = []
        
        for move in legal_moves:
            if completes_box(move[0], move[1], move[2], horizontal, vertical, capture):
                capture_moves.append(move)
            else:
                safe_moves.append(move)
        
        moves_to_check = capture_moves + safe_moves
        
        for move in moves_to_check:
            if time.time() - start_time > time_limit:
                break
                
            new_h, new_v, new_c = apply_move(move, horizontal, vertical, capture, -1)
            
            if completes_box(move[0], move[1], move[2], horizontal, vertical, capture):
                # Opponent gets another turn
                eval_score = minimax(new_h, new_v, new_c, depth - 1, False, alpha, beta, start_time, time_limit)
            else:
                eval_score = minimax(new_h, new_v, new_c, depth - 1, True, alpha, beta, start_time, time_limit)
            
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        
        return min_eval if min_eval != float('inf') else evaluate_state(horizontal, vertical, capture)
