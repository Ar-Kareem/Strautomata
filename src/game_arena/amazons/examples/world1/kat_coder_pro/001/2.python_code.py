
import numpy as np
from typing import List, Tuple, Optional

def policy(board: np.ndarray) -> str:
    """
    Implements a depth-1 minimax policy for Amazons on a 6x6 board.
    
    The policy evaluates all legal moves and selects the one that maximizes
    a heuristic score based on mobility and board control.
    """
    
    def get_legal_moves(board: np.ndarray, player: int) -> List[Tuple[int, int, int, int, int, int]]:
        """Generate all legal moves for the given player."""
        moves = []
        opponent = 3 - player  # 1->2, 2->1
        
        # Find all amazons for the current player
        amazon_positions = np.where(board == player)
        amazon_coords = list(zip(amazon_positions[0], amazon_positions[1]))
        
        for from_row, from_col in amazon_coords:
            # Try all possible move destinations
            for to_row in range(6):
                for to_col in range(6):
                    if (to_row, to_col) == (from_row, from_col):
                        continue
                    
                    # Check if the move is valid (queen-like movement, unobstructed path)
                    if is_valid_move(board, from_row, from_col, to_row, to_col, player):
                        # Try all possible arrow shots from the destination
                        for arrow_row in range(6):
                            for arrow_col in range(6):
                                if (arrow_row, arrow_col) == (to_row, to_col):
                                    continue
                                if is_valid_arrow(board, to_row, to_col, arrow_row, arrow_col, from_row, from_col):
                                    moves.append((from_row, from_col, to_row, to_col, arrow_row, arrow_col))
        
        return moves
    
    def is_valid_move(board: np.ndarray, from_row: int, from_col: int, 
                     to_row: int, to_col: int, player: int) -> bool:
        """Check if a move from (from_row, from_col) to (to_row, to_col) is valid."""
        # Check if destination is empty
        if board[to_row, to_col] != 0:
            return False
        
        # Check if movement is queen-like (orthogonal or diagonal)
        dr = to_row - from_row
        dc = to_col - from_col
        
        # Must move at least one square
        if dr == 0 and dc == 0:
            return False
        
        # Check if it's a valid queen move (straight line)
        if dr != 0 and dc != 0 and abs(dr) != abs(dc):
            return False
        
        # Check path is unobstructed
        step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
        step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
        
        r, c = from_row + step_r, from_col + step_c
        while (r, c) != (to_row, to_col):
            if board[r, c] != 0:
                return False
            r += step_r
            c += step_c
        
        return True
    
    def is_valid_arrow(board: np.ndarray, from_row: int, from_col: int,
                      arrow_row: int, arrow_col: int, amazon_from_row: int, amazon_from_col: int) -> bool:
        """Check if an arrow shot from (from_row, from_col) to (arrow_row, arrow_col) is valid."""
        # Check if arrow destination is not occupied by an amazon
        if board[arrow_row, arrow_col] in [1, 2]:
            return False
        
        # Check if shot is queen-like movement
        dr = arrow_row - from_row
        dc = arrow_col - from_col
        
        # Must shoot at least one square
        if dr == 0 and dc == 0:
            return False
        
        # Check if it's a valid queen move
        if dr != 0 and dc != 0 and abs(dr) != abs(dc):
            return False
        
        # Check path is unobstructed (note: amazon has moved, so original position is now empty)
        step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
        step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
        
        r, c = from_row + step_r, from_col + step_c
        while (r, c) != (arrow_row, arrow_col):
            if board[r, c] in [1, 2, -1]:  # Blocked by amazon or arrow
                return False
            r += step_r
            c += step_c
        
        return True
    
    def evaluate_board(board: np.ndarray, player: int) -> float:
        """Evaluate the board position for the given player."""
        opponent = 3 - player
        
        # Count mobility (number of legal moves available)
        player_moves = len(get_legal_moves(board, player))
        opponent_moves = len(get_legal_moves(board, opponent))
        
        # Simple heuristic: maximize our mobility while minimizing opponent's
        # Add a small bonus for having more amazons (though this shouldn't change in normal play)
        player_amazons = np.sum(board == player)
        opponent_amazons = np.sum(board == opponent)
        
        return player_moves - opponent_moves + 10 * (player_amazons - opponent_amazons)
    
    def make_move(board: np.ndarray, move: Tuple[int, int, int, int, int, int]) -> np.ndarray:
        """Apply a move to the board and return the new board state."""
        from_row, from_col, to_row, to_col, arrow_row, arrow_col = move
        
        new_board = board.copy()
        
        # Move amazon
        new_board[from_row, from_col] = 0
        new_board[to_row, to_col] = 1
        
        # Shoot arrow
        new_board[arrow_row, arrow_col] = -1
        
        return new_board
    
    # Get all legal moves for the current player (1)
    legal_moves = get_legal_moves(board, 1)
    
    if not legal_moves:
        # This should not happen in normal play, but return a placeholder
        return "0,0:0,0:0,0"
    
    # Evaluate all moves and select the best one
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        new_board = make_move(board, move)
        score = evaluate_board(new_board, 1)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    # Format the move as a string
    from_row, from_col, to_row, to_col, arrow_row, arrow_col = best_move
    return f"{from_row},{from_col}:{to_row},{to_col}:{arrow_row},{arrow_col}"
