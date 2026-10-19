
import numpy as np
from typing import List, Tuple

def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    """
    Clobber game policy that evaluates all legal moves and selects the best one
    based on material gain and board control.
    
    Args:
        you: 5x6 array representing your pieces (1 = your piece, 0 = empty)
        opponent: 5x6 array representing opponent pieces (1 = opponent piece, 0 = empty)
    
    Returns:
        A string in format 'row,col,dir' representing the chosen move
    """
    
    # Convert to numpy arrays for easier manipulation
    you_board = np.array(you, dtype=int)
    opp_board = np.array(opponent, dtype=int)
    
    # Define board dimensions
    rows, cols = 5, 6
    
    # Define direction vectors: Up, Right, Down, Left
    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
    
    def is_valid(r: int, c: int) -> bool:
        """Check if position is within board bounds"""
        return 0 <= r < rows and 0 <= c < cols
    
    def evaluate_position(you_temp: np.ndarray, opp_temp: np.ndarray) -> int:
        """
        Evaluate the board position by counting opponent mobility
        Lower score means opponent has fewer options (better for us)
        """
        score = 0
        for r in range(rows):
            for c in range(cols):
                if opp_temp[r, c] == 1:  # If opponent has a piece here
                    # Count how many directions this piece can move
                    for dr, dc, _ in directions:
                        nr, nc = r + dr, c + dc
                        if is_valid(nr, nc) and you_temp[nr, nc] == 1:
                            score += 1  # This piece can capture in this direction
        return score
    
    def is_isolated(you_temp: np.ndarray, r: int, c: int) -> bool:
        """Check if moving this piece would isolate it"""
        for dr, dc, _ in directions:
            nr, nc = r + dr, c + dc
            if is_valid(nr, nc) and you_temp[nr, nc] == 1:
                return False  # Not isolated, has friendly neighbor
        return True
    
    # Find all legal moves
    legal_moves = []
    
    for r in range(rows):
        for c in range(cols):
            if you_board[r, c] == 1:  # If we have a piece here
                for dr, dc, dir_char in directions:
                    nr, nc = r + dr, c + dc
                    if is_valid(nr, nc) and opp_board[nr, nc] == 1:
                        legal_moves.append((r, c, nr, nc, dir_char))
    
    if not legal_moves:
        # This should theoretically never happen in Clobber
        # Return a safe value to avoid disqualification
        return "0,0,U"
    
    best_move = None
    best_score = float('inf')  # We want to minimize opponent mobility
    
    for r, c, nr, nc, dir_char in legal_moves:
        # Create temporary boards for this move
        you_temp = you_board.copy()
        opp_temp = opp_board.copy()
        
        # Simulate the move
        you_temp[r, c] = 0  # Remove from original position
        you_temp[nr, nc] = 1  # Move to new position
        opp_temp[nr, nc] = 0  # Remove opponent piece
        
        # Evaluate the resulting position
        score = evaluate_position(you_temp, opp_temp)
        
        # Apply bonuses/penalties
        if is_isolated(you_temp, nr, nc):
            score += 10  # Penalty for creating isolated piece
        
        # Prefer central positions
        center_bonus = abs(nr - 2) + abs(nc - 2.5)  # Distance from center
        score += center_bonus * 0.1
        
        # Prefer capturing pieces with fewer escape routes
        opp_escape_routes = 0
        for dr, dc, _ in directions:
            orr, occ = nr + dr, nc + dc
            if is_valid(orr, occ) and you_board[orr, occ] == 1:
                opp_escape_routes += 1
        score -= opp_escape_routes * 0.5
        
        if score < best_score:
            best_score = score
            best_move = (r, c, dir_char)
    
    # Return the best move
    r, c, dir_char = best_move
    return f"{r},{c},{dir_char}"
