
def policy(board: list[list[int]], legal_moves: list[int]) -> tuple[int, int]:
    # Precompute lines for each cell (rows, columns, diagonals)
    lines = {
        (0,0): [(0,0), (0,1), (0,2), (1,0), (2,0), (1,1)],
        (0,1): [(0,0), (0,1), (0,2), (1,1), (2,1)],
        (0,2): [(0,0), (0,1), (0,2), (1,2), (2,2), (1,1)],
        (1,0): [(0,0), (1,0), (2,0), (1,1), (1,2)],
        (1,1): [(0,0), (1,0), (1,1), (1,2), (2,0), (2,2), (0,2), (2,1)],
        (1,2): [(0,2), (1,2), (2,2), (1,1), (1,0)],
        (2,0): [(0,0), (1,0), (2,0), (2,1), (2,2)],
        (2,1): [(0,1), (1,1), (2,1), (2,0), (2,2)],
        (2,2): [(0,2), (1,2), (2,2), (2,0), (2,1), (1,1)]
    }
    
    # Filter legal moves to exclude cells already marked as yours (1)
    legal_moves_filtered = [move for move in legal_moves if board[move[0]][move[1]] == 0]
    
    # Check for immediate winning moves (two of your marks + empty cell)
    for move in legal_moves_filtered:
        i, j = move
        for line in lines[(i, j)]:
            other_cells = [cell for cell in line if cell != (i, j)]
            if sum(1 for cell in other_cells if board[cell[0]][cell[1]] == 1) == 2:
                return move
    
    # Evaluate threat potential (one of your mark + two empty cells)
    threat_counts = []
    for move in legal_moves_filtered:
        i, j = move
        threat_count = 0
        for line in lines[(i, j)]:
            other_cells = [cell for cell in line if cell != (i, j)]
            if sum(1 for cell in other_cells if board[cell[0]][cell[1]] == 1) == 1:
                if all(board[cell[0]][cell[1]] == 0 for cell in other_cells):
                    threat_count += 1
        threat_counts.append(threat_count)
    
    # Select move with highest threat count
    max_threat = max(threat_counts) if threat_counts else 0
    candidates = [move for move, count in zip(legal_moves_filtered, threat_counts) if count == max_threat]
    
    # Fallback: choose first move if no threats
    return candidates[0] if candidates else legal_moves_filtered[0]
