
import numpy as np
from typing import List

def policy(board: List[List[int]]) -> int:
    # Create a copy of the board to work with
    board_copy = [row[:] for row in board]
    
    def is_valid_move(col):
        return board_copy[0][col] == 0
    
    def drop_disc(col, player):
        # Find the lowest empty row in the column
        for row in range(5, -1, -1):
            if board_copy[row][col] == 0:
                board_copy[row][col] = player
                return row
        return -1  # Should not happen if is_valid_move is checked first
    
    def undo_disc(col):
        # Find the topmost disc in the column and remove it
        for row in range(6):
            if board_copy[row][col] != 0:
                board_copy[row][col] = 0
                break
    
    def count_consecutive(row, col, d_row, d_col, player):
        """Count consecutive discs in a direction"""
        count = 0
        r, c = row, col
        while 0 <= r < 6 and 0 <= c < 7 and board_copy[r][c] == player:
            count += 1
            r += d_row
            c += d_col
        return count
    
    def check_win(player):
        """Check if player has won"""
        for row in range(6):
            for col in range(7):
                if board_copy[row][col] != player:
                    continue
                # Check all 4 directions
                directions = [
                    (0, 1),  # horizontal
                    (1, 0),  # vertical
                    (1, 1),  # diagonal down-right
                    (1, -1)  # diagonal down-left
                ]
                for d_row, d_col in directions:
                    count = count_consecutive(row, col, d_row, d_col, player)
                    if count >= 4:
                        return True
        return False
    
    def evaluate_position():
        """Evaluate the current board position"""
        score = 0
        
        # Check for wins - if we can win immediately, choose that move
        for col in range(7):
            if is_valid_move(col):
                row = drop_disc(col, 1)
                if check_win(1):
                    undo_disc(col)
                    return 100000  # Very high score for immediate win
                undo_disc(col)
        
        # Check for opponent wins - block them
        for col in range(7):
            if is_valid_move(col):
                row = drop_disc(col, -1)
                if check_win(-1):
                    undo_disc(col)
                    return 90000  # High score to block opponent win
                undo_disc(col)
        
        # Evaluate all possible positions
        for row in range(6):
            for col in range(7):
                if board_copy[row][col] != 0:
                    continue
                
                # Evaluate current position
                player = 1  # We are checking how the position looks for us
                
                # Check all directions for potential winning lines
                directions = [
                    (0, 1),  # horizontal
                    (1, 0),  # vertical
                    (1, 1),  # diagonal down-right
                    (1, -1)  # diagonal down-left
                ]
                
                for d_row, d_col in directions:
                    # Count our discs in this line (including current position)
                    count = 1  # Count the current position
                    # Count forwards
                    r, c = row + d_row, col + d_col
                    while 0 <= r < 6 and 0 <= c < 7 and board_copy[r][c] == player:
                        count += 1
                        r += d_row
                        c += d_col
                    
                    # Count backwards
                    r, c = row - d_row, col - d_col
                    while 0 <= r < 6 and 0 <= c < 7 and board_copy[r][c] == player:
                        count += 1
                        r -= d_row
                        c -= d_col
                    
                    # Score based on consecutive discs
                    if count >= 4:
                        score += 10000
                    elif count == 3:
                        score += 100
                    elif count == 2:
                        score += 10
                
                # Negative evaluation for opponent
                player = -1
                for d_row, d_col in directions:
                    # Count opponent's discs in this line
                    count = 1  # Count the current position
                    # Count forwards
                    r, c = row + d_row, col + d_col
                    while 0 <= r < 6 and 0 <= c < 7 and board_copy[r][c] == player:
                        count += 1
                        r += d_row
                        c += d_col
                    
                    # Count backwards
                    r, c = row - d_row, col - d_col
                    while 0 <= r < 6 and 0 <= c < 7 and board_copy[r][c] == player:
                        count += 1
                        r -= d_row
                        c -= d_col
                    
                    # Score for opponent's lines
                    if count >= 4:
                        score -= 10000
                    elif count == 3:
                        score -= 100
                    elif count == 2:
                        score -= 10
        
        return score
    
    # Try to make a winning move
    for col in range(7):
        if is_valid_move(col):
            drop_disc(col, 1)
            if check_win(1):
                return col
            undo_disc(col)
    
    # Try to block opponent's winning move
    for col in range(7):
        if is_valid_move(col):
            drop_disc(col, -1)
            if check_win(-1):
                undo_disc(col)
                return col
            undo_disc(col)
    
    # Evaluate all columns
    scores = []
    for col in range(7):
        if is_valid_move(col):
            # Temporarily place our disc
            row = drop_disc(col, 1)
            score = evaluate_position()
            undo_disc(col)
            scores.append((score, col))
        else:
            scores.append((-1, col))  # Invalid move
    
    # Sort by score descending
    scores.sort(reverse=True)
    
    # Return the best column
    for score, col in scores:
        if score != -1:
            return col
    
    # Fallback - return any valid move
    for col in range(7):
        if is_valid_move(col):
            return col
    
    # Should never reach here in valid game state
    return 3  # Return center column as last resort
