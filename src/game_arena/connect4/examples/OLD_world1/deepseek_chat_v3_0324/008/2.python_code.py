
import numpy as np

def policy(board: list[list[int]]) -> int:
    """Implements a Connect 4 targeting policy using heuristic evaluation and minimax with alpha-beta pruning."""
    ROWS = 6
    COLS = 7
    
    def get_valid_columns(board):
        return [col for col in range(COLS) if board[0][col] == 0]
    
    def drop_disc(board, col, player):
        """Simulates dropping a disc into the board and returns the new board."""
        board_copy = [row.copy() for row in board]
        for row in range(ROWS-1, -1, -1):
            if board_copy[row][col] == 0:
                board_copy[row][col] = player
                break
        return board_copy
    
    def evaluate_window(window, player):
        """Evaluates a 4-piece window for the given player."""
        opponent = -1 if player == 1 else 1
        player_count = window.count(player)
        opponent_count = window.count(opponent)
        empty_count = window.count(0)
        
        if player_count == 4:
            return 100
        elif player_count == 3 and empty_count == 1:
            return 5
        elif player_count == 2 and empty_count == 2:
            return 2
        elif opponent_count == 3 and empty_count == 1:
            return -4
        return 0
    
    def score_position(board, player):
        """Scores the entire board based on the player's position."""
        score = 0
        
        # Score center column
        center_col = COLS // 2
        center_array = [board[i][center_col] for i in range(ROWS)]
        center_count = center_array.count(player)
        score += center_count * 3
        
        # Score horizontal
        for row in range(ROWS):
            for col in range(COLS - 3):
                window = [board[row][col+i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Score vertical
        for col in range(COLS):
            for row in range(ROWS - 3):
                window = [board[row+i][col] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Score positive diagonals
        for row in range(ROWS - 3):
            for col in range(COLS - 3):
                window = [board[row+i][col+i] for i in range(4)]
                score += evaluate_window(window, player)
        
        # Score negative diagonals
        for row in range(3, ROWS):
            for col in range(COLS - 3):
                window = [board[row-i][col+i] for i in range(4)]
                score += evaluate_window(window, player)
        
        return score
    
    def is_winning_move(board, player):
        """Checks if the last move was a winning move."""
        # Check horizontal
        for row in range(ROWS):
            for col in range(COLS - 3):
                if board[row][col] == board[row][col+1] == board[row][col+2] == board[row][col+3] == player:
                    return True
        
        # Check vertical
        for col in range(COLS):
            for row in range(ROWS - 3):
                if board[row][col] == board[row+1][col] == board[row+2][col] == board[row+3][col] == player:
                    return True
        
        # Check positive diagonals
        for row in range(ROWS - 3):
            for col in range(COLS - 3):
                if board[row][col] == board[row+1][col+1] == board[row+2][col+2] == board[row+3][col+3] == player:
                    return True
        
        # Check negative diagonals
        for row in range(3, ROWS):
            for col in range(COLS - 3):
                if board[row][col] == board[row-1][col+1] == board[row-2][col+2] == board[row-3][col+3] == player:
                    return True
        return False
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        valid_columns = get_valid_columns(board)
        is_terminal = (len(valid_columns) == 0) or is_winning_move(board, 1) or is_winning_move(board, -1)
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if is_winning_move(board, 1):
                    return (None, 1000000)
                elif is_winning_move(board, -1):
                    return (None, -1000000)
                else:
                    return (None, 0)
            else:
                return (None, score_position(board, 1))
        
        if maximizing_player:
            value = -float('inf')
            column = np.random.choice(valid_columns)
            for col in valid_columns:
                board_copy = [row.copy() for row in board]
                board_copy = drop_disc(board_copy, col, 1)
                new_score = minimax(board_copy, depth-1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return (column, value)
        else:
            value = float('inf')
            column = np.random.choice(valid_columns)
            for col in valid_columns:
                board_copy = [row.copy() for row in board]
                board_copy = drop_disc(board_copy, col, -1)
                new_score = minimax(board_copy, depth-1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return (column, value)
    
    # Check for immediate wins
    valid_columns = get_valid_columns(board)
    for col in valid_columns:
        board_copy = [row.copy() for row in board]
        board_copy = drop_disc(board_copy, col, 1)
        if is_winning_move(board_copy, 1):
            return col
    
    # Check for opponent's immediate wins to block them
    for col in valid_columns:
        board_copy = [row.copy() for row in board]
        board_copy = drop_disc(board_copy, col, -1)
        if is_winning_move(board_copy, -1):
            return col
    
    # Use minimax with heuristic evaluation
    best_col, _ = minimax(board, 4, -float('inf'), float('inf'), True)
    return best_col if best_col in valid_columns else valid_columns[0]
