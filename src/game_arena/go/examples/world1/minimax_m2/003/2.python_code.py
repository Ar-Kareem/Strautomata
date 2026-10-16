
from collections import deque

def find_group(board, r, c, player):
    """
    Find the group of connected stones of a given player starting from (r, c).
    Returns a tuple (group_set, liberties_set) where group_set contains all points in the group,
    and liberties_set contains all adjacent empty points.
    """
    if board[r][c] != player:
        return set(), set()
    
    visited = set()
    group = set()
    liberties = set()
    queue = deque([(r, c)])
    
    while queue:
        x, y = queue.popleft()
        if (x, y) in visited:
            continue
        visited.add((x, y))
        group.add((x, y))
        # Check four neighbors for liberties or connections
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 19 and 0 <= ny < 19:
                if board[nx][ny] == 0:
                    liberties.add((nx, ny))
                elif board[nx][ny] == player:
                    if (nx, ny) not in visited:
                        queue.append((nx, ny))
    return group, liberties

def is_legal_move(board, r, c):
    """
    Check if placing a stone at (r, c) is legal for the current player (1).
    Returns (True, lib_count) if legal, where lib_count is the number of liberties after the move.
    Returns (False, 0) if illegal.
    """
    if board[r][c] != 0:
        return False, 0
    
    # Create a copy of the board for simulation
    new_board = [row[:] for row in board]
    new_board[r][c] = 1  # Place the stone
    
    # Check for captures of adjacent opponent groups
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nx, ny = r + dx, c + dy
        if 0 <= nx < 19 and 0 <= ny < 19:
            if new_board[nx][ny] == -1:  # Opponent stone
                group, liberties = find_group(new_board, nx, ny, -1)
                if len(liberties) == 0:
                    # Capture the group
                    for (x, y) in group:
                        new_board[x][y] = 0
    
    # Check if the new group has liberties
    group, liberties = find_group(new_board, r, c, 1)
    if len(liberties) == 0:
        return False, 0
    else:
        return True, len(liberties)

def policy(me, opponent):
    """
    Main policy function. It evaluates the board and returns the next move as (row, col) or (0,0) to pass.
    """
    # Initialize the board: 0 for empty, 1 for me, -1 for opponent
    board = [[0] * 19 for _ in range(19)]
    for r, c in me:
        board[r-1][c-1] = 1
    for r, c in opponent:
        board[r-1][c-1] = -1
    
    total_stones = len(me) + len(opponent)
    legal_moves = []
    
    # Generate all candidate moves
    for i in range(19):
        for j in range(19):
            if board[i][j] == 0:
                legal, lib_count = is_legal_move(board, i, j)
                if legal:
                    # Compute distance to edges and center (using 0-based indices)
                    d_edge = min(i, 18 - i, j, 18 - j)
                    d_center = (i - 9) ** 2 + (j - 9) ** 2
                    lib_count = lib_count  # Already computed
                    
                    # Compute score based on game stage
                    if total_stones < 50:
                        score = d_center - d_edge + lib_count
                    else:
                        score = d_edge - d_center + lib_count
                    
                    legal_moves.append((score, i, j))
    
    if not legal_moves:
        return (0, 0)
    
    # Select the move with the highest score
    best_score, best_i, best_j = max(legal_moves)
    return (best_i + 1, best_j + 1)  # Convert to 1-based indices
