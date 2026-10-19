
import numpy as np

def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    """
    Strategy for Phantom Tic Tac Toe:
    - 1: your confirmed mark
    - 0: unknown (empty or opponent)
    - Choose move from legal_moves with highest priority:
        1. Win: if two 1s in line, take the third (if legal)
        2. Block: if opponent likely has two 0s in line with one 1, block the third
        3. Take center (1,1) if available
        4. Take corner (0,0), (0,2), (2,0), (2,2) if available
        5. Take edge otherwise
    """
    
    # Convert to numpy array for easier indexing
    board = np.array(board)
    
    # Map linear move index to (row, col)
    def index_to_coord(index):
        return index // 3, index % 3
    
    def coord_to_index(row, col):
        return row * 3 + col
    
    # Define all 8 winning lines (rows, cols, diagonals)
    lines = [
        # Rows
        [(0,0), (0,1), (0,2)],
        [(1,0), (1,1), (1,2)],
        [(2,0), (2,1), (2,2)],
        # Columns
        [(0,0), (1,0), (2,0)],
        [(0,1), (1,1), (2,1)],
        [(0,2), (1,2), (2,2)],
        # Diagonals
        [(0,0), (1,1), (2,2)],
        [(0,2), (1,1), (2,0)]
    ]
    
    # Check for immediate win: look for lines with two 1s and one 0
    for line in lines:
        values = [board[r][c] for r, c in line]
        if values.count(1) == 2:
            # Find the index where it's 0
            for r, c in line:
                if board[r][c] == 0:
                    move_idx = coord_to_index(r, c)
                    if move_idx in legal_moves:
                        return move_idx
    
    # Check for potential opponent win: look for lines with two 0s and one 1
    # We assume opponent has placed two marks in such a line and we must block
    for line in lines:
        values = [board[r][c] for r, c in line]
        if values.count(0) == 2 and values.count(1) == 1:
            # Find the 0s; we block one of them (they're both candidates)
            for r, c in line:
                if board[r][c] == 0:
                    move_idx = coord_to_index(r, c)
                    if move_idx in legal_moves:
                        return move_idx
    
    # Prioritize center
    center_idx = coord_to_index(1, 1)
    if center_idx in legal_moves:
        return center_idx
    
    # Prioritize corners
    corners = [coord_to_index(r, c) for r, c in [(0,0), (0,2), (2,0), (2,2)]]
    for corner in corners:
        if corner in legal_moves:
            return corner
    
    # Fallback: any legal move (edges)
    return legal_moves[0]
