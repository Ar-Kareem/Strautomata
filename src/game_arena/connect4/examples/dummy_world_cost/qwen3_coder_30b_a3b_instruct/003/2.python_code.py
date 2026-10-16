
import numpy as np
import math
from typing import List, Tuple

def policy(board: List[List[int]]) -> int:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Define the transposition table for memoization
    transposition_table = {}
    
    def is_valid_move(col: int) -> bool:
        return board_np[0][col] == 0
    
    def get_next_open_row(col: int) -> int:
        for row in range(5, -1, -1):
            if board_np[row][col] == 0:
                return row
        return -1
    
    def drop_disc(col: int, player: int) -> np.ndarray:
        new_board = board_np.copy()
        row = get_next_open_row(col)
        if row != -1:
            new_board[row][col] = player
        return new_board
    
    def check_winner(new_board: np.ndarray, player: int) -> bool:
        # Check horizontal
        for row in range(6):
            for col in range(4):
                if all(new_board[row][col + i] == player for i in range(4)):
                    return True
        
        # Check vertical
        for row in range(3):
            for col in range(7):
                if all(new_board[row + i][col] == player for i in range(4)):
                    return True
        
        # Check positive diagonal
        for row in range(3):
            for col in range(4):
                if all(new_board[row + i][col + i] == player for i in range(4)):
                    return True
        
        # Check negative diagonal
        for row in range(3, 6):
            for col in range(4):
                if all(new_board[row - i][col + i] == player for i in range(4)):
                    return True
        
        return False
    
    def evaluate_position(board_state: np.ndarray) -> int:
        score = 0
        
        # Score center column preference
        center_array = [board_state[row][3] for row in range(6)]
        center_count = center_array.count(1)
        score += center_count * 3
        
        # Score horizontal
        for row in range(6):
            row_array = [int(board_state[row][col]) for col in range(7)]
            for col in range(4):
                window = row_array[col:col + 4]
                score += evaluate_window(window)
        
        # Score vertical
        for col in range(7):
            col_array = [int(board_state[row][col]) for row in range(6)]
            for row in range(3):
                window = col_array[row:row + 4]
                score += evaluate_window(window)
        
        # Score positive diagonals
        for row in range(3):
            for col in range(4):
                window = [board_state[row + i][col + i] for i in range(4)]
                score += evaluate_window(window)
        
        # Score negative diagonals
        for row in range(3, 6):
            for col in range(4):
                window = [board_state[row - i][col + i] for i in range(4)]
                score += evaluate_window(window)
        
        return score
    
    def evaluate_window(window: List[int]) -> int:
        score = 0
        player_count = window.count(1)
        opponent_count = window.count(-1)
        empty_count = window.count(0)
        
        if player_count == 4:
            score += 100
        elif player_count == 3 and empty_count == 1:
            score += 10
        elif player_count == 2 and empty_count == 2:
            score += 2
        
        if opponent_count == 3 and empty_count == 1:
            score -= 80
            
        return score
    
    def minimax(board_state: np.ndarray, depth: int, alpha: float, beta: float, maximizing_player: bool) -> Tuple[int, int]:
        # Possible moves
        valid_moves = [col for col in range(7) if is_valid_move(col)]
        
        # Terminal node or max depth
        if depth == 0 or len(valid_moves) == 0:
            if check_winner(board_state, 1):
                return (None, 100000000000000)
            elif check_winner(board_state, -1):
                return (None, -100000000000000)
            else:  # Game over or depth limit
                return (None, evaluate_position(board_state))
        
        # Transposition table lookup
        board_hash = hash(board_state.tobytes())
        if board_hash in transposition_table:
            if transposition_table[board_hash][1] >= depth:
                return transposition_table[board_hash][0]
        
        if maximizing_player:
            value = -math.inf
            column = valid_moves[0]
            for col in valid_moves:
                new_board = drop_disc(col, 1)
                new_value = minimax(new_board, depth - 1, alpha, beta, False)[1]
                if new_value > value:
                    value = new_value
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            result = (column, value)
            transposition_table[board_hash] = (result, depth)
            return result
        else:
            value = math.inf
            column = valid_moves[0]
            for col in valid_moves:
                new_board = drop_disc(col, -1)
                new_value = minimax(new_board, depth - 1, alpha, beta, True)[1]
                if new_value < value:
                    value = new_value
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            result = (column, value)
            transposition_table[board_hash] = (result, depth)
            return result
    
    # Try to win immediately if possible
    for col in range(7):
        if is_valid_move(col):
            temp_board = drop_disc(col, 1)
            if check_winner(temp_board, 1):
                return col
    
    # Try to block opponent's win
    for col in range(7):
        if is_valid_move(col):
            temp_board = drop_disc(col, -1)
            if check_winner(temp_board, -1):
                return col
    
    # Otherwise use minimax with iterative deepening
    best_score = -math.inf
    best_col = 3  # Default to center column
    
    # Try different depths
    for depth in [2, 3, 4, 5]:
        for col in range(7):
            if is_valid_move(col):
                new_board = drop_disc(col, 1)
                score = minimax(new_board, depth - 1, -math.inf, math.inf, False)[1]
                if score > best_score:
                    best_score = score
                    best_col = col
    
    return best_col
