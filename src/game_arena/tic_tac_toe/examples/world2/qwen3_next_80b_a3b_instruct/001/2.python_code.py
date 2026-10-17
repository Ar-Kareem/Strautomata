
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board = np.array(board)
    
    # Find all empty positions (value 0)
    empty_positions = np.where(board == 0)
    empty_cells = list(zip(empty_positions[0], empty_positions[1]))
    
    # Helper function to check if placing mark at (r,c) creates 4 in a row
    def has_four_in_a_row(brd, player, r, c):
        # Check row
        if sum(brd[r, :] == player) >= 4:
            # Look for 4 consecutive in row
            for start in range(1):  # In 4x4, only possible start positions for 4 in row: 0
                if all(brd[r, start:start+4] == player):
                    return True
        # Check column
        if sum(brd[:, c] == player) >= 4:
            for start in range(1):  # Only start=0 possible in 4x4
                if all(brd[start:start+4, c] == player):
                    return True
        # Check main diagonal (top-left to bottom-right)
        # Check if (r,c) is on a main diagonal of length 4
        # Diagonal: r-c == constant
        diag_const = r - c
        diag_indices = [(i, i - diag_const) for i in range(4) if 0 <= i - diag_const < 4]
        if len(diag_indices) >= 4:
            # We need to check 4 consecutive on this diagonal
            # Only possible 4-in-a-row diagonals in 4x4 are full main and anti-diagonals
            if diag_const == 0:  # main diagonal
                if all(brd[i, i] == player for i in range(4)):
                    return True
            elif diag_const == 1:  # diagonal above main: (0,1), (1,2), (2,3)
                pass
            elif diag_const == -1: # diagonal below main: (1,0), (2,1), (3,2)
                pass
            elif diag_const == 2:  # (0,2), (1,3)
                pass
            elif diag_const == -2: # (2,0), (3,1)
                pass
            # only 4-length diagonals are main and anti
        # Check anti-diagonal (top-right to bottom-left)
        anti_diag_const = r + c
        if anti_diag_const == 3:  # main anti-diagonal (0,3),(1,2),(2,1),(3,0)
            if all(brd[i, 3-i] == player for i in range(4)):
                return True
        elif anti_diag_const == 2: # (0,2),(1,1),(2,0)
            pass
        elif anti_diag_const == 4: # (1,3),(2,2),(3,1)
            pass
        elif anti_diag_const == 1: # (0,1),(1,0)
            pass
        elif anti_diag_const == 5: # (2,3),(3,2)
            pass
        # Also check any 4 consecutive on longer diagonals? But in 4x4, only full diagonals can have 4
        # So we only check the two full diagonals for 4-in-a-row.
        
        # Actually, let's be more systematic and check every possible 4-in-a-row
        # In 4x4, possible sequences: 4 rows, 4 cols, 2 full diagonals (main and anti)
        # No other 4-in-a-row exists because diagonals of length 3 or less can't have 4
        
        for i in range(4):
            # Check row i
            if all(brd[i, j] == player for j in range(4)):
                return True
            # Check column i
            if all(brd[j, i] == player for j in range(4)):
                return True
        
        # Check main diagonal
        if all(brd[i, i] == player for i in range(4)):
            return True
        # Check anti-diagonal
        if all(brd[i, 3-i] == player for i in range(4)):
            return True
            
        return False
    
    # Step 1: Check if we can win in one move
    for r, c in empty_cells:
        board[r, c] = 1
        if has_four_in_a_row(board, 1, r, c):
            board[r, c] = 0  # revert
            return (r, c)
        board[r, c] = 0
    
    # Step 2: Check if opponent can win in one move, block it
    for r, c in empty_cells:
        board[r, c] = -1
        if has_four_in_a_row(board, -1, r, c):
            board[r, c] = 0  # revert
            return (r, c)
        board[r, c] = 0
    
    # Step 3: Prioritize center positions: [1,1], [1,2], [2,1], [2,2]
    center = [(1,1), (1,2), (2,1), (2,2)]
    for pos in center:
        if board[pos[0], pos[1]] == 0:
            return pos
    
    # Step 4: Then corners: (0,0), (0,3), (3,0), (3,3)
    corners = [(0,0), (0,3), (3,0), (3,3)]
    for pos in corners:
        if board[pos[0], pos[1]] == 0:
            return pos
    
    # Step 5: Any remaining edge or other positions (just pick first available)
    for r, c in empty_cells:
        return (r, c)
    
    # Should not reach here if board has at least one empty cell
    # But if board is full (unlikely in game), return anything
    return (0, 0)
