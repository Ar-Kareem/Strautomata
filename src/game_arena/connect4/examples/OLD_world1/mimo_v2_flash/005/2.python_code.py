
import random

def policy(board: list[list[int]]) -> int:
    """
    Implements a Connect 4 AI using a 1-ply lookahead (greedy) strategy.
    It prioritizes the following moves in order:
    1.  Immediate Win: Play a move that completes 4 in a row.
    2.  Immediate Block: Play a move that blocks the opponent from winning on their next turn.
    3.  Center Control: Play the center columns (3, 2, 4, etc.) to maximize future opportunities.
    4.  Random: Pick a valid random column if no tactical or positional advantage is found.
    """
    
    # Helper to get the first available row in a column
    def get_available_row(col_index):
        for r in range(5, -1, -1): # Check from bottom (row 5) to top (row 0)
            if board[r][col_index] == 0:
                return r
        return None

    # Helper to check if a move results in a win
    def is_winning_move(col, player):
        row = get_available_row(col)
        if row is None:
            return False
        
        # Temporarily place the disc
        board[row][col] = player
        
        # Check for 4 in a row
        win = False
        
        # Horizontal
        count = 0
        for c in range(7):
            if board[row][c] == player:
                count += 1
                if count >= 4:
                    win = True
                    break
            else:
                count = 0
        
        # Vertical
        if not win:
            count = 0
            for r in range(6):
                if board[r][col] == player:
                    count += 1
                    if count >= 4:
                        win = True
                        break
                else:
                    count = 0
        
        # Diagonal / (Bottom-left to Top-right)
        if not win:
            count = 0
            # Find start of diagonal segment relevant to (row, col)
            r, c = row, col
            while r > 0 and c > 0:
                r -= 1
                c -= 1
            while r < 6 and c < 7:
                if board[r][c] == player:
                    count += 1
                    if count >= 4:
                        win = True
                        break
                else:
                    count = 0
                r += 1
                c += 1
        
        # Diagonal \ (Top-left to Bottom-right)
        if not win:
            count = 0
            r, c = row, col
            while r > 0 and c < 6:
                r -= 1
                c += 1
            while r < 6 and c >= 0:
                if board[r][c] == player:
                    count += 1
                    if count >= 4:
                        win = True
                        break
                else:
                    count = 0
                r += 1
                c -= 1

        # Undo temporary placement
        board[row][col] = 0
        return win

    # Priority 1: Check for instant win
    valid_cols = [c for c in range(7) if get_available_row(c) is not None]
    
    # Optimization: Iterate in a logical order, but we check all valid cols for win
    for col in valid_cols:
        if is_winning_move(col, 1):
            return col

    # Priority 2: Check for instant loss (block opponent)
    for col in valid_cols:
        if is_winning_move(col, -1):
            return col

    # Priority 3: Prefer center columns
    # Order: 3, 2, 4, 1, 5, 0, 6
    center_order = [3, 2, 4, 1, 5, 0, 6]
    for col in center_order:
        if col in valid_cols:
            return col
            
    # Fallback (should not be reached if board is not full)
    return random.choice(valid_cols) if valid_cols else 0
