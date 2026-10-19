
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Policy for 3x3x3 3D Tic Tac Toe.
    Returns the next move as (z, y, x) coordinates.
    """
    n = 3
    board_np = np.array(board)
    
    # All possible winning lines in 3D tic-tac-toe
    winning_lines = []
    
    # Lines parallel to x-axis
    for z in range(n):
        for y in range(n):
            winning_lines.append([(z, y, x) for x in range(n)])
    
    # Lines parallel to y-axis
    for z in range(n):
        for x in range(n):
            winning_lines.append([(z, y, x) for y in range(n)])
    
    # Lines parallel to z-axis
    for y in range(n):
        for x in range(n):
            winning_lines.append([(z, y, x) for z in range(n)])
    
    # Diagonals in xy-planes
    for z in range(n):
        winning_lines.append([(z, i, i) for i in range(n)])
        winning_lines.append([(z, i, n-1-i) for i in range(n)])
    
    # Diagonals in xz-planes
    for y in range(n):
        winning_lines.append([(i, y, i) for i in range(n)])
        winning_lines.append([(i, y, n-1-i) for i in range(n)])
    
    # Diagonals in yz-planes
    for x in range(n):
        winning_lines.append([(i, i, x) for i in range(n)])
        winning_lines.append([(i, n-1-i, x) for i in range(n)])
    
    # 4 main space diagonals
    winning_lines.append([(i, i, i) for i in range(n)])
    winning_lines.append([(i, i, n-1-i) for i in range(n)])
    winning_lines.append([(i, n-1-i, i) for i in range(n)])
    winning_lines.append([(n-1-i, i, i) for i in range(n)])
    
    def evaluate_line(line):
        """Returns (player_count, opponent_count, empty_positions)"""
        player_count = 0
        opponent_count = 0
        empty_positions = []
        
        for pos in line:
            val = board_np[pos]
            if val == 1:
                player_count += 1
            elif val == -1:
                opponent_count += 1
            else:
                empty_positions.append(pos)
        
        return player_count, opponent_count, empty_positions
    
    # Priority 1: Win if possible
    for line in winning_lines:
        player_count, opponent_count, empty_positions = evaluate_line(line)
        if player_count == 2 and opponent_count == 0 and len(empty_positions) == 1:
            return empty_positions[0]
    
    # Priority 2: Block opponent from winning
    for line in winning_lines:
        player_count, opponent_count, empty_positions = evaluate_line(line)
        if opponent_count == 2 and player_count == 0 and len(empty_positions) == 1:
            return empty_positions[0]
    
    # Priority 3: Create a fork (two ways to win)
    for z in range(n):
        for y in range(n):
            for x in range(n):
                if board_np[z, y, x] == 0:
                    # Simulate placing our piece
                    threats = 0
                    for line in winning_lines:
                        if (z, y, x) in line:
                            player_count, opponent_count, empty_positions = evaluate_line(line)
                            # If this move creates a line with 2 of ours and 1 empty
                            if player_count == 1 and opponent_count == 0 and len(empty_positions) == 2:
                                threats += 1
                    if threats >= 2:
                        return (z, y, x)
    
    # Priority 4: Block opponent fork
    for z in range(n):
        for y in range(n):
            for x in range(n):
                if board_np[z, y, x] == 0:
                    threats = 0
                    for line in winning_lines:
                        if (z, y, x) in line:
                            player_count, opponent_count, empty_positions = evaluate_line(line)
                            if opponent_count == 1 and player_count == 0 and len(empty_positions) == 2:
                                threats += 1
                    if threats >= 2:
                        return (z, y, x)
    
    # Priority 5: Take center
    if board_np[1, 1, 1] == 0:
        return (1, 1, 1)
    
    # Priority 6: Take any good position
    for line in winning_lines:
        player_count, opponent_count, empty_positions = evaluate_line(line)
        if player_count == 1 and opponent_count == 0 and len(empty_positions) == 2:
            return empty_positions[0]
    
    # Priority 7: Take any empty position
    empty_cells = np.argwhere(board_np == 0)
    if len(empty_cells) > 0:
        return tuple(empty_cells[0])
    
    # Fallback (should never reach here in a valid game)
    return (0, 0, 0)
