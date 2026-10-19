
import numpy as np

def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    # Convert board to numpy array for easier handling
    board_array = np.array(board)
    
    # Define winning lines (rows, columns, diagonals)
    lines = [
        [(0, 0), (0, 1), (0, 2)],  # top row
        [(1, 0), (1, 1), (1, 2)],  # middle row
        [(2, 0), (2, 1), (2, 2)],  # bottom row
        [(0, 0), (1, 0), (2, 0)],  # left column
        [(0, 1), (1, 1), (2, 1)],  # middle column
        [(0, 2), (1, 2), (2, 2)],  # right column
        [(0, 0), (1, 1), (2, 2)],  # main diagonal
        [(0, 2), (1, 1), (2, 0)]   # anti diagonal
    ]
    
    # Convert legal_moves to (row, col) format
    legal_positions = [(move // 3, move % 3) for move in legal_moves]
    
    # 1. Check for winning moves (lines with 2 of our confirmed marks and 0 opponent confirmed marks)
    for line in lines:
        our_confirmed = sum(1 for r, c in line if board_array[r, c] == 1)
        # We don't directly see opponent marks, but if a cell is not confirmed as ours,
        # it could be empty or opponent's. We'll be conservative and look for lines
        # where we have maximum confirmed marks and no conflicts with legal moves.
        
        if our_confirmed == 2:
            # Find the empty spot in this line that's still legal
            for r, c in line:
                if (r, c) in legal_positions and board_array[r, c] != 1:
                    return r * 3 + c
    
    # 2. Check for blocking moves (prevent opponent from winning)
    # In phantom TTT, we deduce opponent threats by tracking when our moves fail.
    # For this implementation, we'll block lines that could be threatening.
    for line in lines:
        # Count cells in line that are not confirmed as ours
        # If two cells in a line are not confirmed as ours, and one is confirmed as ours,
        # the opponent might be trying to complete that line.
        not_ours = sum(1 for r, c in line if board_array[r, c] != 1)
        ours = sum(1 for r, c in line if board_array[r, c] == 1)
        
        if not_ours >= 2 and ours >= 1:
            # Try to block by taking one of the unconfirmed cells
            for r, c in line:
                if (r, c) in legal_positions and board_array[r, c] != 1:
                    return r * 3 + c
    
    # 3. Prefer center if available
    if (1, 1) in legal_positions and board_array[1, 1] != 1:
        return 4  # center cell
    
    # 4. Prefer corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for r, c in corners:
        if (r, c) in legal_positions and board_array[r, c] != 1:
            return r * 3 + c
    
    # 5. Take any legal move that's not already confirmed as ours
    for r, c in legal_positions:
        if board_array[r, c] != 1:
            return r * 3 + c
    
    # Fallback (should not happen if legal_moves is non-empty and consistent)
    return legal_moves[0]
