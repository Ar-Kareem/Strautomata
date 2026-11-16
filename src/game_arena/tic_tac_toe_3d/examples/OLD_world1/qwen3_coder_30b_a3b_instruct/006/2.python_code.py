
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determine the next move for 3D Tic Tac Toe using a simple heuristic.
    
    The function prioritizes:
    1. Winning moves (if possible)
    2. Blocking opponent wins
    3. Taking the center if available
    4. Taking a corner
    5. Taking any available spot
    
    Args:
        board: 3x3x3 list representing the current game state
        
    Returns:
        Tuple of (x, y, z) coordinates for the next move
    """
    # Flatten the board for easier processing
    def get_cell(x, y, z):
        return board[x][y][z]
    
    def set_cell(x, y, z, value):
        board[x][y][z] = value
    
    # Check if a line (3 in a row) has been completed
    def check_line(line_values):
        if line_values.count(1) == 3:
            return 1  # Player wins
        elif line_values.count(-1) == 3:
            return -1  # Opponent wins
        return 0  # No one wins
    
    # Get all possible lines (rows, columns, diagonals)
    def get_all_lines():
        lines = []
        
        # Rows (3 lines per layer)
        for x in range(3):
            for y in range(3):
                lines.append([(x, y, z) for z in range(3)])
        
        # Columns (3 lines per layer)
        for x in range(3):
            for z in range(3):
                lines.append([(x, y, z) for y in range(3)])
        
        # Layers (3 lines per row)
        for y in range(3):
            for z in range(3):
                lines.append([(x, y, z) for x in range(3)])
        
        # Main diagonals
        # Diagonals through layers (forward)
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
        
        # DiAGONALS within layers
        # Layer 0
        lines.append([(0, 0, 0), (0, 1, 1), (0, 2, 2)])
        lines.append([(0, 0, 2), (0, 1, 1), (0, 2, 0)])
        lines.append([(0, 0, 0), (1, 0, 1), (2, 0, 2)])
        lines.append([(0, 2, 0), (1, 2, 1), (2, 2, 2)])
        
        # Layer 1
        lines.append([(1, 0, 0), (1, 1, 1), (1, 2, 2)])
        lines.append([(1, 0, 2), (1, 1, 1), (1, 2, 0)])
        lines.append([(0, 1, 0), (1, 1, 1), (2, 1, 2)])
        lines.append([(0, 1, 2), (1, 1, 1), (2, 1, 0)])
        
        # Layer 2
        lines.append([(2, 0, 0), (2, 1, 1), (2, 2, 2)])
        lines.append([(2, 0, 2), (2, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 2, 1), (2, 2, 2)])
        lines.append([(2, 0, 0), (1, 0, 1), (0, 0, 2)])
        
        # All 3D diagonals
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
        
        return lines
    
    # Check if a player has won
    def has_won(player):
        lines = get_all_lines()
        for line in lines:
            line_values = [get_cell(x, y, z) for x, y, z in line]
            if line_values.count(player) == 3:
                return True
        return False
    
    # Check if we can win in one move
    def can_win(player):
        lines = get_all_lines()
        for line in lines:
            line_values = [get_cell(x, y, z) for x, y, z in line]
            if line_values.count(player) == 2 and line_values.count(0) == 1:
                # Get the empty position in this line
                for i, pos in enumerate(line):
                    if line_values[i] == 0:
                        return pos
        return None
    
    # Find a random available spot
    def find_random_move():
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if get_cell(x, y, z) == 0:
                        return (x, y, z)
        return None
    
    # Check if the center is available
    if get_cell(1, 1, 1) == 0:
        return (1, 1, 1)
    
    # Try to win (in one move)
    winning_move = can_win(1)  # Check if we can win
    if winning_move is not None:
        return winning_move
    
    # Try to block opponent from winning
    blocking_move = can_win(-1)  # Check if opponent can win
    if blocking_move is not None:
        return blocking_move
    
    # Try to take a corner
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2), (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    available_corners = [c for c in corners if get_cell(*c) == 0]
    if available_corners:
        return available_corners[0]
    
    # Otherwise, take any available spot
    return find_random_move()
