
import numpy as np
from itertools import product

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    AI policy for 3D Tic Tac Toe.
    Returns the coordinates (x, y, z) of the best move.
    """
    n = len(board)
    board = np.array(board)
    
    # All possible lines in 3D (rows, columns, depths, and diagonals)
    def get_all_lines():
        lines = []
        # 2D lines in each layer
        for z in range(n):
            for y in range(n):
                lines.append(board[z,y,:])  # rows
            for x in range(n):
                lines.append(board[z,:,x])  # columns
            # Layer diagonals
            lines.append(board[z].diagonal())
            lines.append(np.fliplr(board[z]).diagonal())
        
        # Vertical lines
        for x in range(n):
            for y in range(n):
                lines.append(board[:,y,x])
        
        # 3D diagonals
        lines.append(np.array([board[i,i,i] for i in range(n)]))
        lines.append(np.array([board[i,i,n-1-i] for i in range(n)]))
        lines.append(np.array([board[i,n-1-i,i] for i in range(n)]))
        lines.append(np.array([board[n-1-i,i,i] for i in range(n)]))
        
        return lines
    
    def evaluate_line(line):
        """Evaluate how strong a line is for us or opponent"""
        count_p = np.count_nonzero(line == 1)
        count_o = np.count_nonzero(line == -1)
        if count_p > 0 and count_o > 0:
            return 0  # blocked line
        elif count_p > 0:
            return 10 ** (count_p - 1)
        elif count_o > 0:
            return -10 ** (count_o - 1)
        return 1  # empty line has potential
    
    def importance(x, y, z):
        """Calculate importance of position based on centrality"""
        center = (n-1)/2
        distance = ((x-center)**2 + (y-center)**2 + (z-center)**2)**0.5
        return 10 - distance  # center is more important
    
    # Step 1: Check for immediate win
    empty_cells = np.argwhere(board == 0)
    for (z, y, x) in empty_cells:
        temp_board = board.copy()
        temp_board[z,y,x] = 1
        lines = get_all_lines()
        if any(np.count_nonzero(line == 1) == n for line in lines):
            return (z, y, x)
    
    # Step 2: Block opponent's immediate win
    for (z, y, x) in empty_cells:
        temp_board = board.copy()
        temp_board[z,y,x] = -1
        lines = get_all_lines()
        if any(np.count_nonzero(line == -1) == n for line in lines):
            return (z, y, x)
    
    # Step 3: Evaluate all possible moves and choose the best
    best_score = -np.inf
    best_move = None
    
    for (z, y, x) in empty_cells:
        temp_board = board.copy()
        temp_board[z,y,x] = 1
        
        # Calculate score for this move
        score = importance(x, y, z)
        
        # Evaluate all lines affected by this move
        lines = get_all_lines()
        for line in lines:
            line_score = evaluate_line(line)
            if line_score > 0:  # positive for our potential
                score += line_score
        
        # Prefer positions that create opportunities
        if score > best_score or (score == best_score and importance(x, y, z) > importance(*best_move)):
            best_score = score
            best_move = (z, y, x)
    
    return best_move if best_move is not None else empty_cells[0]
