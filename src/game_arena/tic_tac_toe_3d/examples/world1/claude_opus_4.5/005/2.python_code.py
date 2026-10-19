
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    import numpy as np
    
    board = np.array(board)
    
    # Generate all 49 winning lines
    lines = []
    
    # Lines along each axis (27 lines)
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])  # along z
            lines.append([(i, k, j) for k in range(3)])  # along y
            lines.append([(k, i, j) for k in range(3)])  # along x
    
    # Diagonals in each XY plane - z fixed (6 lines)
    for z in range(3):
        lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
        lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
    
    # Diagonals in each XZ plane - y fixed (6 lines)
    for y in range(3):
        lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
        lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
    
    # Diagonals in each YZ plane - x fixed (6 lines)
    for x in range(3):
        lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
        lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
    
    # Space diagonals (4 lines)
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
    
    def get_line_info(line):
        my_count = sum(1 for p in line if board[p] == 1)
        opp_count = sum(1 for p in line if board[p] == -1)
        empty = [p for p in line if board[p] == 0]
        return my_count, opp_count, empty
    
    # Priority 1: Win immediately
    for line in lines:
        my_count, opp_count, empty = get_line_info(line)
        if my_count == 2 and opp_count == 0 and len(empty) == 1:
            return empty[0]
    
    # Priority 2: Block opponent's winning move
    for line in lines:
        my_count, opp_count, empty = get_line_info(line)
        if opp_count == 2 and my_count == 0 and len(empty) == 1:
            return empty[0]
    
    # Priority 3: Create a fork (two ways to win)
    # Score each empty cell
    scores = np.zeros((3, 3, 3))
    
    for line in lines:
        my_count, opp_count, empty = get_line_info(line)
        
        # Offensive scoring - lines I can still win
        if opp_count == 0:
            score = 10 ** my_count
            for p in empty:
                scores[p] += score
        
        # Defensive scoring - lines opponent can still win
        if my_count == 0:
            score = 0.9 * (10 ** opp_count)
            for p in empty:
                scores[p] += score
    
    # Bonus for center (most strategic position)
    if board[1, 1, 1] == 0:
        scores[1, 1, 1] += 50
    
    # Bonus for corners (they're part of more winning lines)
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2),
               (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for c in corners:
        if board[c] == 0:
            scores[c] += 5
    
    # Find best empty cell
    best_score = -1
    best_move = None
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x, y, z] == 0 and scores[x, y, z] > best_score:
                    best_score = scores[x, y, z]
                    best_move = (x, y, z)
    
    # Fallback: return any empty cell
    if best_move is None:
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if board[x, y, z] == 0:
                        return (x, y, z)
    
    return best_move
