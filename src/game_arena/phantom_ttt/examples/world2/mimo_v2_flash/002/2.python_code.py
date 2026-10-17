
import random
import itertools

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Smart policy for Phantom Tic Tac Toe.
    Prioritizes:
    1. Immediate win (2 my marks + 1 unconfirmed in line).
    2. Block potential opponent win (infer via lines with 0 my marks + 3 unconfirmed).
    3. Extend my lines (1 my mark + 2 unconfirmed, prioritizing intersections).
    4. Explore unconfirmed cells (prioritize center, then corners, then edges).
    """
    # Flatten for easier access
    cells = [(i, j) for i in range(3) for j in range(3)]
    my_cells = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 1]
    unconfirmed = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    
    if not unconfirmed:
        # No legal moves? Return a fallback (shouldn't happen in valid game)
        return (0, 0)
    
    # Helper: Check if a line (list of 3 cells) has 2 my marks and 1 unconfirmed
    def line_win(line):
        my_count = sum(1 for (i, j) in line if board[i][j] == 1)
        unconf_count = sum(1 for (i, j) in line if board[i][j] == 0)
        return my_count == 2 and unconf_count == 1
    
    # Helper: Check if line has 0 my marks and 3 unconfirmed (potential opponent win)
    def line_threat(line):
        my_count = sum(1 for (i, j) in line if board[i][j] == 1)
        unconf_count = sum(1 for (i, j) in line if board[i][j] == 0)
        return my_count == 0 and unconf_count == 3
    
    # Helper: Check if line has 1 my mark and 2 unconfirmed (extend opportunity)
    def line_extend(line):
        my_count = sum(1 for (i, j) in line if board[i][j] == 1)
        unconf_count = sum(1 for (i, j) in line if board[i][j] == 0)
        return my_count == 1 and unconf_count == 2
    
    # Define all lines
    lines = []
    # Rows
    for i in range(3):
        lines.append([(i, 0), (i, 1), (i, 2)])
    # Columns
    for j in range(3):
        lines.append([(0, j), (1, j), (2, j)])
    # Diagonals
    lines.append([(0, 0), (1, 1), (2, 2)])
    lines.append([(0, 2), (1, 1), (2, 0)])
    
    # 1. Immediate Win: Find all winning cells
    win_cells = []
    for line in lines:
        if line_win(line):
            for (i, j) in line:
                if board[i][j] == 0:
                    win_cells.append((i, j))
    if win_cells:
        return win_cells[0]  # Return first available win (all are equal value)
    
    # 2. Block: Find cells in lines where opponent could win (infer threat)
    block_cells = []
    for line in lines:
        if line_threat(line):
            for (i, j) in line:
                if board[i][j] == 0:
                    block_cells.append((i, j))
    if block_cells:
        return block_cells[0]
    
    # 3. Extend: Find cells in lines where I have 1 mark
    extend_candidates = []
    for line in lines:
        if line_extend(line):
            for (i, j) in line:
                if board[i][j] == 0:
                    # Score: +1 for each other line this cell is in that has 1 my mark (intersection bonus)
                    score = 0
                    for other_line in lines:
                        if (i, j) in other_line and other_line != line:
                            if line_extend(other_line):
                                score += 1
                    # Prioritize center/corners higher
                    if (i, j) == (1, 1):
                        score += 2
                    elif (i, j) in [(0,0), (0,2), (2,0), (2,2)]:
                        score += 1
                    extend_candidates.append((score, (i, j)))
    
    if extend_candidates:
        extend_candidates.sort(key=lambda x: x[0], reverse=True)
        return extend_candidates[0][1]
    
    # 4. Explore: Priority order - center, corners, edges
    priorities = [(1,1)] + [(0,0), (0,2), (2,0), (2,2)] + [(0,1), (1,0), (1,2), (2,1)]
    for (i, j) in priorities:
        if board[i][j] == 0:
            return (i, j)
    
    # Fallback: random (shouldn't reach here)
    return random.choice(unconfirmed)
