
import numpy as np
from typing import Tuple, List

def policy(board: np.ndarray) -> str:
    """Return the best move for the current player using minimax search."""
    
    def get_legal_moves(board_state: np.ndarray) -> List[str]:
        """Generate all legal moves for the current player."""
        moves = []
        size = board_state.shape[0]
        
        # Find all amazons for current player (1)
        amazon_positions = np.where(board_state == 1)
        amazon_coords = list(zip(amazon_positions[0], amazon_positions[1]))
        
        for from_row, from_col in amazon_coords:
            # Try all possible destination squares
            for to_row in range(size):
                for to_col in range(size):
                    if board_state[to_row, to_col] != 0:
                        continue
                    
                    # Check if movement is valid (queen-like, unobstructed)
                    if not is_valid_move(board_state, from_row, from_col, to_row, to_col):
                        continue
                    
                    # Temporarily move amazon (create new board state)
                    temp_board = board_state.copy()
                    temp_board[from_row, from_col] = 0
                    temp_board[to_row, to_col] = 1
                    
                    # Try all possible arrow shots from the new position
                    for arrow_row in range(size):
                        for arrow_col in range(size):
                            if temp_board[arrow_row, arrow_col] != 0:
                                continue
                            
                            # Check if arrow shot is valid
                            if is_valid_move(temp_board, to_row, to_col, arrow_row, arrow_col):
                                move_str = f"{from_row},{from_col}:{to_row},{to_col}:{arrow_row},{arrow_col}"
                                moves.append(move_str)
        
        return moves
    
    def is_valid_move(board_state: np.ndarray, start_row: int, start_col: int, 
                     end_row: int, end_col: int) -> bool:
        """Check if a queen-like move from start to end is valid (unobstructed)."""
        if start_row == end_row and start_col == end_col:
            return False
        
        # Check if move is orthogonal or diagonal
        dr = abs(end_row - start_row)
        dc = abs(end_col - start_col)
        if dr != dc and dr != 0 and dc != 0:
            return False
        
        # Check path is unobstructed
        row_step = 0 if dr == 0 else (1 if end_row > start_row else -1)
        col_step = 0 if dc == 0 else (1 if end_col > start_col else -1)
        
        current_row, current_col = start_row + row_step, start_col + col_step
        while current_row != end_row or current_col != end_col:
            if board_state[current_row, current_col] != 0:
                return False
            current_row += row_step
            current_col += col_step
        
        return True
    
    def make_move(board_state: np.ndarray, move_str: str) -> np.ndarray:
        """Apply a move to the board state and return the new state."""
        parts = move_str.split(':')
        from_part = parts[0].split(',')
        to_part = parts[1].split(',')
        arrow_part = parts[2].split(',')
        
        from_row, from_col = int(from_part[0]), int(from_part[1])
        to_row, to_col = int(to_part[0]), int(to_part[1])
        arrow_row, arrow_col = int(arrow_part[0]), int(arrow_part[1])
        
        new_board = board_state.copy()
        # Move amazon
        new_board[from_row, from_col] = 0
        new_board[to_row, to_col] = 1
        # Shoot arrow
        new_board[arrow_row, arrow_col] = -1
        
        return new_board
    
    def evaluate(board_state: np.ndarray) -> float:
        """Evaluate the board state. Positive values favor the current player."""
        # Count reachable squares for each player
        my_reachable = count_reachable_squares(board_state, 1)
        opponent_reachable = count_reachable_squares(board_state, 2)
        
        # Simple evaluation: difference in reachable squares
        return my_reachable - opponent_reachable
    
    def count_reachable_squares(board_state: np.ndarray, player: int) -> int:
        """Count the number of squares reachable by a player's amazons."""
        size = board_state.shape[0]
        reachable = set()
        
        # Find all amazons for the player
        amazon_positions = np.where(board_state == player)
        amazon_coords = list(zip(amazon_positions[0], amazon_positions[1]))
        
        for amazon_row, amazon_col in amazon_coords:
            # Check all possible moves from this amazon
            for target_row in range(size):
                for target_col in range(size):
                    if board_state[target_row, target_col] != 0:
                        continue
                    if is_valid_move(board_state, amazon_row, amazon_col, target_row, target_col):
                        reachable.add((target_row, target_col))
        
        return len(reachable)
    
    def minimax(board_state: np.ndarray, depth: int, alpha: float, beta: float, 
               maximizing_player: bool) -> Tuple[float, str]:
        """Minimax search with alpha-beta pruning."""
        # Base case: evaluate leaf node
        if depth == 0:
            return evaluate(board_state), ""
        
        legal_moves = get_legal_moves(board_state)
        
        # If no legal moves, return evaluation (terminal state)
        if not legal_moves:
            return evaluate(board_state), ""
        
        if maximizing_player:
            max_eval = float('-inf')
            best_move = ""
            
            for move in legal_moves:
                new_board = make_move(board_state, move)
                eval_score, _ = minimax(new_board, depth - 1, alpha, beta, False)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = ""
            
            # For opponent moves, we need to swap player labels
            # Create a board where player 2 becomes player 1 for evaluation
            swapped_board = board_state.copy()
            swapped_board[board_state == 1] = 2
            swapped_board[board_state == 2] = 1
            
            opponent_moves = get_legal_moves(swapped_board)
            
            for move in opponent_moves:
                new_board = make_move(swapped_board, move)
                # Swap back for recursive call
                eval_board = new_board.copy()
                eval_board[new_board == 1] = 2
                eval_board[new_board == 2] = 1
                
                eval_score, _ = minimax(eval_board, depth - 1, alpha, beta, True)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            
            return min_eval, best_move
    
    # Get all legal moves and use minimax to find the best one
    legal_moves = get_legal_moves(board)
    
    if not legal_moves:
        # Fallback: if no moves available, return a random valid move format (shouldn't happen)
        return "0,0:0,0:0,0"
    
    # Use depth 3 for reasonable performance on 6x6 board
    _, best_move = minimax(board, depth=3, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)
    
    # If minimax fails to find a move, fall back to first legal move
    if best_move == "":
        best_move = legal_moves[0]
    
    return best_move
