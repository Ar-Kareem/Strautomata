
import numpy as np

ME = 1
OPPONENT = 2
EMPTY = 0

def count_liberties(board, r, c, color):
    """Count liberties of the group at (r,c)."""
    if board[r][c] != color:
        return 0
    visited = np.zeros((19, 19), dtype=bool)
    queue = [(r, c)]
    visited[r][c] = True
    liberties = set()
    directions = [(-1,0), (1,0), (0,-1), (0,1)]
    while queue:
        row, col = queue.pop(0)
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and not visited[nr][nc]:
                if board[nr][nc] == EMPTY:
                    liberties.add((nr, nc))
                elif board[nr][nc] == color:
                    visited[nr][nc] = True
                    queue.append((nr, nc))
    return len(liberties)

def find_group(board, r, c, color):
    """Return all coordinates of the group containing (r,c)."""
    if board[r][c] != color:
        return []
    visited = np.zeros((19, 19), dtype=bool)
    queue = [(r, c)]
    visited[r][c] = True
    group = []
    directions = [(-1,0), (1,0), (0,-1), (0,1)]
    while queue:
        row, col = queue.pop(0)
        group.append((row, col))
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and not visited[nr][nc] and board[nr][nc] == color:
                visited[nr][nc] = True
                queue.append((nr, nc))
    return group

def get_move_info(board, r, c, color):
    """Return (is_legal, captures, liberties) for the move (r,c)."""
    if board[r][c] != EMPTY:
        return (False, 0, 0)
    temp_board = [row.copy() for row in board]
    temp_board[r][c] = color
    directions = [(-1,0), (1,0), (0,-1), (0,1)]
    # Check immediate liberties
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and temp_board[nr][nc] == EMPTY:
            return (True, 0, -1)  # At least one liberty
    # Check captures
    opponent = OPPONENT if color == ME else ME
    captured = 0
    captured_groups = []
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and temp_board[nr][nc] == opponent:
            lib = count_liberties(temp_board, nr, nc, opponent)
            if lib == 0:
                group = find_group(temp_board, nr, nc, opponent)
                captured_groups.extend(group)
    if captured_groups:
        # Remove captured stones
        capture_board = [row.copy() for row in temp_board]
        captured = len(captured_groups)
        for x, y in captured_groups:
            capture_board[x][y] = EMPTY
        # Calculate liberties of the placed group
        group = find_group(capture_board, r, c, color)
        liberties = set()
        for x, y in group:
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 19 and 0 <= ny < 19 and capture_board[nx][ny] == EMPTY:
                    liberties.add((nx, ny))
        return (True, captured, len(liberties))
    else:
        # Check group liberties without captures
        group = find_group(temp_board, r, c, color)
        liberties = set()
        for x, y in group:
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 19 and 0 <= ny < 19 and temp_board[nx][ny] == EMPTY:
                    liberties.add((nx, ny))
        return (True, 0, len(liberties)) if liberties else (False, 0, 0)

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Initialize or update memory
    if 'moves' not in memory:
        memory['moves'] = 0
    else:
        memory['moves'] += 1
    moves_made = memory['moves']
    
    # Create 19x19 board (0-indexed)
    board = np.zeros((19, 19), dtype=int)
    for r, c in me:
        board[r-1][c-1] = ME
    for r, c in opponent:
        board[r-1][c-1] = OPPONENT
    
    legal_moves = []
    for r in range(19):
        for c in range(19):
            if board[r][c] == EMPTY:
                is_legal, captures, liberties = get_move_info(board, r, c, ME)
                if is_legal:
                    distance_to_edge = min(r, 18 - r, c, 18 - c)
                    # Positional preference: edge early, center later
                    if moves_made < 50:
                        position_score = 100 - distance_to_edge
                    else:
                        position_score = distance_to_edge
                    score = captures * 1000 + liberties * 10 + position_score
                    legal_moves.append( ((r+1, c+1), score) )  # Convert to 1-based
    
    if not legal_moves:
        return ((0, 0), memory)
    
    # Select move with highest score
    legal_moves.sort(key=lambda x: -x[1])
    best_move = legal_moves[0][0]
    return (best_move, memory)
