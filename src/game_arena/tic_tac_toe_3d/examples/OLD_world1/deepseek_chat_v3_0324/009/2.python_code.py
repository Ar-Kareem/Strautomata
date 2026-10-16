
import numpy as np
from itertools import product

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    AI policy for 3D Tic Tac Toe that prioritizes:
    1. Immediate wins
    2. Blocking opponent's immediate wins
    3. Creating multiple winning opportunities
    4. Center positions (in all dimensions)
    5. Strategic corner and edge positions
    """
    n = len(board)
    board_array = np.array(board)
    
    def get_lines():
        """Generate all possible winning lines in a 3D board"""
        lines = []
        
        # Straight lines in each dimension
        for dim in range(3):
            for fixed1 in range(n):
                for fixed2 in range(n):
                    # Lines along x direction (with y,z fixed)
                    if dim == 0:
                        lines.append([(x, fixed1, fixed2) for x in range(n)])
                    # Lines along y direction (with x,z fixed)
                    elif dim == 1:
                        lines.append([(fixed1, y, fixed2) for y in range(n)])
                    # Lines along z direction (with x,y fixed)
                    else:
                        lines.append([(fixed1, fixed2, z) for z in range(n)])
        
        # 4 space diagonals in each cube
        for z in range(n):
            lines.append([(i, i, z) for i in range(n)])  # Diagonal in xy plane
            lines.append([(i, n-1-i, z) for i in range(n)])  # Anti-diagonal in xy plane
        
        for x in range(n):
            lines.append([(x, i, i) for i in range(n)])  # Diagonal in yz plane
            lines.append([(x, i, n-1-i) for i in range(n)])  # Anti-diagonal in yz plane
        
        for y in range(n):
            lines.append([(i, y, i) for i in range(n)])  # Diagonal in xz plane
            lines.append([(i, y, n-1-i) for i in range(n)])  # Anti-diagonal in xz plane
        
        # 4 main 3D diagonals
        lines.append([(i, i, i) for i in range(n)])  # From (0,0,0) to (2,2,2)
        lines.append([(i, i, n-1-i) for i in range(n)])  # From (0,0,2) to (2,2,0)
        lines.append([(i, n-1-i, i) for i in range(n)])  # From (0,2,0) to (2,0,2)
        lines.append([(i, n-1-i, n-1-i) for i in range(n)])  # From (0,2,2) to (2,0,0)
        
        return lines
    
    def evaluate_move(x, y, z):
        """Evaluate the desirability of a move at (x,y,z)"""
        if board_array[x][y][z] != 0:
            return -1  # Already occupied
        
        # Base score based on position
        center_dist = sum(abs(coord - (n-1)/2) for coord in (x, y, z))
        score = (3*(n-1)/2 - center_dist) * 0.5  # Prefer center positions
        
        temp_board = board_array.copy()
        temp_board[x][y][z] = 1  # Try our move
        
        # Check if this move would win
        for line in get_lines():
            line_values = [temp_board[coord] for coord in line]
            if sum(line_values) == n:
                return float('inf')  # Winning move is best
        
        # Check how many potential winning lines this creates
        our_lines = 0
        for line in get_lines():
            if (x, y, z) in line:
                line_values = [temp_board[coord] for coord in line]
                if line_values.count(1) == n-1 and line_values.count(-1) == 0:
                    our_lines += 1
        score += our_lines * 3  # Reward moves that create opportunities
        
        # Check if this would block opponent's win
        temp_board[x][y][z] = -1  # Test opponent's move
        for line in get_lines():
            line_values = [temp_board[coord] for coord in line]
            if sum(line_values) == -n:
                score += 100  # Blocking opponent's win is very valuable
        
        return score
    
    # First check for immediate wins or blocks
    best_score = -1
    best_move = None
    empty_cells = []
    
    for x, y, z in product(range(n), repeat=3):
        if board_array[x][y][z] != 0:
            continue
            
        empty_cells.append((x, y, z))
        
        # Check if we can win immediately
        temp_board = board_array.copy()
        temp_board[x][y][z] = 1
        for line in get_lines():
            if (x, y, z) in line:
                line_values = [temp_board[coord] for coord in line]
                if sum(line_values) == n:
                    return (x, y, z)
        
        # Check if we need to block opponent
        temp_board[x][y][z] = -1
        for line in get_lines():
            if (x, y, z) in line:
                line_values = [temp_board[coord] for coord in line]
                if sum(line_values) == -n:
                    return (x, y, z)
    
    # If no immediate win/block, choose best strategic move
    best_score = -1
    best_move = None
    
    for x, y, z in empty_cells:
        score = evaluate_move(x, y, z)
        if score > best_score:
            best_score = score
            best_move = (x, y, z)
    
    # Fallback: return first available move if something went wrong
    if best_move is None and empty_cells:
        return empty_cells[0]
    
    return best_move
