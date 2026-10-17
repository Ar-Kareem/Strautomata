
import numpy as np
import random
from collections import deque

def policy(board: list[list[int]]) -> int:
    # Convert board to numpy array for easier manipulation
    np_board = np.array(board)
    
    # Constants
    ROWS, COLS = 6, 7
    EMPTY = 0
    PLAYER = 1
    OPPONENT = -1
    WIN = 1000000
    LOSE = -1000000
    
    # Check if a move leads to immediate win
    def check_win(board, player, col):
        # Make a temporary move
        temp_board = board.copy()
        for row in range(ROWS-1, -1, -1):
            if temp_board[row][col] == EMPTY:
                temp_board[row][col] = player
                break
        else:
            return False  # Column is full
        
        # Check for win
        return is_winning_board(temp_board, player, col)
    
    # Check if player has won on the board
    def is_winning_board(board, player, last_col):
        # Find the last row where the piece was placed
        last_row = -1
        for row in range(ROWS):
            if board[row][last_col] != EMPTY:
                last_row = row
                break
        
        if last_row == -1:  # Column was empty, piece goes to bottom
            last_row = ROWS - 1
        else:
            last_row -= 1  # Move to the actual row of the new piece
            
        # Check horizontal
        count = 1
        # Check right
        for c in range(last_col + 1, min(COLS, last_col + 4)):
            if board[last_row][c] == player:
                count += 1
            else:
                break
        # Check left
        for c in range(last_col - 1, max(-1, last_col - 4), -1):
            if board[last_row][c] == player:
                count += 1
            else:
                break
        if count >= 4:
            return True
            
        # Check vertical
        count = 1
        # Check down (only down since we place at the top)
        for r in range(last_row + 1, min(ROWS, last_row + 4)):
            if board[r][last_col] == player:
                count += 1
            else:
                break
        if count >= 4:
            return True
            
        # Check diagonal (top-left to bottom-right)
        count = 1
        # Check down-right
        r, c = last_row + 1, last_col + 1
        while r < ROWS and c < COLS and count < 4:
            if board[r][c] == player:
                count += 1
            else:
                break
            r += 1
            c += 1
        # Check up-left
        r, c = last_row - 1, last_col - 1
        while r >= 0 and c >= 0 and count < 4:
            if board[r][c] == player:
                count += 1
            else:
                break
            r -= 1
            c -= 1
        if count >= 4:
            return True
            
        # Check diagonal (top-right to bottom-left)
        count = 1
        # Check down-left
        r, c = last_row + 1, last_col - 1
        while r < ROWS and c >= 0 and count < 4:
            if board[r][c] == player:
                count += 1
            else:
                break
            r += 1
            c -= 1
        # Check up-right
        r, c = last_row - 1, last_col + 1
        while r >= 0 and c < COLS and count < 4:
            if board[r][c] == player:
                count += 1
            else:
                break
            r -= 1
            c += 1
        if count >= 4:
            return True
            
        return False
    
    # Get valid moves
    def get_valid_moves(board):
        return [col for col in range(COLS) if board[0][col] == EMPTY]
    
    # Evaluate board position
    def evaluate_board(board):
        # Check for immediate win/loss
        valid_moves = get_valid_moves(board)
        
        # Check for winning move
        for col in valid_moves:
            if check_win(board, PLAYER, col):
                return WIN
                
        # Check for opponent winning move to block
        for col in valid_moves:
            if check_win(board, OPPONENT, col):
                return 10000  # High value to prioritize blocking
        
        # Center column preference
        score = 0
        center_col = COLS // 2
        center_count = sum(1 for row in range(ROWS) if board[row][center_col] == PLAYER)
        score += center_count * 3
        
        # Evaluate positions based on potential patterns
        # Horizontal
        for row in range(ROWS):
            for col in range(COLS - 3):
                window = [board[row][col+i] for i in range(4)]
                score += evaluate_window(window)
                
        # Vertical
        for row in range(ROWS - 3):
            for col in range(COLS):
                window = [board[row+i][col] for i in range(4)]
                score += evaluate_window(window)
                
        # Diagonal /
        for row in range(3, ROWS):
            for col in range(COLS - 3):
                window = [board[row-i][col+i] for i in range(4)]
                score += evaluate_window(window)
                
        # Diagonal \
        for row in range(ROWS - 3):
            for col in range(COLS - 3):
                window = [board[row+i][col+i] for i in range(4)]
                score += evaluate_window(window)
                
        return score
    
    def evaluate_window(window):
        score = 0
        player_count = window.count(PLAYER)
        opponent_count = window.count(OPPONENT)
        empty_count = window.count(EMPTY)
        
        if opponent_count == 0:
            if player_count == 3 and empty_count == 1:
                score += 100  # Three in a row with space
            elif player_count == 2 and empty_count == 2:
                score += 10   # Two in a row with space
        elif player_count == 0:
            if opponent_count == 3 and empty_count == 1:
                score -= 80   # Block opponent's three
            elif opponent_count == 2 and empty_count == 2:
                score -= 5    # Block opponent's two
                
        return score
    
    # Minimax with alpha-beta pruning
    def minimax(board, depth, alpha, beta, maximizing):
        valid_moves = get_valid_moves(board)
        
        # Terminal conditions
        if depth == 0 or not valid_moves:
            return evaluate_board(board)
            
        # Check for immediate wins
        if maximizing:
            for col in valid_moves:
                if check_win(board, PLAYER, col):
                    return WIN
        else:
            for col in valid_moves:
                if check_win(board, OPPONENT, col):
                    return LOSE
        
        if maximizing:
            max_eval = LOSE
            # Sort moves to improve alpha-beta pruning
            move_scores = []
            for col in valid_moves:
                # Prefer center columns
                move_score = 0
                if col == 3:  # Center column
                    move_score = 3
                elif col in [2, 4]:
                    move_score = 2
                elif col in [1, 5]:
                    move_score = 1
                move_scores.append((col, move_score))
            move_scores.sort(key=lambda x: x[1], reverse=True)
            ordered_moves = [col for col, _ in move_scores]
            
            for col in ordered_moves:
                # Make move
                temp_board = board.copy()
                for row in range(ROWS-1, -1, -1):
                    if temp_board[row][col] == EMPTY:
                        temp_board[row][col] = PLAYER
                        break
                        
                eval_score = minimax(temp_board, depth-1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = WIN
            # Sort moves for opponent too
            move_scores = []
            for col in valid_moves:
                # Prefer center columns
                move_score = 0
                if col == 3:  # Center column
                    move_score = 3
                elif col in [2, 4]:
                    move_score = 2
                elif col in [1, 5]:
                    move_score = 1
                move_scores.append((col, move_score))
            move_scores.sort(key=lambda x: x[1], reverse=True)
            ordered_moves = [col for col, _ in move_scores]
            
            for col in ordered_moves:
                # Make move
                temp_board = board.copy()
                for row in range(ROWS-1, -1, -1):
                    if temp_board[row][col] == EMPTY:
                        temp_board[row][col] = OPPONENT
                        break
                        
                eval_score = minimax(temp_board, depth-1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Get best move
    valid_moves = get_valid_moves(np_board)
    
    # If there's a winning move, take it
    for col in valid_moves:
        if check_win(np_board, PLAYER, col):
            return col
            
    # If opponent has a winning move, block it
    for col in valid_moves:
        if check_win(np_board, OPPONENT, col):
            return col
    
    # Use minimax for deeper search
    best_score = LOSE - 1
    best_col = random.choice(valid_moves)
    
    # Sort moves to improve search - prefer center
    move_scores = []
    for col in valid_moves:
        # Prefer center columns
        move_score = 0
        if col == 3:  # Center column
            move_score = 3
        elif col in [2, 4]:
            move_score = 2
        elif col in [1, 5]:
            move_score = 1
        move_scores.append((col, move_score))
    move_scores.sort(key=lambda x: x[1], reverse=True)
    ordered_moves = [col for col, _ in move_scores]
    
    for col in ordered_moves:
        # Make move
        temp_board = np_board.copy()
        for row in range(ROWS-1, -1, -1):
            if temp_board[row][col] == EMPTY:
                temp_board[row][col] = PLAYER
                break
                
        score = minimax(temp_board, 4, LOSE, WIN, False)
        
        if score > best_score:
            best_score = score
            best_col = col
            
    return best_col
